---
artifact: L4_PHALA_PRE_IMPLEMENTATION_CLOSURE_v1_0.md
canonical_id: L4_PHALA_PRE_IMPLEMENTATION_CLOSURE
version: 1.0
status: DRAFT — the complete structured list of everything to close BEFORE the fully-autonomous swarm launches
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md
grounded_in: code-verified onboarding-path + autonomy-framework mapping (2026-06-21)
role: >
  The pre-implementation closure plan for L4 Phala. Implementation is FULLY AUTONOMOUS — the agentic
  swarm commits, merges, deploys, builds, and populates data with NO human gate. Therefore the prep
  phase must carry ALL human judgment and close everything the swarm cannot discover or decide for
  itself. This document is the exhaustive, structured checklist + the phase sequence to get there.
governing_principle: >
  In a no-human-gate build, the swarm SELF-HEALS at runtime (Tier-1/2 auto-resolve, Vimarśaka
  auto-revert, deep-fix ladder). So prep does NOT need to prevent every bug. Prep must close the
  things the swarm CANNOT do: (a) make design/judgment decisions, (b) verify prod data-plane state,
  (c) author the inputs the Conductor consumes (briefs/queue/kickoff), (d) provision infra/CI/manifest
  surfaces that must be correct BEFORE the swarm can even start, (e) ratify the native-only gates.
---

# L4 Phala — Pre-Implementation Closure Plan v1.0

> **⚠️ AMENDED 2026-06-22 (D47 — fully-autonomous model).** This doc's Gate-F `[OPERATOR]` items
> (apply migs 326–329, CI-green, prod==main, branch, proxy/deps) are NO LONGER human prerequisites —
> they were ABSORBED into the Conductor-run **Phase 0** (the Sthāpati role), per
> `L4_PHALA_AUTONOMOUS_EXECUTION_v2_0.md`. The ONLY human action is now a single kickoff paste. Read
> this doc for the gate STRUCTURE + the closure history; read `L4_PHALA_REMAINING_ACTIVITIES_v2_0.md`
> for the genuinely-final "what's left." Gates A/B/C/D/E are CLOSED; Gate F is absorbed into Phase 0.

> **The reframe.** Because the implementation is autonomous-with-self-healing, the prep gate's job is
> NOT "make the build bug-free." It is: **close every item the swarm cannot close on its own.** Each
> item below is tagged with WHO must close it: `[NATIVE]` (a ratification only the native can give),
> `[COWORK]` (planning/authoring/verification Cowork does now), `[OPERATOR]` (a prod data-plane action
> a human runs), or `[SWARM]` (explicitly deferred to the autonomous build — listed so we confirm it's
> safe to defer). The whole point is to drive every `[NATIVE]`/`[COWORK]`/`[OPERATOR]` item to DONE
> before kickoff, leaving only `[SWARM]` items for the autonomous run.

---

## §0 — The closure structure (six gates, in order)

```
GATE A — VERIFY        prod-truth reconciliation; resolve all unknowns      [OPERATOR + COWORK]
GATE B — DECIDE        ratify every open native gate; lock the asset set    [NATIVE]
GATE C — AUTHOR        finalize all briefs, the plan, queue, kickoff        [COWORK]
GATE D — REGISTER      asset catalog / registry / count_sql / manifest      [COWORK authors → SWARM applies]
GATE E — WIRE          orchestrator + DAG + Dockerfile + cockpit surfaces   [COWORK specs → SWARM implements]
GATE F — ARM           autonomy framework: queue, claim-ledger, CI, budget  [COWORK + OPERATOR]
        ────────────── then KICKOFF (autonomous swarm) ──────────────
```

A gate does not open until the prior gate's `[NATIVE]`/`[COWORK]`/`[OPERATOR]` items are DONE.

---

## §1 — GATE A: VERIFY (close all unknowns)  `[OPERATOR + COWORK]`

The four-times-burned lesson: never plan on documented state. Everything here must be prod-true before
DECIDE/AUTHOR can finalize.

| A# | Item | Who | Status |
|---|---|---|---|
| A1 | Run `L4_PHALA_PROD_RECONCILIATION_v1_0.md` against prod (Q1–Q5, C1–C4); fill the findings table | `[OPERATOR]` | OPEN — gates everything |
| A2 | Resolve **multi-dāśā** real state (U1 branch: wire / build-run / deepen) from A1.Q1 | `[COWORK]` | blocked on A1 |
| A3 | Resolve **M9 multi-school** real state (persisted? hardcode extent?) from A1.Q3/C2 | `[COWORK]` | blocked on A1 |
| A4 | Confirm **all L4-consumed inputs have rows** (convergence 660, obstruction 60, signals 66,738, discoveries 1,411, embeddings 66,738, cdlm cells, subsystem assets) from A1.Q4 | `[COWORK]` | blocked on A1 |
| A5 | Confirm **Prāṇa ceiling** (U2 net-new?) from A1.Q5 | `[COWORK]` | blocked on A1 |
| A6 | Confirm the **global migration max** across BOTH dirs (L4 numbering start) — code-verified 329; re-confirm at A1 time | `[COWORK]` | re-verify |
| A7 | Confirm **prod == main** (Cloud Run revision == HEAD) and L3 `kala_*` lit on the LIVE cockpit | `[OPERATOR]` | OPEN |

**Gate A exit:** the reconciliation findings table is filled; U1/U2/M9 are each sized; all input row
counts confirmed; prod==main. No `[SWARM]` work starts until this is green.

---

## §2 — GATE B: DECIDE (ratify the native-only gates)  `[NATIVE]`

These cannot be delegated to the swarm — they are judgments. Each must be ratified before AUTHOR locks
the briefs. (All are async/resumable per the autonomy pattern, but must be closed pre-kickoff.)

| B# | Decision | Ref | Status |
|---|---|---|---|
| B1 | **G-RECT** — PyJHora `compute_ascendant` accepted as the rectification oracle | LEDGER D12 | OPEN `[NATIVE-RATIFY]` |
| B2 | **G-LADDER** — the exact `f(convergence_score)` confidence mapping for ph_nimitta | LEDGER D13 | OPEN `[NATIVE-RATIFY]` |
| B3 | **ph_anudhyana** — does discovery-seeding get its own asset, or fold into ph_nimitta? | LEDGER §7 | OPEN |
| B4 | **Lag model (ph_sankrama)** — the cross-domain lag curve, if treated as a judgment | ph_sankrama §4 | OPEN |
| B5 | **U2 infra approach** — dedicated Cloud Run batch vs. selective lifetime/Prāṇa | U2 §3 | OPEN |
| B6 | **Final asset count** — confirm 9 (or 8 if ph_anudhyana folds) after A2–A5 re-sizing | LEDGER D8 | OPEN |
| B7 | **Scope of THIS launch** — all of {U1, U2, M9, 9×L4} in one autonomous run, or staged waves? | new | OPEN |

**Gate B exit:** every native gate ratified (or explicitly deferred-to-swarm with a documented default
per the canonical-or-floor rule). The asset set is final.

---

## §3 — GATE C: AUTHOR (finalize every input the Conductor consumes)  `[COWORK]`

The swarm runs on what Cowork authors. Every brief reviewed and finalized in Cowork; the campaign plan,
session queue, and kickoff written. (This is the "review each brief in Cowork to finalize" step.)

| C# | Artifact | From draft | Status |
|---|---|---|---|
| C1 | **Finalize `ph_nimitta` SUPREME** brief (8 axes; resolve `[RECON]` tags from A2–A4) | DRAFT v0.1 | OPEN |
| C2 | **Finalize `ph_sankrama`** brief (lag model from B4) | DRAFT v0.1 | OPEN |
| C3 | **Finalize `ph_pramana`** brief (scaffolding-only boundary) | DRAFT v0.1 | OPEN |
| C4 | **Finalize `ph_muhurta` / `ph_pratikara` / `ph_sodhana` / `ph_suddha_sodhana` / `ph_phaladesa`** (carry enrichments: pratikara remedy-economics, sodhana G-RECT, phaladesa contradiction+precedent, subsystem time-indexing per D11) | 6-asset drafts | OPEN |
| C5 | **Finalize `ph_anudhyana`** brief OR fold into C1 (per B3) | — | OPEN |
| C6 | **Finalize M9 activation** brief (de-hardcode + persist + wire; sized by A3) | DRAFT v0.1 | OPEN |
| C7 | **Finalize U1** brief (branch from A2) | DRAFT v0.1 | OPEN |
| C8 | **Finalize U2** brief (infra from B5; Prāṇa from A5) | DRAFT v0.1 | OPEN |
| C9 | **Author the master `L4_PHALA_CAMPAIGN_PLAN_v2_0`** (9-asset, upstream-first; SUPERSEDES the 6-asset v1.0) | — | OPEN |
| C10 | **Author the Conductor `session_queue.yaml`** (the wave DAG: U1 → U2 → re-seal → M9 → P1..P6 L4) | — | OPEN |
| C11 | **Author the `KICKOFF` prompt** (the single paste-block; embeds the autonomy rails) | — | OPEN |
| C12 | **Author/refresh the `DERIVATION` + reuse principle** (D10 READ→CALL→PyJHora) into the campaign plan | — | OPEN |
| C13 | **Bake the HARD VISUAL SEAL GATE** into the queue's seal block (the #1 L3 lesson) | — | OPEN |
| C14 | **Define per-asset acceptance gates** as machine-checkable ACs (the swarm's pass/fail) incl. `[verify-against: prod]` tags | per brief | OPEN |

**Gate C exit:** every brief finalized in Cowork; the plan, queue, kickoff authored; ACs are
prod-tagged and machine-checkable. These are the swarm's complete input set.

---

## §4 — GATE D: REGISTER (the catalog/registry/CTS/manifest surfaces)  `[COWORK authors specs → SWARM applies]`

These surfaces must be SPEC'd correctly now (Cowork) so the swarm applies them mechanically. The asset
catalog, registry, count_sql, and manifest are the "asset CTS" the native named.

| D# | Item | Detail | Who specs / applies |
|---|---|---|---|
| D1 | **asset_registry_seed.ts rows** — author the full AssetDef for each new/changed asset | All ~30 fields per row: asset_id, layer='phala', sort_order, sanskrit/english names, storage_type, target_table, **count_sql with `$1`**, size_sql, `target_floor: null` (set post-build, floors-aspirational), expected_volume_formula, depends_on, scope='per_chart', is_active:true, estimated_seconds:null, asset_kind='artifact', catalog_status:'DRAFT'→CURRENT-at-seal | COWORK specs → SWARM writes |
| D2 | **count_sql correctness (the "asset CTS")** — every asset's chart-scoped `count_sql` uses `$1` (NEVER `$$CHART_ID$$` — L3 BUG-1); service assets bypass count via service-health | the stats route reads count_sql; wrong binding = cockpit error | COWORK specs → SWARM |
| D3 | **CAPABILITY_MANIFEST.json entries** — one per new writer file + one per new DB table (canonical_id, path, version, status, layer:'L4', fingerprint) | governance reads the manifest; drift_detector cross-checks | COWORK specs → SWARM |
| D4 | **Migration authoring** — one migration per asset table, numbered **330+** in `platform/supabase/migrations/`; first one DROPs `kala_timeline` (CF.L3.2); each: CREATE TABLE + INSERT asset_registry row in one txn; idempotent; reversible-comment | the two-174 trap (D14) — pre-allocate in DAG order | COWORK specs → SWARM |
| D5 | **Registry ↔ manifest ↔ filesystem consistency** — drift_detector + schema_validator must exit clean | the swarm runs these; spec what "clean" means for L4 | COWORK defines → SWARM verifies |
| D6 | **depends_on DAG correctness** — every asset's depends_on lists real upstream asset_ids; no cycles | orchestrator topo-sorts from this | COWORK specs → SWARM |

**Gate D exit:** the registry/manifest/migration specs are authored and embedded in the briefs; the
swarm has an unambiguous "what to register" with correct count_sql and numbering.

---

## §5 — GATE E: WIRE (orchestrator + DAG + Docker + cockpit fully established)  `[COWORK specs → SWARM implements]`

The native's explicit ask: "ensure the orchestrator is wired and fully established; the DAG is wired
and fully established." Code-verified requirements:

| E# | Item | Requirement (code-verified) | Risk if missed |
|---|---|---|---|
| E1 | **Writer registration** — each ph_* writer is `@register('ph_*')` `WriterBase` in `pipeline/orchestrator/writers/` | auto-discovered via pkgutil; MUST be in that dir + decorated | missing @register → asset silently skipped |
| E2 | **DAG wiring** — orchestrator derives order from `asset_registry.depends_on`; confirm the full L4 chain topo-sorts (ph_nimitta → P2 → ph_sankrama → ph_pramana → ph_phaladesa) | DAG = depends_on; no separate declaration | cycle/missing dep → asset fails |
| E3 | **Dockerfile.pipeline COPY** — confirm `COPY platform/python-sidecar/pipeline/orchestrator/writers/` includes the new ph_* files + any data files the engines read (embeddings access is DB, fine) | THE bo_pramana_mapa bug: missing COPY → ModuleNotFoundError at runtime, job hangs IN_PROGRESS | **silent prod hang** — highest-risk gotcha |
| E4 | **Service reuse wiring** — confirm ph_* writers CALL `ka_dasha_kala`/`ka_gochara`/`ka_muhurta_seva`/`ka_tulana`/`ka_graha_sancara` (imported + reachable in the image), not reimplement | D10 reuse rule | duplication / missing import |
| E5 | **Cockpit / Nirmāṇa render** — L4 assets render because the registry has layer='phala'; layers are DERIVED from the registry (no hardcoded frontend list to edit — verified) | `/api/cockpit/registry` groups by layer; constellation DAG auto-renders | none if registry correct |
| E6 | **Nirmāṇa build-tracker L4 state** — confirm the build view shows ph_* as NOT-BUILT pre-build, then lit post-build; the stats route reads count_sql | the native's "Nirmāṇa build tracker L4 updated" | wrong count_sql → shows error |
| E7 | **Orchestrator build-state writing** — orchestrator is the SOLE `asset_throughput` / `last_built_at` writer; ph_* writers never stamp it (CF.L3.8 — L3 used a one-shot reconcile; L4 MUST use the orchestrator click-Build path) | the frozen contract | NOT-MIGRATED display / stale state |
| E8 | **build_runs plan** — the autonomous build enqueues the L4 assets in the run plan (DAG order) for chart `482012f1` | runner reads build_runs.plan | asset not invoked |

**Gate E exit:** the wiring is fully specified — registration, DAG, Dockerfile COPY, service reuse,
cockpit render, build-state authority, and the build plan. The swarm implements against an established
wiring spec, not a discovered one.

---

## §6 — GATE F: ARM (the autonomy framework itself)  `[COWORK + OPERATOR]`

Because there is NO human gate at runtime, the autonomy rails must be armed and correct before launch.

| F# | Item | Detail | Who |
|---|---|---|---|
| F1 | **Conductor session_queue** present + walkable (pre-fan-out steps, waves, seal) | the Sūtradhāra walks it top-to-bottom | COWORK (C10) |
| F2 | **Briefs + governing docs committed to a clean branch off origin/main** | the swarm reads them from the branch | OPERATOR |
| F3 | **Claim-ledger / smriti dir** for the L4 run created (`00_ARCHITECTURE/CONDUCTOR/l4-phala/smriti/`) | shared swarm state + audit log | COWORK |
| F4 | **CI is GREEN on main** — the "main CI red" issue (3 pre-existing failures) must be resolved FIRST, else every PR inherits red and auto-merge logic is unreliable | autonomy merges on CI-green; a red baseline poisons the gate | OPERATOR (dedicated fix) |
| F5 | **deploy.yml applies migrations before the Cloud Run job** + builds both images (web + sidecar) | confirm the migrate step runs pre-job | OPERATOR verify |
| F6 | **AUTONOMOUS_MODE rails confirmed** — branch policy, auto-merge, auto-deploy, DB-ops authority all enabled for this run per AUTONOMY_RESILIENCE_PATTERN | the swarm self-decides gates under §C rails | COWORK confirm in kickoff |
| F7 | **Budget ceiling set** — the per-asset cap + the $5k/wave Tier-3 ceiling (the ONLY synchronous native event) confirmed | the single residual human-input point | NATIVE confirm |
| F8 | **Vimarśaka post-merge audit armed** — temporal + anti-drift auditors active per wave (the auto-revert safety net) | catches RED post-merge, auto-reverts | COWORK confirm in kickoff |
| F9 | **The HARD VISUAL SEAL GATE armed** — the seal step verifies the LIVE cockpit (Cloud Run revision == merge SHA; ph_* lit with real counts; zero error/missing_table) — NOT a green JSON | the #1 L3 lesson, burned ~4× | COWORK (C13) |
| F10 | **Re-seal authority for U1/U2** — confirm the swarm may version-bump + re-seal L1_GANITA_CLOSURE and L3_KALA_CLOSE (since U1/U2 reopen sealed layers) | upstream-first means sealed-layer reopens | NATIVE confirm |

**Gate F exit:** the autonomy framework is armed and correct — queue, branch, CI-green, deploy path,
rails, budget, auditors, seal gate. The swarm can run end-to-end with no human gate.

---

## §7 — The items the native LISTED, mapped to gates (nothing dropped)

| Native's item | Closed in |
|---|---|
| Infrastructure / pipeline provisioning | GATE E (Docker/orchestrator) + GATE F (CI/deploy/budget) |
| Pre-implementation items — the entire list | this whole document (§1–§6) |
| Asset catalog / asset registry / asset CTS (count_sql) | GATE D (D1, D2, D3) |
| Nirmāṇa build tracker L4 updated | GATE E (E5, E6) |
| Review each brief in Cowork to finalize | GATE C (C1–C8) |
| Ensure orchestrator wired + fully established | GATE E (E1, E3, E4, E7, E8) |
| Ensure the DAG wired + fully established | GATE E (E2) + GATE D (D6) |

## §8 — The items the native did NOT list but MUST close (the additions)

1. **GATE A (prod-truth verification)** — the unknowns (multi-dāśā, M9) gate every other gate; this is
   the single most important addition.
2. **GATE B native ratifications** (G-RECT, G-LADDER, asset count, launch scope) — judgments the swarm
   cannot make.
3. **CI-green-on-main first (F4)** — a red baseline makes autonomous auto-merge unreliable; must be
   fixed before kickoff. Dedicated session.
4. **Dockerfile COPY verification (E3)** — the highest-risk silent-hang gotcha; explicit pre-check.
5. **Build-state authority (E7)** — L4 must go through the orchestrator click-Build path, not a
   one-shot reconcile (CF.L3.8).
6. **Re-seal authority for U1/U2 (F10)** — upstream-first reopens sealed layers; the swarm needs
   explicit authorization to version-bump + re-seal.
7. **The HARD VISUAL SEAL GATE (F9)** — the seal must verify the visual cockpit, not the API.
8. **Migration pre-allocation (D4)** — the two-174 trap; numbers pre-assigned in DAG order at
   pre-fan-out.
9. **Vimarśaka auto-revert armed (F8)** — the safety net that makes no-human-gate safe.
10. **A non-native test chart** consideration — if the swarm should prove chart-generality (esp. for
    M9 de-hardcoding), confirm whether Abhinandan `1c826d5a` (Phase E) is used. `[NATIVE decide]`

## §9 — Recommended close sequence (what Cowork does next, in order)
1. **A1 runs** (operator) → fill reconciliation → Cowork resolves A2–A5.
2. **Cowork drives GATE B** to the native (the ratification questions).
3. **Cowork finalizes all briefs (GATE C)** on verified ground.
4. **Cowork specs GATE D + E** into the briefs (registry, manifest, migrations, wiring).
5. **Operator closes F4 (CI-green) + F2/F5 (branch + deploy path)**.
6. **Cowork authors the queue + kickoff (C10/C11), arms the rails (GATE F)**.
7. **Kickoff** — the autonomous swarm runs U1 → U2 → re-seal → M9 → L4 → visual-seal.

---
*End of L4_PHALA_PRE_IMPLEMENTATION_CLOSURE v1.0. Six gates: VERIFY → DECIDE → AUTHOR → REGISTER →
WIRE → ARM → kickoff. Every item tagged by who closes it; everything the autonomous swarm cannot do
for itself is driven to DONE before launch.*
