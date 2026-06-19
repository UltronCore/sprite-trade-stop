# Sprite Trade Stop Cybersecurity QA

Date: 2026-06-19

Repo reviewed: `/Users/bryan/sprite-trade-stop`

Scope:
- security-focused QA only
- no bot code edits made in this pass
- reviewed command abuse, authorization, trust boundaries, storage isolation, input handling, and denial-of-service surfaces

## Validation Performed

Checks run:

```bash
cd /Users/bryan/sprite-trade-stop && ./.venv/bin/pytest
cd /Users/bryan/sprite-trade-stop && ./.venv/bin/ruff check
```

Results:
- `pytest`: 24 passed
- `ruff check`: clean

Manual security checks performed:
- malformed sync-code behavior
- authorization boundary review
- multi-guild isolation review
- privilege and role-resolution review
- abuse-path review for public commands and persistent views

## Executive Summary

This bot does **not** show signs of classic high-severity bugs like:
- remote code execution
- shell injection
- obvious SQL injection
- unsafe deserialization
- unrestricted file reads/writes from user input

That said, there are still several meaningful security and abuse flaws to fix.

The highest-priority issues are:
1. malformed collection sync codes are accepted as valid input
2. the database is not guild-scoped, so one guild can affect another if the bot is ever installed in multiple servers
3. several public commands can be spammed or abused because they have no cooldowns or abuse controls
4. trade and reputation flows are still too easy to game socially even after the recent QA hardening

## Findings

### 1. Malformed sync codes are accepted and stored
Severity: high

The sync-code decoder accepts obviously invalid data and silently turns it into a collection state instead of rejecting it.

Relevant code:
- [spritebot/sprites.py](/Users/bryan/sprite-trade-stop/spritebot/sprites.py:52)
- [spritebot/cogs/collection_sync.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/collection_sync.py:48)

Confirmed manually:
- `!!!!` decoded successfully
- `abc` decoded successfully
- malformed URLs carrying bad `c=` data also decoded successfully

Security impact:
- a malicious user can intentionally submit junk state
- users can accidentally poison their own collection profile
- fake collection state can distort `/holders`, `/spritematch`, `/guildprogress`, and `/spriteinfo`
- this weakens trust in the synced-collection subsystem

Why it happens:
- `base64.b64decode` is used leniently
- there is no payload-length validation
- there is no checksum/version/signature validation

Fix recommendation:
- use strict base64 validation
- reject payloads whose decoded length does not match the expected packed size for `SHARE_ORDER`
- consider adding a checksum or version marker to the sync format

### 2. No guild isolation in the database
Severity: high

The database schema stores vouches, trades, blacklists, scam reports, and collections without a `guild_id`. The code also queries these tables globally by user ID.

Relevant code:
- [spritebot/db.py](/Users/bryan/sprite-trade-stop/spritebot/db.py:45)
- [spritebot/db.py](/Users/bryan/sprite-trade-stop/spritebot/db.py:56)
- [spritebot/db.py](/Users/bryan/sprite-trade-stop/spritebot/db.py:69)
- [spritebot/db.py](/Users/bryan/sprite-trade-stop/spritebot/db.py:75)
- [spritebot/db.py](/Users/bryan/sprite-trade-stop/spritebot/db.py:85)

Security impact:
- if the bot is ever installed in multiple guilds, trust data leaks across tenants
- a blacklist in one guild affects the same user globally
- vouches earned in one guild inflate trust in another
- collections synced in one guild become visible to commands in another
- staff in one community can indirectly influence another community’s reputation model

This is a real isolation flaw, not just a product preference.

Fix recommendation:
- add `guild_id` to all guild-scoped tables
- include `guild_id` in all read/write queries
- migrate existing data carefully
- keep only genuinely global config global

### 3. Several public commands have no cooldowns or anti-spam controls
Severity: medium-high

Public commands like `/trade`, `/synccollection`, `/mycollection`, `/missing`, `/spriteinfo`, `/guildprogress`, and `/spritematch` can be invoked repeatedly without rate limiting.

Relevant code:
- [spritebot/cogs/trades.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/trades.py:121)
- [spritebot/cogs/collection_sync.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/collection_sync.py:48)
- [spritebot/cogs/collection_sync.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/collection_sync.py:63)
- [spritebot/cogs/collection_sync.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/collection_sync.py:68)
- [spritebot/cogs/collection_sync.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/collection_sync.py:123)
- [spritebot/cogs/collection_sync.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/collection_sync.py:182)
- [spritebot/cogs/collection_sync.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/collection_sync.py:216)

Security impact:
- channel spam in `trade-portal`
- repeated expensive image rendering via Pillow
- easy DB churn through repeated sync overwrites
- increased moderation load from nuisance activity

This is more of an abuse/availability flaw than a data breach flaw, but it matters in real Discord communities.

Fix recommendation:
- add per-user cooldowns on trade creation and sync-heavy commands
- add a soft rate limit for image-generation commands
- optionally dedupe or collapse repeated pending trades between the same users

### 4. Trade creation can be spammed without consent from the target user
Severity: medium

Any eligible member can open a `/trade` against another eligible member, which posts immediately into the trade channel and persists in the DB.

Relevant code:
- [spritebot/cogs/trades.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/trades.py:121)
- [spritebot/cogs/trades.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/trades.py:140)

Security impact:
- harassment/spam against a target user
- cluttering `trade-portal` with unsolicited requests
- easy creation of many pending trade records

This is especially relevant because the command causes a public side effect before the other party opts in.

Fix recommendation:
- rate-limit `/trade`
- block duplicate pending trades between the same pair
- consider a private request/accept flow before posting publicly

### 5. Reputation remains socially gameable despite recent hardening
Severity: medium

The recent QA pass improved a lot, but the core trust model can still be gamed by coordinated accounts over time.

Relevant code:
- [spritebot/cogs/vouch.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/vouch.py:26)
- [spritebot/helpers.py](/Users/bryan/sprite-trade-stop/spritebot/helpers.py:61)
- [spritebot/db.py](/Users/bryan/sprite-trade-stop/spritebot/db.py:199)

Security impact:
- coordinated groups can still manufacture reputation slowly
- account-age checks are not enough against prepared sockpuppets
- vouches are not tied to a specific completed trade

What is already good:
- daily vouch cap exists
- blacklist exists
- account-age gate exists

What is still weak:
- no join-tenure requirement
- no requirement that a vouch correspond to a completed trade
- no reciprocal-ring detection

Fix recommendation:
- require a completed trade relationship for vouch eligibility
- add minimum guild-join age
- add reciprocal or cluster-farming detection

### 6. Admin fallback by role name is still a weak authorization edge
Severity: medium-low

`settings.is_admin` falls back to role-name matching when setup has not yet saved owner/admin role IDs.

Relevant code:
- [spritebot/settings.py](/Users/bryan/sprite-trade-stop/spritebot/settings.py:73)

Security impact:
- before `/setup` is run, any role named `Owner` or `Admin` is trusted
- this creates room for accidental misconfiguration or weak server-side role design

This is not a trivial exploit because Discord role creation is itself privileged, but it is still a brittle authorization path.

Fix recommendation:
- disable role-name fallback entirely for admin authorization
- require explicit ID resolution through config or `/setup`

### 7. Public profile exposes blacklist state
Severity: low

`/profile` shows whether a user is blacklisted.

Relevant code:
- [spritebot/cogs/vouch.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/vouch.py:124)

Security impact:
- moderation state is publicly exposed to any user
- depending on community policy, this may be intended transparency or unnecessary disclosure

Fix recommendation:
- decide whether blacklist status should be public or admin-only
- if not public, hide it from general profiles

### 8. Insights can aggregate across every readable channel the bot can access
Severity: low to medium, context-dependent

`/insights` scans all text channels the bot can read and summarizes counts.

Relevant code:
- [spritebot/cogs/insights.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/insights.py:33)

Security impact:
- if the bot has access to staff/private channels, the resulting aggregate stats may reveal activity patterns from spaces users did not intend to include in generalized server analytics

Because the command is admin-only, this is not a direct public leak. It is more a scope-control concern.

Fix recommendation:
- allow an include/exclude list of channels
- or default to a configured public-trade subset

## Security Positives

The code already does several things right:

- Bot-wide mention suppression via `AllowedMentions.none()` is a strong default.
  - [bot.py](/Users/bryan/sprite-trade-stop/bot.py:42)
- Trade completion uses an atomic DB transition to avoid double-completion races.
  - [spritebot/db.py](/Users/bryan/sprite-trade-stop/spritebot/db.py:246)
- SQL queries use bound parameters in the risky places instead of string-built user input.
- No use of `eval`, `exec`, shelling out, pickle loading, or unsafe dynamic imports from user data.
- Scam report cooldown exists.
  - [spritebot/cogs/scam.py](/Users/bryan/sprite-trade-stop/spritebot/cogs/scam.py:31)
- Blacklisted users are excluded from leaderboard calculations.
  - [spritebot/db.py](/Users/bryan/sprite-trade-stop/spritebot/db.py:188)

## What I Did Not Find

I did **not** find evidence of:
- remote code execution paths
- shell command injection
- obvious SQL injection from user-controlled text
- arbitrary filesystem writes from command input
- direct token leakage in repo code
- dangerous YAML/pickle/object deserialization from user payloads

## Recommended Fix Order

1. Fix malformed sync-code acceptance.
2. Add guild scoping to the database model and queries.
3. Add cooldowns / anti-spam controls to public state-changing and rendering commands.
4. Tighten trade/vouch coupling to reduce reputation gaming.
5. Remove admin role-name fallback.
6. Decide whether blacklist state should be public.

## Verdict

Overall security verdict: **reasonably safe from classic code-execution flaws, but still vulnerable to trust abuse, cross-guild isolation issues, and spam/availability abuse**

This is a good base for a community bot, but it still needs another hardening pass before I’d call the trust and collection systems robust against hostile members.
