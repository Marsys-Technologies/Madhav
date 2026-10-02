"""E6.3 review fixes: every fail-open path an independent review found in e2de9520d, each as a test that fails against
the old behaviour and passes now (and a mutant in the mutation run). The rule being protected: `elevated_assets`
either answers truthfully or RAISES; a malformed, forged or unreadable input never turns into "not blocked".

  1  gap rows attach by a raw asset string -> the asset must be well formed AND known, else raise
  2  supersede folds crossed assets and ignored chains -> keyed (asset, gap_id), same asset, chains, cycles raise
  3  registry parser trusted a literal that could be reassigned/mutated -> whole-module walk; floor; layers=()
  4  dispositions' `additions` could be dropped by a later row -> required key, union across rows
  5  duplicate JSON keys, missing cross_checked, E5.1 hash chain / seq
  6  the PARTIAL cap is read from the parsed census source, not a copy
  7  criterion_version type, addition detector spelling, retire for an unregistered asset, declaration basis,
     a core-gate gap re-keyed to info
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from _e6_3_fixtures import (CENSUS, CERTS, DISP, GAPS, MINI_CENSUS, MINI_FLOOR, mini_patch, NA_NULL, SEED, World, cert,  # noqa: E402
                            chained, disp, gap, inval, jsonl, load_tracker, sha, watermark)

T = load_tracker()
REAL_FLOOR = dict(T.E63_REQUIRED_FLOOR)
REAL_PINS = dict(T.E63_REQUIRED_CRITERIA)
ALL = {"ga_alpha", "bg_beta", "ka_gamma"}


@pytest.fixture(autouse=True)
def mini_floor(monkeypatch):
    mini_patch(monkeypatch, T)


@pytest.fixture
def real_floor(monkeypatch):
    monkeypatch.setattr(T, "E63_REQUIRED_FLOOR", REAL_FLOOR)
    monkeypatch.setattr(T, "E63_REQUIRED_CRITERIA", REAL_PINS)


@pytest.fixture
def w(tmp_path):
    return World(tmp_path).default()


def got(w):
    w.commit()
    return w.elevated(T)


def raises(w, code=None):
    w.commit()
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    if code:
        assert e.value.code == code, e.value
    return e.value


# ═══════════════ 1. gap rows attach only to a well-formed, known asset ═══════════════

@pytest.mark.parametrize("asset", ["GA_alpha", "ga_alpha ", " ga_alpha", "ga_alpha\n", "gа_alpha", "ga-alpha",
                                   "ga_alpha​", "ga_nothing"])
def test_1_a_gap_row_on_a_lookalike_or_unknown_asset_raises_instead_of_being_ignored(w, asset):
    w.gaps.append(gap(asset, "Idem.pat"))
    raises(w, "malformed")


def test_1_the_layer_wide_pseudo_asset_is_the_one_allowed_exception_and_blocks_nobody(w):
    w.gaps.append(gap("_layer_all", "Build.diagnosability", gap_id="_layer_all-BT01"))
    assert got(w) == ALL


def test_1_a_known_registry_asset_with_no_certificates_may_carry_gaps(w):
    w.seed_extra = {"ka_pending": "data"}
    w.gaps.append(gap("ka_pending", "Idem.pat"))
    assert got(w) == ALL


def test_1_a_non_string_asset_raises(w):
    w.gaps.append(gap(7, "Idem.pat"))
    raises(w, "malformed")


# ═══════════════ 2. supersede folds: same asset, chains, cycles ═══════════════

def test_2_a_later_closed_row_of_another_asset_reusing_the_gap_id_does_not_erase_an_open_gap(w):
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="G1"))
    w.gaps.append(gap("bg_beta", "Ldgr.src", gap_id="G1", state="CLOSED"))
    assert got(w) == ALL - {"ga_alpha"}


def test_2_a_fold_into_another_assets_gap_raises(w):
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="G1", superseded_by="G2"))
    w.gaps.append(gap("bg_beta", "Ldgr.src", gap_id="G2", state="CLOSED"))
    raises(w, "malformed")


def test_2_a_chain_takes_the_state_of_its_terminal_target_open(w):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="A", superseded_by="B", state="CLOSED"),
               gap("ga_alpha", "Idem.pat", gap_id="B", superseded_by="C", state="CLOSED"),
               gap("ga_alpha", "Idem.pat", gap_id="C")]
    assert got(w) == ALL - {"ga_alpha"}


def test_2_a_chain_into_a_closed_terminal_row_cannot_hide_an_open_origin(w):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="A", superseded_by="B"),
               gap("ga_alpha", "Idem.pat", gap_id="B", superseded_by="C"),
               gap("ga_alpha", "Idem.pat", gap_id="C", state="CLOSED")]
    raises(w, "malformed")


def test_2_a_closed_chain_into_a_closed_terminal_row_is_fine(w):
    w.gaps += [gap("ga_alpha", "Idem.pat", gap_id="A", superseded_by="B", state="CLOSED"),
               gap("ga_alpha", "Idem.pat", gap_id="B", superseded_by="C", state="CLOSED"),
               gap("ga_alpha", "Idem.pat", gap_id="C", state="CLOSED")]
    assert got(w) == ALL


@pytest.mark.parametrize("rows", [
    [("A", "B"), ("B", "A")], [("A", "A")], [("A", "B"), ("B", "C"), ("C", "A")],
])
def test_2_a_supersede_cycle_raises(w, rows):
    for gid, sup in rows:
        w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id=gid, superseded_by=sup, state="CLOSED"))
    raises(w, "malformed")


def test_2_a_fold_whose_target_does_not_exist_raises(w):
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="A", superseded_by="NOPE", state="CLOSED"))
    raises(w, "malformed")


# ═══════════════ 3. the registry parser cannot be fooled by a rewritten literal ═══════════════

def _census_with(extra="", *, replace=None):
    src = MINI_CENSUS
    if replace:
        old, new = replace
        assert old in src, old
        src = src.replace(old, new)
    return src + extra


@pytest.mark.parametrize("extra", [
    'CRITERION_REGISTRY = {}\n',                                               # a second assignment
    'CELL_GATES = ("Ldgr",)\n',
    'NA_RULE_DECISIONS = {"Null.x#columns_any": "N-22a", "Idem.pat#columns_any": "N-99"}\n',
    'LAYERS = {}\n',
    'CRITERION_REGISTRY["Idem.pat"] = dict(gate="Idem", layers=("L9",), detector="x", revision=2)\n',
    'CRITERION_REGISTRY["Idem.pat"]["layers"] = ()\n',
    'CRITERION_REGISTRY.update({})\n',
    'CRITERION_REGISTRY.pop("Idem.alt")\n',
    'CRITERION_REGISTRY.setdefault("Idem.z", {})\n',
    'CRITERION_REGISTRY.clear()\n',
    'del CRITERION_REGISTRY["Idem.alt"]\n',
    'del NA_RULE_DECISIONS\n',
    'CELL_GATES += ("Zzz",)\n',
    'NA_RULE_DECISIONS |= {"x#y": "z"}\n',
    'NA_RULE_DECISIONS["Idem.pat#columns_any"] = "N-99"\n',
    'LAYERS["L1"]["prefix"] = "zz_"\n',
    'LAYERS.pop("L5")\n',
    'alias = CRITERION_REGISTRY\nalias["x"] = 1\n',
    'globals()["CRITERION_REGISTRY"] = {}\n',
    'setattr(__import__("sys").modules[__name__], "CELL_GATES", ())\n',
    'exec("CELL_GATES = ()")\n',
    'def CELL_GATES():\n    pass\n',
    'class LAYERS:\n    pass\n',
    'import os as CRITERION_REGISTRY\n',
    'def f():\n    global CELL_GATES\n    CELL_GATES = ()\n',
    'for CELL_GATES in [()]:\n    pass\n',
    '(NA_RULE_DECISIONS := {})\n',
])
def test_3_a_registry_name_that_is_reassigned_mutated_aliased_or_written_dynamically_raises(tmp_path, extra):
    w = World(tmp_path).default()
    w.census = _census_with(extra)
    raises(w, "registry_unreadable")


def test_3_the_unmodified_mini_registry_is_accepted(w):
    assert got(w) == ALL


def test_3_a_function_local_variable_with_an_unrelated_name_is_not_a_false_positive(tmp_path):
    w = World(tmp_path).default()
    w.census = _census_with("def f(layers):\n    registry = {}\n    registry['x'] = 1\n    return CRITERION_REGISTRY.get('x')\n")
    assert got(w) == ALL


@pytest.mark.parametrize("old,new", [
    ('layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=2)', 'layers=(), columns_any=None, asset_kinds=None, revision=2)'),
    ('layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=2)', 'layers=("L9",), columns_any=None, asset_kinds=None, revision=2)'),
    ('layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=2)', 'layers=[], columns_any=None, asset_kinds=None, revision=2)'),
])
def test_3_an_entry_with_empty_or_undeclared_layers_raises(tmp_path, old, new):
    w = World(tmp_path).default()
    w.census = _census_with(replace=(old, new))
    raises(w, "registry_unreadable")


def test_3_removing_a_core_gate_criterion_falls_below_the_pinned_floor_and_raises(tmp_path):
    w = World(tmp_path).default()
    src = "\n".join(ln for ln in MINI_CENSUS.split("\n") if not ln.strip().startswith('"Idem.alt"'))
    assert src != MINI_CENSUS
    w.census = src
    e = raises(w, "registry_below_floor")
    assert "floor" in str(e)


def test_3_the_floor_names_a_gate_the_registry_no_longer_has_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "E63_REQUIRED_FLOOR", dict(MINI_FLOOR, Zzz=1))
    raises(World(tmp_path).default(), "registry_below_floor")


def test_3_the_pinned_floor_is_met_by_the_real_registry_and_equals_it_but_for_the_listed_extras(real_floor):
    """The floor is derived from the real registry at origin/main, less the criteria a pending PR retires (Carr.detector,
    #2856): every (layer, gate) count is >= the floor, and exceeds it only by the listed extras."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import importlib.util, pathlib
    path = pathlib.Path(__file__).resolve().parents[1] / "asset_census.py"
    spec = importlib.util.spec_from_file_location("asset_census_for_floor", path)
    ac = importlib.util.module_from_spec(spec)
    sys.modules["asset_census_for_floor"] = ac
    spec.loader.exec_module(ac)
    extras = {"Carr": 1}
    for layer in ac.LAYERS:
        counts = {g: sum(1 for e in ac.CRITERION_REGISTRY.values() if e["gate"] == g and layer in e["layers"])
                  for g in ac.CELL_GATES}
        assert all(REAL_FLOOR[g] <= counts[g] <= REAL_FLOOR[g] + extras.get(g, 0) for g in REAL_FLOOR), (layer, counts)


def test_3_the_real_registry_passes_the_floor_and_the_whole_module_walk(tmp_path, real_floor):
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "asset_census.py").read_text(encoding="utf-8")
    w = World(tmp_path, census=src).default()
    w.commit()
    facts = T._e63_registry_facts(str(w.repo), w.last)
    assert len(facts.criteria) > 20 and facts.cap_prefixes == {"Null."} and facts.cap_exact == {"Narr.fidelity_test"}


def test_3_dropping_a_real_core_gate_criterion_raises_against_the_real_floor(tmp_path, real_floor):
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "asset_census.py").read_text(encoding="utf-8")
    lines = src.split("\n")
    i = next(k for k, ln in enumerate(lines) if ln.lstrip().startswith('"Narr.lint"'))
    del lines[i]
    w = World(tmp_path, census="\n".join(lines)).default()
    raises(w, "registry_below_floor")


# ═══════════════ 4. dispositions: `additions` is required and cumulative ═══════════════

def test_4_a_disposition_row_without_additions_raises(w):
    row = disp("ga_alpha", "keep")
    del row["additions"]
    w.disps.append(row)
    raises(w, "malformed")


def test_4_a_later_row_without_the_declaration_cannot_un_declare_an_addition(w):
    w.disps.append(disp("ga_alpha", "keep", additions=["D-TIME"]))           # declared, never certified
    assert got(w) == ALL - {"ga_alpha"}
    w.disps.append(disp("ga_alpha", "enrich", additions=[]))                  # a later row that lists none
    assert got(w) == ALL - {"ga_alpha"}


def test_4_additions_accumulate_across_rows(w):
    w.disps.append(disp("ga_alpha", "keep", additions=["D-TIME"]))
    w.disps.append(disp("ga_alpha", "keep", additions=["D-SALIENCE"]))
    w.certs.append(cert("ga_alpha", "D-TIME", kind="addition"))
    assert got(w) == ALL - {"ga_alpha"}                                       # D-SALIENCE is still declared, uncertified
    w.certs.append(cert("ga_alpha", "D-SALIENCE", kind="addition"))
    assert got(w) == ALL


# ═══════════════ 5. strict JSON, cross_checked, the E5.1 hash chain ═══════════════

def _last_line_with(w, path, mutate_text):
    """Re-render `path` with ONLY its last row's text changed by `mutate_text(text)`: nothing after it can break the
    chain, so the single defect under test is the only one in the file."""
    w.gaps.append(gap("ga_alpha", "Cost.base"))                      # so every ledger has a row to change
    lines = w.render()[path].rstrip("\n").split("\n")
    lines[-1] = mutate_text(lines[-1])
    w.raw[path] = "\n".join(lines) + "\n"


@pytest.mark.parametrize("path", [CERTS, GAPS, DISP])
def test_5_a_duplicate_key_in_any_ledger_row_raises_even_with_an_identical_value(w, path):
    def dup(text):
        asset = json.loads(text)["asset"]
        return text[:-1] + ", \"asset\": " + json.dumps(asset) + "}"
    _last_line_with(w, path, dup)
    raises(w, "malformed")


def test_5_the_same_rows_without_the_duplicate_are_accepted(w):
    w.gaps.append(gap("ga_alpha", "Cost.base"))
    assert got(w) == ALL


def test_5_a_duplicate_key_inside_a_nested_object_raises(w):
    _last_line_with(w, CERTS, lambda t: t.replace('"commit"', '"commit": "x", "commit"', 1))
    raises(w, "malformed")


@pytest.mark.parametrize("path", [CERTS, GAPS, DISP])
def test_5_a_non_finite_number_raises(w, path):
    _last_line_with(w, path, lambda t: t[:-1] + ', "x": NaN}')
    raises(w, "malformed")


@pytest.mark.parametrize("path", [CERTS, GAPS, DISP])
def test_5_absurd_nesting_raises(w, path):
    _last_line_with(w, path, lambda t: t[:-1] + ', "x": ' + "[" * 80 + "]" * 80 + "}")
    raises(w, "malformed")


def test_5_reasonable_nesting_is_fine(w):
    _last_line_with(w, CERTS, lambda t: t[:-1] + ', "x": ' + "[" * 10 + "]" * 10 + "}")
    assert got(w) == ALL


def test_5_a_gate_record_without_cross_checked_true_raises(w):
    w.find("ga_alpha", "Idem.pat").pop("cross_checked")
    raises(w, "malformed")


@pytest.mark.parametrize("val", [False, None, "true", 1])
def test_5_a_gate_record_with_cross_checked_not_exactly_true_raises(w, val):
    w.find("ga_alpha", "Idem.pat")["cross_checked"] = val
    raises(w, "malformed")


def test_5_an_addition_record_needs_no_cross_check(w):
    assert w.find("bg_beta", "D-GROUNDING", "addition")["cross_checked"] is False
    assert got(w) == ALL


def _lines(w):
    return w.certs_text().rstrip("\n").split("\n")


def test_5_chain_an_edited_earlier_line_breaks_the_chain(w):
    lines = _lines(w)
    rec = json.loads(lines[2])
    rec["verified_by"] = "someone-else"                        # any edit of an earlier line
    lines[2] = json.dumps(rec, ensure_ascii=False)
    w.raw[CERTS] = "\n".join(lines) + "\n"
    e = raises(w, "malformed")
    assert "chain" in str(e)


def test_5_chain_a_deleted_line_breaks_it(w):
    lines = _lines(w)
    del lines[3]
    w.raw[CERTS] = "\n".join(lines) + "\n"
    raises(w, "malformed")


def test_5_chain_reordered_lines_break_it(w):
    lines = _lines(w)
    lines[2], lines[3] = lines[3], lines[2]
    w.raw[CERTS] = "\n".join(lines) + "\n"
    raises(w, "malformed")


def test_5_chain_a_wrong_seq_raises(w):
    for bad in (5, 1, 0, None, True, "2"):                       # row 1 must carry seq 2 (1 is the next-but-one's)
        rows = w.ledger_rows()
        rows[1]["seq"] = bad
        w.raw[CERTS] = chained(rows)
        raises(w, "malformed")


def test_5_chain_a_missing_seq_raises(w):
    lines = _lines(w)
    rec = json.loads(lines[2])
    del rec["seq"]
    lines[2] = json.dumps(rec, ensure_ascii=False)
    w.raw[CERTS] = "\n".join(lines) + "\n"
    raises(w, "malformed")


def test_5_chain_a_missing_or_wrong_prev_sha256_raises(w):
    for bad in (None, "0" * 64, 5):
        rows = w.ledger_rows()
        rows[2]["prev_sha256"] = bad
        w.raw[CERTS] = chained(rows)
        raises(w, "malformed")


def test_5_chain_the_first_record_chains_from_the_schema_row_bytes(w):
    lines = _lines(w)
    assert json.loads(lines[1])["prev_sha256"] == sha(lines[0].encode())
    assert got(w) == ALL


def test_5_chain_a_second_schema_row_raises(w):
    rows = w.ledger_rows()
    rows.insert(2, {"asset": "_schema", "_doc": "again"})
    w.raw[CERTS] = chained(rows)
    raises(w, "malformed")


def test_5_chain_blank_lines_are_skipped_as_in_e5_1(w):
    lines = _lines(w)
    w.raw[CERTS] = "\n".join(lines[:3] + [""] + lines[3:]) + "\n\n"
    assert got(w) == ALL


# ═══════════════ 6. the PARTIAL cap comes from the parsed census source ═══════════════

def test_6_a_cap_the_source_does_not_state_is_not_applied(tmp_path):
    """The cap is read from `_check_contribution` at the ref, not hard-coded: with the Null cap removed from the source a
    Null.x PASS is a PASS (and would be elevated), proving the tracker follows the single source."""
    src = MINI_CENSUS.replace('crit.startswith("Null.") or ', "")
    assert src != MINI_CENSUS
    w = World(tmp_path, census=src).default()
    w.find("ga_alpha", "Null.x").update(verdict="PASS", na=None)
    assert got(w) == ALL


def test_6_a_cap_the_source_states_is_applied(tmp_path):
    src = MINI_CENSUS.replace('crit == "Narr.fidelity_test"', 'crit == "Narr.fidelity_test" or crit == "Idem.alt"')
    w = World(tmp_path, census=src).default()
    assert got(w) == {"ka_gamma"}                                # Idem.alt PASS is now capped for everyone


def test_6_no_cap_rule_in_the_source_raises(tmp_path):
    src = MINI_CENSUS.replace("def _check_contribution", "def _other_function")
    raises(World(tmp_path, census=src).default(), "registry_unreadable")
    src2 = MINI_CENSUS.replace('return dict(criterion=crit, v=PARTIAL, state="MEASURED", reason="capped")',
                               'return dict(criterion=crit, v=v, state="MEASURED", reason="capped")')
    assert src2 != MINI_CENSUS
    raises(World(_sub(tmp_path, "x"), census=src2).default(), "registry_unreadable")


def _sub(tmp_path, name):
    p = tmp_path / name
    p.mkdir()
    return p


def test_6_the_real_census_states_the_cap_the_tracker_reads(tmp_path, real_floor):
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "asset_census.py").read_text(encoding="utf-8")
    assert 'crit.startswith("Null.") or crit == "Narr.fidelity_test"' in src
    w = World(tmp_path, census=src).default()
    w.commit()
    f = T._e63_registry_facts(str(w.repo), w.last)
    assert f.capped("Null.schema_default") and f.capped("Null.blank_rows") and f.capped("Narr.fidelity_test")
    assert not f.capped("Narr.lint") and not f.capped("Idem.pattern")


# ═══════════════ 7. the low-severity fail-opens ═══════════════

@pytest.mark.parametrize("version", [True, 1.0, "2", None, 0, -1])
def test_7_criterion_version_must_be_an_int_of_at_least_one(w, version):
    w.find("ga_alpha", "Idem.pat")["criterion_version"] = version
    raises(w, "malformed")


@pytest.mark.parametrize("det", ["NONE ", " none", "None", "NONE​", "ＮＯＮＥ", "N­ONE"])
def test_7_an_addition_whose_detector_is_none_in_any_spelling_is_not_a_pass(w, det):
    w.find("bg_beta", "D-GROUNDING", "addition")["detector"] = det
    assert got(w) == ALL - {"bg_beta"}


def test_7_a_gate_record_whose_detector_is_none_in_any_spelling_is_not_a_pass(w):
    w.find("ga_alpha", "Idem.pat")["detector"] = "none "
    assert got(w) == ALL - {"ga_alpha"}


@pytest.mark.parametrize("d", ["retire", "consolidate"])
def test_7_a_terminal_disposition_for_an_asset_not_in_the_registry_raises(w, d):
    w.seed_exclude = {"ka_gamma"}
    w.disps = [x for x in w.disps if x["asset"] != "ka_gamma"] + [disp("ka_gamma", d, reason="gone")]
    raises(w, "malformed")


def test_7_a_core_gate_gap_re_keyed_to_info_raises(w):
    w.gaps.append(gap("ga_alpha", "Idem.pat", kind="info", state="CLOSED"))
    raises(w, "malformed")


def test_7_a_declared_addition_gap_re_keyed_to_info_raises(w):
    w.gaps.append(gap("bg_beta", "D-GROUNDING", kind="info"))
    raises(w, "malformed")


def test_7_an_info_row_on_a_non_gate_family_is_fine(w):
    w.gaps.append(gap("ga_alpha", "Cost.base", kind="info"))
    assert got(w) == ALL


def test_7_the_declaration_table_mirrors_e5_1s():
    assert T.E63_DECLARATION_BASED == {"Build.target": ("service",)}
