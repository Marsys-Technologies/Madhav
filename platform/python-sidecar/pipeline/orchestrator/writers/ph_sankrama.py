"""
ph_sankrama — Cross-Domain Spillover (L4 Phala wave 4 parallel).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_sankrama.

Reads: phala_anchors · bodha_cdlm_cells
Writes: phala_sankrama (delete-then-insert per chart_id)
"""
from __future__ import annotations

import json
import logging

import psycopg

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_sankrama.engine import (
    CdlmCell,
    SankramaContext,
    derive_spillover,
)

logger = logging.getLogger(__name__)

_LINKAGE_THRESHOLD = 0.25


@register('ph_sankrama')
class PhSankramaWriter(WriterBase):
    """
    Builds phala_sankrama: for each ph_nimitta anchor, finds CDLM cells
    linking its domain to other domains, derives grounded spillovers (SK1-SK4).
    """
    asset_id = 'ph_sankrama'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']

        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_sankrama WHERE chart_id = %s", (chart_id,))

        anchors = self._load_anchors(conn, chart_id)
        cdlm_cells = self._load_cdlm_cells(conn, chart_id)

        # Build all_cells_by_domain_pair for cascade chaining (SK2)
        cells_by_pair: dict[tuple[str, str], list[CdlmCell]] = {}
        for cell in cdlm_cells:
            key = (cell.domain_row, cell.domain_col)
            cells_by_pair.setdefault(key, []).append(cell)

        logger.info(
            "ph_sankrama: %d anchors / %d CDLM cells / %d domain pairs",
            len(anchors), len(cdlm_cells), len(cells_by_pair),
        )

        rows_inserted = 0
        with conn.cursor() as cur:
            for anchor in anchors:
                anchor_id   = str(anchor['anchor_id'])
                domain      = str(anchor['domain'])
                conf        = float(anchor.get('confidence_high') or 0.5)

                ws = anchor.get('window_start')
                we = anchor.get('window_end')
                if isinstance(ws, str):
                    from datetime import date
                    try: ws = date.fromisoformat(ws)
                    except ValueError: ws = None
                if isinstance(we, str):
                    from datetime import date
                    try: we = date.fromisoformat(we)
                    except ValueError: we = None

                # Cells where domain_row = this anchor's domain
                matching_cells = [
                    c for c in cdlm_cells
                    if c.domain_row == domain and c.net_linkage_strength >= _LINKAGE_THRESHOLD
                ]

                if not matching_cells:
                    continue

                sctx = SankramaContext(
                    source_anchor_id=anchor_id,
                    source_domain=domain,
                    source_window_start=ws,
                    source_window_end=we,
                    source_confidence=conf,
                    cdlm_cells=matching_cells,
                    all_cells_by_domain_pair=cells_by_pair,
                )

                spillovers = derive_spillover(sctx)

                for s in spillovers:
                    try:
                        cur.execute(
                            """
                            INSERT INTO phala_sankrama (
                                chart_id, source_anchor_id, cdlm_cell_id,
                                source_domain, target_domain, relationship_type,
                                linkage_strength, asymmetry_score, trajectory,
                                bridge_path_jsonb, mechanism_text,
                                source_window_start, source_window_end,
                                projected_window_start, projected_window_end, projected_peak_date,
                                cascade_chain_jsonb, cascade_depth,
                                spillover_confidence, confidence_basis,
                                falsifier, derivation_ledger_jsonb, source_citation
                            ) VALUES (
                                %s, %s, %s,
                                %s, %s, %s,
                                %s, %s, %s,
                                %s::jsonb, %s,
                                %s, %s,
                                %s, %s, %s,
                                %s::jsonb, %s,
                                %s, %s,
                                %s, %s::jsonb, %s
                            )
                            ON CONFLICT DO NOTHING
                            """,
                            (
                                chart_id, s.source_anchor_id, s.cdlm_cell_id,
                                s.source_domain, s.target_domain, s.relationship_type,
                                s.linkage_strength, s.asymmetry_score, s.trajectory,
                                json.dumps(s.bridge_path_jsonb), s.mechanism_text,
                                s.source_window_start, s.source_window_end,
                                s.projected_window_start, s.projected_window_end, s.projected_peak_date,
                                json.dumps(s.cascade_chain_jsonb) if s.cascade_chain_jsonb else None,
                                s.cascade_depth,
                                s.spillover_confidence, s.confidence_basis,
                                s.falsifier, json.dumps(s.derivation_ledger_jsonb), s.source_citation,
                            ),
                        )
                        rows_inserted += 1
                    except Exception as exc:
                        logger.warning("ph_sankrama: insert failed for anchor %s → %s: %s",
                                       anchor_id, s.target_domain, exc)

        logger.info("ph_sankrama: inserted %d rows into phala_sankrama for %s", rows_inserted, chart_id)
        return WriterResult(asset_id='ph_sankrama', rows_inserted=rows_inserted)

    def _load_anchors(self, conn, chart_id: str) -> list:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT anchor_id, domain, confidence_high, window_start, window_end, peak_date
                FROM phala_anchors
                WHERE chart_id = %s
                ORDER BY confidence_high DESC NULLS LAST
                LIMIT 100
                """,
                (chart_id,),
            )
            return cur.fetchall()

    def _load_cdlm_cells(self, conn, chart_id: str) -> list[CdlmCell]:
        try:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT cell_id, domain_row, domain_col,
                           net_linkage_strength, asymmetry_score,
                           contradicting_signal_pairs_count,
                           cgm_bridge_edge_seeds_jsonb,
                           predicted_activation_dasha_windows_jsonb,
                           cell_evolution_gradient_score
                    FROM bodha_cdlm_cells
                    WHERE chart_id = %s
                    """,
                    (chart_id,),
                )
                cells: list[CdlmCell] = []
                for r in cur.fetchall():
                    bridge_seeds = r.get('cgm_bridge_edge_seeds_jsonb') or []
                    if isinstance(bridge_seeds, str):
                        import json as _json
                        try: bridge_seeds = _json.loads(bridge_seeds)
                        except Exception: bridge_seeds = []

                    act_windows = r.get('predicted_activation_dasha_windows_jsonb') or []
                    if isinstance(act_windows, str):
                        import json as _json
                        try: act_windows = _json.loads(act_windows)
                        except Exception: act_windows = []

                    cells.append(CdlmCell(
                        cell_id=str(r['cell_id']),
                        domain_row=str(r['domain_row']).lower(),
                        domain_col=str(r['domain_col']).lower(),
                        net_linkage_strength=float(r.get('net_linkage_strength') or 0.0),
                        asymmetry_score=float(r.get('asymmetry_score') or 0.0),
                        contradicting_pairs_count=int(r.get('contradicting_signal_pairs_count') or 0),
                        cgm_bridge_edge_seeds=bridge_seeds if isinstance(bridge_seeds, list) else [],
                        predicted_activation_windows=act_windows if isinstance(act_windows, list) else [],
                        evolution_gradient_score=float(r.get('cell_evolution_gradient_score') or 0.0),
                    ))
                return cells
        except Exception as exc:
            logger.debug("ph_sankrama: cdlm_cells load skipped: %s", exc)
            return []
