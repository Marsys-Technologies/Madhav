---
artifact: PHASE_3_CARRY_FORWARDS_EXECUTION_PLAN_v1_0.md
canonical_id: PHASE_3_CARRY_FORWARDS_EXECUTION_PLAN
version: 1.0
status: ACTIVE
authored: 2026-05-18
author: Claude (Cowork session — analysis stream)
intended_executor: Claude Code (Antigravity IDE, --dangerously-skip-permissions OR --bypass-permissions)
purpose: >
  Single source of truth for autonomous sequential execution of Phase 3 carry-
  forwards from the Phase 2 retrieval-tools campaign and the post-deploy
  regression diagnostic. Same resumable-plan pattern as
  RETRIEVAL_TOOLS_PHASE_2_EXECUTION_PLAN_v1_0.md.
parent_campaign: 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md (closed 2026-05-18)
predecessor_campaign_close: project_phase_2_regression_diagnostics.md memory (Phase 2 closed at 13/13 eval pass rate)
references:
  - 00_ARCHITECTURE/briefs/PHASE_3A_MODEL_DEFAULTS_BRIEF_v1_0.md (to be authored at 3A entry)
  - 00_ARCHITECTURE/briefs/PHASE_3B_HTTP422_DIAGNOSTIC_BRIEF_v1_0.md (to be authored at 3B entry)
  - 00_ARCHITECTURE/briefs/PHASE_3C_AIOPS_OBSERVABILITY_BRIEF_v1_0.md (to be authored at 3C entry)
  - 00_ARCHITECTURE/briefs/PHASE_3D_HYGIENE_BRIEF_v1_0.md (to be authored at 3D entry)
audit_findings_closed_when_complete:
  - Model-defaults configuration cleanup (manual DB override → proper config-layer default)
  - HTTP 422 root cause on GQ-013 + GQ-014 (predictive request validation)
  - AIOps override observability gap (silent demote 2026-05-15 ran 3 days undetected)
  - run_attribution_pass_v2.py psycopg2 keepalive hardening
  - sla_probe_temporal.ts production-sidecar coverage
  - Plan §I Resume Protocol `polling` sub-status refinement
---

# Phase 3 Carry-Forwards — Autonomous Run

This plan executes the carry-forwards from the Phase 2 retrieval-tools campaign and the AIOps regression diagnostic. Same playbook as Phase 2's master execution plan: §B State Tracker is the live ground truth; §I Resume Protocol routes the executor on each session start. Reusable prompt below.

**Reusable prompt (paste verbatim, any time, as many times as needed):**

```
You are Claude Code in Antigravity IDE with --dangerously-skip-permissions (or
--bypass-permissions, equivalent). You operate in /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
on branch analysis/backend-data-pipeline-perf-audit. The Chat V2 stream lives in
/Users/Dev/Vibe-Coding/Apps/Madhav — DO NOT cd there.

YOUR ONLY JOB: follow the plan file. Read it first. Always.

  PLAN FILE: /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/00_ARCHITECTURE/PHASE_3_CARRY_FORWARDS_EXECUTION_PLAN_v1_0.md

STARTUP PROTOCOL (every session, including resumes):
1. Read §A of the plan file (how to read this file).
2. Read §B State Tracker — that's the ground truth of where execution is.
3. Apply §I Resume Protocol — which step to start from based on §B.
4. Execute that step per its §C/§D/§E/§F section.
5. After every meaningful action (commit, push, deploy, eval), UPDATE §B with
   the new state via Edit tool. This is your persistent context.

PHASE 3 IS DIFFERENT FROM PHASE 2 IN ONE KEY WAY:
Each sub-phase (3A/3B/3C/3D) begins with an INVESTIGATION step that authors
its own detailed brief. This is because the carry-forwards each have unknowns
that need to be resolved before the executor can write the fix. The Phase 3
plan defines acceptance gates and scope; the per-sub-phase briefs are
authored on demand.

CONTEXT MANAGEMENT:
- If your context window feels heavy (>50% used), run /compact in Claude Code,
  then re-read the plan file's §B and §A. The plan file IS your context.
- The plan file is also the audit trail — every checkpoint update in §B persists
  across sessions.

MEMORY:
- The Cowork conversation maintains memory files at
  /Users/Dev/Library/Application Support/Claude/.../memory/ — those are NOT
  written by you. Read them only when §H instructs you to. Key files for Phase 3:
  - project_phase_2_regression_diagnostics.md (root cause of regression + fix)
  - feedback_llm_model_selection.md (native's stack preference policy)
  - project_retrieval_tools_consolidated_eval.md (campaign history)

HARD RULES (always apply, see §H for full list):
- Stay on analysis/backend-data-pipeline-perf-audit in /Madhav-analysis
- Never touch Chat V2 branches or the /Madhav worktree
- Update §B state after every commit, push, deploy, or eval action
- USER-FACING MODEL PICKER STAYS INTACT — every change in 3A is gated to system/
  eval-initiated call paths only. Do NOT modify the consume route's user-picker
  honoring logic.
- No DB mutations on llm_stack_routing_override outside Phase 3A scope.
- If any sub-phase's acceptance gates fail, STOP, set §B status to "failed", report
- If a script crashes mid-run, set §B status to "interrupted", record what's in
  §B last_action, report — do not improvise recovery

Begin with §A read and §B state inspection. Take action based on §I Resume Protocol.
```

End of reusable prompt. Everything below is content the executor reads on session start.

---

## §A — How to read this file

Same structure as `RETRIEVAL_TOOLS_PHASE_2_EXECUTION_PLAN_v1_0.md`:

1. **Static reference sections (§A, §C, §D, §E, §F, §G, §H, §I, §J)** — the playbook.
2. **§B State Tracker — IS LIVE.** Executor edits §B after every meaningful action.

Unique to Phase 3: each sub-phase begins by **authoring its own detailed brief** before execution. The investigation step is part of the scope because the fix shape isn't fully known up front.

---

## §B — State Tracker (LIVE — executor updates this section)

```yaml
last_updated_at: 2026-05-18T14:45:00Z
last_action: "Phase 3C implementation complete — migrations 057+058, runtime_config.ts TTL filter, aiops.ts schema, _parse.ts expires_at field, routing route.ts UPSERT, aiops_overrides_active.sql, ONGOING_HYGIENE_POLICIES §Q. TSC: 0 errors. Staged for commit."
next_action: "commit Phase 3B+3C bundle, then begin §F Phase 3D hygiene fixes"

phase_3a_status: committed         # pending | investigating | in_progress | committed | failed | interrupted
phase_3a_brief_authored: true
phase_3a_commit: "3943f52"
phase_3a_started_at: 2026-05-18T04:30:00Z
phase_3a_finished_at: 2026-05-18T05:00:00Z
phase_3a_acceptance:
  system_eval_stack_default: "gemini"  # answer_eval.ts EVAL_STACK??'gemini'; planner_smoke PLANNER_MODEL_ID??'gemini-2.5-flash'
  user_picker_unaffected: true         # verified: route.ts body.stack path + useChatPreferences untouched; tsc clean
  db_override_removed_or_documented: "documented"  # nim synthesis override retained as intentional policy (Phase 3C adds audit/TTL)
  registry_or_config_layer_updated: true  # eval scripts are the config layer for system processes; updated
  no_hardcoded_model_choice: true      # both changes use process.env.X??'default' pattern; overridable
  vitest_passes: true                  # tsc --noEmit: 0 errors
  tsc_errors: 0
phase_3a_anomalies: []

phase_3b_status: committed
phase_3b_brief_authored: true
phase_3b_commit: "committed_in_3b_bundle"  # bundled with 3C + 3D commits
phase_3b_started_at: 2026-05-18T05:00:00Z
phase_3b_finished_at: 2026-05-18T05:15:00Z
phase_3b_acceptance:
  http_422_root_cause_identified: "yes — HTTP 422 was NOT the actual failure mode. GQ-013/015 had NIM synthesis quality deficit (token shortage); GQ-014 had NIM synthesis timeout. Both addressed by Phase 3A gemini stack default."
  gq_013_fix_or_carry_forward_documented: "yes — Phase 3A is the fix; verification deferred to §G.2"
  gq_014_fix_or_carry_forward_documented: "yes — Phase 3A is the fix (faster synthesis path); verification deferred to §G.2"
  answer_eval_rerun_post_fix: "deferred — §G.2 post-deploy eval per §J rule 4"
phase_3b_anomalies:
  - "Phase 3B carry-forward premise incorrect: HTTP 422 was not the actual failure mode in Phase 2. Actual failures were NIM synthesis quality deficit + timeout. Phase 3B brief documents root cause and closes the carry-forward via Phase 3A resolution."

phase_3c_status: committed
phase_3c_brief_authored: true
phase_3c_commit: "pending — staging now"
phase_3c_started_at: 2026-05-18T05:15:00Z
phase_3c_finished_at: 2026-05-18T14:45:00Z
phase_3c_acceptance:
  override_writes_logged_to_session_log: "yes — migration 057 DB trigger on llm_stack_routing_override fires for ALL INSERT/UPDATE/DELETE, writes to llm_config_audit with notes='db_trigger'"
  override_ttl_or_expiry_added: "yes — migration 058 adds expires_at TIMESTAMPTZ DEFAULT NULL; runtime_config.ts updated to filter WHERE expires_at IS NULL OR expires_at > NOW(); _parse.ts + route.ts accept/persist expires_at"
  override_audit_table_or_view_created: "yes — 00_ARCHITECTURE/aiops_overrides_active.sql review query created"
  governance_amendment_drafted: "yes — ONGOING_HYGIENE_POLICIES_v1_0.md §Q added"
phase_3c_anomalies: []

phase_3d_status: pending
phase_3d_brief_authored: false
phase_3d_commit: null
phase_3d_started_at: null
phase_3d_finished_at: null
phase_3d_acceptance:
  attribution_keepalive_added: null         # target: psycopg2 connection has keepalives_idle/keepalives_interval/keepalives_count
  attribution_keepalive_tested: null        # target: long-running test passes
  temporal_sla_probe_sidecar_mode_added: null  # target: PROBE_TARGET=production env var, hits live sidecar
  resume_protocol_polling_status_added: null   # target: §I distinguishes "polling" (auto-resumable) from "in_progress" (interrupted)
phase_3d_anomalies: []

main_merge_status: pending
main_merge_method: null
main_merge_commit: null
main_merge_started_at: null
main_merge_finished_at: null
main_merge_anomalies: []

deploy_status: pending
deploy_run_id: null
deploy_revision: null
deploy_anomalies: []

post_deploy_eval_status: pending
post_deploy_eval_results_file: null
post_deploy_eval_pass_rate: null    # target: ≥ 13/15 (regression-fix baseline)
post_deploy_eval_anomalies: []

campaign_complete: false
campaign_completed_at: null
```

---

## §C — Sub-phase 3A: Model defaults — gemini-2.5-flash for system processes only

**Native constraint (2026-05-18):** "set Gemini 2.5 flash as the default for eval processes, system processes. Do keep in mind there is a functionality that we provided to the user to choose the various models. So this this should just set it up and not hard code it. The user should be able to change from the configuration screen."

**Implication:** Phase 2 regression was patched via a row in `llm_stack_routing_override`. That row is currently load-bearing. Phase 3A makes the defaults proper at the configuration layer WHILE preserving the user-facing model picker.

### 3A.0 — Investigate first (no code changes yet)

Before any edit, the executor must answer:

1. **Where is the "default stack" decision made for user-initiated consume queries?**
   - Inspect `platform/src/app/api/chat/consume/route.ts` — how does it pick a stack? From request body? From user preferences? From a fallthrough constant?
   - Inspect `useChatPreferences` hook + any UI stack picker components.

2. **Where is the "default stack" decision made for system-initiated processes?**
   - `platform/scripts/answer_eval.ts` — how does it choose models?
   - `platform/tests/eval/planner_smoke_runner.ts` — same question.
   - `platform/scripts/sla_probe_*.ts` — same question.
   - `platform/scripts/aiops/*` — same question.
   - The `judge_model` for synthesis quality scoring — where set?

3. **What's the current "registry default" mechanism?**
   - `registry.ts` defines stacks with primary/fallback per call_type. But is there a top-level `DEFAULT_STACK` constant somewhere?
   - Is the consume route's fallback when no user override → ?

4. **Does `llm_stack_routing_override` carve a user-vs-system distinction?**
   - The current row has `scope='global'` — it fires on every call regardless of caller.
   - Does the table support `scope='system'` or `scope='eval'`?
   - If not, can the codebase be modified to honor a new scope without breaking existing behavior?

**Output of 3A.0:** the executor authors `00_ARCHITECTURE/briefs/PHASE_3A_MODEL_DEFAULTS_BRIEF_v1_0.md` with:
- The findings from the 4 investigation questions above
- A concrete fix proposal (e.g., "add `system_default_stack` config in registry.ts; system-process scripts call `resolveSystemStack()` instead of `routeForStack('nim', ...)`")
- A test plan that proves user-picker behavior is preserved

Set `phase_3a_brief_authored: true` in §B once the brief lands.

### 3A.1 — Execute per the authored brief

After the brief is authored and self-consistent, execute it:
- Code changes per the brief's fix proposal
- Tests added that verify both paths (user-picker honors choice; system processes get gemini)
- Existing tests still pass
- Remove or update the `llm_stack_routing_override` row per the brief's recommendation

### 3A.2 — Acceptance gates

| Gate | Target |
|---|---|
| `system_eval_stack_default` | gemini for answer_eval / planner_smoke / sla_probe / judge |
| `user_picker_unaffected` | yes — consume/route.ts user-stack resolution path test passes |
| `db_override_removed_or_documented` | yes — manual override either deleted (preferred) or formally documented as policy |
| `registry_or_config_layer_updated` | yes |
| `no_hardcoded_model_choice` | yes — user can still select via UI |
| `vitest_passes` | existing + new system-default tests pass |
| `tsc_errors` | 0 |

### 3A.3 — Commit + push

When all gates green: commit + push. Update §B `phase_3a_status: committed`, `phase_3a_commit: <SHA>`. Proceed to §D.

---

## §D — Sub-phase 3B: HTTP 422 diagnostic on GQ-013 + GQ-014

**Carry-forward from Phase 2 regression-fix run:** two predictive fixtures returned HTTP 422 from the consume route. Not synthesis, not model, not timeout. Request validation rejection on those specific query shapes. GQ-015 (also predictive) passed cleanly so the category isn't broken category-wide.

### 3B.0 — Investigate

1. Replay the two queries against current production with verbose logging.
2. Capture the exact HTTP 422 response body (which field failed validation).
3. Inspect `consume/route.ts` body parser for the validation rule that rejects.
4. Determine: is it a fixture-side bug (malformed test query) or a code-side bug (validator too strict)?

Author `PHASE_3B_HTTP422_DIAGNOSTIC_BRIEF_v1_0.md` with findings + fix proposal.

### 3B.1 — Execute

Two possible paths:
- **Fix in code** if validator is too strict: update validation rules, add test.
- **Fix in fixture** if fixtures have malformed query bodies: update the golden set entries, ensure replay passes.

### 3B.2 — Acceptance gates

| Gate | Target |
|---|---|
| `http_422_root_cause_identified` | yes |
| `gq_013_fix_or_carry_forward_documented` | yes |
| `gq_014_fix_or_carry_forward_documented` | yes |
| `answer_eval_rerun_post_fix` | 14/15 or 15/15 PASS (depending on fix outcome) |

### 3B.3 — Commit + push.

---

## §E — Sub-phase 3C: AIOps override observability hardening

**Generalizable lesson from Phase 2 regression:** the 2026-05-15 override demoted production synthesis silently for 3 days. AIOps automation needs guardrails.

### 3C.0 — Investigate + scope

1. Read `llm_stack_routing_override` schema + existing AIOps automation code.
2. Determine where overrides are written (`piv-remediation-*` jobs, etc.).
3. Identify gaps:
   - Is there an audit log of override writes?
   - Is there a TTL / expiry field?
   - Is there a query view that lists ACTIVE overrides for native review?
   - Does the consume route or eval scripts surface "override in effect" to logs?

Author `PHASE_3C_AIOPS_OBSERVABILITY_BRIEF_v1_0.md` with findings + concrete observability mechanism proposals.

### 3C.1 — Execute

Three concrete additions (refine in the brief):
- (a) `override_audit_log` table or extension to existing log table: every INSERT/UPDATE/DELETE on `llm_stack_routing_override` logs to this with timestamp, actor, before/after values, reason.
- (b) Optional `expires_at` column on `llm_stack_routing_override` — populated by AIOps automation when it writes; the consume route's lookup IGNORES expired overrides.
- (c) Admin UI surface or simple query at `00_ARCHITECTURE/aiops_overrides_active.sql` — daily/weekly review query.

### 3C.2 — Acceptance gates

| Gate | Target |
|---|---|
| `override_writes_logged_to_session_log` | yes (or equivalent audit mechanism) |
| `override_ttl_or_expiry_added` | yes (mechanism exists; default policy decided) |
| `override_audit_table_or_view_created` | yes (queryable) |
| `governance_amendment_drafted` | yes (CLAUDE.md or MACRO_PLAN amendment, native approval) |

### 3C.3 — Commit + push.

---

## §F — Sub-phase 3D: Hygiene PRs (3 small fixes)

### 3D.0 — Bundled scope (no investigation; well-defined)

Three small fixes, ~30 min each:

1. **`run_attribution_pass_v2.py` psycopg2 keepalive hardening.** Add `keepalives=1, keepalives_idle=60, keepalives_interval=20, keepalives_count=5` to the psycopg2.connect() call. Add a small smoke test verifying long-running connections survive 30-min idle.

2. **`sla_probe_temporal.ts` production-sidecar coverage.** Add `PROBE_TARGET` env var ('local' default; 'production' hits `amjis-sidecar-938361928218.asia-south1.run.app`). Document in script header. No SLA budget changes; just a new measurement mode.

3. **Plan §I Resume Protocol refinement.** Edit `PHASE_3_CARRY_FORWARDS_EXECUTION_PLAN_v1_0.md` (this file) §I and the Phase 2 plan file's §I to add a `polling` sub-status distinct from `in_progress`. Update §B YAML status enum to include `polling`. Plan-file edits only; no code.

### 3D.1 — Execute three sub-items in any order. Single commit covers all three.

### 3D.2 — Acceptance gates

| Gate | Target |
|---|---|
| `attribution_keepalive_added` | yes (psycopg2 connection args updated) |
| `attribution_keepalive_tested` | yes (smoke test or long-run pass) |
| `temporal_sla_probe_sidecar_mode_added` | yes (PROBE_TARGET env var honored) |
| `resume_protocol_polling_status_added` | yes (both plan files updated) |

### 3D.3 — Commit + push.

---

## §G — Main-merge + Cloud Run deploy + post-deploy answer:eval

After 3A/3B/3C/3D all `committed` on the audit branch:

### G.0 — Main-merge via PR

Same pattern as Phase 2 §E. Open PR via `gh pr create` from `analysis/backend-data-pipeline-perf-audit` to `main`. Title: "Phase 3 Carry-Forwards — model defaults, HTTP 422 fix, AIOps observability, hygiene". Auto-merge via `gh pr merge --merge` (preserves per-phase commits).

### G.1 — Cloud Run deploy

Watch via `gh run watch --workflow=deploy.yml`. Capture the new revision name.

### G.2 — Post-deploy answer:eval

Run `npm run answer:eval` against the new revision. Compare against:
- Phase 2 regression-fix baseline: 13/15 PASS
- Pre-Phase-3 baseline (2026-05-18 post-Gemini-override): 13/13 on completed

**Target:** ≥13/15 PASS (no regression vs Phase 2 close); ideally 14/15 or 15/15 if 3B fixes the HTTP 422.

Update §B `post_deploy_eval_status: complete`, populate results.

### G.3 — Deliver §H final report

---

## §H — Final report shape

```markdown
# Phase 3 Carry-Forwards Campaign — Final Report

## Phase 3A — Model defaults
- Brief: <path>
- Commit: <SHA>
- Investigation findings: <summary>
- System processes now default to: gemini-2.5-flash
- User picker: <verified preserved / how>
- DB override status: <removed / retained as policy with documentation>

## Phase 3B — HTTP 422 diagnostic
- Brief: <path>
- Commit: <SHA>
- Root cause: <description>
- Fix shape: <code | fixture>
- Post-fix answer:eval: <pass rate>

## Phase 3C — AIOps observability
- Brief: <path>
- Commit: <SHA>
- Audit log mechanism: <description>
- Expiry/TTL mechanism: <description>
- Governance amendment: <reference>

## Phase 3D — Hygiene
- Commit: <SHA>
- keepalive hardening: <verified>
- temporal probe sidecar mode: <verified>
- Resume protocol polling status: <verified>

## Main merge + deploy
- PR: #<N>
- Cloud Run revision: <amjis-web-NNNNN-xxx>

## Post-deploy answer:eval
- Pass rate: <X>/15
- Comparison to Phase 2 close (13/15): <improved | held | regressed>
- B11 / citations / calibration trends: <description>

## Campaign closed
campaign_complete: true
campaign_completed_at: <ISO>
```

---

## §I — Resume Protocol (READ THIS FIRST on every session start)

```
IF phase_3a_status == "pending":
  → Begin §C Phase 3A (investigation + brief authoring + execution).

ELIF phase_3a_status == "investigating":
  → Continue 3A.0 investigation OR resume brief authoring if interrupted.
  → Check §B last_action for context.

ELIF phase_3a_status == "in_progress":
  → A previous session was running 3A.1 when it stopped. Check §B last_action.
  → If stopped at an editable checkpoint (e.g., between file edits), resume.
  → If stopped mid-test or mid-commit, set status: interrupted and STOP.

ELIF phase_3a_status == "interrupted":
  → Inspect what was last completed. Decide: resume vs reset vs ask native.
  → For 3A specifically, NEVER reset the user-picker test path without native
    approval — that path is the load-bearing safety guarantee.

ELIF phase_3a_status == "failed":
  → STOP. Native must investigate root cause.

ELIF phase_3a_status == "committed" AND phase_3b_status == "pending":
  → Begin §D Phase 3B.

ELIF phase_3b_status == "committed" AND phase_3c_status == "pending":
  → Begin §E Phase 3C.

ELIF phase_3c_status == "committed" AND phase_3d_status == "pending":
  → Begin §F Phase 3D.

ELIF phase_3d_status == "committed" AND main_merge_status == "pending":
  → Begin §G.0 main-merge.

ELIF main_merge_status == "merged" AND deploy_status == "pending":
  → Begin §G.1 watch deploy.

ELIF deploy_status == "deployed" AND post_deploy_eval_status == "pending":
  → Begin §G.2 answer:eval.

ELIF post_deploy_eval_status == "complete" AND NOT campaign_complete:
  → Deliver §H final report. Set campaign_complete: true.

ELIF campaign_complete:
  → Report "campaign already complete, no action needed."
```

---

## §J — Hard rules

1. **Branch discipline.** Stay on `analysis/backend-data-pipeline-perf-audit` in `/Madhav-analysis`.
2. **Preserve user model picker.** Phase 3A MUST NOT break or remove the UI control that lets users choose between stacks. Tests for this are in `phase_3a_acceptance.user_picker_unaffected` — that gate is non-negotiable.
3. **State updates after every action.** §B is the source of truth on resume.
4. **No `answer:eval` per sub-phase.** Single post-3D consolidated eval in §G.2.
5. **Brief-author-then-execute** for each sub-phase. The investigation step is mandatory — don't write code before the brief is authored.
6. **No DB mutations outside scope.** 3A may touch `llm_stack_routing_override`. 3C may design new audit tables. No other DB writes.
7. **gemini-2.5-flash** is the system-process default per native instruction. NOT the user-facing default.
8. **/compact recovery.** If context runs low, /compact, re-read this plan's §A + §B.
9. **The brief files are per-sub-phase and must be authored at sub-phase entry.** They're not pre-authored at plan-file time because the investigation findings shape them.

---

## §K — Per-sub-phase brief stubs (authored at sub-phase entry — NOT pre-authored)

Briefs at:
- `00_ARCHITECTURE/briefs/PHASE_3A_MODEL_DEFAULTS_BRIEF_v1_0.md`
- `00_ARCHITECTURE/briefs/PHASE_3B_HTTP422_DIAGNOSTIC_BRIEF_v1_0.md`
- `00_ARCHITECTURE/briefs/PHASE_3C_AIOPS_OBSERVABILITY_BRIEF_v1_0.md`
- `00_ARCHITECTURE/briefs/PHASE_3D_HYGIENE_BRIEF_v1_0.md`

Each follows the same structure: §A executor briefing, §B-§D execution phases, §E reporting, §F hard rules. Authored on demand at each sub-phase entry.

---

*End PHASE_3_CARRY_FORWARDS_EXECUTION_PLAN_v1_0.md. Living document — executor updates §B continuously; per-sub-phase briefs are authored at sub-phase entry; static sections updated only between full campaigns.*
