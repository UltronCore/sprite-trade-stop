"""Tests for collector-role milestone logic (pure, no Discord)."""

from spritebot import collector, sprites

HAVE, MASTERED = 1, 2


def _all(theme=None, rarity=None):
    """Build a collection with HAVE for every released sprite matching a filter."""
    out = {}
    for s in sprites.released():
        if theme and s["theme"] != theme:
            continue
        if rarity and s["rarity"].lower() != rarity.lower():
            continue
        out[s["id"]] = HAVE
    return out


def test_all_gold_role():
    earned = collector.earned_roles(_all(theme="gold"))
    assert "All Gold" in earned
    # missing one gold → not earned
    partial = _all(theme="gold")
    partial.pop(next(iter(partial)))
    assert "All Gold" not in collector.earned_roles(partial)


def test_galaxy_and_gummy():
    assert "Galaxy Sprite Collector" in collector.earned_roles(_all(theme="galaxy"))
    assert "Gummy Sprite Collector" in collector.earned_roles(_all(theme="candy"))


def test_peanut_and_mythic():
    assert "Peanut Collector" in collector.earned_roles({"theburntpeanut_basic": HAVE})
    mythic = _all(rarity="Mythic")
    assert "Mythic Sprite Collector" in collector.earned_roles(mythic)


def test_mastered_milestones():
    rel = sprites.released()
    # master exactly 15 → "15 Sprites Mastered" but not "Mastered Em' All"
    fifteen = {s["id"]: MASTERED for s in rel[:15]}
    e = collector.earned_roles(fifteen)
    assert "15 Sprites Mastered" in e and "Mastered Em' All" not in e
    # master everything → both, plus full-collection "Superior"
    allm = {s["id"]: MASTERED for s in rel}
    e2 = collector.earned_roles(allm)
    assert {"15 Sprites Mastered", "Mastered Em' All", "Superior Sprite Collector"} <= e2


def test_empty_collection_earns_nothing():
    assert collector.earned_roles({}) == set()


def test_text_grid_renders():
    from spritebot.cogs.collection_sync import build_text_grid
    status = {s["id"]: HAVE for s in sprites.released() if s["theme"] == "basic"}
    grid = build_text_grid(status)
    assert "NORMAL" in grid and "GUMMY" in grid and "GALAXY" in grid
    assert "Water" in grid and "Burnt Peanut" in grid
    assert "✅" in grid and "❌" in grid and "collected" in grid
