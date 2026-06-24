"""
Collector roles — auto-assign milestone roles from a member's synced collection.

The server already gives out roles like "All Gold", "Galaxy Sprite Collector",
"Mastered Em' All", "15 Sprites Mastered" by hand. The bot has the collection
data (from /synccollection), so it can grant/remove these automatically.

`earned_roles(status)` is pure (no Discord/DB) so it's easy to test.
`apply_collector_roles(member)` resolves the role names and adds/removes them —
touching ONLY the collector roles in config.COLLECTOR_ROLES, nothing else.
"""

import discord

from . import config, db, settings, sprites

HAVE, MASTERED = 1, 2


def _rule_met(rule: dict, status: dict) -> bool:
    rel = sprites.released()
    have = {sid for sid, v in status.items() if v >= HAVE}
    mastered = {sid for sid, v in status.items() if v == MASTERED}
    kind = rule["rule"]
    if kind == "all_theme":
        ids = [s["id"] for s in rel if s["theme"] == rule["theme"]]
        return bool(ids) and all(i in have for i in ids)
    if kind == "all_rarity":
        ids = [s["id"] for s in rel if s["rarity"].lower() == rule["rarity"].lower()]
        return bool(ids) and all(i in have for i in ids)
    if kind == "has":
        return rule["id"] in have
    if kind == "all_have":
        return all(s["id"] in have for s in rel)
    if kind == "all_mastered":
        return all(s["id"] in mastered for s in rel)
    if kind == "mastered_count":
        return len(mastered) >= rule["n"]
    if kind == "missing_at_most":
        # "Almost complete" — e.g. for a gated pro-traders channel.
        missing = sum(1 for s in rel if s["id"] not in have)
        return missing <= rule["n"]
    return False


def earned_roles(status: dict) -> set:
    """Set of collector-role NAMES this collection qualifies for."""
    return {r["role"] for r in config.COLLECTOR_ROLES if _rule_met(r, status)}


async def apply_collector_roles(member: discord.Member) -> dict:
    """Grant/remove the configured collector roles for a member. Returns a
    summary {role_name: bool}. Only touches roles in config.COLLECTOR_ROLES."""
    if not config.COLLECTOR_ROLES:
        return {}
    status = db.get_collection(member.id)
    earned = earned_roles(status)
    to_add, to_remove, summary = [], [], {}
    for spec in config.COLLECTOR_ROLES:
        name = spec["role"]
        # bound by /setup as role:collector:<name>, else matched by name
        rid = db.get_setting(f"role:collector:{name}")
        role = member.guild.get_role(int(rid)) if rid else \
            settings.get_role_by_name(member.guild, name)
        if not role:
            continue
        has = role in member.roles
        want = name in earned
        summary[name] = want
        if want and not has:
            to_add.append(role)
        elif not want and has:
            to_remove.append(role)
    try:
        if to_add:
            await member.add_roles(*to_add, reason="Collector milestone")
        if to_remove:
            await member.remove_roles(*to_remove, reason="Collector milestone lost")
    except discord.Forbidden:
        pass
    return summary
