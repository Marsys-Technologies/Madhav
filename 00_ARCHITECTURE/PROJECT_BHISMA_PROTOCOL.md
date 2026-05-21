---
artifact: PROJECT_BHISMA_PROTOCOL
canonical_id: PROJECT_BHISMA_PROTOCOL
version: 1.0
status: CURRENT
authored_by: Cowork (Claude Sonnet 4.6) 2026-05-02
purpose: |
  Operating protocol for Project BHISMA — the platform elevation sprint within
  MARSYS-JIS. Governs session naming, domain isolation, brief contract, wave
  handoff, and parallel-session anti-entanglement rules.
changelog:
  - 1.0 (2026-05-02): Initial protocol — Wave 1 CLOSED, Wave 2 PARTIAL-COMPLETE.
---

# Project BHISMA — Operating Protocol v1.0

## §0 — What this is

A naming + cross-session-continuity + parallel-isolation protocol for the BHISMA
platform elevation sprint. Solves four problems:

1. **Session identity.** Every Claude Code session has a unique short name that
   appears in commit messages, session logs, and Cowork thread names.
2. **Cross-account memory.** A new Cowork session typing just `BHISMA` becomes
   fully oriented in under 5 minutes via `PROJECT_BHISMA_BOOTSTRAP.md`.
3. **Domain isolation.** Engineering and Governance sessions never share a commit
   or a running process simultaneously on overlapping files.
4. **Parallel co-existence.** BHISMA runs safely alongside KARN, M4→M5 governance,
   and Project Ustad — each with declared file locks that prevent entanglement.

---

## §1 — Naming convention

### §1.1 — Session names

Format: `BHISMA-W{wave}-{SESSION_ID}-{DESCRIPTION}`

| Field | Rule |
|-------|------|
| `W{wave}` | Sequential wave number. W1 = infrastructure hardening (CLOSED). W2 = UQE + observability (PARTIAL-COMPLETE). W3 = next wave (not yet scoped). |
| `SESSION_ID` | Short uppercase tag for the session type: `S{n}` for sequential sessions, `P{n}` for parallel sessions within a wave, `L{n}` for lever/retry sessions. |
| `DESCRIPTION` | SCREAMING-KEBAB-CASE, max 4 words. |

Examples:
```
BHISMA-W2-S1-UQE-BUGS         ← Wave 2, sequential session 1
BHISMA-W2-P3-SCHEMA-MIGRATIONS ← Wave 2, parallel session 3
BHISMA-W2-L3-PLANNER-MODELSWAP ← Wave 2, Lever 3 retry
BHISMA-W3-S1-OPEN              ← Wave 3 kickoff
```

### §1.2 — Cowork thread names

Format: `BHISMA-{PHASE}-{SUMMARY}`

Examples:
```
BHISMA-W2-STATUS          ← Status audit / housekeeping
BHISMA-W2-PLANNER-L3      ← Lever 3 planner activation
BHISMA-W3-OPEN            ← Wave 3 scope + first session
BHISMA-GOVERNANCE-M5-OPEN ← M5 governance open
```

### §1.3 — Brief files

Engineering briefs: `platform/briefs/W{wave}-{NAME}.md`
  - Example: `platform/briefs/W2-PLANNER.md`, `platform/briefs/W3-VECTOR-REINDEX.md`

Governance briefs: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BHISMA-{SESSION_ID}.md`
  - Example: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BHISMA-W2-L3.md`

Root dispatcher: `CLAUDECODE_BRIEF.md` (routing table only — never a session brief)

---

## §2 — Wave plan

### Wave 1 — CLOSED (commit 03770d2, 2026-05-01)
Model registry, NVIDIA NIM, 5-stack routing, StackPicker UI, stack-aware route.ts.

### Wave 2 — PARTIAL-COMPLETE (2026-05-01 to 2026-05-02)
58 tasks across UQE / MON / TRACE / SCHEMA / EVAL / CTX-ASSEMBLY.
All code landed. Two items parked pending native Lever 3 authorization:
- `LLM_FIRST_PLANNER_ENABLED` (flag stays false)
- `NVIDIA_PLANNER_ENABLED` + API key (deferred)

### Wave 3 — NOT SCOPED
Candidate scope (do not pre-build until Wave 3 is authorized):
- Lever 3 planner activation (if NAP granted)
- W3-UQE-CLEANUP carry-forwards
- DB migration smoke against production Cloud SQL
- TRACE panel integration tests

### Future waves
Scope grows from M5 Probabilistic Engine requirements. Do not pre-build for M5.

---

## §3 — Domain boundaries (file locks)

Every BHISMA session must declare `may_touch` and `must_not_touch` at session open.

### Engineering domain (platform/)

```yaml
may_touch:
  - platform/src/**
  - platform/tests/**
  - platform/briefs/**
  - platform/scripts/**
  - platform/.env.local    # NVIDIA key, feature flag overrides
must_not_touch:
  - 00_ARCHITECTURE/**
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**
  - .geminirules
  - CLAUDE.md
```

Exception: Engineering sessions may append to `00_ARCHITECTURE/SESSION_LOG.md`
at close — that is the ONE allowed cross-domain file.

### Governance domain (architecture/)

```yaml
may_touch:
  - 00_ARCHITECTURE/**
  - CLAUDECODE_BRIEF.md        # root dispatcher only
  - .geminirules               # mirror pair MP.1
  - .gemini/project_state.md  # mirror pair MP.2
must_not_touch:
  - platform/src/**
  - platform/tests/**
  - platform/scripts/**
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**
```

---

## §4 — Parallel session anti-entanglement rules

These rules govern running BHISMA alongside KARN, M4→M5 governance, and Ustad.

### Rule 1 — One domain per process

Each running Claude Code process handles exactly one domain. Never mix engineering
(platform/) and governance (00_ARCHITECTURE/) in the same session.

### Rule 2 — File lock declarations prevent overlap

Before starting a session, check `CLAUDECODE_BRIEF.md` §1 domain map. If another
active session has overlapping `may_touch` globs, the new session must wait or be
scoped to non-overlapping files only.

### Rule 3 — Shared files require sequential access

These files are shared across BHISMA and KARN sessions — only one session writes
at a time:
- `00_ARCHITECTURE/SESSION_LOG.md` — append-only; no concurrent writes
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — sequential writes only
- `CLAUDECODE_BRIEF.md` (root) — sequential writes only

### Rule 4 — Project Ustad is fully isolated

Ustad lives at `/Users/Dev/Vibe-Coding/Apps/Ustad/` — a separate git repository.
No BHISMA session touches Ustad files. No Ustad session touches Madhav files.
No git lock conflict is possible between them.

### Rule 5 — Branch naming encodes project

```
feature/w*                → BHISMA Engineering
feature/bhisma-*          → BHISMA Engineering
feature/m*                → MARSYS-JIS Governance
feature/governance-*      → MARSYS-JIS Governance
feature/karn-*            → KARN Corpus Activation
redesign/*                → Portal/KARN corpus work
```

Seeing two project prefixes in one branch name is a scope violation.

### Rule 6 — Commit messages encode domain

Engineering commits: `feat(w{n}-{stream}):`, `fix(w{n}-{stream}):`, `test(w{n}-):`
Governance commits: `docs(m{phase}):`, `chore(governance):`, `feat(m{phase}-):`
Housekeeping commits: `chore(housekeeping):`, `chore(routing):`

Mixed-domain commit = scope violation → must be split.

---

## §5 — Session open / close ritual

### Open
1. Read `PROJECT_BHISMA_BOOTSTRAP.md` → orient on current state.
2. Read `CLAUDECODE_BRIEF.md` → check active sessions, file locks.
3. Read domain brief → confirm scope, may_touch, must_not_touch.
4. Emit session open declaration (see §3 template above).
5. Check for git locks: `ls .git/*.lock` — remove stale locks.

### Close
1. All ACs from brief must be verified (tsc clean, tests pass).
2. Set brief `status: COMPLETE` (or PARKED/PARTIAL with reason).
3. Append entry to `00_ARCHITECTURE/SESSION_LOG.md`.
4. Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` if phase changed.
5. Commit with domain-appropriate message format.
6. Update `CLAUDECODE_BRIEF.md` §1 domain map row for this domain.

---

## §6 — Lever system for the LLM planner

The LLM-first planner uses a three-lever escalation before full activation:

| Lever | Description | Status |
|-------|-------------|--------|
| Lever 1 | Prompt engineering (system prompt tuning) | EXHAUSTED (8 rounds) |
| Lever 2 | Threshold review — classify() retained | DECIDED (native, 14e4b02) |
| Lever 3 | Model swap: NIM nemotron-49B → Haiku/Flash | PENDING NATIVE AUTHORIZATION |

To proceed with Lever 3:
1. Native says "authorize Lever 3" in conversation.
2. Author brief `platform/briefs/W2-PLANNER-L3.md`.
3. Claude Code session runs: swap model in `STACK_ROUTING`, re-run EVAL-B smoke.
4. If recall ≥ 0.80 AND precision ≥ 0.90: flip `LLM_FIRST_PLANNER_ENABLED = true`.
5. If still failing: escalate to native with results before any further change.

---

## §7 — Bootstrap quick-reference

**Magic phrase for new Cowork session (new account or fresh context):**

Paste into first message, with Madhav workspace folder selected:
```
BHISMA

Pick up Project BHISMA. Read PROJECT_BHISMA_BOOTSTRAP.md in 00_ARCHITECTURE/ first,
then orient from CLAUDECODE_BRIEF.md and CURRENT_STATE_v1_0.md. Tell me current
state, open items, and what the next session should be.
```

Claude will: read bootstrap → read CURRENT_STATE → read platform brief → propose
thread name → report state + open items.

---

*End of PROJECT_BHISMA_PROTOCOL.md v1.0 — 2026-05-02*
