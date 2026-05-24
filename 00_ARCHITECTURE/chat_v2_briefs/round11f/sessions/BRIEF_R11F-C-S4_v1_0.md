---
artifact: BRIEF_R11F-C-S4_v1_0.md
session_id: R11F-C-S4
version: 1.0
phase: C
parallel_safety: false
depends_on: [R11F-C-S3]
estimated_loc_delta: +50  (sealing artifact + governance docs)
---

# R11F-C-S4 — Visual Regression Sweep + Sealing Artifact + Open PR

## Scope

Final session. Three sub-tasks:

1. **Visual regression sweep**: all supported providers, three canonical queries each.
   Saves screenshots to `visual_evidence/final/<provider>/`.
2. **Sealing artifact**: `STREAM_R11F_BOUND_COMPLETE.md` documenting all AC items,
   red-team result, NVIDIA outcome, and post-merge operator steps.
3. **Open PR**: one PR from `chat-v2/r11f-agentic-loop` → `main`. HALT for native
   merge approval — do NOT auto-merge.

## Files May Touch

```
00_ARCHITECTURE/chat_v2_briefs/round11f/STREAM_R11F_BOUND_COMPLETE.md  (new)
00_ARCHITECTURE/chat_v2_briefs/round11f/visual_evidence/final/         (screenshots)
```

No production code changes in this session.

## Part 1 — Visual Regression Sweep

### Canonical queries

Run each query for each supported provider (skip NVIDIA if N/A):

| # | Query | Tool expected |
|---|---|---|
| Q1 | "When does my next Saturn mahadasha start?" | query_dasha_periods |
| Q2 | "What is the current planetary disposition for Rahu and Ketu?" | query_ephemeris |
| Q3 | "Summarise my holistic astrological profile for the next 6 months." | holistic_bundle |

### Procedure

For each `(provider, query)` pair:
1. Navigate to `/consume` with provider selected.
2. Send query.
3. Wait for streaming completion (up to 90 seconds).
4. Screenshot response + tool-flow timeline.
5. Save to `visual_evidence/final/<provider>/Q<n>_response.png` and `Q<n>_tool_flow.png`.

If a provider returns an error for any query: note in sealing artifact as KNOWN_LIMITATION;
do NOT halt.

### Evidence count

- 3 providers × 3 queries × 2 screenshots = 18+ screenshots minimum (more for NVIDIA if Case A).

## Part 2 — Sealing Artifact

Create `00_ARCHITECTURE/chat_v2_briefs/round11f/STREAM_R11F_BOUND_COMPLETE.md`:

```markdown
---
artifact: STREAM_R11F_BOUND_COMPLETE.md
version: 1.0
status: COMPLETE
sealed: <date>
---

# R11.F Bounded Loop Arc — Completion Seal

## AC Summary

| AC | Description | Result |
|---|---|---|
| AC.a | Tools forwarded to SDK (all providers) | PASS |
| AC.b | tool_use round-trip (E2E tests) | PASS — <N> tests |
| AC.c | B.11 floor in context | PASS |
| AC.d | onFinish parity | PASS |
| AC.e | trace_writer iteration rows | PASS |
| AC.f | deploy.yml flags added | PASS |
| AC.g | Visual smoke per provider | PASS (screenshots in visual_evidence/) |
| AC.h | Red-team IS.8(b) | PASS — RT.1/RT.2/RT.3 all PASS |

## NVIDIA Outcome

<State Case A or B from B-S5>

## DeepSeek R1 Limitation

<Summarise thinking-block + tool-call interleaving finding from B-S5>

## Post-Merge Operator Steps

1. Verify Cloud Build deploys from main after PR merge.
2. Confirm R11E flags are live in Cloud Run:
   ```bash
   gcloud run services describe amjis-web --region asia-south1 \
     --format='value(spec.template.spec.containers[0].env)'
   ```
3. Send 1 test query per provider from the UI; confirm tool-flow timeline appears.
4. Monitor error logs for 10 minutes:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
     --project=<project-id> --freshness=10m
   ```

## Out-of-Scope (R11.G+)

- Parallel tool calls
- Structured tool outputs
- DeepSeek R1 reasoning+tools interleaving (full fix)
- Built-in tools (web search, code execution)
- Streaming tool results mid-iteration to UI
```

## Part 3 — Open PR

```bash
git push -u origin chat-v2/r11f-agentic-loop

gh pr create \
  --title "feat(r11f): bounded agentic loop activation — all providers, B.11 floor, onFinish parity" \
  --body "$(cat <<'EOF'
## Summary

Activates the multi-provider agentic tool loop that was structurally wired in the
R11.A–E arc and the R11.F wiring arc but was operationally inert due to three breaks:
- B1: route.ts passed tools:[] to adapter (stub never replaced)
- B2: adapter chat() omitted tools from streamText() call (model never saw definitions)
- B3: adapter dispatch path skipped onFinish (no persistence/prediction/log writes)

This arc closes all three breaks across Anthropic, Google, OpenAI, DeepSeek, and NVIDIA
(NVIDIA: see sealing artifact §NVIDIA Outcome). Adds B.11 floor preservation contract,
14 new test files, visual smoke evidence, and IS.8(b) red-team PASS.

## Acceptance

All 8 AC items PASS. See STREAM_R11F_BOUND_COMPLETE.md.

## Test plan

- [ ] Full vitest: 0 failures
- [ ] E2E loop round-trip tests: 3 pass per provider
- [ ] Red-team IS.8(b): RT.1/RT.2/RT.3 PASS
- [ ] Visual smoke: screenshots in visual_evidence/
- [ ] Post-merge: operator verifies flags live + 1 test query per provider

## Rollback

Set any `R11E_<PROVIDER>_LOOP=false` in Cloud Run env-vars to instantly revert that
provider to plan-and-execute behaviour.

🤖 Generated with Claude Code
EOF
)"
```

**HALT** after PR is created. Do NOT merge. Wait for native approval.

## Acceptance Tests

```bash
# AC: PR URL returned
gh pr list --head chat-v2/r11f-agentic-loop --json url --jq '.[0].url'
# expected: a valid GitHub PR URL

# AC: full vitest one final time
cd platform && npx vitest run --no-coverage 2>&1 | tail -5
# expected: 0 failures
```

## Deliverable Artifacts

- `STREAM_R11F_BOUND_COMPLETE.md` (new)
- `visual_evidence/final/**` (screenshots)
- Open PR on GitHub (URL printed at session close)
- Commit: `docs(r11f-c-s4): sealing artifact + visual regression evidence`

## HALT Protocol

```
HALT_R11F-C-S4: PR OPENED — NATIVE MERGE REQUIRED
PR URL: <url>
All 14 sessions complete. All AC items PASS.
Waiting for native review and merge approval.
```
