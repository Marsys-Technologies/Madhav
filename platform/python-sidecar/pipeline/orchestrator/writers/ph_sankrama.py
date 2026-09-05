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

# Anchor domains (ph_nimitta) → CDLM domains (bodha_cdlm_cells.domain_row/domain_col).
#
# THIS MAP IS NOW EMPTY, DELIBERATELY. The two vocabularies have converged: phala_anchors.domain
# already stores CDLM-native terms, so every translation this map used to perform is either
# inert or harmful. Verified live against production before emptying it:
#
#   anchor domains (7): career character health relationship spirituality transition wealth
#   CDLM domain_row (11): career character education family health progeny relationship
#                         residence spirituality transition travel
#
# Six of the seven match exactly. The map's four entries were all written against ph_nimitta's
# OLD vocabulary and its comment misdescribed CDLM's on four of seven terms:
#
#   'financial' → 'wealth'       DEAD: 'financial' is not an anchor domain (and 'wealth' is not
#                                a CDLM domain either -- see the honest empty below)
#   'spiritual' → 'spirituality' DEAD: the anchor domain is already 'spirituality'
#   'psychological' → 'character' DEAD: the anchor domain is already 'character'
#   'transition' → 'general'     HARMFUL: 'transition' IS an anchor domain AND IS a CDLM
#                                domain_row with 5 material cells -- but 'general' does not
#                                exist in CDLM at all, so this entry redirected a working match
#                                into a guaranteed miss and silently destroyed every spillover
#                                row those anchors should have produced. Measured: 250 rows on
#                                the canonical chart (10% of the asset), 355 across both charts.
#
# Identity mapping is therefore the correct behaviour, not a shortcut. If the vocabularies ever
# diverge again, add the entry here AND to the domain-coverage disclosure in run().
_ANCHOR_TO_CDLM_DOMAIN: dict[str, str] = {}

# Anchor domains with no CDLM counterpart. 'wealth' is a genuine vocabulary divergence, not a
# defect: bodha_cdlm_cells has no 'wealth' domain_row, so those anchors legitimately produce no
# spillover. B.10 forbids dropping that silently -- run() logs it explicitly rather than letting
# the caller read an unexplained zero.
_KNOWN_UNMAPPED_ANCHOR_DOMAINS: frozenset[str] = frozenset({'wealth'})


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
            cur.execute("SET LOCAL statement_timeout = 0")
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
        unmapped_known: dict[str, int] = {}
        unmapped_unexpected: dict[str, int] = {}
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

                # The vocabularies have converged, so this is now an identity lookup --
                # see the note on _ANCHOR_TO_CDLM_DOMAIN for why the old translations were
                # all stale and one of them was actively destructive.
                cdlm_domain = _ANCHOR_TO_CDLM_DOMAIN.get(domain, domain)

                # Cells where domain_row = this anchor's domain (CDLM vocabulary)
                matching_cells = [
                    c for c in cdlm_cells
                    if c.domain_row == cdlm_domain and c.net_linkage_strength >= _LINKAGE_THRESHOLD
                ]

                if not matching_cells:
                    # B.10: never drop silently. An anchor domain with no CDLM counterpart
                    # produces no spillover, and the caller must be able to tell that apart
                    # from a bug. 'wealth' is the known, honest case (no such domain_row
                    # exists); anything else is a vocabulary drift worth surfacing loudly.
                    if domain in _KNOWN_UNMAPPED_ANCHOR_DOMAINS:
                        unmapped_known[domain] = unmapped_known.get(domain, 0) + 1
                    else:
                        unmapped_unexpected[domain] = unmapped_unexpected.get(domain, 0) + 1
                    continue

                sctx = SankramaContext(
                    source_anchor_id=anchor_id,
                    source_domain=cdlm_domain,  # CDLM-vocab domain for engine matching
                    source_window_start=ws,
                    source_window_end=we,
                    source_confidence=conf,
                    cdlm_cells=matching_cells,
                    all_cells_by_domain_pair=cells_by_pair,
                )

                spillovers = derive_spillover(sctx)

                for s in spillovers:
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
                        ON CONFLICT ON CONSTRAINT phala_sankrama_natural_key DO NOTHING
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
                    # §N.8: count what the database accepted. An unconditional increment
                    # beside ON CONFLICT DO NOTHING is a claimed count with no measurement
                    # behind it -- the defect W1 found live in ph_muhurta (139 claimed / 134
                    # stored). Latent here because this natural key cannot collide; counted
                    # honestly anyway, so it stays correct if the key ever changes.
                    if cur.rowcount == 1:
                        rows_inserted += 1

        if unmapped_known:
            logger.info(
                "ph_sankrama: %s anchor(s) produced no spillover -- their domain has no CDLM "
                "counterpart, which is a known vocabulary divergence, not a defect: %s",
                sum(unmapped_known.values()), dict(sorted(unmapped_known.items())),
            )
        if unmapped_unexpected:
            logger.warning(
                "ph_sankrama: %s anchor(s) in %s matched NO CDLM cell and the domain is not a "
                "known divergence -- this is vocabulary drift between phala_anchors.domain and "
                "bodha_cdlm_cells.domain_row and it is silently costing spillover rows",
                sum(unmapped_unexpected.values()), dict(sorted(unmapped_unexpected.items())),
            )
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
                        # §N.7 item 6: `or 0.0` turned "I don't know" into "flat", and a flat
                        # gradient reads as the favourable-sounding 'stable'. The upstream L2
                        # column is 100% NULL, so that default was the ONLY branch reachable --
                        # 2,985 rows all claiming a trajectory nothing measured. Carry the None.
                        evolution_gradient_score=(
                            None if r.get('cell_evolution_gradient_score') is None
                            else float(r['cell_evolution_gradient_score'])
                        ),
                    ))
                return cells
        except Exception as exc:
            logger.warning("ph_sankrama: cdlm_cells load skipped: %s", exc)
            return []
