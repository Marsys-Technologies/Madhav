---
asset_id: ka_sudarshana_varsha
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
track_i_items: [TI-L3-09, TI-L3-10, TI-L3-15, TI-L3-20]
ledger_gap_ids: ["ka_sudarshana_varsha-Earn.build_record", "ka_sudarshana_varsha-Cost.baseline", "ka_sudarshana_varsha-Dens.served", "ka_sudarshana_varsha-Build.history", "ka_sudarshana_varsha-Carr.detector", "new: sudarshana-N1", "new: sudarshana-N2"]
---

# ka_sudarshana_varsha — Sudarśana-Chakra year-wheel: the three lagnas progressed one sign per year

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. SS ruled the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings that touch this asset are in section 7 and `INDEX.md` section 9; items marked (R) are provisional until the J1 review and anything not listed there remains open. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/services/ka_sudarshana_varsha/writer.py`.*

`services/ka_sudarshana_varsha/writer.py` (+ `logic.py`): reads the natal Lagna, Moon and Sun signs from L1 `chart_facts` (`graha_position`, `sign`, `:46`), and for each of 120 varsha years (`DEFAULT_MAX_VARSHA_YEAR`, `logic.py:57`) advances each reference sign by (N−1) signs (house 1 governs ages 1, 13, 25 …), storing the active sign of the Janma, Chandra and Sūrya lagnas, `tri_lagna_convergence` and a calendar-anniversary window from the birth date (`varsha_window`, "NOT a true tropical/anomalistic solar-return instant" by the module's own statement). Pure arithmetic, no ephemeris. The module records a settled naming ruling: a namesake-only collision with `bo_sudarshana` (L2, a static tri-frame house count): same input facts, categorically different computation. The classical 10-year primary + yearly secondary sub-period structure is out of scope by declaration. Replace-after-assembly (`:184`). Served by `query_sudarshana_varsha.ts:89` and the `now` view.

**Canonical chart: `lit`, fresh, 120 rows.** Registry state: throughput `lit`, freshness `fresh`, spec present; latest run `8d74930c` complete/skip_no_delta 2026-09-07; 0 errors and 3 aborts on record (the saved census reads Build.history PARTIAL on aborts alone). Floor 120 = live 120. Not in the rebuild plan (L1 input only, no dependents). Nirmāṇa-frozen under t0 (2026-09-07).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2526` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/services/ka_sudarshana_varsha/writer.py:116`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_sudarshana_varsha`; count_sql tables: kala_sudarshana_varsha | census |
| live rows / floor | 120 / 120 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `lit`; freshness `fresh`; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ga_positions` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 0 / transitive 0 (census blocking_radius, every layer); named (REG 2026-09-30): none | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/tools/kala_views/now.ts`, `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/query_sudarshana_varsha.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): none | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_sudarshana_varsha.ts:89` reads `kala_sudarshana_varsha`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | frozen under t0, 2026-09-07 | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8d74930c complete/skip_no_delta (2026-09-07) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8d74930c complete/skip_no_delta (2026-09-07) |
| Dens | Dens.served † | FAIL | 1 module(s): query_sudarshana_varsha.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 3 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Build.exercised; Build.dep_liveness.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 2 module(s) reach it by code: L3_kala/query_sudarshana_varsha.ts, platform-mcp/src/tools/kala_views/now.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 1 declared edge(s); exists: all 1 are active registry assets (every layer); cycle: ka_sudarshana_varsha is on no dependency cycle (registry-wide graph); reads-match: 1 read(s) of other assets' tables, every one covered by a declared edge; static scan of 5 code unit(s), 2 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_sudarshana_varsha-Dens.served | Dens | Dens rev-1 reading | offline rev-7 FAIL (2 modules, 2 served selects, no contract; no tier column) |
| ka_sudarshana_varsha-Build.history | Build | history | 0 errors, 3 aborts; CF-10 |
| ka_sudarshana_varsha-Earn.build_record | Earn | detector | CF-05 |
| ka_sudarshana_varsha-Cost.baseline | Cost | information | CF-05 |
| ka_sudarshana_varsha-Carr.detector | Carr | detector | D3: re-derive a sample year by hand fixture; the three natal signs cite `lagna_fact_id`, `moon_fact_id`, `sun_fact_id` (CF-07) |
| census: Ldgr (no reading) | Ldgr | detector | no citation column on the table: the carriage is by L1 `fact_id` columns; a `carriage` declaration (CF-08); a classical source for the technique is not carried |
| new: sudarshana-N1 | Vocab | real | imports `SIGNS` from the L3 service `ka_graha_sancara` (`:34`), a vocabulary constant living inside another asset's package (CF-30) |
| new: sudarshana-N2 | information | information | the year window is a calendar anniversary, not a solar return, by disclosure; true solar-return instants are root-found in L1 (`ga_tajaka_writer._solar_return`, `ga_tajaka_writer.py:237`, a Gaṇita asset) and `ka_tithi_pravesha` root-finds lunar (tithi) returns: three annual-wheel methods with different precision, each labelled |
| census: Null/Narr | Null, Narr | detector | `prose_fields` null: stores sign names/indices read from L1/the shared `SIGNS` tuple, no composed text; proposed `[]`; CF-06 |

## 3 · Disposition

**keep (P)** — an exact, cheap, honestly scoped technique with L1 fact citations. Open items are declarations and one imported constant.

Approver under Track A brief §10: **Steward (G16)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare carriage and prose

- **Answers:** census Ldgr (no reading), Null/Narr; CF-06, CF-08
- **Change:** `carriage` declaration naming `lagna_fact_id`, `moon_fact_id`, `sun_fact_id` as the L1 source columns (and stating that no classical source column exists); `prose_fields: []` with evidence `writer.py`
- **Files / declaration / migration:** `asset_declarations.json`
- **Failing-first test and mutation:** inspector Ldgr reads the declared columns; a blank fact id reads FAIL; declarations validation
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Ldgr, Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01

### FD-2 · Take `SIGNS` from a vocabulary module

- **Answers:** new sudarshana-N1; CF-30
- **Change:** import the sign-name tuple from an L0 vocabulary module (shared with FD-2 of `ka_graha_sancara`)
- **Files / declaration / migration:** `writer.py:34`
- **Failing-first test and mutation:** AST check: one definition of the sign tuple; mutation: add a local copy → fails.
- **Output change:** none
- **Blast radius:** writer code digest changes once
- **Rebuild:** none
- **Gate it moves:** Vocab
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-3 · Carr: re-derivation sample

- **Answers:** census Carr; CF-07
- **Change:** D3 detector: for a sample of varsha years, recompute the three active signs from the cited natal sign facts by an independent fixture and compare
- **Files / declaration / migration:** detector (Track E); `tests/l3/test_ka_sudarshana_varsha.py`
- **Failing-first test and mutation:** Failing-first: a seeded wrong active sign is reported; mutation: perturb one year → count ≥ 1.
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T3-02

### Landed or in flight (not designs of this lane)

No Track I item touches this asset.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* carriage by fact id
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 0 / 3
- **CF-30** — Duplicated hand-written reference tables in L3 writers (graha -> domain, natural malefics, combustion orbs, Rikta set). *This asset:* FD-2
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* table-wide `integrity_check_sql` (audit; none measured false)

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, varsha_year)` (DB UNIQUE). Volatile columns excluded: `id`, `computed_at`. Deterministic given the birth date and the three natal signs; no as-of dependence. Rebuild expectation: byte-identical rows (a good candidate to prove the E5.5 fingerprint on).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the exact year-wheel progression with L1 fact citations and the recorded namesake ruling.
- **Carriage check chosen (T4 §4.1; one only):** D3: re-derive the active signs for a stratified sample of years by hand fixture.
- **Opportunities (never blocking):** the 10-year sub-period structure is a named additive follow-on; a solar-return-instant window could read the L1 `ga_tajaka` solar-return instants rather than root-finding again.

## 7 · Decisions applied and open questions

SS answered the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings for this asset are in the block below. (R) = raises or defines a verdict or changes outputs: provisional until the J1 review. The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

**SS rulings (2026-10-01) for this asset:**

- **Q-L3-16 (R) — accepted.** The L0 rulings Q1 (completion by count), Q2 (Dens applicability, `uniform_authority`), Q11 (Build.history window) and Q13 (Carr D1 / N-A for ratified judgment) carry to L3, provisionally until the J1 review.

No question is open for this asset beyond the plane-wide ones in the INDEX.

**Track I items arising (see INDEX section 10):** TI-L3-09, TI-L3-10, TI-L3-15, TI-L3-20.
