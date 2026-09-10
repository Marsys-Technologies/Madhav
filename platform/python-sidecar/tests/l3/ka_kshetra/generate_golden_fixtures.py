"""
tests/l3/ka_kshetra/generate_golden_fixtures.py
SAMPŪRTI-Δ2 V1: generate frozen sampled-engine snapshots.

Run from the python-sidecar root:

    python3 tests/l3/ka_kshetra/generate_golden_fixtures.py

This script uses the engine IN-PROCESS (no DB, no IO, no RNG) and writes:

    tests/l3/ka_kshetra/golden_fixtures/sampled_engine_v1_fixtures.json

The JSON is the FROZEN ground truth for parity testing.  When the analytic
DHĀRĀ engine is built, its outputs are compared against these values.

── FIXTURE MATRIX ────────────────────────────────────────────────────────────
  Charts  : native (482012f1-…), abhinandan (abhinandan-1c826d5a)
  Classes : career_change, marriage, relocation, rare_event (ClassSkipped edge),
            career_change_zw (zero-clock edge)
  Decades : 0 = [0, 3650], 1 = [3650, 7300], 2 = [7300, 10950]

Edge cases included:
  • suppression_active — vedha splits the strong contact hump in decade 1,
    producing a window whose peak sits INSIDE the vedha's active range,
    giving is_suppression_active=True on that window's entry.
  • empty_class (rare_event) — no lifetime prior → ClassSkipped (skipped=True)
  • zero_weight_clocks — all w_s=0 → zero_weight_clocks=True in metadata

── SUPPRESSION DESIGN ────────────────────────────────────────────────────────
For decade 1, a very strong contact hump (beta:x1=1.2, contact amplitude=1.0)
is placed at the decade midpoint.  A vedha obstruction is embedded inside
the hump with rho:vedha=0.6.  The suppression creates a local λ-dip that
SPLITS the big window into three sub-windows; the central sub-window's peak
(at the vedha centre, where it is still above q_threshold because the hump is
strong) has active obstruction → is_suppression_active=True.

── PURITY ────────────────────────────────────────────────────────────────────
NO DB.  NO IO DURING EVALUATION.  NO RNG.  The engine is pure Python; this
script builds its inputs synthetically following the same pattern as the
existing tests/l3/ka_kshetra/test_stage4_field.py helper.

Authority: SAMPŪRTI-Δ2 task brief; KALA_W2_FIELD_DESIGN_v1_0.md §5.1–§5.5.
"""
from __future__ import annotations

import datetime
import json
import math
import sys
from pathlib import Path
from typing import Any, Optional

# Make the sidecar root importable.
_SIDECAR_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_SIDECAR_ROOT))

from services.ka_kshetra import integrator as I, stage5_null as S5
from services.ka_kshetra.contracts import ClockApplicability, PromisePrior, Route
from services.ka_kshetra.stage4_field import (
    ClassSkipped, EnvelopeIndex, FieldEvaluator, LadderPeriod, Primitive,
)

_OUT_DIR = Path(__file__).parent / 'golden_fixtures'
_OUT_FILE = _OUT_DIR / 'sampled_engine_v1_fixtures.json'

# ── constants ─────────────────────────────────────────────────────────────────

ENGINE = 'sampled'
ENGINE_VERSION = 3

# Three 10-year decade windows (in days from birth).
DECADES = [
    (0, 0, 3650),
    (1, 3650, 7300),
    (2, 7300, 10950),
]

# The two canonical chart_ids.
NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
ABHINANDAN_CHART_ID = 'abhinandan-1c826d5a'

# null replicate count (matches stage5_null.DEFAULT_REPLICATES = 256).
NULL_REPLICATES = 256

# Horizon for all field evaluators in this fixture set.
# 10950 days = 30 years — wide enough to cover all 3 decades.
HORIZON_DAYS = 10950.0

# Lifetime counts per class (events per century).
LIFETIME_COUNTS = {
    'career_change': 3.0,
    'marriage': 1.5,
    'relocation': 4.0,
}

# ── helpers: synthetic inputs ─────────────────────────────────────────────────

def _route(event_class: str, lord: str = 'Ju', gain: float = 0.65) -> Route:
    return Route(
        event_class=event_class,
        route_rank=1,
        path_node_ids=(f'graha:{lord}', 'bhava:10', f'event_class:{event_class}'),
        path_edge_ids=(),
        route_gain=gain,
        is_primary=True,
    )


def _prim(kind: str, subject: str, knots, polarity: str = 'supportive',
          object_ref: Optional[str] = None, class_label: Optional[str] = None) -> Primitive:
    return Primitive(
        primitive_kind=kind, subject=subject, object_ref=object_ref,
        polarity=polarity, class_label=class_label,
        knots=tuple((float(t), float(v)) for t, v in knots),
    )


def _vimshottari_ladder() -> list[LadderPeriod]:
    """Synthetic Vimshottari MD ladder covering the full horizon."""
    lords = ['Ju', 'Sa', 'Me', 'Mo', 'Su', 'Ma', 'Ra', 'Ke', 'Ve']
    step = HORIZON_DAYS / len(lords)
    return [
        LadderPeriod('vimshottari', 'MD', lord, i * step, (i + 1) * step)
        for i, lord in enumerate(lords)
    ]


def _yogini_ladder() -> list[LadderPeriod]:
    """Synthetic Yogini MD ladder covering the full horizon."""
    lords = ['Ju', 'Sa', 'Me', 'Mo', 'Su', 'Ma', 'Ra', 'Ke']
    step = HORIZON_DAYS / len(lords)
    return [
        LadderPeriod('yogini', 'MD', lord, i * step, (i + 1) * step)
        for i, lord in enumerate(lords)
    ]


# Shared ladder (both systems, full-horizon) — built once.
_SHARED_LADDER = {
    'vimshottari': _vimshottari_ladder(),
    'yogini': _yogini_ladder(),
}

# Shared clock descriptors (two applicable, predictive systems).
_STANDARD_CLOCKS = [
    ClockApplicability('vimshottari', 'applicable', 'fruition', 1, True, 0.88),
    ClockApplicability('yogini', 'applicable', 'flavour', 2, True, 0.72),
]

# Standard weights (classical v0 with fitted betas that produce visible windows).
#
# beta:x1=2.0, rho:vedha=0.5 chosen so that the narrow humps inside the vedha
# zone still exceed q_threshold after suppression.  Derivation:
#   lam_suppressed = lam_base * (1 - rho * u) = lam_base * (1 - 0.5 * 0.85) = lam_base * 0.575
#   q_threshold (256 replicates) ≈ 1.3e-4
#   lam_base at narrow hump peak (amplitude=1.0, beta:x1=2.0) ≈ 3.5e-4
#   lam_suppressed ≈ 2.0e-4 > 1.3e-4  ✓
# Verified empirically: produces 2 suppressed windows, both above q_threshold.
_STANDARD_WEIGHTS = {
    'w_s:vimshottari': 1.0,
    'w_s:yogini': 0.6,
    'beta:x1': 2.0,   # strong Moon-ref weight — must survive suppression above q
    'beta:x2': 0.6,   # Lagna-ref covariate weight
    'd:MD': 1.0,
    'd:AD': 0.7,
    'd:PD': 0.5,
    'd:SD': 0.3,
    'd:PrD': 0.15,
    'rho:vedha': 0.5,   # 0.5 → S=(1-0.5*0.85)=0.575, mild suppression → sub-windows survive
    'rho:default': 0.25,
}

# Zero-clock weights — all w_s set to 0.  All other weights identical to standard.
_ZERO_CLOCK_WEIGHTS = {**_STANDARD_WEIGHTS, 'w_s:vimshottari': 0.0, 'w_s:yogini': 0.0}


# ── evaluator builders ────────────────────────────────────────────────────────

def _build_evaluator(
    event_class: str,
    *,
    with_suppression: bool = False,
    zero_weight_clocks: bool = False,
) -> FieldEvaluator:
    """
    Build a FieldEvaluator for the given event class.

    Standard (no suppression):
      One wide Moon-ref hump per decade, centred at the decade midpoint,
      amplitude=1.0, ±300 days.  The strong beta:x1=1.5 weight ensures
      every hump clears the q_threshold comfortably → one window per decade.

    Suppression scenario (with_suppression=True):
      The decade-1 hump is replaced by TWO narrow humps (±80 days each)
      embedded inside a wide vedha obstruction zone [5300, 5650].
      Vedha rho=0.6 suppresses both humps but they still exceed q_threshold
      because beta:x1=1.5 and amplitude=1.0 keep λ above the null's 95th
      percentile.  The window finder identifies each narrow hump as an
      independent window whose t_peak (= 5380 and 5570) sits INSIDE the
      active vedha zone → is_suppression_active=True on those entries.

    Design rationale for the suppression layout:
      A vedha that covers the FULL width of a hump pushes the hump's peak
      below q_threshold, eliminating the window.  A vedha that is NARROWER
      than the hump produces sub-windows whose peaks are at the boundary of
      the vedha, where u=0 → no obstruction.  The correct design places the
      vedha WIDER than the contact humps so that every breakpoint of each
      narrow hump falls inside the uniformly-suppressed zone — the sub-window
      peaks then have full vedha activity (u=0.85).

    zero_weight_clocks:
      All w_s=0; the clock-log factor collapses to 1 everywhere.  Promise
      and covariate terms still lift λ above the baseline, so windows still
      appear but are weaker (no clock boost).
    """
    routes = (_route(event_class),)
    promise = PromisePrior(
        p=0.55, routes=routes, n_routes=1,
        fact_ids=(f'fact:p:{event_class}',),
    )
    weights = _ZERO_CLOCK_WEIGHTS if zero_weight_clocks else _STANDARD_WEIGHTS

    # Decade midpoints (days from birth).
    D0_MID, D1_MID, D2_MID = 1825.0, 5475.0, 9125.0
    ORB_WIDE = 300.0    # wide hump for decades 0 and 2
    ORB_NARROW = 80.0   # narrow humps for the suppression sub-windows

    primitives: list[Primitive] = []

    # ── decade 0 hump ─────────────────────────────────────────────────────────
    primitives.append(_prim('contact_moon_ref', 'Ju', [
        (D0_MID - ORB_WIDE, 0.0), (D0_MID, 1.0), (D0_MID + ORB_WIDE, 0.0),
    ]))

    # ── decade 1 hump(s) ──────────────────────────────────────────────────────
    if with_suppression:
        # Two narrow humps (h1, h2) inside the vedha zone [5300, 5650].
        # h1=5380 and h2=5570 are each ±80 days wide, keeping their full
        # extents [5300,5460] and [5490,5650] inside the vedha plateau.
        H1, H2 = 5380.0, 5570.0
        VEDHA_LO, VEDHA_HI = 5300.0, 5650.0

        primitives.append(_prim('contact_moon_ref', 'Ju', [
            (H1 - ORB_NARROW, 0.0), (H1, 1.0), (H1 + ORB_NARROW, 0.0),
        ]))
        primitives.append(_prim('contact_moon_ref', 'Ju', [
            (H2 - ORB_NARROW, 0.0), (H2, 1.0), (H2 + ORB_NARROW, 0.0),
        ]))
        # Wide vedha: plateau u=0.85 covers both humps end-to-end.
        primitives.append(_prim(
            'vedha', 'Sa',
            [
                (VEDHA_LO, 0.0),
                (VEDHA_LO + 50.0, 0.85),
                (VEDHA_HI - 50.0, 0.85),
                (VEDHA_HI, 0.0),
            ],
            polarity='obstructive',
            object_ref='10',
        ))
    else:
        # Single wide hump, no suppression.
        primitives.append(_prim('contact_moon_ref', 'Ju', [
            (D1_MID - ORB_WIDE, 0.0), (D1_MID, 1.0), (D1_MID + ORB_WIDE, 0.0),
        ]))

    # ── decade 2 hump ─────────────────────────────────────────────────────────
    primitives.append(_prim('contact_moon_ref', 'Ju', [
        (D2_MID - ORB_WIDE, 0.0), (D2_MID, 1.0), (D2_MID + ORB_WIDE, 0.0),
    ]))

    envelopes = EnvelopeIndex(primitives, horizon_days=HORIZON_DAYS)

    return FieldEvaluator(
        event_class=event_class,
        lifetime_count=LIFETIME_COUNTS[event_class],
        promise=promise,
        clocks=_STANDARD_CLOCKS,
        ladder=_SHARED_LADDER,
        envelopes=envelopes,
        weights=weights,
        horizon_days=HORIZON_DAYS,
        baseline_source=(
            'brahma_class_priors',
            'ne_v01|*|*',
            f'fact:baseline:{event_class}',
        ),
    )


# ── fixture capture ───────────────────────────────────────────────────────────

def _capture_fixture(
    chart_id: str,
    event_class: str,
    decade_index: int,
    decade_start: float,
    decade_end: float,
    ev: FieldEvaluator,
    *,
    zero_weight_clocks: bool = False,
) -> dict[str, Any]:
    """Run the engine over the full horizon; extract decade-slice results."""

    # Build the full-horizon field segments (sampled engine = §5.2 log-linear).
    segments = ev.build_segments()

    # Run the circular-shift null (R=256, full horizon).
    null_result = S5.run_null(ev, horizon_days=HORIZON_DAYS, replicates=NULL_REPLICATES)
    q_threshold = null_result.q_threshold

    # Find all windows on the full horizon, then filter to this decade window.
    all_windows: list[I.Window] = []
    if q_threshold is not None and q_threshold > 0.0:
        all_windows = I.find_windows(segments, q_threshold)

    decade_windows = [
        w for w in all_windows
        if w.t_end > decade_start and w.t_start < decade_end
    ]

    # Per-window capture (including suppression flag).
    window_entries = []
    for w in decade_windows:
        obs = ev.envelopes.obstructions_at(w.t_peak)
        is_suppression_active = len(obs) > 0
        window_entries.append({
            'window_start': w.t_start,
            'window_end': w.t_end,
            'peak_days': w.t_peak,
            'expected_count': w.expected_count,
            'is_suppression_active': is_suppression_active,
        })

    # Peak ln_lambda inside the decade window (evaluated at breakpoints).
    decade_bps = [
        t for t in ev.breakpoints()
        if decade_start <= t <= decade_end
    ]
    if not decade_bps:
        decade_bps = [decade_start, 0.5 * (decade_start + decade_end), decade_end]
    ln_lambda_at_peak = max(ev.ln_lambda(t) for t in decade_bps)

    # Null stats summary: use the 30-day bucket (mid-range scale).
    # We store ALL 256 max-stats values for that bucket so the analytic
    # engine can recompute rank / p exactly on the same distribution.
    SUMMARY_BUCKET = 30
    bucket_stats: list[float] = null_result.max_stats.get(SUMMARY_BUCKET, [])

    decade_integral = I.integrate(segments, decade_start, decade_end)
    rank_of_real = sum(1 for m in bucket_stats
                       if m >= decade_integral * (1.0 - 1e-12))
    p_value = S5.null_p(bucket_stats, decade_integral) if bucket_stats else None

    return {
        'chart_id': chart_id,
        'event_class': event_class,
        'decade_index': decade_index,
        'decade_start_days': int(decade_start),
        'decade_end_days': int(decade_end),
        'engine': ENGINE,
        'engine_version': ENGINE_VERSION,
        'zero_weight_clocks': zero_weight_clocks,
        'windows': window_entries,
        'null_stats': {
            'replicate_count': NULL_REPLICATES,
            'rank_of_real': rank_of_real,
            'p_value': p_value,
            'null_expected_counts': bucket_stats,
        },
        'segment_count': len(segments),
        'ln_lambda_at_peak': ln_lambda_at_peak,
    }


def _capture_skipped(
    chart_id: str,
    event_class: str,
    decade_index: int,
    decade_start: float,
    decade_end: float,
    reason: str,
) -> dict[str, Any]:
    """Fixture entry for a ClassSkipped scenario (no prior → no field rows)."""
    return {
        'chart_id': chart_id,
        'event_class': event_class,
        'decade_index': decade_index,
        'decade_start_days': int(decade_start),
        'decade_end_days': int(decade_end),
        'engine': ENGINE,
        'engine_version': ENGINE_VERSION,
        'skipped': True,
        'skip_reason': reason,
        # Required structural keys — all null/empty for a skipped class.
        'windows': [],
        'null_stats': {
            'replicate_count': NULL_REPLICATES,
            'rank_of_real': None,
            'p_value': None,
            'null_expected_counts': [],
        },
        'segment_count': 0,
        'ln_lambda_at_peak': None,
    }


# ── main generation loop ──────────────────────────────────────────────────────

def generate() -> dict[str, Any]:
    """Build the full fixture matrix and return the JSON-serializable dict."""
    fixtures: dict[str, Any] = {}

    print('Generating golden fixtures ...')

    for chart_id in [NATIVE_CHART_ID, ABHINANDAN_CHART_ID]:
        chart_short = chart_id[:12]

        # Build evaluators ONCE per class (they are horizon-wide, not per decade).
        evaluators: dict[str, FieldEvaluator] = {}
        evaluators_sup: dict[str, FieldEvaluator] = {}   # suppression variants
        for ec in ['career_change', 'marriage', 'relocation']:
            evaluators[ec] = _build_evaluator(ec, with_suppression=False)
            evaluators_sup[ec] = _build_evaluator(ec, with_suppression=True)

        # ── 3 classes × 3 decades ─────────────────────────────────────────────
        for event_class in ['career_change', 'marriage', 'relocation']:
            for decade_index, decade_start, decade_end in DECADES:
                # Decade 1 uses the suppression evaluator so that decade 1's
                # contact hump carries an embedded vedha → is_suppression_active.
                use_suppression = (decade_index == 1)
                ev = evaluators_sup[event_class] if use_suppression else evaluators[event_class]
                sup_label = ' +suppression' if use_suppression else ''
                print(f'  {chart_short} / {event_class} / decade={decade_index}{sup_label} ...')
                entry = _capture_fixture(
                    chart_id, event_class, decade_index,
                    decade_start, decade_end, ev,
                )
                key = f'{chart_id}:{event_class}:{decade_index}'
                fixtures[key] = entry

        # ── edge case: empty class (ClassSkipped) ─────────────────────────────
        # 'rare_event' has no lifetime-count prior → §5.1 C-1 ClassSkipped.
        for decade_index, decade_start, decade_end in DECADES:
            key = f'{chart_id}:rare_event:{decade_index}'
            print(f'  {chart_short} / rare_event (ClassSkipped) / decade={decade_index} ...')
            fixtures[key] = _capture_skipped(
                chart_id, 'rare_event', decade_index,
                decade_start, decade_end,
                reason='no_class_prior_row',
            )

        # ── edge case: zero-weight clocks ─────────────────────────────────────
        # career_change, decade 0, all w_s=0.
        ec = 'career_change'
        decade_index, decade_start, decade_end = DECADES[0]
        key = f'{chart_id}:career_change_zw:{decade_index}'
        print(f'  {chart_short} / career_change_zw (zero-clock) / decade={decade_index} ...')
        ev_zw = _build_evaluator(ec, zero_weight_clocks=True)
        entry_zw = _capture_fixture(
            chart_id, ec, decade_index,
            decade_start, decade_end, ev_zw,
            zero_weight_clocks=True,
        )
        fixtures[key] = entry_zw

    # Verify edge cases are present before writing.
    _verify_edge_cases(fixtures)

    meta = {
        'engine': ENGINE,
        'engine_version': ENGINE_VERSION,
        'generator': 'tests/l3/ka_kshetra/generate_golden_fixtures.py',
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'null_replicates': NULL_REPLICATES,
        'horizon_days': HORIZON_DAYS,
        'charts': [NATIVE_CHART_ID, ABHINANDAN_CHART_ID],
        'event_classes': ['career_change', 'marriage', 'relocation'],
        'decade_windows': [list(d) for d in DECADES],
        'edge_cases': ['suppression_active', 'empty_class', 'zero_weight_clocks'],
    }

    return {'meta': meta, 'fixtures': fixtures}


def _verify_edge_cases(fixtures: dict[str, Any]) -> None:
    """Fail loudly if any required edge case is missing."""
    all_entries = list(fixtures.values())

    # suppression_active
    has_suppression = any(
        w.get('is_suppression_active') is True
        for f in all_entries
        if not f.get('skipped')
        for w in f.get('windows', [])
    )
    if not has_suppression:
        raise RuntimeError(
            'BUG: no window with is_suppression_active=True generated. '
            'Adjust the suppression hump amplitude or rho so the vedha-centre '
            'sub-window peak still exceeds q_threshold.'
        )

    # empty_class
    has_skipped = any(f.get('skipped') is True for f in all_entries)
    if not has_skipped:
        raise RuntimeError('BUG: no ClassSkipped (skipped=True) entry generated.')

    # zero_weight_clocks
    has_zw = any(
        f.get('zero_weight_clocks') is True
        for f in all_entries
        if not f.get('skipped')
    )
    if not has_zw:
        raise RuntimeError('BUG: no zero_weight_clocks=True entry generated.')

    print('Edge-case verification PASSED.')


def _json_default(obj: Any) -> Any:
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    raise TypeError(f'Object of type {type(obj).__name__} is not JSON serializable')


def main() -> None:
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    data = generate()

    with open(_OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=_json_default, ensure_ascii=False)

    n_fixtures = len(data['fixtures'])
    n_skipped = sum(1 for v in data['fixtures'].values() if v.get('skipped'))
    n_suppression_windows = sum(
        1 for v in data['fixtures'].values()
        if not v.get('skipped')
        for w in v.get('windows', [])
        if w.get('is_suppression_active')
    )
    n_zero_clock = sum(
        1 for v in data['fixtures'].values()
        if v.get('zero_weight_clocks') and not v.get('skipped')
    )

    print()
    print(f'Wrote {_OUT_FILE}')
    print(f'  {n_fixtures} total fixture entries')
    print(f'  {n_skipped} ClassSkipped (empty-class) entries')
    print(f'  {n_suppression_windows} windows with is_suppression_active=True')
    print(f'  {n_zero_clock} zero-weight-clock entries')


if __name__ == '__main__':
    main()
