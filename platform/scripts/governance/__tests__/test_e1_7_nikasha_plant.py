"""test_e1_7_nikasha_plant.py: Suvarna E1.7, the T1 plant harness (nikasha_plant.py).

Two layers, both earned (CLAUDE.md N.8: a signal must be able to read false):

  (A) PURE: the judging, the unplantable guard, the verdict, the run-record hash, the evidence shape and the plant list's own
      invariants. Every plant is run through a seeded-defect test: a plant that moves nothing, moves the wrong verdict, leaks to
      another asset, moves an undeclared cell of its own asset, or rests on a baseline that is not the one it assumes, is NOT reported
      detected / clean. No database.
  (B) REAL (a disposable PostgreSQL, SKIPPED only where no PostgreSQL binaries exist): the real inspector, as a subprocess, on the synthetic
      world. A no-op plant, a plant whose anchor does not exist, a plant that leaks into the pristine world, a plant with collateral and a
      mutated inspector each make the harness say so; and the whole suite detects every plant with no collateral, every plant restored, every
      required registry check covered or declared unplantable, and every mutant noticed.
"""
from __future__ import annotations

import copy
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import nikasha_plant as np_  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

CLOSED_REASONS = ("constant_verdict_no_per_asset_input", "reported_not_graded", "needs_external_service")   # nikasha_scorecard.UNPLANTABLE_REASONS


# ───────────────────────────── (A) pure ─────────────────────────────

def _asset_ids():
    return [a.aid for a in np_.ASSETS] + [np_.D1_AID]


def _clean(plant: np_.Plant) -> dict:
    """A synthetic clean census: every fixture asset reads PASS on every check the plants touch, the plant's own cell at its assumed base."""
    checks = {p.check for p in np_.PLANTS} | {c for p in np_.PLANTS for c, _ in p.also} | {c for p in np_.PLANTS for c in p.allow}
    cm = {aid: {c: "PASS" for c in checks} for aid in _asset_ids()}
    cm[plant.asset][plant.check] = plant.base
    return cm


def _planted(plant: np_.Plant, cm: dict) -> dict:
    """What a correct inspector reads after the plant: the target (and each `also`) cell at an expected verdict."""
    out = copy.deepcopy(cm)
    out[plant.asset][plant.check] = plant.expect[0]
    for c, exp in plant.also:
        out[plant.asset][c] = exp[0]
    return out


ALL = pytest.mark.parametrize("p", np_.PLANTS, ids=lambda p: p.id)


def test_every_plant_is_unique_and_well_formed():
    ids = [p.id for p in np_.PLANTS]
    assert len(ids) == len(set(ids)) and len(ids) >= 25
    for p in np_.PLANTS:
        assert p.expect and all(v in np_.FAILING for v in p.expect), p.id           # a plant must open a gap, never close one
        assert p.base not in p.expect, p.id                                          # the plant must move the cell
        assert p.asset in _asset_ids(), p.id
        for c, exp in p.also:
            assert exp and all(v in np_.FAILING for v in exp), (p.id, c)
        assert p.check not in p.allow and p.check not in dict(p.also), p.id


def test_the_plants_and_the_unplantable_declarations_cover_exactly_the_registry_required_checks():
    """A registry check added without a plant (or an unplantable declaration), or a plant for a check the registry no longer measures, fails here:
    T1 coverage cannot silently decay with a registry revision."""
    required = {c for c, e in ac.CRITERION_REGISTRY.items() if e.get("detector") == np_.MEASURE_DETECTOR}
    planted = {p.check for p in np_.PLANTS}
    assert planted | set(np_.UNPLANTABLE) == required, sorted(planted | set(np_.UNPLANTABLE) ^ required)
    assert not planted & set(np_.UNPLANTABLE)


def test_the_unplantable_reasons_are_in_the_scorecards_closed_list_and_say_what_is_true_of_the_check():
    assert set(np_.UNPLANTABLE.values()) <= set(CLOSED_REASONS)
    assert np_.UNPLANTABLE == {"Complete.width": "constant_verdict_no_per_asset_input", "Reach.fields": "reported_not_graded"}


@ALL
def test_judge_a_plant_that_moves_nothing_is_not_detected(p):                       # seeded defect 1: the plant did nothing
    base = _clean(p)
    rec = np_.judge(p, base, copy.deepcopy(base))
    assert rec["detected"] is False and rec["collateral"] == [] and rec["error"] is None


@ALL
def test_judge_the_expected_move_is_detected_with_no_collateral(p):
    base = _clean(p)
    rec = np_.judge(p, base, _planted(p, base))
    assert rec["detected"] is True and rec["collateral"] == [] and rec["verdict_after"] in p.expect and rec["verdict_before"] == p.base


@ALL
def test_judge_a_verdict_the_plant_did_not_declare_is_not_detected(p):               # seeded defect 2: the cell moved, but not as the plant claims
    base = _clean(p)
    post = _planted(p, base)
    wrong = next(v for v in ("FAIL", "PARTIAL", "NO_DETECTOR", "PASS", "N/A") if v not in p.expect and v != p.base)
    post[p.asset][p.check] = wrong
    assert np_.judge(p, base, post)["detected"] is False


@ALL
def test_judge_a_move_to_a_verdict_that_closes_a_gap_is_never_detected(p):          # seeded defect 3: the cell got BETTER
    base = _clean(p)
    post = _planted(p, base)
    post[p.asset][p.check] = "PASS" if p.base != "PASS" else "N/A"
    assert np_.judge(p, base, post)["detected"] is False


@ALL
def test_judge_a_move_on_another_asset_is_collateral(p):                             # seeded defect 4: the defect leaks
    base = _clean(p)
    post = _planted(p, base)
    other = next(a for a in _asset_ids() if a != p.asset)
    post[other][p.check] = "FAIL"
    rec = np_.judge(p, base, post)
    assert rec["detected"] is True and rec["collateral"] == [f"{other}/{p.check}: PASS->FAIL"]


@ALL
def test_judge_an_undeclared_move_of_the_plants_own_asset_is_collateral(p):         # seeded defect 5: an undeclared co-fire
    base = _clean(p)
    post = _planted(p, base)
    spare = next(c for c in base[p.asset] if c != p.check and c not in p.allow and c not in dict(p.also))
    post[p.asset][spare] = "FAIL"
    rec = np_.judge(p, base, post)
    assert rec["collateral"] == [f"{p.asset}/{spare}: PASS->FAIL"]


@ALL
def test_judge_a_declared_cofire_is_recorded_as_a_same_asset_effect_not_collateral(p):
    base = _clean(p)
    post = _planted(p, base)
    for c in p.allow:
        post[p.asset][c] = "FAIL"
    rec = np_.judge(p, base, post)
    assert rec["collateral"] == [] and set(rec["same_asset_effects"]) == set(p.allow)


@ALL
def test_judge_a_plant_resting_on_a_different_baseline_is_refused(p):               # seeded defect 6: baseline drift
    base = _clean(p)
    base[p.asset][p.check] = "FAIL" if p.base != "FAIL" else "PASS"
    rec = np_.judge(p, base, _planted(p, _clean(p)))
    assert rec["detected"] is False and "baseline drift" in rec["error"]


def test_judge_every_also_cell_must_move_too():
    p = next(x for x in np_.PLANTS if x.also)
    base = _clean(p)
    post = _planted(p, base)
    post[p.asset][p.also[0][0]] = "PASS"
    assert np_.judge(p, base, post)["detected"] is False


def test_unplantable_stale_names_a_declared_check_that_became_gradeable():
    ok = {"a": {"Complete.width": "NOT_GENERIC", "Reach.fields": "NOT_GENERIC"}, "b": {"Complete.width": "NOT_GENERIC", "Reach.fields": "NOT_GENERIC"}}
    assert np_.unplantable_stale([ok]) == []
    bad = copy.deepcopy(ok)
    bad["b"]["Reach.fields"] = "FAIL"
    assert any("Reach.fields" in x for x in np_.unplantable_stale([ok, bad]))
    gone = {"a": {"Complete.width": "NOT_GENERIC"}}                                    # the check vanished from the census entirely
    assert any("Reach.fields" in x for x in np_.unplantable_stale([gone]))


def _doc(**over) -> dict:
    plants = [dict(id=p.id, check=p.check, asset=p.asset, planted=True, detected=True, verdict_before=p.base, verdict_after=p.expect[0],
                   collateral=[], same_asset_effects={}, restore_ok=True, error=None) for p in np_.PLANTS]
    doc = dict(schema=np_.SCHEMA, inspector_blob_sha256="a" * 64, registry=dict(revision=1, fingerprint="f" * 64), plants=plants,
               unplantable=dict(np_.UNPLANTABLE), unplantable_stale=[], uncovered_required=[],
               mutation=dict(suite_notices=True, mutants=[dict(id="m", check="c", plant="p", noticed=True, mutant_detected=False, mutant_verdict_after="PASS")]))
    doc.update(over)
    doc["harness_sha256"] = np_.run_record_sha256(doc)
    return doc


def test_verdict_clean_run_is_zero():
    assert np_.verdict(_doc()) == (0, [])


@pytest.mark.parametrize("breakage, needle", [
    (lambda d: d["plants"][0].update(detected=False), "NOT detected"),
    (lambda d: d["plants"][1].update(collateral=["x/y: PASS->FAIL"]), "collateral"),
    (lambda d: d["plants"][2].update(restore_ok=False), "pristine world changed"),
    (lambda d: d["plants"][3].update(planted=False), "nothing was planted"),
    (lambda d: d["plants"][4].update(error="boom"), "boom"),
    (lambda d: d.update(unplantable_stale=["Reach.fields reads FAIL"]), "unplantable claim stale"),
    (lambda d: d.update(uncovered_required=["Build.new"]), "no plant"),
    (lambda d: d["mutation"].update(suite_notices=False), "mutated detector was not noticed"),
    (lambda d: d["mutation"].update(suite_notices=None, mutants=[]), "no mutation result"),
])
def test_verdict_names_every_failure_mode(breakage, needle):                         # each branch of verdict() can read non-zero
    d = _doc()
    breakage(d)
    code, why = np_.verdict(d)
    assert code == 2 and any(needle in w for w in why), why


def test_a_partial_run_is_judged_only_on_its_own_plants_and_is_marked_partial():
    d = _doc(plants=_doc()["plants"][:2], partial=True, uncovered_required=["Build.x"], mutation=dict(suite_notices=None, mutants=[]))
    assert np_.verdict(d) == (0, [])                                                  # no coverage / mutation claim is made by a partial run ...
    d["plants"][0]["detected"] = False
    assert np_.verdict(d)[0] == 2                                                     # ... but a plant it did run must still be detected
    full = _doc(uncovered_required=["Build.x"])
    assert np_.verdict(full)[0] == 2                                                  # the same gap in a FULL run fails
    assert _doc(partial=True)["harness_sha256"] != _doc()["harness_sha256"]           # and `partial` is bound into the run record


def test_run_record_hash_is_stable_binds_the_results_and_ignores_prose():
    d = _doc()
    assert np_.run_record_sha256(d) == d["harness_sha256"]
    for mutate in (lambda x: x["plants"][0].update(detected=False), lambda x: x["plants"][0].update(verdict_after="NO_DETECTOR"),
                   lambda x: x.update(inspector_blob_sha256="b" * 64), lambda x: x["registry"].update(revision=2),
                   lambda x: x["mutation"].update(suite_notices=False), lambda x: x["plants"][1].update(restore_ok=False)):
        e = copy.deepcopy(d)
        mutate(e)
        assert np_.run_record_sha256(e) != d["harness_sha256"]
    e = copy.deepcopy(d)
    e["plants"][0]["desc"] = "reworded"                                              # prose and dated measured text are not part of the record
    assert np_.run_record_sha256(e) == d["harness_sha256"]


def test_the_evidence_shape_is_the_scorecards_t1_reader_contract():
    """The shape nikasha_scorecard.load_t1_evidence / t1_cells read (E1.1): schema, plants[] {check: str, detected: bool, id, planted, collateral,
    restore_ok}, inspector_blob_sha256, unplantable {check: closed reason}, mutation {suite_notices: bool}, harness_sha256 (64 lowercase hex)."""
    d = _doc()
    assert d["schema"] == "nikasha_t1_evidence/1"
    assert isinstance(d["plants"], list) and d["plants"]
    for x in d["plants"]:
        assert isinstance(x["check"], str) and isinstance(x["detected"], bool) and "id" in x and x["planted"] is True
        assert x["collateral"] == [] and x["restore_ok"] is True
    assert isinstance(d["inspector_blob_sha256"], str)
    assert isinstance(d["unplantable"], dict) and set(d["unplantable"].values()) <= set(CLOSED_REASONS)
    assert d["mutation"]["suite_notices"] in (True, False, None)
    assert re.fullmatch(r"[0-9a-f]{64}", d["harness_sha256"])


def test_cli_list_names_every_plant_and_every_unplantable_check_and_touches_no_database(capsys):
    assert np_.main(["list"]) == 0
    out = capsys.readouterr().out
    for p in np_.PLANTS:
        assert p.id in out and p.check in out
    for c, why in np_.UNPLANTABLE.items():
        assert c in out and why in out


def test_cli_an_unknown_plant_id_is_a_script_error_before_any_cluster_starts(capsys, monkeypatch):
    monkeypatch.setattr(np_, "_cluster", lambda: (_ for _ in ()).throw(AssertionError("a cluster must not start for a bad argument")))
    assert np_.main(["run", "--only", "no_such_plant"]) == 5
    assert "no_such_plant" in capsys.readouterr().err


def test_cli_a_cluster_that_cannot_start_is_exit_5_never_a_verdict(capsys, monkeypatch):
    monkeypatch.setattr(np_, "_cluster", lambda: (_ for _ in ()).throw(np_.HarnessError("no PostgreSQL server binaries")))
    assert np_.main(["run", "--only", "build_dag"]) == 5
    assert "no PostgreSQL" in capsys.readouterr().err


def test_the_mutation_anchors_exist_exactly_once_in_the_inspector():
    src = (np_.REPO / np_.INSPECTOR_REL).read_text(encoding="utf-8")
    for m in np_.MUTANTS:
        assert src.count(m["old"]) == 1, m["id"]
        assert m["old"] != m["new"]
        assert m["plant"] in {p.id for p in np_.PLANTS} and m["check"] == next(p.check for p in np_.PLANTS if p.id == m["plant"])


def test_a_drifted_mutation_anchor_is_a_harness_error_not_a_skipped_mutant():
    with pytest.raises(np_.HarnessError, match="occurs 0 times"):
        np_.mutate(b"x = 1\n", np_.MUTANTS[0])


def test_the_fixture_tree_and_declarations_load_through_the_real_validator():
    ac.validate_declarations(json.loads(np_.declarations_text()))


# ───────────────────────────── (B) real: the inspector on the synthetic world ─────────────────────────────

@pytest.fixture(scope="module")
def world(disposable_pg):
    db = np_.Db(disposable_pg)
    work = Path(tempfile.mkdtemp(prefix="nikasha_plant_t_", dir=None))
    w = np_.World(db, work)
    w.build()
    inst = w.clone("baseline")
    try:
        base = np_.cells(inst.census())
    finally:
        inst.drop()
    yield w, base
    db.drop(w.base_db)
    import shutil
    shutil.rmtree(work, ignore_errors=True)


def _by_id(i):
    return next(p for p in np_.PLANTS if p.id == i)


def test_REAL_the_clean_world_reads_the_baseline_every_plant_assumes(world):
    w, base = world
    for p in np_.PLANTS:
        assert base[p.asset].get(p.check) == p.base, (p.id, base[p.asset].get(p.check))
    assert np_.unplantable_stale([base]) == []


def test_REAL_the_inspector_runs_with_a_scrubbed_environment_whatever_the_parent_holds(world, monkeypatch):
    """The parent environment names a (fake) production database; the inspector subprocess must reach ONLY the disposable cluster."""
    w, base = world
    for k, v in dict(PGHOST="prod.invalid", PGUSER="svc_reader", PGPASSWORD="hunter2", PGDATABASE="prod", PGPORT="6543", PGSERVICE="prod",
                     DATABASE_URL="postgresql://svc_reader:hunter2@prod.invalid:6543/prod", SUPABASE_DB_URL="postgresql://x@prod.invalid/x").items():
        monkeypatch.setenv(k, v)
    inst = w.clone("t_env")
    try:
        doc = inst.census()
    finally:
        inst.drop()
    assert np_.cells(doc) == base
    assert "prod.invalid" not in json.dumps(doc) and "hunter2" not in json.dumps(doc)


def test_REAL_a_real_plant_is_detected_clean_and_restored(world):
    w, base = world
    rec = np_.run_one(w, _by_id("build_count_integrity"), base, "t_real1")
    assert rec["planted"] and rec["detected"] and rec["collateral"] == [] and rec["restore_ok"] and rec["harness_error"] is None
    assert (rec["verdict_before"], rec["verdict_after"]) == ("PASS", "PARTIAL")


def test_REAL_a_plant_that_changes_nothing_is_not_planted_and_not_detected(world):
    w, base = world
    noop = np_.Plant(id="noop", check="Count.floor", asset="bg_t1_floor", desc="x", apply=lambda i: i.sql("UPDATE bg_t1_floor SET note = note WHERE false"))
    rec = np_.run_one(w, noop, base, "t_noop")
    assert rec["planted"] is False and rec["detected"] is False and np_.verdict(_doc(plants=[rec]))[0] == 2


def test_REAL_a_plant_whose_sql_hits_zero_rows_is_not_planted(world):
    w, base = world
    miss = np_.Plant(id="miss", check="Count.floor", asset="bg_t1_floor", desc="x",
                     apply=lambda i: i.sql("DELETE FROM bg_t1_floor WHERE code = 'no-such-code'"))
    rec = np_.run_one(w, miss, base, "t_miss")
    assert rec["planted"] is False and rec["detected"] is False


def test_REAL_a_plant_edit_anchor_that_does_not_exist_is_a_harness_error(world):
    w, base = world
    bad = np_.Plant(id="badanchor", check="Idem.pattern", asset="bg_t1_idem", desc="x", expect=("FAIL",),
                    apply=lambda i: i.edit(np_.wpath("bg_t1_idem"), "THIS TEXT IS NOT THERE", "x"))
    rec = np_.run_one(w, bad, base, "t_anchor")
    assert rec["detected"] is False and rec["harness_error"] and "occurs 0 times" in rec["harness_error"]


def test_REAL_a_plant_that_leaks_into_the_pristine_world_is_reported_not_restored(world):
    w, base = world

    def leak(inst):
        inst.world.db.sql("UPDATE bg_t1_floor SET note = 'leaked' WHERE code = 'c1'", inst.world.base_db)       # the pristine database, not the clone
        inst.sql("DELETE FROM bg_t1_floor WHERE code = 'c4'")
    p = np_.Plant(id="leaky", check="Count.floor", asset="bg_t1_floor", desc="x", apply=leak, allow=("Build.completion",))
    try:
        rec = np_.run_one(w, p, base, "t_leak")
        assert rec["restore_ok"] is False
        assert "pristine world changed" in " ".join(np_.verdict(_doc(plants=[rec]))[1])
    finally:
        w.db.sql("UPDATE bg_t1_floor SET note = 'first' WHERE code = 'c1'", w.base_db)
    assert w.pristine()


def test_REAL_a_plant_that_also_damages_another_asset_reports_collateral(world):
    w, base = world

    def noisy(inst):
        inst.sql("DELETE FROM bg_t1_floor WHERE code = 'c4'")
        inst.sql("UPDATE bg_t1_ctl SET synonyms = '{}'")                                                         # another asset's table
    p = np_.Plant(id="noisy", check="Count.floor", asset="bg_t1_floor", desc="x", apply=noisy, allow=("Build.completion",))
    rec = np_.run_one(w, p, base, "t_noisy")
    assert rec["detected"] is True and any(c.startswith("bg_t1_ctl/Vocab.alias") for c in rec["collateral"])
    assert np_.verdict(_doc(plants=[rec]))[0] == 2


def test_REAL_a_blinded_detector_makes_the_planted_cell_not_detected(world):
    """Seeded inspector defect, end to end: the same plant, judged against the control baseline, on a world built around an inspector whose
    Build.count_integrity ignores integrity_check_sql. The suite must NOT pass the plant."""
    w, base = world
    m = next(x for x in np_.MUTANTS if x["id"] == "count_integrity_ignores_integrity")
    res = np_.run_mutation(w.work, w.db, {p.id: p for p in np_.PLANTS}, base, [m])
    assert res["suite_notices"] is True and res["mutants"][0]["noticed"] is True and res["mutants"][0]["mutant_detected"] is False


SAMPLE = ("build_dag", "build_completion", "vocab_identity", "build_contract", "dens_served", "narr_fidelity_test", "carr_d1")


@pytest.mark.parametrize("pid", SAMPLE)
def test_REAL_a_plant_of_every_kind_is_detected_cleanly_on_the_real_inspector(world, pid):
    """One plant per KIND of plant (registry SQL, throughput SQL, table SQL, writer edit, capability edit, test-file delete, declared D1): the
    real inspector as a subprocess, a fresh clone each, judged against the clean census. The full set is the dedicated job's run."""
    w, base = world
    rec = np_.run_one(w, _by_id(pid), base, f"t_{pid[:20]}")
    assert rec["planted"] and rec["detected"] and rec["collateral"] == [] and rec["restore_ok"] and rec["error"] is None, rec


@pytest.mark.skipif(not os.environ.get("NIKASHA_PLANT_FULL"), reason="the full run (every plant + every mutant, several minutes serial) is the dedicated CI job's "
                                                                    "`nikasha_plant.py run`; set NIKASHA_PLANT_FULL=1 to run it here")
def test_REAL_the_whole_suite_detects_every_plant_cleanly_and_notices_every_mutant(disposable_pg):
    """The long test: the real run_suite, the evidence the scorecard will read, and the harness verdict."""
    work = Path(tempfile.mkdtemp(prefix="nikasha_plant_full_"))
    try:
        doc = np_.run_suite(np_.Db(disposable_pg), work)
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
    code, why = np_.verdict(doc)
    assert code == 0, why
    assert doc["schema"] == "nikasha_t1_evidence/1" and len(doc["plants"]) == len(np_.PLANTS)
    assert all(r["planted"] and r["detected"] and not r["collateral"] and r["restore_ok"] and r["error"] is None for r in doc["plants"])
    required = {c for c, e in ac.CRITERION_REGISTRY.items() if e.get("detector") == np_.MEASURE_DETECTOR}
    assert {r["check"] for r in doc["plants"]} | set(doc["unplantable"]) == required and doc["uncovered_required"] == []
    assert doc["mutation"]["suite_notices"] is True and len(doc["mutation"]["mutants"]) == len(np_.MUTANTS)
    assert doc["registry"]["revision"] == ac.REGISTRY_REVISION and doc["registry"]["fingerprint"] == ac.registry_fingerprint()
    import hashlib
    assert doc["inspector_blob_sha256"] == hashlib.sha256((np_.REPO / np_.INSPECTOR_REL).read_bytes()).hexdigest()
    assert doc["harness_sha256"] == np_.run_record_sha256(doc)


@pytest.mark.skipif(not os.environ.get("NIKASHA_PLANT_FULL"), reason="runs every plant (several minutes serial); set NIKASHA_PLANT_FULL=1")
def test_REAL_the_evidence_is_read_by_the_scorecards_t1_reader_when_the_scorecard_is_present(disposable_pg):
    """Cross-check against nikasha_scorecard (E1.1) once it is on this branch: skipped until then (the shape contract is pinned above)."""
    sc_path = HERE.parent / "nikasha_scorecard.py"
    if not sc_path.is_file():
        pytest.skip("nikasha_scorecard.py is not on this branch yet (E1.1)")
    import importlib.util
    spec = importlib.util.spec_from_file_location("nikasha_scorecard_for_plant_test", sc_path)
    sc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = sc
    spec.loader.exec_module(sc)
    work = Path(tempfile.mkdtemp(prefix="nikasha_plant_sc_"))
    try:
        doc = np_.run_suite(np_.Db(disposable_pg), work, mutants=())
        ev_path = work / "ev.json"
        ev_path.write_text(json.dumps(doc), encoding="utf-8")
        ev = sc.load_t1_evidence(str(ev_path))
        facts = dict(criteria={c: dict(detector=e["detector"]) for c, e in ac.CRITERION_REGISTRY.items()})
        plant_cell, _mut, n = sc.t1_cells(ev, facts, doc["inspector_blob_sha256"])
        # every plant detected, no collateral, all restored; the ONLY uncovered checks are the declared-unplantable ones, so the cell is PARTIAL by the
        # scorecard's own rule ("an unplantable check never counts as covered"), never FAIL / UNMEASURED
        assert n == len(doc["plants"]) and plant_cell["verdict"] == "PARTIAL", plant_cell
        assert plant_cell["undetected"] == [] and plant_cell["collateral"] == [] and plant_cell["uncovered"] == sorted(np_.UNPLANTABLE)
        assert plant_cell["unplantable_declared"] == sorted(np_.UNPLANTABLE) and plant_cell["unplantable_reason_refused"] == []
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
