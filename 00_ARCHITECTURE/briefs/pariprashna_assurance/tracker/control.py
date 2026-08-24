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


def parse_time(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def programme_definition() -> dict[str, Any]:
    phases = [{"id": pid, "name": name, "campaign_weight": weight, "entry_gate": f"CG-{index - 1}" if index else None, "exit_gate": f"CG-{index}"} for index, (pid, name, weight) in enumerate(PHASES)]
    work_items: list[dict[str, Any]] = []
    for phase in phases:
        if phase["id"] == "P3":
            for sid, title in STREAMS:
                for stage_id, stage_name, weight in STAGES:
                    work_items.append({"id": f"{sid}:{stage_id}", "phase_id": "P3", "stream_id": sid, "title": stage_name, "campaign_points": 7.5 * weight / 100, "kind": "stream_lifecycle"})
        else:
            work_items.append({"id": f"{phase['id']}:completion", "phase_id": phase["id"], "stream_id": None, "title": f"{phase['name']} completion evidence", "campaign_points": float(phase["campaign_weight"]), "kind": "phase_completion"})
    return {"schema_version": "campaign-definition@1", "campaign": {"id": "pariprashna-experience-assurance-v3", "name": "Paripraśna Experience Assurance Programme v3.0"}, "phases": phases, "streams": [{"id": sid, "name": name, "phase_id": "P3", "campaign_weight": 7.5} for sid, name in STREAMS], "gates": [{"id": gid, "name": name} for gid, name in GATES], "dependencies": [{"from": "P0", "to": "P1"}, {"from": "P1", "to": "P2"}, {"from": "P2", "to": "P3"}, {"from": "P3", "to": "P4"}, {"from": "P4", "to": "P5"}, {"from": "P5", "to": "P6"}, {"from": "P6", "to": "P7"}], "work_items": work_items}


def contains_progress(value: Any) -> bool:
    if isinstance(value, dict):
        return any(k.lower() in {"progress", "percentage", "percent", "completion_pct"} or contains_progress(v) for k, v in value.items())
    if isinstance(value, list):
        return any(contains_progress(v) for v in value)
    return False


class EventStore:
    def __init__(self, runtime_dir: str | Path):
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.runtime_dir / "control-plane.sqlite3"
        self._lock = threading.RLock()
        self.init()

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

    def init(self) -> None:
        with self.connection() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                  ledger_seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
                  schema_version TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE,
                  stream_id TEXT, stream_seq INTEGER, actor_id TEXT NOT NULL, actor_role TEXT NOT NULL,
                  event_type TEXT NOT NULL, payload_json TEXT NOT NULL, evidence_json TEXT NOT NULL,
                  occurred_at TEXT NOT NULL, prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL UNIQUE
                );
                CREATE UNIQUE INDEX IF NOT EXISTS events_stream_seq ON events(stream_id, stream_seq) WHERE stream_id IS NOT NULL;
                CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
                CREATE TABLE IF NOT EXISTS stream_sequences (stream_id TEXT PRIMARY KEY, current_seq INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS ledger_meta (id INTEGER PRIMARY KEY CHECK (id=1), last_hash TEXT NOT NULL, definition_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS rejected_events (id INTEGER PRIMARY KEY AUTOINCREMENT, received_at TEXT NOT NULL, actor_id TEXT, idempotency_key TEXT, code TEXT NOT NULL, message TEXT NOT NULL, request_json TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS rejected_no_update BEFORE UPDATE ON rejected_events BEGIN SELECT RAISE(ABORT, 'rejections are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS rejected_no_delete BEFORE DELETE ON rejected_events BEGIN SELECT RAISE(ABORT, 'rejections are append-only'); END;
                CREATE TABLE IF NOT EXISTS actors (actor_id TEXT PRIMARY KEY, role TEXT NOT NULL, streams_json TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE);
                CREATE TABLE IF NOT EXISTS presences (session_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, stream_id TEXT, state TEXT NOT NULL, observed_at TEXT NOT NULL, detail TEXT);
                CREATE TABLE IF NOT EXISTS projection_state (id INTEGER PRIMARY KEY CHECK (id=1), canonical_json TEXT NOT NULL, projection_hash TEXT NOT NULL, as_of TEXT NOT NULL, event_count INTEGER NOT NULL, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS projector_health (id INTEGER PRIMARY KEY CHECK (id=1), status TEXT NOT NULL, last_error TEXT, last_success_at TEXT, lag_events INTEGER NOT NULL DEFAULT 0);
            """)
            if not con.execute("SELECT 1 FROM ledger_meta WHERE id=1").fetchone():
                con.execute("INSERT INTO ledger_meta(id,last_hash,definition_json) VALUES(1,?,?)", ("0" * 64, canonical(programme_definition())))
            if not con.execute("SELECT 1 FROM projector_health WHERE id=1").fetchone():
                con.execute("INSERT INTO projector_health(id,status,lag_events) VALUES(1,'UNKNOWN',0)")
            self._seed_actors(con)

    def _seed_actors(self, con: sqlite3.Connection) -> None:
        all_streams = [sid for sid, _ in STREAMS] + ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
        rows = [("lead-p0", "STREAM_LEAD", ["P0"]), *[(f"lead-{sid.lower()}", "STREAM_LEAD", [sid]) for sid, _ in STREAMS], ("surrogate", "NATIVE_SURROGATE", all_streams), ("verifier", "INDEPENDENT_VERIFIER", all_streams), ("integrator", "PROGRAMME_INTEGRATOR", all_streams), ("native", "NATIVE", all_streams)]
        for actor_id, role, streams in rows:
            con.execute("INSERT OR IGNORE INTO actors(actor_id,role,streams_json,token_hash) VALUES(?,?,?,?)", (actor_id, role, canonical(streams), secrets.token_hex(32)))

    def provision_local_credentials(self) -> dict[str, Any]:
        """Create once-per-runtime credentials for local CG-0 proof; never commit them."""
        target = self.runtime_dir / "local-credentials.json"
        if target.exists():
            raise RejectedEvent("CREDENTIALS_EXIST", f"credentials already exist at {target}; do not overwrite them")
        credentials: dict[str, str] = {}
        with self._lock, self.connection() as con:
            con.execute("BEGIN IMMEDIATE")
            for row in con.execute("SELECT actor_id FROM actors ORDER BY actor_id"):
                token = secrets.token_urlsafe(32)
                credentials[row["actor_id"]] = token
                con.execute("UPDATE actors SET token_hash=? WHERE actor_id=?", (hashlib.sha256(token.encode()).hexdigest(), row["actor_id"]))
            con.execute("COMMIT")
        tmp = target.with_suffix(".tmp")
        tmp.write_text(canonical({"schema_version": "local-credentials@1", "created_at": now_iso(), "tokens": credentials}) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, target)
        return {"path": str(target), "actors": sorted(credentials)}

    def definition(self) -> dict[str, Any]:
        with self.connection() as con:
            return json.loads(con.execute("SELECT definition_json FROM ledger_meta WHERE id=1").fetchone()[0])

    def authenticate(self, token: str) -> str | None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self.connection() as con:
            row = con.execute("SELECT actor_id FROM actors WHERE token_hash=?", (token_hash,)).fetchone()
        return row[0] if row else None

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
        if request["event_type"] in COMPLETION_EVENTS and not evidence:
            raise RejectedEvent("EVIDENCE_REQUIRED", f"{request['event_type']} requires primary evidence")
        if any(not isinstance(e, dict) or not e.get("uri") or not e.get("kind") for e in evidence):
            raise RejectedEvent("EVIDENCE_SCHEMA", "each evidence item requires kind and uri")
        with self._lock, self.connection() as con:
            con.execute("BEGIN IMMEDIATE")
            existing = con.execute("SELECT * FROM events WHERE idempotency_key=?", (request["idempotency_key"],)).fetchone()
            if existing:
                con.execute("COMMIT")
                return {"accepted": True, "idempotent": True, "event": self._row_event(existing)}
            actor = con.execute("SELECT * FROM actors WHERE actor_id=?", (request["actor_id"],)).fetchone()
            if not actor:
                con.execute("ROLLBACK")
                raise RejectedEvent("UNAUTHENTICATED", "unknown actor")
            role = actor["role"]
            event_type = request["event_type"]
            if event_type not in ROLE_EVENTS.get(role, set()):
                con.execute("ROLLBACK")
                raise RejectedEvent("ROLE_FORBIDDEN", f"{role} cannot emit {event_type}")
            streams = json.loads(actor["streams_json"])
            if stream_id and stream_id not in streams:
                con.execute("ROLLBACK")
                raise RejectedEvent("STREAM_FORBIDDEN", f"{request['actor_id']} does not own {stream_id}")
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
            occurred_at = request.get("occurred_at") or now_iso()
            body = {"schema_version": EVENT_SCHEMA, "event_id": str(uuid.uuid4()), "idempotency_key": request["idempotency_key"], "stream_id": stream_id, "stream_seq": stream_seq, "actor_id": request["actor_id"], "actor_role": role, "event_type": event_type, "payload": request["payload"], "evidence": evidence, "occurred_at": occurred_at, "prev_hash": previous}
            event_hash = digest(body)
            con.execute("INSERT INTO events(event_id,schema_version,idempotency_key,stream_id,stream_seq,actor_id,actor_role,event_type,payload_json,evidence_json,occurred_at,prev_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (body["event_id"], EVENT_SCHEMA, body["idempotency_key"], stream_id, stream_seq, body["actor_id"], role, event_type, canonical(request["payload"]), canonical(evidence), occurred_at, previous, event_hash))
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
        if typ == "work_item_accepted":
            item = payload.get("work_item_id")
            known_items = {w["id"] for w in self.definition()["work_items"]}
            for row in con.execute("SELECT payload_json FROM events WHERE event_type='scope_change_approved' ORDER BY ledger_seq"):
                known_items.update(x["id"] for x in json.loads(row["payload_json"])["added_work_items"])
            if item not in known_items:
                raise RejectedEvent("UNKNOWN_WORK_ITEM", "work item is not in the accepted denominator")
            verification_id = payload.get("verification_event_id")
            verification = con.execute("SELECT event_type,actor_role,payload_json FROM events WHERE event_id=?", (verification_id,)).fetchone()
            verification_payload = json.loads(verification["payload_json"]) if verification else {}
            if not verification or verification["event_type"] not in {"verification_accepted", "regression_accepted"} or verification["actor_role"] != "INDEPENDENT_VERIFIER" or verification_payload.get("work_item_id") != item or not verification_payload.get("finder_actor_id") or not verification_payload.get("fixer_actor_id"):
                raise RejectedEvent("VERIFICATION_REQUIRED", "work item acceptance needs its linked independent verification event")
            scoped_items = {w["id"]: w for w in self.definition()["work_items"]}
            for row in con.execute("SELECT payload_json FROM events WHERE event_type='scope_change_approved'"):
                scoped_items.update({x["id"]: x for x in json.loads(row["payload_json"])["added_work_items"]})
            item_stream = scoped_items[item].get("stream_id")
            if item_stream:
                current = fold(self.definition(), [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")], now_iso())
                stream = next(s for s in current["streams"] if s["id"] == item_stream)
                if stream["lifecycle"] == "FAILED":
                    raise RejectedEvent("INVALID_TRANSITION", "failed stream cannot receive completion credit")
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
            verification = con.execute("SELECT event_type,actor_role,payload_json FROM events WHERE event_id=?", (payload.get("verification_event_id"),)).fetchone()
            verification_payload = json.loads(verification["payload_json"]) if verification else {}
            if not verification or verification["event_type"] not in {"verification_accepted", "regression_accepted"} or verification["actor_role"] != "INDEPENDENT_VERIFIER" or verification_payload.get("gate_id") != gate or not verification_payload.get("finder_actor_id") or not verification_payload.get("fixer_actor_id"):
                raise RejectedEvent("VERIFICATION_REQUIRED", "gate closure needs its linked independent gate verification")
            required_phase = f"P{gate[-1]}"
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
            current = fold(self.definition(), [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")], now_iso())
            stream = next(s for s in current["streams"] if s["id"] == packet_stream)
            if stream["completion_pct"] != 100:
                raise RejectedEvent("RESULT_PACKET_PREREQUISITE", "result packet requires all stream work items accepted")
            closure = con.execute("SELECT 1 FROM events WHERE stream_id=? AND event_type='stream_closure_recommended' AND actor_role='INDEPENDENT_VERIFIER'", (packet_stream,)).fetchone()
            if not closure:
                raise RejectedEvent("RESULT_PACKET_PREREQUISITE", "result packet requires an independent stream closure recommendation")
        if typ == "native_acceptance":
            current = fold(self.definition(), [self._row_event(row) for row in con.execute("SELECT * FROM events ORDER BY ledger_seq")], now_iso())
            p6 = next(p for p in current["phases"] if p["id"] == "P6")
            cg5 = next(g for g in current["gates"] if g["id"] == "CG-5")
            if p6["completion_pct"] != 100 or cg5["status"] != "CLOSED":
                raise RejectedEvent("GATE_PREREQUISITE", "native acceptance requires complete P6 evidence and closed CG-5")
        if typ == "scope_change_approved":
            additions = payload.get("added_work_items")
            if not isinstance(additions, list) or not additions or not payload.get("reason"):
                raise RejectedEvent("SCOPE_CHANGE_SCHEMA", "approved scope change needs reason and added_work_items")
            known_ids = {w["id"] for w in self.definition()["work_items"]}
            for row in con.execute("SELECT payload_json FROM events WHERE event_type='scope_change_approved'"):
                known_ids.update(x["id"] for x in json.loads(row["payload_json"])["added_work_items"])
            for item in additions:
                if not all(k in item for k in ("id", "phase_id", "title", "campaign_points")):
                    raise RejectedEvent("SCOPE_CHANGE_SCHEMA", "each added work item needs id, phase_id, title, campaign_points")
                if item["id"] in known_ids or item["id"] in {x["id"] for x in additions if x is not item} or item["phase_id"] not in {p[0] for p in PHASES} or not isinstance(item["campaign_points"], (int, float)) or isinstance(item["campaign_points"], bool) or not 0 < item["campaign_points"] <= 100:
                    raise RejectedEvent("SCOPE_CHANGE_SCHEMA", "scope changes may only add new positive work items in known phases")

    @staticmethod
    def _row_event(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        result["evidence"] = json.loads(result.pop("evidence_json"))
        return result

    def record_presence(self, actor_id: str, session_id: str, stream_id: str | None, state: str, detail: str = "", observed_at: str | None = None) -> None:
        if state not in {"ACTIVE", "WAITING", "PAUSED", "COMPLETED"}:
            raise RejectedEvent("PRESENCE_SCHEMA", "invalid presence state")
        with self.connection() as con:
            actor = con.execute("SELECT streams_json FROM actors WHERE actor_id=?", (actor_id,)).fetchone()
            if not actor or (stream_id and stream_id not in json.loads(actor[0])):
                raise RejectedEvent("STREAM_FORBIDDEN", "presence actor does not own stream")
            con.execute("INSERT INTO presences(session_id,actor_id,stream_id,state,observed_at,detail) VALUES(?,?,?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET actor_id=excluded.actor_id,stream_id=excluded.stream_id,state=excluded.state,observed_at=excluded.observed_at,detail=excluded.detail", (session_id, actor_id, stream_id, state, observed_at or now_iso(), detail))

    def rebuild(self, as_of: str | None = None) -> dict[str, Any]:
        as_of = as_of or now_iso()
        with self._lock, self.connection() as con:
            con.execute("BEGIN IMMEDIATE")
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
        if not state:
            return {"ok": False, "reason": "no projection"}
        replay = fold(self.definition(), self.events(), state["as_of"])
        actual = digest(replay)
        try:
            materialized_hash = digest(json.loads(state["canonical_json"]))
        except json.JSONDecodeError:
            materialized_hash = "invalid-json"
        ok = actual == state["projection_hash"] and materialized_hash == state["projection_hash"]
        with self.connection() as con:
            con.execute("UPDATE projector_health SET status=?,last_error=?,lag_events=? WHERE id=1", ("HEALTHY" if ok else "INTEGRITY_DEGRADED", None if ok else "full replay hash mismatch", 0 if ok else 1))
        return {"ok": ok, "expected_hash": state["projection_hash"], "actual_hash": actual, "materialized_hash": materialized_hash, "as_of": state["as_of"]}

    def projection(self, as_of: str | None = None) -> dict[str, Any]:
        with self.connection() as con:
            state = con.execute("SELECT * FROM projection_state WHERE id=1").fetchone()
            health = dict(con.execute("SELECT * FROM projector_health WHERE id=1").fetchone())
            rows = con.execute("SELECT * FROM presences").fetchall()
        if not state:
            self.rebuild(as_of)
            return self.projection(as_of)
        canonical_projection = json.loads(state["canonical_json"])
        integrity = self.verify_replay()
        overlay = presence_overlay(canonical_projection, [dict(r) for r in rows], as_of or now_iso(), integrity["ok"])
        display = copy.deepcopy(canonical_projection)
        for stream in display["streams"]: stream["health"] = overlay["stream_health"].get(stream["id"], "UNKNOWN")
        for phase in display["phases"]: phase["health"] = overlay["phase_health"].get(phase["id"], "UNKNOWN")
        return {"schema_version": "campaign-projection@1", "canonical": canonical_projection, "display": display, "canonical_hash": state["projection_hash"], "projection_as_of": state["as_of"], "integrity": integrity, "projector_health": health, "liveness": overlay, "rejected_events": self.rejected()}

    def export_snapshot(self, path: str | Path) -> dict[str, Any]:
        result = self.verify_replay()
        if not result["ok"]:
            raise RejectedEvent("INTEGRITY_DEGRADED", "cannot export a snapshot with failed replay")
        snapshot = {"schema_version": "immutable-snapshot@1", "exported_at": now_iso(), "projection": self.projection(), "events": self.events(), "event_log_hash": digest(self.events())}
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(canonical(snapshot) + "\n", encoding="utf-8")
        os.replace(tmp, target)
        os.chmod(target, 0o444)
        return {"path": str(target), "snapshot_hash": digest(snapshot), "event_log_hash": snapshot["event_log_hash"]}


def fold(definition: dict[str, Any], events: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
    """Pure durable state projection. Presence is intentionally not an input."""
    items = {item["id"]: {**copy.deepcopy(item), "accepted": False, "evidence": [], "accepted_by": None} for item in definition["work_items"]}
    phases = {p["id"]: {**copy.deepcopy(p), "lifecycle": "NOT_STARTED", "health": "UNKNOWN", "last_evidence_at": None, "responsible_session": None} for p in definition["phases"]}
    streams = {s["id"]: {**copy.deepcopy(s), "lifecycle": "NOT_STARTED", "health": "UNKNOWN", "last_evidence_at": None, "next_checkpoint": None} for s in definition["streams"]}
    gates = {g["id"]: {**copy.deepcopy(g), "status": "OPEN", "evidence": [], "closed_by": None} for g in definition["gates"]}
    findings: dict[str, Any] = {}; remediations: dict[str, Any] = {}; verifications: dict[str, Any] = {}; decisions: list[dict[str, Any]] = []; sessions: dict[str, Any] = {}; scope_changes: list[dict[str, Any]] = []
    bootstrapped = False
    for event in events:
        typ, payload, evidence = event["event_type"], event["payload"], event["evidence"]
        phase_id = payload.get("phase_id") or ("P3" if event.get("stream_id") in streams else event.get("stream_id"))
        if typ == "campaign_bootstrapped":
            bootstrapped = True; phases["P0"]["lifecycle"] = "RUNNING"
        elif typ == "work_started":
            sid = payload.get("session_id")
            if sid:
                sessions[sid] = {"id": sid, "stream_id": event.get("stream_id"), "owner": event["actor_id"], "verifier": payload.get("verifier"), "branch": payload.get("branch"), "worktree": payload.get("worktree"), "baseline_sha": payload.get("baseline_sha"), "current_sha": payload.get("current_sha"), "pr": payload.get("pr"), "ci": payload.get("ci"), "deployed_revision": payload.get("deployed_revision"), "lifecycle": "RUNNING", "last_evidence": evidence, "last_evidence_at": event["occurred_at"], "assignment": payload.get("assignment"), "ceiling": payload.get("ceiling")}
            if event.get("stream_id") in streams: streams[event["stream_id"]]["lifecycle"] = "RUNNING"
            elif phase_id in phases: phases[phase_id]["lifecycle"] = "RUNNING"
        elif typ in {"paused", "blocked", "resumed", "verification_started", "failed"}:
            target = streams.get(event.get("stream_id")) or phases.get(phase_id)
            states = {"paused": "PAUSED", "blocked": "BLOCKED", "resumed": "RUNNING", "verification_started": "IN_VERIFICATION", "failed": "FAILED"}
            if target: target["lifecycle"] = states[typ]; target["last_evidence_at"] = event["occurred_at"]
            for session in sessions.values():
                if session.get("stream_id") == event.get("stream_id"):
                    session["lifecycle"] = states[typ]
        elif typ == "finding_discovered":
            fid = payload.get("finding_id");
            if fid: findings[fid] = {"id": fid, "stream_id": event.get("stream_id"), "severity": payload.get("severity", "UNTRIAGED"), "status": "OPEN", "root_cause_group": payload.get("root_cause_group"), "evidence": evidence, "finder": event["actor_id"]}
        elif typ == "finding_triaged":
            fid = payload.get("finding_id");
            if fid in findings: findings[fid].update({"status": "TRIAGED", "severity": payload.get("severity", findings[fid]["severity"]), "surrogate_decision": True})
        elif typ == "remediation_implemented":
            rid = payload.get("remediation_id")
            if rid: remediations[rid] = {"id": rid, "finding_id": payload.get("finding_id"), "stream_id": event.get("stream_id"), "status": "AWAITING_VERIFICATION", "fixer": event["actor_id"], "evidence": evidence}
        elif typ in {"verification_accepted", "verification_rejected"}:
            vid = payload.get("verification_id", event["event_id"]); verifications[vid] = {"id": vid, "status": "ACCEPTED" if typ == "verification_accepted" else "REJECTED", "verifier": event["actor_id"], "finding_id": payload.get("finding_id"), "remediation_id": payload.get("remediation_id"), "evidence": evidence}
            rid = payload.get("remediation_id")
            if rid in remediations: remediations[rid]["status"] = "VERIFIED" if typ == "verification_accepted" else "REWORK_REQUIRED"
        elif typ == "work_item_accepted":
            wid = payload["work_item_id"]
            if wid in items: items[wid].update({"accepted": True, "evidence": evidence, "accepted_by": event["actor_id"], "accepted_at": event["occurred_at"]})
        elif typ == "scope_change_approved":
            additions = payload["added_work_items"]
            for item in additions:
                if item["id"] not in items: items[item["id"]] = {**item, "accepted": False, "evidence": [], "accepted_by": None, "kind": item.get("kind", "scope_change")}
            scope_changes.append({"event_id": event["event_id"], "reason": payload["reason"], "added_work_items": [x["id"] for x in additions], "evidence": evidence, "at": event["occurred_at"]})
        elif typ == "decision_recorded":
            decisions.append({"event_id": event["event_id"], "label": "SURROGATE DECISION — not native acceptance", "decision": payload.get("decision"), "evidence": evidence})
        elif typ == "gate_closed":
            gate = payload["gate_id"]; gates[gate].update({"status": "CLOSED", "evidence": evidence, "closed_by": event["actor_id"]})
        elif typ == "native_acceptance":
            gates["CG-6"].update({"status": "CLOSED", "evidence": evidence, "closed_by": event["actor_id"]})
        if phase_id in phases and evidence:
            phases[phase_id]["last_evidence_at"] = event["occurred_at"]
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
        if stream_items and all(i["accepted"] for i in stream_items): stream["lifecycle"] = "COMPLETE"
        stream["scenarios"] = {"planned": len(stream_items), "executed": sum(i["accepted"] for i in stream_items)}
        stream["findings"] = [f for f in findings.values() if f["stream_id"] == sid]
        stream["fixed_awaiting_verification"] = sum(r["stream_id"] == sid and r["status"] == "AWAITING_VERIFICATION" for r in remediations.values())
        stream["independently_closed"] = sum(r["stream_id"] == sid and r["status"] == "VERIFIED" for r in remediations.values())
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
    return {"schema_version": "campaign-canonical-projection@1", "campaign": definition["campaign"], "as_of": as_of, "bootstrapped": bootstrapped, "completion": {"earned_campaign_points": round(earned, 4), "planned_campaign_points": round(total, 4), "completion_pct": round(100 * earned / total, 2) if total else 0, "readiness": "GATES_ONLY"}, "phases": list(phases.values()), "streams": list(streams.values()), "work_items": list(items.values()), "findings": list(findings.values()), "root_cause_groups": sorted({f["root_cause_group"] for f in findings.values() if f["root_cause_group"]}), "remediations": list(remediations.values()), "verifications": list(verifications.values()), "gates": list(gates.values()), "dependencies": definition["dependencies"], "decisions": decisions, "execution_sessions": list(sessions.values()), "agent_roles": sorted(ROLES), "scope_changes": scope_changes}


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
        cells.append({"session_id": session["id"], "stream_id": session.get("stream_id"), "actor_id": session["owner"], "state": presence["state"] if presence else "MISSING", "presence_age_seconds": round(age, 1) if age is not None else None, "health": health, "last_meaningful_action": session.get("assignment"), "next_autonomous_action": session.get("assignment"), "branch": session.get("branch"), "pr": session.get("pr"), "ci": session.get("ci"), "ceiling": session.get("ceiling")})
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
    has_attention = "ATTENTION_REQUIRED" in stream_health.values()
    warning = None if integrity_ok and not stale_streams else ("INTEGRITY DEGRADED — do not treat any state as green" if not integrity_ok else "STALE RUNNING PRESENCE — do not treat stream as healthy")
    return {"as_of": as_of, "presence_is_ephemeral": True, "cells": cells, "stale_stream_ids": sorted(stale_streams), "stream_health": stream_health, "phase_health": phase_health, "warning": warning, "overall_health": "INTEGRITY_DEGRADED" if not integrity_ok else ("STALE" if stale_streams else ("ATTENTION_REQUIRED" if has_attention else "HEALTHY"))}
