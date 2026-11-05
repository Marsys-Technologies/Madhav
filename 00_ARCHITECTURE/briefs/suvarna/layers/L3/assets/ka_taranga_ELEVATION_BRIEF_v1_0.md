---
asset_id: ka_taranga
layer: L3 Kāla (ka_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L3 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L3/L3_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 066c58587"
disposition: "qualify (Q)"
disposition_proposal_approver: "Steward (G16) for qualify; retiring the event-class half and the ayanamsha pin are output changes → SS (R5)"
decisions_applied: "SS decision-sheet rulings of 2026-10-01 (section 7; (R) items provisional until J1); L0 rulings by analogy, PROVISIONAL until the J1 review. Prior-campaign evidence (Nirmāṇa W2 §3 SPLIT ruling) is quoted from migration 670 as a pointer and was re-checked against main's code"
track_i_items: [TI-L3-01, TI-L3-04, TI-L3-07, TI-L3-09, TI-L3-10, TI-L3-15, TI-L3-16, TI-L3-17, TI-L3-20, TI-L3-31]
ledger_gap_ids: ["ka_taranga-Earn.build_record", "ka_taranga-Cost.baseline", "ka_taranga-Dens.served", "ka_taranga-Build.history", "ka_taranga-Build.dep_liveness", "ka_taranga-Carr.detector", "new: taranga-N1", "new: taranga-N2", "new: taranga-N3", "new: taranga-N4", "new: taranga-N7", "new: taranga-N8", "new: taranga-N5", "new: taranga-N6"]
---

# ka_taranga — Activation waveform: monthly dasha × transit × promise activation by domain and event class (1950-2100)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. SS ruled the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings that touch this asset are in section 7 and `INDEX.md` section 9; items marked (R) are provisional until the J1 review and anything not listed there remains open. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_taranga.py`.*

`ka_taranga.py`: for every month from 1950-01 to 2100-12 (1,812 months; `:45-46`) and every scope it stores an `activation` in [0,1] and its three components: `dasha_contribution` (1.0 if the Vimshottari MD lord's hand-listed domains include the domain, else 0.15, `:195`), `transit_contribution` (the mean `convergence_score` of `kala_convergence` windows overlapping the month for the domain) and `promise_contribution` (`bodha_pratijna` grade / 10), combined by the rule the writer INLINES twice (`:199` for domains, `:227` for event classes): the harmonic mean of the positive terms when the promise term is positive, else the arithmetic mean of dasha and transit. The shared kernel carries a copy of the same rule for the live on-demand service (`combine_activation`, `services/taranga_kernel/kernel.py:55`, described there as verbatim from the writer); the batch writer imports only `harmonic_mean`, `month_range` and `GRAHA_DOMAINS` from the kernel, so a change to the kernel's rule would not reach the batch rows. 92,412 canonical rows = 1,812 months × 51 scopes: 24 domains (43,488 rows) plus 27 event classes (48,924 rows), the split stated in `L3_W2_DECIDE_v1_0.md` (lines 132-138) and consistent by arithmetic (24 × 1,812 and 27 × 1,812). Light writer, `DELETE` then batch insert. **A second writer exists:** `taranga_service.record_evidence` (`services/taranga_service.py:773`) upserts evidence rows into the same table on the same natural key (`scope_kind` `domain`, or `event_class` with a mechanism id as `scope_id`), with a different `components` shape (`inputs`, `cited_by`, `detail`) and no `dasha_lord` key. Served by `query_activation_waveform.ts:100`; the only reader (census radius 0/0).

**Canonical chart: 92,412 rows present, throughput `stale`.** Table not emptied (no signal key); written 2026-08-13 by run `cbd6ea44` while `kala_convergence` still had canonical rows, so the stored `transit_contribution` reflects that older convergence set, which no longer exists for the chart. Dependencies 2 of 5 lit: `ka_avadhi` is `error` (a phantom edge: the writer never reads it, CF-23) and `bo_pratijna`, `ka_sangam` are stale. 30 errors and 11 aborts on record. In the rebuild plan's downstream-not-in-plan set (`stale`, section 1.4). Output-digest spec present (migration 1021). Not Nirmāṇa-frozen.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2471` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_taranga.py:73`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_taranga`; count_sql tables: kala_taranga | census |
| live rows / floor | 92,412 / 92,412 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `stale`; freshness no freshness row; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ka_avadhi`, `ka_sangam`, `bo_pratijna`, `ga_dashas`, `bg_ghatana` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 0 / transitive 0 (census blocking_radius, every layer); named (REG 2026-09-30): none | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/query_activation_waveform.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `services/taranga_kernel/__init__.py`, `services/taranga_kernel/kernel.py`, `services/taranga_service.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_activation_waveform.ts:100` reads `kala_taranga`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | not frozen (not in the L3 list of NIRMANA_SUPERSESSION_RECORD §2.3) | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Dens | Dens.served † | FAIL | 1 module(s): query_activation_waveform.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 30 error(s) and 11 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) ka_sangam did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | FAIL | 2/5 declared dependencies lit at chart 482012f1 (or global); not live: ['ka_avadhi (error, chart 482012f1)']; stale: ['bo_pratijna (stale, chart 482012f1)', 'ka_sangam (stale, chart 482012f1)'] — a DEP-ASSERT trap if no writer can light them |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Build.exercised.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 1 module(s) reach it by code: L3_kala/query_activation_waveform.ts; 4 served select(s) of its table; no referencing capability that serves it declares density_contract

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 5 declared edge(s); exists: all 5 are active registry assets (every layer); cycle: ka_taranga is on no dependency cycle (registry-wide graph); reads-match: 4 read(s) of other assets' tables, every one covered by a declared edge; static scan of 4 code unit(s), 4 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_taranga-Dens.served | Dens | Dens rev-1 reading | offline rev-7 FAIL (1 module, 4 served selects, no contract; no tier column) |
| ka_taranga-Build.history | Build | history | 30 errors, 11 aborts; latest cascade `BLOCKED` 2026-08-12 (CF-10) |
| ka_taranga-Build.dep_liveness | Build | real (phantom edge) | FAIL: `ka_avadhi (error)`; the edge is declared and never read (CF-23); also `bo_pratijna`, `ka_sangam` stale (clears with the chain) |
| ka_taranga-Earn.build_record | Earn | detector | CF-05 |
| ka_taranga-Cost.baseline | Cost | information | CF-05 |
| ka_taranga-Carr.detector | Carr | detector | D3: re-derive the stamped dasha lord from `chart_dashas` (integrity conjunct (a), which already does this) and the activation from its stored components (no existing conjunct does: conjunct (d) only checks that the dasha term is a function of lord and domain); CF-07 |
| census: Ldgr (no reading) | Ldgr | detector | no citation column on `kala_taranga`; the carriage is by derivation from named inputs (CF-08) |
| new: taranga-N1 | honesty | real | the event-class half is degenerate by construction: `d_contrib = 1.0 if lord and any(d in lord_domains for d in _GRAHA_DOMAINS.get(lord, []))` (`:222`) where `lord_domains = set(_GRAHA_DOMAINS.get(lord, []))`, so the test is true whenever the lord has any domain (all nine do), and the dasha contribution is 1.0 for every event class in every month; and `t_contrib = max(...)` takes the largest convergence score across ALL domains, not the event class's. The scope rows differ only by their promise term. Migration 670 records the same finding as a prior ruling: "W2 §3 ruled this asset a SPLIT: the scope_kind='domain' half is the genuine independent witness and is KEPT -- the scope_kind='event_class' half is degenerate and is to be retired" (`670_nirmana_l3_w3_integrity_contracts.sql:1328`); the writer still emits both halves |
| new: taranga-N2 | Idem / honesty | real | `chart_dashas` is read for `level_n = 1 AND system_id = 'vimshottari'` with no `ayanamsha_id` filter (`:95`), although the table pools five ayanamshas whose boundaries drift by days (the CR-110 double-spine class that `ka_avadhi` and `ka_jivana_parva` pin to lahiri); `_lord_for_month` takes the first overlapping row (`:155`), so for months near a boundary the stamped lord depends on row order. The migration 670 header calls its conjunct (a) "also the CR-110 double-spine detector for this asset" (`670_nirmana_l3_w3_integrity_contracts.sql:1334`) |
| new: taranga-N3 | Idem | real | DELETE (`:85`) precedes the no-MD-rows return (`:104`), whose note also names a service that writes nothing to `chart_dashas` ("run ka_dasha_kala first"): CF-21 |
| new: taranga-N4 | honesty | real | the module docstring says "harmonic_mean(dasha, transit, promise) where all three > 0, else arithmetic mean of available components" (`:18`); the code takes the harmonic mean of the POSITIVE terms whenever the promise term is positive and otherwise `(dasha + transit)/2` including a zero transit — different rules from the one stated |
| new: taranga-N7 | Idem | real | the batch writer's chart-wide `DELETE` (`:85`) also removes any `record_evidence` rows the on-demand service wrote for the chart (same table, same key); the evidence rows are therefore not durable across a rebuild (an inference from the two code paths; whether that is intended is a question for SS) |
| new: taranga-N8 | honesty | real | the pratijna read runs in a SAVEPOINT and a failure is logged at debug level and skipped (`:124`, `except` at `:150`), after which every promise term is 0 and every row takes the arithmetic-mean branch: a failed read is indistinguishable from a chart with no pratijna rows (CF-29) |
| new: taranga-N5 | Vocab | real | `GRAHA_DOMAINS` (`services/taranga_kernel/kernel.py:32`) disagrees with `ka_avadhi._GRAHA_DOMAINS` (CF-30); 0.15 / 0.1 non-matching floors are literals (CF-27) |
| new: taranga-N6 | information | information | the waveform spans 1950-2100 although the native was born in 1984; pre-birth months carry the same formula (the `ka_kalasutra` note says pre-birth cycles are not life-indexable) |
| census: Null/Narr | Null, Narr | detector | `prose_fields` null: numbers and a constant `formula_note`; proposed `[]`; CF-06 |

## 3 · Disposition

**qualify (Q)** — half of what the asset stores is a real, falsifiable domain-level composition; the other half (event class) cannot vary with the event class and a prior campaign ruled it should be retired. Narrowing the asset to the domain scope (FD-1) and pinning the dasha spine (FD-2) changes output, so it goes to SS; the phantom edge (FD-3) and the order defect (FD-4) are tier-independent.

Approver under Track A brief §10: **Steward (G16) for qualify; retiring the event-class half and the ayanamsha pin are output changes → SS (R5)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Retire the degenerate event-class half (or fix its two terms)

- **SS ruling (2026-10-01) (R):** option R, retire the batch event-class rows (92,412 -> 43,488 rows per chart); a design REVIEW follows and must state which served surfaces read those rows. TI-L3-31.
- **Answers:** new taranga-N1; CF-27
- **Change:** stop writing `scope_kind = 'event_class'` rows (the W2 §3 SPLIT), or make them mean something: a per-event-class dasha term from the lord's relation to the event class's domain, and a transit term from windows whose domain equals the event class's domain; the on-demand service (`taranga_service.py`) and its `record_evidence` write path must follow the same choice
- **Files / declaration / migration:** `ka_taranga.py:220-227`; of the migration 670 conjuncts, (a), (b), (b2), (c) and the same-lord-per-month check run over both halves, while (d) and (e) assert only the domain half; nothing checks the event-class half for non-degeneracy
- **Failing-first test and mutation:** Failing-first: with two event classes of different domains the stored rows differ in more than the promise term (fix option), or no event-class rows are written (retire option); mutation: restore the tautology → fails.
- **Output change:** yes — removes (or changes) event-class rows, i.e. the 48,924 event-class rows of the 92,412 (27 of the 51 scopes) → SS (R5)
- **Blast radius:** `query_activation_waveform.ts:100` reads `kala_taranga` by scope; `taranga_service.record_evidence` WRITES `scope_kind = event_class` rows (mechanism ids) into the same table on the same key, so retiring the batch event-class half must keep that path distinguishable from batch rows (the batch `DELETE` is per chart and would also remove evidence rows the service wrote); no python reader of the batch event-class rows was found
- **Rebuild:** needs production rebuild (REVIEW for SS)
- **Gate it moves:** Carr / honesty (a status that cannot vary is not evidence)
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-independent for the mechanics; SS decides retire vs fix

### FD-2 · Pin the Vimshottari read to the canonical ayanamsha

- **SS ruling (2026-10-01):** accepted (Q-L3-03). TI-L3-04.
- **Answers:** new taranga-N2
- **Change:** add `AND ayanamsha_id = 'lahiri_chitrapaksha'` to the MD read (the pin `ka_avadhi` and `ka_jivana_parva` carry), so one row per MD period feeds `_lord_for_month`
- **Files / declaration / migration:** `ka_taranga.py:95`
- **Failing-first test and mutation:** Failing-first: a fixture with two ayanamshas whose MD boundaries differ by days returns the canonical lord for the boundary month in both row orders; mutation: drop the pin → fails.
- **Output change:** yes — `components.dasha_lord` and the dasha term in months near a boundary → SS (R5)
- **Blast radius:** `dasha_lord` is a stored component; the registry integrity conjunct (a) already requires the canonical-ayanamsha lord, so rows that pass it today would not change; rows that fail it would be corrected
- **Rebuild:** needs production rebuild (REVIEW for SS)
- **Gate it moves:** Idem / Carr
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-independent

### FD-3 · Remove the phantom `ka_avadhi` edge

- **Answers:** ka_taranga Build.dep_liveness; CF-23
- **Change:** registry migration removing `ka_avadhi` from `depends_on`; correct the docstring and the "run ka_dasha_kala first" note
- **Files / declaration / migration:** a registry migration (CF-23 batch); `ka_taranga.py` docstring/notes
- **Failing-first test and mutation:** CF-23 over-declaration report; the dep_liveness cell no longer names `ka_avadhi`
- **Output change:** none
- **Blast radius:** one upstream hash changes once; `ka_avadhi`'s declared radius 1 → 0; no Nirmāṇa manifest for this asset
- **Rebuild:** none
- **Gate it moves:** Build.dep_liveness
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent in content, DAG change: own review

### FD-4 · Replace-after-candidate; state the formula as coded

- **Answers:** new taranga-N3, N4; CF-21
- **Change:** delete after the candidate exists (CF-21); correct the docstring to the coded combination rule (or change the code to the stated rule: an output change)
- **Files / declaration / migration:** `ka_taranga.py:85-104`, `:18`
- **Failing-first test and mutation:** CF-21 shape; mutation as CF-21
- **Output change:** none for the docstring/order fix
- **Blast radius:** readers as above
- **Rebuild:** none
- **Gate it moves:** Idem
- **Fix class:** writer code; **buildable before J1:** tier-independent

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset; the 2026-09 integrity contract (migration 670) restricts its dasha-term checks (d) and (e) to the domain half and leaves the rest over both halves.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3: conjuncts (a), (d)
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* no citation column
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 30 / 11
- **CF-21** — Replace-after-candidate: DELETE runs before the empty-upstream early return (five writers). *This asset:* FD-4
- **CF-23** — depends_on audit: declared edges the writer never reads, and the bhavishya back-read. *This asset:* FD-3: phantom edge
- **CF-24** — L2 -> L3 cascade keys and rebuild order (F-3 / migration 1214): four emptied tables and the dangling predicate set. *This asset:* not emptied; its transit inputs are gone until `ka_sangam` re-lands
- **CF-27** — Documented-approximation constants and favourable defaults in the L3 temporal chain (the L2 CF-20 class). *This asset:* 0.15/0.1 floors; harmonic combination
- **CF-29** — Honest absence versus unavailable: swallowed detector failures, proxy fallbacks and soft reads that degrade to empty. *This asset:* the promise term degrades to 0 on a failed read (`sp_taranga_pratijna`, `taranga-N8`)
- **CF-30** — Duplicated hand-written reference tables in L3 writers (graha -> domain, natural malefics, combustion orbs, Rikta set). *This asset:* graha → domain table
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* conjunct (a) is the ayanamsha detector

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, month, scope_kind, scope_id)`; only a surrogate `taranga_id` otherwise. Volatile columns excluded: `taranga_id`, `computed_at`. `activation` and `components` are deterministic given the Vimshottari spine (once pinned, FD-2), the convergence set and the pratijna grades; fingerprint after `ka_sangam` and `bo_pratijna` have re-landed. Rebuild expectation: 92,412 rows (1,812 × 51) until FD-1 changes the scope set.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the domain-level composition and its integrity contract (tiling, lord authority, formula consistency, non-degeneracy), the shared kernel with the live caller.
- **Carriage check chosen (T4 §4.1; one only):** D3: re-derive `dasha_lord` from `chart_dashas` (canonical ayanamsha; integrity conjunct (a) is the existing check) and the `activation` from the stored components for a stratified sample of months and domains (no existing conjunct recomputes the activation).
- **Opportunities (never blocking):** drop pre-birth months; serve the waveform per domain only.

## 7 · Decisions applied and open questions

SS answered the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings for this asset are in the block below. (R) = raises or defines a verdict or changes outputs: provisional until the J1 review. The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

**SS rulings (2026-10-01) for this asset:**

- **A-3 (R) — event-class tautology: option R.** Retire the batch event-class rows (`scope_kind='event_class'`); output change 92,412 -> 43,488 rows per chart (24 x 1,812 domain rows remain). A design REVIEW follows and must state which served surfaces read those rows (the decision sheet found `query_activation_waveform.ts:100`, which filters by scope, and no python reader of batch event-class rows; the live service `taranga_service.py` and `record_evidence` also use `event_class` scope and the batch `DELETE` must not remove the evidence rows). Replaces FD-1's retire-or-fix choice. Track I: TI-L3-31 (supersedes the FD-1 half of TI-L3-04).
- **Q-L3-03 — accepted.** Pin the Vimshottari read to `lahiri_chitrapaksha` (FD-2); no stored `dasha_lord` changes on any of the three charts. Track I: TI-L3-04 (FD-2 half).
- **Q-L3-04 (R) — accepted.** One shared graha -> domain table whose values are members of `CANONICAL_DOMAINS`; both local tables are deleted (taranga's 24 domain scopes fall to at most 13). Track I: TI-L3-15.
- **Q-L3-08 — accepted.** Remove the unread `ka_avadhi` edge (FD-3). Track I: TI-L3-07.
- **Q-L3-01 — accepted** (CF-27 split; 0.15 / 0.1 floors are scale choices under option 1). Track I: TI-L3-17.

Questions put to Strategic Suvarṇa (all answered 2026-10-01, see the block above; kept for the record; consolidated in `INDEX.md` section 9):

- **Q-L3-03** — FD-1: retire the event-class half (the W2 §3 SPLIT) or fix its two terms; FD-2: pin the ayanamsha?

**Track I items arising (see INDEX section 10):** TI-L3-01, TI-L3-04, TI-L3-07, TI-L3-09, TI-L3-10, TI-L3-15, TI-L3-16, TI-L3-17, TI-L3-20, TI-L3-31 (added by the SS rulings of 2026-10-01).
