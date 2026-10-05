# VICHARA TOKEN: python vs SQL agreement, read-only production measurement (2026-10-05)

Definition: `platform/python-sidecar/bodha_writers/vichara_token.py` (ONE python definition) and migration 1295 (`public.chart_vichara_token`, generated from the same `TOKEN_SQL_TEMPLATE`; a test compares the function body to the template byte for byte).

## Method (no migration exists yet, nothing written)
1. For each of the three charts that hold chart_vichara rows, ONE read-only SELECT through `rq.sh` returned, per row: the 12 natural-key columns exactly as a writer reads them (`value_num::text`, `value_jsonb::text`, `constituent_facts_array`) plus `id` and the token computed BY THE SERVER with the migration's expression written inline over `chart_vichara v` (`token_sql_for_alias('v')`). Files: `data/vichara/q_*.sql`, `rows_*.jsonl`.
2. `scripts/compare_vichara_tokens.py` computes the python token from the same fetched columns and compares with the server's token.

## Result
| chart | rows | distinct tokens | python != sql |
|---|---|---|---|
| 482012f1 (canonical, post S-L1) | 7,774 | 7,774 | 0 |
| 1c826d5a | 8,247 | 7,581 | 0 |
| cb73cd3d | 8,240 | 7,569 | 0 |
| **all** | **24,261 rows compared** | | **0 mismatches** |

- No token collision: 22,924 distinct canonical natural keys map to 22,924 distinct tokens (two different keys never share a token); no token is shared between charts.
- Canonical chart: every row has its own token (7,774 = 7,774), the uniqueness the SS ruling relied on.
- The two older charts (never rebuilt since July/August, pre-S-L1 ga_vichara) hold EXACT duplicate rows: 666 and 671 groups of exactly two rows that agree on every column but `id` (also on build_id, computed_at, formula_version, source_citation, constituent_fact_ids). Those pairs share one token by construction; they are not collisions. 23 / 25 of those pairs are D1 valence_pass rows (the ones bo_karanajala looks up), so the lookup chooses among them by smallest token, not by row order.
- Data shapes the production rows exercise: every row has value_num, value_jsonb and constituent_facts_array set (no NULL value_num / jsonb / array, no jsonb null scalar, no trailing-zero numerics, no non-ASCII or control characters): production alone does NOT exercise the NULL / trim_scale / escape branches. Those are covered by the disposable-PostgreSQL test (`tests/l2/test_vichara_token.py`): 400 hostile fuzz rows (NULL in every column, empty and NULL arrays, a NULL array element, unicode and emoji, quotes, backslashes, control characters, numerics 0 / 0.00 / 1.50 / 100 / 1e-9 / 30-digit / NaN, jsonb with unsorted keys, nested objects, big numerics, null scalars) plus 200 production-shaped rows: SQL token == python token on all of them.

## Statement set
`ACCEPTANCE_VICHARA.sql.txt` (final form over the view and a today form with the expression inlined); today's run, `ACCEPTANCE_VICHARA_TODAY.txt`: bodha_cgm_edges 1,387 citations / 0 resolved; bodha_mechanisms 3,058 / 0; RM rows 5 / 0 (all citations are bigserial ids, 4,445 serial-shaped, 0 token-shaped). The canonical chart's resolver is unique today (7,774 rows, 7,774 distinct tokens).
