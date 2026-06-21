"""
ka_yojaka writer — activation-predicate bridge (L3 K3)
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER calls ctx.db_conn.commit() or .rollback()
NEVER writes to any bodha_* table
"""
import json

from psycopg2.extras import execute_values

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ka_yojaka.classifier import classify_signal
from services.ka_yojaka.binder import build_predicate


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

        # Step 3: classify + bind each signal
        rows = []
        for sig in signals:
            signal_dict = {
                'signal_id': sig[0],
                'chart_id': sig[1],
                'ayanamsha_id': sig[2],
                'signal_type_class': sig[3],
                'signal_type_id': sig[4],
                'configuration_jsonb': sig[5],
                'constituent_facts_array': sig[6],
                'valence': sig[7],
                'dignity_score': sig[8],
            }
            sc = classify_signal(signal_dict)
            pred = build_predicate(signal_dict, sc)
            rows.append((
                str(sig[1]),  # chart_id
                str(sig[2]),  # ayanamsha_id
                str(sig[0]),  # signal_id
                sc,
                json.dumps(pred['dasha_eligibility_rule']),
                json.dumps(pred['transit_trigger']),
                json.dumps(pred['strength_affliction_hook']),
                json.dumps(pred['derivation_ledger']),
            ))

        # Step 4: batch insert (1000 rows per batch)
        with conn.cursor() as cur:
            for i in range(0, len(rows), 1000):
                batch = rows[i:i + 1000]
                execute_values(
                    cur,
                    """
                    INSERT INTO kala_activation_predicates
                        (chart_id, ayanamsha_id, signal_id, signature_class,
                         dasha_eligibility_rule_jsonb, transit_trigger_jsonb,
                         strength_affliction_hook_jsonb, derivation_ledger_jsonb)
                    VALUES %s
                    ON CONFLICT (chart_id, signal_id, ayanamsha_id) DO UPDATE SET
                        signature_class = EXCLUDED.signature_class,
                        dasha_eligibility_rule_jsonb = EXCLUDED.dasha_eligibility_rule_jsonb,
                        transit_trigger_jsonb = EXCLUDED.transit_trigger_jsonb,
                        strength_affliction_hook_jsonb = EXCLUDED.strength_affliction_hook_jsonb,
                        derivation_ledger_jsonb = EXCLUDED.derivation_ledger_jsonb
                    """,
                    batch,
                )

        return WriterResult(asset_id='ka_yojaka', rows_inserted=len(rows))
