---
session_id: DAR-P3-S9
phase: 3
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P3-S8]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/RAG_CHUNKS_MSR_REPORT.md  # create
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - platform/migrations/
---

# DAR-P3-S9: Rebuild MSR rag_chunks + re-embed vectors

## Context

`msr_signals` now has 573 rows from MSR v5.0. The `rag_chunks` table (canonical_id='MSR')
still contains chunks from v3.x and needs to be rebuilt. This session deletes stale MSR
rag chunks, rechunks from MSR v5.0 (573 signals → 573 chunks), and triggers re-embedding.

## Steps

1. Delete stale MSR rag chunks:
   ```bash
   psql "$DATABASE_URL" -c "DELETE FROM rag_chunks WHERE canonical_id = 'MSR';"
   ```
   Verify: `SELECT COUNT(*) FROM rag_chunks WHERE canonical_id = 'MSR';` → 0

2. Run the MSR signal chunker to create 573 new chunks:
   ```bash
   cd platform/python-sidecar
   python3 -m rag.chunkers.msr_signal \
     --source ../../025_HOLISTIC_SYNTHESIS/MSR_v5_0.md \
     --canonical-id MSR
   ```
   Adapt flags to actual chunker interface.

3. Verify chunk count:
   ```bash
   psql "$DATABASE_URL" -c "SELECT source_version, COUNT(*) FROM rag_chunks WHERE canonical_id='MSR' GROUP BY source_version;"
   ```
   Expected: `5.0 | 573`

4. Trigger embedding for the new chunks:
   ```bash
   python3 -m rag.embedder --canonical-id MSR --batch-size 50
   ```
   Monitor until all 573 chunks have `embedding IS NOT NULL`.
   Verify:
   ```bash
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM rag_chunks WHERE canonical_id='MSR' AND embedding IS NULL;"
   ```
   Expected: 0

5. Create `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/RAG_CHUNKS_MSR_REPORT.md`:
   ```yaml
   # MSR rag_chunks Rebuild Report
   # Generated: [timestamp]

   canonical_id: MSR
   source_version: 5.0
   msr_rag_chunks_count: 573
   chunks_with_embedding: 573
   null_embeddings: 0
   embed_status: COMPLETE
   ```

6. Commit:
   ```
   dar: P3-S9 rebuild MSR rag_chunks from v5.0 (573 chunks) + re-embed
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/RAG_CHUNKS_MSR_REPORT.md` → TRUE
- `grep 'msr_rag_chunks_count: 573' RAG_CHUNKS_MSR_REPORT.md` → match
- `grep 'embed_status: COMPLETE' RAG_CHUNKS_MSR_REPORT.md` → match
