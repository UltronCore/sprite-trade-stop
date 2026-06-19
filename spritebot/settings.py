"""
Runtime ID resolution: merge /setup overrides (DB) over config defaults, and
turn names into live discord objects.

resolve order for a channel/role key:
    db setting (numeric ID written by /setup)  >  config name/ID  >  None
"""

import discord

from . import config, db


# ---- channels -------------------------------------------------------------
def channel_id(key: str):
    """Return a configured channel ID (int) or None."""
    override = db.get_setting(f"channel:{key}")
    if override:
        return int(override)
    raw = config.CHANNELS.get(key)
    if isinstance(raw, int) and raw:
        return raw
    return None  # only a name is set; must be resolved via /setup


def get_channel(guild: discord.Guild, key: str):
    cid = channel_id(key)
    if cid:
        return guild.get_channel(cid)
    # Fall back to matching by name if only a name is configured.
    name = config.CHANNELS.get(key)
    if isinstance(name, str):
        return discord.utils.get(guild.text_channels, name=name)
    return None


# ---- roles ----------------------------------------------------------------
def _role_override(key: str):
    override = db.get_setting(f"role:{key}")
    return int(override) if override else None


def get_role_by_name(guild: discord.Guild, name: str):
    return discord.utils.get(guild.roles, name=name)


def verified_trader_role(guild: discord.Guild):
    rid = _role_override("verified_trader")
    if rid:
        return guild.get_role(rid)
    return get_role_by_name(guild, config.VERIFIED_TRADER_ROLE_NAME)


def distributor_role(guild: discord.Guild):
    rid = _role_override("distributor")
    if rid:
        return guild.get_role(rid)
    return get_role_by_name(guild, config.DISTRIBUTOR_ROLE_NAME)


def is_distributor(member: discord.Member) -> bool:
    """Admins OR members holding the Distributor role can fulfil queues."""
    if is_admin(member):
        return True
    role = distributor_role(member.guild)
    return role is not None and role in member.roles


def flair_role(guild: discord.Guild, flair_name: str):
    rid = _role_override(f"flair:{flair_name}")
    if rid:
        return guild.get_role(rid)
    return get_role_by_name(guild, flair_name)


def sprite_role(guild: discord.Guild, sprite: str, gold: bool = False):
    variant = "gold" if gold else "base"
    rid = _role_override(f"sprite:{sprite}:{variant}")
    if rid:
        return guild.get_role(rid)
    spec = config.SPRITE_ROLES.get(sprite)
    if not spec:
        return None
    return get_role_by_name(guild, spec[variant])


# ---- permissions ----------------------------------------------------------
def is_admin(member: discord.Member) -> bool:
    """True for configured owners/admins, the Owner/Admin roles, or guild perms.

    Prefers role IDs resolved by /setup (role:owner / role:admin) over matching
    by name, since a role *name* like "Admin" could otherwise be spoofed by a
    self-assignable role. Falls back to name matching only if no ID is saved.
    """
    if member.id in config.OWNER_IDS or member.id in config.ADMIN_IDS:
        return True
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    member_role_ids = {r.id for r in member.roles}
    owner_id = _role_override("owner")
    admin_id = _role_override("admin")
    if owner_id and owner_id in member_role_ids:
        return True
    if admin_id and admin_id in member_role_ids:
        return True
    # No role-NAME fallback: a self-assignable role literally named "Admin"
    # must not grant bot-admin. Authorization comes only from configured IDs,
    # /setup-resolved role IDs, or Discord's Administrator/Manage Server perms
    # (both already checked above). Run /setup to resolve the Owner/Admin roles.
    return False
