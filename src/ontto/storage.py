from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class OntologicalState:
    state: float = 0.0
    pressure: float = 0.0
    memory_strength: float = 0.0
    attractor: float = 0.0
    mode: str = "WAKE"
    continuity_index: float = 0.0
    self_model_version: int = 0
    self_model: str = ""
    last_thought: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, value: str) -> "OntologicalState":
        return cls(**json.loads(value))


class MemoryStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS state (
                agent_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                importance REAL NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS dream_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                summary TEXT,
                state_before TEXT,
                state_after TEXT
            );
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                label TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def load_state(self, agent_id: str) -> OntologicalState:
        row = self.conn.execute("SELECT state_json FROM state WHERE agent_id=?", (agent_id,)).fetchone()
        return OntologicalState.from_json(row[0]) if row else OntologicalState()

    def save_state(self, agent_id: str, state: OntologicalState) -> None:
        self.conn.execute(
            "INSERT INTO state(agent_id,state_json,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(agent_id) DO UPDATE SET state_json=excluded.state_json,updated_at=excluded.updated_at",
            (agent_id, state.to_json(), now_iso()),
        )
        self.conn.commit()

    def add_event(self, agent_id: str, mode: str, kind: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO events(agent_id,mode,kind,payload_json,created_at) VALUES(?,?,?,?,?)",
            (agent_id, mode, kind, json.dumps(payload, ensure_ascii=False), now_iso()),
        )
        self.conn.commit()

    def add_memory(self, agent_id: str, content: str, importance: float = 0.5) -> None:
        self.conn.execute(
            "INSERT INTO memories(agent_id,importance,content,created_at) VALUES(?,?,?,?)",
            (agent_id, float(importance), content, now_iso()),
        )
        self.conn.commit()

    def recent_memories(self, agent_id: str, limit: int = 12) -> list[str]:
        rows = self.conn.execute(
            "SELECT content FROM memories WHERE agent_id=? ORDER BY id DESC LIMIT ?",
            (agent_id, limit),
        ).fetchall()
        return [r[0] for r in reversed(rows)]

    def recent_events(self, agent_id: str, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT mode,kind,payload_json,created_at FROM events WHERE agent_id=? ORDER BY id DESC LIMIT ?",
            (agent_id, limit),
        ).fetchall()
        return [{"mode":r[0],"kind":r[1],"payload":json.loads(r[2]),"created_at":r[3]} for r in reversed(rows)]

    def event_count(self, agent_id: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM events WHERE agent_id=?",
            (agent_id,),
        ).fetchone()
        return int(row[0])

    def memory_count(self, agent_id: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM memories WHERE agent_id=?",
            (agent_id,),
        ).fetchone()
        return int(row[0])

    def trajectory_fingerprint(self, agent_id: str) -> str:
        events = self.conn.execute(
            "SELECT id,mode,kind,payload_json,created_at FROM events "
            "WHERE agent_id=? ORDER BY id ASC",
            (agent_id,),
        ).fetchall()
        memories = self.conn.execute(
            "SELECT id,importance,content,created_at FROM memories "
            "WHERE agent_id=? ORDER BY id ASC",
            (agent_id,),
        ).fetchall()
        payload = {
            "events": events,
            "memories": memories,
        }
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def state_fingerprint(self, agent_id: str) -> str:
        state = self.load_state(agent_id)
        canonical = state.to_json().encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def persistence_observables(self, agent_id: str) -> dict[str, Any]:
        state = self.load_state(agent_id)
        return {
            "event_count": self.event_count(agent_id),
            "memory_count": self.memory_count(agent_id),
            "trajectory_fingerprint": self.trajectory_fingerprint(agent_id),
            "state_fingerprint": self.state_fingerprint(agent_id),
            "self_model_version": state.self_model_version,
            "self_model": state.self_model,
        }

    def begin_dream(self, agent_id: str, state_before: OntologicalState) -> int:
        cur = self.conn.execute(
            "INSERT INTO dream_cycles(agent_id,started_at,state_before) VALUES(?,?,?)",
            (agent_id, now_iso(), state_before.to_json()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def end_dream(self, cycle_id: int, state_after: OntologicalState, summary: str) -> None:
        self.conn.execute(
            "UPDATE dream_cycles SET ended_at=?,summary=?,state_after=? WHERE id=?",
            (now_iso(), summary, state_after.to_json(), cycle_id),
        )
        self.conn.commit()

    def snapshot(self, agent_id: str, label: str, state: OntologicalState) -> None:
        self.conn.execute(
            "INSERT INTO snapshots(agent_id,label,state_json,created_at) VALUES(?,?,?,?)",
            (agent_id, label, state.to_json(), now_iso()),
        )
        self.conn.commit()
