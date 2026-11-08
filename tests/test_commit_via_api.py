"""Los workflows que publican commits lo hacen por la API, que GitHub firma."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
SCRIPT = ROOT / ".github" / "scripts" / "commit_via_api.py"

# La wiki es otro repositorio git (owner/repo.wiki.git). createCommitOnBranch
# no aplica ahi, y esos commits no entran en main.
WIKI = "wiki-sync.yml"


def test_blob_sha_matches_git(tmp_path: Path):
    import subprocess
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("commit_via_api", SCRIPT)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    for data in (b"", b"hola\n"):
        path = tmp_path / "blob"
        path.write_bytes(data)
        expected = subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()
        assert module.git_blob_sha(data) == expected


def test_workflows_do_not_push_local_commits():
    problems: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        if path.name == WIKI:
            continue
        text = path.read_text(encoding="utf-8")
        if "git commit" in text or "git push" in text:
            problems.append(path.name)
    assert problems == []


def test_mirror_log_does_not_commit_to_main():
    text = (WORKFLOWS / "mirror.yml").read_text(encoding="utf-8")
    assert "data/mirror-log" in text
    assert "commit_via_api.py" in text
    assert "git push origin HEAD:main" not in text


def test_wiki_is_the_only_local_push_and_it_is_not_main():
    text = (WORKFLOWS / WIKI).read_text(encoding="utf-8")
    assert ".wiki.git" in text
    assert "git push origin main" not in text
