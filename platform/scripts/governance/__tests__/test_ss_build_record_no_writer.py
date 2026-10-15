"""test_ss_build_record_no_writer.py -- SS 2026-10-05 (build_record no-writer/static): Earn.build_record reads N/A ONLY for an asset that declares `has_writer: false`
AND whose registry row and @register scan agree, with a build_run_assets history that holds no build; a build attempt contradicts the declaration (FAIL); an asset WITH a writer and
no duration-bearing build record stays NO_DETECTOR (closes by a rebuild). Offline, pure functions plus the rollup."""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

NA, FAIL, ND = ac.NA, ac.FAIL, ac.NO_DET
CRIT = "Earn.build_record"
RAW = dict(v=NA, cause="never-attempted", measured="never attempted -- see Build.exercised")
OK = dict(declared=True, registry_has_writer=False, register_files=0, register_mentions=[])


REG = 1000.0                                  # the registry row's current definition (epoch); an attempt created after it is NEWER, at or before it LEGACY (SS R-c)


ERA = 100.0                                    # the disposition era: the first attempt the engine marked disposition='build'


def att(disp, state="complete", run="abcdef0123", ep=2000.0, receipt=False):
    return dict(run_id=run, state=state, disposition=disp, when="2026-09-07", created_epoch=ep, receipt=receipt)


def test_the_rule_row_the_cause_and_the_guard_are_registered():
    assert "no-writer-registry-agrees" in ac.NA_CAUSES[CRIT]
    assert ac.NA_RULE_DECISIONS[f"{CRIT}#measured:no-writer-registry-agrees"].startswith("SS 2026-10-05 build_record no-writer/static")
    assert ac.NO_WRITER_CAUSES[CRIT] == ("no-writer-registry-agrees", "declared-probe-runs-verified")      # + SS probe_attempts
    assert ac.CRITERION_REGISTRY[CRIT]["revision"] == 3 and "SS 2026-10-05" in ac.CRITERION_REGISTRY[CRIT]["applicability"]      # +1 at SS R-c
    for cause in ("never-attempted", "healthy-non-execution", "before-completion-write"):          # the old causes stay un-ruled: a writer asset with no duration stays NO_DETECTOR
        assert f"{CRIT}#measured:{cause}" not in ac.NA_RULE_DECISIONS


@pytest.mark.parametrize("by_chart", [{}, None, {"c": att("probe_green")}, {"c": att("skip_no_delta")}, {"a": att("probe_green"), "b": att("skip_no_delta")}])
def test_an_agreeing_no_writer_asset_with_no_build_reads_na(by_chart):
    got = ac.earn_build_record_no_writer(dict(RAW), by_chart, dict(OK))
    assert got["v"] == NA and got["cause"] == "no-writer-registry-agrees" and got["no_writer"] == OK, got


@pytest.mark.parametrize("disp,state", [("build", "complete"), ("build", "error"), ("build", "aborted")])
def test_a_build_attempt_contradicts_the_declaration_and_reads_fail(disp, state):
    got = ac.earn_build_record_no_writer(dict(RAW), {"c": att(disp, state)}, dict(OK), REG, None, None, ERA)
    assert got["v"] == FAIL and "contradicted" in got["measured"] and got["no_writer"]["attempts"] == 1, got


def test_one_build_among_probes_is_enough_to_contradict():
    got = ac.earn_build_record_no_writer(dict(RAW), {"a": att("probe_green"), "b": att("build", run="1234567890")}, dict(OK), REG, None, None, ERA)
    assert got["v"] == FAIL and got["no_writer"]["attempts"] == 1


@pytest.mark.parametrize("mut", [dict(declared=False), dict(registry_has_writer=True), dict(register_files=1), dict(register_mentions=["x.py"]), dict(declared=None)])
def test_without_all_four_agreeing_facts_the_record_is_returned_unchanged(mut):
    block = dict(OK, **mut)
    assert ac.earn_build_record_no_writer(dict(RAW), {}, block) == RAW
    assert ac.earn_build_record_no_writer(dict(RAW), {"c": att("build")}, block, REG) == RAW        # and no FAIL either: an undeclared asset is not judged by the declaration


def test_the_rollup_releases_only_the_record_that_carries_the_agreeing_block():
    good = ac.earn_build_record_no_writer(dict(RAW), {}, dict(OK))
    assert ac.rollup_asset("L0", {CRIT: good})["Earn"]["checks"][0]["v"] == NA
    forged = dict(good, no_writer=dict(OK, register_files=1))
    assert ac.rollup_asset("L0", {CRIT: forged})["Earn"]["checks"][0]["v"] == ND
    assert ac.no_writer_na_problem(CRIT, dict(good, no_writer=None))
    assert ac.rollup_asset("L0", {CRIT: dict(good, no_writer=None)})["Earn"]["checks"][0]["v"] == ND
    bare = ac.rollup_asset("L0", {CRIT: dict(RAW)})["Earn"]["checks"][0]               # the old measured N/A (never-attempted): no ruled rule, so NO_DETECTOR
    assert bare["v"] == ND


def test_an_asset_with_a_writer_never_reads_na_through_the_old_causes():
    for cause in ("healthy-non-execution", "never-attempted", "before-completion-write", "no-registered-writer"):
        rec = dict(v=NA, cause=cause, measured="m")
        assert ac.rollup_asset("L0", {CRIT: rec})["Earn"]["checks"][0]["v"] == ND, cause


def test_the_declared_assets_among_the_saved_rev25_cells_are_the_four_has_writer_false_assets():
    # test id kept, now THREE (name is historical): bg_sarvatobhadra_grid was retired (migration 1360) and its declaration dropped at declarations rev28b, so it is no longer declared has_writer:false.
    decl = ac.load_asset_declarations()
    assert sorted(a for a, e in decl.items() if e.get("has_writer") is False) == ["bg_ephemeris_engine", "bg_gochara_citation_resolution", "bg_panchanga"]
    assert "bg_sarvatobhadra_grid" not in decl


# ───────────── SS R-c: legacy attempts older than the registry row's current definition do not contradict the declaration ─────────────

def test_rc_a_build_attempt_older_than_the_registry_definition_does_not_contradict_it():
    got = ac.earn_build_record_no_writer(dict(RAW), {"c": att(None, ep=500.0, run="0a0b0c0d0e")}, dict(OK), REG)
    assert got["v"] == NA and got["cause"] == "no-writer-registry-agrees", got
    assert "legacy attempt" in got["measured"] and "0a0b0c0d" in got["measured"] and "OLDER" in got["measured"] and got["no_writer"]["legacy_attempts"] == 1, got


def test_rc_an_attempt_exactly_at_the_definition_is_legacy_and_one_instant_later_is_newer():
    assert ac.earn_build_record_no_writer(dict(RAW), {"c": att("build", ep=REG)}, dict(OK), REG)["v"] == NA
    assert ac.earn_build_record_no_writer(dict(RAW), {"c": att("build", ep=REG + 0.001)}, dict(OK), REG)["v"] == FAIL


def test_rc_one_newer_attempt_among_legacy_ones_contradicts():
    got = ac.earn_build_record_no_writer(dict(RAW), {"a": att(None, ep=100.0, run="aaaaaaaaaa"), "b": att("build", ep=5000.0, run="bbbbbbbbbb")}, dict(OK), REG)
    assert got["v"] == FAIL and got["no_writer"]["attempts"] == 1 and "bbbbbbbb" in got["measured"] and "aaaaaaaa" not in got["measured"], got


def test_rc_an_unreadable_definition_date_places_nothing_and_reads_no_detector_never_fail_or_na():
    got = ac.earn_build_record_no_writer(dict(RAW), {"c": att(None, ep=500.0)}, dict(OK), None, "no main ref")
    assert got["v"] == ND and "no main ref" in got["measured"] and "neither a release nor a contradiction" in got["measured"], got
    undated = ac.earn_build_record_no_writer(dict(RAW), {"c": att("build", ep=float("-inf"))}, dict(OK), REG)
    assert undated["v"] == ND, undated
    nonum = ac.earn_build_record_no_writer(dict(RAW), {"c": dict(att("build"), created_epoch=None)}, dict(OK), REG)
    assert nonum["v"] == ND, nonum


def test_rc_probes_and_skips_need_no_date_at_all():
    assert ac.earn_build_record_no_writer(dict(RAW), {"a": att("probe_green", ep=9e9), "b": att("skip_no_delta", ep=9e9)}, dict(OK), None)["v"] == NA


def test_rc_the_split_function():
    sp = ac.no_writer_attempt_split({"a": att(None, ep=1.0), "b": att("build", ep=2e3), "c": att("probe_green", ep=3e3), "d": att("build", ep=float("-inf")), "e": att("", ep=4e3)}, REG, ERA)
    assert [len(sp[k]) for k in ("legacy", "newer", "undated", "unclassified")] == [1, 1, 1, 1]
    assert ac.no_writer_attempt_split(None, REG) == dict(legacy=[], newer=[], undated=[], unclassified=[])


def test_rc_the_legacy_release_still_rolls_up_only_with_the_agreeing_block():
    good = ac.earn_build_record_no_writer(dict(RAW), {"c": att(None, ep=1.0)}, dict(OK), REG)
    assert ac.rollup_asset("L0", {CRIT: good})["Earn"]["checks"][0]["v"] == NA
    forged = dict(good, no_writer=dict(good["no_writer"], register_files=1))
    assert ac.rollup_asset("L0", {CRIT: forged})["Earn"]["checks"][0]["v"] == ND


# ───────────── measure() wiring: Earn.build_record and Build.exercised for a declared no-writer asset with an old attempt ─────────────

def _reg_row(aid="bg_svc"):
    return dict(asset_id=aid, has_writer=False, target_table=None, count_sql="", has_integrity=False, integrity_sql=None, depends_on=[], target_floor=None, catalog_status="CURRENT",
                asset_kind="service")


def _stub(monkeypatch, tmp_path, ep, reg_epoch, why=None, disp=None, extra=(), log_error=None, basis="migration set has_writer = false", receipt=False, era_epoch=None):
    aid = "bg_svc"
    h = dict(runs=1, error=0, aborted=0, complete=1, queued=0, skipped=0, blocked=0, scopes={"chart"}, last_state="complete", last_when="2026-08-27", last_disposition=disp or "",
             sample_error="", sample_blocked="", executed=1, executed_scopes={"chart"}, last_executed_when="2026-08-27", states={"complete": 1}, sample_error_when="")
    attempt = dict(run_id="abcdef0123456789", state="complete", disposition=disp or "", ended_epoch="", created_epoch=ep, when="2026-08-27", receipt=False)
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "registry", lambda k: ({aid: _reg_row(aid)}, dict(registry_total=1, active=1, excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(), cols={}, keys={}, views=set()))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: None for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={aid: h}, global_runs=0, global_with_layer=0, lit=set()))
    log = [dict(scope="chart", state="complete", disposition=disp or "", when="2026-08-27", error="", started=True, epoch=ep, receipt=receipt)] + [dict(scope="chart", state="complete", when="2026-10-01", error="", started=True, receipt=False, **e) for e in extra]

    def _log(prefix, ids=None):
        if log_error:
            raise ac.Unknown(log_error)
        return {aid: log}
    monkeypatch.setattr(ac, "build_attempt_log", _log)
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({aid: {"c": attempt}}, era_epoch))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {aid: []}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=0, full=[], never=list(c), note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {aid: {"kind": "service", "has_writer": False}})
    bw = ac._lint_module("build_window")
    monkeypatch.setattr(bw.WindowReader, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(bw.WindowReader, "has_writer_commit", lambda self, a: (_ for _ in ()).throw(bw.WindowUnknown(why)) if reg_epoch is None else (reg_epoch, "f" * 40, basis))
    monkeypatch.setattr(bw.WindowReader, "registry_commit", lambda self, a: (_ for _ in ()).throw(AssertionError("the Build.history window date must not date the no-writer definition")))
    monkeypatch.setattr(bw.WindowReader, "commit_epoch", lambda self, sha: 0)                    # the engine-deploy floor is far in the past for these synthetic epochs
    monkeypatch.setattr(bw, "compute_window", lambda reader, a, paths: dict(ok=False, reason="stub"))
    monkeypatch.setattr(ac, "_writer_code_paths", lambda a, f, h: ["x"])
    monkeypatch.setattr(ac, "register_call_mentions", lambda a: [])


def _cells(c):
    return next(a for a in c["assets"] if a["asset_id"] == "bg_svc")["measurements"]


def test_rc_measure_a_legacy_attempt_releases_earn_and_exercised(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, ep=500.0, reg_epoch=1000.0)
    m = _cells(ac.measure("L0"))
    assert m["Earn.build_record"]["v"] == NA and "legacy attempt" in m["Earn.build_record"]["measured"], m["Earn.build_record"]
    assert m["Build.exercised"]["v"] == NA and m["Build.exercised"]["cause"] == "legacy-attempts-no-writer" and "SS R-c" in m["Build.exercised"]["measured"], m["Build.exercised"]
    roll = ac.rollup_asset("L0", m)
    assert roll["Earn"]["checks"][0]["v"] == NA


def test_rc_measure_a_newer_attempt_is_a_contradiction_and_exercised_keeps_its_executed_reading(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, ep=5000.0, reg_epoch=1000.0, disp="build", era_epoch=100.0)
    m = _cells(ac.measure("L0"))
    assert m["Earn.build_record"]["v"] == FAIL and "NEWER" in m["Earn.build_record"]["measured"], m["Earn.build_record"]
    assert m["Build.exercised"]["v"] == ac.PASS, m["Build.exercised"]


def test_rc_measure_an_unreadable_definition_date_changes_nothing_for_exercised_and_reads_no_detector_for_earn(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, ep=500.0, reg_epoch=None, why="the repository is a shallow clone")
    m = _cells(ac.measure("L0"))
    assert m["Earn.build_record"]["v"] == ND and "shallow clone" in m["Earn.build_record"]["measured"], m["Earn.build_record"]
    assert m["Build.exercised"]["v"] == ac.PASS, m["Build.exercised"]


def test_rc_measure_a_probe_attempt_needs_no_date(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, ep=9e9, reg_epoch=None, why="unused", disp="probe_green")
    m = _cells(ac.measure("L0"))
    assert m["Earn.build_record"]["v"] == NA, m["Earn.build_record"]


# ───────────── review: EVERY attempt is read, and the definition is the has_writer set, not an unrelated touch ─────────────

def test_rc_a_real_newer_build_followed_by_a_later_probe_row_still_reads_fail(monkeypatch, tmp_path):
    """LOW 6: latest_attempts kept only the LATEST attempt per chart, so a newer build followed by a later probe_green row was invisible and read N/A."""
    _stub(monkeypatch, tmp_path, ep=500.0, reg_epoch=1000.0, extra=[dict(epoch=5000.0, disposition="build"), dict(epoch=6000.0, disposition="probe_green")])
    m = _cells(ac.measure("L0"))
    assert m["Earn.build_record"]["v"] == FAIL and "NEWER" in m["Earn.build_record"]["measured"], m["Earn.build_record"]
    _stub(monkeypatch, tmp_path, ep=500.0, reg_epoch=1000.0, extra=[dict(epoch=5000.0, disposition="build"), dict(epoch=6000.0, disposition="skip_no_delta")])
    assert _cells(ac.measure("L0"))["Earn.build_record"]["v"] == FAIL


def test_rc_probe_and_skip_rows_alone_after_the_definition_do_not_contradict(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, ep=500.0, reg_epoch=1000.0, extra=[dict(epoch=6000.0, disposition="probe_green"), dict(epoch=7000.0, disposition="skip_no_delta")])
    m = _cells(ac.measure("L0"))
    assert m["Earn.build_record"]["v"] == NA and "legacy attempt" in m["Earn.build_record"]["measured"], m["Earn.build_record"]


def test_rc_an_unreadable_attempt_log_is_no_detector_not_a_release(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, ep=500.0, reg_epoch=1000.0, log_error="psql down")
    m = _cells(ac.measure("L0"))
    assert m["Earn.build_record"]["v"] == ND and "psql down" in m["Earn.build_record"]["measured"], m["Earn.build_record"]


def test_rc_the_earn_function_reads_a_list_or_a_dict_and_names_an_unreadable_log():
    assert ac.earn_build_record_no_writer(dict(RAW), [att("build", ep=5000.0)], dict(OK), REG)["v"] == FAIL
    got = ac.earn_build_record_no_writer(dict(RAW), None, dict(OK), REG, None, "the timed attempt log could not be read (x)")
    assert got["v"] == ND and "could not be read" in got["measured"]
    assert ac.earn_build_record_no_writer(dict(RAW), [dict(att("build"), created_epoch=None, epoch=300.0)], dict(OK), REG)["v"] == NA      # `epoch` (the attempt-log key) is read too


# ───────────── the definition date: scratch repos (build_window.has_writer_commit / migration_commit) ─────────────

import os  # noqa: E402
import subprocess  # noqa: E402

import build_window as bw  # noqa: E402

T0 = 1_700_000_000
DAY = 86400
SEED = "platform/scripts/seed/asset_registry_seed.ts"


def _g(repo, *args, day=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    if day is not None:
        env["GIT_COMMITTER_DATE"] = env["GIT_AUTHOR_DATE"] = f"{T0 + day * DAY} +0000"
    p = subprocess.run(["git", "-c", "user.name=x", "-c", "user.email=x@x", "-c", "commit.gpgsign=false", *args], cwd=str(repo), env=env, capture_output=True, text=True)
    assert p.returncode == 0, (args, p.stderr)


def _c(repo, files, day):
    for rel, text in files.items():
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    _g(repo, "add", "-A")
    _g(repo, "commit", "-q", "-m", "c", day=day)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "r"
    r.mkdir()
    _g(r, "init", "-q", "-b", "main")
    return r


def _seed(has_writer="", extra=""):
    return ("export const ROWS = [\n  {\n    asset_id: 'bg_svc',\n    layer: 'brahmagyan',\n" + (f"    has_writer: {has_writer},\n" if has_writer else "") + extra + "  },\n]\n")


MIGW = "platform/migrations/100_svc_writerless.sql"
SETS_FALSE = "UPDATE asset_registry SET has_writer = false WHERE asset_id = 'bg_svc';\n"
SETS_TRUE = "UPDATE asset_registry SET has_writer = true WHERE asset_id = 'bg_svc';\n"
INS_FALSE = "INSERT INTO asset_registry (asset_id, layer, has_writer) VALUES ('bg_other', 'x', true), ('bg_svc', 'x', false);\n"
INS_TRUE = "INSERT INTO asset_registry (asset_id, layer, has_writer) VALUES ('bg_svc', 'x', true);\n"


def test_rb_the_reference_instant_is_the_migration_that_set_has_writer_false(repo):
    """R-c (b): the moment the asset BECAME writer-less = the commit date on main of the migration that set has_writer = false (a labelled proxy for the ledger's applied_at)."""
    _c(repo, {MIGW: SETS_FALSE}, 3)
    _c(repo, {MIGW: "-- comment\n" + SETS_FALSE}, 25)                  # a later unrelated touch of the file does not move it
    got = bw.WindowReader(repo).has_writer_commit("bg_svc")
    assert got and got[0] == T0 + 3 * DAY and got[2] == "migration set has_writer = false", got


def test_rb_an_insert_row_with_has_writer_false_counts_and_a_true_row_or_another_assets_row_does_not(repo):
    _c(repo, {MIGW: INS_FALSE}, 4)
    got = bw.WindowReader(repo).has_writer_commit("bg_svc")
    assert got and got[0] == T0 + 4 * DAY and got[2] == "migration set has_writer = false", got
    assert bw.WindowReader(repo).has_writer_commit("bg_other") is None or bw.WindowReader(repo).has_writer_commit("bg_other")[2] == "created writer-less"


def test_rb_a_migration_that_sets_has_writer_true_is_not_a_writerless_instant(repo):
    _c(repo, {MIGW: SETS_TRUE}, 3)
    got = bw.WindowReader(repo).has_writer_commit("bg_svc")
    assert got is None or got[2] == "created writer-less", got
    _c(repo, {"platform/migrations/101_b.sql": INS_TRUE}, 5)
    assert (bw.WindowReader(repo).has_writer_commit("bg_svc") or (0, "", "created writer-less"))[2] == "created writer-less"


def test_rb_the_newest_false_set_wins_over_an_older_one(repo):
    _c(repo, {"platform/migrations/100_a.sql": SETS_FALSE}, 2)
    _c(repo, {"platform/migrations/101_b.sql": SETS_TRUE}, 5)
    _c(repo, {"platform/migrations/102_c.sql": SETS_FALSE}, 9)
    got = bw.WindowReader(repo).has_writer_commit("bg_svc")
    assert got and got[0] == T0 + 9 * DAY and got[2] == "migration set has_writer = false", got


def test_rb_a_seed_has_writer_line_is_not_a_migration_and_does_not_set_it(repo):
    _c(repo, {SEED: _seed()}, 2)
    _c(repo, {SEED: _seed("false")}, 20)                                 # the seed row gains `has_writer: false` later: still not a migration
    got = bw.WindowReader(repo).has_writer_commit("bg_svc")
    assert got and got[0] == T0 + 2 * DAY and got[2] == "created writer-less", got


def test_rb_a_row_no_migration_ever_set_is_created_writerless_by_its_earliest_commit(repo):
    _c(repo, {SEED: _seed()}, 2)
    _c(repo, {SEED: _seed(extra="    english_name: 'x',\n")}, 30)
    got = bw.WindowReader(repo).has_writer_commit("bg_svc")
    assert got and got[0] == T0 + 2 * DAY and got[2] == "created writer-less", got


def test_rb_a_migration_insert_without_has_writer_is_dated_by_creation(repo):
    _c(repo, {"platform/migrations/100_own.sql": "INSERT INTO asset_registry (asset_id, layer) VALUES ('bg_svc', 'x');\n"}, 6)
    _c(repo, {"platform/migrations/101_more.sql": "UPDATE asset_registry SET layer = 'y' WHERE asset_id = 'bg_svc';\n"}, 40)
    got = bw.WindowReader(repo).has_writer_commit("bg_svc")
    assert got and got[0] == T0 + 6 * DAY and got[2] == "created writer-less", got


def test_rb_only_the_set_clause_assigns_has_writer():
    """Review LOW: `SET has_writer = true WHERE ... AND has_writer = false` is a WHERE predicate, not a set to false."""
    f = bw._sets_has_writer_false
    assert not f("UPDATE asset_registry SET has_writer = true WHERE asset_id = 'x' AND has_writer = false", "x")
    assert not f("UPDATE asset_registry SET layer = 'a' WHERE asset_id = 'x' AND has_writer = false", "x")
    assert not f("UPDATE asset_registry SET has_writer = true FROM t WHERE has_writer = false AND asset_id = 'x'", "x")
    assert f("UPDATE asset_registry SET layer = 'a', has_writer = false WHERE asset_id = 'x' AND has_writer = true", "x")
    assert f("UPDATE asset_registry SET has_writer = FALSE, layer = 'a' WHERE asset_id = 'x'", "x")
    assert f("UPDATE asset_registry SET has_writer = 'f'", "x")
    assert not f("UPDATE asset_registry SET note = 'has_writer = false' WHERE asset_id = 'x'", "x")


def test_rb_the_has_writer_split_helper_reads_the_forms():
    f = bw._sets_has_writer_false
    assert f("UPDATE asset_registry SET has_writer = false WHERE asset_id = 'x'", "x") and f("update public.asset_registry set has_writer=FALSE, layer='a' where asset_id='x'", "x")
    assert not f("UPDATE asset_registry SET has_writer = true WHERE asset_id = 'x'", "x")
    assert f("INSERT INTO asset_registry (asset_id, has_writer) VALUES ('x', false)", "x")
    assert f("INSERT INTO asset_registry (asset_id, layer, has_writer) VALUES ('a', 'l', true), ('x', 'l', false)", "x")
    assert not f("INSERT INTO asset_registry (asset_id, layer, has_writer) VALUES ('a', 'l', false), ('x', 'l', true)", "x")
    assert not f("INSERT INTO asset_registry (asset_id, layer) VALUES ('x', 'l')", "x")            # no has_writer column
    assert not f("INSERT INTO asset_registry VALUES ('x', false)", "x")                             # no column list: not mapped, never guessed


def test_rc_nothing_that_names_the_row_means_it_cannot_be_dated(repo):
    _c(repo, {"README.md": "x"}, 1)
    assert bw.WindowReader(repo).has_writer_commit("bg_svc") is None


# ───────────── R-c (b) at measure(): the evidence names the proxy; migration-set before / after the attempt; created writer-less ─────────────

def test_rb_measure_attempt_newer_than_the_migration_that_set_has_writer_false_fails_and_names_the_proxy(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, ep=5000.0, reg_epoch=1000.0, disp="build", era_epoch=100.0)
    c = _cells(ac.measure("L0"))["Earn.build_record"]
    assert c["v"] == FAIL and "PROXY for the migration ledger's applied_at" in c["measured"] and "NEWER" in c["measured"], c


def test_rb_measure_attempt_older_than_that_migration_is_legacy_na_and_names_the_proxy(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, ep=500.0, reg_epoch=1000.0)
    c = _cells(ac.measure("L0"))["Earn.build_record"]
    assert c["v"] == NA and "legacy attempt" in c["measured"] and "PROXY for the migration ledger's applied_at" in c["measured"], c


def test_rb_measure_never_set_created_writerless_with_a_later_attempt_is_a_real_contradiction_fail(monkeypatch, tmp_path):
    """bg_ephemeris_engine / bg_panchanga's shape: the row was created writer-less (no migration set it) and a build attempt exists later: FAIL is the correct reading (Exec fix list)."""
    _stub(monkeypatch, tmp_path, ep=5000.0, reg_epoch=1000.0, basis="created writer-less", disp="build", era_epoch=100.0)
    c = _cells(ac.measure("L0"))["Earn.build_record"]
    assert c["v"] == FAIL and "created writer-less" in c["measured"] and "never had a writer" in c["measured"], c
    # the pre-era 2026-08-27 rows of bg_ephemeris_engine / bg_panchanga carry no disposition: they cannot be classified, so NO_DETECTOR (SS checks them read-only), not FAIL
    _stub(monkeypatch, tmp_path, ep=5000.0, reg_epoch=1000.0, basis="created writer-less", disp="", era_epoch=9000.0)
    assert _cells(ac.measure("L0"))["Earn.build_record"]["v"] == ND


def test_rb_measure_equal_dates_are_legacy_and_a_missing_date_is_no_detector(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, ep=1000.0, reg_epoch=1000.0)
    assert _cells(ac.measure("L0"))["Earn.build_record"]["v"] == NA               # equal: not newer
    _stub(monkeypatch, tmp_path, ep=None, reg_epoch=1000.0)
    c = _cells(ac.measure("L0"))["Earn.build_record"]
    assert c["v"] == ND and "cannot be placed" in c["measured"], c                  # NULL attempt date
    _stub(monkeypatch, tmp_path, ep=500.0, reg_epoch=None, why="no migration statement or seed row names it")
    assert _cells(ac.measure("L0"))["Earn.build_record"]["v"] == ND                # NULL definition date


# ───────────── review: the engine's probe-green row (complete, NO disposition, a receipt) never contradicts has_writer: false ─────────────

def _earn(attempts, reg=REG, era=ERA):
    return ac.earn_build_record_no_writer(dict(RAW), attempts, dict(OK), reg, "why", None, era)


def test_an_engine_probe_row_newer_than_the_definition_does_not_fail():
    """_mark_probe_green writes state complete with NO disposition and a receipt: it is a probe, never a build."""
    got = _earn([att("", "complete", ep=5000.0, receipt=True)])
    assert got["v"] == NA, got
    assert _earn([att(None, "complete", ep=5000.0, receipt=True)])["v"] == NA


def test_a_real_build_row_newer_than_the_definition_fails():
    assert _earn([att("build", "complete", ep=5000.0)])["v"] == FAIL
    assert _earn([att("build", "complete", ep=5000.0, receipt=True)])["v"] == FAIL         # a build with a surviving receipt is still a build


def test_a_receipt_row_before_the_disposition_era_may_be_a_real_build_and_is_unclassified_not_a_probe_and_not_a_fail():
    got = _earn([att("", "complete", ep=50.0, receipt=True)], reg=10.0)                       # created before ERA, newer than the definition
    assert got["v"] == ND and "neither a probe" in got["measured"] and "neither a contradiction nor a release" in got["measured"], got


def test_a_complete_row_with_no_disposition_and_no_receipt_is_unclassified_when_newer_and_legacy_when_older():
    assert _earn([att("", "complete", ep=5000.0, receipt=False)])["v"] == ND
    assert _earn([att("", "complete", ep=500.0, receipt=False)])["v"] == NA                   # older than the definition: legacy either way


@pytest.mark.parametrize("state", ["error", "aborted", "building"])
def test_an_error_or_abort_with_no_disposition_is_unclassified_not_a_contradiction(state):
    assert _earn([att("", state, ep=5000.0)])["v"] == ND


def test_without_an_era_a_receipt_row_cannot_be_derived_as_a_probe():
    assert _earn([att("", "complete", ep=5000.0, receipt=True)], era=None)["v"] == ND


def test_a_real_build_beats_an_unclassified_row_and_a_probe_beside_a_build_does_not_hide_it():
    got = _earn([att("", "complete", ep=5000.0), att("build", ep=6000.0, run="b" * 10), att("", "complete", ep=7000.0, receipt=True, run="c" * 10)])
    assert got["v"] == FAIL and got["no_writer"]["attempts"] == 1, got


def test_attempt_kind_table():
    k = ac.attempt_kind
    assert k(att("probe_green"), ERA) == "probe" and k(att("skip_no_delta"), ERA) == "probe"
    assert k(att("build"), ERA) == "build" and k(att("build", "error"), ERA) == "build"
    assert k(att("", receipt=True, ep=ERA), ERA) == "probe" and k(att("", receipt=True, ep=ERA - 1), ERA) == "unclassified"
    assert k(att("", receipt=False), ERA) == "unclassified" and k(att("weird"), ERA) == "unclassified"
    assert k(dict(state="complete", disposition="", receipt=True, epoch=500.0), ERA) == "probe"          # the attempt-log key `epoch`


def test_measure_an_engine_probe_row_on_the_declared_no_writer_asset_is_not_a_contradiction(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, ep=5000.0, reg_epoch=1000.0, disp="", receipt=True, era_epoch=100.0)
    m = _cells(ac.measure("L0"))
    assert m["Earn.build_record"]["v"] == NA, m["Earn.build_record"]
    assert m["Build.exercised"]["v"] == ac.PASS, m["Build.exercised"]             # executed (a started probe): unchanged
    _stub(monkeypatch, tmp_path, ep=5000.0, reg_epoch=1000.0, disp="build", era_epoch=100.0)
    assert _cells(ac.measure("L0"))["Earn.build_record"]["v"] == FAIL


def test_rc_a_migration_that_only_mentions_the_id_does_not_date_it(repo):
    """Review MED 5 (kept): a comment, a SELECT or a grant naming the id is not a statement that sets or creates its row (ownership itself is now the static_data declaration, not a git reading)."""
    _c(repo, {"platform/migrations/100_note.sql": "-- bg_svc and asset_registry are discussed here\nSELECT asset_id FROM asset_registry WHERE asset_id = 'bg_svc';\nGRANT SELECT ON asset_registry TO r; -- bg_svc\n"}, 4)
    assert bw.WindowReader(repo).has_writer_commit("bg_svc") is None


def test_rc_a_migration_under_platform_supabase_migrations_dates_the_definition_too(repo):
    _c(repo, {"platform/supabase/migrations/100_old.sql": "UPDATE asset_registry SET has_writer = false WHERE asset_id = 'bg_svc';\n"}, 7)
    got = bw.WindowReader(repo).has_writer_commit("bg_svc")
    assert got and got[0] == T0 + 7 * DAY and got[2] == "migration set has_writer = false", got


def test_rc_file_at_main_reads_a_file_or_none(repo):
    _c(repo, {"platform/supabase/migrations/565_x.sql": "CREATE TABLE t (id int);\n"}, 1)
    r = bw.WindowReader(repo)
    assert r.file_at_main("platform/supabase/migrations/565_x.sql").startswith("CREATE TABLE") and r.file_at_main("platform/supabase/migrations/nope.sql") is None


# ───────────── review: the disposition ERA is anchored on the engine-deploy commit, not on min(created_at) alone ─────────────

class _Rd:
    def __init__(self, epoch=None, boom=False):
        self.epoch, self.boom = epoch, boom

    def commit_epoch(self, sha):
        if self.boom:
            raise OSError("git")
        return self.epoch


def test_era_is_the_later_of_the_first_started_build_attempt_and_the_deploy_commit():
    assert ac._disposition_era(5000.0, _Rd(1000)) == (5000.0, ac._disposition_era(5000.0, _Rd(1000))[1])
    assert ac._disposition_era(500.0, _Rd(1000))[0] == 1000.0                   # a long-lived run that began before the deploy cannot pull the era earlier than the deploy commit
    assert "ef9ee729e" in ac._disposition_era(500.0, _Rd(1000))[1] and "first to write disposition 'build'" in ac._disposition_era(500.0, _Rd(1000))[1]


@pytest.mark.parametrize("data,rd", [(None, _Rd(1000)), (5000.0, _Rd(None)), (5000.0, _Rd(boom=True))])
def test_era_is_unknown_when_a_part_is_unavailable_and_then_no_probe_is_derived(data, rd):
    era, why = ac._disposition_era(data, rd)
    assert era is None and "unknown" in why, (era, why)
    assert ac.attempt_kind(att("", receipt=True, ep=9e9), None) == "unclassified"                   # no era: a receipt row is never a probe
    assert ac.earn_build_record_no_writer(dict(RAW), [att("", ep=9e9, receipt=True)], dict(OK), REG, None, None, None)["v"] == ND


def test_the_era_constant_is_the_commit_that_first_wrote_disposition_build_and_is_dated_by_git():
    assert ac.DISPOSITION_ERA_COMMIT == "ef9ee729e749ada086c975aac501c78086f4f644"
    bw_ = ac._lint_module("build_window")
    got = bw_.WindowReader(ac.ROOT, env=ac._git_env(), ref="HEAD").commit_epoch(ac.DISPOSITION_ERA_COMMIT)
    assert got is None or got == 1788480576, got                                                     # None only in a checkout that does not hold it (shallow)


def test_the_era_data_query_uses_the_attempts_own_started_at(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: seen.append(sql) or [])
    monkeypatch.setattr(ac, "scalar", lambda sql: seen.append(sql) or "1788900000")
    ac.latest_attempts(["bg_x"])
    q = [x for x in seen if "disposition = 'build'" in x][0]
    assert "min(coalesce(a.started_at, r.created_at))" in q and "min(r.created_at)" not in q, q


def test_measure_a_receipt_row_in_the_gap_before_the_deploy_commit_is_not_a_probe(monkeypatch, tmp_path):
    """The review's false release: a long-lived run created before the deploy set era too early, so a dispositionless receipt-bearing REAL build in the gap read as a probe."""
    _stub(monkeypatch, tmp_path, ep=5000.0, reg_epoch=1000.0, disp="", receipt=True, era_epoch=100.0)
    cbw = ac._lint_module("build_window")
    monkeypatch.setattr(cbw.WindowReader, "commit_epoch", lambda self, sha: 9000)                    # the deploy floor is AFTER the row
    m = _cells(ac.measure("L0"))
    assert m["Earn.build_record"]["v"] == ND and "neither a probe" in m["Earn.build_record"]["measured"], m["Earn.build_record"]
    monkeypatch.setattr(cbw.WindowReader, "commit_epoch", lambda self, sha: 4000)                    # the floor is BEFORE the row: a probe again
    assert _cells(ac.measure("L0"))["Earn.build_record"]["v"] == NA
