"""
W2G V2 — `ephemeris_daily` coverage/cadence, AS AMENDED BY ADJUDICATION-5.

Design §6 V2 originally read "coverage/cadence actually present for
1984–2084 × 9 bodies". ADJUDICATION-5 (N3 ruling, 2026-07-29) AMENDS it:

  > W2G bind-time validation V2 is amended: verify `ephemeris_daily`
  > coverage/cadence for **1900–2084** × 9 bodies (not 1984–2084). If any
  > body proves to have a later start than 1900, `calendar_epoch_start`
  > becomes the **max over bodies** of first-covered date, and that value is
  > recorded in the ledger. The calendar never claims coverage a body cannot
  > support.

So `calendar_epoch_start` is ALWAYS computed as the max-over-bodies
first-covered date and ALWAYS surfaced as data — it is not a constant this
module carries. Symmetrically `calendar_epoch_end` is the min-over-bodies
last-covered date: the calendar cannot claim a day some body cannot support
at either end. The nominal floor (1900-01-01) is only ever the *expectation*
this validation checks the live substrate against; the epoch is derived from
live coverage, "so it moves only if `ephemeris_daily` moves".

BODY LIST IS IMPORTED, NEVER RESTATED (CLAUDE.md §N.7 item 3 — no
wrapper-local constant may shadow a computed value, even when it currently
happens to be correct). The nine bodies come from
`brahmagyan.l0_ephemeris.DAILY_BODIES`, the same list the builder used.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ._db import QueryFn, table_exists
from .types import FAIL, INDETERMINATE, PASS, ValidationResult

# ADJUDICATION-5: the ephemeris floor is the *expected* epoch start. It is an
# EXPECTATION under test here, not an asserted fact — the measured
# `calendar_epoch_start` below is what any consumer must use.
NOMINAL_EPOCH_START = date(1900, 1, 1)
# Design §2/§7: chart-anchored forward horizon. Unchanged by ADJUDICATION-5
# ("Forward horizon unchanged at 2084 for chart-anchored work").
REQUIRED_END = date(2084, 12, 31)

TABLE = "ephemeris_daily"
AYANAMSHA_ID = "tropical"


def _required_bodies() -> list[str]:
    from brahmagyan.l0_ephemeris import DAILY_BODIES

    return [b["name"] for b in DAILY_BODIES]


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def validate_v2_ephemeris_coverage(
    query: QueryFn,
    required_end: date = REQUIRED_END,
    nominal_epoch_start: date = NOMINAL_EPOCH_START,
) -> ValidationResult:
    title = (
        "V2 — ephemeris_daily coverage + daily cadence for "
        f"{nominal_epoch_start.isoformat()}..{required_end.isoformat()} x 9 bodies "
        "(ADJUDICATION-5 amended)"
    )

    if not table_exists(query, TABLE):
        return ValidationResult(
            validation_id="V2",
            title=title,
            status=INDETERMINATE,
            summary=f"`{TABLE}` is not present in this database.",
            reason=(
                f"table `{TABLE}` does not exist — the spline substrate (design §2.1) "
                "has no source to be measured against."
            ),
        )

    per_body = query(
        f"SELECT body, MIN(date) AS first_date, MAX(date) AS last_date, "
        f"COUNT(*) AS n_rows, COUNT(DISTINCT date) AS n_dates "
        f"FROM {TABLE} WHERE ayanamsha_id = %s GROUP BY body ORDER BY body",
        [AYANAMSHA_ID],
    )

    if not per_body:
        return ValidationResult(
            validation_id="V2",
            title=title,
            status=FAIL,
            summary=f"`{TABLE}` holds zero rows for ayanamsha_id={AYANAMSHA_ID!r}.",
            data={"bodies_measured": 0},
            findings=[
                "The 2.0 spline substrate has no position source at all. "
                "Nothing downstream of design §2.1 can be built."
            ],
        )

    required = _required_bodies()
    coverage: dict[str, dict[str, Any]] = {}
    for row in per_body:
        first = _as_date(row["first_date"])
        last = _as_date(row["last_date"])
        n_dates = int(row["n_dates"])
        n_rows = int(row["n_rows"])
        span_days = (last - first).days + 1 if first and last else 0
        coverage[row["body"]] = {
            "first_date": first.isoformat() if first else None,
            "last_date": last.isoformat() if last else None,
            "n_rows": n_rows,
            "n_distinct_dates": n_dates,
            "span_days": span_days,
            # A daily cadence with no gap and no duplicate satisfies BOTH of
            # these. They are reported separately so a failure says WHICH.
            "contiguous_daily": span_days == n_dates,
            "one_row_per_date": n_rows == n_dates,
        }

    findings: list[str] = []

    present = set(coverage)
    missing_bodies = [b for b in required if b not in present]
    unexpected_bodies = sorted(present - set(required))
    if unexpected_bodies:
        findings.append(
            f"Bodies present in `{TABLE}` but not in DAILY_BODIES: {unexpected_bodies}. "
            "The event calendar must decide explicitly whether it covers them."
        )

    measured = [c for c in coverage.values() if c["first_date"] and c["last_date"]]
    if measured:
        # ADJUDICATION-5: max over bodies of first-covered, min over bodies of
        # last-covered. The calendar never claims coverage a body cannot support.
        calendar_epoch_start = max(date.fromisoformat(c["first_date"]) for c in measured)
        calendar_epoch_end = min(date.fromisoformat(c["last_date"]) for c in measured)
    else:  # pragma: no cover - unreachable while per_body is non-empty
        calendar_epoch_start = calendar_epoch_end = None

    gap_bodies = sorted(b for b, c in coverage.items() if not c["contiguous_daily"])
    dup_bodies = sorted(b for b, c in coverage.items() if not c["one_row_per_date"])

    gap_detail: dict[str, list[dict[str, Any]]] = {}
    for body in gap_bodies:
        gap_detail[body] = _sample_gaps(query, body)

    epoch_start_is_late = (
        calendar_epoch_start is not None and calendar_epoch_start > nominal_epoch_start
    )
    epoch_end_is_short = (
        calendar_epoch_end is not None and calendar_epoch_end < required_end
    )

    if missing_bodies:
        findings.append(
            f"Bodies absent from `{TABLE}`: {missing_bodies}. "
            "The chart-independent event calendar (design §2.2) cannot enumerate "
            "their transitions."
        )
    if epoch_start_is_late:
        findings.append(
            f"calendar_epoch_start is {calendar_epoch_start.isoformat()}, LATER than the "
            f"nominal ephemeris floor {nominal_epoch_start.isoformat()}. Per ADJUDICATION-5 "
            "this measured value — not 1900-01-01 — is the epoch, and it must be recorded "
            "in the ledger and served as data."
        )
    if epoch_end_is_short:
        findings.append(
            f"calendar_epoch_end is {calendar_epoch_end.isoformat()}, EARLIER than the "
            f"required chart-anchored horizon {required_end.isoformat()}."
        )
    if gap_bodies:
        findings.append(
            f"Non-contiguous daily cadence (gaps) for: {gap_bodies}. Spline fitting "
            "across a gap silently degrades interpolation accuracy exactly where V3's "
            "tolerance is set."
        )
    if dup_bodies:
        findings.append(
            f"More rows than distinct dates (duplicate (date, body) rows) for: {dup_bodies}."
        )

    ok = not (
        missing_bodies or epoch_start_is_late or epoch_end_is_short or gap_bodies or dup_bodies
    )

    data = {
        "table": TABLE,
        "ayanamsha_id": AYANAMSHA_ID,
        "required_bodies": required,
        "bodies_measured": len(coverage),
        "missing_bodies": missing_bodies,
        "unexpected_bodies": unexpected_bodies,
        # The two values ADJUDICATION-5 requires be recorded and served as data.
        "calendar_epoch_start": calendar_epoch_start.isoformat() if calendar_epoch_start else None,
        "calendar_epoch_end": calendar_epoch_end.isoformat() if calendar_epoch_end else None,
        "calendar_epoch_start_basis": "max_over_bodies_first_covered_date",
        "calendar_epoch_end_basis": "min_over_bodies_last_covered_date",
        "nominal_epoch_start": nominal_epoch_start.isoformat(),
        "required_end": required_end.isoformat(),
        "epoch_start_later_than_nominal": epoch_start_is_late,
        "gap_bodies": gap_bodies,
        "gap_samples": gap_detail,
        "duplicate_date_bodies": dup_bodies,
        "per_body": coverage,
        "total_rows": sum(c["n_rows"] for c in coverage.values()),
    }

    if ok:
        summary = (
            f"{len(coverage)}/9 bodies cover "
            f"{calendar_epoch_start.isoformat()}..{calendar_epoch_end.isoformat()} "
            "at contiguous daily cadence with one row per (date, body)."
        )
    else:
        summary = (
            f"Coverage/cadence does NOT satisfy the ADJUDICATION-5 epoch: "
            f"{len(findings)} finding(s); measured epoch "
            f"{calendar_epoch_start}..{calendar_epoch_end}."
        )

    return ValidationResult(
        validation_id="V2",
        title=title,
        status=PASS if ok else FAIL,
        summary=summary,
        data=data,
        findings=findings,
    )


def _sample_gaps(query: QueryFn, body: str, limit: int = 20) -> list[dict[str, Any]]:
    """Return up to `limit` concrete gaps for `body` — the honest evidence
    behind a cadence FAIL, so a downstream lane never has to take the
    aggregate count on trust."""
    rows = query(
        f"""
        SELECT prev_date, date AS next_date, (date - prev_date) AS gap_days
        FROM (
            SELECT date, LAG(date) OVER (ORDER BY date) AS prev_date
            FROM {TABLE} WHERE body = %s AND ayanamsha_id = %s
        ) s
        WHERE prev_date IS NOT NULL AND (date - prev_date) <> 1
        ORDER BY prev_date
        LIMIT %s
        """,
        [body, AYANAMSHA_ID, limit],
    )
    out = []
    for r in rows:
        prev = _as_date(r["prev_date"])
        nxt = _as_date(r["next_date"])
        out.append(
            {
                "after": prev.isoformat() if prev else None,
                "before": nxt.isoformat() if nxt else None,
                "gap_days": int(r["gap_days"]),
                "missing_from": (prev + timedelta(days=1)).isoformat() if prev else None,
            }
        )
    return out


__all__ = [
    "validate_v2_ephemeris_coverage",
    "NOMINAL_EPOCH_START",
    "REQUIRED_END",
]
