---
artifact: L5_BUILD_READINESS_AUDIT_v1_0.md
canonical_id: L5_BUILD_READINESS_AUDIT
version: 1.0
status: CURRENT — code-grounded audit of the L5 "press Build" path; lists every must-fix before a clean build
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  A thorough, CODE-GROUNDED audit of whether pressing Build for L5 Mīmāṃsā will run all assets through the
  DAG without interruption. Verified against the live orchestrator (asset_runner.py, writers/__init__.py)
  and the live asset_registry_seed.ts — not the design docs. Surfaces BLOCKERS that would break the build
  today and the exact fixes. Honest scope: the mi_* writers don't exist yet (P4), so this audits the
  BUILD-TIME CONTRACT (registry, DAG, conformance, known traps), which is what prevents interruption when
  the writers are built.
---

# L5 Build-Readiness Audit — "Will Press-Build Run Clean?"

> Verified against live code. Verdict: **NOT build-ready as the registry stands today** — 2 confirmed
> blockers + several must-fixes. None are hard; all are fixable in the P3 registry-seed step. This audit
> is the checklist that guarantees a clean, uninterrupted build once applied.

## §1 — How the build path actually works (verified)

From `platform/python-sidecar/pipeline/orchestrator/asset_runner.py` + `writers/__init__.py`:
1. **Registry-driven, no hardcoded layers** — the runner reads `asset_registry` and resolves the DAG from
   the `depends_on` Postgres `text[]` via a **recursive closure** (`compute_downstream_closure`).
2. **Writer discovery is pkgutil-based** (`writers/__init__.py` `discover_all()` walks the package and
   imports every module) — and **HARD-FAILS on any import error in the package** (one bad import breaks
   discovery for ALL writers).
3. **`get_writer(asset_id)`** returns the `@register('<asset_id>')` class or **None**. `asset_runner.py`
   line 524: `if get_writer(asset_id) is None:` — an asset with no registered writer cannot run.
4. **`@register` raises on duplicate asset_id** (`writers/__init__.py` line 177) — a collision hard-fails.
5. Each writer runs on `ctx.db_conn` (orchestrator owns the txn + per-substep savepoint); the orchestrator
   is the sole `asset_throughput` writer.

**Implication:** the build is only as correct as (a) the registry rows + their `depends_on` edges, and
(b) every `mi_*` writer existing, importing clean, and registering under the exact asset_id.

## §2 — 🔴 BLOCKER 1: dependency edges reference TABLE NAMES, not ASSET IDs

**The single most important finding.** `depends_on` must contain **asset_ids**, but the spec pack's
proposed edges used **table names**. In the live registry `asset_id != target_table`:

| spec wrote (table) | correct asset_id | proof (seed) |
|---|---|---|
| `phala_pramana` | **`ph_pramana`** | asset_id `ph_pramana` → target_table `phala_pramana` (line 1549/1555) |
| `phala_anchors` | **`ph_nimitta`** | asset_id `ph_nimitta` → target_table `phala_anchors` (line 1441/1447) |
| `phala_phaladesa` | **`ph_phaladesa`** | asset_id `ph_phaladesa` → target_table `phala_phaladesa` (matches) |

If `mi_bhavisya.depends_on = ['phala_pramana', ...]` ships, the recursive DAG closure finds **no such
asset_id** → the edge is silently dead → `mi_bhavisya` never triggers off L4, OR the build ordering is
wrong. **Fix:** every L5 `depends_on` must use asset_ids:
```
mi_bhavisya.depends_on = ['ph_pramana', 'ph_nimitta', 'ph_phaladesa', 'mi_kula', 'mi_jivanaghatana']
```
(Apply the same asset_id-not-table discipline to any L2/L3 edge: e.g. `bodha_msr_signals` is a table —
its asset is `bo_laksana`; `kala_convergence` table → asset `ka_sangam`.) **Every spec's §8 depends_on is
re-stated in §6 of this audit with verified asset_ids.**

## §3 — 🔴 BLOCKER 2: the registry is missing 6 of the 13 assets + the dependency bug is live

- Live seed has only the **original 6** `mi_*` rows. The 4 new assets (`mi_kula`, `mi_adhilepa`,
  `mi_seva`, `mi_abhilekha`) + the 2 insight assets (`mi_sambandha`, `mi_darshana`) are **NOT registered**.
  A build today would run 6 assets and silently omit the other 7 capabilities.
- `mi_bhavisya.depends_on` is still the **buggy** `['bo_laksana', 'ka_kalasutra']` (line 1635) — it does
  NOT depend on L4 at all. A build today would calibrate against the wrong upstream.
- **Fix (P3.5):** add all new rows + correct `mi_bhavisya` (see §6 for the full verified registry block).

## §4 — 🟡 MUST-FIX checklist (each would interrupt or corrupt the build)

| # | item | why it breaks the build | fix |
|---|---|---|---|
| M1 | **count_sql per asset** (chart-scoped, `$1`) | the L1 trap: stats route reads `count_sql`; wrong/missing → asset shows NOT MIGRATED post-build even if rows wrote | every per_chart asset: `... WHERE chart_id = $1`; global: no `$1` |
| M2 | **scope correctness** | a per-chart asset marked `global` runs in the global pass (wrong lock/ordering) | `mi_pramana`/`mi_gunanaka`/`mi_adhilepa`/`mi_sambandha`/`mi_darshana`/`mi_bhavisya`/`mi_pariksha` = `per_chart`; `mi_jivanaghatana`/`mi_kula`/`mi_vistara` = `global` (confirm) |
| M3 | **services not in build-DAG spine** | `mi_seva`/`mi_abhilekha` are `asset_kind: service` — must NOT be in the click-Build sequential materialize pass, or the build waits on a service that has no table | register as `asset_kind:'service'`,`storage_type:'service'` (like `ka_dasha_kala`); declare depends_on for lineage only |
| M4 | **every mi_* writer imports clean** | pkgutil `discover_all()` HARD-FAILS the whole package on ONE bad import → NO writer runs (not just mi_*) | each writer module must import with zero errors; CI test `discover_all()` succeeds |
| M5 | **no duplicate @register** | `@register` raises on duplicate asset_id → discovery crash | each asset_id registered exactly once |
| M6 | **Dockerfile.pipeline COPYs any new top-level dir** | the silent-hang gotcha (bit bo_pramana_mapa + every ka_/ph_) — a service/helper dir not COPY'd → writer import fails in prod only | if L5 adds a top-level dir (e.g. `mimamsa/`), add the COPY line |
| M7 | **migrations create every table before its writer runs** | a writer inserting into a non-existent table errors mid-build | P3 migrations (6 core + 4 overlay + family/pref/bundle/scorecard/grammar/insight/journal/embeddings) applied BEFORE build |
| M8 | **target_table exists + matches** | `asset_registry.target_table` pointing at a missing table → stats/health break | each new asset's `target_table` created by a migration |
| M9 | **no cycle in the DAG** | a dependency cycle → topological resolution never terminates | verified acyclic in §5 |
| M10 | **upstream assets are BUILT for the chart** | L5 depends on L1–L4 being present for `482012f1`; building L5 on an un-built/again-mid-rebuild chart errors | P0 gate: L4 sealed + L3 rebuild done before L5 build (already enforced) |
| M11 | **pgvector for mi_darshana embeddings** | `storage_type` mismatch / extension missing → embedding table write fails | `mi_darshana` embeddings table = pgvector; extension present (L2 already uses it) |
| M12 | **service health_probe defined** | service assets without a `health_probe` JSONB show "down" | define probes for `mi_seva`/`mi_abhilekha` (mig pattern from ka_* services) |

## §5 — DAG integrity (verified acyclic, asset-id form)

```
mi_jivanaghatana []                         (global root)
mi_kula          [bg_rules]                 (global root)        [NEW]
mi_bhavisya      [ph_pramana, ph_nimitta, ph_phaladesa, mi_kula, mi_jivanaghatana]   ← FIXED
mi_pramana       [mi_bhavisya, mi_jivanaghatana]
mi_gunanaka      [mi_pramana]
mi_adhilepa      [mi_gunanaka]              [NEW]
mi_pariksha      [mi_pramana, mi_kula]
mi_sambandha     [mi_pramana, mi_pariksha]  [NEW]
mi_darshana      [mi_pramana, mi_adhilepa, mi_sambandha, mi_pariksha, mi_gunanaka, mi_kula, mi_jivanaghatana]   [NEW]
mi_vistara       []                         (global; operational)
-- services (NOT in build spine):
mi_seva          [mi_adhilepa]   (service, serve-time)   [NEW]
mi_abhilekha     [mi_bhavisya]   (service, triggered)    [NEW]
```
**Topological order (one valid build sequence):** mi_jivanaghatana, mi_kula → mi_bhavisya → mi_pramana →
mi_gunanaka, mi_pariksha → mi_adhilepa, mi_sambandha → mi_darshana → (mi_vistara any time). **No cycle.**
All upstream asset_ids (`ph_pramana`, `ph_nimitta`, `ph_phaladesa`, `bg_rules`) exist in the registry ✅.

## §6 — The verified registry-seed block to apply in P3.5

For each L5 asset, P3.5 sets: `asset_id`, `layer:'mimamsa'`, `sanskrit_name`/`english_name`, `asset_kind`
(`data`|`service`), `storage_type` (`postgres_table`|`pgvector`|`service`), `target_table`, **`count_sql`
(chart-scoped `$1` for per_chart)**, `scope`, **`depends_on` in ASSET-ID form (§5)**, `is_active:true`,
and (services) `health_probe`. Plus add every new table to migrations (M7) and the **DAG edge list** the
seed maintains. Then update **CAPABILITY_MANIFEST.json** (the tooling source of truth) to match.

## §7 — Pre-build verification gate (run BEFORE pressing Build)

A deterministic pre-flight that prevents interruption:
1. **Registry resolves:** every `mi_*.depends_on` entry exists as an `asset_id` in `asset_registry`
   (the asset-id-not-table check) — query, assert zero dangling edges.
2. **Acyclic:** the recursive closure terminates for every `mi_*` (no cycle).
3. **Writers present + clean:** `discover_all()` succeeds; `get_writer('mi_*')` is not None for all 10
   data assets + service handlers registered.
4. **Tables exist:** every `target_table` (and overlay/bundle/scorecard/grammar/insight/journal/embedding
   table) exists in prod (migrations applied).
5. **count_sql valid:** each runs without error + returns an int, chart-scoped.
6. **Upstream built:** `ph_pramana`/`ph_nimitta`/etc. have `asset_throughput` rows for `482012f1`.
7. **Services excluded from spine:** `mi_seva`/`mi_abhilekha` are `asset_kind:service` (not in the
   sequential pass).
8. **pgvector + extension** present for `mi_darshana`.
This gate is itself an L5 deliverable (extends the cockpit's existing pre-build checks).

## §8 — Verdict + what's NOT yet checkable

**Build-ready when §2 + §3 blockers fixed and the §4 must-fixes applied in P3 — verified clean by the §7
pre-flight.** Today: NOT ready (table-name edges, missing assets, live dependency bug). All fixes are P3
registry/migration work; none require an orchestrator change (the freeze holds).

**Not checkable until P4 (writers exist):** runtime behavior of each writer, actual `count_sql` returns,
real import cleanliness, savepoint behavior. These are covered by the §7 pre-flight + the P6 seal gates
(reproducibility, OFF==baseline, no-LLM, negative-controls, degenerate-distribution) which run against the
live build. The honest statement: **this audit guarantees the build-time CONTRACT is sound; the P6 gates
guarantee the runtime is sound.** Both must pass before L5 seals.

---

*End of L5_BUILD_READINESS_AUDIT v1.0. Two confirmed blockers (table-name-vs-asset-id edges; 6 missing
assets + live mi_bhavisya dependency bug) + 12 must-fixes, all P3 registry/migration work, none needing an
orchestrator change. The §5 DAG is verified acyclic with real asset_ids; §6 is the seed block to apply;
§7 is the pre-build pre-flight that guarantees press-Build runs uninterrupted. Apply these and the build
runs clean.*
