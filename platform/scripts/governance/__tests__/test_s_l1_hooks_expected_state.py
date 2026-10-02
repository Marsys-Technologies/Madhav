"""Synthetic EXPECTED AFTER-STATE tests for the S-L1 attribution hooks (offline: no database, no network).

For every hook in 00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/*.json this builds small before / after
states in the format flip_detector.compare_states() consumes and proves, with the detector's OWN compare:

  T1  the declared change PASSES      (every entry reads its expected count; no failure class is non-empty)
  T2  an undeclared change FAILS      (an undeclared category is UNDECLARED_CHANGE; a declared category with an
                                       undeclared KIND of change is KIND_MISMATCH)
  T3  a count off by one FAILS        (EXPECTATION_MISMATCH naming the entry, for exact, max and exact-zero entries)
  T4  an UNCHANGED state shows no DECLARED_BUT_ABSENT: the only non-pass entries are those whose lower bound is
      positive (EXPECTATION_MISMATCH: the change did not happen) and the optional ones (silent, or an OPTIONAL_ABSENT
      warning); nothing else
  T5  the whole directory together: the union of every applicable hook's expected change passes with zero failures,
      and the unchanged state has no DECLARED_BUT_ABSENT, for the canonical chart and for an Abhinandan-like chart

Not expressible in the detector's snapshot format (stated, not skipped silently): a hook entry on
l1_tajik_varsha_year_lords or a chart_dashas entry whose only change type is `tier` (tiers.json entries 1 and 2): the
detector never reads those columns / tables, so no fixture can make them observed; T-NC asserts they are reported as
NOT CHECKED (never as absent, never as passing). Likewise chart_vichara: not a hook (it is outside the detector's four
tables; the declaration stays under evidence/), asserted by T-VICHARA.

The generator is driven by the hook's own entries, so T1 alone is not an independent check of the COUNTS; the counts are
pinned independently by the lane-scenario tests (LS-*) below, written from the lane evidence, and by the rehearsal
compare recorded in HOOKS_COMPLETENESS_v1_0.md.

The detector arrives with PR #2945 (platform/scripts/governance/flip_detector.py). Until it is in the tree these tests
skip with a stated reason; FLIP_DETECTOR_PATH points them at another copy.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import os
import pathlib

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(__file__).resolve().parents[4]
HOOKS_DIR = REPO / "00_ARCHITECTURE" / "briefs" / "suvarna" / "exec" / "s_l1_attribution_hooks"
DETECTOR = pathlib.Path(os.environ.get("FLIP_DETECTOR_PATH", HERE.parent / "flip_detector.py"))

CANON = "482012f1-710e-4a25-994a-93821f5871aa"
ABHI = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
AYS = ["lahiri_chitrapaksha", "krishnamurti", "true_chitra", "raman", "surya_siddhanta_classical"]
ALL_KINDS = ["value", "appeared", "disappeared", "occurrence_count", "tier"]
# Hooks added or completed in the S-L1 hook-completion phase: every count-bearing / optional entry states its source.
PHASE3_HOOKS = {
    "argala", "argala_other_charts", "ashtakavarga_bindu_contributor", "chandra_bala_birth_moon_sign", "dasha_scope_cap",
    "ga_strength_invariant_rows", "ga_structural_chart_geometry", "ga_vargas_invariant_sentinels", "karaka_dasha_roles",
    "karaka_roles", "karaka_web_order", "karaka_web_order_other_charts", "sade_sati_placeholder_null", "sun_required_rupa",
    "tiers", "tiers_other_charts", "yamakantaka",
}


# The EXACT set of hook lanes (HOOKS_W7_HAND_READBACK Part 1): deleting or adding a hook file must fail a test, not just shrink
# the parametrised suites (107 tests = these 22 lanes x the generic per-hook proofs + the static / scenario tests).
EXPECTED_HOOK_STEMS = frozenset({
    "argala",
    "argala_other_charts",
    "ashtakavarga_bindu_contributor",
    "band_table",
    "chandra_bala_birth_moon_sign",
    "dasha_scope_cap",
    "ga_condition_fallback",
    "ga_strength_invariant_rows",
    "ga_structural_chart_geometry",
    "ga_vargas_invariant_sentinels",
    "gandanta",
    "karaka_dasha_roles",
    "karaka_roles",
    "karaka_web_order",
    "karaka_web_order_other_charts",
    "sade_sati_placeholder_null",
    "special_lagna_offset",
    "special_lagna_offset_other_charts",
    "sun_required_rupa",
    "tiers",
    "tiers_other_charts",
    "yamakantaka",
})


def _load_detector():
    if not DETECTOR.exists():
        return None
    spec = importlib.util.spec_from_file_location("flip_detector_under_test", DETECTOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fd = _load_detector()
needs_detector = pytest.mark.skipif(fd is None, reason=f"flip_detector.py not in the tree ({DETECTOR}); it arrives with PR #2945")


def _hook_files():
    return sorted(HOOKS_DIR.glob("*.json"))


def _load_hooks():
    return {p.stem: json.loads(p.read_text()) for p in _hook_files()}


def _chart_for(hook):
    """A chart id the hook applies to (its first `charts` prefix, else the canonical chart)."""
    if "charts" in hook:
        pre = hook["charts"][0].lower()
        return {"482012f1": CANON, "1c826d5a": ABHI}.get(pre[:8], pre[:8] + "-0000-4000-8000-000000000000")
    return CANON


# ----------------------------------------------------------------------------------------------- state builder
class State:
    """Before / after row lists in the detector's snapshot format, plus the change records used for matching."""

    def __init__(self, chart=CANON):
        self.n = 0
        self.facts_b, self.facts_a = [["lahiri_chitrapaksha", "zz_filler", "F", "k", "x", "", "single"]], [["lahiri_chitrapaksha", "zz_filler", "F", "k", "x", "", "single"]]
        self.div_b, self.div_a = [["lahiri_chitrapaksha", "D0", "G0", "zz_filler", "k", "x", "", ""]], [["lahiri_chitrapaksha", "D0", "G0", "zz_filler", "k", "x", "", ""]]
        self.das_b, self.das_a = [["lahiri_chitrapaksha", "zz_sys", 1, "/Z", "2000-01-01T00:00:00+00:00", "2000-02-01T00:00:00+00:00"]], [["lahiri_chitrapaksha", "zz_sys", 1, "/Z", "2000-01-01T00:00:00+00:00", "2000-02-01T00:00:00+00:00"]]
        self.records = []
        if fd is not None and chart == CANON:  # the native chart's FORENSIC anchors are checked on every compare: keep them true
            for _name, (cat, subj, key), want, ays in fd.ANCHORS:
                for ay in ays:
                    self.facts_b.append([ay, cat, subj, key, want, "", "single"])
                    self.facts_a.append([ay, cat, subj, key, want, "", "single"])

    def snap(self):
        return {"chart_facts": self.facts_b, "divisionals": self.div_b, "dashas": self.das_b}

    def cur(self):
        return {"chart_facts": self.facts_a, "divisionals": self.div_a, "dashas": self.das_a}

    def add(self, table, category, key, ay, kind):
        """Realize ONE change of `kind` on a fresh key. Returns the change record, or None if the table cannot express it."""
        self.n += 1
        subj = f"S{self.n}"
        rec = {"table": table, "category": category, "fact_key": key, "ayanamsha": ay, "change": kind}
        if table == "chart_facts":
            b, a = self.facts_b, self.facts_a
            row = lambda text, tier: [ay, category, subj, key, text, "", tier]
            if kind == "appeared":
                a.append(row("x", "single"))
            elif kind == "disappeared":
                b.append(row("x", "single"))
            elif kind == "value":
                b.append(row("a", "single")); a.append(row("b", "single"))
            elif kind == "occurrence_count":
                b.append(row("x", "single")); a.append(row("x", "single")); a.append(row("x", "single"))
            elif kind == "tier":
                b.append(row("x", "single_pass")); a.append(row("x", "single"))
        elif table == "chart_divisionals":
            b, a = self.div_b, self.div_a
            row = lambda text: [ay, "D1", subj, category, key, text, "", ""]
            if kind == "appeared":
                a.append(row("x"))
            elif kind == "disappeared":
                b.append(row("x"))
            elif kind == "value":
                b.append(row("a")); a.append(row("b"))
            elif kind == "occurrence_count":
                b.append(row("x")); a.append(row("x")); a.append(row("x"))
            else:
                return None  # chart_divisionals has no tier column
        elif table == "chart_dashas":
            if kind not in ("appeared", "disappeared"):
                return None
            row = [ay, category, 1, f"/{subj}", "2001-01-01T00:00:00+00:00", "2001-02-01T00:00:00+00:00"]
            (self.das_a if kind == "appeared" else self.das_b).append(row)
        else:
            return None
        self.records.append(rec)
        return rec


def _observable(e):
    """The entry can be observed by the detector (and realized by State)."""
    if e.get("kind") == "dasha_shift" or e["table"] == "l1_tajik_varsha_year_lords" or e["table"] == "panchanga_daily":
        return False
    if e["table"] == "chart_dashas" and set(e.get("change_types") or ()) == {"tier"}:
        return False
    return True


def _kinds(e):
    ks = list(e.get("change_types") or ALL_KINDS)
    if e["table"] == "chart_divisionals":
        ks = [k for k in ks if k != "tier"]
    if e["table"] == "chart_dashas":
        ks = [k for k in ks if k in ("appeared", "disappeared")]
    return ks


def _combos(e):
    keys = e.get("fact_keys") or ["k"]
    ays = e.get("ayanamsha_ids") or AYS
    return [(c, k, a) for c in e["categories"] for k in keys for a in ays]


def _target(e, over=0):
    """How many changes the entry wants: exact n; min (at least 1 when the entry is not optional); the upper end plus `over`."""
    ec = e.get("expected_count")
    if ec is None:
        return 0 if e.get("optional") else 1
    if "exact" in ec:
        return ec["exact"]
    return max(ec.get("min", 0), 1 if not e.get("optional") and ec.get("max", 1) >= 1 else 0)


def _matches(entry, rec):
    return fd.entry_matches(entry, rec)


def _build_expected(hooks, chart_id, only=None):
    """Union of every applicable hook's expected change. Entries with fewer categories are realized first so the broad ones
    (tiers.json entry 0) only top up what the narrow ones (special_lagna, kp_cuspal_significators) already produced."""
    st = State(chart_id)
    applicable = [h for h in hooks if fd.applies_to_chart(h, chart_id) and (only is None or h["lane"] == only)]
    allentries = [(h, i, e) for h in applicable for i, e in enumerate(h["may_change"]) if _observable(e)]
    allentries.sort(key=lambda t: (len(t[2]["categories"]), -len(t[2].get("fact_keys") or []), t[0]["lane"], t[1]))
    for h, i, e in allentries:
        want = _target(e)
        have = sum(1 for r in st.records if _matches(e, r))
        need = want - have
        assert need >= 0, f"{h['lane']}[{i}]: realized {have} matching changes already, more than its target {want} (entries overlap)"
        combos = _combos(e)
        kinds = _kinds(e)
        assert kinds, f"{h['lane']}[{i}]: no change kind the state builder can realize"
        # prefer combos that no OTHER entry (of any hook in play) also matches, so overlapping entries do not inflate each other
        def foreign(c, k, a, kind):
            probe = {"table": e["table"], "category": c, "fact_key": k, "ayanamsha": a, "change": kind}
            return any(x is not e and _matches(x, probe) for _, _, x in allentries)
        pool = [(c, k, a, kind) for (c, k, a) in combos for kind in kinds if not foreign(c, k, a, kind)]
        if not pool:
            pool = [(c, k, a, kind) for (c, k, a) in combos for kind in kinds]
        j = 0
        made = 0
        while made < need:
            c, k, a, kind = pool[j % len(pool)]
            j += 1
            rec = st.add(e["table"], c, k, a, kind)
            assert rec is not None, f"{h['lane']}[{i}]: cannot realize {kind} on {e['table']}"
            made += 1
    return st, applicable


def _compare(st, hooks, chart_id):
    return fd.compare_states(st.snap(), st.cur(), hooks, chart_id, have_dash=True, have_daily=False)


def _failures(rep):
    return {k: v for k, v in rep["failure_counts"].items() if v}


# ----------------------------------------------------------------------------------------------- static hook checks
def test_hook_directory_shape():
    hooks = _load_hooks()
    assert hooks, "the hook directory has no top-level *.json"
    assert {p.stem for p in _hook_files()} == EXPECTED_HOOK_STEMS, (
        sorted(EXPECTED_HOOK_STEMS - {p.stem for p in _hook_files()}), sorted({p.stem for p in _hook_files()} - EXPECTED_HOOK_STEMS))
    assert len(_hook_files()) == 22
    for stem, h in hooks.items():
        assert h.get("lane") == stem, f"{stem}.json: lane must equal the file stem"
        for i, e in enumerate(h["may_change"]):
            assert e.get("table") != "chart_vichara", f"{stem}[{i}]: chart_vichara is outside the detector's tables; its declaration stays under evidence/"


def test_vichara_declaration_stays_under_evidence():
    assert (HOOKS_DIR / "evidence" / "ga_vichara_writer_HOOK_DECLARATION.json").is_file()
    assert (HOOKS_DIR / "evidence" / "ga_vichara_writer_ACCEPTANCE.sql").is_file()
    assert not (HOOKS_DIR / "ga_vichara_writer.json").exists()
    assert not (HOOKS_DIR / "ga_vichara.json").exists()
    # the old-shape argala declaration was moved under evidence/, never left as a second top-level file
    assert (HOOKS_DIR / "evidence" / "argala_HOOK_DECLARATION_old_shape.json").is_file()


def test_new_entries_state_their_source():
    hooks = _load_hooks()
    for stem in sorted(PHASE3_HOOKS & set(hooks)):
        for i, e in enumerate(hooks[stem]["may_change"]):
            if e.get("optional") or e.get("expected_count") is not None:
                assert "source" in (e.get("note") or "").lower(), f"{stem}[{i}]: a counted entry must state its source evidence in note"


def test_optional_only_for_the_five_chart_dependent_categories():
    five = {"bhava_chalit_rasi_divergence", "combustion_relationship", "graha_yuddha", "parivartana_pairs", "retrograde_aspect_modification"}
    seen = set()
    for stem, h in _load_hooks().items():
        for i, e in enumerate(h["may_change"]):
            if e.get("optional"):
                assert set(e["categories"]) <= five, f"{stem}[{i}]: optional is reserved for the five chart-dependent categories"
                assert "expected_count" in e and e["expected_count"].get("max"), f"{stem}[{i}]: an optional entry carries its upper bound"
                seen |= set(e["categories"])
    assert seen == five


# ----------------------------------------------------------------------------------------------- generic per-hook proofs
def _hook_params():
    return [pytest.param(p.stem, id=p.stem) for p in _hook_files()]


@needs_detector
@pytest.mark.parametrize("stem", [p.stem for p in _hook_files()])
def test_T1_declared_change_passes(stem):
    hooks = _load_hooks()
    h = hooks[stem]
    chart = _chart_for(h)
    st, applicable = _build_expected([h], chart, only=stem)
    rep = _compare(st, [h], chart)
    assert not _failures(rep), (stem, _failures(rep), rep["failures"])
    judged = {(r["lane"], r["entry"]): r for r in rep["expectations"]}
    for i, e in enumerate(h["may_change"]):
        if "expected_count" in e and _observable(e):
            assert judged[(stem, i)]["ok"], (stem, i, judged[(stem, i)])


@needs_detector
@pytest.mark.parametrize("stem", [p.stem for p in _hook_files()])
def test_T2_undeclared_change_fails(stem):
    hooks = _load_hooks()
    h = hooks[stem]
    chart = _chart_for(h)
    # (a) an undeclared CATEGORY on top of the expected after-state
    st, _ = _build_expected([h], chart, only=stem)
    st.add("chart_facts", "zz_undeclared_category", "k", "lahiri_chitrapaksha", "value")
    rep = _compare(st, [h], chart)
    assert rep["failure_counts"]["UNDECLARED_CHANGE"] == 1, rep["failures"]["UNDECLARED_CHANGE"]
    # (b) a declared category with an undeclared KIND of change
    for i, e in enumerate(h["may_change"]):
        if not _observable(e):
            continue
        declared = set(e.get("change_types") or ALL_KINDS)
        if e["table"] == "chart_dashas":
            continue
        for kind in ALL_KINDS:
            if kind in declared or (e["table"] == "chart_divisionals" and kind == "tier"):
                continue
            c, k, a = _combos(e)[0]
            probe = {"table": e["table"], "category": c, "fact_key": k, "ayanamsha": a, "change": kind}
            if any(_matches(x, probe) for x in h["may_change"]):
                continue  # another entry of this hook declares exactly this kind for the same scope
            st2, _ = _build_expected([h], chart, only=stem)
            st2.add(e["table"], c, k, a, kind)
            rep2 = _compare(st2, [h], chart)
            assert rep2["failure_counts"]["KIND_MISMATCH"] == 1, (stem, i, kind, rep2["failures"]["KIND_MISMATCH"], rep2["failures"]["UNDECLARED_CHANGE"])
            break


@needs_detector
@pytest.mark.parametrize("stem", [p.stem for p in _hook_files()])
def test_T3_count_off_by_one_fails(stem):
    hooks = _load_hooks()
    h = hooks[stem]
    chart = _chart_for(h)
    checked = 0
    for i, e in enumerate(h["may_change"]):
        ec = e.get("expected_count")
        if not ec or not _observable(e):
            continue
        if "exact" not in ec and "max" not in ec:
            continue  # min-only: cannot be exceeded
        st, _ = _build_expected([h], chart, only=stem)
        have = sum(1 for r in st.records if _matches(e, r))
        goal = (ec["exact"] + 1) if "exact" in ec else (ec["max"] + 1)
        combos, kinds = _combos(e), _kinds(e)
        j = 0
        while have < goal:
            c, k, a = combos[j % len(combos)]
            rec = st.add(e["table"], c, k, a, kinds[0])
            assert rec is not None
            have += 1
            j += 1
        rep = _compare(st, [h], chart)
        assert any(m.startswith(f"EXPECTATION MISMATCH {stem}[{i}]") for m in rep["failures"]["EXPECTATION_MISMATCH"]), (stem, i, rep["failures"]["EXPECTATION_MISMATCH"][:3])
        checked += 1
    assert checked or not any(e.get("expected_count") and ("exact" in e["expected_count"] or "max" in e["expected_count"]) and _observable(e) for e in h["may_change"]), stem


@needs_detector
@pytest.mark.parametrize("stem", [p.stem for p in _hook_files()])
def test_T4_unchanged_state_has_no_declared_but_absent(stem):
    hooks = _load_hooks()
    h = hooks[stem]
    chart = _chart_for(h)
    st = State(chart)
    rep = fd.compare_states(st.snap(), st.snap(), [h], chart, have_dash=True, have_daily=False)
    assert rep["failure_counts"]["DECLARED_BUT_ABSENT"] == 0, rep["failures"]["DECLARED_BUT_ABSENT"]
    assert rep["failure_counts"]["UNDECLARED_CHANGE"] == 0 and rep["failure_counts"]["KIND_MISMATCH"] == 0
    mism = {m.split(" ")[2] for m in rep["failures"]["EXPECTATION_MISMATCH"]}
    for i, e in enumerate(h["may_change"]):
        if not _observable(e):
            continue
        ec = e.get("expected_count")
        label = f"{stem}[{i}]"
        needs_change = bool(ec and (("exact" in ec and ec["exact"] > 0) or ec.get("min", 0) > 0))
        if needs_change:
            assert label in mism, f"{label}: expected a positive count but the unchanged state did not flag it"
        else:
            assert label not in mism, f"{label}: an entry that allows zero must not fail on an unchanged state"
    warned = {w.split(" ")[1] for w in rep["warnings"]}
    for i, e in enumerate(h["may_change"]):
        if e.get("optional") and "expected_count" not in e:
            assert f"{stem}[{i}]" in warned


@needs_detector
def test_T_NC_unobservable_entries_are_not_checked_never_absent():
    h = _load_hooks()["tiers"]
    st = State(CANON)
    rep = fd.compare_states(st.snap(), st.snap(), [h], CANON, have_dash=True, have_daily=False)
    nc = {n["id"] for n in rep["not_checked"]}
    assert "tiers[1]" in nc and "tiers[2]" in nc
    assert not any("tiers[1]" in m or "tiers[2]" in m for m in rep["failures"]["DECLARED_BUT_ABSENT"] + rep["failures"]["EXPECTATION_MISMATCH"])
    assert rep["verdict"] != "PASS"  # the standing NOT CHECKED registry is never empty


# ----------------------------------------------------------------------------------------------- whole directory together
def _all_hooks():
    return list(_load_hooks().values())


@needs_detector
@pytest.mark.parametrize("chart", [CANON, ABHI], ids=["canonical", "abhinandan"])
def test_T5_whole_directory_expected_after_state_passes(chart):
    hooks = _all_hooks()
    st, applicable = _build_expected(hooks, chart)
    rep = _compare(st, applicable, chart)
    assert not _failures(rep), (_failures(rep), {k: v[:3] for k, v in rep["failures"].items() if v})
    assert rep["verdict"] == "NOT_CHECKED"  # nothing failed; the standing NOT CHECKED registry keeps it from PASS


@needs_detector
@pytest.mark.parametrize("chart", [CANON, ABHI], ids=["canonical", "abhinandan"])
def test_T5_whole_directory_unchanged_state(chart):
    hooks = [h for h in _all_hooks() if fd.applies_to_chart(h, chart)]
    st = State(chart)
    rep = fd.compare_states(st.snap(), st.snap(), hooks, chart, have_dash=True, have_daily=False)
    assert rep["failure_counts"]["DECLARED_BUT_ABSENT"] == 0, rep["failures"]["DECLARED_BUT_ABSENT"]
    assert rep["failure_counts"]["UNDECLARED_CHANGE"] == 0 and rep["failure_counts"]["KIND_MISMATCH"] == 0
    # every non-pass is an entry with a positive lower bound; list them so a reviewer sees exactly which changes the hooks insist on
    for m in rep["failures"]["EXPECTATION_MISMATCH"]:
        assert "observed 0" in m, m


# ----------------------------------------------------------------------------------------------- lane scenarios (independent of the generator)
def _scenario(hooks, chart, before, after, divs_before=(), divs_after=()):
    snap = {"chart_facts": [["lahiri_chitrapaksha", "zz_filler", "F", "k", "x", "", "single"]] + before,
            "divisionals": [["lahiri_chitrapaksha", "D0", "G0", "zz_filler", "k", "x", "", ""]] + list(divs_before),
            "dashas": [["lahiri_chitrapaksha", "zz_sys", 1, "/Z", "2000-01-01T00:00:00+00:00", "2000-02-01T00:00:00+00:00"]]}
    cur = {"chart_facts": [["lahiri_chitrapaksha", "zz_filler", "F", "k", "x", "", "single"]] + after,
           "divisionals": [["lahiri_chitrapaksha", "D0", "G0", "zz_filler", "k", "x", "", ""]] + list(divs_after),
           "dashas": snap["dashas"]}
    return fd.compare_states(snap, cur, hooks, chart, have_dash=True, have_daily=False)


def _only(*stems):
    hs = _load_hooks()
    return [hs[s] for s in stems]


_KV = {"assigned_graha": ("Mars", ""), "sign": ("Aries", ""), "karaka_rank": ("", "8"), "house_d1": ("", "3"), "karaka_school": ("kn_rao_rahu_included", ""),
       "longitude_sidereal": ("", "248.3358"), "degree_in_sign": ("", "8.3358")}


@needs_detector
def test_LS_karaka_roles_relabel_on_the_lane_evidence():
    """kn_rao ranks 5-8 relabelled: per ayanamsha PITRIKARAKA appears (7 keys), STRIKARAKA disappears (7 keys), strikaraka_alias
    appears once, and the three relabelled subjects change assigned_graha and karaka_rank (6 value changes per ayanamsha, the floor)."""
    before, after = [], []
    for ay in AYS:
        for k, (t, n) in _KV.items():
            before.append([ay, "karaka_chara_position", "STRIKARAKA", k, t, n, "single_pass"])
            after.append([ay, "karaka_chara_position", "PITRIKARAKA", k, t, n, "single_pass"])
        after.append([ay, "karaka_chara_position", "DARAKARAKA", "strikaraka_alias", "STRIKARAKA", "", "single"])
        for subj in ("PUTRAKARAKA", "GNATIKARAKA", "DARAKARAKA"):
            before += [[ay, "karaka_chara_position", subj, "assigned_graha", "Mars", "", "single_pass"], [ay, "karaka_chara_position", subj, "karaka_rank", "", "5", "single_pass"]]
            after += [[ay, "karaka_chara_position", subj, "assigned_graha", "Venus", "", "single_pass"], [ay, "karaka_chara_position", subj, "karaka_rank", "", "6", "single_pass"]]
    rep = _scenario(_only("karaka_roles"), CANON, before, after)
    exp = {(r["lane"], r["entry"]): r for r in rep["expectations"]}
    assert exp[("karaka_roles", 0)]["observed"] == 35 and exp[("karaka_roles", 1)]["observed"] == 5
    assert exp[("karaka_roles", 2)]["observed"] == 35 and exp[("karaka_roles", 3)]["observed"] == 30
    assert not _failures(rep), (_failures(rep), rep["failures"])


@needs_detector
def test_LS_gandanta_variant_twins_and_a_surprise():
    hs = _only("gandanta")
    before, after = [], []
    for ay in AYS:
        for s in range(10):
            before.append([ay, "graha_gandanta", f"G{s}", "is_gandanta", "false", "", "single"])
            after.append([ay, "graha_gandanta", f"G{s}", "is_gandanta", "false", "", "single"])
            after.append([ay, "graha_gandanta", f"G{s}", "is_gandanta", "false", "", "single"])  # the strict_0_48 twin
    rep = _scenario(hs, CANON, before, after)
    assert not _failures(rep) and {r["entry"]: r["observed"] for r in rep["expectations"]}[0] == 50
    # DOCUMENTED MASK: a false -> true flip on one of two occurrences is invisible (sorted occurrence pairing), so it is not a surprise the
    # detector can raise; the W7 hand read-back covers it. A NEW is_gandanta key (a different reason) IS caught by exact 0 on entry 1.
    flipped = [list(r) for r in after]
    flipped[0][4] = "true"
    assert not _failures(_scenario(hs, CANON, before, flipped))
    after2 = after + [["lahiri_chitrapaksha", "graha_gandanta", "G99", "is_gandanta", "true", "", "single"]]
    rep2 = _scenario(hs, CANON, before, after2)
    assert any(m.startswith("EXPECTATION MISMATCH gandanta[1]") for m in rep2["failures"]["EXPECTATION_MISMATCH"])


@needs_detector
def test_LS_sun_required_rupa_and_the_node_nulls():
    hs = _only("sun_required_rupa")
    before = [["INVARIANT", "graha_shadbala_total", "SUN", "required_rupa", "", "5", "classical_match"]]
    after = [["INVARIANT", "graha_shadbala_total", "SUN", "required_rupa", "", "6.5", "classical_match"]]
    for ay in AYS:
        before.append([ay, "graha_shadbala_total", "SUN", "ratio", "", "1.694", "single"])
        after.append([ay, "graha_shadbala_total", "SUN", "ratio", "", "1.3031", "single"])  # continuous: never a class change
        for node in ("RAH_MEAN", "KET_MEAN"):
            for h in range(1, 13):
                subj = f"{node}_IN_HOUSE_{h}"
                before += [[ay, "graha_in_house_composite_strength", subj, "bphs_weighted", "", "0.61", "single"],
                           [ay, "graha_in_house_composite_strength", subj, "simple_multiplication", "", "0.52", "single"],
                           [ay, "graha_in_house_composite_strength", subj, "cross_formula_divergence", "", "0.09", "computed_extension"]]
                after += [[ay, "graha_in_house_composite_strength", subj, "bphs_weighted", "", "", "floored"]]
    rep = _scenario(hs, CANON, before, after)
    obs = {r["entry"]: r["observed"] for r in rep["expectations"]}
    assert obs[0] == 1 and obs[1] == 0 and obs[2] == 120 and obs[3] == 120 and obs[4] == 240
    assert not _failures(rep), (_failures(rep), rep["failures"])


@needs_detector
def test_LS_ga_vargas_sentinels_are_one_occurrence_change():
    """2 stored sentinel rows -> 6: ONE key (ALL_VARGAS) goes from 1 to 5 occurrences = exactly one detector change."""
    hs = _only("ga_vargas_invariant_sentinels")
    row = lambda subj: ["INVARIANT", "ALL_VARGAS", "SCOPE_CAP", "scope_cap", "computation_status", "floored", "", ""]
    d_before = [row("a"), ["INVARIANT", "D81", "SCOPE_CAP", "scope_cap", "computation_status", "floored", "", ""]]
    d_after = [row(s) for s in "abcde"] + [d_before[1]]
    rep = _scenario(hs, CANON, [], [], d_before, d_after)
    assert {r["entry"]: r["observed"] for r in rep["expectations"]}[0] == 1 and not _failures(rep)


@needs_detector
def test_LS_sade_sati_placeholders_and_chandra_bala():
    hs = _only("sade_sati_placeholder_null", "chandra_bala_birth_moon_sign")
    before, after = [], []
    for ay in AYS:
        for p in range(6):
            before.append([ay, "sade_sati_phase", f"P{p}", "concurrent_mudda_lord", "PENDING_GA7_LOOKUP", "", "single"])
            after.append([ay, "sade_sati_phase", f"P{p}", "concurrent_mudda_lord", "", "", "single"])
        for p in range(2):
            before.append([ay, "sade_sati_concurrent_dasha_overlay", f"C{p}", "concurrent_mudda_lord", "PENDING_GA7_LOOKUP", "", "single"])
            after.append([ay, "sade_sati_concurrent_dasha_overlay", f"C{p}", "concurrent_mudda_lord", "", "", "single"])
        for s in range(12):
            changed = ay == "surya_siddhanta_classical" and s < 9
            before.append([ay, "chandra_bala_natal_baseline", f"H{s}", "classification", "favorable", "", "single"])
            after.append([ay, "chandra_bala_natal_baseline", f"H{s}", "classification", "unfavorable" if changed else "favorable", "", "single"])
    rep = _scenario(hs, CANON, before, after)
    obs = {(r["lane"], r["entry"]): r["observed"] for r in rep["expectations"]}
    assert obs[("sade_sati_placeholder_null", 0)] == 30 and obs[("sade_sati_placeholder_null", 1)] == 10 and obs[("chandra_bala_birth_moon_sign", 0)] == 9
    assert not _failures(rep)
    # one of the four other ayanamshas changing is a surprise
    k = next(i for i, r in enumerate(after) if r[1] == "chandra_bala_natal_baseline" and r[0] == "krishnamurti")
    after[k] = list(after[k]); after[k][4] = "neutral"
    rep2 = _scenario(hs, CANON, before, after)
    assert any(m.startswith("EXPECTATION MISMATCH chandra_bala_birth_moon_sign[1]") for m in rep2["failures"]["EXPECTATION_MISMATCH"])


@needs_detector
def test_LS_main_landed_categories_appear_exactly():
    hs = _only("ashtakavarga_bindu_contributor", "dasha_scope_cap", "yamakantaka")
    after = []
    n = 0
    for ay in AYS:
        for g in range(7):
            for c in range(8):
                for s in range(12):
                    after.append([ay, "ashtakavarga_bindu_contributor", f"G{g}_C{c}", f"sign_{s}", "", "1", "single"])
        for k in ("house_d1", "longitude_sidereal", "nakshatra", "nakshatra_lord", "pada", "sign", "sign_lord"):
            after.append([ay, "sensitive_point_gulika_mandi", "YAMAKANTAKA", k, "v", "", "single"])
    after.append(["INVARIANT", "dasha_scope_cap", "PRANA_DASHA", "level_5_not_computed", "x", "", "single"])
    rep = _scenario(hs, CANON, [], after)
    obs = {r["lane"]: r["observed"] for r in rep["expectations"]}
    assert obs == {"ashtakavarga_bindu_contributor": 3360, "dasha_scope_cap": 1, "yamakantaka": 35}, obs
    assert not _failures(rep)


@needs_detector
def test_LS_chart_dependent_categories_are_optional_with_an_upper_bound():
    h = _only("ga_structural_chart_geometry")
    rep = _scenario(h, CANON, [], [])
    assert not _failures(rep)  # none of the five appearing is fine
    after = [[ay, "graha_yuddha", f"P{i}", k, "", "1", "single"] for ay in AYS for i in range(21) for k in ("winner", "loser", "orb_deg")]
    rep2 = _scenario(h, CANON, [], after)
    assert not _failures(rep2)  # 315 = the structural maximum
    rep3 = _scenario(h, CANON, [], after + [["lahiri_chitrapaksha", "graha_yuddha", "P99", "winner", "", "1", "single"]])
    assert rep3["failure_counts"]["EXPECTATION_MISMATCH"] == 1  # 316 exceeds the bound


@needs_detector
def test_LS_argala_canonical_counts():
    hs = _only("argala")
    before, after = [], []
    for i in range(3444):
        before.append(["lahiri_chitrapaksha", "argala_natal_matrix", f"C{i}", "cell", "", "1.0", "single"])
        after.append(["lahiri_chitrapaksha", "argala_natal_matrix", f"C{i}", "cell", "no_occupant", "", "single"])
    for i in range(3756):
        before.append(["lahiri_chitrapaksha", "argala_natal_matrix", f"O{i}", "cell", "", "1.0", "single"])
        after.append(["lahiri_chitrapaksha", "argala_natal_matrix", f"O{i}", "cell", "", "1.0", "single"])
    for i in range(156):
        after.append(["lahiri_chitrapaksha", "argala_graha_natal", f"D1_G{i}", f"from_X_offset_{i}", "unobstructed", "3", "single"])
    rep = _scenario(hs, CANON, before, after)
    obs = {r["entry"]: r["observed"] for r in rep["expectations"]}
    assert obs[0] == 156 and obs[1] == 3444 and not _failures(rep)
    # the lane's hook is canonical only: on Abhinandan the same change is UNDECLARED there (argala_other_charts covers it with bounds)
    rep_a = _scenario(_only("argala", "argala_other_charts"), ABHI, before, after)
    assert not _failures(rep_a), _failures(rep_a)


# ----------------------------------------------------------------------------------------------- pinned literals (independent of the generator)
# Each figure is copied here from its lane evidence (see HOOKS_COMPLETENESS_v1_0.md) so that an edit to a hook count cannot pass
# silently just because the generator follows whatever the hook says.
PINNED_EXACT = {
    "argala": {0: 156, 1: 3444},
    "ashtakavarga_bindu_contributor": {0: 3360},
    "chandra_bala_birth_moon_sign": {0: 9},
    "dasha_scope_cap": {0: 1},
    "ga_vargas_invariant_sentinels": {0: 1},
    "gandanta": {0: 50},
    "karaka_roles": {0: 35, 1: 5, 2: 35},
    "sade_sati_placeholder_null": {0: 30, 1: 10},
    "sun_required_rupa": {0: 1, 2: 120, 3: 120, 4: 240},
    "tiers": {0: 19870, 3: 245, 4: 300},
    "tiers_other_charts": {1: 480, 2: 40, 5: 245, 6: 300},
    "yamakantaka": {0: 35},
}
PINNED_RANGE = {
    ("karaka_roles", 3): (30, 60),
    ("karaka_web_order", 0): (950, 1300),
    ("ga_structural_chart_geometry", 0): (0, 45),
    ("ga_structural_chart_geometry", 1): (0, 30),
    ("ga_structural_chart_geometry", 2): (0, 315),
    ("ga_structural_chart_geometry", 3): (0, 15),
    ("ga_structural_chart_geometry", 4): (0, 85),
}


# EVERY entry of EVERY hook, in order (None = the entry declares no count): a count, a bound or an entry added, dropped or
# re-ordered in any hook fails here, including the entries the PINNED_EXACT / PINNED_RANGE tables above do not name.
PINNED_ENTRY_COUNTS = {
    'argala': [{'exact': 156}, {'exact': 3444}, {'exact': 0}, {'exact': 0}, {'exact': 0}],
    'argala_other_charts': [{'min': 1, 'max': 360}, {'min': 1, 'max': 7200}, {'exact': 0}, {'exact': 0}, {'exact': 0}],
    'ashtakavarga_bindu_contributor': [{'exact': 3360}],
    'band_table': [{'exact': 0}],
    'chandra_bala_birth_moon_sign': [{'exact': 9}, {'exact': 0}, {'exact': 0}],
    'dasha_scope_cap': [{'exact': 1}],
    'ga_condition_fallback': [{'exact': 0}],
    'ga_strength_invariant_rows': [{'exact': 0}],
    'ga_structural_chart_geometry': [{'min': 0, 'max': 45}, {'min': 0, 'max': 30}, {'min': 0, 'max': 315}, {'min': 0, 'max': 15}, {'min': 0, 'max': 85}],
    'ga_vargas_invariant_sentinels': [{'exact': 1}],
    'gandanta': [{'exact': 50}, {'exact': 0}, {'min': 0, 'max': 15}],
    'karaka_dasha_roles': [{'exact': 0}],
    'karaka_roles': [{'exact': 35}, {'exact': 5}, {'exact': 35}, {'min': 30, 'max': 60}, {'exact': 0}, {'exact': 0}],
    'karaka_web_order': [{'min': 950, 'max': 1300}],
    'karaka_web_order_other_charts': [{'min': 1}],
    'sade_sati_placeholder_null': [{'exact': 30}, {'exact': 10}],
    'special_lagna_offset': [{'exact': 0}, {'exact': 0}],
    'special_lagna_offset_other_charts': [{'min': 0, 'max': 120}, {'exact': 0}],
    'sun_required_rupa': [{'exact': 1}, {'exact': 0}, {'exact': 120}, {'exact': 120}, {'exact': 240}, {'exact': 0}, {'exact': 0}],
    'tiers': [{'exact': 19870}, None, None, {'exact': 245}, {'exact': 300}],
    'tiers_other_charts': [{'min': 16900, 'max': 22750}, {'exact': 480}, {'exact': 40}, None, None, {'exact': 245}, {'exact': 300}],
    'yamakantaka': [{'exact': 35}],
}


def test_every_entry_count_of_every_hook_is_pinned():
    hooks = _load_hooks()
    assert set(PINNED_ENTRY_COUNTS) == set(hooks) == set(EXPECTED_HOOK_STEMS)
    for lane, counts in PINNED_ENTRY_COUNTS.items():
        assert [e.get("expected_count") for e in hooks[lane]["may_change"]] == counts, lane


def test_pinned_counts_match_the_lane_evidence():
    hooks = _load_hooks()
    for lane, entries in PINNED_EXACT.items():
        for i, n in entries.items():
            assert hooks[lane]["may_change"][i]["expected_count"] == {"exact": n}, (lane, i)
    for (lane, i), (lo, hi) in PINNED_RANGE.items():
        assert hooks[lane]["may_change"][i]["expected_count"] == {"min": lo, "max": hi}, (lane, i)


@needs_detector
def test_LS_tiers_entry_zero_contains_the_two_narrow_entries():
    """19,870 canonical tier changes = 245 special_lagna + 300 kp_cuspal_significators + 19,325 elsewhere in the list; the narrow
    entries are counted inside the broad one (so a 244 or 246 on special_lagna also moves entry 0)."""
    h = _load_hooks()["tiers"]
    cats = [c for c in h["may_change"][0]["categories"] if c not in ("special_lagna", "kp_cuspal_significators")]
    before, after = [], []
    for i in range(19325):
        before.append([AYS[i % 5], cats[i % len(cats)], f"S{i}", "k", "x", "", "single_pass"])
        after.append([AYS[i % 5], cats[i % len(cats)], f"S{i}", "k", "x", "", "single"])
    for cat, n in (("special_lagna", 245), ("kp_cuspal_significators", 300)):
        for i in range(n):
            before.append([AYS[i % 5], cat, f"S{i}", f"k{i}", "x", "", "two_pass_verified"])
            after.append([AYS[i % 5], cat, f"S{i}", f"k{i}", "x", "", "single"])
    obs = {r["entry"]: r["observed"] for r in _scenario([h], CANON, before, after)["expectations"]}
    assert obs == {0: 19870, 3: 245, 4: 300}
    # a 19,871st change, or 244 special_lagna rows, is caught
    rep = _scenario([h], CANON, before + [["lahiri_chitrapaksha", "arudha_pada", "X", "k", "x", "", "single_pass"]], after + [["lahiri_chitrapaksha", "arudha_pada", "X", "k", "x", "", "single"]])
    assert any(m.startswith("EXPECTATION MISMATCH tiers[0]") for m in rep["failures"]["EXPECTATION_MISMATCH"])
    rep2 = _scenario([h], CANON, before[:-1], after[:-1])
    assert any(m.startswith("EXPECTATION MISMATCH tiers[0]") or m.startswith("EXPECTATION MISMATCH tiers[4]") for m in rep2["failures"]["EXPECTATION_MISMATCH"])
