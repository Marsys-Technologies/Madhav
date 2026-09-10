---
artifact: SESSION_OPEN_TEMPLATE_v1_0.md
version: 1.2
status: CURRENT
produced_during: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION (2026-04-24)
implements: GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §F
authoritative_side: tool-neutral (the instantiated handshake produced by each session is the
  governed provenance surface, via SESSION_LOG + CURRENT_STATE_v1_0.md pairings. STEP_LEDGER
  retired 2026-04-24; FILE_REGISTRY superseded by CAPABILITY_MANIFEST.json 2026-04-27.)
mirror_obligations: >
  None for this template file itself. Per-session instantiations are appended to SESSION_LOG
  (Claude-side) as the opening block of the session's entry; the Gemini-side mirror is the
  corresponding state reflected in `.gemini/project_state.md` per MP.2 adapted parity.
consumers:
  - Every Claude Code and Codex session opening on this project
  - `schema_validator.py` — validates the handshake YAML before any substantive work
  - `mirror_enforcer.py` — reads `mirror_pair_freshness_check` to decide whether a mid-session
    enforcer run is obligated
  - Step 9 (CLAUDE.md rebuild) — absorbs the "emit session-open handshake at start" instruction
    into CLAUDE.md's mandatory reading list
  - Step 10 (SESSION_LOG schema retrofit) — extends the session_id naming convention and upgrades
    the `step_number_or_macro_phase` field to name a CURRENT_STATE row instead of a STEP_LEDGER
    row post-rebuild
changelog:
  - v1.2 (2026-08-15, CODEX_ONBOARDING): Adds tool/profile/worktree provenance,
    coordination-lease evidence, and mandatory CCD-register consumption for the shared
    Claude Code/Codex operating convention in GOVERNANCE_INTEGRITY_PROTOCOL §P.
  - v1.0 (2026-04-24, Step 7): Initial template. Produced per GOVERNANCE_INTEGRITY_PROTOCOL §F.
    Carries the mandatory-field schema, enforcement rules, two worked examples (rebuild-era
    and post-rebuild-era), and the CLI invocation for validation.
  - v1.1 (2026-05-31, DOC_CLEANUP): Retire STEP_LEDGER from mandatory reads (GOVERNANCE_CLOSED
    2026-04-24); replace FILE_REGISTRY with CAPABILITY_MANIFEST.json (superseded 2026-04-27);
    mark ND.1 Mirror Discipline RETIRED in obligation sections (2026-05-27).
---

# SESSION_OPEN_TEMPLATE v1.0
## MARSYS-JIS Project — Session-Open Handshake

*Implements `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §§F, P`. Every Claude Code or Codex
session emits a handshake per this schema **before any substantive tool call**. A session
whose handshake fails `schema_validator.py` halts and reports; it does not proceed.*

---

## §1 — How to use this template

1. At session open, the agent reads its mandatory-reading list (per current CLAUDE.md item 1 plus the ledger's per-step brief).
2. It emits a YAML handshake per the schema in §2 below.
3. It passes the handshake to `schema_validator.py` (or the equivalent in-session check).
4. If the handshake validates, the session proceeds. The handshake is appended to `SESSION_LOG.md` as the opening block of that session's entry.
5. If the handshake fails, the session halts and reports the failing field(s) to the native.

The handshake is paired with a `session_close` block at session end (per `SESSION_CLOSE_TEMPLATE_v1_0.md`). The pair is what `schema_validator.py` validates as a well-formed session.

---

## §2 — The schema

```yaml
session_open:
  # ------------------------------------------------------------------
  # Identity
  # ------------------------------------------------------------------
  session_id: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION
    # unique session_id.
    # Rebuild era (Steps 0–15): STEP_NN_<SHORT_TITLE>
    # Post-rebuild era: per MP macro-phase + sub-phase, e.g., M2_B3_UCN_RETRIEVAL_BUNDLE
    # (format TBD at Step 10)
  cowork_thread_name: "Madhav 07 — Governance Integrity Implementation"
    # Per CONVERSATION_NAMING_CONVENTION_v1_0.md §1. Proposed at the top of the first
    # substantive response per §4 of that artifact.
  agent_name: claude-opus-4-7
    # "claude-opus-4-7" / "claude-opus-4-6" / "claude-sonnet-4-6" /
    # "gemini-2-5-pro" / etc. Pinned per MP v2.0 §3.4.F.
  agent_version: claude-opus-4-7
    # Model version identifier at session open (may equal agent_name).
  tool: "Claude Code"
    # Required provenance: "Claude Code" or "Codex".
  tool_profile: null
    # Codex sessions record "madhav-safe" or "madhav-parity"; Claude Code records null.
  worktree_path: <absolute-path>
    # Every state-changing session uses its own task-specific worktree.
  step_number_or_macro_phase: STEP_7
    # Rebuild era: STEP_NN. Post-rebuild: M.P.sub-phase, e.g., M2.B.3.
  predecessor_session: STEP_6_GOVERNANCE_INTEGRITY_DESIGN
    # session_id of the previous session that handed off to this one. MUST match
    # STEP_LEDGER's most recently `completed` row (rebuild era) or the last
    # `current_state_updated: true` session (post-rebuild).

  # ------------------------------------------------------------------
  # Cross-tool coordination
  # ------------------------------------------------------------------
  coordination:
    coordination_ref: "origin/campaign-coordination"
    lease_id: "L-<live-id>"
    lease_status_verified: true
    lease_verified_at: <ISO-8601>
    work_order_surface: <owning-campaign-ledger-or-queue>
  cross_tool_state_read:
    cross_cutting_decision_register: true
    stale_surfaces_disregarded:
      - ".conductor-state.json"
      - ".gemini/project_state.md"
      - "CLAUDECODE_BRIEF.md (when COMPLETE)"

  # ------------------------------------------------------------------
  # Mandatory reading confirmation
  # ------------------------------------------------------------------
  mandatory_reading_confirmation:
    # One entry per item in the current mandatory-reading list (per CLAUDE.md +
    # the active step brief). Each entry carries the file path, the sha256 of the
    # file content at read time, and the ISO timestamp.
    - file: MARSYS_JIS_BOOTSTRAP_HANDOFF.md
      fingerprint_sha256: <hex>
      read_at: 2026-04-24T00:00:00+05:30
    - file: 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md
      fingerprint_sha256: <hex>
      read_at: 2026-04-24T00:00:00+05:30
    - file: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
      fingerprint_sha256: <hex>
      read_at: 2026-04-24T00:00:00+05:30
    - file: 00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md
      fingerprint_sha256: <hex>
      read_at: 2026-04-24T00:00:00+05:30
    # STEP_LEDGER retired (GOVERNANCE_CLOSED 2026-04-24) — replaced by CURRENT_STATE_v1_0.md
    - file: 00_ARCHITECTURE/CURRENT_STATE_v1_0.md  # replaces STEP_LEDGER post-rebuild
      fingerprint_sha256: <hex>
      read_at: 2026-04-24T00:00:00+05:30
    - file: 00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md
      fingerprint_sha256: <hex>
      read_at: 2026-08-15T00:00:00+05:30
    - file: 00_ARCHITECTURE/STEP_BRIEFS/STEP_07_GOVERNANCE_INTEGRITY_IMPLEMENTATION_v1_0.md
      fingerprint_sha256: <hex>
      read_at: 2026-04-24T00:00:00+05:30
    - file: 00_ARCHITECTURE/GROUNDING_AUDIT_v1_0.md
      fingerprint_sha256: <hex>
      read_at: 2026-04-24T00:00:00+05:30

  # ------------------------------------------------------------------
  # Canonical-artifact fingerprint check
  # ------------------------------------------------------------------
  canonical_artifact_fingerprint_check:
    # Read CANONICAL_ARTIFACTS_v1_0.md; re-compute fingerprints of
    # (a) every canonical artifact this session's declared_scope names, AND
    # (b) MACRO_PLAN_v2_0.md AND CANONICAL_ARTIFACTS_v1_0.md unconditionally.
    # A match: false value indicates silent file mutation since last
    # CANONICAL_ARTIFACTS update — handshake FAILS.
    - canonical_id: MACRO_PLAN
      declared_fingerprint: <hex from CANONICAL_ARTIFACTS>
      observed_fingerprint: <hex from actual file read>
      match: true
    - canonical_id: CANONICAL_ARTIFACTS
      declared_fingerprint: <hex from CANONICAL_ARTIFACTS>
      observed_fingerprint: <hex from actual file read>
      match: true
    # ... additional rows per declared_scope ...

  # ------------------------------------------------------------------
  # Declared scope (GA.20 closure; Axis C.4 enforcement)
  # ------------------------------------------------------------------
  declared_scope:
    may_touch:
      # Enumerate every path (or glob) the session may write to.
      - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
      - 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md
      - 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md
      - 00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md
      - platform/scripts/governance/*.py
      - .geminirules
      - .gemini/project_state.md
      - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json  # Supersedes FILE_REGISTRY (2026-04-27)
      - 00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md
      # STEP_LEDGER retired (GOVERNANCE_CLOSED 2026-04-24) — do not list in may_touch
      - 00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md
      - 00_ARCHITECTURE/SESSION_LOG.md
      - CLAUDE.md    # single-line addition only per protocol §M.1 P5
    must_not_touch:
      # Positive enumeration of what is OUT of scope. Required (empty list fails).
      - 025_HOLISTIC_SYNTHESIS/**          # L2.5 corpus untouched in Step 7
      - 01_FACTS_LAYER/**                  # L1 facts untouched
      - 03_DOMAIN_REPORTS/**               # L3 reports untouched
      - 00_ARCHITECTURE/MACRO_PLAN_v2_0.md # MP v2.0 frozen until next meta-gov revision
      - 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md  # frozen
      - 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md  # frozen; Step 8 red-team then Step 9 close
      - 02_ANALYTICAL_LAYER/**             # L2 matrices untouched
      - 06_LEARNING_LAYER/**               # Step 11 scope
      - platform/src/**                    # corpus-platform code out of Step 7 scope

  # ------------------------------------------------------------------
  # Mirror-pair freshness (ND.1; Axis C.6 enforcement)
  # ------------------------------------------------------------------
  mirror_pair_freshness_check:
    # For every mirror pair in CANONICAL_ARTIFACTS §2 (MP.1–MP.8 as of Step 7),
    # report last_verified_on + gap-in-days. Threshold for stale: >1 day
    # (daily-cadence project). A stale pair obligates running mirror_enforcer.py
    # as the session's first substantive action.
    - pair_id: MP.1
      claude_side: CLAUDE.md
      gemini_side: .geminirules
      last_verified_on: 2026-04-24
      days_since_verification: 0
      stale: false
    - pair_id: MP.2
      claude_side: "composite(SESSION_LOG + STEP_LEDGER + active plan pointers)"
      gemini_side: .gemini/project_state.md
      last_verified_on: 2026-04-24
      days_since_verification: 0
      stale: false
    # ... MP.3 through MP.8 ...

  # ------------------------------------------------------------------
  # Native-directive obligations
  # ------------------------------------------------------------------
  native_directive_obligations:
    # For every `open` or `partially_addressed` ND.N whose consumption matrix
    # names the current step, enumerate the obligation.
    # ND.1 Mirror Discipline: RETIRED 2026-05-27 per native directive (Gemini collaboration inactive)
    # No open directives as of 2026-05-27. native_directive_obligations is empty.
    # Example entry (historical — DO NOT USE for new sessions):
    # - directive_id: ND.1
    #   obligation_summary: "..."
    #   acknowledged: true

  # ------------------------------------------------------------------
  # Red-team cadence
  # ------------------------------------------------------------------
  red_team_due: false
    # true if this session is a 3rd-session-cadence cycle or closes a macro-phase
    # per MP v2.0 §IS.8. Step-bound red-teams (Step 4, Step 8) are the step's own
    # scope, not a session-cadence red-team.

  # ------------------------------------------------------------------
  # Free-form notes (optional)
  # ------------------------------------------------------------------
  notes: ""
```

---

## §3 — Enforcement

The handshake is validated by `schema_validator.py` **before** any other action in the session. Validation failures (any of these) halt the session:

1. `mandatory_reading_confirmation` is missing any item from the current mandatory-reading list (CLAUDE.md items + current step brief + any `open` ND.N matrix input).
2. Any `canonical_artifact_fingerprint_check` row has `match: false` — indicates silent file mutation since last CANONICAL_ARTIFACTS update.
3. Any `mirror_pair_freshness_check` row has `stale: true` — session must run `mirror_enforcer.py` as its first substantive action and either (a) confirm parity and refresh `last_verified_on` in CANONICAL_ARTIFACTS, or (b) open a DISAGREEMENT_REGISTER mirror-desync entry.
4. `declared_scope.must_not_touch` is empty — every session must declare both may-touch and must-not-touch positively.
5. Any `open` ND.N whose matrix names this step has `acknowledged: false`.

A session whose handshake fails does **not proceed**. It halts, reports the failing field(s) to the native, and waits for either a corrected handshake or explicit native override.

---

## §4 — Integration with Cowork thread-naming rule

Per `CONVERSATION_NAMING_CONVENTION_v1_0.md §4`, the session proposes its Cowork thread name at the top of the first substantive response. The `cowork_thread_name` field in the handshake is the machine-readable mirror of that proposal. The handshake and the first response must agree.

---

## §5 — Worked example 1: rebuild-era session (STEP_7)

```yaml
session_open:
  session_id: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION
  cowork_thread_name: "Madhav 07 — Governance Integrity Implementation"
  agent_name: claude-opus-4-7
  agent_version: claude-opus-4-7
  step_number_or_macro_phase: STEP_7
  predecessor_session: STEP_6_GOVERNANCE_INTEGRITY_DESIGN
  mandatory_reading_confirmation:
    - file: CLAUDE.md
      fingerprint_sha256: bdfe753ebabc2e0748c717482feed5dcd17029fff0918e53a319fce2902fdeb6
      read_at: 2026-04-24T00:30:00+05:30
    # STEP_LEDGER retired (GOVERNANCE_CLOSED 2026-04-24) — replaced by CURRENT_STATE_v1_0.md
    - file: 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
      fingerprint_sha256: "<read-at-session-open>"
      read_at: 2026-04-24T00:30:00+05:30
    - file: 00_ARCHITECTURE/STEP_BRIEFS/STEP_07_GOVERNANCE_INTEGRITY_IMPLEMENTATION_v1_0.md
      fingerprint_sha256: "<read-at-session-open>"
      read_at: 2026-04-24T00:30:00+05:30
    - file: 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
      fingerprint_sha256: 799ce848d4fb2a2b0a6668e316788bf374da09e6ce158fab2dd871084cf5cd10
      read_at: 2026-04-24T00:30:00+05:30
    - file: 00_ARCHITECTURE/GROUNDING_AUDIT_v1_0.md
      fingerprint_sha256: "<read-at-session-open>"
      read_at: 2026-04-24T00:30:00+05:30
    - file: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
      fingerprint_sha256: 2fef28fdcfa54c425ce96c0dd82e8016a47d907545915139c39688f19ab451c3
      read_at: 2026-04-24T00:30:00+05:30
    - file: 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md
      fingerprint_sha256: 33f4e39c01ab0b9adf0469d70323bcb3b0c480573e6e94650ecfd57599b7b6d9
      read_at: 2026-04-24T00:30:00+05:30
    - file: 00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md
      fingerprint_sha256: b2b46f0806d526e251c984e864a1402cc0990f10365b563c66bcb5434c3e91c6
      read_at: 2026-04-24T00:30:00+05:30
  canonical_artifact_fingerprint_check:
    # During Step 7, CANONICAL_ARTIFACTS_v1_0.md does not yet exist — this row
    # is therefore filled in "n/a (artifact being produced this session)" per the
    # bootstrap rule: Step 7 is the session that creates CANONICAL_ARTIFACTS; it
    # cannot check against a registry it hasn't yet written. From Step 8 onward,
    # this block is fully populated.
    - canonical_id: MACRO_PLAN
      declared_fingerprint: "n/a (CANONICAL_ARTIFACTS not yet written)"
      observed_fingerprint: 2fef28fdcfa54c425ce96c0dd82e8016a47d907545915139c39688f19ab451c3
      match: "n/a-bootstrap"
  declared_scope:
    may_touch:
      - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
      - 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md
      - 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md
      - 00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md
      - platform/scripts/governance/*.py
      - platform/scripts/governance/schemas/*.yaml
      - .geminirules
      - .gemini/project_state.md
      - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json  # Supersedes FILE_REGISTRY (2026-04-27)
      - 00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md
      # STEP_LEDGER retired (GOVERNANCE_CLOSED 2026-04-24)
      - 00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md
      - 00_ARCHITECTURE/SESSION_LOG.md
      - CLAUDE.md                                # single-line addition only
      - 00_ARCHITECTURE/drift_reports/**
      - 00_ARCHITECTURE/schema_reports/**
      - 00_ARCHITECTURE/mirror_reports/**
    must_not_touch:
      - 025_HOLISTIC_SYNTHESIS/**
      - 01_FACTS_LAYER/**
      - 03_DOMAIN_REPORTS/**
      - 02_ANALYTICAL_LAYER/**
      - 06_LEARNING_LAYER/**
      - 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
      - 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md
      - 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
      - platform/src/**
      - platform/scripts/{citation_graph_builder,invariants_l1,corpus_common}.py  # existing corpus scripts
  mirror_pair_freshness_check:
    - pair_id: MP.1
      claude_side: CLAUDE.md
      gemini_side: .geminirules
      last_verified_on: 2026-04-24
      days_since_verification: 0
      stale: false
    - pair_id: MP.2
      claude_side: composite(SESSION_LOG + STEP_LEDGER + active plan pointers)
      gemini_side: .gemini/project_state.md
      last_verified_on: 2026-04-24
      days_since_verification: 0
      stale: false
    - pair_id: MP.3
      claude_side: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
      gemini_side: compact MP ref in .geminirules + .gemini/project_state.md
      last_verified_on: 2026-04-24
      days_since_verification: 0
      stale: false
    - pair_id: MP.4
      claude_side: 00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md
      gemini_side: Phase-B pointer in .gemini/project_state.md + .geminirules item #4
      last_verified_on: 2026-04-24
      days_since_verification: 0
      stale: false
    - pair_id: MP.5
      claude_side: 00_ARCHITECTURE/FILE_REGISTRY_v1_2.md
      gemini_side: canonical-path block in .geminirules
      last_verified_on: 2026-04-24
      days_since_verification: 0
      stale: false
    - pair_id: MP.6
      claude_side: 00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md
      gemini_side: null
      last_verified_on: 2026-04-24
      days_since_verification: 0
      stale: false
      claude_only: true
    - pair_id: MP.7
      claude_side: 00_ARCHITECTURE/SESSION_LOG.md
      gemini_side: null
      last_verified_on: 2026-04-24
      days_since_verification: 0
      stale: false
      claude_only: true
    - pair_id: MP.8
      claude_side: 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md
      gemini_side: compact architecture ref in .geminirules + .gemini/project_state.md
      last_verified_on: 2026-04-24
      days_since_verification: 0
      stale: false
  native_directive_obligations:
    # ND.1 RETIRED — this example block is historical only; no ND.1 obligation exists
    # ND.1 Mirror Discipline: RETIRED 2026-05-27 per native directive (Gemini collaboration inactive)
    # - directive_id: ND.1  # HISTORICAL EXAMPLE ONLY — DO NOT USE
    #   obligation_summary: "Implement mirror_enforcer.py..."
    #   acknowledged: true
  red_team_due: false
  notes: "Step 7 is the first session that produces the Integrity bundle; CANONICAL_ARTIFACTS self-bootstrap noted above."
```

---

## §6 — Worked example 2: post-rebuild-era session (M2.B.3)

*(Shown for forward-compatibility; the `step_number_or_macro_phase` schema tightens at Step 10, and `step_ledger_updated` is replaced by `current_state_updated` in the close-checklist.)*

```yaml
session_open:
  session_id: M2_B3_UCN_RETRIEVAL_BUNDLE
  cowork_thread_name: "Madhav M2.B3 — UCN retrieval bundle"
  agent_name: claude-opus-4-7
  agent_version: claude-opus-4-7
  step_number_or_macro_phase: M2.B.3
  predecessor_session: M2_B2_MSR_CITATION_INDEX
  mandatory_reading_confirmation:
    - file: CLAUDE.md
      fingerprint_sha256: <hex>
      read_at: <ts>
    - file: 00_ARCHITECTURE/CURRENT_STATE_v1_0.md     # Step 10 deliverable; replaces STEP_LEDGER post-rebuild
      fingerprint_sha256: <hex>
      read_at: <ts>
    - file: 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
      fingerprint_sha256: <hex>
      read_at: <ts>
    - file: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
      fingerprint_sha256: <hex>
      read_at: <ts>
    - file: 00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md
      fingerprint_sha256: <hex>
      read_at: <ts>
  canonical_artifact_fingerprint_check:
    - canonical_id: MSR
      declared_fingerprint: <hex-from-CA>
      observed_fingerprint: <hex-from-file>
      match: true
    - canonical_id: UCN
      declared_fingerprint: <hex-from-CA>
      observed_fingerprint: <hex-from-file>
      match: true
    - canonical_id: CANONICAL_ARTIFACTS
      declared_fingerprint: <hex-from-CA>
      observed_fingerprint: <hex-from-file>
      match: true
    - canonical_id: MACRO_PLAN
      declared_fingerprint: <hex-from-CA>
      observed_fingerprint: <hex-from-file>
      match: true
  declared_scope:
    may_touch:
      - 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md      # retrieval-bundle writes to UCN indexes
      - platform/scripts/retrieval/**
      - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md   # state transition
    must_not_touch:
      - 01_FACTS_LAYER/**                         # L1 is never edited mid-phase
      - 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
      - 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
  mirror_pair_freshness_check:
    # ... MP.1–MP.8 check ...
  native_directive_obligations: []   # ND.1 addressed at Step 7; no currently-open directive naming M2.B.3
  red_team_due: true                 # every 3rd-session cadence per MP §IS.8
  notes: "Retrieval-bundle assembly; P1/P2 fire at every chunk write."
```

---

## §7 — CLI invocation

From the repo root:

```bash
# Validate a handshake saved to disk
python3 platform/scripts/governance/schema_validator.py --handshake path/to/session_open.yaml

# Or validate the SESSION_LOG's latest open-block
python3 platform/scripts/governance/schema_validator.py --session-log 00_ARCHITECTURE/SESSION_LOG.md --check latest_open
```

Exit codes:
- `0` — handshake valid; session may proceed
- `1` — validation error (see stderr); session halts
- `2` — internal script error

---

## §8 — Related artifacts

- `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §F` — authoritative spec this template implements
- `SESSION_CLOSE_TEMPLATE_v1_0.md` — paired close checklist
- `CANONICAL_ARTIFACTS_v1_0.md` — canonical artifact fingerprints + mirror-pair inventory
- `CONVERSATION_NAMING_CONVENTION_v1_0.md` §4 — the thread-naming proposal rule
- `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` — directive list this template's `native_directive_obligations` block acknowledges

---

*End of SESSION_OPEN_TEMPLATE_v1_0.md.*
