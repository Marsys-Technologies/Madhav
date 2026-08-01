"""
services/ka_moorti_nirnaya/logic.py — pure, DB-free computation for item 4
(Moorti-nirṇaya, "the classical gold/silver/copper/iron 'statue' of a
transit"). SHAD_DARSHANA_BRIEF_v2_0.md §1 item 4: "Moorti-nirṇaya per ingress
per chart." Wave W3. Registered as writer id `ka_moorti_nirnaya` (layer kala).

── WHAT MOORTI-NIRṆAYA IS ────────────────────────────────────────────────────
A classical transit-quality refinement (Phaladeepika Ch.26 §moorti-nirnaya;
BPHS Ch.28): when a transiting graha ingresses a new sign, the quality of
that WHOLE STAY (not just the instant) is graded gold/silver/copper/iron
(svarna/rajata/tamra/loha) by counting the nakshatra the MOON occupies AT THE
MOMENT OF INGRESS, offset from the native's own janma nakshatra (natal
Moon's nakshatra). This is a genuinely differentiating classical technique —
KALA_SIX_VIEWS_DESIGN_v1_0.md §1.2 names it explicitly: "reference rules
exist (`bg_transit_moorti`); the per-chart, per-ingress computation does
not. BUILD." `bg_transit_moorti` (migration 401) already carries the full
27-row nakshatra-offset -> quality-tier table, REAL and cited (Phaladeepika
Ch.26; BPHS Ch.28) — this module does not re-derive that table (§N.5: L0 is
the authority), it only computes the two inputs the table needs: which
ingress, and the Moon's nakshatra at that ingress.

── SCOPE (disclosed, not an oversight) ───────────────────────────────────────
Computed for the 8 grahas OTHER than the Moon itself (Sun, Mars, Mercury,
Jupiter, Venus, Saturn, Rahu, Ketu) — matches classical Gochara practice,
where transiting grahas are read against the natal Moon as the reference
point; "the Moon's position at the Moon's own ingress" is not a construction
this or any codebase-attested classical source treats as a distinct
technique, so evaluating the Moon against itself is out of scope here (a
disclosed choice, not an oversight). `MOORTI_GRAHAS` below is the exact
scope.

── RUN DETECTION (shared idiom with ka_kota_chakra) ──────────────────────────
`detect_sign_runs`/`run_containing_date` are the same generic
contiguous-daily-run detection `ka_kota_chakra.logic.detect_ring_runs` uses
for nakshatra-index runs, applied here to SIGN index instead — day-grade
precision throughout (SHAD_DARSHANA_BRIEF_v2_0.md §4: "No wave may be
designed to REQUIRE sub-day precision"). A run's `start_truncated` flag means
the run's start touches the scanned horizon's edge, so its TRUE ingress
instant is unverified — see `moorti_computed` discipline below for why this
specifically invalidates the moorti classification for that one run (a
stricter consequence than ka_kota_chakra's own truncation flag carries,
because moorti's classification is anchored to the exact ingress day, not
merely "which nakshatra-count currently holds").

── HONESTY DISCIPLINE: `moorti_computed` (B.10 / §N.7) ───────────────────────
A run whose `start_truncated` is True was NOT observed to begin within the
scanned horizon — we only know the graha was ALREADY in that sign on the
horizon's first scanned day, not that today's Moon-nakshatra-at-horizon-start
is the Moon's nakshatra AT THE TRUE INGRESS MOMENT (which may have been
months or years earlier). Presenting a moorti classification for that run
would silently pass off "Moon's nakshatra on the day we happened to start
scanning" as "Moon's nakshatra at ingress" — exactly the kind of invented
precision B.10 forbids. `moorti_computed=False` on these rows, with the
moorti fields left `None`, is the honest alternative to a plausible-looking
but unverified value (§N.7 item 6).
"""
from __future__ import annotations

from datetime import date
from typing import Optional, TypedDict

# The 8 grahas moorti-nirnaya is scoped to (see module docstring). Order
# matches services.ka_graha_sancara.engine.ALL_GRAHAS minus "Moon".
MOORTI_GRAHAS: tuple[str, ...] = (
    "Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


class SignRun(TypedDict):
    sign_idx: int
    start_date: date
    end_date: date
    start_truncated: bool
    end_truncated: bool


def detect_sign_runs(
    daily_sign_idx: list[tuple[date, int]],
    *,
    horizon_start: date,
    horizon_end: date,
) -> list[SignRun]:
    """Groups a sorted, contiguous daily (date, sign_idx) series into maximal
    same-sign runs — one run per (graha) sign-occupancy window. Identical
    algorithm to `ka_kota_chakra.logic.detect_ring_runs`, applied to sign
    index rather than nakshatra index; see that module for the full
    truncation-honesty rationale, which applies unchanged here.

    `daily_sign_idx` must be sorted ascending by date with no gaps (the
    caller is responsible for supplying a complete daily series over
    [horizon_start, horizon_end]).
    """
    if not daily_sign_idx:
        return []

    runs: list[SignRun] = []
    run_start_date, run_sign_idx = daily_sign_idx[0]
    prev_date = run_start_date

    def _flush(end_date: date) -> None:
        runs.append({
            "sign_idx": run_sign_idx,
            "start_date": run_start_date,
            "end_date": end_date,
            "start_truncated": run_start_date == horizon_start,
            "end_truncated": end_date == horizon_end,
        })

    for d, sign_idx in daily_sign_idx[1:]:
        if sign_idx != run_sign_idx:
            _flush(prev_date)
            run_start_date, run_sign_idx = d, sign_idx
        prev_date = d

    _flush(prev_date)
    return runs


def run_containing_date(runs: list[SignRun], as_of: date) -> Optional[SignRun]:
    for r in runs:
        if r["start_date"] <= as_of <= r["end_date"]:
            return r
    return None


def nakshatra_offset_from_janma(moon_nak_idx_at_ingress: int, janma_nak_idx: int) -> int:
    """The `bg_transit_moorti.nakshatra_offset` key (1..27): the Moon's
    nakshatra AT THE INGRESS MOMENT, counted forward from the natal janma
    nakshatra (offset 1 = the Moon is transiting the janma nakshatra itself
    at that instant). Matches migration 401's own convention exactly
    ("count the transit nakshatra from natal janma nakshatra, offset 1..27")
    and `ka_kota_chakra.logic.count_from_janma`'s identical 1-indexed,
    27-wraparound arithmetic."""
    return ((moon_nak_idx_at_ingress - janma_nak_idx) % 27) + 1


__all__ = [
    "MOORTI_GRAHAS",
    "SignRun",
    "detect_sign_runs",
    "run_containing_date",
    "nakshatra_offset_from_janma",
]
