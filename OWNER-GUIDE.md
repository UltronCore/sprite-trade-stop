# Sprite Trade Stop Bot — Owner Guide

A plain-English walkthrough for the server owner: what the bot does and how to
add it. **Visual version (send this link):**
https://ultroncore.github.io/sprite-tracker/pitch/

---

## What it does (in one minute)

Five things, all inside Discord — members keep using the server normally, the
bot handles the rest:

1. **Trust & reputation** — members `/vouch` each other after good trades;
   vouches auto-promote them up flair ranks and earn the **verified-trader**
   role. `/profile`, `/rank`, `/leaderboard`.
2. **Safe two-party trades** — `/trade @user` only counts when **both** press
   Confirm, so nobody gets scammed on the in-game drop. Everything is logged.
3. **Collection tracking** — members track all 41 sprites on a companion
   website, then `/synccollection` into Discord. The bot makes shareable
   **collection** and **"looking for"** images automatically (`/mycollection`,
   `/missing`, `/spriteset`).
4. **Trade matchmaking** — the bot knows who has what: `/holders <sprite>`,
   `/spritematch` (who can complete your set), `/guildprogress`, `/spriteinfo`.
5. **Hand-off queues** — for rare sprites, a distributor gives them out one at a
   time in a fair line. `/queue open <sprite>` posts a board with a **Join**
   button members click; `/queue next` pings whoever's up; `/queue done @user`
   delivers it and auto-marks it in their collection. Open only the queues you
   want — closed by default.
6. **Safety + housekeeping** — `/reportscammer`, `/blacklist`, anti-alt checks,
   welcome messages, auto-updated holder lists, a daily leaderboard, an optional
   weekly digest (`/digest`), and a "new sprite released" announcement.

---

## How to add it — 6 steps (~30 min, no coding)

**1. Create the bot.** [Discord Developer Portal](https://discord.com/developers/applications)
→ **New Application** → name it → **Bot** → **Add Bot**.

**2. Turn on two intents.** On the **Bot** page → **Privileged Gateway Intents**
→ enable **Server Members Intent** and **Message Content Intent** → **Save**.

**3. Copy the token.** **Bot** page → **Reset Token** → **Copy**. Keep it secret
(it's the bot's password). You'll paste it once during hosting.

**4. Invite it.** **OAuth2 → URL Generator** → scopes **bot** +
**applications.commands** → permissions **Manage Roles, Send Messages, Embed
Links, Attach Files, Read Message History, Add Reactions** → open the generated
link → add to your server.
**⚠️ Then drag the bot's role ABOVE all sprite / Gold / flair / verified roles**
in Server Settings → Roles (a bot can only manage roles below its own).

**5. Host it 24/7.** Pick one (full steps in
[HOSTING.md](HOSTING.md)):
- **Oracle Cloud Always Free** — $0 forever, a real server (most setup).
- **Bot-Hosting.net** — free, easiest, web panel, no Linux.
- **Hetzner / DigitalOcean** — ~$4–5/mo, most reliable.
During hosting you paste the token from Step 3 into a `.env` file (or the panel).

**6. Run `/setup`.** In Discord, type `/setup` — the bot auto-detects your
channels and sprite/flair/verified roles by name and saves them, and reports
anything missing. Optionally `/digest on` for the weekly recap.

✅ Done — members can `/synccollection`, `/trade`, and `/vouch` immediately.

---

## The companion website
The collection tracker (members mark Have/Missing/Mastered, export images, copy a
sync code): **https://ultroncore.github.io/sprite-tracker/**

## Who does what
- **You, once:** the 6 steps above + keep the bot's role on top.
- **The bot, forever (automatic):** welcomes, runs trades/vouches/ranks, renders
  images, finds matches, updates lists, posts the leaderboard, announces new
  sprites, blocks scammers.

## Why it's safe to run
Free (no paid APIs), **locked to your one server**, anti-scam/anti-spam controls
(two-party confirms, account-age + tenure gates, cooldowns, blacklist), and fully
open-source with tests and a complete handoff guide
([ARCHITECTURE.md](ARCHITECTURE.md)).

---

*Full command reference: [README.md](README.md). How it all works:
[ARCHITECTURE.md](ARCHITECTURE.md). Sprite art © Epic Games (fan project).*
