---
artifact: DECISION_SHEET_L2
layer: L2 Bodha (bo_*)
version: "1.1"
status: "RULED (SS decision N-59, 2026-10-01); items marked (R) provisional until the J1 independent review"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L2 (decision sheet over the briefs; one pass for Strategic Suvarṇa)
source_branch: "suvarna/land/A-L2-briefs-001 (PR #2831, open) at 29b2268a8; this sheet is on suvarna/land/A-L2-decisions-001"
source_files: "00_ARCHITECTURE/briefs/suvarna/layers/L2/assets/INDEX.md (section 9, 20 open questions plus the one answered argala item) and the 23 per-asset briefs in the same directory"
scope: "docs only; no code, registry, migration or database write (read-only SELECTs as suvarna_reader)"
provisional: "every ruling taken from this sheet is provisional until the J1 independent review"
ruling_record: "SS decision N-59, 2026-10-01, on PR #2841 (branch suvarna/land/A-L2-decisions-001, HEAD 1ad09993b at the time of ruling); recorded in section Rulings (SS, N-59, 2026-10-01) below; the briefs and INDEX carry the rulings on branch suvarna/land/A-L2-briefs-002"
---

# L2 Bodha decision sheet (for one ruling pass by Strategic Suvarṇa)

## 0 · How to read this sheet

**Structure.** Group A records four items SS has already ruled; they are not re-asked. For each, the sheet records the ruling, the facts verified against code and the database, what the ruling requires in the code, and the effect, so it can be executed without another round. Group B holds the open questions: the 20 open questions of INDEX section 9 (Q-L2-01 to Q-L2-20, in INDEX order) plus Q-L2-21, the residual of the argala ruling (INDEX section 9 records the argala item as ANSWERED and leaves one domain question inside the `bo_karanajala` brief; together that is the 21 questions routed to SS). Every B item has the same fields: question, facts, recommendation, effect of each possible answer, citation. A summary table closes the sheet. Items marked **(R)** in the summary raise or define a verdict or change stored outputs: provisional until J1.

**Rules SS gave for rulings (applied throughout).** (1) A classical fact needs a `bg_texts` corpus citation (B.3). (2) Where traditions differ, the project's existing L1/engine convention is the authority (CLAUDE.md §N.5) and the alternative is recorded as a named variant. (3) Every ruling is provisional until the J1 independent review. (4) Citation states (new rule from the coordinator, applied to every citation here): an OCR text-search hit not checked against the print is `sourced_ocr_unverified` (a distinct state, neither `sourced` nor `unsourced`); a passage not found is `unsourced`; only a citation verified at passage level counts toward a PASS on the Ldgr gate. No citation in this sheet is above `sourced_ocr_unverified`. The L3 rulings the coordinator relayed (3°20' Gandanta width with 0°48' as a named stricter variant; MEAN node as the L1/engine convention with TRUE a named variant; an honest null where the engine defines no scope) touch no L2 item and are not used here, except that the "honest null, never an invented scope" principle is applied in Q-L2-03 and Q-L2-05.

**Evidence tags.** `[code]` = read in the repository at 29b2268a8 (the PR #2831 head; file:line given); a few `[code@main]` items were read from `origin/main` 4eb40bec1 because the files are not on this branch. `[db]` = read-only `SELECT` as `suvarna_reader` on 2026-10-01 between 17:50Z and 18:10Z (queries in the appendix; no write; no credential shown). `[corpus]` = text search of `classical_text_chunks` (the chunk table of the `bg_texts` corpus); the chunk id is given; the text is OCR and was read by me but not checked against the printed book, so every `[corpus]` item is `sourced_ocr_unverified`. `[brief]` = quoted from a brief or INDEX and NOT re-verified here. Where a classical item was searched for and not found the sheet says `citation: not found in repo, needs bg_texts lookup` (state `unsourced`). Non-classical items say `citation: n/a`.

**Charts.** Canonical = `482012f1`. Abhinandan = `1c826d5a`. Third chart = `cb73cd3d`. Every `[db]` figure is the canonical chart unless another chart is named.

**Four facts that change how several answers read** (found while verifying; none is in the briefs):

1. **Every canonical-chart L2 row predates the code on main.** The 23 `bo_*` assets were last built between 2026-09-08 and 2026-09-12 (`asset_throughput.last_built_at`; 12 `lit`, 11 `stale`) `[db]`. PR #2607 (`fa9857f00`, merged 2026-09-16) changed 22 `bo_*` writer files, which cover all 23 L2 assets (the rerank lives in `bo_laksana.py`), plus `_idempotency.py`, `formulas.py` and the amplifier module, and added `data_plane_contracts.py` (`git show --stat fa9857f00`); #2773 (2026-09-30) changed `bo_upaya` again. So a census cell that reads "never populated" or "no detector" can describe a gap that main's code already closes but no rebuild has applied. Two such cases are found below: the CDLM shared-root carrier (Q-L2-14) and three `bo_pramana_mapa` pass-flags (Q-L2-20). Output-change estimates in this sheet are measured from rows built by the older code.
2. **Ten, not nine, `bodha_*` tables are unreadable to `suvarna_reader`** `[db]`: the nine INDEX names plus `bodha_rm_dasha_windowed_prescriptions`. The reader grant INDEX §5 CF-02 asks for has not been applied (Q-L2-01).
3. **Migration number 1211 is taken.** `origin/main` carries `platform/migrations/1211_asset_throughput_state_audit_builder_grants.sql` (Pravāha B6.0, an unrelated grant) `[code@main]`, while INDEX §1 and the `bo_pratijna` brief still call the held five-edge migration "1211, not applied". That migration needs a fresh number at execution (Q-L2-07).
4. **A global fact about the MSR cascade changed under the briefs.** Live `pg_constraint` shows zero foreign keys referencing `bodha_msr_signals` `[db]`; the briefs' F-3 text describes three L2 keys still in force. This is Group A item A-2.

---

## GROUP A · Already ruled by SS (recorded; do not re-ask)

SS N-59 (2026-10-01): Group A accepted as written.

### A-1 · `bo_karanajala` argala: L1 is the authority; L2 references

**Ruling (SS, relayed by the coordinator 2026-10-01).** By CLAUDE.md §N.5 L1 is the authority and L2 never recomputes an L1 fact: `bo_karanajala` must REFERENCE L1's computed argala (`argala_natal_matrix` / `virodha_argala_natal_matrix`, offsets {2, 4, 5, 11}, Jaimini). If L2 genuinely needs the BPHS {2, 4, 11} variant it is a separately named, cited convention, never a silent second definition. (INDEX §9 "Answered since"; `bo_karanajala` brief FD-2; the residual domain question is Q-L2-21.)

**Facts.**
- L2 computes its own: `ARGALA_POSITIONS = {2, 4, 11}`, `VIRODHA_POSITIONS = {12, 3, 10}` and the pairing 2→12, 4→3, 11→10 (`pipeline/orchestrator/writers/bo_karanajala.py:386-391`, `:495-560`) `[code]`. Stored edges on the canonical chart: `argala_positive` 75, `argala_virodha` 44 (119 across five ayanamshas), of which 10 are cancelled `[db]`. Arithmetic check: over the nine grahas in Lahiri the ordered pairs at house offset 2 / 4 / 11 number 10 / 6 / 8 = 24, and 119 / 5 is about 24 per ayanamsha, so the stored set is exactly the {2, 4, 11} pairs; the 5th-house pairs (4 in Lahiri) are absent `[db]`.
- L1 stores a 12 x 12 sign matrix per varga and ayanamsha: `argala_natal_matrix` and `virodha_argala_natal_matrix`, 144 rows each for D1 (`ga_writers/ga_structural_writer.py:4670-4770`, `_build_argala_rows`), with `ARGALA_OFFSETS = [2, 4, 5, 11]` and `VIRODHA_OFFSETS = [12, 10, 9, 3]` (`:615-616`) `[code]`; a separate `net_argala_per_varga` count (`:7258-7285`) `[code]`.
- **Three properties of the L1 rows that the L2 fix must respect** (found while reading; for the L1 owner): (i) the matrix is sign-to-sign, not graha-to-graha: an argala cell scores `1.0` for any source sign at an argala offset and subtracts `0.25` per malefic occupant, so an EMPTY source sign scores `1.0` (`:4713-4722`); a graha-level edge therefore needs the occupant join to `graha_position`, and the score must not be read as proof of an occupant; of the 48 non-zero D1 cells for Lahiri, 32 score `1.0`, 12 score `0.75`, 4 score `0.5` `[db]`; (ii) every argala row carries `verification_pass_status = single` (`verif=UNVERIFIED_DEFAULT`, `:4737`, `:4759`) `[code][db]`; (iii) neither L1 nor L2 reverses the count for Rahu and Ketu, which both classical texts state (Q-L2-21 citation) `[code]`.
- Ground truth that supports the ruling: L1's offsets match the two corpus texts cited at Q-L2-21, so the ruling picks the better-supported set.

**What the ruling requires.** (1) `_build_argala_edges` reads the L1 matrix cells (offset in {2, 4, 5, 11} for argala, {12, 10, 9, 3} for virodha) joined to the graha occupants of the source sign, and cites the L1 `fact_id`s in `constituent_fact_ids_array`; `ARGALA_POSITIONS`/`VIRODHA_POSITIONS`/`ARGALA_TO_VIRODHA` are removed from the writer. (2) The virodha pairing (which obstructing offset cancels which argala offset: 12-2, 3-4, 10-11, 9-5) is a rule L1 does not store as a pairing (it stores offsets, not pairs); either L1 adds the pairing or L2 states it as a named, cited rule. This is the one place the ruling does not close by itself; recorded as a sub-point of Q-L2-21. (3) Failing-first tests per the brief: every stored argala edge corresponds to an L1 matrix cell and cites its `fact_id`; no edge exists at an offset L1 does not list; mutation: restore a local offset set and the test fails.

**Effect.**
- Output: the argala edge set changes: up to +4 argala pairs per ayanamsha (the 5th-house pairs, about +17% over 24) plus their virodha counterparts at the 9th; edge ids are deterministic (`assign_deterministic_edge_ids`), so unchanged pairs keep their ids `[brief][code]`. The count for the canonical chart cannot be stated before the build.
- Rebuild: `bo_karanajala` and its dependents (`bo_cgm_motifs`, `bo_cgm_paths`, `bo_yantra_mechanism`, `bo_laksana_rerank`, `bo_sangati`, `bo_drishti`, `bo_anveshana`, `bo_pramana_mapa`, `bo_samvada`, `bo_chart_gestalt`, `ph_nimitta` and the L3/L5 readers; transitive 44) `[brief]`. Output change: (R), provisional until J1. No registry or migration change.

**Citation.** See Q-L2-21 (all `sourced_ocr_unverified`).

**RULING (SS, N-59, 2026-10-01).** Accepted as written.

---

### A-2 · The F-3 / MSR-before-Kāla-and-Phala ordering rule retires after 1214 AND the three L2 key drops

**Ruling (SS).** The ordering invariant (the six MSR writers strictly before the five Kāla assets, `ka_yojaka`, the seven Phala assets and the six L2 consumers) retires only after migration 1214 is merged (five `kala_*` keys dropped) AND the three L2 key drops are applied. (INDEX §3, §5 CF-13, §7; `F3_MSR_FK_DROP_v1_0.md`.)

**Facts.**
- Migration `platform/supabase/migrations/1214_f3_drop_kala_msr_signal_fks.sql` is on `origin/main` (PR #2828, `9f02ed504`) `[code@main]`. It drops `kala_activation`, `kala_bhavishya`, `kala_convergence`, `kala_darshana`, `kala_obstruction` `signal_id` keys and states that the three L2 keys (`bodha_contradictions.signal_a_id` / `signal_b_id`, `bodha_signal_embeddings.signal_id`) are an owner-path change, not part of 1214.
- Live: `select ... from pg_constraint where contype='f' and confrelid='bodha_msr_signals'::regclass` returns **0 rows** (2026-10-01 17:50Z) `[db]`. Both conditions of the ruling hold on the database structure (the grant plan v1.3 document that records the L2 drops was not read; the structure was).
- The MSR replace helper does not rely on the keys any more: it deletes `bodha_signal_embeddings` and `bodha_contradictions` rows explicitly before the MSR delete (`bodha_writers/_idempotency.py:196-206`), so dropping the L2 keys orphans nothing `[code]`. The comment above those deletes still says every key is `ON DELETE CASCADE`, "all eight" (`:179-180`, and `:89` in the sibling helper): now stale; a documentation edit.
- `assert_l2_msr_delete_safe` still exists (SECURITY DEFINER). It now enforces only the admitted-asset context and the exact-scope row lock, and its cross-layer refusal loop finds no key to refuse on, so it refuses nothing on any chart `[db: pg_get_functiondef]`.
- No dangling reference today: `kala_activation` 336,093 (Abhinandan) and 1,055 (third), `kala_convergence` 17,957 and 2,540, `kala_obstruction` 741 and 6, `kala_darshana` 750, `kala_bhavishya` 100 all resolve to a live `bodha_msr_signals.signal_id`; 0 dangling `[db]`. The canonical chart has no Kāla rows (I-6) `[brief]`.
- The residual hazard 1214 itself names: a changed or removed signal id leaves a Kāla row dangling with no error; the control is the read-only detector `platform/scripts/governance/msr_dangling_signal_refs.py` (on `origin/main`). Charts 1c826d5a and cb73cd3d carry v4 signal ids, so a first v5 regeneration of either would strand rows until their Kāla assets rebuild `[brief][code@main]`.

**What the ruling requires.** (1) Retire the ordering invariant as a rebuild precondition (the plan no longer needs "MSR writers before Kāla/Phala"). (2) Reword the R243 annotation (Q-L2-10). (3) Keep `msr_dangling_signal_refs.py --chart-id` as the post-wave check; it replaces the keys' visibility, not their prevention.

**Effect.** Plan and documentation only: no code, registry or data change; removes an ordering constraint from the L2 rebuild plan. Edit the stale `_idempotency.py` comment (doc-only). One conservative note: the order guard's other rule (a dependent rebuilt after the MSR set sees the final ids, so references stay valid instead of dangling) remains good practice for the two v4-id charts and costs nothing to follow.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as written.

---

### A-3 · `chart_divisionals` RLS incident fixed; "table empty" readings resolved

**Ruling (SS).** The RLS incident is fixed (row-level security disabled, data intact: canonical 24,392 rows; Abhinandan and third chart 23,542 each); any brief reading that says the table is empty is resolved.

**Facts.** `select relrowsecurity, relforcerowsecurity from pg_class where relname='chart_divisionals'` = `f`, `f`; row counts 23,542 (`1c826d5a`), 24,392 (`482012f1`), 23,542 (`cb73cd3d`) `[db]`, matching the ruling. L2 readers of the table: `brahmagyan/chart_reader_v4.py:182-250` (`varga_house_occupant`, `varga_position`, `varga_house_lord`), reached through `bo_pratijna` (via `ChartReaderV4`) and `bo_vargottama_dhana`'s D3 design. I searched the 23 L2 briefs and INDEX for an "empty"/"RLS" reading of `chart_divisionals` and found none, so no L2 text needs correcting; the incident bears on L2 only as an input availability fact for `bo_pratijna` (its stored 135 rows are unaffected; a rebuild now has its inputs) `[code][db]`.

**What the ruling requires.** Nothing in the L2 briefs; note for the `bo_pratijna` rebuild that its upstream read is available (and see Q-L2-07 for the declared-edge audit that touches the same reads).

**Effect.** None (record only).

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as written.

---

### A-4 · SS rulings rules and the new citation-state rule

**Ruling (SS).** (1) A classical fact needs a `bg_texts` corpus citation (B.3). (2) Where traditions differ, the project's existing L1/engine convention is the authority (§N.5) and the alternative is recorded as a named variant. (3) Every ruling is provisional until the J1 independent review. (4) Coordinator addition: OCR text-search hits not checked against print are `sourced_ocr_unverified`; not found = `unsourced`; only passage-level verification counts toward an Ldgr PASS. Items that raise/define a verdict or change outputs are provisional (R).

**Effect.** Applied in this sheet (see §0). The only classical-fact item in L2 is argala (A-1, Q-L2-21); its citations are `sourced_ocr_unverified` and therefore cannot yet support an Ldgr PASS for that asset.

**RULING (SS, N-59, 2026-10-01).** Accepted as written.

---

## GROUP B · Open questions

SS N-59 (2026-10-01): 17 accepted as recommended (Q-L2-01, 02, 04, 05, 07, 09, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21), 4 changed (Q-L2-03, 06, 08, 16). Each item carries its ruling line after the Citation; the section Rulings (SS, N-59, 2026-10-01) after the summary table holds the digest, the sequencing, the Track I items and the list of writers that would change.

### Q-L2-01 — CF-02: producer attribution for the five multi-table / shared-table writers

**Question.** Should the five Build.completion FAILs be fixed by declaring each asset's produced-table set (option A, which first needs a declarations-schema field), or by widening `count_sql` to every produced table (option C); and may `suvarna_reader` be granted SELECT on the unreadable `bodha_*` tables so the unexplained gaps can be confirmed?

**Facts.**
- Return expressions sum every table a writer fills: `bo_cdlm_summary.py:464` (summary + rollups + clusters), `bo_karanajala.py:1921` (edges + contradictions; the 130 arudha/special_lagna nodes it inserts are not counted), `bo_sangati.py:511` (cells + convergence + triangulation), `bo_upaya.py:1987` (resonances + prescriptions + summary + bundles + patterns), `bo_anveshana.py:834` (discoveries + anomalies), `bo_bimba.py:663` (its five node types) `[code]`.
- Live `rows_written` against the registry `count_sql` count: `bo_bimba` 255 vs 385; `bo_cdlm_summary` 70 vs 5; `bo_karanajala` 864 vs 849; `bo_sangati` 535 vs 475; `bo_upaya` 240 vs 180; `bo_anveshana` 4,437 vs 4,437 `[db]`.
- Reconstruction from readable tables: `bo_sangati` count = `bodha_cdlm_cells` 280 + `bodha_triangulation` 195 = 475; `bo_upaya` = `bodha_rm_resonances` 45 + `bodha_rm_remedy_prescriptions` 135 = 180; `bo_karanajala` edges 849; `bo_cdlm_summary` chart summary 5; `bo_anveshana` 1,161 discoveries + 3,276 anomalies = 4,437; `bo_bimba` writes 255 of the 385 nodes and `arudha` 95 + `special_lagna` 35 = 130 are `bo_karanajala`'s `[db]`. The gaps 60 (sangati), 60 (upaya), 15 (karanajala) and 65 (cdlm_summary) therefore lie in tables I cannot read: `bodha_convergence`, the three upaya ancillary tables, `bodha_contradictions`, `bodha_cdlm_domain_rollups`, `bodha_cdlm_pattern_clusters`. **Not verified.**
- `has_table_privilege('suvarna_reader', ..., 'SELECT')` is false for 10 tables: `bodha_cdlm_domain_rollups`, `bodha_cdlm_pattern_clusters`, `bodha_cgm_chart_topology_summary`, `bodha_cgm_sub_graphs`, `bodha_contradictions`, `bodha_convergence`, `bodha_rm_chart_summary`, `bodha_rm_dasha_windowed_prescriptions`, `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies` (RLS is off on all) `[db]`.
- `platform/scripts/governance/asset_declarations.json` (1.6.0) has `cross_asset_writes` but no produced-table field (grep) `[code]`.
- Precedents `[brief]` (L0 INDEX §9, read on `origin/main`): L0 Q19 "scope `count_sql` to the primary table and declare the asset multi-table"; L0 Q6 "a sibling's dispatch counts when the registry declares the rider relation". Migration 661 PART 3 widened `bo_sangati`'s `count_sql` for a cockpit-truth defect (INDEX §5).
- The orchestrator contract returns one total (`WriterResult.rows_inserted`) and is FROZEN, so no writer-side per-table split (INDEX option B is not available).

**Recommendation.** Option A: declare each asset's produced-table set (new declarations field, vocabulary, validator and a detector clause), and compare `rows_written` with the chart-scoped count over that set; do not widen `count_sql` and do not narrow it. For the two shared tables attribute by partition (`producer_asset_id` for MSR; `node_type` for `bodha_cgm_nodes`, i.e. the L0 Q6 rider relation). Also grant `suvarna_reader` read-only SELECT on the 10 tables (not 9) so the four gaps are confirmed once, before the detector is written. Reason: it is the L0 shape already ruled (Q19, Q6); a widened `count_sql` (C) would need floors re-set after a rebuild, evidence refreshes of five frozen manifests and still cannot attribute a shared table; the writer-side option is closed by the freeze.

**Effect.**
- (a) Option A: declarations-schema extension, validator and detector clause (Track E); no registry row, no stored data, no rebuild; Build.completion of the five assets then compares like with like; `bo_bimba`/`bo_karanajala` read as two producers of one table.
- (b) Option C (widen `count_sql`): registry edit for five assets (manifest `evidence_refresh_required`), cockpit counts change (cosmetic), floors must be re-stated after a rebuild; no data change.
- (c) Grant: a read-only privilege change on 10 tables (Track E / grants, not decided here); it only enables the verification of 65 / 15 / 60 / 60; no data effect. Decline: the four gaps stay "consistent with unnamed tables" and unverified.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended (option A: declared produced-table set with a detector clause; no widening of `count_sql`; L0 Q6 rider relation). The reader SELECT on the 10 tables: do it; confirm the 65 / 15 / 60 / 60 gaps before writing the detector. **Route found while recording:** all 10 tables are owned by `data_plane_l2_owner`, not `amjis_app` (`pg_tables.tableowner`, read-only), and all 10 appear in `L2_ACTIVE_TABLES` of `platform/scripts/data-plane-ownership-preflight.ts` (origin/main), so the pre-approval's condition (amjis_app owns all 10 and no gate pins their ACL) is NOT met: the grant goes as a D6 plan with hash as REVIEW, not as a migration. TI-L2-01, TI-L2-02.

---

### Q-L2-02 — CF-04: Dens (serving density) on the L2 served modules

**Question.** May a limit-only served module declare `paginated: false`; is the MSR attribution rule (a producer's served surface is the `signal_type_class` facet of `query_signals.ts`) accepted; is the scanner fix for `registry_bridge.ts` and `register_p1_synthesis.ts` a Track E item before the re-measure; and may a tier column be given to the detector through a static select rather than the descriptor?

**Facts.**
- Modules declaring `density_contract` today: `query_cdlm_summary`, `query_chart_gestalt`, `query_discoveries`, `query_mechanisms`, `query_pratijna`, `query_question_lenses`, `query_signals` (grep of `platform/src/lib/retrieval/registry/layers/L2_bodha`); not declaring: `query_cgm_motifs`, `query_cgm_paths`, `query_contradictions`, `query_quality_scorecard`, `query_triangulation`, `query_rm_*`, `query_remedies`, `query_ucd`, `query_domain_reading`, `traverse_chart_graph`, `graha_portrait` `[code]`. The contract type is `{paginated, facets, empty_reason, max_*_bytes}` (`registry/types.ts:207-213`).
- **The convention already exists:** `query_cdlm_summary.ts:144` and `query_chart_gestalt.ts:64` both declare `paginated: false, // limit is a cap; no offset, no cursor`; `query_question_lenses.ts:55-61` is the stated standard ("these values state what this handler actually does"; an auto-stamped `empty_reason` is an unbacked claim) `[code]`.
- `query_cgm_motifs.ts` and `query_cgm_paths.ts`: `MAX_LIMIT = 50` (`:14`, `:13`), `limit` but no `offset`, and they disclose `total_matching` / `more_available`; both already select `verification_pass_status` (a tier column) `[code]`. The canonical chart has 120 motifs per ayanamsha (36 `mutual_aspect`, 84 `mutual_aspect_triangle` in Lahiri), so rows beyond the 50 cap are unreachable by the tool for motifs; paths hold 45 per chart (under the cap); triangulation 39 per ayanamsha `[db]`.
- Attribution rule check: the 18 `signal_type_class` values on the canonical chart partition exactly by producer (`bo_laksana` 12 classes, each satellite 1-2 classes, no class shared by two producers) `[db]`; the facet is applied in the WHERE before the salience cap (`query_signals.ts:448-451`) and is declared in the contract (`:246`) `[code]`.
- The scanner desync on the two TS files and the NO_DETECTOR x14 count are `[brief]` (INDEX §1); not re-run.
- Dens rule context: L0 Q2 `[brief]`: "Dens applies wherever a served surface is reached; `uniform_authority: true` ... mixed-authority tables need a real tier"; `uniform_authority` is not yet a field of `asset_declarations.json` 1.6.0 or `asset_census.py` (0 occurrences).

**Recommendation.** (a) Yes: declare `paginated: false` and the true `empty_reason` on `query_cgm_motifs`, `query_cgm_paths`, `query_quality_scorecard` and the sangati modules, on the existing two-module precedent; add `offset` only to `query_cgm_motifs.ts` (the one module where the cap hides real rows: 84 triangles vs 50). (b) Yes: accept the facet attribution rule (the partition is verified on the canonical chart). (c) Yes, Track E: fix the scanner before the re-measure; reading 14 NO_DETECTORs as PASS or FAIL before then is premature. (d) A static select: `query_mechanisms.ts` should select `verification_pass_status` in a fixed column list so the claim can be read from the SQL (CLAUDE.md §N.8: a declared tier column that no code path checks is a flag without a detector); a descriptor declaration may supplement it. Reason: each answer keeps the contract equal to what the handler does, which is the standard §N.6 and N-17 already set.

**Effect.**
- (a) Yes: declaration text in five modules (TypeScript only); additive response fields; no data change; moves Dens FAIL to a measured reading for four assets after the scanner fix. No: the four FAIL cells stay FAIL, or the modules must gain offset first (a larger served-surface change for four tools).
- (b) Yes: seven MSR assets read Dens through one facet contract. No: the seven cells stay NO_DETECTOR and a per-producer served column (`producer_asset_id`) would have to be exposed (a served-surface change).
- (c) Yes: instrument work, no asset change. No: the re-measure reads 14 NO_DETECTORs.
- (d) Static select: one added response field on `query_mechanisms`; its consumers (`reading_checklist.ts`, `register_d9_judgment.ts`, `compiled_floor_adapter.ts`) gain the tier value only `[brief]`. Descriptor-only: no output change, weaker evidence.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended, (a) to (d). Declarations and TS text: no rebuild, pre-approved now. TI-L2-03, TI-L2-04.

---

### Q-L2-03 — CF-20: neutral-constant salience inputs in the five MSR satellite emitters

**Question.** The five satellite emitters feed the salience formula neutral stand-in constants for terms they never compute; are these ratified as documented approximations (option 1), replaced by an explicit not-measured value (option 2), or computed from L1 facts (option 3)?

**Facts.**
- Emitters: `arudha_emitter.py:96-100` (`_base_inputs`), `special_lagna_emitter.py:96-100`, `vargottama_dhana_emitter.py:119-123`, `sudarshana_emitter.py:241-245`, `nakshatra_semantic_emitter.py:232-236`: `orb_tightness=1.0`, `shadbala_norm=1.0`, `dignity_score=0.50`, `ashtakavarga_bindus=4`, `vargottama_amplification=0.0`, `neechabhanga_modifier=1.0`, `cancellation_modifier=1.0`, `verification_pass_status="documented_approximation"` `[code]`.
- **The formula in use is `salience_formula_v2`, not v1** (the INDEX quotes the v1 limitation): `SalienceInputsV2` makes `ashtakavarga_bindus`, `vargottama_amplification`, `neechabhanga_modifier`, `cancellation_modifier` and `argala_modifier` Optional ("None means NO DETECTOR RAN ... the caller stores None rather than the identity"), but `orb_tightness`, `shadbala_norm` and `dignity_score` are non-Optional floats with neutral defaults (`bodha_writers/formulas.py:571-606`, formula `:609-690`). So passing None is already supported for four of the seven constant terms; the INDEX's "NULL cannot be passed into `math.log`" describes v1, which only the 45 D9-cross-check rows still carry (Q-L2-04) `[code][db: salience_formula_version]`.
- Stored (canonical chart, 149 satellite rows): `salience_inputs_complete = false` and `verification_pass_status = documented_approximation` on all 149; `salience_pctl_in_class` null on all 149; `dignity_score` exactly 0.5, `shadbala_norm` exactly 1.0, `orb_tightness` exactly 1.0 on all 149; `computed_salience` min 0.243, median 0.378, max 0.536 against `bo_laksana` median 0.465, p99 1.493, max 2.097 `[db]`. So each row already says "not complete" and "approximation"; what reads as measured is the numeric columns.
- **`orb_tightness` is 1.0 on all 50,678 canonical MSR rows (one distinct value), including every `bo_laksana` row** `[db]`: it is a factor in the product that never varies anywhere in the table, not only in the satellites.
- Where an L1 authority exists and L2 already reads it: `bo_laksana` builds a per-graha strength lookup (`_build_strength_lookup`, `bo_laksana.py:906`; the D9 site reads it at `:2972`) and its stored `shadbala_norm` varies from 0.84 to 1.79; `graha_shadbala_total.rupa` is the L1 strength authority the UCD view uses (`bo_samvada.py` view SQL) `[code][db]`. How `bo_laksana` sources its dignity score on the main path was not traced.
- Coupling: the L3 sheet (Q-L3-01) defers its option 3 to this ruling `[brief]`.

**Recommendation.** Split by term. (1) `ashtakavarga_bindus`, `vargottama_amplification`, `neechabhanga_modifier`, `cancellation_modifier`: pass None (option 2) where the emitter computes nothing; v2 already treats None as the identity and stores None; no formula change. (2) `shadbala_norm` and `dignity_score`: option 3 where the satellite's subject is a graha, reading the same L1 sources `bo_laksana` reads (the five emitters' per-row subjects were not individually verified; `bo_nakshatra_semantic` and `bo_sudarshana` store 45 rows = 9 grahas x 5 ayanamshas); for lagna-point satellites (`bo_arudha` 25, `bo_special_lagna` 20) there is no per-graha strength, so make the two fields Optional in `SalienceInputsV2` (a small formula-module change, version bump) rather than invent a default. (3) `orb_tightness`: ratify as a neutral factor "not applicable to non-aspect signals" with a decision id (option 1) and record that it is constant table-wide; compute it only where an L1 orb fact exists (not checked here). Reason: option 1 alone leaves 149 rows whose numbers read as measured; the stored flag already discloses it, so the remaining honesty gap is small and the L1 sources exist; CLAUDE.md §N.7 items 3 and 6.

**Effect.**
- Option 1 for all: no row changes; decision ids added; no rebuild. (The honest minimum; leaves the numeric columns reading as measured.)
- Option 2 (None for the four terms): satellite rows' stored `ashtakavarga_bindus`-derived columns and the `vargottama/neechabhanga/cancellation` columns change from neutral numbers to NULL; `computed_salience` is unchanged (None contributes its identity); rebuild of the five satellites; readers unchanged.
- Option 3 (shadbala, dignity): `computed_salience` changes on up to 149 canonical rows (and the same count on each other chart); downstream the rebuild chain is the five satellites, then `bo_laksana_rerank` (centrality), `bo_karanajala`/`bo_sangati`/`bo_anveshana` (salience-weighted), `bo_chart_gestalt`, `bo_pramana_mapa`, `bo_samvada` `[brief]`; under the retired ordering rule (A-2) no Kāla/Phala ordering is required, but L3 `ka_yojaka` and Phala readers see new salience on the next build. Output change: (R).
- Mixed (recommended): the union of options 2 and 3 on one rebuild of the five satellites and their dependents.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** CHANGED. The split is accepted, but `orb_tightness` is NOT ratified as 1.0: it becomes Optional with `shadbala_norm` and `dignity_score`; None is stored wherever no orb was computed (identity in the product, salience unchanged); for `bo_laksana` aspect-class signals read an L1 orb fact if one exists, if none exists None plus one Track I item; Lagna-point satellites store None for shadbala and dignity; graha-subject satellites read L1 (option 3); ONE formula version bump covers all three. **Facts found while recording (read-only):** L1 stores an `orb_deg` fact only for conjunctions (`conjunction_per_varga` 115 rows, `conjunction_within_orb` 2 rows in Lahiri) and none was found with 'orb' in the key for aspect categories, so the aspect case is today the 'none exists' branch (TI-L2-21); the columns `orb_tightness`, `shadbala_norm`, `dignity_score` are nullable, `deterministic_strength` is NOT NULL (it is the product, and None terms contribute their identity). Output change (R); batched. TI-L2-21, TI-L2-27.

---

### Q-L2-04 — `bo_laksana` FD-1: the literal 2 and the hand-set salience constants

**Question.** On the three emit sites that store `source_corroboration_count_by_text = 2` without computing it, should the column be NULL; and are the hand-set salience values of the D9 cross-check (0.6 / 1.2 / 1.6 / 1.8 / 2.0) and the divergence signal (1.2) acceptable design defaults?

**Facts.**
- Constant-2 sites: `bo_laksana.py:1423` (varga-divergence), `:2969` (D1/D9 cross-check), `bodha_writers/bhavat_bhavam_amplifier.py:345`; the main path computes the count from `classical_sources_jsonb` and the satellites store NULL (`arudha_emitter.py:163`) `[code]`. The column is nullable `[db: information_schema]`.
- Stored on the canonical chart: 45 D9 cross-check rows and 9 divergence rows carry the 2; no `bhavat_bhavam_amplifier` row exists on this chart; the `varga_pattern` class has 1,355 NULL and 45 value-2 rows `[db]`. (14 `yoga_label` rows also read 2; their source was not traced and is not one of these three sites.) The affected canonical rows are therefore 54.
- Hand-set salience: `salience_base` 1.6 / 1.8 / 1.6 / 2.0 / 1.2 / 0.6 by classification (`bo_laksana.py:2855-2895`); divergence `round(1.2 * 1.0, 6)` (`:1457`); `computed_salience` is set directly, `salience_inputs_complete = false` (`:1460`, `:3008`) `[code]`; the INDEX states these do not call the formula (`[brief]`; I confirmed the hand-set assignments, not the absence of every call). Stored range of the 45 D9 rows: 0.6 to 2.0 (median 0.6); the whole `bo_laksana` table spans 0.0 to 2.097 (p99 1.493), so the hand-set values do not sit outside the table's scale `[db]`.
- **Version stamp (found in verification, not in the brief):** the 45 D9 cross-check rows carry `salience_formula_version = 'v1.0'` and the 9 divergence rows `v2.0`, while their salience is hand-set and neither formula was called for them; the other 50,484 `bo_laksana` rows read `v2.0` `[db]`. A version stamp that names a formula that did not produce the value is the CLAUDE.md §N.8 pattern (a flag without the detector behind it).
- The only reader of the column outside the writers is the served `query_signals.ts` `[code: grep]`; no Python consumer reads it.

**Recommendation.** (1) Yes, NULL on the three constant sites (a value with no computation behind it, §N.7 item 6); the salience values do not change, so nothing downstream moves except the served field on 54 canonical rows. (2) Ratify the classification salience table (0.6 / 1.2 / 1.6 / 1.8 / 2.0) as a named design table with a decision id (option 1): these are class-level weights, not stand-ins for a missing measurement; but (3) correct the stamp: store the formula version only where the formula ran (NULL, or a named `classification_weight_v1`, if the column's vocabulary allows; the column's constraints were not read). Reason: NULL is cheap and honest; the table is a design choice that needs only a name.

**Effect.**
- (1) NULL: the column changes on 54 canonical rows (and the equivalent rows on other charts); `computed_salience` unchanged; rebuild of `bo_laksana` (the 50,529-row writer, 24 direct dependents) which cannot be justified alone: bundle it with the post-#2607 rebuild this layer needs anyway (fact 1). Ratify instead: no change.
- (2) Ratify the table: declaration only. Replace by the formula: rejected here (changes all 54 saliences and invents inputs).
- (3) Stamp correction: the stamp changes on 54 rows, same rebuild.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended, with notes: the stamp is the named `classification_weight_v1` if the column allows it, else NULL. **Found while recording:** `salience_formula_version` is plain `text` and the only CHECK on `bodha_msr_signals` is `bodha_msr_signals_producer_asset_check` (on `producer_asset_id`), so the named stamp is allowed and no ALTER is needed (the table is owned by `data_plane_l2_owner`, so the amjis_app ALTER pre-approval would not have covered it anyway). Trace the 14 `yoga_label` rows that read 2 and treat them like the three sites if they are uncomputed. The class-weight table is (R) and goes on the J1 reviewers' list BY NAME. Batched. TI-L2-18, TI-L2-22, TI-L2-28.

---

### Q-L2-05 — `bo_anveshana` FD-1 / FD-2: stored confidence, fragility, falsifier, and the acharya claim

**Question.** Should the stored `confidence`, `ayanamsha_fragility` and `falsifier` be NULL until earned, and must `why_an_acharya_misses_it` stop asserting what an acharya would miss?

**Facts.**
- Every discovery stores `epistemic_jsonb = {"confidence": round(min(consequence + 0.1, 1.0), 3), "ayanamsha_fragility": "low"}` and a fixed `falsifier_jsonb` (`bo_anveshana.py:416-430`) `[code]`. On the canonical chart: 1,161 discoveries; `ayanamsha_fragility` has one distinct value (`low`) on 1,161; `confidence` equals `min(consequence_score + 0.1, 1)` on 1,161 of 1,161; the falsifier sentence has one distinct value on 1,161; classes: `distributional_anomaly` 1,127, `embedding_outlier` 34 (the non-obviousness and broker primitives produced no rows on this chart) `[db]`.
- `why_an_acharya_misses_it` is composed at four sites (`:509`, `:585`, `:648`, `:732`): "falls below acharya's attentional threshold", "invisible to pattern-matching", "easy to miss when chart is read holistically", and a broker sentence that states a graph property. The stored strings repeat the same template on all rows of a class (top four are the `ga_structural` anomaly sentence, differing only in the σ value) `[code][db]`.
- No documented attention threshold exists for "an acharya's attentional threshold" in the code or the briefs `[code]`. The writer stores `calibration_hook = "empty - L4/L5 fill"`, which is the honest empty `[code]`.
- Consumers: `bo_chart_gestalt`, `bo_pramana_mapa`, `ph_nimitta`; served by `query_discoveries.ts` (`epistemic_jsonb` and `falsifier_jsonb` are dark by default) `[brief]`.

**Recommendation.** FD-1: yes, store NULL (or omit the keys) for `confidence` and `ayanamsha_fragility`, and give the falsifier either a per-class text naming the L3/L4 outcome class it will be compared to or NULL, until a measured function with a decision id exists; keep `calibration_hook` as is. FD-2: yes, keep the numeric restatement and drop or define the attention claim (for example "salience percentile below X, stated in the string"); the broker sentence already states a derivable graph property and may stay. Reason: `confidence = consequence + 0.1` and a constant `low` are invented judgments standing in for "not computed" (§N.7 item 6, §N.8); a sentence about an acharya's attention has no cited fact behind it (§N.7 items 1 and 6); the data row is otherwise sound (the references resolve).

**Effect.**
- FD-1 yes: `epistemic_jsonb` and `falsifier_jsonb` change on every discovery row (1,161 canonical); rebuild `bo_anveshana`, then `bo_chart_gestalt`, `bo_pramana_mapa` (its discovery-grounding detector reads `constituent_refs_jsonb` and `reasoning_chain_jsonb`, not these columns) and `ph_nimitta`; output change (R). FD-1 no: the confidence reads as a measured 0.1-1.0 value on every row.
- FD-2 yes: the text of `why_an_acharya_misses_it` changes on all rows; same rebuild; a golden-value test (CF-14) pins the new strings. FD-2 no: an ungrounded claim stays in the engine's headline column.
- Both ride one `bo_anveshana` rebuild.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended: `confidence`, `ayanamsha_fragility` and `falsifier` are NULL now (FD-2 as recommended). Computing fragility (does the discovery hold in all five ayanamshas) is a post-J1 improvement item. Batched. TI-L2-25, TI-L2-29.

---

### Q-L2-06 — `bo_bimba` FD-1: yoga/dosha node names and the collision measurement

**Question.** Fix only the display name of yoga/dosha nodes (no identity change), and is the measured collision of distinct yogas onto one node subject also in scope?

**Facts.**
- `_yoga_config_name` reads `fact_value_text` first, then `yoga_name`, `dosha_name`, `name`, `label`, then `signal_type_id` (`bo_bimba.py:252-258`); `yoga_node_subject` slugs that same name (`:261-271`); the node label is the name (`:505`), the citation is `"{Class} node: {name}"` (`:523`); signals with the same `(class, subject)` are reduced to the single highest-salience one (`yoga_best`, `:467-486`) `[code]`.
- **Collision measurement (requested by the brief; I ran it read-only):** the canonical chart holds 100 yoga/dosha signals (74 yoga, 26 dosha; 20 per ayanamsha) and 85 yoga/dosha nodes (69 + 16; 17 per ayanamsha). Per ayanamsha 15 yoga signals map to 14 nodes and 5 dosha signals to 3 nodes (4 in `surya_siddhanta_classical`, 6 signals), so 3 signals per ayanamsha (15 across five) have no node of their own `[db]`.
- The collisions: `yoga:false` merges two different signal types, `graha_yoga_karaka_flag:is_yoga_karaka` and `panchanga_yoga:inauspicious_flag` (10 signals, 2 per ayanamsha); `dosha:afflicted` and `dosha:unafflicted` each merge the 2 per-ayanamsha `kendradhipati_dosha` signals into one node `[db]`.
- Names that are statuses or identifiers, not names: of 18 distinct node subjects per chart, 7 are non-names: `true`, `false`, `1984-02-05T19:29:13+00:00`, `panchanga_yoga:number`, `panchanga_special_yoga_combinations:constituent_facts_jsonb_atomic`, `afflicted`, `unafflicted`; the other 11 are real catalogue names (for example Gola Yoga, Manglik Dosha, Kemadruma Dosha, Shiva, panchaka) `[db]`. The 7 appear in `node_label_human` and `citation_human` verbatim ("Yoga node: true").
- Node ids are deterministic functions of `(chart, ayanamsha, node_type, node_subject)` (`bodha_cgm_node_identity()`, migration 714), so a `node_subject` change re-keys the node and the `yoga_member` edges `bo_karanajala` wires to it `[brief][code]`.

**Recommendation.** Approve the display-name fix now (FD-1 as written: a label from `yoga_name`/`dosha_name`/the catalogue name for `signal_type_id`, never `fact_value_text`; identity input unchanged so no id moves), and rule separately that the collision is a real identity defect to be fixed by an identity change: the proper identity is `(signal_type_id, configuration key)`, not a status value; an identity change is a separate (R) SS ruling with its own rebuild of `bo_bimba`, `bo_karanajala` and the readers of `yoga_node_subject`. Reason: the display fix is safe and removes the visible garbage; the collision silently drops 15 signals' nodes and merges two different yogas into `yoga:false`, but fixing it moves ids.

**Effect.**
- Display fix only: `node_label_human` and `citation_human` change on the 7 non-name subjects per ayanamsha (about 35 node rows on the canonical chart); no id, edge or downstream key moves; rebuild `bo_bimba` (255 rows, idempotent), then `bo_karanajala` rewrites centrality on its next run; readers `traverse_chart_graph.ts`, `graha_portrait.ts`. Output change: (R).
- Identity fix as well: node ids and edge ids change for the affected nodes; `bo_karanajala` and every downstream asset keyed on those ids (`bo_cgm_motifs`, `bo_cgm_paths`, `bo_yantra_mechanism`, ...) rebuild; 15 currently dropped signals gain nodes; output change on node counts (85 -> up to 100 yoga/dosha nodes on the canonical chart). Defer: the collision stays.
- Neither: status text keeps naming nodes.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** CHANGED. Do the name fix AND the identity fix TOGETHER in the one `bo_bimba` rebuild (identity = `signal_type_id` + configuration key). BEFORE coding, classify the 7 non-name subjects: a real yoga with a bad name gets its catalogue name; a flag, timestamp or number that is not a yoga (for example `is_yoga_karaka = false`, `inauspicious_flag = false`) gets NO yoga node. Produce that classification and the id-change list as one short design REVIEW document for SS (TI-L2-19). The Q-L2-15 (2) node move rides the same change. Input to that REVIEW (my read of the live signal types behind the 7 subjects, not a classification): `true` is `panchanga_special_yoga_combinations:active_at_birth_flag`; `false` is `graha_yoga_karaka_flag:is_yoga_karaka` and `panchanga_yoga:inauspicious_flag`; the timestamp is `panchanga_yoga:end_iso`; `panchanga_yoga:number` and `panchanga_special_yoga_combinations:constituent_facts_jsonb_atomic` are their own signal types; `afflicted` and `unafflicted` both come from `kendradhipati_dosha:doshas_kendradhipati` (a dosha status, two signals per ayanamsha). Output change (R); batched. TI-L2-19, TI-L2-30.

---

### Q-L2-07 — CF-15: declared `depends_on` edges versus what each writer reads

**Question.** May the two deferred edges (`bo_laksana -> ga_yoga`, `bo_upaya -> bo_bimba`) be added; may `bo_pratijna`'s two declared-but-unread L2 edges be replaced by direct L1 edges after a per-category audit; and keep `bo_samvada`'s five view-lineage edges?

**Facts.**
- `bo_laksana.py:2713` (and a second read at `:2769`) reads `ga_yoga_firings` (neecha-bhanga lookup) with no `ga_yoga` edge; `bo_upaya.py:578` joins `bodha_cgm_nodes` with no `bo_bimba` edge `[code]` (the brief cites `:2712` and `:575`, one to three lines earlier). Live `depends_on`: `bo_laksana {bg_rules, ga_positions, ga_strength, ga_sensitive, ga_panchanga, ga_sade_sati, ga_structural, ga_nakshatra, ga_condition, ga_vargas, ga_vichara}`; `bo_upaya {bo_laksana, bo_sangati, ga_structural, ga_dashas, bo_cgm_motifs}`; `ga_yoga {ga_structural, ga_dashas}`; `bo_bimba {bo_laksana, the five satellites}` `[db]`. Neither added edge makes a cycle: `ga_yoga` depends on no `bo_*`; `bo_bimba` does not depend on `bo_upaya`. `ga_yoga` and `bo_bimba` are `lit` on the canonical chart (2026-09-08, 2026-09-11) `[db]`.
- `bo_pratijna` declares `{bo_laksana, bo_sangati, ga_vargas}` `[db]` and the writer states it reads no `bodha_msr_signals` (docstring: "this engine never reads `bodha_msr_signals` at all"; `supporting_signal_ids` always NULL) (`bo_pratijna.py:125-140`) `[code]`. It reads `chart_divisionals`, `chart_facts`, `chart_fact_identity` and `brahma_reference_planets` exclusively through `ChartReaderV4` (`bo_pratijna.py:15`, `:153-154`) `[code]`.
- First-pass producer map for the categories `ChartReaderV4` reads (`brahmagyan/chart_reader_v4.py`): `varga_position`, `varga_house_occupant`, `varga_house_lord` are `chart_divisionals` columns written by `ga_vargas` (migration 1210 added that edge); `bhava_cusps` is `ga_positions` (`source_calculation pyjhora_adapter.houses...`, 72 rows); `special_lagna` and `karaka_chara_position` are `ga_sensitive` (`pyjhora_adapter.sensitive`, 49 and 105 rows); `graha_dignity_per_varga`, `aspect_parashari_given`, `aspect_parashari_per_varga`, `upapada_lagna` are `ga_structural` (`ga_structural.*` / `pyjhora_adapter.aspect_parashari`, 270 / 19 / 570 / 2 rows) `[db: chart_facts.source_calculation][code]`. `chart_fact_identity` and `brahma_reference_planets` are two further reads **not in the brief's category list**; their producers were not traced `[unverified]`.
- `chart_facts` is a SOFT shared table in `dag_edge_guard` (any producer in the closure satisfies it), so a rev-2 PASS after removing the L2 edges would not prove the ordering `[brief]`.
- `bo_pratijna` is `stale` on the canonical chart (built 2026-09-09); its latest error on record is a `BLOCKED` cascade from `bo_laksana`/`bo_sangati` (2026-08-06) `[db][brief]`. The held `ph_nimitta -> bo_pratijna` edge was to travel in "migration 1211" `[brief]`, a number now used by an unrelated migration (fact 3).
- Frozen manifests: a `depends_on` edit makes `assertManifestMatchesRegistryIdentity` throw (`plan_adaptation_required`) for the edited asset's frozen manifest; 1210 already passed this for four L2 rows `[brief]`.

**Recommendation.** (1) Yes: add `bo_laksana -> ga_yoga` and `bo_upaya -> bo_bimba` in one surgical, append-only, guarded migration (the shape of 1210), numbered max+1 across both migration directories at execution (not 1211), and verified by production structure afterwards. (2) Yes to replacing `bo_pratijna`'s two L2 edges, but only after the per-category audit is closed: from the first-pass map the replacement set is `ga_vargas` (present), `ga_positions`, `ga_structural` and `ga_sensitive`, plus whatever produces `chart_fact_identity` and `brahma_reference_planets`; remove `bo_laksana` and `bo_sangati` only in the same migration that adds the direct edges, so ordering is never lost. (3) Keep `bo_samvada`'s five edges (they are the view's lineage and freshness gating). (4) Sequence the held `ph_nimitta -> bo_pratijna` edge after `bo_pratijna` is lit and fresh. Reason: the first two edges are acyclic by construction and fix the two remaining Build.dag FAILs; the pratijna replacement is the only edit that could lose an ordering, so it must follow the audit, as the brief says.

**Effect.**
- (1) Add: DAG gains two edges; `compute_upstream_hash` for `bo_laksana` and `bo_upaya` changes once (a one-time rebuild signal at next dispatch); the two frozen manifests go to `plan_adaptation_required`; no data row; Build.dag reads-match reads PASS for both. Not adding: two rev-2 FAILs stay.
- (2) Replace: pratijna's upstream hash changes once; its blocked-cascade history stops; frozen t1 manifest stale. Not replacing: the writer keeps waiting on two assets it does not read. Replacing before the audit: ordering could silently weaken.
- (3) Keep the five samvada edges: no change; remove them: the view loses freshness gating.
- (4) Held edge: needs a new migration number; waits.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended. The two edges may ride the held-edges migration (1216, branch TI-edges-002) if it is still unapplied, else max+1. The `bo_pratijna` re-point only after the two untraced reads (`chart_fact_identity`, `brahma_reference_planets`) are traced. **Found while recording:** `origin/main` has no migration above 1214 and the only TI-edges branch on origin is TI-edges-001 (no migration beyond 1210), so 1216 / TI-edges-002 could not be verified from here: confirm at execution. TI-L2-05, TI-L2-06.

---

### Q-L2-08 — `bo_grounding`: integrate, keep as substrate, or retire

**Question.** Integrate `bo_grounding` (connect `bodha_grounding_matches` to the grounding spine and the attribution catalogue, then promote it to CURRENT), keep it as an unconnected substrate, or retire it; and is adjudication #1726 (the `sruti` tier definition) still open?

**Facts.**
- 50,731 rows on the canonical chart, `state = lit` (built 2026-09-12), registry `DRAFT`, floor 0 `[db]`. Readers: the table is named only by the writer, its idempotency helper, its test and migrations (grep over py/ts/tsx and migrations); no capability selects it `[code]`.
- Tier distribution (canonical chart): `msr_signal` rows: `pratyaksa` 50,489, `yukti` 189; `yoga_dosha_firing` rows: `sruti` 29 (all `citation_granularity = page_column`), `yukti` 16, `pratyaksa` 8 `[db]`. So the earned tiers (`sruti` + `yukti`) are 234 of 50,731 rows (0.46%); `pratyaksa` is the honest default carrying no citation.
- The design is a native ruling: D-NATIVE-09 (2026-09-07) fixed the detector order sruti -> yukti -> pratyaksa with the earning evidence stored per row; D-NATIVE-11 made `bo_grounding` a SUPPORTING writer outside the 128-asset denominator (`briefs/nirmana/CAMPAIGN_STATE.md:398-399`, `sessions/L2_STATE.md` rows 810 and 820) `[code]`.
- #1726: `sutravali_rules.verse_ref` is page:column for the whole corpus (3,002 of 3,002), so a `chapter_verse` claim would be fabricated precision; the matcher now stores `page_column` (`L2_STATE.md` row 820: "the exact fabricated-precision claim #1726 condition 3 forbids ... fixed shape-derived") `[code]`. The adjudication store itself is not in the repository; whether #1726 is formally closed was **not verifiable**. The repository shows its condition 3 honoured in code and data (29 `sruti` rows all `page_column`).
- Matcher caveat the writer documents: `sutravali_rules.yoga_canonical_id` is unreliable alone (2,994 of 3,002 rules untagged), so the matcher verifies structurally (`bodha_writers/grounding_matcher.py:1-30`) `[code]`.

**Recommendation.** Integrate, narrowly and layered: add the tier, granularity and evidence to the grounding spine (`resolver.ts`) and a facet or capability that serves earned tiers (`sruti`, `yukti`) as the confirmed layer and `pratyaksa` as the default, catalogue-only layer with its own count (CLAUDE.md §N.6 item 1: never present a default tier as a confirmed finding); then set `catalog_status` to CURRENT. Do not retire (it discards a native ruling, D-NATIVE-09). Treat #1726 as satisfied in practice by the `page_column` granularity and ask the adjudication owner to confirm. Reason: the asset is built, deterministic and idempotent with no consumer; the only work left is connection; the measured tier mix shows the served surface must not read the row count as grounded claims.

**Effect.**
- (a) Integrate: new served fields or a capability (served-surface change, (R)); registry `catalog_status` edit (the asset is not frozen, so no manifest effect); no rebuild of the table; Dens/Reach move from "no consumer" to measured.
- (b) Keep as substrate: no change; `unresolved` until a consumer exists; 50,731 rows keep no reader.
- (c) Retire: removes the asset and table (a destructive registry/data decision), discards D-NATIVE-09.

**Citation.** Not classical (a matcher over `sutravali_rules`, whose own citations are page:column). citation: n/a.

**RULING (SS, N-59, 2026-10-01).** CHANGED. `bo_grounding` stays a declared substrate for now (outside the denominator per D-NATIVE-11, no consumer, the reason stated in the declaration); no retire; no new served surface before J1; integration is a post-J1 item. Adjudication #1726 is not ours to close: record 'satisfied in practice'. TI-L2-07, TI-L2-26.

---

### Q-L2-09 — `bo_samvada`: confirm qualify, the build record, and the later consolidation

**Question.** Confirm `qualify` (a passive boundary over the `vw_chart_digest` view with a real chart-scoped `count_sql`), say which build record a passive boundary should show (the saved record says 1, the code returns 0), and decide whether to consolidate the view into a versioned projection later.

**Facts.**
- The writer is a no-op: `rows_inserted=0, rows_skipped=1`, note "legacy serving projection preserved; no per-chart DDL" (`bo_samvada.py:141-160`) `[code]`. Its module docstring still says "rows_written = 1 (the VIEW itself counts as 1 object created)" (`:40`) and "count_sql already reads `SELECT count(*) FROM vw_chart_digest WHERE chart_id = ...`" (`:31-35`), both stale `[code]`.
- Live registry: `count_sql = SELECT 0 AS count`, `target_floor 0`, `asset_kind data`, `natural_key_partition` blank, `storage_type postgres_view`; the seed says `count(*) FROM vw_chart_digest WHERE chart_id = $1`, floor 5 (`asset_registry_seed.ts:1832-1850`); declarations say kind `view` `[db][code]`. Last build record `rows_written = 1` (2026-09-11) `[db]`.
- `vw_chart_digest` returns 5 rows per chart on all three charts `[db]`, so a chart-scoped `count(*)` reads 5, the seed value. The live view definition already matches the writer's corrected SQL: `weakest_graha` comes from L1 `graha_shadbala_total.rupa` (live value Venus on all five ayanamshas) `[db: pg_get_viewdef]`; `platform/src/lib/vidhi/cr_status.ts:26-30` still says the raw view "STILL returns Mercury" (verified live 2026-07-21), now stale `[code][db]`.
- The view has a real consumer: `query_ucd.ts` reads it (`cr_status.ts:17-30` also records a serve-side `weakest_graha` override in that module; whether it is still there was not re-read) `[code]`.
- L0 Q1 `[brief]`: a rerun with `rows_written = 0` reads Build.completion PASS only if the writer declares the changed-rows convention and count_integrity passes on populated rows.

**Recommendation.** Confirm qualify. (1) Restore a real chart-scoped `count_sql` (`SELECT count(*) FROM vw_chart_digest WHERE chart_id = $1`, reads 5) with floor 5 and `natural_key_partition` stated as "none: view"; (2) the intended build record is 0 (the truthful value for a writer that creates nothing), declared under the L0 Q1 changed-rows convention so completion is proven by the count; (3) correct the docstring and the `cr_status.ts` comment; (4) do not consolidate into a versioned projection now: the view has a consumer and a later integration packet already exists as the stated route. Reason: the count must be able to read false (a constant 0 beside a floor of 0 cannot, §N.8).

**Effect.**
- (1)+(2) Yes: one registry migration (rides CF-03), docstring and comment edits, a declaration; no data change; no rebuild; Build.completion reads from a count that can fail. No: `count_sql = 0` stays a number that cannot read false.
- (3) Consolidate later: a separate DDL packet and a consumer migration. Consolidate now: unrequested global DDL, rejected here.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended. Registry, docstring and comment edits: no rebuild, pre-approved now. TI-L2-08.

---

### Q-L2-10 — CF-13: the R243 annotation after F-3

**Question.** Is R243's chart list or W2-3_REVIEW's authoritative per asset, and is the annotation "refused via `assert_l2_msr_delete_safe` on <charts>" reworded now that the keys are gone; is the F-3 order guard wired into the L2 rebuild plan?

**Facts.** The six `Idem.pattern` PASSes are annotated with the verbatim R243 text and a per-asset chart list (R243: `1c826d5a, cb73cd3d` for five assets, `1c826d5a` for `bo_laksana`; W2-3_REVIEW differs for four) (`L2_LAYER_INSTANCE_v1_0.md:1011-1037`) `[brief]`. By A-2 the live database has no foreign key onto `bodha_msr_signals`, so the function has nothing to refuse on any chart `[db]`; the annotation's "refused" clause is therefore no longer true on any chart, which makes the per-asset chart-list dispute moot. The brief's own inference that the annotation "would lapse once F-3 drops the keys" is confirmed by the structure. The control that replaced refusal is `msr_dangling_signal_refs.py`; the ordering guard retired with A-2.

**Recommendation.** Reword once and drop the per-asset lists: `chart_scope: all charts; no cross-layer cascade (kala_* keys dropped by 1214; bodha_contradictions and bodha_signal_embeddings keys dropped at the owner path; deletes of those two are explicit in _idempotency.py); control: msr_dangling_signal_refs.py post-wave`. Keep `assert_l2_msr_delete_safe` as is (admitted-context check), and do not wire the order guard in as a gate. Reason: an annotation that states a refusal the system no longer performs is a claim without a detector (§N.8).

**Effect.** (a) Reword: declaration/annotation text only; the six PASS cells read the new text; no data, registry or rebuild. (b) Keep the old text: a false clause in every emitted Idem PASS for the six assets. (c) Wire the order guard anyway: allowed (it is harmless), an extra plan check with no stated purpose after A-2.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended. Declaration text: no rebuild, pre-approved now. TI-L2-09.

---

### Q-L2-11 — `bo_upaya`: lift the "PASS withheld" annotation?

**Question.** Lift the "PASS withheld" annotation on `bo_upaya` emits now that #2773 is on main, or only after the live rebuild (plan item B.U) proves it?

**Facts.** #2773 (`9fecaecda`, 2026-09-30) restored the legacy windowed-prescriptions delete: `replace_prior_rm_dasha_windowed(conn, chart_id, aya)` at `bo_upaya.py:1952`, with `test_bo_upaya_source_order.py` `[code]`. The live `bo_upaya` rows were built 2026-09-09 (`stale`), before both #2607 (a 407-line rewrite of this writer) and #2773 `[db]`. The register's "5 referencing rows" on the canonical chart was never re-measured: the table `bodha_rm_dasha_windowed_prescriptions` is unreadable to `suvarna_reader` `[db]`.

**Recommendation.** Lift only after B.U proves it live. Reason: the PASS rests on a code path that has not run in production, and the one measurement that would show the risk (the referencing rows) cannot be read; §N.8 asks what code path would have to run and fail for the signal to read false.

**Effect.** (a) Wait for B.U: no change now; the annotation lifts on a clean live rebuild (a `bo_upaya` rebuild; four direct dependents re-run: `bo_pramana_mapa`, `bo_samvada`, `ka_kshetra`, `ph_pratikara` `[brief]`). (b) Lift now: the PASS is earned in code only; a failure at the first live rebuild would contradict an emitted PASS.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended: lift only after a live rebuild proves it; that proof is now the one coherent L2 rebuild (B.U folds into it), and the annotation is read after it. TI-L2-24.

---

### Q-L2-12 — CF-03: registry correction batch (seed alignment direction and the two 60,000 floors)

**Question.** May the seed literals (`catalog_status`, volume formulas, count scopes, floors) be aligned to the live values (not the reverse), and the two 60,000 floors refreshed only after a coherent rebuild?

**Facts** (live registry re-read; seed read at `platform/scripts/seed/asset_registry_seed.ts`) `[db][code]`:
- (a) `bo_samvada`: live `count_sql = SELECT 0 AS count`, floor 0; seed `count(*) FROM vw_chart_digest WHERE chart_id = $1`, floor 5.
- (b) `natural_key_partition` blank on exactly `bo_anveshana`, `bo_karanajala`, `bo_samvada`; stated on the other 20.
- (c) `bo_pratijna`: live floor 0 and `AYANAMSHAS * EVENT_CLASSES`; seed floor 110, `EVENT_CLASSES * AYANAMSHAS` with `EVENT_CLASSES: 22`; live rows 135 = 5 x 27.
- (d) `bo_bimba`, `bo_samskara` and `bo_upaya` carry `storage_type = pgvector`; only `bo_bimba`'s is contradicted by data: `bodha_cgm_nodes.node_embedding_vec` is NULL on all 1,101 table-wide nodes (`bo_samskara` fills 50,678 embedding rows; `bo_upaya`'s vector column was not checked).
- (e) Seed `catalog_status = DRAFT` for seven assets (`bo_sudarshana`, `bo_nakshatra_semantic`, `bo_yantra_mechanism`, `bo_arudha`, `bo_laksana_rerank`, `bo_special_lagna`, `bo_vargottama_dhana`) while live reads CURRENT; the only live DRAFT is `bo_grounding`.
- (g) Floors seed / live / achieved (canonical chart): `bo_laksana` 66,738 / 60,000 / 50,529; `bo_samskara` 66,738 / 60,000 / 50,678; `bo_anveshana` 5,770 / 500 / 4,437; `bo_sangati` 84 / 70 / 475; `bo_pratijna` 110 / 0 / 135; `bo_cgm_paths` 5 / 9 / 45; `bo_chart_gestalt` 5 / 1 / 5; `bo_cdlm_summary` 5 / 1 / 5; `bo_samvada` 5 / 0 / 5.
- (f), (h): not re-verified here `[brief]`.
- CLAUDE.md §N.4: floors are aspirational; set a floor to the achieved count after a build; never fabricate rows to meet one. A floor edit does not trip the frozen-manifest check (only `count_sql`, `natural_key_partition`, `catalog_status`, `target_table`, `integrity_check_sql` do) `[brief]`.
- The achieved counts predate the code on main (fact 1): 23 writers changed after the builds that produced them.

**Recommendation.** Yes: align the seed TO the live values (a re-seed never rewrites an existing row, so this only stops a fresh bootstrap from re-introducing stale values) for (c), (e), the formulas and the count scopes; make the one surgical migration for the registry-side items (a) `bo_samvada` (with Q-L2-09), (b) the three partitions, (d) the `storage_type`/description of `bo_bimba`. Do not refresh the two 60,000 floors now: refresh both (and the others) to the achieved counts after the coherent rebuild; they are information only. Reason: the achieved counts are not predictors, since main's code is not the code that built them and several rulings here change counts (Q-L2-06, Q-L2-14).

**Effect.** (a) Seed alignment: a seed edit, no live row changes. Migration: registry rows only (three assets get `natural_key_partition`, `bo_samvada` gets `count_sql`/floor/`asset_kind`, `bo_bimba` loses `pgvector`); the cockpit counts of the named assets change; frozen manifests of the named assets need `evidence_refresh_required`; no rebuild. (b) Floors now: two numbers that a later rebuild would re-state. (c) Reverse direction (live to seed): would undo cockpit-truth work.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended. The registry migration and seed alignment are pre-approved now; the floors are restated after the rebuild, not before. TI-L2-10, TI-L2-24.

---

### Q-L2-13 — CF-06: is `path_label_human` narration; is `embedding_input_summary` narration

**Question.** Is `path_label_human` (a label that states "self-ruling / final dispositor") narration or a structural label; is `embedding_input_summary` narration or an embedding input outside the Narr rule?

**Facts.**
- The declarations file states SS's rule: a composed string that states a computed value is narration; "verbalising an L1 fact value states a computed value"; "a citation that is only an identity (an entity name ...) is not narration" (`platform/scripts/governance/asset_declarations.json`, `description`) `[code]`.
- `path_label_human` is built as `"{graha} (self-ruling / final dispositor)"` for a self-ruling start and `"A -> B -> ... (final dispositor)"` otherwise (`bo_cgm_paths.py:166-200`); live labels read "Jupiter (self-ruling / final dispositor)", "Venus -> Jupiter (final dispositor)" `[code][db]`. The suffix states a derived classification (the chain ends at a self-ruling graha). **Observation found while reading:** `_is_self_ruling` re-derives "occupies a sign it rules" from a wrapper-local table `SELF_RULING_PAIRS` (`:77-85`, `:130-145`) rather than reading an L1 dignity fact: CLAUDE.md §N.7 item 3 (no wrapper-local constant may shadow an L1-computed value) `[code]`.
- `embedding_input_summary` is `"{signal_type_class} | {tradition} | {signal_type_id} | fact_key=... | fact_value_text=... | graha=... | domains=..."` (`bo_samskara.py:95-111`); live example: `karaka_alignment | jaimini | karaka_bhava_concordance:concordance_value | fact_key=concordance_value | fact_value_text=friendly_reverse | domains=...` `[code][db]`. It verbalises L1 fact values, and it is stored in a column.

**Recommendation.** Both are narration: declare `path_label_human` and `embedding_input_summary` in `prose_fields` with writer evidence, and add a golden-value test for each (a self-ruling and a chained case; one case per signal class). The embedding-input purpose does not exempt a string that restates computed values. Reason: SS's rule has no exception for the string's downstream use. Separately, route the `SELF_RULING_PAIRS` observation to the `bo_cgm_paths` owner as a §N.7-3 item (read dignity from L1).

**Effect.** (a) Narration: a declarations-file edit (Track E), two new tests; Narr gate measured for two more assets; no data change. (b) Structural label / embedding input: declare `[]` or leave undeclared; the two strings stay outside the Narr rule and the stated-value claim is untested. No rebuild either way. The `SELF_RULING_PAIRS` fix, if taken, changes no stored value (the table is standard sign lordship) and is writer code.

**Citation.** Not classical. citation: n/a (sign lordship in `SELF_RULING_PAIRS` is standard and not at issue).

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended. Declarations and tests: no rebuild, pre-approved now; the `SELF_RULING_PAIRS` observation is routed to the owner. TI-L2-11, TI-L2-34.

---

### Q-L2-14 — CF-16 (TG-L2-021): the counting rule for independent support

**Question.** What is the counting rule for independent support, so the shared-root carrier columns can be filled or retired: is a root one L1 fact, one placement (fact subject and category), or one fact subject?

**Facts.**
- The tiers supply the unit and the principle (several signals derived from one placement are not independent; do not inflate independent support) but not the carrier or the counting procedure (`L2_TIER_GAPS_v1_0.md`, TG-L2-021) `[brief]`.
- **Main's code already implements one rule, and the live data predates it.** `bo_sangati.py:210-232` `_signal_root_groups` takes a signal's declared roots (`shared_factor_keys_jsonb` on the MSR row) and falls back to its `constituent_facts_array` ids; `:298-358` writes `shared_factor_keys_jsonb = {"shared_root_groups": [...], "derivation": "constituent_fact_or_declared_root_ancestry"}` and `shared_factor_count = len(roots)` into each CDLM cell and feeds the count to `linkage_formula_v1`; the lines come from #2607 (`git log -S shared_root_groups`: `fa9857f00`, 2026-09-16) `[code]`.
- Live (built 2026-09-11): `bodha_cdlm_cells.shared_factor_keys_jsonb` NULL on 280 of 280 cells; `shared_factor_count` equals `shared_signal_count` on all 280 (range 3 to 4,358), i.e. the old behaviour counted signals, not roots; the MSR columns `shared_factor_keys_jsonb` and `cross_domain_shared_factor_count` are NULL on 50,678 of 50,678 `[db]`.
- The rerank counts signals sharing a `chart_facts.fact_subject` for `system_convergence_count` (non-null 50,023; greater than 1 on 27,952) (`bo_laksana.py:3726-3752`) `[code][db]`.
- The three candidate units give very different numbers. Distinct cited L1 facts on the canonical chart: 71,586 fact ids (73,049 references); distinct (fact_subject, fact_category) pairs 10,381; distinct fact subjects 5,770 `[db]`. (Counts span five ayanamshas.)
- In the formula the count enters as `log(1 + shared_factor_count) * 0.1` (`formulas.py:226`): by arithmetic a count of 4,358 gives 0.84 and a count about 12 times smaller (363) gives 0.59.

**Recommendation.** Adopt the conservative unit, one fact subject (the entity the cited L1 fact is about, plus the varga where the subject is a varga sign), as the root, and use it in both `bo_sangati` (replace the fact-id fallback) and the rerank so there is one rule; populate `shared_factor_keys_jsonb` with those subject keys (references only, never values) on the MSR rows and the CDLM cells. Independent support for a claim is the number of distinct roots across its supporting signals. Reason: the tier says count the contribution without manufacturing independent evidence; the fact-id unit credits four facts about one graha as four roots, which is the inflation the tier forbids; the subject unit is already production behaviour in the rerank. This is a modelling rule, not a classical one, so it carries an (R) and needs an acharya check of the unit.

**Effect.**
- Subject unit (recommended): `bo_sangati` cells' `shared_factor_count`, `shared_factor_keys_jsonb` and `computed_linkage_strength` change on all 280 canonical cells (the count falls from the signal count to a root count); the MSR carrier columns are populated by the MSR writers; rebuild: the MSR producers, `bo_laksana_rerank`, `bo_sangati` and the consumers of cell strength (`bo_cdlm_summary`, `bo_chart_gestalt`, `bo_drishti`, `bo_pramana_mapa` ...). Output change (R).
- Fact-id unit (main's present code): the same columns change on a `bo_sangati` rebuild with larger counts; the rerank and sangati would disagree on the unit.
- (Placement = subject + category): between the two; a finer unit that still credits several facts of one graha.
- No rule yet: the CDLM carrier stays NULL or fact-id based and `bo_pramana_mapa`'s `ledger_independence_pass` reads false (Q-L2-20).

**Citation.** Not classical (a method rule). citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended: root = fact subject (plus varga where the subject is a varga sign), one rule in `bo_sangati` and the rerank. (R). The unit goes on the J1 reviewers' list BY NAME. Batched. TI-L2-22, TI-L2-31.

---

### Q-L2-15 — CF-12 / CF-19: who owns the arudha and special-lagna nodes; whose is `valence`

**Question.** Do the arudha and special-lagna nodes stay with `bo_karanajala` (a declared cross-asset write with an orphan census) or move to `bo_bimba`; does `valence` belong to the producer or to the rerank for fingerprint ownership?

**Facts.**
- `bo_karanajala.py:1532-1650` upserts `arudha`/`special_lagna` nodes `ON CONFLICT (node_id)`; the code comment says it was done there because `bo_bimba.py` was outside the lane's `may_touch` glob (a scope convenience, not a design principle); the centrality UPDATE is at `:1870-1885` `[code]`. `replace_prior_cgm_nodes` (`_idempotency.py:343`) deletes only bimba's five node types, so these nodes are never deleted by anyone `[code]`. Canonical chart: 385 nodes = 255 bimba types + `arudha` 95 + `special_lagna` 35 `[db]`. Neither writer's build record counts the 130 (Q-L2-01). `asset_declarations.json` `cross_asset_writes` is null (unknown) for both `bo_karanajala` and `bo_laksana_rerank` `[code]`.
- Every arudha/special-lagna node cites its resolving L1 `fact_id` (§N.5-clean, comment at `:1529-1531`) `[code]`. `bo_bimba` already depends on `bo_arudha` and `bo_special_lagna` and is a declared dependency of `bo_karanajala` (live `depends_on`), so a bimba-owned node builder would still run before the edge builder `[db]`.
- `valence`/`valence_source` are written at insert by the producer (heuristic or `ga_vichara`), then the rerank re-resolves rows with `valence_source = 'keyword_heuristic_v1'` against a widened vichara lookup and UPDATEs both columns (`bo_laksana.py:3893-3951`) `[code]`. Canonical `valence_source`: `keyword_heuristic_v1` 44,479; `ga_vichara_v1` 6,050; `categorical_deterministic_v1` 125; `valence_doctrine_v1` 24 `[db]`. The rerank touches only `bo_laksana`'s rows; the satellites' valence is theirs.

**Recommendation.** (1) Now: declare both cross-asset writes with evidence pointers, run the orphan census (dry-run builder versus live nodes) and add a scoped prune only if orphans can occur. (2) End state: move the node builder to `bo_bimba` (the node registry) when `bo_bimba` is next rebuilt for Q-L2-06, so one writer owns a node type set and a delete-then-insert scope that covers all seven types; node ids are deterministic so edges do not re-wire. (3) `valence` and `valence_source` of `bo_laksana`-owned rows belong to the rerank in the fingerprint, because the rerank writes the final value; the producer's fingerprint excludes them (this extends the brief's own rule for `ga_vichara_v1` rows to all of `bo_laksana`'s rows, since the two writers cannot be told apart row by row). Reason: ownership by node type removes the orphan class by construction; a single writer of a column's final value is what a fingerprint needs.

**Effect.**
- (1) Declare/census: declaration edits, a read-only check; no data change; a prune only if orphans exist.
- (2) Move: code move across two writers; node set unchanged if ids are stable; `bo_bimba` build record becomes 385 (completion attribution for bimba reads true); `bo_karanajala` code digest changes; frozen t3 manifests of both stay valid (no `depends_on` change), only code digests move. Keep with karanajala: the shared table stays two-producer with a declared write.
- (3) Valence to the rerank in fingerprints: declaration/fingerprint contract only; no data change.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended: (1) declare the cross-asset writes and run the orphan census now; (2) the node move to `bo_bimba` rides the Q-L2-06 change in the one `bo_bimba` rebuild; (3) `valence`/`valence_source` of `bo_laksana` rows belong to the rerank in the fingerprint contract. TI-L2-17, TI-L2-30.

---

### Q-L2-16 — `bo_laksana_rerank`: keyword-heuristic valence, and the definition of the L2 MSR set

**Question.** Is the keyword-heuristic valence (44,479 of 50,678 canonical rows) an accepted documented approximation or a Null-gate defect; and is the architecture definition of the L2 MSR set corrected to six producers with the rerank an UPDATE-only dependant?

**Facts.**
- `_infer_valence` returns `malefic`/`benefic` from category lists and value substrings, else `neutral` (`bo_laksana.py:364-377`); a `ga_vichara` `valence_pass` row overrides it and sets `valence_source = 'ga_vichara_v1'` (`:380-440`) `[code]`. Canonical: `keyword_heuristic_v1` 44,479 rows (benefic 3,033; malefic 6,581; neutral 34,865); `ga_vichara_v1` 6,050 (benefic 2,371; malefic 2,047; mixed 1,632; neutral 0) `[db]`. So 34,865 rows (68.8% of the chart) read `neutral` with the heuristic as the source.
- `valence` and `valence_source` are nullable `[db]`; the default served projection exposes `valence_source` (`query_signals.ts:125-154`) `[code]`; `neutral` is a legitimate categorical value elsewhere (for example `valence_doctrine_v1` neutral for the kendradhipati dosha) `[db]`.
- MSR producers: six (`bo_laksana`, `bo_arudha`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`, `bo_nakshatra_semantic`), as in `msr_rebuild_order_guard.py` `MSR_PRODUCERS` and the check constraint named in its docstring (migration 1036) `[code@main]`; the rerank is UPDATE-only by its own comment (`bo_laksana.py:3640-3646`) `[code]`. "Arch §12.9" is not in this repository `[unverified]`.

**Recommendation.** (1) Accept the heuristic valence as a documented approximation with a decision id, using `valence_source` as the earned-signal discriminator (each row discloses which computation produced it, and the served default projection shows it); do not store NULL for `neutral` where a category rule matched, since `neutral` is a real category; grow `ga_vichara` valence coverage as the improvement path (L1 owner). (2) Yes: correct the definition to six producers with the rerank an UPDATE-only dependant (arch §12.9 text could not be read). Reason: the row says what produced the value (§N.8 satisfied); replacing 34,865 values by NULL would change every reader of `valence` for a discriminator that already exists in a column.

**Effect.**
- (1) Accept: declaration/decision id only; no data change. NULL for unmatched rows: `valence` changes on up to 34,865 canonical rows; consumers that treat `neutral` and NULL alike (`bo_sangati._is_qualified_contradiction` uses only malefic/mixed/antagonistic) are unaffected, others not traced; rebuild of `bo_laksana` and its chain; (R).
- (2) Correct to six: an architecture-document edit; the F-3 tooling already lists six; no code. Keep seven: a definition that disagrees with the CHECK constraint and the guard.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** CHANGED. Six producers accepted. Valence: where a category or keyword rule matched, keep the value (including a matched `neutral`); where nothing matched and the code falls through to `neutral`, store NULL. FIRST trace every reader of `valence`; if any reader breaks on NULL, ASK before coding. (R). **Found while recording:** `valence` and `valence_source` are nullable and carry no CHECK; a first-pass grep for files naming both `valence` and `bodha_msr_signals` gives 27 candidate readers (listed in the Rulings section), none traced. Batched after the trace. TI-L2-20, TI-L2-32.

---

### Q-L2-17 — `bo_samskara`: is the embedding table a navigation aid or a served semantic query

**Question.** Is `bodha_signal_embeddings` a build-time substrate with no served surface (declare it and correct the served text), or must the semantic query be built?

**Facts.**
- 50,678 embedding rows (canonical chart), one per MSR row; the table has in-repo readers that the brief did not list: `bo_anveshana.py:198` (embedding-outlier detection; `bo_samskara` is a declared dependency of `bo_anveshana`), `bo_pramana_mapa.py:684` (count) and `ph_nimitta.py:601-605` (existence check) `[code][db]`.
- `query_signals.ts` describes `semantic_query` as "pgvector cosine similarity over signal embeddings (768-dim)" and "100% populated for production charts" (`:223`, `:320-322`) while a code comment says "semantic_query: vertex embedding not available at query time; salience fallback used" (`:484`) and the response discloses `semantic_fallback` (`:731`) `[code]`. The tool text therefore promises a path the handler does not run, and the response corrects it after the fact.
- `coverage_matrix.ts:709` maps the table to `marsys://tool/L2/get_signal_embeddings`, which appears nowhere else in the repository (grep) `[code]`. Declarations record `served_surface: null` `[code]`.
- Building the query needs a Vertex embedding of the query string at call time, a new served-surface and cost item `[code: comment]`.

**Recommendation.** Declare it a build-time substrate (named readers `bo_anveshana`, `bo_pramana_mapa`, `ph_nimitta`), do not build the semantic query now, and correct the served text: remove the pgvector/"100% populated" wording from the tool and parameter descriptions and the dead `coverage_matrix.ts:709` pointer. Reason: a tool description that promises a mechanism the code does not run is a claim without a detector (§N.8); the table is useful as a substrate, and the new query is a separate feature.

**Effect.** (a) Declare + fix text: TypeScript text edits in two files and a declaration; no data change; no rebuild; Dens/Reach read "no served surface" with a stated reason. (b) Build the query: a new served surface and an embedding call (cost, latency), a new capability; out of scope here.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended. Declaration and TS text: no rebuild, pre-approved now. TI-L2-12.

---

### Q-L2-18 — CF-10: should Build.history count only runs since the last writer/registry change

**Question.** Should `Build.history` PARTIAL count only runs since the last change to the asset's writer or registry row (all 23 L2 assets read PARTIAL from recorded past errors)?

**Facts.** SS ruled this for L0 (Q11, 2026-10-01): "yes: Build.history counts only runs since the last change to the writer or the registry row" `[brief]` (L0 INDEX §9 read on `origin/main`). L2's PARTIALs are recorded errors (from 0/3 for three satellites to 39 errors and 7 aborts for `bo_laksana`); many latest errors are `BLOCKED` cascades or already-fixed defects (INDEX CF-10). Every L2 asset's writer file changed on 2026-09-16 (#2607; `bo_upaya` again on 2026-09-30), and the last builds are 2026-09-08 to 2026-09-12, so "runs since the last change" is empty for every asset until the coherent rebuild (fact 1) `[code][db]`.

**Recommendation.** Yes, carry L0 Q11 to L2 provisionally; no layer-specific fork. Reason: the cell differs by asset, not by criterion. Note the consequence: after #2607 no L2 asset has a run since its last writer change, so the cell reads "no run since change" until the coherent rebuild, which is the correct statement of fact.

**Effect.** Criterion definition and inspector reading only. (a) Carry: L2 cells re-read after the rebuild; no asset, registry or data change. (b) Do not carry: L2 needs its own window definition (a per-layer fork).

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended (carry L0 Q11); read after the rebuild. TI-L2-13, TI-L2-24.

---

### Q-L2-19 — CF-07: is a stratified re-derivation sample with the §N.5 resolver an acceptable L2 carriage detector

**Question.** Is a stratified re-derivation sample (D3), with the §N.5 constituent resolver as the reference leg, an acceptable Carr detector for L2 (D1 for `bo_upaya` and `bo_grounding`)?

**Facts.** The reference leg exists and passes: `msr_referential_integrity.py` (self-test is the CI gate; live mode runs per chart). I ran the same resolution read-only on the canonical chart: 73,049 `constituent_facts_array` references from `bodha_msr_signals`, 0 unresolved against `chart_facts.fact_id` (71,586 distinct) `[db]`. L0 Q13 `[brief]`: D1 anchor-term matching accepted, "the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled"; ratified judgment seeds get check-level N/A by cause `ratified_judgment`. Per-asset legs are designed in the briefs (D3 for most, D1 for `bo_upaya` and `bo_grounding`, D2/D3 for `bo_chart_gestalt`); none is built (`Carr` NO_DETECTOR x23).

**Recommendation.** Yes, with the L0 Q13 grading carried over: PASS only if every sampled row re-derives, else PARTIAL; the sample strata and size are declared in the detector; a seeded mismatch must be caught (the failing-first proof). Reason: it is the L0 rule applied to a layer that asserts structure over L1 facts; the reference leg is cheap and currently clean.

**Effect.** Detector/tooling only (Track E): no asset, registry or data change. (a) Accept: 23 Carr cells become measured after the detectors land; (b) Decline: Carr stays NO_DETECTOR x23 and the §N.5 trap has no gate beyond the existing CI self-test.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended (L0 Q13 grading). Detector work: no rebuild. TI-L2-14.

---

### Q-L2-20 — `bo_chart_gestalt.pivot_ids` and the `bo_pramana_mapa` pass-flags

**Question.** Is `pivot_ids` declared NULL-by-design (owner: CDLM §C3) or removed from the contract; and is the "open detector backlog" (three NULL pass-flags on the scorecard) in scope for the first L2 wave?

**Facts.**
- `pivot_ids`: always written `None` with the comment "L4 Phala fills when CDLM §C3 pivot factors are identified" (`bo_chart_gestalt.py:526`); the column is `UUID[]` from migration 325 (`:979`); NULL on 15 of 15 table-wide rows; no writer anywhere in the repository fills it (grep); the served tool lists `pivot_ids` among its fields (`query_chart_gestalt.ts:28`, `:85`) `[code][db]`.
- The three flags **are no longer an open detector backlog in code**: `bo_pramana_mapa.py:511-620` defines `_NO_PRE_ANSWER_SQL`, `_LEDGER_INDEPENDENCE_SQL`, `_DISCOVERY_GROUNDING_SQL` and `detect_l2_contract_integrity`, wired to `no_pre_answer_pass`, `ledger_independence_pass`, `discovery_not_fabricated_pass` (`:864-874`); added in #2607 (`fa9857f00`, 2026-09-16), and `tests/l2/test_l2_semantic_corrections.py` references them `[code]`. The live scorecard row was scored 2026-09-10 and still shows the three flags NULL (`lel_zero_leak_pass` t, `pillars_meet_reachability_pass` t) `[db]`; the INDEX and brief read the NULLs as "no detector".
- I ran the three detector SQLs read-only on the canonical chart: `no_pre_answer` 0 violations over 60 `bodha_question_lenses` rows (PASS); `discovery_grounding` 0 over 1,161 discoveries (PASS); `ledger_independence` **280 violations over 280 CDLM cells** (FALSE), because it requires `shared_factor_keys_jsonb` to carry `shared_root_groups`, which is NULL on the live cells until `bo_sangati` is rebuilt with main's code (Q-L2-14) `[db]`.

**Recommendation.** (1) `pivot_ids`: declare NULL-by-design with the owner named (CDLM §C3, L4 Phala) and keep the column; add "not computed" to the served field text; do not populate with `[]`. (2) Pass-flags: yes, in scope for the first wave, but as a rebuild, not detector work: rebuild `bo_sangati` first, then `bo_pramana_mapa`; expect `no_pre_answer_pass` and `discovery_not_fabricated_pass` true and `ledger_independence_pass` true only if the carrier rule of Q-L2-14 populates the cells (otherwise false, which is the honest reading). Reason: the code path that can fail now exists; the flags stay NULL only because the row predates it.

**Effect.**
- (1) Declare: declaration and text only. Remove the column: a surgical migration plus a served-field change (not recommended: the carrier has a named future owner).
- (2) In wave: one `bo_pramana_mapa` row rebuild (cheap, no cascade) after `bo_sangati`; the three flags change from NULL to true/false; downstream readers of the scorecard (`bo_samvada` view `trap1_count`) unchanged. Out of wave: the flags stay NULL on a row that is stale relative to its code.

**Citation.** Not classical. citation: n/a.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended: `pivot_ids` NULL-by-design with the named owner; the three pass-flags are read after the one rebuild (`bo_sangati` before `bo_pramana_mapa` inside it). TI-L2-15, TI-L2-24.

---

### Q-L2-21 — `bo_karanajala` argala (residual of A-1): does L2 need the BPHS {2, 4, 11} set as a named class

**Question.** Given that L2 must reference L1's {2, 4, 5, 11} argala, does L2 also need the BPHS {2, 4, 11} reading as a separately named, cited class, and who states the virodha pairing?

**Facts.**
- Corpus (all `sourced_ocr_unverified`): the Santhanam BPHS chapter is **Chapter 31 "Argala or Planetary Intervention"** (index `bphs_pg0006_c01`; chapter head `bphs_pg0310_c01`), not 28 as the writer's comment says; chapter numbering differs by edition, so the writer's label is uncorroborated rather than proved wrong. The text: the 4th, 2nd and 11th house occupants cause Argala, the obstructors are those in the 10th, 12th and 3rd, and "the 5th is also an Argala place where the planet in the 9th will counteract such Argala" (`bphs_pg0311_c01`, translator R. Santhanam). The Jaimini Sutras (trans. B. Suryanarain Rao, 1949): "the fourth, second and eleventh places ... from the aspecting body are Argalas" (`bphs_jaimini_pg0023_c01`, Su. 5); malefics in the 3rd give evil argala (Su. 6); "planets in the tenth, twelfth and third ... cause obstruction" (Su. 7); fewer or weaker obstructers do not defeat the argala (Su. 8); the trikonas "5 and 9" similarly influence the argala (Su. 9) (`bphs_jaimini_pg0023_c01`, `bphs_jaimini_pg0027_c02`, `bphs_jaimini_pg0028_c01`); for Rahu and Ketu the order is reversed (`bphs_pg0311_c01`; `bphs_jaimini_pg0028_c02`, Su. 10).
- So {2, 4, 11} is the basic set in both texts and the 5th (obstructed by the 9th) is a stated extension in both: L1's {2, 4, 5, 11} / {12, 10, 9, 3} is the full reading, not a different tradition. L2's current set is the subset without the 5th (24 pairs per ayanamsha vs 28 in Lahiri `[db]`).
- L1 stores offsets, not offset pairs (12-2, 3-4, 10-11, 9-5), and no node reversal (A-1 facts).

**Recommendation.** No: do not add a separate BPHS {2, 4, 11} class. The two sources agree on a basic set plus the 5th extension, so the project convention (L1's {2, 4, 5, 11}) is the authority and "{2, 4, 11}" is recorded as a named reading, produced as a filter (exclude offset 5 and its 9th obstruction) over the same L1 rows if a consumer ever needs it, never as a second definition. State the virodha pairing once, as a named cited rule (corpus passages above), in L1 if L1 will own it or in the L2 builder with its citation otherwise; route the Rahu/Ketu reversal and the empty-source-sign scoring (A-1) to the L1 owner as findings. The writer's "BPHS Ch. 28" label should be replaced by the corpus chunk ids once checked against print. Reason: SS rule 2, and both texts support the L1 set.

**Effect.**
- (a) No separate class (recommended): no extra edges; the A-1 rebuild gives the {2, 4, 5, 11} edges only; a documentation entry names the basic-set variant.
- (b) Add a named class: a second `relationship_class` (for example a basic-set argala) duplicating the three shared offsets (about 24 edges per ayanamsha), doubling most argala rows; needs its own citation state and Ldgr entry; more rows to maintain for no new fact.
- (c) Where the pairing lives: L1 (a new fact family, an L1 rebuild) versus L2 (a code constant with a citation). L2 keeps a constant that restates a classical rule, which §N.7 item 3 discourages; L1 is cleaner.

**Citation.** BPHS (Santhanam), `bphs_pg0310_c01` (Ch. 31 head), `bphs_pg0311_c01` (offsets {2, 4, 11}, obstructers {10, 12, 3}, the 5th/9th pair, node reversal): `sourced_ocr_unverified`. Jaimini Sutras (Suryanarain Rao), `bphs_jaimini_pg0023_c01` (Su. 5-9), `bphs_jaimini_pg0028_c02` (Su. 10, node reversal): `sourced_ocr_unverified`. The virodha pairing 12-2 / 3-4 / 10-11 is read from the same passages; the explicit "9 obstructs 5" is in `bphs_pg0311_c01`.

**RULING (SS, N-59, 2026-10-01).** Accepted as recommended: no separate class. The virodha pairing, the Rahu/Ketu reversal and the empty-source-sign score of 1.0 go to the L1 sheet as L1 items (L1 owns the pairing). The `bo_karanajala` argala fix lands after the L1 ruling; L2 creates a graha edge only where an occupant exists; 'BPHS Ch. 28' is replaced by the chunk ids and marked `sourced_ocr_unverified`. Batched, gated on the L1 ruling. TI-L2-16, TI-L2-33.

---

## SUMMARY TABLE (one page)

| id | short question | recommendation | ruling (N-59) |
|---|---|---|---|
| A-1 (ruled) | Argala: reference L1, not a local {2,4,11} | Record. Build graha edges from L1 matrix cells joined to occupants; caveats: empty source signs score 1.0, tier `single`, no node reversal. (R) | As written |
| A-2 (ruled) | F-3 order rule retires after 1214 + L2 key drops | Record. Verified: 0 FKs onto `bodha_msr_signals`; 0 dangling Kāla refs; keep `msr_dangling_signal_refs.py` post-wave. | As written |
| A-3 (ruled) | `chart_divisionals` RLS fixed | Record. Verified 24,392 / 23,542 / 23,542, RLS off; no L2 brief needs correcting. | As written |
| A-4 (ruled) | SS rules + citation states | Record. All citations here are `sourced_ocr_unverified` or n/a. | As written |
| Q-L2-01 | CF-02 produced-table set vs widen `count_sql`; grant | Option A (declare set + detector), no widening; grant SELECT on 10 tables. | Accepted; grant is a D6 plan (tables owned by `data_plane_l2_owner`) |
| Q-L2-02 | CF-04 `paginated:false`, MSR attribution, scanner, tier select | Yes to all four; offset only for `query_cgm_motifs`; static tier select. (R) | Accepted |
| Q-L2-03 | CF-20 neutral-constant salience inputs | Split: None for four Optional terms; L1 for shadbala/dignity; ratify orb as N/A; (R) | CHANGED: `orb_tightness` Optional, not ratified; one formula bump |
| Q-L2-04 | `bo_laksana` constant 2 and hand-set salience | NULL on 3 sites (54 rows); ratify the class-weight table; fix the v1.0/v2.0 stamp. (R) | Accepted; named stamp allowed (no CHECK); J1 list by name |
| Q-L2-05 | `bo_anveshana` confidence/fragility/falsifier + acharya claim | NULL until earned; drop or define the attention claim. (R) | Accepted; NULL now; fragility post-J1 |
| Q-L2-06 | `bo_bimba` yoga/dosha names + collisions | Approve display fix now; rule the identity collision separately (15 signals lost). (R) | CHANGED: name + identity fix together; design REVIEW first |
| Q-L2-07 | CF-15 edges (`ga_yoga`, `bo_bimba`, pratijna re-point) | Add the two; re-point pratijna after audit (L1: ga_vargas, ga_positions, ga_structural, ga_sensitive + 2 untraced); new migration number. | Accepted; 1216 unverified; trace two reads first |
| Q-L2-08 | `bo_grounding` integrate / substrate / retire | Integrate narrowly, layered (234 of 50,731 earned); #1726 satisfied in practice. (R) | CHANGED: declared substrate; integrate post-J1 |
| Q-L2-09 | `bo_samvada` qualify; build record; consolidation | Confirm qualify; real chart-scoped count (reads 5); record 0; no consolidation now. | Accepted |
| Q-L2-10 | CF-13 R243 annotation | Reword once; drop per-asset chart lists; no order-guard gate. | Accepted |
| Q-L2-11 | `bo_upaya` annotation lift | Only after B.U proves it live. | Accepted; read after the rebuild |
| Q-L2-12 | CF-03 seed alignment and 60,000 floors | Seed to live; one registry migration; floors after the coherent rebuild. | Accepted; floors after the rebuild |
| Q-L2-13 | CF-06 narration of `path_label_human`, `embedding_input_summary` | Both narration; declare and test; route `SELF_RULING_PAIRS`. | Accepted |
| Q-L2-14 | CF-16 counting rule for independent support | Root = fact subject (conservative); one rule in sangati and rerank; (R) | Accepted; unit on J1 list by name |
| Q-L2-15 | CF-12/19 node ownership; `valence` ownership | Declare now; move nodes to `bo_bimba` at its rebuild; valence to the rerank in fingerprints. | Accepted; node move rides Q-L2-06 |
| Q-L2-16 | Keyword valence; MSR set = six | Accept with decision id (`valence_source` discloses); correct to six. (R) | CHANGED: NULL where nothing matched; trace readers, ASK first |
| Q-L2-17 | `bo_samskara` embeddings: navigation or served | Declare substrate (3 readers); fix false served text; no semantic query now. | Accepted |
| Q-L2-18 | CF-10 Build.history window | Carry L0 Q11. | Accepted |
| Q-L2-19 | CF-07 D3 sample + §N.5 resolver | Yes, L0 Q13 grading (PASS only if every sampled row matches); resolver clean (0 of 73,049). | Accepted |
| Q-L2-20 | `pivot_ids`; pramana pass-flags | NULL-by-design with owner; flags are coded, need a rebuild (`ledger_independence` false until Q-L2-14). | Accepted |
| Q-L2-21 | BPHS {2,4,11} as a named class? | No; L1's {2,4,5,11} is supported by both texts; {2,4,11} a named filter; state the pairing once. (R) | Accepted; L1 items; gated on L1 ruling |

---

## Rulings (SS, N-59, 2026-10-01)

SS ruled this sheet on 2026-10-01 (decision N-59; PR #2841, branch `suvarna/land/A-L2-decisions-001`, HEAD `1ad09993b`; the briefs are PR #2831, branch `suvarna/land/A-L2-briefs-001`). Group A is accepted as written. Of the 21 open questions, **17 are accepted as recommended** (Q-L2-01, 02, 04, 05, 07, 09, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21; Q-L2-01, 04, 05, 07, 14 and 21 carry notes) and **4 are changed** (Q-L2-03, 06, 08, 16). Items marked (R) in the summary raise or define a verdict or change stored outputs and stay PROVISIONAL until the J1 independent review. Each ruling line above is the record; this section adds what I found while recording them (all read-only), the binding sequencing, and the lists SS asked for.

### Facts found while recording the rulings (read-only; 2026-10-01)

1. **Q-L2-01, route of the reader grant.** All 10 unreadable tables are owned by `data_plane_l2_owner` (`pg_tables.tableowner`), not `amjis_app`, and all 10 are listed in `L2_ACTIVE_TABLES` of `platform/scripts/data-plane-ownership-preflight.ts` (read on `origin/main`). The pre-approval was conditional on amjis_app ownership of all 10 and no gate pinning their ACL; neither holds, so the grant goes as a D6 plan with hash as REVIEW. `asset_registry` itself is owned by `amjis_app`, so every registry migration in this sheet stays on the pre-approved path.
2. **Q-L2-04, the stamp and the CHECK.** The only CHECK on `bodha_msr_signals` is `bodha_msr_signals_producer_asset_check` (six producer ids); `salience_formula_version`, `valence` and `valence_source` have none. So `classification_weight_v1` is allowed as written and no CHECK ALTER is needed (the table is `data_plane_l2_owner`'s, outside the amjis_app ALTER pre-approval, which therefore is not used).
3. **Q-L2-03, orb.** L1 has `orb_deg` facts for conjunctions only (Lahiri: `conjunction_per_varga` 115 rows, `conjunction_within_orb` 2); a search of `fact_key`/`unit`/`fact_category` for 'orb' found nothing for aspect categories. The 'none exists' branch of the ruling therefore applies to aspect classes today (TI-L2-21). On `bodha_msr_signals`, `orb_tightness`, `shadbala_norm` and `dignity_score` are nullable; `deterministic_strength` and `verification_certainty` are NOT NULL (computed products).
4. **Q-L2-07, the held migration.** `origin/main` has no migration above 1214 (`1214_f3_drop_kala_msr_signal_fks.sql`; `1211`-`1213` are taken) and the only TI-edges branch on origin is `suvarna/land/TI-edges-001` (nothing beyond 1210). Migration 1216 / branch TI-edges-002 therefore cannot be verified from here; confirm its number and whether it is applied at execution, else use max+1 across both migration directories.
5. **Q-L2-16, candidate readers of `valence` (first-pass grep of py/ts/tsx for files naming both `valence` and `bodha_msr_signals`; none traced, none excluded):**
   - platform/python-sidecar/pipeline/orchestrator/writers/: bo_pramana_mapa, bo_karanajala, bo_sangati, bo_chart_gestalt, bo_sudarshana, bo_nakshatra_semantic, bo_special_lagna, bo_vargottama_dhana, bo_arudha, bo_laksana, ka_yojaka
   - platform/python-sidecar/bodha_writers/: nakshatra_semantic_emitter.py, sudarshana_emitter.py, bhavat_bhavam_amplifier.py
   - platform/python-sidecar/services/ph_nimitta/engine.py
   - platform/src/lib/retrieval/: envelope.ts, ranking/composite_ranker.ts, spine/compute_spine_bundle.ts, registry/layers/register_d9_judgment.ts, registry/layers/reading_checklist.ts, registry/layers/L2_bodha/ (query_domain_reading.ts, query_signals.ts, traverse_chart_graph.ts, query_ucd.ts), registry/knowledge/source_query_availability.ts
   - platform-mcp/src/tools/: registry_bridge.ts, register_p1_synthesis.ts, register_p1_aliases.ts

### Sequencing (binding, per SS)

Batch every output-changing L2 fix, then run ONE coherent canonical L2 rebuild on main's code. No L2 asset is rebuilt twice for these rulings. Floors (Q-L2-12), Build.history (Q-L2-18), the three `bo_pramana_mapa` pass-flags (Q-L2-20) and the `bo_upaya` annotation (Q-L2-11; the B.U live proof folds into the single rebuild) are read AFTER that rebuild. Docs, declarations and TS-text items (Q-L2-02, 09, 10, 12, 13, 17, 18, 19) need no rebuild and are pre-approved now. With the F-3 ordering rule retired (A-2) there is no Kāla/Phala ordering constraint inside the rebuild; the canonical chart's Kāla tables are empty (I-6) and are rebuilt by the L3 campaign, not here.

**Gates before the one rebuild (my reading of the rulings; SS to confirm):**

- Q-L2-06 design REVIEW (classification of the 7 subjects and the id-change list) approved by SS (TI-L2-19)
- Q-L2-16 reader trace done, and any NULL-breaking reader put to SS (TI-L2-20)
- Q-L2-21 L1 ruling on the virodha pairing, the Rahu/Ketu reversal and the empty-source-sign score (TI-L2-16): the `bo_karanajala` argala change cannot be coded before it, so the one rebuild waits for it or SS rules that the argala change is excluded (then `bo_karanajala` is rebuilt again later, which the sequencing rule otherwise forbids)
- Q-L2-04 trace of the 14 `yoga_label` rows (TI-L2-18) and Q-L2-03 orb check (TI-L2-21) closed
- (not a gate for the rebuild, a gate for the detector) Q-L2-01 grant and the 65 / 15 / 60 / 60 confirmation (TI-L2-01)

### (a) Track I items from the rulings

The L2 INDEX carried no Track I numbering (the L0 and L3 INDEXes do: `TI-L0-nn`, `TI-L3-nn`), so the ids start at TI-L2-01. The same table is in `INDEX.md` section 12 (branch `suvarna/land/A-L2-briefs-002`). Classes: registry / declaration / writer code / detector / research / process. `y` items are the batched writer changes of the one rebuild.

**Go now (no rebuild):**

| id | asset(s) | item | class | rebuild | from |
|---|---|---|---|---|---|
| TI-L2-01 | the 10 unreadable `bodha_*` tables | reader SELECT for `suvarna_reader`. All 10 are owned by `data_plane_l2_owner` and all 10 are in `L2_ACTIVE_TABLES` of `platform/scripts/data-plane-ownership-preflight.ts`, so the pre-approved-migration condition is not met: go as a D6 plan with hash as REVIEW. Then read the tables and confirm the 65 / 15 / 60 / 60 gaps BEFORE the detector (TI-L2-02) is written | registry / grant (D6 REVIEW) | n | Q-L2-01 |
| TI-L2-02 | bo_bimba, bo_cdlm_summary, bo_karanajala, bo_sangati, bo_upaya | declarations-schema field for each asset's produced-table set, validator, and a Build.completion detector clause comparing `rows_written` with the chart-scoped count over that set; shared tables by partition (`producer_asset_id`; `node_type`) under the L0 Q6 rider relation; `count_sql` neither widened nor narrowed | declaration + detector | n | Q-L2-01 |
| TI-L2-03 | bo_cgm_motifs, bo_cgm_paths, bo_pramana_mapa (`query_quality_scorecard`), the bo_sangati modules (`query_triangulation` and the others) | declare `density_contract` with `paginated: false` and the true `empty_reason` (precedent `query_cdlm_summary.ts:144`, `query_chart_gestalt.ts:64`); add `offset` to `query_cgm_motifs.ts` only | served surface (TS, additive) | n | Q-L2-02 (a) |
| TI-L2-04 | the seven MSR producers, bo_yantra_mechanism, scanner | accept the `signal_type_class` facet as the MSR attribution rule; fix the scanner on `registry_bridge.ts` and `register_p1_synthesis.ts` before the re-measure; give `query_mechanisms.ts` a fixed select including `verification_pass_status` | detector + served surface (TS) | n | Q-L2-02 (b)-(d) |
| TI-L2-05 | bo_laksana, bo_upaya | add `bo_laksana -> ga_yoga` and `bo_upaya -> bo_bimba`; ride the held-edges migration (1216, branch TI-edges-002) if still unapplied, else max+1 across both migration directories; verify by production structure | registry | n | Q-L2-07 |
| TI-L2-06 | bo_pratijna | trace the producers of the two reads the brief missed (`chart_fact_identity`, `brahma_reference_planets`) and close the per-category audit; only then replace the two L2 edges by direct L1 edges (first-pass set `ga_vargas`, `ga_positions`, `ga_structural`, `ga_sensitive`) in one migration; the held `ph_nimitta -> bo_pratijna` edge waits | research, then registry | n | Q-L2-07 |
| TI-L2-07 | bo_grounding | declare it a substrate: outside the denominator (D-NATIVE-11), no consumer, reason stated; stays DRAFT; no retire; no new served surface before J1; record adjudication #1726 as 'satisfied in practice' (not ours to close) | declaration | n | Q-L2-08 |
| TI-L2-08 | bo_samvada | chart-scoped `count_sql` over the view (reads 5), floor 5, `natural_key_partition`, build record 0 under the changed-rows convention (L0 Q1); correct the docstring (`bo_samvada.py:31-40`) and the `cr_status.ts` comment | registry + documentation | n | Q-L2-09 |
| TI-L2-09 | bo_laksana, bo_arudha, bo_special_lagna, bo_nakshatra_semantic, bo_sudarshana, bo_vargottama_dhana | reword the R243 annotation (no cross-layer cascade remains; control `msr_dangling_signal_refs.py`); drop the per-asset chart lists; do not gate on the order guard | declaration text | n | Q-L2-10 |
| TI-L2-10 | the 18 CF-03 assets | one surgical registry migration (`bo_samvada` count/floor/kind, the three blank `natural_key_partition`s, `bo_bimba` storage_type and description) and the seed aligned TO the live values; floors are NOT touched now | registry + seed | n | Q-L2-12 |
| TI-L2-11 | bo_cgm_paths, bo_samskara | declare `path_label_human` and `embedding_input_summary` as narration in `prose_fields` with writer evidence; one golden-value test each | declaration + test | n | Q-L2-13 |
| TI-L2-12 | bo_samskara | declare `bodha_signal_embeddings` a build-time substrate with its readers (`bo_anveshana`, `bo_pramana_mapa`, `ph_nimitta`); remove the pgvector / '100% populated' wording from `query_signals.ts` (`:223`, `:320-322`) and the dead pointer at `coverage_matrix.ts:709`; no semantic query | declaration + served text (TS) | n | Q-L2-17 |
| TI-L2-13 | all 23 L2 assets | carry L0 Q11 (Build.history counts only runs since the last writer or registry change); read after the rebuild | detector definition | n | Q-L2-18 |
| TI-L2-14 | all 23 L2 assets | Carr: D3 stratified re-derivation with the section N.5 resolver as the reference leg, PASS only if every sampled row re-derives (L0 Q13 grading); D1 for `bo_upaya` and `bo_grounding` | detector | n | Q-L2-19 |
| TI-L2-15 | bo_chart_gestalt | declare `pivot_ids` NULL-by-design with the named owner (CDLM section C3, L4 Phala); say 'not computed' in the served field text; keep the column | declaration + served text (TS) | n | Q-L2-20 |
| TI-L2-16 | L1 (via the L1 decision sheet) | route to the L1 sheet as L1 items, L1 owning the pairing: the virodha pairing (12-2, 3-4, 10-11, 9-5), the Rahu/Ketu reversal, the empty-source-sign score of 1.0 in `argala_natal_matrix` (and the `single` tier of those rows) | research (L1 sheet) | n | Q-L2-21 / A-1 |
| TI-L2-17 | bo_karanajala, bo_laksana_rerank | declare the cross-asset writes (karanajala: `bodha_cgm_nodes` arudha/special_lagna rows and the centrality UPDATE; rerank: its six columns incl. `valence`/`valence_source`) with evidence pointers; run the orphan census (dry-run node builder against live nodes); `valence`/`valence_source` of `bo_laksana` rows belong to the rerank in the fingerprint contract | declaration + detector | n | Q-L2-15 (1), (3) |
| TI-L2-18 | bo_laksana | trace the 14 `yoga_label` rows that store `source_corroboration_count_by_text = 2` (source not traced in the sheet); treat them like the three sites if uncomputed | research | n | Q-L2-04 |
| TI-L2-19 | bo_bimba, bo_karanajala | ONE short design REVIEW document for SS, BEFORE any coding: (a) classify the 7 non-name yoga/dosha node subjects (a real yoga with a bad name gets its catalogue name; a flag, timestamp or number that is not a yoga, for example `is_yoga_karaka = false` or `inauspicious_flag = false`, gets NO yoga node); (b) the id-change list under the new identity (`signal_type_id` + configuration key) | research (design REVIEW) | n | Q-L2-06 |
| TI-L2-20 | bo_laksana, bo_laksana_rerank | trace every reader of `valence` first (first-pass candidate list in the Rulings section); if any reader breaks on NULL, ASK SS before coding | research | n | Q-L2-16 |
| TI-L2-21 | bo_laksana | orb: L1 stores `orb_deg` for conjunctions only (`conjunction_per_varga`, `conjunction_within_orb`); no orb fact was found for aspects, so for aspect-class signals store None and record this one Track I item (an L1 orb fact for aspects); re-check at execution | research (Track I item) | n | Q-L2-03 |
| TI-L2-22 | process | J1 reviewers' list BY NAME: (1) the `bo_laksana` classification-weight table (0.6 / 1.2 / 1.6 / 1.8 / 2.0), Q-L2-04; (2) the independence unit = fact subject (plus varga), Q-L2-14; the other (R) rulings are listed in the Rulings section | process | n | Q-L2-04, Q-L2-14 |
| TI-L2-23 | rebuild plan | retire the F-3 ordering invariant from the L2 rebuild plan (A-2); plan ONE coherent canonical L2 rebuild on main's code; record the gates before it (TI-L2-18, -19, -20, -16, -21 and the Q-L2-04 trace) | process | n | A-2, sequencing |
| TI-L2-24 | bo_upaya, bo_pramana_mapa, floors, Build.history | read AFTER the one rebuild: the `bo_upaya` annotation lift (the B.U live proof folds into the single rebuild), the three `bo_pramana_mapa` pass-flags (sangati before pramana_mapa inside the rebuild), floors restated to achieved counts (Q-L2-12), Build.history (Q-L2-18) | process | after the rebuild | Q-L2-11, 12, 18, 20 |

**Post-J1:**

| id | asset(s) | item | class | rebuild | from |
|---|---|---|---|---|---|
| TI-L2-25 | bo_anveshana | compute `ayanamsha_fragility` as 'the discovery holds in all five ayanamshas' (stored NULL until then) | writer code (improvement) | post-J1 | Q-L2-05 |
| TI-L2-26 | bo_grounding | integration: tier/granularity/evidence into the grounding spine and an earned-tier facet layered apart from the `pratyaksa` default; then CURRENT | served surface (improvement) | post-J1 | Q-L2-08 |

**Batched for the one L2 rebuild:**

| id | asset(s) | item | class | rebuild | from |
|---|---|---|---|---|---|
| TI-L2-27 | bo_arudha, bo_special_lagna, bo_sudarshana, bo_nakshatra_semantic, bo_vargottama_dhana, `formulas.py`, bo_laksana (aspect classes) | make `orb_tightness`, `shadbala_norm` and `dignity_score` Optional in `SalienceInputsV2` with ONE formula version bump; None for `ashtakavarga_bindus`, `vargottama_amplification`, `neechabhanga_modifier`, `cancellation_modifier` wherever not computed; shadbala/dignity read from L1 for graha-subject satellites, None for Lagna-point satellites (`bo_arudha`, `bo_special_lagna`); `orb_tightness` None wherever no orb was computed (identity in the product; salience unchanged); `bo_laksana` aspect classes read an L1 orb fact only if one exists (TI-L2-21) | writer code (R) | y | Q-L2-03 |
| TI-L2-28 | bo_laksana (`bhavat_bhavam_amplifier.py`) | `source_corroboration_count_by_text` NULL on the three constant sites (and the 14 `yoga_label` rows if uncomputed, TI-L2-18); stamp hand-set rows `classification_weight_v1` (no CHECK on `salience_formula_version`, no ALTER needed; the class-weight table is (R), J1 by name); ratify the table with a decision id | writer code (R) | y | Q-L2-04 |
| TI-L2-29 | bo_anveshana | `confidence`, `ayanamsha_fragility` and `falsifier` stored NULL; drop or define the acharya-attention claim in `why_an_acharya_misses_it` (numbers kept) | writer code (R) | y | Q-L2-05 |
| TI-L2-30 | bo_bimba, bo_karanajala | name fix AND identity fix together (identity = `signal_type_id` + configuration key), classification per the approved design REVIEW (TI-L2-19); the arudha/special_lagna node builder moves from `bo_karanajala` to `bo_bimba`; `yoga_node_subject` consumers and the `yoga_member` edges follow | writer code (R) | y | Q-L2-06, Q-L2-15 (2) |
| TI-L2-31 | bo_sangati, bo_laksana_rerank, the MSR producers (carriers) | root = fact subject (plus varga where the subject is a varga sign) as the one independence rule; populate `shared_factor_keys_jsonb` and the count on MSR rows and CDLM cells; replace sangati's fact-id fallback | writer code (R) | y | Q-L2-14 |
| TI-L2-32 | bo_laksana, bo_laksana_rerank | `valence` kept where a category/keyword rule matched (a matched neutral too); NULL where nothing matched and the code falls through to `neutral`; only after TI-L2-20 and any ASK | writer code (R) | y | Q-L2-16 |
| TI-L2-33 | bo_karanajala | argala edges from the L1 matrix cells joined to occupants (a graha edge only where an occupant exists); remove the local offset constants; replace the comment 'BPHS Ch. 28' by the chunk ids `bphs_pg0310_c01`, `bphs_pg0311_c01`, `bphs_jaimini_pg0023_c01` marked `sourced_ocr_unverified`; lands after the L1 ruling (TI-L2-16) | writer code (R) | y | Q-L2-21 / A-1 |
| TI-L2-34 | bo_cgm_paths | route the `SELF_RULING_PAIRS` observation (a wrapper-local constant, section N.7 item 3) to the owner; if taken it rides the one rebuild (not scheduled by the ruling) | writer code (conditional) | y if taken | Q-L2-13 |
| TI-L2-35 | `bodha_writers/_idempotency.py` | comment-only: the stale 'all eight CASCADE' text (`:179-180`, `:89`); changes every L2 writer's helper digest, so it rides the rebuild change set, not a separate run | documentation in code | rides the rebuild | A-2 |

### (b) L2 assets whose writers would change (for the sequencing statement)

**Code changes (11 of the 23 assets):**

| asset(s) | why |
|---|---|
| bo_arudha, bo_special_lagna, bo_sudarshana, bo_nakshatra_semantic, bo_vargottama_dhana | Q-L2-03 (the five emitters and the shared `bodha_writers/formulas.py`, one formula version bump); Q-L2-14 (carrier columns) |
| bo_laksana | Q-L2-03 (aspect-class orb), Q-L2-04 (NULL sites, `classification_weight_v1`, with `bhavat_bhavam_amplifier.py`), Q-L2-14 (carrier columns), Q-L2-16 (valence NULL) |
| bo_laksana_rerank (same file, `bo_laksana.py`) | Q-L2-14 (one independence rule), Q-L2-16 (valence re-resolution) |
| bo_anveshana | Q-L2-05 |
| bo_bimba | Q-L2-06 (name + identity), Q-L2-15 (2) (receives the arudha/special_lagna node builder) |
| bo_karanajala | Q-L2-06 (`yoga_node_subject` consumers), Q-L2-15 (2) (loses the node builder), Q-L2-21 / A-1 (argala from L1, gated on the L1 ruling) |
| bo_sangati | Q-L2-14 |

**Conditional or comment-only:**

| file / asset | note |
|---|---|
| bo_cgm_paths | TI-L2-34, only if the owner takes the `SELF_RULING_PAIRS` observation |
| `bodha_writers/_idempotency.py` (helper) and `bo_samvada.py` (docstring) | comment/docstring only (TI-L2-35, TI-L2-08); no behaviour change; the digest moves, a no-op writer's rebuild changes nothing |

**Re-run in the same rebuild with no writer change (12 of the 23):** bo_samskara, bo_grounding, bo_cgm_motifs, bo_cgm_paths, bo_yantra_mechanism, bo_drishti, bo_cdlm_summary, bo_pratijna, bo_upaya, bo_chart_gestalt, bo_pramana_mapa, bo_samvada. All 23 run, in DAG order, once: the 11 above change code and the other 12 sit downstream of an MSR producer or of a changed asset. `bo_laksana` and `bo_laksana_rerank` are one source file (`bo_laksana.py`), so their code changes together.

### J1 reviewers' list, BY NAME (items SS asked to be named)

1. The **`bo_laksana` classification-weight table** (the hand-set salience values 0.6 / 1.2 / 1.6 / 1.8 / 2.0 of the D9 cross-check and 1.2 of the divergence signal, stamped `classification_weight_v1`), Q-L2-04.
2. The **independence unit**: root = fact subject (plus varga where the subject is a varga sign), one rule in `bo_sangati` and the rerank, Q-L2-14.

Other (R) rulings, provisional until J1: A-1 and Q-L2-21 (argala from L1), Q-L2-02 (Dens declarations), Q-L2-03 (Optional salience terms, formula version bump), Q-L2-05 (NULL discovery epistemics), Q-L2-06 (node identity), Q-L2-16 (valence NULL). Q-L2-08 loses its (R) because no served surface is added before J1.

### Effects on other sheets

- **L3 sheet, Q-L3-01 option 3** (compute from L1 where an authority exists) followed the L2 CF-20 ruling: the Q-L2-03 ruling is the L2 answer. For L3 the same principle applies (Optional terms, None where no detector ran, L1 where an L1 fact exists); L3's own stand-ins are not changed by this record.
- **L1 sheet:** receives TI-L2-16 (virodha pairing, Rahu/Ketu reversal, empty-source-sign score of 1.0, `single` tier) and TI-L2-21 (an L1 orb fact for aspects, if SS wants one).

---

## What I could not verify

- **Branch tip.** Code was read at 29b2268a8 (PR #2831 head); `origin/main` is at 4eb40bec1 and carries migrations 1211 and 1214 and the F-3 scripts, which are not on the branch (read via `git show origin/main:`). Whether PR #2831 or the L3 decisions branch has merged since was not re-checked after the first fetch.
- **Documents outside the repository:** "arch §12.9", `F3_MSR_FK_DROP_v1_0.md`, the grant plan v1.3 (A-2 rests on the database structure, not on that document), `W2-3_REVIEW`, register R243/R244/R247, `reg_state.json`, the Track I edge evidence, adjudication #1726 and #2258 as records (only their repository echoes were read).
- **The 10 unreadable tables:** the gaps 65 / 15 / 60 / 60 (Q-L2-01), R244's "5 referencing rows" (Q-L2-11) and the contents of `bodha_convergence`, `bodha_contradictions` and the rollup tables remain unmeasured. Only the three CF-16/pramana detector SQLs that read readable tables were run.
- **Counts that need a code run, not a read:** how many argala edges the L1-referenced build would produce (only the Lahiri pair arithmetic: 24 vs 28), how many nodes an identity change would add (upper bound 100 on the canonical chart), what a rebuild with main's code produces for the CDLM carrier or the salience of the satellites.
- **Subject type of each satellite row** (Q-L2-03): the 45 + 45 counts equal 9 grahas x 5 ayanamshas but the per-row subject was not read; the L1 sources for `chart_fact_identity` and `brahma_reference_planets` (Q-L2-07) were not traced.
- **Scanner behaviour** on `registry_bridge.ts` and `register_p1_synthesis.ts` and every NO_DETECTOR count: quoted from the briefs.
- **Corpus citations** are text-search hits in OCR text, read by me, not checked against the printed books (`sourced_ocr_unverified` throughout). The chapter number of the argala chapter differs by edition.
- **Constraints I did not read:** whether `bodha_msr_signals.salience_formula_version` carries a CHECK that would block the stamp correction in Q-L2-04.
- **Seed items (f) and (h)** of CF-03 (volume formulas for some assets; count scope of `bo_laksana` by migration 448) were not re-verified.
- **The "no live reader" claims** rest on greps over py/ts/tsx and migrations; external callers cannot be excluded.

## Appendix · read-only evidence queries (as `suvarna_reader`, 2026-10-01 17:50-18:10Z)

Run through a wrapper script that sources the credential file silently (`. ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -f <file>`); no credential is shown here. All are `SELECT`.

```sql
-- A-2: foreign keys onto the MSR table (0 rows), function body, dangling Kala references
select conrelid::regclass, conname from pg_constraint where contype='f' and confrelid='bodha_msr_signals'::regclass;
select pg_get_functiondef(p.oid) from pg_proc p where p.proname='assert_l2_msr_delete_safe';
select 'kala_activation', k.chart_id, count(*), count(*) filter (where m.signal_id is null)
  from kala_activation k left join bodha_msr_signals m on m.signal_id=k.signal_id group by 2;   -- same for the other four kala_* tables
-- A-3
select relrowsecurity from pg_class where relname='chart_divisionals';
select chart_id, count(*) from chart_divisionals group by 1;
-- Q-L2-01: unreadable tables, counts, build records
select c.relname, has_table_privilege('suvarna_reader', c.oid, 'SELECT') from pg_class c ... where relname like 'bodha\_%';
select asset_id, state, rows_written, last_built_at from asset_throughput where asset_id like 'bo\_%' and chart_id='482012f1-...';
select 'cdlm_cells', count(*) from bodha_cdlm_cells where chart_id='482012f1-...';  -- and triangulation, rm_resonances, rm_remedy_prescriptions, cgm_edges, cgm_nodes, discoveries, anomalies
-- Q-L2-02: producer partition of signal classes; motif counts per ayanamsha
select signal_type_class, string_agg(distinct producer_asset_id, ','), count(*) from bodha_msr_signals where chart_id='482012f1-...' group by 1;
select ayanamsha_id, count(*) from bodha_cgm_motifs where chart_id='482012f1-...' group by 1;
-- Q-L2-03/04: satellite and laksana inputs, hand-set salience, version stamps
select producer_asset_id, salience_inputs_complete, verification_pass_status, count(*), min(orb_tightness), max(orb_tightness), min(shadbala_norm), max(shadbala_norm), min(dignity_score), max(dignity_score) from bodha_msr_signals where chart_id='482012f1-...' group by 1,2,3;
select producer_asset_id, salience_formula_version, count(*) from bodha_msr_signals where chart_id='482012f1-...' group by 1,2;
-- Q-L2-05: discovery constants
select count(distinct epistemic_jsonb->>'ayanamsha_fragility'), count(distinct falsifier_jsonb->>'falsifier'), count(*) filter (where round((epistemic_jsonb->>'confidence')::numeric,3)=round(least(consequence_score+0.1,1.0)::numeric,3)) from bodha_discoveries where chart_id='482012f1-...';
-- Q-L2-06: yoga/dosha collision measurement (names built with the same coalesce order as bo_bimba._yoga_config_name)
with s as (select ayanamsha_id, signal_type_class c, signal_type_id t, coalesce(nullif(trim(configuration_jsonb->>'fact_value_text'),''), nullif(trim(configuration_jsonb->>'yoga_name'),''), ..., signal_type_id) nm from bodha_msr_signals where chart_id='482012f1-...' and signal_type_class in ('yoga','dosha'))
select ayanamsha_id, c, count(*), count(distinct nm), count(distinct t) from s group by 1,2;
select node_type, count(*), count(distinct node_subject) from bodha_cgm_nodes where chart_id='482012f1-...' and node_type in ('yoga','dosha') group by 1;
-- Q-L2-07: registry edges; producer attribution of the categories ChartReaderV4 reads
select asset_id, depends_on from asset_registry where asset_id in ('bo_laksana','bo_upaya','bo_pratijna','ga_yoga','bo_bimba',...);
select fact_category, split_part(source_calculation,'/',1), count(*) from chart_facts where chart_id='482012f1-...' and ayanamsha_id='lahiri_chitrapaksha' and fact_category in ('bhava_cusps','special_lagna','karaka_chara_position','graha_dignity_per_varga','aspect_parashari_given','aspect_parashari_per_varga','upapada_lagna') group by 1,2;
-- Q-L2-08: grounding tier mix
select target_kind, grounding_tier, citation_granularity, count(*) from bodha_grounding_matches where chart_id='482012f1-...' group by 1,2,3;
-- Q-L2-09: view definition, per-chart view counts, registry row
select pg_get_viewdef('vw_chart_digest'::regclass, true);
select chart_id, count(*) from vw_chart_digest group by 1;
-- Q-L2-12: registry floors, partitions, status
select asset_id, catalog_status, target_floor, storage_type, (natural_key_partition is null or natural_key_partition='') from asset_registry where asset_id like 'bo\_%';
-- Q-L2-14/16: carrier columns, valence mix, root-unit counts, §N.5 resolution (also Q-L2-19)
select count(*), count(shared_factor_keys_jsonb), count(*) filter (where shared_signal_count=shared_factor_count) from bodha_cdlm_cells where chart_id='482012f1-...';
select valence_source, valence, count(*) from bodha_msr_signals where chart_id='482012f1-...' group by 1,2;
with refs as (select distinct unnest(constituent_facts_array)::text fid from bodha_msr_signals where chart_id='482012f1-...') select count(*), count(distinct cf.fact_subject), count(distinct (cf.fact_subject, cf.fact_category)) from refs r join chart_facts cf on cf.fact_id::text=r.fid and cf.chart_id='482012f1-...';
select count(*), count(*) filter (where cf.fact_id is null) from (select unnest(constituent_facts_array)::text fid from bodha_msr_signals where chart_id='482012f1-...') s left join chart_facts cf on cf.fact_id::text=s.fid and cf.chart_id='482012f1-...';
-- Q-L2-20: the three pramana detectors run read-only over the canonical chart (SQL as in bo_pramana_mapa.py:511-540), and the stored scorecard flags
select lel_zero_leak_pass, no_pre_answer_pass, pillars_meet_reachability_pass, ledger_independence_pass, discovery_not_fabricated_pass from synthesis_quality_scorecard where chart_id='482012f1-...' order by scored_at desc limit 1;
-- A-1/Q-L2-21: L1 argala rows and L2 argala edges; ordered graha pairs by house offset (Lahiri)
select fact_value_num, verification_pass_status, count(*) from chart_facts where chart_id='482012f1-...' and ayanamsha_id='lahiri_chitrapaksha' and fact_category='argala_natal_matrix' and fact_subject like 'D1\_SIGN\_%' and fact_value_num<>0 group by 1,2;
select relationship_class, count(*) from bodha_cgm_edges where chart_id='482012f1-...' group by 1;
-- corpus (all citations): classical_text_chunks(text_id, chunk_id, verse_ref, chapter, content_en, translator) searched with ~* 'argala'
```
