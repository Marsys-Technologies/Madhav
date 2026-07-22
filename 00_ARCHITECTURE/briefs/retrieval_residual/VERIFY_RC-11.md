---
artifact: VERIFY_RC-11.md
residual: RC-11 (R-10 / CR-118) — mid-stream fast-fail tool errors
branch: res/rc11-cr118-fastfails
head_commit: abbe155e
verifier: independent VERIFIER agent (opus, high effort) — NOT the implementer
verified_at: 2026-07-23
verdict: ACCEPT
---

# VERIFY RC-11 — CR-118 mid-stream fast-fail tool errors

## Verdict: **ACCEPT**

The root cause is correctly identified, the fix is minimal and correct, the
regression tests genuinely reproduce and guard the defect (independently
re-verified), and CR-118 is marked RESOLVED with an honest, evidence-backed
trail. The one strict-verbatim element not yet discharged — a live re-probe of
the actual failing door (`/api/chat/consult`) *post-fix* — is genuinely
deploy-gated and folds into Wave R-C by the brief's own §F dependency graph
(exactly as RC-05's live discovery/remedy legs do). It was honestly flagged, not
shortcut. See §5 carry-condition.

## 1. DONE bar (brief §E RC-11), verbatim, vs. delivered

> **DONE:** each of the three resolves cleanly on a live trace (no fast-fail);
> CR-118 marked RESOLVED in `MARSYS_DEFECT_GAP_REGISTER` with evidence;
> regression tests added.

| DONE element | Status | Evidence |
|---|---|---|
| Each of the three resolves cleanly on a live trace (no fast-fail) | MET (every door reachable this session) + 1 deploy-gated leg carried to R-C | I re-ran all three deployed twins myself on 482012f1 (§4). CR-118's *origin* door `/api/chat/consult` re-probe is deploy-gated (§5). |
| CR-118 marked RESOLVED with evidence | MET | Register v3.10→3.11; CR-118 block lines 903–1032 + changelog. Full root-cause + fix + evidence trail. |
| Regression tests added | MET | Two files; I independently reproduced pre-fix failure + post-fix green (§3). |

## 2. Root cause — independently confirmed airtight

The implementer's diagnosis holds under direct inspection:

- `tool_name_bridge.ts:335` — `const chartId = typeof plan['chart_id'] === 'string' ? plan['chart_id'] : undefined`.
- `tool_name_bridge.ts:343-344` — for `cap.scope === 'per_chart'`, `args['chart_id']` is populated **solely** from `plan['chart_id']` (and the handler context arg at line 358 likewise). It is NOT sourced from `params`. So a plan lacking `chart_id` sends no chart_id to any per_chart handler.
- The three CR-118 tools are all per_chart in the bridge map: `msr_sql → marsys://tool/L2/query_signals`, `cgm_graph_walk → marsys://tool/L2/traverse_chart_graph`, `get_yoga_firings → marsys://tool/L1/get_yoga_firings`. Their handlers open with a synchronous `if (!chart_id) return {error:'chart_id is required', is_error:true}` — a pre-DB return, matching the observed ~4-6ms fast-fail exactly.
- `vector_search` is chart-agnostic (never reads chart_id), which is why it alone succeeded in the same request — the selective-failure signature the two live probes recorded.
- `consult/route.ts:674,827` — the `LegacyQueryPlanShape` `queryPlan` literal is the object handed to `executeWithCache(t, queryPlan, …)` → `tool.retrieve(plan, params)`. Pre-fix it carried no `chart_id`, so `plan['chart_id']` was `undefined` for every per_chart dispatch on this route regardless of the request's chart.
- The `ToolEvent` shape the probes cite (`name`/`status`/`ms`/`ok_count`/`err_count`) is unique to `consult/route.ts` in `platform/src` (grep-confirmed) — correctly locating both probes to the web-chat door, not the MCP door.

## 3. Regression tests — independently re-verified

Reverted ONLY the four source files to `main` (kept the new tests), reran:
```
Test Files  2 failed (2)
Tests  3 failed | 15 passed (18)
AssertionError: msr_sql plan.chart_id: expected undefined to be '482012f1-…'
```
This reproduces CR-118's exact symptom (`plan.chart_id === undefined` for the
per_chart tools). Restored the fix → `2 passed / 18 passed`. The
`cr118_chart_id_plan_regression.test.ts` test drives the real `POST` handler and
captures the actual `plan` object handed to `executeWithCache` — it exercises
the true code path, not a synthetic stand-in. `primitives.test.ts` adds the
header-only-chart_id case that the second (defense-in-depth) fix site closes.

tsc: `--noEmit` exit 0, clean. Neighboring suites: `src/app/api/chat/__tests__/`
+ `src/lib/__tests__/mcp/` = 19 files / 179 tests all pass — no collateral
breakage from adding the field.

## 4. Live spot-check — re-run by the verifier (not trusting transcripts)

Live, deployed connector, chart `482012f1-710e-4a25-994a-93821f5871aa`:
- `get_signals` (msr_sql-equiv) → full ranked signal payload, `is_error:false`, real data (9,946 signals, resolvable fact_ids).
- `ganita_yoga_firings_get` (get_yoga_firings-equiv) → 3 fired yogas (sasa/budha_aditya/vasi) with strengths, `is_error:false`.
- `get_cgm_subgraph` mode=convergence (cgm_graph_walk-equiv) → 10 hub nodes, 174 edges, topology summary, `is_error:false`.

All three deployed handlers are healthy when chart_id is supplied — confirming
the tools themselves are not the defect; the missing-chart_id plumbing on the
consult door was. Consistent with the implementer's analysis.

## 5. Carry-condition (not a REJECT, not a "carried-forward" violation)

`/api/chat/consult` (CR-118's origin door) was NOT re-probed live *post-fix*:
deployed `main@651c6478` does not carry this fix (branch unmerged/undeployed),
and this MCP-only session has no browser/session-cookie HTTP tool to hit that
route. This is a real, precisely-stated constraint — the live-trace-on-origin
leg structurally requires the fix to be deployed first.

The brief's §F places exactly this class of leg in **Wave R-C** (live
verification of the deployed cumulative state, "after R-A/R-B have merged +
deployed"), explicitly folding code-residual live legs (e.g. RC-05's
discovery/remedy traces) into that wave. RC-11's consult live re-probe is
identical and belongs there. **Acceptance is therefore conditioned on Wave R-C
re-probing `/api/chat/consult` on 482012f1 post-batched-deploy and confirming
`msr_sql`/`get_yoga_firings`/`cgm_graph_walk` no longer fast-fail** — the fix is
already merged into the deployed set at that point, and the regression tests
guard against re-introduction in the interim. This is sequencing per the brief,
not deferral of doable work.

## 6. Scope / must_not_touch compliance

Files changed (7): `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (may_touch, explicit),
`consult/route.ts`, `mcp/primitives/[tool]/route.ts`, `shared_types.ts`,
`router/types.ts` (all `platform/** source`, may_touch), plus two test files.
None touch the FROZEN orchestrator/WriterBase, `ga_*/bo_*/ka_*/ph_*/mi_*` writer
build logic, `chart_facts` semantics, LEL content, `kala_*`/gochara serving
semantics, or any D-4b branch. The primitives-route change preserves the
entitlement gate behavior (`if (!chartId)` still fires identically on null vs
undefined) and only additionally threads the resolved chartId onto queryPlan.
**No must_not_touch violation.**

## 7. Verifier's adversarial failure-mode hunt

- *Could params rescue chart_id in production, making the fix a no-op?* No —
  per_chart arg population reads `plan['chart_id']` (line 343), not params; the
  consult planner does not emit chart_id in per-tool params (it is a
  request-level scope). The regression test proves the real path yields
  `undefined` pre-fix.
- *Is the second fix site (primitives route) load-bearing or noise?* It is
  defense-in-depth, correctly labeled as NOT the CR-118 origin (every observed
  MCP tool def passes chart_id in params). Harmless, tested, honest.
- *Does the added field break any QueryPlan consumer?* No — declared optional on
  the shared/router types; tsc clean; 179 neighboring tests green.

---
**VERDICT: ACCEPT** — root cause fixed and proven, register RESOLVED with
evidence, regression tests independently re-verified, three tools confirmed
live-healthy on every reachable door. Carry the `/api/chat/consult` post-deploy
live re-probe into Wave R-C per §F (already the campaign's sequencing).
