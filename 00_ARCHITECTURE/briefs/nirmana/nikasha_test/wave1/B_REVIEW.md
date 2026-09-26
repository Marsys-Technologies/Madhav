---
artifact: NIKASHA_WAVE1_LANE_B_REVIEW
reviewer: Opus gate (fresh context, read-only, not the implementer)
reviewed_on: 2026-09-27
packet: Nikaṣa wave 1, Lane B — "the catalog names its producers" (R85 / D5 rev. 2.1)
packet_commit: 4e586118d
packet_report: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/B_REPORT.md
authority: NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md §2, §4 · DECISIONS_RECOMMENDATIONS_v2_0.md D5 rev. 2.1 · CLAUDE.md §N.7, §N.8
verdict: REJECT
---

# Lane B gate review

## §1 — Verdict

**REJECT.** The core of the packet is real work and mostly reproduces. I re-ran the derivation against
production (read-only) and the committed `producer_provenance.derived.json` is byte-identical apart from
`generated_at`. 108/182 SCUs, 74 NO_DETECTOR (28/29/16/1), 63→111 of 127 and the 16-asset outside list
all reproduce, and 12 of 12 hand-sampled derived producers are real reads in the cited handler range. The
packet touched nothing it shouldn't. But three of the gate's REJECT triggers fire, each proven below:

1. **The B-4 detector can't read false on anything the pipeline produces.** `derive_all` always writes a
   `no_detector` string, with a catch-all fallback (`catalog_provenance.py:693`). So `--check`
   returns PASS for the checklist's own constructed case: an SCU with no reviewed and no derived producer
   exits 0. `--check` also never reads the committed JSON artifact. The PASS is a green signal with no
   detector behind it (§N.8).
2. **One named test can't fail for its stated reason, and the report says it can.** If the out-of-bounds
   guard is deleted, all 9 tests stay green. Under the report's own case-2 mutation, the case-2 test
   passes, but the report's table (B_REPORT.md:366) says it **FAILS**.
3. **The report overstates or misstates several things.** It says the ruling's "15 assets" is an
   off-by-one and that the closure corroborates 14. Both are false: 15 is correct once the
   `route_evidence_only` claim is counted, and 15 seeds also give 63. It says the 16-class is
   annotation gaps or bound parameters, but 7 of the 16 are stale out-of-bounds segments with a
   misleading reason string. Several figures don't reproduce (§4).

Four derived producer rows are also **wrong**, which is worse than a NO_DETECTOR (finding 3). They don't
move the 111 headline.

**What would change the verdict to ACCEPT:** corrections C1–C6 in §3, each bound to the gate it blocks.
All of them are inside Lane B's own files, and none needs a writer, the orchestrator, the registry or a
production write. The derivation design and the closure computation are sound and do not need re-doing.

## §2 — Checklist

### Item 1 — The proof proves the claim

- **Read-only DB:** `source dbenv.sh; export PGPORT=5433; psql -Atc "SHOW default_transaction_read_only"` → `on`.
- **Population:** `count(*) filter (where is_active and not coalesce(dead_flag,false))` = **127**;
  `dead_flag IS NOT TRUE` = 127; literal `NOT dead_flag` = **0** (129 rows total). The executor's baseline
  predicate and the packet's predicate agree. The packet's three-valued-logic finding is correct.
- **Derivation re-run** (scratchpad driver calling `_run_derivation` and writing to scratch, not the repo):
  `named 108 · before 63 (14 seeds) · after 111 (95 seeds) · check failures []`. The diff against the
  committed JSON after dropping `generated_at` → `identical: True`.
- **Independent closure (SQL, not the packet's code):** a recursive CTE over `asset_registry.depends_on`
  seeded with the 14 reviewed assets gives 63 active. Outside by layer: bodha 4, brahmagyan 21, ganita 6,
  kala 9, mimamsa 15, phala 9 (= 64). **Seeding with 15 (adding `ka_kalasutra`) also gives 63.** So
  the baseline doesn't tell 14 from 15 (see finding 5).
- **Calibration:** reproduced. 5 of 12 reviewed SCUs are comparable, 3 "agree" and 2 "disagree". The
  agreement metric is superset-based (`calibration_report`), so it measures recall and never precision:
  naming every asset would "agree". This limit isn't stated.
- **`--check` (real CLI, which writes nothing):** `[B-4] --check PASS: all 182 SCUs …` exit 0.
- **Tests:** `pytest test_catalog_provenance.py` → `9 passed`.
- **Mutation tests** (on a scratchpad copy; repo untouched):

| # | mutation | result | verdict |
|---|---|---|---|
| M1 | `filter_known_relations` passthrough | 2 failed (both noise tests) | proof real |
| M2 | narrowing → `candidates[:1], False` | 1 failed (`test_shared_table_flags_every_producer`) | proof real |
| M3 | `check_completeness` returns `[]` | 1 failed (`…fails_on_a_scu_with_neither…`) | proof real |
| M4 | `resolve_segment_text` → `None` (the report's case-1/2 mutation) | 4 failed; **`test_unresolvable_range…` PASSED** | report's "case 2 FAILS" is false |
| M5 | delete the OOB guard (`:258`) | **9 passed** | case 2 can't fail for its stated reason |
| M6 | derived disposition relabelled `reviewed_output` | 1 failed (`test_resolvable…`) | proof real |
| M7 | `derive_all` leaves `no_detector=None` when no producers | **9 passed** | the derive→check pipeline is untested |

### Item 2 — Nothing untouchable was touched

- `git show --stat 4e586118d` shows 6 new files: `catalog_provenance.py`, its test, and under
  `provenance/`: `producer_provenance.derived.json`, `CLOSURE_REPORT.md`, `BUILD_DEPENDENCIES_READER_SCAN.md`,
  plus `wave1/B_REPORT.md`. No writer, orchestrator, `editorial.ts`, `compiler.ts`, migration,
  register/plan/decisions/STATE, or Lane A file.
- `git diff 9981b8f5d 4e586118d --stat` also lists `asset_census.py`, `asset_elevation_tracker.py`, two
  Lane A tests and `a2_t3_proof/asset_gaps.jsonl`. Those come from Lane A's own commits `e2819e625` and
  `432ed07da`, which sit between the base and this packet. They are not in 4e586118d. A path-filtered
  diff over `*_writers/*`, `pipeline/orchestrator/*`, `editorial.ts`, `compiler.ts` and both migration
  dirs is empty.
- The script only runs SELECTs, and the session is read-only. `build_dependencies` is not altered.
  `manifest_fingerprint.py --check` → `MATCH f484f581767ad641`.
- **Clean.**

### Item 3 — Honest tiers

- Dispositions in the JSON: `derived_from_source_query` 305, `reviewed_output` 14,
  **`derived_from_service_probe` 9**. No derived row is labelled `reviewed_output` (M6 confirms a test
  guards this).
- 77 distinct producer tables. All 77 are in `asset_registry.target_table ∪ information_schema.tables` and
  all exist physically. No noise word (`today`, `the`, `one`, `unnest`, CTE names such as `refs`) appears
  as a producer table.
- Shared tables name every producer, flagged `shared`: chart_facts ← 7 `ga_*`, bodha_msr_signals ← 7
  `bo_*`, brahma_class_priors ← 2, classical_text_chunks ← 2 (all verified against the registry).
- Narrowing fired on real data twice, and neither case is mentioned in the report:
  - `get_ayurdaya`: pin `ayurdaya` → `ga_ayurdaya`, whose NKP is `chart_facts.fact_category = ayurdaya`.
  - `firing_and_cancellation`: pin `yoga` → `bo_laksana`, whose NKP is `signal_type_class IN (yoga, …)`.
  - Both are justified by explicit declarations, not guesses. **OK.**
- **Not clean:**
  - The 9 service-probe producers carry `table: null` and an anchor (`#…`) `source_ref`, not a range.
    They sit under a third disposition that the prompt doesn't define and the report never names.
    Checklist item 3 ("every derived producer traces to a source range AND a target_table") therefore
    fails for these 9, and the report doesn't say so (C5).
  - 4 derived rows trace to writer or migration text, not to the capability's query (finding 3).

### Item 4 — The status can read false

- **Constructed case through the real pipeline** (`load_snapshot` monkeypatched to append two orphan SCUs,
  then `main(["--check"])` against the live registry). The first orphan has only a `producer_output`
  requirement and only a `route_evidence_only` claim, so no reviewed and no derived producer. The second
  has an empty contract.
  - Result: `[B-4] --check PASS: all 184 SCUs …` **exit 0**.
  - `derive_all` auto-filled `'NO_DETECTOR — no source_query requirement'` for the first orphan. That
    reason is inexact: the SCU has a `producer_output` requirement.
- **Only after bypassing `derive_all`** and stripping the reason does `--check` go
  `FAIL … scu.test.orphan_empty_contract` exit 1.
- `check_completeness` as a function can read false. The pipeline feeding it guarantees it never will,
  because every branch of `derive_all` (`:652-693`) assigns a reason, with a catch-all at `:693`.
- `--check` re-derives in memory and never reads `producer_provenance.derived.json`. A stale or
  hand-edited artifact can't fail it either.
- **Fails the item** (finding 1).

### Item 5 — Scope

- Everything is inside §4: B-1..B-4 and the lane's own files. Nothing was wired into `compiler.ts`.
- Extras:
  - The `derived_from_service_probe` disposition is new vocabulary. It is honest in substance, since
    labelling these rows `source_query` would be worse, but it needs executor acknowledgement.
  - §0 of the report registers the stale root `CLAUDECODE_BRIEF.md` pointer, correctly as a finding and
    not as a fix.
- No out-of-scope file was written. **Clean, with the one vocabulary extra noted.**

### Item 6 — Honesty of the report

- **14 vs 15 — both counts are right, for different sets.**
  - `{c['asset_id'] for x in scus for c in x['producer_output_claims']}` → **15**, because
    `ka_kalasutra` enters via `scu.kala.temporal_activation`'s claim with `disposition: route_evidence_only`.
  - Filtering to `reviewed_output` → **14**.
  - The ruling counted claims ("naming 15 assets"). The packet counted reviewed claims. The report instead
    calls the ruling "very likely a pre-existing off-by-one" (B_REPORT.md:124) and says the 63/127
    calibration "corroborates" 14 (:121). That corroboration is void: 15 seeds also give 63, because
    `ka_kalasutra` is already upstream of `ka_yojaka`/`ka_bhavishya_lekha`. **Overstated.** The packet
    also drops the `route_evidence_only` claim silently; it appears nowhere in the output.
- **74 NO_DETECTOR by class:** 28 / 29 / 16 / 1. **Reproduced.**
  - The 29-class spans **27** distinct unregistered tables, not "~20" (:194, :458).
  - **The 16-class misstates its cause for 7 of the 16.**
    - Four SCUs' only handler segment is out of bounds: `get_aspects.ts:55-91` (file has 86 lines),
      `get_avasthas.ts:71-100` (91), `get_dignity.ts:78-108` (104), `get_eclipse_flags.ts:38-62` (60).
    - Three more lose one handler segment: `get_ashtakavarga`, `get_panchanga`, `get_structural`.
    - `resolve_segment_text` returns `None` and the segment is dropped silently (`:556`). The only
      survivor is migration `204_chart_facts.sql:10-29`, a `CREATE TABLE` that the FROM/JOIN/INTO/UPDATE
      regex correctly ignores. The emitted reason, "resolved source range(s) contain no relation name"
      (`:575`), is therefore false for these SCUs. `get_dignity.ts` has `FROM chart_facts` at lines 87
      and 92, inside the intended range.
    - The other 9 are real limits of the method. Six are remedy handlers whose range holds no SQL.
      `query_cdlm_summary` uses `FROM ${table}` via a `TIER_TABLE` map, and `call_dasha_eligibility` is
      the annotation gap the report traced.
    - The report's "bound-parameter category filter" explanation fits none of the 16.
- **"125 fully resolved / 11 partial" doesn't reproduce as defined.** The report says "file exists, range
  in-bounds" (:140). 125 is the shape-valid count (137 − 12 non-range-shaped). With bounds checked it is
  **113 full / 23 partial / 1 none**. 12 SCUs carry out-of-bounds or missing numeric segments, and the
  report never mentions them. "136 with ≥1 resolving segment" **reproduces**.
- **"16 still outside": list reproduces exactly; the reason is misleading for at least 2 of the 16.**
  - `bg_prashna_rules` (no `target_table`) seeds the five `bg_prashna_*` tables. Catalog SCUs
    `query_prashna_{fructification_rules,lagna_methods,significators,special_techniques,tajik_yogas}` read
    those tables, and they sit in the 29-class.
  - `ga_prashna` (target `ga_prashna_judgment`) writes `ga_prashna_lagna`, which
    `scu.catalog.get_prashna_lagna` reads (also 29-class).
  - Both are catalog producers hidden by registry `target_table` gaps. They are reported as "no catalog
    unit names this asset", which under D5 part 3 reads as a merge/retire candidate.
- Other figures that don't reproduce, or wrong statements:
  - "14 reviewed + 94 newly derived" (:407) should be 12 reviewed SCUs + 96 derived-only SCUs = 108, or
    14 + 81 = 95 assets. The commit message's "up from 14 reviewed-only" mixes assets and SCUs; it is 12
    SCUs.
  - The `producer_output` SCU count (:98) is **11**, not 12.
  - The Phala explanation (:301) has the direction wrong: all 9 `ph_*` are direct `source_query`
    producers, and L0 service probes can't pull L4 in an upstream closure.
  - The yoga SCU's second table is `kala_activation`, not `kala_gochara_windows` (:234).
  - "Everything else in the 67 hits" (:343) should be 80.
  - The `reason_for` branch at `:785` is described as "a real possible cause … never fired" (:297). It is
    **unreachable**: any dependency of a necessary asset is itself in the closure.

### Item 7 — Regression

- Sampled 12 derived producers across L0–L5, reading the handler line that matched:
  - L0: `query_dosha_catalog`→`brahma_dosha_catalog` (`:75`), `list_entities`→`brahma_ontology` (`:138`).
  - L1: `get_vastu_directions`→`ga_vastu_planet_direction_map` (`:98`), `get_tajik`→`l1_tajik_varsha_year_lords` (`:215`).
  - L2: `query_remedies`→`bodha_rm_resonances` (`:362`), `traverse_chart_graph`→`bodha_cgm_edges` (`:557`),
    `query_quality_scorecard`→`chart_facts` (`freshness_notes.ts:85`).
  - L3: `query_kota_chakra`→`kala_kota_chakra` (`:110`), `temporal_activation`→`kala_activation_predicates` (`:388`).
  - L4: `query_remedy_program`→`phala_anchors` (`:408`), `query_prospective_ledger`→`brahma_event_ontology` (`:180`).
  - L5: `query_calibration`→`mimamsa_qa_eval` (`:186`).
  - **12/12 real reads.**
- Exhaustive trace of every (SCU, table) pair to the segment that produced it: 305 rows, 124 pairs.
  **4 pairs have no support from any handler segment, and all 4 are wrong** (finding 3).
- The closure headline doesn't move: removing them still gives 111, because `bg_dignity_reference` is
  reached via another path. The per-SCU provenance file does carry these false producers.
- Latent: `known_tables_and_producer_map` (`:220`) maps inactive assets too. `kala_gochara_windows` is
  owned by `ka_gochara` and by the inactive `ka_gochara_sweep`. It isn't hit today, but it would name an
  inactive producer.

## §3 — Findings

| # | finding | evidence | gate it blocks | correction |
|---|---|---|---|---|
| 1 | `--check` PASS is structurally guaranteed: `derive_all` always assigns a reason (catch-all `or "NO_DETECTOR — no source_query requirement"`), so the checklist's constructed orphan exits 0. `--check` never reads the committed artifact. §N.8. | `catalog_provenance.py:693`, `:973-984`, `:989-1000`; §2 item 4 run | **§6 "`--check` runs and its figures reproduce"; R85 register fold** | **C1:** `--check` validates `producer_provenance.derived.json` itself: every SCU has ≥1 producer with `table` non-null and a range `source_ref` (or a declared exemption), or a `no_detector` from a closed reason enum. Remove the catch-all fallback; an unclassified case must surface as a check failure. Add a test driving `derive_all` → `check_completeness` with an SCU whose only requirement is an unreviewed `producer_output` (it must FAIL or carry an exact reason), plus a test where the artifact is stale. |
| 2 | Case-2 test can't fail for the OOB guard (M5 green). The report's mutation table claims "FAILS" under M4 (false). | test file `:80-95` (asserts only `startswith("NO_DETECTOR")`); B_REPORT.md:366 | **§2.5 "each needs a test that fails without the change"; gate item 1** | **C2:** assert the exact reason class (e.g. `out_of_bounds`) and distinguish "segment unresolved" from "resolved, no relation". Correct B_REPORT's mutation table with actually-run results. |
| 3 | 4 false derived producers. (a) `ga_dashas`/`chart_dashas` on `scu.catalog.get_ayurdaya` and `scu.catalog.get_sensitive_degrees`: the one-hop follower matched the **definition header** `def replace_prior_chart_dashas(` on the last line of range `_idempotency.py:54-78` and read that function's body. Neither handler contains `chart_dashas`. (b) `bg_dignity_reference` on `scu.catalog.query_graha_naisargika_friendship`, from migration 606's integrity-check SQL. The handler reads `bg_graha_naisargika_friendship` (`query_graha_naisargika_friendship.ts:67`), an unregistered table, so the honest answer is a 29-class NO_DETECTOR. (c) `bg_texts`/`bg_text_index` on `scu.catalog.query_compendium_index`, from the `bg_compendium_index` writer's *input* read of `classical_text_chunks`. | `catalog_provenance.py:368`, `:434`; `_idempotency.py:74`; migration `606_…:166-179`; `bg_compendium_index.py:116-211` | **gate item 7; §4 B-1 "every producer traces to … the query"** | **C3:** the call-follower skips `def`/`function` definition sites, and the output records `via_helper` and the segment kind (handler / writer / migration). Relations found only in writer- or migration-kind segments are not producers of the SCU's read, or are flagged as a separate evidence class. Re-derive and report the delta. |
| 4 | NO_DETECTOR reason inexact for 7 of 16: stale out-of-bounds handler segments are dropped silently and reported as "resolved … no relation". 12 SCUs carry OOB or missing numeric segments, which the report doesn't disclose. "125 fully resolved" is really a shape count. | `:556`, `:575`; `get_dignity.ts` 104 lines vs ref `78-108` | **§2.6 "NO_DETECTOR — <exact reason>"** | **C4:** per-segment resolution status in the output. A reason class `source_ref_out_of_bounds` naming segment and file length. Report 113/23/1 with the definition used. List the 12 stale annotations as a registered finding for the `source_query_availability.ts` owner. |
| 5 | Report overstatements: "15 is an off-by-one" and "closure corroborates 14" (both false; 15 = all claims incl. `route_evidence_only`; 15 seeds → 63). The third disposition `derived_from_service_probe` (9 rows, `table: null`, anchor refs) isn't disclosed. The `route_evidence_only` claim is dropped silently. Non-reproducing figures: 94 (→96), producer_output 12 (→11), ~20 (→27), 67 (→80); wrong Phala explanation; wrong table name for the yoga SCU; unreachable branch called "a real possible cause". | B_REPORT.md :98, :121-126, :194, :234, :297, :301, :343, :407, :458; commit msg | **gate item 6; the executor's R85/D5 fold (which would otherwise "correct" a ruling that is right)** | **C5:** retract the off-by-one claim and state both counts with their definitions. Disclose the service-probe disposition and its missing range/table as a limit. Carry `route_evidence_only` claims as their own tier (not dropped, not seeded as reviewed). Fix every figure listed in §4. |
| 6 | Outside-closure reason is misleading for `bg_prashna_rules` and `ga_prashna`: both write tables catalog SCUs read (29-class), hidden only by registry `target_table` gaps. | `bg_prashna_rules.py:14` ("Seeds the five bg_prashna_* reference tables"); 29-class list; `CLOSURE_REPORT.md` | **D5 part 3 (outside ⇒ merge/retire candidate); the T3 §0.1 derived section (R221)** | **C6:** for each still-outside asset, cross-reference the 29-class tables its writer touches and emit reason `registry_target_table_gap` where found. Also state the closure computation (not only the population query) in CLOSURE_REPORT, per §4 B-2 "every query stated". |

Also noted, blocking nothing: the committed `BUILD_DEPENDENCIES_READER_SCAN.md` (80 hits) is already stale against the
final B_REPORT.md (a re-run gives 81; the difference is B_REPORT lines). Exclude `wave1/` from the scan, or state that
the count includes its own report. The "one live reader, `pipeline/dispatcher.py`, uncalled outside its tests"
finding **verified**: no non-test importer of `pipeline.dispatcher`, and no caller of `rebuild_asset`, `resume_build`
or `compute_descendants` outside the module.

## §4 — Fact spot-check

| # | claim (source) | result |
|---|---|---|
| 1 | active population 127; literal `NOT dead_flag` reads 0 (B_REPORT §2.2) | **VERIFIED** (127 / 127 / 0 of 129) |
| 2 | 108/182 SCUs named, 74 NO_DETECTOR (§2.6) | **VERIFIED** (byte-identical re-derivation) |
| 3 | NO_DETECTOR classes 28/29/16/1 (§2.6) | **VERIFIED** |
| 4 | baseline 63/127, 64 outside, layer split 21/4/6/9/15/9 (§3) | **VERIFIED** (independent SQL CTE) |
| 5 | after 111/127, 95 seed assets, 16 outside with the listed ids (§3) | **VERIFIED** |
| 6 | 12 SCUs with reviewed claims, 14 distinct reviewed assets (§2.4) | **VERIFIED** |
| 7 | the ruling's "15 assets" is an off-by-one, and the closure corroborates 14 (§2.4) | **WRONG**: 15 = all `producer_output_claims` (adds `ka_kalasutra`, `route_evidence_only`); 15 seeds also → 63 |
| 8 | "23 Phala/Mīmāṃsā" should be 24 (§3, finding 3) | **VERIFIED** (9 + 15 = 24; the ruling's split sums to 63) |
| 9 | 136 of 137 source_query SCUs have ≥1 resolving segment (§2.5) | **VERIFIED** |
| 10 | 125 fully resolved / 11 partial, "file exists, range in-bounds" (§2.5) | **WRONG**: 113 / 23 / 1 under the stated definition (12 SCUs have OOB/missing segments) |
| 11 | `producer_output` carried by 12 SCUs (§2.3 table) | **WRONG**: 11 SCUs (12 distinct assets) |
| 12 | "14 reviewed + 94 newly derived" = 108 (§7) | **WRONG**: 12 reviewed SCUs + 96 derived-only SCUs; assets 14 + 81 = 95 |
| 13 | ~20 queried tables with no registry owner (§2.6, finding 5) | **WRONG**: 27 distinct tables |
| 14 | the 16-class is annotation gaps / bound-parameter filters (§2.6, §7) | **WRONG** for 7/16 (stale OOB segments); bound-parameter fits none |
| 15 | case-2 test FAILS under the case-1 mutation (§5 table) | **WRONG**: passes under M4; nothing fails under M5 |
| 16 | 9 tests pass; the M1/M2/M3/M6-class mutations fail the named tests (§5) | **VERIFIED** |
| 17 | `--check` exits 0 on production (§5) | **VERIFIED**, but can't read false (finding 1) |
| 18 | `build_dependencies`' only live reader is `dispatcher.py`, not imported elsewhere (§4) | **VERIFIED** |
| 19 | 80 hits across 37 files, stable (§4) | **WRONG now**: 81 across 37 (the scan includes B_REPORT.md itself) |
| 20 | all 9 Phala assets necessary "chiefly via service_probe-derived … chains reaching L4" (§3) | **WRONG** mechanism: all 9 `ph_*` are direct `source_query` producers |
| 21 | the yoga SCU's timing route reads `kala_gochara_windows` → `ka_kalasutra` (§2.7) | **WRONG** table: `kala_activation` → `ka_kalasutra` |
| 22 | manifest fingerprint MATCH (§6) | **VERIFIED** (`f484f581767ad641`) |
| 23 | 117 of 127 active assets declare a target_table; 103 distinct (prompt §4) | **VERIFIED** |
