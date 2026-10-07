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


def row(asset, deps=(), *, scope="per_chart", layer="ganita", kind="data", active=True, writer=True, domain=None, target=None):
    return {"asset_id": asset, "domain": domain or ("shared" if scope == "global" else "chart"), "layer": layer, "scope": scope,
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
}
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
                 conn_numbers=None, run_state="completed", asset_rows=None, fail_commit=False, terminalise_rows=1, change_after_first=None):
        self.log, self.registry = [], dict(REG if registry is None else registry)
        self.charts, self.deps = set(charts), DEPS_STATE if deps is None else deps
        self.anchor_active, self.global_runs, self.conflicts, self.prior = list(anchor_active), list(global_runs), list(conflicts), list(prior)
        self.conn_numbers = conn_numbers or {"max_connections": 50, "reserved": 3, "in_use": 9}
        self.run_state, self.asset_rows = run_state, asset_rows
        self.fail_commit, self.commit_calls, self.terminalise_rows = fail_commit, 0, terminalise_rows
        self.rows_calls, self.change_after_first = 0, change_after_first
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
        if "unnest(%s::text[]) AS dep" in sql:
            return [{"asset_id": d, "asset_kind": (self.deps.get(d) or (None, None, "data"))[2], "state": (self.deps.get(d) or (None,))[0],
                     "freshness_state": (self.deps.get(d) or (None, None))[1]} for d in params[0]]
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
        if "SELECT state, last_error FROM build_runs WHERE id" in sql:
            return [{"state": self.run_state, "last_error": None}]
        if "FROM build_run_assets bra JOIN build_runs br" in sql:
            plan = json.loads(self.inserted_run[3]) if self.inserted_run else GOOD
            rows = self.asset_rows if self.asset_rows is not None else {a: ("complete", "build") for a in plan}
            return [{"asset_id": a, "position": i, "state": s, "disposition": d, "error": None, "throughput_state": "lit",
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
    jobfile = tmp_path / "job-sha"
    jobfile.write_text(sha_of("deadbeef") + "\n")
    return {"repo": str(repo), "receipt": str(out / "receipt.json"), "jobfile": str(jobfile), "tmp": tmp_path}


def argv_for(env, *extra, assets=GOOD, commit=False, confirm=None, anchor=CHART, worker_limit=None):
    argv = ["--assets", ",".join(assets), "--anchor-chart", anchor, "--receipt", env["receipt"], "--repo", env["repo"],
            "--deployed-sha", "deadbeef", "--deployed-job-sha", "deadbeef", "--job-sha-file", env["jobfile"]]
    if worker_limit is not None:
        argv += ["--worker-limit", str(worker_limit)]
    if commit:
        argv += ["--commit", "--confirm", confirm or "x"]
    return asd.build_parser().parse_args(argv + list(extra))


def run(env, args, db=None, git=None, dispatch=None):
    db = db or FakeDB()
    git = git or FakeGit(deployed=DIGESTS)
    out = Stream()
    code = asd.run_cli(args, connect=db.connect, git=git, out=out, sleep=lambda s: None, monotonic=lambda: 0.0, dispatch=dispatch,
                       now=lambda: T0)
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


def test_commit_requires_the_job_sha_file_and_both_shas(env):
    args = argv_for(env, commit=True, confirm="x")
    args.job_sha_file = None
    code, ev = run(env, args, db=FakeDB())
    assert code == 2 and "--job-sha-file" in last(ev)["error"]
    args = argv_for(env)
    args.deployed_job_sha = None
    code, ev = run(env, args, db=FakeDB())
    assert code == 4 and refusal_pairs(ev) == [(None, "DEPLOYED_JOB_SHA_REQUIRED")]


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
    assert code == 8 and "FORCE_DID_NOT_TAKE_EFFECT" in last(ev)["verification"]["codes"] and last(ev)["second_dispatch"] == "FORBIDDEN"
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
    assert asd.ROWS_SQL.replace("ar.domain, ", "", 1) == slw.CANDIDATES_SQL
