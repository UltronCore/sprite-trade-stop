# Changelog

All notable changes to Sprite Trade Stop. Format: date — what — why.
This project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-06-08
Initial release. Built end-to-end and verified (lint + tests + cog-load smoke test).

### Added
- **Vouch + reputation:** `/vouch` and `+rep` alias with unique IDs, proof,
  notes; `/profile`, `/rank`, `/leaderboard`; admin `/editvouch`, `/removevouch`.
  *Why:* trust economy is the core of a trading server.
- **Vouch-driven XP + flair ladder** (Newbie → Trader → Verified Trader →
  Veteran → Max Helper), all thresholds configurable; auto-assigns
  `verified-trader`. *Why:* recognize active, trusted traders automatically.
- **Two-party trade flow** (`/trade`) with persistent Confirm/Cancel buttons;
  counts only when both confirm, then prompts vouches. *Why:* anti-scam.
- **Scam protection:** `/reportscammer` → modlog, `/blacklist`/`/unblacklist`,
  configurable minimum account age. *Why:* protect members from scammers.
- **Collection lookup from existing Onboarding roles:** `/whohas`, `/whoneeds`,
  `/match`; auto-maintained `#sprite-list` and `#gold-zp-list`. *Why:* work with
  the server's setup instead of duplicating it; help members find trade partners.
- **`/insights`** — AI-free analytics (pure counts) over recent messages.
  *Why:* help the owner decide what to adjust, without any paid AI.
- **Welcome** message + Newbie assignment on join. *Why:* onboard new traders.
- **`/setup`** admin command to auto-detect and save channel/role IDs.
  *Why:* the team shouldn't hunt for IDs by hand.
- Owner-editable **config block**, `.env` token handling, SQLite storage.
- Repo scaffolding: MIT license, `requirements.txt`, `.gitignore`,
  GitHub Actions CI (ruff + pytest), unit tests, `update.sh` with rollback,
  README / HOSTING / MAINTAINERS / DECISIONS / ISSUES docs.

[1.0.0]: https://github.com/UltronCore/sprite-trade-stop/releases/tag/v1.0.0
