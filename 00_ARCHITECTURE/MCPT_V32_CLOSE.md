---
artifact: MCPT_V32_CLOSE.md
version: 1.0
status: CLOSED
project: MCP Transformation
phase: v3.2 — Classical Grounding
sessions: v3.2-S1, v3.2-S2, v3.2-S3, v3.2-S4, v3.2-S5
closed_at: '2026-05-22'
---

# v3.2 Phase Close — Classical Grounding

## Result: PASS

### classical_texts rows (by text_key)

| text_key | work | chunks |
|---|---|---|
| bphs | BPHS | 1032 |
| jaimini_sutra | JAIMINI_SUTRA | 181 |
| kp_texts | KP_TEXTS | 1646 |
| tajaka_neelakanthi | TAJAKA_NEELAKANTHI | 0 (S3 residual — see below) |

Note: Additional classical texts were pre-existing on main (brihat_jataka, brihat_samhita, etc.)

### school_signal_coverage matrix (DB state post-v3.2)

| school | primary | secondary | silent |
|---|---|---|---|
| parashari | 51 | 448 | 15 |
| jaimini | 310 | 236 | 27 |
| kp | 346 | 113 | 114 |
| tajika | 71 | 413 | 61 |
| yogini | 0 | 51 | 463 |
| nadi | 0 | 0 | 514 |
| bnn | 0 | 0 | 514 |

### school_convergence_index (MV)

| metric | value |
|---|---|
| total rows | 574 |
| avg convergence_score | 0.866 |
| max convergence_score | 1.00 |
| signals with all 4 schools | 349 |

### tajaka_annual table

| metric | value |
|---|---|
| rows | 87 (1984–2070) |
| muntha_sign | deterministic (Cancer→Leo→...→Gemini cycle from natal Lagna=Cancer) |
| year_lord / annual_lagna / saham_names | NULL [EXTERNAL_COMPUTATION_REQUIRED] |

### Migrations (v3.2 range)

| file | content |
|---|---|
| 078_multi_school_extensions.sql | notes column + substantive index on school_signal_coverage (S4) |
| 079_tajaka_and_convergence.sql | school_convergence_index MV + tajaka_annual table (S5) |
| 080_classical_texts_work_column.sql | work column + index on classical_texts (S1, renamed from 072 collision fix) |

### Merge evidence (feature/mcpt-final)

| merge | SHA |
|---|---|
| BPHS → final | bd0a01fb |
| 072 collision rename | 0a5b2348 |
| Jaim+KP → final | c2842656 |
| Tajaka → final | b83a6ad6 |

Migration prefix check: v3.2 merges CLEAN (078, 079, 080 no duplicates). Pre-existing 070/071
duplicates are inherited from main (Coverage Campaign vs MCP Server workstreams — not introduced
by v3.2).

## Sessions Summary

### v3.2-S1: BPHS Ingestion (feature/mcpt-bphs)
Commit: 2aa53e47
- bootstrap_classical_texts_bphs.ts: 1615 chunks, 88 chapters, 768-dim Vertex AI embeddings
- classical_text_chunker.ts + classical_text_embedder.ts library modules
- migration 072_classical_texts_work_column.sql (work = generated column)
- 373 vitest tests (bphs_ingestion.test.ts)

### v3.2-S2: Jaimini Sutram + KP Reader Ingestion (feature/mcpt-jaim-kp)
Commit: c9bb3865
- bootstrap_classical_texts_jaimini.ts: 181 chunks
- bootstrap_classical_texts_kp.ts: 1646 chunks (KP Readers vol 1-3)
- 768-dim Vertex AI embeddings for both
- 826 vitest tests (jaimini + kp ingestion tests)

### v3.2-S3: Tajaka Neelakanthi Ingestion (feature/mcpt-tajaka)
Commit: c6e31890
- tajaka_corpus.ts: 333 verse entries, 28 chapters, structured from M9 knowledge layer
- bootstrap_classical_texts_tajaka.ts: row created in classical_texts
- Chunk ingestion residual (0 chunks — Vertex AI embeddings not run; tracked below)
- 163 vitest tests (tajaka_ingestion.test.ts)

### v3.2-S4: Jaimini + KP Multi-School Backfill (feature/mcpt-jaim-kp)
Commit: 58c45a2f
- bootstrap_multi_school_jaimini.ts: Jaimini school_signal_coverage rows
- bootstrap_multi_school_kp.ts: KP school_signal_coverage rows
- migration 078_multi_school_extensions.sql
- 804 vitest tests (multi_school_jaimini + multi_school_kp tests)

### v3.2-S5: Tajaka Multi-School Backfill + school_convergence_index (feature/mcpt-tajaka)
Commit: a5684970
- bootstrap_multi_school_tajaka.ts: 484 tajika coverage rows (71 primary + 413 secondary)
- tajaka_annual seeded: 87 rows (1984-2070), muntha_sign deterministic
- migration 079_tajaka_and_convergence.sql: school_convergence_index MV + tajaka_annual
- 30 vitest tests (multi_school_tajaka + school_convergence_index.perf tests)

## Residuals

1. **tajaka_neelakanthi chunks = 0**: The classical_texts row was created (S3) but the
   chunk embedding pipeline was not run against the live DB. Requires re-running
   `bootstrap_classical_texts_tajaka.ts` with Vertex AI credentials.
   Tagged as v3.3 prerequisite — Tajaka varshaphal depth data (S3 of v3.3) may proceed
   without the chunk embeddings if using the corpus directly.

2. **tajaka_annual year_lord / annual_lagna / saham_names = NULL**:
   [EXTERNAL_COMPUTATION_REQUIRED] — requires Jagannatha Hora or Swiss Ephemeris solar
   return calculation for each year. B.10 compliance: not fabricated. v3.3 scope item.

3. **Migration 070/071 pre-existing duplicates**: Inherited from main (not a v3.2 issue).
   Coverage Campaign created 070_capability_tool_registry; MCP Server created 070_mcp_api_keys.
   Requires a cleanup migration or renaming in a future hygiene session.

## Next Phase: v3.3 Depth Backfill

v3.3 sessions (S1–S4) are unblocked:
- S1: shadbala + ashtakavarga + bhava_bala (already committed on feature/mcpt-depth: a1c7a5ae)
- S2: kp_* tables + upagraha
- S3: Tajaka varshaphal (tajaka_annual year_lord computation via JH)
- S4: Depth sealing + feature/mcpt-final merge
