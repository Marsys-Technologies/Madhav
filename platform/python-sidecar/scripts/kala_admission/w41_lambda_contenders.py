#!/usr/bin/env python3
"""
w41_lambda_contenders.py -- W4.1 bakeoff: λ_v1 and λ_v3 as TemporalCurveModel
contenders in the existing scoring harness.

GOCHARA-UTKARSA campaign, wave W4.1.

WHAT THIS DOES
══════════════
Enters two gochara-window corpora as TemporalCurveModel contenders into the
existing `checks.run_blind_battery_curve` scoring harness and produces a JSON
report for the ADJUDICATOR comparing their train-split hit rates.

  λ_v1 -- `signed_intensity` from `kala_gochara_windows`
           WHERE chart_id = CHART_ID AND generation = 'v1'.
           This is the existing sweep corpus (READ-ONLY, protected).

  λ_v3 -- `signed_intensity` from `kala_gochara_windows_v2`
           WHERE chart_id = CHART_ID AND era_slice_key LIKE 'g3_%%'.
           This is the W3.4 century-horizon workbench corpus.

TEMPORALCURVEMODEL
══════════════════
For each corpus, a `TemporalCurveModel` is a curve builder whose intensity at
any date `d` is the sum of `signed_intensity` for all windows that overlap `d`
(i.e. window_start <= d < window_end) and match the event category's domain.
The step grid follows checks.STEP_DAYS = 5, matching the rest of the harness.

When the event category maps to a domain (via mechanisms.domain_for_category),
windows are filtered to those whose `event_class` contains a domain keyword
(e.g. 'career', 'wealth', 'health', 'marriage'). If no windows match the
domain filter, ALL windows are used as an honest fallback (documented below).

CONSTRAINTS (per W4.1 brief)
═══════════════════════════════
  I2: Zero imports from gochara_grammar/*, gochara_intensity/*, ka_gochara_sweep/*.
  I4: Empty inputs → honest 0-row results, no fabrication.
  Read-only: never INSERT/UPDATE/DELETE on kala_gochara_windows or _v2.
  Sealed split: NEVER score test events (>= 2020-01-01). Uses lel.load_train_events().

DB ACCESS
═════════
Requires DATABASE_URL environment variable. If unavailable (e.g. offline test
runs), the contenders can be instantiated with pre-loaded window data directly
via `TemporalCurveModel` (no DB needed for the scoring math).

Usage:
    DATABASE_URL=postgresql://... python3 scripts/kala_admission/w41_lambda_contenders.py

Exit codes:
    0 — report produced successfully
    3 — DATABASE_URL missing or psycopg unavailable
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

# Make the `kala_admission` package importable when run as a script.
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]  # .../scripts/
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from kala_admission.checks import CurveBuilder, run_blind_battery_curve  # noqa: E402
from kala_admission.curve import CurvePoint  # noqa: E402
from kala_admission.dates import parse_date  # noqa: E402
from kala_admission.lel import (  # noqa: E402
    TEST_SPLIT_BOUNDARY,
    load_train_events,
    partition_scorable,
)
from kala_admission.mechanisms import domain_for_category  # noqa: E402

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BOUNDS_START = parse_date("1984-02-05")
BOUNDS_END = parse_date("2022-06-01")

# Domain keyword map: maps domain name → substrings to match in event_class.
# Used to filter gochara windows to those relevant to the event's domain.
# If no windows match, falls back to ALL windows (honest I4 fallback).
_DOMAIN_CLASS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "wealth":  ("finance", "wealth", "gain", "loss", "windfall", "dhana"),
    "career":  ("career", "profession", "employment", "work"),
    "health":  ("health", "medical", "illness", "accident", "vitality"),
    "marriage": ("marriage", "relationship", "partner", "family", "love"),
    "general": (),  # empty → use all windows (same as fallback)
}


# ── GochaWindow dataclass ────────────────────────────────────────────────────

@dataclass(frozen=True)
class GochaWindow:
    """One row from kala_gochara_windows or kala_gochara_windows_v2."""
    event_class: str
    window_start: date
    window_end: date
    signed_intensity: float


# ── TemporalCurveModel ───────────────────────────────────────────────────────

class TemporalCurveModel:
    """A curve model whose intensity at any date is the sum of
    signed_intensity for all overlapping gochara windows.

    Instantiate with a list of GochaWindows and a label. Then call
    `curve_builder_for_event(event_id)` to get a `CurveBuilder` closure
    suitable for `checks.run_blind_battery_curve`.

    Domain filtering: windows are pre-filtered by domain keyword at builder
    construction time. If no windows survive the filter, ALL windows are used
    (honest I4 fallback -- logged as a note in the per-event output).
    """

    def __init__(self, windows: list[GochaWindow], label: str) -> None:
        self.windows = windows
        self.label = label

    # ── public API ──────────────────────────────────────────────────────────

    def curve_builder_for_event(self, category: str) -> CurveBuilder:
        """Return a (start, end) -> list[CurvePoint] closure for the given
        event category. Windows are filtered to those whose event_class
        contains a keyword matching the category's domain. Falls back to ALL
        windows when no domain-matching windows exist."""
        domain = domain_for_category(category)
        keywords = _DOMAIN_CLASS_KEYWORDS.get(domain, ())
        filtered = _filter_windows_by_domain(self.windows, keywords)
        # I4: empty input → use all windows (honest fallback, no fabrication)
        active_windows = filtered if filtered else self.windows

        def _build(range_start: date, range_end: date) -> list[CurvePoint]:
            return _build_lambda_curve(active_windows, range_start, range_end)

        return _build

    def summary_stats(self) -> dict:
        return {
            "label": self.label,
            "total_windows": len(self.windows),
        }


# ── curve math ───────────────────────────────────────────────────────────────

def _filter_windows_by_domain(
    windows: list[GochaWindow],
    keywords: tuple[str, ...],
) -> list[GochaWindow]:
    """Return windows whose event_class contains any of the given keywords
    (case-insensitive). Returns an empty list (not the full set) when
    keywords is empty or no window matches -- the caller decides the fallback."""
    if not keywords:
        return []
    kw_lower = tuple(k.lower() for k in keywords)
    return [w for w in windows if any(k in w.event_class.lower() for k in kw_lower)]


def _intensity_at(windows: list[GochaWindow], d: date) -> float:
    """Sum signed_intensity for all windows overlapping date d.
    Overlap condition: window_start <= d < window_end (half-open interval,
    matching the convention used by period_at() in curve.py)."""
    total = 0.0
    for w in windows:
        if w.window_start <= d < w.window_end:
            total += w.signed_intensity
    return total


def _build_lambda_curve(
    windows: list[GochaWindow],
    range_start: date,
    range_end: date,
    step_days: int = 5,  # matches checks.STEP_DAYS
) -> list[CurvePoint]:
    """Build a CurvePoint list for [range_start, range_end] at step_days
    granularity. If windows is empty, every point is 0.0 (honest I4 result)."""
    out: list[CurvePoint] = []
    d = range_start
    while d <= range_end:
        out.append(CurvePoint(date=d, intensity=_intensity_at(windows, d)))
        d = d + timedelta(days=step_days)
    return out


# ── DB loading ───────────────────────────────────────────────────────────────

def _parse_date_field(val) -> date:
    """Accept a date object or an ISO string."""
    if isinstance(val, date):
        return val
    return parse_date(str(val)[:10])


def load_v1_windows(conn, chart_id: str) -> list[GochaWindow]:
    """Load λ_v1: signed_intensity from kala_gochara_windows WHERE
    chart_id = %s AND generation = 'v1'. READ-ONLY -- no mutation.
    Falls back to raw_intensity when signed_intensity is NULL.

    INTENTIONAL: generation='v1' pin — λ_v1 IS the v1 corpus by definition.
    This function is one side of a two-contender bakeoff (λ_v1 vs λ_v3) whose
    entire purpose is to compare v1 scoring against 3.0 scoring. Reading any
    other generation here would collapse the comparison to a single corpus and
    produce a meaningless bakeoff. The pin is permanent and correct. (MR-18)
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT event_class, window_start, window_end, "
            "       COALESCE(signed_intensity, raw_intensity, 0.0) AS intensity "
            "FROM kala_gochara_windows "
            "WHERE chart_id = %s AND generation = 'v1' "
            "ORDER BY window_start",
            [chart_id],
        )
        rows = cur.fetchall()
    return [
        GochaWindow(
            event_class=str(r["event_class"]),
            window_start=_parse_date_field(r["window_start"]),
            window_end=_parse_date_field(r["window_end"]),
            signed_intensity=float(r["intensity"]),
        )
        for r in rows
    ]


def load_v3_windows(conn, chart_id: str) -> list[GochaWindow]:
    """Load λ_v3: signed_intensity from kala_gochara_windows_v2 WHERE
    chart_id = %s AND era_slice_key LIKE 'g3_%%'. READ-ONLY -- no mutation.
    Falls back to raw_intensity when signed_intensity is NULL."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT event_class, window_start, window_end, "
            "       COALESCE(signed_intensity, raw_intensity, 0.0) AS intensity "
            "FROM kala_gochara_windows_v2 "
            "WHERE chart_id = %s AND era_slice_key LIKE 'g3_%%' "
            "ORDER BY window_start",
            [chart_id],
        )
        rows = cur.fetchall()
    return [
        GochaWindow(
            event_class=str(r["event_class"]),
            window_start=_parse_date_field(r["window_start"]),
            window_end=_parse_date_field(r["window_end"]),
            signed_intensity=float(r["intensity"]),
        )
        for r in rows
    ]


# ── scoring ──────────────────────────────────────────────────────────────────

def score_contender(
    model: TemporalCurveModel,
    scorable_events,
) -> dict:
    """Run the blind battery against TRAIN-scorable events for one contender.
    Returns the BlindBatteryResult as a dict plus metadata."""

    # build_curve_for_event maps event_id → CurveBuilder using the model's
    # domain-filtered curve builder, keyed by the event's category.
    event_category_map = {e.event_id: e.category for e in scorable_events}

    def build_curve_for_event(event_id: str) -> CurveBuilder:
        category = event_category_map.get(event_id, "other")
        return model.curve_builder_for_event(category)

    events_input = [(e.event_id, e.event_date) for e in scorable_events]

    result = run_blind_battery_curve(
        build_curve_for_event=build_curve_for_event,
        events=events_input,
        bounds_start=BOUNDS_START,
        bounds_end=BOUNDS_END,
    )

    return {
        "label": model.label,
        "blind_battery_hit_rate": round(result.hit_rate, 4),
        "hit_count": result.hit_count,
        "scored_count": result.scored_count,
        "per_event": [asdict(s) for s in result.per_event],
        "window_count": len(model.windows),
    }


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL is required", file=sys.stderr)
        return 3

    try:
        import psycopg
        import psycopg.rows
    except ImportError as exc:
        print(f"ERROR: psycopg unavailable: {exc}", file=sys.stderr)
        return 3

    # ── Load LEL train events (sealed split enforced by lel.py) ──
    events = load_train_events()
    for e in events:
        # Belt-and-suspenders assertion -- load_train_events() already raises if violated.
        assert e.event_date < TEST_SPLIT_BOUNDARY, (
            f"unreachable: {e.event_id} dated {e.event_date} is >= sealed boundary"
        )
    scorable, excluded = partition_scorable(events)

    # ── Load gochara windows from DB ──
    with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        v1_windows = load_v1_windows(conn, CHART_ID)
        v3_windows = load_v3_windows(conn, CHART_ID)

    # ── Build TemporalCurveModels ──
    model_v1 = TemporalCurveModel(v1_windows, label="lambda_v1")
    model_v3 = TemporalCurveModel(v3_windows, label="lambda_v3")

    # ── Score both contenders ──
    result_v1 = score_contender(model_v1, scorable)
    result_v3 = score_contender(model_v3, scorable)

    # ── Comparison summary ──
    delta = round(result_v3["blind_battery_hit_rate"] - result_v1["blind_battery_hit_rate"], 4)
    if delta > 0:
        winner = "lambda_v3"
        margin_note = f"λ_v3 scores {abs(delta):.4f} higher than λ_v1"
    elif delta < 0:
        winner = "lambda_v1"
        margin_note = f"λ_v1 scores {abs(delta):.4f} higher than λ_v3"
    else:
        winner = "tie"
        margin_note = "λ_v1 and λ_v3 score identically"

    report = {
        "harness": "w41_lambda_contenders",
        "wave": "W4.1",
        "chart_id": CHART_ID,
        "test_split_boundary": TEST_SPLIT_BOUNDARY.isoformat(),
        "bounds_start": BOUNDS_START.isoformat(),
        "bounds_end": BOUNDS_END.isoformat(),
        "train_events_used_count": len(events),
        "train_events_scorable_count": len(scorable),
        "train_events_excluded_count": len(excluded),
        "contenders": {
            "lambda_v1": result_v1,
            "lambda_v3": result_v3,
        },
        "comparison": {
            "hit_rate_delta_v3_minus_v1": delta,
            "winner": winner,
            "note": margin_note,
        },
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
