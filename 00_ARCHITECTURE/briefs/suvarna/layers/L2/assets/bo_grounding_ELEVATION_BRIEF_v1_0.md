---
asset_id: bo_grounding
layer: L2 Bodha (bo_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L2 (briefs, dispositions, designs)
census_revision_used: "after-grant census `00_ARCHITECTURE/briefs/suvarna/layers/census/after_reader_grant/census_L2.json` (generated 2026-09-30T20:30:56+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). It differs from the first run (`census/census_L2.json`, 20:23:30) in exactly six cells (bo_anveshana, bo_sangati, bo_upaya: Build.completion and Count.floor, ERRORED then). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L2/L2_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "integrate (I)"
disposition_proposal_approver: "Strategic Suvarṇa (integrate is parked to SS, Track A §10)"
nirmana_freeze: "none (not in the frozen 22)"
decisions_applied: "SS decision N-59 (2026-10-01) on DECISION_SHEET_L2_v1_0.md (PR #2841); items marked (R) provisional until J1; section 8 lists the rulings for this asset"
track_i_items: [TI-L2-07, TI-L2-13, TI-L2-14, TI-L2-26]
ledger_gap_ids: [bo_grounding-Idem.pattern, bo_grounding-Earn.build_record, bo_grounding-Cost.baseline, bo_grounding-Build.history, bo_grounding-Carr.detector]
---
# bo_grounding — Grounding tier matches (śruti / yukti / pratyakṣa) per fired yoga and MSR signal

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Populates `bodha_grounding_matches` by running `bodha_writers/grounding_matcher.py`'s detector over two v1 target classes: fired `ga_yoga_firings` rows and `bodha_msr_signals` rows, against the classical rule corpus (`sutravali_rules`), assigning a tier by the native-ruled detector order (D-NATIVE-09: first earned tier wins, earning evidence stored per row) (`bo_grounding.py` docstring; adjudication #2258, 2026-09-07). Pure L2 derivation; it deliberately declares the narrowest sufficient ancestor set (`ga_yoga`, `bo_laksana` and the five satellites) rather than the rerank's 24-ancestor gate. `@register("bo_grounding")` at `bo_grounding.py:112`; `replace_prior_grounding_matches` (`_idempotency.py:232`) at `:162`. 50,731 chart rows (floor 0); catalog_status DRAFT (seed and live); **not in Nirmāṇa's frozen manifest** (a SUPPORTING writer, registry migration 899, schema migration 897). **No reader:** two non-test files reference the table (the writer and its test); no capability module selects it (`Reach.fields` 0/13; 0 registry dependents; no TS file mentions `grounding_tier`), although the editorial map marks it `directly_serves_output` for `scu.catalog.query_attribution` and no such consumer is built yet (declaration evidence).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2085` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_grounding.py:112`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_grounding_matches`; count_sql tables: `bodha_grounding_matches` | census CEN-R |
| live rows / floor | 50731 / 0 (chart 482012f1, count_sql scope) — no reader of the table exists in code | census `live_rows`, `Count.floor` |
| catalog_status | DRAFT | census |
| depends_on (declared, seed incl. migration 1210) | `ga_yoga`, `bo_laksana`, `bo_sudarshana`, `bo_nakshatra_semantic`, `bo_arudha`, `bo_special_lagna`, `bo_vargottama_dhana` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 0 / transitive 0; seed-derived closure (post-1210): direct 0 / transitive 0; direct dependents: none | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_grounding_matches`: 2 non-test py/ts/tsx files reference it (0 outside bodha_writers/, brahmagyan/ and bo_*.py writers) | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none by the census (`Reach.fields` 0 modules);  | census reach |
| Nirmāṇa freeze | not in Nirmāṇa's frozen 22-asset manifest (SUPPORTING writer, registry migration 899; seed comment at asset_registry_seed.ts:2078-2084) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a1a5f7d6 complete/build (2026-09-12) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_grounding_matches (bodha_writers/_idempotency.py:232 via bo_grounding.py → bodha_writers/_idempotency.py:replace_prior_grounding_matches) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served† | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 2 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-11): post-write integrity check failed: integrity_check_sql error: canceling statement due to user request |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a1a5f7d6 complete/build (2026-09-12) |
| Count (information) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=50731) |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 0/13 built column(s) (0.0%) selected by 0 capability module(s); dark: ['ayanamsha_id', 'build_id', 'chart_id', 'citation_granularity', 'computed_at', 'derivation_chain', 'engine_version', 'gr… |

Census emits **no cell** (absent, not N/A) for: Ldgr.source_presence (MF-L2-003, register R128).

**PASS cells (compact):** Vocab.identity (declared key (chart_id, ayanamsha_id, target_kind, target_id, build_id): 0 duplicate(s)); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=50731 = live=50731 (count_sql over the target table; chart 482012f1)); Build.exercised (2 executed run(s) of 4 build_run_assets row(s), scope(s): asset, last executed 2026-09-12); Build.dep_liveness; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **NO_DETECTOR** — no module in the serving roots references bodha_grounding_matches, but it is named outside the scanned serving roots where a served select cannot be ruled out (R51): platform/src/lib/nirmana-elevation/definitions.ts (a comment names it), platform/src/lib/nirmana-elevation/monitor.ts (a; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PASS (not in the recompute's L2 gate-diff list; no change from the saved rev-1 PASS) The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| census: Reach.fields (0 modules), blocking radius 0/0; declaration `served_surface: null` | Dens / Reach | real (not integrated) | 50,731 rows with no consumer: no capability, no registry dependent and no TS reference to its columns. The registry description and the editorial map say it is meant to be consumed (the grounding spine `resolver.ts`, `scu.catalog.query_attribution`); prior-campaign item N-18 (extend the resolver to carry the grounding fields) is not on main. The layer instance records its individual contribution as ≈ 0 without implying a disposition (§1.2). FD-1. |
| census: catalog_status DRAFT; `bo_grounding-Idem.pattern` (ledger, stale) | Build | information | the asset is the only DRAFT in the layer (the seed marks eight assets DRAFT, the live registry reads CURRENT for the other seven). The ledger Idem row is from 2026-09-27; saved census PASS and offline rev-2 PASS. CF-03 (catalog_status truth after the disposition). |
| census: no `Ldgr.source_presence` cell (MF-L2-003) | Ldgr | detector | the table stores `matched_rule_id`, `grounding_tier`, `citation_granularity` and `grounding_evidence_jsonb`; the carrying column is `matched_rule_id`/`derivation_chain`, not a recognised citation column. Declare it. CF-08. |
| declarations `prose_fields: null` (undeclared) | Null, Narr | detector (declaration) | the writer binds ids, a tier code and an evidence jsonb built by `grounding_matcher.py`; no composed sentence appears in `bo_grounding.py`; proposal: declare `[]` after reading `grounding_matcher.py`'s evidence builders for text. CF-06. |
| `bo_grounding-Build.history` | Build (history) | history | latest run complete; 2 errors and 1 abort on record (latest error 2026-09-11, `post-write integrity check failed: integrity_check_sql error: canceling statement due to user request`, i.e. the integrity SQL was cancelled on a 50,731-row table; the latest run completed). CF-10; the integrity SQL's cost on this table is worth a look when the asset is next built. |
| `bo_grounding-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |
| prior-campaign item L-02 (L2_W2_DECIDE, adjudication #1726) | Carr | real-or-SS-question | the `sruti` tier "as literally defined" was HELD because the corpus has page/column addressing, not verses ("under no circumstances is `chapter` emitted as a chapter"); the stored `citation_granularity` carries that distinction. Whether the held ruling is still open is not established here. |

## 3 · Disposition

**integrate (I)** — a deterministic, idempotent, fully built asset (50,731 rows) that nothing reads: the work left is connection, not content. Integration means choosing the consumers (the grounding spine in the resolver, the attribution catalogue) and promoting the catalog status after that. Retiring it would discard a native-ruled design (D-NATIVE-09); keeping it unconnected leaves the layer's grounding claim unserved.

Approver under Track A brief §10: **Strategic Suvarṇa (integrate is parked to SS, Track A §10)**.

**SS ruling (N-59, 2026-10-01): the proposed `integrate (I)` is NOT applied now.** `bo_grounding` stays a declared substrate (outside the denominator per D-NATIVE-11, no consumer, reason stated in the declaration); integration is a post-J1 item (Q-L2-08; TI-L2-07, TI-L2-26).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Connect the grounding tier to a consumer, then promote the status

- **Answers:** the not-integrated gap; prior-campaign N-18
- **Change:** extend the grounding spine (`resolver.ts` SELECT and `GroundedSignal`) to carry `grounding_tier`, `citation_granularity` and `grounding_evidence_jsonb` for the signals it already returns (≤ 1 hop to the grounding tier), with the rule that an empty citation on a `pratyaksa` row is not a defect; add a capability or facet that serves the matches with a `density_contract` (confirmed rows layered apart from catalogue-only ones, CLAUDE.md §N.6); then set `catalog_status` to CURRENT
- **Files / declaration / migration:** `platform/src/lib/retrieval/**/resolver.ts` (grounding spine), a new `L2_bodha/query_grounding.ts` or a facet on `query_signals.ts`, registry `catalog_status` via CF-03
- **Failing-first test and mutation:** a grounded signal in the spine carries its tier and granularity; an empty-citation `pratyaksa` row is not flagged; mutation: drop the field from the SELECT → the spine test fails
- **Output change:** yes (new served fields): SS (R5)
- **Blast radius:** output change: this asset's registry dependents see new values after the rebuild (direct 0: none; transitive 0)
- **Rebuild:** none for the table; the registry status edit stales no manifest (the asset is not frozen)
- **Gate it moves:** Dens, Reach (and Earn once consumed)
- **Fix class:** served surface (TS) + registry; **buildable before J1:** tier-dependent: how `grounding_tier` relates to the epistemic tiers (TGH row for the grounding doctrine) and TGH-T3-26
- **Question for SS:** Integrate (which consumers first), or is the table to stay an internal substrate until a consumer is designed (then `unresolved`)?

### FD-2 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D1 (source correspondence): for each matched row, resolve `matched_rule_id` to `sutravali_rules` and the cited text chunk and test that the antecedent terms the matcher claims are present; report matched/unmatched/unresolvable counts (PASS only on the matched subset).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 0: none; transitive 0); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-08** — Ldgr: assets with no recognised citation column (no census cell). *This asset:* no Ldgr reading
- **CF-06** — prose_fields declarations for the L2 assets that have none (Null and Narr gates). *This asset:* declare `[]` after reading the matcher
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* catalog_status after integration
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D1 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, target_kind, target_id)` (registry partition; the live table also carries `matched_rule_id` in its unique constraint). Fingerprint: `target_kind`, `target_id` resolved to the target's natural key (a firing or a signal), `matched_rule_id`, `grounding_tier`, `citation_granularity`, `grounding_evidence_jsonb`, `derivation_chain`. **Volatile:** `match_id`, `build_id`, `computed_at`, `engine_version`. Expected 50,731 rows on the chart (53 firings beyond the 50,678 signals is an inference, not measured).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the deterministic detector order with stored earning evidence per row, and the refusal to emit `chapter` as a chapter.
- **Carriage check chosen (T4 §4.1; one only):** D1 (source correspondence) (design in FD-2)
- **Opportunities (never blocking):** surface the tier to readers (the product of the asset); `sruti` once #1726 is ruled.

## 7 · Rebuild and frozen-manifest consequences

Not in Nirmāṇa's frozen manifest, so no manifest staleness. **A production rebuild (SS REVIEW):** its direct dependents (none) re-run after it in DAG order; seed-derived transitive closure 0 assets. No dependents, so a rebuild is local; it reads the MSR table and `ga_yoga_firings`, so it follows the MSR producers.

## 8 · Questions for Strategic Suvarṇa

1. Integrate (connect to the grounding spine and the attribution catalogue), keep as a substrate (then `unresolved` until a consumer exists), or retire (would discard D-NATIVE-09)?
2. Is adjudication #1726 (the `sruti` tier definition) still open?

**SS rulings (N-59, 2026-10-01; decision sheet `DECISION_SHEET_L2_v1_0.md` (PR #2841); (R) = provisional until the J1 review). The questions above are kept for the record.**

- **Q-L2-08 - changed.** `bo_grounding` stays a declared SUBSTRATE for now: outside the denominator per D-NATIVE-11, no consumer, reason stated in the declaration; no retire; no new served surface before J1; integration is a post-J1 item. Adjudication #1726 is not ours to close: recorded 'satisfied in practice'. The proposed disposition 'integrate (I)' is therefore deferred, not applied. TI-L2-07, TI-L2-26.
- **Layer-wide (Q-L2-18, Q-L2-19, sequencing).** Build.history counts only runs since the last writer or registry change (L0 Q11 carried; TI-L2-13) and Carr uses a D3 stratified sample with the section N.5 resolver, PASS only if every sampled row re-derives (L0 Q13 grading; TI-L2-14); both are read after the one coherent L2 rebuild on main's code, in which no asset is rebuilt twice.
