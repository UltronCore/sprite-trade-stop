"""
Pure progression logic — no Discord, no DB. Easy to unit-test.

Everything is driven by VOUCHES RECEIVED:
    xp      = vouches * XP_PER_VOUCH
    flair   = highest FLAIR_TIERS entry whose threshold <= vouches
    trusted = vouches >= VERIFIED_TRADER_THRESHOLD
"""

from . import config


def xp_for(vouches: int) -> int:
    return max(0, vouches) * config.XP_PER_VOUCH


def flair_for(vouches: int) -> str:
    """Return the flair role NAME the member has earned."""
    earned = config.FLAIR_TIERS[0][0]
    for name, threshold in config.FLAIR_TIERS:
        if vouches >= threshold:
            earned = name
    return earned


def next_tier(vouches: int):
    """Return (name, threshold) of the next flair tier, or None if maxed."""
    for name, threshold in config.FLAIR_TIERS:
        if vouches < threshold:
            return name, threshold
    return None


def is_verified_trader(vouches: int) -> bool:
    return vouches >= config.VERIFIED_TRADER_THRESHOLD


def all_flair_names() -> list:
    return [name for name, _ in config.FLAIR_TIERS]
