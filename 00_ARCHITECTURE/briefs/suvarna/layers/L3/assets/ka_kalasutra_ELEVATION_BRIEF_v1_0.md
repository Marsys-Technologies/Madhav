---
asset_id: ka_kalasutra
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
disposition_proposal_approver: "Steward (G16); the output changes in CF-27 go to SS (R5)"
decisions_applied: "none specific to L3 yet; L0 rulings by analogy, PROVISIONAL until the J1 review"
track_i_items: [TI-L3-01, TI-L3-05, TI-L3-09, TI-L3-10, TI-L3-17, TI-L3-20]
ledger_gap_ids: ["ka_kalasutra-Build.completion", "ka_kalasutra-Earn.build_record", "ka_kalasutra-Cost.baseline", "ka_kalasutra-Count.floor", "ka_kalasutra-Dens.served", "ka_kalasutra-Build.history", "ka_kalasutra-Build.dep_liveness", "ka_kalasutra-Carr.detector", "new: kalasutra-N1", "new: kalasutra-N2", "new: kalasutra-N3", "new: kalasutra-N4", "new: kalasutra-N5", "new: kalasutra-N6"]
---

# ka_kalasutra — Bounded activation windows per activation predicate (dasha-resolved, convergence-refined)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. No SS answer exists yet for L3: the open questions are in `INDEX.md` section 9. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_kalasutra.py`.*

`ka_kalasutra.py`: for every `kala_activation_predicates` row of the chart (the `ka_yojaka` output, `:45`) it resolves activation windows through the shared deterministic helper `services/ka_temporal` (`resolve_activation_windows`, `:109`): a convergence peak refines a window (half-widths 7/14/5/5 days by signature class); without one, the matched daśā period of the predicate's own ayanamsha timeline, birth-forward, supplies real start/end/peak dates (WP-2.1: "No fabricated dates (B.10): every date traces to a chart_dashas row"). One row per matched in-life period (CR-109, `:147`) goes into `kala_activation` with `dasha_activation_proximity_score`, the predicate's `active_dasha_periods_jsonb` (plus an `always_on` marker when `ka_yojaka` found no discriminating lord) and a convergence cross-reference; `source_citation` carries the signal, source and period index and keys the `ON CONFLICT DO NOTHING` safety net (`:196`). The 335,403-row volume is the largest L3 table after `kala_field`. Served by `query_temporal_activation.ts:287`, the spine bundle (`compute_spine_bundle.ts`), `call_service_wrappers.ts` and the assess/judgment registry modules.

**Canonical chart: `stale`, 0 rows (cascade-shaped).** `kala_activation` has 0 canonical rows while `asset_throughput` reads `stale`, `rows_written` 335,403 (08-13 01:15); Abhinandan holds 336,093, the third chart 1,055 (I-6; 336,093 + 1,055 = 337,148 is the saved census's table-wide denominator). 1 of 3 declared dependencies lit (`ka_yojaka`, `ka_sangam` stale; `ka_sangam`'s `kala_convergence` is empty for the chart, so a build now resolves every window from the dasha timeline alone, not from convergence peaks). The predicate input exists (50,678 rows); I-6 called its signal references dead after the MSR replacement, and F-3's later measurement is narrower: 79 of the canonical chart's predicate references dangle (the 49,730 of 49,875 figure is the third chart's), because signal ids are deterministic uuid-v5 values that an unchanged signal keeps. So the writer itself is unaffected (it never reads `bodha_msr_signals`) but the served `bodha_msr_signals ⋈ kala_activation` joins (CF-24) would find fewer or no live signals. Wave 4 of the rebuild plan (v1.0 numbering, v1.1.1 keeps the order) (with `ka_vighnakara`), after `ka_sangam` and `ka_yojaka`; migration 1210 added `ka_kalasutra → ga_dashas` (the resolver reads `chart_dashas`). Not Nirmāṇa-frozen; output-digest spec present.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2306` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_kalasutra.py:23`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_activation`; count_sql tables: kala_activation | census |
| live rows / floor | 0 / 335,403 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `stale`; freshness no freshness row; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ka_yojaka`, `ka_sangam`, `bo_laksana`, `ga_dashas (migration 1210)` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 2 / transitive 22 (census blocking_radius, every layer); named (REG 2026-09-30): L3 `ka_kala_darshana`; L4 `ph_muhurta` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/lib/ahead_autofile.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`, `platform-mcp/src/tools/kala_views/now.ts`, `platform-mcp/src/tools/kala_views/promise_gate.ts`, `platform-mcp/src/tools/register_p1_aliases.ts`, `src/lib/retrieval/registry/knowledge/editorial.ts`, `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/call_service_wrappers.ts`, `registry/layers/L3_kala/query_temporal_activation.ts`, `registry/layers/register_d8_assess_domain.ts`, `registry/layers/register_d9_judgment.ts`, `registry/layers/register_spine_bundle.ts`, `src/lib/retrieval/spine/compute_spine_bundle.ts`, `src/lib/retrieval/spine/constants.ts`, `src/lib/retrieval/spine/types.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `bodha_writers/_idempotency.py`, `services/taranga_service.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts:287` reads `kala_activation`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | not frozen (not in the L3 list of NIRMANA_SUPERSESSION_RECORD §2.3) | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | empty: live=0 (count_sql over the target table; chart 482012f1) and the registry does not declare zero rows complete (target_floor=335403); build record rows_written=335403 |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | FAIL | live=0, floor=335403, delta=-335403 |
| Dens | Dens.served † | FAIL | 2 module(s): call_service_wrappers.ts, query_temporal_activation.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 32 error(s) and 12 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) ka_sangam did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 1/3 declared dependencies lit at chart 482012f1 (or global); stale: ['ka_yojaka (stale, chart 482012f1)', 'ka_sangam (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Complete.depth; Vocab.identity; Build.exercised; Ldgr.source_presence.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 7 module(s) reach it by code: L3_kala/call_service_wrappers.ts, L3_kala/query_temporal_activation.ts, register_d8_assess_domain.ts, register_d9_judgment.ts, register_spine_bundle.ts, platform-mcp/src/tools/kala_views/ahead.ts (+1 more); 4 served select(s) of its table; no referencing capability that serves it declares density_contract

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **FAIL** — 3 declared edge(s); exists: all 3 are active registry assets (every layer); cycle: ka_kalasutra is on no dependency cycle (registry-wide graph); reads-match: FAIL — missing depends_on edge: ka_kalasutra -> ga_dashas (reads chart_dashas at services/ka_temporal/date_resolver.py:348, via ka_kalasutra.py → services/ka_temporal/date_resolver.py:load_dasha_timeline; the producer is reachable transitively via bo_laksana, ka_sangam, ka_yojaka, so ordering holds b…

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_kalasutra-Build.completion | Build | real (cascade-shaped) | empty: live 0 vs floor 335,403, `rows_written` 335,403; cause I-6; clears with the chain (CF-24) |
| ka_kalasutra-Count.floor | Count | information | live 0 vs floor 335,403 |
| ka_kalasutra-Dens.served | Dens | Dens rev-1 reading | offline rev-7 FAIL (7 modules, 4 served selects, no `density_contract`) |
| ka_kalasutra-Build.history | Build | history | 32 errors, 12 aborts; latest error cascade `BLOCKED` (CF-10) |
| ka_kalasutra-Build.dep_liveness | Build | stale | 1 of 3 declared dependencies lit; chain order clears it |
| ka_kalasutra-Earn.build_record | Earn | detector | CF-05 |
| ka_kalasutra-Cost.baseline | Cost | information | CF-05 |
| ka_kalasutra-Carr.detector | Carr | detector | D2: every date traces to a `chart_dashas` row; integrity conjunct (a) is its own detector (CF-07) |
| census: Ldgr | Ldgr | information | PASS on `source_citation` populated 337,148/337,148 — table-wide and a build tag; CF-08 |
| new: kalasutra-N1 | Idem / Build | real | DELETE (`:33`) precedes the "No predicates" return (`:52`): CF-21 |
| new: kalasutra-N2 | Null / honesty | real + SS question | `dasha_activation_proximity_score` is `dignity × non_affliction` with defaults 0.5 and 1.0 and 0.5 when no peak resolves (`date_resolver.py:674`); for the five L2 satellite emitters both inputs are themselves constants (CF-27), so the score is a flat 0.5 for those signals; the 'peak' on the dasha path is the period midpoint (`date_resolver.py:559`) |
| new: kalasutra-N3 | Idem | real | which period rows exist depends on `as_of_date` defaulting to today (`date_resolver.py:418`): the primary period is not stored, but it is moved to the front of the matched list before the cut to `max_windows` (`date_resolver.py:497-500`) and the stored rows come from that list (`period_windows`, `ka_kalasutra.py:147`), so for a predicate matching more than `max_windows` periods the surviving rows and the `active_dasha_periods` listing follow the build date; the call does not pass the date (CF-28) |
| new: kalasutra-N4 | Idem | detector | `ON CONFLICT … DO NOTHING` after a chart-wide DELETE is a safety net the comment says "should never actually fire"; it would drop rows silently if it did: the build note reports `rows_actually_inserted/len(rows)` (`:210`), so the loss is visible only in notes, not in a gate |
| new: kalasutra-N5 | Build.dag | real | its declared dependents `ka_kala_darshana` and `ph_muhurta` read `kala_activation` nowhere in python (CF-23); python modules reading the table: none besides this writer (grep) |
| new: kalasutra-N6 | information | information | legacy convergence-only helpers (`_derive_dasha_periods` … `_compute_activation_end`, `:230-284`) are unreachable from `run()` and keep a second copy of the half-width table (7/14/5/5) "for backward-compat + unit tests" |
| census: Null/Narr | Null, Narr | detector | `prose_fields` null; the writer composes only machine tokens: the `always_on` marker's `reason` is the `ka_yojaka` token (`:135`) and the `source_citation` tag; proposed `[]`; CF-06 |

## 3 · Disposition

**keep (P)** — the writer's date discipline is the right one (every date from `chart_dashas`, no fabrication, birth-forward life indexing) and it is deterministic. The open items are an order defect (CF-21), a proxy-heavy score that needs a ruling (CF-27), build-date dependence (CF-28) and a phantom-edge audit (CF-23).

Approver under Track A brief §10: **Steward (G16); the output changes in CF-27 go to SS (R5)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Replace-after-candidate

- **Answers:** new kalasutra-N1; CF-21
- **Change:** read the predicates first; when there are none and activation rows exist, preserve them and report (or refuse); move the DELETE (`:33`) after the candidate `rows` list is built (`:172`)
- **Files / declaration / migration:** `ka_kalasutra.py:33-172`
- **Failing-first test and mutation:** CF-21 shape in `tests/l3/test_ka_kalasutra.py`; mutation: restore order → fails.
- **Output change:** none on a healthy rebuild
- **Blast radius:** `kala_activation` readers are serving modules, `taranga_service.py` (docstring only) and the spine bundle; the rows stop vanishing on an empty `ka_yojaka` output
- **Rebuild:** none (exercised by the next rebuild)
- **Gate it moves:** Idem / Build
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-2 · Pass the as-of date and record it

- **Answers:** new kalasutra-N3; CF-28
- **Change:** pass the pinned `as_of_date` into `resolve_activation_windows` and record it in the row-level source tag or the build note
- **Files / declaration / migration:** `ka_kalasutra.py:109`
- **Failing-first test and mutation:** CF-28 test shape: two builds, same as-of → identical; different as-of → only primary selection / predicted-date truncation differ
- **Output change:** none for a fixed as-of
- **Blast radius:** which of the matched period rows (and the `active_dasha_periods` listing) survive for predicates with more than `max_windows` matched periods
- **Rebuild:** none
- **Gate it moves:** Idem (fingerprint)
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-3 · Ratify or null the proximity inputs (CF-27)

- **Answers:** new kalasutra-N2; CF-27
- **Change:** per the CF-27 ruling: ratified approximations recorded with decision ids, or NULL where the hook value is absent so `dasha_activation_proximity_score` is NULL rather than 0.5 × 1.0, or computed from the L1 dignity/shadbala facts
- **Files / declaration / migration:** `services/ka_temporal/date_resolver.py`, `ka_yojaka.py`, the L2 emitters (outside this lane)
- **Failing-first test and mutation:** CF-27 test shape
- **Output change:** yes for options 2/3 → SS (R5)
- **Blast radius:** stored scores of every row; serving ranks by it? (not traced)
- **Rebuild:** needs production rebuild for options 2/3 (REVIEW for SS)
- **Gate it moves:** Null
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-dependent: the Null rule

### FD-4 · Declare `prose_fields: []` and drop the dead helpers

- **Answers:** census Null/Narr, new kalasutra-N6; CF-06
- **Change:** declare `[]` with `evidence.prose_fields` → `ka_kalasutra.py:135` and `ka_yojaka.py:407`; delete or quarantine the unreachable legacy helpers once their tests are re-pointed
- **Files / declaration / migration:** `asset_declarations.json`; `ka_kalasutra.py` helpers; `tests/l3/test_ka_kalasutra.py`
- **Failing-first test and mutation:** declarations validation; helper removal: the suite stays green; mutation: declare `[]` on `ka_kala_darshana` → Narr.lint flags it
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only (+ dead-code removal); **buildable before J1:** tier-independent

### Landed or in flight (not designs of this lane)

- **Migration 1210 (merged, #2810) added `ka_kalasutra → ga_dashas`** (the resolver's `chart_dashas` read, `services/ka_temporal/date_resolver.py:350`); the E6 reads-match FAIL for this asset is closed by it.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D2
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* build tag; table-wide
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 32 / 12
- **CF-21** — Replace-after-candidate: DELETE runs before the empty-upstream early return (five writers). *This asset:* FD-1
- **CF-23** — depends_on audit: declared edges the writer never reads, and the bhavishya back-read. *This asset:* two declared dependents read it nowhere in python
- **CF-24** — L2 -> L3 cascade keys and rebuild order (F-3 / migration 1214): four emptied tables and the dangling predicate set. *This asset:* emptied table; wave 4
- **CF-27** — Documented-approximation constants and favourable defaults in the L3 temporal chain (the L2 CF-20 class). *This asset:* FD-3
- **CF-28** — Rolling-horizon writers: as-of pin, calendar-safe horizon, floors that move with the build date. *This asset:* FD-2
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* table-wide `integrity_check_sql` (audit; none measured false)

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, signal_id, ayanamsha_id, source_citation)` (the writer's own unique key; `source_citation` embeds the period index, so it is part of identity, not a free text). Volatile columns excluded: `id`, `computed_at`. Depends on the as-of date (primary selection, truncated predicted dates): fingerprint at a pinned as-of. Rebuild expectation: a function of the predicate set, the dasha timeline and (for a predicate matching more than `max_windows` periods) the as-of date; with a different MSR identity set the signal-keyed rows change.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** every date traces to a `chart_dashas` row, birth-forward life indexing, one row per matched in-life period, the `always_on` disclosure for structurally undatable predicates.
- **Carriage check chosen (T4 §4.1; one only):** D2/D3: re-derive a sampled row's `activation_start/end` from `chart_dashas` for the predicate's lords and its own ayanamsha (the integrity conjunct (a) states this as its dating-authority check).
- **Opportunities (never blocking):** serve `always_on` and `no_resolvable_dasha_lord` counts so the undated share is visible; a read-time proximity that does not store a score.

## 7 · Decisions applied and open questions

No SS answer exists yet for L3 (this is the first set). The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

Open questions for Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L3-01** — CF-27: ratify, null or compute the proximity inputs?

**Track I items arising (see INDEX section 10):** TI-L3-01, TI-L3-05, TI-L3-09, TI-L3-10, TI-L3-17, TI-L3-20.
