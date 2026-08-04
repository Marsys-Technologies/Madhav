#!/usr/bin/env python3
"""
dryrun_skill_gof_synthetic.py — end-to-end SYNTHETIC dry-run of the
`mi_bhara` skill-score + goodness-of-fit harness (ṢAḌ-DARŚANA W2 §7.3),
staged ahead of SESSION-A-SWEEP's SWEEPS-COMPLETE signal.

────────────────────────────────────────────────────────────────────────────
WHY SYNTHETIC, AND WHY NOW
────────────────────────────────────────────────────────────────────────────
The real skill score / GOF publish needs a real `ka_kshetra` field build on
both canonical charts, which needs the real gochara sweep, which is
SESSION-A-SWEEP's exclusive territory and is not complete yet
(`SHAD_DARSHANA_STATE.md` NEXT-ACTION: 482012f1 495/606, 1c826d5a 463/606 at
last check). This script does NOT wait for that, and does NOT touch any
real chart, field, or sweep data — it exercises the harness's own PURE
functions (`services/mi_bhara/skill.py::compute_skill` /
`aggregate_chart_skill`, `services/mi_bhara/gof.py::compute_gof`) against a
hand-fabricated synthetic point process, so a future session can confirm —
in seconds, with no DB and no field build — that the harness itself still
runs end-to-end without errors before spending the hours needed for the
real thing.

This is deliberately NOT a substitute for the real skill-score/GOF publish.
It proves the HARNESS works; it says nothing about the FIELD's actual skill
(a synthetic process has no relationship to the native's chart). Per
CLAUDE.md §N.8, a green run of this script is evidence the code path is
live, not evidence of anything astrological.

The unit test suites already dry-run these same functions on synthetic
fixtures (`tests/l5/test_mi_bhara_skill.py`, `tests/l5/test_mi_bhara_gof.py`
— 30 cases, run via `pytest`); this script is a standalone, human-readable
companion that exercises the SAME two functions end-to-end in one flow
(skill AND gof, single-class AND chart-level aggregate) and prints a
report, so a Conductor/Verifier session can eyeball a concrete before/after
example rather than reading pytest's dot output.

────────────────────────────────────────────────────────────────────────────
WHAT IT FABRICATES
────────────────────────────────────────────────────────────────────────────
Two synthetic event classes over a 1000-day observation window:
  * "signal_class"  — model log-intensity has a deliberate, decaying bump
    around real "event" times, i.e. the model should have REAL skill against
    a flat null (SS > 0 expected).
  * "noise_class"   — model log-intensity is statistically indistinguishable
    from the null replicates (SS ≈ 0 expected, `not_established`).
Both are deterministic (fixed seed), so a rerun reproduces the exact same
report — mirroring the real harness's own determinism discipline
(`services/mi_bhara/skill.py`'s `bootstrap_seed`).

────────────────────────────────────────────────────────────────────────────
USAGE
────────────────────────────────────────────────────────────────────────────
    python3 scripts/dryrun_skill_gof_synthetic.py
    python3 scripts/dryrun_skill_gof_synthetic.py --json   # machine-readable report

Exit codes:
    0 — the harness ran end-to-end with no exceptions (regardless of the
        synthetic scores it produced — this script is a SMOKE TEST, not a
        pass/fail judgment on synthetic data)
    1 — the harness raised an exception; the dry-run itself FAILED
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from services.mi_bhara.gof import compute_gof  # noqa: E402
from services.mi_bhara.skill import aggregate_chart_skill, compute_skill  # noqa: E402

SYNTHETIC_CHART_ID = "00000000-synthetic-dryrun-0000-000000000000"
SYNTHETIC_WEIGHTS_VERSION = "v0_classical_dryrun"
OBSERVATION_WINDOW_DAYS = 1000.0
N_NULL_REPLICATES = 256  # matches kala_field_null.replicates at W2 (design §5.5)
RNG_SEED = 20260805  # fixed — this script's own determinism, unrelated to the real chart


def _fabricate_signal_class(rng: np.random.Generator) -> dict[str, Any]:
    """A class whose model genuinely explains its events better than a flat null:
    events are placed near three 'promise' epochs, and the model log-intensity
    is a decaying bump around each epoch while the null (§5.5's circular-shift
    replicate — SAME total marginal rate, i.e. same Λ, only WHEN differs) is
    flat. Calibrated so `Λ_model ≈ Λ_null ≈ n_events` (a properly normalized
    process predicts roughly as many events as actually occurred) — a model
    whose absolute rate is merely miscalibrated, even with the right shape,
    is not what 'skill' means here; skill is about WHEN, not how many.
    """
    epochs = [180.0, 500.0, 800.0]
    n_events = 18
    # Event times clustered near the epochs (the "real" temporal structure).
    events = np.sort(
        rng.choice(epochs, size=n_events) + rng.normal(0.0, 12.0, size=n_events)
    )
    events = np.clip(events, 1.0, OBSERVATION_WINDOW_DAYS - 1.0)

    baseline = 0.002
    amplitude = 0.13  # chosen so Λ_model over the window ≈ n_events (see integral below)

    def model_log_intensity(t: float) -> float:
        # baseline + a decaying bump near each epoch — this is what should make
        # the model score REAL events (near an epoch) higher than random times.
        bump = sum(math.exp(-((t - e) ** 2) / (2 * 15.0**2)) for e in epochs)
        return math.log(baseline + amplitude * bump)

    model_vals = [model_log_intensity(t) for t in events]

    def integral(a: float, b: float) -> float:
        # closed-form-ish trapezoidal integral of exp(model_log_intensity), fine
        # grid — this is a dry-run fixture, not the real field's analytic segments.
        grid = np.linspace(a, b, max(2, int((b - a) * 4) + 1))
        vals = np.array([math.exp(model_log_intensity(x)) for x in grid])
        return float(np.trapezoid(vals, grid))

    model_integral = integral(0.0, OBSERVATION_WINDOW_DAYS)
    # The null is the SAME total marginal rate (Λ_null == Λ_model, §5.5's "same baseline,
    # same marginal rate, differs only in when") realized as a flat background — flat means
    # no epoch structure, so the null cannot see the clustering the model was built to see.
    flat_null_rate = model_integral / OBSERVATION_WINDOW_DAYS

    def null_log_intensity(_t: float) -> float:
        return math.log(flat_null_rate)

    null_replicates = [
        [null_log_intensity(t) for t in events] for _ in range(N_NULL_REPLICATES)
    ]
    null_integrals = [model_integral for _ in range(N_NULL_REPLICATES)]

    return {
        "event_class": "signal_class",
        "event_times": events.tolist(),
        "model_log_intensity": model_vals,
        "null_log_intensity_per_replicate": null_replicates,
        "model_integral": model_integral,
        "null_integrals": null_integrals,
        "integrate_fn": integral,
    }


def _fabricate_noise_class(rng: np.random.Generator) -> dict[str, Any]:
    """A class with NO real temporal structure: events uniform on the window,
    model and null both flat and statistically identical (up to noise). Expected
    to land `not_established` / GOF `pass` (a flat model correctly fits a flat
    process) — the harness's honest-null path.
    """
    n_events = 12
    events = np.sort(rng.uniform(1.0, OBSERVATION_WINDOW_DAYS - 1.0, size=n_events))
    rate = 0.008

    model_vals = [math.log(rate) for _ in events]
    # null replicates carry the SAME rate plus tiny iid noise, exactly like the
    # model has no informational edge over its own null.
    null_replicates = [
        [math.log(rate) + float(rng.normal(0.0, 1e-3)) for _ in events]
        for _ in range(N_NULL_REPLICATES)
    ]

    def integral(a: float, b: float) -> float:
        return rate * (b - a)

    model_integral = integral(0.0, OBSERVATION_WINDOW_DAYS)
    null_integrals = [model_integral + float(rng.normal(0.0, 1e-3)) for _ in range(N_NULL_REPLICATES)]

    return {
        "event_class": "noise_class",
        "event_times": events.tolist(),
        "model_log_intensity": model_vals,
        "null_log_intensity_per_replicate": null_replicates,
        "model_integral": model_integral,
        "null_integrals": null_integrals,
        "integrate_fn": integral,
    }


def run_dry_run() -> dict[str, Any]:
    rng = np.random.default_rng(RNG_SEED)
    classes = [_fabricate_signal_class(rng), _fabricate_noise_class(rng)]

    per_class_skill = []
    per_class_gof = []
    report_classes: dict[str, Any] = {}

    for c in classes:
        skill = compute_skill(
            chart_id=SYNTHETIC_CHART_ID,
            weights_version=SYNTHETIC_WEIGHTS_VERSION,
            event_class=c["event_class"],
            model_log_intensity=c["model_log_intensity"],
            null_log_intensity_per_replicate=c["null_log_intensity_per_replicate"],
            model_integral=c["model_integral"],
            null_integrals=c["null_integrals"],
        )
        per_class_skill.append(skill)

        gof = compute_gof(
            event_class=c["event_class"],
            integrate_fn=c["integrate_fn"],
            event_times=c["event_times"],
            observation_start=0.0,
        )
        per_class_gof.append(gof)

        report_classes[c["event_class"]] = {
            "n_events": len(c["event_times"]),
            "skill": {
                "score": skill.skill_score,
                "ci_lo": skill.skill_lo,
                "ci_hi": skill.skill_hi,
                "state": skill.skill_state,
            },
            "gof": {
                "n": gof.n,
                "ks_p": gof.ks_p,
                "ljung_box_p": gof.ljung_box_p,
                "state": gof.gof_state,
                "failing_statistic": gof.failing_statistic,
            },
        }

    chart_skill = aggregate_chart_skill(
        per_class_skill,
        chart_id=SYNTHETIC_CHART_ID,
        weights_version=SYNTHETIC_WEIGHTS_VERSION,
    )

    return {
        "harness_ran_end_to_end": True,
        "synthetic_chart_id": SYNTHETIC_CHART_ID,
        "weights_version": SYNTHETIC_WEIGHTS_VERSION,
        "n_null_replicates": N_NULL_REPLICATES,
        "per_class": report_classes,
        "chart_level_skill": {
            "n_events": chart_skill.n_events,
            "score": chart_skill.skill_score,
            "ci_lo": chart_skill.skill_lo,
            "ci_hi": chart_skill.skill_hi,
            "state": chart_skill.skill_state,
        },
        "note": (
            "SYNTHETIC DATA — these numbers describe a fabricated point process, not the "
            "native's chart. This run proves the skill/GOF harness executes end-to-end "
            "(compute_skill, aggregate_chart_skill, compute_gof all completed without "
            "exception); it is not a skill-score publish and satisfies no gate on its own."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="print the raw JSON report only")
    args = parser.parse_args()

    try:
        report = run_dry_run()
    except Exception as exc:  # the one place this script deliberately catches broadly —
        # the whole point is to report a harness-level failure cleanly, not stack-trace it.
        print(f"DRY-RUN FAILED — the skill/GOF harness raised: {exc!r}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("=" * 78)
        print("SKILL-SCORE / GOF HARNESS — SYNTHETIC DRY-RUN")
        print("=" * 78)
        for ec, c in report["per_class"].items():
            print(f"\n[{ec}]  n_events={c['n_events']}")
            print(f"  skill: score={c['skill']['score']:+.4f} "
                  f"CI=[{c['skill']['ci_lo']:+.4f}, {c['skill']['ci_hi']:+.4f}] "
                  f"state={c['skill']['state']}")
            print(f"  gof:   n={c['gof']['n']} ks_p={c['gof']['ks_p']} "
                  f"lb_p={c['gof']['ljung_box_p']} state={c['gof']['state']} "
                  f"failing={c['gof']['failing_statistic']}")
        cs = report["chart_level_skill"]
        print(f"\n[chart-level, event-weighted]  n_events={cs['n_events']} "
              f"score={cs['score']:+.4f} CI=[{cs['ci_lo']:+.4f}, {cs['ci_hi']:+.4f}] "
              f"state={cs['state']}")
        print(f"\n{report['note']}")
        print("\nHARNESS RAN END-TO-END WITHOUT ERRORS.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
