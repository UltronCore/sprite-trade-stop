# Server Inspection Checklist — Sprite Trade Stop

What to verify inside the Discord before/while deploying the bot. Grounded in the
channels/roles observed in the server as of 2026-06-24. Work top to bottom; most
issues are "a channel/role name doesn't match what the bot expects" — fixable by
renaming, creating, or just running `/setup`.

> **Run `/setup` first** — it auto-binds whatever it can find by name and tells
> you exactly what's missing. This checklist is for the gaps it can't fix alone.

---

## 1. Channel name reconciliation (most important)

The bot looks for channels by the names in `config.CHANNELS`. The server's real
channels differ in places — decide per row: **rename the channel**, **create it**,
or **point the bot at it** (edit `config.CHANNELS` then `/setup`).

| Bot expects (`config`) | Seen in server | Action |
|---|---|---|
| `trade-portal` | **trade-portal-1**, trade-portal-2, galaxy-sprite-trade-portal | Set config `trade_portal` → `trade-portal-1` (or rename) |
| `vouch-trades` | **vouch-trades** ✓ | OK |
| `news` | **news** ✓ | OK |
| `welcome` | **welcome** ✓ | OK |
| `sprite-queue` | **galaxy-sprite-queue-system** | Set config `queue` → that name, or make a `#sprite-queue` |
| `modlog` | *(not seen)* | Create a private `#modlog` for scam reports |
| `leaderboard` | *(not seen)* | Create one, or it falls back gracefully |
| `sprite-list` / `gold-zp-list` | *(not seen)* | Create if you want the auto holder lists |
| `sprite-digest` | *(not seen)* | Optional — only if you turn on `/digest on` |

- [ ] Decided each channel above (rename / create / config)
- [ ] `show-collection` exists ✓ — point `/mycollection` users there
- [ ] Re-ran `/setup` after any change; "Found" list looks complete, "Missing" is acceptable

## 2. Roles

- [ ] **7 sprite roles + Gold variants** exist (Zero Point, Dream, Punk, King, Ghost, Demon, Duck — base + "(Gold)") and are assigned via **Onboarding** (verify a test member can pick them)
- [ ] **verified-trader** role exists ✓ (seen)
- [ ] **Distributor** role exists (for queue staff) — create if missing; `/setup` binds it
- [ ] **Flair roles** exist if you want the ladder: Newbie / Trader / Verified Trader / Veteran / Max Helper (or set `config.FLAIR_TIERS` to your real names)
- [ ] **Owner / Admin** roles exist and are bound by `/setup` (so admin auth uses IDs, not names)
- [ ] Confirm new upcoming sprites — do you want roles for Striker/Fishy/Aura/Boss/Grim Reaper/John Wick when they drop **June 25**? (the web tracker handles them with no roles needed)

## 3. Bot placement & permissions

- [ ] The **bot's role is ABOVE** every sprite/Gold/flair/verified/Distributor role (Server Settings → Roles) — else role assignment silently fails
- [ ] Bot has: **Manage Roles, Send Messages, Embed Links, Attach Files, Read Message History, Add Reactions**
- [ ] In the Developer Portal: **Server Members Intent** + **Message Content Intent** are ON (can't verify from the server side — check the portal)
- [ ] `config.GUILD_ID` is set to this server's ID (the bot refuses other guilds)

## 4. The server's OWN vouch bot (overlap decision) ⚠️

The server now runs its own vouch/sprite bot. Decide how to avoid two bots doing
the same thing:

- [ ] Identify the other bot and list its commands (does it do vouches? trades? leaderboard?)
- [ ] If it **covers vouches**, set `config.DISABLED_COGS = ["vouch", "scam"]` so this bot runs only the **collection / queue / panel / events** side (which the other bot doesn't do). Keep `trades` if the other bot has no two-party confirm flow.
- [ ] Confirm no command-name collisions (e.g. both have `/vouch` or `+rep`) — if they collide, disable mine for that feature
- [ ] Tell members which bot to use for what (pin it / put in `#roles-info`)

## 5. Smoke-test each feature (after setup)

- [ ] `/panel` → posts the control panel; pin it. Click every button: My Collection, Find Trades, My Queues, Join a Queue, Sync (modal), Open Tracker
- [ ] `/synccollection <code>` with a real code from the tracker → "Synced! X/41"
- [ ] `/mycollection` and `/missing` → images render
- [ ] `/queue open zeropoint_galaxy` → board posts with Join/Leave buttons; click Join; `/queue next`; `/queue done @you` (check it marked the sprite in your collection)
- [ ] `/spriteinfo`, `/holders`, `/spritematch`, `/guildprogress`
- [ ] `/events` → shows the weekly schedule, highlights today
- [ ] `/tracker` link works; welcome message fires on a test join
- [ ] If trust cogs enabled: `/vouch`, `+rep`, `/trade`, `/leaderboard`, `/reportscammer`

## 6. New-sprite readiness (June 25 "Gone Wild" drop)

- [ ] When Striker/Fishy/Aura/Boss/Grim Reaper go live, flip them to `unreleased: false` in the tracker `data.js`, regenerate `sprites.json` (see MAINTAINERS), restart the bot → it auto-announces them in `#news`
- [ ] Same for **John Wick** when it lands (date TBD)
- [ ] Confirm `#news` is the channel the announcement should post to (config `news` ✓)

## 7. Housekeeping observations to confirm

- [ ] Is the **old manual queue** (`galaxy-sprite-queue-system`, `queue-system-faq`) being retired in favor of `/queue`? If so, archive those channels or repurpose one as the bot's queue channel
- [ ] `community-sprites`, `collect-your-sprites` channels — any overlap with bot features? (these look like other-bot/manual systems)
- [ ] Boost level (33 boosts seen) → sticker/emoji slots if you also use the emoji-studio skill

---

### Quick verdict template (fill in during inspection)
- Channels matched/created: ___ / needs work: ___
- Roles OK: ___ / missing: ___
- Bot role above sprite roles: Y / N
- Other vouch bot overlap → DISABLED_COGS = ___
- Commands smoke-tested OK: ___ / broken: ___
