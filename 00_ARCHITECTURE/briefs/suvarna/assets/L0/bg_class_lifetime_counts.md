---
asset_id: bg_class_lifetime_counts
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
ledger_gap_ids: [bg_class_lifetime_counts-Idem.pattern, bg_class_lifetime_counts-Earn.build_record, bg_class_lifetime_counts-Cost.baseline, bg_class_lifetime_counts-Dens.served, bg_class_lifetime_counts-Carr.detector, bg_class_lifetime_counts-Build.history]
---
# bg_class_lifetime_counts — N_e expected lifetime counts per event class (one partition of `brahma_class_priors`)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

L0 global seed of N_e, the expected lifetime count of each `brahma_event_ontology` event class over a 100-year modelled timeline: the chart-independent structural baseline of the Kāla Kṣetra hazard field (`platform/python-sidecar/brahmagyan/l0_class_lifetime_counts.py:1-9`; ruling ADJUDICATION-2 item 2). Its own rule limits what may be a source: only a published demographic/actuarial statistic carrying six source fields (tier N-i) or a stated arithmetic identity from one (tier N-ii); 'a reasonable proportion of' is forbidden (`:13-26`). The asset owns a **partition** of a table it shares with `bg_class_priors`: `WHERE prior_version='ne_v01' AND fact_kind='lifetime_count_per_100y'` (seed `asset_registry_seed.ts:580-608`), 6 rows. Writer `bg_class_lifetime_counts.py` delegates to `seed_class_lifetime_counts` (ON CONFLICT upsert, `l0_class_lifetime_counts.py:721`); the module is APPEND-ONLY by its own header.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:587` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_class_lifetime_counts.py:44`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `brahma_class_priors`; count_sql tables: `brahma_class_priors` | census CEN-R |
| live rows / floor | 6 / 6 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_ghatana` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 3 (every layer) (named 0 of 1 direct; the rest not identified offline) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `brahma_class_priors`: 11 non-test py/ts/tsx files reference it (6 outside brahmagyan/ and bg_*.py writers): `mi_kula.py`, `bo_laksana.py`, `formulas.py`, `stage8_spec.py`, `stage4_field.py` +1 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_class_priors.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 21df3b6a complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_class_priors.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 21df3b6a complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): brahma_class_priors (brahmagyan/l0_class_lifetim…); Vocab.identity (declared key (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (2 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.registered (@register in bg_class_lifetime_counts.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_class_lifetime_counts-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_class_lifetime_counts-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_class_lifetime_counts-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_class_lifetime_counts-Dens.served | Dens | real as measured at rev 1; applicability and re-measure pending | CF-04 \| ledger: measured: 1 module(s): query_class_priors.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_class_lifetime_counts-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_class_lifetime_counts-Build.history | Build | history | CF-10: a record of past errors/aborts; the latest run completed \| ledger: measured: latest run complete, but 0 error(s) and 1 abort(s) on record. / required: the Build gate's claim |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — the census shows no real blocking gap beyond detectors and the Dens applicability question. The layer instance carried **C** (consolidate with `bg_class_priors`: one table, two partitions). The sources read here do not show shared authority: this partition is governed by ADJUDICATION-2 source tiers, `bg_class_priors` by the judgment seed package (`l0_class_priors.py:10`), and the count_sql already scopes each asset to its own rows (seed L580-608). T2 §10.1 C requires tracing callers and semantics before a successor is chosen; nothing found justifies one (smallest sufficient change).

Approver under Track A brief §10: **Steward (G16)**. The divergence from the carried C is a proposal flagged to SS in §7 (a consolidation would be an SS decision under Track A §10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr detector — D1/D3 on the tier N-i / N-ii rows

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** for each row, check that a tier N-i row carries all six source fields the module requires and that each tier N-ii row’s stated arithmetic identity re-computes from the N-i row it names; report matched/unmatched. The columns to read are confirmed at design time (the saved census records populated `citation`, `ratified_by`, `prior_version` and never-read `prior_basis`, `source_ref`).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-2 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_class_lifetime_counts.py` (the seed list and its INSERT) for any composed text column; declare `[]` with evidence if the seed stores literal values only (expected: numeric counts plus a stored identity string), otherwise the composed column
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-3 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in `citation` / `source_ref` (columns present in the saved reach record) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration) / needs production rebuild only if a column is added
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### FD-4 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 1 module: `query_class_priors.ts` (shared with bg_class_priors); CF-04
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
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1/D3 as above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* source columns `citation` / `source_ref`
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* shares `query_class_priors.ts` with bg_class_priors
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 1 abort on record, latest run complete
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* upsert, no DELETE found; the module is APPEND-ONLY by its own header, so the answer is a declaration, not a prune

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)` (census `Vocab.identity`: 0 duplicates), scoped to `prior_version='ne_v01' AND fact_kind='lifetime_count_per_100y'`. Volatile columns excluded: `created_at` (populated-column list in the saved reach record); no embedding column. A rebuild must leave the six partition rows unchanged.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the six N-i/N-ii lifetime-count rows with their stated sources and arithmetic; the tier rule that forbids a judged value; the append-only discipline.
- **Carriage check chosen (T4 §4.1; one only):** D1 (source correspondence to the published statistic) with D3 on the N-ii arithmetic identities; one detector, one table.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Keep both `bg_class_priors` and `bg_class_lifetime_counts` as separate assets (this brief) or hold the carried C open until the caller trace names a successor?
