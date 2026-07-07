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
from datetime import date, datetime, timedelta
from typing import Optional

import psycopg

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_nimitta.base_rate import base_rate_for_age
from services.ph_nimitta.engine import (
    NimittaContext,
    AnchorRecord,
    derive_anchor_from_convergence,
    derive_anchor_from_bhavishya,
    derive_anchor_from_discovery,
)

logger = logging.getLogger(__name__)

_MAX_CONVERGENCE = 200  # top windows by convergence_score
_MAX_DISCOVERIES = 100  # top discoveries by confidence_score


def _parse_iso_date(v) -> Optional[date]:
    """Coerce a psycopg date/datetime or ISO string to a date; None on failure."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except Exception:
        return None


def _parse_birth_date(birth_params) -> Optional[date]:
    """Native birth date from ctx.config['birth_params']['datetime_iso']."""
    if not isinstance(birth_params, dict):
        return None
    return _parse_iso_date(birth_params.get('datetime_iso'))


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
        # JL-009 point-2: birth date drives the age-band base_rate lookup (per anchor).
        self._birth_date = _parse_birth_date(ctx.config.get('birth_params'))

        # Step 1: disable statement timeout + delete-then-insert idempotency (§N.3 L4+)
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 0")
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
        posterior_m     = self._load_posterior_meta(conn, chart_id, signal_meta)

        # Step 4: derive anchors per source
        anchors: list[AnchorRecord] = []

        for row in convergence_rows:
            try:
                ctx_n = self._build_ctx(row, signal_meta, cgm_meta, contradiction_m, precedent_m, posterior_m)
                icc = int(row.get('independent_current_count') or 1)
                a = derive_anchor_from_convergence(dict(row), ctx_n, icc)
                anchors.append(a)
            except Exception as exc:
                logger.warning("ph_nimitta: convergence anchor failed for %s: %s", row.get('convergence_id'), exc)

        # D37: inherit ALL kala_bhavishya projections
        for row in bhavishya_rows:
            try:
                ctx_n = self._build_ctx(row, signal_meta, cgm_meta, contradiction_m, precedent_m, posterior_m)
                a = derive_anchor_from_bhavishya(dict(row), ctx_n)
                anchors.append(a)
            except Exception as exc:
                logger.warning("ph_nimitta: bhavishya anchor failed for %s: %s", row.get('id'), exc)

        for row in discovery_rows:
            try:
                # B5: enrich row with timing (window_start/end) + real domain FIRST so the
                # age-band base_rate lookup (JL-009 point-2) sees the discovery's window_start.
                enriched_row = self._enrich_discovery_row(conn, dict(row), chart_id)
                ctx_n = self._build_ctx(enriched_row, signal_meta, cgm_meta, contradiction_m, precedent_m, posterior_m)
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
                cur.execute(
                    """
                    INSERT INTO phala_anchors (
                        chart_id, anchor_source, convergence_id, discovery_id,
                        bhavishya_id, signal_id, subsystem_source,
                        event_type, direction, domain, horizon_tier,
                        window_start, peak_date, window_end,
                        magnitude, magnitude_basis,
                        confidence_low, confidence_high, confidence_basis,
                        posterior, lift_vector_jsonb, structured_falsifier_jsonb,
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
                        %s, %s::jsonb, %s::jsonb,
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
                        a.posterior, json.dumps(a.lift_vector or {}), json.dumps(a.structured_falsifier or {}),
                        a.karmic_frame, a.karmic_note,
                        a.malleability, json.dumps(a.counterfactual_jsonb or {}),
                        json.dumps(a.contradiction_jsonb or {}), json.dumps(a.causal_chain_jsonb or {}),
                        json.dumps(a.precedent_refs_jsonb or {}), a.dasha_consensus_count,
                        json.dumps(a.school_consensus_jsonb or {}), a.ayanamsha_robustness,
                        a.falsifier, json.dumps(a.derivation_ledger_jsonb), a.source_citation,
                    ),
                )
                rows_inserted += 1

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
                       ayanamsha_id,
                       (domains_affected_array)[1] AS domain,
                       signature_class,
                       computed_salience AS salience_score
                FROM bodha_msr_signals
                WHERE signal_id = ANY(%s::uuid[])
                """,
                (signal_ids,),
            )
            return {str(r['signal_id']): dict(r) for r in cur.fetchall()}

    def _load_posterior_meta(self, conn, chart_id: str, signal_meta: dict[str, dict]) -> dict[str, dict]:
        """
        BA-P5B / Phase 2.5 #8: real posterior model inputs.

        pratijna_grade/pratijna_status/event_class_id come from bodha_pratijna, joined via
        the same domain-overlap the writer itself uses (event_class_id.domain == signal's
        domains_affected_array[1]), scoped to the signal's own ayanamsha_id (bo_pratijna is
        computed per-ayanamsha, one row per (chart, ayanamsha, event_class)).

        multi_system_confirmation_count comes from ka_yojaka's own already-computed
        dasha_eligibility_rule_jsonb->>'multi_system_confirmation_count' (kala_activation_predicates),
        keyed by (chart_id, signal_id, ayanamsha_id) — no re-derivation, just a join.

        av_transit_potency has no real scalar source anywhere in the codebase (ka_yojaka's
        transit_trigger_jsonb is a symbolic trigger-type descriptor, not a potency score) —
        fabricating one would violate B.10, so it stays the documented placeholder (0.0)
        until a real AV-transit-gate model exists.
        """
        if not signal_meta:
            return {}

        event_class_by_domain: dict[str, str] = {}
        base_rate_by_class: dict[str, dict] = {}
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT event_class_id, domain, base_rate_by_age FROM brahma_event_ontology")
            for r in cur.fetchall():
                event_class_by_domain.setdefault(r['domain'], str(r['event_class_id']))
                base_rate_by_class[str(r['event_class_id'])] = r.get('base_rate_by_age') or {}

        pratijna_by_key: dict[tuple[str, str], dict] = {}
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT ayanamsha_id, event_class_id, status, grade "
                "FROM bodha_pratijna WHERE chart_id = %s",
                (chart_id,),
            )
            for r in cur.fetchall():
                pratijna_by_key[(str(r['ayanamsha_id']), str(r['event_class_id']))] = dict(r)

        confirmation_by_signal: dict[str, int] = {}
        signal_ids = list(signal_meta.keys())
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_nimitta_yojaka")
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT signal_id, "
                    "(dasha_eligibility_rule_jsonb->>'multi_system_confirmation_count')::int AS mscc "
                    "FROM kala_activation_predicates "
                    "WHERE chart_id = %s AND signal_id = ANY(%s::uuid[])",
                    (chart_id, signal_ids),
                )
                for r in cur.fetchall():
                    confirmation_by_signal[str(r['signal_id'])] = r['mscc'] or 0
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_nimitta_yojaka")
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_nimitta_yojaka")
            except Exception:
                pass
            logger.debug("ph_nimitta: ka_yojaka confirmation-count lookup skipped: %s", exc)

        out: dict[str, dict] = {}
        for sid, sm in signal_meta.items():
            domain = sm.get('domain')
            aya = sm.get('ayanamsha_id')
            event_class_id = event_class_by_domain.get(domain) if domain else None
            pratijna = pratijna_by_key.get((str(aya), str(event_class_id))) if event_class_id else None
            out[sid] = {
                'event_class_id': event_class_id,
                'base_rate_by_age': base_rate_by_class.get(str(event_class_id)) if event_class_id else None,
                'pratijna_grade': float(pratijna['grade']) if pratijna and pratijna.get('grade') is not None else None,
                'pratijna_status': pratijna['status'] if pratijna else None,
                'multi_system_confirmation_count': confirmation_by_signal.get(sid, 0),
            }
        return out

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
        # cross_subsystem_root is a BOOLEAN column — guard before .lower()
        _csroot = row.get('cross_subsystem_root')
        subsystem = (row.get('discovery_subsystem') or (str(_csroot) if _csroot else '') or '').lower()
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

    def _build_ctx(self, row: dict, signal_meta, cgm_meta, contradiction_m, precedent_m, posterior_m=None) -> NimittaContext:
        sid = str(row.get('signal_id') or '')
        sm   = signal_meta.get(sid, {})
        # cgm_meta is a chart-level aggregate (not per-signal) — bodha_cgm_paths has no
        # signal_id FK so per-signal lookup was always a miss. Use directly as chart context.
        cgm  = cgm_meta  # type: dict (chart-level)
        cont = contradiction_m.get(sid, {})
        prec = precedent_m.get(sid, {})
        post = (posterior_m or {}).get(sid, {})

        return NimittaContext(
            signal_domain=sm.get('domain'),
            signal_signature_class=sm.get('signature_class'),
            signal_salience=sm.get('salience_score'),
            cgm_path_ids=[str(p['path_id']) for p in cgm.get('paths', []) if p.get('path_id')],
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
            # BA Phase 2.5 #8: pratijna_grade/pratijna_status/event_class_id are real,
            # joined from bodha_pratijna (domain-overlap match, scoped by the signal's own
            # ayanamsha_id); multi_system_confirmation_count is a real join from ka_yojaka's
            # own already-computed kala_activation_predicates row. Fall back to the prior
            # neutral defaults only when no pratijna/yojaka row exists for this signal (e.g.
            # its domain has no matching event class) — never a fabricated non-neutral value.
            # av_transit_potency has no real scalar source in the codebase yet (ka_yojaka's
            # transit_trigger_jsonb is a symbolic type descriptor, not a potency score) — B.10
            # forbids inventing one, so it stays the documented placeholder pending a real
            # AV-transit-gate model.
            # JL-009 CLOSED (native glance 2026-07-07): base_rate is the ontology's
            # age-band prior, ROW-NORMALIZED to sum 1.0 at lookup (native point-2), for the
            # age band containing this anchor's predicted date. See _resolve_base_rate.
            event_class_id=post.get('event_class_id'),
            pratijna_grade=post.get('pratijna_grade') if post.get('pratijna_grade') is not None else 5.0,
            pratijna_status=post.get('pratijna_status') or 'conditional',
            multi_system_confirmation_count=post.get('multi_system_confirmation_count', 0),
            av_transit_potency=0.0,
            base_rate=self._resolve_base_rate(row, post),
        )

    def _resolve_base_rate(self, row: dict, post: dict) -> float:
        """JL-009 point-2: normalized age-band base_rate for this anchor.

        base_rate = normalize(brahma_event_ontology.base_rate_by_age)[age_band(peak_date)],
        where age is the native's age at the anchor's predicted date (peak_date, else
        window_start). Missing vector/birth/date → uniform age prior (0.20). Never the
        old flat 0.10 placeholder, never a fabricated value."""
        at = _parse_iso_date(row.get('peak_date') or row.get('window_start'))
        return base_rate_for_age(
            post.get('base_rate_by_age'),
            getattr(self, '_birth_date', None),
            at,
        )

    def _spine_gate(self, anchors: list[AnchorRecord]) -> None:
        """
        D26 — SPINE-FIRST hard gate: at least one anchor must have ALL 5 elevations
        populated (magnitude, confidence range, karmic_frame, malleability, falsifier).
        """
        for a in anchors:
            if (
                a.magnitude and
                a.posterior is not None and
                a.lift_vector is not None and
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
