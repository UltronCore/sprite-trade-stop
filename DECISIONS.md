# Decisions & Assumptions

Every assumption made during the autonomous build, so nothing is a mystery later.

## Repo / process
- **Public GitHub repo under UltronCore.** The spec said "open-source," MIT,
  with GitHub Actions on every push and semantic version tags — all of which
  imply a public GitHub home. (The prior research repo was explicitly *private*;
  this one was explicitly *open-source*, so public.)
- **Language/runtime:** Python 3.10+ targeted (developed/tested on 3.14; CI runs
  3.12). discord.py 2.x for native slash commands + UI buttons.
- **Single bot, cogs architecture** (not literally separate parallel processes).
  The requested "subagents A–E" were build-time roles; the shipped artifact is
  one cohesive bot with one shared DB/config to avoid integration drift.

## Data model
- **Reputation is derived, not cached.** Vouch count drives XP/flair/verified on
  the fly, so edit/remove vouch stays consistent with zero extra bookkeeping.
- **One active vouch per (voucher → target) pair** to prevent spam-vouching.
  Removed vouches are soft-deleted (`removed=1`) to preserve audit history.
- **XP = vouches × XP_PER_VOUCH.** No chat XP, per spec ("XP only by receiving
  vouches").

## Config / setup
- **Config holds names; `/setup` resolves IDs into the DB; DB overrides config.**
  This satisfies both "owner-editable config block" and "/setup auto-detects IDs."
- **Default thresholds chosen** (tunable): verified-trader at **5** vouches;
  flair ladder Newbie 0 / Trader 1 / Verified Trader 5 / Veteran 15 / Max Helper
  40; **XP_PER_VOUCH = 10**; **MIN_ACCOUNT_AGE_DAYS = 7**;
  **MAX_VOUCHES_PER_DAY = 10** (anti-farming);
  **SCAM_REPORT_COOLDOWN_SECONDS = 60**. These are guesses for a ~175-member
  server — the owner should tune them. The daily vouch cap + account-age gates
  are deliberately conservative anti-sybil measures, not perfect ones (account
  age is farmable; see ISSUES.md for the server-tenure follow-up).
- **Default channel names** assumed: `trade-portal`, `vouch-trades`, `modlog`,
  `leaderboard`, `sprite-list`, `gold-zp-list`, `welcome`. Owner can rename in
  config and re-run `/setup`.
- **7 sprite roles + Gold variants** seeded from the spec: Zero Point, Dream,
  Punk, King, Ghost, Demon, Duck. Fire/Earth/Water are starters (no role).

## Permissions
- **Admin = configured OWNER_IDS/ADMIN_IDS, OR the Owner/Admin roles, OR Discord
  Manage Server/Administrator perms.** Belt-and-suspenders so the team isn't
  locked out. Owner/Admin roles are never auto-stripped (only flair + verified
  roles are managed).

## Trades
- A **trade only counts when BOTH parties confirm** (anti-scam). On completion
  the bot prompts both to vouch but does **not** auto-vouch (vouching stays a
  deliberate act). Either party or an admin can cancel.
- Trade descriptions are **free text** ("you_give"/"they_give") rather than a
  fixed sprite picker, because trades can involve quantities, Gold variants, or
  multi-item swaps.

## Insights
- **AI-free by counting only.** "Most-requested" uses a simple keyword regex
  (`want|wtb|lf|looking for|need|needing`) intersected with sprite-name matches.
  It's a heuristic, clearly labeled as approximate. Requires Message Content Intent.

## Hosting doc
- Free tiers and VPS pricing **verified via web search on 2026-06-08** (Oracle
  Always Free, Bot-Hosting.net, Pella, Hetzner CX22, DigitalOcean). HOSTING.md
  tells the reader to re-check live pages since prices drift.

## Out of scope (intentionally)
- No reaction roles (server uses Discord Onboarding — explicit requirement).
- No V-Bucks/price fields anywhere (server rule). The rule is surfaced in
  welcome + trade messages.
- See [ISSUES.md](ISSUES.md) for deferred niceties.
