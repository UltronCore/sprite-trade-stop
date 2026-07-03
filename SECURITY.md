# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately via **GitHub → Security → "Report a vulnerability"** (private security advisories) on this repository. Do not open a public issue for security reports.

You can expect an acknowledgment within a few days. Please include reproduction steps and the affected version/commit if known.

## Scope

- This repository's code (`spritebot/`, `bot.py`) and its configuration handling.
- The bot stores its token only via environment variables (`.env`, never committed) and uses a local SQLite database. If you believe a token or member data could be exposed by a code path, that is in scope.

## Out of scope

- Discord platform vulnerabilities (report to Discord).
- Issues requiring server-admin permissions the bot doesn't request.

## Hardening notes for self-hosters

- Never commit `.env`; rotate the bot token immediately if it is ever exposed.
- Run with least-privilege Discord intents/permissions per `HOSTING.md`.
