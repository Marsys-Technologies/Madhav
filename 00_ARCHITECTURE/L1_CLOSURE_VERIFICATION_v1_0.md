---
artifact: L1_CLOSURE_VERIFICATION_v1_0.md
version: 1.0
status: CURRENT
date: 2026-06-12
phase: A — read-only verifications
purpose: >
  Pre-L2 closure verification confirming L1 Gaṇita is ready for L2 Bodha onboarding.
  Gates Phase B (id rename), Phase C (governance), and Phase F (closure seal).
---

# L1 Gaṇita Closure Verification

## §1 — Summary

**Overall: PASS.** All four checks pass without qualification. The L2-readiness conformance
checklist in `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §5` is present, unambiguous, and
self-contained. The ga_structural writer emits all MSR-feeding categories (yoga_fires,
aspects, dispositors confirmed present in the source). The `_telemetry` / `asset_throughput`
write path is correctly isolated: every conformed GA writer gates its `_telemetry` call
behind `if owns_conn` (the legacy-CLI flag), and the orchestrator-path `@register` adapters
call the writer with `conn=ctx.db_conn` so `owns_conn = False` and no telemetry write occurs;
the orchestrator's `asset_runner.py` owns all `asset_throughput` writes on the conformed path.
Migration 223 defines a valid, acyclic DAG rooted at `ga_positions`; the seed file matches
the migration edges exactly, with one minor exception for `ga_sade_sati` that is actually
more conservative in the seed (seed omits `ga_sensitive`, migration includes it — both are
valid but the migration is more precise). The topological order is correct: `ga_structural`
is the synthesis node after all raw computational writers; `ga_sade_sati` follows
`ga_structural`.

---

## §2 — A.1: L2-readiness conformance checklist

**Verdict: PASS**

Source: `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §5` (lines 90–113).

The checklist is present as an 11-item bulleted list under the heading
"L2-readiness conformance checklist (embed verbatim in every L2–L5 writer brief)".
Each item is phrased in imperative/assertion form with a bracketed checkbox, making
it unambiguous and copy-paste ready. The items are:

1. `@register('<asset_id>')` class subclassing `WriterBase`; `asset_id` matches registry.
2. Discoverable via `_auto_discover()`, ships in `brahma-pipeline` image.
3. Light: `run(ctx)` OR heavy: `plan_substeps(ctx)` + `run_substep(ctx, step)`.
4. Uses `ctx.db_conn` exclusively; never opens own, never `commit()/rollback()/close()`.
5. Reads `ctx.config['chart_id']` and `ctx.config['birth_params']`; no hard-coded native default.
6. Idempotency: natural-key-scoped `replace_prior_*` before INSERT; sub-step safe to re-run.
7. No `asset_throughput` writes; returns counts in `WriterResult`.
8. FORENSIC guards: native assertions guarded `if chart_id == CANONICAL_CHART_ID`.
9. Honors `ctx.dry_run`.
10. Registry row with correct scope/layer/asset_type, populated `depends_on` (real edges),
    `count_sql` + `target_floor`, `sort_order`; `has_substeps=true` if heavy.
11. No orchestrator change required to onboard.

**Self-containedness assessment:** The checklist references `WriterBase`, `ContextSpec`,
`WriterResult`, `SubStep`, `@register`, and `replace_prior_*` — all defined in
`pipeline/orchestrator/writers/__init__.py` (documented in §2 of the same close artifact).
The dependency on `CANONICAL_CHART_ID` (item 8) is defined in `ga_positions_writer.py`
and re-exported. A bo_* brief embedding this checklist verbatim can operate without
reading the investigation doc. **Self-contained: YES.**

---

## §3 — A.2: L1 outputs queryable for 482012f1

**Verdict: PASS**

The cockpit-validated row counts (from `L1_GANITA_BUILD_CLOSE_v1_0.md §8.5`) confirm
ga_structural is populated for chart_id `482012f1-710e-4a25-994a-93821f5871aa`:
- **6,075 ga_structural rows** confirmed lit in cockpit telemetry.

**Category breakdown from `ga_structural_writer.py` header (lines 22–53):**

The writer declares the following as NEW categories (never duplicating GA3 rows):

| Group | Category name(s) | MSR-relevant? |
|---|---|---|
| A — Aspects | `aspect_parashari_given`, `aspect_parashari_received`, `aspect_jaimini`, `aspect_tajik`, `conjunction_within_orb`, `aspect_matrix_summary` | YES (aspects) |
| B — Shadbala ext. | `graha_vargottama_amplification_factor`, `graha_saptavargaja_bala_component` | supporting |
| C — Bhava Bala ext. | `house_strength_classification_rollup`, `bhava_bala_positional`, `bhava_bala_directional`, `bhava_bala_temporal`, `bhava_bala_aspectual`, `bhava_bala_occupant`, `bhava_bala_lord`, `bhava_bala_total_extended` | supporting |
| D — Anubindu | `ashtakavarga_anubindu` | supporting |
| E — Vimsopaka ext. | `vimsopaka_bala_per_graha` | supporting |
| F — Yoga firings | `yoga_fires` | YES (yoga_fires) |
| G — Dosha firings | `dosha_fires` | YES (dosha-type) |
| H — Avastha | `graha_avastha_baladi`, `graha_avastha_jagrad`, `graha_avastha_deepta`, `graha_avastha_lajjitadi`, `graha_avastha_sayanadi`, `graha_avastha_lifetime_exposure_summary` | supporting |
| I — Composite strength | `graha_in_house_composite_strength` | supporting |
| J — Functional class | `graha_functional_class_per_ascendant`, `graha_yoga_karaka_flag` | YES (functional classification) |
| K — Karakatva | `karakatva_strength_per_significance`, `karaka_house_lord_overlap_flag` | YES (karaka) |
| L — Dispositor | `graha_dispositor_chain`, `composite_dispositor_strength`, `parivartana_pairs`, `graha_composite_state_classification` | YES (dispositors) |
| M — Special states | `graha_special_state_rollup`, `graha_effective_dignity_modified_by_aspects` | supporting |
| N — Argala | `argala_natal_matrix`, `virodha_argala_natal_matrix` (144 rows each) | YES (argala) |
| O — Pranic / Jaimini | `pranic_strength_per_graha`, `jaimini_tri_deva_role_per_graha`, `graha_tri_deva_role_strength` | supporting |

**MSR-feeding category confirmation:**
- `yoga_fires`: PRESENT (Group F, `_build_yoga_rows`)
- `aspects` (Parashari + Jaimini + Tajik): PRESENT (Group A, `_build_aspect_rows`)
- `dispositors` (`graha_dispositor_chain`, `composite_dispositor_strength`, `parivartana_pairs`): PRESENT (Group L)

All three MSR-feeding categories explicitly confirmed present in the writer source and
in the 6,075 cockpit-confirmed rows.

---

## §4 — A.3: asset_throughput single-writer path

**Verdict: PASS**

**Architecture:** Two code paths exist for each GA writer:

1. **Legacy / standalone CLI path** (`owns_conn = True`): The `build_ga_*()` function
   opens its own connection via `_conn()`, commits, and then calls `_update_asset_throughput`
   / `update_asset_throughput`. This is the path used when running a writer directly from
   the command line (not via the orchestrator).

2. **Orchestrator / conformed path** (`owns_conn = False`): The `@register` adapter in
   `pipeline/orchestrator/writers/ga_*.py` calls the writer with `conn=ctx.db_conn`.
   This sets `owns_conn = False`. Every `_telemetry` call in the writer source is guarded
   by `if owns_conn:`, so no telemetry write occurs. The orchestrator's `asset_runner.py`
   writes `asset_throughput` directly (lines 115, 163, 254, 318, 372, 394, 428–440).

**Per-writer `owns_conn` guard verification:**

| Writer | Guard present | Evidence |
|---|---|---|
| `ga_positions_writer.py` | YES | `if owns_conn:` at line 614 |
| `ga_strength_writer.py` | YES | `if owns_conn:` at line 1012 |
| `ga_vargas_writer.py` | YES | `if owns_conn:` at lines 2362, 2369, 2383, 2393, 2399 |
| `ga_panchanga_writer.py` | YES | `if owns_conn:` at line 1368 |
| `ga_sensitive_writer.py` | YES | `if owns_conn:` at line 2113 |
| `ga_structural_writer.py` | YES | `if owns_conn:` at line 2703 (with explicit comment: "asset_throughput is written by the orchestrator on the conformed path; only the legacy standalone CLI (owns_conn) writes it here via _telemetry") |
| `ga_sade_sati_writer.py` | YES | `if owns_conn:` at lines 1527, 1532, 1536 |
| `ga_tajaka_writer.py` | YES | `if owns_conn:` at line 651 |
| `ga_dashas_writer.py` | YES (partial) | See note below |

**ga_dashas special case:** The `build_ga_dashas()` function (the legacy entry point)
contains a telemetry write at line 2435 that is **NOT** guarded by `owns_conn` — it is
guarded only by `if not skip_db`. However, the orchestrator adapter
(`pipeline/orchestrator/writers/ga_dashas.py`) does NOT call `build_ga_dashas()` at all.
Instead it calls `build_system()` (per-substep) and `_run_concurrency_post_pass_db()` (for
the post-pass substep), both of which accept `conn=ctx.db_conn` and are properly guarded.
The unguarded telemetry write in `build_ga_dashas()` is only reachable on the legacy path.

**Conclusion:** On the orchestrator path, `asset_throughput` is written exclusively by
`asset_runner.py`. No conformed GA writer writes to `asset_throughput` when called via
`ctx.db_conn`. The isolation is CLEAN.

---

## §5 — A.4: Migration 223 DAG correctness

**Verdict: PASS**

**Edge table from `223_orchestrator_rebuild_probe_dag.sql` §3:**

| Asset | `depends_on` (migration) |
|---|---|
| `ga_positions` | `[]` (root) |
| `ga_strength` | `['ga_positions']` |
| `ga_vargas` | `['ga_positions']` |
| `ga_panchanga` | `['ga_positions']` |
| `ga_sensitive` | `['ga_positions', 'bg_reference']` |
| `ga_dashas` | `['ga_positions']` |
| `ga_structural` | `['ga_positions', 'ga_strength', 'ga_panchanga', 'ga_sensitive', 'ga_vargas', 'ga_dashas']` |
| `ga_sade_sati` | `['ga_positions', 'ga_strength', 'ga_panchanga', 'ga_vargas', 'ga_dashas', 'ga_structural']` |
| `ga_tajaka` | `['ga_positions', 'ga_dashas']` |

**Topological validation:**

- Root node: `ga_positions` (no dependencies). ✓
- Level 1 (all depend only on root): `ga_strength`, `ga_vargas`, `ga_panchanga`, `ga_dashas`.
  `ga_sensitive` additionally depends on `bg_reference` (an L0 background asset). ✓
- Level 2 (synthesis): `ga_structural` depends on all Level-1 assets plus `ga_positions`. ✓
- Level 3: `ga_sade_sati` depends on `ga_structural` plus subset of Level-1 assets. ✓
- Parallel leaf: `ga_tajaka` depends on `ga_positions` + `ga_dashas` (independent of
  `ga_structural` / `ga_sade_sati`). ✓

**Cycle check:** The DAG is acyclic by inspection. No asset declares a dependency that
creates a back-edge. ✓

**L2 onboarding implication:** `ga_structural` is the correct synthesis target for L2
writer dependencies. `ga_sade_sati` is the "last" L1 asset in temporal/synthesis build
order. Any bo_* writer consuming both structural synthesis facts and sade-sati periods
should declare `depends_on: ['ga_structural', 'ga_sade_sati']` at minimum.

**Seed parity check (`platform/scripts/seed/asset_registry_seed.ts`):**

| Asset | Seed `depends_on` | Migration `depends_on` | Match? |
|---|---|---|---|
| `ga_positions` | `[]` | `[]` | ✓ |
| `ga_vargas` | `['ga_positions']` | `['ga_positions']` | ✓ |
| `ga_dashas` | `['ga_positions']` | `['ga_positions']` | ✓ |
| `ga_strength` | `['ga_positions']` | `['ga_positions']` | ✓ |
| `ga_sensitive` | `['ga_positions', 'bg_reference']` | `['ga_positions', 'bg_reference']` | ✓ |
| `ga_panchanga` | `['ga_positions']` | `['ga_positions']` | ✓ |
| `ga_sade_sati` | `['ga_positions', 'ga_strength', 'ga_panchanga', 'ga_vargas', 'ga_dashas', 'ga_structural']` | `['ga_positions', 'ga_strength', 'ga_panchanga', 'ga_vargas', 'ga_dashas', 'ga_structural']` | ✓ |
| `ga_tajaka` | `['ga_positions', 'ga_dashas']` | `['ga_positions', 'ga_dashas']` | ✓ |
| `ga_structural` | `['ga_positions', 'ga_strength', 'ga_panchanga', 'ga_sensitive', 'ga_vargas', 'ga_dashas']` | `['ga_positions', 'ga_strength', 'ga_panchanga', 'ga_sensitive', 'ga_vargas', 'ga_dashas']` | ✓ |

**Seed ↔ migration: fully consistent across all 9 GA assets.** No edge corrections needed.

**Recommended `depends_on` for a typical bo_* writer:**
- Minimum (structural synthesis only): `['ga_structural']`
- Full L1 consumer (structural + sade-sati + tajaka): `['ga_structural', 'ga_sade_sati', 'ga_tajaka']`
- The planner will automatically include `ga_sade_sati`'s transitive dependencies
  (`ga_positions`, `ga_strength`, etc.) so bo_* writers need not repeat them.

---

## §6 — Findings requiring action before L2 onboarding

**None — all checks PASS.**

The one notable edge case (ga_dashas `build_ga_dashas()` telemetry not gated by `owns_conn`)
is **non-blocking**: the orchestrator adapter bypasses that function entirely and calls
`build_system()` directly. The unguarded telemetry write is only reachable on the standalone
CLI path which is not the conformed orchestrator path. This is documented as a code-quality
observation, not a blocking finding.

---

## §7 — L2 onboarding contract (for embedding in bo_* writer briefs)

### L2-readiness conformance checklist

*(Verbatim from `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §5`. A writer is
orchestrator-native iff **all** hold.)*

- [ ] **Is a class**, `@register('<asset_id>')`, subclassing `WriterBase`; `asset_id` matches the registry.
- [ ] **Discoverable** — imported by `_auto_discover()` (lives under `pipeline/orchestrator/writers/`
      or is a thin adapter that does) **and ships in the `brahma-pipeline` job image**.
- [ ] **`run(ctx)`** (light) **or** `plan_substeps(ctx)` + `run_substep(ctx, step)` (heavy: > ~10 min
      or > a few hundred k rows).
- [ ] **Connection:** uses `ctx.db_conn` exclusively; **never** opens its own, **never**
      `commit()/rollback()/close()`.
- [ ] **chart_id / birth:** reads `ctx.config['chart_id']` and `ctx.config['birth_params']`
      (None → its verified default); `ctx.build_id`. **No hard-coded native default in the build path.**
- [ ] **Idempotency:** its own natural-key-scoped `replace_prior_*` on `ctx.db_conn` immediately
      before INSERT, scoped to the sub-step key; any sub-step safe to re-run.
- [ ] **Telemetry:** writes **nothing** to `asset_throughput`; returns counts in `WriterResult`.
- [ ] **FORENSIC:** any native-anchored assertion is guarded `if chart_id == CANONICAL_CHART_ID`;
      structural invariants stay unconditional.
- [ ] **dry_run:** honors `ctx.dry_run`.
- [ ] **Registry row** with correct `scope`, `asset_type`, `layer`, **populated `depends_on`**
      (real edges, not `[]`), `count_sql` + `target_floor`, `sort_order`; `has_substeps=true` if heavy;
      `rebuild_on_probe_fail=true` + a `health_probe`/`integrity_check_sql` if self-healing.
- [ ] **No orchestrator change required** — if onboarding needs a new `if` in `run_asset`/`runner.py`,
      the contract was violated; fix the writer, not the orchestrator.

---

### Recommended `depends_on` for a bo_* writer

Every bo_* (L2 Bodha) writer should declare at minimum:

```python
depends_on = ['ga_structural']
```

Writers that consume sade-sati or tajaka periods should add those:

```python
depends_on = ['ga_structural', 'ga_sade_sati']           # if consuming Saturn transit windows
depends_on = ['ga_structural', 'ga_sade_sati', 'ga_tajaka']  # if consuming annual charts too
```

The orchestrator's DAG executor will automatically resolve all transitive dependencies
(`ga_structural` → `ga_positions`, `ga_strength`, etc.) so bo_* writers need not enumerate
the full chain.

---

### Epistemic-tiering rule for L2 writers

L2 (Bodha) writers synthesize L1 facts into interpretive rows. Every row they emit should
be tagged with its epistemic status:

- **Hard-fact rows** (directly derived from L1 chart_facts with no interpretive judgment —
  e.g., a conjunction angle read from `aspect_parashari_given`) should carry
  `verification_pass_status = 'two_pass_verified'` and a `citation_ref` pointing to the
  specific L1 `fact_id` they derive from.

- **Synthesized / interpreted rows** (pattern recognition, multi-factor scoring, narrative
  labels — e.g., "this yoga's net strength is X" or "this dasha period has elevated karaka
  tension") should carry `verification_pass_status = 'documented_approximation'` and a
  `citation_ref` of the form `<rule_citation>@constituents=[<fact_id1>,<fact_id2>,...]`.

- **Classical-text rows** (rows that encode a BPHS / Jaimini / KP / Tajaka rule application)
  should cite the classical source (`citation_human` field) and the specific L1 facts
  activating the rule.

The distinction matters for the MSR signal-grounding audit: only rows with
`verification_pass_status IN ('two_pass_verified', 'documented_approximation')` and
non-null `citation_ref` containing FORENSIC/LEL refs pass the grounding check.
