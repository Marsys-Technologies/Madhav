"""E6.3 delta-review fixes (c00564256): the registry floor was a COUNT (swap one criterion for another and the count
holds), a gap could vanish by re-keying its kind/criterion or by a fold, plus the cheap LOW items. Each test fails
against the reviewed commit and has a mutant in the mutation run."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from _e6_3_fixtures import (GENERATOR, MINI_CENSUS, World, cert, disp, gap, inval, load_tracker,  # noqa: E402
                            mini_patch)

T = load_tracker()
REAL_FLOOR = dict(T.E63_REQUIRED_FLOOR)
REAL_PINS = dict(T.E63_REQUIRED_CRITERIA)
ALL = {"ga_alpha", "bg_beta", "ka_gamma"}


@pytest.fixture(autouse=True)
def _mini(monkeypatch):
    mini_patch(monkeypatch, T)


@pytest.fixture
def real_pins(monkeypatch):
    monkeypatch.setattr(T, "E63_REQUIRED_FLOOR", REAL_FLOOR)
    monkeypatch.setattr(T, "E63_REQUIRED_CRITERIA", REAL_PINS)


@pytest.fixture
def w(tmp_path):
    return World(tmp_path).default()


def raises(w, code=None, needle=None):
    w.commit()
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    if code:
        assert e.value.code == code, e.value
    if needle:
        assert needle in str(e.value), e.value
    return e.value


def got(w):
    w.commit()
    return w.elevated(T)


# ═══════════════ HIGH: pinned criterion ids, not just a count ═══════════════

def _swap(old_line_start, new_line):
    out = []
    for ln in MINI_CENSUS.split("\n"):
        out.append(new_line if ln.strip().startswith(old_line_start) else ln)
    return "\n".join(out)


def test_probe1_adding_a_criterion_and_deleting_a_pinned_one_keeps_the_count_but_raises_naming_the_id(tmp_path):
    extra = '    "Idem.second": dict(gate="Idem", check="second", detector="census", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),'
    census = _swap('"Idem.pat"', extra)                                  # Idem still has TWO criteria: the count floor holds
    w = World(tmp_path, census=census).default()
    raises(w, "registry_below_floor", "Idem.pat")


def test_probe2_renaming_a_pinned_criterion_raises_naming_it(tmp_path):
    renamed = '    "Idem.alt9": dict(gate="Idem", check="alt9", detector="census", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),'
    w = World(tmp_path, census=_swap('"Idem.alt"', renamed)).default()
    raises(w, "registry_below_floor", "Idem.alt")


def test_a_pinned_criterion_moved_to_another_gate_raises(tmp_path):
    src = MINI_CENSUS.replace('"Idem.alt":  dict(gate="Idem",  check="alt"', '"Idem.alt":  dict(gate="Ldgr",  check="alt"')
    assert src != MINI_CENSUS
    raises(World(tmp_path, census=src).default(), "registry_below_floor", "Idem.alt")


def test_a_pinned_criterion_re_layered_to_fewer_layers_raises(tmp_path):
    src = MINI_CENSUS.replace('"Idem.alt":  dict(gate="Idem",  check="alt",  detector="census", layers=ALL_LAYERS',
                              '"Idem.alt":  dict(gate="Idem",  check="alt",  detector="census", layers=("L1", "L2")')
    assert src != MINI_CENSUS
    raises(World(tmp_path, census=src).default(), "registry_below_floor", "Idem.alt")


def test_a_pinned_gate_no_longer_in_cell_gates_raises_from_the_pins_alone(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "E63_REQUIRED_FLOOR", {g: n for g, n in dict(T.E63_REQUIRED_FLOOR).items() if g != "Null"})
    src = MINI_CENSUS.replace('CELL_GATES = ("Ldgr", "Idem", "Null", "Build")', 'CELL_GATES = ("Ldgr", "Idem", "Build")')
    assert src != MINI_CENSUS
    e = raises(World(tmp_path, census=src).default(), "registry_below_floor", "pinned gate")
    assert "Null" in str(e)


def test_the_count_floor_is_a_second_check_that_fires_when_it_exceeds_the_pins(tmp_path, monkeypatch):
    # pins name Idem.alt + Idem.pat (all present); a floor of 3 for Idem makes the registry's two criteria too few
    monkeypatch.setattr(T, "E63_REQUIRED_FLOOR", dict(T.E63_REQUIRED_FLOOR, Idem=3))
    e = raises(World(tmp_path).default(), "registry_below_floor", "floor of 3")
    assert "Idem" in str(e)


def test_adding_a_criterion_is_fine_and_only_adds_a_requirement(tmp_path):
    extra = '    "Idem.extra": dict(gate="Idem", check="extra", detector="census", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1),\n'
    census = MINI_CENSUS.replace('    "Null.x":', extra + '    "Null.x":', 1)
    w = World(tmp_path, census=census).default()
    # no raise; nobody has a certificate for the new criterion, so nobody but the terminal asset is elevated
    assert got(w) == {"ka_gamma"}
    w.certs += [cert("ga_alpha", "Idem.extra"), cert("bg_beta", "Idem.extra")]
    assert got(w) == ALL


ALLOWED_EXTRAS = {"Carr": ("Carr.detector",)}      # real core-gate ids that are deliberately NOT pinned (retired by #2856)


def _real_ac():
    import importlib.util, pathlib
    path = pathlib.Path(__file__).resolve().parents[1] / "asset_census.py"
    spec = importlib.util.spec_from_file_location("asset_census_for_pins", path)
    ac = importlib.util.module_from_spec(spec)
    sys.modules["asset_census_for_pins"] = ac
    spec.loader.exec_module(ac)
    return ac


def test_the_pins_are_a_subset_of_the_real_core_gate_ids_and_every_unpinned_id_is_a_listed_extra(real_pins):
    ac = _real_ac()
    today = {g: set(c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == g) for g in ac.CELL_GATES}
    for g, ids in REAL_PINS.items():
        assert set(ids) <= today[g], g
        assert set(today[g]) - set(ids) == set(ALLOWED_EXTRAS.get(g, ())), g
    assert all(set(e["layers"]) == set(T.E63_PINNED_LAYERS) for e in ac.CRITERION_REGISTRY.values() if e["gate"] in ac.CELL_GATES)
    assert REAL_PINS["Carr"] == ("Carr.D1", "Carr.D2", "Carr.D3") and REAL_FLOOR["Carr"] == 3


E6_CARR = "/Users/Dev/suvarna-engine-lane-e6-carr/platform/scripts/governance/asset_census.py"


def test_the_real_pins_hold_on_the_registry_with_carr_detector_retired_2856(tmp_path, real_pins):
    """suvarna/engine-E6-carr (#2856) retires Carr.detector (REGISTRY_REVISION 8+): the function must not raise on it."""
    if not os.path.exists(E6_CARR):
        pytest.skip("the engine-E6-carr worktree is not on this machine")
    src = open(E6_CARR, encoding="utf-8").read()
    assert '    "Carr.detector": dict(\n        retired_in_revision=' in src           # it really is the retired form
    w = World(tmp_path, census=src).default()
    w.commit()
    facts = T._e63_registry_facts(str(w.repo), w.last)
    assert "Carr.detector" not in facts.criteria and {"Carr.D1", "Carr.D2", "Carr.D3"} <= set(facts.criteria)


def test_a_registry_that_still_has_carr_detector_just_requires_one_more_criterion(tmp_path, real_pins):
    ac = _real_ac()
    import pathlib
    src = (pathlib.Path(ac.__file__)).read_text(encoding="utf-8")
    w = World(tmp_path, census=src).default()
    w.commit()
    facts = T._e63_registry_facts(str(w.repo), w.last)
    assert "Carr.detector" in facts.required("L1")["Carr"] and len(facts.required("L1")["Carr"]) == 4


def test_real_registry_replacing_carr_d1_by_carr_d9_raises_although_the_count_is_unchanged(tmp_path, real_pins):
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "asset_census.py").read_text(encoding="utf-8")
    marker = '    "Carr.D1":'
    assert src.index(marker) < src.index("NA_CAUSES")            # the first occurrence is the CRITERION_REGISTRY entry
    w = World(tmp_path, census=src.replace(marker, '    "Carr.D9":', 1)).default()
    raises(w, "registry_below_floor", "Carr.D1")


# ═══════════════ MED: a gap cannot change what it is about ═══════════════

def test_a_later_row_re_keying_an_open_core_gate_gap_to_opportunity_raises(w):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="G1"), gap("ga_alpha", "Idem.pat", gap_id="G1", kind="opportunity")]
    raises(w, "malformed", "G1")


def test_a_later_row_moving_an_open_core_gate_gap_to_a_non_gate_family_raises(w):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="G1"), gap("ga_alpha", "Cost.base", gap_id="G1")]
    raises(w, "malformed", "G1")


def test_a_later_row_changing_only_the_state_is_still_a_normal_closure(w):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="G1"), gap("ga_alpha", "Idem.pat", gap_id="G1", state="CLOSED")]
    assert got(w) == ALL


@pytest.mark.parametrize("target", [
    dict(criterion="Idem.pat", kind="opportunity"),          # same asset, an opportunity row
    dict(criterion="Cost.base", kind="gap"),                 # same asset, a non-gate family
    dict(criterion="Ldgr.src", kind="gap"),                  # another GATE
    dict(criterion="Idem.pat", kind="info"),
])
def test_folding_an_open_core_gate_gap_into_a_row_that_cannot_block_or_is_another_gate_raises(w, target):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="G1", superseded_by="G2"),
               gap("ga_alpha", target["criterion"], gap_id="G2", kind=target["kind"], state="CLOSED")]
    raises(w, "malformed")


def test_a_fold_inside_one_gate_and_a_fold_of_a_non_blocking_row_are_allowed(w):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="G1", superseded_by="G2"), gap("ga_alpha", "Idem.alt", gap_id="G2")]
    assert got(w) == ALL - {"ga_alpha"}                       # the terminal row (open, Idem) still blocks
    w.gaps += [gap("ga_alpha", "Cost.base", gap_id="C1", superseded_by="C2"), gap("ga_alpha", "Reach.f", gap_id="C2", kind="opportunity")]
    assert got(w) == ALL - {"ga_alpha"}


def test_the_real_gap_ledgers_folds_and_duplicate_ids_still_parse(real_pins):
    import subprocess
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    r = subprocess.run(["git", "-C", repo, "show", "origin/campaign/nikasha-test:00_ARCHITECTURE/control/asset_gaps.jsonl"],
                       capture_output=True)
    if r.returncode != 0:
        pytest.skip("origin/campaign/nikasha-test is not fetched here")
    sha = T._e63_resolve_ref("HEAD", repo)
    known = set(T._e63_registry_assets(repo, sha))
    facts = T._e63_registry_facts(repo, sha)
    assert len(T._e63_parse_gaps(r.stdout, known, facts, {})) > 700


# ═══════════════ LOW ═══════════════

def test_a_list_valued_gap_asset_raises_the_dedicated_error_not_a_type_error(w):
    w.gaps.append(gap(["ga_alpha"], "Idem.pat"))
    raises(w, "malformed")


@pytest.mark.parametrize("reason", ["​", "​‍ ﻿", "­"])
def test_a_retire_reason_of_only_invisible_characters_does_not_make_it_terminal(w, reason):
    w.disps = [d for d in w.disps if d["asset"] != "ka_gamma"] + [disp("ka_gamma", "retire", reason=reason)]
    assert got(w) == ALL - {"ka_gamma"}


def test_an_event_that_also_carries_certificate_fields_is_an_invalid_line_not_a_certificate(w):
    row = cert("ga_alpha", "Ldgr.src", gen=2)
    row["type"] = "invalidation"                              # a complete certificate record that also names an event type
    w.tail_certs.append(row)
    raises(w, "malformed")


def test_the_registry_seed_parser_is_the_one_committed_at_the_ref(w):
    w.raw["00_ARCHITECTURE/control/generate_level_map.py"] = None      # the tool is absent at the ref (present in the working tree)
    raises(w, "unreadable")


def test_a_generator_committed_at_the_ref_that_cannot_load_raises(w):
    w.raw["00_ARCHITECTURE/control/generate_level_map.py"] = "raise RuntimeError('broken tool')\n"
    raises(w, "registry_unreadable")


def test_the_committed_generator_not_the_working_trees_reads_the_seed(w):
    # a committed parser that sees an EMPTY registry makes every disposition's asset unknown, whatever the checkout holds
    src = open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", GENERATOR), encoding="utf-8").read()
    w.raw[GENERATOR] = src.replace("    return rows\n\n\ndef load_registry_from_seed", "    return []\n\n\ndef load_registry_from_seed")
    assert w.raw[GENERATOR] != src
    raises(w)


# ═══════════════ final delta: a fold cannot hide an OPEN gap ═══════════════

@pytest.mark.parametrize("target_crit,target_state", [
    ("Idem.alt", "CLOSED"), ("Idem.alt", "WITHDRAWN"),       # an open gap vanishing into a closed registered row
    ("Idem.zzz", "WITHDRAWN"), ("Idem.zzz", "OPEN"),          # an unregistered id of the same gate family
    ("Ldgr.src", "OPEN"),                                     # an OPEN registered row of ANOTHER gate
])
def test_folding_an_open_core_gate_gap_into_a_closed_or_unregistered_row_of_the_same_gate_raises(w, target_crit, target_state):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="G1", superseded_by="G2"),
               gap("ga_alpha", target_crit, gap_id="G2", state=target_state)]
    raises(w, "malformed")


def test_a_closed_origin_may_fold_into_a_closed_row_and_an_open_fold_into_an_open_registered_row_still_blocks(w):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="G1", superseded_by="G2", state="CLOSED"),
               gap("ga_alpha", "Idem.alt", gap_id="G2", state="CLOSED")]
    assert got(w) == ALL
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="H1", superseded_by="H2"), gap("ga_alpha", "Idem.alt", gap_id="H2")]
    assert got(w) == ALL - {"ga_alpha"}


def test_a_chain_whose_terminal_row_is_closed_cannot_hide_an_open_origin(w):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="A", superseded_by="B"), gap("ga_alpha", "Idem.alt", gap_id="B", superseded_by="C"),
               gap("ga_alpha", "Idem.alt", gap_id="C", state="CLOSED")]
    raises(w, "malformed")


def _with_addition(w, name="Reach.new"):
    w.disps.append(disp("ga_alpha", "keep", additions=[name]))
    w.certs.append(cert("ga_alpha", name, kind="addition"))


def test_an_open_gap_on_an_addition_in_an_info_family_blocks(w):
    _with_addition(w)
    w.gaps.append(gap("ga_alpha", "Reach.new"))
    assert got(w) == ALL - {"ga_alpha"}


@pytest.mark.parametrize("target", [dict(criterion="Cost.base", kind="gap", state="CLOSED"),
                                    dict(criterion="Cost.base", kind="opportunity", state="OPEN"),
                                    dict(criterion="Reach.other", kind="gap", state="CLOSED"),
                                    dict(criterion="Reach.new", kind="opportunity", state="OPEN")])
def test_folding_an_open_gap_on_a_declared_info_family_addition_into_a_row_that_cannot_block_raises(w, target):
    _with_addition(w)
    w.gaps += [gap("ga_alpha", "Reach.new", gap_id="G1", superseded_by="G2"),
               gap("ga_alpha", target["criterion"], gap_id="G2", kind=target["kind"], state=target["state"])]
    raises(w, "malformed")


def test_an_addition_gap_may_fold_into_another_open_row_of_the_same_addition(w):
    _with_addition(w)
    w.gaps += [gap("ga_alpha", "Reach.new", gap_id="G1", superseded_by="G2"), gap("ga_alpha", "Reach.new.sub", gap_id="G2")]
    assert got(w) == ALL - {"ga_alpha"}


def test_an_open_addition_gap_folded_into_a_closed_row_of_the_same_addition_is_refused(w):
    _with_addition(w)
    w.gaps += [gap("ga_alpha", "Reach.new", gap_id="G1", superseded_by="G2"),
               gap("ga_alpha", "Reach.new.sub", gap_id="G2", state="CLOSED")]
    raises(w, "malformed", "OPEN gap")


def test_a_non_gate_family_gap_with_no_such_addition_folds_freely(w):
    w.gaps += [gap("ga_alpha", "Reach.new", gap_id="G1", superseded_by="G2"), gap("ga_alpha", "Cost.base", gap_id="G2", state="CLOSED")]
    assert got(w) == ALL                                       # Reach.new is NOT a declared addition here: informational


E6_CARR_CENSUS = "/Users/Dev/suvarna-engine-lane-e6-carr/platform/scripts/governance/asset_census.py"


def test_the_real_gap_ledger_also_parses_against_the_registry_with_carr_detector_retired(tmp_path, real_pins):
    import subprocess
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    r = subprocess.run(["git", "-C", repo, "show", "origin/campaign/nikasha-test:00_ARCHITECTURE/control/asset_gaps.jsonl"],
                       capture_output=True)
    if r.returncode != 0 or not os.path.exists(E6_CARR_CENSUS):
        pytest.skip("origin/campaign/nikasha-test or the engine-E6-carr worktree is not available here")
    w = World(tmp_path, census=open(E6_CARR_CENSUS, encoding="utf-8").read()).default()
    w.commit()
    facts = T._e63_registry_facts(str(w.repo), w.last)
    known = set(T._e63_registry_assets(repo, T._e63_resolve_ref("HEAD", repo)))        # the real seed's asset ids
    assert len(T._e63_parse_gaps(r.stdout, known, facts, {})) > 700
