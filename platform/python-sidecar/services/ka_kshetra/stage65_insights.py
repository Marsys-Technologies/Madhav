"""
services/ka_kshetra/stage65_insights.py — Stage 6.5 insight synthesis (E2),
KALA_W2_FIELD_DESIGN_v1_0.md §6.4.

`kala_insights` rows are manufactured DETERMINISTICALLY (B.10 — never
generative), each carrying `fact_ids`, a cohort surprise score, a robustness
vector, and a drill id (`insight_id`). This module owns SEVEN of the eight
catalog types; the eighth, `biographical_echo`, reads the LEL and is written
exclusively by Lane E's biographical-join refresh — see the CIRCULARITY
GUARD CARVE-OUT below, which is binding, not a Lane D design choice.

┌─────────────────────────────────────────────────────────────────────────┐
│ CIRCULARITY GUARD CARVE-OUT (§6.4, §8.3 CG-1) — read before editing.     │
│ Every function in this module MUST remain free of any LEL reference.    │
│ `synthesize_insights()` never emits `insight_type='biographical_echo'`   │
│ and always writes `lel_derived=False`. The field hash (§7.4) covers only │
│ rows with `lel_derived=FALSE` — this is what lets the field never move  │
│ when the LEL is mutated, while still serving the insight (via a         │
│ SEPARATE, Lane-E-owned write path).                                     │
└─────────────────────────────────────────────────────────────────────────┘

This module is pure: no DB connection, no LEL, no generative model. Callers
(eventually Lane C's `ka_kshetra` orchestration) assemble the typed inputs
from `kala_field_windows` / `kala_field_provenance` rows plus this lane's
own `stage6_salience` / `cohort_client` outputs.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from math import log

from services.ka_kshetra.stage6_salience import compute_reliability
from services.ka_kshetra.submodular import window_family_id as _window_family_id

_DAYS_PER_JULIAN_YEAR = 365.2425

# The seven non-LEL types this module writes. `biographical_echo` is
# deliberately absent -- see the CIRCULARITY GUARD CARVE-OUT above.
NON_LEL_INSIGHT_TYPES = (
    "concurrence", "rarity_firing", "absence_of_expected",
    "compression", "scarcity", "reversal", "contrast",
)

P_RARE_DEFAULT = 0.05
CONCURRENCE_MIN_SYSTEMS = 3
COMPRESSION_MIN_WINDOWS = 3
COMPRESSION_SPAN_DAYS = 45.0
SCARCITY_MIN_YEARS = 5.0
CONTRAST_MIN_DELTA_LN_LAMBDA = 0.5
ABSENCE_MIN_PROMISE = 0.60


# ── Input shapes (mirror the frozen §5.1-§5.3 boundary Lane D reads) ───────

@dataclass(frozen=True)
class ClockAgreement:
    """One applicable+predictive daśā system's signed relevance at a
    window's peak (§5.1 C-3's `r_{s,e}(t)`)."""

    system_id: str
    competence_class: str
    r_value: float


@dataclass(frozen=True)
class InsightWindow:
    """The slice of a `kala_field_windows` row (§5.3) plus this lane's own
    §6.1 salience that Stage 6.5's detectors need."""

    window_id: str
    event_class: str
    t_start: float
    t_end: float
    t_peak: float
    lambda_peak: float
    salience: float
    confidence_tier: str | None
    lord_stack_at_peak: tuple[str, ...] = ()
    clock_agreements: tuple[ClockAgreement, ...] = ()
    fact_ids: tuple[str, ...] = ()
    robustness: dict | None = None

    @property
    def window_family_id(self) -> str:
        return _window_family_id(self.event_class, self.lord_stack_at_peak)


@dataclass(frozen=True)
class CohortSurpriseInput:
    """The rarity signal this lane's own `cohort_client.CohortRate` supplies."""

    p_cohort: float | None
    n_cohort: int


@dataclass(frozen=True)
class ReversalSample:
    t: float
    signed_obstruction: float   # in (-1, 0]
    lambda_value: float
    q_e: float


@dataclass(frozen=True)
class InsightCandidate:
    """An internal, pre-assembly detector output. `synthesize_insights()`
    turns these into full `kala_insights` row dicts."""

    insight_type: str
    event_class: str | None
    window_id: str | None
    t_start: float | None
    t_end: float | None
    statement_key: str
    statement_params: dict
    discriminator: str          # extra uniqueness key beyond (type, window_id)
    carrier_salience: float
    confidence_tier: str | None
    fact_ids: tuple[str, ...] = ()
    robustness: dict | None = None
    cohort: CohortSurpriseInput | None = None


# ── cohort_surprise / reliability (§6.4's insight_score formula) ──────────

def compute_cohort_surprise(cohort: CohortSurpriseInput | None) -> tuple[float, str]:
    """
    cohort_surprise = −ln(p_cohort) / −ln(1/N_cohort), EXCEPT §6.4's own
    override: when `p_cohort` is None (not computable), cohort_surprise is
    NOT surprise-credited — use 0.5 and record the basis, rather than the
    formula's degenerate min(1, inf/finite)=1.0 a naive read would produce.
    """
    if cohort is None or cohort.p_cohort is None or cohort.n_cohort <= 1:
        return 0.5, "not_surprise_credited"
    if cohort.p_cohort <= 0.0:
        return 1.0, "cohort_base_rate"
    if cohort.p_cohort >= 1.0:
        return 0.0, "cohort_base_rate"
    return min(1.0, -log(cohort.p_cohort) / log(cohort.n_cohort)), "cohort_base_rate"


def _reliability(confidence_tier: str | None) -> float:
    """Reliability B for the insight_score formula. Falls back to the
    weakest defined tier (structural_prior=0.5) for an unresolved tier
    rather than aborting scoring entirely -- every real `kala_field_windows`
    row carries a confidence_tier by construction (§5.6), so this fallback
    is defensive, not a silent substitution for missing real data."""
    reliability = compute_reliability(confidence_tier)
    return reliability if reliability is not None else 0.5


def compute_insight_score(carrier_salience: float, cohort: CohortSurpriseInput | None,
                           confidence_tier: str | None) -> tuple[float, str]:
    """insight_score = cohort_surprise × carrier_salience × reliability (§6.4)."""
    surprise, basis = compute_cohort_surprise(cohort)
    reliability = _reliability(confidence_tier)
    return surprise * carrier_salience * reliability, basis


def _insight_id(chart_id: str, insight_type: str, discriminator: str) -> str:
    payload = f"{chart_id}|{insight_type}|{discriminator}"
    return "kin_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _sign(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


# ── The seven non-LEL detectors ─────────────────────────────────────────────

def detect_concurrence(
    window: InsightWindow, min_systems: int = CONCURRENCE_MIN_SYSTEMS,
) -> InsightCandidate | None:
    """
    Type 1: >=3 independent, applicable, predictive daśā systems have
    r_{s,e}(t_peak) > 0 on the same window. Independence = distinct
    competence_class (two systems sharing a competence_class count as one
    voice, not two).
    """
    agreeing = [ca for ca in window.clock_agreements if ca.r_value > 0]
    distinct_classes = {ca.competence_class for ca in agreeing}
    if len(distinct_classes) < min_systems:
        return None
    systems = sorted(ca.system_id for ca in agreeing)
    return InsightCandidate(
        insight_type="concurrence", event_class=window.event_class,
        window_id=window.window_id, t_start=window.t_start, t_end=window.t_end,
        statement_key="insight_concurrence_v1",
        statement_params={
            "event_class": window.event_class, "systems": systems,
            "n_independent_systems": len(distinct_classes),
        },
        discriminator=window.window_id, carrier_salience=window.salience,
        confidence_tier=window.confidence_tier, fact_ids=window.fact_ids,
        robustness=window.robustness,
    )


def detect_rarity_firing(
    window: InsightWindow, cohort: CohortSurpriseInput, p_rare: float = P_RARE_DEFAULT,
) -> InsightCandidate | None:
    """Type 2: the window's active configuration occurs in < p_rare of the
    cohort (from `cohort_base_rate`, matched sub-cohort where available)."""
    if cohort.p_cohort is None or cohort.p_cohort >= p_rare:
        return None
    return InsightCandidate(
        insight_type="rarity_firing", event_class=window.event_class,
        window_id=window.window_id, t_start=window.t_start, t_end=window.t_end,
        statement_key="insight_rarity_firing_v1",
        statement_params={"event_class": window.event_class, "p_cohort": cohort.p_cohort},
        discriminator=window.window_id, carrier_salience=window.salience,
        confidence_tier=window.confidence_tier, fact_ids=window.fact_ids,
        robustness=window.robustness, cohort=cohort,
    )


def detect_absence_of_expected(
    event_class: str, p_e: float, windows_in_horizon: list[InsightWindow],
    horizon_start: float, horizon_end: float,
    threshold: float = ABSENCE_MIN_PROMISE,
) -> InsightCandidate | None:
    """Type 4: P_e >= 0.60 (strong natal promise) AND zero windows for `e`
    in the queried horizon. `window_id`/`event_class` on the row is NULL for
    this type per §6.4's own schema note."""
    if p_e < threshold or windows_in_horizon:
        return None
    return InsightCandidate(
        insight_type="absence_of_expected", event_class=event_class,
        window_id=None, t_start=horizon_start, t_end=horizon_end,
        statement_key="insight_absence_of_expected_v1",
        statement_params={"event_class": event_class, "p_e": p_e,
                           "horizon_start": horizon_start, "horizon_end": horizon_end},
        discriminator=f"{event_class}|{horizon_start}|{horizon_end}",
        carrier_salience=0.0,  # no carrier window -- see synthesize_insights() default handling
        confidence_tier=None, fact_ids=(),
    )


def detect_compression(
    windows: list[InsightWindow], k: int = COMPRESSION_MIN_WINDOWS,
    span_days: float = COMPRESSION_SPAN_DAYS,
) -> list[InsightCandidate]:
    """
    Type 5: >=k=3 windows from DISTINCT window_family_ids overlap a single
    span of <=45 days. Deterministic greedy clustering by ascending t_peak:
    once a qualifying cluster is found, it consumes its member windows so a
    single dense stretch never emits overlapping duplicate insights.
    """
    ws = sorted(windows, key=lambda w: (w.t_peak, w.window_id))
    candidates: list[InsightCandidate] = []
    i, n = 0, len(ws)
    while i < n:
        j = i
        families: dict[str, list[InsightWindow]] = {}
        while j < n and ws[j].t_peak - ws[i].t_peak <= span_days:
            families.setdefault(ws[j].window_family_id, []).append(ws[j])
            j += 1
        if len(families) >= k:
            cluster = ws[i:j]
            top = max(cluster, key=lambda w: w.salience)
            candidates.append(InsightCandidate(
                insight_type="compression", event_class=top.event_class,
                window_id=top.window_id, t_start=cluster[0].t_peak, t_end=cluster[-1].t_peak,
                statement_key="insight_compression_v1",
                statement_params={
                    "window_ids": [w.window_id for w in cluster],
                    "n_families": len(families),
                    "span_days": cluster[-1].t_peak - cluster[0].t_peak,
                },
                discriminator=f"compression|{cluster[0].window_id}|{cluster[-1].window_id}",
                carrier_salience=top.salience, confidence_tier=top.confidence_tier,
                fact_ids=tuple(sorted({fid for w in cluster for fid in w.fact_ids})),
                robustness=top.robustness,
            ))
            i = j  # advance past the whole cluster -- no overlapping duplicate emission
        else:
            i += 1
    return candidates


def detect_scarcity(
    current_window: InsightWindow, later_windows_same_class: list[InsightWindow],
    years: float = SCARCITY_MIN_YEARS,
) -> InsightCandidate | None:
    """Type 6: the recurrence ladder for `e` shows no further window for
    >=N=5 years after this one -- the honest cost-of-inaction."""
    gap_days_threshold = years * _DAYS_PER_JULIAN_YEAR
    later = sorted(
        (w for w in later_windows_same_class if w.t_start > current_window.t_end),
        key=lambda w: w.t_start,
    )
    if not later:
        gap_days = None
        next_window_id = None
    else:
        gap_days = later[0].t_start - current_window.t_end
        next_window_id = later[0].window_id
        if gap_days < gap_days_threshold:
            return None

    return InsightCandidate(
        insight_type="scarcity", event_class=current_window.event_class,
        window_id=current_window.window_id, t_start=current_window.t_start,
        t_end=current_window.t_end,
        statement_key="insight_scarcity_v1",
        statement_params={
            "event_class": current_window.event_class,
            "gap_days": gap_days, "next_window_id": next_window_id,
        },
        discriminator=f"scarcity|{current_window.window_id}",
        carrier_salience=current_window.salience,
        confidence_tier=current_window.confidence_tier,
        fact_ids=current_window.fact_ids, robustness=current_window.robustness,
    )


def detect_reversal(
    event_class: str, carrier_window: InsightWindow, samples: list[ReversalSample],
) -> list[InsightCandidate]:
    """Type 7: sign(signed_obstruction) crosses, or λ_e crosses q_e in the
    opposite direction, within the horizon — "the weather turns in June"."""
    candidates: list[InsightCandidate] = []
    ordered = sorted(samples, key=lambda s: s.t)
    for prev, cur in zip(ordered, ordered[1:]):
        prev_obs_sign, cur_obs_sign = _sign(prev.signed_obstruction), _sign(cur.signed_obstruction)
        obstruction_crossed = prev_obs_sign != 0 and cur_obs_sign != 0 and prev_obs_sign != cur_obs_sign

        prev_above_q = prev.lambda_value >= prev.q_e
        cur_above_q = cur.lambda_value >= cur.q_e
        lambda_crossed = prev_above_q != cur_above_q

        if obstruction_crossed or lambda_crossed:
            candidates.append(InsightCandidate(
                insight_type="reversal", event_class=event_class,
                window_id=carrier_window.window_id, t_start=prev.t, t_end=cur.t,
                statement_key="insight_reversal_v1",
                statement_params={
                    "event_class": event_class, "t_cross": cur.t,
                    "obstruction_crossed": obstruction_crossed,
                    "lambda_crossed": lambda_crossed,
                },
                discriminator=f"reversal|{carrier_window.window_id}|{cur.t}",
                carrier_salience=carrier_window.salience,
                confidence_tier=carrier_window.confidence_tier,
                fact_ids=carrier_window.fact_ids, robustness=carrier_window.robustness,
            ))
    return candidates


def detect_contrast(
    carrier_window: InsightWindow, current_ln_lambda: float, baseline_ln_lambda: float,
    baseline_label: str, threshold: float = CONTRAST_MIN_DELTA_LN_LAMBDA,
) -> InsightCandidate | None:
    """Type 8: field diff vs a baseline (last_month/last_year/a pinned
    field_snapshot_id/an alternative option) exceeds Δln λ >= 0.5."""
    delta = current_ln_lambda - baseline_ln_lambda
    if abs(delta) < threshold:
        return None
    return InsightCandidate(
        insight_type="contrast", event_class=carrier_window.event_class,
        window_id=carrier_window.window_id, t_start=carrier_window.t_start,
        t_end=carrier_window.t_end,
        statement_key="insight_contrast_v1",
        statement_params={
            "event_class": carrier_window.event_class, "delta_ln_lambda": delta,
            "baseline_label": baseline_label,
        },
        discriminator=f"contrast|{carrier_window.window_id}|{baseline_label}",
        carrier_salience=carrier_window.salience,
        confidence_tier=carrier_window.confidence_tier,
        fact_ids=carrier_window.fact_ids, robustness=carrier_window.robustness,
    )


# ── Assembly: InsightCandidate -> a full kala_insights row dict ────────────

def assemble_insight_row(
    chart_id: str, candidate: InsightCandidate, weights_version: str, field_snapshot_id: str,
) -> dict:
    """
    Turn one detector's `InsightCandidate` into a full `kala_insights` row
    (migration 495), ALWAYS with `lel_derived=False` (CIRCULARITY GUARD
    CARVE-OUT — this module never writes an lel_derived=TRUE row).
    """
    insight_score, surprise_basis = compute_insight_score(
        candidate.carrier_salience, candidate.cohort, candidate.confidence_tier,
    )
    cohort_p = candidate.cohort.p_cohort if candidate.cohort else None
    cohort_surprise_value, _ = compute_cohort_surprise(candidate.cohort)

    return {
        "chart_id": chart_id,
        "insight_id": _insight_id(chart_id, candidate.insight_type, candidate.discriminator),
        "insight_type": candidate.insight_type,
        "event_class": candidate.event_class,
        "window_id": candidate.window_id,
        "t_start": candidate.t_start,
        "t_end": candidate.t_end,
        "statement_key": candidate.statement_key,
        "statement_params": candidate.statement_params,
        "fact_ids": list(candidate.fact_ids),
        "cohort_surprise": cohort_surprise_value if cohort_p is not None else None,
        "cohort_version": None,
        "surprise_basis": surprise_basis,
        "robustness": candidate.robustness or {},
        "insight_score": insight_score,
        "lel_derived": False,
        "weights_version": weights_version,
        "field_snapshot_id": field_snapshot_id,
    }


def synthesize_insights(
    chart_id: str,
    windows: list[InsightWindow],
    weights_version: str,
    field_snapshot_id: str,
    cohort_by_window: dict[str, CohortSurpriseInput] | None = None,
    absence_candidates: list[tuple[str, float, float, float]] | None = None,
    scarcity_pairs: list[tuple[InsightWindow, list[InsightWindow]]] | None = None,
    reversal_inputs: list[tuple[str, InsightWindow, list[ReversalSample]]] | None = None,
    contrast_inputs: list[tuple[InsightWindow, float, float, str]] | None = None,
) -> list[dict]:
    """
    The top-level Stage 6.5 entry point: runs every non-LEL detector this
    module owns over the given inputs and returns fully-assembled
    `kala_insights` row dicts (§6.4), all with `lel_derived=False`.

    Every optional input defaults to "not supplied" (empty), so a caller
    that only has windows + cohort rates still gets concurrence/
    rarity_firing/compression -- the detectors this module can run from
    `kala_field_windows` rows alone. absence_of_expected/scarcity/reversal/
    contrast each need extra context (a natal promise prior, a recurrence
    ladder, a time series, a baseline) that only the caller (Lane C's
    `ka_kshetra` orchestration) has -- passing none of them is honest-empty,
    never an error.
    """
    cohort_by_window = cohort_by_window or {}
    candidates: list[InsightCandidate] = []

    for w in windows:
        c = detect_concurrence(w)
        if c is not None:
            candidates.append(c)
        cohort = cohort_by_window.get(w.window_id)
        if cohort is not None:
            c = detect_rarity_firing(w, cohort)
            if c is not None:
                candidates.append(c)

    candidates.extend(detect_compression(windows))

    for event_class, p_e, horizon_start, horizon_end in (absence_candidates or []):
        matching = [w for w in windows if w.event_class == event_class]
        c = detect_absence_of_expected(event_class, p_e, matching, horizon_start, horizon_end)
        if c is not None:
            candidates.append(c)

    for current, later in (scarcity_pairs or []):
        c = detect_scarcity(current, later)
        if c is not None:
            candidates.append(c)

    for event_class, carrier, samples in (reversal_inputs or []):
        candidates.extend(detect_reversal(event_class, carrier, samples))

    for carrier, current_ln, baseline_ln, label in (contrast_inputs or []):
        c = detect_contrast(carrier, current_ln, baseline_ln, label)
        if c is not None:
            candidates.append(c)

    return [
        assemble_insight_row(chart_id, cand, weights_version, field_snapshot_id)
        for cand in candidates
    ]


def select_leading_insight(rows: list[dict]) -> dict | None:
    """
    The composer contract (E2, enforced): every view's `reading.thesis` is
    composed from the highest-scoring insight available for that view's
    scope. Ties resolve to the lexicographically lower `insight_id`
    (deterministic — no arbitrary "first in list wins").
    """
    if not rows:
        return None
    return min(rows, key=lambda r: (-r["insight_score"], r["insight_id"]))


# ── Item 33: bodha_pratijna-aware absence detector (W3) ─────────────────────

@dataclass(frozen=True)
class PratijnaRow:
    """A typed slice of a `bodha_pratijna` DB row.

    `grade` is the classical promise score ∈ [0, 1] for the event class on
    this chart (the normalised value stored in `bodha_pratijna.grade`).
    `fact_ids` are the `chart_facts.fact_id`s that established the promise —
    they ride the resulting InsightCandidate for B.3 provenance.
    """
    pratijna_id: str
    event_class: str
    grade: float
    fact_ids: tuple[str, ...] = ()


def detect_absence_from_pratijna(
    event_class: str,
    pratijna_rows: list[PratijnaRow],
    windows_in_horizon: list[InsightWindow],
    horizon_start: float,
    horizon_end: float,
    threshold: float = ABSENCE_MIN_PROMISE,
) -> InsightCandidate | None:
    """
    Item 33 (W3): bodha_pratijna-aware absence-of-expected detector.

    Fires when:
    - At least one `PratijnaRow` for `event_class` exists (absence of
      something *expected* — never of something never promised).
    - The MAXIMUM grade across all rows is >= `threshold` (strong natal
      promise).
    - Zero windows exist for `event_class` in the queried horizon.

    The resulting InsightCandidate carries the union of `fact_ids` from ALL
    pratijna rows (B.3 — every consumer can trace back to the natal facts
    that established the promise).

    `carrier_salience` is proportional to `max_grade` so the monotonicity
    property holds: a stronger promise (higher grade) yields a higher-scoring
    absence insight, ceteris paribus (more windows → fewer open promises).
    """
    if not pratijna_rows:
        return None
    max_grade = max(r.grade for r in pratijna_rows)
    if max_grade < threshold:
        return None
    matching_windows = [w for w in windows_in_horizon if w.event_class == event_class]
    if matching_windows:
        return None

    all_fact_ids: tuple[str, ...] = tuple(sorted({
        fid for row in pratijna_rows for fid in row.fact_ids
    }))

    return InsightCandidate(
        insight_type="absence_of_expected",
        event_class=event_class,
        window_id=None,
        t_start=horizon_start,
        t_end=horizon_end,
        statement_key="insight_absence_of_expected_v1",
        statement_params={
            "event_class": event_class,
            "p_e": max_grade,
            "horizon_start": horizon_start,
            "horizon_end": horizon_end,
        },
        discriminator=f"{event_class}|{horizon_start}|{horizon_end}",
        # carrier_salience = max_grade so a higher promise → higher score
        # (monotonicity property, Item 33 brief spec).
        carrier_salience=max_grade,
        confidence_tier=None,
        fact_ids=all_fact_ids,
    )


# ── Item 34: Contrastive field-diff (W3) ────────────────────────────────────

@dataclass
class FieldSnapshot:
    """A lightweight representation of the set of `kala_field_windows` at a
    past or alternative time-point, used as the baseline for `compute_field_diff`.

    `windows_by_id` is keyed by `window_id` for O(1) lookup during diff.
    Not frozen: the `windows_by_id` index is derived at construction time
    and stored as a plain attribute for fast lookup.
    """
    snapshot_label: str
    windows: list[InsightWindow]

    def __post_init__(self):
        self.windows_by_id: dict[str, InsightWindow] = {
            w.window_id: w for w in self.windows
        }

    def __init__(self, snapshot_label: str, windows: list[InsightWindow]):
        self.snapshot_label = snapshot_label
        self.windows = windows
        self.windows_by_id = {w.window_id: w for w in windows}


def compute_field_diff(
    current_windows: list[InsightWindow],
    baseline: FieldSnapshot,
    lambda_threshold: float = CONTRAST_MIN_DELTA_LN_LAMBDA,
) -> dict:
    """
    Item 34 (W3): compute the contrastive field diff between the current set
    of `kala_field_windows` and a `FieldSnapshot` baseline.

    Returns a dict with four lists (always present, even if empty):
    - `new_windows`:        present in current, absent from baseline.
    - `closed_windows`:     present in baseline, absent from current.
    - `intensified_windows`: present in both; ln(λ_current/λ_baseline) > threshold.
    - `weakened_windows`:   present in both; ln(λ_baseline/λ_current) > threshold.

    Each list entry is a dict carrying at minimum:
        { "window_id", "event_class", "fact_ids", "delta_ln_lambda" (where applicable) }

    This function is the PURE data-layer diff — no insight rows assembled here.
    Callers (serving layer or synthesize_insights) wrap the diff into
    InsightCandidates / kala_insights rows as needed.
    """
    current_by_id: dict[str, InsightWindow] = {w.window_id: w for w in current_windows}
    baseline_by_id = baseline.windows_by_id

    current_ids = set(current_by_id)
    baseline_ids = set(baseline_by_id)

    new_windows = [
        {
            "window_id": wid,
            "event_class": current_by_id[wid].event_class,
            "fact_ids": list(current_by_id[wid].fact_ids),
        }
        for wid in sorted(current_ids - baseline_ids)
    ]

    closed_windows = [
        {
            "window_id": wid,
            "event_class": baseline_by_id[wid].event_class,
            "fact_ids": list(baseline_by_id[wid].fact_ids),
        }
        for wid in sorted(baseline_ids - current_ids)
    ]

    intensified_windows: list[dict] = []
    weakened_windows: list[dict] = []

    for wid in sorted(current_ids & baseline_ids):
        w_cur = current_by_id[wid]
        w_base = baseline_by_id[wid]
        if w_base.lambda_peak <= 0:
            continue
        delta_ln = log(w_cur.lambda_peak / w_base.lambda_peak) if w_cur.lambda_peak > 0 else float("-inf")
        entry = {
            "window_id": wid,
            "event_class": w_cur.event_class,
            "fact_ids": list(w_cur.fact_ids),
            "delta_ln_lambda": delta_ln,
        }
        if delta_ln > lambda_threshold:
            intensified_windows.append(entry)
        elif -delta_ln > lambda_threshold:
            weakened_windows.append(entry)

    return {
        "new_windows": new_windows,
        "closed_windows": closed_windows,
        "intensified_windows": intensified_windows,
        "weakened_windows": weakened_windows,
    }
