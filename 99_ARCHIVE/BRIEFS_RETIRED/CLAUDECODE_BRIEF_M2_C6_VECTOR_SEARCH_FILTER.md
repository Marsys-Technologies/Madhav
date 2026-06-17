---
brief_id: M2_C6_VECTOR_SEARCH_FILTER
karn_session_name: KARN-W1-R2-VECTOR-FILTER
wave: 1
stream: B
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-29
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (TypeScript router prompt + tool filter; tests; deploy; verify)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: none (independent of A1)
  blocks: nothing in Wave 1; informs F2 eval harness
parallel_stream_note: |
  Three other Wave-1 briefs run concurrently: M2_PHASE_ALPHA (Stream A,
  read-only audit), M2_D56_OBSERVABILITY (Stream E, migrations), M2_B3_CLUSTER_RECLUSTER
  (Stream C, JSON outputs). All disjoint paths.
estimated_time: ½ day single Claude Code session

scope_summary: |
  F2.2 from the master plan. Add doc_type[] and layer filter parameters
  to vector_search.ts so the classifier can narrow vector retrieval
  per query class. Update the router prompt to instruct the LLM to
  emit doc_type filter per query_class. Verify with E2E queries.

  Specifically targets the Q1 verification gap from 2026-04-29: a
  factual query "What sign is my Mercury?" returned only DVS L1 chunks
  from vector_search and msr_sql=0 rows. With doc_type filter exposed,
  the classifier can route factual queries to L1 chunks while
  interpretive queries get L1+L2.5, etc.

may_touch:
  - platform/src/lib/retrieve/vector_search.ts                       # add filter params
  - platform/src/lib/retrieve/types.ts                               # extend if Tool input schema needs new fields
  - platform/src/lib/retrieve/__tests__/vector_search.test.ts        # extend with filter tests
  - platform/src/lib/router/prompt.ts                                # add doc_type filter guidance + few-shot
  - platform/src/lib/router/types.ts                                 # if QueryPlan needs vector_search_filter field
  - platform/src/lib/router/__tests__/router.test.ts                 # add tests for filter emission
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_C6_VECTOR_SEARCH_FILTER.md  # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_C6_VERIFICATION_<DATE>.txt             # CREATE post-deploy verification

must_not_touch:
  - CLAUDECODE_BRIEF.md (root)                                       # UI/UX stream
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_PHASE_ALPHA.md        # other Wave-1 brief
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_D56_OBSERVABILITY.md  # other Wave-1 brief
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B3_CLUSTER_RECLUSTER.md  # other Wave-1 brief
  - platform/src/components/**                                       # UI/UX scope
  - platform/src/app/**                                              # UI/UX scope
  - platform/src/hooks/**                                            # UI/UX scope
  - platform/src/lib/retrieve/**                                     # OTHER tools — no edits
  - platform/src/lib/retrieve/cgm_graph_walk.ts                      # explicit
  - platform/src/lib/retrieve/msr_sql.ts                             # explicit
  - platform/src/lib/retrieve/pattern_register.ts                    # explicit
  - platform/src/lib/retrieve/resonance_register.ts                  # explicit
  - platform/src/lib/retrieve/cluster_atlas.ts                       # explicit
  - platform/src/lib/retrieve/contradiction_register.ts              # explicit
  - platform/src/lib/retrieve/manifest_query.ts                      # explicit
  - platform/src/lib/retrieve/temporal.ts                            # explicit
  - platform/src/lib/retrieve/query_msr_aggregate.ts                 # explicit
  - platform/src/lib/router/router.ts                                # caller; do not modify
  - platform/src/lib/bundle/**                                       # not in scope
  - platform/src/lib/synthesis/**                                    # not in scope
  - platform/python-sidecar/**                                       # backend off-limits
  - platform/migrations/**                                           # NO migrations
  - 025_HOLISTIC_SYNTHESIS/**                                        # source-of-truth read-only

acceptance_criteria:
  AC.1: |
    vector_search.ts gains two new optional input parameters:
      - doc_type?: string[]    (filter to specific doc_types)
      - layer?: string         (filter to specific layer; e.g., "L1", "L2.5")
    Both default to "no filter" (backward compatible).
  AC.2: |
    The SQL WHERE clause in vector_search adds:
      AND ($N::text[] IS NULL OR doc_type = ANY($N::text[]))
      AND ($M::text IS NULL OR layer = $M)
    while preserving the existing is_stale=false filter and ORDER BY embedding distance.
  AC.3: |
    QueryPlan.vector_search_filter optional sub-object added to types.ts if not already present.
    Shape: { doc_type?: string[], layer?: string }
    OR re-use existing per-tool params field if the codebase already uses that pattern.
  AC.4: |
    prompt.ts ROUTER_SYSTEM_PROMPT extended with a "## Vector Search Filter Guidance" block:
      - factual class → layer="L1", doc_type=["l1_fact"]
      - interpretive class → layer null (all layers), doc_type=["l1_fact","ucn_section","msr_signal","cdlm_cell"]
      - cross_domain class → no filter (all docs)
      - discovery class → doc_type=["msr_signal","ucn_section","domain_report","cdlm_cell"]
      - holistic class → no filter
      - predictive class → doc_type=["l1_fact","msr_signal"] (lean toward facts + signals)
      - remedial class → doc_type=["l4_remedial","domain_report"] when those exist
    At least 3 few-shot examples updated to show the new filter param.
  AC.5: |
    vector_search.test.ts adds ≥6 new tests: layer filter, doc_type filter, both filters,
    backward compat (no filters → existing behavior), invalid doc_type values handled gracefully,
    SQL injection safety for filter values.
  AC.6: |
    router.test.ts adds ≥4 new tests asserting the classifier's emitted plan includes the
    expected vector_search_filter for factual / interpretive / discovery / predictive classes.
  AC.7: |
    npm test passes at the pre-existing baseline (~9 known failures). NO new failures.
    Closing summary reports exact passed/failed counts before and after.
  AC.8: |
    Cloud Run revision amjis-web is rebuilt and serving 100% via:
      bash platform/scripts/cloud_build_submit.sh
    New revision number captured in closing summary.
  AC.9: |
    Post-deploy verification — send 5 representative queries through the deployed Consume
    tab via the trace UI or via curl with a known session cookie:
      Q-V1: "What sign is my Mercury?" (factual; expect layer=L1 doc_type=[l1_fact])
      Q-V2: "What does my chart say about career?" (interpretive; expect mixed L1+L2.5)
      Q-V3: "What patterns does my chart show?" (discovery; expect msr_signal+ucn_section)
      Q-V4: "Are there contradictions in my chart?" (cross_domain; expect no filter)
      Q-V5: "When is my next career change?" (predictive; expect l1_fact+msr_signal)
    Wait ~30s after the last query. Then query query_trace_steps for each, capturing the
    classify step's emitted plan AND the vector_search step's input params.
    Append to 00_ARCHITECTURE/BRIEFS/M2_C6_VERIFICATION_<DATE>.txt.
    Pass criterion: ≥4 of 5 queries show the expected filter in the trace.
  AC.10: |
    This brief's frontmatter `status` flipped to COMPLETE.
  AC.11: |
    git status post-session shows ONLY the 7 expected files (vector_search.ts, types.ts in retrieve,
    vector_search.test.ts, prompt.ts, types.ts in router, router.test.ts, this brief, the verification txt).
    Specifically: NO files under platform/src/components/**, platform/src/app/**, platform/src/hooks/**,
    other retrieve tools, bundle, synthesis, python-sidecar, or migrations.

halt_conditions:
  - Auth Proxy unreachable on 127.0.0.1:5433 (only needed for AC.9 verification)
  - npm test introduces NEW failures (count > pre-existing baseline)
  - Cloud Build fails after one auto-retry
  - Cloud Run deploy fails
  - Branch is not redesign/r0-foundation
  - Pre-existing uncommitted modifications to files this brief intends to edit
---

# CLAUDECODE_BRIEF — M2_C6_VECTOR_SEARCH_FILTER (Wave 1, Stream B)

## §1 — Why this session

Verification on 2026-04-29 showed Q1 ("What sign is my Mercury?") returned msr_sql=0 rows and only DVS L1 chunks from vector_search. The factual query class isn't getting the right vector retrieval — the classifier doesn't currently tell vector_search what doc_types to retrieve. Adding the filter and the per-class guidance closes that gap with one small surgical change.

This brief is independent of A1's audit and other Wave-1 briefs. It can run in parallel.

## §2 — Pre-flight self-diagnostics (mandatory)

### §2.1 — Branch + working tree
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
test "$(git branch --show-current)" = "redesign/r0-foundation" || HALT "wrong branch"
git status --short
# HALT if any of these have uncommitted modifications:
#   platform/src/lib/retrieve/vector_search.ts
#   platform/src/lib/retrieve/types.ts
#   platform/src/lib/router/prompt.ts
#   platform/src/lib/router/types.ts
```

### §2.2 — Test baseline
```bash
cd platform
npm test --silent 2>&1 | tail -5 > /tmp/test_baseline.txt
cat /tmp/test_baseline.txt
# Expected pattern: "X passed | Y failed" with Y ~= 9 (pre-existing).
# If Y > 12, halt — pre-existing regression unrelated to this brief.
```

### §2.3 — Verify vector_search current implementation
```bash
test -f platform/src/lib/retrieve/vector_search.ts || HALT "vector_search.ts missing"
grep -q "VECTOR_SEARCH_ENABLED" platform/src/lib/retrieve/vector_search.ts || \
  echo "WARN: feature flag may have moved — check before edit"
```

## §3 — Implementation steps

### §3.1 — Read vector_search.ts and types.ts to understand current shape

Read both files end-to-end. Identify:
- The current `inputSchema` Zod object (Vercel AI SDK pattern likely).
- The current SQL WHERE clause structure.
- How params reach the SQL query.

Document the existing shape in scratch notes.

### §3.2 — Extend the input schema

Add two optional params to vector_search's input schema:

```ts
inputSchema: z.object({
  // ... existing params (query_text, top_k, native_id, etc.)
  doc_type: z.array(z.string()).optional()
    .describe('Filter results to specific doc_types. Default: no filter (all doc_types). Valid values include l1_fact, ucn_section, msr_signal, cdlm_cell, cgm_node, domain_report, rm_element.'),
  layer: z.string().optional()
    .describe('Filter results to a specific layer. Default: no filter. Valid values: L1, L2.5, L3, L4, L5.'),
}),
```

### §3.3 — Extend the SQL WHERE clause

Find the existing query. Likely:
```sql
WHERE c.is_stale = false
ORDER BY e.embedding <=> $1::vector
LIMIT $2
```

Extend to:
```sql
WHERE c.is_stale = false
  AND ($3::text[] IS NULL OR c.doc_type = ANY($3::text[]))
  AND ($4::text IS NULL OR c.layer = $4)
ORDER BY e.embedding <=> $1::vector
LIMIT $2
```

Pass the new params positionally (or via named params if the codebase uses that). Default to NULL when undefined so backward-compat is preserved.

### §3.4 — Update QueryPlan / types if needed

If the existing pattern is per-tool params (i.e., the QueryPlan has a `tool_params: { vector_search: {...} }` shape), the new fields slot into that. If not, add an optional `vector_search_filter: { doc_type?: string[], layer?: string }` field on QueryPlan.

Choose whichever matches the existing convention. Document the choice in a one-line code comment.

### §3.5 — Update the router prompt

In `platform/src/lib/router/prompt.ts`, add a new "## Vector Search Filter Guidance" block to ROUTER_SYSTEM_PROMPT, BEFORE the few-shot examples. Per AC.4, include the per-class doc_type/layer guidance.

Update at least 3 few-shot examples to show the new filter:
- factual: `"vector_search_filter": { "layer": "L1", "doc_type": ["l1_fact"] }`
- interpretive: `"vector_search_filter": { "doc_type": ["l1_fact","ucn_section","msr_signal","cdlm_cell"] }`
- predictive: `"vector_search_filter": { "doc_type": ["l1_fact","msr_signal"] }`

Add a rule to the rules list:
```
14. vector_search_filter: optional object with {doc_type[], layer} that narrows
    semantic retrieval. See "Vector Search Filter Guidance" block. When unsure,
    omit (omit = no filter = all doc_types).
```

### §3.6 — Tests

In `vector_search.test.ts`, add the 6 tests per AC.5. Use the existing test scaffold. Mock the DB call where the existing tests do; assert the SQL params include the filter values.

In `router.test.ts`, add the 4 tests per AC.6. Each test mocks the LLM response with a representative QueryPlan that includes vector_search_filter; assert the parsed plan has the expected filter values.

### §3.7 — Run tests + deploy

```bash
cd platform
npm test --silent 2>&1 | tail -5 > /tmp/test_after.txt
cat /tmp/test_after.txt
# Compare to /tmp/test_baseline.txt — fail count must be the SAME (or lower).
# If higher, HALT.
```

If tests pass:
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
bash platform/scripts/cloud_build_submit.sh
```

Wait for deploy. Confirm:
```bash
gcloud run revisions list --service amjis-web --region asia-south1 --project madhav-astrology --limit 3
```

The newest revision should be serving 100%.

### §3.8 — Post-deploy live verification

Per AC.9, send 5 queries through the deployed Consume tab. Two paths:

**Path A — Browser/UI:** Hit the Consume tab as super_admin, send each query, wait for response.

**Path B — curl:** If you have a session cookie, post to /api/chat/consume.

After all 5 queries complete (~3 minutes total), query query_trace_steps:

```sql
WITH recent_queries AS (
  SELECT DISTINCT query_id
  FROM query_trace_steps
  WHERE created_at > NOW() - INTERVAL '10 minutes'
  ORDER BY created_at DESC
  LIMIT 5
)
SELECT
  qts.query_id,
  qts.step_seq,
  qts.step_name,
  CASE
    WHEN qts.step_name = 'classify' THEN qts.payload->'plan_emitted'->>'query_class'
    ELSE NULL
  END AS query_class,
  CASE
    WHEN qts.step_name = 'classify' THEN qts.payload->'plan_emitted'->'vector_search_filter'
    WHEN qts.step_name = 'vector_search' THEN qts.payload->'invocation_params'
    ELSE NULL
  END AS filter_or_params
FROM query_trace_steps qts
JOIN recent_queries rq ON qts.query_id = rq.query_id
WHERE qts.step_name IN ('classify', 'vector_search')
ORDER BY qts.query_id, qts.step_seq;
```

Capture output to `00_ARCHITECTURE/BRIEFS/M2_C6_VERIFICATION_<DATE>.txt`.

For each of the 5 queries, document: query class, filter emitted, filter actually used by vector_search. Pass = ≥4 of 5 match expected behavior.

### §3.9 — Closing summary

Print to session output per execution plan §3.4 standardized format, including:
- Pre-test baseline vs post-test counts (Y failed → Y' failed).
- Cloud Run revision deployed.
- Per-query verification of the filter behavior.
- Brief status flip.

### §3.10 — Update brief status

Edit this brief's frontmatter `status: PENDING` → `status: COMPLETE`.

## §4 — Hard constraints

- **Only the 7 named files may change.** No other retrieve tools. No bundle. No synthesis. No backend.
- **Backward compat preserved.** Existing callers that don't pass doc_type/layer behave exactly as before.
- **No migrations.** rag_chunks already has doc_type and layer columns.
- **No new feature flags.** The filter is always available; classifier opt-in.
- **No changes to cgm_graph_walk, msr_sql, etc.** Other retrieve tools work as-is.

## §5 — Closing checklist

- [ ] Pre-flight §2.1–§2.3 PASS
- [ ] vector_search.ts has new doc_type[] + layer params
- [ ] SQL WHERE updated with filter clauses
- [ ] router prompt has filter guidance block + 3+ updated few-shots
- [ ] router rules updated to include rule 14
- [ ] vector_search.test.ts has ≥6 new tests, all pass
- [ ] router.test.ts has ≥4 new tests, all pass
- [ ] npm test failure count = baseline (no new failures)
- [ ] Cloud Run revision deployed and serving 100%
- [ ] M2_C6_VERIFICATION_<DATE>.txt has 5-query trace + filter analysis
- [ ] ≥4 of 5 verification queries show expected filter behavior
- [ ] git status shows only the 7 expected files
- [ ] This brief's status flipped to COMPLETE

---

*End of M2_C6_VECTOR_SEARCH_FILTER. Status: COMPLETE. Closed 2026-04-30 by KARN-W1-R2-VECTOR-FILTER.*

## Kickoff prompt

```
You are running KARN-W1-R2-VECTOR-FILTER.

Read 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_C6_VECTOR_SEARCH_FILTER.md
as the governing scope. Branch is redesign/r0-foundation. Do NOT read
CLAUDECODE_BRIEF.md at the project root — UI/UX stream owns it.

This session is part of Project KARN. For cross-session context:
- 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md (operating rules)
- 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md (history)
- 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §3 (autonomous brief contract)

This is TypeScript-side only (vector_search + router prompt), no backend
work, no migrations. Run autonomously per the brief's §3 implementation
steps. Halt and report only on conditions enumerated in halt_conditions.
Otherwise complete fully including deploy + post-deploy verification.

At session close, append a standardized closing entry to
PROJECT_KARN_SESSION_LOG.md per the protocol §2 entry format. Use
karn_session_name = KARN-W1-R2-VECTOR-FILTER.
```
