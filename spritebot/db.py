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

        -- Per-member sprite collection, synced from the web tracker's share code.
        -- status: 0 missing (not stored) | 1 have | 2 mastered
        CREATE TABLE IF NOT EXISTS collections (
            user_id   INTEGER NOT NULL,
            sprite_id TEXT    NOT NULL,
            status    INTEGER NOT NULL,
            PRIMARY KEY (user_id, sprite_id)
        );
        CREATE INDEX IF NOT EXISTS idx_coll_sprite ON collections(sprite_id, status);

        -- Members who opted their collection OUT of guild-visible features
        -- (holders / spritematch / leaderboard / digest). Their own commands
        -- still work; they're just invisible to others.
        CREATE TABLE IF NOT EXISTS collection_private (
            user_id INTEGER PRIMARY KEY
        );

        -- Sprite hand-off queues: a member waits in line for a distributor to
        -- give them a sprite. sprite_id is a released id, or 'general'.
        -- Ordering is by the autoincrement `id` (true insertion order) so two
        -- people joining in the same second still get correct FIFO positions.
        CREATE TABLE IF NOT EXISTS queues (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sprite_id TEXT    NOT NULL,
            user_id   INTEGER NOT NULL,
            joined_at INTEGER NOT NULL,
            UNIQUE (sprite_id, user_id)
        );
        -- Which queues are currently OPEN for joining (closed by default).
        CREATE TABLE IF NOT EXISTS open_queues (
            sprite_id TEXT PRIMARY KEY,
            opened_at INTEGER NOT NULL
        );

        -- Sessions: a host opens a custom game / sprite hunt / dust farm and
        -- members join via a button up to an optional slot limit.
        CREATE TABLE IF NOT EXISTS sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            host_id    INTEGER NOT NULL,
            kind       TEXT    NOT NULL,
            title      TEXT,
            slots      INTEGER NOT NULL DEFAULT 0,   -- 0 = unlimited
            status     TEXT    NOT NULL DEFAULT 'open',  -- open | closed
            message_id INTEGER,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS session_members (
            session_id INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            joined_at  INTEGER NOT NULL,
            PRIMARY KEY (session_id, user_id)
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


def seconds_since_pair_vouch(voucher_id: int, target_id: int):
    """Seconds since this voucher last vouched this target, or None if never.

    Used for the per-pair cooldown so repeat trading partners can keep building
    trust over time without instant ring-farming."""
    c = connect()
    row = c.execute(
        "SELECT MAX(created_at) last FROM vouches WHERE voucher_id=? AND target_id=?",
        (voucher_id, target_id),
    ).fetchone()
    if not row or row["last"] is None:
        return None
    return now() - row["last"]


def leaderboard(limit: int = 10):
    """Top members by active vouches received (blacklisted users excluded)."""
    c = connect()
    return c.execute(
        "SELECT target_id, COUNT(*) n FROM vouches "
        "WHERE removed=0 AND target_id NOT IN (SELECT user_id FROM blacklist) "
        "GROUP BY target_id ORDER BY n DESC, target_id ASC LIMIT ?",
        (limit,),
    ).fetchall()


def recent_vouch_count(voucher_id: int, window_seconds: int) -> int:
    """How many vouches this user has GIVEN within the last window (rate limit)."""
    c = connect()
    row = c.execute(
        "SELECT COUNT(*) n FROM vouches WHERE voucher_id=? AND created_at >= ?",
        (voucher_id, now() - window_seconds),
    ).fetchone()
    return row["n"]


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


def pending_trade_between(a: int, b: int):
    """Return an open (pending) trade between this pair, either direction."""
    c = connect()
    return c.execute(
        "SELECT * FROM trades WHERE status='pending' AND "
        "((party_a=? AND party_b=?) OR (party_a=? AND party_b=?)) LIMIT 1",
        (a, b, b, a)).fetchone()


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


def complete_if_both_confirmed(trade_id: int) -> bool:
    """Atomically flip pending->complete ONLY if both sides confirmed.

    Returns True for exactly the one caller that performed the transition, so
    the completion message can never post twice (fixes the two-confirm race).
    """
    c = connect()
    cur = c.execute(
        "UPDATE trades SET status='complete' "
        "WHERE id=? AND status='pending' AND a_confirm=1 AND b_confirm=1",
        (trade_id,),
    )
    c.commit()
    return cur.rowcount == 1


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
# ---- queues ---------------------------------------------------------------
def queue_open(sprite_id: str) -> None:
    c = connect()
    c.execute("INSERT OR IGNORE INTO open_queues(sprite_id,opened_at) VALUES(?,?)",
              (sprite_id, now()))
    c.commit()


def queue_close(sprite_id: str) -> None:
    c = connect()
    c.execute("DELETE FROM open_queues WHERE sprite_id=?", (sprite_id,))
    c.commit()


def is_queue_open(sprite_id: str) -> bool:
    c = connect()
    return c.execute("SELECT 1 FROM open_queues WHERE sprite_id=?",
                     (sprite_id,)).fetchone() is not None


def open_queue_ids() -> list:
    c = connect()
    return [r["sprite_id"] for r in c.execute(
        "SELECT sprite_id FROM open_queues ORDER BY opened_at").fetchall()]


def queue_add(sprite_id: str, user_id: int) -> str:
    """Add a member to a queue. Returns 'added' or 'exists'."""
    c = connect()
    cur = c.execute(
        "INSERT OR IGNORE INTO queues(sprite_id,user_id,joined_at) VALUES(?,?,?)",
        (sprite_id, user_id, now()))
    c.commit()
    return "added" if cur.rowcount else "exists"


def queue_remove(sprite_id: str, user_id: int) -> bool:
    c = connect()
    cur = c.execute("DELETE FROM queues WHERE sprite_id=? AND user_id=?",
                    (sprite_id, user_id))
    c.commit()
    return cur.rowcount > 0


def queue_position(sprite_id: str, user_id: int):
    """1-based position in line, or None if not queued. Ordered by insertion id."""
    c = connect()
    row = c.execute("SELECT id FROM queues WHERE sprite_id=? AND user_id=?",
                    (sprite_id, user_id)).fetchone()
    if not row:
        return None
    ahead = c.execute(
        "SELECT COUNT(*) n FROM queues WHERE sprite_id=? AND id < ?",
        (sprite_id, row["id"])).fetchone()["n"]
    return ahead + 1


def queue_list(sprite_id: str, limit: int = 100) -> list:
    c = connect()
    return c.execute(
        "SELECT user_id, joined_at FROM queues WHERE sprite_id=? "
        "ORDER BY id ASC LIMIT ?", (sprite_id, limit)).fetchall()


def queue_length(sprite_id: str) -> int:
    c = connect()
    return c.execute("SELECT COUNT(*) n FROM queues WHERE sprite_id=?",
                     (sprite_id,)).fetchone()["n"]


def queue_head(sprite_id: str):
    """The next member in line (first to join), or None."""
    c = connect()
    return c.execute(
        "SELECT user_id, joined_at FROM queues WHERE sprite_id=? "
        "ORDER BY id ASC LIMIT 1", (sprite_id,)).fetchone()


def queue_user_count(user_id: int) -> int:
    c = connect()
    return c.execute("SELECT COUNT(*) n FROM queues WHERE user_id=?",
                     (user_id,)).fetchone()["n"]


def queue_user_entries(user_id: int) -> list:
    c = connect()
    return c.execute(
        "SELECT sprite_id, joined_at FROM queues WHERE user_id=? "
        "ORDER BY id ASC", (user_id,)).fetchall()


# ---- sessions (custom games / hunts) --------------------------------------
def create_session(host_id: int, kind: str, title: str, slots: int) -> int:
    c = connect()
    cur = c.execute(
        "INSERT INTO sessions(host_id,kind,title,slots,created_at) VALUES(?,?,?,?,?)",
        (host_id, kind, title, slots, now()))
    c.commit()
    return cur.lastrowid


def get_session(sid: int):
    c = connect()
    return c.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()


def get_session_by_message(message_id: int):
    c = connect()
    return c.execute("SELECT * FROM sessions WHERE message_id=?",
                     (message_id,)).fetchone()


def set_session_message(sid: int, message_id: int) -> None:
    c = connect()
    c.execute("UPDATE sessions SET message_id=? WHERE id=?", (message_id, sid))
    c.commit()


def close_session(sid: int) -> None:
    c = connect()
    c.execute("UPDATE sessions SET status='closed' WHERE id=?", (sid,))
    c.commit()


def open_sessions() -> list:
    c = connect()
    return c.execute("SELECT * FROM sessions WHERE status='open' "
                     "ORDER BY id DESC").fetchall()


def session_join(sid: int, user_id: int) -> str:
    """Add a member if room. Returns 'joined' | 'exists' | 'full' | 'closed'."""
    c = connect()
    sess = c.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    if not sess or sess["status"] != "open":
        return "closed"
    if c.execute("SELECT 1 FROM session_members WHERE session_id=? AND user_id=?",
                 (sid, user_id)).fetchone():
        return "exists"
    if sess["slots"]:
        n = c.execute("SELECT COUNT(*) n FROM session_members WHERE session_id=?",
                      (sid,)).fetchone()["n"]
        if n >= sess["slots"]:
            return "full"
    c.execute("INSERT INTO session_members(session_id,user_id,joined_at) VALUES(?,?,?)",
              (sid, user_id, now()))
    c.commit()
    return "joined"


def session_leave(sid: int, user_id: int) -> bool:
    c = connect()
    cur = c.execute("DELETE FROM session_members WHERE session_id=? AND user_id=?",
                    (sid, user_id))
    c.commit()
    return cur.rowcount > 0


def session_members(sid: int) -> list:
    c = connect()
    return c.execute("SELECT user_id FROM session_members WHERE session_id=? "
                     "ORDER BY joined_at ASC", (sid,)).fetchall()


def session_member_count(sid: int) -> int:
    c = connect()
    return c.execute("SELECT COUNT(*) n FROM session_members WHERE session_id=?",
                     (sid,)).fetchone()["n"]


def add_scam_report(reporter_id, target_id, proof) -> int:
    c = connect()
    cur = c.execute(
        "INSERT INTO scam_reports(reporter_id,target_id,proof,at) "
        "VALUES(?,?,?,?)",
        (reporter_id, target_id, proof, now()),
    )
    c.commit()
    return cur.lastrowid


def set_collection(user_id: int, status: dict) -> None:
    """Replace a member's whole collection with the given {sprite_id: status}.
    Only non-zero (have/mastered) entries are stored."""
    c = connect()
    c.execute("DELETE FROM collections WHERE user_id=?", (user_id,))
    rows = [(user_id, sid, v) for sid, v in status.items() if v]
    if rows:
        c.executemany(
            "INSERT INTO collections(user_id,sprite_id,status) VALUES(?,?,?)", rows)
    c.commit()


def get_collection(user_id: int) -> dict:
    c = connect()
    rows = c.execute(
        "SELECT sprite_id, status FROM collections WHERE user_id=?",
        (user_id,)).fetchall()
    return {r["sprite_id"]: r["status"] for r in rows}


def has_collection(user_id: int) -> bool:
    c = connect()
    return c.execute("SELECT 1 FROM collections WHERE user_id=? LIMIT 1",
                     (user_id,)).fetchone() is not None


# Exclude opted-out members from every guild-visible aggregate/listing.
_NOT_PRIVATE = "user_id NOT IN (SELECT user_id FROM collection_private)"


def set_collection_private(user_id: int, private: bool) -> None:
    c = connect()
    if private:
        c.execute("INSERT OR IGNORE INTO collection_private(user_id) VALUES(?)",
                  (user_id,))
    else:
        c.execute("DELETE FROM collection_private WHERE user_id=?", (user_id,))
    c.commit()


def is_collection_private(user_id: int) -> bool:
    c = connect()
    return c.execute("SELECT 1 FROM collection_private WHERE user_id=?",
                     (user_id,)).fetchone() is not None


def sprite_holders(sprite_id: int) -> list:
    """User IDs who have (or mastered) a given sprite, mastered first.
    Excludes members who set their collection private."""
    c = connect()
    return c.execute(
        f"SELECT user_id, status FROM collections WHERE sprite_id=? AND status>=1 "
        f"AND {_NOT_PRIVATE} ORDER BY status DESC", (sprite_id,)).fetchall()


def collection_leaderboard(limit: int = 10) -> list:
    """Members ranked by how many sprites they have (non-private only)."""
    c = connect()
    return c.execute(
        f"SELECT user_id, COUNT(*) n, SUM(CASE WHEN status=2 THEN 1 ELSE 0 END) m "
        f"FROM collections WHERE status>=1 AND {_NOT_PRIVATE} GROUP BY user_id "
        f"ORDER BY n DESC, m DESC LIMIT ?", (limit,)).fetchall()


def users_with_collections() -> list:
    """Non-private members who have synced a collection."""
    c = connect()
    return [r["user_id"] for r in c.execute(
        f"SELECT DISTINCT user_id FROM collections WHERE {_NOT_PRIVATE}").fetchall()]


def have_counts() -> dict:
    """sprite_id -> number of (non-private) members who have it (status>=1)."""
    c = connect()
    rows = c.execute(
        f"SELECT sprite_id, COUNT(*) n FROM collections WHERE status>=1 "
        f"AND {_NOT_PRIVATE} GROUP BY sprite_id").fetchall()
    return {r["sprite_id"]: r["n"] for r in rows}


def set_sprite_status(user_id: int, sprite_id: str, status: int) -> None:
    """Set one sprite for a member (status 0 deletes the row)."""
    c = connect()
    if status <= 0:
        c.execute("DELETE FROM collections WHERE user_id=? AND sprite_id=?",
                  (user_id, sprite_id))
    else:
        c.execute(
            "INSERT INTO collections(user_id,sprite_id,status) VALUES(?,?,?) "
            "ON CONFLICT(user_id,sprite_id) DO UPDATE SET status=excluded.status",
            (user_id, sprite_id, status))
    c.commit()


def seconds_since_last_report(reporter_id: int):
    """Seconds since this user's last scam report, or None if they've none."""
    c = connect()
    row = c.execute(
        "SELECT MAX(at) last FROM scam_reports WHERE reporter_id=?",
        (reporter_id,),
    ).fetchone()
    if not row or row["last"] is None:
        return None
    return now() - row["last"]
