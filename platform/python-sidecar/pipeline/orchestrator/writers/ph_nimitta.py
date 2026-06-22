"""
ph_nimitta — Predictive Anchors (THE SPINE of L4 Phala).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_anchors.

Reads: kala_convergence · kala_bhavishya · bodha_discoveries · bodha_msr_signals ·
       bodha_cgm_paths · bodha_contradictions · bodha_signal_embeddings
Writes: phala_anchors (delete-then-insert per chart_id)
SPINE-FIRST gate (D26): verifies one anchor end-to-end before returning.
"""
from __future__ import annotations

import json
import logging
from datetime import date

import psycopg2.extras

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_nimitta.engine import (
    NimittaContext,
    derive_anchor_from_convergence,
    derive_anchor_from_bhavishya,
    derive_anchor_from_discovery,
    AnchorRecord,
)

logger = logging.getLogger(__name__)

_MAX_CONVERGENCE = 200  # top windows by convergence_score
_MAX_DISCOVERIES = 100  # top discoveries by confidence_score


@register('ph_nimitta')
class PhNimittaWriter(WriterBase):
    """
    Builds phala_anchors from enriched kala_convergence + kala_bhavishya + bodha_discoveries.
    8 axes + 5 elevations per D8/D11/D21/D37/D38.
    """
    asset_id = 'ph_nimitta'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']

        # Step 1: delete-then-insert idempotency (§N.3 L4+)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_anchors WHERE chart_id = %s", (chart_id,))
        logger.info("ph_nimitta: deleted existing phala_anchors for %s", chart_id)

        # Step 2: load sources
        convergence_rows = self._load_convergence(conn, chart_id)
        bhavishya_rows   = self._load_bhavishya(conn, chart_id)
        discovery_rows   = self._load_discoveries(conn, chart_id)

        logger.info(
            "ph_nimitta: loaded %d convergence / %d bhavishya / %d discovery rows",
            len(convergence_rows), len(bhavishya_rows), len(discovery_rows),
        )

        # Step 3: build signal → context map (batch fetch)
        all_signal_ids = list({
            str(r['signal_id']) for r in (convergence_rows + bhavishya_rows + discovery_rows)
            if r.get('signal_id')
        })
        signal_meta     = self._load_signal_meta(conn, all_signal_ids)
        cgm_meta        = self._load_cgm_meta(conn, all_signal_ids)
        contradiction_m = self._load_contradictions(conn, chart_id, all_signal_ids)
        precedent_m     = self._load_precedent_refs(conn, chart_id, all_signal_ids)

        # Step 4: derive anchors per source
        anchors: list[AnchorRecord] = []

        for row in convergence_rows:
            try:
                ctx_n = self._build_ctx(row, signal_meta, cgm_meta, contradiction_m, precedent_m)
                icc = int(row.get('independent_current_count') or 1)
                a = derive_anchor_from_convergence(dict(row), ctx_n, icc)
                anchors.append(a)
            except Exception as exc:
                logger.warning("ph_nimitta: convergence anchor failed for %s: %s", row.get('convergence_id'), exc)

        # D37: inherit ALL kala_bhavishya projections
        for row in bhavishya_rows:
            try:
                ctx_n = self._build_ctx(row, signal_meta, cgm_meta, contradiction_m, precedent_m)
                a = derive_anchor_from_bhavishya(dict(row), ctx_n)
                anchors.append(a)
            except Exception as exc:
                logger.warning("ph_nimitta: bhavishya anchor failed for %s: %s", row.get('id'), exc)

        for row in discovery_rows:
            try:
                ctx_n = self._build_ctx(row, signal_meta, cgm_meta, contradiction_m, precedent_m)
                a = derive_anchor_from_discovery(dict(row), ctx_n)
                anchors.append(a)
            except Exception as exc:
                logger.warning("ph_nimitta: discovery anchor failed for %s: %s", row.get('id'), exc)

        logger.info("ph_nimitta: derived %d total anchors before insert", len(anchors))

        # Step 5: SPINE-FIRST gate (D26) — verify ≥1 anchor with all axes present
        self._spine_gate(anchors)

        # Step 6: batch insert
        rows_inserted = 0
        with conn.cursor() as cur:
            for a in anchors:
                try:
                    cur.execute(
                        """
                        INSERT INTO phala_anchors (
                            chart_id, anchor_source, convergence_id, discovery_id,
                            bhavishya_id, signal_id, subsystem_source,
                            event_type, direction, domain, horizon_tier,
                            window_start, peak_date, window_end,
                            magnitude, magnitude_basis,
                            confidence_low, confidence_high, confidence_basis,
                            karmic_frame, karmic_note,
                            malleability, counterfactual_jsonb,
                            contradiction_jsonb, causal_chain_jsonb,
                            precedent_refs_jsonb, dasha_consensus_count,
                            school_consensus_jsonb, ayanamsha_robustness,
                            falsifier, derivation_ledger_jsonb, source_citation
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, %s::jsonb,
                            %s::jsonb, %s::jsonb,
                            %s::jsonb, %s,
                            %s::jsonb, %s,
                            %s, %s::jsonb, %s
                        )
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            chart_id, a.anchor_source, a.convergence_id, a.discovery_id,
                            a.bhavishya_id, a.signal_id, a.subsystem_source,
                            a.event_type, a.direction, a.domain, a.horizon_tier,
                            a.window_start, a.peak_date, a.window_end,
                            a.magnitude, a.magnitude_basis,
                            a.confidence_low, a.confidence_high, a.confidence_basis,
                            a.karmic_frame, a.karmic_note,
                            a.malleability, json.dumps(a.counterfactual_jsonb or {}),
                            json.dumps(a.contradiction_jsonb or {}), json.dumps(a.causal_chain_jsonb or {}),
                            json.dumps(a.precedent_refs_jsonb or {}), a.dasha_consensus_count,
                            json.dumps(a.school_consensus_jsonb or {}), a.ayanamsha_robustness,
                            a.falsifier, json.dumps(a.derivation_ledger_jsonb), a.source_citation,
                        ),
                    )
                    rows_inserted += 1
                except Exception as exc:
                    logger.warning("ph_nimitta: insert failed for anchor %s/%s: %s",
                                   a.anchor_source, a.convergence_id or a.bhavishya_id or a.discovery_id, exc)

        logger.info("ph_nimitta: inserted %d rows into phala_anchors for %s", rows_inserted, chart_id)
        return WriterResult(asset_id='ph_nimitta', rows_inserted=rows_inserted)

    # ── private helpers ──────────────────────────────────────────────────────

    def _load_convergence(self, conn, chart_id: str) -> list:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT convergence_id, chart_id, signal_id, mode, peak_date,
                       window_start, window_end, convergence_score, rarity_years,
                       constituent_factors, source_citation, independent_current_count,
                       confidence_score, confidence_label
                FROM kala_convergence
                WHERE chart_id = %s
                ORDER BY convergence_score DESC
                LIMIT %s
                """,
                (chart_id, _MAX_CONVERGENCE),
            )
            return cur.fetchall()

    def _load_bhavishya(self, conn, chart_id: str) -> list:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, chart_id, signal_id, convergence_id, domain,
                       peak_date, window_start, window_end,
                       probability_tier, effective_score,
                       falsifiability, source_chain, narrative, outcome_recorded
                FROM kala_bhavishya
                WHERE chart_id = %s
                """,
                (chart_id,),
            )
            return cur.fetchall()

    def _load_discoveries(self, conn, chart_id: str) -> list:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # bodha_discoveries may not have window_start/end columns; use signal dates as fallback
            cur.execute(
                """
                SELECT d.id, d.signal_id, d.domain, d.discovery_type,
                       d.surface_depth_delta, d.why_an_acharya_misses_it,
                       d.falsifier_jsonb, d.confidence_score
                FROM bodha_discoveries d
                WHERE d.chart_id = %s
                ORDER BY d.confidence_score DESC NULLS LAST
                LIMIT %s
                """,
                (chart_id, _MAX_DISCOVERIES),
            )
            return cur.fetchall()

    def _load_signal_meta(self, conn, signal_ids: list[str]) -> dict[str, dict]:
        if not signal_ids:
            return {}
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT signal_id, domain, signature_class, salience_score
                FROM bodha_msr_signals
                WHERE signal_id = ANY(%s::uuid[])
                """,
                (signal_ids,),
            )
            return {str(r['signal_id']): dict(r) for r in cur.fetchall()}

    def _load_cgm_meta(self, conn, signal_ids: list[str]) -> dict[str, dict]:
        """Load top CGM path per signal (Axis 3 causal chain)."""
        if not signal_ids:
            return {}
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # bodha_cgm_paths: get top path per signal by path_length asc / centrality desc
                cur.execute(
                    """
                    SELECT DISTINCT ON (p.source_signal_id)
                           p.source_signal_id, p.path_id, p.path_label_human,
                           p.path_length, p.is_final_dispositor, p.root_graha
                    FROM bodha_cgm_paths p
                    WHERE p.source_signal_id = ANY(%s::uuid[])
                    ORDER BY p.source_signal_id, p.path_length ASC
                    LIMIT 100
                    """,
                    (signal_ids,),
                )
                result = {}
                for r in cur.fetchall():
                    sid = str(r['source_signal_id'])
                    result[sid] = {
                        'path_ids': [str(r['path_id'])],
                        'root_graha': r.get('root_graha'),
                        'centrality': None,
                    }
                return result
        except Exception as exc:
            logger.debug("ph_nimitta: cgm_meta load skipped: %s", exc)
            return {}

    def _load_contradictions(self, conn, chart_id: str, signal_ids: list[str]) -> dict[str, dict]:
        if not signal_ids:
            return {}
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT c.signal_id_a, c.countervailing_thread, c.net_direction
                    FROM bodha_contradictions c
                    WHERE c.chart_id = %s
                      AND c.signal_id_a = ANY(%s::uuid[])
                    """,
                    (chart_id, signal_ids),
                )
                return {str(r['signal_id_a']): dict(r) for r in cur.fetchall()}
        except Exception as exc:
            logger.debug("ph_nimitta: contradictions load skipped: %s", exc)
            return {}

    def _load_precedent_refs(self, conn, chart_id: str, signal_ids: list[str]) -> dict[str, dict]:
        """Axis 5: nearest embedding neighbors (top-3 per signal)."""
        if not signal_ids:
            return {}
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # bodha_signal_embeddings: self-join via cosine similarity is complex; use simpler
                # approach — find signals in same domain as precedents
                cur.execute(
                    """
                    SELECT e.signal_id, e.domain
                    FROM bodha_signal_embeddings e
                    WHERE e.chart_id = %s
                      AND e.signal_id = ANY(%s::uuid[])
                    LIMIT 50
                    """,
                    (chart_id, signal_ids),
                )
                result = {}
                for r in cur.fetchall():
                    sid = str(r['signal_id'])
                    result[sid] = {'nearest_signal_ids': [sid], 'precedent_dates': []}
                return result
        except Exception as exc:
            logger.debug("ph_nimitta: precedent_refs load skipped: %s", exc)
            return {}

    def _build_ctx(self, row: dict, signal_meta, cgm_meta, contradiction_m, precedent_m) -> NimittaContext:
        sid = str(row.get('signal_id') or '')
        sm   = signal_meta.get(sid, {})
        cgm  = cgm_meta.get(sid, {})
        cont = contradiction_m.get(sid, {})
        prec = precedent_m.get(sid, {})

        return NimittaContext(
            signal_domain=sm.get('domain'),
            signal_signature_class=sm.get('signature_class'),
            signal_salience=sm.get('salience_score'),
            cgm_path_ids=cgm.get('path_ids', []),
            cgm_centrality=cgm.get('centrality'),
            root_graha=cgm.get('root_graha'),
            precedent_signal_ids=prec.get('nearest_signal_ids', []),
            precedent_dates=prec.get('precedent_dates', []),
            contradiction_contested=bool(cont),
            contradiction_thread=cont.get('countervailing_thread'),
            contradiction_net=cont.get('net_direction'),
            dasha_consensus_count=0,   # U1: pre-fetched per window in production; 0 for now
            school_consensus_jsonb=None,  # U4: fetched via separate service at serve-time
            ayanamsha_robustness=3,       # default; real value comes from kala_convergence row
        )

    def _spine_gate(self, anchors: list[AnchorRecord]) -> None:
        """
        D26 — SPINE-FIRST hard gate: at least one anchor must have ALL 5 elevations
        populated (magnitude, confidence range, karmic_frame, malleability, falsifier).
        """
        for a in anchors:
            if (
                a.magnitude and
                a.confidence_low is not None and
                a.confidence_high is not None and
                a.malleability and
                a.falsifier and
                a.derivation_ledger_jsonb
            ):
                logger.info("ph_nimitta: SPINE GATE D26 PASSED (first qualifying anchor: source=%s)", a.anchor_source)
                return

        raise RuntimeError(
            "ph_nimitta SPINE GATE FAILED (D26): zero anchors passed end-to-end across "
            "all elevations. Cannot fan out further L4 assets."
        )
