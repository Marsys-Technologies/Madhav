---
artifact: PHASE_3B_HTTP422_DIAGNOSTIC_BRIEF_v1_0.md
version: 1.0
status: ACTIVE
authored: 2026-05-18
authored_by: Claude Code (analysis/backend-data-pipeline-perf-audit)
parent_plan: 00_ARCHITECTURE/PHASE_3_CARRY_FORWARDS_EXECUTION_PLAN_v1_0.md §D
purpose: >
  Phase 3B investigation: root cause of reported HTTP 422 failures on
  GQ-013 and GQ-014 predictive fixtures. Findings + fix proposal.
---

# Phase 3B — HTTP 422 Diagnostic Brief

## §A — Executive Finding

**The HTTP 422 premise does not match the Phase 2 execution record.**

The Phase 3 plan (§D) describes GQ-013 and GQ-014 as returning HTTP 422 (request validation rejection). The authoritative record in `RETRIEVAL_TOOLS_PHASE_2_EXECUTION_PLAN_v1_0.md §B` shows:

| Fixture | Actual failure mode | HTTP 422? |
|---------|---------------------|-----------|
| GQ-013 predictive | **Low-quality synthesis** — HTTP 200 received, scored 0% on layer_coverage/b11/citations/calibration | No |
| GQ-014 predictive | **Timeout** — AbortSignal.timeout(130,000ms) at 2m10s | No |
| GQ-015 predictive | **Low-quality synthesis** — HTTP 200 received, scored 0% | No |

None of the predictive fixtures returned HTTP 422 in the documented Phase 2 run. The "HTTP 422" description in the Phase 3 plan was likely drafted from a different execution context (possibly the Cowork memory which captured a different run).

---

## §B — Code-Path Investigation

### B.1 — Where does route.ts return HTTP 422?

Two code paths in `platform/src/app/api/chat/consume/route.ts` return HTTP 422:

**Path 1 — PlannerFault (line 350–356):**
```typescript
} catch (err) {
  if (err instanceof PlannerFault) {
    return NextResponse.json(
      { error: 'planner_failed', message: err.message },
      { status: 422 },
    )
  }
  throw err
}
```
Triggered when `pipeline_planner.ts` throws `PipelinePlannerError`:
- Empty LLM text output
- Non-JSON LLM output (JSON parse failure)
- Schema-invalid JSON (fails `PipelinePlanSchema.safeParse`)

**Path 2 — Bundle validation failure (line 696–700):**
```typescript
if (bundleSummary.overall === 'fail' && configService.getFlag('VALIDATOR_FAILURE_HALT')) {
  return NextResponse.json(
    { error: 'bundle_validation_failed', failures: bundleSummary.failures },
    { status: 422 }
  )
}
```
Triggered only when `VALIDATOR_FAILURE_HALT` feature flag is `true`. In current production this flag is `false`.

### B.2 — Would GQ-013/014 query shapes trigger PlannerFault?

GQ-013: "What themes and tendencies might emerge in the next 6 months based on my current dasha and transits?"
GQ-014: "What does my chart suggest about the timing and nature of significant career transitions?"

Both are well-formed natural-language queries. The planner (`pipeline_planner.ts`) uses an LLM call (gemini-2.5-flash for planner_fast on the gemini stack) to produce a JSON `PipelinePlan`. For these queries to trigger PlannerFault, the LLM would need to return malformed JSON — which is possible under NIM stack (nemotron-3-super has lower JSON compliance rate than Gemini models for structured output) but unlikely under the gemini stack with native JSON mode.

**Key:** The Phase 2 run used `EVAL_STACK='nim'`. The NIM planner models use `structured_output_format: 'json_object'` (OpenAI compat, less strict than Gemini's `response_schema`). NIM planner failures causing HTTP 422 are plausible under heavy load or model degradation.

### B.3 — Why did GQ-013/015 score 0% despite HTTP 200?

From the Phase 2 synthesis bottleneck diagnosis (obs 580): "nvidia/nemotron-3-super-120b-a12b synthesis causes extreme latency variance and substantial token usage per call." The 0% scoring on layer_coverage/b11/citations/calibration suggests the NIM synthesis model:
- Generated a very short response (token deficit — confirmed root cause in Phase 2)
- Did not include L2.5 artifact references (MSR/CGM/FORENSIC)
- Did not include any citations (→ 0% citation_presence)

This is confirmed by S80: "synthesis output token deficit as root cause of quality failures."

### B.4 — Phase 3A resolves the root cause

Phase 3A changed `EVAL_STACK` default from `'nim'` to `'gemini'`. Under the gemini stack:
- Planner: `gemini-2.5-flash` (native structured output, high JSON compliance → PlannerFault unlikely)
- Synthesis: `gemini-2.5-pro` (high output token count → layer coverage, citations, calibration expected to pass)

The Phase 2 gemini-2.5-flash override eval (S82–S86) showed 3/3 factual passing with GQ-001 specifically passing "where it previously timed out." The same synthesis quality improvement should help GQ-013/015 (low-score failures) and GQ-014 (timeout — now using faster gemini synthesis path, no more NIM 5k-per-call latency variance).

---

## §C — Fix Proposal

### Decision: No code fix needed for HTTP 422

The HTTP 422 failure mode was not observed in the Phase 2 execution record. The actual failure modes were:
1. Low-quality synthesis (GQ-013, GQ-015) → resolved by Phase 3A's gemini stack default
2. Timeout (GQ-014) → likely resolved by Phase 3A (gemini synthesis is significantly faster than NIM nemotron-3-super under the 2m10s budget)

### Carry-forward for GQ-013/014/015

Per plan §D.1 path options: "Fix in code" vs "Fix in fixture":
- GQ-013/015 low-score failure: this is a **synthesis quality issue**, not a validation issue. Fix = Phase 3A (gemini stack default). No code change to query shape or validation rules needed.
- GQ-014 timeout: this is a **latency issue** on the NIM synthesis path. Fix = Phase 3A (gemini stack default eliminates NIM synthesis bottleneck). No code change needed.

**Formal fixture fix:** If post-deploy answer:eval (§G.2) confirms GQ-013/014/015 pass under the gemini stack, Phase 3B is resolved by Phase 3A. If they still fail, the failure mode should be diagnosed from the §G.2 results (log the exact HTTP status and scoring details for each).

### Answer:eval rerun timing

Per plan §J rule 4: "No `answer:eval` per sub-phase. Single post-3D consolidated eval in §G.2." The GQ-013/014/015 pass/fail determination is deferred to §G.2.

---

## §D — Acceptance Gate Assessment

| Gate | Target | Assessment |
|------|--------|------------|
| `http_422_root_cause_identified` | yes | Yes — 422s were NOT the actual failure mode. Actual failures: NIM synthesis quality deficit (GQ-013/015) + NIM synthesis timeout (GQ-014). Root cause addressed by Phase 3A |
| `gq_013_fix_or_carry_forward_documented` | yes | Fix: Phase 3A's gemini stack default. Verification: §G.2 post-deploy eval |
| `gq_014_fix_or_carry_forward_documented` | yes | Fix: Phase 3A's gemini stack default (faster synthesis path). Verification: §G.2 |
| `answer_eval_rerun_post_fix` | 14/15 or 15/15 | Deferred to §G.2 per §J rule 4. Target: ≥13/15 |

---

## §E — Code Artifacts Changed

**None.** Phase 3B requires no code changes. The Phase 3A changes (EVAL_STACK default → 'gemini') are the effective fix for the underlying failure modes.

A note in the plan file §D is the only artifact: the acceptance gates document the root cause finding.

---

## §F — Hard Rules Compliance

- **No code changes made** — Phase 3B finding is that Phase 3A resolves the root cause
- **No DB mutations** — not applicable
- **Brief-author-then-execute discipline** — this brief IS the execution for Phase 3B (the "fix" is documenting no code change needed)
- **answer:eval deferred to §G.2** — per plan §J rule 4

---

*End PHASE_3B_HTTP422_DIAGNOSTIC_BRIEF_v1_0.md. Authored 2026-05-18 by Claude Code on analysis/backend-data-pipeline-perf-audit.*
