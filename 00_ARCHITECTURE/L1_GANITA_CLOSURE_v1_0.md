---
artifact: L1_GANITA_CLOSURE_v1_0.md
canonical_id: L1_GANITA_CLOSURE
version: 1.0
status: CURRENT
date_sealed: 2026-06-12
seals:
  - L1-GANITA-CLOSURE-PASS (Phases A–D; Phase E pending operator E2E)
  - L1_GANITA_BUILD_CLOSE_v1_0.md (v1.3)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md (v1.0)
  - L1_CLOSURE_VERIFICATION_v1_0.md (v1.0)
main_head_at_seal: 77cef8acb32a8c829044a06b47a292058d742e8d
prs_in_scope:
  - "#254 (orchestrator Phase 1 — deployment foundation)"
  - "#255 (orchestrator Phase 2 — contract freeze + sub-steps)"
  - "#256 (orchestrator Phase 3 — 9 GA writers converged)"
  - "#257 (orchestrator Phase 3B — per-chart generalization)"
  - "#258 (orchestrator Phase 4 — probe DAG + migration 223)"
  - "#259 (orchestrator Phase 6 — convergence close)"
  - "#260 (closure Phase B — migration 224 id-naming standardization)"
  - "#261 (closure Phase C — governance seal consistency)"
  - "#262 (closure Phase D — hygiene, formula annotations)"
  - "#263 (build fix — migration 225 drops orphaned asset_throughput_pkey)"
  - "#264 (cockpit fix — asset.substep SSE live progress)"
phase_e_status: GATED — awaiting operator E2E confirmation (Abhinandan Mohanty 1c826d5a)
changelog:
  - v1.0 (2026-06-12): initial seal. Phase E gated; all other phases COMPLETE.
---

# L1 Gaṇita — Closure Record v1.0

## §1 — Verdict

The L1 Gaṇita layer is **CLOSED**. All 10 assets (GA3–GA10 + 1 service) are:

- **Data-complete** for the canonical native (chart_id `482012f1-710e-4a25-994a-93821f5871aa`) — FORENSIC 7/7 PASS, cockpit-validated row counts, all states `lit`.
- **Per-chart general** — the orchestrator builds any chart (not just the native); non-native birth params fetched from `public.charts`; native FORENSIC assertions guarded.
- **Orchestrator-native** — all 9 data writers are `@register` `WriterBase` subclasses on the FROZEN contract; no orchestrator change is needed to build L2.
- **ID-naming standardized** — all placeholder L2–L5 asset_ids use the canonical underscore form (`bo_*`, `ka_*`, `ph_*`, `mi_*`); migration 224 applied.
- **Schema-clean** — migration 225 drops the orphaned `asset_throughput_pkey` constraint that was blocking non-native builds.
- **Cockpit-faithful** — real-time `asset.substep` SSE events consumed; live row count + substep progress shown during builds.

The orchestrator is the build engine. L2 Bodha writers onboard by conforming to the frozen contract — no orchestrator edits required.

---

## §2 — Layer state snapshot

### §2.1 — Asset registry (L1 Gaṇita)

| asset_id | layer | scope | has_substeps | target_table | target_floor |
|---|---|---|---|---|---|
| `ga_positions` | L1 | per_chart | false | `chart_facts` | 100 |
| `ga_strength` | L1 | per_chart | false | `chart_facts` | 50 |
| `ga_vargas` | L1 | per_chart | true (5) | `chart_divisionals` | 1000 |
| `ga_panchanga` | L1 | per_chart | false | `chart_facts` | 10 |
| `ga_sensitive` | L1 | per_chart | false | `chart_facts` | 50 |
| `ga_dashas` | L1 | per_chart | true (36) | `chart_dashas` | 1000 |
| `ga_structural` | L1 | per_chart | false | `chart_facts` | 200 |
| `ga_sade_sati` | L1 | per_chart | false | `chart_facts` | 1 |
| `ga_tajaka` | L1 | per_chart | false | `l1_tajik_varsha_year_lords` | 1 |
| `ga_chart_service` | L1 | per_chart | false | (service; no direct table) | — |

### §2.2 — DAG (depends_on edges, from migration 223)

```
ga_positions  (root)
  ├── ga_strength
  ├── ga_vargas
  ├── ga_panchanga
  ├── ga_sensitive  (also depends on bg_reference)
  ├── ga_dashas
  │     └── ga_tajaka  (leaf; also depends on ga_positions)
  └── ga_structural  (synthesis node — all Level-1 assets + ga_positions)
            └── ga_sade_sati  (last in temporal order)
```

### §2.3 — Canonical row counts (native chart, cockpit-validated)

| asset_id | table | rows | state |
|---|---|---|---|
| `ga_positions` | `chart_facts` | 27,554 | lit |
| `ga_strength` | `chart_facts` | (included in ga_positions total) | lit |
| `ga_panchanga` | `chart_facts` | (included in ga_positions total) | lit |
| `ga_sensitive` | `chart_facts` | (included in ga_positions total) | lit |
| `ga_structural` | `chart_facts` | 6,075 | lit |
| `ga_sade_sati` | `chart_facts` | (included above) | lit |
| `ga_vargas` | `chart_divisionals` | 21,635 | lit |
| `ga_dashas` | `chart_dashas` | 536,471 | lit |
| `ga_tajaka` | `l1_tajik_varsha_year_lords` | 240 | lit |
| **L1 Gaṇita total** | | **≈ 585,975** | all lit |

*(chart_facts total of 27,554 spans ga_positions + ga_strength + ga_panchanga + ga_sensitive + ga_structural + ga_sade_sati writes; each writer appends to the same table.)*

---

## §3 — Closure pass deliverables (Phases A–F)

| Phase | Title | Deliverable | Status |
|---|---|---|---|
| A | Read-only verifications | `L1_CLOSURE_VERIFICATION_v1_0.md` — 4 checks PASS | COMPLETE |
| B | ID naming standardization | Migration 224 (23 renames) + seed parity; PR #260 | COMPLETE |
| C | Governance seal consistency | `L1_GANITA_BUILD_CLOSE` v1.2→v1.3; `CURRENT_STATE` v5.72→v5.73; PR #261 | COMPLETE |
| D | Hygiene | STALE_FORMULA annotations (ga_vargas, ga_strength); branch pruning; PR #262 | COMPLETE |
| E | Non-native E2E teardown | Operator E2E: Abhinandan Mohanty (`1c826d5a`) Gaṇita build PASS → test data cleanup | **GATED** |
| F | Closure seal | This document + `CURRENT_STATE` v5.74; PR #265 | COMPLETE (Phase E pending) |

**Build fixes shipped concurrently:**
- PR #263 (migration 225): drops orphaned `asset_throughput_pkey`; unblocks all non-native Gaṇita builds.
- PR #264: wires `asset.substep` SSE into cockpit; live row count + substep progress during builds.

---

## §4 — Phase E runbook (operator; do before marking E COMPLETE)

**Precondition:** Migration 225 applied to production DB.

1. Navigate to Abhinandan Mohanty's chart (`chart_id = 1c826d5a-41cb-4450-b4dc-59d440e5f75a`).
2. Confirm `asset_throughput` has no `lit` GA rows for `1c826d5a` (clean slate — prior stuck run `89f5cb5b` was `failed` or cleaned by migration 225 reaper).
3. Trigger Gaṇita build: cockpit → Build → Layer: ganita.
4. Verify: all 10 GA assets reach `lit`; `build_runs.state = 'completed'`; `ga_dashas` shows `asset.substep` events in cockpit.
5. Confirm no FORENSIC halt (non-native → native assertions not asserted).
6. Report back: "Phase E E2E PASSED" with chart_id `1c826d5a`.

**After E2E confirmation:**
7. Delete test chart rows (per-chart tables): `DELETE FROM chart_facts WHERE chart_id = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'` + same on `chart_divisionals`, `chart_dashas`, `l1_tajik_varsha_year_lords`, `asset_throughput`.
8. Delete the client profile row if it was created solely for this test.
9. Update this document: `phase_e_status → COMPLETE`, version 1.0 → 1.1.

---

## §5 — FROZEN orchestrator contract (reference)

The contract is defined in `pipeline/orchestrator/writers/__init__.py` and sealed in `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2`. This block is a reference copy — **`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2` is authoritative.**

- `ContextSpec{ asset_id, build_id, db_conn (caller-owned; writer never commits/closes), config{chart_id, birth_params}, dry_run }`
- `WriterResult{ asset_id, rows_inserted, rows_updated, rows_skipped, duration_seconds, notes }`
- `SubStep{ key, label }` — one savepoint-isolated, heartbeated unit; `key` is the writer's idempotency scope.
- `WriterBase`: light writer → `run(ctx)`; heavy writer → `plan_substeps(ctx)` + `run_substep(ctx, step)`.

**If any future layer appears to need a contract change: STOP and raise with the native.** The freeze was a deliberate architectural decision.

---

## §6 — L2-readiness conformance checklist

*(Verbatim from `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §5`. Embed in every L2–L5 writer brief.)*

A writer is orchestrator-native iff **all** hold:

- [ ] **Is a class**, `@register('<asset_id>')`, subclassing `WriterBase`; `asset_id` matches the registry.
- [ ] **Discoverable** — imported by `_auto_discover()` (lives under `pipeline/orchestrator/writers/` or is a thin adapter that does) **and ships in the `brahma-pipeline` job image**.
- [ ] **`run(ctx)`** (light) **or** `plan_substeps(ctx)` + `run_substep(ctx, step)` (heavy: > ~10 min or > a few hundred k rows).
- [ ] **Connection:** uses `ctx.db_conn` exclusively; **never** opens its own, **never** `commit()/rollback()/close()`.
- [ ] **chart_id / birth:** reads `ctx.config['chart_id']` and `ctx.config['birth_params']` (None → its verified default); `ctx.build_id`. **No hard-coded native default in the build path.**
- [ ] **Idempotency:** its own natural-key-scoped `replace_prior_*` on `ctx.db_conn` immediately before INSERT, scoped to the sub-step key; any sub-step safe to re-run.
- [ ] **Telemetry:** writes **nothing** to `asset_throughput`; returns counts in `WriterResult`.
- [ ] **FORENSIC:** any native-anchored assertion is guarded `if chart_id == CANONICAL_CHART_ID`; structural invariants stay unconditional.
- [ ] **dry_run:** honors `ctx.dry_run`.
- [ ] **Registry row** with correct `scope`, `asset_type`, `layer`, **populated `depends_on`** (real edges, not `[]`), `count_sql` + `target_floor`, `sort_order`; `has_substeps=true` if heavy; `rebuild_on_probe_fail=true` + a `health_probe`/`integrity_check_sql` if self-healing.
- [ ] **No orchestrator change required** — if onboarding needs a new `if` in `run_asset`/`runner.py`, the contract was violated; fix the writer, not the orchestrator.

---

## §7 — L2 onboarding contract

### §7.1 — Recommended `depends_on` for bo_* writers

```python
# Minimum — structural synthesis only
depends_on = ['ga_structural']

# With Saturn transit windows
depends_on = ['ga_structural', 'ga_sade_sati']

# Full L1 consumer (incl. annual charts)
depends_on = ['ga_structural', 'ga_sade_sati', 'ga_tajaka']
```

The orchestrator DAG executor resolves transitive dependencies automatically (`ga_structural` pulls in `ga_positions`, `ga_strength`, etc.) — bo_* writers need not enumerate the full chain.

### §7.2 — Epistemic-tiering rule for L2 rows

Every L2 row should carry:

| Row type | `verification_pass_status` | `citation_ref` form |
|---|---|---|
| Hard-fact (directly read from L1, no judgment) | `two_pass_verified` | `<fact_id>` pointing to L1 `chart_facts` row |
| Synthesized / interpreted (multi-factor scoring, narrative) | `documented_approximation` | `<rule_citation>@constituents=[<fact_id1>,...]` |
| Classical-text application (BPHS / Jaimini / KP rule) | `documented_approximation` | classical source + L1 fact_ids activating the rule (also populate `citation_human`) |

Only rows with `verification_pass_status IN ('two_pass_verified', 'documented_approximation')` and non-null `citation_ref` pass the MSR signal-grounding audit.

### §7.3 — MSR-feeding categories available from L1

The following `ga_structural` categories are confirmed populated (6,075 rows, FORENSIC-verified) and available to bo_* writers:

- **Aspects:** `aspect_parashari_given`, `aspect_parashari_received`, `aspect_jaimini`, `aspect_tajik`, `conjunction_within_orb`, `aspect_matrix_summary`
- **Yoga firings:** `yoga_fires`
- **Dispositors:** `graha_dispositor_chain`, `composite_dispositor_strength`, `parivartana_pairs`, `graha_composite_state_classification`
- **Functional classification:** `graha_functional_class_per_ascendant`, `graha_yoga_karaka_flag`
- **Karakatva:** `karakatva_strength_per_significance`, `karaka_house_lord_overlap_flag`
- **Argala:** `argala_natal_matrix`, `virodha_argala_natal_matrix`

Full category list in `L1_CLOSURE_VERIFICATION_v1_0.md §3`.

---

## §8 — What is NOT in L1 (non-blocking residuals)

These items are documented, non-blocking, and tracked in `V1_3_AUDIT_QUEUE_v1_0.md`:

| Item | Description | Tracking ref |
|---|---|---|
| `ga_vargas` formula | `expected_volume_formula` STALE_FORMULA annotation added (actual=21,635, naive formula gives 2,700) | Phase D annotation; CF.V13.x |
| `ga_strength` formula | `expected_volume_formula` STALE_FORMULA annotation added (actual=2,184, naive formula gives 4,950) | Phase D annotation; CF.V13.x |
| `ga_dashas` telemetry | `build_ga_dashas()` legacy entry point has unguarded `_telemetry` call — not reachable on the orchestrator path | L1_CLOSURE_VERIFICATION §4 note |
| `rebuild_on_probe_fail` | No GA asset sets this yet — primitive is wired + tested, ready for first opt-in | R4-1 in ORCHESTRATOR_CONVERGENCE_CLOSE §6 |
| Phase E teardown | Test chart cleanup gated on operator E2E confirmation | §4 above |

---

## §9 — Next arc: L2 Bodha

L1 is closed. The next work is **L2 Bodha** — the interpretive synthesis layer. Every bo_* writer:

1. Embeds the checklist from §6 verbatim.
2. Declares `depends_on` per §7.1.
3. Tags every emitted row per §7.2.
4. Is a `@register` `WriterBase` subclass — no orchestrator edits.

The L2 brief author should reference this document (canonical_id `L1_GANITA_CLOSURE`) as the onboarding contract.
