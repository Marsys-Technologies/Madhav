"""test_suvarna_global_asset_dispatch.py -- the forced single GLOBAL-asset dispatcher (suvarna_global_asset_dispatch.py).

Offline. No database, no gcloud, no network: every outside contact (database connection, git, the Cloud Run dispatch, the
fingerprint reader, the clock) is an injected fake that records what it was asked to do. Nothing here is run against production.

Proof map
  plan                 exactly one asset, a deterministic token, INSERT then ROLLBACK, the receipt, no commit / no dispatch
  refusals             0 or 2 assets; a per_chart asset; an unknown / phantom / non-uuid anchor; a busy anchor chart; a conflicting
                       run elsewhere; a lit dependent (overridable ONLY with the exact flag); an undeclared / empty / partial /
                       non-deterministic fingerprint; image without force support; registry or impact changed; token mismatch
  one dispatch         skip_no_delta stops (exit 8), a second dispatch is refused, --allow-redispatch names the prior run
  verification         run complete, force effective, duration-bearing build record, post fingerprint == pre fingerprint
  manifest             byte-identical to dispatch_frozen_rebuild.build_manifest and to build_level_manifest; accepted by the REAL runner
  recording            triggered_by prefix / length / no collision; the INSERT text equals the wave's; the closed receipt schema
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import itertools
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import fingerprint_declarations as fd  # noqa: E402
import suvarna_global_asset_dispatch as gad  # noqa: E402
import suvarna_level_wave as slw  # noqa: E402

REPO = HERE.parents[3]
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER_CHART = "1c826d5a-0000-4000-8000-000000000001"
ASSET = "bg_phaladeepika_latta"
DEPENDENT = "ka_vedha_gochara"
T0 = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
DECLS = fd.load_declarations()
UNIT = ASSET
# import-time local reads (E5.5 pulls asset_census, which runs `git rev-parse --show-toplevel` once at import) happen here, before the
# autouse fixture below makes any real subprocess an error:
EMPTY_SHA = fd.empty_table_fingerprint(DECLS, UNIT, ASSET)
SELECT_SQL = fd.reader_selects(DECLS, [UNIT])[0]["sql"]


def _hex(name: str, salt: str = "") -> str:
    return hashlib.sha256((name + salt).encode()).hexdigest()


def sha_of(ref: str) -> str:
    return hashlib.sha1(ref.encode()).hexdigest()


def row(asset, deps=(), *, scope="per_chart", cow=False, part=None, active=True, writer=True, kind="data", layer="bodha",
        target=None, timeout=600, est=None):
    return {"asset_id": asset, "layer": layer, "scope": scope, "asset_kind": kind, "is_active": active, "has_writer": writer,
            "target_table": target, "writer_timeout_seconds": timeout, "estimated_seconds": est, "depends_on": list(deps),
            "natural_key_partition": part, "has_cowriters": cow}


LATTA = row(ASSET, scope="global", layer="brahmagyan", target=ASSET, part="table_version, graha")
KA_VEDHA = row(DEPENDENT, [ASSET], scope="per_chart", layer="kala", target="kala_vedha_gochara")
PRE_SHA = _hex("latta rows before")
POST_SHA = _hex("latta rows after")


# ───────────────────────── fakes ─────────────────────────

class FakeCursor:
    def __init__(self, db):
        self.db, self._rows = db, []

    def execute(self, sql, params=None):
        sql = " ".join(sql.split())
        self.db.log.append(("execute", sql, params))
        self._rows = self.db.respond(sql, params)

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def close(self):
        pass


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
    def __init__(self, *, candidates=None, charts=(CHART,), downstream=(DEPENDENT,), peers=(), registry=None, throughput=(),
                 anchor_active=(), conflicts=(), prior=(), deps=None, run_states=None, dispositions=None, run_asset="auto",
                 global_record="auto", chart_bound=(), fail_commit=False, run_row=None, impact_after_first=None):
        self.log, self.cand, self.charts = [], list(candidates or [[LATTA]]), set(charts)
        self.downstream, self.peers = list(downstream), list(peers)
        self.registry = [KA_VEDHA] if registry is None else list(registry)
        self.throughput, self.anchor_active, self.conflicts, self.prior = list(throughput), list(anchor_active), list(conflicts), list(prior)
        self.deps = deps or {}
        self.run_states, self.dispositions = run_states or {}, dispositions
        self.run_asset, self.global_record, self.chart_bound = run_asset, global_record, list(chart_bound)
        self.fail_commit, self.commit_calls, self.cand_calls = fail_commit, 0, 0
        self.run_row = run_row
        self.impact_after_first, self.impact_calls = impact_after_first, 0
        self.inserted_run = None
        self.ended = T0 + timedelta(seconds=40)

    def connect(self):
        self.log.append(("connect",))
        return FakeConn(self)

    def respond(self, sql, params):
        if "pg_advisory_xact_lock" in sql:
            return []
        if "FROM charts WHERE id" in sql:
            return [{"id": params[0]}] if params[0] in self.charts else []
        if "writer_timeout_seconds" in sql and "FROM asset_registry ar WHERE ar.asset_id = ANY" in sql:
            i = min(self.cand_calls, len(self.cand) - 1)
            self.cand_calls += 1
            return [r for r in self.cand[i] if r["asset_id"] in set(params[0])]
        if "unnest(%s::text[]) AS dep" in sql:
            return [{"asset_id": d, "asset_kind": (self.deps.get(d) or (None, None, "data"))[2], "state": (self.deps.get(d) or (None,))[0],
                     "freshness_state": (self.deps.get(d) or (None, None))[1]} for d in params[0]]
        if sql.startswith("WITH RECURSIVE downstream"):
            self.impact_calls += 1
            names = self.downstream
            if self.impact_after_first is not None and self.impact_calls > 1:
                names = self.impact_after_first
            return [{"asset_id": a} for a in names]
        if "JOIN asset_registry peer" in sql:
            return [{"asset_id": a} for a in self.peers]
        if sql.startswith("SELECT ar.asset_id, ar.layer, ar.scope, ar.asset_kind, ar.is_active, ar.has_writer, ar.target_table FROM"):
            return [r for r in self.registry if r["asset_id"] in set(params[0])]
        if "FROM asset_throughput at LEFT JOIN LATERAL" in sql:
            return [t for t in self.throughput if t["asset_id"] in set(params[0])]
        if "FROM build_runs WHERE chart_id" in sql:
            return list(self.anchor_active)
        if "left(br.triggered_by" in sql:
            return list(self.prior)
        if "FROM build_runs br JOIN build_run_assets bra" in sql:
            return list(self.conflicts)
        if sql.startswith("INSERT INTO build_runs"):
            self.inserted_run = params
        if "SELECT state, last_error FROM build_runs WHERE id" in sql:
            seq = self.run_states.get(params[0], "completed")
            state = (seq.pop(0) if len(seq) > 1 else seq[0]) if isinstance(seq, list) else seq
            return [{"state": state, "last_error": None}]
        if "FROM build_run_assets bra JOIN build_runs br" in sql:
            d = self.dispositions if self.dispositions is not None else {ASSET: "build"}
            return [{"asset_id": a, "position": 0, "state": "complete", "disposition": disp, "error": None, "throughput_state": "lit",
                     "started_at": T0, "ended_at": self.ended} for a, disp in d.items()]
        if "FROM build_run_assets WHERE run_id = %s AND asset_id" in sql:
            if self.run_asset == "auto":
                return [{"state": "complete", "disposition": "build", "started_at": T0, "ended_at": self.ended, "error": None}]
            return [self.run_asset] if self.run_asset else []
        if "FROM asset_throughput WHERE asset_id = %s AND chart_id IS NULL" in sql:
            if self.global_record == "auto":
                return [{"state": "lit", "last_built_at": self.ended, "duration_seconds": 38.5}]
            return list(self.global_record)
        if "FROM asset_throughput WHERE asset_id = %s AND chart_id IS NOT NULL" in sql:
            return list(self.chart_bound)
        if "plan_manifest_digest FROM build_runs WHERE id" in sql:
            return [self.run_row] if self.run_row else []
        return []

    def statements(self):
        return [e for e in self.log if e[0] == "execute"]

    def inserts(self, table):
        return [e for e in self.statements() if e[1].startswith(f"INSERT INTO {table}")]

    def kinds(self):
        return [e[0] for e in self.log]


class FakeFp:
    """A fingerprint reader: the n-th call answers shas[n] (the last repeats); rows per table."""

    def __init__(self, shas=(PRE_SHA, PRE_SHA), rows=8, fail=False):
        self.shas, self.rows, self.fail, self.calls, self.opened = list(shas), rows, fail, 0, 0

    def connect(self):
        self.opened += 1
        return type("C", (), {"rollback": lambda s: None, "close": lambda s: None})()

    def reader(self, conn, decls, units):
        if self.fail:
            raise RuntimeError("fake unreadable table")
        sha = self.shas[min(self.calls, len(self.shas) - 1)]
        self.calls += 1
        (unit,) = units
        tables = {t: {"sha256": sha, "rows": self.rows} for t in decls.tables(unit)}
        return {"definition": fd.FINGERPRINT_DEFINITION, "declarations_sha256": decls.sha256, "fingerprints": {unit: sha},
                "tables": {unit: tables}, "projections": {}, "horizons": {}}


RUNNER_WITH_FORCE = 'force = os.environ.get("NIRMANA_FORCE_EXECUTE", "").strip().lower() in ("1", "true", "yes")\n'
ASSET_RUNNER_WITH_FORCE = "    if declared_deps is not None and has_cowriters is not None and not force:\n        return _skip()\n"
RUNNER_WITHOUT_FORCE = "def execute_run(run_id):\n    pass\n"


class FakeGit:
    def __init__(self, *, runner_text=RUNNER_WITH_FORCE, asset_runner_text=ASSET_RUNNER_WITH_FORCE, deployed=None, family_set=()):
        self.runner_text, self.asset_runner_text = runner_text, asset_runner_text
        self.deployed = deployed
        self.family = {k: [] for k in slw.FAMILY_LIST_KEYS}
        self.family["family_sangam"] = list(family_set)
        self.family["family_set"] = sorted(family_set)
        self.calls = []

    def __call__(self, repo, args):
        self.calls.append(list(args))
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
                return cp(0, self.asset_runner_text)
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
        return f"brahma-build-pipeline-job-exec-{len(self.calls)}"


class Stream(io.StringIO):
    def flush(self):
        super().flush()


@pytest.fixture(autouse=True)
def no_real_subprocess(monkeypatch):
    """No test may start a real process: not gcloud, not git. A test that wants to observe a command patches subprocess.run itself
    (a later patch wins over this one)."""
    def blocked(*a, **k):
        raise AssertionError(f"a real subprocess was requested in a test: {a[:1]}")
    for name in ("run", "Popen", "check_output", "check_call", "call"):
        monkeypatch.setattr(subprocess, name, blocked)


@pytest.fixture
def env(tmp_path):
    repo = tmp_path / "repo"
    gen = repo / "platform" / "src" / "generated"
    gen.mkdir(parents=True)
    digests = {ASSET: _hex(ASSET)}
    (gen / "nirmana-writer-digests.json").write_text(json.dumps({"version": 1, "writers": digests}))
    outdir = tmp_path / "out"
    outdir.mkdir()
    jobfile = tmp_path / "job-sha"
    jobfile.write_text(sha_of("deadbeef") + "\n")
    return {"repo": str(repo), "receipt": str(outdir / "receipt.json"), "jobfile": str(jobfile), "digests": digests, "tmp": tmp_path}


def argv_for(env, *extra, asset=ASSET, anchor=CHART, commit=False, confirm=None, jobfile=True):
    argv = ["--assets", asset, "--anchor-chart", anchor, "--receipt", env["receipt"], "--repo", env["repo"],
            "--deployed-sha", "deadbeef", "--deployed-job-sha", "deadbeef"]
    if jobfile:
        argv += ["--job-sha-file", env["jobfile"]]
    if commit:
        argv += ["--commit", "--confirm", confirm or "x"]
    return gad.build_parser().parse_args(argv + list(extra))


def run(env, args, db=None, fp=None, git=None, dispatch=None, decls=DECLS, monotonic=None):
    db = db or FakeDB()
    fp = fp or FakeFp()
    git = git or FakeGit(deployed=env["digests"])
    out = Stream()
    mono = monotonic or (lambda: 0.0)
    code = gad.run_cli(args, connect=db.connect, fp_connect=fp.connect, git=git, out=out, sleep=lambda s: None, monotonic=mono,
                       dispatch=dispatch, now=lambda: T0, decls=decls, fp_reader=fp.reader)
    return code, [json.loads(l) for l in out.getvalue().splitlines() if l.strip()]


def last(events):
    return events[-1]


def codes_of(events):
    return [r["code"] for r in last(events).get("refusals", [])]


def plan_token(env, **kw):
    code, ev = run(env, argv_for(env), **kw)
    assert code == 0, ev
    return last(ev)["confirm_token"]


def commit_run(env, db=None, fp=None, dispatch=None, extra=(), **kw):
    db = db or FakeDB()
    fp = fp or FakeFp((PRE_SHA, PRE_SHA, PRE_SHA))
    token = plan_token(env, db=FakeDB(candidates=[[LATTA]]) if db is None else db, fp=FakeFp((PRE_SHA,)))
    db.log.clear()
    db.cand_calls = 0
    db.impact_calls = 0
    fp.calls = 0
    args = argv_for(env, *extra, commit=True, confirm=token)
    disp = dispatch if dispatch is not None else Dispatch()
    code, ev = run(env, args, db=db, fp=fp, dispatch=disp, **kw)
    return code, ev, db, disp, token


# ───────────────────────── plan ─────────────────────────

def test_plan_shows_exactly_one_asset_and_prints_a_deterministic_token(env):
    db1, db2 = FakeDB(), FakeDB()
    code1, ev1 = run(env, argv_for(env), db=db1)
    pathlib.Path(env["receipt"]).unlink()
    code2, ev2 = run(env, argv_for(env), db=db2)
    s1, s2 = last(ev1), last(ev2)
    assert code1 == code2 == 0 and s1["event"] == "summary"
    assert s1["plan"] == [ASSET] and s1["scope"] == "global" and s1["force_execute"] is True and s1["committed"] is False
    assert re.fullmatch(r"GLOBAL1ASSET_[0-9A-F]{12}_FORCE_GLOBAL_REBUILD", s1["confirm_token"])
    assert s1["confirm_token"] == s2["confirm_token"] and s1["manifest_digest"] == s2["manifest_digest"]
    assert s1["force_support_check"]["result"] == "supported" and s1["pre_fingerprint"]["composite"] == PRE_SHA
    # the impact: ka_vedha_gochara only, no lit row
    assert [d["asset_id"] for d in (json.loads(pathlib.Path(env["receipt"]).read_text())["impact"]["dependents"])] == [DEPENDENT]
    assert s1["impact_summary"] == {"dependents": 1, "dependents_with_lit_rows": 0, "lit_rows": 0}
    assert any(DEPENDENT in line for line in s1["impact_lines"])
    # the cost of the anchor chart is printed
    assert s1["anchor_chart_cost"]["blocks_anchor_chart"] is True
    assert "blocks other builds of the anchor chart" in s1["anchor_chart_cost"]["message"]
    assert "ACTIVE_RUN" in s1["anchor_chart_cost"]["message"] and "expected duration" in s1["anchor_chart_cost"]["message"]


def test_plan_runs_the_inserts_and_rolls_back_and_never_commits_or_dispatches(env):
    db, disp = FakeDB(), Dispatch()
    code, ev = run(env, argv_for(env), db=db, dispatch=disp)
    assert code == 0
    assert len(db.inserts("build_runs")) == 1 and len(db.inserts("build_run_assets")) == 1
    assert "commit" not in db.kinds() and db.kinds().count("rollback") >= 1
    assert disp.calls == [] and last(ev)["committed"] is False
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    gad.validate_receipt(rec)
    assert rec["committed"] is False and rec["run_id"] is None and rec["committed_at"] is None
    assert rec["asset"] == ASSET and rec["anchor_chart"] == CHART and rec["anchor_is_canonical"] is True
    assert rec["image_sha"] == sha_of("deadbeef") and rec["impact_sha256"] == gad.sha256_json(rec["impact"])
    assert rec["confirm_token"] == last(ev)["confirm_token"] and rec["pre_fingerprint"]["composite"] == PRE_SHA
    assert (pathlib.Path(env["receipt"]).stat().st_mode & 0o777) == 0o600


def test_the_token_binds_every_input(env):
    base = dict(manifest_digest=_hex("m"), asset=ASSET, anchor_chart=CHART, image_sha=sha_of("x"), impact_sha256=_hex("i"),
                pre_fingerprint=_hex("p"), accepted_lit=[], allow_redispatch=[])
    t0 = gad.build_confirm_token(**base)
    for k, v in (("manifest_digest", _hex("m2")), ("asset", "bg_other"), ("anchor_chart", OTHER_CHART), ("image_sha", sha_of("y")),
                 ("impact_sha256", _hex("i2")), ("pre_fingerprint", _hex("p2")), ("accepted_lit", [f"{DEPENDENT}@{CHART}"]),
                 ("allow_redispatch", [CHART])):
        assert gad.build_confirm_token(**{**base, k: v}) != t0, k
    assert t0.endswith("_FORCE_GLOBAL_REBUILD") and not t0.endswith("_FROZEN_REBUILD")
    assert t0 != slw.expected_confirmation(base["manifest_digest"], 1, True)


# ───────────────────────── one asset, a global asset ─────────────────────────

@pytest.mark.parametrize("values", [[""], ["a_one,a_two"], ["a_one", "a_two"], ["a_one,a_one"], ["a_one,"], []])
def test_zero_or_several_assets_are_refused(env, values):
    argv = ["--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"], "--deployed-sha", "deadbeef",
            "--deployed-job-sha", "deadbeef"]
    for v in values:
        argv += ["--assets", v]
    if not values:
        with pytest.raises(SystemExit):                       # argparse: --assets is required
            gad.build_parser().parse_args(argv)
        with pytest.raises(slw.LevelWaveRefusal) as exc:
            gad.parse_single_asset([])
        assert exc.value.refusals[0]["code"] == "NOT_EXACTLY_ONE_ASSET"
        return
    db = FakeDB()
    code, ev = run(env, gad.build_parser().parse_args(argv), db=db)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["NOT_EXACTLY_ONE_ASSET"] and db.inserts("build_runs") == []


def test_a_malformed_asset_id_and_an_at_file_are_bad_input(env):
    for bad in ("Bg_Upper", "has space", "@/tmp/list"):
        code, ev = run(env, argv_for(env, asset=bad))
        assert code == slw.EXIT_BAD_INPUT and last(ev)["event"] == "error", bad


@pytest.mark.parametrize("scope", ["per_chart", "chart", None, "weird"])
def test_a_non_global_asset_is_refused_and_points_at_the_level_wave(env, scope):
    db = FakeDB(candidates=[[dict(LATTA, scope=scope)]])
    code, ev = run(env, argv_for(env), db=db)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["NOT_GLOBAL_SCOPE"]
    assert "suvarna_level_wave.py" in last(ev)["refusals"][0]["detail"] and db.inserts("build_runs") == []


@pytest.mark.parametrize("change", [{"is_active": False}, {"has_writer": False}, {"asset_kind": "service"}])
def test_an_inactive_writerless_or_service_asset_is_refused_by_the_waves_own_gate(env, change):
    code, ev = run(env, argv_for(env), db=FakeDB(candidates=[[dict(LATTA, **change)]]))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["REGISTRY_ROW_INVALID"]


def test_a_missing_registry_row_is_refused(env):
    code, ev = run(env, argv_for(env), db=FakeDB(candidates=[[]]))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["REGISTRY_ROW_INVALID"]


def test_a_family_asset_is_refused_for_force(env):
    fam = row("ka_gochara_v5", scope="global")
    code, ev = run(env, argv_for(env, asset="ka_gochara_v5"), db=FakeDB(candidates=[[fam]]))
    assert code == slw.REFUSAL_EXIT_CODE and "FORCE_FAMILY_ASSET" in codes_of(ev)


# ───────────────────────── the anchor chart ─────────────────────────

@pytest.mark.parametrize("anchor", ["not-a-uuid", "", "362f9f17-95a5-490b-a5a7-027d3e0efda0", CHART.upper(),
                                    "482012f1710e4a2599793821f5871aa"])
def test_a_non_uuid_phantom_or_non_canonical_anchor_is_refused_before_any_database_contact(env, anchor):
    db = FakeDB()
    code, ev = run(env, argv_for(env, anchor=anchor), db=db)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["ANCHOR_CHART_INVALID"] and db.log == []


def test_an_anchor_that_is_not_a_chart_is_refused(env):
    code, ev = run(env, argv_for(env, anchor=OTHER_CHART), db=FakeDB(charts=(CHART,)))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["ANCHOR_CHART_INVALID"]
    assert "charts table" in last(ev)["refusals"][0]["detail"]


@pytest.mark.parametrize("state", ["planned", "running", "paused"])
def test_a_busy_anchor_chart_is_refused_in_plan_and_commit_mode(env, state):
    active = [{"id": "r1", "chart_id": CHART, "state": state}]
    db = FakeDB(anchor_active=active)
    code, ev = run(env, argv_for(env), db=db)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["ANCHOR_CHART_BUSY"] and db.inserts("build_runs") == []
    assert "commit" not in db.kinds()


def test_a_conflicting_run_on_another_chart_that_touches_a_dependent_is_refused(env):
    db = FakeDB(conflicts=[{"id": "r9", "chart_id": OTHER_CHART, "state": "running", "asset_id": DEPENDENT}])
    code, ev = run(env, argv_for(env), db=db)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["CONFLICTING_ACTIVE_RUN"] and db.inserts("build_runs") == []


def test_the_dependency_gate_of_the_wave_is_applied_to_the_assets_upstream(env):
    latta = dict(LATTA, depends_on=["bg_ontology"])
    db = FakeDB(candidates=[[latta]], deps={"bg_ontology": ("stale", "fresh", "data")})
    code, ev = run(env, argv_for(env), db=db)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["DEPENDENCY_NOT_READY"] and db.inserts("build_runs") == []


# ───────────────────────── lit dependents ─────────────────────────

def lit(chart, state="lit", asset=DEPENDENT):
    return {"asset_id": asset, "chart_id": chart, "state": state, "last_built_at": T0, "freshness_state": "fresh"}


def test_a_lit_dependent_is_refused_and_listed(env):
    db = FakeDB(throughput=[lit(CHART), lit(OTHER_CHART, "stale"), lit(None, "service_ok")])
    code, ev = run(env, argv_for(env), db=db)
    r = last(ev)["refusals"][0]
    assert code == slw.REFUSAL_EXIT_CODE and r["code"] == "LIT_DEPENDENT"
    assert r["rows"] == sorted([f"{DEPENDENT}@global", f"{DEPENDENT}@{CHART}"]) and db.inserts("build_runs") == []


def test_a_lit_dependent_is_overridable_only_with_the_exact_flag_for_each_row(env):
    rows = [lit(CHART), lit(OTHER_CHART)]
    only_one = argv_for(env, "--accept-lit-dependent", f"{DEPENDENT}@{CHART}")
    code, ev = run(env, only_one, db=FakeDB(throughput=rows))
    assert code == slw.REFUSAL_EXIT_CODE and last(ev)["refusals"][0]["rows"] == [f"{DEPENDENT}@{OTHER_CHART}"]
    both = argv_for(env, "--accept-lit-dependent", f"{DEPENDENT}@{CHART}", "--accept-lit-dependent", f"{DEPENDENT}@{OTHER_CHART}")
    code, ev = run(env, both, db=FakeDB(throughput=rows))
    assert code == 0 and last(ev)["impact_summary"]["lit_rows"] == 2
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert rec["accepted_lit_dependents"] == sorted([f"{DEPENDENT}@{CHART}", f"{DEPENDENT}@{OTHER_CHART}"])
    plain = plan_token(env, db=FakeDB())
    assert last(ev)["confirm_token"] != plain                    # the override is part of what the token authorises


@pytest.mark.parametrize("flag", [f"{DEPENDENT}@global", f"other_asset@{CHART}", f"{DEPENDENT}@{OTHER_CHART}"])
def test_an_accept_flag_that_names_no_lit_row_is_refused(env, flag):
    code, ev = run(env, argv_for(env, "--accept-lit-dependent", flag), db=FakeDB(throughput=[lit(CHART)]))
    assert code == slw.REFUSAL_EXIT_CODE
    assert codes_of(ev) == ["LIT_DEPENDENT", "ACCEPT_LIT_DEPENDENT_UNMATCHED"]


@pytest.mark.parametrize("bad", ["x", "x@", "@y", f"{DEPENDENT}@a@b", "Bad@global"])
def test_a_malformed_accept_flag_is_bad_input(env, bad):
    code, ev = run(env, argv_for(env, "--accept-lit-dependent", bad))
    assert code == slw.EXIT_BAD_INPUT


def test_the_impact_statement_is_deterministic_and_reads_the_runners_stale_rule(env):
    db = FakeDB(downstream=["b_two", "a_one"], peers=["c_peer", "a_one"],
                registry=[row("a_one", [ASSET], layer="x"), row("b_two", ["a_one"]), row("c_peer", scope="global", target=ASSET)],
                throughput=[lit(CHART, asset="a_one"), lit(OTHER_CHART, asset="a_one"), lit(None, "dormant", "b_two")])
    impact = gad.read_impact_via(db.connect, asset=ASSET, anchor_chart=CHART, target_table=ASSET)
    assert [d["asset_id"] for d in impact["dependents"]] == ["a_one", "b_two", "c_peer"]
    a_one = impact["dependents"][0]
    assert a_one["relations"] == ["shares_target_table", "transitive_depends_on"]
    assert [(t["chart_id"], t["runner_stales_if_output_changes"]) for t in a_one["throughput"]] == [(OTHER_CHART, False), (CHART, True)]
    assert impact["dependents"][1]["lit_rows"] == 0 and impact["dependents"][2]["throughput"] == []
    assert impact["summary"] == {"dependents": 3, "dependents_with_lit_rows": 1, "lit_rows": 2}
    again = gad.read_impact_via(db.connect, asset=ASSET, anchor_chart=CHART, target_table=ASSET)
    assert gad.sha256_json(again) == gad.sha256_json(impact)
    assert all(e[1].split()[0] in ("SELECT", "WITH") for e in db.statements())        # read-only


def test_the_downstream_sql_is_the_runners_own_closure():
    runner = " ".join((REPO / "platform/python-sidecar/pipeline/orchestrator/asset_runner.py").read_text().split())
    assert " ".join(gad.DOWNSTREAM_SQL.split()) in runner


def test_the_impact_is_reread_in_the_transaction_and_a_change_refuses(env):
    # a dependent appears between the read that made the plan and the read inside the transaction
    db = FakeDB(impact_after_first=[DEPENDENT, "ka_new_dependent"], registry=[KA_VEDHA, row("ka_new_dependent", [ASSET])])
    code, ev = run(env, argv_for(env), db=db)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["IMPACT_CHANGED"] and db.inserts("build_runs") == []
    # a change before the commit-time plan is rebuilt moves the token, so the old token no longer confirms anything
    token = plan_token(env, db=FakeDB())
    pathlib.Path(env["receipt"]).unlink()
    db = FakeDB(downstream=[DEPENDENT, "ka_new_dependent"], registry=[KA_VEDHA, row("ka_new_dependent", [ASSET])])
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA,)), dispatch=Dispatch())
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["CONFIRM_TOKEN_MISMATCH"] and "commit" not in db.kinds()


# ───────────────────────── the committed fingerprint declarations ─────────────────────────

def test_the_real_declarations_declare_latta_as_a_full_deterministic_unit():
    assert gad.declared_unit_or_refuse(DECLS, ASSET) == ASSET


def test_an_undeclared_asset_is_refused(env):
    other = row("bg_not_declared", scope="global", target="bg_not_declared")
    digests = {**env["digests"], "bg_not_declared": _hex("bg_not_declared")}
    (pathlib.Path(env["repo"]) / "platform/src/generated/nirmana-writer-digests.json").write_text(json.dumps({"version": 1, "writers": digests}))
    db = FakeDB(candidates=[[other]])
    code, ev = run(env, argv_for(env, asset="bg_not_declared"), db=db, git=FakeGit(deployed=digests))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["ASSET_NOT_DECLARED"] and db.inserts("build_runs") == []
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.declared_unit_or_refuse(DECLS, "bg_not_declared")
    assert exc.value.refusals[0]["code"] == "ASSET_NOT_DECLARED"


class _Decl:
    """A stand-in declarations object for the partial / non-deterministic branches."""
    path = "FINGERPRINT_DECLARATIONS.json"

    def __init__(self, partial=False, repro=("deterministic",), kind="asset"):
        self._partial, self._repro, self._kind = partial, list(repro), kind

    def units(self):
        return {ASSET: {"kind": self._kind}}

    def undeclared_assets(self):
        return {}

    def partial_assets(self):
        return {ASSET: []} if self._partial else {}

    def reproducibility(self, unit):
        return self._repro


@pytest.mark.parametrize("decl,code", [(_Decl(partial=True), "FINGERPRINT_COVERAGE_PARTIAL"),
                                       (_Decl(repro=("rolling_horizon",)), "FINGERPRINT_NOT_DETERMINISTIC"),
                                       (_Decl(kind="group"), "ASSET_NOT_DECLARED")])
def test_a_partial_non_deterministic_or_group_declaration_is_refused(decl, code):
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.declared_unit_or_refuse(decl, ASSET)
    assert exc.value.refusals[0]["code"] == code


def test_an_empty_table_is_refused(env):
    code, ev = run(env, argv_for(env), fp=FakeFp((PRE_SHA,), rows=0), db=FakeDB())
    assert code == slw.REFUSAL_EXIT_CODE and "FINGERPRINT_TABLE_EMPTY" in codes_of(ev)


def test_a_fingerprint_equal_to_the_empty_table_fingerprint_is_refused(env):
    code, ev = run(env, argv_for(env), fp=FakeFp((EMPTY_SHA,), rows=3), db=FakeDB())
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["FINGERPRINT_EQUALS_EMPTY"]


def test_an_unreadable_table_is_a_refusal_never_an_empty_fingerprint(env):
    code, ev = run(env, argv_for(env), fp=FakeFp(fail=True), db=FakeDB())
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["FINGERPRINT_UNREADABLE"]


def test_the_real_reader_through_the_declarations_reads_with_selects_only_on_tuple_rows():
    cols = ["table_version", "graha", "count_from_graha", "direction", "effect_description", "affliction_condition",
            "source_citation", "verse_ref", "created_at"]
    rows = [("v1", f"g{i}", i, "fwd", "e", "a", "c", "v", T0 + timedelta(seconds=i)) for i in range(3)]
    log = []

    class Cur:
        description = [(c,) for c in cols]

        def __init__(self):
            self._left = list(rows)

        def execute(self, sql, params=None):
            log.append(sql)

        def fetchmany(self, n):
            out, self._left = self._left[:n], self._left[n:]
            return out

        def close(self):
            pass

    class Conn:
        def cursor(self, name=None):
            return Cur()

        def rollback(self):
            log.append("ROLLBACK")

        def close(self):
            pass

    fp = gad.read_fingerprint(lambda: Conn(), DECLS, UNIT)
    assert re.fullmatch(r"[0-9a-f]{64}", fp["composite"]) and fp["tables"][ASSET]["rows"] == 3
    assert [s for s in log if s != "ROLLBACK"] == [SELECT_SQL]
    assert all(s.lstrip().upper().startswith(("SELECT", "ROLLBACK")) for s in log)


# ───────────────────────── the image and the deployment ─────────────────────────

def test_an_image_without_force_support_is_refused_in_plan_mode_too(env):
    for git in (FakeGit(deployed=env["digests"], runner_text=RUNNER_WITHOUT_FORCE),
                FakeGit(deployed=env["digests"], asset_runner_text="    if declared_deps is not None:\n        return _skip()\n")):
        db = FakeDB()
        code, ev = run(env, argv_for(env), db=db, git=git)
        assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["FORCE_NOT_SUPPORTED_BY_IMAGE"] and db.log == []


def test_image_skew_is_refused(env):
    code, ev = run(env, argv_for(env), git=FakeGit(deployed={ASSET: _hex(ASSET, "another build")}))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["IMAGE_SKEW"]


def test_the_deployed_shas_are_required_and_must_bind(env):
    args = gad.build_parser().parse_args(["--assets", ASSET, "--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"]])
    code, ev = run(env, args)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["DEPLOYED_JOB_SHA_REQUIRED"]
    args = gad.build_parser().parse_args(["--assets", ASSET, "--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"],
                                          "--deployed-sha", "deadbeef", "--deployed-job-sha", "cafe"])
    code, ev = run(env, args)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["JOB_SHA_MISMATCH"]


def test_commit_needs_the_job_sha_file_and_refuses_a_redeploy(env):
    token = plan_token(env)
    code, ev = run(env, argv_for(env, commit=True, confirm=token, jobfile=False))
    assert code == slw.EXIT_BAD_INPUT
    pathlib.Path(env["jobfile"]).write_text(sha_of("a newer deploy") + "\n")
    db = FakeDB()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=Dispatch())
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["JOB_SHA_CHANGED"] and db.inserts("build_runs") == []


# ───────────────────────── token, registry, commit ─────────────────────────

def test_a_wrong_token_is_refused_and_nothing_is_inserted(env):
    for wrong in (None, "x", slw.expected_confirmation(_hex("m"), 1, True), "GLOBAL1ASSET_000000000000_FORCE_GLOBAL_REBUILD"):
        db, disp = FakeDB(), Dispatch()
        args = argv_for(env, commit=True, confirm=wrong or "")
        code, ev = run(env, args, db=db, dispatch=disp)
        assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["CONFIRM_TOKEN_MISMATCH"], wrong
        assert db.inserts("build_runs") == [] and "commit" not in db.kinds() and disp.calls == []


def test_a_registry_row_changed_between_plan_and_commit_is_refused(env):
    token = plan_token(env)
    changed = dict(LATTA, depends_on=["bg_new_dependency"])
    db = FakeDB(candidates=[[LATTA], [changed]])
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=Dispatch())
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["REGISTRY_ROW_CHANGED"]
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds()


def test_a_changed_pre_fingerprint_between_plan_and_commit_invalidates_the_token(env):
    token = plan_token(env)
    code, ev = run(env, argv_for(env, commit=True, confirm=token), fp=FakeFp((_hex("someone wrote the table"), PRE_SHA)),
                   dispatch=Dispatch())
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["CONFIRM_TOKEN_MISMATCH"]


def test_the_happy_path_dispatches_once_forced_and_verifies(env):
    code, ev, db, disp, token = commit_run(env)
    assert code == 0, ev
    kinds = [e["event"] for e in ev]
    assert kinds[:2] == ["run_committed", "run_dispatched"] and kinds[-1] == "summary"
    assert len(disp.calls) == 1 and db.kinds().count("commit") == 1
    s = last(ev)
    assert s["verification"]["verdict"] == "PASS" and s["verification"]["fingerprint_equal"] is True
    assert s["verification"]["duration_seconds"] == 38.5 and s["forced_effective"] is True
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    gad.validate_receipt(rec)
    assert rec["committed"] is True and rec["run_id"] == disp.calls[0] and rec["execution_name"].endswith("exec-1")
    assert rec["post_fingerprint"]["composite"] == PRE_SHA and rec["verified_at"] and rec["committed_at"]
    assert rec["verification"]["verdict"] == "PASS" and rec["confirm_token"] == token


def test_the_dispatch_mechanism_is_the_waves_force_override(env, monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, 0, "brahma-build-pipeline-job-exec-1\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)              # the ONLY way a command can run in these tests: recorded, not run
    token = plan_token(env)
    db = FakeDB()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA, PRE_SHA)), dispatch=None)
    gcloud = [c for c, _ in calls if c and c[0] == "gcloud"]
    assert code == 0 and len(gcloud) == 1 and len(calls) == 1
    assert "--update-env-vars=NIRMANA_FORCE_EXECUTE=1" in gcloud[0] and gcloud[0][:4] == ["gcloud", "run", "jobs", "execute"]
    assert gcloud[0] == slw.dispatch_command(run_id=db.inserted_run[0], project="madhav-astrology", region="asia-south1",
                                             job="brahma-build-pipeline-job", force_execute=True)


def test_without_a_fake_the_default_dispatch_cannot_reach_a_real_process(env):
    token = plan_token(env)
    db = FakeDB()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA,)), dispatch=None)
    assert code == slw.EXIT_DISPATCH_FAILED and "real subprocess" in last(ev)["dispatch_error"]       # blocked by the autouse fixture


def test_nothing_in_plan_mode_or_with_an_injected_dispatch_ever_calls_gcloud(env, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("subprocess.run must not be called (no gcloud, no git) in these tests")

    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(slw.subprocess, "run", boom)
    code, ev = run(env, argv_for(env))
    assert code == 0
    code, ev, db, disp, token = commit_run(env)
    assert code == 0 and len(disp.calls) == 1


def test_skip_no_delta_stops_with_a_non_zero_exit_and_forbids_a_second_dispatch(env):
    db = FakeDB(dispositions={ASSET: "skip_no_delta"})
    code, ev, db, disp, token = commit_run(env, db=db)
    s = last(ev)
    assert code == gad.EXIT_FORCE_NOT_EFFECTIVE and code != 0
    assert s["verification"]["codes"] == ["FORCE_DID_NOT_TAKE_EFFECT"] and s["second_dispatch"] == "FORBIDDEN"
    assert "SECOND DISPATCH IS FORBIDDEN" in s["warning"] and len(disp.calls) == 1
    # the tool never dispatches again by itself, and a new invocation refuses: a prior run of this tool exists
    run_id = disp.calls[0]
    db2 = FakeDB(prior=[{"id": run_id, "state": "completed", "plan_manifest_digest": _hex("m"), "triggered_by": s["triggered_by"]}])
    code2, ev2 = run(env, argv_for(env), db=db2, dispatch=disp)
    assert code2 == slw.REFUSAL_EXIT_CODE and codes_of(ev2) == ["ALREADY_DISPATCHED"] and len(disp.calls) == 1
    assert db2.inserts("build_runs") == []


def test_a_second_dispatch_needs_every_prior_run_named(env):
    p1, p2 = "11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"
    prior = [{"id": p1, "state": "completed", "plan_manifest_digest": "d", "triggered_by": "t"},
             {"id": p2, "state": "failed", "plan_manifest_digest": "d", "triggered_by": "t"}]
    code, ev = run(env, argv_for(env, "--allow-redispatch", p1), db=FakeDB(prior=prior))
    assert code == slw.REFUSAL_EXIT_CODE and last(ev)["refusals"][0]["runs"] == [p2]
    code, ev = run(env, argv_for(env, "--allow-redispatch", p1, "--allow-redispatch", p2), db=FakeDB(prior=prior))
    assert code == 0
    assert last(ev)["confirm_token"] != plan_token(env, db=FakeDB())     # the override is part of the token


def test_the_prior_run_query_matches_the_triggered_by_prefix_and_the_asset(env):
    db = FakeDB()
    run(env, argv_for(env), db=db)
    (q,) = [e for e in db.statements() if "left(br.triggered_by" in e[1]]
    assert q[2] == (len(gad.TRIGGERED_BY_PREFIX), gad.TRIGGERED_BY_PREFIX, ASSET)


@pytest.mark.parametrize("states", [["running", "running", "running"], ["failed"]])
def test_a_run_that_does_not_complete_is_not_verified(env, states):
    db = FakeDB()
    clock = itertools.count(0, 6000)
    token = plan_token(env)
    disp = Dispatch()
    db.run_states = {}
    orig = db.respond

    def respond(sql, params):
        if "SELECT state, last_error FROM build_runs WHERE id" in sql:
            return [{"state": states[min(db.run_poll, len(states) - 1)], "last_error": "boom"}]
        return orig(sql, params)

    db.run_poll = 0
    db.respond = respond
    args = argv_for(env, "--run-timeout-seconds", "100", commit=True, confirm=token)
    code, ev = run(env, args, db=db, fp=FakeFp((PRE_SHA, PRE_SHA)), dispatch=disp, monotonic=lambda: next(clock))
    assert code == gad.EXIT_VERIFY_FAILED and "RUN_NOT_COMPLETED" in last(ev)["verification"]["codes"]
    assert last(ev)["verification"]["fingerprint_equal"] is None and len(disp.calls) == 1


def test_a_completed_run_without_a_duration_bearing_build_record_fails_verification(env):
    for record in ([], [{"state": "lit", "last_built_at": T0 + timedelta(seconds=40), "duration_seconds": None}],
                   [{"state": "lit", "last_built_at": T0 + timedelta(seconds=99), "duration_seconds": 5.0}],
                   [{"state": "error", "last_built_at": T0 + timedelta(seconds=40), "duration_seconds": 5.0}]):
        pathlib.Path(env["receipt"]).unlink(missing_ok=True)
        code, ev, db, disp, token = commit_run(env, db=FakeDB(global_record=record))
        assert code == gad.EXIT_VERIFY_FAILED, record
        assert last(ev)["verification"]["codes"] == ["BUILD_RECORD_NOT_DURATION_BEARING"]


def test_a_chart_bound_throughput_row_for_the_global_asset_is_reported(env):
    code, ev, db, disp, token = commit_run(env, db=FakeDB(chart_bound=[{"chart_id": CHART, "state": "lit"}]))
    assert code == 0 and any("chart-bound asset_throughput row" in n for n in last(ev)["verification"]["notes"])


def test_a_changed_fingerprint_after_a_forced_rebuild_is_reported_and_exits_non_zero(env):
    code, ev, db, disp, token = commit_run(env, fp=FakeFp((PRE_SHA, POST_SHA)))
    s = last(ev)
    assert code == gad.EXIT_FINGERPRINT_CHANGED and code != 0
    assert s["verification"]["codes"] == ["FINGERPRINT_CHANGED_ON_FORCED_REBUILD"] and s["verification"]["fingerprint_equal"] is False
    assert PRE_SHA in s["warning"] and POST_SHA in s["warning"] and "cannot be undone" in s["warning"]
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert rec["pre_fingerprint"]["composite"] == PRE_SHA and rec["post_fingerprint"]["composite"] == POST_SHA


def test_an_unreadable_post_fingerprint_fails_verification(env):
    class Flaky(FakeFp):
        def reader(self, conn, decls, units):
            if self.calls >= 1:
                raise RuntimeError("gone")
            return super().reader(conn, decls, units)

    code, ev, db, disp, token = commit_run(env, fp=Flaky((PRE_SHA,)))
    assert code == gad.EXIT_VERIFY_FAILED and last(ev)["verification"]["codes"] == ["POST_FINGERPRINT_UNREADABLE"]


def test_a_dispatch_failure_terminalises_the_planned_run(env):
    token = plan_token(env)
    db, disp = FakeDB(), Dispatch(fail=True)
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=disp, fp=FakeFp((PRE_SHA,)))
    assert code == slw.EXIT_DISPATCH_FAILED
    assert any("UPDATE build_runs SET state='failed'" in e[1] for e in db.statements())
    assert [e["event"] for e in ev][:2] == ["run_committed", "dispatch_failed"]
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert rec["committed"] is True and rec["verification"]["codes"] == ["DISPATCH_FAILED"]


def test_a_commit_that_fails_is_reported_as_unknown_never_as_not_committed(env):
    token = plan_token(env)
    db = FakeDB(fail_commit=True)
    disp = Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=disp, fp=FakeFp((PRE_SHA,)))
    assert code == slw.EXIT_UNEXPECTED and last(ev)["commit_outcome_unknown"] is True and disp.calls == []


def test_an_interrupt_names_the_run_and_forbids_a_new_dispatch(env):
    token = plan_token(env)

    class Interrupted(Dispatch):
        def __call__(self, run_id):
            raise KeyboardInterrupt

    code, ev = run(env, argv_for(env, commit=True, confirm=token), dispatch=Interrupted(), fp=FakeFp((PRE_SHA,)))
    assert code == slw.EXIT_INTERRUPTED and "--verify-run" in last(ev)["warning"] and len(last(ev)["committed_runs"]) == 1


# ───────────────────────── --verify-run ─────────────────────────

def test_verify_run_checks_a_committed_run_without_inserting_or_dispatching(env):
    code, ev, db, disp, token = commit_run(env)
    assert code == 0
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "completed", "triggered_by": rec["triggered_by"],
               "plan_manifest_digest": rec["manifest_digest"]}
    db2, disp2 = FakeDB(run_row=run_row), Dispatch()
    args = gad.build_parser().parse_args(["--assets", ASSET, "--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"],
                                          "--verify-run", rec["run_id"]])
    code, ev = run(env, args, db=db2, fp=FakeFp((POST_SHA,)), dispatch=disp2)
    assert code == gad.EXIT_FINGERPRINT_CHANGED and db2.inserts("build_runs") == [] and disp2.calls == []
    assert json.loads(pathlib.Path(env["receipt"]).read_text())["post_fingerprint"]["composite"] == POST_SHA
    wrong = dict(run_row, triggered_by="something-else")
    code, ev = run(env, args, db=FakeDB(run_row=wrong), fp=FakeFp((PRE_SHA,)))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_RUN_MISMATCH"]
    code, ev = run(env, args, db=FakeDB(run_row=None), fp=FakeFp((PRE_SHA,)))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_RUN_MISMATCH"]


# ───────────────────────── the manifest and the recording ─────────────────────────

def _frozen_dispatcher():
    spec = importlib.util.spec_from_file_location("dispatch_frozen_rebuild_gad", REPO / "platform/scripts/dispatch_frozen_rebuild.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_stored_manifest_is_byte_identical_to_the_existing_dispatchers_for_the_same_one_asset_input(env):
    code, ev, db, disp, token = commit_run(env)
    assert code == 0
    run_id, chart, scope_target, plan_json, manifest_json, digest, triggered_by = db.inserted_run
    want, want_digest = _frozen_dispatcher().build_manifest(chart_id=CHART, candidate=LATTA, expected_code_digest=_hex(ASSET))
    assert json.loads(manifest_json) == want and digest == want_digest
    assert gad.canonical_json(want).encode() == _frozen_dispatcher()._canonical_json(want).encode()
    lw, lw_digest = slw.build_level_manifest(chart_id=CHART, plan_waves=[[ASSET]], rows={ASSET: LATTA}, writer_digests={ASSET: _hex(ASSET)})
    assert lw == want and lw_digest == want_digest
    assert set(want) == {"version", "chart_id", "scope", "scope_target", "action", "waves", "assets"}      # no new key
    assert want["assets"][0]["scope"] == "global" and want["scope"] == "asset_set" and want["action"] == "rebuild"
    assert chart == CHART and scope_target == ASSET and json.loads(plan_json) == [ASSET]
    assert triggered_by == gad.build_triggered_by(CHART, gad.sha256_json(json.loads(pathlib.Path(env["receipt"]).read_text())["impact"]))


def test_the_real_runner_accepts_the_one_asset_global_manifest_and_keeps_the_assets_scope_global():
    sys.path.insert(0, str(REPO / "platform/python-sidecar"))
    try:
        from pipeline.orchestrator.runner import validate_frozen_run_manifest
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"frozen runner not importable here: {exc.__class__.__name__}")
    m, d = slw.build_level_manifest(chart_id=CHART, plan_waves=[[ASSET]], rows={ASSET: LATTA}, writer_digests={ASSET: _hex(ASSET)})
    frozen = validate_frozen_run_manifest({"plan_manifest": m, "plan_manifest_digest": d, "chart_id": CHART, "scope": "asset_set",
                                           "scope_target": ASSET, "action": "rebuild", "plan": [ASSET]})
    assert frozen.plan == [ASSET] and frozen.asset_scopes[ASSET] == "global"
    # runner.py:619 / :839: a global asset's throughput row is written with chart_id None whatever the run's chart is
    text = (REPO / "platform/python-sidecar/pipeline/orchestrator/runner.py").read_text()
    assert 'eff_chart_id = None if asset_scopes.get(asset_id) == "global" else chart_id' in text
    assert 'return None if asset_scopes.get(a) == "global" else chart_id' in text


def test_triggered_by_is_a_short_fixed_prefix_that_fits_the_column_and_collides_with_no_test_trigger():
    value = gad.build_triggered_by(CHART, _hex("impact"))
    assert value == f"global-asset-dispatch:anchor_chart={CHART};impact_sha256={_hex('impact')[:16]}"
    assert value.startswith(gad.TRIGGERED_BY_PREFIX) and len(value) <= gad.TRIGGERED_BY_MAX_CHARS and len(value) < 120
    # build_runs.triggered_by is TEXT NOT NULL (no length limit) -- the measurement the claim rests on:
    m = json.loads((REPO / "00_ARCHITECTURE/briefs/nirmana/engine/measurements/A1_before_20260926T120730Z.json").read_text()
                   ) if (REPO / "00_ARCHITECTURE/briefs/nirmana/engine/measurements/A1_before_20260926T120730Z.json").exists() else None
    if m is not None:
        assert "triggered_by text NOT NULL" in json.dumps(m)
    known = {"nirmana-f0-machinery-canary", "gochara-v5-small-test", slw.TRIGGERED_BY, "l3-lane-frozen-manifest-rebuild", "nirmana-campaign",
             "manual", "test", "asset_runner"}
    assert value not in known and not any(value.startswith(k) or k.startswith(value) for k in known)
    for bad_anchor in ("g", "x" * 300):
        with pytest.raises(slw.LevelWaveError):
            gad.build_triggered_by(bad_anchor, _hex("impact"))


def test_the_insert_statements_are_the_waves_own_text():
    src = " ".join(__import__("inspect").getsource(slw.insert_run).split())
    assert " ".join(gad.INSERT_RUN_SQL.split()) in src
    assert " ".join(gad.INSERT_RUN_ASSET_SQL.split()) in src
    assert "scope_target" in gad.INSERT_RUN_SQL and "'asset_set'" in gad.INSERT_RUN_SQL and "'rebuild'" in gad.INSERT_RUN_SQL
    assert " ".join(gad.ANCHOR_ACTIVE_SQL.split()) in src


def test_the_advisory_lock_is_the_waves_chart_key(env):
    db = FakeDB()
    run(env, argv_for(env), db=db)
    locks = [e[2][0] for e in db.statements() if "pg_advisory_xact_lock" in e[1]]
    assert locks[0] == slw._lock_key(CHART) and locks[1].endswith(ASSET)


# ───────────────────────── the receipt: closed schema, safe path ─────────────────────────

def _valid_receipt(env):
    code, ev = run(env, argv_for(env))
    assert code == 0
    return json.loads(pathlib.Path(env["receipt"]).read_text())


def test_the_receipt_schema_is_closed_and_self_consistent(env):
    rec = _valid_receipt(env)
    gad.validate_receipt(rec)
    assert set(rec) == set(gad.RECEIPT_KEYS) and rec["schema"] == "suvarna-global-dispatch-receipt/v1"
    for key in ("run_id", "asset", "anchor_chart", "manifest_digest", "image_sha", "impact", "impact_sha256", "pre_fingerprint",
                "confirm_token", "committed", "planned_at", "committed_at"):
        assert key in rec
    extra = dict(rec, surprise=1)
    missing = {k: v for k, v in rec.items() if k != "impact_sha256"}
    tampered = dict(rec, impact_sha256=_hex("other"))
    committed_without_run = dict(rec, committed=True)
    bad_digest = dict(rec, manifest_digest="abc")
    bad_token = dict(rec, confirm_token="1ASSETS_ABCDEF_FORCE_FROZEN_REBUILD")
    phantom = dict(rec, anchor_chart="362f9f17-95a5-490b-a5a7-027d3e0efda0")
    for bad in (extra, missing, tampered, committed_without_run, bad_digest, bad_token, phantom, "nope", {}):
        with pytest.raises(slw.LevelWaveError):
            gad.validate_receipt(bad)
    with pytest.raises(slw.LevelWaveError):
        gad.new_receipt(not_a_field=1)


def test_the_receipt_path_must_be_outside_the_repo_and_never_clobbers_a_committed_receipt(env):
    inside = str(pathlib.Path(env["repo"]) / "receipt.json")
    args = argv_for(env)
    args.receipt = inside
    code, ev = run(env, args)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_PATH_INVALID"]
    args.receipt_in_repo = True
    pathlib.Path(env["repo"], "platform").exists()
    code, ev = run(env, args)
    assert code == 0 and pathlib.Path(inside).exists()
    args = argv_for(env)
    args.receipt = str(pathlib.Path(env["tmp"]) / "missing_dir" / "r.json")
    code, ev = run(env, args)
    assert codes_of(ev) == ["RECEIPT_PATH_INVALID"]
    # a committed receipt of another run is never overwritten; a file that is not a receipt is not overwritten either
    code, ev, db, disp, token = commit_run(env)
    assert code == 0
    code, ev = run(env, argv_for(env, "--allow-redispatch", disp.calls[0]))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_PATH_INVALID"]
    junk = pathlib.Path(env["tmp"]) / "out" / "junk.json"
    junk.write_text("not a receipt")
    args = argv_for(env)
    args.receipt = str(junk)
    code, ev = run(env, args)
    assert codes_of(ev) == ["RECEIPT_PATH_INVALID"] and junk.read_text() == "not a receipt"


def test_the_cli_requires_the_anchor_the_receipt_and_has_no_force_or_verify_flag():
    parser = gad.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--assets", ASSET, "--receipt", "/x"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--assets", ASSET, "--anchor-chart", CHART])
    opts = {o for a in parser._actions for o in a.option_strings}
    assert "--force-execute" not in opts and "--verify-forced" not in opts           # implied and mandatory, never optional
    assert {"--commit", "--confirm", "--accept-lit-dependent", "--allow-redispatch", "--verify-run", "--receipt"} <= opts


def test_main_refuses_without_a_database_url(monkeypatch, capsys):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert gad.main(["--assets", ASSET, "--anchor-chart", CHART, "--receipt", "/x"]) == gad.EXIT_NO_DATABASE_URL
