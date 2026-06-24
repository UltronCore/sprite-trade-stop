# Tracking every player's collection at scale (~5k) — feasibility

**Question:** can we have a tracker that knows what *all* players have (up to ~5k),
not just one person's localStorage — "make it better if feasible, if not naw"?

## Verdict: **already feasible — via the bot, not a new web backend.**

The right architecture is already in place:
- **Web tracker** (Rickventure's / this fork) = the *per-player editor*
  (localStorage, no login, free). It does NOT need to know about other players.
- **The bot** = the *shared, multi-player layer*. `/synccollection` stores every
  member's collection in SQLite, and `/holders`, `/spritematch`, `/guildprogress`,
  collector roles all query across **everyone**. That's the "what does everyone
  have" tracker — inside Discord, where the community already is.

### It scales to 5k comfortably (measured)
Loaded **5,000 members** with random collections (117k rows, 8.3 MB DB) and timed
the heaviest queries:

| Query | Median time @ 5k |
|---|---|
| insert 5,000 collections | 0.95 s (one-time) |
| `sprite_holders` (who has X) | **1.6 ms** |
| `collection_leaderboard` | **19 ms** |
| `have_counts` (guild progress / most-needed) | **41 ms** |
| `find_matches` (spritematch — full 5k scan) | **65 ms** |

All well under a slash-command's budget (and those commands `defer` anyway). SQLite
on free hosting handles this with huge headroom — 5k is not a concern; even 50k
would be fine for these query shapes.

## Why NOT a separate web backend ("naw")
A central *website* that tracks 5k players would need: a database **+** an auth
system (so people can't edit others' data) **+** a public API **+** anti-fake-data
moderation **+** paid hosting. That's real, ongoing infrastructure — and it would
**duplicate what the bot already does for free**. The bot already has identity
(Discord), storage (SQLite), and the cross-player queries.

**Recommendation:** keep the web tracker as the single-player editor (the server
officially uses Rickventure's — the bot decodes its share codes identically, so
don't fork the community away from it), and use **the bot** as the shared 5k
tracker. No new backend. If you ever outgrow SQLite (tens of thousands of *active
writers*), the same code moves to Postgres with a one-file change to `db.py`.
