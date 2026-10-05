# VICHARA TOKEN: python vs SQL agreement, read-only production measurement (2026-10-05)

Definition: `platform/python-sidecar/bodha_writers/vichara_token.py` (the writer-side python definition) and the committed SQL expression `vichara_token_expression.sql` in this folder (the single SQL definition; no function, no view, no migration: the routine migrate role cannot CREATE in schema public). A pytest evaluates that file on a disposable PostgreSQL and requires equality with the python token.

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
`ACCEPTANCE_VICHARA.sql.txt` (every statement inlines the expression); today's run, `ACCEPTANCE_VICHARA_TODAY.txt`: bodha_cgm_edges 1,387 citations / 0 resolved; bodha_mechanisms 3,058 / 0; all 4,445 edge+mechanism citations are serial-shaped, 0 token-shaped; the 5 RM rows still carry legacy `vichara_row_id` / `dasha_row_id` / uuid tokens (V3a), none token citations. The canonical chart's token is unique today (7,774 rows, 7,774 distinct tokens).
