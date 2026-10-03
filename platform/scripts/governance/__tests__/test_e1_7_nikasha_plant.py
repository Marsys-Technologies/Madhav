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
    files = np_.runtime_files_sha256()
    doc = dict(schema=np_.SCHEMA, inspector_blob_sha256=files[np_.INSPECTOR_REL], harness_file_sha256=files[np_.GEN_REL], runtime_files_sha256=files,
               inspector_tree_dirty=False, runtime_files_dirty=[], registry=dict(revision=1, fingerprint="f" * 64), plants=plants,
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
                   lambda x: x["mutation"].update(suite_notices=False), lambda x: x["plants"][1].update(restore_ok=False),
                   lambda x: x.update(harness_file_sha256="0" * 64), lambda x: x["runtime_files_sha256"].update({np_.INSPECTOR_REL: "0" * 64}),
                   lambda x: x["runtime_files_sha256"].pop("platform/scripts/governance/carriage_d1.py"),
                   lambda x: x.update(inspector_tree_dirty=True), lambda x: x.update(runtime_files_dirty=["x"])):
        e = copy.deepcopy(d)
        mutate(e)
        assert np_.run_record_sha256(e) != d["harness_sha256"]
    e = copy.deepcopy(d)
    e["plants"][0]["desc"] = "reworded"                                              # prose and dated measured text are not part of the record
    assert np_.run_record_sha256(e) == d["harness_sha256"]


def test_the_sibling_modules_the_inspector_loads_are_hashed_into_the_evidence_and_mutated():
    files = set(np_.evidence_files())
    for rel in np_.RUNTIME_FILES:
        assert rel in files, rel
    for rel in ("platform/scripts/governance/carriage_d1.py", "platform/scripts/governance/check_fact_category_pinning.py",
                "platform/scripts/governance/check_no_raw_token_in_narrative.py", "platform/python-sidecar/pipeline/orchestrator/dag_edge_guard.py",
                np_.DECLARATIONS_REL, np_.D1_FIXTURE_REL, np_.GEN_REL):
        assert rel in files, rel
    assert set(np_.runtime_files_sha256()) == files
    assert {m["file"] for m in np_.MUTANTS} >= {np_.INSPECTOR_REL, "platform/scripts/governance/carriage_d1.py",
                                                  "platform/scripts/governance/check_no_raw_token_in_narrative.py"}


# ── verify_evidence: integrity is checked against the tree, and the hash alone proves nothing (F1) ──
CARR = "platform/scripts/governance/carriage_d1.py"


def test_verify_a_genuine_record_is_consistent_with_the_working_tree():
    assert np_.verify_evidence(_doc()) == []


def _forge(**changes):
    """A hand-written record that RECOMPUTES its own harness_sha256: what anyone can produce without running the harness."""
    d = _doc()
    for k, v in changes.items():
        d[k] = v
    d["harness_sha256"] = np_.run_record_sha256(d)
    return d


def test_verify_a_zeroed_harness_hash_does_not_survive():                              # H13: the hash replaced by zeros
    d = _doc()
    d["harness_sha256"] = "0" * 64
    assert any("harness_sha256" in w for w in np_.verify_evidence(d))
    z = _forge(harness_file_sha256="0" * 64)
    assert any("harness_file_sha256" in w for w in np_.verify_evidence(z))               # consistent record, but not the file's hash
    files = dict(z["runtime_files_sha256"])
    files[np_.GEN_REL] = "0" * 64
    z = _forge(harness_file_sha256="0" * 64, runtime_files_sha256=files)
    assert any(np_.GEN_REL in w and "tree" in w for w in np_.verify_evidence(z))         # both consistent with each other, neither with the tree


def test_verify_a_forged_inspector_or_sibling_hash_is_named():
    for rel in (np_.INSPECTOR_REL, CARR, "platform/python-sidecar/pipeline/orchestrator/dag_edge_guard.py"):
        files = dict(np_.runtime_files_sha256())
        files[rel] = "0" * 64
        d = _forge(runtime_files_sha256=files, **({"inspector_blob_sha256": "0" * 64} if rel == np_.INSPECTOR_REL else {}))
        assert any(rel in w for w in np_.verify_evidence(d)), rel


def test_verify_an_omitted_runtime_file_is_a_problem():
    files = dict(np_.runtime_files_sha256())
    files.pop(CARR)
    assert any("differently" in w for w in np_.verify_evidence(_forge(runtime_files_sha256=files)))


def test_verify_inspector_blob_must_equal_its_runtime_entry():
    assert any("inspector_blob_sha256" in w for w in np_.verify_evidence(_forge(inspector_blob_sha256="b" * 64)))


@pytest.mark.parametrize("dirty, files", [(True, []), (False, ["x.py"]), (None, None), (True, None)])
def test_verify_a_dirty_or_unknown_tree_is_unmeasured(dirty, files):
    assert any("UNMEASURED" in w for w in np_.verify_evidence(_forge(inspector_tree_dirty=dirty, runtime_files_dirty=files)))


def test_verify_a_malformed_document_never_raises():
    assert np_.verify_evidence({"schema": "x"}) and np_.verify_evidence([]) and np_.verify_evidence(None)
    d = _doc()
    d.pop("registry")
    assert any("malformed" in w for w in np_.verify_evidence(d))


def test_verify_against_a_git_ref_compares_the_blobs_at_that_ref():
    blobs = {rel: np_._blob(rel, "HEAD") for rel in np_.evidence_files()}
    if any(b is None for b in blobs.values()):
        pytest.skip("an evidence file is not committed at HEAD yet")
    import hashlib
    files = {rel: hashlib.sha256(b).hexdigest() for rel, b in blobs.items()}
    d = _forge(runtime_files_sha256=files, harness_file_sha256=files[np_.GEN_REL], inspector_blob_sha256=files[np_.INSPECTOR_REL])
    assert np_.verify_evidence(d, "HEAD") == []
    files[CARR] = "0" * 64
    assert any(CARR in w for w in np_.verify_evidence(_forge(runtime_files_sha256=files), "HEAD"))
    assert any("tree" in w for w in np_.verify_evidence(d, "no-such-ref-xyz"))


def test_cli_verify_exit_codes(tmp_path, capsys):
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps(_doc()), encoding="utf-8")
    assert np_.main(["verify", str(ok)]) == 0
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(_forge(harness_file_sha256="0" * 64)), encoding="utf-8")
    assert np_.main(["verify", str(bad)]) == 2 and "harness_file_sha256" in capsys.readouterr().err
    assert np_.main(["verify", str(tmp_path / "missing.json")]) == 5


def test_the_evidence_says_it_is_integrity_not_authenticity():
    assert "INTEGRITY, not authenticity" in np_.EVIDENCE_DOC and "CI job" in np_.EVIDENCE_DOC
    assert "INTEGRITY, NOT AUTHENTICITY" in np_.__doc__ and "L0-ONLY" in np_.__doc__
    assert "INTEGRITY" in np_.run_record_sha256.__doc__


def test_dirty_files_reports_a_modified_evidence_file_and_none_when_git_cannot_answer(monkeypatch):
    got = np_.dirty_files()
    assert got is None or isinstance(got, list)
    monkeypatch.setattr(np_, "_git_out", lambda *a: (_ for _ in ()).throw(OSError("no git")))
    assert np_.dirty_files() is None
    monkeypatch.setattr(np_, "_git_out", lambda *a: subprocess_result(128, b"", b"fatal"))
    assert np_.dirty_files() is None
    monkeypatch.setattr(np_, "_git_out", lambda *a: subprocess_result(0, b" M platform/scripts/governance/asset_census.py\n", b""))
    assert np_.dirty_files() == ["platform/scripts/governance/asset_census.py"]


def subprocess_result(rc, out, err):
    import subprocess
    return subprocess.CompletedProcess([], rc, out, err)


# ── survivors of the independent mutation sweep: each guard now has a test that kills its mutant ──
def test_covered_checks_counts_only_planted_detected_clean_restored_plants():              # H11
    good = dict(check="A", planted=True, detected=True, collateral=[], restore_ok=True)
    assert np_.covered_checks([good]) == {"A"}
    for broken in (dict(restore_ok=False), dict(planted=False), dict(detected=False), dict(collateral=["x/y: PASS->FAIL"])):
        assert np_.covered_checks([dict(good, **broken)]) == set(), broken


def test_noticed_requires_the_harness_to_have_run(  ):                                      # H8
    m = dict(id="m", check="c", plant="p", file=np_.INSPECTOR_REL)
    clean = dict(detected=True, collateral=[], harness_error=None, verdict_after="FAIL", error=None)
    assert np_.noticed_record(m, clean)["noticed"] is False                                  # the suite still passes the plant: the mutant went unseen
    assert np_.noticed_record(m, dict(clean, detected=False))["noticed"] is True
    assert np_.noticed_record(m, dict(clean, collateral=["a/b: PASS->FAIL"]))["noticed"] is True
    assert np_.noticed_record(m, dict(clean, detected=False, harness_error="boom"))["noticed"] is False   # a failed run is never a notice
    assert np_.noticed_record(m, dict(clean, detected=False, harness_error=None))["noticed"] is True
    assert np_.suite_notices([]) is False and np_.suite_notices([dict(noticed=True), dict(noticed=False)]) is False
    assert np_.suite_notices([dict(noticed=True)]) is True


@pytest.mark.parametrize("rc, wrote", [(4, True), (5, True), (1, True), (6, True), (-9, True), (0, False), (2, False)])
def test_run_census_accepts_only_exit_0_2_3_with_a_census_file(monkeypatch, tmp_path, rc, wrote):   # H6
    import subprocess
    tree = tmp_path / "t"
    (tree / "platform/scripts/governance").mkdir(parents=True)

    def fake(cmd, **kw):
        if wrote:
            (tree / "census.json").write_text(json.dumps({"L0": {"assets": []}}), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, rc, b"", b"census crashed")
    monkeypatch.setattr(np_.subprocess, "run", fake)

    class _Cl:
        bin_dir, env = tmp_path, staticmethod(lambda: {})
    with pytest.raises(np_.HarnessError, match="did not produce a census"):
        np_.run_census(type("D", (), {"cl": _Cl})(), tree, "x")


@pytest.mark.parametrize("rc", [0, 2, 3])
def test_run_census_accepts_the_inspectors_own_exit_codes(monkeypatch, tmp_path, rc):
    import subprocess
    tree = tmp_path / "t"
    tree.mkdir()

    def fake(cmd, **kw):
        (tree / "census.json").write_text(json.dumps({"L0": {"assets": []}}), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, rc, b"", b"")
    monkeypatch.setattr(np_.subprocess, "run", fake)

    class _Cl:
        bin_dir, env = tmp_path, staticmethod(lambda: {})
    assert np_.run_census(type("D", (), {"cl": _Cl})(), tree, "x") == {"L0": {"assets": []}}


def test_an_edit_anchor_that_occurs_twice_is_refused_like_one_that_occurs_never(tmp_path):    # H12
    class _W:
        work = tmp_path
        wid = 0
    inst = np_.Instance(_W, "k")
    inst.tree = tmp_path
    (tmp_path / "f.txt").write_text("a b a", encoding="utf-8")
    with pytest.raises(np_.HarnessError, match="occurs 2 times"):
        inst.edit("f.txt", "a", "c")
    with pytest.raises(np_.HarnessError, match="occurs 0 times"):
        inst.edit("f.txt", "zzz", "c")
    inst.edit("f.txt", "b", "c")
    assert (tmp_path / "f.txt").read_text() == "a c a"


def test_write_tree_refuses_an_override_that_is_not_a_runtime_file(tmp_path):
    with pytest.raises(np_.HarnessError, match="not a runtime file"):
        np_.write_tree(tmp_path / "t", {}, {"some/other/file.py": b"x"})


def test_a_runtime_file_and_its_mutant_win_over_a_synthetic_copy_of_the_same_path(tmp_path):
    """The D1 declaration cites carriage_d1.py, so the synthetic file set holds a copy of it: written AFTER the runtime copy it silently replaced
    the mutant (the carriage_d1 mutant was 'unnoticed' because it never reached the tree)."""
    t1 = tmp_path / "a"
    np_.write_tree(t1, {CARR: "SYNTHETIC COPY\n"}, {CARR: b"MUTANT\n"})
    assert (t1 / CARR).read_bytes() == b"MUTANT\n"
    t2 = tmp_path / "b"
    np_.write_tree(t2, {CARR: "SYNTHETIC COPY\n"})
    assert (t2 / CARR).read_bytes() == (np_.REPO / CARR).read_bytes()
    assert (np_.REPO / CARR).read_bytes() == (np_.REPO / CARR).read_bytes() and b"SYNTHETIC" not in (t2 / CARR).read_bytes()


def test_the_new_plants_cover_the_branches_the_sweep_found_unplanted():
    ids = {p.id: p for p in np_.PLANTS}
    assert ids["build_completion_integrity"].expect == ("PARTIAL",) and ids["build_completion_integrity"].check == "Build.completion"
    assert ids["build_history_aborted"].check == "Build.history" and ids["build_dep_liveness_stale"].expect == ("PARTIAL",)


def test_the_fixture_integrity_sql_holds_on_the_clean_world_and_is_declared_for_every_asset():
    sql = np_.world_sql()
    assert sql.count("bool_and(length(code) > 0)") == len(np_.ASSETS) and "bool_and(length(graha) > 0)" in sql
    assert "WHERE code IS NULL" not in sql                                                  # the pre-N-99 SQL returned 0 (falsy): a baseline that cannot PASS


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


def test_the_mutation_anchors_exist_exactly_once_in_the_file_each_mutant_targets():
    for m in np_.MUTANTS:
        src = (np_.REPO / m["file"]).read_text(encoding="utf-8")
        assert m["file"] in np_.RUNTIME_FILES, m["id"]
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
    assert doc["runtime_files_sha256"] == np_.runtime_files_sha256() and doc["harness_file_sha256"] == doc["runtime_files_sha256"][np_.GEN_REL]
    assert doc["inspector_tree_dirty"] in (True, False, None)
    assert all("UNMEASURED" in w for w in np_.verify_evidence(doc))              # consistent with the tree; a dirty working tree is the only problem allowed
    assert {m["file"] for m in doc["mutation"]["mutants"]} == {m["file"] for m in np_.MUTANTS}


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


# ── F4: SIGTERM must stop the cluster and remove the temp dirs (a REAL subprocess; it starts and then kills its own cluster) ──
def _pids_mentioning(path: Path) -> list:
    import subprocess
    out = subprocess.run(["ps", "-eo", "pid=,command="], capture_output=True, text=True).stdout
    return [int(ln.split(None, 1)[0]) for ln in out.splitlines() if str(path) in ln and "ps -eo" not in ln]


@pytest.mark.parametrize("sig_name, code", [("SIGTERM", 143), ("SIGHUP", 129)])
def test_REAL_a_signal_stops_the_cluster_and_removes_the_temp_dirs(sig_name, code):
    import shutil
    import signal
    import subprocess
    import time
    tmpd = Path(tempfile.mkdtemp(prefix="sigt_", dir="/tmp"))
    env = {k: v for k, v in os.environ.items() if not (k.startswith("PG") or k in ("DATABASE_URL", "POSTGRES_URL"))}
    env["TMPDIR"] = str(tmpd)
    p = subprocess.Popen([sys.executable, str(HERE.parent / "nikasha_plant.py"), "run", "--only", "build_dag"], env=env, cwd=str(tmpd),
                         start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.time() + 120
        while time.time() < deadline and p.poll() is None and not list(tmpd.glob("nikasha_plant_*/tree_base")):
            time.sleep(0.2)
        if p.poll() is not None:
            pytest.skip(f"the run ended before it reached the suite (no cluster?): {p.stderr.read().decode()[-300:]}")
        assert list(tmpd.glob("suvarna_pg_*/data/postmaster.pid")), "the cluster should be up while the suite runs"
        p.send_signal(getattr(signal, sig_name))
        rc = p.wait(timeout=90)
        assert rc == code, (rc, p.stderr.read().decode()[-300:])
        deadline = time.time() + 30
        while time.time() < deadline and _pids_mentioning(tmpd):
            time.sleep(0.3)
        assert _pids_mentioning(tmpd) == [], "a process of the run (postgres, psql, the inspector) survived the signal"
        assert list(tmpd.glob("suvarna_pg_*")) == [] and list(tmpd.glob("nikasha_plant_*")) == [], "temp directories were left behind"
    finally:
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
        for pid in _pids_mentioning(tmpd):                    # never leave a cluster behind (host SysV memory is scarce), whatever the assertion said
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        shutil.rmtree(tmpd, ignore_errors=True)
