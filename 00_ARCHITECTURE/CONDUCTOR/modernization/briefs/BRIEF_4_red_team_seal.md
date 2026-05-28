---
unit: 4.red_team_seal
wave: 4
title: Final red-team + macro-phase seal + retire program-tracker + close-out
stream: A
worktree: ../MadhavStreamA
blockedBy: [4.refactor_pipeline_shim, 4.build_trigger, 4.memorystore_caching, 4.edge_and_infra_hygiene, 4.observability, 4.learning_loop]
on_red: halt_queue   # this IS the seal — any class-1 finding stops + surfaces
---

## Context (self-contained)
Last unit. Per IS.8(b) cadence, a macro-phase close requires a red-team pass. With every other Wave-4 unit
green, run the adversarial review, dispose of remaining open decisions, retire the ephemeral program tracker,
and seal the program with a canonical close-out artifact.

## Scope
- **Adversarial red-team pass** (class-1 findings = anything that could ship a wrong answer or leak data):
  authz coverage (owner / grant / super_admin), the constant-offset ayanamsha invariant, B.11 forced-first on
  every gateway path, no-tier-path-reachable, no `NATIVE_CHART_ID` literal, no LEL in build/churn, prediction-
  log determinism, kill-switch wiring (budget + error-rate), MCP IAM (no public reach), secret hygiene.
- **Open-decisions disposition:** depth-selector default = planner-auto-by-query-class (lock); Anthropic-cost
  call (record decision); macro-phase number assigned (M-number); the layer-vocabulary canonicalization
  status; the §9 open decisions all marked RESOLVED or DEFERRED with a note.
- **Retire the program tracker (`0t` lifecycle: ephemeral):** `rm -rf tools/program-tracker/`, delete the
  Cloud Run service (`gcloud run services delete amjis-tracker` if deployed); confirm no app code imports it.
- **Macro-phase seal artifact:** `00_ARCHITECTURE/M{n}_PLATFORM_MODERNIZATION_CLOSE_v1_0.md` summarizing every
  wave, every gate, every unit, every cherry-pick to main, the open-decisions disposition, the red-team
  findings disposition, and the deferred operator items.
- **Version bumps:** CLAUDE.md + affected canonical artifacts version-bumped per CLAUDE.md §L; CURRENT_STATE
  updated to reflect the closed macro-phase.

## Acceptance criteria (all automated)
1. Red-team report: 0 class-1 findings; class-2/3 findings logged with disposition.
2. `tools/program-tracker/` removed; `grep -rn program-tracker platform platform-mcp` returns 0 imports.
3. Seal artifact committed; CLAUDE.md + CURRENT_STATE bumped + reconciled.
4. All 8 hard gates remain green; full test suite green on main.

## must_not_touch
`chart_facts`/`l25_*`, `platform/src/lib/synthesis/panel/**`, the engine.

## Commit cadence / rollback
Commits: (1) red-team report + class-2/3 disposition, (2) program-tracker removal + deploy cleanup, (3) seal
artifact + version bumps. Rollback = revert (but at this point the program is by definition complete; a
rollback would re-open the macro-phase). on_red=halt_queue: a class-1 finding requires native review before sealing.
