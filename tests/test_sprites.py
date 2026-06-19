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
    with pytest.raises(ValueError):
        sprites.decode("")
    # non-base64 still decodes leniently to all-missing or raises; ensure no crash
    try:
        sprites.decode("!!!!")
    except ValueError:
        pass


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
