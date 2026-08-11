"""
W2G V6 — divergence classifier + divergence-rate pilot on one materialized
year.

Design §6 V6: "divergence-rate pilot on 1 materialized year (2.0 prototype
math on paper/spike vs v1 rows — sizes §3.2's workload)."
Design §3.2 is the contract this module implements in code:

  > where 2.0 differs, each divergence is classified with evidence:
  > (a) v1 grid artifact (chunk-edge bounds, midnight snapping) — 2.0 correct;
  > (b) v1 Moon-undersampling miss — 2.0 found a real sub-day window v1
  >     couldn't see (expected headline finding);
  > (c) genuine 2.0 bug — fix. NO divergence ships unclassified.

Two deliverables, deliberately separated:

  1. `classify_divergence` / `run_divergence_report` — the REAL classifier
     the E-6 lane will run, pure and unit-tested, with UNCLASSIFIED as an
     explicit, countable outcome rather than a silent default. Gate W2G's
     "zero unclassified rows" is a property of this report, so the report has
     to be able to say a row is unclassified out loud.

  2. The live PILOT — what is measurable today, with no 2.0 engine in
     existence: a census of v1 rows in one materialized year whose window
     edges coincide with the v1 writer's own CHUNK boundaries. Those are the
     class-(a) candidates (design §1.3's RED-C defect class), and their count
     sizes §3.2's workload from the v1 side alone.

WHY V6 CANNOT REPORT A DIVERGENCE RATE TODAY, AND SAYS SO. A rate needs both
sides. The 2.0 engine does not exist yet, so this validation returns
INDETERMINATE for the rate and hands over the sized workload and the working
classifier as data. Reporting the class-(a) candidate count as if it were a
divergence rate would be exactly the proxy-for-the-claim substitution
CLAUDE.md §N.8 forbids.

CHUNK BOUNDARY BASIS, read from the v1 writer rather than assumed:
`ka_gochara_sweep.writer.run_substep` maps `year_idx` to the calendar year
`[birth_year+year_idx-01-01, birth_year+year_idx+1-01-01)`. So a v1 chunk
edge is a JANUARY 1 / DECEMBER 31 calendar boundary. A window edge landing
exactly there is chunk-boundary-COINCIDENT — evidence of a class-(a)
candidate, never on its own a proof (a real window may genuinely start on
January 1). The census counts candidates and names them that.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from ._db import QueryFn, table_exists
from .types import INDETERMINATE, ValidationResult

WINDOWS_TABLE = "kala_gochara_windows"

# v1's own registered fidelity bound (design §1.2: "v1 windows are honest
# only at >=1-day resolution"). Two bounds agreeing within this are agreeing.
V1_RESOLUTION_DAYS = 1

CLASS_AGREEMENT = "agreement"
CLASS_A_V1_GRID_ARTIFACT = "a_v1_grid_artifact"
CLASS_B_V1_MOON_UNDERSAMPLING = "b_v1_moon_undersampling_miss"
CLASS_C_CANDIDATE_2_0_BUG = "c_candidate_2_0_bug"
UNCLASSIFIED = "unclassified"

DIVERGENCE_CLASSES = (
    CLASS_AGREEMENT,
    CLASS_A_V1_GRID_ARTIFACT,
    CLASS_B_V1_MOON_UNDERSAMPLING,
    CLASS_C_CANDIDATE_2_0_BUG,
    UNCLASSIFIED,
)


def _d(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def is_chunk_boundary(d: date | None) -> bool:
    """True when `d` sits on a v1 substep chunk edge (calendar-year boundary)."""
    if d is None:
        return False
    return (d.month, d.day) in ((1, 1), (12, 31))


def classify_divergence(
    v1_row: dict | None,
    candidate_row: dict | None,
    resolution_days: int = V1_RESOLUTION_DAYS,
) -> dict[str, Any]:
    """Classify one v1-vs-2.0 pairing per design §3.2.

    `v1_row` / `candidate_row` carry `window_start`, `window_end`, and
    optionally `event_class`, `peak_date`, `sub_day` (bool — the 2.0 row
    resolves below one day), `transiting_bodies` (iterable).

    Returns `{"class": ..., "evidence": [...], "delta_days": {...}}`. The
    class is ALWAYS one of `DIVERGENCE_CLASSES`; `UNCLASSIFIED` is a real,
    countable outcome — never a silent default that a caller might read as
    benign.
    """
    if v1_row is None and candidate_row is None:
        raise ValueError("classify_divergence needs at least one row")

    evidence: list[str] = []

    # --- 2.0 found something v1 has no row for ---------------------------
    if v1_row is None:
        assert candidate_row is not None
        sub_day = bool(candidate_row.get("sub_day"))
        bodies = {str(b) for b in (candidate_row.get("transiting_bodies") or [])}
        if sub_day:
            evidence.append("2.0-only row resolves below one day")
            if "Moon" in bodies:
                evidence.append("Moon is among the transiting bodies")
                return {
                    "class": CLASS_B_V1_MOON_UNDERSAMPLING,
                    "evidence": evidence,
                    "delta_days": {},
                }
            evidence.append(
                "no Moon among the transiting bodies — a sub-day window from slow "
                "bodies alone is not the design §3.2(b) mechanism"
            )
            return {"class": UNCLASSIFIED, "evidence": evidence, "delta_days": {}}
        evidence.append(
            "2.0-only row is NOT sub-day, so v1's daily grid should have seen it"
        )
        return {"class": CLASS_C_CANDIDATE_2_0_BUG, "evidence": evidence, "delta_days": {}}

    v1_start, v1_end = _d(v1_row.get("window_start")), _d(v1_row.get("window_end"))

    # --- v1 has a row 2.0 produced nothing for ---------------------------
    if candidate_row is None:
        edges_on_boundary = [
            name
            for name, value in (("window_start", v1_start), ("window_end", v1_end))
            if is_chunk_boundary(value)
        ]
        if edges_on_boundary:
            evidence.append(
                f"v1 row is absent from 2.0 and its {', '.join(edges_on_boundary)} "
                "sits on a substep chunk boundary (calendar-year edge)"
            )
            return {
                "class": CLASS_A_V1_GRID_ARTIFACT,
                "evidence": evidence,
                "delta_days": {},
            }
        evidence.append(
            "v1 row is absent from 2.0 and no edge sits on a chunk boundary — "
            "needs disposition, not a default"
        )
        return {"class": UNCLASSIFIED, "evidence": evidence, "delta_days": {}}

    # --- both sides present: compare bounds -------------------------------
    c_start, c_end = _d(candidate_row.get("window_start")), _d(candidate_row.get("window_end"))
    d_start = abs((c_start - v1_start).days) if (c_start and v1_start) else None
    d_end = abs((c_end - v1_end).days) if (c_end and v1_end) else None
    deltas = {"start_days": d_start, "end_days": d_end}

    within = [x for x in (d_start, d_end) if x is not None]
    if within and max(within) <= resolution_days:
        evidence.append(
            f"both bounds agree within v1's own {resolution_days}-day registered "
            "fidelity bound (design §3.1)"
        )
        return {"class": CLASS_AGREEMENT, "evidence": evidence, "delta_days": deltas}

    disagreeing_edges = []
    if d_start is not None and d_start > resolution_days:
        disagreeing_edges.append(("window_start", v1_start, d_start))
    if d_end is not None and d_end > resolution_days:
        disagreeing_edges.append(("window_end", v1_end, d_end))

    on_boundary = [name for name, value, _ in disagreeing_edges if is_chunk_boundary(value)]
    if on_boundary and len(on_boundary) == len(disagreeing_edges):
        evidence.append(
            f"every disagreeing v1 edge ({', '.join(on_boundary)}) sits on a substep "
            "chunk boundary — the RED-C chunk-artifact signature (design §1.3)"
        )
        return {"class": CLASS_A_V1_GRID_ARTIFACT, "evidence": evidence, "delta_days": deltas}

    if bool(candidate_row.get("sub_day")) and "Moon" in {
        str(b) for b in (candidate_row.get("transiting_bodies") or [])
    }:
        evidence.append(
            "2.0's bound is sub-day and Moon-driven, which v1's daily grid cannot resolve"
        )
        return {
            "class": CLASS_B_V1_MOON_UNDERSAMPLING,
            "evidence": evidence,
            "delta_days": deltas,
        }

    evidence.append(
        "bounds disagree beyond v1's resolution with no chunk-boundary and no "
        "sub-day Moon signature — needs disposition"
    )
    return {"class": UNCLASSIFIED, "evidence": evidence, "delta_days": deltas}


def run_divergence_report(
    v1_rows: Iterable[dict],
    candidate_rows: Iterable[dict],
    key_fields: tuple[str, ...] = ("event_class", "peak_date"),
) -> dict[str, Any]:
    """Pair v1 rows with 2.0 candidate rows on `key_fields` and classify every
    pairing. The report is complete by construction: every row on either side
    appears in exactly one classified pairing.
    """

    def _key_part(value: Any) -> str:
        """Normalise one key field. Dates are compared as ISO dates so a
        `date` and its string spelling pair up; anything else compares as
        its own string."""
        if isinstance(value, date):
            return value.isoformat()
        try:
            return date.fromisoformat(str(value)[:10]).isoformat()
        except ValueError:
            return str(value)

    def _key(row: dict) -> tuple:
        return tuple(_key_part(row.get(f)) for f in key_fields)

    v1_by_key: dict[tuple, list[dict]] = {}
    for row in v1_rows:
        v1_by_key.setdefault(_key(row), []).append(row)
    cand_by_key: dict[tuple, list[dict]] = {}
    for row in candidate_rows:
        cand_by_key.setdefault(_key(row), []).append(row)

    classified: list[dict[str, Any]] = []
    for key in sorted(set(v1_by_key) | set(cand_by_key)):
        left = list(v1_by_key.get(key, []))
        right = list(cand_by_key.get(key, []))
        for i in range(max(len(left), len(right))):
            v1_row = left[i] if i < len(left) else None
            c_row = right[i] if i < len(right) else None
            result = classify_divergence(v1_row, c_row)
            result["key"] = list(key)
            classified.append(result)

    counts = {cls: 0 for cls in DIVERGENCE_CLASSES}
    for c in classified:
        counts[c["class"]] += 1

    total = len(classified)
    divergences = total - counts[CLASS_AGREEMENT]
    return {
        "total_pairings": total,
        "counts": counts,
        "divergences": divergences,
        "unclassified": counts[UNCLASSIFIED],
        "divergence_rate": round(divergences / total, 6) if total else None,
        # Gate W2G's own condition, computed rather than asserted.
        "zero_unclassified": counts[UNCLASSIFIED] == 0,
        "rows": classified,
    }


def _pilot_census(query: QueryFn, chart_id: str, year: int) -> dict[str, Any]:
    """v1-side class-(a) candidate census for one materialized year."""
    # INTENTIONAL: generation='v1' pin — this pilot measures chunk-boundary
    # candidates in v1's own rows (the rows produced by ka_gochara_sweep whose
    # chunk structure this census analyses). Including gen-3.0 rows would mix
    # corpora: 3.0 rows use a different materialization strategy and do not share
    # v1's Jan-1/Dec-31 substep-chunk boundaries, so they would spuriously inflate
    # the candidate count and misrepresent the v1 workload. The pin is permanent:
    # this pilot exists specifically to characterise the v1 corpus. (MR-18)
    rows = query(
        f"SELECT event_class, temporal_shape, window_start, window_end, peak_date "
        f"FROM {WINDOWS_TABLE} WHERE chart_id::text = %s "
        f"AND generation = 'v1' "
        f"AND window_start >= %s AND window_start <= %s "
        f"ORDER BY window_start",
        [chart_id, date(year, 1, 1), date(year, 12, 31)],
    )
    boundary_rows = []
    for r in rows:
        edges = [
            name
            for name, value in (
                ("window_start", _d(r["window_start"])),
                ("window_end", _d(r["window_end"])),
            )
            if is_chunk_boundary(value)
        ]
        if edges:
            boundary_rows.append(
                {
                    "event_class": r["event_class"],
                    "temporal_shape": r["temporal_shape"],
                    "window_start": str(_d(r["window_start"])),
                    "window_end": str(_d(r["window_end"])),
                    "boundary_edges": edges,
                }
            )
    return {
        "year": year,
        "rows_in_year": len(rows),
        "chunk_boundary_coincident_rows": len(boundary_rows),
        "class_a_candidate_rate": round(len(boundary_rows) / len(rows), 6) if rows else None,
        "samples": boundary_rows[:15],
    }


def validate_v6_divergence_pilot(
    query: QueryFn,
    chart_ids: list[str],
    pilot_year: int,
) -> ValidationResult:
    title = (
        "V6 — divergence classifier (design §3.2) + one-materialized-year pilot "
        "sizing the equivalence workload"
    )

    if not table_exists(query, WINDOWS_TABLE):
        return ValidationResult(
            validation_id="V6",
            title=title,
            status=INDETERMINATE,
            summary=f"`{WINDOWS_TABLE}` is not present in this database.",
            reason=f"no v1 corpus to pilot against (`{WINDOWS_TABLE}` missing)",
        )

    census = {chart_id: _pilot_census(query, chart_id, pilot_year) for chart_id in chart_ids}

    # Self-check: the classifier is exercised here against the pilot's own
    # shape so this validation never ships a classifier it did not run.
    self_check = run_divergence_report(
        [
            {"event_class": "marriage", "peak_date": date(pilot_year, 6, 1),
             "window_start": date(pilot_year, 1, 1), "window_end": date(pilot_year, 12, 31)},
        ],
        [
            {"event_class": "marriage", "peak_date": date(pilot_year, 6, 1),
             "window_start": date(pilot_year, 5, 20), "window_end": date(pilot_year, 6, 14)},
        ],
    )

    total_rows = sum(c["rows_in_year"] for c in census.values())
    total_candidates = sum(c["chunk_boundary_coincident_rows"] for c in census.values())

    findings = [
        f"Pilot year {pilot_year}: {total_candidates} of {total_rows} v1 rows across "
        f"{len(chart_ids)} chart(s) have a window edge coincident with a v1 substep chunk "
        "boundary. These are class-(a) CANDIDATES — a real window may legitimately start "
        "on January 1, so coincidence sizes the workload, it does not adjudicate it.",
        "The divergence RATE itself is not computable yet: it needs the 2.0 side, which "
        "does not exist. The classifier that will compute it ships here, tested, so E-6 "
        "inherits a working instrument rather than a specification of one.",
    ]

    return ValidationResult(
        validation_id="V6",
        title=title,
        status=INDETERMINATE,
        summary=(
            f"Classifier delivered and self-checked; v1-side workload sized at "
            f"{total_candidates}/{total_rows} class-(a) candidate rows for {pilot_year}. "
            "Divergence rate awaits the 2.0 engine."
        ),
        reason=(
            "a divergence rate requires both sides of the comparison; the GOCHARA-2.0 "
            "engine has not been built, so no 2.0 row set exists to compare against v1"
        ),
        data={
            "pilot_year": pilot_year,
            "per_chart_census": census,
            "total_rows_in_pilot_year": total_rows,
            "total_class_a_candidates": total_candidates,
            "chunk_boundary_basis": "calendar-year edges (Jan 1 / Dec 31) per ka_gochara_sweep.writer.run_substep",
            "divergence_classes": list(DIVERGENCE_CLASSES),
            "classifier_self_check": {
                "counts": self_check["counts"],
                "zero_unclassified": self_check["zero_unclassified"],
            },
        },
        findings=findings,
    )


__all__ = [
    "validate_v6_divergence_pilot",
    "classify_divergence",
    "run_divergence_report",
    "is_chunk_boundary",
    "DIVERGENCE_CLASSES",
    "CLASS_AGREEMENT",
    "CLASS_A_V1_GRID_ARTIFACT",
    "CLASS_B_V1_MOON_UNDERSAMPLING",
    "CLASS_C_CANDIDATE_2_0_BUG",
    "UNCLASSIFIED",
]
