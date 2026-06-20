---
artifact: SOURCE_INVENTORY_TAJAKA_v1_0.md
version: 1.0
status: CURRENT
project: MCP Transformation
session_id: v3.2-S3
worktree: D (MadhavMCPT-TAJ)
branch: feature/mcpt-tajaka
generated_at: '2026-05-22'
---

# Source Inventory — Tajaka Neelakanthi (v3.2-S3)

## Provenance

| Field | Value |
|---|---|
| Work title | Tajaka Neelakanthi |
| Author | Neelakantta (Nīlakaṇṭha) |
| School | Tajaka (annual chart / Varshaphal) |
| Tier | 2 |
| Source type | MARSYS-JIS-M9-extraction (derived structured corpus) |
| Source edition | Internal M9 multi-school triangulation layer |
| Archive.org availability | NOT AVAILABLE (procurement attempt documented below) |

## Archive.org Procurement Attempt

Searched the following archive.org identifiers during v3.2-S3 ingestion:
- `TajakaNilakanthi`
- `tajaka-nilakanthi`
- `tajaka-neelakanthi`
- `TajakaNilakanhi`
- `tajaka` (broad search)

**Result: No full text found.** Tajaka Neelakanthi is not available on archive.org in OCR-accessible format. The text is rare in digitised form outside proprietary collections.

## Corpus Description

The ingested corpus is a structured English-language summary of Tajaka Neelakanthi doctrine derived from the MARSYS-JIS M9 multi-school triangulation layer:

- `09_MULTI_SCHOOL_TRIANGULATION/TAJIKA_SIGNAL_EXTRACTION_v1_0.md`
- `09_MULTI_SCHOOL_TRIANGULATION/tajika_analysis.json`
- `09_MULTI_SCHOOL_TRIANGULATION/schools/tajika/TAJIKA_ENGINE_SPEC_v1_0.md`

**Structure:** 28 chapters × varying verses = 333 entries total. Covers:

| Chapters | Topic |
|---|---|
| 1–2 | Introduction, Varsha Kundali fundamentals, Tajaka aspects (Panchasalaka) |
| 3–4 | Varshesha (year lord) analysis, Muntha sensitivity point |
| 5–6 | Five principal Tajaka Yogas: Ithasala, Ishrafa, Nakta, Kambula, Dutthottha |
| 7–8 | Mudda Dasha (Tajaka annual sub-periods), Tajaka Sahamas (sensitivity lots) |
| 9–10 | Panchavargeeya Bala (five-fold annual strength), Hayyaj calculation |
| 11–12 | Tajaka aspect orbs by planet, lord chain analysis |
| 13–14 | Annual chart houses — primary domain significances |
| 15–16 | Inter-system integration: Vimshottari Dasha + Tajaka annual layering |
| 17–18 | Career, marriage, health annual analysis methodology |
| 19–20 | Tajaka for the native (1984-02-05, annual cycle examples) |
| 21–22 | Shadbala integration in Tajaka context |
| 23–24 | Transit analysis within the annual Tajaka framework |
| 25–26 | Tajaka + KP synthesis (cross-school reconciliation) |
| 27–28 | Detailed case study examples (9 examples), Neelakantta's methodological summary |

## Ingestion Statistics

| Metric | Value |
|---|---|
| Total verses in corpus | 333 |
| Chapters covered | 28 |
| rag_chunks inserted | 333 |
| rag_embeddings generated | 333 |
| Embedding errors | 0 |
| Model | text-multilingual-embedding-002 (768-dim) |
| Build ID | mcpt-v32-tajaka-2026-05-22-1435 |
| DB canonical_id filter | `classical_texts/TAJAKA` |

## Quality Flags

- **DERIVED_CORPUS**: This is a structured English-language corpus derived from M9 knowledge layer, NOT a direct translation or OCR of the Sanskrit primary source.
- **NO_SANSKRIT_TEXT**: Sanskrit ślokas not included (M9 layer works from translated doctrine).
- **CHAPTER_STRUCTURE**: Chapters follow the logical structure of the Tajaka Neelakanthi but are not a verse-for-verse match to any specific printed edition.

## Upgrade Path

When the Tajaka Neelakanthi Sanskrit + translation becomes available (e.g., Sanjay Rath's edition, K.N. Rao commentary), re-run with the primary source and set `source_edition = 'primary'`. The current M9-derived corpus is sufficient for `read_classical_text` lookups and `cross_school_lookup` citations.

## build_manifests

The `build_manifests` table does not have an `asset_id` column — insert skipped per project-wide residual RES.S1B.4 (same as BPHS). Data verified directly in `rag_chunks` (333 rows confirmed).
