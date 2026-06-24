# 5. Jr-mod / distributor sub-roles

**Suggested by:** DominicGTB — "Jr mod roles… mainly for the roles admin, helper
and sprite distributors… more mods for each role."

**Verdict:** ⚪ Mostly a server task — the bot recognises the roles you make.

## Response
Creating a Jr-mod / sub-mod role tier is a **server admin decision** (role
hierarchy + permissions), not bot code. The bot fits in cleanly:
- It already recognises a **Distributor** role for queue staff (`/setup` binds it).
- `settings.is_admin` accepts the **Admin/Owner** roles and Discord permissions —
  give Jr-mods the Discord permissions you want and they'll pass admin checks; or
  keep them distributor-only (queue powers, no admin).
- Helper/Distributor roles can also be **earned automatically** if you tie them to
  collection milestones (see collector roles) — e.g. a "Helper" perk for big
  collectors.

**No bot change needed** unless you want a command that grants a sub-mod role on
some condition — tell me the rule and I'll add it.
