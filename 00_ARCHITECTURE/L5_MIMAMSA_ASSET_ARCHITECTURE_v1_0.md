---
artifact: L5_MIMAMSA_ASSET_ARCHITECTURE_v1_0.md
canonical_id: L5_MIMAMSA_ASSET_ARCHITECTURE
version: 1.0
status: DRAFT — the corrected, complete L5 asset structure (10 assets), the table-ownership map, the DAG, the registry/orchestrator wiring spec
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The authoritative asset architecture for L5 Mīmāṃsā after the pre-build structural review. Resolves the
  three structural findings: (1) zero services → add 2; (2) new design tables uncatalogued → fold the
  natural sub-tables, promote the significantly-different ones to their own assets; (3) mi_bhavisya
  depends_on wrong → re-point at phala_*. Result: 8 data assets + 2 services = 10. Includes the table-
  ownership map, the corrected DAG, upstream-leverage map, and the registry-seed + orchestrator wiring spec.
native_decisions_2026_06_22:
  - "Add 2 service assets (serve-time apply + journal/re-sync), mirroring L3's ka_* service pattern"
  - "Fold natural sub-tables into existing assets; PROMOTE significantly-different tables to their own assets (native: 'you take the call')"
  - "Cowork call: promote overlay tables (mi_adhilepa) + signal-family registry (mi_kula); fold bundle/scorecard/preference"
supersedes_partial: L5_MIMAMSA_CAMPAIGN_PLAN_v1_0.md §3 (6-asset list) — superseded by the 10-asset structure here
depends_on_artifacts:
  - L5_MIMAMSA_CAMPAIGN_PLAN · LEARNING_PROPAGATION · CONTRIBUTION_CONTROL · ELEVATION · CALIBRATION_COMPARISON_MODEL
  - asset_registry_seed.ts (the live registry) · ORCHESTRATOR_CONVERGENCE_CLOSE §2 (frozen contract)
  - L3 ka_* service pattern (the precedent for service assets)
---

# L5 Mīmāṃsā — Corrected Asset Architecture

> Pre-build structural review outcome. The design was leveraging the right upstream assets and had the
> right 6 core assets — but had **zero services** (the upper layers use them), and the new tables we
> designed weren't catalogued. This locks the corrected structure: **10 assets total.**

---

## §1 — The three findings this resolves

| # | finding | resolution |
|---|---|---|
| F1 | **Zero services** — all 6 L5 assets were `postgres_table`; but serve-time apply + the journal behave like callable/triggered services (L3 models these as `ka_*` services). | Add **2 service assets**: `mi_seva` (serve-time apply) + `mi_abhilekha` (journal/re-sync). |
| F2 | **New design tables uncatalogued** — overlay tables, family registry, preference store, bundle/scorecard not in the catalog. | **Fold** natural sub-tables; **promote** the significantly-different ones (overlays → `mi_adhilepa`; family registry → `mi_kula`). |
| F3 | **`mi_bhavisya` depends_on wrong** — points at `bo_laksana, ka_kalasutra`, not the `phala_*` it scores. | Re-point at `phala_pramana` (+ `phala_anchors`). |

**Fold-or-promote test applied:** *is this table a different KIND of thing with its own lifecycle and
consumers, or just more storage for an existing asset's job?*
- **Folded** (natural sub-tables): bundle + scorecard (the prediction & its result), preference store
  (serve-time config).
- **Promoted** (significantly different): overlay/adjustment tables (the reverse-channel output that
  L1–L4 read back; the two-key-locked, safety-critical surface) → `mi_adhilepa`; the signal-family
  registry (the controllable tier-tagged matrix + negative-control battery; governs what may influence
  at all) → `mi_kula`. These deserve their own cockpit visibility + integrity checks.

---

## §2 — The 10 assets (8 data + 2 service)

| # | asset_id | sanskrit gloss | kind | scope | owns (tables) | role |
|---|---|---|---|---|---|---|
| 1 | `mi_jivanaghatana` | Jīvanaghaṭanā (life events) | data | global | `life_events` (+ held-out/provenance view) | clean-evidence vault + leakage firewall |
| 2 | `mi_bhavisya` | Bhaviṣya (predictions) | data | per_chart | `mimamsa_predictions` + **frozen-bundle** + **manifestation_set** tables | prediction registry (full frozen bundle) |
| 3 | `mi_pramana` | Pramāṇa (proof) | data | per_chart | `mimamsa_calibration` + **scorecard** tables | matcher + multi-dimensional scorecard + reliability curves |
| 4 | `mi_kula` ⭐NEW | Kula (family/lineage) | data | global | `mimamsa_signal_families` + tier/citation tables | the controllable signal-family registry + negative-control battery |
| 5 | `mi_gunanaka` | Guṇānaka (multipliers) | data | per_chart | `mimamsa_multipliers` (learned weights) | learned-weight register (LL.1 + LL.2–8 structure) |
| 6 | `mi_adhilepa` ⭐NEW | Adhilepa (overlay) | data | per_chart | the **4 overlay tables** (`mimamsa_fact/signal/convergence/anchor_adjustment`) | the bounded, two-key-locked reverse-channel overlay surface |
| 7 | `mi_pariksha` | Parīkṣā (examination) | data | per_chart | `mimamsa_qa_eval` + attribution tables | per-dimension + per-channel attribution; runs the neg-control harness |
| 8 | `mi_vistara` | Vistāra (export log) | data | global | `mimamsa_export_log` | export-integrity ledger |
| 9 | `mi_seva` ⭐NEW | Sevā (service) | **service** | per_chart | (no build table; reads overlay+base) owns `mimamsa_preferences` | **serve-time apply**: effective-value resolve + contribution-control toggles + transit-current binding |
| 10 | `mi_abhilekha` ⭐NEW | Abhilekha (record/journal) | **service** | per_chart | (triggered) `mimamsa_journal` | **journal + re-sync**: journal ingestion + due-sweep + debounced LEL-update recompute |

⭐NEW = added/promoted in this review (4 new: 2 promoted data + 2 services). Sanskrit names are
proposals — native may rename; the structure is the decision.

> **Count:** 8 data + 2 service = **10 assets** — matching the granularity of L3 (14) and L4 (10), and
> keeping the safety-critical surfaces (overlay, family registry) independently visible + governed.

---

## §3 — The corrected DAG (build order)

```
            L4 (sealed)         L1 (held-out)        L0 (classical, read-only)
       phala_pramana/anchors      life_events            bg_rules/significations
              │                       │                         │
              ▼                       ▼                         │
   mi_kula (family registry) ◄────────┼─────────────────────────┘  (families + citations + neg-controls)
              │                       │
              ▼                       ▼
        mi_bhavisya ◄─────────── mi_jivanaghatana
        (frozen bundle +              (clean evidence)
         manifestation_set)           │
              │                       │
              └──────────┬────────────┘
                         ▼
                    mi_pramana  (deterministic match + scorecard)
                         │
                         ▼
                    mi_gunanaka  (learned weights)
                         │
                         ▼
                    mi_adhilepa  (overlays — bounded, two-key-locked) ──► [read back by L1–L4 at serve]
                         │
            ┌────────────┼─────────────┐
            ▼                          ▼
       mi_pariksha                mi_vistara
       (attribution +             (export ledger)
        neg-control harness)

   SERVICES (callable/triggered, not in the build DAG spine):
     mi_seva       — serve-time: applies mi_adhilepa overlay + toggles, per query
     mi_abhilekha  — triggered: journal ingest → grows life_events → re-sync (mi_bhavisya→…→mi_adhilepa)
```

**Build-DAG `depends_on` (corrected, for the seed):**
```
mi_jivanaghatana : []                                   (global; LEL load)
mi_kula          : [bg_rules]                            (global; families + citations + neg-controls)   [NEW]
mi_bhavisya      : [phala_pramana, phala_anchors, mi_kula, mi_jivanaghatana]   ← FIXED (was bo_laksana,ka_kalasutra)
mi_pramana       : [mi_bhavisya, mi_jivanaghatana]
mi_gunanaka      : [mi_pramana]
mi_adhilepa      : [mi_gunanaka]                         (the overlay output)   [NEW]
mi_pariksha      : [mi_pramana, mi_kula]                 (attribution + neg-control harness)
mi_vistara       : []                                    (export ledger)
mi_seva          : [mi_adhilepa]  (service; serve-time)  [NEW]
mi_abhilekha     : [mi_bhavisya]  (service; triggered)   [NEW]
```
> All `depends_on` are PROPOSED — reconcile against the live registry + sealed `phala_pramana` in P1/P2,
> then native-ratify.

---

## §4 — Upstream leverage map (confirmed — the design DOES use the necessary assets)

| layer | assets L5 leverages | how |
|---|---|---|
| **L4 Phala** | `phala_pramana` (primary), `phala_anchors`, `phala_phaladesa` | the predictions L5 scores; the falsifier seam + reverse-channel return path |
| **L3 Kāla** | `kala_convergence`, dāśā timeline; **services** `ka_dasha_kala`/`ka_gochara`/`ka_tulana` | timing context per window; CALL the services (don't re-derive) for transit-current binding |
| **L2 Bodha** | `bodha_msr_signals` (keystone, ~66k), `bodha_signal_embeddings`, `bodha_cdlm_cells`, `bodha_discoveries`, RM | the signal substrate the overlay modulates; the richest latent input |
| **L1 Gaṇita** | `chart_facts`, `chart_dashas`, per-subsystem assets | the fact authority every verdict resolves to |
| **L0 Brahmagyan** | `bg_rules`, significations, `brahma_yoga_catalog`, `bg_texts` | manifestation-set generation + classical citations (READ-ONLY; never modulated) |

**Reuse discipline (inherited L4 D10):** READ-asset → CALL-service → recompute-PyJHora-only-if-absent.
L5 needs ZERO new chart computation — it scores + overlays what exists. The L3 services give L5 its
transit-current binding without re-deriving timing.

---

## §5 — Orchestrator wiring (the contract, applied to all 10)

**Status: contract-correct in design; zero `mi_*` writers exist yet (P4 build work).** Every L5 asset
onboards via the FROZEN contract (`ORCHESTRATOR_CONVERGENCE_CLOSE §2`) — no orchestrator change:

- **8 data assets:** each a `@register('mi_*')` `WriterBase` subclass; `run(ctx)` or
  `plan_substeps`+`run_substep`; `conn = ctx.db_conn` never committed; `rows_inserted`; per-chart
  delete-then-insert idempotency; `count_sql` uses `$1`; imports clean (pkgutil hard-fails otherwise).
- **2 service assets:** registered as `asset_kind: 'service'` / `storage_type: 'service'` (mirroring
  `ka_dasha_kala` etc.) — **callable/triggered, not built in the DAG spine.** `mi_seva` is invoked at
  serve time by the Whole-Chart-Read; `mi_abhilekha` is invoked by the journal/due-sweep triggers.
  Services declare their `depends_on` for catalog lineage but are not part of the click-Build sequential
  pass that materializes tables.
- **Service dir COPY'd** in `platform/python-sidecar/Dockerfile.pipeline` (the silent-hang gotcha).
- **Cockpit `count_sql`** correct + chart-scoped per asset (the L1 trap — stats route reads `count_sql`).

---

## §6 — Registry-seed correction spec (what P3.5 changes in asset_registry_seed.ts)

1. **Fix `mi_bhavisya.depends_on`** → `['phala_pramana','phala_anchors','mi_kula','mi_jivanaghatana']`.
2. **Add 4 new assets:** `mi_kula`, `mi_adhilepa` (data), `mi_seva`, `mi_abhilekha` (service) with
   correct `asset_kind`/`storage_type`/`scope`/`depends_on`/`count_sql`.
3. **Reconcile scope:** calibration/overlay assets are per_chart (not global) — fix `mi_pramana`,
   `mi_gunanaka` to `per_chart`; keep `mi_jivanaghatana`/`mi_kula`/`mi_vistara` global where correct.
4. **Add target tables** for the folded sub-tables under their owning assets (bundle/scorecard under
   `mi_bhavisya`/`mi_pramana`; preferences under `mi_seva`).
5. **DAG edges** added to the dependency table (seed's edge list) for the 4 new assets.
6. **CAPABILITY_MANIFEST + CANONICAL_ARTIFACTS** updated to match (manifest is the tooling source of truth).

---

## §7 — What this changes downstream (consistency sweep)

- `L5_MIMAMSA_CAMPAIGN_PLAN §3` (6-asset list) → **superseded** by this §2 (10 assets); the per-asset
  specs there still hold for the 6 originals.
- `L5_MIMAMSA_MASTER_ACTIVITY_LIST` P3/P4 → add `mi_kula`, `mi_adhilepa` writers + `mi_seva`,
  `mi_abhilekha` services to the build phases.
- `LEARNING_PROPAGATION` overlay tables → now owned by `mi_adhilepa` (was implied under `mi_gunanaka`).
- `ELEVATION` signal-family matrix → now owned by `mi_kula`.
- `CONTRIBUTION_CONTROL` serve-time gates + preference store → now owned by `mi_seva`.

---

*End of L5_MIMAMSA_ASSET_ARCHITECTURE v1.0. The corrected structure: 8 data assets + 2 services = 10.
Folded the natural sub-tables (bundle/scorecard/preferences); promoted the significantly-different ones
(overlays → mi_adhilepa, family registry → mi_kula); added 2 services (mi_seva serve-time apply,
mi_abhilekha journal/re-sync) mirroring L3's ka_* pattern; fixed mi_bhavisya to depend on phala_*. The
design provably leverages the right upstream assets L0–L4; the orchestrator wiring is contract-correct
and waits only on the P4 build. depends_on/scope are proposals to reconcile + native-ratify in P1/P2.*
