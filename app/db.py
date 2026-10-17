"""SQLite layer — one file, one volume, zero config."""
import json, os, sqlite3, datetime as dt

DB_PATH = os.environ.get("DB_PATH", "/data/watcher.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS domains (
  id INTEGER PRIMARY KEY,
  domain TEXT UNIQUE NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  note TEXT NOT NULL DEFAULT '',
  notify TEXT NOT NULL DEFAULT 'discord',
  ping_available INTEGER NOT NULL DEFAULT 1,
  ping_drop INTEGER NOT NULL DEFAULT 1,
  snapshot TEXT,
  warned INTEGER,
  last_check TEXT,
  last_result TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

SEED = [
    ("adept.dev", "lost to a drop-catcher 2026-10-10 — watch for re-drop"),
    ("adeptproductions.com", "dormant since 2005 — watch for lapse"),
    ("adeptproductions.dev", "OWNED — renewal safety net"),
    ("adeptofficial.dev", "fallback name — alert if taken"),
    ("adeptlab.dev", "OWNED — infra-critical"),
]


def conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init() -> None:
    with conn() as c:
        c.executescript(SCHEMA)
        if os.environ.get("WEBHOOK_URL") and not get_setting("discord_webhook"):
            set_setting("discord_webhook", os.environ["WEBHOOK_URL"])
        if os.environ.get("PING_DISCORD_ID") and not get_setting("ping_discord_id"):
            set_setting("ping_discord_id", os.environ["PING_DISCORD_ID"])
        empty = c.execute("SELECT COUNT(*) FROM domains").fetchone()[0] == 0
        if empty and os.environ.get("SEED_WATCHLIST") == "1":
            for d, note in SEED:
                c.execute("INSERT OR IGNORE INTO domains(domain, note) VALUES(?,?)", (d, note))


def get_setting(key: str, default: str = "") -> str:
    with conn() as c:
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                  (key, value))


def list_domains() -> list[sqlite3.Row]:
    with conn() as c:
        return c.execute("SELECT * FROM domains ORDER BY domain").fetchall()


def get_domain(did: int) -> sqlite3.Row | None:
    with conn() as c:
        return c.execute("SELECT * FROM domains WHERE id=?", (did,)).fetchone()


def add_domain(domain: str, note: str = "") -> int:
    with conn() as c:
        cur = c.execute("INSERT INTO domains(domain, note) VALUES(?,?)", (domain, note))
        return cur.lastrowid


def delete_domain(did: int) -> None:
    with conn() as c:
        c.execute("DELETE FROM domains WHERE id=?", (did,))


def toggle(did: int, field: str) -> None:
    assert field in ("enabled", "ping_available", "ping_drop")
    with conn() as c:
        c.execute(f"UPDATE domains SET {field} = 1 - {field} WHERE id=?", (did,))


def set_notify(did: int, channel: str) -> None:
    assert channel in ("discord", "none")
    with conn() as c:
        c.execute("UPDATE domains SET notify=? WHERE id=?", (channel, did))


def save_check(did: int, snapshot: dict, warned: int | None, result: str) -> None:
    with conn() as c:
        c.execute("UPDATE domains SET snapshot=?, warned=?, last_check=?, last_result=? WHERE id=?",
                  (json.dumps(snapshot), warned, dt.datetime.now().isoformat(timespec="seconds"), result, did))
