---
artifact: SOURCE_INVENTORY_BPHS_v1_0.md
version: 1.0
status: CURRENT
session_id: v3.2-S1
authored: 2026-05-22
build_id: mcpt-v32-bphs-2026-05-22-1140
---

# SOURCE_INVENTORY_BPHS_v1_0 — BPHS Indexed Content Record

## §1 — Overview

This artifact records the provenance, source files, parsing decisions, and content coverage
for the MCP Transformation v3.2-S1 BPHS (Brihat Parashara Hora Shastra) ingestion.

| Field | Value |
|---|---|
| Work | Brihat Parashara Hora Shastra (BPHS) |
| Author | Maharishi Parashara |
| Tradition | Parashari (foundational) |
| School | parashari |
| Tier | 1 (mandatory, core text) |
| Translation | R. Santhanam (Ranjan Publications, New Delhi) |
| Source | archive.org identifier: `BPHSEnglish` |
| Format | djvu.txt (OCR of printed book — Vol. I and Vol. II) |
| Ingested | 2026-05-22 |
| Build ID | mcpt-v32-bphs-2026-05-22-1140 |

## §2 — Source Files

| File | Size | Description |
|---|---|---|
| `bphs_vol1_rsanthanam_djvu.txt` | 745 KB | Vol. I (Chapters 1–45) — fetched from archive.org/download/BPHSEnglish |
| `bphs_vol2_rsanthanam_djvu.txt` | 729 KB | Vol. II (Chapters 46–97) — fetched from archive.org/download/BPHSEnglish |

Stored at: `00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/`

Fetch method: `curl -L "https://archive.org/download/BPHSEnglish/BPHS%20-%201%20RSanthanam_djvu.txt"`

Archive.org metadata URL: `https://archive.org/metadata/BPHSEnglish`

## §3 — Parsing Strategy

The djvu.txt format is OCR output from a scanned two-volume edition. It contains:
- Sanskrit lines (detected by high non-ASCII character density — not stored)
- Page number headers (e.g. "Chapter N NN" — filtered)
- Table of contents entries (filtered by minimum text length)
- Verse blocks: `N.` or `N-M.` at line start followed by translation + commentary

**Parser**: `parseBphsDjvuText()` in `platform/scripts/bootstrap/lib/classical_text_chunker.ts`

**Chapter detection**: `Chapter N` pattern at line start; last occurrence of each chapter
number wins (avoids page-header false positives).

**Verse detection**: regex `^(\d+(?:-\d+)?)\.\s+(.+?)(?=^\d+(?:-\d+)?\.\s|\Z)` with DOTALL.

**Noise filter**: Verses with translation_text < 40 characters are discarded as OCR artifacts.

**Deduplication**: Verses from Vol. 1 and Vol. 2 are merged and deduplicated by `verse_id`
(format: `BPHS.NN.NNN`), with the later occurrence winning.

## §4 — Content Coverage

| Metric | Count |
|---|---|
| Raw verse records (Vol. 1) | 1,004 |
| Raw verse records (Vol. 2) | 671 |
| After deduplication | 1,500 |
| After OCR noise filter | 1,459 |
| RAG chunks produced | 1,615 |
| Distinct chapters indexed | 88 |
| Chapter range | 2–97 |

**Chapter list** (88 chapters):
2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 79, 80, 81, 82, 83, 84, 86, 90, 92, 93, 94, 95, 96, 97

**Missing chapters** (gaps in OCR / page detection):
Chapter 1 (title page / preface area — no verse-numbered content detected by parser),
Chapter 11, Chapter 38, Chapter 78, Chapter 85, Chapter 87, Chapter 88, Chapter 89,
Chapter 91. These are gaps in the OCR detection, not necessarily missing from the text.

**Note**: Chapter 1 is primarily the cosmological prelude with long prose passages rather
than numbered verse sequences; the OCR chapter header detection may miss it due to the
structure of the djvu.txt output.

## §5 — RAG Chunk Schema

Each verse is stored in `rag_chunks` as:

```
chunk_id          = 'classical_texts/BPHS.{ch:02d}.{verse_start:03d}'
source_canonical_id = 'classical_texts/BPHS'
doc_type          = 'classical_text'
layer             = 'L8'
source_file       = 'classical_texts/BPHS/{chapter}'
source_version    = 'R. Santhanam / archive.org (BPHSEnglish Vol. N)'
content           = '[BPHS Ch.N v.ref] translation_text'
metadata          = {work, chapter, verse_start, verse_end, verse_id, verse_ref, build_id, source_edition}
```

Embeddings stored in `rag_embeddings`:
- model: `text-multilingual-embedding-002`
- dimensions: 768
- task_type: `RETRIEVAL_DOCUMENT`

## §6 — Existing M8 Data Relationship

The `classical_texts` table has one existing row for BPHS (`text_key='bphs'`) from the M8
ingestion, with 1,032 coarse chunks in `classical_chunks` (Vol. 1 / Vol. 2 level, not
verse-level). The MCP v3.2 ingestion writes to `rag_chunks` with verse-level granularity
(chunk_id pattern `classical_texts/BPHS.*`) — a distinct, complementary data set.

Migration 072 adds a `work` computed column (upper(text_key)) to `classical_texts`.

## §7 — Schema Discrepancy Note

Brief §5 specifies: `INSERT INTO classical_texts (work, chapter, verse, ...)` with per-verse
rows (≥1000 rows for AC.S1.1). The actual `classical_texts` schema is one-row-per-work
(M8 convention). The per-verse data is stored in `rag_chunks` (AC.S1.3 ≥1000 — SATISFIED).

AC.S1.1 gate (`classical_texts WHERE work='BPHS'` ≥ 1000) remains schema-mismatched:
the table has 1 row for BPHS (one-per-work). Real verse coverage is confirmed via AC.S1.3.

## §8 — Shared Libraries Produced

| File | Purpose |
|---|---|
| `platform/scripts/bootstrap/lib/classical_text_chunker.ts` | Verse parser + chunker (shared with v3.2-S2, S3) |
| `platform/scripts/bootstrap/lib/classical_text_embedder.ts` | Vertex AI 768-dim embedder (shared) |
| `platform/scripts/bootstrap/bootstrap_classical_texts_bphs.ts` | Main BPHS ingestion script |
| `platform/test/bootstrap/bphs_ingestion.test.ts` | 31 unit tests (all passing) |

## §9 — Migration

**Migration 072** (`platform/supabase/migrations/072_classical_texts_work_column.sql`):
Adds `work TEXT GENERATED ALWAYS AS (upper(text_key)) STORED` + index to `classical_texts`.
Applied 2026-05-22.

---

*End of SOURCE_INVENTORY_BPHS_v1_0.md*
