# 1. Sprite News channel + ping role

**Suggested by:** Jaxlax410 — "We should have a separate 'Sprite News' channel
where news specifically about sprites is posted, with its own ping role."

**Verdict:** ✅ Built (bot covers the ping side).

## Response
The server already has `#news`. The bot's **`/announcenew`** (and the automatic
"new sprite released" check) posts new-sprite announcements there and now **pings
a configurable role**:
- Set `config.NEWS_PING_ROLE_NAME = "Sprite News"` (your exact role name).
- Create that role as self-assignable (via Onboarding / a reaction-role bot).
- Run `/setup` — the bot binds it and pings it on every new-sprite drop.

If you want sprite news in a dedicated channel separate from general `#news`,
create `#sprite-news` and point `config.CHANNELS["news"]` at it.

**Not handled by the bot:** general (non-sprite) Fortnite news — that's a
separate feed (e.g. the FortniteLeaks follow already in `#news`).
