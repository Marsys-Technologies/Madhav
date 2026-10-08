"""test_n233_ratified_judgment.py: Carr.D1/D2/D3 of a ratified-judgment seed (SS N-235). Offline.

The cause `ratified_judgment` had no rule; N-235 declares Carr.D1/D2/D3#measured:ratified_judgment. Declaration-keyed AND checked: the cell reads N/A only for a carriage declaration of nature ratified_judgment that names
ruling N-235 (the measured record carries that block); certification names the ceiling. Forgery probes turn each unbacked cell back into a NO_DETECTOR / blocker.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e5_7_census_postprocess as base  # noqa: E402

cp, cell, eng, good_cells, world, run = base.cp, base.cell, base.eng, base.good_cells, base.world, base.run
CAR = {"served_surface": True, "nature": "ratified_judgment", "why": "system-authored constants typed as literals; ratified by SS ruling N-235", "evidence": "platform/python-sidecar/brahmagyan/l0_formula_constants.py:26",
       "ruling": "N-235", "per_witness_values": False}
RULES = [f"Carr.D{i}#measured:ratified_judgment" for i in (1, 2, 3)]


def _checks(car):
    return ac.carriage_declared_checks("bg_x", car, None, column_types=None, prose_columns=[])


def test_the_three_rules_are_declared_and_cite_n235():
    for r in RULES:
        assert r in ac.NA_RULE_DECISIONS and "N-235" in ac.NA_RULE_DECISIONS[r]
        assert r.split("#")[0] in ("Carr.D1", "Carr.D2", "Carr.D3") and "ratified_judgment" in ac.NA_CAUSES[r.split("#")[0]]


def test_a_declared_ratified_judgment_reads_ruled_na_in_the_rollup_with_the_n235_decision():
    rec = _checks(CAR)
    for crit in ("Carr.D1", "Carr.D2", "Carr.D3"):
        assert rec[crit]["cause"] == "ratified_judgment" and rec[crit]["ratified_judgment"] == {"nature": "ratified_judgment", "ruling": "N-235"}
        c = ac._check_contribution(crit, "L0", rec[crit], None)
        assert c["v"] == ac.NA and c["rule_id"] == f"{crit}#measured:ratified_judgment" and "N-235" in c["decision"], c
        assert ac._na_released(crit, rec[crit]) is True


def test_FORGERY_a_ratified_judgment_na_without_the_block_or_with_another_ruling_is_no_detector():
    good = _checks(CAR)["Carr.D3"]
    for bad in (dict(good, ratified_judgment=None), {k: v for k, v in good.items() if k != "ratified_judgment"},
                dict(good, ratified_judgment={"nature": "ratified_judgment", "ruling": "N-99"}),
                dict(good, ratified_judgment={"nature": "single_derivation", "ruling": "N-235"})):
        c = ac._check_contribution("Carr.D3", "L0", bad, None)
        assert c["v"] == ac.NO_DET and "N-235" in c["reason"], c
        assert ac._na_released("Carr.D3", bad) is False


def test_the_rule_applies_to_the_carr_criteria_only():
    forged = dict(ac._na("x", "ratified_judgment"), ratified_judgment={"nature": "ratified_judgment", "ruling": "N-235"})
    assert ac.ratified_judgment_na_problem("Idem.pattern", forged) is None                       # not this guard's criterion
    c = ac._check_contribution("Idem.pattern", "L0", forged, None)
    assert c["v"] == ac.NO_DET                                                                    # and not a registered cause of it either: never honoured


def test_a_ratified_judgment_with_another_ruling_id_validates_but_is_not_released_by_the_n235_rule():
    rec = _checks(dict(CAR, ruling="N-77"))
    assert ac._check_contribution("Carr.D1", "L0", rec["Carr.D1"], None)["v"] == ac.NO_DET


# ───────────────────────── certification: the ceiling is named, non-blocking, and checked ─────────────────────────

def test_ratified_judgment_cells_certify_at_a_named_ceiling(tmp_path):
    cells = good_cells(**{"Carr.D1": eng(RULES[0]), "Carr.D2": eng(RULES[1]), "Carr.D3": eng(RULES[2])})
    rc, out = run(world(tmp_path, {"a1": cells}), tmp_path)
    cert = {c["asset"]: c for c in json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"]}
    assert "a1" in cert and cert["a1"]["ceilings"] == ["Ratified judgment (N-235)"] and cert["a1"]["ruled_na"] == 3
    assert "Ratified judgment (N-235) 1)" in (out / "CERTIFIED_LIST.md").read_text()


@pytest.mark.parametrize("variant", ["no-detector", "wrong-decision", "wrong-criterion"])
def test_FORGERY_an_unbacked_ratified_cell_blocks_certification(tmp_path, variant):
    if variant == "no-detector":
        bad = dict(cell("Carr.D3", "NO_DETECTOR"), rule_id=RULES[2], decision=cp.engine_rule_decisions()[RULES[2]])
    elif variant == "wrong-decision":
        bad = cell("Carr.D3", "N/A", rule_id=RULES[2], decision="N-235")
    else:
        bad = eng(RULES[0], name="Carr.D3")
    rc, out = run(world(tmp_path, {"a1": good_cells(**{"Carr.D3": bad})}), tmp_path)
    assert "a1" in json.loads((out / "FIX_LIST.json").read_text())["fix_list"]
