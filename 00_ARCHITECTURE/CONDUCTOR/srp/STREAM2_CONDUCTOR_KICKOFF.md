# SRP Stream 2 Conductor — Kick-off Prompt
# Paste this into a Claude Code session started with:
#   cd /Users/Dev/Vibe-Coding/Apps/Madhav
#   claude --dangerously-skip-permissions
#
# Pre-requisite: STREAM_SETUP_PROMPT.md has already been run.
# This stream runs fully independently of Stream 1.

You are the **SRP Stream 2 Conductor**. Your job is to execute the System Repair Plan
Phase 3 (architecture) in its entirety, session after session, with zero human interaction.
You use the Task tool to spawn sub-agents.

Queue file: `00_ARCHITECTURE/CONDUCTOR/srp/stream2_queue.yaml`
Root: `/Users/Dev/Vibe-Coding/Apps/Madhav`
Mode: `--dangerously-skip-permissions` (inherited by all sub-agents)

---

## Your Execution Protocol

**Read the queue first.** Parse `stream2_queue.yaml`. It has two sequential batches:
`batch_id: 1` (A-1), `batch_id: 2` (A-2, blocked on A-1).

**For each batch:**

### Sequential batches (batch_id: 1, then batch_id: 2)

Spawn the session as a Task sub-agent. Wait for it to complete. Run `check_commands`.
If check_commands fail, retry once. If still failing, log BLOCKED and continue.

**Before spawning A-2**: run the A-2 `pre_commands` to merge the A-1 branch into the A-2 worktree:

```bash
git -C /Users/Dev/Vibe-Coding/Apps/MadhavSRP-A2 fetch origin arch/srp-a1-tech-debt
git -C /Users/Dev/Vibe-Coding/Apps/MadhavSRP-A2 merge origin/arch/srp-a1-tech-debt --no-ff \
  -m "merge: bring A-1 audit into A-2 branch"
```

---

## Sub-agent Kickoff Pattern

When spawning each session, use the `kickoff_prompt` from the queue entry verbatim, plus:

```
Additional context:
- You have full file system access. Use --dangerously-skip-permissions semantics.
- Do not ask for human confirmation at any point.
- This is a READ-ONLY analysis session. Do NOT modify any file in platform/ or platform-mcp/.
- Your only output is the document specified in the brief.
- When done, commit and push. Report "SESSION COMPLETE" at the very end.
- If you encounter an error you cannot resolve in 2 attempts, commit whatever you have,
  push, and report "SESSION BLOCKED: [reason]".
```

---

## A-1 Session Guidance

A-1 is a deep read-only audit. Expect it to take 10–20 minutes as the sub-agent reads
many files. The check_commands just verify the output file exists and has key sections.
Do not interrupt — let it run to completion.

Key areas the sub-agent should cover (remind it if it reports back too thin):
- `createOrchestrator` / `single_model_strategy` — find all files, count LoC
- Feature flags in `feature_flags.ts` — list all, check each for dead branches
- `valence` / `significance` / `domain` — find all definitions across both packages
- `params_json` logging in retrieval tools — find all occurrences
- Test files in `platform/src/lib/retrieve/__tests__/` — list what exists

---

## A-2 Session Guidance

A-2 synthesizes A-1's audit into a report. The sub-agent must:
1. Read `TECH_DEBT_AUDIT_v1_0.md` in full first.
2. Also read `CAPABILITY_MANIFEST.json` for the tool catalog.
3. Produce `TARGET_ARCHITECTURE_REPORT_v1_0.md` with §1–§4.

The deletion list (§2) should have **numbered DEL-NNN entries**. The architecture (§3) should
include a concrete 6-month classic-orchestrator sunset plan with a dateable trigger
("30 stable production days post-SRP-F-1 deploy" = approx. 2026-06-22).

---

## Conductor Log

```bash
echo "[$(date '+%H:%M:%S')] BATCH batch_id COMPLETE | sessions: X passed, Y blocked" >> /tmp/srp_stream2_log.txt
```

---

## Completion

When both batches are done, print:

```
╔══════════════════════════════════════════════════════╗
║         SRP Stream 2 Complete                        ║
╠══════════════════════════════════════════════════════╣
║  SRP-A-1   [PASS/BLOCK]                              ║
║  SRP-A-2   [PASS/BLOCK]                              ║
╚══════════════════════════════════════════════════════╝
```

List any BLOCKED sessions with reasons.

State: "Stream 2 is complete. Architecture report at 00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md"

---

## BEGIN

Start now. Parse the queue. Spawn the A-1 sub-agent immediately.
