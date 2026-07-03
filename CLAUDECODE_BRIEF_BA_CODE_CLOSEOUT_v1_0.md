---
canonical_id: CLAUDECODE_BRIEF_BA_CODE_CLOSEOUT
version: 1.0
status: IN-PROGRESS
created: 2026-07-04
author: Cowork + Claude Code conductor
program: BEYOND_ACHARYA endgame (BA_ENDGAME_ACTIVITY_PLAN) — Activity 1.5: deploy all remaining phase code
  so the Nirmāṇa cockpit audit (Activity 2, Cowork/Chrome MCP) sees the COMPLETE instrument, then the single
  cascade rebuild (Activity 3, native cockpit), then E2E (Activity 4).
prerequisite_met: PR #408 merged to origin/main at 32647340; git pull done; local main = origin/main.
next_migration_number: 391
---

# CLAUDECODE_BRIEF — BA CODE CLOSE-OUT (Activity 1.5)

## §0 — WHAT THIS IS (and is NOT)

Deploy the code, migrations, registry rows, DAG edges, and serving logic for EVERY remaining phase —
**P3B → P4 → P5A → P5B → P6 → P7A ≥ P7B** — WITHOUT building or regenerating any chart data. Every phase's
substance is already frozen in its own brief; this charter runs their **code steps only** and DEFERS every
data build to the ONE post-audit cascade rebuild (Activity 3).

**This charter does NOT:** trigger any cockpit build/rebuild/regeneration; touch chart data; re-tune priors
(frozen at P2T, priors_version=1.0); alter the ratified salience formula beyond R1; re-scope any frozen brief's
substance.

## §1 — GLOBAL SCOPING OVERRIDE

For each phase, execute all steps EXCEPT the cockpit build/regeneration step:
- **DO:** writers (@register WriterBase subclasses, FROZEN contract §N.2), migrations (CREATE TABLE +
  asset_registry INSERT with correct layer/sort_order/scope/has_writer=true/chart-scoped count_sql $1/
  target_floor placeholder + DAG depends_on), retrieval/MCP serving code, formula unification.
- **DO NOT:** run any writer against a chart; trigger cockpit Build/Rebuild; regenerate L2–L5 data.
  Steps marked "Regenerate ONCE / rebuild / build via cockpit" are DEFERRED-TO-CASCADE.
- **Migration numbering:** next-free = 391; scan BOTH platform/migrations AND platform/supabase/migrations
  before each new migration.

## §2 — EXECUTION ORDER

1. P3B — bo_laksana v2 formula, bo_pratijna NEW, bo_sangati triangulation EXT, typed graph edges, L0 classical bridge
2. P4 — verdict object in mi_darshana, judgment terms, synth_* MCP tools, PD-5 UI retirement
3. P5A — ka_yojaka EXT, ka_avadhi NEW, ka_taranga NEW, conflation fixes
4. P5B — ph_nimitta v2 engine, ph_muhurta EXT, prashna path (JL-009 gate at data stage)
5. P6 — mi_pramana v2, mi_pariksha v2, mi_gunanaka shrinkage, LEL intake, weight unification
6. P7A ≥ P7B — Nadi/AV/avastha writers + portal learning loops (parallelizable)

## §3 — GATES THAT APPLY NOW vs DEFERRED

- **Apply now:** platform + platform-mcp builds exit 0; typecheck green; migrations present in repo;
  asset_registry rows with correct count_sql; DAG edges; merged to main; all three deploy surfaces on new HEAD.
- **DEFERRED to cascade rebuild:** degeneracy sweeps, G10-STORED, constituent-resolve ≥99%,
  classical-bridge ≥60%, sanity row counts, promise-register smoke, anchor probability-range, golden-eval RUN,
  retrodiction skill table.

## §4 — BUILD-PIPELINE JOB IMAGE

After all phase code merged to main, rebuild + push brahma-build-pipeline-job to close-out SHA.
Must confirm: `gcloud run jobs describe brahma-build-pipeline-job` image maps to close-out HEAD.

## §5 — EXIT ARTIFACT

Emit BA_CODE_CLOSEOUT_REPORT_v1_0.md containing:
- Per-phase: PRs/SHAs, migrations consumed, Ring-1 + deploy-truth evidence, DEFERRED gate list
- ASSET-REGISTRY DELTA MANIFEST: every NEW/CHANGED asset (asset_id, layer, sort_order, names, scope, has_writer, count_sql, depends_on[])
- Final close-out SHA; all three deploy surfaces confirmed; JOB image digest
- Explicit statement: zero chart data built; zero cockpit rebuild triggered; priors_version=1.0 unchanged
- GO for Activity 2 (Nirmāṇa build-tracker audit)

## §6 — ANTI-GOALS / TRAPS

No cockpit build or data regeneration (Activity 3, native-executed). No priors re-tune. No salience
formula change beyond ratified R1. No frozen-brief substance changes. Surgical migrations only.

## §7 — PROGRESS LEDGER

| Phase | Status | Branch/PR | Migrations | Notes |
|-------|--------|-----------|------------|-------|
| P3B | PENDING | — | 391, 392 | bo_pratijna + bodha_triangulation |
| P4 | PENDING | — | — | verdict + synth tools + UI |
| P5A | PENDING | — | 393, 394 | kala_avadhi + kala_taranga |
| P5B | PENDING | — | — | ph_nimitta v2 engine |
| P6 | PENDING | — | — | mimamsa engine v2 |
| P7A | PENDING | — | — | Nadi + AV + avastha |
| P7B | PENDING | — | — | portal learning loops |
| JOB rebuild | PENDING | — | — | pipeline image |

*Set status: COMPLETE when all §5 exit criteria met.*
