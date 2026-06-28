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
from datetime import date, timedelta

import psycopg

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
                # B5: enrich row with timing (window_start/end) + real domain before engine call
                enriched_row = self._enrich_discovery_row(conn, dict(row), chart_id)
                a = derive_anchor_from_discovery(enriched_row, ctx_n)
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
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
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
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
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
        # bodha_discoveries schema uses discovery_id, discovery_class, affected_domains_array,
        # composite_discovery_rank — alias to names the engine expects.
        # computed_at (aliased detected_at) + discovery_subsystem fetched for
        # B5 timing + domain enrichment.
        # Uses a SAVEPOINT so a load error here does not abort the outer transaction
        # and fail the whole asset (mirrors the 3 sibling loaders).
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_nimitta_disc")
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT d.discovery_id AS id,
                           NULL::uuid AS signal_id,
                           (d.affected_domains_array)[1] AS domain,
                           d.discovery_class AS discovery_type,
                           d.surface_depth_delta, d.why_an_acharya_misses_it,
                           d.falsifier_jsonb,
                           d.composite_discovery_rank AS confidence_score,
                           NULL::date AS peak_date,
                           NULL::date AS window_start,
                           NULL::date AS window_end,
                           d.computed_at AS detected_at,
                           d.discovery_subsystem,
                           d.cross_subsystem_root
                    FROM bodha_discoveries d
                    WHERE d.chart_id = %s
                    ORDER BY d.composite_discovery_rank DESC NULLS LAST
                    LIMIT %s
                    """,
                    (chart_id, _MAX_DISCOVERIES),
                )
                rows = cur.fetchall()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_nimitta_disc")
            return rows
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_nimitta_disc")
            except Exception:
                pass
            logger.warning("ph_nimitta: discoveries load skipped: %s", exc)
            return []

    def _load_signal_meta(self, conn, signal_ids: list[str]) -> dict[str, dict]:
        if not signal_ids:
            return {}
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT signal_id,
                       (domains_affected_array)[1] AS domain,
                       signature_class,
                       computed_salience AS salience_score
                FROM bodha_msr_signals
                WHERE signal_id = ANY(%s::uuid[])
                """,
                (signal_ids,),
            )
            return {str(r['signal_id']): dict(r) for r in cur.fetchall()}

    def _load_cgm_meta(self, conn, signal_ids: list[str]) -> dict:
        """Load chart-level CGM path metadata (Axis 3 causal chain).

        bodha_cgm_paths has no signal_id FK — paths are chart-level graha chains, not
        per-signal. Returns a chart-level aggregate dict (not per-signal).
        _build_ctx uses it as global context, not a per-signal lookup.
        Uses a SAVEPOINT so a missing-table error does not abort the outer transaction.
        """
        if not signal_ids:
            return {}
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_nimitta_cgm")
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT DISTINCT ON (p.path_id)
                           p.path_id, p.path_label_human,
                           p.path_length, p.is_final_dispositor
                    FROM bodha_cgm_paths p
                    WHERE p.chart_id = (
                        SELECT chart_id FROM bodha_msr_signals
                        WHERE signal_id = ANY(%s::uuid[]) LIMIT 1
                    )
                    ORDER BY p.path_id, p.path_length ASC
                    LIMIT 10
                    """,
                    (signal_ids,),
                )
                rows = cur.fetchall()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_nimitta_cgm")
            # CONTRACT-3 (A7→A5 fix): bodha_cgm_paths has no signal_id FK so the old
            # per-signal keyed dict (path_id → row) was never reachable via
            # cgm_meta.get(signal_id, {}). Return a chart-level aggregate instead;
            # _build_ctx passes it through as-is (chart-level, not per-signal).
            return {
                "path_count": len(rows),
                "paths": [dict(r) for r in rows],
                "has_final_dispositor": any(r['is_final_dispositor'] for r in rows),
                "max_path_length": max((r['path_length'] for r in rows), default=0),
            }
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_nimitta_cgm")
            except Exception:
                pass
            logger.debug("ph_nimitta: cgm_meta load skipped: %s", exc)
            return {}

    def _load_contradictions(self, conn, chart_id: str, signal_ids: list[str]) -> dict[str, dict]:
        if not signal_ids:
            return {}
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_nimitta_contra")
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                # bodha_contradictions: signal_a_id (not signal_id_a); no countervailing_thread/net_direction
                cur.execute(
                    """
                    SELECT c.signal_a_id,
                           c.tension_basis_jsonb->>'hint' AS countervailing_thread,
                           c.tension_class AS net_direction
                    FROM bodha_contradictions c
                    WHERE c.chart_id = %s
                      AND c.signal_a_id = ANY(%s::uuid[])
                    """,
                    (chart_id, signal_ids),
                )
                result = {str(r['signal_a_id']): dict(r) for r in cur.fetchall()}
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_nimitta_contra")
            return result
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_nimitta_contra")
            except Exception:
                pass
            logger.debug("ph_nimitta: contradictions load skipped: %s", exc)
            return {}

    def _load_precedent_refs(self, conn, chart_id: str, signal_ids: list[str]) -> dict[str, dict]:
        """Axis 5: nearest embedding neighbors (top-3 per signal)."""
        if not signal_ids:
            return {}
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_nimitta_prec")
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                # bodha_signal_embeddings: no domain column; just confirm signal existence
                cur.execute(
                    """
                    SELECT e.signal_id
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
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_nimitta_prec")
            return result
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_nimitta_prec")
            except Exception:
                pass
            logger.debug("ph_nimitta: precedent_refs load skipped: %s", exc)
            return {}

    # B5: subsystem → canonical domain mapping for discovery anchors.
    # Canonical domains (from engine.py derive_anchor_from_discovery):
    # career | relationship | financial | spiritual | health | transition | psychological
    _SUBSYSTEM_DOMAIN: dict[str, str] = {
        'yoga':          'spiritual',
        'graha':         'career',
        'bhava':         'career',
        'dasha':         'career',
        'transit':       'career',
        'nakshatra':     'psychological',   # nakshatra = character/psychological axis
        'divisional':    'career',
        'career':        'career',
        'wealth':        'financial',
        'health':        'health',
        'relationship':  'relationship',
        'marriage':      'relationship',
        'spiritual':     'spiritual',
        'dharma':        'spiritual',
        'psychology':    'psychological',
        'psychological': 'psychological',
        'financial':     'financial',
        'money':         'financial',
    }

    def _enrich_discovery_row(self, conn, row: dict, chart_id: str | None = None) -> dict:
        """B5: derive timing (window_start/end) + real domain for discovery-sourced rows.

        1. Domain: map discovery_subsystem / cross_subsystem_root → canonical domain;
           fall back to the row's own domain field (set by _load_discoveries from
           affected_domains_array). 'transition' is only used when nothing maps.
        2. Timing: use detected_at as window_start; window_end = detected_at + 90 days.
           Also attempt to find nearest kala_convergence row within 90 days to set
           convergence_id and borrow its peak_date.

        chart_id is passed explicitly from run() scope (IMPORTANT-1 fix: the discovery
        SELECT does not include chart_id so row.get('chart_id') was always None, causing
        the proximity lookup to be silently skipped 100% of the time).
        """
        # 1. Domain enrichment — avoid 'transition' when subsystem tells us better
        subsystem = (row.get('discovery_subsystem') or row.get('cross_subsystem_root') or '').lower()
        mapped_domain = self._SUBSYSTEM_DOMAIN.get(subsystem)
        if mapped_domain:
            row['domain'] = mapped_domain
        # If still 'transition' (or None) but the original affected_domains_array element
        # was something useful, it is already in row['domain'] from the query.

        # 2. Timing enrichment from detected_at
        detected_at = row.get('detected_at')
        if detected_at is not None:
            if isinstance(detected_at, str):
                try:
                    detected_at = date.fromisoformat(detected_at[:10])
                except ValueError:
                    detected_at = None

        if detected_at is not None:
            row['window_start'] = detected_at
            row['window_end']   = detected_at + timedelta(days=90)

            # 3. Proximity-match to kala_convergence for convergence_id + tighter peak_date
            try:
                with conn.cursor() as sp:
                    sp.execute("SAVEPOINT sp_nimitta_disc_conv")
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    # chart_id is now passed explicitly as a parameter (IMPORTANT-1 fix).
                    # The discovery SELECT does not include chart_id in its columns so
                    # row.get('chart_id') is always None — we use the caller-supplied value.
                    if chart_id:
                        cur.execute(
                            """
                            SELECT convergence_id, peak_date, domain
                            FROM kala_convergence
                            WHERE chart_id = %s
                              AND ABS(EXTRACT(EPOCH FROM (peak_date - %s::date))) < 7776000
                            ORDER BY ABS(EXTRACT(EPOCH FROM (peak_date - %s::date)))
                            LIMIT 1
                            """,
                            (chart_id, detected_at, detected_at),
                        )
                        conv_row = cur.fetchone()
                        if conv_row:
                            row['convergence_id'] = conv_row['convergence_id']
                            if conv_row.get('peak_date'):
                                row['peak_date'] = conv_row['peak_date']
                with conn.cursor() as sp:
                    sp.execute("RELEASE SAVEPOINT sp_nimitta_disc_conv")
            except Exception as exc:
                try:
                    with conn.cursor() as sp:
                        sp.execute("ROLLBACK TO SAVEPOINT sp_nimitta_disc_conv")
                except Exception:
                    pass
                logger.debug("ph_nimitta: discovery convergence proximity lookup skipped: %s", exc)

        return row

    def _build_ctx(self, row: dict, signal_meta, cgm_meta, contradiction_m, precedent_m) -> NimittaContext:
        sid = str(row.get('signal_id') or '')
        sm   = signal_meta.get(sid, {})
        # cgm_meta is a chart-level aggregate (not per-signal) — bodha_cgm_paths has no
        # signal_id FK so per-signal lookup was always a miss. Use directly as chart context.
        cgm  = cgm_meta  # type: dict (chart-level)
        cont = contradiction_m.get(sid, {})
        prec = precedent_m.get(sid, {})

        return NimittaContext(
            signal_domain=sm.get('domain'),
            signal_signature_class=sm.get('signature_class'),
            signal_salience=sm.get('salience_score'),
            cgm_path_ids=[p.get('path_id') for p in cgm.get('paths', [])],
            cgm_centrality=cgm.get('max_path_length'),
            root_graha=cgm.get('paths', [{}])[0].get('path_label_human') if cgm.get('paths') else None,
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
