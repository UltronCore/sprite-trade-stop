# Changelog

All notable changes to Sprite Trade Stop. Format: date — what — why.
This project uses [Semantic Versioning](https://semver.org/).

## [1.2.0] — 2026-06-19
### Added — web tracker integration
- **`/synccollection <code>`** — imports a member's collection from the web
  tracker's share/sync code (accepts the raw code or a full link). Decoded from
  a bundled `spritebot/assets/sprites.json` generated from the web app's data,
  so the sprite order/encoding can never drift between the two.
- **`/mycollection [@user]`** and **`/missing [@user]`** — the bot now renders
  the "My Sprites" (green) and "Looking For" (red) images **server-side with
  Pillow** and posts them directly in Discord (no screenshotting the site).
- **`/holders <sprite>`** (autocomplete) — who, among synced members, has a
  sprite — find a trade partner instantly.
- **`/spritematch`** — ranks members who have the sprites *you're* missing.
- New `collections` table; Pillow added to requirements; +9 tests (share-code
  decode parity, round-trip, collection storage/holders/leaderboard).

## [1.1.0] — 2026-06-19
### Added
- **`/tracker`** command + a welcome-message link to the new web sprite
  collection tracker (https://ultroncore.github.io/sprite-tracker/) — members
  mark Have/Missing/Mastered, filter by Normal/Gold/Gummy/Galaxy, and export a
  shareable trade image. `TRACKER_URL` is configurable in `config.py`.

## [1.0.1] — 2026-06-08
Hardening pass from a full QA review (correctness + security + docs). No breaking
changes to commands or config defaults; adds two tunable knobs.

### Fixed
- **Trade confirm race:** two simultaneous confirms could post the completion
  message twice / double-count. Now an atomic `complete_if_both_confirmed`
  guarantees exactly-once completion. *Why:* data integrity.
- **`+rep` in DMs** raised `AttributeError` (no guild). Added `@commands.guild_only()`
  and an error handler so misuse replies instead of failing silently.
- **Embed field overflow:** long `/trade` items or vouch notes could exceed
  Discord's 1024-char field limit and bounce the send. All user text is now capped.
- **`/whohas` `/whoneeds` `/match`** now `defer()` and `chunk()` the guild so
  results are complete and never hit the 3s timeout.

### Security
- **Mention injection neutralized:** bot-wide `allowed_mentions=AllowedMentions.none()`;
  the trade-complete message pings only the two traders explicitly.
- **Anti-farming:** `MAX_VOUCHES_PER_DAY` cap on vouches given; `/trade` now
  enforces the same blacklist + minimum-account-age gate as vouching.
- **Blacklist teeth:** blacklisting strips a user's flair/verified roles and
  removes them from the leaderboard.
- **`reportscammer` guards:** no self-reports, blacklisted users blocked, and a
  per-user cooldown (`SCAM_REPORT_COOLDOWN_SECONDS`) against report-bombing.
- **Admin checks** prefer `/setup`-resolved role IDs over spoofable role names.

### Changed
- CI now runs a Python **3.10 / 3.11 / 3.12** matrix (the README "3.10+" claim
  is now actually tested).
- Doc fixes: `+rep` takes note-only (not proof); documented `/insights`
  `messages_per_channel`; noted that adding a sprite needs a bot restart;
  corrected stale `tasks.py` docstring references and the `LIST_REFRESH_MINUTES`
  comment.

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
