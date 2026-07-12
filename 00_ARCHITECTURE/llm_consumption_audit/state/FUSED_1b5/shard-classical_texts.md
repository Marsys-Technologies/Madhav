# FUSED 1b+5 shard — classical_texts (1 family)

| family_key | channel | retrievability_verdict (1b) | fidelity_verdict (5) | derivation |
|---|---|---|---|---|
| `__table_row_count__=16` | truly-UNREACHABLE (structured catalog); provenance blurb reachable denormalized | PARTIAL/NOT RETRIEVABLE — no tool serves the 16-row text-catalog rows; structured fields (title_en, author, school, tier, license, total_chapters, total_verses) appear on NO wire surface. Only a denormalized `source_citation` string reaches the wire via `read_classical_text`. | N/A (catalog fields never on wire) | path-grade(exemplar=`__table_row_count__=16`) + member-confirmation (single family) |

## Evidence
- DB truth: `SELECT count(*) FROM classical_texts` = 16 (matches ledger). 15/16 text_ids have matching chunks in classical_text_chunks.
- No surgical-whitelist tool enumerates or reads classical_texts rows. `read_classical_text` returns chunk rows carrying a denormalized `source_citation` string only — never the catalog's structured fields (tier, license_cleared, total_verses, school).

## Findings
- **[lane 1b][class 1 UNREACHABLE][MEDIUM] Text-catalog structured metadata unreachable.** The 16-row canon catalog (per-text tier, license clearance, school, total_verses, author) has no retrieval path; a consuming LLM cannot enumerate the corpus, filter by tier/school, or verify license clearance. Provenance survives only as a free-text blurb embedded per-chunk. Repro: no tool in whitelist targets `classical_texts`; DB has 16 rows.
