---
artifact: CLAUDECODE_BRIEF_MCPT_V310_S2_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.1.0-S2
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN
branch: feature/mcpt-foundation
depends_on: [v3.1.0-S1]
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: Tier 2 composite bundles (holistic_bundle, multi_school_bundle) + SSE streaming + 5-min content-addressable cache
migration_number: 072
---

# v3.1.0-S2 — Tier 2 Bundles + SSE Streaming

You are a Claude Code sub-agent on WT-A (`MadhavMCPT-FDN`, branch `feature/mcpt-foundation`). v3.1.0-S1 has merged; primitives now honor `params` filters correctly. Your job is to implement the two composite bundles, wire SSE streaming for them, and add the 5-min content-addressable bundle cache.

Read: `MCP_ARCH_v3_PROPOSAL_2026-05-22.md §3.2 (bundles), §5 (envelope), §8 (streaming), §13 Q6 (cache)`; `MCP_TRANSFORMATION_PLAN_v1_0.md §3, §5`; `CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md §4 / v3.1.0-S2`.

## §1 — Scope

Implement `holistic_bundle` and `multi_school_bundle` as **opt-in orchestration aids** per arch §3.2 — deterministic parallel fan-out across primitives, NO LLM, per-sub-tool error isolation, SSE-streamed responses, content-addressable cache.

## §2 — Files in scope

```
platform-mcp/src/bundles/holistic_bundle.ts                              # new
platform-mcp/src/bundles/multi_school_bundle.ts                          # new
platform-mcp/src/bundles/index.ts                                        # composition rules + sub-tool fan-out
platform-mcp/src/bundles/cache.ts                                        # 5-min content-addressable cache
platform-mcp/src/server.ts                                               # register bundles + SSE transport
platform/src/app/api/mcp/bundles/[name]/route.ts                         # new SSE-emitting platform endpoint
platform/supabase/migrations/072_mcp_bundle_cache.sql                    # bundle cache table
platform-mcp/test/bundles/holistic_bundle.test.ts                        # new tests
platform-mcp/test/bundles/multi_school_bundle.test.ts
platform-mcp/test/bundles/cache.test.ts
platform-mcp/test/bundles/sse_streaming.integration.test.ts
```

## §3 — Files NOT in scope

```
platform-mcp/src/resources/**                                            # S3 territory
platform/src/lib/perf/**                                                 # S4 territory
platform-mcp/src/tools/*.ts                                              # S1 owned (descriptions); only register bundles in server.ts
platform/src/lib/prompts/templates/shared.ts                             # not in MCP Transformation scope
platform/src/app/consume/**, platform/src/app/api/chat/**                # web /consume untouched
```

## §4 — Per-bundle specification

### `holistic_bundle(query_text, focus_domains?, time_window?, subset?)`

Sub-tool composition (run in parallel via `Promise.allSettled`):
1. `query_signals` filtered by `focus_domains` if provided, else top 100 MSR signals by significance
2. `get_cgm_subgraph` with `hops=3` around nodes matching `query_text` keywords
3. `vector_search` with `source_filter:UCN_v4_1`, top_k=25
4. `vector_search` with `source_filter:RM_v2_2`, top_k=15
5. `vector_search` with `source_filter:CDLM_v1_3`, top_k=15
6. `lel_query` filtered by `time_window` if provided
7. `query_panchanga(today)` for current panchang
8. `query_dasha_periods(active_only:true)` for current dasha state

If `subset:["MSR","CGM"]` provided, fire only those (case-insensitive name match).

Per-sub-tool timeout: 8 seconds. On timeout or error: include `{errored: true, error_class: "...", attempted_params: {...}}` in that `bundle_entries[]` slot; do not fail the bundle.

Top-level `provenance.signal_ids_available[]` = union across all successful sub-tools' `signal_ids_available[]`.

### `multi_school_bundle(claim, schools?)`

Sub-tool composition (parallel):
1. `cross_school_lookup(claim, schools)`
2. Per requested school: targeted primitive query for that school's evidence:
   - Parashara: `query_signals` filtered by keywords from claim
   - Jaimini: `query_chart_facts(category:"strength_extra")` filtered for jaimini karaka rows
   - KP: `query_chart_facts(category:"kp_cusp")` for the relevant cusps (skip if not backfilled — `data_coverage` reports 0 rows)
   - Tajaka: `query_chart_facts(category:"varshphal")` (skip if not backfilled)
3. `read_classical_text` for the most-cited classical reference per school (use cross_school_lookup's response to identify which work/chapter)

Same error-isolation semantics as `holistic_bundle`.

### Bundle cache (`platform-mcp/src/bundles/cache.ts` + migration 072)

Schema:

```sql
CREATE TABLE mcp_bundle_cache (
  cache_key text PRIMARY KEY,                       -- sha256(query_text + JSON-stringified composition_params + tier + chart_id)
  bundle_name text NOT NULL,                        -- 'holistic_bundle' | 'multi_school_bundle'
  audience_tier text NOT NULL,
  chart_id uuid NOT NULL,
  envelope_json jsonb NOT NULL,                     -- full envelope (per arch §5)
  cached_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL                   -- cached_at + interval '5 minutes'
);

CREATE INDEX mcp_bundle_cache_expiry ON mcp_bundle_cache (expires_at);
-- Periodic cleanup (every 10 min): DELETE FROM mcp_bundle_cache WHERE expires_at < now();
```

Lookup logic in `cache.ts`: compute key, SELECT, if hit and not expired return cached envelope with `served_from_cache: true`. On miss, run the bundle, store result, return with `served_from_cache: false`.

### SSE streaming (`platform/src/app/api/mcp/bundles/[name]/route.ts`)

Emit SSE events per arch §8:

```
event: bundle.sub_tool.started
data: {"sub_tool":"query_signals","started_at":"..."}

event: bundle.sub_tool.completed
data: {"sub_tool":"query_signals","ok":true,"rows_returned":87,"signal_ids":["SIG.MSR.053",...]}

event: bundle.sub_tool.error
data: {"sub_tool":"vector_search","ok":false,"error_class":"timeout"}

event: bundle.completed
data: { /* full envelope with consolidated provenance */ }
```

Implementation: Next.js `Response` with `ReadableStream` body; SSE-formatted chunks; `Promise.allSettled` over sub-tools; pipe each settled promise to the stream.

Tier 1 primitives do NOT stream; only bundles.

## §5 — Acceptance criteria (AC.S2.1 through AC.S2.8)

Per parent brief `CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md §4 / v3.1.0-S2 §Acceptance`.

## §6 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN && \
  test -f platform-mcp/src/bundles/holistic_bundle.ts && \
  test -f platform-mcp/src/bundles/multi_school_bundle.ts && \
  test -f platform/supabase/migrations/072_mcp_bundle_cache.sql && \
  grep -q "holistic_bundle" platform-mcp/src/server.ts && \
  grep -q "multi_school_bundle" platform-mcp/src/server.ts && \
  cd platform-mcp && npm test -- bundles/ 2>&1 | tail -10
```

## §7 — Sealing artifact

`00_ARCHITECTURE/MCPT_V310_S2_CLOSE.md`. Body: bundle composition decisions per sub-tool, SSE wire format spec, cache hit/miss test evidence, AC evidence table.

---

*End of CLAUDECODE_BRIEF_MCPT_V310_S2_v1_0.md.*
