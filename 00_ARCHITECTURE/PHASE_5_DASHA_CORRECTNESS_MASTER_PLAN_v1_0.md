---
canonical_id: PHASE_5_DASHA_CORRECTNESS_MASTER_PLAN
version: 1.0
status: ACTIVE — §5A AUTHORED_READY_TO_EXECUTE
author: Claude (analysis stream)
authored_on: 2026-05-19
campaign_name: Phase 5 Dasha Correctness
mirror_pair: none
scope: analysis-stream
related:
  - DASHA_CORRECTNESS_RESEARCH_v1_0.md (research dossier, v1.1 APPROVED)
  - briefs/PHASE_5A_DASHA_TOOL_BRIEF_v1_0.md (sub-phase 5A brief)
  - briefs/PHASE_5B_DASHA_DISCIPLINE_BRIEF_v1_0.md (to be authored after 5A close)
  - briefs/PHASE_5C_DASHA_VALIDATOR_BRIEF_v1_0.md (to be authored after 5B close)
two_stream_branch: analysis/backend-data-pipeline-perf-audit
---

# Phase 5 — Dasha Correctness Campaign

## §A Purpose

Eliminate the "wrong next/upcoming Vimshottari MD" hallucination class. The data is correct everywhere it's stored; the failure lives in five layers of how synthesis reaches the data. This campaign closes all five — discoverability + delivery + grounding-discipline + post-synthesis validation.

Anchored on `DASHA_CORRECTNESS_RESEARCH_v1_0.md §6` (approved decisions):

1. Validator: silent retry × 2 then hard `VALIDATOR_FAILURE`.
2. Synthesis gate: all 4 templates.
3. `query_dasha_periods` as a separate 30th tool.
4. Multi-system from day one (Vimshottari/Yogini/Chara); validator Vimshottari-only initially.
5. Baseline audit as Stage 0 of §5A.

## §B State tracker (live — updated at each sub-phase close)

```yaml
campaign:
  phase_5_dasha_correctness:
    status: IN_PROGRESS
    started: 2026-05-19
    closed: null
    sub_phases:
      5A_dasha_tool_plus_planner:
        status: AUTHORED_READY_TO_EXECUTE
        brief: briefs/PHASE_5A_DASHA_TOOL_BRIEF_v1_0.md
        scope: |
          Stage 0: baseline audit of "wrong-next-MD" failure rate on the
          last 50 dasha-related audit_events rows (one-off measurement).
          Stage 1: RCS extension — advertise dasha categories in
          chart_facts_query optimal patterns + extend the TS query to
          support as_of_date / from_date filters on JSON dates.
          Stage 2: query_dasha_periods retrieval tool (30th in registry)
          with system / level / as_of_date / next_count / prev_count /
          md_lord / ad_lord / from_date / to_date / limit params.
          Default empty params returns today's chain + next 3 MDs.
          Stage 3: R-DA (Dasha Anchor) planner rule + §4.28 few-shot
          example.
          Stage 4: Pair golden_set + regression_baseline extension
          (GT.083-086 — current/next/specific-lord/negative-natal).
          Stage 5: Planner-only smoke test (mirrors §4.A pattern).
        outputs:
          - platform/src/lib/retrieve/query_dasha_periods.ts (new)
          - platform/src/lib/retrieve/__tests__/query_dasha_periods.test.ts (new)
          - platform/src/lib/retrieve/chart_facts_query.ts (extend as_of_date / from_date)
          - platform/src/lib/retrieve/__tests__/chart_facts_query.test.ts (extend)
          - platform/src/lib/retrieve/index.ts (+1 entry)
          - platform/src/lib/router/retrieval_capability_spec.ts (chart_facts_query desc update + query_dasha_periods entry)
          - platform/src/lib/trace/types.ts (literal count 29 → 30)
          - 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md (R-DA rule + §4.28 few-shot)
          - platform/tests/eval/planner_golden_set.json (+4: GT.083-086)
          - platform/tests/eval/fixtures/regression_baseline.json (paired)
          - 00_ARCHITECTURE/DASHA_BASELINE_AUDIT_v1_0.md (Stage 0 baseline snapshot)
        acceptance:
          - tsc green
          - all unit tests pass (5+ new query_dasha_periods + 3+ chart_facts_query extensions)
          - planner-only smoke 4/4 PASS on GT.083-086
          - planner_regression_gate green (no drops on existing 82-entry set)
          - Baseline audit doc captured with N samples + wrong-rate %
        commit_target: feat(dasha): query_dasha_periods tool + R-DA rule + chart_facts_query dasha extension (§5A)
      5B_synthesis_dasha_gate:
        status: PENDING — author after 5A closes
        scope: |
          DASHA DISCIPLINE GATE added to all 4 synthesis prompt templates
          (predictive / factual / holistic / remedial). Mandates DSH.V.NNN
          citation for any next/previous/upcoming dasha claim. Forbids
          extrapolating from generic Vimshottari knowledge when bundle
          rows are present. Emits [EXTERNAL_COMPUTATION_REQUIRED] when
          rows missing.
        depends_on: 5A
      5C_dasha_validator:
        status: PENDING — author after 5B closes
        scope: |
          checkpoint_dasha.ts post-synthesis validator. Extracts dasha
          claims via regex; cross-checks against chart_facts dasha
          rows; on mismatch: silent retry × 2 then hard
          VALIDATOR_FAILURE per native-approved decision §6.1.
          Vimshottari-only initially; Yogini/Chara extension queued
          as follow-up.
        depends_on: 5B
```

## §C Hard constraints

- **Branch**: every commit lands on `analysis/backend-data-pipeline-perf-audit`. Never on a Chat V2 branch. Per two-stream policy.
- **Files OFF-LIMITS** (Chat V2 ownership): same globs as Phase 4 — `platform/src/components/consume/*`, `platform/src/components/chat/*`, `platform/tests/{unit,integration,e2e,component,components}/chat-v2/*`, `00_ARCHITECTURE/CHAT_V2_*`, `00_ARCHITECTURE/chat_v2_briefs/*`, `CHAT_V2_PROGRESS.md`.
- **Cloud Run**: NO redeploy from sub-phase commits alone. Production answer:eval runs ONLY at campaign close, batched with any other queued retrieval-tools changes per consolidated-batch discipline declared 2026-05-17.
- **Approved decisions** in dossier §6 are locked. Any deviation requires explicit native re-approval.
- **No autonomous `npm run answer:eval`**. Pre-commit gates only.
- **Reuse existing infra**: chart_facts has all 50 dasha rows (no new migration needed in 5A); checkpoint pattern exists in `platform/src/lib/checkpoints/` (5C extends it, doesn't reinvent).

## §D Resume protocol

Same pattern as Phase 4:

1. Read this master plan.
2. Read `DASHA_CORRECTNESS_RESEARCH_v1_0.md` for design context.
3. Read §B state tracker — pick first `AUTHORED_READY_TO_EXECUTE` sub-phase; skip `PENDING`.
4. `git status` first. If working tree dirty, STOP and report.
5. On successful close: update §B `status: CLOSED` + `closing_commit_sha`; the next sub-phase brief is authored in a separate Cowork session.

## §E Exit criteria (campaign close)

Closes when:

- §5A through §5C all `status: CLOSED`, OR
- Native explicitly directs partial-close (e.g., "ship 5A + 5B, defer 5C").

At close, author `PHASE_5_CLOSE_v1_0.md` per the Phase 4 precedent — sub-phase table, baseline-vs-post-campaign rate comparison, lessons captured to memory.

## §F Where to start

**§5A is AUTHORED_READY_TO_EXECUTE.** Brief at `briefs/PHASE_5A_DASHA_TOOL_BRIEF_v1_0.md`.

Execution prompt to paste into Claude Code:

```
Read 00_ARCHITECTURE/briefs/PHASE_5A_DASHA_TOOL_BRIEF_v1_0.md and execute it.

Start with:
git -C /Users/Dev/Vibe-Coding/Apps/Madhav-analysis checkout analysis/backend-data-pipeline-perf-audit
git -C /Users/Dev/Vibe-Coding/Apps/Madhav-analysis status

If branch is correct and working tree clean, proceed with the brief
autonomously. If not, STOP and report.

Hard constraints (re-stated from CLAUDE.md + master plan §C):
- Analysis branch only. Never touch Chat V2 files.
- No autonomous npm run answer:eval. Pre-commit verification only.
- Approved decisions in DASHA_CORRECTNESS_RESEARCH_v1_0.md §6 are locked.
- No new migration in §5A — chart_facts already has 50 dasha_vimshottari rows.
- Pre-commit gates: tsc + TS vitest + planner_regression_gate +
  Stage 0 baseline audit doc emitted.

When complete: report commit SHA + git log + gate results + baseline
audit findings + any §5B/5C scope adjustments suggested by §5A execution.
```

After §5A closes, return to Cowork and I'll author the §5B brief (synthesis prompt gate) based on what §5A delivered.
