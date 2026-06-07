# SESSION a4 — rag_chunks AC Assessment

Timestamp: 2026-06-05
Stream: postdeploy-a

## AC Definition (from CLAUDECODE_BRIEF_POSTDEPLOY_FIVE_STREAMS_v1_0 §1.A4)
```sql
SELECT count(*) FROM rag_chunks;
-- AC: count >= 4,589 (BPHS + Jaimini + KP + Tajaka + Remedy)
```

## Findings

### Table existence
`rag_chunks` table does NOT exist in the production database.

Evidence:
```sql
SELECT schemaname, tablename FROM pg_tables 
WHERE tablename IN ('rag_chunks', 'rag_chunks_staging');
-- Returns 0 rows
```

### Root Cause
The `001_baseline.sql` (brahma baseline squash) explicitly lists `rag_chunks` as a "DROP table" —
tables intentionally omitted from the baseline because they were part of the legacy RAG pipeline
(pre-MCP-Transformation). The note in §34 of the baseline reads:
> "Views referencing DROP tables (chart_facts, rag_chunks, msr_signals, ...) are intentionally OMITTED"

The MCP Transformation (migrations 072-080 per CLAUDE.md §E) was supposed to populate rag_chunks
with 4,589 rows but those migrations are in `platform/supabase/migrations/_archive/` (OPERATOR_ACTIONS_PENDING.md HIGH section marks them as "UNCONFIRMED").

### Current equivalent corpus
The WS-2 L0 architecture replaces the legacy `rag_chunks` table with:
- `classical_text_chunks` (from `ws2_l0_texts.sql` — not yet applied)
- `brahma_remedy_corpus` (55 rows — SEEDED GREEN, a3 PASS)
- `ephemeris_daily` (building — AMBER)

### a4 AC Status: INFRA_PENDING
The `rag_chunks >= 4,589` AC cannot pass because:
1. The table doesn't exist in the current prod schema (squashed out)
2. The MCP Transformation migrations that would create+populate it are archived/deferred
3. The WS-2 L0 architecture uses `classical_text_chunks` as the replacement

### Recommendation
Update a4 AC to check `classical_text_chunks` count once `ws2_l0_texts.sql` is applied.
Or: apply the legacy `rag_chunks` restoration migration from archive if the MCP sidecar requires it.
For now: a4 = INFRA_PENDING (pre-existing condition, not a Stream A regression).
