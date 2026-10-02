---
asset_id: ka_graha_sancara
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
decisions_applied: "SS decision-sheet rulings of 2026-10-01 (section 7; (R) items provisional until J1); L0 rulings by analogy, PROVISIONAL until the J1 review"
track_i_items: [TI-L3-09, TI-L3-10, TI-L3-12, TI-L3-19, TI-L3-21, TI-L3-36]
ledger_gap_ids: ["ka_graha_sancara-Idem.pattern", "ka_graha_sancara-Build.count_integrity", "ka_graha_sancara-Earn.build_record", "ka_graha_sancara-Cost.baseline", "ka_graha_sancara-Dens.served", "ka_graha_sancara-Carr.detector", "new: graha_sancara-N1", "new: graha_sancara-N2", "new: graha_sancara-N3", "new: graha_sancara-N4"]
---

# ka_graha_sancara — Ephemeris-at-t service (graha positions at an arbitrary time) and its FORENSIC self-test writer

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. SS ruled the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings that touch this asset are in section 7 and `INDEX.md` section 9; items marked (R) are provisional until the J1 review and anything not listed there remains open. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_graha_sancara.py`.*

Registry: kind service, scope `global`, no table. The service (`services/ka_graha_sancara/engine.py`; the package is 468 lines, the writer module 268) provides `get_ephemeris` (positions at an arbitrary datetime) and the shared constants `ALL_GRAHAS`, `NAKSHATRAS`, `NAK_SIZE_DEG`, `SIGNS`. It is served by `call_ephemeris_at_t` (`call_service_wrappers.ts`) with a Nirmāṇa health probe (`service_probe`, `probe_id graha_sancara_forensic`). The registered writer (`ka_graha_sancara.py:47`) is a known-answer self-test: for the native's birth instant (`_BIRTH_DT_ISO`, `:40`) it asserts nine grahas with speeds and the Moon in Aquarius (`_FORENSIC_MOON_SIGN`, `:44`), then a stored-ephemeris read check, writes `service_health` and `selftest_detail`, and raises when not healthy (`:94`, the M11 fix: before it, an unhealthy self-test still returned a normal result and the asset was promoted to `lit`).

**Canonical chart: global service, throughput `lit`; recorded `service_health` = `unhealthy`.** Registry state read for the rebuild plan (2026-10-01 14:5x): throughput `lit`, `service_health unhealthy`, no output-digest spec. Latest run `fef77aaf` complete 2026-07-26 (it predates commit `97fd08e1c`, 2026-09-05, #1751, which added the M11 raise (comment at `:86`) and the `KeyError: 0` selftest fix (M3 note at `:210`)); so the registry says lit and unhealthy at once — the §N.8 mismatch M11 closed for future runs but not for the stored row. A new run would re-measure it. Nirmāṇa-frozen under t0 (2026-09-06). No emptied table is involved.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | service | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2256` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_graha_sancara.py:47`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `none (service)`; count_sql tables: none | census |
| live rows / floor | n/a (service) / none (service) | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `lit`; freshness no freshness row; output-digest spec ABSENT; service_health `unhealthy` | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `bg_ephemeris` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 0 / transitive 0 (census blocking_radius, every layer); named (REG 2026-09-30): none | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: none; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): none | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | service: served by `call_service_wrappers.ts` (a service call, not a read of rows); declarations `served_surface` null | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | frozen under t0, 2026-09-06 | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PARTIAL | no write to the asset's own table(s) (none declared) anywhere in the resolved scope — nothing to replace; not graded N/A, since a static scan cannot prove a write's absence [resolved scope: ka_graha_sancara.py, services/ka_graha_sancara/engine.py, brahmagyan/l0_ephemeris.py] |
| Build | Build.target † | N/A | no target_table; asset_kind='service', has_writer=True |
| Build | Build.count_integrity | PARTIAL | count_sql=no, integrity_check_sql=yes |
| Build | Build.completion | N/A | no count_sql and nothing to count: has_writer=True, asset_kind='service', no target_table; build state='lit' |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run fef77aaf complete/no disposition (2026-07-26) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run fef77aaf complete/no disposition (2026-07-26) |
| Dens | Dens.served † | FAIL | 1 module(s): call_service_wrappers.ts; declaring density_contract: 0 |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Build.dag †; Build.exercised; Build.history; Build.dep_liveness.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PARTIAL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build NO_DETECTOR.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **NO_DETECTOR** — NO_DETECTOR — 1 module(s) reach it by code: L3_kala/call_service_wrappers.ts, but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 1 declared edge(s); exists: all 1 are active registry assets (every layer); cycle: ka_graha_sancara is on no dependency cycle (registry-wide graph); reads-match: 1 read(s) of other assets' tables, every one covered by a declared edge; static scan of 6 code unit(s), 1 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_graha_sancara-Idem.pattern | Idem | detector | service: nothing to replace (PARTIAL by rev-2 reading); N-22 service rule |
| ka_graha_sancara-Build.count_integrity | Build | detector | `count_sql` none by design; `integrity_check_sql` present |
| ka_graha_sancara-Dens.served | Dens | Dens rev-1 reading | offline rev-7 NO_DETECTOR (service call, no served select of rows) |
| ka_graha_sancara-Earn.build_record | Earn | detector | CF-05; the recorded `unhealthy` beside `lit` is the instance |
| ka_graha_sancara-Cost.baseline | Cost | information | CF-05 |
| ka_graha_sancara-Carr.detector | Carr | detector | D3: the FORENSIC known-answer test is the carriage; CF-07 |
| new: graha_sancara-N1 | Build | stale/real | recorded state `unhealthy` + `lit` (above); needs a run to re-measure; the writer raises on a degraded result now |
| new: graha_sancara-N2 | Build.dag | real | declared dependents 0 (census radius 0/0) but code importers are many: `ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_sudarshana_varsha`, `ka_vedha_gochara` import its constants, and `pyjhora_adapter/transits.py:74` and `brahmagyan/phala/muhurta.py:729` import `get_ephemeris` (grep of `platform/python-sidecar`); the registry understates the asset's real coupling (not DAG data reads, so no missing edge is claimed) |
| new: graha_sancara-N3 | registry | real | no output-digest spec (same class as 1213; not covered by PR #2826); the builder grant gap applies to `selftest_detail` |
| new: graha_sancara-N4 | honesty | information | the self-test is pinned to one native's birth instant by design (a known-answer test); `service_health = healthy` therefore means "the engine reproduces the FORENSIC anchor", not "every chart works" |
| census: Null/Narr | Null, Narr | detector | `prose_fields` null; the writer composes only error strings for the health row; proposed `[]`; CF-06 |

## 3 · Disposition

**keep (P)** — a shared engine other writers import, with a genuine known-answer self-test. The gaps are the stored `unhealthy`/`lit` mismatch (a run re-measures it), the missing digest spec, and declarations.

Approver under Track A brief §10: **Steward (G16)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Re-measure the service and land its digest spec

- **SS ruling (2026-10-01):** the spec is accepted (Q-L3-10); the global dispatch is yes in principle and comes to SS as a REVIEW when the time comes (Q-L3-11). TI-L3-12, TI-L3-36.
- **Answers:** new graha_sancara-N1, N3; CF-26
- **Change:** run the self-test (a production dispatch; global scope needs `super_admin`) so the registry row is re-measured; add a digest spec in the 1213 shape (`service_health`, `selftest_detail`) after a determinism check (two runs, byte-identical `selftest_detail`)
- **Files / declaration / migration:** a new spec migration (number = max+1 at execution time); `ka_graha_sancara.py` unchanged
- **Failing-first test and mutation:** Failing-first: two consecutive runs digest equal; mutation: a volatile field in the hashed set → fails.
- **Output change:** none
- **Blast radius:** the registry health row; no data table; importers are unaffected (code, not data)
- **Rebuild:** a service dispatch (REVIEW for SS), no data rows
- **Gate it moves:** Earn / Build
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent

### FD-2 · Move the shared constants out of the service package

- **Answers:** new graha_sancara-N2; CF-30
- **Change:** `ALL_GRAHAS`, `NAKSHATRAS`, `NAK_SIZE_DEG`, `SIGNS` live in `services/ka_graha_sancara/engine.py` and are imported by four L3 writers; place them in the L0 vocabulary module (`brahmagyan/graha_vocabulary.py` is the existing precedent for the graha names) so a change to the service cannot change a table writer's output unnoticed
- **Files / declaration / migration:** `services/ka_graha_sancara/engine.py`, the four importers, a vocabulary module
- **Failing-first test and mutation:** Failing-first: the constants have one definition (an AST check); mutation: re-add a local copy → fails.
- **Output change:** none (same values)
- **Blast radius:** four writers' code digests change once (they hash imported local modules, `asset_runner._writer_source_files`), so their delta-skip re-runs once; no data change
- **Rebuild:** none
- **Gate it moves:** Vocab (§N.7 item 3)
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-3 · Service declarations and `prose_fields: []`

- **Answers:** census Idem/count_integrity/Null/Narr; CF-06
- **Change:** as for `ka_dasha_kala` FD-4: declare `[]` with `evidence.prose_fields` → `ka_graha_sancara.py` (health strings only); propose Idem N/A by measured cause
- **Files / declaration / migration:** `asset_declarations.json`
- **Failing-first test and mutation:** declarations validation; mutation as CF-06
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Idem, Build, Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### Landed or in flight (not designs of this lane)

- **M11 (raise on unhealthy) and the `KeyError: 0` selftest fix are in the writer** (`:86`); the stored row predates them.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed `catalog_status` DRAFT vs CURRENT live
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline NO_DETECTOR; N/A by cause
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent; the unhealthy/lit row
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3: the FORENSIC known-answer test
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* history: no error on record (PASS)
- **CF-26** — Service self-test assets: output-digest specs, source_paths and builder grants (I-4 / I-5 and the same class left open). *This asset:* FD-1: same class as 1213, not covered
- **CF-30** — Duplicated hand-written reference tables in L3 writers (graha -> domain, natural malefics, combustion orbs, Rikta set). *This asset:* FD-2

## 5 · Semantic fingerprint contract (for E5.5)

No table. Stored output: `service_health` and `selftest_detail` on the registry row; `last_selftest_at` volatile, excluded. Expected after a run: `healthy` with the nine-graha and FORENSIC checks listed.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the shared ephemeris-at-t engine and the known-answer self-test.
- **Carriage check chosen (T4 §4.1; one only):** D3: the FORENSIC anchor (Moon in Aquarius at 1984-02-05 10:43 IST, CLAUDE.md §B) is itself the independent re-derivation; extend with a second ephemeris read at another instant.
- **Opportunities (never blocking):** serve a per-instant positions tool for any chart (it already exists as `call_ephemeris_at_t`); none blocking.

## 7 · Decisions applied and open questions

SS answered the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings for this asset are in the block below. (R) = raises or defines a verdict or changes outputs: provisional until the J1 review. The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

**SS rulings (2026-10-01) for this asset:**

- **Q-L3-10 — accepted.** Digest spec in the 1213 shape after a determinism check (FD-1). Track I: TI-L3-12.
- **Q-L3-11 — yes in principle.** The global-scope dispatch of the self-test is not authorised now: it comes to SS as a REVIEW item when the time comes (the recorded `unhealthy` predates the 2026-09-05 fix). Track I: TI-L3-36.

Questions put to Strategic Suvarṇa (all answered 2026-10-01, see the block above; kept for the record; consolidated in `INDEX.md` section 9):

- **Q-L3-10** — CF-26: extend digest specs to `ka_graha_sancara`?
- **Q-L3-11** — run the self-test as a global-scope dispatch (super_admin)?

**Track I items arising (see INDEX section 10):** TI-L3-09, TI-L3-10, TI-L3-12, TI-L3-19, TI-L3-21, TI-L3-36 (added by the SS rulings of 2026-10-01).
