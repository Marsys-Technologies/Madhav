---
asset_id: bg_medical_mappings
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
ledger_gap_ids: [bg_medical_mappings-Idem.pattern, bg_medical_mappings-Earn.build_record, bg_medical_mappings-Cost.baseline, bg_medical_mappings-Dens.served, bg_medical_mappings-Carr.detector, bg_medical_mappings-Build.completion]
---
# bg_medical_mappings — Medical graha mappings (21 rows; rides the shared medical writer)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Registry description: 'Classical Ayurvedic Jyotish mappings per BPHS Ch.18, Ashtanga Hridayam and Charaka Samhita: 9 grahas, 6 planetary combinations and 6 dignity modifiers. L0 static reference'; 21 rows, flagged `not_diagnosis = TRUE` (`platform/python-sidecar/pipeline/orchestrator/writers/bg_medical_mappings.py:1-14`). One writer class registers three ids (`bg_sign_medical`, `bg_nakshatra_medical`, `bg_medical_mappings`, `:25-27`) and returns the sum of all three seeds (`:49`): 60 = 21 + 27 + 12, which is the recorded `rows_written` against 21 for this asset's own count_sql. ON CONFLICT upsert (`brahmagyan/l0_medical.py:421`). The writer docstring still says '9 graha rows' while live is 21 (stale text). No declared dependents; read by `query_medical_mappings.ts`.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:696` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_medical_mappings.py:27`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_medical_mappings`; count_sql tables: `bg_medical_mappings` | census CEN-R |
| live rows / floor | 21 / 21 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_medical_mappings`: 9 non-test py/ts/tsx files reference it (6 outside brahmagyan/ and bg_*.py writers): `runner.py`, `ga_medical_writer.py`, `definitions.ts`, `get_medical_indications.ts`, `producer_editorial_review.ts` +1 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_medical_mappings.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_medical_mappings.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record rows_written=60 disagrees with live=21 (count_sql over the target table; global) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (classical_citation populated on 21/21 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_medical_mappings (brahmagyan/l0_medical.py:42…); Vocab.identity (declared key (graha): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.exercised (3 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_medical_mappings.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_medical_mappings-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_medical_mappings-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_medical_mappings-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_medical_mappings-Dens.served | Dens | real as measured at rev 1; applicability and re-measure pending | CF-04 \| ledger: measured: 1 module(s): query_medical_mappings.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_medical_mappings-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_medical_mappings-Build.completion | Build | real (T4 §4.2 check 6) | see the fix design \| ledger: measured: build record rows_written=60 disagrees with live=21 (count_sql over the target table; global) / required: the Build gate's claim |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — census Idem/Vocab/Ldgr PASS; the one FAIL is a build-record attribution artefact of the shared writer (CF-02), not a data defect.

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Build.completion: one writer reports three ids

- **Answers:** census `Build.completion` FAIL (60 vs 21); ledger `bg_medical_mappings-Build.completion`; CF-02
- **Change:** report rows per registered id: return this asset’s own partition (`counts["bg_medical_mappings"]`) from `run()` when dispatched as `bg_medical_mappings`, or scope the other two assets’ records separately (they are declared riders). The shared seed already returns per-table counts (`l0_medical.py:416-448`), so no new computation.
- **Files / declaration / migration:** `pipeline/orchestrator/writers/bg_medical_mappings.py` (WriterResult construction; `ctx` carries the dispatched asset id or the writer keeps `asset_id`)
- **Failing-first test and mutation:** failing-first: `rows_written` equals the asset’s own count_sql scope after a first build; a seeded row in a sibling table does not move it; mutation: revert → mismatch returns
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** needs production rebuild of the three medical assets (small tables, idempotent) to refresh the records; or detector-side per CF-01/CF-02 with no rebuild
- **Gate it moves:** Build (completion)
- **Fix class:** writer code; **buildable before J1:** tier-independent for the writer; the rider semantics (`producer_covered`) are tier-dependent (TGH-T4-01)
- **Question for SS:** May the rider ids be dispatched through this writer and each recorded on its own count?

### FD-2 · Carr detector — D1 on the 21 rows

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** resolve each row’s `classical_citation` (BPHS Ch.18 / Ashtāṅga Hṛdaya / Caraka) to the corpus where present and test anchor terms; rows citing texts not in the 15-text corpus (Ashtāṅga Hṛdaya, Caraka) are reported as unverifiable, never passed.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-3 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_medical.py` for any composed text column; declare `[]` expected (literal mappings)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-4 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 1 module: `query_medical_mappings.ts`; CF-04
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
- **CF-02** — Producer attribution: rider ids, multi-table writers and multi-producer tables. *This asset:* shared writer total 60 vs own 21
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* 1 module

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `graha` (census, 0 duplicates; the 21 rows comprise graha, combination and modifier rows, so the key is read at design time against the DDL). Upsert; volatile: `created_at`. `not_diagnosis` must stay TRUE on every row.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 21 classical mappings and the `not_diagnosis` flag; this is a reference, not a diagnostic system.
- **Carriage check chosen (T4 §4.1; one only):** D1 (only for the texts present in the corpus).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2
