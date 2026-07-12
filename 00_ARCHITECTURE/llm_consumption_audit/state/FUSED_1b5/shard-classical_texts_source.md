# FUSED 1b+5 shard — classical_texts_source (1 family)

| family_key | channel | retrievability_verdict (1b) | fidelity_verdict (5) | derivation |
|---|---|---|---|---|
| `__table_row_count__=11` | truly-UNREACHABLE | NOT RETRIEVABLE — no tool serves the 11-row source/provenance catalog. Its structured fields (title, author, era, edition, translator, publisher, year, sha256, license, source_url) reach no wire surface. `read_classical_text` uses a separately-denormalized `source_citation` on the chunk, NOT a join to this table. | N/A (never on wire) | path-grade(exemplar=`__table_row_count__=11`) + member-confirmation (single family) |

## Evidence
- DB truth: `SELECT count(*) FROM classical_texts_source` = 11 (matches ledger). Only 9/11 source text_ids have any matching chunk; exemplar chunk's text_id `nadi_navamsa_patel` returns `[]` from this table — provenance is denormalized into the chunk, not looked up here.
- No surgical-whitelist tool targets classical_texts_source.

## Findings
- **[lane 1b][class 1 UNREACHABLE][LOW-MEDIUM] Source provenance catalog unreachable + partly orphaned.** 11-row bibliographic provenance table (edition, translator, publisher, year, sha256, license, source_url) has no retrieval path; 2/11 rows have no chunk linkage at all. Consumers cannot cite edition/translator/license authoritatively — only the per-chunk denormalized blurb (which for the sampled text is not even backed by a row here). Repro: no tool in whitelist targets it; `source_ids_matching_chunks=9` of 11.
