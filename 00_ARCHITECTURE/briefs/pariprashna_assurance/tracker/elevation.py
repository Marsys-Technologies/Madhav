#!/usr/bin/env python3
"""Shadow-only governed elevation ledger for the Paripraśna assurance tracker.

This module deliberately has no write path to the accepted control-plane runtime.
It records source observations separately from independently accepted evidence and
never derives a gate, progress percentage, or cutover decision from either alone.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


class InvariantViolation(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class ElevationStore:
    """SQLite-backed, append-only shadow ledger with explicit authority boundaries."""

    def __init__(self, database: str | Path):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _init(self) -> None:
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS plan_revisions (
                    revision INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_hash TEXT NOT NULL UNIQUE,
                    plan_json TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    registered_by TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 0 CHECK(active IN (0,1))
                );
                CREATE UNIQUE INDEX IF NOT EXISTS only_one_active_plan ON plan_revisions(active) WHERE active=1;
                CREATE TRIGGER IF NOT EXISTS plans_no_update BEFORE UPDATE ON plan_revisions
                  WHEN OLD.plan_hash != NEW.plan_hash OR OLD.plan_json != NEW.plan_json
                  BEGIN SELECT RAISE(ABORT, 'plan revisions are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS plans_no_delete BEFORE DELETE ON plan_revisions
                  BEGIN SELECT RAISE(ABORT, 'plan revisions are append-only'); END;

                CREATE TABLE IF NOT EXISTS source_cursors (
                    source_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    cursor TEXT,
                    fresh_after_seconds INTEGER NOT NULL,
                    observed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    cursor TEXT,
                    idempotency_key TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    authors_json TEXT NOT NULL DEFAULT '[]',
                    observed_at TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('OBSERVED','QUARANTINED')),
                    UNIQUE(source_id, idempotency_key)
                );
                CREATE TRIGGER IF NOT EXISTS observations_no_update BEFORE UPDATE ON observations
                  BEGIN SELECT RAISE(ABORT, 'observations are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS observations_no_delete BEFORE DELETE ON observations
                  BEGIN SELECT RAISE(ABORT, 'observations are append-only'); END;
                CREATE TABLE IF NOT EXISTS observation_failures (
                    source_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    last_error TEXT NOT NULL,
                    quarantined INTEGER NOT NULL DEFAULT 0 CHECK(quarantined IN (0,1)),
                    PRIMARY KEY(source_id, idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS accepted_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    observation_id INTEGER NOT NULL REFERENCES observations(observation_id),
                    accepted_by TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    supports_json TEXT NOT NULL,
                    accepted_at TEXT NOT NULL,
                    CHECK(classification IN ('VERIFIED','REJECTED','INCONCLUSIVE'))
                );
                CREATE TRIGGER IF NOT EXISTS evidence_no_update BEFORE UPDATE ON accepted_evidence
                  BEGIN SELECT RAISE(ABORT, 'accepted evidence is append-only'); END;
                CREATE TRIGGER IF NOT EXISTS evidence_no_delete BEFORE DELETE ON accepted_evidence
                  BEGIN SELECT RAISE(ABORT, 'accepted evidence is append-only'); END;
                CREATE TABLE IF NOT EXISTS independent_verifiers (
                    actor_id TEXT PRIMARY KEY,
                    enrolled_by TEXT NOT NULL,
                    approval_evidence_json TEXT NOT NULL,
                    enrolled_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS impact_dispositions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_hash TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    action TEXT NOT NULL CHECK(action IN ('CARRY_FORWARD','INVALIDATE')),
                    reason TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    recorded_by TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    UNIQUE(candidate_hash, scope)
                );
                CREATE TABLE IF NOT EXISTS contradictions (
                    id TEXT PRIMARY KEY,
                    sources_json TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN','RESOLVED','DO_NOT_RELY'))
                );
                CREATE TRIGGER IF NOT EXISTS contradictions_no_delete BEFORE DELETE ON contradictions
                  BEGIN SELECT RAISE(ABORT, 'contradictions are append-only'); END;
            """)
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(observations)")}
            if "authors_json" not in columns:
                connection.execute("ALTER TABLE observations ADD COLUMN authors_json TEXT NOT NULL DEFAULT '[]'")

    @staticmethod
    def _validate_plan(plan: dict[str, Any]) -> None:
        required = {"campaign_id", "spine", "streams", "catalogue"}
        if not isinstance(plan, dict) or set(plan) != required:
            raise InvariantViolation("PLAN_SCHEMA", "plan must contain exactly campaign_id, spine, streams, catalogue")
        if plan["spine"] != [f"P{i}" for i in range(8)] or plan["streams"] != [f"S{i}" for i in range(1, 7)]:
            raise InvariantViolation("PLAN_SPINE", "plan must retain the P0-P7 spine and S1-S6 streams")
        allowed_catalogue = {"P-PIPE", "P-PORTAL", "P-GUIDED", "PPR", "EDIR"}
        if not plan["catalogue"] or not set(plan["catalogue"]).issubset(allowed_catalogue):
            raise InvariantViolation("CATALOGUE_SCOPE", "catalogue may contain only mapped P-PIPE, P-PORTAL, P-GUIDED, PPR and EDIR scopes")

    def register_plan(self, plan: dict[str, Any], *, actor: str) -> dict[str, Any]:
        self._validate_plan(plan)
        plan_hash = digest(plan)
        with self._connect() as connection:
            if connection.execute("SELECT COUNT(*) FROM plan_revisions").fetchone()[0] == 0 and plan["catalogue"] != BASELINE_CATALOGUE:
                raise InvariantViolation("CATALOGUE_BASELINE", "the first revision must preserve the complete v2 P-PIPE/P-PORTAL/P-GUIDED/PPR/EDIR mapping")
            existing = connection.execute("SELECT revision,plan_hash FROM plan_revisions WHERE plan_hash=?", (plan_hash,)).fetchone()
            if existing:
                return dict(existing)
            connection.execute("INSERT INTO plan_revisions(plan_hash,plan_json,registered_at,registered_by) VALUES(?,?,?,?)", (plan_hash, canonical(plan), utc_now(), actor))
            row = connection.execute("SELECT revision,plan_hash FROM plan_revisions WHERE plan_hash=?", (plan_hash,)).fetchone()
        return dict(row)

    def plan(self, plan_hash: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT revision,plan_hash,plan_json,active FROM plan_revisions WHERE plan_hash=?", (plan_hash,)).fetchone()
        if not row:
            raise InvariantViolation("PLAN_UNKNOWN", "plan revision is not registered")
        result = dict(row)
        result["plan"] = json.loads(result.pop("plan_json"))
        result["active"] = bool(result["active"])
        return result

    def observe(self, source: dict[str, Any], *, cursor: str, idempotency_key: str, payload: Any, observed_at: str | None = None) -> dict[str, Any]:
        for key in ("source_id", "kind", "fresh_after_seconds"):
            if key not in source:
                raise InvariantViolation("SOURCE_SCHEMA", f"source missing {key}")
        observed_at = observed_at or utc_now()
        if not isinstance(payload, dict):
            return self._failed_observation(source, cursor, idempotency_key, payload, observed_at)
        authors = source.get("authors", [])
        if not isinstance(authors, list) or not all(isinstance(author, str) and author for author in authors):
            raise InvariantViolation("OBSERVATION_AUTHORSHIP", "observation provenance authors must be a list of non-empty identities")
        payload_hash = digest({"payload": payload, "authors": authors})
        with self._connect() as connection:
            existing = connection.execute("SELECT observation_id,payload_hash,status FROM observations WHERE source_id=? AND idempotency_key=?", (source["source_id"], idempotency_key)).fetchone()
            if existing:
                if existing["payload_hash"] != payload_hash:
                    raise InvariantViolation("OBSERVATION_IDEMPOTENCY_CONFLICT", "idempotency key was reused with a different payload")
                # The observation body is append-only and unchanged, but a source whose
                # real-world value is genuinely stable between ticks must still have its
                # freshness clock advanced by this successful re-check -- otherwise a
                # healthy, actively-polled source falsely alarms as stale purely from
                # time passing rather than from any actual failure to re-verify it.
                connection.execute("INSERT INTO source_cursors(source_id,kind,cursor,fresh_after_seconds,observed_at) VALUES(?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET kind=excluded.kind,cursor=excluded.cursor,fresh_after_seconds=excluded.fresh_after_seconds,observed_at=excluded.observed_at", (source["source_id"], source["kind"], cursor, int(source["fresh_after_seconds"]), observed_at))
                return {"observation_id": existing["observation_id"], "status": existing["status"], "idempotent": True}
            connection.execute("INSERT INTO observations(source_id,source_kind,cursor,idempotency_key,payload_json,authors_json,observed_at,payload_hash,status) VALUES(?,?,?,?,?,?,?,?,?)", (source["source_id"], source["kind"], cursor, idempotency_key, canonical(payload), canonical(authors), observed_at, payload_hash, "OBSERVED"))
            observation_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            connection.execute("INSERT INTO source_cursors(source_id,kind,cursor,fresh_after_seconds,observed_at) VALUES(?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET kind=excluded.kind,cursor=excluded.cursor,fresh_after_seconds=excluded.fresh_after_seconds,observed_at=excluded.observed_at", (source["source_id"], source["kind"], cursor, int(source["fresh_after_seconds"]), observed_at))
        return {"observation_id": observation_id, "status": "OBSERVED", "idempotent": False}

    def _failed_observation(self, source: dict[str, Any], cursor: str, idempotency_key: str, payload: Any, observed_at: str) -> dict[str, Any]:
        with self._connect() as connection:
            failure = connection.execute("SELECT attempts,quarantined FROM observation_failures WHERE source_id=? AND idempotency_key=?", (source["source_id"], idempotency_key)).fetchone()
            attempts = (failure["attempts"] if failure else 0) + 1
            quarantined = attempts >= 3
            connection.execute("INSERT INTO observation_failures(source_id,idempotency_key,attempts,last_error,quarantined) VALUES(?,?,?,?,?) ON CONFLICT(source_id,idempotency_key) DO UPDATE SET attempts=excluded.attempts,last_error=excluded.last_error,quarantined=excluded.quarantined", (source["source_id"], idempotency_key, attempts, "payload must be an object", int(quarantined)))
            if quarantined and not connection.execute("SELECT 1 FROM observations WHERE source_id=? AND idempotency_key=?", (source["source_id"], idempotency_key)).fetchone():
                connection.execute("INSERT INTO observations(source_id,source_kind,cursor,idempotency_key,payload_json,observed_at,payload_hash,status) VALUES(?,?,?,?,?,?,?,?)", (source["source_id"], source["kind"], cursor, idempotency_key, canonical({"raw_payload_type": type(payload).__name__}), observed_at, digest({"raw_payload_type": type(payload).__name__}), "QUARANTINED"))
                observation_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            else:
                row = connection.execute("SELECT observation_id FROM observations WHERE source_id=? AND idempotency_key=?", (source["source_id"], idempotency_key)).fetchone()
                observation_id = row["observation_id"] if row else None
        return {"observation_id": observation_id, "status": "QUARANTINED" if quarantined else "RETRY", "attempts": attempts}

    def source_state(self, source_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM source_cursors WHERE source_id=?", (source_id,)).fetchone()
        if not row:
            raise InvariantViolation("SOURCE_UNKNOWN", "source has no observation")
        return dict(row)

    def observations(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM observations ORDER BY observation_id").fetchall()
        output = []
        for row in rows:
            item = dict(row); item["payload"] = json.loads(item.pop("payload_json")); item["authors"] = json.loads(item.pop("authors_json")); output.append(item)
        return output

    def quarantine(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM observation_failures WHERE quarantined=1 ORDER BY source_id,idempotency_key")]

    def enroll_independent_verifier(self, verifier: str, *, actor: str, approval_evidence: list[str]) -> None:
        if actor != "native-surrogate" or not verifier or not approval_evidence:
            raise InvariantViolation("VERIFIER_ENROLLMENT_AUTHORITY", "Native Surrogate enrollment requires a verifier identity and approval evidence")
        with self._connect() as connection:
            connection.execute("INSERT INTO independent_verifiers(actor_id,enrolled_by,approval_evidence_json,enrolled_at) VALUES(?,?,?,?)", (verifier, actor, canonical(approval_evidence), utc_now()))

    def accept_evidence(self, evidence_id: str, *, observation_id: int, actor: str, classification: str, scope: str, supports: list[str], authors: list[str]) -> None:
        if classification not in {"VERIFIED", "REJECTED", "INCONCLUSIVE"}:
            raise InvariantViolation("EVIDENCE_AUTHORITY", "evidence classification is invalid")
        if not authors:
            raise InvariantViolation("EVIDENCE_AUTHORSHIP_REQUIRED", "evidence acceptance requires declared source authors")
        with self._connect() as connection:
            verifier = connection.execute("SELECT 1 FROM independent_verifiers WHERE actor_id=?", (actor,)).fetchone()
            if not verifier:
                raise InvariantViolation("EVIDENCE_VERIFIER_UNENROLLED", "only an enrolled independent verifier may classify evidence")
            if actor in authors:
                raise InvariantViolation("EVIDENCE_SELF_CERTIFICATION", "a verifier cannot certify evidence they authored or fixed")
            observation = connection.execute("SELECT status,authors_json FROM observations WHERE observation_id=?", (observation_id,)).fetchone()
            if not observation or observation["status"] != "OBSERVED":
                raise InvariantViolation("EVIDENCE_OBSERVATION", "only a retained non-quarantined observation can be accepted")
            observed_authors = json.loads(observation["authors_json"])
            if actor in observed_authors:
                raise InvariantViolation("EVIDENCE_SELF_CERTIFICATION", "a verifier cannot certify an observation they authored or fixed")
            if authors != observed_authors:
                raise InvariantViolation("EVIDENCE_PROVENANCE_MISMATCH", "acceptance authors must exactly match immutable observation provenance")
            connection.execute("INSERT INTO accepted_evidence(evidence_id,observation_id,accepted_by,classification,scope,supports_json,accepted_at) VALUES(?,?,?,?,?,?,?)", (evidence_id, observation_id, actor, classification, scope, canonical(supports), utc_now()))

    def preview_impact(self, candidate_hash: str) -> dict[str, Any]:
        candidate = self.plan(candidate_hash)["plan"]
        with self._connect() as connection:
            active = connection.execute("SELECT plan_json FROM plan_revisions WHERE active=1").fetchone()
        old_catalogue = set(json.loads(active["plan_json"])["catalogue"]) if active else set(PLAN_CATALOGUE)
        return {"candidate_hash": candidate_hash, "removed_catalogue_scopes": sorted(old_catalogue - set(candidate["catalogue"])), "added_catalogue_scopes": sorted(set(candidate["catalogue"]) - old_catalogue), "activation": "PREVIEW_ONLY"}

    def activate_plan(self, candidate_hash: str, *, actor: str, dispositions: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        if actor != "native-surrogate":
            raise InvariantViolation("ACTIVATION_AUTHORITY", "only the Native Surrogate may request a plan activation")
        impact = self.preview_impact(candidate_hash)
        dispositions = dispositions or {}
        missing = [scope for scope in impact["removed_catalogue_scopes"] if scope not in dispositions]
        if missing:
            raise InvariantViolation("IMPACT_DISPOSITION_REQUIRED", f"missing impact dispositions: {', '.join(missing)}")
        for scope in impact["removed_catalogue_scopes"]:
            item = dispositions[scope]
            if item.get("action") not in {"CARRY_FORWARD", "INVALIDATE"} or not item.get("reason") or not item.get("evidence"):
                raise InvariantViolation("IMPACT_DISPOSITION_INVALID", "impact disposition requires action, reason and evidence")
        with self._connect() as connection:
            for scope in impact["removed_catalogue_scopes"]:
                item = dispositions[scope]
                connection.execute("INSERT OR IGNORE INTO impact_dispositions(candidate_hash,scope,action,reason,evidence_json,recorded_by,recorded_at) VALUES(?,?,?,?,?,?,?)", (candidate_hash, scope, item["action"], item["reason"], canonical(item["evidence"]), actor, utc_now()))
            connection.execute("UPDATE plan_revisions SET active=0 WHERE active=1")
            connection.execute("UPDATE plan_revisions SET active=1 WHERE plan_hash=?", (candidate_hash,))
            row = connection.execute("SELECT revision FROM plan_revisions WHERE plan_hash=?", (candidate_hash,)).fetchone()
        return {"active_revision": row["revision"], "activation": "GOVERNED_PLAN_ONLY", "does_not_close_gates": True}

    def record_contradiction(self, contradiction_id: str, *, sources: list[str], detail: str) -> None:
        with self._connect() as connection:
            connection.execute("INSERT INTO contradictions(id,sources_json,detail,recorded_at) VALUES(?,?,?,?)", (contradiction_id, canonical(sources), detail, utc_now()))

    def reconcile(self, *, now: str | None = None) -> dict[str, Any]:
        now = now or utc_now()
        with self._connect() as connection:
            active = connection.execute("SELECT revision FROM plan_revisions WHERE active=1").fetchone()
            evidence = connection.execute("SELECT evidence_id,observation_id,accepted_by,classification,scope,supports_json,accepted_at FROM accepted_evidence ORDER BY accepted_at,evidence_id").fetchall()
            contradictions = connection.execute("SELECT * FROM contradictions WHERE status='OPEN' ORDER BY recorded_at,id").fetchall()
        accepted = []
        for row in evidence:
            item = dict(row); item["supports"] = json.loads(item.pop("supports_json")); accepted.append(item)
        return {"schema_version": "pariprashna-elevation-projection@1", "active_plan_revision": active["revision"] if active else None, "accepted_evidence": accepted, "accepted_progress": {}, "closed_gates": [], "cutover_eligible": False, "contradictions": [dict(row) for row in contradictions], "as_of": now, "authority_boundary": "observations and evidence never self-promote progress, gates, or cutover"}

    def dashboard(self, *, now: str | None = None) -> dict[str, Any]:
        now = now or utc_now()
        now_value = parse_time(now)
        with self._connect() as connection:
            sources = connection.execute("SELECT * FROM source_cursors ORDER BY source_id").fetchall()
        rendered_sources = []
        for row in sources:
            item = dict(row)
            age = max(0, int((now_value - parse_time(item["observed_at"])).total_seconds()))
            item["age_seconds"] = age
            item["freshness"] = "FRESH" if age <= item["fresh_after_seconds"] else "STALE"
            rendered_sources.append(item)
        projection = self.reconcile(now=now)
        source_states = {name: {"freshness": "UNKNOWN", "payload": None} for name in AdapterRunner.REQUIRED_ADAPTERS}
        for item in rendered_sources:
            latest = next((row for row in reversed(self.observations()) if row["source_id"] == item["source_id"]), None)
            source_states[item["source_id"]] = {"freshness": item["freshness"], "payload": latest["payload"] if latest else None, "cursor": item["cursor"], "observed_at": item["observed_at"]}
        gaps = [name for name, state in source_states.items() if state["freshness"] != "FRESH"]
        return {"schema_version": "pariprashna-elevation-dashboard@1", "plan_revision": projection["active_plan_revision"], "sources": rendered_sources, "source_states": source_states, "contradictions": projection["contradictions"], "data_quality_gaps": gaps, "projection": projection}

    def cutover_packet(self) -> dict[str, Any]:
        dashboard = self.dashboard()
        missing = ["independent shadow comparison", "restart/restore/rollback proof", "attested immutable release", "native decision"]
        if dashboard["data_quality_gaps"]:
            missing.insert(0, "fresh source reconciliation")
        if dashboard["contradictions"]:
            missing.insert(0, "resolved contradictions")
        return {"schema_version": "pariprashna-cutover-packet@1", "eligible": False, "missing": missing, "live_runtime_changed": False, "authority_boundary": "final service swap requires a native decision"}


PLAN_CATALOGUE = {"P-PIPE", "P-PORTAL", "P-GUIDED", "PPR", "EDIR"}
BASELINE_CATALOGUE = {
    "P-PIPE": {"scope": "historical-observation-only", "items": [f"S{i}" for i in range(1, 12)]},
    "P-PORTAL": {"scope": "historical-observation-only", "items": [f"J{i}" for i in range(1, 11)]},
    "P-GUIDED": {"scope": "historical-observation-only", "items": ["L-USER", "L-WIRE", "L-CODE"]},
    "PPR": {"scope": "current-assurance", "items": ["pariprashna-product-requirements"]},
    "EDIR": {"scope": "historical-observation-only", "items": ["experience-defect-and-improvement-register"]},
}


class AdapterRunner:
    """Runs source probes into the shadow observation ledger, never into evidence acceptance."""

    REQUIRED_ADAPTERS = ("codex_tasks", "github", "git_worktrees", "runtime", "tests_evidence", "edir")
    _KINDS = {
        "codex_tasks": "CODEX_TASK", "github": "GITHUB_PR_CI_MERGE_QUEUE",
        "git_worktrees": "GIT_WORKTREE", "runtime": "DEPLOYED_RUNTIME",
        "tests_evidence": "TEST_EVIDENCE", "edir": "EDIR",
    }

    def __init__(self, store: ElevationStore, *, probes: dict[str, Any], fresh_after_seconds: int | dict[str, int] = 300):
        unknown = set(probes) - set(self.REQUIRED_ADAPTERS)
        if unknown:
            raise InvariantViolation("ADAPTER_UNKNOWN", f"unsupported adapters: {', '.join(sorted(unknown))}")
        self.store = store
        self.probes = probes
        if isinstance(fresh_after_seconds, dict):
            unknown_budget = set(fresh_after_seconds) - set(self.REQUIRED_ADAPTERS)
            if unknown_budget:
                raise InvariantViolation("ADAPTER_UNKNOWN", f"unsupported adapters in freshness budget: {', '.join(sorted(unknown_budget))}")
            self.fresh_after_seconds = {adapter: fresh_after_seconds.get(adapter, 300) for adapter in self.REQUIRED_ADAPTERS}
        else:
            self.fresh_after_seconds = {adapter: fresh_after_seconds for adapter in self.REQUIRED_ADAPTERS}

    def collect(self, adapter: str) -> dict[str, Any]:
        if adapter not in self.REQUIRED_ADAPTERS:
            raise InvariantViolation("ADAPTER_UNKNOWN", "adapter is not required by the elevation plan")
        probe = self.probes.get(adapter)
        if not probe:
            return {"status": "UNKNOWN", "reason": "not configured"}
        previous = None
        try:
            previous = self.store.source_state(adapter).get("cursor")
        except InvariantViolation:
            pass
        try:
            result = probe(previous)
            if not isinstance(result, dict) or not isinstance(result.get("payload"), dict) or "cursor" not in result:
                raise InvariantViolation("ADAPTER_PAYLOAD", "adapter result must contain cursor and object payload")
            return self.store.observe({"source_id": adapter, "kind": self._KINDS[adapter], "fresh_after_seconds": self.fresh_after_seconds[adapter]}, cursor=str(result["cursor"]), idempotency_key=f"{adapter}:{result['cursor']}", payload=result["payload"])
        except Exception as exc:
            return {"status": "UNKNOWN", "reason": str(exc), "cursor": previous}

    def collect_all(self) -> dict[str, dict[str, Any]]:
        return {adapter: self.collect(adapter) for adapter in self.REQUIRED_ADAPTERS}
