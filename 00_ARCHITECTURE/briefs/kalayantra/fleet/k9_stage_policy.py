#!/usr/bin/env python3
"""K9-4b `k9_rebuild_stage` admission policy: the absence and exposure gates (ruling SR-PREP-LANES-1 (2)).

The executor loads THIS file from the request's reviewed (merged) commit, exactly as it loads the head policy, and calls `request_problem(req, ops, accepted_readback)`
at the tail of `validate` (so again immediately before execution). Standard library only: the executor is standalone and imports nothing from a working tree.

The kind stages, in PRODUCTION, the frozen `build_runs` row and the ONE open candidate that `orchestrator_rebuild` requires. Besides the generic production gates (live lease,
signer acceptance or a verified pack fill, the owner's go in `run/ops/owner_go/<operation_id>.json`, the dry run's receipt) it is admitted only when two ACCEPTED, FRESH
`readback_sql` receipts of item K9-4b are cited, each of the fixed SELECT this file defines (the readback request's `sql-sha256` must equal the digest of the exact wrapped
bytes below, so a different query reading zeros proves nothing):

  absence_readback   `ky.k9_stage_absence/1`: for the request's run-id there is no build run and no candidate, and the chart has no open (planned/running/paused) rebuild
                     run and no building candidate -- nothing exists that a second frozen row or candidate would duplicate;
  exposure_readback  `ky.k9_stage_exposure/1`: the served head is exactly the request's `expected-head` (`NONE` = no head), and the candidate generation the staging will
                     create (`candidate:<run-id>`) holds no row in any generation-partitioned layer table or in the candidate grain table -- the candidate is invisible to serving.

Every detector here reads a number or a string out of the readback's own JSON; a missing field, a wrong schema, another run, a stale `measured_at` or a non-zero count REFUSES.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import re

CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
ITEM = "K9-4b"
KINDS = ("k9_rebuild_stage", "k9_rebuild_stage_dryrun")
ABSENCE_SCHEMA = "ky.k9_stage_absence/1"
EXPOSURE_SCHEMA = "ky.k9_stage_exposure/1"
FRESH_S = 3600          # a readback older than this says nothing about now
FUTURE_S = 300          # clock skew allowed between the database and the executor
UUID_RE = re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ASSET_ID = re.compile(r"^ka_[a-z0-9_]{1,60}$")
GENERATION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
OPEN_RUN_STATES = ("planned", "running", "paused")
# the generation-partitioned layer tables migrations 1404/1405 added (fleet/k9_readback + generation_partitions readbacks); a row under the new generation anywhere is exposure
PARTITIONED_TABLES = ("kala_activation_predicates", "kala_convergence", "kala_obstruction", "gochara_resonance_map")


def _uuid(value) -> str:
    if not (isinstance(value, str) and UUID_RE.fullmatch(value)):
        raise ValueError("run-id must be a lowercase UUID")
    return value


def absence_sql(run_id: str) -> str:
    run_id = _uuid(run_id)
    return (f"SELECT jsonb_build_object('schema','{ABSENCE_SCHEMA}','chart_id','{CANONICAL_CHART}','run_id','{run_id}',"
            "'measured_at',to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"'),"
            f"'build_runs_for_run_id',(SELECT count(*) FROM build_runs WHERE id='{run_id}'::uuid),"
            f"'candidates_for_run_id',(SELECT count(*) FROM kala_layer_candidate WHERE build_id='{run_id}'::uuid),"
            f"'open_rebuild_runs',(SELECT count(*) FROM build_runs WHERE chart_id='{CANONICAL_CHART}'::uuid AND action='rebuild' AND state IN "
            + "(" + ",".join(f"'{s}'" for s in OPEN_RUN_STATES) + ")),"
            f"'building_candidates',(SELECT count(*) FROM kala_layer_candidate WHERE chart_id='{CANONICAL_CHART}'::uuid AND state='building')"
            ") AS evidence")


def exposure_sql(run_id: str) -> str:
    run_id = _uuid(run_id)
    generation = "candidate:" + run_id
    partitions = ",".join(f"'{t}',(SELECT count(*) FROM {t} WHERE chart_id='{CANONICAL_CHART}'::uuid AND generation='{generation}')" for t in PARTITIONED_TABLES)
    return (f"SELECT jsonb_build_object('schema','{EXPOSURE_SCHEMA}','chart_id','{CANONICAL_CHART}','run_id','{run_id}',"
            "'measured_at',to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"'),"
            f"'head_generation',(SELECT generation FROM kala_layer_head WHERE chart_id='{CANONICAL_CHART}'::uuid),"
            f"'target_generation','{generation}',"
            f"'grain_rows',(SELECT count(*) FROM kala_layer_candidate_grain WHERE chart_id='{CANONICAL_CHART}'::uuid AND generation='{generation}'),"
            f"'partition_rows',jsonb_build_object({partitions})"
            ") AS evidence")


def wrapped_sql(query: str) -> str:
    """The bytes the readback child runs (fleet/k9_readback.prepare_readback wraps a single-column JSONB SELECT this way)."""
    return "SELECT evidence::text AS evidence FROM (" + query.strip() + ") AS t"


def sql_sha256(query: str) -> str:
    return hashlib.sha256(wrapped_sql(query).encode()).hexdigest()


def _utc(value) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone-qualified time required")
    return parsed.astimezone(dt.timezone.utc)


def _count(value) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("a count is not a non-negative integer")
    return value


def _evidence(ref, label: str, query: str, ops, accepted_readback, now: dt.datetime) -> dict:
    """The parsed evidence object of ONE cited, accepted, fresh readback of exactly `query`; raises ValueError naming the gate."""
    if not (isinstance(ref, dict) and set(ref) == {"name", "sha256"} and isinstance(ref["name"], str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}\.json", ref["name"])
            and isinstance(ref["sha256"], str) and HEX64.fullmatch(ref["sha256"])):
        raise ValueError(f"{label} {{name, sha256}} citing an accepted readback receipt is required")
    operation_id = ref["name"][:-len(".json")]
    if not SAFE_ID.fullmatch(operation_id):
        raise ValueError(f"{label} names an unsafe operation id")
    receipts = (ops / "receipts").resolve()
    path = (ops / "receipts" / ref["name"]).resolve()
    if path.parent != receipts:
        raise ValueError(f"{label} escapes the receipts directory")
    try:
        if hashlib.sha256(path.read_bytes()).hexdigest() != ref["sha256"]:
            raise ValueError(f"{label} differs from its cited sha256")
        archived = json.loads((ops / "done" / ref["name"]).read_text())
        got = accepted_readback(operation_id, "readback_sql")
    except (OSError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"{label} cannot be read as an accepted readback") from exc
    if got is None:
        raise ValueError(f"{label} is not an accepted, completed readback_sql")
    if not (isinstance(archived, dict) and archived.get("kind") == "readback_sql" and archived.get("item_id") == ITEM and archived.get("operation_id") == operation_id):
        raise ValueError(f"{label} is not a K9-4b readback_sql")
    args = archived.get("args") or {}
    if (args.get("sql-sha256") or args.get("sql_sha256")) != sql_sha256(query):
        raise ValueError(f"{label} did not run this gate's fixed query (sql-sha256 differs)")
    try:
        rows = list(csv.DictReader(io.StringIO(got[1].decode()), delimiter="\t"))
        evidence = json.loads(rows[0]["evidence"]) if len(rows) == 1 else None
    except (ValueError, KeyError, IndexError, UnicodeError):
        evidence = None
    if not isinstance(evidence, dict):
        raise ValueError(f"{label} output is not one evidence row")
    try:
        measured = _utc(evidence.get("measured_at"))
    except (TypeError, ValueError):
        raise ValueError(f"{label} has no readable measured_at") from None
    if not (now - dt.timedelta(seconds=FRESH_S) <= measured <= now + dt.timedelta(seconds=FUTURE_S)):
        raise ValueError(f"{label} is stale or from the future (measured_at {evidence.get('measured_at')})")
    return evidence


def args_problem(req: dict) -> str | None:
    """The shape of the request itself (the dry run too): item K9-4b and exactly the four staging arguments, each well formed."""
    if req.get("item_id") != ITEM:
        return f"{req.get('kind')} is item {ITEM} only"
    args = req.get("args") or {}
    if set(args) != {"assets", "run-id", "natal-build", "expected-head"}:
        return "args must be exactly assets, run-id, natal-build and expected-head"
    try:
        _uuid(args["run-id"]), _uuid(args["natal-build"])
    except ValueError as exc:
        return str(exc)
    assets = str(args["assets"]).split(",")
    if not assets or any(not ASSET_ID.fullmatch(a) for a in assets) or len(set(assets)) != len(assets):
        return "assets must be distinct ka_ asset ids"
    if args["expected-head"] != "NONE" and not GENERATION.fullmatch(str(args["expected-head"])):
        return "expected-head must be NONE or a generation"
    return None


def request_problem(req: dict, ops, accepted_readback, now: dt.datetime | None = None) -> str | None:
    """None when the request may proceed, else the refusal. The dry run is checked for shape only; the real kind also for absence and exposure."""
    if req.get("kind") not in KINDS:
        return None
    problem = args_problem(req)
    if problem or req["kind"] != "k9_rebuild_stage":
        return problem
    now = now or dt.datetime.now(dt.timezone.utc)
    args = req["args"]
    run_id = args["run-id"]
    try:
        absence = _evidence(req.get("absence_readback"), "absence_readback", absence_sql(run_id), ops, accepted_readback, now)
        if (absence.get("schema") != ABSENCE_SCHEMA or absence.get("run_id") != run_id or absence.get("chart_id") != CANONICAL_CHART
                or any(_count(absence.get(k)) != 0 for k in ("build_runs_for_run_id", "candidates_for_run_id", "open_rebuild_runs", "building_candidates"))):
            return "absence gate: a run or candidate already exists for this staging (or the readback is not this run's absence record)"
        exposure = _evidence(req.get("exposure_readback"), "exposure_readback", exposure_sql(run_id), ops, accepted_readback, now)
        head = exposure.get("head_generation")
        if (exposure.get("schema") != EXPOSURE_SCHEMA or exposure.get("run_id") != run_id or exposure.get("chart_id") != CANONICAL_CHART
                or exposure.get("target_generation") != "candidate:" + run_id or _count(exposure.get("grain_rows")) != 0):
            return "exposure gate: the readback is not this run's exposure record, or the candidate generation already holds grain rows"
        partitions = exposure.get("partition_rows")
        if not isinstance(partitions, dict) or set(partitions) != set(PARTITIONED_TABLES) or any(_count(v) != 0 for v in partitions.values()):
            return "exposure gate: the candidate generation already holds rows in a layer table"
        if (head if head is not None else "NONE") != args["expected-head"]:
            return f"exposure gate: the served head is {head!r}, not the request's expected-head {args['expected-head']!r}"
    except ValueError as exc:
        return str(exc)
    return None


def main(argv=None) -> int:
    """`k9_stage_policy.py sql absence|exposure <run-id>` prints the fixed query the cockpit prepares as a K9-4b readback_sql (fleet/k9_readback.prepare_readback binds its digest)."""
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 3 or args[0] != "sql" or args[1] not in ("absence", "exposure"):
        print("usage: k9_stage_policy.py sql absence|exposure <run-id>", file=sys.stderr)
        return 2
    print((absence_sql if args[1] == "absence" else exposure_sql)(args[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
