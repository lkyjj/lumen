# Security policy

## Secrets

LUMEN never accepts credentials in source files, `film.yaml`, command arguments, Git remotes,
screenshots or `run.jsonl`. Use a local `.env` file for developer runs or request-scoped key
injection in Studio. `.env` is ignored; `.env.example` contains placeholders only.

Any credential that has appeared in a chat message, screenshot, terminal command or remote URL
must be treated as compromised and revoked immediately. Do not “test it one last time.” Create a
replacement only after revocation, and enter it locally.

Provider errors pass through `lumen.runlog.redact()` before they reach disk or user-visible status.
Values under names such as `api_key`, `token`, `password`, `authorization` and `secret` are removed,
and common GitHub/ModelScope/DashScope token prefixes are scrubbed from arbitrary error text.

## Before every push

Run the automated scan and inspect the staged patch:

```bash
.venv/bin/pytest
.venv/bin/python scripts/scan_secrets.py
git diff --check
git diff --cached
git remote -v
```

The final command must show a credential-free URL such as
`https://github.com/lkyjj/lumen.git` or `git@github.com:lkyjj/lumen.git`.

## Paid-call invariant

Every paid provider receives an injected `Budget`. It must:

1. calculate a worst-case estimate;
2. call `Budget.check()` or `Budget.reserve()` before sending the request;
3. call `Budget.charge()` only after the provider reports success;
4. release a reservation on failure;
5. stop when retries are exhausted and request human review.

Free quota and discounts are not considered permission to skip the circuit breaker.

## Reporting a vulnerability

Do not open a public issue containing a key or private response body. Revoke the credential first,
then report only a redacted reproduction and the affected code path.
