# 4. Sprite Royale (Customs) event

**Suggested by:** PandaXLMX — a custom where teams fight for their sprite group;
teams of 10 (or 9 with Burnt Peanut); winner gets a "Winner of the Sprite War"
title. (The server has a **Customs** role + `#custom-games`.)

**Verdict:** ✅ **Built** — the `/session` system.

## Response (shipped)
Built as a generic **session** system (custom games, sprite hunts, dust farming),
with the queue cog's button UX:
- **`/session open <kind> [title] [slots]`** — host opens it (auto-joined) and
  posts an embed with **Join / Leave** buttons + a live roster. `kind` includes
  *Custom Game*; `slots:20` caps it (0 = unlimited).
- Members click **Join** until full (buttons persist across restarts).
- **`/session teams <id> <count>`** — host/admin randomly splits the roster into
  N teams for the "sprite war".
- **`/session list`** / **`/session close <id>`** to manage it.

**Server side:** the `Customs` role + `#custom-games` already exist, so it slots
straight in. (A temporary "Sprite War Winner" role via a `/session win` is an
easy follow-up — say the word.)
