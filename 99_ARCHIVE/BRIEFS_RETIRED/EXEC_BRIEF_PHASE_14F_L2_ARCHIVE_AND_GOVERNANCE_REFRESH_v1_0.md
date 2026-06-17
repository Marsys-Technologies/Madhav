---
brief_id: EXEC_BRIEF_PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_v1_0.md and execute it."
phase: 14F
phase_name: L2 Archive Formal Close + Governance Documentation Refresh
risk_classification: LOW (zero platform code changes; zero DB changes; zero cloud changes; documentation + filesystem cleanup only)
parallelizable_with: [14A, 14B, 14C, 14D, 14E]
must_complete_before: [14G]
depends_on: [EXEC_BRIEF_PHASE_14_0_ASSET_INVENTORY_v1_0.md (COMPLETE — registry is canonical input)]
output_artifact: 00_ARCHITECTURE/PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_REPORT_v1_0.md
---

# EXEC_BRIEF — Phase 14F — L2 Archive Formal Close + Governance Refresh

## Mission

Phase 14.0 physically relocated all 7 L2 files (`02_ANALYTICAL_LAYER/*.md`) to `99_ARCHIVE/02_ANALYTICAL_LAYER/` via `git mv` and recorded the moves in `VALIDATED_ASSET_REGISTRY_v1_0.json`. This brief closes the L2 retirement formally by (a) disposing of the now-empty `02_ANALYTICAL_LAYER/` directory, (b) refreshing every governance-layer document that still treats L2 as a live layer, and (c) cleaning up the secondary documentation-drift findings flagged at 14.0 close (`025_HOLISTIC_SYNTHESIS/CLAUDE.md` outdated version pointers; `GOVERNANCE_STACK_v1_0.md` outdated CGM/MSR/MATRIX entries).

After this phase, the project's governance documents reflect a clean three-content-layer architecture (L1 Facts → L2.5 Holistic Synthesis → L3 Discovery Layer + L4 Federated/L5 Calibration), with L2 explicitly archived and pointer-referenced from the archive index. No production code path touches L2. No L2 file is consumed by the build pipeline (14B). No L2 entry exists in the live `CAPABILITY_MANIFEST.json` outside an `archived` block.

This brief is **parallelizable with 14A–14E**: it touches only governance markdown files, the empty L2 directory, and the registry's L2 entries. It must complete **before 14G** because Phase 14G's lockdown verification cross-checks that no governance document still treats L2 as live.

## Pre-flight gate

1. Verify Phase 14.0 is COMPLETE — frontmatter `status: COMPLETE` on `EXEC_BRIEF_PHASE_14_0_ASSET_INVENTORY_v1_0.md`.
2. Verify all 7 L2 files exist under `99_ARCHIVE/02_ANALYTICAL_LAYER/` (this is what 14.0 moved):
   - `CLAUDE.md`, `DEEP_ANALYSIS_Abhisek_Mohanty_v1.md`, `MATRIX_DASHA_PERIODS.md`, `MATRIX_DIVISIONALS.md`, `MATRIX_HOUSES.md`, `MATRIX_PLANETS.md`, `MATRIX_SIGNS.md`.
3. Verify `02_ANALYTICAL_LAYER/` exists and is empty (`find 02_ANALYTICAL_LAYER -type f` returns zero rows).
4. Verify `00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json` parses and contains the 7 L2 archive entries.
5. Confirm git working tree is clean (no uncommitted edits to governance docs).

If any fail, halt with a clear actionable message — do NOT attempt repair from this brief.

## Scope

**`may_touch`:**
- `02_ANALYTICAL_LAYER/` — directory removal (empty after 14.0).
- `025_HOLISTIC_SYNTHESIS/CLAUDE.md` — full rewrite (drift cleanup; Stream B).
- `00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md` — L2 section flip + CGM/MSR entry refresh (Stream C).
- `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md` — additive ARCHIVED-L2 note + L2 layer description amendment (Stream D).
- `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` — L2 reclassification fix at line ~315 (Stream D).
- `00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md` — survey + amend any L2-as-live references (Stream D).
- `00_ARCHITECTURE/DATA_INTEGRITY_AUDIT_PLAN_v1_0.md` — flip L2 references to "ARCHIVED" status (Stream D).
- `CLAUDE.md` (project root) — survey for L2 references; amend if any (Stream D).
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — verify zero L2 entries in active set; if any, move to `archived` block (Stream E).
- `00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json` — flip any L2 entry whose `status` is not yet `ARCHIVED` to `ARCHIVED` with `archived_in: PHASE_14F` (Stream E).
- `00_ARCHITECTURE/PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_REPORT_v1_0.md` (NEW — this brief's report).

**`must_not_touch`:**
- `99_ARCHIVE/**` — already-archived files stay archived; do NOT mutate frontmatter, content, or paths.
- `01_FACTS_LAYER/**` — L1 governance is owned by Phase 14C, not this brief.
- `025_HOLISTIC_SYNTHESIS/*.md` (the data files: MSR, UCN, CDLM, RM, CGM, RED_TEAM) — content owned by Phase 14D; ONLY `025_HOLISTIC_SYNTHESIS/CLAUDE.md` is in scope here.
- `035_DISCOVERY_LAYER/**` — L3 governance owned by Phase 14E.
- `06_LEARNING_LAYER/**` — calibration scope, not this brief.
- `platform/**` — zero platform code changes in this brief.
- `JHora/`, `Assets/`, `docs/`, `verification_artifacts/` — out of scope.
- **Concurrency boundaries** (parallel-with-14A-through-14E):
  - 14A may modify `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` and `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md` — if 14A is running concurrently, coordinate through git rebase, NOT silent overwrites.
  - 14B–14E will modify other architecture surfaces but NOT the L2-related governance files this brief owns.
  - **Lock rule**: this brief touches `CAPABILITY_MANIFEST.json` ONLY in the `archived` block; if 14A is mid-flight, it owns the active block additions. No conflict expected, but if `git status` shows manifest modifications mid-stream from another session, halt and surface.

## Sub-streams (6 sequential)

### Stream A — Empty L2 directory disposition

The directory `02_ANALYTICAL_LAYER/` is empty after 14.0's `git mv`. Decision: **delete the directory entirely.** Rationale: keeping an empty layer directory invites future drift (someone re-creates a file there assuming the layer is live). The archive at `99_ARCHIVE/02_ANALYTICAL_LAYER/` is the canonical historical record.

Steps:
1. Confirm `02_ANALYTICAL_LAYER/` is empty: `find 02_ANALYTICAL_LAYER -type f` → 0 rows. Halt if non-zero.
2. `rmdir 02_ANALYTICAL_LAYER` (will fail if any hidden files; halt and surface).
3. Stage the deletion: `git add -A 02_ANALYTICAL_LAYER`.
4. Verify `git status` shows the directory removal cleanly with no untracked stragglers.

### Stream B — `025_HOLISTIC_SYNTHESIS/CLAUDE.md` rewrite

Current file is materially wrong on three counts (verified 2026-04-28):
- References `PROJECT_ARCHITECTURE_v2_1` (current canonical: `v2_2`).
- Lists `CGM_v2_0.md` (current canonical: `CGM_v9_0.md`).
- Lists `MSR_v2_0.md` with "500 signals v2.1" (current canonical: `MSR_v3_0.md` with **499** signals per `CAPABILITY_MANIFEST.json`).

Rewrite the file end-to-end. Requirements:
1. Frontmatter pointers reference current canonical versions only.
2. Artifact table lists exactly: `UCN_v4_0.md`, `CGM_v9_0.md`, `MSR_v3_0.md`, `CDLM_v1_1.md`, `RM_v2_0.md`, `RED_TEAM_L2_5_v1_0.md`. Counts match `CAPABILITY_MANIFEST.json` (499 signals for MSR).
3. Whole-Chart-Read principle preserved (this is the load-bearing claim of the file).
4. Add explicit note: **"L2 (`02_ANALYTICAL_LAYER/`) was archived in Phase 14F (2026-04-28). All MATRIX_* and DEEP_ANALYSIS_* files are at `99_ARCHIVE/02_ANALYTICAL_LAYER/`. Do not cite L2 artifacts; the L2.5 stack above supersedes them."**
5. Replace `CGP_AUDIT` reference with the current canonical pointer (verify path in `01_FACTS_LAYER/CGP_AUDIT_v1_0.md`).

### Stream C — `GOVERNANCE_STACK_v1_0.md` L2 section flip

Lines 34–43 of `GOVERNANCE_STACK_v1_0.md` declare an "L2 — Analytical Layer (Mode A + Mode B)" section listing 5 MATRIX_* files as `CLOSED` and an unmentioned MATRIX_DASHA_PERIODS as another row. Plus the file's CGM entry references an old version per the 14.0 secondary findings.

Steps:
1. **L2 section flip**: replace the L2 — Analytical Layer table with a concise tombstone block:
   ```
   ### L2 — Analytical Layer (ARCHIVED 2026-04-28)
   
   The entire L2 layer was archived in Phase 14F. Files preserved at
   `99_ARCHIVE/02_ANALYTICAL_LAYER/` for historical audit only. The L2.5
   Holistic Synthesis stack (MSR, UCN, CDLM, RM, CGM) supersedes L2
   per `MARSYS_JIS_ARCHITECTURE_v1_0.md`. No production code path
   reads from L2.
   
   Predecessor entries: 7 files (DEEP_ANALYSIS_*, MATRIX_PLANETS,
   MATRIX_HOUSES, MATRIX_SIGNS, MATRIX_DIVISIONALS, MATRIX_DASHA_PERIODS,
   CLAUDE.md). See `VALIDATED_ASSET_REGISTRY_v1_0.json §archive_actions`.
   ```
2. **CGM entry refresh**: locate the L2.5 section's CGM row and update version → `9.0`, status → `CURRENT`. Cross-check against `CAPABILITY_MANIFEST.json` for the canonical version string before writing.
3. **MSR entry refresh**: same treatment — version → `3.0`, signal count → `499`, status → `CURRENT`. Verify against manifest.
4. Add a `## Changelog` entry: `2026-04-28 — Phase 14F: L2 section flipped to ARCHIVED tombstone; CGM v2.0 → v9.0; MSR v2.0 → v3.0 (499 signals).`

### Stream D — Architecture & plan documents survey + amend

Run a comprehensive grep for L2-as-live references across architecture and plan documents. Produce a survey table in the close report. Then amend each hit.

Survey scope (these files MUST be scanned):
- `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md`
- `00_ARCHITECTURE/MACRO_PLAN_v2_0.md`
- `00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md`
- `00_ARCHITECTURE/DATA_INTEGRITY_AUDIT_PLAN_v1_0.md`
- `CLAUDE.md` (project root)
- `00_ARCHITECTURE/CLAUDE.md` if present
- All other `*.md` files in `00_ARCHITECTURE/` whose `status` frontmatter is `CURRENT` or `LIVING`

Grep patterns:
- `02_ANALYTICAL_LAYER`
- `MATRIX_PLANETS|MATRIX_HOUSES|MATRIX_SIGNS|MATRIX_DIVISIONALS|MATRIX_DASHA`
- `DEEP_ANALYSIS_Abhisek`
- `\bL2\b` (word-boundary; filter out matches that mean "L2.5" or "L2 archive")

For each hit, classify:
- **HISTORICAL_OK** — appears in an audit report, session log, or AUDIT_REPORT_v1_0 historical record. Leave unchanged; these are point-in-time records.
- **LIVE_DRIFT** — appears in a CURRENT/LIVING governance doc as if L2 were active. **Amend.**

Known LIVE_DRIFT items (executor MUST handle these explicitly; the survey may surface more):
1. `MACRO_PLAN_v2_0.md` line ~315 — currently reads "*L2 signals register (MSR)*". MSR is L2.5, not L2. Amend to "*L2.5 signals register (MSR)*" or restructure the sentence to remove the L2 misclassification while preserving the M2 scope description.
2. `DATA_INTEGRITY_AUDIT_PLAN_v1_0.md` line ~15 + ~31 + ~43 + ~55 — reference `02_ANALYTICAL_LAYER/`, `MATRIX_PLANETS.md`, etc. as live audit targets. Amend each occurrence to either remove L2 from scope or re-point to `99_ARCHIVE/02_ANALYTICAL_LAYER/` with explicit ARCHIVED note.
3. `PROJECT_ARCHITECTURE_v2_2.md` — wherever L2 is described as a live layer in the architecture diagram or §C/§D layer enumeration, add an ARCHIVED-2026-04-28 note. Do NOT delete the L2 description (that's load-bearing historical context); annotate.

For each amendment, preserve the surrounding sentence's voice; do not rewrite paragraphs unless necessary.

Produce a `survey.json` artifact at `00_ARCHITECTURE/PHASE_14F_SURVEY.json` listing every grep hit, its classification, and (if amended) the diff hash. This becomes audit input for 14G.

### Stream E — Registry + manifest cross-check

1. Open `00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json`. For each L2 asset entry (asset_id starting with `L2_`), confirm `status: ARCHIVED`. If any are still `CURRENT` or unset, flip to `ARCHIVED` and add `archived_in: PHASE_14F`, `archived_at: 2026-04-28`.
2. Open `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`. Search for any active-block entries whose path contains `02_ANALYTICAL_LAYER` (excluding the `99_ARCHIVE/` archived block). Expected count: zero. If non-zero, halt with a clear error — this means 14.0 left a manifest entry behind.
3. Recompute manifest fingerprint after any edits; record old and new fingerprints in the close report.
4. If `manifest_overrides.yaml` has any L2 mirror_pair declarations, flip them to status `archived` and document.

### Stream F — Verification + commit + close report

1. Run `git status` — confirm only the in-scope files have changed.
2. Run any existing governance validators that are not gated on cloud connectivity:
   - `platform/scripts/governance/schema_validator.py` if invokable
   - `platform/scripts/governance/drift_detector.py --use-manifest` if invokable
   - `platform/scripts/governance/mirror_enforcer.py` if invokable
   Capture exit codes in the close report. Exit code 0 required for all three; exit code 3 (`known_residuals` whitelist) acceptable per `ONGOING_HYGIENE_POLICIES §F`.
3. Atomic commit with message: `Phase 14F: L2 archive formal close + governance refresh (drift cleanup)`. Include the close report and survey.json in the same commit.
4. Author `00_ARCHITECTURE/PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_REPORT_v1_0.md` covering:
   - Files modified (list with diff line counts)
   - L2 directory disposition (deleted / preserved with rationale)
   - Survey results (HISTORICAL_OK count, LIVE_DRIFT count, amended count)
   - Manifest fingerprint before/after
   - Validator exit codes
   - Findings flagged for downstream phases (e.g., if survey caught additional drift not anticipated here)
   - Native sign-off section (empty; awaiting "Phase 14F accepted" before 14G can verify)

## Done criteria

This brief is COMPLETE when ALL of the following are true:

1. `02_ANALYTICAL_LAYER/` directory does NOT exist in the working tree (deleted).
2. `99_ARCHIVE/02_ANALYTICAL_LAYER/` contains exactly 7 files (untouched from 14.0).
3. `025_HOLISTIC_SYNTHESIS/CLAUDE.md` references current canonical versions: PROJECT_ARCHITECTURE_v2_2, CGM_v9_0, MSR_v3_0 (499 signals), UCN_v4_0, CDLM_v1_1, RM_v2_0.
4. `GOVERNANCE_STACK_v1_0.md` L2 section is a tombstone pointing at `99_ARCHIVE/`. CGM entry = v9.0. MSR entry = v3.0 / 499.
5. `MACRO_PLAN_v2_0.md`, `PROJECT_ARCHITECTURE_v2_2.md`, `PHASE_B_PLAN_v1_0.md`, `DATA_INTEGRITY_AUDIT_PLAN_v1_0.md`, root `CLAUDE.md`: zero LIVE_DRIFT references to L2 as if active. HISTORICAL_OK references unchanged.
6. `VALIDATED_ASSET_REGISTRY_v1_0.json`: every L2_* asset has `status: ARCHIVED, archived_in: PHASE_14F`.
7. `CAPABILITY_MANIFEST.json` active block contains zero `02_ANALYTICAL_LAYER` paths.
8. `PHASE_14F_SURVEY.json` exists at `00_ARCHITECTURE/`.
9. `PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_REPORT_v1_0.md` exists at `00_ARCHITECTURE/` with all sections populated.
10. Commit landed on the working branch with a clean diff.
11. All applicable governance validators exit 0 (or 3 with known_residuals whitelist).

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Concurrent 14A session edits `CAPABILITY_MANIFEST.json` mid-stream | Medium | Medium | Stream E modifies only the `archived` block; if a manifest conflict arises at git push, rebase and retry. Halt only if conflict is in the `archived` block. |
| Survey misses an L2-as-live reference | Medium | Low | Survey scope is broad (all CURRENT/LIVING governance docs). 14G's lockdown verification re-scans; any missed item gets flagged then. |
| Empty `02_ANALYTICAL_LAYER/` directory contains a hidden file (`.DS_Store`, `.gitkeep`) | Medium | Low | Stream A step 2's `rmdir` will fail loudly. Executor inspects, removes the hidden file with rationale, retries. |
| `025_HOLISTIC_SYNTHESIS/CLAUDE.md` rewrite over-deletes load-bearing content | Low | Medium | Required content explicitly enumerated in Stream B. Diff review by executor before commit. |
| `GOVERNANCE_STACK_v1_0.md` L2 section is referenced by other docs (e.g., session log links to specific line numbers) | Low | Low | Tombstone preserves section heading; line-number drift acceptable for archived sections. |
| Validator failures because validators were written assuming L2 layer presence | Low | Medium | If a validator hard-fails on L2 absence, executor reports the validator name + exit code in close report and surfaces to native — does NOT silently bypass. |

## Concurrency declaration

This brief is **safe to run in parallel with 14A, 14B, 14C, 14D, 14E**. Surface boundaries:

- 14A owns: GCS provisioning + `CAPABILITY_MANIFEST.json` *active block* + `GCS_LAYOUT_v1_0.md`.
- 14B owns: build pipeline + Cloud Build/Cloud Run Jobs + `BUILD_PIPELINE_*.md` (NEW).
- 14C owns: L1 structured tables + `01_FACTS_LAYER/CLAUDE.md`.
- 14D owns: L2.5 structured tables + `025_HOLISTIC_SYNTHESIS/*.md` data files (NOT `CLAUDE.md`).
- 14E owns: L3 register tables + `035_DISCOVERY_LAYER/CLAUDE.md`.
- **14F (this brief) owns**: L2 directory disposition + governance markdown drift cleanup + registry L2 entries + manifest `archived` block.

The only shared file is `CAPABILITY_MANIFEST.json` (14A modifies active block, 14F modifies archived block — disjoint within the JSON). If a merge conflict arises in the manifest's archived block specifically, halt and surface; otherwise rebase and retry.

This brief MUST complete BEFORE 14G runs, because 14G's lockdown verification re-scans governance docs for L2-as-live drift and would fail if 14F hasn't run yet.

## Trigger phrase

"Read EXEC_BRIEF_PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_v1_0.md and execute it."

## Notes for the executor

- This is a **paperwork-heavy, code-light** brief. There is no production risk. Take time to scan thoroughly in Stream D — drift caught here is drift not caught in 14G.
- When in doubt about whether a reference is HISTORICAL_OK or LIVE_DRIFT: if the document's frontmatter status is `CLOSED` or `SUPERSEDED`, classify HISTORICAL_OK and leave alone. Only `CURRENT`/`LIVING` documents are in scope for amendment.
- Preserve the original tone of each governance doc when amending. Do not rewrite paragraphs that don't need rewriting.
- The `MARSYS_JIS_ARCHITECTURE_v1_0.md` (referenced in Stream C tombstone) is the post-2026-04-27 holistic architecture. Verify the path before quoting it.
- Phase 14.0's secondary findings list at `project_phase_14_0_complete.md` (memory) names exactly the two drift items in 025/CLAUDE.md and GOVERNANCE_STACK. This brief discharges both.
