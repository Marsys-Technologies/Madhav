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

# ── WP9 overlay stamps (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1 §5.4; migration
# 1082) ──────────────────────────────────────────────────────────────────────
# A moorti-computed row restates bg_transit_moorti verbatim (migration 401).
# That table is cited (Phaladeepika Ch.26; BPHS Ch.28) but the mūrti
# (sūkṣma/sthūla Moon-in-sign disposition) RULE FORM is NOT present in the
# served corpus — so doctrine N7 forbids stamping it 'verse_cited' or
# corpus-verifiable merely because the computation succeeded. Computed rows
# stamp 'algorithmic_approximation' (the migration-1082 CHECK vocabulary for
# a computed value whose rule form is not corpus-verifiable — the same stamp
# ka_vedha_gochara's sarvatobhadra rows carry with uncited_extension=true),
# corpus_verifiable=False. A row whose moorti could NOT be computed
# (truncated run / ephemeris gap — moorti_computed=False) has no sourced
# value → 'unsourced', not corpus-verifiable. precision_regime is
# 'date_grain' for the day-grade ingress date and 'instant_grain' only when
# the grade was taken at a true kernel sign-ingress instant (WP9 5.3).
#
# NOTE on the N7 repair token: the doctrine vocabulary token for this defect
# class is 'uncited_extension', but migration 1082's CHECK constrains
# kala_moorti_nirnaya.source_qualification to the three values below and the
# moorti table has no uncited_extension column — stamping the literal token
# would violate the CHECK at every insert. 'algorithmic_approximation' is the
# constraint-compatible stamp carrying the same semantics.
SOURCE_QUALIFICATIONS: tuple[str, ...] = ("verse_cited", "algorithmic_approximation", "unsourced")
PRECISION_REGIMES: tuple[str, ...] = ("date_grain", "instant_grain")


def moorti_source_qualification(moorti_computed: bool) -> str:
    # N7: provenance reflects corpus presence of the mūrti rule form, NOT
    # computation success. The rule form is absent from the served corpus, so
    # a successfully computed moorti is an algorithmic approximation of an
    # uncited rule — never 'verse_cited'.
    return "algorithmic_approximation" if moorti_computed else "unsourced"


def moorti_corpus_verifiable(moorti_computed: bool) -> bool:
    # N7: False independent of computation success — the served corpus does
    # not contain the mūrti rule form, so no row is corpus-verifiable.
    return False


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
    "SOURCE_QUALIFICATIONS",
    "PRECISION_REGIMES",
    "moorti_source_qualification",
    "moorti_corpus_verifiable",
    "SignRun",
    "detect_sign_runs",
    "run_containing_date",
    "nakshatra_offset_from_janma",
    "moorti_upstream_fingerprint",
]


# ── §12.9 upstream fingerprint ───────────────────────────────────────────────
# A kala_moorti_nirnaya row restates a `bg_transit_moorti` row verbatim (name, tier, phala,
# citation). Nothing on the row said WHICH version of that table it was built from, so an
# upstream change left built rows silently stale (CLAUDE.md §N.8). This digests exactly the
# rows a build consumed — the same in-memory objects the writer holds — so comparing it to a
# fresh read answers "was this built from what the table says now?".
# Step 3 §4 closes the two gaps this comment used to declare deliberate: the consumed
# `ephemeris_daily` node series now rides the fingerprint as the `node_series` component
# (the L0-owned node_series_digest_v1 identity — services.w2g.node_series), and the consumed
# natal L1 operand (the chart's MOON longitude fact: fact_id, build_id, stored value text)
# rides it as the `l1` component — so an L1 rebuild or a series change now makes older rows
# stale instead of silently fresh.
from services.gochara_kernel.fingerprint import FINGERPRINT_ALGORITHM, canonical_digest


def moorti_upstream_fingerprint(moorti_table: dict, *,
                                node_series: Optional[dict] = None,
                                l1: Optional[dict] = None,
                                formula_version: Optional[str] = None) -> dict:
    """Digest of the `bg_transit_moorti` rows one build consumed.

    `moorti_table` is `{nakshatra_offset: row}` — what the writer's `_fetch_moorti_table`
    returns. Order-independent; sensitive to every consumed field. JSON-safe, so it
    round-trips through a jsonb column.

    Step 3 §4: `node_series`, `l1` and `formula_version` fold in the consumed series
    identity, the consumed natal operand identity and the writer version (same contract
    as ka_vedha_gochara's upstream_fingerprint; omitted components keep the pre-step-3
    shape, which the gate reads stale by construction). The bulk-ephemeris caveat above
    is now carried by the `node_series` component, not by silence.
    """
    rows = sorted(
        ([int(k), {f: v for f, v in sorted(dict(row).items())}] for k, row in moorti_table.items()),
        key=lambda x: x[0],
    )
    fp = {
        "algorithm": FINGERPRINT_ALGORITHM,
        "bg_transit_moorti": canonical_digest(rows),
        "n_moorti_rows": len(rows),
    }
    if node_series is not None:
        fp["node_series"] = node_series
    if l1 is not None:
        fp["l1"] = l1
    if formula_version is not None:
        fp["formula_version"] = formula_version
    return fp
