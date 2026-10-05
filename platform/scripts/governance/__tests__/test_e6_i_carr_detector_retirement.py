"""test_e6_i_carr_detector_retirement.py — E6 work-list item (i): RETIRE `Carr.detector` (SS ruling A2, 2026-09-30/10-01;
N-22 proposal v1.2.3, `00_ARCHITECTURE/briefs/suvarna/N22_APPLICABILITY_PROPOSAL_v1_0.md` §E6 item i).

SS: "RETIRE it. A meta-check that reads NO_DETECTOR on all 127 duplicates what the D1-D3 checks say. Carr becomes
exactly the D1-D3 checks. Retiring it must not raise any verdict: with D1-D3 still at detector NONE the gate stays
NO_DETECTOR (this must be PROVEN in the regression)."

What is proven here, on the real rollup code (never a re-implementation of it):

  P1  the Carr cell of every one of the 127 assets is the same verdict with and without the criterion (NO_DETECTOR on
      all 127), and NO other gate cell moves (verdict AND checks identical), with the N/A rule set empty;
  P2  D1-D3 are still detector NONE: even a measured PASS on them reads NO_DETECTOR, so the retirement cannot raise Carr;
  P3  the ceiling: with `no-carriage` emitted and declared on D1-D3 for the six strict-ceiling assets, Carr reads N/A on
      exactly those six and NO_DETECTOR on the other 121; with `Carr.detector` still measured the same six read
      NO_DETECTOR (the gap A2 named);
  P4  a check that is not N/A holds the cell: one D-check left NO_DETECTOR keeps the cell NO_DETECTOR.

Plus the counts SS asked to have stated (checks per asset 4 to 3; contributions 508 to 381; check-level N/A ceiling
24 to 18), the registry/revision/fingerprint discipline, measure() no longer emitting the criterion, rollup tolerance
for a SAVED census that still carries it, and the ledger lifecycle of the retired criterion's OPEN rows.

P1-P4 run twice: on the committed verdict fixture (always) and on the saved Track A census JSONs under
/Users/Dev/suvarna-evidence/census*/ (when present on the machine).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_1_p1_registry_rollup as p1  # noqa: E402
import test_w2_1_earned_verdicts as w1  # noqa: E402

FIXTURE = json.loads((HERE / "fixtures" / "census_cells_2026-09-30.json").read_text(encoding="utf-8"))
ALL_LAYERS = ("L0", "L1", "L2", "L3", "L4", "L5")
# N-22 v1.2.3 §3.5 / `n22_v12_counts.json` ceilings.carr_ceiling_strict_assets: no DAG dependents and not served.
CEILING = ("bg_concordance", "bg_gochara_arcs", "bg_vidhi_floors", "bo_grounding", "mi_seva", "mi_vistara")
D_CHECKS = ("Carr.D1", "Carr.D2", "Carr.D3")
# the pinned revision-7 fingerprint (test_e6_1_p1_registry_rollup.PINNED_FINGERPRINTS[7]): the real predecessor
REV7_FINGERPRINT = p1.PINNED_FINGERPRINTS[7]
NARR_AGREE_REV7 = ("prose_fields declared non-empty (null = undeclared: NO_DETECTOR; [] = declared no prose: measured N/A candidate, "
                   "cause no-prose, undecided)")
NO_DET_RECORD = dict(v="NO_DETECTOR", measured="no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics")

# The registry entry exactly as it stood at REGISTRY_REVISION 7 (origin/main bf6fe712b): used ONLY to rebuild the
# pre-retirement inspector for the with/without comparison. It is deliberately NOT importable from asset_census.
OLD_CARR_DETECTOR = dict(gate="Carr", check="detector", applicability="always (the generic 'some carriage detector exists' reading)",
                         detector="asset_census.py:measure()", layers=ALL_LAYERS, columns_any=None, asset_kinds=None, revision=1)


def _assets():
    """[(layer, asset_id, measurements)] from the committed fixture (Carr.detector already removed from it)."""
    return [(L, a, dict({c: dict(v=v, measured="fixture") for c, v in ms.items()}))
            for L, assets in FIXTURE["layers"].items() for a, ms in assets.items()]


NARR_GUARD_CLAUSE = ("; an asset that declares prose_fields [] WITH a prose_coupling to carriage_d1 (NARR-GUARD, pin 16, N-94) reads N/A only while its own Carr.D1 reads PASS, else NO_DETECTOR")


E57_CHECKABLE = "; rows are scoped from a plain count_sql OR a sum of plain count subselects (one term per table), pinned to the chart by a depth-0 `chart_id = $1` conjunct (E5.7)"
E57_FIDELITY = ("structural test discovery (N.7 item 5) caps at PARTIAL; PASS only when the asset DECLARES fidelity_tests and golden_test_scan verifies each from source (the named test calls the builder "
                "and asserts the built output EQUAL to an independent literal sentence) and every declared prose entry is covered (E5.7, SS N-150 R7; the golden assertion must compare the entry's own value, picked out by its key / attribute / assigned name, with an independent literal sentence of at least 2 words and 10 characters; which column a sentence belongs to is read from that reference, not proven)")


def _restore_pre_retirement(monkeypatch):
    """Rebuild the revision-7 inspector around the real rollup code: the criterion back in the registry, nothing retired."""
    reg = dict(ac.CRITERION_REGISTRY)
    reg["Carr.detector"] = dict(OLD_CARR_DETECTOR)
    reg["Carr.D1"] = dict(reg["Carr.D1"], detector="NONE", revision=1,           # revision 11 gave Carr.D1 a detector
                          applicability="the asset restates a value from a cited source (source correspondence)")
    reg["Carr.D2"] = dict(reg["Carr.D2"], revision=1, applicability="the asset carries two independent witnesses of the same fact")        # N-156 re-worded and bumped D2 / D3
    reg["Carr.D3"] = dict(reg["Carr.D3"], detector="NONE", revision=1, applicability="the asset computes a value that a second method could re-derive")
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    monkeypatch.setattr(ac, "RETIRED_CRITERIA", {}, raising=False)
    reg["Narr.agree"] = dict(reg["Narr.agree"], revision=1, applicability=NARR_AGREE_REV7)    # its text said "undecided" until revision 9; revision 16 (NARR-GUARD) re-worded and bumped all four Narr checks
    for crit in ("Narr.checkable", "Narr.fidelity_test", "Narr.lint"):
        reg[crit] = dict(reg[crit], revision=1, applicability=re.sub(r"; N-150 R1/R2.*$", "", reg[crit]["applicability"].replace(E57_CHECKABLE, "")
                         .replace(E57_FIDELITY, "structural test discovery (N.7 item 5); never PASS").replace(NARR_GUARD_CLAUSE, "")))     # pin 26: E5.7 (checkable / fidelity) and N-150 R1/R2 (all four) re-worded and bumped them
    reg["Vocab.alias"] = dict(reg["Vocab.alias"], revision=1, applicability="the table declares an alias-bearing class census")     # revision 12 (S3) re-worded and bumped both
    reg["Ldgr.source_presence"] = dict(reg["Ldgr.source_presence"], revision=2,
                                       applicability="the target table carries a recognised citation column (R60: singular classical_citation included)")
    for crit in ("Null.schema_default", "Null.blank_rows"):       # revision 13 (S1) re-worded and bumped both
        was = "schema_default" if crit.endswith("default") else "blank_rows"
        reg[crit] = dict(reg[crit], revision=1, applicability=("prose_fields declared non-empty; a non-NULL DEFAULT on a declared prose column; never PASS alone"
                                                               if was == "schema_default" else
                                                               "prose_fields declared non-empty; blank or placeholder rows standing in for NULL; never PASS alone"))
    reg["Dens.served"] = dict(reg["Dens.served"], revision=4,                      # revision 14 (N-74(a)) re-worded and bumped it
                              applicability="reaches a served capability module; PASS (structural) needs ONE capability entry (the object literal that declares density_contract) "
                                            "whose own served read of the asset's table selects a tier column; a sibling entry, a sub-select, an INSERT...SELECT or a UNION "
                                            "branch does not count")
    reg["Build.completion"] = dict(reg["Build.completion"], revision=2, applicability="a count_sql or view target exists")     # revision 25 (N-99) re-worded and bumped it
    reg["Earn.service_state"] = dict(reg["Earn.service_state"], revision=1, detector="NONE",       # E5.7 (revision 2) gave it a real detector and re-worded it
                                     applicability="asset_kind='service' (no target_table; asset_throughput's rows_written signal cannot distinguish healthy-and-idle from broken)")
    reg["Build.count_integrity"] = dict(reg["Build.count_integrity"], revision=1, applicability="always")     # revision 26 (role reading) re-worded and bumped it
    reg["Build.dep_liveness"] = dict(reg["Build.dep_liveness"], revision=1, applicability="declares at least one depends_on")     # revision 26 (cause text) re-worded and bumped it
    reg["Build.history"] = dict(reg["Build.history"], revision=1, applicability="has been exercised at least once")     # revision 26 (SS Build.history window) re-worded and bumped it
    causes = dict(ac.NA_CAUSES)
    causes["Count.floor"] = ("target-floor-zero",)          # revision 26 (N-149) added `zero-row-convention-holds`
    causes["Narr.lint"] = ("no-prose",)                    # pin 26 (N-150 R2) added `lint-not-applicable`
    causes.pop("Earn.service_state", None)                 # revision 10 added `not-a-service`; revision 7 had no cause there
    causes.pop("Vocab.alias", None)                        # revision 12 (S3) added the two declaration-keyed causes
    causes.pop("Ldgr.source_presence", None)
    for c in D_CHECKS:                                      # revision 11 added the two declaration-keyed Carr causes (N-156 added one ceiling cause each)
        causes[c] = ("no-carriage",)
    monkeypatch.setattr(ac, "NA_CAUSES", causes)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {})      # revision 7 declared no rule (revision 9 declares three: they are fingerprinted)


def _no_carriage_causes(monkeypatch):
    """E6 item (f) (merged, REGISTRY_REVISION 7) registers the cause `no-carriage` for D1-D3; here only the RULE
    declarations are emulated (NA_RULE_DECISIONS is {} in the repo until SS approves them). The cause itself is asserted,
    not re-injected, so a change to NA_CAUSES cannot hide behind this helper."""
    assert all("no-carriage" in ac.NA_CAUSES.get(c, ()) for c in D_CHECKS)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {f"{c}#measured:no-carriage": "N-22 (emulated declaration)" for c in D_CHECKS})


def _na_rec():
    return dict(v="N/A", measured="no-carriage (emulated)", cause="no-carriage")


# ───────────────────────── registry / revision / fingerprint ─────────────────────────

def test_carr_detector_is_not_registered_and_carr_is_exactly_d1_d2_d3():
    assert "Carr.detector" not in ac.CRITERION_REGISTRY
    assert [k for k, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Carr"] == list(D_CHECKS)
    assert len(ac.CRITERION_REGISTRY) == 31          # 32 at revision 7, before the retirement (N-22 v1.2.3 §3.5)
    assert ac.registered_criterion("Carr.detector") is None
    assert ac.lookup_criterion("bg_x", None, "Carr.detector") is None


def test_the_retirement_is_recorded_with_its_reason_and_decision_and_never_overlaps_the_registry():
    assert set(ac.RETIRED_CRITERIA) == {"Carr.detector"}
    e = ac.RETIRED_CRITERIA["Carr.detector"]
    assert e["retired_in_revision"] == 8
    assert all(isinstance(e[k], str) and e[k].strip() for k in ("reason", "decision"))
    assert "A2" in e["decision"] and "D1" in e["reason"]
    assert not (set(ac.RETIRED_CRITERIA) & set(ac.CRITERION_REGISTRY))
    assert all(v["retired_in_revision"] <= ac.REGISTRY_REVISION for v in ac.RETIRED_CRITERIA.values())


def test_registry_revision_is_the_latest_pinned_one_and_its_fingerprint_is_not_the_revision_7_one():
    assert ac.REGISTRY_REVISION == max(p1.PINNED_FINGERPRINTS) >= 8       # the retirement is revision 8; the current one is pinned
    assert ac.registry_fingerprint() != REV7_FINGERPRINT


def test_the_fingerprint_changes_when_the_retired_criterion_is_re_registered(monkeypatch):
    fp = ac.registry_fingerprint()
    _restore_pre_retirement(monkeypatch)
    assert ac.registry_fingerprint() != fp


def test_the_revision_7_pin_is_reproduced_by_the_rebuilt_pre_retirement_registry(monkeypatch):
    """The rebuilt revision-7 registry (used for every with/without comparison below) is faithful: its fingerprint IS
    the pinned revision-7 one, so the comparison is against the real predecessor, not a lookalike."""
    _restore_pre_retirement(monkeypatch)
    # RETIRED_CRITERIA is not part of the fingerprinted content (it decides no cell), so the registry alone decides it
    assert ac.registry_fingerprint() == REV7_FINGERPRINT


# ───────────────────────── measure() stops emitting it ─────────────────────────

def test_measure_no_longer_emits_carr_detector_even_when_a_detector_script_exists(monkeypatch, tmp_path):
    w1._stub_layer(monkeypatch, tmp_path, {"bg_x": w1._reg_row("bg_x")})
    det = tmp_path / "detectors"
    det.mkdir()
    (det / "bg_x_D1.py").write_text('import json\nprint(json.dumps({"verdict": "PASS", "measured": "ok"}))\n', encoding="utf-8")
    c = ac.measure("L0")
    ms = c["assets"][0]["measurements"]
    assert "Carr.detector" not in ms
    assert not [k for k in ms if k.startswith("Carr.")], "D1-D3 are detector NONE: nothing measures a Carr check"
    ac.rollup_asset("L0", ms)   # a freshly measured layer rolls up without any retired-criterion handling


# ───────────────────────── a saved census that still carries it ─────────────────────────

def test_rollup_ignores_a_retired_measurement_from_a_saved_census_and_reports_it_as_excluded():
    ms = {"Carr.detector": NO_DET_RECORD, "Build.dag": dict(v="PASS", measured="m")}
    with_it = ac.rollup_asset("L2", ms)
    without = ac.rollup_asset("L2", {"Build.dag": dict(v="PASS", measured="m")})
    assert json.dumps(with_it, sort_keys=True) == json.dumps(without, sort_keys=True)
    assert [c["criterion"] for c in with_it["Carr"]["checks"]] == list(D_CHECKS)
    assert ac.rollup_excluded("L2", ms) == {"Carr.detector": "NO_DETECTOR"}     # reported, never silently dropped


def test_an_unregistered_non_retired_measurement_still_raises():
    with pytest.raises(KeyError):
        ac.rollup_asset("L2", {"Carr.detector2": NO_DET_RECORD})


def test_a_retired_criterion_can_never_be_cell_graded_even_with_a_pass(monkeypatch):
    cell = ac.rollup_asset("L2", {"Carr.detector": dict(v="PASS", measured="x")})["Carr"]
    assert cell["v"] == "NO_DETECTOR" and [c["criterion"] for c in cell["checks"]] == list(D_CHECKS)


# ───────────────────────── P1-P4 on the committed fixture ─────────────────────────

def _carr_cells(extra=None):
    out = {}
    for L, a, ms in _assets():
        m = dict(ms)
        if extra:
            m.update(extra(a))
        out[a] = ac.rollup_asset(L, m)
    return out


def test_fixture_is_the_127_asset_2330_cell_census_without_the_retired_criterion():
    assert sum(len(v) for v in FIXTURE["layers"].values()) == 127
    assert sum(len(ms) for v in FIXTURE["layers"].values() for ms in v.values()) == 2457 - 127
    assert not [1 for v in FIXTURE["layers"].values() for ms in v.values() if "Carr.detector" in ms]


def test_P1_carr_cell_unchanged_and_no_other_gate_moves_on_all_127(monkeypatch):
    after = _carr_cells(extra=lambda a: {"Carr.detector": NO_DET_RECORD})          # ignored by the retired inspector
    after_clean = _carr_cells()
    assert json.dumps(after, sort_keys=True) == json.dumps(after_clean, sort_keys=True)
    _restore_pre_retirement(monkeypatch)
    before = _carr_cells(extra=lambda a: {"Carr.detector": NO_DET_RECORD})
    assert len(before) == len(after) == 127
    assert {c["Carr"]["v"] for c in before.values()} == {"NO_DETECTOR"}
    assert {c["Carr"]["v"] for c in after.values()} == {"NO_DETECTOR"}
    for aid in after:
        for g in ac.CELL_GATES:
            b, a_ = before[aid][g], after[aid][g]
            assert b["v"] == a_["v"], (aid, g)
            if g != "Carr":      # every other gate: the whole cell (checks included) is identical, not just the verdict
                assert json.dumps(b["checks"], sort_keys=True) == json.dumps(a_["checks"], sort_keys=True), (aid, g)


def test_P2_a_measured_pass_on_d1_d3_still_reads_no_detector():
    for L, a, ms in _assets():
        if a not in (CEILING[0], _assets()[0][1]):
            continue
        ms = dict(ms, **{c: dict(v="PASS", measured="hypothetical PASS (proof only)") for c in D_CHECKS})
        cell = ac.rollup_asset(L, ms)["Carr"]
        assert cell["v"] == "NO_DETECTOR", a
        # D2 is detector NONE (D1 got a detector in revision 11, D3 in N-156: a measured D1 / D3 PASS is honoured only with its evidence)
        assert all("detector NONE never reaches PASS" in c["reason"] for c in cell["checks"] if c["criterion"] == "Carr.D2")
        assert all("without re-derivation evidence" in c["reason"] for c in cell["checks"] if c["criterion"] == "Carr.D3")
        assert all(c["v"] == "NO_DETECTOR" for c in cell["checks"])      # and a bare D1 PASS (no verified evidence) is not honoured either


def test_P3_ceiling_reads_na_on_exactly_the_six_after_the_retirement_and_not_before(monkeypatch):
    _no_carriage_causes(monkeypatch)
    after = {}
    for L, a, ms in _assets():
        m = dict(ms)
        if a in CEILING:
            m.update({c: _na_rec() for c in D_CHECKS})
        after[a] = ac.rollup_asset(L, m)["Carr"]["v"]
    assert sorted(a for a, v in after.items() if v == "N/A") == sorted(CEILING)
    assert sum(1 for v in after.values() if v == "NO_DETECTOR") == 121 and len(after) == 127

    _restore_pre_retirement(monkeypatch)
    _no_carriage_causes(monkeypatch)                     # Carr.detector still registered, still measured NO_DETECTOR
    before = {}
    for L, a, ms in _assets():
        m = dict(ms, **{"Carr.detector": NO_DET_RECORD})
        if a in CEILING:
            m.update({c: _na_rec() for c in D_CHECKS})
        before[a] = ac.rollup_asset(L, m)["Carr"]["v"]
    assert set(before.values()) == {"NO_DETECTOR"}       # the gap A2 named: the meta-check held all six


def test_P4_one_d_check_left_no_detector_holds_the_cell(monkeypatch):
    _no_carriage_causes(monkeypatch)
    for L, a, ms in _assets():
        if a != CEILING[0]:
            continue
        m = dict(ms, **{"Carr.D1": _na_rec(), "Carr.D2": _na_rec()})                  # D3 unmeasured -> NO_DETECTOR
        cell = ac.rollup_asset(L, m)["Carr"]
        assert cell["v"] == "NO_DETECTOR"
        assert [c["v"] for c in cell["checks"]] == ["N/A", "N/A", "NO_DETECTOR"]
        full = ac.rollup_asset(L, dict(ms, **{c: _na_rec() for c in D_CHECKS}))["Carr"]
        assert full["v"] == "N/A"


def test_counts_checks_per_asset_contributions_and_check_level_ceiling(monkeypatch):
    after = _carr_cells()
    assert {len(c["Carr"]["checks"]) for c in after.values()} == {3}
    assert sum(len(c["Carr"]["checks"]) for c in after.values()) == 381
    assert len(CEILING) * 3 == 18
    _restore_pre_retirement(monkeypatch)
    before = _carr_cells()
    assert {len(c["Carr"]["checks"]) for c in before.values()} == {4}
    assert sum(len(c["Carr"]["checks"]) for c in before.values()) == 508
    assert len(CEILING) * 4 == 24


# ───────────────────────── P1-P4 on the saved Track A census JSONs ─────────────────────────

EV = pathlib.Path("/Users/Dev/suvarna-evidence")
_SAVED = {L: EV / ("census2" if L in ("L1", "L2") else "census") / f"census_{L}.json" for L in ALL_LAYERS}
saved = pytest.mark.skipif(not all(p.exists() for p in _SAVED.values()), reason="saved Track A census JSONs not on this machine")


def _saved_layer(L):
    return json.loads(_SAVED[L].read_text(encoding="utf-8"))[L]


@saved
def test_saved_census_P1_carr_127_no_detector_both_ways_and_no_other_cell_moves(monkeypatch):
    layers = {L: _saved_layer(L) for L in ALL_LAYERS}
    n_meas = sum(1 for c in layers.values() for a in c["assets"] if (a["measurements"].get("Carr.detector") or {}).get("v") == "NO_DETECTOR")
    assert n_meas == 127, "the saved census measured Carr.detector NO_DETECTOR on every asset"
    after = {a: cells for L, c in layers.items() for a, cells in ac.rollup_census(c).items()}
    _restore_pre_retirement(monkeypatch)
    before = {a: cells for L, c in layers.items() for a, cells in ac.rollup_census(c).items()}
    assert len(after) == len(before) == 127
    for aid in after:
        assert before[aid]["Carr"]["v"] == after[aid]["Carr"]["v"] == "NO_DETECTOR", aid
        for g in ac.CELL_GATES:
            assert before[aid][g]["v"] == after[aid][g]["v"], (aid, g)
            if g != "Carr":
                assert json.dumps(before[aid][g]["checks"], sort_keys=True) == json.dumps(after[aid][g]["checks"], sort_keys=True)
        assert sorted(c["criterion"] for c in before[aid]["Carr"]["checks"]) == sorted(["Carr.detector", *D_CHECKS])
        assert [c["criterion"] for c in after[aid]["Carr"]["checks"]] == list(D_CHECKS)


@saved
def test_saved_census_P2_P3_P4_through_the_repo_rollup(monkeypatch):
    layers = {L: _saved_layer(L) for L in ALL_LAYERS}
    recs = {(a["asset_id"]): (L, a["measurements"]) for L, c in layers.items() for a in c["assets"]}
    assert set(CEILING) <= set(recs)
    # P2
    L, ms = recs[CEILING[0]]
    ms2 = dict(ms, **{c: dict(v="PASS", measured="proof only") for c in D_CHECKS})
    assert ac.rollup_asset(L, ms2)["Carr"]["v"] == "NO_DETECTOR"
    # P3 / P4
    _no_carriage_causes(monkeypatch)
    cells = {}
    for aid, (L, ms) in recs.items():
        m = dict(ms)
        if aid in CEILING:
            m.update({c: _na_rec() for c in D_CHECKS})
        cells[aid] = ac.rollup_asset(L, m)["Carr"]["v"]
    assert sorted(a for a, v in cells.items() if v == "N/A") == sorted(CEILING)
    assert sum(v == "NO_DETECTOR" for v in cells.values()) == 121
    L, ms = recs[CEILING[0]]
    assert ac.rollup_asset(L, dict(ms, **{"Carr.D1": _na_rec(), "Carr.D2": _na_rec()}))["Carr"]["v"] == "NO_DETECTOR"


# ───────────────────────── the ledger: OPEN rows of the retired criterion ─────────────────────────

def _row(aid, state="OPEN", crit="Carr.detector", **extra):
    base = dict(asset=aid, gap_id=f"{aid}-{crit}", kind="gap", criterion=crit,
                what="measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim",
                change="hand change", detector=f"asset_census.py --layer L0 ({crit})", owner="hand owner",
                gate="hand gate", state=state, ts="t0")
    base.update(extra)
    return base


def _write(ctrl, rows):
    (ctrl / "asset_gaps.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _read(ctrl):
    p = ctrl / "asset_gaps.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def _census(*assets, **ms):
    return dict(layer="L0", assets=[dict(asset_id=a, measurements=dict(ms)) for a in (assets or ("bg_x",))])


@pytest.fixture()
def ctrl(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    return tmp_path


def test_an_open_row_of_the_retired_criterion_is_closed_with_a_recorded_reason(ctrl):
    _write(ctrl, [_row("bg_x")])
    added, skipped, closed, reopened = ac.emit_gaps(_census())
    assert (added, skipped, closed, reopened) == (0, 0, 1, 0)
    rows = _read(ctrl)
    assert len(rows) == 2 and rows[0]["state"] == "OPEN", "append-only: the OPEN row is never edited"
    new = rows[1]
    assert new["state"] == "CLOSED" and new["gap_id"] == "bg_x-Carr.detector" and new["criterion"] == "Carr.detector"
    assert new["what"].startswith("CLOSED by retirement of criterion Carr.detector")
    assert "registry revision 8" in new["what"] and "A2" in new["what"] and "D1" in new["what"]
    assert (new["change"], new["owner"], new["gate"]) == ("hand change", "hand owner", "hand gate")   # hand metadata carried
    assert "RETIRED_CRITERIA" in new["detector"] and new["kind"] == "gap"
    assert new["closed_by"] == "retirement" and new["retired_criterion"] == "Carr.detector"   # distinguishes it from a measurement close


def test_in_progress_rows_close_too_and_every_layer_is_closed_whatever_layer_the_run_measured(ctrl):
    _write(ctrl, [_row("bg_x", "IN_PROGRESS"), _row("ga_y"), _row("mi_z")])
    assert ac.emit_gaps(_census("bg_x")) == (0, 0, 3, 0)
    assert {r["gap_id"] for r in _read(ctrl) if r["state"] == "CLOSED"} == {"bg_x-Carr.detector", "ga_y-Carr.detector", "mi_z-Carr.detector"}


def test_closure_is_idempotent(ctrl):
    _write(ctrl, [_row("bg_x")])
    ac.emit_gaps(_census())
    n = len(_read(ctrl))
    assert ac.emit_gaps(_census()) == (0, 0, 0, 0)
    assert len(_read(ctrl)) == n


def test_closed_withdrawn_and_superseded_rows_are_left_alone(ctrl):
    _write(ctrl, [_row("bg_a", "CLOSED"), _row("bg_b", "WITHDRAWN"),
                  _row("bg_c", superseded_by="bg_c-Carr.D1"), _row("bg_d", "OPEN")])
    assert ac.emit_gaps(_census()) == (0, 0, 1, 0)       # only bg_d
    rows = _read(ctrl)
    assert [r["gap_id"] for r in rows if r["state"] == "CLOSED" and r["ts"] != "t0"] == ["bg_d-Carr.detector"]
    assert len(rows) == 5


def test_a_later_plain_row_after_a_supersession_does_not_resurrect_the_id(ctrl):
    _write(ctrl, [_row("bg_c", superseded_by="bg_c-Carr.D1"), _row("bg_c", "OPEN")])
    assert ac.emit_gaps(_census()) == (0, 0, 0, 0)


def test_other_criteria_rows_and_rows_without_a_criterion_are_untouched(ctrl):
    hand = dict(asset="bg_x", kind="gap", what="hand row no gap_id", state="OPEN", ts="t0")
    _write(ctrl, [_row("bg_x", crit="Carr.D1"), _row("bg_x", crit="Build.dag"), hand])
    assert ac.emit_gaps(_census()) == (0, 0, 0, 0)
    assert len(_read(ctrl)) == 3


def test_a_retired_criterion_never_opens_a_gap_even_if_something_measures_it(ctrl):
    assert ac.emit_gaps(_census(**{"Carr.detector": NO_DET_RECORD})) == (0, 0, 0, 0)
    assert _read(ctrl) == []


def test_a_retired_row_is_not_reopened_by_a_stray_measurement(ctrl):
    _write(ctrl, [_row("bg_x", "CLOSED")])
    assert ac.emit_gaps(_census(**{"Carr.detector": NO_DET_RECORD})) == (0, 0, 0, 0)
    assert len(_read(ctrl)) == 1


def test_closure_of_retired_rows_does_not_disturb_normal_transitions_in_the_same_run(ctrl):
    _write(ctrl, [_row("bg_x")])
    added, skipped, closed, reopened = ac.emit_gaps(_census(**{"Build.dag": dict(v="FAIL", measured="m")}))
    assert (added, closed) == (1, 1)
    assert {r["gap_id"] for r in _read(ctrl)} == {"bg_x-Carr.detector", "bg_x-Build.dag"}


def test_a_retired_criterion_has_no_na_cause_and_no_rule_can_be_declared_for_it(monkeypatch):
    assert "Carr.detector" not in ac.NA_CAUSES
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Carr.detector#measured:no-carriage": "x"})
    with pytest.raises(ValueError):
        ac.validate_na_rule_decisions()


# ───────────────────────── review corrections: id match, opportunities, marker, import guard, clamp ─────────────────────────

def test_a_hand_row_with_a_non_deterministic_id_is_untouched_even_if_its_criterion_is_retired(ctrl):
    hand = _row("bg_a", gap_id="bg_a-G05")           # criterion Carr.detector, but NOT the deterministic id
    _write(ctrl, [hand])
    assert ac.emit_gaps(_census()) == (0, 0, 0, 0)
    assert _read(ctrl) == [hand]


def test_a_row_without_a_criterion_field_but_the_deterministic_id_is_closed(ctrl):
    r = _row("bg_a")
    del r["criterion"]
    _write(ctrl, [r])
    assert ac.emit_gaps(_census()) == (0, 0, 1, 0)
    new = _read(ctrl)[-1]
    assert new["state"] == "CLOSED" and new["gap_id"] == "bg_a-Carr.detector" and new["criterion"] == "Carr.detector"


def test_a_scoped_id_is_not_the_deterministic_unscoped_id(ctrl):
    _write(ctrl, [_row("bg_a", gap_id="bg_a-Carr.detector@chart1")])
    assert ac.emit_gaps(_census()) == (0, 0, 0, 0)


def test_an_opportunity_row_is_never_closed_by_retirement_and_is_counted(ctrl):
    opp = _row("bg_a", kind="opportunity")
    _write(ctrl, [opp, _row("bg_b"), _row("bg_c", "CLOSED", kind="opportunity")])
    out = ac.emit_gaps_summary(_census())
    assert out == dict(added=0, skipped=0, closed=1, reopened=0, retired_opportunity_rows_left=1)
    rows = _read(ctrl)
    assert rows[0] == opp and not [r for r in rows if r["gap_id"] == "bg_a-Carr.detector" and r is not rows[0] and r["state"] == "CLOSED"]
    assert {r["gap_id"] for r in rows[3:]} == {"bg_b-Carr.detector"}
    assert ac.emit_gaps_summary(_census())["retired_opportunity_rows_left"] == 1      # still reported on every run


def test_emit_gaps_keeps_its_four_tuple_return(ctrl):
    _write(ctrl, [_row("bg_b"), _row("bg_a", kind="opportunity")])
    assert ac.emit_gaps(_census()) == (0, 0, 1, 0)


def test_main_prints_the_retired_opportunity_count(ctrl, monkeypatch, capsys):
    monkeypatch.setattr(ac, "measure", lambda k: dict(layer=k, layer_name="x", scoring="s", n_assets=0, registered_ids=0,
        registry_has_writer=0, population_registry_total=0, population_active=0, population_excluded_inactive=[],
        global_runs=0, global_runs_touching_layer=0, never_exercised_with_writer=[], phantom_registered=[], assets=[]))
    _write(ctrl, [_row("bg_a", kind="opportunity")])
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--emit-gaps", "--out", str(ctrl / "o.json")])
    ac.main()
    assert "1 retired-criterion opportunity row(s) left as is" in capsys.readouterr().out


def test_the_overlap_guard_raises_for_an_id_in_both_tables():
    with pytest.raises(RuntimeError, match="Carr.D1"):
        ac._check_retired_disjoint({"Carr.D1": {}}, {"Carr.D1": {}})
    ac._check_retired_disjoint(ac.CRITERION_REGISTRY, ac.RETIRED_CRITERIA)


def test_the_overlap_guard_fires_at_import_time():
    import importlib.util
    src = (HERE.parent / "asset_census.py").read_text(encoding="utf-8")
    assert src.count('RETIRED_CRITERIA: dict[str, dict] = {\n    "Carr.detector": dict(') == 1
    bad = src.replace('RETIRED_CRITERIA: dict[str, dict] = {\n    "Carr.detector": dict(', 'RETIRED_CRITERIA: dict[str, dict] = {\n    "Carr.D1": dict(')
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = pathlib.Path(d) / "asset_census_bad.py"
        f.write_text(bad, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("asset_census_bad", f)
        mod = importlib.util.module_from_spec(spec)
        with pytest.raises(RuntimeError, match="Carr.D1"):
            spec.loader.exec_module(mod)


def test_clamp_a_measured_partial_on_all_of_d1_d3_still_reads_no_detector():
    """Detector NONE never earns a graded verdict above FAIL: PASS and PARTIAL both clamp to NO_DETECTOR (chosen
    behaviour; before the clamp was extended PARTIAL on D1-D3 would have given Carr PARTIAL, which the retired
    Carr.detector had hidden by reading NO_DETECTOR)."""
    cell = ac.rollup_asset("L2", {c: dict(v="PARTIAL", measured="x") for c in ("Carr.D2", "Carr.D3")})["Carr"]
    assert cell["v"] == "NO_DETECTOR"
    assert all("detector NONE never reaches PARTIAL" in c["reason"] for c in cell["checks"] if c["criterion"] == "Carr.D2")
    assert all("without re-derivation evidence" in c["reason"] for c in cell["checks"] if c["criterion"] == "Carr.D3")      # N-156: D3 is a detector; a bare PARTIAL carries no evidence


def test_clamp_a_measured_fail_on_a_detector_none_check_is_still_a_fail():
    assert ac.rollup_asset("L2", {"Carr.D1": dict(v="FAIL", measured="x")})["Carr"]["v"] == "FAIL"


# ───────────────────────── E1.9 F1: a SCOPED emit never closes another asset's retired-criterion row ─────────────────────────

def _raw(ctrl):
    return (ctrl / "asset_gaps.jsonl").read_bytes()


def _scoped(scope, *assets):
    """A census labelled scoped to `scope` (the label E1.9's measure(assets=...) writes) holding `assets`."""
    c = _census(*assets)
    c["scope"] = dict(assets=sorted(scope), partial=True)
    return c


def test_F1_a_scoped_run_closes_only_the_in_scope_assets_retired_rows_and_leaves_the_rest_byte_identical(ctrl):
    _write(ctrl, [_row("bg_other"), _row("bg_in"), _row("ga_other", "IN_PROGRESS")])
    before = _raw(ctrl)
    assert ac.emit_gaps(_scoped(["bg_in"], "bg_in")) == (0, 0, 1, 0)           # the in-scope row DOES close
    after = _raw(ctrl)
    assert after.startswith(before), "every pre-existing row byte-identical and in order"
    new = [json.loads(x) for x in after[len(before):].decode().splitlines()]
    assert [(r["gap_id"], r["state"], r["closed_by"]) for r in new] == [("bg_in-Carr.detector", "CLOSED", "retirement")]


def test_F1_a_scoped_run_with_no_in_scope_retired_row_leaves_the_ledger_byte_identical(ctrl):
    _write(ctrl, [_row("bg_other"), _row("ga_other", "IN_PROGRESS"), _row("mi_other", kind="opportunity")])
    before = _raw(ctrl)
    assert ac.emit_gaps_summary(_scoped(["bg_in"], "bg_in")) == dict(
        added=0, skipped=0, closed=0, reopened=0, retired_opportunity_rows_left=0)
    assert _raw(ctrl) == before


def test_F1_the_assets_argument_scopes_the_closure_exactly_like_the_census_label(ctrl):
    _write(ctrl, [_row("bg_other"), _row("bg_in")])
    before = _raw(ctrl)
    assert ac.emit_gaps(_census("bg_in", "bg_other"), assets=["bg_in"]) == (0, 0, 1, 0)
    after = _raw(ctrl)
    assert after.startswith(before)
    assert [json.loads(x)["gap_id"] for x in after[len(before):].decode().splitlines()] == ["bg_in-Carr.detector"]


def test_F1_an_out_of_scope_opportunity_row_is_neither_closed_nor_counted(ctrl):
    _write(ctrl, [_row("bg_other", kind="opportunity"), _row("bg_in", kind="opportunity")])
    before = _raw(ctrl)
    out = ac.emit_gaps_summary(_scoped(["bg_in"], "bg_in"))
    assert out["closed"] == 0 and out["retired_opportunity_rows_left"] == 1      # only the in-scope one is reported
    assert _raw(ctrl) == before


def test_F1_an_unscoped_run_still_closes_every_assets_retired_rows(ctrl):
    _write(ctrl, [_row("bg_other"), _row("bg_in")])
    assert ac.emit_gaps(_census("bg_in")) == (0, 0, 2, 0)


def test_F1_a_scoped_run_then_the_unscoped_run_closes_the_remainder_once(ctrl):
    _write(ctrl, [_row("bg_other"), _row("bg_in")])
    assert ac.emit_gaps(_scoped(["bg_in"], "bg_in")) == (0, 0, 1, 0)
    assert ac.emit_gaps(_scoped(["bg_in"], "bg_in")) == (0, 0, 0, 0)               # idempotent under the same scope
    assert ac.emit_gaps(_census("bg_in")) == (0, 0, 1, 0)                           # the out-of-scope row was still OPEN
    assert {r["gap_id"] for r in _read(ctrl) if r["state"] == "CLOSED"} == {"bg_in-Carr.detector", "bg_other-Carr.detector"}


# ───────────────────────── review LOW fixes: tolerant reads of hand-edited rows, wrong-asset id ─────────────────────────

def test_a_lower_case_hand_edited_state_is_still_a_live_row_and_is_closed(ctrl):
    _write(ctrl, [_row("bg_a", "open"), _row("bg_b", "In_Progress")])
    assert ac.emit_gaps(_census()) == (0, 0, 2, 0)
    assert {r["gap_id"] for r in _read(ctrl) if r["state"] == "CLOSED"} == {"bg_a-Carr.detector", "bg_b-Carr.detector"}


def test_a_row_without_a_kind_field_is_read_as_a_gap_and_closed(ctrl):
    r = _row("bg_a")
    del r["kind"]
    _write(ctrl, [r])
    assert ac.emit_gaps_summary(_census()) == dict(added=0, skipped=0, closed=1, reopened=0, retired_opportunity_rows_left=0)
    new = _read(ctrl)[-1]
    assert new["state"] == "CLOSED" and new["kind"] == "gap" and new["gap_id"] == "bg_a-Carr.detector"


def test_a_row_whose_gap_id_names_another_asset_is_not_closed_under_the_wrong_asset(ctrl):
    wrong = _row("bg_a", gap_id="bg_b-Carr.detector")      # asset says bg_a, the deterministic id says bg_b
    _write(ctrl, [wrong])
    before = _raw(ctrl)
    assert ac.emit_gaps(_census()) == (0, 0, 0, 0)
    assert _raw(ctrl) == before
