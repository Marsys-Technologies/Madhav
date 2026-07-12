# FUSED 1b+5 shard — classical_chunks (1 family)

| family_key | channel | retrievability_verdict (1b) | fidelity_verdict (5) | derivation |
|---|---|---|---|---|
| `__table_row_count__=0` | truly-UNREACHABLE | NOT RETRIEVABLE — table is EMPTY (0 rows) and superseded by `classical_text_chunks` (10651). No surgical tool references it; nothing to serve. | N/A (no data, no wire) | path-grade(exemplar=`__table_row_count__=0`) + member-confirmation (single family) |

## Evidence
- DB truth: `SELECT count(*) FROM classical_chunks` = 0 (matches ledger). Legacy schema (id uuid, text_id uuid, chunk_index, content, embedding) — the pre-migration corpus table, deprecated in favour of `classical_text_chunks` (text_id text, verse_ref, content_en/sa).
- No tool in the surgical whitelist targets `classical_chunks`.

## Findings
- **[lane 1b][class 1 UNREACHABLE-by-nonexistence / data-plane][LOW/INFORMATIONAL] Empty superseded table.** classical_chunks holds 0 rows; its role is served entirely by classical_text_chunks. Not a live gap — flagged as a dead/deprecated table candidate for teardown so the census does not carry a phantom surface. No wire probe possible (no data, no tool).
