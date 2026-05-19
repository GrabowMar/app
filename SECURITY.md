# Security Policy

## Supported versions

Only the current `main` branch is supported. There are no maintained release
branches.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Instead, report them privately via GitHub's
[Security Advisories](https://github.com/GrabowMar/app/security/advisories/new)
flow, which gives us a private channel to triage and fix the issue before
public disclosure.

Please include:

- A description of the issue and its impact.
- Steps to reproduce (or a proof-of-concept).
- The affected commit / branch.
- Any suggested mitigation.

We will acknowledge reports within a few business days and aim to have a fix
or mitigation in place within 30 days of confirmation, depending on
complexity.

## Known prior leaks

The following secrets were briefly committed to git history (now removed
from the working tree but **still present in older commits**):

- `OPENROUTER_API_KEY` (real key)
- Local-dev `POSTGRES_USER` / `POSTGRES_PASSWORD`
- Local-dev `CELERY_FLOWER_USER` / `CELERY_FLOWER_PASSWORD`

**The OpenRouter key has been rotated at <https://openrouter.ai/keys>.** The
Postgres/Flower values only ever protected a local dev environment — they
have been regenerated for fresh clones by `just bootstrap`, and were never
used in production.

If you find a secret that hasn't been rotated, please open a private
advisory using the link above.

## Out of scope

- Issues that require physical access to a developer's machine.
- Findings purely from automated scanners with no demonstrated impact.
- Reports on third-party services (OpenRouter, Sentry, etc.) — please report
  those to the respective vendors.
