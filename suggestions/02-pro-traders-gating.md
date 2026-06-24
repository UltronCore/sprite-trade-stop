# 2. "Pro traders" channel (only near-complete collectors)

**Suggested by:** Goose — a channel where "only people that are only missing a
few sprites can be in… so it doesn't get overwhelming with people begging for
anything rare." (Owner reply: good idea, but manual gating is too much work
while growing 400+ members/2 days.)

**Verdict:** ✅ Built — the bot removes the manual work.

## Response
The owner's blocker was "too much work to gate manually." The bot makes it
automatic: it already auto-assigns **collector roles** from synced collections.
Add one more threshold role and gate the channel by it:

```python
# config.COLLECTOR_ROLES — add an "almost done" tier
{"role": "Pro Trader", "rule": "mastered_count", "n": 30},   # or a have-count rule
```

Better, gate by **near-complete collection** rather than mastery — I can add a
`missing_at_most` rule (e.g. missing ≤ 3 released sprites → "Pro Trader" role).
Then make `#pro-traders` visible only to that role. No mod effort: the bot grants
and revokes the role as collections change.

**To enable:** tell me the exact role name + threshold (e.g. "Pro Trader",
missing ≤ 5) and I'll add the rule; you create the role + restrict the channel.
