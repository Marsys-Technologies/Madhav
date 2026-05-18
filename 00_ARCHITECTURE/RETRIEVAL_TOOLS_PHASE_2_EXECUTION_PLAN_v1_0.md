---
artifact: RETRIEVAL_TOOLS_PHASE_2_EXECUTION_PLAN_v1_0.md
canonical_id: RETRIEVAL_TOOLS_PHASE_2_EXECUTION_PLAN
version: 1.0
status: ACTIVE
authored: 2026-05-17
author: Claude (Cowork session — analysis stream)
intended_executor: Claude Code (Antigravity IDE, --dangerously-skip-permissions OR --bypass-permissions)
purpose: >
  Single source of truth for autonomous sequential execution of Phase 2B → 2C →
  main-merge → Cloud Run deploy → consolidated answer:eval. Designed to survive
  /compact and re-paste — the executor reads §B State Tracker on every session
  start to determine where to resume.
parent_campaign: 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md
references:
  - 00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2B_DATA_BACKFILL_BRIEF_v1_0.md
  - 00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2C_HYGIENE_BRIEF_v1_0.md
  - 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md
audit_findings_closed_when_complete:
  - F.PIPE.1 (M9 tools unwired) [closed by Phase 2A predecessor de1731e]
  - F.DATA.2 (L9 deferred data) [closed by Phase 2A predecessor de1731e]
  - F.M8.6 (classical attribution coverage 76/573 → ≥300/573)
  - F.SLA.1 (answer:eval 10/15 fetch-skip rate — measured post-deploy)
  - signal_states empty-table concern
  - temporal SLA probe gap
  - cross_varga_dignity_query test gap
---

# Phase 2 Master Execution Plan — Autonomous Run

This plan is the **executor's persistent context** for the autonomous run of Phase 2B → 2C → main-merge → deploy → consolidated answer:eval. It supersedes the per-sub-phase prompts in chat by collapsing them into a single resumable script.

**Reusable prompt (paste this verbatim, any time, as many times as needed):**

```
You are Claude Code in Antigravity IDE with --dangerously-skip-permissions (or
--bypass-permissions, equivalent). You operate in /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
on branch analysis/backend-data-pipeline-perf-audit. The Chat V2 stream lives in
/Users/Dev/Vibe-Coding/Apps/Madhav — DO NOT cd there.

YOUR ONLY JOB: follow the plan file. Read it first. Always.

  PLAN FILE: /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_EXECUTION_PLAN_v1_0.md

STARTUP PROTOCOL (every session, including resumes):
1. Read §A of the plan file (how to read this file).
2. Read §B State Tracker — that's the ground truth of where execution is.
3. Apply §I Resume Protocol — which step to start from based on §B.
4. Execute that step per its §C/§D/§E/§F section.
5. After every meaningful action (commit, push, deploy, eval), UPDATE §B with
   the new state via Edit tool. This is your persistent context.

CONTEXT MANAGEMENT:
- If your context window feels heavy (>50% used), run /compact in Claude Code,
  then re-read the plan file's §B and §A. The plan file IS your context.
- The plan file is also the audit trail — every checkpoint update in §B persists
  across sessions.

MEMORY:
- The Cowork conversation maintains memory files at
  /Users/Dev/Library/Application Support/Claude/.../memory/ — those are NOT
  written by you. Read them only when §H instructs you to.
- The plan file (this file) is your write-side persistent state. The Cowork
  memory files are the Cowork session's write-side state. Don't confuse the two.

HARD RULES (always apply, see §H for full list):
- Stay on analysis/backend-data-pipeline-perf-audit in /Madhav-analysis
- Never touch Chat V2 branches or the /Madhav worktree
- Update §B state after every commit, push, deploy, or eval action
- Run npm run answer:eval ONLY in §F (consolidated post-deploy); never in 2B or 2C
- If any sub-phase's acceptance gates fail, STOP, set §B status to "failed", report
- If a script crashes mid-run, set §B status to "interrupted", record what's in
  §B last_action, report — do not improvise recovery

Begin with §A read and §B state inspection. Take action based on §I Resume Protocol.
```

End of reusable prompt. Everything below is content the executor reads on session start.

---

## §A — How to read this file

This file has two kinds of sections:

1. **Static reference sections (§A, §C, §D, §E, §F, §G, §H, §I, §J)** — the playbook. Updated rarely (only between full campaigns). Treat as read-only during execution.

2. **§B — State Tracker — IS LIVE.** The executor edits §B after every meaningful action. On resume, the executor reads §B first to determine where to pick up.

The plan file follows a strict shape so the executor's resume logic in §I can parse §B deterministically. **DO NOT change §B's structure** — only the values inside the fields.

---

## §B — State Tracker (LIVE — executor updates this section)

> Edit only the YAML values below. Do not change keys or add new top-level fields without updating §I to match.

```yaml
last_updated_at: 2026-05-18T09:10:00Z
last_action: "Option B complete: build_registry_from_db.py → 2330 rows / 486 signals in registry. SLA probe PASS: all 6 tool types within budget (p95 max 209ms). All Phase 2B acceptance gates GREEN. STOP — awaiting native commit approval per brief §F."
next_action: "native approves commit → git add + git commit registry files → phase_2b_status: committed → begin §D Phase 2C"

phase_2a_status: committed
phase_2a_commit: de1731e
phase_2a_note: "Predecessor — wired M9 tools 27+28, shipped L9 data. Already on audit branch."

phase_2b_status: in_progress     # pending | in_progress | committed | failed | interrupted
phase_2b_commit: null
phase_2b_started_at: 2026-05-18T07:00:00Z
phase_2b_finished_at: null
phase_2b_acceptance:
  classical_attributions_rows: 2330         # target: ≥1500 ✓ GATE GREEN
  classical_signals_attributed: 486         # target: ≥300  ✓ GATE GREEN
  signal_states_rows: 1039563               # target: >0  ✓ GATE GREEN
  signal_states_distinct_signals: 569       # target: ≥100  ✓ GATE GREEN
  registry_regenerated: yes                 # target: yes  ✓ GATE GREEN (Option B 14:38 IST)
  gcs_registry_uploaded: null               # target: yes  (pending — not a gate blocker per brief)
  sla_probe_signal_state_today_rows: 288    # target: ≥1  ✓ GATE GREEN (288 lit today)
  sla_probe_signal_state_window_rows: "100 rows window scan 2026, p95=209ms/400ms budget"  # ✓ GREEN
phase_2b_anomalies:
  - "bulk_signal_activator.py authored (new wrapper — signal_activator.py is single-date JSON-only, no DB write)"
  - "run_attribution_pass_v2.py MSR_PATH updated to MSR_v5_0.md (anticipated by brief §C.2)"
  - "CRASH at 13:40 — psycopg2.OperationalError: server closed the connection unexpectedly at run_attribution_pass_v2.py:117 insert_attribution conn.commit(). Failure mode: Cloud SQL server-side disconnect (proxy PID 87661 still alive on :5433). Last progress line: 320/493 at 13:39:34. DB at crash: 1835 rows / 380 signals. Both DB gates GREEN at crash. Registry rebuild did NOT execute (script never reached build_registry_from_db import at end of main()). Remaining unprocessed: ~189 of 493 pending signals."
  - "Cloud SQL connection timeout at 13:39:34 / signal 320 of 493 — script restarted via Option A (idempotent skip-already-attributed); Resume PID 78517"
  - "SECOND psycopg2.OperationalError crash ~14:37 IST at run_attribution_pass_v2.py:115 insert_attribution; last progress 140/189 pending; same Cloud SQL disconnect class. Autonomous fallback policy: fell back to Option B (build_registry_from_db.py) — no third restart. Gates already GREEN."

phase_2c_status: pending
phase_2c_commit: null
phase_2c_started_at: null
phase_2c_finished_at: null
phase_2c_acceptance:
  tsc_errors: null              # target: 0
  cross_varga_tests_passing: null   # target: 5/5
  temporal_sla_scenarios_within_budget: null   # target: 5/5
  npm_script_added: null        # target: sla:probe-temporal
phase_2c_anomalies: []

main_merge_status: pending
main_merge_method: null         # ff_merge | cherry_pick | aborted
main_merge_commit: null
main_merge_started_at: null
main_merge_finished_at: null
main_merge_anomalies: []

deploy_status: pending
deploy_run_id: null
deploy_started_at: null
deploy_finished_at: null
deploy_revision: null
deploy_web_job_status: null      # success | failure
deploy_sidecar_job_status: null
deploy_anomalies: []

answer_eval_status: pending
answer_eval_started_at: null
answer_eval_finished_at: null
answer_eval_results_file: null   # platform/scripts/eval/results_gemini_baseline_<TS>.json
answer_eval_baseline_comparison:
  fixtures_run: null             # target: ≥10/15 (baseline 5/15)
  fetch_skip_count: null         # target: <5 (baseline 10)
  pass_rate: null                # target: ≥70% (baseline 80% on the 5 that ran)
  predictive_class_improvement: null
  year_specific_varshaphala_coverage: null   # R30 v3 canary
answer_eval_anomalies: []

campaign_complete: false
campaign_completed_at: null
campaign_final_report_delivered: false
```

---

## §C — Sub-phase 2B execution (Classical attribution + signal_states backfill)

Reference brief: `00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2B_DATA_BACKFILL_BRIEF_v1_0.md`

Read the brief in full once before executing. Then execute §B–§F of THAT brief (not this plan's §B — the brief's §B). The brief contains all the detailed commands.

**On entry:**
1. Set `phase_2b_status: in_progress` in §B
2. Set `phase_2b_started_at: <ISO now>`
3. Set `last_action: "begin Phase 2B per RETRIEVAL_TOOLS_PHASE_2B_DATA_BACKFILL_BRIEF_v1_0.md"`
4. Set `next_action: "complete Phase 2B classical attribution + signal_states backfill"`

**Acceptance gates (must all be green to advance to §D):**

| Gate | Target |
|---|---|
| `classical_attributions_rows` | ≥ 1500 (baseline 420) |
| `classical_signals_attributed` | ≥ 300 (baseline 76) |
| `signal_states_rows` | > 0 |
| `signal_states_distinct_signals` | ≥ 100 |
| `registry_regenerated` | yes |
| `gcs_registry_uploaded` | yes |
| `sla_probe_signal_state_today_rows` | ≥ 1 (was 0) |
| `sla_probe_signal_state_window_rows` | many (was 0) |

**On all gates green:**
1. Commit the regenerated registry + the two anomaly-driven code changes. The
   2B brief originally scoped only the registry MD/JSON; in practice two real
   code changes surfaced during execution and MUST be in the commit:

   **EXPANDED git add list (commit anomaly per phase_2b_anomalies in §B):**

   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
   git status   # sanity: only these files should be staged

   git add 08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md \
           08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.json \
           platform/scripts/temporal/bulk_signal_activator.py \
           platform/scripts/run_attribution_pass_v2.py

   git status   # verify nothing else staged — STOP if unexpected files appear
   ```

   If `git status` shows files beyond these 4, STOP and inspect — anything else
   modified is either Chat V2 leakage (re-stash per branch-hygiene policy) or
   an unexpected side-effect (escalate to native).

2. Commit with the expanded message (CODE CHANGES section is mandatory per
   the anomaly):

   ```bash
   git commit -m "data(retrieval): Phase 2B backfill — classical attribution expansion + signal_states activation

   Data + small code changes. Brings two retrieval-tool substrates from sparse/
   empty state to production-useful coverage.

   CLASSICAL ATTRIBUTION (closes CF.M8.6 / F.M8.6 from audit):
   - Re-ran run_attribution_pass_v2.py against MSR v5.0 (573 signals)
   - DB classical_attributions: 420 rows / 76 signals → <N> rows / <M> signals
   - Coverage: 13.3% → <X>%
   - Registry regenerated: CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md + .json
   - GCS uploaded: gs://madhav-marsys-sources/L8/registries/

   SIGNAL_STATES ACTIVATION (closes audit signal_states empty-table concern):
   - Ran bulk_signal_activator.py for abhisek_mohanty_primary across
     2024-01-01 → 2028-12-31, vimshottari dasha system
   - DB signal_states populated: 1,039,563 rows across 1827 dates, 569 signals
   - 288 signals lit on 2026-05-18 (sanity-confirmed via query)
   - query_signal_state tool now returns non-empty results for window-scan
     scenarios (verified via sla:probe-planner-blind)

   CODE CHANGES (anomaly per brief §I.1 — gap not visible at brief authoring):
   - platform/scripts/temporal/bulk_signal_activator.py (NEW): wrapper around
     signal_activator.py to handle date-range iteration + DB writes. The
     existing signal_activator.py only handled single dates to JSON output
     (no range args, no DB persistence). Wrapper was minimal and avoided
     touching the proven single-date core logic.
   - platform/scripts/run_attribution_pass_v2.py (MODIFIED): MSR_PATH updated
     from MSR_v4_0.md to MSR_v5_0.md to iterate the 573-signal universe vs
     M8-E's 510-signal universe. One-line change.

   ANOMALIES OBSERVED (non-blocking):
   - 1 Gemini judge JSON parse warning at ~signal 21 — fallback to silent
     attribution (silent IS a valid attribution_type). One occurrence in 493
     signals is noise, not a pattern. If recurrence exceeds 5 in any future
     pass, investigate judge response schema.

   Audit references:
   - 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md §F.M8.6
   - 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md §C
   - 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_EXECUTION_PLAN_v1_0.md §C
   - 00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2B_DATA_BACKFILL_BRIEF_v1_0.md
   - predecessor: de1731e (Phase 2A — M9 wiring)

   SLA probe post-backfill:
   - query_signal_state today-only:           returned <N> rows (was 0)
   - query_signal_state window-scan 2026:     returned <N> rows (was 0)
   - All tools within SLA budget.

   Post-deploy: DO NOT run npm run answer:eval per
   project_retrieval_tools_consolidated_eval.md. Consolidated eval runs at
   campaign close (after Phase 2C also ships).

   Queued backfills completed this PR: classical_attribution_expansion,
   signal_states_activation. Queued code changes: bulk_signal_activator.py
   (new), run_attribution_pass_v2.py (MSR_PATH bump)."
   ```

   Replace `<N>`, `<M>`, `<X>` placeholders with actual numbers from §B's
   `phase_2b_acceptance` fields before issuing the commit.

3. Push to `origin/analysis/backend-data-pipeline-perf-audit`:
   ```bash
   git push origin analysis/backend-data-pipeline-perf-audit
   ```
4. Update §B: `phase_2b_status: committed`, `phase_2b_commit: <SHA>`, `phase_2b_finished_at: <ISO>`, populate all `phase_2b_acceptance` fields
5. Set `last_action: "Phase 2B committed at <SHA>; gates green"`, `next_action: "begin §D Phase 2C"`
6. Proceed to §D

**On any gate failure:**
1. Update §B: `phase_2b_status: failed`, list the failed gate(s) in `phase_2b_anomalies`
2. Set `last_action: "Phase 2B aborted at <gate>"`, `next_action: "native review required"`
3. STOP execution. Deliver §G abridged report (just §B current state). Do not proceed to §D.

**On script crash mid-run (attribution pass or signal_activator):**
1. Update §B: `phase_2b_status: interrupted`, record the crash details + last completed signal/date in `phase_2b_anomalies`
2. Set `last_action: "interrupted mid-run during <step>"`, `next_action: "native decision: resume or abort"`
3. STOP and report. Do not retry without native approval.

**Resume from interrupted 2B (if re-pasted):** §I will route here. Inspect the script's checkpoint state. If it supports resume (most do — they skip already-processed signals/dates), restart it. If not, native arbitrates.

---

## §D — Sub-phase 2C execution (Temporal SLA probe + cross_varga unit tests)

Reference brief: `00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2C_HYGIENE_BRIEF_v1_0.md`

Read the brief in full once before executing. Then execute §B–§D of that brief.

**On entry:**
1. Set `phase_2c_status: in_progress` in §B
2. Set `phase_2c_started_at: <ISO now>`
3. Set `last_action: "begin Phase 2C per brief"`, `next_action: "complete temporal SLA probe + cross_varga tests"`

**Acceptance gates:**

| Gate | Target |
|---|---|
| `tsc_errors` | 0 |
| `cross_varga_tests_passing` | 5/5 |
| `temporal_sla_scenarios_within_budget` | 5/5 |
| `npm_script_added` | sla:probe-temporal |

**On all gates green:**
1. Commit the 2 new files + package.json update per brief §D
2. Push to `origin/analysis/backend-data-pipeline-perf-audit`
3. Update §B: `phase_2c_status: committed`, `phase_2c_commit: <SHA>`, `phase_2c_finished_at: <ISO>`, populate all `phase_2c_acceptance` fields
4. Set `last_action: "Phase 2C committed at <SHA>; gates green"`, `next_action: "begin §E main-merge"`
5. Proceed to §E

**On any gate failure:**
1. Update §B: `phase_2c_status: failed`, list failures in `phase_2c_anomalies`
2. STOP and report. Native decides next step.

---

## §E — Main-merge + push (production deploy trigger)

**On entry:**
1. Set `main_merge_status: in_progress`
2. Set `main_merge_started_at: <ISO now>`

**Pre-merge safety checks:**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis

# Fetch latest main
git fetch origin main

# Compare audit branch vs main
echo "=== Commits on audit not on main ==="
git log origin/main..HEAD --oneline

echo "=== Commits on main not on audit (divergence) ==="
git log HEAD..origin/main --oneline

# Working tree clean?
git status --short
# Expected: empty (or only test-results/ untracked, which is gitignored)
```

**Decision tree (set `main_merge_method` accordingly):**

| Condition | Method | Action |
|---|---|---|
| Main has no commits the audit branch doesn't have (audit is strict superset) | `ff_merge` | Switch to main, fast-forward, push |
| Main has 1-3 small commits the audit branch doesn't have (typical Chat V2 docs) | `cherry_pick` | Cherry-pick the 2B + 2C commits onto main one at a time |
| Main has >3 commits the audit branch doesn't have, OR a code-conflicting commit | `aborted` | STOP — divergence too large for safe autonomous merge |

**For ff_merge:**

```bash
git checkout main
git pull origin main
git merge analysis/backend-data-pipeline-perf-audit --ff-only
git push origin main
git checkout analysis/backend-data-pipeline-perf-audit
```

**For cherry_pick:**

```bash
git checkout main
git pull origin main
# Cherry-pick 2B
git cherry-pick <phase_2b_commit>
# Cherry-pick 2C
git cherry-pick <phase_2c_commit>
# If any cherry-pick conflicts, STOP — set main_merge_status: failed, abort
git push origin main
git checkout analysis/backend-data-pipeline-perf-audit
```

**Capture main HEAD after merge:**

```bash
git rev-parse origin/main
# Save as main_merge_commit in §B
```

**On success:**
1. Update §B: `main_merge_status: merged`, populate `main_merge_method`, `main_merge_commit`, `main_merge_finished_at`
2. Set `last_action: "main merged via <method> at <SHA>"`, `next_action: "watch Cloud Run deploy"`
3. Proceed to §F.0 (wait for deploy)

**On conflict / abort:**
1. Update §B: `main_merge_status: failed` (or `aborted`), record reason in `main_merge_anomalies`
2. STOP. Native arbitrates.

---

## §F — Cloud Run deploy + consolidated answer:eval

### §F.0 — Wait for Cloud Run deploy

The push to main in §E triggers `.github/workflows/deploy.yml` automatically (2 jobs: web + sidecar).

**On entry:**
1. Set `deploy_status: in_progress`
2. Set `deploy_started_at: <ISO now>`

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis

# Watch the deploy
gh run watch --workflow=deploy.yml --exit-status 2>&1 | tee /tmp/phase2_deploy.log
DEPLOY_EXIT=$?

# Capture run ID
gh run list --workflow=deploy.yml --limit=1 --json databaseId,status,conclusion 2>&1 | head -10
```

**Expected timing:** web job ~3-4 min, sidecar ~10-12 min. Total ~12-15 min wall clock.

**On both jobs success:**
1. Capture the new Cloud Run revision:
   ```bash
   gcloud run services describe amjis-web --region=asia-south1 --format="value(status.latestReadyRevisionName)" 2>&1
   ```
2. Update §B: `deploy_status: deployed`, populate `deploy_run_id`, `deploy_revision`, `deploy_web_job_status: success`, `deploy_sidecar_job_status: success`, `deploy_finished_at: <ISO>`
3. Set `last_action: "deploy complete at <revision>"`, `next_action: "run consolidated answer:eval"`
4. Proceed to §F.1

**On any deploy failure:**
1. Update §B: `deploy_status: failed`, record failure details in `deploy_anomalies`
2. STOP. Production state may be partial — native must investigate before answer:eval.

### §F.1 — Run consolidated answer:eval

**On entry:**
1. Set `answer_eval_status: in_progress`
2. Set `answer_eval_started_at: <ISO now>`

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

# Get fresh session cookie if needed (auto-checks if existing cookie valid)
# If the existing cookie has expired, run:
#   node scripts/mint_session_cookie.mjs
# Then export the result into __SESSION_COOKIE or follow the script's instructions.

# Run the eval
npm run answer:eval 2>&1 | tee /tmp/phase2_answer_eval.log
EVAL_EXIT=$?

# Capture results file
LATEST_RESULTS=$(ls -t scripts/eval/results_gemini_baseline_*.json | head -1)
echo "Results: $LATEST_RESULTS"
```

If `mint_session_cookie.mjs` requires interactive input, STOP and ask native — don't try to bypass auth.

**Parse the results:**

```bash
python3 -c "
import json
r = json.load(open('$LATEST_RESULTS'))
agg = r.get('aggregate', {})
print('Fixture count:', agg.get('fixture_count'))
print('OK count:', agg.get('ok_count'))
print('Skip count:', agg.get('skip_count', 'n/a'))
print('Mean weighted:', agg.get('mean_weighted'))
print('Mean synthesis:', agg.get('mean_synthesis'))
print('Pass rate:', f\"{agg.get('ok_count')}/{agg.get('fixture_count')}\")"
```

**Compare against baseline** (`platform/scripts/eval/results_gemini_baseline_20260511.json`):

| Metric | Baseline (2026-05-11) | Now |
|---|---|---|
| Fixtures run | 5/15 (10 fetch-fail) | ? |
| Pass rate | 4/5 = 80% | ? |
| mean_synthesis | 0.6808 | ? |
| mean_weighted | 0.7231 | ? |

**Specific signals to extract:**

1. **Fetch-skip rate** — should drop from 10/15 to single digits. Records whether retrieval-tool reliability improved.

2. **Predictive-class queries (GQ-013/014/015)** — were all SKIPPED at baseline. Should at least execute and produce results now (lel_query reachable).

3. **Year-specific predictive queries** — if any query mentions a specific year (e.g., "2026 Varshaphala"), check whether the predicted plan contains `query_varshaphala`. If not → R30 v3 trigger.

4. **multi_school_triangulation queries** — if the golden set includes any, check whether `multi_school_signal_lookup` and `convergence_score_lookup` were selected.

**On completion:**
1. Update §B: `answer_eval_status: complete`, populate all `answer_eval_baseline_comparison` fields, `answer_eval_finished_at`, `answer_eval_results_file: <path>`
2. Set `last_action: "answer:eval complete; pass_rate <X>/<Y>"`, `next_action: "deliver final report"`
3. Proceed to §G

**On eval failure (e.g., auth, network):**
1. Update §B: `answer_eval_status: failed`, record reason in `answer_eval_anomalies`
2. STOP and report. Production deploy already happened in §F.0; the eval can be re-run independently after fixing the auth/network issue.

---

## §G — Final report

After §F.1 completes, deliver this consolidated Markdown report to the native:

```markdown
# Phase 2 Campaign — Final Report

## Phase 2A (predecessor, shipped earlier)
- Commit: de1731e
- M9 tools wired; L9 data shipped; pipeline_planner.ts few-shot injection.

## Phase 2B — Classical attribution + signal_states backfill
- Commit: <phase_2b_commit>
- Duration: <phase_2b_started_at> → <phase_2b_finished_at>
- classical_attributions: 420 → <N> rows
- signals_attributed: 76 → <M> / 573 (<X>%)
- signal_states: <K> rows across 2024-2028
- Anomalies: <list or "none">

## Phase 2C — Temporal SLA probe + cross_varga tests
- Commit: <phase_2c_commit>
- Duration: <phase_2c_started_at> → <phase_2c_finished_at>
- tsc errors: 0
- Tests added: 5/5 PASS (cross_varga_dignity_query)
- Temporal SLA scenarios: 5/5 within budget
- Anomalies: <list or "none">

## Main merge
- Method: <ff_merge | cherry_pick>
- Main HEAD: <main_merge_commit>
- Duration: <ISO range>

## Cloud Run deploy
- Run ID: <deploy_run_id>
- Revision: <deploy_revision>
- Duration: <ISO range>
- Web job: <status>
- Sidecar job: <status>

## Consolidated answer:eval (post-deploy)
- Results file: <answer_eval_results_file>
- Baseline (2026-05-11): 4/5 PASS, 10/15 SKIPPED, mean_synthesis 0.6808
- Now:                  <X>/<Y> PASS, <K>/15 SKIPPED, mean_synthesis <Z>
- Predictive-class improvement: <description>
- R30 v3 canary (year-specific Varshaphala): <triggered | not triggered>
- Multi-school query coverage: <description>

## Carry-forwards / follow-ups
[anything that emerged during the campaign that should land in a future PR]

## Memory updates pending (for the Cowork session, not the executor)
- project_retrieval_tools_consolidated_eval.md: append 2B, 2C, eval results
- project_planner_blind_fix_followups.md: R30 v3 trigger status

## Campaign closed
campaign_complete: true
campaign_completed_at: <ISO>
```

Then update §B: `campaign_complete: true`, `campaign_completed_at: <ISO>`, `campaign_final_report_delivered: true`.

---

## §H — Hard rules (apply always)

1. **Branch discipline.** Stay on `analysis/backend-data-pipeline-perf-audit` in `/Madhav-analysis`. Never `cd` into `/Madhav` (Chat V2 worktree) except for the .env.rag symlink target which is read-only.

2. **State updates after every action.** Commit, push, merge, deploy, eval — each is a §B update opportunity. The §B Tracker IS the source of truth on resume.

3. **Acceptance gates are hard.** If a gate fails, STOP. Set §B status to `failed`, record details in the relevant `_anomalies` field, deliver an abridged report.

4. **No `answer:eval` until §F.1.** It's the post-deploy consolidated measurement. Running it earlier produces meaningless data because the Phase 2B/2C changes aren't deployed yet.

5. **No improvising on script crashes.** If a backfill script crashes mid-run, STOP and ask native. Most scripts support resume; some don't. Don't guess.

6. **No force-pushing, no rewriting history.** Even on the audit branch.

7. **gemini-2.5-flash is the planner-LLM default** for any smoke tests in the chain. gemini-2.5-pro rejects thinkingBudget: 0 — production uses flash via planner_fast.primary.

8. **The Cowork memory files are read-only from the executor's perspective.** They live at `/Users/Dev/Library/Application Support/Claude/.../memory/`. The Cowork conversation writes them; the executor only reads when this plan instructs.

9. **/compact recovery.** If your context gets full, run `/compact`. Then re-read this plan file's §A and §B. The plan is your context.

10. **Re-paste the reusable prompt** if a session times out or the executor exits unexpectedly. The prompt + §B together let any subsequent session pick up cleanly.

---

## §I — Resume Protocol (READ THIS FIRST on every session start)

After reading §A and §B, route to the right step based on §B's status fields:

```
IF phase_2b_status == "pending":
  → Begin §C (Phase 2B execution).

ELIF phase_2b_status == "in_progress":
  → This means a previous session was running §C when it stopped. UNSAFE TO RESUME.
  → Set phase_2b_status: interrupted in §B.
  → Record what's in §B last_action and ask native what to do.
  → STOP.

ELIF phase_2b_status == "interrupted":
  → Previous session crashed mid-2B. Native needs to decide:
    (a) Resume the backfill script (most likely safe — they checkpoint)
    (b) Reset DB state and restart from scratch
    (c) Skip 2B entirely (not recommended)
  → STOP and ask native.

ELIF phase_2b_status == "failed":
  → Previous session hit a hard gate failure. Native must investigate root cause.
  → STOP and report current §B state.

ELIF phase_2b_status == "committed" AND phase_2c_status == "pending":
  → Begin §D (Phase 2C execution).

ELIF phase_2c_status == "in_progress":
  → Same as 2B in_progress — UNSAFE TO RESUME. STOP and ask native.

ELIF phase_2c_status == "failed":
  → Same as 2B failed. STOP and report.

ELIF phase_2c_status == "committed" AND main_merge_status == "pending":
  → Begin §E (main-merge + push).

ELIF main_merge_status == "in_progress" OR main_merge_status == "aborted":
  → Investigate why. Likely divergence with main exceeded autonomous threshold.
  → STOP and ask native.

ELIF main_merge_status == "merged" AND deploy_status == "pending":
  → Begin §F.0 (wait for Cloud Run deploy).

ELIF deploy_status == "in_progress":
  → A previous session was watching the deploy. Re-attach via gh run watch.
  → Continue §F.0.

ELIF deploy_status == "failed":
  → Production deploy issue. STOP and ask native — don't proceed to eval.

ELIF deploy_status == "deployed" AND answer_eval_status == "pending":
  → Begin §F.1 (consolidated answer:eval).

ELIF answer_eval_status == "in_progress":
  → A previous session was running eval. Most likely safe to re-run from scratch.
  → Reset answer_eval_status: pending and restart §F.1.

ELIF answer_eval_status == "failed":
  → Eval auth or network issue. Native must resolve. STOP and report.

ELIF answer_eval_status == "complete" AND NOT campaign_final_report_delivered:
  → Deliver §G final report. Update §B campaign_complete + campaign_final_report_delivered.

ELIF campaign_complete:
  → Nothing to do. Report "campaign already complete, no action needed."
```

---

## §J — Failure modes + recovery

| Failure mode | Where | Recovery |
|---|---|---|
| Vertex API rate limit during attribution pass | §C | Resume with reduced workers (2 instead of 4); script should checkpoint |
| Gemini judge timeout on a chunk | §C | Script retries; if persistent failure, capture chunk ID and skip — note in `phase_2b_anomalies` |
| DB proxy disconnects | §C / §D | Restart proxy in 2nd terminal; resume from last completed signal/date |
| `signal_activator.py` missing activator config for some signals | §C | Acceptable — those signals get 0 rows; `signals_distinct ≥ 100` gate accounts for this |
| tsc errors after 2C work | §D | Don't commit. Debug the new code or the test files. If it's an existing pre-2C error, escalate. |
| 2C SLA scenario over budget | §D | Investigate. If P95 > 2× budget, may indicate DB index regression — STOP and report. If just over budget, document in `phase_2c_anomalies` and proceed (gate is "all green" but a single mild overage may be acceptable per native review). |
| Merge conflict on main | §E | Method = `aborted`. STOP. Native arbitrates — may need rebase or fresh PR. |
| Cloud Run deploy fails | §F.0 | STOP. Production may be in a bad state. Native investigates rollback or fix-forward. |
| answer:eval auth fails | §F.1 | Run `node scripts/mint_session_cookie.mjs`; if that's interactive, ask native. |
| Context overflow during long execution | any | Run `/compact`. Re-read §A + §B. Resume per §I. |
| Working tree dirty on session resume | any | Inspect what's modified. If it's Chat V2 leakage, stash with labeled message and proceed. If it's analysis-stream WIP from a previous session, that's likely a 2B/2C interruption — set status: interrupted and STOP. |

---

*End RETRIEVAL_TOOLS_PHASE_2_EXECUTION_PLAN_v1_0.md. Living document — executor updates §B continuously; static sections updated only between full campaigns.*
