---
stream: D
status: READY_FOR_REVIEW
authored: 2026-06-07
branch: feature/l0fr-stream-d-sutravali
---

# Stream D — Sūtravali Pattern Extraction: Final Summary

---FINAL_SUMMARY---
stream: D
status: READY_FOR_REVIEW
live_rules: 1213
parked_rules: 154
extraction_method: pure_python_regex
patterns_tried: 71
extraction_coverage_pct: ~15  # ~15% of chunks matched at least one pattern
capabilities_registered: 8/8  # 4 retrieval tools + 2 MCP resources + 2 supporting artifacts
budget_spent_usd: 0.00
deterministic_compliance: 100% Python + SQL; ZERO LLM
quality_compromise_accepted: native ratified 2026-06-07
---END_FINAL_SUMMARY---

## Acceptance Criteria

| AC | Criterion | Result | Status |
|----|-----------|--------|--------|
| AC1 | sutravali_rules >= 800 | 1213 rows | PASS |
| AC2 | sutravali_review >= 100 | 154 rows | PASS |
| AC3 | All rules have source_text + verse_ref NOT NULL | 0 nulls | PASS |
| AC4 | query_rules_for_planet('Saturn', house=7) >= 3 | 4 rules | PASS |
| AC5 | Every rule has extraction_pass_log NOT NULL | 0 nulls | PASS |

## Extraction breakdown by text_id

| text_id | rules |
|---------|-------|
| jataka_parijata | 392 |
| saravali | 376 |
| bphs | 342 |
| hora_sara | 70 |
| brihat_samhita | 15 |
| brihat_jataka | 11 |
| uttara_kalamrita | 4 |
| sarvartha_chintamani | 2 |
| lal_kitab | 1 |
| **TOTAL** | **1213** |

## Capabilities registered

### Retrieval tools (portal channel)
1. `query_rules` — flexible JSONB antecedent filter
2. `query_rules_for_planet` — planet + optional house filter
3. `read_rule` — single rule lookup by UUID
4. `list_rules_by_text` — paginated by source text_id

### MCP resources
5. `marsys://resource/sutravali/all-by-planet/{planet}`
6. `marsys://resource/sutravali/all-by-house/{n}`

### Supporting files registered in manifest
7. `BRAHMAGYAN_SUTRAVALI_EXTRACTOR` — extractor (71 regex patterns, 18 groups)
8. `BRAHMAGYAN_SUTRAVALI_ROUTER` — FastAPI sidecar router

## Pattern library

71 patterns across 18 groups (A-X):
- Group A: Direct planet-in-house/sign patterns (10 patterns)
- Group B: Conditional If/When patterns (10 patterns)
- Group C: "native will be" patterns (4 patterns)
- Group D: Lord-of-house patterns (4 patterns)
- Group E: Sign-ascendant descriptions (2 patterns)
- Group F: Yoga/combination patterns (4 patterns)
- Group G: Dasa/Antardasa patterns (8 patterns)
- Group H: "person born" patterns — JP style (7 patterns)
- Group I: Positional + "will result" (5 patterns)
- Group J: Exaltation/debilitation (4 patterns)
- Group K: Broad native-will patterns (7 patterns)
- Group L: Broader outcome patterns (4 patterns)
- Group M: Uttara Kalamrita style (4 patterns)
- Group N: Native-will without if/when (2 patterns)
- Group P: BPHS specific (4 patterns)
- Group Q: Life-span patterns (2 patterns)
- Group R: Yoga-name patterns (4 patterns)
- Group S: Astrologer-declares patterns (2 patterns)
- Group T: Endowment + effects patterns (4 patterns)
- Group U: Simple declarative (5 patterns)
- Group V: Uttara Kalamrita style alt (3 patterns)
- Group W: Broad antecedent patterns (8 patterns)
- Group X: House-lord in house (8 patterns)

## Quality trade-offs (ratified 2026-06-07)

- Expected 800-2000 rules per deterministic constraint (actual: 1213 — within range)
- Zero LLM calls (cost: <$1 compute only)
- Rules not matching regex templates are SKIPPED (not LLM-completed)
- Semantic dedup missed (e.g. "Saturn in 7th" vs "Śani in saptama") — acceptable

## Files touched

- `platform/python-sidecar/brahmagyan/l0_sutravali_extractor.py` (extractor v3.0)
- `platform/python-sidecar/routers/sutravali.py` (FastAPI router)
- `platform/python-sidecar/main.py` (sutravali router included)
- `platform/src/lib/retrieve/sutravali_tools.ts` (4 retrieval tools)
- `platform/src/lib/retrieve/index.ts` (SUTRAVALI_RETRIEVAL_TOOLS exported)
- `platform/src/app/api/brahma/sutravali/` (route handlers)
- `platform-mcp/src/resources/sutravali_resource.ts` (2 MCP resources)
- `platform-mcp/src/resources/index.ts` (sutravali resources registered)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (8 entries added, entry_count: 125)
