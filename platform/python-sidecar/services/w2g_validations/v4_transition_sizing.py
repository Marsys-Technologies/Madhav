"""
W2G V4 — transition-count sizing.

Design §6 V4: "transition-count estimate for this chart (events per primitive
family — validates the 'tens of thousands' sizing)."
Design §2.3: "an outer body crosses a given degree 1-3x per cycle (retro
loops); total per-chart events ~= tens of thousands of millisecond
root-finds."

HOW THE CHART-SPECIFIC COUNT IS DERIVED WITHOUT GUESSING AT RETRO LOOPS.
The naive sizing ("laps around the zodiac, times 1-3 for retrogradation")
requires a hand-waved multiplier. It is unnecessary. For a body whose
longitude traces a continuous path, the number of times it crosses a FIXED
degree over an interval is exactly the path's total angular variation
divided by 360 — averaged over where that degree sits, and counting every
retrograde re-crossing automatically, because a retrograde loop contributes
its own arc length to the total variation twice over.

Total variation is directly measurable from `ephemeris_daily`: sum the
shortest-arc day-to-day steps. That turns "1-3x per cycle" from an assumed
multiplier into a measured quantity, per body, over the real epoch.

Daily sampling cannot alias here: no body in the substrate moves more than
~15 deg/day, far under the 180 deg/step at which shortest-arc attribution
would become ambiguous. The Moon's intra-day curvature makes the daily-step
sum a slight UNDER-estimate of true path length, so the crossing counts
below are a lower bound — stated, not silently absorbed.

GLOBAL (chart-independent) counts — design §2.2's "sky's own diary" — are
counted directly: sign ingresses, nakshatra ingresses, and stations, all
detected as real transitions in the substrate via window functions, not
estimated from mean motions.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from ._db import QueryFn, table_exists
from .types import FAIL, INDETERMINATE, PASS, ValidationResult

EPHEMERIS_TABLE = "ephemeris_daily"
RESONANCE_TABLE = "gochara_resonance_map"
AYANAMSHA_ID = "tropical"

# Design §2.3's own sizing claim, as the band this validation tests against.
TENS_OF_THOUSANDS_LOW = 10_000
TENS_OF_THOUSANDS_HIGH = 100_000

# Design §2.3: "root-solve orb entry/exit/peak crossings". Three solved
# instants per crossing of a target degree.
EVENTS_PER_CROSSING = 3

# Design §2.5: "Moon/lagna-scale precision computed LAZILY — materialized only
# inside windows the slow layers already elevate". The Moon is the whole of
# the lazy layer among the nine ephemeris bodies (lagna is chart-parameterised
# and is not in `ephemeris_daily` at all).
LAZY_LAYER_BODIES = frozenset({"Moon"})


def _shortest_arc_sum_sql() -> str:
    """Sum of |shortest-arc daily step| per body, over the whole substrate.

    `MOD(MOD(d, 360) + 540, 360) - 180` maps any raw difference into
    (-180, 180], which is the shortest arc; its magnitude is the step length.

    `MOD(...)` is used rather than the `%` operator ON PURPOSE: psycopg reads
    a bare `%` in a parameterised statement as the start of a placeholder and
    raises `incomplete placeholder`. Escaping it as `%%` would work but leaves
    a statement that is wrong the moment someone runs it by hand. `MOD()` is
    correct in both contexts. (Found live, not in review — see
    `test_v4_sql_uses_mod_not_percent`.)
    """
    return f"""
        SELECT body,
               SUM(ABS(MOD(MOD(tropical_longitude - prev_lon, 360) + 540, 360) - 180)) AS total_variation_deg,
               COUNT(*) AS n_steps,
               MIN(date) AS variation_first_date,
               MAX(date) AS variation_last_date
        FROM (
            SELECT body, date, tropical_longitude,
                   LAG(tropical_longitude) OVER (PARTITION BY body ORDER BY date) AS prev_lon
            FROM {EPHEMERIS_TABLE} WHERE ayanamsha_id = %s
              AND date BETWEEN %s AND %s
        ) s
        WHERE prev_lon IS NOT NULL
        GROUP BY body ORDER BY body
    """


def _global_transition_sql() -> str:
    return f"""
        SELECT body,
               COUNT(*) FILTER (WHERE sign_number <> prev_sign)                 AS sign_ingresses,
               COUNT(*) FILTER (WHERE nakshatra_number <> prev_nak)             AS nakshatra_ingresses,
               COUNT(*) FILTER (WHERE SIGN(speed_dps) <> SIGN(prev_speed))      AS stations
        FROM (
            SELECT body, sign_number, nakshatra_number, speed_dps,
                   LAG(sign_number)      OVER (PARTITION BY body ORDER BY date) AS prev_sign,
                   LAG(nakshatra_number) OVER (PARTITION BY body ORDER BY date) AS prev_nak,
                   LAG(speed_dps)        OVER (PARTITION BY body ORDER BY date) AS prev_speed
            FROM {EPHEMERIS_TABLE} WHERE ayanamsha_id = %s
              AND date BETWEEN %s AND %s
        ) s
        WHERE prev_sign IS NOT NULL
        GROUP BY body ORDER BY body
    """


def validate_v4_transition_sizing(
    query: QueryFn,
    chart_ids: list[str],
    epoch_start: date,
    epoch_end: date,
) -> ValidationResult:
    title = (
        "V4 — measured transition counts (global calendar) and chart-specific "
        "contact-event sizing vs design §2.3's 'tens of thousands'"
    )

    for table in (EPHEMERIS_TABLE, RESONANCE_TABLE):
        if not table_exists(query, table):
            return ValidationResult(
                validation_id="V4",
                title=title,
                status=INDETERMINATE,
                summary=f"`{table}` is not present in this database.",
                reason=f"cannot size transitions without `{table}`",
            )

    variation_rows = query(_shortest_arc_sum_sql(), [AYANAMSHA_ID, epoch_start, epoch_end])
    if not variation_rows:
        return ValidationResult(
            validation_id="V4",
            title=title,
            status=INDETERMINATE,
            summary="No ephemeris rows inside the requested epoch.",
            reason=(
                f"`{EPHEMERIS_TABLE}` returned no rows for "
                f"{epoch_start.isoformat()}..{epoch_end.isoformat()}"
            ),
        )

    crossings_per_degree: dict[str, float] = {}
    variation: dict[str, Any] = {}
    for r in variation_rows:
        total_var = float(r["total_variation_deg"] or 0.0)
        crossings_per_degree[r["body"]] = total_var / 360.0
        variation[r["body"]] = {
            "total_variation_deg": round(total_var, 3),
            "crossings_per_fixed_degree": round(total_var / 360.0, 3),
            "n_daily_steps": int(r["n_steps"]),
        }

    global_rows = query(_global_transition_sql(), [AYANAMSHA_ID, epoch_start, epoch_end])
    global_calendar: dict[str, Any] = {}
    for r in global_rows:
        global_calendar[r["body"]] = {
            "sign_ingresses": int(r["sign_ingresses"]),
            "nakshatra_ingresses": int(r["nakshatra_ingresses"]),
            "stations": int(r["stations"]),
        }
    global_totals = {
        key: sum(v[key] for v in global_calendar.values())
        for key in ("sign_ingresses", "nakshatra_ingresses", "stations")
    }
    global_totals["all_families"] = sum(global_totals.values())

    target_rows = query(
        f"SELECT chart_id::text AS chart_id, event_class, COUNT(*) AS n "
        f"FROM {RESONANCE_TABLE} WHERE chart_id::text = ANY(%s) "
        f"GROUP BY chart_id, event_class ORDER BY chart_id, event_class",
        [list(chart_ids)],
    )

    # A transiting body crosses each target degree; every body in the
    # substrate is a transiting body for this purpose.
    mean_crossings = (
        sum(crossings_per_degree.values()) / len(crossings_per_degree)
        if crossings_per_degree
        else 0.0
    )
    total_crossings_all_bodies = sum(crossings_per_degree.values())
    # Design §2.5 splits the work by rate: slow layers are computed FULL-SPAN
    # EAGERLY, while "Moon/lagna-scale precision [is] computed lazily —
    # materialized only inside windows the slow layers already elevate". The
    # eager budget is therefore the all-bodies-except-Moon figure; the Moon's
    # share is the lazy layer's, and reporting one number for both would
    # misattribute the entire architecture's savings.
    eager_crossings = sum(
        v for b, v in crossings_per_degree.items() if b not in LAZY_LAYER_BODIES
    )
    lazy_crossings = total_crossings_all_bodies - eager_crossings

    per_chart: dict[str, Any] = {}
    for chart_id in chart_ids:
        rows = [r for r in target_rows if r["chart_id"] == chart_id]
        by_class = {r["event_class"]: int(r["n"]) for r in rows}
        n_targets = sum(by_class.values())
        # Each (target degree x transiting body) pair yields
        # crossings_per_degree[body] crossings over the epoch, and each
        # crossing yields EVENTS_PER_CROSSING root-solved instants.
        contact_events = n_targets * total_crossings_all_bodies * EVENTS_PER_CROSSING
        eager_events = n_targets * eager_crossings * EVENTS_PER_CROSSING
        per_chart[chart_id] = {
            "n_resonance_targets": n_targets,
            "targets_by_event_class": by_class,
            "estimated_contact_events": int(round(contact_events)),
            "estimated_contact_events_eager_layer": int(round(eager_events)),
            "estimated_contact_events_lazy_layer": int(round(contact_events - eager_events)),
            "basis": (
                "n_targets x SUM_over_bodies(total_angular_variation/360) x "
                f"{EVENTS_PER_CROSSING} (orb entry/peak/exit); the eager figure "
                f"excludes {sorted(LAZY_LAYER_BODIES)} per design §2.5's lazy layer"
            ),
        }

    findings: list[str] = [
        "Crossing counts are derived from measured total angular variation, so "
        "retrograde re-crossings are counted as they actually occur — no assumed "
        "'1-3x per cycle' multiplier appears anywhere in this number.",
        "Daily sampling makes the Moon's path length a slight under-estimate, so "
        "every count here is a LOWER bound.",
    ]

    charted = [v["estimated_contact_events"] for v in per_chart.values() if v["n_resonance_targets"]]
    if not charted:
        return ValidationResult(
            validation_id="V4",
            title=title,
            status=INDETERMINATE,
            summary="No resonance-map targets for any requested chart.",
            reason=(
                f"`{RESONANCE_TABLE}` has no rows for {chart_ids} — the chart-specific "
                "contact-event count design §6 V4 asks for has no input"
            ),
            data={
                "epoch": [epoch_start.isoformat(), epoch_end.isoformat()],
                "global_calendar_by_body": global_calendar,
                "global_calendar_totals": global_totals,
                "angular_variation_by_body": variation,
            },
            findings=findings,
        )

    max_events = max(charted)
    max_eager = max(
        v["estimated_contact_events_eager_layer"]
        for v in per_chart.values()
        if v["n_resonance_targets"]
    )
    in_band = TENS_OF_THOUSANDS_LOW <= max_events <= TENS_OF_THOUSANDS_HIGH
    if not in_band:
        side = "BELOW" if max_events < TENS_OF_THOUSANDS_LOW else "ABOVE"
        findings.append(
            f"Largest chart-specific contact-event count is {max_events:,}, {side} design "
            f"§2.3's stated 'tens of thousands' band "
            f"({TENS_OF_THOUSANDS_LOW:,}-{TENS_OF_THOUSANDS_HIGH:,}). The sizing assumption "
            "that the E-3 solver budget rests on does not hold as written and must be "
            "re-stated from this measurement before E-3 is scoped."
        )
        eager_in_band = TENS_OF_THOUSANDS_LOW <= max_eager <= TENS_OF_THOUSANDS_HIGH
        findings.append(
            f"Split by design §2.5's own eager/lazy architecture, the EAGER layer "
            f"(all bodies except {sorted(LAZY_LAYER_BODIES)}) is {max_eager:,} events and "
            f"the Moon accounts for the remaining {max_events - max_eager:,}. The Moon is "
            f"{round(100.0 * (max_events - max_eager) / max_events)}% of the total, which is "
            "precisely why §2.5 defers it — but the eager layer alone is "
            + ("still ABOVE" if not eager_in_band else "inside")
            + " the stated band, so §2.5's lazy refinement is a NECESSARY but not "
            "SUFFICIENT condition for the §2.3 sizing to hold."
        )

    return ValidationResult(
        validation_id="V4",
        title=title,
        status=PASS if in_band else FAIL,
        summary=(
            f"Global calendar: {global_totals['all_families']:,} transitions over "
            f"{epoch_start.isoformat()}..{epoch_end.isoformat()}. "
            f"Largest chart-specific contact-event estimate: {max_events:,} "
            f"({max_eager:,} eager + {max_events - max_eager:,} lazy/Moon; "
            f"design band {TENS_OF_THOUSANDS_LOW:,}-{TENS_OF_THOUSANDS_HIGH:,})."
        ),
        data={
            "epoch": [epoch_start.isoformat(), epoch_end.isoformat()],
            "global_calendar_by_body": global_calendar,
            "global_calendar_totals": global_totals,
            "angular_variation_by_body": variation,
            "mean_crossings_per_fixed_degree": round(mean_crossings, 3),
            "sum_crossings_per_fixed_degree_all_bodies": round(total_crossings_all_bodies, 3),
            "sum_crossings_eager_layer": round(eager_crossings, 3),
            "sum_crossings_lazy_layer": round(lazy_crossings, 3),
            "lazy_layer_bodies": sorted(LAZY_LAYER_BODIES),
            "events_per_crossing": EVENTS_PER_CROSSING,
            "per_chart": per_chart,
            "design_band": [TENS_OF_THOUSANDS_LOW, TENS_OF_THOUSANDS_HIGH],
            "largest_chart_estimate": max_events,
            "largest_chart_estimate_eager_layer": max_eager,
        },
        findings=findings,
    )


__all__ = [
    "validate_v4_transition_sizing",
    "EVENTS_PER_CROSSING",
    "TENS_OF_THOUSANDS_LOW",
    "TENS_OF_THOUSANDS_HIGH",
]
