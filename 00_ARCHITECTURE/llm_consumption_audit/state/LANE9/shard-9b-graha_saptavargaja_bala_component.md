# Shard 9b — graha_saptavargaja_bala_component

shard_id: 9b-graha_saptavargaja_bala_component
charts: Abhisek 482012f1 · Abhinandan 1c826d5a

## Exact SQL: proven 9b 5-cell recipe, <CAT>=graha_saptavargaja_bala_component.
## Confirmation SQL:
`SELECT fact_category,chart_id,COUNT(*) FROM chart_facts WHERE fact_category='graha_saptavargaja_bala_component' AND chart_id IN ('482012f1-...','1c826d5a-...') GROUP BY 1,2;`

## Verbatim results
- 5-cell recipe returned: **[] (zero rows)** for BOTH charts.
- chart_facts baseline: Abhisek=35, Abhinandan=35 rows EXIST.

## 5-cell verdicts
1. Consumed? **NO.** 0 MSR signals despite 35 chart_facts rows/chart.
2. Salience: N/A (no signals).
3. Attribution: N/A.
4. Domain mapping: N/A.
5. Emergence: **ZERO** signals.

## design_correctness_verdict: NOT_CONSUMED

## Findings
- **Saptavargaja bala never ingested by MSR (funnel-narrowing / UNREACHABLE-by-omission).** 35 chart_facts rows per chart exist for graha_saptavargaja_bala_component (the seven-varga positional strength — the sthana-bala positional component that weights a graha's dignity across D1/D2/D3/D7/D9/D12/D30), yet bo_laksana emits ZERO MSR signals resolving to this category on either chart. Notably the sibling sthana/shadbala components (cheshta, dig, drik, kala, naisargika, sthana, total) ARE all consumed — saptavargaja is singled out and dropped. Any downstream consumer asking "how strong is this graha across its vargas?" receives nothing. failure_class=1 (UNREACHABLE — exists in table, MSR did not ingest it). severity=HIGH. suspected layer: L-writer (bo_laksana ingestion selection). evidence: recipe returned [] both charts; chart_facts count = 35/35.
