# CLAUDE.md Amendment Proposal — Conductor as Sixth Concurrent Workstream

**Status:** PROPOSED — DO NOT APPLY until after the Wave 2 migration cherry-pick PR merges to main.
**Authored:** 2026-05-19, session CONDUCTOR-S0.
**Apply in:** A dedicated follow-up Cowork session on the Madhav clone (main branch),
after `feature/conductor-to-main` PR merges.

---

## §1 — Exact text block to add to CLAUDE.md §E

Insert this block after the Phase 4C Panchang entry (currently the last entry in §E).
The section header changes from "Five workstreams" to "Six workstreams".

### Change to §E section header

**Before:**
```
## §E — Concurrent workstreams

Five workstreams run concurrently with (not inside) the currently-active macro-phase
and must not be forgotten when the rebuild banner is lifted:
```

**After:**
```
## §E — Concurrent workstreams

Six workstreams run concurrently with (not inside) the currently-active macro-phase
and must not be forgotten when the rebuild banner is lifted:
```

### New entry to append after the Phase 4C entry

```markdown
- **Conductor — Autonomous Session Orchestrator** — canonical_id `CONDUCTOR_PROMPT_v1_0`,
  path `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md`. **STATUS: ACTIVE — on main
  since Wave 1 cherry-pick PR (PR 1 of split-PR strategy, 2026-05-XX).** The Conductor
  is project-spanning orchestration infrastructure. It walks `session_queue.yaml`, spawns
  sub-agents per brief, gates each session via shell tests, and halts for human approval
  at required checkpoints. Wave 1 scope: Phase 4C only (11 entries, 4C-1-S1 through 4C-9).
  Wave 2 (M5-A, 4B, 4D) expands the queue after Wave 1 closes. Context budget: 20
  sub-agents per orchestrator chat; user re-kicks in a fresh chat for the next batch.
  Smoke test SMOKE-S0 PASSED on 2026-05-19 (commit ef3d14d). **Key files:**
  `00_ARCHITECTURE/CONDUCTOR/README.md` (operator docs), `session_queue.yaml` (live queue
  state), `CONDUCTOR_LOG.md` (run history), `CONDUCTOR_HALT_LOG.md` (open halts).
  **Architectural rule:** Conductor commits must be cleanly cherry-pickable to main —
  they must touch ONLY `00_ARCHITECTURE/CONDUCTOR/` paths. If a Conductor commit
  accidentally drags application code, that is a session-discipline failure. **Wave 2
  migration:** WAVE_2_MIGRATION_NOTE.md documents the cherry-pick procedure.
```

---

## §2 — Rationale

**Why the Conductor is a workstream, not just a tool:**

The Conductor is project-spanning infrastructure that:
1. Spans multiple macro-phases (Wave 1 = Phase 4C; Wave 2 = M5-A + 4B + 4D + beyond)
2. Lives on main after the cherry-pick PR — not inside any single phase branch
3. Requires active maintenance: queue entries are authored per session, gate commands
   are tuned when tests evolve, the orchestrator prompt is updated when the pattern
   changes
4. Has its own governance discipline (Conductor commits must be cleanly cherry-pickable;
   brief-authoring halts are mandatory pause points; the 20-session context cap requires
   user coordination)

Including it in §E makes it visible to every session that reads CLAUDE.md, which is
the correct behavior — sessions that are being orchestrated by the Conductor should
know the Conductor exists and where to find its logs.

---

## §3 — Suggested version bump

CLAUDE.md current version: v2.6 (amended 2026-05-19 when Phase 4C was declared)
Proposed version after amendment: **v2.7**

Changelog entry to add at the bottom of CLAUDE.md:

```
*v2.7 (YYYY-MM-DD §E — Conductor workstream added as sixth concurrent workstream;
"Five workstreams" → "Six workstreams"; Conductor cherry-pick PR merged to main).
Prior: v2.6 (2026-05-19 §E — Phase 4C Panchang workstream added).*
```

---

## §4 — Mirror impact (MP.1 — must accompany the CLAUDE.md edit)

MP.1 pairs `CLAUDE.md` with `.geminirules`. Any CLAUDE.md §E change triggers a
same-session MP.1 update to `.geminirules`.

**Add to `.geminirules` §E concurrent workstreams block:**

```
- Conductor (autonomous session orchestrator) — ACTIVE on main since Wave 1 cherry-pick.
  Session queue: 00_ARCHITECTURE/CONDUCTOR/session_queue.yaml (11 entries, Wave 1 = Phase 4C).
  Operator docs: 00_ARCHITECTURE/CONDUCTOR/README.md.
  Wave 2 (M5-A, 4B, 4D) expands the queue after Wave 1 closes.
  Architectural rule: Conductor commits touch ONLY 00_ARCHITECTURE/CONDUCTOR/ paths —
  must be cleanly cherry-pickable to main separate from application-code PRs.
```

---

## §5 — Timing note — DO NOT apply early

**Apply ONLY AFTER the Wave 2 migration cherry-pick PR (PR 1) merges to main.**

Why this timing matters:

1. Before PR 1 merges, the Conductor lives only on `feature/phase-4c-panchang`. A CLAUDE.md
   amendment on main that references a Conductor not visible on main creates a misleading
   state — sessions on other worktrees that read CLAUDE.md from main would see a Conductor
   workstream entry but no Conductor files.

2. The amendment and the cherry-pick are designed as a three-step sequence:
   - **Step A:** Cherry-pick Conductor commits → PR 1 → merge to main (Conductor lands on main)
   - **Step B:** Apply this amendment → CLAUDE.md v2.7 → MP.1 update to `.geminirules` (Conductor
     becomes visible in CLAUDE.md)
   - **Step C:** Phase 4C close PR → PR 2 → merge to main (Phase 4C COMPLETE in §E)

   Steps A, B, C are separate commits/sessions. Do not compress them into one.

3. The cherry-pick PR itself does NOT include this CLAUDE.md amendment — the PR reviewer
   sees only the Conductor infrastructure, uncluttered by governance prose changes. Cleaner
   review; faster merge; then B runs as a tiny 5-minute follow-up Cowork session.

---

*End of CLAUDE_MD_AMENDMENT_PROPOSAL.md — authored 2026-05-19, session CONDUCTOR-S0.*
*Status: PROPOSED (not applied). Apply after Wave 2 migration PR merges to main.*
