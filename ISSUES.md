# Known Limitations & TODOs

Short, honest list of what's deferred. Good first issues for a contributor (or a
future AI session). File these as GitHub issues if you want tracking.

## Limitations (by design / current scope)
1. **`/insights` "most-requested" is a keyword heuristic**, not semantics. It
   matches `want|wtb|lf|looking for|need|needing` near sprite names. Good enough
   to spot trends; not exact. (AI-free on purpose.)
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
- [ ] **Stronger anti-sybil:** gate vouching/trading on **server-join tenure**
      (`member.joined_at`) in addition to account age, since account age is
      farmable but join age isn't. (Deferred from the v1.0.1 QA pass.)
- [ ] **Reciprocal-vouch dampening:** detect A↔B mutual vouches and down-weight
      or flag them in `vouch_count`/leaderboard to blunt ring-vouching.
- [ ] Optionally require a completed `/trade` between two users before a vouch
      between them counts, tying reputation to real trade records.

## Hardened in the v1.0.1 QA pass
- **Trade two-party confirm race** → atomic `complete_if_both_confirmed` (no double completion). ✅
- **`+rep` in DMs** no longer crashes (`@commands.guild_only()` + error handler). ✅
- **Mention injection** neutralized bot-wide (`AllowedMentions.none()`; trades ping only the two parties). ✅
- **Vouch farming** capped (`MAX_VOUCHES_PER_DAY`); `/trade` now enforces account-age gate. ✅
- **Blacklist** now strips flair/verified roles and excludes the user from the leaderboard. ✅
- **`reportscammer`** guards: no self-report, blacklisted blocked, per-user cooldown. ✅
- **Admin-by-role** prefers resolved role IDs over spoofable names. ✅
- **Embed field caps** enforced (trade items, vouch notes) → no 400s. ✅
- **`/whohas`/`/whoneeds`/`/match`** defer + chunk the guild for complete, timely results. ✅

## Verified working (1.0.1)
- Loads with an empty database (no crash). ✅
- All 17 slash commands + `+rep` alias register. ✅
- ruff lint clean; pytest green (14 tests: progression + db, incl. new guards). ✅
- CI matrix on Python 3.10 / 3.11 / 3.12. ✅
