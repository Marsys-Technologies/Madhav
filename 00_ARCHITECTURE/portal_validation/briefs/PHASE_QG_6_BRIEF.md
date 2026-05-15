---
status: OPEN
session_id: PIV_QG_6
phase: QG.6
phase_name: "Edge cases + failure modes — fallback, retry, timeout, malformed input"
next_session: PIV_QG_7
authored_at: 2026-05-14
authored_by: PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — PIV_QG_6
## Portal Integration Validation, Step 6 — Edge Cases & Failure Modes

---

## §0 — Executor orientation

QG.6 exercises the negative paths. The previous five sub-phases proved
the happy path works. QG.6 asks: when things go wrong — bad model
selection, timeout, malformed JSON, provider 5xx, rate limit — does
the system degrade gracefully, fall back as designed, and surface a
recoverable error to the user?

Cheap models. Failures induced via crafted requests, NOT by mutating
production state.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/portal_validation/QG2_PROVIDER_MATRIX.md (known good cells)
3. 00_ARCHITECTURE/portal_validation/QG4_AUDIT_TRACE_AUDIT.md (observability shape)
4. platform/src/lib/adapters/dispatcher.ts (fallback path)
5. platform/src/lib/adapters/run_adapter.ts + stream_adapter.ts
6. platform/src/lib/models/runtime_config.ts (fallback resolution)
7. platform/src/lib/synthesis/single_model_strategy.ts (retry logic, if any)
8. platform/src/app/api/chat/consume/route.ts (error surfacing)
```

---

## §2 — Scope

### may_touch
```
00_ARCHITECTURE/portal_validation/QG6_FAILURE_MODE_AUDIT.md       # NEW
00_ARCHITECTURE/portal_validation/qg6_evidence/                     # NEW
CLAUDECODE_BRIEF.md
```

### must_not_touch
- All production code.
- Persistent AIOps config.

---

## §3 — Work plan

### 3.1 — Failure scenarios to induce

| ID | Scenario | How to induce | Expected behavior |
|---|---|---|---|
| F1 | Invalid model in override | `x-aiops-model-synthesis-primary: not-a-real-model` | Fallback to registry default OR clean 400 |
| F2 | Stack with no fallback configured | force primary failure on a stack | Error surfaced with stack + model name |
| F3 | Empty messages array | `{"messages":[]}` | 400 with validation error |
| F4 | Malformed chart_id | `chart_id: "not-a-uuid"` | 400 OR 404 |
| F5 | Extremely long input (token explosion) | 50K-char user message | Either truncation OR clean error; no provider crash |
| F6 | Provider 401 (use anthropic if BANNED) | Force a cell where auth fails | FAIL_AUTH classified; no retry storm |
| F7 | Cancellation mid-stream | Close SSE connection after 1s | Server cleans up; no zombie tokens billed |
| F8 | Tool-call without matching tool | Request planner with non-existent tool ID | Adapter rejects OR planner adjusts; no crash |

### 3.2 — Execute each scenario

For each Fn, capture:
- Request body
- Response status + body
- audit_events row (if any)
- llm_usage_events row (if any)

```bash
COOKIE=$(npx --prefix platform tsx platform/scripts/dev/mint_session_cookie.ts)
SERVICE_URL=$(gcloud run services describe amjis-web --region asia-south1 --format='value(status.url)')

mkdir -p qg6_evidence

# Example F1 — invalid model
RUN_ID="QG6-F1-$(date +%s)"
curl -si -H "Cookie: __session=$COOKIE" \
     -H "Content-Type: application/json" \
     -H "x-aiops-stack: gemini" \
     -H "x-aiops-model-synthesis-primary: gemini-not-real" \
     -H "x-piv-test-run: $RUN_ID" \
     -d '{"messages":[{"role":"user","content":"hi"}],"chart_id":"<test-chart-id>"}' \
     "$SERVICE_URL/api/chat/consume" \
     > qg6_evidence/F1_invalid_model.txt
```

Build similar curl invocations for F2–F8 following the pattern.

### 3.3 — Cancellation test (F7)

```bash
# Start request, kill after 1s
RUN_ID="QG6-F7-$(date +%s)"
timeout 1 curl -sN -H "Cookie: __session=$COOKIE" \
     -H "Content-Type: application/json" \
     -H "x-piv-test-run: $RUN_ID" \
     -d '{"messages":[{"role":"user","content":"Write a 2000-word essay on saturn"}],"chart_id":"<test-chart-id>"}' \
     "$SERVICE_URL/api/chat/consume" \
     > qg6_evidence/F7_cancellation.sse || true

# 30s later, check whether tokens kept billing
sleep 30
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc "
  SELECT completion_tokens, total_cost_usd, occurred_at
  FROM llm_usage_events
  WHERE request_metadata->>'x-piv-test-run' = '$RUN_ID'
" > qg6_evidence/F7_cancellation_billing.txt
```

Assert: completion_tokens ≤ ~200 (cancellation honored). Continued
streaming after disconnect = HIGH (billing leak).

### 3.4 — Fallback path validation (F2)

The runtime_config + dispatcher should fall back to the registry's
declared fallback model when primary fails. Force a primary failure
(F1-style invalid model) and verify the synthesis still completes
using the registry's fallback:

```bash
RUN_ID="QG6-F2-$(date +%s)"
curl -sN -H "Cookie: __session=$COOKIE" \
     -H "Content-Type: application/json" \
     -H "x-aiops-stack: gemini" \
     -H "x-aiops-model-synthesis-primary: gemini-totally-fake-xyz" \
     -H "x-piv-test-run: $RUN_ID" \
     -d '{"messages":[{"role":"user","content":"hi"}],"chart_id":"<test-chart-id>"}' \
     "$SERVICE_URL/api/chat/consume" \
     > qg6_evidence/F2_fallback.sse

# Check audit for which model actually ran
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc "
  SELECT model_name FROM llm_usage_events
  WHERE request_metadata->>'x-piv-test-run' = '$RUN_ID'
" > qg6_evidence/F2_fallback_model.txt
```

Assert: a model ran (any model — primary or fallback). If nothing ran,
either fallback isn't wired (HIGH) or the request hard-failed (depends
on policy — document in the audit).

### 3.5 — Author QG6_FAILURE_MODE_AUDIT.md

Sections:
- §1 — Failure scenarios run (table with F1–F8 + outcome)
- §2 — Per-scenario evidence (request/response/audit)
- §3 — Cancellation billing audit (F7 detail)
- §4 — Fallback behavior summary (F2 detail)
- §5 — Findings (any unexpected error surfaces, leaked billing, retry
       storms, zombie streams)
- §6 — Open follow-ups

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.QG6.1 | F1–F8 all executed (evidence files exist) | file count = 8 |
| AC.QG6.2 | F7 cancellation: completion_tokens ≤ 500 | assertion |
| AC.QG6.3 | F2 fallback: a model completed OR clean error surfaced | audit |
| AC.QG6.4 | No 5xx response on any F-scenario (4xx expected for some) | response codes |
| AC.QG6.5 | QG6_FAILURE_MODE_AUDIT.md authored §1–§6 | grep |
| AC.QG6.6 | Cumulative PIV LLM cost < $0.85 | sum |
| AC.QG6.7 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit + rotate to QG.7.

---

## §6 — BAIL OUT

- Any F-scenario produces a 5xx with stack trace exposed to client
  (security finding — capture and BAIL).
- F7 cancellation shows runaway billing (>5K tokens after disconnect).
- Production state mutates during a failure test.

---

*End of PHASE_QG_6_BRIEF.md*
