---
status: OPEN
session_id: PIV_QG_4
phase: QG.4
phase_name: "Audit + observability trace — query → audit_events → Observatory"
next_session: PIV_QG_5
authored_at: 2026-05-14
authored_by: PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — PIV_QG_4
## Portal Integration Validation, Step 4 — Audit & Observability Trace

---

## §0 — Executor orientation

QG.4 validates the seventh integration seam from PORTAL_INVENTORY:
the audit/observability surface. A query runs → audit events are
emitted → trace + cost telemetry land in DB → Observatory + /trace UI
expose them. Each link can drop data without immediately failing user
queries — this is where silent observability rot hides.

Live LLM calls allowed, cheap models, one query per test category.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/portal_validation/PORTAL_INVENTORY.md (§3 audit surfaces)
3. 00_ARCHITECTURE/portal_validation/QG2_PROVIDER_MATRIX.md (cells that PASSed)
4. platform/src/app/api/chat/consume/route.ts (event emitter)
5. platform/src/lib/audit/** (writer modules)
6. platform/src/lib/observability/** (trace writers)
7. platform/supabase/migrations/011_audit_events.sql (or equivalent)
8. platform/supabase/migrations/040_query_trace_steps.sql (or equivalent)
9. platform/supabase/migrations/045_audit_events_*.sql (nullable cols)
10. platform/src/app/(super-admin)/observatory/** (reader)
11. platform/src/app/(super-admin)/trace/** (reader)
```

---

## §2 — Scope

### may_touch
```
00_ARCHITECTURE/portal_validation/QG4_AUDIT_TRACE_AUDIT.md       # NEW
00_ARCHITECTURE/portal_validation/qg4_evidence/                    # NEW
CLAUDECODE_BRIEF.md
```

### must_not_touch
- All production code (read-only).
- DB tables (read-only via psql).

---

## §3 — Work plan

### 3.1 — Run a "golden trace" query

Submit a single representative query with a cheap model AND with
`x-piv-test-run: QG4-GOLDEN-<ts>` header:

```bash
COOKIE=$(npx --prefix platform tsx platform/scripts/dev/mint_session_cookie.ts)
SERVICE_URL=$(gcloud run services describe amjis-web --region asia-south1 --format='value(status.url)')
RUN_ID="QG4-GOLDEN-$(date +%s)"

mkdir -p qg4_evidence

curl -sN -H "Cookie: __session=$COOKIE" \
     -H "Content-Type: application/json" \
     -H "x-aiops-stack: gemini" \
     -H "x-aiops-model-synthesis-primary: gemini-2.5-flash-lite" \
     -H "x-piv-test-run: $RUN_ID" \
     -d '{"messages":[{"role":"user","content":"Holistic chart summary in 3 sentences"}],"chart_id":"<test-chart-id>"}' \
     "$SERVICE_URL/api/chat/consume" \
     > "qg4_evidence/01_consume_stream.sse"

echo "$RUN_ID" > qg4_evidence/run_id.txt
```

### 3.2 — Verify audit_events writes

```bash
# Start Cloud SQL Auth Proxy (port 5433)
bash platform/scripts/start_db_proxy.sh &
sleep 3

psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc "
  SELECT stage, event_type, model_name, occurred_at
  FROM audit_events
  WHERE provider_request_id IS NOT NULL
    AND occurred_at >= now() - interval '5 minutes'
  ORDER BY occurred_at ASC
" > qg4_evidence/02_audit_events.txt

cat qg4_evidence/02_audit_events.txt
```

**Expected stages (per production taxonomy):**
`classify` → `compose_bundle` → `plan_per_tool` → `tool_fetch` (×N)
→ `synthesis` → `audit`.

Assert: ≥6 distinct stages logged. Missing stage = MEDIUM finding.

### 3.3 — Verify llm_usage_events cost telemetry

```bash
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc "
  SELECT model_name, prompt_tokens, completion_tokens, total_cost_usd
  FROM llm_usage_events
  WHERE provider_request_id IS NOT NULL
    AND occurred_at >= now() - interval '5 minutes'
  ORDER BY occurred_at ASC
" > qg4_evidence/03_llm_usage.txt

cat qg4_evidence/03_llm_usage.txt
```

Assert: per LLM call there is a row with non-null tokens + cost.
Zero rows = BLOCKER (Observatory blind). Null cost = MEDIUM (pricing
seed gap).

### 3.4 — Verify query_trace_steps writes

```bash
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc "
  SELECT step_name, parent_id, started_at, ended_at - started_at AS dur
  FROM query_trace_steps
  WHERE root_query_id IN (
    SELECT id FROM query_trace_steps
    WHERE root_query_id IS NULL
      AND started_at >= now() - interval '5 minutes'
    ORDER BY started_at DESC LIMIT 1
  )
  ORDER BY started_at ASC
" > qg4_evidence/04_query_trace.txt

cat qg4_evidence/04_query_trace.txt
```

Assert: tree-structured rows present. Missing = HIGH finding (trace UI
broken).

### 3.5 — Verify Observatory UI reads it

```bash
# Hit Observatory cost-per-query for current period
curl -sf -H "Cookie: __session=$COOKIE" \
     "$SERVICE_URL/api/admin/observatory/cost-per-query?period=last_24h" \
     > qg4_evidence/05_observatory_cpq.json
```

Assert: response includes the just-fired query's cost contribution.
Stale data = HIGH (cache or write lag).

### 3.6 — Verify /trace UI reads it

```bash
# Fetch the trace details endpoint
TRACE_ID=$(psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc "
  SELECT id FROM query_trace_steps
  WHERE root_query_id IS NULL AND started_at >= now() - interval '5 minutes'
  ORDER BY started_at DESC LIMIT 1
")

curl -sf -H "Cookie: __session=$COOKIE" \
     "$SERVICE_URL/api/admin/trace/$TRACE_ID" \
     > qg4_evidence/06_trace_api.json
```

Assert: response includes step tree + lifecycle states. Missing = HIGH.

### 3.7 — Config audit rail

For any AIOps config-touching action this session (PIV uses per-request
overrides; no persistent writes expected), audit the `llm_config_audit`
table for unexpected rows:

```bash
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc "
  SELECT actor, action, target, occurred_at
  FROM llm_config_audit
  WHERE occurred_at >= now() - interval '1 hour'
  ORDER BY occurred_at DESC
" > qg4_evidence/07_config_audit.txt
```

Assert: zero PIV-attributable persistent writes. Any write = BLOCKER
(PIV scope violation).

### 3.8 — Cost reconciliation

Sum the cost of all `x-piv-test-run` tagged queries (QG1 + QG2 + QG3 +
QG4):

```bash
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc "
  SELECT COALESCE(SUM(total_cost_usd), 0) AS piv_total_usd
  FROM llm_usage_events
  WHERE request_metadata->>'x-piv-test-run' LIKE 'QG%'
" > qg4_evidence/08_piv_total_cost.txt
```

Assert: total < $0.60 (running budget through QG.4). If approaching
$1.00, BAIL.

### 3.9 — Author QG4_AUDIT_TRACE_AUDIT.md

Sections:
- §1 — Golden trace summary (which query, which model, run-id)
- §2 — Audit events: which stages wrote, which didn't
- §3 — Cost telemetry: which models priced, which gaps remain
- §4 — Trace tree: depth, total steps, completeness
- §5 — Observatory/Trace UI: reads consistent with writes
- §6 — Findings (BLOCKER / HIGH / MEDIUM / LOW)

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.QG4.1 | Golden trace query executed + tagged | run-id file |
| AC.QG4.2 | audit_events has ≥6 stages for the trace | count |
| AC.QG4.3 | llm_usage_events has cost rows per LLM call | non-zero |
| AC.QG4.4 | query_trace_steps has tree structure (≥3 nodes) | count |
| AC.QG4.5 | Observatory cost-per-query reflects new query | freshness |
| AC.QG4.6 | /trace endpoint returns the trace | 200 OK |
| AC.QG4.7 | llm_config_audit shows zero PIV persistent writes | count = 0 |
| AC.QG4.8 | Cumulative PIV LLM cost < $0.60 | sum |
| AC.QG4.9 | QG4_AUDIT_TRACE_AUDIT.md authored | grep §1–§6 |
| AC.QG4.10 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit + rotate to QG.5.

---

## §6 — BAIL OUT

- llm_usage_events writes zero rows for any QG4 query (Observatory
  is blind to live traffic).
- llm_config_audit shows a PIV-attributable persistent config write
  (scope violation).
- DB proxy unreachable.

---

*End of PHASE_QG_4_BRIEF.md*
