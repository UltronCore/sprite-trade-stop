# 4. Sprite Royale (Customs) event

**Suggested by:** PandaXLMX — a custom where teams fight for their sprite group;
teams of 10 (or 9 with Burnt Peanut); winner gets a "Winner of the Sprite War"
title. (The server has a **Customs** role + `#custom-games`.)

**Verdict:** 🟡 Feasible — designed; build on request.

## Response (design)
A lightweight `/customs` flow, reusing the queue/session pattern already in the
bot:
- `/customs open <name> <slots>` (Customs host/staff) → posts an embed with a
  **Join** button and a live roster, like the queue board.
- Members click Join until slots fill; team auto-split (e.g. two teams of 10).
- `/customs win <team>` → posts the result; optionally grants a temporary
  "Sprite War Winner" role to that team (auto-removed next event).
- Closeable; logged.

This is ~1 small cog (mirrors `queue.py`). I didn't build it this turn to keep
the change focused on the high-value collector-role integration — **say "build
customs" and I'll add it** with the same button UX.

**Server side:** the `Customs` role + `#custom-games` already exist, so it slots
straight in.
