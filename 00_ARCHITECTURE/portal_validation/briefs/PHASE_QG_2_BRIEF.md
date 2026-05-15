---
status: OPEN
session_id: PIV_QG_2
phase: QG.2
phase_name: "Provider matrix smoke — all stacks × all call types × roles"
next_session: PIV_QG_3
authored_at: 2026-05-14
authored_by: PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — PIV_QG_2
## Portal Integration Validation, Step 2 — Provider Matrix Smoke

---

## §0 — Executor orientation

QG.2 walks the full provider × call-type × role matrix using live LLM
calls. Confirms the adapter correctly routes through each provider's
quirks and produces a valid `ModelInteraction` with expected fields.

5 active providers (anthropic skipped) × 11 call types × 2 roles = up to
110 cells. PIV uses the cheapest model per stack (master plan §3) to
keep cost under $0.20.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/portal_validation/PORTAL_INVENTORY.md
3. 00_ARCHITECTURE/portal_validation/PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0.md §3 (cost model)
4. platform/src/app/api/admin/aiops/probe/route.ts (the probe endpoint)
5. platform/src/lib/aiops/probe/runner.ts
6. platform/src/lib/adapters/types.ts (ModelInteraction shape)
7. platform/src/lib/models/registry.ts (which models are 'role: synthesis' / 'role: both' / etc.)
```

---

## §2 — Scope

### may_touch
```
00_ARCHITECTURE/portal_validation/QG2_PROVIDER_MATRIX.md            # NEW
00_ARCHITECTURE/portal_validation/qg2_evidence/                       # NEW
CLAUDECODE_BRIEF.md
```

### must_not_touch
- All production code (read-only).
- Per-request override only; no persistent config writes.

---

## §3 — Work plan

### 3.1 — Build the test matrix

11 call types from registry:
  synthesis, planner_deep, planner_fast, context_assembly, worker,
  eval_judge, eval_generator, smoke_synth,
  checkpoint_4_5, checkpoint_5_5, checkpoint_8_5

5 active stacks: nim, gemini, deepseek, gpt, marsys

For each (stack, call_type, role) cell:
- Resolve the model the production STACK_ROUTING + overrides + per-request
  cheap-model preference yields.
- Run a probe via `POST /api/admin/aiops/probe` with body
  `{stack, call_type, role}` plus override headers forcing the cheap model.

Some cells will use models that don't exist for that provider (e.g.,
`gemini`'s synthesis primary cheap-model-override would be
`gemini-2.5-flash-lite` which is `role: 'both'` — valid). Others may
genuinely have no cheap equivalent (e.g., a call type whose spec demands
≥1M context — only the registry's preferred models for that stack are
viable). Document these as "cell skipped: <reason>" in the matrix.

### 3.2 — Probe execution

```bash
COOKIE=$(npx --prefix platform tsx platform/scripts/dev/mint_session_cookie.ts)
SERVICE_URL=$(gcloud run services describe amjis-web --region asia-south1 \
  --format='value(status.url)')

mkdir -p qg2_evidence

for STACK in nim gemini deepseek gpt marsys; do
  for CALL_TYPE in synthesis planner_deep planner_fast context_assembly worker \
                   eval_judge eval_generator smoke_synth \
                   checkpoint_4_5 checkpoint_5_5 checkpoint_8_5; do
    for ROLE in primary fallback; do
      RUN_ID="QG2-${STACK}-${CALL_TYPE}-${ROLE}"
      echo "[$RUN_ID]"
      curl -sf -X POST \
           -H "Cookie: __session=$COOKIE" \
           -H "Content-Type: application/json" \
           -H "x-piv-test-run: $RUN_ID" \
           -d "{\"stack\":\"$STACK\",\"call_type\":\"$CALL_TYPE\",\"role\":\"$ROLE\"}" \
           "$SERVICE_URL/api/admin/aiops/probe" \
           > "qg2_evidence/${RUN_ID}.json"
      sleep 1  # rate-limit-friendly
    done
  done
done
```

### 3.3 — Result classification

For each probe result file, classify into one of:
- **PASS** — `result.pass === true`, latency < timeout, expected event types observed
- **FAIL_AUTH** — provider returned 401 (expected for anthropic; unexpected otherwise)
- **FAIL_TIMEOUT** — exceeded 30s; common for NIM nemotron-3-nano cold-start
- **FAIL_SPEC** — model selected violates call-type spec (e.g., synthesis using <1M ctx)
- **FAIL_OTHER** — any other failure mode, with error message captured

### 3.4 — Reasoning emission audit

For probes against models with `quirks.reasoning_via !== 'none'`, verify
the `ModelInteraction.reasoning.text` field is populated. For models
with `'none'`, verify it's absent. Mismatch is a finding.

### 3.5 — Tool-use audit

For call types `planner_deep`, `planner_fast`, `pipeline/pipeline_planner`,
verify the adapter's `tools` parameter was honored when sent. (Sample a few
cells; not exhaustive.)

### 3.6 — Author QG2_PROVIDER_MATRIX.md

The main deliverable: a matrix table showing the result per cell, plus
summary stats:
- Total probes attempted: N
- PASS: N / total
- FAIL_AUTH: N (expected for anthropic; unexpected otherwise)
- FAIL_TIMEOUT: N (note which models)
- FAIL_SPEC: N (any?)
- FAIL_OTHER: N

Plus findings (any unexpected failures).

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.QG2.1 | Probe results captured for all viable cells | file count ≥ 100 (5 stacks × 11 call types × 2 roles, minus skipped) |
| AC.QG2.2 | PASS rate ≥ 80% across non-anthropic cells | aggregate |
| AC.QG2.3 | Reasoning emission matches `reasoning_via` per probed model | parametrized |
| AC.QG2.4 | QG2_PROVIDER_MATRIX.md authored with summary + matrix + findings | grep |
| AC.QG2.5 | Total live LLM cost < $0.30 | sum from llm_usage_events with PIV tag |
| AC.QG2.6 | Anthropic probes confirmed skipped (no provider calls) | audit query |
| AC.QG2.7 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit + rotate to QG.3. Rough cost estimate goes in the commit body.

---

## §6 — BAIL OUT

- Probe endpoint returns 5xx systematically (broken in production).
- Cost telemetry shows PIV spending > $1 cumulative (rate-limit issue or model leakage).
- Anthropic provider calls escape despite skip rule.

---

*End of PHASE_QG_2_BRIEF.md*
