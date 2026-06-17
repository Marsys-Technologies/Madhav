---
brief_id: EXEC_BRIEF_PHASE_14_0_ASSET_INVENTORY
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_14_0_ASSET_INVENTORY_v1_0.md and execute it."
phase: 14.0
phase_name: Asset Inventory + Validation + Cleanup (gates Phase 14A onward)
risk_classification: LOW (read-mostly inventory; only file moves to 99_ARCHIVE/, no deletions)
parallelizable_with: []
depends_on: [None — this is the gate before modernization begins]
output_artifact: 00_ARCHITECTURE/ASSET_INVENTORY_REPORT_v1_0.md
---

# EXEC_BRIEF — Phase 14.0 — Asset Inventory + Validation + Cleanup

## Mission

Before any data-layer modernization (Phase 14A onward), produce a complete, verified inventory of every data asset in the project with a per-file decision: **KEEP** (CURRENT load-bearing), **ARCHIVE** (SUPERSEDED or predecessor), or **TRANSFORM** (subject to modernization). The output is the single source of truth that all subsequent Phase 14 briefs will reference.

This brief exists because the user needs **certainty and authority** about what's in each layer before committing to structural changes. We cannot modernize storage if we don't know which files are load-bearing. We cannot archive safely without verifying nothing live depends on a file we're moving.

The cleanup itself happens in this same brief — files determined to be SUPERSEDED move to `99_ARCHIVE/` with a frontmatter note. Nothing is deleted. Nothing is renamed except for archival relocation.

## Pre-flight gate

1. Verify `99_ARCHIVE/` directory exists at project root. If missing, create it.
2. Verify `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` is present and parseable.
3. Verify Cloud SQL Auth Proxy is running (some validations require DB lookups).
4. Confirm git working tree is clean (`git status` returns no uncommitted changes). The cleanup creates a single commit at the end; pre-existing uncommitted work would mix with it.

If any fail, halt with a clear actionable message.

## Scope

**`may_touch`:**
- Read access to all of `01_FACTS_LAYER/`, `02_ANALYTICAL_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `035_DISCOVERY_LAYER/`, `06_LEARNING_LAYER/`, `00_ARCHITECTURE/`
- Read access to `platform/src/` and `platform/python-sidecar/` for cross-reference checks
- Write: `00_ARCHITECTURE/ASSET_INVENTORY_REPORT_v1_0.md` (the report, NEW)
- Write: `00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json` (machine-readable companion, NEW)
- File moves only: SUPERSEDED files relocated to `99_ARCHIVE/<original-layer-dir>/` preserving directory structure
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (update to reflect archived locations)
- `CLAUDE.md` and `01_FACTS_LAYER/CLAUDE.md` (update file lists to reflect cleaned state)

**`must_not_touch`:**
- File contents themselves (no edits to .md, .csv, .json content). Only relocations.
- Any file currently referenced by platform code (verified in Stream G). Halt if a SUPERSEDED-tagged file is still imported anywhere.
- Any DB schema or content
- Any `platform/` source code
- Any feature flag
- The CSV files (EPHEMERIS, ECLIPSES, RETROGRADES) — they're CURRENT regardless of how they're stored; modernization decides their fate, not this brief
- `06_LEARNING_LAYER/SCHEMAS/` — those are validators, leave untouched

## Sub-streams (8 total, sequential except where noted)

### Stream A — L1 (Facts Layer) audit

For every file in `01_FACTS_LAYER/` (including `SOURCES/` subdirectory):

1. Read the frontmatter (first 30 lines).
2. Extract: `version`, `status`, `superseded_by`, `expose_to_chat`, `layer`, `purpose` (one line).
3. Determine current state: **CURRENT** / **SUPERSEDED** / **GOVERNANCE** / **SOURCE_REFERENCE** / **DEAD_DATA** (CSV not query-able, not yet projected — flag for Phase 14C).

Expected files (from prior audit):
- `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — expected CURRENT
- `FORENSIC_DATA_v8_0_SUPPLEMENT.md` — expected SUPERSEDED (frontmatter says so)
- `LIFE_EVENT_LOG_v1_1.md` — expected SUPERSEDED (predecessor of v1_2)
- `LIFE_EVENT_LOG_v1_2.md` — expected CURRENT
- `SADE_SATI_CYCLES_ALL.md` — expected CURRENT
- `EXTERNAL_COMPUTATION_SPEC_v1_0.md` — expected SUPERSEDED (predecessor of v2_0)
- `EXTERNAL_COMPUTATION_SPEC_v2_0.md` — expected CURRENT (governance)
- `CGP_AUDIT_v1_0.md` — expected CURRENT (governance audit)
- `CLAUDE.md` — orientation, KEEP
- `EPHEMERIS_MONTHLY_1900_2100.csv` — expected DEAD_DATA (currently inert; Phase 14C activates)
- `ECLIPSES_1900_2100.csv` — expected DEAD_DATA
- `RETROGRADES_1900_2100.csv` — expected DEAD_DATA
- `SOURCES/EVENT_CHART_STATES_v1_0.md` — expected SOURCE_REFERENCE
- `SOURCES/JHORA_TRANSCRIPTION_v8_0_SOURCE.md` — expected SOURCE_REFERENCE

For each file, also answer the **coverage question**: what specific data does this file carry that nothing else does? This builds the coverage matrix. Report per-file in the L1 section.

**The user's specific question to answer in this stream:** does the combination of `FORENSIC v8.0` + `LIFE_EVENT_LOG_v1_2` + `SADE_SATI_CYCLES_ALL` cover all required L1 information, or are there gaps that require external computation? Answer with a per-fact-category present/absent table:

| Fact category | Where it lives | Coverage |
|---|---|---|
| Natal planetary positions | FORENSIC §2.2 | Complete |
| House cusps + KP system | FORENSIC §2.3 + §4.1 | Complete |
| Dashas | FORENSIC §5 | Complete |
| Subsidiary lagnas | FORENSIC §11 | Complete |
| Sahams | FORENSIC §12 (post-merge) | Complete |
| Navatara | FORENSIC §14 | Complete |
| Aspect tables | FORENSIC §16 | Complete |
| Life events | LIFE_EVENT_LOG_v1_2 | 36 events |
| Sade Sati phases | SADE_SATI_CYCLES_ALL | Complete |
| Daily ephemeris | EPHEMERIS CSV | Inert today; Phase 14C activates |
| Eclipses | ECLIPSES CSV | Inert today; Phase 14C activates |
| Retrogrades | RETROGRADES CSV | Inert today; Phase 14C activates |
| Transit-to-natal computations | EXTERNAL_COMPUTATION_SPEC v2 | Specified, computed externally on-demand |

**Stream A deliverable:** L1 inventory section in the report + per-file decision (KEEP/ARCHIVE/TRANSFORM).

### Stream B — L2 (Analytical Layer) audit

For every file in `02_ANALYTICAL_LAYER/` (expected: 6 markdown files per prior audit).

For each: read frontmatter, confirm SUPERSEDED status. The user already approved archiving L2 entirely. This stream's job is to verify that **no file is still referenced by platform code or current governance docs** before archiving.

Run a recursive grep on `platform/src/`, `platform/python-sidecar/`, and `00_ARCHITECTURE/*.md` for each L2 file's basename. If any reference is found, halt and surface to native — don't archive yet.

If no references: mark all L2 files as ARCHIVE candidates.

**Stream B deliverable:** L2 inventory section + reference-check evidence + archive list.

### Stream C — L2.5 (Holistic Synthesis) audit

For every file in `025_HOLISTIC_SYNTHESIS/`.

Expected files (from prior audit):
- `MSR_v3_0.md` — CURRENT
- `UCN_v4_0.md` — CURRENT
- `CDLM_v1_0.md` — likely SUPERSEDED (predecessor of v1_1)
- `CDLM_v1_1.md` — CURRENT
- `RM_v2_0.md` — CURRENT
- `CGM_v9_0.md` — CURRENT
- `RED_TEAM_L2_5_v1_0.md` — CURRENT (governance / red-team artifact)
- Possible predecessors of MSR, UCN, RM (e.g., `MSR_v2_0.md`, `UCN_v3_0.md`)

For each: status determination, coverage question (what data is here that nothing else has), reference check.

**Specific check:** for MSR (which has both .md AND `msr_signals` table), confirm the .md and the table are in sync. Spot-check 3 random signals: does the .md row match the DB row? If drift, flag it as a Phase 14E concern.

For CGM (which has .md AND `rag_graph_nodes` + `rag_graph_edges`): same drift check on a sample of nodes/edges.

**Stream C deliverable:** L2.5 inventory + coverage + drift-check results.

### Stream D — L3 (Discovery Layer) audit

For everything in `035_DISCOVERY_LAYER/`.

Expected per prior audit:
- `REGISTERS/PATTERN_REGISTER_v1_0.json` + `.md`
- `REGISTERS/RESONANCE_REGISTER_v1_0.json` + `.md`
- `REGISTERS/CONTRADICTION_REGISTER_v1_0.json` + `.md`
- `REGISTERS/CLUSTER_ATLAS_v1_0.json` + `.md`
- `REGISTERS/INDEX.json` (empty stub)
- `LEDGER/` (empty `.gitkeep`)
- `PROMPTS/claude/synthesis_v1_0.md` (B.8 deliverable, possibly here)

For each register: count entries, confirm matches expected counts (22 patterns, 12 resonances, 8 contradictions, 12 clusters), validate JSON schema. Reference check.

**Stream D deliverable:** L3 inventory + validity check on the four registers.

### Stream E — L5 (Predictions & Calibration) audit

For everything in `06_LEARNING_LAYER/`.

Expected per prior audit: 9 subdirectories (PREDICTION_LEDGER, LEDGER, PROMPT_REGISTRY, PROMPT_OPTIMIZATION, EMBEDDING_SPACE_ADAPTATION, GRAPH_EDGE_WEIGHT_LEARNING, SIGNAL_WEIGHT_CALIBRATION, OBSERVATIONS, PARAMETER_UPDATES, SCHEMAS).

For each subdir: enumerate files, classify as DATA / SCHEMA / GOVERNANCE. The `prediction_ledger.jsonl` is the only one that mirrors a Postgres table — verify it does NOT drift from the DB (count matches; spot-check 3 random entries).

**Stream E deliverable:** L5 inventory + DB-mirror drift check + per-subdir purpose summary.

### Stream F — Cross-reference: platform code dependencies

For every file marked KEEP, ARCHIVE, or TRANSFORM in Streams A-E, run:

```bash
grep -rn "<filename-without-extension>" platform/src/ platform/python-sidecar/ 00_ARCHITECTURE/*.md
```

Capture every hit. For each, classify:
- **HARD reference** (file path used in code import or fs.readFileSync) → file MUST stay where it is OR code must be updated atomically
- **SOFT reference** (mentioned in a comment, doc, or test fixture) → safe to archive, but note the reference for Phase 14F doc-update sweep
- **NO reference** → safe to archive

Any HARD reference on a file proposed for ARCHIVE → **halt with error**, do not archive that file. Surface to native.

**Stream F deliverable:** dependency matrix + final ARCHIVE list (intersection of "proposed-archive" AND "no-hard-reference").

### Stream G — Coverage matrix synthesis

Build the master coverage matrix in `00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json`:

```json
{
  "version": "1.0",
  "generated_at": "ISO timestamp",
  "layers": {
    "L1": {
      "purpose": "Atomic facts about the chart and reference timelines",
      "current_assets": [
        {
          "asset_id": "FORENSIC_v8_0",
          "path": "01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md",
          "format": "markdown",
          "data_categories": ["natal_positions", "house_cusps", "kp_cusps", "dashas", "lagnas", "sahams", "navatara", "aspects"],
          "current_storage": ["filesystem", "rag_chunks (chunked)"],
          "modernization_target": "+ chart_facts Postgres table",
          "modernization_phase": "14C"
        },
        ...
      ],
      "archived_assets": [...],
      "coverage_gaps": []
    },
    "L2": {...},
    "L2_5": {...},
    "L3": {...},
    "L4": {
      "status": "not_built",
      "rationale": "Single-native today; federated discovery is M3+ work"
    },
    "L5": {...}
  },
  "archive_plan": {
    "files_to_relocate": [
      {
        "from": "01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md",
        "to": "99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md",
        "reason": "SUPERSEDED — content merged into FORENSIC v8.0 per frontmatter line 5"
      },
      ...
    ]
  }
}
```

**Stream G deliverable:** the JSON registry + a human-readable companion in the report.

### Stream H — Cleanup execution + governance update

Execute the archive plan from Stream G:

1. Create `99_ARCHIVE/01_FACTS_LAYER/`, `99_ARCHIVE/025_HOLISTIC_SYNTHESIS/`, etc. as needed (preserve original directory structure).
2. `git mv` each file in the archive list to its `99_ARCHIVE/` counterpart. (Use `git mv` so file history is preserved.)
3. For each archived file, prepend a 3-line block to its frontmatter:
   ```
   archived_at: 2026-04-28
   archived_by: Phase_14_0_Asset_Inventory
   archived_reason: <reason from Stream G>
   ```
4. Update `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` so any entry pointing at an archived file now points at the new `99_ARCHIVE/` path AND has `status: ARCHIVED`.
5. Update `CLAUDE.md` items 7+ if they list any archived file.
6. Update `01_FACTS_LAYER/CLAUDE.md` to reflect the cleaned file list.
7. Run `manifest:build` if the manifest builder script exists; verify post-cleanup fingerprint.
8. Single git commit: `chore(14.0): asset inventory + archive cleanup per ASSET_INVENTORY_REPORT_v1_0`

**Stream H deliverable:** git commit hash + diff summary in the report.

## Critical constraints

- **No deletions, ever.** Files only move to `99_ARCHIVE/`. The user's directive is explicit.
- **No content edits.** This brief does not modify any file's body. Only frontmatter `archived_*` lines are added on archived files (3 lines).
- **Hard-reference safety.** If Stream F finds a hard code reference to any proposed-archive file, halt. Don't archive that file. Surface to native — they'll either remove the code reference first or leave the file in place.
- **Single commit at end.** All file moves + governance updates land as one commit, atomically. If anything fails mid-stream, the brief halts and surfaces what's done vs not.
- **Authority of the report.** `00_ARCHITECTURE/ASSET_INVENTORY_REPORT_v1_0.md` becomes load-bearing. All Phase 14A-G briefs cite it as the canonical asset list.
- **Coverage-gap honesty.** If Stream A finds a fact category that's marked as needing external computation (per `EXTERNAL_COMPUTATION_SPEC_v2_0`), document it. The user needs to know what's NOT in the corpus, not just what IS.

## Done criteria

1. Streams A-E: per-layer inventory completed; every file has a status decision.
2. Stream F: dependency matrix built; no hard references on archive list.
3. Stream G: `VALIDATED_ASSET_REGISTRY_v1_0.json` exists, schema-valid.
4. Stream H: git commit lands; archived files moved; manifest updated; CLAUDE.md docs reflect cleaned state.
5. Report at `00_ARCHITECTURE/ASSET_INVENTORY_REPORT_v1_0.md` exists with sections per layer + executive summary at top.
6. Native acceptance: native reads the report, confirms every archive decision is correct, signs off via a chat reply ("Phase 14.0 accepted — proceed to 14A").
7. Phase 14A through 14G briefs can now reference the validated asset registry as their canonical input.

## Risk classification: LOW

This brief moves files but doesn't modify content. Mitigations:
- Stream F's hard-reference check prevents archiving anything still in active use
- `git mv` preserves history
- Single commit makes rollback trivial (`git revert HEAD`) if anything is wrong
- Report-first, execute-after pattern: native reviews the proposed archive list before Stream H runs (optional pause-point if native wants it)

## Optional pause point

After Stream G (the proposed archive plan written to the registry) and before Stream H (the execute step), the brief CAN halt and ask native: "Here is the proposed archive list. Confirm to proceed with relocations." Native says yes → Stream H runs. Native says no → Stream H aborts; native edits the registry; brief is re-triggered with the corrected list.

This optional pause adds safety. Recommend native asks for it.

## Output artifacts

1. `00_ARCHITECTURE/ASSET_INVENTORY_REPORT_v1_0.md` — human-readable per-layer inventory + decisions + coverage matrix
2. `00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json` — machine-readable, used by all Phase 14A-G briefs
3. Updated `CAPABILITY_MANIFEST.json` reflecting archived locations
4. Updated `CLAUDE.md` reflecting cleaned state
5. Files relocated to `99_ARCHIVE/` with archive frontmatter
6. Single git commit

## How native triggers

In a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension):

> Read EXEC_BRIEF_PHASE_14_0_ASSET_INVENTORY_v1_0.md and execute it.

Recommend native explicitly asks for the optional pause point at Stream G/H boundary so they review the proposed archive list before relocations execute.

After Phase 14.0 closes successfully, the modernization plan (Phase 14A through 14G) becomes triggerable. Each subsequent brief reads `VALIDATED_ASSET_REGISTRY_v1_0.json` to know exactly which assets it operates on.

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when all 7 done-criteria pass and native accepts
