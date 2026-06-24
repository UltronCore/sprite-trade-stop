# Architecture & Handoff — Sprite Trade Stop

Everything this bot does, and how, written so a brand-new maintainer (or a fresh
AI session with **zero prior context**) can pick it up. Read this once top to
bottom and you'll understand the whole system.

---

## 1. What this is

A Discord bot for the **Sprite Trade Stop** Fortnite sprite-trading community.
It does four things:

1. **Trust & trading** — members vouch for each other and run confirmed two-party
   trades; trust drives flair roles.
2. **Collection tracking** — members sync their sprite collection from a companion
   web app, and the bot stores, renders, and trade-matches on it.
3. **Coordination** — server-wide progress, "who has X", "who can complete my set".
4. **Housekeeping** — onboarding-role lookups, welcome, scam reporting, a weekly
   digest, and new-sprite announcements.

It is **single-guild by design** (one configured server), **free to host**
(Python + SQLite, no paid APIs), and pairs with a separate static web tracker.

### The two halves
| Piece | Repo | Role |
|---|---|---|
| **Web tracker** | `UltronCore/sprite-tracker` (GitHub Pages) | The *editor*: a grid where members mark Have/Missing/Mastered and export images. Static, localStorage, no backend. |
| **This bot** | `UltronCore/sprite-trade-stop` | The *social layer*: imports collections via a share code, renders images in Discord, trade-matches, runs the trust economy. |

They're linked by a **share code** (see §6). The bot bundles
`spritebot/assets/sprites.json`, generated from the web app's data, so the sprite
order/encoding is identical on both sides and can't drift.

---

## 2. Two collection "truth" models (read this)

There are **two independent sources of collection data**, used by different
commands. This is intentional, but you must know which is which:

| Source | What it is | Commands that use it |
|---|---|---|
| **Onboarding roles** | Discord roles the server assigns via Onboarding (7 sprites + Gold). A *coarse, public* signal of what someone has. | `/whohas`, `/whoneeds`, `/match`, the auto `#sprite-list` / `#gold-zp-list` |
| **Synced collection** | The *full* 41-sprite collection a member imported with `/synccollection` (Have/Missing/Mastered). Stored in the `collections` table. | `/holders`, `/spritematch`, `/spriteinfo`, `/guildprogress`, `/mycollection`, `/missing`, `/spriteset`, the digest |

**Rule of thumb:** *roles = quick public trade intent; sync = full private-ish
collection truth.* They can disagree (a member may have roles but never synced,
or vice-versa). The role-based commands now only count members who hold ≥1 sprite
role as "participating", so non-onboarded members don't show as needing everything.

If you ever unify them, make synced collections canonical and *derive* the role
view — don't try to keep two writable sources in lockstep.

---

## 3. File map

```
bot.py                       entry: intents, single-guild guard, error handler,
                             load cogs, sync slash commands, run
spritebot/
  config.py                  ALL owner-tunable settings (IDs, names, thresholds,
                             cooldowns, channel names)
  db.py                      SQLite layer — the single source of truth
  sprites.py                 bundled catalog + STRICT share-code decode/encode
  progression.py             PURE xp/flair/tier math (no Discord, no DB)
  settings.py                resolve channel/role IDs (DB override > config); is_admin
  helpers.py                 apply_progression(), eligibility (age/tenure/blacklist),
                             rate-limit, role stripping
  collector.py               auto-assign collector milestone roles from a
                             collection (All Gold / Galaxy Collector / Mastered…)
  render.py                  Pillow renderer for collection/wishlist images
  assets/
    sprites.json             catalog generated from the web app's data.js
    sprites/<id>.png         54 sprite images (used by render.py + /spriteinfo)
  cogs/
    vouch.py                 /vouch, +rep, /profile, /rank, /leaderboard, edit/remove
    trades.py                /trade + persistent Confirm/Cancel buttons
    scam.py                  /reportscammer, /blacklist, /unblacklist
    collection.py            role-based /whohas /whoneeds /match + auto lists + /tracker
    collection_sync.py       sync-based /synccollection /mycollection /missing
                             /holders /spriteinfo /spriteset /spriteprivacy
                             /guildprogress /spritematch + build_progress_embed()
    queue.py                 /queue group (join/leave/mine/list/open/close/next/
                             done/skip/board) + persistent Join/Leave buttons
    hub.py                   /panel control panel: persistent button hub + sync
                             modal + join-queue dropdown (click instead of type)
    events.py                /events weekly Sprite events (Mon/Thu/Sat cadence)
    insights.py              /insights (AI-free message counts)
    welcome.py               on_member_join: Newbie flair + welcome embed
    admin.py                 /setup, /digest, /announcenew, /postleaderboard,
                             and ALL background jobs
tests/                       pytest: progression, db, share-code, command registration
```

---

## 4. Data model (SQLite, `sprite_trade_stop.db`)

| Table | Purpose | Key columns |
|---|---|---|
| `settings` | key/value config written by `/setup` + flags (`digest_enabled:<gid>`, `seen_released`) | key, value |
| `reputation` | *(legacy, vouch counts derive from `vouches`)* | — |
| `vouches` | every vouch (soft-deleted for audit) | voucher_id, target_id, note, proof, created_at, removed |
| `trades` | two-party trades + confirm state | party_a, party_b, give_a, give_b, status, a_confirm, b_confirm, message_id |
| `blacklist` | members blocked from the system | user_id, reason, at |
| `scam_reports` | reports routed to modlog | reporter_id, target_id, proof, at |
| `collections` | synced sprite collection (status 1=have, 2=mastered; 0 not stored) | user_id, sprite_id, status |
| `collection_private` | members opted out of guild-visible features | user_id |
| `queues` | hand-off waiting lines (FIFO by autoincrement `id`) | id, sprite_id, user_id, joined_at |
| `open_queues` | which queues currently accept joins (closed by default) | sprite_id, opened_at |

**Everything reputation-related is derived from `vouches`** — there's no cached
XP. `db.vouch_count()` → `progression.*` → `helpers.apply_progression()` applies
flair + verified roles. Edit/remove a vouch and re-apply; it stays consistent.

**All guild-visible collection queries exclude `collection_private` members.**

---

## 5. The trust economy (vouch → flair)

- A vouch is gated by `helpers.eligible_to_vouch` (not blacklisted, account ≥
  `MIN_ACCOUNT_AGE_DAYS`, joined ≥ `MIN_GUILD_TENURE_HOURS`), a global daily cap
  (`MAX_VOUCHES_PER_DAY`), and a **per-pair cooldown** (`VOUCH_PAIR_COOLDOWN_HOURS`)
  so repeat partners keep earning trust without instant ring-farming.
- Vouch count → XP (`XP_PER_VOUCH`) → flair tier (`FLAIR_TIERS`) and the
  `verified-trader` role at `VERIFIED_TRADER_THRESHOLD`. Tiers: Newbie → Trader →
  Verified Trader → Veteran → Max Helper.
- `helpers.apply_progression(member)` recomputes and applies roles. It only ever
  touches flair + verified roles — never Owner/Admin/sprite roles.

## 6. The web ↔ bot bridge (share code)

The web tracker encodes a collection as **2 bits per sprite** (0/1/2) over a fixed
`share_order`, packed 4 per byte, base64url, no padding (≈19 chars for 54 sprites).
`sprites.py` decodes it with **strict validation** (charset, exact length, valid
status values). `sprites.json` is generated from the web `data.js`, guaranteeing
identical order. `sprites.encode()` is the inverse and round-trips byte-for-byte.

Flow: member edits on the web → **Copy sync code** → `/synccollection <code>` →
`db.set_collection()`. Pull-based (re-paste to update) — deliberate, so the web
side stays a free static site with no backend.

## 6b. Hand-off queues (`queue.py`)

A distributor gives a sprite to members one at a time, in a fair FIFO line.
- `open_queues` controls which queues accept joins (closed by default — open only
  the rare ones). `queues` is the line, ordered by autoincrement `id` so
  same-second joins still get correct positions.
- Members join via `/queue join` **or** by clicking **Join** on a board posted by
  `/queue open`/`/queue board`. The buttons are **persistent dynamic items**
  (`QueueJoinButton`/`QueueLeaveButton`, registered in the cog's `setup` via
  `bot.add_dynamic_items`) so they keep working after a restart — the sprite id is
  encoded in the button's `custom_id` (`queue:join:<sprite>`).
- `/queue next` pings the head of the line; `/queue done @user` removes them,
  **flips that sprite to Have in their synced collection**, and prompts a vouch.
- Joining reuses `helpers.eligible_to_vouch` (blacklist/age/tenure) and a
  per-member max-queues cap.

## 7. Image rendering

`render.py` (Pillow) draws the same "My Collection" (green) / "Looking For" (red)
cards the web exports, from `assets/sprites/<id>.png`, and returns PNG bytes the
bot attaches to a message. Used by `/mycollection`, `/missing`, `/spriteinfo`,
and the new-sprite announcement.

## 8. Background jobs (all in `admin.py`, all `wait_until_ready` + error-guarded)

| Job | Schedule | Does |
|---|---|---|
| `periodic_refresh` | every `LIST_REFRESH_MINUTES` | rebuilds `#sprite-list` / `#gold-zp-list` from role membership (edits its own message) |
| `daily_leaderboard` | fixed **18:00 UTC** | posts the rep leaderboard |
| `weekly_digest` | every `DIGEST_INTERVAL_HOURS` | posts guild sprite progress **if** `/digest on` for that guild |
| `announce_new_releases_once` | once after startup | diffs released catalog vs `seen_released`; announces new sprites to `#news`; first run just sets a baseline |

## 9. Safety & abuse controls

- **Single-guild guard** (`bot.py`): interactions outside `GUILD_ID` are refused.
- **`AllowedMentions.none()`** bot-wide; trades ping only the two parties.
- **Cooldowns** on public/image commands; a global `tree.on_error` handles them.
- **Atomic trade completion** (`db.complete_if_both_confirmed`) — no double-count.
- **Strict sync-code validation**, blacklist enforcement, scam-report cooldown,
  admin = IDs/Discord-perms only (no role-name trust), privacy opt-out.

## 10. How to extend

- **New sprite / variant ships:** edit the web `data.js` (+ add `sprites/<id>.png`),
  regenerate `assets/sprites.json` (see MAINTAINERS), restart the bot → it
  auto-announces via `announce_new_releases_once`. Slash autocomplete for sprites
  is generated from `sprites.released()`, so no per-sprite code.
- **New flair tier / threshold / cooldown:** all in `config.py`; create the
  Discord role and run `/setup`.
- **New command:** add a method to the right cog. If it changes vouches, call
  `helpers.apply_progression`. Gate admin commands with `settings.is_admin`. Add
  the command name to `tests/test_commands.py::EXPECTED`.

## 11. Run / deploy / test

- Local: `pip install -r requirements.txt`, `cp .env.example .env` (token),
  `python bot.py`. See README for the Developer Portal steps (needs Server
  Members + Message Content intents; bot role above sprite/flair roles).
- Hosting: see [HOSTING.md](HOSTING.md) (free Oracle Always Free or ~$5/mo VPS).
- Tests/CI: `ruff check .` + `pytest` run on Python 3.10/3.11/3.12 via
  `.github/workflows/ci.yml`. `test_commands.py` asserts the full command set
  registers — keep it updated when adding/removing commands.

## 11b. Feature toggles & roster growth
- **`config.DISABLED_COGS`** — cog short-names to skip at load (filtered in
  `bot.py setup_hook`). Use `["vouch","scam"]` when another bot owns vouching.
- **Adding sprites:** append to the web `data.js` at the END (preserves share
  codes), regenerate `assets/sprites.json`, drop images in `assets/sprites/`.
  `sprites.decode` is roster-growth-safe: shorter (older) codes still decode,
  new sprites default to missing. Released total is gated by `unreleased:false`.

## 12. Known limits (see ISSUES.md)
Single-guild only (by design); collection sync is pull-based; reciprocal-ring
detection and per-level (0–5) tracking are deferred; `/match` pairing is
order-based, not optimized.
