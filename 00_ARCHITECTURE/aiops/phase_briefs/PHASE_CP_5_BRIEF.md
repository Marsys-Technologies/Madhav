---
status: OPEN
session_id: AIOPS_CP_5
phase: CP.5
phase_name: "Final smoke + flag flip + monitoring + native acceptance"
next_session: AIOPS_PHASE_1_COMPLETE
authored_at: 2026-05-13
authored_by: AIOPS_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CP_5
## AIOps Phase 1, Step 5 — Cutover and acceptance

---

## §0 — Executor orientation

CP.5 is the cutover phase. The feature is code-complete after CP.4. CP.5
runs the final stack-wide smoke, flips the feature flag from `false` to
`true` on the branch, opens a 48-hour observation window, and writes the
native-acceptance handoff.

**Native acceptance is required to merge this branch.** CP.5 does NOT
merge to main; it produces the PR-ready state and a written acceptance
checklist.

---

## §1 — Mandatory reads

```
1.  CLAUDE.md
2.  00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md §10, §11, §12, §15, §17
3.  00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4.  00_ARCHITECTURE/aiops/CP3_CALL_SITES_INVENTORY.md  (from CP.3)
5.  00_ARCHITECTURE/aiops/CP4_A11Y_AUDIT.md            (from CP.4)
6.  00_ARCHITECTURE/aiops/CP4_BRAND_AUDIT.md           (from CP.4)
7.  All six provider catalog endpoints (live HTTP) — confirm at least 4 of 5
    are reachable; one allowed degraded (e.g., NIM if Nemotron endpoint
    flaky).
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/config/feature_flags.ts              # flip the flag DEFAULT? NO — see §3.4
platform/scripts/aiops/cutover_smoke.ts                # NEW
platform/scripts/aiops/cutover_smoke_report.json       # NEW (generated output)
00_ARCHITECTURE/aiops/CP5_CUTOVER_REPORT_v1_0.md       # NEW
00_ARCHITECTURE/aiops/CP5_NATIVE_ACCEPTANCE.md         # NEW
00_ARCHITECTURE/CURRENT_STATE_v1_0.md                  # update concurrent_workstreams
CLAUDECODE_BRIEF.md                                    # flip to status: COMPLETE
```

### must_not_touch
- Everything else.
- `feature_flags.ts` is touched ONLY in the sense of confirming
  `AIOPS_OVERRIDES_ENABLED` is read from env; we DO NOT change its default
  in code. The flip happens at deployment time by setting the env variable
  in production. This brief documents that step.

---

## §3 — Work plan

### 3.1 — Cutover smoke

Author `platform/scripts/aiops/cutover_smoke.ts`:

```ts
#!/usr/bin/env node
// Runs a Stack Smoke against every one of the 6 stacks sequentially.
// For MARSYS, uses the seeded defaults from CP.1.
// Writes a structured report to cutover_smoke_report.json.

import { runProbe } from '@/lib/aiops/probe/runner'
import type { ModelStack, CallType } from '@/lib/models/registry'

const STACKS: ModelStack[] = ['nim', 'gemini', 'deepseek', 'gpt', 'anthropic', 'marsys']
const CALL_TYPES: CallType[] = [
  'synthesis', 'planner_deep', 'planner_fast',
  'context_assembly', 'worker',
  'eval_judge', 'smoke_synth',
]
const ROLES = ['primary', 'fallback'] as const

const results = []
for (const stack of STACKS) {
  for (const callType of CALL_TYPES) {
    for (const role of ROLES) {
      const r = await runProbe({ stack, callType, role })
      results.push({ stack, callType, role, ...r })
      console.log(`[${r.pass ? 'OK' : 'FAIL'}] ${stack}/${callType}/${role}`)
    }
  }
}

await fs.writeFile('cutover_smoke_report.json', JSON.stringify({
  ran_at: new Date().toISOString(),
  total: results.length,
  pass: results.filter(r => r.pass).length,
  fail: results.filter(r => !r.pass).length,
  results,
}, null, 2))
```

Run it twice:
- Once with `AIOPS_OVERRIDES_ENABLED=false` (registry path).
- Once with `AIOPS_OVERRIDES_ENABLED=true` (DB path; with current overrides).

Both runs should pass at the same rate for any stack/call_type combo. Diff
between them is the surface area where DB overrides are active.

Per the user's standing LLM stack rule, the Anthropic stack rows are
expected to FAIL with `auth_fail` if no Anthropic key is configured —
that's not a CP.5 blocker. Document it as "expected: Anthropic skipped".

### 3.2 — Cutover report

Author `00_ARCHITECTURE/aiops/CP5_CUTOVER_REPORT_v1_0.md`:

```markdown
---
artifact: CP5_CUTOVER_REPORT_v1_0.md
status: CLOSED
authored_at: <ISO timestamp>
session_id: AIOPS_CP_5
---

# CP.5 Cutover Report

## §1 — Smoke test summary
- Flag-off run: <pass>/<total>
- Flag-on run:  <pass>/<total>
- Anthropic rows: <expected failures, not blocking>

## §2 — Catalog freshness (per provider)
- NIM:       <last_fetch>, <model_count>
- Gemini:    <last_fetch>, <model_count>
- DeepSeek:  <last_fetch>, <model_count>
- GPT:       <last_fetch>, <model_count>
- Anthropic: <last_fetch or AUTH_FAIL>, <model_count>

## §3 — Override surface
For each (stack, call_type) with a non-default override, list:
- Current model_id (primary / fallback)
- Registry default
- Reason (if recorded in audit notes)

## §4 — Health table snapshot
List every model and its current health status.

## §5 — Outstanding risks
- (auto-populated from any FAIL or DEGRADED)
```

### 3.3 — Native acceptance handoff

Author `00_ARCHITECTURE/aiops/CP5_NATIVE_ACCEPTANCE.md`:

```markdown
---
artifact: CP5_NATIVE_ACCEPTANCE.md
status: AWAITING_NATIVE
session_id: AIOPS_CP_5
---

# AIOps Phase 1 — Native Acceptance Checklist

The AIOps Phase 1 feature branch `feature/aiops-control-panel` is
code-complete and tested. Before merging to main:

1. [ ] Pull the branch locally; run `npm install` + `npm run db:migrate`
   (against your local DB).
2. [ ] Visit `/aiops/control` as super-admin. Confirm all 6 stacks render.
3. [ ] Switch active stack to NIM. Click "Run smoke test for this stack".
   Confirm at least 8 of 10 probes pass.
4. [ ] Change synthesis primary on NIM to a different model from the
   dropdown. Click Test. Confirm probe succeeds.
5. [ ] Switch to MARSYS. Pick a synthesis primary from Gemini and a worker
   primary from DeepSeek. Confirm Test buttons work for both.
6. [ ] Visit `/observatory`. Click the Configure pencil on any stack card.
   Confirm it lands on `/aiops/control?stack=<stack>`.
7. [ ] Inspect `CP5_CUTOVER_REPORT_v1_0.md`. Confirm flag-off vs flag-on
   parity.
8. [ ] Inspect `CP4_A11Y_AUDIT.md`. Confirm 0 outstanding.
9. [ ] Inspect `CP4_BRAND_AUDIT.md`. Confirm 0 violations.

If all boxes check: merge the PR. Set `AIOPS_OVERRIDES_ENABLED=true` in
production env. Schedule a Cloud Scheduler job to call
`POST /api/admin/aiops/health/probe` nightly.

48-hour observation window starts at the env-var flip. During the window:
- Confirm Observatory cost/usage numbers continue normally.
- Confirm no regression in /consume latency or error rate.
- If anything looks off, rollback by setting `AIOPS_OVERRIDES_ENABLED=false`
  in production env — no code change required.

Schedule flag removal 2 weeks after the flip (per Phase 11B precedent).
```

### 3.4 — Update CURRENT_STATE

Edit `00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2`:

- Add to `concurrent_workstreams` block:
  ```
  AIOps Phase 1 (Control Panel) CODE-COMPLETE 2026-MM-DD on branch
  feature/aiops-control-panel. Awaiting native acceptance per
  00_ARCHITECTURE/aiops/CP5_NATIVE_ACCEPTANCE.md before merge.
  Phase 2 (Adapter Layer) and Phase 3 (Consume UI Overhaul) tracked in
  AIOPS_MASTER_PLAN_v1_0.md §14 — future scope.
  ```
- Bump CURRENT_STATE version + changelog entry.

### 3.5 — Flip CLAUDECODE_BRIEF to COMPLETE

Rewrite root `CLAUDECODE_BRIEF.md`:

```yaml
---
status: COMPLETE
session_id: AIOPS_CP_5
completed_at: <ISO timestamp>
deliverables:
  - 00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md
  - 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
  - 00_ARCHITECTURE/aiops/phase_briefs/PHASE_CP_0…5_BRIEF.md
  - 00_ARCHITECTURE/aiops/CP3_CALL_SITES_INVENTORY.md
  - 00_ARCHITECTURE/aiops/CP4_A11Y_AUDIT.md
  - 00_ARCHITECTURE/aiops/CP4_BRAND_AUDIT.md
  - 00_ARCHITECTURE/aiops/CP5_CUTOVER_REPORT_v1_0.md
  - 00_ARCHITECTURE/aiops/CP5_NATIVE_ACCEPTANCE.md
next_native_action: >
  Review CP5_NATIVE_ACCEPTANCE.md and complete the checklist; merge
  feature/aiops-control-panel to main when satisfied; set
  AIOPS_OVERRIDES_ENABLED=true in production env.
---

# AIOps Phase 1 — COMPLETE

All six phases CP.0 → CP.5 closed. Native acceptance pending per
00_ARCHITECTURE/aiops/CP5_NATIVE_ACCEPTANCE.md.
```

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CP5.1 | `cutover_smoke.ts` exists + runs both flag states | exit 0 from `npm run aiops:cutover-smoke` |
| AC.CP5.2 | Smoke report generated | `test -f platform/scripts/aiops/cutover_smoke_report.json` |
| AC.CP5.3 | Flag-off and flag-on parity (all stacks/call_types match, Anthropic auth_fail allowed) | parse the JSON, assert |
| AC.CP5.4 | `CP5_CUTOVER_REPORT_v1_0.md` exists with all §1–§5 populated | grep section markers |
| AC.CP5.5 | `CP5_NATIVE_ACCEPTANCE.md` exists with all checklist items | grep `[ ]` count |
| AC.CP5.6 | `CURRENT_STATE_v1_0.md` mentions AIOps in concurrent_workstreams | grep |
| AC.CP5.7 | Root `CLAUDECODE_BRIEF.md` `status: COMPLETE` | grep |
| AC.CP5.8 | Branch is on `feature/aiops-control-panel` with N commits ahead of main where N = 6 phases | `git rev-list --count main..HEAD` ≥ 6 |
| AC.CP5.9 | Full test suite green | exit 0 |
| AC.CP5.10 | `npm run typecheck` | exit 0 |
| AC.CP5.11 | scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Final commit message:
```
feat(aiops-CP.5): cutover smoke + native acceptance handoff

- platform/scripts/aiops/cutover_smoke.ts (both flag states)
- 00_ARCHITECTURE/aiops/CP5_CUTOVER_REPORT_v1_0.md
- 00_ARCHITECTURE/aiops/CP5_NATIVE_ACCEPTANCE.md
- CURRENT_STATE_v1_0.md updated with AIOps Phase 1 code-complete note
- CLAUDECODE_BRIEF.md flipped to status: COMPLETE

Phase 1 (Control Panel) is now code-complete. Branch ready for native
review + merge per CP5_NATIVE_ACCEPTANCE.md.

AC summary: 11/11 PASS
```

Do NOT push the branch. Native pushes / opens the PR.

Report:
```
[AIOPS-CLOSE] phase=CP.5 status=COMPLETE branch=feature/aiops-control-panel
[AIOPS-COMPLETE] Phase 1 (Control Panel) code-complete. Awaiting native.
```

---

## §6 — BAIL OUT triggers (CP.5 specific)

- Smoke shows flag-off ≠ flag-on parity on a non-Anthropic stack — there's
  a hidden override creeping in. BAIL OUT, log the discrepancy, ask native
  to investigate.
- More than one provider's catalog endpoint is dead — the Control Panel
  is non-functional in practice. BAIL OUT for native to provision credentials.
- Test suite or typecheck regresses from CP.4 close — something in this
  session broke an upstream contract.

---

*End of PHASE_CP_5_BRIEF.md*
*End of AIOps Phase 1 brief arc.*
