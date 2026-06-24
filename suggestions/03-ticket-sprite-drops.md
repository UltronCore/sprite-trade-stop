# 3. Ticket system for sprite drops

**Suggested by:** Call Me Spooks — like a 10K Elden Ring server: droppers/
indexers/helpers; members open 1 ticket / 24h asking for 1 sprite; helpers ping
them when ready; everything logged for scammer traces. (Suggested Ticket Tool or
MEE6.)

**Verdict:** ✅ Covered — the bot's queue system does this, with less overhead.

## Response
This is exactly what **`/queue` + `/panel`** already do, and it scales better
than per-member tickets:

| Ticket idea | Bot equivalent |
|---|---|
| Open a ticket asking for 1 sprite | `/queue join <sprite>` or click **Join** on a board |
| 1 ticket / 24h (avoid overwhelm) | Closed-by-default queues + `MAX_QUEUES_PER_USER` cap |
| Helpers ping when ready | `/queue next` pings the person at the front |
| "boom done" | `/queue done @user` — removes them **and marks the sprite in their collection** |
| Logged for scammer traces | Every join/serve is in the DB; pair with `#report` tickets |
| droppers/indexers/helpers | The **Distributor** role (bound by `/setup`) |

Why this beats one-channel-per-ticket: a queue handles **many people for the same
sprite in fair order** without spawning a channel each, shows live positions, and
ties the hand-off back to the member's tracked collection.

**If you still want literal tickets** for 1:1 support (not sprite requests), keep
**Ticket Tool** for `#support`/`#report` — it complements the bot, no overlap.

**Optional add:** a 1-request-per-24h cooldown on `/queue join` to mirror the
"1 ticket/24h" rule — say the word and I'll add `QUEUE_JOIN_COOLDOWN_HOURS`.
