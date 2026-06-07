---
artifact: CLAUDECODE_BRIEF_L0FR_STREAM_C_v1_0.md
stream: C — Classical Text Ingestion + Capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavL0FR-C
branch: feature/l0fr-stream-c-text-ingestion
budget_cap_usd: 200
tier3_escalation_usd: 5000
v1.0_note: Deterministic-first per memory feedback_deterministic_first_for_data_build (2026-06-07)
---

# Stream C — Classical Text Ingestion (Deterministic-First)

## §0-§0.5
Master plan, source data, Vimarśaka specs required reading.

**Deterministic-first principle:** PyMuPDF + Python regex for ingestion. NO Gemini for chunking. NO Document AI unless PyMuPDF fails on a specific PDF. Embeddings are kept (deterministic transformation, not generative LLM).

## §1 — Mission
Ingest 15 classical texts (or subset available without manual upload) → parse into ~6,000+ verse chunks using Python regex → Vertex AI embed (deterministic) → register 8 retrieval capabilities. Midway gate after first 3 texts.

## §2 — Dependencies
Blocks on `state.yaml: gates.vimarsaka_a.status = pass`. Midway gate emits when 3 texts complete → Vimarśaka-C reviews → on pass, Stream D spawns + Stream C continues.

## §3 — Scope

### Phase 1 — Source acquisition (Python only)
1. Per source data §2, identify auto-downloadable texts (Internet Archive); skip manual-upload-required texts (log to `/tmp/l0fr_manual_upload_pending.txt`)
2. Download via `curl` or Internet Archive Python SDK to `/tmp/l0fr_texts/`
3. Upload PDFs to `gs://madhav-classical-texts/sources/<text_id>/`

### Phase 2 — Text extraction (PyMuPDF first, OCR fallback only on fail)
4. For each PDF: attempt `PyMuPDF` (`fitz`) text extraction
   - If text-layer present: extract directly (deterministic, fast, free)
   - Verify extracted text contains ≥20 sequences matching common verse markers (`||`, `॥`, `Verse \d`, etc.)
   - If verification fails: PyMuPDF couldn't find text-layer → fallback
5. Fallback ONLY for PyMuPDF failures: pytesseract with Sanskrit-trained data
   - Document AI as a last-resort second fallback (logged + budget-tracked)
6. Save raw extracted text per chapter to `/tmp/l0fr_texts/<text_id>/raw/CH<N>.txt`

### Phase 3 — Chunking (pure Python regex)
7. Author `platform/python-sidecar/brahmagyan/l0_text_chunker.py`:
   ```python
   VERSE_MARKERS = [
     r'॥\s*(\d+)\s*॥',            # Devanagari verse end with number
     r'\|\|\s*(\d+)\s*\|\|',      # ASCII verse end with number
     r'(?:Verse|Sloka|Sūtra)\s+(\d+)[.:]\s*(\d+)',  # "Verse 1.5"
     r'^\s*(\d+)\.\s+',           # numbered list "1. "
     r'\n\n(\d+)\s*[-:]\s*',      # paragraph-break + verse number
   ]
   
   def chunk_text(raw_text: str, text_id: str, chapter: int) -> list[Chunk]:
     # Try each marker pattern; for each match split into chunks
     # Each chunk = (verse_ref, content, char_offset, char_length)
     # If NO marker pattern produces ≥3 chunks for this chapter:
     #   → mark this chapter as PARK (manual review needed); skip; log
     # Heuristic safety:
     #   - chunk shorter than 50 chars → PARK
     #   - chunk longer than 2000 chars → PARK
     #   - chunk starts mid-sentence (no capital letter, no Sanskrit beginning marker) → PARK
   ```
8. Run chunker over all texts; parked chunks go to `/tmp/l0fr_chunks_parked.txt` for native review (post-seal)
9. For successful chunks: INSERT into `classical_text_chunks` with text_id, verse_ref, chapter, content_en, content_sa (if separable; otherwise null), translator, tradition_school, source_citation, content_sha256
10. Also populate `classical_texts_source` with per-text metadata (title, author, edition, etc. per source data §2)

### Phase 4 — Embedding (deterministic transformation, kept)
11. Author `platform/python-sidecar/brahmagyan/l0_text_embedder.py`:
    - For each chunk: concat (content_en + ' ' + content_sa); call Vertex AI `text-multilingual-embedding-002`
    - Embedding is a deterministic transformation — same text always produces the same 768-dim vector
    - Store vector in `classical_text_chunks.embedding`
    - After bulk insert, the HNSW index from Stream A's migration auto-builds
12. Embedding cost: ~$0.63 one-time for ~10,000 chunks. Acceptable per deterministic-first principle (embeddings are deterministic transforms, not generative LLM).

### Midway gate trigger
13. After first 3 texts (BPHS, Phaladeepika, Jataka Parijata) complete Phases 2+3+4:
    - Set `state.yaml: streams.C.status = midway_review`
    - Wait for `state.yaml: gates.vimarsaka_c.status = midway_pass`
    - On pass: continue with texts 4-15; also Stream D spawns

### Capability registrations
14. Tools (handlers are Python; no LLM at runtime for these):
    - `read_classical_text(text_id, verse_ref)` → SQL lookup
    - `read_chapter(text_id, chapter)` → SQL lookup
    - `search_classical_texts(query, top_k=5)` → embedding similarity (deterministic) + tsvector full-text combined; ranking via Python
    - `list_classical_texts()` → SQL lookup
    - `find_verses_about(topic, text_ids=null)` → embedding similarity + filter
15. Resources:
    - `marsys://resource/text/<text_id>/chapter/<n>` → dynamic resource loader (SQL)
    - `marsys://resource/text/<text_id>/index` → SQL lookup
16. Prompt:
    - `marsys://prompt/classical-canon` → static template (Python string)
17. All registered in BOTH MCP and Consume Chat; parity_check passes

### Smoke tests (Python-only)
18. Vector search: `search_classical_texts('Mars in 7th house')` returns ≥3 chunks (validated by Python check that returned chunks contain "Mars" OR "Mangal" OR "Kuja" tokens)
19. `read_classical_text('BPHS', 'CH7:V14')` returns a chunk row (validated by Python that result is non-null with content)

## §5 — Acceptance criteria (programmatic, Python-only)
- `SELECT count(*) FROM classical_text_chunks ≥ 6000` (chunks that passed regex chunking)
- `SELECT count(DISTINCT text_id) FROM classical_texts_source ≥ 6` (auto-downloadable subset; manual-upload deferred to post-seal)
- `SELECT count(*) FROM classical_text_chunks WHERE embedding IS NOT NULL = total chunk count` (every chunk embedded)
- Parked chunks documented at `/tmp/l0fr_chunks_parked.txt` (acceptable to have parked chunks; quality compromise accepted)
- Vector search smoke test (Python token check) PASS
- 8 capabilities registered; parity_check passes

## §6 — Budget
Tier-3 cap $200 (was $600). Cost breakdown:
- OCR (only fallback): ~$0-5 if PyMuPDF handles most PDFs
- Chunking: $0 (pure Python)
- Embeddings: ~$0.63 (one-time, deterministic)
- Smoke tests: <$1

## §7-§8 — Final summary
```yaml
---FINAL_SUMMARY---
stream: C
status: READY_FOR_REVIEW
texts_ingested: <N>/15
texts_pending_manual_upload: <list>
chunk_count_live: <N>
chunk_count_parked: <N>
embedded_chunk_count: <N>
capabilities_registered: 8/8
adapter_smoke_results: { ... }
budget_spent_usd: <N>
deterministic_compliance: 100% Python except deterministic embeddings
---END_FINAL_SUMMARY---
```
