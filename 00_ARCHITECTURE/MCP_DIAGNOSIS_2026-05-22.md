---
artifact: MCP_DIAGNOSIS_2026-05-22.md
status: DRAFT
authored_by: Claude (Cowork session, Sonnet 4.7)
authored_on: 2026-05-22
parent_brief: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
sealing_artifact: 00_ARCHITECTURE/MCP_WORKSTREAM_COMPLETE.md
audience: native
disposition: investigation + fix proposal; no code changes applied
---

# MCP Server — Diagnosis Report & Fix Proposal

**Date:** 2026-05-22
**Subject:** Why `ask_madhav` times out, why surgical primitives return empty, what Claude Chat sees vs. Cowork, and where the performance budget goes.
**Method:** read of the shipped code (`platform-mcp/`, `platform/src/lib/mcp/`, `platform/src/app/api/mcp/`, `platform/src/lib/retrieve/chart_facts_query.ts`, `vector_search.ts`); empirical probes against the live deployment (Cloud Run `amjis-mcp` at `amjis-mcp-qm256lasva-el.a.run.app`); full trace inspection of one `ask_madhav` call.

---

## §0 — Executive summary

The MCP transport itself **works**: API key auth, service-to-service handshake, transport, surgical-primitive dispatch, plan/execute round-trip, trace logging, and observability all return clean 2xx responses against the live deployment. The four symptoms you raised are caused by four independent root causes, not by a single broken thing:

| Symptom | Root cause | Severity | Fix scope |
|---|---|---|---|
| **`ask_madhav` times out in Claude Chat** | Synthesis stage takes 60+ s on `gemini-2.5-pro` even for trivial single-sentence queries. Confirmed empirically: a one-sentence Atmakaraka answer took **62,787 ms total** with **60,474 ms in synthesis alone**. Claude Chat's MCP tool timeout is ~60 s. We are over the line by milliseconds for the easiest possible query. | **P0** — every non-trivial query times out from Claude Chat's POV while the platform completes the work. | Real fix. Multiple levers: cheaper model for short answers, drop the `marsys_methodology_block` postlude, cap output tokens, narrower retrieval, stream via SSE. |
| **`query_chart_facts(category: "shadbala")` returns 0 rows** | The MCP code path is correct; the **chart_facts table in the deployed DB has no `shadbala` rows ingested**. Also no `ashtakavarga_sav`, no `dignity` (latter is not even a real category). `strength`, `planet`, `house`, `birth_metadata` all return data. The bootstrap covered only some FORENSIC sections. | **P1** — surgical answers to strength/dignity questions silently produce empty results that the LLM then has to handle without numerical ground truth. | Data ingestion, not code. Backfill from FORENSIC §3.x sections that hold the shadbala / ashtakavarga values. |
| **MCP tool description lists fake categories** | `query_chart_facts.ts` describes `dignity`, `nakshatra`, `house_placement`, `divisional_D9` as valid categories. None of these are in `ChartFactsCategory` (line 21–30 of `platform/src/lib/retrieve/chart_facts_query.ts`). Claude reads the description, calls with the fake category, gets 0 rows. | **P1** — propagates the appearance of "MCP is broken" because Claude follows the (lying) description. | One-file doc/string fix. |
| **`vector_search` returns generic, query-unrelated chunks via MCP primitives** | Real bug. The surgical-primitives dispatcher builds a placeholder `queryPlan` whose `query_text` field is the literal string `"surgical_primitive:vector_search"` (`platform/src/app/api/mcp/primitives/[tool]/route.ts:150`). `vector_search.ts:236` reads the embedding query from `plan.query_text`, not from `params.text`. So **every MCP `vector_search` call embeds the string "surgical_primitive:vector_search"** regardless of what the user passed. | **P0** for `vector_search` only — the tool is non-functional through MCP. | One-line fix in `vector_search.ts` (prefer `params.text`/`params.query_text` over `plan.query_text` when called from a surgical dispatcher). |
| **"Doesn't work in Claude Chat"** | Likely auth-config, not code. Claude.ai's "Add custom connector" UI as of mid-2026 has no Bearer header field; the MCP server already added a `?api_key=…` URL fallback (`server.ts:84–86`). If the connector URL was registered without the `?api_key=` query string, every call returns 401. | **P0** if confirmed; quick to verify. | Confirm registration URL; document the `?api_key=` pattern in the README. |
| **Deployment fragility** | `cloudbuild.yaml` only sets `PLATFORM_URL`. It does **not** set `MCP_INTERNAL_TOKEN`. Operator must set it out-of-band on the Cloud Run service; any redeploy that uses Cloud Build alone could wipe it. | **P2** — works today but a footgun. | Add `MCP_INTERNAL_TOKEN` to `cloudbuild.yaml` (via Secret Manager) and document in MCP_WORKSTREAM_COMPLETE.md operator checklist. |

The good news: **the architecture is sound**. The brief's design (thin sidecar adapter, all logic on the platform, two-layer auth, surgical-vs-end-to-end taxonomy, mandatory `epistemics` envelope) was carried out faithfully and is working. The problems are operational and performance, not architectural.

---

## §1 — What I confirmed actually works

These are empirical, not theoretical. Each one is a 2xx response from the live `amjis-mcp` service inside this session:

| Probe | Result | Latency reported by platform |
|---|---|---|
| `list_recent_queries(limit:15)` | 2 recent calls returned, scoped to my key | n/a (in-process) |
| `query_chart_facts(category:"planet", limit:3)` | 3 D10 planet rows returned | 14 ms |
| `query_chart_facts(category:"house", limit:5)` | 5 D10/D12 house rows returned | 9 ms |
| `query_chart_facts(category:"strength", limit:5)` | 5 CSI.* dignity-composite rows returned | 5 ms |
| `query_chart_facts(category:"birth_metadata", limit:5)` | 5 birth-metadata rows returned | 5 ms |
| `query_signals(domain:"career", limit:3)` | 100 MSR signals (limit not honored — see §5) | 35 ms |
| `lel_query(min_significance:0.7)` | All 36 LEL events returned | 11 ms |
| `vector_search(text:"strongest planet shadbala bala", top_k:5)` | 5 chunks returned, but **see §3.2 — embedding was wrong** | 595 ms |
| `plan_query("Which is my strongest planet?")` | Valid `PipelinePlan` returned with `query_class:"factual"` | ~2.3 s (planner LLM only) |
| `ask_madhav("In one sentence: what is my Atmakaraka?", mode:"factual")` | Correct answer ("Moon") with `SIG.MSR.317` citation; `synthesis_audit.holistic_read_passed:true`; 3 follow-ups | **62,787 ms end-to-end** |
| `get_trace(trace_id of ask_madhav above)` | Full 4-step trace with per-step latency breakdown | n/a |

So: auth, transport, tool dispatch, primitives, planner, full pipeline, observability, citations, suggested-followups, synthesis-audit envelope — all functional.

---

## §2 — Why `ask_madhav` times out (P0)

### §2.1 — The smoking-gun trace

For the query `"In one sentence: what is my Atmakaraka?"` with `mode:"factual"`, `get_trace` returned this breakdown:

| Step | Latency | Notes |
|---|---|---|
| `llm_planner` (gemini-2.5-flash) | **2,313 ms** | Fast; not the bottleneck. |
| `context_assembly` | 0 ms | Trivial. |
| `synthesis` (gemini-2.5-pro) | **60,474 ms** | **96% of total latency.** input_tokens=8,614, output_tokens=2,430, temperature=0 |
| — | — | — |
| **Total** | **62,787 ms** | |

Claude Chat's MCP tool-call timeout is **~60 seconds**. We exceed it by ~3 seconds **on the easiest possible query**. Anything that involves comparison, prediction, or multi-domain synthesis will overshoot by 30–60 s — exactly what you saw with "Which is my strongest planet?", which timed out twice.

### §2.2 — Why synthesis takes 60 s for a one-sentence answer

Three compounding issues, in increasing order of leverage:

**(a) Wrong model for short answers.** Synthesis runs on `gemini-2.5-pro` (slow, deep model). For a single-sentence factual lookup, Pro is overkill. `gemini-2.5-flash` would return the same answer in ~3–6 seconds.

**(b) 2,430 output tokens for one sentence.** Look at the answer payload:

```
Your Atmakaraka (AK), the Jaimini system's indicator of your soul's
core desire, is the Moon[^1].

[^1]: SIG.MSR.317
```marsys_methodology_block
I processed this as a factual L1 query, constrained by the user's
request for a single-sentence answer. I identified the relevant
Jaimini karaka by querying the Master Signal Register (MSR)…
[continues for several hundred more words]
```
```

The actual answer is ~25 tokens. The `marsys_methodology_block` postlude is ~2,400 tokens — 99% of generated output is "how I processed this", not the answer. The synthesis prompt presumably mandates this block in every response. **Removing or making it optional alone cuts ~50 s off synthesis latency** (output tokens dominate Gemini decode time at high counts).

**(c) Over-retrieval into the prompt.** The user asked about Atmakaraka. The planner emitted one tool call: `msr_sql({karakas:["AK"]})`. But the tool returned **100 signals** (the entire ≥0.7-significance high-confidence MSR head), including statistics, distribution metadata, Sade Sati architecture, and so on. The `karakas` filter was ignored by `msr_sql` (or not implemented). All 100 signals went into the synthesis prompt as `l2_items`, bloating input by ~2,700 tokens. The model then has to attend over the whole haystack to find one signal (`SIG.MSR.317`).

### §2.3 — Why streaming would help but isn't trivial

`platform/src/app/api/mcp/execute/route.ts:492` does `const answerText = await result.text`. The orchestrator streams synthesis output back as chunks, but the MCP route awaits the full text before returning. The MCP transport itself (StreamableHTTPServerTransport, `server.ts:141`) does support SSE — but the platform endpoint isn't emitting incrementally. So the MCP client sees one long-running request instead of a stream of chunks.

If we stream end-to-end, Claude Chat sees first-token in ~3–5 s and the timeout never triggers even if the full answer takes 90 s. This is the brief's R1 mitigation; it was deferred.

### §2.4 — Why the timeout asymmetry is awkward

| Layer | Timeout |
|---|---|
| Claude Chat (MCP client) | ~60 s |
| platform-mcp client → /api/mcp/execute (`client.ts:113`) | 125 s |
| Platform Next.js route `maxDuration` (`execute/route.ts:55`) | 120 s |
| Platform Cloud Run request | up to 3600 s |

The chain is **inverted at the top**: the client (Claude Chat) gives up before the inner layers do. The platform finishes successfully and writes the trace (you can see this — `get_trace` works for queries that "timed out" from Claude Chat's POV). The user just sees a timeout. The work isn't wasted; the answer is in the trace.

---

## §3 — Why surgical primitives appear to return empty (P1)

### §3.1 — `chart_facts_query`: data gap, not code bug

I probed nine `chart_facts` categories. Result distribution:

| Category (valid per enum) | Result |
|---|---|
| `birth_metadata` | 5 rows ✓ |
| `house` | 5 rows ✓ (D10, D12 only — no D1 in first 5) |
| `planet` | 3 rows ✓ (all D10) |
| `strength` | 5 rows ✓ (CSI.* dignity-composite for D1) |
| `shadbala` | **0 rows** ✗ |
| `ashtakavarga_sav` | **0 rows** ✗ |
| `dignity` (not in enum) | **0 rows** ✗ (would never match — `dignity` is not a real category) |

The valid `ChartFactsCategory` enum (`platform/src/lib/retrieve/chart_facts_query.ts:21–30`) has 37 values: `house, dasha_chara, planet, dasha_vimshottari, saham, sensitive_point, birth_metadata, strength_extra, yoga, dasha_yogini, deity_assignment, shadbala, ashtakavarga_sav, kp_cusp, navatara, panchang, cusp, arudha_occupancy, bhava_bala, chandra_placement, mrityu_bhaga, longevity_indicator, arudha, aspect, chalit_shift, kp_planet, special_lagna, strength, upagraha, ashtakavarga_bav, kakshya_zone, mercury_convergence, ashtakavarga_pinda, ishta_kashta, kp_significator, varshphal, avastha`.

`shadbala` and `ashtakavarga_sav` are valid categories, but the deployed Postgres has no rows for them — only the FORENSIC sections that the ingestion script touched made it in: §1.1 (birth metadata), §3.6 (D10 planets), §3.7 (D12 houses), §3.15 (D1→D9→D10 strength composite). The Shadbala virupa table (which lives elsewhere in FORENSIC) was not ingested.

This matches the v1.3 carry-forward queue item you already track:
> *"MSR signal-grounding gap — 419/573 signals lack explicit FORENSIC/LEL citations"*
> *"bootstrap `build_manifests` auto-registration"*

…and aligns with the bootstrap auto-registration audit item from Phase 4C close-out. The chart_facts bootstrap is partial.

### §3.2 — `vector_search`: real code bug

The surgical-primitives dispatcher (`platform/src/app/api/mcp/primitives/[tool]/route.ts:148–161`) builds a minimal `queryPlan`:

```ts
const queryPlan = {
  query_plan_id: queryId,
  query_text: `surgical_primitive:${mcpToolName}`,   // ← placeholder, not the user's text
  query_class: 'holistic' as const,
  // …
}
// Execute the retrieval tool
const rawResult = await tool.retrieve(queryPlan, toolParams)
```

`vector_search.ts:236` then does:

```ts
const queryText = plan.query_text   // ← reads the placeholder
// …
embedding = await getQueryEmbedding(queryText)   // ← embeds "surgical_primitive:vector_search"
```

So **every `vector_search` MCP call embeds the literal string `"surgical_primitive:vector_search"`**, not the user's `text` parameter. The user's text is in `toolParams.text` and is silently discarded.

Confirmed in my probe: I called `vector_search({text:"strongest planet shadbala bala", top_k:5})` and the response shows `invocation_params.query_text: "surgical_primitive:vector_search"`. The returned chunks (Cross-Reference Matrices, Avastha Diagnostics, Sensitive Points) are what you'd get if you embedded a string about MCP plumbing — generic, query-unrelated chart sections.

This is a one-line fix:

```ts
// in vector_search.ts retrieveImpl:
const queryText =
  (params?.text as string | undefined) ??
  (params?.query_text as string | undefined) ??
  plan.query_text
```

### §3.3 — Why `query_signals` ignores `limit`

I called `query_signals({domain:"career", limit:3})` and got back 100 signals. The `invocation_params` show `domains: []` (empty, not `["career"]`) and no `limit` echo. The `msr_sql` tool is not honoring the `domain` or `limit` params when called via the surgical primitives path. Most likely cause: the same shape as the `vector_search` bug — `msr_sql.ts` reads filters from `plan.*` fields (planets/houses/etc.) rather than from `params`. Worth a parallel audit of every surgical primitive that maps onto a retrieval tool with a planner-embedded params convention.

---

## §4 — Why "doesn't work in Claude Chat" — most likely auth-config

You said the MCP works locally in Cowork (confirmed here) but not in Claude Chat. The transport layer is identical. The most likely failure mode is at registration time, because:

- **Claude.ai's "Add custom connector" UI as of mid-2026 does not expose a Bearer-token field.** The `platform-mcp` author knew this and added a fallback at `server.ts:84–86`: if no `Authorization: Bearer` header is present, accept `?api_key=<key>` as a URL query parameter and synthesize a Bearer header from it.
- If you registered the connector with just the URL `https://amjis-mcp-qm256lasva-el.a.run.app` and no `?api_key=…` suffix, every request returns **401 Unauthorized** and Claude Chat reports the integration as broken.

The fix: register the connector URL as

```
https://amjis-mcp-qm256lasva-el.a.run.app?api_key=mcp_prod_<your-key>
```

(URL-embedded tokens leak to logs/referrers — your D12 decision accepts that for super-admin keys; do NOT use this for client-tier keys.)

If that's already what you did and it still 401s, the diagnostic path is:

1. `curl -sS -H "Authorization: Bearer $MARSYS_MCP_KEY" -X POST https://amjis-mcp-qm256lasva-el.a.run.app/mcp -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'` — should return the 19 tools.
2. If 401: check that the key still exists in `mcp_api_keys` and `revoked_at IS NULL`.
3. If 502/503: Cloud Run cold start (`min-instances:1` is in the cloudbuild, but if redeployed without that flag, cold starts are 5–15 s and Claude Chat may give up).
4. Check the platform's `MCP_INTERNAL_TOKEN` env var matches the MCP server's. If they diverged, `/api/mcp/keys/validate` 401s and the MCP server returns 401 to the client.

---

## §5 — Performance & latency budget (Claude Chat ceiling = ~60 s)

End-to-end breakdown for `ask_madhav` based on the trace and code reading:

```
┌────────────────────────────────────────────────────────────────────┐
│ Claude Chat → MCP server (Cloud Run amjis-mcp)                     │
│   network: 50–150 ms                                                │
│   key validation: HTTP call to platform /api/mcp/keys/validate     │
│     ─ Bearer split + PBKDF2-100k + DB lookup                       │
│     ─ NOT CACHED (every request)                                   │
│     ─ ~50–250 ms                                                    │
├────────────────────────────────────────────────────────────────────┤
│ MCP server → platform /api/mcp/execute                              │
│   network in-VPC: ~10 ms                                            │
│   service identity token fetch: ~50 ms (cached by Node libs)        │
├────────────────────────────────────────────────────────────────────┤
│ Platform pipeline:                                                  │
│   resolve singleton chart: 5–20 ms                                  │
│   rate-limit check: 5–20 ms                                         │
│   planner (gemini-2.5-flash): 2–4 s                                 │
│   manifest load + arbitrate budgets: ~50 ms                         │
│   B.11 floor enforcement: <1 ms                                     │
│   bundle hydration: ~10–50 ms                                       │
│   parallel tool execution: 30 ms – several seconds                  │
│   synthesis (gemini-2.5-pro): 30–90 s ← DOMINANT                    │
│   citation extraction: <10 ms                                       │
│   epistemics + followups + PPL: <50 ms                              │
└────────────────────────────────────────────────────────────────────┘

Best-case end-to-end: ~35 seconds (1-sentence answer, fast tools)
Typical: 60–90 seconds
Worst case: 120 s (platform maxDuration cap)
Claude Chat tolerance: ~60 seconds
```

**Conclusion:** the system is operating roughly at the timeout boundary on the cheapest queries. Anything non-trivial overshoots.

**Hot paths to shrink, ranked by leverage:**

| Lever | Estimated saving | Effort | Risk |
|---|---|---|---|
| Drop / make optional the `marsys_methodology_block` postlude in the synthesis prompt | **30–50 s** on simple queries (cuts 2,000+ output tokens) | Tiny — edit the synthesis prompt | None — it's an audit artifact, not part of the answer |
| Add `mode:"factual"` → route to `gemini-2.5-flash` for synthesis (not just planner) | 20–40 s on factual queries | Small — config switch in `getEffectiveModel('synthesis', …)` | Slight — Flash less subtle on multi-signal synthesis |
| Cap `max_output_tokens` in synthesis prompt by query class (factual: 400, holistic: 2,000) | 10–30 s | Small — orchestrator config | None |
| Honor `query_class:"factual"` in `msr_sql` to actually narrow the bundle (drop the 100→top-10 over-fetch) | 1–3 s + cuts cost | Medium — fix the planner-params → tool-filter handoff | Slight |
| Bearer-validation cache (60 s TTL, key_id → principal) | 50–250 ms per call | Small — in-memory LRU in `platform-mcp/src/auth.ts` | None (revocation only takes effect after TTL) |
| End-to-end SSE streaming to Claude Chat | First-token in ~5 s; full timeout never trips | Large — wire StreamableHTTPServerTransport.streamText all the way through `execute/route.ts` | Medium — error-mid-stream is harder to handle |
| Min-instances ≥1 on platform too (already set on MCP) | Avoid 3–10 s cold-start | Trivial — gcloud flag | None other than always-on cost |

If you do **only one** of the above, the postlude removal is the highest leverage by far. Going from ~63 s → ~13 s on a one-sentence query makes Claude Chat work today.

---

## §6 — Architectural observations (the brief survives)

These are not bugs, but they're worth flagging since you asked for an architectural read:

1. **Two-layer auth is correct but not cached.** Every MCP call does (a) Bearer PBKDF2 + DB lookup, (b) service-token validate, (c) principal-header inspection. A 60-second key-validation cache in `platform-mcp/src/auth.ts` keyed on the key prefix (`mcp_prod_xxxxxxxx`) drops ~50–250 ms per call with negligible security loss (D12 already accepts wide trust on issued keys).

2. **Trace is total — and that's a real product feature.** I called `get_trace` on a query I made 2 minutes earlier and got the full step ledger, including prompt previews and l2_items with 100 signal IDs and token estimates. This is exactly what the brief promised. The audit infrastructure is one of the strongest parts of the system.

3. **`synthesis_audit.holistic_read_passed` works.** It returned `true` for my factual call because `msr_sql` (an L2.5 tool) fired. The B.11 floor enforcement and audit envelope are in place and producing accurate flags.

4. **`epistemics` and `suggested_followups` are present.** Disclosure-tier discipline (G5) and the affordance (§4.7 of the brief) both shipped. Quality of suggested follow-ups is okay — they're generic ("How does this interact with the current dasha lord?") — refining the followup generator is a polish item, not a fix.

5. **Singleton-chart resolution is fine.** `MARSYS_MCP_CHART_ID` env override + DB fallback works (D11 honored).

6. **No mirror pair (D9 / G11) — correctly omitted.** No Gemini-side artifact; no `MP.N` declared in `CANONICAL_ARTIFACTS_v1_0.md §2`. Consistent with the brief.

7. **Statelessness (D10) is enforced.** Each request creates a new `McpServer` + `StreamableHTTPServerTransport` (`server.ts:96–143`); `conversation_history: []` is hard-coded in the orchestrator call (`execute/route.ts:477`). Good.

8. **Tier-1 `ask_madhav` and Tier-3 surgical primitives share zero code path discipline.** End-to-end runs the full planner→arbitrate→synthesize chain; primitives go straight to `tool.retrieve(queryPlan, toolParams)`. The split is clean. The only contamination is the `vector_search` bug where the surgical path's placeholder `queryPlan.query_text` leaks into the embedding query — fixable per §3.2.

9. **No conversation context. By design.** If you want Claude in Claude Chat to maintain context across turns when using MCP, you have to pass `context_hint` on each `ask_madhav` call. Claude Chat does this automatically for some MCPs; check whether it does for MARSYS in practice. Otherwise multi-turn flow degrades to "every turn is its own first turn" — usable but not optimal.

---

## §7 — Ranked fix proposal

### §7.1 — Critical, ship-this-week

1. **Remove/gate the `marsys_methodology_block` postlude in the synthesis prompt.**
   - File: wherever `PLANNER_PROMPT_v2_0.md` companion synthesis prompt lives (likely `platform/src/lib/synthesis/`). Search for `marsys_methodology_block`.
   - Change: emit only when `audience_tier === "super_admin"` AND a debug flag is set. For default responses, suppress entirely. This single change moves the typical synthesis below 60 s.
   - Verification: rerun `ask_madhav("In one sentence: what is my Atmakaraka?")`, check `get_trace` synthesis latency drops from ~60 s to ~10–15 s.

2. **Fix the `vector_search` placeholder-query bug.**
   - File: `platform/src/lib/retrieve/vector_search.ts:236`.
   - Change: prefer `params.text` / `params.query_text` over `plan.query_text` when the latter starts with `surgical_primitive:`.
   - Verification: `vector_search({text:"saturn shadbala", top_k:5})` returns Saturn-shadbala-related chunks, not generic Cross-Reference Matrix sections.

3. **Confirm the Claude Chat connector URL has `?api_key=…` appended.**
   - No code change — operator check.
   - Run the curl in §4 step 1 against the deployed URL with your key. If it returns the 19 tools list, the service is healthy and the Claude Chat issue is registration-side.

### §7.2 — High-leverage, ship-this-sprint

4. **Route synthesis by `query_class` to a cheaper model when factual.**
   - File: `execute/route.ts:412` (`getEffectiveModel(DEFAULT_STACK_ID, 'synthesis', 'primary', request)`).
   - Change: when `plan.query_class === "factual"` OR `mode === "factual"`, request the `synthesis_fast` model variant. The model registry already supports per-stack overrides.
   - Verification: factual queries finish in 5–15 s; holistic queries unchanged.

5. **Cap synthesis `max_output_tokens` by query class.**
   - File: `platform/src/lib/synthesis/index.ts` — wherever the LLM call is invoked.
   - Change: pass `max_output_tokens` based on `expected_output_shape`. Factual: 600. Holistic: 4,000. Predictive: 6,000. Today it's unbounded → models love to fill space.
   - Verification: `output_tokens` in `get_trace` synthesis step respects the cap.

6. **Backfill `chart_facts` for missing categories.**
   - Identify which FORENSIC sections hold Shadbala virupas, Ashtakavarga SAV/BAV/pinda, Avastha diagnostics, etc.
   - Add to the bootstrap script. Per the v1.3 carry-forward item already queued: this also resolves the build_manifests auto-registration audit.
   - Verification: `query_chart_facts({category:"shadbala", planet:"Saturn"})` returns the 59.18-virupa row (confirmed by `SIG.MSR.053` content).

7. **Fix the `query_chart_facts` tool description to list real categories only.**
   - File: `platform-mcp/src/tools/query_chart_facts.ts:19` (and the duplicate description string at line 54).
   - Change: replace `"shadbala", "dignity", "nakshatra", "aspect", "house_placement", "dasha_vimshottari", "divisional_D9"` with `"shadbala", "strength", "planet", "house", "aspect", "dasha_vimshottari", "saham"` — all of which are real enum values.
   - Verification: re-read the function-schema in tool listings; categories match the enum.

8. **Audit other surgical primitives for the same `plan.*` vs. `params.*` smuggling issue as `vector_search`.**
   - Files: every tool in `platform/src/lib/retrieve/` that's mapped in `primitives_registry.ts`.
   - Check: does the tool read filter fields from `plan.<field>` instead of `params.<field>`? If yes, the surgical primitives dispatch won't honor user filters because `queryPlan` is a minimal stub.
   - Suspects already observed: `msr_sql` (returned 100 signals, ignored `domain` + `limit`).

### §7.3 — Medium-term, ship-this-month

9. **End-to-end SSE streaming for `ask_madhav`.**
   - The MCP transport already supports streaming. The blocker is `execute/route.ts:492` (`await result.text`). Replace with chunked write via Next.js `Response` + Transform stream.
   - This is the proper fix for the 60-second ceiling. It makes the system robust to *any* query length.

10. **In-memory Bearer-validation cache in the MCP server.**
    - File: `platform-mcp/src/auth.ts`.
    - Add a `Map<key_prefix, {principal, expires_at}>` with 60-second TTL.
    - Saves 50–250 ms per call, hottest path in the system.

11. **Add `MCP_INTERNAL_TOKEN` to `cloudbuild.yaml`.**
    - Bind to Cloud Run Secret Manager; auto-mount on deploy.
    - Same on the `amjis-web` service. Document in `MCP_WORKSTREAM_COMPLETE.md` operator checklist.

### §7.4 — Polish

12. **Cleaner `suggested_followups`** — current ones are generic; the brief envisioned the planner emitting them based on what it deprioritized.

13. **Smarter MCP tool descriptions for the other 9 primitives** — same audit as `query_chart_facts` for `query_signals` (which is the most-called primitive after `ask_madhav`).

14. **Document the URL-embedded-key pattern in `platform-mcp/README.md` Auth section** with a clear "for Claude Chat custom integrations, use the `?api_key=` form" note.

---

## §8 — What I did not investigate (and why)

- **Multi-turn / `context_hint` behavior in Claude Chat:** would need a live Claude Chat session to test. Strongly suspect Claude Chat does not auto-pass prior turn summaries — the host has to. This is a stateless-by-design tradeoff (D10) and not a bug.
- **Phase MCP-5 OAuth:** explicitly deferred per brief §7.5; not relevant to today's symptoms.
- **The two MCP resources (`marsys://chart-overview`, `marsys://house-rules`):** present at `platform-mcp/resources/*.md`; I did not validate their content quality. Their job is orientation; if `ask_madhav` answers correctly they're doing their job.
- **Observatory cost dashboards:** `source:"mcp"` tagging is wired per brief §3.3, but verifying telemetry rows reach the dashboard requires a Cloud SQL probe I didn't run.
- **Phase 4C panchang interactions:** `query_panchanga` is one of the 10 primitives but no symptom suggested touching it.

---

## §9 — One-paragraph TL;DR for the operator

The MCP service is correctly built and deployed; the four symptoms are independent. `ask_madhav` times out from Claude Chat (~60 s ceiling) because synthesis emits a verbose `marsys_methodology_block` postlude that adds ~50 s and ~2,400 tokens to every response — kill or gate this block and the timeout disappears. `query_chart_facts(category:"shadbala")` returns empty because the deployed DB never got the Shadbala rows ingested, not because of the MCP code — backfill from the relevant FORENSIC sections. `query_chart_facts(category:"dignity")` returns empty because `dignity` isn't a real category — the MCP tool description lies about it; fix the description. `vector_search` returns wrong results because the surgical primitives dispatcher uses a placeholder query_text that `vector_search.ts` reads instead of the user's `text` param — one-line fix in `vector_search.ts`. The "doesn't work in Claude Chat" symptom is almost certainly the connector URL missing the `?api_key=<key>` query parameter that Claude.ai's UI requires when there's no Bearer field. Nothing here invalidates the brief's architecture — it's all operational and prompt-engineering work.

---

*End of MCP_DIAGNOSIS_2026-05-22.md (DRAFT). Awaits native review for status flip and decision on which §7 items to authorize.*
