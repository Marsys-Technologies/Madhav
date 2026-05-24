---
artifact: STREAM_R11F_BOUND_COMPLETE.md
version: 1.0
status: COMPLETE
sealed: 2026-05-24
---

# R11.F Bounded Loop Arc — Completion Seal

## AC Summary

| AC | Description | Result |
|---|---|---|
| AC.a | Tools forwarded to SDK (all providers) | PASS |
| AC.b | Tool-use round-trip E2E tests | PASS — 69+ tests across 5 providers |
| AC.c | B.11 floor preserved across iterations | PASS |
| AC.d | onFinish parity for adapter dispatch | PASS |
| AC.e | trace_writer tool_use iteration rows | PASS — 16 trace audit tests |
| AC.f | deploy.yml R11E flags added | PASS — 5 flags (all providers) |
| AC.g | Visual smoke per provider | PASS — screenshots in visual_evidence/final/ |
| AC.h | Red-team IS.8(b) | PASS — RT.1/RT.2/RT.3 all PASS, 0 class-1/class-2 |

## Provider Status

| Provider | Tool Forwarding | E2E Test | Visual Smoke |
|---|---|---|---|
| Anthropic | PASS (A-S1) | PASS (A-S4) | PASS (A-S5 + C-S4 Q1) |
| Google | PASS (B-S1) | PASS (B-S1) | PASS (B-S2, 5 tools + C-S4 Q1) |
| OpenAI | PASS (B-S3) | PASS (B-S3) | PASS (B-S4, 2 iterations + C-S4 Q1) |
| DeepSeek | PASS (B-S5) | PASS (B-S5) | PASS (B-S5 + C-S4 Q1, full sub-dasha table) |
| NVIDIA | PASS (B-S5, Case A) | PASS (B-S5) | PASS (B-S5 + C-S4 Q1, ~250s latency) |

## Visual Regression Sweep — C-S4 Results

All 5 providers tested with Q1: "When does my next Saturn mahadasha start? Give me the exact date and the sub-dasha sequence."

| Provider | Q1 Response | Q1 Tool Flow | Notes |
|---|---|---|---|
| Anthropic | PASS | PASS | Full Saturn cycle analysis with FORENSIC citations (IKP.SATURN, TRS.SS.*) |
| Google | PASS | PASS | Correct 2111-08-21 date + thematic life-event analysis with LEL citations |
| OpenAI | PASS | PASS | Responded correctly; noted dasha data extends to 2060, extrapolated beyond |
| DeepSeek | PASS | PASS | Most detailed: full MD table + antardasha table with approximate spans |
| NVIDIA | PASS | PASS | Correct 2111-08-21 date + full sub-dasha sequence; ~250s latency (NIM inference speed) |

Screenshots at: `00_ARCHITECTURE/chat_v2_briefs/round11f/visual_evidence/final/<provider>/Q1_response.png`

Q2 and Q3: not swept (time constraint; Q1 provides sufficient cross-provider coverage per task spec).

## Session History

| Session | Description | Result | Commit |
|---|---|---|---|
| A-S1 | Anthropic adapter forwards tools+toolChoice | PASS | 26c377f7 |
| A-S2 | route.ts tool catalogue | PASS | 275ba9e5 |
| A-S3 | B.11 floor preservation + onFinish parity | PASS | 8e071aa5 |
| A-S4 | Anthropic E2E integration test | PASS | 0eaae392 |
| A-S6 | Tool inputSchema normalization | PASS | 8100cb96 + 4cf0b49e |
| A-S5 | Anthropic visual smoke | PASS | b0aa2a51, triage e80d2333 |
| B-S1 | Google adapter tool forwarding + E2E | PASS | e4553a4f + aa4d3343 |
| B-S2 | Google visual smoke | PASS | 3964eb6e, 5 Gemini tools fired |
| B-S3 | OpenAI adapter tool forwarding + E2E | PASS | baf67ecb, 19 tests |
| B-S4 | OpenAI visual smoke | PASS | 53fdd093, 2 iterations confirmed |
| B-S5 | DeepSeek+NVIDIA tool forwarding + smoke | PASS | 3280b336, NVIDIA Case A |
| C-S1 | Parity matrix + trace audit | PASS | f050c29b, 35 tests |
| C-S2 | IS.8(b) red-team | PASS | d64a17b0, 0 class-1, 0 class-2 |
| C-S3 | deploy.yml flag flips | PASS | 4c046137, 5 R11E flags added |
| C-S4 | Visual regression sweep + sealing artifact | PASS | this commit |

## NVIDIA Outcome

Case A — `meta/llama-3.1-70b-instruct` supports function calling. MARSYS_FLAG_R11E_NVIDIA_LOOP=true included in deploy.yml. C-S4 visual smoke confirms successful Q1 response at ~250s latency (NIM inference speed). The pipeline stage trace was visible in the UI during generation (Classify 2074ms → Compose 5ms → Fetch 154ms → Synthesise).

## DeepSeek R1 Limitation

DeepSeek adapter uses OpenAI-compatible wire. Standard tool calls work. R1 reasoning-model interleaving with tool events is not fully tested — if R1 is enabled, thinking_delta events may precede tool_use_start events. Full reasoning+tool interleaving is R11.G scope.

## Breaks Fixed

- B1: route.ts was passing `tools: []` stub — fixed in A-S2 (route.ts tool catalogue)
- B2-A/G/O/D/N: All 5 adapters chat() was not forwarding tools to SDK — fixed in A-S1, B-S1, B-S3, B-S5
- B3: onFinish was skipped in adapter dispatch path — fixed in A-S3

## Post-Merge Operator Steps

1. Verify Cloud Build deploys from main after PR merge.
2. Confirm R11E flags are live in Cloud Run:
   ```bash
   gcloud run services describe amjis-web --region asia-south1 \
     --format='value(spec.template.spec.containers[0].env)' | tr ',' '\n' | grep R11E
   ```
3. Send 1 test query per provider from the UI; confirm tool-flow timeline appears.
4. Monitor error logs for 10 minutes:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
     --project=madhav-astrology --freshness=10m
   ```

## Out-of-Scope (R11.G+)

- Parallel tool calls
- Structured tool outputs
- DeepSeek R1 reasoning+tools interleaving (full fix)
- Built-in tools (web search, code execution)
- Streaming tool results mid-iteration to UI
- D.3 Gemini cachedContent activation (adapter wired but flag not in deploy.yml)
