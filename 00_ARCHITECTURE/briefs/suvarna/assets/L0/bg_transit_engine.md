---
asset_id: bg_transit_engine
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
ledger_gap_ids: [bg_transit_engine-Build.registered, bg_transit_engine-Idem.pattern, bg_transit_engine-Earn.build_record, bg_transit_engine-Cost.baseline, bg_transit_engine-Dens.served, bg_transit_engine-Carr.detector]
---
# bg_transit_engine — Transit engine parameters (9 rows; rider on the transit writer)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

'L0 average graha motion parameters — daily motion, zodiac period, sign residence. Source: BPHS Ch.22'; 9 rows, `classical_citation` 9/9. A sub-table seeded by the same writer as `bg_transit_rules`: `@register('bg_transit_engine')` is the second decorator on `BgTransitRulesWriter` (`platform/python-sidecar/pipeline/orchestrator/writers/bg_transit_rules.py:11-12`; ON CONFLICT upsert at `brahmagyan/l0_transit.py:913`). **The registry says `has_writer = false` while code registers it** (census `Build.registered` FAIL; layer instance C-12); declarations mark it `kind: rider`; never dispatched (no `build_run_assets` row), `asset_throughput` `lit`. No declared dependents; read by `query_transit_engine.ts`.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | rider | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:660` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_transit_rules.py:12`; registry `has_writer` = False | writers dir, census `Build.registered` |
| target table(s) | `bg_transit_engine`; count_sql tables: `bg_transit_engine` | census CEN-R |
| live rows / floor | 9 / 9 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_transit_engine`: 9 non-test py/ts/tsx files reference it (6 outside brahmagyan/ and bg_*.py writers): `runner.py`, `citations.py`, `throughputError.ts`, `definitions.ts`, `producer_editorial_review.ts` +1 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_transit_engine.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; no started attempt at any chart (global build record) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_transit_engine.ts; declaring density_contract: 0 |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Build | Build.exercised | N/A | never run, and it has no writer — consistent |
| Build | Build.history | N/A | never run; check 7 owns this |
| Build | Build.registered | FAIL | @register in bg_transit_rules.py but registry says has_writer=false |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; no started attempt at any chart (global build record) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (classical_citation populated on 9/9 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_transit_engine (brahmagyan/l0_transit.py:913 …); Vocab.identity (declared key (graha): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_transit_engine-Build.registered | Build | real (registry) | `@register` in code but registry `has_writer = false`; CF-03 \| ledger: measured: @register in bg_transit_rules.py but registry says has_writer=false / required: the Build gate's claim |
| bg_transit_engine-Idem.pattern | Idem | stale | saved census Idem.pattern reads PASS (upsert at `l0_transit.py:913`) \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_transit_engine-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_transit_engine-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_transit_engine-Dens.served | Dens | real as measured at rev 1; applicability and re-measure pending | CF-04 \| ledger: measured: 1 module(s): query_transit_engine.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_transit_engine-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — complete and cited; the findings are the registry/status contradictions (CF-03) and the rider question (CF-02).

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Registry: `has_writer` false → true

- **Answers:** census `Build.registered` FAIL; ledger `bg_transit_engine-Build.registered`; layer instance C-12; CF-03
- **Change:** set `has_writer = true` in the same surgical migration as `bg_nakshatra_medical` (guarded by the old value) and the seed literal. Expected cascade (Nikaṣa R61): `Build.exercised` FAIL until the id is dispatched.
- **Files / declaration / migration:** migration (max+1 across all heads and both directories at execution time) + `asset_registry_seed.ts`
- **Failing-first test and mutation:** failing-first: `Build.registered` PASS after the migration; `Build.exercised` FAIL recorded as the cascade; mutation: revert → FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none for the flip; clearing the cascade needs a dispatch (production run): REVIEW item for SS
- **Gate it moves:** Build (registered)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent
- **Question for SS:** Cascade accepted until first dispatch?

### FD-2 · Rider dispatch

- **Answers:** census `Build.exercised` (never run); CF-02
- **Change:** decide whether the sibling `bg_transit_rules` dispatch exercises this id (T4 `producer_covered`) or dispatch it through the same writer.
- **Files / declaration / migration:** a ruling or the L0 run
- **Failing-first test and mutation:** one L0 run records both ids
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** needs production dispatch (REVIEW item)
- **Gate it moves:** Build (exercised)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T4-01
- **Question for SS:** Does the sibling’s dispatch count for a rider?

### FD-3 · Carr detector — D1 on the 9 rows

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** resolve `classical_citation` (BPHS Ch.22) to the corpus and test the daily-motion/period anchor terms; compare the stored mean motions to the ephemeris-implied mean motion (a D3 flavour: mean daily motion from `ephemeris_daily` over a long span) within a declared tolerance.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_transit.py` for any composed text column; declare `[]` expected (literal parameters)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 1 module: `query_transit_engine.ts`; CF-04
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
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* has_writer flip and its cascade
- **CF-02** — Producer attribution: rider ids, multi-table writers and multi-producer tables. *This asset:* rider id
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 + mean-motion D3
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* 1 module

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `graha` (census, 0 duplicates). Upsert; volatile: `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the nine average-motion parameter rows and their citation.
- **Carriage check chosen (T4 §4.1; one only):** D1 (corpus) with a D3 on mean motion from the ephemeris.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Has_writer flip: cascade accepted until first dispatch?
