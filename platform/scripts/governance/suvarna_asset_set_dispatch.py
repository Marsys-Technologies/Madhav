#!/usr/bin/env python3
"""suvarna_asset_set_dispatch.py -- ONE forced multi-asset (L0 + L1 + L2) build run over an EXPLICIT id list.

WHY THIS EXISTS
  The portal Build (scope='global') never carries L0, and the two dispatchers refuse the shape that can: suvarna_level_wave.py is
  per_chart only (NON_PER_CHART_SCOPE) and allows --force-execute for one asset; suvarna_global_asset_dispatch.py is exactly one
  global asset. The only run shape that carries global (L0) and per-chart (L1, L2) assets together is
  scope='asset_set', action='rebuild', scope_target='<comma list>' on one anchor chart (research: POST/DAG_RUN_ANSWERS.md, section A5;
  the runner accepts mixed scopes, runner.py validate_frozen_run_manifest takes each asset's scope from the frozen manifest).
  This tool inserts exactly ONE such build_runs row (the same INSERT text and manifest builder as the wave and the portal), then
  executes the Cloud Run job once with NIRMANA_FORCE_EXECUTE=1 (and, optionally, ORCHESTRATOR_WORKER_LIMIT=<n>) set on THAT
  execution only (`--update-env-vars` on `gcloud run jobs execute`; the job's own environment is never changed).
  It IMPORTS suvarna_level_wave / suvarna_global_asset_dispatch gates and helpers; it edits neither, nor the FROZEN orchestrator.

THE RUN
  build_runs: scope 'asset_set', scope_target = the ids in plan order, action 'rebuild', state 'planned', plan = the ids,
  plan_manifest = nirmana-run-manifest/v1 (waves from the wave tool's longest-path planner; the runner executes dependency-gated,
  the waves are informational), chart_id = the ANCHOR chart (a real chart, e.g. 482012f1-...), triggered_by =
  `asset-set-dispatch:anchor_chart=<uuid>;manifest_sha256=<16 hex>`; build_run_assets: one 'queued' row per id.
  LOCKS (runner.py execute_run, locks.py): the run takes the anchor chart's advisory lock; because the plan holds a global asset it
  also takes the ONE global-assets lock. While it is planned/running/paused: no other run on the anchor chart can start (unique
  active-run index + ANCHOR_CHART_BUSY), and any other run (any chart) that contains a global asset DEFERS (exit 3) on the global
  lock. Per-chart-only runs of OTHER charts are not blocked. The global assets' throughput rows stay chart_id NULL (runner eff()).

REFUSALS (exit 4, JSON `refusals`, one entry per id where it concerns an id; fail closed; nothing inserted)
  per id: REGISTRY_ROW_MISSING, NOT_ACTIVE, NO_WRITER, WRITER_SUBASSET (built as a side effect of its parent writer: list the parent),
  SERVICE_ASSET, SCOPE_NOT_ALLOWED, DOMAIN_SCOPE_MISMATCH, LAYER_NOT_ALLOWED, FAMILY_ASSET, SPLITS_FAMILY, PROTECTED_ASSET (build_protected_assets
  for the anchor chart), FORCE_BYPASSED_BY_PROBE (rebuild_on_probe_fail=true: a green probe skips the writer even under force),
  ACCEPT_EXCLUDED_NOT_NEEDED (an id that passes every check cannot be waved away), ACCEPT_EXCLUDED_NOT_REQUESTED.
  FAMILY OVERRIDE (--allow-family-assets <ids>, SS N-443 D3; OUR tool only, the frozen orchestrator and FAMILY_ASSETS.json are untouched): waives
  EXACTLY FAMILY_ASSET and SPLITS_FAMILY, ONLY for the ids named, each of which must be in the request and be a family member (name pattern or
  FAMILY_ASSETS.json family_set). Everything else still refuses for a named id (NOT_ACTIVE, NO_WRITER, SERVICE_ASSET, PROTECTED_ASSET,
  FORCE_BYPASSED_BY_PROBE, LAYER_NOT_ALLOWED, ...): the layer allow-list stays --allowed-layers. A named id that is not requested
  (ACCEPT_FAMILY_NOT_REQUESTED), not a family member (ACCEPT_FAMILY_NOT_FAMILY) or also in --accept-excluded (ACCEPT_FAMILY_ALSO_EXCLUDED) refuses.
  The sorted list is bound into the confirm token, written to the receipt (`family_override`, `inputs.allow_family`), put in the run_committed /
  run_dispatched events and the plan summary, and logged as `family-override: <ids>`. --dispatch-existing takes it from the receipt. With the flag
  absent the token, the summary, the receipt and the events are byte-for-byte what they were before the flag existed.
  An id that fails is NEVER dropped silently: the run is refused unless the id is named in --accept-excluded (then it is dropped, listed in the
  plan, and bound into the confirm token).
  cross-chart impact (the 33 global assets): CROSS_CHART_IMPACT_NOT_ACCEPTED / CROSS_CHART_COUNT_MISMATCH / ACCEPT_CROSS_CHART_UNMATCHED -- every OTHER
  chart (and `global`) that keeps lit rows of dependents of the plan's global assets must be named with its exact count,
  `--accept-cross-chart-impact <chart uuid|global>=<n>` (the plan prints the counts and the flags); the impact's sha256 and the accepted counts are
  bound into the token and re-read inside the INSERT transaction (IMPACT_CHANGED).
  run level: EMPTY_PLAN, ANCHOR_CHART_INVALID, ANCHOR_CHART_BUSY, GLOBAL_LOCK_HELD, CONFLICTING_ACTIVE_RUN, ALREADY_DISPATCHED (a prior run of
  this tool exists: name each with --allow-redispatch <run_id>), WORKER_LIMIT_INVALID, CONNECTION_HEADROOM_LOW, CONFIRM_TOKEN_MISMATCH,
  RECEIPT_PATH_INVALID, LIVE_JOB_IMAGE_UNREADABLE, LIVE_JOB_IMAGE_DIFFERS, and every gate of the wave (IMAGE_SKEW, CODE_DIGEST_UNAVAILABLE,
  FORCE_NOT_SUPPORTED_BY_IMAGE, JOB_SHA_MISMATCH, JOB_SHA_CHANGED, DEPENDENCY_NOT_READY, REGISTRY_ROW_CHANGED, FAMILY_FILE_*, FAMILY_REF_*).

RECOVERY MODES (the run was committed 'planned' but the process died before the execute; it blocks the anchor chart)
  --dispatch-existing <RUN_ID> --commit --confirm <the receipt's token> re-plans from the receipt's inputs, requires the same
      manifest digest AND token, the run still 'planned' and ours, no execution in the receipt, then executes once (no INSERT).
  --terminalise-run <RUN_ID> [--commit --confirm TERMINALISE_<run8>_NO_EXECUTION_STARTED]   cancels a still-'planned' run of this tool (the UPDATE
      matches state='planned' only). Check `gcloud run jobs executions list` for an execution with that --run-id first.
  Write-ahead marker: the receipt gets `dispatch_intended_at` BEFORE the execute; --dispatch-existing refuses (DISPATCH_ALREADY_ATTEMPTED) when it is set and no
  execution is recorded, and --terminalise-run refuses (EXECUTION_RECORDED_IN_RECEIPT) when an execution or the marker is recorded; in both, `--allow-redispatch <RUN_ID>`
  asserts "the executions list was checked: no live execution of this run exists". After an unknown COMMIT outcome (exit 6) the receipt is rewritten with the run id
  (committed "unknown"); the database row (chart + triggered_by + manifest digest + state planned) is the real binding. One mutating process per receipt (flock on <receipt>.lock).
  Gates that stay in the operator runbook (they need gh / gcloud, which this tool deliberately never calls except the one execute and the read-only live-image `describe`): no deploy
  workflow open, watchdog-reaper paused, backup / PITR point recorded, (the live job image sha is read by the tool itself: gcloud run jobs describe, read-only, at plan / before INSERT / before execute).

EXIT CODES  0 ok (plan done / dispatched; verified when --wait / --verify-run) | 1 DATABASE_URL missing | 2 bad input |
  3 dispatch failed after the run was committed (terminalised, or a warning names it) | 4 a gate refused | 6 unexpected / COMMIT outcome
  unknown / receipt unwritable | 7 interrupted (the run id was printed: never dispatch again, use --verify-run) |
  8 FORCE_DID_NOT_TAKE_EFFECT (an asset ended skip_no_delta) | 10 the run did not complete cleanly / could not be verified.

Exec runs it; the tests use fakes only. Nothing here is run against production by the author.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import suvarna_global_asset_dispatch as gad  # noqa: E402
import suvarna_level_wave as slw  # noqa: E402

SCHEMA = "suvarna.asset_set_dispatch/1"
RECEIPT_SCHEMA = "suvarna-asset-set-dispatch-receipt/v1"
TOKEN_SCHEMA = "suvarna-asset-set-dispatch-token/v1"
TRIGGERED_BY_PREFIX = "asset-set-dispatch:"
_TRIGGERED_BY_RE = re.compile(
    r"asset-set-dispatch:anchor_chart=[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12};manifest_sha256=[0-9a-f]{16}")

FORCE_ENV_VAR = slw.FORCE_ENV_VAR                       # NIRMANA_FORCE_EXECUTE
WORKER_LIMIT_ENV_VAR = "ORCHESTRATOR_WORKER_LIMIT"      # runner.py reads it once at import: set per execution it applies to that run only
WORKER_LIMIT_MIN, WORKER_LIMIT_MAX = 1, 6
MIN_HEADROOM_CONNECTIONS = 10                           # refuse a run that would leave fewer than this many connections free
RUNNER_DEFAULT_WORKER_LIMIT = 4                         # runner.py `_WORKER_LIMIT` default when the job env does not set it

FAMILY_WAIVED_CODES = ("FAMILY_ASSET", "SPLITS_FAMILY")   # the ONLY refusals --allow-family-assets can waive
DEFAULT_ALLOWED_LAYERS = ("brahmagyan", "ganita", "bodha")
ALLOWED_SCOPES = ("per_chart", "global")
# runner._WRITER_SUBASSET_IDS: registered writers with no own registry writer row; built as a side effect of the parent.
WRITER_SUBASSET_PARENTS = {"bg_nakshatra_medical": "bg_medical_mappings", "bg_transit_engine": "bg_transit_rules"}

IMPACT_SCHEMA = "suvarna-asset-set-cross-chart-impact/v1"
GLOBAL_KEY = "global"
EXIT_OK = 0
EXIT_FORCE_NOT_EFFECTIVE = 8
EXIT_VERIFY_FAILED = 10
IDS_FILE_MAX_BYTES = 64 * 1024
_ID_RE = re.compile(r"[a-z][a-z0-9_]*")

# The wave's candidate statement plus the registry `domain` column. Derived (not copied) so a change of the wave's SQL is inherited.
ROWS_SQL = slw.CANDIDATES_SQL.replace("SELECT ar.asset_id, ar.layer,", "SELECT ar.asset_id, ar.domain, ar.rebuild_on_probe_fail, ar.layer,", 1)
assert ROWS_SQL != slw.CANDIDATES_SQL, "wave CANDIDATES_SQL changed shape: re-derive ROWS_SQL"

CONNECTIONS_SQL = """
SELECT current_setting('max_connections')::int AS max_connections,
       current_setting('superuser_reserved_connections')::int AS reserved,
       (SELECT count(*) FROM pg_stat_activity)::int AS in_use
"""

GLOBAL_LOCK_RUNS_SQL = """
SELECT br.id, br.chart_id::text AS chart_id, br.state, bra.asset_id
  FROM build_runs br
  JOIN build_run_assets bra ON bra.run_id = br.id
  JOIN asset_registry ar ON ar.asset_id = bra.asset_id
 WHERE br.state IN ('planned','running','paused') AND ar.scope = 'global'
 ORDER BY br.id, bra.asset_id
"""

PROTECTED_SQL = "SELECT asset_id FROM build_protected_assets WHERE chart_id = %s AND asset_id = ANY(%s)"

# The runner's own downstream closure (asset_runner.compute_downstream_closure), for a SET of assets.
DOWNSTREAM_SET_SQL = """
WITH RECURSIVE downstream AS (
    SELECT asset_id FROM asset_registry
    WHERE depends_on && %s::text[]
    UNION
    SELECT ar.asset_id FROM asset_registry ar
    INNER JOIN downstream d ON d.asset_id = ANY(ar.depends_on)
)
SELECT asset_id FROM downstream ORDER BY asset_id
"""

PRIOR_DISPATCH_SQL = """
SELECT br.id, br.state, br.plan_manifest_digest, br.triggered_by
  FROM build_runs br
 WHERE left(br.triggered_by, %s) = %s
 ORDER BY br.created_at, br.id
"""


# ───────────────────────── helpers ─────────────────────────

def _refuse(code: str, detail: str, **extra: Any) -> slw.LevelWaveRefusal:
    return slw.LevelWaveRefusal([{"code": code, "detail": detail, **extra}])


def _emit(out, event: str, **fields) -> None:
    out.write(json.dumps({"schema": SCHEMA, "event": event, **fields}, sort_keys=True, default=str) + "\n")
    flush = getattr(out, "flush", None)
    if flush is not None:
        flush()


def _utc_iso(now: Callable[[], datetime]) -> str:
    return now().astimezone(timezone.utc).isoformat(timespec="seconds")


# ───────────────────────── input ─────────────────────────

def parse_asset_ids(assets: Sequence[str] | None, assets_file: str | None) -> list[str]:
    """Ids from --assets (comma list, repeatable) and/or --assets-file (ids separated by commas, spaces or newlines; `#` starts a
    comment). Order is the caller's. Empty, malformed or duplicate ids are errors, never normalised."""
    tokens: list[str] = []
    for raw in assets or ():
        tokens += [t.strip() for t in raw.split(",")]
    if assets_file:
        p = Path(assets_file)
        try:
            if p.is_symlink() or not p.is_file():
                raise OSError("not a regular file")
            data = p.read_bytes()
            if len(data) > IDS_FILE_MAX_BYTES:
                raise OSError(f"larger than {IDS_FILE_MAX_BYTES} bytes")
            text = data.decode("utf-8")
        except (OSError, ValueError) as exc:
            raise slw.LevelWaveError(f"--assets-file {assets_file}: {exc}") from None
        for line in text.splitlines():
            line = line.split("#", 1)[0]
            tokens += [t for t in re.split(r"[,\s]+", line) if t]
    if not tokens:
        raise slw.LevelWaveError("no asset ids: give --assets and/or --assets-file")
    bad = [t for t in tokens if not _ID_RE.fullmatch(t)]
    if bad:
        raise slw.LevelWaveError(f"malformed asset id(s): {bad[:5]!r}")
    dup = sorted({t for t in tokens if tokens.count(t) > 1})
    if dup:
        raise slw.LevelWaveError(f"duplicate asset id(s): {dup}")
    return tokens


def parse_id_list(values: Sequence[str] | None, flag: str) -> list[str]:
    out: list[str] = []
    for raw in values or ():
        out += [t.strip() for t in raw.split(",") if t.strip()]
    bad = [t for t in out if not _ID_RE.fullmatch(t)]
    if bad:
        raise slw.LevelWaveError(f"{flag}: malformed asset id(s) {bad[:5]!r}")
    if len(set(out)) != len(out):
        raise slw.LevelWaveError(f"{flag} names the same asset twice")
    return sorted(out)


def validate_worker_limit(value: int | None) -> int | None:
    if value is None:
        return None
    if not (WORKER_LIMIT_MIN <= value <= WORKER_LIMIT_MAX):
        raise _refuse("WORKER_LIMIT_INVALID", f"--worker-limit must be {WORKER_LIMIT_MIN}..{WORKER_LIMIT_MAX} (got {value})")
    return int(value)


# ───────────────────────── per-id validation ─────────────────────────

def classify_assets(ids: Sequence[str], rows: Sequence[Mapping[str, Any]], family: Mapping[str, Any], *,
                    allowed_layers: Sequence[str] = DEFAULT_ALLOWED_LAYERS, protected: Sequence[str] = (),
                    allow_family: Sequence[str] = ()) -> list[dict]:
    """Every problem of every requested id, as {asset, code, detail}, all reported together (sorted by id, then code). Empty = every
    id is a plannable asset. Pure. `allow_family` (the token-bound --allow-family-assets list) waives FAMILY_ASSET and SPLITS_FAMILY for
    exactly those ids and nothing else; its names are checked by validate_allow_family, not here."""
    waived = frozenset(allow_family)
    by_id: dict[str, dict] = {}
    findings: list[dict] = []
    for r in rows:
        if r["asset_id"] in by_id:
            findings.append({"asset": r["asset_id"], "code": "REGISTRY_ROW_MISSING", "detail": "duplicate registry rows"})
        by_id[r["asset_id"]] = dict(r)
    req = set(ids)
    for a in ids:
        r = by_id.get(a)
        if r is None:
            findings.append({"asset": a, "code": "REGISTRY_ROW_MISSING", "detail": f"no registry row for {a}"})
            continue
        if r.get("is_active") is not True:
            findings.append({"asset": a, "code": "NOT_ACTIVE", "detail": f"{a} is not active in the registry"})
        if r.get("asset_kind") == "service":
            findings.append({"asset": a, "code": "SERVICE_ASSET", "detail": f"{a} is a service (nothing to build; a probe is its own singleton run)"})
        if r.get("has_writer") is not True:
            if a in WRITER_SUBASSET_PARENTS:
                parent = WRITER_SUBASSET_PARENTS[a]
                findings.append({"asset": a, "code": "WRITER_SUBASSET", "parent": parent,
                                 "detail": f"{a} has no writer of its own: it is written as a side effect of {parent}"
                                           + ("" if parent in req else f" (which is not in the list)")})
            else:
                findings.append({"asset": a, "code": "NO_WRITER", "detail": f"{a} has has_writer=false: the planner never builds it"})
        scope = r.get("scope")
        if scope not in ALLOWED_SCOPES:
            findings.append({"asset": a, "code": "SCOPE_NOT_ALLOWED", "detail": f"{a} has scope {scope!r}; allowed {list(ALLOWED_SCOPES)}"})
        else:
            dom = r.get("domain")
            if dom is not None and ((scope == "global") != (dom == "shared")):
                findings.append({"asset": a, "code": "DOMAIN_SCOPE_MISMATCH",
                                 "detail": f"{a}: scope {scope!r} with domain {dom!r} (global assets are domain 'shared', per_chart are 'chart')"})
        if r.get("rebuild_on_probe_fail") is True:
            findings.append({"asset": a, "code": "FORCE_BYPASSED_BY_PROBE",
                             "detail": f"{a} has rebuild_on_probe_fail=true: with a green probe the runner marks it lit WITHOUT running the writer "
                                       "(force is not consulted), so a forced rebuild could not be verified"})
        if a in set(protected):
            findings.append({"asset": a, "code": "PROTECTED_ASSET",
                             "detail": f"{a} is in build_protected_assets for the anchor chart (the portal withholds it from every build)"})
        if r.get("layer") not in allowed_layers:
            findings.append({"asset": a, "code": "LAYER_NOT_ALLOWED", "detail": f"{a} is layer {r.get('layer')!r}; allowed {list(allowed_layers)}"})
    for f in slw.family_refusals(list(ids), family, committing=False):
        if f["code"] == "FAMILY_ASSET":
            if f["asset"] not in waived:
                findings.append({"asset": f["asset"], "code": "FAMILY_ASSET", "detail": f["detail"]})
        elif f["code"] == "SPLITS_FAMILY":
            for a in f["requested"]:
                if a not in waived:
                    findings.append({"asset": a, "code": "SPLITS_FAMILY", "detail": f["detail"]})
    return sorted(findings, key=lambda x: (x["asset"], x["code"]))


def validate_allow_family(ids: Sequence[str], allow_family: Sequence[str], family: Mapping[str, Any],
                          accept_excluded: Sequence[str] = ()) -> None:
    """The --allow-family-assets names themselves: every one must be requested and be a family member (the same test that raises
    FAMILY_ASSET: name pattern, or FAMILY_ASSETS.json family_set), and none may also be dropped by --accept-excluded. Raises
    LevelWaveRefusal with every problem; returns None when the list is exact. Pure."""
    req = set(ids)
    members = {f["asset"] for f in slw.family_refusals(list(ids), family, committing=False) if f["code"] == "FAMILY_ASSET"}
    bad: list[dict] = []
    for a in sorted(allow_family):
        if a not in req:
            bad.append({"asset": a, "code": "ACCEPT_FAMILY_NOT_REQUESTED",
                        "detail": f"--allow-family-assets names {a}, which is not in the requested list"})
        elif a not in members:
            bad.append({"asset": a, "code": "ACCEPT_FAMILY_NOT_FAMILY",
                        "detail": f"--allow-family-assets names {a}, which is not a family member (name pattern or FAMILY_ASSETS.json family_set): "
                                  "there is nothing to waive for it"})
        elif a in set(accept_excluded):
            bad.append({"asset": a, "code": "ACCEPT_FAMILY_ALSO_EXCLUDED",
                        "detail": f"{a} is named in --allow-family-assets (build it) and in --accept-excluded (drop it): choose one"})
    if bad:
        raise slw.LevelWaveRefusal(bad)


def apply_exclusions(ids: Sequence[str], findings: Sequence[Mapping[str, Any]], accept_excluded: Sequence[str]) -> tuple[list[str], list[dict]]:
    """Refuse (all at once) unless every failing id is named in --accept-excluded; an accepted id must really fail and must be in the
    list. Returns (the plan ids in the caller's order, the excluded ids with their codes)."""
    failing: dict[str, list[dict]] = {}
    for f in findings:
        failing.setdefault(f["asset"], []).append(dict(f))
    accepted = set(accept_excluded)
    bad: list[dict] = []
    for a in sorted(set(failing) - accepted):
        bad += failing[a]
    for a in sorted(accepted - set(ids)):
        bad.append({"asset": a, "code": "ACCEPT_EXCLUDED_NOT_REQUESTED", "detail": f"--accept-excluded names {a}, which is not in the list"})
    for a in sorted((accepted & set(ids)) - set(failing)):
        bad.append({"asset": a, "code": "ACCEPT_EXCLUDED_NOT_NEEDED",
                    "detail": f"{a} passes every check: a valid asset is never dropped by --accept-excluded (remove it from the list instead)"})
    if bad:
        raise slw.LevelWaveRefusal(bad)
    plan_ids = [a for a in ids if a not in accepted]
    if not plan_ids:
        raise _refuse("EMPTY_PLAN", "every requested id was excluded: nothing to build")
    excluded = [{"asset": a, "codes": sorted(f["code"] for f in failing[a])} for a in ids if a in accepted]
    return plan_ids, excluded


# ───────────────────────── plan ─────────────────────────

def make_plan(*, anchor: str, ids: Sequence[str], rows_by_id: Mapping[str, Mapping[str, Any]], local: Mapping[str, str],
              deployed: Mapping[str, str], outside_deps: Mapping[str, Sequence[str]]) -> dict:
    """Pure: image skew, the wave tool's longest-path waves, the one-run manifest. The registry order of `ids` does not matter: the
    planner's order (waves, ids sorted inside a wave) is the plan order, exactly as for the wave tool."""
    slw.check_image_skew(list(ids), local, deployed)
    deps = {a: list(rows_by_id[a].get("depends_on") or []) for a in ids}
    waves = slw.derive_waves(list(ids), {**dict(outside_deps), **deps})
    manifest, digest = slw.build_level_manifest(chart_id=anchor, plan_waves=waves, rows=dict(rows_by_id), writer_digests=local)
    plan = [a for w in waves for a in w]
    if sorted(plan) != sorted(ids):
        raise slw.LevelWaveError("the planned assets differ from the requested set (an id would be dropped silently)")
    return {"waves": waves, "plan": plan, "manifest": manifest, "manifest_digest": digest,
            "row_digests": {a: slw.registry_row_digest(rows_by_id[a]) for a in ids},
            "external_dependencies": slw.external_dependencies(ids, deps),
            "scopes": {a: rows_by_id[a]["scope"] for a in plan}, "outside": dict(outside_deps)}


def connection_budget(limit_effective: int, db: Mapping[str, Any]) -> dict:
    """Worst-case connections the ONE run holds at `limit_effective` workers, against the database's own numbers.
    main (advisory lock + run state) 1 + workers L + the staleness hook's transient connection 1 + at most L writer-owned connections
    (some ga_* writers open their own `_conn()` when not handed ctx.db_conn): 2 + 2L. The runner's documented per-run bound is
    1 + L (runner.py ~line 90, `_MAX_CONCURRENT_RUNS x (1 + _WORKER_LIMIT) <= ~33`); both are printed."""
    usable = int(db["max_connections"]) - int(db["reserved"])
    runner_doc = 1 + limit_effective
    worst = 2 + 2 * limit_effective
    headroom = usable - int(db["in_use"]) - worst
    return {"worker_limit_effective": limit_effective, "runner_documented_connections_per_run": runner_doc,
            "worst_case_connections_for_this_run": worst, "db_max_connections": int(db["max_connections"]),
            "db_superuser_reserved": int(db["reserved"]), "db_usable_connections": usable, "db_in_use_now": int(db["in_use"]),
            "headroom_after_this_run": headroom, "min_headroom_required": MIN_HEADROOM_CONNECTIONS,
            "ok": headroom >= MIN_HEADROOM_CONNECTIONS,
            "note": "in_use is a snapshot (pg_stat_activity count incl. this session); headroom is what the app, Kala and other runs "
                    "share while this run is active"}


def read_connection_numbers(connect) -> dict:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(CONNECTIONS_SQL)
        row = cur.fetchone()
        conn.rollback()
    finally:
        conn.close()
    if not row:
        raise slw.LevelWaveError("could not read max_connections / pg_stat_activity")
    return dict(row)


def sha256_json(value: object) -> str:
    return hashlib.sha256(slw.canonical_json(value).encode("utf-8")).hexdigest()


def read_cross_chart_impact(cur, *, anchor: str, plan_ids: Sequence[str], global_ids: Sequence[str]) -> dict:
    """Read-only SELECTs through `cur`. The rows a changed GLOBAL output would leave behind on OTHER charts: every transitive dependent
    (the runner's own closure) of the plan's global assets, with every lit asset_throughput row it has on a chart other than the anchor
    (the runner stales only the RUN's chart), plus lit global rows of dependents that are not in the plan. Rows of assets that this run
    rebuilds for the anchor chart are NOT impact on the anchor; their rows on other charts are. Deterministic (no timestamps)."""
    empty = {"schema": IMPACT_SCHEMA, "anchor_chart": anchor, "global_assets": sorted(global_ids), "dependents_considered": 0,
             "by_chart": {}, "total_lit_rows": 0}
    if not global_ids:
        return empty
    cur.execute(DOWNSTREAM_SET_SQL, (sorted(global_ids),))
    downstream = sorted({r["asset_id"] for r in cur.fetchall()})
    if not downstream:
        return empty
    cur.execute(gad.IMPACT_THROUGHPUT_SQL, (downstream,))
    inplan = set(plan_ids)
    by_chart: dict[str, dict[str, Any]] = {}
    for t in cur.fetchall():
        chart = None if t.get("chart_id") is None else str(t["chart_id"])
        if chart == anchor or t.get("state") not in gad.LIT_STATES:
            continue
        if chart is None and t["asset_id"] in inplan:        # a global row this run rebuilds
            continue
        e = by_chart.setdefault(chart or GLOBAL_KEY, {"lit_rows": 0, "assets": []})
        e["lit_rows"] += 1
        e["assets"].append(t["asset_id"])
    for e in by_chart.values():
        e["assets"] = sorted(e["assets"])
    return {**empty, "dependents_considered": len(downstream), "by_chart": dict(sorted(by_chart.items())),
            "total_lit_rows": sum(e["lit_rows"] for e in by_chart.values())}


def read_cross_chart_impact_via(connect, **kw) -> dict:
    conn = connect()
    try:
        impact = read_cross_chart_impact(conn.cursor(), **kw)
        conn.rollback()
        return impact
    finally:
        conn.close()


def cross_chart_lines(impact: Mapping[str, Any]) -> list[str]:
    lines = [f"CROSS-CHART IMPACT of rebuilding {len(impact['global_assets'])} global asset(s) on anchor {impact['anchor_chart']}: "
             f"{impact['dependents_considered']} dependent asset(s); lit rows left on OTHER charts: {impact['total_lit_rows']}"]
    for chart, e in impact["by_chart"].items():
        lines.append(f"  - {chart}: {e['lit_rows']} lit row(s) ({', '.join(e['assets'][:6])}{', ...' if len(e['assets']) > 6 else ''}) "
                     f"-> accept with --accept-cross-chart-impact {chart}={e['lit_rows']}")
    if not impact["by_chart"]:
        lines.append("  (no lit row on any other chart)")
    return lines


def parse_cross_chart_accepts(values: Sequence[str] | None) -> dict[str, int]:
    """`--accept-cross-chart-impact <chart uuid|global>=<lit row count>` (repeat per chart)."""
    out: dict[str, int] = {}
    for raw in values or ():
        for part in raw.split(","):
            key, sep, n = part.strip().partition("=")
            if not sep or not (n.isascii() and n.isdigit()):
                raise slw.LevelWaveError(f"--accept-cross-chart-impact {part!r}: the form is <chart uuid | global>=<number of lit rows>")
            if key != GLOBAL_KEY:
                try:
                    key = str(uuid.UUID(key))
                except ValueError:
                    raise slw.LevelWaveError(f"--accept-cross-chart-impact {part!r}: {key!r} is not a chart uuid or 'global'") from None
            if key in out:
                raise slw.LevelWaveError(f"--accept-cross-chart-impact names {key} twice")
            out[key] = int(n)
    return dict(sorted(out.items()))


def check_cross_chart_acceptance(impact: Mapping[str, Any], accepted: Mapping[str, int]) -> None:
    """Every other chart that keeps lit rows must be named WITH its exact count, as suvarna_global_asset_dispatch demands for each lit
    dependent; a flag that names nothing in the impact, or the wrong count, is refused too (a stale override is never carried)."""
    need = {c: e["lit_rows"] for c, e in impact["by_chart"].items()}
    bad = []
    missing = sorted(c for c in need if c not in accepted)
    if missing:
        bad.append({"code": "CROSS_CHART_IMPACT_NOT_ACCEPTED", "charts": {c: need[c] for c in missing},
                    "required_flags": [f"--accept-cross-chart-impact {c}={need[c]}" for c in missing],
                    "impact_lines": cross_chart_lines(impact),
                    "detail": "rebuilding global assets can change output that other charts' lit rows were derived from, and the runner stales only the "
                              "run's chart: name each chart with its lit-row count to accept that those rows are left as they are"})
    wrong = sorted(c for c in accepted if c in need and accepted[c] != need[c])
    if wrong:
        bad.append({"code": "CROSS_CHART_COUNT_MISMATCH", "charts": {c: {"accepted": accepted[c], "lit_rows_now": need[c]} for c in wrong},
                    "detail": "the accepted count differs from the live count of lit rows"})
    unmatched = sorted(c for c in accepted if c not in need)
    if unmatched:
        bad.append({"code": "ACCEPT_CROSS_CHART_UNMATCHED", "charts": unmatched,
                    "detail": "--accept-cross-chart-impact names a chart with no lit row in the impact"})
    if bad:
        raise slw.LevelWaveRefusal(bad)


def build_confirm_token(*, manifest_digest: str, ids: Sequence[str], anchor: str, image_sha: str, worker_limit: int | None,
                        accepted_excluded: Sequence[str], allow_redispatch: Sequence[str], accepted_cross_chart: Mapping[str, int] = {},
                        impact_sha256: str | None = None, job: str = "", project: str = "", region: str = "",
                        job_worker_limit: int | None = None, allow_family: Sequence[str] = ()) -> str:
    """`ASSETSET<N>_<12 hex>_FORCE_ASSET_SET_REBUILD`: a hash over the manifest digest (which carries the ids, waves, scopes, writer
    digests), the id set, the anchor chart, the deployed image sha, force=1, the worker-limit override (or its absence), the operator
    overrides (exclusions, redispatch), the cross-chart impact (its sha256 and the accepted per-chart counts) and WHERE it executes
    (--job / --project / --region) and the job's declared worker limit the connection math used, and the family override list
    (`allow_family`, sorted; the key is present ONLY when the list is non-empty, so a run without the flag keeps its token byte-for-byte).
    Never equal to a wave or global token."""
    body = {"schema": TOKEN_SCHEMA, "manifest_digest": manifest_digest, "assets": sorted(ids), "anchor_chart": anchor,
            "image_sha": image_sha, "force_execute": True, "worker_limit": worker_limit,
            "accepted_excluded": sorted(accepted_excluded), "allow_redispatch": sorted(allow_redispatch),
            "accepted_cross_chart": dict(sorted(accepted_cross_chart.items())), "impact_sha256": impact_sha256,
            "job": job, "project": project, "region": region, "job_worker_limit": job_worker_limit}
    if allow_family:
        body["allow_family"] = sorted(allow_family)
    h = hashlib.sha256(slw.canonical_json(body).encode("utf-8")).hexdigest()
    return f"ASSETSET{len(ids)}_{h[:12].upper()}_FORCE_ASSET_SET_REBUILD"


def build_triggered_by(anchor: str, manifest_digest: str) -> str:
    value = f"{TRIGGERED_BY_PREFIX}anchor_chart={anchor};manifest_sha256={manifest_digest[:16]}"
    if len(value) > gad.TRIGGERED_BY_MAX_CHARS or not _TRIGGERED_BY_RE.fullmatch(value):
        raise slw.LevelWaveError(f"triggered_by {value!r} is malformed or too long")
    return value


# ───────────────────────── the transaction ─────────────────────────

def insert_asset_set_run(connect, *, anchor: str, manifest: Mapping[str, Any], digest: str, row_digests: Mapping[str, str],
                         external: Mapping[str, Sequence[str]], triggered_by: str, allow_redispatch: Sequence[str], token: str,
                         confirm: str | None, commit: bool, impact_reader: Callable[[Any], dict] | None = None,
                         impact_sha256: str | None = None, on_commit=None, meta: Mapping[str, Any] | None = None) -> dict:
    """ONE transaction: the anchor chart's advisory lock (the wave's own key, so wave, global dispatch and this tool serialise);
    ANCHOR_CHART_BUSY; GLOBAL_LOCK_HELD (another active run holds a global asset: it would defer or defer us); CONFLICTING_ACTIVE_RUN
    (an active run on ANY chart containing one of the ids); ALREADY_DISPATCHED; registry rows re-read and compared; outside dependencies
    lit+fresh; INSERT build_runs + build_run_assets; ROLLBACK (plan) or COMMIT (exact token only)."""
    plan = [a for wave in manifest["waves"] for a in wave]
    if commit and confirm != token:
        raise _refuse("CONFIRM_TOKEN_MISMATCH", f"--commit requires --confirm {token}", expected=token)
    has_global = any(a["scope"] == "global" for a in manifest["assets"])
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (slw._lock_key(anchor),))
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", ("suvarna-asset-set-dispatch",))
        cur.execute(gad.ANCHOR_ACTIVE_SQL, (anchor,))
        active = cur.fetchall()
        if active:
            raise _refuse("ANCHOR_CHART_BUSY", f"the anchor chart has planned/running/paused build run(s): {active}",
                          runs=[dict(r) for r in active])
        if has_global:
            cur.execute(GLOBAL_LOCK_RUNS_SQL)
            held = [dict(r) for r in cur.fetchall()]
            if held:
                raise _refuse("GLOBAL_LOCK_HELD", "an active run holds a global asset (the runner's single global-assets lock would "
                              f"defer one of the two runs): {held}", runs=held)
        cur.execute(gad.CONFLICT_RUNS_SQL, (sorted(plan),))
        conflicts = [dict(r) for r in cur.fetchall()]
        if conflicts:
            raise _refuse("CONFLICTING_ACTIVE_RUN", f"an active run (any chart) contains an asset of this list: {conflicts}", runs=conflicts)
        cur.execute(PRIOR_DISPATCH_SQL, (len(TRIGGERED_BY_PREFIX), TRIGGERED_BY_PREFIX))
        prior = [dict(r) for r in cur.fetchall()]
        unnamed = [str(r["id"]) for r in prior if str(r["id"]) not in set(allow_redispatch)]
        if unnamed:
            raise _refuse("ALREADY_DISPATCHED", f"a prior run of this tool exists: {unnamed}. A second dispatch is forbidden unless "
                          "every prior run is named with --allow-redispatch <run_id>", runs=unnamed)
        cur.execute(ROWS_SQL, (plan,))
        slw.check_registry_unchanged(row_digests, [dict(r) for r in cur.fetchall()])
        slw.check_external_dependencies(cur, anchor, external)
        if impact_reader is not None:
            now_sha = sha256_json(impact_reader(cur))
            if now_sha != impact_sha256:
                raise _refuse("IMPACT_CHANGED", "the cross-chart impact changed since the plan was made: plan again",
                              planned=impact_sha256, now=now_sha)
        run_id = str(uuid.uuid4())
        cur.execute(gad.INSERT_RUN_SQL, (run_id, anchor, manifest["scope_target"], json.dumps(plan), json.dumps(manifest), digest,
                                         triggered_by))
        for position, asset_id in enumerate(plan):
            cur.execute(gad.INSERT_RUN_ASSET_SQL, (run_id, asset_id, position))
        receipt = {"run_id": run_id, "chart_id": anchor, "assets": plan, "manifest_digest": digest, "committed": bool(commit),
                   "confirm_token": token, "triggered_by": triggered_by}
        receipt.update(dict(meta or {}))
        if commit:
            try:
                conn.commit()
            except Exception as exc:  # noqa: BLE001 -- the outcome of a failed COMMIT is unknown, never "not committed"
                raise slw.CommitOutcomeUnknown(run_id, anchor, exc) from exc
            if on_commit is not None:
                on_commit(receipt)
        else:
            conn.rollback()
        return receipt
    except slw.CommitOutcomeUnknown:
        raise
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


# ───────────────────────── dispatch (per-execution env only) ─────────────────────────

def dispatch_command(*, run_id: str, project: str, region: str, job: str, worker_limit: int | None) -> list[str]:
    """`gcloud run jobs execute` with the per-EXECUTION override `--update-env-vars=NIRMANA_FORCE_EXECUTE=1[,ORCHESTRATOR_WORKER_LIMIT=n]`.
    The job resource is not modified; both variables exist for this one execution only."""
    env = f"{FORCE_ENV_VAR}=1" + (f",{WORKER_LIMIT_ENV_VAR}={int(worker_limit)}" if worker_limit is not None else "")
    return ["gcloud", "run", "jobs", "execute", job, f"--project={project}", f"--region={region}", f"--args=--run-id,{run_id}",
            f"--update-env-vars={env}", "--async", "--format=value(metadata.name)"]


def dispatch_run(*, run_id: str, project: str, region: str, job: str, worker_limit: int | None, run_command=None,
                 timeout: float = slw.GCLOUD_TIMEOUT_SECONDS, authorised: bool = False) -> str:
    """Same contract as slw.dispatch_run_with_timeout (timeout, no stdin, no prompts, runner injected, real process only when
    `authorised`), with the extra per-execution variable."""
    if run_command is None:
        if not authorised:
            raise RuntimeError("dispatch refused: no runner injected and the call is not the authorised --commit path")
        run_command = lambda *a, **k: subprocess.run(*a, **k)  # noqa: E731 -- resolved at call time
    try:
        result = run_command(dispatch_command(run_id=run_id, project=project, region=region, job=job, worker_limit=worker_limit),
                             capture_output=True, check=False, text=True, timeout=timeout, stdin=subprocess.DEVNULL,
                             env={**os.environ, "CLOUDSDK_CORE_DISABLE_PROMPTS": "1"})
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"gcloud timed out after {timeout}s: dispatch outcome unknown") from exc
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "unknown gcloud error").strip()[:1000])
    execution = result.stdout.strip()
    if not execution:
        raise RuntimeError("gcloud returned no execution name")
    return execution


# ───────────────────────── receipt ─────────────────────────

def new_receipt(**fields: Any) -> dict:
    doc = {"schema": RECEIPT_SCHEMA, "run_id": None, "committed": False, "committed_at": None, "execution_name": None,
           "verification": None}
    doc.update(fields)
    return doc


def validate_receipt(doc: Any) -> None:
    need = ("schema", "run_id", "committed", "anchor_chart", "assets", "manifest_digest", "confirm_token", "triggered_by", "worker_limit")
    if not isinstance(doc, dict) or doc.get("schema") != RECEIPT_SCHEMA or any(k not in doc for k in need):
        raise slw.LevelWaveError("not a receipt of this tool")


def check_receipt_overwrite(path: Path, doc: Mapping[str, Any]) -> None:
    if not path.exists():
        return
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
        validate_receipt(old)
    except (OSError, ValueError, slw.LevelWaveError):
        raise _refuse("RECEIPT_PATH_INVALID", f"{path} exists and is not a receipt of this tool: not overwritten") from None
    same = old["anchor_chart"] == doc["anchor_chart"]
    continues = (not old["committed"]) or (old["run_id"] is not None and old["run_id"] == doc["run_id"])
    if not (same and continues):
        raise _refuse("RECEIPT_PATH_INVALID", f"{path} already holds a committed receipt of another run: not overwritten")


def write_receipt(path: Path, doc: dict) -> None:
    validate_receipt(doc)
    check_receipt_overwrite(path, doc)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    try:
        fd_ = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd_, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(doc, sort_keys=True, indent=1, default=str) + "\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ───────────────────────── verification ─────────────────────────

def verify_run(connect, run_id: str, plan: Sequence[str], wait: Mapping[str, Any]) -> dict:
    """Read the run and every asset. forced_effective is True only when the run ended and every asset's disposition is 'build';
    False when any asset ended skip_no_delta; None when it can not be established. `complete` needs run state 'completed', every asset
    present, and every asset's state in the runner's success vocabulary. Never a guess."""
    eff = slw.forced_effect(connect, run_id)
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(slw.RUN_ASSETS_SQL, (run_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.rollback()
    finally:
        conn.close()
    states = {r["asset_id"]: r.get("state") for r in rows}
    # build_run_assets.state is written 'complete' for every terminal outcome (runner.py F-01); asset_throughput.state is the computed truth
    bad_throughput = sorted(r["asset_id"] for r in rows if r.get("throughput_state") not in slw.GOOD_THROUGHPUT_STATES)
    errors = {r["asset_id"]: r.get("error") for r in rows if r.get("error")}
    missing = sorted(set(plan) - set(states))
    not_done = sorted(a for a, s in states.items() if s != "complete")
    run_state = eff["run_state"]
    complete = run_state == "completed" and not missing and not not_done and not bad_throughput
    codes: list[str] = []
    if bad_throughput:
        codes.append("ASSET_THROUGHPUT_NOT_LIT")
    if eff["forced_effective"] is False:
        codes.append("FORCE_DID_NOT_TAKE_EFFECT")
    if not complete:
        codes.append("RUN_NOT_COMPLETE")
    elif eff["forced_effective"] is not True:
        codes.append("FORCE_EFFECT_NOT_ESTABLISHED")
    verdict = "PASS" if not codes else codes
    return {"verdict": verdict, "codes": codes, "run_state": run_state, "wait": wait.get("state"), "complete": complete,
            "assets_total": len(plan), "assets_complete": sum(1 for s in states.values() if s == "complete"),
            "assets_not_complete": not_done, "assets_missing": missing, "assets_throughput_not_lit": bad_throughput, "asset_errors": errors,
            "forced_effect": eff, "exit_code": EXIT_OK if not codes else (EXIT_FORCE_NOT_EFFECTIVE if "FORCE_DID_NOT_TAKE_EFFECT" in codes
                                                                       else EXIT_VERIFY_FAILED)}


# ───────────────────────── command line ─────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="suvarna_asset_set_dispatch.py", formatter_class=argparse.RawDescriptionHelpFormatter,
        description="ONE forced multi-asset (L0+L1+L2) asset_set run over an explicit id list. Reads DATABASE_URL from the environment; "
                    "never reads credential files; plan mode only reads the live job image (read-only gcloud describe).",
        epilog="Default is a PLAN: INSERT build_runs + build_run_assets, ROLLBACK, print the waves, the connection math and the confirm "
               "token. --commit --confirm <token> inserts, then executes the Cloud Run job ONCE with NIRMANA_FORCE_EXECUTE=1 "
               "(and ORCHESTRATOR_WORKER_LIMIT=<n> with --worker-limit) set on that execution only. Without --wait it returns the run id "
               "(monitor it, then --verify-run). Exit: 0 ok | 1 DATABASE_URL missing | 2 bad input | 3 dispatch failed | 4 refused | "
               "6 unexpected | 7 interrupted | 8 force did not take effect | 10 not complete / not verified.")
    p.add_argument("--assets", action="append", metavar="LIST", help="comma list of asset ids (repeatable)")
    p.add_argument("--assets-file", metavar="FILE", help="file of asset ids (commas / spaces / newlines; # comments); <= 64 KiB")
    p.add_argument("--accept-excluded", action="append", metavar="LIST",
                   help="ids that FAIL validation and are dropped on purpose; any other failing id refuses the run")
    p.add_argument("--allow-family-assets", action="append", metavar="LIST",
                   help="ids of Pravaha-family assets (name pattern or FAMILY_ASSETS.json family_set) that are BUILT in this run: waives FAMILY_ASSET and "
                        "SPLITS_FAMILY for exactly these ids and nothing else (NOT_ACTIVE, NO_WRITER, SERVICE_ASSET, PROTECTED_ASSET, layer ... still "
                        "refuse); every name must be in the request; bound into the confirm token, the receipt and the log (`family-override: <ids>`)")
    p.add_argument("--accept-cross-chart-impact", action="append", metavar="CHART=N",
                   help="accept that the lit rows of dependents on OTHER charts (<chart uuid|global>=<count the plan printed>) are left as they are "
                        "after the global assets are rebuilt; one per chart; required when the plan has global assets with such rows; bound into the token")
    p.add_argument("--allowed-layers", default=",".join(DEFAULT_ALLOWED_LAYERS), help="registry layers a plan may contain")
    p.add_argument("--anchor-chart", required=True, help="a REAL chart id carrying the run (e.g. 482012f1-...)")
    p.add_argument("--receipt", required=True, help="receipt JSON path (outside the repo unless --receipt-in-repo)")
    p.add_argument("--receipt-in-repo", action="store_true")
    p.add_argument("--deployed-sha", help="OPTIONAL cross-check: the commit whose committed writer digests are the deployed image's "
                   "(default: the commit the tool READS from the live job image); if given and not the live image: JOB_SHA_MISMATCH")
    p.add_argument("--deployed-job-sha", help="OPTIONAL cross-check only: the tool READS the live job image itself (gcloud run jobs "
                   "describe, read-only) at plan time and again right before the INSERT and the execute; a value that differs from "
                   "the live image refuses (LIVE_JOB_IMAGE_DIFFERS)")
    p.add_argument("--worker-limit", type=int, default=None, metavar="N",
                   help=f"set ORCHESTRATOR_WORKER_LIMIT={WORKER_LIMIT_MIN}..{WORKER_LIMIT_MAX} on THIS execution only (default unset = the job's "
                        "own value); bound into the confirm token")
    p.add_argument("--job-worker-limit", type=int, default=None, metavar="N",
                   help="the job's CURRENT ORCHESTRATOR_WORKER_LIMIT (read by the operator), used for the connection math when "
                        f"--worker-limit is unset (default {RUNNER_DEFAULT_WORKER_LIMIT}, the runner's code default)")
    p.add_argument("--repo", default=str(slw.REPO_ROOT))
    p.add_argument("--family-ref", default="origin/main")
    p.add_argument("--commit", action="store_true")
    p.add_argument("--confirm", help="required with --commit: the token the plan printed")
    p.add_argument("--allow-redispatch", action="append", metavar="RUN_ID", help="name a prior run of this tool")
    p.add_argument("--wait", action="store_true", help="after dispatch poll until the run ends and verify it (otherwise return the run id)")
    p.add_argument("--verify-run", metavar="RUN_ID", help="verify an existing run of this tool from its receipt (no insert, no dispatch)")
    p.add_argument("--dispatch-existing", metavar="RUN_ID",
                   help="RECOVERY: execute the run this tool already committed as 'planned' but never executed (crash between COMMIT and execute). "
                        "Re-plans with the receipt's inputs, requires the SAME manifest digest and token (--confirm), the run still 'planned', the "
                        "receipt without an execution; needs --commit")
    p.add_argument("--terminalise-run", metavar="RUN_ID",
                   help="RECOVERY: cancel a committed run that is still 'planned' and never executed (plan mode prints the confirm token; "
                        "--commit --confirm <token> asserts that no execution of it exists: check `gcloud run jobs executions list` first)")
    p.add_argument("--poll-seconds", type=float, default=30.0)
    p.add_argument("--run-timeout-seconds", type=float, default=8 * 3600.0)
    p.add_argument("--project", default="madhav-astrology")
    p.add_argument("--region", default="asia-south1")
    p.add_argument("--job", default="brahma-build-pipeline-job")
    return p


def _recovery_run_hint(args) -> str | None:
    """The run a recovery / verify mode is about (for honest warnings: such a mode commits no NEW run, but a run exists)."""
    return args.dispatch_existing or args.terminalise_run or args.verify_run or None


def _record_unknown_commit(holder: dict, run_id: str) -> str:
    """The COMMIT outcome is unknown: put the run id on disk (committed 'unknown') so the recovery modes can find the run; the database row
    (chart + triggered_by + manifest digest + state 'planned') is what binds it. Returns a note for the operator."""
    rec, path = holder.get("receipt"), holder.get("receipt_path")
    if rec is None or path is None:
        return "no receipt was open: find the run by `build_runs WHERE left(triggered_by,19)='asset-set-dispatch:'` (read-only)"
    rec.update(run_id=run_id, committed="unknown")
    try:
        write_receipt(path, rec)
    except Exception as exc:  # noqa: BLE001
        return f"the receipt could not be updated ({type(exc).__name__}: {exc}); the run id is {run_id}"
    return f"the receipt {path} now names run {run_id} (committed 'unknown'): query its state read-only, then --terminalise-run / --dispatch-existing"


def _acquire_receipt_lock(receipt_path: Path, holder: dict) -> None:
    """One mutating process per receipt (commit and the recovery modes): an exclusive non-blocking flock on <receipt>.lock."""
    try:
        import fcntl  # noqa: PLC0415
    except ImportError:
        return
    fh = open(str(receipt_path) + ".lock", "a")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        raise _refuse("RECEIPT_LOCKED", f"another process holds {receipt_path}.lock: one mutating run of this tool per receipt") from None
    holder["lock"] = fh


def run_cli(args: argparse.Namespace, *, connect, git=slw._git, out=None, sleep=time.sleep, monotonic=time.monotonic, dispatch=None,
            now: Callable[[], datetime] | None = None, live_reader=None) -> int:
    out = out or sys.stdout
    now = now or (lambda: datetime.now(timezone.utc))
    committed: list[dict] = []
    holder: dict = {}
    try:
        return _run_cli(args, connect=connect, git=git, out=out, sleep=sleep, monotonic=monotonic, dispatch=dispatch, now=now,
                        committed=committed, holder=holder, live_reader=live_reader or slw.live_reader_for(args))
    except slw.LevelWaveRefusal as exc:
        _emit(out, "refused", refused=True, refusals=exc.refusals, committed_runs=committed)
        return slw.REFUSAL_EXIT_CODE
    except slw.LevelWaveError as exc:
        _emit(out, "error", error=str(exc), committed_runs=committed)
        return slw.EXIT_BAD_INPUT
    except slw.CommitOutcomeUnknown as exc:
        note = _record_unknown_commit(holder, exc.run_id)
        _emit(out, "error", unexpected=True, commit_outcome_unknown=True, run_id=exc.run_id, chart_id=exc.chart_id, error=exc.detail,
              committed_runs=committed, warning=exc.detail + " " + note)
        return slw.EXIT_UNEXPECTED
    except gad.ReceiptNotWritten as exc:
        _emit(out, "run_committed_receipt_not_written", unexpected=True, run_id=exc.run_id, chart_id=exc.chart_id, error=exc.detail,
              terminalised=exc.terminalised, committed_runs=committed, warning=exc.detail)
        return slw.EXIT_UNEXPECTED
    except KeyboardInterrupt:
        hint = _recovery_run_hint(args)
        base = (slw._interrupt_warning(committed, args.anchor_chart) if (committed or not hint) else
                f"interrupted in a recovery / verify mode for run {hint}: no NEW run was committed, but that run exists and an execution may "
                "have started")
        _emit(out, "interrupted", interrupted=True, committed_runs=committed,
              warning=base + " Check its state and the executions list first; verify it with --verify-run <run_id>; never dispatch again blindly.")
        return slw.EXIT_INTERRUPTED
    except Exception as exc:  # noqa: BLE001 -- never an escaped traceback: the operator must see the run id
        hint = _recovery_run_hint(args)
        _emit(out, "error", unexpected=True, error=f"{type(exc).__name__}: {exc}", committed_runs=committed,
              warning=("the run listed in committed_runs exists and may be planned/running: find it by run_id before anything else"
                       if committed else (f"recovery / verify mode for run {hint}: no NEW run was committed, but that run exists: read its state "
                                          "(build_runs) and the executions list before any retry" if hint else "no run was committed")))
        return slw.EXIT_UNEXPECTED
    finally:
        fh = holder.get("lock")
        if fh is not None:
            fh.close()


def _effective_limit(args) -> int:
    if args.worker_limit is not None:
        return int(args.worker_limit)
    return int(args.job_worker_limit) if args.job_worker_limit is not None else RUNNER_DEFAULT_WORKER_LIMIT


def _validate_numbers(args) -> None:
    if args.job_worker_limit is not None and not (WORKER_LIMIT_MIN <= args.job_worker_limit <= WORKER_LIMIT_MAX):
        raise _refuse("WORKER_LIMIT_INVALID", f"--job-worker-limit must be {WORKER_LIMIT_MIN}..{WORKER_LIMIT_MAX} (got {args.job_worker_limit})")
    if not (args.poll_seconds > 0 and args.run_timeout_seconds > 0):
        raise slw.LevelWaveError("--poll-seconds and --run-timeout-seconds must be > 0")


def _parse_run_id(value: str, flag: str) -> str:
    try:
        return str(uuid.UUID(str(value).strip()))
    except ValueError:
        raise slw.LevelWaveError(f"{flag} {value!r} is not a run id (uuid)") from None


def _read_run_row(connect, run_id: str) -> dict | None:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(gad.RUN_ROW_SQL, (run_id,))
        found = cur.fetchone()
        conn.rollback()
    finally:
        conn.close()
    return dict(found) if found else None


def _read_protected(connect, anchor: str, ids: Sequence[str]) -> list[str]:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(PROTECTED_SQL, (anchor, list(ids)))
        out = sorted(r["asset_id"] for r in cur.fetchall())
        conn.rollback()
        return out
    finally:
        conn.close()


def _load_committed_receipt(receipt_path: Path, anchor: str, run_id: str) -> dict:
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise slw.LevelWaveError(f"this mode needs the receipt of the run: {receipt_path}: {exc}") from None
    validate_receipt(receipt)
    # A receipt written before the COMMIT outcome was known (committed False / "unknown", run_id None or the unknown-commit run id) is accepted:
    # the REAL binding is _check_run_is_ours (chart + triggered_by + manifest digest + state 'planned' read from the database).
    if not (receipt["run_id"] in (None, run_id) and receipt["anchor_chart"] == anchor):
        raise _refuse("RECEIPT_RUN_MISMATCH", "the receipt is not the receipt of this run and anchor chart")
    return receipt


def _check_run_is_ours(connect, run_id: str, anchor: str, receipt: Mapping[str, Any]) -> dict:
    found = _read_run_row(connect, run_id)
    if (not found or str(found["chart_id"]) != anchor or found["triggered_by"] != receipt["triggered_by"]
            or found["plan_manifest_digest"] != receipt["manifest_digest"]):
        raise _refuse("RECEIPT_RUN_MISMATCH", f"build_runs {run_id} is not this tool's run for the receipt (chart, triggered_by or digest differ)")
    return found


def _run_cli(args, *, connect, git, out, sleep, monotonic, dispatch, now, committed, holder, live_reader) -> int:
    emit = lambda event, **f: _emit(out, event, **f)  # noqa: E731
    anchor = gad.validate_anchor_format(args.anchor_chart)
    receipt_path = gad.check_receipt_path(args.receipt, args.repo, args.receipt_in_repo)
    commit = bool(args.commit)
    worker_limit = validate_worker_limit(args.worker_limit)
    _validate_numbers(args)
    if sum(1 for m in (args.verify_run, args.dispatch_existing, args.terminalise_run) if m) > 1:
        raise slw.LevelWaveError("--verify-run, --dispatch-existing and --terminalise-run are separate modes: give one")
    if args.verify_run:
        if commit:
            raise slw.LevelWaveError("--verify-run is read-only: do not combine it with --commit")
        return _verify_run_mode(args, anchor=anchor, receipt_path=receipt_path, connect=connect, out=out, sleep=sleep, monotonic=monotonic,
                                now=now)
    if commit:
        _acquire_receipt_lock(receipt_path, holder)
    if args.terminalise_run:
        return _terminalise_mode(args, anchor=anchor, receipt_path=receipt_path, connect=connect, out=out, commit=commit)
    old = None
    if args.dispatch_existing:
        if not commit:
            raise slw.LevelWaveError("--dispatch-existing executes a run: it needs --commit --confirm <the receipt's token>")
        if args.assets or args.assets_file or args.accept_excluded or args.accept_cross_chart_impact or args.allow_family_assets:
            raise slw.LevelWaveError("--dispatch-existing takes the ids and acceptances from the receipt: do not pass --assets / --assets-file / "
                                     "--accept-excluded / --accept-cross-chart-impact / --allow-family-assets (--allow-redispatch <RUN_ID> here means: the executions "
                                     "list was checked and no execution of this run exists)")
        run_uuid = _parse_run_id(args.dispatch_existing, "--dispatch-existing")
        gad.parse_redispatch(args.allow_redispatch)          # validated up front (it is the "I checked the executions list" override)
        old = _load_committed_receipt(receipt_path, anchor, run_uuid)
        inputs = old.get("inputs")
        if not isinstance(inputs, dict):
            raise slw.LevelWaveError("the receipt carries no `inputs`: it was not written by this version of the tool")
        if old.get("execution_name"):
            raise _refuse("ALREADY_EXECUTED_PER_RECEIPT", f"the receipt already records execution {old['execution_name']}: nothing to dispatch")
        ids = list(inputs["requested"])
        accept_excluded = list(inputs["accept_excluded"])
        accepted_cross = {k: int(v) for k, v in inputs["accept_cross_chart"].items()}
        allow_redispatch = list(inputs["allow_redispatch"])
        allow_family = sorted(inputs.get("allow_family") or [])        # absent in receipts without the override
    else:
        allow_redispatch = gad.parse_redispatch(args.allow_redispatch)
        ids = parse_asset_ids(args.assets, args.assets_file)
        accept_excluded = parse_id_list(args.accept_excluded, "--accept-excluded")
        accepted_cross = parse_cross_chart_accepts(args.accept_cross_chart_impact)
        allow_family = parse_id_list(args.allow_family_assets, "--allow-family-assets")
    allowed_layers = tuple(x for x in args.allowed_layers.split(",") if x)

    # 1. the wave's gates: family ref, job sha binding, force support, re-read of the job sha
    ref_status = slw.family_ref_status(args.repo, args.family_ref, git=git)
    family = slw.load_family_info(args.repo, args.family_ref, git=git)
    ref_refusals = slw.family_ref_refusals(ref_status, committing=commit)
    if family.get("state") == "absent" and commit:
        ref_refusals.append({"code": "FAMILY_FILE_MISSING", "detail": f"{slw.FAMILY_FILE_REL} is not on the family ref: a real dispatch needs it"})
    if ref_refusals:
        raise slw.LevelWaveRefusal(ref_refusals)
    live = live_reader()                       # READ by the tool, never asserted by hand (the flags are only cross-checks)
    binding = slw.bind_live_job_sha(args.repo, live_sha=live, asserted_job_sha=args.deployed_job_sha, deployed_sha=args.deployed_sha, git=git)
    pinned = binding["deployed_job_sha"]
    slw.check_image_supports_force(args.repo, pinned, git=git)
    local = slw.load_local_writer_digests(args.repo)
    deployed = slw.load_deployed_writer_digests(repo=args.repo, sha=binding["inventory_sha"], git=git)
    frozen = slw._load_frozen_dispatcher() if commit else None        # before any insert: a load failure strands nothing

    # 2. anchor chart, registry rows, per-id validation (nothing is dropped unless named in --accept-excluded)
    gad.check_anchor_exists(connect, anchor)
    rows = _read_rows(connect, ids)
    validate_allow_family(ids, allow_family, family, accept_excluded)
    findings = classify_assets(ids, rows, family, allowed_layers=allowed_layers, protected=_read_protected(connect, anchor, ids),
                               allow_family=allow_family)
    if allow_family:
        override_line = "family-override: " + ",".join(allow_family)
        emit("family_override", ids=allow_family, waives=list(FAMILY_WAIVED_CODES), line=override_line)
        print(override_line, file=sys.stderr)
    plan_ids, excluded = apply_exclusions(ids, findings, accept_excluded)
    rows_by_id = {r["asset_id"]: dict(r) for r in rows if r["asset_id"] in set(plan_ids)}
    plan_rows = [rows_by_id[a] for a in plan_ids]
    outside = slw.read_dependency_closure(connect, plan_ids, plan_rows)
    plan = make_plan(anchor=anchor, ids=plan_ids, rows_by_id=rows_by_id, local=local, deployed=deployed, outside_deps=outside)
    slw.precheck_external(connect, anchor, plan["external_dependencies"])
    global_assets = sorted(a for a, sc in plan["scopes"].items() if sc == "global")

    # 3. cross-chart impact of the global assets (every other chart's lit rows): must be accepted by name and count
    impact_kw = {"anchor": anchor, "plan_ids": list(plan["plan"]), "global_ids": global_assets}
    impact = read_cross_chart_impact_via(connect, **impact_kw)
    impact_sha = sha256_json(impact)
    check_cross_chart_acceptance(impact, accepted_cross)

    # 4. connection budget (read-only) at the limit this execution will run with
    limit_eff = _effective_limit(args)
    budget = connection_budget(limit_eff, read_connection_numbers(connect))
    budget["worker_limit_source"] = ("override on this execution" if worker_limit is not None else
                                     ("--job-worker-limit (operator-supplied job value)" if args.job_worker_limit is not None
                                      else f"runner code default {RUNNER_DEFAULT_WORKER_LIMIT} (job value not supplied: pass --job-worker-limit)"))
    if not budget["ok"]:
        raise _refuse("CONNECTION_HEADROOM_LOW", f"at worker limit {limit_eff} this run needs up to {budget['worst_case_connections_for_this_run']} "
                      f"connections and would leave {budget['headroom_after_this_run']} (< {MIN_HEADROOM_CONNECTIONS}); use a lower --worker-limit",
                      connection_budget=budget)

    token = build_confirm_token(manifest_digest=plan["manifest_digest"], ids=plan["plan"], anchor=anchor, image_sha=pinned,
                                worker_limit=worker_limit, accepted_excluded=[e["asset"] for e in excluded], allow_redispatch=allow_redispatch,
                                accepted_cross_chart=accepted_cross, impact_sha256=impact_sha, job=args.job, project=args.project,
                                region=args.region, job_worker_limit=args.job_worker_limit, allow_family=allow_family)
    triggered_by = build_triggered_by(anchor, plan["manifest_digest"])
    estimate = slw.estimate_runtime(plan["waves"], {a: rows_by_id[a] for a in plan["plan"]})
    deps_all = {**plan["outside"], **{a: rows_by_id[a].get("depends_on") or [] for a in plan["plan"]}}
    meta = {"deployed_job_sha": pinned, "inventory_sha": binding["inventory_sha"], "force_execute": True, "worker_limit": worker_limit}
    if allow_family:
        meta["family_override"] = list(allow_family)
    cmd_preview = dispatch_command(run_id="<run_id>", project=args.project, region=args.region, job=args.job, worker_limit=worker_limit)
    inputs = {"requested": list(ids), "accept_excluded": list(accept_excluded), "accept_cross_chart": dict(accepted_cross),
              "allow_redispatch": list(allow_redispatch)}
    if allow_family:
        inputs["allow_family"] = list(allow_family)
    summary = {
        "anchor_chart": anchor, "anchor_is_canonical": anchor == gad.CANONICAL_CHART_ID, "assets": plan["plan"],
        "asset_count": len(plan["plan"]), "layer_counts": _layer_counts(plan["plan"], rows_by_id), "global_assets": global_assets,
        "excluded_accepted": excluded, "waves": plan["waves"], "wave_count": len(plan["waves"]),
        "wave_widths": [len(w) for w in plan["waves"]], "external_dependencies": plan["external_dependencies"],
        "out_of_set_intermediates_at_risk": slw.at_risk_intermediates(plan["plan"], deps_all),
        "cross_chart_impact": impact, "cross_chart_impact_lines": cross_chart_lines(impact), "impact_sha256": impact_sha,
        "cross_chart_impact_accepted": accepted_cross,
        "manifest_digest": plan["manifest_digest"], "triggered_by": triggered_by, "scope": "asset_set", "action": "rebuild",
        "force_execute": True, "worker_limit_override": worker_limit, "connection_budget": budget,
        "execution_env_override": {FORCE_ENV_VAR: "1", **({WORKER_LIMIT_ENV_VAR: str(worker_limit)} if worker_limit is not None else {})},
        "target": {"job": args.job, "project": args.project, "region": args.region},
        "job_image_check": {"deployed_job_sha": pinned, "inventory_sha": binding["inventory_sha"], "binding": "verified",
                            "force_markers": [m[2] for m in slw._FORCE_MARKERS], "image_skew": "no skew for the planned assets",
                            "family_ref": ref_status},
        "locks": {"anchor_chart": f"held while the run is planned/running/paused: no other build of {anchor}",
                  "global_assets": ("taken (the plan holds global assets): another run containing a global asset defers while this one runs"
                                    if global_assets else "not taken (no global asset in the plan)")},
        "runtime_estimate": estimate, "dispatch_command_preview": cmd_preview, "confirm_token": token, "committed": False,
        "receipt_path": str(receipt_path), "committed_runs": committed,
        "runbook_gates_not_in_tool": ["no deploy workflow open", "watchdog-reaper paused", "backup / PITR point recorded before the run",
                                      "live job image sha: READ by the tool (gcloud run jobs describe) at plan, before the INSERT and before the execute; nothing is asserted by hand"],
    }
    if allow_family:
        summary["family_override"] = {"ids": list(allow_family), "waives": list(FAMILY_WAIVED_CODES), "line": override_line,
                                      "note": "bound into the confirm token and the receipt; every other refusal still applies to these ids"}
    if commit and args.confirm != token:
        raise _refuse("CONFIRM_TOKEN_MISMATCH", f"--commit requires --confirm {token}", expected=token)

    if old is not None:                                   # --dispatch-existing: the SAME plan, the SAME token, no INSERT
        return _dispatch_existing(args, old=old, run_id=run_uuid, committed=committed, token=token, plan=plan, anchor=anchor, pinned=pinned, worker_limit=worker_limit, meta=meta,
                                  summary=summary, receipt_path=receipt_path, connect=connect, frozen=frozen, git=git, dispatch=dispatch,
                                  out=out, sleep=sleep, monotonic=monotonic, now=now, emit=emit, live_reader=live_reader)

    receipt = new_receipt(anchor_chart=anchor, assets=plan["plan"], waves=plan["waves"], manifest_digest=plan["manifest_digest"],
                          confirm_token=token, triggered_by=triggered_by, worker_limit=worker_limit, image_sha=pinned,
                          inventory_sha=binding["inventory_sha"], excluded_accepted=excluded, connection_budget=budget,
                          cross_chart_impact=impact, impact_sha256=impact_sha, inputs=inputs,
                          target={"job": args.job, "project": args.project, "region": args.region}, planned_at=_utc_iso(now),
                          **({"family_override": list(allow_family)} if allow_family else {}))
    check_receipt_overwrite(receipt_path, receipt)
    holder.update(receipt=receipt, receipt_path=receipt_path)
    if commit:
        try:
            write_receipt(receipt_path, receipt)
        except OSError as exc:
            raise _refuse("RECEIPT_PATH_INVALID", f"the receipt {receipt_path} cannot be written ({type(exc).__name__}: {exc}); "
                          "nothing was inserted") from None

    def on_commit(r):
        rec = {"run_id": r["run_id"], "anchor_chart": anchor, "manifest_digest": plan["manifest_digest"], **meta}
        committed.append(rec)
        receipt.update(run_id=r["run_id"], committed=True, committed_at=_utc_iso(now))
        try:
            write_receipt(receipt_path, receipt)
        except Exception as exc:  # noqa: BLE001 -- the run is COMMITTED: never leave it 'planned' (it would block the anchor chart)
            term = gad.terminalise_planned_run(connect, r["run_id"], anchor, f"run committed, receipt not written: {exc}", frozen)
            raise gad.ReceiptNotWritten(r["run_id"], anchor, exc, term) from exc
        emit("run_committed", **rec)

    if commit:
        slw.recheck_live_job_sha(live_reader, pinned_job_sha=pinned)     # immediately before the INSERT / COMMIT
    run = insert_asset_set_run(connect, anchor=anchor, manifest=plan["manifest"], digest=plan["manifest_digest"],
                               row_digests=plan["row_digests"], external=plan["external_dependencies"], triggered_by=triggered_by,
                               allow_redispatch=allow_redispatch, token=token, confirm=args.confirm if commit else None, commit=commit,
                               impact_reader=lambda cur: read_cross_chart_impact(cur, **impact_kw), impact_sha256=impact_sha,
                               on_commit=on_commit if commit else None, meta=meta)
    summary["insert"] = run
    if not commit:
        write_receipt(receipt_path, receipt)
        emit("summary", **summary)
        return EXIT_OK
    summary["committed"] = True
    return _dispatch_stage(run["run_id"], args=args, anchor=anchor, pinned=pinned, worker_limit=worker_limit, meta=meta, receipt=receipt,
                           receipt_path=receipt_path, summary=summary, plan_ids=plan["plan"], connect=connect, frozen=frozen, git=git,
                           dispatch=dispatch, out=out, sleep=sleep, monotonic=monotonic, now=now, emit=emit, live_reader=live_reader)


def _dispatch_stage(run_id, *, args, anchor, pinned, worker_limit, meta, receipt, receipt_path, summary, plan_ids, connect, frozen, git,
                    dispatch, out, sleep, monotonic, now, emit, live_reader) -> int:
    """After the run exists as 'planned': re-read the job sha, execute ONCE (force + limit on that execution only), record, optionally wait."""
    send = dispatch or (lambda rid: dispatch_run(run_id=rid, project=args.project, region=args.region, job=args.job,
                                                 worker_limit=worker_limit, authorised=True))
    try:
        slw.recheck_live_job_sha(live_reader, pinned_job_sha=pinned)     # a redeploy since the INSERT: the live image is READ again
        # write-ahead marker: on disk BEFORE the execute, so a crash inside / after it can never be mistaken for "never executed"
        receipt["dispatch_intended_at"] = _utc_iso(now)
        write_receipt(receipt_path, receipt)
        execution = send(run_id)
    except Exception as exc:  # noqa: BLE001
        term = gad.terminalise_planned_run(connect, run_id, anchor, str(exc), frozen)
        warn = term["warning"]
        emit("dispatch_failed", run_id=run_id, error=str(exc), warning=warn, terminalised=term["terminalised"], **meta)
        receipt["verification"] = {"verdict": ["DISPATCH_FAILED"], "codes": ["DISPATCH_FAILED"], "notes": [str(exc), warn or "terminalised"]}
        write_receipt(receipt_path, receipt)
        summary.update(dispatch_error=str(exc), terminalise_warning=warn)
        emit("summary", **summary)
        return slw.EXIT_DISPATCH_FAILED
    receipt["execution_name"] = execution
    summary["execution_name"] = execution
    emit("run_dispatched", run_id=run_id, execution_name=execution, **meta)       # BEFORE the receipt write: the execution is reported even if the write fails
    try:
        write_receipt(receipt_path, receipt)
    except Exception as exc:  # noqa: BLE001
        warn = (f"run {run_id} WAS EXECUTED (execution {execution}) but the receipt could not be written ({type(exc).__name__}: {exc}). The receipt "
                "keeps the write-ahead marker, so --dispatch-existing will refuse a second execute. Do NOT dispatch again: use --verify-run "
                f"{run_id} once the receipt path is fixed (copy the execution name above into the evidence)")
        summary.update(warning=warn, receipt_write_error=str(exc))
        emit("summary", **summary)
        return slw.EXIT_UNEXPECTED
    if not args.wait:
        summary["verification"] = "not_waited"
        summary["monitor"] = (f"watch /clients/{anchor}/nirmana ; then: --verify-run {run_id} --anchor-chart {anchor} "
                              f"--receipt {receipt_path} --poll-seconds 30")
        emit("summary", **summary)
        return EXIT_OK
    return _finish(summary, receipt, receipt_path, connect=connect, run_id=run_id, plan=plan_ids, args=args, out=out,
                   sleep=sleep, monotonic=monotonic, now=now)


def _dispatch_existing(args, *, old, run_id, committed, token, plan, anchor, pinned, worker_limit, meta, summary, receipt_path, connect, frozen, git, dispatch,
                       out, sleep, monotonic, now, emit, live_reader) -> int:
    """RECOVERY: the run was committed 'planned' and never executed. Same plan (manifest digest), same token (the receipt's), the run
    still 'planned' and ours; then the ordinary dispatch stage. A late duplicate execution is harmless: the runner claims a run by
    compare-and-swap on state 'planned' and refuses one that is no longer runnable."""
    if token != old["confirm_token"]:
        raise _refuse("TOKEN_DIFFERS_FROM_RECEIPT", "the token recomputed from the current plan differs from the receipt's: the manifest, impact, "
                      "image or options changed since the plan; terminalise this run and plan again", expected=old["confirm_token"], now=token)
    if plan["manifest_digest"] != old["manifest_digest"]:
        raise _refuse("MANIFEST_DIGEST_CHANGED", "the current manifest digest differs from the committed run's")
    found = _check_run_is_ours(connect, run_id, anchor, old)
    if found["state"] != "planned":
        raise _refuse("RUN_NOT_PLANNED", f"run {run_id} is {found['state']!r}, not 'planned': it may already be executing. Verify it with "
                      f"--verify-run {run_id}; never execute it again", state=found["state"])
    if old.get("dispatch_intended_at") and run_id not in gad.parse_redispatch(args.allow_redispatch):
        raise _refuse("DISPATCH_ALREADY_ATTEMPTED", f"the receipt records that an execute of run {run_id} was INTENDED at "
                      f"{old['dispatch_intended_at']} (write-ahead marker) and no execution is recorded: it may have started. Check "
                      "`gcloud run jobs executions list` / describe for one with this --run-id; only if none exists, repeat with "
                      f"--allow-redispatch {run_id}", run_id=run_id)
    old.update(run_id=run_id, committed=True)         # the database row is the binding; the receipt now names it
    committed_rec = {"run_id": run_id, "anchor_chart": anchor, "manifest_digest": plan["manifest_digest"], "recovery": "dispatch-existing", **meta}
    committed.append(committed_rec)
    emit("run_dispatching_existing", **committed_rec)
    summary["committed"] = True
    summary["recovery"] = "dispatch-existing"
    return _dispatch_stage(run_id, args=args, anchor=anchor, pinned=pinned, worker_limit=worker_limit, meta=meta, receipt=old,
                           receipt_path=receipt_path, summary=summary, plan_ids=plan["plan"], connect=connect, frozen=frozen, git=git,
                           dispatch=dispatch, out=out, sleep=sleep, monotonic=monotonic, now=now, emit=emit, live_reader=live_reader)


def _terminalise_mode(args, *, anchor, receipt_path, connect, out, commit) -> int:
    """RECOVERY: cancel a committed run that is still 'planned' (it blocks the anchor chart). Needs the run's receipt, the run to be ours
    and 'planned'. Plan mode prints the confirm token; --commit --confirm asserts that no execution of the run exists."""
    run_id = _parse_run_id(args.terminalise_run, "--terminalise-run")
    old = _load_committed_receipt(receipt_path, anchor, run_id)
    found = _check_run_is_ours(connect, run_id, anchor, old)
    token = f"TERMINALISE_{run_id[:8].upper()}_NO_EXECUTION_STARTED"
    if found["state"] != "planned":
        raise _refuse("RUN_NOT_PLANNED", f"run {run_id} is {found['state']!r}, not 'planned': it has started or ended and is not terminalised "
                      f"by this tool. Verify it with --verify-run {run_id}", state=found["state"])
    recorded = ({"execution_name": old.get("execution_name"), "dispatch_intended_at": old.get("dispatch_intended_at")}
                if (old.get("execution_name") or old.get("dispatch_intended_at")) else None)
    summary = {"mode": "terminalise-run", "run_id": run_id, "anchor_chart": anchor, "state": found["state"], "confirm_token": token,
               "committed": False, "receipt_path": str(receipt_path), "execution_recorded": recorded,
               "note": "COMMIT asserts that NO execution of this run exists: check `gcloud run jobs executions list` for one with "
                       f"--run-id {run_id} first. The UPDATE only matches state='planned' (0 rows = it had started: nothing is changed)"}
    if not commit:
        _emit(out, "summary", **summary)
        return EXIT_OK
    if args.confirm != token:
        raise _refuse("CONFIRM_TOKEN_MISMATCH", f"--commit requires --confirm {token}", expected=token)
    if recorded and run_id not in gad.parse_redispatch(args.allow_redispatch):
        raise _refuse("EXECUTION_RECORDED_IN_RECEIPT", f"the receipt records an execution / an intended execute for run {run_id} ({recorded}): it "
                      "may be starting or deferred on the global lock. Check the executions list; only if it is dead repeat with "
                      f"--allow-redispatch {run_id}", recorded=recorded)
    old.update(run_id=run_id, committed=True)
    frozen = slw._load_frozen_dispatcher()
    term = gad.terminalise_planned_run(connect, run_id, anchor, "terminalised by the operator: the run was never executed", frozen)
    old["verification"] = {"verdict": ["TERMINALISED_BY_OPERATOR"], "codes": ["TERMINALISED_BY_OPERATOR"],
                           "notes": [term["warning"] or "terminalised"]}
    write_receipt(receipt_path, old)
    summary.update(committed=True, terminalised=term["terminalised"], warning=term["warning"])
    _emit(out, "summary", **summary)
    return EXIT_OK if term["terminalised"] is True else slw.EXIT_UNEXPECTED


def _read_rows(connect, ids: Sequence[str]) -> list[dict]:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(ROWS_SQL, (list(ids),))
        rows = [dict(r) for r in cur.fetchall()]
        conn.rollback()
        return rows
    finally:
        conn.close()


def _layer_counts(plan: Sequence[str], rows_by_id: Mapping[str, Mapping[str, Any]]) -> dict:
    out: dict[str, int] = {}
    for a in plan:
        out[rows_by_id[a].get("layer")] = out.get(rows_by_id[a].get("layer"), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: str(kv[0])))


def _finish(summary, receipt, receipt_path, *, connect, run_id, plan, args, out, sleep, monotonic, now) -> int:
    wait = slw.wait_for_terminal_run(connect, run_id, poll_seconds=args.poll_seconds, timeout_seconds=args.run_timeout_seconds,
                                     sleep=sleep, monotonic=monotonic)
    ver = verify_run(connect, run_id, plan, wait)
    receipt["verification"] = {k: ver[k] for k in ("verdict", "codes", "run_state", "wait", "complete", "assets_total", "assets_complete",
                                                   "assets_not_complete", "assets_missing", "assets_throughput_not_lit", "asset_errors")}
    receipt["verified_at"] = _utc_iso(now)
    write_receipt(receipt_path, receipt)
    _emit(out, "forced_effect", **ver["forced_effect"], wait=wait["state"])
    summary["verification"] = receipt["verification"]
    if ver["codes"]:
        summary["warning"] = ", ".join(ver["codes"])
    if "FORCE_DID_NOT_TAKE_EFFECT" in ver["codes"]:
        summary["second_dispatch"] = ("do NOT dispatch again without SS: the per-execution force override did not reach the container; read the "
                                      "execution's env, and only then plan again with --allow-redispatch <this run id> and a new token")
    _emit(out, "summary", **summary)
    return ver["exit_code"]


def _verify_run_mode(args, *, anchor, receipt_path, connect, out, sleep, monotonic, now) -> int:
    run_id = _parse_run_id(args.verify_run, "--verify-run")
    receipt = _load_committed_receipt(receipt_path, anchor, run_id)
    _check_run_is_ours(connect, run_id, anchor, receipt)
    summary = {"anchor_chart": anchor, "run_id": run_id, "mode": "verify-run", "receipt_path": str(receipt_path)}
    return _finish(summary, receipt, receipt_path, connect=connect, run_id=run_id, plan=receipt["assets"], args=args, out=out,
                   sleep=sleep, monotonic=monotonic, now=now)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return slw.EXIT_NO_DATABASE_URL

    def _term(signum, frame):  # noqa: ARG001
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _term)
    return run_cli(args, connect=slw._psycopg_connect_factory(database_url))


if __name__ == "__main__":
    raise SystemExit(main())
