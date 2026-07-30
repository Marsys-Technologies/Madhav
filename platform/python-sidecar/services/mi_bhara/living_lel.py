"""
living_lel.py — THE LIVING-LEL CALIBRATION PLANE (registry item 39) and the auto-filed
prospective falsifier ledger (registry item 20).

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.6; `SHAD_DARSHANA_BRIEF_v2_0.md` §3 W2 and §2.5.5.

═══════════════════════════════════════════════════════════════════════════════════════════
  THE INCREMENTAL FLOW ON ONE LEL APPEND (§7.6)
═══════════════════════════════════════════════════════════════════════════════════════════
LEL entries remain native-only (brief §7 rail). When one lands:

  1. **Falsifier resolution FIRST.** Score the new event against every OPEN prospective ledger
     entry — item 20 auto-files one per AHEAD window and per adopted upāya. Prospective
     hits/misses are the gold-standard currency and are tallied SEPARATELY from backfill.
     Resolution comes first because a weight update must not be able to change what counts as
     a hit: the falsifier was fixed when the prediction was filed, and it is scored against
     the model that filed it.
  2. **Weight update** via §7.2 shrinkage → a NEW weights version row (never an UPDATE).
  3. **Skill + GOF recompute**, published to `kala_field_skill` / `kala_field_gof`.
  4. **Biographical-join refresh** — `biographical_echo` insights with `lel_derived = TRUE`,
     STORY chapter verdicts, per-chapter retrodiction fits. The ONLY served artifacts that
     consume the LEL directly, and the reason `kala_insights.lel_derived` exists: the field
     hash covers only `lel_derived = FALSE` rows, so the insight is served AND the field
     never moved (§6.4's carve-out, §8.3's CG-1).
  5. **Maturity index update** — `calibration_maturity = {n_events, prospective_resolutions,
     event_class_coverage, weights_version, skill_score}`, carried in every envelope.
     `platform-mcp/src/lib/kala_envelope.ts::CalibrationMaturity` is the shape; W2 fills it,
     and `noLelCalibrationMaturity()` remains exactly correct for the LEL-absent chart.

═══════════════════════════════════════════════════════════════════════════════════════════
  DISPATCH DISCIPLINE (§2.5.5 — BINDING)
═══════════════════════════════════════════════════════════════════════════════════════════
The LEL-append hook dispatches a **standard, tracked, scoped build run** through the
orchestrator — `scope='asset_set'`, `scope_target='mi_bhara'`. **NO SIDE-CHANNEL
RECOMPUTATION.** The orchestrator remains the sole build-state writer, and Nirmāṇa must see
state, progress and throughput for a recalibration exactly as for any other build.

`recalibration_dispatch` below produces that request and nothing else — it deliberately does
NOT execute anything. A module that could both decide to recalibrate and perform the
recalculation would be one refactor away from being a side channel; keeping the decision and
the execution in different processes makes the rule structural rather than aspirational. The
biographical-join refresh is phase 4 INSIDE `mi_bhara.run()`, not a separate asset, so the
asset set is exactly `['mi_bhara']` and there is no second id to keep in sync.

═══════════════════════════════════════════════════════════════════════════════════════════
  THE THREE LEL SCENARIOS (D6, §7.6) — ALL THREE GATED AT W2
═══════════════════════════════════════════════════════════════════════════════════════════
  LEL-rich    fitted with shrinkage; calibrated-track claims where `n_eff` supports
  LEL-ABSENT  `φ = φ⁰` EXACTLY (falls out of `n_eff = 0`); everything `structural_prior`;
              STORY chapters flagged `no_lived_history_recorded`; `calibration_maturity` an
              honest ZERO; `skill_state = 'underpowered'`
  LEL-growing tiers migrate visibly, auditable via `tier_migrations`

Note that NOTHING in this module branches on chart identity or on "does this chart have a
LEL". The LEL-absent behaviour is what the arithmetic produces when the inputs are empty.

Pure functions. No DB, no clock (timestamps are arguments), no RNG.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Iterable, Mapping, Sequence

#: The STORY flag the LEL-absent chart carries (§7.6's three-scenario table).
NO_LIVED_HISTORY_FLAG = "no_lived_history_recorded"

#: Confidence tiers, weakest first. §5.6 sets the first two from the robustness vector; stage
#: 9's maturity index is the ONLY thing that may promote to the last two.
TIER_STRUCTURAL_PRIOR = "structural_prior"
TIER_CONCURRENT = "concurrent"
TIER_CALIBRATED_PROVISIONAL = "calibrated_provisional"
TIER_CALIBRATED = "calibrated"
TIER_ORDER = (
    TIER_STRUCTURAL_PRIOR,
    TIER_CONCURRENT,
    TIER_CALIBRATED_PROVISIONAL,
    TIER_CALIBRATED,
)

#: Promotion thresholds, in PROSPECTIVE resolutions — not in raw event count. Backfill can
#: make a model look fitted; only a prediction filed before its outcome can make it look
#: TESTED, and the tier vocabulary is about testedness (Elevation §7).
PROSPECTIVE_FOR_PROVISIONAL = 3
PROSPECTIVE_FOR_CALIBRATED = 12

OUTCOME_HIT = "hit"
OUTCOME_MISS = "miss"
OUTCOME_UNRESOLVED = "unresolved"


# ── item 20 — the auto-filed prospective falsifier ledger ──────────────────────────────

@dataclass(frozen=True)
class OpenPrediction:
    """One OPEN row of `brahma_prospective_ledger`, as the scorer sees it.

    `window_id` is the `kala_field_windows.window_id` the prediction was filed against — the
    item-44 `authority_basis` value. A prediction with no `window_id` is scoreable but is
    NOT credited to the field: it was not a field claim.
    """

    prediction_id: str
    event_class: str
    window_start: float
    window_end: float
    filed_at_t: float
    window_id: str | None = None
    claim_shape: str = "interval"


@dataclass(frozen=True)
class LelEventRef:
    """A life event as the ledger scorer sees it. `t` is days since birth."""

    event_id: str
    event_class: str
    t: float


@dataclass(frozen=True)
class ScoredPrediction:
    prediction_id: str
    window_id: str | None
    outcome: str
    matched_event_id: str | None
    lead_time_days: float | None
    #: True only when the prediction was FILED strictly before the event occurred. This is
    #: what makes a resolution "prospective"; a ledger row back-filed after the fact is a
    #: retrodiction wearing a prediction's clothes and is counted as backfill.
    is_prospective: bool


def score_predictions_against_event(
    event: LelEventRef, open_predictions: Sequence[OpenPrediction]
) -> list[ScoredPrediction]:
    """§7.6 step 1 — resolve every open prospective entry against one newly-appended event.

    A prediction is a HIT iff the event's class matches AND the event time falls inside the
    prediction's window. Same class but outside the window is a MISS (the claim was about
    WHEN, and it was wrong about when). A different class leaves the prediction UNTOUCHED and
    it is not returned at all — one event does not resolve an unrelated claim.

    `lead_time_days = event.t − filed_at_t`, and `is_prospective` is `lead_time_days > 0`.
    Both are reported per row; nothing here decides they are "close enough".
    """
    out: list[ScoredPrediction] = []
    for p in open_predictions:
        if p.event_class != event.event_class:
            continue
        inside = p.window_start <= event.t <= p.window_end
        lead = event.t - p.filed_at_t
        out.append(
            ScoredPrediction(
                prediction_id=p.prediction_id,
                window_id=p.window_id,
                outcome=OUTCOME_HIT if inside else OUTCOME_MISS,
                matched_event_id=event.event_id if inside else None,
                lead_time_days=lead,
                is_prospective=lead > 0.0,
            )
        )
    return out


def lapsed_predictions(
    open_predictions: Sequence[OpenPrediction], as_of_t: float
) -> list[ScoredPrediction]:
    """Predictions whose window closed with no matching event.

    Reported as `unresolved` rather than as `miss`: an unobserved window is not evidence the
    claim was wrong, only that nothing was recorded. (`brahma_prospective_ledger` carries the
    matching lifecycle value `lapsed_unobserved`, added by migration 466 for exactly this
    distinction.) Counting these as misses would flatter or damn the model on the strength of
    the native's diary-keeping, which is not a property of the model.
    """
    return [
        ScoredPrediction(
            prediction_id=p.prediction_id,
            window_id=p.window_id,
            outcome=OUTCOME_UNRESOLVED,
            matched_event_id=None,
            lead_time_days=None,
            is_prospective=True,
        )
        for p in open_predictions
        if p.window_end < as_of_t
    ]


# ── the maturity index (§7.6 step 5) ───────────────────────────────────────────────────

@dataclass(frozen=True)
class CalibrationMaturity:
    """Mirrors `platform-mcp/src/lib/kala_envelope.ts::CalibrationMaturity` field for field.

    `event_class_coverage` is a FRACTION in [0,1], and `0` — not `null` — is the honest value
    for a chart with zero LEL events, exactly as `noLelCalibrationMaturity()` returns.
    `weights_version` and `skill_score` are nullable because "no version pinned yet" and
    "skill not measurable" are real states that must not be rendered as zeros.
    """

    n_events: int
    prospective_resolutions: int
    event_class_coverage: float
    weights_version: str | None
    skill_score: float | None

    def to_envelope_dict(self) -> dict:
        return {
            "n_events": self.n_events,
            "prospective_resolutions": self.prospective_resolutions,
            "event_class_coverage": self.event_class_coverage,
            "weights_version": self.weights_version,
            "skill_score": self.skill_score,
        }


def no_lel_calibration_maturity() -> CalibrationMaturity:
    """The Python twin of `kala_envelope.ts::noLelCalibrationMaturity()`.

    Kept byte-for-byte equivalent on purpose: the LEL-absent chart must serve the SAME honest
    zero whether the envelope was assembled by the TypeScript facade or filled from a writer.
    `tests/l5/test_mi_bhara_living_lel.py` asserts the two agree by reading the TS source.
    """
    return CalibrationMaturity(
        n_events=0,
        prospective_resolutions=0,
        event_class_coverage=0.0,
        weights_version=None,
        skill_score=None,
    )


def compute_calibration_maturity(
    *,
    lel_events: Sequence[LelEventRef],
    prospective_resolutions: int,
    known_event_classes: Sequence[str],
    weights_version: str | None,
    chart_skill_score: float | None,
) -> CalibrationMaturity:
    """§7.6 step 5.

    `event_class_coverage` is |classes with ≥1 recorded event| / |classes in the ontology| —
    a coverage fraction, so a chart with 57 events all in one class reads as thin coverage,
    which is the truth. An empty ontology yields 0.0 rather than a division error; the honest
    reading of "no classes are known" is "nothing is covered".

    `weights_version` and `skill_score` are reported as NULL when there are no events, so that
    `compute_calibration_maturity([], …)` equals `no_lel_calibration_maturity()` exactly. This
    is a reporting distinction, not a fitting branch — the FIT has no empty-LEL special case at
    all (see `fit.py`; `n_eff = 0 ⇒ φ⁰` is pure arithmetic). What this field means is "which
    version CALIBRATION produced", and with no lived history none did: the chart is running on
    `v0_classical`, a structural prior, and reporting that id here would let a reader take the
    presence of a version as evidence of calibration. Same reasoning for `skill_score`: with
    zero events skill is not measurable, and `0.0` would read as "measured, and it is zero".
    """
    n = len(lel_events)
    total_classes = len(set(known_event_classes))
    covered = len({e.event_class for e in lel_events} & set(known_event_classes))
    coverage = (covered / total_classes) if total_classes else 0.0
    return CalibrationMaturity(
        n_events=n,
        prospective_resolutions=prospective_resolutions,
        event_class_coverage=coverage,
        weights_version=weights_version if n > 0 else None,
        skill_score=chart_skill_score if n > 0 else None,
    )


def tier_for(structural_tier: str, prospective_resolutions: int) -> str:
    """The maturity index's ONLY promotion power (§5.6): it may raise a window's
    `confidence_tier` to `calibrated_provisional` / `calibrated`, and nothing else may.

    A tier is never promoted ABOVE what the robustness vector supports — a window whose
    structural tier is `structural_prior` (some robustness dimension is false) does not become
    `calibrated` because the chart happens to have a long diary. Promotion requires the
    structural evidence AND the prospective record.
    """
    if structural_tier not in TIER_ORDER:
        raise ValueError(f"unknown structural tier {structural_tier!r}")
    if structural_tier == TIER_STRUCTURAL_PRIOR:
        return TIER_STRUCTURAL_PRIOR
    if prospective_resolutions >= PROSPECTIVE_FOR_CALIBRATED:
        return TIER_CALIBRATED
    if prospective_resolutions >= PROSPECTIVE_FOR_PROVISIONAL:
        return TIER_CALIBRATED_PROVISIONAL
    return structural_tier


@dataclass(frozen=True)
class TierMigration:
    scope: str
    from_tier: str
    to_tier: str


def tier_migrations(
    before: Mapping[str, str], after: Mapping[str, str]
) -> list[TierMigration]:
    """The auditable `tier_migrations[]` of the §7.6 calibration receipt.

    Sorted by scope so the receipt is deterministic — a receipt whose row order varied would
    be indistinguishable from one whose CONTENT varied, to anyone diffing two of them.
    """
    out = [
        TierMigration(scope=k, from_tier=before[k], to_tier=after[k])
        for k in sorted(set(before) & set(after))
        if before[k] != after[k]
    ]
    return out


# ── the portal calibration receipt (§7.6 — a W2 deliverable, not aspiration) ───────────

def calibration_receipt(
    *,
    scored: Sequence[ScoredPrediction],
    maturity_before: CalibrationMaturity,
    maturity_after: CalibrationMaturity,
    migrations: Sequence[TierMigration],
) -> dict:
    """The exact §7.6 receipt returned through the existing mimāṃsā / standing-predictions
    surface on the LEL-intake path.

    `hits` and `misses` count only RESOLVED rows; `unresolved` is reported separately rather
    than folded into `misses` (see `lapsed_predictions`). A receipt whose numbers did not add
    up to its own row list would be exactly the "populated-looking but hollow envelope"
    §N.6 item 3 forbids, so the counts are derived from the rows, never passed in.
    """
    return {
        "predictions_scored": [
            {
                "prediction_id": s.prediction_id,
                "window_id": s.window_id,
                "outcome": s.outcome,
                "lead_time_days": s.lead_time_days,
                "is_prospective": s.is_prospective,
            }
            for s in scored
        ],
        "hits": sum(1 for s in scored if s.outcome == OUTCOME_HIT),
        "misses": sum(1 for s in scored if s.outcome == OUTCOME_MISS),
        "unresolved": sum(1 for s in scored if s.outcome == OUTCOME_UNRESOLVED),
        "maturity_before": maturity_before.to_envelope_dict(),
        "maturity_after": maturity_after.to_envelope_dict(),
        "tier_migrations": [
            {"scope": m.scope, "from": m.from_tier, "to": m.to_tier} for m in migrations
        ],
    }


# ── §2.5.5 — the TRACKED scoped build run (never a side channel) ───────────────────────

#: `mi_bhara` alone: the biographical-join refresh is phase 4 inside its own `run()`, not a
#: separate asset, so there is no second id that could drift out of sync with this list.
RECALIBRATION_ASSET_SET = ("mi_bhara",)


@dataclass(frozen=True)
class RecalibrationDispatch:
    """A request for the orchestrator's standard build-run endpoint. Data, not an action.

    Shape matches `POST /api/cockpit/runs` (`platform/src/app/api/cockpit/runs/route.ts`):
    `scope='asset_set'` with a comma-separated `scope_target`, which `parseAssetSetTarget`
    splits and `resolveBuildPlan` topo-sorts like any other build. Nirmāṇa therefore shows
    state, progress and throughput for a recalibration exactly as for a user-initiated build.
    """

    chart_id: str
    scope: str
    scope_target: str
    action: str
    reason: str
    triggering_event_ids: tuple[str, ...] = dc_field(default_factory=tuple)

    def to_request_body(self) -> dict:
        return {
            "chart_id": self.chart_id,
            "scope": self.scope,
            "scope_target": self.scope_target,
            "action": self.action,
        }


def recalibration_dispatch(
    *, chart_id: str, triggering_event_ids: Iterable[str]
) -> RecalibrationDispatch:
    """Build the §2.5.5 tracked-run request for an LEL append.

    This function RETURNS a request. It does not send one, does not open a connection, and
    does not compute anything a build would compute. That separation is the rule made
    structural: there is no code path here that could become a side-channel recompute, because
    there is no compute here at all.
    """
    return RecalibrationDispatch(
        chart_id=chart_id,
        scope="asset_set",
        scope_target=",".join(RECALIBRATION_ASSET_SET),
        action="rebuild",
        reason="lel_append",
        triggering_event_ids=tuple(triggering_event_ids),
    )
