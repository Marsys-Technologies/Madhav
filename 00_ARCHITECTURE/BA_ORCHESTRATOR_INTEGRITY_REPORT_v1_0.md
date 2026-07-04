---
artifact: BA_ORCHESTRATOR_INTEGRITY_REPORT
type: audit_report
version: 1.0
status: CURRENT
authored_by: Claude (BA_FULL_ASSET_AUDIT)
date: 2026-07-05
---

# BA Orchestrator Integrity Report (v1.0)

Scope: the FROZEN orchestrator (`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`) and its live DAG across all 91 `@register()` writers in the current build (L0 Brahmagyan → L5 Mīmāṃsā). Covers static graph structure, `dag_edge_guard.py`'s live edge-completeness check, a resolve-plan simulation of `resolveBuildPlan` (`plan.ts`), and an explicit rebuild-readiness verdict.

---

## 1. Static graph summary

- **Cycles found:** none. `[]` — the 91-asset DAG is acyclic.
- **Dangling deps found:** none. `[]` — every `depends_on` entry across all 91 assets resolves to a real, registered `asset_id`.

Static structure is clean. The issues below are all **edge-completeness** issues (real runtime reads not reflected in declared `depends_on`), not structural graph defects.

---

## 2. Undeclared runtime edges

`dag_edge_guard.py` was run live against the current DB and writer source (`python -m pipeline.orchestrator.dag_edge_guard`). It scans each writer's SQL for `FROM`/`JOIN` targets and cross-checks against `asset_registry.depends_on`, exempting a documented `_UNGATED_PREFIXES` allowlist (`bg_*`/`brahma_*`/`reference_*`/`sutravali_*`/`classical_*` — L0 static bedrock, assumed always-present, gated separately by a precondition check on `brahma_remedy_corpus` emptiness in `runs/route.ts`).

### 2.1 HARD violations (non-exempt — genuine per-chart cross-asset reads missing from `depends_on`)

| asset | missing dependency | evidence |
|---|---|---|
| `ka_taranga` | `ka_sangam` | `ka_taranga.py:133` — `FROM kala_convergence` (ka_sangam's target table). `depends_on=[ka_avadhi, bo_pratijna]`; ka_sangam not in transitive closure. |
| `ka_yojaka` | `bo_pratijna` | `ka_yojaka.py:67,81` — `FROM bodha_pratijna bp ... JOIN brahma_event_ontology`, inside a SAVEPOINT-guarded soft-dependency block (comment: "soft dependency on P3B data — bodha_pratijna may not be built yet"). `depends_on=[bo_laksana, bg_transit_rules, ga_dashas, bo_bimba, bo_sangati]`; bo_pratijna absent. |
| `mi_darshana` | `bo_pratijna` | `mi_darshana.py:240,248,296` — `FROM bodha_pratijna bp ... JOIN brahma_event_ontology`; `SELECT COUNT(DISTINCT ayanamsha_id) FROM bodha_pratijna`. `depends_on=[mi_pramana, mi_adhilepa, mi_sambandha, mi_pariksha, mi_gunanaka, mi_kula, mi_jivanaghatana]`; bo_pratijna absent (cross-layer L2→L5 gap). |

All three are CI-confirmed real HARD violations: `dag_edge_guard.py` exits 1 with these reported. Each is a genuine per-chart cross-asset read the L0-bedrock exemption does not cover, meaning the wave-parallel scheduler (`runner.py execute_dag`) can legally dispatch these writers before their true upstream is lit — silently building on incomplete/absent data. This is exactly the failure class the guard (migration 365 lineage) was built to catch.

### 2.2 Tooling false positive (4th guard-reported violation — not real)

| asset | reported missing dependency | disposition |
|---|---|---|
| `ph_nimitta` | `bo_pratijna` | **FALSE POSITIVE.** `dag_edge_guard.py`'s `_reads()` regex scans raw source text, including Python **comments**, for `FROM|JOIN` without stripping `#`-prefixed lines. It matched English prose "from bodha_pratijna + ka_yojaka + AV-transit data" in a comment at `ph_nimitta.py:506`. Direct inspection of `ph_nimitta.py` and `services/ph_nimitta/engine.py` shows no actual SQL reading `bodha_pratijna` — `pratijna_grade`/`pratijna_status`/`event_class_id` are hardcoded JL-009 placeholder defaults, not queried. Not a rebuild blocker; the guard tool itself has a comment-stripping gap worth fixing (filed as a MINOR finding against ph_nimitta in the register). |

### 2.3 L0-bedrock guard-exempted edges (documentation-accuracy gaps only, NOT scheduling bugs)

`dag_edge_guard.py` deliberately exempts `bg_*`/`brahma_*`-prefixed tables from HARD gating, since L0 is a chart-independent singleton built once and gated separately. The following writers read L0 bedrock tables without declaring the corresponding `bg_*` asset in `depends_on`. These violate the derivation-ledger spirit of CLAUDE.md §I B.3 but are **not** live scheduling-correctness bugs:

| asset | undeclared L0 dependency | evidence |
|---|---|---|
| `mi_kula` | `bg_class_priors` | `mi_kula.py:55` — `FROM brahma_class_priors`. `depends_on=[bg_rules]` only. **This is the one prior-flagged example that still reproduces** (of the task's 3 named prior examples, only this one reproduces as a live runtime read). |
| `bo_pratijna` | `bg_ghatana` | `bo_pratijna.py:60` — `FROM brahma_event_ontology`. `depends_on=[bo_laksana, bo_sangati]`. |
| `ka_yojaka` | `bg_ghatana` | `ka_yojaka.py:68,82` — `JOIN brahma_event_ontology beo USING (event_class_id)`. |
| `ka_avadhi` | `bg_ghatana` | `ka_avadhi.py:78` — `JOIN brahma_event_ontology beo USING (event_class_id)`. `depends_on=[ka_yojaka, bo_pratijna]`. |
| `mi_pramana` | `bg_ghatana` | `mi_pramana.py:69` — `SELECT event_class_id, base_rate FROM brahma_event_ontology`. `depends_on=[mi_bhavisya, mi_jivanaghatana]`. |
| `mi_pramana` | `bg_formula_constants` | `mi_pramana.py:51` — `SELECT value_jsonb FROM brahma_formula_constants`. |
| `mi_jivanaghatana` | `bg_ghatana` | `mi_jivanaghatana.py:137` — `SELECT event_class_id FROM brahma_event_ontology`. `depends_on=[]`. |
| `ph_muhurta` | `bg_ghatana` | `ph_muhurta.py:431-455` — `FROM brahma_activity_ontology` (comment: "BA-P5B EXT: load brahma_activity_ontology"). Migration 388's own description says bg_ghatana "governs L4 ph_nimitta and ph_muhurta," confirming intent, just not wired into `depends_on`. |
| `mi_pariksha` | `bg_formula_constants` | `mi_pariksha.py:56` — `SELECT value_jsonb FROM brahma_formula_constants`. `depends_on=[mi_pramana, mi_kula]`. |
| `mi_gunanaka` | `bg_formula_constants` | `mi_gunanaka.py:49` — `SELECT constant_id, value_jsonb FROM brahma_formula_constants`. `depends_on=[mi_pramana, mi_kula]`. |
| `bo_upaya` | `bg_remedies` | `bo_upaya.py:340` — `FROM brahma_remedy_corpus`. `depends_on=[bo_laksana, bo_sangati, ga_strength, ga_structural, ga_positions, ga_sensitive]`. |

**Prior-flagged examples that did NOT reproduce:** `bo_laksana`/`bg_class_priors` — `bo_laksana.py:935-941` hardcodes `class_prior` to 1.0 pending a documented future optimization pass; it does not read `brahma_class_priors` at runtime at all. `ph_nimitta`/`bg_ghatana` — no SQL reference to `brahma_event_ontology` found anywhere in `ph_nimitta.py` or its service. Neither is a current blocker.

---

## 3. Resolve-plan simulation findings (`resolveBuildPlan` / `plan.ts`)

- **FROZEN-orchestrator-contract conformance:** No violations found. Every one of the 91 named assets resolves to a `@register('<asset_id>')` `WriterBase` subclass (directly, or via a documented thin shim importing the real writer from `services/<asset>/writer.py` for `ka_gochara`, `ka_tulana`, `ka_dasha_kala`, `ka_muhurta_seva`, `ph_rectification`). None call `ctx.db_conn.commit()`/`close()`. None write `asset_throughput` directly. `bg_*` (L0) writers correctly omit `ctx.config` chart_id access (chart-agnostic global scope); per-chart writers correctly source `chart_id` from `ctx.config`.
- **has_writer flag correctness:** All 87 real `@register()`'d writers have `has_writer=true` in the live DB. The 4 legitimate sub-registrations/service-probes (`bg_ephemeris_engine`, `bg_panchanga`, `bg_transit_engine`, `bg_nakshatra_medical`) correctly have `has_writer=false` and are explicitly whitelisted in `runner.py`'s `_WRITER_SUBASSET_IDS` / migration 370's documented exclusion. No writer-gap risk.
- **`resolveBuildPlan` (plan.ts) logic:** Correct by inspection. Global scope enumerates all `has_writer=true, is_active=true` non-brahmagyan assets — L0 is deliberately excluded from global scope per native ruling (2026-06-26), enforced in `runs/route.ts`'s `planRegistry` filter; this is an intentional design choice, not a defect. Layer scope correctly separates intra-layer (DAG-ordered) vs. cross-layer (pre-flight-gated) dependencies. `FORBIDDEN_L0` and `ALL_LIT` gates behave as documented/tested.
- **Conclusion:** Once the 3 HARD `depends_on` gaps (§2.1) are fixed, global scope + all 6 layers would be REBUILD-READY on resolve-plan logic alone. The resolve-plan simulator itself has no defects.

---

## 4. REBUILD-READY verdict

### Global

**REBUILD-READY: NO.**

`dag_edge_guard.py` — the project's own CI edge-completeness gate — currently exits 1 with 3 confirmed real HARD violations (a 4th, `ph_nimitta`, is a tooling false positive, see §2.2). Any full "click Build" rebuild run today would legally allow the wave-parallel scheduler to dispatch `ka_taranga`, `ka_yojaka`, and `mi_darshana` before their true upstream (`ka_sangam` / `bo_pratijna`) is lit, in violation of the derivation-ledger guarantee the orchestrator is supposed to enforce.

### Per-layer

| layer | rebuild_ready | blockers |
|---|---|---|
| L0 Brahmagyan | **YES** | none |
| L1 Gaṇita | **YES** | none |
| L2 Bodha | **YES** | none (the `bo_pratijna`/`bg_ghatana` and `bo_upaya`/`bg_remedies` gaps are L0-bedrock documentation-accuracy items, not scheduling bugs) |
| L3 Kāla | **NO** | `ka_taranga` missing `ka_sangam` in `depends_on`; `ka_yojaka` missing `bo_pratijna` in `depends_on` |
| L4 Phala | **YES** | none (the `ph_muhurta`/`bg_ghatana` gap is L0-bedrock documentation-accuracy only; the `ph_nimitta` guard hit is a confirmed tooling false positive) |
| L5 Mīmāṃsā | **NO** | `mi_darshana` missing `bo_pratijna` in `depends_on` (cross-layer L2→L5 gap) |

### Exact blockers (must fix before REBUILD-READY = global YES)

1. Add `ka_sangam` to `ka_taranga.depends_on` (asset_registry migration).
2. Add `bo_pratijna` to `ka_yojaka.depends_on` (asset_registry migration).
3. Add `bo_pratijna` to `mi_darshana.depends_on` (asset_registry migration).
4. Re-run `python -m pipeline.orchestrator.dag_edge_guard` after the migration to confirm exit 0.

None of these three fixes were applied this session (see `BA_AUDIT_FIX_PLAN_v1_0.md` — they are registry/DAG changes distinct from the 4 findings that were in scope for the Fix phase). They remain open BLOCKERS.

### Non-blocking but worth a follow-up migration (documentation-accuracy, §2.3 list)

11 additional `depends_on` gaps against L0-bedrock tables (`bg_ghatana`, `bg_formula_constants`, `bg_remedies`, `bg_class_priors`) are guard-exempted and do not block rebuild-readiness, but leaving them undeclared violates the derivation-ledger spirit of CLAUDE.md §I B.3. Recommend a single follow-up migration to backfill all 11 declared edges (including `mi_kula`→`bg_class_priors`, the one reproducing prior-flagged example) for audit-trail completeness, independent of and lower priority than the 3 HARD blockers above.

### Tooling defect to file separately

`dag_edge_guard.py`'s `_reads()` should strip `#`-prefixed comment lines before regex-matching `FROM|JOIN`, to eliminate the `ph_nimitta` class of false positive in future audits.

See `BA_AUDIT_FIX_PLAN_v1_0.md` for prioritization and native-judgment items.
