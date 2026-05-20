import json
import sqlite3
import threading
from typing import Any

from utils.logger import get_logger
from utils.paths import get_database_path

logger = get_logger(__name__)


class DatabaseManager:
    _instance: "DatabaseManager | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._initialized = False
                    cls._instance = inst
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.db_path = get_database_path()
        self._init_db()

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key        TEXT PRIMARY KEY,
                    value      TEXT,
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS installed_packs (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    name             TEXT NOT NULL,
                    source_path      TEXT NOT NULL,
                    tags             TEXT DEFAULT '[]',
                    install_manifest TEXT DEFAULT '{}',
                    installed_at     TEXT DEFAULT (datetime('now')),
                    status           TEXT DEFAULT 'installed'
                );

                CREATE TABLE IF NOT EXISTS history (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    action     TEXT NOT NULL,
                    pack_name  TEXT,
                    details    TEXT,
                    status     TEXT DEFAULT 'success',
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS logs (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    level      TEXT NOT NULL,
                    message    TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                """
            )
        logger.info("Database initialised at %s", self.db_path)

    # ------------------------------------------------------------------ #
    #  Settings                                                            #
    # ------------------------------------------------------------------ #

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._conn() as c:
            row = c.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        if row:
            try:
                return json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                return row["value"]
        return default

    def set_setting(self, key: str, value: Any) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) "
                "VALUES (?, ?, datetime('now'))",
                (key, json.dumps(value)),
            )

    def get_all_settings(self) -> dict[str, Any]:
        with self._conn() as c:
            rows = c.execute("SELECT key, value FROM settings").fetchall()
        result: dict[str, Any] = {}
        for row in rows:
            try:
                result[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                result[row["key"]] = row["value"]
        return result

    def save_settings(self, settings: dict[str, Any]) -> None:
        for k, v in settings.items():
            self.set_setting(k, v)

    # ------------------------------------------------------------------ #
    #  Installed packs                                                     #
    # ------------------------------------------------------------------ #

    def add_installed_pack(
        self,
        name: str,
        source_path: str,
        tags: list[str],
        manifest: dict,
    ) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO installed_packs (name, source_path, tags, install_manifest) "
                "VALUES (?, ?, ?, ?)",
                (name, source_path, json.dumps(tags), json.dumps(manifest)),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def remove_installed_pack(self, name: str) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE installed_packs SET status = 'uninstalled' WHERE name = ?",
                (name,),
            )

    def get_installed_packs(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM installed_packs WHERE status = 'installed' "
                "ORDER BY installed_at DESC"
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["tags"] = json.loads(item.get("tags") or "[]")
            item["install_manifest"] = json.loads(
                item.get("install_manifest") or "{}"
            )
            result.append(item)
        return result

    def get_pack_manifest(self, name: str) -> dict:
        with self._conn() as c:
            row = c.execute(
                "SELECT install_manifest FROM installed_packs "
                "WHERE name = ? AND status = 'installed'",
                (name,),
            ).fetchone()
        if row:
            return json.loads(row["install_manifest"] or "{}")
        return {}

    def is_pack_installed(self, name: str) -> bool:
        with self._conn() as c:
            row = c.execute(
                "SELECT id FROM installed_packs WHERE name = ? AND status = 'installed'",
                (name,),
            ).fetchone()
        return row is not None

    # ------------------------------------------------------------------ #
    #  History                                                             #
    # ------------------------------------------------------------------ #

    def add_history(
        self,
        action: str,
        pack_name: str | None = None,
        details: str | None = None,
        status: str = "success",
    ) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO history (action, pack_name, details, status) VALUES (?,?,?,?)",
                (action, pack_name, details, status),
            )

    def get_history(self, limit: int = 50) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------ #
    #  Logs                                                                #
    # ------------------------------------------------------------------ #

    def add_log(self, level: str, message: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO logs (level, message) VALUES (?, ?)", (level, message)
            )

    def get_logs(self, limit: int = 100) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM logs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
