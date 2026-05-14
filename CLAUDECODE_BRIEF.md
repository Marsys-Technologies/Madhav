---
artifact: CLAUDECODE_BRIEF.md
status: NOT_COMPLETE
executor: VS Code Claude Code Extension (anti-gravity) — dangerously-skip-permissions
session_id_prefix: M6
active_phase: M6-A
authored_at: 2026-05-14
authored_by: Cowork-M6-WORKTREE-SETUP
worktree_branch: feature/m6-prospective-testing
governing_macro_phase: M6 — Prospective Testing
predecessor_close: 06_LEARNING_LAYER/M5_CLOSE_v1_0.md (M5 CLOSED 2026-05-14)
nap_gates:
  - NAP.M6.0: phase plan approval — PENDING native review after M6-A
  - NAP.M6.1: prediction batch review before windows sealed — PENDING native review after M6-B
---

# CLAUDECODE_BRIEF — M6 Prospective Testing

## §0 — Mandatory reading order (before any tool call)

Read in this order at every session open:
1. CLAUDE.md (root)
2. 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §changelog v5.3 (M5 closed; M6 INCOMING)
3. 06_LEARNING_LAYER/M5_CLOSE_v1_0.md §6 carry-forwards (CF.M5.1–CF.M5.9) + §8 seal block
4. 00_ARCHITECTURE/MACRO_PLAN_v2_0.md §M6 (scope, exit state, risks a–d, time-gated note)
5. 00_ARCHITECTURE/MACRO_PLAN_v2_0.md §CW.PPL (prediction ledger workstream)
6. 06_LEARNING_LAYER/dbn/LL8_SPEC_v1_0.md (LL.8 ACTIVE; conjugate Beta protocol)
7. 06_LEARNING_LAYER/miss_registry/LL9_SPEC_v1_0.md (LL.9 SCAFFOLD; activation conditions)
8. 06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl (current 20 predictions)
9. 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §C.1–C.6 + §K
10. 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md + SESSION_CLOSE_TEMPLATE_v1_0.md
11. 00_ARCHITECTURE/ROOT_FILE_POLICY.md (before creating any file)
12. This file (governs session scope and ACs)

Do NOT read held-out LEL partition entries during M6-A.

## §1 — Execution strategy

Sessions run sequentially with --dangerously-skip-permissions.
Each session closes (SESSION_LOG appended, CURRENT_STATE updated) before the next opens.

NAP gates are mandatory pauses. At each gate, set status field in this file's frontmatter
to the gate value and HALT. The user resumes by setting status back to NOT_COMPLETE.

Session sequence:
  M6-A-S1 → plan + scaffold + carry-forwards → HALT (status: AWAITING_NAP_M6_0)
  [native approves PHASE_M6_PLAN_v1_0.md → sets status: NOT_COMPLETE]
  M6-B-S1 → prediction batch draft (CAREER + HEALTH; ≥12 predictions)
  M6-B-S2 → prediction batch draft (RELATIONSHIP + SPIRITUAL + PSYCHOLOGICAL; ≥13 predictions)
            → HALT (status: AWAITING_NAP_M6_1)
  [native reviews predictions before windows sealed → sets status: NOT_COMPLETE]
  M6-C-S1 → scoring engine + LL.9 activation
  M6-C-S2 → answer:eval integration + calibration drift monitor + IS.8(a) check

## §2 — M6-A scope (ACTIVE)

### M6-A-S1 deliverables

ITEM 1: PHASE_M6_PLAN_v1_0.md
Author at 00_ARCHITECTURE/PHASE_M6_PLAN_v1_0.md.
Sub-phases: M6-A (infrastructure), M6-B (prediction emission), M6-C (scoring engine),
M6-D (ongoing scoring cycles — time-gated; scaffold only), M6-E (M6 close — time-gated).
Each sub-phase must contain: scope, ACs, may_touch, must_not_touch, NAP registry rows.
Risk register: reproduce MACRO_PLAN §M6 risks a–d with project-specific mitigations.
Note explicitly: M6 is TIME-GATED (exit bar ≥50 scored windows requires elapsed calendar
time; phase cannot be compressed). M6-D and M6-E open only as windows close.
LLM stack: Gemini → DeepSeek → NIM. No Anthropic/Claude API per standing constraint.

ITEM 2: 07_PROSPECTIVE_TESTING/ scaffold
Create directory structure:
  07_PROSPECTIVE_TESTING/
    README.md            ← purpose, path, link to PHASE_M6_PLAN
    scoring/
      scoring_protocol_v1_0.md   ← rubric: CONFIRMED/FALSIFIED/PARTIAL/AMBIGUOUS verdicts
                                    + tie-break rules + window-drift prohibition
      windows/                    ← empty; one JSON written here at each window close
    predictions/
      README.md                   ← pointers to prediction_ledger.jsonl + scored/
      scored/                     ← predictions moved here after window closes
    counterfactual/
      README.md                   ← LL.9 mirror; links to miss_registry
    calibration/
      drift_log.jsonl             ← baseline entry written at M6-C-S1; empty for now
      README.md

ITEM 3: Carry-forward dispositions
CF.M5.6 (HIGH — LL.8 first live update):
  Read 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md header to find LEL version and last entry date.
  If any LEL training event was added after 2026-05-14 (M5 close date): apply conjugate Beta
  update per LL8_SPEC_v1_0.md §3.2b and update parameter_register.json.
  If no new events: write to SESSION_LOG "CF.M5.6 queued — LL.8 update fires on next LEL entry."

CF.M5.1 (MEDIUM — calibration UI):
  Confirm MARSYS_FLAG_PREDICTION_ENGINE_ENABLED is still OFF (check platform/lib/feature_flags.ts
  or equivalent). Document PE.1 (per-chart prediction toggle) as a carry-forward into M6.

CF.M5.3 (LOW — cosmetic commit):
  Run: git log --oneline | head -20 and check if commit 0793719 malformed root tree is visible.
  If fixable surgically (e.g., git rm --cached of stray file), fix it. If complex, document
  "CF.M5.3 deferred — requires interactive rebase beyond autonomous scope" in SESSION_LOG.

CF.M5.8 (LOW — AC.IV.7 latency):
  Note in SESSION_LOG: "CF.M5.8 disposition — AC.IV.7 latency re-evaluation deferred to
  M6 hygiene pass after 7-day production window (non-blocking per M5_CLOSE §6)."

CF.M5.9 (LOW — LEL gap audit):
  Note in SESSION_LOG: "CF.M5.9 — 5 source-backed LEL events deferred from M4A carry into M6.
  Will address during M6-B when LEL is in scope for prediction emission context."

ITEM 4: Mirror propagation MP.1 + MP.2 + MP.4
.geminirules §F state block: update to M6 INCOMING / M6-A-S1 OPEN
.geminirules §C item #5: update phase plan pointer to PHASE_M6_PLAN_v1_0.md (M6)
.gemini/project_state.md Active Phase block: update to M6; add M6-A-S1 deliverables section

ITEM 5: CURRENT_STATE + SESSION_LOG
Update CURRENT_STATE_v1_0.md: active_macro_phase=M6 OPEN; active_sub_phase=M6-A-S1 CLOSED;
next_session=M6 AWAITING NAP.M6.0; red_team_counter unchanged.
Append SESSION_LOG.md full M6-A-S1 entry (open + body + close).

### M6-A acceptance criteria

[ ] AC.M6A.1 — PHASE_M6_PLAN_v1_0.md present; M6-A through M6-E sub-phases with ACs
[ ] AC.M6A.2 — 07_PROSPECTIVE_TESTING/ scaffold created; scoring_protocol_v1_0.md present
[ ] AC.M6A.3 — CF.M5.6 disposed: LL.8 update applied OR queued-pending entry documented
[ ] AC.M6A.4 — CF.M5.1 confirmed: PE.1 carry-forward noted; flag confirmed OFF
[ ] AC.M6A.5 — CF.M5.3 / CF.M5.8 / CF.M5.9 dispositioned in SESSION_LOG
[ ] AC.M6A.6 — MP.1 + MP.2 + MP.4 mirrors propagated to M6 state
[ ] AC.M6A.7 — CURRENT_STATE updated; SESSION_LOG M6-A-S1 appended
[ ] AC.M6A.8 — CAPABILITY_MANIFEST.json updated: PHASE_M6_PLAN + 07_PROSPECTIVE_TESTING entries
[ ] AC.M6A.9 — CLAUDECODE_BRIEF.md status set to AWAITING_NAP_M6_0 (HALT)

## §3 — M6-B scope (LOCKED until NAP.M6.0 cleared)

### M6-B-S1 + M6-B-S2 deliverables

Emit ≥25 new forward predictions; push total prediction_ledger.jsonl to ≥45 entries.

Prediction rules (INVIOLABLE — Learning Layer discipline #4):
  - Each prediction is written BEFORE any LEL held-out outcome for that window period is read
  - Windows are PROSPECTIVE: window_close_date ≥ 2026-09-01 minimum (3-month horizon)
  - Once submitted for NAP.M6.1 review, window_open_date and window_close_date NEVER change
  - dbn_params_ref must cite dbn_params_v1_0.json
  - 90% HDI computed via Monte Carlo (300k samples, seed=42) per NAP.M5.3 CI policy
  - Every prediction carries falsifier_condition: a single unambiguous sentence that, if true
    at window_close_date, renders the prediction CONFIRMED; if false, FALSIFIED

Domain coverage targets (minimum per domain):
  CAREER: ≥5 predictions
  HEALTH: ≥5 predictions
  RELATIONSHIP: ≥5 predictions
  SPIRITUAL: ≥5 predictions
  PSYCHOLOGICAL: ≥5 predictions

Session split:
  M6-B-S1: CAREER + HEALTH batches (≥12 predictions drafted, NOT yet sealed)
  M6-B-S2: RELATIONSHIP + SPIRITUAL + PSYCHOLOGICAL batches (≥13 predictions drafted)
           Then: HALT with status=AWAITING_NAP_M6_1
           Present a readable summary of all ≥25 predictions for native review
           Predictions become immovable ONLY after native approves (status reset to NOT_COMPLETE)

### M6-B acceptance criteria

[ ] AC.M6B.1 — ≥25 new predictions in prediction_ledger.jsonl; total ≥45
[ ] AC.M6B.2 — All 5 DBN domains covered; ≥5 per domain
[ ] AC.M6B.3 — Every prediction: window_open, window_close, falsifier, domain, dasha_lord,
               dbn_params_ref, 90%_HDI (asymmetric), n=1 caveat field
[ ] AC.M6B.4 — NAP.M6.1 APPROVED by native (windows sealed)
[ ] AC.M6B.5 — CURRENT_STATE updated; SESSION_LOG appended; CAPABILITY_MANIFEST updated

## §4 — M6-C scope (LOCKED until NAP.M6.1 cleared)

### M6-C-S1 + M6-C-S2 deliverables

ITEM 1: Automated scoring engine
  platform/scripts/scoring/score_predictions.py
  - Input: prediction_ledger.jsonl + LEL (for any window_close_date already past)
  - Verdict assignment per scoring_protocol_v1_0.md (CONFIRMED/FALSIFIED/PARTIAL/AMBIGUOUS)
  - Output: JSON file per scored prediction in 07_PROSPECTIVE_TESTING/scoring/windows/
  - Reproducibility requirement: deterministic (same input → same output on re-run)
  - LLM for ambiguous verdicts: Gemini flash via existing API stack — NOT Anthropic
  - Unit tests: ≥10 test cases (mock predictions + mock LEL events); all pass

ITEM 2: LL.9 activation
  Update 06_LEARNING_LAYER/miss_registry/LL9_SPEC_v1_0.md: status SCAFFOLD → ACTIVE
  (activation condition: "scoring engine exists and is capable of generating FALSIFIED verdicts")
  Write first miss_registry entry:
    If any predictions already have elapsed windows AND verdict=FALSIFIED: full entry
    Otherwise: sentinel entry documenting "0 misses at M6-C-S1; miss registry active and ready"
  Update 06_LEARNING_LAYER/miss_registry/miss_registry_stub.json to miss_registry_v1_0.json

ITEM 3: answer:eval production integration (CF.M5.4)
  The DeepSeek-based eval harness was scaffolded at M5-A-S1 at platform/scripts/eval/.
  Read that scaffold and integrate it so it can be run as:
    npm run eval:answer  (or equivalent)
  against production chat responses. Rubric: B.11 (Whole-Chart-Read), citation completeness,
  calibration statements present, B.10 (no fabricated computation).
  LLM: DeepSeek — not Anthropic.

ITEM 4: Calibration drift baseline
  Write to 07_PROSPECTIVE_TESTING/calibration/drift_log.jsonl:
  {
    "entry_date": "2026-05-14",
    "session_id": "M6-C-S1",
    "baseline": true,
    "mean_lift": 1.145,
    "beat_fraction": "5/5",
    "total_predictions": <count from ledger>,
    "scored_predictions": <count with outcomes>,
    "tolerance_threshold": 1.05,
    "drift_flag": false,
    "source": "M5-D held-out validation + dbn_params_v1_0.json"
  }

ITEM 5: IS.8(a) red-team check
  Read ONGOING_HYGIENE_POLICIES_v1_0.md §G for red_team_counter logic.
  Read CURRENT_STATE_v1_0.md for current counter value.
  If counter = 3 at M6-C-S2 open: run IS.8(a) five-axis red team and record results.
  If counter < 3: note "IS.8(a) not due; counter = N" in SESSION_LOG.

### M6-C acceptance criteria

[ ] AC.M6C.1 — score_predictions.py present; deterministic; ≥10 unit tests passing
[ ] AC.M6C.2 — LL.9 SCAFFOLD → ACTIVE; miss_registry_v1_0.json present; first entry written
[ ] AC.M6C.3 — answer:eval harness runnable via npm script; DeepSeek-backed; rubric covers B.11+B.10
[ ] AC.M6C.4 — drift_log.jsonl baseline entry written
[ ] AC.M6C.5 — IS.8(a) discharged or counter documented
[ ] AC.M6C.6 — CURRENT_STATE updated; SESSION_LOG appended; CAPABILITY_MANIFEST updated; mirrors propagated

## §5 — may_touch / must_not_touch (all M6-A/B/C)

may_touch:
  00_ARCHITECTURE/PHASE_M6_PLAN_v1_0.md
  00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  00_ARCHITECTURE/SESSION_LOG.md
  00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  07_PROSPECTIVE_TESTING/**
  06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl
  06_LEARNING_LAYER/miss_registry/**
  06_LEARNING_LAYER/dbn/ll8_bayesian_update/**
  platform/scripts/scoring/**
  platform/scripts/eval/**
  platform/lib/feature_flags.ts (read-only verify; no writes)
  .geminirules
  .gemini/project_state.md
  CLAUDECODE_BRIEF.md (status field only)

must_not_touch:
  01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_*.md
  01_FACTS_LAYER/LIFE_EVENT_LOG_*.md (read-only for dasha context; no new entries in M6-A)
  06_LEARNING_LAYER/dbn/DBN_TOPOLOGY_v1_0.md
  06_LEARNING_LAYER/dbn/PRIOR_SPEC_v1_0.md
  06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/production/**
  025_HOLISTIC_SYNTHESIS/**
  platform/src/**

## §6 — LLM stack constraint

NO Anthropic/Claude API calls in any code written during M6.
Stack: Gemini → DeepSeek → NIM.
Non-critical tasks: flash-tier models.
Critical evaluation (scoring, eval harness): Gemini Pro or DeepSeek v4.
Flag any hardcoded Anthropic model strings before writing them.

## §7 — Session-open handshake

Every M6 session emits SESSION_OPEN artifact per SESSION_OPEN_TEMPLATE_v1_0.md
before any tool call. Session IDs: M6-A-S1, M6-B-S1, M6-B-S2, M6-C-S1, M6-C-S2.
cowork_thread_name must match handshake session_id field.
