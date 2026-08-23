---
artifact: NIRMANA_ELEVATION_PLAN_v2_0.md
version: 2.2
status: SUPERSEDED — by NIRMANA_ELEVATION_PLAN_v3_0.md (2026-08-23); retained in place per ONGOING_HYGIENE_POLICIES §A
produced_on: 2026-08-23
grounded_at: HEAD 6326cda7a (2026-08-22) + live production DB reads 2026-08-23
authoritative_side: claude
role: >
  The elevation programme for the Nirmāṇa Build Tracker — the per-chart build cockpit, the
  orchestrator behind it, and the asset DAG both operate on. v2.0 adds the Asset Catalogue
  Reconciliation pre-flight as Phase 0 and realigns every later phase to build on a frozen,
  contract-conformant, CI-guarded catalogue.
supersedes: >
  NIRMANA_ELEVATION_PLAN_v1_0.md (2026-08-23, PROPOSED, never ratified, never committed —
  removed rather than retained, since nothing referenced it). v1.0's diagnosis is carried
  forward intact; what changed is the front of the roadmap and the addition of §3.
companion_artifacts:
  - 00_ARCHITECTURE/control/NIRMANA_ASSET_CONTROL_WORKBOOK_v2_0.xlsx — the per-asset execution surface
  - 00_ARCHITECTURE/control/build_asset_control_workbook.py — its generator; re-run after each phase
invariants:
  - I1 — SUPERSEDED 2026-08-23 by native instruction. All per-asset build protection has been
    REMOVED (migrations 588 + 589): 3 triggers dropped, 4 build_protected_assets rows deleted,
    3 trigger functions dropped. The campaign rebuilds every asset, so a guard requiring an
    override on every legitimate write is no longer wanted. Corpus verified intact after removal
    (38,287 v1 + 1,884 gen-3.0 rows).
  - I2 — REPLACED BY SNAPSHOT DISCIPLINE. Protection's role is now served by a verified logical
    snapshot taken immediately before removal:
    00_ARCHITECTURE/control/snapshots/20260823_pre_protection_removal/ (16.2 MB, pg_restore-verified).
    STANDING CAUTION: ka_gochara_sweep's 38,287 generation='v1' rows have NO registered writer —
    the @register was removed at retirement, so the build system CANNOT regenerate them. That
    snapshot is their only recovery path. Any destructive operation touching them must take a
    fresh snapshot first.
  - I3 — the FROZEN orchestrator contract (@register / WriterBase / run(ctx) / ctx.db_conn never
    committed by the writer) is preserved. Phases 3–5 need a native-authorised freeze exception
    on orchestrator internals; the writer-facing contract itself does not change.
  - I4 — no phase closes on CI-green or code review alone (PARIPRAŚNA DD-21); every acceptance
    criterion is verified by live execution against production.
  - I5 — every status, grade and PASS this plan introduces has a real detector behind it or is
    null (CLAUDE.md §N.8 Earned-Signal Principle).
  - I6 — NEW. No registry row is ever DELETEd. Assets leave the build path by lifecycle
    transition, never by deletion. Retired rows carry FK dependants, audit history and
    protection references; migration 563 already failed once on exactly this.
changelog:
  - 2.2 (2026-08-23) — Folds in every accepted recommendation: adds §12 Infrastructure and
    Database (the section v2.1's changelog announced but never wrote — a self-inflicted
    registry_disagreement, fixed here); expands Phase 0 to 15 steps covering the catalog_status
    drift and the zero-consumer review; distributes the infrastructure, database and process
    items into the phases that own them (spill volume + rehearsal chart → Phase 1; determinism
    harness → Phase 3; chart_id partitioning → Phase 4; connection pooler → Phase 5; per-substep
    tracing → Phase 6); adds defect D-16; records the v1-corpus-has-no-writer fact as a standing
    constraint rather than a footnote.
  - 2.1 (2026-08-23) — Protection removed on native instruction (migrations 588/589) after a
    verified snapshot; invariants I1/I2 rewritten accordingly and defect D-02 closed by
    supersession. Adds §12 Infrastructure and Database. Two new catalogue findings recorded:
    47 assets sit at catalog_status=DRAFT while being actively built and served, and 13
    table-backed assets have no detected serving consumer. Conformance model split into
    structural violations vs advisory gaps so the signal is usable.
  - 2.0 (2026-08-23) — Adds §3 Asset Catalogue Contract and Phase 0 Pre-flight; renumbers the
    roadmap to seven phases; adds invariant I6 (tombstone, never delete); records the semantic
    definition of "duplicate" after measuring that four target tables have legitimate multiple
    writers; adds the SOURCE classification outside L0–L5; adds the consumer map as a
    prerequisite for safe retirement; splits the P0 queue into catalogue-truth vs runtime defects.
  - 1.0 (2026-08-23) — Initial re-grounded plan. Superseded same day.
---

# Nirmāṇa Elevation Plan v2.0

## §0 — Grounding

Verified at HEAD `6326cda7a` (2026-08-22) with live production database reads on 2026-08-23.
239 commits landed between the prior grounding (`77109b8ac`, 2026-08-13) and HEAD.

Campaigns folded in: **GOCHARA-UTKARṢA** (closed via PARIṢKĀRA), **PARIṢKĀRA** (complete
2026-08-12), **SAMPŪRTI/DHARA** (closed 2026-08-15), **EKAVĀKYATĀ** (closed-partial, 18 of 40
lanes unlanded), **PARIŚEṢA-RĀTRI-V4** (closed with residuals 2026-08-22), **PARIPRAŚNA**
(P3-Preflight closed; P3 not yet open).

**The structural fact this plan exists to answer:** every one of those campaigns changed something
the tracker depends on, and none of them changed the tracker. The cockpit API and build library
last changed 2026-08-06; its components 2026-08-10; the orchestrator core 2026-07-31. New
fingerprint semantics, a new state-audit trigger, a new engine for the heaviest asset, and
retired and renamed assets all landed underneath it, and none of its logic was reconciled against
any of them.

---

## §1 — Diagnosis

### 1.1 Fewer than half of all build attempts succeed

`build_run_assets`, all history: **3,255 complete · 1,565 error · 847 aborted · 1,477 queued
never run** = 7,144 attempts, **45.6 % reaching `complete`**. Cost and failure are correlated, not
independent — the two most expensive assets have the worst rates: `ka_gochara_sweep` **9.6 %** of
94 attempts (worst run 35.6 h) and `ka_kshetra` **11.9 %** of 126 attempts (worst 33.8 h).

### 1.2 Live chart state (2026-08-23)

| chart | lit | stale | error | dormant | incomplete |
|---|---|---|---|---|---|
| 482012f1 (Abhisek, native) | 64 | 8 | 10 | 1 | 0 |
| 1c826d5a (Abhinandan) | 76 | 1 | 2 | 2 | 0 |
| cb73cd3d (third chart) | 31 | 14 | 14 | 0 | 1 |
| global (`chart_id IS NULL`) | 42 | 0 | 1 | 0 | 0 |

### 1.3 Five failures live right now

1. **`ka_gochara_v3_century_materialize` — `error: BUILD-PROTECTED`.** `build_protected_assets`
   registers gen-3.0 protection under `asset_id = 'ka_gochara'`, but the writer producing gen-3.0
   rows is the v3 materializer. The guard cannot distinguish a legitimate write from a destructive
   one, so it blocks the authoritative writer.
2. **`ka_gochara_sweep` — `error: "no writer registered"` on both canonical charts.** A RETIRED
   asset still holds throughput rows the runner picks up. Retirement is not a supported operation.
3. **`ka_kshetra` — reaped at 301 of 308 committed substeps.** 10.5 M rows, ~6.3 h of compute,
   discarded at 97.7 % complete by the `NOW()`-vs-`clock_timestamp()` watchdog defect.
4. **Mīmāṃsā cascade — 8 of 14 `mi_*` assets blocked from one root fault.** And `mi_bhara` reports
   being blocked by a dependency named `timeout:600s` — a sentinel rendered as an asset id.
5. **`bg_ephemeris_engine` — `error` since 2026-06-18**, 66 days, missing ephemeris file.

### 1.4 The `has_substeps` false-negative defect

**28 registered writers implement `plan_substeps`; only 14 carry `has_substeps = true`.** The 14
false negatives span every layer: `bg_reference`, `bg_muhurta_lattice` (L0); `ga_ayurdaya`,
`ga_nakshatra`, `ga_sensitive`, `ga_sensitive_degree`, `ga_structural` (L1); `bo_laksana`,
`bo_laksana_rerank`, `bo_samskara` (L2); `ka_sangam` (L3); `mi_darshana`, `mi_pariksha`,
`mi_pramana` (L5).

The orchestrator's no-op-completion rescue reads this flag; when false it sets
`plan_complete = True` unconditionally and promotes the asset to `lit`. **A genuinely partial build
of these assets is reported green** — precisely the defect SATYA-DĪPA was chartered to fix. The fix
is intact; its detector reads a flag that drifted. `ka_sangam` is the proof: 61 substep rows
recorded per chart while the registry says it has none — and 11 downstream assets consume it.

### 1.5 Fragmented resume, polluted telemetry, a thin deep graph

- **20 heavy assets have no resume capability at all** (led by `bo_laksana`, 19.2 h worst run,
  41.2 % success). Three private copies of the same resume protocol exist; two independently
  reached `_RESUME_VERSION = 7`; the orchestrator's own `completed_keys` primitive is passed by no
  production caller.
- **Telemetry is corrupt.** Failed runs are never closed: `ga_positions` shows a 16.9-day maximum,
  `ga_sade_sati` 4.4 days. `estimated_seconds` is populated on **2 of 128** assets, so every ETA is
  inferred from those medians.
- **The DAG is 21 levels deep and ~3 assets wide from L3 down** (34 and 26 at L0/L1, then 1–5 per
  level). With `WORKER_LIMIT = 4`, **18 of 21 levels cannot use the parallelism they are given.**
  Wall-clock approximates the weighted critical path. No cycles — the depth is genuine.

### 1.6 Catalogue status has drifted from its meaning

**47 assets carry `catalog_status = 'DRAFT'`; 34 of them are actively built AND read by a serving
surface.** DRAFT is defined as "registered, not yet authoritative" — these are authoritative in
practice. A status that covers a third of the catalogue cannot gate any decision, and in particular
cannot support the rule a contract needs: *a CURRENT asset may not depend on a DRAFT one.*

### 1.7 Thirteen assets have no detected consumer

Thirteen table-backed assets are read by no MCP tool, API route or retrieval layer. Each is either
a real asset whose consumer was never recorded, or dead weight the DAG still builds. Both readings
require the consumer map (§3.5) to resolve — which is why the map is a Phase 0 deliverable rather
than a documentation nicety.

### 1.8 The v1 gochara corpus cannot be rebuilt

`ka_gochara_sweep` is RETIRED and its `@register` was removed at retirement, so **no writer in the
build system can regenerate its 38,287 generation='v1' rows** — and those rows are still read by 5
serving surfaces (chart 3 has no authority row, so it serves v1). This is a standing constraint on
every later phase, not a footnote: "the campaign rebuilds everything" is true of every asset except
this one.

### 1.9 Verification of v1.0's defect list at HEAD

Eleven of thirteen claims **STILL TRUE**: dead `isStale()` and write-only hash columns; timestamp
upstream hash and git-SHA writer hash; duplicate and now-**divergent** staleness cascades; `stale`
unreachable with rows; no-op Refresh; null substep totals; `NOW()` watchdog; zero retry;
`service_ok`/`mature` absent from the CHECK constraint; no prod-run guard on the seed; zero new
tracker work. **FIXED:** seed drift (W0.1) and the `ka_gochara_v2_materialize` dependency gate
(migration 563).

---

## §2 — Target state

Nirmāṇa becomes a **content-addressed, partition-aware, self-healing build system with a
cost-honest cockpit, standing on a contract-conformant asset catalogue.** Freshness is decided by
what an asset was built *from*, not when it was built. Invalidation is scoped to the partitions
actually affected. Interrupted work resumes as an orchestrator guarantee rather than a per-writer
heroic. Failures are classified and retried when transient. The DAG is a managed, audited artifact
with a measured critical path. And the cockpit tells the operator the truth — what is fresh, why
something is stale, what an action will cost, and which single fault sits behind a screen full of
red.

**v2.0's central addition:** none of that can be built on a catalogue whose own description of
reality is wrong. Phase 0 makes the catalogue true and keeps it true.

---

## §3 — The Asset Catalogue Contract

*New in v2.0. This section is the specification Phase 0 implements.*

### 3.1 Why a contract, and why now

The instruction "register the asset properly, as per the system we have set up" cannot currently
be followed, **because that system is not written down as an enforceable specification.** That is
the direct cause of what is measurable today: 14 assets with no `layer_index` and 6 more carrying a
bare numeral instead of the `Lx` form, two encodings of
the same concept (`'3'` and `'L3'`), spelling drift between `Kala` and `Kāla`, three columns
disagreeing about which assets are services, and 14 substep writers whose completeness gate is
silently disabled.

Phase 0's first deliverable is therefore the contract itself. The reconciliation is the second.

### 3.2 Lifecycle states — tombstone, never delete (I6)

| State | Meaning | Rules |
|---|---|---|
| `CURRENT` | Live, buildable, authoritative for its output | Full contract conformance required |
| `DRAFT` | Registered, not yet authoritative | May lack build coverage; must not be depended on by a `CURRENT` asset |
| `RETIRED` | No longer built; record retained | `is_active=false`, zero throughput rows, `superseded_by` set if applicable, `data_disposition` recorded |
| `SUPERSEDED_BY(x)` | Replaced by a named successor | Same as RETIRED plus a resolvable pointer |
| `SOURCE` | Ingested data the DAG reads but never builds | Sits **outside** L0–L5; exempt from writer and count_sql requirements |

**`data_disposition` is mandatory on exit** and takes one of: `RETAINED_AS_CAPITAL` (the rows are
irreplaceable — `ka_gochara_sweep`'s 38,287 v1 windows), `SUPERSEDED_IN_PLACE` (a successor owns
the rows), or `DROPPABLE` (safe to remove).

Deletion is prohibited because retired rows are load-bearing: `ka_gochara_sweep`'s registry row is
what the protection triggers and the PK-R-4 retention ruling reference, and it carries FK
dependants in `asset_throughput`, `asset_coefficients` and `build_run_assets`. **Migration 563
already failed silently on exactly this FK.** What must be removed is the asset's presence in the
build path, not its record.

### 3.3 What "duplicate" means — measured, not assumed

A naive de-duplication by `target_table` would destroy fourteen legitimate assets. Measured on
2026-08-23, four tables have multiple active writers, and all four are correct:

| table | writers | verdict |
|---|---|---|
| `bodha_msr_signals` | 7 (`bo_laksana`, `bo_arudha`, `bo_sudarshana`, `bo_special_lagna`, `bo_nakshatra_semantic`, `bo_vargottama_dhana`, `bo_laksana_rerank`) | legitimate co-writers, partitioned by natural key |
| `chart_facts` | 5 (`ga_positions`, `ga_panchanga`, `ga_nakshatra`, `ga_ayurdaya`, `ga_sensitive_degree`) | legitimate co-writers |
| `brahma_class_priors` | 2 | legitimate |
| `classical_text_chunks` | 2 | legitimate |

**The invariant is therefore not one asset per table.** It is:

> Exactly one authoritative producing asset per **(target_table × generation × natural-key partition)**.

The genuine duplicate defect in the catalogue is in the gochara family, where `ka_gochara`'s
registry row claims gen-3.0 rows that `ka_gochara_v3_century_materialize` actually writes, while
its own gen-2.0 output goes uncounted.

### 3.4 Required fields, by asset kind

| Field | data | service | artifact | source |
|---|---|---|---|---|
| `asset_id` matching its layer prefix (§N.1) | ✔ | ✔ | ✔ | exempt |
| `layer` + `layer_index` (`Lx` form) + `layer_name` (derived) | ✔ | ✔ | ✔ | n/a — outside L0–L5 |
| `sanskrit_name`, `english_name`, `english_description`, `sort_order` | ✔ | ✔ | ✔ | ✔ |
| `scope` (`global` / `per_chart`) | ✔ | ✔ | ✔ | ✔ |
| `catalog_status` + lifecycle fields (§3.2) | ✔ | ✔ | ✔ | ✔ |
| `target_table`, chart-scoped `count_sql`, `clear_tables`, `target_floor` | ✔ | ✖ must be null | ✔ | ✖ |
| `has_substeps` **derived from the writer class**, `writer_timeout_seconds`, `estimated_seconds` | ✔ if substep writer | ✖ | ✔ if substep writer | ✖ |
| `health_probe`, `provides_apis`, `service_health` | ✖ | ✔ | ✖ | ✖ |
| authority pointer + `protected_generations` | ✔ if generation-bearing | ✖ | ✖ | ✖ |
| `depends_on` — every target exists and is active | ✔ | ✔ | ✔ | ✖ |
| `consumers` — serving surfaces reading this asset (§3.5) | ✔ | ✔ | ✔ | ✔ |

`asset_kind` becomes the single authoritative classification column; `asset_type` and
`storage_type` are derived from it or dropped. Today they disagree — 4 services by `asset_type`,
6 by `asset_kind`, 8 by `storage_type`.

### 3.4a `catalog_status` must regain meaning

DRAFT currently covers 47 of 128 assets, 34 of which are built and served (§1.6). The contract
therefore fixes the semantics and makes them load-bearing:

- **CURRENT** — authoritative for its output. May depend only on CURRENT or SOURCE assets.
- **DRAFT** — registered, not yet authoritative. **A CURRENT asset may not depend on a DRAFT one**,
  and CI asserts it. This rule is what makes the status worth having; it is unenforceable today
  because a third of the catalogue would fail it.

Phase 0 promotes each of the 34 to CURRENT or records explicitly why it remains DRAFT.

### 3.5 The consumer map

The catalogue records which **assets** depend on an asset. It does not record which **MCP tools,
API routes and retrieval layers read its table** — that had to be established by grep during the
gochara cutover.

Without a consumer map, *"is it safe to retire this?"* is unanswerable, and that is the question
the entire pre-flight exists to serve. Phase 0 therefore builds an asset → consumer index across
`platform-mcp/src/tools/**`, `platform/src/app/api/**` and `platform/src/lib/retrieval/**`, and
makes it a required field.

### 3.6 The `SOURCE` classification

Measured: **`lel_events` is the only asset whose id prefix violates §N.1** (`lel_` in a layer
demanding `mi_`), it has no writer, and it has never been built on any chart. It is ingested data
the DAG reads but never builds. Forcing it into L5 corrupts that layer's population count and its
health arithmetic. `SOURCE` sits outside L0–L5 and is exempt from writer, `count_sql` and layer
requirements.

### 3.7 Registered but dead

Two active assets have never been built on any chart: `lel_events` (a `SOURCE`, correctly) and
**`bg_gochara_citation_resolution` — `catalog_status = CURRENT` with `has_writer = false`**: a
CURRENT asset that nothing can build and that has never existed. The catalogue must distinguish
*registered and real* from *registered but dead*, and every active asset must either have build
coverage or be explicitly flagged.

---

## §4 — Per-asset elevation, by tier

127 active assets across five tiers, each with a uniform treatment. Populations from the control
workbook.

| Tier | n | Treatment |
|---|---|---|
| **G · Global substrate** | 40 | Publish `substrate_version` + output content digest; consumers record the version read. Excluded from per-chart plans but visible to the readiness gate. Own build cadence and freshness SLO. `bg_gochara_arcs` is the exemplar — 34,553 arcs for the whole epoch in 48 s, amortised across every chart forever. |
| **H · Heavy partitioned** | 25 | Universal partition receipts: every substep records the digest of the inputs it consumed, so a rebuild diffs receipts and re-runs only mismatches. Shared `ResumableWriter` mixin replacing three private copies. Persisted plan totals. Per-partition cost declared so an invalidation can be priced before it is committed to. |
| **M · Medium deterministic** | 51 | Output content digest + early cutoff. A rebuild producing identical rows stops invalidating downstream — this is the long tail that makes full rebuilds slow. |
| **S · Service probe** | 8 | Real probes with SLOs, health history, alerting, and a dedicated cockpit lane rather than being mixed into the data ledger. |
| **X · Generation-bearing** | 4 | Generation and per-chart authority become first-class registry and UI concepts, each generation with its own count and freshness. Ends the hand-repointing of `count_sql`. |

### 4.1 Heavy assets, measured

| asset | substeps | median | worst | success | resume today |
|---|---|---|---|---|---|
| `ka_gochara_sweep` (RETIRED) | 606 | 2.1 h | 35.6 h | 9.6 % | private copy |
| `ka_kshetra` | 308 | 39 m | 33.8 h | 11.9 % | private copy |
| `bo_laksana` | yes | 3.4 m | 19.2 h | 41.2 % | **none** |
| `ga_sensitive` | yes | 4 m | 6.4 h | 61.6 % | **none** |
| `ka_gochara_v3_century_materialize` | 270 | 2 m | 58 m | — | delta fingerprint |
| `ka_sangam` | 61 | 8 m | 2.8 h | 43.1 % | private copy |
| `bo_samskara` | yes | 13 m | 2.6 h | 43.7 % | **none** |
| `ga_dashas` | yes | 10 m | 89 m | 46.3 % | **none** |

---

## §5 — Build-time optimization · six levers

1. **Skip what has not changed (content addressing).** Highest return by a wide margin. Today any
   upstream completion marks the whole downstream cone stale regardless of whether content changed.
   This is the direct fix for "a small L1 change stales the whole DAG."
2. **Partition-scoped invalidation.** Turns "one class of rules changed" from a full re-sweep into
   a partial, and "an unrelated upstream rebuilt" from a total loss into zero work.
3. **Shorten the critical path, don't widen the pool.** From L3 down the win is removing edges that
   are declared but not read. The Mīmāṃsā tail is the specimen: a five-deep serial chain inside two
   layers, one asset declaring eight dependencies.
4. **Automatic retry on transient failures.** At 45.6 % completion, most operator wall-clock is
   spent noticing failures and re-dispatching by hand.
5. **Multi-dispatch continuation.** A build exceeding the job wall clock re-dispatches itself until
   its plan completes — promoting into the product what hand-rolled `/tmp` restart loops did during
   SAMPŪRTI.
6. **Right-size timeouts and resources per asset**, from clean telemetry rather than from estimates
   that exist on 2 of 128 assets.

**Prerequisite:** close orphaned `build_run_assets` rows and recompute medians. Until then every
cost number the cockpit shows is computed from corrupted data.

---

## §6 — Orchestrator elevation

Requires a native-authorised freeze exception on orchestrator internals (precedent: SATYA-DĪPA
§7.1). **The writer-facing contract does not change** — every existing writer keeps working
unmodified.

1. **One staleness engine.** Delete the inline cascade in `asset_runner.py`; `staleness.py` becomes
   sole owner. The two currently disagree on their state allowlist and one fabricates `from_state`.
2. **Content-digest freshness with early cutoff.** Re-point the upstream hash from timestamps to
   content digests; switch the writer hash from git SHA to source content; read both at plan time.
3. **Graded staleness:** `fresh · stale:upstream-content · stale:code · stale:config`, each with a
   real detector (§N.8).
4. **Error taxonomy + retry policy**, seeded from real specimens already in the logs.
5. **Shared resumability:** `ResumableWriter` mixin, `completed_keys` wired, plan totals persisted,
   per-partition input digests.
6. **Heartbeat correctness:** `clock_timestamp()` instead of `NOW()`; the watchdog reads
   `build_substep_progress.completed_at` as primary liveness.
7. **State vocabulary reconciliation:** one enum across the DB CHECK, Python allowlists and the TS
   union.
8. **Registry lifecycle operations** implementing §3.2 — retire, rename and supersede that repoint
   dependants and clear throughput rows in one transaction.
9. **`has_substeps` derived from the writer class** at registration, asserted in CI.
10. **The audit trigger becomes the event spine.** `asset_throughput_state_audit` (migration 586)
    holds 4 rows and is read by nothing; it is the substrate for run history and provenance.

---

## §7 — DAG elevation

1. **Edge provenance** — every `depends_on` edge records who added it, when and why. Edges are
   currently added and removed by ad-hoc migrations (546 added one, 569 removed one).
2. **Declared-vs-read audit.** Over-declared edges are pure serialization cost (§5 lever 3).
3. **Shape guards in CI:** no cycles, no orphans, no throughput row without a registry row, every
   `depends_on` target active. *Note: zero dangling edges today — lock the invariant in while it is
   free, so a future retirement cannot reintroduce the `ka_kshetra` dispatch deadlock.*
4. **Critical path as a first-class report**, published per chart on every plan.
5. **Scope explicit in the graph** — global vs per-chart honoured uniformly by the readiness gate.
6. **Blast radius on pull request** for any change to a dependency, a writer's source, or a scoring
   formula.

---

## §8 — UX elevation

1. **Never disagree with the planner.** Stale-with-data renders amber using the planner's own
   predicate. The green-then-`UPSTREAM_BLOCKED` contradiction ends.
2. **Collapse cascades to their root.** Eight red rows for one fault is a reporting failure.
3. **Price every action before it is taken** — partition-aware for heavy assets, with an extra
   acknowledgment for protected or expensive targets.
4. **Provenance panel per asset:** built from which digests, which writer version, which
   generation, which authority — and if stale, exactly which input changed.
5. **Honest progress** with real denominators, and run history from the audit spine.
6. **Service-health lane**, multi-chart view, and protected assets shown as protected rather than
   discovered by bouncing off a trigger.
7. **Fix or remove the fake Refresh**, which today only bumps a column nothing reads.
8. **Sweep the small dishonesties:** the 9 px unlabelled stale badge, the unstyled failure state,
   the unused `activeRunPaused` prop, the duplicated `ClearPreview` type, the `useMemo` dep that
   swallows row-count updates.

---

## §9 — Roadmap · seven phases

Each phase closes only on live production verification (I4). Phases renumbered from v1.0: the
pre-flight becomes Phase 0 and everything shifts by one.

### Phase 0 · Pre-flight: Asset Catalogue Reconciliation
*Scale: its own campaign phase, not a warm-up. No freeze exception (registry + CI only).*

| Step | Work |
|---|---|
| **0.1 Six-source census** | Reconcile `asset_registry` · `@register()` in code · `asset_registry_seed.ts` · migrations · `asset_throughput` · `CAPABILITY_MANIFEST.json` + `catalog_assets_*`. Orphans live in the gaps between sources — a registry-only census would have missed the throughput row that killed migration 563. |
| **0.2 Author the contract** | Write §3 as an enforceable specification with per-kind required fields. This is the artifact that does not exist today. |
| **0.3 Lifecycle + tombstone** | Implement §3.2. Add `superseded_by` and `data_disposition`. No DELETEs (I6). |
| **0.4 Semantic de-duplication** | Apply the (table × generation × partition) invariant from §3.3. Correct the `ka_gochara` attribution. Do **not** dedupe by table — four tables have legitimate co-writers. |
| **0.5a Layer position** | Backfill 14 null `layer_index` values; normalise the 6 bare-numeral forms (`'0'`,`'1'`,`'2'`,`'3'`) to `Lx`; derive `layer_name` from `layer` in the locked lexicon (ends the `Kala`/`Kāla` drift). |
| **0.5b SOURCE classification** | Introduce `SOURCE` outside L0–L5 and move `lel_events` into it — the only asset whose id prefix violates §N.1, with no writer and no build coverage. |
| **0.6a has_substeps** | The 14 false negatives — derive from the writer class at registration rather than declaring in the registry. This re-arms the §N.8 completeness gate. |
| **0.6b Kind reconciliation** | Collapse `asset_type`/`asset_kind`/`storage_type` (6 disagreements) to `asset_kind` as the single authoritative column; derive or drop the others. |
| **0.7 Consumer map** | Build the asset → serving-surface index (§3.5) and make it a required field. Retirement is unsafe without it. |
| **0.8a Build coverage audit** | Flag *registered but dead* — `bg_gochara_citation_resolution` is CURRENT, has no writer and has never been built. |
| **0.8b catalog_status drift** | Promote the 34 DRAFT-but-served assets to CURRENT or record why each stays DRAFT; then enforce §3.4a's dependency rule. |
| **0.8c Zero-consumer review** | Resolve each of the 13 table-backed assets with no detected consumer: record the missing consumer, or retire it with a disposition. |
| **0.9 Telemetry repair** | Close orphaned `build_run_assets` rows, recompute medians, backfill `estimated_seconds` (advisory today on 119 assets), and put the refresh on a schedule. Every cost estimate in Phases 1–6 reads this. |
| **0.10 CI enforcement** | Three-way guard (code ↔ seed ↔ live DB) plus contract conformance, prefix-matches-layer, CURRENT-may-not-depend-on-DRAFT, and the edge invariant. Extends the existing `test_has_writer_completeness.py` precedent to every contract field. |
| **0.11 Freeze the baseline** | Tag the reconciled catalogue as the control-workbook baseline. Every later phase measures drift against it rather than re-deriving truth. |

**Exit criteria — all must return zero, verified live:**
code ↔ seed ↔ DB three-way diff · contract violations per kind · `asset_id` prefixes not matching
their layer (or classified `SOURCE`) · `depends_on` targets absent or inactive · tables with more
than one authoritative producer per (generation × partition) · throughput or coefficient rows
referencing inactive assets · retired assets lacking `superseded_by` + `data_disposition` · active
assets with neither build coverage nor a dead flag · CURRENT assets depending on DRAFT assets ·
table-backed assets with an unresolved zero-consumer finding · **and the CI guard for all of the
above merged and blocking.**

> **Why this precedes everything:** content addressing (Phase 3) hashes an asset's declared inputs;
> partition receipts (Phase 4) key on its declared partitions; blast-radius pricing (Phase 6) reads
> its declared consumers and costs. Each of those inherits whatever the catalogue says. Building
> them on today's catalogue would encode 14 missing layer positions, 14 disabled completeness
> gates, 34 mis-stated statuses and a mis-attributed generation into the foundation.

### Phase 1 · Runtime truth debris
*Days. No freeze exception. The P0s that change behaviour or data, executed against a known-good catalogue.*

Execute the lifecycle retirement of `ka_gochara_sweep` using the Phase 0 operation (clears two
permanent reds) · `bg_ephemeris_engine` ephemeris file (clears a 66-day red) · **mount a real
volume for the hash spill directory** (§12 item 1 — the only infrastructure item that fixes a live
correctness risk rather than buying headroom) · **designate chart 3 the standing rehearsal
subject** (§12 item 9 — it is already unhealthy and is not a serving target, and with protection
removed no elevation step should be first executed against a canonical chart) · record the F-52
rematerialization decision explicitly rather than showing green.

*(The gochara protection asset-id mismatch that was originally scoped here is closed — all
protection was removed 2026-08-23 per I1/I2. See §12.6 for the rule if protection is ever reinstated.)*

**Acceptance:** error counts drop on all three charts, verified against production; every remaining
red is a real fault with a named owner.

### Phase 2 · Truth and safety
*Days. One orchestrator deletion needs the exception.*

Amber stale-with-data; delete the duplicate cascade; persist substep totals; correct the heartbeat
clock; real-or-removed Refresh; state vocabulary reconciled with a CI guard; generation and
authority in the UI; cascade-root collapse; service-health lane.

**Acceptance:** a heavy build survives a full substep without a watchdog reap; a stale-with-data
asset renders amber and the planner agrees with the cockpit.

### Phase 3 · Content-addressed freshness
*1–2 weeks. Freeze exception.*

Output digests on every asset; upstream-digest freshness with early cutoff; source-content writer
hash read at plan time; graded staleness; the dead staleness specification wired or deleted;
**a determinism harness** (§12 item 10) — build-twice-and-compare-digests for a representative
asset per tier, since content addressing otherwise assumes a determinism it never verifies.

**Acceptance:** rebuilding an upstream to identical content leaves its downstream fresh, verified
live on a real chart; editing a writer marks exactly that asset `stale:code`; the determinism
harness passes for one asset in every tier.

### Phase 4 · Receipts and robust execution
*~2 weeks. Freeze exception.*

Shared `ResumableWriter` mixin replacing three private copies; per-substep input digests; error
taxonomy and retry; multi-dispatch continuation; resume-run and rebuild-failed-only.

**Acceptance:** a deliberately interrupted heavy build resumes without losing committed substeps; a
transient failure recovers with no human dispatch; completion rate measured before and after
against the 45.6 % baseline.

### Phase 5 · DAG management
*~1 week. Freeze exception.*

Edge provenance; declared-vs-read audit; published critical path; blast radius on pull request;
**a connection pooler** (§12 item 2) so worker width can finally rise where the DAG is genuinely
wide — parallelism is capped by a connection budget, not CPU. Shape guards already landed in
Phase 0.10.

**Acceptance:** the critical path is published per chart, and at least one over-declared edge is
removed with a measured wall-clock reduction.

### Phase 6 · Operator experience
*1–2 weeks. UI only.*

Blast-radius preview, provenance panel, run timeline from the audit spine, failure triage,
generation display, multi-chart view, **per-substep tracing and build metrics** (§12 item 6) so the
timeline and cost model read measured data rather than inference, and the polish sweep.

**Acceptance:** an operator can answer without leaving the cockpit — what is stale and why, what
this action costs, which fault is behind the red, and what happened on the last run.

---

## §10 — Risks and coordination

- **Freeze exception is a hard gate** for Phases 2–5. Nothing starts before it is granted and
  recorded. Phase 0 needs none — it touches the registry, the seed and CI only.
- **Protection is gone; snapshots replace it.** Removed 2026-08-23 (I1/I2). Any destructive
  operation on an irreplaceable corpus takes a verified snapshot first — that is now a procedural
  discipline rather than a database-enforced one, which makes it weaker and therefore deliberate.
- **No DELETEs (I6).** The catalogue shrinks by lifecycle transition only.
- **Campaign coordination is mandatory.** A lease and migration numbers must be claimed in
  `CAMPAIGN_COORDINATION.md` before any shared-surface write — PARIPRAŚNA P3 is about to open and
  PARIŚEṢA residuals remain.
- **No destructive first-runs against a canonical chart.** With protection removed, chart 3 is the
  designated rehearsal subject (§12.5). Snapshot before any irreversible operation.
- **The false-close precedent binds.** GOCHARA-UTKARṢA's verifiers passed work on paper that was
  broken in production; every genuine defect was found by live execution. No phase closes on review
  alone (I4).
- **Adjacent governance debt** a session touching the build system will encounter: `CURRENT_STATE`
  §2 is behind reality for three campaigns; three campaigns wrote no SESSION_LOG entries; the
  production MCP key in `.codex/config.toml` is still unrotated. Out of scope, but present.

---

## §11 — Control workbook

`00_ARCHITECTURE/control/NIRMANA_ASSET_CONTROL_WORKBOOK_v2_0.xlsx` is the execution surface for
this plan — 128 assets × 39 columns across 8 sheets, generated live from production.

**Generated, never hand-edited.** The generator lives at
`00_ARCHITECTURE/control/build_asset_control_workbook.py`: self-contained, reads the registry
directly, scans the writer code for substep and resume facts, builds the consumer index, and
evaluates every asset against §3. **Re-run it after each phase** so the workbook shows movement
rather than a stale snapshot.

| Sheet | Role |
|---|---|
| Control | Provenance, protection-removal record, legends, current counts |
| Layer Map | L0–L5 roll-up: population, conformance, health, cost, per-layer thesis |
| Asset Register | The master sheet — fact, contract conformance, plan, benefit, per-chart state |
| Phase 0 Queue | The pre-flight work queue, 13 items |
| Elevation Plan | Per-asset actions and expected benefit, ordered by priority |
| Defect Register | 16 cross-cutting defects (D-01 … D-16) |
| Infrastructure | §12's ranked items in tracking form |
| Roadmap | The seven phases with gates and acceptance |

Conformance is split into **structural violations** (63 assets) and **advisory gaps** (119 assets
lack `estimated_seconds`). Folding the advisory gap into the headline produced a useless
123-of-128 signal; separating them makes the column actionable.

---

## §12 — Infrastructure and database

Ranked by measured value. The headline finding first, because it governs how much to spend here:

> **Infrastructure is not the bottleneck.** 18 of 21 DAG levels are already narrower than the
> existing worker pool of 4; the build is effectively serial from L3 down, so added cores idle. The
> job already runs at 8Gi/4CPU. Wall-clock is changed by *not running work* (Phase 3), *running only
> changed partitions* (Phase 4) and *shortening the critical path* (Phase 5) — not by a bigger
> machine. Three infrastructure items nonetheless earn their place, and one of them fixes a live
> correctness risk.

| # | Area | Item | Verdict | Phase |
|---|---|---|---|---|
| 1 | Cloud Run | Real volume for the hash spill directory | **DO IT** | 1 |
| 2 | Database | Connection pooler | HIGH VALUE | 5 |
| 3 | Database | `chart_id` partitioning on the largest tables | HIGH VALUE | 4 |
| 4 | Database | Autovacuum tuning on high-churn build tables | WORTH DOING | 4 |
| 5 | Cloud Run | Multi-dispatch continuation *(solve in code)* | DO IT (as code) | 4 |
| 6 | Observability | Per-substep tracing and build metrics | WORTH DOING | 6 |
| 7 | Cloud Run | CPU / memory sizing | **NOT THE BOTTLENECK** | defer |
| 8 | Database | Per-chart databases | LATER — hybrid shape | later |
| 9 | Process | Formalise a rehearsal chart | WORTH DOING | 1 |
| 10 | Process | Determinism harness | WORTH DOING | 3 |

### 12.1 The spill directory is RAM-backed (the one live risk)

`KA_KSHETRA_HASH_SPILL_DIR` is pinned to `/tmp`, which on Cloud Run is a **tmpfs — RAM, not disk**.
A 3–4.2 GB spill therefore counts against the 8 Gi job limit, inverting the bounded-memory
guarantee the external merge sort was built to provide. The compensating response so far was
doubling job memory rather than fixing the substrate, and **the repo contains zero Cloud Run volume
mounts anywhere**. Mount a disk or Cloud Storage FUSE volume and point the spill directory at it.

### 12.2 Parallelism is capped by connections, not CPU

The orchestrator enforces `MAX_CONCURRENT_RUNS × (1 + WORKER_LIMIT) ≤ ~33`, derived from the
database connection budget; `WORKER_LIMIT` is 4. Raising it without a pooler just exhausts
connections. A pooler decouples worker count from backend connections and lets width rise where the
DAG is genuinely wide — L0 and L1 hold 60 of 128 assets. Sequenced into Phase 5 because it only
pays once the critical path has been shortened.

### 12.3 Partition by `chart_id` — protection by schema

`ka_kshetra` writes 10.5 M rows per chart, and §N.3 idempotency is delete-then-insert, so **every
rebuild deletes and reinserts millions of rows**, generating heavy bloat and long transactions.
Partitioning by `chart_id` turns a per-chart rebuild into `DROP PARTITION`: instant, no bloat, and
**structurally incapable of touching another chart**.

That last property matters beyond performance. It is the guarantee the protection triggers were
installed to provide, achieved by schema rather than by trigger — which is the right place for it,
and why removing the triggers (I1/I2) is safe to pair with this work rather than being a bare loss.

### 12.4 Per-chart databases — the hybrid shape

Native intent, correctly deferred. When the time comes, the constraint to design around is that
**44 of 128 assets are `scope=global`** chart-independent substrate whose whole value is that it
amortises across charts (`bg_gochara_arcs`: 34,553 arcs for the entire epoch in ~48 s, reused by
every chart forever), and that L5 calibration and cohort priors are inherently cross-chart.

So the shape that works is **hybrid, not pure per-chart**: one shared reference database for the
global substrate, one database per chart for L1–L5. §12.3's partitioning is the migration path — it
delivers most of the isolation benefit now and makes the eventual split mechanical rather than a
rewrite.

### 12.5 Rehearsal chart and determinism harness

**Rehearsal chart.** Chart 3 (`cb73cd3d`) is already unhealthy (31 lit / 14 stale / 14 error) and is
not a serving target, while both canonical charts are. Designate it the standing subject for
destructive and first-run operations, so no elevation step is ever first executed against a
canonical chart. This matters more now that protection is removed.

**Determinism harness.** No test builds an asset twice and compares output — yet content addressing
(Phase 3) assumes exactly that determinism. Build-twice-and-compare-digests for a representative
asset per tier doubles as Phase 3's acceptance test, and is the class of check that would have
caught the frozen-score defect the scoring-signature fix later had to repair.

### 12.6 If protection is ever reinstated

Key it on **(table, generation)**, never on `asset_id`. The removed guard registered gen-3.0
protection under `ka_gochara` while the writer producing gen-3.0 rows was
`ka_gochara_v3_century_materialize`, so it could not distinguish a legitimate write from a
destructive one and blocked the authoritative writer outright (D-02).


*End of NIRMANA_ELEVATION_PLAN_v2_0.md — PROPOSED. Nothing in this artifact has been executed.*
