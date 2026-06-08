"""
Shared helpers that touch both Discord and the DB — mainly applying the
progression roles (flair + verified-trader) to a member based on their vouch
count. Only ever adds/removes FLAIR and VERIFIED roles; it never touches Owner,
Admin, sprite, or any other roles.
"""

import discord

from . import config, db, progression, settings


async def apply_progression(member: discord.Member) -> dict:
    """Recompute and apply a member's flair + verified-trader roles.

    Returns a summary dict (useful for messages/logging). Safe to call any time
    a member's vouch count may have changed.
    """
    guild = member.guild
    vouches = db.vouch_count(member.id)
    earned_flair = progression.flair_for(vouches)
    trusted = progression.is_verified_trader(vouches)

    # All flair roles that exist on this guild, so we can swap to just the one.
    flair_role_objs = {}
    for name in progression.all_flair_names():
        role = settings.flair_role(guild, name)
        if role:
            flair_role_objs[name] = role

    to_add, to_remove = [], []

    # Flair: ensure the member has exactly the earned flair (if the role exists).
    target_flair = flair_role_objs.get(earned_flair)
    for name, role in flair_role_objs.items():
        has = role in member.roles
        if name == earned_flair and not has:
            to_add.append(role)
        elif name != earned_flair and has:
            to_remove.append(role)

    # Verified trader.
    vt_role = settings.verified_trader_role(guild)
    if vt_role:
        has_vt = vt_role in member.roles
        if trusted and not has_vt:
            to_add.append(vt_role)
        elif not trusted and has_vt:
            to_remove.append(vt_role)

    try:
        if to_add:
            await member.add_roles(*to_add, reason="Sprite Trade Stop progression")
        if to_remove:
            await member.remove_roles(*to_remove, reason="Sprite Trade Stop progression")
    except discord.Forbidden:
        # Bot role is probably below the target roles — surfaced to admins
        # via the command that triggered this; don't crash.
        pass

    return {
        "vouches": vouches,
        "xp": progression.xp_for(vouches),
        "flair": earned_flair if target_flair else f"{earned_flair} (role missing)",
        "verified": trusted,
    }


def eligible_to_vouch(member: discord.Member) -> tuple[bool, str]:
    """Check blacklist + minimum account age. Returns (ok, reason_if_not)."""
    if db.is_blacklisted(member.id):
        return False, "This user is blacklisted from the trade system."
    age_days = (discord.utils.utcnow() - member.created_at).days
    if age_days < config.MIN_ACCOUNT_AGE_DAYS:
        return (False,
                f"Account too new ({age_days}d). Minimum is "
                f"{config.MIN_ACCOUNT_AGE_DAYS} days to use vouches.")
    return True, ""
