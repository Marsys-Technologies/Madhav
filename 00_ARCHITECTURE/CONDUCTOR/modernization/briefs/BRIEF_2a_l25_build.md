---
unit: 2a
wave: 2
title: Deterministic L1→L2.5 build into chart_id + ayanamsha-keyed stores (sets G4_no_native_lit)
stream: C
worktree: ../MadhavStreamC
blockedBy: [G1_jh_parity]
sets_gate: G4_no_native_lit
on_red: halt_queue   # this is the data spine — stop and surface, don't churn
file_fence: "touches platform/src/lib/retrieve/* (NATIVE_CHART_ID removal) — the tool-layer units (3.gateway, 3.dejudge, 3.tool_asset_recon) MUST run after 2a, never concurrent"
---

## Context (self-contained)
The engine (G1, jh_true_chitra) now reproduces JH. Use it to regenerate the data layer as pure deterministic
facts (MASTER_PLAN §12 + DATA_LAYER_REBUILD spec): structural fact layer (T1) + the L2.5 assets, keyed by
`(chart_id, ayanamsha_id)`. Strangler/parallel-build — never destructive in place.

## Scope
- **Build** (per chart_id, per ayanamsha role): T1 structural facts → `chart_facts`; **MSR** never-drop signal
  enumeration with the **decomposed coefficient as 3 DB columns** `deterministic_strength`,
  `verification_certainty`, `computed_salience` (Gemini keeper — structural, no fused score); deterministic
  **CDLM** shared-factor graph; **CGM** structural graph; **RM** remedy lookup; **UCN** computed-signature
  digest. Ayanamsha-dependent assets carry `ayanamsha_id` (canonical=jh_true_chitra for Parashari/MSR; kp where KP).
- **Cutover discipline:** build into chart_id-keyed STAGING tables → validate (invariants + never-drop counts
  vs `data_source_expected` + pyswisseph cross-check + native vs engine) → atomic staging→live swap (Phase 4C
  pattern, build_id) → **freeze the old corpus** as `provenance: model_attributed` archive (do NOT delete).
- **Remove `NATIVE_CHART_ID` / `DEFAULT_CHART_ID` literals** from `platform/src/lib/retrieve/*` (thread
  `chart_id` as required) → this is what sets **G4**.

## Acceptance criteria (all automated)
1. `chart_facts` + `l25_*` rebuilt, keyed `(chart_id, ayanamsha_id)`; MSR coefficient = 3 distinct columns.
2. Never-drop: per-category row counts ≥ `data_source_expected`; constant-offset invariant holds across ayanamsha sets.
3. **G4 gate:** `platform/scripts/governance/assert_no_native_literal.sh` exits 0 (no NATIVE_CHART_ID/DEFAULT_CHART_ID literal in prod paths).
4. Native chart L2.5 validates against engine output; old corpus archived (present, frozen), not deleted.
5. Determinism: same inputs + engine_version ⇒ byte-identical JSONL across two runs.

## must_not_touch
`platform/src/lib/pipelines/**`, `platform/src/app/api/chat/consume/route.ts`, `platform-mcp/src/**`,
`platform/src/app/**` (frontend), `platform/src/lib/disclosure/**`.

## Commit cadence / rollback
Commits per asset (T1 → MSR → CDLM → CGM → RM → UCN → loader/swap → NATIVE-removal). Rollback = revert +
the frozen old corpus is the data fallback (never overwritten). on_red=halt_queue.
