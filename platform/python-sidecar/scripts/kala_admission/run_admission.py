#!/usr/bin/env python3
"""
run_admission.py -- D-3 wave/D-3/ADMIT kernel admission loop.

BRIEF_D3.md §F1: "Kernel admission loop (conductor-run, inherently serial):
T-1/T-4/T-5 currents are IMPLEMENTED in parallel but ADMITTED one at a time:
v1 kernel = dasha-capability steps + slow-transit pulses + SAV potency; each
further current stays only if the T-0 blind-battery score improves. Weights
are earned against lived history, not doctrine."

Stage 0 -- v1 baseline (dasha-lord confluence, T-0's proxy). No admission
decision here; this IS the kernel v1 already ships with.

Stage 1 -- T-4 PERMISSION: try admitting the capability-term gate
(currents.permission_gate_at) as a multiplier on the v1 curve. Admit only if
train_score improves over Stage 0.

Stage 2 -- T-5 TRIGGER: with Stage 1's decision fixed, GRID-SEARCH
TRIGGER_ADDITIVE_WEIGHTS / TRIGGER_SUPPRESSIVE_WEIGHTS (currents.py's two
tunable scalars) over {0.2, 0.4, 0.6, 0.8} x {0.2, 0.4, 0.6, 0.8} = 16
configurations. Admit TRIGGER, at the WEIGHT COMBINATION THAT MAXIMIZES
train_score across the grid, only if that maximum beats Stage 1's score.
This is the step that must satisfy the Adjudicator's falsifier: the loop
searches over weight VALUES, not just a fixed-default on/off toggle.

Scoring (`train_score`), TRAIN-ONLY (see lel.py's circuit-breaker docstring
for the enforcement of this):
  train_score = 0.4 * windfall_pass + 0.6 * blind_battery_hit_rate
  - windfall_pass: the 2010-07-01 finance/family_windfall event (Venus+
    Jupiter dhana-yoga significators), peak-proximity +/-45d, top-decile
    threshold (percentile=0.9) -- same check T-0 ran as check (b).
  - blind_battery_hit_rate: every TRAIN-scorable event (BIND_D-3 §B-3
    scorability rule, ported in lel.py), peak-proximity +/-45d, top-tercile
    threshold (percentile=2/3) -- same check T-0 ran as check (c), just
    scoped to TRAIN.
  Composite weights (0.4/0.6) are a CALIBRATION choice this session makes
  explicitly, not inherited from a ratified prior formula -- documented
  here per CLAUDE.md B.10/B.3 honesty discipline.

NEVER reads/scores the 2025-05-15 loss event or any event >= 2020-01-01 --
lel.py's load_train_events() raises SealedTestSplitViolation if the cache
ever contained one; this script also independently asserts the fact below.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/ -- so `kala_admission` is importable as a package

from kala_admission.checks import score_event_curve  # noqa: E402
from kala_admission.currents import (  # noqa: E402
    CurrentsConfig,
    TRIGGER_ADDITIVE_WEIGHTS_DEFAULT,
    TRIGGER_SUPPRESSIVE_WEIGHTS_DEFAULT,
    make_candidate_curve_builder,
)
from kala_admission.dasha_periods import load_dasha_lord_capability, load_dasha_periods  # noqa: E402
from kala_admission.dates import parse_date  # noqa: E402
from kala_admission.lel import TEST_SPLIT_BOUNDARY, load_train_events, partition_scorable  # noqa: E402
from kala_admission.mechanisms import WINDFALL_SIGNIFICATORS, significators_for_category  # noqa: E402

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
WINDFALL_EVENT_ID = "bd7f5711-8668-5315-8e25-94dc94f2a101"
LOSS_EVENT_ID_SEALED = "d81fae4e-edf4-58d9-b201-cced7eae19d7"  # 2025-05-15 -- MUST NEVER appear in this script's data
BOUNDS_START = parse_date("1984-02-05")
BOUNDS_END = parse_date("2022-06-01")  # matches cache/dasha_periods.json's fetched window
WEIGHT_GRID = [0.2, 0.4, 0.6, 0.8]
WINDFALL_WEIGHT = 0.4
BLIND_BATTERY_WEIGHT = 0.6


@dataclass
class ConfigResult:
    label: str
    permission_admitted: bool
    trigger_admitted: bool
    trigger_additive_weight: float | None
    trigger_suppressive_weight: float | None
    windfall_pass: bool
    windfall_peak_lag_days: int | None
    blind_battery_hit_rate: float
    blind_battery_hit_count: int
    blind_battery_scored_count: int
    train_score: float


def score_config(
    periods, lord_capability, scorable_events, windfall_event, config: CurrentsConfig
) -> ConfigResult:
    # ── Windfall check (top-decile, +/-45d) ──
    windfall_curve_builder = make_candidate_curve_builder(
        periods, WINDFALL_SIGNIFICATORS, lord_capability, config
    )
    windfall_score = score_event_curve(
        windfall_curve_builder,
        windfall_event.event_id,
        windfall_event.event_date,
        BOUNDS_START,
        BOUNDS_END,
        percentile=0.9,
    )

    # ── Blind battery (top-tercile, +/-45d, every TRAIN-scorable event) ──
    per_event_hits = 0
    for e in scorable_events:
        sig = significators_for_category(e.category)
        cb = make_candidate_curve_builder(periods, sig, lord_capability, config)
        s = score_event_curve(cb, e.event_id, e.event_date, BOUNDS_START, BOUNDS_END, percentile=2.0 / 3.0)
        if s.passed:
            per_event_hits += 1
    hit_rate = per_event_hits / len(scorable_events) if scorable_events else 0.0

    train_score = WINDFALL_WEIGHT * float(windfall_score.passed) + BLIND_BATTERY_WEIGHT * hit_rate

    label_parts = [f"perm={'on' if config.permission_admitted else 'off'}"]
    if config.trigger_admitted:
        label_parts.append(
            f"trig=on(add={config.trigger_additive_weight},sup={config.trigger_suppressive_weight})"
        )
    else:
        label_parts.append("trig=off")

    return ConfigResult(
        label=" ".join(label_parts),
        permission_admitted=config.permission_admitted,
        trigger_admitted=config.trigger_admitted,
        trigger_additive_weight=config.trigger_additive_weight if config.trigger_admitted else None,
        trigger_suppressive_weight=config.trigger_suppressive_weight if config.trigger_admitted else None,
        windfall_pass=windfall_score.passed,
        windfall_peak_lag_days=windfall_score.peak_lag_days,
        blind_battery_hit_rate=round(hit_rate, 4),
        blind_battery_hit_count=per_event_hits,
        blind_battery_scored_count=len(scorable_events),
        train_score=round(train_score, 4),
    )


def main() -> None:
    events = load_train_events()  # raises SealedTestSplitViolation if contaminated -- see lel.py
    for e in events:
        assert e.event_date < TEST_SPLIT_BOUNDARY, "unreachable -- load_train_events() already enforces this"
        assert e.event_id != LOSS_EVENT_ID_SEALED, "unreachable -- the sealed loss event is TEST, never in TRAIN cache"

    scorable, excluded = partition_scorable(events)
    windfall_event = next(e for e in events if e.event_id == WINDFALL_EVENT_ID)
    assert windfall_event.event_date < TEST_SPLIT_BOUNDARY

    periods = load_dasha_periods()
    lord_capability = load_dasha_lord_capability()["lords"]

    search_table: list[ConfigResult] = []

    # ── Stage 0: v1 baseline ──
    stage0_config = CurrentsConfig(permission_admitted=False, trigger_admitted=False)
    stage0 = score_config(periods, lord_capability, scorable, windfall_event, stage0_config)
    search_table.append(stage0)

    # ── Stage 1: try admitting PERMISSION ──
    stage1_config = CurrentsConfig(permission_admitted=True, trigger_admitted=False)
    stage1 = score_config(periods, lord_capability, scorable, windfall_event, stage1_config)
    search_table.append(stage1)

    permission_admitted = stage1.train_score > stage0.train_score
    active_baseline = stage1 if permission_admitted else stage0

    # ── Stage 2: grid-search TRIGGER weights, with Stage 1's decision fixed ──
    stage2_results: list[ConfigResult] = []
    for add_w in WEIGHT_GRID:
        for sup_w in WEIGHT_GRID:
            cfg = CurrentsConfig(
                permission_admitted=permission_admitted,
                trigger_admitted=True,
                trigger_additive_weight=add_w,
                trigger_suppressive_weight=sup_w,
            )
            r = score_config(periods, lord_capability, scorable, windfall_event, cfg)
            stage2_results.append(r)
    search_table.extend(stage2_results)

    best_trigger = max(stage2_results, key=lambda r: r.train_score)
    trigger_admitted = best_trigger.train_score > active_baseline.train_score

    final = best_trigger if trigger_admitted else active_baseline

    report = {
        "harness": "kala_admission_loop",
        "wave": "D-3",
        "lane": "ADMIT",
        "chart_id": CHART_ID,
        "test_split_boundary": TEST_SPLIT_BOUNDARY.isoformat(),
        "sealed_loss_event_id_never_used": LOSS_EVENT_ID_SEALED,
        "train_events_used_count": len(events),
        "train_events_scorable_count": len(scorable),
        "train_events_excluded_from_blind_battery": [
            {"event_id": e.event_id, "event_date": e.event_date.isoformat(), "reasons": reasons}
            for e, reasons in excluded
        ],
        "all_train_event_ids_and_dates": [
            {"event_id": e.event_id, "event_date": e.event_date.isoformat()} for e in events
        ],
        "windfall_event": {"event_id": windfall_event.event_id, "event_date": windfall_event.event_date.isoformat()},
        "trigger_weight_defaults_imported_from_trigger_py": {
            "additive": TRIGGER_ADDITIVE_WEIGHTS_DEFAULT,
            "suppressive": TRIGGER_SUPPRESSIVE_WEIGHTS_DEFAULT,
        },
        "weight_grid_searched": WEIGHT_GRID,
        "search_table": [asdict(r) for r in search_table],
        "admission_decision": {
            "stage0_v1_baseline_train_score": stage0.train_score,
            "stage1_permission_train_score": stage1.train_score,
            "permission_admitted": permission_admitted,
            "stage2_best_trigger_config": asdict(best_trigger),
            "trigger_admitted": trigger_admitted,
            "final_train_score": final.train_score,
            "final_train_score_delta_vs_v1_baseline": round(final.train_score - stage0.train_score, 4),
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
