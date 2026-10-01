---
asset_id: ka_kota_chakra
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
track_i_items: [TI-L3-09, TI-L3-10, TI-L3-13, TI-L3-15, TI-L3-20]
ledger_gap_ids: ["ka_kota_chakra-Earn.build_record", "ka_kota_chakra-Cost.baseline", "ka_kota_chakra-Count.floor", "ka_kota_chakra-Dens.served", "ka_kota_chakra-Build.history", "ka_kota_chakra-Carr.detector", "new: kota-N1", "new: kota-N2", "new: kota-N3", "new: kota-N4"]
---

# ka_kota_chakra — Kota-Chakra fort chart: transiting grahas by ring from the janma nakshatra

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. No SS answer exists yet for L3: the open questions are in section 7 and in the INDEX. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_kota_chakra.py`.*

`services/ka_kota_chakra/writer.py` (+ `logic.py`; shim `pipeline/orchestrator/writers/ka_kota_chakra.py`): from the natal Moon's sidereal longitude (the L1 fact, `:76`) it derives the janma nakshatra, reads the ring partition (stambha, durgantara, prakara, bahya) from L0 `bg_kota_chakra_rings` (`:87`; honest-empty when absent), reads daily tropical positions of the grahas for a horizon of 60 days back to 400 days forward (`:73-74`) from `ephemeris_daily`, corrects to sidereal with one ayanamsha offset at the build date (`:181`), detects contiguous runs of the nakshatra index per graha, and for each run stores the count from janma, the ring, and a posture/severity reading from a hand table (`logic.py:106`) flagged `uncited_extension = true` ("THIS WRITER'S OWN SYNTHESIS"). It refuses with a preserved partition when any graha lacks one row for every horizon day (`:257`) and replaces after assembly. Light writer; served by `query_kota_chakra.ts:110` and the `now` view.

**Canonical chart: `lit`, fresh, 585 rows.** Registry state: throughput `lit`, freshness `fresh`, spec present; latest run `8d74930c` complete/skip_no_delta 2026-09-07; 3 errors and 3 aborts on record, the latest error (2026-08-08) a `KeyError: 1` from positional row indexing against a dict-row connection, fixed in the writer (DB9 comment at `:136`). Live 585 against floor 588 (−3): the window moves with the build date (CF-28). Not part of the 26-asset rebuild plan (its inputs are L0/L1 and it has no dependents); the smoke build of that plan uses the sibling leaf `ka_tithi_pravesha`. Nirmāṇa-frozen under t0 (2026-09-07).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2500` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_kota_chakra.py:6`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_kota_chakra`; count_sql tables: kala_kota_chakra | census |
| live rows / floor | 585 / 588 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `lit`; freshness `fresh`; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ga_positions`, `bg_ephemeris`, `bg_kota_chakra_rings` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 0 / transitive 0 (census blocking_radius, every layer); named (REG 2026-09-30): none | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/tools/kala_views/now.ts`, `registry/layers/L3_kala/query_kota_chakra.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `services/gochara_v3/mechanisms/w25_kota_chakra.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_kota_chakra.ts:110` reads `kala_kota_chakra`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, section 1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | frozen under t0, 2026-09-07 | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8d74930c complete/skip_no_delta (2026-09-07) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8d74930c complete/skip_no_delta (2026-09-07) |
| Count (information, D3) | Count.floor | FAIL | live=585, floor=588, delta=-3 |
| Dens | Dens.served † | FAIL | 1 module(s): query_kota_chakra.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 3 error(s) and 3 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-08): KeyError: 1 Traceback (most recent call last):   File "/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/pipeline/orchestrator/asset_runner.py", line 562, in _run_data_writer     rows_inserte |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Complete.depth; Vocab.identity; Build.exercised; Build.dep_liveness.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 2 module(s) reach it by code: L3_kala/query_kota_chakra.ts, platform-mcp/src/tools/kala_views/now.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 3 declared edge(s); exists: all 3 are active registry assets (every layer); cycle: ka_kota_chakra is on no dependency cycle (registry-wide graph); reads-match: 3 read(s) of other assets' tables, every one covered by a declared edge; static scan of 12 code unit(s), 4 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_kota_chakra-Count.floor | Count | information | live 585 vs floor 588 (−3); rolling window (CF-28) |
| ka_kota_chakra-Dens.served | Dens | Dens rev-1 reading | offline rev-7 FAIL (2 modules, 2 served selects, no contract); no tier column |
| ka_kota_chakra-Build.history | Build | history | 3 errors, 3 aborts; latest error 2026-08-08 (`KeyError: 1`, fixed); CF-10 |
| ka_kota_chakra-Earn.build_record | Earn | detector | CF-05 |
| ka_kota_chakra-Cost.baseline | Cost | information | CF-05 |
| ka_kota_chakra-Carr.detector | Carr | detector | D3: re-count the ring of a sampled run by hand fixture; `janma_nakshatra_fact_id` cites the L1 fact (CF-07) |
| census: Ldgr (no reading) | Ldgr | detector | `ring_table_citation` is not in `CITATION_COLUMNS` (CF-08); the column carries the L0 row's citation text verbatim |
| new: kota-N1 | Idem | real | horizon from `date.today()` (`:239`): rows, floor and receipts move with the build date (CF-28) |
| new: kota-N2 | Vocab | real | `NATURAL_MALEFICS` / `NATURAL_BENEFICS` are local frozensets (`logic.py:95`) that the module's own header says duplicate `ga_yoga_writer.py` and `ga_structural_writer.py`; imports `ALL_GRAHAS`, `NAKSHATRAS`, `NAK_SIZE_DEG` from the L3 service `ka_graha_sancara` (CF-30) |
| new: kota-N3 | honesty | information | the posture/severity labels are the asset's own synthesis, honestly flagged `uncited_extension = true` on every row; the Ldgr/Carr gates have no state for "classically cited ring, uncited reading" (a question for the gate map, not a defect) |
| new: kota-N4 | information | information | one ayanamsha offset is computed at the build date and applied to the whole horizon (<0.02° over ~460 days by the module's own estimate), day-grade precision by campaign design |
| census: Null/Narr | Null, Narr | detector | `prose_fields` null: no free text is composed; `posture`/`severity` are enumerations from `_READING_TABLE`; proposed `[]` (candidate list for the Steward, CF-06) |

## 3 · Disposition

**keep (P)** — one of the four honest Śāḍ-darśana writers: L0 table for the rings, L1 fact for the anchor, a counted refusal on incomplete ephemeris coverage, an explicit uncited-extension flag. Open items are declarations, the rolling window, local malefic sets.

Approver under Track A brief §10: **Steward (G16)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Pin the as-of date and state the rolling floor

- **Answers:** new kota-N1; CF-28, CF-03
- **Change:** read `as_of_date` from the run config (default today, recorded in the build note); declare the asset's floor as rolling (N/A by cause, decided with CF-28) rather than refresh 588
- **Files / declaration / migration:** `services/ka_kota_chakra/writer.py:239`; registry/declarations
- **Failing-first test and mutation:** CF-28 shape: same as-of → identical rows; mutation: ignore the pin → fails.
- **Output change:** none for a fixed as-of
- **Blast radius:** `now.ts` and `query_kota_chakra.ts` readers want a today-relative window: default must stay today
- **Rebuild:** none
- **Gate it moves:** Count (information), Idem
- **Fix class:** writer code + declaration; **buildable before J1:** tier-dependent for the floor declaration

### FD-2 · Use the L0/L1 malefic sets and the shared constants

- **Answers:** new kota-N2; CF-30
- **Change:** import the natural malefic/benefic sets from the L1/L0 authority (or one shared module) and the graha/nakshatra constants from a vocabulary module instead of the service package
- **Files / declaration / migration:** `services/ka_kota_chakra/logic.py:95`, `writer.py` imports
- **Failing-first test and mutation:** Failing-first: an AST check that no local malefic frozenset remains; mutation: re-add one → fails.
- **Output change:** none (same values)
- **Blast radius:** code digest of this writer changes once (delta-skip re-runs it)
- **Rebuild:** none
- **Gate it moves:** Vocab
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-3 · Declare carriage and prose

- **Answers:** census Ldgr (no reading), Null/Narr; CF-06, CF-08
- **Change:** `carriage` declaration naming `ring_table_citation` as the source column and `janma_nakshatra_fact_id` as the L1 anchor; `prose_fields: []` with evidence `logic.py` (`_READING_TABLE` enumerations)
- **Files / declaration / migration:** `asset_declarations.json`
- **Failing-first test and mutation:** inspector reads Ldgr PASS/FAIL on the declared column; a blank citation reads FAIL; declarations validation
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Ldgr, Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01

### Landed or in flight (not designs of this lane)

- **DB9 (dict-row cursor) fixed** in the writer (`KeyError: 1` is the recorded latest error).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* floor 588 (rolling); seed `catalog_status` matches
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]` (candidate list)
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* `ring_table_citation`
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 3 / 3
- **CF-28** — Rolling-horizon writers: as-of pin, calendar-safe horizon, floors that move with the build date. *This asset:* FD-1
- **CF-30** — Duplicated hand-written reference tables in L3 writers (graha -> domain, natural malefics, combustion orbs, Rikta set). *This asset:* FD-2

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, graha, window_start)` (DB UNIQUE, `ON CONFLICT … DO NOTHING`). Volatile columns excluded: `id`, `computed_at`. The horizon is build-date-relative: fingerprint at a fixed as-of window; `start_truncated`/`end_truncated` rows at the horizon edge change with the as-of by design. Rebuild expectation: same rows for the same as-of, ring table version and ephemeris.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the L0 ring table as the sole ring authority, the L1 janma anchor by `fact_id`, the counted refusal on incomplete coverage, `uncited_extension`.
- **Carriage check chosen (T4 §4.1; one only):** D3: re-derive the nakshatra count and ring for a stratified sample of runs from the janma nakshatra and the L0 ring table by an independent hand-written fixture.
- **Opportunities (never blocking):** multi-ayanamsha support is named in the module as additive; a longer horizon for the life arc.

## 7 · Decisions applied and open questions

No SS answer exists yet for L3 (this is the first set). The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

Open questions for Strategic Suvarṇa (consolidated in `INDEX.md` section 7):

- **Q-L3-12** — CF-28: how is a rolling floor declared?

**Track I items arising (see INDEX section 10):** TI-L3-09, TI-L3-10, TI-L3-13, TI-L3-15, TI-L3-20.
