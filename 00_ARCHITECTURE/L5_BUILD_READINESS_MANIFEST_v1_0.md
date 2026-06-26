---
artifact: L5_BUILD_READINESS_MANIFEST_v1_0.md
canonical_id: L5_BUILD_READINESS_MANIFEST
version: 1.0
status: CURRENT — the COMPLETE executable checklist of everything that must exist for press-Build to generate all L5 data
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes_role_of: L5_BUILD_READINESS_AUDIT_v1_0.md (that = the diagnosis; THIS = the full executable build-out plan)
role: >
  The exhaustive, itemized readiness manifest. Every single thing that must be built/created/wired so that
  pressing Build on L5 Mīmāṃsā in the Nirmāṇa tracker generates the ENTIRE dataset without interruption.
  Grounded in the live code (WriterBase frozen contract, asset_runner DAG resolution, migrate.ts, the
  cockpit runs API, the empty L5 retrieval scaffold). Organized as workstreams W1–W9, each a checklist of
  concrete, verifiable line items. When every box is ticked and the W9 pre-flight passes, press-Build is
  guaranteed to run clean. Nothing is assumed "already there" — if it must exist, it is listed.
verification_basis:
  - writers/__init__.py (WriterBase/ContextSpec/WriterResult frozen contract; pkgutil discover_all hard-fail; @register)
  - asset_runner.py (registry-driven recursive DAG closure; get_writer; count_sql/scope/throughput)
  - asset_registry_seed.ts (live registry state — 6 mi_* rows, the dependency bug, asset_id≠table)
  - migrate.ts (reads platform/migrations/ + platform/supabase/migrations/; push-to-main auto-applies)
  - L5_mimamsa retrieval scaffold (empty — capabilities not registered)
---

# L5 Build-Readiness Manifest — Everything Required for a Clean Press-Build

> This is the executable plan. Each line is a checkbox. When all are ✅ and the W9 pre-flight passes,
> pressing Build on L5 generates the entire dataset uninterrupted. Owner tags: **[CC]** Claude Code builds ·
> **[NATIVE]** ratify/gate. `[P2]` = exact number set at build-planning. The 13 assets are the canonical set
> from `L5_SPECS/` + `L5_MIMAMSA_ASSET_ARCHITECTURE`.

## Status legend
☐ = to do · the report below is the master list; execution ticks each box; W9 is the final gate.

---

## W0 — PRECONDITIONS (not L5 code, but L5 cannot build without them)
- ☐ **P0.0** L4 `ph_pratikara` rebuilt from corrected `kala_convergence` (the all-Jupiter fix committed) — L4-seal precondition. [CC/NATIVE]
- ☐ **L4 sealed** — `L4_PHALA_CLOSE_v1_0.md` exists; `phala_pramana` column contract frozen. [NATIVE/CC]
- ☐ **L3/L4 freshly built for `482012f1`** — `asset_throughput` rows present for all `ph_*`, `ka_*`, `bo_*`, `ga_*`, `bg_*` the L5 DAG reads. [CC]
- ☐ `CURRENT_STATE` updated (stale at v5.90). [CC]
- ☐ `PROD_DATABASE_URL` secret set; prod == main; CI green. [CC]
- ☐ **P2 numbers ratified** (caps, min-n, weights, thresholds, tolerances, held-out fraction) + corrected DAG ratified. [NATIVE]

## W1 — MIGRATIONS (every table must exist BEFORE its writer runs)
Numbered after L4's last (check BOTH `platform/migrations/` and `platform/supabase/migrations/` for the safe next number — the two-dir lexical-merge). Each ☐ = one table created + indexed.
**Core asset tables (6):**
- ☐ `mimamsa_event_provenance` + views `vw_mimamsa_held_out`, `vw_mimamsa_admissible_clean`  (mi_jivanaghatana)
- ☐ `mimamsa_predictions`  (mi_bhavisya)
- ☐ `mimamsa_manifestation_sets`  (mi_bhavisya)
- ☐ `mimamsa_calibration`  (mi_pramana)
- ☐ `mimamsa_reliability`  (mi_pramana)
- ☐ `mimamsa_multipliers`  (mi_gunanaka)
- ☐ `mimamsa_qa_eval`  (mi_pariksha)
- ☐ `mimamsa_export_log`  (mi_vistara)
**New-asset tables (promoted + insight):**
- ☐ `mimamsa_signal_families` + `mimamsa_negative_controls`  (mi_kula)
- ☐ `mimamsa_fact_adjustment`, `mimamsa_signal_adjustment`, `mimamsa_convergence_adjustment`, `mimamsa_anchor_adjustment`  (mi_adhilepa)
- ☐ `mimamsa_load_bearing`  (mi_adhilepa)
- ☐ `mimamsa_attribution`, `mimamsa_discoveries`  (mi_pariksha)
- ☐ `mimamsa_manifestation_grammar`  (mi_sambandha)
- ☐ `mimamsa_insight_units`  (mi_darshana)
- ☐ `mimamsa_insight_embeddings` (**pgvector**)  (mi_darshana)
- ☐ query-views `vw_mimamsa_insight_by_domain/_by_horizon/_by_lens/_negative_knowledge`  (mi_darshana)
**Service tables:**
- ☐ `mimamsa_preferences`  (mi_seva)
- ☐ `mimamsa_journal`  (mi_abhilekha)
**Migration hygiene:**
- ☐ surgical migrations only (no deploy.yml-auto / bulk migrate.ts)
- ☐ first L5 migration drops any stale draft `mimamsa_*` tables found in P1 audit
- ☐ all applied to prod (push-to-main auto-migrates) + ledger-reconciled
- ☐ **degenerate-distribution check:** every attribution column has the expected diversity domain documented

## W2 — REGISTRY ROWS (asset_registry_seed.ts — the DAG source of truth)
For EACH of the 13 assets, one row with ALL fields correct:
- ☐ `mi_jivanaghatana` — data, global, `count_sql` global, depends_on `[]`
- ☐ `mi_kula` ⭐ — data, global, depends_on `['bg_rules']`
- ☐ `mi_bhavisya` — data, per_chart, **depends_on `['ph_pramana','ph_nimitta','ph_phaladesa','mi_kula','mi_jivanaghatana']`** (ASSET-IDs not table names; was the bug)
- ☐ `mi_pramana` — data, **per_chart** (fix from global), depends_on `['mi_bhavisya','mi_jivanaghatana']`
- ☐ `mi_gunanaka` — data, **per_chart**, depends_on `['mi_pramana']`
- ☐ `mi_adhilepa` ⭐ — data, per_chart, depends_on `['mi_gunanaka']`
- ☐ `mi_pariksha` — data, per_chart, depends_on `['mi_pramana','mi_kula']`
- ☐ `mi_sambandha` ⭐ — data, per_chart, depends_on `['mi_pramana','mi_pariksha']`
- ☐ `mi_darshana` ⭐ — data, per_chart, pgvector, depends_on `['mi_pramana','mi_adhilepa','mi_sambandha','mi_pariksha','mi_gunanaka','mi_kula','mi_jivanaghatana']`
- ☐ `mi_vistara` — data, global, depends_on `[]`
- ☐ `mi_seva` ⭐ — **service** (`asset_kind:'service'`,`storage_type:'service'`), per_chart, depends_on `['mi_adhilepa']`, **health_probe defined**
- ☐ `mi_abhilekha` ⭐ — **service**, per_chart, depends_on `['mi_bhavisya']`, **health_probe defined**
**Per-row field correctness (each asset):**
- ☐ `count_sql` chart-scoped with `$1` (per_chart) / no `$1` (global) — the L1 NOT-MIGRATED trap
- ☐ `target_table` matches a W1 table
- ☐ `scope` correct (per_chart vs global) — drives which runner/lock
- ☐ `is_active: true`
- ☐ `sanskrit_name`/`english_name`/`english_description` set (cockpit display)
- ☐ `layer: 'mimamsa'`, `sort_order` set
- ☐ DAG edge list (the seed's edges block) includes all new edges
- ☐ no duplicate `asset_id` anywhere (would crash @register)

## W3 — WRITERS (the missing code — 10 data writers + 2 service handlers)
Each is a `@register('mi_*')` `WriterBase` subclass in `platform/python-sidecar/pipeline/orchestrator/writers/` (or a declared `source_paths` dir). Each ☐ = one writer, built to its `L5_SPECS/` spec, conforming to the FROZEN contract:
- ☐ `mi_jivanaghatana.py` — LEL load + provenance/leakage + held-out partition
- ☐ `mi_kula.py` — family registry + neg-control defs + G6
- ☐ `mi_bhavisya.py` — frozen bundle + manifestation_set (hybrid, citation-gated)
- ☐ `mi_pramana.py` — **HEAVY** (`plan_substeps`+`run_substep`): matcher → scorecard → aggregate
- ☐ `mi_gunanaka.py` — weight register + hard gate + two keys + kill-switch
- ☐ `mi_adhilepa.py` — 4 overlays + single-origin dedup + bounds + load-bearing (G3)
- ☐ `mi_pariksha.py` — **HEAVY**: attribution + neg-control harness (blocking) + degenerate guard + discovery (G1/G4/G5/G7)
- ☐ `mi_sambandha.py` — manifestation grammar (G2)
- ☐ `mi_darshana.py` — **HEAVY**: insight units + embeddings + views + provenance + negative knowledge (R1–R6)
- ☐ `mi_vistara.py` — export ledger
- ☐ `mi_seva` handler — serve-time service (effective-value, toggles, transit-current, prefs, parity)
- ☐ `mi_abhilekha` handler — journal/due-sweep/re-sync service
**Per-writer FROZEN-CONTRACT conformance (each MUST):**
- ☐ class attr `asset_id` == registry asset_id; `@register('<asset_id>')` exactly once
- ☐ implements `run(ctx)` OR (`plan_substeps`+`run_substep`); never both-missing (raises NotImplementedError)
- ☐ uses `conn = ctx.db_conn`; **never commit/rollback/close**; never opens own conn
- ☐ **never writes `asset_throughput`**
- ☐ returns `WriterResult(asset_id=…, rows_inserted=…)` — kwarg `rows_inserted` (NOT rows_written — L3 BUG-3)
- ☐ gets `chart_id` from `ctx.config`
- ☐ idempotency: natural-key-scoped `replace_prior_*` (delete-then-insert) before INSERT, scoped to sub-step key
- ☐ honors `ctx.dry_run`
- ☐ **imports clean** (any import error hard-fails `discover_all()` for ALL writers — module-level imports must resolve)
- ☐ deterministic (no generative LLM in compute — the D-1 gate); embeddings (deterministic transform) OK
- ☐ heavy writers (`mi_pramana`/`mi_pariksha`/`mi_darshana`) expose natural sub-step grain (e.g. per-domain) + heartbeat-safe

## W4 — DEPLOY / PACKAGING (the silent-prod-only failures)
- ☐ If L5 adds a top-level dir (e.g. `python-sidecar/mimamsa/` helpers): **add the COPY line in `Dockerfile.pipeline`** (the silent-hang gotcha that bit bo_pramana_mapa + every ka_/ph_)
- ☐ any new Python dependency added to the sidecar requirements + image rebuilt
- ☐ `pgvector` extension present in prod (L2 uses it — confirm) for `mimamsa_insight_embeddings`
- ☐ the pinned embedding model available to the sidecar (same provider as `bodha_signal_embeddings`)
- ☐ pinned external-data snapshots (geomag/sunspot/ephemeris) bundled/accessible (D-3)
- ☐ Cloud Run job image rebuilt + deployed (the build runs on GCP Cloud Run, not local sidecar — stale-image risk)

## W5 — RETRIEVAL LAYER (the L5_mimamsa registry — currently EMPTY)
`platform/src/lib/retrieval/registry/layers/L5_mimamsa/index.ts` is a stub. Must register L5 capabilities:
- ☐ register `mi_darshana` retrieval primitives (tools/resources/prompts) — the LLM's interface to L5
- ☐ the query-shaped views (R3) exposed as retrieval resources
- ☐ the provenance/"why" endpoint (R4) as a tool
- ☐ negative-knowledge surface (R6) retrievable
- ☐ **parity:** MCP exports == portal capabilities — extend `parity_check.ts` (CI gate) so it covers the L5 contribution-control toggles + L5 retrieval
- ☐ wire L5 calibration view into the Whole-Chart-Read (B.11) path

## W6 — SERVE-PATH + CONTRIBUTION CONTROL (mi_seva)
- ☐ shared contribution-control module (channel registry + resolver: per-request → saved → system-ON)
- ☐ the two serve-time gates: `lel_citation` + `learning_influence` (base vs effective)
- ☐ cached `effective` views + per-calibration-session invalidation
- ☐ per-family + tier-group + soundness_basis controls
- ☐ conversational-defaults behavior (LLM asks on unknown prefs; session defaults)
- ☐ MCP optional tool args for the toggles
- ☐ `contribution_state` response metadata
- ☐ transit-current binding (calls L3 `ka_*` services)

## W7 — COCKPIT / NIRMĀṆA TRACKER WIRING (so Build shows + drives L5)
- ☐ L5 `mimamsa` layer appears in `/api/cockpit/registry` with all 13 assets + correct sanskrit/english names
- ☐ Build/Update/Rebuild actions resolve the L5 DAG (the runs API → runner path) for `482012f1`
- ☐ services render correctly (not as buildable-table assets — they show health, not row counts)
- ☐ SSE live-transition events fire for L5 assets (the DAG constellation)
- ☐ `count_sql` returns correct chart-scoped counts post-build (stats route reads count_sql) — no NOT-MIGRATED
- ☐ build-access = owner/admin only (Nirmāṇa permission rule)

## W8 — TESTS + SEAL GATES (the runtime guarantees, P6)
- ☐ `discover_all()` succeeds (all writers import) — CI
- ☐ every `mi_*` registers; `get_writer` not None for all 10 data assets
- ☐ DAG resolves: no dangling depends_on edges; acyclic (recursive closure terminates)
- ☐ reproducibility: run L5 twice → byte-identical overlays + scorecards (RL-1) **[SEAL]**
- ☐ OFF==baseline: `learning_influence` off == pre-L5 byte-for-byte (RL-2) **[SEAL]**
- ☐ no-LLM-in-L5: CI grep, zero generative-LLM calls in writers (D-1) **[SEAL]**
- ☐ negative-control battery scores null; FAIL blocks seal (E3) **[SEAL]**
- ☐ double-count path test: one finding adjusts a dependent prediction exactly once **[SEAL]**
- ☐ no-L0-touch: no overlay targets a `bg_*` **[SEAL]**
- ☐ pre-registration admissibility enforced (HC-5) **[SEAL]**
- ☐ falsifier-as-judge + no post-hoc manifestation widening **[SEAL]**
- ☐ insufficient-evidence honesty (min-n → no number, B.12) **[SEAL]**
- ☐ degenerate-distribution guard active across all attribution columns (RL-6) **[SEAL]**
- ☐ bounds + two-key lock enforced **[SEAL]**
- ☐ all `mimamsa_*` registered with drift_detector + schema_validator (RL-5)
- ☐ meta-calibration + discriminative-validity headline produced (HC-2/HC-3)

## W9 — THE PRE-BUILD PRE-FLIGHT (the final gate — run immediately BEFORE pressing Build)
A deterministic check that ALL of the above is in place. **If any item fails, do NOT press Build.**
1. ☐ Registry resolves — every `mi_*.depends_on` entry exists as an `asset_id` (the asset-id-not-table check); zero dangling edges.
2. ☐ DAG acyclic — recursive closure terminates for every `mi_*`.
3. ☐ Writers present + clean — `discover_all()` succeeds; `get_writer('mi_*')` not None for all 10 data assets; 2 service handlers registered.
4. ☐ Tables exist — every W1 table + view present in prod.
5. ☐ `count_sql` valid — each runs, returns an int, chart-scoped correctly.
6. ☐ Upstream built — `ph_pramana`/`ph_nimitta`/`ph_phaladesa`/`bg_rules`/`bo_laksana`/`ka_sangam` have `asset_throughput` rows for `482012f1`.
7. ☐ Services excluded from the build-DAG spine (asset_kind:service).
8. ☐ pgvector + embedding model available.
9. ☐ Cloud Run job image == current main (no stale image).
10. ☐ P2 numbers present (no `[P2]` placeholder left in active config).

---

## How to read the verdict
- **Every box in W0–W8 ticked + W9 all-green → press-Build generates the entire L5 dataset uninterrupted.** I can then state that affirmatively.
- **Any W9 item red → build will interrupt or under-generate.** W9 is the single source of truth for "ready or not."
- Today: **NOT ready** — W1 (no migrations), W2 (6 rows missing + the asset-id bug), W3 (zero writers), W5 (empty retrieval), W6/W7 (not wired) are all open. This manifest is the plan to close them.

## What I can vs cannot verify pre-build
- **I (Cowork) verify the build-time CONTRACT** (W1/W2/W5/W7/W9 structural items) by inspecting registry + code.
- **W3 writer runtime + W8 seal gates** are verifiable only once the writers exist (P4) + run against the live build. The W9 pre-flight + W8 seals are what convert "specs look right" into "the build provably works."

---

*End of L5_BUILD_READINESS_MANIFEST v1.0. Nine workstreams (W0 preconditions · W1 migrations · W2 registry ·
W3 writers · W4 deploy · W5 retrieval · W6 serve · W7 cockpit · W8 tests/seal · W9 pre-flight) enumerate
EVERYTHING required for press-Build to generate the entire L5 dataset. Execute the boxes; when W9 is
all-green, the build is guaranteed to run clean. The missing writers (W3) and every other gap now appear
explicitly as checklist items, as required.*
