---
brief_id: M2_G2_M2_CLOSE
karn_session_name: KARN-W8-R2-M2-CLOSE
wave: 8
stream: G
status: READY
authored_by: Claude (Cowork) 2026-04-30 — Wave 8 open
authored_for: Claude Code execution (autonomous, long-running)
session_type: governance (M2 CLOSE artifact + mirror sync + M3 handoff)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md §M2
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: |
    KARN-W8-R1-REDTEAM-SMOKE — MUST BE COMPLETE WITH VERDICT PASS or PASS_WITH_FIXES
    before this session opens. Read REDTEAM_M2_v1_0.md at session open; if verdict
    is FAIL, halt immediately and report to native.
    Also required: native has run eval baseline (BASELINE_RUN_W7.json non-stub).
    If baseline is still stub, proceed anyway — record as known gap in M2 CLOSE;
    do not halt the entire close for this.
  blocks: KARN-W9-M3-OPEN (M3 cannot open until M2 CLOSE artifact is CURRENT)
sequence_note: |
  W8-R2 is the final session of Wave 8 and the final session of M2.
  It MUST run after W8-R1 completes with PASS/PASS_WITH_FIXES verdict.
  The native triggers W8-R2 after reviewing W8-R1's REDTEAM_M2_v1_0.md.
estimated_time: 1–2 days single Claude Code session
---

# CLAUDECODE_BRIEF_M2_G2_M2_CLOSE
## Wave 8-R2 — M2 CLOSE Artifact + Mirror Sync + M3 Handoff

---

## §0 — Pre-flight (read before any tool call)

```
ROOT = ~/Vibe-Coding/Apps/Madhav
PLATFORM = ~/Vibe-Coding/Apps/Madhav/platform
```

Read in order before any action:
1. This brief (complete)
2. `00_ARCHITECTURE/EVAL/REDTEAM_M2_v1_0.md` — **STOP if verdict is FAIL**
3. `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` — M2 exit criteria (§M2 row)
4. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — current state pointer (update in §3.5)
5. `00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` — last 100 lines
6. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — v1.7 state
7. `.geminirules` and `.gemini/project_state.md` — current Gemini-side state
8. `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` — check for open DIS entries

Emit session-open handshake per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`.

---

## §1 — Gate check

At session open, confirm ALL of the following before any substantive work:

| Gate | Check | Action if fails |
|---|---|---|
| W8-R1 verdict | REDTEAM_M2_v1_0.md verdict = PASS or PASS_WITH_FIXES | HALT — do not proceed |
| All 3 audits PASS | Audit 1 ≥95%, Audit 2 ≥90%, Audit 3 ≥95% | HALT if any FAIL |
| Eval baseline | BASELINE_RUN_W7.json is non-stub | WARN (not halt) — note as gap |
| Open DIS entries | DISAGREEMENT_REGISTER has no OPEN class entries | Report; do not halt |
| TypeScript clean | npm run typecheck exits 0 (confirm from W8-R1) | HALT if non-zero |

---

## §2 — Scope

```
CREATES:
  00_ARCHITECTURE/M2_CLOSE_v1_0.md                     (M2 CLOSE artifact — CURRENT)
  00_ARCHITECTURE/HANDOFF_M2_TO_M3_v1_0.md             (M3 handoff memo)

MODIFIES:
  00_ARCHITECTURE/CURRENT_STATE_v1_0.md                (flip active phase M2→M3)
  .geminirules                                          (mirror update — MP.1)
  .gemini/project_state.md                              (mirror update — MP.2)
  00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md           (W8-R2 entry + M2 seal)

MUST NOT TOUCH:
  025_HOLISTIC_SYNTHESIS/**     (corpus frozen at M2 close)
  01_FACTS_LAYER/**             (read only)
  platform/src/**               (no app code changes)
  platform/migrations/**        (no schema changes)
  platform/scripts/eval/**      (W7-R3 delivered; no changes)
```

---

## §3 — Implementation

### §3.1 — Author M2_CLOSE_v1_0.md

This is the sealing artifact for Macro Phase 2 — Corpus Activation. It must
be a governed document per B.8 (versioned, with frontmatter, status CURRENT).

```markdown
---
artifact: M2_CLOSE_v1_0.md
canonical_id: M2_CLOSE_v1_0
version: 1.0
status: CURRENT
authored_by: KARN-W8-R2-M2-CLOSE
authored_at: <ISO date>
macro_phase: M2 — Corpus Activation
phase_opened: approx 2026-04-19 (M1 close / KARN wave protocol start)
phase_closed: <today's date>
predecessor_governance_doc: 00_ARCHITECTURE/GOVERNANCE_BASELINE_v1_0.md (M1 close + governance rebuild)
---

# M2 CLOSE — Macro Phase 2: Corpus Activation

## Executive summary

M2 (Corpus Activation) is closed. The activation corpus is live: retrieval
pipeline operational, all provenance audits passing, eval harness scaffolded.

## M2 quality bar — final status

| Criterion | Target | Final result | Status |
|---|---|---|---|
| Audit 1: MSR→FORENSIC | ≥95% | 98.99% (490/495) | PASS |
| Audit 2: UCN→MSR | ≥90% | 95.52% (128/134 UCN_SECTION nodes) | PASS |
| Audit 3: CGM→MSR | ≥95% | 95.52% (128/134 nodes) | PASS |
| Eval harness scaffold | exists | 24 fixtures + runner + A/B | PASS |
| Eval baseline run | exists | <PASS — aggregate x.xx | PENDING — stub> | <PASS|WARN> |
| Per-tool planner | unit-smoke | 15/15 vitest | PASS |
| Red-team pass | PASS | REDTEAM_M2_v1_0.md verdict: <verdict> | PASS |
| New query pipeline | default true | NEW_QUERY_PIPELINE_ENABLED=true | PASS |

## Wave log summary

[List each KARN wave (W1–W8) with one-line summary and status]

## Known deferred items (non-blocking)

1. `entry_count` field in CAPABILITY_MANIFEST off by 3 (inherited; scheduled audit pass)
2. SIG.MSR.207 absent from MSR (medium severity; investigate in M3)
3. UCN inline citation pass (Option A — aspirational; no M2 close gate)
4. Eval baseline (if still stub — run manually; does not block M2 close)

## Red-team evidence

`00_ARCHITECTURE/EVAL/REDTEAM_M2_v1_0.md` — verdict: <verdict>

## M2 exit — confirmed

M2 is CLOSED. M3 (Discovery Layer: Pattern + Contradiction Engines) may now open.
```

Populate all `<...>` fields from what you read in pre-flight.

### §3.2 — Author HANDOFF_M2_TO_M3_v1_0.md

The M3 handoff memo orients the first M3 session. It must be readable cold by
a session that has not seen M2's internal work.

```markdown
---
artifact: HANDOFF_M2_TO_M3_v1_0.md
canonical_id: HANDOFF_M2_TO_M3_v1_0
version: 1.0
status: CURRENT
authored_by: KARN-W8-R2-M2-CLOSE
authored_at: <ISO date>
---

# Handoff: M2 → M3

## You are here

Macro-phase M2 (Corpus Activation) closed <date>. M3 (Discovery Layer) is
now the active phase.

## What M2 delivered (brief)

[4–6 sentences covering: retrieval pipeline, composition rules, per-tool
planner, provenance audits, eval harness. Cite wave numbers.]

## Live state of the platform

- Query pipeline: classify → [per_tool_planner] → compose → retrieve(parallel)
  → validate → synthesize → audit
- NEW_QUERY_PIPELINE_ENABLED: true (default)
- PER_TOOL_PLANNER_ENABLED: false (default — flip true after smoke)
- Retrieval tools: 17 (5 L2.5 structured + 7 L1 structured + 5 RAG)
- Provenance audits: all 3 PASS (see M2_CLOSE_v1_0.md §quality bar)
- Eval harness: platform/scripts/eval/ — 24 fixtures, runner, A/B

## What M3 needs to know

1. **Primary M3 deliverable:** Pattern Engine (L3.5 pattern register activation +
   query-time pattern retrieval) and Contradiction Engine (contradiction register
   surfaced in synthesis).
2. **First M3 session should:** Read MACRO_PLAN_v2_0.md §M3, read
   CURRENT_STATE_v1_0.md, orient on L3.5 register state (pattern_register,
   resonance_register, contradiction_register — all in DB).
3. **Prerequisite in M3:** eval baseline must be run before M3 work changes
   retrieval behavior (need the M2 baseline as a pre-M3 comparison point).

## Open items inherited from M2

[List from M2_CLOSE deferred items]

## Active feature flags at M2 close

[List all flags from feature_flags.ts with their default values]
```

### §3.3 — Update CURRENT_STATE_v1_0.md

Flip the `active_macro_phase` from M2 to M3. Update `last_updated_by`,
`last_closed_session`, and `next_session_committed_to`.

Follow the exact schema of the existing CURRENT_STATE file — do not restructure.

### §3.4 — Mirror update (MP.1 + MP.2)

Per GOVERNANCE_INTEGRITY_PROTOCOL §K and ND.1, any Claude-side governance
change with a Gemini-side counterpart must be mirrored in the same session.

M2 close is a governance state change → update both mirror files to adapted parity:

**.geminirules (MP.1):**
- Update the `active_phase` or equivalent field to reflect M3 is now active
- Add a note that M2 corpus activation is CLOSED
- Do not alter Gemini-specific operational rules

**.gemini/project_state.md (MP.2):**
- Update the state pointer to M3
- List M2 close date and key deliverables at summary level
- Preserve all Gemini-specific state; adapt, do not overwrite

Record what was changed in the session close `mirror_updates_propagated` block.

### §3.5 — Git commit and push

After all files are written and verified (§3.1–§3.4), commit all M2 close
artifacts to `redesign/r0-foundation` and push to GitHub.

**Step G.1 — Stage all changed and new files:**
```bash
cd ~/Vibe-Coding/Apps/Madhav
git add \
  00_ARCHITECTURE/M2_CLOSE_v1_0.md \
  00_ARCHITECTURE/HANDOFF_M2_TO_M3_v1_0.md \
  00_ARCHITECTURE/CURRENT_STATE_v1_0.md \
  .geminirules \
  .gemini/project_state.md \
  00_ARCHITECTURE/EVAL/REDTEAM_M2_v1_0.md
```

Also stage any other files modified during this session (mirror files, etc.):
```bash
git add -u
```

**Step G.2 — Verify staged set:**
```bash
git status
git diff --cached --stat
```
Review the diff. Confirm no unintended files are staged (especially no
`platform/src/**` changes, no corpus file edits). If anything unexpected
is staged, unstage it with `git restore --staged <path>` before committing.

**Step G.3 — Commit:**
```bash
git commit -m "M2 CLOSE — Corpus Activation sealed

- M2_CLOSE_v1_0.md: quality bar 7/7 PASS, red-team PASS
- HANDOFF_M2_TO_M3_v1_0.md: M3 orientation memo
- CURRENT_STATE_v1_0.md: active phase M2 → M3
- REDTEAM_M2_v1_0.md: 9/9 axes PASS, 0 findings
- Mirror updates: .geminirules + .gemini/project_state.md

KARN-W8-R2-M2-CLOSE"
```

**Step G.4 — Push:**
```bash
git push origin redesign/r0-foundation
```

If the push is rejected (non-fast-forward), run `git pull --rebase origin redesign/r0-foundation` first, then re-push. Do not force-push.

**Step G.5 — Confirm:**
Print the final commit SHA:
```bash
git log --oneline -1
```
Record the SHA in the SESSION_LOG entry and in the M2 macro-phase seal block.

### §3.6 — SESSION_LOG M2 seal

Append two items to `PROJECT_KARN_SESSION_LOG.md`:

1. The W8-R2 session entry (standard format).
2. The M2 macro-phase seal block:

```
## ═══════ M2 — CORPUS ACTIVATION — CLOSED ═══════

Sealed by: KARN-W8-R2-M2-CLOSE
Sealed at: <ISO date>
Governing artifact: 00_ARCHITECTURE/M2_CLOSE_v1_0.md
Red-team: 00_ARCHITECTURE/EVAL/REDTEAM_M2_v1_0.md (verdict: <verdict>)
Quality bar: all 3 audits PASS; eval harness scaffolded; pipeline live.
Git commit: <SHA> on redesign/r0-foundation (pushed to GitHub)
Next phase: M3 — Discovery Layer (Pattern + Contradiction Engines)
First M3 session name: KARN-W9-M3-OPEN

═══════════════════════════════════════════════════
```

---

## §4 — Acceptance criteria

| # | Criterion |
|---|---|
| AC.1 | Gate checks all pass (or WARN for baseline stub — see §1) |
| AC.2 | `M2_CLOSE_v1_0.md` created with all quality-bar rows populated |
| AC.3 | `HANDOFF_M2_TO_M3_v1_0.md` created and readable cold |
| AC.4 | `CURRENT_STATE_v1_0.md` active phase flipped M2→M3 |
| AC.5 | `.geminirules` updated to adapted parity (M3 active) |
| AC.6 | `.gemini/project_state.md` updated to adapted parity (M2 closed) |
| AC.7 | Mirror pair changes recorded in close checklist `mirror_updates_propagated` |
| AC.8 | SESSION_LOG W8-R2 entry appended |
| AC.9 | SESSION_LOG M2 macro-phase seal block appended (includes git SHA) |
| AC.10 | No changes to `platform/src/**`, `migrations/**`, or corpus files |
| AC.11 | All M2 close files committed to `redesign/r0-foundation` and pushed to GitHub |
| AC.12 | `git log --oneline -1` SHA recorded in SESSION_LOG and M2 seal block |

---

## §5 — Halt conditions

Stop and report if:
- REDTEAM_M2_v1_0.md verdict is FAIL (do not proceed with M2 close)
- Any of the 3 provenance audits returns FAIL when re-verified
- CURRENT_STATE_v1_0.md schema validation fails after edit
- Mirror files cannot be updated (e.g. permission error) — report but do not halt M2 close
- `git push` fails and cannot be resolved with a rebase — commit locally, report the push failure, do not force-push

---

## §6 — Closing summary template

```
=== KARN-W8-R2 CLOSE — M2 CLOSED ===
M2_CLOSE_v1_0.md:         CREATED
HANDOFF_M2_TO_M3_v1_0.md: CREATED
CURRENT_STATE_v1_0.md:    active_phase M2 → M3
.geminirules:             adapted parity (M3 active noted)
.gemini/project_state.md: adapted parity (M2 closed noted)
SESSION_LOG:              W8-R2 entry + M2 seal appended
M2 status:                CLOSED

Next: KARN-W9-M3-OPEN — first M3 session.
```
