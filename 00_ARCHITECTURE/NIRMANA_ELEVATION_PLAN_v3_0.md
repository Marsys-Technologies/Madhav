---
artifact: NIRMANA_ELEVATION_PLAN_v3_0.md
version: 3.0
status: PROPOSED — plan only; the only executed items are migrations 588/589 (protection removal)
produced_on: 2026-08-23
grounded_at: HEAD 6326cda7a (2026-08-22) + live production DB reads and per-asset measurement 2026-08-23
authoritative_side: claude
role: >
  The complete elevation programme for the Nirmāṇa Build Tracker — the per-chart build cockpit,
  the orchestrator behind it, the asset DAG both operate on, and the catalogue that describes it.
  v3.0 is the first version with a plan of action for EVERY asset in EVERY layer (§13), across
  three dimensions — correctness & completeness, rebuild time, re-architecture & alignment — each
  derived from that asset's own measured facts and carrying a quantified benefit.
supersedes: >
  NIRMANA_ELEVATION_PLAN_v2_0.md (v2.2, 2026-08-23) — retained in place, marked SUPERSEDED.
  Everything in v2.2 is carried forward; v3.0 adds the correctness/completeness measurement
  programme (§4), the per-asset plans (§13), the Gochara transition strategy (§5), and folds in
  every item discussed in the 2026-08-23 sessions that v2.2 had not yet absorbed.
companion_artifacts:
  - 00_ARCHITECTURE/control/NIRMANA_ASSET_CONTROL_WORKBOOK_v3_0.xlsx — execution surface, 9 sheets
  - 00_ARCHITECTURE/control/build_asset_control_workbook.py — generates the workbook AND §13 of this file
  - 00_ARCHITECTURE/control/asset_plans.py — the per-asset plan derivation (single source for both)
  - 00_ARCHITECTURE/control/measure_assets.py — per-asset row/floor measurement → asset_measurements.json
  - 00_ARCHITECTURE/control/snapshots/20260823_pre_protection_removal/ — verified logical snapshot
invariants:
  - I1 — Protection REMOVED 2026-08-23 on native instruction (migrations 588 + 589). The campaign
    rebuilds every asset; a guard needing an override on every legitimate write is not wanted.
  - I2 — Snapshot discipline replaces protection. Any destructive operation on an irreplaceable
    corpus takes a verified logical snapshot first. STANDING: ka_gochara_sweep's 38,287 v1 rows
    have NO registered writer and cannot be regenerated; the 2026-08-23 snapshot is their only
    recovery path.
  - I3 — The FROZEN orchestrator contract (@register / WriterBase / run(ctx) / ctx.db_conn never
    committed by the writer) is preserved. Phases 2–5 need a native-authorised freeze exception
    on orchestrator internals; the writer-facing contract does not change.
  - I4 — No phase closes on CI-green or code review alone (PARIPRAŚNA DD-21). Every acceptance
    criterion is verified by live execution against production.
  - I5 — Every status, grade, PASS, and now every `lit` this plan touches has a real detector
    behind it or is null (CLAUDE.md §N.8). `lit` is earned by an integrity check, not assumed
    from a row count.
  - I6 — No registry row is ever DELETEd. Assets leave the build path by lifecycle transition.
  - I7 — NEW. Floors are aspirational, never fabricated (§N.4): a missing floor is set to the
    achieved count; a below-floor asset is decided explicitly (stale floor vs incomplete build),
    never left to sit.
  - I8 — NEW. No destructive or first-run operation is executed first against a canonical chart.
    Chart 3 (cb73cd3d) is the standing rehearsal subject.
changelog:
  - 3.0 (2026-08-23) — Per-asset plans for all 128 assets (§13, generated); correctness &
    completeness programme (§4) from a fresh measurement pass — 80.7% of native L1 facts at
    verification tier `single`, zero assets with an integrity_check_sql, 9 below floor (one at
    57%), 48 without a floor, 6 with zero rows on the native chart including the L1 asset
    ga_prashna, 29 empty on the rehearsal chart; Gochara transition strategy (§5); invariants I7,
    I8; Phase 1 gains the migration-tracking item for hand-applied 588/589; workbook gains the
    Asset Plans sheet and six measurement columns; every item discussed but not yet folded in
    (deterministic-first audit result, §N.5 resolution check, MSR build generations, proxy drops,
    governance debris) is now in the plan.
  - 2.2 (2026-08-23) — §12 Infrastructure and database; catalog_status drift; zero-consumer
    review; infra items distributed into owning phases; defect D-16.
  - 2.1 (2026-08-23) — Protection removed (588/589); I1/I2 rewritten; D-02 closed.
  - 2.0 (2026-08-23) — §3 Asset Catalogue Contract; Phase 0 pre-flight; I6.
  - 1.0 (2026-08-23) — Initial re-grounded plan.
---

# Nirmāṇa Elevation Plan v3.0

## §0 — Grounding

Verified at HEAD `6326cda7a` (2026-08-22) with live production reads on 2026-08-23, plus a
per-asset measurement pass (`measure_assets.py`) that executed every asset's `count_sql` against
all three charts and recorded rows vs declared floor, integrity-check presence, and descriptions.

Campaigns folded in: **GOCHARA-UTKARṢA**, **PARIṢKĀRA**, **SAMPŪRTI/DHARA**, **EKAVĀKYATĀ**,
**PARIŚEṢA-RĀTRI-V4**, **PARIPRAŚNA** — 239 commits, 6 campaigns, zero changes to the tracker
itself (cockpit last touched 2026-08-10, orchestrator core 2026-07-31).

---

## §1 — Diagnosis

### 1.1 Fewer than half of all build attempts succeed

3,255 complete · 1,565 error · 847 aborted · 1,477 queued-never-run = 7,144 attempts, **45.6 %
complete**. Cost and failure correlate: `ka_gochara_sweep` 9.6 % of 94 (worst 35.6 h),
`ka_kshetra` 11.9 % of 126 (worst 33.8 h), `ga_vichara` 25.7 %.

### 1.2 Live chart state (2026-08-23)

| chart | lit | stale | error | dormant | incomplete |
|---|---|---|---|---|---|
| 482012f1 (Abhisek, native) | 64 | 8 | 10 | 1 | 0 |
| 1c826d5a (Abhinandan) | 76 | 1 | 2 | 2 | 0 |
| cb73cd3d (chart 3, rehearsal) | 31 | 14 | 14 | 0 | 1 |
| global | 42 | 0 | 1 | 0 | 0 |

### 1.3 Failures live right now

`ka_gochara_sweep` "no writer registered" ×2 (retired zombie rows) · `ka_kshetra` reaped at
301/308 substeps (`NOW()` heartbeat) · eight `mi_*` blocked from one root, one of them by a
dependency literally named `timeout:600s` · `bg_ephemeris_engine` red since 2026-06-18 (66 days).
The `BUILD-PROTECTED` error on the v3 materializer is cleared by the protection removal.

### 1.4 The `has_substeps` false negative

28 writers plan substeps; 14 carry `has_substeps=false` — so the §N.8 completeness gate is
silently skipped and a partial build is promoted to `lit`. Every layer is affected. `ka_sangam`
has 61 recorded substeps per chart and 11 downstream dependants.

### 1.5 Correctness and completeness — measured for the first time *(new in v3.0)*

| finding | measurement |
|---|---|
| Verification tier of native L1 facts | **112,589 of 139,471 (80.7 %) are `single`** — unverified; 9,320 (6.7 %) `two_pass_verified` |
| Assets with an `integrity_check_sql` | **0 of 128** — no asset has a post-build correctness gate |
| Assets below declared floor | **9**: `ga_sade_sati` 57 % (6,287 / 11,019), `bo_laksana` 83 %, `bo_samskara` 84 %, `bg_reference` 84 %, `ga_dashas` 90 % (483,859 / 536,471), `bg_concordance`, `bg_text_index`, `ga_sensitive`, `bg_sky_calendar` |
| Assets with rows but no floor | **48** — completeness is unmeasurable for them |
| Zero rows on the native chart | **6**: `bg_sarvatobhadra_grid` (by design), **`ga_prashna` — an L1 asset whose throughput reads `lit` on all three charts with zero rows: a live specimen of the unearned-`lit` defect**, `mi_abhilekha`, `mi_sankalpa`, `mi_seva`, `mi_vistara` |
| Empty on the rehearsal chart while populated on native | **29** — chart 3 cannot serve as a rehearsal subject for them |
| Empty on Abhinandan while populated on native | **5**: `ka_sudarshana_varsha`, `lel_events`, `mi_bhara`, `mi_jivanaghatana`, `mi_pramana` |
| Accretion across build generations | `chart_facts`: 15 fact_keys under two `build_id`s; `bodha_msr_signals`: three `build_id`s (49,955 / 104 / 45) — verified to be the seven co-writers, not stale residue |
| §N.5 derivation-ledger resolution | 2,000 / 2,000 sampled `constituent_facts_array` ids resolve to `chart_facts.fact_id` — **sound** |
| Deterministic-first audit | Three writers touch `genai`; all three are embeddings only (`bg_texts`, `bo_samskara`, `mi_darshana`) — **compliant**; `ph_phaladesa` bans generative narration by policy |

Two of these are doctrinal drift: `ga_dashas`' floor of 536,471 is the historical figure
CLAUDE.md §C.14 deliberately stopped hardcoding (DVA Ruling 16) — it lives on in the registry and
now reads as a 10 % shortfall; and a `single`-tier majority at L1 means most downstream narration
stands on unverified numbers, which §N.7 item 5 says no narration test can compensate for.

### 1.6 Catalogue drift

47 assets at `catalog_status=DRAFT`, 34 of them built and served · 13 table-backed assets with no
detected serving consumer · 14 null `layer_index` + 6 bare-numeral forms · three columns
disagreeing on which assets are services · `lel_events` the only prefix violation · one CURRENT
asset (`bg_gochara_citation_resolution`) with no writer and no build on any chart.

### 1.7 Resume, telemetry, DAG shape

10 genuinely heavy assets (p90 ≥ 30 min, median ≥ 10 min, or a substep plan running ≥ 5 min — a substep
plan alone does not make an asset heavy); 8 of them have no resume at all; three private copies of the
resume protocol elsewhere; `completed_keys` passed by no caller · telemetry polluted (16.9-day maxima), `estimated_seconds` on 2 of 128 · DAG
21 levels deep, ~3 wide from L3 down, no cycles — 18 of 21 levels cannot use `WORKER_LIMIT=4`.

### 1.8 The v1 gochara corpus cannot be rebuilt

`ka_gochara_sweep` is RETIRED; its `@register` was removed at retirement. No writer can regenerate
its 38,287 v1 rows, which chart 3 still serves (no authority row). The 2026-08-23 snapshot is the
only recovery path. "The campaign rebuilds everything" is true of every asset except this one.

---

## §2 — Target state

Nirmāṇa becomes a **content-addressed, partition-aware, self-healing build system with a
cost-honest cockpit, standing on a contract-conformant catalogue whose every `lit` is earned by an
integrity check.** Freshness is decided by what an asset was built *from*. Invalidation is scoped
to the partitions affected. Interrupted work resumes as an orchestrator guarantee. Failures are
classified and retried when transient. The DAG is managed, audited, and has a measured critical
path. Completeness is measured against an honest floor on every chart. And the cockpit tells the
operator the truth — what is fresh, why something is stale, what an action costs, which single
fault sits behind a screen of red, and whether a green asset is actually complete.

---

## §3 — The Asset Catalogue Contract

### 3.1 Why a contract

"Register the asset as per the system we have set up" cannot be followed because that system is
not written down. The contract is Phase 0's first deliverable; reconciliation is its second.

### 3.2 Lifecycle — tombstone, never delete (I6)

| State | Meaning | Rules |
|---|---|---|
| `CURRENT` | Live, buildable, authoritative | Full conformance; may depend only on CURRENT or SOURCE |
| `DRAFT` | Registered, not yet authoritative | A CURRENT asset may not depend on it (CI-asserted) |
| `RETIRED` | No longer built; record retained | `is_active=false`, zero throughput rows, `data_disposition` |
| `SUPERSEDED_BY(x)` | Replaced by a named successor | As RETIRED + resolvable pointer |
| `SOURCE` | Ingested data the DAG reads, never builds | Outside L0–L5; exempt from writer/count/floor |

`data_disposition` ∈ {`RETAINED_AS_CAPITAL`, `SUPERSEDED_IN_PLACE`, `DROPPABLE`} is mandatory on
exit. Retired rows carry FK dependants and audit history; migration 563 already failed on that FK.

### 3.3 "Duplicate" — measured, not assumed

Four tables have multiple active writers and all are legitimate (`bodha_msr_signals` 7,
`chart_facts` 5, `brahma_class_priors` 2, `classical_text_chunks` 2). The invariant is **one
authoritative producer per (target_table × generation × natural-key partition)** — never one per
table. Each co-writer declares its partition in the registry so the invariant is checkable.

### 3.4 Required fields by kind

| Field | data | service | artifact | source |
|---|---|---|---|---|
| `asset_id` prefix matches layer (§N.1) | ✔ | ✔ | ✔ | exempt |
| `layer` · `layer_index` (`Lx`) · `layer_name` (derived) | ✔ | ✔ | ✔ | outside L0–L5 |
| names, description, `sort_order`, `scope` | ✔ | ✔ | ✔ | ✔ |
| `catalog_status` + lifecycle fields | ✔ | ✔ | ✔ | ✔ |
| `target_table` · chart-scoped `count_sql` · `clear_tables` | ✔ | ✖ null | ✔ | ✖ |
| **`target_floor` (achieved, never invented)** | ✔ | ✖ | ✔ | ✖ |
| **`integrity_check_sql` (the post-build gate that earns `lit`)** | ✔ | ✖ | ✔ | ✖ |
| `has_substeps` **derived from the writer class** · `writer_timeout_seconds` · `estimated_seconds` | if substep writer | ✖ | if substep writer | ✖ |
| natural-key partition declaration (co-written tables) | ✔ | ✖ | ✔ | ✖ |
| `health_probe` · `provides_apis` · `service_health` | ✖ | ✔ | ✖ | ✖ |
| authority pointer + `protected_generations` | if generation-bearing | ✖ | ✖ | ✖ |
| `depends_on` — every target exists, is active, and is not DRAFT | ✔ | ✔ | ✔ | ✖ |
| `consumers` — serving surfaces reading this asset | ✔ | ✔ | ✔ | ✔ |

`asset_kind` is the single authoritative classification column. The two **bold** rows are new in
v3.0: they move correctness from a tribal expectation to a registration requirement. Their
*presence* is reconciled in Phase 0; their *enforcement as a gate* lands in Phase 2.

### 3.5 The consumer map

Asset → {MCP tools, API routes, retrieval layers} reading its table. Built from
`platform-mcp/src/tools/**`, `platform/src/app/api/**`, `platform/src/lib/retrieval/**`. Without
it, "is it safe to retire this?" is unanswerable. 13 assets currently have no detected consumer.

### 3.6 `SOURCE` and "registered but dead"

`lel_events` → `SOURCE`. `bg_gochara_citation_resolution` (CURRENT, no writer, never built) →
provision, demote, or retire — never leave a CURRENT asset that nothing can build.

---

## §4 — Correctness & completeness programme *(new in v3.0)*

Six disciplines. Each has a measured baseline (§1.5), a per-asset action (§13), and a detector.

1. **The integrity gate earns `lit`.** Every data asset gets an `integrity_check_sql` expressing
   its own invariant (row count ≥ floor, no duplicate natural keys per chart, plus kind-specific
   clauses — one row per `(chart_id, fact_key)` for `chart_facts` writers; every
   `constituent_facts_array` id resolves for MSR writers; one authoritative generation per chart
   for gochara). The orchestrator runs it after the writer commits; `lit` is written only on pass,
   `incomplete` on fail. This generalises SATYA-DĪPA from "the substep plan finished" to "the
   data is what the asset claims." Baseline: 0 of 128.
2. **Honest floors on every chart (I7).** 48 assets get `target_floor` = achieved count; the 9
   below-floor assets are each decided explicitly — `ga_dashas` 536,471 is a stale historical
   figure (reset to measured); `ga_sade_sati` at 57 % and `ga_prashna` at zero are incomplete
   builds (rebuild and verify); `bo_laksana`/`bo_samskara` 60,000 floors are re-measured.
   Completeness % becomes a cockpit column.
3. **Verification-tier programme for L1.** 80.7 % `single` is the correctness ceiling of the
   whole instrument. For each `chart_facts` writer, add a second derivation path for its fact
   categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab`
   constants; `single` remains a permitted, honest tier (S7 ruling) — the goal is to shrink it,
   not to relabel it. Cockpit shows the tier mix per L1 asset.
4. **Accretion guard.** Delete-then-insert scope is declared per writer as
   (chart_id × natural-key partition) and the integrity check asserts single-row-per-key across
   `build_id`s. Baseline: 15 duplicated fact_keys on the native chart.
5. **Derivation receipts for L3–L5.** Every output row of an asset with ≥4 inputs records the
   upstream digests it was built from, so a wrong answer is traceable to the input that produced
   it — the same receipt that drives partition-scoped invalidation (§6).
6. **Narration fidelity and determinism.** §N.7 golden tests for every narrative writer
   (`ka_bhavishya_lekha`, `ph_phaladesa`, `mi_darshana`, `bo_chart_gestalt`, …); a build-twice-
   compare-digests harness for one asset per tier, which is also Phase 3's acceptance test.

**Cross-chart parity** is the seventh, implicit discipline: 29 assets are empty on chart 3 and 5
on Abhinandan while populated on native. Before chart 3 can be the rehearsal subject (I8) it must
be brought to parity; that is Phase 1's first rebuild.

---

## §5 — Gochara: the transition strategy, in one place

Discussed across several sessions; recorded here so it is not lost.

- **What exists.** v1 sweep (`ka_gochara_sweep`, RETIRED, 38,287 rows, daily-grid, ~30 h/chart,
  no writer — capital, not cache). v2/W2G (`ka_gochara`, validation surface, ±3 y, 5 bodies,
  degree-contact only, 54 rows, read by nothing). v3 (`ka_gochara_v3_century_materialize`, 8
  contact primitives, 27 classes, all shapes, full century in 270 decade slices, delta
  fingerprint folding the live scoring signature after F-52) — **serving both canonical charts
  via `kala_gochara_authority`** (943 / 941 windows); chart 3 has no authority row and serves v1.
- **The strategy.** v1 stays as the frozen benchmark generation (I2). v3 is the authority and the
  only writer that is elevated further. v2 is honestly a validation artefact: either promote its
  row to DRAFT with that stated, or retire it with `SUPERSEDED_BY(v3)`; either way its `count_sql`
  stops claiming v3's rows. Chart 3 gets an authority row and a v3 build so it serves the same
  generation as the canonical charts.
- **Slices as capital.** v3's per-slice delta fingerprint is the proven pattern §6 generalises:
  receipts per partition, rebuild only mismatches, never burn on suspicion.
- **The open decision.** F-52 made every materialized v2 row stale under the live scoring
  signature; no rebuild has been dispatched. Phase 1 either rematerializes v3 under the
  determinism harness or records the deferral so the cockpit stops showing green.
- **Protection.** Removed (I1). If ever reinstated, key it on (table, generation), never on
  `asset_id` — the old guard was keyed to `ka_gochara` while the writer was the v3 materializer,
  and blocked the authoritative writer outright (D-02).

---

## §6 — Per-asset elevation, by tier

| Tier | n | Treatment |
|---|---|---|
| **G · Global substrate** | 40 | `substrate_version` + output digest; consumers record the version read; visible to the per-chart readiness gate; own cadence and SLO. Exemplar `bg_gochara_arcs`: the whole epoch in ~48 s, reused forever. |
| **H · Heavy partitioned** | 10 | Universal partition receipts; shared `ResumableWriter` replacing three private copies; persisted plan totals; per-partition cost so an invalidation can be priced. |
| **M · Medium deterministic** | 66 | Output digest + early cutoff — the long tail that makes full rebuilds slow. |
| **S · Service probe** | 8 | Real known-answer probes with SLOs, history, alerting, own cockpit lane. |
| **X · Generation-bearing** | 4 | Generation + per-chart authority as first-class registry/UI concepts, one count and one freshness per generation. |

Partition granularity, measured from the writers: fourteen L1/L2 writers partition by
**ayanamsha** (5 substeps), `ga_dashas` by `{system}:{aya}`, `bg_reference` by
`{system}:{ayanamsha}`, `ka_kshetra` by `stage{n}:{event_class}:{slice}`, gochara v3 by
`{event_class}::{decade}`, `ka_sangam` by `near + lifetime:{i}`. Per-substep input digests turn
each of these into a receipt: an ephemeris change re-runs one ayanamsha partition, not five.

---

## §7 — Build-time optimization · six levers

1. **Skip what has not changed** — content addressing with early cutoff; the direct fix for "a
   small L1 change stales the whole DAG."
2. **Partition-scoped invalidation** — receipts per substep.
3. **Shorten the critical path, not widen the pool** — from L3 down, remove declared-but-unread
   edges; the Mīmāṃsā tail is a five-deep serial chain inside two layers.
4. **Retry transient failures** — at 45.6 % completion, most wall-clock is human re-dispatch.
   SAMPŪRTI specimens: cloud-sql proxy drops after ~8 min of heavy writes; `/tmp` restart loops.
5. **Multi-dispatch continuation** — in the orchestrator, not the infrastructure.
6. **Right-size timeouts and resources** from clean telemetry (prerequisite: close orphaned
   `build_run_assets` rows; 16.9-day maxima today).

---

## §8 — Orchestrator elevation *(freeze exception required; writer contract unchanged)*

One staleness engine · content-digest freshness with early cutoff · graded staleness
(`fresh · stale:upstream-content · stale:code · stale:config`) · **integrity gate after commit
(§4.1)** · error taxonomy + retry · shared resumability with `completed_keys` wired and plan totals
persisted · `clock_timestamp()` heartbeat · one state vocabulary across DB/Python/TS · registry
lifecycle operations (§3.2) · `has_substeps` derived at registration · `asset_throughput_state_audit`
as the event spine.

---

## §9 — DAG elevation

Edge provenance · declared-vs-read audit · shape guards in CI (no cycles, no orphans, every
`depends_on` target active and non-DRAFT — zero dangling edges today; lock it in) · critical path
published per chart · scope explicit in the graph · blast radius on pull request.

---

## §10 — UX elevation

Never disagree with the planner (amber stale-with-data) · collapse cascades to their root · price
every action before it is taken, partition-aware · provenance panel (digests, writer version,
generation, authority, *why stale*) · honest progress with real denominators · **completeness %
and verification-tier mix per asset** · run timeline from the audit spine · service-health lane ·
multi-chart view · fix-or-remove the fake Refresh · sweep the small dishonesties.

---

## §11 — Infrastructure and database

**Not the bottleneck**: 18 of 21 levels are narrower than the worker pool; the job is already
8 Gi / 4 CPU. Ranked items and their owning phases:

| # | Item | Verdict | Phase |
|---|---|---|---|
| 1 | Real volume for the hash spill directory (`/tmp` on Cloud Run is tmpfs; zero volume mounts exist) | **DO IT** | 1 |
| 2 | Connection pooler (parallelism is capped by `runs × (1+workers) ≤ ~33`, not CPU) | HIGH | 5 |
| 3 | `chart_id` partitioning on the largest tables — `DROP PARTITION` rebuilds, structurally chart-isolated: protection by schema | HIGH | 4 |
| 4 | Autovacuum tuning on high-churn build tables | worth doing | 4 |
| 5 | Multi-dispatch continuation — in code | do it | 4 |
| 6 | Per-substep tracing and build metrics | worth doing | 6 |
| 7 | CPU/memory sizing | not the bottleneck | defer |
| 8 | Per-chart databases — **hybrid**: one shared reference DB for the 44 global assets, one per chart for L1–L5; partitioning is the migration path | later | later |
| 9 | Rehearsal chart formalised (I8) | do it | 1 |
| 10 | Determinism harness | do it | 3 |

---

## §12 — Roadmap · seven phases

Each closes only on live production verification (I4).

### Phase 0 · Pre-flight: Asset Catalogue Reconciliation *(own campaign phase; no freeze exception)*

| Step | Work |
|---|---|
| **0.1 Six-source census** | `asset_registry` · `@register()` · `asset_registry_seed.ts` · migrations · `asset_throughput` · `CAPABILITY_MANIFEST.json`. Orphans live in the gaps. |
| **0.2 Author the contract** | §3 as an enforceable per-kind specification — including `integrity_check_sql` and `target_floor` as required fields. |
| **0.3 Lifecycle + tombstone** | §3.2; `superseded_by`, `data_disposition`; no DELETEs (I6). |
| **0.4 Semantic de-duplication** | (table × generation × partition) invariant; correct the gochara attribution; declare co-writer partitions. |
| **0.5a Layer position** | 14 null + 6 malformed `layer_index` → `Lx`; `layer_name` derived. |
| **0.5b SOURCE classification** | `lel_events` → `SOURCE`. |
| **0.6a has_substeps** | 14 false negatives — derive from the writer class. |
| **0.6b Kind reconciliation** | `asset_kind` authoritative; 6 disagreements resolved. |
| **0.7 Consumer map** | Asset → serving-surface index as a required field. |
| **0.8a Build coverage audit** | Registered-but-dead flagged (`bg_gochara_citation_resolution`). |
| **0.8b catalog_status drift** | 34 DRAFT-but-served promoted or justified; CURRENT-may-not-depend-on-DRAFT enforced. |
| **0.8c Zero-consumer review** | 13 assets: record the consumer or retire with a disposition. |
| **0.9 Telemetry repair** | Close orphaned rows; recompute medians; backfill `estimated_seconds`; schedule the refresh. |
| **0.10 CI enforcement** | Three-way guard + contract conformance + prefix + edge + DRAFT-dependency invariants, merged and **blocking**. |
| **0.11 Freeze the baseline** | Tag the reconciled catalogue; later phases measure drift against it. |

**Exit criteria (all zero, verified live):** three-way diff · contract violations per kind · prefix
mismatches · dangling or DRAFT-targeted edges · multi-producer partitions · throughput rows on
inactive assets · retired assets without a disposition · active assets with neither build coverage
nor a dead flag · unresolved zero-consumer findings — **and the CI guard merged and blocking.**

### Phase 1 · Runtime truth debris and parity *(days; no freeze exception)*

Lifecycle retirement of `ka_gochara_sweep` (clears two permanent reds) · `bg_ephemeris_engine`
image fix (66-day red) · **register hand-applied migrations 588/589 with the tracked runner**
(both idempotent; the next deploy re-applies harmlessly, but the record must match) · real volume
for the spill directory · **chart 3 brought to parity and designated the rehearsal subject** (29
empty assets rebuilt there first; gets a gochara authority row) · the 5 Abhinandan-empty assets
rebuilt · the F-52 rematerialization decision recorded · `ga_prashna` zero-row and `ga_sade_sati`
57 % investigated and rebuilt.
**Acceptance:** error counts drop on all three charts; chart 3 matches the canonical charts'
asset population; every remaining red has a named owner.

### Phase 2 · Truth and safety *(days; one orchestrator deletion needs the exception)*

Amber stale-with-data · delete the duplicate cascade · persist substep totals ·
`clock_timestamp()` heartbeat · real-or-removed Refresh · state vocabulary reconciled ·
generation/authority in the UI · cascade-root collapse · service-health lane · **integrity gate
live for every data asset (§4.1); floors honest on every chart (§4.2); completeness % in the
cockpit**.
**Acceptance:** a heavy build survives a full substep without a reap; an asset whose integrity
check fails cannot reach `lit`; no asset lacks a floor.

### Phase 3 · Content-addressed freshness *(1–2 weeks; freeze exception)*

Output digests · upstream-digest freshness with early cutoff · source-content writer hash read at
plan time · graded staleness · dead staleness spec wired or deleted · **determinism harness** ·
**L1 verification-tier programme begins (§4.3)**.
**Acceptance:** identical-content upstream rebuild leaves downstream fresh, live; editing a writer
marks exactly that asset `stale:code`; harness passes for one asset per tier; `single` share at L1
measured and falling.

### Phase 4 · Receipts and robust execution *(~2 weeks; freeze exception)*

Shared `ResumableWriter` · per-substep input digests (derivation receipts, §4.5) · error taxonomy
and retry · multi-dispatch continuation · `chart_id` partitioning · autovacuum tuning · resume-run
and rebuild-failed-only.
**Acceptance:** an interrupted heavy build resumes without loss; a transient failure self-heals;
completion rate measured against the 45.6 % baseline.

### Phase 5 · DAG management *(~1 week; freeze exception)*

Edge provenance · declared-vs-read audit · critical path published · blast radius on PR ·
connection pooler.
**Acceptance:** at least one over-declared edge removed with a measured wall-clock reduction.

### Phase 6 · Operator experience *(1–2 weeks; UI only)*

Blast-radius preview · provenance panel · run timeline · failure triage · generation display ·
multi-chart view · per-substep tracing · polish sweep.
**Acceptance:** an operator can answer, without leaving the cockpit — what is stale and why, what
this costs, which fault is behind the red, what happened last run, and whether green means
complete.

---

## §13 — Plan of action for every asset, by layer

> **Superseded by v4.1 §15** — `00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md` §15 now carries the live-regenerated, single-chart per-asset plans (Track M0). This §13 copy is retained as three-chart measurement history only.

*This section is generated. Each asset carries its own three-dimension plan and benefit, derived
from its measured facts by `asset_plans.py`. The workbook's **Asset Plans** sheet is the same
derivation, so the two cannot disagree.*

<!-- ASSET_PLANS:BEGIN -->
*Generated by `build_asset_control_workbook.py` from live production measurements; identical to the workbook's **Asset Plans** sheet. Do not hand-edit between the markers.*


### L0 · Brahmagyan — 40 assets · 2 non-conformant · 0 P0 · 0 heavy

*Global reference substrate — chart-independent, built once, reused by every chart.* Publish a substrate version + content digest per asset so every chart records what it consumed. Repair the service probes — this layer holds most of them, and one sat red for 66 days. Cost here is paid once and amortises across every chart, so it is the cheapest layer to make honest.


#### `bg_ephemeris_engine` — S · Service probe · P1 · High · CURRENT

**What:** Swiss Ephemeris (pyswisseph) with DE441 JPL file providing sidereal planetary positions from 9999 BCE to 9999 CE  
**Now:** service · global state error

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout.<br>• Currently in error — repair first (Phase 1), then the probe becomes the regression guard. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `bg_panchanga` — S · Service probe · P1 · High · CURRENT

**What:** Deterministic panchang computation service (swisseph DE441, Lahiri ayanamsha, Drik-parity)  
**Now:** service · global state lit

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `bg_ghatana` — G · Global substrate · P2 · Medium · CURRENT

**What:** Life-event ontology (27 event classes keyed to LEL categories, DR-13 shape-extended 2026-07-19: point/interval/chain temporal shapes, gain-vs-loss evidence_requ  
**Now:** global · lit · 39 rows · median 3s, worst 3s

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 39 (achieved on native; floors are aspirational, never fabricated — §N.4). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 3s · p90 3s · worst 3s · 1 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_transit_rules` — G · Global substrate · P2 · Medium · CURRENT

**What:** Classical transit rules (favourable/unfavourable/vedha houses) from BPHS Ch.29 and Phaladeepika Ch.26.  
**Now:** global · lit · 75 rows / floor 50

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_class_lifetime_counts` — G · Global substrate · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W2 (ADJUDICATION-2): N_e — the expected lifetime count of each brahma_event_ontology event class over a 100-year modelled timeline from birth, assum  
**Now:** global · lit · 6 rows

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `brahma_class_priors` has 2 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_class_priors` — G · Global substrate · P3 · Standard · CURRENT

**What:** Ranked salience class-prior weights for composite query-time ranking  
**Now:** global · lit · 177 rows · median 10s, worst 10s

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 177 (achieved on native; floors are aspirational, never fabricated — §N.4). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 10s · p90 10s · worst 10s · 1 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `brahma_class_priors` has 2 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_cohort` — G · Global substrate · P3 · Standard · CURRENT

**What:** Synthetic (not real-person) reference population of ~10,000 birth charts' Lahiri-sidereal graha + Lagna positions (sign/nakshatra grain) — the statistical base-  
**Now:** global · lit · 10,000 rows / floor 10,000

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_compendium_index` — G · Global substrate · P3 · Standard · CURRENT

**What:** Cross-reference index over the 15 classical texts — chapter summaries, topic-coverage map, significance scores  
**Now:** global · lit · 9,538 rows / floor 9,538

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_concordance` — G · Global substrate · P3 · Standard · CURRENT

**What:** Cross-school chunk-pointer index per (topic, school) — chunk refs for L1+ synthesis at query-time  
**Now:** global · lit · 720 rows / floor 800

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 720 of 800 (90%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_dasha_systems` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical dasha system definitions — sequence rules, computation methods, conditions for use  
**Now:** global · lit · 20 rows / floor 18

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_dignity_reference` — G · Global substrate · P3 · Standard · CURRENT

**What:** Planetary dignity and state reference: exaltation/debilitation/own-sign boundaries, naisargika friendship matrix, avastha schemes, combustion orbs, motion state  
**Now:** global · lit · 151 rows / floor 151

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_doshas` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical dosha definitions — formation rules, effects, severity, cancellation conditions  
**Now:** global · lit · 79 rows / floor 50

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_ephemeris` — G · Global substrate · P3 · Standard · CURRENT

**What:** Swiss Ephemeris DE441 — raw astronomical positions for all grahas  
**Now:** global · lit · 825,084 rows / floor 825,084

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_formula_constants` — G · Global substrate · P3 · Standard · CURRENT

**What:** Canonical formula constants registry — combustion orbs, obstruction thresholds, magnitude tiers, dignity scores, house weights, attention budget, and engineerin  
**Now:** global · lit · 17 rows · median 2s, worst 2s

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 17 (achieved on native; floors are aspirational, never fabricated — §N.4). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 2s · worst 2s · 1 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_gochara_arcs` — G · Global substrate · P3 · Standard · CURRENT

**What:** W2G (GOCHARA-2.0, item 19)  
**Now:** global · lit · 34,553 rows / floor 34,553

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• Substep key `body`: add per-substep input digests so a partial substrate change re-runs only the affected partition.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_gochara_citation_resolution` — G · Global substrate · P3 · Standard · CURRENT

**What:** MR-25 (PARIṢKĀRA): maps gochara citation strings (gochara_grammar/citations.py constants + primitives.py families) to classical_text_chunks verse_refs  
**Now:** global · — · 14 rows / floor 4

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• No registered writer: nothing builds this asset, so there is no build cost to profile. Bound class `not-a-build` (§19.4 step 3) — hotspot is null by structure, not by omission. |
| Re-architecture & alignment | • Registered but never built: provision a writer, demote to DRAFT, or retire with a disposition (Phase 0.8a).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_kota_chakra_rings` — G · Global substrate · P3 · Standard · CURRENT

**What:** ADJUDICATION-9: the Kota-Chakra fort-chakra ring partition (stambha/durgantara/prakara/bahya, 1-indexed distance from janma nakshatra), moved from an inline wri  
**Now:** global · lit · 27 rows / floor 27

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_kp_sublord_division` — G · Global substrate · P3 · Standard · CURRENT

**What:** ADJUDICATION-7 Part 1: the canonical 249-fold Krishnamurti Paddhati sub-lord division of the sidereal zodiac  
**Now:** global · lit · 249 rows / floor 249 · median 1s, worst 1s

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 1s · worst 1s · 1 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_medical_mappings` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical Ayurvedic graha → dosha/dhatu/organ/body-part mappings per BPHS Ch.18, Ashtanga Hridayam, Charaka Samhita  
**Now:** global · lit · 21 rows / floor 9

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_muhurta_lattice` — G · Global substrate · P3 · Standard · CURRENT

**What:** Global chart-independent muhūrta factor lattice — Agnivāsa states, combination-yoga spans (Sarvārtha-siddhi, Amṛta-siddhi, Ravi/Guru-Puṣya, Tripuṣkara/Dvipuṣkar  
**Now:** global · lit · 164,886 rows / floor 91,477

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• Substep key `year:{year}`: add per-substep input digests so a partial substrate change re-runs only the affected partition.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_nakshatra` — G · Global substrate · P3 · Standard · CURRENT

**What:** Global nakshatra reference — 28 nakshatras (incl  
**Now:** global · lit · 2,857 rows / floor 2,857

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_nakshatra_medical` — G · Global substrate · P3 · Standard · CURRENT

**What:** 27 nakshatras → body-part correspondences per Ashtanga Hridayam / BPHS  
**Now:** global · lit · 27 rows / floor 27

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_ontology` — G · Global substrate · P3 · Standard · CURRENT

**What:** Canonical entity vocabulary — grahas, signs, houses, nakshatras, dashas, domains + synonyms  
**Now:** global · lit · 737 rows / floor 623

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_parihara_rules` — G · Global substrate · P3 · Standard · CURRENT

**What:** Global chart-independent parihāra (doṣa-cancellation) graph, per-activity muhūrta factor-quality rules, and the Muhūrta Factor Census + corpus-gap register  
**Now:** global · lit · 449 rows / floor 447

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_phaladeepika_latta` — G · Global substrate · P3 · Standard · CURRENT

**What:** ADJUDICATION-11 Part 4: Phaladeepika Adh  
**Now:** global · lit · 8 rows / floor 8

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_prashna_rules` — G · Global substrate · P3 · Standard · CURRENT

**What:** Static horary astrology rules — Prashna lagna methods, Tajik yogas, significators, fructification rules, and special techniques.  
**Now:** global · lit · 41 rows / floor 41

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_reference` — G · Global substrate · P3 · Standard · CURRENT

**What:** The holy grail of L0 — structured properties of every classical Jyotish concept across 15 specialized typed tables.  
**Now:** global · lit · 1,242 rows / floor 1,485

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 1,242 of 1,485 (84%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_remedies` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical remedies: mantras, gemstones, charity, vrata, yantras, puja, tantric, ayurvedic, vastu, behavioral  
**Now:** global · lit · 336 rows / floor 266

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_rules` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical rules extracted from text chunks via Python regex patterns — verse-traceable  
**Now:** global · lit · 3,003 rows / floor 2,912

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_sarvatobhadra_grid` — G · Global substrate · P3 · Standard · CURRENT

**What:** ADJUDICATION-11: school-tagged Sarvatobhadra Chakra grid reference table, registered DELIBERATELY EMPTY  
**Now:** global · lit · 0 rows

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• No registered writer: nothing builds this asset, so there is no build cost to profile. Bound class `not-a-build` (§19.4 step 3) — hotspot is null by structure, not by omission. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_sign_medical` — G · Global substrate · P3 · Standard · CURRENT

**What:** Kalapurusha (Cosmic Man) zodiacal body-map: 12 signs → body-part / organ-systems / element / dosha (BPHS Ch.4 + Ashtanga Hridayam)  
**Now:** global · lit · 12 rows / floor 12

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_sky_calendar` — G · Global substrate · P3 · Standard · CURRENT

**What:** Chart-independent global sky-event diary: sign ingresses (9 grahas), planetary stations (5 classical planets), solar/lunar eclipse timing, and Jupiter-Saturn do  
**Now:** global · lit · 31,059 rows / floor 31,064

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 31,059 of 31,064 (100%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_text_index` — G · Global substrate · P3 · Standard · CURRENT

**What:** Measurement of retrieval index health — distinct topic tags across embedded + indexed chunks  
**Now:** global · lit · 361 rows / floor 400

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 361 of 400 (90%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit.<br>• Embeddings are a deterministic transform (permitted). Pin the model id + dimension in the output digest so a model change invalidates correctly. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `classical_text_chunks` has 2 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_texts` — G · Global substrate · P3 · Standard · CURRENT

**What:** Indexed verse chunks from BPHS, Jaimini Sutram, KP Reader, Tajaka, Phaladeepika, etc.  
**Now:** global · lit · 10,667 rows / floor 10,651

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Embeddings are a deterministic transform (permitted). Pin the model id + dimension in the output digest so a model change invalidates correctly. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `classical_text_chunks` has 2 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_transit_engine` — G · Global substrate · P3 · Standard · CURRENT

**What:** L0 average graha motion parameters — daily motion, zodiac period, sign residence  
**Now:** global · lit · 9 rows / floor 9

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_vastu_directions` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical Vastu Shastra direction–graha associations: 8 compass directions each mapped to a ruling graha, secondary graha, element, favorable color, and classic  
**Now:** global · lit · 32 rows / floor 32

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_vedha_malefic_scale` — G · Global substrate · P3 · Standard · CURRENT

**What:** ADJUDICATION-11 Part 4: Phaladeepika Adh  
**Now:** global · lit · 5 rows / floor 5

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_vidhi_floors` — G · Global substrate · P3 · Standard · DRAFT

**What:** Per-intent-class acharya floor + machine band header + ordered floor items — the compiled scope_tuple->contract input (D-2 Lane V-1).  
**Now:** global · lit · 286 rows / floor 11 · median 0s, worst 1s

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 1s · worst 1s · 5 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bg_vidhi_primitives` — G · Global substrate · P3 · Standard · DRAFT

**What:** Versioned vidhi primitive atoms — definition, live-tool mapping+args, fallback face, known_gap CR pointer  
**Now:** global · lit · 52 rows / floor 48 · median 0s, worst 0s

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 0s · worst 0s · 5 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bg_yogas` — G · Global substrate · P3 · Standard · CURRENT

**What:** Classical yoga definitions — formation rules, significations, classical citations  
**Now:** global · lit · 691 rows / floor 250

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 unmeasured. Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

### L1 · Gaṇita — 19 assets · 5 non-conformant · 1 P0 · 5 heavy

*Computed chart facts — the authority every higher layer references, never restates.* The authority layer: everything above references its fact ids. Content digests here have the highest leverage in the system — a no-op L1 rebuild currently invalidates the entire DAG above it. Several writers carry substep plans and none of them can resume.


#### `ga_vichara` — H · Heavy partitioned · P0 · Blocking defect · DRAFT

**What:** Judgment layer over ga_structural: functional-lordship valence pass, varga-ratification matrix + divergence signals, continuous varga-consistency index, and lev  
**Now:** native lit · abhinandan lit · chart3 lit · rows 8,249 / 8,247 / 8,240 · median 30s, worst 36m · 25.7% of 70 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • No resume today — a 36m run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `ayanamsha_{a}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Only 25.7% of 70 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 30s · p90 15m · worst 36m · 70 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 10 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 36m of committed work.<br>• Completion rate rises from 25.7% as transient failures self-heal. |

#### `ga_dashas` — H · Heavy partitioned · P1 · High · CURRENT

**What:** Vimshottari dasha timeline: MD × AD × PD rows per ayanamsha  
**Now:** native lit · abhinandan lit · chart3 incomplete · rows 483,859 / 471,767 / 505,348 (floor 536,471) · median 10m, worst 89m · 46.3% of 121 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 483,859 of 536,471 (90%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • No resume today — a 89m run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `{system}:{aya}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 46.3% completion today.<br>• Fan-out 13: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 13 dependants.<br>• Only 46.3% of 121 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 10m · p90 48m · worst 89m · 121 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 13 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 89m of committed work.<br>• Completion rate rises from 46.3% as transient failures self-heal. |

#### `ga_positions` — M · Medium deterministic · P1 · High · CURRENT

**What:** Natal graha positions per ayanamsha (sidereal/tropical longitude, sign, nakshatra)  
**Now:** native lit · abhinandan lit · chart3 lit · rows 890 / 890 / 890 (floor 50) · median 4s, p90 58s (recorded worst 406.1h is an unclosed-run artefact — D-13) · 81.8% of 66 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer's fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.<br>• Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer's fact_keys) explicit and assert single-row-per-key in the integrity check. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 30: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 30 dependants.<br>• **Not profiled.** Measured baseline only: p50 4s · p90 58s · recorded worst 406.1h is a D-13 unclosed-run artefact · 66 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `chart_facts` has 5 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 30 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base. |

#### `ga_sade_sati` — M · Medium deterministic · P1 · High · CURRENT

**What:** Saturn transit-over-natal-Moon Sade Sati + Dhaiya window calculations per ayanamsha  
**Now:** native lit · abhinandan lit · chart3 lit · rows 6,287 / 6,280 / 6,120 (floor 11,019) · median 71s, p90 9m (recorded worst 105.2h is an unclosed-run artefact — D-13) · 40.2% of 127 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 6,287 of 11,019 (57%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.2% of 127 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 71s · p90 9m · recorded worst 105.2h is a D-13 unclosed-run artefact · 127 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.2% as transient failures self-heal. |

#### `ga_sensitive` — H · Heavy partitioned · P1 · High · CURRENT

**What:** Per-chart sensitive point positions computed from the catalog × ayanamshas  
**Now:** native lit · abhinandan lit · chart3 lit · rows 8,565 / 8,565 / 8,565 (floor 8,610) · median 4m, worst 6.4h · 61.6% of 73 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 8,565 of 8,610 (99%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit. |
| Rebuild time | • No resume today — a 6.4h run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `ayanamsha:{aya}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 61.6% completion today.<br>• **Not profiled.** Measured baseline only: p50 4m · p90 31m · worst 6.4h · 73 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 6.4h of committed work. |

#### `ga_strength` — H · Heavy partitioned · P1 · High · CURRENT

**What:** Shadbala, ashtakavarga, and bhava bala per ayanamsha  
**Now:** native lit · abhinandan lit · chart3 lit · rows 13,621 / 13,621 / 13,621 (floor 11,936) · median 2m, worst 13.1h · 65.3% of 75 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Single-shot writer (no substep plan) with p90 5m: add a `plan_substeps` partition by ayanamsha so it becomes resumable and receipt-bearing; until then any interruption is a total loss.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 65.3% completion today.<br>• Fan-out 5: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 5 dependants.<br>• **Not profiled.** Measured baseline only: p50 2m · p90 5m · worst 13.1h · 75 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 13.1h of committed work. |

#### `ga_panchanga` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** Natal panchanga (tithi, vara, nakshatra, yoga, karana) per ayanamsha  
**Now:** native lit · abhinandan lit · chart3 lit · rows 437 / 417 / 415 (floor 221) · median 3s, worst 56s · 74.6% of 67 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer's fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.<br>• Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer's fact_keys) explicit and assert single-row-per-key in the integrity check. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 5: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 5 dependants.<br>• **Not profiled.** Measured baseline only: p50 3s · p90 43s · worst 56s · 67 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `chart_facts` has 5 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base. |

#### `ga_structural` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** GA8 T1 structural layer: aspects (Parāśarī + Jaimini + Tājik), yogas, doshas, graha avasthās, argala/virodha-argala, dispositor chains, composite states, kāraka  
**Now:** native lit · abhinandan lit · chart3 lit · rows 98,542 / 98,662 / 98,446 (floor 77,821) · median 2m, worst 38m · 40.6% of 128 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{id}`) but runs in 2m — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 6: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 6 dependants.<br>• Only 40.6% of 128 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 2m · p90 3m · worst 38m · 128 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 6 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.6% as transient failures self-heal. |

#### `ga_vargas` — H · Heavy partitioned · P2 · Medium · CURRENT

**What:** D1–D60 divisional chart positions per ayanamsha  
**Now:** native lit · abhinandan lit · chart3 lit · rows 23,542 / 23,542 / 23,542 (floor 22,092) · median 2m, worst 59m · 69.6% of 69 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • No resume today — a 59m run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `ayanamsha`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Fan-out 6: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 6 dependants.<br>• **Not profiled.** Measured baseline only: p50 2m · p90 10m · worst 59m · 69 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 6 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 59m of committed work. |

#### `ga_ayurdaya` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Ayurdaya / longevity (LCA-16): ALL THREE classical methods (Pindayu, Nisargayu, Amsayu) method-attributed, with the classical applicability rule served alongsid  
**Now:** native lit · abhinandan lit · chart3 lit · rows 130 / 130 / 130 · median 4s, worst 19s · 59.1% of 22 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer's fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.<br>• Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer's fact_keys) explicit and assert single-row-per-key in the integrity check. |
| Rebuild time | • Has a substep plan (`ayanamsha_{aya}`) but runs in 4s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 4s · p90 18s · worst 19s · 22 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `chart_facts` has 5 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base. |

#### `ga_condition` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Unified dignity, avastha (baladi/jagradadi/deeptaadi/lajjitaadi/sayanadi), motion state, combustion, naisargika/tatkalika/panchadha friendship, graha yuddha, an  
**Now:** native lit · abhinandan lit · chart3 lit · rows 2,880 / 2,895 / 2,880 (floor 2,880) · median 29s, worst 5m · 50.5% of 101 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{id}`) but runs in 29s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 29s · p90 4m · worst 5m · 101 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ga_medical` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-chart Ayurvedic Jyotish indication summary: dosha aggravation, organ watch, body-part watch, and indication_strength derived from ga_condition condition_sco  
**Now:** native lit · abhinandan lit · chart3 lit · rows 45 / 45 / 45 (floor 45) · median 1s, worst 10s · 66.7% of 75 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{aya}`) but runs in 1s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 7s · worst 10s · 75 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ga_nakshatra` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-chart parallel nakshatra chart: placement+attribute JOIN from bg_nakshatra, KP sub-lords (star/sub/sub-sub/prana) per body and house cusp, the 4-limbed KP s  
**Now:** native lit · abhinandan lit · chart3 lit · rows 2,847 / 2,858 / 1,813 (floor 1,802) · median 14s, worst 7m · 72.7% of 66 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer's fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.<br>• Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer's fact_keys) explicit and assert single-row-per-key in the integrity check. |
| Rebuild time | • Has a substep plan (`ayanamsha:{ay} + cross_ayanamsha`) but runs in 14s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 14s · p90 3m · worst 7m · 66 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `chart_facts` has 5 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base. |

#### `ga_prashna` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-prashna-chart horary judgment: Prashna-Lagna by each method, querent/quesited significators, Tajik Ithasala/Eesarpha analysis, and fructification timing  
**Now:** native lit · abhinandan lit · chart3 lit · rows 0 / 0 / 0 · median 1s, worst 6s · 77.0% of 61 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• **Unearned `lit`:** throughput says lit on 3 chart(s) while the table holds zero rows — a live §N.8 specimen. The integrity gate (§4.1) must fail this; then decide: empty by design (record in `volume_explanation`, floor 0) or never built (rebuild). |
| Rebuild time | • Has a substep plan (`ayanamsha_{id}`) but runs in 1s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 4s · worst 6s · 61 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ga_sensitive_degree` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-graha sensitive-degree facts (LCA-10): mrityu-bhaga, neecha-bhanga, kartari, sarvatobhadra-vedha, khareshwara (22nd drekkana + 64th navamsa), pushkara-bhaga  
**Now:** native lit · abhinandan lit · chart3 lit · rows 275 / 275 / 275 · median 22s, worst 56s · 60.0% of 25 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer's fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.<br>• Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer's fact_keys) explicit and assert single-row-per-key in the integrity check. |
| Rebuild time | • Has a substep plan (`ayanamsha_{aya}`) but runs in 22s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 22s · p90 44s · worst 56s · 25 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • `chart_facts` has 5 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base. |

#### `ga_tajaka` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Vārṣaphal annual chart per varsha (solar-return year): Muntha position, Vārṣeśa (year-lord) by tajik_classical + panchavargiya methods with candidate scoring, a  
**Now:** native lit · abhinandan lit · chart3 lit · rows 240 / 235 / 305 (floor 240) · median 14s, worst 54s · 63.4% of 82 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 14s · p90 34s · worst 54s · 82 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ga_transit_anchors` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Natal position anchors for Gochara (transit) analysis: stores each graha's natal sign, natal degree absolute, and house-from-Moon for each ayanamsha  
**Now:** native lit · abhinandan lit · chart3 lit · rows 45 / 45 / 45 (floor 45) · median 1s, worst 13s · 77.0% of 61 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{aya}`) but runs in 1s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 8s · worst 13s · 61 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ga_vastu` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Maps each classical graha to its ruling Vastu direction (per bg_vastu_directions) and computes direction_impact (weakened / neutral / strengthened) using condit  
**Now:** native lit · abhinandan lit · chart3 lit · rows 40 / 40 / 40 (floor 40) · median 1s, worst 14s · 66.7% of 75 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{id}`) but runs in 1s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 7s · worst 14s · 75 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ga_yoga` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-chart yoga firing table: evaluates classical Nabhasa and other yoga formation rules against L1 chart_facts  
**Now:** native lit · abhinandan lit · chart3 lit · rows 63 / 69 / 80 (floor 5) · median 6s, worst 36m · 42.5% of 120 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Has a substep plan (`ayanamsha_{a}`) but runs in 6s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 42.5% of 120 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 6s · p90 22s · worst 36m · 120 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 42.5% as transient failures self-heal. |

### L2 · Bodha — 22 assets · 9 non-conformant · 7 P0 · 2 heavy

*Derivation & synthesis — signals, mechanisms, contradictions, gestalt.* Broad, shallow and cheap per asset, but deep in fan-out. The win is early cutoff: most L2 rebuilds produce identical rows and should stop propagating.


#### `bo_arudha` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Arudha Lagna bhava-relation, AL conjunctions, and A2/A11 (dhana/labha arudha) tenancy — pure L2 derivation over existing ga_structural/ga_positions facts; emits  
**Now:** native lit · abhinandan lit · chart3 lit · rows 25 / 24 / 20 (floor 15) · median 1s, worst 8s · 68.4% of 19 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 7s · worst 8s · 19 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_laksana_rerank` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Post-CGM structural re-rank pass: writes real CGM centrality (pagerank/eigenvector/betweenness/harmonic) onto each MSR signal's graph_node_strength_contribution  
**Now:** native lit · abhinandan lit · chart3 stale · rows 10,824 / 10,868 / 100 (floor 1) · median 4m, worst 21m · 63.6% of 22 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Partitioned by ayanamsha (`aya_{ayanamsha}`, 5 substeps). Per-substep input digests mean an ephemeris or single-ayanamsha change re-runs one partition, not five.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 4m · p90 20m · worst 21m · 22 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_nakshatra_semantic` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Own-star identity, dispositor chain, tara bala, and gandanta/end-degree flagging per graha — pure L2 derivation over existing ga_positions/ga_nakshatra facts; e  
**Now:** native lit · abhinandan lit · chart3 lit · rows 45 / 45 / 45 (floor 45) · median 1s, worst 12s · 82.4% of 17 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 10s · worst 12s · 17 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_special_lagna` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Domain-scoped corroboration from the four canonical special/upapada lagnas (Indu, Sree, Ghati, Hora) — pure L2 derivation over existing ga_sensitive facts; emit  
**Now:** native lit · abhinandan lit · chart3 lit · rows 20 / 20 / 20 (floor 20) · median 0s, worst 9s · 68.8% of 16 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 4s · worst 9s · 16 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_sudarshana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Tri-frame (Lagna/Chandra/Sūrya) house assignment per graha — pure L2 derivation over existing ga_positions facts; emits sudarshana_agreement MSR signals (confir  
**Now:** native lit · abhinandan lit · chart3 lit · rows 45 / 45 / 45 (floor 45) · median 1s, worst 10s · 78.6% of 14 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 10s · worst 10s · 14 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_vargottama_dhana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Cross-frame (D1/D9) vargottama confirmation and complete 2nd/11th-house (dhana/labha) tenancy analysis — pure L2 derivation over existing ga_vargas/ga_positions  
**Now:** native lit · abhinandan lit · chart3 lit · rows 14 / 16 / 15 (floor 10) · median 1s, worst 8s · 80.0% of 15 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 7s · worst 8s · 15 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 36 serving surface(s), so it is authoritative in practice.<br>• `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_yantra_mechanism` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Named, valenced CGM subgraph — promotes CGM motifs + dispositor/house-lordship chain-and-circuit detection into first-class mechanisms with real edge-strength p  
**Now:** native lit · abhinandan lit · chart3 stale · rows 615 / 633 / 620 (floor 1) · median 13s, worst 2m · 68.2% of 22 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 13s · p90 2m · worst 2m · 22 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 8 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_laksana` — H · Heavy partitioned · P1 · High · CURRENT

**What:** MARSYS Signal Register — grounded signals derived from exhaustive L1 structural enumeration (ga_structural) × L1 chart_facts; primary table bodha_msr_signals  
**Now:** native lit · abhinandan lit · chart3 lit · rows 49,955 / 50,021 / 49,730 (floor 60,000) · median 3m, worst 19.2h · 41.2% of 136 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 49,955 of 60,000 (83%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit.<br>• §N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer's natural-key partition of the shared table so co-writers cannot overwrite each other. |
| Rebuild time | • No resume today — a 19.2h run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `aya_{ayanamsha}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 41.2% completion today.<br>• Fan-out 20: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 20 dependants.<br>• Only 41.2% of 136 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 3m · p90 21m · worst 19.2h · 136 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • `bodha_msr_signals` has 7 co-writers: declare this writer's natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 20 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 19.2h of committed work.<br>• Completion rate rises from 41.2% as transient failures self-heal. |

#### `bo_samskara` — H · Heavy partitioned · P1 · High · CURRENT

**What:** Vertex AI 768-dim vector embeddings — one per MSR signal  
**Now:** native lit · abhinandan lit · chart3 lit · rows 50,104 / 50,102 / 49,875 (floor 60,000) · median 13m, worst 2.6h · 43.7% of 103 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Below floor: 50,104 of 60,000 (84%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit.<br>• Embeddings are a deterministic transform (permitted). Pin the model id + dimension in the output digest so a model change invalidates correctly. |
| Rebuild time | • No resume today — a 2.6h run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.<br>• Partition key `aya_{ayanamsha}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 43.7% completion today.<br>• Only 43.7% of 103 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 13m · p90 25m · worst 2.6h · 103 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 2.6h of committed work.<br>• Completion rate rises from 43.7% as transient failures self-heal. |

#### `bo_bimba` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** CGM node registry — one node per signal; carries composite_centrality, pagerank, betweenness, VECTOR(768) embedding and igraph-computed metrics  
**Now:** native lit · abhinandan lit · chart3 lit · rows 385 / 356 / 360 (floor 140) · median 16s, worst 73s · 40.5% of 126 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 8: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 8 dependants.<br>• Only 40.5% of 126 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 16s · p90 38s · worst 73s · 126 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 8 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.5% as transient failures self-heal. |

#### `bo_karanajala` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** Causal Graph Model — valenced directed edges between CGM nodes; pre-computed igraph metrics stored as flat columns  
**Now:** native lit · abhinandan lit · chart3 lit · rows 849 / 838 / 830 (floor 300) · median 18s, worst 18m · 40.9% of 127 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 10: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 10 dependants.<br>• Only 40.9% of 127 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 18s · p90 2m · worst 18m · 127 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 10 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.9% as transient failures self-heal. |

#### `bo_pratijna` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** Per-event-class promise registry: promised/denied/conditional verdicts with grade, supporting and contradicting signal IDs, varga confirmation, derivation audit  
**Now:** native lit · abhinandan lit · chart3 lit · rows 135 / 135 / 135 · median 16s, worst 71s · 37.3% of 118 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 5: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 5 dependants.<br>• Only 37.3% of 118 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 16s · p90 36s · worst 71s · 118 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 37.3% as transient failures self-heal. |

#### `bo_sangati` — M · Medium deterministic · P2 · Medium · CURRENT

**What:** Cross-Domain Linkage Matrix — computed_linkage cells, domain rollups, pattern clusters, evolution gradients; primary table bodha_cdlm_cells  
**Now:** native lit · abhinandan lit · chart3 lit · rows 280 / 75 / 75 (floor 70) · median 12s, worst 25m · 39.7% of 126 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Cross-chart asymmetry (280 vs 75): confirm it is chart-driven, not a partial build on one chart. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 12: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 12 dependants.<br>• Only 39.7% of 126 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 12s · p90 35s · worst 25m · 126 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 12 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.7% as transient failures self-heal. |

#### `bo_anveshana` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Discovery engine: non-obviousness + graph-mining + embedding outliers + bodha_discoveries + anomalies.  
**Now:** native lit · abhinandan lit · chart3 stale · rows 3,774 / 4,909 / 5,222 (floor 500) · median 31s, worst 9m · 41.6% of 101 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 41.6% of 101 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 31s · p90 3m · worst 9m · 101 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 41.6% as transient failures self-heal. |

#### `bo_cdlm_summary` — M · Medium deterministic · P3 · Standard · DRAFT

**What:** Per-chart cross-domain linkage strength summary aggregated from bodha_cdlm_cells  
**Now:** native lit · abhinandan lit · chart3 stale · rows 5 / 5 / 5 (floor 1) · median 1s, worst 17s · 53.1% of 81 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 10s · worst 17s · 81 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `bo_cgm_motifs` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Recurring structural patterns detected over the CGM graph: mutual reception, stellium, parivartana chains  
**Now:** native lit · abhinandan lit · chart3 stale · rows 600 / 606 / 605 · median 3s, worst 2m · 37.4% of 123 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 37.4% of 123 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 3s · p90 66s · worst 2m · 123 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 37.4% as transient failures self-heal. |

#### `bo_cgm_paths` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Dispositor chain paths and structural path analysis over CGM graph  
**Now:** native lit · abhinandan lit · chart3 stale · rows 45 / 45 / 45 (floor 9) · median 2s, worst 20m · 56.2% of 80 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 10s · worst 20m · 80 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bo_chart_gestalt` — M · Medium deterministic · P3 · Standard · DRAFT

**What:** Per-chart gestalt: defining threads, central dynamics, domain verdict map, zoom spine — pointer-only, no verdicts stored  
**Now:** native lit · abhinandan lit · chart3 stale · rows 5 / 5 / 5 (floor 1) · median 2s, worst 53s · 40.0% of 95 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.0% of 95 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 12: sits in the serial tail. Audit its 5 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 9s · worst 53s · 95 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 40.0% as transient failures self-heal. |

#### `bo_drishti` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Question-lens table: template + wildcard graph-sweep + ranks-never-caps, per question domain.  
**Now:** native lit · abhinandan lit · chart3 stale · rows 60 / 60 / 60 (floor 60) · median 2m, worst 15m · 55.3% of 85 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 2m · p90 3m · worst 15m · 85 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `bo_pramana_mapa` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-build synthesis quality scorecard — citation density, whole-chart coverage, derivation compliance, layer separation score; keyed by (chart_id, build_id)  
**Now:** native stale · abhinandan lit · chart3 error · rows 1 / 1 / 1 (floor 1) · median 4s, worst 28s · 42.2% of 102 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 42.2% of 102 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 12: sits in the serial tail. Audit its 8 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 4s · p90 19s · worst 28s · 102 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 42.2% as transient failures self-heal. |

#### `bo_samvada` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** UCD — read-side conceptual digest (join of A8/A11/A12/A13 chart_summaries via vw_chart_digest + query_ucd)  
**Now:** native stale · abhinandan lit · chart3 error · rows 5 / 5 / 5 (floor 5) · median 0s, worst 2s · 42.6% of 101 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 42.6% of 101 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 13: sits in the serial tail. Audit its 5 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 2s · 101 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 42.6% as transient failures self-heal. |

#### `bo_upaya` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Remediation Map — ALL 6 RM tables; primary table bodha_rm_resonances (resonance targets that remedies key off) + bodha_rm_remedy_prescriptions + 4 ancillary tab  
**Now:** native lit · abhinandan lit · chart3 error · rows 180 / 180 / 180 (floor 180) · median 9s, worst 17m · 38.9% of 131 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 38.9% of 131 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 9s · p90 68s · worst 17m · 131 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 38.9% as transient failures self-heal. |

### L3 · Kāla — 23 assets · 8 non-conformant · 8 P0 · 2 heavy

*Time — dashas, transits, windows, the field; the heaviest layer by compute.* Where the wall-clock lives. Two assets have individually exceeded 33 hours. Partition receipts and shared resumability convert interruption from total loss into bounded rework, and the generation/authority model belongs here.


#### `ka_bhavishya_lekha` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Probabilistic forward projections (3-year horizon)  
**Now:** native lit · abhinandan lit · chart3 error · rows 100 / 100 / 0 · median 0s, worst 2s · 37.8% of 127 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 100 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 4 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 37.8% of 127 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 15: sits in the serial tail. Audit its 4 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 2s · 127 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 6 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 37.8% as transient failures self-heal. |

#### `ka_gochara_sweep` — X · Generation-bearing · P0 · Blocking defect · SUPERSEDED_BY

**What:** D-5 Lane G-4: birth->birth+100y daily-grid gochara (transit) intensity sweep (lambda_e via G-3's services/gochara_intensity), shape-aware (point/interval/chain   
**Now:** native error · abhinandan error · chart3 error · rows 16,297 / 19,323 / 2,667 · median 2.1h, worst 35.6h · 9.6% of 94 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `one authoritative generation per chart via kala_gochara_authority; no window with end < start`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• RETIRED and unrebuildable: no registered writer. Correctness = the verified 2026-08-23 snapshot; chart 3 still serves these v1 rows (no authority row). Record `data_disposition = RETAINED_AS_CAPITAL`. |
| Rebuild time | • Has a substep plan (`{event_class}:year:{idx}`) but runs in 2.1h — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 9.6% of 94 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 2.1h · p90 6.0h · worst 35.6h · 94 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Lifecycle: execute the supported retire operation — clear residual throughput rows, set `superseded_by` and `data_disposition`; never DELETE the registry row (I6).<br>• Generation-bearing: model generation + per-chart authority as first-class registry/UI concepts; one count and one freshness per generation (Phase 2). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 9.6% as transient failures self-heal. |

#### `ka_jivana_parva` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Life-arc biographical chapter artifact  
**Now:** native lit · abhinandan lit · chart3 stale · rows 100 / 100 / 109 · median 0s, worst 3s · 36.3% of 124 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 100 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Derivation ledger: 5 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 36.3% of 124 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 15: sits in the serial tail. Audit its 5 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 3s · 124 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 5 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 36.3% as transient failures self-heal. |

#### `ka_kala_darshana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Display-ready temporal view  
**Now:** native lit · abhinandan lit · chart3 stale · rows 750 / 750 / 0 · median 0s, worst 4s · 39.3% of 122 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 750 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.3% of 122 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 14: sits in the serial tail. Audit its 3 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 3s · worst 4s · 122 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 4 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.3% as transient failures self-heal. |

#### `ka_kalasutra` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Bounded activation artifact (1 row per signal×ayanamsha)  
**Now:** native lit · abhinandan lit · chart3 stale · rows 335,403 / 336,093 / 1,055 · median 33s, worst 41m · 39.8% of 123 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 335,403 (achieved on native; floors are aspirational, never fabricated — §N.4). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.8% of 123 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 13: sits in the serial tail. Audit its 3 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 33s · p90 11m · worst 41m · 123 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 12 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.8% as transient failures self-heal. |

#### `ka_sangam` — H · Heavy partitioned · P0 · Blocking defect · DRAFT

**What:** Rigor-scored intersection windows (Mode A daśā-prior funnel + Mode B off-daśā sweep)  
**Now:** native lit · abhinandan lit · chart3 stale · rows 14,868 / 17,957 / 2,540 · median 8m, worst 2.8h · 43.1% of 116 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 14,868 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Derivation ledger: 10 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Private resume copy with a hand-bumped `_RESUME_VERSION`: migrate to the shared mixin and replace the whole-build fingerprint with per-substep INPUT digests, so a mismatch replans only the changed partitions instead of everything.<br>• Partition key `near + lifetime:{i}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 43.1% completion today.<br>• Fan-out 11: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 11 dependants.<br>• Only 43.1% of 116 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 12: sits in the serial tail. Audit its 10 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 8m · p90 40m · worst 2.8h · 116 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 4 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 11 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 2.8h of committed work.<br>• Completion rate rises from 43.1% as transient failures self-heal. |

#### `ka_vighnakara` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Obstruction/counter-indicator detector  
**Now:** native lit · abhinandan lit · chart3 stale · rows 536 / 741 / 6 · median 14s, worst 32m · 40.2% of 117 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 536 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Derivation ledger: 4 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 5: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 5 dependants.<br>• Only 40.2% of 117 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 13: sits in the serial tail. Audit its 4 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 14s · p90 31s · worst 32m · 117 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 3 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 5 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.2% as transient failures self-heal. |

#### `ka_yojaka` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Classifies each L2 signal into a signature_class, binds the RATIFIED class template, stores concrete activation predicates for ka_sangam/ka_vighnakara to search  
**Now:** native lit · abhinandan lit · chart3 error · rows 50,104 / 50,171 / 49,875 · median 36s, worst 2m · 49.0% of 104 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 50,104 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Derivation ledger: 7 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 49.0% of 104 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 36s · p90 77s · worst 2m · 104 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 4 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 49.0% as transient failures self-heal. |

#### `ka_dasha_kala` — S · Service probe · P1 · High · DRAFT

**What:** Lazy-pruning tree-walk over chart_dashas (level-4 Sookshma) with cross-system agreement scoring  
**Now:** service · global state n/a · median 1s, worst 26s · 42.3% of 111 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `ka_gochara` — X · Generation-bearing · P1 · High · CURRENT

**What:** Primary per-chart gochara window materializer (GOCHARA-UTKARSA)  
**Now:** native lit · abhinandan lit · chart3 — · rows 943 / 941 / 0 · median 0s, worst 6.5h · 54.1% of 61 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `one authoritative generation per chart via kala_gochara_authority; no window with end < start`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• F-52 consequence: every materialized v2 row is stale under the live scoring signature and no rebuild has been dispatched — rematerialize under the determinism harness, or mark stale honestly in the UI. |
| Rebuild time | • Has a substep plan (`event_class`) but runs in 0s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 6.5h · 61 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Generation-bearing: model generation + per-chart authority as first-class registry/UI concepts; one count and one freshness per generation (Phase 2).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ka_graha_sancara` — S · Service probe · P1 · High · DRAFT

**What:** Ephemeris-at-T service: sidereal positions for all 9 grahas at any datetime  
**Now:** service · global state lit · median 0s, worst 2s · 54.2% of 59 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `ka_kshetra` — H · Heavy partitioned · P1 · High · CURRENT

**What:** ṢAḌ-DARŚANA W2: the ten-stage point-process temporal field  
**Now:** native stale · abhinandan lit · chart3 error · rows 8,599,775 / 2,412,882 / 0 · median 39m, worst 33.8h · 11.9% of 126 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Cross-chart asymmetry (8,599,775 vs 2,412,882): confirm it is chart-driven, not a partial build on one chart.<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 8 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• DHARA engine (analytic) replaced the sampled engine mid-August; `_RESUME_VERSION` is at 7. Add a build-twice determinism check at the stage level — the content hash (F-149) already exists, so compare digests across two clean builds. |
| Rebuild time | • Private resume copy with a hand-bumped `_RESUME_VERSION`: migrate to the shared mixin and replace the whole-build fingerprint with per-substep INPUT digests, so a mismatch replans only the changed partitions instead of everything.<br>• Partition key `stage{n}:{event_class}:{slice}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.<br>• Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.<br>• Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — 11.9% completion today.<br>• Only 11.9% of 126 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 39m · p90 2.2h · worst 33.8h · 126 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 names this among the ten heavy assets where the efficiency pass concentrates. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Interruption stops costing up to 33.8h of committed work.<br>• Completion rate rises from 11.9% as transient failures self-heal. |

#### `ka_muhurta_seva` — S · Service probe · P1 · High · DRAFT

**What:** Deterministic panchāṅga/muhūrta scoring service  
**Now:** service · global state lit · median 0s, worst 4s · 54.2% of 59 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).<br>• Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `ka_tulana` — S · Service probe · P1 · High · DRAFT

**What:** Serve-time QT-4 ranking engine  
**Now:** service · global state n/a · median 0s, worst 1s · 37.3% of 118 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `ka_avadhi` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Per-dasha-period dossiers: for each chart, dasha system, MD/AD/PD level, stores lord condition (refs to chart_facts), activated promise-register IDs (from bodha  
**Now:** native lit · abhinandan lit · chart3 error · rows 1,169 / 1,160 / 1,291 · median 14s, worst 15m · 45.3% of 95 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 45.3% of 95 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• **Not profiled.** Measured baseline only: p50 14s · p90 26s · worst 15m · 95 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 45.3% as transient failures self-heal. |

#### `ka_gochara_resonance` — X · Generation-bearing · P3 · Standard · CURRENT

**What:** D-5 Lane G-1: per-chart x event-class classical-prior-weighted target sets (bhavas, lords, karakas, mechanism nodes, sensitive degrees, arudhas, yoga constituen  
**Now:** native lit · abhinandan lit · chart3 lit · rows 762 / 750 / 77 · median 0s, worst 17s · 78.3% of 23 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `one authoritative generation per chart via kala_gochara_authority; no window with end < start`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 17s · worst 17s · 23 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Generation-bearing: model generation + per-chart authority as first-class registry/UI concepts; one count and one freshness per generation (Phase 2).<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ka_gochara_v3_century_materialize` — X · Generation-bearing · P3 · Standard · CURRENT

**What:** GOCHARA-UTKARSA W3.4 heavy writer: plan_substeps returns 60 substeps (6 event classes x 10 decade slices spanning birth-century 1984-2084)  
**Now:** native error · abhinandan stale · chart3 — · rows 914 / 916 / 0 · median 2m, worst 58m

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `one authoritative generation per chart via kala_gochara_authority; no window with end < start`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 6 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• F-52 consequence: every materialized v2 row is stale under the live scoring signature and no rebuild has been dispatched — rematerialize under the determinism harness, or mark stale honestly in the UI. |
| Rebuild time | • Has a substep plan (`{event_class}::{decade}`) but runs in 2m — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 2m · p90 34m · worst 58m · 7 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Generation-bearing: model generation + per-chart authority as first-class registry/UI concepts; one count and one freshness per generation (Phase 2).<br>• No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.<br>• Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ka_kota_chakra` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W3 item 16: transiting grahas mapped to the kota's stambha/durgantara/prakara/bahya rings relative to the janma nakshatra, with entry/exit windows a  
**Now:** native lit · abhinandan dormant · chart3 — · rows 588 / 585 / 0 · median 1s, worst 3s · 27.3% of 11 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 3s · worst 3s · 11 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ka_moorti_nirnaya` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W3 item 4: the classical gold/silver/copper/iron quality of a transiting graha's stay in a sign, determined by the Moon's nakshatra at the moment of  
**Now:** native lit · abhinandan lit · chart3 — · rows 72 / 72 / 0 · median 1s, worst 4s · 33.3% of 12 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 3s · worst 4s · 12 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ka_sudarshana_varsha` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W3 item 17: the rotating annual house-per-year progression of the tri-lagna framework (Janma/Chandra/Sūrya Lagna), full 120-year lifespan  
**Now:** native lit · abhinandan — · chart3 — · rows 120 / 0 / 0 · median 2s, worst 2s

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 2s · worst 2s · 6 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `ka_taranga` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** Monthly activation waveform (1950–2100): convolution of dasha × transit × promise for each domain and event class  
**Now:** native lit · abhinandan lit · chart3 error · rows 92,412 / 92,412 / 92,412 · median 22s, worst 41m · 39.4% of 109 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Derivation ledger: 5 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.4% of 109 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 13: sits in the serial tail. Audit its 5 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 22s · p90 54s · worst 41m · 109 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 39.4% as transient failures self-heal. |

#### `ka_tithi_pravesha` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W3 item 13: the lunar-return counterpart to Tājika Vārṣaphala (ga_tajaka) — the annual chart cast for the instant the transiting Moon returns to its  
**Now:** native lit · abhinandan lit · chart3 — · rows 120 / 120 / 0 · median 2s, worst 2s · 33.3% of 12 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 2s · worst 2s · 12 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `ka_vedha_gochara` — M · Medium deterministic · P3 · Standard · CURRENT

**What:** ṢAḌ-DARŚANA W3 item 5 (closes R-19, CLOSED-PARTIAL-BY-DESIGN per ADJUDICATION-11): three classical vedha (obstruction) mechanisms applied to a chart's currently  
**Now:** native lit · abhinandan dormant · chart3 — · rows 176 / 178 / 0 · median 3s, worst 3s · 27.3% of 11 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 6 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 3s · p90 3s · worst 3s · 11 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

### L4 · Phala — 9 assets · 9 non-conformant · 9 P0 · 0 heavy

*Deterministic outcome shaping — phala, remedies, rectification.* Deterministic and inexpensive, but structurally serial — it sits at DAG depths 16–20 and gates all of L5. The win is edge hygiene: removing declared-but-unread dependencies shortens the critical path.


#### `ph_muhurta` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Personalized auspicious windows: chart-strength + live-transit scored, personal-danger-avoiding, prediction-fused (rides ph_nimitta windows), honest no-good-win  
**Now:** native lit · abhinandan lit · chart3 — · rows 134 / 49 / 0 · median 1s, worst 38s · 43.0% of 107 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 134 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 8 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 43.0% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 17: sits in the serial tail. Audit its 8 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 14s · worst 38s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 4 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 43.0% as transient failures self-heal. |

#### `ph_nimitta` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Predictive anchors: 8 derivation axes (graph-causal, discovery-seeded, embedding-precedent, dāśā+school consensus, ayanāṃśa-robustness, subsystem) + 5 elevation  
**Now:** native lit · abhinandan lit · chart3 error · rows 139 / 56 / 0 · median 2s, worst 68s · 42.2% of 109 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 139 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 9 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Fan-out 10: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all 10 dependants.<br>• Only 42.2% of 109 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 16: sits in the serial tail. Audit its 9 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 46s · worst 68s · 109 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 16 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 10 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 42.2% as transient failures self-heal. |

#### `ph_phaladesa` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Domain result declaration: 7 domains × 1 row  
**Now:** native stale · abhinandan lit · chart3 error · rows 13 / 13 / 0 · median 1s, worst 8s · 39.1% of 110 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 13 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 7 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.1% of 110 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 20: sits in the serial tail. Audit its 7 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 6s · worst 8s · 110 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.1% as transient failures self-heal. |

#### `ph_pramana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Unified machine-evaluable falsifiers for every L4 prediction + the L5 onboarding contract + evaluation-staging (no scoring) + portfolio/reverse-calibration chan  
**Now:** native stale · abhinandan lit · chart3 — · rows 139 / 56 / 0 · median 1s, worst 38s · 40.2% of 107 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 139 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 6 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.2% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 19: sits in the serial tail. Audit its 6 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 17s · worst 38s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.2% as transient failures self-heal. |

#### `ph_pratikara` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Managed remedy program: economics/feasibility tiers, sequenced+conflict-free schedule, muhūrta-timed initiation, severity-proportional, cross-tradition choice,   
**Now:** native stale · abhinandan lit · chart3 — · rows 536 / 741 / 0 · median 3s, worst 73s · 43.0% of 107 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 536 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 4 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose). |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 43.0% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 17: sits in the serial tail. Audit its 4 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 3s · p90 52s · worst 73s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 6 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 43.0% as transient failures self-heal. |

#### `ph_rectification` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Birth-time rectification via PyJHora ascendant scan (±90 min, 5-min steps, 5 ayanamshas) scored against pre-2020 LEL events  
**Now:** native lit · abhinandan lit · chart3 — · rows 186 / 186 / 0 · median 1s, worst 34s · 43.0% of 107 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 186 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 43.0% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 17: sits in the serial tail. Audit its 1 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 20s · worst 34s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 3 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 43.0% as transient failures self-heal. |

#### `ph_sankrama` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Grounded multi-hop cross-domain dynamics: lag from real activation windows + graph-bridge mechanism, A→B→C cascades, cross-domain conflicts, trajectory + mitiga  
**Now:** native lit · abhinandan lit · chart3 — · rows 2,510 / 475 / 0 · median 4s, worst 4m · 43.0% of 107 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 2,510 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Cross-chart asymmetry (2,510 vs 475): confirm it is chart-driven, not a partial build on one chart.<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 43.0% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 17: sits in the serial tail. Audit its 2 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 4s · p90 2m · worst 4m · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 3 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 43.0% as transient failures self-heal. |

#### `ph_sodhana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Anomaly registry: 5 deterministic detectors (confidence inflation, magnitude drift, falsifier absent, ledger gap, layer leakage)  
**Now:** native lit · abhinandan lit · chart3 — · rows 97 / 41 / 0 · median 0s, worst 11s · 40.2% of 107 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 97 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.2% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 17: sits in the serial tail. Audit its 2 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 5s · worst 11s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.2% as transient failures self-heal. |

#### `ph_suddha_sodhana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Cleansed disposition: one row per phala_anchors entry, classified as clean/flagged/staged_revision  
**Now:** native lit · abhinandan lit · chart3 — · rows 139 / 56 / 0 · median 1s, worst 32s · 40.2% of 107 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 139 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.2% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 18: sits in the serial tail. Audit its 2 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 11s · worst 32s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 1 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.2% as transient failures self-heal. |

### L5 · Mīmāṃsā — 15 assets · 10 non-conformant · 10 P0 · 0 heavy

*Calibration & judgment — prediction/outcome loop, scoring, review.* The deepest and most cascade-prone layer: eight of its assets were recently blocked by a single upstream fault. Cascade-root collapse and honest partial states matter more here than raw speed.


#### `mi_abhilekha` — S · Service probe · P0 · Blocking defect · DRAFT

**What:** Journal + re-sync service: surfaces due predictions for native feedback, ingests answers as LEL events, triggers L5-only recompute  
**Now:** service · global state n/a · median 0s, worst 2s · 42.6% of 94 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 1 serving surface(s), so it is authoritative in practice.<br>• Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `mi_adhilepa` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** L5 learned-weight overlay on L1–L4 base values; 4 adjustment tables + load-bearing sensitivity map (G3)  
**Now:** native error · abhinandan lit · chart3 error · rows 112,270 / 112,481 / 0 · median 10s, worst 14m · 39.3% of 107 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 5 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.3% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 24: sits in the serial tail. Audit its 5 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 10s · p90 24s · worst 14m · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 1 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.3% as transient failures self-heal. |

#### `mi_bhavisya` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Time-indexed prospective predictions with confidence + falsifiers  
**Now:** native error · abhinandan lit · chart3 — · rows 278 / 112 / 0 · median 2s, worst 16s · 41.0% of 105 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 6 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 41.0% of 105 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 21: sits in the serial tail. Audit its 6 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 6s · worst 16s · 105 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 8 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 41.0% as transient failures self-heal. |

#### `mi_darshana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** LLM-ready pre-composed insight units with embeddings + provenance chains + trust metadata (R1–R6)  
**Now:** native error · abhinandan lit · chart3 error · rows 115 / 35 / 0 · median 1s, worst 6s · 36.1% of 108 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Cross-chart asymmetry (115 vs 35): confirm it is chart-driven, not a partial build on one chart.<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 8 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.<br>• §N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose).<br>• Embeddings are a deterministic transform (permitted). Pin the model id + dimension in the output digest so a model change invalidates correctly. |
| Rebuild time | • Has a substep plan (`insight_units \| embeddings`) but runs in 1s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 36.1% of 108 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 25: sits in the serial tail. Audit its 8 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 5s · worst 6s · 108 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 4 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• Completion rate rises from 36.1% as transient failures self-heal. |

#### `mi_gunanaka` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Empirical multiplier weights learned from calibration outcomes  
**Now:** native error · abhinandan lit · chart3 — · rows 13 / 10 / 0 · median 0s, worst 2s · 41.1% of 107 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 41.1% of 107 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 23: sits in the serial tail. Audit its 3 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 2s · 107 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 7 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 41.1% as transient failures self-heal. |

#### `mi_kula` — G · Global substrate · P0 · Blocking defect · DRAFT

**What:** Signal-family registry + negative-control battery — the governing catalogue of what influences a reading  
**Now:** global · lit · 15 rows · median 0s, worst 2s · 88.4% of 43 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8). |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 1s · worst 2s · 43 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 1 serving surface(s), so it is authoritative in practice.<br>• Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `mi_pariksha` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Answer quality evaluation runs — automated + human QA over synthesis outputs  
**Now:** native error · abhinandan lit · chart3 error · rows 1,664 / 6 / 0 · median 2s, worst 33s · 39.6% of 106 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Cross-chart asymmetry (1,664 vs 6): confirm it is chart-driven, not a partial build on one chart.<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Has a substep plan (`retrodiction \| control_windows \| …(7)`) but runs in 2s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 39.6% of 106 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 23: sits in the serial tail. Audit its 3 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 9s · worst 33s · 106 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 2 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 39.6% as transient failures self-heal. |

#### `mi_pramana` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Prediction outcome calibration records — confidence score vs outcome mapping  
**Now:** native error · abhinandan lit · chart3 — · rows 63 / 0 / 0 · median 0s, worst 4s · 41.0% of 105 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.<br>• Derivation ledger: 4 declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it. |
| Rebuild time | • Has a substep plan (`match \| score \| …(3)`) but runs in 0s — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.<br>• Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 41.0% of 105 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 22: sits in the serial tail. Audit its 4 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 4s · worst 4s · 105 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 11 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 4 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 41.0% as transient failures self-heal. |

#### `mi_sambandha` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Per-native grammar of how each signal/house/karaka expresses — which channel fires for THIS person (G2)  
**Now:** native error · abhinandan lit · chart3 — · rows 24 / 23 / 0 · median 0s, worst 5s · 40.0% of 105 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• Only 40.0% of 105 attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.<br>• DAG depth 24: sits in the serial tail. Audit its 3 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 5s · 105 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 1 direct dependant(s) stop invalidating when this asset rebuilds to identical content.<br>• Completion rate rises from 40.0% as transient failures self-heal. |

#### `mi_sankalpa` — M · Medium deterministic · P0 · Blocking defect · DRAFT

**What:** Unified intervention ledger — every elected act (upāya · yajña · elected activity) with its adjudication record, predicted differential, performance attestation  
**Now:** native dormant · abhinandan — · chart3 — · rows 0 / 0 / 0 · median 1s, worst 2s · 50.0% of 10 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Zero rows on the native chart. Either the asset is empty by design (record it in `volume_explanation`) or it has never been built — the cockpit must not render this as lit. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• DAG depth 12: sits in the serial tail. Audit its 1 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 1s · p90 2s · worst 2s · 10 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by 2 serving surface(s), so it is authoritative in practice. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `mi_seva` — S · Service probe · P1 · High · DRAFT

**What:** Serve-time contribution-control gateway: effective-value resolution, toggle gates, transit-current binding, MCP parity  
**Now:** service · global state n/a · median 0s, worst 2s · 40.2% of 97 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer query and compare against a pinned expected value; alert on drift or timeout. |
| Rebuild time | • Not a build; nothing to speed up. Exclude from build plans and ETA math. |
| Re-architecture & alignment | • Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null. |
| Expected benefit | • A degraded service surfaces in minutes, not months (one sat red for 66 days). |

#### `lel_events` — M · Medium deterministic · P3 · Standard · SOURCE

**What:** Per-chart user-authored life-event corpus (occurrence + recording dates, chart-state index)  
**Now:** native — · abhinandan — · chart3 — · rows 64 / 0 / 0

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • No completed-run telemetry: p50 and p90 are both unmeasured, so even the §19.4 build-cost baseline is null here — measure before planning anything.<br>• No registered writer: nothing builds this asset, so there is no build cost to profile. Bound class `not-a-build` (§19.4 step 3) — hotspot is null by structure, not by omission. |
| Re-architecture & alignment | • Contract-conformant. Inherits the platform-wide changes: content digest, graded staleness, shared resumability. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `mi_bhara` — M · Medium deterministic · P3 · Standard · DRAFT

**What:** Stage 9 of the temporal-field pipeline: fits the hazard field's weights against this chart's recorded life events (blocked forward-chaining CV, shrinkage to the  
**Now:** native error · abhinandan error · chart3 — · rows 7 / 0 / 0 · median 2s, worst 10m · 53.1% of 64 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Set `target_floor` = 7 (achieved on native; floors are aspirational, never fabricated — §N.4).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• DAG depth 12: sits in the serial tail. Audit its 1 declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.<br>• **Not profiled.** Measured baseline only: p50 2s · p90 5s · worst 10m · 64 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Contract-conformant. Inherits the platform-wide changes: content digest, graded staleness, shared resumability. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |

#### `mi_jivanaghatana` — M · Medium deterministic · P3 · Standard · DRAFT

**What:** LEL — held-out event log isolated from generation; ground truth for prediction calibration  
**Now:** native lit · abhinandan lit · chart3 — · rows 64 / 0 / 0 · median 0s, worst 23s · 78.8% of 52 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count ≥ floor AND no duplicate natural keys per chart`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject. |
| Rebuild time | • Early cutoff is the structural win: when this asset's output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer's speed.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 2s · worst 23s · 52 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Contract-conformant. Inherits the platform-wide changes: content digest, graded staleness, shared resumability. |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it.<br>• 3 direct dependant(s) stop invalidating when this asset rebuilds to identical content. |

#### `mi_vistara` — G · Global substrate · P3 · Standard · DRAFT

**What:** Audit log of all synthesis export events (PDF, JSON, MCP bundles)  
**Now:** global · lit · 0 rows · median 0s, worst 2s · 86.4% of 44 attempts complete

| Dimension | Plan of action |
|---|---|
| Correctness & completeness | • Add `integrity_check_sql` (none exists on any asset today): `row count = expected volume formula AND no duplicate natural keys`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).<br>• Structural-mode L5 asset: zero rows is by design until outcome data accrues. Record that in `volume_explanation` and set `target_floor = 0` so the cockpit renders "0 rows (by design)" rather than dormant. |
| Rebuild time | • Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.<br>• **Not profiled.** Measured baseline only: p50 0s · p90 1s · worst 2s · 44 run(s). Hotspot, bound class, technique, target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, not as fine). The profiling harness is M3. §19.6 places this in the long tail, which receives the systemic sweep (indexes, batching, set-based rewrites) rather than a bespoke investigation — a scope decision from the plan, not a finding that it is already fast. |
| Re-architecture & alignment | • Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural). |
| Expected benefit | • `lit` becomes an earned signal with a real detector behind it. |
<!-- ASSET_PLANS:END -->

---

## §14 — Control workbook

`NIRMANA_ASSET_CONTROL_WORKBOOK_v3_0.xlsx` — 128 assets, 9 sheets: Control · Layer Map · Asset
Register (45 columns incl. rows on all three charts, floor, completeness %, integrity check) ·
**Asset Plans** · Phase 0 Queue (15 steps) · Elevation Plan · Defect Register · Infrastructure ·
Roadmap. Generated, never hand-edited; re-run after each phase.

---

## §15 — Risks, coordination, and adjacent debris

- Freeze exception gates Phases 2–5; Phase 0 and 1 need none.
- Snapshot before any destructive operation (I2); rehearse on chart 3 first (I8).
- Claim a lease and migration numbers in `CAMPAIGN_COORDINATION.md` before any shared write —
  PARIPRAŚNA P3 is about to open.
- The false-close precedent binds (I4).
- **Adjacent governance debris, not in scope but on the path:** `CURRENT_STATE` §2 is behind
  reality for three campaigns; three campaigns wrote no SESSION_LOG entries; the production MCP
  key in `.codex/config.toml` is unrotated (P0-2); `CAMPAIGN_COORDINATION.md` on `main` is behind
  the live branch; this plan's own artifacts are uncommitted.

---

*End of NIRMANA_ELEVATION_PLAN_v3_0.md — PROPOSED. Executed to date: migrations 588 and 589 only.*
