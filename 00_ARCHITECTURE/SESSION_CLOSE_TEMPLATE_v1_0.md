---
artifact: SESSION_CLOSE_TEMPLATE_v1_0.md
version: 1.1
status: CURRENT
produced_during: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION (2026-04-24)
implements: GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §G
authoritative_side: tool-neutral (per-session instantiations are the governed provenance
  surface via SESSION_LOG + CURRENT_STATE_v1_0.md.)
mirror_obligations: >
  None for this template file itself. Per-session instantiations are appended to SESSION_LOG
  as the closing block of the session's entry; the Gemini-side mirror is the corresponding
  state-after reflected in `.gemini/project_state.md` per MP.2 adapted parity.
consumers:
  - Every Claude Code and Codex session closing on this project
  - `schema_validator.py` — validates the checklist YAML as its LAST action before SESSION_LOG
    append
  - `drift_detector.py` + `mirror_enforcer.py` — their exit codes feed the checklist's
    `drift_detector_run.exit_code` / `mirror_enforcer_run.exit_code` fields
  - Step 9 (CLAUDE.md rebuild) — absorbs the "emit session-close checklist before claiming
    close" instruction into CLAUDE.md's operating-principle list
  - Step 10 (SESSION_LOG schema retrofit) — swaps `step_ledger_updated` for `current_state_updated`
    post-rebuild
changelog:
  - v1.1 (2026-08-15, CODEX_ONBOARDING): Adds tool provenance and mandatory CCD,
    work-order, and remote lease-release synchronization for the shared Claude Code/Codex
    operating convention in GOVERNANCE_INTEGRITY_PROTOCOL §P.
  - v1.0 (2026-04-24, Step 7): Initial template. Produced per GOVERNANCE_INTEGRITY_PROTOCOL §G.
    Carries the mandatory-field schema, enforcement rules, and two worked examples
    (rebuild-era Step 7, post-rebuild-era M2.B.3).
  - v1.0 amended in-place (2026-04-26, Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1): Added
    `native_overrides[]` and `halts_encountered[]` optional blocks to §2 schema (per
    PORTAL_BUILD_TRACKER_PLAN_v0_1.md §9 G.2 + G.3; native approval Q.3 2026-04-26).
    Added `shards_emitted` + `cowork_ledger_referenced` fields to `build_state_serialized`
    block (per §9 G.1 + ONGOING_HYGIENE_POLICIES §O extension).
    LOW finding if optional blocks absent (existing closed sessions remain valid).
  - v1.0 amended in-place (2026-04-26, Madhav_BUILD_TRACKER_INTEGRATION_v0_1): Added
    `build_state_serialized` block to §2 schema, §5 worked example 1, and §6 worked
    example 2. Implements ONGOING_HYGIENE_POLICIES §O (build-state serialization at
    session close). See BUILD_TRACKER_DEPLOYMENT_NOTES.md §4.2.
---

# SESSION_CLOSE_TEMPLATE v1.0
## MARSYS-JIS Project — Session-Close Checklist

*Implements `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §§G, P`. Every Claude Code or Codex
session, before claiming close, emits a machine-readable checklist per this schema. The
checklist is the LAST thing `schema_validator.py` validates; only after it validates does
the SESSION_LOG append happen atomically.*

---

## §1 — How to use this template

1. As the session approaches close, the agent performs the close-side actions: runs the scripts (`drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py`), updates registries, appends SESSION_LOG, transitions STEP_LEDGER (rebuild era) or CURRENT_STATE (post-rebuild).
2. It emits a YAML `session_close` block per the schema in §2.
3. It passes the block to `schema_validator.py` (or equivalent in-session check).
4. If every field passes, SESSION_LOG.md is appended atomically — session_open block + body + session_close block → one entry.
5. If any field fails, the session does NOT close. It halts and either (a) fixes the failing item within-session, or (b) reports to the native with the failing fields and waits for decision.

Fields with `true|false` values must be `true` for close. `exit_code` fields must be `0`. `within_declared_scope: false` anywhere fails close. Mirror pairs with `both_updated_same_session: false` fail close unless the rationale names a declared Claude-only or Gemini-only pair (MP.6, MP.7 as of Step 7).

---

## §2 — The schema

```yaml
session_close:
  # ------------------------------------------------------------------
  # Identity (matches session_open.session_id)
  # ------------------------------------------------------------------
  session_id: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION
  closed_at: 2026-04-24T23:59:00+05:30
  tool: "Claude Code"
    # Required provenance: "Claude Code" or "Codex".

  # ------------------------------------------------------------------
  # Files touched (GA.21 closure; Axis C.5 hygiene enforcement)
  # ------------------------------------------------------------------
  files_touched:
    # One entry per file created/modified/superseded/archived/deleted this
    # session. `within_declared_scope: false` on any row fails close.
    - path: 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
      mutation_type: created
      sha256_before: null
      sha256_after: <hex>
      justification: "Step 7 P1 deliverable per protocol §E / §M.1"
      within_declared_scope: true
    - path: .geminirules
      mutation_type: modified
      sha256_before: <hex>
      sha256_after: <hex>
      justification: "ND.1 Step 7 obligation — re-authored to adapted parity"
      within_declared_scope: true
    # ... one row per touched file ...

  # ------------------------------------------------------------------
  # Registry updates (Axis C.5 hygiene enforcement)
  # ------------------------------------------------------------------
  registry_updates_made:
    file_registry:
      # Each touched-file row must correspond to a FILE_REGISTRY row update,
      # a GOVERNANCE_STACK amendment-log entry, OR an explicit "no registry
      # update required" entry with rationale. Orphan mutations fail schema.
      - row_before: "new"
        row_after: "CANONICAL_ARTIFACTS_v1_0.md | CURRENT | §9.1 row added"
        version_of_registry: "v1.3"
    governance_stack:
      - section: "§11 STEP_7 amendment log"
        entry_excerpt: "Step 7 of the Step 0→15 governance rebuild: CANONICAL_ARTIFACTS_v1_0 NEW CURRENT; drift_detector/schema_validator/mirror_enforcer scripts registered; .geminirules + project_state.md re-authored to ND.1 adapted parity; ND.1 status flipped open → addressed ..."
    canonical_artifacts:
      # CANONICAL_ARTIFACTS row changes (fingerprint rotation, version bump, etc.)
      - canonical_id: CLAUDE
        change: fingerprint_rotated
        details: "One-line addition for SESSION_OPEN_TEMPLATE pointer (protocol §M.1 P5)"
      - canonical_id: GEMINIRULES
        change: fingerprint_rotated
        details: "ND.1 re-author to adapted parity with Asymmetries section"

  # ------------------------------------------------------------------
  # Mirror updates propagated (ND.1; Axis C.6 enforcement)
  # ------------------------------------------------------------------
  mirror_updates_propagated:
    # For every mirror pair touched this session, confirm the counterpart was
    # updated in the same session (ND.1 claim 1). Declared Claude-only / Gemini-only
    # pairs have a required rationale when only one side is touched.
    - pair_id: MP.1
      claude_side_touched: true    # CLAUDE.md got the one-line addition
      gemini_side_touched: true    # .geminirules re-authored
      both_updated_same_session: true
      rationale: "Both sides updated 2026-04-24 in Step 7"
    - pair_id: MP.2
      claude_side_touched: true    # STEP_LEDGER + SESSION_LOG + STEP_7 close
      gemini_side_touched: true    # project_state.md re-authored
      both_updated_same_session: true
      rationale: "Composite state + Gemini mirror both refreshed"
    # ... MP.3 through MP.8 ...

  # ------------------------------------------------------------------
  # Red-team (cadence-bound)
  # ------------------------------------------------------------------
  red_team_pass:
    due: false                              # from session_open.red_team_due
    performed: false
    verdict: n/a                            # PASS | PASS_WITH_FIXES | FAIL | n/a
    artifact_path: null

  # ------------------------------------------------------------------
  # Governance scripts (Axes C.2 + C.3 + C.6 enforcement)
  # ------------------------------------------------------------------
  drift_detector_run:
    script: platform/scripts/governance/drift_detector.py
    exit_code: 0                            # OR known-deferred findings pattern
    report_path: 00_ARCHITECTURE/drift_reports/DRIFT_REPORT_STEP_7_v1_0.md
    divergences_found: 0
  schema_validator_run:
    script: platform/scripts/governance/schema_validator.py
    exit_code: 0
    report_path: 00_ARCHITECTURE/schema_reports/SCHEMA_VALIDATION_REPORT_STEP_7_v1_0.md
    violations_found: 0
  mirror_enforcer_run:
    script: platform/scripts/governance/mirror_enforcer.py
    exit_code: 0
    report_path: 00_ARCHITECTURE/mirror_reports/MIRROR_REPORT_STEP_7_v1_0.md
    desync_pairs: []                         # empty list at exit 0

  # ------------------------------------------------------------------
  # State transition
  # ------------------------------------------------------------------
  step_ledger_updated: true                  # rebuild era (Steps 0–15)
  current_state_updated: n/a                 # post-Step-10 field; n/a pre-Step-10
  session_log_appended: true

  # ------------------------------------------------------------------
  # Cross-tool synchronization and lease release
  # ------------------------------------------------------------------
  cross_tool_sync:
    ccd_entries_appended: []
    work_order_outcome_recorded: true
    work_order_surface: <owning-campaign-ledger-or-queue>
    lease_release_recorded: true
    lease_release_verified_on_remote: true
    next_session_can_resume_from:
      - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
      - 00_ARCHITECTURE/SESSION_LOG.md
      - 00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md

  # ------------------------------------------------------------------
  # Disagreement register
  # ------------------------------------------------------------------
  disagreement_register_entries_opened: []   # list of DR entry IDs if any opened this session
  disagreement_register_entries_resolved: [] # list of DR entry IDs resolved this session

  # ------------------------------------------------------------------
  # Native overrides (optional — LOW finding if absent)
  # Per PORTAL_BUILD_TRACKER_PLAN_v0_1.md §9 G.2 + §0.1 Q.3 (native approval 2026-04-26).
  # Populate when the native issued a mid-session directive that overrode the session's
  # declared scope, AC interpretation, or execution path. Schema validator does NOT require
  # this field; absence produces a LOW finding, not a close failure.
  # Backfill example: Madhav_M2A_Exec_5 AC.2 hard-stop / native override for Cloud SQL
  # (the canonical test case this field was designed to capture per Q.3 disposition).
  # ------------------------------------------------------------------
  native_overrides: []
  # Each entry: {override_id: "OVR.1", issued_at: "...", description: "...", scope_effect: "..."}

  # ------------------------------------------------------------------
  # Halts encountered (optional — LOW finding if absent)
  # Per PORTAL_BUILD_TRACKER_PLAN_v0_1.md §9 G.3 + §0.1 Q.3 (native approval 2026-04-26).
  # Populate when the session encountered a halt-and-ask event (AC blocked, blocker hit,
  # external dependency unavailable) that required native input before continuing.
  # Schema validator does NOT require this field; absence produces LOW, not close failure.
  # ------------------------------------------------------------------
  halts_encountered: []
  # Each entry: {halt_id: "HLT.1", occurred_at: "...", description: "...", resolution: "..."}

  # ------------------------------------------------------------------
  # Native-directive per-step verification
  # ------------------------------------------------------------------
  native_directive_per_step_verification:
    # For every ND.N whose matrix names this step, confirm the obligation
    # was addressed with evidence.
    # ND.1 RETIRED — this example block is historical only; no ND.1 obligation exists
    # ND.1 Mirror Discipline: RETIRED 2026-05-27 per native directive (Gemini collaboration inactive)
    # For post-2026-05-27 sessions, native_directive_per_step_verification should be []
    - directive_id: ND.1
      step: STEP_7
      obligation_addressed: true
      evidence: >
        HISTORICAL EXAMPLE ONLY — ND.1 RETIRED 2026-05-27. No current sessions carry
        ND.1 obligations. CANONICAL_ARTIFACTS §2 carries MP.1–MP.8 with per-pair
        mirror_obligations + enforcement rules. mirror_enforcer.py implemented and
        exits 0 against the full inventory. `.geminirules` and `.gemini/project_state.md`
        re-authored to adapted parity; each carries an Asymmetries section. ND.1 global
        status flipped from `open` to `addressed`.

  # ------------------------------------------------------------------
  # Build-state serialization (ONGOING_HYGIENE_POLICIES §O)
  # ------------------------------------------------------------------
  build_state_serialized:
    serialized: true                         # bool — serialize_build_state.py ran without error
    output_path: /tmp/build_state.json       # local copy path
    uploaded: true                           # bool — GCS upload succeeded
    gcs_uri: gs://marsys-jis-build-state/build-state.json
    schema_validated: true                   # bool — passed --validate-against-schema
    serializer_version: "0.2.0"
    shards_emitted: 0                        # int — number of session+phase shards written+uploaded
    cowork_ledger_referenced: true           # bool — COWORK_LEDGER.md read (or graceful empty)

  # ------------------------------------------------------------------
  # Close-criteria verdict + handoff
  # ------------------------------------------------------------------
  close_criteria_met: true                   # every checklist box green
  unblocks: "Step 8 (red-team on the Step 7 implementation) — status → ready"
  handoff_notes: >
    Step 8 is the red-team on this implementation. The next session reads the Step 8 brief
    + every artifact in §3 of this step + the two Step 7 reports (DRIFT_REPORT_STEP_7,
    SCHEMA_VALIDATION_REPORT_STEP_7). Cowork thread: `Madhav 08 — Governance Integrity
    Red-team`.
```

---

## §3 — Enforcement

Every field with a `true|false` value must be `true` for close. Any `exit_code: nonzero` fails close. Any `within_declared_scope: false` row fails close. Any mirror pair with `both_updated_same_session: false` fails close unless the rationale explains a declared Claude-only or Gemini-only pair (currently MP.6 GOVERNANCE_STACK, MP.7 SESSION_LOG).

The schema validator runs the checklist validation as its **last** action of the session. Only after the checklist validates does the SESSION_LOG append happen atomically. This prevents a half-written log from recording a "closed" session that in fact failed its checklist.

---

## §4 — Integration with STEP_LEDGER (rebuild era) and CURRENT_STATE (post-rebuild)

- **Rebuild era (Steps 0–15)**: `step_ledger_updated: true` is required. The `unblocks` field corresponds to the ledger's per-row `status` transition — the closing session moves its own row to `completed` and the next-in-sequence row to `ready`.
- **Post-rebuild (after Step 15 closes `GOVERNANCE_BASELINE_v1_0`)**: `current_state_updated: true` is required; `step_ledger_updated` is dropped (schema-amended away at Step 10).

---

## §5 — Worked example 1: rebuild-era session (STEP_7, close-moment)

*(Filled values reflect the expected state at Step 7 close; actual close will populate with observed hashes.)*

```yaml
session_close:
  session_id: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION
  closed_at: 2026-04-24T23:59:00+05:30
  files_touched:
    - path: 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
      mutation_type: created
      sha256_before: null
      sha256_after: <hex-at-close>
      justification: "Step 7 P1 deliverable — machine-readable canonical-path registry (protocol §E/§M.1)"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md
      mutation_type: created
      sha256_before: null
      sha256_after: <hex>
      justification: "Step 7 P1 deliverable — §F"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md
      mutation_type: created
      sha256_before: null
      sha256_after: <hex>
      justification: "Step 7 P1 deliverable — §G (this file)"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md
      mutation_type: created
      sha256_before: null
      sha256_after: <hex>
      justification: "Step 7 P1 deliverable — §K"
      within_declared_scope: true
    - path: platform/scripts/governance/drift_detector.py
      mutation_type: created
      sha256_before: null
      sha256_after: <hex>
      justification: "Step 7 P2 deliverable — §H"
      within_declared_scope: true
    - path: platform/scripts/governance/schema_validator.py
      mutation_type: created
      sha256_before: null
      sha256_after: <hex>
      justification: "Step 7 P2 deliverable — §I"
      within_declared_scope: true
    - path: platform/scripts/governance/mirror_enforcer.py
      mutation_type: created
      sha256_before: null
      sha256_after: <hex>
      justification: "Step 7 P2 deliverable — §J / ND.1"
      within_declared_scope: true
    - path: .geminirules
      mutation_type: modified
      sha256_before: 31c558b8506fe41f1e414ae6490e84eac64f0edd4b85ef4d0d5fb9cb974ae9a3
      sha256_after: <hex>
      justification: "ND.1 Step 7 obligation — re-authored to adapted parity + Asymmetries section; CANONICAL_ARTIFACTS now named as machine-enforceable inventory"
      within_declared_scope: true
    - path: .gemini/project_state.md
      mutation_type: modified
      sha256_before: fdef568adece8e973865d29e46387d5cb5e5b77b4db58e7207a5557935cb5ad4
      sha256_after: <hex>
      justification: "ND.1 Step 7 obligation — re-authored to adapted parity + Asymmetries section; Step 7 close state reflected"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/FILE_REGISTRY_v1_3.md
      mutation_type: created
      sha256_before: null
      sha256_after: <hex>
      justification: "Step 7 P3 deliverable — registers Step 7 artifacts; adds canonical_artifact_id + mirror_obligations columns"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/FILE_REGISTRY_v1_2.md
      mutation_type: superseded
      sha256_before: ac5dd59ec6859dfd6e5ff9c86ad2f3aa51fa536a542766725c62d1055d331173
      sha256_after: <hex>
      justification: "SUPERSEDED banner + frontmatter flipped by v1.3 introduction"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md
      mutation_type: modified
      sha256_before: 98c8da89a03b141e4fe75145d9ac7f6bedb89673b26ccbeca0390cf51a6c5b70
      sha256_after: <hex>
      justification: "§11 STEP_7 amendment log appended; §1 version-registry rows added for Step 7 artifacts"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/STEP_LEDGER_v1_0.md
      mutation_type: modified
      sha256_before: 68958f182071a0d78908fbb9487fc52a516763e5f76b19d5aced73b542159ef5
      sha256_after: <hex>
      justification: "Step 7 row → completed; Step 8 row → ready; History Step 7 closed entry appended"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md
      mutation_type: modified
      sha256_before: b2b46f0806d526e251c984e864a1402cc0990f10365b563c66bcb5434c3e91c6
      sha256_after: <hex>
      justification: "ND.1 status flipped `open` → `addressed`; Step 7 verification entry appended"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/SESSION_LOG.md
      mutation_type: modified
      sha256_before: 4a293979fc6b46671607f1623d99ea09928911ad46d863e2dc753dbe77ccf4b7
      sha256_after: <hex>
      justification: "STEP_7 session entry appended"
      within_declared_scope: true
    - path: CLAUDE.md
      mutation_type: modified
      sha256_before: bdfe753ebabc2e0748c717482feed5dcd17029fff0918e53a319fce2902fdeb6
      sha256_after: <hex>
      justification: "Single-line addition per protocol §M.1 P5 — SESSION_OPEN_TEMPLATE pointer"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/drift_reports/DRIFT_REPORT_STEP_7_v1_0.md
      mutation_type: created
      sha256_before: null
      sha256_after: <hex>
      justification: "Step 7 P4 deliverable"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/schema_reports/SCHEMA_VALIDATION_REPORT_STEP_7_v1_0.md
      mutation_type: created
      sha256_before: null
      sha256_after: <hex>
      justification: "Step 7 P4 deliverable"
      within_declared_scope: true
  registry_updates_made:
    file_registry:
      - row_before: "new file (v1.3)"
        row_after: "FILE_REGISTRY_v1_3.md — new CURRENT; §9.1 + §9.3 register all Step 7 artifacts; new canonical_artifact_id + mirror_obligations columns"
        version_of_registry: "v1.3"
    governance_stack:
      - section: "§11 STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION amendment log"
        entry_excerpt: "2026-04-24 — Step 7 of the Step 0→15 governance rebuild. CANONICAL_ARTIFACTS_v1_0 + three scripts + three templates + DISAGREEMENT_REGISTER + DRIFT_REPORT + SCHEMA_VALIDATION_REPORT produced ..."
    canonical_artifacts:
      - canonical_id: CLAUDE
        change: fingerprint_rotated
        details: "One-line addition for SESSION_OPEN_TEMPLATE pointer"
      - canonical_id: GEMINIRULES
        change: fingerprint_rotated
        details: "ND.1 re-author to adapted parity with Asymmetries section"
      - canonical_id: PROJECT_STATE
        change: fingerprint_rotated
        details: "ND.1 re-author"
      - canonical_id: FILE_REGISTRY
        change: version_bumped
        details: "v1.2 → v1.3"
  mirror_updates_propagated:
    - pair_id: MP.1
      claude_side_touched: true
      gemini_side_touched: true
      both_updated_same_session: true
      rationale: "MP.1 mirror refreshed per ND.1 claim 1 + 2"
    - pair_id: MP.2
      claude_side_touched: true
      gemini_side_touched: true
      both_updated_same_session: true
      rationale: "Claude composite state + Gemini project_state.md mirror both refreshed"
    - pair_id: MP.3
      claude_side_touched: false
      gemini_side_touched: false
      both_updated_same_session: true
      rationale: "MP.3 unchanged this session (MP v2.0 frozen per declared_scope.must_not_touch); no cascade required"
    - pair_id: MP.4
      claude_side_touched: false
      gemini_side_touched: false
      both_updated_same_session: true
      rationale: "PHASE_B_PLAN unchanged; no cascade"
    - pair_id: MP.5
      claude_side_touched: true      # FILE_REGISTRY v1.3 published
      gemini_side_touched: true      # .geminirules canonical-path block refreshed
      both_updated_same_session: true
      rationale: "FILE_REGISTRY version bump cascaded to .geminirules canonical-path block"
    - pair_id: MP.6
      claude_side_touched: true
      gemini_side_touched: false
      both_updated_same_session: true
      rationale: "Declared Claude-only per MP v2.2 §D.11.2 + CANONICAL_ARTIFACTS §2"
    - pair_id: MP.7
      claude_side_touched: true
      gemini_side_touched: false
      both_updated_same_session: true
      rationale: "Declared Claude-only per MP v2.2 §D.11.2 Step 5A decision"
    - pair_id: MP.8
      claude_side_touched: false
      gemini_side_touched: true      # .geminirules + project_state.md refreshed with compact ref
      both_updated_same_session: true
      rationale: "PROJECT_ARCHITECTURE unchanged; Gemini-side compact summary aligned at Step 7"
  red_team_pass:
    due: false
    performed: false
    verdict: n/a
    artifact_path: null
  drift_detector_run:
    script: platform/scripts/governance/drift_detector.py
    exit_code: 3                              # known-state MEDIUM/LOW residuals (pre-Step-9 deferrals)
    report_path: 00_ARCHITECTURE/drift_reports/DRIFT_REPORT_STEP_7_v1_0.md
    divergences_found: <populated-at-close>
  schema_validator_run:
    script: platform/scripts/governance/schema_validator.py
    exit_code: 0
    report_path: 00_ARCHITECTURE/schema_reports/SCHEMA_VALIDATION_REPORT_STEP_7_v1_0.md
    violations_found: 0
  mirror_enforcer_run:
    script: platform/scripts/governance/mirror_enforcer.py
    exit_code: 0
    report_path: 00_ARCHITECTURE/mirror_reports/MIRROR_REPORT_STEP_7_v1_0.md
    desync_pairs: []
  step_ledger_updated: true
  current_state_updated: n/a
  session_log_appended: true
  disagreement_register_entries_opened: []
  disagreement_register_entries_resolved: []
  # ND.1 RETIRED 2026-05-27 — example below is historical only; post-retirement sessions use []
  native_directive_per_step_verification:
    - directive_id: ND.1  # HISTORICAL EXAMPLE — ND.1 RETIRED 2026-05-27; new sessions: []
      step: STEP_7
      obligation_addressed: true
      evidence: "CANONICAL_ARTIFACTS §2 MP.1–MP.8 inventory; mirror_enforcer.py exit 0; Asymmetries sections in .geminirules and project_state.md; ND.1 status flipped open → addressed"
  build_state_serialized:
    serialized: true
    output_path: /tmp/build_state.json
    uploaded: true
    gcs_uri: gs://marsys-jis-build-state/build-state.json
    schema_validated: true
    serializer_version: "0.1.0"
  close_criteria_met: true
  unblocks: "Step 8 (Red-team on Integrity implementation) — status → ready"
  handoff_notes: >
    Step 8 reads the Step 8 brief, CLAUDE.md, STEP_LEDGER, every Step 7 deliverable in §3 of
    the Step 7 brief, and the two Step 7 reports. Red-team prompts seed from Step 7 brief §8
    (bypass-the-drift-detector test; CANONICAL_ARTIFACTS-vs-CLAUDE.md precedence test;
    PHASE_B_PLAN v1.0.2 partial-mirror recurrence test). Proposed Cowork thread:
    `Madhav 08 — Governance Integrity Red-team`.
```

---

## §6 — Worked example 2: post-rebuild-era close (M2.B.3)

*(Shown for forward-compatibility. Post-Step-10, `step_ledger_updated` is dropped and `current_state_updated: true` is required.)*

```yaml
session_close:
  session_id: M2_B3_UCN_RETRIEVAL_BUNDLE
  closed_at: <ts>
  files_touched:
    - path: 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md
      mutation_type: modified
      sha256_before: <hex>
      sha256_after: <hex>
      justification: "UCN retrieval-bundle indexes updated"
      within_declared_scope: true
    - path: 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
      mutation_type: modified
      sha256_before: <hex>
      sha256_after: <hex>
      justification: "M2.B.3 → M2.B.4 transition"
      within_declared_scope: true
  registry_updates_made:
    file_registry:
      - row_before: "UCN_v4_0 | 4.1 | CURRENT"
        row_after: "UCN_v4_0 | 4.2 | CURRENT (retrieval-bundle indexes)"
        version_of_registry: "v1.X"
    canonical_artifacts:
      - canonical_id: UCN
        change: fingerprint_rotated
        details: "Retrieval-bundle indexes appended to §R.X"
  mirror_updates_propagated:
    # ... MP.1–MP.8 ...
  red_team_pass:
    due: true                    # 3rd-session cadence per MP §IS.8
    performed: true
    verdict: PASS_WITH_FIXES
    artifact_path: 00_ARCHITECTURE/red_team_reports/RT_M2_B3_UCN_v1_0.md
  drift_detector_run: {exit_code: 0, report_path: ..., divergences_found: 0}
  schema_validator_run: {exit_code: 0, report_path: ..., violations_found: 0}
  mirror_enforcer_run:   {exit_code: 0, report_path: ..., desync_pairs: []}
  step_ledger_updated: n/a
  current_state_updated: true
  session_log_appended: true
  disagreement_register_entries_opened: []
  native_directive_per_step_verification: []     # no open directive names M2.B.3
  build_state_serialized:
    serialized: true
    output_path: /tmp/build_state.json
    uploaded: true
    gcs_uri: gs://marsys-jis-build-state/build-state.json
    schema_validated: true
    serializer_version: "0.1.0"
  close_criteria_met: true
  unblocks: "M2.B.4 (Cluster-extraction bundle)"
  handoff_notes: "M2.B.4 scope: cluster extraction across UCN's refreshed indexes."
```

---

## §7 — CLI invocation

```bash
# Validate a checklist saved to disk (pre-SESSION_LOG-append)
python3 platform/scripts/governance/schema_validator.py --close-checklist path/to/session_close.yaml

# Or validate the SESSION_LOG's latest close-block
python3 platform/scripts/governance/schema_validator.py --session-log 00_ARCHITECTURE/SESSION_LOG.md --check latest_close
```

---

## §7.9 — Layer-seal live-deployment guard (added 2026-06-22)

**Applies to any session that claims a LAYER seal (L1–L5).** A layer is NOT sealed by a green branch, a
green local build, or a "DONE" report — only by the LIVE deployed instance showing the layer's assets.
Before a layer-seal close-checklist validates, assert against the **RUNNING API** (the prod URL, and
localhost if that is the verification surface) — NOT the branch source files:

```
# Replace <base>/<layer>/<prefix>/<chartId> per the sealing layer (e.g. phala / ph / 9 assets).
curl -s <base>/api/cockpit/registry \
  | jq '[.data.assets[]|select(.layer=="<layer>")]|length'                    # must equal the expected count (e.g. phala == 9)
curl -s "<base>/api/cockpit/stats?chartId=<chartId>" \
  | jq '[.data.assets[]|select(.asset_id|startswith("<prefix>_"))|select(.state!="lit")]'   # must be []  (all lit)
gcloud run services describe amjis-web --region=asia-south1 \
  --format='value(status.traffic[0].revisionName)'                           # must correspond to the merge SHA
```

Rationale: the L4 cockpit-out-of-sync incident (2026-06-22) — the build was branch/worktree-complete but
`main`/prod/localhost served the OLD 5-asset registry, and the cockpit faithfully rendered stale data.
This guard makes "the live registry shows N assets lit, on the deployed revision" a hard close-gate,
closing the worktree-complete-≠-deployed trap (see `feedback_ac_must_verify_target_environment`). A
layer-seal close-checklist that cannot produce these three green assertions HALTS and does not claim the seal.

---

## §8 — Related artifacts

- `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §G` — authoritative spec this template implements
- `SESSION_OPEN_TEMPLATE_v1_0.md` — paired handshake
- `DISAGREEMENT_REGISTER_v1_0.md` — DR entries referenced in `disagreement_register_entries_opened`
- `CANONICAL_ARTIFACTS_v1_0.md` — declared fingerprints the `files_touched.sha256_before/after` cross-check against
- `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` — directive list this checklist's `native_directive_per_step_verification` block verifies

---

*End of SESSION_CLOSE_TEMPLATE_v1_0.md.*
