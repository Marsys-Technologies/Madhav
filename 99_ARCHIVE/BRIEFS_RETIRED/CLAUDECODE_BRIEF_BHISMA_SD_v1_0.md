---
title: "BHISMA Wave 2 — Session S-D: Integration Verification + Wave 2 Close"
brief_id: BHISMA_SD
version: 1.0
status: COMPLETE
created_date: 2026-05-03
session_id: BHISMA-W2-S-D
executor: claude-opus-4-6
active_phase: "BHISMA Wave 2 — Close"
isolation_tier: BHISMA_ONLY
blocked_by: BHISMA_SC
---

# BHISMA Wave 2 — Session S-D
## Integration Verification + Wave 2 Close

**Set `status: IN_PROGRESS` at session open. Set `status: COMPLETE` only after ALL acceptance criteria pass.**

---

## §0 Context

S-A, S-B, and S-C are all COMPLETE. This final session runs the full test suite, closes any open EVAL gaps, presents the Lever 2 report to the native for decision, creates the Wave 2 sealing artifact, and appends the session close block to SESSION_LOG.

This session has one native-decision gate (§4): the full tsc + vitest report and Lever 2 recall/precision score are presented; the native decides whether to flip `LLM_FIRST_PLANNER_ENABLED`.

---

## §1 Pre-Work: Full Test Suite Run

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform

# TypeScript check
npx tsc --noEmit 2>&1 | tee /tmp/bhisma_tsc_report.txt
echo "Exit code: $?"

# Full test suite
npx vitest run --reporter=verbose 2>&1 | tee /tmp/bhisma_vitest_report.txt
echo "Exit code: $?"

# Summary counts
grep -E "✓|×|PASS|FAIL" /tmp/bhisma_vitest_report.txt | tail -30
```

**Expected baseline (from S-A):** 1102 passing tests. New tests from S-A (UQE + MON) should be in this count.

**Known pre-existing failures (do NOT count as regressions):**
- e2e/Playwright tests — require browser runtime
- `manifest_planner.test.ts` — incomplete `ai` SDK mock
- `cgm_graph_walk.test.ts` — "feature flag disabled" variant
- `integration.test.ts` — "17 tools" count assertion (pre-dates Wave 2)

Document all FAILING tests in BHISMA_W2_CLOSE with `pre_existing: true` or `introduced_by_wave2: true` classification.

---

## §2 EVAL Golden Set Coverage Gap (close before sealing)

S-B flagged: `predictive=4` (need 5), `edge_case=2` (need 5) in `platform/tests/eval/planner_golden_set.json`.

**This session closes the gap:**

Read `platform/tests/eval/planner_golden_set.json`. Add the following entries to reach 5 predictive + 5 edge-case:

**Predictive gap (need 1 more):**
```json
{
  "query_text": "According to my Vimshottari Dasha sequence, when does my Mercury period begin and what will it activate?",
  "expected_tools": ["l1_facts_query", "msr_sql"],
  "expected_planets": ["Mercury"],
  "expected_domain": "timing",
  "min_tools": 2,
  "forbidden_tools": [],
  "reasoning": "Dasha timing query requires L1 chart data (dasha sequence) and MSR signals for Mercury"
}
```

**Edge case gaps (need 3 more):**
```json
{
  "query_text": "",
  "expected_tools": [],
  "expected_planets": [],
  "expected_domain": "",
  "min_tools": 0,
  "forbidden_tools": [],
  "reasoning": "Empty query should trigger circuit breaker / fallback; planner must not error"
},
{
  "query_text": "?",
  "expected_tools": [],
  "expected_planets": [],
  "expected_domain": "",
  "min_tools": 0,
  "forbidden_tools": [],
  "reasoning": "Single punctuation: graceful no-op; planner should return minimal plan without crashing"
},
{
  "query_text": "Tell me everything about everything in my entire chart in full detail with all possible combinations and permutations and every possible interpretation",
  "expected_tools": ["l1_facts_query", "msr_sql", "cgm_graph_walk"],
  "expected_planets": [],
  "expected_domain": "holistic",
  "min_tools": 2,
  "forbidden_tools": [],
  "reasoning": "Overloaded holistic query: budget arbitration must trim to fit context; planner must not hang"
}
```

Also update `platform/tests/eval/fixtures/regression_baseline.json` to reflect the new total (28 cases). If the baseline stores aggregate counts, update them. If it stores full case lists, append the new cases.

**After adding:** re-run the mocked regression gate to confirm it still passes:
```bash
npx vitest run tests/eval/planner_regression_gate.test.ts --reporter=verbose 2>&1
```

---

## §3 Lever 2 Re-Evaluation (if NIM recovered)

Check NIM provider health:
```bash
# Attempt a lightweight NIM call to see if provider is up
curl -s -X POST [NIM_ENDPOINT]/v1/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [NIM_KEY]" \
  -d '{"model":"meta/llama-3.1-8b-instruct","prompt":"hello","max_tokens":5}' 2>&1 | head -5
```

**If NIM is healthy:** Run full EVAL-2:
```bash
cd platform && npm run eval:planner 2>&1 | tee /tmp/bhisma_lever2_report.txt
```
Record `tool_recall` and `tool_precision` from output.

**If NIM is still down:** Record as BLOCKED; include in BHISMA_W2_CLOSE as an open item.

**Present to native in the BHISMA_W2_CLOSE artifact.** Do NOT flip `LLM_FIRST_PLANNER_ENABLED` — that is a native action.

---

## §4 Create BHISMA_W2_CLOSE_v1_0.md

**File:** `00_ARCHITECTURE/BHISMA_W2_CLOSE_v1_0.md`

This is the Wave 2 sealing artifact. It must include all of the following sections:

```markdown
---
title: "BHISMA Wave 2 — Wave Close Artifact"
canonical_id: BHISMA_W2_CLOSE
version: 1.0
status: CURRENT
created_date: 2026-05-03
sealed_by: BHISMA-W2-S-D
---

# BHISMA Wave 2 — Wave Close

## §1 Executive Summary

[1 paragraph: what Wave 2 delivered, total tasks, streams, session sequence]

## §2 Session Outcomes

| Session | Delivered | Test Impact |
|---------|-----------|-------------|
| S-A | [key deliverables from session summary] | +83 tests (1019→1102) |
| S-B | [key deliverables] | EVAL scripts added |
| S-C | [migrations applied] | DB schema live |
| S-D | [gap close + report] | [count] passing |

## §3 Stream Completion Status

| Stream | Tasks | Status | Notes |
|--------|-------|--------|-------|
| UQE | 15 | COMPLETE | LLM_FIRST_PLANNER_ENABLED=false (Lever 2 pending) |
| MON | 10 | COMPLETE | Tables live (S-C); emission verified (S-A) |
| TRACE | 10 | COMPLETE | All 10 panels shipped in prior commits (Wave 1 B3) |
| SCHEMA | 6 | COMPLETE | RETENTION_POLICY_v1_0.md created (S-B) |
| EVAL | 5 | COMPLETE | Golden set 28 cases; EVAL-4 script live; EVAL-2 Lever 2 [PASS/BLOCKED] |

## §4 Lever 2 Report

- **LLM_FIRST_PLANNER_ENABLED current value:** false (default)
- **EVAL-2 result:** [PASS / BLOCKED — NIM provider down]
- **tool_recall:** [score or N/A]
- **tool_precision:** [score or N/A]
- **Recommendation:** [FLIP if PASS with both thresholds met / HOLD if BLOCKED or FAIL]
- **Native action required to flip:** Set `MARSYS_FLAG_LLM_FIRST_PLANNER_ENABLED=true` in `.env.production`; redeploy Cloud Run service

## §5 Known Pre-Existing Test Failures

| Test File | Failure Reason | Classification |
|-----------|---------------|----------------|
| [file] | [reason] | pre_existing |
| ...      |               |                |

None of the above were introduced by Wave 2 sessions.

## §6 Open Items (carry into Wave 3 or follow-on)

| Item | Owner | Priority | Notes |
|------|-------|----------|-------|
| CI workflow gate (eval:planner-regression on PR) | Native sign-off required | MEDIUM | Add ci.yml on pull_request |
| NIM provider stability | Infrastructure | HIGH | EVAL-2 blocked; needs provider health gate |
| 16 structured tools in src/lib/tools/structured/ missing query_id | Phase 11B scope | LOW | Legacy path; deletion scheduled |
| LLM_FIRST_PLANNER_ENABLED flip | Native decision | HIGH | Gate: tool_recall ≥0.80, tool_precision ≥0.90 |

## §7 ADR Status (from BHISMA_PLAN_v1_0.md §2)

All 6 ADRs remain active and are now fully instrumented:
- ADR-1 (Multi-family FAMILY_WORKER): registry.ts ✅
- ADR-2 (o-series calling convention): resolver.ts ✅
- ADR-3 (Failure loud): PipelineError enforced ✅
- ADR-4 (FORENSIC synthesis floor): validator.ts ✅
- ADR-5 (LLM-first planning): universal_query_engine.ts created ✅ (flag OFF pending Lever 2)
- ADR-6 (Token budget enforcement): budget_arbiter.ts ✅

## §8 Post-Wave 2 Roadmap

Next workstream: **W3-DB-MIGRATIONS** (deferred from Wave 1 §6) and **BHISMA-W2-S1-DISCOVERY-FRESHNESS** (signal embedding refresh).

MARSYS-JIS M5 (Probabilistic Engine) is the next macro-phase and runs independently of BHISMA.
```

---

## §5 Append to SESSION_LOG

Read `00_ARCHITECTURE/SESSION_LOG.md`. Append a combined entry for BHISMA Wave 2 (S-A through S-D) following the existing SESSION_LOG format. Include:
- session_ids: BHISMA-W2-S-A through BHISMA-W2-S-D
- dates: 2026-05-03
- deliverables: enumerate key artifacts created
- open_items: Lever 2 decision, CI workflow, EVAL coverage (now closed)
- outcome: BHISMA_W2_CLOSE_v1_0.md sealed

---

## §6 File Scope

### may_touch
```
00_ARCHITECTURE/BHISMA_W2_CLOSE_v1_0.md             [NEW — sealing artifact]
00_ARCHITECTURE/SESSION_LOG.md                       [append only]
platform/tests/eval/planner_golden_set.json          [extend to 28 cases]
platform/tests/eval/fixtures/regression_baseline.json [update totals]
```

### must_not_touch
```
platform/src/**
platform/migrations/**
CLAUDECODE_BRIEF_BHISMA_SA_v1_0.md
CLAUDECODE_BRIEF_BHISMA_SB_v1_0.md
CLAUDECODE_BRIEF_BHISMA_SC_v1_0.md
00_ARCHITECTURE/BHISMA_PLAN_v1_0.md
00_ARCHITECTURE/BHISMA_WAVE2_PLAN_v1_1.md
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
/Users/Dev/Vibe-Coding/Apps/Ustad/**
CLAUDE.md
```

---

## §7 Acceptance Criteria

- [ ] Full tsc + vitest run complete; report in BHISMA_W2_CLOSE §5 (pre-existing failures catalogued)
- [ ] EVAL golden set extended to ≥28 cases (predictive=5, edge_case=5)
- [ ] `planner_regression_gate.test.ts` still PASS after golden set extension
- [ ] Lever 2 report in BHISMA_W2_CLOSE §4 (PASS, FAIL, or BLOCKED with explanation)
- [ ] `BHISMA_W2_CLOSE_v1_0.md` created with all 8 sections
- [ ] `SESSION_LOG.md` appended with Wave 2 combined entry

---

## §8 Hard Constraints

1. **Do NOT flip LLM_FIRST_PLANNER_ENABLED** — this is a native decision after reading §4 of the close artifact.
2. **Do NOT add CI workflow without native approval** — document it as PENDING in the close artifact.
3. **SESSION_LOG append only** — do not edit existing entries; only append at the bottom.
4. **Session close:** When all ACs pass, set `status: COMPLETE` in this file's frontmatter.

---

## §9 How to Start

Open a new Antigravity window at `/Users/Dev/Vibe-Coding/Apps/Madhav/` and run:
```
Read CLAUDECODE_BRIEF_BHISMA_SD_v1_0.md and execute it.
```
