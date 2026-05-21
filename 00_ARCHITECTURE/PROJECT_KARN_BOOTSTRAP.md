---
artifact: PROJECT_KARN_BOOTSTRAP
canonical_id: PROJECT_KARN_BOOTSTRAP
version: 1.1
status: CURRENT
authored_by: Cowork (Claude) 2026-04-29
purpose: |
  Entry-point document for any new Cowork conversation that needs to pick
  up Project KARN. Read me first; I tell you what to read next.
changelog:
  - 1.1: handle bare "KARN" trigger; W (wave) naming
  - 1.0: initial bootstrap
---

# Project KARN — Bootstrap Document

## YOU ARE A NEW COWORK CONVERSATION.

Did the user's first message contain just `KARN` (or close to it, like "KARN" or "Project KARN" or "kern")? If yes — that's the bootstrap trigger. Proceed with the protocol below.

## Step 1 — Read these files in order

After this file, read:

1. **`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md`** — naming convention (W = Wave, R = Run), wave plan (7 waves), close ritual. The operating rules.

2. **`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md`** — every Claude Code session that has run, with outcomes. Read end-to-end; the most recent entries are at the bottom. The most recent wave-close marker tells you which wave is next.

3. **`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md`** — the operating manual. Six streams (A–F), 18 briefs, autonomous-brief contract.

4. **`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/M1_M2_ACTIVATION_MASTER_PLAN_v0_1_DRAFT.md`** — the strategy. The 10 quality-bar criteria for M2 close.

5. **`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md`** — exists once W1-R1 has closed. The M2-close acceptance gate.

6. **`/Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDE.md`** — project's general operating rules.

7. **The current wave's 3 briefs** at `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_*.md` — figure out from the protocol §5 wave plan + the session log which wave is current.

## Step 2 — Propose Cowork thread name

Per `CONVERSATION_NAMING_CONVENTION_v1_0.md §4` and Project KARN protocol §2.3, propose this conversation's Cowork thread name at the top of your first substantive response:

> **Proposed thread name: `KARN-W{n}-{SUMMARY}`**

Where `{n}` is the current wave (determined from the session log's most recent wave-close marker + 1) and `{SUMMARY}` is the wave's theme per protocol §1.1 wave conversation names table.

If this is the FIRST KARN wave (no prior wave-close marker), the wave is W1 and the name is `KARN-W1-FOUNDATION`.

## Step 3 — Report orientation

Print a concise summary back to the native:

- **Current wave.** Which wave (`W1`, `W2`, ...) is in flight per the protocol's wave plan.
- **Last 3 sessions that closed.** Their KARN names + one-line outcomes from the session log.
- **The 3 briefs to launch in this wave.** Brief paths + KARN session names.
- **Open halts or questions.** Any HALTED briefs or outstanding native decisions.
- **Sync points the native must honor before this wave's briefs launch.** (e.g., "Sync 1 happened post-W1; W2 scope confirmed.")

Then wait for the native's instruction. Do NOT autonomously launch anything.

## Step 4 — Awaiting native action

After orientation, the native will typically:

- **Kick off the wave's 3 briefs** by opening 3 terminal tabs and pasting the kickoff prompts from the brief files. You provide guidance if they ask.
- **Ask questions** about the project state. Answer from the files you've read.
- **Type `close` when the wave is done.** You verify per protocol §4, append the wave-close marker, and provide the bootstrap prompt for the next wave.

## Key context the native may NOT re-explain

These are stable across sessions. After reading the files in Step 1, you should already know:

- **Project parent:** MARSYS-JIS, the LLM-operated Jyotish instrument, native Abhisek Mohanty (born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha). KARN is its M1/M2 activation workstream.
- **Branch:** `redesign/r0-foundation`. (NOT `main`.)
- **Cowork session role:** strategic / planning / coordination. You write briefs; you don't run code.
- **Claude Code session role:** execution. Each Claude Code session runs ONE brief autonomously per the autonomous-brief contract.
- **Parallelism:** 3 parallel Claude Code sessions per wave. Native runs them in separate terminal tabs.
- **Native interaction principle:** minimal interference. Each brief embeds full diagnostics, tests, deploy, verification, and rollback. The native kicks off, monitors closing summaries, gates only at sync points + the `close` ritual.
- **Quality bar at M2 close:** the 10 criteria in master plan §1. M2 closes when all 10 PASS.

## When this document changes

Re-version when:
- New canonical artifacts join the must-read list above.
- The session log format changes (currently per protocol §3.1).
- The naming convention changes.
- The "KARN" bare trigger interpretation changes.

Currently v1.1.

---

*End of PROJECT_KARN_BOOTSTRAP v1.1. Companions: PROJECT_KARN_PROTOCOL.md (operating rules), PROJECT_KARN_SESSION_LOG.md (audit trail).*
