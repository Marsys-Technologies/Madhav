"""test_e5_3_level_wave.py -- Suvarna E5.3: the multi-asset level-wave dispatcher (section 2 of suvarna_level_wave.py).

Offline. No database, no gcloud, no network: every outside contact (database connection, git, the Cloud Run dispatch, the
operator's pause) is an injected fake that records what it was asked to do. Nothing here proves behaviour at production
scale -- the dispatcher has never run above 17 assets / 1 wave (see README_level_wave.md).

Proof map
  waves                      hand-computed fixture; longest path; order independence; cycles
  manifest                   byte-identical to dispatch_frozen_rebuild.build_manifest for one asset; accepted by the REAL
                             runner.validate_frozen_run_manifest (read-only import of the frozen runner)
  refusals                   image skew; dependency not lit+fresh; registry row changed since build; family asset; split
                             family; unreadable family file; active run; confirm token; each leaves NO insert behind
  dry run                    INSERT then ROLLBACK, COMMIT only with the exact token
  stop hook / wave-by-wave   nothing continues without the operator's token
  wall-time report           per-asset / per-wave seconds from build_run_assets rows; unmeasured is never 0
  23 bo_* manifest           the L2 asset set offline (fixture rows; see BO23_SOURCE)
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import itertools
import json
import pathlib
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suvarna_level_wave as slw  # noqa: E402

REPO = HERE.parents[3]
CHART = "482012f1-710e-4a25-994a-93821f5871aa"


def _hexdigest(name: str, salt: str = "") -> str:
    return hashlib.sha256((name + salt).encode()).hexdigest()


def row(asset, deps=(), *, scope="per_chart", cow=False, part=None, active=True, writer=True, kind="data",
        layer="bodha", target=None, timeout=600, est=None):
    return {"asset_id": asset, "layer": layer, "scope": scope, "asset_kind": kind, "is_active": active,
            "has_writer": writer, "target_table": target, "writer_timeout_seconds": timeout, "estimated_seconds": est,
            "depends_on": list(deps), "natural_key_partition": part, "has_cowriters": cow}


# ───────────────────────── fakes ─────────────────────────

class FakeCursor:
    def __init__(self, db, conn):
        self.db, self.conn, self._rows = db, conn, []

    def execute(self, sql, params=None):
        self.db.log.append(("execute", " ".join(sql.split()), params))
        self._rows = self.db.respond(" ".join(sql.split()), params)

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def close(self):
        pass


class FakeConn:
    def __init__(self, db):
        self.db, self.closed = db, False

    def cursor(self):
        return FakeCursor(self.db, self)

    def commit(self):
        self.db.log.append(("commit",))

    def rollback(self):
        self.db.log.append(("rollback",))

    def close(self):
        self.closed = True
        self.db.log.append(("close",))


class FakeDB:
    """candidates: a list of row-lists, one per candidate SELECT in order (the last repeats). deps: {asset: (state,
    freshness, kind)} for the dependency query. runs: {run_id: state or [states]} for the terminal poll."""

    def __init__(self, candidates, deps=None, active=(), run_states=None, run_assets=None, fk_rows=None, table_rows=None):
        self.log, self.cand, self.deps, self.active = [], list(candidates), deps or {}, list(active)
        self.cand_calls = 0
        self.run_states = run_states or {}
        self.run_assets = run_assets or {}
        self.fk_rows, self.table_rows = fk_rows or [], table_rows or []
        self.inserted = {}

    def connect(self):
        self.log.append(("connect",))
        return FakeConn(self)

    def respond(self, sql, params):
        if "FROM asset_registry ar WHERE ar.asset_id = ANY" in sql:
            i = min(self.cand_calls, len(self.cand) - 1)
            self.cand_calls += 1
            wanted = set(params[0])
            return [r for r in self.cand[i] if r["asset_id"] in wanted]
        if "unnest(%s::text[]) AS dep" in sql:
            out = []
            for dep in params[0]:
                st, fr, kind = self.deps.get(dep, (None, None, "data"))
                out.append({"asset_id": dep, "asset_kind": kind, "state": st, "freshness_state": fr})
            return out
        if "FROM build_runs WHERE chart_id" in sql:
            return list(self.active)
        if "SELECT state, last_error FROM build_runs WHERE id" in sql:
            seq = self.run_states.get(params[0], "completed")
            if isinstance(seq, list):
                state = seq.pop(0) if len(seq) > 1 else seq[0]
            else:
                state = seq
            return [{"state": state, "last_error": None}]
        if sql.startswith("INSERT INTO build_run_assets"):
            self.inserted.setdefault(params[0], []).append(params[1])
        if "FROM build_run_assets bra" in sql:
            if params[0] in self.run_assets:
                return list(self.run_assets[params[0]])
            return [{"asset_id": a, "position": i, "state": "complete", "error": None, "throughput_state": "lit",
                     "started_at": T0 + timedelta(seconds=10 * i), "ended_at": T0 + timedelta(seconds=10 * i + 5)}
                    for i, a in enumerate(self.inserted.get(params[0], []))]
        if "FROM pg_constraint" in sql:
            return list(self.fk_rows)
        if "FROM pg_class c" in sql:
            return list(self.table_rows)
        return []

    # helpers for assertions
    def statements(self):
        return [e for e in self.log if e[0] == "execute"]

    def inserts(self, table):
        return [e for e in self.statements() if e[1].startswith(f"INSERT INTO {table}")]

    def kinds(self):
        return [e[0] for e in self.log]


class FakeGit:
    """Answers the four git calls load_family_info / load_deployed_writer_digests make."""

    def __init__(self, *, family_text=None, family_listed=True, ref_ok=True, deployed=None, show_fails=False):
        self.family_text, self.family_listed, self.ref_ok = family_text, family_listed, ref_ok
        self.deployed, self.show_fails = deployed, show_fails
        self.calls = []

    def __call__(self, repo, args):
        self.calls.append(list(args))
        cp = lambda rc=0, out="", err="": subprocess.CompletedProcess(args, rc, out, err)  # noqa: E731
        if args[0] == "rev-parse":
            return cp(0 if self.ref_ok else 128, "abc\n", "" if self.ref_ok else "bad ref")
        if args[0] == "ls-tree":
            return cp(0, slw.FAMILY_FILE_REL + "\n" if self.family_listed else "")
        if args[0] == "show":
            spec = args[1]
            if spec.endswith(slw.FAMILY_FILE_REL):
                return cp(128, "", "boom") if self.show_fails else cp(0, self.family_text)
            if spec.endswith(slw.WRITER_DIGESTS_REL):
                return cp(0, json.dumps({"writers": self.deployed})) if self.deployed is not None else cp(128, "", "no such sha")
        raise AssertionError(f"unexpected git call {args}")


def family_doc(**lists):
    keys = {k: [] for k in slw.FAMILY_LIST_KEYS}
    keys.update(lists)
    keys["family_set"] = sorted(set().union(*[set(v) for v in keys.values()]))
    return json.dumps(keys)


def make_repo(tmp_path, digests):
    d = tmp_path / "platform" / "src" / "generated"
    d.mkdir(parents=True)
    (d / "nirmana-writer-digests.json").write_text(json.dumps({"version": 1, "writers": digests}))
    return str(tmp_path)


def args_for(repo, assets, *extra, mode=None, deployed_sha="deadbeef"):
    argv = ["--chart-id", CHART, "--assets", assets, "--repo", repo, "--deployed-sha", deployed_sha]
    if mode:
        argv += ["--mode", mode]
    return slw.build_parser().parse_args(argv + list(extra))


def run(args, db, git, **kw):
    out = io.StringIO()
    code = slw.run_cli(args, connect=db.connect, git=git, out=out, **kw)
    return code, json.loads(out.getvalue())


SMALL = [row("a_one", ["ext_one"]), row("a_two", ["a_one"]), row("a_three", ["a_one", "ext_two"])]
SMALL_DIGESTS = {r["asset_id"]: _hexdigest(r["asset_id"]) for r in SMALL}
READY = {"ext_one": ("lit", "fresh", "data"), "ext_two": ("lit", "fresh", "data")}


@pytest.fixture
def env(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS)
    return repo, git


# ───────────────────────── waves ─────────────────────────

HAND = {  # hand-computed: wave = 1 + max(wave of in-set dependencies); outside dependencies never move an asset
    "a": [], "g": [], "b": ["a"], "c": ["a"], "d": ["b", "c"], "e": ["d", "x_outside"], "f": ["a", "e"],
}
HAND_WAVES = [["a", "g"], ["b", "c"], ["d"], ["e"], ["f"]]


def test_waves_match_the_hand_computed_fixture():
    assert slw.derive_waves(list(HAND), HAND) == HAND_WAVES


def test_wave_is_the_longest_path_not_the_shortest():
    # f depends on a (wave 0) AND e (wave 3): it must land in wave 4, not 1
    assert slw.derive_waves(list(HAND), HAND)[4] == ["f"]


def test_waves_ignore_input_order_and_flatten_to_a_stable_plan():
    base = slw.derive_waves(list(HAND), HAND)
    rng = random.Random(53)
    for _ in range(20):
        ids = list(HAND)
        rng.shuffle(ids)
        assert slw.derive_waves(ids, HAND) == base


def test_a_dependency_outside_the_set_does_not_create_a_wave():
    assert slw.derive_waves(["p", "q"], {"p": ["outside_1"], "q": ["outside_2"]}) == [["p", "q"]]
    assert slw.external_dependencies(["p", "q"], {"p": ["outside_1"], "q": []}) == {"p": ["outside_1"]}


@pytest.mark.parametrize("deps", [{"a": ["b"], "b": ["a"]}, {"a": ["a"]}, {"a": ["b"], "b": ["c"], "c": ["a"]}])
def test_cycles_raise(deps):
    with pytest.raises(slw.LevelWaveError, match="cycle"):
        slw.derive_waves(list(deps), deps)


def test_duplicate_assets_raise():
    with pytest.raises(slw.LevelWaveError):
        slw.derive_waves(["a", "a"], {})


# ───────────────────────── manifest ─────────────────────────

def _frozen_dispatcher():
    spec = importlib.util.spec_from_file_location("dispatch_frozen_rebuild_golden", REPO / "platform/scripts/dispatch_frozen_rebuild.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_single_asset_manifest_and_digest_are_byte_identical_to_the_existing_dispatcher():
    old = _frozen_dispatcher()
    for candidate in (row("ga_x", ["bg_y", "ga_z"], scope="global", cow=True, part="k (a, b)"), row("bo_q")):
        digest = _hexdigest(candidate["asset_id"])
        want, want_digest = old.build_manifest(chart_id=CHART, candidate=candidate, expected_code_digest=digest)
        got, got_digest = slw.build_level_manifest(chart_id=CHART, plan_waves=[[candidate["asset_id"]]],
                                                   rows={candidate["asset_id"]: candidate},
                                                   writer_digests={candidate["asset_id"]: digest})
        assert got == want
        assert got_digest == want_digest
        assert slw.canonical_json(got).encode() == old._canonical_json(want).encode()


def test_manifest_digest_is_the_sha256_of_the_canonical_json():
    m, d = slw.build_level_manifest(chart_id=CHART, plan_waves=[["a_one"], ["a_two"]], rows={r["asset_id"]: r for r in SMALL},
                                    writer_digests=SMALL_DIGESTS)
    assert d == hashlib.sha256(json.dumps(m, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert m["version"] == "nirmana-run-manifest/v1" and m["scope"] == "asset_set" and m["action"] == "rebuild"
    assert m["scope_target"] == "a_one,a_two" and m["waves"] == [["a_one"], ["a_two"]]
    assert [a["asset_id"] for a in m["assets"]] == ["a_one", "a_two"]
    assert m["assets"][1]["depends_on"] == ["a_one"] and m["assets"][1]["expected_code_digest"] == SMALL_DIGESTS["a_two"]


def test_manifest_requires_a_valid_writer_digest_and_non_empty_waves():
    rows = {r["asset_id"]: r for r in SMALL}
    with pytest.raises(slw.LevelWaveError):
        slw.build_level_manifest(chart_id=CHART, plan_waves=[["a_one"]], rows=rows, writer_digests={"a_one": "xyz"})
    with pytest.raises(slw.LevelWaveError):
        slw.build_level_manifest(chart_id=CHART, plan_waves=[["a_one"], []], rows=rows, writer_digests=SMALL_DIGESTS)
    with pytest.raises(slw.LevelWaveError):
        slw.build_level_manifest(chart_id=CHART, plan_waves=[["a_one"], ["a_one"]], rows=rows, writer_digests=SMALL_DIGESTS)


def _runner_validate():
    sys.path.insert(0, str(REPO / "platform/python-sidecar"))
    try:
        from pipeline.orchestrator.runner import validate_frozen_run_manifest
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"frozen runner not importable here: {exc.__class__.__name__}")
    return validate_frozen_run_manifest


def _as_run(manifest, digest):
    plan = [a for w in manifest["waves"] for a in w]
    return {"plan_manifest": manifest, "plan_manifest_digest": digest, "chart_id": manifest["chart_id"],
            "scope": "asset_set", "scope_target": manifest["scope_target"], "action": "rebuild", "plan": plan}


def test_the_real_runner_accepts_a_multi_wave_manifest():
    validate = _runner_validate()
    m, d = slw.build_level_manifest(chart_id=CHART, plan_waves=HAND_WAVES, rows={a: row(a, deps) for a, deps in HAND.items()},
                                    writer_digests={a: _hexdigest(a) for a in HAND})
    frozen = validate(_as_run(m, d))
    assert frozen.plan == [a for w in HAND_WAVES for a in w]
    assert frozen.asset_deps["e"] == ["d", "x_outside"]


def test_the_real_runner_rejects_a_tampered_manifest():
    validate = _runner_validate()
    m, d = slw.build_level_manifest(chart_id=CHART, plan_waves=[["a_one"], ["a_two"]], rows={r["asset_id"]: r for r in SMALL},
                                    writer_digests=SMALL_DIGESTS)
    m["assets"][0]["scope"] = "global"
    with pytest.raises(ValueError, match="digest mismatch"):
        validate(_as_run(m, d))


def test_registry_row_digest_covers_every_field_the_dispatch_depends_on():
    base = row("a_one", ["x", "y"])
    d0 = slw.registry_row_digest(base)
    assert slw.registry_row_digest(dict(base, depends_on=["y", "x"])) == d0          # unordered, like the runner
    for change in ({"depends_on": ["x"]}, {"scope": "global"}, {"natural_key_partition": "p"}, {"has_cowriters": True},
                   {"is_active": False}, {"has_writer": False}, {"asset_kind": "service"}, {"layer": "kala"}):
        assert slw.registry_row_digest(dict(base, **change)) != d0, change


def test_confirm_token_is_bound_to_the_manifest_digest_and_keeps_the_frozen_rebuild_suffix():
    t1, t2 = slw.expected_confirmation("a" * 64, 23), slw.expected_confirmation("b" * 64, 23)
    assert t1 != t2 and t1.endswith("_FROZEN_REBUILD") and t1.startswith("23ASSETS_AAAAAAAAAAAA")


# ───────────────────────── image skew ─────────────────────────

def test_image_skew_is_refused_and_nothing_is_inserted(env):
    repo, _ = env
    skewed = dict(SMALL_DIGESTS, a_two=_hexdigest("a_two", "other build"))
    git = FakeGit(family_text=family_doc(), deployed=skewed)
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two,a_three"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refused"] is True
    assert [r["code"] for r in out["refusals"]] == ["IMAGE_SKEW"] and out["refusals"][0]["asset"] == "a_two"
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds()


def test_an_asset_missing_from_the_deployed_inventory_is_skew_not_a_skip(env):
    repo, _ = env
    git = FakeGit(family_text=family_doc(), deployed={k: v for k, v in SMALL_DIGESTS.items() if k != "a_three"})
    code, out = run(args_for(repo, "a_one,a_three"), FakeDB([SMALL], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["asset"] == "a_three"


def test_unreadable_deployed_digest_source_refuses(env):
    repo, _ = env
    git = FakeGit(family_text=family_doc(), deployed=None)         # `git show <sha>:...` fails
    code, out = run(args_for(repo, "a_one"), FakeDB([SMALL], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "DEPLOYED_DIGESTS_UNAVAILABLE"


def test_no_deployed_digest_source_at_all_refuses(env):
    repo, git = env
    a = slw.build_parser().parse_args(["--chart-id", CHART, "--assets", "a_one", "--repo", repo])
    code, out = run(a, FakeDB([SMALL], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "DEPLOYED_DIGESTS_UNAVAILABLE"


def test_deployed_digests_file_is_an_accepted_source(env, tmp_path):
    repo, git = env
    f = tmp_path / "deployed.json"
    f.write_text(json.dumps({"writers": SMALL_DIGESTS}))
    a = slw.build_parser().parse_args(["--chart-id", CHART, "--assets", "a_one", "--repo", repo, "--deployed-digests-file", str(f)])
    code, out = run(a, FakeDB([SMALL], READY), git)
    assert code == 0 and out["committed"] is False


def test_checkout_without_a_digest_refuses(tmp_path):
    repo = make_repo(tmp_path, {"a_two": SMALL_DIGESTS["a_two"]})
    git = FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS)
    code, out = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "CODE_DIGEST_UNAVAILABLE"


# ───────────────────────── dependencies lit + fresh ─────────────────────────

@pytest.mark.parametrize("deps,needle", [
    ({"ext_one": ("lit", "stale", "data"), "ext_two": ("lit", "fresh", "data")}, "ext_one(receipt:stale)"),
    ({"ext_one": ("lit", "fresh", "data"), "ext_two": ("building", "fresh", "data")}, "ext_two(building)"),
    ({"ext_one": ("lit", None, "data"), "ext_two": ("lit", "fresh", "data")}, "ext_one(receipt:absent)"),
    ({"ext_two": ("lit", "fresh", "data")}, "ext_one(absent)"),
])
def test_a_dependency_outside_the_set_that_is_not_lit_and_fresh_refuses(env, deps, needle):
    repo, git = env
    db = FakeDB([SMALL], deps)
    code, out = run(args_for(repo, "a_one,a_two,a_three"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE
    assert out["refusals"][0]["code"] == "DEPENDENCY_NOT_READY" and needle in out["refusals"][0]["detail"]
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds()


def test_a_stale_dependency_of_a_later_wave_asset_refuses_too(env):
    # ext_two is declared by a_three (wave 1), not by the wave-0 asset: still checked, in single-run mode
    repo, git = env
    deps = {"ext_one": ("lit", "fresh", "data"), "ext_two": ("lit", "stale", "data")}
    code, out = run(args_for(repo, "a_one,a_two,a_three"), FakeDB([SMALL], deps), git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["needed_by"] == ["a_three"]


def test_every_offender_is_listed_not_just_the_first(env):
    repo, git = env
    deps = {"ext_one": ("lit", "stale", "data"), "ext_two": ("error", "fresh", "data")}
    _, out = run(args_for(repo, "a_one,a_two,a_three"), FakeDB([SMALL], deps), git)
    assert sorted(r["dependency"] for r in out["refusals"]) == ["ext_one", "ext_two"]


def test_a_service_dependency_needs_only_service_ok():
    class Cur:
        def execute(self, sql, params):
            self.p = params

        def fetchall(self):
            return [{"asset_id": "svc", "asset_kind": "service", "state": "service_ok", "freshness_state": None}]
    slw.check_external_dependencies(Cur(), CHART, {"a": ["svc"]})   # no raise


def test_dependencies_inside_the_set_are_not_required_to_be_lit(env):
    repo, git = env
    # a_two depends on a_one, which is in the set and not built yet: fine
    code, _ = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], {"ext_one": ("lit", "fresh", "data")}), git)
    assert code == 0


# ───────────────────────── registry row changed since the manifest was built ─────────────────────────

@pytest.mark.parametrize("change", [
    {"depends_on": ["a_one", "ext_one"]}, {"scope": "global"}, {"natural_key_partition": "changed"},
    {"has_cowriters": True}, {"is_active": False}, {"has_writer": False},
])
def test_registry_row_change_between_build_and_insert_refuses_without_inserting(env, change):
    repo, git = env
    later = [dict(r, **change) if r["asset_id"] == "a_two" else r for r in SMALL]
    db = FakeDB([SMALL, later], READY)             # 1st read builds the manifest, 2nd (in the insert transaction) differs
    code, out = run(args_for(repo, "a_one,a_two,a_three"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE
    assert out["refusals"][0]["code"] == "REGISTRY_ROW_CHANGED" and out["refusals"][0]["asset"] == "a_two"
    assert db.cand_calls == 2
    assert db.inserts("build_runs") == [] and db.inserts("build_run_assets") == [] and "commit" not in db.kinds()


def test_a_row_deleted_between_build_and_insert_refuses(env):
    repo, git = env
    db = FakeDB([SMALL, [r for r in SMALL if r["asset_id"] != "a_three"]], READY)
    code, out = run(args_for(repo, "a_one,a_two,a_three"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["asset"] == "a_three"


def test_the_re_read_happens_after_the_lock_and_before_the_insert(env):
    repo, git = env
    db = FakeDB([SMALL], READY)
    run(args_for(repo, "a_one,a_two,a_three"), db, git)
    sql = [e[1] for e in db.statements()]
    i_lock = next(i for i, s in enumerate(sql) if "pg_advisory_xact_lock" in s)
    reads = [i for i, s in enumerate(sql) if "FROM asset_registry ar WHERE ar.asset_id = ANY" in s]
    i_insert = next(i for i, s in enumerate(sql) if s.startswith("INSERT INTO build_runs"))
    assert len(reads) == 2 and reads[0] < i_lock < reads[1] < i_insert


def test_inactive_missing_or_service_assets_refuse(env):
    repo, git = env
    for rows in ([row("a_one", active=False)], [], [row("a_one", kind="service")], [row("a_one", writer=False)]):
        code, out = run(args_for(repo, "a_one"), FakeDB([rows], READY), git)
        assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "REGISTRY_ROW_INVALID"


def test_an_active_run_on_the_chart_refuses(env):
    repo, git = env
    db = FakeDB([SMALL], READY, active=[{"id": "r1", "chart_id": CHART, "state": "running"}])
    code, out = run(args_for(repo, "a_one,a_two"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "ACTIVE_RUN"
    assert db.inserts("build_runs") == []


# ───────────────────────── family ─────────────────────────

@pytest.mark.parametrize("asset", ["ka_gochara", "ka_gochara_resonance", "ka_gochara_sweep", "gochara_x", "kala_gochara_y"])
def test_name_pattern_family_assets_are_refused_even_when_the_family_file_lists_nothing(tmp_path, asset):
    repo = make_repo(tmp_path, {asset: _hexdigest(asset), "a_one": SMALL_DIGESTS["a_one"]})
    git = FakeGit(family_text=family_doc(), deployed={asset: _hexdigest(asset), "a_one": SMALL_DIGESTS["a_one"]})
    db = FakeDB([[row(asset), SMALL[0]]], READY)
    code, out = run(args_for(repo, f"a_one,{asset}"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE
    assert [(r["code"], r["asset"]) for r in out["refusals"]] == [("FAMILY_ASSET", asset)]
    assert db.log == []                                             # refused before any database contact


def test_family_set_member_with_an_ordinary_name_is_refused(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_text=family_doc(family_sangam=["a_two"]), deployed=SMALL_DIGESTS)
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE
    assert ("FAMILY_ASSET", "a_two") in [(r["code"], r.get("asset")) for r in out["refusals"]]
    assert db.log == []


def test_a_partial_family_is_refused_as_a_split(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_text=family_doc(family_kshetra=["a_two", "a_three"]), deployed=SMALL_DIGESTS)
    code, out = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE
    split = [r for r in out["refusals"] if r["code"] == "SPLITS_FAMILY"]
    assert len(split) == 1 and split[0]["family"] == "family_kshetra"
    assert split[0]["requested"] == ["a_two"] and split[0]["missing"] == ["a_three"]


def test_a_whole_family_is_still_refused_as_family_assets(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_text=family_doc(family_kshetra=["a_two", "a_three"]), deployed=SMALL_DIGESTS)
    code, out = run(args_for(repo, "a_two,a_three"), FakeDB([SMALL], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE
    assert sorted(r["asset"] for r in out["refusals"] if r["code"] == "FAMILY_ASSET") == ["a_three", "a_two"]
    assert not [r for r in out["refusals"] if r["code"] == "SPLITS_FAMILY"]


@pytest.mark.parametrize("git_kwargs,why", [
    (dict(family_text="{not json"), "not valid JSON"),
    (dict(family_text="[]"), "not an object"),
    (dict(family_text=json.dumps({"family_set": []})), "missing"),
    (dict(family_text=json.dumps({**json.loads(family_doc()), "family_set": ["zzz"]})), "union"),
    (dict(family_text=json.dumps({**json.loads(family_doc()), "family_gochara": "oops"})), "not a list"),
    (dict(family_text=family_doc(), show_fails=True), "git show failed"),
    (dict(family_text=family_doc(), ref_ok=False), "not resolvable"),
])
def test_an_unreadable_or_malformed_family_file_refuses_and_never_fails_open(tmp_path, git_kwargs, why):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(deployed=SMALL_DIGESTS, **git_kwargs)
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE
    assert out["refusals"][0]["code"] == "FAMILY_FILE_UNREADABLE" and why in out["refusals"][0]["detail"]
    assert db.log == []


def test_an_absent_family_file_allows_a_dry_run_on_name_patterns_only_and_blocks_a_commit(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_listed=False, deployed=SMALL_DIGESTS)
    code, out = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], READY), git)
    assert code == 0 and out["family_enforcement"] == "name_patterns_only"
    code, out = run(args_for(repo, "a_one,a_two", "--commit", "--confirm", "x", mode="single-run"), FakeDB([SMALL], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "FAMILY_FILE_MISSING"


def test_the_family_file_is_read_from_the_committed_ref_not_the_working_tree(env):
    repo, git = env
    run(args_for(repo, "a_one"), FakeDB([SMALL], READY), git, )
    shows = [c for c in git.calls if c[0] == "show"]
    assert any(c[1] == f"origin/main:{slw.FAMILY_FILE_REL}" for c in shows)


# ───────────────────────── dry run / commit ─────────────────────────

def test_dry_run_is_the_default_and_rolls_back_after_the_inserts(env):
    repo, git = env
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two,a_three"), db, git)
    assert code == 0 and out["committed"] is False and out["insert"]["committed"] is False
    kinds = db.kinds()
    assert "commit" not in kinds
    sql = [e[1] for e in db.statements()]
    i_run = next(i for i, s in enumerate(sql) if s.startswith("INSERT INTO build_runs"))
    n_assets = [s for s in sql if s.startswith("INSERT INTO build_run_assets")]
    assert len(n_assets) == 3
    # the last transaction ends with ROLLBACK straight after the final INSERT
    last_insert_idx = max(i for i, e in enumerate(db.log) if e[0] == "execute" and e[1].startswith("INSERT INTO build_run_assets"))
    assert db.log[last_insert_idx + 1] == ("rollback",)
    assert i_run < len(sql)


def test_the_inserted_rows_carry_the_manifest_the_plan_and_positions(env):
    repo, git = env
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_three,a_one,a_two"), db, git)
    ins = db.inserts("build_runs")[0]
    run_id, chart, scope_target, plan_json, manifest_json, digest, trig = ins[2]
    assert chart == CHART and scope_target == "a_one,a_three,a_two" and json.loads(plan_json) == ["a_one", "a_three", "a_two"]
    manifest = json.loads(manifest_json)
    assert digest == slw.manifest_digest(manifest) == out["manifest_digest"]
    assert json.loads(plan_json) == [a for w in manifest["waves"] for a in w]
    assert trig == slw.TRIGGERED_BY
    positions = {p[2][1]: p[2][2] for p in db.inserts("build_run_assets")}
    assert positions == {a: i for i, a in enumerate(json.loads(plan_json))}


def test_commit_without_the_token_never_commits(env):
    repo, git = env
    for confirm in (None, "WRONG_FROZEN_REBUILD", "A_ONE_FROZEN_REBUILD"):
        db = FakeDB([SMALL], READY)
        extra = ["--commit"] + (["--confirm", confirm] if confirm else [])
        code, out = run(args_for(repo, "a_one,a_two", *extra, mode="single-run"), db, git, dispatch=lambda r: pytest.fail("dispatched"))
        assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "CONFIRM_TOKEN_MISMATCH"
        assert "commit" not in db.kinds() and db.inserts("build_runs") == []


def test_insert_run_itself_refuses_a_commit_without_the_exact_token_before_touching_the_database():
    db = FakeDB([SMALL], READY)
    m, d = slw.build_level_manifest(chart_id=CHART, plan_waves=[["a_one"]], rows={"a_one": SMALL[0]}, writer_digests=SMALL_DIGESTS)
    kw = dict(chart_id=CHART, manifest=m, digest=d, row_digests={"a_one": slw.registry_row_digest(SMALL[0])}, external={})
    for confirm in (None, "", "WRONG", slw.expected_confirmation("0" * 64, 1)):
        with pytest.raises(slw.LevelWaveRefusal) as exc:
            slw.insert_run(db.connect, confirm=confirm, commit=True, **kw)
        assert exc.value.refusals[0]["code"] == "CONFIRM_TOKEN_MISMATCH"
    assert db.log == []                                      # no connection, no statement, no commit
    receipt = slw.insert_run(db.connect, confirm=slw.expected_confirmation(d, 1), commit=True, **kw)
    assert receipt["committed"] is True and db.kinds().count("commit") == 1


def test_commit_requires_a_mode(env):
    repo, git = env
    code, out = run(args_for(repo, "a_one", "--commit", "--confirm", "x"), FakeDB([SMALL], READY), git)
    assert code == 2 and "--mode" in out["error"]


def test_commit_with_the_exact_token_commits_once_and_dispatches(env):
    repo, git = env
    dry_db = FakeDB([SMALL], READY)
    _, dry = run(args_for(repo, "a_one,a_two,a_three"), dry_db, git)
    token = dry["confirm_token_single_run"]
    db = FakeDB([SMALL], READY)
    sent = []
    code, out = run(args_for(repo, "a_one,a_two,a_three", "--commit", "--confirm", token, mode="single-run"), db, git,
                    dispatch=lambda run_id: sent.append(run_id) or "executions/x1")
    assert code == 0 and out["committed"] is True and out["execution_name"] == "executions/x1"
    assert db.kinds().count("commit") == 1 and sent == [out["insert"]["run_id"]]
    # the commit comes after both kinds of insert
    sql_idx = [i for i, e in enumerate(db.log) if e[0] == "execute" and e[1].startswith("INSERT INTO")]
    assert db.log.index(("commit",)) > max(sql_idx)
    assert out["manifest_digest"] == dry["manifest_digest"]


def test_a_token_from_one_manifest_does_not_confirm_another(env):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], READY), git)
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two,a_three", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "CONFIRM_TOKEN_MISMATCH"


def test_dispatch_failure_terminalises_the_planned_run(env):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], READY), git)
    db = FakeDB([SMALL], READY)

    def boom(run_id):
        raise RuntimeError("gcloud down")
    code, out = run(args_for(repo, "a_one,a_two", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"), db, git, dispatch=boom)
    assert code == 3 and "gcloud down" in out["dispatch_error"]
    assert any("UPDATE build_runs SET state='failed'" in e[1] for e in db.statements())


def test_with_footprint_adds_the_e5_9_section_using_select_only_catalog_reads(env):
    repo, git = env
    rows = [dict(r, target_table="tbl_a" if r["asset_id"] == "a_one" else None) for r in SMALL]
    fk = [("c_fkey", "public.tbl_b", "public.tbl_a", "c", "a", ["a_id"], [], False, False, None, None, False, False)]
    db = FakeDB([rows], READY, fk_rows=fk, table_rows=[("public.tbl_a",), ("public.tbl_b",)])
    code, out = run(args_for(repo, "a_one,a_two,a_three", "--with-footprint"), db, git)
    fp = out["insert"]["footprint"]["footprint"]
    assert code == 0 and fp["write_tables"] == ["public.tbl_a"] and fp["delete_cascades"][0]["table"] == "public.tbl_b"
    assert any("Transitive write/delete footprint" in l for l in out["insert"]["footprint"]["impact_lines"])
    assert db.inserts("build_runs")                                  # the footprint did not replace the insert


# ───────────────────────── scope argument ─────────────────────────

def test_scope_forms_comma_flag_and_file(tmp_path):
    f = tmp_path / "ids.txt"
    f.write_text("# comment\na_one, a_two\na_three\n")
    assert slw.parse_asset_scope(["a_one,a_two"]) == ["a_one", "a_two"]
    assert slw.parse_asset_scope(["a_one", "a_two"]) == ["a_one", "a_two"]
    assert slw.parse_asset_scope([f"@{f}"]) == ["a_one", "a_two", "a_three"]


@pytest.mark.parametrize("bad", [["a_one,a_one"], ["a_one,,a_two"], ["A_One"], [""], ["a one"], ["@/no/such/file"]])
def test_scope_errors_are_refused_not_normalised(bad):
    with pytest.raises(slw.LevelWaveError):
        slw.parse_asset_scope(bad)


def test_level_flags_do_not_exist():
    with pytest.raises(SystemExit):
        slw.build_parser().parse_args(["--chart-id", CHART, "--level", "2", "--assets", "a"])


# ───────────────────────── stop hook ─────────────────────────

class Clock:
    def __init__(self):
        self.t = 0.0

    def mono(self):
        return self.t

    def sleep(self, s):
        self.t += s


NEXT = {"wave": 1, "assets": ["a_two"], "manifest_digest": "c" * 64}


def test_stop_hook_writes_the_pending_file_and_waits_for_the_exact_token(tmp_path):
    clock = Clock()
    token = slw.continue_token(1, "c" * 64)

    def sleeper(s):                        # the operator writes the token while the hook is waiting
        clock.sleep(s)
        (tmp_path / "after-wave-0.continue").write_text(token + "\n")
    hook = slw.file_stop_hook(tmp_path, poll_seconds=1, timeout_seconds=100, sleep=sleeper, monotonic=clock.mono)
    assert hook(0, {"ok": True}, NEXT) is True
    pending = json.loads((tmp_path / "after-wave-0.pending.json").read_text())
    assert pending["continue_token"] == token and pending["next"]["assets"] == ["a_two"] and pending["wave_done"] == 0


@pytest.mark.parametrize("answer", ["WRONG", "", "CONTINUE_WAVE_1_000000000000"])
def test_a_wrong_token_stops(tmp_path, answer):
    clock = Clock()
    (tmp_path / "after-wave-0.continue").write_text(answer)
    assert slw.file_stop_hook(tmp_path, sleep=clock.sleep, monotonic=clock.mono)(0, {}, NEXT) is False


def test_a_stop_file_stops_and_so_does_the_timeout(tmp_path):
    clock = Clock()
    (tmp_path / "after-wave-0.stop").write_text("")
    assert slw.file_stop_hook(tmp_path, sleep=clock.sleep, monotonic=clock.mono)(0, {}, NEXT) is False
    clock2 = Clock()
    hook = slw.file_stop_hook(tmp_path / "other", poll_seconds=10, timeout_seconds=35, sleep=clock2.sleep, monotonic=clock2.mono)
    assert hook(0, {}, NEXT) is False and clock2.t >= 35          # nothing continues by default


WBW_WAVES = [["w0a", "w0b"], ["w1"], ["w2"]]


def ok_report(run_id, state="complete"):
    return {"assets": [{"asset_id": a, "state": state} for a in WBW_WAVES[int(run_id.replace("run", "").replace("r", ""))]]}


def _wbw_plan():
    rows = {a: row(a, deps) for a, deps in [("w0a", []), ("w0b", []), ("w1", ["w0a"]), ("w2", ["w1", "w0b"])]}
    waves = slw.derive_waves(list(rows), {a: r["depends_on"] for a, r in rows.items()})
    return slw.make_plan(chart_id=CHART, assets=list(rows), rows=list(rows.values()),
                         writer_digests={a: _hexdigest(a) for a in rows}, deployed_digests={a: _hexdigest(a) for a in rows}), waves


def test_wave_by_wave_stops_between_waves_until_the_operator_continues():
    plan, waves = _wbw_plan()
    assert waves == [["w0a", "w0b"], ["w1"], ["w2"]]
    dispatched, hooks = [], []

    def dispatch_wave(i):
        dispatched.append(i)
        return {"run_id": f"run{i}"}

    def hook(done, summary, nxt):
        hooks.append((done, nxt["wave"], len(dispatched)))
        return len(hooks) < 2                                    # continue after wave 0, stop after wave 1
    res = slw.run_wave_by_wave(plan, dispatch_wave=dispatch_wave, wait_terminal=lambda r: {"state": "completed"},
                               wave_report=lambda r: ok_report(r), hook=hook)
    assert res["status"] == "STOPPED_BY_OPERATOR" and dispatched == [0, 1]
    assert hooks == [(0, 1, 1), (1, 2, 2)]                       # the hook ran BEFORE the next dispatch each time
    assert [w["status"] for w in res["waves"]] == ["COMPLETED", "COMPLETED"] and res["waves"][1]["hook"] == "STOP"


def test_wave_by_wave_runs_all_waves_when_the_operator_continues_each_time():
    plan, _ = _wbw_plan()
    seen = []
    res = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: seen.append(i) or {"run_id": f"r{i}"},
                               wait_terminal=lambda r: {"state": "completed"},
                               wave_report=lambda r: ok_report(r, state="skipped"),
                               hook=lambda *a: True)
    assert res["status"] == "ALL_WAVES_COMPLETED" and seen == [0, 1, 2]


@pytest.mark.parametrize("terminal,expect", [({"state": "failed"}, "STOPPED_RUN_NOT_COMPLETED"),
                                             ({"state": "timeout"}, "STOPPED_RUN_NOT_COMPLETED"),
                                             ({"state": "stopped"}, "STOPPED_RUN_NOT_COMPLETED")])
def test_a_run_that_does_not_complete_stops_before_the_hook_and_the_next_wave(terminal, expect):
    plan, _ = _wbw_plan()
    seen = []
    res = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: seen.append(i) or {"run_id": "r"}, wait_terminal=lambda r: terminal,
                               wave_report=lambda r: {"assets": []}, hook=lambda *a: pytest.fail("hook must not run"))
    assert res["status"] == expect and seen == [0]


def test_a_wave_whose_report_is_missing_or_empty_stops_it_is_not_a_pass():
    plan, _ = _wbw_plan()
    for report in ({"assets": []}, {"assets": [], "error": "no rows"}, {"assets": [{"asset_id": "w0a", "state": "complete"}]}):
        res = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": "r"}, wait_terminal=lambda r: {"state": "completed"},
                                   wave_report=lambda r: report, hook=lambda *a: pytest.fail("hook must not run"))
        assert res["status"] == "STOPPED_ASSETS_NOT_COMPLETE"


def test_a_wave_with_an_errored_asset_stops_even_if_the_run_says_completed():
    plan, _ = _wbw_plan()
    res = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": "r"}, wait_terminal=lambda r: {"state": "completed"},
                               wave_report=lambda r: {"assets": [{"asset_id": "w0a", "state": "error"}, {"asset_id": "w0b", "state": "complete"}]},
                               hook=lambda *a: pytest.fail("hook must not run"))
    assert res["status"] == "STOPPED_ASSETS_NOT_COMPLETE" and res["waves"][0]["assets_not_complete"] == ["w0a"]


def test_a_refusal_inside_a_wave_dispatch_stops_the_campaign():
    plan, _ = _wbw_plan()

    def dispatch_wave(i):
        raise slw.LevelWaveRefusal([{"code": "DEPENDENCY_NOT_READY", "detail": "w0a(receipt:stale)"}])
    res = slw.run_wave_by_wave(plan, dispatch_wave=dispatch_wave, wait_terminal=None, wave_report=None, hook=None)
    assert res["status"] == "STOPPED_REFUSED" and res["waves"][0]["refusals"][0]["code"] == "DEPENDENCY_NOT_READY"


def test_cli_wave_by_wave_dispatches_one_run_per_wave_with_its_own_manifest(env, tmp_path):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two,a_three", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    assert [w["assets"] for w in dry["per_wave"]] == [["a_one"], ["a_three", "a_two"]]
    assert dry["insert"]["assets"] == ["a_one"]                      # the dry run exercised wave 0 only
    db = FakeDB([SMALL], {**READY, "a_one": ("lit", "fresh", "data")})
    sent = []
    code, out = run(args_for(repo, "a_one,a_two,a_three", "--commit", "--confirm", dry["confirm_token_single_run"],
                             "--pause-dir", str(tmp_path / "pause"), mode="wave-by-wave"), db, git,
                    dispatch=lambda rid: sent.append(rid) or "exec",
                    hook=lambda done, summary, nxt: True,
                    sleep=lambda s: None)
    assert code == 0 and out["wave_by_wave"]["status"] == "ALL_WAVES_COMPLETED" and len(sent) == 2
    runs = [e for e in db.inserts("build_runs")]
    waves = [json.loads(r[2][4])["waves"] for r in runs]
    assert waves == [[["a_one"]], [["a_three", "a_two"]]]
    assert db.kinds().count("commit") == 2
    # wave 1's manifest lists wave 0's asset as an ordinary declared dependency
    second = json.loads(runs[1][2][4])
    assert {a["asset_id"]: a["depends_on"] for a in second["assets"]}["a_two"] == ["a_one"]


def test_cli_wave_by_wave_needs_a_confirm_for_the_whole_plan_and_a_pause_dir(env):
    repo, git = env
    code, out = run(args_for(repo, "a_one,a_two", "--commit", "--confirm", "x", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    assert code == 2 and "--pause-dir" in out["error"]
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two", "--commit", "--confirm", "x", "--pause-dir", "/tmp/x", mode="wave-by-wave"), db, git,
                    dispatch=lambda r: pytest.fail("dispatched"))
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "CONFIRM_TOKEN_MISMATCH"
    assert "commit" not in db.kinds()


# ───────────────────────── wall-time report ─────────────────────────

T0 = datetime(2026, 10, 3, 6, 0, 0, tzinfo=timezone.utc)


def _ra(asset, pos, start_s, end_s, state="complete", error=None, tp="lit"):
    return {"asset_id": asset, "position": pos, "state": state, "error": error, "throughput_state": tp,
            "started_at": None if start_s is None else T0 + timedelta(seconds=start_s),
            "ended_at": None if end_s is None else T0 + timedelta(seconds=end_s)}


def test_wall_time_report_per_asset_per_wave_and_run():
    rows = [_ra("a", 0, 0, 30), _ra("b", 1, 0, 90), _ra("c", 2, 100, 160), _ra("d", 3, 100, 130, state="skipped")]
    rep = slw.asset_wall_time_report(rows, [["a", "b"], ["c", "d"]])
    by = {a["asset_id"]: a for a in rep["assets"]}
    assert [by[x]["wall_seconds"] for x in "abcd"] == [30.0, 90.0, 60.0, 30.0]
    assert [by[x]["wave"] for x in "abcd"] == [0, 0, 1, 1] and by["d"]["state"] == "skipped"
    assert rep["per_wave"] == {"0": {"assets": 2, "wall_seconds": 90.0}, "1": {"assets": 2, "wall_seconds": 60.0}}
    assert rep["run_wall_seconds"] == 160.0 and rep["sum_asset_seconds"] == 210.0
    assert rep["slowest"][:2] == ["b", "c"] and rep["unmeasured"] == []


def test_missing_or_inverted_timestamps_are_unmeasured_never_zero():
    rows = [_ra("a", 0, 0, 30), _ra("b", 1, 10, None, state="building"), _ra("c", 2, None, None, state="aborted", error="dep"),
            _ra("d", 3, 50, 40)]
    rep = slw.asset_wall_time_report(rows, [["a"], ["b", "c", "d"]])
    by = {a["asset_id"]: a for a in rep["assets"]}
    assert by["b"]["wall_seconds"] is None and by["c"]["wall_seconds"] is None and by["d"]["wall_seconds"] is None
    assert rep["unmeasured"] == ["b", "c", "d"] and rep["per_wave"]["1"]["wall_seconds"] is None
    assert rep["run_wall_seconds"] is None and rep["sum_asset_seconds"] == 30.0


def test_wall_time_report_accepts_iso_strings_and_is_deterministic():
    rows = [dict(r, started_at=r["started_at"].isoformat() if r["started_at"] else None,
                 ended_at=r["ended_at"].isoformat() if r["ended_at"] else None) for r in [_ra("a", 0, 0, 5), _ra("b", 1, 5, 12)]]
    rep = slw.asset_wall_time_report(list(reversed(rows)), [["a"], ["b"]])
    assert [a["asset_id"] for a in rep["assets"]] == ["a", "b"] and rep["assets"][1]["wall_seconds"] == 7.0
    assert json.dumps(rep, sort_keys=True) == json.dumps(slw.asset_wall_time_report(rows, [["a"], ["b"]]), sort_keys=True)


def test_read_wall_time_report_reads_build_run_assets_and_throughput_only_by_select():
    db = FakeDB([SMALL], run_assets={"r9": [_ra("a_one", 0, 0, 12), _ra("a_two", 1, 12, 20, tp="stale")]})
    rep = slw.read_wall_time_report(db.connect, "r9", [["a_one"], ["a_two"]])
    sql = [e[1] for e in db.statements()]
    assert len(sql) == 1 and sql[0].startswith("SELECT") and "build_run_assets" in sql[0] and "asset_throughput" in sql[0]
    assert {a["asset_id"]: a["throughput_state"] for a in rep["assets"]} == {"a_one": "lit", "a_two": "stale"}
    with pytest.raises(slw.LevelWaveError):
        slw.read_wall_time_report(FakeDB([SMALL]).connect, "none")


def test_runtime_estimate_has_bounds_and_never_invents_a_measurement():
    rows = {a: row(a, timeout=t, est=e) for a, t, e in [("a", 600, None), ("b", 1800, None), ("c", 600, 40)]}
    est = slw.estimate_runtime([["a", "b"], ["c"]], rows)
    assert est["parallel_upper_bound_seconds"] == 1800 + 600 and est["serial_upper_bound_seconds"] == 3000
    assert est["measured_seconds"] is None
    rows2 = {a: row(a, timeout=600, est=e) for a, e in [("a", 10), ("b", 30), ("c", 5)]}
    assert slw.estimate_runtime([["a", "b"], ["c"]], rows2)["measured_seconds"] == 35
    rows3 = {"a": row("a", timeout=None)}
    assert slw.estimate_runtime([["a"]], rows3)["assets_without_timeout"] == ["a"]


# ───────────────────────── the 23 bo_* assets, offline ─────────────────────────

# BO23_SOURCE: the asset LIST is the 23 bo_* writers in platform/src/generated/nirmana-writer-digests.json (it equals the
# registry seed's bodha rows). depends_on: platform/scripts/seed/asset_registry_seed.ts, overridden by the rehearsal
# registry rows (127.0.0.1:55432/rehearsal, read-only SELECT through rehearsal_guard) where that row exists AND carries a
# non-empty depends_on ('rehearsal' below). The rehearsal registry holds 16 of the 23 and shows [] for several assets whose
# seed rows were rewired by migration 365 after insertion, so [] was not trusted. INDICATIVE ONLY: the live registry
# is the authority; Exec Suvarna's dry run recomputes everything.
BO23 = {
    "bo_anveshana": ["bo_sangati", "bo_karanajala", "bo_samskara", "bo_drishti", "bo_bimba", "bo_laksana"],
    "bo_arudha": ["ga_structural", "ga_positions"],
    "bo_bimba": ["bo_laksana", "bo_sudarshana", "bo_nakshatra_semantic", "bo_arudha", "bo_special_lagna", "bo_vargottama_dhana"],
    "bo_cdlm_summary": ["bo_sangati"],
    "bo_cgm_motifs": ["bo_bimba", "bo_karanajala"],
    "bo_cgm_paths": ["bo_bimba", "bo_karanajala"],
    "bo_chart_gestalt": ["bo_laksana", "bo_sangati", "bo_bimba", "bo_cgm_paths", "bo_anveshana"],
    "bo_drishti": ["bo_laksana", "bo_sangati", "bo_karanajala"],
    "bo_grounding": ["ga_yoga", "bo_laksana"],
    "bo_karanajala": ["bo_laksana", "bo_bimba", "ga_positions", "bo_sudarshana", "bo_nakshatra_semantic", "bo_arudha",
                      "bo_special_lagna", "bo_vargottama_dhana", "ga_vichara"],
    "bo_laksana": ["bg_rules", "ga_positions", "ga_strength", "ga_sensitive", "ga_panchanga", "ga_sade_sati", "ga_structural",
                   "ga_nakshatra", "ga_condition", "ga_vargas", "ga_vichara"],
    "bo_laksana_rerank": ["bo_karanajala"],
    "bo_nakshatra_semantic": ["ga_nakshatra", "ga_positions", "ga_structural"],
    "bo_pramana_mapa": ["bo_upaya", "bo_drishti", "bo_anveshana"],
    "bo_pratijna": ["bo_laksana", "bo_sangati"],
    "bo_samskara": ["bo_arudha", "bo_laksana", "bo_nakshatra_semantic", "bo_special_lagna", "bo_sudarshana", "bo_vargottama_dhana"],
    "bo_samvada": ["bo_laksana", "bo_karanajala", "bo_upaya", "bo_sangati", "bo_pramana_mapa"],
    "bo_sangati": ["bo_laksana", "bo_karanajala", "bo_sudarshana", "bo_nakshatra_semantic", "bo_arudha", "bo_special_lagna",
                   "bo_vargottama_dhana", "bo_laksana_rerank"],
    "bo_special_lagna": ["ga_sensitive"],
    "bo_sudarshana": ["ga_positions"],
    "bo_upaya": ["bo_laksana", "bo_sangati", "ga_structural", "ga_dashas", "bo_cgm_motifs"],
    "bo_vargottama_dhana": ["ga_vargas", "ga_positions"],
    "bo_yantra_mechanism": ["bo_karanajala", "bo_cgm_motifs", "bo_cgm_paths"],
}
BO23_COWRITERS = {"bo_arudha", "bo_laksana_rerank", "bo_nakshatra_semantic", "bo_special_lagna", "bo_sudarshana", "bo_vargottama_dhana"}
BO23_WAVES = [
    ["bo_arudha", "bo_laksana", "bo_nakshatra_semantic", "bo_special_lagna", "bo_sudarshana", "bo_vargottama_dhana"],
    ["bo_bimba", "bo_grounding", "bo_samskara"],
    ["bo_karanajala"],
    ["bo_cgm_motifs", "bo_cgm_paths", "bo_laksana_rerank"],
    ["bo_sangati", "bo_yantra_mechanism"],
    ["bo_cdlm_summary", "bo_drishti", "bo_pratijna", "bo_upaya"],
    ["bo_anveshana"],
    ["bo_chart_gestalt", "bo_pramana_mapa"],
    ["bo_samvada"],
]


def _bo23_rows():
    return [row(a, d, cow=a in BO23_COWRITERS, timeout=1800 if a in ("bo_grounding", "bo_laksana_rerank") else 600)
            for a, d in sorted(BO23.items())]


def test_bo23_is_exactly_the_registered_bodha_writer_set():
    inventory = json.loads((REPO / slw.WRITER_DIGESTS_REL).read_text())["writers"]
    assert sorted(BO23) == sorted(k for k in inventory if k.startswith("bo_")) and len(BO23) == 23


def test_bo23_waves_are_the_longest_path_levels():
    waves = slw.derive_waves(sorted(BO23), BO23)
    assert waves == BO23_WAVES
    assert sum(len(w) for w in waves) == 23
    wave_of = {a: i for i, w in enumerate(waves) for a in w}
    for a, deps in BO23.items():
        inside = [d for d in deps if d in BO23]
        assert all(wave_of[d] < wave_of[a] for d in inside), a                       # strictly after every in-set dependency
        assert wave_of[a] == (0 if not inside else 1 + max(wave_of[d] for d in inside)), a   # and no later than it must be


def test_bo23_external_dependencies_are_only_l0_l1_assets():
    ext = slw.external_dependencies(sorted(BO23), BO23)
    flat = sorted({d for deps in ext.values() for d in deps})
    assert flat == ["bg_rules", "ga_condition", "ga_dashas", "ga_nakshatra", "ga_panchanga", "ga_positions", "ga_sade_sati",
                    "ga_sensitive", "ga_strength", "ga_structural", "ga_vargas", "ga_vichara", "ga_yoga"]


def test_bo23_manifest_is_valid_for_the_real_runner_and_its_digest_is_pinned_for_fixture_digests():
    rows = {r["asset_id"]: r for r in _bo23_rows()}
    digests = {a: _hexdigest(a) for a in rows}
    m, d = slw.build_level_manifest(chart_id=CHART, plan_waves=BO23_WAVES, rows=rows, writer_digests=digests)
    assert [a["asset_id"] for a in m["assets"]] == [a for w in BO23_WAVES for a in w]
    assert m["scope_target"].count(",") == 22
    assert d == "49dcca56e13e34bbf1dcb07fc8e96338de35c1f6f99c403a7fba6b5ac688d99e"  # PIN: fixture rows + sha256(asset_id) digests
    validate = _runner_validate()
    assert len(validate(_as_run(m, d)).plan) == 23


def test_bo23_end_to_end_dry_run_through_the_cli_with_the_real_digest_inventory(tmp_path):
    inventory = json.loads((REPO / slw.WRITER_DIGESTS_REL).read_text())["writers"]
    repo = make_repo(tmp_path, inventory)
    git = FakeGit(family_text=family_doc(), deployed=inventory)
    ext_all = {d: ("lit", "fresh", "data") for deps in slw.external_dependencies(sorted(BO23), BO23).values() for d in deps}
    db = FakeDB([_bo23_rows()], ext_all)
    code, out = run(args_for(repo, ",".join(sorted(BO23))), db, git)
    assert code == 0 and out["asset_count"] == 23 and out["waves"] == BO23_WAVES
    assert len(out["per_wave"]) == 9 and out["committed"] is False and "commit" not in db.kinds()
    # waves 1 (bo_grounding) and 3 (bo_laksana_rerank) hold the two 1800s writers; the other seven waves are 600s
    assert out["runtime_estimate"]["parallel_upper_bound_seconds"] == 7 * 600 + 2 * 1800
    assert len(db.inserts("build_run_assets")) == 23
    assert out["never_executed_note"].startswith("NEVER EXECUTED IN PRODUCTION above 17 assets")


# ───────────────────────── documentation promises ─────────────────────────

def test_help_and_readme_state_the_never_executed_limit_and_the_missing_runner_hook():
    help_text = slw.build_parser().format_help()
    assert "NEVER EXECUTED IN PRODUCTION above 17 assets / 1 wave" in " ".join(help_text.split())
    readme = (HERE.parent / "README_level_wave.md").read_text()
    flat = " ".join(readme.split())
    assert "17 assets" in flat and "1 wave" in flat
    assert "no hook between waves" in flat and "wave-by-wave" in flat
    assert "image skew" in flat.lower() and "FAMILY_ASSETS.json" in flat


def test_the_module_never_reads_credential_files_or_runs_git_writes():
    src = (HERE.parent / "suvarna_level_wave.py").read_text()
    import re as _re
    for needle in ("pgenv", "dbenv", "git push", "git commit", "git checkout"):
        assert needle not in src, needle
    assert not _re.search(r"\.env\b|dotenv|open\([^)]*secret", src)
    assert 'os.environ.get("DATABASE_URL")' in src
