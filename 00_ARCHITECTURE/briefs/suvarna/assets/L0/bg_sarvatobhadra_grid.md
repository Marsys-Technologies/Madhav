---
asset_id: bg_sarvatobhadra_grid
layer: L0 Brahmagyan (bg_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L0 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L0/L0_LAYER_INSTANCE_v3_1.md (3.1-rev1, PROVISIONAL)"
base_commit: "main 0250cbade"
disposition: "qualify (Q)"
disposition_proposal_approver: "Steward (G16)"
ledger_gap_ids: [bg_sarvatobhadra_grid-G01, bg_sarvatobhadra_grid-G02, bg_sarvatobhadra_grid-O1, bg_sarvatobhadra_grid-O2, bg_sarvatobhadra_grid-Build.count_integrity, bg_sarvatobhadra_grid-Earn.build_record, bg_sarvatobhadra_grid-Cost.baseline, bg_sarvatobhadra_grid-Carr.detector, bg_sarvatobhadra_grid-Complete.depth, bg_sarvatobhadra_grid-Vocab.identity]
---
# bg_sarvatobhadra_grid — School-tagged Sarvatobhadra Chakra grid (registered deliberately empty)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

ADJUDICATION-11: a school-keyed Sarvatobhadra Chakra grid table 'registered DELIBERATELY EMPTY': the grid geometry varies by tradition and no single school has been source-verified, so an empty table honestly states that variants exist and none is endorsed (seed description). `bg_sarvatobhadra_grid` has 0 rows, `target_floor = 0`; no writer (`has_writer = false`, no `@register`); declarations kind `static`; `count_sql` present, **`integrity_check_sql` absent** (census `Build.count_integrity` PARTIAL); `asset_throughput.state = lit` with no `build_run_assets` row (never dispatched; `Build.exercised` N/A 'never run, and it has no writer'); a proven provenance receipt for the empty state exists (migration 912; layer instance Q-11). Declared dependent `ka_vedha_gochara` (census direct 1 / transitive 31), which reads the empty table and uses a disclosed approximation. Natural key `(school_tag, cell_kind, cell_index, table_version)` (vacuous on 0 rows).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | static | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:957` | seed (live may differ by migration) |
| writer / `@register` | none registered in code; registry `has_writer` = False | writers dir, census `Build.registered` |
| target table(s) | `bg_sarvatobhadra_grid`; count_sql tables: `bg_sarvatobhadra_grid` | census CEN-R |
| live rows / floor | 0 / 0 (Δ 0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 31 (every layer); named: `ka_vedha_gochara` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_sarvatobhadra_grid`: 7 non-test py/ts/tsx files reference it (7 outside brahmagyan/ and bg_*.py writers): `engine.py`, `logic.py`, `writer.py`, `definitions.ts`, `query_vedha_gochara.ts` +2 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | N/A | no writer, and the registry agrees (has_writer=false) — nothing to scan |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; no started attempt at any chart (global build record) |
| Vocab | Vocab.identity | NO_DETECTOR | NO_DETECTOR — table empty: uniqueness under (school_tag, cell_kind, cell_index, table_version) is vacuous on 0 rows |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.contract | N/A | no writer, and the registry agrees (has_writer=false) — nothing to scan |
| Build | Build.count_integrity | PARTIAL | count_sql=yes, integrity_check_sql=no |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Build | Build.exercised | N/A | never run, and it has no writer — consistent |
| Build | Build.history | N/A | never run; check 7 owns this |
| Build | Build.registered | N/A | no writer, and the registry agrees (service or static) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; no started attempt at any chart (global build record) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=0) |
| Complete (information, D3) | Complete.depth | NO_DETECTOR | NO_DETECTOR — table empty (0 rows, 10 cols): column population cannot be measured on no rows |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.completion; Build.dag †; Build.target †.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem NO_DETECTOR · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_sarvatobhadra_grid-G01 | Complete (width) | blocked (domain input absent) | the universe (28 nakshatra positions + a school’s vedha pairs) cannot be declared until a school’s passage is in hand; not designed here \| ledger: measured: 0 rows of a universe that cannot be declared until a school's passage is in hand (28 nakshatra positions + that passage's vedha pairs) / required: a declared u… |
| bg_sarvatobhadra_grid-G02 | Vocab | detector (pre-registered) | when seated, `cell_value` must carry ontology nakshatra ids and `school_tag` a school id; nothing to check today \| ledger: measured: pre-registered — when seated, cell_value must carry ontology nakshatra ids and school_tag a school id; today there is nothing to check / required: ontology-res… |
| bg_sarvatobhadra_grid-O1 | NONE | opportunity | seat the grid when a passage exists \| ledger: activates a waiting consumer with no code change and converts a disclosed approximation into a cited classical grid |
| bg_sarvatobhadra_grid-O2 | NONE | opportunity | hold two school grids \| ledger: holding two grids is not preferring either — which is what school_tag was designed for |
| bg_sarvatobhadra_grid-Build.count_integrity | Build | real (registry) | count_sql present, no integrity SQL; the abstention has no integrity claim that can fail \| ledger: measured: count_sql=yes, integrity_check_sql=no / required: the Build gate's claim |
| bg_sarvatobhadra_grid-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_sarvatobhadra_grid-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_sarvatobhadra_grid-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_sarvatobhadra_grid-Complete.depth | Complete | information | NO_DETECTOR on an empty table \| ledger: measured: NO_DETECTOR — table empty (0 rows, 10 cols): column population cannot be measured on no rows / required: the Complete gate's claim |
| bg_sarvatobhadra_grid-Vocab.identity | Vocab | detector | NO_DETECTOR on an empty table: uniqueness is vacuous \| ledger: measured: NO_DETECTOR — table empty: uniqueness under (school_tag, cell_kind, cell_index, table_version) is vacuous on 0 rows / required: the Vocab gate's claim |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |
| census: Earn / status | Earn | detector | `lit` with no run and no rows: a status with no detector (CF-05); the receipt is the only evidence |

## 3 · Disposition

**qualify (Q)** — agreed with the carried Q: retain the asset and keep the abstention explicit; it is an honest null by a native-level ruling, not an unfinished build. Seating the grid requires a school's passage that is not in hand (`bg_sarvatobhadra_grid-G01`), so no data is proposed.

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Integrity SQL for an abstaining table

- **Answers:** census `Build.count_integrity` PARTIAL; ledger `bg_sarvatobhadra_grid-Build.count_integrity`
- **Change:** add an `integrity_check_sql` that is TRUE for 0 rows and, if rows are ever seated, TRUE only when every row carries an ontology nakshatra id and a known `school_tag` (a check that can read false). It also pre-registers the Vocab gate (G02).
- **Files / declaration / migration:** a surgical migration setting `integrity_check_sql` (guarded by the old NULL) + seed literal
- **Failing-first test and mutation:** failing-first: with a seeded row carrying an unknown `school_tag` the check is FALSE; with 0 rows TRUE; mutation: drop the school test → the seeded row passes
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (registry only)
- **Gate it moves:** Build (count_integrity), Vocab (future)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-2 · Declare the abstention as a null with a reason

- **Answers:** Track A §5 (null with a reason is decided, D3); ledger `bg_sarvatobhadra_grid-G01`
- **Change:** record `ADJUDICATION-11` as the declared null reason so the Null gate reads an explained abstention and the empty table is not graded as an unbuilt asset; declare `Complete.width` universe blocked with the same reason.
- **Files / declaration / migration:** `asset_declarations.json` (null reason) — Track E file
- **Failing-first test and mutation:** declarations validation; mutation: remove the reason → Null reads NO_DETECTOR
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Null, Complete (information)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-3 · Writer/no-writer and `lit` status

- **Answers:** census `Build.exercised` N/A; layer instance §1.1 finding 5; CF-05
- **Change:** confirm that no writer is intended (static, empty by ruling) so `has_writer = false` is correct; the `lit` throughput row without a run is the §N.8 pattern and is handled by the CF-05 instrument, not by a writer.
- **Files / declaration / migration:** none for the asset
- **Failing-first test and mutation:** n/a
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Earn
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T4-03 (an empty writer-backed/static asset: how "empty by design" is declared)

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read the migration that created the table for any composed text column; declare `[]` (an empty table has no prose)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* never run: history N/A

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(school_tag, cell_kind, cell_index, table_version)`; the fingerprint of the current state is the empty set plus the declared reason. Any seated grid is fingerprinted per `school_tag`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the empty-by-ruling state with its disclosed approximation downstream; the school-keyed shape that lets variants coexist.
- **Carriage check chosen (T4 §4.1; one only):** none applies while empty (no restatement and no computation); recorded NO_DETECTOR with the reason (T4 §4.1). A D1 against the school’s passage applies once a grid is seated.
- **Opportunities (never blocking):** `bg_sarvatobhadra_grid-O1/O2` (seat the grid when a passage exists; hold two school grids).
