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
import re
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
        self.db.commit_calls += 1
        if self.db.fail_commit_nth == self.db.commit_calls:
            raise RuntimeError("fake connection dropped during COMMIT")
        self.db.log.append(("commit",))

    def rollback(self):
        self.db.log.append(("rollback",))

    def close(self):
        self.closed = True
        self.db.log.append(("close",))
        if self.db.close_raises_after_commit and ("commit",) in self.db.log:
            raise RuntimeError("fake close failure after commit")


class FakeDB:
    """candidates: a list of row-lists, one per candidate SELECT in order (the last repeats). deps: {asset: (state,
    freshness, kind)} for the dependency query. runs: {run_id: state or [states]} for the terminal poll."""

    def __init__(self, candidates, deps=None, active=(), run_states=None, run_assets=None, fk_rows=None, table_rows=None,
                 closure=None, fail_on=None, close_raises_after_commit=False, fail_commit_nth=None):
        self.log, self.cand, self.deps, self.active = [], list(candidates), deps or {}, list(active)
        self.closure = closure or {}
        self.fail_on = dict(fail_on or {})          # {sql substring: nth occurrence (1-based) that raises}
        self.fail_seen = {}
        self.close_raises_after_commit = close_raises_after_commit
        self.fail_commit_nth, self.commit_calls = fail_commit_nth, 0
        self.cand_calls = 0
        self.run_states = run_states or {}
        self.run_assets = run_assets or {}
        self.fk_rows, self.table_rows = fk_rows or [], table_rows or []
        self.inserted = {}

    def connect(self):
        self.log.append(("connect",))
        return FakeConn(self)

    def respond(self, sql, params):
        for needle, nth in self.fail_on.items():
            if needle in sql:
                self.fail_seen[needle] = self.fail_seen.get(needle, 0) + 1
                if self.fail_seen[needle] == nth:
                    raise RuntimeError(f"fake database failure on {needle!r}")
        if sql.startswith("SELECT ar.asset_id, COALESCE(ar.depends_on"):
            return [{"asset_id": d, "depends_on": self.closure[d]} for d in params[0] if d in self.closure]
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
            return [{"asset_id": a, "position": i, "state": "complete", "disposition": "build", "error": None, "throughput_state": "lit",
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


RUNNER_WITH_FORCE = 'force = os.environ.get("NIRMANA_FORCE_EXECUTE", "").strip().lower() in ("1", "true", "yes")\n'
ASSET_RUNNER_WITH_FORCE = "    if declared_deps is not None and has_cowriters is not None and not force:\n        return _skip()\n"
RUNNER_WITHOUT_FORCE = "def execute_run(run_id):\n    pass\n"                      # an image built before O-wave WP-2
ASSET_RUNNER_WITHOUT_FORCE = "    if declared_deps is not None and has_cowriters is not None:\n        return _skip()\n"


class FakeGit:
    """Answers the four git calls load_family_info / load_deployed_writer_digests make."""

    def __init__(self, *, family_text=None, family_listed=True, ref_ok=True, deployed=None, show_fails=False,
                 rev_map=None, remote_sha=None, remote_fails=False, remote_stdout=None,
                 runner_text=None, asset_runner_text=None, runner_show_fails=False):
        self.family_text, self.family_listed, self.ref_ok = family_text, family_listed, ref_ok
        self.deployed, self.show_fails = deployed, show_fails
        self.rev_map, self.remote_sha, self.remote_fails = dict(rev_map or {}), remote_sha, remote_fails
        self.remote_stdout = remote_stdout
        self.runner_text = RUNNER_WITH_FORCE if runner_text is None else runner_text
        self.asset_runner_text = ASSET_RUNNER_WITH_FORCE if asset_runner_text is None else asset_runner_text
        self.runner_show_fails = runner_show_fails
        self.calls = []

    def __call__(self, repo, args):
        self.calls.append(list(args))
        cp = lambda rc=0, out="", err="": subprocess.CompletedProcess(args, rc, out, err)  # noqa: E731
        if args[0] == "rev-parse":
            ref = args[2][: -len("^{commit}")] if args[2].endswith("^{commit}") else args[2]
            full = ref if re.fullmatch(r"[0-9a-f]{40}", ref) else sha_of(ref)
            return cp(0 if self.ref_ok else 128, (self.rev_map.get(ref) or full) + "\n", "" if self.ref_ok else "bad ref")
        if args[0] == "ls-remote":
            if self.remote_fails:
                return cp(128, "", "could not read from remote")
            if self.remote_stdout is not None:
                return cp(0, self.remote_stdout)
            return cp(0, f"{self.remote_sha or sha_of('origin/main')}\t{args[2]}\n")
        if args[0] == "ls-tree":
            return cp(0, slw.FAMILY_FILE_REL + "\n" if self.family_listed else "")
        if args[0] == "show":
            spec = args[1]
            if spec.endswith(slw.FAMILY_FILE_REL):
                return cp(128, "", "boom") if self.show_fails else cp(0, self.family_text)
            if spec.endswith(slw.RUNNER_REL) or spec.endswith(slw.ASSET_RUNNER_REL):
                if self.runner_show_fails:
                    return cp(128, "", "no such path at that sha")
                return cp(0, self.runner_text if spec.endswith(slw.RUNNER_REL) else self.asset_runner_text)
            if spec.endswith(slw.WRITER_DIGESTS_REL):
                return cp(0, json.dumps({"writers": self.deployed})) if self.deployed is not None else cp(128, "", "no such sha")
        raise AssertionError(f"unexpected git call {args}")


def sha_of(ref: str) -> str:
    """A stable fake 40-hex commit for a ref spelling."""
    return hashlib.sha1(ref.encode()).hexdigest()


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


def args_for(repo, assets, *extra, mode=None, deployed_sha="deadbeef", job_sha="deadbeef"):
    argv = ["--chart-id", CHART, "--assets", assets, "--repo", repo, "--deployed-sha", deployed_sha,
            "--deployed-job-sha", job_sha]
    if mode:
        argv += ["--mode", mode]
    return slw.build_parser().parse_args(argv + list(extra))


class FlushStream(io.StringIO):
    def __init__(self):
        super().__init__()
        self.flushes = 0

    def flush(self):
        self.flushes += 1
        super().flush()


def lines(out):
    return [json.loads(l) for l in out.getvalue().splitlines() if l.strip()]


class FakeLive:
    """The injected, read-only reader of the LIVE job image sha (what `gcloud run jobs describe` would answer). `queue` changes the
    answer from the next read on (a redeploy); `error` makes it unreadable."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.sha, self.error, self.queue, self.calls = sha_of("deadbeef"), None, [], 0

    def __call__(self):
        self.calls += 1
        if self.queue:
            self.sha = self.queue.pop(0)
        if self.error:
            raise slw.LevelWaveRefusal([{"code": "LIVE_JOB_IMAGE_UNREADABLE", "detail": self.error}])
        return self.sha


LIVE = FakeLive()


@pytest.fixture(autouse=True)
def _reset_live():
    LIVE.reset()
    yield


def run(args, db, git, **kw):
    out = FlushStream()
    kw.setdefault("live_reader", LIVE)
    code = slw.run_cli(args, connect=db.connect, git=git, out=out, **kw)
    return code, lines(out)[-1]


def run_all(args, db, git, **kw):
    out = FlushStream()
    kw.setdefault("live_reader", LIVE)
    code = slw.run_cli(args, connect=db.connect, git=git, out=out, **kw)
    return code, lines(out), out


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


def test_deployed_digests_file_is_an_accepted_source(env, tmp_path):
    repo, git = env
    f = tmp_path / "deployed.json"
    f.write_text(json.dumps({"writers": SMALL_DIGESTS}))
    a = slw.build_parser().parse_args(["--chart-id", CHART, "--assets", "a_one", "--repo", repo, "--deployed-digests-file", str(f),
                                         "--deployed-job-sha", "deadbeef"])
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
    reads = [i for i, s in enumerate(sql) if s.startswith("SELECT ar.asset_id, ar.layer") and "ANY(%s)" in s]
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
    (dict(family_text=family_doc(), ref_ok=False), "does not resolve"),
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


NEXT = {"wave": 1, "assets": ["a_two"], "manifest_digest": "c" * 64, "continue_token": "CONTINUE_WAVE_1_ABCDEF012345",
        "after_run_id": "run-0"}


def test_stop_hook_writes_the_pending_file_and_waits_for_the_exact_token(tmp_path):
    clock = Clock()
    token = NEXT["continue_token"]

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

    def sleeper(s):                                    # written AFTER the pending file exists: not stale
        clock.sleep(s)
        (tmp_path / "after-wave-0.continue").write_text(answer)
    assert slw.file_stop_hook(tmp_path, sleep=sleeper, monotonic=clock.mono)(0, {}, NEXT) is False


def test_a_stop_file_stops_and_so_does_the_timeout(tmp_path):
    clock = Clock()

    def sleeper(s):
        clock.sleep(s)
        (tmp_path / "after-wave-0.stop").write_text("")
    assert slw.file_stop_hook(tmp_path, sleep=sleeper, monotonic=clock.mono)(0, {}, NEXT) is False
    clock2 = Clock()
    hook = slw.file_stop_hook(tmp_path / "other", poll_seconds=10, timeout_seconds=35, sleep=clock2.sleep, monotonic=clock2.mono)
    assert hook(0, {}, NEXT) is False and clock2.t >= 35          # nothing continues by default


WBW_WAVES = [["w0a", "w0b"], ["w1"], ["w2"]]


def ok_report(run_id, state="complete", tp="lit", disposition="build", only=None):
    wave = WBW_WAVES[int(run_id.replace("run", "").replace("r", ""))]
    return {"assets": [{"asset_id": a, "state": state, "throughput_state": tp, "disposition": disposition}
                       for a in wave if only is None or a in only]}


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
                               wave_report=lambda r: ok_report(r),
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
    for report in ({"assets": []}, {"assets": [], "error": "no rows"}, ok_report("run0", only=["w0a"])):
        res = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": "r"}, wait_terminal=lambda r: {"state": "completed"},
                                   wave_report=lambda r: report, hook=lambda *a: pytest.fail("hook must not run"))
        assert res["status"] == "STOPPED_ASSETS_NOT_COMPLETE"


def test_a_wave_with_an_errored_asset_stops_even_if_the_run_says_completed():
    plan, _ = _wbw_plan()
    res = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": "r"}, wait_terminal=lambda r: {"state": "completed"},
                               wave_report=lambda r: {"assets": [{"asset_id": "w0a", "state": "error", "throughput_state": "error", "disposition": "build"},
                                                                 {"asset_id": "w0b", "state": "complete", "throughput_state": "lit", "disposition": "build"}]},
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


def test_cli_wave_by_wave_needs_a_confirm_for_the_whole_plan_and_a_pause_dir(env, tmp_path):
    repo, git = env
    code, out = run(args_for(repo, "a_one,a_two", "--commit", "--confirm", "x", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    assert code == 2 and "--pause-dir" in out["error"]
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two", "--commit", "--confirm", "x", "--pause-dir", str(tmp_path / "px"), mode="wave-by-wave"), db, git,
                    dispatch=lambda r: pytest.fail("dispatched"))
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "CONFIRM_TOKEN_MISMATCH"
    assert "commit" not in db.kinds()


# ───────────────────────── wall-time report ─────────────────────────

T0 = datetime(2026, 10, 3, 6, 0, 0, tzinfo=timezone.utc)


def _ra(asset, pos, start_s, end_s, state="complete", error=None, tp="lit", disposition="build"):
    return {"asset_id": asset, "position": pos, "state": state, "error": error, "throughput_state": tp, "disposition": disposition,
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


# ═════════════════════════ security review follow-up (H1, M1-M4, L2-L7, strategist additions) ═════════════════════════

def _full_wbw(env, tmp_path, *, db=None, hook=None, extra=(), dispatch=None, sleep=lambda s: None):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two,a_three", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    db = db or FakeDB([SMALL], {**READY, "a_one": ("lit", "fresh", "data")})
    argv = ["--commit", "--confirm", dry["confirm_token_single_run"], "--pause-dir", str(tmp_path / "pause"), *extra]
    code, lines_, out = run_all(args_for(repo, "a_one,a_two,a_three", *argv, mode="wave-by-wave"), db, git,
                                dispatch=dispatch or (lambda rid: "exec/" + rid[:8]), hook=hook, sleep=sleep)
    return code, lines_, out, db


# ── H1: the stop hook can not be released without the operator ──

def test_continue_token_is_bound_to_the_run_and_to_end_times_that_exist_only_after_the_wave():
    rep = {"assets": [{"asset_id": "x", "ended_at": "2026-10-03T06:00:05+00:00"}]}
    tok = slw.continue_token(1, "run-A", rep)
    assert tok == slw.continue_token(1, "run-A", rep) and tok.startswith("CONTINUE_WAVE_1_")
    assert tok != slw.continue_token(1, "run-B", rep)
    assert tok != slw.continue_token(1, "run-A", {"assets": [{"asset_id": "x", "ended_at": "2026-10-03T06:00:06+00:00"}]})
    assert tok != slw.continue_token(2, "run-A", rep)


def test_the_token_is_not_derivable_from_the_manifest_or_the_dry_run_output(tmp_path):
    plan, _ = _wbw_plan()
    seen = []

    def hook(done, summary, info):
        seen.append(info)
        return False
    slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": f"run{i}"}, wait_terminal=lambda r: {"state": "completed"},
                         wave_report=lambda r: ok_report(r), hook=hook)
    old_style = "CONTINUE_WAVE_1_" + plan["per_wave"][1]["manifest_digest"][:12].upper()
    assert seen[0]["continue_token"] != old_style and seen[0]["after_run_id"] == "run0"


@pytest.mark.parametrize("name", ["after-wave-0.continue", "after-wave-0.stop"])
def test_hook_refuses_a_preexisting_continue_or_stop_file_and_deletes_nothing(tmp_path, name):
    f = tmp_path / name
    f.write_text("CONTINUE_WAVE_1_ABCDEF012345")
    clock = Clock()
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        slw.file_stop_hook(tmp_path, sleep=clock.sleep, monotonic=clock.mono)(0, {}, NEXT)
    assert exc.value.refusals[0]["code"] == "STALE_HOOK_FILES" and name in exc.value.refusals[0]["files"]
    assert f.exists() and not (tmp_path / "after-wave-0.pending.json").exists()


def test_a_stale_file_for_a_later_wave_is_refused_when_that_wave_finishes_and_stops_the_campaign(tmp_path):
    plan, _ = _wbw_plan()
    (tmp_path / "after-wave-1.stop").write_text("")            # written in advance for the second pause
    clock = Clock()

    def sleeper(s):                                              # the operator answers the first pause correctly
        clock.sleep(s)
        pending = json.loads((tmp_path / "after-wave-0.pending.json").read_text())
        (tmp_path / "after-wave-0.continue").write_text(pending["continue_token"])
    res = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": f"run{i}"}, wait_terminal=lambda r: {"state": "completed"},
                               wave_report=lambda r: ok_report(r),
                               hook=slw.file_stop_hook(tmp_path, sleep=sleeper, monotonic=clock.mono))
    assert res["status"] == "STOPPED_HOOK_REFUSED" and res["waves"][1]["refusals"][0]["code"] == "STALE_HOOK_FILES"


def test_a_pause_dir_holding_hook_files_is_refused_at_campaign_start(env, tmp_path):
    repo, git = env
    pd = tmp_path / "pause"
    pd.mkdir()
    (pd / "after-wave-0.continue").write_text("CONTINUE_WAVE_1_AAAAAAAAAAAA")
    (pd / "after-wave-3.pending.json").write_text("{}")
    (pd / "after-wave-5.stop").write_text("")
    _, dry = run(args_for(repo, "a_one,a_two,a_three", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two,a_three", "--commit", "--confirm", dry["confirm_token_single_run"],
                             "--pause-dir", str(pd), mode="wave-by-wave"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "STALE_HOOK_FILES"
    assert out["refusals"][0]["files"] == ["after-wave-0.continue", "after-wave-3.pending.json", "after-wave-5.stop"]
    assert db.log == [] and (pd / "after-wave-0.continue").exists()              # nothing touched, nothing deleted


def test_a_token_pre_written_from_the_dry_run_output_never_releases_a_wave(env, tmp_path):
    """The operator-less path: take everything the dry run printed, write it as the .continue token."""
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two,a_three", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    guesses = [dry["confirm_token_single_run"], dry["per_wave"][1]["confirm_token"],
               "CONTINUE_WAVE_1_" + dry["per_wave"][1]["manifest_digest"][:12].upper(),
               "CONTINUE_WAVE_1_" + dry["manifest_digest"][:12].upper()]
    for n, guess in enumerate(guesses):
        pd = tmp_path / f"pause{n}"
        clock = Clock()

        def sleeper(s, guess=guess, pd=pd):
            clock.sleep(s)
            (pd / "after-wave-0.continue").write_text(guess)
        db = FakeDB([SMALL], {**READY, "a_one": ("lit", "fresh", "data")})
        sent = []
        code, out = run(args_for(repo, "a_one,a_two,a_three", "--commit", "--confirm", dry["confirm_token_single_run"],
                                 "--pause-dir", str(pd), mode="wave-by-wave"), db, git,
                        dispatch=lambda rid: sent.append(rid) or "x", sleep=sleeper, monotonic=clock.mono)
        assert code == slw.EXIT_CAMPAIGN_STOPPED and out["wave_by_wave"]["status"] == "STOPPED_BY_OPERATOR"
        assert len(sent) == 1                                        # wave 1 was never dispatched


def test_the_exact_token_from_the_pending_file_after_the_wave_does_release_it(env, tmp_path):
    pd = tmp_path / "pause"
    clock = Clock()

    def sleeper(s):
        clock.sleep(s)
        pending = json.loads((pd / "after-wave-0.pending.json").read_text())
        (pd / "after-wave-0.continue").write_text(pending["continue_token"] + "\n")
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two,a_three", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    db = FakeDB([SMALL], {**READY, "a_one": ("lit", "fresh", "data")})
    code, out = run(args_for(repo, "a_one,a_two,a_three", "--commit", "--confirm", dry["confirm_token_single_run"],
                             "--pause-dir", str(pd), mode="wave-by-wave"), db, git,
                    dispatch=lambda rid: "x", sleep=sleeper, monotonic=clock.mono)
    assert code == 0 and out["wave_by_wave"]["status"] == "ALL_WAVES_COMPLETED"
    assert json.loads((pd / "after-wave-0.pending.json").read_text())["next"]["after_run_id"] == out["committed_runs"][0]["run_id"]


# ── M1: every wave's outside dependencies, before anything is inserted ──

def test_wave_by_wave_dry_run_checks_the_whole_plans_outside_dependencies(env):
    repo, git = env
    stale_later = {"ext_one": ("lit", "fresh", "data"), "ext_two": ("lit", "stale", "data")}   # ext_two: a_three, wave 1
    db = FakeDB([SMALL], stale_later)
    code, out = run(args_for(repo, "a_one,a_two,a_three", mode="wave-by-wave"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["dependency"] == "ext_two"
    assert out["refusals"][0]["needed_by"] == ["a_three"]
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds()


def test_wave_by_wave_commit_refuses_before_wave_zero_is_inserted(env, tmp_path):
    stale_later = {"ext_one": ("lit", "fresh", "data"), "ext_two": ("error", "fresh", "data"), "a_one": ("lit", "fresh", "data")}
    code, lines_, out, db = _full_wbw(env, tmp_path, db=FakeDB([SMALL], stale_later))
    assert code == slw.REFUSAL_EXIT_CODE and lines_[-1]["refusals"][0]["dependency"] == "ext_two"
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds() and lines_[-1]["committed_runs"] == []


def test_the_readme_no_longer_says_later_waves_are_checked_only_at_their_own_dispatch():
    flat = " ".join((HERE.parent / "README_level_wave.md").read_text().split())
    assert "later waves' dependencies are earlier waves, which are not built yet" not in flat
    assert "outside dependencies of every wave" in flat


# ── M2: incremental output, and no escaped traceback ──

def test_every_commit_dispatch_and_wave_end_is_printed_and_flushed_before_the_summary(env, tmp_path):
    code, lines_, out, db = _full_wbw(env, tmp_path, hook=lambda *a: True)
    events = [l["event"] for l in lines_]
    assert code == 0 and events[-1] == "summary"
    assert events.count("run_committed") == 2 and events.count("run_dispatched") == 2
    assert events.count("wave_dispatched") == 2 and events.count("wave_ended") == 2 and events.count("hook_continue") == 1
    assert events.index("run_committed") < events.index("run_dispatched") < events.index("wave_ended") < events.index("hook_continue")
    first = next(l for l in lines_ if l["event"] == "run_committed")
    assert first["run_id"] and first["deployed_job_sha"] == sha_of("deadbeef") and first["wave"] == 0
    assert out.flushes >= len(lines_)


def test_a_database_error_mid_campaign_still_prints_a_summary_with_the_committed_runs(env, tmp_path):
    db = FakeDB([SMALL], {**READY, "a_one": ("lit", "fresh", "data")}, fail_on={"pg_advisory_xact_lock": 2})
    code, lines_, out, db = _full_wbw(env, tmp_path, db=db, hook=lambda *a: True)
    summ = lines_[-1]
    assert code == slw.EXIT_UNEXPECTED and summ["event"] == "summary"
    assert summ["wave_by_wave"]["status"] == "STOPPED_ERROR" and "fake database failure" in summ["wave_by_wave"]["waves"][1]["error"]
    assert [r["wave"] for r in summ["committed_runs"]] == [0] and summ["committed_runs"][0]["run_id"]
    assert any(l["event"] == "run_committed" for l in lines_[:-1])       # printed before the failure, not reconstructed after


def test_an_error_while_waiting_names_the_run_that_may_still_be_running(env, tmp_path):
    db = FakeDB([SMALL], {**READY, "a_one": ("lit", "fresh", "data")}, fail_on={"SELECT state, last_error FROM build_runs WHERE id": 1})
    code, lines_, _, _ = _full_wbw(env, tmp_path, db=db, hook=lambda *a: True)
    w0 = lines_[-1]["wave_by_wave"]["waves"][0]
    assert code == slw.EXIT_UNEXPECTED and w0["status"] == "ERROR" and w0["run_id"] in w0["note"]


def test_an_error_reading_the_wall_time_report_stops_with_the_run_id(env, tmp_path):
    db = FakeDB([SMALL], {**READY, "a_one": ("lit", "fresh", "data")}, fail_on={"FROM build_run_assets bra": 1})
    code, lines_, _, _ = _full_wbw(env, tmp_path, db=db, hook=lambda *a: True)
    w0 = lines_[-1]["wave_by_wave"]["waves"][0]
    assert code == slw.EXIT_UNEXPECTED and w0["status"] == "ERROR" and w0["run_id"]


def test_an_unexpected_error_before_any_commit_is_json_not_a_traceback(env):
    repo, git = env
    db = FakeDB([SMALL], READY, fail_on={"SELECT ar.asset_id, ar.layer": 1})
    code, out = run(args_for(repo, "a_one"), db, git)
    assert code == slw.EXIT_UNEXPECTED and out["unexpected"] is True and out["committed_runs"] == []
    assert out["warning"] == "no run was committed" and "fake database failure" in out["error"]


def test_a_failure_right_after_the_commit_still_reports_the_run(env):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two,a_three"), FakeDB([SMALL], READY), git)
    db = FakeDB([SMALL], READY, close_raises_after_commit=True)
    code, lines_, _ = run_all(args_for(repo, "a_one,a_two,a_three", "--commit", "--confirm", dry["confirm_token_single_run"],
                                       mode="single-run"), db, git, dispatch=lambda r: "x")
    assert code == slw.EXIT_UNEXPECTED and lines_[-1]["unexpected"] is True
    assert len(lines_[-1]["committed_runs"]) == 1 and lines_[-1]["committed_runs"][0]["run_id"]
    assert "find them by run_id" in lines_[-1]["warning"]


# ── M3: the deployed job sha ──

def test_a_job_sha_that_is_not_the_inventorys_commit_is_refused_before_any_database_contact(env):
    repo, git = env
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one", deployed_sha="cafebabe"), db, git)       # the inventory commit is not the live image
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "JOB_SHA_MISMATCH"
    assert out["refusals"][0]["inventory_sha"] == sha_of("cafebabe") and out["refusals"][0]["deployed_job_sha"] == sha_of("deadbeef")
    assert db.log == []


def test_nothing_has_to_be_asserted_by_hand_the_live_image_supplies_the_job_sha_and_the_inventory(env):
    repo, git = env
    a = slw.build_parser().parse_args(["--chart-id", CHART, "--assets", "a_one", "--repo", repo])
    code, out = run(a, FakeDB([SMALL], READY), git)
    assert code == 0 and out["deployed_job_sha"] == sha_of("deadbeef") == out["inventory_sha"] and out["job_sha_binding"] == "verified"
    assert LIVE.calls == 1


def test_a_stale_asserted_job_sha_is_refused_against_the_live_image(env):
    repo, git = env
    LIVE.sha = sha_of("bb143edf2")                     # the live image moved on; the operator still asserts deadbeef
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one"), db, git)
    r = out["refusals"][0]
    assert code == slw.REFUSAL_EXIT_CODE and r["code"] == "LIVE_JOB_IMAGE_DIFFERS"
    assert r["live_job_sha"] == sha_of("bb143edf2") and r["asserted_job_sha"] == sha_of("deadbeef") and db.log == []


def test_an_unreadable_live_image_refuses_fail_closed_before_any_database_contact(env):
    repo, git = env
    LIVE.error = "gcloud run jobs describe failed: PERMISSION_DENIED"
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "LIVE_JOB_IMAGE_UNREADABLE" and db.log == []


def test_a_live_image_that_changes_between_plan_and_commit_refuses_before_the_insert(env):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two", mode="single-run"), FakeDB([SMALL], READY), git)
    LIVE.reset()
    LIVE.queue = [sha_of("deadbeef"), sha_of("a redeploy")]        # read 1 = the gates, read 2 = immediately before the COMMIT
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"), db, git,
                    dispatch=lambda r: pytest.fail("dispatched"))
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "JOB_SHA_CHANGED" and "commit" not in db.kinds()


def test_the_same_commit_under_a_different_spelling_is_accepted(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    full = "a" * 40
    git = FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS, rev_map={"deadbeef": full, "deadbeef0123456789": full})
    LIVE.sha = full                                    # the live image names the commit in full
    code, out = run(args_for(repo, "a_one", job_sha="deadbeef0123456789"), FakeDB([SMALL], READY), git)
    assert code == 0 and out["deployed_job_sha"] == full and out["inventory_sha"] == full and out["job_sha_binding"] == "verified"


def test_an_unresolvable_job_sha_is_refused(env):
    repo, git = env
    git2 = FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS, ref_ok=False)
    code, out = run(args_for(repo, "a_one"), FakeDB([SMALL], READY), git2)
    assert code == slw.REFUSAL_EXIT_CODE


def test_the_deployed_job_sha_is_printed_on_every_receipt(env, tmp_path):
    code, lines_, _, _ = _full_wbw(env, tmp_path, hook=lambda *a: True)
    sha = sha_of("deadbeef")
    summ = lines_[-1]
    assert summ["deployed_job_sha"] == sha and summ["inventory_sha"] == sha
    assert all(r["deployed_job_sha"] == sha for r in summ["committed_runs"])
    assert all(l["deployed_job_sha"] == sha for l in lines_ if l["event"] in ("run_committed", "run_dispatched"))
    repo, git = env
    _, single = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], READY), git)
    assert single["insert"]["deployed_job_sha"] == sha


def test_the_live_image_is_re_read_before_every_wave_and_a_redeploy_stops_the_campaign(env, tmp_path):
    def redeploy(done, summary, info):                   # the live job image changes while the operator is paused
        LIVE.sha = sha_of("cafebabe")
        return True
    code, lines_, _, db = _full_wbw(env, tmp_path, hook=redeploy)
    summ = lines_[-1]
    assert code == slw.EXIT_CAMPAIGN_STOPPED and summ["wave_by_wave"]["status"] == "STOPPED_REFUSED"
    assert summ["wave_by_wave"]["waves"][1]["refusals"][0]["code"] == "JOB_SHA_CHANGED"
    assert len(db.inserts("build_runs")) == 1 and len(summ["committed_runs"]) == 1


def test_a_digests_file_can_not_back_a_real_dispatch(env, tmp_path):
    repo, git = env
    f = tmp_path / "deployed.json"
    f.write_text(json.dumps({"writers": SMALL_DIGESTS}))
    a = slw.build_parser().parse_args(["--chart-id", CHART, "--assets", "a_one", "--repo", repo, "--deployed-digests-file", str(f),
                                       "--deployed-job-sha", "deadbeef", "--commit", "--confirm", "x", "--mode", "single-run"])
    db = FakeDB([SMALL], READY)
    code, out = run(a, db, git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "DEPLOYED_BINDING_UNVERIFIED" and db.log == []


# ── M4: the post-COMMIT window ──

def test_the_dispatcher_module_is_loaded_before_the_first_insert(env, monkeypatch):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two,a_three"), FakeDB([SMALL], READY), git)
    monkeypatch.setattr(slw, "_load_frozen_dispatcher", lambda: (_ for _ in ()).throw(RuntimeError("cannot load dispatcher")))
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two,a_three", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"), db, git)
    assert code == slw.EXIT_UNEXPECTED and "cannot load dispatcher" in out["error"]
    assert db.log == [] and out["committed_runs"] == []


def test_a_terminalise_failure_after_commit_reports_the_run_id_and_the_chart_blocking_warning(env):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two,a_three"), FakeDB([SMALL], READY), git)
    db = FakeDB([SMALL], READY, fail_on={"UPDATE build_runs SET state='failed'": 1})

    def boom(run_id):
        raise RuntimeError("gcloud down")
    code, lines_, _ = run_all(args_for(repo, "a_one,a_two,a_three", "--commit", "--confirm", dry["confirm_token_single_run"],
                                       mode="single-run"), db, git, dispatch=boom)
    summ = lines_[-1]
    run_id = summ["insert"]["run_id"]
    assert code == slw.EXIT_DISPATCH_FAILED and "gcloud down" in summ["dispatch_error"]
    assert run_id in summ["terminalise_warning"] and "BLOCKS chart" in summ["terminalise_warning"] and CHART in summ["terminalise_warning"]
    ev = next(l for l in lines_ if l["event"] == "dispatch_failed")
    assert ev["run_id"] == run_id and "BLOCKS chart" in ev["warning"]


def test_a_successful_terminalise_leaves_no_warning(env):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], READY), git)
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"), db, git,
                    dispatch=lambda r: (_ for _ in ()).throw(RuntimeError("x")))
    assert code == slw.EXIT_DISPATCH_FAILED and out["terminalise_warning"] is None


def test_wave_by_wave_dispatch_failure_carries_the_run_id_and_the_warning(env, tmp_path):
    db = FakeDB([SMALL], {**READY, "a_one": ("lit", "fresh", "data")}, fail_on={"UPDATE build_runs SET state='failed'": 1})
    code, lines_, _, _ = _full_wbw(env, tmp_path, db=db, dispatch=lambda r: (_ for _ in ()).throw(RuntimeError("gcloud down")))
    ref = lines_[-1]["wave_by_wave"]["waves"][0]["refusals"][0]
    assert code == slw.EXIT_DISPATCH_FAILED and ref["code"] == "DISPATCH_FAILED" and ref["run_id"] in ref["terminalise_warning"]
    assert "BLOCKS chart" in ref["terminalise_warning"]


# ── L2: ordering through out-of-set assets ──

def test_waves_see_ordering_paths_through_out_of_set_assets():
    deps = {"A": ["E"], "E": ["B"], "B": []}
    assert slw.derive_waves(["A", "B"], deps) == [["B"], ["A"]]                       # A after B, via the outside E
    assert slw.derive_waves(["A", "B"], {"A": ["E1"], "E1": ["E2"], "E2": ["B"], "B": []}) == [["B"], ["A"]]
    assert slw.derive_waves(["A", "B"], {"A": ["E"], "B": []}) == [["A", "B"]]        # no information about E: no edge
    # an in-set ancestor reached only through another in-set asset is that asset's business, not a second edge
    assert slw.derive_waves(["A", "B", "C"], {"A": ["B"], "B": ["E"], "E": ["C"], "C": []}) == [["C"], ["B"], ["A"]]


def test_a_loop_through_an_outside_asset_is_a_cycle():
    with pytest.raises(slw.LevelWaveError, match="cycle"):
        slw.derive_waves(["A", "B"], {"A": ["E"], "E": ["A"], "B": []})


def test_the_dependency_closure_is_read_in_rounds_and_bounded():
    db = FakeDB([[]], closure={"e1": ["e2"], "e2": ["e3", "a_in"], "e3": []})
    rows = [row("a_in", ["e1"])]
    assert slw.read_dependency_closure(db.connect, ["a_in"], rows) == {"e1": ["e2"], "e2": ["e3", "a_in"], "e3": []}
    assert all(e[1].lstrip().startswith("SELECT") for e in db.statements())
    with pytest.raises(slw.LevelWaveError, match="converge"):
        slw.read_dependency_closure(db.connect, ["a_in"], rows, max_rounds=2)
    assert slw.read_dependency_closure(db.connect, ["a_in"], [row("a_in", ["unknown_id"])]) == {"unknown_id": []}


def test_the_cli_orders_an_asset_after_an_in_set_ancestor_reached_through_an_outside_asset(tmp_path):
    rows = [row("x_a", ["ext_mid"]), row("x_b", [])]
    digests = {r["asset_id"]: _hexdigest(r["asset_id"]) for r in rows}
    repo = make_repo(tmp_path, digests)
    git = FakeGit(family_text=family_doc(), deployed=digests)
    db = FakeDB([rows], {"ext_mid": ("lit", "fresh", "data")}, closure={"ext_mid": ["x_b"]})
    code, out = run(args_for(repo, "x_a,x_b"), db, git)
    assert code == 0 and out["waves"] == [["x_b"], ["x_a"]]
    assert out["external_dependencies"] == {"x_a": ["ext_mid"]}


# ── L3 / L5 ──

def test_a_non_per_chart_asset_is_refused(env):
    repo, git = env
    code, out = run(args_for(repo, "a_one"), FakeDB([[row("a_one", scope="global")]], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "NON_PER_CHART_SCOPE"


def test_a_no_delta_skip_is_not_success_unless_declared_and_is_always_reported():
    plan, _ = _wbw_plan()
    skip = lambda r: ok_report(r, disposition="skip_no_delta")  # noqa: E731  (state='complete', as the runner writes it)
    res = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": f"run{i}"}, wait_terminal=lambda r: {"state": "completed"},
                               wave_report=skip, hook=lambda *a: pytest.fail("no pause"))
    assert res["status"] == "STOPPED_ASSETS_NOT_COMPLETE"
    w0 = res["waves"][0]
    assert w0["assets_skipped"] == ["w0a", "w0b"] and w0["assets_not_complete"] == ["w0a", "w0b"]
    assert "not in --declared-skips" in w0["not_complete_reasons"]["w0a"]
    partial = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": f"run{i}"}, wait_terminal=lambda r: {"state": "completed"},
                                   wave_report=skip, hook=lambda *a: pytest.fail("no pause"), declared_skips=["w0a"])
    assert partial["waves"][0]["assets_not_complete"] == ["w0b"]
    ok = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": f"run{i}"}, wait_terminal=lambda r: {"state": "completed"},
                              wave_report=skip, hook=lambda *a: True, declared_skips=["w0a", "w0b", "w1", "w2"])
    assert ok["status"] == "ALL_WAVES_COMPLETED" and ok["waves"][0]["assets_skipped"] == ["w0a", "w0b"]


def test_the_dead_skipped_state_is_not_a_success_signal():
    plan, _ = _wbw_plan()
    res = slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": f"run{i}"}, wait_terminal=lambda r: {"state": "completed"},
                               wave_report=lambda r: ok_report(r, state="skipped"), hook=lambda *a: pytest.fail("no pause"),
                               declared_skips=["w0a", "w0b"])
    assert res["status"] == "STOPPED_ASSETS_NOT_COMPLETE" and "not 'complete'" in res["waves"][0]["not_complete_reasons"]["w0a"]


# ── L6: family names and the freshness of the family ref ──

@pytest.mark.parametrize("asset", ["ka_vedha_gochara", "ka_vedha_gochara_x", "bg_gochara_y"])
def test_more_gochara_family_name_patterns_are_refused(tmp_path, asset):
    repo = make_repo(tmp_path, {asset: _hexdigest(asset)})
    git = FakeGit(family_text=family_doc(), deployed={asset: _hexdigest(asset)})
    code, out = run(args_for(repo, asset), FakeDB([[row(asset)]], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "FAMILY_ASSET"


def test_the_family_ref_sha_is_printed_and_a_stale_ref_is_refused(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    fresh = FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS)
    _, out = run(args_for(repo, "a_one"), FakeDB([SMALL], READY), fresh)
    assert out["family_ref"] == {"ref": "origin/main", "sha": sha_of("origin/main"), "remote_sha": sha_of("origin/main"), "freshness": "fresh"}
    stale = FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS, remote_sha="f" * 40)
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one"), db, stale)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "FAMILY_REF_STALE" and db.log == []


def test_an_unverifiable_family_ref_is_reported_in_a_dry_run_and_refused_for_a_commit(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS, remote_fails=True)
    code, out = run(args_for(repo, "a_one"), FakeDB([SMALL], READY), git)
    assert code == 0 and out["family_ref"]["freshness"] == "unverified"
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one", "--commit", "--confirm", "x", mode="single-run"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "FAMILY_REF_UNVERIFIED" and db.log == []


def test_a_non_remote_family_ref_can_not_back_a_commit(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS)
    code, out = run(args_for(repo, "a_one", "--family-ref", "HEAD", "--commit", "--confirm", "x", mode="single-run"), FakeDB([SMALL], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "FAMILY_REF_UNVERIFIED"
    code, out = run(args_for(repo, "a_one", "--family-ref", "HEAD"), FakeDB([SMALL], READY), git)
    assert code == 0 and out["family_ref"]["freshness"] == "not_a_remote_ref"


# ── L7 and the strategist's additions ──

def test_exit_codes_are_distinct_and_documented(monkeypatch, capsys):
    codes = [slw.EXIT_NO_DATABASE_URL, slw.EXIT_BAD_INPUT, slw.EXIT_DISPATCH_FAILED, slw.REFUSAL_EXIT_CODE,
             slw.EXIT_CAMPAIGN_STOPPED, slw.EXIT_UNEXPECTED]
    assert codes == [1, 2, 3, 4, 5, 6] and slw.EXIT_INTERRUPTED == 7
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert slw.main(["--chart-id", CHART, "--assets", "a_one"]) == slw.EXIT_NO_DATABASE_URL
    flat = " ".join(slw.build_parser().format_help().split())
    for needle in ("Exit codes:", "1 DATABASE_URL missing", "6 unexpected exception or database error"):
        assert needle in flat
    readme = " ".join((HERE.parent / "README_level_wave.md").read_text().split())
    assert "| 6 |" in readme and "| 1 |" in readme


def test_help_and_readme_make_the_live_dry_run_mandatory_and_the_wave_list_indicative():
    flat_help = " ".join(slw.build_parser().format_help().split())
    flat_readme = " ".join((HERE.parent / "README_level_wave.md").read_text().split())
    for flat in (flat_help, flat_readme):
        assert "LIVE dry run" in flat and "MANDATORY before the first --commit" in flat
        assert "live wave list" in flat.lower() and "indicative" in flat
    assert "the tool reads the live job image itself" in flat_readme.lower() and "nothing is asserted by hand" in flat_readme.lower()
    assert "Trap 103" in flat_readme and "head_sha" in flat_readme


def test_commit_stays_refused_until_the_family_file_is_on_the_ref(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_listed=False, deployed=SMALL_DIGESTS)
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one", "--commit", "--confirm", "x", mode="single-run"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and "FAMILY_FILE_MISSING" in [r["code"] for r in out["refusals"]] and db.log == []


# ═════════════════════════ delta security review (MED-1 and the LOW fixes) ═════════════════════════

# ── MED-1: a build_run_assets.state of 'complete' proves nothing about the build ──

def _drive(report, *, declared=(), hook=lambda *a: True):
    plan, _ = _wbw_plan()
    return slw.run_wave_by_wave(plan, dispatch_wave=lambda i: {"run_id": f"run{i}"}, wait_terminal=lambda r: {"state": "completed"},
                                wave_report=report, hook=hook, declared_skips=declared)


def test_the_good_throughput_states_are_exactly_the_runners_success_states():
    sys.path.insert(0, str(REPO / "platform/python-sidecar"))
    try:
        from pipeline.orchestrator.runner import _SUCCESS_OUTCOMES
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"frozen runner not importable here: {exc.__class__.__name__}")
    assert slw.GOOD_THROUGHPUT_STATES == frozenset({"lit", "mature", "dormant", "service_ok"})
    assert slw.GOOD_THROUGHPUT_STATES == frozenset(_SUCCESS_OUTCOMES) - {"complete"}


@pytest.mark.parametrize("tp", ["lit", "mature", "dormant", "service_ok"])
def test_every_good_throughput_state_passes(tp):
    assert _drive(lambda r: ok_report(r, tp=tp))["status"] == "ALL_WAVES_COMPLETED"


@pytest.mark.parametrize("tp", ["incomplete", "error", "stale", "building", "absent", "", None])
def test_state_complete_with_a_bad_or_missing_throughput_state_stops_the_campaign(tp):
    res = _drive(lambda r: ok_report(r, tp=tp), hook=lambda *a: pytest.fail("no pause after a failed wave"))
    assert res["status"] == "STOPPED_ASSETS_NOT_COMPLETE"
    w0 = res["waves"][0]
    assert w0["assets_not_complete"] == ["w0a", "w0b"] and len(res["waves"]) == 1
    assert "asset_throughput.state" in w0["not_complete_reasons"]["w0a"] and repr(tp) in w0["not_complete_reasons"]["w0a"]


def test_an_incomplete_asset_in_the_LAST_wave_stops_it_never_all_waves_completed():
    # the next-wave dependency check can never see the last wave: the report is the only gate
    res = _drive(lambda r: ok_report(r, tp="incomplete") if r == "run2" else ok_report(r))
    assert res["status"] == "STOPPED_ASSETS_NOT_COMPLETE" and res["status"] != "ALL_WAVES_COMPLETED"
    assert [w["status"] for w in res["waves"]] == ["COMPLETED", "COMPLETED", "ASSETS_NOT_COMPLETE"]
    assert res["waves"][2]["assets_not_complete"] == ["w2"]


@pytest.mark.parametrize("disposition", ["withheld_protected", "deferred_no_writer", "blocked_dependency", "out_of_domain", "dormant", None])
def test_a_disposition_other_than_build_is_not_a_build(disposition):
    res = _drive(lambda r: ok_report(r, disposition=disposition))
    assert res["status"] == "STOPPED_ASSETS_NOT_COMPLETE" and "disposition" in res["waves"][0]["not_complete_reasons"]["w0a"]


def test_a_missing_report_row_names_the_asset():
    res = _drive(lambda r: ok_report(r, only=["w0a"]))
    assert res["waves"][0]["not_complete_reasons"] == {"w0b": "no build_run_assets row was reported for this asset"}


def test_the_report_sql_reads_the_disposition_and_the_report_carries_it():
    assert "bra.disposition" in slw.RUN_ASSETS_SQL
    rep = slw.asset_wall_time_report([_ra("a", 0, 0, 5, disposition="skip_no_delta")], [["a"]])
    assert rep["assets"][0]["disposition"] == "skip_no_delta"


def test_cli_wave_by_wave_stops_with_exit_5_on_an_incomplete_asset_the_runner_called_complete(env, tmp_path):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two,a_three", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    db = FakeDB([SMALL], {**READY, "a_one": ("lit", "fresh", "data")})
    real = db.respond

    def respond(sql, params):
        rows = real(sql, params)
        if "FROM build_run_assets bra" in sql:
            for r in rows:
                r["throughput_state"] = "incomplete"
        return rows
    db.respond = respond
    code, lines_, _ = run_all(args_for(repo, "a_one,a_two,a_three", "--commit", "--confirm", dry["confirm_token_single_run"],
                                       "--pause-dir", str(tmp_path / "p"), mode="wave-by-wave"),
                              db, git, dispatch=lambda r: "x", hook=lambda *a: pytest.fail("no pause"), sleep=lambda s: None)
    assert code == slw.EXIT_CAMPAIGN_STOPPED and lines_[-1]["wave_by_wave"]["status"] == "STOPPED_ASSETS_NOT_COMPLETE"
    assert any(l["event"] == "wave_assets_not_complete" for l in lines_)
    assert len(db.inserts("build_runs")) == 1


# ── LOW: timeouts, no prompts, no stdin ──

def test_git_never_prompts_never_reads_stdin_and_is_time_limited(monkeypatch):
    seen = {}

    def fake_run(cmd, **kw):
        seen.update(kw)
        raise subprocess.TimeoutExpired(cmd, kw["timeout"])
    monkeypatch.setattr(slw.subprocess, "run", fake_run)
    cp = slw._git("/repo", ["ls-remote", "origin", "refs/heads/main"])
    assert seen["timeout"] == slw.GIT_TIMEOUT_SECONDS and seen["stdin"] == subprocess.DEVNULL
    assert seen["env"]["GIT_TERMINAL_PROMPT"] == "0"
    assert cp.returncode == 124 and "timed out" in cp.stderr
    # a timed-out ls-remote reads as unverified, never as fresh
    st = slw.family_ref_status("/repo", "origin/main", git=lambda repo, args: cp if args[0] == "ls-remote" else
                               subprocess.CompletedProcess(args, 0, "a" * 40 + "\n", ""))
    assert st["freshness"] == "unverified"


def test_gcloud_dispatch_has_a_timeout_no_stdin_and_the_same_command_as_the_existing_dispatcher(monkeypatch):
    calls = []

    def runner(cmd, **kw):
        calls.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, 0, "executions/e1\n", "")
    assert slw.dispatch_run_with_timeout(run_id="r1", project="p", region="g", job="j", run_command=runner) == "executions/e1"
    cmd, kw = calls[0]
    assert kw["timeout"] == slw.GCLOUD_TIMEOUT_SECONDS and kw["stdin"] == subprocess.DEVNULL
    assert kw["env"]["CLOUDSDK_CORE_DISABLE_PROMPTS"] == "1"
    old = _frozen_dispatcher()
    monkeypatch.setattr(old.subprocess, "run", lambda c, **k: subprocess.CompletedProcess(c, 0, "x\n", "") if calls.append((c, k)) is None else None)
    old.dispatch_run(run_id="r1", project="p", region="g", job="j")
    assert calls[1][0] == cmd                                     # byte-for-byte the same gcloud command


def test_gcloud_timeout_is_an_error_that_says_the_outcome_is_unknown():
    def runner(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw["timeout"])
    with pytest.raises(RuntimeError, match="outcome unknown"):
        slw.dispatch_run_with_timeout(run_id="r", project="p", region="g", job="j", run_command=runner)
    for rc, out, err in ((1, "", "denied"), (0, "", "")):
        with pytest.raises(RuntimeError):
            slw.dispatch_run_with_timeout(run_id="r", project="p", region="g", job="j",
                                          run_command=lambda c, **k: subprocess.CompletedProcess(c, rc, out, err))


def test_the_default_dispatch_refuses_before_any_process_starts(monkeypatch):
    """No runner injected and not the authorised --commit path: the call refuses; no process runner is ever called."""
    started = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: started.append(a) or subprocess.CompletedProcess(a, 0, "x\n", ""))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: started.append(a))
    with pytest.raises(RuntimeError, match="dispatch refused"):
        slw.dispatch_run_with_timeout(run_id="r", project="p", region="g", job="j")
    with pytest.raises(RuntimeError, match="dispatch refused"):
        slw.dispatch_run_with_timeout(run_id="r", project="p", region="g", job="j", force_execute=True, authorised=False)
    assert started == []


def test_the_authorised_runner_is_resolved_at_call_time_not_bound_at_import(monkeypatch):
    """authorised=True uses subprocess.run as it is AT CALL TIME (a later patch is honoured), with the same command as before."""
    import inspect
    assert inspect.signature(slw.dispatch_run_with_timeout).parameters["run_command"].default is None   # no import-time binding
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: calls.append((cmd, kw)) or subprocess.CompletedProcess(cmd, 0, "executions/e9\n", ""))
    assert slw.dispatch_run_with_timeout(run_id="r9", project="p", region="g", job="j", authorised=True) == "executions/e9"
    cmd, kw = calls[0]
    assert cmd == slw.dispatch_command(run_id="r9", project="p", region="g", job="j", force_execute=False)
    assert kw["timeout"] == slw.GCLOUD_TIMEOUT_SECONDS and kw["stdin"] == subprocess.DEVNULL
    assert kw["env"]["CLOUDSDK_CORE_DISABLE_PROMPTS"] == "1"


def test_an_injected_runner_wins_over_the_real_one_even_when_authorised(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("the real runner must not be used when one is injected"))
    seen = []
    runner = lambda cmd, **kw: seen.append(cmd) or subprocess.CompletedProcess(cmd, 0, "executions/i\n", "")   # noqa: E731
    assert slw.dispatch_run_with_timeout(run_id="r", project="p", region="g", job="j", run_command=runner, authorised=True) == "executions/i"
    assert len(seen) == 1


def test_only_a_correct_commit_invocation_asks_for_the_real_runner(env, monkeypatch):
    """A correct --commit + token run dispatches with authorised=True and the same job/force arguments as before; a dry run
    (and a refused --commit) never calls the dispatcher at all."""
    repo, git = env
    sent = []
    monkeypatch.setattr(slw, "dispatch_run_with_timeout", lambda **kw: sent.append(kw) or "executions/x")
    _, dry = run(args_for(repo, "a_one"), FakeDB([SMALL], READY), git)
    assert sent == []                                                       # plan: no dispatch
    bad_code, _ = run(args_for(repo, "a_one", "--commit", "--confirm", "WRONG", mode="single-run"), FakeDB([SMALL], READY), git)
    assert bad_code != 0 and sent == []                                     # wrong token: refused, no dispatch
    code, _ = run(args_for(repo, "a_one", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"),
                  FakeDB([SMALL], READY), git)
    assert code == 0 and len(sent) == 1
    assert sent[0]["authorised"] is True and sent[0]["job"] == "brahma-build-pipeline-job" and sent[0]["force_execute"] is False


def test_the_cli_dispatches_through_the_timeout_wrapper_by_default(env, monkeypatch):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], READY), git)
    sent = []
    monkeypatch.setattr(slw, "dispatch_run_with_timeout", lambda **kw: sent.append(kw) or "executions/x")
    code, out = run(args_for(repo, "a_one,a_two", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"),
                    FakeDB([SMALL], READY), git)
    assert code == 0 and sent and sent[0]["job"] == "brahma-build-pipeline-job"


# ── LOW: every ls-remote line is parsed ──

@pytest.mark.parametrize("stdout,expect", [
    (f"{'1' * 40}\trefs/heads/main\n", "stale"),
    (f"{'2' * 40}\trefs/heads/other\n{sha_of('origin/main')}\trefs/heads/main\n", "fresh"),       # tab/space tolerant, extra line ignored
    (f"{sha_of('origin/main')}\trefs/heads/main\n{'3' * 40}\trefs/heads/main\n", "unverified"),  # two different tips
    ("", "unverified"), ("garbage\n", "unverified"), (f"{'z' * 40}\trefs/heads/main\n", "unverified"),
    (f"{sha_of('origin/main')}\trefs/heads/main\n{sha_of('origin/main')}\trefs/heads/main\n", "fresh"),
])
def test_ls_remote_output_is_parsed_line_by_line(stdout, expect):
    git = FakeGit(remote_stdout=stdout)
    assert slw.family_ref_status("/r", "origin/main", git=git)["freshness"] == expect


# ── the live image reading itself: gcloud injected, fail closed ──

IMG = "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:"


def _runner(stdout="", rc=0, stderr="", raises=None, seen=None):
    def runner(cmd, **kw):
        if seen is not None:
            seen.append((cmd, kw))
        if raises:
            raise raises
        return subprocess.CompletedProcess(cmd, rc, stdout, stderr)
    return runner


def test_the_live_image_is_read_with_a_read_only_describe_and_the_tag_is_the_sha():
    seen = []
    sha = "0123456789abcdef0123456789abcdef01234567"
    got = slw.read_live_job_sha(job="j", project="p", region="r", run_command=_runner(IMG + sha + "\n", seen=seen))
    assert got == sha
    cmd, kw = seen[0]
    assert cmd[:5] == ["gcloud", "run", "jobs", "describe", "j"] and "--project=p" in cmd and "--region=r" in cmd
    assert "--format=value(spec.template.spec.template.spec.containers[0].image)" in cmd
    assert not any(w in cmd for w in ("execute", "update", "create", "delete", "replace")) and kw["timeout"] == slw.GCLOUD_TIMEOUT_SECONDS


def test_a_digest_after_the_tag_is_ignored():
    sha = "a" * 40
    assert slw.parse_image_sha(IMG + sha + "@sha256:" + "b" * 64) == sha


@pytest.mark.parametrize("image", ["", "\n", IMG + "latest", IMG + "deadbeef", IMG + "A" * 40, "host:5000/amjis/brahma-pipeline",
                                   "amjis/brahma-pipeline@sha256:" + "b" * 64, IMG + "a" * 40 + "\n" + IMG + "b" * 40])
def test_an_image_without_a_full_commit_sha_tag_is_unreadable(image):
    with pytest.raises(slw.LevelWaveRefusal) as ei:
        slw.parse_image_sha(image)
    assert ei.value.refusals[0]["code"] == "LIVE_JOB_IMAGE_UNREADABLE"


@pytest.mark.parametrize("runner", [
    _runner(rc=1, stderr="PERMISSION_DENIED"), _runner(rc=0, stdout=""), _runner(raises=subprocess.TimeoutExpired("gcloud", 1)),
    _runner(raises=FileNotFoundError("gcloud")), _runner(stdout=IMG + "latest")])
def test_any_gcloud_failure_refuses_fail_closed(runner):
    with pytest.raises(slw.LevelWaveRefusal) as ei:
        slw.read_live_job_sha(job="j", project="p", region="r", run_command=runner)
    assert ei.value.refusals[0]["code"] == "LIVE_JOB_IMAGE_UNREADABLE"


def test_the_cli_reads_the_image_through_the_injected_gcloud_runner(env):
    repo, git = env
    args = args_for(repo, "a_one")
    seen = []
    out = FlushStream()
    reader = slw.live_reader_for(args, run_command=_runner(IMG + sha_of("deadbeef") + "\n", seen=seen))
    code = slw.run_cli(args, connect=FakeDB([SMALL], READY).connect, git=git, out=out, live_reader=reader)
    assert code == 0 and len(seen) == 1 and seen[0][0][4] == "brahma-build-pipeline-job"
    out = FlushStream()
    reader = slw.live_reader_for(args, run_command=_runner(rc=1, stderr="boom"))
    code = slw.run_cli(args, connect=FakeDB([SMALL], READY).connect, git=git, out=out, live_reader=reader)
    assert code == slw.REFUSAL_EXIT_CODE and lines(out)[-1]["refusals"][0]["code"] == "LIVE_JOB_IMAGE_UNREADABLE"


def test_a_live_read_that_fails_on_a_later_re_read_stops_the_campaign(env, tmp_path):
    def corrupt(done, summary, info):
        LIVE.error = "gcloud timed out"
        return True
    code, lines_, _, db = _full_wbw(env, tmp_path, hook=corrupt)
    assert lines_[-1]["wave_by_wave"]["waves"][1]["refusals"][0]["code"] == "LIVE_JOB_IMAGE_UNREADABLE" and len(db.inserts("build_runs")) == 1


# ── LOW: a half-written .continue is not a false STOP ──

def test_an_empty_or_partial_continue_file_is_re_polled_before_it_counts_as_wrong(tmp_path):
    clock = Clock()
    token = NEXT["continue_token"]
    steps = iter([token[:10], token[:20], token])
    state = {"phase": 0}

    def sleeper(s):
        clock.sleep(s)
        if state["phase"] == 0:                       # the operator's editor creates the file empty ...
            (tmp_path / "after-wave-0.continue").write_text("")
            state["phase"] = 1
        else:                                          # ... then fills it in over a few reads
            (tmp_path / "after-wave-0.continue").write_text(next(steps))
    assert slw.file_stop_hook(tmp_path, sleep=sleeper, monotonic=clock.mono)(0, {}, NEXT) is True


def test_a_wrong_but_complete_token_stops_after_a_bounded_number_of_re_reads(tmp_path):
    clock = Clock()
    sleeps = []

    def sleeper(s):
        sleeps.append(s)
        clock.sleep(s)
        (tmp_path / "after-wave-0.continue").write_text("CONTINUE_WAVE_1_WRONGWRONG12")
    hook = slw.file_stop_hook(tmp_path, settle_attempts=4, settle_seconds=0.5, sleep=sleeper, monotonic=clock.mono)
    assert hook(0, {}, NEXT) is False
    assert sleeps.count(0.5) == 3                       # attempts - 1 re-polls, then the verdict


def test_a_stop_file_created_while_settling_wins(tmp_path):
    clock = Clock()

    def sleeper(s):
        clock.sleep(s)
        (tmp_path / "after-wave-0.continue").write_text("")
        (tmp_path / "after-wave-0.stop").write_text("")
    assert slw.file_stop_hook(tmp_path, sleep=sleeper, monotonic=clock.mono)(0, {}, NEXT) is False


# ── LOW: private files ──

def test_the_pause_dir_is_0700_and_the_pending_file_0600(tmp_path):
    pd = tmp_path / "pause"
    pd.mkdir(mode=0o755)
    clock = Clock()

    def sleeper(s):
        clock.sleep(s)
        (pd / "after-wave-0.stop").write_text("")
    slw.file_stop_hook(pd, sleep=sleeper, monotonic=clock.mono)(0, {}, NEXT)
    assert (pd.stat().st_mode & 0o777) == 0o700
    assert ((pd / "after-wave-0.pending.json").stat().st_mode & 0o777) == 0o600
    fresh = tmp_path / "new" / "deeper"
    slw.file_stop_hook(fresh, sleep=sleeper2(fresh), monotonic=Clock().mono)(0, {}, NEXT)
    assert (fresh.stat().st_mode & 0o777) == 0o700


def sleeper2(pd):
    def s(_):
        (pd / "after-wave-0.stop").write_text("")
    return s


# ── LOW: wave-by-wave dispatch failure exits 3 (the documented code) ──

def test_a_wave_by_wave_dispatch_failure_exits_3_like_single_run(env, tmp_path):
    code, lines_, _, _ = _full_wbw(env, tmp_path, dispatch=lambda r: (_ for _ in ()).throw(RuntimeError("gcloud down")))
    assert code == slw.EXIT_DISPATCH_FAILED == 3
    assert lines_[-1]["wave_by_wave"]["status"] == "STOPPED_REFUSED"
    readme = " ".join((HERE.parent / "README_level_wave.md").read_text().split())
    assert "| 3 | dispatch failed after the run was committed" in readme and "wave-by-wave too" in readme


# ── LOW: out-of-set intermediates that may go stale ──

def test_at_risk_intermediates_name_the_outside_asset_its_in_set_ancestor_and_who_needs_it():
    deps = {"A": ["E"], "E": ["B"], "B": [], "C": ["F"], "F": ["ga_x"], "ga_x": []}
    assert slw.at_risk_intermediates(["A", "B", "C"], deps) == [{"asset": "E", "depends_on_in_set": ["B"], "needed_by": ["A"]}]
    deps2 = {"A": ["E1"], "E1": ["E2"], "E2": ["B"], "B": []}
    assert slw.at_risk_intermediates(["A", "B"], deps2) == [
        {"asset": "E1", "depends_on_in_set": ["B"], "needed_by": ["A"]}, {"asset": "E2", "depends_on_in_set": ["B"], "needed_by": ["A"]}]
    assert slw.at_risk_intermediates(["A", "B"], {"A": ["E"], "B": []}) == []
    assert slw.at_risk_intermediates(["A"], {"A": ["E"], "E": ["F"], "F": ["E"]}) == []          # a loop outside is finite


def test_the_summary_lists_the_at_risk_intermediates_before_the_live_run(tmp_path):
    rows = [row("x_a", ["ext_mid"]), row("x_b", [])]
    digests = {r["asset_id"]: _hexdigest(r["asset_id"]) for r in rows}
    repo = make_repo(tmp_path, digests)
    git = FakeGit(family_text=family_doc(), deployed=digests)
    db = FakeDB([rows], {"ext_mid": ("lit", "fresh", "data")}, closure={"ext_mid": ["x_b"]})
    _, out = run(args_for(repo, "x_a,x_b"), db, git)
    assert out["out_of_set_intermediates_at_risk"] == [{"asset": "ext_mid", "depends_on_in_set": ["x_b"], "needed_by": ["x_a"]}]
    _, quiet = run(args_for(make_repo(tmp_path / "q", SMALL_DIGESTS), "a_one,a_two"), FakeDB([SMALL], READY), FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS))
    assert quiet["out_of_set_intermediates_at_risk"] == []


# ── LOW: a COMMIT whose outcome is unknown ──

def test_a_connection_that_drops_during_commit_is_reported_as_outcome_unknown_never_as_not_committed(env):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], READY), git)
    db = FakeDB([SMALL], READY, fail_commit_nth=1)
    code, lines_, _ = run_all(args_for(repo, "a_one,a_two", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"),
                              db, git, dispatch=lambda r: pytest.fail("must not dispatch an unknown-outcome run"))
    last = lines_[-1]
    assert code == slw.EXIT_UNEXPECTED and last["commit_outcome_unknown"] is True and last["run_id"]
    assert "COMMIT outcome unknown" in last["error"] and "ACTIVE_RUN" in last["error"] and last["run_id"] in last["error"]
    assert last["warning"] != "no run was committed" and "no run was committed" not in json.dumps(last)


def test_wave_by_wave_unknown_commit_stops_with_the_run_id(env, tmp_path):
    db = FakeDB([SMALL], {**READY, "a_one": ("lit", "fresh", "data")}, fail_commit_nth=1)
    code, lines_, _, _ = _full_wbw(env, tmp_path, db=db, hook=lambda *a: True)
    w0 = lines_[-1]["wave_by_wave"]["waves"][0]
    assert code == slw.EXIT_UNEXPECTED and w0["commit_outcome_unknown"] is True and w0["run_id"] in w0["error"]
    assert "COMMIT outcome unknown" in w0["error"] and lines_[-1]["committed_runs"] == []


# ── LOW: Ctrl-C / SIGTERM between commit and dispatch ──

def test_an_interrupt_between_commit_and_dispatch_prints_the_run_id_and_the_chart_blocking_warning(env):
    repo, git = env
    _, dry = run(args_for(repo, "a_one,a_two"), FakeDB([SMALL], READY), git)

    def interrupted(run_id):
        raise KeyboardInterrupt
    code, lines_, _ = run_all(args_for(repo, "a_one,a_two", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"),
                              FakeDB([SMALL], READY), git, dispatch=interrupted)
    last = lines_[-1]
    run_id = last["committed_runs"][0]["run_id"]
    assert code == slw.EXIT_INTERRUPTED == 7 and last["event"] == "interrupted"
    assert run_id in last["warning"] and "BLOCKS chart" in last["warning"] and CHART in last["warning"]
    assert any(l["event"] == "run_committed" for l in lines_[:-1])


def test_an_interrupt_during_a_pause_lists_the_runs_so_far(env, tmp_path):
    def ctrl_c(*a):
        raise KeyboardInterrupt
    code, lines_, _, _ = _full_wbw(env, tmp_path, hook=ctrl_c)
    last = lines_[-1]
    assert code == slw.EXIT_INTERRUPTED and len(last["committed_runs"]) == 1 and last["committed_runs"][0]["run_id"] in last["warning"]


def test_an_interrupt_before_any_commit_does_not_claim_a_run_exists(env):
    repo, git = env
    db = FakeDB([SMALL], READY)
    real = db.respond

    def respond(sql, params):
        if sql.startswith("SELECT ar.asset_id, ar.layer"):
            raise KeyboardInterrupt
        return real(sql, params)
    db.respond = respond
    code, out = run(args_for(repo, "a_one"), db, git)
    assert code == slw.EXIT_INTERRUPTED and out["committed_runs"] == [] and "no run id is known" in out["warning"]


def test_main_turns_sigterm_into_the_same_interrupt_path(monkeypatch):
    import signal as _signal
    monkeypatch.setenv("DATABASE_URL", "postgresql://x/y")
    monkeypatch.setattr(slw, "_psycopg_connect_factory", lambda url: None)
    seen = {}
    old = _signal.getsignal(_signal.SIGTERM)

    def fake_run_cli(args, **kw):
        seen["handler"] = _signal.getsignal(_signal.SIGTERM)
        return 0
    monkeypatch.setattr(slw, "run_cli", fake_run_cli)
    try:
        assert slw.main(["--chart-id", CHART, "--assets", "a_one"]) == 0
        with pytest.raises(KeyboardInterrupt):
            seen["handler"](_signal.SIGTERM, None)
    finally:
        _signal.signal(_signal.SIGTERM, old)


def test_readme_and_help_document_exit_7_and_the_new_rules():
    flat = " ".join((HERE.parent / "README_level_wave.md").read_text().split())
    assert "| 7 |" in flat and "GOOD_THROUGHPUT_STATES" in flat and "skip_no_delta" in flat
    assert "full commit sha" in flat and "`--job-sha-file` no longer exists" in flat
    assert "7 interrupted" in " ".join(slw.build_parser().format_help().split())


# ═════════════════════════ --force-execute (NIRMANA_FORCE_EXECUTE per dispatch) ═════════════════════════

BASE_CMD = ["gcloud", "run", "jobs", "execute", "j", "--project=p", "--region=g", "--args=--run-id,r1"]
TAIL = ["--async", "--format=value(metadata.name)"]


def test_gcloud_command_is_pinned_byte_for_byte_with_and_without_force(monkeypatch):
    kw = dict(run_id="r1", project="p", region="g", job="j")
    assert slw.dispatch_command(**kw) == BASE_CMD + TAIL
    assert slw.dispatch_command(**kw, force_execute=False) == BASE_CMD + TAIL
    assert slw.dispatch_command(**kw, force_execute=True) == BASE_CMD + ["--update-env-vars=NIRMANA_FORCE_EXECUTE=1"] + TAIL
    seen = []

    def runner(cmd, **k):
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "executions/e\n", "")
    slw.dispatch_run_with_timeout(run_command=runner, **kw)
    slw.dispatch_run_with_timeout(run_command=runner, force_execute=True, **kw)
    assert seen[0] == BASE_CMD + TAIL and seen[1] == BASE_CMD + ["--update-env-vars=NIRMANA_FORCE_EXECUTE=1"] + TAIL
    # the un-forced command is still the existing dispatcher's own command
    old = _frozen_dispatcher()
    got = []
    monkeypatch.setattr(old.subprocess, "run", lambda c, **k: got.append(c) or subprocess.CompletedProcess(c, 0, "x\n", ""))
    old.dispatch_run(**kw)
    assert got[0] == seen[0]


def test_the_env_var_name_is_the_one_the_runner_reads():
    src = (REPO / "platform/python-sidecar/pipeline/orchestrator/runner.py").read_text()
    assert f'os.environ.get("{slw.FORCE_ENV_VAR}"' in src


def test_force_is_off_by_default():
    a = slw.build_parser().parse_args(["--chart-id", CHART, "--assets", "a_one", "--deployed-job-sha", "x"])
    assert a.force_execute is False
    assert slw.build_parser().parse_args(["--chart-id", CHART, "--assets", "a_one", "--force-execute"]).force_execute is True


def test_the_force_token_differs_from_the_normal_token_and_keeps_the_suffix():
    d = "a" * 64
    n, f = slw.expected_confirmation(d, 1), slw.expected_confirmation(d, 1, True)
    assert n == "1ASSETS_AAAAAAAAAAAA_FROZEN_REBUILD" and f == "1ASSETS_AAAAAAAAAAAA_FORCE_FROZEN_REBUILD" and n != f
    assert slw.expected_confirmation(d, 1, False) == n


def test_a_force_dry_run_previews_the_force_token_and_dispatches_nothing(env):
    repo, git = env
    _, plain = run(args_for(repo, "a_one"), FakeDB([SMALL], READY), git)
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one", "--force-execute"), db, git, dispatch=lambda r: pytest.fail("dry run dispatched"))
    assert code == 0 and out["force_execute"] is True and plain["force_execute"] is False
    assert out["confirm_token_single_run"].endswith("_FORCE_FROZEN_REBUILD") and out["confirm_token_single_run"] != plain["confirm_token_single_run"]
    assert out["manifest_digest"] == plain["manifest_digest"]                  # force is not part of the manifest
    assert out["insert"]["force_execute"] is True and "commit" not in db.kinds()


def test_force_commit_dispatches_with_the_flag_and_every_receipt_carries_it(env, monkeypatch):
    repo, git = env
    _, dry = run(args_for(repo, "a_one", "--force-execute"), FakeDB([SMALL], READY), git)
    sent = []
    monkeypatch.setattr(slw, "dispatch_run_with_timeout", lambda **kw: sent.append(kw) or "executions/x")
    code, lines_, _ = run_all(args_for(repo, "a_one", "--force-execute", "--commit", "--confirm", dry["confirm_token_single_run"],
                                       mode="single-run"), FakeDB([SMALL], READY), git)
    assert code == 0 and sent[0]["force_execute"] is True
    assert all(l["force_execute"] is True for l in lines_ if l["event"] in ("run_committed", "run_dispatched"))
    assert lines_[-1]["force_execute"] is True and lines_[-1]["committed_runs"][0]["force_execute"] is True
    assert lines_[-1]["insert"]["force_execute"] is True


def test_a_normal_commit_never_forces(env, monkeypatch):
    repo, git = env
    _, dry = run(args_for(repo, "a_one"), FakeDB([SMALL], READY), git)
    sent = []
    monkeypatch.setattr(slw, "dispatch_run_with_timeout", lambda **kw: sent.append(kw) or "executions/x")
    code, lines_, _ = run_all(args_for(repo, "a_one", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"),
                              FakeDB([SMALL], READY), git)
    assert code == 0 and sent[0]["force_execute"] is False and lines_[-1]["force_execute"] is False


def test_the_token_is_bound_to_the_force_flag_in_both_directions(env):
    repo, git = env
    _, plain = run(args_for(repo, "a_one"), FakeDB([SMALL], READY), git)
    _, forced = run(args_for(repo, "a_one", "--force-execute"), FakeDB([SMALL], READY), git)
    for flag, token in ((["--force-execute"], plain["confirm_token_single_run"]), ([], forced["confirm_token_single_run"])):
        db = FakeDB([SMALL], READY)
        code, out = run(args_for(repo, "a_one", *flag, "--commit", "--confirm", token, mode="single-run"), db, git,
                        dispatch=lambda r: pytest.fail("dispatched"))
        assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "CONFIRM_TOKEN_MISMATCH"
        assert "commit" not in db.kinds() and db.inserts("build_runs") == []


def test_insert_run_itself_binds_the_token_to_force():
    db = FakeDB([SMALL], READY)
    m, d = slw.build_level_manifest(chart_id=CHART, plan_waves=[["a_one"]], rows={"a_one": SMALL[0]}, writer_digests=SMALL_DIGESTS)
    kw = dict(chart_id=CHART, manifest=m, digest=d, row_digests={"a_one": slw.registry_row_digest(SMALL[0])}, external={}, commit=True)
    with pytest.raises(slw.LevelWaveRefusal):
        slw.insert_run(db.connect, confirm=slw.expected_confirmation(d, 1), force_execute=True, **kw)
    with pytest.raises(slw.LevelWaveRefusal):
        slw.insert_run(db.connect, confirm=slw.expected_confirmation(d, 1, True), force_execute=False, **kw)
    assert db.log == []
    assert slw.insert_run(db.connect, confirm=slw.expected_confirmation(d, 1, True), force_execute=True, **kw)["committed"] is True


def test_force_is_refused_for_a_multi_asset_plan_even_with_non_family_assets(env):
    repo, git = env
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one,a_two", "--force-execute"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and [r["code"] for r in out["refusals"]] == ["FORCE_MULTI_ASSET"]
    assert db.log == []
    code, out = run(args_for(repo, "a_one,a_two,a_three", "--force-execute", "--commit", "--confirm", "x", mode="single-run"), FakeDB([SMALL], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "FORCE_MULTI_ASSET"


@pytest.mark.parametrize("asset", ["ka_gochara", "ka_vedha_gochara_x", "bg_gochara_y", "gochara_z"])
def test_force_is_refused_for_a_family_name_pattern_asset_even_alone(tmp_path, asset):
    repo = make_repo(tmp_path, {asset: _hexdigest(asset)})
    git = FakeGit(family_text=family_doc(), deployed={asset: _hexdigest(asset)})
    db = FakeDB([[row(asset)]], READY)
    code, out = run(args_for(repo, asset, "--force-execute"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and "FORCE_FAMILY_ASSET" in [r["code"] for r in out["refusals"]] and db.log == []


def test_force_is_refused_for_a_family_set_member_with_an_ordinary_name_even_alone(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_text=family_doc(family_sangam=["a_two"]), deployed=SMALL_DIGESTS)
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_two", "--force-execute"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and ("FORCE_FAMILY_ASSET", "a_two") in [(r["code"], r.get("asset")) for r in out["refusals"]]
    assert db.log == []


def test_the_force_family_refusal_stands_on_its_own(tmp_path, monkeypatch):
    """Even if the ordinary family check were bypassed, force still refuses a family asset."""
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_text=family_doc(family_sangam=["a_two"]), deployed=SMALL_DIGESTS)
    monkeypatch.setattr(slw, "family_refusals", lambda *a, **k: [])
    code, out = run(args_for(repo, "a_two", "--force-execute"), FakeDB([SMALL], READY), git)
    assert code == slw.REFUSAL_EXIT_CODE and [r["code"] for r in out["refusals"]] == ["FORCE_FAMILY_ASSET"]
    assert slw.force_refusals(["a_one"], {"state": "absent"}) == []
    assert slw.force_refusals(["ka_gochara"], {"state": "absent"})[0]["code"] == "FORCE_FAMILY_ASSET"


def test_a_single_non_family_asset_passes_the_force_checks():
    fam = {"state": "present", "family_set": frozenset({"other"})}
    assert slw.force_refusals(["a_one"], fam) == []


def test_force_in_wave_by_wave_uses_the_flag_for_its_single_asset(env, tmp_path, monkeypatch):
    repo, git = env
    _, dry = run(args_for(repo, "a_one", "--force-execute", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    sent = []
    monkeypatch.setattr(slw, "dispatch_run_with_timeout", lambda **kw: sent.append(kw) or "executions/x")
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one", "--force-execute", "--commit", "--confirm", dry["confirm_token_single_run"],
                             "--pause-dir", str(tmp_path / "p"), mode="wave-by-wave"), db, git,
                    hook=lambda *a: True, sleep=lambda s: None)
    assert code == 0 and sent[0]["force_execute"] is True and out["committed_runs"][0]["force_execute"] is True


def test_help_and_readme_document_force_and_the_delta_skip():
    flat_help = " ".join(slw.build_parser().format_help().split())
    assert "--force-execute" in flat_help and "OFF by default" in flat_help and "NIRMANA_FORCE_EXECUTE=1" in flat_help
    readme = " ".join((HERE.parent / "README_level_wave.md").read_text().split())
    readme = readme.replace("The delta-skip", "the delta-skip")
    assert ("the delta-skip: an unchanged writer re-dispatched without force no-op-completes and emits no new receipt "
            "(asset_runner.py ~1141-1160)") in readme
    assert "force bypasses it for every asset of that run" in readme.lower() and "--update-env-vars=NIRMANA_FORCE_EXECUTE=1" in readme
    assert "gcloud 576.0.0" in readme and "FORCE_MULTI_ASSET" in readme and "FORCE_FAMILY_ASSET" in readme


# ═════════════════════════ force: the image must honour it; what is verified afterwards ═════════════════════════

@pytest.mark.parametrize("kw,needle", [
    (dict(runner_text=RUNNER_WITHOUT_FORCE), "runner.py"),
    (dict(asset_runner_text=ASSET_RUNNER_WITHOUT_FORCE), "asset_runner.py"),
    (dict(runner_text="", asset_runner_text=""), "runner.py"),
    (dict(runner_show_fails=True), "unreadable"),
])
def test_force_is_refused_when_the_pinned_image_does_not_honour_it(tmp_path, kw, needle):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS, **kw)
    db = FakeDB([SMALL], READY)
    for extra in ([], ["--commit", "--confirm", "x", "--verify-forced"]):
        code, out = run(args_for(repo, "a_one", "--force-execute", *extra, mode="single-run" if extra else None), db, git,
                        dispatch=lambda r: pytest.fail("dispatched"))
        assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "FORCE_NOT_SUPPORTED_BY_IMAGE"
        assert needle in " ".join(out["refusals"][0]["problems"]) and out["refusals"][0]["job_sha"] == sha_of("deadbeef")
    assert db.log == [] and "commit" not in db.kinds()


def test_the_image_check_reads_the_runner_sources_at_the_pinned_job_sha(env):
    repo, git = env
    run(args_for(repo, "a_one", "--force-execute"), FakeDB([SMALL], READY), git)
    shows = [c[1] for c in git.calls if c[0] == "show" and "orchestrator" in c[1]]
    assert f"{sha_of('deadbeef')}:{slw.RUNNER_REL}" in shows and f"{sha_of('deadbeef')}:{slw.ASSET_RUNNER_REL}" in shows


def test_the_image_check_is_not_run_without_force(env):
    repo, git = env
    run(args_for(repo, "a_one"), FakeDB([SMALL], READY), git)
    assert not [c for c in git.calls if c[0] == "show" and "orchestrator" in c[1]]
    git2 = FakeGit(family_text=family_doc(), deployed=SMALL_DIGESTS, runner_text=RUNNER_WITHOUT_FORCE)
    code, _ = run(args_for(repo, "a_one"), FakeDB([SMALL], READY), git2)
    assert code == 0                                       # an old image is fine for a normal rebuild


def test_the_real_repo_runner_sources_satisfy_the_markers():
    for rel in (slw.RUNNER_REL, slw.ASSET_RUNNER_REL):
        text = (REPO / rel).read_text()
        pat = next(p for r, p, _ in slw._FORCE_MARKERS if r == rel)
        assert pat.search(text), rel                        # drift guard: the markers still exist in the runner today


def test_single_run_force_says_the_effect_is_not_verified_by_default(env, monkeypatch):
    repo, git = env
    _, dry = run(args_for(repo, "a_one", "--force-execute"), FakeDB([SMALL], READY), git)
    monkeypatch.setattr(slw, "dispatch_run_with_timeout", lambda **kw: "executions/x")
    code, out = run(args_for(repo, "a_one", "--force-execute", "--commit", "--confirm", dry["confirm_token_single_run"], mode="single-run"),
                    FakeDB([SMALL], READY), git)
    assert code == 0 and out["forced_effective"] == "not_verified" and "NOT verified" in out["forced_note"]


def _forced_db(dispositions, run_state="completed"):
    db = FakeDB([SMALL], READY, run_states={})
    real = db.respond

    def respond(sql, params):
        if "FROM build_run_assets bra" in sql:
            return [{"asset_id": a, "position": i, "state": "complete", "disposition": d, "error": None, "throughput_state": "lit",
                     "started_at": T0, "ended_at": T0 + timedelta(seconds=5)} for i, (a, d) in enumerate(dispositions.items())]
        if "SELECT state, last_error FROM build_runs WHERE id" in sql:
            return [{"state": run_state, "last_error": None}]
        return real(sql, params)
    db.respond = respond
    return db


@pytest.mark.parametrize("disp,run_state,expect", [
    ({"a_one": "build"}, "completed", True), ({"a_one": "skip_no_delta"}, "completed", False),
    ({"a_one": "build"}, "running", None), ({"a_one": "withheld_protected"}, "completed", None), ({}, "completed", None),
])
def test_forced_effect_reads_build_versus_skip_no_delta_from_the_run(disp, run_state, expect):
    eff = slw.forced_effect(_forced_db(disp, run_state).connect, "r1")
    assert eff["forced_effective"] is expect
    assert bool(eff["warning"]) is (expect is False) and ("FORCE DID NOT TAKE EFFECT" in (eff["warning"] or "")) is (expect is False)
    if expect is None:
        assert eff["note"]


def test_forced_effect_only_runs_selects():
    db = _forced_db({"a_one": "build"})
    slw.forced_effect(db.connect, "r1")
    assert all(e[1].lstrip().startswith("SELECT") for e in db.statements()) and "commit" not in db.kinds()


@pytest.mark.parametrize("disp,eff,warns", [("build", True, False), ("skip_no_delta", False, True)])
def test_verify_forced_reports_the_effect_and_warns_when_a_forced_run_skipped(env, monkeypatch, disp, eff, warns):
    repo, git = env
    _, dry = run(args_for(repo, "a_one", "--force-execute"), FakeDB([SMALL], READY), git)
    monkeypatch.setattr(slw, "dispatch_run_with_timeout", lambda **kw: "executions/x")
    db = _forced_db({"a_one": disp})
    code, lines_, _ = run_all(args_for(repo, "a_one", "--force-execute", "--verify-forced", "--commit", "--confirm",
                                       dry["confirm_token_single_run"], mode="single-run"), db, git, sleep=lambda s: None)
    last = lines_[-1]
    assert code == 0 and last["forced_effective"] is eff and bool(last.get("warning")) is warns
    assert any(l["event"] == "forced_effect" and l["forced_effective"] is eff for l in lines_)
    if warns:
        assert "FORCE DID NOT TAKE EFFECT" in last["warning"]


def test_force_with_declared_skips_for_the_same_asset_is_refused(env):
    repo, git = env
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one", "--force-execute", "--declared-skips", "a_one"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and out["refusals"][0]["code"] == "FORCE_WITH_DECLARED_SKIP" and db.log == []
    code, out = run(args_for(repo, "a_one", "--force-execute", "--declared-skips", "other_asset"), FakeDB([SMALL], READY), git)
    assert code == 0                                                       # naming some other asset is harmless


def test_wave_by_wave_force_that_skipped_stops_the_campaign_and_reports_not_verified(env, tmp_path, monkeypatch):
    repo, git = env
    _, dry = run(args_for(repo, "a_one", "--force-execute", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    monkeypatch.setattr(slw, "dispatch_run_with_timeout", lambda **kw: "executions/x")
    db = _forced_db({"a_one": "skip_no_delta"})
    code, out = run(args_for(repo, "a_one", "--force-execute", "--commit", "--confirm", dry["confirm_token_single_run"],
                             "--pause-dir", str(tmp_path / "p"), mode="wave-by-wave"), db, git,
                    hook=lambda *a: True, sleep=lambda s: None)
    assert code == slw.EXIT_CAMPAIGN_STOPPED and out["wave_by_wave"]["status"] == "STOPPED_ASSETS_NOT_COMPLETE"
    assert out["forced_effective"] == "not_verified"


def test_wave_by_wave_force_that_built_reports_effective(env, tmp_path, monkeypatch):
    repo, git = env
    _, dry = run(args_for(repo, "a_one", "--force-execute", mode="wave-by-wave"), FakeDB([SMALL], READY), git)
    monkeypatch.setattr(slw, "dispatch_run_with_timeout", lambda **kw: "executions/x")
    code, out = run(args_for(repo, "a_one", "--force-execute", "--commit", "--confirm", dry["confirm_token_single_run"],
                             "--pause-dir", str(tmp_path / "p"), mode="wave-by-wave"),
                    FakeDB([SMALL], READY), git, hook=lambda *a: True, sleep=lambda s: None)
    assert code == 0 and out["forced_effective"] is True


def test_force_dry_run_with_the_family_file_absent_works_on_name_patterns_and_a_commit_is_refused(tmp_path):
    repo = make_repo(tmp_path, SMALL_DIGESTS)
    git = FakeGit(family_listed=False, deployed=SMALL_DIGESTS)
    code, out = run(args_for(repo, "a_one", "--force-execute"), FakeDB([SMALL], READY), git)
    assert code == 0 and out["family_enforcement"] == "name_patterns_only" and out["force_execute"] is True
    code, out = run(args_for(make_repo(tmp_path / "g", {"ka_gochara": _hexdigest("ka_gochara")}), "ka_gochara", "--force-execute"),
                    FakeDB([[row("ka_gochara")]], READY), FakeGit(family_listed=False, deployed={"ka_gochara": _hexdigest("ka_gochara")}))
    assert code == slw.REFUSAL_EXIT_CODE and "FORCE_FAMILY_ASSET" in [r["code"] for r in out["refusals"]]
    db = FakeDB([SMALL], READY)
    code, out = run(args_for(repo, "a_one", "--force-execute", "--commit", "--confirm", "x", mode="single-run"), db, git)
    assert code == slw.REFUSAL_EXIT_CODE and "FAMILY_FILE_MISSING" in [r["code"] for r in out["refusals"]] and db.log == []


def test_readme_documents_the_image_check_the_unverified_single_run_and_the_job_level_env():
    flat = " ".join((HERE.parent / "README_level_wave.md").read_text().split())
    for needle in ("FORCE_NOT_SUPPORTED_BY_IMAGE", "ef9ee729e", "records the operator's INTENT", "is NOT verified afterwards",
                   "--verify-forced", "forced_effective", "gcloud run jobs describe", "would force EVERY run of that job",
                   "FORCE_WITH_DECLARED_SKIP"):
        assert needle in flat, needle
