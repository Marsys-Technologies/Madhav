"""
Unit tests for the M-22 Stage 3 "A3" wiring fix in ga_dashas_writer.py.

Background: `_vimshottari_independent_verifier.py` (PR #1047) was built and
discrimination-tested standalone but was never actually called from
`ga_dashas_writer.build_system()`'s write path — that path broadcast ONE
`_verify_vimshottari()` string onto every L1 row and defaulted every L2-4
row to `UNVERIFIED_DEFAULT`, regardless of whether anything about any
individual row was ever checked. This file proves the fix:
`_apply_vimshottari_independent_verification()` calls the REAL
`_vimshottari_independent_verifier.compare_row` /
`compute_independent_vimshottari_tree` functions (imported, not
reimplemented) to give every L1-4, non-KP row its OWN earned verdict.

Probes (a)-(c) mirror the shape of the 3 core discrimination probes in
`ga_writers/__tests__/test_vimshottari_independent_verifier.py` (wrong lord,
boundary beyond tolerance, boundary within tolerance) but exercise them
through the WRITER's own new per-row function, with REAL rows produced by
`compute_vimshottari()` (the writer's real engine) — a single row is
corrupted, every other row is left exactly as the real engine computed it,
and only the corrupted row is asserted to flip.
"""
from __future__ import annotations

import inspect
import json
from datetime import datetime, timedelta

import swisseph as swe

from ga_writers import ga_dashas_writer as sut
from ga_writers._vimshottari_independent_verifier import (
    TOLERANCE_SECONDS_DEFAULT,
    compare_row as _real_compare_row,
    compute_independent_vimshottari_tree as _real_compute_independent_tree,
)

# Same FORENSIC mock inputs test_ga7_writer.py uses — Moon in Purva
# Bhadrapada (nak 25, lord Jupiter), 1984-02-05 10:43 IST birth.
_MOON_SID_DEG = 325.5
_BIRTH_JD = swe.julday(1984, 2, 5, 5.21667)
_AYANAMSHA = "lahiri"
_BUILD_ID = "test-build-a3-wiring-00000-0000-0000-000000000000"


def _real_engine_rows() -> list[dict]:
    """The writer's REAL `compute_vimshottari()` output — L1-4, no KP rows."""
    return sut.compute_vimshottari(_MOON_SID_DEG, _BIRTH_JD, _AYANAMSHA, sut.CANONICAL_CHART_ID, _BUILD_ID)


# ─────────────────────────────────────────────────────────────────────────
# Baseline: an unmodified real chart must verify cleanly end-to-end — the
# precondition every corruption probe below relies on (if the clean
# baseline weren't all two_pass_verified, a probe's "divergent" result
# wouldn't prove the MUTATION caused it).
# ─────────────────────────────────────────────────────────────────────────

def test_baseline_clean_chart_all_rows_two_pass_verified():
    rows = _real_engine_rows()
    stamped = sut._apply_vimshottari_independent_verification(rows, _MOON_SID_DEG, _BIRTH_JD)
    l1_4 = [r for r in rows if r["level_n"] in (1, 2, 3, 4) and r.get("kp_sublevel") is None]
    assert l1_4, "no L1-4 rows produced by compute_vimshottari"
    assert stamped == len(l1_4)
    statuses = {r["verification_pass_status"] for r in l1_4}
    assert statuses == {"two_pass_verified"}, (
        f"clean, uncorrupted engine output did not verify cleanly: {statuses} "
        f"— either the engine and the independent verifier have genuinely "
        f"drifted, or the wiring pairs rows incorrectly"
    )


# ─────────────────────────────────────────────────────────────────────────
# Probe (a): a deliberately wrong lord on ONE real row must be flagged
# divergent — and ONLY that row, proving this is genuine per-row
# discrimination, not a chart-wide broadcast in either direction.
# ─────────────────────────────────────────────────────────────────────────

def test_probe_a_writer_wrong_lord_on_one_row_flagged_divergent_others_unaffected():
    rows = _real_engine_rows()
    l1 = [r for r in rows if r["level_n"] == 1]
    assert len(l1) >= 3, "need at least 3 L1 rows for a meaningful per-row probe"
    target = l1[1]
    correct_lord = target["lord_graha"]
    idx = sut.VIMSHOTTARI_SEQUENCE.index(correct_lord)
    wrong_lord = sut.VIMSHOTTARI_SEQUENCE[(idx + 1) % 9]  # adjacent in the cycle
    assert wrong_lord != correct_lord
    target["lord_graha"] = wrong_lord

    sut._apply_vimshottari_independent_verification(rows, _MOON_SID_DEG, _BIRTH_JD)

    assert target["verification_pass_status"] == "divergent_flagged", (
        f"wrong-lord probe FAILED TO DISCRIMINATE at the writer's own "
        f"wiring: got {target['verification_pass_status']!r}"
    )
    # A sibling L1 row left untouched must still verify cleanly — proves
    # this is per-row, not a chart-wide broadcast that would either flag
    # everything or nothing (the exact defect A3 fixes).
    untouched = next(r for r in l1 if r is not target)
    assert untouched["verification_pass_status"] == "two_pass_verified", (
        "an untouched sibling row was affected by a single corrupted row's "
        "verdict — this is the broadcast bug A3 was meant to fix"
    )


# ─────────────────────────────────────────────────────────────────────────
# Probe (b): a boundary shifted BEYOND tolerance on one real row must be
# flagged divergent.
# ─────────────────────────────────────────────────────────────────────────

def test_probe_b_writer_boundary_beyond_tolerance_flagged_divergent():
    rows = _real_engine_rows()
    l2 = [r for r in rows if r["level_n"] == 2]
    assert len(l2) >= 2
    target = l2[1]
    tol = TOLERANCE_SECONDS_DEFAULT
    orig_end = datetime.fromisoformat(target["end_iso"])
    target["end_iso"] = (orig_end + timedelta(seconds=tol * 3)).isoformat()

    sut._apply_vimshottari_independent_verification(rows, _MOON_SID_DEG, _BIRTH_JD)

    assert target["verification_pass_status"] == "divergent_flagged", (
        f"beyond-tolerance probe FAILED TO DISCRIMINATE at the writer's own "
        f"wiring: got {target['verification_pass_status']!r} for a "
        f"{tol * 3}s shift against a {tol}s tolerance"
    )


# ─────────────────────────────────────────────────────────────────────────
# Probe (c): a boundary shifted WITHIN tolerance must NOT be flagged — the
# "don't cry wolf on legitimate rounding noise" half of the proof.
# ─────────────────────────────────────────────────────────────────────────

def test_probe_c_writer_boundary_within_tolerance_not_flagged():
    rows = _real_engine_rows()
    l3 = [r for r in rows if r["level_n"] == 3]
    assert len(l3) >= 2
    target = l3[1]
    tol = TOLERANCE_SECONDS_DEFAULT
    orig_end = datetime.fromisoformat(target["end_iso"])
    target["end_iso"] = (orig_end + timedelta(seconds=tol * 0.5)).isoformat()

    sut._apply_vimshottari_independent_verification(rows, _MOON_SID_DEG, _BIRTH_JD)

    assert target["verification_pass_status"] == "two_pass_verified", (
        f"within-tolerance probe FALSE POSITIVE at the writer's own wiring: "
        f"got {target['verification_pass_status']!r} for a {tol * 0.5}s "
        f"shift against a {tol}s tolerance (this would fire on legitimate "
        f"float/rounding noise across every real build)"
    )


# ─────────────────────────────────────────────────────────────────────────
# Scope: KP sub-periods (a different derivation — V-12) must be left
# completely untouched by the independent verifier — never silently marked
# verified just because they happen to be present in the same `rows` list.
# ─────────────────────────────────────────────────────────────────────────

def test_kp_subperiod_rows_are_never_stamped_by_the_independent_verifier():
    rows = _real_engine_rows()
    kp_rows = sut.compute_kp_subperiods(rows, sut.CANONICAL_CHART_ID, _BUILD_ID, _AYANAMSHA)
    assert kp_rows, "no KP sub-period rows produced — test fixture assumption broken"
    sentinel = "TEST_SENTINEL_UNSTAMPED"
    for r in kp_rows:
        r["verification_pass_status"] = sentinel
    all_rows = rows + kp_rows

    sut._apply_vimshottari_independent_verification(all_rows, _MOON_SID_DEG, _BIRTH_JD)

    for r in kp_rows:
        assert r["verification_pass_status"] == sentinel, (
            "a KP sub-period row (kp_sublevel is not None) was stamped by "
            "the independent verifier — out of its documented scope (V-12); "
            "the caller's broadcast-fallback loop, not this function, is "
            "responsible for KP rows"
        )


# ─────────────────────────────────────────────────────────────────────────
# Proof this is the REAL code path build_system() actually runs at write
# time, not a standalone function nobody calls (the exact defect this A3
# fix closes — see PR #1047 / M22_NIGHT_LEDGER.md).
# ─────────────────────────────────────────────────────────────────────────

def test_build_system_source_calls_the_new_per_row_verification():
    src = inspect.getsource(sut.build_system)
    assert "_apply_vimshottari_independent_verification(rows, moon_sid, birth_jd)" in src, (
        "build_system() no longer calls _apply_vimshottari_independent_verification "
        "— the A3 wiring fix would be dead code again, exactly like "
        "_vimshottari_independent_verifier.py was before this fix"
    )
    # And the broadcast-fallback loop must explicitly skip the rows this
    # function already stamped, for vimshottari specifically — otherwise
    # the broadcast would silently clobber the per-row verdicts right back
    # down to one function-level string.
    assert 'system_id == "vimshottari" and row["level_n"] in (1, 2, 3, 4)' in src, (
        "build_system()'s broadcast-fallback loop no longer skips already-"
        "stamped vimshottari L1-4 rows — the per-row verdicts computed above "
        "would be immediately overwritten"
    )


def test_apply_vimshottari_independent_verification_calls_the_real_verifier_functions():
    """Confirms `_apply_vimshottari_independent_verification` is not a
    reimplementation — it calls the exact same `compare_row` /
    `compute_independent_vimshottari_tree` functions
    `ga_writers/__tests__/test_vimshottari_independent_verifier.py`'s
    discrimination probes exercise against the standalone module."""
    src = inspect.getsource(sut._apply_vimshottari_independent_verification)
    assert "_iv_compute_independent_tree(" in src
    assert "_iv_compare_row(" in src
    # And those module-level names must resolve to the real verifier
    # module's functions, not a local shadow/reimplementation.
    assert sut._iv_compare_row is _real_compare_row
    assert sut._iv_compute_independent_tree is _real_compute_independent_tree


# ─────────────────────────────────────────────────────────────────────────
# Determinism: two builds of the same chart/ayanamsha/inputs must produce
# byte-identical Vimshottari rows (modulo genuinely non-deterministic
# per-row identity fields: dasha_row_id/parent_row_id are random uuid4,
# computed_at is a wall-clock timestamp — the same fields
# `_vimshottari_independent_verifier.NOT_INDEPENDENTLY_CHECKABLE_COLUMNS`
# documents as carrying no derivable astronomical content). Pattern follows
# `tests/l5/test_kala_timeline_spec.py::test_output_is_deterministic_and_totally_ordered`
# (build twice, `json.dumps(..., sort_keys=True)` byte comparison).
# ─────────────────────────────────────────────────────────────────────────

_NONDETERMINISTIC_FIELDS = ("dasha_row_id", "parent_row_id", "computed_at")


def _strip_nondeterministic(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in r.items() if k not in _NONDETERMINISTIC_FIELDS} for r in rows]


def test_compute_vimshottari_is_deterministic_across_two_builds():
    rows_a = sut.compute_vimshottari(_MOON_SID_DEG, _BIRTH_JD, _AYANAMSHA, sut.CANONICAL_CHART_ID, _BUILD_ID)
    rows_b = sut.compute_vimshottari(_MOON_SID_DEG, _BIRTH_JD, _AYANAMSHA, sut.CANONICAL_CHART_ID, _BUILD_ID)

    a_stripped = _strip_nondeterministic(rows_a)
    b_stripped = _strip_nondeterministic(rows_b)

    assert json.dumps(a_stripped, sort_keys=True, default=str) == json.dumps(b_stripped, sort_keys=True, default=str), (
        "compute_vimshottari() produced different output across two calls "
        "with identical inputs — the writer's core computation is not "
        "deterministic (excluding row-identity uuid4/wall-clock fields)"
    )


def test_apply_vimshottari_independent_verification_is_deterministic_across_two_builds():
    """The per-row verdicts themselves (the A3 fix's actual output) must
    also be deterministic — a chart rebuilt twice must earn the same
    verification_pass_status per row both times."""
    rows_a = sut.compute_vimshottari(_MOON_SID_DEG, _BIRTH_JD, _AYANAMSHA, sut.CANONICAL_CHART_ID, _BUILD_ID)
    rows_b = sut.compute_vimshottari(_MOON_SID_DEG, _BIRTH_JD, _AYANAMSHA, sut.CANONICAL_CHART_ID, _BUILD_ID)
    sut._apply_vimshottari_independent_verification(rows_a, _MOON_SID_DEG, _BIRTH_JD)
    sut._apply_vimshottari_independent_verification(rows_b, _MOON_SID_DEG, _BIRTH_JD)

    statuses_a = [(r["level_n"], r["lord_graha"], r["start_iso"], r["verification_pass_status"]) for r in rows_a]
    statuses_b = [(r["level_n"], r["lord_graha"], r["start_iso"], r["verification_pass_status"]) for r in rows_b]
    assert statuses_a == statuses_b


# ─────────────────────────────────────────────────────────────────────────
# Required test 3: byte-identical emissions except verification_pass_status.
#
# Proves the A3 refactor is SURGICAL. `build_system()`'s vimshottari branch
# (see this PR's diff to ga_dashas_writer.py) assembles rows via
# compute_vimshottari() + compute_kp_subperiods() — completely UNCHANGED by
# A3 — then, before this fix, ran ONE final loop that broadcast a single
# `_verify_vimshottari()` string onto every L1 row and UNVERIFIED_DEFAULT
# onto everything else; after this fix it runs
# `_apply_vimshottari_independent_verification()` (real per-row verdicts)
# first, then a final loop that only fills in the rows that function did NOT
# already stamp (KP sub-periods, anything outside level_n 1-4).
#
# The two tiny helper functions below are VERBATIM transcriptions of those
# two final loops (before/after) straight from this PR's diff — there is no
# comparison/verdict LOGIC in either one to reimplement (each is a bare
# level_n/kp_sublevel branch); the actual verdict-earning work
# (compute_vimshottari, compute_kp_subperiods, _verify_vimshottari,
# _apply_vimshottari_independent_verification) is invoked via the REAL
# functions in both branches, from the SAME base row set (deep-copied before
# either branch mutates it). This isolates exactly the code A3 changed and
# proves nothing else moved.
# ─────────────────────────────────────────────────────────────────────────

import copy


def _build_all_rows_unstamped() -> tuple[list[dict], str]:
    """Mirrors build_system()'s vimshottari row-assembly + `verification`
    string computation exactly, via the real functions — no
    verification_pass_status stamping yet."""
    rows = sut.compute_vimshottari(_MOON_SID_DEG, _BIRTH_JD, _AYANAMSHA, sut.CANONICAL_CHART_ID, _BUILD_ID)
    kp_rows = sut.compute_kp_subperiods(rows, sut.CANONICAL_CHART_ID, _BUILD_ID, _AYANAMSHA)
    rows.extend(kp_rows)
    verification = sut._verify_vimshottari(
        [r for r in rows if r["level_n"] <= 4 and r.get("kp_sublevel") is None],
        _MOON_SID_DEG, sut.CANONICAL_CHART_ID,
    )
    return rows, verification


def _apply_old_pre_a3_broadcast_verdict(rows: list[dict], verification: str) -> None:
    """Verbatim transcription of the PRE-A3 final loop this PR removed from
    build_system() — reproduced here because that code no longer exists in
    the tree after this fix, and this is the "before" half of the surgical-
    diff proof (see this file's block comment above)."""
    for row in rows:
        examined = row["level_n"] == 1 and row.get("kp_sublevel") is None
        row["verification_pass_status"] = verification if examined else sut.UNVERIFIED_DEFAULT


def _apply_new_post_a3_verdict(rows: list[dict], verification: str) -> None:
    """Mirrors build_system()'s POST-A3 final assignment: the REAL
    `_apply_vimshottari_independent_verification` earns every L1-4 non-KP
    row its own verdict, then the same skip-already-stamped fallback loop
    build_system() runs afterward for everything that function didn't
    touch."""
    sut._apply_vimshottari_independent_verification(rows, _MOON_SID_DEG, _BIRTH_JD)
    for row in rows:
        if row["level_n"] in (1, 2, 3, 4) and row.get("kp_sublevel") is None:
            continue
        examined = row["level_n"] == 1 and row.get("kp_sublevel") is None
        row["verification_pass_status"] = verification if examined else sut.UNVERIFIED_DEFAULT


def test_old_broadcast_vs_new_per_row_emissions_byte_identical_except_tier():
    base_rows, verification = _build_all_rows_unstamped()
    assert base_rows, "no rows produced by compute_vimshottari + compute_kp_subperiods"

    rows_old = copy.deepcopy(base_rows)
    rows_new = copy.deepcopy(base_rows)

    _apply_old_pre_a3_broadcast_verdict(rows_old, verification)
    _apply_new_post_a3_verdict(rows_new, verification)

    assert len(rows_old) == len(rows_new)

    exclude = set(_NONDETERMINISTIC_FIELDS) | {"verification_pass_status"}
    old_stripped = [{k: v for k, v in r.items() if k not in exclude} for r in rows_old]
    new_stripped = [{k: v for k, v in r.items() if k not in exclude} for r in rows_new]

    assert json.dumps(old_stripped, sort_keys=True, default=str) == json.dumps(new_stripped, sort_keys=True, default=str), (
        "the A3 refactor changed a field OTHER than verification_pass_status "
        "— this was supposed to be a surgical change to how the tier is "
        "earned, not to what dates/lords/any other computed value comes out"
    )

    # Sanity: prove the tier actually DID earn something different for L2-4
    # rows — otherwise "byte-identical except tier" would be vacuously true
    # because nothing ever differed to begin with (e.g. if the new function
    # silently no-op'd).
    old_l2_4 = {r["verification_pass_status"] for r in rows_old
                if r["level_n"] in (2, 3, 4) and r.get("kp_sublevel") is None}
    new_l2_4 = {r["verification_pass_status"] for r in rows_new
                if r["level_n"] in (2, 3, 4) and r.get("kp_sublevel") is None}
    assert old_l2_4 == {sut.UNVERIFIED_DEFAULT}, (
        "sanity check failed: OLD code is expected to broadcast "
        "UNVERIFIED_DEFAULT onto every L2-4 row"
    )
    assert new_l2_4 != {sut.UNVERIFIED_DEFAULT}, (
        "NEW code produced the same UNVERIFIED_DEFAULT for L2-4 rows as the "
        "OLD broadcast fallback — the per-row wiring earned nothing "
        "different here, so this test's 'byte-identical except tier' proof "
        "would be vacuous"
    )
    # And KP rows must be identically UNVERIFIED_DEFAULT in both — A3's
    # scope is explicitly L1-4 non-KP rows only (see the KP-scope test
    # above); nothing about KP row tiers should have moved.
    old_kp = {r["verification_pass_status"] for r in rows_old if r.get("kp_sublevel") is not None}
    new_kp = {r["verification_pass_status"] for r in rows_new if r.get("kp_sublevel") is not None}
    assert old_kp == new_kp == {sut.UNVERIFIED_DEFAULT}
