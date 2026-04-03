"""
In-memory SQLite olay günlüğü. İleride dosya veya sunucu veritabanına taşınabilir.
"""
from __future__ import annotations

import csv
import sqlite3
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Literal

FilterKind = Literal["all", "alarms", "system"]


class EventType(str, Enum):
    SYSTEM = "SYSTEM"
    ALARM = "ALARM"
    CLEAR = "CLEAR"
    ERROR = "ERROR"
    COMMAND = "COMMAND"
    SERIAL = "SERIAL"
    STATE_SNAPSHOT = "STATE_SNAPSHOT"


@dataclass
class LogRow:
    id: int
    ts_unix: float
    event_type: str
    angle: int | None
    alarm_active: int  # 0/1 bilinmiyorsa 0
    message: str


class LogService:
    """Thread-safe in-memory SQLite günlük."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_unix REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    angle INTEGER,
                    alarm_state INTEGER NOT NULL DEFAULT 0,
                    extra TEXT
                );
                """
            )

    def add(
        self,
        event_type: str,
        message: str,
        *,
        angle: int | None = None,
        alarm_active: bool = False,
    ) -> int:
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO events (ts_unix, event_type, angle, alarm_state, extra)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    event_type,
                    angle,
                    1 if alarm_active else 0,
                    message,
                ),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    def clear(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM events")
            self._conn.commit()

    def fetch(self, filter_kind: FilterKind, limit: int = 500) -> list[LogRow]:
        where = "1=1"
        params: tuple = ()
        if filter_kind == "alarms":
            where = "event_type IN ('ALARM', 'CLEAR')"
        elif filter_kind == "system":
            where = "event_type IN ('SYSTEM', 'ERROR', 'COMMAND', 'SERIAL')"

        with self._lock:
            cur = self._conn.execute(
                f"""
                SELECT id, ts_unix, event_type, angle, alarm_state, extra
                FROM events
                WHERE {where}
                ORDER BY id DESC
                LIMIT ?
                """,
                (*params, limit),
            )
            rows = cur.fetchall()

        out: list[LogRow] = []
        for r in reversed(rows):
            out.append(
                LogRow(
                    id=r["id"],
                    ts_unix=r["ts_unix"],
                    event_type=r["event_type"],
                    angle=r["angle"],
                    alarm_active=r["alarm_state"],
                    message=r["extra"] or "",
                )
            )
        return out

    def export_csv(self, path: Path, filter_kind: FilterKind = "all") -> int:
        rows = self.fetch(filter_kind, limit=10_000)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "ts_unix", "event_type", "angle", "alarm_state", "extra"])
            for r in rows:
                w.writerow(
                    [r.id, r.ts_unix, r.event_type, r.angle, r.alarm_active, r.message]
                )
        return len(rows)
