"""Synthetic expected-state tests for the S-L2 attribution hooks (offline: no database, no network).

Two parts, deliberately separated because the flip detector (platform/scripts/governance/flip_detector.py, v2.x) reads FOUR L1 tables
only (chart_facts, chart_divisionals, chart_dashas, panchanga_daily) and no L2 table at all:

PART A, the real detector, unmodified.
  hooks dir: 00_ARCHITECTURE/briefs/suvarna/exec/s_l2_attribution_hooks/*.json (top level only, exactly what the detector loads)
  The lane s_l2_l1_untouched declares "S-L2 moves no L1 row". Proved with the detector's own compare_states():
    A1  the hook directory validates and the lane is present
    A2  an unchanged L1 state: no failure class is non-empty (verdict NOT_CHECKED, the standing registry is never empty)
    A3  EVERY kind of change in EVERY compared L1 table fails (value / appeared / disappeared / occurrence_count / tier, a dasha row, a
        dasha start shift, a panchanga_daily column), each as UNDECLARED_CHANGE, EXPECTATION_MISMATCH or DASHA_SHIFT_UNDECLARED
    A4  mutation: the zero claim is what blocks the declared category (a hook with {"min":0,"max":5} lets one change through)

PART B, the L2 hooks (s_l2_attribution_hooks/l2/*.json, NOT loadable by the detector today: sub-folders are never read and the
  tables are not in its HOOK_TABLES). They are written in the detector's own hook schema. This part proves each entry REAL with
  the detector's own pure functions (diff_table, occ_map, attribute_all, expectation_report) and the detector's own hook validator,
  with ONE stated difference: the table allow-list HOOK_TABLES is extended for the duration of the test with the L2 table names (the
  one-line change a detector extension must make, together with reading the L2 tables in read_state/compare_states; that wiring is
  NOT built here and is listed for SS in S_L2_ATTRIBUTION_HOOKS_v1_0.md). Every expected count is the output of a derivation function
  in this file (rule + declared L1 delta), and the test fails if the hook file and the derivation disagree.

The detector arrives with PR #2945 and is on main; FLIP_DETECTOR_PATH points the tests at another copy.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import pathlib

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(__file__).resolve().parents[4]
HOOKS_DIR = REPO / "00_ARCHITECTURE" / "briefs" / "suvarna" / "exec" / "s_l2_attribution_hooks"
L2_HOOKS_DIR = HOOKS_DIR / "l2"
DETECTOR = pathlib.Path(os.environ.get("FLIP_DETECTOR_PATH", HERE.parent / "flip_detector.py"))

CANON = "482012f1-710e-4a25-994a-93821f5871aa"
AYS = ["lahiri_chitrapaksha", "krishnamurti", "true_chitra", "raman", "surya_siddhanta_classical"]
ALL_KINDS = ["value", "appeared", "disappeared", "occurrence_count", "tier"]


def _load_detector():
    if not DETECTOR.exists():
        return None
    spec = importlib.util.spec_from_file_location("flip_detector_under_test_s_l2", DETECTOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fd = _load_detector()
needs_detector = pytest.mark.skipif(fd is None, reason=f"flip_detector.py not in the tree ({DETECTOR})")


# ----------------------------------------------------------------------------------------------- PART A state builder
class L1State:
    """Before / after rows in the detector's snapshot format. The FORENSIC anchors are kept true on the canonical chart."""

    def __init__(self):
        self.facts = [["lahiri_chitrapaksha", "zz_filler", "F", "k", "x", "", "single"]]
        self.divs = [["lahiri_chitrapaksha", "D0", "G0", "zz_filler", "k", "x", "", ""]]
        self.dash = [["lahiri_chitrapaksha", "zz_sys", 1, "/Z", "2000-01-01T00:00:00+00:00", "2000-02-01T00:00:00+00:00"]]
        self.daily = [["2026-01-01", 1, "S", 1, 1, "x", 1, 1, 1, "t", "v", "y", "k"]]
        for _name, (cat, subj, key), want, ays in fd.ANCHORS:
            for ay in ays:
                self.facts.append([ay, cat, subj, key, want, "", "single"])

    def state(self):
        return {"chart_facts": copy.deepcopy(self.facts), "divisionals": copy.deepcopy(self.divs),
                "dashas": copy.deepcopy(self.dash), "daily": copy.deepcopy(self.daily)}


def _hooks():
    hooks, errors = fd.load_hooks(str(HOOKS_DIR), required=("s_l2_l1_untouched",))
    assert not errors, errors
    return hooks


def _compare(before, after, hooks=None):
    return fd.compare_states(before.state(), after.state(), hooks if hooks is not None else _hooks(), CANON, have_dash=True, have_daily=True)


def _failing(rep):
    return {k: v for k, v in rep["failure_counts"].items() if v}


def test_hook_directory_shape():
    files = sorted(p.name for p in HOOKS_DIR.glob("*.json"))
    assert files == ["s_l2_l1_untouched.json"], files
    assert (HOOKS_DIR / "l2").is_dir(), "the L2 hooks live in a sub-folder the detector never reads"


@needs_detector
def test_A1_hooks_validate_with_the_real_validator():
    hooks = _hooks()
    assert [h["lane"] for h in hooks] == ["s_l2_l1_untouched"]
    for e in hooks[0]["may_change"]:
        assert e["expected_count"] == {"exact": 0}, "every entry of the tripwire is an explicit zero claim"
    assert {e["table"] for e in hooks[0]["may_change"]} == set(fd.TABLES)


@needs_detector
def test_A2_unchanged_l1_passes_with_no_failure_class():
    a, b = L1State(), L1State()
    rep = _compare(a, b)
    assert not _failing(rep), (_failing(rep), rep["failures"])
    assert rep["verdict"] == "NOT_CHECKED"  # the standing NOT CHECKED registry is never empty: never PASS, never FAIL
    assert rep["changes_total"] == 0


def _pair(change):
    """-> (before, after) L1State pair realising ONE change. `change` = (table, category, kind)."""
    before, after = L1State(), L1State()
    table, cat, kind = change
    ay = "lahiri_chitrapaksha"
    if table == "chart_facts":
        row = lambda text, tier: [ay, cat, "S1", "k", text, "", tier]
        if kind == "appeared":
            after.facts.append(row("x", "single"))
        elif kind == "disappeared":
            before.facts.append(row("x", "single"))
        elif kind == "value":
            before.facts.append(row("a", "single")); after.facts.append(row("b", "single"))
        elif kind == "occurrence_count":
            before.facts.append(row("x", "single")); after.facts.append(row("x", "single")); after.facts.append(row("x", "single"))
        elif kind == "tier":
            before.facts.append(row("x", "single_pass")); after.facts.append(row("x", "single"))
    elif table == "chart_divisionals":
        row = lambda text: [ay, "D1", "S1", cat, "k", text, "", ""]
        if kind == "appeared":
            after.divs.append(row("x"))
        elif kind == "disappeared":
            before.divs.append(row("x"))
        elif kind == "value":
            before.divs.append(row("a")); after.divs.append(row("b"))
        elif kind == "occurrence_count":
            before.divs.append(row("x")); after.divs.append(row("x")); after.divs.append(row("x"))
    elif table == "chart_dashas":
        r = [ay, cat, 1, "/N1", "2001-01-01T00:00:00+00:00", "2001-02-01T00:00:00+00:00"]
        if kind == "appeared":
            after.dash.append(r)
        elif kind == "disappeared":
            before.dash.append(r)
        elif kind == "shift":  # one paired row whose start moves 7,000 s (the S-L1 Vimshottari scale)
            before.dash.append(r)
            after.dash.append([ay, cat, 1, "/N1", "2001-01-01T01:56:40+00:00", "2001-02-01T01:56:40+00:00"])
    elif table == "panchanga_daily":
        if kind == "value":
            after.daily[0] = list(after.daily[0]); after.daily[0][1] = 2  # tithi_id changes on the one daily row
        elif kind == "appeared":
            after.daily.append(["2026-01-02", 1, "S", 1, 1, "x", 1, 1, 1, "t", "v", "y", "k"])
    return before, after


L1_CHANGES = [
    ("chart_facts", "graha_position", "value"),       # the declared (zero-claim) category
    ("chart_facts", "graha_position", "appeared"),
    ("chart_facts", "graha_position", "disappeared"),
    ("chart_facts", "graha_position", "occurrence_count"),
    ("chart_facts", "graha_position", "tier"),
    ("chart_facts", "zz_undeclared_category", "value"),  # any other category
    ("chart_facts", "zz_undeclared_category", "appeared"),
    ("chart_facts", "zz_undeclared_category", "disappeared"),
    ("chart_facts", "zz_undeclared_category", "tier"),
    ("chart_divisionals", "varga_position", "value"),
    ("chart_divisionals", "varga_position", "appeared"),
    ("chart_divisionals", "varga_position", "disappeared"),
    ("chart_divisionals", "zz_undeclared_category", "appeared"),
    ("chart_dashas", "vimshottari", "appeared"),
    ("chart_dashas", "vimshottari", "disappeared"),
    ("chart_dashas", "vimshottari", "shift"),
    ("chart_dashas", "zz_other_system", "appeared"),
    ("panchanga_daily", "tithi_id", "value"),
    ("panchanga_daily", "row", "appeared"),
]


@needs_detector
@pytest.mark.parametrize("change", L1_CHANGES, ids=[f"{t}:{c}:{k}" for t, c, k in L1_CHANGES])
def test_A3_any_change_to_any_l1_table_fails(change):
    before, after = _pair(change)
    rep = _compare(before, after)
    failing = _failing(rep)
    assert failing, f"{change}: S-L2 would have been allowed to change L1 silently"
    assert rep["verdict"] == "FAIL", (change, rep["verdict"], failing)
    assert set(failing) <= {"UNDECLARED_CHANGE", "EXPECTATION_MISMATCH", "KIND_MISMATCH", "DASHA_SHIFT_UNDECLARED"}, failing


@needs_detector
def test_A4_mutation_the_zero_claim_is_what_blocks_the_declared_category():
    hooks = copy.deepcopy(_hooks())
    entry = next(e for e in hooks[0]["may_change"] if e["table"] == "chart_facts")
    before, after = _pair(("chart_facts", "graha_position", "value"))
    assert _failing(_compare(before, after, hooks)), "baseline: the exact-0 claim fails a declared-category change"
    entry["expected_count"] = {"min": 0, "max": 5}  # mutation: weaken the claim
    assert not _failing(_compare(before, after, hooks)), "mutation: with a weakened claim the same change passes (so the exact-0 is load-bearing)"
    del entry["expected_count"]  # mutation: an entry with no count
    rep = _compare(before, after, hooks)
    assert not rep["failure_counts"]["EXPECTATION_MISMATCH"]


@needs_detector
def test_A5_the_tripwire_does_not_attribute_a_dasha_shift_to_the_lane():
    """A start shift is a DASHA_SHIFT_UNDECLARED failure: the lane declares no dasha_shift entry, so an ephemeris-scale shift cannot ride S-L2."""
    before, after = _pair(("chart_dashas", "vimshottari", "shift"))
    rep = _compare(before, after)
    assert rep["failure_counts"]["DASHA_SHIFT_UNDECLARED"] >= 1, rep["failure_counts"]
