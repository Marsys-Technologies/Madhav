#!/usr/bin/env python3
"""CG-0 event store and deterministic campaign projector. Python standard library only."""
from __future__ import annotations

import contextlib
import copy
import datetime as dt
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

EVENT_SCHEMA = "pariprashna-assurance-event@1"
LIFECYCLES = {"NOT_STARTED", "READY", "RUNNING", "BLOCKED", "PAUSED", "IN_VERIFICATION", "COMPLETE", "FAILED"}
HEALTH = {"HEALTHY", "ATTENTION_REQUIRED", "STALE", "INTEGRITY_DEGRADED", "UNKNOWN"}
ROLES = {"STREAM_LEAD", "NATIVE_SURROGATE", "INDEPENDENT_VERIFIER", "PROGRAMME_INTEGRATOR", "NATIVE"}
COMPLETION_EVENTS = {"work_item_accepted", "verification_accepted", "regression_accepted", "stream_closure_recommended", "result_packet_accepted", "gate_closed", "native_acceptance"}
ROLE_EVENTS = {
    "STREAM_LEAD": {"work_started", "scenario_executed", "finding_discovered", "reproduction_recorded", "remediation_proposed", "remediation_implemented", "paused", "blocked", "resumed", "verification_started", "failed", "regression_requested", "correction_recorded"},
    "NATIVE_SURROGATE": {"decision_recorded", "finding_triaged", "remediation_approved", "improvement_parked"},
    "INDEPENDENT_VERIFIER": {"reproduction_accepted", "reproduction_rejected", "verification_accepted", "verification_rejected", "regression_accepted", "regression_rejected", "stream_closure_recommended"},
    "PROGRAMME_INTEGRATOR": {"work_item_accepted", "dependency_resolved", "result_packet_accepted", "integration_baseline_advanced", "gate_closed", "scope_change_approved", "campaign_bootstrapped"},
    "NATIVE": {"native_acceptance"},
}
PHASES = [("P0", "Campaign Control and Live Tracker", 5), ("P1", "Previous-Campaign Takeover and Reconciliation", 8), ("P2", "Known-Blocker Clearance and Safe-to-Test", 17), ("P3", "Six Parallel Closed-Loop Streams", 45), ("P4", "Integration and Cross-Stream Regression", 10), ("P5", "Long-Window Canary and Operational Evidence", 7), ("P6", "Native Acceptance", 5), ("P7", "Release Decision and Campaign Closeout", 3)]
STAGES = [("charter", "Charter, ownership and preflight", 10), ("baseline", "Frozen-baseline investigation", 25), ("triage", "Finding freeze and triage", 10), ("remediation", "Approved remediation", 25), ("verification", "Independent verification", 20), ("regression", "Complete stream regression", 7), ("closure", "Closure packet accepted", 3)]
STREAMS = [("S1", "Navigation, Shell and History"), ("S2", "Conversation and Reading Experience"), ("S3", "Answer Quality and Epistemic Trust"), ("S4", "Pipeline Correctness and Door Parity"), ("S5", "Security, Privacy and Data Integrity"), ("S6", "Performance, Resilience and Observability")]
GATES = [("CG-0", "Control Plane Ready"), ("CG-1", "Takeover Reconciled"), ("CG-2", "Safe to Test"), ("CG-3", "Stream Complete"), ("CG-4", "Integrated Assurance"), ("CG-5", "Operationally Proven"), ("CG-6", "Native Accepted"), ("CG-7", "Release Closed")]
STAGE_NAMES = {stage_id: stage_name for stage_id, stage_name, _ in STAGES}
STREAM_IDS = {stream_id for stream_id, _ in STREAMS}


class RejectedEvent(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def request_fingerprint(request: dict[str, Any]) -> str:
    """Bind idempotency to the actor's complete, server-timestamp-free intent."""
    return digest({key: request.get(key) for key in (
        "actor_id", "idempotency_key", "event_type", "payload", "stream_id",
        "expected_stream_seq", "evidence",
    )})


def parse_time(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def programme_definition(p0b_only: bool = False) -> dict[str, Any]:
    phases = [{"id": pid, "name": name, "campaign_weight": weight, "entry_gate": f"CG-{index - 1}" if index else None, "exit_gate": f"CG-{index}"} for index, (pid, name, weight) in enumerate(PHASES)]
    work_items: list[dict[str, Any]] = []
    for phase in phases:
        if phase["id"] == "P3":
            for sid, title in STREAMS:
                for stage_id, stage_name, weight in STAGES:
                    work_items.append({"id": f"{sid}:{stage_id}", "phase_id": "P3", "stream_id": sid, "title": stage_name, "campaign_points": 7.5 * weight / 100, "kind": "stream_lifecycle"})
        else:
            work_items.append({"id": f"{phase['id']}:completion", "phase_id": phase["id"], "stream_id": None, "title": f"{phase['name']} completion evidence", "campaign_points": float(phase["campaign_weight"]), "kind": "phase_completion"})
    return {"schema_version": "campaign-definition@1", "operator_mode": "P0B_ONLY" if p0b_only else "GENERAL", "campaign": {"id": "pariprashna-experience-assurance-v3", "name": "Paripraśna Experience Assurance Programme v3.0"}, "phases": phases, "streams": [{"id": sid, "name": name, "phase_id": "P3", "campaign_weight": 7.5} for sid, name in STREAMS], "gates": [{"id": gid, "name": name} for gid, name in GATES], "dependencies": [{"from": "P0", "to": "P1"}, {"from": "P1", "to": "P2"}, {"from": "P2", "to": "P3"}, {"from": "P3", "to": "P4"}, {"from": "P4", "to": "P5"}, {"from": "P5", "to": "P6"}, {"from": "P6", "to": "P7"}], "work_items": work_items}


def contains_progress(value: Any) -> bool:
    if isinstance(value, dict):
        return any(k.lower() in {"progress", "percentage", "percent", "completion_pct"} or contains_progress(v) for k, v in value.items())
    if isinstance(value, list):
        return any(contains_progress(v) for v in value)
    return False


class EventStore:
    def __init__(self, runtime_dir: str | Path, *, p0b_only: bool = False, p1_enabled: bool = False):
        if p1_enabled and not p0b_only:
            raise RejectedEvent("P1_ENABLEMENT_MODE", "P1 identity enablement is only defined for the approved P0B runtime")
        self.runtime_dir = Path(runtime_dir)
        self.p0b_only = p0b_only
        self.p1_enabled = p1_enabled
        self.runtime_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
        self._secure_runtime_path(self.runtime_dir, 0o700)
        self.db_path = self.runtime_dir / "control-plane.sqlite3"
        self._lock = threading.RLock()
        self.init()

    @staticmethod
    def _secure_runtime_path(path: Path, mode: int) -> None:
        status = path.stat()
        if status.st_uid != os.getuid():
            raise RejectedEvent("RUNTIME_OWNER", f"{path} is not owned by the current account")
        os.chmod(path, mode)

    def _secure_runtime_files(self) -> None:
        self._secure_runtime_path(self.runtime_dir, 0o700)
        for path in (self.db_path, self.runtime_dir / "control-plane.sqlite3-wal", self.runtime_dir / "control-plane.sqlite3-shm"):
            try:
                if path.exists():
                    self._secure_runtime_path(path, 0o600)
            except FileNotFoundError:
                # SQLite may remove its transient WAL/SHM files between exists() and chmod().
                continue

    @contextlib.contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.db_path, timeout=10, isolation_level=None, check_same_thread=False)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        try:
            yield con
        finally:
            con.close()
            self._secure_runtime_files()

    def init(self) -> None:
        with self.connection() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                  ledger_seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
                  schema_version TEXT NOT NULL, idempotency_key TEXT NOT NULL,
                  request_fingerprint TEXT NOT NULL,
                  stream_id TEXT, stream_seq INTEGER, actor_id TEXT NOT NULL, actor_role TEXT NOT NULL,
                  event_type TEXT NOT NULL, payload_json TEXT NOT NULL, evidence_json TEXT NOT NULL,
                  occurred_at TEXT NOT NULL, prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL UNIQUE
                );
                CREATE UNIQUE INDEX IF NOT EXISTS events_actor_idempotency_key ON events(actor_id, idempotency_key);
                CREATE UNIQUE INDEX IF NOT EXISTS events_stream_seq ON events(stream_id, stream_seq) WHERE stream_id IS NOT NULL;
                CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
                CREATE TABLE IF NOT EXISTS stream_sequences (stream_id TEXT PRIMARY KEY, current_seq INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS ledger_meta (id INTEGER PRIMARY KEY CHECK (id=1), last_hash TEXT NOT NULL, definition_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS rejected_events (id INTEGER PRIMARY KEY AUTOINCREMENT, received_at TEXT NOT NULL, actor_id TEXT, idempotency_key TEXT, code TEXT NOT NULL, message TEXT NOT NULL, request_json TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS rejected_no_update BEFORE UPDATE ON rejected_events BEGIN SELECT RAISE(ABORT, 'rejections are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS rejected_no_delete BEFORE DELETE ON rejected_events BEGIN SELECT RAISE(ABORT, 'rejections are append-only'); END;
                CREATE TABLE IF NOT EXISTS actors (actor_id TEXT PRIMARY KEY, role TEXT NOT NULL, streams_json TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE);
                CREATE TABLE IF NOT EXISTS p1_actors (actor_id TEXT PRIMARY KEY, role TEXT NOT NULL, streams_json TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE);
                CREATE TABLE IF NOT EXISTS presences (session_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, stream_id TEXT, state TEXT NOT NULL, observed_at TEXT NOT NULL, detail TEXT);
                CREATE TABLE IF NOT EXISTS projection_state (id INTEGER PRIMARY KEY CHECK (id=1), canonical_json TEXT NOT NULL, projection_hash TEXT NOT NULL, as_of TEXT NOT NULL, event_count INTEGER NOT NULL, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS projector_health (id INTEGER PRIMARY KEY CHECK (id=1), status TEXT NOT NULL, last_error TEXT, last_success_at TEXT, lag_events INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS monitor_health (id INTEGER PRIMARY KEY CHECK (id=1), status TEXT NOT NULL, last_error TEXT, last_success_at TEXT);
            """)
            definition = canonical(programme_definition(self.p0b_only))
            stored_definition = con.execute("SELECT definition_json FROM ledger_meta WHERE id=1").fetchone()
            if not stored_definition:
                con.execute("INSERT INTO ledger_meta(id,last_hash,definition_json) VALUES(1,?,?)", ("0" * 64, definition))
            elif stored_definition["definition_json"] != definition:
                raise RejectedEvent("DEFINITION_INTEGRITY", "programme definition does not match this immutable source release")
            if not con.execute("SELECT 1 FROM projector_health WHERE id=1").fetchone():
                con.execute("INSERT INTO projector_health(id,status,lag_events) VALUES(1,'UNKNOWN',0)")
            if not con.execute("SELECT 1 FROM monitor_health WHERE id=1").fetchone():
                con.execute("INSERT INTO monitor_health(id,status) VALUES(1,'UNKNOWN')")
            self._seed_actors(con)

    def _seed_actors(self, con: sqlite3.Connection) -> None:
        if self.p0b_only:
            rows = (("lead-p0b", "STREAM_LEAD", ["P0"]), ("surrogate-p0b", "NATIVE_SURROGATE", ["P0"]), ("verifier-p0b", "INDEPENDENT_VERIFIER", ["P0"]), ("integrator-p0b", "PROGRAMME_INTEGRATOR", ["P0"]))
            for actor_id, role, streams in rows:
                con.execute("INSERT OR IGNORE INTO actors(actor_id,role,streams_json,token_hash) VALUES(?,?,?,?)", (actor_id, role, canonical(streams), secrets.token_hex(32)))
            if self.p1_enabled:
                p1_rows = (("lead-p1", "STREAM_LEAD", ["P1"]), ("surrogate-p1", "NATIVE_SURROGATE", ["P1"]), ("verifier-p1", "INDEPENDENT_VERIFIER", ["P1"]), ("integrator-p1", "PROGRAMME_INTEGRATOR", ["P1"]))
                for actor_id, role, streams in p1_rows:
                    con.execute("INSERT OR IGNORE INTO p1_actors(actor_id,role,streams_json,token_hash) VALUES(?,?,?,?)", (actor_id, role, canonical(streams), secrets.token_hex(32)))
            return
        all_streams = [sid for sid, _ in STREAMS] + ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
        rows = *[(f"lead-{phase_id.lower()}", "STREAM_LEAD", [phase_id]) for phase_id, _, _ in PHASES], *[(f"lead-{sid.lower()}", "STREAM_LEAD", [sid]) for sid, _ in STREAMS], ("surrogate", "NATIVE_SURROGATE", all_streams), ("verifier", "INDEPENDENT_VERIFIER", all_streams), ("integrator", "PROGRAMME_INTEGRATOR", all_streams), ("native", "NATIVE", all_streams)
        for actor_id, role, streams in rows:
            con.execute("INSERT OR IGNORE INTO actors(actor_id,role,streams_json,token_hash) VALUES(?,?,?,?)", (actor_id, role, canonical(streams), secrets.token_hex(32)))

    def provision_local_credentials(self) -> dict[str, Any]:
        """Create once-per-runtime credentials for local CG-0 proof; never commit them."""
        target = self.runtime_dir / "local-credentials.json"
        try:
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            raise RejectedEvent("CREDENTIALS_EXIST", f"credentials already exist at {target}; do not overwrite them") from None
        credentials: dict[str, str] = {}
        try:
            with self._lock, self.connection() as con:
                con.execute("BEGIN IMMEDIATE")
                for row in con.execute("SELECT actor_id FROM actors ORDER BY actor_id"):
                    token = secrets.token_urlsafe(32)
                    credentials[row["actor_id"]] = token
                    con.execute("UPDATE actors SET token_hash=? WHERE actor_id=?", (hashlib.sha256(token.encode()).hexdigest(), row["actor_id"]))
                con.execute("COMMIT")
            with os.fdopen(descriptor, "w", encoding="utf-8") as credential_file:
                descriptor = -1
                credential_file.write(canonical({"schema_version": "local-credentials@1", "created_at": now_iso(), "tokens": credentials}) + "\n")
                credential_file.flush(); os.fsync(credential_file.fileno())
        except Exception:
            if descriptor >= 0: os.close(descriptor)
            target.unlink(missing_ok=True)
            raise
        return {"path": str(target), "actors": sorted(credentials)}

    def provision_p1_credentials(self) -> dict[str, Any]:
        """Issue P1-only tokens once without exposing or rotating P0B credentials."""
        if not self.p0b_only or not self.p1_enabled:
            raise RejectedEvent("P1_ENABLEMENT_REQUIRED", "P1 credentials require the explicit approved P1 enablement mode")
        target = self.runtime_dir / "p1-credentials.json"
        try:
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            raise RejectedEvent("P1_CREDENTIALS_EXIST", f"P1 credentials already exist at {target}; do not overwrite them") from None
        credentials: dict[str, str] = {}
        try:
            with self._lock, self.connection() as con:
                con.execute("BEGIN IMMEDIATE")
                if not self._p0_to_p1_dependency_resolved(con):
                    con.execute("ROLLBACK")
                    raise RejectedEvent("P1_DEPENDENCY_UNRESOLVED", "P1 credentials require the durable P0-to-P1 dependency receipt")
                rows = con.execute("SELECT actor_id FROM p1_actors ORDER BY actor_id").fetchall()
                if {row["actor_id"] for row in rows} != {"lead-p1", "surrogate-p1", "verifier-p1", "integrator-p1"}:
                    con.execute("ROLLBACK")
                    raise RejectedEvent("P1_IDENTITIES_UNAVAILABLE", "the approved P1 identity set is incomplete")
                for row in rows:
                    token = secrets.token_urlsafe(32)
                    credentials[row["actor_id"]] = token
                    con.execute("UPDATE p1_actors SET token_hash=? WHERE actor_id=?", (hashlib.sha256(token.encode()).hexdigest(), row["actor_id"]))
                con.execute("COMMIT")
            with os.fdopen(descriptor, "w", encoding="utf-8") as credential_file:
                descriptor = -1
                credential_file.write(canonical({"schema_version": "p1-credentials@1", "created_at": now_iso(), "tokens": credentials}) + "\n")
                credential_file.flush(); os.fsync(credential_file.fileno())
        except Exception:
            if descriptor >= 0: os.close(descriptor)
            target.unlink(missing_ok=True)
            raise
        return {"path": str(target), "actors": sorted(credentials)}

    def _actor(self, con: sqlite3.Connection, actor_id: str) -> sqlite3.Row | None:
        actor = con.execute("SELECT * FROM actors WHERE actor_id=?", (actor_id,)).fetchone()
        if actor is None and self.p1_enabled:
            actor = con.execute("SELECT * FROM p1_actors WHERE actor_id=?", (actor_id,)).fetchone()
        return actor

    @staticmethod
    def _p0_to_p1_dependency_resolved(con: sqlite3.Connection) -> bool:
        for row in con.execute("SELECT payload_json FROM events WHERE event_type='dependency_resolved' ORDER BY ledger_seq"):
            payload = json.loads(row["payload_json"])
            if payload.get("from") == "P0" and payload.get("to") == "P1":
                return True
        return False

    def definition(self) -> dict[str, Any]:
        with self.connection() as con:
            return json.loads(con.execute("SELECT definition_json FROM ledger_meta WHERE id=1").fetchone()[0])

    def authenticate(self, token: str) -> str | None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self.connection() as con:
            row = con.execute("SELECT actor_id FROM actors WHERE token_hash=?", (token_hash,)).fetchone()
            if row is None and self.p1_enabled:
                row = con.execute("SELECT actor_id FROM p1_actors WHERE token_hash=?", (token_hash,)).fetchone()
        return row[0] if row else None

    def actor_role(self, actor_id: str) -> str | None:
        with self.connection() as con:
            row = self._actor(con, actor_id)
        return row["role"] if row else None

    def next_stream_seq(self, stream_id: str) -> int:
        with self.connection() as con:
            row = con.execute("SELECT current_seq FROM stream_sequences WHERE stream_id=?", (stream_id,)).fetchone()
        return (row[0] if row else 0)

    def events(self) -> list[dict[str, Any]]:
        with self.connection() as con:
            rows = con.execute("SELECT * FROM events ORDER BY ledger_seq").fetchall()
        return [{**dict(r), "payload": json.loads(r["payload_json"]), "evidence": json.loads(r["evidence_json"])} for r in rows]

    def _record_rejection(self, request: dict[str, Any], code: str, message: str) -> None:
        with self.connection() as con:
            con.execute("INSERT INTO rejected_events(received_at,actor_id,idempotency_key,code,message,request_json) VALUES(?,?,?,?,?,?)", (now_iso(), request.get("actor_id"), request.get("idempotency_key"), code, message, canonical(request)))

    def rejected(self) -> list[dict[str, Any]]:
        with self.connection() as con:
            rows = con.execute("SELECT * FROM rejected_events ORDER BY id DESC").fetchall()
        return [{**dict(r), "request": json.loads(r["request_json"])} for r in rows]

    def submit(self, request: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            try:
                result = self._submit(request)
                if not result["idempotent"]:
                    self.rebuild()
                return result
            except RejectedEvent as exc:
                self._record_rejection(request, exc.code, str(exc))
                raise

    def _submit(self, request: dict[str, Any]) -> dict[str, Any]:
        required = {"actor_id", "idempotency_key", "event_type", "payload"}
        if required - request.keys():
            raise RejectedEvent("SCHEMA", f"missing fields: {sorted(required - request.keys())}")
        if contains_progress(request["payload"]):
            raise RejectedEvent("MANUAL_PROGRESS_FORBIDDEN", "events cannot contain progress or percentage")
        if not isinstance(request["payload"], dict) or not isinstance(request.get("evidence", []), list):
            raise RejectedEvent("SCHEMA", "payload must be object and evidence must be array")
        stream_id = request.get("stream_id")
        if stream_id is not None and not isinstance(stream_id, str):
            raise RejectedEvent("SCHEMA", "stream_id must be string or null")
        evidence = request.get("evidence", [])
        if request["event_type"] in COMPLETION_EVENTS | {"dependency_resolved"} and not evidence:
            raise RejectedEvent("EVIDENCE_REQUIRED", f"{request['event_type']} requires primary evidence")
        if any(not isinstance(e, dict) or not e.get("uri") or not e.get("kind") for e in evidence):
            raise RejectedEvent("EVIDENCE_SCHEMA", "each evidence item requires kind and uri")
        if "occurred_at" in request:
            raise RejectedEvent("OCCURRED_AT_FORBIDDEN", "the server assigns event occurrence time")
        with self._lock, self.connection() as con:
            con.execute("BEGIN IMMEDIATE")
            actor = self._actor(con, request["actor_id"])
            if not actor:
                con.execute("ROLLBACK")
                raise RejectedEvent("UNAUTHENTICATED", "unknown actor")
            role = actor["role"]
            event_type = request["event_type"]
            if event_type not in ROLE_EVENTS.get(role, set()):
                con.execute("ROLLBACK")
                raise RejectedEvent("ROLE_FORBIDDEN", f"{role} cannot emit {event_type}")
            streams = json.loads(actor["streams_json"])
            p0b_onboarding_handoff = (
                self.p0b_only
                and request["actor_id"] == "integrator-p0b"
                and event_type == "dependency_resolved"
                and stream_id == "P1"
                and request["payload"].get("from") == "P0"
                and request["payload"].get("to") == "P1"
            )
            if stream_id and stream_id not in streams and not p0b_onboarding_handoff:
                con.execute("ROLLBACK")
                raise RejectedEvent("STREAM_FORBIDDEN", f"{request['actor_id']} does not own {stream_id}")
            fingerprint = request_fingerprint(request)
            existing = con.execute(
                "SELECT * FROM events WHERE actor_id=? AND idempotency_key=?",
                (request["actor_id"], request["idempotency_key"]),
            ).fetchone()
            if existing:
                if existing["request_fingerprint"] != fingerprint:
                    con.execute("ROLLBACK")
                    raise RejectedEvent("IDEMPOTENCY_CONFLICT", "idempotency key was already used for a different request")
                con.execute("COMMIT")
                return {"accepted": True, "idempotent": True, "event": self._row_event(existing)}
            self._validate_transition(con, request, role)
            stream_seq = None
            if stream_id:
                row = con.execute("SELECT current_seq FROM stream_sequences WHERE stream_id=?", (stream_id,)).fetchone()
                current = row[0] if row else 0
                if request.get("expected_stream_seq") != current:
                    con.execute("ROLLBACK")
                    raise RejectedEvent("SEQUENCE_CONFLICT", f"expected {request.get('expected_stream_seq')}, current {current}")
                stream_seq = current + 1
                con.execute("INSERT INTO stream_sequences(stream_id,current_seq) VALUES(?,?) ON CONFLICT(stream_id) DO UPDATE SET current_seq=excluded.current_seq", (stream_id, stream_seq))
            previous = con.execute("SELECT last_hash FROM ledger_meta WHERE id=1").fetchone()[0]
            occurred_at = now_iso()
            body = {"schema_version": EVENT_SCHEMA, "event_id": str(uuid.uuid4()), "idempotency_key": request["idempotency_key"], "request_fingerprint": fingerprint, "stream_id": stream_id, "stream_seq": stream_seq, "actor_id": request["actor_id"], "actor_role": role, "event_type": event_type, "payload": request["payload"], "evidence": evidence, "occurred_at": occurred_at, "prev_hash": previous}
            event_hash = digest(body)
            con.execute("INSERT INTO events(event_id,schema_version,idempotency_key,request_fingerprint,stream_id,stream_seq,actor_id,actor_role,event_type,payload_json,evidence_json,occurred_at,prev_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (body["event_id"], EVENT_SCHEMA, body["idempotency_key"], fingerprint, stream_id, stream_seq, body["actor_id"], role, event_type, canonical(request["payload"]), canonical(evidence), occurred_at, previous, event_hash))
            con.execute("UPDATE ledger_meta SET last_hash=? WHERE id=1", (event_hash,))
            row = con.execute("SELECT * FROM events WHERE event_id=?", (body["event_id"],)).fetchone()
            con.execute("COMMIT")
        return {"accepted": True, "idempotent": False, "event": self._row_event(row)}

    def _validate_transition(self, con: sqlite3.Connection, request: dict[str, Any], role: str) -> None:
        typ, payload = request["event_type"], request["payload"]
        stream_id = request.get("stream_id")
        if typ == "campaign_bootstrapped" and con.execute("SELECT COUNT(*) FROM events").fetchone()[0] != 0:
            raise RejectedEvent("INVALID_TRANSITION", "campaign may only bootstrap from an empty log")
        state_events = {"work_started": "RUNNING", "paused": "PAUSED", "blocked": "BLOCKED", "resumed": "RUNNING", "verification_started": "IN_VERIFICATION", "failed": "FAILED"}
        if typ in state_events and stream_id:
            states = {"work_started": {"NOT_STARTED", "READY"}, "paused": {"RUNNING", "IN_VERIFICATION"}, "blocked": {"RUNNING", "IN_VERIFICATION"}, "resumed": {"PAUSED", "BLOCKED"}, "verification_started": {"RUNNING"}, "failed": {"RUNNING", "IN_VERIFICATION", "PAUSED", "BLOCKED"}}
            current = "NOT_STARTED"
            for row in con.execute("SELECT event_type FROM events WHERE stream_id=? ORDER BY ledger_seq", (stream_id,)):
                current = state_events.get(row["event_type"], current)
            if current not in states[typ]:
                raise RejectedEvent("INVALID_TRANSITION", f"{typ} is not allowed from {current}")
        if typ == "work_started":
            if stream_id == "P1" and not self._p0_to_p1_dependency_resolved(con):
                raise RejectedEvent("P1_DEPENDENCY_UNRESOLVED", "P1 work cannot start before the durable P0-to-P1 dependency receipt")
            session_id = payload.get("session_id")
            if not isinstance(session_id, str) or not session_id.strip():
                raise RejectedEvent("SESSION_ID_REQUIRED", "a work_started event requires a non-empty session_id")
            for row in con.execute("SELECT payload_json FROM events WHERE event_type='work_started'"):
                if json.loads(row["payload_json"]).get("session_id") == session_id:
                    raise RejectedEvent("SESSION_ID_CONFLICT", "session_id is already owned by an existing execution session")
            participants = payload.get("participants", [])
            if not isinstance(participants, list):
                raise RejectedEvent("PARTICIPANT_ROSTER_INVALID", "participants must be a list when supplied")
            participant_ids: set[str] = set()
            for participant in participants:
                if not isinstance(participant, dict) or not isinstance(participant.get("actor_id"), str) or not participant["actor_id"].strip():
                    raise RejectedEvent("PARTICIPANT_ROSTER_INVALID", "each participant requires a non-empty actor_id")
                if participant["actor_id"] in participant_ids or participant.get("role") not in ROLES | {"SPECIALIST"} or participant.get("state") not in {"ACTIVE", "WAITING", "PAUSED", "COMPLETED"}:
                    raise RejectedEvent("PARTICIPANT_ROSTER_INVALID", "participant actor, role, and state must be valid and unique")
                if participant["role"] != "SPECIALIST":
                    registered = self._actor(con, participant["actor_id"])
                    if not registered or registered["role"] != participant["role"]:
                        raise RejectedEvent("PARTICIPANT_ROSTER_UNVERIFIED", "known-role participants must match a registered actor and role")
                    if stream_id and stream_id not in json.loads(registered["streams_json"]):
                        raise RejectedEvent("PARTICIPANT_ROSTER_UNVERIFIED", "known-role participants must be eligible for the execution stream")
                participant_ids.add(participant["actor_id"])
            if stream_id in STREAM_IDS:
                planned = payload.get("planned_scenarios")
                if not isinstance(planned, int) or isinstance(planned, bool) or planned <= 0:
                    raise RejectedEvent("SCENARIO_DENOMINATOR_REQUIRED", "a stream charter must freeze a positive planned_scenarios denominator")
                stage = payload.get("lifecycle_stage", "charter")
                if stage not in STAGE_NAMES:
                    raise RejectedEvent("STAGE_SCHEMA", "lifecycle_stage must be a defined stream stage")
        if typ == "scenario_executed":
            if stream_id not in STREAM_IDS or not isinstance(payload.get("scenario_id"), str) or not payload["scenario_id"].strip():
                raise RejectedEvent("SCENARIO_SCHEMA", "scenario execution requires a known stream and non-empty scenario_id")
            planned, scoped_ids, previous = self._scenario_contract(con, stream_id)
            if not isinstance(planned, int):
                raise RejectedEvent("SCENARIO_DENOMINATOR_REQUIRED", "scenario execution requires a chartered planned_scenarios denominator")
            if payload["scenario_id"] in previous:
                raise RejectedEvent("DUPLICATE_SCENARIO", "a scenario can be executed only once per stream")
            if len(previous) >= planned + len(scoped_ids):
                raise RejectedEvent("SCENARIO_DENOMINATOR_EXCEEDED", "executed scenarios cannot exceed the frozen denominator")
        if typ == "work_item_accepted":
            item = payload.get("work_item_id")
            known_items = {w["id"] for w in self.definition()["work_items"]}
            scoped_items = {w["id"]: w for w in self.definition()["work_items"]}
            for row in con.execute("SELECT payload_json FROM events WHERE event_type='scope_change_approved' ORDER BY ledger_seq"):
                additions = json.loads(row["payload_json"])["added_work_items"]
                known_items.update(x["id"] for x in additions); scoped_items.update({x["id"]: x for x in additions})
            if item not in known_items:
                raise RejectedEvent("UNKNOWN_WORK_ITEM", "work item is not in the accepted denominator")
            item_target = scoped_items[item].get("stream_id") or scoped_items[item]["phase_id"]
            if stream_id != item_target:
                raise RejectedEvent("WORK_ITEM_TARGET", "work-item acceptance must be written to its declared stream or phase")
            verification_id = payload.get("verification_event_id")
            verification = con.execute("SELECT event_type,actor_role,stream_id,payload_json FROM events WHERE event_id=?", (verification_id,)).fetchone()
            verification_payload = json.loads(verification["payload_json"]) if verification else {}
            if not verification or verification["event_type"] not in {"verification_accepted", "regression_accepted"} or verification["actor_role"] != "INDEPENDENT_VERIFIER" or verification["stream_id"] != item_target or verification_payload.get("work_item_id") != item or not verification_payload.get("finder_actor_id") or not verification_payload.get("fixer_actor_id"):
                raise RejectedEvent("VERIFICATION_REQUIRED", "work item acceptance needs its linked independent verification event")
            item_stream = scoped_items[item].get("stream_id")
            if item_stream:
                current = fold(self.definition(), [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")], now_iso())
                stream = next(s for s in current["streams"] if s["id"] == item_stream)
                if stream["lifecycle"] == "FAILED":
                    raise RejectedEvent("INVALID_TRANSITION", "failed stream cannot receive completion credit")
                stage_ids = [stage_id for stage_id, _, _ in STAGES]
                expected_id = next((stage_id for stage_id in stage_ids if item == f"{item_stream}:{stage_id}"), None)
                if expected_id:
                    prior = stage_ids[:stage_ids.index(expected_id)]
                    accepted = {work_item["id"] for work_item in current["work_items"] if work_item["accepted"]}
                    if any(f"{item_stream}:{stage_id}" not in accepted for stage_id in prior):
                        raise RejectedEvent("WORK_ITEM_ORDER", "stream lifecycle work items must be accepted in order")
                    if expected_id == "closure":
                        raise RejectedEvent("RESULT_PACKET_REQUIRED", "closure credit is issued only by result_packet_accepted")
                    if expected_id == "regression":
                        scenarios = stream["scenarios"]
                        required_scope_ids = set(stream["scope_scenario_ids"])
                        if scenarios["planned"] is None or scenarios["executed"] != scenarios["planned"] or not required_scope_ids.issubset(set(stream["scenario_ids"])):
                            raise RejectedEvent("REGRESSION_INCOMPLETE", "regression credit requires every chartered and scope-approved scenario to be executed")
                    if expected_id == "remediation":
                        plan = self._remediation_contract(con, item_stream)
                        if plan is None:
                            raise RejectedEvent("REMEDIATION_PLAN_REQUIRED", "remediation credit requires a triage-frozen remediation plan")
                        current_remediations = {remediation["id"]: remediation for remediation in current["remediations"]}
                        incomplete = [entry["id"] for entry in plan if current_remediations.get(entry["id"], {}).get("status") != "VERIFIED"]
                        if incomplete:
                            raise RejectedEvent("REMEDIATION_INCOMPLETE", f"remediation credit requires independently verified planned remediations: {incomplete}")
        if typ == "finding_triaged":
            finding_id = payload.get("finding_id")
            discovered = any(json.loads(row["payload_json"]).get("finding_id") == finding_id and row["stream_id"] == stream_id for row in con.execute("SELECT stream_id,payload_json FROM events WHERE event_type='finding_discovered'"))
            if not discovered:
                raise RejectedEvent("FINDING_REFERENCE_REQUIRED", "triage must reference a discovered finding in the same stream")
        if typ == "finding_discovered":
            finding_id = payload.get("finding_id")
            if stream_id not in STREAM_IDS or not isinstance(finding_id, str) or not finding_id.strip() or payload.get("severity") not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
                raise RejectedEvent("FINDING_SCHEMA", "a finding needs a known stream, unique non-empty id, and declared severity")
            if any(json.loads(row["payload_json"]).get("finding_id") == finding_id for row in con.execute("SELECT payload_json FROM events WHERE event_type='finding_discovered'")):
                raise RejectedEvent("FINDING_ID_CONFLICT", "a finding identifier may be discovered once")
            if self._remediation_contract(con, stream_id) is not None:
                raise RejectedEvent("FINDING_FREEZE", "a new finding after the frozen remediation plan requires a separately governed scope path")
        if typ == "remediation_approved" and "remediation_plan" in payload:
            plan = payload["remediation_plan"]
            if stream_id not in STREAM_IDS or not isinstance(plan, list):
                raise RejectedEvent("REMEDIATION_PLAN_SCHEMA", "a remediation plan must be an array for a known stream")
            if self._remediation_contract(con, stream_id) is not None:
                raise RejectedEvent("REMEDIATION_PLAN_LOCKED", "a stream remediation plan is frozen after triage")
            current = fold(self.definition(), [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")], now_iso())
            stream_findings = {finding["id"]: finding for finding in current["findings"] if finding["stream_id"] == stream_id}
            if any(finding["status"] != "TRIAGED" for finding in stream_findings.values()):
                raise RejectedEvent("TRIAGE_INCOMPLETE", "every discovered stream finding must be triaged before freezing remediation work")
            plan_ids: set[str] = set()
            planned_findings: set[str] = set()
            for entry in plan:
                if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not entry["id"].strip() or not isinstance(entry.get("finding_id"), str) or entry["finding_id"] not in stream_findings or entry["id"] in plan_ids or entry["finding_id"] in planned_findings:
                    raise RejectedEvent("REMEDIATION_PLAN_SCHEMA", "each plan entry needs unique id and a unique triaged finding from this stream")
                plan_ids.add(entry["id"]); planned_findings.add(entry["finding_id"])
            if set(stream_findings) != planned_findings:
                raise RejectedEvent("REMEDIATION_PLAN_SCHEMA", "the frozen remediation plan must account for every triaged stream finding")
        if typ == "remediation_implemented":
            plan = self._remediation_contract(con, stream_id or "")
            remediation_id = payload.get("remediation_id")
            finding_id = payload.get("finding_id")
            matched = next((entry for entry in plan or [] if entry["id"] == remediation_id and entry["finding_id"] == finding_id), None)
            if not matched:
                raise RejectedEvent("REMEDIATION_CONTRACT", "implemented remediation must be a planned remediation for its finding")
            if any(json.loads(row["payload_json"]).get("remediation_id") == remediation_id for row in con.execute("SELECT payload_json FROM events WHERE event_type='remediation_implemented'")):
                raise RejectedEvent("REMEDIATION_CONTRACT", "a planned remediation may be implemented once")
        if typ in {"verification_accepted", "verification_rejected"} and payload.get("remediation_id") is not None:
            plan = self._remediation_contract(con, stream_id or "")
            remediation_id = payload.get("remediation_id")
            finding_id = payload.get("finding_id")
            matched = next((entry for entry in plan or [] if entry["id"] == remediation_id and entry["finding_id"] == finding_id), None)
            if not matched:
                raise RejectedEvent("REMEDIATION_VERIFICATION_REFERENCE", "remediation verification must name the planned remediation and its finding in the same stream")
            implemented = any(json.loads(row["payload_json"]).get("remediation_id") == remediation_id and json.loads(row["payload_json"]).get("finding_id") == finding_id and row["stream_id"] == stream_id for row in con.execute("SELECT stream_id,payload_json FROM events WHERE event_type='remediation_implemented'"))
            if not implemented:
                raise RejectedEvent("REMEDIATION_VERIFICATION_REFERENCE", "remediation verification requires the matching implemented remediation")
        if typ == "dependency_resolved":
            if not isinstance(payload.get("from"), str) or not payload["from"].strip() or not isinstance(payload.get("to"), str) or not payload["to"].strip():
                raise RejectedEvent("DEPENDENCY_SCHEMA", "dependency resolution must name non-empty source and destination phases")
            dependency = (payload["from"], payload["to"])
            if dependency not in {(item["from"], item["to"]) for item in self.definition()["dependencies"]}:
                raise RejectedEvent("DEPENDENCY_SCHEMA", "dependency resolution must name a defined dependency edge")
            if stream_id != payload["to"]:
                raise RejectedEvent("DEPENDENCY_TARGET", "dependency resolution must be written to its downstream phase")
            if any((json.loads(row["payload_json"]).get("from"), json.loads(row["payload_json"]).get("to")) == dependency for row in con.execute("SELECT payload_json FROM events WHERE event_type='dependency_resolved'")):
                raise RejectedEvent("DEPENDENCY_ALREADY_RESOLVED", "a dependency edge may be resolved once")
            if self.p0b_only and dependency == ("P0", "P1"):
                current = fold(self.definition(), [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")], now_iso())
                if not any(gate["id"] == "CG-0" and gate["status"] == "CLOSED" for gate in current["gates"]):
                    raise RejectedEvent("P0B_HANDOFF_PREREQUISITE", "P0-to-P1 onboarding requires closed CG-0")
        if typ == "verification_accepted":
            finder = payload.get("finder_actor_id")
            fixer = payload.get("fixer_actor_id")
            if request["actor_id"] in {finder, fixer}:
                raise RejectedEvent("SELF_VERIFICATION", "finder/fixer cannot independently verify closure")
        if typ == "stream_closure_recommended" and payload.get("finder_actor_id") == request["actor_id"]:
            raise RejectedEvent("SELF_VERIFICATION", "finder cannot recommend its own stream closure")
        if typ == "gate_closed":
            gate = payload.get("gate_id")
            if gate not in {g[0] for g in GATES}:
                raise RejectedEvent("UNKNOWN_GATE", "unknown gate")
            if gate == "CG-6":
                raise RejectedEvent("NATIVE_REQUIRED", "CG-6 requires native_acceptance, not a gate closure")
            required_phase = f"P{gate[-1]}"
            if stream_id != required_phase:
                raise RejectedEvent("GATE_TARGET", "gate closure must be written to its corresponding phase")
            verification = con.execute("SELECT event_type,actor_role,stream_id,payload_json FROM events WHERE event_id=?", (payload.get("verification_event_id"),)).fetchone()
            verification_payload = json.loads(verification["payload_json"]) if verification else {}
            if not verification or verification["event_type"] not in {"verification_accepted", "regression_accepted"} or verification["actor_role"] != "INDEPENDENT_VERIFIER" or verification["stream_id"] != required_phase or verification_payload.get("gate_id") != gate or not verification_payload.get("finder_actor_id") or not verification_payload.get("fixer_actor_id"):
                raise RejectedEvent("VERIFICATION_REQUIRED", "gate closure needs its linked independent gate verification")
            current = fold(self.definition(), [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")], now_iso())
            phase = next(p for p in current["phases"] if p["id"] == required_phase)
            if phase["completion_pct"] != 100:
                raise RejectedEvent("GATE_PREREQUISITE", f"{gate} requires all {required_phase} work items accepted")
            gate_number = int(gate[-1])
            if gate_number and not any(g["id"] == f"CG-{gate_number - 1}" and g["status"] == "CLOSED" for g in current["gates"]):
                raise RejectedEvent("GATE_PREREQUISITE", f"{gate} requires CG-{gate_number - 1} to be closed")
            if gate == "CG-3":
                packets = {json.loads(row["payload_json"]).get("stream_id") for row in con.execute("SELECT payload_json FROM events WHERE event_type='result_packet_accepted'")}
                if packets != {sid for sid, _ in STREAMS}:
                    raise RejectedEvent("GATE_PREREQUISITE", "CG-3 requires an accepted result packet for every stream")
        if typ == "result_packet_accepted":
            packet_stream = payload.get("stream_id")
            if packet_stream not in {sid for sid, _ in STREAMS}:
                raise RejectedEvent("RESULT_PACKET_SCHEMA", "result packet needs a known stream_id")
            if stream_id != packet_stream:
                raise RejectedEvent("RESULT_PACKET_TARGET", "result packet acceptance must be written to its packet stream")
            current = fold(self.definition(), [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")], now_iso())
            stream = next(s for s in current["streams"] if s["id"] == packet_stream)
            if stream["lifecycle"] == "FAILED":
                raise RejectedEvent("FAILED_STREAM", "a failed stream cannot receive result-packet closure credit")
            pending = [item["id"] for item in current["work_items"] if item.get("stream_id") == packet_stream and item["id"] != f"{packet_stream}:closure" and not item["accepted"]]
            if pending:
                raise RejectedEvent("RESULT_PACKET_PREREQUISITE", f"result packet requires every non-closure stream work item accepted: {pending}")
            scenarios = stream["scenarios"]
            if scenarios["planned"] is None or scenarios["executed"] != scenarios["planned"] or not set(stream["scope_scenario_ids"]).issubset(set(stream["scenario_ids"])):
                raise RejectedEvent("RESULT_PACKET_PREREQUISITE", "result packet requires every chartered and scope-approved scenario to be executed")
            closure = con.execute("SELECT 1 FROM events WHERE stream_id=? AND event_type='stream_closure_recommended' AND actor_role='INDEPENDENT_VERIFIER'", (packet_stream,)).fetchone()
            if not closure:
                raise RejectedEvent("RESULT_PACKET_PREREQUISITE", "result packet requires an independent stream closure recommendation")
        if typ == "native_acceptance":
            if stream_id != "P6":
                raise RejectedEvent("NATIVE_TARGET", "native acceptance must be written to P6")
            current = fold(self.definition(), [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")], now_iso())
            p6 = next(p for p in current["phases"] if p["id"] == "P6")
            cg5 = next(g for g in current["gates"] if g["id"] == "CG-5")
            if p6["completion_pct"] != 100 or cg5["status"] != "CLOSED":
                raise RejectedEvent("GATE_PREREQUISITE", "native acceptance requires complete P6 evidence and closed CG-5")
        if typ == "scope_change_approved":
            additions = payload.get("added_work_items")
            scenarios = payload.get("added_scenarios", [])
            if not isinstance(additions, list) or not additions or not isinstance(scenarios, list) or not payload.get("reason"):
                raise RejectedEvent("SCOPE_CHANGE_SCHEMA", "approved scope change needs reason and added_work_items")
            if any(not isinstance(item, dict) for item in additions):
                raise RejectedEvent("SCOPE_CHANGE_SCHEMA", "each added work item must be an object")
            known_ids = {w["id"] for w in self.definition()["work_items"]}
            for row in con.execute("SELECT payload_json FROM events WHERE event_type='scope_change_approved'"):
                known_ids.update(x["id"] for x in json.loads(row["payload_json"])["added_work_items"])
            declared_scenarios = {(scenario.get("id"), scenario.get("stream_id")) for scenario in scenarios if isinstance(scenario, dict)}
            for item in additions:
                if not all(k in item for k in ("id", "phase_id", "title", "campaign_points")):
                    raise RejectedEvent("SCOPE_CHANGE_SCHEMA", "each added work item needs id, phase_id, title, campaign_points")
                if item["id"] in known_ids or item["id"] in {x["id"] for x in additions if x is not item} or item["phase_id"] not in {p[0] for p in PHASES} or item.get("stream_id") not in {None, *STREAM_IDS} or not isinstance(item["campaign_points"], (int, float)) or isinstance(item["campaign_points"], bool) or not 0 < item["campaign_points"] <= 100:
                    raise RejectedEvent("SCOPE_CHANGE_SCHEMA", "scope changes may only add new positive work items in known phases")
                if item.get("kind") == "scenario" and (item.get("scenario_id"), item.get("stream_id")) not in declared_scenarios:
                    raise RejectedEvent("SCOPE_CHANGE_SCHEMA", "a scenario work item must reference a matching explicitly added scenario")
            known_scenarios = set()
            for row in con.execute("SELECT payload_json FROM events WHERE event_type='scope_change_approved'"):
                known_scenarios.update(scenario["id"] for scenario in json.loads(row["payload_json"]).get("added_scenarios", []))
            new_scenario_ids: set[str] = set()
            for scenario in scenarios:
                if not isinstance(scenario, dict) or not isinstance(scenario.get("id"), str) or not scenario["id"].strip() or scenario.get("stream_id") not in STREAM_IDS or scenario["id"] in known_scenarios or scenario["id"] in new_scenario_ids:
                    raise RejectedEvent("SCOPE_CHANGE_SCHEMA", "each added scenario needs a globally unique id and known stream_id")
                _, _, executed = self._scenario_contract(con, scenario["stream_id"])
                if scenario["id"] in executed:
                    raise RejectedEvent("SCOPE_CHANGE_SCHEMA", "a scope-approved scenario cannot already have been executed")
                new_scenario_ids.add(scenario["id"])
        if typ == "correction_recorded":
            corrected = payload.get("corrects_event_id")
            exists = con.execute("SELECT 1 FROM events WHERE event_id=?", (corrected,)).fetchone()
            if not corrected or not exists or not payload.get("reason"):
                raise RejectedEvent("CORRECTION_REFERENCE_REQUIRED", "corrections must name an existing event and a reason")

    @staticmethod
    def _scenario_contract(con: sqlite3.Connection, stream_id: str) -> tuple[int | None, list[str], list[str]]:
        started = con.execute("SELECT payload_json FROM events WHERE stream_id=? AND event_type='work_started' ORDER BY ledger_seq LIMIT 1", (stream_id,)).fetchone()
        planned = json.loads(started["payload_json"]).get("planned_scenarios") if started else None
        scoped_ids: list[str] = []
        for row in con.execute("SELECT payload_json FROM events WHERE event_type='scope_change_approved' ORDER BY ledger_seq"):
            scoped_ids.extend(scenario["id"] for scenario in json.loads(row["payload_json"]).get("added_scenarios", []) if scenario.get("stream_id") == stream_id)
        executed = [json.loads(row["payload_json"]).get("scenario_id") for row in con.execute("SELECT payload_json FROM events WHERE stream_id=? AND event_type='scenario_executed'", (stream_id,))]
        return planned, scoped_ids, executed

    @staticmethod
    def _remediation_contract(con: sqlite3.Connection, stream_id: str) -> list[dict[str, Any]] | None:
        for row in con.execute("SELECT payload_json FROM events WHERE stream_id=? AND event_type='remediation_approved' ORDER BY ledger_seq", (stream_id,)):
            payload = json.loads(row["payload_json"])
            if "remediation_plan" in payload:
                return payload["remediation_plan"]
        return None

    @staticmethod
    def _row_event(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        result["evidence"] = json.loads(result.pop("evidence_json"))
        return result

    @staticmethod
    def _event_body(event: dict[str, Any]) -> dict[str, Any]:
        return {key: event[key] for key in ("schema_version", "event_id", "idempotency_key", "request_fingerprint", "stream_id", "stream_seq", "actor_id", "actor_role", "event_type", "payload", "evidence", "occurred_at", "prev_hash")}

    def _verify_event_chain(self, con: sqlite3.Connection) -> tuple[bool, str, str]:
        meta = con.execute("SELECT last_hash,definition_json FROM ledger_meta WHERE id=1").fetchone()
        if not meta or meta["definition_json"] != canonical(programme_definition(self.p0b_only)):
            return False, "programme definition mismatch", "0" * 64
        previous = "0" * 64
        for row in con.execute("SELECT * FROM events ORDER BY ledger_seq"):
            event = self._row_event(row)
            if event["prev_hash"] != previous:
                return False, "event previous hash mismatch", previous
            current = digest(self._event_body(event))
            if event["event_hash"] != current:
                return False, "event hash mismatch", previous
            previous = current
        if meta["last_hash"] != previous:
            return False, "ledger root hash mismatch", previous
        return True, "ok", previous

    def record_presence(self, actor_id: str, session_id: str, stream_id: str | None, state: str, detail: str = "", observed_at: str | None = None) -> None:
        if state not in {"ACTIVE", "WAITING", "PAUSED", "COMPLETED"}:
            raise RejectedEvent("PRESENCE_SCHEMA", "invalid presence state")
        with self.connection() as con:
            actor = self._actor(con, actor_id)
            if not actor or (stream_id and stream_id not in json.loads(actor["streams_json"])):
                raise RejectedEvent("STREAM_FORBIDDEN", "presence actor does not own stream")
            session = None
            for row in con.execute("SELECT actor_id,stream_id,payload_json FROM events WHERE event_type='work_started' ORDER BY ledger_seq"):
                payload = json.loads(row["payload_json"])
                if payload.get("session_id") == session_id:
                    session = {"owner": row["actor_id"], "stream_id": row["stream_id"]}
                    break
            if not session:
                raise RejectedEvent("UNKNOWN_SESSION", "presence requires a durable work_started session")
            if session["owner"] != actor_id or session["stream_id"] != stream_id:
                raise RejectedEvent("PRESENCE_FORBIDDEN", "only the session owner may update its matching presence")
            con.execute("INSERT INTO presences(session_id,actor_id,stream_id,state,observed_at,detail) VALUES(?,?,?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET actor_id=excluded.actor_id,stream_id=excluded.stream_id,state=excluded.state,observed_at=excluded.observed_at,detail=excluded.detail", (session_id, actor_id, stream_id, state, observed_at or now_iso(), detail))

    def rebuild(self, as_of: str | None = None) -> dict[str, Any]:
        as_of = as_of or now_iso()
        with self._lock, self.connection() as con:
            con.execute("BEGIN IMMEDIATE")
            chain_ok, chain_reason, _ = self._verify_event_chain(con)
            if not chain_ok:
                con.execute("UPDATE projector_health SET status='INTEGRITY_DEGRADED',last_error=?,lag_events=1 WHERE id=1", (chain_reason,))
                con.execute("COMMIT")
                raise RejectedEvent("LEDGER_INTEGRITY", chain_reason)
            definition = json.loads(con.execute("SELECT definition_json FROM ledger_meta WHERE id=1").fetchone()[0])
            events = [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")]
            projection = fold(definition, events, as_of)
            projection_hash = digest(projection)
            con.execute("INSERT INTO projection_state(id,canonical_json,projection_hash,as_of,event_count,updated_at) VALUES(1,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET canonical_json=excluded.canonical_json,projection_hash=excluded.projection_hash,as_of=excluded.as_of,event_count=excluded.event_count,updated_at=excluded.updated_at", (canonical(projection), projection_hash, as_of, len(events), now_iso()))
            con.execute("UPDATE projector_health SET status='HEALTHY',last_error=NULL,last_success_at=?,lag_events=0 WHERE id=1", (now_iso(),))
            con.execute("COMMIT")
        return projection

    def verify_replay(self) -> dict[str, Any]:
        with self.connection() as con:
            state = con.execute("SELECT * FROM projection_state WHERE id=1").fetchone()
            chain_ok, chain_reason, chain_hash = self._verify_event_chain(con)
        if not state:
            return {"ok": False, "reason": "no projection"}
        if not chain_ok:
            with self.connection() as con:
                con.execute("UPDATE projector_health SET status=?,last_error=?,lag_events=? WHERE id=1", ("INTEGRITY_DEGRADED", chain_reason, 1))
            return {"ok": False, "reason": chain_reason, "event_log_hash": chain_hash, "as_of": state["as_of"]}
        replay = fold(self.definition(), self.events(), state["as_of"])
        actual = digest(replay)
        try:
            materialized_hash = digest(json.loads(state["canonical_json"]))
        except json.JSONDecodeError:
            materialized_hash = "invalid-json"
        ok = actual == state["projection_hash"] and materialized_hash == state["projection_hash"]
        with self.connection() as con:
            con.execute("UPDATE projector_health SET status=?,last_error=?,lag_events=? WHERE id=1", ("HEALTHY" if ok else "INTEGRITY_DEGRADED", None if ok else "full replay hash mismatch", 0 if ok else 1))
        return {"ok": ok, "reason": "ok" if ok else "full replay hash mismatch", "expected_hash": state["projection_hash"], "actual_hash": actual, "materialized_hash": materialized_hash, "event_log_hash": chain_hash, "as_of": state["as_of"]}

    def record_monitor_status(self, status: str, error: str | None = None) -> None:
        if status not in {"HEALTHY", "INTEGRITY_DEGRADED", "UNKNOWN"}:
            raise ValueError("invalid monitor status")
        with self.connection() as con:
            con.execute("UPDATE monitor_health SET status=?,last_error=?,last_success_at=? WHERE id=1", (status, error, now_iso() if status == "HEALTHY" else None))

    def projection(self, as_of: str | None = None) -> dict[str, Any]:
        with self.connection() as con:
            state = con.execute("SELECT * FROM projection_state WHERE id=1").fetchone()
            health = dict(con.execute("SELECT * FROM projector_health WHERE id=1").fetchone())
            monitor = dict(con.execute("SELECT * FROM monitor_health WHERE id=1").fetchone())
            rows = con.execute("SELECT * FROM presences").fetchall()
        if not state:
            self.rebuild(as_of)
            return self.projection(as_of)
        try:
            canonical_projection = json.loads(state["canonical_json"])
        except json.JSONDecodeError:
            canonical_projection = {}
        integrity = self.verify_replay()
        # A corrupt materialization must still produce a safe, inspectable response rather
        # than a 500. Reconstruct only the display shape from the durable log; integrity
        # remains false and the overlay forces every affected surface out of green.
        if not isinstance(canonical_projection, dict) or not {"phases", "streams", "execution_sessions"}.issubset(canonical_projection):
            canonical_projection = fold(self.definition(), self.events(), state["as_of"])
        monitor_safe = monitor["status"] == "HEALTHY" or monitor["last_error"] is None
        overlay = presence_overlay(canonical_projection, [dict(r) for r in rows], as_of or now_iso(), integrity["ok"] and monitor_safe)
        display = copy.deepcopy(canonical_projection)
        for stream in display["streams"]: stream["health"] = overlay["stream_health"].get(stream["id"], "UNKNOWN")
        for phase in display["phases"]: phase["health"] = overlay["phase_health"].get(phase["id"], "UNKNOWN")
        return {"schema_version": "campaign-projection@1", "canonical": canonical_projection, "display": display, "canonical_hash": state["projection_hash"], "projection_as_of": state["as_of"], "integrity": integrity, "projector_health": health, "monitor_health": monitor, "liveness": overlay, "rejected_events": self.rejected()}

    def export_snapshot(self, path: str | Path) -> dict[str, Any]:
        # The durable event log, ledger root, and materialized projection must come from
        # one SQLite read snapshot.  Holding the process lock also prevents an in-process
        # writer from slipping an event between any two exported fields.
        with self._lock, self.connection() as con:
            con.execute("BEGIN")
            try:
                state = con.execute("SELECT * FROM projection_state WHERE id=1").fetchone()
                chain_ok, chain_reason, chain_hash = self._verify_event_chain(con)
                events = [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")]
                definition = json.loads(con.execute("SELECT definition_json FROM ledger_meta WHERE id=1").fetchone()[0])
                if not state or not chain_ok:
                    raise RejectedEvent("INTEGRITY_DEGRADED", chain_reason if not chain_ok else "cannot export without a projection")
                try:
                    materialized = json.loads(state["canonical_json"])
                except json.JSONDecodeError as exc:
                    raise RejectedEvent("INTEGRITY_DEGRADED", "materialized projection is invalid") from exc
                replay = fold(definition, events, state["as_of"])
                replay_hash = digest(replay)
                if state["event_count"] != len(events) or replay_hash != state["projection_hash"] or digest(materialized) != state["projection_hash"]:
                    raise RejectedEvent("INTEGRITY_DEGRADED", "snapshot sources do not reconcile")
                projection = {
                    "schema_version": "campaign-projection@1",
                    "canonical": materialized,
                    "canonical_hash": state["projection_hash"],
                    "projection_as_of": state["as_of"],
                }
                snapshot = {"schema_version": "immutable-snapshot@1", "exported_at": now_iso(), "projection": projection, "events": events, "event_log_hash": digest(events), "ledger_root_hash": chain_hash}
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        protected_runtime_files = {
            self.db_path.resolve(),
            (self.runtime_dir / "control-plane.sqlite3-wal").resolve(),
            (self.runtime_dir / "control-plane.sqlite3-shm").resolve(),
            (self.runtime_dir / "local-credentials.json").resolve(),
        }
        if target.resolve(strict=False) in protected_runtime_files:
            raise RejectedEvent("SNAPSHOT_PATH_FORBIDDEN", "snapshot path cannot replace a protected runtime file")
        if target.exists() or target.is_symlink():
            raise RejectedEvent("SNAPSHOT_TARGET_EXISTS", "snapshot target already exists; immutable snapshots are never overwritten")
        tmp = target.parent / f".{target.name}.{uuid.uuid4().hex}.tmp"
        descriptor = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        published = False
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as snapshot_file:
                descriptor = -1
                snapshot_file.write(canonical(snapshot) + "\n")
                snapshot_file.flush()
                os.fsync(snapshot_file.fileno())
            # link(2) is an atomic create-only publish: a competing target wins and this
            # export fails closed instead of replacing its immutable snapshot.
            os.link(tmp, target)
            published = True
            os.chmod(target, 0o400)
            target_descriptor = os.open(target, os.O_RDONLY)
            try:
                os.fsync(target_descriptor)
            finally:
                os.close(target_descriptor)
            directory_descriptor = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
            tmp.unlink()
        except Exception:
            if descriptor >= 0:
                os.close(descriptor)
            tmp.unlink(missing_ok=True)
            if not published:
                # The existing target, if any, belongs to the competing writer and is never
                # removed by this exporter.
                pass
            raise
        return {"path": str(target), "snapshot_hash": digest(snapshot), "event_log_hash": snapshot["event_log_hash"]}

    def restore_snapshot(self, path: str | Path) -> dict[str, Any]:
        """Restore a validated snapshot only into an initialized but otherwise empty runtime."""
        try:
            snapshot = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RejectedEvent("SNAPSHOT_INVALID", f"snapshot cannot be read: {exc}") from exc
        events = snapshot.get("events")
        if snapshot.get("schema_version") != "immutable-snapshot@1" or not isinstance(events, list) or snapshot.get("event_log_hash") != digest(events):
            raise RejectedEvent("SNAPSHOT_INVALID", "snapshot schema or event-log hash is invalid")
        source_projection = snapshot.get("projection")
        if not isinstance(source_projection, dict) or not isinstance(source_projection.get("projection_as_of"), str) or not isinstance(source_projection.get("canonical"), dict) or not isinstance(source_projection.get("canonical_hash"), str):
            raise RejectedEvent("SNAPSHOT_INVALID", "snapshot projection envelope is invalid")
        restored_projection = fold(programme_definition(self.p0b_only), events, source_projection["projection_as_of"])
        restored_hash = digest(restored_projection)
        if source_projection["canonical"] != restored_projection or source_projection["canonical_hash"] != restored_hash:
            raise RejectedEvent("SNAPSHOT_RECONCILIATION", "snapshot projection does not reconcile with its event log")
        with self._lock, self.connection() as con:
            con.execute("BEGIN IMMEDIATE")
            if con.execute("SELECT COUNT(*) FROM events").fetchone()[0] or con.execute("SELECT COUNT(*) FROM rejected_events").fetchone()[0] or con.execute("SELECT 1 FROM projection_state WHERE id=1").fetchone():
                con.execute("ROLLBACK")
                raise RejectedEvent("RECOVERY_RUNTIME_NOT_EMPTY", "restore requires a separate empty recovery runtime")
            previous = "0" * 64
            for event in events:
                if not isinstance(event, dict) or event.get("prev_hash") != previous or event.get("event_hash") != digest(self._event_body(event)):
                    con.execute("ROLLBACK")
                    raise RejectedEvent("SNAPSHOT_INTEGRITY", "snapshot event chain is invalid")
                previous = event["event_hash"]
            if snapshot.get("ledger_root_hash") != previous:
                con.execute("ROLLBACK")
                raise RejectedEvent("SNAPSHOT_INTEGRITY", "snapshot ledger root hash is invalid")
            for event in events:
                if not isinstance(event.get("request_fingerprint"), str):
                    con.execute("ROLLBACK")
                    raise RejectedEvent("SNAPSHOT_INTEGRITY", "snapshot event is missing its idempotency fingerprint")
                con.execute("INSERT INTO events(event_id,schema_version,idempotency_key,request_fingerprint,stream_id,stream_seq,actor_id,actor_role,event_type,payload_json,evidence_json,occurred_at,prev_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (event["event_id"], event["schema_version"], event["idempotency_key"], event["request_fingerprint"], event["stream_id"], event["stream_seq"], event["actor_id"], event["actor_role"], event["event_type"], canonical(event["payload"]), canonical(event["evidence"]), event["occurred_at"], event["prev_hash"], event["event_hash"]))
                if event["stream_id"]:
                    con.execute("INSERT INTO stream_sequences(stream_id,current_seq) VALUES(?,?) ON CONFLICT(stream_id) DO UPDATE SET current_seq=MAX(current_seq,excluded.current_seq)", (event["stream_id"], event["stream_seq"]))
            con.execute("UPDATE ledger_meta SET last_hash=? WHERE id=1", (previous,))
            con.execute("INSERT INTO projection_state(id,canonical_json,projection_hash,as_of,event_count,updated_at) VALUES(1,?,?,?,?,?)", (canonical(restored_projection), restored_hash, source_projection["projection_as_of"], len(events), now_iso()))
            con.execute("UPDATE projector_health SET status='HEALTHY',last_error=NULL,last_success_at=?,lag_events=0 WHERE id=1", (now_iso(),))
            con.execute("COMMIT")
        return {"canonical_hash": restored_hash, "event_log_hash": snapshot["event_log_hash"], "restored_at": now_iso()}


def fold(definition: dict[str, Any], events: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
    """Pure durable state projection. Presence is intentionally not an input."""
    items = {item["id"]: {**copy.deepcopy(item), "accepted": False, "evidence": [], "accepted_by": None} for item in definition["work_items"]}
    phases = {p["id"]: {**copy.deepcopy(p), "lifecycle": "NOT_STARTED", "health": "UNKNOWN", "last_evidence_at": None, "responsible_session": None} for p in definition["phases"]}
    streams = {s["id"]: {**copy.deepcopy(s), "lifecycle": "NOT_STARTED", "health": "UNKNOWN", "last_evidence_at": None, "next_checkpoint": None, "blocker_reason": None, "scenario_ids": [], "scope_scenario_ids": [], "remediation_plan": None, "execution_session": None} for s in definition["streams"]}
    gates = {g["id"]: {**copy.deepcopy(g), "status": "OPEN", "evidence": [], "closed_by": None} for g in definition["gates"]}
    dependencies = {(dependency["from"], dependency["to"]): {**copy.deepcopy(dependency), "status": "PENDING", "evidence": [], "resolved_by": None, "resolved_at": None} for dependency in definition["dependencies"]}
    findings: dict[str, Any] = {}; remediations: dict[str, Any] = {}; verifications: dict[str, Any] = {}; decisions: list[dict[str, Any]] = []; sessions: dict[str, Any] = {}; scope_changes: list[dict[str, Any]] = []
    bootstrapped = False; demonstration = False
    for event in events:
        typ, payload, evidence = event["event_type"], event["payload"], event["evidence"]
        phase_id = payload.get("phase_id") or ("P3" if event.get("stream_id") in streams else event.get("stream_id"))
        if typ == "campaign_bootstrapped":
            bootstrapped = True; demonstration = payload.get("campaign_id") == "demo"; phases["P0"]["lifecycle"] = "RUNNING"
        elif typ == "work_started":
            sid = payload.get("session_id")
            if sid:
                sessions[sid] = {"id": sid, "conversation_id": payload.get("conversation_id", sid), "conversation_uri": payload.get("conversation_uri"), "stream_id": event.get("stream_id"), "owner": event["actor_id"], "verifier": payload.get("verifier"), "participants": payload.get("participants", []), "model": payload.get("model"), "reasoning_config": payload.get("reasoning_config"), "branch": payload.get("branch"), "worktree": payload.get("worktree"), "baseline_sha": payload.get("baseline_sha"), "current_sha": payload.get("current_sha"), "pr": payload.get("pr"), "ci": payload.get("ci"), "deployed_revision": payload.get("deployed_revision"), "lifecycle_stage": payload.get("lifecycle_stage", "charter"), "planned_scenarios": payload.get("planned_scenarios"), "lifecycle": "RUNNING", "started_at": event["occurred_at"], "last_evidence": evidence, "last_evidence_at": event["occurred_at"], "last_meaningful_action": payload.get("assignment"), "assignment": payload.get("assignment"), "next_checkpoint": payload.get("next_checkpoint"), "ceiling": payload.get("ceiling"), "cost": payload.get("cost")}
            if event.get("stream_id") in streams: streams[event["stream_id"]]["lifecycle"] = "RUNNING"; streams[event["stream_id"]]["next_checkpoint"] = payload.get("next_checkpoint")
            elif phase_id in phases: phases[phase_id]["lifecycle"] = "RUNNING"; phases[phase_id]["responsible_session"] = sid
        elif typ in {"paused", "blocked", "resumed", "verification_started", "failed"}:
            target = streams.get(event.get("stream_id")) or phases.get(phase_id)
            states = {"paused": "PAUSED", "blocked": "BLOCKED", "resumed": "RUNNING", "verification_started": "IN_VERIFICATION", "failed": "FAILED"}
            if target: target["lifecycle"] = states[typ]; target["last_evidence_at"] = event["occurred_at"]
            if target and typ == "blocked": target["blocker_reason"] = payload.get("reason", "No blocker reason recorded")
            if target and typ == "resumed": target["blocker_reason"] = None
            for session in sessions.values():
                if session.get("stream_id") == event.get("stream_id"):
                    session["lifecycle"] = states[typ]; session["last_meaningful_action"] = payload.get("assignment") or typ; session["last_evidence"] = evidence; session["last_evidence_at"] = event["occurred_at"]
        elif typ == "scenario_executed" and event.get("stream_id") in streams:
            streams[event["stream_id"]]["scenario_ids"].append(payload["scenario_id"])
        elif typ == "finding_discovered":
            fid = payload.get("finding_id");
            if fid: findings[fid] = {"id": fid, "stream_id": event.get("stream_id"), "severity": payload.get("severity", "UNTRIAGED"), "status": "OPEN", "root_cause_group": payload.get("root_cause_group"), "evidence": evidence, "finder": event["actor_id"]}
        elif typ == "finding_triaged":
            fid = payload.get("finding_id");
            if fid in findings: findings[fid].update({"status": "TRIAGED", "severity": payload.get("severity", findings[fid]["severity"]), "surrogate_decision": True})
        elif typ == "remediation_implemented":
            rid = payload.get("remediation_id")
            if rid: remediations[rid] = {"id": rid, "finding_id": payload.get("finding_id"), "stream_id": event.get("stream_id"), "status": "AWAITING_VERIFICATION", "fixer": event["actor_id"], "evidence": evidence}
        elif typ == "remediation_approved" and "remediation_plan" in payload and event.get("stream_id") in streams:
            streams[event["stream_id"]]["remediation_plan"] = copy.deepcopy(payload["remediation_plan"])
        elif typ in {"verification_accepted", "verification_rejected"}:
            vid = payload.get("verification_id", event["event_id"]); verifications[vid] = {"id": vid, "status": "ACCEPTED" if typ == "verification_accepted" else "REJECTED", "verifier": event["actor_id"], "finding_id": payload.get("finding_id"), "remediation_id": payload.get("remediation_id"), "evidence": evidence}
            rid = payload.get("remediation_id")
            if rid in remediations: remediations[rid]["status"] = "VERIFIED" if typ == "verification_accepted" else "REWORK_REQUIRED"
        elif typ == "work_item_accepted":
            wid = payload["work_item_id"]
            if wid in items: items[wid].update({"accepted": True, "evidence": evidence, "accepted_by": event["actor_id"], "accepted_at": event["occurred_at"]})
        elif typ == "scope_change_approved":
            before_total = sum(item["campaign_points"] for item in items.values())
            before_earned = sum(item["campaign_points"] for item in items.values() if item["accepted"])
            additions = payload["added_work_items"]
            for item in additions:
                if item["id"] not in items: items[item["id"]] = {**item, "accepted": False, "evidence": [], "accepted_by": None, "kind": item.get("kind", "scope_change")}
            for scenario in payload.get("added_scenarios", []):
                streams[scenario["stream_id"]]["scope_scenario_ids"].append(scenario["id"])
            after_total = sum(item["campaign_points"] for item in items.values())
            scope_changes.append({"event_id": event["event_id"], "reason": payload["reason"], "added_work_items": [x["id"] for x in additions], "added_scenarios": [x["id"] for x in payload.get("added_scenarios", [])], "evidence": evidence, "at": event["occurred_at"], "completion_before_pct": round(100 * before_earned / before_total, 2) if before_total else 0, "completion_after_pct": round(100 * before_earned / after_total, 2) if after_total else 0})
        elif typ == "dependency_resolved":
            dependencies[(payload["from"], payload["to"])].update({"status": "RESOLVED", "evidence": evidence, "resolved_by": event["actor_id"], "resolved_at": event["occurred_at"]})
        elif typ in {"decision_recorded", "remediation_approved", "improvement_parked"}:
            decisions.append({"event_id": event["event_id"], "label": "SURROGATE DECISION — not native acceptance", "decision": payload.get("decision") or payload.get("reason") or typ, "kind": typ, "requires_a3": bool(payload.get("requires_a3")), "evidence": evidence})
        elif typ == "gate_closed":
            gate = payload["gate_id"]; gates[gate].update({"status": "CLOSED", "evidence": evidence, "closed_by": event["actor_id"]})
        elif typ == "native_acceptance":
            gates["CG-6"].update({"status": "CLOSED", "evidence": evidence, "closed_by": event["actor_id"]})
        elif typ == "result_packet_accepted":
            closure_id = f"{payload['stream_id']}:closure"
            if streams[payload["stream_id"]]["lifecycle"] != "FAILED":
                items[closure_id].update({"accepted": True, "evidence": evidence, "accepted_by": event["actor_id"], "accepted_at": event["occurred_at"]})
        if phase_id in phases and evidence: phases[phase_id]["last_evidence_at"] = event["occurred_at"]
        if event.get("stream_id") in streams and evidence: streams[event["stream_id"]]["last_evidence_at"] = event["occurred_at"]
    total = sum(item["campaign_points"] for item in items.values())
    earned = sum(item["campaign_points"] for item in items.values() if item["accepted"])
    ordered_phase_ids = [p["id"] for p in definition["phases"]]
    for phase_id, phase in phases.items():
        phase_items = [i for i in items.values() if i["phase_id"] == phase_id]
        denominator = sum(i["campaign_points"] for i in phase_items); numerator = sum(i["campaign_points"] for i in phase_items if i["accepted"])
        phase["completion_pct"] = round(100 * numerator / denominator, 2) if denominator else 0.0
        phase["work_items"] = {"accepted": sum(i["accepted"] for i in phase_items), "total": len(phase_items)}
        if bootstrapped and phase_id != "P0" and phase["lifecycle"] == "NOT_STARTED":
            predecessor = phases[ordered_phase_ids[ordered_phase_ids.index(phase_id) - 1]]
            phase["lifecycle"] = "READY" if predecessor["completion_pct"] == 100 else "NOT_STARTED"
        if phase_items and all(i["accepted"] for i in phase_items):
            phase["lifecycle"] = "COMPLETE"
    for sid, stream in streams.items():
        stream_items = [i for i in items.values() if i.get("stream_id") == sid]
        stream["completion_pct"] = round(100 * sum(i["campaign_points"] for i in stream_items if i["accepted"]) / sum(i["campaign_points"] for i in stream_items), 2)
        if stream_items and all(i["accepted"] for i in stream_items) and stream["lifecycle"] != "FAILED": stream["lifecycle"] = "COMPLETE"
        stream_sessions = [session for session in sessions.values() if session.get("stream_id") == sid]
        stream_sessions.sort(key=lambda session: session.get("started_at") or "", reverse=True)
        stream["execution_session"] = stream_sessions[0] if stream_sessions else None
        planned_scenarios = stream["execution_session"].get("planned_scenarios") if stream["execution_session"] else None
        stream["scenarios"] = {"planned": planned_scenarios + len(stream["scope_scenario_ids"]) if planned_scenarios is not None else None, "executed": len(stream["scenario_ids"])}
        next_stage = next((stage_id for stage_id, _, _ in STAGES if not items[f"{sid}:{stage_id}"]["accepted"]), "closure")
        stream["lifecycle_stage"] = {"id": next_stage, "name": STAGE_NAMES[next_stage]}
        if stream["execution_session"]:
            stream["execution_session"]["lifecycle_stage"] = next_stage
            if stream["lifecycle"] == "COMPLETE": stream["execution_session"]["lifecycle"] = "COMPLETE"
        stream["findings"] = [f for f in findings.values() if f["stream_id"] == sid]
        stream["findings_by_severity"] = {severity: sum(f["severity"] == severity for f in stream["findings"]) for severity in sorted({f["severity"] for f in stream["findings"]})}
        stream["blockers"] = [{"reason": stream["blocker_reason"]}] if stream["blocker_reason"] else []
        stream["fixed_awaiting_verification"] = sum(r["stream_id"] == sid and r["status"] == "AWAITING_VERIFICATION" for r in remediations.values())
        stream["independently_closed"] = sum(r["stream_id"] == sid and r["status"] == "VERIFIED" for r in remediations.values())
        planned_remediations = stream["remediation_plan"]
        stream["remediations"] = {"planned": len(planned_remediations) if planned_remediations is not None else None, "implemented": sum(r["stream_id"] == sid for r in remediations.values()), "verified": stream["independently_closed"]}
    stream_states = {s["lifecycle"] for s in streams.values()}
    if stream_states == {"COMPLETE"}:
        phases["P3"]["lifecycle"] = "COMPLETE"
    elif "RUNNING" in stream_states:
        phases["P3"]["lifecycle"] = "RUNNING"
    elif "IN_VERIFICATION" in stream_states:
        phases["P3"]["lifecycle"] = "IN_VERIFICATION"
    elif "BLOCKED" in stream_states:
        phases["P3"]["lifecycle"] = "BLOCKED"
    elif "PAUSED" in stream_states:
        phases["P3"]["lifecycle"] = "PAUSED"
    elif "FAILED" in stream_states:
        phases["P3"]["lifecycle"] = "FAILED"
    return {"schema_version": "campaign-canonical-projection@1", "campaign": definition["campaign"], "as_of": as_of, "bootstrapped": bootstrapped, "runtime_mode": "DEMONSTRATION" if demonstration else "CAMPAIGN", "completion": {"earned_campaign_points": round(earned, 4), "planned_campaign_points": round(total, 4), "completion_pct": round(100 * earned / total, 2) if total else 0, "readiness": "GATES_ONLY"}, "phases": list(phases.values()), "streams": list(streams.values()), "work_items": list(items.values()), "findings": list(findings.values()), "root_cause_groups": sorted({f["root_cause_group"] for f in findings.values() if f["root_cause_group"]}), "remediations": list(remediations.values()), "verifications": list(verifications.values()), "gates": list(gates.values()), "dependencies": list(dependencies.values()), "decisions": decisions, "execution_sessions": list(sessions.values()), "agent_roles": sorted(ROLES), "scope_changes": scope_changes}


def presence_overlay(canonical_projection: dict[str, Any], presences: list[dict[str, Any]], as_of: str, integrity_ok: bool) -> dict[str, Any]:
    now = parse_time(as_of) or time.time(); by_session = {p["session_id"]: p for p in presences}; cells = []
    stale_streams: set[str] = set()
    for session in canonical_projection["execution_sessions"]:
        presence = by_session.get(session["id"]); age = None if not presence else max(0, now - (parse_time(presence["observed_at"]) or 0))
        lifecycle = session["lifecycle"]
        if not integrity_ok: health = "INTEGRITY_DEGRADED"
        elif lifecycle in {"RUNNING", "IN_VERIFICATION"}: health = "STALE" if age is None or age > 300 else "HEALTHY"
        elif lifecycle in {"PAUSED", "BLOCKED", "FAILED"}: health = "ATTENTION_REQUIRED"
        else: health = "UNKNOWN"
        if health == "STALE" and session.get("stream_id"): stale_streams.add(session["stream_id"])
        started = parse_time(session.get("started_at"))
        elapsed = max(0, now - started) if started is not None else None
        ceiling = session.get("ceiling")
        remaining = max(0, ceiling - elapsed) if isinstance(ceiling, (int, float)) and not isinstance(ceiling, bool) and elapsed is not None else None
        stream = next((item for item in canonical_projection["streams"] if item["id"] == session.get("stream_id")), None)
        cells.append({"session_id": session["id"], "conversation_id": session.get("conversation_id"), "conversation_uri": session.get("conversation_uri"), "stream_id": session.get("stream_id"), "actor_id": session["owner"], "verifier": session.get("verifier"), "participants": session.get("participants", []), "model": session.get("model"), "reasoning_config": session.get("reasoning_config"), "work_item": stream.get("lifecycle_stage", {}).get("id") if stream else session.get("lifecycle_stage"), "state": presence["state"] if presence else "MISSING", "last_presence_at": presence["observed_at"] if presence else None, "presence_age_seconds": round(age, 1) if age is not None else None, "health": health, "last_meaningful_action": session.get("last_meaningful_action"), "next_autonomous_action": session.get("assignment"), "branch": session.get("branch"), "current_sha": session.get("current_sha"), "pr": session.get("pr"), "ci": session.get("ci"), "deployed_revision": session.get("deployed_revision"), "elapsed_seconds": round(elapsed, 1) if elapsed is not None else None, "cost": session.get("cost"), "ceiling": ceiling, "remaining_ceiling_seconds": round(remaining, 1) if remaining is not None else None})
    stream_health = {}
    for stream in canonical_projection["streams"]:
        sid, lifecycle = stream["id"], stream["lifecycle"]
        related = [c for c in cells if c["stream_id"] == sid]
        if not integrity_ok: stream_health[sid] = "INTEGRITY_DEGRADED"
        elif lifecycle in {"RUNNING", "IN_VERIFICATION"}: stream_health[sid] = "HEALTHY" if related and all(c["health"] == "HEALTHY" for c in related) else "STALE"
        elif lifecycle in {"PAUSED", "BLOCKED", "FAILED"}: stream_health[sid] = "ATTENTION_REQUIRED"
        else: stream_health[sid] = "UNKNOWN"
    phase_health = {p["id"]: ("INTEGRITY_DEGRADED" if not integrity_ok else "UNKNOWN") for p in canonical_projection["phases"]}
    if integrity_ok:
        p3 = [stream_health[sid] for sid, _ in STREAMS]
        phase_health["P3"] = "STALE" if "STALE" in p3 else ("ATTENTION_REQUIRED" if "ATTENTION_REQUIRED" in p3 else ("HEALTHY" if "HEALTHY" in p3 else "UNKNOWN"))
        for phase in canonical_projection["phases"]:
            phase_id = phase["id"]
            if phase_id == "P3":
                continue
            related = [cell["health"] for cell in cells if cell["stream_id"] == phase_id]
            if related:
                phase_health[phase_id] = "STALE" if "STALE" in related else ("ATTENTION_REQUIRED" if "ATTENTION_REQUIRED" in related else ("HEALTHY" if all(health == "HEALTHY" for health in related) else "UNKNOWN"))
    owners_by_stream: dict[str, set[str]] = {}
    for cell in cells:
        if cell.get("stream_id"): owners_by_stream.setdefault(cell["stream_id"], set()).add(cell["actor_id"])
    ownership_conflicts = sorted(stream_id for stream_id, owners in owners_by_stream.items() if len(owners) > 1)
    phase_lifecycles = {phase["id"]: phase["lifecycle"] for phase in canonical_projection["phases"]}
    dependency_warnings = [dependency for dependency in canonical_projection["dependencies"] if dependency["status"] != "RESOLVED" and phase_lifecycles.get(dependency["to"]) in {"RUNNING", "IN_VERIFICATION", "BLOCKED", "PAUSED", "FAILED"}]
    for dependency in dependency_warnings:
        phase_health[dependency["to"]] = "ATTENTION_REQUIRED"
    has_attention = "ATTENTION_REQUIRED" in stream_health.values() or any(cell["health"] == "ATTENTION_REQUIRED" for cell in cells) or bool(dependency_warnings)
    all_unknown = not cells and all(health == "UNKNOWN" for health in stream_health.values()) and all(health == "UNKNOWN" for health in phase_health.values())
    campaign = {"active_cells": len(cells), "healthy_cells": sum(cell["health"] == "HEALTHY" for cell in cells), "stale_cells": sum(cell["health"] == "STALE" for cell in cells), "verifier_backlog": sum(remediation["status"] == "AWAITING_VERIFICATION" for remediation in canonical_projection["remediations"]), "surrogate_decision_backlog": sum(finding["status"] == "OPEN" for finding in canonical_projection["findings"]), "a3_decisions": sum(decision.get("requires_a3", False) for decision in canonical_projection["decisions"]), "ownership_conflicts": ownership_conflicts, "ceiling_risks": sum(cell["remaining_ceiling_seconds"] == 0 for cell in cells if cell["remaining_ceiling_seconds"] is not None), "dependency_warnings": len(dependency_warnings)}
    warning = "INTEGRITY DEGRADED — do not treat any state as green" if not integrity_ok else ("STALE RUNNING PRESENCE — do not treat stream as healthy" if stale_streams else ("UNRESOLVED ACTIVE DEPENDENCY — do not treat campaign state as green" if dependency_warnings else None))
    return {"as_of": as_of, "presence_is_ephemeral": True, "cells": cells, "campaign": campaign, "dependency_warnings": dependency_warnings, "stale_stream_ids": sorted(stale_streams), "stream_health": stream_health, "phase_health": phase_health, "warning": warning, "overall_health": "INTEGRITY_DEGRADED" if not integrity_ok else ("STALE" if stale_streams else ("ATTENTION_REQUIRED" if has_attention else ("UNKNOWN" if all_unknown else "HEALTHY")))}
