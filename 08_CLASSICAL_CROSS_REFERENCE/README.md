---
artifact: 08_CLASSICAL_CROSS_REFERENCE/README.md
version: 1.0
status: CURRENT
governing_macro_phase: M8 — Classical Text Cross-Reference
created_at: 2026-05-14
created_by: M8-A-S1
---

# 08_CLASSICAL_CROSS_REFERENCE

M8 phase artifact layer. Indexed corpus of canonical classical Jyotish texts,
cross-referenced against every MSR signal and M5 probabilistic output.

## Structure

```
08_CLASSICAL_CROSS_REFERENCE/
├── README.md                           ← this file
├── PROCUREMENT_MAP_v1_0.md             ← 14-text tier list with source URLs
├── M8_CLOSE_v1_0.md                    ← authored at M8-H-S1 close
├── corpus/
│   ├── ingestion/
│   │   ├── scripts/                    ← per-text Python ingestion scripts
│   │   └── logs/                       ← per-run ingestion logs (gitignored)
│   └── raw/                            ← raw fetched text (gitignored; GCS canonical)
├── attributions/
│   ├── CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md
│   ├── CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json
│   └── findings/
│       ├── FINDINGS_M5_CROSS_REF_v1_0.md
│       └── FINDINGS_CLASSICAL_CLAIM_v1_0.md
├── nadi_bnn/
│   ├── NADI_SIGNAL_EXTRACTION_v1_0.md
│   ├── BNN_SIGNAL_EXTRACTION_v1_0.md
│   └── MSR_EXPANSION_PROPOSAL_v1_0.md
└── quality/
    ├── TRANSLATION_CROSS_CHECK_v1_0.md
    └── ACHARYA_REVIEW_SAMPLE_v1_0.md
```

## Database tables (migrations 053–055)

| Table | Migration | Purpose |
|---|---|---|
| `classical_texts` | 053 | One row per text; tier, source metadata |
| `classical_chunks` | 054 | Chunked text with pgvector embeddings (768-dim) |
| `classical_attributions` | 055 | MSR signal × chunk attribution records |

## GCS Location

`gs://madhav-marsys-sources/L8/` — see [GCS_LAYOUT_v1_0.md](../00_ARCHITECTURE/GCS_LAYOUT_v1_0.md) §L8 block.

## LLM Stack

- Ingestion (non-critical): gemini-2.5-flash-lite
- Attribution judge / signal extraction (critical): gemini-2.5-pro or deepseek-v4-pro
- Embedding: Vertex AI text-embedding-004 (768-dim)

**No Anthropic/Claude API in any M8 code.**
