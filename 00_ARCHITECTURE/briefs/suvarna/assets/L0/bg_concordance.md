---
asset_id: bg_concordance
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
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
ledger_gap_ids: [bg_concordance-Idem.pattern, bg_concordance-Earn.build_record, bg_concordance-Cost.baseline, bg_concordance-Carr.detector]
---
# bg_concordance — Topic × school attribution projection (`classical_attributions`)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Builds one `classical_attributions` row per (topic_id, school) where at least one corpus chunk is tagged with the topic, schools assigned by the writer's own `TEXT_SCHOOL` map, `rule_ids` = `sutravali_rules` whose `text_id`+`verse_ref` overlap a matched chunk (`platform/python-sidecar/pipeline/orchestrator/writers/bg_concordance.py:1-20`); delete-then-insert of the whole projection (`:207`); 721 rows. **Chunk-level pointers are not carried:** `source_chunk_ids` is stored as an empty array because `classical_attributions.source_chunk_ids` is BIGINT[] while `classical_text_chunks.chunk_id` is TEXT (`:11-16`); only text-level pointers (`source_text_ids`) are. The only depth-3 asset in L0 (← bg_reference, bg_rules, bg_text_index, bg_texts); no active dependent (census 0/0). The layer instance names it the witness-carriage asset (§2.7 b).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:320` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_concordance.py:58`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `classical_attributions`; count_sql tables: `classical_attributions` | census CEN-R |
| live rows / floor | 721 / 721 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_reference`, `bg_rules`, `bg_text_index`, `bg_texts` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `classical_attributions`: 6 non-test py/ts/tsx files reference it (5 outside brahmagyan/ and bg_*.py writers): `index.ts`, `classical_attribution_lookup.ts`, `register_d7_channel.ts`, `classical_grounding.ts`, `retrieval_capability_spec.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 3007f775 complete/build (2026-09-06) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 3007f775 complete/build (2026-09-06) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (the asset's own table(s) replaced by delete-then-insert: classical_attributions (bg_concordance.py:207) — a f…); Vocab.identity (declared key (attribution_id): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (1 executed run(s) of 1 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-06); Build.history; Build.registered (@register in bg_concordance.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build PASS.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_concordance-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_concordance-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_concordance-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_concordance-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — the census has no non-detector cell for it (Build, Idem, Vocab PASS; Dens N/A). The weak point found in the writer, an empty `source_chunk_ids`, is a carriage limit not a registered gap (no detector exists for it); it is raised as a question and a design option below.

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr detector — D2 witness carriage

- **Answers:** census `Carr.detector` NO_DETECTOR; layer instance §2.7 b PARTIAL; CF-07
- **Change:** for each topic with chunks from more than one school, assert the attribution table carries one row per school (the disagreement is carried, not collapsed or dropped), and that every `rule_ids` entry resolves to a `sutravali_rules` row (the FK guard the writer cites). Counts reported; seeded case: delete one school’s row for a two-school topic → must fail.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-2 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_concordance.py` for any composed text column; declare `[]` expected (a projection of keys and pointers; confirm no composed column)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-3 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in `source_text_ids` (text-level pointers; the table has no citation column) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration) / needs production rebuild only if a column is added
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### FD-4 · Chunk-level carriage (design option, not a registered gap)

- **Answers:** writer header L11-16 (empty `source_chunk_ids`); no census cell; layer instance §2.7 b
- **Change:** a pointer to the passage level would let a reader reach the cited chunk from an attribution. It needs a schema change (`source_chunk_ids` as TEXT[] or a join table keyed by `chunk_id`) and a writer change; it is an output change. Not registered as a gap because no detector states the requirement (T4 §5: a gap with no detector is a question).
- **Files / declaration / migration:** a migration on `classical_attributions` + `bg_concordance.py`
- **Failing-first test and mutation:** a round-trip test: each attribution’s chunk pointers resolve to chunks of the same topic and school; mutation: blank the pointers → test fails
- **Output change:** `source_chunk_ids` populated; consumers of `classical_attributions` see new pointers (additive)
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** needs production rebuild of bg_concordance (full replacement, global)
- **Gate it moves:** Carr (b) and Reach
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-dependent: T2 DP02 (rule qualification / witness carriage) wording
- **Question for SS:** Does SS want chunk-level carriage on the attributions (an output change), or is text-level carriage the L0 contract?

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D2 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* no citation column; `source_text_ids`

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `attribution_id` (census: 0 duplicates); logical key `(topic_id, school)`. Whole-projection replacement: fingerprint is the ordered set of `(topic_id, school, source_text_ids, rule_ids)`; volatile: `attribution_id` if a surrogate uuid, `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the (topic, school) grouping and the `TEXT_SCHOOL` assignment of each text; the 721-row projection; the rule overlap join.
- **Carriage check chosen (T4 §4.1; one only):** D2 (witness carriage).
- **Opportunities (never blocking):** chunk-level pointers (FD-4); the `TEXT_SCHOOL` map is a local name→school map (a Vocab rule 6 candidate: `school` is an ontology class with 8 rows; derive the map from it).

## 7 · Questions for Strategic Suvarṇa

1. Chunk-level carriage on `classical_attributions`: in scope for L0 or not?
