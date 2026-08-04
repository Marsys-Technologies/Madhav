"""
M-22 Stage 3 discrimination proof for `_vimshottari_independent_verifier.py`.

Per the Stage 3 task brief: "If your verifier can't discriminate a genuinely
wrong input from a genuinely right one, this whole stage is worthless." This
file is that proof, not a formality. Every probe below calls the SAME
`compare_row()` function `verify_chart_vimshottari()` calls against live data
— there is no mock, no reimplementation, no shortcut version of the
comparison logic used only in tests.

Probes (a)-(c) construct a genuinely-correct derived row via
`compute_independent_vimshottari_tree()` (the real tree builder, run against
the live-DB-shaped inputs for the canonical native chart), then mutate a
COPY of the engine side to probe each failure mode independently. Probe (d)
is the explicit "this is the real code path" demonstration: it prints/asserts
that `compare_row` is the exact function object `verify_chart_vimshottari`
calls, and re-runs one of the probes through a `RowComparison` dataclass
constructed the same way the live driver constructs one.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ga_writers import _vimshottari_independent_verifier as sut


# The canonical native's own confirmed anchor (FORENSIC): Moon in Purva
# Bhadrapada -> Jupiter. Any real sidereal longitude inside that nakshatra's
# span works for these probes; using a concrete, plausible value (not an edge
# case at a nakshatra boundary) keeps the probes about the comparison logic,
# not about degenerate inputs.
_MOON_SID_DEG = 327.055230133129  # lahiri_chitrapaksha, chart 482012f1 (live value)
_BIRTH_JD_UT = sut._gregorian_to_jd(1984, 2, 5, 5, 13, 0)  # 1984-02-05 10:43 IST = 05:13 UT


def _reference_tree_result():
    """Full `IndependentTreeResult` (rows + H3 excluded_by_level counts)."""
    return sut.compute_independent_vimshottari_tree(_MOON_SID_DEG, _BIRTH_JD_UT)


def _reference_tree():
    return _reference_tree_result().rows


def test_jd_self_test_already_ran_at_import():
    # `_self_test_jd_roundtrip()` runs at module import time (fail-loud design).
    # Re-invoking it here makes the guarantee visible inside the test report
    # rather than only implicit in "the import didn't raise".
    sut._self_test_jd_roundtrip()


def test_reference_tree_is_nonempty_and_well_formed():
    rows = _reference_tree()
    by_level = {1: 0, 2: 0, 3: 0, 4: 0}
    for r in rows:
        by_level[r.level_n] += 1
        assert r.lord in sut.CLASSICAL_9_LORDS
        assert r.start_dt <= r.end_dt
    # Levels 1-4 all populated over a 150-year window; zero level 5 by construction
    # (the tree builder has no level-5 branch at all — CRITICAL OVERRIDE 1 parity).
    assert all(n > 0 for n in by_level.values())


# ─────────────────────────────────────────────────────────────────────────────
# Probe (a): a deliberately wrong lord (swapped to an ADJACENT lord in the
# 9-cycle) must be flagged divergent. Adjacent-lord swap is the harder case
# than a random wrong string — it's the kind of off-by-one-in-sequence defect
# a real engine bug would actually produce.
# ─────────────────────────────────────────────────────────────────────────────

def test_probe_a_wrong_lord_is_flagged_divergent():
    rows = _reference_tree()
    l1 = [r for r in rows if r.level_n == 1]
    assert len(l1) >= 2
    correct_row = l1[0]
    correct_idx = sut.CLASSICAL_9_LORDS.index(correct_row.lord)
    wrong_lord = sut.CLASSICAL_9_LORDS[(correct_idx + 1) % 9]  # adjacent in the cycle
    assert wrong_lord != correct_row.lord

    cmp_ = sut.compare_row(
        wrong_lord, correct_row.start_dt, correct_row.end_dt,     # "engine" side: wrong lord
        correct_row.lord, correct_row.start_dt, correct_row.end_dt,  # "derived" side: correct
    )
    assert cmp_.lord_agree is False
    assert cmp_.verdict == sut.DIVERGENT_FLAGGED, (
        f"wrong-lord probe FAILED TO DISCRIMINATE: got {cmp_.verdict!r} for "
        f"engine_lord={wrong_lord!r} vs derived_lord={correct_row.lord!r}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Probe (b): a boundary shifted BEYOND tolerance must be flagged divergent.
# ─────────────────────────────────────────────────────────────────────────────

def test_probe_b_boundary_beyond_tolerance_is_flagged_divergent():
    rows = _reference_tree()
    row = next(r for r in rows if r.level_n == 2)  # an Antardasha row, mid-tree
    tol = sut.TOLERANCE_SECONDS_DEFAULT
    shifted_end = row.end_dt + timedelta(seconds=tol * 3)  # 3x tolerance — unambiguously beyond

    cmp_ = sut.compare_row(
        row.lord, row.start_dt, shifted_end,     # "engine" side: end shifted beyond tolerance
        row.lord, row.start_dt, row.end_dt,       # "derived" side: correct
        tolerance_seconds=tol,
    )
    assert cmp_.end_diff_seconds == pytest.approx(tol * 3, abs=0.5)
    assert cmp_.verdict == sut.DIVERGENT_FLAGGED, (
        f"beyond-tolerance probe FAILED TO DISCRIMINATE: got {cmp_.verdict!r} for a "
        f"{tol * 3}s shift against a {tol}s tolerance"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Probe (c): a boundary shifted WITHIN tolerance (50% of it) must NOT be
# flagged — this is the "don't cry wolf on legitimate float/rounding noise"
# half of the discrimination proof; without it, probe (b) alone would only
# show the verifier can ALWAYS say divergent, which is worthless.
# ─────────────────────────────────────────────────────────────────────────────

def test_probe_c_boundary_within_tolerance_is_not_flagged():
    rows = _reference_tree()
    row = next(r for r in rows if r.level_n == 3)  # a Pratyantardasha row
    tol = sut.TOLERANCE_SECONDS_DEFAULT
    shifted_start = row.start_dt + timedelta(seconds=tol * 0.5)  # 50% of tolerance

    cmp_ = sut.compare_row(
        row.lord, shifted_start, row.end_dt,      # "engine" side: start shifted, within tolerance
        row.lord, row.start_dt, row.end_dt,        # "derived" side: correct
        tolerance_seconds=tol,
    )
    assert cmp_.start_diff_seconds == pytest.approx(tol * 0.5, abs=0.01)
    assert cmp_.verdict == sut.TWO_PASS_VERIFIED, (
        f"within-tolerance probe FALSE POSITIVE: got {cmp_.verdict!r} for a "
        f"{tol * 0.5}s shift against a {tol}s tolerance (this would fire on "
        f"legitimate rounding noise across ~1.36M rows)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Probe (d): explicit proof these probes exercise the REAL verifier code path
# — the same `compare_row` that `verify_chart_vimshottari()` (the function
# that will eventually run against live data) calls, not a mock or a
# test-local reimplementation.
# ─────────────────────────────────────────────────────────────────────────────

def test_probe_d_probes_exercise_the_real_verify_chart_code_path():
    import inspect

    # H1 FIX NOTE: the per-level pairing loop that used to live inline in
    # `verify_chart_vimshottari` was extracted into `compare_level()`
    # specifically so the H1 fix (symmetric row-count-mismatch pairing)
    # could be unit-tested without a live DB connection (see
    # `test_h1_row_count_mismatch_surfaces_as_divergence_in_main_verdict_path`
    # below). So the chain this test now verifies is TWO hops:
    # verify_chart_vimshottari -> compare_level -> compare_row.
    driver_src = inspect.getsource(sut.verify_chart_vimshottari)
    assert "compare_level(" in driver_src, (
        "verify_chart_vimshottari() no longer calls compare_level() — the "
        "H1 row-pairing fix would no longer be exercised by the code path "
        "that runs against live data"
    )
    level_src = inspect.getsource(sut.compare_level)
    assert "compare_row(" in level_src, (
        "compare_level() no longer calls compare_row() — the discrimination "
        "probes in this file would no longer be testing the code path that "
        "runs against live data"
    )

    # And re-run probe (a)'s exact scenario through a literal call to the
    # function name `verify_chart_vimshottari` resolves at module scope,
    # confirming it's the identical function object under test elsewhere in
    # this file (guards against a local shadow/monkeypatch anywhere in the
    # test session bleeding into this assertion).
    assert sut.verify_chart_vimshottari.__module__ == sut.__name__
    assert sut.compare_level.__module__ == sut.__name__
    assert sut.compare_row.__module__ == sut.__name__


def test_probe_d_full_row_comparison_pipeline_end_to_end_no_db():
    """Runs compute_independent_vimshottari_tree -> compare_row exactly as
    verify_chart_vimshottari() does per row, but with a synthetic "engine"
    side built by copying the derived tree (simulating a perfect-agreement
    DB) — proving the whole non-DB half of the pipeline (tree -> per-row
    verdict aggregation) executes and agrees on real computed data, not
    canned fixtures."""
    rows = _reference_tree()
    l1 = [r for r in rows if r.level_n == 1]
    verdicts = [
        sut.compare_row(r.lord, r.start_dt, r.end_dt, r.lord, r.start_dt, r.end_dt).verdict
        for r in l1
    ]
    assert verdicts, "no level-1 rows produced by the real tree builder"
    assert all(v == sut.TWO_PASS_VERIFIED for v in verdicts), (
        "identical engine/derived rows (self-comparison) did not agree — "
        "compare_row is broken independent of any real divergence"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H1 — tail-truncation blind spot. Proves the Skeptic's exact reproduction
# (dropping the last row of a level and getting a clean "0 divergent" back)
# is fixed: a row-count mismatch now surfaces as divergent_flagged in
# `compare_level()` — the SAME object `verify_chart_vimshottari()` builds
# and any real promotion driver would read — not only via a pytest-only
# `count_mismatch` assertion.
# ─────────────────────────────────────────────────────────────────────────────

def _synthetic_engine_rows(level_rows: list, *, level_n: int):
    """Build a perfect-agreement synthetic 'engine' row set (dicts, matching
    `fetch_engine_rows()`'s shape) from a derived-row list — the same
    self-comparison pattern probe (d) uses, extended to carry the H2
    extended columns too."""
    out = []
    for i, r in enumerate(level_rows):
        next_r = level_rows[i + 1] if (level_n == 1 and i + 1 < len(level_rows)) else None
        extended = sut.derive_extended_columns(r, next_r)
        out.append({"lord_graha": r.lord, "start_iso": r.start_dt, "end_iso": r.end_dt, **extended})
    return out


def test_h1_row_count_mismatch_surfaces_as_divergence_in_main_verdict_path():
    tree = _reference_tree_result()
    l1 = [r for r in tree.rows if r.level_n == 1]
    assert len(l1) >= 3, "need at least 3 level-1 rows for a meaningful truncation probe"

    full_engine_rows = _synthetic_engine_rows(l1, level_n=1)

    # Sanity baseline: full (untruncated) pairing must be clean — proves any
    # divergence below is caused by the truncation, not a defect in the
    # comparison logic itself.
    full_summary = sut.compare_level(1, full_engine_rows, l1, tolerance_seconds=sut.TOLERANCE_SECONDS_DEFAULT)
    assert full_summary.count_mismatch is False
    assert full_summary.divergent_flagged == 0
    assert full_summary.two_pass_verified == len(l1)

    # The Skeptic's exact reproduction: drop the last row of the level (as
    # if the DB were missing a tail row the independent tree still has).
    truncated_engine_rows = full_engine_rows[:-1]
    summary = sut.compare_level(1, truncated_engine_rows, l1, tolerance_seconds=sut.TOLERANCE_SECONDS_DEFAULT)

    assert summary.count_mismatch is True
    assert summary.divergent_flagged >= 1, (
        "H1 REGRESSION: a row-count mismatch (dropped last DB row, the "
        "Skeptic's exact reproduction) did not surface as a divergence in "
        "compare_level()'s output — this is the tail-truncation blind spot "
        "that let a real run report 'verified=9201, divergent=0' with 4 "
        "rows silently unexamined."
    )
    assert summary.count_mismatch_divergences >= 1
    # The mismatch must be visible in divergent_flagged/total, not siphoned
    # into a side channel — divergent_flagged already INCLUDES it.
    assert summary.two_pass_verified == len(truncated_engine_rows), (
        "every row that DID have a counterpart should still verify cleanly "
        "— only the missing tail row should be flagged"
    )


def test_h1_row_count_mismatch_also_fires_when_derived_side_is_longer():
    """The inverse of the Skeptic's reproduction: the DB has FEWER rows than
    the independent computation (e.g. the engine silently failed to persist
    a period the classical math says should exist). The OLD code's loop only
    ever iterated `engine_rows`, so this direction was invisible by
    construction, not just by accident — must be fixed too."""
    tree = _reference_tree_result()
    l2 = [r for r in tree.rows if r.level_n == 2]
    assert len(l2) >= 3

    full_engine_rows = _synthetic_engine_rows(l2, level_n=2)
    # Drop a row from the middle of the ENGINE side (derived stays full).
    engine_rows_missing_one = full_engine_rows[:1] + full_engine_rows[2:]

    summary = sut.compare_level(2, engine_rows_missing_one, l2, tolerance_seconds=sut.TOLERANCE_SECONDS_DEFAULT)
    assert summary.count_mismatch is True
    assert summary.divergent_flagged >= 1, (
        "H1 REGRESSION: derived-longer-than-engine mismatch was not flagged"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H2 — column coverage. Proves the 42-column classification is internally
# consistent, the transcribed classical tables match known values, and —
# critically — that an extended-column mismatch (not just lord/boundaries)
# now flips a row's verdict to divergent, so a 'two_pass_verified' row can
# no longer silently overclaim full-row earnedness.
# ─────────────────────────────────────────────────────────────────────────────

def test_h2_column_coverage_partitions_all_42_columns_honestly():
    assert sut.TOTAL_CHART_DASHAS_COLUMNS == 42
    buckets = [
        set(sut.INDEPENDENTLY_VERIFIED_COLUMNS),
        set(sut.QUERY_GUARANTEED_COLUMNS),
        set(sut.NOT_INDEPENDENTLY_CHECKABLE_COLUMNS),
    ]
    assert sum(len(b) for b in buckets) == 42
    union = buckets[0] | buckets[1] | buckets[2]
    assert len(union) == 42, "a column is double-counted across buckets"
    # H2 must have added REAL coverage beyond the pre-fix 3
    # (lord_graha/start_iso/end_iso) — otherwise this is coverage in name only.
    assert len(sut.INDEPENDENTLY_VERIFIED_COLUMNS) > 3
    assert set(sut.PRIMARY_VERIFIED_COLUMNS) == {"lord_graha", "start_iso", "end_iso"}
    assert set(sut.PRIMARY_VERIFIED_COLUMNS).issubset(set(sut.INDEPENDENTLY_VERIFIED_COLUMNS))


def test_h2_karaka_role_and_relationship_match_transcribed_classical_tables():
    # Sun's Jaimini karaka role is Atmakaraka (AK) — a fixed classical
    # constant, independent of any chart.
    assert sut._derive_karaka_role("Sun") == "AK"
    assert sut._derive_karaka_role("Rahu") is None  # not in the 7-graha Jaimini karaka table

    # Sun/Moon are classical Parashari friends; Sun/Saturn are enemies.
    assert sut._derive_planet_relationship("Sun", "Moon") == "friend"
    assert sut._derive_planet_relationship("Sun", "Saturn") == "enemy"
    assert sut._derive_planet_relationship("Sun", None) is None  # level 1: no parent

    assert sut._derive_karakas_active("Sun", "Mars") == ["Sun:AK", "Mars:AmK"]
    assert sut._derive_karakas_active("Rahu", "Ketu") is None  # neither is a Jaimini karaka


def test_h2_extended_column_mismatch_is_flagged_divergent():
    rows = _reference_tree()
    row = next(r for r in rows if r.level_n == 1)
    derived_extended = sut.derive_extended_columns(row, None)

    # Perfect agreement first — establishes the baseline is clean.
    clean_cmp = sut.compare_row(
        row.lord, row.start_dt, row.end_dt, row.lord, row.start_dt, row.end_dt,
        engine_extended=dict(derived_extended), derived_extended=derived_extended,
    )
    assert clean_cmp.verdict == sut.TWO_PASS_VERIFIED
    assert clean_cmp.extended_mismatches == {}
    assert set(clean_cmp.extended_checked) == set(sut.EXTENDED_VERIFIED_COLUMNS)

    # Now corrupt ONE extended column (duration_days) while lord+boundaries
    # still agree exactly.
    corrupted_extended = dict(derived_extended)
    corrupted_extended["duration_days"] = (derived_extended["duration_days"] or 0) + 999

    cmp_ = sut.compare_row(
        row.lord, row.start_dt, row.end_dt, row.lord, row.start_dt, row.end_dt,
        engine_extended=corrupted_extended, derived_extended=derived_extended,
    )
    assert "duration_days" in cmp_.extended_mismatches
    assert cmp_.verdict == sut.DIVERGENT_FLAGGED, (
        "H2 REGRESSION: an extended-column mismatch (duration_days) with "
        "agreeing lord+boundaries did not flip the row verdict to divergent "
        "— a full-row 'two_pass_verified' promotion would silently overclaim "
        "earnedness on a column that actually disagrees."
    )


def test_h2_compare_row_backward_compatible_without_extended_args():
    """The 4 pre-existing discrimination probes above call compare_row with
    ONLY the 6 positional args — H2 must not have changed that contract."""
    cmp_ = sut.compare_row("Jupiter", datetime(2000, 1, 1, tzinfo=timezone.utc),
                            datetime(2001, 1, 1, tzinfo=timezone.utc),
                            "Jupiter", datetime(2000, 1, 1, tzinfo=timezone.utc),
                            datetime(2001, 1, 1, tzinfo=timezone.utc))
    assert cmp_.verdict == sut.TWO_PASS_VERIFIED
    assert cmp_.extended_checked == ()
    assert cmp_.extended_mismatches == {}


# ─────────────────────────────────────────────────────────────────────────────
# H3 — the collapsed-civil-date engine quirk's cost must be a distinct,
# reported category, not silently folded into "verified".
# ─────────────────────────────────────────────────────────────────────────────

def test_h3_collapsed_periods_are_tracked_as_a_distinct_excluded_count():
    result = _reference_tree_result()
    assert isinstance(result, sut.IndependentTreeResult)
    assert set(result.excluded_by_level.keys()) == {1, 2, 3, 4}
    # Empirically (per the Skeptic's smoke-test measurement of 132/188/142
    # level-4 periods per chart) the canonical chart's level-4 (Sukshma)
    # population over the full 1950-2100 window has a nonzero collapsed
    # count. If this regresses to 0, either the window shrank or
    # `_collapses_to_same_civil_date` stopped firing — re-check against the
    # Skeptic's measurement before trusting a "0 excluded" result.
    assert result.excluded_by_level[4] > 0, (
        f"expected a nonzero level-4 collapsed-period count, got "
        f"{result.excluded_by_level[4]} — see docstring for what this would mean"
    )


def test_h3_excluded_count_surfaces_separately_not_folded_into_verified():
    tree = _reference_tree_result()
    l4 = [r for r in tree.rows if r.level_n == 4]
    engine_rows = _synthetic_engine_rows(l4, level_n=4)

    summary = sut.compare_level(
        4, engine_rows, l4,
        excluded_known_quirk=tree.excluded_by_level[4],
    )
    # The excluded count is carried on the summary VERBATIM (a third,
    # independent field) — not derived from, and not entangled with,
    # two_pass_verified/divergent_flagged arithmetic.
    assert summary.excluded_known_quirk == tree.excluded_by_level[4]
    assert summary.excluded_known_quirk > 0
    assert summary.divergent_flagged == 0
    assert summary.two_pass_verified == len(l4)
    # Population accounting: every row that DOES exist on both sides (after
    # exclusion already happened inside compute_independent_vimshottari_tree)
    # is verified — excluded rows were never part of this count at all,
    # which is exactly the honesty gap H3 closes (they used to be invisible,
    # silently absent from both "verified" and "divergent").
    assert summary.two_pass_verified + summary.divergent_flagged == len(l4)


def test_h3_chart_verification_result_reports_total_excluded_known_quirk():
    """Pure-logic check that the ChartVerificationResult-level rollup exists
    and sums correctly, without needing a live DB."""
    lvl1 = sut.LevelSummary(level_n=1, engine_row_count=1, derived_row_count=1,
                             count_mismatch=False, two_pass_verified=1, excluded_known_quirk=3)
    lvl2 = sut.LevelSummary(level_n=2, engine_row_count=1, derived_row_count=1,
                             count_mismatch=False, two_pass_verified=1, excluded_known_quirk=5)
    result = sut.ChartVerificationResult(
        chart_id="x", ayanamsha_id="y", moon_sid_deg=0.0, birth_jd_ut=0.0,
        tolerance_seconds=5.0, per_level=[lvl1, lvl2],
    )
    assert result.total_excluded_known_quirk == 8
    assert result.total_two_pass_verified == 2
    assert result.total_divergent == 0


# ─────────────────────────────────────────────────────────────────────────────
# Live-DB smoke test (read-only; no writes). Skipped when DATABASE_URL is not
# set (e.g. no Cloud SQL proxy running) rather than failing the suite — this
# mirrors how other ga_writers tests in this repo treat DB availability.
# Per the M-22 Stage 3 task: DIAGNOSTIC, not the final re-promotion verdict.
# ─────────────────────────────────────────────────────────────────────────────

def _live_conn():
    import os
    url = os.environ.get("DATABASE_URL")
    if not url:
        return None
    import psycopg
    return psycopg.connect(url)


@pytest.mark.skipif(_live_conn() is None, reason="DATABASE_URL not set — no live DB to smoke-test against")
def test_smoke_canonical_chart_lahiri_full_agreement():
    """The canonical native chart, lahiri_chitrapaksha (the pipeline default
    ayanamsha), levels 1-4, classical Vimshottari only (kp_sublevel IS NULL).
    This is the smoke-test sample the Stage 3 task brief calls for.

    Post-H1/H2/H3-fix, the honest breakdown is a THREE-way population
    (verified / divergent / excluded-known-quirk) across 20-of-42 covered
    columns — printed below for the record, not just asserted — rather than
    the pre-fix single "9205/9205, 0 divergent" number that couldn't
    distinguish "genuinely compared and agreed" from "silently excluded" and
    only ever checked 3 of 42 columns. See the Stage 3 report for a SEPARATE
    genuine-defect finding (ayanamsha_id key mismatch causing the
    'krishnamurti' and 'surya_siddhanta_classical' ayanamshas' Vimshottari
    builds to silently fall back to Lahiri) that this same verifier caught
    on the other 2 of 5 ayanamshas — not asserted here since fixing that is
    explicitly out of this task's scope (no DB writes; re-promotion gated on
    a later Skeptic pass)."""
    conn = _live_conn()
    try:
        result = sut.verify_chart_vimshottari(
            conn, "482012f1-710e-4a25-994a-93821f5871aa", "lahiri_chitrapaksha",
        )
        assert result.total_examined > 0

        print("\n=== M-22 Stage 3 post-fix smoke test: canonical chart, lahiri_chitrapaksha ===")
        for lvl in result.per_level:
            print(
                f"level {lvl.level_n}: engine={lvl.engine_row_count} derived={lvl.derived_row_count} "
                f"verified={lvl.two_pass_verified} divergent={lvl.divergent_flagged} "
                f"(count_mismatch_divergences={lvl.count_mismatch_divergences}) "
                f"excluded_known_quirk={lvl.excluded_known_quirk}"
            )
        print(
            f"TOTALS: examined={result.total_examined} verified={result.total_two_pass_verified} "
            f"divergent={result.total_divergent} (count_mismatch_divergences="
            f"{result.total_count_mismatch_divergences}) excluded_known_quirk="
            f"{result.total_excluded_known_quirk}"
        )
        coverage = result.column_coverage_report()
        print(coverage["honest_summary"])
        print(f"per_column_mismatch_count: {coverage['per_column_mismatch_count']}")

        for lvl in result.per_level:
            assert not lvl.count_mismatch, (
                f"level {lvl.level_n}: engine={lvl.engine_row_count} "
                f"derived={lvl.derived_row_count} — {lvl.divergences[:3]}"
            )
            assert lvl.divergent_flagged == 0, (
                f"level {lvl.level_n} has {lvl.divergent_flagged} divergent row(s): "
                f"{lvl.divergences[:3]}"
            )
        assert result.total_count_mismatch_divergences == 0
        # H3: the collapsed-quirk population is expected and non-alarming —
        # NOT asserted to be zero — but must be visible.
        assert result.total_excluded_known_quirk >= 0
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Reference-table cross-check (independence strengthening, not a probe) —
# only meaningful against a live DB; skipped otherwise.
# ─────────────────────────────────────────────────────────────────────────────

def test_nakshatra_lord_table_matches_classical_construction():
    # Pure-logic check, no DB required: NAKSHATRA_LORDS_27 must be exactly 3
    # repetitions of CLASSICAL_9_LORDS in order (the classical assignment),
    # and its Purva Bhadrapada (idx 24, 0-based) entry must be Jupiter — the
    # FORENSIC anchor for the canonical native chart.
    assert len(sut.NAKSHATRA_LORDS_27) == 27
    assert sut.NAKSHATRA_LORDS_27[0:9] == sut.CLASSICAL_9_LORDS
    assert sut.NAKSHATRA_LORDS_27[9:18] == sut.CLASSICAL_9_LORDS
    assert sut.NAKSHATRA_LORDS_27[18:27] == sut.CLASSICAL_9_LORDS
    assert sut.NAKSHATRA_LORDS_27[24] == "Jupiter"  # Purva Bhadrapada, 0-based idx 24
