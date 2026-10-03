---
asset_id: bg_vastu_directions
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
decisions_applied: "SS answers to INDEX section 7, 2026-10-01 (items marked R are PROVISIONAL until the J1 review); disposition accepted as proposed"
track_i_items: [TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-25, TI-L0-33]
ledger_gap_ids: [bg_vastu_directions-Idem.pattern, bg_vastu_directions-Earn.build_record, bg_vastu_directions-Cost.baseline, bg_vastu_directions-Complete.depth, bg_vastu_directions-Dens.served, bg_vastu_directions-Carr.detector]
---
# bg_vastu_directions — Vāstu direction–graha reference (8 directions + remedials; 32 rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

'Classical Vastu Shastra direction–graha associations: 8 compass directions each mapped to a ruling graha, secondary graha, element, favorable color and classical citation (Mayamata Ch.6). Also seeds `bg_vastu_direction_remedials` (~22 rows) with 2–3 remedies per direction' (seed description). Two tables (`bg_vastu_directions`, `bg_vastu_direction_remedials`; 32 rows summed), ON CONFLICT upserts (`platform/python-sidecar/brahmagyan/l0_vastu_directions.py:298,320`). `classical_citation` 8/8; `secondary_graha` is never populated (information). No declared dependents (census 0/0), but `platform/src/lib/retrieval/registry/layers/L1_ganita/get_vastu_directions.ts` reads `bg_vastu_direction_remedials`, i.e. an L1 served module reads an L0 table with no declared edge (upper-layer reads of L0 are `bedrock_exempt` in the DAG detector, a provisional SS ruling of 2026-10-01 pending the J1 review). Served by `query_vastu_directions.ts` and `query_vastu_direction_remedials.ts`. The cited text, Mayamata, is not among the 15 texts of the corpus.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:642` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_vastu_directions.py:22`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_vastu_directions`; count_sql tables: `bg_vastu_directions`, `bg_vastu_direction_remedials` | census CEN-R |
| live rows / floor | 32 / 32 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_vastu_direction_remedials`: 5 non-test py/ts/tsx files reference it (2 outside brahmagyan/ and bg_*.py writers): `get_vastu_directions.ts`, `source_query_availability.ts`; `bg_vastu_directions`: 7 non-test py/ts/tsx files reference it (3 outside brahmagyan/ and bg_*.py writers): `producer_editorial_review.ts`, `source_query_availability.ts`, `dossier_slices.generated.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_vastu_directions.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_vastu_directions.ts; declaring density_contract: 0 |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Complete (information, D3) | Complete.depth | PARTIAL | 8 rows, 8 cols; fully populated 6; NEVER populated ['secondary_graha'] |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (classical_citation populated on 8/8 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_vastu_directions (brahmagyan/l0_vastu_directi…); Vocab.identity (declared key (direction): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.exercised (2 executed run(s) of 2 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_vastu_directions.py; registry agrees); Build.target †; Count.floor.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_vastu_directions-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_vastu_directions-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_vastu_directions-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_vastu_directions-Complete.depth | Complete | information | `secondary_graha` never populated (8 rows, 8 cols) \| ledger: measured: 8 rows, 8 cols; fully populated 6; NEVER populated ['secondary_graha'] / required: the Complete gate's claim |
| bg_vastu_directions-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | CF-04 \| ledger: measured: 2 module(s): query_vastu_direction_remedials.ts, query_vastu_directions.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_vastu_directions-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — census Idem/Vocab/Ldgr PASS; the open items are detectors and the carriage limit that the cited source is outside the corpus.

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10); the rows are recorded `unsourced` (Q18).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr detector — D1 with an explicit unverifiable class

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** decided (SS 2026-10-01, Q18): the Mayamata rows are recorded as outside the corpus, explicitly `unsourced` (attribution state), for now; admitting the text to the corpus is an opportunity. The D1 detector reports all 32 rows `unverifiable: source outside corpus`, never a pass. No row changes.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-2 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_vastu_directions.py` for any composed text column; declare `[]` expected (literal mappings and remedials) after reading `l0_vastu_directions.py`
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-3 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 2 modules: `query_vastu_direction_remedials.ts`, `query_vastu_directions.ts`; CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** no row changes (test or code-side only); declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference.
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### FD-4 · Record the Mayamata rows as explicitly `unsourced` (declaration only)

- **Answers:** SS Q18; TI-L0-33
- **Change:** declare in the declarations file that all 32 rows’ source (Mayamata Ch.6) is outside the corpus and therefore `unsourced`; no row, column or citation changes and no rebuild (the additive `attribution_state` column of TI-L0-09 is NOT applied to this asset in this wave).
- **Files / declaration / migration:** `asset_declarations.json` (`carriage`/source note) — Track E file
- **Failing-first test and mutation:** declarations validation; the D1 detector reads all 32 rows `unverifiable: source outside corpus`; mutation: remove the declaration → the Ldgr/Carr reading loses its explanation
- **Output change:** none
- **Blast radius:** no row changes; readers (`query_vastu_directions.ts`, `get_vastu_directions.ts`, editorial-review modules) see no change.
- **Rebuild:** none (declaration only)
- **Gate it moves:** Ldgr (qualification), Carr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (decided)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 with an unverifiable class
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* 2 modules
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* upsert over two tables, no DELETE found

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `direction` (census, 0 duplicates) for `bg_vastu_directions`; the remedials table has its own key (read at design time). Upsert; volatile: `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 8 direction rows with citations and the remedials.
- **Carriage check chosen (T4 §4.1; one only):** D1 (reported unverifiable while the source is outside the corpus).
- **Opportunities (never blocking):** admit Mayamata to the corpus so D1 can run (deferred by SS).

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (Q18): record the Mayamata rows as outside the corpus (explicitly `unsourced`) for now; admitting the text is an opportunity.
2. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
3. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
4. CF-12: ANSWERED by SS 2026-10-01 (Q12): yes: 'no orphan rows under the writer's own partition' is the Idem claim for L0 upsert writers.

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-25, TI-L0-33.


## 8 · WAVE addendum (2026-10-03, Track I I.FL0; docs only, additive, PROVISIONAL like the rest of this brief)

**Disposition note, N-102 (owner ruling): deferred by owner (N-102): source not held.** This asset's classical source text is not in the served corpus (the corpus holds the 16 texts listed by `classical_texts`; this asset's source is not among them or not at passage grain). The owner ruled to leave classical texts the platform does not hold: this asset is NOT being provenance-confirmed now. It stays NO_DETECTOR on Carr and is not elevated in this campaign. No other disposition in this brief changes; the existing fix designs remain valid but are not to be scheduled for Carr. Evidence and the no-writer analysis for the neighbouring assets: `/Users/Dev/suvarna-evidence/TrackI/WAVE_NO_WRITER_LIST.md`.
