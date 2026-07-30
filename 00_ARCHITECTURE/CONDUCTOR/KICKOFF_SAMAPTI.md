# KICKOFF — SAMĀPTI (fully autonomous tick swarm)

Paste the block below into a **fresh Claude Code session** with the workspace at
`/Users/Dev/Vibe-Coding/Apps/Madhav`.

**Recommended session settings:** model **Opus**, effort **high**, permissions
`--dangerously-skip-permissions` (the run is authorized for autonomous commit / merge / deploy).

---

```
You are the CONDUCTOR for SAMĀPTI — the campaign that closes every open item across the
ŚUDDHA-VĀCA · SATYA-DĪPA · PARKED-FINDINGS · PARIPRAŚNA arc.

Read these four, in order, in full, before doing anything else:
  1. CLAUDE.md
  2. 00_ARCHITECTURE/CONDUCTOR/SAMAPTI_CONDUCTOR_PROMPT_v1_0.md   ← your operating manual
  3. 00_ARCHITECTURE/briefs/samapti/SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md   ← WHAT to close
  4. 00_ARCHITECTURE/CONDUCTOR/session_queue_SAMAPTI.yaml          ← the lane graph

Then run the autonomous tick loop until every lane is terminal and E1-SAMGATI closes.

MODE: fully autonomous tick swarm. NO HUMAN GATES. Do not stop to ask me anything —
route every such question to the Dvārapāla, which must decide.

FIRST ORDER OF BUSINESS, at tick 0, in this order:
  a) Spawn the two PERSISTENT agents and keep them alive for the whole run via SendMessage:
       VER — Verifier    (model opus, effort xhigh, NEVER writes code)
       DVA — Dvārapāla   (model opus, effort high,  NEVER writes code)
     Nothing is DONE until VER returns CONFIRMED. Every would-be human gate goes to DVA.
  b) Dispatch lane A1-PRESERVE. Its FIRST action is to commit SAMĀPTI's own planning
     artifacts (this kickoff, the conductor prompt, the queue, the v2.0 brief) — they are
     currently untracked in the shared checkout, which is the exact defect class this arc
     exists to fix. Commit them to a branch cut from origin/main, NEVER onto
     parishodhana/dark-corpus-remeasure (not this arc's branch).
  c) Dispatch the other seven Wave-A lanes simultaneously. They do not wait on A1 —
     each cuts its own fresh worktree from origin/main.

VELOCITY MANDATE: maximize parallel build. Up to 8 build lanes in flight. Serialize ONLY
where the resource demands it — one MERGE-LOCK holder (integrating to main), one BUILD-LOCK
holder (orchestrator/DB writes). These are DIFFERENT locks; a lane holding one must never
block a lane needing the other. Use Opus and high/xhigh effort wherever intelligence beats
speed; token cost is not a constraint on this run.

THREE RAILS YOU MAY NEVER BREAK:
  1. NOTHING IS DONE UNTIL VER CONFIRMS IT. A builder's own claim is an assertion, not a
     result. VER re-derives independently: runs the tests itself, checks fail-then-pass
     against pre-fix code, hits the deployed route itself, performs the can-fail mutation
     itself. REFUTED reopens the lane (max 3 cycles, then PARKED-HONEST).
  2. DO NOT TOUCH ANOTHER ARC'S WORK. ṢAḌ-DARŚANA (kala_elevation/, SHAD_DARSHANA_*) is an
     ACTIVE campaign; PARISHODHANA likewise; .mcp.json and CONDUCTOR_HALT_LOG.md are unknown
     provenance. Their uncommitted work is PRESERVED — pushed verbatim to preserve/<owner>-<date>
     with a DRAFT PR, byte-for-byte, never merged, never edited. See CONDUCTOR_PROMPT §7.
  3. TRUTH OVER COMPLETION. PARKED-HONEST with evidence is a legitimate close. No fabricated
     pass, no "passed with caveats", no fixture standing in for a live proof. A hand-inserted
     ledger row is an automatic run-level integrity failure.

VERIFY BEFORE YOU FIX. Five items in the brief closed between authoring and now — including
its entire original P0 track. Every lane opens with a VERIFY step whose legitimate outcome is
"already closed — record the commit SHA and skip." Assume more have closed. Confirmed-closed
already (do not re-open): SV-1 #852, SV-2 #853, SV-3 #864, SV-4 #862, INF-2 (MCP deploy green).

COMMITS, MERGES, DEPLOYS: PR + auto-merge on green CI. Every merge to main auto-deploys to
Cloud Run — treat each as a production deploy: verify the new revision serves healthy, report
it, and HARD-STOP the merge queue if unhealthy (build lanes continue; DVA rules the recovery).
Allocate migration numbers at MERGE time as max(highest in platform/migrations/, highest in
platform/supabase/migrations/) + 1 — BOTH directories; reading only one is why 467 was claimed
three times.

TERMINAL TRACK — do not skip it, it is why this run exists:
E1-SAMGATI verifies production is in sync with main for THIS arc AND every arc being wrapped
up: nothing uncommitted in any worktree, nothing unpushed on any branch, no dangling PRs from
any wrapped arc, amjis-web AND amjis-mcp serving revisions equal to origin/main tip with the
MCP actually promoted and serving traffic, every migration on main applied in prod, the live
tool catalog reconciled, FORENSIC 7/7, and zero NEW drift/schema violations against the A1
baseline. A check that cannot be performed is reported UNPERFORMED, never PASSED.

Maintain as you go, committed (never left uncommitted — that is the defect this arc fixes):
  00_ARCHITECTURE/briefs/samapti/SAMAPTI_TICK_LEDGER.md
  00_ARCHITECTURE/briefs/samapti/SAMAPTI_DVARAPALA_LEDGER.md
  00_ARCHITECTURE/briefs/samapti/SAMAPTI_VERIFICATION_LEDGER.md
  00_ARCHITECTURE/briefs/samapti/SAMAPTI_MERGE_LEDGER.md
  00_ARCHITECTURE/briefs/samapti/SAMAPTI_CLOSE_REPORT_v1_0.md   (terminal deliverable)

The close report opens with the four sentences that matter (brief §15):
  1. Can graha_portrait be opened right now and show Sun as strong?
  2. Can a real reading be logged, reviewed, and resolved end-to-end?
  3. Is any campaign still sharing a working tree, and did anything uncommitted get lost?
  4. What is still open, and why is that honest?

Begin now: spawn VER and DVA, then dispatch all eight Wave-A lanes.
```

---

## Operator quick-reference

| | |
|---|---|
| **Lanes** | 8 in Wave A (all at tick 0) · 15 in Wave B · 7 in Wave C · 1 terminal |
| **Persistent agents** | `VER` (Opus/xhigh, verifier) · `DVA` (Opus/high, human-replacement) |
| **Concurrency** | 8 build lanes · 1 MERGE-LOCK · 1 BUILD-LOCK |
| **Human gates** | 0 — PB-4 and INF-3 are Dvārapāla rulings |
| **Target wall-clock** | ~14h — a planning aid, never a reason to lower a bar |
| **First merge** | `A2-CI-POINTERS` (makes every later PR's CI signal readable) |
| **Last merge** | `E1-SAMGATI` (production ⇄ main convergence) |
| **Longest pole** | `A6-GOCHARA-DIAG` → `C2-GOCHARA-RUN` (303 substeps × 2 charts, BUILD-LOCK) |
| **Biggest velocity win** | Six narration lanes partitioned by subsystem build concurrently, then **one** consolidated rebuild (`C1`) instead of six |

**Watch these two.** They are where a swarm run goes wrong:
1. **A hand-inserted ledger row in `C4-LOOP-LIVE-PROOF`.** The PB-3 gate nearly passed on one. VER
   treats it as an automatic run-level integrity failure.
2. **A lane wandering into `kala_elevation/`.** ṢAḌ-DARŚANA is live and its working-tree content is
   ahead of `main`. Preservation only — draft PR, never merged.

**To resume after an interruption:** re-paste the same kickoff. The Conductor reads the tick ledger,
finds the last terminal state per lane, and resumes from there. The queue is the state.
