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
import os
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
                 global_record="auto", chart_bound=(), fail_commit=False, run_row=None, impact_after_first=None, duration_column=True,
                 terminalise_rows=1, build_record_error=None):
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
        self.duration_column, self.terminalise_rows, self.build_record_error = duration_column, terminalise_rows, build_record_error
        self.ended = T0 + timedelta(seconds=40)

    def connect(self):
        self.log.append(("connect",))
        return FakeConn(self)

    def respond(self, sql, params):
        if "pg_advisory_xact_lock" in sql:
            return []
        if "FROM information_schema.columns" in sql:
            return [{"?column?": 1}] if self.duration_column else []
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
            if self.build_record_error:
                raise self.build_record_error
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
        return {"definition": fd.FINGERPRINT_DEFINITION, "declarations_sha256": decls.sha256, "fingerprints": {u: sha for u in units},
                "tables": {u: {t: {"sha256": sha, "rows": self.rows} for t in decls.tables(u)} for u in units}, "projections": {}, "horizons": {}}


RUNNER_WITH_FORCE = 'force = os.environ.get("NIRMANA_FORCE_EXECUTE", "").strip().lower() in ("1", "true", "yes")\n'
FORCE_GATE = "    if declared_deps is not None and has_cowriters is not None and not force:\n        return _skip()\n"
DURATION_WRITE = ('    cur.execute("""UPDATE asset_throughput\n               SET state = %s, last_error = NULL, duration_seconds = %s, rows_per_second = %s\n'
                  '               WHERE asset_id = %s""", ())\n')
ASSET_RUNNER_WITH_FORCE = "def _complete(cur, force):\n" + FORCE_GATE + DURATION_WRITE
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


class RealProcessAttempt(BaseException):
    """Raised when a test reaches for a real process. A BaseException on purpose: the tool's broad `except Exception` paths can
    never swallow it into an exit code, so an attempt always fails the test loudly."""


BLOCKED_OS_PROCESS_CALLS = ("system", "popen", "posix_spawn", "posix_spawnp", "execl", "execle", "execlp", "execlpe", "execv", "execve",
                            "execvp", "execvpe", "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp",
                            "spawnvpe", "fork", "forkpty")


@pytest.fixture(autouse=True)
def no_real_subprocess(monkeypatch):
    """No test may start a real process: not gcloud, not git, by ANY route (subprocess.* and os.system / popen / exec* / spawn* /
    posix_spawn* / fork). A test that wants to observe a command patches subprocess.run itself (a later patch wins over this one)."""
    def blocked(*a, **k):
        raise RealProcessAttempt(f"a real subprocess was requested in a test: {a[:1]}")
    for name in ("run", "Popen", "check_output", "check_call", "call", "getoutput", "getstatusoutput"):
        monkeypatch.setattr(subprocess, name, blocked)
    for name in BLOCKED_OS_PROCESS_CALLS:
        if hasattr(os, name):
            monkeypatch.setattr(os, name, blocked)


def test_the_no_process_fixture_blocks_every_os_level_route():
    import os
    for name in BLOCKED_OS_PROCESS_CALLS:
        if hasattr(os, name):
            with pytest.raises(RealProcessAttempt, match="real subprocess"):
                getattr(os, name)("true")
    with pytest.raises(RealProcessAttempt, match="real subprocess"):
        subprocess.getoutput("true")


SINGLE_WRITERS = ("bg_ontology", "bg_doshas", "bg_yogas", "bg_dasha_systems", "bg_class_priors", "bg_class_lifetime_counts", "bg_not_declared", "bg_text_index", "bg_texts",
                  "bg_ghatana", "bg_formula_constants")


@pytest.fixture
def env(tmp_path):
    repo = tmp_path / "repo"
    gen = repo / "platform" / "src" / "generated"
    gen.mkdir(parents=True)
    digests = {ASSET: _hex(ASSET)}
    (gen / "nirmana-writer-digests.json").write_text(json.dumps({"version": 1, "writers": digests}))
    wr = repo / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "writers"
    wr.mkdir(parents=True)
    # the real shape: two classes in one file are two runs (no siblings)
    (wr / "bg_phaladeepika_vedha.py").write_text("@register('bg_vedha_malefic_scale')\nclass A:\n    pass\n\n\n@register('bg_phaladeepika_latta')\nclass B:\n    pass\n")
    (wr / "singles.py").write_text("".join(f"@register('{a}')\nclass C{i}:\n    pass\n\n\n" for i, a in enumerate(SINGLE_WRITERS)))
    nested = wr / "ph_sub"
    nested.mkdir()
    (nested / "__init__.py").write_text("@register('bg_nested_writer')\nclass N:\n    pass\n")
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


def test_without_a_fake_the_default_dispatch_goes_through_a_patched_subprocess_run_that_records_and_refuses(env, monkeypatch):
    calls = []

    def recording_refusal(cmd, **kw):
        calls.append((cmd, kw))                                   # RECORDS the call; no process is started
        raise RuntimeError("test double: refused, no process started")

    monkeypatch.setattr(subprocess, "run", recording_refusal)
    token = plan_token(env)
    db = FakeDB()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA,)), dispatch=None)
    assert code == slw.EXIT_DISPATCH_FAILED and "no process started" in last(ev)["dispatch_error"]
    assert len(calls) == 1                                        # the default resolved subprocess.run AT CALL TIME: exactly one attempt
    cmd, kw = calls[0]
    assert cmd == slw.dispatch_command(run_id=db.inserted_run[0], project="madhav-astrology", region="asia-south1",
                                       job="brahma-build-pipeline-job", force_execute=True)
    assert kw["stdin"] == subprocess.DEVNULL and kw["env"]["CLOUDSDK_CORE_DISABLE_PROMPTS"] == "1" and kw["timeout"] > 0


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
    again = argv_for(env)
    again.receipt = str(env["tmp"] / "out" / "second_receipt.json")        # the first receipt's path would refuse first (clobber guard)
    code2, ev2 = run(env, again, db=db2, dispatch=disp)
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
    assert set(rec) == set(gad.RECEIPT_KEYS) - {"expected_change"} and rec["schema"] == "suvarna-global-dispatch-receipt/v1"
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


# ───────────────────────── review fixes: the receipt, the duration preflight, the verification guard ─────────────────────────

def _bytes(env):
    return pathlib.Path(env["receipt"]).read_bytes()


def test_commit_onto_an_existing_committed_receipt_is_refused_before_the_insert(env):
    code, ev, db0, disp0, token = commit_run(env)                # a COMMITTED receipt of run X now sits at env["receipt"]
    assert code == 0
    before = _bytes(env)
    db, disp = FakeDB(), Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA, PRE_SHA)), dispatch=disp)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_PATH_INVALID"]        # exit 4, not 'nothing inserted' after a COMMIT
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds() and disp.calls == [] and last(ev)["committed_runs"] == []
    assert _bytes(env) == before                                  # never clobbered


def test_a_receipt_that_cannot_be_written_is_refused_before_the_insert(env, monkeypatch):
    token = plan_token(env)
    pathlib.Path(env["receipt"]).unlink()
    real = gad.write_receipt

    def failing(path, doc):
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(gad, "write_receipt", failing)
    db, disp = FakeDB(), Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA,)), dispatch=disp)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_PATH_INVALID"] and "Permission denied" in last(ev)["refusals"][0]["detail"]
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds() and disp.calls == []
    monkeypatch.setattr(gad, "write_receipt", real)


def _fail_when_committed(monkeypatch, exc):
    real = gad.write_receipt

    def writer(path, doc):
        if doc.get("committed"):
            raise exc
        return real(path, doc)

    monkeypatch.setattr(gad, "write_receipt", writer)


def test_a_receipt_write_failure_after_the_commit_terminalises_the_run_and_reports_it_honestly(env, monkeypatch, capsys):
    token = plan_token(env)
    pathlib.Path(env["receipt"]).unlink()
    _fail_when_committed(monkeypatch, OSError(28, "No space left on device"))
    db, disp = FakeDB(), Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA,)), dispatch=disp)
    run_id = db.inserted_run[0]
    last_ev = last(ev)
    assert code == slw.EXIT_UNEXPECTED and last_ev["event"] == "run_committed_receipt_not_written"
    assert "run committed, receipt not written" in last_ev["error"] and run_id in last_ev["error"] and last_ev["terminalised"] is True
    assert last_ev["unexpected"] is True and [r["run_id"] for r in last_ev["committed_runs"]] == [run_id]
    assert db.kinds().count("commit") == 2                        # the run's COMMIT, then the terminalise's
    (upd,) = [e for e in db.statements() if e[1].startswith("WITH failed_run AS")]
    assert "state='planned'" in upd[1] and upd[2][1] == run_id and "receipt not written" in upd[2][0]   # the same discipline as a dispatch failure
    assert disp.calls == []                                       # never dispatched
    assert run_id in capsys.readouterr().err                      # the operator can find the run
    assert not pathlib.Path(env["receipt"]).exists() or json.loads(_bytes(env).decode())["committed"] is False


def test_a_receipt_write_failure_after_the_commit_with_a_failing_terminalise_names_the_blocked_run(env, monkeypatch, capsys):
    token = plan_token(env)
    pathlib.Path(env["receipt"]).unlink()
    _fail_when_committed(monkeypatch, OSError(5, "Input/output error"))
    db, disp = FakeDB(), Dispatch()
    orig = db.respond

    def respond(sql, params):
        if sql.startswith("WITH failed_run AS"):
            raise RuntimeError("terminalise connection dropped")
        return orig(sql, params)

    db.respond = respond
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA,)), dispatch=disp)
    e = last(ev)
    assert code == slw.EXIT_UNEXPECTED and e["event"] == "run_committed_receipt_not_written" and e["terminalised"] is False
    assert "BLOCKS chart" in e["warning"] and "by hand" in e["warning"] and db.inserted_run[0] in e["warning"] and disp.calls == []
    assert db.inserted_run[0] in capsys.readouterr().err


def test_the_duration_column_must_exist_in_plan_and_commit_mode(env):
    db = FakeDB(duration_column=False)
    code, ev = run(env, argv_for(env), db=db)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["DURATION_COLUMN_ABSENT"] and db.inserts("build_runs") == []
    assert "1200_asset_throughput_duration_seconds" in last(ev)["refusals"][0]["detail"]
    token = plan_token(env)
    db2, disp = FakeDB(duration_column=False), Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db2, dispatch=disp)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["DURATION_COLUMN_ABSENT"] and "commit" not in db2.kinds() and disp.calls == []


def test_the_duration_probe_is_the_runners_own_and_the_marker_is_in_the_real_asset_runner():
    runner = " ".join((REPO / "platform/python-sidecar/pipeline/orchestrator/asset_runner.py").read_text().split())
    assert " ".join(gad.DURATION_COLUMN_SQL.split()) in runner
    real = (REPO / "platform/python-sidecar/pipeline/orchestrator/asset_runner.py").read_text()
    for _rel, pattern, _what in gad.DURATION_MARKERS:
        assert any(pattern.search(t) for t in gad.duration_write_strings(real))          # the REAL write, matched as code
        assert "duration_seconds = %s, rows_per_second = %s" in " ".join(real.split())   # the adjacent pair, as the runner writes it


def test_an_image_without_the_duration_write_is_refused_in_plan_mode_before_any_database_contact(env):
    no_duration = "def _complete(cur, force):\n" + FORCE_GATE
    db = FakeDB()
    code, ev = run(env, argv_for(env), db=db, git=FakeGit(deployed=env["digests"], asset_runner_text=no_duration))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["IMAGE_DOES_NOT_RECORD_DURATION"] and db.log == []
    assert "writes asset_throughput.duration_seconds" in last(ev)["refusals"][0]["detail"]
    # a commit-mode run refuses it too, and an unreadable runner file refuses (never a pass)
    token = plan_token(env)
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=FakeDB(), dispatch=Dispatch(),
                   git=FakeGit(deployed=env["digests"], asset_runner_text=no_duration))
    assert codes_of(ev) == ["IMAGE_DOES_NOT_RECORD_DURATION"]
    unreadable = lambda repo, args: subprocess.CompletedProcess(args, 128, "", "fatal: bad object")  # noqa: E731
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.check_image_records_duration(env["repo"], sha_of("deadbeef"), git=unreadable)
    assert exc.value.refusals[0]["code"] == "IMAGE_DOES_NOT_RECORD_DURATION" and "unreadable" in exc.value.refusals[0]["detail"]


def test_the_plan_reports_the_duration_preflight(env):
    code, ev = run(env, argv_for(env))
    assert code == 0 and last(ev)["force_support_check"]["duration_write_markers"] == ["writes asset_throughput.duration_seconds on completion"]


def test_an_unreadable_build_record_after_a_completed_run_is_reported_precisely(env):
    err = RuntimeError('UndefinedColumn: column "duration_seconds" does not exist')
    code, ev, db, disp, token = commit_run(env, db=FakeDB(build_record_error=err))
    s = last(ev)
    assert code == gad.EXIT_VERIFY_FAILED and s["event"] == "summary" and s["verification"]["codes"] == ["BUILD_RECORD_UNREADABLE"]
    note = " ".join(s["verification"]["notes"])
    assert "COMPLETED" in note and "duration_seconds" in note and "may be planned" not in json.dumps(s)
    assert s["verification"]["fingerprint_equal"] is True and len(disp.calls) == 1        # the rest of the verification still ran


@pytest.mark.parametrize("disposition", ["error", "failed", None])
def test_a_completed_run_whose_disposition_is_neither_build_nor_skip_is_never_a_pass(env, disposition):
    code, ev, db, disp, token = commit_run(env, db=FakeDB(dispositions={ASSET: disposition}))
    s = last(ev)
    assert code == gad.EXIT_VERIFY_FAILED and code != 0
    assert s["verification"]["codes"] == ["FORCED_EFFECT_UNVERIFIED"] and s["verification"]["verdict"] != "PASS"
    assert s["forced_effective"] is None and "FORCE_DID_NOT_TAKE_EFFECT" not in s["verification"]["codes"]


def test_a_redeploy_between_the_insert_and_the_dispatch_never_dispatches(env):
    token = plan_token(env)
    db = FakeDB()
    orig = db.respond

    def respond(sql, params):
        if sql.startswith("INSERT INTO build_runs"):
            pathlib.Path(env["jobfile"]).write_text(sha_of("a newer deploy") + "\n")        # the redeploy lands right after the INSERT
        return orig(sql, params)

    db.respond = respond
    disp = Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=disp, fp=FakeFp((PRE_SHA,)))
    assert code == gad.EXIT_DISPATCH_FAILED and disp.calls == [] and "JOB_SHA_CHANGED" in last(ev)["dispatch_error"]
    assert any(e[1].startswith("WITH failed_run AS") for e in db.statements())


@pytest.mark.parametrize("what", ["not_committed", "run_id", "asset", "anchor"])
def test_verify_run_refuses_a_receipt_that_is_not_this_runs(env, what):
    code, ev, db, disp, token = commit_run(env)
    assert code == 0
    rec = json.loads(_bytes(env).decode())
    run_id, asset, anchor = rec["run_id"], ASSET, CHART
    if what == "not_committed":
        pathlib.Path(env["receipt"]).write_text(json.dumps(dict(rec, committed=False, committed_at=None)))
    elif what == "run_id":
        run_id = "33333333-3333-4333-8333-333333333333"
    elif what == "asset":
        asset = "bg_other_asset"
    else:
        anchor = OTHER_CHART
    args = gad.build_parser().parse_args(["--assets", asset, "--anchor-chart", anchor, "--receipt", env["receipt"], "--repo", env["repo"],
                                          "--verify-run", run_id])
    ok_row = {"id": run_id, "chart_id": anchor, "state": "completed", "triggered_by": rec["triggered_by"],
              "plan_manifest_digest": rec["manifest_digest"]}
    db2, fp2 = FakeDB(run_row=ok_row), FakeFp((PRE_SHA,))
    code, ev = run(env, args, db=db2, fp=fp2)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_RUN_MISMATCH"]
    assert last(ev)["refusals"][0]["detail"].startswith("the receipt is not the committed receipt of this run, asset and anchor chart")
    assert db2.log == [] and fp2.opened == 0                       # refused from the receipt alone, before any database contact


def test_an_external_dependency_that_goes_stale_inside_the_transaction_refuses_and_inserts_nothing(env):
    latta = dict(LATTA, depends_on=["bg_ontology"])
    lit_dep = {"bg_ontology": ("lit", "fresh", "data")}
    token = plan_token(env, db=FakeDB(candidates=[[latta]], deps=lit_dep))
    db = FakeDB(candidates=[[latta]], deps=lit_dep)
    orig, seen = db.respond, {"n": 0}

    def respond(sql, params):
        if "unnest(%s::text[]) AS dep" in sql:
            seen["n"] += 1
            if seen["n"] >= 2:                                    # the 1st read is precheck_external, the 2nd is IN the transaction
                db.deps = {"bg_ontology": ("stale", "fresh", "data")}
        return orig(sql, params)

    db.respond = respond
    disp = Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA,)), dispatch=disp)
    assert seen["n"] == 2 and code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["DEPENDENCY_NOT_READY"]
    assert db.inserts("build_runs") == [] and "commit" not in db.kinds() and disp.calls == []


class _FrozenStub:
    """Stands in for dispatch_frozen_rebuild: records the terminalise call and the DB state at load time."""

    def __init__(self, db):
        self.db, self.statements_at_load, self.terminalised = db, None, []
        self.loads = 0

    def load(self):
        self.loads += 1
        self.statements_at_load = len(self.db.statements())
        return self

    def terminalize_dispatch_failure(self, cur, *, run_id, error):
        self.terminalised.append((run_id, error))
        cur.execute("WITH failed_run AS (UPDATE build_runs SET state='failed' WHERE id=%s AND state='planned' RETURNING id) "
                    "UPDATE build_run_assets SET state='aborted'", (run_id,))


def test_the_frozen_dispatcher_is_loaded_before_any_database_contact_and_is_the_one_that_terminalises(env, monkeypatch):
    token = plan_token(env)
    db = FakeDB()
    stub = _FrozenStub(db)
    monkeypatch.setattr(slw, "_load_frozen_dispatcher", stub.load)
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=Dispatch(fail=True), fp=FakeFp((PRE_SHA,)))
    assert code == gad.EXIT_DISPATCH_FAILED and stub.loads == 1 and stub.statements_at_load == 0
    assert stub.terminalised == [(db.inserted_run[0], "gcloud refused")]


def test_a_frozen_dispatcher_that_cannot_be_loaded_strands_nothing(env, monkeypatch):
    token = plan_token(env)

    def cannot_load():
        raise RuntimeError("dispatch_frozen_rebuild.py is unreadable")

    monkeypatch.setattr(slw, "_load_frozen_dispatcher", cannot_load)
    db, disp = FakeDB(), Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=disp, fp=FakeFp((PRE_SHA,)))
    assert code == slw.EXIT_UNEXPECTED and db.inserts("build_runs") == [] and "commit" not in db.kinds() and disp.calls == []
    assert last(ev)["committed_runs"] == [] and last(ev)["warning"] == "no run was committed"


def test_plan_mode_never_loads_the_frozen_dispatcher(env, monkeypatch):
    def boom():
        raise AssertionError("plan mode must not load the frozen dispatcher")

    monkeypatch.setattr(slw, "_load_frozen_dispatcher", boom)
    code, ev = run(env, argv_for(env))
    assert code == 0


def test_the_receipt_on_disk_names_the_committed_run_even_when_the_dispatch_is_interrupted(env):
    token = plan_token(env)

    class Interrupted(Dispatch):
        def __call__(self, run_id):
            raise KeyboardInterrupt

    db = FakeDB()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=Interrupted(), fp=FakeFp((PRE_SHA,)))
    assert code == slw.EXIT_INTERRUPTED
    rec = json.loads(_bytes(env).decode())
    gad.validate_receipt(rec)
    assert rec["committed"] is True and rec["run_id"] == db.inserted_run[0] and rec["committed_at"] == T0.isoformat(timespec="seconds")
    assert [e["event"] for e in ev][0] == "run_committed"


def test_a_dispatch_failure_reports_terminalised_only_when_the_update_matched_a_planned_run(env):
    token = plan_token(env)
    db = FakeDB()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=Dispatch(fail=True), fp=FakeFp((PRE_SHA,)))
    assert code == gad.EXIT_DISPATCH_FAILED and last(ev)["terminalise_warning"] is None
    assert json.loads(_bytes(env).decode())["verification"]["notes"][-1] == "terminalised"
    # the run had already started (a gcloud timeout whose execution started late): the UPDATE matches 0 rows
    pathlib.Path(env["receipt"]).unlink()
    db0 = FakeDB(terminalise_rows=0)
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db0, dispatch=Dispatch(fail=True), fp=FakeFp((PRE_SHA,)))
    e = [x for x in ev if x["event"] == "dispatch_failed"][0]
    assert code == gad.EXIT_DISPATCH_FAILED and e["terminalised"] is False
    assert "NOT terminalised" in e["warning"] and "0 rows" in e["warning"] and f"--verify-run {db0.inserted_run[0]}" in e["warning"]
    notes = json.loads(_bytes(env).decode())["verification"]["notes"]
    assert "terminalised" != notes[-1] and "NOT terminalised" in notes[-1]


def test_a_gcloud_timeout_whose_run_already_started_is_not_reported_as_terminalised(env, monkeypatch):
    def timeout(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, 1)

    monkeypatch.setattr(subprocess, "run", timeout)
    token = plan_token(env)
    db = FakeDB(terminalise_rows=0)
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA,)), dispatch=None)
    e = [x for x in ev if x["event"] == "dispatch_failed"][0]
    assert code == gad.EXIT_DISPATCH_FAILED and "timed out" in e["error"] and "NOT terminalised" in e["warning"]


def test_plan_mode_also_refuses_a_committed_receipt_path_before_any_insert(env):
    code, ev, db0, disp0, token = commit_run(env)
    assert code == 0
    before = _bytes(env)
    db = FakeDB()
    code, ev = run(env, argv_for(env), db=db)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_PATH_INVALID"] and db.inserts("build_runs") == [] and _bytes(env) == before
    assert "pg_advisory_xact_lock" not in " ".join(e[1] for e in db.statements())     # refused before the transaction took its locks


def test_write_receipt_itself_never_clobbers_a_committed_receipt_of_another_run(env):
    code, ev, db0, disp0, token = commit_run(env)
    assert code == 0
    before = _bytes(env)
    other = json.loads(before.decode())
    other.update(run_id="44444444-4444-4444-8444-444444444444")
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.write_receipt(pathlib.Path(env["receipt"]), other)
    assert exc.value.refusals[0]["code"] == "RECEIPT_PATH_INVALID" and _bytes(env) == before
    gad.write_receipt(pathlib.Path(env["receipt"]), json.loads(before.decode()))        # the very run it continues is allowed


# ───────────────────────── round 2: the duration marker is code, the fixture error is unswallowable, UNKNOWN run state ─────────────────────────

COMMENT_DECOY = "# the completion UPDATE named `duration_seconds = %s` unconditionally (a comment, not a write)\n"


@pytest.mark.parametrize("name,runner", [
    ("only the comment line", "def _complete(cur, force):\n" + FORCE_GATE + "\n" + COMMENT_DECOY),
    ("comment holding the whole pair", "def _complete(cur, force):\n" + FORCE_GATE + "# SET duration_seconds = %s, rows_per_second = %s\n"),
    ("inline comment", "def _complete(cur, force):\n" + FORCE_GATE + "    x = 1  # UPDATE asset_throughput SET duration_seconds = %s, rows_per_second = %s\n"),
    ("docstring", 'def _complete(cur, force):\n    """UPDATE asset_throughput SET duration_seconds = %s, rows_per_second = %s"""\n' + FORCE_GATE),
    ("module docstring", '"""UPDATE asset_throughput SET duration_seconds = %s, rows_per_second = %s"""\ndef f(force):\n' + FORCE_GATE),
    ("the write without the adjacent pair", "def _complete(cur, force):\n" + FORCE_GATE +
     '    cur.execute("UPDATE asset_throughput SET last_error = NULL, duration_seconds = %s WHERE x", ())\n'),
    ("pair in an unrelated statement", "def _complete(cur, force):\n" + FORCE_GATE +
     '    cur.execute("UPDATE other_table SET duration_seconds = %s, rows_per_second = %s", ())\n'),
    ("pattern split across two strings", "def _complete(cur, force):\n" + FORCE_GATE +
     '    a = "UPDATE asset_throughput SET x = 1"\n    b = "duration_seconds = %s, rows_per_second = %s"\n'),
    ("not parseable (the whole write present as text)", FORCE_GATE + DURATION_WRITE),
])
def test_a_decoy_without_a_real_duration_write_is_refused(env, name, runner):
    # the runner passes the force check (its marker is present as text) but its duration "write" is only a comment / doc / fragment
    git = FakeGit(deployed=env["digests"], asset_runner_text=runner)
    db = FakeDB()
    code, ev = run(env, argv_for(env), db=db, git=git)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["IMAGE_DOES_NOT_RECORD_DURATION"], name
    assert db.log == []
    if name.startswith("not parseable"):
        assert "could not be checked" in last(ev)["refusals"][0]["detail"]


def test_the_real_write_passes_and_its_strings_are_matched_one_at_a_time():
    pattern = gad.DURATION_MARKERS[0][1]
    assert any(pattern.search(t) for t in gad.duration_write_strings(ASSET_RUNNER_WITH_FORCE))
    assert gad.duration_write_strings(COMMENT_DECOY) == []
    with pytest.raises(ValueError):
        gad.duration_write_strings("def broken(:\n")


@pytest.mark.parametrize("route", ["default_dispatch", "os_system_in_the_database_fake"])
def test_a_real_process_attempt_is_never_swallowed_by_the_tools_broad_except_paths(env, route):
    token = plan_token(env)
    db = FakeDB()
    if route == "os_system_in_the_database_fake":
        orig = db.respond

        def respond(sql, params):
            if "FROM asset_throughput WHERE asset_id = %s AND chart_id IS NULL" in sql:
                os.system("true")                                  # reached inside verify_forced_run's `except Exception`
            return orig(sql, params)

        db.respond = respond
    with pytest.raises(RealProcessAttempt):
        # default_dispatch: no injected dispatch and no subprocess patch -> slw.dispatch_run_with_timeout -> blocked subprocess.run,
        # inside the tool's `except Exception` around the dispatch; the other route is inside the build-record `except Exception`
        run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA, PRE_SHA)),
            dispatch=None if route == "default_dispatch" else Dispatch())
    assert RealProcessAttempt.__mro__[1] is BaseException and not issubclass(RealProcessAttempt, Exception)


@pytest.mark.parametrize("rows", [None, -1])
def test_a_receipt_failure_with_an_unreported_terminalise_count_says_the_run_state_is_unknown(env, monkeypatch, capsys, rows):
    token = plan_token(env)
    pathlib.Path(env["receipt"]).unlink()
    _fail_when_committed(monkeypatch, OSError(28, "No space left on device"))
    db, disp = FakeDB(terminalise_rows=rows), Dispatch()
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA,)), dispatch=disp)
    e, run_id = last(ev), db.inserted_run[0]
    assert code == slw.EXIT_UNEXPECTED and e["event"] == "run_committed_receipt_not_written" and e["terminalised"] is None
    for text in (e["warning"], e["error"], capsys.readouterr().err):
        assert "UNKNOWN" in text and f"--verify-run {run_id}" in text and "was terminalised" not in text
    assert disp.calls == []


def test_a_dispatch_failure_with_an_unreported_terminalise_count_is_not_reported_as_terminalised(env):
    token = plan_token(env)
    db = FakeDB(terminalise_rows=None)
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=db, dispatch=Dispatch(fail=True), fp=FakeFp((PRE_SHA,)))
    e = [x for x in ev if x["event"] == "dispatch_failed"][0]
    assert code == gad.EXIT_DISPATCH_FAILED and e["terminalised"] is None and "UNKNOWN" in e["warning"]
    assert json.loads(_bytes(env).decode())["verification"]["notes"][-1] != "terminalised"


def test_receipt_not_written_never_leaves_the_run_state_blank():
    exc = gad.ReceiptNotWritten("55555555-5555-4555-8555-555555555555", CHART, OSError("disk"), {"terminalised": None, "warning": None})
    assert "UNKNOWN" in exc.detail and "--verify-run 55555555-5555-4555-8555-555555555555" in exc.detail and exc.terminalised is None
    ok = gad.ReceiptNotWritten("55555555-5555-4555-8555-555555555555", CHART, OSError("disk"), {"terminalised": True, "warning": None})
    assert "was terminalised" in ok.detail and "UNKNOWN" not in ok.detail


# ═════════════════════════ EXPECTED-CHANGE MODE (--expected-change FILE) ═════════════════════════
# The default path is unchanged (every test above). The mode is opt-in, declared in a file the token binds, accepted explicitly, and the post state is
# compared to the DECLARATION: never "anything goes". Fakes only; the autouse fixture blocks every real process.

ROWS_PRE, ROWS_POST = 8, 11                 # FakeFp reports `rows` per table; the latta unit has one table, so the unit total equals it


class FakeFpRows(FakeFp):
    """FakeFp whose rows per call differ (pre rows, then post rows)."""

    def __init__(self, shas, rows_seq):
        super().__init__(shas)
        self.rows_seq = list(rows_seq)

    def reader(self, conn, decls, units):
        n = self.calls
        self.rows = self.rows_seq[min(n, len(self.rows_seq) - 1)]
        return super().reader(conn, decls, units)


def _spec(**kw):
    d = {"asset": ASSET, "expected_post_row_count": ROWS_POST, "expected_post_fingerprint": POST_SHA,
         "why": "the L0 fix rebuild adds the three corrected rows", "decision": "N-150", "evidence": "rehearsal run of the fix on the scratch cluster"}
    d.update(kw)
    return {k: v for k, v in d.items() if v is not ...}


def write_spec(env, name="expected_change.json", **kw):
    p = env["tmp"] / name
    p.write_text(json.dumps(_spec(**kw)), encoding="utf-8")
    return str(p)


def xargs(env, path, *extra, accept=True, **kw):
    return argv_for(env, "--expected-change", path, *(["--accept-changed-output"] if accept else []), *extra, **kw)


def commit_expected(env, path, *, fp, db=None, dispatch=None, extra=()):
    db = db or FakeDB()
    code, ev = run(env, xargs(env, path, *extra), db=FakeDB(), fp=FakeFpRows((PRE_SHA,), (ROWS_PRE,)))
    assert code == 0, ev
    token = last(ev)["confirm_token"]
    db.log.clear()
    db.cand_calls = db.impact_calls = 0
    fp.calls = 0
    disp = dispatch if dispatch is not None else Dispatch()
    code, ev = run(env, xargs(env, path, *extra, commit=True, confirm=token), db=db, fp=fp, dispatch=disp)
    return code, ev, db, disp, token


# ── the file ──

def test_a_valid_expected_change_file_is_read_and_its_byte_digest_returned(env):
    path = write_spec(env)
    spec, sha = gad.load_expected_change(path, ASSET)
    assert spec["expected_post_row_count"] == ROWS_POST and spec["expected_post_fingerprint"] == POST_SHA and spec["asset"] == ASSET
    import hashlib
    assert sha == hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
    spec2, _ = gad.load_expected_change(write_spec(env, "b.json", expected_post_fingerprint=None, decision=None), ASSET)
    assert spec2["expected_post_fingerprint"] is None and spec2["decision"] is None and spec2["evidence"]


@pytest.mark.parametrize("kw", [
    dict(asset="bg_other"), dict(asset=None), dict(expected_post_row_count=0), dict(expected_post_row_count=-1), dict(expected_post_row_count=True),
    dict(expected_post_row_count="11"), dict(expected_post_row_count=None), dict(expected_post_fingerprint="abc"), dict(expected_post_fingerprint=POST_SHA.upper()),
    dict(why="TBD"), dict(why="n/a n/a n/a n/a n/a"), dict(why="short"), dict(why=...), dict(why=" padded reason for the change "),
    dict(decision="ratified"), dict(decision="TBD-1"), dict(decision=None, evidence=None), dict(evidence="todo later on"), dict(bogus=1),
])
def test_an_invalid_expected_change_file_is_refused(env, kw):
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.load_expected_change(write_spec(env, **kw), ASSET)
    assert exc.value.refusals[0]["code"] == "EXPECTED_CHANGE_INVALID"


def test_an_unreadable_malformed_duplicate_keyed_oversized_or_credential_named_file_is_refused(env):
    t = env["tmp"]
    cases = {"missing.json": None, "arr.json": "[1]", "bad.json": "{not json", "dup.json": '{"asset": "a", "asset": "b"}', "big.json": " " * (gad.EXPECTED_CHANGE_MAX_BYTES + 1),
             ".env.json": json.dumps(_spec()), "secrets.json": json.dumps(_spec()), "creds.pem": json.dumps(_spec()), "spec.txt": json.dumps(_spec())}
    for name, body in cases.items():
        if body is not None:
            (t / name).write_text(body)
        with pytest.raises(slw.LevelWaveRefusal) as exc:
            gad.load_expected_change(str(t / name), ASSET)
        assert exc.value.refusals[0]["code"] == "EXPECTED_CHANGE_INVALID", name
    with pytest.raises(slw.LevelWaveRefusal):
        gad.load_expected_change(str(t), ASSET)                                  # a directory
    with pytest.raises(slw.LevelWaveRefusal):
        gad.load_expected_change(None, ASSET)


# ── plan: impact, explicit acceptance, the token ──

def test_the_default_token_is_exactly_what_it_was_and_the_flag_without_a_file_is_bad_input(env):
    base = dict(manifest_digest=_hex("m"), asset=ASSET, anchor_chart=CHART, image_sha=sha_of("x"), impact_sha256=_hex("i"), pre_fingerprint=_hex("p"),
                accepted_lit=[], allow_redispatch=[])
    assert gad.build_confirm_token(**base) == gad.build_confirm_token(**base, expected_change_sha256=None, accepted_changed_output=False)
    assert gad.build_confirm_token(**base) != gad.build_confirm_token(**base, expected_change_sha256=_hex("f"), accepted_changed_output=True)
    code, ev = run(env, argv_for(env, "--accept-changed-output"))
    assert code == gad.EXIT_BAD_INPUT and "--accept-changed-output is only for --expected-change" in last(ev)["error"]


def test_the_token_binds_the_expected_change_files_bytes_and_the_acceptance(env):
    base = dict(manifest_digest=_hex("m"), asset=ASSET, anchor_chart=CHART, image_sha=sha_of("x"), impact_sha256=_hex("i"), pre_fingerprint=_hex("p"),
                accepted_lit=[], allow_redispatch=[], expected_change_sha256=_hex("f"), accepted_changed_output=True)
    t0 = gad.build_confirm_token(**base)
    assert gad.build_confirm_token(**{**base, "expected_change_sha256": _hex("g")}) != t0
    assert gad.build_confirm_token(**{**base, "accepted_changed_output": False}) != t0
    code, ev = run(env, xargs(env, write_spec(env)), fp=FakeFpRows((PRE_SHA,), (ROWS_PRE,)))
    code2, ev2 = run(env, xargs(env, write_spec(env, expected_post_row_count=ROWS_POST + 1)), fp=FakeFpRows((PRE_SHA,), (ROWS_PRE,)))
    assert code == code2 == 0 and last(ev)["confirm_token"] != last(ev2)["confirm_token"]
    assert last(ev)["confirm_token"] != plan_token(env, db=FakeDB())                 # and differs from the unchanged-content token


def test_a_changing_rebuild_is_refused_until_accepted_with_the_impact_printed_and_nothing_inserted(env):
    db = FakeDB()
    code, ev = run(env, xargs(env, write_spec(env), accept=False), db=db, fp=FakeFpRows((PRE_SHA,), (ROWS_PRE,)))
    r = last(ev)["refusals"][0]
    assert code == slw.REFUSAL_EXIT_CODE and r["code"] == "CHANGED_OUTPUT_NOT_ACCEPTED" and "--accept-changed-output" in r["detail"]
    assert any(DEPENDENT in l for l in r["impact_lines"]) and r["changed_output_lines"][0].startswith("CHANGING REBUILD of")
    assert db.inserts("build_runs") == [] and not pathlib.Path(env["receipt"]).exists()


def test_the_plan_prints_the_changing_rebuild_block_and_records_the_declaration_in_the_receipt(env):
    rows = [lit(CHART), lit(OTHER_CHART)]
    acc = ("--accept-lit-dependent", f"{DEPENDENT}@{CHART}", "--accept-lit-dependent", f"{DEPENDENT}@{OTHER_CHART}")
    code, ev = run(env, xargs(env, write_spec(env), *acc), db=FakeDB(throughput=rows), fp=FakeFpRows((PRE_SHA,), (ROWS_PRE,)))
    s = last(ev)
    assert code == 0 and s["committed"] is False
    ec = s["expected_change"]
    assert ec["pre_row_count"] == ROWS_PRE and ec["accepted_changed_output"] is True and ec["spec"]["expected_post_row_count"] == ROWS_POST
    lines = "\n".join(ec["changed_output_lines"])
    assert f"{DEPENDENT}@{CHART} is lit" in lines and "the runner stales this row" in lines and f"{DEPENDENT}@{OTHER_CHART} is lit" in lines
    assert any(DEPENDENT in l for l in s["impact_lines"])
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    gad.validate_receipt(rec)
    assert rec["expected_change"]["file_sha256"] == ec["file_sha256"] and rec["expected_change"]["outcome"] is None and rec["expected_change"]["post_row_count"] is None


def test_lit_dependents_still_need_their_own_explicit_flags_in_expected_change_mode(env):
    db = FakeDB(throughput=[lit(CHART)])
    code, ev = run(env, xargs(env, write_spec(env)), db=db, fp=FakeFpRows((PRE_SHA,), (ROWS_PRE,)))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["LIT_DEPENDENT"] and db.inserts("build_runs") == []


def test_a_declared_post_fingerprint_equal_to_the_pre_one_declares_no_change_and_is_refused(env):
    code, ev = run(env, xargs(env, write_spec(env, expected_post_fingerprint=PRE_SHA)), fp=FakeFpRows((PRE_SHA,), (ROWS_PRE,)))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["EXPECTED_CHANGE_INVALID"]


def test_a_file_for_another_asset_is_refused_before_any_database_contact(env):
    db = FakeDB()
    code, ev = run(env, xargs(env, write_spec(env, asset="bg_other")), db=db)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["EXPECTED_CHANGE_INVALID"] and db.log == []


# ── commit: the post state is compared to the declaration ──

def test_a_change_that_matches_the_declaration_passes_and_the_receipt_records_both_sides(env):
    path = write_spec(env)
    code, ev, db, disp, token = commit_expected(env, path, fp=FakeFpRows((PRE_SHA, POST_SHA), (ROWS_PRE, ROWS_POST)))
    s = last(ev)
    assert code == 0, s
    assert s["verification"]["verdict"] == "PASS" and s["verification"]["expectation"] == "MET" and s["verification"]["fingerprint_equal"] is False
    assert s["verification"]["row_counts"] == {"pre": ROWS_PRE, "post": ROWS_POST, "expected_post": ROWS_POST}
    assert len(disp.calls) == 1 and db.kinds().count("commit") == 1
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    gad.validate_receipt(rec)
    assert rec["pre_fingerprint"]["composite"] == PRE_SHA and rec["post_fingerprint"]["composite"] == POST_SHA
    assert rec["expected_change"]["pre_row_count"] == ROWS_PRE and rec["expected_change"]["post_row_count"] == ROWS_POST and rec["expected_change"]["outcome"] == "MET"
    assert rec["confirm_token"] == token and rec["committed"] is True


def test_without_a_declared_fingerprint_a_changed_post_with_the_declared_rows_passes_and_an_unchanged_one_does_not(env):
    path = write_spec(env, expected_post_fingerprint=None)
    code, ev, *_ = commit_expected(env, path, fp=FakeFpRows((PRE_SHA, POST_SHA), (ROWS_PRE, ROWS_POST)))
    assert code == 0 and last(ev)["verification"]["expectation"] == "MET"
    pathlib.Path(env["receipt"]).unlink()
    code, ev, *_ = commit_expected(env, path, fp=FakeFpRows((PRE_SHA, PRE_SHA), (ROWS_PRE, ROWS_POST)))
    s = last(ev)
    assert code == gad.EXIT_EXPECTATION_MISMATCH == 11 and s["verification"]["codes"] == ["EXPECTED_CHANGE_NOT_OBSERVED"]
    assert "did not change the content" in s["warning"]


def test_a_row_count_that_differs_from_the_declaration_is_exit_11_with_an_honest_receipt(env):
    code, ev, db, disp, token = commit_expected(env, write_spec(env), fp=FakeFpRows((PRE_SHA, POST_SHA), (ROWS_PRE, ROWS_POST + 2)))
    s = last(ev)
    assert code == 11 and s["verification"]["codes"] == ["EXPECTED_ROW_COUNT_MISMATCH"] and s["verification"]["expectation"] == "MISMATCH"
    assert f"post rows {ROWS_POST + 2} != declared {ROWS_POST}" in s["warning"] and "cannot be undone" in s["warning"]
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    gad.validate_receipt(rec)
    assert rec["expected_change"]["outcome"] == "MISMATCH" and rec["expected_change"]["post_row_count"] == ROWS_POST + 2
    assert rec["post_fingerprint"]["composite"] == POST_SHA and rec["committed"] is True


def test_a_post_fingerprint_that_differs_from_the_declared_one_is_exit_11(env):
    other = _hex("some other content")
    code, ev, *_ = commit_expected(env, write_spec(env), fp=FakeFpRows((PRE_SHA, other), (ROWS_PRE, ROWS_POST)))
    s = last(ev)
    assert code == 11 and s["verification"]["codes"] == ["EXPECTED_FINGERPRINT_MISMATCH"] and other in s["warning"]
    pathlib.Path(env["receipt"]).unlink()
    both = commit_expected(env, write_spec(env, "c.json"), fp=FakeFpRows((PRE_SHA, other), (ROWS_PRE, ROWS_POST + 1)))
    assert both[0] == 11 and last(both[1])["verification"]["codes"] == ["EXPECTED_ROW_COUNT_MISMATCH", "EXPECTED_FINGERPRINT_MISMATCH"]


def test_skip_no_delta_stays_exit_8_and_outranks_the_expectation_in_expected_change_mode(env):
    code, ev, db, disp, token = commit_expected(env, write_spec(env), db=FakeDB(dispositions={ASSET: "skip_no_delta"}),
                                                fp=FakeFpRows((PRE_SHA, PRE_SHA), (ROWS_PRE, ROWS_PRE)))
    s = last(ev)
    assert code == gad.EXIT_FORCE_NOT_EFFECTIVE == 8 and s["second_dispatch"] == "FORBIDDEN" and "FORCE_DID_NOT_TAKE_EFFECT" in s["verification"]["codes"]
    assert s["verification"]["expectation"] in ("MISMATCH",) and len(disp.calls) == 1


@pytest.mark.parametrize("states", [["running", "running", "running"], ["failed"]])
def test_an_unfinished_or_failed_run_establishes_nothing_exit_10_outcome_null_never_a_pass(env, states):
    path = write_spec(env)
    code, ev = run(env, xargs(env, path), db=FakeDB(), fp=FakeFpRows((PRE_SHA,), (ROWS_PRE,)))
    token = last(ev)["confirm_token"]
    db, clock = FakeDB(), itertools.count(0, 6000)
    orig = db.respond

    def respond(sql, params):
        if "SELECT state, last_error FROM build_runs WHERE id" in sql:
            return [{"state": states[-1], "last_error": "boom"}]
        return orig(sql, params)
    db.respond = respond
    code, ev = run(env, xargs(env, path, "--run-timeout-seconds", "100", commit=True, confirm=token), db=db, fp=FakeFpRows((PRE_SHA, POST_SHA), (ROWS_PRE, ROWS_POST)),
                   dispatch=Dispatch(), monotonic=lambda: next(clock))
    s = last(ev)
    assert code == gad.EXIT_VERIFY_FAILED and "RUN_NOT_COMPLETED" in s["verification"]["codes"] and s["verification"]["expectation"] is None
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    gad.validate_receipt(rec)
    assert rec["expected_change"]["outcome"] is None and rec["expected_change"]["post_row_count"] is None and rec["post_fingerprint"] is None


def test_a_wrong_token_or_a_swapped_expected_change_file_is_refused_and_nothing_is_inserted(env):
    path = write_spec(env)
    code, ev = run(env, xargs(env, path), fp=FakeFpRows((PRE_SHA,), (ROWS_PRE,)))
    token = last(ev)["confirm_token"]
    swapped = write_spec(env, "swapped.json", expected_post_row_count=ROWS_POST + 5)
    db = FakeDB()
    code, ev = run(env, xargs(env, swapped, commit=True, confirm=token), db=db, fp=FakeFpRows((PRE_SHA,), (ROWS_PRE,)))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["CONFIRM_TOKEN_MISMATCH"] and db.inserts("build_runs") == []
    code, ev = run(env, argv_for(env, commit=True, confirm=token), db=FakeDB(), fp=FakeFp((PRE_SHA,)))          # the declaration dropped: the unchanged-content token is another token
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["CONFIRM_TOKEN_MISMATCH"]


def test_the_default_mode_still_refuses_a_changed_fingerprint_with_exit_9(env):
    code, ev, *_ = commit_run(env, fp=FakeFp((PRE_SHA, POST_SHA)))
    assert code == gad.EXIT_FINGERPRINT_CHANGED == 9 and "expectation" not in last(ev)["verification"] and "row_counts" not in last(ev)["verification"]


# ── verify-run in expected-change mode, and the receipt schema ──

def test_verify_run_grades_the_receipts_declaration_and_needs_the_same_file(env):
    path = write_spec(env)
    code, ev, db, disp, token = commit_expected(env, path, fp=FakeFpRows((PRE_SHA, POST_SHA), (ROWS_PRE, ROWS_POST)))
    assert code == 0
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "completed", "triggered_by": rec["triggered_by"], "plan_manifest_digest": rec["manifest_digest"]}
    base = ["--assets", ASSET, "--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"], "--verify-run", rec["run_id"]]
    good = gad.build_parser().parse_args(base + ["--expected-change", path])
    db2, disp2 = FakeDB(run_row=run_row), Dispatch()
    code, ev = run(env, good, db=db2, fp=FakeFpRows((POST_SHA,), (ROWS_POST,)), dispatch=disp2)
    assert code == 0 and last(ev)["verification"]["expectation"] == "MET" and db2.inserts("build_runs") == [] and disp2.calls == []
    code, ev = run(env, good, db=FakeDB(run_row=run_row), fp=FakeFpRows((POST_SHA,), (ROWS_POST + 1,)))
    assert code == 11 and last(ev)["verification"]["codes"] == ["EXPECTED_ROW_COUNT_MISMATCH"]
    other = write_spec(env, "other.json", expected_post_row_count=ROWS_POST + 9)
    for argv in (base, base + ["--expected-change", other]):
        code, ev = run(env, gad.build_parser().parse_args(argv), db=FakeDB(run_row=run_row), fp=FakeFpRows((POST_SHA,), (ROWS_POST,)))
        assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_EXPECTED_CHANGE_MISMATCH"]


def test_verify_run_of_an_unchanged_mode_receipt_refuses_an_expected_change_file(env):
    code, ev, db, disp, token = commit_run(env)
    assert code == 0
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "completed", "triggered_by": rec["triggered_by"], "plan_manifest_digest": rec["manifest_digest"]}
    args = gad.build_parser().parse_args(["--assets", ASSET, "--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"], "--verify-run", rec["run_id"],
                                          "--expected-change", write_spec(env)])
    code, ev = run(env, args, db=FakeDB(run_row=run_row), fp=FakeFp((PRE_SHA,)))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_EXPECTED_CHANGE_MISMATCH"]


def test_the_receipt_schema_accepts_a_pre_expected_change_receipt_and_refuses_a_malformed_block(env):
    rec = _valid_receipt(env)
    old = {k: v for k, v in rec.items() if k != "expected_change"}
    gad.validate_receipt(old)                                                 # a receipt written before the mode existed stays valid
    good = dict(rec, expected_change={"file_sha256": _hex("f"), "spec": _spec(), "accepted_changed_output": True, "pre_row_count": 8, "post_row_count": None, "outcome": None})
    gad.validate_receipt(good)
    for bad_block in ({"file_sha256": _hex("f")}, {**good["expected_change"], "accepted_changed_output": False}, {**good["expected_change"], "outcome": "maybe"},
                      {**good["expected_change"], "file_sha256": "abc"}, {**good["expected_change"], "pre_row_count": True},
                      {**good["expected_change"], "spec": _spec(asset="bg_other")}, "x"):
        with pytest.raises(slw.LevelWaveError):
            gad.validate_receipt(dict(rec, expected_change=bad_block))


def test_the_cli_has_the_two_new_flags_and_still_no_force_flag():
    opts = {o for a in gad.build_parser()._actions for o in a.option_strings}
    assert {"--expected-change", "--accept-changed-output"} <= opts and "--force-execute" not in opts


# ── review fixes: receipt shape, the file reader, verify grades the file, outcome semantics, multi-table totals ──

def test_the_default_receipt_has_exactly_the_keys_and_verification_it_always_had(env):
    code, ev, db, disp, token = commit_run(env)
    assert code == 0
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert "expected_change" not in rec and set(rec) == set(gad.RECEIPT_KEYS) - {"expected_change"}
    assert set(rec["verification"]) == {"verdict", "run_state", "wait", "disposition", "duration_seconds", "fingerprint_equal", "codes", "notes"}
    assert "expected_change" not in gad.new_receipt(asset=ASSET) and "expected_change" in gad.new_receipt(asset=ASSET, expected_change={"x": 1})


def test_a_symlink_to_a_good_file_is_refused_even_when_its_own_name_is_innocent(env):
    real = write_spec(env, "real.json")
    link = env["tmp"] / "innocent.json"
    link.symlink_to(real)
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.load_expected_change(str(link), ASSET)
    assert "symbolic link" in exc.value.refusals[0]["detail"]
    envfile = env["tmp"] / ".env.json"
    envfile.write_text(json.dumps(_spec()))
    ok_name = env["tmp"] / "plain.json"
    ok_name.symlink_to(envfile)
    with pytest.raises(slw.LevelWaveRefusal):
        gad.load_expected_change(str(ok_name), ASSET)


def test_an_ordinary_path_through_a_real_directory_still_reads(env):
    real_dir = env["tmp"] / "plain_dir"
    real_dir.mkdir()
    spec_file = real_dir / "spec.json"
    spec_file.write_text(json.dumps(_spec()))
    assert gad.load_expected_change(str(spec_file), ASSET)[0]["asset"] == ASSET


def test_a_relative_path_is_read_relative_to_the_working_directory(env, monkeypatch):
    write_spec(env, "rel.json")
    monkeypatch.chdir(env["tmp"])
    spec, sha = gad.load_expected_change("rel.json", ASSET)
    assert spec["asset"] == ASSET and len(sha) == 64
    spec2, _ = gad.load_expected_change("./rel.json", ASSET)
    assert spec2 == spec
    with pytest.raises(slw.LevelWaveRefusal):
        gad.load_expected_change("nothere.json", ASSET)


def test_the_reader_reads_at_most_the_cap_plus_one_byte_and_a_duplicate_key_is_not_echoed(env, monkeypatch):
    reads = []
    real_read = os.read
    monkeypatch.setattr(os, "read", lambda fd, n: (reads.append(n), real_read(fd, n))[1])
    big = env["tmp"] / "big.json"
    big.write_bytes(b" " * (gad.EXPECTED_CHANGE_MAX_BYTES * 4))
    with pytest.raises(slw.LevelWaveRefusal, match="larger than"):
        gad.load_expected_change(str(big), ASSET)
    assert reads and all(n <= gad.EXPECTED_CHANGE_MAX_BYTES + 1 for n in reads) and sum(reads) <= gad.EXPECTED_CHANGE_MAX_BYTES + 1 + 1
    dup = env["tmp"] / "dup.json"
    dup.write_text('{"asset": "x", "SECRET_LOOKING_KEY": 1, "SECRET_LOOKING_KEY": 2}')
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.load_expected_change(str(dup), ASSET)
    assert "duplicate key" in exc.value.refusals[0]["detail"] and "SECRET_LOOKING_KEY" not in exc.value.refusals[0]["detail"]


@pytest.mark.parametrize("field", ["why", "evidence"])
def test_why_and_evidence_are_capped_at_500_characters(env, field):
    long = "a real sentence about the change " * 20
    assert len(long) > 500
    with pytest.raises(slw.LevelWaveRefusal, match="longer than 500"):
        gad.load_expected_change(write_spec(env, **{field: long.strip()}), ASSET)
    gad.load_expected_change(write_spec(env, "ok.json", **{field: ("a real sentence about the change " * 14).strip()}), ASSET)


def test_verify_run_grades_the_file_and_refuses_a_receipt_whose_recorded_spec_differs_from_it(env):
    path = write_spec(env)
    code, ev, db, disp, token = commit_expected(env, path, fp=FakeFpRows((PRE_SHA, POST_SHA), (ROWS_PRE, ROWS_POST)))
    assert code == 0
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    spec, sha = gad.load_expected_change(path, ASSET)
    assert rec["expected_change"]["spec"] == spec and rec["expected_change"]["file_sha256"] == sha
    rec["expected_change"]["spec"] = dict(spec, expected_post_row_count=ROWS_POST + 3)         # a doctored receipt: digest of the file matches, the recorded spec does not
    pathlib.Path(env["receipt"]).write_text(json.dumps(rec))
    run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "completed", "triggered_by": rec["triggered_by"], "plan_manifest_digest": rec["manifest_digest"]}
    args = gad.build_parser().parse_args(["--assets", ASSET, "--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"], "--verify-run", rec["run_id"],
                                          "--expected-change", path])
    code, ev = run(env, args, db=FakeDB(run_row=run_row), fp=FakeFpRows((POST_SHA,), (ROWS_POST + 3,)))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_EXPECTED_CHANGE_MISMATCH"]


def test_the_outcome_is_met_only_when_the_whole_verification_passed(env):
    bad_record = [{"state": "lit", "last_built_at": T0 + timedelta(seconds=40), "duration_seconds": None}]          # the build record carries no duration
    code, ev, *_ = commit_expected(env, write_spec(env), db=FakeDB(global_record=bad_record), fp=FakeFpRows((PRE_SHA, POST_SHA), (ROWS_PRE, ROWS_POST)))
    s = last(ev)
    assert code == gad.EXIT_VERIFY_FAILED and s["verification"]["expectation"] == "MET" and "BUILD_RECORD_NOT_DURATION_BEARING" in s["verification"]["codes"]
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert rec["expected_change"]["outcome"] is None and rec["expected_change"]["post_row_count"] == ROWS_POST         # the expectation held, the run did not verify: not MET


def test_the_unit_total_sums_every_table_and_the_expectation_is_compared_to_that_total(env):
    fp = {"tables": {"t1": {"sha256": PRE_SHA, "rows": 5}, "t2": {"sha256": PRE_SHA, "rows": 6}, "t3": {"sha256": PRE_SHA, "rows": 0}}}
    assert gad.unit_row_count(fp) == 11 and gad.unit_row_count({"tables": {}}) == 0

    def reader_for(rows_by_table, sha):
        def reader(conn, decls, units):
            return {"definition": fd.FINGERPRINT_DEFINITION, "declarations_sha256": "x" * 64, "fingerprints": {units[0]: sha},
                    "tables": {units[0]: {t: {"sha256": sha, "rows": r} for t, r in rows_by_table.items()}}, "projections": {}, "horizons": {}}
        return reader

    pre = gad.read_fingerprint(FakeFp().connect, DECLS, UNIT, reader=reader_for({"t1": 5, "t2": 3}, PRE_SHA))
    assert gad.unit_row_count(pre) == ROWS_PRE
    spec = _spec()
    fp = FakeFp()

    def verify(post_rows):
        return gad.verify_forced_run(FakeDB().connect, fp.connect, DECLS, run_id="33333333-3333-4333-8333-333333333333", asset=ASSET, unit=UNIT, pre=pre,
                                     wait={"state": "completed"}, reader=reader_for(post_rows, POST_SHA), expected=spec)
    ok = verify({"t1": 7, "t2": 4})                                              # 7 + 4 = the declared 11 across TWO tables
    assert ok["row_counts"] == {"pre": ROWS_PRE, "post": ROWS_POST, "expected_post": ROWS_POST} and ok["expectation"] == "MET" and ok["verdict"] == "PASS", ok
    off = verify({"t1": 7, "t2": 5})                                             # one table off by one: the total differs
    assert off["exit_code"] == 11 and off["codes"] == ["EXPECTED_ROW_COUNT_MISMATCH"] and off["expectation"] == "MISMATCH"


def test_a_fifo_named_like_a_spec_is_refused_without_blocking(env):
    import signal  # noqa: PLC0415
    fifo = env["tmp"] / "pipe.json"
    os.mkfifo(fifo)
    signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(AssertionError("the open blocked on a FIFO")))
    signal.alarm(5)
    try:
        with pytest.raises(slw.LevelWaveRefusal) as exc:
            gad.load_expected_change(str(fifo), ASSET)
    finally:
        signal.alarm(0)
    assert exc.value.refusals[0]["code"] == "EXPECTED_CHANGE_INVALID" and "regular file" in exc.value.refusals[0]["detail"]


def test_verify_run_names_what_differs(env):
    path = write_spec(env)
    code, ev, db, disp, token = commit_expected(env, path, fp=FakeFpRows((PRE_SHA, POST_SHA), (ROWS_PRE, ROWS_POST)))
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "completed", "triggered_by": rec["triggered_by"], "plan_manifest_digest": rec["manifest_digest"]}
    base = ["--assets", ASSET, "--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"], "--verify-run", rec["run_id"]]

    def detail(argv):
        code, ev = run(env, gad.build_parser().parse_args(argv), db=FakeDB(run_row=run_row), fp=FakeFpRows((POST_SHA,), (ROWS_POST,)))
        assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_EXPECTED_CHANGE_MISMATCH"]
        return last(ev)["refusals"][0]["detail"]
    assert "none was given" in detail(base)
    assert "file sha differs" in detail(base + ["--expected-change", write_spec(env, "o.json", expected_post_row_count=ROWS_POST + 9)])
    rec["expected_change"]["spec"] = dict(rec["expected_change"]["spec"], why="an altered but still valid reason text")
    pathlib.Path(env["receipt"]).write_text(json.dumps(rec))
    assert "recorded spec differs" in detail(base + ["--expected-change", path])


# ═════════════════════════ group members (non-seeded, deterministic groups) ═════════════════════════

GROUP_MEMBERS = {"bg_ontology": ("grp_brahma_ontology", "brahma_ontology"), "bg_class_priors": ("grp_brahma_class_priors", "brahma_class_priors"),
                 "bg_class_lifetime_counts": ("grp_brahma_class_priors", "brahma_class_priors")}


@pytest.mark.parametrize("asset", sorted(GROUP_MEMBERS))
def test_a_pure_member_of_a_deterministic_group_resolves_to_its_group_unit(asset):
    unit, table = GROUP_MEMBERS[asset]
    assert gad.declared_unit_or_refuse(DECLS, asset) == unit
    assert DECLS.tables(unit) == [table] and asset in DECLS.members(unit)


def test_a_seeded_group_member_and_a_partial_one_are_refused_with_every_reason():
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.declared_unit_or_refuse(DECLS, "bg_text_index")
    assert [r["code"] for r in exc.value.refusals] == ["GROUP_UNIT_SEEDED"]
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.declared_unit_or_refuse(DECLS, "bg_texts")
    assert [r["code"] for r in exc.value.refusals] == ["FINGERPRINT_COVERAGE_PARTIAL", "GROUP_UNIT_SEEDED"]


@pytest.mark.parametrize("asset", ["bg_doshas", "bg_yogas", "bg_dasha_systems"])
def test_a_mixed_member_fingerprints_its_own_tables_and_the_shared_group_table(asset):
    """SS ruling 1: bg_doshas / bg_yogas / bg_dasha_systems write brahma_ontology rows too; the unit includes that table."""
    assert gad.declared_unit_or_refuse(DECLS, asset) == f"{asset}+grp_brahma_ontology"
    assert set(gad.unit_siblings(DECLS, asset, f"{asset}+grp_brahma_ontology")) == {"bg_ontology", "bg_dasha_systems", "bg_doshas", "bg_yogas"} - {asset}


@pytest.mark.parametrize("asset", ["bg_ghatana", "bg_formula_constants", "bg_phaladeepika_latta"])
def test_an_asset_with_own_tables_and_no_group_keeps_its_plain_unit_id(asset):
    assert gad.declared_unit_or_refuse(DECLS, asset) == asset and gad.unit_siblings(DECLS, asset, asset) == []


@pytest.mark.parametrize("asset", ["bg_not_declared", "bg_transit_rules", "bg_compendium_index"])
def test_an_undeclared_asset_never_resolves_to_a_unit(asset):
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.declared_unit_or_refuse(DECLS, asset)
    assert exc.value.refusals[0]["code"] == "ASSET_NOT_DECLARED"


def test_a_shared_writer_run_fingerprints_every_table_it_touches():
    sibs = ["bg_nakshatra_medical", "bg_sign_medical"]
    unit = gad.declared_unit_or_refuse(DECLS, "bg_medical_mappings", sibs)
    assert unit == "bg_medical_mappings+bg_nakshatra_medical+bg_sign_medical"
    assert gad.unit_siblings(DECLS, "bg_medical_mappings", unit, sibs) == sibs
    # dispatching the sign-medical id runs the same class: the same three tables, the asset's own unit first
    assert gad.declared_unit_or_refuse(DECLS, "bg_sign_medical", ["bg_medical_mappings", "bg_nakshatra_medical"]) == "bg_sign_medical+bg_medical_mappings+bg_nakshatra_medical"


def test_a_sibling_that_is_not_a_declared_unit_refuses_the_run_naming_it():
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.declared_unit_or_refuse(DECLS, "bg_transit_engine", ["bg_transit_rules"])
    r = exc.value.refusals[0]
    assert r["code"] == "WRITER_SIBLING_NOT_DECLARED" and r["asset"] == "bg_transit_rules" and "migration_owned_rows" in r["detail"]
    with pytest.raises(slw.LevelWaveRefusal) as exc:                                   # a declared asset with a seeded / partial sibling reports every reason
        gad.declared_unit_or_refuse(DECLS, "bg_ghatana", ["bg_texts"])
    assert [r["code"] for r in exc.value.refusals] == ["FINGERPRINT_COVERAGE_PARTIAL", "GROUP_UNIT_SEEDED"]


# ── the writer scan ──

def _writers(env, **files):
    d = pathlib.Path(env["repo"]) / gad.WRITERS_REL
    for f in list(d.glob("*.py")):
        f.unlink()
    for name, body in files.items():
        (d / name).write_text(body)
    return env["repo"]


def test_stacked_register_decorators_on_one_class_are_siblings_and_two_classes_are_not(env):
    repo = _writers(env, **{"w.py": "@register('a')\n@register('b')\n@register('c')\nclass W:\n    pass\n", "v.py": "@register('x')\nclass A:\n    pass\n\n@register('y')\nclass B:\n    pass\n"})
    assert gad.writer_siblings(repo, "a") == ["b", "c"] and gad.writer_siblings(repo, "c") == ["a", "b"]
    assert gad.writer_siblings(repo, "x") == [] and gad.writer_siblings(repo, "y") == []


def test_the_scan_resolves_a_module_constant_and_the_real_shapes(env):
    repo = _writers(env, **{"w.py": "ID = 'a'\n@register(ID)\n@register(\"b\")\nclass W:\n    pass\n"})
    assert gad.writer_siblings(repo, "a") == ["b"]
    top = str(pathlib.Path(__file__).resolve().parents[4])
    if (pathlib.Path(top) / gad.WRITERS_REL).is_dir():                                      # the committed tree: the two shared classes and nothing else we depend on
        assert gad.writer_siblings(top, "bg_medical_mappings") == ["bg_nakshatra_medical", "bg_sign_medical"]
        assert gad.writer_siblings(top, "bg_transit_rules") == ["bg_transit_engine"] and gad.writer_siblings(top, "bg_phaladeepika_latta") == []
        assert gad.writer_siblings(top, "bg_vedha_malefic_scale") == []


def test_the_scan_refuses_what_it_cannot_establish(env):
    import shutil  # noqa: PLC0415
    repo = _writers(env, **{"w.py": "@register(WHICH)\nclass W:\n    pass\n"})
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.writer_siblings(repo, "a")
    assert exc.value.refusals[0]["code"] == "WRITER_SCAN_UNAVAILABLE" and "not a literal positional id" in exc.value.refusals[0]["detail"]
    repo = _writers(env, **{"bad.py": "def (:\n"})
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.writer_siblings(repo, "a")
    assert "cannot be parsed" in exc.value.refusals[0]["detail"]
    shutil.rmtree(pathlib.Path(env["repo"]) / gad.WRITERS_REL)
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.writer_siblings(env["repo"], "a")
    assert exc.value.refusals[0]["code"] == "WRITER_SCAN_UNAVAILABLE"


def test_an_asset_that_no_scanned_class_registers_fails_closed_never_to_its_own_unit(env):
    repo = _writers(env, **{"w.py": "@register('a')\nclass W:\n    pass\n"})
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.writer_siblings(repo, "nothing")
    r = exc.value.refusals[0]
    assert r["code"] == "WRITER_SCAN_UNAVAILABLE" and "no writer class" in r["detail"] and "registers nothing" in r["detail"]
    code, ev = run(env, argv_for(env, asset="bg_not_registered_anywhere"), db=FakeDB(candidates=[[row("bg_not_registered_anywhere", scope="global", target="t")]]))
    assert code != 0


@pytest.mark.parametrize("decorator", ["@register(asset_id='a')", "@register(*IDS)", "@register()", "@writers.register(some_call())", "@register(f'{X}')", "@register(ID_NOT_A_CONSTANT)"])
def test_every_register_form_the_scan_cannot_read_refuses_whatever_the_file_names(env, decorator):
    # the asset 'a' is NOT named anywhere in this file: the old `asset in text` shortcut would have let it through
    repo = _writers(env, **{"w.py": f"{decorator}\nclass W:\n    pass\n", "ok.py": "@register('a')\nclass K:\n    pass\n"})
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.writer_siblings(repo, "a")
    assert exc.value.refusals[0]["code"] == "WRITER_SCAN_UNAVAILABLE" and "w.py" in exc.value.refusals[0]["detail"]


def test_the_scan_is_recursive_and_skips_test_directories(env):
    repo = _writers(env, **{"top.py": "@register('a')\nclass A:\n    pass\n"})
    d = pathlib.Path(repo) / gad.WRITERS_REL
    (d / "ph_sub").mkdir(exist_ok=True)
    (d / "ph_sub" / "__init__.py").write_text("@register('b')\n@register('c')\nclass B:\n    pass\n")
    (d / "__tests__").mkdir()
    (d / "__tests__" / "test_x.py").write_text("@register('a')\n@register('zz_fake')\nclass T:\n    pass\n@register(UNRESOLVED)\nclass U:\n    pass\n")
    assert gad.writer_siblings(repo, "b") == ["c"] and gad.writer_siblings(repo, "c") == ["b"]            # a package's __init__.py is read
    assert gad.writer_siblings(repo, "a") == []                                                            # the test directory's fake sibling and unresolved decorator are not read


def test_the_committed_writers_tree_has_no_unreadable_register_form_and_registers_the_dispatchable_assets():
    top = str(pathlib.Path(__file__).resolve().parents[4])
    if not (pathlib.Path(top) / gad.WRITERS_REL).is_dir():
        pytest.skip("no writers tree in this checkout")
    for asset in ("bg_phaladeepika_latta", "bg_ontology", "bg_doshas", "bg_sign_medical", "bg_ghatana", "bg_remedies"):
        gad.writer_siblings(top, asset)                                                                    # does not raise: every register form in the tree is readable


def test_verify_run_refuses_when_the_checkouts_unit_differs_from_the_receipts(env):
    onto, git = _mixed_env(env)
    code, ev = run(env, argv_for(env, asset="bg_doshas"), db=FakeDB(candidates=[[onto]], downstream=()), fp=FakeFp((PRE_SHA,)), git=git)
    token = last(ev)["confirm_token"]
    db = FakeDB(candidates=[[onto]], downstream=(), dispositions={"bg_doshas": "build"})
    orig = db.respond
    db.respond = lambda sql, params: ([{"state": "lit", "last_built_at": db.ended, "duration_seconds": 5.0}] if "FROM asset_throughput WHERE asset_id = %s AND chart_id IS NULL" in sql else orig(sql, params))
    code, ev = run(env, argv_for(env, asset="bg_doshas", commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA, PRE_SHA)), git=git, dispatch=Dispatch())
    assert code == 0
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    rec["pre_fingerprint"]["unit"] = "bg_doshas"                                                              # the receipt was committed under another unit than this checkout computes
    pathlib.Path(env["receipt"]).write_text(json.dumps(rec))
    run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "completed", "triggered_by": rec["triggered_by"], "plan_manifest_digest": rec["manifest_digest"]}
    args = gad.build_parser().parse_args(["--assets", "bg_doshas", "--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"], "--verify-run", rec["run_id"]])
    code, ev = run(env, args, db=FakeDB(run_row=run_row), fp=FakeFp((PRE_SHA,)))
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["RECEIPT_UNIT_MISMATCH"] and "drift" in last(ev)["refusals"][0]["detail"]


# ── the composed unit end to end ──

def _mixed_env(env, asset="bg_doshas", **writer_files):
    digests = {**env["digests"], asset: _hex(asset)}
    (pathlib.Path(env["repo"]) / "platform/src/generated/nirmana-writer-digests.json").write_text(json.dumps({"version": 1, "writers": digests}))
    if writer_files:
        _writers(env, **writer_files)
    return row(asset, scope="global", layer="brahmagyan", target="reference_doshas"), FakeGit(deployed=digests)


def test_a_mixed_member_plans_over_both_units_with_a_composite_and_per_table_units(env):
    onto, git = _mixed_env(env)
    code, ev = run(env, argv_for(env, asset="bg_doshas"), db=FakeDB(candidates=[[onto]], downstream=()), fp=FakeFp((PRE_SHA,)), git=git)
    s = last(ev)
    assert code == 0, s
    pre = s["pre_fingerprint"]
    assert pre["unit"] == "bg_doshas+grp_brahma_ontology" and pre["units"] == ["bg_doshas", "grp_brahma_ontology"]
    assert pre["table_units"]["brahma_ontology"] == "grp_brahma_ontology" and pre["table_units"]["reference_doshas"] == "bg_doshas"
    assert pre["composite"] == gad.sha256_json({"schema": "suvarna-composed-unit/v1", "units": {"bg_doshas": PRE_SHA, "grp_brahma_ontology": PRE_SHA}})
    fu = s["fingerprint_unit"]
    assert fu["units"] == ["bg_doshas", "grp_brahma_ontology"] and "brahma_ontology" in fu["tables"] and "reference_doshas" in fu["tables"] and "bg_ontology" in fu["members"]
    assert "WHOLE of every such table" in fu["note"]
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    gad.validate_receipt(rec)
    assert rec["pre_fingerprint"]["unit"] == "bg_doshas+grp_brahma_ontology"


def test_a_change_confined_to_the_shared_table_is_caught_by_a_mixed_member(env):
    onto, git = _mixed_env(env)
    code, ev = run(env, argv_for(env, asset="bg_doshas"), db=FakeDB(candidates=[[onto]], downstream=()), fp=FakeFp((PRE_SHA,)), git=git)
    token = last(ev)["confirm_token"]
    db = FakeDB(candidates=[[onto]], downstream=(), dispositions={"bg_doshas": "build"})
    orig = db.respond
    db.respond = lambda sql, params: ([{"state": "lit", "last_built_at": db.ended, "duration_seconds": 5.0}] if "FROM asset_throughput WHERE asset_id = %s AND chart_id IS NULL" in sql else orig(sql, params))

    class SliceChange(FakeFp):
        def reader(self, conn, decls, units):
            out = super().reader(conn, decls, units)
            if self.calls >= 2:                                                  # the post read: only the shared group table differs
                out["fingerprints"]["grp_brahma_ontology"] = POST_SHA
                out["tables"]["grp_brahma_ontology"] = {t: {"sha256": POST_SHA, "rows": v["rows"]} for t, v in out["tables"]["grp_brahma_ontology"].items()}
            return out
    code, ev = run(env, argv_for(env, asset="bg_doshas", commit=True, confirm=token), db=db, fp=SliceChange((PRE_SHA,)), git=git, dispatch=Dispatch())
    assert code == gad.EXIT_FINGERPRINT_CHANGED and last(ev)["verification"]["codes"] == ["FINGERPRINT_CHANGED_ON_FORCED_REBUILD"]


def test_a_shared_writer_asset_is_planned_over_the_tables_of_every_sibling(env):
    shared = "@register('bg_sign_medical')\n@register('bg_nakshatra_medical')\n@register('bg_medical_mappings')\nclass W:\n    pass\n"
    onto, git = _mixed_env(env, asset="bg_medical_mappings", **{"bg_medical_mappings.py": shared})
    reg = [row(a, scope="global", layer="brahmagyan", target=a) for a in ("bg_sign_medical", "bg_nakshatra_medical")]
    code, ev = run(env, argv_for(env, asset="bg_medical_mappings"), db=FakeDB(candidates=[[onto]], downstream=(), registry=reg), fp=FakeFp((PRE_SHA,)), git=git)
    s = last(ev)
    assert code == 0, s
    assert s["pre_fingerprint"]["unit"] == "bg_medical_mappings+bg_nakshatra_medical+bg_sign_medical" and set(s["pre_fingerprint"]["tables"]) == {"bg_medical_mappings", "bg_nakshatra_medical", "bg_sign_medical"}
    assert s["fingerprint_unit"]["writer_siblings"] == ["bg_nakshatra_medical", "bg_sign_medical"]
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    assert {d["asset_id"]: d["relations"] for d in rec["impact"]["dependents"]} == {a: ["sibling_in_fingerprint_unit"] for a in ("bg_nakshatra_medical", "bg_sign_medical")}
    code, ev = run(env, argv_for(env, asset="bg_medical_mappings"), db=FakeDB(candidates=[[onto]], downstream=(), registry=reg, conflicts=[{"id": "r1", "chart_id": OTHER_CHART, "state": "running", "asset_id": "bg_sign_medical"}]),
                   fp=FakeFp((PRE_SHA,)), git=git)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["CONFLICTING_ACTIVE_RUN"]


def test_a_shared_writer_run_with_an_undeclared_sibling_is_refused_before_anything_is_inserted(env):
    shared = "@register('bg_transit_rules')\n@register('bg_transit_engine')\nclass W:\n    pass\n"
    onto, git = _mixed_env(env, asset="bg_transit_engine", **{"bg_transit_rules.py": shared})
    db = FakeDB(candidates=[[onto]], downstream=())
    code, ev = run(env, argv_for(env, asset="bg_transit_engine"), db=db, fp=FakeFp((PRE_SHA,)), git=git)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["WRITER_SIBLING_NOT_DECLARED"] and db.inserts("build_runs") == []


def test_verify_run_recomputes_the_composed_unit_from_the_checkout(env):
    onto, git = _mixed_env(env)
    code, ev = run(env, argv_for(env, asset="bg_doshas"), db=FakeDB(candidates=[[onto]], downstream=()), fp=FakeFp((PRE_SHA,)), git=git)
    token = last(ev)["confirm_token"]
    db = FakeDB(candidates=[[onto]], downstream=(), dispositions={"bg_doshas": "build"})
    orig = db.respond
    db.respond = lambda sql, params: ([{"state": "lit", "last_built_at": db.ended, "duration_seconds": 5.0}] if "FROM asset_throughput WHERE asset_id = %s AND chart_id IS NULL" in sql else orig(sql, params))
    code, ev = run(env, argv_for(env, asset="bg_doshas", commit=True, confirm=token), db=db, fp=FakeFp((PRE_SHA, PRE_SHA)), git=git, dispatch=Dispatch())
    assert code == 0, last(ev)
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    run_row = {"id": rec["run_id"], "chart_id": CHART, "state": "completed", "triggered_by": rec["triggered_by"], "plan_manifest_digest": rec["manifest_digest"]}
    args = gad.build_parser().parse_args(["--assets", "bg_doshas", "--anchor-chart", CHART, "--receipt", env["receipt"], "--repo", env["repo"], "--verify-run", rec["run_id"]])
    db2 = FakeDB(run_row=run_row, dispositions={"bg_doshas": "build"})
    orig2 = db2.respond
    db2.respond = lambda sql, params: ([{"state": "lit", "last_built_at": db2.ended, "duration_seconds": 5.0}] if "FROM asset_throughput WHERE asset_id = %s AND chart_id IS NULL" in sql else orig2(sql, params))
    code, ev = run(env, args, db=db2, fp=FakeFp((PRE_SHA,)))
    assert code == 0 and last(ev)["post_fingerprint"]["unit"] == "bg_doshas+grp_brahma_ontology"


def test_a_group_whose_declaration_is_not_deterministic_is_refused_for_its_members(monkeypatch):
    doc = json.loads(json.dumps(DECLS.doc))
    doc["groups"]["brahma_ontology"]["reproducibility"] = ["platform_bound"]
    d2 = fd.Declarations(doc=doc, sha256=DECLS.sha256, path=DECLS.path)
    with pytest.raises(slw.LevelWaveRefusal) as exc:
        gad.declared_unit_or_refuse(d2, "bg_ontology")
    assert exc.value.refusals[0]["code"] == "FINGERPRINT_NOT_DETERMINISTIC"


def test_a_group_member_plans_and_verifies_over_the_whole_shared_table(env):
    asset, (unit, table) = "bg_ontology", GROUP_MEMBERS["bg_ontology"]
    onto = row(asset, scope="global", layer="brahmagyan", target=table, part="entity_class, canonical_id")
    digests = {**env["digests"], asset: _hex(asset)}
    (pathlib.Path(env["repo"]) / "platform/src/generated/nirmana-writer-digests.json").write_text(json.dumps({"version": 1, "writers": digests}))
    git = FakeGit(deployed=digests)
    code, ev = run(env, argv_for(env, asset=asset), db=FakeDB(candidates=[[onto]]), fp=FakeFp((PRE_SHA,)), git=git)
    s = last(ev)
    assert code == 0, s
    assert s["pre_fingerprint"]["unit"] == unit and list(s["pre_fingerprint"]["tables"]) == [table]
    assert s["fingerprint_unit"]["unit"] == unit and asset in s["fingerprint_unit"]["members"] and "WHOLE of every such table" in s["fingerprint_unit"]["note"]
    token = s["confirm_token"]
    db2 = FakeDB(candidates=[[onto]], dispositions={asset: "build"})
    orig2 = db2.respond
    db2.respond = lambda sql, params: ([{"state": "lit", "last_built_at": db2.ended, "duration_seconds": 12.0}] if "FROM asset_throughput WHERE asset_id = %s AND chart_id IS NULL" in sql
                                       else orig2(sql, params))
    code, ev = run(env, argv_for(env, asset=asset, commit=True, confirm=token), db=db2, fp=FakeFp((PRE_SHA, POST_SHA)), git=git, dispatch=Dispatch())
    assert code == gad.EXIT_FINGERPRINT_CHANGED and last(ev)["verification"]["codes"] == ["FINGERPRINT_CHANGED_ON_FORCED_REBUILD"]       # another member's slice changing is caught too


# ── group siblings: listed in the impact, their lit rows need acceptance, a concurrent run of one refuses ──

def _onto(env):
    asset, table = "bg_ontology", "brahma_ontology"
    onto = row(asset, scope="global", layer="brahmagyan", target=table, part="entity_class, canonical_id")
    digests = {**env["digests"], asset: _hex(asset)}
    (pathlib.Path(env["repo"]) / "platform/src/generated/nirmana-writer-digests.json").write_text(json.dumps({"version": 1, "writers": digests}))
    return asset, onto, FakeGit(deployed=digests)


def test_the_siblings_of_a_group_unit_are_listed_in_the_impact_with_their_relation(env):
    asset, onto, git = _onto(env)
    assert gad.unit_siblings(DECLS, asset, "grp_brahma_ontology") == ["bg_dasha_systems", "bg_doshas", "bg_yogas"]
    assert gad.unit_siblings(DECLS, ASSET, ASSET) == []
    reg = [row(a, scope="global", layer="brahmagyan", target="brahma_ontology") for a in ("bg_dasha_systems", "bg_doshas", "bg_yogas")]
    code, ev = run(env, argv_for(env, asset=asset), db=FakeDB(candidates=[[onto]], downstream=(), registry=reg), fp=FakeFp((PRE_SHA,)), git=git)
    s = last(ev)
    assert code == 0, s
    rec = json.loads(pathlib.Path(env["receipt"]).read_text())
    deps = {d["asset_id"]: d["relations"] for d in rec["impact"]["dependents"]}
    assert deps == {a: ["sibling_in_fingerprint_unit"] for a in ("bg_dasha_systems", "bg_doshas", "bg_yogas")}
    assert s["impact_summary"]["dependents"] == 3


def test_a_lit_row_of_a_sibling_needs_its_own_acceptance(env):
    asset, onto, git = _onto(env)
    sib = {"asset_id": "bg_doshas", "chart_id": None, "state": "lit", "last_built_at": T0, "freshness_state": "fresh"}
    db = FakeDB(candidates=[[onto]], downstream=(), throughput=[sib])
    code, ev = run(env, argv_for(env, asset=asset), db=db, fp=FakeFp((PRE_SHA,)), git=git)
    assert code == slw.REFUSAL_EXIT_CODE and last(ev)["refusals"][0]["rows"] == ["bg_doshas@global"] and db.inserts("build_runs") == []
    code, ev = run(env, argv_for(env, "--accept-lit-dependent", "bg_doshas@global", asset=asset), db=FakeDB(candidates=[[onto]], downstream=(), throughput=[sib]),
                   fp=FakeFp((PRE_SHA,)), git=git)
    assert code == 0


def test_a_concurrent_run_of_a_sibling_is_looked_for_by_id_and_refuses(env):
    asset, onto, git = _onto(env)
    conflict = {"id": "r9", "chart_id": OTHER_CHART, "state": "running", "asset_id": "bg_yogas"}
    db = FakeDB(candidates=[[onto]], downstream=(), conflicts=[conflict])
    code, ev = run(env, argv_for(env, asset=asset), db=db, fp=FakeFp((PRE_SHA,)), git=git)
    assert code == slw.REFUSAL_EXIT_CODE and codes_of(ev) == ["CONFLICTING_ACTIVE_RUN"] and db.inserts("build_runs") == []
    q = [e for e in db.statements() if "bra.asset_id = ANY(%s)" in e[1]]
    assert q and set(q[0][2][0]) == {"bg_ontology", "bg_dasha_systems", "bg_doshas", "bg_yogas"}      # the siblings are in the ids the conflict query is run for
