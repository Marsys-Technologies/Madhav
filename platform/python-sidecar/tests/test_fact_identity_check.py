"""
test_fact_identity_check.py — G-IDX corrected check (SS ruling, S-L1 rehearsal P3)
and the pure per-fact classifier used by `scripts/build_fact_identity_index.py`.

The corrected check (W7 abort rule, as AMENDED by SS 2026-10-03):
  1. rows in chart_fact_identity == parsed;
  2. parsed + identity_free + gap == total chart_facts rows;
  3. gap == 0 (target; the earlier "<= 15 known" bound is retired — the 15 were
     the YOGA_PANCHAKA rows, now classified);
  4. coverage of identity-bearing rows (parsed / (parsed + gap)) >= 99.98 %;
  5. the set of identity_free reasons == the 14 pre-S-L1 reasons + the one
     explicit amendment 'scope_cap_sentinel'; ANY other reason aborts.

Mutation proofs: `test_mutants_are_killed` builds a mutant of the check
function's own source for each relaxation (reason-set equality, gap
threshold, coverage threshold, partition-sum equation, rows==parsed, new
reasons allowed) and asserts the shared battery goes red on every one.
"""
from __future__ import annotations

import inspect
import textwrap

import pytest

from brahmagyan import fact_identity_check as fic
from brahmagyan.fact_identity_check import (
    IDENTITY_FREE_REASONS_ALLOWED,
    IDENTITY_FREE_REASONS_V1,
    SCOPE_CAP_SENTINEL_REASON,
    check_identity_index,
    classify_fact,
)

# ── the amended reason set is explicit and versioned ─────────────────────

_FOURTEEN = {
    "ashtakavarga_kakshya_index_not_house",
    "ayurdaya_method_label",
    "bhrigu_nadi_chakra_index_not_house",
    "dhaiya_subperiod_label_moon_relative_not_lagna_house",
    "dosha_label_catalog_label",
    "fixed_reference_lookup_table_row_not_natal_placement",
    "jaimini_karaka_role_label",
    "nakshatra_name_fifth_dimension_out_of_scope",
    "panchanga_constant_label",
    "sade_sati_cycle_phase_label_moon_relative_not_lagna_house",
    "saham_arabic_part_label",
    "special_point_or_aggregate_marker",
    "tajik_hadda_degree_term_index_not_house",
    "yoga_label_catalog_label",
}  # the 14 reasons measured on the S-L1 rehearsal (gidx_final_reasons.txt)


def test_v1_reason_set_is_exactly_todays_fourteen():
    assert IDENTITY_FREE_REASONS_V1 == frozenset(_FOURTEEN)
    assert len(IDENTITY_FREE_REASONS_V1) == 14


def test_allowed_set_is_fourteen_plus_exactly_one_amendment():
    assert IDENTITY_FREE_REASONS_ALLOWED == IDENTITY_FREE_REASONS_V1 | {"scope_cap_sentinel"}
    assert SCOPE_CAP_SENTINEL_REASON == "scope_cap_sentinel"
    assert len(IDENTITY_FREE_REASONS_ALLOWED) == 15
    assert fic.REASON_SET_VERSION  # versioned, non-empty


# ── fixtures: the S-L1 rehearsal END STATE after the parser fix ─────────
# total 147,751 (rehearsal), parsed 130,472 + 3,360 ashtakavarga contributors,
# identity_free 13,868 + 35 YAMAKANTAKA + 15 YOGA_PANCHAKA + 1 scope-cap, gap 0.

def _good_summary() -> dict:
    reasons = {
        "sade_sati_cycle_phase_label_moon_relative_not_lagna_house": 4792,
        "saham_arabic_part_label": 2800,
        "special_point_or_aggregate_marker": 2253 + 35 + 15,
        "dhaiya_subperiod_label_moon_relative_not_lagna_house": 1495,
        "tajik_hadda_degree_term_index_not_house": 1200,
        "jaimini_karaka_role_label": 530,
        "bhrigu_nadi_chakra_index_not_house": 280,
        "fixed_reference_lookup_table_row_not_natal_placement": 195,
        "panchanga_constant_label": 147,
        "ashtakavarga_kakshya_index_not_house": 120,
        "yoga_label_catalog_label": 34,
        "ayurdaya_method_label": 15,
        "dosha_label_catalog_label": 6,
        "nakshatra_name_fifth_dimension_out_of_scope": 1,
        "scope_cap_sentinel": 1,
    }
    ident_free = sum(reasons.values())
    parsed = 130472 + 3360
    return {
        "total_facts": 147751,
        "parsed": parsed,
        "identity_free": ident_free,
        "gap": 0,
        "identity_free_reasons": reasons,
        "rows_in_table": parsed,
    }


def test_fixture_is_internally_consistent():
    s = _good_summary()
    assert s["parsed"] + s["identity_free"] + s["gap"] == s["total_facts"]


def test_good_end_state_passes():
    r = check_identity_index(_good_summary())
    assert r.ok, r.render()
    assert r.failed == [] and r.not_evaluated == []


# ── the failing end state the rehearsal actually measured (P3) ───────────

def test_rehearsal_p3_end_state_before_fix_fails():
    s = {
        "total_facts": 147751, "parsed": 130472, "identity_free": 13868, "gap": 3411,
        "identity_free_reasons": {r: 1 for r in _FOURTEEN},
        "rows_in_table": 130472,
    }
    # make the reason counts sum to identity_free so ONLY gap/coverage fail
    s["identity_free_reasons"]["special_point_or_aggregate_marker"] += 13868 - 14
    # (judged against the pre-amendment 14-reason set that run actually had)
    r = check_identity_index(s, expected_reasons=IDENTITY_FREE_REASONS_V1)
    assert not r.ok
    names = {i.name for i in r.failed}
    assert names == {"gap_within_limit", "coverage_of_identity_bearing"}


def test_emptied_index_1205_rows_fails_rows_equals_parsed():
    s = _good_summary()
    s["rows_in_table"] = 1205  # the FK-cascade-emptied index (P3)
    r = check_identity_index(s)
    assert [i.name for i in r.failed] == ["rows_equal_parsed"]


# ── each clause individually ──────────────────────────────────────────────

def test_rows_not_equal_parsed_fails():
    s = _good_summary(); s["rows_in_table"] = s["parsed"] - 1
    assert "rows_equal_parsed" in {i.name for i in check_identity_index(s).failed}


def test_rows_not_measured_is_not_evaluated_not_green():
    # dry-run: nothing written, so rows==parsed has no detector -> null, not green (CLAUDE.md N.8)
    s = _good_summary(); s["rows_in_table"] = None
    r = check_identity_index(s)
    assert r.failed == []
    assert [i.name for i in r.not_evaluated] == ["rows_equal_parsed"]
    assert not r.ok


def test_partition_does_not_sum_to_total_fails():
    s = _good_summary(); s["total_facts"] += 1
    assert "partition_sums_to_total" in {i.name for i in check_identity_index(s).failed}
    s = _good_summary(); s["total_facts"] -= 1
    assert "partition_sums_to_total" in {i.name for i in check_identity_index(s).failed}


def test_reason_counts_must_sum_to_identity_free():
    s = _good_summary(); s["identity_free_reasons"]["saham_arabic_part_label"] -= 1
    assert "reason_counts_sum_to_identity_free" in {i.name for i in check_identity_index(s).failed}


def test_gap_of_one_fails_target_is_zero():
    s = _good_summary(); s["gap"] = 1; s["total_facts"] += 1; s["rows_in_table"] = s["parsed"]
    r = check_identity_index(s)
    assert "gap_within_limit" in {i.name for i in r.failed}


def test_old_known_gap_of_fifteen_no_longer_tolerated():
    s = _good_summary(); s["gap"] = 15; s["total_facts"] += 15
    assert "gap_within_limit" in {i.name for i in check_identity_index(s).failed}


def test_coverage_threshold_independent_of_gap_threshold():
    # 3 gap rows in 10,000 identity-bearing = 99.97 % < 99.98 %: with the gap
    # limit raised out of the way, coverage alone must still fail.
    s = _good_summary()
    s["parsed"] = 9997; s["gap"] = 3; s["identity_free"] = 100
    s["identity_free_reasons"] = {"saham_arabic_part_label": 100}
    s["total_facts"] = 9997 + 3 + 100; s["rows_in_table"] = 9997
    r = check_identity_index(s, max_gap=100, exact_reasons=False)
    assert {i.name for i in r.failed} == {"coverage_of_identity_bearing"}
    # exactly at threshold passes: 2 / 10,000 = 99.98 %
    s["parsed"] = 9998; s["gap"] = 2; s["total_facts"] = 9998 + 2 + 100; s["rows_in_table"] = 9998
    assert check_identity_index(s, max_gap=100, exact_reasons=False).ok


def test_new_reason_aborts():
    s = _good_summary()
    s["identity_free_reasons"]["brand_new_reason"] = 1
    s["identity_free"] += 1; s["total_facts"] += 1
    r = check_identity_index(s)
    assert {i.name for i in r.failed} == {"identity_free_reason_set"}
    assert "brand_new_reason" in r.failed[0].detail


def test_missing_reason_fails_under_exact_equality():
    s = _good_summary()
    n = s["identity_free_reasons"].pop("scope_cap_sentinel")
    s["identity_free"] -= n; s["total_facts"] -= n
    r = check_identity_index(s)
    assert {i.name for i in r.failed} == {"identity_free_reason_set"}
    assert "scope_cap_sentinel" in r.failed[0].detail


def test_subset_mode_tolerates_missing_but_never_a_new_reason():
    s = _good_summary()
    n = s["identity_free_reasons"].pop("scope_cap_sentinel")
    s["identity_free"] -= n; s["total_facts"] -= n
    assert check_identity_index(s, exact_reasons=False).ok
    s["identity_free_reasons"]["brand_new_reason"] = 1
    s["identity_free"] += 1; s["total_facts"] += 1
    assert not check_identity_index(s, exact_reasons=False).ok


def test_zero_reason_counts_are_not_observed_reasons():
    s = _good_summary(); s["identity_free_reasons"]["zero_count_noise"] = 0
    assert check_identity_index(s).ok


def test_empty_chart_is_not_a_pass():
    s = {"total_facts": 0, "parsed": 0, "identity_free": 0, "gap": 0,
         "identity_free_reasons": {}, "rows_in_table": 0}
    r = check_identity_index(s, exact_reasons=False)
    assert "facts_present" in {i.name for i in r.failed}


# ── MUTATION PROOFS ─────────────────────────────────────────────────────
# Every relaxation of the check must turn the battery red.

def _battery(fn) -> list[str]:
    """Return the names of battery cases `fn` gets WRONG (empty == all right).
    Each case pins the EXACT set of failing clauses, so a mutant that fails
    for a different reason (or not at all) is caught."""
    wrong: list[str] = []

    def case(name, summary, expect_failed, **kw):
        try:
            res = fn(summary, **kw)
            got = {i.name for i in res.failed}
        except Exception:  # a mutant that crashes is also "red"
            got = {"<crash>"}
        if got != set(expect_failed):
            wrong.append(name)

    case("good", _good_summary(), set())

    s = _good_summary(); s["rows_in_table"] = 1205
    case("rows_ne_parsed", s, {"rows_equal_parsed"})

    s = _good_summary(); s["total_facts"] += 1
    case("partition_over", s, {"partition_sums_to_total"})
    s = _good_summary(); s["total_facts"] -= 1
    case("partition_under", s, {"partition_sums_to_total"})

    s = _good_summary(); s["gap"] = 1; s["total_facts"] += 1
    case("gap_1", s, {"gap_within_limit"})
    s = _good_summary(); s["gap"] = 15; s["total_facts"] += 15
    case("gap_15", s, {"gap_within_limit"})

    s = _good_summary()
    s["parsed"] = 9997; s["gap"] = 3; s["identity_free"] = 100
    s["identity_free_reasons"] = {"saham_arabic_part_label": 100}
    s["total_facts"] = 10100; s["rows_in_table"] = 9997
    case("coverage_9997", s, {"coverage_of_identity_bearing"}, max_gap=100, exact_reasons=False)

    s = _good_summary(); s["identity_free_reasons"]["brand_new_reason"] = 1
    s["identity_free"] += 1; s["total_facts"] += 1
    case("new_reason_exact", s, {"identity_free_reason_set"})
    case("new_reason_subset", s, {"identity_free_reason_set"}, exact_reasons=False)

    s = _good_summary(); n = s["identity_free_reasons"].pop("scope_cap_sentinel")
    s["identity_free"] -= n; s["total_facts"] -= n
    case("missing_reason_exact", s, {"identity_free_reason_set"})
    case("missing_reason_subset_tolerated", s, set(), exact_reasons=False)

    s = _good_summary(); s["identity_free_reasons"]["saham_arabic_part_label"] -= 1
    case("reason_counts_mismatch", s, {"reason_counts_sum_to_identity_free"})
    return wrong


def test_battery_is_green_on_the_real_function():
    assert _battery(check_identity_index) == []


def _mutant(old: str, new: str):
    src = textwrap.dedent(inspect.getsource(check_identity_index))
    assert src.count(old) == 1, f"mutation anchor not unique/present: {old!r} ({src.count(old)})"
    ns = dict(vars(fic))
    exec(compile(src.replace(old, new), "<mutant>", "exec"), ns)
    return ns["check_identity_index"]


MUTANTS = {
    "reason-set equality relaxed to subset": ("reasons_ok = observed == expected", "reasons_ok = observed <= expected"),
    "new reasons allowed": ("reasons_ok = observed <= expected", "reasons_ok = True"),
    "reason-set check dropped (exact branch)": ("reasons_ok = observed == expected", "reasons_ok = True"),
    "gap threshold relaxed to the old 15": ("gap_ok = gap <= max_gap", "gap_ok = gap <= 15"),
    "gap threshold dropped": ("gap_ok = gap <= max_gap", "gap_ok = True"),
    "coverage threshold relaxed": ("coverage_ok = coverage_pct >= min_coverage_pct", "coverage_ok = coverage_pct >= 90.0"),
    "coverage threshold dropped": ("coverage_ok = coverage_pct >= min_coverage_pct", "coverage_ok = True"),
    "partition-sum equation dropped": ("sum_ok = parsed + identity_free + gap == total", "sum_ok = True"),
    "rows == parsed dropped": ("rows_ok = rows == parsed", "rows_ok = True"),
    "reason-count sum dropped": ("reason_sum_ok = sum(counts.values()) == identity_free", "reason_sum_ok = True"),
}


@pytest.mark.parametrize("label", sorted(MUTANTS))
def test_mutants_are_killed(label):
    old, new = MUTANTS[label]
    mutant = _mutant(old, new)
    assert _battery(mutant) != [], f"mutant SURVIVED (battery stayed green): {label}"


# ── classify_fact: the 3-way partition (parsed / identity_free / gap) ────

def test_unknown_category_and_subject_lands_in_gap_not_identity_free():
    kind, payload = classify_fact("brand_new_category", "NEVER_SEEN_BEFORE_SUBJECT", "some_key")
    assert kind == "gap" and payload is None


def test_unknown_subject_in_a_known_category_lands_in_gap():
    # a known category is NOT a free pass (only the two open-ended label catalogs are)
    assert classify_fact("ashtakavarga_bindu_contributor", "SUN-CONTRIBUTOR_SUN-SIGN_13", "bindus")[0] == "gap"
    assert classify_fact("panchanga_special_yoga_combinations", "YOGA_SOMETHING_NEW", "combination_name")[0] == "gap"
    assert classify_fact("sensitive_point_gulika_mandi", "NEW_UPAGRAHA", "sign")[0] == "gap"
    assert classify_fact("dasha_scope_cap", "SIXTH_DASHA", "level_6_not_computed")[0] == "gap"


@pytest.mark.parametrize("category,subject,key,kind,detail", [
    ("ashtakavarga_bindu_contributor", "SUN-CONTRIBUTOR_SUN-SIGN_1", "bindus", "parsed", "ashtakavarga_contributor_graha_sign"),
    ("ashtakavarga_bindu_sign", "SUN-SIGN_1", "bindus", "parsed", "hyphen_graha_sign"),
    ("sensitive_point_gulika_mandi", "YAMAKANTAKA", "sign", "identity_free", "special_point_or_aggregate_marker"),
    ("sensitive_point_gulika_mandi", "GULIKA", "sign", "identity_free", "special_point_or_aggregate_marker"),
    ("panchanga_special_yoga_combinations", "YOGA_PANCHAKA", "combination_name", "identity_free", "special_point_or_aggregate_marker"),
    ("dasha_scope_cap", "PRANA_DASHA", "level_5_not_computed", "identity_free", "scope_cap_sentinel"),
])
def test_the_four_rehearsal_gap_categories_now_classify(category, subject, key, kind, detail):
    got_kind, payload = classify_fact(category, subject, key)
    assert got_kind == kind
    if kind == "parsed":
        assert payload.parse_rule == detail
    else:
        assert payload == detail
        assert payload in IDENTITY_FREE_REASONS_ALLOWED
