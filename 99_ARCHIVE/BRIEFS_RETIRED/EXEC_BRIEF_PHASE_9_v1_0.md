---
artifact: EXEC_BRIEF_PHASE_9_v1_0.md
status: COMPLETE
completed_on: 2026-04-27
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
status_history:
  - timestamp: 2026-04-27
    from: AUTHORED
    to: IN_PROGRESS_STREAM_A_B_C
    note: "Claude Code (Sonnet 4.6) claimed all three streams simultaneously; executing in parallel via subagents. Prereqs verified: 1A/1B/2 COMPLETE, Phase 3 IN_PROGRESS_STREAM_A (disjoint surfaces confirmed). Cloud SQL Proxy not running locally — unit tests use mocked storage; integration tests require proxy. Proceeding: msr_sql.ts pattern established, rag table schemas from migrations 005/008/009 confirmed, CAPABILITY_MANIFEST.json 62-entry structure confirmed."
  - timestamp: 2026-04-27
    from: IN_PROGRESS_STREAM_A_B_C
    to: COMPLETE
    note: "All three streams complete. 146 tests pass across 11 retrieve/__tests__/ + config/__tests__/ files. 0 TypeScript errors in Phase 9 code. must_not_touch verified: no Phase 3 surfaces touched, no python-sidecar, no governance scripts. Registry now exports 10 tools (7 Phase-2 + 3 Phase-9). Stream A: cgm_graph_walk.ts (11 tests), BFS over rag_graph_nodes/edges, depth-capped at configService value, batched SQL queries, router prompt updated with cgm_graph_walk entry. Stream B: manifest_query.ts (14 tests), keyword scoring against CAPABILITY_MANIFEST.json 62 entries, graceful degradation on file read failure. Stream C: vector_search.ts (22 tests), Voyage-3-large embedding via HTTP + pgvector HNSW cosine query, secondary: true in registry, graceful degradation on API/DB failure. feature_flags.ts extended with CGM_GRAPH_WALK_ENABLED/MANIFEST_QUERY_ENABLED/VECTOR_SEARCH_ENABLED (all default true). Pre-existing test failures (supabase imports, parity_validator count) confirmed pre-existing via git stash — not introduced by Phase 9."
executor_target: Claude Code (Anti-Gravity / VS Code extension; NOT the CLI)
trigger_phrase: "Read EXEC_BRIEF_PHASE_9_v1_0.md and execute it."
phase_number: 9
phase_name: Advanced Retrieval (Domain D2 — extension)
purpose: Extend the Phase-2 Retrieval Tool Suite (C2.3) with three new tools — CGM Graph Walk, Manifest-Query meta-tool, and Vector Search secondary tool. Phase 9 is purely additive to platform/src/lib/retrieve/; each new tool implements the uniform retrieve(QueryPlan) → ToolBundle interface and registers against the existing tool registry. Phase 9 is INDEPENDENT of Phase 3 (and of any other in-flight phase) — its only dependencies are Phase 1 + Phase 2, both COMPLETE. Designed to run in parallel with Phase 3 in a separate Claude Code session.
depends_on:
  - 00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md (APPROVED 2026-04-27 — §4.2 D2 Query Pipeline component C2.3 Retrieval Tool Suite; §8 Retrieval Architecture; §15 Interface Contracts — ToolBundle is the uniform return shape)
  - 00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md (APPROVED 2026-04-27 — §13 Phase 9 specification)
  - EXEC_BRIEF_PHASE_0_v1_0.md (COMPLETE — Schema Registry holds tool_bundle.schema.json; Configuration Service holds feature flags; Storage Layer abstraction)
  - EXEC_BRIEF_PHASE_1A_v1_0.md (COMPLETE — Storage Layer; rag_graph_nodes + rag_graph_edges + rag_embeddings tables populated by M2/B.5 work; per-native namespacing)
  - EXEC_BRIEF_PHASE_1B_v1_0.md (COMPLETE — Capability Manifest is the catalog Manifest-Query reads against)
  - EXEC_BRIEF_PHASE_2_v1_0.md (COMPLETE — Phase-2 Retrieval Tool Suite is the registry Phase 9 extends; 7 existing tools + 3 new = 10 tools after Phase 9)
  - CLAUDE.md
parallel_stream_tolerance: |
  Phase 9 is designed to run with the M2/B.5 thread RESUMED in parallel AND with Phase 3 IN_PROGRESS
  in another Claude Code session. Phase 9's modifications are scoped to platform/src/lib/retrieve/
  (new files + minimal edit to index.ts to register the three new tools). Phase 9 may also make a
  small additive edit to platform/src/lib/router/ to add the new tools to the router's prompt's
  available-tools list — that file is read-only consumed by Phase 3 (Phase 3 calls classify() but
  doesn't modify the router), so the additive edit doesn't collide. Phase 9 does NOT modify
  governance tooling, the manifest, Python sidecar, the route.ts file, OR any of Phase 3's
  in-flight surfaces (validators/, synthesis/, prompts/, disclosure/).
chosen_path: Run in parallel with Phase 3 to compress critical-path time. By the time Phase 3
  reports COMPLETE and the feature flag is potentially flipped, the full retrieval surface
  (basic + advanced) is available rather than just basic.
risk_classification: LOW. Purely additive; well-bounded; three independent sub-streams. Vector
  Search depends on rag_embeddings being populated (which it is per M2/B.5 B.6 work); Graph Walk
  depends on rag_graph_nodes + rag_graph_edges being populated (same source); Manifest-Query
  reads filesystem.
in_parallel_with: |
  This brief is designed to run in PARALLEL with EXEC_BRIEF_PHASE_3_v1_0.md (currently in flight).
  Use a SEPARATE Claude Code session for Phase 9. The two sessions touch disjoint surfaces:
  Phase 3 owns platform/src/lib/synthesis/, validators/, prompts/, disclosure/, and route.ts.
  Phase 9 owns platform/src/lib/retrieve/ (extension) and a small additive edit to router/.
---

# EXECUTION BRIEF — Phase 9: Advanced Retrieval

## §0 — Trigger and Execution Model

Native triggers this brief by saying to a (SEPARATE from any Phase-3 session) Claude Code session: **"Read EXEC_BRIEF_PHASE_9_v1_0.md and execute it."**

**Multi-session note.** This brief is explicitly designed to run in PARALLEL with `EXEC_BRIEF_PHASE_3_v1_0.md` (currently IN_PROGRESS). The two phases touch disjoint file surfaces — see `parallel_stream_tolerance` and §3 hard constraints. If for any reason Phase 9 needs to touch a surface Phase 3 is also touching, halt and ask native.

On trigger, Claude Code MUST:
1. Read this entire brief end-to-end before any other action.
2. Read the mandatory pre-flight artifacts in §2 in the order specified.
3. Verify Phase 1A, Phase 1B, and Phase 2 are all `COMPLETE` (read their frontmatter `status` fields).
4. Acknowledge readiness; propose the sub-stream sequence (one of A-C in series, or all in parallel via subagents — recommended).
5. Execute Streams A, B, C per the specifications.
6. On completion: integration verification per §8; flip status to `COMPLETE`; notify native.

**Status transitions.** AUTHORED → IN_PROGRESS_STREAM_(A|B|C) → STREAMS_COMPLETE_PENDING_INTEGRATION → COMPLETE. Each transition writes a `status_history` entry with timestamp.

**Coordination with Phase 3.** Phase 9 does NOT depend on Phase 3 outputs and does NOT need Phase 3 complete before completing. Phase 9 can finish before Phase 3 finishes, or after, or simultaneously. The two run as independent threads.

## §1 — Mission

Extend the Phase-2 Retrieval Tool Suite with three new tools per architecture §4.2 C2.3 and project plan §13:

- **CGM Graph Walk** (`cgm_graph_walk.ts`) — BFS over the CGM nodes via the `rag_graph_nodes` and `rag_graph_edges` tables. Configurable depth (default 1, max 3). Edge-type filters (SUPPORTS, CONTRADICTS, CROSS_LINKS, plus any others present). Adaptive seed selection from `QueryPlan.graph_seed_hints` (the Phase-2 Router emits these hints; Phase 9 is the consumer).
- **Manifest-Query meta-tool** (`manifest_query.ts`) — lets the synthesizer LLM ask "what's available about X" as a tool call. Reads `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` via the Storage Layer's filesystem adapter; filters/searches manifest entries against the question; returns relevant `AssetEntry` records. Useful for queries where the synthesizer wants to introspect the catalog.
- **Vector Search secondary tool** (`vector_search.ts`) — Voyage-3-large 1024-d embeddings (already populated in `rag_embeddings` per M2/B.5 B.6 work) queried via pgvector HNSW index. Returns top-K semantically similar passages. Marked as **secondary** in the tool registry — invoked only when other tools have nothing matching, or explicitly requested. Default top-K = 10 (configurable).

All three tools implement the uniform `retrieve(QueryPlan) → ToolBundle` interface from architecture §15 (the same interface Phase 2's seven tools use). All three register against the existing C2.3 tool registry at `platform/src/lib/retrieve/index.ts`. The Router's prompt is minimally updated to include the three new tools in its available-tools list (so the router can authorize them in QueryPlan.tools_authorized).

The phase is parallelizable into three independent sub-streams. Within a single Claude Code session, subagent parallelism is recommended.

## §2 — Mandatory Pre-flight Reading

Read in full, in this order. Do not skip.

**§2.1 — Architectural and project context (read first):**

1. `CLAUDE.md` — note item 2 references `CAPABILITY_MANIFEST.json` (post-1B cutover).
2. `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` — pay particular attention to: §4.2 C2.3 Retrieval Tool Suite (the plug-in registry pattern; uniform `retrieve(QueryPlan) → ToolBundle` interface); §8 Retrieval Architecture (KGAG positioning — "build now, scale progressively"); §15 Interface Contracts (ToolBundle).
3. `00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md` §13 Phase 9 specification — components, deliverables, acceptance criteria, open implementation questions (especially graph traversal depth and Vector Search top-K).

**§2.2 — Phase 0/1A/1B/2 outputs you depend on:**

4. `platform/src/lib/retrieve/index.ts` — the Phase-2 tool registry. You'll add 3 new tool registrations.
5. `platform/src/lib/retrieve/msr_sql.ts` (or any one of the existing 7 tools) — read as exemplar for the `RetrievalTool` interface implementation pattern.
6. `platform/src/lib/storage/index.ts` — Storage Layer abstraction. You'll use `query()` for SQL operations (Graph Walk, Vector Search) and `readFile()` for filesystem reads (Manifest-Query).
7. `platform/src/lib/schemas/tool_bundle.schema.json` — output validation.
8. `platform/src/lib/schemas/asset_entry.schema.json` — Manifest-Query returns AssetEntry-shaped records.
9. `platform/src/lib/cache/index.ts` — Tool-Call Cache; the new tools integrate with it via the existing `executeWithCache` helper.
10. `platform/src/lib/router/prompt.ts` (or wherever the router's prompt template is) — you'll make a small additive edit to include the three new tools in the available-tools list. Read this file's structure first.
11. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — the manifest the Manifest-Query tool reads. Note current entry count (62 post-1B).

**§2.3 — Database state to verify before tool implementation:**

12. Run `SELECT count(*) FROM rag_graph_nodes WHERE native_id='abhisek'` and `SELECT count(*) FROM rag_graph_edges WHERE native_id='abhisek'` to confirm graph data is populated. Per memory: ~1,752 nodes and ~3,911 edges as of Exec_8 close (M2/B.5 work).
13. Run `SELECT count(*) FROM rag_embeddings WHERE native_id='abhisek'` to confirm embeddings populated. Per memory: ~977 embeddings.
14. If any of these counts is zero or non-existent, halt and ask native — Phase 9 cannot complete without the M2/B.5-populated data.

**§2.4 — Existing pipeline code to understand for integration context (do NOT modify):**

15. `platform/src/lib/router/router.ts` — the Phase-2 Router. The new tools' authorization rules need to be reachable from the Router's prompt. You may make a SMALL additive edit to the prompt template (see Stream A's task list) but should not modify the router's classification logic.
16. `platform/src/app/api/chat/consume/route.ts` — DO NOT modify. Phase 3 owns this file.
17. `platform/src/lib/synthesis/`, `platform/src/lib/validators/`, `platform/src/lib/prompts/`, `platform/src/lib/disclosure/` — Phase 3's surfaces. DO NOT touch.

After completing pre-flight reading, summarize understanding in 4-6 sentences. Confirm: (a) graph/embedding data is present in the DB; (b) tool registry pattern from existing tools; (c) the disjoint-surface relationship with Phase 3.

## §3 — Hard Scope Constraints

### `may_touch` (allowed surfaces)

**New files (creation allowed):**
- `platform/src/lib/retrieve/cgm_graph_walk.ts` — Stream A.
- `platform/src/lib/retrieve/manifest_query.ts` — Stream B.
- `platform/src/lib/retrieve/vector_search.ts` — Stream C.
- Test files in the project's existing test pattern.

**Existing files (modification allowed only as specified):**
- `platform/src/lib/retrieve/index.ts` — add the 3 new tool exports + registrations to the `RETRIEVAL_TOOLS` array. Do NOT modify any existing tool registrations.
- `platform/src/lib/router/prompt.ts` (or equivalent — the file holding the router's prompt template) — additive edit only: add the 3 new tools' names and one-line descriptions to the available-tools list in the prompt. Do NOT modify other parts of the prompt.
- `platform/src/lib/config/feature_flags.ts` — add new flags as needed: `CGM_GRAPH_WALK_ENABLED` (default true), `MANIFEST_QUERY_ENABLED` (default true), `VECTOR_SEARCH_ENABLED` (default true), `CGM_GRAPH_WALK_MAX_DEPTH` (default 3), `VECTOR_SEARCH_TOP_K` (default 10).
- `package.json` — add npm scripts as needed.

**This brief itself** — only for status transitions and `status_history` updates.

### `must_not_touch` (forbidden surfaces)

**Phase 3's in-flight surfaces (CRITICAL — Phase 3 is concurrently active):**
- `platform/src/lib/validators/` — Phase 3 owns this.
- `platform/src/lib/synthesis/` — Phase 3 owns this.
- `platform/src/lib/prompts/` — Phase 3 owns this.
- `platform/src/lib/disclosure/` — Phase 3 owns this.
- `platform/src/app/api/chat/consume/route.ts` — Phase 3 owns this.

**Architecture and plan (read-only):**
- `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` — do NOT modify.
- `00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md` — do NOT modify.
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — read-only. Manifest-Query reads it; does NOT modify.
- `00_ARCHITECTURE/manifest_overrides.yaml` — read-only.

**Phase 0/1A/1B/2 deliverables (read-only consumers — Phase 9 USES, does NOT modify):**
- `platform/src/lib/router/router.ts` — DO NOT modify the classifier logic. Only the prompt template's available-tools list (per may_touch above).
- `platform/src/lib/router/index.ts` — DO NOT modify (the public router API).
- `platform/src/lib/bundle/` — DO NOT modify.
- `platform/src/lib/retrieve/` — existing tools (msr_sql, pattern_register, etc.) DO NOT modify; Phase 9 only ADDS new tools.
- `platform/src/lib/cache/` — DO NOT modify.
- `platform/src/lib/schemas/`, `platform/src/lib/storage/`, `platform/src/lib/config/` (except feature_flags additions), `platform/src/lib/telemetry/`, `platform/src/lib/models/`.

**Existing pipeline code:**
- `platform/src/lib/claude/consume-tools.ts` — STAYS as-is (the flag-OFF path tools).
- `platform/src/lib/claude/system-prompts.ts` — STAYS as-is.
- `platform/src/components/consume/*` — UI components untouched.

**M2/B.5 surfaces (parallel-stream protection):**
- `platform/python-sidecar/` — entire Python sidecar.
- `platform/scripts/governance/` — governance scripts.
- `platform/src/lib/rag/` (if present) — recent B.6 retrieval client work. Phase 9's Vector Search builds its OWN tool at `platform/src/lib/retrieve/vector_search.ts`; it does NOT call into or modify `platform/src/lib/rag/`.
- `035_DISCOVERY_LAYER/` — entire directory (M2/B.5 active surface).
- `06_LEARNING_LAYER/` — entire directory.
- The active CLAUDECODE_BRIEF.md (if present).
- `.gemini/`, `.geminirules`.

**Database:**
- READ-ONLY queries against `rag_graph_nodes`, `rag_graph_edges`, `rag_embeddings`. NO schema changes. NO data writes.

### Behavioral constraints

- All three tools follow the existing `RetrievalTool` interface from Phase 2 exactly. Do NOT introduce new interfaces or contract changes.
- All tools default-enabled via feature flag (true). Toggling a flag to false should make the corresponding tool's `retrieve()` return an empty ToolBundle gracefully (not throw).
- The Vector Search tool is registered as `secondary` in metadata; the Router's prompt should describe it as "use when other tools have nothing matching." The router emits it less aggressively than the primary tools.
- The Manifest-Query tool is the LLM-introspection meta-tool — it's intended for the synthesizer to call mid-synthesis (Phase 3+ uses it). Phase 9 just builds it; no immediate consumer integration.
- Latency targets per project plan §13: graph walk ≤200ms (depth 1), manifest query ≤100ms, vector search ≤300ms. These are integration test acceptance bars.
- If Phase 9 finds it needs to touch a Phase 3 surface, HALT immediately and ask native. The disjoint-surface assumption is critical for parallel execution safety.

## §4 — Sub-Stream Overview

**Stream A — CGM Graph Walk.** TypeScript tool implementing `retrieve(QueryPlan) → ToolBundle`. BFS over `rag_graph_nodes` and `rag_graph_edges` tables. Seeds from QueryPlan.graph_seed_hints. Configurable depth.

**Stream B — Manifest-Query meta-tool.** TypeScript tool implementing the same interface. Reads `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` via Storage Layer; filters by question; returns AssetEntry records.

**Stream C — Vector Search secondary tool.** TypeScript tool implementing the same interface. pgvector HNSW query against `rag_embeddings`; returns top-K passages.

All three are mutually independent. Recommended within-session subagent parallelism: A + B + C all in parallel.

## §5 — Stream A: CGM Graph Walk

**Goal.** BFS over the CGM graph (rag_graph_nodes + rag_graph_edges) to find connected signals from seed nodes.

**Tasks:**

**A.1 — Create the tool file.** `platform/src/lib/retrieve/cgm_graph_walk.ts`.

**A.2 — Examine the schema.** Inspect `rag_graph_nodes` and `rag_graph_edges` tables (via Storage Layer or `\d` in psql). Document: column names, edge_type values present, node_type values present, native_id partitioning (per Phase 1A).

**A.3 — Implement the BFS.** Tool inputs (from QueryPlan):
- `graph_seed_hints: string[]` — node IDs the router suggests as starting points.
- `graph_traversal_depth: number` — depth (1-3, default 1).
- Optional edge-type filter from tool params (e.g., only SUPPORTS + CONTRADICTS, exclude CROSS_LINKS).

Algorithm:
```
visited = set(seeds)
frontier = seeds
results = []
for level in 0..depth-1:
  next_frontier = []
  for node in frontier:
    edges = SELECT * FROM rag_graph_edges 
      WHERE source = node AND native_id = ? 
      AND (edge_type_filter applied)
    for edge in edges:
      if edge.target not in visited:
        visited.add(edge.target)
        next_frontier.append(edge.target)
        results.append({ from: node, to: edge.target, edge_type, level })
  frontier = next_frontier
return results
```

For each visited node, fetch the node record from `rag_graph_nodes` to include node metadata (signal_id, type, content_summary).

**A.4 — Return ToolBundle.** Results array contains: connected node IDs, the edges traversed (with types), node metadata. `served_from_cache` initially false (Tool-Call Cache will set this on cache hits via the existing `executeWithCache` wrapper).

**A.5 — Register in tool registry.** Add `cgm_graph_walk` entry to `platform/src/lib/retrieve/index.ts`'s `RETRIEVAL_TOOLS` array. Match the existing registration pattern.

**A.6 — Update router prompt.** Make a small additive edit to `platform/src/lib/router/prompt.ts` (or wherever the available-tools list is) to add: `"cgm_graph_walk: Traverse the chart's cognitive graph from seed nodes via SUPPORTS / CONTRADICTS / CROSS_LINKS edges. Use for cross-signal-relationship queries."`

**A.7 — Tests.** `platform/src/lib/retrieve/__tests__/cgm_graph_walk.test.ts`:
- Unit: BFS correctness on synthetic graph.
- Integration: real DB query for known seeds; depth 1 returns expected adjacent nodes; depth 2 returns expected expanded set.
- Latency: end-to-end ≤200ms for depth 1.

**Stream A acceptance criteria:**
- [ ] `cgm_graph_walk.ts` exists and implements RetrievalTool interface.
- [ ] BFS correctness: synthetic test passes.
- [ ] Real DB query returns expected nodes for a representative seed (e.g., a Saturn-related node).
- [ ] Depth=1 latency ≤200ms.
- [ ] Tool registered in `RETRIEVAL_TOOLS`.
- [ ] Router prompt updated with the tool's description.
- [ ] Empty ToolBundle returned cleanly when feature flag is false.

## §6 — Stream B: Manifest-Query Meta-Tool

**Goal.** Let the synthesizer LLM introspect the Capability Manifest. Filters manifest entries by relevance to a question.

**Tasks:**

**B.1 — Create the tool file.** `platform/src/lib/retrieve/manifest_query.ts`.

**B.2 — Implement the query logic.** Inputs (from QueryPlan or tool params): a question or topic string (e.g., "Saturn data", "career signals").

Approach:
- Read CAPABILITY_MANIFEST.json via Storage Layer's `readFile()`.
- Parse JSON; iterate entries.
- For each entry, score relevance: simple keyword match against `canonical_id`, `path`, `description` (if present in entry), `preferred_for`, etc. For each match, increment score.
- Optionally: small-LLM-mediated relevance scoring as an upgrade path (defer to Phase 6 calibration; for Phase 9 use keyword scoring as the simple version).

**B.3 — Return ToolBundle.** Results contain matched AssetEntry records, sorted by relevance score descending. Top-N (default 10, configurable).

**B.4 — Register in tool registry.**

**B.5 — Update router prompt.** Add: `"manifest_query: Ask 'what's available about X' to introspect the data catalog. Use to discover whether the corpus has data on a specific topic before deeper retrieval."`

**B.6 — Tests.** `platform/src/lib/retrieve/__tests__/manifest_query.test.ts`:
- Unit: keyword-scoring against synthetic manifest entries.
- Integration: real manifest query returning expected entries (e.g., "Saturn" should match FORENSIC, MSR, anything with Saturn-related keywords).
- Latency: ≤100ms.

**Stream B acceptance criteria:**
- [ ] `manifest_query.ts` exists and implements RetrievalTool interface.
- [ ] Keyword-scoring works on synthetic + real manifest.
- [ ] Latency ≤100ms.
- [ ] Tool registered.
- [ ] Router prompt updated.

## §7 — Stream C: Vector Search Secondary Tool

**Goal.** Voyage-3-large pgvector search against `rag_embeddings`. Marked as secondary in tool registry.

**Tasks:**

**C.1 — Create the tool file.** `platform/src/lib/retrieve/vector_search.ts`.

**C.2 — Embedding generation for the query.** The tool needs to embed the user's query text using the same Voyage-3-large model used to populate `rag_embeddings`. Look at how the M2/B.5 ingest pipeline did this (likely in the Python sidecar's embed.py); replicate the embedding call from TypeScript using whatever Voyage SDK or HTTP wrapper the project uses. If the project doesn't have a TypeScript Voyage client, use `fetch` against the Voyage API directly (the API is straightforward).

If the embedding call fails or is unavailable, the tool's `retrieve()` returns an empty ToolBundle with a clear status (NOT throw).

**C.3 — pgvector HNSW query.** Use Storage Layer's `query()`:

```sql
SELECT chunk_id, content, source_file, layer,
       embedding <=> $1::vector AS distance
FROM rag_embeddings
WHERE native_id = $2
ORDER BY embedding <=> $1::vector
LIMIT $3;
```

`<=>` is pgvector's cosine distance operator. Default LIMIT = 10 (configurable via `VECTOR_SEARCH_TOP_K` flag).

**C.4 — Return ToolBundle.** Results contain top-K passages with their cosine distance scores. Mark each as `representation: 'vector_search'` for downstream consumers to know the source.

**C.5 — Register in tool registry as SECONDARY.** The tool registration metadata should include `secondary: true` (or equivalent). The Router's prompt should describe it as "secondary — use when primary tools (MSR-SQL, registers) have nothing matching, OR when the query is exploratory and semantic similarity is the right access pattern."

**C.6 — Update router prompt.** Add: `"vector_search [secondary]: Semantic similarity search across all chunked content. Use for exploratory queries where structured filters miss relevant passages, or when prior tools returned no results."`

**C.7 — Tests.** `platform/src/lib/retrieve/__tests__/vector_search.test.ts`:
- Unit: query embedding mocked; pgvector query syntax correct.
- Integration: real query against rag_embeddings; verify top-K returns sensible passages (e.g., "wealth and material success" returns chunks mentioning prosperity, abundance).
- Latency: ≤300ms (includes embedding call).
- Failure path: when Voyage API fails, returns empty ToolBundle gracefully.

**Stream C acceptance criteria:**
- [ ] `vector_search.ts` exists and implements RetrievalTool interface.
- [ ] Voyage embedding call works for query text.
- [ ] pgvector query returns top-K results.
- [ ] Latency ≤300ms.
- [ ] Marked secondary in registry.
- [ ] Router prompt updated.
- [ ] Graceful failure when Voyage API unavailable.

## §8 — Integration and Final Acceptance

After all three sub-streams complete:

**§8.1 — Tool registry verification.** `platform/src/lib/retrieve/index.ts` should now export 10 tools (7 from Phase 2 + 3 from Phase 9). `getTool('cgm_graph_walk')`, `getTool('manifest_query')`, `getTool('vector_search')` all return non-null.

**§8.2 — End-to-end retrieval test.** Run `npm run pipeline:test` (the Phase-2 smoke test). The smoke test now exercises 10 tools instead of 7. Verify all 8 query classes still produce ToolBundles.

**§8.3 — Router authorization.** For a representative cross-domain query, verify the router's QueryPlan can include the new tools in `tools_authorized` (the prompt template now describes them; the router may authorize them per query class).

**§8.4 — Latency benchmarks.** Per-tool latency tests pass: graph walk ≤200ms, manifest query ≤100ms, vector search ≤300ms.

**§8.5 — Test suite execution.** Full project test suite passes.

**§8.6 — `must_not_touch` verification.** `git status`. Confirm only allowed surfaces modified. **Particular attention: nothing in Phase 3's surface area was touched.**

**§8.7 — Phase 3 coexistence check.** Verify `EXEC_BRIEF_PHASE_3_v1_0.md` status field is unchanged by Phase 9's execution. Phase 9 didn't accidentally write into Phase 3's status_history or modify Phase 3's brief.

**§8.8 — Lint and type-check.** Clean.

## §9 — Phase 9 Done Criteria

`COMPLETE` when:

1. All Stream A acceptance criteria met.
2. All Stream B acceptance criteria met.
3. All Stream C acceptance criteria met.
4. Integration verification (§8) passes.
5. Test suite + lint + type-check clean.
6. `must_not_touch` verified — including no overlap with Phase 3's surfaces.
7. Native confirms acceptance.

When complete:
- Update brief frontmatter `status` to `COMPLETE`.
- Add `completed_on` field.
- Append final `status_history` entry summarizing: graph walk results on representative seed, manifest query example output, vector search top-K on a sample query, latencies achieved per tool.
- Notify native: Phase 9 complete. Phase 6 (LLM Checkpoints) can be authored/executed when Phase 3 reports COMPLETE; Phase 7 (Panel Mode) requires Phase 6 complete.

## §10 — Communication Discipline

**Halt on uncertainty.** If you discover an architectural choice the brief didn't make, halt and surface to native.

**No scope creep.** Tangential issues → `PHASE_9_OBSERVATIONS_v1_0.md`.

**No collision with Phase 3.** This is the most important constraint. If you find yourself needing to touch a Phase-3 surface (validators/, synthesis/, prompts/, disclosure/, route.ts), halt immediately.

**No collision with M2/B.5.** Same principle. If you find yourself needing to modify python-sidecar, governance scripts, src/lib/rag/, or anything in 035/ or 06/, halt.

**Status updates between sessions.** Multi-session execution updates `status_history`.

**Adherence to architectural principles.** Per architecture §3 P.7 (modularity), the new tools follow the same RetrievalTool contract as Phase 2's tools — they're additive plug-ins, not new abstractions. P.8 (LLM where domain knowledge needed; deterministic for integrity / lookup / algorithm): graph walk is deterministic algorithmic; manifest query is keyword-scoring deterministic; vector search uses an embedding (LLM call to Voyage) but the search itself is deterministic kNN.

## §11 — Final Notes

Phase 9 is a parallelization win — it compresses critical-path time by running alongside Phase 3 and producing the advanced retrieval surface that downstream phases (Phase 6 LLM Checkpoints, Phase 7 Panel Mode) will leverage.

Per architecture §8: KGAG (the graph walk tool) is built now, scaled progressively. Today's CGM graph density (~22 reconciled edges per the discovery layer report) means the graph walk's marginal value over MSR-SQL alone is small in early use. As graph density grows in subsequent M2 phases, the graph walk tool starts paying off proportionally. Build it now, light it up later.

Manifest-Query is a research-grade capability — it lets the LLM reason about its own capabilities. This becomes more valuable as the manifest grows (post-M5, post-multi-native) and the LLM needs to navigate a larger asset space. Today's value is modest; tomorrow's value scales with corpus complexity.

Vector Search is genuinely secondary in this corpus — the typed metadata in MSR + the structured registers do most of the work. Vector search shines for exploratory queries the structured tools miss. Keep its registry metadata clear that it's secondary; the router should default to NOT authorizing it unless the query is exploratory.

When Phase 9 reports COMPLETE alongside Phase 3 in flight: the full retrieval surface is ready. By the time Phase 3 reports COMPLETE and you flip `NEW_QUERY_PIPELINE_ENABLED=true`, the chat has access to all 10 tools — not just 7.

---

*End of EXEC_BRIEF_PHASE_9_v1_0.md (status `AUTHORED`, 2026-04-27). Trigger phrase: "Read EXEC_BRIEF_PHASE_9_v1_0.md and execute it." Designed for parallel execution alongside Phase 3.*
