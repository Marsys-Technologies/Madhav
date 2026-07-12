# Shard 9b — graha_kp_lords

shard_id: 9b-graha_kp_lords
charts: Abhisek 482012f1-710e-4a25-994a-93821f5871aa · Abhinandan 1c826d5a-41cb-4450-b4dc-59d440e5f75a

## Exact SQL run (proven 9b 5-cell recipe, <CAT>=graha_kp_lords)
```sql
WITH sig AS (SELECT DISTINCT ms.signal_id, ms.chart_id, ms.signature_tier, ms.signal_type_class,
  ms.domains_affected_array, ms.constituent_facts_array FROM bodha_msr_signals ms
  JOIN LATERAL unnest(ms.constituent_facts_array) AS cf(fid) ON true
  JOIN chart_facts f ON f.fact_id = cf.fid AND f.chart_id = ms.chart_id
  WHERE f.fact_category = 'graha_kp_lords'
    AND ms.chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa','1c826d5a-41cb-4450-b4dc-59d440e5f75a'))
SELECT 'cell1', chart_id, COUNT(*) FROM sig GROUP BY chart_id
UNION ALL SELECT 'cell2_salience', ... UNION ALL SELECT 'cell5_type', ...
UNION ALL SELECT 'cell3_attr', ... UNION ALL SELECT 'cell4_domains', ...;
-- baseline: SELECT fact_category,chart_id,COUNT(*) FROM chart_facts WHERE fact_category='graha_kp_lords' ...
```

## Verbatim results
chart_facts baseline: Abhisek=200, Abhinandan=200 rows.
- cell1 (consumed): Abhinandan=132, Abhisek=131
- cell2_salience: Abhinandan `background=34, major=10, supporting=88`; Abhisek `background=13, major=26, supporting=92`
- cell3_attr: Abhinandan `132/132`, Abhisek `131/131` (100% non-empty)
- cell4_domains: BOTH charts `character|relationship`
- cell5_type: Abhinandan `tradition_specific=132`, Abhisek `tradition_specific=131`

## 5-cell verdicts
1. Consumed? YES (131/132 signals).
2. Salience: mostly supporting/background, modest major — proportionate.
3. Attribution: 100% non-empty, sound.
4. Domain mapping: **character|relationship ONLY** — defect.
5. Emergence: all `tradition_specific` (sensible for KP).

## design_correctness_verdict: WEAK

## Findings
- **KP significators domain-mono-mapped to character|relationship (KP-4 rediscovery).** graha_kp_lords carries the nakshatra/sub/sub-sub lord significator machinery that KP uses to answer EVERY house question — wealth (2nd/11th significators), career (10th), health (6th). All 131/132 signals map only to `character|relationship`, so a wealth/career/health domain-filtered query on domains_affected_array can never surface a single KP-lord signal. failure_class=2 (WRONG; class-1 UNREACHABLE consequence for domain-filtered queries). severity=HIGH. suspected layer: L-writer (bo_laksana domain-mapping). evidence: cell4 both charts = `character|relationship` verbatim, over 131/132 signals.
