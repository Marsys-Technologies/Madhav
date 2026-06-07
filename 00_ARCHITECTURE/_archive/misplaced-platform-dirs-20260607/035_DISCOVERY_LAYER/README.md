---
artifact: 035_DISCOVERY_LAYER/README.md
version: "1.0"
status: CURRENT
produced_by: Madhav_17_B0
date: 2026-04-24
implements: PHASE_B_PLAN_v1_0.md §B.3 + §E.1 + §G B.0 Task 2
---

# 035_DISCOVERY_LAYER — L4 Discovery Layer

The Discovery Layer is the fourth architectural stratum of MARSYS-JIS, sitting above the L3
Domain Reports and receiving input from L2.5 Holistic Synthesis. Its purpose is to surface
emergent cross-domain patterns, resonances, contradictions, and clusters that are not visible
within any single domain report — the kinds of insights that require holding the entire
corpus in working memory simultaneously.

Per `PHASE_B_PLAN_v1_0.md §A` items 1 and 5:

1. **Surfaces patterns and contradictions across layers and systems** that no individual
   astrologer could hold in working memory — this is the Discovery Layer's primary value
   proposition over domain-siloed L3 analysis.

5. **Makes time-indexed, probabilistic, calibrated predictions testable against lived reality**
   — the Discovery Layer is the prediction-generation engine; all forward-looking claims
   emitted here are logged to `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl`
   before outcomes are observed (Learning Layer discipline rule #4 — held-out prospective data
   is sacrosanct).

## Directory Structure

```
035_DISCOVERY_LAYER/
├── README.md                     (this file)
├── REGISTERS/
│   └── INDEX.json                (discovery artifact register — populated B.5)
├── LEDGER/
│   └── .gitkeep                  (ledger events written by Hook 1 + Hook 2)
├── SCHEMAS/
│   └── chunker_spec_v1_0.md      (chunker specification — B.0 Task 12)
├── PROMPTS/
│   ├── gemini/
│   │   ├── .gitkeep
│   │   └── responses/            (raw Gemini response storage — Hook 3)
│   └── claude/
│       └── .gitkeep
├── RED_TEAM/
│   └── .gitkeep                  (red-team finding artifacts)
└── QUERY_TAXONOMY/
    └── (migrated from 06_QUERY_INTERFACE — B.0 Task 4)
```

## Activation Sequence

- **B.0 (this session):** Scaffold + migration. No discovery work yet.
- **B.1:** Ingestion — chunk L2.5 corpus into `rag_chunks` table.
- **B.2:** Chunker implementation — per `SCHEMAS/chunker_spec_v1_0.md`.
- **B.3:** Graph construction — citation edges + CGM edge proposals.
- **B.3.5:** CGM rebuild — `CGM_v9_0.md` with 8-karaka lock.
- **B.4:** RAG retrieval layer — hybrid vector + BM25 + graph.
- **B.5:** Discovery Layer activation — first live discovery runs; REGISTERS/INDEX.json populated.

## Layer Tags

All content produced in this layer carries the layer tag `[L4 Discovery Layer]`. Claims that
surface from the Discovery Layer and are routed back to users carry the disclosure tier per
`MACRO_PLAN_v2_0.md §Ethical Framework`.
