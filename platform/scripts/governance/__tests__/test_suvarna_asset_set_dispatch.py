"""test_suvarna_asset_set_dispatch.py -- the forced multi-asset (L0+L1+L2) asset_set dispatcher (suvarna_asset_set_dispatch.py).

Offline. No database, no gcloud, no network: every outside contact (database connection, git, the Cloud Run dispatch, the clock)
is an injected fake. Nothing here is run against production.

Proof map
  plan          mixed global + per_chart ids -> one asset_set manifest in the planner's wave order; INSERT then ROLLBACK; no commit, no
                dispatch; the force / worker-limit env, the connection math and the token are printed; the manifest is accepted by the
                REAL runner.validate_frozen_run_manifest
  refusals      per id with a code (missing, inactive, no writer, writer sub-asset, service, scope, layer, domain, FAMILY); all reported
                together; nothing dropped unless --accept-excluded names it (and only if it really fails)
  token         binds ids + manifest digest + anchor + image + force + worker limit + accepted exclusions + redispatch
  commit        wrong token = no insert; exact token = INSERT, COMMIT, ONE execute with --update-env-vars on THAT execution only
  run level     busy anchor, global lock held, conflicting run, already dispatched, image skew, dependency not ready, registry changed
  verify        complete+forced = 0, skip_no_delta = 8, incomplete = 10
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suvarna_asset_set_dispatch as asd  # noqa: E402
import suvarna_global_asset_dispatch as gad  # noqa: E402
import suvarna_level_wave as slw  # noqa: E402

REPO = HERE.parents[3]
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
T0 = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)


def _hex(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def sha_of(ref: str) -> str:
    return hashlib.sha1(ref.encode()).hexdigest()


def row(asset, deps=(), *, scope="per_chart", layer="ganita", kind="data", active=True, writer=True, domain=None, target=None, probe=False):
    return {"asset_id": asset, "domain": domain or ("shared" if scope == "global" else "chart"), "rebuild_on_probe_fail": probe,
            "layer": layer, "scope": scope,
            "asset_kind": kind, "is_active": active, "has_writer": writer, "target_table": target or asset, "writer_timeout_seconds": 600,
            "estimated_seconds": None, "depends_on": list(deps), "natural_key_partition": None, "has_cowriters": False}


# L0 -> L1 -> L2 chain plus a side branch; bg_panchanga is a SERVICE dependency outside the set.
REG = {
    "bg_ontology": row("bg_ontology", scope="global", layer="brahmagyan"),
    "bg_reference": row("bg_reference", ["bg_ontology"], scope="global", layer="brahmagyan"),
    "bg_remedies": row("bg_remedies", scope="global", layer="brahmagyan"),
    "ga_panchanga": row("ga_panchanga", ["bg_panchanga"]),
    "ga_sensitive": row("ga_sensitive", ["bg_reference"]),
    "bo_laksana": row("bo_laksana", ["ga_sensitive", "ga_panchanga"], layer="bodha"),
    "bo_samskara": row("bo_samskara", ["bo_laksana"], layer="bodha"),
    # things that must be refused
    "bg_gochara_arcs": row("bg_gochara_arcs", scope="global", layer="brahmagyan"),
    "bg_transit_engine": row("bg_transit_engine", scope="global", layer="brahmagyan", writer=False),
    "bg_transit_rules": row("bg_transit_rules", scope="global", layer="brahmagyan"),
    "bg_panchanga": row("bg_panchanga", scope="global", layer="brahmagyan", kind="service", writer=False),
    "ga_fact_identity": row("ga_fact_identity", writer=False),
    "ka_dasha_x": row("ka_dasha_x", layer="kala"),
    "bg_retired": row("bg_retired", scope="global", layer="brahmagyan", active=False),
    "ga_odd_scope": row("ga_odd_scope", scope="mixed"),
    "ga_bad_domain": row("ga_bad_domain", domain="shared"),
    "ga_probe_x": row("ga_probe_x", probe=True),
    "ga_protected_x": row("ga_protected_x"),
}
OTHER_A, OTHER_B = "1c826d5a-0000-4000-8000-000000000001", "cb73cd3d-0000-4000-8000-000000000002"


def lit(asset, chart, state="lit"):
    return {"asset_id": asset, "chart_id": chart, "state": state, "last_built_at": T0, "freshness_state": "fresh"}


# lit rows other charts keep for dependents of the plan's global assets: 3 on A, 2 on B (the live counts are 41 and 29)
OTHER_ROWS = ([lit("ga_sensitive", OTHER_A), lit("bo_laksana", OTHER_A), lit("bo_samskara", OTHER_A), lit("ga_sensitive", OTHER_B),
               lit("bo_laksana", OTHER_B)] + [lit("ga_sensitive", CHART), lit("bg_reference", None)])
ACCEPT_ALL = ["--accept-cross-chart-impact", f"{OTHER_A}=3", "--accept-cross-chart-impact", f"{OTHER_B}=2"]
GOOD = ["bg_ontology", "bg_reference", "bg_remedies", "ga_panchanga", "ga_sensitive", "bo_laksana", "bo_samskara"]
DIGESTS = {a: _hex(a) for a in REG}
DEPS_STATE = {"bg_panchanga": ("lit", "unknown", "service")}      # service dependency outside the set: lit, freshness not required


class FakeCursor:
    def __init__(self, db):
        self.db, self._rows, self.rowcount = db, [], -1

    def execute(self, sql, params=None):
        sql = " ".join(sql.split())
        self.db.log.append(("execute", sql, params))
        self.rowcount = self.db.terminalise_rows if sql.startswith("WITH failed_run AS") else -1
        self._rows = self.db.respond(sql, params)

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConn:
    def __init__(self, db):
        self.db = db

    def cursor(self):
        return FakeCursor(self.db)

    def commit(self):
        self.db.commit_calls += 1
        if self.db.fail_commit:
            raise RuntimeError("fake connection dropped during COMMIT")
        self.db.log.append(("commit",))

    def rollback(self):
        self.db.log.append(("rollback",))

    def close(self):
        self.db.log.append(("close",))


class FakeDB:
    def __init__(self, *, registry=None, charts=(CHART,), deps=None, anchor_active=(), global_runs=(), conflicts=(), prior=(),
                 conn_numbers=None, run_state="completed", asset_rows=None, fail_commit=False, terminalise_rows=1, change_after_first=None,
                 throughput=(), protected=(), deps_after_first=None, on_insert=None, throughput_states=None, impact_after_first=None):
        self.log, self.registry = [], dict(REG if registry is None else registry)
        self.charts, self.deps = set(charts), DEPS_STATE if deps is None else deps
        self.anchor_active, self.global_runs, self.conflicts, self.prior = list(anchor_active), list(global_runs), list(conflicts), list(prior)
        self.conn_numbers = conn_numbers or {"max_connections": 50, "reserved": 3, "in_use": 9}
        self.run_state, self.asset_rows = run_state, asset_rows
        self.fail_commit, self.commit_calls, self.terminalise_rows = fail_commit, 0, terminalise_rows
        self.rows_calls, self.change_after_first = 0, change_after_first
        self.throughput, self.protected, self.deps_after_first, self.on_insert = list(throughput), list(protected), deps_after_first, on_insert
        self.throughput_states, self.impact_after_first = throughput_states or {}, impact_after_first
        self.dep_calls, self.impact_calls = 0, 0
        self.inserted_run = None

    def connect(self):
        self.log.append(("connect",))
        return FakeConn(self)

    def respond(self, sql, params):
        if "pg_advisory_xact_lock" in sql:
            return []
        if "FROM charts WHERE id" in sql:
            return [{"id": params[0]}] if params[0] in self.charts else []
        if sql.startswith("SELECT ar.asset_id, ar.domain,"):
            self.rows_calls += 1
            reg = self.registry
            if self.change_after_first and self.rows_calls > 1:
                reg = {**reg, **self.change_after_first}
            return [dict(reg[a]) for a in sorted(params[0]) if a in reg]
        if sql.startswith("SELECT ar.asset_id, COALESCE(ar.depends_on"):
            return [{"asset_id": a, "depends_on": self.registry[a]["depends_on"]} for a in params[0] if a in self.registry]
        if "FROM build_protected_assets" in sql:
            return [{"asset_id": a} for a in self.protected if a in set(params[1])]
        if sql.startswith("WITH RECURSIVE downstream"):
            seen, todo = set(), set(params[0])
            while todo:
                nxt = {a for a, r in self.registry.items() if set(r["depends_on"]) & todo} - seen
                seen |= nxt
                todo = nxt
            return [{"asset_id": a} for a in sorted(seen)]
        if "FROM asset_throughput at LEFT JOIN LATERAL" in sql:
            self.impact_calls += 1
            rows = self.throughput if not (self.impact_after_first is not None and self.impact_calls > 1) else self.impact_after_first
            return [t for t in rows if t["asset_id"] in set(params[0])]
        if "unnest(%s::text[]) AS dep" in sql:
            self.dep_calls += 1
            deps = self.deps_after_first if (self.deps_after_first is not None and self.dep_calls > 1) else self.deps
            return [{"asset_id": d, "asset_kind": (deps.get(d) or (None, None, "data"))[2], "state": (deps.get(d) or (None,))[0],
                     "freshness_state": (deps.get(d) or (None, None))[1]} for d in params[0]]
        if "FROM build_runs WHERE chart_id" in sql:
            return list(self.anchor_active)
        if "JOIN asset_registry ar ON ar.asset_id = bra.asset_id" in sql:
            return list(self.global_runs)
        if "left(br.triggered_by" in sql:
            return list(self.prior)
        if "FROM build_runs br JOIN build_run_assets bra" in sql:
            return list(self.conflicts)
        if "current_setting('max_connections')" in sql:
            return [dict(self.conn_numbers)]
        if sql.startswith("INSERT INTO build_runs"):
            self.inserted_run = params
            if self.on_insert:
                self.on_insert()
        if "SELECT state, last_error FROM build_runs WHERE id" in sql:
            return [{"state": self.run_state, "last_error": None}]
        if "FROM build_run_assets bra JOIN build_runs br" in sql:
            plan = json.loads(self.inserted_run[3]) if self.inserted_run else GOOD
            rows = self.asset_rows if self.asset_rows is not None else {a: ("complete", "build") for a in plan}
            return [{"asset_id": a, "position": i, "state": s, "disposition": d, "error": None, "throughput_state": self.throughput_states.get(a, "lit"),
                     "started_at": T0, "ended_at": T0, "last_built_at": T0} for i, (a, (s, d)) in enumerate(rows.items())]
        if "plan_manifest_digest FROM build_runs WHERE id" in sql:
            return [self.run_row] if getattr(self, "run_row", None) else []
        return []

    def statements(self):
        return [e for e in self.log if e[0] == "execute"]

    def inserts(self, table):
        return [e for e in self.statements() if e[1].startswith(f"INSERT INTO {table}")]

    def kinds(self):
        return [e[0] for e in self.log]


RUNNER_WITH_FORCE = 'force = os.environ.get("NIRMANA_FORCE_EXECUTE", "").strip().lower() in ("1", "true", "yes")\n'
ASSET_RUNNER_WITH_FORCE = "def _c(cur, force):\n    if declared_deps is not None and has_cowriters is not None and not force:\n        return _skip()\n"


class FakeGit:
    def __init__(self, *, deployed=None, family_set=(), runner_text=RUNNER_WITH_FORCE):
        self.deployed, self.runner_text = deployed, runner_text
        self.family = {k: [] for k in slw.FAMILY_LIST_KEYS}
        self.family["family_gochara"] = list(family_set)
        self.family["family_set"] = sorted(family_set)

    def __call__(self, repo, args):
        cp = lambda rc=0, out="", err="": subprocess.CompletedProcess(args, rc, out, err)  # noqa: E731
        if args[0] == "rev-parse":
            ref = args[2][: -len("^{commit}")]
            return cp(0, (ref if re.fullmatch(r"[0-9a-f]{40}", ref) else sha_of(ref)) + "\n")
        if args[0] == "ls-remote":
            return cp(0, f"{sha_of('origin/main')}\t{args[2]}\n")
        if args[0] == "ls-tree":
            return cp(0, slw.FAMILY_FILE_REL + "\n")
        if args[0] == "show":
            spec = args[1]
            if spec.endswith(slw.FAMILY_FILE_REL):
                return cp(0, json.dumps(self.family))
            if spec.endswith(slw.RUNNER_REL):
                return cp(0, self.runner_text)
            if spec.endswith(slw.ASSET_RUNNER_REL):
                return cp(0, ASSET_RUNNER_WITH_FORCE)
            if spec.endswith(slw.WRITER_DIGESTS_REL):
                return cp(0, json.dumps({"writers": self.deployed}))
        raise AssertionError(f"unexpected git call {args}")


class FakeLive:
    """The injected, read-only reader of the LIVE job image sha (what `gcloud run jobs describe` would answer). `queue` changes the answer
    from the next read on (a redeploy); `error` makes it unreadable."""
    def __init__(self, sha):
        self.sha, self.error, self.queue, self.calls = sha, None, [], 0

    def __call__(self):
        self.calls += 1
        if self.queue:
            self.sha = self.queue.pop(0)
        if self.error:
            raise slw.LevelWaveRefusal([{"code": "LIVE_JOB_IMAGE_UNREADABLE", "detail": self.error}])
        return self.sha


class Dispatch:
    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def __call__(self, run_id):
        self.calls.append(run_id)
        if self.fail:
            raise RuntimeError("gcloud refused")
        return "brahma-build-pipeline-job-exec-1"


class Stream(io.StringIO):
    pass


class RealProcessAttempt(BaseException):
    pass


@pytest.fixture(autouse=True)
def no_real_subprocess(monkeypatch):
    def blocked(*a, **k):
        raise RealProcessAttempt(f"a real subprocess was requested in a test: {a[:1]}")
    for name in ("run", "Popen", "check_output", "check_call", "call"):
        monkeypatch.setattr(subprocess, name, blocked)


@pytest.fixture
def env(tmp_path):
    repo = tmp_path / "repo"
    gen = repo / "platform" / "src" / "generated"
    gen.mkdir(parents=True)
    (gen / "nirmana-writer-digests.json").write_text(json.dumps({"version": 1, "writers": DIGESTS}))
    out = tmp_path / "out"
    out.mkdir()
    return {"repo": str(repo), "receipt": str(out / "receipt.json"), "live": FakeLive(sha_of("deadbeef")), "tmp": tmp_path}


def argv_for(env, *extra, assets=GOOD, commit=False, confirm=None, anchor=CHART, worker_limit=None):
    argv = ["--assets", ",".join(assets), "--anchor-chart", anchor, "--receipt", env["receipt"], "--repo", env["repo"],
            "--deployed-sha", "deadbeef", "--deployed-job-sha", "deadbeef"]
    if worker_limit is not None:
        argv += ["--worker-limit", str(worker_limit)]
    if commit:
        argv += ["--commit", "--confirm", confirm or "x"]
    return asd.build_parser().parse_args(argv + list(extra))


def run(env, args, db=None, git=None, dispatch=None, live=None):
    db = db or FakeDB()
    git = git or FakeGit(deployed=DIGESTS)
    out = Stream()
    code = asd.run_cli(args, connect=db.connect, git=git, out=out, sleep=lambda s: None, monotonic=lambda: 0.0, dispatch=dispatch,
                       now=lambda: T0, live_reader=live or env["live"])
    return code, [json.loads(l) for l in out.getvalue().splitlines() if l.strip()]


def last(ev):
    return ev[-1]


def refusal_pairs(ev):
    return sorted((r.get("asset"), r["code"]) for r in last(ev).get("refusals", []))


def plan(env, **kw):
    code, ev = run(env, argv_for(env, **kw), db=FakeDB())
    assert code == 0, ev
    if pathlib.Path(env["receipt"]).exists():
        pathlib.Path(env["receipt"]).unlink()
    return last(ev)


# ───────────────────────── plan ─────────────────────────

def test_plan_orders_global_and_per_chart_assets_by_the_waves_and_never_commits_or_dispatches(env):
    db, disp = FakeDB(), Dispatch()
    code, ev = run(env, argv_for(env, worker_limit=4), db=db, dispatch=disp)
    s = last(ev)
    assert code == 0 and s["event"] == "summary" and s["committed"] is False and disp.calls == []
    assert s["waves"] == [["bg_ontology", "bg_remedies", "ga_panchanga"], ["bg_reference"], ["ga_sensitive"], ["bo_laksana"], ["bo_samskara"]]
    assert s["assets"] == [a for w in s["waves"] for a in w] and s["asset_count"] == 7
    assert s["layer_counts"] == {"bodha": 2, "brahmagyan": 3, "ganita": 2}
    assert s["global_assets"] == ["bg_ontology", "bg_reference", "bg_remedies"]
    assert s["external_dependencies"] == {"ga_panchanga": ["bg_panchanga"]}
    assert s["force_execute"] is True and s["scope"] == "asset_set" and s["action"] == "rebuild" and s["anchor_chart"] == CHART
    assert s["execution_env_override"] == {"NIRMANA_FORCE_EXECUTE": "1", "ORCHESTRATOR_WORKER_LIMIT": "4"}
    assert s["dispatch_command_preview"][-3] == "--update-env-vars=NIRMANA_FORCE_EXECUTE=1,ORCHESTRATOR_WORKER_LIMIT=4"
    assert "global_assets" in s["locks"] and "defer" in s["locks"]["global_assets"]
    assert s["job_image_check"]["binding"] == "verified"
    assert re.fullmatch(r"ASSETSET7_[0-9A-F]{12}_FORCE_ASSET_SET_REBUILD", s["confirm_token"])
    # INSERT then ROLLBACK
    assert len(db.inserts("build_runs")) == 1 and len(db.inserts("build_run_assets")) == 7
    assert "commit" not in db.kinds() and db.kinds().count("rollback") >= 1
    assert s["triggered_by"].startswith("asset-set-dispatch:anchor_chart=" + CHART + ";manifest_sha256=")
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert rec["committed"] is False and rec["run_id"] is None and rec["worker_limit"] == 4


def test_the_insert_texts_are_the_waves_and_the_row_is_asset_set_rebuild(env):
    db = FakeDB()
    run(env, argv_for(env), db=db)
    sql, params = db.inserts("build_runs")[0][1], db.inserts("build_runs")[0][2]
    assert sql == " ".join(gad.INSERT_RUN_SQL.split())
    assert "'asset_set'" in sql and "'rebuild'" in sql and "'planned'" in sql
    run_id, chart, scope_target, plan_json, manifest_json, digest, trig = params
    assert chart == CHART and json.loads(plan_json) == scope_target.split(",") and trig == build_trig(digest)
    assert db.inserts("build_run_assets")[0][1] == " ".join(gad.INSERT_RUN_ASSET_SQL.split())


def build_trig(digest):
    return asd.build_triggered_by(CHART, digest)


def test_the_manifest_is_accepted_by_the_real_runner_with_mixed_scopes(env):
    db = FakeDB()
    run(env, argv_for(env), db=db)
    _, chart, scope_target, plan_json, manifest_json, digest, _t = db.inserts("build_runs")[0][2]
    manifest = json.loads(manifest_json)
    sys.path.insert(0, str(REPO / "platform/python-sidecar"))
    try:
        from pipeline.orchestrator.runner import validate_frozen_run_manifest
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"frozen runner not importable here: {exc.__class__.__name__}")
    frozen = validate_frozen_run_manifest({"plan_manifest": manifest, "plan_manifest_digest": digest, "chart_id": chart, "scope": "asset_set",
                                           "scope_target": scope_target, "action": "rebuild", "plan": json.loads(plan_json)})
    assert {frozen.asset_scopes[a] for a in frozen.plan} == {"global", "per_chart"}
    assert frozen.plan == json.loads(plan_json)


def test_the_dry_run_prints_the_connection_math_and_headroom(env):
    s = last(run(env, argv_for(env, worker_limit=4), db=FakeDB())[1])
    b = s["connection_budget"]
    assert (b["worker_limit_effective"], b["runner_documented_connections_per_run"], b["worst_case_connections_for_this_run"]) == (4, 5, 10)
    assert (b["db_max_connections"], b["db_usable_connections"], b["db_in_use_now"]) == (50, 47, 9)
    assert b["headroom_after_this_run"] == 28 and b["ok"] is True and "override" in b["worker_limit_source"]
    pathlib.Path(env["receipt"]).unlink()
    s3 = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])
    assert s3["connection_budget"]["headroom_after_this_run"] == 47 - 9 - 8


def test_unset_worker_limit_prints_only_the_force_override_and_uses_the_job_value_for_the_math(env):
    s = last(run(env, argv_for(env, "--job-worker-limit", "2"), db=FakeDB())[1])
    assert s["execution_env_override"] == {"NIRMANA_FORCE_EXECUTE": "1"} and s["worker_limit_override"] is None
    assert s["dispatch_command_preview"][-3] == "--update-env-vars=NIRMANA_FORCE_EXECUTE=1"
    assert s["connection_budget"]["worker_limit_effective"] == 2 and "job-worker-limit" in s["connection_budget"]["worker_limit_source"]


def test_low_connection_headroom_refuses_before_any_insert(env):
    db = FakeDB(conn_numbers={"max_connections": 50, "reserved": 3, "in_use": 30})
    code, ev = run(env, argv_for(env, worker_limit=4), db=db)
    assert code == 4 and [c for _a, c in refusal_pairs(ev)] == ["CONNECTION_HEADROOM_LOW"]
    assert db.inserts("build_runs") == []


@pytest.mark.parametrize("bad", [0, 7, -1])
def test_worker_limit_out_of_range_is_refused(env, bad):
    code, ev = run(env, argv_for(env, worker_limit=bad), db=FakeDB())
    assert code == 4 and [c for _a, c in refusal_pairs(ev)] == ["WORKER_LIMIT_INVALID"]


# ───────────────────────── per-id refusals ─────────────────────────

def test_every_failing_id_is_refused_with_its_own_code_all_at_once(env):
    ids = GOOD + ["bg_gochara_arcs", "bg_transit_engine", "bg_panchanga", "ga_fact_identity", "ka_dasha_x", "bg_retired", "ga_odd_scope",
                  "ga_bad_domain", "bg_missing_x"]
    db = FakeDB()
    code, ev = run(env, argv_for(env, assets=ids), db=db, git=FakeGit(deployed=DIGESTS, family_set=["bg_gochara_arcs"]))
    assert code == 4
    pairs = set(refusal_pairs(ev))
    assert ("bg_gochara_arcs", "FAMILY_ASSET") in pairs
    assert ("bg_transit_engine", "WRITER_SUBASSET") in pairs and ("bg_transit_engine", "NO_WRITER") not in pairs
    assert {("bg_panchanga", "SERVICE_ASSET"), ("bg_panchanga", "NO_WRITER")} <= pairs
    assert ("ga_fact_identity", "NO_WRITER") in pairs and ("ka_dasha_x", "LAYER_NOT_ALLOWED") in pairs and ("bg_retired", "NOT_ACTIVE") in pairs
    assert ("ga_odd_scope", "SCOPE_NOT_ALLOWED") in pairs and ("ga_bad_domain", "DOMAIN_SCOPE_MISMATCH") in pairs
    assert ("bg_missing_x", "REGISTRY_ROW_MISSING") in pairs
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds()


def test_the_gochara_family_is_refused_by_name_even_without_the_family_file_listing_it(env):
    code, ev = run(env, argv_for(env, assets=GOOD + ["bg_gochara_arcs"]), db=FakeDB())
    assert code == 4 and refusal_pairs(ev) == [("bg_gochara_arcs", "FAMILY_ASSET")]
    assert last(ev)["refusals"][0]["detail"].startswith("bg_gochara_arcs matches the Pravaha gochara family name pattern")


def test_a_split_family_is_refused_per_member(env):
    reg = {**REG, "bg_remedies": row("bg_remedies", scope="global", layer="brahmagyan")}
    git = FakeGit(deployed=DIGESTS)
    git.family["family_gochara"] = ["bg_remedies", "bg_transit_rules"]
    git.family["family_set"] = ["bg_remedies", "bg_transit_rules"]
    code, ev = run(env, argv_for(env), db=FakeDB(registry=reg), git=git)
    assert code == 4 and ("bg_remedies", "FAMILY_ASSET") in refusal_pairs(ev)


def test_nothing_is_dropped_silently_accept_excluded_drops_exactly_the_named_failing_id(env):
    ids = GOOD + ["bg_gochara_arcs"]
    code, ev = run(env, argv_for(env, "--accept-excluded", "bg_gochara_arcs", assets=ids), db=FakeDB())
    s = last(ev)
    assert code == 0 and s["excluded_accepted"] == [{"asset": "bg_gochara_arcs", "codes": ["FAMILY_ASSET"]}]
    assert sorted(s["assets"]) == sorted(GOOD) and "bg_gochara_arcs" not in s["assets"]
    pathlib.Path(env["receipt"]).unlink()
    assert plan(env)["confirm_token"] != s["confirm_token"]            # bound by the accepted exclusion list


def test_accept_excluded_cannot_drop_a_valid_asset_or_an_unrequested_one(env):
    code, ev = run(env, argv_for(env, "--accept-excluded", "bo_samskara,bg_not_in_list"), db=FakeDB())
    assert code == 4
    assert refusal_pairs(ev) == [("bg_not_in_list", "ACCEPT_EXCLUDED_NOT_REQUESTED"), ("bo_samskara", "ACCEPT_EXCLUDED_NOT_NEEDED")]


def test_a_list_that_is_entirely_excluded_is_an_empty_plan(env):
    code, ev = run(env, argv_for(env, "--accept-excluded", "bg_gochara_arcs", assets=["bg_gochara_arcs"]), db=FakeDB())
    assert code == 4 and [c for _a, c in refusal_pairs(ev)] == ["EMPTY_PLAN"]


def test_protected_and_probe_bypassed_assets_are_refused_per_id(env):
    code, ev = run(env, argv_for(env, assets=GOOD + ["ga_probe_x", "ga_protected_x"]), db=FakeDB(protected=["ga_protected_x"]))
    assert code == 4 and refusal_pairs(ev) == [("ga_probe_x", "FORCE_BYPASSED_BY_PROBE"), ("ga_protected_x", "PROTECTED_ASSET")]
    code, ev = run(env, argv_for(env, "--accept-excluded", "ga_probe_x,ga_protected_x", assets=GOOD + ["ga_probe_x", "ga_protected_x"]),
                   db=FakeDB(protected=["ga_protected_x"]))
    assert code == 0 and {e["asset"] for e in last(ev)["excluded_accepted"]} == {"ga_probe_x", "ga_protected_x"}


def test_the_asset_list_is_a_file_with_comments_and_a_bad_file_is_bad_input(env, tmp_path):
    f = tmp_path / "ids.txt"
    f.write_text("# L0\nbg_ontology, bg_reference  # two\nbg_remedies\nga_panchanga ga_sensitive\nbo_laksana\nbo_samskara\n")
    assert asd.parse_asset_ids(None, str(f)) == GOOD
    for text in ("bg_ontology\nbg_ontology\n", "BG_Bad\n", ""):
        f.write_text(text)
        with pytest.raises(slw.LevelWaveError):
            asd.parse_asset_ids(None, str(f))
    link = tmp_path / "link.txt"
    link.symlink_to(f)
    with pytest.raises(slw.LevelWaveError):
        asd.parse_asset_ids(None, str(link))
    f.write_text("a" * (asd.IDS_FILE_MAX_BYTES + 1))
    with pytest.raises(slw.LevelWaveError):
        asd.parse_asset_ids(None, str(f))
    with pytest.raises(slw.LevelWaveError):
        asd.parse_asset_ids(["bg_ontology", "bg_ontology"], None)


# ───────────────────────── token ─────────────────────────

def test_the_token_binds_ids_manifest_anchor_image_force_worker_limit_exclusions_and_redispatch():
    base = dict(manifest_digest=_hex("m"), ids=["a", "b"], anchor=CHART, image_sha=sha_of("i"), worker_limit=4, accepted_excluded=[],
                allow_redispatch=[])
    t = asd.build_confirm_token(**base)
    assert t == asd.build_confirm_token(**{**base, "ids": ["b", "a"]})           # order-free id set; the digest carries the order
    for k, v in (("manifest_digest", _hex("m2")), ("ids", ["a", "c"]), ("anchor", "1c826d5a-0000-4000-8000-000000000001"),
                 ("image_sha", sha_of("j")), ("worker_limit", 3), ("worker_limit", None), ("accepted_excluded", ["x"]),
                 ("allow_redispatch", ["00000000-0000-4000-8000-000000000000"])):
        assert asd.build_confirm_token(**{**base, k: v}) != t, k
    assert t.startswith("ASSETSET2_") and t.endswith("_FORCE_ASSET_SET_REBUILD")


def test_a_token_from_another_limit_or_id_list_cannot_confirm(env):
    tok4 = plan(env, worker_limit=4)["confirm_token"]
    db = FakeDB()
    code, ev = run(env, argv_for(env, commit=True, confirm=tok4, worker_limit=3), db=db, dispatch=Dispatch())
    assert code == 4 and refusal_pairs(ev) == [(None, "CONFIRM_TOKEN_MISMATCH")]
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds()
    code, ev = run(env, argv_for(env, commit=True, confirm=tok4, worker_limit=4, assets=GOOD[:-1]), db=db, dispatch=Dispatch())
    assert code == 4 and refusal_pairs(ev) == [(None, "CONFIRM_TOKEN_MISMATCH")]


# ───────────────────────── commit + dispatch (force + limit on THAT execution only) ─────────────────────────

def commit_run(env, *, worker_limit=4, db=None, dispatch=None, extra=()):
    token = plan(env, worker_limit=worker_limit)["confirm_token"]
    db = db or FakeDB()
    disp = dispatch if dispatch is not None else Dispatch()
    code, ev = run(env, argv_for(env, *extra, commit=True, confirm=token, worker_limit=worker_limit), db=db, dispatch=disp)
    return code, ev, db, disp


def test_commit_inserts_commits_and_dispatches_once_and_returns_the_run_id(env):
    code, ev, db, disp = commit_run(env)
    s = last(ev)
    assert code == 0 and s["committed"] is True and db.commit_calls == 1 and len(disp.calls) == 1
    assert [e["event"] for e in ev][:2] == ["run_committed", "run_dispatched"]
    assert s["verification"] == "not_waited" and db.inserted_run[0] == disp.calls[0] and "--verify-run" in s["monitor"]
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert rec["committed"] is True and rec["run_id"] == disp.calls[0] and rec["execution_name"] and rec["worker_limit"] == 4


def test_the_real_dispatch_runs_one_execute_with_update_env_vars_and_never_updates_the_job(env, monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, 0, "exec-name-1\n", "")
    monkeypatch.setattr(subprocess, "run", fake_run)
    token = plan(env, worker_limit=4)["confirm_token"]
    db = FakeDB()
    code, ev = run(env, argv_for(env, commit=True, confirm=token, worker_limit=4), db=db, dispatch=None)
    assert code == 0 and len(calls) == 1
    cmd, kw = calls[0]
    assert cmd[:5] == ["gcloud", "run", "jobs", "execute", "brahma-build-pipeline-job"]
    assert f"--args=--run-id,{db.inserted_run[0]}" in cmd
    assert "--update-env-vars=NIRMANA_FORCE_EXECUTE=1,ORCHESTRATOR_WORKER_LIMIT=4" in cmd
    assert not any(x in cmd for x in ("update", "deploy", "--set-env-vars", "--replace-env-vars", "--remove-env-vars"))
    assert kw["stdin"] == subprocess.DEVNULL and kw["env"]["CLOUDSDK_CORE_DISABLE_PROMPTS"] == "1"


def test_unset_limit_commit_with_matching_token(env, monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: calls.append(cmd) or subprocess.CompletedProcess(cmd, 0, "e\n", ""))
    token = plan(env, worker_limit=None)["confirm_token"]
    code, _ = run(env, argv_for(env, commit=True, confirm=token), db=FakeDB(), dispatch=None)
    assert code == 0 and len(calls) == 1 and "--update-env-vars=NIRMANA_FORCE_EXECUTE=1" in calls[0]
    assert not any("ORCHESTRATOR_WORKER_LIMIT" in x for x in calls[0])


def test_dispatch_command_unit_and_unauthorised_default_refuses():
    cmd = asd.dispatch_command(run_id="r1", project="p", region="r", job="j", worker_limit=3)
    assert cmd == ["gcloud", "run", "jobs", "execute", "j", "--project=p", "--region=r", "--args=--run-id,r1",
                   "--update-env-vars=NIRMANA_FORCE_EXECUTE=1,ORCHESTRATOR_WORKER_LIMIT=3", "--async", "--format=value(metadata.name)"]
    with pytest.raises(RuntimeError, match="not the authorised"):
        asd.dispatch_run(run_id="r1", project="p", region="r", job="j", worker_limit=None)
    with pytest.raises(RealProcessAttempt):
        asd.dispatch_run(run_id="r1", project="p", region="r", job="j", worker_limit=None, authorised=True)


def test_plan_never_dispatches_even_with_a_real_runner_path(env):
    code, _ = run(env, argv_for(env), db=FakeDB(), dispatch=None)         # the autouse fixture turns any real process into a failure
    assert code == 0


def test_a_dispatch_failure_terminalises_the_planned_run_and_exits_3(env):
    code, ev, db, disp = commit_run(env, dispatch=Dispatch(fail=True))
    e = [x for x in ev if x["event"] == "dispatch_failed"][0]
    assert code == 3 and e["terminalised"] is True and e["warning"] is None
    assert any(s[1].startswith("WITH failed_run AS") for s in db.statements())
    pathlib.Path(env["receipt"]).unlink()
    code, ev, db, disp = commit_run(env, db=FakeDB(terminalise_rows=0), dispatch=Dispatch(fail=True))
    e = [x for x in ev if x["event"] == "dispatch_failed"][0]
    assert code == 3 and e["terminalised"] is False and "NOT terminalised" in e["warning"]


def test_an_unknown_commit_outcome_is_reported_with_the_run_id(env):
    token = plan(env, worker_limit=4)["confirm_token"]
    db = FakeDB(fail_commit=True)
    disp = Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=token, worker_limit=4), db=db, dispatch=disp)
    assert code == 6 and last(ev)["commit_outcome_unknown"] is True and disp.calls == []


def _bare_args(env, *extra, commit=False, confirm=None):
    """No --deployed-sha / --deployed-job-sha at all: nothing is asserted by hand, the live image is the only source."""
    argv = ["--assets", ",".join(GOOD), "--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"]]
    if commit:
        argv += ["--commit", "--confirm", confirm or "x"]
    return asd.build_parser().parse_args(argv + list(extra))


def test_nothing_needs_to_be_asserted_by_hand_the_live_image_is_read_and_bound_into_the_token(env):
    code, ev = run(env, _bare_args(env), db=FakeDB())
    s = last(ev)
    assert code == 0 and s["job_image_check"]["deployed_job_sha"] == sha_of("deadbeef") == s["job_image_check"]["inventory_sha"]
    assert env["live"].calls == 1                                    # the plan read the live image once
    pathlib.Path(env["receipt"]).unlink()
    env["live"].sha = sha_of("a newer deploy")
    assert last(run(env, _bare_args(env), db=FakeDB())[1])["confirm_token"] != s["confirm_token"]       # the token binds the LIVE sha


def test_the_parser_no_longer_accepts_a_job_sha_file():
    with pytest.raises(SystemExit):
        asd.build_parser().parse_args(["--anchor-chart", CHART, "--receipt", "r", "--job-sha-file", "f"])


def test_a_live_image_that_differs_from_the_asserted_job_sha_refuses_at_plan(env):
    env["live"].sha = sha_of("bb143edf2")
    code, ev = run(env, argv_for(env), db=FakeDB())                  # the operator still asserts deadbeef (a stale value)
    r = last(ev)["refusals"][0]
    assert code == 4 and r["code"] == "LIVE_JOB_IMAGE_DIFFERS" and r["live_job_sha"] == sha_of("bb143edf2") and r["asserted_job_sha"] == sha_of("deadbeef")


def test_a_deployed_sha_that_is_not_the_live_image_refuses_at_plan(env):
    args = _bare_args(env, "--deployed-sha", "cafebabe")
    code, ev = run(env, args, db=FakeDB())
    assert code == 4 and last(ev)["refusals"][0]["code"] == "JOB_SHA_MISMATCH"


def test_an_unreadable_live_image_refuses_fail_closed_at_plan_and_commit(env):
    env["live"].error = "gcloud run jobs describe failed: PERMISSION_DENIED"
    for args in (_bare_args(env), _bare_args(env, commit=True, confirm="x")):
        db, disp = FakeDB(), Dispatch()
        code, ev = run(env, args, db=db, dispatch=disp)
        assert code == 4 and last(ev)["refusals"][0]["code"] == "LIVE_JOB_IMAGE_UNREADABLE" and db.inserts("build_runs") == [] and disp.calls == []


def test_a_live_image_that_changes_between_plan_and_commit_refuses_before_the_insert(env):
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    pathlib.Path(env["receipt"]).unlink()
    env["live"].queue = [sha_of("deadbeef"), sha_of("a redeploy")]   # read 1 (gates) = planned sha, read 2 (right before the INSERT) = redeployed
    db, disp = FakeDB(), Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=tok, worker_limit=3), db=db, dispatch=disp)
    r = last(ev)["refusals"][0]
    assert code == 4 and r["code"] == "JOB_SHA_CHANGED" and r["pinned"] == sha_of("deadbeef") and r["now"] == sha_of("a redeploy")
    assert db.inserts("build_runs") == [] and disp.calls == []


# ───────────────────────── run-level gates ─────────────────────────

@pytest.mark.parametrize("kw,code_", [
    ({"anchor_active": [{"id": "r1", "chart_id": CHART, "state": "running"}]}, "ANCHOR_CHART_BUSY"),
    ({"global_runs": [{"id": "r2", "chart_id": "x", "state": "running", "asset_id": "bg_other"}]}, "GLOBAL_LOCK_HELD"),
    ({"conflicts": [{"id": "r3", "chart_id": "x", "state": "planned", "asset_id": "ga_sensitive"}]}, "CONFLICTING_ACTIVE_RUN"),
    ({"prior": [{"id": "6b1e0c1a-0000-4000-8000-000000000001", "state": "failed", "plan_manifest_digest": "d", "triggered_by": "asset-set-dispatch:x"}]},
     "ALREADY_DISPATCHED"),
    ({"charts": ()}, "ANCHOR_CHART_INVALID"),
])
def test_run_level_refusals_leave_nothing_behind(env, kw, code_):
    db = FakeDB(**kw)
    code, ev = run(env, argv_for(env), db=db)
    assert code == 4 and [c for _a, c in refusal_pairs(ev)] == [code_]
    assert db.inserts("build_runs") == []


def test_a_prior_run_is_allowed_only_when_named(env):
    prior = [{"id": "6b1e0c1a-0000-4000-8000-000000000001", "state": "failed", "plan_manifest_digest": "d", "triggered_by": "asset-set-dispatch:x"}]
    code, ev = run(env, argv_for(env, "--allow-redispatch", "6b1e0c1a-0000-4000-8000-000000000001"), db=FakeDB(prior=prior))
    assert code == 0


def test_a_global_lock_check_is_skipped_for_a_plan_with_no_global_asset(env):
    code, ev = run(env, argv_for(env, assets=["ga_panchanga"]),
                   db=FakeDB(global_runs=[{"id": "r2", "chart_id": "x", "state": "running", "asset_id": "bg_other"}]))
    assert code == 0 and last(ev)["locks"]["global_assets"].startswith("not taken")


def test_image_skew_and_dependency_and_registry_change_refuse(env):
    code, ev = run(env, argv_for(env), db=FakeDB(), git=FakeGit(deployed={**DIGESTS, "bo_laksana": _hex("other build")}))
    assert code == 4 and refusal_pairs(ev) == [("bo_laksana", "IMAGE_SKEW")]
    code, ev = run(env, argv_for(env), db=FakeDB(deps={"bg_panchanga": (None, None, "service")}))
    assert code == 4 and [c for _a, c in refusal_pairs(ev)] == ["DEPENDENCY_NOT_READY"]
    token = plan(env)["confirm_token"]
    changed = {"bo_laksana": {**REG["bo_laksana"], "depends_on": ["ga_sensitive"]}}
    db = FakeDB(change_after_first=changed)
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=Dispatch())
    assert code == 4 and refusal_pairs(ev) == [("bo_laksana", "REGISTRY_ROW_CHANGED")] and "commit" not in db.kinds()


def test_force_unsupported_image_is_refused(env):
    code, ev = run(env, argv_for(env), db=FakeDB(), git=FakeGit(deployed=DIGESTS, runner_text="def execute_run(run_id):\n    pass\n"))
    assert code == 4 and refusal_pairs(ev) == [(None, "FORCE_NOT_SUPPORTED_BY_IMAGE")]


# ───────────────────────── verification ─────────────────────────

def _committed_receipt(env, db):
    token = plan(env, worker_limit=4)["confirm_token"]
    code, ev = run(env, argv_for(env, commit=True, confirm=token, worker_limit=4), db=db, dispatch=Dispatch())
    assert code == 0
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    db.run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "completed", "triggered_by": rec["triggered_by"],
                  "plan_manifest_digest": rec["manifest_digest"]}
    return rec


def _verify(env, db, rec):
    args = argv_for(env)
    args.verify_run = rec["run_id"]
    return run(env, args, db=db)


def test_verify_run_passes_when_complete_and_every_asset_was_built(env):
    db = FakeDB()
    rec = _committed_receipt(env, db)
    code, ev = _verify(env, db, rec)
    assert code == 0 and last(ev)["verification"]["verdict"] == "PASS" and last(ev)["verification"]["assets_complete"] == 7


def test_verify_run_skip_no_delta_is_exit_8_and_incomplete_is_exit_10(env):
    db = FakeDB()
    rec = _committed_receipt(env, db)
    db.asset_rows = {a: ("complete", "build") for a in GOOD}
    db.asset_rows["bg_ontology"] = ("complete", "skip_no_delta")
    code, ev = _verify(env, db, rec)
    assert code == 8 and "FORCE_DID_NOT_TAKE_EFFECT" in last(ev)["verification"]["codes"] and "do NOT dispatch again" in last(ev)["second_dispatch"]
    db.asset_rows = {a: ("complete", "build") for a in GOOD}
    db.asset_rows["bo_samskara"] = ("error", None)
    code, ev = _verify(env, db, rec)
    assert code == 10 and last(ev)["verification"]["assets_not_complete"] == ["bo_samskara"]
    db.run_state = "failed"
    db.asset_rows = None
    code, ev = _verify(env, db, rec)
    assert code == 10 and "RUN_NOT_COMPLETE" in last(ev)["verification"]["codes"]


def test_verify_run_refuses_a_run_that_is_not_this_tools(env):
    db = FakeDB()
    rec = _committed_receipt(env, db)
    db.run_row = {**db.run_row, "triggered_by": "someone-else"}
    code, ev = _verify(env, db, rec)
    assert code == 4 and refusal_pairs(ev) == [(None, "RECEIPT_RUN_MISMATCH")]


def test_a_committed_receipt_of_another_run_is_never_overwritten(env):
    db = FakeDB()
    _committed_receipt(env, db)
    code, ev = run(env, argv_for(env), db=FakeDB())
    assert code == 4 and refusal_pairs(ev) == [(None, "RECEIPT_PATH_INVALID")]


def test_rows_sql_is_the_waves_candidate_sql_plus_domain():
    assert asd.ROWS_SQL.replace("ar.domain, ar.rebuild_on_probe_fail, ", "", 1) == slw.CANDIDATES_SQL


# ───────────────────────── F1: cross-chart impact acceptance ─────────────────────────

def test_cross_chart_lit_rows_refuse_the_plan_until_each_chart_is_named_with_its_count(env):
    db = FakeDB(throughput=OTHER_ROWS)
    code, ev = run(env, argv_for(env), db=db)
    r = last(ev)["refusals"][0]
    assert code == 4 and r["code"] == "CROSS_CHART_IMPACT_NOT_ACCEPTED" and r["charts"] == {OTHER_A: 3, OTHER_B: 2}
    assert f"--accept-cross-chart-impact {OTHER_A}=3" in r["required_flags"] and any(OTHER_B in l for l in r["impact_lines"])
    assert db.inserts("build_runs") == []
    # the anchor chart's own rows and the global rows this run rebuilds are not impact
    assert CHART not in r["charts"] and "global" not in r["charts"]


def test_the_plan_prints_the_counts_once_accepted_and_the_token_binds_them(env):
    s = last(run(env, argv_for(env, *ACCEPT_ALL), db=FakeDB(throughput=OTHER_ROWS))[1])
    assert s["cross_chart_impact"]["by_chart"][OTHER_A]["lit_rows"] == 3 and s["cross_chart_impact"]["by_chart"][OTHER_B]["lit_rows"] == 2
    assert s["cross_chart_impact"]["total_lit_rows"] == 5 and s["cross_chart_impact_accepted"] == {OTHER_A: 3, OTHER_B: 2}
    assert s["cross_chart_impact_lines"][0].startswith("CROSS-CHART IMPACT") and re.fullmatch(r"[0-9a-f]{64}", s["impact_sha256"])
    # a different (or no) rows set is a different token; the accepted counts are bound too
    t = s["confirm_token"]
    pathlib.Path(env["receipt"]).unlink()
    s2 = last(run(env, argv_for(env, *ACCEPT_ALL), db=FakeDB(throughput=OTHER_ROWS + [lit("bo_samskara", OTHER_B)]))[1])
    assert s2["refusals"][0]["code"] == "CROSS_CHART_COUNT_MISMATCH"        # B has 3 lit rows now: a stale acceptance is refused
    base = dict(manifest_digest=_hex("m"), ids=["a"], anchor=CHART, image_sha=sha_of("i"), worker_limit=3, accepted_excluded=[], allow_redispatch=[])
    t1 = asd.build_confirm_token(**base, accepted_cross_chart={OTHER_A: 3}, impact_sha256=_hex("x"))
    assert t1 != asd.build_confirm_token(**base, accepted_cross_chart={OTHER_A: 4}, impact_sha256=_hex("x"))
    assert t1 != asd.build_confirm_token(**base, accepted_cross_chart={OTHER_A: 3}, impact_sha256=_hex("y"))
    assert t1 != asd.build_confirm_token(**base, accepted_cross_chart={}, impact_sha256=_hex("x")) and t


def test_wrong_count_and_unmatched_acceptances_are_refused(env):
    db = FakeDB(throughput=OTHER_ROWS)
    code, ev = run(env, argv_for(env, "--accept-cross-chart-impact", f"{OTHER_A}=9", "--accept-cross-chart-impact", f"{OTHER_B}=2"), db=db)
    assert code == 4 and [r["code"] for r in last(ev)["refusals"]] == ["CROSS_CHART_COUNT_MISMATCH"]
    code, ev = run(env, argv_for(env, *ACCEPT_ALL, "--accept-cross-chart-impact", "global=1"), db=db)
    assert code == 4 and [r["code"] for r in last(ev)["refusals"]] == ["ACCEPT_CROSS_CHART_UNMATCHED"]
    code, ev = run(env, argv_for(env, "--accept-cross-chart-impact", "not-a-chart=1"), db=db)
    assert code == 2


def test_an_unneeded_acceptance_without_global_assets_is_refused_and_no_global_means_no_impact(env):
    code, ev = run(env, argv_for(env, assets=["ga_panchanga"]), db=FakeDB(throughput=OTHER_ROWS))
    assert code == 0 and last(ev)["cross_chart_impact"]["by_chart"] == {}
    pathlib.Path(env["receipt"]).unlink()
    code, ev = run(env, argv_for(env, *ACCEPT_ALL, assets=["ga_panchanga"]), db=FakeDB(throughput=OTHER_ROWS))
    assert code == 4 and last(ev)["refusals"][0]["code"] == "ACCEPT_CROSS_CHART_UNMATCHED"


def test_global_rows_of_dependents_outside_the_plan_count_as_impact(env):
    reg = {**REG, "bg_dep_out": row("bg_dep_out", ["bg_ontology"], scope="global", layer="brahmagyan")}
    rows = OTHER_ROWS + [lit("bg_dep_out", None)]
    code, ev = run(env, argv_for(env, *ACCEPT_ALL), db=FakeDB(registry=reg, throughput=rows))
    assert code == 4 and last(ev)["refusals"][0]["charts"] == {"global": 1}
    code, ev = run(env, argv_for(env, *ACCEPT_ALL, "--accept-cross-chart-impact", "global=1"), db=FakeDB(registry=reg, throughput=rows))
    assert code == 0 and last(ev)["cross_chart_impact"]["by_chart"]["global"]["assets"] == ["bg_dep_out"]


def test_the_impact_is_reread_in_the_transaction_and_a_change_refuses_before_any_insert(env):
    db0 = FakeDB(throughput=OTHER_ROWS)
    tok = last(run(env, argv_for(env, *ACCEPT_ALL, worker_limit=3), db=db0)[1])["confirm_token"]
    pathlib.Path(env["receipt"]).unlink()
    db = FakeDB(throughput=OTHER_ROWS, impact_after_first=OTHER_ROWS[:-3])      # rows change after the plan-time read: impact_calls > 1
    code, ev = run(env, argv_for(env, *ACCEPT_ALL, worker_limit=3, commit=True, confirm=tok), db=db, dispatch=Dispatch())
    assert code == 4 and last(ev)["refusals"][0]["code"] == "IMPACT_CHANGED"
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds()


def test_job_project_region_and_job_worker_limit_are_bound_into_the_token(env):
    base = last(run(env, argv_for(env, "--job-worker-limit", "2"), db=FakeDB())[1])["confirm_token"]
    for extra in (["--job", "other-job"], ["--project", "other-p"], ["--region", "other-r"], ["--job-worker-limit", "3"]):
        pathlib.Path(env["receipt"]).unlink()
        argv = ["--job-worker-limit", "2"] + extra if extra[0] != "--job-worker-limit" else extra
        assert last(run(env, argv_for(env, *argv), db=FakeDB())[1])["confirm_token"] != base, extra


def test_job_worker_limit_poll_and_timeout_are_validated(env):
    code, ev = run(env, argv_for(env, "--job-worker-limit", "0"), db=FakeDB())
    assert code == 4 and last(ev)["refusals"][0]["code"] == "WORKER_LIMIT_INVALID"
    for bad in (["--poll-seconds", "0"], ["--run-timeout-seconds", "-1"]):
        code, ev = run(env, argv_for(env, *bad), db=FakeDB())
        assert code == 2


# ───────────────────────── F2: recovery (dispatch-existing / terminalise-run) ─────────────────────────

def _crashed_after_commit(env, *, worker_limit=3, keep_marker=False):
    """A committed run whose execute never happened: the dispatch raised KeyboardInterrupt-free 'kill' (modelled: the receipt on disk
    has the run id, no execution, and the DB row is still planned)."""
    db0 = FakeDB()
    tok = last(run(env, argv_for(env, worker_limit=worker_limit), db=db0)[1])["confirm_token"]
    db = FakeDB()

    class Killed(Dispatch):
        def __call__(self, run_id):
            self.calls.append(run_id)
            raise KeyboardInterrupt
    code, ev = run(env, argv_for(env, commit=True, confirm=tok, worker_limit=worker_limit), db=db, dispatch=Killed())
    assert code == 7
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert rec["committed"] is True and rec["run_id"] and rec["execution_name"] is None
    if rec.get("dispatch_intended_at"):                # the kill happened INSIDE the execute: keep the marker only when asked
        if not keep_marker:
            rec.pop("dispatch_intended_at")
            pathlib.Path(env["receipt"]).write_text(json.dumps(rec))
    db.run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "planned", "triggered_by": rec["triggered_by"],
                  "plan_manifest_digest": rec["manifest_digest"]}
    return db, rec, tok


def _existing_args(env, rec, tok, *, worker_limit=3, mode="dispatch", confirm=True, commit=True, extra=()):
    argv = ["--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"], "--deployed-sha", "deadbeef",
            "--deployed-job-sha", "deadbeef", "--worker-limit", str(worker_limit)]
    argv += ["--dispatch-existing", rec["run_id"]] if mode == "dispatch" else ["--terminalise-run", rec["run_id"]]
    if commit:
        argv += ["--commit"] + (["--confirm", tok] if confirm else [])
    return asd.build_parser().parse_args(argv + list(extra))


def test_dispatch_existing_executes_the_planned_run_once_with_the_same_token_and_no_insert(env):
    db, rec, tok = _crashed_after_commit(env)
    db.log.clear()
    disp = Dispatch()
    code, ev = run(env, _existing_args(env, rec, tok), db=db, dispatch=disp)
    assert code == 0 and disp.calls == [rec["run_id"]] and db.inserts("build_runs") == [] and db.inserts("build_run_assets") == []
    assert [e["event"] for e in ev][:2] == ["run_dispatching_existing", "run_dispatched"]
    assert json.loads(pathlib.Path(env["receipt"]).read_text())["execution_name"]


def test_dispatch_existing_refuses_a_wrong_token_a_non_planned_run_a_foreign_run_and_a_second_execution(env):
    db, rec, tok = _crashed_after_commit(env)
    disp = Dispatch()
    code, ev = run(env, _existing_args(env, rec, "ASSETSET75_000000000000_FORCE_ASSET_SET_REBUILD"), db=db, dispatch=disp)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "CONFIRM_TOKEN_MISMATCH" and disp.calls == []
    code, ev = run(env, _existing_args(env, rec, tok, worker_limit=4), db=db, dispatch=disp)          # other limit: another token
    assert code == 4 and disp.calls == []
    db.run_row = {**db.run_row, "state": "running"}
    code, ev = run(env, _existing_args(env, rec, tok), db=db, dispatch=disp)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "RUN_NOT_PLANNED" and disp.calls == []
    db.run_row = {**db.run_row, "state": "planned", "triggered_by": "someone-else"}
    code, ev = run(env, _existing_args(env, rec, tok), db=db, dispatch=disp)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "RECEIPT_RUN_MISMATCH" and disp.calls == []
    db.run_row = {**db.run_row, "triggered_by": rec["triggered_by"]}
    code, ev = run(env, _existing_args(env, rec, tok, commit=False), db=db, dispatch=disp)
    assert code == 2
    assert run(env, _existing_args(env, rec, tok), db=db, dispatch=disp)[0] == 0 and len(disp.calls) == 1
    code, ev = run(env, _existing_args(env, rec, tok), db=db, dispatch=disp)                          # the receipt now records the execution
    assert code == 4 and last(ev)["refusals"][0]["code"] == "ALREADY_EXECUTED_PER_RECEIPT" and len(disp.calls) == 1


def test_dispatch_existing_refuses_when_the_plan_moved_since_the_commit(env):
    db, rec, tok = _crashed_after_commit(env)
    changed = {"bo_laksana": {**REG["bo_laksana"], "depends_on": ["ga_sensitive"]}}
    db2 = FakeDB(registry={**REG, **changed})
    db2.run_row = db.run_row
    disp = Dispatch()
    code, ev = run(env, _existing_args(env, rec, tok), db=db2, dispatch=disp)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "CONFIRM_TOKEN_MISMATCH" and disp.calls == []
    # even with the NEW plan's own token the receipt's token is the authority
    env2 = {**env, "receipt": str(pathlib.Path(env["receipt"]).with_name("other_receipt.json"))}
    new_tok = last(run(env2, argv_for(env2, worker_limit=3), db=db2)[1])["confirm_token"]
    assert new_tok != tok
    code, ev = run(env, _existing_args(env, rec, new_tok), db=db2, dispatch=disp)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "TOKEN_DIFFERS_FROM_RECEIPT" and disp.calls == []


def test_terminalise_run_prints_a_token_then_cancels_only_a_planned_run_of_this_tool(env):
    db, rec, tok = _crashed_after_commit(env)
    code, ev = run(env, _existing_args(env, rec, None, mode="terminalise", commit=False), db=db)
    s = last(ev)
    assert code == 0 and s["committed"] is False and s["confirm_token"] == f"TERMINALISE_{rec['run_id'][:8].upper()}_NO_EXECUTION_STARTED"
    assert not any(e[1].startswith("WITH failed_run AS") for e in db.statements())
    code, ev = run(env, _existing_args(env, rec, "wrong", mode="terminalise"), db=db)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "CONFIRM_TOKEN_MISMATCH"
    code, ev = run(env, _existing_args(env, rec, s["confirm_token"], mode="terminalise"), db=db)
    assert code == 0 and last(ev)["terminalised"] is True and any(e[1].startswith("WITH failed_run AS") for e in db.statements())
    assert json.loads(pathlib.Path(env["receipt"]).read_text())["verification"]["codes"] == ["TERMINALISED_BY_OPERATOR"]


def test_terminalise_run_refuses_a_started_run_and_reports_zero_rows_honestly(env):
    db, rec, tok = _crashed_after_commit(env)
    db.run_row = {**db.run_row, "state": "running"}
    code, ev = run(env, _existing_args(env, rec, "x", mode="terminalise"), db=db)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "RUN_NOT_PLANNED"
    db.run_row = {**db.run_row, "state": "planned"}
    db.terminalise_rows = 0                                                  # it started between the read and the UPDATE
    code, ev = run(env, _existing_args(env, rec, f"TERMINALISE_{rec['run_id'][:8].upper()}_NO_EXECUTION_STARTED", mode="terminalise"), db=db)
    assert code == 6 and last(ev)["terminalised"] is False and "NOT terminalised" in last(ev)["warning"]


# ───────────────────────── F3 / F5: verification detector, surviving mutations, --wait ─────────────────────────

def test_verify_run_reads_the_throughput_state_not_only_build_run_assets_state(env):
    db = FakeDB()
    rec = _committed_receipt(env, db)
    db.throughput_states = {"ga_sensitive": "incomplete"}                    # build_run_assets.state is 'complete' for it (runner F-01)
    code, ev = _verify(env, db, rec)
    v = last(ev)["verification"]
    assert code == 10 and "ASSET_THROUGHPUT_NOT_LIT" in v["codes"] and v["assets_throughput_not_lit"] == ["ga_sensitive"] and v["complete"] is False


def test_an_outside_dependency_that_goes_stale_between_plan_and_insert_refuses_in_the_transaction(env):
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    db = FakeDB(deps_after_first={"bg_panchanga": (None, None, "service")})        # the precheck passed; the in-transaction recheck sees it gone
    disp = Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=tok, worker_limit=3), db=db, dispatch=disp)
    assert code == 4 and [c for _a, c in refusal_pairs(ev)] == ["DEPENDENCY_NOT_READY"]
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds() and disp.calls == []


def test_a_job_sha_change_after_the_insert_stops_the_dispatch_and_terminalises(env):
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    pathlib.Path(env["receipt"]).unlink()
    db = FakeDB(on_insert=lambda: env["live"].queue.append(sha_of("a redeploy")))
    disp = Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=tok, worker_limit=3), db=db, dispatch=disp)
    e = [x for x in ev if x["event"] == "dispatch_failed"][0]
    assert code == 3 and "JOB_SHA_CHANGED" in e["error"] and disp.calls == [] and e["terminalised"] is True
    assert any(s[1].startswith("WITH failed_run AS") for s in db.statements())


def test_commit_with_wait_verifies_the_run_and_records_it_in_the_receipt(env):
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    pathlib.Path(env["receipt"]).unlink()
    db, disp = FakeDB(), Dispatch()
    code, ev = run(env, argv_for(env, "--wait", commit=True, confirm=tok, worker_limit=3), db=db, dispatch=disp)
    s = last(ev)
    assert code == 0 and s["verification"]["verdict"] == "PASS" and s["verification"]["assets_complete"] == 7
    assert json.loads(pathlib.Path(env["receipt"]).read_text())["verification"]["verdict"] == "PASS"
    pathlib.Path(env["receipt"]).unlink()
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    pathlib.Path(env["receipt"]).unlink()
    code, ev = run(env, argv_for(env, "--wait", commit=True, confirm=tok, worker_limit=3),
                   db=FakeDB(asset_rows={**{a: ("complete", "build") for a in GOOD}, "bg_ontology": ("complete", "skip_no_delta")}), dispatch=Dispatch())
    assert code == 8 and "do NOT dispatch again" in last(ev)["second_dispatch"]


# ───────────────────────── delta review: R1 / R2 / R3 / R5 / T1 / T2 ─────────────────────────

def _receipt(env):
    return json.loads(pathlib.Path(env["receipt"]).read_text())


def test_t1_non_lit_rows_of_other_charts_are_not_impact(env):
    rows = OTHER_ROWS + [lit("bo_samskara", OTHER_A, "stale"), lit("ga_sensitive", OTHER_B, "error"), lit("bo_laksana", OTHER_B, "incomplete"),
                         lit("bo_laksana", OTHER_A, "dormant")]
    s = last(run(env, argv_for(env, *ACCEPT_ALL), db=FakeDB(throughput=rows))[1])
    assert s["cross_chart_impact"]["by_chart"][OTHER_A]["lit_rows"] == 3 and s["cross_chart_impact"]["by_chart"][OTHER_B]["lit_rows"] == 2


def test_t2_a_run_whose_manifest_digest_differs_from_the_receipt_is_not_ours(env):
    db, rec, tok = _crashed_after_commit(env)
    db.run_row = {**db.run_row, "plan_manifest_digest": _hex("another manifest")}
    for args in (_existing_args(env, rec, tok), _existing_args(env, rec, "x", mode="terminalise")):
        code, ev = run(env, args, db=db, dispatch=Dispatch())
        assert code == 4 and last(ev)["refusals"][0]["code"] == "RECEIPT_RUN_MISMATCH"


def test_r1_an_unknown_commit_outcome_writes_the_run_id_into_the_receipt_and_recovery_works(env):
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    db = FakeDB(fail_commit=True)
    code, ev = run(env, argv_for(env, commit=True, confirm=tok, worker_limit=3), db=db, dispatch=Dispatch())
    rec = _receipt(env)
    assert code == 6 and rec["run_id"] == db.inserted_run[0] == last(ev)["run_id"] and rec["committed"] == "unknown"
    db.run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "planned", "triggered_by": rec["triggered_by"],
                  "plan_manifest_digest": rec["manifest_digest"]}            # the COMMIT had in fact landed
    db.fail_commit = False
    code, ev = run(env, _existing_args(env, rec, None, mode="terminalise", commit=False), db=db)
    assert code == 0 and last(ev)["confirm_token"].startswith("TERMINALISE_")
    code, ev = run(env, _existing_args(env, rec, f"TERMINALISE_{rec['run_id'][:8].upper()}_NO_EXECUTION_STARTED", mode="terminalise"), db=db)
    assert code == 0 and last(ev)["terminalised"] is True
    # ... and when the COMMIT had NOT landed there is no such run: refused
    pathlib.Path(env["receipt"]).unlink()
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    db2 = FakeDB(fail_commit=True)
    run(env, argv_for(env, commit=True, confirm=tok, worker_limit=3), db=db2, dispatch=Dispatch())
    rec2 = _receipt(env)
    code, ev = run(env, _existing_args(env, rec2, "x", mode="terminalise"), db=FakeDB())            # no row in the database
    assert code == 4 and last(ev)["refusals"][0]["code"] == "RECEIPT_RUN_MISMATCH"


def test_r1_a_kill_between_commit_and_the_receipt_write_is_recoverable_from_the_database_row(env):
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    rec = _receipt(env)
    assert rec["committed"] is False and rec["run_id"] is None                    # what a SIGKILL right after COMMIT leaves on disk
    db = FakeDB()
    run_id = "6b1e0c1a-0000-4000-8000-0000000000aa"
    db.run_row = {"id": run_id, "chart_id": CHART, "state": "planned", "triggered_by": rec["triggered_by"],
                  "plan_manifest_digest": rec["manifest_digest"]}
    rec["run_id"] = run_id                                                          # the operator reads the id from the database (runbook)
    args = _existing_args(env, {**rec}, tok)
    disp = Dispatch()
    rec_disk = _receipt(env)
    assert rec_disk["run_id"] is None
    code, ev = run(env, args, db=db, dispatch=disp)
    assert code == 0 and disp.calls == [run_id] and _receipt(env)["run_id"] == run_id and _receipt(env)["committed"] is True


def test_r2_the_marker_is_written_before_the_execute_and_blocks_a_second_execute_unless_named(env):
    db, rec, tok = _crashed_after_commit(env, keep_marker=True)         # a kill INSIDE the execute: the marker is on disk, no execution recorded
    assert _receipt(env)["dispatch_intended_at"] and _receipt(env)["execution_name"] is None
    disp = Dispatch()
    code, ev = run(env, _existing_args(env, rec, tok), db=db, dispatch=disp)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "DISPATCH_ALREADY_ATTEMPTED" and disp.calls == []
    other = "6b1e0c1a-0000-4000-8000-0000000000bb"
    code, ev = run(env, _existing_args(env, rec, tok, extra=("--allow-redispatch", other)), db=db, dispatch=disp)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "DISPATCH_ALREADY_ATTEMPTED"       # it must name THIS run
    code, ev = run(env, _existing_args(env, rec, tok, extra=("--allow-redispatch", rec["run_id"])), db=db, dispatch=disp)
    assert code == 0 and disp.calls == [rec["run_id"]]


def test_r2_the_marker_is_on_disk_before_gcloud_runs(env):
    seen = []

    class Probe(Dispatch):
        def __call__(self, run_id):
            seen.append(_receipt(env).get("dispatch_intended_at"))
            return super().__call__(run_id)
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    code, ev = run(env, argv_for(env, commit=True, confirm=tok, worker_limit=3), db=FakeDB(), dispatch=Probe())
    assert code == 0 and seen and seen[0] == T0.isoformat(timespec="seconds")


def test_r2_a_receipt_write_failure_after_the_execute_reports_the_execution_and_a_retry_is_refused(env, monkeypatch):
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    real = asd.write_receipt
    calls = {"n": 0}

    def flaky(path, doc):
        calls["n"] += 1
        if doc.get("execution_name"):
            raise OSError("disk full")
        return real(path, doc)
    monkeypatch.setattr(asd, "write_receipt", flaky)
    db, disp = FakeDB(), Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=tok, worker_limit=3), db=db, dispatch=disp)
    names = [e["event"] for e in ev]
    assert code == 6 and "run_dispatched" in names and len(disp.calls) == 1
    assert "brahma-build-pipeline-job-exec-1" in json.dumps(last(ev)) and "disk full" in json.dumps(last(ev))
    monkeypatch.setattr(asd, "write_receipt", real)
    rec = _receipt(env)
    assert rec["dispatch_intended_at"] and rec["execution_name"] is None            # the marker survived: a retry cannot execute again
    db.run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "planned", "triggered_by": rec["triggered_by"],
                  "plan_manifest_digest": rec["manifest_digest"]}
    code, ev = run(env, _existing_args(env, rec, tok), db=db, dispatch=disp)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "DISPATCH_ALREADY_ATTEMPTED" and len(disp.calls) == 1


def test_r2_recovery_modes_do_not_say_no_run_was_committed(env):
    db, rec, tok = _crashed_after_commit(env)

    class Interrupted(Dispatch):
        def __call__(self, run_id):
            raise KeyboardInterrupt
    code, ev = run(env, _existing_args(env, rec, tok), db=db, dispatch=Interrupted())
    w = last(ev)["warning"]
    assert code == 7 and rec["run_id"] in w and "no run id is known" not in w
    pathlib.Path(env["receipt"]).write_text(json.dumps({**_receipt(env), "dispatch_intended_at": None}))
    code, ev = run(env, _existing_args(env, rec, tok, extra=("--allow-redispatch", "not-a-uuid")), db=db, dispatch=Dispatch())
    assert code == 2


def test_r2_a_second_process_on_the_same_receipt_is_refused_by_the_lock(env):
    import fcntl
    tok = last(run(env, argv_for(env, worker_limit=3), db=FakeDB())[1])["confirm_token"]
    pathlib.Path(env["receipt"]).unlink()
    with open(env["receipt"] + ".lock", "w") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        db, disp = FakeDB(), Dispatch()
        code, ev = run(env, argv_for(env, commit=True, confirm=tok, worker_limit=3), db=db, dispatch=disp)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "RECEIPT_LOCKED" and db.inserts("build_runs") == [] and disp.calls == []


def test_r3_terminalise_refuses_when_the_receipt_records_an_execution_unless_the_run_is_named(env):
    db, rec, tok = _crashed_after_commit(env)
    r = _receipt(env)
    r["execution_name"] = "brahma-build-pipeline-job-exec-9"
    pathlib.Path(env["receipt"]).write_text(json.dumps(r))
    token = f"TERMINALISE_{rec['run_id'][:8].upper()}_NO_EXECUTION_STARTED"
    code, ev = run(env, _existing_args(env, rec, None, mode="terminalise", commit=False), db=db)
    assert code == 0 and "exec-9" in json.dumps(last(ev)["execution_recorded"])           # plan mode warns
    code, ev = run(env, _existing_args(env, rec, token, mode="terminalise"), db=db)
    assert code == 4 and last(ev)["refusals"][0]["code"] == "EXECUTION_RECORDED_IN_RECEIPT"
    assert not any(e[1].startswith("WITH failed_run AS") for e in db.statements())
    code, ev = run(env, _existing_args(env, rec, token, mode="terminalise", extra=("--allow-redispatch", rec["run_id"])), db=db)
    assert code == 0 and last(ev)["terminalised"] is True


def test_r5_bad_run_ids_and_non_ascii_digits_are_bad_input_not_unexpected(env):
    for flag in ("--verify-run", "--dispatch-existing", "--terminalise-run"):
        args = asd.build_parser().parse_args(["--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"], flag, "nope"]
                                             + (["--commit"] if flag == "--dispatch-existing" else []))
        code, ev = run(env, args, db=FakeDB())
        assert code == 2, flag
    code, ev = run(env, argv_for(env, "--accept-cross-chart-impact", f"{OTHER_A}=\u00b2"), db=FakeDB())
    assert code == 2


# ───────────────────────── family override (--allow-family-assets, SS N-443 D3) ─────────────────────────
# The override waives EXACTLY FAMILY_ASSET and SPLITS_FAMILY, ONLY for the named ids; it is bound into the token, the receipt and the log.
# With the flag absent every output is what it was before the flag existed (the GOLDEN_* constants were captured from the old code).

FX = json.loads((HERE / "_asset_set_family_override_fixture.json").read_text())
FX_ROWS = {r["asset_id"]: r for r in FX["rows"]}
FAMILY_FILE = json.loads((REPO / "00_ARCHITECTURE" / "control" / "FAMILY_ASSETS.json").read_text())
FAMILY_REAL = {"state": "present", "family_set": frozenset(FAMILY_FILE["family_set"]),
               "families": {k: frozenset(FAMILY_FILE[k]) for k in slw.FAMILY_LIST_KEYS}}
ALL_LAYERS = "brahmagyan,ganita,bodha,kala,phala,mimamsa"
FAMILY_FLAG = "--allow-family-assets"
FAM_MIN = {"state": "present", "family_set": frozenset({"fam_a", "fam_b", "fam_c"}),
           "families": {**{k: frozenset() for k in slw.FAMILY_LIST_KEYS}, "family_gochara": frozenset({"fam_a", "fam_b", "fam_c"})}}
FAMILY_CODES = {"FAMILY_ASSET", "SPLITS_FAMILY"}

GOLDEN_UNIT_TOKEN = "ASSETSET2_0F753BD8FEF8_FORCE_ASSET_SET_REBUILD"
GOLDEN_PLAN_TOKEN = "ASSETSET7_AC8EC62423B3_FORCE_ASSET_SET_REBUILD"
GOLDEN_SUMMARY_KEYS = sorted("""action anchor_chart anchor_is_canonical asset_count assets committed committed_runs confirm_token connection_budget
cross_chart_impact cross_chart_impact_accepted cross_chart_impact_lines dispatch_command_preview event excluded_accepted execution_env_override
external_dependencies force_execute global_assets impact_sha256 insert job_image_check layer_counts locks manifest_digest
out_of_set_intermediates_at_risk receipt_path runbook_gates_not_in_tool runtime_estimate schema scope target triggered_by wave_count wave_widths
waves worker_limit_override""".split())
GOLDEN_RECEIPT_KEYS = sorted("""anchor_chart assets committed committed_at confirm_token connection_budget cross_chart_impact excluded_accepted
execution_name image_sha impact_sha256 inputs inventory_sha manifest_digest planned_at run_id schema target triggered_by verification waves
worker_limit""".split())
GOLDEN_INPUT_KEYS = ["accept_cross_chart", "accept_excluded", "allow_redispatch", "requested"]


def _codes(findings, asset):
    return sorted(f["code"] for f in findings if f["asset"] == asset)


def _fam_rows(**over):
    base = {"fam_a": row("fam_a"), "fam_b": row("fam_b"), "ok_1": row("ok_1")}
    base.update(over)
    return list(base.values())


# ── pure classifier ──

def test_the_waiver_applies_only_to_the_named_ids_and_covers_both_family_codes():
    ids = ["fam_a", "fam_b", "ok_1"]
    plain = asd.classify_assets(ids, _fam_rows(), FAM_MIN)
    assert _codes(plain, "fam_a") == ["FAMILY_ASSET", "SPLITS_FAMILY"] and _codes(plain, "fam_b") == ["FAMILY_ASSET", "SPLITS_FAMILY"]
    waived = asd.classify_assets(ids, _fam_rows(), FAM_MIN, allow_family=["fam_a"])
    assert _codes(waived, "fam_a") == []                                                    # both codes waived for the named id
    assert _codes(waived, "fam_b") == ["FAMILY_ASSET", "SPLITS_FAMILY"]                     # the id that is not named is refused as before
    assert _codes(waived, "ok_1") == []
    assert asd.classify_assets(ids, _fam_rows(), FAM_MIN, allow_family=["fam_a", "fam_b"]) == []


def test_the_name_pattern_family_is_waived_for_a_named_id_too():
    rows = [row("bg_gochara_arcs", scope="global", layer="brahmagyan")]
    assert _codes(asd.classify_assets(["bg_gochara_arcs"], rows, {"state": "absent"}), "bg_gochara_arcs") == ["FAMILY_ASSET"]
    assert asd.classify_assets(["bg_gochara_arcs"], rows, {"state": "absent"}, allow_family=["bg_gochara_arcs"]) == []


@pytest.mark.parametrize("over,protected,expected", [
    (row("fam_a", active=False), (), ["NOT_ACTIVE"]),
    (row("fam_a", kind="service", writer=False), (), ["NO_WRITER", "SERVICE_ASSET"]),
    (row("fam_a", writer=False), (), ["NO_WRITER"]),
    (row("fam_a", probe=True), (), ["FORCE_BYPASSED_BY_PROBE"]),
    (row("fam_a", layer="kala"), (), ["LAYER_NOT_ALLOWED"]),
    (row("fam_a", scope="mixed"), (), ["SCOPE_NOT_ALLOWED"]),
    (row("fam_a"), ("fam_a",), ["PROTECTED_ASSET"]),
])
def test_every_other_refusal_still_fires_for_a_named_family_id(over, protected, expected):
    f = asd.classify_assets(["fam_a", "fam_b", "ok_1"], _fam_rows(fam_a=over), FAM_MIN, protected=protected, allow_family=["fam_a", "fam_b"])
    assert _codes(f, "fam_a") == expected and _codes(f, "fam_b") == []


def test_the_family_names_are_validated_requested_member_and_not_also_excluded():
    ids = ["fam_a", "fam_b", "ok_1"]
    asd.validate_allow_family(ids, ["fam_a", "fam_b"], FAM_MIN)                              # exact list: no refusal
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        asd.validate_allow_family(ids, ["fam_c", "ok_1", "fam_a", "no_such_x"], FAM_MIN, accept_excluded=["fam_a"])
    got = sorted((r["asset"], r["code"]) for r in exc.value.refusals)
    assert got == [("fam_a", "ACCEPT_FAMILY_ALSO_EXCLUDED"), ("fam_c", "ACCEPT_FAMILY_NOT_REQUESTED"),
                   ("no_such_x", "ACCEPT_FAMILY_NOT_REQUESTED"), ("ok_1", "ACCEPT_FAMILY_NOT_FAMILY")]


# ── token ──

def test_the_token_changes_with_the_family_list_and_is_unchanged_without_it():
    base = dict(manifest_digest=_hex("m"), ids=["a", "b"], anchor=CHART, image_sha=sha_of("i"), worker_limit=4, accepted_excluded=[],
                allow_redispatch=[])
    assert asd.build_confirm_token(**base) == GOLDEN_UNIT_TOKEN                              # captured from the code before the flag existed
    assert asd.build_confirm_token(**base, allow_family=[]) == GOLDEN_UNIT_TOKEN              # empty list == absent flag
    a = asd.build_confirm_token(**base, allow_family=["a"])
    ab = asd.build_confirm_token(**base, allow_family=["a", "b"])
    assert len({GOLDEN_UNIT_TOKEN, a, ab}) == 3                                              # a different list is a different token
    assert ab == asd.build_confirm_token(**base, allow_family=["b", "a"])                    # the list is a set: order-free
    assert asd.build_confirm_token(**base, allow_family=["b"]) != a


# ── the CLI, small registry ──

def _world(env, extra_rows=None, *, family_set=("bg_gochara_arcs",), registry_over=None):
    reg = {**REG, **(extra_rows or {}), **(registry_over or {})}
    digests = {a: _hex(a) for a in reg}
    (pathlib.Path(env["repo"]) / "platform" / "src" / "generated" / "nirmana-writer-digests.json").write_text(
        json.dumps({"version": 1, "writers": digests}))
    return FakeDB(registry=reg), FakeGit(deployed=digests, family_set=family_set)


def _token_without_or_with(s, allow):
    return asd.build_confirm_token(manifest_digest=s["manifest_digest"], ids=s["assets"], anchor=CHART,
                                   image_sha=s["job_image_check"]["deployed_job_sha"], worker_limit=None, accepted_excluded=[],
                                   allow_redispatch=[], accepted_cross_chart={}, impact_sha256=s["impact_sha256"], job="brahma-build-pipeline-job",
                                   project="madhav-astrology", region="asia-south1", job_worker_limit=None, allow_family=allow)


def test_the_plan_with_the_flag_records_the_override_everywhere_and_the_token_binds_it(env, capsys):
    ids = GOOD + ["bg_gochara_arcs"]
    db, git = _world(env)
    code, ev = run(env, argv_for(env, assets=ids), db=db, git=git)                           # without the flag: refused, as before
    assert code == 4 and refusal_pairs(ev) == [("bg_gochara_arcs", "FAMILY_ASSET")]
    capsys.readouterr()
    code, ev = run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs", assets=ids), db=db, git=git)
    assert code == 0, ev
    s = last(ev)
    assert [e["event"] for e in ev] == ["family_override", "summary"]
    assert ev[0]["ids"] == ["bg_gochara_arcs"] and ev[0]["waives"] == ["FAMILY_ASSET", "SPLITS_FAMILY"]
    assert ev[0]["line"] == "family-override: bg_gochara_arcs"
    assert "family-override: bg_gochara_arcs" in capsys.readouterr().err                     # the plain log line
    assert s["family_override"]["ids"] == ["bg_gochara_arcs"] and s["family_override"]["line"] == "family-override: bg_gochara_arcs"
    assert "bg_gochara_arcs" in s["assets"] and s["asset_count"] == len(ids)
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert rec["family_override"] == ["bg_gochara_arcs"] and rec["inputs"]["allow_family"] == ["bg_gochara_arcs"]
    # the list is part of the token: the printed token is the one WITH the list, and not the one without it
    assert _token_without_or_with(s, ["bg_gochara_arcs"]) == s["confirm_token"]
    assert _token_without_or_with(s, []) != s["confirm_token"]


def test_only_the_named_family_id_is_waived_the_other_family_id_and_split_members_still_refuse(env):
    aux = {"bg_gochara_aux": row("bg_gochara_aux", scope="global", layer="brahmagyan")}
    db, git = _world(env, aux, family_set=("bg_gochara_arcs", "bg_gochara_aux", "bg_gochara_unrequested"))
    ids = GOOD + ["bg_gochara_arcs", "bg_gochara_aux"]
    code, ev = run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs", assets=ids), db=db, git=git)
    assert code == 4
    assert refusal_pairs(ev) == [("bg_gochara_aux", "FAMILY_ASSET"), ("bg_gochara_aux", "SPLITS_FAMILY")]
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds()


@pytest.mark.parametrize("over,code_", [
    ({"bg_gochara_arcs": row("bg_gochara_arcs", scope="global", layer="brahmagyan", active=False)}, "NOT_ACTIVE"),
    ({"bg_gochara_arcs": row("bg_gochara_arcs", scope="global", layer="brahmagyan", writer=False)}, "NO_WRITER"),
    ({"bg_gochara_arcs": row("bg_gochara_arcs", scope="global", layer="brahmagyan", probe=True)}, "FORCE_BYPASSED_BY_PROBE"),
    ({"bg_gochara_arcs": row("bg_gochara_arcs", scope="global", layer="kala")}, "LAYER_NOT_ALLOWED"),
])
def test_a_named_family_id_that_trips_another_refusal_is_still_refused(env, over, code_):
    db, git = _world(env, registry_over=over)
    code, ev = run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs", assets=GOOD + ["bg_gochara_arcs"]), db=db, git=git)
    assert code == 4 and (("bg_gochara_arcs", code_) in refusal_pairs(ev))
    assert not any(c in FAMILY_CODES for _a, c in refusal_pairs(ev))
    assert db.inserts("build_runs") == []


def test_protected_family_id_is_still_refused(env):
    db, git = _world(env)
    db.protected = ["bg_gochara_arcs"]
    code, ev = run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs", assets=GOOD + ["bg_gochara_arcs"]), db=db, git=git)
    assert code == 4 and refusal_pairs(ev) == [("bg_gochara_arcs", "PROTECTED_ASSET")]


def test_unknown_unrequested_non_family_and_excluded_names_refuse_and_insert_nothing(env):
    db, git = _world(env)
    ids = GOOD + ["bg_gochara_arcs"]
    for extra, pair in ((("ga_sensitive",), ("ga_sensitive", "ACCEPT_FAMILY_NOT_FAMILY")),
                        (("bg_transit_rules",), ("bg_transit_rules", "ACCEPT_FAMILY_NOT_REQUESTED")),
                        (("no_such_asset",), ("no_such_asset", "ACCEPT_FAMILY_NOT_REQUESTED"))):
        code, ev = run(env, argv_for(env, FAMILY_FLAG, ",".join(("bg_gochara_arcs",) + extra), assets=ids), db=db, git=git)
        assert code == 4 and refusal_pairs(ev) == [pair], extra
    code, ev = run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs", "--accept-excluded", "bg_gochara_arcs", assets=ids), db=db, git=git)
    assert code == 4 and refusal_pairs(ev) == [("bg_gochara_arcs", "ACCEPT_FAMILY_ALSO_EXCLUDED")]
    code, ev = run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs,bg_gochara_arcs", assets=ids), db=db, git=git)
    assert code == 2                                                                         # the same id twice is bad input
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds()


def test_commit_needs_the_flagged_plan_token_and_records_the_override_in_events_and_receipt(env):
    ids = GOOD + ["bg_gochara_arcs"]
    db0, git = _world(env)
    s = last(run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs", assets=ids, worker_limit=3), db=db0, git=git)[1])
    pathlib.Path(env["receipt"]).unlink()
    tok = s["confirm_token"]
    # the same token without the flag cannot run (the family id is refused again, and the token is a different one): nothing is inserted
    db = FakeDB(registry=db0.registry)
    code, ev = run(env, argv_for(env, assets=ids, commit=True, confirm=tok, worker_limit=3), db=db, git=git, dispatch=Dispatch())
    assert code == 4 and db.inserts("build_runs") == [] and "commit" not in db.kinds()
    # a wrong token with the flag
    code, ev = run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs", assets=ids, commit=True, confirm=GOLDEN_PLAN_TOKEN, worker_limit=3),
                   db=db, git=git, dispatch=Dispatch())
    assert code == 4 and refusal_pairs(ev) == [(None, "CONFIRM_TOKEN_MISMATCH")] and db.inserts("build_runs") == []
    disp = Dispatch()
    code, ev = run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs", assets=ids, commit=True, confirm=tok, worker_limit=3), db=db, git=git,
                   dispatch=disp)
    assert code == 0 and len(disp.calls) == 1 and len(db.inserts("build_runs")) == 1
    by = {e["event"]: e for e in ev}
    assert by["run_committed"]["family_override"] == ["bg_gochara_arcs"] and by["run_dispatched"]["family_override"] == ["bg_gochara_arcs"]
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert rec["committed"] is True and rec["confirm_token"] == tok
    assert rec["family_override"] == ["bg_gochara_arcs"] and rec["inputs"]["allow_family"] == ["bg_gochara_arcs"]


def _crashed_flagged(env):
    ids = GOOD + ["bg_gochara_arcs"]
    db0, git = _world(env)
    tok = last(run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs", assets=ids, worker_limit=3), db=db0, git=git)[1])["confirm_token"]
    pathlib.Path(env["receipt"]).unlink()
    db = FakeDB(registry=db0.registry)

    class Killed(Dispatch):
        def __call__(self, run_id):
            self.calls.append(run_id)
            raise KeyboardInterrupt
    code, _ev = run(env, argv_for(env, FAMILY_FLAG, "bg_gochara_arcs", assets=ids, commit=True, confirm=tok, worker_limit=3), db=db, git=git,
                    dispatch=Killed())
    assert code == 7
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    rec.pop("dispatch_intended_at", None)
    pathlib.Path(env["receipt"]).write_text(json.dumps(rec))
    db.run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "planned", "triggered_by": rec["triggered_by"],
                  "plan_manifest_digest": rec["manifest_digest"]}
    return db, git, rec, tok


def test_dispatch_existing_takes_the_family_list_from_the_receipt_and_refuses_the_flag_and_a_tampered_list(env):
    db, git, rec, tok = _crashed_flagged(env)
    assert rec["inputs"]["allow_family"] == ["bg_gochara_arcs"]
    # the flag is not accepted in recovery mode: the receipt is the source
    code, ev = run(env, _existing_args(env, rec, tok, extra=[FAMILY_FLAG, "bg_gochara_arcs"]), db=db, git=git, dispatch=Dispatch())
    assert code == 2
    # a receipt whose list was edited cannot be executed (the family id is refused again)
    good_rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    bad = json.loads(json.dumps(good_rec))
    bad["inputs"]["allow_family"] = []
    pathlib.Path(env["receipt"]).write_text(json.dumps(bad))
    disp = Dispatch()
    code, ev = run(env, _existing_args(env, rec, tok), db=db, git=git, dispatch=disp)
    assert code == 4 and disp.calls == [] and ("bg_gochara_arcs", "FAMILY_ASSET") in refusal_pairs(ev)
    # the untouched receipt executes once, with the same token, and no new INSERT
    pathlib.Path(env["receipt"]).write_text(json.dumps(good_rec))
    db.log.clear()
    code, ev = run(env, _existing_args(env, rec, tok), db=db, git=git, dispatch=disp)
    assert code == 0 and disp.calls == [rec["run_id"]] and db.inserts("build_runs") == []
    assert [e["event"] for e in ev][:3] == ["family_override", "run_dispatching_existing", "run_dispatched"]
    assert ev[0]["ids"] == ["bg_gochara_arcs"]


def test_a_receipt_without_a_family_list_still_works_in_recovery_mode(env):
    db, rec, tok = _crashed_after_commit(env)                                                  # an unflagged run: no allow_family anywhere
    on_disk = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert "allow_family" not in on_disk["inputs"] and "family_override" not in on_disk
    db.log.clear()
    code, ev = run(env, _existing_args(env, rec, tok), db=db, dispatch=Dispatch())
    assert code == 0 and "family_override" not in [e["event"] for e in ev]


# ── flag absent: byte-for-byte the old behaviour ──

def test_without_the_flag_token_summary_receipt_and_events_are_exactly_what_they_were(env, capsys):
    code, ev = run(env, argv_for(env, *ACCEPT_ALL, worker_limit=4), db=FakeDB(throughput=OTHER_ROWS))
    assert code == 0
    assert [e["event"] for e in ev] == ["summary"]
    s = last(ev)
    assert s["confirm_token"] == GOLDEN_PLAN_TOKEN                                           # token captured from the code before the flag
    assert sorted(s) == GOLDEN_SUMMARY_KEYS and "family_override" not in s
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert sorted(rec) == GOLDEN_RECEIPT_KEYS and sorted(rec["inputs"]) == GOLDEN_INPUT_KEYS
    assert "family-override" not in capsys.readouterr().err


def test_without_the_flag_a_committed_run_has_no_family_field_anywhere(env):
    code, ev, db, disp = commit_run(env)
    assert code == 0
    assert all("family_override" not in e for e in ev)
    assert "family_override" not in json.loads(pathlib.Path(env["receipt"]).read_text())


# ── offline planner on the single-rebuild id lists (run 1 and tails A / B), registry rows from the in-repo fixture ──

RUN1_FAMILY = ["bg_gochara_arcs", "bg_gochara_citation_resolution"]
TAIL_A_FAMILY = ["ka_gochara", "ka_gochara_resonance", "ka_moorti_nirnaya", "ka_sangam", "ka_vedha_gochara", "ka_vighnakara", "ka_yojaka"]
TAIL_B_FAMILY = ["ka_bhavishya_lekha", "ka_kala_darshana", "ka_kalasutra", "mi_adhilepa", "ph_muhurta", "ph_nimitta", "ph_pratikara"]
FX_CASES = [("run1", 53, 17, RUN1_FAMILY), ("tailA", 8, 4, TAIL_A_FAMILY), ("tailB_482012f1", 22, 13, TAIL_B_FAMILY),
            ("tailB_1c826d5a", 22, 13, TAIL_B_FAMILY)]
SLOT = "bg_gochara_citation_resolution"        # reserved run-1 slot: no writer today (NO_WRITER until its writer PR lands)


def _fx_world(env, assume_writer=()):
    reg = {a: row(a, r["depends_on"], scope=r["scope"], layer=r["layer"], kind=r["asset_kind"], active=r["is_active"],
                  writer=True if a in assume_writer else r["has_writer"], domain=r["domain"], probe=bool(r["rebuild_on_probe_fail"]))
           for a, r in FX_ROWS.items()}
    digests = {a: _hex(a) for a in reg}
    (pathlib.Path(env["repo"]) / "platform" / "src" / "generated" / "nirmana-writer-digests.json").write_text(
        json.dumps({"version": 1, "writers": digests}))
    git = FakeGit(deployed=digests)
    git.family = {k: list(FAMILY_FILE[k]) for k in (*slw.FAMILY_LIST_KEYS, "family_set")}
    return reg, git


def _fx_cli(env, name, allow, *extra, assume_writer=()):
    reg, git = _fx_world(env, assume_writer)
    ids = FX["lists"][name]
    deps = {a: ("lit", "fresh", reg[a]["asset_kind"]) for a in reg if a not in ids}          # everything outside the list is lit and fresh
    db = FakeDB(registry=reg, deps=deps)
    flag = [FAMILY_FLAG, ",".join(allow)] if allow else []
    code, ev = run(env, argv_for(env, "--allowed-layers", ALL_LAYERS, *flag, *extra, assets=ids), db=db, git=git)
    return code, ev, db


def _fx_classify(name, allow=(), assume_writer=()):
    ids = FX["lists"][name]
    rows = [{**FX_ROWS[a], **({"has_writer": True} if a in assume_writer else {})} for a in ids]
    return asd.classify_assets(ids, rows, FAMILY_REAL, allowed_layers=tuple(ALL_LAYERS.split(",")), protected=["ka_gochara_sweep"],
                               allow_family=allow)


@pytest.mark.parametrize("name,count,waves,family", FX_CASES)
def test_the_fixture_lists_are_what_the_runbook_says(name, count, waves, family):
    ids = FX["lists"][name]
    assert len(ids) == count and sorted(set(ids) & FAMILY_REAL["family_set"]) == family


@pytest.mark.parametrize("name,count,waves,family", FX_CASES)
def test_without_the_flag_the_family_ids_of_each_run_are_refused(name, count, waves, family):
    f = _fx_classify(name, assume_writer=(SLOT,))
    assert sorted({x["asset"] for x in f if x["code"] == "FAMILY_ASSET"}) == family
    assert any(x["code"] == "SPLITS_FAMILY" for x in f)


@pytest.mark.parametrize("name,count,waves,family", FX_CASES)
def test_with_the_flag_the_family_refusals_disappear_and_the_planner_builds_the_waves(env, name, count, waves, family):
    assert _fx_classify(name, allow=family, assume_writer=(SLOT,)) == []
    code, ev, db = _fx_cli(env, name, family, assume_writer=(SLOT,))
    assert code == 0, ev
    s = last(ev)
    assert s["asset_count"] == count and s["wave_count"] == waves and sorted(s["assets"]) == sorted(FX["lists"][name])
    assert s["family_override"]["ids"] == family and s["excluded_accepted"] == []
    assert sum(s["wave_widths"]) == count
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert rec["family_override"] == family and rec["inputs"]["allow_family"] == family
    assert len(db.inserts("build_runs")) == 1 and "commit" not in db.kinds()                    # plan: INSERT then ROLLBACK


@pytest.mark.parametrize("name", ["run1", "tailA", "tailB_482012f1"])
def test_the_cli_without_the_flag_refuses_the_same_lists(env, name):
    code, ev, db = _fx_cli(env, name, [], assume_writer=(SLOT,))
    assert code == 4 and {a for a, c in refusal_pairs(ev) if c == "FAMILY_ASSET"} == set(FX["lists"][name]) & FAMILY_REAL["family_set"]
    assert db.inserts("build_runs") == []


def test_run1_slot_without_a_writer_is_still_refused_even_when_named():
    f = _fx_classify("run1", allow=RUN1_FAMILY)
    assert [(x["asset"], x["code"]) for x in f] == [(SLOT, "NO_WRITER")]


def test_run1_cli_with_the_slot_unbuilt_refuses_no_writer_and_inserts_nothing(env):
    code, ev, db = _fx_cli(env, "run1", RUN1_FAMILY)
    assert code == 4 and refusal_pairs(ev) == [(SLOT, "NO_WRITER")] and db.inserts("build_runs") == []


def test_naming_only_some_family_ids_waives_only_those(env):
    named = ["ka_gochara", "ka_moorti_nirnaya", "ka_vedha_gochara", "ka_vighnakara"]
    code, ev, db = _fx_cli(env, "tailA", named)
    assert code == 4
    left = {a for a, c in refusal_pairs(ev) if c == "FAMILY_ASSET"}
    assert left == {"ka_gochara_resonance", "ka_sangam", "ka_yojaka"} and not left & set(named)
    assert not any(a in named for a, _c in refusal_pairs(ev))


def test_the_whole_family_with_the_override_still_cannot_include_its_unbuildable_members():
    members = sorted(a for a in FAMILY_REAL["family_set"] if a in FX_ROWS)
    rows = [dict(FX_ROWS[a]) for a in members]
    f = asd.classify_assets(members, rows, FAMILY_REAL, allowed_layers=tuple(ALL_LAYERS.split(",")), protected=["ka_gochara_sweep"],
                            allow_family=members)
    got = {}
    for x in f:
        got.setdefault(x["asset"], []).append(x["code"])
    assert got == {"bg_gochara_citation_resolution": ["NO_WRITER"],
                   "ka_gochara_sweep": ["NOT_ACTIVE", "PROTECTED_ASSET"],
                   "ka_gochara_v3_century_materialize": ["NOT_ACTIVE"], "ka_gochara_v4_41_candidate": ["NOT_ACTIVE"],
                   "ka_gochara_v5": ["NOT_ACTIVE"], "ka_tulana": ["SERVICE_ASSET"]}
    assert not any(c in FAMILY_CODES for codes in got.values() for c in codes)
