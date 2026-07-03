# Project Context (AI agents — Claude, Fable, Codex)

**Purpose:** Open-source Discord bot for a Fortnite sprite-trading community — vouch/trust economy, two-party trades, collection lookup. Python + discord.py + SQLite, AI-free.
**Status:** active, public, best-maintained repo in this ecosystem. Deep docs already exist — read them first: `ARCHITECTURE.md`, `USAGE.md`, `DECISIONS.md`, `ISSUES.md`, `HOSTING.md`, `OWNER-GUIDE.md`.

## Run / test
- `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
- Copy `.env.example` → `.env`, set `DISCORD_TOKEN`. Run: `python bot.py`
- Tests: `pytest -q` (CI runs ruff + pytest on 3.10/3.11/3.12). Lint: `ruff check`.

## Safe vs dangerous
- Safe: cogs, tests, docs, `ruff check`, `pytest`.
- **Dangerous:** never commit `.env` or the SQLite DB (real member data); `update.sh` redeploys a live bot; don't hardcode tokens/guild IDs.
- Env: `DISCORD_TOKEN` (see `.env.example`).

## Conventions & workflow
ruff (E/F/I/UP, line 100, py310). Small PRs, imperative commits. Security policy: `SECURITY.md`. Internal planning/roadmap is maintained separately (not in this public repo).

## Next tasks
See `ISSUES.md`. CI could add a `permissions: contents: read` block.
