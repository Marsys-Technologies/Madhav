"""test_n233_postprocess_residuals.py: certification and the closed list of RULED RESIDUALS (SS ruling N-233 R3).

A NAMED, declared residual in the engine's closed vocabulary (Carr.D1 transcription-not-verified, Carr.D2 no-per-witness-values, Carr.D3 single-derivation, Ldgr.source_presence unsourced-declared) is a ruled N/A for
certification, not a blocker, and the certified line names it. It is CHECKED, never trusted: the cell must be N/A, its rule id must be in the engine's closed list (asset_census.NA_RULE_DECISIONS) AND belong to its own
criterion, and its decision text must be the engine's text. An undeclared NO_DETECTOR, an undeclared rule id, a forged decision and a residual rule on another criterion's cell all still block. Offline (no database).
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import test_e5_7_census_postprocess as base  # noqa: E402  (its fixtures: world / run / cell / eng / good_cells)

cp, cell, eng, good_cells, world, run = base.cp, base.cell, base.eng, base.good_cells, base.world, base.run

D1 = "Carr.D1#measured:transcription-not-verified"
D2 = "Carr.D2#measured:no-per-witness-values"
D3 = "Carr.D3#measured:single-derivation"
UNS = "Ldgr.source_presence#measured:unsourced-declared"


def _out(tmp_path, a1_cells):
    tmp_path.mkdir(parents=True, exist_ok=True)
    rc, out = run(world(tmp_path, {"a1": a1_cells}), tmp_path)
    cert = {c["asset"]: c for c in json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"]}
    fix = json.loads((out / "FIX_LIST.json").read_text())["fix_list"]
    return cert, fix


def test_the_four_named_residuals_certify_and_are_named_on_the_line(tmp_path):
    cells = good_cells(**{"Carr.D1": eng(D1), "Carr.D2": eng(D2), "Carr.D3": eng(D3), "Ldgr.source_presence": eng(UNS)})
    cert, fix = _out(tmp_path, cells)
    assert "a1" in cert and "a1" not in fix
    assert cert["a1"]["ruled_residuals"] == ["D1: unverified transcription", "D2: no per-witness values", "D3: single derivation (no second method)", "Ldgr: unsourced (declared)"]
    assert cert["a1"]["ruled_na"] == 4 and cert["a2"]["ruled_residuals"] == []


def test_the_residual_vocabulary_is_a_closed_subset_of_the_engines_rule_list():
    rules = cp.engine_rule_decisions()
    assert set(cp.RULED_RESIDUALS) == {D1, D2, D3, UNS} and set(cp.RULED_RESIDUALS) <= set(rules)
    assert set(cp.CEILING_RULES) <= set(cp.RULED_RESIDUALS)


# ───────────────────────── forgery probes: every one of these turns the cell back into a blocker ─────────────────────────

def _blocks(tmp_path, name, bad, needle):
    cert, fix = _out(tmp_path, good_cells(**{name: bad}))
    assert "a1" not in cert and "a1" in fix, (name, bad)
    item = next(i for i in fix["a1"] if i["criterion"] == name)
    assert needle in item["cause"], item
    return item


def test_FORGERY_an_undeclared_rule_id_is_not_a_ruled_residual(tmp_path):
    forged = cell("Carr.D3", "N/A", rule_id="Carr.D3#measured:single-derivation-ish", decision="N-156")
    _blocks(tmp_path, "Carr.D3", forged, "not in the engine's closed N/A rule list")


def test_FORGERY_a_forged_decision_text_is_not_a_ruled_residual(tmp_path):
    forged = cell("Carr.D3", "N/A", rule_id=D3, decision="N-156")
    _blocks(tmp_path, "Carr.D3", forged, "not the engine's text")


def test_FORGERY_a_residual_rule_on_another_criterions_cell_is_not_a_ruled_residual(tmp_path):
    forged = eng(D3, name="Carr.D1")
    _blocks(tmp_path, "Carr.D1", forged, "not a rule of criterion Carr.D1")


@pytest.mark.parametrize("rid", [D1, D2, D3, UNS])
def test_FORGERY_a_residual_named_cell_that_reads_no_detector_still_blocks(tmp_path, rid):
    """The residual label on a NO_DETECTOR (or any non-N/A) cell is not the residual: only an N/A the detector emitted counts."""
    name = rid.split("#")[0]
    for v in ("NO_DETECTOR", "PARTIAL", "FAIL"):
        forged = dict(cell(name, v), rule_id=rid, decision=cp.engine_rule_decisions()[rid])
        cert, fix = _out(tmp_path / v, good_cells(**{name: forged}))
        assert "a1" not in cert and any(i["criterion"] == name and i["verdict"] == v for i in fix["a1"]), (rid, v)


def test_an_undeclared_no_detector_still_blocks(tmp_path):
    item = _blocks(tmp_path, "Carr.D3", cell("Carr.D3", "NO_DETECTOR", "APPLIES", reason="not measured (applies)"), "not measured (applies)")
    assert item["verdict"] == "NO_DETECTOR"


def test_a_ruled_na_without_rule_or_decision_is_unruled(tmp_path):
    _blocks(tmp_path, "Carr.D2", cell("Carr.D2", "N/A"), "unruled")
    _blocks(tmp_path / "x", "Carr.D2", cell("Carr.D2", "N/A", rule_id=D2), "unruled")


def test_MUTATION_removing_a_residual_from_the_engines_list_makes_it_a_blocker(tmp_path, monkeypatch):
    rules = dict(cp.engine_rule_decisions())
    cells = good_cells(**{"Carr.D3": eng(D3)})
    cert, _fix = _out(tmp_path / "before", cells)
    assert "a1" in cert
    del rules[D3]
    monkeypatch.setattr(cp, "_ENGINE_RULES", rules)
    cert, fix = _out(tmp_path / "after", cells)
    assert "a1" not in cert and "a1" in fix


def test_every_ruled_na_of_census_a_is_backed_by_the_engines_list_when_the_files_are_present():
    root = pathlib.Path("/Users/Dev/suvarna-evidence/census_final/1b6734e91")
    files = [root / f"census_{l}.json" for l in ("L0", "L1", "L2")]
    if not all(f.is_file() for f in files):
        pytest.skip("the final census A files are not on this machine")
    n = bad = 0
    for l, f in zip(("L0", "L1", "L2"), files):
        d = json.loads(f.read_text())
        for gates in d["rollup"]["layers"][l].values():
            for g in gates.values():
                for c in g["checks"]:
                    if c["v"] == "N/A":
                        n += 1
                        bad += cp.ruled_na_problem(c["criterion"], c) is not None
    assert n == 507 and bad == 0
