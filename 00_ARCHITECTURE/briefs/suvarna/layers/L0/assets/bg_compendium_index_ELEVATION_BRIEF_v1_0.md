---
asset_id: bg_compendium_index
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
track_i_items: [TI-L0-03, TI-L0-05]
ledger_gap_ids: [bg_compendium_index-Idem.pattern, bg_compendium_index-Earn.build_record, bg_compendium_index-Cost.baseline, bg_compendium_index-Complete.depth, bg_compendium_index-Dens.served, bg_compendium_index-Carr.detector, bg_compendium_index-Build.history]
---
# bg_compendium_index — Top-level navigational index over the corpus (per-text-per-chapter and per-text-per-topic rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

Aggregates `classical_text_chunks` into `brahma_compendium_index`: pass A per-text-per-chapter rows, pass B per-text-per-topic-tag rows, with a mechanical synopsis (first three chunks concatenated, ≤1,000 characters; zero LLM) and a convergent full replacement after source validation (`platform/python-sidecar/pipeline/orchestrator/writers/bg_compendium_index.py:1-12`; delete-then-insert at `:168`). 9,571 rows. Depends on `bg_reference` and `bg_texts`; no active dependent declared (census 0/0). The declarations record that the writer **composes** the `significance` text column by f-string from the passage count (`:97,109`), so Narr applies.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:401` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_compendium_index.py:116`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `brahma_compendium_index`; count_sql tables: `brahma_compendium_index` | census CEN-R |
| live rows / floor | 9571 / 9,571 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_reference`, `bg_texts` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `brahma_compendium_index`: 5 non-test py/ts/tsx files reference it (3 outside brahmagyan/ and bg_*.py writers): `coverage_matrix.ts`, `parity_check.ts`, `source_query_availability.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_compendium_index.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 9c96df96 complete/skip_no_delta (2026-09-06) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_compendium_index.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 1 error(s) and 0 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-05): post-write integrity check failed: integrity_check_sql → False |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 9c96df96 complete/skip_no_delta (2026-09-06) |
| Complete (information, D3) | Complete.depth | PARTIAL | 9571 rows, 13 cols; fully populated 9; NEVER populated ['chapter_title_en', 'chapter_title_sa'] |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = ['significance'] (declared) |

**PASS cells (compact):** Idem.pattern † (the asset's own table(s) replaced by delete-then-insert: brahma_compendium_index (bg_compendium_index.py:168)…); Vocab.identity (declared key (index_id): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (3 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-06); Build.registered (@register in bg_compendium_index.py; registry agrees); Build.target †; Count.floor.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_compendium_index-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_compendium_index-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_compendium_index-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_compendium_index-Complete.depth | Complete | information | `chapter_title_en` and `chapter_title_sa` never populated (9,571 rows, 13 cols); a width/depth opportunity, not a blocker (D3) \| ledger: measured: 9571 rows, 13 cols; fully populated 9; NEVER populated ['chapter_title_en', 'chapter_title_sa'] / required: the Complete gate's claim |
| bg_compendium_index-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | CF-04 \| ledger: measured: 1 module(s): query_compendium_index.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_compendium_index-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_compendium_index-Build.history | Build | history | 1 error 2026-09-05 (`post-write integrity check failed`); latest run complete; CF-10 \| ledger: measured: latest run complete, but 1 error(s) and 0 abort(s) on record. post-write integrity check failed: integrity_check_sql → False / required: the Build gate's claim |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |

## 3 · Disposition

**keep (P)** — the index is regenerated from the corpus and nothing reads it as authority; open items are the Narr/Null declaration already made, depth information and detectors. No retire: a reference asset is not retired for want of a reader (T4 §4.1).

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Narr: golden test for the composed `significance` text

- **Answers:** declarations `prose_fields = [significance]`; census Narr.* registered at rev 5 (not in the saved run); CF-06
- **Change:** Narr applies: the string states a computed count (`{len(rows)} passage(s)`). Add the narration-fidelity test (N.7 item 5): for each pass-A/pass-B row, the count in `significance` equals the row’s passage-count column; one golden row per pass.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/tests/` (new test next to the writer) — the writer is unchanged
- **Failing-first test and mutation:** golden-value test: the sentence for a seeded chapter with 3 passages says 3; mutation: change the f-string’s count → the test fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (test only)
- **Gate it moves:** Narr (fidelity_test)
- **Fix class:** writer code (test only); **buildable before J1:** tier-independent (N.7 item 5, SS Narr ruling 2026-10-01)

### FD-2 · Carr detector — D1 against the corpus

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** every index row points to a (text_id, chapter/topic) that exists in `classical_text_chunks` and its passage count equals the live grouped count; report mismatches. The index carries no classical claim of its own, so D1 here is referential correspondence.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-3 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in `classical_text_chunks` (the index has no citation column of its own; its provenance is the text_id/chapter pointer) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration); a data fix would be a separate design
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### FD-4 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 1 module: `query_compendium_index.ts` (shared with bg_texts); CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* referential D1
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* no citation column on the table
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* `query_compendium_index.ts`
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 1 error on record; latest run complete

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `index_id` (census: 0 duplicates). Convergent full replacement: the fingerprint is the set of `(text_id, chapter_num | topic_id, passage count, synopsis)`; volatile: `index_id` if surrogate, `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the two-pass shape (chapter and topic) and the mechanical synopsis rule; the passage counts.
- **Carriage check chosen (T4 §4.1; one only):** D1 (referential correspondence to `classical_text_chunks`); no semantic claim to carry.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
2. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
3. CF-10: ANSWERED by SS 2026-10-01 (Q11): yes: Build.history counts only runs since the last change to the writer or the registry row.

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-05.
