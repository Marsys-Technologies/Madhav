"""
ka_yojaka writer — activation-predicate bridge (L3 K3)
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
Orchestrator owns the transaction — writer must NOT commit or rollback
NEVER writes to any bodha_* table

D6 (Kāla completeness v2): reads bodha_cgm_nodes pagerank centrality and
bodha_cdlm_cells domain-link strength to enrich each predicate's
dasha_eligibility_rule with a cgm_centrality_weight field. This allows
ka_sangam to prioritize predicates whose primary graha is a graph hub.
"""
import json
import logging

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ka_yojaka.classifier import classify_signal
from services.ka_yojaka.binder import build_predicate

logger = logging.getLogger(__name__)


@register('ka_yojaka')
class KaYojakaWriter(WriterBase):
    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # orchestrator owns the transaction; writer never commits
        chart_id = ctx.config['chart_id']

        # Step 1: delete existing for this chart (delete-then-insert idempotency per §N.3)
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM kala_activation_predicates WHERE chart_id = %s",
                (chart_id,),
            )

        # Step 2: read all MSR signals for this chart (SELECT only — never write to bodha_*)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT signal_id, chart_id, ayanamsha_id, signal_type_class, signal_type_id,
                       configuration_jsonb, constituent_facts_array, valence, dignity_score
                FROM bodha_msr_signals WHERE chart_id = %s
                """,
                (chart_id,),
            )
            signals = cur.fetchall()

        # D6: pre-fetch CGM centrality (pagerank) by node_subject for this chart.
        # Used to add cgm_centrality_weight to each predicate's dasha_eligibility_rule.
        cgm_pagerank: dict[str, float] = self._fetch_cgm_pagerank(conn, chart_id)

        # D6: pre-fetch CDLM domain strengths for this chart (domain → link_strength).
        cdlm_domain_strength: dict[str, float] = self._fetch_cdlm_domain_strength(conn, chart_id)

        # Step 3: classify + bind each signal
        # Connection uses dict_row factory — access columns by name, not integer index.
        rows = []
        for sig in signals:
            signal_dict = {
                'signal_id': sig['signal_id'],
                'chart_id': sig['chart_id'],
                'ayanamsha_id': sig['ayanamsha_id'],
                'signal_type_class': sig['signal_type_class'],
                'signal_type_id': sig['signal_type_id'],
                'configuration_jsonb': sig['configuration_jsonb'],
                'constituent_facts_array': sig['constituent_facts_array'],
                'valence': sig['valence'],
                'dignity_score': sig['dignity_score'],
            }
            sc = classify_signal(signal_dict)
            pred = build_predicate(signal_dict, sc)

            # D6: enrich dasha_eligibility_rule with CGM centrality weight.
            # Primary graha is the planet most likely to be the graph node subject.
            primary_graha = _extract_primary_graha(signal_dict)
            cgm_weight = cgm_pagerank.get(primary_graha, 0.5) if primary_graha else 0.5
            pred['dasha_eligibility_rule']['cgm_centrality_weight'] = round(cgm_weight, 4)

            # D6: enrich with CDLM domain strength for the signal's inferred domain.
            domain = _infer_signal_domain(signal_dict)
            pred['dasha_eligibility_rule']['cdlm_domain_strength'] = round(
                cdlm_domain_strength.get(domain, 0.5), 4
            )

            rows.append((
                str(sig['chart_id']),
                str(sig['ayanamsha_id']),
                str(sig['signal_id']),
                sc,
                json.dumps(pred['dasha_eligibility_rule']),
                json.dumps(pred['transit_trigger']),
                json.dumps(pred['strength_affliction_hook']),
                json.dumps(pred['derivation_ledger']),
            ))

        # Step 4: batch insert (1000 rows per batch)
        # psycopg3 executemany: standard VALUES (%s, ...) form, delete-then-insert idempotency per §N.3
        _INSERT_SQL = """
            INSERT INTO kala_activation_predicates
                (chart_id, ayanamsha_id, signal_id, signature_class,
                 dasha_eligibility_rule_jsonb, transit_trigger_jsonb,
                 strength_affliction_hook_jsonb, derivation_ledger_jsonb)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """
        with conn.cursor() as cur:
            for i in range(0, len(rows), 1000):
                batch = rows[i:i + 1000]
                cur.executemany(_INSERT_SQL, batch)

        return WriterResult(asset_id='ka_yojaka', rows_inserted=len(rows))

    def _fetch_cgm_pagerank(self, conn, chart_id: str) -> dict[str, float]:
        """
        Fetch CGM node pagerank scores keyed by node_subject (graha name / bhava label).
        Normalizes scores to [0, 1] relative to the chart's max pagerank.
        Returns empty dict on failure (soft dependency — CGM may not be built yet).
        """
        result: dict[str, float] = {}
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT node_subject, COALESCE(pagerank_score::float, 0.5) AS pgr
                    FROM bodha_cgm_nodes
                    WHERE chart_id = %s AND pagerank_score IS NOT NULL
                    ORDER BY pagerank_score DESC
                    """,
                    (chart_id,),
                )
                rows = cur.fetchall()
            if not rows:
                return result
            max_pgr = max(float(r['pgr']) for r in rows) or 1.0
            for r in rows:
                result[str(r['node_subject'])] = min(1.0, float(r['pgr']) / max_pgr)
            logger.debug("ka_yojaka: CGM centrality loaded — %d nodes", len(result))
        except Exception as exc:
            logger.debug("ka_yojaka: CGM pagerank fetch skipped: %s", exc)
        return result

    def _fetch_cdlm_domain_strength(self, conn, chart_id: str) -> dict[str, float]:
        """
        Fetch average CDLM link strength per domain from bodha_cdlm_cells.
        Returns {domain_name: avg_strength} for use in predicate enrichment.
        """
        result: dict[str, float] = {}
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT domain_a, AVG(link_strength::float) AS avg_strength
                    FROM bodha_cdlm_cells
                    WHERE chart_id = %s AND link_strength IS NOT NULL
                    GROUP BY domain_a
                    """,
                    (chart_id,),
                )
                for r in cur.fetchall():
                    result[str(r['domain_a']).lower()] = min(1.0, max(0.0, float(r['avg_strength'])))
            logger.debug("ka_yojaka: CDLM domain strengths loaded — %d domains", len(result))
        except Exception as exc:
            logger.debug("ka_yojaka: CDLM domain strength fetch skipped: %s", exc)
        return result


# ── D6 helpers (module-level) ─────────────────────────────────────────────────

def _extract_primary_graha(signal_dict: dict) -> str | None:
    """Extract the primary graha name from a signal's configuration_jsonb."""
    cfg = signal_dict.get('configuration_jsonb') or {}
    if isinstance(cfg, str):
        import json as _json
        try:
            cfg = _json.loads(cfg)
        except Exception:
            return None
    # Try common keys where planet name appears
    for key in ('fact_value_text', 'primary_graha', 'graha', 'planet', 'lord'):
        val = cfg.get(key)
        if val and isinstance(val, str):
            return val
    return None


_SIGNAL_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    'career':       ['raja', 'karma', 'tenth', 'arudha', 'amatyakaraka', 'profession'],
    'relationship': ['kalatra', 'seventh', 'navamsha', 'spouse', 'venus', 'upapada'],
    'finance':      ['dhana', 'second', 'eleventh', 'wealth', 'lakshmi', 'artha'],
    'health':       ['ayur', 'sixth', 'eighth', 'maraka', 'vitality', 'disease'],
    'spiritual':    ['dharma', 'ninth', 'twelfth', 'moksha', 'guru', 'liberation'],
    'education':    ['vidya', 'fourth', 'fifth', 'mercury', 'saraswati', 'learning'],
}


def _infer_signal_domain(signal_dict: dict) -> str:
    """Infer a signal's domain from signal_type_id for CDLM strength lookup."""
    stid = (signal_dict.get('signal_type_id') or '').lower()
    for domain, keywords in _SIGNAL_DOMAIN_KEYWORDS.items():
        if any(kw in stid for kw in keywords):
            return domain
    return 'general'
