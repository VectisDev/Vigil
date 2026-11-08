# Ops keys

The ops panel keeps the access-key field. That field is not sent, not stored, and not written to a log. New keys are not shown on the page.

Three clicks, on your own copy:

1. Open the panel and press Regenerar claves. That opens Actions → Regenerate Admin Seeds (`.github/workflows/regenerate-seeds.yml`) on your own copy. Only the owner of that copy can run it.
2. Press Run workflow.
3. When the run finishes, download the artifact `vigil-keys-download-once`. It expires in one day. The workflow commits hashes in `web/access.json` and does not print the keys.

The boundary for a commit GitHub reports as verified is still the signature. Pushing that commit uses a GitHub credential.

The store is a per-key salted PBKDF2 hash in `config/ops_keys.yml`. Older generators used 24-character secrets. One of those sets was published in the commit message of `d32970cf1` (pull request 627). Those keys are invalid.

The person who forks the repository generates the keys and hands them to their team:

```bash
python3 scripts/ops_keys.py generate
```

Each key is 12 characters from a 62-character alphabet (about 71 bits), drawn with a CSPRNG. The key is the secret and, through its fingerprint, the anonymous id. `config/ops_keys.yml` stores a salted hash. Commit that file. Do not commit the printed keys.

A signed commit that changes the pace, or any other ops action, names `key_id`. An Action checks that the id is active. To check a key someone presents, run `python3 scripts/ops_keys.py check` and type the key on stdin. The command prints the id, or `no match`.

Rotate one id with `python3 scripts/ops_keys.py rotate ID`. Revoke one with `python3 scripts/ops_keys.py revoke ID`. Revocation stops later actions. Older commits still show the old id. No personal data is stored.

Keys printed by older generators, including any copy of `centinel-seeds.txt`, should be retired. They are not in this file.
