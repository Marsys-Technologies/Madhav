---
artifact: CLAUDECODE_BRIEF_MCPT_V32_S3_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.2-S3
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-TAJ
branch: feature/mcpt-tajaka
depends_on: []                                                          # parallel-eligible from Day 1
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: Tajaka Neelakanthi corpus indexing
source_data: 00_ARCHITECTURE/SOURCE_DATA/classical_texts/Tajaka_Neelakanthi/
---

# v3.2-S3 — Tajaka Neelakanthi Indexing

You are a Claude Code sub-agent on WT-D (`MadhavMCPT-TAJ`). Ingest Tajaka Neelakanthi (the canonical Tajaka classical text) into `classical_texts`. Smallest of the three v3.2 text-indexing sessions; the Tajaka school is the most under-served at v3.1 start (20% coverage in multi-school tables), so this corpus unblocks the Tajaka rubric capability.

Read: `MCP_ARCH §3.3, §9.2`; `MCP_TRANSFORMATION_PLAN §6`; v3.2-S1 brief for shared chunker + embedder usage.

## §1 — Scope

Ingest Tajaka Neelakanthi (single text, ~500 verses across ~20 chapters depending on edition). Per-verse rows in `classical_texts.work='Tajaka Neelakanthi'`. RAG-indexed.

## §2 — Source data prerequisite

`00_ARCHITECTURE/SOURCE_DATA/classical_texts/Tajaka_Neelakanthi/full.txt` or per-chapter files. If missing, halt with `MISSING_SOURCE_DATA`.

## §3 — Files in scope

```
platform/scripts/bootstrap/bootstrap_classical_texts_tajaka.ts           # new
platform/test/bootstrap/tajaka_ingestion.test.ts
00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_TAJAKA_v1_0.md
```

Reuses shared chunker + embedder libs (rebase against `feature/mcpt-bphs` for those helpers, same as WT-C).

## §4 — Files NOT in scope

Same as v3.2-S1.

## §5 — Ingestion specification

Per-verse: `work='Tajaka Neelakanthi'`, `chapter='{NN}'`, `verse='{NNN}'`, sanskrit + translation + commentary, `build_id='mcpt-v32-tajaka-<timestamp>'`. RAG chunk + embed. `build_manifests` entry on completion.

## §6 — Acceptance criteria

- **AC.S3.1** — `SELECT count(*) FROM classical_texts WHERE work='Tajaka Neelakanthi'` ≥ 400.
- **AC.S3.2** — `SELECT count(*) FROM rag_chunks WHERE source_canonical_id LIKE 'classical_texts/Tajaka%'` ≥ 400.
- **AC.S3.3** — `build_manifests` entry present.

## §7 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-TAJ && \
  test -f platform/scripts/bootstrap/bootstrap_classical_texts_tajaka.ts && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM classical_texts WHERE work='Tajaka Neelakanthi'" | grep -qE "^\s+[4-9][0-9]{2,}|^\s+[1-9][0-9]{3,}"
```

## §8 — Sealing artifact

`00_ARCHITECTURE/MCPT_V32_S3_CLOSE.md`. Body: row counts, build manifest, RAG indexing evidence.

---

*End of CLAUDECODE_BRIEF_MCPT_V32_S3_v1_0.md.*
