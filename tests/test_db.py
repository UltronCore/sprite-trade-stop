"""DB-layer tests on a throwaway database. Confirms no crash on empty DB and
that vouch/trade/blacklist logic behaves."""

import os
import tempfile

import pytest

from spritebot import config, db


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    path = tempfile.mktemp(suffix=".db")
    monkeypatch.setattr(config, "DB_PATH", path)
    db._conn = None  # force a new connection at the temp path
    db.setup()
    yield
    db._conn = None
    if os.path.exists(path):
        os.remove(path)


def test_empty_db_queries_dont_crash():
    assert db.vouch_count(123) == 0
    assert db.leaderboard() == []
    assert db.completed_trade_count(123) == 0
    assert not db.is_blacklisted(123)


def test_vouch_lifecycle():
    vid = db.add_vouch(1, 2, note="great trade", proof="http://x")
    assert db.vouch_count(2) == 1
    assert db.already_vouched(1, 2)
    assert not db.already_vouched(9, 2)
    assert db.edit_vouch(vid, note="updated")
    assert db.remove_vouch(vid)
    assert db.vouch_count(2) == 0
    assert not db.remove_vouch(vid)  # already removed


def test_leaderboard_order():
    db.add_vouch(1, 100)
    db.add_vouch(2, 100)
    db.add_vouch(1, 200)
    lb = db.leaderboard()
    assert lb[0]["target_id"] == 100 and lb[0]["n"] == 2


def test_trade_two_party_confirm():
    tid = db.create_trade(1, 2, "Ghost", "Duck")
    t = db.get_trade(tid)
    assert t["status"] == "pending"
    db.confirm_trade(tid, "a")
    db.confirm_trade(tid, "b")
    t = db.get_trade(tid)
    assert t["a_confirm"] and t["b_confirm"]
    db.set_trade_status(tid, "complete")
    assert db.completed_trade_count(1) == 1
    assert db.completed_trade_count(2) == 1


def test_blacklist():
    db.add_blacklist(5, "scammer")
    assert db.is_blacklisted(5)
    assert db.remove_blacklist(5)
    assert not db.is_blacklisted(5)
