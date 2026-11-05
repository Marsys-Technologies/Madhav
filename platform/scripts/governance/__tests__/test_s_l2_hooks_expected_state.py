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


# =============================================================================================================== PART B
# The L2 hook lanes. Three independent things are proved:
#   B1  the five files are byte-for-byte the output of s_l2_hook_rules.py (the derivation), and every input of that derivation is load-bearing
#       (a mutated input changes the output);
#   B2  the files are accepted by the L2-aware detector's own validator, cover all 29 L2 tables, name only categories that exist, and every
#       rule label cited in a note is defined in S_L2_ATTRIBUTION_HOOKS_v1_0.md;
#   B3  an ORACLE written here by hand (a second derivation: the arithmetic is in the comments, not imported from the rules module) is run
#       through the real detector: for each (table, category, kind) the stated in-bound counts are accepted and the stated out-of-bound
#       counts are refused. Hook mutations (widen / narrow / drop / re-scope an entry) must each make the oracle fail.
# Part B needs the L2-aware flip_detector (PR #3035: `L2_TABLES`, `--l2`); on a tree without it the detector-dependent tests skip and only
# B1 and the doc checks run. Point FLIP_DETECTOR_PATH at a copy that has it.
RULES_PATH = HERE.parent / "s_l2_hook_rules.py"
DOC_PATH = REPO / "00_ARCHITECTURE" / "briefs" / "suvarna" / "exec" / "s_l2" / "S_L2_ATTRIBUTION_HOOKS_v1_0.md"
_rspec = importlib.util.spec_from_file_location("s_l2_hook_rules_under_test", RULES_PATH)
RULES = importlib.util.module_from_spec(_rspec)
_rspec.loader.exec_module(RULES)

has_l2 = fd is not None and hasattr(fd, "L2_TABLES")
needs_l2 = pytest.mark.skipif(not has_l2, reason="flip_detector.py has no L2 extension (PR #3035); set FLIP_DETECTOR_PATH to a copy that has")
LANE_FILES = sorted(RULES.LANES)


@pytest.mark.parametrize("lane", LANE_FILES)
def test_B1_files_are_the_output_of_the_derivation(lane):
    on_disk = (L2_HOOKS_DIR / f"{lane}.json").read_text(encoding="utf-8")
    assert on_disk == RULES.render(lane), f"{lane}.json is not what s_l2_hook_rules.py derives: regenerate with --write and READ the diff"


def test_B1_the_l2_folder_holds_exactly_the_five_lanes():
    assert sorted(p.stem for p in L2_HOOKS_DIR.glob("*.json")) == LANE_FILES


def _perturb(attr, fn):
    """Apply `fn` to RULES.<attr> (in place on a deep copy swapped into the module), return {lane: output differs from the file}."""
    original = getattr(RULES, attr)
    setattr(RULES, attr, fn(copy.deepcopy(original)))
    try:
        return {lane: RULES.render(lane) != (L2_HOOKS_DIR / f"{lane}.json").read_text(encoding="utf-8") for lane in LANE_FILES}
    finally:
        setattr(RULES, attr, original)


def _bump(path):
    def fn(obj):
        node = obj
        for p in path[:-1]:
            node = node[p]
        node[path[-1]] += 1
        return obj
    return fn


RULE_INPUT_MUTATIONS = [
    # (id, attribute, mutation, lanes that MUST change)
    ("msr_yoga_count", "MSR", _bump(["yoga"]), {"s_l2_msr_projection", "s_l2_embeddings_grounding"}),
    ("msr_composite_count", "MSR", _bump(["composite_state"]), {"s_l2_msr_projection", "s_l2_embeddings_grounding"}),
    ("composite_citing_rekeyed", "COMPOSITE_CITING_REKEYED", lambda v: v + 1, {"s_l2_msr_projection"}),
    ("appeared_argala_graha_natal", "APPEARED_COMPOSITE", _bump(["argala_graha_natal"]), {"s_l2_msr_projection", "s_l2_embeddings_grounding"}),
    ("appeared_karaka_web", "APPEARED_KARAKA", _bump(["karaka_web_per_varga (upper end of 950..1,300)"]), {"s_l2_msr_projection", "s_l2_embeddings_grounding"}),
    ("appeared_parivartana", "APPEARED_PARIVARTANA", _bump(["parivartana_pairs (optional)"]), {"s_l2_msr_projection", "s_l2_embeddings_grounding"}),
    ("disappeared_sun_required_rupa", "DISAPPEARED_COMPOSITE", _bump(["sun_required_rupa: graha_in_house_composite_strength"]), {"s_l2_msr_projection", "s_l2_embeddings_grounding"}),
    ("disappeared_strikaraka", "DISAPPEARED_KARAKA", _bump(["karaka_chara_position STRIKARAKA relabel"]), {"s_l2_msr_projection", "s_l2_embeddings_grounding"}),
    ("cgm_edges_aspect_rows", "CAT", lambda c: (c["bodha_cgm_edges"].__setitem__("aspect", c["bodha_cgm_edges"]["aspect"] + 1) or c), {"s_l2_cgm_graph"}),
    ("cgm_nodes_graha_rows", "CAT", lambda c: (c["bodha_cgm_nodes"].__setitem__("graha", 46) or c), {"s_l2_cgm_graph"}),
    ("dasha_windowed_rows", "CAT", lambda c: (c["bodha_rm_dasha_windowed_prescriptions"].__setitem__("vimshottari", 6) or c), {"s_l2_remedy_discovery_misc"}),
    ("pratijna_rows", "CAT", lambda c: (c["bodha_pratijna"].__setitem__("pratijna", 136) or c), {"s_l2_remedy_discovery_misc"}),
    ("cdlm_cells_rows", "CAT", lambda c: (c["bodha_cdlm_cells"].__setitem__("static_natal", 281) or c), {"s_l2_cdlm_sangati"}),
    ("domains_in_grid", "DOMAINS", lambda v: v + 1, {"s_l2_cdlm_sangati"}),
    ("question_classes_in_grid", "QUESTION_CLASSES", lambda v: v + 1, {"s_l2_cdlm_sangati"}),
    ("traditions_in_grid", "TRADITIONS", lambda v: v + 1, {"s_l2_cdlm_sangati"}),
    ("ayanamshas", "AYAS", lambda v: v + 1, {"s_l2_cgm_graph", "s_l2_cdlm_sangati", "s_l2_msr_projection"}),
    ("vichara_citing_edges", "VICHARA_CITING_EDGES", lambda v: v + 1, {"s_l2_cgm_graph"}),
    ("vichara_citing_mechanisms", "VICHARA_CITING_MECHANISMS", lambda v: v + 1, {"s_l2_cgm_graph"}),
    ("argala_cap_per_aya", "ARGALA_EDGE_CAP_PER_AYA", lambda v: v + 1, {"s_l2_cgm_graph"}),
]


@pytest.mark.parametrize("mut", RULE_INPUT_MUTATIONS, ids=[m[0] for m in RULE_INPUT_MUTATIONS])
def test_B1_mutation_every_derivation_input_is_load_bearing(mut):
    _id, attr, fn, must = mut
    changed = {lane for lane, differs in _perturb(attr, fn).items() if differs}
    assert must <= changed, f"{_id}: expected lanes {sorted(must)} to change, got {sorted(changed)}"


def test_B2_every_rule_label_cited_in_a_note_is_defined_in_the_record():
    import re
    cited = set()
    for lane in LANE_FILES:
        for e in json.loads((L2_HOOKS_DIR / f"{lane}.json").read_text())["may_change"]:
            cited |= set(re.findall(r"\(R(\d+)(?:[,)]| and)", e.get("note", ""))) | set(re.findall(r", R(\d+)", e.get("note", "")))
    assert cited, "the notes must cite rules"
    if not DOC_PATH.exists():
        pytest.skip("S_L2_ATTRIBUTION_HOOKS_v1_0.md not present")
    doc = DOC_PATH.read_text(encoding="utf-8")
    for n in sorted(cited, key=int):
        assert re.search(rf"\*\*R{n}\.", doc), f"rule R{n} is cited by a hook note but not defined (as **R{n}.**) in the record"


def _all_l2_hooks():
    hooks, errors = fd.load_hooks(str(L2_HOOKS_DIR))
    assert not errors, errors
    return hooks


@needs_l2
def test_B2_files_validate_with_the_l2_aware_validator_and_cover_all_tables():
    hooks = _all_l2_hooks()
    assert sorted(h["lane"] for h in hooks) == LANE_FILES
    covered = {e["table"] for h in hooks for e in h["may_change"]}
    assert covered == set(fd.L2_TABLES), (sorted(set(fd.L2_TABLES) - covered), sorted(covered - set(fd.L2_TABLES)))
    for h in hooks:
        for e in h["may_change"]:
            assert e["table"] in fd.L2_TABLES and "expected_count" in e and e.get("note")


@needs_l2
def test_B2_categories_named_by_the_hooks_are_exactly_the_production_categories():
    produced = {t: set(c) for t, c in RULES.CAT.items()}
    produced["bodha_msr_signals"] = set(RULES.MSR)
    produced["bodha_signal_embeddings"] = set(RULES.MSR)
    named = {}
    for h in _all_l2_hooks():
        for e in h["may_change"]:
            named.setdefault(e["table"], set()).update(e["categories"])
    assert set(named) == set(produced) == set(fd.L2_TABLES)
    for t in produced:
        assert named[t] == produced[t], (t, sorted(named[t] ^ produced[t]))


@needs_l2
def test_B2_every_entry_bound_is_internally_consistent():
    for h in _all_l2_hooks():
        for e in h["may_change"]:
            ec = e["expected_count"]
            assert not ("exact" in ec and len(ec) > 1)
            if "min" in ec and "max" in ec:
                assert ec["min"] <= ec["max"], (h["lane"], e)
            if e.get("optional"):
                assert ec.get("min", 0) == 0 and "exact" not in ec, "an optional entry must allow zero"


# ----------------------------------------------------------------------------------------------- B3: the oracle (hand-written, independent)
S_CHART = "5a5a5a5a-1111-4222-8333-444444444444"   # not the canonical chart: no anchor handling, no hook scoped to it
AY0 = "lahiri_chitrapaksha"
KINDS = ("value", "appeared", "disappeared", "tier", "occurrence_count")


def _l1_minimal():
    return {"chart_facts": [[AY0, "zz_filler", "F", "k", "x", "", "single"]], "divisionals": [[AY0, "D0", "G0", "zz_filler", "k", "x", "", ""]],
            "dashas": [], "daily": []}


def _l2_pair(table, cat, kind, n):
    row = lambda i, text=None, tier="": [AY0, cat, f"s{i}", f"k{i}", text or f"id=a{i}", "", tier]
    filler = [AY0, "zz_filler", "F", "k", "id=f", "", ""]
    before, after = [filler], [filler]
    for i in range(n):
        if kind == "value":
            before.append(row(i, f"id=a{i}")); after.append(row(i, f"id=b{i}"))
        elif kind == "appeared":
            after.append(row(i))
        elif kind == "disappeared":
            before.append(row(i))
        elif kind == "tier":
            before.append(row(i, tier="t0")); after.append(row(i, tier="t1"))
        elif kind == "occurrence_count":
            before.append(row(i)); after.append(row(i)); after.append(row(i))
        else:
            raise AssertionError(kind)
    s0, s1 = _l1_minimal(), _l1_minimal()
    s0["l2"], s1["l2"] = {table: before}, {table: after}
    return s0, s1


def _within(ec, n):
    """The detector's own expectation rule (expectation_report), restated for the bounds that are too large to push through it."""
    return (n == ec["exact"]) if "exact" in ec else (ec.get("min", 0) <= n <= ec.get("max", 10 ** 12))


DETECTOR_MAX_ROWS = 6000  # larger counts are judged by the entries' bounds with the detector's own rule instead of a 50k-row diff (CI time)


def judge(hooks, table, cat, kind, n):
    """-> (accepted, why). Accepted = attributed (no undeclared / kind-mismatch failure) and every hook entry the change touched is within its bound."""
    if n > DETECTOR_MAX_ROWS:
        touched = [e for h in hooks for e in h["may_change"]
                   if e["table"] == table and cat in e["categories"] and kind in (e.get("change_types") or KINDS)]
        if not touched:
            return False, "undeclared"
        bad = [e for e in touched if not _within(e["expected_count"], n)]
        return (not bad), ("ok" if not bad else "out of bound")
    s0, s1 = _l2_pair(table, cat, kind, n)
    rep = fd.compare_states(s0, s1, hooks, S_CHART, have_dash=False, have_daily=False, l2_tables=(table,), l2_requested=True)
    fc = rep["failure_counts"]
    if fc["UNDECLARED_CHANGE"] or fc["KIND_MISMATCH"]:
        return False, "undeclared"
    touched = [x for x in rep["expectations"] if x["observed"] > 0]
    if not touched:
        return False, "nothing observed"
    return all(x["ok"] for x in touched), "ok" if all(x["ok"] for x in touched) else "out of bound"


T = "bodha_msr_signals"
# (table, category, kind, [accepted counts], [refused counts]); the arithmetic of each bound is in the trailing comment
ORACLE = [
    # --- MSR (S-L1 declared deltas: appeared composite = argala_graha_natal 156 + ashtakavarga_bindu_contributor 3360 + dasha_scope_cap 1x5 + gulika/mandi 35 + geometry 45+30+315+85 + gandanta twin 50)
    (T, "annual", "value", [6764], [6763, 6765]),                    # 13 classes: 315+150+26+590+1169+1400+74+25+45+20+4+2871+75 = 6764 (all cite a re-keyed fact, none appear/disappear)
    (T, "sade_sati", "value", [6764], [6763, 6765]),
    (T, "composite_state", "value", [36388, 37694], [36387, 37695]),  # 36,628 cite a re-keyed fact - 240 that may vanish = 36,388 ; max = all 37,694
    (T, "karaka_alignment", "value", [6121, 6156], [6120, 6157]),    # 6,156 - 35 = 6,121 ; max = 6,156
    (T, "sudarshana_agreement", "value", [0 + 1, 55], [56]),         # 45 + 10 signals with stable cites
    (T, "dhana_axis", "value", [55], [56]),
    (T, "composite_state", "appeared", [4081], [4082]),             # 156+3360+5+35+475+50 = 4081
    (T, "composite_state", "disappeared", [240], [241]),
    (T, "karaka_alignment", "appeared", [1340], [1341]),            # 35 + 5 + 1300
    (T, "karaka_alignment", "disappeared", [35], [36]),
    (T, "parivartana", "appeared", [15], [16]),
    (T, "parivartana", "disappeared", [], [1]),
    (T, "annual", "appeared", [], [1]),
    (T, "yoga", "appeared", [], [1]),
    (T, "dosha", "disappeared", [], [1]),
    (T, "special_lagna", "appeared", [], [1]),
    (T, "sudarshana_agreement", "appeared", [], [1]),
    (T, "zz_new_class", "appeared", [], [1]),                       # a class nobody declared can never ride
    (T, "composite_state", "tier", [50678], [50679]),               # one tier change per signal: 37694+6156+2871+1400+1169+590+315+150+75+74+45+45+26+25+20+10+9+4 = 50678
    (T, "varga_ratification_divergence", "appeared", [1, 100], []),  # attribution only (no derivable bound)
    (T, "varga_ratification_divergence", "value", [1], []),
    (T, "annual", "occurrence_count", [1, 100], []),
    # --- embeddings and grounding follow the signal set (appeared max 4081+1340+15 = 5436 ; disappeared max 240+35 = 275 ; rows 50,678)
    ("bodha_signal_embeddings", "yoga", "appeared", [5436], [5437]),
    ("bodha_signal_embeddings", "yoga", "disappeared", [275], [276]),
    ("bodha_signal_embeddings", "yoga", "value", [50678], [50679]),
    ("bodha_signal_embeddings", "yoga", "tier", [], [1]),
    ("bodha_grounding_matches", "msr_signal", "appeared", [5436], [5437]),
    ("bodha_grounding_matches", "msr_signal", "disappeared", [275], [276]),
    ("bodha_grounding_matches", "msr_signal", "value", [50678], [50679]),
    ("bodha_grounding_matches", "msr_signal", "tier", [50678], [50679]),
    ("bodha_grounding_matches", "yoga_dosha_firing", "appeared", [53, 200], []),
    ("bodha_grounding_matches", "zz_new_kind", "appeared", [], [1]),
    # --- Bodha graph (nodes 385 ; edges 849 ; argala cap 24 x 5 = 120 ; edges citing vichara ids 754 - 119 argala that may vanish = 635 ; mechanisms 615, citing vichara 605)
    ("bodha_cgm_nodes", "graha", "appeared", [], [1]),
    ("bodha_cgm_nodes", "bhava", "disappeared", [], [1]),
    ("bodha_cgm_nodes", "yoga", "appeared", [], [1]),
    ("bodha_cgm_nodes", "arudha", "value", [385], [386]),
    ("bodha_cgm_nodes", "domain", "tier", [385], [386]),
    ("bodha_cgm_edges", "aspect", "appeared", [], [1]),
    ("bodha_cgm_edges", "dispositor", "disappeared", [], [1]),
    ("bodha_cgm_edges", "argala", "appeared", [120], [121]),
    ("bodha_cgm_edges", "argala", "disappeared", [119], [120]),
    ("bodha_cgm_edges", "aspect", "value", [635, 849], [634, 850]),
    ("bodha_cgm_edges", "lordship", "tier", [969], [970]),          # 849 + 120
    ("bodha_cgm_paths", "dispositor_chain", "appeared", [], [1]),
    ("bodha_cgm_paths", "dispositor_chain", "value", [], [1]),
    ("bodha_cgm_paths", "dispositor_chain", "tier", [45], [46]),
    ("bodha_cgm_motifs", "mutual_aspect", "appeared", [], [1]),
    ("bodha_cgm_motifs", "mutual_aspect_triangle", "value", [], [1]),
    ("bodha_cgm_motifs", "mutual_aspect", "tier", [600], [601]),
    ("bodha_cgm_sub_graphs", "connected_component", "value", [], [1]),
    ("bodha_cgm_sub_graphs", "connected_component", "appeared", [1, 5], []),
    ("bodha_cgm_chart_topology_summary", "topology", "appeared", [], [1]),
    ("bodha_cgm_chart_topology_summary", "topology", "value", [5], [6]),
    ("bodha_mechanisms", "mutual_aspect", "appeared", [], [1]),
    ("bodha_mechanisms", "mutual_aspect", "value", [605, 615], [604, 616]),
    ("bodha_contradictions", "domain_promise_vs_denial", "appeared", [], [1]),
    ("bodha_contradictions", "domain_promise_vs_denial", "value", [15], [16]),
    # --- cdlm / sangati (13 domains, 12 question classes, 4 traditions, 5 ayanamshas)
    ("bodha_cdlm_cells", "static_natal", "appeared", [565], [566]),         # 13 x 13 x 5 = 845 - 280
    ("bodha_cdlm_cells", "static_natal", "disappeared", [280], [281]),
    ("bodha_cdlm_cells", "static_natal", "value", [280], [281]),
    ("bodha_convergence", "static_natal", "appeared", [5], [6]),            # 13 x 5 = 65 - 60
    ("bodha_convergence", "static_natal", "disappeared", [60], [61]),
    ("bodha_cdlm_domain_rollups", "rollup", "appeared", [5], [6]),
    ("bodha_cdlm_domain_rollups", "rollup", "value", [60], [61]),
    ("bodha_triangulation", "career", "appeared", [45], [46]),              # 12 x 4 x 5 = 240 - 195
    ("bodha_triangulation", "career", "disappeared", [195], [196]),
    ("bodha_triangulation", "wealth", "occurrence_count", [], [1]),
    ("bodha_cdlm_chart_summary", "summary", "appeared", [], [1]),
    ("bodha_cdlm_chart_summary", "summary", "value", [5], [6]),
    ("bodha_cdlm_pattern_clusters", "unclassified_linkage_cluster", "appeared", [1, 50], []),
    ("bodha_cdlm_pattern_clusters", "unclassified_linkage_cluster", "value", [5], [6]),
    ("bodha_question_lenses", "lens", "appeared", [], [1]),
    ("bodha_question_lenses", "lens", "value", [60], [61]),
    ("bodha_chart_gestalt", "gestalt", "appeared", [], [1]),
    ("bodha_chart_gestalt", "gestalt", "value", [5], [6]),
    # --- remedies, pratijna, discoveries, anomalies, scorecard
    ("bodha_rm_resonances", "static_natal", "appeared", [], [1]),
    ("bodha_rm_resonances", "static_natal", "value", [45], [46]),
    ("bodha_rm_remedy_prescriptions", "mantra", "appeared", [1, 500], []),
    ("bodha_rm_remedy_prescriptions", "japa", "value", [270], [271]),       # twice the 135 rows
    ("bodha_rm_chart_summary", "summary", "appeared", [], [1]),
    ("bodha_rm_dosha_remedy_bundles", "bundle", "appeared", [1, 10], []),
    ("bodha_rm_pattern_remedies", "resonance", "value", [45], [46]),
    ("bodha_rm_dasha_windowed_prescriptions", "vimshottari", "disappeared", [5], [4, 6]),   # the tombstone table: exactly the 5 legacy rows
    ("bodha_rm_dasha_windowed_prescriptions", "vimshottari", "appeared", [], [1]),
    ("bodha_rm_dasha_windowed_prescriptions", "vimshottari", "value", [], [1]),
    ("bodha_pratijna", "pratijna", "value", [135], [136]),                  # 27 event classes x 5
    ("bodha_pratijna", "pratijna", "appeared", [135], [136]),
    ("bodha_pratijna", "pratijna", "disappeared", [135], [136]),
    ("bodha_pratijna", "pratijna", "tier", [], [1]),
    ("bodha_discoveries", "distributional_anomaly", "appeared", [1, 1000], []),
    ("bodha_discoveries", "embedding_outlier", "value", [1161], [1162]),
    ("bodha_anomalies", "low_salience_high_consequence", "value", [3276], [3277]),
    ("bodha_anomalies", "distributional_anomaly", "disappeared", [1, 1000], []),
    ("synthesis_quality_scorecard", "scorecard", "appeared", [], [1]),
    ("synthesis_quality_scorecard", "scorecard", "disappeared", [], [1]),
    ("synthesis_quality_scorecard", "scorecard", "value", [1], [2]),
]
ORACLE_IDS = [f"{t.replace('bodha_', '').replace('synthesis_quality_', '')}:{c}:{k}" for t, c, k, _ok, _bad in ORACLE]


@needs_l2
@pytest.mark.parametrize("row", ORACLE, ids=ORACLE_IDS)
def test_B3_oracle_in_bound_counts_are_accepted_and_out_of_bound_counts_are_refused(row):
    table, cat, kind, ok_ns, bad_ns = row
    hooks = _all_l2_hooks()
    for n in ok_ns:
        accepted, why = judge(hooks, table, cat, kind, n)
        assert accepted, f"{table}:{cat}:{kind} n={n} must be accepted ({why})"
    for n in bad_ns:
        accepted, why = judge(hooks, table, cat, kind, n)
        assert not accepted, f"{table}:{cat}:{kind} n={n} must be refused"


def _oracle_failures(hooks, tables):
    out = []
    for table, cat, kind, ok_ns, bad_ns in ORACLE:
        if table not in tables:
            continue
        out += [(table, cat, kind, n, "refused-in-bound") for n in ok_ns if not judge(hooks, table, cat, kind, n)[0]]
        out += [(table, cat, kind, n, "accepted-out-of-bound") for n in bad_ns if judge(hooks, table, cat, kind, n)[0]]
    return out


def _entry(hooks, table, cat, kind):
    for h in hooks:
        for e in h["may_change"]:
            if e["table"] == table and cat in e["categories"] and kind in (e.get("change_types") or KINDS):
                return e
    raise AssertionError((table, cat, kind))


def _set_count(ec):
    def fn(hooks, table, cat, kind):
        _entry(hooks, table, cat, kind)["expected_count"] = ec
    return fn


def _widen(hooks, table, cat, kind):
    ec = _entry(hooks, table, cat, kind)["expected_count"]
    ec["max"] = ec["max"] + 1


def _narrow(hooks, table, cat, kind):
    ec = _entry(hooks, table, cat, kind)["expected_count"]
    if "max" in ec:
        ec["max"] = ec["max"] - 1
    else:
        ec["exact"] = ec["exact"] - 1


def _raise_min(hooks, table, cat, kind):
    ec = _entry(hooks, table, cat, kind)["expected_count"]
    ec["min"] = ec["min"] + 1


def _drop_entry(hooks, table, cat, kind):
    e = _entry(hooks, table, cat, kind)
    for h in hooks:
        if e in h["may_change"]:
            h["may_change"].remove(e)


def _drop_kind(hooks, table, cat, kind):
    e = _entry(hooks, table, cat, kind)
    e["change_types"] = [k for k in e["change_types"] if k != kind] or ["occurrence_count"]


def _drop_category(hooks, table, cat, kind):
    e = _entry(hooks, table, cat, kind)
    e["categories"] = [c for c in e["categories"] if c != cat]


def _open_the_cap(hooks, table, cat, kind):
    ec = _entry(hooks, table, cat, kind)["expected_count"]
    ec.pop("max", None); ec.pop("exact", None)


def _exact_to_open(hooks, table, cat, kind):
    e = _entry(hooks, table, cat, kind)
    e["expected_count"] = {"min": 0}


HOOK_MUTATIONS = [
    ("widen composite appeared cap", _widen, (T, "composite_state", "appeared")),
    ("widen karaka disappeared cap", _widen, (T, "karaka_alignment", "disappeared")),
    ("narrow 13-class exact value count", _narrow, (T, "annual", "value")),
    ("raise composite value floor", _raise_min, (T, "composite_state", "value")),
    ("open the MSR tier cap", _open_the_cap, (T, "yoga", "tier")),
    ("drop the parivartana appeared entry", _drop_entry, (T, "parivartana", "appeared")),
    ("drop 'appeared' from the embeddings appeared entry", _drop_kind, ("bodha_signal_embeddings", "yoga", "appeared")),
    ("widen embeddings value cap", _widen, ("bodha_signal_embeddings", "yoga", "value")),
    ("open the grounding disappeared cap", _open_the_cap, ("bodha_grounding_matches", "msr_signal", "disappeared")),
    ("zero claim on node appearance relaxed to open", _exact_to_open, ("bodha_cgm_nodes", "graha", "appeared")),
    ("zero claim on aspect edge appearance relaxed", _exact_to_open, ("bodha_cgm_edges", "aspect", "appeared")),
    ("argala appeared cap widened", _widen, ("bodha_cgm_edges", "argala", "appeared")),
    ("edge value floor raised", _raise_min, ("bodha_cgm_edges", "aspect", "value")),
    ("mechanism value floor lowered away (drop category)", _drop_category, ("bodha_mechanisms", "mutual_aspect", "value")),
    ("path value zero claim relaxed", _exact_to_open, ("bodha_cgm_paths", "dispositor_chain", "value")),
    ("cdlm cell appeared cap widened", _widen, ("bodha_cdlm_cells", "static_natal", "appeared")),
    ("convergence appeared cap narrowed", _narrow, ("bodha_convergence", "static_natal", "appeared")),
    ("triangulation appeared cap widened", _widen, ("bodha_triangulation", "career", "appeared")),
    ("lens zero claim relaxed", _exact_to_open, ("bodha_question_lenses", "lens", "appeared")),
    ("dasha-windowed exact 5 relaxed", _exact_to_open, ("bodha_rm_dasha_windowed_prescriptions", "vimshottari", "disappeared")),
    ("pratijna value cap widened", _widen, ("bodha_pratijna", "pratijna", "value")),
    ("scorecard appearance zero claim relaxed", _exact_to_open, ("synthesis_quality_scorecard", "scorecard", "appeared")),
    ("resonance appearance zero claim relaxed", _exact_to_open, ("bodha_rm_resonances", "static_natal", "appeared")),
    ("discoveries value cap narrowed", _narrow, ("bodha_discoveries", "embedding_outlier", "value")),
]


@needs_l2
def test_B3_baseline_oracle_has_no_failure_on_the_real_files():
    assert _oracle_failures(_all_l2_hooks(), {r[0] for r in ORACLE}) == []


@needs_l2
@pytest.mark.parametrize("mut", HOOK_MUTATIONS, ids=[m[0] for m in HOOK_MUTATIONS])
def test_B3_mutation_a_changed_hook_entry_is_caught_by_the_oracle(mut):
    _name, fn, (table, cat, kind) = mut
    hooks = copy.deepcopy(_all_l2_hooks())
    fn(hooks, table, cat, kind)
    failures = _oracle_failures(hooks, {table})
    assert failures, f"{_name}: the oracle did not notice"


# ----------------------------------------------------------------------------------------------- B4: the L1 tripwire and the L2 lanes together; NOT CHECKED
@needs_l2
def test_B4_l2_entries_are_not_checked_when_the_run_does_not_compare_l2():
    hooks = _all_l2_hooks()
    rep = fd.compare_states(_l1_minimal(), _l1_minimal(), hooks, S_CHART, have_dash=False, have_daily=False)
    ids = {n["id"] for n in rep["not_checked"]}
    for h in hooks:
        for i in range(len(h["may_change"])):
            assert f"{h['lane']}[{i}]" in ids, "an L2 entry in a run without --l2 must read NOT CHECKED, never passing"
    assert rep["verdict"] != "PASS"


@needs_l2
def test_B4_a_l1_change_still_fails_when_the_l2_lanes_are_loaded_with_the_tripwire():
    hooks = _hooks() + _all_l2_hooks()
    before, after = _pair(("chart_facts", "graha_position", "value"))
    s0, s1 = before.state(), after.state()
    for s in (s0, s1):
        s["l2"] = {}
    rep = fd.compare_states(s0, s1, hooks, CANON, have_dash=True, have_daily=True, l2_tables=("bodha_msr_signals",), l2_requested=True)
    assert rep["verdict"] == "FAIL" and _failing(rep)


@needs_l2
def test_B4_an_in_bound_l2_change_alongside_unchanged_l1_raises_no_attribution_failure():
    hooks = _hooks() + _all_l2_hooks()
    s0, s1 = L1State().state(), L1State().state()
    row = lambda i, t: [AY0, "annual", f"s{i}", f"k{i}", t, "", ""]
    s0["l2"] = {T: [row(i, f"id=a{i}") for i in range(10)]}
    s1["l2"] = {T: [row(i, f"id=b{i}") for i in range(10)]}
    rep = fd.compare_states(s0, s1, hooks, CANON, have_dash=True, have_daily=True, l2_tables=(T,), l2_requested=True)
    assert rep["failure_counts"]["UNDECLARED_CHANGE"] == 0 and rep["failure_counts"]["KIND_MISMATCH"] == 0
    assert not any(x["ok"] is True and x["observed"] for x in rep["expectations"] if x["lane"] == "s_l2_l1_untouched")
    # ten annual value changes are far below the 13-class exact count (6,764): that entry is the one expectation that fails, as it must in a partial rebuild
    assert any((not x["ok"]) and x["lane"] == "s_l2_msr_projection" and x["expected"] == {"exact": 6764} for x in rep["expectations"])
