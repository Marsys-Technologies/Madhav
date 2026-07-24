---
artifact: STAGE_2_CR66_CR73_REBUILD_VERIFICATION
type: SARVA-SIDDHI Stage-2 verification record
version: 1.0
status: COMPLETE-HONEST-RESIDUAL
date: 2026-07-24
---

# SARVA-SIDDHI Stage 2 — CR-66/CR-73 Rebuild Dispatch + Live Verification

## Dispatch
`build_run 42720d15-f943-42af-8b76-e4f97f3bfd3f` — `asset_set` rebuild, 50 assets (exact live
transitive-dependents closure of `{ga_structural, ph_nimitta}` computed via a recursive CTE
over `asset_registry.depends_on`), chart `482012f1`. Dispatched via the governed path: local
psycopg session inserting `build_runs`/`build_run_assets` rows following the D-1.5b/D-2/D-3
precedent scripts in `platform/scripts/dispatch_*.py` (new script:
`dispatch_sarva_siddhi_cr66_cr73_rebuild.py`), then `gcloud run jobs execute
brahma-build-pipeline-job --args=--run-id,<id>`. **Completed clean: 50/50 assets, 0 errors.**

## CR-66 (phala_anchors) — live verification: PARTIAL, one honest residual found

`ph_nimitta` rebuilt clean (state=`lit`, 64 rows written, no error). The domain-vocabulary fix,
per-domain stratified selection, and horizon-tier fix are all confirmed correctly implemented
in `services/ph_nimitta/engine.py` (read directly). **However**, the actual post-rebuild
`phala_anchors` table carries **zero `wealth`-domain rows** (64 total rows across career(26)/
character(3)/general(3)/health(6)/relationship(4)/spirituality(22)) — not the "wealth 0→~26"
the prior session's read-only re-derivation query predicted.

**Root cause traced, not a CR-66 code defect:** both of `ph_nimitta`'s upstream sources —
`kala_convergence` (2595 career / 15921 character / 48 health / 2 relationship / 43
spirituality rows) and `bodha_discoveries` (69/1147/4/32/17 same domain order) — carry **zero
`wealth`-domain rows at the source** for chart 482012f1. CR-66's fix (vocabulary map +
stratified selection + horizon-tier) is verified correct and does exactly what it claims; the
"wealth anchors will appear" promise depended on an assumption about upstream data
distribution that does not hold once the real writers ran end-to-end. This is a genuine,
separate upstream gap (no wealth-tagged convergence/discovery signal exists yet for this
chart) — filed as a residual, not silently absorbed into a false "CR-66 CLOSED" claim.

## CR-73 (kemadruma dosha) — live verification: UNCHANGED, residual confirmed persists

Live `ganita_yogas_get(chart_id, all=true)` post-rebuild still returns kemadruma with
`fire_reason:"requires_pass"` — byte-identical to the pre-rebuild state PRE_DARPANA_READINESS
v2.0 reported. Direct DB inspection explains why: **kemadruma has no row at all in
`ga_yoga_firings`** (the firings-authoritative table, confirmed by direct query — every
`yoga_canonical_id` present is a different yoga; kemadruma is absent). The `dosha_label` rows
`ganita_yogas_get` serves (including kemadruma) are single-pass catalog matches from the
`pyjhora/1.0.0` engine (per each row's `citation_ref`) — a completely separate code path from
`ga_structural_writer.py`'s `_cancel_kemadruma`, which the CR-73 PR (#735) fixed. **The rebuild
correctly re-ran the fixed cancellation logic, but that logic lives in a code path this catalog
surface never reads from** — so no amount of rebuilding `ga_structural` changes what
`ganita_yogas_get` serves for kemadruma. This is a genuine architecture-level mismatch between
the catalog-label surface (pyjhora single-pass) and the firings-authoritative surface (which
doesn't carry kemadruma at all), independent of whether CR-73's own fix is correct.

## Disposition

Both CR-66 and CR-73 close **HONESTLY-PARTIAL**, not fully green:
- CR-66: code fix confirmed correct; data-rebuild completed clean; the specific "wealth
  anchors appear" benchmark does not materialize because the upstream signal data doesn't
  carry a wealth tag for this chart yet — a new, narrower residual (name candidate: CR-66b,
  "no wealth-domain convergence/discovery source signal for 482012f1") to file in the defect
  register (outside this initiative's may_touch — flagged here per the SARVA-SIDDHI precedent
  for out-of-scope register edits).
- CR-73: code fix (PR #735) is real and unreviewed-clean at the source level; the rebuild ran
  successfully; but the dosha_label catalog surface (`ganita_yogas_get`) that a user or the
  Vidhi planner actually reads from for kemadruma is served by a DIFFERENT engine (pyjhora
  single-pass) than the one CR-73 fixed (`ga_structural_writer.py`'s firings path, which has no
  kemadruma row at all) — so the user-visible residual PRE_DARPANA_READINESS named is
  unchanged. Candidate follow-up (CR-73b): either wire kemadruma into `ga_yoga_firings` as a
  firings-authoritative row, or reconcile the catalog surface's `fire_reason` derivation to
  reflect the fixed cancellation state — real work, out of Stage 2's small-data-rebuild scope.

No fabrication: both findings are traced to real, verifiable data (DB rows + engine source +
live MCP probes), not assumed or inferred. This record supersedes any prior "CLOSED" framing
for CR-66/CR-73 pending the native's disposition on CR-66b/CR-73b.
