# CL-02 Census — S5 MŪLA (F-04, F-05, F-22, F-61, F-70)

Per plan §2 S5 "Known": census every dead-backend literal against `information_schema`
BEFORE writing specs, to distinguish genuinely-absent tables from unwired-but-present ones.

Run 2026-08-16, live prod DB, via `mcp__postgres__query`.

| Finding | Table claimed present | information_schema.tables hit? | Row count | Verdict |
|---|---|---|---|---|
| F-04 | `reference_nakshatra` (singular; manifest cites migration 302 deprecating plural `reference_nakshatras`) | YES | 28 | Table is REAL and populated. Sibling `reference_nakshatras` (plural, legacy) also exists, 27 rows — confirms the deprecation-migration story; serving code must target the singular canonical table. |
| F-05 | `brahma_remedy_corpus` (production remedy table; `tantric` type never emitted) | YES | remedy_type breakdown: ayurvedic 1, behavioral 9, charity 67, gemstone 22, homa 10, japa 24, mantra 67, puja 76, vrata 33, yantra 23 — **`tantric` absent from the GROUP BY entirely**, confirming claim: the seeding pipeline (`l0_remedy_corpus.py`) never emits it even though `tantric.yaml` exists as dead-code input to an uncalled loader. |
| F-22 | `brahma_dasha_systems` | YES | 20 | Table is REAL and populated. Sibling `reference_dasha_systems` also exists (not queried in this pass) — second candidate table worth a one-line check before the lane closes so the spec picks the right one. |
| F-61 | `chart_divisionals` (6-7 per-varga rows resolvable by UUID pointer, never aggregated into `saptavargaja_score`) | YES | table exists (row count not sampled — manifest's own direct-SQL resolution of the 6 UUID pointers for SUN already proved non-null per-varga values) | Table is REAL; the gap is a missing aggregation step, not a missing table — differs from the other four CL-02 members (no-consumer) in being a missing-computation defect, not a missing-connection defect. Flag this distinction for the D-stage lane; it changes the S-stage fix shape (write an aggregator, not just re-point a query). |
| F-70 | `kala_field_weight_versions`, `kala_field_skill`, `kala_field_gof` | YES (all three) | weight_versions=1, skill=7, gof=6 | Tables are REAL and non-empty globally — confirms `mi_bhara.py`'s calibration-maturity computation genuinely runs and persists somewhere; the 8 `kala_*_get` view facades hardcode `noLelCalibrationMaturity()` instead of reading these tables. (Note: `kala_field_weight_versions` has no `chart_id` column — the join path from a chart to its weight-version row needs tracing in Stage D, not assumed.) |

**Net verdict for S5's CL-02 five: none of the five backends are genuinely absent.** All are
"real data, no consumer" per the plan's framing — the degrade-order and fix shape is a wiring
fix (repoint a query / read an existing table), not new backend development, for F-04/F-05/F-22/F-70.
F-61 is the one exception in this group: the backend exists but the *aggregation step* the
`fact_key` promises was never written — the fix is a small aggregator, not a repoint.
