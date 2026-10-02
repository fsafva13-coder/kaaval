"""SQLite storage: senders, messages, blocks, alerts, antibodies and spend."""
import json
import sqlite3
import threading
from datetime import datetime, timezone

from .config import DB_PATH

_lock = threading.Lock()
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row

SCHEMA = """
CREATE TABLE IF NOT EXISTS senders (
    sender_id   TEXT PRIMARY KEY,
    device_id   TEXT,
    state       TEXT NOT NULL DEFAULT 'trusted',
    refusals    INTEGER NOT NULL DEFAULT 0,
    signals     TEXT NOT NULL DEFAULT '[]',
    profile     TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id   TEXT NOT NULL,
    role        TEXT NOT NULL,
    text        TEXT NOT NULL,
    screen      TEXT,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS blocks (
    sender_id   TEXT PRIMARY KEY,
    device_id   TEXT,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id   TEXT NOT NULL,
    verdict     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    resolved    INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS antibodies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern     TEXT NOT NULL,
    source      TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS spend (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    model       TEXT NOT NULL,
    usd         REAL NOT NULL,
    created_at  TEXT NOT NULL
);
"""

with _lock:
    _conn.executescript(SCHEMA)
    _conn.commit()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    with _lock:
        cur = _conn.execute(sql, params)
        _conn.commit()
        return cur


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with _lock:
        return _conn.execute(sql, params).fetchall()


# --- Senders --------------------------------------------------------------
def get_sender(sender_id: str, device_id: str | None = None) -> dict:
    rows = query("SELECT * FROM senders WHERE sender_id = ?", (sender_id,))
    if not rows:
        execute(
            "INSERT INTO senders (sender_id, device_id, created_at) VALUES (?, ?, ?)",
            (sender_id, device_id, now()),
        )
        rows = query("SELECT * FROM senders WHERE sender_id = ?", (sender_id,))
    row = dict(rows[0])
    row["signals"] = json.loads(row["signals"])
    row["profile"] = json.loads(row["profile"])
    return row


def save_sender(sender: dict) -> None:
    execute(
        "UPDATE senders SET state = ?, refusals = ?, signals = ?, profile = ? WHERE sender_id = ?",
        (
            sender["state"],
            sender["refusals"],
            json.dumps(sorted(set(sender["signals"]))),
            json.dumps(sender["profile"]),
            sender["sender_id"],
        ),
    )


# --- Messages -------------------------------------------------------------
def add_message(sender_id: str, role: str, text: str, screen: dict | None = None) -> None:
    execute(
        "INSERT INTO messages (sender_id, role, text, screen, created_at) VALUES (?, ?, ?, ?, ?)",
        (sender_id, role, text, json.dumps(screen) if screen else None, now()),
    )


def update_last_screen(sender_id: str, screen: dict) -> None:
    """Replace the stored screening verdict of the sender's latest message."""
    execute(
        "UPDATE messages SET screen = ? WHERE id = (SELECT MAX(id) FROM messages WHERE sender_id = ? AND role = 'user')",
        (json.dumps(screen), sender_id),
    )


def history(sender_id: str, limit: int = 20) -> list[dict]:
    rows = query(
        "SELECT role, text, screen, created_at FROM messages WHERE sender_id = ? ORDER BY id DESC LIMIT ?",
        (sender_id, limit),
    )
    out = []
    for r in reversed(rows):
        d = dict(r)
        d["screen"] = json.loads(d["screen"]) if d["screen"] else None
        out.append(d)
    return out


def messages_today(sender_id: str) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    rows = query(
        "SELECT COUNT(*) AS n FROM messages WHERE sender_id = ? AND role = 'user' AND created_at >= ?",
        (sender_id, today),
    )
    return rows[0]["n"]


# --- Blocks ---------------------------------------------------------------
def is_blocked(sender_id: str, device_id: str | None) -> bool:
    rows = query(
        "SELECT 1 FROM blocks WHERE active = 1 AND (sender_id = ? OR (device_id IS NOT NULL AND device_id = ?))",
        (sender_id, device_id or ""),
    )
    return bool(rows)


def block(sender_id: str, device_id: str | None) -> None:
    execute(
        "INSERT OR REPLACE INTO blocks (sender_id, device_id, active, created_at) VALUES (?, ?, 1, ?)",
        (sender_id, device_id, now()),
    )


def unblock(sender_id: str) -> None:
    execute("UPDATE blocks SET active = 0 WHERE sender_id = ?", (sender_id,))
    execute(
        "UPDATE senders SET state = 'trusted', refusals = 0, signals = '[]' WHERE sender_id = ?",
        (sender_id,),
    )
    execute("UPDATE alerts SET resolved = 1 WHERE sender_id = ?", (sender_id,))


# --- Alerts ---------------------------------------------------------------
def add_alert(sender_id: str, verdict: dict) -> None:
    execute(
        "INSERT INTO alerts (sender_id, verdict, created_at) VALUES (?, ?, ?)",
        (sender_id, json.dumps(verdict), now()),
    )


def list_alerts() -> list[dict]:
    rows = query("SELECT * FROM alerts ORDER BY id DESC")
    return [{**dict(r), "verdict": json.loads(r["verdict"])} for r in rows]


# --- Antibodies -----------------------------------------------------------
def add_antibody(pattern: str, source: str) -> None:
    execute(
        "INSERT INTO antibodies (pattern, source, created_at) VALUES (?, ?, ?)",
        (pattern, source, now()),
    )


def list_antibodies() -> list[str]:
    return [r["pattern"] for r in query("SELECT pattern FROM antibodies")]


# --- Spend ----------------------------------------------------------------
def record_spend(model: str, usd: float) -> None:
    execute("INSERT INTO spend (model, usd, created_at) VALUES (?, ?, ?)", (model, usd, now()))


def total_spend() -> float:
    return query("SELECT COALESCE(SUM(usd), 0) AS t FROM spend")[0]["t"]
