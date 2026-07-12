# FUSED 1b+5 shard — classical_text_chunks (1 family)

Rubric ratified (Charter v1.1 §7, GATE_RATIFICATION v1.1) — grading is FINAL, not provisional.

| family_key | channel | retrievability_verdict (1b) | fidelity_verdict (5) | derivation |
|---|---|---|---|---|
| `__table_row_count__=10651` | reachable-surgical | RETRIEVABLE — served by `read_classical_text` (internal tool_name `classical_text_search`), hybrid vector+keyword RAG; ok:true. Query-gated (no full-enum), correct for a corpus. | PASS — wire == DB byte-for-byte | path-grade(exemplar=`__table_row_count__=10651`) + member-confirmation (single family) |

## Evidence
- DB truth: `SELECT count(*) FROM classical_text_chunks` = 10651 (matches ledger).
- Wire CONFIRM call:
  `POST /api/mcp/primitives/read_classical_text` body `{"params":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa","query":"Saturn tenth house","limit":2}}` → `ok:true`, `tool_name:"classical_text_search"`.
- Fidelity diff on chunk `nadi_navamsa_patel_pg2234_c01`:
  DB `SELECT content_en,content_sa,content_summary,topics,source_citation,tradition_school,verse_ref,chapter FROM classical_text_chunks WHERE chunk_id='nadi_navamsa_patel_pg2234_c01'`
  → content_en=`"and (2) Saturn the lord of the 8th house is situated in the 12th\n“house."`, content_sa=null, content_summary=null, topics=[], source_citation=`"[MEDIUM] Predicting Through Navamsa and Nadi Astrology — C.S. Patel, Sagar Publications (1996); archive.org grey-upload, provenance MEDIUM | PG2234"`, tradition_school=`vedic:nadi`, verse_ref=`PG2234:C1`, chapter=2234.
  WIRE `verse_text_en`/`verse_text_sa`/`content_summary`/`topics`/`source_citation`/`tradition_school`/`verse_ref`/`chapter` = IDENTICAL. No pivot-drop, no subject-merge, no trim, no budget drop → wire_value_matches_table=TRUE.

## Findings
- **[lane 5][class 6 UNUSABLE FORM][LOW] Payload doubling.** `read_classical_text` result ships `citations[]` and `rows[]` as byte-identical arrays (`citations==rows` True, n=2/n=2) plus a `total` — every chunk is serialized twice in one response, ~doubling bytes without disclosure. Budget-proportionality defect (Charter §7.1 pt 3); not a fidelity/value error. Evidence: python diff `inner['citations']==inner['rows'] → True`.
- **[lane 5][data-plane note, not a wire defect] Mid-sentence chunk boundaries + OCR noise.** content_en begins mid-clause "and (2)…", contains OCR garble ("Sth house", smart-quote `“house`). This is DB-stored ingestion-chunking quality, faithfully reproduced on the wire — the wire is NOT trimming (R-32 does NOT apply); logged as data-plane provenance note only.
