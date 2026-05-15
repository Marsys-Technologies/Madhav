---
status: OPEN
session_id: PIV_QG_1
phase: QG.1
phase_name: "AIOps Control Panel → runtime_config → adapter integration"
next_session: PIV_QG_2
authored_at: 2026-05-14
authored_by: PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — PIV_QG_1
## Portal Integration Validation, Step 1 — Config → Runtime

---

## §0 — Executor orientation

QG.1 validates the Phase 1 ↔ Phase 2 seam: does an AIOps Control Panel
config change actually change the model that runs the next query?

Tests are live but cheap. Per-request override headers (`x-aiops-stack`,
`x-aiops-model-...`) eliminate the need to persistently mutate
production state. The cheapest model per stack (per master plan §3) runs
the canonical query that proves the override took effect.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/portal_validation/PORTAL_INVENTORY.md (QG.0 deliverable)
3. 00_ARCHITECTURE/portal_validation/PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0.md §3 (cost model)
4. platform/src/lib/models/runtime_config.ts (priority chain)
5. platform/src/lib/models/registry.ts (STACK_ROUTING, MODELS, quirks)
6. platform/src/lib/adapters/dispatcher.ts
7. platform/src/app/api/admin/aiops/state/route.ts
8. platform/src/app/api/admin/aiops/stack/route.ts
9. platform/src/app/api/admin/aiops/routing/[stack]/[call_type]/route.ts
10. platform/src/app/api/chat/consume/route.ts (the actual consumer)
```

---

## §2 — Scope

### may_touch
```
00_ARCHITECTURE/portal_validation/QG1_CONFIG_RUNTIME_REPORT.md     # NEW
00_ARCHITECTURE/portal_validation/qg1_evidence/                     # NEW — captured artifacts
CLAUDECODE_BRIEF.md
```

### must_not_touch
- All production code (read-only).
- Persistent AIOps config (DO NOT call PUT /api/admin/aiops/stack to change production state).
  - Use per-request override headers only.

---

## §3 — Work plan

### 3.1 — Pre-flight

Capture current production state via read-only API call:

```bash
COOKIE=$(npx --prefix platform tsx platform/scripts/dev/mint_session_cookie.ts)
SERVICE_URL=$(gcloud run services describe amjis-web --region asia-south1 \
  --format='value(status.url)')

curl -sf -H "Cookie: __session=$COOKIE" "$SERVICE_URL/api/admin/aiops/state" \
  > qg1_evidence/00_baseline_state.json

# Read .active_stack from that file — call it BASELINE_STACK.
```

The baseline is whatever the user has currently set (likely `gemini`).
PIV does NOT touch this.

### 3.2 — Routing matrix tests (read-only)

For each of the 6 stacks {nim, gemini, deepseek, gpt, anthropic, marsys},
fetch effective routing via:

```bash
curl -sf -H "Cookie: __session=$COOKIE" \
  "$SERVICE_URL/api/admin/aiops/routing/$STACK" \
  > "qg1_evidence/01_routing_${STACK}.json"
```

Confirm response shape: each entry has primary + fallback, both are valid
model IDs in `MODELS` registry. Per-call-type spec violations would be a
finding (HIGH severity).

### 3.3 — Per-request override probe

For each cheap model per stack (master plan §3 table), construct a
canonical query and submit it with override headers:

```bash
for STACK in nim gemini deepseek gpt marsys; do
  case "$STACK" in
    nim)      MODEL='nvidia/nemotron-3-super-120b-a12b' ;;
    gemini)   MODEL='gemini-2.5-flash-lite' ;;
    deepseek) MODEL='deepseek-chat' ;;
    gpt)      MODEL='gpt-4.1-nano' ;;
    marsys)   MODEL='gemini-2.5-flash-lite' ;;
  esac

  curl -sN -H "Cookie: __session=$COOKIE" \
       -H "Content-Type: application/json" \
       -H "x-aiops-stack: $STACK" \
       -H "x-aiops-model-synthesis-primary: $MODEL" \
       -H "x-piv-test-run: QG1-$(date +%s)" \
       -d '{"messages":[{"role":"user","content":"Two-sentence summary of saturn dasha effects on career"}],"chart_id":"<test-chart-id>"}' \
       "$SERVICE_URL/api/chat/consume" \
       > "qg1_evidence/02_consume_${STACK}.sse"
done
```

If `x-aiops-stack` / `x-aiops-model-*` headers are NOT supported by the
production code path, that's a finding (BLOCKER for "config affects
runtime"). Reach this finding by checking whether `runtime_config`
actually reads these headers (search the source).

### 3.4 — Verify the model that actually ran

For each query above, after the SSE stream completes, query the audit
table for the model_id used in the synthesis step:

```bash
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc "
  SELECT model_name FROM llm_usage_events
  WHERE provider_request_id IS NOT NULL
    AND occurred_at >= now() - interval '5 minutes'
    AND pipeline_stage = 'synthesis'
  ORDER BY occurred_at DESC LIMIT 1
" > "qg1_evidence/03_audit_model_${STACK}.txt"
```

Assert: the model_id captured matches the model PIV sent in the
override header. If it doesn't, that's a BLOCKER finding (config doesn't
affect runtime).

### 3.5 — Param override smoke

Test that a per-request param override (e.g., `x-aiops-param-synthesis-max_output_tokens`)
caps the response length. Send a query that would normally produce a
long response with `max_output_tokens=200` override; verify response is
≤ 200 tokens.

### 3.6 — Author QG1_CONFIG_RUNTIME_REPORT.md

Sections:
- §1 — Baseline state (production active_stack at time of test)
- §2 — Routing matrix snapshot (per stack, primary + fallback per call_type)
- §3 — Per-request override behavior (model substitution verified per stack)
- §4 — Param override behavior (verified)
- §5 — Findings (any unexpected behavior; categorize BLOCKER / HIGH / MEDIUM / LOW)

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.QG1.1 | Baseline state captured | file exists |
| AC.QG1.2 | Routing matrix captured for all 6 stacks | 6 files |
| AC.QG1.3 | Per-request override produces matching audit model_name per stack | parametrized assertion |
| AC.QG1.4 | Param override caps response length | assertion |
| AC.QG1.5 | Anthropic stack tests skipped per banned-by-default rule | grep audit shows no anthropic provider calls from PIV |
| AC.QG1.6 | QG1_CONFIG_RUNTIME_REPORT.md authored with §1–§5 | grep section headers |
| AC.QG1.7 | Production active_stack unchanged after session | diff baseline vs end-state |
| AC.QG1.8 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit + rotate to QG.2.

```
docs(piv-QG.1): config → runtime integration validation

- Verified per-request override headers (x-aiops-stack, x-aiops-model-*)
  successfully redirect synthesis to the requested model.
- Verified param overrides cap response length.
- 5 stacks tested live (anthropic skipped per cost rule).
- N findings captured.
- Production active_stack unchanged.

AC summary: 8/8 PASS
```

---

## §6 — BAIL OUT

- Per-request override headers not recognized by runtime_config (this means
  Phase 1's "per-request priority" path was never wired — significant finding).
- DB proxy unreachable (need start_db_proxy.sh).
- Anthropic queries somehow fire despite skip rule.

---

*End of PHASE_QG_1_BRIEF.md*
