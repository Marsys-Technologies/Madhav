---
artifact: CLAUDECODE_BRIEF_MCPT_V32_S1_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.2-S1
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-BPHS
branch: feature/mcpt-bphs
depends_on: []                                                          # data-only; starts Day 1 in parallel
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: BPHS (Brihat Parashara Hora Shastra) corpus indexing into classical_texts table
source_data: 00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/
---

# v3.2-S1 — BPHS Indexing

You are a Claude Code sub-agent on WT-B (`MadhavMCPT-BPHS`, branch `feature/mcpt-bphs`). Your job is to ingest the Brihat Parashara Hora Shastra corpus into the `classical_texts` table for downstream use by the `read_classical_text` MCP tool and by `cross_school_lookup` citations.

Read: `MCP_ARCH_v3_PROPOSAL §3.3 (read_classical_text), §9.2 (backfill priorities)`; `MCP_PERF_SYSTEM_BRIEF §4.2 (mv_data_source_coverage UNION block)`; `MCP_TRANSFORMATION_PLAN §6` (source-data manifest).

## §1 — Scope

Ingest BPHS chapters 1–30 (minimum) from cleaned-text source files into `classical_texts`. Per-verse rows with `work`, `chapter`, `verse`, `sanskrit_text`, `translation_text`, `commentary_text` (if available), `source_edition`. Index for RAG via `rag_chunks` + Vertex 768-dim embeddings.

## §2 — Source data prerequisite

Files at `00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/{chapter_NN}.txt` (or `.md`) with one verse per logical block. Operator-staged per `MCP_TRANSFORMATION_PLAN §6`. If a chapter file is missing or empty, the sub-agent halts with `MISSING_SOURCE_DATA` and includes the missing chapter list in its FINAL_SUMMARY.

## §3 — Files in scope

```
platform/scripts/bootstrap/bootstrap_classical_texts_bphs.ts             # new ingestion script
platform/scripts/bootstrap/lib/classical_text_chunker.ts                 # verse-level chunker (shared with v3.2-S2, S3)
platform/scripts/bootstrap/lib/classical_text_embedder.ts                # Vertex 768-dim embedder (shared)
platform/test/bootstrap/bphs_ingestion.test.ts                           # ingestion unit tests
00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_BPHS_v1_0.md                     # operator-facing record of what was indexed
```

No migrations (uses existing `classical_texts` and `rag_chunks` tables).

## §4 — Files NOT in scope

```
platform/src/lib/retrieve/**                                             # no tool changes (S1 territory of WT-A)
platform-mcp/**                                                          # no MCP-server changes
01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**                             # untouched
00_ARCHITECTURE/CONDUCTOR/**                                             # not Conductor work
```

## §5 — Ingestion specification

For each chapter file:
1. Parse into verses (one row per verse). Verse identifier format: `BPHS.{chapter:02d}.{verse:03d}` (e.g. `BPHS.08.012`).
2. INSERT INTO `classical_texts (work, chapter, verse, sanskrit_text, translation_text, commentary_text, source_edition, ingested_at, build_id)` with `build_id = 'mcpt-v32-bphs-<YYYYMMDD-HHMM>'`.
3. Chunk for RAG: each verse becomes one chunk (~200–400 tokens of combined sanskrit + translation + commentary). Compute Vertex 768-dim embedding via `classical_text_embedder.ts`.
4. INSERT INTO `rag_chunks` + `rag_embeddings`.
5. UPSERT `data_source_expected` row for `('classical_texts', 'BPHS')` with `expected_row_count` set to the total verses ingested.

## §6 — Build manifest

After all chapters ingest successfully, INSERT INTO `build_manifests (asset_id, build_id, started_at, completed_at, row_count, source_metadata)` so the data-coverage view reflects the bootstrap. Per the v1.3 carry-forward item to audit `bootstrap_panchanga.py` (CLAUDE.md §E), this brief explicitly registers its build manifest — do not skip.

## §7 — Acceptance criteria

- **AC.S1.1** — `SELECT count(*) FROM classical_texts WHERE work='BPHS'` returns ≥ 1000 (BPHS has ~30 chapters × ~50 verses average minimum).
- **AC.S1.2** — `SELECT DISTINCT chapter FROM classical_texts WHERE work='BPHS' ORDER BY chapter` returns chapters 1 through at least 30.
- **AC.S1.3** — `SELECT count(*) FROM rag_chunks WHERE source_canonical_id LIKE 'classical_texts/BPHS%'` ≥ 1000.
- **AC.S1.4** — `SELECT 1 FROM build_manifests WHERE asset_id='classical_texts' AND build_id LIKE 'mcpt-v32-bphs-%' AND completed_at IS NOT NULL` returns exactly one row.
- **AC.S1.5** — After v3.1.0-S4 merges, calling `data_coverage({asset_id:"classical_texts", subkey:"BPHS"})` shows `coverage_pct: ≥ 0.9` against the expected count.

## §8 — Workflow

1. `git checkout -b feature/mcpt-bphs`.
2. Author shared chunker + embedder libs at `platform/scripts/bootstrap/lib/`.
3. Author `bootstrap_classical_texts_bphs.ts`.
4. Run: `npx tsx platform/scripts/bootstrap/bootstrap_classical_texts_bphs.ts --staging` (verify against staging DB first).
5. Commit per chapter or per major step (`MCPT v3.2-S1: BPHS chapter NN ingested`).
6. After staging verification, run against production.
7. Commit final `MCPT v3.2-S1: BPHS ingestion complete (N rows, build_id mcpt-v32-bphs-...)`.
8. Push.

## §9 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-BPHS && \
  test -f platform/scripts/bootstrap/bootstrap_classical_texts_bphs.ts && \
  test -f platform/scripts/bootstrap/lib/classical_text_chunker.ts && \
  test -f 00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_BPHS_v1_0.md && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM classical_texts WHERE work='BPHS'" | grep -qE "^\s+[1-9][0-9]{3,}" && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM build_manifests WHERE asset_id='classical_texts' AND build_id LIKE 'mcpt-v32-bphs-%'" | grep -q "1"
```

## §10 — Sealing artifact

`00_ARCHITECTURE/MCPT_V32_S1_CLOSE.md`. Body: per-chapter ingestion row count, RAG indexing evidence, build_manifest entry.

---

*End of CLAUDECODE_BRIEF_MCPT_V32_S1_v1_0.md.*
