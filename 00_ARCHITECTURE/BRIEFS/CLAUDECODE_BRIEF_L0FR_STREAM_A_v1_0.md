---
artifact: CLAUDECODE_BRIEF_L0FR_STREAM_A_v1_0.md
stream: A — Foundation Infrastructure
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavL0FR-A
branch: feature/l0fr-stream-a-infrastructure
budget_cap_usd: 500
tier3_escalation_usd: 5000
authored_by: Cowork 2026-06-07
---

# Stream A — Foundation Infrastructure (Autonomous)

## §0 — Identity

Conductor for L0FR Stream A. Operating under:
- AUTONOMOUS_MODE
- AUTONOMY_RESILIENCE_PATTERN
- BUILD_GUARANTOR_SWARM_CHARTER

Master plan: `00_ARCHITECTURE/BRAHMA_L0_FOUNDATION_REBUILD_v1_2.md`
Source data: `00_ARCHITECTURE/L0FR_SOURCE_DATA_v1_0.md`
Vimarśaka spec: `00_ARCHITECTURE/L0FR_VIMARSAKA_SPECS_v1_0.md`

## §0.5 — Rebuild discipline

Per memory `feedback_rebuild_skepticism_of_existing_code`: existing retrieval, MCP, and orchestrator code is INTENT reference. Treat as such. Where clean, reuse. Where it carries audience_tier or stale concepts, **rewrite without retrofit**.

## §1 — Mission

Lay the foundation for all subsequent streams: Swiss Ephemeris shared infrastructure, schema migrations, orchestrator `--global-build` mode, retrieval registry scaffolding with all 4 adapters, MCP OAuth 2.0 for ChatGPT, audience_tier kill-list audit, first 5 L0 capabilities as pattern validation.

## §2 — Dependencies + cross-stream signal

**Dependencies:** None. This is the foundation stream.

**Signal protocol:**
- On completion, write `state.yaml`: `streams.A.status: review`, `streams.A.tag: <git_sha>`
- Vimarśaka-A polls; runs reviews; updates `state.yaml`: `gates.vimarsaka_a.status: pass` on approval
- Master Conductor (Sūtradhāra) detects pass, spawns B/C/E/F/G

## §3 — Scope (numbered steps)

### Infrastructure
1. Download `.se1` files per source data §1; sha256 manifest; upload to `gs://madhav-ephemeris/se1/`
2. Add `.se1` bundle to brahma-pipeline Dockerfile and python-sidecar Dockerfile
3. Author pyhora-sidecar Dockerfile (NEW) at `platform/python-sidecar/pyhora.Dockerfile` OR fold PyHora into existing python-sidecar — either way, `.se1` bundled
4. Smoke test: `docker run brahma-pipeline:test python -c "import swisseph as swe; swe.set_ephe_path('/app/ephe'); print(swe.calc_ut(2451545, 0))"` returns Sun position J2000

### Schema
5. Author migration `platform/supabase/migrations/081_l0fr_schema.sql`:
   - CREATE TABLE `sutravali_rules` (rule_id UUID, text_id TEXT, verse_ref TEXT, antecedent_jsonb JSONB, predicate_jsonb JSONB, prediction_jsonb JSONB, confidence NUMERIC, extracted_by TEXT, extraction_pass_log JSONB, created_at TIMESTAMPTZ)
   - CREATE TABLE `sutravali_review` (same shape + rejection_reason TEXT)
   - CREATE TABLE `chart_panchanga_cache` (chart_id UUID, date DATE, tithi TEXT, vara TEXT, nakshatra TEXT, yoga TEXT, karana TEXT, sunrise_utc TIMESTAMPTZ, sunset_utc TIMESTAMPTZ, computed_at TIMESTAMPTZ, PRIMARY KEY (chart_id, date))
   - CREATE TABLE `classical_texts_source` (text_id TEXT PK, title TEXT, author TEXT, era TEXT, edition TEXT, translator TEXT, publisher TEXT, year INT, sha256 TEXT, license TEXT, citation_format TEXT, source_url TEXT)
   - ALTER TABLE `classical_text_chunks` ADD COLUMN translator TEXT, tradition_school TEXT, embedding VECTOR(768), content_sha256 TEXT
   - ALTER TABLE `brahma_remedy_corpus` ADD COLUMN category TEXT, deity TEXT, mantra_sanskrit TEXT, mantra_transliteration TEXT, ingredients_jsonb JSONB, timing_rules_jsonb JSONB, cost_tier TEXT, contraindications TEXT, classical_attestation_text TEXT
   - CREATE TABLE `remedy_review_queue` (mirror of brahma_remedy_corpus + rejection_reason)
   - CREATE INDEX `idx_classical_text_chunks_embedding` USING hnsw (embedding vector_cosine_ops)
6. Apply migration to prod via Cloud SQL Auth Proxy
7. Update `asset_registry` rows (single transaction so cockpit sees consistent state):
   ```sql
   BEGIN;
   -- Rename + correct ephemeris asset
   UPDATE asset_registry SET
     english_name = 'Graha Sphuṭa / Ephemeris',
     target_floor = 821250,
     scope = 'global',
     expected_volume_formula = 'DATES_1900_TO_2150 * BODIES_9'
   WHERE asset_id = 'brahmagyan.kalapancanga';

   -- Deactivate panchanga_almanac (replaced by service)
   UPDATE asset_registry SET is_active = false
   WHERE asset_id = 'brahmagyan.panchanga_almanac';

   -- Mark L0 reference + ontology + texts + remedies + rules as global scope
   UPDATE asset_registry SET scope = 'global'
   WHERE layer = 'brahmagyan' AND is_active = true AND asset_id != 'brahmagyan.panchanga_almanac';

   -- Update target floors per master plan
   UPDATE asset_registry SET target_floor = 96 WHERE asset_id = 'brahmagyan.sarani';
   UPDATE asset_registry SET target_floor = 100 WHERE asset_id = 'brahmagyan.samanvaya';
   UPDATE asset_registry SET target_floor = 6000, target_table = 'classical_text_chunks' WHERE asset_id = 'brahmagyan.shastra';
   UPDATE asset_registry SET target_floor = 500 WHERE asset_id = 'brahmagyan.upaya_kosha';
   UPDATE asset_registry SET target_floor = 3000, target_table = 'sutravali_rules' WHERE asset_id = 'brahmagyan.sutravali';

   -- Add new text_index asset
   INSERT INTO asset_registry (asset_id, layer, sanskrit_name, english_name, target_table, target_floor, expected_volume_formula, count_sql, depends_on, scope, is_active)
   VALUES (
     'brahmagyan.text_index',
     'brahmagyan',
     'Vidyā Kośa',
     'Vector Index',
     'classical_text_chunks',
     6000,
     'ACTUAL(brahmagyan.shastra)',
     'SELECT count(*) FROM classical_text_chunks WHERE embedding IS NOT NULL',
     '["brahmagyan.shastra"]'::jsonb,
     'global',
     true
   ) ON CONFLICT (asset_id) DO UPDATE SET is_active = true;

   -- Inspect sensitive_point_catalog: read writer to determine if in-scope
   -- If no writer found: SET is_active = false
   -- If writer exists: SET scope = 'global', leave is_active as-is

   COMMIT;
   ```
   After commit: poll the cockpit's `/api/cockpit/registry` once and verify the response reflects all 8 active brahmagyan assets with correct metadata.

### Orchestrator
8. Modify brahma-pipeline `main.py` to accept `--global-build` flag parallel to `--run-id`
9. When `--global-build`: acquire `pg_advisory_lock(hashtext('global'))`, walk asset_registry rows where `scope='global'`, run their writers, release lock
10. Smoke test: `gcloud run jobs execute brahma-build-pipeline-job --args=--global-build,--run-id,<empty_run> --wait` completes successfully

### Audience tier kill-list
11. Grep all three repos per source data — list every residual reference
12. For each (outside SESSION_LOG / governance docs): rewrite/remove
13. Re-grep; AC: 0 residual references

### Retrieval registry
14. Author `platform/src/lib/retrieval/registry/types.ts` with full Capability descriptor per master plan §6
15. Author `platform/src/lib/retrieval/registry/index.ts` with `registerCapability`, `listCapabilities`, `getCapability(uri)`
16. Author `platform/src/lib/retrieval/registry/parity_check.ts` as CI gate (compares MCP exports to Consume Chat registry; throws on mismatch)
17. Create empty layer directories for L0-L5

### Four adapters
18. Author `platform/src/lib/retrieval/adapters/agentic_loop/` (substantive implementations):
    - `loop_engine.ts` — main orchestrator with no hard iteration cap; soft budget governor
    - `chain_of_thought.ts` — thinking block pass-through and accumulation
    - `deferred_tool_loader.ts` — LLM gets catalog, loads schemas on demand
    - `adaptive_planner.ts` — mid-loop re-planning based on intermediate results
    - `reflection.ts` — periodic "ready to synthesize?" prompts
    - `error_recovery.ts` — semantic alternatives on tool failure
    - `budget_governor.ts` — per-call cost tracking + budget header injection
19. Author `platform/src/lib/retrieval/adapters/bulk_context/`:
    - `intent_classifier.ts` — regex + Gemini Flash-Lite for query intent tagging
    - `prefetcher.ts` — for tagged intent, pre-fetch resources by priority
    - `bundler.ts` — clip + structure into system context
    - `synthesizer.ts` — single-pass Gemini call with citations
20. Author `platform/src/lib/retrieval/adapters/openai_function_calling/`:
    - `adapter.ts` — OpenAI function schema translation; parallel tool calls; structured outputs; reasoning tokens for o1
    - `oauth.ts` — OAuth 2.0 endpoints (see step 21)
21. Author `platform/src/lib/retrieval/adapters/hybrid/`:
    - `adapter.ts` — pre-fetch top-priority resources + expose remaining tools to Gemini
22. Author `platform/src/lib/retrieval/adapters/shared/`:
    - `result_clipper.ts` — clip results to result_max_kb
    - `cost_tracker.ts` — per-call cost tracking, accumulator

### MCP OAuth 2.0
23. In `platform-mcp/src/`, add OAuth endpoints per source data §4: authorize, token, refresh, discovery
24. Underlying identity: Firebase (existing); the OAuth layer is a protocol bridge
25. Update MCP server manifest to advertise OAuth-protected resources
26. Smoke test:
    - `curl -X POST http://localhost:8080/mcp/oauth/token -d "grant_type=client_credentials&client_id=test&client_secret=$MCP_TEST_SECRET"` returns access_token
    - `curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/mcp/tools/list` returns tool catalog
27. Configure a test ChatGPT desktop instance (or curl-simulate the ChatGPT MCP handshake); end-to-end roundtrip on at least one tool

### First 5 L0 capabilities (pattern validation)
28. Author `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/resolve_entity.ts`:
    - Tool URI: `marsys://tool/L0/resolve_entity`
    - args: { name: string }
    - returns: { canonical_id, entity_class, synonyms[] }
    - Handler: SELECT canonical_id, entity_class, synonyms FROM brahma_ontology WHERE $1 = ANY(SELECT jsonb_array_elements_text(synonyms_jsonb)) OR canonical_name_en=$1 OR canonical_name_sa=$1
    - llm_hints: { agentic: { cost_class: 'cheap' }, bulk_context: { pre_fetch_priority: 80 } }
    - Note: brahma_ontology table is part of asset brahmagyan.samanvaya; Stream A also seeds it with minimal ontology (9 grahas + 27 nakshatras + 12 signs at minimum) for the resolve_entity test
29. Author `marsys://tool/L0/list_entities` (class filter)
30. Author `marsys://resource/asset-registry/all` (resource loader returns asset_registry as JSON)
31. Author `marsys://resource/asset-registry/L0` (L0-only slice)
32. Author `marsys://prompt/intent-classify` (template prompt used by Bulk Context adapter)
33. All 5 registered in BOTH MCP server (platform-mcp) and Consume Chat (platform/src/lib/retrieval/) — parity_check.ts passes
34. End-to-end test: query each capability via both clients; results match

## §4 — Capability registrations summary

5 capabilities registered as pattern validation. Full Stream A capability table per master plan §8 Stream A row.

## §5 — Acceptance criteria

Per Vimarśaka-A checks (see `L0FR_VIMARSAKA_SPECS_v1_0.md`). 15 programmatic checks; all 15 must PASS for APPROVE.

## §6 — Budget

- Tier-3 cap: $500
- Per-call cost tracking via shared adapter cost_tracker (authored in this stream)
- If $400 burn-rate observed and progress <80%, log to Smṛti and consider scope reduction

## §7 — Pre-Vimarśaka readiness checklist

Before signaling READY:
- All 34 numbered steps complete OR explicitly documented as deferred with reason
- Local smoke tests all pass
- Commits pushed to feature/l0fr-stream-a-infrastructure
- `state.yaml` updated: streams.A.status = 'review', streams.A.tag = `<HEAD sha>`
- Final summary block emitted to `00_ARCHITECTURE/CONDUCTOR/l0fr/smriti/stream_A_final.md`

## §8 — Final summary output

```yaml
---FINAL_SUMMARY---
stream: A
status: READY_FOR_REVIEW | TIER3_ESCALATION
commits: [<sha>, ...]
scope_steps_complete: <N> / 34
deferred_items: [...]
audience_tier_residual_count: <N>
migration_081_applied: true|false
adapters_compile: 4/4 | <N>/4
five_capabilities_registered: 5/5 | <N>/5
oauth_smoke_test: pass|fail
parity_check_status: pass|fail
budget_spent_usd: <N>
notes_for_vimarsaka_a: >
  <one paragraph>
---END_FINAL_SUMMARY---
```
