# PIV Autonomous Loop Prompt — paste into Claude Code (anti-gravity)

Paste this into Claude Code with cwd set to
`/Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp` (the PIV worktree). It
runs the QG.0 → QG.8 sequence to completion, rotating
`CLAUDECODE_BRIEF.md` between phases.

---

You are executing the **Portal Integration Validation (PIV)** workstream
autonomously in worktree `/Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp`.

## Operating mode

- **Worktree:** `/Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp`. Do NOT
  `cd` into `/Users/Dev/Vibe-Coding/Apps/Madhav` for any reason. That
  is the native's worktree; PIV is isolated.
- **Branch:** `feature/portal-integration-validation`. All commits on
  this branch only.
- **Models:** cheap-only — see PIV master plan §3. Anthropic stack is
  BANNED per native standing instructions.
- **Cost:** hard budget $1.00 total across QG.0–QG.8. BAIL if
  approached.
- **Persistent state:** read-only against production AIOps config. Use
  per-request override headers (`x-aiops-stack`, `x-aiops-model-*`)
  exclusively.
- **Scope discipline:** every brief declares `may_touch` + `must_not_touch`.
  Enforce strictly.

## The loop

For each phase N in `[0, 1, 2, 3, 4, 5, 6, 7, 8]`:

1. **Read** `CLAUDECODE_BRIEF.md` — it points to PHASE_QG_<N>.
2. **Execute** the §3 work plan. Capture evidence under
   `00_ARCHITECTURE/portal_validation/qg<N>_evidence/`.
3. **Author** the §3 deliverable (e.g., `QG<N>_*.md`).
4. **Verify** all `AC.QG<N>.*` acceptance criteria. If any fail and
   none are listed under §6 BAIL conditions, document the failure in
   the deliverable and continue with the rest of the phase — DO NOT
   stop on a single non-BAIL AC.
5. **Commit**:
   ```
   git add -A
   git commit -m "docs(piv-QG.<N>): <phase name>

   - <one-line summary>
   - <one-line summary>

   AC summary: X/Y PASS"
   ```
6. **Set status: COMPLETE** in the current `CLAUDECODE_BRIEF.md`
   frontmatter.
7. **Rotate** the brief to the next phase:
   ```
   cp 00_ARCHITECTURE/portal_validation/briefs/PHASE_QG_<N+1>_BRIEF.md CLAUDECODE_BRIEF.md
   git add CLAUDECODE_BRIEF.md
   git commit -m "chore(piv): rotate CLAUDECODE_BRIEF to PHASE_QG_<N+1>"
   ```
8. **Continue** to the next phase. When N=8 completes, **STOP** — no
   rotation, no `cp` of a tenth brief.

## BAIL OUT rules (global, in addition to per-phase §6)

STOP and report immediately if ANY of:

- Production AIOps config table (`llm_stack_config`, `llm_stack_routing_override`,
  `llm_param_override`) shows a write attributable to PIV.
- Cumulative `llm_usage_events` cost for `x-piv-test-run` tagged calls
  exceeds $0.95.
- Anthropic stack receives a provider call (audit shows `model_name`
  matches an Anthropic model with `x-piv-test-run` metadata).
- DB proxy unreachable for >5 minutes (port 5433).
- A held-out-sacrosanct leak is observed (M6 / M7 paths).
- Cloud Run service returns 5xx systematically.

On BAIL: commit any in-flight work with message
`chore(piv-QG.<N>): BAIL OUT — <reason>` and STOP.

## Initial sanity check (before phase 0)

Run once at the very start:

```
pwd
```
must print `/Users/Dev/Vibe-Coding/Apps/madhav-piv-tmp`. If it doesn't,
STOP — you are in the wrong worktree.

```
git rev-parse --abbrev-ref HEAD
```
must print `feature/portal-integration-validation`. If not, STOP.

```
cat CLAUDECODE_BRIEF.md | head -10
```
must show frontmatter with `session_id: PIV_QG_0`. If not, STOP.

Once these three pass, begin phase 0.

## Madhav-worktree protection (the native is working in parallel)

The native may be making commits to
`/Users/Dev/Vibe-Coding/Apps/Madhav` during this run. At session start
and session end, capture:

```
git -C /Users/Dev/Vibe-Coding/Apps/Madhav rev-parse HEAD
git -C /Users/Dev/Vibe-Coding/Apps/Madhav status --porcelain | head -20
```

Document in the QG.8 final report §9.D if Madhav HEAD advanced —
note as "independent native activity, not PIV-attributable" and
include the SHA delta. This is REPORT-not-BAIL.

## At completion (after QG.8 commits)

Print to stdout:

```
=== PIV COMPLETE ===
Phases:      QG.0 → QG.8 all closed
Final HEAD:  <sha on feature/portal-integration-validation>
Total cost:  $<X> across <N> live LLM calls
Findings:    BLOCKER:X HIGH:Y MEDIUM:Z LOW:W
Report:      00_ARCHITECTURE/portal_validation/PORTAL_INTEGRATION_VALIDATION_REPORT_v1_0.md
Next:        native review + merge to main via worktree pattern
====================
```

Then STOP. Do NOT push the branch. Do NOT merge to main. The native
performs the final merge.

---

Begin.
