#!/usr/bin/env python3
"""Crea un commit que GitHub firma.

Un `git commit` local empujado con el token del workflow queda Unverified:
el autor es quien configuró `git config` y nadie firma. `createCommitOnBranch`
lo escribe la API y el committer es GitHub (`noreply@github.com`, reason valid).

El script no hace `git commit` ni `git push`. Compara los archivos locales con
el árbol de la rama y, si hay diferencia, manda un commit. Si la rama no
existe, la crea apuntando a la rama base y el commit sale de ahí.

Uso:
  commit_via_api.py --branch main --message "texto" -- archivo [archivo...]
  commit_via_api.py --branch data/mirror-log --from main --message "texto" -- docs/transparency/MIRROR-LOG.md
  commit_via_api.py --ensure-branch snapshots --from main
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    # Identificador de blob de git, no un hash de seguridad.
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


class GitHub:
    def __init__(self, token: str, repository: str) -> None:
        self.token = token
        self.repository = repository
        owner, _, name = repository.partition("/")
        if not owner or not name:
            raise SystemExit(f"repositorio invalido: {repository}")
        self.owner = owner
        self.name = name

    def request(self, method: str, url: str, body: dict | None = None) -> tuple[int, dict]:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "vigil-commit-via-api",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode()
                return resp.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode()
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {"message": raw}
            return exc.code, parsed

    def graphql(self, query: str, variables: dict) -> dict:
        status, payload = self.request(
            "POST",
            "https://api.github.com/graphql",
            {"query": query, "variables": variables},
        )
        if status >= 300:
            raise SystemExit(f"graphql http {status}: {payload}")
        if payload.get("errors"):
            return payload
        return payload.get("data") or {}

    def branch_oid(self, branch: str) -> str | None:
        data = self.graphql(
            """query($owner:String!,$name:String!,$ref:String!){
              repository(owner:$owner,name:$name){ ref(qualifiedName:$ref){ target{ oid } } }
            }""",
            {"owner": self.owner, "name": self.name, "ref": f"refs/heads/{branch}"},
        )
        if data.get("errors"):
            raise SystemExit(json.dumps(data["errors"]))
        ref = (data.get("repository") or {}).get("ref")
        if not ref:
            return None
        return ref["target"]["oid"]

    def create_branch(self, branch: str, sha: str) -> None:
        status, payload = self.request(
            "POST",
            f"https://api.github.com/repos/{self.repository}/git/refs",
            {"ref": f"refs/heads/{branch}", "sha": sha},
        )
        if status == 422 and "already exists" in json.dumps(payload):
            return
        if status >= 300:
            raise SystemExit(f"crear rama {branch}: http {status}: {payload}")

    def tree_shas(self, oid: str) -> dict[str, str]:
        status, payload = self.request(
            "GET",
            f"https://api.github.com/repos/{self.repository}/git/trees/{oid}?recursive=1",
        )
        if status >= 300:
            raise SystemExit(f"arbol {oid}: http {status}: {payload}")
        out: dict[str, str] = {}
        for entry in payload.get("tree") or []:
            if entry.get("type") == "blob":
                out[entry["path"]] = entry["sha"]
        return out

    def commit(self, branch: str, oid: str, message: str, additions: list[dict], deletions: list[dict]) -> str:
        headline, _, body = message.partition("\n")
        message_input: dict = {"headline": headline.strip()}
        if body.strip():
            message_input["body"] = body.strip()
        changes: dict = {}
        if additions:
            changes["additions"] = additions
        if deletions:
            changes["deletions"] = deletions
        data = self.graphql(
            """mutation($input:CreateCommitOnBranchInput!){
              createCommitOnBranch(input:$input){ commit{ oid } }
            }""",
            {
                "input": {
                    "branch": {"repositoryNameWithOwner": self.repository, "branchName": branch},
                    "message": message_input,
                    "expectedHeadOid": oid,
                    "fileChanges": changes,
                }
            },
        )
        if data.get("errors"):
            text = json.dumps(data["errors"])
            raise RuntimeError(text)
        return data["createCommitOnBranch"]["commit"]["oid"]


def collect(root: Path, paths: list[str], remote: dict[str, str], sync: bool) -> tuple[list[dict], list[dict]]:
    additions: list[dict] = []
    deletions: list[dict] = []
    seen: set[str] = set()
    for raw in paths:
        path = Path(raw)
        absolute = path if path.is_absolute() else root / path
        if absolute.is_dir():
            prefix = "" if path.as_posix() in {".", ""} else path.as_posix().rstrip("/")
            for child in absolute.rglob("*"):
                if not child.is_file() or ".git" in child.parts:
                    continue
                rel = child.relative_to(root).as_posix()
                seen.add(rel)
                _maybe_add(additions, rel, child.read_bytes(), remote)
            if sync:
                for rel in list(remote):
                    if not prefix or rel == prefix or rel.startswith(prefix + "/"):
                        if rel not in seen:
                            deletions.append({"path": rel})
            continue
        rel = path.as_posix()
        if not absolute.is_file():
            if rel in remote:
                deletions.append({"path": rel})
            continue
        seen.add(rel)
        _maybe_add(additions, rel, absolute.read_bytes(), remote)
    return additions, deletions


def _maybe_add(additions: list[dict], rel: str, data: bytes, remote: dict[str, str]) -> None:
    if remote.get(rel) == git_blob_sha(data):
        return
    additions.append({"path": rel, "contents": base64.b64encode(data).decode()})


def publish(
    github: GitHub, branch: str, base: str, message: str, paths: list[str], root: Path, sync: bool
) -> str | None:
    oid = github.branch_oid(branch)
    if oid is None:
        base_oid = github.branch_oid(base)
        if base_oid is None:
            raise SystemExit(f"no existe la rama base {base}")
        github.create_branch(branch, base_oid)
        oid = github.branch_oid(branch)
        if oid is None:
            raise SystemExit(f"no se pudo crear {branch}")
    for attempt in range(1, 6):
        remote = github.tree_shas(oid)
        additions, deletions = collect(root, paths, remote, sync)
        if not additions and not deletions:
            print(f"sin cambios en {branch}")
            return None
        try:
            new_oid = github.commit(branch, oid, message, additions, deletions)
            print(new_oid)
            return new_oid
        except RuntimeError as exc:
            text = str(exc)
            if attempt == 5 or not any(
                word in text.lower() for word in ("expectedhead", "fast-forward", "not a fast forward", "update")
            ):
                raise SystemExit(text) from exc
            print(f"la rama se movio, reintento {attempt}", file=sys.stderr)
            time.sleep(attempt)
            oid = github.branch_oid(branch) or oid
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", required=True)
    parser.add_argument("--from", dest="base", default="main")
    parser.add_argument("--message", default="")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--root", default=".")
    parser.add_argument("--sync", action="store_true")
    parser.add_argument("--ensure-branch", action="store_true")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        raise SystemExit("falta GH_TOKEN o GITHUB_TOKEN")
    if not args.repository:
        raise SystemExit("falta --repository o GITHUB_REPOSITORY")
    github = GitHub(token, args.repository)
    if args.ensure_branch and not args.paths:
        if github.branch_oid(args.branch):
            print(f"{args.branch} ya existe")
            return
        base_oid = github.branch_oid(args.base)
        if base_oid is None:
            raise SystemExit(f"no existe la rama base {args.base}")
        github.create_branch(args.branch, base_oid)
        print(f"creada {args.branch} en {base_oid}")
        return
    if not args.message:
        raise SystemExit("falta --message")
    if not args.paths:
        raise SystemExit("falta al menos un archivo")
    publish(github, args.branch, args.base, args.message, args.paths, Path(args.root).resolve(), args.sync)


if __name__ == "__main__":
    main()
