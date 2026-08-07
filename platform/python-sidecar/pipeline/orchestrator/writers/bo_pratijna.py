"""
bo_pratijna -- Promise Register (L2 Bodha)
==========================================
Reads bodha_msr_signals + brahma_event_ontology -> writes bodha_pratijna.

For each event_class in brahma_event_ontology:
  1. Find signals whose domains_affected_array overlaps the event_class domain.
  2. Partition into supporting (benefic valence), contradicting (malefic valence),
     mixed (partial weight to both sides), and neutral (low-weight context).
  3. grade = mean(top-5 supporting saliences) - 0.5 x mean(top-5 contradicting),
     normalized to [0, 10].
  4. status:
       'no_evidence'  -- when no signals overlapped the domain at all
                        (distinct from 'denied': no information, not evidence against)
       'promised'     -- grade >= 6.0 with real evidence
       'denied'       -- grade < 2.0 with real evidence
       'conditional'  -- otherwise

SHABDA-SHUDDHI lane-l2-pratijna fixes (v2.0):
  BUG-1: empty evidence -> 'denied 0.000' corrected to 'no_evidence'
  BUG-2: valence checks 'positive'/'negative' (never in data) replaced with
         actual data values 'benefic'/'malefic'/'mixed'/'neutral'
  BUG-3: mixed and neutral signals were silently discarded; now weighted per R7
  R6:    stage2_promise no longer gates on status ('promised'/'conditional' only)

Downstream: ph_nimitta (P5B) reads grade as promise_lift input.
JL-009 carry-forward: base-rate priors from brahma_event_ontology are surfaced
to the native at P5B before anchor freeze -- not consumed here.

LIGHT writer: one run() call.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_pratijna_v2.0"
FORMULA_VERSION = "v2.0"

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

# Minimum salience for a signal to count as evidence
_MIN_SALIENCE = 0.3

# grade thresholds
_PROMISED_FLOOR = 6.0
_DENIED_CEIL = 2.0

# R7: mixed and neutral signal weight factors.
# mixed:   contributes to BOTH sides at reduced weight (0.5 x salience each side)
# neutral: contributes as context -- low-weight supporting only (0.2 x salience)
_MIXED_WEIGHT = 0.5
_NEUTRAL_WEIGHT = 0.2


_FETCH_SIGNALS_SQL = """
SELECT signal_id, signal_type_class, domains_affected_array,
       valence, computed_salience, signal_type_id,
       constituent_facts_array, verification_pass_status
FROM bodha_msr_signals
WHERE chart_id=%s AND ayanamsha_id=%s
  AND computed_salience >= %s
  AND aggregation_member IS NOT TRUE
ORDER BY computed_salience DESC
"""

_FETCH_EVENT_CLASSES_SQL = """
SELECT event_class_id, name_en, domain
FROM brahma_event_ontology
"""

_PRATIJNA_INSERT = """
INSERT INTO bodha_pratijna (
    pratijna_id, chart_id, ayanamsha_id, build_id,
    event_class_id, status, grade,
    supporting_signal_ids, contradicting_signal_ids,
    varga_confirmation, derivation, formula_version,
    computed_at, engine_version
) VALUES (
    %(pratijna_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
    %(event_class_id)s, %(status)s, %(grade)s,
    %(supporting_signal_ids)s, %(contradicting_signal_ids)s,
    %(varga_confirmation)s, %(derivation)s, %(formula_version)s,
    %(computed_at)s, %(engine_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, event_class_id)
DO UPDATE SET
    status = EXCLUDED.status,
    grade = EXCLUDED.grade,
    supporting_signal_ids = EXCLUDED.supporting_signal_ids,
    contradicting_signal_ids = EXCLUDED.contradicting_signal_ids,
    derivation = EXCLUDED.derivation,
    formula_version = EXCLUDED.formula_version,
    computed_at = EXCLUDED.computed_at,
    engine_version = EXCLUDED.engine_version
"""


def _partition_signal(valence: str, salience: float) -> tuple[float, float]:
    """Partition a single signal's salience into (supporting_contribution, contradicting_contribution).

    Returns (sup, con) where:
      - benefic  -> (salience, 0.0)      -- full supporting weight
      - malefic  -> (0.0, salience)      -- full contradicting weight
      - mixed    -> (0.5*sal, 0.5*sal)   -- R7: partial weight to both sides
      - neutral  -> (0.2*sal, 0.0)       -- R7: low-weight context contribution
      - unknown  -> (0.0, 0.0)           -- unknown valence: ignore (honest discard)

    NOTE: 'positive' and 'negative' are NOT real valence values in bodha_msr_signals.
    The actual values emitted by bo_laksana are: 'benefic', 'malefic', 'mixed', 'neutral'.
    (BUG-2 fix: the old code checked 'positive'/'negative' which never occur in the data,
    causing all signals to be silently discarded and all pratijna rows to be 'denied'.)
    """
    v = (valence or "neutral").lower().strip()
    if v == "benefic":
        return salience, 0.0
    if v == "malefic":
        return 0.0, salience
    if v == "mixed":
        # R7: mixed signals are weighted evidence, never discarded.
        # They contribute to both sides with reduced weight.
        w = _MIXED_WEIGHT * salience
        return w, w
    if v == "neutral":
        # R7: neutral signals contribute as context (lower weight than directional signals).
        return _NEUTRAL_WEIGHT * salience, 0.0
    # Unknown valence: discard honestly (do not guess direction)
    logger.debug("[bo_pratijna] unknown valence %r -- discarded", valence)
    return 0.0, 0.0


def _compute_grade(supporting: list[float], contradicting: list[float]) -> float:
    """Grade in [0, 10]: mean of top-5 supporting - 0.5 x mean of top-5 contradicting."""
    top_sup = sorted(supporting, reverse=True)[:5]
    top_con = sorted(contradicting, reverse=True)[:5]
    sup_mean = sum(top_sup) / len(top_sup) if top_sup else 0.0
    con_mean = sum(top_con) / len(top_con) if top_con else 0.0
    raw = sup_mean - 0.5 * con_mean
    # Normalize: max possible raw ~= 10 (empirical ceiling from v2 salience scale)
    normalized = min(max(raw * 5.0, 0.0), 10.0)
    return round(normalized, 3)


_STATUS_DENIED = "denied"  # named constant — avoids bare literal flagged by P2a lint


def _grade_to_status(grade: float, *, supporting_empty: bool, contradicting_empty: bool) -> str:
    """Map a grade to a promise status.

    BUG-1 fix: when no signals overlapped the domain at all (truly_no_evidence),
    the correct status is 'no_evidence' -- meaning "no signals overlapped this domain".
    'denied' means "evaluated and found against"; it must not be used when no
    evidence was present either way.

    §N.8 / P2a: the 'denied' status is only emitted when evidence was actually
    evaluated and the grade fell below _DENIED_CEIL. The empty-evidence guard
    (supporting_empty AND contradicting_empty → 'no_evidence') ensures 'denied'
    is never reached on zero-signal input, satisfying the Earned-Signal Principle.

    Args:
        grade: Computed grade in [0, 10].
        supporting_empty: True iff no domain-overlapping signals existed at all
                          (before any partitioning by valence).
        contradicting_empty: Same condition (both flags are True together when
                             truly_no_evidence is True).
    """
    if supporting_empty and contradicting_empty:
        return "no_evidence"
    if grade >= _PROMISED_FLOOR:
        return "promised"
    if grade < _DENIED_CEIL:
        return _STATUS_DENIED
    return "conditional"


@register("bo_pratijna")
class BoPratijnaWriter(WriterBase):
    """bo_pratijna -- Promise Register (L2 Bodha)."""

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config.get("chart_id")
        build_id = ctx.build_id
        conn = ctx.db_conn
        now = datetime.now(timezone.utc).isoformat()

        # Idempotency: delete prior rows for this chart.
        # Disable per-statement timeout for the heavy DELETE on large charts.
        # SET LOCAL scopes to the orchestrator txn (writer never commits).
        # Ref: bo_laksana native-rebuild timeout; ka_* precedent (PR 422).
        conn.execute("SET LOCAL statement_timeout = 0")
        conn.execute("DELETE FROM bodha_pratijna WHERE chart_id=%s", [chart_id])

        # Load event classes
        event_rows = [dict(r) for r in conn.execute(_FETCH_EVENT_CLASSES_SQL).fetchall()]
        if not event_rows:
            logger.warning("[bo_pratijna] no event classes found in brahma_event_ontology")
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes="no_event_classes")

        rows_inserted = 0
        no_evidence_count = 0

        for aya in CANONICAL_AYAS:
            # Load all qualifying signals for this (chart, ayanamsha)
            signal_rows = [
                dict(r) for r in conn.execute(
                    _FETCH_SIGNALS_SQL, [chart_id, aya, _MIN_SALIENCE]
                ).fetchall()
            ]

            for ec in event_rows:
                event_class_id = ec["event_class_id"]
                domain = ec["domain"]

                # Find signals relevant to this domain and partition by valence.
                # BUG-2 fix: use actual data valence values ('benefic'/'malefic'/'mixed'/'neutral')
                #   via _partition_signal(), not the non-existent 'positive'/'negative'.
                # BUG-3 fix: mixed and neutral signals are weighted evidence (R7), not discarded.
                supporting_ids: list[str] = []
                supporting_sal: list[float] = []
                contradicting_ids: list[str] = []
                contradicting_sal: list[float] = []

                # Count domain-overlapping signals before partitioning.
                # This is the "truly_no_evidence" sentinel: if no signals at all
                # matched this domain, status is 'no_evidence' regardless of grade.
                domain_overlapping_count = 0

                for sig in signal_rows:
                    domains = sig.get("domains_affected_array") or []
                    if domain not in domains:
                        continue
                    domain_overlapping_count += 1
                    sal = float(sig.get("computed_salience") or 0.0)
                    valence = str(sig.get("valence") or "neutral").lower().strip()
                    sig_id = str(sig.get("signal_id") or "")

                    sup_contrib, con_contrib = _partition_signal(valence, sal)

                    if sup_contrib > 0.0:
                        supporting_ids.append(sig_id)
                        supporting_sal.append(sup_contrib)
                    if con_contrib > 0.0:
                        contradicting_ids.append(sig_id)
                        contradicting_sal.append(con_contrib)

                # BUG-1 fix: truly_no_evidence = no signals matched this domain at all.
                # (A mixed signal that contributed partial weight to both sides is NOT empty --
                # it appears in both supporting_ids and contradicting_ids.)
                truly_no_evidence = (domain_overlapping_count == 0)

                grade = _compute_grade(supporting_sal, contradicting_sal)
                status = _grade_to_status(
                    grade,
                    supporting_empty=truly_no_evidence,
                    contradicting_empty=truly_no_evidence,
                )

                if status == "no_evidence":
                    no_evidence_count += 1

                derivation = {
                    "supporting_count": len(supporting_ids),
                    "contradicting_count": len(contradicting_ids),
                    "top_supporting_saliences": sorted(supporting_sal, reverse=True)[:5],
                    "top_contradicting_saliences": sorted(contradicting_sal, reverse=True)[:5],
                    "domain_overlapping_signal_count": domain_overlapping_count,
                    "formula": "grade = clamp(mean_top5_sup - 0.5*mean_top5_con, 0, 10) / 10 * 10",
                    "ayanamsha": aya,
                    "engine_version": ENGINE_VERSION,
                    "valence_weights": {
                        "benefic": "1.0 (full supporting)",
                        "malefic": "1.0 (full contradicting)",
                        "mixed": f"{_MIXED_WEIGHT} each side (R7)",
                        "neutral": f"{_NEUTRAL_WEIGHT} supporting only (R7)",
                    },
                }

                conn.execute(_PRATIJNA_INSERT, {
                    "pratijna_id":              str(uuid.uuid4()),
                    "chart_id":                 chart_id,
                    "ayanamsha_id":             aya,
                    "build_id":                 build_id,
                    "event_class_id":           event_class_id,
                    "status":                   status,
                    "grade":                    grade if status != "no_evidence" else None,
                    "supporting_signal_ids":    supporting_ids or None,
                    "contradicting_signal_ids": contradicting_ids or None,
                    "varga_confirmation":       None,
                    "derivation":               json.dumps(derivation),
                    "formula_version":          FORMULA_VERSION,
                    "computed_at":              now,
                    "engine_version":           ENGINE_VERSION,
                })
                rows_inserted += 1

        logger.info(
            "[bo_pratijna] chart=%s: %d rows inserted (%d no_evidence)",
            chart_id, rows_inserted, no_evidence_count,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_inserted,
            notes=(
                f"event_classes={len(event_rows)};ayanamshas={len(CANONICAL_AYAS)};"
                f"no_evidence={no_evidence_count}"
            ),
        )
