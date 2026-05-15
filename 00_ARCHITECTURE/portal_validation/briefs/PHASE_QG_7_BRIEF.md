---
status: OPEN
session_id: PIV_QG_7
phase: QG.7
phase_name: "Performance + cost baseline — latency p50/p95, cost-per-query, throughput"
next_session: PIV_QG_8
authored_at: 2026-05-14
authored_by: PORTAL_INTEGRATION_VALIDATION_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — PIV_QG_7
## Portal Integration Validation, Step 7 — Performance & Cost Baseline

---

## §0 — Executor orientation

QG.7 establishes the *baseline* — what the production query path
actually costs and how long it takes on cheap-model configurations.
The output is a per-stack performance fingerprint that future
regression tests can compare against.

NOT a load test. Single-stream sequential execution. Cheap models.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/portal_validation/QG2_PROVIDER_MATRIX.md (which cells passed)
3. 00_ARCHITECTURE/portal_validation/QG4_AUDIT_TRACE_AUDIT.md (cost telemetry shape)
4. platform/src/app/(super-admin)/observatory/** (cost reporting)
5. 00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md (latency targets if any)
```

---

## §2 — Scope

### may_touch
```
00_ARCHITECTURE/portal_validation/QG7_PERFORMANCE_BASELINE.md     # NEW
00_ARCHITECTURE/portal_validation/qg7_evidence/                     # NEW
CLAUDECODE_BRIEF.md
```

### must_not_touch
- All production code.
- DB write access (read-only psql).

---

## §3 — Work plan

### 3.1 — Canonical query set

Define 3 canonical queries spanning complexity tiers:

```
Q-SHORT:    "One sentence: what's a major theme in my chart?"
Q-MEDIUM:   "Three-paragraph summary of my career outlook over next year."
Q-LONG:     "Full holistic synthesis with cross-domain linkages, classical citations, and a probabilistic forecast."
```

Each will be run N=5 times per stack to compute p50/p95.

### 3.2 — Execution loop

```bash
COOKIE=$(npx --prefix platform tsx platform/scripts/dev/mint_session_cookie.ts)
SERVICE_URL=$(gcloud run services describe amjis-web --region asia-south1 --format='value(status.url)')

mkdir -p qg7_evidence

for STACK in nim gemini deepseek gpt marsys; do
  case "$STACK" in
    nim)      MODEL='nvidia/nemotron-3-super-120b-a12b' ;;
    gemini)   MODEL='gemini-2.5-flash-lite' ;;
    deepseek) MODEL='deepseek-chat' ;;
    gpt)      MODEL='gpt-4.1-nano' ;;
    marsys)   MODEL='gemini-2.5-flash-lite' ;;
  esac

  for QID in Q-SHORT Q-MEDIUM Q-LONG; do
    case "$QID" in
      Q-SHORT)  Q="One sentence: what's a major theme in my chart?" ;;
      Q-MEDIUM) Q="Three-paragraph summary of my career outlook over next year." ;;
      Q-LONG)   Q="Full holistic synthesis with cross-domain linkages, classical citations, and a probabilistic forecast." ;;
    esac

    for I in 1 2 3 4 5; do
      RUN_ID="QG7-${STACK}-${QID}-${I}"
      START=$(date +%s%3N)
      curl -sN -H "Cookie: __session=$COOKIE" \
           -H "Content-Type: application/json" \
           -H "x-aiops-stack: $STACK" \
           -H "x-aiops-model-synthesis-primary: $MODEL" \
           -H "x-piv-test-run: $RUN_ID" \
           -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$Q\"}],\"chart_id\":\"<test-chart-id>\"}" \
           "$SERVICE_URL/api/chat/consume" \
           > "qg7_evidence/${RUN_ID}.sse"
      END=$(date +%s%3N)
      echo "$RUN_ID $((END - START))" >> qg7_evidence/_latencies_ms.txt
      sleep 2
    done
  done
done
```

That's 5 stacks × 3 query tiers × 5 reps = 75 calls.

### 3.3 — Aggregate latency

```bash
awk '{
  split($1, parts, "-")
  key = parts[2] "-" parts[3] "-" parts[4]
  count[key]++
  values[key, count[key]] = $2
}
END {
  for (k in count) {
    n = count[k]
    # sort values for this key
    for (i = 1; i <= n; i++) {
      for (j = i+1; j <= n; j++) {
        if (values[k, i] > values[k, j]) {
          tmp = values[k, i]
          values[k, i] = values[k, j]
          values[k, j] = tmp
        }
      }
    }
    p50_idx = int(n/2) + 1
    p95_idx = int(n * 0.95 + 0.5)
    if (p95_idx > n) p95_idx = n
    print k, "p50=" values[k, p50_idx] "ms p95=" values[k, p95_idx] "ms"
  }
}' qg7_evidence/_latencies_ms.txt > qg7_evidence/01_latency_summary.txt
```

### 3.4 — Aggregate cost from llm_usage_events

```bash
psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -tAc "
  SELECT
    request_metadata->>'x-piv-test-run' AS run_id,
    SUM(prompt_tokens)       AS prompt,
    SUM(completion_tokens)   AS completion,
    SUM(total_cost_usd)      AS cost
  FROM llm_usage_events
  WHERE request_metadata->>'x-piv-test-run' LIKE 'QG7-%'
  GROUP BY 1
  ORDER BY 1
" > qg7_evidence/02_cost_per_run.txt
```

Compute mean cost per stack × tier:
```bash
awk -F'[|]' 'NR>1 {
  split($1, parts, "-")
  key = parts[2] "-" parts[3]
  total[key] += $4
  count[key]++
}
END {
  for (k in total) {
    print k, "mean_cost_usd=" total[k]/count[k]
  }
}' qg7_evidence/02_cost_per_run.txt > qg7_evidence/03_mean_cost_per_stack_tier.txt
```

### 3.5 — Cost-vs-latency scatter (for the report)

For each (stack, tier) pair, capture mean latency × mean cost — this
is the dominant data shape for the QG.7 deliverable.

### 3.6 — Observe Observatory dashboard

Verify the Observatory's cost-per-query widget reflects the QG.7 burst:

```bash
curl -sf -H "Cookie: __session=$COOKIE" \
     "$SERVICE_URL/api/admin/observatory/cost-per-query?period=last_1h" \
     > qg7_evidence/04_observatory_post_burst.json
```

Assert: post-burst cost > pre-burst cost by approximately the sum
captured in step 3.4.

### 3.7 — Author QG7_PERFORMANCE_BASELINE.md

Sections:
- §1 — Methodology (3 tiers, 5 reps per stack)
- §2 — Latency baseline table (per stack × tier, p50 + p95)
- §3 — Cost baseline table (per stack × tier, mean USD)
- §4 — Cost-vs-latency analysis (which stacks are price-performant)
- §5 — Observatory reconciliation (burst visible in dashboard)
- §6 — Findings (any stack with anomalous latency or cost)
- §7 — Recommended cheap-model defaults per call-type (input to AIOps
       Control Panel default routing tuning, IF any)

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.QG7.1 | 75 runs captured (5 stacks × 3 tiers × 5 reps) | file count |
| AC.QG7.2 | Latency p50/p95 computed per cell | grep file |
| AC.QG7.3 | Mean cost computed per cell | grep file |
| AC.QG7.4 | Observatory dashboard reflects QG.7 burst | freshness |
| AC.QG7.5 | QG7_PERFORMANCE_BASELINE.md authored §1–§7 | grep |
| AC.QG7.6 | Cumulative PIV LLM cost < $1.00 | sum (hard budget) |
| AC.QG7.7 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit + rotate to QG.8 (final report).

```
docs(piv-QG.7): perf + cost baseline across 5 stacks × 3 tiers

- 75 live runs captured at cheap-model defaults.
- Latency p50/p95 + mean cost tabulated per (stack, tier).
- Observatory burst reconciliation confirmed.
- Total PIV cumulative cost: $<X> (under $1.00 budget).

AC summary: 7/7 PASS
```

---

## §6 — BAIL OUT

- Cumulative PIV LLM cost approaches $1.00 before completing the 75
  runs — STOP and BAIL with partial data; QG.8 final report still
  proceeds with what was captured.
- Observatory dashboard does NOT reflect the burst (BLOCKER — cost
  visibility broken; deserves immediate native attention).

---

*End of PHASE_QG_7_BRIEF.md*
