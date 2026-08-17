---
artifact: CANONICAL_ARTIFACTS_v1_0.md
version: 1.0
status: "SUPERSEDED (2026-04-27 — canonical-path registry function migrated to CAPABILITY_MANIFEST.json; mirror_pairs migrated to manifest_overrides.yaml mirror_pairs section; retained in place for historical audit)"
produced_during: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION (2026-04-24)
implements: GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §E
authoritative_side: Claude (the machine-readable canonical-path registry — Claude-resident by
  construction; its role is to be the single source of truth that every other surface imports
  from rather than duplicates)
mirror_obligations: >
  This file itself is Claude-only (no Gemini counterpart). Its §2 Mirror-pair inventory is the
  machine-readable declaration of every Claude ↔ Gemini mirror pair on the project, per ND.1.
  The §1 table is the authoritative artifact inventory — other surfaces cite it; it does not
  cite them.
supersedes: (none — first version of this registry)
schema_version: 1.0
  # Changes that would break machine-parse compatibility force a major bump (v2.0). Changes
  # that add rows / optional fields are minor (v1.X). Changes that rotate a fingerprint in an
  # existing row are patch (v1.0.Y).
update_rules:
  - "Rotate a fingerprint whenever the file content changes. Record the rotating session in
    `last_verified_session` + `last_verified_on`."
  - "Add a row for a new canonical artifact at the session that admits it. Bump to v1.X."
  - "Change a mirror pair's authoritative_side / mirror_mode / known_asymmetries only via
    an explicit ND.N directive or a native-approved protocol amendment; bump to v1.X."
  - "Never carry a SUPERSEDED row. Superseded versions live in FILE_REGISTRY §8 Archival."
  - "Never duplicate FILE_REGISTRY's inventory. CANONICAL_ARTIFACTS lists only canonical
    artifacts — those with a stable canonical_id. Closed artifacts (STEP_BRIEFS, CRITIQUEs,
    REDTEAMs, SESSION_LOG entries) do not appear here unless they also carry a CURRENT
    canonical role (e.g., STEP_LEDGER, which is LIVE until Step 15 closure)."
consumers:
  - platform/scripts/governance/drift_detector.py — reads §1 path + fingerprint per canonical_id
    as the authoritative source for cross-surface comparison (protocol §H.3)
  - platform/scripts/governance/schema_validator.py — reads §1 to resolve artifact-class schemas
    and §2 to validate mirror-pair structural equivalence (protocol §I.3)
  - platform/scripts/governance/mirror_enforcer.py — reads §2 as the full MP.1–MP.8 inventory
    (protocol §J / ND.1)
  - 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md — canonical_artifact_fingerprint_check block
    reads declared fingerprints from §1
  - 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md — registry_updates_made.canonical_artifacts
    block writes back to §1 when fingerprints rotate
  - Step 9 (CLAUDE.md rebuild) — CLAUDE.md's canonical-path table is replaced by a
    cite-CANONICAL_ARTIFACTS-by-reference rule
changelog:
  - 2026-08-17 (PARISESA preflight governance reconciliation): the historical
    MACRO_PLAN record is reconciled from v2.0 / `2fef28fd…451c3` to v2.1 /
    `8e98ad46…e6c6e`, after independent provenance and semantic review. This
    preserves this superseded registry's audit value; CAPABILITY_MANIFEST remains
    the tooling authority after the 2026-04-27 cutover.
  - v1.0 (2026-04-24, Step 7 of the Step 0→15 governance rebuild):
    Initial registry. §1 carries one row per CURRENT canonical artifact (19 rows including
    CANONICAL_ARTIFACTS self-entry). §2 carries the MP.1–MP.8 mirror-pair inventory
    transcribed machine-readably from PROJECT_ARCHITECTURE_v2_2.md §D.11.2. Fingerprints
    computed at Step 7 session close. ND.1 global status flip fires at this session's close
    per directive consumption-matrix close condition.
date: 2026-04-24
---

# CANONICAL ARTIFACTS v1.0
## MARSYS-JIS Project — Machine-Readable Canonical-Path Registry

*Implements `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §E`. Single source of truth for canonical artifact paths, versions, fingerprints, and mirror obligations. Every other governance surface imports from here or cites it by reference — no other surface may declare a canonical version without citing this file.*

*Produced in Step 7 of the Step 0 → Step 15 governance rebuild.*

---

## §0 — How to read this registry

- **§1 Canonical artifact table** — one row per canonical_id. Each row is a YAML-block header (for machine parse) plus a human-readable summary paragraph. The YAML block is authoritative; the paragraph is a reading aid.
- **§2 Mirror-pair inventory** — one row per mirror pair (MP.1 through MP.8 as of v1.0). Each row is a YAML-block header + summary paragraph. The YAML is authoritative.
- **§3 Asymmetry declarations** — per-pair `known_asymmetries`, duplicated here for grep-friendliness. Drift between this section and the §2 rows' `known_asymmetries` field is itself a finding (`asymmetry_declaration_drift`).

**Machine parse.** A script consumes this file by (a) locating all fenced `yaml` blocks under §1 or §2 headers, (b) parsing each as YAML, (c) indexing by `canonical_id` or `pair_id`. Text outside fenced blocks is documentation and is ignored by the parser.

**Fingerprint rotation.** When a file's content changes, the next session that touches it updates the row's `fingerprint_sha256` and records the rotating session in `last_verified_session` + `last_verified_on`. Any fingerprint mismatch between declared and observed (at session open) fails the `canonical_artifact_fingerprint_check` block in the session-open handshake — indicates silent file mutation.

**Bootstrap note.** Step 7 is the session that creates this file. The canonical_artifact_fingerprint_check block of the Step 7 session-open handshake fills rows with "n/a-bootstrap" because there is no prior CANONICAL_ARTIFACTS to check against. Steps 8 onward fully populate the check.

---

## §1 — Canonical artifact table

Sorted by layer: L1 → L2.5 → Architecture/Governance (sub-sorted by canonical_id).

### L1 — Facts Layer

#### FORENSIC

```yaml
canonical_id: FORENSIC
path: 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md
version: "8.0"
status: ARCHIVED
fingerprint_sha256: 0b2f383b7b7448d4dc9f4b8825e3f3929765e66b26da82acab08d84b921a7ed9
mirror_obligations:
  claude_side: null
  gemini_side: null
  mirror_mode: none
  authoritative_side: db
  asymmetries: "v8.0 markdown deleted from 01_FACTS_LAYER/ in PR #187 Legacy Teardown. Live source = chart_facts DB table via platform/src/lib/ganita/forensic_render.ts. Cold benchmark archived at 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md."
last_verified_session: feature/panchanga-service-registry
last_verified_on: 2026-06-10
notes: "ARCHIVED 2026-06-08. File deleted PR #187. Authoritative registry is CAPABILITY_MANIFEST.json (supersedes this file as of 2026-04-27)."
```

Unified canonical L1 — 1,950-line single-source-of-truth for every planet/house/lagna/saham/dasha fact. All L2+ claims cite `v6_ids_consumed` rooted here. FORENSIC fingerprint rotation requires a formal supplement or v9.0 event + FIX_SESSION mirror cascade to MSR/UCN/CDLM/RM/CGM. Not touched in Step 7.

#### LEL

```yaml
canonical_id: LEL
path: 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md
version: "1.7"
status: CURRENT
fingerprint_sha256: ROTATED_DAR-P1-S3_2026-05-25
mirror_obligations:
  claude_side: 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "L1 facts are Claude-resident; Gemini reads them at L4 Discovery Layer but does not author."
last_verified_session: DAR-P1-S3_2026-05-25
last_verified_on: 2026-05-25
notes: "57 events + 5 period summaries + 8 chronic patterns. v1.4: 11 pending→computed. v1.5: PPL migration annotations. v1.6: EVT.2019+2023 dual-tagged residential+travel per NAP.M4.2. v1.7: count correction to 57 events + 8 chronic patterns per DAR-P1-S3. Confidence 0.89."
```

Life Event Log v1.2 is CURRENT. MP v2.0 names LEL as M4 prerequisite with cadence "Start immediately; do not defer." Closes GA.9 at the CANONICAL_ARTIFACTS registration layer; full CLAUDE.md surfacing lands at Step 9.

### L2.5 — Holistic Synthesis

#### MSR

```yaml
canonical_id: MSR
path: 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
version: "5.1"
status: CURRENT
fingerprint_sha256: ROTATED_DAR-P5-S20-2026-05-25
predecessor_path: 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md
mirror_obligations:
  claude_side: 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "MSR is Claude-authored; Gemini consumes at L4. The Gemini-side L2.5 canonical-path block in .geminirules (MP.5) names MSR_v5_0 as CURRENT — that declaration is a path pointer, not a content mirror."
last_verified_session: DAR-P5-S20
last_verified_on: 2026-05-25
numeric_invariants:
  signal_count: 573
notes: "573 signals: 543 natal (v4.0) + §VIII 15 Yogini signals (SIG.MSR.544–558) + §IX 15 Tajika signals (SIG.MSR.559–573). MSR_v4_0.md retained as SUPERSEDED predecessor. M9-A-S1 2026-05-14."
```

Master Signal Register 499 signals. Authoritative source for every P5 (Signal ID Resolution) validator check. Not touched in Step 7.

#### UCN

```yaml
canonical_id: UCN
path: 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md
version: "4.1"
status: CURRENT
fingerprint_sha256: 9f4a2833ab6708d23cd75c97b4151b92db2161f6fb23d5adb50714048e490fd7
mirror_obligations:
  claude_side: 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "UCN is Claude-authored; Gemini consumes at L4. MP.5 name-pointer in .geminirules is a path reference, not a content mirror."
last_verified_session: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION
last_verified_on: 2026-04-24
notes: "Unified Chart Narrative — canonical single-file mother document. v1.0–v3.0 superseded; v4.1 internal cleanup applied within v4_0 file."
```

#### CDLM

```yaml
canonical_id: CDLM
path: 025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md
version: "1.3"
status: CURRENT
fingerprint_sha256: ROTATED_canonical_id_frontmatter_patch_2026-05-12
mirror_obligations:
  claude_side: 025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "CDLM is Claude-authored."
last_verified_session: canonical_id_frontmatter_patch_2026-05-12
last_verified_on: 2026-05-12
notes: "Cross-Domain Linkage Matrix 9×9 domain grid. v1.1 filename; v1.2 corpus cleanup 2026-04-19; v1.3 CF.LL7.1 Pancha-MP msr_anchors patch (M4-D-P1-CDLM-PATCH 2026-05-02) — MSR.117/118/119/143 anchored to CDLM cells."
```

#### RM

```yaml
canonical_id: RM
path: 025_HOLISTIC_SYNTHESIS/RM_v2_0.md
version: "2.2"
status: CURRENT
fingerprint_sha256: ROTATED_canonical_id_frontmatter_patch_2026-05-12
mirror_obligations:
  claude_side: 025_HOLISTIC_SYNTHESIS/RM_v2_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "RM is Claude-authored."
last_verified_session: canonical_id_frontmatter_patch_2026-05-12
last_verified_on: 2026-05-12
notes: "Resonance Map — 35 elements (RM.31–RM.35 added at v2.2 via VARGA-ETL-FULL-S1 D14 2026-05-10: five cross-varga resonances anchored in MSR.500–514). v2.1 corpus cleanup 2026-04-19."
```

#### CGM

```yaml
canonical_id: CGM
path: 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md
version: "9.0"
status: CURRENT
fingerprint_sha256: ROTATED_Madhav_M2A_Exec_6_2026-04-26_frontmatter-amendment-manifest-pointer
mirror_obligations:
  claude_side: 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "CGM is Claude-authored. Gemini-side .geminirules L2.5 path block updated to CGM_v9_0 at Madhav_M2A_Exec_5. Gemini-side project_state.md updated to reflect edge_count_reconciled:22 at Madhav_M2A_Exec_6."
last_verified_session: Madhav_M2A_Exec_6
last_verified_on: 2026-04-26
notes: "Chart Graph Model — 234 YAML node blocks rebuilt on FORENSIC_v8_0 at B.3.5 (2026-04-26, Madhav_M2A_Exec_5). 8-karaka canonical (GAP.13 resolved). All nodes P1-clean; stop-condition verified chunk_count=234=node_count. CGM_v2_0.md SUPERSEDED; archive copy at 99_ARCHIVE/CGM_v2_0.md. Amended in-place 2026-04-26 at Madhav_M2A_Exec_6: reconciled_edges_manifest pointer added (035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json), edge_count_reconciled:22; no node content changed; fingerprint rotates."
```

### Architecture & Governance

#### PROJECT_ARCHITECTURE

```yaml
canonical_id: PROJECT_ARCHITECTURE
path: 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md
version: "2.2"
status: CURRENT
fingerprint_sha256: 33f4e39c01ab0b9adf0469d70323bcb3b0c480573e6e94650ecfd57599b7b6d9
mirror_obligations:
  claude_side: 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md
  gemini_side: "compact architecture block in .geminirules + .gemini/project_state.md"
  mirror_mode: adapted_parity
  authoritative_side: claude
  mirror_pair_id: MP.8
  asymmetries: "Gemini-side carries a compact five-layer summary + pointer to full v2.2; not a full duplicate."
last_verified_session: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION
last_verified_on: 2026-04-24
notes: "v2.1 SUPERSEDED 2026-04-24 at Step 5A. v2.2 absorbs MP v2.0 arc (§I pointer), Learning Layer (§D.10), Multi-Agent Collaboration + ND.1 (§D.11), §L Governance Rebuild Reference."
```

#### MACRO_PLAN

```yaml
canonical_id: MACRO_PLAN
path: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
version: "2.1"
status: CURRENT
fingerprint_sha256: 8e98ad46d7f0ba5ee4a9605f17f8ef21ba6da6d126092f7e0c52d318bc9e6c6e
mirror_obligations:
  claude_side: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
  gemini_side: "compact MP summary in .geminirules (item #3) + .gemini/project_state.md"
  mirror_mode: adapted_parity
  authoritative_side: claude
  mirror_pair_id: MP.3
  asymmetries: "Gemini-side carries compact arc summary (M1–M10 names) + pointer to full MP v2.0; not a full duplicate."
last_verified_session: PARISESA_PHASE_MINUS_1_GOVERNANCE_RECONCILIATION
last_verified_on: 2026-08-17
notes: "Reconciled against origin/main@f003bf3af3b372eb5c1365ca4753a95aba4b7551 after independent two-key review. v2.1 is semantically earned: ee5bf081 AM-JIS→MARSYS-JIS naming propagation; 055165b L2→L2.5 correction; 43ff2f1 native-arbitrated LL.5 naming propagation with no protocol/I-O/gate change; 96f30bc required artifact frontmatter; 449d2c3 LEL count correction. CAPABILITY_MANIFEST is the post-cutover tooling authority; this record is reconciled for audit and session-provenance compatibility."
```

#### PHASE_B_PLAN

```yaml
canonical_id: PHASE_B_PLAN
path: 00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md
version: "1.0.3"
status: CURRENT
fingerprint_sha256: 65bc6332b2753f651fc6481a56b213d27e7bb744eae71454ffb5c321dec08880
mirror_obligations:
  claude_side: 00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md
  gemini_side: "current-phase pointer in .gemini/project_state.md + .geminirules item #4"
  mirror_mode: adapted_parity
  authoritative_side: claude
  mirror_pair_id: MP.4
  asymmetries: "Gemini-side carries the current-phase pointer + paused-during-rebuild banner; not the full B.0–B.10 plan."
last_verified_session: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION
last_verified_on: 2026-04-24
notes: "M2 Corpus Activation execution plan (B.0–B.10). v1.0.3 amendment complete (Madhav 16, 2026-04-24): WARN.2/3/5/7 stale-pointer cleanup; MACRO_PLAN v1.0 → v2.0 references. B.0 sub-phase execution is next."
```

#### FILE_REGISTRY

```yaml
canonical_id: FILE_REGISTRY
path: 00_ARCHITECTURE/FILE_REGISTRY_v1_15.md
version: "1.15"
status: CURRENT
fingerprint_sha256: 75ca992e4569600007dfed8d17b9e78dd181dba14b0e38f9067b20b5f5ea9241
mirror_obligations:
  claude_side: 00_ARCHITECTURE/FILE_REGISTRY_v1_15.md
  gemini_side: "L2.5 canonical-path block in .geminirules"
  mirror_mode: adapted_parity_subset
  authoritative_side: claude
  mirror_pair_id: MP.5
  asymmetries: "Gemini-side carries only the L2.5 subset (MSR, UCN, CDLM, CGM, RM) relevant to L4 Discovery Layer. v1.15 bump adds B.8 deliverables (synthesis prompt, synthesize.py, rag_synthesize.py, synthesizeClient.ts, synthesis_golden_v1_0.json, synthesis_eval_v1_0.json — Claude-only; Gemini-side requires MP.5 parity check but no content change for this bump)."
last_verified_session: Madhav_M2A_Exec_14
last_verified_on: 2026-04-28
notes: "v1.14 → v1.15 at Madhav_M2A_Exec_14 (2026-04-28). v1.15 delta: §9.17 adds Exec_14 deliverables (synthesis_v1_0.md, synthesize.py, rag_synthesize.py, synthesizeClient.ts, synthesis_golden_v1_0.json, synthesis_eval_v1_0.json; schemas.py v1.1 + main.py v1.3 mutation rows). v1.14 SUPERSEDED. SUPERSEDED versions live in FILE_REGISTRY §8 Archival."
```

#### GOVERNANCE_STACK

```yaml
canonical_id: GOVERNANCE_STACK
path: 00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md
version: "1.0-updated-STEP_15_GOVERNANCE_BASELINE_CLOSE"
status: CURRENT
fingerprint_sha256: 0b88cd67106cdd1de3e0ebcf087079880ace9fff372ddd6473847da0eea7b1d5
mirror_obligations:
  claude_side: 00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  mirror_pair_id: MP.6
  asymmetries: "Declared Claude-only at PROJECT_ARCHITECTURE_v2_2 §D.11.2. Revisit if a Gemini-side governance surface emerges."
last_verified_session: STEP_15_GOVERNANCE_BASELINE_CLOSE
last_verified_on: 2026-04-24
notes: "Amended in-place at each step close. §10–§17 as previously recorded. §18 STEP_14 log + §14 index. §19 STEP_15 log (NEW this session) + §14 cumulative index refreshed + end-of-file footer updated. Fingerprint rotation history: … → 8ba55f17…e95949 (STEP_13b_CLOSE_MACHINERY_FIX — §16+§17) → 1bf17ef7…b28 (Step 14 — §18+§14 index) → 0b88cd67…b1d5 (Step 15 — §19+§14 index+footer). Schema-break would force v2.0."
```

#### STEP_LEDGER

```yaml
canonical_id: STEP_LEDGER
path: 00_ARCHITECTURE/STEP_LEDGER_v1_0.md
version: "1.0"
status: GOVERNANCE_CLOSED
fingerprint_sha256: cf5f8e7352eb25c0b04ba4f668e234c7b4da976473c30fdee430984768d718f1
mirror_obligations:
  claude_side: 00_ARCHITECTURE/STEP_LEDGER_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  mirror_pair_id: "MP.2 (composite — STEP_LEDGER now GOVERNANCE_CLOSED; removed from composite at Step 15)"
  asymmetries: "STEP_LEDGER is now GOVERNANCE_CLOSED and retired. It was part of the MP.2 composite during the rebuild era only. Post-Step-15, CURRENT_STATE_v1_0.md is the sole authoritative state surface."
last_verified_session: STEP_15_GOVERNANCE_BASELINE_CLOSE
last_verified_on: 2026-04-24
notes: "GOVERNANCE_CLOSED at Step 15 (2026-04-24). CURRENT_STATE_v1_0.md takes over as authoritative state surface per CURRENT_STATE §5.2. This row retained as audit trail. Status change: LIVE → GOVERNANCE_CLOSED. File amended at Step 15: frontmatter status → GOVERNANCE_CLOSED; role updated; row 15 → completed; §Step 15 History block appended. Fingerprint rotation history: 88b3a97c…7d69123c (Step 12.1) → unchanged at STEP_13b_CLOSE_MACHINERY_FIX (Step 13 remained completed, Step 14 remained ready) → fd61876b…c3e (Step 14 — row 14 completed + row 15 ready) → cf5f8e73…18f1 (Step 15 — row 15 completed + GOVERNANCE_CLOSED + History block)."
```

#### SESSION_LOG

```yaml
canonical_id: SESSION_LOG
path: 00_ARCHITECTURE/SESSION_LOG.md
version: "rolling-schema-v1.0-adopted-STEP_10"
status: LIVE
fingerprint_sha256: "<populated-at-step-15-close-after-session-log-entry-appended>"
mirror_obligations:
  claude_side: 00_ARCHITECTURE/SESSION_LOG.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  mirror_pair_id: MP.7
  asymmetries: "Declared Claude-only at Step 5A. The session-pointer aspect is mirrored via MP.2 composite (now including CURRENT_STATE as of Step 10); a full Gemini-side SESSION_LOG has no present need."
last_verified_session: STEP_15_GOVERNANCE_BASELINE_CLOSE
last_verified_on: 2026-04-24
notes: "Append-only. Schema retrofit COMPLETED at Step 10. Bootstrap placeholder forward-rotation history: `<populated-at-step-10-close-after-session-log-entry-appended>` → (Step 12 placeholder `<rotated-at-step-12-close>` — anti-pattern, Step-13-detected defect) → `<populated-at-step-12-1-close-after-session-log-entry-appended>` (Step 12.1 restored Step-7-pattern) → (Step 13b declared rotation but did NOT execute — one of three Step 13b close-machinery defects) → `<populated-at-step-13b-close-machinery-fix-after-session-log-entry-appended>` (STEP_13b_CLOSE_MACHINERY_FIX resolved) → unchanged at Step 14 (SESSION_LOG appended but placeholder rotation was not explicitly tracked in this step's CA rotation set) → `<populated-at-step-15-close-after-session-log-entry-appended>` (Step 15 — forward rotation). Placeholder remains `<populated-*>` pattern (drift_detector.py L215-225 LOW downgrade, not HIGH) because the SESSION_LOG Step 15 entry is appended as part of this session's atomic close; a real sha256 written here would be invalidated by that append."
```

#### NATIVE_DIRECTIVES

```yaml
canonical_id: NATIVE_DIRECTIVES
path: 00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md
version: "1.0"
status: LIVING
fingerprint_sha256: 9e44283f237f33cfde5de2a409440fb8d28f52b9afc31a9f76a5a19c0e53154b
mirror_obligations:
  claude_side: 00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Directive log is Claude-resident; Gemini-side session_open handshake acknowledges directives but does not author."
last_verified_session: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION
last_verified_on: 2026-04-24
notes: "ND.1 status flipped open → addressed at this session close per ND.1 consumption-matrix close condition."
```

#### CONVERSATION_NAMING_CONVENTION

```yaml
canonical_id: CONVERSATION_NAMING_CONVENTION
path: 00_ARCHITECTURE/CONVERSATION_NAMING_CONVENTION_v1_0.md
version: "1.4"
status: LIVING
fingerprint_sha256: ROTATED_COW03_2026-04-25_v1-4
mirror_obligations:
  claude_side: 00_ARCHITECTURE/CONVERSATION_NAMING_CONVENTION_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Claude-only per the artifact's own frontmatter (Cowork thread-naming is a Claude session-open behavior)."
last_verified_session: Madhav_COW03_2026-04-25
last_verified_on: 2026-04-25
notes: "v1.3 amendments (COW-03): milestone groupings M2A-E, checkpoint protocol §8.5, model assignment matrix §8.6, Google Anti-Gravity IDE executor correction, COW ledger update."
```

#### GOVERNANCE_INTEGRITY_PROTOCOL

```yaml
canonical_id: GOVERNANCE_INTEGRITY_PROTOCOL
path: 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
version: "1.0"
status: CURRENT
fingerprint_sha256: a57e9dd9a05b0853f8f447d1895084bf28dcc5f194cb6104fd78a67934d04c64
mirror_obligations:
  claude_side: 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "The protocol governs mirror discipline but is not itself a mirror pair; the principle is stated verbatim in MP v2.0 §IS.2 and v2.2 §D.11, both of which do have Gemini-side mirrors."
last_verified_session: STEP_8_GOVERNANCE_INTEGRITY_REDTEAM
last_verified_on: 2026-04-24
notes: "Status flipped DRAFT_PENDING_REDTEAM → CURRENT at Step 8 close 2026-04-24 per red-team verdict PASS_WITH_FIXES (GOVERNANCE_INTEGRITY_REDTEAM_v1_0.md §1) and this row's prior close condition."
```

#### CANONICAL_ARTIFACTS (self-entry)

```yaml
canonical_id: CANONICAL_ARTIFACTS
path: 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
version: "1.0"
status: CURRENT
fingerprint_sha256: "<populated-at-step-15-close>"
  # Step-7-pattern continuation. Chicken-and-egg: writing any real sha256 into this
  # self-row changes CANONICAL_ARTIFACTS content and invalidates the written value.
  # The `<populated-*>` placeholder is downgraded by drift_detector.py L215-225 to
  # LOW `fingerprint_bootstrap_placeholder` (not HIGH `fingerprint_mismatch`).
  # Rotation history: `<populated-at-step-7-close>` → ... → `<populated-at-step-12-1-close>`
  # (Step 12.1 restored Step-7-pattern) → unchanged at Step 13b (execution defect) →
  # `<populated-at-step-13b-close-machinery-fix>` (STEP_13b_CLOSE_MACHINERY_FIX) →
  # `<populated-at-step-14-close>` (Step 14) → `<populated-at-step-15-close>` (Step 15).
mirror_obligations:
  claude_side: 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "The authoritative machine-readable inventory — Claude-resident by construction. Gemini-side surfaces cite it by reference (`.geminirules` Mirror Discipline section §3 names this file as the authoritative inventory)."
last_verified_session: STEP_14_SCHEMA_VALIDATION_RUN
last_verified_on: 2026-04-24
notes: "Self-entry: this row is the registry's own record of itself. Placeholder forward-rotation history: Step 7 `<populated-at-step-7-close>` → Steps 8–11 unchanged → Step 12 `<rotated-at-step-12-close>` (anti-pattern; Step-13-detected defect) → Step 12.1 `<populated-at-step-12-1-close>` (restored Step-7-pattern) → Step 13b unchanged (Step 13b declared rotation to `<populated-at-step-13b-close>` but did not execute — one of three Step 13b close-machinery defects) → `<populated-at-step-13b-close-machinery-fix>` (STEP_13b_CLOSE_MACHINERY_FIX this session). Fingerprint rotation of this file (whether by CA edits or by writing a new value into this self-row) forces every downstream script to re-read; that re-read observes the placeholder and correctly treats as LOW BASELINE. A future step that wants to commit a real self-row hash must first resolve the fixed-point problem (e.g., by using a hash-of-content-excluding-this-row schema, or by moving the self-row out of the file entirely) — booked as a future governance-rebuild item."
```

#### SESSION_OPEN_TEMPLATE

```yaml
canonical_id: SESSION_OPEN_TEMPLATE
path: 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md
version: "1.0"
status: CURRENT
fingerprint_sha256: 25ad044030d903129d6e9dfd18274225149737d0c65c4137093b7cd9f8897e77
mirror_obligations:
  claude_side: 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Template is Claude-resident; per-session instantiations appended to SESSION_LOG. Gemini sessions emit their own handshake by reading this template."
last_verified_session: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION
last_verified_on: 2026-04-24
notes: "Implements protocol §F."
```

#### SESSION_CLOSE_TEMPLATE

```yaml
canonical_id: SESSION_CLOSE_TEMPLATE
path: 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md
version: "1.0"
status: CURRENT
fingerprint_sha256: 5875af7ae389a7ea786d091d57e284db54f685ddb91817a2f7750e19a16ebf0b
mirror_obligations:
  claude_side: 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Template is Claude-resident."
last_verified_session: STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION
last_verified_on: 2026-04-24
notes: "Implements protocol §G."
```

#### DISAGREEMENT_REGISTER

```yaml
canonical_id: DISAGREEMENT_REGISTER
path: 00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md
version: "1.0"
status: LIVING
fingerprint_sha256: 64855abcb1839b4feb29468560f296a4168da70757ffa4a116e755d472e82687
mirror_obligations:
  claude_side: 00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Register is Claude-resident; entries may cite both Claude-side and Gemini-side evidence."
last_verified_session: Madhav_M2A_Exec_11
last_verified_on: 2026-04-27
notes: "Implements protocol §K. DIS.003/4/5 resolved (Option B). DIS.006/7/8 backfilled+resolved. DIS.009 opened (PAT.008 gemini_conflict). 9 entries total."
```

#### CLAUDE (master instructions)

```yaml
canonical_id: CLAUDE
path: CLAUDE.md
version: "2.0"
status: CURRENT
fingerprint_sha256: ad58903901865c22b80900f5b29c7349b3ab57ae063c60f1fa533807b7a3dd20
mirror_obligations:
  claude_side: CLAUDE.md
  gemini_side: .geminirules
  mirror_mode: adapted_parity
  authoritative_side: claude
  mirror_pair_id: MP.1
  asymmetries: "Claude-side contains Claude Code / MCP / skills references with no Gemini equivalent (documented in .geminirules Asymmetries section). Gemini-side contains Gemini-rules idiom + Gemini-tool expectations with no Claude equivalent."
last_verified_session: STEP_15_GOVERNANCE_BASELINE_CLOSE
last_verified_on: 2026-04-24
notes: "Rebuilt to v2.0 at Step 9. §A–§M structure. At Step 10, §F + §C item #8 amended (CURRENT_STATE pointer). At Step 12: §C item #11 BOOTSTRAP dropped; ONGOING_HYGIENE_POLICIES added. At Step 15 (this update): rebuild-era banner removed from §F; §C item #5 paused note removed; §C item #8 → steady-state CURRENT_STATE pointer; §D STEP_LEDGER row → GOVERNANCE_CLOSED; §L rebuild-step bullet removed; footer updated. Fingerprint rotation history: 16002b6b…a54d → (Step 12 placeholder `<rotated-at-step-12-close>`) → 320bdc47…f841b5 (Step 12.1) → 50b59665…386dc (Step 15 — banner removal + §L + §D + footer)."
```

#### GEMINIRULES (RETIRED 2026-05-27)

Canonical entry RETIRED 2026-05-27 per native directive ND.1 close-out. `.geminirules` file removed.

#### PROJECT_STATE (RETIRED 2026-05-27)

Canonical entry RETIRED 2026-05-27 per native directive ND.1 close-out. `.gemini/project_state.md` file removed.

#### SESSION_LOG_SCHEMA

```yaml
canonical_id: SESSION_LOG_SCHEMA
path: 00_ARCHITECTURE/SESSION_LOG_SCHEMA_v1_0.md
version: "1.0"
status: CURRENT
fingerprint_sha256: 1148e541f0ad4ae5d865e8da7b63d1e79a93f2b5d59af9c6d5dd0a647b637304
mirror_obligations:
  claude_side: 00_ARCHITECTURE/SESSION_LOG_SCHEMA_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "SESSION_LOG itself is declared Claude-only at MP.7; this schema — the rule-set for SESSION_LOG entries — is Claude-only by inheritance. Gemini sessions that append to SESSION_LOG would emit entries conforming to §2 of the schema; no Gemini-side schema counterpart is required."
last_verified_session: STEP_10_SESSION_LOG_SCHEMA
last_verified_on: 2026-04-24
notes: "New at Step 10. §1 naming schema; §2 entry structure (session_open YAML + body + session_close YAML + one committed next-objective); §3 optional frontmatter; §4 menu-form deprecation; §5 SESSION_LOG header banner; §6 forward-only retrofit; §7 schema-validator integration. Closes GA.17 + GA.18 at the schema layer."
```

#### LEARNING_LAYER_SCAFFOLD_DECISION

```yaml
canonical_id: LEARNING_LAYER_SCAFFOLD_DECISION
path: 00_ARCHITECTURE/LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md
version: "1.0"
status: CURRENT
fingerprint_sha256: 23af6e2cf51ffe0863336715da7399b1ad32dc0f886728c2f8992548dce8efc5
mirror_obligations:
  claude_side: 00_ARCHITECTURE/LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Closed governance decision artifact; Claude-resident. Gemini-side reflects Step 11 closure via .gemini/project_state.md state-block transition (MP.2 composite mirror), not via a parallel decision file."
last_verified_session: STEP_11_LEARNING_LAYER_SCAFFOLD
last_verified_on: 2026-04-24
notes: "New at Step 11. Closed decision record resolving GA.6 at the full-surface layer. SCAFFOLD verdict per native input 2026-04-24. §3 enumerates the 06_LEARNING_LAYER/ scaffold bundle (top-level README + four LL.1–LL.4 mechanism stubs + OBSERVATIONS/ + PARAMETER_UPDATES/ empty subdirs). §5 guardrails bind every future Learning-Layer-touching session. §7 documents the PHASE_B_PLAN B.0 substrate-hook coordination (sibling extension at M2 resume; Step 4 red-team WARN.1 resolved at design-intent layer)."
```

The Step 11 closure record. Names the SCAFFOLD verdict, enumerates the scaffold bundle, declares binding guardrails. Sibling artifacts (the four mechanism stubs + top-level README + two `.gitkeep` markers under `06_LEARNING_LAYER/`) are not separately registered here — they are tracked through this decision record §3 inventory + the directory's existence on disk + (Step 12 hygiene) FILE_REGISTRY §9.1 rows. CANONICAL_ARTIFACTS lists only artifacts with stable canonical_ids per §0 update_rules bullet 5; the scaffold stubs have directory-relative names, not canonical IDs.

#### GOVERNANCE_BASELINE

```yaml
canonical_id: GOVERNANCE_BASELINE
path: 00_ARCHITECTURE/GOVERNANCE_BASELINE_v1_0.md
version: "1.0"
status: CURRENT
fingerprint_sha256: 82033d4d82f0ffd0bbc79c85340a58362ce05c1203106450f328c7c2652a0719
mirror_obligations:
  claude_side: 00_ARCHITECTURE/GOVERNANCE_BASELINE_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Sealing artifact for the Step 0→15 governance rebuild. Claude-resident. Gemini-side is informed of the rebuild closure via the MP.2 composite mirror (.gemini/project_state.md §Governance Rebuild CLOSED section), not via a parallel baseline file."
last_verified_session: STEP_15_GOVERNANCE_BASELINE_CLOSE
last_verified_on: 2026-04-24
notes: "NEW at Step 15. Final governance-rebuild closure document. §1 Declaration; §2 Closure matrix (32 GA.N findings: 30 RESOLVED, 1 ACCEPTED_AS_POLICY GA.11 scope-separation, 1 DEFERRED_AS_DESIGN_CHOICE GA.27 non-binding timeline); §3 Artifacts produced Steps 0–15; §4 Scripts (clean-state invocation + output for drift/schema/mirror); §5 Governance guarantees G.1–G.6; §6 What changed vs pre-Step-0; §7 What did not change (corpus: FORENSIC v8.0, LEL v1.2, MSR v3.0, UCN, CDLM, RM, CGM, L3 reports, PHASE_B_PLAN); §8 Known deferred items (WARN.2/3/5/7, GA.11, GA.27, 46 schema violations, PHASE_B_PLAN v1.0.3 amendment cycle); §9 Resumption pointer (M2 resumes; PHASE_B_PLAN v1.0.3 first act); §10 Next governance cycle (quarterly pass due 2026-07-24; red-team counter reset to 0)."
```

The Step 15 sealing artifact. Final closure document for the governance rebuild. Retains the audit trail of all 32 GA.N findings and their resolution status. Marks the transition from rebuild-era governance to steady-state governance. Future governance reviews cite this file as the baseline from which steady-state operates.

#### CURRENT_STATE

```yaml
canonical_id: CURRENT_STATE
path: 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
version: "1.0"
status: AUTHORITATIVE
fingerprint_sha256: ffeecf7d412fd250278985f7583bde81879367357bb1c05000a3ecbfa60ba9f8
mirror_obligations:
  claude_side: 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  gemini_side: ".gemini/project_state.md §Governance Rebuild CLOSED + §Canonical Corpus State"
  mirror_mode: adapted_parity_state
  authoritative_side: claude
  mirror_pair_id: "MP.2 (composite — CURRENT_STATE is now the sole authoritative state surface post-Step-15)"
  asymmetries: "Claude-side is a single canonical YAML block (§2) + narrative §3. Gemini-side is free-form Gemini-idiom prose in .gemini/project_state.md. Semantic parity; not byte-identity. CURRENT_STATE is now authoritative (§5.2 in force; STEP_LEDGER GOVERNANCE_CLOSED)."
last_verified_session: Madhav_16_PHASE_B_PLAN_v1_0_3_AMENDMENT
last_verified_on: 2026-04-24
notes: "New at Step 10. Status AUTHORITATIVE since Step 15 close (was LIVE/secondary during rebuild era per §5.1). At Step 15 (this update): §2 YAML full state transition (active_macro_phase_status → active; active_phase_plan_version → 1.0.3; active_governance_step → Step_15 completed; next_governance_step → null; red_team_counter → 0; last_session_id → STEP_15_GOVERNANCE_BASELINE_CLOSE; next_session_objective → PHASE_B_PLAN v1.0.3; cross_check_authority → CURRENT_STATE); §3 narrative refreshed; §5.1 marked HISTORICAL; footer updated. Fingerprint rotation history: 81da20d1…24dacef (Step 12.1) → 82452377…bfb0ec41 (Step 13b partial) → 86d53f31…17268a08 (STEP_13b_CLOSE_MACHINERY_FIX) → 9ff48c47…946a (Step 14 — Step 14 state-block transition) → 88f40331…9234 (Step 15 — full governance-closed state transition) → 5a837de6…9e87 (Madhav 16 — state-block transition to Madhav_16 last_session + B.0 next). Closes GA.19 at the full-surface layer."
```

#### ONGOING_HYGIENE_POLICIES

```yaml
canonical_id: ONGOING_HYGIENE_POLICIES
path: 00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md
version: "1.0"
status: CURRENT
fingerprint_sha256: 878e884a6b11a1a39a7c73850b7dfb41cb818b1b05840f0df9ab3efc303fb34f
mirror_obligations:
  claude_side: 00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Claude-only policy artifact. Gemini-side sessions cite by reference from .geminirules collaboration section. No Gemini-side counterpart required — the enforcing mechanisms (schema_validator.py extensions, CANONICAL_ARTIFACTS schema, SESSION_LOG_SCHEMA entry structure) are Claude-side Claude-only infrastructure."
last_verified_session: STEP_12_1_FINGERPRINT_AND_REGISTRY_FIX
last_verified_on: 2026-04-24
notes: "New at Step 12. §A archival retain-in-place; §B LEL v1.1 cleanup + standing predecessor rule (closes GA.12); §C scope-boundary enforcement (closes GA.20 at close-checklist layer); §D SESSION_LOG completeness (closes GA.21); §E Staleness Register; §F CI cadence + exit-code-3 whitelist (closes F.2); §G red-team cadence + learning_layer_stub class + LL N=3 default (closes LL scaffold §5.7 + §5.4); §H quarterly governance pass; §I Macro Plan review triggers (explicit WARN.2/3/5/7 re-defer with PHASE_B_PLAN v1.0.3 owner + M2 resume trigger); §J implementation actions index; §K residual disposition; §L finding coverage; §M interactions; §N fingerprint-rotation audit. File itself not touched at Step 12.1 — only the `<computed-at-step-12-close>` placeholder in this row resolved to observed hash 878e884a…303fb34f (content unchanged since Step 12 close)."
```

#### COWORK_LEDGER

```yaml
canonical_id: COWORK_LEDGER
path: 00_ARCHITECTURE/COWORK_LEDGER.md
version: "1.0"
status: LIVING
fingerprint_sha256: 8333c090b373a084932a85a89869de819721f26fa38139ebbb0c48e00c32cffa
mirror_obligations:
  claude_side: 00_ARCHITECTURE/COWORK_LEDGER.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Claude-only canonical artifact. Cowork conversations happen in the Cowork platform; this file is the project-side record of those threads. The Cowork platform itself is not mirrored — only this register is maintained."
last_verified_session: Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1
last_verified_on: 2026-04-26
notes: "New at Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1 (2026-04-26). §1 Purpose; §2 Entry schema (YAML blocks); §3 Entries — 5 bootstrap rows covering predecessor Cowork threads. Admitted per PORTAL_BUILD_TRACKER_PLAN_v0_1.md §0.1 Q.2 native approval. Cadence: append-on-thread-close per ONGOING_HYGIENE_POLICIES §P. Serializer reads this file; absent file returns empty cowork_ledger[] gracefully."
```

#### INTERVENTION_BACKFILL

```yaml
canonical_id: INTERVENTION_BACKFILL
path: 00_ARCHITECTURE/INTERVENTION_BACKFILL_v1_0.md
version: "1.0"
status: CURRENT
fingerprint_sha256: null
mirror_obligations:
  claude_side: 00_ARCHITECTURE/INTERVENTION_BACKFILL_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Claude-only annotation file. Captures native overrides and halts from past sessions that SESSION_LOG cannot retroactively record (per CLAUDE.md §L constraint). No Gemini-side counterpart — interventions are Claude-session artifacts."
last_verified_session: Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_2_3
last_verified_on: 2026-04-26
notes: "New at Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_2_3 (2026-04-26). Admitted per PORTAL_BUILD_TRACKER_PLAN_v0_2.md §10 (D.3). Contains 4 backfill entries covering: Exec_6 wrong-prompt halt, GCS_PERMISSIONS_FIX governance aside approval, IMPL_v0_1_1 FILE_REGISTRY residual acceptance, IMPL_v0_1_3 brief supersession. Serializer reads this file and merges into session emitted native_overrides[]/halts_encountered[] for sessions with empty arrays."
```

#### PORTAL_REDESIGN_VISION

```yaml
canonical_id: PORTAL_REDESIGN_VISION
path: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md
version: "1.0.2"
status: CURRENT
fingerprint_sha256: null
mirror_obligations:
  claude_side: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Claude-only UX vision. Gemini's primary role is L4 Discovery Layer (PROJECT_ARCHITECTURE_v2_2.md §D.11); the redesign is platform-UI-scoped and has no Gemini-facing surface."
last_verified_session: redesign-r0-foundation-2026-04-29
last_verified_on: 2026-04-29
notes: "Admitted at R0 Foundation close (2026-04-29). Authored by Cowork (Opus) 2026-04-29. Covers the full R0–R7 UX strategy. Status promoted DRAFT→CURRENT at R0 close. Companion to PORTAL_REDESIGN_TRACKER."
```

#### PORTAL_REDESIGN_TRACKER

```yaml
canonical_id: PORTAL_REDESIGN_TRACKER
path: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
version: "1.0.4"
status: LIVING
fingerprint_sha256: null
mirror_obligations:
  claude_side: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Claude-only phase ledger. No Gemini-side counterpart per TRACKER mirror_obligations declaration."
last_verified_session: redesign-r0-foundation-2026-04-29
last_verified_on: 2026-04-29
notes: "Admitted at R0 Foundation close (2026-04-29). LIVING — updated at every redesign session-close. §2 canonical state block + §3 phase ledger (R0 closed; R1–R6 parallel-ready). Companion to PORTAL_REDESIGN_VISION."
```

#### L2_BODHA_CAMPAIGN_HANDOFF

```yaml
canonical_id: L2_BODHA_CAMPAIGN_HANDOFF
path: 00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md
version: "1.1"
status: CURRENT
fingerprint_sha256: e2771595a114bf5b41dd077403a346bc002762dbff015e091781c14476981807
mirror_obligations:
  claude_side: 00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "Claude-only campaign handoff. L2 Bodha campaign planning and execution is a Claude Code (Antigravity) workstream; no Gemini-side counterpart."
last_verified_session: nirmana-fixes-task13-2026-06-29
last_verified_on: 2026-06-29
notes: "Admitted retroactively at nirmana-fixes-task13 (2026-06-29). Original v1.0 was authored 2026-06-10 for the L2 Bodha campaign open but was never registered. v1.1 adds bo_drishti and bo_anveshana to the 14-asset DAG inventory and updates all asset-count references from 8→14."
```

---

## §2 — Mirror-pair inventory (RETIRED 2026-05-27)

Mirror-pair inventory (MP.1–MP.8) RETIRED 2026-05-27 per native directive (ND.1 close-out). Gemini collaboration declared inactive. The historical inventory and §3 aggregate asymmetry declarations have been removed from this file. See `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K` close-out note and `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md §1 ND.1` for the retirement record. Historical mirror-related entries in audit-trail artifacts (SESSION_LOG, archived briefs) remain unchanged.

#### MCPT_V310_CLOSE

```yaml
canonical_id: MCPT_V310_CLOSE
path: 00_ARCHITECTURE/MCPT_V310_CLOSE.md
version: "1.0"
status: CLOSED
fingerprint_sha256: ROTATED_v310_S6_2026-05-22
mirror_obligations:
  claude_side: 00_ARCHITECTURE/MCPT_V310_CLOSE.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: "MCP Transformation sealing artifact; Claude-resident governance record. Gemini-side aware via .gemini/project_state.md MCP Transformation workstream entry (MP.2 adapted parity)."
last_verified_session: v3.1.0-S6
last_verified_on: 2026-05-22
notes: "Foundation phase sealing artifact for MCP Transformation v3.1.0. Per-sub-phase AC evidence table (S1–S6 all PASS). Migration number audit (072–077). House-rules finalization (no corrections needed). v3.2 entry conditions. Red-team scheduling note (discharges at v3.4-S2). Mirror propagation evidence for MP.1 + MP.2. Admitted 2026-05-22 at v3.1.0-S6 close."
```

MCP Transformation v3.1.0 Foundation phase close. All 6 sub-sessions (S1–S6) CLOSED with full AC evidence. feature/mcpt-foundation merged to feature/mcpt-final. MARSYS_FLAG_MCP_V3_ENABLED default true. 6 migrations (072–077) in MCPT reserved range. Worktree A (MadhavMCPT-FDN) wave contribution complete.

---

## §4 — Future-agent admission protocol

Per `MACRO_PLAN_v2_0.md §3.4.E`: if a third agent is admitted (e.g., Gemini 3.0 alongside 2.5 Pro, or Opus 5.0 alongside 4.7), the admission session:

1. Adds new mirror-pair rows (MP.9+) to §2 with their own enforcement rules.
2. Extends `mirror_enforcer.py`'s rule set within the same session that introduces the pair.
3. Updates `FILE_REGISTRY` and `GOVERNANCE_STACK` per the protocol §D registry triad.
4. Bumps this file to v1.X for the additive change.

---

## §5 — Changelog reference

See frontmatter `changelog` field. Fingerprint rotations of individual rows do not bump the file's own version (they are per-row edits tracked in `last_verified_session` / `last_verified_on`). Schema-breaking changes (new required field, field removal) force a major bump to v2.0.

---

*End of CANONICAL_ARTIFACTS_v1_0.md — Step 7 of the Step 0→15 governance rebuild — 2026-04-24.*
