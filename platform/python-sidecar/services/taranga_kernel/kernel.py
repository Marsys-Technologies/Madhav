"""
services.taranga_kernel.kernel — pure activation-curve primitives (L3 Kāla).

Doctrine-Waves D-3 / wave/D-3/T-3.

`harmonic_mean` and `GRAHA_DOMAINS` below are extracted VERBATIM (byte-identical
bodies) from `pipeline/orchestrator/writers/ka_taranga.py`'s former module-level
`_harmonic_mean` / `_GRAHA_DOMAINS` — that writer now imports them from here
instead of defining its own copies, so its stored `kala_taranga` output is
unchanged (same code, not just equivalent code — see
tests/l3/test_taranga_kernel_extraction.py for the byte-identical regression
guard).

`ChartStaticSubstrate` / `compute_activation_curve` are the NEW shared,
point-in-time (or monthly-range) activation-curve interface: the same
dasha × transit × promise combination formula ka_taranga runs at 1950-2100
monthly grain, but callable at an arbitrary single month or [start, end]
range, with ALL I/O already resolved into the substrate by the caller. This
is the interface T-2's live on-demand caller imports.

NO writer-side I/O anywhere in this module: no db_conn, no psycopg, no
network calls. Every function is a pure function of its arguments.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterator, Optional, Union

# ── GRAHA_DOMAINS (verbatim from ka_taranga.py's former _GRAHA_DOMAINS) ──────

GRAHA_DOMAINS: dict[str, list[str]] = {
    "Sun":     ["dharma", "career"],
    "Moon":    ["mind", "relationship", "health"],
    "Mars":    ["career", "property", "health"],
    "Mercury": ["education", "commerce", "wealth"],
    "Jupiter": ["dharma", "wealth", "children", "education"],
    "Venus":   ["relationship", "wealth", "creativity"],
    "Saturn":  ["karma", "career", "longevity", "health"],
    "Rahu":    ["karma", "foreign", "technology"],
    "Ketu":    ["moksha", "spirituality"],
}


def harmonic_mean(values: list[float]) -> float:
    """Verbatim extraction of ka_taranga.py's former `_harmonic_mean`."""
    pos = [v for v in values if v > 0]
    if not pos:
        return 0.0
    if len(pos) == 1:
        return pos[0]
    return len(pos) / sum(1.0 / v for v in pos)


def combine_activation(
    dasha_contribution: float,
    transit_contribution: float,
    promise_contribution: float,
) -> float:
    """The dasha × transit × promise combination rule (verbatim from the
    per-scope inline expression in ka_taranga.py's `run()`):
      harmonic_mean([d, t, p])  when promise_contribution > 0
      arithmetic_mean([d, t])   otherwise (harmonic mean is undefined/0 when
                                 any term is exactly 0 — arithmetic fallback
                                 keeps a signal even when promise data is
                                 absent for this scope, matching the writer's
                                 original behavior).
    Not clamped here — callers clamp to [0, 1] at the point of use (matches
    ka_taranga.py: `round(min(1.0, max(0.0, act)), 6)`), so this function
    stays a pure combination rule reusable at any rounding/clamping policy.
    """
    if promise_contribution > 0:
        return harmonic_mean([dasha_contribution, transit_contribution, promise_contribution])
    return (dasha_contribution + transit_contribution) / 2.0


def month_range(start: date, end: date) -> Iterator[date]:
    """Verbatim extraction of ka_taranga.py's former `_month_range`: yield
    first-of-month dates from start to end inclusive."""
    cur = date(start.year, start.month, 1)
    while cur <= end:
        yield cur
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)


# ── ChartStaticSubstrate / compute_activation_curve (new shared interface) ──

@dataclass(frozen=True)
class ChartStaticSubstrate:
    """Per-chart, already-resolved-from-DB static inputs for activation-curve
    computation. NO I/O happens inside this dataclass or compute_activation_curve
    — the caller (batch writer OR live on-demand service) resolves every field
    from chart_dashas / kala_convergence / bodha_pratijna (or the live PROMISE
    formula in `promise.py`) BEFORE constructing this object.

    CR-87 (must_not_touch per D-3/T-3 brief §F2): `chart_id` is a REQUIRED
    positional field — never defaulted — so this substrate can never silently
    stand in for a different chart's data. Every current/function built on top
    of this substrate must take chart context as a required parameter, per the
    two-chart CR-87 regression guard in
    tests/test_cr87_native_chart_context.py.

    dasha_periods: vimshottari MD rows, [{'lord_graha': str, 'ds': date, 'de': date}, ...]
    graha_domains: which life-domains each graha's daśā activates (defaults to
        the canonical GRAHA_DOMAINS map above — pass a chart-specific override
        only if a session explicitly derives one; do not fabricate one).
    transit_windows: kala_convergence rows relevant to this chart,
        [{'domain': str, 'window_start': date, 'window_end': date,
          'convergence_score': float}, ...]
    promise_by_domain / promise_by_event_class: PROMISE (or legacy pratijna
        grade/10) score per scope_id, already resolved by the caller — see
        promise.py for the real PROMISE formula this should be built from.
    """
    chart_id: str
    dasha_periods: list[dict]
    graha_domains: dict[str, list[str]] = field(default_factory=lambda: dict(GRAHA_DOMAINS))
    transit_windows: list[dict] = field(default_factory=list)
    promise_by_domain: dict[str, float] = field(default_factory=dict)
    promise_by_event_class: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.chart_id:
            raise ValueError(
                "ChartStaticSubstrate.chart_id is required (CR-87) — never "
                "construct a substrate without resolving the real chart_id."
            )


def dasha_lord_at(substrate: ChartStaticSubstrate, t: date) -> Optional[str]:
    """Which dasha lord's MD period covers date `t`. Linear scan over
    substrate.dasha_periods (mirrors ka_taranga.py's `_lord_for_month`
    closure) — fine for the ~120-period vimshottari MD list; a live caller
    querying many points should pre-sort/bisect on its own copy if needed."""
    for row in substrate.dasha_periods:
        if row["ds"] <= t <= row["de"]:
            return row["lord_graha"]
    return None


def _transit_scores_by_domain_at(substrate: ChartStaticSubstrate, t: date) -> dict[str, list[float]]:
    """{domain: [convergence_score, ...]} for every transit window overlapping
    month `t` (first-of-month date). Mirrors ka_taranga.py's
    `transit_by_month_domain` precomputation, but evaluated lazily per-call
    (the batch writer precomputes once across all months for performance;
    this pure function trades that for O(windows) per call, appropriate for
    a live single-point-in-time caller)."""
    out: dict[str, list[float]] = {}
    month_start = date(t.year, t.month, 1)
    for tw in substrate.transit_windows:
        ws, we = tw["window_start"], tw["window_end"]
        if ws <= month_start <= we:
            domain = tw.get("domain") or "unknown"
            out.setdefault(domain, []).append(float(tw.get("convergence_score") or 0))
    return out


@dataclass(frozen=True)
class ActivationPoint:
    """One point on an activation curve."""
    t: date
    scope_kind: str
    scope_id: str
    activation: float
    components: dict


def compute_activation_curve(
    substrate: ChartStaticSubstrate,
    t_or_range: Union[date, tuple[date, date]],
    scope_kind: str,
    scope_id: str,
    *,
    resolution: str = "month",
) -> list[ActivationPoint]:
    """Pure activation-curve computation. Same formula as ka_taranga.py's
    per-scope row generation, generalized to a single point OR a [start, end]
    range instead of the writer's fixed 1950-2100 sweep.

    substrate: ChartStaticSubstrate — REQUIRED, carries chart_id (CR-87).
    t_or_range: a single `date` (evaluated at that date's first-of-month) or
        a (start, end) tuple of dates (evaluated at every first-of-month in
        the inclusive range, per `month_range`).
    scope_kind: 'domain' | 'event_class' — same two scopes ka_taranga writes.
    scope_id: the domain name or event_class_id.
    resolution: only 'month' is implemented (matches the only grain
        ka_taranga's stored kala_taranga table carries — see module
        docstring: "Fine grain (daily/hourly) = SERVICE computation, never
        stored"). A live caller needing finer grain must extend this
        function (or build a sibling one on the same substrate/primitives)
        rather than fork the combination formula — flagged here rather than
        silently approximated (B.10).

    Returns one ActivationPoint per evaluated month, sorted by t ascending.
    """
    if resolution != "month":
        raise NotImplementedError(
            f"compute_activation_curve: resolution={resolution!r} not supported — "
            "only 'month' grain is wired today (see docstring). This is an "
            "honest gap, not a silent approximation."
        )
    if scope_kind not in ("domain", "event_class"):
        raise ValueError(f"compute_activation_curve: unknown scope_kind {scope_kind!r}")

    if isinstance(t_or_range, tuple):
        start, end = t_or_range
        times = list(month_range(start, end))
    else:
        times = [date(t_or_range.year, t_or_range.month, 1)]

    points: list[ActivationPoint] = []
    for t in times:
        lord = dasha_lord_at(substrate, t)
        lord_domains = set(substrate.graha_domains.get(lord, [])) if lord else set()
        transit_this_month = _transit_scores_by_domain_at(substrate, t)

        if scope_kind == "domain":
            d_contrib = 1.0 if scope_id in lord_domains else 0.15
            t_vals = transit_this_month.get(scope_id, [])
            t_contrib = sum(t_vals) / len(t_vals) if t_vals else 0.0
            p_contrib = float(substrate.promise_by_domain.get(scope_id) or 0)
        else:  # event_class
            p_contrib = float(substrate.promise_by_event_class.get(scope_id) or 0)
            d_contrib = 1.0 if lord and any(
                d in lord_domains for d in substrate.graha_domains.get(lord, [])
            ) else 0.1
            t_vals = [s for dvals in transit_this_month.values() for s in dvals]
            t_contrib = max(t_vals) if t_vals else 0.0

        act = combine_activation(d_contrib, t_contrib, p_contrib)
        points.append(ActivationPoint(
            t=t,
            scope_kind=scope_kind,
            scope_id=scope_id,
            activation=round(min(1.0, max(0.0, act)), 6),
            components={
                "dasha_contribution": round(d_contrib, 4),
                "transit_contribution": round(t_contrib, 4),
                "promise_contribution": round(p_contrib, 4),
                "dasha_lord": lord,
                "chart_id": substrate.chart_id,
            },
        ))
    return points


__all__ = [
    "GRAHA_DOMAINS",
    "harmonic_mean",
    "combine_activation",
    "month_range",
    "ChartStaticSubstrate",
    "dasha_lord_at",
    "ActivationPoint",
    "compute_activation_curve",
]
