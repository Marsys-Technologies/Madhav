"""
ph_phaladesa — Domain Result Declaration (L4 Phala wave 7).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_phaladesa.

B.11 WHOLE-CHART-READ: writer reads L2 Bodha synthesis (MSR, CDLM, CGM)
before building domain declarations.

MODEL POLICY: writer emits a DETERMINISTIC template narration (§N.4 deterministic-
first) — narration_status='ready', narration_jsonb populated from the computed
record, narration_model=NULL (no LLM). Any FUTURE generative-LLM enrichment remains
a separate step restricted to Gemini/DeepSeek; Anthropic is BANNED and
validate_narration_model() enforces the allowlist. (WP-2.2/LCA-5: previously every
row sat at status='pending' / narration_jsonb=NULL because that async step never ran.)

Reads: phala_anchors · phala_suddha_sodhana · phala_sodhana (flag counts)
       phala_sankrama (spillovers) · phala_mitigation (domains covered)
       phala_muhurta (domains covered) · phala_pramana (window status)
       bodha_msr_signals (B.11) · bodha_cdlm_cells (B.11) · bodha_cgm_edges (B.11)
Writes: phala_phaladesa (delete-then-insert per chart_id)
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import date

import psycopg


class _UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_phaladesa.engine import (
    DomainAnchorSummary,
    SpilloverSummary,
    BodhaSynthesisContext,
    PhaladesakContext,
    validate_narration_model,
    derive_phaladesa_for_chart,
    _ALL_DOMAINS,
)

logger = logging.getLogger(__name__)

# phala_anchors domain vocabulary → phala_phaladesa_domain_canonical (CDLM vocab)
_ANCHOR_TO_PHALADESA_DOMAIN: dict[str, str] = {
    'financial':    'wealth',
    'spiritual':    'spirituality',
    'psychological': 'character',
}

# WP-2.2 / LCA-5: deterministic narration.
# The async LLM narration step (Gemini/DeepSeek) was never wired, so every row sat
# at narration_status='pending' / narration_jsonb=NULL. Per §N.4 (deterministic-first)
# we verbalize the ALREADY-COMPUTED structured phaladesa fields into a template
# narration — NO generative LLM, no new interpretation (B.1/B.10): the text asserts
# only what magnitude/window/confidence/malleability/mitigation/spillover/pramana
# already state. narration_model stays NULL (its CHECK allowlist is LLM-only); the
# deterministic method is recorded inside narration_jsonb.
_NARRATION_METHOD = "deterministic_template_v1"

# F18 fix (SAMAPTI B-NAR-PH, seed F18 CONFIRMED §3): _ALL_DOMAINS (engine.py) is the
# authoritative emission set. Before this fix, 'transition' — a real _ALL_DOMAINS
# member — had no entry here, so the `.get(domain, domain)` fallback in
# _build_deterministic_narration emitted the raw slug "transition" mid-sentence
# instead of a proper label; 'general' had an entry but is never emitted by
# _ALL_DOMAINS (dead config, kept below — harmless, and removing it is not what
# the finding is about). _DOMAIN_LABEL must cover every _ALL_DOMAINS member.
_DOMAIN_LABEL: dict[str, str] = {
    'career': 'career and profession', 'wealth': 'wealth and finances',
    'health': 'health and vitality', 'relationship': 'relationships and marriage',
    'spirituality': 'spirituality and dharma', 'character': 'character and psychology',
    'transition': 'transition and change', 'general': 'general life-arc',
}


def _build_deterministic_narration(rec) -> dict:
    """Template narration from the computed phaladesa record. Deterministic; no LLM."""
    domain_label = _DOMAIN_LABEL.get(str(rec.domain), str(rec.domain))
    mag = rec.magnitude or 'moderate'
    mall = (rec.malleability or 'semi_influenceable').replace('_', '-')

    parts: list[str] = []
    if rec.anchor_count:
        parts.append(
            f"The {domain_label} domain rests on {rec.anchor_count} predictive anchor(s), "
            f"of which {rec.clean_anchor_count} passed clean sodhana review."
        )
    else:
        parts.append(f"No predictive anchors were derived for the {domain_label} domain in this build.")

    if rec.magnitude:
        parts.append(f"The assessed magnitude of effect is {mag}.")

    if rec.prediction_window_start and rec.prediction_window_end:
        win = f"{rec.prediction_window_start} to {rec.prediction_window_end}"
        if rec.peak_date:
            parts.append(f"The active window runs {win}, peaking around {rec.peak_date}.")
        else:
            parts.append(f"The active window runs {win}.")

    if rec.confidence_low is not None and rec.confidence_high is not None:
        parts.append(
            f"Confidence band spans {rec.confidence_low}–{rec.confidence_high}; "
            f"the outcome is classed as {mall}."
        )

    if rec.mitigation_available:
        parts.append("Remedial mitigation is available for this domain.")
    if rec.muhurta_available:
        parts.append("Supportive muhurta windows have been identified.")

    if getattr(rec, 'incoming_spillover_count', 0):
        parts.append(
            f"{rec.incoming_spillover_count} cross-domain spillover(s) feed into this domain."
        )

    if rec.pramana_window_status:
        parts.append(f"Falsifiability status: {rec.pramana_window_status}.")

    contradiction = rec.contradiction_summary_jsonb
    if contradiction:
        n = len(contradiction) if isinstance(contradiction, (list, dict)) else 0
        if n:
            parts.append(f"{n} contradiction signal(s) temper this reading and warrant caution.")

    return {
        "language": "en",
        "text": " ".join(parts),
        "method": _NARRATION_METHOD,
        "model": None,
        "prompt_hash": None,
        "generated_at": date.today().isoformat(),
    }


@register('ph_phaladesa')
class PhPhaladesakWriter(WriterBase):
    """
    Builds phala_phaladesa: 7 domain declarations per chart.
    Writer is B.11 compliant: always reads Bodha synthesis before building.
    Writer never calls an LLM: narration_status='pending', narration_model=NULL.
    """
    asset_id = 'ph_phaladesa'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']

        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 0")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_phaladesa WHERE chart_id = %s", (chart_id,))

        # B.11: read Bodha synthesis first
        bodha = self._load_bodha_synthesis(conn, chart_id)
        if not bodha.bodha_consulted:
            logger.warning("ph_phaladesa: Bodha synthesis unavailable for %s — B.11 soft miss", chart_id)

        domain_summaries = self._load_domain_summaries(conn, chart_id)
        spillovers       = self._load_spillovers(conn, chart_id)
        mitigation_d     = self._load_covered_domains(conn, chart_id, 'phala_mitigation')
        muhurta_d        = self._load_covered_domains(conn, chart_id, 'phala_muhurta')

        logger.info(
            "ph_phaladesa: %d domain summaries / %d spillovers / bodha=%s",
            len(domain_summaries), len(spillovers), bodha.bodha_consulted,
        )

        pctx = PhaladesakContext(
            chart_id=chart_id,
            domain_summaries=domain_summaries,
            spillovers=spillovers,
            mitigation_domains=mitigation_d,
            muhurta_domains=muhurta_d,
            bodha=bodha,
        )

        records = derive_phaladesa_for_chart(pctx)

        rows_inserted = 0
        with conn.cursor() as cur:
            for rec in records:
                # Model policy gate. rec.narration_model stays None (no LLM); the
                # deterministic narration records its method inside narration_jsonb.
                validate_narration_model(rec.narration_model)  # None → passes (no LLM used)
                narration = _build_deterministic_narration(rec)

                cur.execute(
                    """
                    INSERT INTO phala_phaladesa (
                        chart_id, domain,
                        anchor_count, clean_anchor_count,
                        staged_revision_count, anomaly_flag_count,
                        top_anchor_id,
                        prediction_window_start, prediction_window_end, peak_date,
                        magnitude, confidence_low, confidence_high, malleability,
                        spillover_domains_jsonb, incoming_spillover_count,
                        mitigation_available, muhurta_available,
                        pramana_window_status, evidence_type,
                        precedent_refs_jsonb, contradiction_summary_jsonb,
                        derivation_summary_jsonb,
                        narration_status, narration_model, narration_jsonb,
                        derivation_ledger_jsonb, source_citation
                    ) VALUES (
                        %s, %s,
                        %s, %s,
                        %s, %s,
                        %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s::jsonb, %s,
                        %s, %s,
                        %s, %s,
                        %s::jsonb, %s::jsonb,
                        %s::jsonb,
                        %s, NULL, %s::jsonb,
                        %s::jsonb, %s
                    )
                    ON CONFLICT (chart_id, domain) DO UPDATE SET
                        narration_status            = EXCLUDED.narration_status,
                        narration_jsonb             = EXCLUDED.narration_jsonb,
                        anchor_count                = EXCLUDED.anchor_count,
                        clean_anchor_count          = EXCLUDED.clean_anchor_count,
                        staged_revision_count       = EXCLUDED.staged_revision_count,
                        anomaly_flag_count          = EXCLUDED.anomaly_flag_count,
                        top_anchor_id               = EXCLUDED.top_anchor_id,
                        prediction_window_start     = EXCLUDED.prediction_window_start,
                        prediction_window_end       = EXCLUDED.prediction_window_end,
                        peak_date                   = EXCLUDED.peak_date,
                        magnitude                   = EXCLUDED.magnitude,
                        confidence_low              = EXCLUDED.confidence_low,
                        confidence_high             = EXCLUDED.confidence_high,
                        malleability                = EXCLUDED.malleability,
                        spillover_domains_jsonb     = EXCLUDED.spillover_domains_jsonb,
                        incoming_spillover_count    = EXCLUDED.incoming_spillover_count,
                        mitigation_available        = EXCLUDED.mitigation_available,
                        muhurta_available           = EXCLUDED.muhurta_available,
                        pramana_window_status       = EXCLUDED.pramana_window_status,
                        evidence_type               = EXCLUDED.evidence_type,
                        precedent_refs_jsonb        = EXCLUDED.precedent_refs_jsonb,
                        contradiction_summary_jsonb = EXCLUDED.contradiction_summary_jsonb,
                        derivation_summary_jsonb    = EXCLUDED.derivation_summary_jsonb,
                        derivation_ledger_jsonb     = EXCLUDED.derivation_ledger_jsonb,
                        source_citation             = EXCLUDED.source_citation,
                        computed_at                 = now()
                    """,
                    (
                        chart_id, rec.domain,
                        rec.anchor_count, rec.clean_anchor_count,
                        rec.staged_revision_count, rec.anomaly_flag_count,
                        rec.top_anchor_id,
                        rec.prediction_window_start, rec.prediction_window_end, rec.peak_date,
                        rec.magnitude, rec.confidence_low, rec.confidence_high, rec.malleability,
                        json.dumps(rec.spillover_domains_jsonb, cls=_UUIDEncoder) if rec.spillover_domains_jsonb else None,
                        rec.incoming_spillover_count,
                        rec.mitigation_available, rec.muhurta_available,
                        rec.pramana_window_status, rec.evidence_type,
                        json.dumps(rec.precedent_refs_jsonb, cls=_UUIDEncoder) if rec.precedent_refs_jsonb else None,
                        json.dumps(rec.contradiction_summary_jsonb, cls=_UUIDEncoder) if rec.contradiction_summary_jsonb else None,
                        json.dumps(rec.derivation_summary_jsonb, cls=_UUIDEncoder),
                        'ready',  # deterministic narration is ready (no async LLM step)
                        json.dumps(narration, cls=_UUIDEncoder),
                        json.dumps(rec.derivation_ledger_jsonb, cls=_UUIDEncoder), rec.source_citation,
                    ),
                )
                rows_inserted += 1

        logger.info("ph_phaladesa: inserted %d rows for %s", rows_inserted, chart_id)
        return WriterResult(asset_id='ph_phaladesa', rows_inserted=rows_inserted)

    def _load_bodha_synthesis(self, conn, chart_id: str) -> BodhaSynthesisContext:
        """B.11: pre-fetch Bodha MSR + CDLM + CGM before any derivation."""
        bctx = BodhaSynthesisContext()
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_phaladesa_bodha")
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM bodha_msr_signals WHERE chart_id = %s",
                    (chart_id,),
                )
                count = cur.fetchone()["count"]
                bctx.bodha_consulted = count > 0

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT (domains_affected_array)[1] AS signal_domain_primary,
                           AVG(computed_salience) AS score
                    FROM bodha_msr_signals WHERE chart_id = %s
                    GROUP BY (domains_affected_array)[1]
                    """,
                    (chart_id,),
                )
                for r in cur.fetchall():
                    if r["signal_domain_primary"]:
                        bctx.msr_domain_scores[str(r["signal_domain_primary"]).lower()] = float(r["score"] or 0.0)
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_phaladesa_bodha")
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_phaladesa_bodha")
            except Exception:
                pass
            logger.debug("ph_phaladesa: Bodha load skipped: %s", exc)
        return bctx

    def _load_domain_summaries(self, conn, chart_id: str) -> dict[str, DomainAnchorSummary]:
        """Load phala_anchors + suddha_sodhana disposition + pramana status per domain."""
        summaries: dict[str, DomainAnchorSummary] = {}
        try:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        pa.anchor_id, pa.domain, pa.magnitude, pa.confidence_low,
                        pa.confidence_high, pa.malleability, pa.window_start,
                        pa.window_end, pa.peak_date, pa.precedent_refs_jsonb,
                        pa.contradiction_jsonb,
                        COALESCE(ss.cleanliness_status, 'unknown') AS clean_status,
                        COALESCE(ss.critical_flag_count, 0) + COALESCE(ss.major_flag_count, 0)
                            + COALESCE(ss.minor_flag_count, 0) AS flag_count,
                        pr.window_status AS pramana_status,
                        pr.evidence_type AS pramana_evidence_type
                    FROM phala_anchors pa
                    LEFT JOIN phala_suddha_sodhana ss ON ss.anchor_id = pa.anchor_id
                    LEFT JOIN phala_pramana pr ON pr.anchor_id = pa.anchor_id
                    WHERE pa.chart_id = %s
                    ORDER BY pa.domain, pa.confidence_high DESC NULLS LAST
                    """,
                    (chart_id,),
                )
                for r in cur.fetchall():
                    d = _ANCHOR_TO_PHALADESA_DOMAIN.get(str(r['domain']).lower(), str(r['domain']).lower())
                    if d not in summaries:
                        summaries[d] = DomainAnchorSummary(domain=d)
                    s = summaries[d]
                    aid = str(r['anchor_id'])
                    s.anchor_ids.append(aid)
                    s.anomaly_flag_count += int(r.get('flag_count') or 0)
                    cs = str(r.get('clean_status') or '')
                    if cs == 'clean':
                        s.clean_ids.append(aid)
                    elif cs == 'staged_revision':
                        s.staged_revision_ids.append(aid)
                    # Set top anchor from first (highest confidence) row per domain
                    if s.top_anchor_id is None:
                        s.top_anchor_id   = aid
                        s.window_start    = r.get('window_start')
                        s.window_end      = r.get('window_end')
                        s.peak_date       = r.get('peak_date')
                        s.magnitude       = r.get('magnitude')
                        s.confidence_low  = float(r['confidence_low']) if r.get('confidence_low') is not None else None
                        s.confidence_high = float(r['confidence_high']) if r.get('confidence_high') is not None else None
                        s.malleability    = r.get('malleability')
                        s.pramana_window_status = r.get('pramana_status')
                        s.evidence_type         = r.get('pramana_evidence_type')
                        # P1-b fix (SAMAPTI B-NAR-PH): pa.precedent_refs_jsonb and
                        # pa.contradiction_jsonb are SELECTed above (:317-321) but were
                        # never assigned onto the summary — so PhaladosaRecord.contradiction_
                        # summary_jsonb / precedent_refs_jsonb were always None and the
                        # narration builder's "N contradiction signal(s)" branch
                        # (_build_deterministic_narration :121-125) was dead code on every
                        # build, regardless of real phala_anchors data.
                        s.precedent_refs_jsonb  = r.get('precedent_refs_jsonb')
                        s.contradiction_summary = r.get('contradiction_jsonb')
        except Exception as exc:
            logger.debug("ph_phaladesa: domain summaries load skipped: %s", exc)
        return summaries

    def _load_spillovers(self, conn, chart_id: str) -> list[SpilloverSummary]:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT source_domain, target_domain, relationship_type, spillover_confidence
                    FROM phala_sankrama
                    WHERE chart_id = %s
                    ORDER BY spillover_confidence DESC
                    """,
                    (chart_id,),
                )
                return [
                    SpilloverSummary(
                        source_domain=str(r['source_domain']),
                        target_domain=str(r['target_domain']),
                        relationship_type=str(r['relationship_type']),
                        spillover_confidence=float(r['spillover_confidence'] or 0.0),
                    )
                    for r in cur.fetchall()
                ]
        except Exception as exc:
            logger.debug("ph_phaladesa: spillovers load skipped: %s", exc)
            return []

    def _load_covered_domains(self, conn, chart_id: str, table: str) -> set[str]:
        """Return set of domains that have at least one row in the given phala_* table."""
        try:
            with conn.cursor() as cur:
                # Both phala_mitigation (via anchor domain) and phala_muhurta (via action_class)
                # are linked indirectly via phala_anchors; use linked_anchor_id join
                if table == 'phala_muhurta':
                    cur.execute(
                        """
                        SELECT DISTINCT pa.domain
                        FROM phala_muhurta pm
                        JOIN phala_anchors pa ON pa.anchor_id = pm.linked_anchor_id::uuid
                        WHERE pm.chart_id = %s
                        """,
                        (chart_id,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT DISTINCT pa.domain
                        FROM phala_mitigation pm
                        JOIN phala_anchors pa ON pa.anchor_id = pm.linked_anchor_id::uuid
                        WHERE pm.chart_id = %s
                        """,
                        (chart_id,),
                    )
                return {_ANCHOR_TO_PHALADESA_DOMAIN.get(str(r['domain']).lower(), str(r['domain']).lower()) for r in cur.fetchall()}
        except Exception as exc:
            logger.debug("ph_phaladesa: %s domain coverage load skipped: %s", table, exc)
            return set()
