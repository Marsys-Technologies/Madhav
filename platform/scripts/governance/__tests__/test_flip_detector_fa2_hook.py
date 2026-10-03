"""test_flip_detector_fa2_hook.py -- the F-A2 hook (fa2_ga_vargas.json) against a model built from the F-A2 SPEC, not from a rehearsal run.

Spec: F_A2_KEY_WIDENING_D6_PLAN_v1_0.md (f_a2_key_widening/, branch TI-d6-dataplane-capture-fa2-001), section 3 table + section 8 criteria C3 to C6, and the
ga_vargas writer's row builders (ga_vargas_writer.py: _build_ashtakavarga_rows, _build_house_lord_rows, _build_d30_lord_per_amsa_rows, the scope_cap block).

The model below is the chart_divisionals slice of those four categories under the OLD six-column key (the first-written row of each key survives) and under the NEW
seven-column key (every row lands). It is fed to the detector's pure comparison with the REAL hook file. Passing proves the hook declares what the spec predicts; the
mutations prove that removing, inflating or broadening the hook, or adding a change the spec does not predict, is caught (a hook that blesses any change is no detector).

No database, no network: flip_detector.q is replaced by a tripwire.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
GOV_DIR = HERE.parent
FIX = HERE / "fixtures" / "flip_detector"
REAL_HOOKS = FIX / "hooks_real"

_TOOL = pathlib.Path(os.environ.get("FLIP_DETECTOR_TOOL_UNDER_TEST") or (GOV_DIR / "flip_detector.py"))
_spec = importlib.util.spec_from_file_location("flip_detector_fa2_hook_under_test", _TOOL)
F = importlib.util.module_from_spec(_spec)
sys.modules["flip_detector_fa2_hook_under_test"] = F
_spec.loader.exec_module(F)

NATIVE = F.NATIVE
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
LANE = "fa2_ga_vargas"
LIVE_DIR = HERE.parents[3] / "00_ARCHITECTURE" / "briefs" / "suvarna" / "exec" / "s_l1_attribution_hooks"   # not F.DEFAULT_HOOKS_DIR: a mutated copy of the tool lives elsewhere
LIVE_HOOK = LIVE_DIR / f"{LANE}.json"


@pytest.fixture(autouse=True)
def _no_database(monkeypatch):
    def tripwire(sql, retries=4):
        raise AssertionError("flip_detector test reached the database layer: " + sql[:80])
    monkeypatch.setattr(F, "q", tripwire)


# ---------------------------------------------------------------------------------------------- the spec model
VARGAS = [f"D{n}" for n in range(1, 31)]                       # spec: 30 vargas (the stored table has 30, not 32)
GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "SARVA"]   # spec: 96 ashtakavarga rows per varga = 8 labels x 12 signs
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
D30_ODD = [("Mars", 0, 5), ("Saturn", 5, 10), ("Jupiter", 10, 18), ("Mercury", 18, 25), ("Venus", 25, 30)]
D30_EVEN = [("Venus", 0, 5), ("Mercury", 5, 12), ("Jupiter", 12, 20), ("Saturn", 20, 25), ("Mars", 25, 30)]
AYS = list(F.AYANS)                                            # the five declared ayanamshas
FLOORED = ["Uranus", "Neptune", "Pluto", "Lilith", "MC"]       # spec: D81 sentinel + five floored bodies


def _row(ay, varga, graha, cat, key, text, num, sign):
    return [ay, varga, graha, cat, key, text, num, sign]


def new_rows(lagna_sign=0):
    """Every row the seven-column key stores (nothing collides). Rows are emitted in WRITER order, so the old six-column key keeps the first of each key."""
    rows = []
    for ay in AYS:
        for v in VARGAS:
            for g in GRAHAS:                                                   # varga_ashtakavarga: 12 sign rows per (graha, varga), shared fact_key 'bindus'
                for s in range(12):
                    rows.append(_row(ay, v, g, "varga_ashtakavarga", "bindus", "", str((s * 3 + len(g)) % 7), SIGNS[s]))
            for house in range(1, 13):                                         # varga_house_lord: twelve houses, graha = the sign lord, fact_key 'lord'
                sidx = (lagna_sign + house - 1) % 12
                rows.append(_row(ay, v, SIGN_LORDS[sidx], "varga_house_lord", "lord", SIGN_LORDS[sidx], str(house), SIGNS[sidx]))
        for s in range(12):                                                    # varga_d30_lord_per_amsa: five regions per sign, fact_key '<lord>_<start>_<end>'
            for lord, a, b in (D30_ODD if s % 2 == 0 else D30_EVEN):
                rows.append(_row(ay, "D30", lord, "varga_d30_lord_per_amsa", f"{lord}_{a}_{b}", lord, str(a), SIGNS[s]))
    rows.append(_row("INVARIANT", "D81", "SCOPE_CAP", "scope_cap", "computation_status", "intentionally_not_computed", "", ""))
    for _ in FLOORED:                                                          # the five floored bodies share ONE key (they differ only in fact_subject)
        rows.append(_row("INVARIANT", "ALL_VARGAS", "SCOPE_CAP", "scope_cap", "computation_status", "intentionally_not_computed", "", ""))
    return rows


def old_rows(lagna_sign=0):
    """Same writer stream under the six-column key with ON CONFLICT DO NOTHING: the first row of each key survives."""
    seen, out = set(), []
    for r in new_rows(lagna_sign):
        k = tuple(r[:5])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def anchor_facts():
    """The seven FORENSIC birth anchors the detector watches (an absent anchor is an ALERT, which would mask the verdict under test)."""
    facts = []
    for ay in F.AYANS:
        facts += [[ay, "graha_position", "SUN", "sign", "Capricorn", "", "single"], [ay, "graha_position", "MOON", "nakshatra", "Purva Bhadrapada", "", "single"],
                  [ay, "graha_position", "LAGNA", "sign", "Aries", "", "single"]]
    for cat, subj, key, val in (("panchanga_tithi", "TITHI_BIRTH", "name", "Shukla Tritiya"), ("panchanga_vara", "VARA_BIRTH", "name", "Ravivara"),
                                ("panchanga_yoga", "YOGA_BIRTH", "name", "Shiva"), ("panchanga_karana", "KARANA_BIRTH", "name", "Garaja")):
        facts.append(["INVARIANT", cat, subj, key, val, "", "single"])
    return facts


def state(div_rows):
    return {"chart_facts": anchor_facts(),
            "divisionals": copy.deepcopy(div_rows), "dashas": [], "daily": []}


def cmp(before, after, hooks, chart=NATIVE):
    return F.compare_states(state(before), state(after), hooks, chart, have_dash=False, have_daily=False)


def load_real(tmp_path, patch=None, name="h"):
    d = tmp_path / name
    d.mkdir(exist_ok=True)
    h = json.loads(LIVE_HOOK.read_text())
    if patch:
        patch(h)
    (d / f"{LANE}.json").write_text(json.dumps(h))
    hooks, errs = F.load_hooks(str(d), [LANE])
    assert not errs, errs
    return hooks


def counts(rows, cat):
    return len([r for r in rows if r[3] == cat])


# ---------------------------------------------------------------------------------------------- the model reproduces the spec's own numbers
def test_model_reproduces_the_spec_row_counts():
    """Spec section 3 table (canonical chart): ashtakavarga 1,200 -> 14,400; house_lord 1,050 -> 1,800; d30 50 -> 300; scope_cap 2 -> 6. If these fail the model, not the hook, is wrong."""
    o, n = old_rows(), new_rows()
    assert (counts(o, "varga_ashtakavarga"), counts(n, "varga_ashtakavarga")) == (1200, 14400)
    assert (counts(o, "varga_house_lord"), counts(n, "varga_house_lord")) == (1050, 1800)
    assert (counts(o, "varga_d30_lord_per_amsa"), counts(n, "varga_d30_lord_per_amsa")) == (50, 300)
    assert (counts(o, "scope_cap"), counts(n, "scope_cap")) == (2, 6)
    assert counts(n, "varga_ashtakavarga") // len(AYS) // len(VARGAS) == 96                 # acceptance C5
    assert counts(n, "varga_house_lord") // len(AYS) // len(VARGAS) == 12                   # acceptance C4
    assert counts(n, "varga_d30_lord_per_amsa") // len(AYS) == 60                           # acceptance C6
    assert counts(n, "scope_cap") == 6                                                      # acceptance C3


def test_model_gain_is_purely_additive():
    """The spec says the gained rows are rows the six-column key dropped: every old row is still present, none is removed or altered."""
    new_multiset = {}
    for r in new_rows():
        new_multiset[tuple(r)] = new_multiset.get(tuple(r), 0) + 1
    for r in old_rows():
        assert new_multiset.get(tuple(r), 0) >= 1, r


@pytest.mark.parametrize("lagna", range(12))
def test_house_lord_gain_does_not_depend_on_the_lagna(tmp_path, lagna):
    """Twelve consecutive signs always give Sun and Moon one house and the five other lords two: 750 keys for any lagna."""
    rep = cmp(old_rows(lagna), new_rows(lagna), load_real(tmp_path))
    assert rep["failure_counts"]["UNDECLARED_CHANGE"] == 0
    assert rep["failure_counts"]["EXPECTATION_MISMATCH"] == 0
    by = {tuple(k): v for k, v in rep["by_table_category_change_lane"]}
    assert by[("chart_divisionals", "varga_house_lord", "occurrence_count", LANE)] == 750


# ---------------------------------------------------------------------------------------------- the real hook attributes exactly the spec's change set
def test_real_hook_attributes_the_whole_spec_change_set(tmp_path):
    hooks = load_real(tmp_path)
    rep = cmp(old_rows(), new_rows(), hooks)
    assert rep["failure_counts"] == {k: 0 for k in rep["failure_counts"]}, rep["failures"]
    assert rep["changes_total"] == 3201          # 1,200 + 1,200 + 750 + 50 + 1 scope_cap (the live W7 run showed 3,200 undeclared without this hook: scope_cap was already attributed to ga_vargas_invariant_sentinels)
    assert rep["unattributed"] == 0
    by = {tuple(k): v for k, v in rep["by_table_category_change_lane"]}
    assert by == {("chart_divisionals", "varga_ashtakavarga", "occurrence_count", LANE): 1200,
                  ("chart_divisionals", "varga_ashtakavarga", "value", LANE): 1200,
                  ("chart_divisionals", "varga_house_lord", "occurrence_count", LANE): 750,
                  ("chart_divisionals", "varga_d30_lord_per_amsa", "occurrence_count", LANE): 50,
                  ("chart_divisionals", "scope_cap", "occurrence_count", LANE): 1}
    assert [e["ok"] for e in rep["expectations"]] == [True] * 7 and len(rep["expectations"]) == 7
    assert {e["observed"] for e in rep["expectations"]} == {1200, 750, 50, 1, 0}


def test_the_1200_value_changes_are_the_pairing_artifact_and_nothing_else(tmp_path):
    """Every value change is Aries (old S1 survivor) paired with Aquarius (first sorted new row); the old Aries row itself is unchanged."""
    rep = cmp(old_rows(), new_rows(), load_real(tmp_path))
    ch = F.diff_table("chart_divisionals",
                      F.occ_map(old_rows(), lambda r: tuple(r[:5]), lambda r: (r[5] or r[7], r[6], "")),
                      F.occ_map(new_rows(), lambda r: tuple(r[:5]), lambda r: (r[5] or r[7], r[6], "")), (3, 4))[0]
    vals = [c for c in ch if c["change"] == "value"]
    assert len(vals) == 1200 and {c["category"] for c in vals} == {"varga_ashtakavarga"}
    assert {c["before"][0] for c in vals} == {"Aries"} and {c["after"][0] for c in vals} == {"Aquarius"}
    assert rep["verdict"] != F.V_FAIL


def test_exit_code_is_not_a_pass_only_because_the_detector_has_standing_not_checked(tmp_path):
    rep = cmp(old_rows(), new_rows(), load_real(tmp_path))
    assert F.exit_code(rep) in (0, 4) and rep["verdict"] in (F.V_PASS, F.V_NOT_CHECKED)


# ---------------------------------------------------------------------------------------------- mutations of the HOOK
def _fails(rep):
    return rep["verdict"] == F.V_FAIL and F.exit_code(rep) == 2


def _flagged(rep):
    """changes the detector refuses to attribute: no entry at all (UNDECLARED) or an entry for the key that does not declare this KIND of change (KIND_MISMATCH)."""
    return rep["failure_counts"]["UNDECLARED_CHANGE"] + rep["failure_counts"]["KIND_MISMATCH"]


@pytest.mark.parametrize("drop,n", [(0, 1200), (1, 1200), (2, 750), (3, 50), (4, 1)])
def test_mutation_removing_a_declared_entry_is_caught(tmp_path, drop, n):
    """Entries 0 to 4 are the five predicted change groups. Dropping any one leaves exactly its changes flagged (UNDECLARED or KIND_MISMATCH, depending on whether a sibling
    entry still covers the key), never absorbed by the explicit-zero entries."""
    def patch(h):
        del h["may_change"][drop]
    rep = cmp(old_rows(), new_rows(), load_real(tmp_path, patch))
    assert _fails(rep)
    assert _flagged(rep) == n, rep["failure_counts"]


def test_mutation_removing_the_hook_entirely_leaves_every_change_undeclared():
    rep = cmp(old_rows(), new_rows(), [])
    assert _fails(rep) and rep["failure_counts"]["UNDECLARED_CHANGE"] == 3201


def test_mutation_removing_the_scope_cap_entry_does_not_lean_on_the_sentinels_hook(tmp_path):
    """The scope_cap change is also declared by ga_vargas_invariant_sentinels.json, but this hook must stand alone: dropping its entry leaves the change flagged."""
    def patch(h):
        del h["may_change"][4]
    rep = cmp(old_rows(), new_rows(), load_real(tmp_path, patch))
    assert _fails(rep) and _flagged(rep) == 1


def test_mutation_extra_entry_the_diff_does_not_have_is_declared_but_absent(tmp_path):
    def patch(h):
        h["may_change"].append({"table": "chart_divisionals", "categories": ["varga_dignity"], "change_types": ["occurrence_count"]})
    rep = cmp(old_rows(), new_rows(), load_real(tmp_path, patch))
    assert _fails(rep) and rep["failure_counts"]["DECLARED_BUT_ABSENT"] == 1
    assert "varga_dignity" in rep["failures"]["DECLARED_BUT_ABSENT"][0]


def test_mutation_inflated_or_deflated_count_is_an_expectation_mismatch(tmp_path):
    for entry, delta in ((0, 1), (0, -1), (2, 1), (3, -1), (4, 1)):
        def patch(h, entry=entry, delta=delta):
            h["may_change"][entry]["expected_count"]["exact"] += delta
        rep = cmp(old_rows(), new_rows(), load_real(tmp_path, patch, name=f"h{entry}_{delta}"))
        assert _fails(rep) and rep["failure_counts"]["EXPECTATION_MISMATCH"] == 1, (entry, delta, rep["failure_counts"])


# ---------------------------------------------------------------------------------------------- mutations of the DIFF (a change the spec does not predict)
def _after_with(fn):
    rows = new_rows()
    fn(rows)
    return rows


def test_a_real_value_change_in_house_lord_is_not_blessed(tmp_path):
    """The rehearsal stand-in (optional, value allowed, no counts) would have absorbed this; the real hook declares exact 0 value changes in house_lord."""
    def fn(rows):
        for r in rows:
            if r[3] == "varga_house_lord" and r[0] == "raman" and r[1] == "D9" and r[2] == "Sun":
                r[5] = "Moon"
                break
    rep = cmp(old_rows(), _after_with(fn), load_real(tmp_path))
    assert _fails(rep) and rep["failure_counts"]["EXPECTATION_MISMATCH"] == 1
    assert any("EXPECTATION MISMATCH fa2_ga_vargas[6]" in m for m in rep["failures"]["EXPECTATION_MISMATCH"])


def test_a_disappearing_ashtakavarga_key_is_not_blessed(tmp_path):
    def fn(rows):
        rows[:] = [r for r in rows if not (r[3] == "varga_ashtakavarga" and r[0] == "raman" and r[1] == "D9" and r[2] == "Mars")]
    rep = cmp(old_rows(), _after_with(fn), load_real(tmp_path))
    assert _fails(rep)
    assert rep["failure_counts"]["EXPECTATION_MISMATCH"] >= 1


def test_a_missing_non_aries_ashtakavarga_row_moves_the_count(tmp_path):
    """A sign row that fails to land (11 of 12 instead of 12) leaves the key at 11 occurrences: the key still changes, but the value of the count entry is exactly 1,200 keys,
    so this is NOT caught by the count -- it is caught because the pairing changes nothing here. Pin the truth: the loss is invisible to this hook (the S-L1 acceptance C5
    and the 14,400 row total are what prove 12 rows per key)."""
    def fn(rows):
        for i, r in enumerate(rows):
            if r[3] == "varga_ashtakavarga" and r[0] == "raman" and r[1] == "D9" and r[2] == "Mars" and r[7] == "Pisces":
                del rows[i]
                break
    rep = cmp(old_rows(), _after_with(fn), load_real(tmp_path))
    assert rep["verdict"] != F.V_FAIL     # documented blind spot: 1 -> 11 is still one occurrence_count change; row-grain completeness is acceptance C1/C5, not this detector


def test_documented_blind_spot_a_real_change_to_the_surviving_aries_row_is_hidden_by_the_pairing(tmp_path):
    """The 1,200 value changes are a pairing artifact (old Aries vs new Aquarius). If the Aries row's bindu number really changed, the detector still reports the same 1,200
    value changes, so the hook cannot see it. The hook's value entry says so and points to a hand read-back; this test pins the limit instead of pretending otherwise."""
    def fn(rows):
        for r in rows:
            if r[3] == "varga_ashtakavarga" and r[7] == "Aries" and r[0] == "raman" and r[1] == "D9" and r[2] == "Mars":
                r[6] = "99"
    rep = cmp(old_rows(), _after_with(fn), load_real(tmp_path))
    assert rep["verdict"] != F.V_FAIL
    assert "read it by hand" in json.loads(LIVE_HOOK.read_text())["may_change"][1]["note"]


def test_a_d30_key_outside_the_writers_ten_is_flagged(tmp_path):
    def fn(rows):
        rows.append(_row("raman", "D30", "Mars", "varga_d30_lord_per_amsa", "Mars_99_100", "Mars", "99", "Aries"))
    rep = cmp(old_rows(), _after_with(fn), load_real(tmp_path))
    assert _fails(rep) and _flagged(rep) + rep["failure_counts"]["EXPECTATION_MISMATCH"] >= 1


def test_a_stray_change_in_another_category_is_undeclared(tmp_path):
    before = old_rows() + [_row("raman", "D9", "Sun", "varga_dignity", "dignity", "exalted", "", "Aries")]
    after = new_rows() + [_row("raman", "D9", "Sun", "varga_dignity", "dignity", "debilitated", "", "Aries")]
    rep = cmp(before, after, load_real(tmp_path))
    assert _fails(rep) and rep["failure_counts"]["UNDECLARED_CHANGE"] == 1


def test_a_change_in_an_ayanamsha_the_spec_does_not_name_is_flagged(tmp_path):
    def fn(rows):
        rows.extend(_row("made_up_ayanamsha", "D9", "Sun", "varga_house_lord", "lord", "Sun", "2", "Leo") for _ in range(2))
    rep = cmp(old_rows(), _after_with(fn), load_real(tmp_path))
    assert _fails(rep) and _flagged(rep) + rep["failure_counts"]["EXPECTATION_MISMATCH"] >= 1


def test_the_hook_is_canonical_chart_only(tmp_path):
    """charts: ['482012f1'] -- another chart's F-A2 change is not covered here (Abhinandan / Kiran hold stale generations: S-L1b), so it reads undeclared, not silently blessed."""
    rep = cmp(old_rows(), new_rows(), load_real(tmp_path), chart=OTHER)
    assert _fails(rep) and rep["failure_counts"]["UNDECLARED_CHANGE"] == 3201


# ---------------------------------------------------------------------------------------------- the file itself
def test_live_hook_is_a_byte_copy_of_the_hooks_real_fixture():
    assert LIVE_HOOK.read_bytes() == (REAL_HOOKS / f"{LANE}.json").read_bytes()


def test_live_hook_directory_validates_with_the_24_stems(capsys):
    d = LIVE_DIR
    stems = sorted(p.stem for p in d.glob("*.json"))
    assert len(stems) == 24 and LANE in stems
    assert F.main(["--validate-hooks", "--hooks-dir", str(d), "--require-lanes", ",".join(stems)]) == 0
    assert F.main(["--validate-hooks", "--hooks-dir", str(d), "--require-lanes", ",".join(stems) + ",no_such_lane"]) == 2
    capsys.readouterr()


def test_hook_entries_cite_the_spec_not_only_a_run():
    h = json.loads(LIVE_HOOK.read_text())
    assert h["lane"] == LANE and h["pr"] == "#2858" and h["charts"] == ["482012f1"]
    assert "F_A2_KEY_WIDENING_D6_PLAN_v1_0.md" in h["description"]
    for i in (0, 2, 3, 4, 5, 6):
        assert "F_A2_KEY_WIDENING_D6_PLAN_v1_0.md" in h["may_change"][i]["note"], i
    assert h["may_change"][1]["note"].startswith("DERIVED, not stated by the spec")      # the pairing-artifact entry says so
    assert not any(e.get("optional") for e in h["may_change"]) and all("expected_count" in e for e in h["may_change"])
