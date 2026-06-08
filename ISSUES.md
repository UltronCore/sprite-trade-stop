# Known Limitations & TODOs

Short, honest list of what's deferred. Good first issues for a contributor (or a
future AI session). File these as GitHub issues if you want tracking.

## Limitations (by design / current scope)
1. **`/insights` "most-requested" is a keyword heuristic**, not semantics. It
   matches `want|wtb|lf|looking for|need` near sprite names. Good enough to spot
   trends; not exact. (AI-free on purpose.)
2. **`/whoneeds` / `/match` treat "no role" as "needs it."** A member who simply
   hasn't picked sprite roles via Onboarding will appear to "need" everything.
   Mitigate by encouraging everyone to complete Onboarding.
3. **Large lists are truncated** in embeds (Discord 6000-char / field limits):
   `/whohas` shows up to 50 names, gold-zp-list up to 80. Fine for ~175 members.
4. **One bot = one guild assumed.** `GUILD_ID` drives instant slash sync. It will
   run in multiple guilds but lists/leaderboards aren't namespaced per guild for
   vouches (vouches are global by user ID).
5. **Daily leaderboard timer** posts every 24h from bot start, not at a fixed
   clock time. Restarting the bot shifts the post time.

## TODO / nice-to-haves
- [ ] `/trade` optional sprite **picker** (autocomplete) in addition to free text.
- [ ] Pin the auto-maintained list messages and reuse a stored message ID instead
      of scanning the last 20 messages.
- [ ] `/vouches @user` paginated full history (currently `/profile` shows last 5).
- [ ] Configurable leaderboard **post time** (e.g. 18:00 server time) via a
      `discord.ext.tasks` time= loop.
- [ ] Export/import of the SQLite DB via an admin command for easy backups.
- [ ] Optional cooldown on `/reportscammer` to prevent report spam.
- [ ] Unit tests for `settings.is_admin` and `helpers.eligible_to_vouch` with
      mocked members.

## Verified working (1.0.0)
- Loads with an empty database (no crash). ✅
- All 17 slash commands + `+rep` alias register. ✅
- ruff lint clean; pytest green (progression + db). ✅
