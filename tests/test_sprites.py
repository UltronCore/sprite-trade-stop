"""Tests for the web<->bot share-code bridge and collection storage."""

import pytest

from spritebot import config, db, sprites


def test_manifest_loaded():
    assert len(sprites.SHARE_ORDER) == 54
    assert len(sprites.released()) == 41
    assert sprites.SHARE_ORDER[0] == "water_basic"


def test_decode_known_web_code():
    # Code produced by the web app's packCode() for a known collection.
    code = "QgAAAAgAAAAAACAAEAQ"
    st = sprites.decode(code)
    assert st["water_basic"] == 2      # mastered
    assert st["water_galaxy"] == 1     # have
    assert st["zeropoint_galaxy"] == 1
    assert st["king_basic"] == 2
    assert st["duck_gold"] == 2
    assert st["theburntpeanut_basic"] == 1
    assert st["fire_basic"] == 0       # missing


def test_encode_decode_roundtrip():
    status = {"water_basic": 2, "duck_gold": 1, "ghost_galaxy": 1, "punk_basic": 2}
    code = sprites.encode(status)
    back = sprites.decode(code)
    for sid, v in status.items():
        assert back[sid] == v


def test_decode_accepts_full_url():
    code = "QgAAAAgAAAAAACAAEAQ"
    st = sprites.decode(f"https://ultroncore.github.io/sprite-tracker/?c={code}")
    assert st["water_basic"] == 2


def test_decode_rejects_garbage():
    # Strict validation: bad charset, wrong length, and empty all rejected.
    for bad in ["", "!!!!", "abc", "xx", "@@@@", "QgAA"]:
        with pytest.raises(ValueError):
            sprites.decode(bad)


def test_decode_rejects_invalid_status_value():
    # A right-length code whose bits include status 3 (impossible) is rejected.
    import base64
    bad = base64.b64encode(b"\xff" * sprites._EXPECTED_BYTES).decode()
    with pytest.raises(ValueError):
        sprites.decode(bad)


def test_summarize():
    s = sprites.summarize({"water_basic": 2, "duck_gold": 1, "fire_basic": 0})
    assert s["total"] == 41 and s["have"] == 2 and s["mastered"] == 1


@pytest.fixture()
def fresh_db(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "c.db"))
    db._conn = None
    db.setup()
    yield
    db._conn = None


def test_collection_storage(fresh_db):
    db.set_collection(7, {"water_basic": 2, "duck_gold": 1, "fire_basic": 0})
    got = db.get_collection(7)
    assert got == {"water_basic": 2, "duck_gold": 1}  # 0s not stored
    assert db.has_collection(7)
    assert not db.has_collection(99)


def test_collection_holders_and_leaderboard(fresh_db):
    db.set_collection(1, {"water_basic": 2, "duck_gold": 1})
    db.set_collection(2, {"water_basic": 1})
    holders = db.sprite_holders("water_basic")
    assert {r["user_id"] for r in holders} == {1, 2}
    assert holders[0]["status"] == 2  # mastered listed first
    lb = db.collection_leaderboard()
    assert lb[0]["user_id"] == 1 and lb[0]["n"] == 2
    assert set(db.users_with_collections()) == {1, 2}


def test_set_collection_replaces(fresh_db):
    db.set_collection(1, {"water_basic": 1, "duck_gold": 1})
    db.set_collection(1, {"water_basic": 2})  # replace
    assert db.get_collection(1) == {"water_basic": 2}


def test_privacy_excludes_from_guild_features(fresh_db):
    db.set_collection(1, {"water_basic": 2, "duck_gold": 1})
    db.set_collection(2, {"water_basic": 1})
    # user 2 goes private
    db.set_collection_private(2, True)
    assert db.is_collection_private(2)
    # excluded from holders, leaderboard, users list, have_counts
    assert {r["user_id"] for r in db.sprite_holders("water_basic")} == {1}
    assert {r["user_id"] for r in db.collection_leaderboard()} == {1}
    assert db.users_with_collections() == [1]
    assert db.have_counts()["water_basic"] == 1
    # their own data still intact
    assert db.get_collection(2) == {"water_basic": 1}
    # toggling back restores visibility
    db.set_collection_private(2, False)
    assert {r["user_id"] for r in db.sprite_holders("water_basic")} == {1, 2}


def test_have_counts_and_single_set(fresh_db):
    db.set_collection(1, {"water_basic": 1, "duck_gold": 2})
    db.set_collection(2, {"water_basic": 1})
    counts = db.have_counts()
    assert counts["water_basic"] == 2 and counts["duck_gold"] == 1
    # single-sprite edit
    db.set_sprite_status(3, "ghost_basic", 2)
    assert db.get_collection(3) == {"ghost_basic": 2}
    db.set_sprite_status(3, "ghost_basic", 0)  # 0 removes
    assert db.get_collection(3) == {}
