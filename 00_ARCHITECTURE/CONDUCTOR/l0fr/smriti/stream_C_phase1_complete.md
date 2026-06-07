---
artifact: stream_C_phase1_complete.md
stream: C
phase: 1
status: MIDWAY_COMPLETE
authored: 2026-06-07T06:38+05:30
texts_ingested: 3
chunk_count_total: 2643
embedded_count: 2643
embedding_coverage_pct: 100.0
smoke_test_1: PASS
smoke_test_2: PASS
---

# Stream C — Phase 1 Complete (BPHS + Phaladeepika + Jataka Parijata)

## Summary

All 3 Phase 1 texts ingested, chunked, and embedded at 100% coverage.

## Chunk counts per text

| text_id | chunks | embedded | coverage |
|---|---|---|---|
| bphs | 1723 | 1723 | 100% |
| phaladeepika | 179 | 179 | 100% |
| jataka_parijata | 741 | 741 | 100% |
| **TOTAL** | **2643** | **2643** | **100%** |

## Sample verse refs

### BPHS
- `CH1:V1` — "EFFECTS OF ASCENDANT LORD IN VARIOUS HOUSES — Should the ascendant lord be in the ascendant itself..."
- `CH7:V14` — "Khavedamsa for auspicious and inauspicious effects..."
- `CH24:V67` — "If the 6th lord is in the 7th, the native will be deprived of happiness through wife..."
- `CH83:V2` — "Mars, Rahu, the Sun and Saturn are in the Ascendant, the 5th, the 8th and the..."

### Phaladeepika
- `CH5:V1-V7` — Index/appendix matter (OCR back-matter; parked quality)
- `CH9:V1` — Actual body content beginning from Chapter 9
- `CH10:V1` through `CH33` — Substantive astrological content

### Jataka Parijata
- `CH1:V1` — "Men experience good when the Ishta portion of a planet's influence..."
- `CH1:V5` — "The Karaka of the 3rd bhava that is strong and at an advantageous position..."
- Chapter range: 1 through multiple adhyayas

## Source files

- BPHS: Internet Archive `BPHSEnglish` (djvu.txt vol1+vol2, R. Santhanam ed.)
- Phaladeepika: Internet Archive `Phaladeepika2ndEd.1950ByVSubrahmanyaSastri` (V. Subrahmanya Sastri ed.)
- Jataka Parijata: Internet Archive `JatakaParijataVolIOfIIByVSubrahmanyaSastri` (V. Subrahmanya Sastri ed., vol 1 only)

## Smoke tests

| Test | Query/Key | Expected | Result |
|---|---|---|---|
| Vector search | "Mars in 7th house" | ≥3 chunks with Mars/Mangal/Kuja | PASS — top result BPHS CH83:V2 (sim=0.735) contains "Mars" |
| Direct lookup | BPHS CH7:V14 | non-null chunk with content | PASS — content: "Khavedamsa for auspicious and inauspicious effects" |

## Notes

1. Phaladeepika chapters 5, 8 appear to be OCR of back-matter index — valid parked quality. Chapters 9+ contain substantive astrological content.
2. Jataka Parijata vol 2 not yet ingested (Internet Archive IA ID: `JatakaParijataVolIIOfIIByVSubrahmanyaSastri`). Vol 1 complete (741 chunks).
3. Embedding model: `text-multilingual-embedding-002` (768-dim Vertex AI, deterministic).
4. The `text-multilingual-embedding-002` REST API has a 20,000 token limit per batch. Batch size set to 50 with recursive halving on 400 errors.
5. DB tables populated: `classical_texts` (3 rows), `classical_texts_source` (3 rows), `classical_text_chunks` (2,643 rows + embeddings).

## Files authored this phase

- `platform/python-sidecar/brahmagyan/l0_text_chunker.py` — deterministic regex chunker
- `platform/python-sidecar/brahmagyan/l0_text_embedder.py` — Vertex AI embedder
- `platform/python-sidecar/brahmagyan/l0_text_ingest.py` — ingestion runner
- `platform/python-sidecar/brahmagyan/l0_embed_runner.py` — robust embedding runner (batch-size-aware, token-limit-safe)

## Ready for Vimarśaka-C review

Awaiting `state.yaml: gates.vimarsaka_c.status = midway_pass` before proceeding to texts 4–15.
