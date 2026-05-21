---
artifact: PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0
canonical_id: PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN
version: 1.1
status: CLOSED — §4.A CLOSED (bd41f13); §4.B CLOSED (c63ef9f); §4.C CLOSED (abab885); §4.D CLOSED (d7ec853)
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
        status: CLOSED
        brief: briefs/PHASE_4B_DERIVED_ENRICHMENT_BRIEF_v1_0.md
        authored_on: 2026-05-19
        closed_on: 2026-05-19
        closing_commit_sha: c63ef9f
        scope: |
          Migration 059 adds 7 nullable derived columns to ephemeris_daily:
            dignity_d1, is_combust, combust_orb_deg, vargottama_today,
            sign_ingress_today, whole_sign_house, graha_yuddha_with.
          ephemeris_derivations.py pure-Python BPHS-canonical computation module.
          bootstrap_ephemeris.py: TRUE_NODE → MEAN_NODE Rahu fix + inline derived computation.
          enrich_ephemeris_daily.py: idempotent backfill for existing rows.
          query_ephemeris (4A tool) extended with derived_fields param.
          14 Python derivation unit tests + 5 new TS tests + GT.070-073 golden set.
          RUNBOOK_EPHEMERIS_REBUILD_v1_0.md delivered for native-supervised rebuild.
        outputs:
          - platform/migrations/059_ephemeris_derived_columns.sql (new)
          - platform/python-sidecar/pipeline/ephemeris_derivations.py (new)
          - platform/python-sidecar/pipeline/bootstrap_ephemeris.py (updated — MEAN_NODE + derived)
          - platform/python-sidecar/pipeline/enrich_ephemeris_daily.py (new)
          - platform/python-sidecar/pipeline/__tests__/test_ephemeris_derivations.py (new, 14 tests)
          - platform/src/lib/retrieve/query_ephemeris.ts (+derived_fields param)
          - platform/src/lib/retrieve/__tests__/query_ephemeris.test.ts (+5 tests)
          - platform/src/lib/router/retrieval_capability_spec.ts (entry rewrite)
          - platform/tests/eval/planner_golden_set.json (+4: GT.070-073)
          - platform/tests/eval/fixtures/regression_baseline.json (paired)
          - 00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md (new)
        boundary: |
          The brief delivers code + migration + runbook. It does NOT
          execute the 657K-row rebuild against production Cloud SQL.
          Native triggers post-merge per RUNBOOK §Steps.
        acceptance_results:
          tsc: GREEN
          ts_unit_tests: 12/12 PASS (5 new + 7 existing)
          python_pytest: 20/20 PASS (all BPHS spot-checks)
          migration_sql: REVIEWED — valid PostgreSQL with IF NOT EXISTS + transaction guard
          enrich_script_review: VERIFIED — LAG window for prior_sign + day-grouping
          planner_regression_gate: 2/2 PASS
          production_rebuild: DEFERRED to native (Path A recommended; ~4-6h)
        executor_scope_notes:
          - §4.C should import SIGNS+SIGN_TO_IDX from ephemeris_derivations (not re-declare)
          - §4.D should refine graha_yuddha to add latitude-difference check OR formally document longitude-only form
        depends_on: 4A (CLOSED at bd41f13)
      4C_panchanga:
        status: CLOSED
        closing_commit_sha: abab885
        closed_on: 2026-05-19
        brief: briefs/PHASE_4C_PANCHANGA_BRIEF_v1_0.md
        authored_on: 2026-05-19
        scope: |
          Migration 060 adds panchanga_daily + panchanga_daily_staging (73K rows expected).
          panchanga_derivations.py — pure-Python 5-limb computation (tithi/vara/nakshatra/yoga/karana).
          Imports SIGNS+SIGN_TO_IDX from ephemeris_derivations per §4.B executor note.
          bootstrap_panchanga.py uses swe.rise_trans for Bhubaneswar sunrise (20.27021N, 85.82966E, 45m).
          query_panchanga is the 28th retrieval tool. Filters by date/range/tithi/paksha/nakshatra/vara_lord/yoga/karana.
          PLANNER_PROMPT v2.0.4: new R-PA (Panchanga Anchor) rule + R-TC pairing-clause amendment + §4.26 few-shot.
          15 Python pytest cases + 5 TS vitest cases + GT.074-077 golden set (3 positive + 1 negative).
          RUNBOOK §4 panchanga bootstrap section added.
        outputs:
          - platform/migrations/060_panchanga_daily.sql (new)
          - platform/python-sidecar/pipeline/panchanga_derivations.py (new)
          - platform/python-sidecar/pipeline/bootstrap_panchanga.py (new)
          - platform/python-sidecar/pipeline/__tests__/test_panchanga_derivations.py (new, ~15 tests)
          - platform/src/lib/retrieve/query_panchanga.ts (new)
          - platform/src/lib/retrieve/__tests__/query_panchanga.test.ts (new, ~5 tests)
          - platform/src/lib/retrieve/index.ts (+1 entry)
          - platform/src/lib/router/retrieval_capability_spec.ts (+1 entry)
          - platform/src/lib/trace/types.ts (literal count 27 → 28)
          - 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md (R-PA rule + R-TC pairing-clause + §4.26)
          - 00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md (§4 panchanga bootstrap section)
          - platform/tests/eval/planner_golden_set.json (+4: GT.074-077)
          - platform/tests/eval/fixtures/regression_baseline.json (paired)
        boundary: |
          The brief delivers code + migration + runbook addendum. It does NOT
          execute the ~73K-row panchanga bootstrap against production Cloud SQL.
          Native triggers post-merge per RUNBOOK §4.
        acceptance_results:
          tsc: GREEN
          ts_unit_tests: 6/6 PASS query_panchanga + full retrieve suite 263 tests across 28 files
          python_pytest: 31/31 PASS (5 test classes — TestComputeTithi 8, TestComputeVara 4, TestComputeMoonNakshatra 5, TestComputeYoga 5, TestComputeKarana 9)
          migration_sql: REVIEWED — no autonomous DB execution
          planner_regression_gate: 2/2 PASS
          production_bootstrap: DEFERRED to native (~73K rows, ~30 min)
        executor_scope_notes_for_4D:
          - "Tithi boundary semantics are integer-floor, not nearest-rounding. At exactly 180° elongation, result is Krishna Pratipada (16), not Purnima (15). §4.D event-search should document its crossing-moment convention (swe.solcross/mooncross return exact JD when longitude equals target, not 'the day of crossing')."
          - "Vara/day-of-week computation requires IST datetime, not UTC. A 00:30 UTC sunrise = 06:00 IST same day; passing UTC datetime would yield wrong vara. §4.D sidecar /transit_search endpoint must use jd_to_ist_iso() conversion for any vara-relevant output."
        depends_on: 4A (bd41f13), 4B (c63ef9f)
      4D_transit_search:
        status: CLOSED
        brief: briefs/PHASE_4D_TRANSIT_SEARCH_BRIEF_v1_0.md
        authored_on: 2026-05-19
        closing_commit_sha: d7ec853
        scope: |
          query_transit_event retrieval tool (29th). Four event classes routed:
            ingress → ephemeris_daily.sign_ingress_today (§4.B-precomputed)
            station → retrogrades table (existing migration 016)
            aspect → sidecar POST /transit_search live compute
            conjunction → sidecar POST /transit_search live compute
          Sidecar uses swe.solcross/mooncross for Sun/Moon, day-step + bisection
          root-finding for other planets. ±10 year window cap. Lahiri sidereal.
          PLANNER_PROMPT v2.0.5: new R-TE (Transit Event) rule + §4.27 few-shot.
          Graha-yuddha docstring update — formally documents longitude-only as
          accepted Vedic approximation per §4.B executor scope-note (no code change).
          12 Python pytest cases + 5 TS vitest cases + GT.078-082 (4 positive + 1 negative).
          RUNBOOK §5 sidecar verification section. PHASE_4_CLOSE_v1_0.md sealing artifact.
          Also: revisit graha_yuddha latitude-difference check (per §4.B executor note)
          or document longitude-only form as accepted approximation.
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

**§4.A is CLOSED** (2026-05-19 at `bd41f13`). `query_ephemeris` tool live in RETRIEVAL_TOOLS registry, R-TC rule encoded in PLANNER_PROMPT_v2_0.md v2.0.3.

**§4.B is CLOSED** (2026-05-19 at `c63ef9f`). Migration 059 + 7 derived columns + MEAN_NODE Rahu fix + `ephemeris_derivations.py` + `enrich_ephemeris_daily.py` + `query_ephemeris` `derived_fields` param + 20 Python tests + 12 TS tests (5 new) + GT.070–073 + RUNBOOK_EPHEMERIS_REBUILD_v1_0.md all shipped. tsc clean, vitest 12/12, pytest 20/20, planner_regression_gate 2/2. Production 657K-row rebuild deferred to native per runbook — Path A recommended.

**§4.C is CLOSED** (2026-05-19 at `abab885`). Migration 060 + `panchanga_daily` + `panchanga_derivations.py` + `bootstrap_panchanga.py` + `query_panchanga` (28th tool) + R-PA rule + 31 Python pytests + 6 TS vitests (full retrieve suite 263 tests across 28 files) + GT.074-077 + RUNBOOK §4 all shipped. tsc clean, planner_regression_gate 2/2. Production ~73K-row bootstrap deferred to native per runbook. Two semantics carry-forwards captured in §B for §4.D (tithi integer-floor, vara IST datetime).

**§4.D is CLOSED** (2026-05-19 at `d7ec853`). `query_transit_event` (29th tool) routes four event classes: ingress → `ephemeris_daily.sign_ingress_today` (§4.B-precomputed), station → `retrogrades` (migration 016), aspect+conjunction → sidecar `/transit_search` live-compute using `swe.solcross`/`mooncross` for Sun/Moon + day-step bisection for other planets. ±10 year window cap. Lahiri throughout. R-TE rule in PLANNER_PROMPT v2.0.5 + §4.27 few-shot. Graha-yuddha docstring updated in `ephemeris_derivations.py` documenting longitude-only form as accepted Vedic approximation (resolves §4.B carry-forward; no code change). 12 Python pytests (12/12) + 5 TS vitests (5/5) + GT.078-082 + RUNBOOK §5 all shipped. tsc clean, planner_regression_gate 2/2. PHASE 4 EPHEMERIS ACCESSIBILITY CAMPAIGN CLOSED. Sealing artifact: `PHASE_4_CLOSE_v1_0.md`.

**Execution prompt to paste into Claude Code for §4.D:**

```
Read 00_ARCHITECTURE/briefs/PHASE_4D_TRANSIT_SEARCH_BRIEF_v1_0.md and execute it.

Start with:
git -C /Users/Dev/Vibe-Coding/Apps/Madhav-analysis checkout analysis/backend-data-pipeline-perf-audit
git -C /Users/Dev/Vibe-Coding/Apps/Madhav-analysis status

If branch is correct and working tree clean, proceed with the brief autonomously.
If not, STOP and report.

Hard constraints (re-stated from CLAUDE.md + master plan §C):
- Analysis branch only. Never touch Chat V2 files.
- No autonomous npm run answer:eval. Pre-commit verification only.
- Approved decisions in EPHEMERIS_ACCESSIBILITY_RESEARCH_v1_0.md §6 are locked.
- Reuse existing tables: ephemeris_daily.sign_ingress_today (§4.B) for ingress,
  retrogrades table (migration 016) for station. NO new migration in §4.D.
- Import SIGNS / SIGN_TO_IDX / NAKSHATRAS from existing modules per the
  established pattern (no re-declaration). §4.C executor honored this for
  panchanga; §4.D must continue.
- Tithi integer-floor convention + vara IST-datetime convention from §4.C
  carry forward to /transit_search endpoint output formatting.
- Pre-commit gates: tsc + TS vitest + Python pytest + planner_regression_gate.

After §4.D commit lands, author PHASE_4_CLOSE_v1_0.md per master plan §E + §6.1
of the brief. This SEALS the campaign.

When complete: report commit SHA + git log + gate results + confirmation that
PHASE_4_CLOSE_v1_0.md was authored + final tool count check (29 in all three
registries) + recommendation on whether to run operator data operations
(Path A rebuild + panchanga bootstrap) before or in parallel with the
consolidated answer:eval batch.
```

After §4.D closes AND `PHASE_4_CLOSE_v1_0.md` is authored, the campaign is sealed. Native then triggers (1) the operator data operations per `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md`, and (2) the consolidated answer:eval batch — these are the deferred operator-supervised steps that the discipline kept out of the brief executions.
