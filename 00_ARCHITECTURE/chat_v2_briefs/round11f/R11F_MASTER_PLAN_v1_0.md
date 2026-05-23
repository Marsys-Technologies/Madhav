---
artifact: R11F_MASTER_PLAN_v1_0.md
canonical_id: CHAT_V2_R11F_MASTER_PLAN
version: 1.0
status: CURRENT
authored: 2026-05-23
owners: marsys+claude
mirror_pair: none
branch: chat-v2/r11f-agentic-loop
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11FBound
precursor_arc: feature/r11f-wiring-arc (S1–S7 — must merge before this arc opens)
queue_path: 00_ARCHITECTURE/CONDUCTOR/r11f/session_queue.yaml
---

# R11.F — Bounded Agentic Loop Activation (Multi-Provider)

## §1 — Mission

Make the multi-provider agentic tool loop operational in production. The R11.A–E arc
(PRs #143–#147, merged 2026-05-22) and the R11.F wiring arc (`feature/r11f-wiring-arc`,
S1–S7) together deliver the structural scaffold: `runAgenticLoop()` engine, per-provider
tool-event emission, and route.ts dispatch wiring. What they do NOT deliver is:

- Tools forwarded from the retrieval registry into the adapter `chat()` API request (the
  model never sees tool definitions; it cannot call tools).
- B.11 Whole-Chart-Read floor executed deterministically before the loop starts.
- onFinish parity (context_assembly_log, prediction candidates, conversation_messages
  persistence) for the adapter-dispatch code path.
- End-to-end integration tests that exercise the actual adapter → SDK → tool-call round-trip.
- Visual smoke verification per provider.
- Red-team adversarial coverage.

This arc closes all of those gaps across all five providers (Anthropic, Google, OpenAI,
DeepSeek, NVIDIA) and gates production activation behind passing smoke + red-team.

## §2 — Confirmed Findings (pre-arc audit, 2026-05-23)

| ID | Location | Description |
|---|---|---|
| B1 | `route.ts:946` | `tools: []` stub — tool catalogue never populated; `convertRetrievalToolToChatTool` helper does not exist |
| B2 | `anthropic/adapter.ts chat()` | `streamParams` omits `tools` and `toolChoice` — model receives no tool definitions despite adapter emitting tool stream events |
| B2-G | `google/adapter.ts chat()` | Same shape as B2 — Gemini format requires `tools: [{ functionDeclarations: [...] }]` |
| B2-O | `openai/adapter.ts chat()` | Same shape as B2 — OpenAI format requires `tools: [{ type:'function', function:{...} }]` |
| B2-D | `deepseek/adapter.ts chat()` | OpenAI-compat; tool event emission added in S2 but forwarding not confirmed |
| B2-N | `nvidia/adapter.ts chat()` | Same as B2-D |
| B3 | `route.ts ~1082` | Adapter branch returns via `createUIMessageStreamResponse()` without onFinish — skips context_assembly_log, prediction candidates, conversation_messages persistence |
| B4 | All providers | No E2E integration test exercises the full adapter→SDK→tool_call→executor→second-iteration round-trip |
| B5 | All providers | `R11E_*_LOOP` flags default `false` in `feature_flags.ts`; absent from `deploy.yml` |

**The engine itself (`agentic_loop.ts`, `mcp_tool_executor.ts`) is real.** 33 tests pass
against it. Every test uses `makeMockAdapter()`; zero tests cover the adapter → SDK seam.

## §3 — Architectural Decision: Bounded Loop

The user has accepted that `/consume` must NOT become a free-running agentic loop:

- **B.11 Whole-Chart-Read floor is non-negotiable.** MSR, UCN, CGM are pre-executed
  deterministically before any model call, regardless of what the model would choose.
  The loop adds gap-recovery and ambiguity-resolution capability AFTER the floor is met.
- **Plan-and-execute structure is preserved.** The planner still runs first; the planner's
  authorised tool subset constrains what the loop may call. The loop does not replace the
  planner.
- **The existing `MAX_ITERATIONS = 8` cap is binding.** No session in this arc raises it.
- **Rollback is a flag flip.** Setting any `R11E_<PROVIDER>_LOOP` flag to `false` in Cloud
  Run returns that provider's path to the existing plan-and-execute behaviour instantly.
  No code change required.

Contract implemented in Phase A session A-S3:
```
BEFORE LOOP:
  1. Run B.11 floor tools deterministically (existing pre-execution path, unchanged)
  2. Hydrate context with floor results
ENTER LOOP (only after floor completes):
  3. Provide planner-authorised subset of tools to the model
  4. Run up to MAX_ITERATIONS iterations of: model call → tool dispatch → result injection
  5. Model signals end-of-turn → exit loop
  6. Run onFinish path (context_assembly_log, prediction candidates, persistence)
```

## §4 — Acceptance Criteria

For each of the five providers, the arc is not done until ALL of the following pass:

| # | Criterion | Tested by |
|---|---|---|
| AC.a | Tool definitions reach the AI SDK in the API request (not empty array) | Spy test on `streamText`/`generateText` |
| AC.b | A tool_use round-trip succeeds: model calls tool → executor runs → result injected → second iteration produces text | E2E integration test |
| AC.c | B.11 floor (MSR/UCN/CGM) appears in context regardless of model behaviour | Integration test assertion |
| AC.d | onFinish path writes context_assembly_log row, detects prediction candidates, persists conversation_messages | Assertion test comparing adapter and legacy paths |
| AC.e | `query_trace_steps` rows contain tool_use iteration rows with `tool_name`, `iteration`, `duration_ms`, `cache_hit` | Trace audit test |
| AC.f | `R11E_<PROVIDER>_LOOP=true` added to `deploy.yml` env_vars block | grep check on deploy.yml |
| AC.g | Visual smoke: provider-specific query ("when is my next Saturn mahadasha?") shows tool-flow timeline rows in the UI | Screenshot saved to `visual_evidence/<provider>/` |
| AC.h | Red-team: adversarial prompts cannot skip B.11 floor, cannot exceed iteration cap, cannot hallucinate tool results without citation mismatch | R11F-C-S2 red-team PASS |

## §5 — Session Topology

**Precondition:** `feature/r11f-wiring-arc` (S1–S7) must be merged to main before any
session in this arc commits to production paths. Sessions A-S1 and A-S2 can be authored
in the worktree concurrently with S5–S7 execution, but must not be pushed to the feature
branch until the precursor arc lands on main.

### Phase A — Anthropic Foundation (serial; must complete before Phase B)

| Session | Title | Parallel-safe | Depends on |
|---|---|---|---|
| R11F-A-S1 | Anthropic adapter: forward `tools`+`toolChoice` to `streamText` | No | precursor merged |
| R11F-A-S2 | Route.ts: `convertRetrievalToolToChatTool` helper + replace `tools:[]` | No | A-S1 |
| R11F-A-S3 | B.11 floor pre-execution preservation + onFinish parity | No | A-S2 |
| R11F-A-S4 | Anthropic E2E integration test (VCR/spied `streamText`) | No | A-S3 |
| R11F-A-S5 | Anthropic visual smoke via Chrome MCP | No | A-S4 |

### Phase B — Other Providers (B1/B3 can run parallel; B5 waits for B1-B4)

| Session | Title | Parallel-safe | Depends on |
|---|---|---|---|
| R11F-B-S1 | Google adapter: forward tools in Gemini format + integration test | Yes (with B-S3) | A-S2 |
| R11F-B-S2 | Google visual smoke via Chrome MCP | No | B-S1 |
| R11F-B-S3 | OpenAI adapter: forward tools in OpenAI format + integration test | Yes (with B-S1) | A-S2 |
| R11F-B-S4 | OpenAI visual smoke via Chrome MCP | No | B-S3 |
| R11F-B-S5 | DeepSeek + NVIDIA: verify/fix forwarding + combined smoke | No | B-S1,B-S3 done |

### Phase C — Cross-Cutting (mostly serial)

| Session | Title | Parallel-safe | Depends on |
|---|---|---|---|
| R11F-C-S1 | Cross-provider parity matrix + trace audit suite | No | All B sessions |
| R11F-C-S2 | Iteration-cap stress + red-team adversarial pass | No | C-S1 |
| R11F-C-S3 | deploy.yml flag flips for all five R11E loop flags | No | C-S2 PASS |
| R11F-C-S4 | Visual regression sweep (all 5 providers) + sealing artifact + open PR | No | C-S3 |

**Total: 14 sessions** across 3 phases. One PR opened at C-S4; HALT for native merge approval
(do not auto-merge — this is the live chat production path).

## §6 — Flag Taxonomy

| Flag | Default pre-arc | Default post-arc | Type | deploy.yml |
|---|---|---|---|---|
| `MARSYS_FLAG_R11E_ANTHROPIC_LOOP` | false | true | server-side | yes |
| `MARSYS_FLAG_R11E_GEMINI_LOOP` | false | true | server-side | yes |
| `MARSYS_FLAG_R11E_OPENAI_LOOP` | false | true | server-side | yes |
| `MARSYS_FLAG_R11E_DEEPSEEK_LOOP` | false | true | server-side | yes |
| `MARSYS_FLAG_R11E_NVIDIA_LOOP` | false | true or N/A* | server-side | yes if supported |

*NVIDIA: if the chosen NIM model does not support function calling, mark flag N/A in
`feature_flags.ts` comment; document limitation in sealing artifact; do NOT add to
`deploy.yml`. Per B-S5 outcome.

## §7 — Rollback Path

Any `R11E_<PROVIDER>_LOOP` flag set to `false` in Cloud Run env-vars restores plan-and-execute
behaviour for that provider instantly, with no code change required. Rollback procedure:

```bash
# example: roll back Anthropic loop
gcloud run services update amjis-web \
  --region asia-south1 \
  --update-env-vars MARSYS_FLAG_R11E_ANTHROPIC_LOOP=false
```

The existing plan-and-execute code path (non-adapter branch) is not touched in this arc.
The adapter branch retains its current flag-off behaviour as the fallback.

## §8 — Out of Scope (R11.G+ territory)

The following are explicitly NOT part of this arc:

- Parallel tool calls (multiple tools in a single model response)
- Structured tool outputs (JSON-schema-validated outputs)
- Built-in tools (web search, code execution) — these are provider-specific and not in the
  MARSYS retrieval registry
- Streaming tool results back to the UI mid-iteration (current: tool steps appear after
  loop completion in the tool-flow timeline)
- Anthropic extended thinking interleaved with tool calls across iterations
- DeepSeek R1 thinking-block + tool-call interleaving edge cases (document only; full fix is
  R11.G)

---
*R11F_MASTER_PLAN_v1_0.md — authored 2026-05-23 — 14 sessions across 3 phases*
