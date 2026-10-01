---
asset_id: ka_muhurta_seva
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
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "none specific to L3 yet; L0 rulings by analogy, PROVISIONAL until the J1 review"
track_i_items: [TI-L3-09, TI-L3-10, TI-L3-12, TI-L3-19, TI-L3-21]
ledger_gap_ids: ["ka_muhurta_seva-Idem.pattern", "ka_muhurta_seva-Build.count_integrity", "ka_muhurta_seva-Earn.build_record", "ka_muhurta_seva-Cost.baseline", "ka_muhurta_seva-Dens.served", "ka_muhurta_seva-Carr.detector", "new: muhurta-N1", "new: muhurta-N2", "new: muhurta-N3", "new: muhurta-N4"]
---

# ka_muhurta_seva — Muhūrta scoring service (panchāṅga + tāra bala + knockout) and its FORENSIC self-test writer

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. No SS answer exists yet for L3: the open questions are in section 7 and in the INDEX. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_muhurta_seva.py`.*

Registry: kind service, scope `global`, no table. The service (`services/ka_muhurta_seva/service.py`) reuses the `score_muhurat()` primitive of the existing muhūrta engine (`muhurat/`, `panchang_engine/`) and is served by `call_muhurta_score` in `call_service_wrappers.ts` with a Nirmāṇa health probe (`probe_id muhurta_seva_forensic`). It is imported in code by `ka_sangam` and `ka_vighnakara` (`KaMuhurtaSevaService`). The registered writer (`services/ka_muhurta_seva/writer.py:20`) is a FORENSIC self-test: it recomputes the birth panchāṅga and asserts the five FORENSIC anchors (tithi 3, vara 1, nakshatra 25, yoga 20, karana 5 — CLAUDE.md §B: Shukla Tritiya, Ravivara, Purva Bhadrapada, Shiva, Garaja), a live tāra-bala check and the knockout path, writes `service_health` and `selftest_detail` to its own row, and raises on failure (`:132`, the pattern the M11 fixes in the sibling services copied). If the `muhurat` package fails to import, the module logs a FATAL and the self-test fails by design (`:37`).

**Canonical chart: global service, `lit`, no freshness row, `service_health` healthy.** Registry state: throughput `lit`, `asset_freshness` absent, spec absent; latest run `fef77aaf` complete 2026-07-26. The rebuild plan's blocker B-3: the planner's service exception fails for an asset with no freshness row, so it blocks `ka_sangam` and `ka_vighnakara` as `UPSTREAM_BLOCKED` unless it is planned (global scope, `super_admin`; wave 1). `ka_sangam`'s upstream digest also stays NULL until this service has a receipt with an `output_digest` (B-2 / I-5: migration 1213 adds the spec, PR #2826 NOT merged at base). Nirmāṇa-frozen under t0 (2026-09-06). No emptied table involved.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | service | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2288` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_muhurta_seva.py:12`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `none (service)`; count_sql tables: none | census |
| live rows / floor | n/a (service) / none (service) | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `lit`; freshness no freshness row; output-digest spec ABSENT; service_health `healthy` | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | none | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 2 / transitive 26 (census blocking_radius, every layer); named (REG 2026-09-30): L3 `ka_sangam`, `ka_vighnakara` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: none; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): none | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | service: served by `call_service_wrappers.ts` (a service call, not a read of rows); declarations `served_surface` null | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | frozen under t0, 2026-09-06 | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PARTIAL | no write to the asset's own table(s) (none declared) anywhere in the resolved scope — nothing to replace; not graded N/A, since a static scan cannot prove a write's absence [resolved scope: services/ka_muhurta_seva/writer.py, panchang_engine/__init__.py, panchang_engine/tara_bala.py, panchang_engine/types.py, muhurat/finder.py, panchang_engine/config_loader.py] |
| Build | Build.target † | N/A | no target_table; asset_kind='service', has_writer=True |
| Build | Build.count_integrity | PARTIAL | count_sql=no, integrity_check_sql=yes |
| Build | Build.completion | N/A | no count_sql and nothing to count: has_writer=True, asset_kind='service', no target_table; build state='lit' |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run fef77aaf complete/no disposition (2026-07-26) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run fef77aaf complete/no disposition (2026-07-26) |
| Dens | Dens.served † | FAIL | 1 module(s): call_service_wrappers.ts; declaring density_contract: 0 |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Build.dag †; Build.exercised; Build.history.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PARTIAL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build NO_DETECTOR.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **NO_DETECTOR** — NO_DETECTOR — 1 module(s) reach it by code: L3_kala/call_service_wrappers.ts, but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 0 declared edge(s); exists: no declared edge to resolve; cycle: ka_muhurta_seva is on no dependency cycle (registry-wide graph); reads-match: 0 read(s) of other assets' tables, every one covered by a declared edge; static scan of 112 code unit(s), 0 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_muhurta_seva-Idem.pattern | Idem | detector | service: nothing to replace (PARTIAL by rev-2 reading); N-22 service rule |
| ka_muhurta_seva-Build.count_integrity | Build | detector | `count_sql` none by design; `integrity_check_sql` present |
| ka_muhurta_seva-Dens.served | Dens | Dens rev-1 reading | offline rev-7 NO_DETECTOR (service call, no served select) |
| ka_muhurta_seva-Earn.build_record | Earn | detector | CF-05 |
| ka_muhurta_seva-Cost.baseline | Cost | information | CF-05 |
| ka_muhurta_seva-Carr.detector | Carr | detector | D3: the FORENSIC anchors are the known-answer carriage (CF-07) |
| new: muhurta-N1 | Build | real | no `asset_freshness` row and no output-digest spec: blocks `ka_sangam` and `ka_vighnakara` in the rebuild plan (B-2, B-3); I-5 covers the spec, not the freshness row |
| new: muhurta-N2 | registry | real | no `source_paths` declared, so a change to `panchang_engine/` or `muhurat/` is not hashed into its code digest (1213 header limit (c): a stale 'healthy' is possible once the service is 'proven' and delta-skips) |
| new: muhurta-N3 | registry | real | `selftest_detail` write: the builder role has no grant (1213 limit (e)); the write at `:298` is wrapped in `try/except` (`:306`) that swallows the failure, which on PostgreSQL leaves the transaction aborted |
| new: muhurta-N4 | Build.dag | registry | seed `depends_on = [ka_graha_sancara]` vs live empty (layer instance 0.3); the writer imports nothing from `ka_graha_sancara`; live is right (CF-03) |
| census: Null/Narr | Null, Narr | detector | `prose_fields` null; the writer composes check strings for the health row only; proposed `[]`; CF-06 |

## 3 · Disposition

**keep (P)** — a correct known-answer self-test over a real engine, raising on failure; the open items are all registry/provenance (freshness row, digest spec, `source_paths`, builder grant) and they matter because two Kāla assets wait on them.

Approver under Track A brief §10: **Steward (G16)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Digest spec, `source_paths` and a freshness row

- **Answers:** new muhurta-N1, N2; CF-26
- **Change:** land migration 1213's spec for this asset after a determinism check on `selftest_detail`; declare `source_paths` (the service package, `panchang_engine/`, `muhurat/`) on the registered class; plan the asset in wave 1 so the planner's freshness exception no longer fails (rebuild plan B-3)
- **Files / declaration / migration:** `services/ka_muhurta_seva/writer.py` (class attribute `source_paths`); migration 1213 (PR #2826)
- **Failing-first test and mutation:** Failing-first: a change to a file under `muhurat/` changes the writer's code digest; two self-test runs digest equal; mutation: remove `source_paths` → the first fails.
- **Output change:** none
- **Blast radius:** `ka_sangam` (upstream digest) and `ka_vighnakara`; both are in the rebuild plan's chain; code digest changes once, so the service re-runs once
- **Rebuild:** a global service dispatch (REVIEW for SS; `super_admin`)
- **Gate it moves:** Earn / Build
- **Fix class:** registry/declaration + class attribute; **buildable before J1:** tier-independent

### FD-2 · Do not swallow the registry write

- **Answers:** new muhurta-N3
- **Change:** let a failed `UPDATE asset_registry` raise (or write inside a SAVEPOINT) so an aborted transaction cannot be committed as a success; the builder grant makes the write succeed (grants item)
- **Files / declaration / migration:** `services/ka_muhurta_seva/writer.py:298-306`
- **Failing-first test and mutation:** Failing-first: with the write failing, the writer raises and the asset reads `error`; mutation: restore the swallow → fails.
- **Output change:** none
- **Blast radius:** the service's own build state; no data
- **Rebuild:** none
- **Gate it moves:** Earn honesty
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-3 · Seed literal and declarations

- **Answers:** new muhurta-N4; CF-03, CF-06
- **Change:** correct the seed `depends_on` and `catalog_status` literals to the live values; declare `prose_fields: []` and the service N-22 rules as for `ka_dasha_kala` FD-4
- **Files / declaration / migration:** `platform/scripts/seed/asset_registry_seed.ts`; `asset_declarations.json`
- **Failing-first test and mutation:** CF-03 seed test
- **Output change:** none
- **Blast radius:** seed only
- **Rebuild:** none
- **Gate it moves:** Build (dag), Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### Landed or in flight (not designs of this lane)

- **I-5 (digest spec) — PR #2826 / migration 1213 NOT merged at base** (FD-1).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed `depends_on` and `catalog_status`
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline NO_DETECTOR; N/A by cause
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3: FORENSIC anchors
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* history: no error on record (PASS)
- **CF-26** — Service self-test assets: output-digest specs, source_paths and builder grants (I-4 / I-5 and the same class left open). *This asset:* FD-1: spec, `source_paths`, builder grant, freshness

## 5 · Semantic fingerprint contract (for E5.5)

No table. Stored output: `service_health` and `selftest_detail` (the FORENSIC check strings, deterministic); `last_selftest_at` is volatile and excluded.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the FORENSIC birth-panchāṅga self-test and the knockout-path assertion.
- **Carriage check chosen (T4 §4.1; one only):** D3: the five FORENSIC anchors are an independent known answer; add one more known-answer instant.
- **Opportunities (never blocking):** extend the self-test to a second known chart; none blocking.

## 7 · Decisions applied and open questions

No SS answer exists yet for L3 (this is the first set). The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

Open questions for Strategic Suvarṇa (consolidated in `INDEX.md` section 7):

- **Q-L3-10** — CF-26: land I-5 and plan this service in wave 1 (global, super_admin)?

**Track I items arising (see INDEX section 10):** TI-L3-09, TI-L3-10, TI-L3-12, TI-L3-19, TI-L3-21.
