---
asset_id: bg_class_priors
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
ledger_gap_ids: [bg_class_priors-Idem.pattern, bg_class_priors-Earn.build_record, bg_class_priors-Cost.baseline, bg_class_priors-Dens.served, bg_class_priors-Carr.detector]
---
# bg_class_priors — Judgment and salience priors (171 rows, one partition of `brahma_class_priors`)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Seeds `brahma_class_priors` with 171 rows over five axes (17 signal_type_class, 12 source_subsystem, 6 signal_tradition, 30 varga base weights with a domain overlay, 99 graha×domain affinities) from `BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md` §2–§4 (`platform/python-sidecar/brahmagyan/l0_class_priors.py:1-12`), ON CONFLICT DO UPDATE, five-column primary key with a `'*'` sentinel on inactive axes (`:14-20`). Consumed by `mi_kula` (declared direct 1 / transitive 10). Note a stale comment: the seed row's comment says the table holds '164 signal-salience priors' (`asset_registry_seed.ts:580-583`) while the module header and live count_sql say 171 (non-blocking).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:750` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_class_priors.py:21`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `brahma_class_priors`; count_sql tables: `brahma_class_priors` | census CEN-R |
| live rows / floor | 171 / 171 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 10 (every layer); named: `mi_kula` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `brahma_class_priors`: 11 non-test py/ts/tsx files reference it (6 outside brahmagyan/ and bg_*.py writers): `mi_kula.py`, `bo_laksana.py`, `formulas.py`, `stage8_spec.py`, `stage4_field.py` +1 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_class_priors.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_class_priors.ts; declaring density_contract: 0 |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): brahma_class_priors (brahmagyan/l0_class_priors.…); Vocab.identity (declared key (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.exercised (4 executed run(s) of 4 build_run_assets row(s), scope(s): asset_set, layer, last executed 2026-09-04); Build.history; Build.registered (@register in bg_class_priors.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_class_priors-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_class_priors-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_class_priors-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_class_priors-Dens.served | Dens | real as measured at rev 1; applicability and re-measure pending | CF-04 \| ledger: measured: 1 module(s): query_class_priors.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_class_priors-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — all applicable Build/Idem/Vocab cells PASS or are detector gaps; the values are ratified judgments (`ratified_by`, `contested` columns), a different authority from the N_e baseline sharing the table (see bg_class_lifetime_counts for the consolidate question).

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr applicability for judgment seeds

- **Answers:** census Carr NO_DETECTOR; CF-07
- **Change:** no D1/D2/D3 applies to a ratified judgment seed: the rows are not a restatement of a passage nor computable a second way. T4 §4.1 says where none applies the record is NO_DETECTOR with the reason; record the reason in the asset’s declarations so the gate is not left as an unexplained NO_DETECTOR. If SS wants a measurable carriage claim, the candidate is D1 against the seed package’s tables (a file-level correspondence of the 171 literals to the package §2–§4).
- **Files / declaration / migration:** `asset_declarations.json` (reason string) — Track E file
- **Failing-first test and mutation:** declarations validation; mutation: delete the reason → gate returns to unexplained NO_DETECTOR
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration)
- **Gate it moves:** Carr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-02 (carriage assignment) and an N-22 applicability rule
- **Question for SS:** Is Carr N/A (with a decision id) for a ratified judgment seed, or does SS want the package-to-literals D1?

### FD-2 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_class_priors.py` (literal tables and `varga_weights` overlay) for any composed text column; declare `[]` with evidence if the seed stores literal values only
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-3 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in `citation` (column present and exposed in the saved reach record) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration) / needs production rebuild only if a column is added
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### FD-4 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 1 module: `query_class_priors.ts`; CF-04
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
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* Carr applicability for judgment seeds
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* `citation` column
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* shared module with bg_class_lifetime_counts

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)` (census `Vocab.identity`: 0 duplicates), excluding the `ne_v01` / `lifetime_count_per_100y` partition owned by bg_class_lifetime_counts. Volatile: `created_at`. The JSONB `varga_weights` is compared as canonical JSON.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 171 ratified priors with their `ratified_by` and `contested` flags; the sentinel encoding.
- **Carriage check chosen (T4 §4.1; one only):** none applies as D1/D2/D3 (judgment seed); the reason is recorded (T4 §4.1 'where none applies, NO_DETECTOR with the reason').
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Carr for judgment seeds: N/A with a decision id, or a package-correspondence D1?
