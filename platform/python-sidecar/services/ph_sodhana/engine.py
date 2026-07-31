"""
ph_sodhana engine — DB-free anomaly detection for phala_anchors.

LEAKAGE-FIREWALL gate (D43a):
  If anomaly_type == 'layer_leakage' with leakage_class == 'l5_calibration_attempted',
  the writer raises LeakageFirewallError (RuntimeError subclass). The build halts.
  Nothing is committed. The native must inspect and manually correct phala_anchors.

Five anomaly types (no LLM, fully deterministic):
  confidence_inflation  — confidence_high > G-LADDER ceiling(n_independent, ayanamsha_robustness)
  magnitude_drift       — magnitude label inconsistent with convergence_score quartile
  falsifier_absent      — falsifier missing machine-evaluable REFUTED/CONFIRMED tokens
  ledger_gap            — derivation_ledger_jsonb missing ≥1 required axis key
  layer_leakage         — confidence_basis != 'structural_not_yet_empirical'
                          (any other value is an L5 contamination attempt)

auto_action is ALWAYS 'stage_for_review' — enforced at DB level AND here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

__all__ = [
    'AnchorRow',
    'SodhanaContext',
    'SodhanaRecord',
    'LeakageFirewallError',
    'detect_confidence_inflation',
    'detect_magnitude_drift',
    'detect_falsifier_absent',
    'detect_ledger_gap',
    'detect_layer_leakage',
    'detect_confidence_degenerate',
    'derive_sodhana_flags',
]

# G-LADDER ceiling formula. NARRATION FIDELITY (SAMAPTI B-NAR-PH, P2 :38): a
# prior version of this comment claimed shared authorship with ph_nimitta's
# confidence model — stale since BA-P5B (2026-07-04, commit ab99ada1), when
# ph_nimitta REPLACED its G-LADDER confidence_range model with a structured
# posterior (base_rate × promise_lift × activation_lift × trigger_lift ×
# robustness_mod; see services/ph_nimitta/engine.py module docstring).
# ph_sodhana's copy of the formula was never updated to track that change and
# has been this detector's OWN independent QA ceiling ever since — it has not
# tracked any live ph_nimitta computation for months. Kept as ph_sodhana's own
# heuristic (a structural rewrite to align the two is out of this lane's
# one-function scope); the outdated cross-reference is removed here so a
# reader does not assume this ceiling still tracks ph_nimitta's actual
# confidence-generating model.
_LADDER_FLOORS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]  # n=1..6+
_ROBUSTNESS_FACTOR_MIN = 0.80
_ROBUSTNESS_FACTOR_MAX = 1.00
_CONF_CAP = 0.80

# Required axes in derivation_ledger_jsonb
_MINIMUM_LEDGER_KEYS = {'anchor_source'}

_FALSIFIER_TOKENS = {'REFUTED', 'CONFIRMED'}

# Magnitude ↔ convergence_score quartile thresholds
_MAGNITUDE_THRESHOLDS = {
    'pivotal':  0.80,  # convergence_score must be >= 0.80 to justify 'pivotal'
    'major':    0.60,
    'moderate': 0.35,
    'minor':    0.0,
}


class LeakageFirewallError(RuntimeError):
    """Raised by derive_sodhana_flags when L5 calibration leakage is detected.
    The writer propagates this as a build halt — no partial commit (D43a).
    """


@dataclass
class AnchorRow:
    """Subset of phala_anchors fields needed for anomaly detection."""
    anchor_id:              str
    anchor_source:          str
    domain:                 str
    confidence_low:         Optional[float] = None
    confidence_high:        Optional[float] = None
    confidence_basis:       Optional[str]   = None
    magnitude:              Optional[str]   = None
    falsifier:              Optional[str]   = None
    derivation_ledger_jsonb: dict           = field(default_factory=dict)
    dasha_consensus_count:  Optional[int]   = None
    ayanamsha_robustness:   Optional[int]   = None
    convergence_id:         Optional[int]   = None


@dataclass
class SodhanaContext:
    """Pre-fetched anchor rows (writer supplies; engine is DB-free)."""
    chart_id: str
    anchors:  list[AnchorRow] = field(default_factory=list)


@dataclass
class SodhanaRecord:
    anchor_id:              str
    anomaly_type:           str
    anomaly_severity:       str
    detected_field:         str
    expected_value_text:    Optional[str]
    observed_value_text:    Optional[str]
    leakage_class:          Optional[str]
    recommendation_text:    str
    auto_action:            str = 'stage_for_review'   # LOCKED
    derivation_ledger_jsonb: dict = field(default_factory=dict)
    source_citation:        str = ''


def _g_ladder_ceiling(n_independent: Optional[int], ayanamsha_robustness: Optional[int]) -> float:
    n   = min(max(int(n_independent or 1), 1), 6)
    rob = min(max(int(ayanamsha_robustness or 3), 0), 5)
    rob_factor = _ROBUSTNESS_FACTOR_MIN + 0.04 * rob
    return min(_CONF_CAP, (0.50 + 0.05 * n) * rob_factor)


def detect_confidence_inflation(anchor: AnchorRow) -> Optional[SodhanaRecord]:
    """confidence_high must not exceed G-LADDER ceiling for this anchor."""
    if anchor.confidence_high is None:
        return None
    ceiling = _g_ladder_ceiling(anchor.dasha_consensus_count, anchor.ayanamsha_robustness)
    if float(anchor.confidence_high) > ceiling + 1e-6:
        return SodhanaRecord(
            anchor_id=anchor.anchor_id,
            anomaly_type='confidence_inflation',
            anomaly_severity='major',
            detected_field='confidence_high',
            expected_value_text=f'<= {ceiling:.3f} (G-LADDER ceiling for n={anchor.dasha_consensus_count}, '
                                f'rob={anchor.ayanamsha_robustness})',
            observed_value_text=str(anchor.confidence_high),
            leakage_class=None,
            recommendation_text=(
                f'Recalculate confidence_high using G-LADDER: n_independent={anchor.dasha_consensus_count}, '
                f'ayanamsha_robustness={anchor.ayanamsha_robustness} → ceiling={ceiling:.3f}. '
                'Stage correction for native review before using this anchor in ph_pramana.'
            ),
            derivation_ledger_jsonb={'anchor_id': anchor.anchor_id, 'ceiling': ceiling, 'observed': anchor.confidence_high},
            source_citation=f'ph_sodhana/confidence_inflation/{anchor.anchor_id}',
        )
    return None


def detect_magnitude_drift(anchor: AnchorRow) -> Optional[SodhanaRecord]:
    """
    Magnitude label consistency check.

    NARRATION FIDELITY (SAMAPTI B-NAR-PH, P2 :136): the docstring previously
    claimed this checks magnitude against "convergence_score quartile" — the
    phala_anchors.confidence formula's actual third factor
    (score = dasha_quality × signal_strength × convergence_score). It does not.
    AnchorRow carries only `convergence_id` (a kala_convergence FK), never the
    raw convergence_score value — wiring the real score in requires a join in
    the ph_sodhana WRITER (pipeline/orchestrator/writers/ph_sodhana.py), a file
    this engine-only lane does not own (§4.0: one file → one lane; flagged as
    an out-of-lane residual, not attempted here). So this detector uses
    confidence_high as a PROXY signal instead — an honest, in-lane, one-function
    fix: the docstring now says so, and the returned record's
    derivation_ledger_jsonb carries an explicit `check_basis` key naming the
    substitution, so no downstream consumer of the 'magnitude_drift' anomaly can
    mistake this for a genuine convergence_score check.
    """
    mag = (anchor.magnitude or '').lower()
    if mag not in _MAGNITUDE_THRESHOLDS:
        return None
    # Proxy check (see docstring above): confidence_high stands in for the
    # convergence_score this engine cannot see. If magnitude claims a high tier
    # but confidence_high sits well below the tier's threshold, flag the
    # inconsistency — honestly labelled as a proxy-basis finding, not a
    # convergence_score-basis one.
    conf_high = float(anchor.confidence_high or 0.0)
    threshold = _MAGNITUDE_THRESHOLDS[mag]
    if threshold > 0 and conf_high < threshold * 0.80:
        return SodhanaRecord(
            anchor_id=anchor.anchor_id,
            anomaly_type='magnitude_drift',
            anomaly_severity='minor',
            detected_field='magnitude',
            expected_value_text=f'magnitude consistent with confidence_high >= {threshold * 0.80:.2f} for {mag!r}',
            observed_value_text=f'magnitude={mag!r}, confidence_high={conf_high:.3f}',
            leakage_class=None,
            recommendation_text=(
                f'Anchor claims magnitude={mag!r} but confidence_high={conf_high:.3f} is well below '
                f'the {mag} threshold ({threshold:.2f}). Downgrade magnitude or verify convergence evidence. '
                '(Basis: confidence_high proxy, not a direct convergence_score check — see check_basis.)'
            ),
            derivation_ledger_jsonb={
                'anchor_id': anchor.anchor_id, 'magnitude': mag, 'conf_high': conf_high,
                'check_basis': 'confidence_high_proxy_not_convergence_score',
            },
            source_citation=f'ph_sodhana/magnitude_drift/{anchor.anchor_id}',
        )
    return None


def detect_falsifier_absent(anchor: AnchorRow) -> Optional[SodhanaRecord]:
    """Falsifier must contain machine-evaluable REFUTED and CONFIRMED tokens."""
    falsifier = (anchor.falsifier or '').strip()
    if not falsifier or not any(tok in falsifier for tok in _FALSIFIER_TOKENS):
        return SodhanaRecord(
            anchor_id=anchor.anchor_id,
            anomaly_type='falsifier_absent',
            anomaly_severity='critical',
            detected_field='falsifier',
            expected_value_text='text containing both REFUTED and CONFIRMED with measurable criteria',
            observed_value_text=repr(falsifier[:120]) if falsifier else '(empty)',
            leakage_class=None,
            recommendation_text=(
                'Regenerate falsifier with machine-evaluable format: '
                '"REFUTED if <observable criterion> by <date>. CONFIRMED if <observable criterion>."'
            ),
            derivation_ledger_jsonb={'anchor_id': anchor.anchor_id},
            source_citation=f'ph_sodhana/falsifier_absent/{anchor.anchor_id}',
        )
    return None


def detect_ledger_gap(anchor: AnchorRow) -> Optional[SodhanaRecord]:
    """derivation_ledger_jsonb must contain at least 'anchor_source' key."""
    ledger = anchor.derivation_ledger_jsonb or {}
    missing = _MINIMUM_LEDGER_KEYS - set(ledger.keys())
    if missing:
        return SodhanaRecord(
            anchor_id=anchor.anchor_id,
            anomaly_type='ledger_gap',
            anomaly_severity='major',
            detected_field='derivation_ledger_jsonb',
            expected_value_text=f'contains keys: {sorted(_MINIMUM_LEDGER_KEYS)}',
            observed_value_text=f'missing: {sorted(missing)}',
            leakage_class=None,
            recommendation_text=(
                f'Rebuild anchor derivation to include required ledger keys: {sorted(missing)}. '
                'Without a complete ledger, ph_pramana cannot trace derivation provenance.'
            ),
            derivation_ledger_jsonb={'anchor_id': anchor.anchor_id, 'missing_keys': sorted(missing)},
            source_citation=f'ph_sodhana/ledger_gap/{anchor.anchor_id}',
        )
    return None


def detect_layer_leakage(anchor: AnchorRow) -> Optional[SodhanaRecord]:
    """
    confidence_basis MUST be 'structural_not_yet_empirical'.
    Any other value is an L5 calibration contamination (LEAKAGE-FIREWALL).
    Returns a record with leakage_class = 'l5_calibration_attempted'.
    The WRITER raises LeakageFirewallError when it sees this record type.
    """
    basis = (anchor.confidence_basis or '').strip()
    if basis and basis != 'structural_not_yet_empirical':
        return SodhanaRecord(
            anchor_id=anchor.anchor_id,
            anomaly_type='layer_leakage',
            anomaly_severity='critical',
            detected_field='confidence_basis',
            expected_value_text="'structural_not_yet_empirical'",
            observed_value_text=repr(basis),
            leakage_class='l5_calibration_attempted',
            recommendation_text=(
                'LEAKAGE-FIREWALL: phala_anchors.confidence_basis must always be '
                "'structural_not_yet_empirical'. L5 Mimamsa owns empirical calibration. "
                'This anchor has been written with an L5-calibrated basis — this is a '
                'write-time bug in ph_nimitta. Correct the writer before re-running the build.'
            ),
            derivation_ledger_jsonb={'anchor_id': anchor.anchor_id, 'observed_basis': basis},
            source_citation=f'ph_sodhana/layer_leakage/{anchor.anchor_id}',
        )
    return None


_DEGENERATE_MIN_ANCHORS = 5     # below this, "zero variance" isn't a meaningful signal
_DEGENERATE_STDDEV_EPS  = 1e-9  # effectively-zero population stddev


def detect_confidence_degenerate(ctx: SodhanaContext) -> Optional[SodhanaRecord]:
    """
    Chart-wide check (unlike the other four, which are per-anchor): flags when
    confidence_high has ~zero variance across every anchor in the chart.

    This catches a class of anomaly none of the per-anchor detectors can see:
    a posterior/confidence model that has collapsed to a single constant value
    for every anchor (e.g. because its inputs are hardcoded defaults rather
    than computed per-anchor) will sit safely under the G-LADDER ceiling for
    every anchor and trip zero per-anchor detectors — reading as a clean bill
    of health for a structurally broken model. A single constant confidence
    value across an entire chart is itself the anomaly.
    """
    values = [a.confidence_high for a in ctx.anchors if a.confidence_high is not None]
    if len(values) < _DEGENERATE_MIN_ANCHORS:
        return None

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    stddev = variance ** 0.5
    if stddev > _DEGENERATE_STDDEV_EPS:
        return None

    anchor = ctx.anchors[0]
    return SodhanaRecord(
        anchor_id=anchor.anchor_id,
        anomaly_type='confidence_degenerate',
        anomaly_severity='critical',
        detected_field='confidence_high',
        expected_value_text='confidence_high varying across anchors per real per-anchor inputs',
        observed_value_text=f'constant={mean:.4f} across all {len(values)} anchors (stddev={stddev:.2e})',
        leakage_class=None,
        recommendation_text=(
            'confidence_high is numerically identical across every anchor in this '
            'chart — the posterior model is almost certainly being fed hardcoded '
            'defaults rather than per-anchor computed inputs (e.g. pratijna_grade, '
            'multi_system_confirmation_count, av_transit_potency). This reads as '
            '"0 anomalies" to the per-anchor detectors and would otherwise pass as a '
            'clean bill of health for a structurally non-differentiated model — '
            'investigate ph_nimitta._build_ctx before trusting any posterior/'
            'confidence value from this build.'
        ),
        derivation_ledger_jsonb={
            'chart_id': str(ctx.chart_id),
            'anchor_count': len(values),
            'constant_value': mean,
        },
        source_citation=f'ph_sodhana/confidence_degenerate/{ctx.chart_id}',
    )


def derive_sodhana_flags(ctx: SodhanaContext) -> list[SodhanaRecord]:
    """
    Run all detectors over every anchor. Returns list of SodhanaRecords.
    RAISES LeakageFirewallError immediately if any layer_leakage with
    leakage_class='l5_calibration_attempted' is detected — build halts.
    """
    records: list[SodhanaRecord] = []
    leakage_found: list[SodhanaRecord] = []

    detectors = [
        detect_layer_leakage,       # check leakage first
        detect_confidence_inflation,
        detect_magnitude_drift,
        detect_falsifier_absent,
        detect_ledger_gap,
    ]

    for anchor in ctx.anchors:
        for detector in detectors:
            rec = detector(anchor)
            if rec is not None:
                if rec.leakage_class == 'l5_calibration_attempted':
                    leakage_found.append(rec)
                else:
                    records.append(rec)

    # Chart-wide detector (operates over all anchors at once, not per-anchor)
    degenerate_rec = detect_confidence_degenerate(ctx)
    if degenerate_rec is not None:
        records.append(degenerate_rec)

    # LEAKAGE-FIREWALL: halt before any insert
    if leakage_found:
        anchor_ids = [r.anchor_id for r in leakage_found]
        raise LeakageFirewallError(
            f"ph_sodhana LEAKAGE-FIREWALL (D43a): {len(leakage_found)} anchor(s) have "
            f"L5 calibration contamination in confidence_basis. anchor_ids={anchor_ids}. "
            "Build halted. Correct ph_nimitta writer before re-running."
        )

    return records
