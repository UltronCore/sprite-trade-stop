# Maintainers Guide

Written so a brand-new person — or a fresh AI session with **zero prior
context** — can pick this up and keep building. Read top to bottom once.

> **Start with [ARCHITECTURE.md](ARCHITECTURE.md)** — the complete "what it does
> and how" map (subsystems, data model, web↔bot bridge, jobs, safety). This file
> is the hands-on day-to-day reference.

## Regenerating the sprite manifest (when a sprite/variant ships)
The catalog `spritebot/assets/sprites.json` is generated **from the web tracker's
`data.js`** so the share-code order never drifts. To update it:
```bash
# in the sprite-tracker repo:
cp data.js /tmp/_d.js && printf '\nmodule.exports={SPRITES,THEMES,SHARE_ORDER};\n' >> /tmp/_d.js
node -e "const d=require('/tmp/_d.js');process.stdout.write(JSON.stringify({share_order:d.SHARE_ORDER,themes:d.THEMES,sprites:d.SPRITES},null,2))" \
  > /path/to/sprite-trade-stop/spritebot/assets/sprites.json
cp sprites/<newid>.png /path/to/sprite-trade-stop/spritebot/assets/sprites/   # new art
```
Restart the bot → `announce_new_releases_once` posts the new sprite to `#news`.

## What this bot is
A discord.py 2.x bot for a Fortnite sprite **trading** community. Core loop:
members trade sprites in-game, then **vouch** each other; vouches drive **trust
tiers, XP, and auto-assigned flair roles**. It also reads the server's existing
**Onboarding sprite roles** for collection lookups. **No paid APIs** — pure
counting for analytics. SQLite for storage.

## Architecture at a glance

```
bot.py                      entry point: load .env, db.setup(), add persistent
                            views, load cogs, sync slash commands, run
spritebot/
  config.py                 ALL owner-tunable settings (IDs, names, thresholds)
  db.py                     SQLite layer (single source of truth)
  progression.py            PURE functions: xp/flair/tier from vouch count
  settings.py               resolve channel/role IDs (DB override > config),
                            name->object lookups, is_admin()
  helpers.py                apply_progression(member) + eligible_to_vouch()
  cogs/
    vouch.py                /vouch, +rep, /profile, /rank, /leaderboard,
                            /editvouch, /removevouch
    trades.py               /trade + persistent Confirm/Cancel buttons
    scam.py                 /reportscammer, /blacklist, /unblacklist
    collection.py           /whohas, /whoneeds, /match, list rebuild
    insights.py             /insights (AI-free counts)
    welcome.py              on_member_join -> Newbie + welcome embed
    admin.py                /setup, /postleaderboard, background tasks
tests/                      pytest: progression + db (run on empty DB)
```

### Data flow that matters
**Everything reputation-related is derived from the `vouches` table.** There is
no cached XP column. `db.vouch_count(user)` counts active (non-removed) vouches;
`progression.*` turns that number into XP / flair / verified status;
`helpers.apply_progression(member)` applies the resulting roles. So editing or
removing a vouch and re-calling `apply_progression` keeps everything correct —
no migration or recompute job needed.

### ID resolution (important)
`config.py` holds **names** (and optionally IDs). `/setup` writes resolved
numeric IDs into the `settings` table. `settings.py` reads **DB override first,
then config**. This is why the owner can either edit config by hand *or* just
run `/setup`. When adding a new configurable channel/role, add it to `config.py`
**and** to `/setup` in `admin.py` so it gets auto-detected.

## How to do common tasks

### Add a new sprite (e.g. a new season drops "Storm")
1. Create the Discord roles `Storm` and `Storm (Gold)` (via Onboarding as usual).
2. Add to `config.SPRITE_ROLES`:
   ```python
   "Storm": {"base": "Storm", "gold": "Storm (Gold)"},
   ```
3. **Restart the bot**, then run `/setup`. The restart matters: the slash-command
   choices for `/whohas` / `/whoneeds` / `/match` are generated from
   `SPRITE_ROLES` **at import time** (`@app_commands.choices(...)`), so a new
   sprite only appears in the pickers after the process restarts and re-syncs.
   `/setup` then resolves the new role IDs. Lists and `/insights` pick it up too.

### Add or retune a flair tier
Edit `config.FLAIR_TIERS` (name, min-vouches). Create the matching Discord role,
run `/setup`. `progression.py` and `helpers.apply_progression` use the list
directly — no other code changes. Order matters (ascending thresholds).

### Change XP-per-vouch / verified threshold / min account age
All in `config.py` (`XP_PER_VOUCH`, `VERIFIED_TRADER_THRESHOLD`,
`MIN_ACCOUNT_AGE_DAYS`). No code changes.

### Add a new command
Create a method in the relevant cog with `@app_commands.command(...)`. If it
changes a member's vouches, call `await helpers.apply_progression(member)` after.
Gate admin commands with `if not settings.is_admin(interaction.user): ...`.

## Database schema
`settings(key,value)` · `vouches(id,voucher_id,target_id,note,proof,created_at,removed)`
· `trades(id,party_a,party_b,give_a,give_b,status,a_confirm,b_confirm,message_id,created_at)`
· `blacklist(user_id,reason,at)` · `scam_reports(id,reporter_id,target_id,proof,at)`.
WAL mode is on. The file is `sprite_trade_stop.db` (config.DB_PATH); back it up
by copying that file.

## Background tasks (admin.py)
- `periodic_refresh` (every `LIST_REFRESH_MINUTES`) rebuilds `#sprite-list` and
  `#gold-zp-list` from current role membership.
- `daily_leaderboard` (every 24h) posts to the leaderboard channel.
Both `wait_until_ready()` first and swallow per-guild errors so the loop never dies.

## Persistent buttons
`TradeConfirmView` uses `timeout=None` + fixed `custom_id`s and is re-registered
in `bot.setup_hook`. Button handlers look the trade up by `message_id`, so they
work after a restart. Follow this pattern for any new long-lived buttons.

## Testing & CI
`pytest -q` runs `tests/` (progression + db on a temp DB; confirms no crash on
empty DB). `ruff check .` lints. CI runs both on every push
(`.github/workflows/ci.yml`). There's also a manual cog-load smoke test pattern
in the build notes — instantiate a Bot, `await load_extension` each cog, assert
the commands appear in `bot.tree`.

## Gotchas
- **Bot role height:** role assignment silently fails if the bot's role is below
  the target roles. `apply_progression` catches `Forbidden` and moves on.
- **Slash sync:** with `GUILD_ID` set, commands sync instantly to that guild;
  globally it can take ~1 hour. Keep `GUILD_ID` set for this single-server bot.
- **Intents:** members + message_content must be ON in the Developer Portal, not
  just in code.
