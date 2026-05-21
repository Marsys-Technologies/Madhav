---
artifact: HUMAN_GATE_D
version: 1.0
status: OPEN
produced_during: GH-CORPUS-FRONTMATTER-BACKFILL
produced_on: 2026-05-21
gate_type: HALT_PARTIAL_COMPLETE
---

# Human Gate D — Corpus Frontmatter Backfill: Partial Complete + Learning Layer HALT

## Status

**PARTIAL COMPLETE + HALT**. The vast majority of frontmatter violations have been resolved. Two files in `06_LEARNING_LAYER/` require native arbitration before they can be fixed.

## What was completed (before HALT)

### AC.1 — Diagnosis
Completed. See `00_ARCHITECTURE/governance_hygiene_briefs/corpus_frontmatter/_DIAGNOSIS.md`.

Baseline: 208 violations (exit=2).
Post-fix: 58 violations (exit=2). Of these 58:
- 36 HIGH: session_log session_id disagreements — pre-existing, scope of separate brief (GH_SESSION_LOG_STRUCTURE)
- 2 HIGH: learning_layer_population_gate_violation on SIGNAL_WEIGHT_CALIBRATION — HALT (see below)
- 1 HIGH: learning_layer_stub_banner_missing on OBSERVATIONS/README.md — HALT (see below)
- 1 MEDIUM: frontmatter_missing[learning_layer_stub] on OBSERVATIONS/README.md — HALT (see below)
- 1 MEDIUM: current_state_last_session_id_disagreement — pre-existing, not a frontmatter issue
- 17 LOW: session_log_entry_missing_next_objective_heading — pre-existing, separate brief scope

**Frontmatter MEDIUM violations cleared: 116 of 118 (2 halted on learning_layer)**

### AC.2 — Authority check
Completed. Read `artifact_schemas.yaml`. Required fields confirmed.

### AC.3 — Backfill completed
- `00_ARCHITECTURE/*.md` — 83 MEDIUM violations cleared (65 `artifact:` added, 9 `frontmatter_missing` blocks added, 7 `version:` added)
- `03_DOMAIN_REPORTS/*.md` — 18 MEDIUM violations cleared (13 `artifact:` added, 2 `version:`+`status:` added for nested-metadata files, 3 `artifact:` added to loose-YAML)
- `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — 1 MEDIUM cleared (artifact: added)
- `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` — 1 MEDIUM cleared (artifact: added)
- `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` — 1 LOW cleared (artifact: added to loose-YAML)
- Also fixed 11 LOW loose-YAML `architecture_governance` violations (7 `artifact:` added, 4 `version:` added)

### AC.4 — learning_layer HALT (see below)

### AC.5 — CANONICAL_ARTIFACTS version_missing
Completed. 21 entries in `CAPABILITY_MANIFEST.json` updated with `version: "1.0"` (M9x tools + retrieval tools that had no version field).

### AC.6 — Partial
Schema_validator went from 208 → 58 violations. Frontmatter MEDIUM count → 2 (both HALT). Session_log HIGH count unchanged (separate brief). EXIT CODE remains 2 (was already 2 — session_log HIGH violations are pre-existing and out of scope for this brief).

### AC.7 — Partial
- drift_detector: exit 2 (unchanged from baseline — pre-existing HIGH fingerprint_mismatch findings)
- mirror_enforcer: exit 0 (unchanged)
- FORENSIC/LEL/CGM fingerprints updated in CAPABILITY_MANIFEST.json to reflect frontmatter additions.

## HALT conditions

### HALT.1 — SIGNAL_WEIGHT_CALIBRATION/README.md

**Violations:**
- `learning_layer_population_gate_violation` (HIGH×2): STATUS ACTIVE but `activation_session_id` missing + no `activation_lel_entry/ppl_entry`

**Root cause:**
The file has `status: ACTIVE-PENDING` in frontmatter and the body banner `STATUS: ACTIVE-PENDING (M4-A) — M3 CLOSED 2026-05-01. LEL gate CLEARED (46 events)...`.

The validator regex `^STATUS:\s*(STUB|ACTIVE)\s*[—-]\s*.*$` matches `ACTIVE-PENDING` because:
- It matches "ACTIVE" as the status tag
- The `-` in "-PENDING" is treated as the separator dash `[—-]`

This is a validator regex quirk — the file intends `ACTIVE-PENDING` as a compound status meaning "eligible for activation but pending a scoring rubric approval before first write."

**Options for native to choose:**
1. **Rename banner to STUB**: Change `STATUS: ACTIVE-PENDING (M4-A) — M3 CLOSED...` to `STATUS: STUB — M3 closed, LEL gate cleared, awaiting scoring rubric approval before first write`. This matches the schema's STUB class and eliminates the population gate requirement. Then remove `status: ACTIVE-PENDING` and replace with `status: STUB`.

2. **Promote to full ACTIVE**: Add `activation_session_id: M4-A-S2` (or the correct session) + `activation_lel_entry: EVT.*` (pointing to the first LEL event used). This formally activates the mechanism.

3. **Fix the validator regex**: Change the regex from `(STUB|ACTIVE)` to `(STUB|ACTIVE-PENDING|ACTIVE)` to handle the compound state. This requires a schema YAML edit (allowed per brief AC.3) + potentially a validator script edit (NOT allowed per brief hard constraints). Recommend option 1 or 2.

**What is NOT ambiguous:** The activation data (session ID, LEL entry) is not recorded in the file itself — only native knows which session first fired LL.1. That's why this halts.

### HALT.2 — OBSERVATIONS/README.md

**Violations:**
- `frontmatter_missing[learning_layer_stub]` (MEDIUM): No frontmatter `---` block found
- `learning_layer_stub_banner_missing` (HIGH): No STATUS banner found

**Root cause:**
The file has YAML-formatted content but without `---` delimiters — the YAML fields appear as plain text at the top of the file. The required field `mechanism_id` (e.g., `LL.N`) is not present and has no obvious value — OBSERVATIONS is a data directory, not a numbered Learning Layer mechanism.

**Options for native to choose:**
1. **Assign mechanism_id: OBSERVATIONS** (or a descriptive id): The `mechanism_id` field's required values are `LL.1 .. LL.10` per the schema. If OBSERVATIONS doesn't have an LL.N assignment, either assign one or declare it exempt.

2. **Exclude OBSERVATIONS from the learning_layer_stub schema class**: Add an exclusion note to `artifact_schemas.yaml` or rename the directory's README to something other than README.md (since the glob is `06_LEARNING_LAYER/*/README.md`). This would be a schema glob refinement per AC.3.

3. **Add minimal frontmatter without mechanism_id**: Accept the existing content fields (status: SCAFFOLD, produced_during: M4-A-T2-PPL-INFRA), add `---` delimiters, and set `mechanism_id: OBSERVATIONS` (a non-LL.N value). The validator may still flag this if it range-checks mechanism_id values.

**Recommended path:** Option 2 — update the `path_glob` in `artifact_schemas.yaml` to exclude `06_LEARNING_LAYER/OBSERVATIONS/README.md` specifically (using a negative pattern or restricting the glob). Then apply minimal frontmatter with `---` delimiters and no `mechanism_id` (since OBSERVATIONS is a data directory, not a mechanism stub).

## Next actions (what native needs to do)

1. For HALT.1 (SIGNAL_WEIGHT_CALIBRATION): Choose option 1 (STUB rename) or option 2 (full ACTIVE with activation session/LEL pointers). Native knows the activation session.

2. For HALT.2 (OBSERVATIONS): Choose how to handle the mechanism_id gap. Recommend option 2 (schema glob exclusion) or option 3 (accept non-standard mechanism_id).

3. After native provides guidance: The agent can apply the fix in a follow-up commit on this branch, then re-run the validator to confirm 0 learning_layer violations.

4. The PR on branch `governance-hygiene/corpus-frontmatter` is already open and contains all completed fixes. The learning_layer fixes can be added as additional commits before merge.

## Files already committed/staged on branch governance-hygiene/corpus-frontmatter

~100 files touched with frontmatter additions. See PR for full diff.
