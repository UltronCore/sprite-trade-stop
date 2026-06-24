# How to Use Every Feature — Sprite Trade Stop Bot

Plain-English guide for the owner. Each feature shows **who uses it**, **exactly
what they type or click**, and **what happens**. Commands are slash commands
(type `/` in Discord and pick from the list). Most replies are **private**
(only you see them) so channels stay clean.

> One-time setup is in [README.md](README.md) → run **`/setup`** once and it wires
> the bot to your channels and roles automatically.

**Quick legend:** 👤 anyone · 🎁 distributor (queue staff) · 🛡️ admin

---

## 🖱️ The Control Panel — start here

**`/panel`** 🛡️ → posts a pinned message of buttons. **Pin it.** From then on
members rarely type anything — they click:

| Button | What it does |
|---|---|
| 📇 **My Collection** | Shows their collection as an image (private) |
| 🔎 **Find Trades** | Lists members who have the sprites they're missing |
| 📋 **My Queues** | Their spots in any hand-off lines |
| ➕ **Join a Queue** | A dropdown of open queues — pick one to join |
| 🔄 **Sync** | A pop-up box to paste their tracker code |
| 🎮 **Open Tracker** | Link to the collection website |

*Example:* a new member clicks **🔄 Sync**, pastes their code, then **📇 My
Collection** to see their card — all without typing a command.

---

## 📒 Collection tracking

The flow: members mark sprites on the **website**, copy a code, and the bot
imports it. Then the bot can show images, find trades, and auto-give roles.

| Command | Who | What they do | What happens |
|---|---|---|---|
| `/synccollection <code>` | 👤 | Paste the code from the tracker's **Copy sync code** button (or click 🔄 Sync on the panel) | Bot saves their full collection. "Synced! 31/41" |
| `/mycollection [@user]` | 👤 | — | Posts the green collection image |
| `/missing [@user]` | 👤 | — | Posts the red "looking for these" image |
| `/grid [@user]` | 👤 | — | Posts the `NORMAL\|GOLD\|GUMMY\|GALAXY ✅/❌` **text grid** people type by hand |
| `/spriteset <name> <status>` | 👤 | Update one sprite ("just got Galaxy Duck") | Updates it without re-syncing the whole thing |
| `/spriteprivacy <visible>` | 👤 | Hide their collection from server features | They become invisible to `/holders`, leaderboard, etc. |

*Example:* instead of typing out a grid in `#trade-portal-1`, a member runs
`/grid` and the bot posts a clean owned/missing grid in one click.

---

## 🔎 Finding trades & who-has-what

| Command | Who | What it shows |
|---|---|---|
| `/spritematch` | 👤 | Members who have the sprites **you** are missing, ranked |
| `/holders <sprite>` | 👤 | Who (that synced) owns a given sprite — find a trade partner |
| `/spriteinfo <name>` | 👤 | A sprite's image, rarity, variant line, and who owns it |
| `/guildprogress` | 👤 | Server-wide stats: members synced, average %, most-needed sprites, top collectors |
| `/whohas` `/whoneeds` `/match` | 👤 | Same idea but from **Discord roles** (onboarding), for sprites without a synced collection |

*Example:* a member missing Galaxy Dream runs `/holders galaxy dream` and DMs
someone from the list to set up a trade.

---

## 🏅 Collector roles (automatic — the big one)

The bot **auto-gives the milestone roles you currently hand out by hand**, based
on a member's synced collection. No manual checking.

| Role (rename in config to match yours) | Earned when they have… |
|---|---|
| **All Gold** | every Gold sprite |
| **Galaxy / Gummy Sprite Collector** | every Galaxy / Gummy sprite |
| **Mythic / Epic Sprite Collector** | every Mythic / Epic sprite |
| **Peanut Collector** | Burnt Peanut |
| **Superior Sprite Collector** | the full collection |
| **Mastered Em' All / 15 Sprites Mastered** | all / 15 mastered |
| **Almost Complete** | missing ≤3 (gate a `#pro-traders` channel by this) |

- It re-checks **every time** they sync, use `/spriteset`, or receive a queue
  hand-off. Members can force a re-check with **`/collectorroles`**.
- It only ever adds/removes these specific roles — never touches anything else.
- **Setup:** make sure your role names match `config.COLLECTOR_ROLES`, then
  `/setup`, and put the **bot's role above** the collector roles.

*Example:* a member syncs with all 10 Galaxy sprites → the bot instantly gives
them **Galaxy Sprite Collector**. Trade one away and re-sync → it's removed.

---

## 📋 Hand-off queues (giving out rare sprites fairly)

Replaces the old manual queue. A distributor gives a rare sprite to members one
at a time, in a fair line.

| Command | Who | What it does |
|---|---|---|
| `/queue open <sprite>` | 🎁 | Opens a queue **and posts a board** with Join/Leave buttons |
| (members click **Join** on the board, or `/queue join <sprite>`) | 👤 | Gets in line; shows their position |
| `/queue next <sprite>` | 🎁 | Pings whoever's at the front |
| `/queue done <sprite> @user` | 🎁 | Marks delivered — removes them, **auto-marks the sprite in their collection**, asks them to vouch |
| `/queue mine` `/queue list` | 👤 | Their positions / who's in a queue |
| `/queue skip` `/queue close` | 🎁 | Remove a no-show / close the queue |

Queues are **closed by default** — you open only the rare ones (Zero Point, John
Wick, etc.). *Example:* `/queue open zeropoint_galaxy` → members click Join →
`/queue next` pings #1 → after the drop, `/queue done zeropoint_galaxy @them`.

---

## 🎮 Sessions — custom games, hunts, dust farming

| Command | Who | What it does |
|---|---|---|
| `/session open <kind> [title] [slots]` | 👤 | Opens a lobby with a **Join** button + live roster. `slots:20` caps it |
| (members click **Join**) | 👤 | Fills the lobby |
| `/session teams <id> <count>` | host | Randomly splits everyone into teams (for the "Sprite War") |
| `/session list` `/session close <id>` | 👤/host | See open ones / end yours |

*Example (Sprite Royale):* `/session open "Custom Game" slots:20` → 20 people
click Join → `/session teams 2` → two teams of 10, ready to fight.

---

## 📅 Events & news

| Command | Who | What it does |
|---|---|---|
| `/events` | 👤 | Shows the weekly Sprite events (Mastery Monday / New Sprite Thursday / Saturday Power Hour) and highlights today |
| `/announcenew` | 🛡️ | Announces sprites added since last check to `#news` (pings the news role if set). Also runs automatically on restart after you add a sprite |
| `/tracker` | 👤 | Posts the link to the collection website |

*New sprites (e.g. June 25 drop):* flip them to released in the tracker data,
restart the bot → it auto-announces them in `#news`. (Steps in MAINTAINERS.md.)

---

## 🛡️ Admin tools

| Command | What it does |
|---|---|
| `/setup` | Auto-detects and binds your channels + roles by name. Run after any rename. Reports what's missing |
| `/digest on\|off\|now` | A weekly server-progress recap to `#sprite-digest` |
| `/postleaderboard` `/refreshlists` | Force the auto leaderboard / holder lists |
| `/blacklist` `/unblacklist` | Block a user from the system *(only if the vouch/scam side is enabled)* |

---

## ⚙️ Running alongside your existing Sprite bot

Your server already has the **Sprite** bot for vouches. To avoid two bots doing
the same thing, set in `config.py`:
```python
DISABLED_COGS = ["vouch", "scam"]   # their bot owns vouching + reports
```
This bot then runs only the parts theirs doesn't: **collection tracking, queues,
sessions, the panel, collector roles, and events.** Full breakdown in
[SERVER-CHECK.md](SERVER-CHECK.md).

---

## 🌐 The collection website
Members track sprites at **https://ultroncore.github.io/sprite-tracker/** — mark
Have/Missing/Mastered, filter by line, then **Copy sync code** and paste into
`/synccollection` (or the panel's 🔄 Sync). The bot reads that code; the two
always stay in sync. (Based on the community tracker by Rickventure —
[staticvacant/fnsprites](https://github.com/staticvacant/fnsprites).)
