---
asset_id: bg_reference
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
ledger_gap_ids: [bg_reference-Idem.pattern, bg_reference-Build.completion, bg_reference-Earn.build_record, bg_reference-Cost.baseline, bg_reference-Carr.detector, bg_reference-Build.history]
---
# bg_reference — Typed reference library (11 tables, 1,242 rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Registry description: 'Structured properties owned by `bg_reference` across 11 current typed tables; yoga, dosha and dasha reference rows belong to their dedicated assets'. The tables: `reference_planets` (11), `reference_signs`, `reference_houses`, `reference_aspects`, `reference_karakas`, `reference_vargas`, `reference_upagrahas`, `reference_strength_systems`, `reference_constants`, `reference_glossary`, `reference_topic_tags` (1,242 rows in total; the conventions in force that T2's DP01 asks L0 to hold). The writer delegates to `brahmagyan/l0_reference.py:seed_reference` (ON CONFLICT upserts, e.g. `:1315,1362`) and pins `tuple_row` around the call because `l0_reference.py:1418` indexes a fetched row numerically while the orchestrator connection uses `dict_row`; the writer's comment records the `KeyError: 0` that put the asset in error in the 2026-08-02 L0 global build (`platform/python-sidecar/pipeline/orchestrator/writers/bg_reference.py:26-45`). Depends on `bg_ontology` (FK validation of ontology ids); declared dependents `bg_compendium_index`, `bg_concordance`, `bg_text_index`, `ga_sensitive` (census direct 4 / transitive 62). `source_citation` populated 11/11 on `reference_planets`.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:202` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_reference.py:18`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `reference_planets`; count_sql tables: `reference_planets`, `reference_signs`, `reference_aspects`, `reference_vargas`, `reference_houses`, `reference_strength_systems`, `reference_karakas`, `reference_upagrahas`, `reference_constants`, `reference_topic_tags`, `reference_glossary` | census CEN-R |
| live rows / floor | 1242 / 1,242 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_ontology` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 4 / transitive 62 (every layer); named: `bg_compendium_index`, `bg_concordance`, `bg_text_index`, `ga_sensitive` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `reference_aspects`: 1 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers); `reference_constants`: 1 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers); `reference_glossary`: 1 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers); `reference_houses`: 1 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers); `reference_karakas`: 3 non-test py/ts/tsx files reference it (1 outside brahmagyan/ and bg_*.py writers): `bo_pratijna_karyatva.py`; `reference_planets`: 4 non-test py/ts/tsx files reference it (1 outside brahmagyan/ and bg_*.py writers): `bo_pratijna_v4_engine.py`; `reference_signs`: 11 non-test py/ts/tsx files reference it (10 outside brahmagyan/ and bg_*.py writers): `ga_nakshatra.py`, `resonance_rebuild_disposable_rehearsal.py`, `resonance_rebuild_backup_sql.py`, `ga_sensitive_writer.py`, `ga_sensitive_degree_writer.py` +5; `reference_strength_systems`: 1 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers); `reference_topic_tags`: 5 non-test py/ts/tsx files reference it (1 outside brahmagyan/ and bg_*.py writers): `parity_check.ts`; `reference_upagrahas`: 2 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers); `reference_vargas`: 2 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers) | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 21df3b6a complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record says rows_written=0 against live=1242 (global); target_table reference_planets alone: 11 row(s), whole table — context, not the compared figure |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 21df3b6a complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 11/11 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): reference_planets (brahmagyan/l0_reference.py:13…); Vocab.identity (declared key (planet_id): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (2 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.registered (@register in bg_reference.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_reference-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_reference-Build.completion | Build | real (T4 §4.2 check 6) | see the fix design \| ledger: measured: build record says rows_written=0 against live=1242 / required: the Build gate's claim |
| bg_reference-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_reference-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_reference-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_reference-Build.history | Build | history | 1 abort on record, 0 errors; the 2026-08-02 error predates the saved history window or was repaired; latest run complete; CF-10 \| ledger: measured: latest run complete, but 0 error(s) and 1 abort(s) on record. / required: the Build gate's claim |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — all applicable Idem/Vocab cells PASS; the FAIL is the changed-rows reading (CF-01) and the one defect found is a latent shared-module fragility already contained at the writer boundary.

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Build.completion: converged rerun reports 0 changed rows

- **Answers:** census `Build.completion` FAIL ("rows_written=0 against live=…"); CF-01
- **Change:** apply CF-01 option A (or B after the ruling): the seeds report inserted/changed rows only; declaration + detector rule
- **Files / declaration / migration:** `platform/scripts/governance/asset_census.py` (Build.completion) + the asset’s declarations entry; option B instead edits the seed function’s returned counts
- **Failing-first test and mutation:** see CF-01
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** A: none. B: needs production rebuild of this asset (idempotent, no data change)
- **Gate it moves:** Build (completion)
- **Fix class:** detector/tooling (A) or writer code (B); **buildable before J1:** tier-dependent: T4 §4.2 check 6 wording
- **Question for SS:** CF-01: is a converged-rerun `rows_written = 0` on a declared changed-rows writer a PASS?

### FD-2 · Remove the root cause of the row-factory workaround

- **Answers:** writer comment `bg_reference.py:26-45`; no census cell (the workaround holds)
- **Change:** make `l0_reference.py:1418` read the fetched row by key or by a helper that accepts both row factories, so the `tuple_row` pin becomes unnecessary; keep the pin until the shared-module test passes under `dict_row`. `l0_reference.py` is a shared brahmagyan module, so the change is made in one reviewed lane.
- **Files / declaration / migration:** `platform/python-sidecar/brahmagyan/l0_reference.py:1418`; test under `platform/python-sidecar/tests/`
- **Failing-first test and mutation:** failing-first: run `seed_reference` against a `dict_row` connection (fails today without the pin); mutation: reintroduce `r[0]` → fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (idempotent; no data change)
- **Gate it moves:** Build (contract robustness; not a registered cell)
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-3 · Carr detector — D1 over the reference tables

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** check each table’s source/convention column against its declared sources (`reference_planets.source_citation` 11/11); for `reference_aspects`, `reference_vargas`, `reference_strength_systems` the conventions are declared values, so D1 is referential (every referenced ontology id resolves) plus a sampled source reading.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_reference.py` for any composed text column; declare the composed column list or `[]` after reading `l0_reference.py`: `reference_glossary` carries definitions (a candidate for prose to check)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Dens attribution

- **Answers:** census `Dens.served` N/A at rev 1; `N22/dens_repair_needs.json` lists it as comment-only: under the repaired scanner (rev 4) it reads NO_DETECTOR, never N/A; CF-04
- **Change:** if a served module reads a `reference_*` table, declare `carriage.served_surface` with `read_evidence`; otherwise declare no served surface with evidence.
- **Files / declaration / migration:** `asset_declarations.json` (`carriage`)
- **Failing-first test and mutation:** declarations validation
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Dens
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: N-22

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-01** — Build.completion for converged reruns (rows_written = changed rows, not rows present). *This asset:* rows_written = 0 on a converged rerun
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration (`reference_glossary`)
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* NO_DETECTOR (comment-only mention) under rev 4
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 1 abort on record
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* upsert over eleven tables, no DELETE found

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `planet_id` for `reference_planets` (census, 0 duplicates); each of the 11 tables has its own key (read at design time). Upsert; volatile: `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 1,242 reference rows across the 11 typed tables and their ontology-id references.
- **Carriage check chosen (T4 §4.1; one only):** D1 (referential to the ontology plus sampled source correspondence).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2
