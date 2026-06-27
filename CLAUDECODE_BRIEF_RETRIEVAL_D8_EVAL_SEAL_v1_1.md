---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D8_EVAL_SEAL
version: 1.1
status: COMPLETE
created: 2026-06-27
updated: 2026-06-28
author: Cowork (planning v1.0) + Claude Code DETAIL-PASS agent (v1.1 resolution)
classification: CLAUDECODE_BRIEF — D8 eval harness + governance + seal (closes the master artifact)
session_type: implementation — the gate that seals the retrieval system
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (wave D8; principle 10)
depends_on: D1–D7 + D-PROFILES
resolved_from:
  - CLAUDECODE_BRIEF_RETRIEVAL_D8_EVAL_SEAL_v1_0.md (parameterized shell)
  - RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md (4 provider specs)
  - RETRIEVAL_MODEL_PROFILES_v1_0.md (4 family profiles, UNMEASURED)
  - platform/src/lib/retrieval/ (registry, router, grounding, MARO, synergy, channel)
  - platform-mcp/src/server.ts (13 wired tools; GET /mcp → 405; stateless)
  - RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_1.md (14 principles; §H contamination audit)
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md §6 (14 binding principles)
hard_constraints:
  - eval harness GATES the seal — no retrieval seal without it (principle #10)
  - evaluate trajectories, not just outputs; calibrate the LLM judge against a human gold set
  - chart-agnostic eval (multiple charts, never native-only) — principle #14
acceptance_criteria: see §4
changelog:
  - v1.0 (2026-06-27): Parameterized shell — structure set, specifics deferred to detail-pass.
  - v1.1 (2026-06-28): DETAIL-PASS — every [resolved from …] marker filled with concrete specs.
    Eval queries, per-model expected behaviors, governance checks, profile-hardening targets,
    red-team checklist, and seal criteria are now concrete. No structural changes to §1–§4 shape.
---

# CLAUDE CODE BRIEF — D8: EVAL HARNESS + GOVERNANCE + SEAL (resolved v1.1)

> The eval harness both grades retrieval quality AND hardens the D-PROFILES values from hypothesis
> to measured fact. It gates the seal. This v1.1 brief is fully resolved: every parameter, query,
> threshold, and governance check is specified concretely from the built system.

---

## §0 — Resolved inputs (what was built in D1–D7 + D-PROFILES)

**The system to evaluate** (resolved from code-plane audit):

- **Registry**: `platform/src/lib/retrieval/registry/` — clean, chart-agnostic; L0 (15 caps),
  L1 (19 caps), L2 (8 caps incl. `query_ucd`, `query_signals`, `query_contradictions`,
  `query_domain_reading`, `traverse_chart_graph`, `register_d4_graph`, `query_quality_scorecard`,
  `query_remedies`), L3 (7 caps), L4 (3 caps), L5 (5 caps). Plus D6 (2 synergy caps), D7 (2
  channel caps), D-PROFILES (MARO registration). Total registry: ~61+ capability URIs.
- **Router**: `platform/src/lib/retrieval/router/` — rule-driven classifier → tool_selector →
  budget + termination → trajectory log. Five route classes. `chart_id` required; throws if absent.
- **Grounding spine**: `platform/src/lib/retrieval/grounding/` — `resolveSignals()` +
  `resolveMetric()` + `assertNoN5Violations()`. Governed metric vocabulary (GOVERNED_METRICS set).
  Orphan fact_id tracking. Chart-scoped, errors if `chart_id` absent.
- **MARO**: `platform/src/lib/retrieval/maro/` — `orchestrate()` / `resolveNormalization()` /
  `getMcpSurface()` / `normalizeToolArgs()` / `validateAndRepair()` / `stripMcpConstructs()`.
  Four profiles (ANTHROPIC, GEMINI, OPENAI, DEEPSEEK) + UNIVERSAL fallback. All tagged
  `status: UNMEASURED` / `PROFILE_VERSION: '1.0.0'` — D8 measurement upgrades these to `MEASURED`.
- **Synergy (D6)**: `register_d6_synergy.ts` — `marsys://tool/synergy/pipeline` +
  `marsys://tool/synergy/cross_layer`. Introspection-only; pipeline descriptor is the D8 harness
  entry point.
- **Channel (D7)**: `register_d7_channel.ts` — `marsys://tool/channel/mcp_wiring` +
  `marsys://tool/channel/chat_dispatch`. The chat dispatch descriptor explicitly marks migration
  status as PENDING (legacy `lib/retrieve` still active; `getCatalog()` not yet wired).
- **MCP server**: `platform-mcp/src/server.ts` — 13 registered tools (L0 Brahmagyan, L0 ephemeris,
  3 L1 PyJHora, L2 holistic bundle ×2, L3 kala_temporal, L0 remedy ×7 grouped, L4 event anchors,
  L4 mitigation, L4 muhurta, L4 outlook, L5 lel_intake, L5 outcome). GET /mcp → 405 (stateless
  Streamable HTTP only). D6/D7 registry caps NOT integrated into server startup yet.
- **Known contamination to remediate (from §H audit)**: `platform-mcp/src/tools/kala_temporal.ts`,
  `retrieval/holistic_bundle.ts`, `retrieval/ganita_forensic_render.ts`, `l0_brahmagyan.ts` all
  carry CRITICAL native defaults; `kala_convergence.ts` defaults date ranges to native lifespan;
  `mimamsa_lel_intake.ts` serves native LEL with no chart selector. These are remediation targets,
  not passing the chart-agnostic gate.

**The golden set** (resolved per §1 — calibration approach, not blog numbers):
- 50 human-rated items minimum (target: 100–150 for stable correlation); items span all 5 route
  classes and 6 layers; multiple chart_ids (never only the native). See §1.1 for sourcing.
- Judge calibration threshold: Pearson r ≥ 0.80 on the human-vs-judge overlap set before the
  judge scores anything in CI.

---

## §1 — Eval harness (concrete specs)

### §1.1 — Golden set construction

**Sourcing (chart-agnostic, principle #14):**
- Use AT LEAST 3 distinct chart_ids in the golden set: the native chart
  `482012f1-710e-4a25-994a-93821f5871aa` for audit/read-only validation runs; plus at minimum 2
  synthetic charts (e.g. Abhinandan `1c826d5a` if populated, or test fixture charts with known
  L1 data). Any item that references only the native chart is marked `native_only: true` and
  excluded from the primary CI gate score — it contributes to the calibration audit only.
- **Human annotation protocol**: each item is annotated by the native (Abhisek Mohanty, the domain
  expert) on two axes: (a) retrieval relevance (did the retrieved context contain what was needed?
  0/1/2) and (b) answer faithfulness (is every claim in the answer traceable to the retrieved
  context? 0/1/2 per atomic claim). A 2-annotator subset (native + one additional reviewer) on 20%
  of items gives inter-annotator agreement (Cohen's κ target ≥ 0.70 before using annotations).
- **Item distribution (100-item target)**:

  | Route class | Layer focus | Count |
  |---|---|---|
  | single_shot | L0/L1 | 20 |
  | deterministic | L1/L2 | 20 |
  | relational / multi_hop | L2/L3 (CGM, contradictions) | 25 |
  | semantic / narrative | L2/L4/L5 | 20 |
  | graph | L2 CGM + CDLM | 15 |

**Specific golden queries (concrete, not illustrative):**

*single_shot / deterministic:*
1. "What is the longitude of Mars in the D1 chart?" → expected: `resolveMetric(fact_value_num)` for the Mars longitude fact_id; answer cites `fact_id`; no fabrication.
2. "List all yogas formed in the chart with their component planets." → expected: `query_yoga_dosha` (L1); result contains yoga names + planet lists from `chart_facts`; faithfulness = every planet mentioned is in a resolved fact.
3. "What is the Vimshottari mahadasha sequence from birth?" → expected: `get_dashas` (L1); answer ordered chronologically; each period has start/end date from L1.
4. "Which houses does Saturn aspect in the D9 chart?" → expected: `get_aspects` (L1, divisional=D9); answer references `fact_id` for each aspect.
5. "What is the ashtakavarga score for the 7th house?" → expected: `get_ashtakavarga` (L1); numeric value read from `chart_facts`, cited.

*relational / contradiction / multi_hop:*
6. "What are the top-3 contradicting signals in the L2 Bodha layer and their constituent facts?" → expected: `query_contradictions` (L2); returns signal_id pairs + `signal_a_id` / `signal_b_id` + resolved constituent facts from `chart_facts`; `has_n5_violations: false`.
7. "Traverse the CGM graph from the karma bhava node and return connected signals within 2 hops." → expected: `traverse_chart_graph` or `register_d4_graph` (L2); graph response; no fabricated edges.
8. "Which L2 signals cite the same L1 fact_id as the Sun's dignity entry?" → expected: grounding spine `resolveSignals()` on Sun dignity fact_id; signals that share it in `constituent_facts_array`.
9. "What domain does the highest-salience L2 signal belong to, and what L1 facts does it rest on?" → expected: `query_signals` (L2) ordered by `computed_salience` DESC; top signal's `constituent_facts_array` resolved via grounding spine; domain from `signal_type_class`.
10. "Reconcile the L2 and L3 readings for the career domain." → expected: D6 `synergy/cross_layer`; layers=['L2','L3']; response surfaces any contradictions.

*semantic / narrative:*
11. "Summarize the remedies available for Ketu-related afflictions in the classical texts." → expected: `query_remedy_corpus` (L0) + `query_classical_texts` (L0); answer attributes every remedy to a text chunk_id; no unattributed statements.
12. "What does the overall dignity profile suggest about the native's capacity for focused intellectual work?" → expected: Whole-Chart-Read path: `query_ucd` (L2 umbrella) → `get_dignity` (L1 drill); answer routes through L2 first (principle B.11); no L1-only direct answer.
13. "Which life-arc phases in L3 show convergence across the dasha, transit, and yoga layers?" → expected: `query_convergence_windows` (L3); multi-layer convergence; each window cites the contributing signals.

*graph:*
14. "Find all signals connected to the Moon node in the CGM within salience > 0.6." → expected: graph traversal with salience filter; returns signal_id list + salience values from `bodha_msr_signals`; no invented nodes.
15. "What cross-domain linkages exist between the 5th-house signals and the 10th-house signals?" → expected: CDLM query path; linkages from `bodha_cgm_edges` or equivalent; `relationship_basis` field cited.

**Calibration items** (human-graded baseline, for judge correlation only, not CI gate):
- 20 additional items where the human rating is intentionally varied (10 clearly correct, 5 partially faithful, 5 unfaithful) to calibrate the LLM judge's scoring distribution.

### §1.2 — Retrieval evaluation (retrieval decomposed from generation)

**Recall@k (the ceiling metric):**
- For each item where the gold context is known (i.e. the human annotator identified which signal_ids / fact_ids are needed), score: was each required signal_id / fact_id retrieved in the top-k result? k=5 for single_shot; k=10 for multi_hop/graph.
- Report recall@5, recall@10, and MRR (mean reciprocal rank) for items with ordered relevance.
- **Floor thresholds (aspirational, not gates — per §N.4 floors-are-aspirational-not-gates):**
  recall@5 ≥ 0.75, recall@10 ≥ 0.85 at full golden set; re-baseline when golden set changes.

**Label-free fallback (for items without explicit gold context):**
- Context precision: fraction of retrieved facts actually referenced in the final answer.
- Context recall (LLM-estimated): does the retrieved context contain sufficient information to answer without hallucination? Scored by the calibrated judge.

**§N.5 violation tracking:**
- Every retrieval that passes through the grounding spine: report `orphan_fact_count` and `has_n5_violations`. A result with N.5 violations is scored 0 for faithfulness regardless of answer quality. CI gate: zero N.5 violations allowed in the golden set on release.

### §1.3 — Generation evaluation (faithfulness / groundedness as headline)

**Atomic claim decomposition protocol:**
1. Parse each model answer into atomic claims (one clause = one verifiable assertion).
2. For each atomic claim, verify it against the retrieved context using the calibrated judge:
   - `supported` — the claim is traceable to a specific fact_id or signal_id in the retrieved context.
   - `contradicted` — the claim contradicts a retrieved fact.
   - `ungrounded` — the claim is not traceable to any retrieved context (true-but-hallucinated).
3. **Faithfulness score** = `supported_claims / (supported + contradicted + ungrounded)`.
4. **CI gate**: faithfulness ≥ 0.85 at the golden-set level (averaged across items). Any single item with faithfulness < 0.50 is flagged for review.

**Grounding compliance (principle #3):**
- Every numeric value in the answer must cite a `fact_id` or `signal_id` (or the governed metric resolver path). An answer that states a number without citation is an automatic faithfulness deduction for that claim.
- The grounding spine's `resolveMetric()` OOV (out-of-vocabulary) errors must appear in the trajectory log and must NOT cause fabrication. Test: send 5 golden queries with a deliberately out-of-vocabulary metric name; expect `OUT_OF_VOCAB` error returned, not a SQL guess.

### §1.4 — Trajectory evaluation (agentic routes)

**Trajectory log fields to score** (from `RouteTrajectory` in `router/types.ts`):
- `route_class` accuracy: does the classifier route to the correct class? (Human-labeled for each golden item.)
- `routing_method` distribution: `rule` vs `model_fallback` — log the split; model fallback should be ≤ 20% of prod traffic.
- `routing_latency_ms`: p50 / p95 / p99. CI alert if p95 > 500ms for single_shot routes.
- `planned_tool_uris`: verify the planned tools match expected tools for the golden item. Score: correct_plan / total_items. Floor: ≥ 0.70.
- `budget_usd`: log actual vs budgeted spend; flag overruns.
- `lel_enabled`: confirm `false` by default in every trajectory (LEL excluded unless explicitly enabled — principle #14).

**Per-step latency (multi_hop routes):**
- For each multi_hop item, record per-tool-call latency and whether the termination policy fired correctly (value-based stop, not hard loop count overrun). A route that loops past the termination budget is a bug.

**Span scoring (agentic loop / adapter routes):**
- For items that exercise `agentic_loop` adapters: score each tool-call span on (a) did the plan include it? (b) was the call necessary? (c) did it contribute to the final answer? Unnecessary tool calls are scored as waste; missing necessary calls as recall failures.

### §1.5 — LLM-as-judge calibration protocol

**Judge model**: use a strong reasoning model (e.g. `claude-opus-4-7` or `claude-sonnet-4-6` via
the ANTHROPIC_PROFILE) as the judge. Do not use the same model tier as the model under evaluation
for the same family (avoid self-evaluation bias).

**Calibration procedure (before any CI gate scoring):**
1. Score the 20-item calibration subset with the LLM judge (faithfulness + retrieval relevance, same protocol as §1.2–§1.3).
2. Score the same 20 items with human annotations (already done as part of §1.1).
3. Compute Pearson r between judge scores and human scores for faithfulness and relevance.
4. **Gate**: r ≥ 0.80 on both axes before the judge is used for CI. If r < 0.80, revise the judge prompt and re-calibrate.
5. Report the r value in the eval run output. Re-calibrate after any judge model change.

**Judge prompt template (concrete — use verbatim in the harness):**
```
You are an evaluator for a Jyotish retrieval system. You are given:
(A) A query.
(B) The retrieved context (a list of facts and signals with their IDs).
(C) The model's answer.

Your tasks:
1. RETRIEVAL RELEVANCE: For each retrieved item, rate 0 (irrelevant), 1 (partially relevant),
   2 (directly relevant). Report as a list.
2. FAITHFULNESS: Decompose the answer into atomic claims. For each claim, classify as:
   'supported' (traceable to a specific retrieved item ID), 'contradicted' (contradicts retrieved
   item), or 'ungrounded' (not traceable to any retrieved item).
   Report each claim with its classification and the supporting item ID (if supported).
3. FINAL SCORE: faithfulness = supported/(supported+contradicted+ungrounded). Report as a float.

Rules:
- A claim that states a numeric value without citing a fact_id or signal_id is 'ungrounded'.
- Do not use domain knowledge to fill in gaps — only what is in the retrieved context counts.
- If you cannot determine relevance or faithfulness, say so explicitly rather than guessing.
Output as JSON matching the schema: {relevance: [{item_id, score}], claims: [{text, class, item_id}], faithfulness_score: float}
```

**Re-baseline trigger**: re-run calibration when the judge model changes, when the golden set
grows by >20 items, or quarterly (whichever comes first).

---

## §2 — Per-model harness execution (4 families — profile hardening)

For each of the 4 LLM families, run the full golden set through the harness and record the
measurements that will upgrade each `[UNMEASURED — D8]` profile parameter to `MEASURED`. The
profiles are in `platform/src/lib/retrieval/maro/profiles.ts` (`PROFILE_VERSION: '1.0.0'`).
After measurement, bump to `1.1.0` and set `PROFILE_STATUS: 'MEASURED'`.

### §2.1 — Anthropic (claude-sonnet-4-6 as mid; claude-haiku-4-5 as worker)

**Model IDs under test**: `claude-sonnet-4-6` (mid), `claude-haiku-4-5` (worker).
**Profile parameters to harden** (currently `[UNMEASURED — D8]`):

| Parameter | Hypothesis | Measurement method |
|---|---|---|
| `tool_result_wire` ordering | results-first user msg | Send 5 tool calls; inspect raw wire format; confirm `tool_result` blocks come first in the content array of the following user message |
| `max_active_tools` sweet spot | ≤ 20 strict; observe granularity preference | Register 10, 15, 20, 25 tools; test selection accuracy at each count; report degradation onset |
| `bundle_strategy` (many_small vs fat_bundle) | many_small for Opus/Sonnet agentic strength | Run 10 multi_hop golden items with bundle of 5 small tools vs 2 consolidated tools; compare recall@10 + latency |
| `structured_output.drift_rate` | 0 in strict mode | Run 50 structured output requests with `json_schema + strict=true`; count schema violations; expected ≈ 0 |
| `context_degradation_onset` | good to 1M | Run needle-in-haystack probes at 50K, 200K, 500K, 800K tokens; report accuracy at each depth |
| `reasoning_round_trip` | thinking+redacted blocks pass unmodified | Send an extended thinking request → tool use → continuation; confirm blocks appear verbatim in round-trip |

**Expected behaviors on golden queries:**
- Query 1 (Mars longitude): routes to `deterministic`; `get_positions` tool called; numeric value cited from `fact_value_num`; Anthropic structured output schema-compliant on first try (drift_rate=0 expected).
- Query 7 (CGM graph traversal): routes to `graph` or `multi_hop`; `traverse_chart_graph` called; tool result delivered as parsed object (not JSON string — `tool_arg_format: 'object'`); no JSON.parse call.
- Query 12 (Whole-Chart-Read): routes through `query_ucd` first (umbrella); then drills to `get_dignity`; extended thinking budget may activate for the synthesis step.
- Caching: the stable [tools+system] prefix should hit cache after the first request in a batch; confirm `cache_read_input_tokens > 0` in the second call's usage block.

**Pass criteria**: faithfulness ≥ 0.87 (highest bar — grammar-constrained strict output means
fabrication should be structurally blocked); recall@5 ≥ 0.78; zero N.5 violations.

### §2.2 — Gemini (gemini-2.5-flash as mid; gemini-2.5-pro for premium graph queries)

**Model IDs under test**: `gemini-2.5-flash` (mid), `gemini-2.5-pro` (premium).
**Profile parameters to harden**:

| Parameter | Hypothesis | Measurement method |
|---|---|---|
| `tool_result_wire` (exact id match) | functionResponse must include exact id from functionCall | Inspect 5 tool calls; verify `functionResponse.id` == `functionCall.id`; test what happens on mismatch (expect silent failure) |
| `max_active_tools` soft cap | 10–20; may reject large/nested schemas | Register 10, 20, 25 tools; note any rejection or schema-parse errors; test deeply nested schemas |
| `bundle_strategy` (fat_bundle) | single large context pull for Pro's 2M window | Run 5 corpus-wide queries with fat bundle (all L1+L2 signals pre-loaded) vs incremental multi_hop; compare quality + cost |
| `structured_output.drift_rate` | unknown ("values may err") | Run 50 structured output requests with `response_schema`; count semantic-value errors (schema-conformant but wrong value); expected > 0 |
| `reasoning_round_trip` (thought signatures) | per-Part, never merge | Send function-calling request; capture thought_signatures; re-send in original Part; confirm no 400/signature error |
| `no_hyphen_names` enforcement | hyphen in server name = rejection | Attempt to register a test MCP server with a hyphen in name; confirm rejection |

**Expected behaviors on golden queries:**
- Query 4 (Saturn aspects in D9): Gemini receives tool args as parsed object (`tool_arg_format: 'object'`); `get_aspects` called with `divisional='D9'`; VALIDATED mode reduces malformed calls.
- Query 10 (career domain L2+L3 reconciliation): Gemini-Pro can load the full L2 MSR bundle + L3 kala data in a single context due to 2M window (`bundle_strategy: 'single_large'`); expected higher recall than other families on wide-context queries.
- Query 14 (CGM graph, salience filter): structured output validates values are semantically correct — MUST validate the salience numbers returned against `bodha_msr_signals.computed_salience` even though schema is valid.
- Tool result wire: `functionResponse` must carry `id` matching the `functionCall`; test harness must verify this at the wire level.
- Caching: use explicit `caches.create` for the system + tools prefix on large batches; verify saved cache handle reduces costs on repeated runs (billed by tokens + storage time).
- MCP transport: Gemini reaches the MCP server via Streamable HTTP (GET /mcp → 405 is expected/correct); confirm no SSE attempt.

**Pass criteria**: faithfulness ≥ 0.82; recall@5 ≥ 0.75 (lower ceiling than Anthropic due to
known value drift); always-validate semantics even on schema-conformant responses; all thought
signatures round-tripped; zero `functionResponse.id` mismatches.

### §2.3 — OpenAI (gpt-4.1 as premium; gpt-4.1-mini as mid)

**Model IDs under test**: `gpt-4.1` (premium), `gpt-4.1-mini` (mid).
**Profile parameters to harden**:

| Parameter | Hypothesis | Measurement method |
|---|---|---|
| `tool_result_wire` (JSON string args) | MUST JSON.parse(arguments) | Send 5 tool calls; confirm `arguments` is a string, not object; parse and validate |
| `max_active_tools` | "keep small"; <20 | Test at 10, 15, 20, 25; measure selection accuracy and first-call correctness |
| `cache_strategy` (automatic) | no code change needed; min 1024 tokens | Send same [tools+system] prefix twice in succession; check `cached_tokens > 0` in second call's usage |
| `structured_output.drift_rate` | 0 with strict=true | Run 50 requests with `strict=true + additionalProperties:false + all-required`; count schema violations |
| `reasoning_round_trip` | reasoning items pass back with tool outputs | Use a reasoning-capable model path; inspect that reasoning items are passed back alongside function_call_output |
| `billing_threshold` effect | extended-context billing above 272K | Profile cost on queries that push context above 272K; confirm billing rate shift |

**Expected behaviors on golden queries:**
- All queries: `normalizeToolArgs()` in MARO must call `JSON.parse(arguments)` — test that the normalizer does this for every OpenAI tool call; a raw string reaching the handler is a bug.
- Query 9 (highest-salience L2 signal): OpenAI strict schema guarantees correct JSON shape for the `query_signals` response; the `refusal` field must be checked (not just content).
- Query 5 (ashtakavarga score): numeric value in answer must cite `fact_id`; strict mode does not prevent fabricated *values* — only schema shape is guaranteed, so faithfulness scoring of the numeric claim still required.
- Tool result format: Responses API `function_call_output{call_id}` vs Chat `role:tool{tool_call_id}` — the harness must test BOTH API paths (Responses and Chat Completions) since the project may use either.
- `allowed_tools` preferred over `tool_choice` (per provider spec) — verify the MARO normalizer uses `allowed_tools` in OpenAI mode to preserve prompt-cache savings.
- NVIDIA NIM: inherits OpenAI profile with `cache_strategy:none` + `streaming_required:true` overrides (via `applyNvidiaOverrides()`). Run 5 golden items on an NVIDIA NIM model to confirm the overrides activate and `cached_tokens` telemetry reports 0.

**Pass criteria**: faithfulness ≥ 0.86 (strict schema blocks structural errors; value fabrication
is the remaining risk); recall@5 ≥ 0.77; `cached_tokens > 0` on 2nd+ call in batch; zero
raw-string tool args reaching handlers.

### §2.4 — DeepSeek (deepseek-chat as worker; deepseek-v4-pro as premium)

**Model IDs under test**: `deepseek-chat` (worker, non-thinking), `deepseek-v4-pro` (premium,
thinking=toggle).
**Profile parameters to harden**:

| Parameter | Hypothesis | Measurement method |
|---|---|---|
| `context_budget.worker` | ~128K floor (UNMEASURED) | Send a 200K-token context to deepseek-chat; confirm whether it errors or truncates; adjust floor if 1M confirmed |
| `structured_output.drift_rate` | 5–12% hypothesis from provider spec | Run 50 `json_object` requests with "json" word + example + max_tokens; count schema/parse violations; report actual rate |
| `validate_and_repair` coverage | MANDATORY — may return empty content | Inject 5 empty-content responses (simulate provider returning `{}`); confirm harness retries and reports |
| `reasoning_content` V4 round-trip | MUST pass back on tool turns (400 otherwise) | Send deepseek-v4-pro tool call; capture `reasoning_content`; re-send; confirm 200 (pass) and then send WITHOUT reasoning_content on next turn; confirm 400 (expected error) |
| `max_active_tools` | 10 (smallest footprint) | Test at 5, 10, 15 tools; report selection accuracy at each count |
| `deprecation_watchpoint` (2026-07-24) | deepseek-chat alias retires | Note in test run if date is within 30 days; emit deprecation warning in harness output |

**Expected behaviors on golden queries:**
- All queries: `normalizeToolArgs()` MUST call `JSON.parse(arguments)` (same as OpenAI); `strip_mcp_constructs: true` — any MCP-specific blocks must be stripped before delivery.
- Query 1 (Mars longitude): `json_object` response; harness validates the JSON parses and contains expected keys; if empty content returned, harness retries (up to 3 times); third failure = item scored as fail.
- Query 6 (contradiction signals): DeepSeek's 5–12% drift means even a schema-conformant response may have wrong signal_ids; faithfulness scoring catches this at the claim level.
- Query 13 (L3 convergence windows): `deepseek-v4-pro` with `thinking=true`; `reasoning_content` must be in the response and MUST be passed back in the next turn of a multi-turn trace; harness verifies the round-trip.
- No MCP path: DeepSeek receives all tools as plain function calls; harness must not send `mcp_servers` parameter; `tool_result_wire: 'role_tool'` confirmed.
- Deprecation alert: if harness date is within 30 days of 2026-07-24, emit `DEPRECATION_WARNING: deepseek-chat and deepseek-reasoner aliases retire 2026-07-24 — migrate to V4 explicit IDs`.

**Pass criteria**: faithfulness ≥ 0.78 (lowest bar — `json_object` drift is the limiting factor);
recall@5 ≥ 0.72; actual drift_rate measured and recorded in profile; zero MCP construct leakage;
`reasoning_content` round-trip verified on V4 tool turns.

### §2.5 — Chart-agnostic compliance (all families, principle #14)

Run a dedicated chart-agnostic gate across all 4 families:

1. **Missing chart_id test**: send 10 queries to `route()` with `chart_id` omitted or empty.
   Expected: all 10 throw `[D2-router] chart_id is required and must not be empty` before any
   tool call. Any family that proceeds without `chart_id` = hard fail.
2. **Native-default contamination probe**: send 10 queries to the OLD MCP tools surface
   (`platform-mcp/src/tools/kala_temporal.ts`, `holistic_bundle.ts`, `l0_brahmagyan.ts`) without
   `chart_id`. Record how many fall back to `NATIVE_CHART_ID`. These must all be remediated before
   the seal; document count as `contamination_count` in eval output.
3. **LEL firewall test**: send `lel_enabled=true` queries and `lel_enabled=false` (default) queries
   on the same item. Confirm that `lel_enabled=false` (default) trajectories contain zero
   `lel_origin`-sourced signals in the grounded result.
4. **Description string scan**: grep all registered capability `description` fields for literal
   `482012f1`, `Abhisek Mohanty`, `native`, `NATIVE_CHART_ID`. Expected: zero hits in
   `platform/src/lib/retrieval/registry/` (confirmed clean by §H audit). Record count from
   `platform-mcp/src/tools/` surface — these must be remediated.

---

## §3 — Governance + debt closure (concrete checklist)

### §3.1 — Model-default discrepancy (gemini vs nim) — resolve before seal

**The bug**: `DEFAULT_STACK_ID='gemini'` in one code path; `CALL_TYPE_ROUTING=STACK_ROUTING['nim']`
in another. These disagree on the effective default by call site (from code validation §C.1.6).

**Resolution steps**:
1. Grep for both `DEFAULT_STACK_ID` and `CALL_TYPE_ROUTING` in `platform/src/lib/models/`.
2. Confirm the intended default with the native (policy is Gemini-primary, DeepSeek-fallback;
   NIM is not the default).
3. Reconcile to a single source of truth: one exported constant `DEFAULT_STACK_ID = 'gemini'`
   consumed by all routing paths.
4. Update the MARO's `resolveFamily()` fallback to match.
5. Confirm in a routing smoke test that an undeclared-family request resolves to `gemini` (not `nim`).
6. Document the resolution in the seal artifact.

### §3.2 — CAPABILITY_MANIFEST registration

**State**: both CAPABILITY_MANIFEST.json copies are stale (stamped 2026-06-05; predate migration
325 + L3–L5 writers + D1–D7 retrieval capabilities). Root copy: 137 entries. Platform copy: 117.
Neither reflects the D-PROFILES, D5–D7 registration, or the mig-325 schema additions.

**Steps**:
1. Regenerate the manifest from the live seed (81 assets) + the D1–D7 capability URIs registered
   in `platform/src/lib/retrieval/registry/`. The regenerated manifest is the authoritative copy.
2. Resolve the two-copy drift: one canonical copy (recommend `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
   as the authoritative root; `platform/` copy auto-generated or symlinked).
3. Register every retrieval primitive as a manifest entry:
   - URI pattern: `marsys://{type}/{layer}/{name}` for all ~61+ registry capabilities.
   - Fields: `canonical_id`, `path` (source file), `version` (`1.0.0`), `status` (`CURRENT`),
     `layer`, `type` (tool/resource/prompt), `wave` (D1–D7 or D-PROFILES).
   - D6 synergy caps: `marsys://tool/synergy/pipeline`, `marsys://tool/synergy/cross_layer`.
   - D7 channel caps: `marsys://tool/channel/mcp_wiring`, `marsys://tool/channel/chat_dispatch`.
   - MARO profile artifact: `RETRIEVAL_MODEL_PROFILES` → update status from `UNMEASURED` to
     `MEASURED` after D8 run; bump version to `1.1.0`.
4. Verify `drift_detector.py` can read the regenerated manifest without errors.

### §3.3 — Schema validator + drift detector coverage for retrieval primitives

**Current coverage gap**: `drift_detector.py` and `schema_validator.py` check the canonical
artifact registry and layer data assets. They do not currently check retrieval capability
registrations (no frontmatter on `.ts` files; no per-primitive version tracking).

**Steps**:
1. Emit a `RETRIEVAL_PRIMITIVES_REGISTRY_v1_0.md` — a lightweight versioned `.md` artifact that
   lists every registered capability URI, its source file, and its `wave`/`version`/`status`. This
   is the surface `drift_detector.py` can check.
2. Add a `schema_validator.py` check: for every URI in the RETRIEVAL_PRIMITIVES_REGISTRY, confirm
   the source file (a) exists, (b) exports a `CapabilityDescriptor` with `required_inputs` declared,
   (c) has no literal native chart_id, (d) has `chart_id` in `required_inputs` for per-chart tools.
3. This check runs in CI alongside the existing schema + drift checks.

### §3.4 — Audience-tier residue in MCP resources

**State**: `platform-mcp/src/resources/house_rules_variants/` had `client.md`, `acharya.md`,
`super_admin.md` variants per §H audit. The code-validation confirmed `server_tier_visibility.test.ts`
is still active. Only `universal.md` remains after the last commit (observed in directory listing —
`client`, `acharya`, `super_admin` variants not present in current source tree).

**Steps**:
1. Confirm `house_rules_variants/` contains ONLY `universal.md` (the no-tier version).
2. Confirm `server_tier_visibility.test.ts` has been retired or repurposed to test the universal
   surface only (not tier-gating logic).
3. Grep `platform-mcp/src/` for `audience_tier`, `signature_tier` (as a serving concept, not data),
   `client_tier`, `super_admin`; any remaining hits = remediation required before seal.
4. Document result in the seal artifact (PASS = zero hits; FAIL = enumerate).

### §3.5 — CI hard gate on the golden set

**Gate specification** (to be implemented as a CI step, e.g. GitHub Actions / Cloud Build job):

```yaml
# ci_eval_gate.yml (pseudocode — implement in actual CI framework)
name: Retrieval Eval Gate
trigger: [push to main, PR to main]
steps:
  - run: npx tsx platform/src/lib/retrieval/__eval__/run_golden_set.ts
    env:
      GOLDEN_SET_PATH: platform/src/lib/retrieval/__eval__/golden_set.json
      JUDGE_MODEL: claude-sonnet-4-6
      CHART_IDS: "482012f1-710e-4a25-994a-93821f5871aa,<synthetic_chart_2>,<synthetic_chart_3>"
      N5_VIOLATIONS_ALLOWED: 0
    assert:
      faithfulness_score: ">= 0.85"
      recall_at_5: ">= 0.75"
      chart_agnostic_gate: "PASS"      # zero missing-chart_id passthrough
      contamination_count: 0           # zero native defaults in registry layer
      judge_human_correlation: ">= 0.80"  # must be pre-calibrated
```

**Rolling-window faithfulness alert** (production sampling):
- Sample 5% of live production queries (anonymized; no native-specific data in the log).
- Run the faithfulness scorer (LLM judge) on each sample asynchronously.
- Alert if rolling 7-day faithfulness on sampled prod drops below 0.80 (below the CI gate floor
  is a signal that prod is drifting from the golden set).
- Implement as a Cloud Scheduler job writing to a monitoring table; alert via existing notification
  channel.

---

## §4 — Seal (concrete checklist)

### §4.1 — Red-team pass (required before seal per §M cadence)

The retrieval system close is a macro-phase close trigger. The red-team pass must cover:

1. **Principle audit (all 14)** — for each principle in RETRIEVAL_SYSTEM_DESIGN_APPROACH §6,
   document whether it is satisfied end-to-end, with evidence (code file:line or test name):

   | # | Principle | Evidence | Status |
   |---|---|---|---|
   | 1 | Route, don't choose | `router/router.ts` — `route()` is the top-level arch | VERIFY |
   | 2 | Failure mode > raw accuracy | `router.ts` throws on missing chart_id; grounding returns `EMPTY` not invented | VERIFY |
   | 3 | Numbers cited from deterministic source | `grounding/resolver.ts resolveMetric()` OOV returns error; `fact_value_num` from `chart_facts` | VERIFY |
   | 4 | Graph edges + cheap traversal | `traverse_chart_graph.ts` (L2); `register_d4_graph.ts` wired | VERIFY |
   | 5 | Hybrid retrieval baseline | `query_classical_texts` (L0) + dense path in L2 — confirm BM25+RRF implemented | VERIFY |
   | 6 | Pre-render relational bundles | `query_ucd.ts` (L2 umbrella) + pre-rendered `vw_chart_digest` view | VERIFY |
   | 7 | Primitives once as MCP, consumed cross-model | `mcp_capability_bridge.ts`; server.ts wires 13; MARO shapes surface | VERIFY |
   | 8 | Shared MARO, not per-channel logic | `maro/index.ts` exports `orchestrate()` + `getMcpSurface()` for both channels | VERIFY |
   | 9 | Never trust raw model JSON | `validateAndRepair()` in MARO; DeepSeek mandatory; all families validate values | VERIFY |
   | 10 | Eval harness gates seal | This brief; CI gate spec in §3.5 | VERIFY |
   | 11 | Behavioral profiles — evidence-based + living | `profiles.ts` PROFILE_VERSION `1.0.0`; UNMEASURED → MEASURED after D8 | VERIFY |
   | 12 | LLM-facing design from authoritative docs | `RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md` v1.0 (cited) | VERIFY |
   | 13 | Tool topology is an astrological question | `query_ucd` umbrella → drill tools; topology derived per D-GROUNDTRUTH | VERIFY |
   | 14 | Chart-agnostic, zero native contamination | `chart_agnostic_gate.ts`; `route()` throws on empty chart_id; contamination_count=0 required | VERIFY |

2. **F1 dedup gate** (cited in §4 acceptance criteria): every retrieval result de-dups before DB
   fetch. Evidence: `resolver.ts` line `const uniqueSignalIds = [...new Set(signal_ids)]` and
   `const allFactIds = new Set<FactId>()`. Verify the same pattern in L2/L3/L4/L5 layer handlers.

3. **Anti-patterns scan**:
   - No `?? NATIVE_CHART_ID` or `.default(NATIVE)` in `platform/src/lib/retrieval/` (must be clean).
   - No `audience_tier` in `platform/src/lib/retrieval/` or `platform-mcp/src/resources/`.
   - No `gemini-2.0-flash-lite` or deprecated model IDs in active routing paths.
   - No `deepseek-v4-flash` as an API model ID (rejects toolChoice).
   - The `lel_enabled` default is `false` in `router.ts` (confirmed: `const lel_enabled = hints.lel_enabled ?? false`).

4. **D7 chat migration status**: the `channel_chat_dispatch` descriptor confirms the chat route is
   PENDING migration (`lib/retrieve` still active). The red-team must confirm this is an ACCEPTED
   open item (not a blocking bug) and document it as a known residual in the seal artifact with a
   follow-on brief reference.

### §4.2 — D-PROFILES: values hardened from UNMEASURED to MEASURED

After the per-family harness runs in §2:

1. For each `[UNMEASURED — D8]` parameter in `platform/src/lib/retrieval/maro/profiles.ts`:
   fill in the measured value from the harness output.
2. Bump `PROFILE_VERSION` from `'1.0.0'` to `'1.1.0'`.
3. Set `PROFILE_STATUS` from `'UNMEASURED'` to `'MEASURED'`.
4. Update `RETRIEVAL_MODEL_PROFILES_v1_0.md` with the measured values; version bump to `1.1.0`
   in the frontmatter; add changelog entry `v1.1.0 (YYYY-MM-DD): D8 measurement pass — values
   hardened from provider-spec hypotheses to MARSYS-corpus measurements.`
5. Re-commit both the `.ts` profile file and the `.md` artifact (they must stay in sync).

### §4.3 — Seal artifact

Emit `RETRIEVAL_SYSTEM_DESIGN_SEAL_v1_0.md` (new file in `00_ARCHITECTURE/`) with:

```markdown
---
canonical_id: RETRIEVAL_SYSTEM_DESIGN_SEAL
version: 1.0
status: SEALED
sealed_date: [date]
sealed_by: [session id]
---
# RETRIEVAL SYSTEM DESIGN SEAL v1.0

## Summary
- D0–D8 + D-PROFILES waves complete.
- ~61+ retrieval capabilities registered across L0–L5.
- 4 LLM family profiles: MEASURED (values hardened by D8 harness on MARSYS corpus).
- Eval gate: faithfulness ≥ 0.85 / recall@5 ≥ 0.75 / N.5 violations = 0 / chart-agnostic PASS.
- Judge–human correlation: r = [measured value].
- Governance: manifest regenerated; drift/schema coverage added; tier residue cleared;
  model-default discrepancy resolved (DEFAULT_STACK_ID='gemini' canonical).
- Red-team pass: all 14 principles verified. Known residual: chat route migration PENDING
  (tracked as [follow-on brief reference]).

## Open items (not blocking seal)
- Chat route migration from lib/retrieve → retrieval registry (D7 follow-on).
- Runtime data-plane validation (L3–L5 writer population, bo_samskara embeddings, live
  count_sql correctness) — deferred per §C.4 governance (prod-only session required).
- DeepSeek alias retirement (2026-07-24) — watchpoint set in DEPRECATION_WATCHLIST.

## Principles satisfied
[paste principle audit table from §4.1 with PASS/FAIL per row]
```

### §4.4 — CURRENT_STATE + campaign tracker updates

1. Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2: mark retrieval system design campaign
   SEALED; point at `RETRIEVAL_SYSTEM_DESIGN_SEAL_v1_0.md`.
2. If a `RETRIEVAL_SYSTEM_DESIGN_CAMPAIGN` tracker artifact exists, mark it COMPLETE.
3. SESSION_LOG.md entry: record the D8 session close with the seal artifact reference and the
   measured eval scores.

---

## §5 (new) — Resolved marker summary

The following `[resolved from …]` markers in v1.0 have been filled:

| Marker | v1.0 placeholder | v1.1 resolution |
|---|---|---|
| Golden set + thresholds | "resolved in-wave"; "calibrate against 50–200 human-rated items" | 100-item target; 3-chart minimum; 5 route classes; human annotation protocol; κ ≥ 0.70; judge r ≥ 0.80; faithfulness ≥ 0.85 CI gate (§1.1) |
| Specific queries | absent | 15 named golden queries with expected tool path and faithfulness criterion (§1.1) |
| Per-model expected behaviors | "run the harness across Anthropic/Gemini/OpenAI/DeepSeek" | Concrete per-model behavior table for each of 4 families; specific tool wire-format tests; deprecation watch (§2.1–§2.4) |
| UNMEASURED parameter list | "context-degradation curve, output-drift, bundle sweet spot" | Full table per family: which parameter, what hypothesis, what measurement method (§2.1–§2.4) |
| Governance: model-default discrepancy | "Reconcile the gemini-vs-nim model-default discrepancy (deferred from DG4)" | Concrete 5-step resolution + smoke test spec (§3.1) |
| Governance: manifest registration | "register retrieval primitives in CAPABILITY_MANIFEST" | Full spec: regenerate from seed+registry; resolve two-copy drift; register ~61+ URIs with required fields (§3.2) |
| Governance: drift/schema coverage | "wire drift_detector/schema_validator coverage" | RETRIEVAL_PRIMITIVES_REGISTRY_v1_0.md artifact + schema_validator check spec (§3.3) |
| Governance: audience-tier residue | implicit (from DG4 mention) | Explicit grep + confirm steps; document PASS/FAIL in seal (§3.4) |
| CI hard gate spec | "CI hard gate on the golden set" | YAML pseudocode with asserts; rolling-window prod sampling spec (§3.5) |
| Red-team pass scope | "Red-team pass (macro-phase-close cadence requires it before seal)" | 14-principle audit table + F1 dedup gate + anti-patterns scan + D7 chat migration status (§4.1) |
| Seal artifact content | "Emit the seal artifact" | Full seal artifact template with required sections (§4.3) |
| CURRENT_STATE update | "update CURRENT_STATE + the campaign tracker" | Specific file + section updates (§4.4) |
| Chart-agnostic eval gate | "Eval is chart-agnostic (multiple charts); no native-only evaluation" | 3-chart minimum; native items marked `native_only:true` and excluded from CI gate score; dedicated chart-agnostic compliance test block (§2.5) |

*End of CLAUDECODE_BRIEF_RETRIEVAL_D8_EVAL_SEAL v1.1 (resolved, 2026-06-28).*
*Resolves v1.0 parameterized shell. All [resolved from …] markers filled.*
*Source: D1–D7 built system + D-PROFILES profiles.ts + PROVIDER_SPEC + CODE_VALIDATION + DESIGN_APPROACH §6.*
