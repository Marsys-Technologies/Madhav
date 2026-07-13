---
artifact: NIGHT1_LANE1_GA_STRUCTURAL_MODULARIZATION
type: IMPLEMENTATION BRIEF (Sonnet-executable, self-contained)
version: 1.0
status: READY
campaign: Doctrine Campaign D-1 / Night-1
lane: L1 — ga_structural internal modularization + effective_dignity fix
depends_on_lanes: NONE (first D-1 lane; BLOCKS Lane 2)
register_rows: CR-50 (writer half deferred to serving — see anti-scope), effective_dignity inconsistency (design §10c)
design_ref: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §10 (a)(b)(c)
---

# LANE 1 — `ga_structural` internal modularization + `effective_dignity` fix

## 0. Why (verbatim from the design, §10)

> **Scope today:** ~6,372 lines, ~30 fact families × 30 vargas — vast enumeration, zero judgment, one internal inconsistency (`effective_dignity` uses a 15° longitude orb foreign to the file's own Parāśari model, D1-only, fixed benefic/malefic sets ignoring functional status computed elsewhere in the same file).
>
> **Elevate:** (a) split internally into **registered sub-builders** (one per family) behind the unchanged asset contract — modularity, no DAG change; (b) keep it **enumeration-pure** — all new judgment goes to `ga_vichara`; (c) fix the `effective_dignity` inconsistency; (d) CR-50 default-ordering ... + §N.6 density. Scope is right; shape and downstream consumption need work.

This lane delivers (a), (b), (c). Item (d) is serving-plane → Lane 5.

## 1. Exact scope

**File modified / split:** `platform/python-sidecar/ga_writers/ga_structural_writer.py` (6,372 lines as of 2026-07-13).
**Asset contract UNCHANGED:** asset_id stays `ga_structural`; the orchestrator adapter `platform/python-sidecar/pipeline/orchestrator/writers/ga_structural.py` keeps its exact shape (heavy writer, `plan_substeps` = one `SubStep` per ayanamsha over `CANONICAL_AYANAMSHAS`, `run_substep` → `build_ga_structural_substep(chart_id, build_id, ayanamsha_id, conn, birth_params)`). If you find you must change the adapter's public signature, STOP and report.
**Target table UNCHANGED:** `chart_facts` (single `INSERT INTO chart_facts` path, currently around line 3301). No schema migration in this lane.

### 1.1 The sub-builder registry (design §10a)

The file already has ~45 family builders named `_build_*_rows` (verified at these line anchors, which will drift — re-grep `^def _build_` before starting): `_build_aspect_rows` (1046), `_build_shadbala_extension_rows` (1308), `_build_yoga_rows` (1933), `_build_dosha_rows` (2043), `_build_avastha_rows` (2254), `_build_functional_class_rows` (2575), `_build_special_state_rows` (2972 — contains the effective_dignity block), `_build_house_lord_matrix_rows` (3558), `_build_karaka_web_rows` (4041), `_build_sambandha_per_varga_rows` (5473), `_build_bhava_web_per_varga_rows` (5545 — emits `bhava_significance_link`), `_build_nakshatra_dispositor_chain_rows` (5922), … and the rest.

Refactor to a **module-level ordered registry**:

```python
# ga_writers/ga_structural/registry.py  (or top of the writer if you keep one file)
STRUCTURAL_SUB_BUILDERS: list[tuple[str, Callable[..., list[dict]]]] = [
    ("aspects", _build_aspect_rows),
    ("shadbala_extension", _build_shadbala_extension_rows),
    ...
]
```

Rules:
1. **One registry entry per fact family**; entry name = stable family key (used in logs and per-family row counts in `WriterResult.notes`).
2. `build_ga_structural_substep` becomes a thin driver: load shared chart state once (positions, varga states, catalogs — exactly what it loads today), then iterate the registry, concatenating rows, then the single existing `INSERT INTO chart_facts` + the existing delete-then-insert idempotency scoped to `(chart_id, ayanamsha_id)` (§N.3 — per-chart delete-then-insert, rebuild REPLACES never accretes). Do not move the DELETE inside sub-builders.
3. Preferred physical shape: split into a package `ga_writers/ga_structural/` with one module per family group (e.g. `families_aspects.py`, `families_vargas.py`, `families_esoteric.py`, …) plus `registry.py` and a `__init__.py` re-exporting `build_ga_structural_substep` at the old import path `ga_writers.ga_structural_writer` (keep a shim module `ga_writers/ga_structural_writer.py` that re-exports EVERYTHING other modules import today — verified importers include `pipeline/orchestrator/writers/ga_structural.py` (`build_ga_structural_substep`) and `ga_writers/ga_yoga_writer.py` (`_load_varga_positions`). Grep for every `from ga_writers.ga_structural_writer import` / `from ga_writers import ga_structural_writer` and keep all of them working). If the package split threatens the timebox, the fallback is registry-within-one-file — the registry is the non-negotiable deliverable, the file split is the preferred one.
4. **Mechanical refactor discipline**: no behavior change in any family except effective_dignity (§1.2). Move code, don't edit it.

### 1.2 The `effective_dignity` fix (design §10c)

Current code (verified, inside `_build_special_state_rows`, ~lines 3050–3086): for each graha it sums ±0.25 per other graha within a **15° longitude orb**, with **fixed sets** `benefics = {"Jupiter","Venus","Mercury"}` / `malefics = {"Saturn","Mars","Sun"}`, then `effective_dignity_score = clamp(base_dignity_score + net_modification * 0.1, 0, 1)`, emitted as fact family `graha_effective_dignity_modified_by_aspects` (key `effective_dignity_score`), D1 only.

Three inconsistencies to fix, per design §10 + register §I.1:

1. **Aspect model**: replace the 15° longitude-orb proximity test with the file's OWN Parāśari model — the same `PARASHARI_ASPECTS` graha-specific house-based aspect offsets + strengths already used by `_build_aspect_rows` (and the retrograde modification builder around line 5430). An aspecting graha contributes `±0.25 × aspect_strength` where `aspect_strength` is the Parāśari strength for that house offset (full aspect = 1.0, special aspects per the existing table). A graha that casts no Parāśari aspect on the target's house contributes 0 — regardless of longitude proximity. Same-house conjunction counts as association at strength 1.0 (this preserves the old behavior's core case).
2. **Benefic/malefic status**: replace the fixed natural sets with **functional status for the chart's lagna**, from the same file's `_get_functional_class_dynamic(g_name, lagna_sign)` (used by `_build_functional_class_rows`, line ~2575). Map: functional benefic → +0.25×strength; functional malefic → −0.25×strength; functional neutral → 0. Moon/Mercury conditional-benefic subtleties: use exactly what `_get_functional_class_dynamic` returns — do not invent a new classifier (B.10). Keep the natural-set computation ONLY if `_get_functional_class_dynamic` returns nothing for a graha (Rahu/Ketu may be outside its domain) — in that case fall back to natural class and record `"fallback":"natural_class"` in the row's `value_jsonb`.
3. **Varga scope**: the fact stays honest about being D1: it is emitted per-ayanamsha within the D1 special-state pass — that is fine, keep D1-only. Do NOT extend it per-varga in this lane (that is ga_vichara judgment territory, Lane 2 — enumeration-purity §10b).

Formula versioning (B.8): change the row's `source` string from `pyjhora_adapter.effective_dignity/{eng_ver}` to `ga_structural.effective_dignity_v2/{eng_ver}` and include `{"formula":"parashari_aspect_functional_v2", "base_dignity": ..., "contributions":[{graha, aspect_strength, functional_class, delta}]}` in `value_jsonb` so downstream consumers can audit the change (B.3 derivation-ledger).

### 1.3 Enumeration purity (design §10b) — a constraint, not a task

While refactoring you will be tempted to "improve" families with judgment (valence, ratification, rankings). **Do not.** All judgment lands in the NEW asset `ga_vichara` (Lane 2). This writer enumerates; if a change makes a row express an opinion about good/bad rather than a structural fact, it belongs in Lane 2.

## 2. Contract to satisfy (quoted from ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2/§5)

> - `WriterBase`: **light writer** → `run(ctx) -> WriterResult`; **heavy writer** → `plan_substeps(ctx) -> list[SubStep]` + `run_substep(ctx, step) -> WriterResult`.
> - **Connection:** uses `ctx.db_conn` exclusively; **never** opens its own, **never** `commit()/rollback()/close()`.
> - **Idempotency:** natural-key-scoped replace on `ctx.db_conn` immediately before INSERT, scoped to the sub-step key; any sub-step safe to re-run.
> - **Telemetry:** writes **nothing** to `asset_throughput`; returns counts in `WriterResult`.
> - **FORENSIC:** any native-anchored assertion is guarded `if chart_id == CANONICAL_CHART_ID`; structural invariants stay unconditional.
> - **No orchestrator change required** — if onboarding needs a new `if` in `run_asset`/`runner.py`, the contract was violated; fix the writer, not the orchestrator.

`ga_structural` already satisfies all of this; your job is to not break it. One exception to note: `source_paths` in the adapter (`pipeline/orchestrator/writers/ga_structural.py:20`) lists `platform/python-sidecar/ga_writers/ga_structural_writer.py` — if you split into a package, update `source_paths` to the package's files (this list feeds `get_writer_git_hash`; an incomplete list silently breaks build-provenance hashing).

## 3. Tests

- Existing suite: `pytest platform/python-sidecar` must show **zero new failures**. `ga_structural` has existing tests — find them with `grep -rln "ga_structural" platform/python-sidecar --include="test_*.py" --include="*_test.py"` and keep them green.
- **New — registry completeness**: a test asserting every `_build_*_rows` family function is present in `STRUCTURAL_SUB_BUILDERS` exactly once (reflection over the module), so a future family can't be silently dropped from the build.
- **New — refactor row-parity**: for a fixture chart state (use whatever fixture pattern the existing ga_structural tests use), total rows and the multiset of `(fact_category, fact_subject, fact_key)` from the driver equal the pre-refactor output for all families EXCEPT `graha_effective_dignity_modified_by_aspects`. Cheapest honest form: capture a pre-refactor fixture (category → row-count + key multiset) in a first commit, assert against it after.
- **New — effective_dignity v2**: unit tests: (i) a functional-malefic full-aspecting graha lowers the score by 0.025 (0.25×1.0×0.1); (ii) a graha with no Parāśari aspect on the target contributes 0 even at <15° longitude distance; (iii) score clamps to [0,1]; (iv) `value_jsonb.formula == "parashari_aspect_functional_v2"`.

## 4. Acceptance criteria

- [ ] `STRUCTURAL_SUB_BUILDERS` registry exists; driver iterates it; registry-completeness test passes.
- [ ] Import shim intact: `from ga_writers.ga_structural_writer import build_ga_structural_substep` and `_load_varga_positions` still work (ga_yoga_writer imports the latter — verified dependency).
- [ ] Adapter `pipeline/orchestrator/writers/ga_structural.py` diff is nil or `source_paths`-only.
- [ ] Row-parity test green (all families byte-stable except effective_dignity).
- [ ] effective_dignity v2: Parāśari aspects + functional class; v2 formula version stamped; 4 unit tests green.
- [ ] Full sidecar suite zero new failures.
- [ ] No new judgment rows, no new fact families, no schema migration.

## 5. Known traps (cite: register)

- **CR-53 / FORENSIC**: the writer contains native-anchored FORENSIC assertions guarded by `CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"` — keep the guards exactly; never make them unconditional, never delete them.
- **CR-72/CR-73 (dosha stubs)**: you will refactor `_build_dosha_rows`/`_build_yoga_rows` into the registry — move them **as-is**. Their `requires_pass` label-stub defect is Lane 3's job (with a documented handshake — see LANE3 §1.3); fixing it here creates a merge conflict and splits the audit trail.
- **§N.5**: don't restate computed values across families "for convenience" — each family computes its own facts from chart state, referencing not duplicating.
- **The 15° orb is not "a bug to keep partially"**: the design ruling is total replacement by the file's own Parāśari model. Do not blend the two.

## 6. Anti-scope

- NO new asset, NO `ga_vichara` work (Lane 2), NO valence/ratification/leverage logic.
- NO detector work (dhana yogas, NBRY, dosha cancellation — Lane 3).
- NO serving-plane/TypeScript changes; CR-50 default-ordering is Lane 5's.
- NO migration, NO DB schema change, NO chart rebuilds (CONDUCTOR owns rebuilds).
- Do NOT modify the frozen orchestrator (`pipeline/orchestrator/writers/__init__.py`, `runner.py`, `run_asset`).

## 7. Done-definition / handback

Worktree branch with the refactor + fix + tests, full suite green. Report: final module layout, registry entry list with per-family row counts from a dry run if available, the effective_dignity diff summary, and §4 checklist confirmation. **Lane 2 starts from your merged branch** — flag the exact commit.
