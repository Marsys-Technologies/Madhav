---
artifact: CLAUDECODE_BRIEF_MCPT_V32_S2_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.2-S2
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-JK
branch: feature/mcpt-jaim-kp
depends_on: []                                                          # parallel-eligible from Day 1
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: Jaimini Sutram + KP Reader indexing into classical_texts
source_data: 00_ARCHITECTURE/SOURCE_DATA/classical_texts/Jaimini_Sutram/ + .../KP_Reader/
---

# v3.2-S2 — Jaimini Sutram + KP Reader Indexing

You are a Claude Code sub-agent on WT-C (`MadhavMCPT-JK`). Ingest two classical corpora: Jaimini Sutram (4 padas × 4 adhyayas) and KP Reader (volumes 1–6).

Read: `MCP_ARCH §3.3, §9.2`; `MCP_TRANSFORMATION_PLAN §6`; the v3.2-S1 brief (shares the chunker + embedder libs from `platform/scripts/bootstrap/lib/`).

## §1 — Scope

Two ingestions in one session:
- Jaimini Sutram full text → `classical_texts.work='Jaimini Sutram'`. ~400 sutras across 16 padas. Sutra ID format: `JS.{adhyaya}.{pada}.{sutra:03d}`.
- KP Reader Volumes 1–6 → `classical_texts.work='KP Reader Vol N'`. OCR-cleaned PDFs accepted. Section ID format: `KP.Vol{N}.Ch{NN}.S{NN}`.

## §2 — Source data prerequisites

- `00_ARCHITECTURE/SOURCE_DATA/classical_texts/Jaimini_Sutram/full.txt` (or per-adhyaya files)
- `00_ARCHITECTURE/SOURCE_DATA/classical_texts/KP_Reader/vol{1..6}/` (cleaned-text OR PDF + OCR-stage allowed)

If KP source is PDF-only, this session runs OCR via `tesseract` or equivalent as a pre-step. Brief allows "best-effort indexing" where OCR quality is degenerate — flag affected sections in the sealing artifact.

## §3 — Files in scope

```
platform/scripts/bootstrap/bootstrap_classical_texts_jaimini.ts          # new
platform/scripts/bootstrap/bootstrap_classical_texts_kp.ts               # new (includes OCR step if needed)
platform/scripts/bootstrap/lib/ocr_pipeline.ts                           # new shared helper if KP needs OCR
platform/test/bootstrap/jaimini_ingestion.test.ts
platform/test/bootstrap/kp_ingestion.test.ts
00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_JAIMINI_v1_0.md
00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_KP_v1_0.md
```

Reuses `platform/scripts/bootstrap/lib/classical_text_chunker.ts` + `classical_text_embedder.ts` from v3.2-S1. **Cross-WT note:** these helpers are authored on `feature/mcpt-bphs` (WT-B). Coordination required: WT-C rebases against `feature/mcpt-bphs` before authoring its scripts, OR WT-B commits the helpers first and pushes within Wave 1 Day 1 hour 1. Recommended: WT-B authors the helpers AS ITS FIRST COMMIT (before any BPHS ingestion logic) and pushes immediately, so WT-C can rebase within the same hour.

## §4 — Files NOT in scope

Same as v3.2-S1.

## §5 — Per-ingestion specification

### Jaimini Sutram

For each adhyaya/pada/sutra:
1. Parse into rows: `work='Jaimini Sutram'`, `chapter='{adhyaya}.{pada}'`, `verse='{sutra_number}'`, plus sanskrit + translation + commentary.
2. INSERT INTO `classical_texts` with `build_id='mcpt-v32-jaimini-<timestamp>'`.
3. RAG chunk + embed.

### KP Reader (vol 1–6)

For each volume/chapter/section:
1. If source is PDF, run OCR via `ocr_pipeline.ts`. Reject pages where OCR confidence < 0.7 and flag for operator review.
2. Parse into sections (KP doesn't have verses; uses prose sections).
3. INSERT INTO `classical_texts` with `work='KP Reader Vol N'`, `chapter='Ch{NN}'`, `verse='S{NN}'`, `build_id='mcpt-v32-kp-<timestamp>'`.
4. RAG chunk + embed.

## §6 — Acceptance criteria

- **AC.S2.1** — `SELECT count(*) FROM classical_texts WHERE work='Jaimini Sutram'` ≥ 350 (16 padas × ~25 sutras average).
- **AC.S2.2** — `SELECT count(*) FROM classical_texts WHERE work LIKE 'KP Reader Vol%'` ≥ 1500 (6 volumes × ~250 sections average).
- **AC.S2.3** — RAG chunks present for both works.
- **AC.S2.4** — `build_manifests` entries for both ingestions.
- **AC.S2.5** — OCR quality report attached to sealing artifact (KP only); sections with confidence < 0.7 listed for operator review.

## §7 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-JK && \
  test -f platform/scripts/bootstrap/bootstrap_classical_texts_jaimini.ts && \
  test -f platform/scripts/bootstrap/bootstrap_classical_texts_kp.ts && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM classical_texts WHERE work='Jaimini Sutram'" | grep -qE "^\s+[3-9][0-9]{2,}" && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM classical_texts WHERE work LIKE 'KP Reader%'" | grep -qE "^\s+1[5-9][0-9]{2}|^\s+[2-9][0-9]{3,}"
```

## §8 — Sealing artifact

`00_ARCHITECTURE/MCPT_V32_S2_CLOSE.md`. Body: per-work row counts, OCR quality report (KP), build_manifest entries.

---

*End of CLAUDECODE_BRIEF_MCPT_V32_S2_v1_0.md.*
