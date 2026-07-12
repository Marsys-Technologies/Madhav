# FUSED 1b+5 shard — brahma_formula_constants (1 family)

DB truth: `SELECT count(*) FROM brahma_formula_constants` = 18 rows.
NO tool serves this table — surgical OR full-pipeline. Check:
 `grep -rn brahma_formula_constants platform/src/lib/retrieval platform/src/lib/retrieve` → 0 hits.
All references are build-side writers only (bg_formula_constants.py builds it; downstream writers
consume constants internally at compute time). No retrieval tool, no MCP surface, no ask_madhav path
exposes it. A consuming LLM cannot obtain these 18 constants by any tool. → truly-UNREACHABLE.

| family_key | channel | retrievability | fidelity | derivation |
|---|---|---|---|---|
| __table_row_count__=18 | truly-UNREACHABLE | UNREACHABLE (no retrieval tool references the table anywhere; build-side only) | N/A | path-grade(exemplar=__table_row_count__=18) sole family; grep-verified no-tool check |
