"""
SQLite data layer for Sprite Trade Stop.

One small file on disk (config.DB_PATH). All tables are created on first run,
so the bot never crashes on an empty database. Vouch counts / XP / flair are
DERIVED from the vouches table (single source of truth) so editing or removing
a vouch automatically keeps everything consistent.

Tables
------
settings        key/value overrides written by /setup (channel & role IDs)
vouches         every vouch (soft-deleted via removed flag for audit history)
trades          two-party trade records with confirm state
blacklist       users blocked from the vouch/trade system
scam_reports    scammer reports routed to modlog
"""

import sqlite3
import time

from . import config

_conn = None


def connect() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(config.DB_PATH)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
    return _conn


def setup() -> None:
    """Create all tables. Safe to call on every startup."""
    c = connect()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS vouches (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_id INTEGER NOT NULL,
            target_id  INTEGER NOT NULL,
            note       TEXT,
            proof      TEXT,
            created_at INTEGER NOT NULL,
            removed    INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_vouch_target ON vouches(target_id, removed);

        CREATE TABLE IF NOT EXISTS trades (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            party_a       INTEGER NOT NULL,
            party_b       INTEGER NOT NULL,
            give_a        TEXT,
            give_b        TEXT,
            status        TEXT NOT NULL DEFAULT 'pending',  -- pending|complete|cancelled
            a_confirm     INTEGER NOT NULL DEFAULT 0,
            b_confirm     INTEGER NOT NULL DEFAULT 0,
            message_id    INTEGER,
            created_at    INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS blacklist (
            user_id INTEGER PRIMARY KEY,
            reason  TEXT,
            at      INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS scam_reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER NOT NULL,
            target_id   INTEGER NOT NULL,
            proof       TEXT,
            at          INTEGER NOT NULL
        );
        """
    )
    c.commit()


def now() -> int:
    return int(time.time())


# ---- settings (key/value) -------------------------------------------------
def set_setting(key: str, value) -> None:
    c = connect()
    c.execute(
        "INSERT INTO settings(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )
    c.commit()


def get_setting(key: str):
    c = connect()
    row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


# ---- vouches --------------------------------------------------------------
def add_vouch(voucher_id: int, target_id: int, note=None, proof=None) -> int:
    c = connect()
    cur = c.execute(
        "INSERT INTO vouches(voucher_id,target_id,note,proof,created_at) "
        "VALUES(?,?,?,?,?)",
        (voucher_id, target_id, note, proof, now()),
    )
    c.commit()
    return cur.lastrowid


def get_vouch(vouch_id: int):
    c = connect()
    return c.execute("SELECT * FROM vouches WHERE id=?", (vouch_id,)).fetchone()


def remove_vouch(vouch_id: int) -> bool:
    c = connect()
    cur = c.execute("UPDATE vouches SET removed=1 WHERE id=? AND removed=0",
                    (vouch_id,))
    c.commit()
    return cur.rowcount > 0


def edit_vouch(vouch_id: int, note=None, proof=None) -> bool:
    c = connect()
    fields, vals = [], []
    if note is not None:
        fields.append("note=?")
        vals.append(note)
    if proof is not None:
        fields.append("proof=?")
        vals.append(proof)
    if not fields:
        return False
    vals.append(vouch_id)
    cur = c.execute(f"UPDATE vouches SET {','.join(fields)} WHERE id=?", vals)
    c.commit()
    return cur.rowcount > 0


def vouch_count(target_id: int) -> int:
    c = connect()
    row = c.execute(
        "SELECT COUNT(*) n FROM vouches WHERE target_id=? AND removed=0",
        (target_id,),
    ).fetchone()
    return row["n"]


def vouches_for(target_id: int, limit: int = 10):
    c = connect()
    return c.execute(
        "SELECT * FROM vouches WHERE target_id=? AND removed=0 "
        "ORDER BY id DESC LIMIT ?",
        (target_id, limit),
    ).fetchall()


def already_vouched(voucher_id: int, target_id: int) -> bool:
    """One active vouch per voucher->target pair (prevents spam-vouching)."""
    c = connect()
    row = c.execute(
        "SELECT 1 FROM vouches WHERE voucher_id=? AND target_id=? AND removed=0",
        (voucher_id, target_id),
    ).fetchone()
    return row is not None


def leaderboard(limit: int = 10):
    """Top members by active vouches received."""
    c = connect()
    return c.execute(
        "SELECT target_id, COUNT(*) n FROM vouches WHERE removed=0 "
        "GROUP BY target_id ORDER BY n DESC, target_id ASC LIMIT ?",
        (limit,),
    ).fetchall()


# ---- trades ---------------------------------------------------------------
def create_trade(party_a, party_b, give_a, give_b) -> int:
    c = connect()
    cur = c.execute(
        "INSERT INTO trades(party_a,party_b,give_a,give_b,created_at) "
        "VALUES(?,?,?,?,?)",
        (party_a, party_b, give_a, give_b, now()),
    )
    c.commit()
    return cur.lastrowid


def get_trade(trade_id: int):
    c = connect()
    return c.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()


def get_trade_by_message(message_id: int):
    c = connect()
    return c.execute("SELECT * FROM trades WHERE message_id=?",
                     (message_id,)).fetchone()


def set_trade_message(trade_id: int, message_id: int) -> None:
    c = connect()
    c.execute("UPDATE trades SET message_id=? WHERE id=?",
              (message_id, trade_id))
    c.commit()


def confirm_trade(trade_id: int, side: str) -> None:
    col = "a_confirm" if side == "a" else "b_confirm"
    c = connect()
    c.execute(f"UPDATE trades SET {col}=1 WHERE id=?", (trade_id,))
    c.commit()


def set_trade_status(trade_id: int, status: str) -> None:
    c = connect()
    c.execute("UPDATE trades SET status=? WHERE id=?", (status, trade_id))
    c.commit()


def trade_history(user_id: int, limit: int = 5):
    c = connect()
    return c.execute(
        "SELECT * FROM trades WHERE (party_a=? OR party_b=?) AND status='complete' "
        "ORDER BY id DESC LIMIT ?",
        (user_id, user_id, limit),
    ).fetchall()


def completed_trade_count(user_id: int) -> int:
    c = connect()
    row = c.execute(
        "SELECT COUNT(*) n FROM trades WHERE (party_a=? OR party_b=?) "
        "AND status='complete'",
        (user_id, user_id),
    ).fetchone()
    return row["n"]


# ---- blacklist ------------------------------------------------------------
def add_blacklist(user_id: int, reason: str) -> None:
    c = connect()
    c.execute(
        "INSERT INTO blacklist(user_id,reason,at) VALUES(?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET reason=excluded.reason",
        (user_id, reason, now()),
    )
    c.commit()


def remove_blacklist(user_id: int) -> bool:
    c = connect()
    cur = c.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
    c.commit()
    return cur.rowcount > 0


def is_blacklisted(user_id: int) -> bool:
    c = connect()
    return c.execute("SELECT 1 FROM blacklist WHERE user_id=?",
                     (user_id,)).fetchone() is not None


# ---- scam reports ---------------------------------------------------------
def add_scam_report(reporter_id, target_id, proof) -> int:
    c = connect()
    cur = c.execute(
        "INSERT INTO scam_reports(reporter_id,target_id,proof,at) "
        "VALUES(?,?,?,?)",
        (reporter_id, target_id, proof, now()),
    )
    c.commit()
    return cur.lastrowid
