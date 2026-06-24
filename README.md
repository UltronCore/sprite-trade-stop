# 🔁 Sprite Trade Stop

![CI](https://github.com/UltronCore/sprite-trade-stop/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2)

A custom, open-source Discord bot for **Sprite Trade Stop**, a Fortnite sprite
**trading** community with a trust/vouch economy. Sprites are traded for sprites
— **never** sold for V-Bucks (server rule, enforced in messaging). Built to be
**free to run** (no paid AI APIs), beginner-friendly, and to work *with* the
server's existing Discord Onboarding roles instead of duplicating them.

> ### 📖 Owner — read this first: **[USAGE.md](USAGE.md)**
> A plain-English guide to **every feature**: who uses it, exactly what to type or
> click, and what happens. Start there.
>
> Other docs: visual walkthrough → **https://ultroncore.github.io/sprite-tracker/pitch/**
> · community suggestions + responses → **[suggestions/](suggestions/)**
> · pre-deploy inspection (view-only) → **[SERVER-CHECK.md](SERVER-CHECK.md)**.

> **Server owner?** The quickest tour is the visual walkthrough → **https://ultroncore.github.io/sprite-tracker/pitch/** (or the text version, [OWNER-GUIDE.md](OWNER-GUIDE.md)).
>
> **New here (owner or a future maintainer)?** This README gets you running.
> For the full "what it does and how it works" — every subsystem, the data
> model, and how to extend it — read **[ARCHITECTURE.md](ARCHITECTURE.md)**.
> For day-to-day maintenance, **[MAINTAINERS.md](MAINTAINERS.md)**.

### How it fits together (30-second version)
- **Web tracker** ([sprite-tracker](https://ultroncore.github.io/sprite-tracker/)) = the *editor*: members mark Have/Missing/Mastered on a grid and click **Copy sync code**.
- **This bot** = the *social layer*: `/synccollection <code>` imports it, then the bot renders collection images, finds trade matches, and runs the vouch/trust economy — all in Discord.
- Two collection sources by design: **onboarding roles** (coarse/public — `/whohas`, `/whoneeds`, `/match`) and **synced collections** (full — `/holders`, `/spritematch`, `/guildprogress`, …). See [ARCHITECTURE.md §2](ARCHITECTURE.md).

---

## ✨ Features

**Vouch + reputation (core)**
- `/vouch @user [proof] [note]` — each vouch gets a unique ID, optional proof link, timestamp. The `+rep @user [note]` text alias does the same but takes only an optional note (attach a proof link with `/vouch`). A per-member daily vouch cap (`MAX_VOUCHES_PER_DAY`) limits farming.
- Trust tiers from vouches received; **auto-assigns `verified-trader`** at a configurable threshold.
- `/profile [@user]` — vouches, trust, XP/rank, flair, completed-trade history.
- `/rank [@user]`, `/leaderboard`, plus a **daily leaderboard** auto-posted to a channel.
- Admins can `/editvouch <id>` or `/removevouch <id>` (soft delete keeps history; roles recalc automatically).

**Vouch-driven XP + flair ladder** (auto-assigned roles)
- XP earned **only by receiving vouches** (configurable per vouch — *no chat XP*).
- Flair ladder, all thresholds tunable: **Newbie** (on join) → **Trader** → **Verified Trader** → **Veteran** → **Max Helper**. A member holds exactly the highest flair they've earned.
- Static **Owner**/**Admin** roles are recognized for permissions and **never auto-stripped**.

**Trades (two-party, anti-scam)**
- `/trade @user you_give they_give` posts an embed in `#trade-portal` with **Confirm** buttons for both parties. It only counts once **both** confirm, then prompts both to vouch. Buttons survive restarts.

**Scam protection**
- `/reportscammer @user proof` → routed to `#modlog`. `/blacklist` / `/unblacklist` (admin) block users from the system. Configurable **minimum account age** to vouch.

**Collection lookup (reads existing Onboarding roles — no reaction roles)**
- `/whohas <sprite> [gold]`, `/whoneeds <sprite>`, `/match` (HAVE ↔ NEED pairing).
- Auto-maintained `#sprite-list` and `#gold-zp-list`, refreshed on a timer.

**Auto-assigned collector roles** 🏅
- The bot grants milestone roles **automatically** from synced collections — All Gold, Galaxy/Gummy/Mythic/Epic Sprite Collector, Mastered Em' All, 15 Sprites Mastered, Peanut Collector, Superior Sprite Collector — the same roles the server gives by hand. Re-checked on every sync, `/spriteset`, queue hand-off, or `/collectorroles`. Edit `config.COLLECTOR_ROLES` to match your exact role names.

**One-click control panel (no typing needed)**
- `/panel` posts a pinned hub of buttons: **My Collection**, **Find Trades**, **My Queues**, **Join a Queue** (dropdown of open queues), **Sync** (paste your code in a pop-up form), and **Open Tracker**. Members click instead of remembering slash commands. Buttons persist across restarts; replies are private (ephemeral) so channels stay clean.

**Sprite hand-off queues**
- A distributor gives a rare sprite to members one at a time, in a fair FIFO line. `/queue open <sprite>` opens a queue (closed by default — open only the ones worth queueing), and posts a live **board with Join/Leave buttons** members just click.
- `/queue next` pings the person at the front; `/queue done @user` removes them, **auto-marks the sprite as Have in their collection**, and nudges them to vouch. `/queue mine` shows everyone's positions.

**Insights (admin, AI-FREE)**
- `/insights [messages_per_channel]` scans recent message history (needs Message Content Intent; default 200 msgs/channel, clamped 20–1000) and reports **pure counts**: most-mentioned/most-requested sprites, busiest channels, most active members, open want-posts, top traders. No AI, no paid API.

**Welcome** — greets new members, assigns **Newbie**, and explains onboarding roles, safe trading, the no-V-Bucks rule, and how vouching/flair works.

---

## 🚀 Setup (step by step)

### 1. Create the bot
1. <https://discord.com/developers/applications> → **New Application**.
2. **Bot** → **Add Bot**. Under **Privileged Gateway Intents**, enable:
   - ✅ **Server Members Intent** (welcome + role logic)
   - ✅ **Message Content Intent** (the `+rep` alias and `/insights`)
3. **Reset Token** → **Copy** — keep it secret.

### 2. Invite the bot
- **OAuth2 → URL Generator** → scopes **`bot`** + **`applications.commands`**.
- Permissions: **Manage Roles**, **Send Messages**, **Embed Links**, **Read Message History**.
- Open the URL and add the bot.

> ⚠️ **The server owner (Manage Server + Manage Roles) must deploy it.** In **Server Settings → Roles**, drag the **bot's role ABOVE** all sprite, flair, and verified roles — Discord only lets a bot manage roles **below** its own.

### 3. Install & run
```bash
git clone https://github.com/UltronCore/sprite-trade-stop.git
cd sprite-trade-stop
python3 -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # paste your bot token after DISCORD_TOKEN=
python bot.py
```

### 4. Configure
1. Open **[`spritebot/config.py`](spritebot/config.py)** and set `GUILD_ID` and `OWNER_IDS` (Frosty's user ID). Adjust thresholds/role names if yours differ.
2. In Discord, run **`/setup`** (admin) — it **auto-detects** your channels and sprite/flair/verified roles by name and saves their IDs, so you don't hunt for them. It reports anything missing; create those and re-run `/setup`.

That's it. For 24/7 hosting (free **Oracle Cloud** or a ~$5/mo VPS), see **[HOSTING.md](HOSTING.md)**.

---

## 🧩 Command reference

| Command | Who | What |
|---|---|---|
| `/vouch @user [proof] [note]` · `+rep @user [note]` | anyone | Vouch for a trader (`+rep` = note only) |
| `/profile [@user]` · `/rank [@user]` | anyone | Reputation / progression |
| `/leaderboard` | anyone | Top traders by vouches |
| `/trade @user you_give they_give` | anyone | Two-party confirmed trade |
| `/whohas` · `/whoneeds` · `/match` | anyone | Collection lookup from roles |
| `/synccollection <code>` | anyone | Import your collection from the [web tracker](https://ultroncore.github.io/sprite-tracker/) sync code |
| `/mycollection` · `/missing` | anyone | Bot-rendered collection / wishlist image |
| `/holders <sprite>` · `/spritematch` | anyone | Find trade partners from synced collections |
| `/spriteinfo <name>` | anyone | Look up a sprite: image, rarity, line, who has it |
| `/spriteset <name> <status>` | anyone | Quick single-sprite update without the web |
| `/guildprogress` | anyone | Server-wide completion, most-needed sprites, top collectors |
| `/queue join \| leave \| mine \| list` | anyone | Wait in line for a sprite hand-off (or click **Join** on a board) |
| `/queue open \| close \| next \| done \| skip \| board` | distributor | Run a hand-off queue: open it, ping next, mark delivered |
| `/collectorroles` | anyone | Re-check & apply your collector milestone roles |
| `/grid` | anyone | Post your collection as a text grid (for trade channels) |
| `/session open\|list\|teams\|close` | anyone | Host a custom game / hunt; auto-split teams |
| `/spriteprivacy <visible>` | anyone | Hide/show your collection in server features |
| `/digest on\|off\|now` | admin | Weekly low-noise guild sprite digest |
| `/announcenew` | admin | Announce sprites added since the last baseline |
| `/panel` | admin | Post the one-click **control panel** (pin it) |
| `/events` | anyone | Weekly Sprite events (Mastery Monday / New Sprite Thursday / Power Hour) |

Public and image-rendering commands have per-user **cooldowns** to prevent spam.
The bot is **single-guild** (`GUILD_ID`) and refuses commands from other servers.

> **Running another vouch bot already?** Set `config.DISABLED_COGS = ["vouch", "scam"]`
> to run only the collection / queue / panel / events side and avoid overlap.
> Before deploying, work through **[SERVER-CHECK.md](SERVER-CHECK.md)** — a
> concrete inspection checklist (channel/role names, bot role position, overlap).
| `/reportscammer @user proof` | anyone | Report to modlog |
| `/editvouch` · `/removevouch` | admin | Manage vouches |
| `/blacklist` · `/unblacklist` | admin | Block from the system |
| `/insights [messages_per_channel]` | admin | AI-free analytics |
| `/setup` | admin | Auto-detect & save channel/role IDs |
| `/refreshlists` · `/postleaderboard` | admin | Force the auto tasks |

---

## 🛠️ Maintenance
- **Update safely:** `./update.sh` (records the current commit for rollback, pulls, reinstalls deps, restarts the service). Rollback instructions print at the end and live in [HOSTING.md](HOSTING.md).
- **CI:** every push runs ruff lint + pytest (`.github/workflows/ci.yml`).
- **Versioning:** semantic tags (`v1.0.0`). See [CHANGELOG.md](CHANGELOG.md).
- **Known limitations / TODOs:** [ISSUES.md](ISSUES.md).
- **Architecture & how to extend:** [MAINTAINERS.md](MAINTAINERS.md). **Assumptions made during the build:** [DECISIONS.md](DECISIONS.md).

MIT licensed.
