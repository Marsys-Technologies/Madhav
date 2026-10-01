---
asset_id: ka_vighnakara
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
disposition_proposal_approver: "Steward (G16); FD-2 to FD-5 are output changes and go to SS (R5); FD-1 and FD-6 are not; several are classical-definition questions for an acharya"
decisions_applied: "SS decision-sheet rulings of 2026-10-01 (section 7; (R) items provisional until J1); L0 rulings by analogy, PROVISIONAL until the J1 review"
track_i_items: [TI-L3-01, TI-L3-02, TI-L3-05, TI-L3-10, TI-L3-11, TI-L3-12, TI-L3-15, TI-L3-16, TI-L3-17, TI-L3-19, TI-L3-20, TI-L3-23, TI-L3-26, TI-L3-27, TI-L3-28, TI-L3-29, TI-L3-30]
ledger_gap_ids: ["ka_vighnakara-Build.completion", "ka_vighnakara-Earn.build_record", "ka_vighnakara-Cost.baseline", "ka_vighnakara-Count.floor", "ka_vighnakara-Dens.served", "ka_vighnakara-Build.history", "ka_vighnakara-Build.dep_liveness", "ka_vighnakara-Carr.detector", "new: vighnakara-N1", "new: vighnakara-N2", "new: vighnakara-N3", "new: vighnakara-N4", "new: vighnakara-N5", "new: vighnakara-N6", "new: vighnakara-N7", "new: vighnakara-N8", "new: vighnakara-N9", "new: vighnakara-N10", "new: vighnakara-N11"]
---

# ka_vighnakara — Obstruction detector: five detectors evaluated at each convergence or dasha-anchored peak

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. SS ruled the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings that touch this asset are in section 7 and `INDEX.md` section 9; items marked (R) are provisional until the J1 review and anything not listed there remains open. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_vighnakara.py`.*

`ka_vighnakara.py`: for up to 500 `kala_convergence` windows (`:213`) and for dasha-anchored peaks of predicates that have no convergence window (`_dasha_anchor_peaks`, capped at `_MAX_DASHA_ANCHORS = 200`, `:40`) it runs five detectors at the peak date and stores `kala_obstruction` rows (`obstruction_type`, `severity`, `severity_score`, `override_score`, `obstruction_detail`, `source_citation`): `malefic_transit` (transiting Saturn or Rahu in a house-offset adverse sign from this chart's lagna / Moon — chart-relative since Track I-2, `:48-62`), `panchanga_obstruction` (Rikta tithi from the panchāṅga engine), `gandanta` (Moon in a junction zone), `papakartari` (natal lagna sign hemmed by transiting Saturn/Mars/Rahu in the adjacent signs) and `combustion` (transiting Mars or Saturn within a per-graha orb of the Sun, orbs from L0 `bg_combustion_orbs`). Transit positions come from swisseph (Lahiri, `FLG_SIDEREAL`) at 0h UT of the peak date; natal lagna and Moon longitudes come from L1 `chart_facts` with pinned category/subject/key and a total ORDER BY (`:403`, `:431`). The `reason` text names the planet, sign, anchors and offsets (`obstruction_detail.reason`, declared prose). Served by `query_obstruction_periods.ts:81` and `kala_temporal.ts`; read in code by `ka_kala_darshana`, `ph_muhurta`, `ph_pratikara`.

**Canonical chart: `stale`, 0 rows (cascade-shaped).** `kala_obstruction` has 0 canonical rows while `asset_throughput` reads `stale`, `rows_written` 536 (08-13 01:08); Abhinandan holds 741, the third chart 6 (I-6). 3 of 5 declared dependencies lit (`ka_sangam` — empty for the chart — and `ka_yojaka` stale). **Blocked by B-1 (rebuild plan): no output-digest spec**, so a rebuilt receipt is 'unknown' and `ka_kala_darshana`, `ka_bhavishya_lekha`, `ph_muhurta`, `ph_pratikara` are refused by DEP-ASSERT; I-4 (PR #2826, migration 1212, NOT merged at base) adds the spec (pinned to the canonical chart). Also waits on the global service `ka_muhurta_seva` (B-3). Wave 4, after `ka_sangam` and `ka_yojaka`, and only after I-2 is merged (it is) AND deployed. Migration 1210 added `ka_vighnakara → ga_dashas` (the resolver's dasha read). Not Nirmāṇa-frozen. Stored content is stale against I-2: the lagna/Moon text is the old literal until rebuilt (the canonical Aries/Aquarius chart's reasons and scores are expected to be unchanged, rebuild plan 4.2).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2343` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_vighnakara.py:178`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_obstruction`; count_sql tables: kala_obstruction | census |
| live rows / floor | 0 / 536 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `stale`; freshness no freshness row; output-digest spec ABSENT; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ka_sangam`, `ka_muhurta_seva`, `ka_yojaka`, `ga_positions`, `bg_dignity_reference`, `ga_dashas (migration 1210)` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 5 / transitive 22 (census blocking_radius, every layer); named (REG 2026-09-30): L3 `ka_bhavishya_lekha`, `ka_kala_darshana`, `ka_tulana`; L4 `ph_muhurta`, `ph_pratikara` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/tools/retrieval/kala_temporal.ts`, `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/index.ts`, `registry/layers/L3_kala/query_obstruction_periods.ts`, `registry/layers/L4_phala/salience_order.ts`, `registry/layers/register_d5_fanout.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `bodha_writers/_idempotency.py`, `brahmagyan/kala/obstruction.py`, `pipeline/orchestrator/kala_derivation_completeness_guard.py`, `pipeline/orchestrator/writers/ka_kala_darshana.py`, `pipeline/orchestrator/writers/ph_muhurta.py`, `pipeline/orchestrator/writers/ph_pratikara.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_obstruction_periods.ts:81` reads `kala_obstruction`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | not frozen (not in the L3 list of NIRMANA_SUPERSESSION_RECORD §2.3) | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | empty: live=0 (count_sql over the target table; chart 482012f1) and the registry does not declare zero rows complete (target_floor=536); build record rows_written=536 |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | FAIL | live=0, floor=536, delta=-536 |
| Dens | Dens.served † | FAIL | 1 module(s): query_obstruction_periods.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 28 error(s) and 12 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) ka_gochara, ka_sangam did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 3/5 declared dependencies lit at chart 482012f1 (or global); stale: ['ka_sangam (stale, chart 482012f1)', 'ka_yojaka (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = ["obstruction_detail.$.reason"] (the cells would be measured by a fresh census; the Null check needs the database, so none could be run offline) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Complete.depth; Vocab.identity; Build.exercised; Ldgr.source_presence.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 2 module(s) reach it by code: L3_kala/query_obstruction_periods.ts, platform-mcp/src/tools/retrieval/kala_temporal.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **FAIL** — 5 declared edge(s); exists: all 5 are active registry assets (every layer); cycle: ka_vighnakara is on no dependency cycle (registry-wide graph); reads-match: FAIL — missing depends_on edge: ka_vighnakara -> ga_dashas (reads chart_dashas at services/ka_temporal/date_resolver.py:348, via ka_vighnakara.py → services/ka_temporal/date_resolver.py:load_dasha_timeline; the producer is reachable transitively via ka_sangam, ka_yojaka, so ordering holds but the ed…

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_vighnakara-Build.completion | Build | real (cascade-shaped) | empty: live 0 vs floor 536, `rows_written` 536; cause I-6; clears with the chain (CF-24) |
| ka_vighnakara-Count.floor | Count | information | live 0 vs floor 536 |
| ka_vighnakara-Dens.served | Dens | Dens rev-1 reading | offline rev-7 FAIL (2 modules, 2 served selects, no contract) |
| ka_vighnakara-Build.history | Build | history | 28 errors, 12 aborts; latest cascade `BLOCKED` 2026-08-12 (CF-10) |
| ka_vighnakara-Build.dep_liveness | Build | stale | 3 of 5 lit; `ka_sangam`, `ka_yojaka` stale; chain order clears it |
| ka_vighnakara-Earn.build_record | Earn | detector | CF-05 |
| ka_vighnakara-Cost.baseline | Cost | information | CF-05 |
| ka_vighnakara-Carr.detector | Carr | detector | D3 for the astronomical detectors (re-derive Moon/Saturn/Rahu signs, tithi, orbs from a second ephemeris read); D2 for the restatement checks (registry integrity conjuncts (c)-(e)); CF-07 |
| census: Ldgr | Ldgr | information | PASS on `source_citation` populated 747/747 rows — table-wide (741 + 6) and a build tag (`ka_vighnakara:v2.0:conv=<id>` / `:dasha_anchor`); the per-detector classical citation is in `obstruction_detail.citation`, outside the column the gate reads; CF-08 |
| new: vighnakara-N1 | Idem / Build | real | DELETE (`:203`) precedes the "No convergence windows" return (`:220`); the comment above the DELETE protects only against a missing swisseph: CF-21 |
| new: vighnakara-N2 | Idem | real | `ORDER BY convergence_score DESC NULLS LAST LIMIT 500` has no tiebreak (`:212`): CF-22 |
| new: vighnakara-N3 | real (astrological) | real + SS/acharya question | Gandanta: `_GANDANTA_RANGES = [(90.0, 93.333), (210.0, 213.333), (330.0, 333.333)]` (`:92`) is described as the "last 3°20' of water signs" (also in the detector docstring and the stored `citation`), but sidereal 90° is 0° Cancer (Cancer 90–120°, Scorpio 210–240°, Pisces 330–360°): the windows are the FIRST 3°20' of Cancer, Scorpio and Pisces. The last 3°20' would be 116°40'–120°, 236°40'–240°, 356°40'–360°; the stored `reason` says "in Gandanta zone at end of {sign}". The only test asserts the swisseph-less stub. Every stored `gandanta` row (severity 0.55) is mis-located relative to the writer's own definition |
| new: vighnakara-N4 | real (astrological) | real + SS/acharya question | Rikta: the writer flags `tithi in (4, 9, 14, 15)` (`:722`) on the panchāṅga engine's 1..30 numbering (`panchang_engine/types.py:17`; shukla 1–15, krishna 16–30), while the engine's own classification is `[4, 9, 14, 19, 24, 29]` (`panchang_engine/rich_topics.py:36`) and the writer's docstrings say "Rikta tithi (4, 9, 14)": the three krishna Rikta tithis are missed and tithi 15 (full-moon day) is counted. The 15 comes from the day-mod proxy's "Amavasya proxy" comment, which does not apply on the engine path |
| new: vighnakara-N5 | honesty (B.10) | real | when the engine is unavailable or raises, `tithi = (peak_date.day % 15) or 15` (`:694`) — a calendar arithmetic proxy with no astronomical basis — and the stored `source` reads `'panchang_engine' if muhurta_service else 'day_mod_proxy'` (`:732`), so a proxy tithi computed after an engine exception is labelled engine-sourced; the module docstring promises "real tithi, not day-mod arithmetic" (CF-29) |
| new: vighnakara-N6 | honesty | real | each of the five detectors runs inside `except Exception: logger.debug` (`:544-584`), so a crashed detector is indistinguishable from a clean negative; an unavailable `KaMuhurtaSevaService` is a warning and the panchanga detector silently loses its engine path (CF-29) |
| new: vighnakara-N7 | Vocab / scope | real | combustion tests only transiting Mars and Saturn (`:894`) while the module docstring says "any planet within 6° of Sun (from chart_facts natal positions)" and `_COMBUSTION_ORBS_CLASSICAL` lists eight grahas; the orbs dict is a local fallback copy of L0 `bg_combustion_orbs`, and an unknown graha defaults to 8.0 (`:895`): CF-30 |
| new: vighnakara-N8 | honesty | real + SS question | Rahu is read as the TRUE node (`'Rahu': 11`, swe TRUE_NODE, `:110`) while L1 stores nodes as `RAH_MEAN`/`KET_MEAN` and the L0 index records the engine/panchang standard as MEAN_NODE (L0 INDEX section 5; SS Q5 declares `bg_ephemeris` TRUE by authority-side declaration and asks consumers that need MEAN not to read it): which node convention is the L3 transit contract? |
| new: vighnakara-N9 | real (non-canonical charts) | real | `ZoneInfo(tzid).utcoffset(datetime.now())` (`:391`) applies today's UTC offset to every peak date of a chart: harmless for IST (no DST), wrong across a decade for a zone with daylight saving; the canonical chart is unaffected |
| new: vighnakara-N10 | Null | real + SS question | severity scores 0.35 / 0.55 / 0.50 / 0.30, offset scores 0.40–0.65, `override_score = 0.45 × score` or 0.12 / 0.22 / 0.20 / 0.12, and the 0.70 / 0.40 severity cuts are literals; the detectors judge a SINGLE DATE (the peak, or a dasha midpoint for anchored rows, CF-27) although the table is read as "obstruction periods" |
| new: vighnakara-N11 | information | information | legacy second producer and native-specific constants in the L0 package: `brahmagyan/kala/obstruction.py:456` `scan_and_seed_obstructions` (BRAHMA-KA-3-3) upserts into `kala_obstruction` under an older row contract (a `date` column; types such as `adverse_dasha`), is a standalone module with its own `__main__` call (`:690`) and no importer in the repository (grep of python, TS, workflows), and `brahmagyan/kala/l3_obstruction.py` holds hand-written Sade-Sati/malefic-cluster windows for "Native Moon = Aquarius" that `brahmagyan/mimamsa/l5_event_chart_state_index.py:81` imports; not part of any registered asset and not examined further here (an inventory item for the Steward: a second path that could write the table) |
| census: Null/Narr | Null, Narr | detector | declared `obstruction_detail.$.reason`; no fidelity test measured; the I-2 test (`test_ti_i2_vighnakara_chart_relative.py`) is the seed; CF-25 |

## 3 · Disposition

**keep (P)** — the detectors read real positions and L1 facts with pinned selectors, and the I-2 fix made the adversity tables chart-relative. But this is the asset with the most substantive correctness items (Gandanta degrees, the Rikta set, a day-of-month proxy, swallowed failures), all of which are domain rulings or honesty fixes with output consequences; none argues for retiring or consolidating it (it feeds the darshana, the Phala muhūrta and pratikāra chain). The output changes go to SS (R5).

Approver under Track A brief §10: **Steward (G16); FD-2 to FD-5 are output changes and go to SS (R5); FD-1 and FD-6 are not; several are classical-definition questions for an acharya**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Replace-after-candidate and a total ORDER BY

- **Answers:** new vighnakara-N1, N2; CF-21, CF-22
- **Change:** move the DELETE below the point where `rows` is known non-empty (or refuse when obstruction rows exist and the convergence input is empty); add `peak_date, convergence_id` to the intake ORDER BY
- **Files / declaration / migration:** `ka_vighnakara.py:203-220`, `:212-213`
- **Failing-first test and mutation:** CF-21 and CF-22 test shapes on `tests/l3/test_ka_vighnakara.py`
- **Output change:** none on a healthy rebuild; the capped subset may change once on ties
- **Blast radius:** readers `ka_kala_darshana`, `ph_muhurta`, `ph_pratikara`, `query_obstruction_periods.ts`, `kala_temporal.ts`
- **Rebuild:** none (rides the planned rebuild)
- **Gate it moves:** Idem / Build
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-2 · Correct the Gandanta degrees

- **SS ruling (2026-10-01) (R):** accepted (A-1). ONE shared L0 Gandanta module read by `ka_vighnakara`; canonical width 3°20' each side; 0°48' only as a named stricter variant, never the default; each width cited or marked `unsourced`. The "acharya decides" part of the change below is superseded. TI-L3-26.
- **Answers:** new vighnakara-N3; CF-30
- **Change:** set the windows to the writer's own stated definition — the last 3°20' of Cancer, Scorpio and Pisces (116°40'–120°, 236°40'–240°, 356°40'–360°) — and have the acharya decide whether the first 3°20' of the following fire sign (Leo, Sagittarius, Aries: 120°–123°20', 240°–243°20', 0°–3°20') belongs to the same zone (the code comment says "end → start" but covers one side); correct `junction_sign` and the reason text accordingly
- **Files / declaration / migration:** `ka_vighnakara.py:92-96`, `:743`
- **Failing-first test and mutation:** Failing-first: Moon at 118.0° → gandanta; Moon at 91.0° → none; Moon at 358.0° → gandanta; mutation: restore the old ranges → fails.
- **Output change:** yes — which obstruction rows exist (gandanta rows move) → SS/acharya (R5)
- **Blast radius:** `kala_obstruction` readers as in FD-1; `kala_darshana` effective scores that used a gandanta override (0.22) and the Phala chain `ph_muhurta`/`ph_pratikara` read the rows
- **Rebuild:** needs production rebuild of `ka_vighnakara`, then `ka_kala_darshana`, `ka_bhavishya_lekha`, `ph_muhurta`, `ph_pratikara` (REVIEW for SS)
- **Gate it moves:** Carr / honesty
- **Fix class:** writer code (+ SS/acharya ruling); **buildable before J1:** tier-independent

### FD-3 · Correct the Rikta set

- **SS ruling (2026-10-01) (R):** accepted (A-2). Read the engine's Rikta set through its accessor. TI-L3-27.
- **Answers:** new vighnakara-N4; CF-30
- **Change:** read the Rikta set from the engine's own classification (`panchang_engine/rich_topics.py:36`) or use `{4, 9, 14, 19, 24, 29}` on the 1..30 numbering; drop the 15
- **Files / declaration / migration:** `ka_vighnakara.py:722`
- **Failing-first test and mutation:** Failing-first: engine tithi ids 19, 24, 29 → rikta; id 15 → none; mutation: restore the set → fails.
- **Output change:** yes — rikta rows (krishna Rikta appear, tithi-15 rows disappear) → SS/acharya (R5)
- **Blast radius:** as FD-2
- **Rebuild:** as FD-2 (one rebuild serves FD-2 to FD-4)
- **Gate it moves:** Carr / honesty
- **Fix class:** writer code (+ SS/acharya ruling); **buildable before J1:** tier-independent

### FD-4 · Remove the day-mod proxy; record detector status

- **SS ruling (2026-10-01) (R):** accepted (X1). Flag only, never score, for an absent detector until ruled otherwise; the root-found obstruction-window design is a separate design REVIEW being written. TI-L3-28.
- **Answers:** new vighnakara-N5, N6; CF-29
- **Change:** when the engine fails or is unavailable, emit no panchanga row and record `detector_status.panchanga = unavailable (reason)`; replace the blanket `except Exception` by counted failures in the build note; keep an explicit `obstruction_detail.detector_status` listing which of the five detectors ran for the peak
- **Files / declaration / migration:** `ka_vighnakara.py:690-740`, `:544-584`
- **Failing-first test and mutation:** Failing-first: with `panchang_engine` forced to raise, no `rikta_tithi` row is derived from a day of month and the status says why; mutation: restore the proxy → fails.
- **Output change:** yes — day-mod proxy rows disappear; additive `detector_status` key → SS (R5)
- **Blast radius:** as FD-2; `ka_kala_darshana` copies `obstruction_summary` and ignores unknown keys (it reads fixed keys, `ka_kala_darshana.py:53-58`)
- **Rebuild:** as FD-2
- **Gate it moves:** honesty (no census criterion)
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-independent for the record; the severity semantics of an absent detector are tier-dependent (TG-L3-019)

### FD-5 · Orbs, scope and node convention

- **SS ruling (2026-10-01) (R):** MEAN node (TRUE a named variant); docstring fixed now; orbs from L0 only; combustion scope per the L1/engine convention, honest null where the engine defines none. TI-L3-29, TI-L3-30.
- **Answers:** new vighnakara-N7, N8, N9; CF-30
- **Change:** delete `_COMBUSTION_ORBS_CLASSICAL` and the 8.0 default (raise when `bg_combustion_orbs` is empty); decide the combustion scope (transiting Mars/Saturn only, as coded, or the natal positions the docstring says) and correct the docstring or the code; state the node convention in the row's `source` (`swisseph/lahiri/true_node` or mean) per the SS answer; use the offset at the peak date, not today, for the panchāṅga location
- **Files / declaration / migration:** `ka_vighnakara.py:101`, `:895`, `:110`, `:391`
- **Failing-first test and mutation:** Failing-first: an empty orbs table raises; a fixture zone with daylight saving gets the offset of the peak date; mutation: restore each → fails.
- **Output change:** orbs/zone: none for the canonical chart; node/scope: yes if changed → SS
- **Blast radius:** as FD-2
- **Rebuild:** as FD-2 where output changes
- **Gate it moves:** Vocab / honesty
- **Fix class:** writer code (+ SS ruling for node and scope); **buildable before J1:** tier-independent for the orbs and zone; node and scope are rulings

### FD-6 · Narr golden-value tests (Gandanta, Rikta, malefic transit)

- **Answers:** census Narr; CF-25
- **Change:** fixtures for each detector's `reason` string: planet, sign, anchors, offsets, degrees, tithi number all equal what the detector read; the I-2 test already pins the chart-relative sentence
- **Files / declaration / migration:** `tests/l3/test_ka_vighnakara.py`, `test_ti_i2_vighnakara_chart_relative.py` (extend)
- **Failing-first test and mutation:** Failing-first: reproduces the "end of Cancer" sentence for 91°; mutation: change one composed token → fails.
- **Output change:** none
- **Blast radius:** none (tests)
- **Rebuild:** none
- **Gate it moves:** Narr
- **Fix class:** detector/tooling (tests); **buildable before J1:** tier-independent

### Landed or in flight (not designs of this lane)

- **I-2 (chart-relative adversity) — merged, PR #2823 (`066c58587`, the base of this lane):** the Aries/Aquarius literals and the one-native Saturn/Rahu tables are replaced by house offsets from the chart's own lagna and Moon (a missing anchor omits the clause, never defaults); stored rows keep the old text until the asset is rebuilt.
- **I-4 (digest spec) — PR #2826 / migration 1212 NOT merged at base:** unblocks `ka_kala_darshana`, `ka_bhavishya_lekha`, `ph_muhurta`, `ph_pratikara` from DEP-ASSERT once the service dependency (`ka_muhurta_seva`, 1213) has also rebuilt (limit (b)).
- Migration 1210 added `ka_vighnakara → ga_dashas` (merged, #2810).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed `depends_on` (`ka_gochara` vs live `bg_dignity_reference`, `ka_yojaka`)
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 (astronomical re-derivation) + D2
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* build tag; classical citations in `detail.citation`
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 28 / 12
- **CF-21** — Replace-after-candidate: DELETE runs before the empty-upstream early return (five writers). *This asset:* FD-1
- **CF-22** — Capped intakes without a total ORDER BY (LIMIT 750 / LIMIT 500). *This asset:* FD-1
- **CF-23** — depends_on audit: declared edges the writer never reads, and the bhavishya back-read. *This asset:* its declared dependent count falls 5 → 3 (`ka_bhavishya_lekha` and `ka_tulana` do not read it)
- **CF-24** — L2 -> L3 cascade keys and rebuild order (F-3 / migration 1214): four emptied tables and the dangling predicate set. *This asset:* emptied table; wave 4
- **CF-25** — Narr fidelity (golden-value) tests per L3 narration writer. *This asset:* FD-6
- **CF-26** — Service self-test assets: output-digest specs, source_paths and builder grants (I-4 / I-5 and the same class left open). *This asset:* I-4 spec (B-1)
- **CF-27** — Documented-approximation constants and favourable defaults in the L3 temporal chain (the L2 CF-20 class). *This asset:* N10; single-date judgments
- **CF-28** — Rolling-horizon writers: as-of pin, calendar-safe horizon, floors that move with the build date. *This asset:* dasha anchors via the resolver's as-of default
- **CF-29** — Honest absence versus unavailable: swallowed detector failures, proxy fallbacks and soft reads that degrade to empty. *This asset:* FD-4
- **CF-30** — Duplicated hand-written reference tables in L3 writers (graha -> domain, natural malefics, combustion orbs, Rikta set). *This asset:* FD-2, FD-3, FD-5
- **CF-31** — integrity_check_sql scope audit (the I-7 class: table-wide checks coupled to other charts). *This asset:* table-wide `integrity_check_sql` (audit; none measured false)

## 5 · Semantic fingerprint contract (for E5.5)

No stable natural key in the table: `id` is a BIGSERIAL, `convergence_id` is regenerated by every `ka_sangam` rebuild and NULL for dasha-anchored rows (the 1212 header). The I-4 spec hashes the output columns `signal_id, obstruction_type, severity, severity_score, override_score, obstruction_detail` ordered by all of them (a total order over the hashed projection) and excludes `id`, `computed_at`, `convergence_id`, `source_citation`; use the same projection for the semantic fingerprint (E5.5). Rebuild expectation: row set a function of the convergence set, the predicate set and the ephemeris; the canonical Aries/Aquarius chart's I-2 reasons and scores are expected equal to the pre-fix code's (rebuild plan 4.2).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** swisseph transit positions with L1 natal anchors pinned by category/subject/key, chart-relative adversity (I-2), per-chart birth location (CR-87), dasha-anchored reachability for signals without a convergence window.
- **Carriage check chosen (T4 §4.1; one only):** D3 for the astronomical detectors: re-derive the Moon/Saturn/Rahu sign, the Sun-planet separation and the tithi for a stratified sample of peaks from a second ephemeris read and compare; D2: severity from score, override restating (integrity conjuncts (c)-(e)).
- **Opportunities (never blocking):** serve obstruction windows (start/end) instead of single-date checks; Ketu and the inner planets in the transit/combustion detectors if the acharya wants them.

## 7 · Decisions applied and open questions

SS answered the L3 decision sheet on 2026-10-01 (`DECISION_SHEET_L3_v1_0.md` (PR #2838)); the rulings for this asset are in the block below. (R) = raises or defines a verdict or changes outputs: provisional until the J1 review. The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

**SS rulings (2026-10-01) for this asset:**

- **A-1 (R) — Gandanta window: accepted.** The window is a defect. ONE shared L0 Gandanta module that `ka_vighnakara` reads; canonical width 3°20' each side (one pāda: last 3°20' of Cancer/Scorpio/Pisces AND first 3°20' of Leo/Sagittarius/Aries); the 0°48' width is kept ONLY as a named stricter variant, never the default; each width is cited or marked `unsourced`. Replaces FD-2's "the acharya decides" wording. Track I: TI-L3-26.
- **A-2 (R) — Rikta set: accepted.** Read the engine set `[4, 9, 14, 19, 24, 29]` (1..30 numbering) through the engine accessor; the writer's `(4, 9, 14, 15)` is wrong (FD-3). Track I: TI-L3-27.
- **Q-L3-09 (R) — node and combustion.** MEAN node is the L3 transit contract (L1/engine convention; TRUE is a named variant); fix the docstring now. Combustion: orbs from L0 `bg_combustion_orbs` only (no local copy, no 8.0 default); scope per the L1/engine convention; where the engine defines none, emit an honest null (no invented scope). FD-5 is amended accordingly. Track I: TI-L3-29, TI-L3-30.
- **Q-L3-X1 (R) — day-of-month proxy: accepted.** Remove the proxy, emit no panchāṅga row when the engine fails, record `detector_status` (flag only, never score, until ruled otherwise). The design for root-found obstruction windows plus the fallback removal is a separate design REVIEW already being written (not specified here). Track I: TI-L3-28 (and TI-L3-16).
- **Q-L3-01 — accepted** (CF-27 split: option 1 for thresholds and weights; option 2, drop and renormalise, for stand-ins of uncomputed terms; option 3 follows the L2 CF-20 ruling). Track I: TI-L3-17.
- Citations rule (SS, all layers): an OCR text-search hit not checked against print is `sourced_ocr_unverified` (a distinct attribution state, neither `sourced` nor `unsourced`); a passage not found is `unsourced`; only a citation verified at passage level counts toward a Ldgr PASS.

Questions put to Strategic Suvarṇa (all answered 2026-10-01, see the block above; kept for the record; consolidated in `INDEX.md` section 9):

- **Q-L3-09** — FD-2/FD-3/FD-5: accept the Gandanta and Rikta corrections as written (acharya review), and which node convention is the transit contract?
- **Q-L3-01** — CF-27: severity constants and single-date judgments

**Track I items arising (see INDEX section 10):** TI-L3-01, TI-L3-02, TI-L3-05, TI-L3-10, TI-L3-11, TI-L3-12, TI-L3-15, TI-L3-16, TI-L3-17, TI-L3-19, TI-L3-20, TI-L3-23, TI-L3-26, TI-L3-27, TI-L3-28, TI-L3-29, TI-L3-30 (added by the SS rulings of 2026-10-01).
