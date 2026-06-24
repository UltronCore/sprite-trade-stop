# Feasibility: tracking what every player has, for ~5,000 members

**Question:** can we have a tracker that records what *all* players own (so anyone
can query who-has-what across the whole server), for up to ~5k players?

**Answer: yes — and it's already built into the bot. No separate web backend needed.**

## How it works today
- Members edit their collection on the web tracker → **Copy sync code** → `/synccollection`.
- The bot stores every member's collection in **SQLite** (`collections` table).
- Anyone can then query across everyone: `/holders <sprite>`, `/spritematch`,
  `/guildprogress`, the leaderboard, and collector roles — all server-wide.

The web page stays a simple static editor (per-browser); the **bot is the shared,
centralized store**. That's the part that makes it "multi-player".

## Load test (5,000 users, full collections)
Ran on the actual DB layer — 5,000 users, ~123,000 collection rows:

| Operation | Time |
|---|---|
| Insert all 5,000 users' collections | 0.20 s |
| `/holders` (who has a sprite — 3,026 holders) | **1.8 ms** |
| `/leaderboard` top 10 | **18 ms** |
| `have_counts` (powers `/guildprogress`) | **43 ms** |
| `/spritematch` (scans all 5,000 users) | **65 ms** |
| Whole DB file size | **9.1 MB** |

Everything is well under Discord's 3-second interaction window, with room to
spare. SQLite handles this size trivially; no Postgres/Redis/cloud DB required.

## Why NOT a separate web backend (the "if not, naw" path)
A web tracker that stores all players centrally would need: a database + an API +
accounts/auth + anti-cheat (people faking collections) + hosting/uptime. That's
real infrastructure and cost — and it would **duplicate** what the bot already
does for free. So: **naw** to a new web backend. The bot is the central tracker.

## If we ever DID outgrow it (we won't at 5k)
- The heavy op is `/spritematch` (full scan). At ~50k+ users you'd add an index
  or precompute matches on sync. Not needed anywhere near 5k.
- Backups: just copy the SQLite file (9 MB) — already documented in HOSTING.md.

## Suggesting edits to the original web tracker
The web tracker is **[staticvacant/fnsprites](https://github.com/staticvacant/fnsprites)**
(by Rickventure) — **public, Issues enabled**. To suggest changes: open a GitHub
**Issue** there, or fork → edit → **Pull Request** (note: no license, so it's
goodwill). Our bot already speaks its exact share-code format, so the two stay
compatible regardless.
