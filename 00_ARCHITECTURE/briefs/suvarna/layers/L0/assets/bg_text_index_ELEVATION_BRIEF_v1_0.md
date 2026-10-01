---
asset_id: bg_text_index
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
disposition: "integrate (I)"
disposition_proposal_approver: "Strategic Suvarṇa"
ledger_gap_ids: [bg_text_index-Idem.pattern, bg_text_index-Build.completion, bg_text_index-Earn.build_record, bg_text_index-Cost.baseline, bg_text_index-Complete.depth, bg_text_index-Dens.served, bg_text_index-Carr.detector]
---
# bg_text_index — Topic-tag index over the corpus (a measurement asset on `classical_text_chunks`)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

'Measurement of retrieval index health — distinct topic tags across embedded + indexed chunks'. The writer UPDATEs `classical_text_chunks.topic_tag` with a deterministic keyword/regex classifier against the `reference_topic_tags` vocabulary and reports the cockpit metric `count(DISTINCT topic_tag)` over embedded chunks: 361 (`platform/python-sidecar/pipeline/orchestrator/writers/bg_text_index.py:1-22,500-558`). It reconciles every embedded chunk: a chunk whose classification is now absent has its tag cleared (the `desired_tag = None` path at `:513-531`), so a rebuild does re-derive all rows (the saved Idem.pattern PARTIAL says this 'is not measured'). The asset shares its table with `bg_texts` (10,651 rows) but counts a different unit (distinct tags), so `rows_written` (rows changed) and live (distinct tags) cannot agree. The writer docstring states a target of ≥ 400 distinct tags (`:8`); the registry floor and live are 361. Depends on `bg_reference` and `bg_texts`; declared dependent `bg_concordance` (census 1 / 1). `Complete.depth`: `content_summary` and `cleaned_translation_text` never populated (shared with bg_texts).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:262` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_text_index.py:447`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `classical_text_chunks`; count_sql tables: `classical_text_chunks` | census CEN-R |
| live rows / floor | 361 / 361 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_reference`, `bg_texts` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 1 (every layer); named: `bg_concordance` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `classical_text_chunks`: 40 non-test py/ts/tsx files reference it (13 outside brahmagyan/ and bg_*.py writers): `bo_laksana.py`, `favourable_houses.py`, `w29_citation_resolution.py`, `logic.py`, `route.ts` +8 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_classical_texts.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PARTIAL | the asset's own table(s) are only UPDATEd in place: classical_text_chunks (bg_text_index.py:546) — no row is added, but whether a rebuild re-derives every row is not measured [resolved scope: bg_text_index.py] |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 237b88a3 complete/skip_no_delta (2026-09-06) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 2 module(s): query_classical_texts.ts, query_compendium_index.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record says rows_written=0 against live=361 (global) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 237b88a3 complete/skip_no_delta (2026-09-06) |
| Complete (information, D3) | Complete.depth | PARTIAL | 10651 rows, 26 cols; fully populated 16; NEVER populated ['content_summary', 'cleaned_translation_text'] |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 10651/10651 rows); Vocab.identity (declared key (chunk_id): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (3 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-06); Build.history; Build.registered (@register in bg_text_index.py; registry agrees); Build.target †; Count.floor.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PARTIAL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_text_index-Idem.pattern | Idem | detector (PARTIAL: update-only reading) | saved Idem.pattern PARTIAL: "no row is added, but whether a rebuild re-derives every row is not measured"; the code shows a full reconcile (`:513-531`), so the claim is provable by a test \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_text_index-Build.completion | Build | real (T4 check 6) with a unit mismatch | rows_written 0 (rows changed) vs live 361 (distinct tags): two different units for one asset; CF-01 and the grain declaration \| ledger: measured: build record says rows_written=0 against live=361 / required: the Build gate's claim |
| bg_text_index-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_text_index-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_text_index-Complete.depth | Complete | information | columns never populated (D3: information, not a blocker) \| ledger: measured: 10651 rows, 26 cols; fully populated 16; NEVER populated ['content_summary', 'cleaned_translation_text'] / required: the Complete gate's claim |
| bg_text_index-Dens.served | Dens | real as measured at rev 1; applicability and re-measure pending | CF-04 \| ledger: measured: 2 module(s): query_classical_texts.ts, query_compendium_index.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_text_index-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**integrate (I)** — the carried I stands in a narrower form: the asset is a projection on `bg_texts`'s table with a different grain and unit, so the repair is to declare that grain once (one table, two assets, two stated units), not to change data. Integrate routes to SS (Track A §10).

Approver under Track A brief §10: **Strategic Suvarṇa**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare the grain and unit once

- **Answers:** layer instance §1.1 finding 3 (two units over one table); census `Build.completion` FAIL; TG-L0-010
- **Change:** declare that `bg_text_index` measures distinct `topic_tag` over embedded chunks of `classical_text_chunks` (count unit = tags) while `bg_texts` counts chunk rows; its `rows_written` is rows reclassified. With that declared the cell is a CF-01 convention case rather than a unit conflict.
- **Files / declaration / migration:** `asset_declarations.json` (grain/unit note) + the registry `english_description` is already accurate; no registry column change
- **Failing-first test and mutation:** declarations validation; the CF-01 rule reads PASS only when the unit is declared
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Build (completion)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T2-05 (one table, several producers/units)
- **Question for SS:** Keep `bg_text_index` as a separate asset with its own unit (declared), or fold the metric into bg_texts (integrate)?

### FD-2 · Prove the reconcile (Idem)

- **Answers:** saved Idem.pattern PARTIAL; CF-12
- **Change:** a rebuild-twice test: run the classifier, change a chunk’s text so its tag disappears, rerun, assert the tag is cleared and every other chunk’s tag is unchanged; the Idem detector can then read PASS on evidence instead of "not measured".
- **Files / declaration / migration:** a test next to the writer; the writer is unchanged
- **Failing-first test and mutation:** failing-first: today the claim has no test; mutation: skip the `None` branch → the clearing assertion fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Idem
- **Fix class:** writer code (test only); **buildable before J1:** tier-dependent: TGH-T3-18

### FD-3 · Carr detector — D1 referential

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** every non-null `topic_tag` is in `reference_topic_tags` (the writer already skips an invalid tag at `:518-524`); count violations; the classifier’s keyword rules are deterministic, so a seeded chunk with a known keyword must receive its tag.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_text_index.py` for any composed text column; declare `[]` (tags are vocabulary ids)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 2 modules: `query_classical_texts.ts`, `query_compendium_index.ts` (shared with bg_texts); CF-04
- **Change:** per CF-04: declare `density_contract` where the module paginates or facets, after the applicability ruling
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: TGH-T3-26 + N-22 applicability
- **Question for SS:** Does Dens apply to this reference table at all (it carries no verification tier)?

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-01** — Build.completion for converged reruns (rows_written = changed rows, not rows present). *This asset:* rows changed vs distinct tags (unit mismatch)
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* referential D1
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* no citation column of its own
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* shared modules

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `chunk_id` (census, 0 duplicates). Fingerprint = the `chunk_id → topic_tag` map over embedded chunks; the cockpit metric (361) is derived from it. Volatile: none (the asset only writes `topic_tag`); it must not touch `content_en` or embeddings.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the deterministic classifier and the `reference_topic_tags` vocabulary; the rule that only `topic_tag` is written.
- **Carriage check chosen (T4 §4.1; one only):** D1 (referential: tags resolve to the vocabulary).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Keep as a distinct asset with a declared unit, or integrate with bg_texts (the carried I)?
