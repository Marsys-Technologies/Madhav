---
canonical_id: PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN
version: 1.1
status: ACTIVE — §4.A CLOSED; §4.B next
author: Claude (analysis stream)
authored_on: 2026-05-18
last_updated: 2026-05-19
campaign_name: Phase 4 Ephemeris Accessibility
mirror_pair: none
scope: analysis-stream
related:
  - EPHEMERIS_ACCESSIBILITY_RESEARCH_v1_0.md (research dossier, v1.1 APPROVED)
  - briefs/PHASE_4A_QUERY_EPHEMERIS_BRIEF_v1_0.md (sub-phase 4A brief)
  - briefs/PHASE_4B_DERIVED_ENRICHMENT_BRIEF_v1_0.md (to be authored after 4A close)
  - briefs/PHASE_4C_PANCHANGA_BRIEF_v1_0.md (to be authored after 4B close)
  - briefs/PHASE_4D_TRANSIT_SEARCH_BRIEF_v1_0.md (to be authored after 4C close)
two_stream_branch: analysis/backend-data-pipeline-perf-audit (must never touch Chat V2 files)
---

# Phase 4 — Ephemeris Accessibility Campaign

## §A Purpose

Make `ephemeris_daily` (657K rows · 1900–2100 daily · Lahiri sidereal) and the broader Swiss Ephemeris capability surface fully planner-reachable, so the query pipeline can enrich every non-natal question with transit context. Closes the gap surfaced at Phase 3 close (2026-05-18): the entire daily ephemeris table is unreachable by the planner today.

Bounded by `EPHEMERIS_ACCESSIBILITY_RESEARCH_v1_0.md §6 (approved decisions)`:

1. Rahu = MEAN_NODE (fix bootstrap inconsistency).
2. Panchanga observer = Bhubaneswar native birth location.
3. Combustion = BPHS classical thresholds.
4. `query_ephemeris` = single tool, optional date OR date_range.
5. Ayanamsha = Lahiri only.
6. House systems = Whole-Sign as peer; Placidus where already wired; Bhava-Chalit deferred.
7. **Transit-Context heuristic (R-TC)**: non-natal queries default to including `query_ephemeris` at priority 2.

## §B State tracker (live — updated at each sub-phase close)

```yaml
campaign:
  phase_4_ephemeris_accessibility:
    status: IN_PROGRESS
    started: 2026-05-18
    closed: null
    sub_phases:
      4A_query_ephemeris_tool:
        status: CLOSED
        brief: briefs/PHASE_4A_QUERY_EPHEMERIS_BRIEF_v1_0.md
        closed_on: 2026-05-19
        closing_commit_sha: bd41f13
        scope: |
          Wrap ephemeris_daily as a planner-reachable RetrievalTool.
          Encode R-TC transit-context rule in PLANNER_PROMPT.
          Pair golden_set + regression_baseline extension.
          Planner-only smoke test.
        outputs:
          - platform/src/lib/retrieve/query_ephemeris.ts (new)
          - platform/src/lib/retrieve/index.ts (+1 entry)
          - platform/src/lib/router/retrieval_capability_spec.ts (+1 entry)
          - platform/src/lib/trace/types.ts (+3 entries: query_ephemeris + classical_text_search + classical_attribution_lookup; closes trace-gap cosmetic residual)
          - 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md (+1 R-rule + 1 few-shot example)
          - platform/tests/eval/planner_golden_set.json (+5 entries GT.065-069)
          - platform/tests/eval/fixtures/regression_baseline.json (paired +5)
          - platform/src/lib/retrieve/__tests__/query_ephemeris.test.ts (new)
          - platform/tests/eval/r_tc_transit_context_smoke.ts (new)
        acceptance_results:
          tsc: GREEN
          unit_tests: 252/252 PASS (7 new query_ephemeris tests)
          planner_regression_gate: GREEN (2/2)
          planner_smoke_live: DEFERRED — requires live API keys; run post-push
        commit_target: feat(retrieval): query_ephemeris tool + R-TC transit-context rule (§4.A)
      4B_derived_enrichment:
        status: PENDING — author after 4A closes
        scope: |
          Migration 059 + bootstrap enrichment for combust, dignity_d1,
          vargottama, sign_ingress, graha_yuddha, whole_sign_house columns.
          Includes TRUE_NODE → MEAN_NODE Rahu fix + 657K row rebuild.
          Extend query_ephemeris with derived_fields param.
        depends_on: 4A
      4C_panchanga:
        status: PENDING — author after 4B closes
        scope: |
          query_panchanga retrieval tool reading sunrise-anchored
          tithi/vara/karana/yoga/nakshatra at Bhubaneswar observer.
          Migration + precompute table or sidecar live-compute.
        depends_on: 4B
      4D_transit_search:
        status: PENDING — author after 4C closes
        scope: |
          query_transit_event retrieval tool. Sidecar /transit_search endpoint.
          Ingress + aspect + conjunction + station search using swe.solcross/mooncross
          for Sun/Moon, root-finding for others. ±10 year window cap.
        depends_on: 4C
```

## §C Hard constraints

- **Branch**: every commit lands on `analysis/backend-data-pipeline-perf-audit`. Never on a Chat V2 branch. Per two-stream policy declared 2026-05-17.
- **Files OFF-LIMITS** (Chat V2 ownership): `platform/src/components/consume/*`, `platform/src/components/chat/*`, `platform/tests/{unit,integration,e2e,component,components}/chat-v2/*`, `00_ARCHITECTURE/CHAT_V2_*`, `00_ARCHITECTURE/chat_v2_briefs/*`, `CHAT_V2_PROGRESS.md`.
- **Cloud Run**: NO redeploy from sub-phase commits alone. Production answer:eval runs ONLY after the campaign batch ships (per the consolidated retrieval-tools eval discipline declared 2026-05-17). The §4.A executor must NOT run `npm run answer:eval` autonomously.
- **Approved decisions** (§A) are locked. Any deviation requires explicit native re-approval.
- **MEAN_NODE Rahu fix** is §4.B scope, not §4.A. §4.A reads `ephemeris_daily` as-is, even with TRUE_NODE Rahu. Hygiene only.

## §D Resume protocol

If a Claude Code session opens mid-campaign, it must:

1. Read this master plan (you are here).
2. Read `EPHEMERIS_ACCESSIBILITY_RESEARCH_v1_0.md` for design context.
3. Read §B state tracker — pick the first `AUTHORED_READY_TO_EXECUTE` sub-phase brief and execute it. Skip `PENDING` ones.
4. Run `git status` first. If working tree has uncommitted analysis-stream changes from a prior partial run, STOP and report. If clean, proceed.
5. After successful close: update §B status block to `CLOSED`, append closing-commit SHA, mark the next sub-phase brief as `AUTHORED_READY_TO_EXECUTE` (if Claude is also authoring the next brief), or `PENDING` (if author phase comes later).

## §E Exit criteria (campaign close)

Campaign closes when:

- §4.A through §4.D all status=CLOSED, OR
- Native explicitly directs partial-close at any milestone (e.g., "ship 4A + 4B, defer 4C and 4D").

At close, author `PHASE_4_CLOSE_v1_0.md` sealing artifact with:

- Final per-sub-phase status + commit SHAs.
- Production deploy commit (or "deferred — analysis-only campaign" if no deploy).
- answer:eval result against the consolidated retrieval-tools batch.
- Lessons captured to memory.

## §F Where to start

**§4.A is CLOSED** (2026-05-19). `query_ephemeris` tool live in RETRIEVAL_TOOLS registry, R-TC rule encoded in PLANNER_PROMPT_v2_0.md v2.0.3.

**Next: §4.B** — author `briefs/PHASE_4B_DERIVED_ENRICHMENT_BRIEF_v1_0.md`. Depends on 4A outputs (query_ephemeris tool + ephemeris_daily schema). Key 4B scope: migration 059 for derived columns, TRUE_NODE → MEAN_NODE Rahu fix, 657K row rebuild, `derived_fields` param extension for query_ephemeris.

After §4.A closes (commit lands on analysis branch), come back to Cowork and I'll author the §4.B brief based on what §4.A delivered.
