"""
bo_pratijna — Promise Register (L2 Bodha)
==========================================
Reads bodha_msr_signals + brahma_event_ontology → writes bodha_pratijna.

For each event_class in brahma_event_ontology:
  1. Find signals whose domains_affected_array overlaps the event_class domain.
  2. Partition into supporting (positive valence, salience ≥ 0.3) and
     contradicting (negative valence, salience ≥ 0.3).
  3. grade = mean(top-5 supporting saliences) − 0.5 × mean(top-5 contradicting),
     normalized to [0, 10].
  4. status: 'promised' if grade ≥ 6.0, 'denied' if grade < 2.0, else 'conditional'.

Downstream: ph_nimitta (P5B) reads grade as promise_lift input.
JL-009 carry-forward: base-rate priors from brahma_event_ontology are surfaced
to the native at P5B before anchor freeze — not consumed here.

LIGHT writer: one run() call.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_pratijna_v1.0"
FORMULA_VERSION = "v1.0"

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

# Minimum salience for a signal to count as evidence
_MIN_SALIENCE = 0.3

# grade thresholds
_PROMISED_FLOOR = 6.0
_DENIED_CEIL = 2.0


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


def _compute_grade(supporting: list[float], contradicting: list[float]) -> float:
    """Grade in [0, 10]: mean of top-5 supporting − 0.5 × mean of top-5 contradicting."""
    top_sup = sorted(supporting, reverse=True)[:5]
    top_con = sorted(contradicting, reverse=True)[:5]
    sup_mean = sum(top_sup) / len(top_sup) if top_sup else 0.0
    con_mean = sum(top_con) / len(top_con) if top_con else 0.0
    raw = sup_mean - 0.5 * con_mean
    # Normalize: max possible raw ≈ 10 (empirical ceiling from v2 salience scale)
    normalized = min(max(raw * 5.0, 0.0), 10.0)
    return round(normalized, 3)


def _grade_to_status(grade: float) -> str:
    if grade >= _PROMISED_FLOOR:
        return "promised"
    if grade < _DENIED_CEIL:
        return "denied"
    return "conditional"


@register("bo_pratijna")
class BoPratijnaWriter(WriterBase):
    """bo_pratijna — Promise Register (L2 Bodha)."""

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config.get("chart_id")
        build_id = ctx.build_id
        conn = ctx.db_conn
        now = datetime.now(timezone.utc).isoformat()

        # Idempotency: delete prior rows for this chart
        conn.execute("DELETE FROM bodha_pratijna WHERE chart_id=%s", [chart_id])

        # Load event classes
        event_rows = [dict(r) for r in conn.execute(_FETCH_EVENT_CLASSES_SQL).fetchall()]
        if not event_rows:
            logger.warning("[bo_pratijna] no event classes found in brahma_event_ontology")
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes="no_event_classes")

        rows_inserted = 0

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

                # Find signals relevant to this domain
                supporting_ids: list[str] = []
                supporting_sal: list[float] = []
                contradicting_ids: list[str] = []
                contradicting_sal: list[float] = []

                for sig in signal_rows:
                    domains = sig.get("domains_affected_array") or []
                    if domain not in domains:
                        continue
                    sal = float(sig.get("computed_salience") or 0.0)
                    valence = str(sig.get("valence") or "neutral").lower()
                    sig_id = str(sig.get("signal_id") or "")
                    if valence in ("positive", "benefic"):
                        supporting_ids.append(sig_id)
                        supporting_sal.append(sal)
                    elif valence in ("negative", "malefic"):
                        contradicting_ids.append(sig_id)
                        contradicting_sal.append(sal)

                grade = _compute_grade(supporting_sal, contradicting_sal)
                status = _grade_to_status(grade)

                derivation = {
                    "supporting_count": len(supporting_ids),
                    "contradicting_count": len(contradicting_ids),
                    "top_supporting_saliences": sorted(supporting_sal, reverse=True)[:5],
                    "top_contradicting_saliences": sorted(contradicting_sal, reverse=True)[:5],
                    "formula": "grade = clamp(mean_top5_sup - 0.5*mean_top5_con, 0, 10) / 10 * 10",
                    "ayanamsha": aya,
                }

                conn.execute(_PRATIJNA_INSERT, {
                    "pratijna_id":              str(uuid.uuid4()),
                    "chart_id":                 chart_id,
                    "ayanamsha_id":             aya,
                    "build_id":                 build_id,
                    "event_class_id":           event_class_id,
                    "status":                   status,
                    "grade":                    grade,
                    "supporting_signal_ids":    supporting_ids or None,
                    "contradicting_signal_ids": contradicting_ids or None,
                    "varga_confirmation":       None,
                    "derivation":               json.dumps(derivation),
                    "formula_version":          FORMULA_VERSION,
                    "computed_at":              now,
                    "engine_version":           ENGINE_VERSION,
                })
                rows_inserted += 1

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_inserted,
            notes=f"event_classes={len(event_rows)};ayanamshas={len(CANONICAL_AYAS)}",
        )
