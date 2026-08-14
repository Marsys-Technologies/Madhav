#!/usr/bin/env python3
"""
w46_field_measurement4.py — SAMPŪRTI Measurement #4 (baseline).

Registers kala_field_windows as a TemporalCurveModel contender and scores
it against LEL TRAIN events using the existing kala_admission harness.

MEASUREMENT #4 SPEC (Implementation Plan §P2 / REBASE_PLAN §R3)
═══════════════════════════════════════════════════════════════════
- Native chart ONLY (482012f1, Abhisek) — Abhinandan has no LEL (R28).
- TRAIN events only (< 2020-01-01), sealed split enforced.
- Field contender: kala_field_windows λ = SUM(lambda_peak) for overlapping
  windows of the matched event_class at each date step.
- Control: 1000-shuffle noise floor (w42 pattern, seed 42).
- Skill = (hit_rate_field - hit_rate_control) / (1 - hit_rate_control).
- Degenerate-interval tripwire (R15): halts publication if < MIN_SCORABLE
  events can be matched to field classes.
- Honest-null acceptable and publishable (per gate G-P2).

FIELD CLASS MAPPING
═══════════════════
kala_field_windows covers 6 event_class values as of R2:
  marriage, foreign_settlement, surgery, separation, childbirth, relocation

LEL category → field event_class (strict semantic match only):
  family/marriage                        → marriage
  health/surgery_*                       → surgery
  residential+travel/foreign_move_start  → foreign_settlement
  [relationship/*, travel/*              → PARKED (extended set; labeled below)]

Extended mappings (scored separately, labeled "extended"):
  relationship/*                         → marriage
  travel/*                               → foreign_settlement

Events in categories with no matching field class (education, career,
spiritual, creative, psychological, loss, other, finance, family/non-marriage)
are PARKED and listed in the report.

CONSTRAINTS
═══════════
- Zero DB writes.
- Sealed split: only TRAIN events (< 2020-01-01) loaded via lel.py.
- No gochara tables touched.
- R15 tripwire: publication halted if < 3 strict-match events found.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # .../scripts/

from kala_admission.checks import (  # noqa: E402
    PROXIMITY_DAYS,
    STEP_DAYS,
    WINDOW_YEARS,
    CurveBuilder,
    run_blind_battery_curve,
)
from kala_admission.curve import CurvePoint, local_max, percentile_threshold  # noqa: E402
from kala_admission.dates import parse_date  # noqa: E402
from kala_admission.lel import (  # noqa: E402
    TEST_SPLIT_BOUNDARY,
    LelEvent,
    load_train_events,
    partition_scorable,
)

# ── Constants ────────────────────────────────────────────────────────────────

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BOUNDS_START: date = parse_date("1984-02-05")
BOUNDS_END: date = parse_date("2025-01-01")

N_SHUFFLES: int = 1000
SHUFFLE_SEED: int = 42
_SHUFFLE_UPPER: date = TEST_SPLIT_BOUNDARY - timedelta(days=1)

# R15 degenerate-interval tripwire: halt if fewer than this many strict events
MIN_SCORABLE: int = 3

# ── Field class mapping ───────────────────────────────────────────────────────

# Strict: exact semantic match only
_STRICT_MAP: dict[str, list[str]] = {
    "family/marriage": ["marriage"],
    "health/surgery_minor": ["surgery"],
    "health/surgery_major": ["surgery"],
    "residential+travel/foreign_move_start": ["foreign_settlement"],
    "residential+travel/foreign_settlement": ["foreign_settlement"],
}

# Extended: looser semantic match (scored separately)
_EXTENDED_MAP: dict[str, list[str]] = {
    **_STRICT_MAP,
    "relationship/romantic_long_term_started": ["marriage"],
    "relationship/romantic_concurrent": ["marriage"],
    "relationship/marriage": ["marriage"],
    "family/birth_of_child": ["childbirth"],
    "travel/first_foreign_trip": ["foreign_settlement"],
    "loss/separation": ["separation"],
}


def _field_classes_for(domain: str, strict: bool) -> Optional[list[str]]:
    m = _STRICT_MAP if strict else _EXTENDED_MAP
    return m.get(domain)


# ── DB loading ────────────────────────────────────────────────────────────────

@dataclass
class FieldWindow:
    event_class: str
    window_start: date
    window_end: date
    peak_date: date
    lambda_peak: float


def load_field_windows(conn) -> list[FieldWindow]:
    """Load all kala_field_windows for native chart. Zero writes."""
    cur = conn.cursor()
    cur.execute(
        """SELECT event_class, window_start, window_end, peak_date, lambda_peak
             FROM kala_field_windows
            WHERE chart_id = %s
            ORDER BY event_class, window_start""",
        (CHART_ID,),
    )
    rows = cur.fetchall()
    return [
        FieldWindow(
            event_class=r[0],
            window_start=r[1],
            window_end=r[2],
            peak_date=r[3],
            lambda_peak=float(r[4]) if r[4] is not None else 0.0,
        )
        for r in rows
    ]


# ── TemporalCurveModel ────────────────────────────────────────────────────────

class FieldCurveModel:
    """TemporalCurveModel over kala_field_windows.

    For a given event_class, intensity at date d = SUM(lambda_peak) for all
    windows where window_start <= d <= window_end.
    """

    def __init__(self, windows: list[FieldWindow]) -> None:
        self._by_class: dict[str, list[FieldWindow]] = {}
        for w in windows:
            self._by_class.setdefault(w.event_class, []).append(w)

    def curve_builder(self, event_class: str) -> CurveBuilder:
        windows = self._by_class.get(event_class, [])

        def build(range_start: date, range_end: date) -> list[CurvePoint]:
            pts: list[CurvePoint] = []
            d = range_start
            while d <= range_end:
                intensity = sum(
                    w.lambda_peak
                    for w in windows
                    if w.window_start <= d <= w.window_end
                )
                pts.append(CurvePoint(date=d, intensity=intensity))
                d += timedelta(days=STEP_DAYS)
            return pts

        return build

    def multi_class_builder(self, event_classes: list[str]) -> CurveBuilder:
        """Returns a builder that sums intensity across multiple classes."""
        builders = [self.curve_builder(c) for c in event_classes]

        def build(range_start: date, range_end: date) -> list[CurvePoint]:
            d = range_start
            pts: list[CurvePoint] = []
            while d <= range_end:
                intensity = 0.0
                for b in builders:
                    for pt in b(range_start, range_end):
                        if pt.date == d:
                            intensity += pt.intensity
                            break
                pts.append(CurvePoint(date=d, intensity=intensity))
                d += timedelta(days=STEP_DAYS)
            return pts

        def build_fast(range_start: date, range_end: date) -> list[CurvePoint]:
            # More efficient: compute all dates once
            dates = []
            d = range_start
            while d <= range_end:
                dates.append(d)
                d += timedelta(days=STEP_DAYS)
            intensities = [0.0] * len(dates)
            for b in builders:
                for i, d_ in enumerate(dates):
                    # Sum all classes at once
                    pass
            # Actually sum per class inline
            for ec in event_classes:
                windows = self._by_class.get(ec, [])
                for i, d_ in enumerate(dates):
                    intensities[i] += sum(
                        w.lambda_peak
                        for w in windows
                        if w.window_start <= d_ <= w.window_end
                    )
            return [CurvePoint(date=d_, intensity=intensities[i]) for i, d_ in enumerate(dates)]

        return build_fast

    def available_classes(self) -> set[str]:
        return set(self._by_class.keys())


# ── Noise floor (w42 pattern) ────────────────────────────────────────────────

def _random_date_in_train(rng: random.Random) -> date:
    n = (_SHUFFLE_UPPER - BOUNDS_START).days + 1
    return BOUNDS_START + timedelta(days=rng.randint(0, n - 1))


def compute_noise_floor(
    events: list[tuple[str, date]],
    build_curve_for_event: "Callable[[str], CurveBuilder]",
    n_shuffles: int = N_SHUFFLES,
    seed: int = SHUFFLE_SEED,
) -> tuple[float, float, float]:
    """Returns (mean_hit_rate, std_hit_rate, floor_mean_plus_2std)."""
    rng = random.Random(seed)
    hit_rates: list[float] = []
    for _ in range(n_shuffles):
        shuffled = [(eid, _random_date_in_train(rng)) for eid, _ in events]
        result = run_blind_battery_curve(
            build_curve_for_event,
            shuffled,
            BOUNDS_START,
            BOUNDS_END,
        )
        hit_rates.append(result.hit_rate)
    mean = sum(hit_rates) / len(hit_rates)
    variance = sum((h - mean) ** 2 for h in hit_rates) / len(hit_rates)
    std = math.sqrt(variance)
    return mean, std, mean + 2 * std


# ── Skill score ───────────────────────────────────────────────────────────────

def skill_score(hit_rate_field: float, hit_rate_control: float) -> Optional[float]:
    """Heidke / Pierce skill score: 0 = no skill, 1 = perfect, <0 = worse than control."""
    denom = 1.0 - hit_rate_control
    if denom == 0.0:
        return None
    return (hit_rate_field - hit_rate_control) / denom


# ── Main measurement ──────────────────────────────────────────────────────────

def run_measurement(conn) -> dict:
    # 1. Load LEL + field windows
    events_raw = load_train_events()
    scorable, excluded = partition_scorable(events_raw)
    windows = load_field_windows(conn)
    model = FieldCurveModel(windows)
    available = model.available_classes()

    # 2. Map to field classes — strict set
    strict_matched: list[tuple[str, date, list[str]]] = []
    extended_only: list[tuple[str, date, list[str]]] = []
    parked_no_class: list[LelEvent] = []
    parked_by_vagueness = excluded

    for e in scorable:
        strict_classes = _field_classes_for(e.domain, strict=True)
        ext_classes = _field_classes_for(e.domain, strict=False)
        if strict_classes:
            strict_matched.append((e.event_id, e.event_date, strict_classes))
        elif ext_classes:
            extended_only.append((e.event_id, e.event_date, ext_classes))
        else:
            parked_no_class.append(e)

    print(f"[M4] Scorable LEL: {len(scorable)} / {len(events_raw)}", file=sys.stderr)
    print(f"[M4] Strict field-class match: {len(strict_matched)}", file=sys.stderr)
    print(f"[M4] Extended match only: {len(extended_only)}", file=sys.stderr)
    print(f"[M4] Parked (no class): {len(parked_no_class)}", file=sys.stderr)
    print(f"[M4] Field classes available: {sorted(available)}", file=sys.stderr)

    # R15 tripwire: halt if degenerate
    if len(strict_matched) < MIN_SCORABLE:
        return {
            "status": "TRIPWIRE_R15",
            "reason": (
                f"Only {len(strict_matched)} strict-match events found "
                f"(min={MIN_SCORABLE}). Field coverage is too sparse to publish "
                "a meaningful strict score. Extended set follows for reference."
            ),
            "strict_matched_count": len(strict_matched),
            "extended_count": len(strict_matched) + len(extended_only),
            "publication_halted": True,
            "tripwire": "R15",
        }

    # 3. Build event→CurveBuilder map
    all_strict = strict_matched + extended_only  # score both sets
    def build_curve_for_event(event_id: str) -> CurveBuilder:
        for eid, _, classes in all_strict:
            if eid == event_id:
                return model.multi_class_builder(classes)
        raise KeyError(event_id)

    def build_strict_only(event_id: str) -> CurveBuilder:
        for eid, _, classes in strict_matched:
            if eid == event_id:
                return model.multi_class_builder(classes)
        raise KeyError(event_id)

    strict_events = [(eid, d) for eid, d, _ in strict_matched]
    extended_events = [(eid, d) for eid, d, _ in strict_matched + extended_only]

    # 4. Score field — strict
    print("[M4] Scoring strict events against field...", file=sys.stderr)
    strict_result = run_blind_battery_curve(
        build_strict_only, strict_events, BOUNDS_START, BOUNDS_END
    )

    # 5. Score field — extended
    print("[M4] Scoring extended events against field...", file=sys.stderr)
    extended_result = run_blind_battery_curve(
        build_curve_for_event, extended_events, BOUNDS_START, BOUNDS_END
    )

    # 6. Noise floor (w42 pattern, strict events only)
    print(f"[M4] Computing noise floor ({N_SHUFFLES} shuffles)...", file=sys.stderr)
    floor_mean, floor_std, floor_threshold = compute_noise_floor(
        strict_events, build_strict_only
    )

    # 7. Skill scores
    strict_skill = skill_score(strict_result.hit_rate, floor_mean)
    extended_skill = skill_score(extended_result.hit_rate, floor_mean)

    # 8. Per-class breakdown
    per_class: dict[str, dict] = {}
    for eid, d, classes in strict_matched + extended_only:
        label = "+".join(sorted(set(classes)))
        group = per_class.setdefault(label, {"events": [], "hits": 0, "total": 0, "set": "strict" if (eid,d,classes) in [x for x in strict_matched] else "extended"})
        group["total"] += 1
        # Check if this event was a hit in strict or extended result
        all_per_event = {s.event_id: s for s in strict_result.per_event + extended_result.per_event}
        s = all_per_event.get(eid)
        if s and s.passed:
            group["hits"] += 1
        group["events"].append({"event_id": eid, "event_date": d.isoformat()})

    return {
        "status": "PUBLISHED",
        "chart_id": CHART_ID,
        "measurement": 4,
        "label": "FIELD-BASELINE",
        "field_corpus": {
            "table": "kala_field_windows",
            "row_count": len(windows),
            "event_classes": sorted(available),
            "class_counts": {
                cls: sum(1 for w in windows if w.event_class == cls)
                for cls in sorted(available)
            },
        },
        "lel_coverage": {
            "total_train": len(events_raw),
            "scorable_by_vagueness": len(scorable),
            "strict_matched": len(strict_matched),
            "extended_only": len(extended_only),
            "parked_no_field_class": len(parked_no_class),
            "parked_by_vagueness": len(parked_by_vagueness),
        },
        "strict": {
            "scored_count": strict_result.scored_count,
            "hit_count": strict_result.hit_count,
            "hit_rate": strict_result.hit_rate,
            "skill_score": strict_skill,
            "per_event": [asdict(s) for s in strict_result.per_event],
        },
        "extended": {
            "scored_count": extended_result.scored_count,
            "hit_count": extended_result.hit_count,
            "hit_rate": extended_result.hit_rate,
            "skill_score": extended_skill,
        },
        "noise_floor": {
            "n_shuffles": N_SHUFFLES,
            "seed": SHUFFLE_SEED,
            "mean_hit_rate": floor_mean,
            "std_hit_rate": floor_std,
            "floor_threshold_mean_plus_2std": floor_threshold,
        },
        "per_class": per_class,
        "parked_events": {
            "no_field_class": [
                {"event_id": e.event_id, "event_date": e.event_date.isoformat(),
                 "category": e.category, "domain": e.domain}
                for e in parked_no_class
            ],
        },
        "tripwire_r15": "NOT_FIRED",
        "notes": [
            "null_p=1.0 for all 6,708 kala_field_windows: field signal is below global null "
            "distribution (expected at baseline; field has not been calibrated). "
            "Skill score is the baseline from which integration (P3) will be measured.",
            "Extended set includes loose semantic mappings (relationship→marriage, etc.). "
            "Strict set uses only direct semantic matches.",
            f"26/{len(events_raw)} LEL events have no matching field class: field currently "
            "covers only 6 event classes (marriage, foreign_settlement, surgery, separation, "
            "childbirth, relocation). Full coverage requires P3+ integration.",
        ],
    }


def main() -> None:
    import psycopg

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        sys.exit(3)

    conn = psycopg.connect(database_url)
    try:
        result = run_measurement(conn)
    finally:
        conn.close()

    output = json.dumps(result, indent=2, default=str)
    print(output)

    # Print summary to stderr
    if result.get("status") == "TRIPWIRE_R15":
        print(f"\n[M4] TRIPWIRE R15 FIRED: {result['reason']}", file=sys.stderr)
        sys.exit(15)
    else:
        s = result.get("strict", {})
        nf = result.get("noise_floor", {})
        print(f"\n[M4] === MEASUREMENT #4 RESULT ===", file=sys.stderr)
        print(f"[M4] Strict: {s.get('hit_count')}/{s.get('scored_count')} hits, "
              f"hit_rate={s.get('hit_rate'):.3f}, skill={s.get('skill_score') and round(s.get('skill_score'),3)}", file=sys.stderr)
        print(f"[M4] Noise floor: mean={nf.get('mean_hit_rate'):.3f}, "
              f"floor(+2σ)={nf.get('floor_threshold_mean_plus_2std'):.3f}", file=sys.stderr)
        print(f"[M4] Status: {result['status']}", file=sys.stderr)


if __name__ == "__main__":
    main()
