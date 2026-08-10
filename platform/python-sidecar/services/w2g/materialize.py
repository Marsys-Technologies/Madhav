"""W2G — the per-chart materialization layer: contact stream + natal points -> served rows.

WHAT THIS MODULE IS. The join step design §2's architecture description calls
"chart-SPECIFIC contact events (per chart, cheap)": take the chart-INDEPENDENT
contact stream (`bg_gochara_arcs`, read via `services.w2g.solver.ContactSolver`)
and a chart's own natal resonance-map targets
(`gochara_grammar.resonance_map.fetch_resonance_targets`), and produce
`kala_gochara_windows`-shaped rows.

WHAT THIS MODULE DELIBERATELY REUSES, UNCHANGED (design §5 — "2.0 changes HOW,
never WHAT"; no new astrology in this wave): the scoring itself is v1's own
`gochara_intensity.compute_lambda_e` (PROMISE x PERMISSION x exp(beta*X) -
suppression), v1's own `gochara_intensity.enrichment.enrich_targets`, and v1's
own row-serialization helper (`ka_gochara_sweep.shape_output._serialize_result`)
and active-sentence re-gather helper
(`ka_gochara_sweep.sweep._gather_active_sentences_at`). Nothing here reimplements
grammar, orb policy, PROMISE/PERMISSION/suppression, or valence — importing and
calling the frozen v1 functions IS the "changes HOW never WHAT" discipline, not
a description of it.

WHAT ACTUALLY CHANGES: v1 finds "which dates matter" by stepping a daily grid
and asking `compute_lambda_e` at every single day (~36,500 candidate days for a
full century). 2.0 finds "which dates matter" by asking the arc substrate for
the EXACT dates a transiting body reaches a natal degree (a handful of contacts
per target per body, not one evaluation per day) and only then calls the same
`compute_lambda_e` at those exact instants. Fewer, exact evaluations of an
unchanged scoring function — a different sampling shape, not a different
answer.

HONEST SCOPE OF THIS FIRST LANE (disclosed here, not just in the PR body):
  * Only `temporal_shape == 'point'` event classes are materialized.
    `interval`/`chain` shapes need v1's segment-consolidation machinery
    (`shape_output.build_interval_segments` + `writer.py`'s DB-driven
    continuity chaining) which is NOT reused here — a future lane's job.
    `materialize_event_class` returns an honest empty list with a `skipped`
    reason for those classes rather than fabricating a shape it does not
    implement.
  * Candidate-date discovery only covers TARGETS WITH A RESOLVED EXACT DEGREE
    (`target_longitude_deg is not None` after `enrich_targets` — karaka/lord/
    dasha_lord_portfolio grahas, sensitive degrees). A `bhava`-type target
    resolves only a natal SIGN (`enrichment.enrich_target`), not an exact
    degree, so there is no single point on the ecliptic to root-find against;
    such targets are honestly excluded from candidate discovery. They are NOT
    excluded from SCORING — `compute_lambda_e` re-fetches the full target set
    for PROMISE/PERMISSION, so a candidate date found via a degree-resolved
    target still scores correctly against the whole picture.
  * Candidate discovery uses ONLY Tier A (eager) bodies by default
    (ADJUDICATION-14) — Tier B/C (conditional/lazy) are a documented future
    extension, not silently dropped forever.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Optional, Sequence

from services.gochara_grammar import dasha_data as DD
from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar.models import ResonanceTarget
from services.gochara_intensity import compute_lambda_e, enrich_targets
from services.gochara_intensity.engine import fetch_temporal_shape
from services.ka_gochara_sweep.shape_output import ACTIVATION_EPS, _serialize_result
# Deliberate reuse of v1's own active-sentence re-gather helper (see module
# docstring) -- not a fork. Underscore-prefixed in its home module (private by
# convention, not by enforcement); imported here for exactly the reason its
# docstring exists: a bounded, per-row re-gather, not a per-grid-day one.
from services.ka_gochara_sweep.sweep import _gather_active_sentences_at

from .solver import ArcSource, ContactSolver
from .tiers import eager_bodies

logger = logging.getLogger(__name__)

# The v1 grammar/scoring engine this module calls unchanged. Bumped only if
# gochara_grammar/gochara_intensity's OWN logic changes -- which, per design
# §5, is out of this wave's scope in the first place. Feeds
# `services.w2g.fingerprint.class_fingerprint`'s `grammar_version` input.
GRAMMAR_VERSION = "v1_frozen_2026_08"

# Widest orb any v1 primitive discloses (primitives.py's eclipse-proximity
# check, 8.0 deg) -- used ONLY to cast a net for "is this date worth asking
# compute_lambda_e about", never as a claim about which primitive fires. The
# real per-primitive orb judgment happens inside compute_lambda_e's own
# gather_configuration_sentences call, unchanged from v1.
CANDIDATE_NET_ORB_DEG = 8.0

# Design amendment 3 (progressive horizon onboarding): build ±N years from
# "now" first, fast, honestly labelled -- never silently present a partial
# horizon as the whole one.
PROGRESSIVE_HORIZON_YEARS = 3

HORIZON_STATUS_PROGRESSIVE = "progressive_partial"
HORIZON_STATUS_FULL = "full_backfill"

PEAK_BASIS_V2 = "gochara_lambda_e_v1"  # same model as v1 -- see module docstring
GENERATION_V2 = "2.0"


@dataclass(frozen=True)
class HorizonAttestation:
    """An HONEST disclosure of how much of the century this build actually
    covered -- design amendment 3's binding requirement. Never silently
    presented as a full-century result when it isn't."""

    start_date: date
    end_date: date
    status: str  # HORIZON_STATUS_PROGRESSIVE | HORIZON_STATUS_FULL

    def as_dict(self) -> dict[str, Any]:
        return {
            "horizon_start_date": self.start_date.isoformat(),
            "horizon_end_date": self.end_date.isoformat(),
            "horizon_status": self.status,
        }


def _shift_years(d: date, years: int) -> date:
    """`d` shifted by whole `years`, clamped to the target month's last real
    day (handles the Feb-29 leap-day case honestly instead of raising)."""
    target_year = d.year + years
    try:
        return date(target_year, d.month, d.day)
    except ValueError:
        # d.month/d.day is Feb 29 and target_year is not a leap year.
        return date(target_year, d.month, d.day - 1)


def progressive_horizon(today: date, years: int = PROGRESSIVE_HORIZON_YEARS) -> HorizonAttestation:
    """±`years` from `today` -- design amendment 3's fast first onboarding
    slice. `today` is a parameter (never `date.today()` called internally) so
    this function stays deterministic and testable."""
    start = _shift_years(today, -years)
    end = _shift_years(today, years)
    return HorizonAttestation(start_date=start, end_date=end, status=HORIZON_STATUS_PROGRESSIVE)


def full_century_horizon(epoch_start: date, epoch_end: date) -> HorizonAttestation:
    """The eventual full-backfill horizon, bounded by the live ephemeris floor
    (ADJUDICATION-5: `calendar_epoch_start` = 1900-01-01, N3). Not invoked by
    this lane's writer yet -- see PR body for what's deferred -- but the
    attestation shape exists now so a future backfill lane has nowhere to
    invent a different one."""
    return HorizonAttestation(start_date=epoch_start, end_date=epoch_end, status=HORIZON_STATUS_FULL)


def resolve_target_degrees(targets: Sequence[ResonanceTarget]) -> list[float]:
    """Exact-degree targets only (see module docstring on `bhava` exclusion).
    Honest empty list, never a fabricated degree."""
    return [
        float(t.target_longitude_deg) % 360.0
        for t in targets
        if t.target_longitude_deg is not None
    ]


def candidate_point_jds(
    arc_source: ArcSource,
    target_degs: Sequence[float],
    horizon_start_jd: float,
    horizon_end_jd: float,
    bodies: Sequence[str] = eager_bodies(),
    orb_deg: float = CANDIDATE_NET_ORB_DEG,
    include_lazy: bool = False,
) -> list[float]:
    """Every EXACT contact instant (arc-solved conjunction) within the
    horizon, across `bodies` x `target_degs`. Sorted, de-duplicated to
    millisecond-JD precision (two primitives sharing a target degree should
    not double-evaluate the same instant).

    Honest empty list when `target_degs` is empty -- no fabricated dates."""
    if not target_degs:
        return []
    solver = ContactSolver(arc_source)
    events = solver.solve(bodies, target_degs, orb_deg, include_lazy=include_lazy)
    seen: set[float] = set()
    out: list[float] = []
    for ev in events:
        if not (horizon_start_jd <= ev.exact_jd <= horizon_end_jd):
            continue
        key = round(ev.exact_jd, 6)  # ~0.09s -- collapses true duplicates, not distinct contacts
        if key in seen:
            continue
        seen.add(key)
        out.append(ev.exact_jd)
    out.sort()
    return out


@dataclass
class MaterializeResult:
    rows: list[dict[str, Any]]
    contacts_evaluated: int
    targets_resolved: int
    skipped_reason: Optional[str] = None


def materialize_event_class(
    swe: Any,
    conn: Any,
    chart_id: str,
    event_class: str,
    arc_source: ArcSource,
    horizon_start_jd: float,
    horizon_end_jd: float,
    bodies: Sequence[str] = eager_bodies(),
    orb_deg: float = CANDIDATE_NET_ORB_DEG,
    ayanamsha_id: str = "lahiri_chitrapaksha",
    fetch_resonance_targets: Callable[..., list[ResonanceTarget]] = RM.fetch_resonance_targets,
    fetch_dasha_periods: Callable[..., list[dict]] = DD.fetch_dasha_periods,
    compute_lambda_e_fn: Callable[..., Any] = compute_lambda_e,
    gather_active_sentences_fn: Callable[..., list] = _gather_active_sentences_at,
    fetch_temporal_shape_fn: Callable[..., str] = fetch_temporal_shape,
) -> MaterializeResult:
    """The join + score step for ONE (chart_id, event_class). Reuses v1's
    grammar unchanged (module docstring); the only new logic here is WHICH
    instants get asked about, via the arc substrate.

    `fetch_resonance_targets`/`fetch_dasha_periods`/`compute_lambda_e_fn`/
    `gather_active_sentences_fn`/`fetch_temporal_shape_fn` are all injectable
    (tests supply fixtures that need no DB/swisseph; the live path's defaults
    are v1's own, unmodified functions -- same DB-defensive honest-empty
    contract those already carry)."""
    raw_targets = fetch_resonance_targets(conn, chart_id, event_class)
    if not raw_targets:
        return MaterializeResult(rows=[], contacts_evaluated=0, targets_resolved=0,
                                  skipped_reason="no gochara_resonance_map targets for this "
                                                  "chart/event_class -- honest empty, not fabricated")

    targets = enrich_targets(conn, raw_targets, ayanamsha_id=ayanamsha_id)

    shape = fetch_temporal_shape_fn(conn, event_class)
    if shape != "point":
        return MaterializeResult(rows=[], contacts_evaluated=0, targets_resolved=len(targets),
                                  skipped_reason=f"temporal_shape={shape!r} not yet materialized by "
                                                  "W2G (interval/chain segment-consolidation deferred "
                                                  "to a future lane -- see module docstring)")

    target_degs = resolve_target_degrees(targets)
    candidate_jds = candidate_point_jds(
        arc_source, target_degs, horizon_start_jd, horizon_end_jd,
        bodies=bodies, orb_deg=orb_deg,
    )

    dasha_periods = fetch_dasha_periods(conn, chart_id, ayanamsha_id=ayanamsha_id)

    rows: list[dict[str, Any]] = []
    for t_jd in candidate_jds:
        result = compute_lambda_e_fn(
            swe, conn, chart_id, event_class, t_jd,
            targets=targets, dasha_periods=dasha_periods, temporal_shape="point",
            ayanamsha_id=ayanamsha_id,
        )
        if result.raw_lambda <= ACTIVATION_EPS:
            continue  # honest inactivity, not a served row -- matches v1's _active_runs threshold
        peak_date = _jd_to_date_ist(swe, t_jd)
        row: dict[str, Any] = {
            "event_class": event_class,
            "temporal_shape": "point",
            "window_start": peak_date,
            "window_end": peak_date,
            "peak_date": peak_date,
            "milestone_id": None,
            "is_irreversibility_milestone": False,
            "active_sentences": gather_active_sentences_fn(swe, conn, chart_id, targets, t_jd),
            "peak_basis": PEAK_BASIS_V2,
        }
        row.update(_serialize_result(result))
        # W1.5: wire λ decomposition + CI fields from IntensityResult onto the row.
        # These are None on v1-parity rows (IntensityResult defaults) and
        # populated on v3 rows by gochara_v3.engine._evaluate_single_from_context.
        row["term_breakdown"] = result.term_breakdown
        row["lambda_v3_ci_low"] = result.lambda_v3_ci_low
        row["lambda_v3_ci_high"] = result.lambda_v3_ci_high
        row["ci_source"] = result.ci_source
        rows.append(row)

    return MaterializeResult(
        rows=rows, contacts_evaluated=len(candidate_jds), targets_resolved=len(targets),
    )


def _jd_to_date_ist(swe: Any, jd: float) -> date:
    y, m, d, _hour = swe.revjul(jd + 5.5 / 24.0)
    return date(int(y), int(m), int(d))


__all__ = [
    "CANDIDATE_NET_ORB_DEG",
    "GENERATION_V2",
    "GRAMMAR_VERSION",
    "HORIZON_STATUS_FULL",
    "HORIZON_STATUS_PROGRESSIVE",
    "PEAK_BASIS_V2",
    "PROGRESSIVE_HORIZON_YEARS",
    "HorizonAttestation",
    "MaterializeResult",
    "candidate_point_jds",
    "full_century_horizon",
    "materialize_event_class",
    "progressive_horizon",
    "resolve_target_degrees",
]
