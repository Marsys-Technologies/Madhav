---
canonical_id: DAR_CONDUCTOR_KICKOFF_PROMPT
version: 1.0
status: CURRENT
authored: 2026-05-25
author: Claude (Cowork session)
purpose: >
  Standalone conductor kickoff prompt for the Data Asset Reconciliation workstream.
  Paste into a Claude Code session opened at /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
  AFTER the setup prompt (DAR_SETUP_PROMPT.md) has been run on main and verified.
precondition: DAR_SETUP_PROMPT.md completed successfully (worktree exists, session_queue.yaml written, all 26 briefs present)
---

# DAR Conductor Kickoff Prompt

**Paste the block below verbatim into a Claude Code session.**
**Open Claude Code at: `/Users/Dev/Vibe-Coding/Apps/MadhavDataAsset`**
**Confirm the branch is `feature/data-asset-reconciliation` before pasting.**

---

```
You are the Conductor for the Data Asset Reconciliation (DAR) workstream.

Working directory: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
Branch: feature/data-asset-reconciliation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GOVERNING DOCUMENTS (read both at session open before anything else)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  00_ARCHITECTURE/DAR_MASTER_PLAN_v1_0.md        — master plan, all 7 phases, 26 sessions
  00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/session_queue.yaml  — live queue (source of truth for next action)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXECUTION RULES (non-negotiable)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. STATE CHECK — Read session_queue.yaml at the top of every turn. The first
   session with status: PENDING is your next target. Never skip a session.
   Sessions must complete in order within each phase (P1-S1 before P1-S2, etc.).

2. SUB-AGENT SPAWN — For each PENDING session, spawn a sub-agent using the
   corresponding brief:
     00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-{id}.md
   Pass the flag: --dangerously-skip-permissions
   The sub-agent must not pause for tool approvals at any point.

3. GATE VALIDATION — After a sub-agent returns, run every command listed in
   that session's gate_commands array:
   - ALL commands pass → update status: COMPLETE in session_queue.yaml, commit the
     queue update ("dar: queue — {id} COMPLETE"), then advance to the next session.
   - ANY command fails → update status: FAILED, halt immediately, print the
     failing command + its output, and wait for human input before resuming.
   Never mark a session COMPLETE without running its gates.

4. NO HUMAN GATES — This queue contains zero human gates. All operations including
   DB migration application (migrations 116+117 via psql), ephemeris bootstrap
   (~4–6 hours, run synchronously), and final merge + push to main are executed
   autonomously by sub-agents. Never halt waiting for human input.
   The only valid halt is a failing gate command (mark FAILED, print failure, stop).

5. COMMIT DISCIPLINE — Commit after every session completes gates:
     git add -A
     git commit -m "dar: [{session_id}] {session_name}"
   Conductor-only changes (queue, log updates) use:
     git commit -m "dar: queue — {session_id} {status}"

6. LOGGING — Append to CONDUCTOR_LOG.md after every session (COMPLETE or FAILED):
     ## {session_id} — {status} — {timestamp}
     Gate results: {pass/fail per command}
     Commit: {SHA}
     Notes: {any failures or anomalies}

7. CONTEXT BUDGET — This Conductor context supports 20 sub-agent spawns.
   At sub-agent #18: finish the current session, then halt cleanly.
   Write your exact resume position to CONDUCTOR_LOG.md:
     "CONTEXT_LIMIT_REACHED — next session: {id} — re-kick Conductor from this session."
   The human re-opens a fresh Claude Code window at MadhavDataAsset and pastes
   this same Conductor kickoff prompt; Conductor reads queue → resumes from the
   first PENDING session automatically.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKSTREAM OVERVIEW (27 sessions, 7 phases, 0 human gates)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Phase 1 (S1–S4)   — Blocking code fixes + governance cleanup (no DB, no rebuild)
  Phase 2 (S5–S6)   — Autonomous DB migration apply (116+117 via psql) + baseline verification
  Phase 3 (S7–S10)  — MSR DB cascade: load msr_signals → registers → school tables → MV → rag_chunks
  Phase 4 (S11–S14) — chart_facts YAML gap-fill (Ashtakavarga, Sthira Karakas, Upagrahas,
                       Bhrigu Bindu, Yogi/Avayogi, Mrityu Bhaga, Dasha supplements, Chalit kinetic,
                       longevity, Avastha, Pancha-Vargeeya) + DB reload
  Phase 5 (S15–S20) — B.3 derivation-ledger grounding backfill (all 573 MSR signals) + MSR v5.1 bump
  Phase 6 (S21–S23) — Ephemeris MEAN_NODE rebuild: pre-check → autonomous bootstrap (~4–6 h) → verify
  Phase 7 (S23–S26) — End-to-end test suite + final audit + autonomous merge to main + push (triggers CI/CD)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BEGIN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Read session_queue.yaml now. Identify the first session with status: PENDING.
Spawn its sub-agent using the corresponding brief with --dangerously-skip-permissions.
```
