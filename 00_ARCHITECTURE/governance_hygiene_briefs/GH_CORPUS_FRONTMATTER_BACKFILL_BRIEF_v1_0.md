---
artifact: GH_CORPUS_FRONTMATTER_BACKFILL_BRIEF_v1_0.md
canonical_id: GH_CORPUS_FRONTMATTER_BACKFILL_BRIEF
version: 1.0
status: ACTIVE_HALTED
authored_by: Cowork (Claude Opus 4.7) 2026-05-21
authored_for_session: GH-CORPUS-FRONTMATTER-BACKFILL
purpose: >
  Backfill missing schema-required frontmatter (`artifact:`, `version:`,
  per-class fields) across the corpus to clear the 74 MEDIUM
  `frontmatter_field_missing[architecture_governance/artifact]` + 18 MEDIUM
  `frontmatter_field_missing[l3_domain_reports/artifact]` + 15 MEDIUM
  `version_missing_in_canonical_artifacts` + 9 MEDIUM
  `frontmatter_missing[architecture_governance]` + 1 MEDIUM each
  for `l1_facts` and `l2_5_cgm` schema_validator violations, AND the 3
  HIGH `learning_layer_*` violations (stub banner / population gate).
  Largest of the three governance-hygiene follow-ups from the
  PR-111-REMEDIATION SESSION_HALT.md. Run LAST — after drift_detector and
  session_log_structure briefs have shipped.
launch_instructions: >
  Copy to /Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF.md when ready.
  This brief touches `must_not_touch` paths from PR #112's brief
  (01_FACTS_LAYER, 025_HOLISTIC_SYNTHESIS, 06_LEARNING_LAYER) — that's
  expected and necessary; the may_touch declared HERE is what's authoritative
  for THIS session.
active_phase: Governance Hygiene (post-PR-111 follow-up; concurrent workstream)
may_touch:
  - 00_ARCHITECTURE/**.md
  - 03_DOMAIN_REPORTS/**.md
  - 01_FACTS_LAYER/**.md
  - 025_HOLISTIC_SYNTHESIS/**.md
  - 06_LEARNING_LAYER/**.md
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
  - 00_ARCHITECTURE/governance_hygiene_briefs/**
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  - 00_ARCHITECTURE/SESSION_LOG.md
  - .gemini/project_state.md
  - .geminirules
  - CLAUDECODE_BRIEF.md
  - CLAUDE.md
must_not_touch:
  - platform/**
  - 02_*/**  # legacy L2 Analytical Layer; archived Phase 14F 2026-04-28
  - 035_DISCOVERY_LAYER/**
  - 04_REMEDIAL_CODEX/**
  - 05_TEMPORAL_ENGINES/**
  - 08_CLASSICAL_CROSS_REFERENCE/**
  - 09_MULTI_SCHOOL_TRIANGULATION/**
  - 99_ARCHIVE/**
  - 00_ARCHITECTURE/PHASE_*.md
  - 00_ARCHITECTURE/MACRO_PLAN_*.md
  - 00_ARCHITECTURE/PROJECT_ARCHITECTURE_*.md
  - 00_ARCHITECTURE/CONDUCTOR/**
acceptance_criteria:
  - AC.1: Diagnose. Run schema_validator.py and group every `frontmatter_*` violation by (file, rule). Write to 00_ARCHITECTURE/governance_hygiene_briefs/corpus_frontmatter/_DIAGNOSIS.md. Total expected (per SESSION_HALT.md table) — 74 + 18 + 15 + 9 + 1 + 1 = 118 MEDIUM, plus 3 HIGH `learning_layer_*`. Diagnosis confirms or revises these numbers.
  - AC.2: Authority check. For each affected schema class (`architecture_governance`, `l1_facts`, `l2_5_cgm`, `l3_domain_reports`, `learning_layer_stub`), read its definition in `platform/scripts/governance/schemas/artifact_schemas.yaml` (read-only — do NOT modify). Confirm the required-fields list and the exact frontmatter-key names the validator expects.
  - AC.3: Backfill. For every flagged file, add the missing frontmatter fields. Defaults — `artifact:` = the file's basename without extension; `version:` = read from existing changelog if present, else `1.0`; `status:` = inferred from filename pattern (`*_v*_*.md` → CURRENT; `*SUPERSEDED*` → SUPERSEDED; etc.) or set to `CURRENT` with a one-line changelog noting the backfill. Do NOT invent canonical_id values — only fill `artifact:` and `version:` and `status:` where missing; if a file legitimately doesn't need a frontmatter block (e.g. README.md), update the schema class definition's `applies_to_glob` to exclude it (this counts as a validator-data edit, not a script edit, and is acceptable). Log such exclusions in _DIAGNOSIS.md.
  - AC.4: HIGH `learning_layer_*` fix. The 3 violations are in `06_LEARNING_LAYER/**`. Per ONGOING_HYGIENE_POLICIES §G — (a) `learning_layer_stub_banner_missing` HIGH = stub README missing the STATUS banner (the required class is `learning_layer_stub` per LEARNING_LAYER_SCAFFOLD_DECISION §5.7); (b) `learning_layer_population_gate_violation` HIGH = STATUS: ACTIVE without `activation_lel_entry:` or `activation_ppl_entry:` field. Diagnosis identifies which of the 3 are class (a) vs class (b). Fix class (a) by adding the STATUS banner; for class (b), if the README is in fact populated (events exist), add the activation pointer; if it's NOT populated, demote STATUS from ACTIVE to one of the legitimate non-active states (DRAFT, SCAFFOLDED, etc — per the schema class definition).
  - AC.5: 15 MEDIUM `version_missing_in_canonical_artifacts` — for each entry in CANONICAL_ARTIFACTS_v1_0.md missing a version field, look up the file's actual version from its frontmatter and add it. CANONICAL_ARTIFACTS is SUPERSEDED but still readable; per CLAUDE.md §C item 2 the manifest is now authoritative — the agent decides whether to (a) fix CANONICAL_ARTIFACTS (since it's a known-residual archived doc) OR (b) update CAPABILITY_MANIFEST.json mirror entries instead. Default: fix CANONICAL_ARTIFACTS in place since it's the file the validator reads.
  - AC.6: Re-run schema_validator. Frontmatter-class MEDIUM counts → 0. `learning_layer_*` HIGH count → 0. `session_log_entry_*` count unchanged (separate brief). Total exit code drops from current baseline to ≤ 2 or 3 depending on remaining LOW counts.
  - AC.7: No regression — drift_detector, mirror_enforcer exit codes unchanged or improved.
  - AC.8: Governance trail. CURRENT_STATE next version (read §3 to pick the correct number). SESSION_LOG entry. CLAUDE.md no-op. .gemini mirror.
  - AC.9: Work on branch `governance-hygiene/corpus-frontmatter` in worktree /Users/Dev/Vibe-Coding/Apps/MadhavGH3/. PR opened against main. PR body itemises AC statuses + counts of MEDIUM violations resolved per schema class.
  - AC.10: Brief `status:` flipped to COMPLETE. Final summary.
hard_constraints:
  - Single-purpose. Do NOT bundle drift_detector fix or SESSION_LOG structural fix.
  - Do NOT modify the validator script.
  - Do NOT modify the schema definitions in `artifact_schemas.yaml` EXCEPT to refine `applies_to_glob` patterns when AC.3 calls for it AND only with an inline comment justifying the exclusion.
  - Do NOT bulk-rewrite file bodies. Frontmatter additions only.
  - On `01_FACTS_LAYER/**` (FORENSIC + LEL) — the corpus L1 — be extra conservative; if any required field's value isn't obvious from the file, halt rather than guess. These files are quasi-canonical scripture for the project; wrong frontmatter is worse than missing frontmatter.
  - Do NOT merge the PR.
  - Work in a worktree.
session_open_obligations:
  - Read CLAUDE.md, CURRENT_STATE §2, this brief.
  - Read SESSION_HALT.md from chat-v2/pr-111-remediation branch.
  - Read ONGOING_HYGIENE_POLICIES_v1_0.md §G (learning_layer_stub validator class) and §K (residual-finding disposition).
  - Read LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md §5.7 (learning_layer_stub class semantics).
  - Read platform/scripts/governance/schemas/artifact_schemas.yaml (read-only).
  - Emit SESSION_OPEN handshake.
session_close_obligations:
  - Validators meet AC.6 + AC.7 thresholds.
  - SESSION_LOG entry per CORRECT structure (assuming GH_SESSION_LOG_STRUCTURE shipped first).
  - Update CURRENT_STATE.
  - Mirror to .gemini.
  - Flip status to COMPLETE.
  - PR + summary.
---

# Governance Hygiene: Corpus Frontmatter Backfill Brief

## §1 — Context

118 MEDIUM frontmatter violations + 3 HIGH learning_layer violations across the corpus. Sources per SESSION_HALT.md:

| Class | Count | Severity | Path |
|---|---|---|---|
| `frontmatter_field_missing[architecture_governance/artifact]` | 74 | MEDIUM | `00_ARCHITECTURE/*.md` (mixed) |
| `frontmatter_field_missing[l3_domain_reports/artifact]` | 13+5 | MEDIUM | `03_DOMAIN_REPORTS/**` |
| `version_missing_in_canonical_artifacts` | 15 | MEDIUM | `CANONICAL_ARTIFACTS_v1_0.md` |
| `frontmatter_missing[architecture_governance]` | 9 | MEDIUM | `00_ARCHITECTURE/*.md` |
| `frontmatter_field_missing[l1_facts/artifact]` | 1+1 | MEDIUM | `01_FACTS_LAYER/**` |
| `frontmatter_field_missing[l2_5_cgm/artifact]` | 1 | MEDIUM | `025_HOLISTIC_SYNTHESIS/**` |
| `learning_layer_*` (banner + population gate) | 3 | HIGH | `06_LEARNING_LAYER/**` |

This is the largest of the three hygiene briefs. Run AFTER drift_detector fix (so the validator suite is in a clean state) and AFTER session_log_structure (so this brief's own SESSION_LOG append is on a correct structural footing).

## §2 — Default backfill template

For each `architecture_governance` class file missing the `artifact:` field, prepend frontmatter shaped like:

```yaml
---
artifact: <basename-without-extension>
version: <from changelog, else 1.0>
status: <CURRENT | SUPERSEDED | DRAFT — inferred from filename + history>
authored_by: backfill GH-CORPUS-FRONTMATTER-BACKFILL 2026-05-2X
backfill_note: >
  Frontmatter backfilled by the governance hygiene pass following PR #111
  SESSION_HALT.md AC.7. Existing file body untouched.
---
```

Adjust per schema class — `l1_facts` may need a `derived_from:` field, `l3_domain_reports` may need `domain:` + `report_id:`. Read `artifact_schemas.yaml` to confirm.

## §3 — Order of operations within the session

1. _DIAGNOSIS.md — group violations.
2. `00_ARCHITECTURE/*.md` — 83 MEDIUM (74 + 9). Largest cluster; do this first since it's lowest risk.
3. `03_DOMAIN_REPORTS/**` — 18 MEDIUM. Medium risk.
4. CANONICAL_ARTIFACTS_v1_0.md — 15 MEDIUM. Mechanical version-field add.
5. `06_LEARNING_LAYER/**` — 3 HIGH. Highest care; per AC.4 split (a) vs (b) before acting.
6. `01_FACTS_LAYER/**` + `025_HOLISTIC_SYNTHESIS/**` — 3 MEDIUM. Highest care; halt rather than guess.

After each cluster, re-run schema_validator and confirm that cluster's count is 0 before moving to the next.

## §4 — Step-by-step (compressed — same shape as the other GH briefs)

1. Worktree at /Users/Dev/Vibe-Coding/Apps/MadhavGH3, branch governance-hygiene/corpus-frontmatter.
2. SESSION_OPEN handshake.
3. AC.1 diagnose.
4. AC.2 authority check.
5. AC.3 backfill clusters 2 → 5 → 6 → others per §3.
6. AC.4 + AC.5 specialized clusters (learning_layer + CANONICAL_ARTIFACTS versions).
7. AC.6 + AC.7 validator re-run + regression check.
8. AC.8 governance trail.
9. AC.9 + AC.10 PR + final summary.

## §5 — Halt conditions

- Any `01_FACTS_LAYER/**` or `025_HOLISTIC_SYNTHESIS/**` file requires a frontmatter field whose value isn't obvious from the file itself → halt with diagnosis; native fills in.
- Schema class definitions appear incorrect (e.g., requiring fields the corpus has never used) → halt; revising the schema is a different brief.
- A `learning_layer_*` violation requires demoting STATUS in a way that conflicts with what the file body claims about its own activation → halt; native arbitrates.
- Cluster N's fix regresses cluster N-1 (validator count for an already-fixed rule rises) → halt and revert.

## §6 — Expected scale

Estimate: 100+ files touched, mostly frontmatter-block additions of 5–10 lines each. PR will be large but reviewable since every diff is just a frontmatter prepend. Reviewer should diff with `git diff --stat` first to confirm scope, then spot-check a few clusters.
