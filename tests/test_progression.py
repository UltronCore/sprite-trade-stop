"""Unit tests for the pure progression logic (no Discord/DB needed)."""

from spritebot import config, progression


def test_xp_scales_with_vouches():
    assert progression.xp_for(0) == 0
    assert progression.xp_for(3) == 3 * config.XP_PER_VOUCH


def test_flair_thresholds():
    assert progression.flair_for(0) == "Newbie"
    assert progression.flair_for(1) == "Trader"
    assert progression.flair_for(5) == "Verified Trader"
    assert progression.flair_for(15) == "Veteran"
    assert progression.flair_for(1000) == "Max Helper"


def test_next_tier():
    assert progression.next_tier(0) == ("Trader", 1)
    name, threshold = progression.next_tier(2)
    assert name == "Verified Trader" and threshold == 5
    assert progression.next_tier(10_000) is None


def test_verified_trader_flag():
    assert not progression.is_verified_trader(4)
    assert progression.is_verified_trader(5)


def test_all_flair_names():
    names = progression.all_flair_names()
    assert names[0] == "Newbie" and "Max Helper" in names
