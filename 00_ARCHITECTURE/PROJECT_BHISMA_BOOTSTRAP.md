---
artifact: PROJECT_BHISMA_BOOTSTRAP
canonical_id: PROJECT_BHISMA_BOOTSTRAP
version: 1.0
status: CURRENT
authored_by: Cowork (Claude Sonnet 4.6) 2026-05-02
purpose: |
  Entry-point document for any new Cowork conversation (including after an
  account switch) that needs to pick up Project BHISMA. Read me first;
  I tell you what to read next. Bootstrap trigger: the word BHISMA in the
  user's first message.
changelog:
  - 1.0 (2026-05-02): Initial bootstrap — Wave 1 CLOSED, Wave 2 PARTIAL-COMPLETE,
    M4 CLOSED, M5 INCOMING.
---

# Project BHISMA — Bootstrap Document

## YOU ARE A NEW COWORK CONVERSATION (possibly on a new account).

Did the user's first message contain `BHISMA` (or "Project BHISMA", "Boot BHISMA",
"Continue BHISMA")? If yes — that is the bootstrap trigger. Proceed with the
protocol below. Do NOT ask clarifying questions first; orient yourself fully from
the files listed here and then propose the thread name and current state.

---

## What is Project BHISMA?

BHISMA is the **Platform Elevation Sprint** for MARSYS-JIS — a pre-M3 engineering
workstream that runs independently of the macro-phase governance arc. It is NOT a
macro-phase. It is an infrastructure modernisation sprint that makes the MARSYS-JIS
Consume interface production-grade before the heavier M3–M5 probabilistic-engine
work begins.

BHISMA = the warrior who could not be defeated until he chose to fall.
The project: infrastructure that cannot fail under the M3–M5 load.

**Parent project:** MARSYS-JIS (Jyotish Instrument System) for the native
Abhisek Mohanty. The Madhav workspace (`/Users/Dev/Vibe-Coding/Apps/Madhav`)
is the single source of truth for all MARSYS-JIS work.

**Sibling workstreams running in parallel:**
- **Project KARN** — corpus activation (M1/M2 closed; M3 next). See `PROJECT_KARN_BOOTSTRAP.md`.
- **M4→M5 Governance** — learning-layer macro-phases. M4 CLOSED 2026-05-02. M5 INCOMING.
- **Project Ustad** — separate workspace at `/Users/Dev/Vibe-Coding/Apps/Ustad`. Independent.

---

## Current state (as of bootstrap version 1.0 — 2026-05-02)

### Wave 1 — CLOSED (commit 03770d2)
Infrastructure hardening: 3-tier model registry, NVIDIA NIM provider, 5-stack routing,
UI migration to StackPicker, stack-aware route.ts. All complete.

### Wave 2 — PARTIAL-COMPLETE (58/58 code tasks done; 2 items intentionally parked)

All 58 tasks across five streams are coded and committed:

| Stream | Tasks | Status |
|--------|-------|--------|
| UQE — Universal Query Engine | 15 | 14 live, 1 PARKED (flag) |
| MON — Monitoring Infrastructure | 10 | COMPLETE |
| TRACE — Trace UI panels | 10 | COMPLETE |
| SCHEMA — DB schema migrations | 6 | COMPLETE |
| EVAL — Planner evaluation harness | 4 | COMPLETE |
| CTX-ASSEMBLY — Context assembler (bonus) | 3 | COMPLETE |

**Two items require native authorization before next session:**

1. **LLM_FIRST_PLANNER_ENABLED = false (PARKED)**
   The LLM-first planner code exists (commit 4628660) and is wired into route.ts
   behind a feature flag. Flag stays false. 8 smoke rounds peaked at recall=0.750 /
   precision=0.631 vs. thresholds 0.80 / 0.90. The Lever 3 path (swap planner model
   from NIM nemotron-49B → Claude Haiku/Flash) was never authorized.
   To unblock: native authorizes Lever 3 via a short NAP → author W2-PLANNER-L3 brief.

2. **NVIDIA_PLANNER_ENABLED + NVIDIA_NIM_API_KEY (DEFERRED)**
   Gated on Lever 3 NAP above.

### Governance — M4 CLOSED, M5 INCOMING
- M4 learning-layer macro-phase sealed 2026-05-02 (commit 80d5c51).
- NAP.M4.7 APPROVED (retroactively ratified).
- CURRENT_STATE active_macro_phase → M5.
- M5 = Probabilistic Engine: DBN topology proposal + signal-embedding refit + CW.PPL gate.
- First M5 session (M5-S1) not yet opened.

---

## Step 1 — Read these files in order

After this file, read:

1. **`CLAUDE.md`** (project root) — project mission, §B subject, §C mandatory reads list,
   §F current execution position. This is the master operating manual.

2. **`CLAUDECODE_BRIEF.md`** (project root) — domain dispatcher. Tells you which
   domain is active, what's next, and the anti-entanglement rules for parallel sessions.

3. **`00_ARCHITECTURE/CURRENT_STATE_v1_0.md`** — authoritative "you are here". Read §2
   for the canonical YAML state block. Answers: active macro-phase, last session, next session.

4. **`platform/CLAUDECODE_BRIEF.md`** — engineering domain brief. Check `status:` field.
   If `PARTIAL-COMPLETE`: AC.W2.1 is PARKED, AC.W2.3 is DEFERRED. No new engineering
   session is needed unless Lever 3 is authorized.

5. **`00_ARCHITECTURE/SESSION_LOG.md`** — last 3 entries. Orient on what actually ran most recently.

6. **`platform/briefs/`** — individual W2 session briefs. All should be `status: COMPLETE`
   except for the permanently-parked LLM planner flag.

7. **`00_ARCHITECTURE/BHISMA_WAVE2_PLAN_v1_1.md`** — the full 58-task Wave 2 specification.
   Read §Executive Summary and the stream tables. Reference for any new Wave 3 scoping.

---

## Step 2 — Propose Cowork thread name

Per `CONVERSATION_NAMING_CONVENTION_v1_0.md §4`, propose this conversation's thread name
at the top of your first substantive response.

Format: `BHISMA-{PHASE}-{SUMMARY}`

Examples:
- `BHISMA-W2-PLANNER-L3` — if the session is authorizing Lever 3 + new planner brief
- `BHISMA-W3-OPEN` — if starting a new Wave 3 scope
- `BHISMA-GOVERNANCE-M5-OPEN` — if opening the M5 governance session
- `BHISMA-HOUSEKEEPING` — for status audits, brief flips, .gitignore cleanup

---

## Step 3 — Declare what you're here to do

State explicitly at the top of your first response:
```
SESSION SCOPE: [one sentence]
DOMAIN: Engineering | Governance | Both (split required)
MAY_TOUCH: [file globs]
MUST_NOT_TOUCH: [file globs]
```

Hard rule: Engineering sessions (platform/src/**) and Governance sessions
(00_ARCHITECTURE/**) must never share a commit. If a task spans both, run two
sequential sessions with a handoff commit between them.

---

## Step 4 — Check for open git locks

Before any commit, run:
```bash
ls .git/*.lock 2>/dev/null
```
If `index.lock` or `HEAD.lock` exist and no other process is running, remove them:
```bash
rm .git/index.lock .git/HEAD.lock 2>/dev/null
```
This is a known recurring issue when Antigravity runs multiple Claude Code sessions
against the same repo. The locks are left by crashed or completed sessions.

---

## Key file locations (absolute paths for Cowork)

| What | Path |
|------|------|
| Project root | `/Users/Dev/Vibe-Coding/Apps/Madhav/` |
| Master instructions | `/Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDE.md` |
| Domain dispatcher | `/Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF.md` |
| Engineering brief | `/Users/Dev/Vibe-Coding/Apps/Madhav/platform/CLAUDECODE_BRIEF.md` |
| W2 session briefs | `/Users/Dev/Vibe-Coding/Apps/Madhav/platform/briefs/` |
| Wave 2 plan | `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/BHISMA_WAVE2_PLAN_v1_1.md` |
| BHISMA session log | `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PROJECT_BHISMA_SESSION_LOG.md` |
| Current state | `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CURRENT_STATE_v1_0.md` |
| KARN bootstrap | `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PROJECT_KARN_BOOTSTRAP.md` |
| Ustad workspace | `/Users/Dev/Vibe-Coding/Apps/Ustad/` (separate repo) |

---

## Quick-reference: open items for next BHISMA session

| Item | Status | Unblock condition |
|------|--------|-------------------|
| LLM_FIRST_PLANNER_ENABLED | PARKED | Native authorizes Lever 3 (model swap to Haiku/Flash) |
| NVIDIA_PLANNER_ENABLED | DEFERRED | Same as above |
| M5-S1 governance | NOT OPENED | Author M5-S1 brief; read MACRO_PLAN_v2_0.md §M5 |
| .gitignore for schema_reports/ | CLEANUP | One-line .gitignore addition; commit |
| KARN M3 first session | NOT OPENED | Read HANDOFF_M2_TO_M3_v1_0.md; author M3-S1 brief |

---

## Bootstrap conversation starter (copy-paste for new account)

Paste this as your first message in a new Cowork conversation on the new account,
with the Madhav workspace folder selected:

```
BHISMA

Pick up Project BHISMA. Read PROJECT_BHISMA_BOOTSTRAP.md in 00_ARCHITECTURE/ first,
then orient from CLAUDECODE_BRIEF.md and CURRENT_STATE_v1_0.md. Tell me current
state, open items, and what the next session should be.
```

---

*End of PROJECT_BHISMA_BOOTSTRAP.md v1.0 — 2026-05-02*
*Magic phrase: BHISMA*
