# Server Inspection — READ-ONLY pass

> 🔒 **This pass is VIEW & SEARCH ONLY.** When given computer access I will
> **only browse and read** the server — no posting messages, no running slash
> commands, no changing settings. Anything that needs a command *run* or a
> message *sent* is listed in §7 for a human to do.

Goal: confirm the server is ready for the bot, grounded in what was observed as
of 2026-06-24. Each item says exactly **what I look at** (read-only) and the
expected result. I'll fill in a verdict per item and report back.

---

## 1. Channels exist & names match config (view the channel list)

The bot finds channels by the names in `config.CHANNELS`. I'll **view the channel
list** and check each. Mismatches are fixed later by renaming, creating, or
editing config + running `/setup` (a human step).

| Bot expects (`config`) | Seen 2026-06-24 | What I'll verify (view only) |
|---|---|---|
| `trade-portal` | trade-portal-1/2/3, galaxy-sprite-trade-portal | Which exact name to point config at |
| `vouch-trades` | vouch-trades ✓ | Exists |
| `news` | news ✓ | Exists |
| `welcome` | welcome ✓ | Exists |
| `sprite-queue` | galaxy-sprite-queue-system | Confirm name / whether a `#sprite-queue` exists |
| `modlog` `leaderboard` `sprite-list` `gold-zp-list` `sprite-digest` | not seen | Note which are missing |
| `news ping` target | — | Is there a sprite-news ping role/channel (suggestion #1)? |

- [ ] Listed which channels exist vs. missing vs. name-mismatched
- [ ] Read the `#rules-and-faq` / `#roles-info` pins for how trading/vouching is described

## 2. Roles exist & hierarchy (view Server Settings → Roles)

I'll **view the role list and its order** (read-only):

- [ ] **Sprite roles + Gold** (Zero Point, Dream, Punk, King, Ghost, Demon, Duck — base + "(Gold)") exist and are onboarding-assignable
- [ ] **verified-trader**, **Distributor / Sprite Distributors**, **Owner/Admin** roles exist
- [ ] **Collector roles** exist and match `config.COLLECTOR_ROLES` names exactly:
  All Gold, Galaxy/Gummy/Mythic/Epic Sprite Collector, Mastered Em' All,
  15 Sprites Mastered, Peanut Collector, Superior Sprite Collector
  *(seen on the Sprite bot's role list — I'll confirm exact spelling/emoji)*
- [ ] **Role order:** note where the (future) bot role would need to sit — it must
  be **above** all sprite/Gold/flair/verified/collector roles to assign them

## 3. Permissions & intents (view only / portal note)

- [ ] In Server Settings, note whether a role for this bot would have Manage Roles
- [ ] **Cannot verify from the server side:** the two Privileged Intents (Members,
  Message Content) live in the Developer Portal → flagged in §7 for a human

## 4. The other bot — "Sprite" (view its profile, read-only) ⚠️ DECIDED

Confirmed by viewing its profile: **Sprite (FNSprite Custom Bot)** — `/vouch`
(star rating), `/vouches`, `/manage vouch`; auto-assigns verified-trader at 3
vouches and another role at 15. It also holds the collector roles list.

- [x] **Decision:** set `config.DISABLED_COGS = ["vouch", "scam"]` so this bot does
  NOT duplicate vouching or scam-reports (their `#report` tickets own that).
- [ ] I'll **read** its slash-command list (view-only) to confirm no other overlap
- [ ] Confirm: this bot should own **collection tracking, queues, sessions, panel,
  collector roles, events** — which Sprite does not do

## 5. Collector-role readiness (the big integration win) — view only

The server hands out collector roles **by hand**; this bot auto-assigns them.
Read-only checks:

- [ ] Compare the EXACT role names on the Sprite bot's profile vs.
  `config.COLLECTOR_ROLES` and note any spelling/emoji differences to fix in config
- [ ] Confirm a `#pro-traders`-style channel exists or note it's needed for the
  new **"Almost Complete"** role (suggestion #2)

## 6. Suggestions cross-check (read `#suggestions`, view-only)

For each post in `#suggestions`, I'll confirm the bot's response in
[suggestions/](suggestions/) still matches reality:
- [ ] #1 Sprite-news ping → role/channel present? (bot supports it)
- [ ] #2 Pro-traders gate → channel present for the Almost-Complete role?
- [ ] #3 Ticket drops → is the old `galaxy-sprite-queue-system` still in use? (`/queue` replaces it)
- [ ] #4 Customs → `#custom-games` + Customs role present? (`/session` covers it)
- [ ] #5 Jr-mod roles / #6 meme channel → server tasks, just note status

---

## 7. ⚠️ Needs a HUMAN (not part of my read-only pass)

These require **running a command or sending a message** — I will NOT do them.
Listed so you (or a mod) can do them, ideally in a private/test channel:

- [ ] Run **`/setup`** (binds channels/roles) — then read its "Found/Missing" report
- [ ] Enable the 2 Privileged Intents in the Developer Portal
- [ ] Move the bot's role **above** the sprite/collector roles
- [ ] Smoke-test by running: `/panel` (click each button), `/synccollection <code>`,
  `/mycollection`, `/queue open …` → Join → `/queue done`, `/session open` → Join →
  `/session teams`, `/grid`, `/events`, `/collectorroles`, `/spritematch`
- [ ] Confirm a collector role flips correctly (sync all-Gold → "All Gold" granted)

---

### Verdict template (I fill this in after the read-only pass)
- Channels: exist ___ / missing ___ / name-mismatch ___
- Roles: exist ___ / missing ___ / name differences to fix in config: ___
- Bot role position (where it must sit): ___
- Other-bot overlap → DISABLED_COGS = ___
- Suggestions still accurate? ___
- Human to-do handed off: ___
