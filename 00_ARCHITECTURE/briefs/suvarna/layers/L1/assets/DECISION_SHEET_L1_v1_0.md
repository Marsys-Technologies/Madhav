---
artifact: DECISION_SHEET_L1
layer: L1 Gaṇita (ga_*)
version: "1.0"
status: "RULED (SS 2026-10-02: argala block N-61, the rest N-62); items marked (R) are provisional until the J1 independent review"
produced_by: exec-suvarna
produced_on: 2026-10-02
plan_item: A.L1 (decision sheet over the briefs; one pass for Strategic Suvarṇa)
source_branch: "suvarna/land/A-L1-briefs-001 (PR #2832, open) at f315b2dc2 (code and briefs read here); the SS rulings are recorded in the briefs and INDEX on suvarna/land/A-L1-briefs-001-rulings (c5c3c284f, N-61) and suvarna/land/A-L1-briefs-001-rulings2 (854fbe051, N-62), each a fast-forward of the previous tip; this sheet (suvarna/land/A-L1-decisions-001, PR #2844) is rebased on that tip"
source_files: "00_ARCHITECTURE/briefs/suvarna/layers/L1/assets/INDEX.md (section 7, the 17 questions) and the 19 per-asset briefs in the same directory"
scope: "docs only; no code, registry, migration or database write"
provisional: "every ruling taken from this sheet is provisional until the J1 independent review"
changelog: "1.2 (2026-10-02): SS-accepted deviation on Q-L1-16(a) recorded (sibling module `brahmagyan/verification_tiers.py`, PR #2854; `verification_vocab.py` not edited), in the Rulings section, the Q-L1-16 ruling line, I-27 and the summary; briefs/INDEX on suvarna/land/A-L1-briefs-001-rulings3 (4c4bde1d8). 1.1 (2026-10-02): SS ruling N-62 recorded: second Rulings section, a ruling line per item (A-3, A-4, Q-L1-01..17, X1, X2), summary column, Track I items I-21 to I-42; also recorded in the 20 affected briefs and the INDEX on suvarna/land/A-L1-briefs-001-rulings2 (854fbe051), on which this sheet is rebased. 1.0 (2026-10-02): complete sheet: Group A, Group B (Q-L1-01..17), B-X (X1, X2), summary table, findings beyond the briefs, unverifiable items, appendix. Earlier entry, 1.0-early rulings (2026-10-02): SS rulings on group B-0 (decision N-61) recorded: Rulings section, a ruling line per item AR-1..AR-6, summary column; the rulings are also recorded in the L1 INDEX and the ga_structural brief on suvarna/land/A-L1-briefs-001-rulings (c5c3c284f), on which this sheet is rebased. 1.0-early (2026-10-02): the first commit carried only group B-0 (the six argala items), put first at SS's priority request."
---

# L1 Gaṇita decision sheet (for one ruling pass by Strategic Suvarṇa)

## 0 · How to read this sheet

**Structure.** The sheet opens with the Rulings section and Group B-0, the six argala items, because SS asked for them first (they are RULED, N-61). Group A (already ruled or resolved: argala, the `chart_divisionals` RLS fix, the canonical ephemeris backend as a first-class finding, Gandanta width, MEAN node) records each ruling, the facts I verified, what the ruling requires in the code, and the effect, so it can be executed without another round; it is not re-asked. Group B holds the 17 open questions of the L1 INDEX (section 7) as Q-L1-01 to Q-L1-17, and B-X holds two new questions found while verifying. Every open item has the same fields: question, facts, recommendation, effect of each possible answer (outputs, which assets rebuild, doc/registry only), citation. A one-page summary table closes the sheet, followed by findings beyond the briefs and what I could not verify.

**Rules SS gave for rulings (applied throughout).** (1) A classical fact needs a `bg_texts` corpus citation (B.3). (2) Where traditions differ, the project's existing L1/engine convention is the authority (CLAUDE.md §N.5) and the alternative is recorded as a named variant. (3) Every ruling is provisional until the J1 independent review. (4) Items that raise or define a verdict, or change stored outputs, are marked **(R)**.

**Citation states (SS rule, applied to every citation).** An OCR text-search hit not checked against print is `sourced_ocr_unverified`. A passage I looked for and did not find is `unsourced`. Only a citation verified at passage level counts toward a PASS on Ldgr; nothing in this sheet is above `sourced_ocr_unverified`.

**Evidence tags.** `[code]` = read in the repository at `f315b2dc2` (file:line). `[investigation]` = quoted from the ephemeris investigation of PR #2840 and not re-run by me. `[db]` = read-only `SELECT` as `suvarna_reader` (2026-10-01 to 2026-10-02; queries in the appendix; no write, no credential shown). `[corpus]` = text search of `classical_text_chunks` (the chunk table of the `bg_texts` corpus); the chunk id is given so the passage can be re-found; the text is OCR and I read it, but it is not checked against the printed book. `[calc]` = a figure I computed offline from stored L1 facts read with `[db]` (method stated; not a rebuild result). `[brief]` = quoted from a brief or INDEX and not re-verified.

**Charts.** Canonical = `482012f1` (native). Abhinandan = `1c826d5a`. Third chart = `cb73cd3d`. Every `[db]` figure is the canonical chart unless another chart is named.

**Ruling status carried in.** SS has already ruled that L1 is the authority for argala and L2 references it (CLAUDE.md §N.5; L2 decision sheet A-1). The six items below are what that ruling leaves open, now routed to L1 because L1 owns the pairing.

---

## Rulings (SS, 2026-10-02, decision N-61) — argala block

SS ruled the argala block (group B-0). **All six recommendations are ACCEPTED**, with the points below made binding or more precise. Every (R) item is provisional until the J1 independent review, and **the argala pairing and the node reversal go on the J1 reviewers' list BY NAME.**

| item | what SS ruled (beyond or sharpening the recommendation) |
|---|---|
| AR-1 (R) | (a): L1 owns the pairing 2-12, 4-10, 11-3, 5-9. Obstruction applies to benefic AND malefic argala. Outcome by count only: argala count > obstructor count = `argala_prevails`; fewer = `obstructed`; equal = `undetermined`; "stronger" stays null (unsourced). `virodha` means the obstruction in every layer; L2's "argala by a malefic" gets a different name (the L2 design note proposes it). The `get_argala.ts` offsets text is fixed now (pre-approved). |
| AR-2 (R) | (a): reverse for BOTH nodes when the node is the reference, in the L1 graha-level rows (`count_direction`). Ketu-only is a named stricter variant. The sign matrix stays forward-only and says so. |
| AR-3 (R) | (a): empty source sign = NULL with `no_occupant`. The 1.0 / 0.25 formula stays as a project convention (`unsourced`); the BPHS count grading is post-J1. |
| AR-4 | (a): keep `single`; correct the provenance string to the real writer function. |
| AR-5 | Accepted as written. |
| AR-6 (R) | (a): L1 {2, 4, 5, 11} / {12, 10, 9, 3} canonical, {2, 4, 11} a named filter. L1 adds the graha-level family, D1 only. L2 builds edges from those rows, cites their `fact_id`s, and deletes its offset constants, its pairing and its own malefic set. If an edge needs a benefic/malefic label, ONE cited definition in the L0 graha vocabulary (Sun, Saturn, Mars; nodes stated separately) read by both layers. The vipareeta / 3rd-house evil argala is recorded, not built. |
| Sequence (binding) | ONE `ga_structural` rebuild carrying the argala change AND the ephemeris fix, after G-EPH and G-FLIP, as part of S-L1; then `bo_karanajala` inside the single S-L2 batch; no argala-only L1 rebuild. Migration 1219 is allocated for the `fact_category_ownership` row (and the `count_sql` / floor touch). |

**Track I items** (continuing the L1 INDEX numbering after I-13; defined in `INDEX.md` section 9): I-14 graha-level family, pairing, node reversal (AR-1, AR-2, AR-6); I-15 empty cells (AR-3); I-16 provenance string and citation block (AR-4, AR-5); I-17 `get_argala.ts` description (AR-1); I-18 L0 benefic/malefic definition (AR-6); I-19 `bo_karanajala` reads L1 rows (L2 set); I-20 binding sequence and migration 1219.

---

## Rulings (SS, 2026-10-02, decision N-62) — the rest of the sheet

SS ruled the sheet. **EVERY recommendation of Q-L1-01 to Q-L1-17, X1 and X2 is ACCEPTED**, with the specifics below; all (R) items are provisional until the J1 independent review.

**S-L1 scope (binding).** S-L1 is the canonical chart `482012f1` first; the other two charts (`1c826d5a`, `cb73cd3d`) are a later stage, **S-L1b**, a separate REVIEW after the canonical run passes. S-L1 never waits for an optional item.

**Mandatory before S-L1 (merged and deployed):** the ephemeris fix (G-EPH, G-FLIP; I-21); argala (N-61; I-14 to I-20); the Gandanta shared L0 module and X1 (3°20' in `is_gandanta`, 0°48' as `formula_id = strict_0_48` variant rows; I-22); Q-L1-01 F-A2 key widening and non-empty integrity clause (I-23); Q-L1-02 the two `ga_vargas` edges AND the Daridra cancellation moved to `ga_vichara` as its own family (order-independence is a correctness fix; trace the readers of the `dosha_label` bhanga fields first; I-24, I-25); Q-L1-03 honest tiers (I-26); Q-L1-16(a) tier constants, satisfied by the sibling module `brahmagyan/verification_tiers.py` (PR #2854; `verification_vocab.py` is NOT edited, deviation accepted by SS), emit `single`, never `single_pass` (I-27); Q-L1-16(c) one band table at `ga_condition`, cut points 0.4 / 0.7, NULL score = NULL / `unknown`, never `neutral` (I-28); X2 fallback made visible plus an integrity clause (I-29); Q-L1-04 ownership (I-30).

**Optional (ride S-L1 only if ready when the gates clear, otherwise the next wave):** Q-L1-10 ayurdaya haranas (I-32), Q-L1-11 activation periods and D9 lineage by natural key (I-33), Q-L1-13 transit-anchor `source_fact_ids` (I-34), Q-L1-15 the three `ga_condition` columns (I-35).

**Deviation accepted by SS (Q-L1-16(a)).** (a) is SATISFIED by the sibling module `platform/python-sidecar/brahmagyan/verification_tiers.py` (constants derived from `verification_vocab` at import; `emit_tier()` rejects the deprecated `single_pass` alias; implementation PR #2854), NOT by editing `verification_vocab.py`: editing it moved 30 writer digests (1 L0, 15 L2 including the FROZEN `bo_laksana`, 4 L3, 10 L1) and made `NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE` false (the 29 frozen L0 capsules fail closed; the L0 pin readmission test went red). SS accepted the deviation: keep the sibling module, do NOT edit `verification_vocab.py`, do not pursue the L0 pin readmission. Recorded in the Q-L1-16 ruling line, I-27, the summary and the INDEX/briefs that mention Q-L1-16(a).

**Before S-L1, read-only answers to SS:** F-4 and F-8 (separate workers; I-31), and the per-emitter tier audit table (I-26). **Migration numbers:** asked per migration (1219 is allocated for the argala ownership row and the other ownership rows may ride it).

| item | what SS ruled (beyond or sharpening the recommendation) |
|---|---|
| Q-L1-03 (R) | `two_pass_verified` ONLY for an independent re-derivation compared through `two_pass_verdict`; bounds, ordering and same-formula arithmetic re-checks = `classical_match`; the 1,780 zero-tolerance default rows = `single`; a per-emitter audit of the 6,970 positive-tolerance rows (table: emitter, rows, second path yes/no, resulting tier) goes to SS before S-L1; Yogi authority = `bphs_93_20`, `alt_96_40` a named variant, `ga_sensitive_degree` reads it; the second derivation of the four pañcāṅga angas is later. |
| Q-L1-04 | `ga_structural` owns `bhava_bala_*`; ownership rows may ride 1219; `ga_condition` declared multi-table, `count_sql` on the primary table, `rows_written` counts everything it writes. |
| Q-L1-10 (R) | NOW, display-side, pre-approved: the served ayurdaya totals say they are unreduced base figures (no reductions applied). The enrichment itself only for rules whose passage is at least `sourced_ocr_unverified` (the three Pindayu haranas qualify; astangata and Chakrapata do not until found), additive beside the base totals, each applied reduction named. OPTIONAL. |
| Q-L1-11 (R) | Offline dry run authorised (read-only); `partial_formation_pct` deferred; floor = achieved count after S-L1; activation periods and D9 lineage OPTIONAL. |
| Q-L1-12, Q-L1-14 | The two N/A rules (`no question-moment chart for a natal build`; `rolling_horizon`) are prepared as `NA_RULE_DECISIONS` entries; the engine session owns that list. |
| Q-L1-15 (R) | OPTIONAL. `speed_degrees_per_day` stays NULL, declared null-by-design with `[EXTERNAL_COMPUTATION_REQUIRED]` until `ga_positions` stores it; the column is NOT dropped. |
| Q-L1-16 | (a) is SATISFIED by the sibling module `platform/python-sidecar/brahmagyan/verification_tiers.py` (constants derived from `verification_vocab` at import; `emit_tier()` rejects the deprecated `single_pass` alias; implementation PR #2854), NOT by editing `verification_vocab.py`: editing it moved 30 writer digests (1 L0, 15 L2 including the FROZEN `bo_laksana`, 4 L3, 10 L1) and made `NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE` false (the 29 frozen L0 capsules fail closed; the L0 pin readmission test went red). SS accepted the deviation: keep the sibling module, do NOT edit `verification_vocab.py`, do not pursue the L0 pin readmission. (b) keep the eight sites, declared CLI-only, with the grep guard; (c) one band table 0.4 / 0.7. |
| Q-L1-07 | No standalone rerun. |
| X2 (R) | The two affected charts are rebuilt in S-L1b (after the canonical run). |
| Accepted as written | A-3, A-4 (as recorded), Q-L1-01, 02, 05, 06, 08, 09, 12, 13, 14, 17, X1. |

**Track I items** (continuing the L1 INDEX numbering after I-20; defined in `INDEX.md` section 9): the table below, split into mandatory before S-L1, optional, and now (pre-approved).

| id | bucket | asset(s) | item | class | rebuild | from |
|---|---|---|---|---|---|---|
| I-21 | mandatory before S-L1 | ga_positions, ga_dashas, ga_vargas, ga_strength, ga_structural, ga_tajaka, ga_sensitive, ga_nakshatra, ga_condition, ga_panchanga, ga_sade_sati | ephemeris fix, L1 side (G-EPH, G-FLIP): re-assert the Swiss path at the PyJHora choke point, replace the four `set_ephe_path(None)` in `panchang_engine` and the three `/usr/share/ephe` calls in `ga_sade_sati_writer.py` by one shared helper, record the backend in each writer's `WriterResult.notes`, correct the "Swiss" provenance strings (180 `midpoint` rows, docstrings), Carr D3 detectors read the recorded backend | writer code (output) (R) | S-L1 | A-3 |
| I-22 | mandatory before S-L1 | ga_sensitive_degree, ga_structural, ga_nakshatra (+ L0 module) | Gandanta: ONE shared L0 module (3°20' each side) imported by the three writers; X1: `graha_gandanta.is_gandanta` follows 3°20', the 0°48' reading is emitted as `formula_id = strict_0_48` variant rows; the bare `except` around the import in `ga_structural` counts and logs | writer code (output) + L0 module (R) | S-L1 | A-4, X1 |
| I-23 | mandatory before S-L1 | ga_vargas | Q-L1-01: widen `chart_divisionals_unique_idx` and both `ON CONFLICT` targets to include `fact_subject` (F-A2, +250 D30 rows per chart; surgical migration, verified by production structure); non-empty clause in the `ga_vargas` `integrity_check_sql`; cutover-gate check (no protected active table with RLS and no policy for a serving or builder role) | migration + writer code + registry (R) | S-L1 | Q-L1-01 |
| I-24 | mandatory before S-L1 | ga_dashas, ga_yoga | Q-L1-02: declare `ga_dashas -> ga_vargas` and `ga_yoga -> ga_vargas` (guarded, append-only, acyclic-checked migration of the 1210 kind) | registry (migration) | n (digest signal inside S-L1) | Q-L1-02 |
| I-25 | mandatory before S-L1 | ga_structural, ga_vichara | Q-L1-02: the Daridra cancellation moves to `ga_vichara` as its own family; `ga_structural` keeps detection only; order-independence is a correctness fix; FIRST trace the readers of the `dosha_label` bhanga fields | writer code + data (R) | S-L1 | Q-L1-02 |
| I-26 | mandatory before S-L1 | ga_sensitive, ga_sade_sati, ga_sensitive_degree, ga_nakshatra | Q-L1-03 honest tiers: `two_pass_verified` ONLY for an independent re-derivation compared through `two_pass_verdict`; bounds, ordering and same-formula arithmetic re-checks = `classical_match`; the 1,780 zero-tolerance default rows = `single`; PER-EMITTER AUDIT of the 6,970 positive-tolerance `ga_sensitive` rows BEFORE S-L1 (table: emitter, rows, second path yes/no, resulting tier) goes to SS; Yogi authority = `esoteric_point_yogi` `formula_id = bphs_93_20`, `alt_96_40` a named variant, `ga_sensitive_degree` reads it; the second derivation of the four pañcāṅga angas is later | writer code (output) (R) | S-L1 | Q-L1-03 |
| I-27 | mandatory before S-L1 | `brahmagyan/verification_tiers.py` (sibling module, PR #2854); 13 L1 writers | Q-L1-16(a), satisfied by the sibling module instead of editing the L0 `verification_vocab.py` (deviation accepted by SS): constants derived from `verification_vocab` at import, `emit_tier()` rejects the deprecated `single_pass` alias; the L1 writers adopt it and emit `single` (10,836 canonical rows) | new module + writer code | S-L1 | Q-L1-16 |
| I-28 | mandatory before S-L1 | ga_condition, ga_medical, ga_vastu | Q-L1-16(c): ONE band table at `ga_condition`, cut points 0.4 / 0.7, read by both writers; NULL score = NULL / `unknown`, never `neutral` | writer code (output) (R) | S-L1 | Q-L1-16 |
| I-29 | mandatory before S-L1 | ga_condition | X2: a D1-fallback row is made visible (served field and Dens facet) and an integrity clause fails a fallback on a chart that has divisionals | writer code + registry (R) | S-L1 (canonical); the other two charts in S-L1b | X2 |
| I-30 | mandatory before S-L1 | ga_structural, ga_strength, ga_condition, other chart_facts producers | Q-L1-04: `ga_structural` owns `bhava_bala_*`; narrow `ga_strength`'s predicate; complete `fact_category_ownership` for every producer (the 12 `ga_structural` categories and the rest) with a writer-constants parity test; `ga_condition` declared multi-table, `count_sql` on the primary table, `rows_written` counts everything it writes; ownership rows may ride migration 1219; floors re-declared from achieved counts | registry (migration) + writer code + test | n (registry); `rows_written` on next dispatch | Q-L1-04 |
| I-31 | mandatory before S-L1 | ga_vargas, ga_dashas, ga_positions | BEFORE S-L1, read-only answers to SS (separate workers): F-4 (the 15,078-row `chart_divisionals` build-record gap) and F-8 (`ga_dashas` `incomplete` on the third chart; the 2026-09-19 `ga_positions` abort) | research (read-only diagnosis) | n | F-4, F-8 |
| I-32 | optional (rides S-L1 only if ready when the gates clear) | ga_ayurdaya | Q-L1-10 haranas: only rules whose passage is at least `sourced_ocr_unverified` (the three Pindayu haranas qualify; astangata and Chakrapata do not until found); additive beside the base totals, each applied reduction named; new `depends_on` edges allowed | writer code (output) (R) | rides S-L1 only if ready, else next wave | Q-L1-10 |
| I-33 | optional (rides S-L1 only if ready when the gates clear) | ga_yoga | Q-L1-11: `activation_dasha_periods` read from stored `chart_dashas` rows (Nabhasa yogas null with reason); D9 lineage by natural key in `grounds_jsonb`; `partial_formation_pct` deferred; floor = achieved count after S-L1 | writer code (output) (R) | rides S-L1 only if ready, else next wave | Q-L1-11 |
| I-34 | optional (rides S-L1 only if ready when the gates clear) | ga_transit_anchors | Q-L1-13: stored `source_fact_ids` column (additive migration), written from the rows the writer read; the served tool reads it (serve-time resolver kept as fallback until the rebuild) | migration + writer code (R) | rides S-L1 only if ready, else next wave | Q-L1-13 |
| I-35 | optional (rides S-L1 only if ready when the gates clear) | ga_condition | Q-L1-15: populate `avastha_sayanadi`, `avastha_lajjitaadi`, `graha_yuddha_result` from the existing L1 facts (reference, never re-derive); `speed_degrees_per_day` stays NULL, declared null-by-design with `[EXTERNAL_COMPUTATION_REQUIRED]` until `ga_positions` stores it; do NOT drop the column | writer code (output) (R) | rides S-L1 only if ready, else next wave | Q-L1-15 |
| I-36 | now (pre-approved) | ga_ayurdaya (served) | Q-L1-10 display side, pre-approved: the served ayurdaya totals say they are unreduced base figures (no reductions applied) | served surface (TS) | n | Q-L1-10 |
| I-37 | now (pre-approved) | ga_yoga | Q-L1-11: the offline dry run of the detectors against stored L1 facts (reproduce the 53; list the D9-dependent firings) is authorised, read-only, no DB write | research (read-only) | n | Q-L1-11 |
| I-38 | now (pre-approved) | ga_prashna, ga_tajaka | Q-L1-12 and Q-L1-14: prepare the two N/A rules as `NA_RULE_DECISIONS` entries (`no question-moment chart for a natal build`; `rolling_horizon`, with the reference year recorded in `WriterResult.notes`); the engine session owns that list | declaration + detector | n | Q-L1-12, Q-L1-14 |
| I-39 | now (pre-approved) | 8 writers with legacy `_telemetry` calls | Q-L1-16(b): keep the eight `update_asset_throughput` sites, declared CLI-only, with a grep guard that no `ga_writers` module calls it outside the declared CLI | test (guard) + declaration | n | Q-L1-16 |
| I-40 | now (pre-approved) | ga_medical, ga_vastu, ga_yoga | Q-L1-05: declare `prose_fields` for `direction_impact`, `indication_strength`, and extend `ga_yoga` (`derivation`, `strength_label`, `bhanga_na_reason`) with golden-value tests at each cut point | declaration + tests | n | Q-L1-05 |
| I-41 | now (pre-approved) | L1 served modules; inspector | Q-L1-06: Dens read per `fact_category` partition via `carriage.served_surface`; add the tier to the selects that lack it (not `get_argala.ts`, which has it); the scanner reads the primary select; correct the INDEX list | served surface (TS) + inspector | n | Q-L1-06 |
| I-42 | now (pre-approved) | all L1 (Track E) | Q-L1-08 and Q-L1-09: the Idem claim (zero live keys under the writer's own partition that its produced-key set lacks; rebuild-twice fingerprint) and the Carr rules (verified subset is the PASS population; invariant-only detectors read PARTIAL; seeded mismatch; recorded backend; D2 for `ga_ayurdaya`) | detector/tooling | n | Q-L1-08, Q-L1-09 |

---

## GROUP B-0 · Argala (priority block; the bo_karanajala fix and the single batched L2 rebuild wait on this)

### What L1 and L2 hold today (shared facts for AR-1 to AR-6)

- **L1 writes three argala families, all owned by `ga_structural`** (`fact_category_ownership`: `argala_natal_matrix`, `virodha_argala_natal_matrix`, `net_argala_per_varga` -> `ga_structural`) `[db]`. (a) `argala_natal_matrix` and (b) `virodha_argala_natal_matrix`: a 12 x 12 sign matrix per divisional chart, 144 rows each (`ga_writers/ga_structural_writer.py:4670-4781`, with a halt if the count is not 144, `:4771-4781`); (c) `net_argala_per_varga`, a house-level net count (`:7259-7295`). Offsets: `ARGALA_OFFSETS = [2, 4, 5, 11]`, `VIRODHA_OFFSETS = [12, 10, 9, 3]`, comment "per Jaimini Sutram" (`:614-616`) `[code]`.
- **Stored (canonical chart):** 21,600 argala rows + 21,600 virodha rows + 1,800 net rows = 45,000 `chart_facts` rows (30 divisional charts x 5 ayanamshas), every one `verification_pass_status = single` `[db]`.
- **L2 computes its own argala** from graha signs, graha to graha: `ARGALA_POSITIONS = {2, 4, 11}`, `VIRODHA_POSITIONS = {12, 3, 10}`, a pairing `{2: 12, 4: 3, 11: 10}`, malefic set `{Saturn, Mars, Rahu, Ketu}` (`pipeline/orchestrator/writers/bo_karanajala.py:387-390, 409, 548`). Stored edges, canonical chart, Lahiri: 24 (15 `argala_positive`, 9 `argala_virodha`, 2 cancelled); the same shape in the other four ayanamshas (surya_siddhanta 15 + 8) `[db]`. All 119 canonical-chart argala edges carry `constituent_fact_ids_array = {}` (empty), citation `BPHS_Ch28/argala`, tier `documented_approximation` `[db]`; the writer defaults the array to empty (`:1521-1522`) `[code]`. No `bo_*` writer reads any of the three L1 argala categories (grep over `platform/` for the three category names finds only L1 migrations and comments in `ka_yojaka.py`) `[code]`.
- **Rebuild blast radius** (live `asset_registry.depends_on`, transitive closure, `is_active`) `[db]`: a `ga_structural` rebuild reaches 55 declared dependents (3 L1, 20 L2, 12 L3, 9 L4, 11 L5); a `bo_karanajala` rebuild reaches 44 (13 L2, 11 L3, 9 L4, 11 L5). `bo_karanajala` declares no edge to `ga_structural`, but `ga_structural` is in its transitive closure through `ga_vichara`, so a new read of `ga_structural`'s categories needs no new edge (the reads-match detector accepts any producer in the declared transitive closure) `[db][brief]`.
- **Hold already in force (SS, 2026-10-01):** any L1 rebuild is held until the ephemeris boundary-flip report is reviewed (A-3 below). `ga_structural` computes through the PyJHora adapter, whose L1 `chart_facts` path the investigation (PR #2840) shows ran on the Moshier fallback. An argala-only `ga_structural` rebuild now would therefore have to be repeated after the ephemeris fix; the economical order is one `ga_structural` rebuild that carries both (recommendation under AR-6).

---

### AR-1 · Virodha pairing: which obstructor offset cancels which argala offset, and who states it

**SS ruling (2026-10-02):** (R) (a) accepted; outcome by count, "stronger" null; `virodha` = the obstruction in every layer, L2's malefic-argala class renamed; `get_argala.ts` text fixed now. J1 by name. Track I: I-14, I-17, I-19.

**Question.** Should L1 own the argala-to-obstructor pairing (2 with 12, 4 with 10, 11 with 3, 5 with 9) as a named, cited rule that L2 reads, correcting L2's current pairing?

**Facts.**
- L1 stores offsets, not pairs. A virodha cell is `virodha_score = 1.0 if the source sign holds any graha else 0.0` at an obstructing offset (`ga_structural_writer.py:4748`); nothing links it to the argala offset it obstructs. The third family, `net_argala_per_varga`, subtracts every occupant at {3, 10, 9, 12} from every occupant at {2, 4, 5, 11} with no pairing (`:7273-7295`) `[code]`. So L1 itself has no pairing and no outcome rule.
- **L2's pairing contradicts BPHS.** L2 cancels the 4th-house argala by the 3rd and the 11th-house argala by the 10th (`bo_karanajala.py:546-554`). The BPHS (Santhanam) worked example states the pairs: "The Argala of 4th house Mars is countered by 10th house Saturn, that of Sun-Mercury in the 2nd by Venus in the 12th and that of Jupiter in the 11th by Moon-Rahu in the 3rd" (`bphs_pg0312_c01`), and the chapter text adds "The 5th is also an Argala place where the planet in the 9th will counteract such Argala" (`bphs_pg0311_c01`) `[corpus]`. So the pairs are 2-12, 4-10, 11-3, 5-9; L2 has the 4th and 11th obstructors swapped. Jaimini Su. 7 gives the obstructing set {10, 12, 3} without pairing and Su. 9 adds the trikonas 5 and 9 (`bphs_jaimini_pg0023_c01`) `[corpus]`.
- **Effect size `[calc]`.** I re-ran L2's rule over the stored L1 `graha_position` sign facts (MEAN node, as L1 stores them) and it reproduces the stored result exactly (canonical chart, Lahiri: 9 malefic argala edges, 2 cancelled). With the BPHS pairing, 5 of the same 9 are cancelled and the cancelled flag differs on 7 of the 9 (the two L2 cancels are not cancels under BPHS; five new ones appear). The result is the same in krishnamurti, raman and true_chitra (9 / 2 / 5 / 7); in surya_siddhanta (8 edges) 2 / 2 and no difference. Abhinandan, Lahiri: 8 edges, 7 cancelled by the L2 pairing, 6 by BPHS, flag differs on 1.
- **Two further departures from the text, same function.** (i) L2 applies cancellation only to malefic argala (`if is_malefic:`, `:547-554`), but BPHS says an obstructed Argala "will go astray" whether benefic or malefic (`bphs_pg0311_c01`). (ii) L2's label `argala_virodha` means "argala by a malefic", while in L1 and in the served tool `virodha argala` means the obstruction (`get_argala.ts:62-65`): the same word has two meanings across the layers. (iii) Neither layer applies the outcome rule: BPHS and Jaimini say the argala prevails if its planet is stronger than the obstructor or if the argala planets outnumber the obstructors (`bphs_pg0311_c01`; Su. 8, `bphs_jaimini_pg0023_c01`); L1 scores 1.0 for any occupant and L2 cancels on any occupant `[code][corpus]`.
- A doc defect in the served tool: `get_argala.ts:64-65` describes the obstruction offsets as "3rd/12th/10th/3rd"; the ninth is missing and the third is repeated `[code]`.

**Recommendation.** Yes: L1 owns the pairing, as a named, cited rule: 2-12, 4-10, 11-3, 5-9, citing the chunks above. Store the paired offset on every L1 argala and virodha row (additive `fact_value_jsonb` key, same 144-cell structure) and give the obstruction as facts (occupants at the paired offset and their count), so the count rule (argala planets outnumber obstructors) can be applied; leave "stronger" as an honest null, because no sourced strength basis was found. L2 reads the pair from L1 and deletes its constant. Reason: SS rule 2 (L1 is the authority); CLAUDE.md §N.7 item 3 (no consumer-local constant may shadow an L1 value); the BPHS worked example settles the pairs.

**Effect.**
- (a) **L1 owns the pairing (recommended) (R).** `ga_structural` rebuilds (adds the paired-offset key to 43,200 rows per canonical chart and the obstruction facts of AR-6); then `bo_karanajala` rebuilds and reads the pair. On the canonical chart the cancelled flags in the 9 malefic argala edges change on 7 (Lahiri; `[calc]`, a rebuild may also change other fields). Downstream: the L2 closure of `bo_karanajala` (44) and the L1 closure of `ga_structural` (55) execute rather than delta-skip.
- (b) **L2 states the BPHS pairing as its own named, cited constant.** No L1 rebuild; `bo_karanajala` only. The pairing then lives in two places and L2 holds a classical constant, which §N.7 item 3 discourages; L1's own virodha rows stay unpaired.
- (c) **Keep L2's pairing.** No rebuild; the stored cancellations stay at odds with the BPHS worked example on 7 of 9 edges.

**Citation.** BPHS (Santhanam trans.) Ch. 31: `bphs_pg0311_c01` (offsets, obstructors, the 5th and 9th, prevailing rule), `bphs_pg0312_c01` (worked example with the three pairs): `sourced_ocr_unverified`. Jaimini Sutras (Suryanarain Rao trans., 1949) Su. 7-9: `bphs_jaimini_pg0023_c01`: `sourced_ocr_unverified`. The explicit "11 with 3" appears in the worked example; the translator's note in `bphs_pg0311_c01` / `_c02` is garbled by OCR for that pair, which is why the worked example is the basis.

---

### AR-2 · Rahu and Ketu: reverse the count (neither layer does)

**SS ruling (2026-10-02):** (R) (a) accepted: both nodes reversed when the node is the reference, `count_direction` in the L1 graha-level rows; Ketu-only a named stricter variant; sign matrix forward-only. J1 by name. Track I: I-14.

**Question.** When Rahu or Ketu is the reference (the one receiving the argala), should argala and its obstruction be counted in reverse order, in L1, and for both nodes?

**Facts.**
- Both texts say so. BPHS: "As the nodes have retrograde motions, the Argalas and obstructions be also counted accordingly in a reverse manner" (`bphs_pg0311_c01`); the worked example: "From Rahu, the 2nd house counted in reverse order contains Sun-Mercury causing Argala to Rahu which is, however, obstructed by Mars in the 12th from Rahu (counted in reverse manner)" (`bphs_pg0312_c01`). Jaimini Su. 10: for Ketu "the formation of Argala and obstruction to it must be calculated in the reverse order"; the commentary notes Rahu is not named in the original but "some commentators are of opinion that the mention of Ketu is enough to include Rahu" (`bphs_jaimini_pg0028_c02`, `bphs_jaimini_pg0029_c01`) `[corpus]`.
- Neither layer reverses. L1 counts forward only (`ga_structural_writer.py:4716`, `offset = ((source - target) % 12) + 1`); L2 counts forward only (`bo_karanajala.py:487-492`) `[code]`.
- **The sign matrix cannot carry it.** L1 stores a cell as 0.0 whenever the forward offset is not an argala offset (`:4727`), so a reversed argala (for example the source sign one before the target, which is forward offset 12) is stored as "no argala"; a consumer cannot rebuild the reversed reading from the existing 144 cells. The reversal is a property of a graha reference, and the sign matrix has none `[code]`.
- **Effect size `[calc]`** (stored L1 sign facts, Lahiri, D1, node as target, 16 ordered pairs = 2 nodes x 8 other grahas): canonical chart 3 argala pairs counted forward, 7 counted in reverse, membership differs on 10 of 16; Abhinandan 6 forward, 5 reverse, differs on 11; third chart 8 forward, 4 reverse, differs on 12. Pairs where a node is only the source (the causer) are unaffected; the worked example counts them normally.

**Recommendation.** Yes, reverse, in L1, for both nodes when the node is the reference. Implement it in the graha-level rows proposed at AR-6 (a `count_direction` field, `forward` or `reverse`); the sign-level matrix stays forward-only and its description says so. Both nodes, not Ketu only, because BPHS states "the nodes" and L1's convention already treats Rahu and Ketu together as MEAN nodes; the Rahu half is recorded as the named variant of Su. 10's literal text if SS prefers the stricter reading. Reason: SS rule 1 (both texts), rule 2 (the L1 node convention), §N.5.

**Effect.**
- (a) **Both nodes reversed, in L1 (recommended) (R).** New graha-level rows (AR-6); `ga_structural` rebuild; then `bo_karanajala`, whose node-targeted edges change (the 10 of 16 pairs above on the canonical chart, before pairing).
- (b) **Ketu only (the literal Su. 10).** As (a) with the Rahu rows forward; smaller change; Rahu then disagrees with the BPHS worked example, which reverses for Rahu.
- (c) **L2 reverses, L1 does not.** No L1 rebuild; the reversal becomes an L2 rule, and L1's graha references stay forward.
- (d) **Status quo.** No rebuild; node-targeted argala stays wrong on the pairs above.

**Citation.** BPHS Ch. 31, `bphs_pg0311_c01`, `bphs_pg0312_c01`: `sourced_ocr_unverified`. Jaimini Su. 10, `bphs_jaimini_pg0023_c01`, `bphs_jaimini_pg0028_c02`, commentary `bphs_jaimini_pg0029_c01`: `sourced_ocr_unverified`.

---

### AR-3 · An empty source sign scores 1.0 in L1

**SS ruling (2026-10-02):** (R) (a) accepted: NULL with `no_occupant`; formula stays `unsourced`; BPHS count grading post-J1. Track I: I-15.

**Question.** Should an argala cell whose source sign holds no graha be stored as a null (no claim) instead of the current score of 1.0?

**Facts.**
- At an argala offset the cell starts at `net_argala = 1.0` and loses 0.25 per malefic occupant; an empty sign loses nothing, so it stays 1.0 (`ga_structural_writer.py:4719-4727`; malefic set `{Saturn, Mars, Sun, Rahu, Ketu}`, `:4704`) `[code]`. The virodha cell, by contrast, is occupant-based (`1.0 if occupants else 0.0`, `:4748`), so the two families are asymmetric.
- **Measured `[db]`.** Canonical chart: 7,200 argala-offset cells (30 divisional charts x 5 ayanamshas x 48); 3,444 of them (47.8%) have an empty source sign, and all 3,444 are stored at 1.0. In D1, Lahiri, the same 48 cells split 24 occupied / 24 empty. Concrete rows (D1, Lahiri): Aries from Cancer (offset 4) and from Leo (offset 5) read "argala from Cancer (offset 4): score 1.00 (argala)" and "... Leo (offset 5): score 1.00 (argala)", while the graha-position facts put no graha in Cancer or in Leo (Moon in Aquarius, Rahu in Taurus, Sun and Mercury in Capricorn, Saturn and Mars in Libra, Venus and Jupiter in Sagittarius, Ketu in Scorpio).
- The served tool tells readers these cells measure "which grahas intervene" (`platform/src/lib/retrieval/registry/layers/L1_ganita/get_argala.ts:62-63`), so the empty cells are read as interventions `[code]`.
- The score formula (1.0 base, minus 0.25 per malefic occupant) has no corpus source I could find. BPHS grades argala by the number of planets (one gives limited results, two medium, more than two excellent) and by benefic or malefic character (subhargala is favourable) (`bphs_pg0311_c01`, `bphs_pg0311_c02`) `[corpus]`.

**Recommendation.** Yes: an empty source sign stores `fact_value_num = NULL` with `fact_value_text = 'no_occupant'`; the 144-cell structure and the count assertion are untouched (a NULL is still a row). The occupied-cell formula stays for now, labelled in the citation as a project convention (`unsourced`). Whether to replace the formula by the BPHS count grading (limited, medium, excellent) is a separate ruling (option (b) below). Reason: CLAUDE.md §N.7 item 6 (an honest null beats an invented judgment), §N.8 (a score with no detector that could read false).

**Effect.**
- (a) **NULL for empty cells (recommended) (R).** 3,444 of 7,200 argala-offset cells per canonical chart change from 1.0 to NULL (other charts and any rebuilt chart in proportion); the 144-row structure and the 21,600-row total are unchanged. `ga_structural` rebuilds. Readers: the served `get_argala.ts` (the `all_zero` flag and any consumer that assumes a number); no `bo_*` writer reads these rows today; `ka_yojaka.py` mentions the net family in comments only (not traced further).
- (b) **Replace the score by the BPHS count grading.** All 7,200 values change; larger; the benefic and malefic split (subhargala / papargala) then needs one L0 definition of the natural malefics: BPHS gives the Sun, Saturn and Mars (`bphs_pg0343_c01`), which matches L1 and not L2 (AR-6).
- (c) **Keep.** No rebuild; 47.8% of the argala-offset cells assert an argala no planet makes.

**Citation.** BPHS Ch. 31, `bphs_pg0311_c01`, `bphs_pg0311_c02`: `sourced_ocr_unverified` (count grading, subhargala). The 1.0 base and the 0.25 malefic penalty: `unsourced` (no passage found). Natural malefics: `bphs_pg0343_c01`: `sourced_ocr_unverified`.

---

### AR-4 · L1 argala rows carry the `single` verification tier

**SS ruling (2026-10-02):** (a) accepted: keep `single`, correct the provenance string. Track I: I-16.

**Question.** Is `single` the honest tier for the L1 argala rows (never claimed as verified), and should the mislabelled provenance string be corrected?

**Facts.**
- Both families are built with `verif=UNVERIFIED_DEFAULT` (`ga_structural_writer.py:4737, 4759`), stored as `single` on all 45,000 canonical-chart rows `[code][db]`. The S7 ruling (CLAUDE.md §N.4, native-authorized 2026-08-06) makes `single` a permitted tier, provided a row is never stamped verified without a second derivation. No second derivation exists for these rows: every path (matrix, virodha, net count) reads the same occupancy dictionary.
- L2 weights the tier: `single` carries 0.85, `two_pass_verified` 1.00, `classical_match` 0.90 (`bodha_writers/formulas.py:535-542`) `[code]`. L2's own argala edges are stored `documented_approximation` (0.60) (`bo_karanajala.py:622`; 119/119 `[db]`).
- **A provenance label overstates the source.** The rows say `source_calculation = pyjhora_adapter.argala/pyjhora/1.0.0` (and `.../virodha_argala/...`) (`:4738, :4760`), but `pyjhora_adapter/` has no argala module (directory listing and grep, no hit): the computation is inline in the writer `[code][db]`.
- The vocabulary note names `CLASSICAL_MATCH` as the tier for a check that validates against a table the producer itself draws from (`brahmagyan/verification_vocab.py:274-282`) `[code]`; an offset table checked against itself is that case.

**Recommendation.** Keep `single`; do not upgrade. Correct the provenance string to name the writer function. Do not stamp `two_pass_verified` unless an independent recomputation from the stored `graha_position` sign facts (a different code path from the occupancy dictionary) is added and compared through `two_pass_verdict`; even then the honest ceiling for an offset lookup is `classical_match`. Reason: CLAUDE.md §N.4, §N.8.

**Effect.**
- (a) **Keep `single`, fix the label (recommended).** No tier change; L2 weights unchanged; the label text changes on the 43,200 argala and virodha rows at the next `ga_structural` rebuild, which rides AR-1 to AR-3 (no extra run).
- (b) **Add an independent check and stamp `classical_match`.** A new check in the writer; 0.85 becomes 0.90 for those rows in L2; an extra code path to maintain.
- (c) **Stamp `two_pass_verified`.** Not earned; this is the §N.8 defect class.
- Label correction alone is registry/doc-neutral for outputs except the string.

**Citation.** Not classical. citation: n/a.

---

### AR-5 · The chapter label: BPHS "Ch. 28" versus Ch. 31 in the corpus

**SS ruling (2026-10-02):** accepted as written. Track I: I-16.

**Question.** Replace the writer's "BPHS Ch. 28" label by the corpus chunk ids, marked `sourced_ocr_unverified`, and give L1 rows a classical reference they do not carry today?

**Facts.**
- L2 cites "BPHS Ch. 28" in five comments and docstrings (`bo_karanajala.py:15, 385, 388, 500, 546`) and stores `citation_ref = BPHS_Ch28/argala` on all 119 canonical argala edges (`:623`; `[db]`) `[code]`.
- In the corpus the BPHS (Santhanam trans.) chapter is headed "Chapter 31 'Argala or Planetary Intervention'" (`bphs_pg0310_c01`; text continues in `bphs_pg0311_c01`, `bphs_pg0311_c02`, `bphs_pg0312_c01`); Ch. 29 is "Bhavapadas" (`bphs_pg0298_c01`, TOC `bphs_pg0006_c01`) `[corpus]`. Chapter numbers differ between editions, so "28" is uncorroborated rather than proved wrong.
- **L1 rows carry no classical reference at all.** `citation_ref` on an L1 argala row is a generated row key (`argala_natal_matrix.D1_SIGN_1.from_sign_2_offset_2@chart=...`), `citation_human` describes the cell, and the writer comment says only "per Jaimini Sutram" (`ga_structural_writer.py:614`) `[code][db]`. `chart_facts` has a `formula_provenance_text` column that other L1 writers already use for a source sentence (`ga_sensitive_writer.py`) `[db]`.
- Jaimini Sutras (Suryanarain Rao trans., 1949): Su. 5-10 are at `bphs_jaimini_pg0023_c01`, commentary at `bphs_jaimini_pg0026_c01` to `bphs_jaimini_pg0029_c01`.

**Recommendation.** Replace the label with the citation block: "BPHS (Santhanam trans.) Ch. 31 'Argala or Planetary Intervention': `bphs_pg0310_c01`, `bphs_pg0311_c01`, `bphs_pg0311_c02`, `bphs_pg0312_c01`; Jaimini Sutras (Suryanarain Rao trans.) Su. 5-10: `bphs_jaimini_pg0023_c01`, `bphs_jaimini_pg0028_c01`, `bphs_jaimini_pg0028_c02`", state `sourced_ocr_unverified`, put it in `formula_provenance_text` for L1 rows and in `citation_ref` / `citation_human` for the L2 edges. Move any row to `sourced` only after a passage-level check against the print (a Track I research item, spot-checked at the milestone review). Reason: B.3; the citations rule.

**Effect.** Citation strings only; no value or row-count change. It rides the `ga_structural` and `bo_karanajala` rebuilds that AR-1 to AR-3 and AR-6 already need (no separate run). If SS rules none of those, it is a string-only rebuild of 45,000 L1 rows and 119 L2 rows that is not worth a run on its own; keep it for the next scheduled rebuild.

**Citation.** As above, all `sourced_ocr_unverified`.

---

### AR-6 · Which offsets are canonical, and does L2 consume the L1 rows or recompute

**SS ruling (2026-10-02):** (R) (a) accepted: L1 offsets canonical, {2, 4, 11} a named filter; L1 graha-level family, D1 only; L2 reads and cites it and deletes its constants and malefic set; one L0 benefic/malefic definition if a label is needed; binding sequence (one `ga_structural` rebuild with the ephemeris fix after G-EPH and G-FLIP, then `bo_karanajala` in the S-L2 batch); migration 1219. Track I: I-14, I-18, I-19, I-20.

**Question.** Is L1's set {2, 4, 5, 11} with obstructors {12, 10, 9, 3} the canonical one (L2's {2, 4, 11} then a named variant), and should L2 build its argala edges from L1 fact rows instead of recomputing?

**Facts.**
- BPHS and Jaimini agree on the basic set {2, 4, 11} and both state the 5th as an extension obstructed by the 9th: "The 5th is also an Argala place where the planet in the 9th will counteract such Argala" (`bphs_pg0311_c01`); Su. 9, trikonas 5 and 9 (`bphs_jaimini_pg0023_c01`, commentary `bphs_jaimini_pg0028_c01`) `[corpus]`. So L1's set is the full reading, not a different tradition; L2's is the basic subset.
- **Pairs `[calc]`** (stored L1 sign facts, canonical, Lahiri, 9 grahas): 24 ordered graha pairs at {2, 4, 11}, 28 at {2, 4, 5, 11}, of which 4 at the 5th; obstructor pairs at {12, 3, 10} 24 and 4 at the 9th. L2 therefore omits 4 of 28 argala pairs (14%) and the 9th-house obstructions.
- **L2 does not consume L1.** It reads graha signs, computes graha-to-graha edges, and cites no L1 fact (`constituent_fact_ids_array` empty on 119 of 119; no `bo_*` reader of the three L1 categories) `[db][code]`. L1's rows are sign-to-sign and carry no occupant, so L2 cannot derive graha edges from them alone; it would have to join `graha_position` signs itself and apply the pairing and reversal.
- BPHS: "Argalas should be counted from a sign or a planet as the case may be" (`bphs_pg0311_c01`): both a sign-level and a graha-level reading are classical. L1 offers only the sign level.
- **Malefic set.** L1 `{Saturn, Mars, Sun, Rahu, Ketu}` (`ga_structural_writer.py:4704`); L2 `{Saturn, Mars, Rahu, Ketu}` (`bo_karanajala.py:409`). BPHS: "Malefics are the Sun, Saturn and Mars", with the nodes treated separately (`bphs_pg0343_c01`, `bphs_pg0343_c02`) `[corpus]`; L0 has no benefic or malefic vocabulary (`brahmagyan/graha_vocabulary.py` has none) `[code]`. L1's set agrees with the text; L2 leaves out the Sun.
- Not modelled by either layer (recorded, not asked): malefics in the 3rd as a separate evil argala and "three or more malefics in the 3rd give vipareeta (harmless, favourable) argala" (`bphs_pg0311_c01`; Su. 6, `bphs_jaimini_pg0023_c01`).

**Recommendation.** (1) Canonical offsets: L1's {2, 4, 5, 11} with obstructors {12, 10, 9, 3} and the pairs of AR-1; {2, 4, 11} is recorded as a named variant ("basic set"), produced if ever needed as a filter over the same rows (exclude offset 5 and its 9th obstruction), never as a second definition. (2) L2 consumes L1: L1 adds a graha-level family in `ga_structural` (working name `argala_graha_natal`; D1 first, other divisional charts only on a later ruling): per (target graha, source graha) at an argala offset, the offset, `count_direction` (AR-2), the paired obstruction offset (AR-1), the obstructing grahas and the argala and obstructor counts, and an outcome of `argala_prevails`, `obstructed` or `undetermined` (equal counts: strength comparison is null, because no sourced basis exists). L2 builds its edges from those rows and cites their `fact_id`s, deleting its constants and its own malefic set (classification of benefic or malefic stays out of the L1 rows; if a label is needed, one L0 definition with BPHS's Sun, Saturn and Mars plus the nodes). (3) Sequence: one `ga_structural` rebuild that carries AR-1 to AR-6 and the pending ephemeris fix (so the 55 dependents execute once), then one `bo_karanajala` rebuild. Reason: SS ruling (L1 authority, L2 references), §N.5, §N.7 item 3, SS rule 2 (BPHS and Jaimini support the L1 set).

**Effect.**
- (a) **L1 graha-level rows, L2 reads them (recommended) (R).** L1: at most 72 ordered pairs per ayanamsha for D1 (360 rows per chart; 9 grahas x 8 sources x 5 ayanamshas), of which only those at argala offsets are meaningful (28 per ayanamsha on the canonical chart in Lahiri); the new category must be added to `fact_category_ownership` by a surgical migration (otherwise it joins the 4,816 `ga_structural` rows that are already unowned; see Q-L1-04 below) and to `ga_structural`'s `count_sql`/floor (floors aspirational, CLAUDE.md §N.4). L2: edges change from 24 to 28 argala pairs per ayanamsha on the canonical chart before AR-1 and AR-2 effects, gain the 9th-house obstruction, and gain real `constituent_fact_ids_array` (the 119 empty become resolvable). Rebuilds: `ga_structural` (55 declared dependents) then `bo_karanajala` (44); the single batched L2 rebuild is this one.
- (b) **L2 reads L1 sign-level cells plus `graha_position` and applies L1's pairing and reversal.** No new L1 category; L1 still adds the paired-offset key (AR-1a) and the reversal has to be coded in L2, which then holds a classical rule; `ga_structural` and `bo_karanajala` still rebuild.
- (c) **Keep L2's own set, record {2, 4, 11} as a named class (the Q-L2-21 option b).** No L1 change; L2 keeps its recomputation, contradicting the ruling that L1 is the authority; about 24 duplicated edges per ayanamsha.
- (d) **Status quo.** No rebuild; L2 stays at 24 of 28 pairs with a swapped pairing and no L1 citation.

**Citation.** BPHS Ch. 31, `bphs_pg0311_c01`, `bphs_pg0312_c01`: `sourced_ocr_unverified`. Jaimini Su. 5-10, `bphs_jaimini_pg0023_c01`, `bphs_jaimini_pg0028_c01`, `bphs_jaimini_pg0028_c02`, `bphs_jaimini_pg0029_c01`: `sourced_ocr_unverified`. Natural malefics, `bphs_pg0343_c01`, `bphs_pg0343_c02`: `sourced_ocr_unverified`. Strength basis for "stronger obstructor": `unsourced` (BPHS names strength but gives no measure here).

---

### Argala block summary

| id | short question | recommendation | (R) | rebuilds | SS ruling (2026-10-02) |
|---|---|---|---|---|---|
| AR-1 | Who owns the argala/obstructor pairing; L2's 4->3 and 11->10 contradict BPHS | L1 owns 2-12, 4-10, 11-3, 5-9 (paired offset on rows, obstruction facts); L2 reads | (R) | `ga_structural` then `bo_karanajala` |
| AR-2 | Reverse the count for Rahu and Ketu | Yes, both nodes, when the node is the reference, in L1 graha-level rows | (R) | same two |
| AR-3 | Empty source sign scores 1.0 (3,444 of 7,200 cells) | NULL with `no_occupant`; formula stays, labelled `unsourced`; count grading is a separate ruling | (R) | `ga_structural` |
| AR-4 | `single` tier on the 45,000 L1 argala rows | Keep `single`; fix the `pyjhora_adapter.argala` label; no upgrade | no | string only, rides the others |
| AR-5 | "BPHS Ch. 28" vs Ch. 31; L1 rows have no citation | Replace by chunk ids, `sourced_ocr_unverified`; L1 uses `formula_provenance_text` | no | string only, rides the others |
| AR-6 | Canonical offsets; does L2 consume L1 rows | L1 {2,4,5,11}/{12,10,9,3} canonical, {2,4,11} named variant; L1 adds graha-level rows, L2 reads and cites them; one batched `ga_structural` rebuild (with the ephemeris fix), then one `bo_karanajala` rebuild | (R) | same two; 55 and 44 dependents |

---

---

## GROUP A · Already ruled or resolved (recorded; do not re-ask)

### A-1 · Argala: L1 is the authority, L2 references

**Ruling (SS).** By CLAUDE.md §N.5 L1 is the authority for argala and L2 references it. The residual questions were ruled on 2026-10-02 (decision N-61); see the Rulings section and group B-0 above. Nothing further to ask here.

---

### A-2 · `chart_divisionals` access incident: FIXED 2026-10-01 (RLS disabled, plan D); data intact; CF-16 closed as an access incident

**Ruling (SS / coordinator).** Row-level security was disabled on `chart_divisionals` (plan D). The data is intact: canonical 24,392 rows, Abhinandan 23,542, third chart 23,542; the `chart_snapshot` canary passes for all three. Every "table empty" reading in the briefs was a reader-side artefact and is resolved; CF-16 is now an access incident, closed.

**Facts verified by me `[db]`, 2026-10-01.**
- `pg_class` for `chart_divisionals`: `relrowsecurity = false`, `relforcerowsecurity = false`; no policy rows; `suvarna_reader` reads the table.
- Rows per chart: 24,392 / 23,542 / 23,542 (canonical, Abhinandan, third); the three sum to 71,476, which equals `reltuples` (71,476) exactly. Each chart holds 33 divisional-chart ids, 27 fact categories and 6 distinct `ayanamsha_id` values.
- The unique index is unchanged: `chart_divisionals_unique_idx (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key) NULLS NOT DISTINCT`; no `fact_subject` in it (Q-L1-01).
- The `ga_vargas` integrity SQL is unchanged and still has no clause that requires rows to exist (its four conjuncts are all `NOT EXISTS`-shaped), so it still passes on an empty table (Q-L1-01).

**What this does to the briefs.** The CF-16 text (INDEX section 4 item 1, the `ga_vargas` brief gaps and FD-1, and the one-line CF-16 pointers in the other 17 briefs) and the saved `ga_vargas` census cells (Count.floor, Build.completion, Complete.depth, Vocab.identity) were written before the fix. They should be corrected in the rulings pass; this sheet does not edit them. One figure the briefs use as the "intact" test does not reconcile and is recorded as finding F-4 below: the build records say 24,400 / 38,620 / 38,620 rows, the live counts are 24,392 / 23,542 / 23,542.

**Effect.** None to rows. Registry/doc only: the CF-16 diagnosis rows become closed; the residual real items (F-A2, the non-empty guard, the cutover-gate check) are asked at Q-L1-01.

**Citation.** Not classical. citation: n/a.

---

### A-3 · First-class finding: the canonical ephemeris backend is Swiss `.se1`; production L1 and `panchanga_daily` ran on the Moshier fallback

**SS ruling (2026-10-02):** (R) recorded; the L1 side (I-21) is mandatory before S-L1, behind G-EPH and G-FLIP.

**Ruling (SS).** The Swiss file backend (`swieph`) is canonical. Production L1 `chart_facts` and `panchanga_daily` were computed on the Moshier fallback (proven by reproduction, investigation PR #2840, `00_ARCHITECTURE/briefs/suvarna/exec/INVESTIGATION_EPHEMERIS_BACKEND_v1_0.md`). A fix PR and a boundary-flip report for all three charts are in progress. **Any L1 or panchanga rebuild is held until the flip report is reviewed.** (Sequence terms as SS names them in the N-61 ruling: G-EPH = the ephemeris fix, G-FLIP = the flip report reviewed, S-L1 = the single L1 rebuild batch, S-L2 = the single L2 batch.)

**Facts.**
- **The investigation** (read from `suvarna/land/TI-ephemeris-backend-001`, PR #2840, not re-run by me): the images set `SWE_EPHE_PATH`, which the Swiss library never reads; `set_ephe_path(None)` consults only `SE_EPHE_PATH` (set nowhere); PyJHora re-points the path to a wheel directory with no planetary `.se1` at import; the orchestrator runs assets as threads in one process, so an unchecked asset sees whatever the last writer left. Stored native Moon `327.055230133129` reproduces Moshier to 0.000 arcsec and differs from the `.se1` files by 0.665 arcsec; `panchanga_daily` likewise (0.2 to 0.9 arcsec on the Moon) `[investigation]`.
- **L1 call sites, verified at `f315b2dc2` `[code]`.** `panchang_engine/__init__.py:71, 149, 252, 347` call `swe.set_ephe_path(None)`. `ga_sade_sati_writer.py:366, 439, 1595` call `swe.set_ephe_path(os.environ.get("SWISSEPH_EPHE_PATH", "/usr/share/ephe"))`; neither the variable nor that directory is created by either image per the investigation, so the asset points at a missing directory; its docstring labels the source "swisseph/DE441" (`:1909`). `pyjhora_adapter/_jhora.py:26-43` says in its own header that "no planetary .se1 ephemeris files ship with the wheel" and names a Moshier-range failure. No L1 writer records a backend; `ephemeris_version` stores the library version, not the backend `[investigation]`.
- **Labels that still say Swiss `[db][code]`.** 180 canonical-chart `midpoint` rows read "MC from Swiss Ephemeris (swe.houses_ex ...)" in their provenance text; `ga_sensitive_writer.py:24` describes the upagraha check as "swisseph derivation"; the panchanga rows cite "Swiss Ephemeris / pyswisseph" `[investigation]`.
- **L1 briefs that name Swiss and are affected.** `ga_positions` FD (Carr D3: "a second Swiss Ephemeris call (different flags)", brief line 118), `ga_sade_sati` (D3 "second ephemeris root-find", line 116), `ga_sensitive` (D3 "upagraha Swiss-Ephemeris vs BPHS formula", lines 26, 132, 149). `ga_tajaka`'s recorded "outside Moshier planet range" error is not evidence of the backend (the investigation shows Swiss falls back to the same text for that Julian day).
- **Consequence for the proposed D3 detectors.** A D3 check that recomputes a longitude with "a second ephemeris call" compares two calls inside the same process-global state; unless the path is set explicitly and the returned flag recorded, a PASS cannot tell the two backends apart (CLAUDE.md §N.8). The Carr designs must record `retflag` or an explicit backend per run before they can read PASS.
- **Blast radius (live `asset_registry.depends_on`, transitive, `is_active`) `[db]`.** `ga_positions` has 79 declared transitive dependents (18 L1, 23 L2, 18 L3, 9 L4, 11 L5); `ga_vargas` 61; `ga_dashas` 61; `ga_sensitive` 58; `ga_condition` 51. The PyJHora-routed L1 assets are `ga_positions`, `ga_dashas`, `ga_vargas`, `ga_strength`, `ga_structural`, `ga_tajaka`, `ga_sensitive`, `ga_nakshatra`, `ga_condition`; `ga_panchanga` and `ga_sade_sati` use the engine and the missing-directory path.
- **The node convention limits the damage.** L1 uses the MEAN node (A-5), which the investigation reports as SWIEPH under every path (analytic); the 25 arcsec TRUE-node difference does not apply to L1 `[investigation][code]`.
- **Boundary margins `[calc]`** (stored `graha_position.longitude_sidereal`, Lahiri, 9 grahas plus Lagna, per chart; margin = distance to the nearest sign, nakshatra or pāda boundary, in arcseconds): Abhinandan 6,064 / 4,040 / 380 (closest to a pāda boundary: the Moon); canonical 3,020 / 3,248 / 765 (Jupiter); third chart 2,539 / 207 / 207 (Ketu, a mean node, which does not move). Against a Moon difference of about 1 arcsec, no sign, nakshatra or pāda flips on D1 in Lahiri. Not examined here: the other four ayanamshas, the finer divisional charts (D60 to D2700 are narrower than a pāda), dasha boundary dates (the Moon moves about 1,980 arcsec per hour, so 1 arcsec is about 2 seconds), tithi and yoga ends. That is what the flip report is for.

**What the ruling requires in L1 (design, not executed).** (1) Re-assert the Swiss path at the single choke point every `ga_*` passes through (`pyjhora_adapter/_jhora.py`, after the `jhora` imports) and replace the four `set_ephe_path(None)` calls in `panchang_engine` and the three `/usr/share/ephe` calls in `ga_sade_sati_writer.py` by one shared helper that sets the `/app/ephe` path, probes the returned flag and returns `{backend, path, file digest}` (investigation §7 R1 to R5; R6 would need a freeze exception, so use `WriterResult.notes`). (2) Each L1 writer writes the recorded backend into its `WriterResult.notes` (inside the frozen contract). (3) Correct the provenance strings above in the same change. (4) The D3 detectors read the recorded backend. (5) One S-L1 rebuild after G-FLIP.

**Effect.**
- **Output (R).** Every L1 position, divisional, dasha boundary, Tajaka, sensitive point and panchanga value moves by up to about 1 arcsec (Moon); stored digests change; sign, nakshatra, tithi flags can flip only near boundaries (none on D1 Lahiri for the three charts, above).
- **Rebuild.** All of S-L1 (the 11 PyJHora-routed assets plus `ga_panchanga`, `ga_sade_sati`), after G-EPH and G-FLIP; the 79 dependents of `ga_positions` execute rather than delta-skip. Every L1 question below that needs a rebuild rides this one batch.
- **Doc/registry only (now).** The three brief passages above are worded for "Swiss"; they should read "an explicit, recorded backend" in the rulings pass.

**Citation.** Not classical. citation: n/a.

---

### A-4 · Gandanta: canonical width 3°20' each side; 0°48' a named stricter variant; one shared L0 module (L1 is the existing definition)

**SS ruling (2026-10-02):** (R) recorded; the shared L0 module is mandatory before S-L1 (I-22, with X1).

**Ruling (SS).** Canonical width is 3°20' each side (one pāda); 0°48' is kept only as a named stricter variant; one shared L0 module.

**Facts.**
- **L1's existing definition conforms.** `ga_writers/ga_sensitive_degree_writer.py:194-224`: `GANDANTA_ARC = 30.0 / 9.0` (3°20'), water signs {Cancer, Scorpio, Pisces}, fire signs {Leo, Sagittarius, Aries}, `check_gandanta(sign_num, degree_in_sign)` fires on the last arc of a water sign OR the first arc of a fire sign. It is a private function inside a writer, not an L0 module; `ga_structural_writer.py:3362-3392` imports it by name from that writer (inside a bare `except Exception: fires = False`, so an import or wiring error silently reports "no gandanta") `[code]`.
- **The 0°48' reading is inside L1 under the unqualified name.** `ga_writers/ga_nakshatra_compute.py:20-21, 74-108`: junctions 0°, 120°, 240°, orb 48 arcmin each side; `ga_nakshatra_emitters.py:186-216` writes it as `graha_gandanta` / `is_gandanta`. There is no variant label on those rows `[code]`. The `chart_facts.formula_id` column is the existing variant mechanism (1,295 canonical rows use it: `bphs_93_20` / `alt_96_40` Yogi points, `kn_rao_rahu_included` / `parashari_rahu_excluded` karakas, `bphs_ch39` / `saravali` / `tajik_aapamrityu` mṛtyu points) `[db]`.
- **The two L1 assets contradict each other on a real chart `[db]`.** Abhinandan, Mars, Lahiri: 3.18° before the end of Pisces. `sensitive_degree_check.gandanta` reads `gandanta` on 7 rows (Mars in 5 ayanamshas, Venus in raman and surya_siddhanta); `graha_gandanta.is_gandanta` reads `true` on 1 row (Mars, surya_siddhanta, 12.97 arcmin). On the canonical and third charts both read false everywhere (45 and 50 rows).
- **Other places that define it.** L0 `brahma_dosha_catalog` `gandanta_dosha`: "Moon at a water-fire sign junction (last 3deg20' of Cancer/Scorpio/Pisces or first 3deg20' of Leo/Sagittarius/Aries)" with a narrative rule string the generic evaluator does not execute (no `gandanta` row in any stored `dosha_label`); L2 `bodha_writers/nakshatra_semantic_emitter.py:68-103` uses 0.8° on pāda 4 / pāda 1 `[db][code]`.
- The writer's citation names "BPHS / Sarvartha Chintamani" (`GANDANTA_CITATION`, `:201-205`).

**What the ruling requires.** (1) Move `GANDANTA_ARC`, the sign sets and `check_gandanta` to one L0 module (precedent: `domain_vocabulary.py`, `graha_vocabulary.py`, `verification_vocab.py`), imported by `ga_sensitive_degree`, `ga_structural` and `ga_nakshatra`; their source digests change once. (2) `ga_nakshatra`'s 0°48' flag becomes the named stricter variant (a `formula_id` such as `strict_0_48`) and its unqualified `is_gandanta` follows the canonical width: that is X1 below. (3) Every width carries its citation state (below). (4) The `except Exception` around the import in `ga_structural` should count and log, not hide.

**Effect.**
- Output (R): `graha_gandanta` rows change (50 per chart; Abhinandan `true` goes from 1 to 7 on the canonical width, `[calc]` from the stored sensitive-degree rows); `ga_structural`'s hardcoded gandanta rule is only in the legacy fallback and does not appear in stored data.
- Rebuild: `ga_nakshatra`, `ga_sensitive_degree`, `ga_structural` rows only where they change, in S-L1; the L0 module edit is a source-hash event for the three writers (flag to the L1 owner). L2 `nakshatra_semantic_emitter` (0.8°) and `ka_vighnakara` read the same module in their own sets.

**Citation.** BPHS (Santhanam trans.) `bphs_pg0111_c01`, translator's note: "The last Navamsas of Cancer, of Scorpio and of Pisces are called as Gandanta": `sourced_ocr_unverified` (the water side, one navamsa = 3°20'). BPHS Ch. 92 (`bphs_pg1018_c01`, `bphs_pg1019_c01`): Tithi, Nakshatra and Lagna Gandanta in ghatikas (the last half ghatika of Pisces / Cancer / Scorpio and the first half ghatika of Aries / Leo / Sagittarius for Lagna), not in degrees: `sourced_ocr_unverified`. Uttara Kalamrita `uttara_kalamrita_pg0176_c02`, `uttara_kalamrita_pg0177_c01`: the last degrees of Aslesha, Jyeshtha, Revati and the first degrees of Magha, Mula, Asvini, no width: `sourced_ocr_unverified`. **Width states:** 3°20' water side `sourced_ocr_unverified` (`bphs_pg0111_c01`); 3°20' fire side `unsourced` (a symmetric convention; BPHS Ch. 92 gives ghatikas); 0°48' `unsourced` (no passage in the code or the corpus search); the writer's "Sarvartha Chintamani" pointer `unsourced` (the corpus holds that text, 342 chunks, with no gandanta passage found); the L0 catalog's `{"chapter": 9, "text_id": "bphs"}` pointer not corroborated: `unsourced`.

---

### A-5 · MEAN node is the L1/engine convention; TRUE is a named variant

**Ruling (SS).** The MEAN node is the L1/engine convention; the TRUE node is a named variant.

**Facts `[code][db]`.** L1 pins Rahu and Ketu to the MEAN node for all ayanamshas and redirects any TRUE-node request at the lowest shared layer (`pyjhora_adapter/_jhora.py:23-55`, `positions.py:4-22`, `vargas.py:5-21`, `ga_writers/ga_vargas_writer.py:869-874`); `panchang_engine/planets.py:6-8, 118-124` forbids the TRUE node with an assertion. Stored subjects are `RAH_MEAN` and `KET_MEAN` (1,946 canonical rows); no stored subject names a TRUE node; Rahu and Ketu are exactly 180° apart (49.0330441° and 229.0330441°, canonical, Lahiri). The ayanamsha `true_chitra` is unrelated to the TRUE node (a name collision only). Not verified: that no PyJHora path reaches `swe.TRUE_NODE` without going through `drik.sidereal_longitude` (the redirect covers that function only).

**Effect.** Recorded convention; no row, registry or rebuild change. If the TRUE node is ever wanted it is a named variant (a `formula_id`), never a second default.

**Citation.** Not classical (a project convention, CLAUDE.md / Phase 4B). citation: n/a.

---

## GROUP B · Open questions (the 17 questions of INDEX section 7; the argala questions are in B-0 above)

All rebuilds below ride **S-L1** (after G-EPH and G-FLIP) and, where an L2 reader changes, the single S-L2 batch; nothing is run on its own.

### Q-L1-01 — CF-16 residual: the `fact_subject` key (F-A2), the vacuous integrity check, the cutover-gate check

**SS ruling (2026-10-02):** (R) accepted; mandatory before S-L1. Track I: I-23. F-4 (the build-record gap) is a read-only answer to SS before S-L1 (I-31).

**Question.** With the access fix done, do we widen the `chart_divisionals` unique key to include `fact_subject` (F-A2), add a non-empty clause to the `ga_vargas` integrity check, and add the cutover-gate check for a protected table with RLS and no policy?

**Facts.**
- The conflict target omits `fact_subject` and the statement is `ON CONFLICT ... DO NOTHING` (`ga_writers/ga_vargas_writer.py:2638-2661`), so rows differing only in `fact_subject` are silently dropped `[code]`.
- **Measured `[db]`:** `varga_d30_lord_per_amsa` stores 10 rows per ayanamsha (5 lords x 2 subjects) on each chart (50 per chart); the writer emits 12 signs x 5 regions = 60 per ayanamsha (`:1555-1590`: `fact_key = {lord}_{start}_{end}`, `fact_subject = D30.S{n}`), so 250 rows per chart are lost, as the briefs' "60 to 10" says.
- `mv_chart_vargas_summary` and `mv_chart_super_vargottama_bodies` read `chart_divisionals` `[db]`; their grain after a wider key was not re-read.
- The integrity SQL has four clauses, all `NOT EXISTS` (sign consistency, vargottama, D1 against `chart_facts` for the canonical chart, non-null identity); none requires a row to exist, so an empty or unreadable table passes (CLAUDE.md §N.8) `[db]`. The cutover-gate check is `[brief]`.

**Recommendation.** Yes to all three. F-A2: a surgical migration widening `chart_divisionals_unique_idx` and the two `ON CONFLICT` targets, verified by production structure, never editing 002/1035; the rows appear in the S-L1 `ga_vargas` rebuild (no extra run). Integrity: add a clause that the chart has at least one `varga_position` row per declared ayanamsha. Cutover gate: fail a protected active table with `relrowsecurity` and no policy for a serving or builder role. Reason: the fixed key is the intended grain (the writer comment says so); §N.8.

**Effect.**
- Widen the key (R): +250 rows per chart (about 24,392 to 24,642 canonical, `[calc]`); floor 22,092 then re-declared after the build (floors equal the achieved count); the two materialised views refresh. Rebuild: `ga_vargas` (61 declared dependents execute).
- Integrity clause: registry only (one surgical migration); no rebuild.
- Cutover gate: tooling only.
- Decline: the D30 lords stay collapsed to 10 of 60 per ayanamsha; the integrity check stays vacuous.

**Citation.** Not classical. citation: n/a (the D30 region table is `unsourced` in this sheet: not examined).

---

### Q-L1-02 — CF-13: declare the two missing `ga_vargas` edges; where does the daridra-cancellation pass belong

**SS ruling (2026-10-02):** (R) accepted (a): both edges AND the Daridra cancellation moved to `ga_vichara` as its own family; order-independence is a correctness fix; trace the readers of the `dosha_label` bhanga fields first. Mandatory before S-L1. Track I: I-24, I-25.

**Question.** Declare `ga_dashas -> ga_vargas` and `ga_yoga -> ga_vargas`, and move the daridra-cancellation pass out of `ga_structural`: into `ga_vichara`, a declared stale read, or a new post-yoga asset?

**Facts.**
- Live `depends_on`: `ga_dashas {ga_positions}`, `ga_yoga {ga_structural, ga_dashas}`, `ga_vichara {ga_structural, ga_strength, ga_dashas, ga_yoga}`, `ga_structural {ga_dashas, ga_nakshatra, ga_panchanga, ga_positions, ga_sensitive, ga_strength, ga_vargas}` `[db]`. `ga_dashas` reads `chart_divisionals` (`ga_dashas_writer.py:575-587`); `ga_yoga` reads D9 through `ga_structural_writer._load_varga_positions` (`ga_yoga_writer.py:2435-2445`) `[code]`. `ga_dashas` has 16 direct dependents. The dependency gate reads `lit` and fresh state, not row counts; `ga_vargas` is `lit` on all three charts `[db]`. The access fix removes the precondition the INDEX set.
- **The back-read.** `ga_structural` reads `chart_vichara` and `ga_yoga_firings` to decide whether Daridra is cancelled (`ga_structural_writer.py:2765-2830, 2839-2892`), and swallows any error as "no data" (`return None` / `return []`). `ga_yoga` is built after `ga_structural`, so on a first build the read sees nothing and on a rebuild sees the previous generation.
- **Live proof of the order effect `[db][calc]`.** Daridra (`dosha_label`, subject `daridra`): Abhinandan stored `fires = false`, `bhanga_active = true`, `bhanga_rule_fired = dhana_structure_fires:dhana_yoga_lagna_2`; the third chart stored `fires = true`, `bhanga_active = false` in all five ayanamshas. The third chart's `ga_yoga_firings` hold three dhana yogas (`dhana_yoga_2_11`, `dhana_yoga_2_5_9_11`, `dhana_yoga_house_lords`, constituent planets sun and venus), its Lagna is Cancer (lords: 2nd Sun, 9th Jupiter, 11th Venus), so the cancel rule as written (a fired `%dhana%` yoga whose planets intersect the 2nd, 9th and 11th lords) would cancel it; it is stored uncancelled. The Daridra rows were written about 15 seconds before the yoga rows on that chart (09:03:12 against 09:03:27), which is the order the DAG imposes. That a rebuild would flip the third chart's Daridra is an inference from the rule and the stored firings, not a rebuild result.

**Recommendation.** Yes to both edges (one guarded, append-only, acyclic-checked migration of the 1210 kind; with S-L1 executing everything the new upstream hash costs nothing extra). Move the cancellation into `ga_vichara`, which already follows `ga_structural`, `ga_yoga`, `ga_strength` and `ga_dashas` in the DAG and already owns the wealth ratification the cancel rule reads; `ga_structural` keeps only the detection and its grounds; `ga_vichara` writes the cancellation as its own family (not an update of `ga_structural`'s rows). Reason: removes the back-read cycle, makes the result order-independent (§N.5, §N.8).

**Effect.**
- Edges (registry): `ga_dashas` moves to level 2; no data row; consumers execute at S-L1 anyway.
- (a) Move to `ga_vichara` (R): Daridra cancellation rows move between assets (`ga_structural` loses the `bhanga_*` content of `dosha_label` for daridra, `ga_vichara` gains a family; floors 98,446 and 8,249 shift); the third chart's Daridra probably flips to cancelled; readers of `dosha_label` bhanga fields (not traced) see the move. Rebuild `ga_structural` and `ga_vichara`.
- (b) Declare a stale read: no data change; the outcome stays order-dependent.
- (c) A new post-yoga asset: a registry row, a writer and a DAG change for one family; the largest change.

**Citation.** The daridra cancellation conditions cite the L0 catalog (`classical_tradition`, `bphs:daridra:...`): not classical in the code; for the corpus: citation not found in repo, needs bg_texts lookup: `unsourced`.

---

### Q-L1-03 — CF-19: the earned verification tier (`two_pass_verified`)

**SS ruling (2026-10-02):** (R) accepted with the specifics in the Rulings section (independent re-derivation only; invariants and same-formula re-checks `classical_match`; 1,780 zero-tolerance rows `single`; per-emitter audit table to SS before S-L1; Yogi authority `bphs_93_20`). Mandatory before S-L1. Track I: I-26.

**Question.** May the `ga_sensitive` default and literal `two_pass_verified` stamps be corrected, and which tier does an invariant, a bounds check or an arithmetic re-evaluation earn?

**Facts.**
- `ga_sensitive_writer.py:373-374` defaults `verification_pass_status=TWO_PASS_VERIFIED` and `tolerance_arcsec=0.0` in `_make_row`; the Yogi/Dagdha rows pass the literal `"two_pass_verified"` (`:2650-2680`); the module header says "Every row two-pass verified" (`:9`) `[code]`. `two_pass_verdict` is called only in `ga_nakshatra.py:147`, `ga_kp_significators.py:224` and `_vimshottari_independent_verifier.py:1147` `[code]`.
- **The census SS asked for, read-only `[db]` (canonical chart, 143,299 `chart_facts` rows).** `two_pass_verified` = 9,320 rows: `ga_sensitive` 8,750, `ga_sade_sati` 320, `ga_nakshatra` 190, `ga_sensitive_degree` 60. **`ga_strength` stores none** (its rows are `single_pass` 10,575, `floored`, `computed_extension`, `single`, `documented_approximation`, `not_defined_for_nodes`, `classical_match` 14), so the brief's CF-19 reading of `ga_strength` does not apply to stored data. Of the 8,750 `ga_sensitive` rows, 1,780 (20%) carry the default `tolerance_arcsec = 0` (`tajik_hadda_lord` 1,200, `sun_derived_upagraha` 140, `lal_kitab_special_point` 100, and six smaller categories) and 6,970 carry a positive tolerance (whether each emitter really ran a second path was not read emitter by emitter).
- `ga_sade_sati`'s `two_pass_verify_cycles` checks a 7.5-year duration band and entry ordering (`:632-659`): bounds and ordering invariants, not a re-derivation. `ga_sensitive_degree`'s Yogi check re-evaluates `Sun + Moon + 93°20'` in integer arcseconds (`:506-530`): the same formula and inputs, different arithmetic.
- **L2 effect.** `bodha_writers/formulas.py:535-542`: `two_pass_verified` 1.00, `classical_match` 0.90, `single` 0.85 (the alias `single_pass` resolves to it). **The alias is stored in 10,836 canonical rows** (7.6%: `ga_strength` 10,575, `ga_panchanga` 176, `ga_structural` 85), so the CF-17 spelling clean-up is larger than the brief's `ga_panchanga` 437 rows `[db]`. `ga_panchanga` writes `single_pass` for the four FORENSIC angas on purpose (`ga_panchanga_writer.py:140-151`).
- **Yogi-point authority `[db]`.** Three categories hold it: `esoteric_point_yogi` (`ga_sensitive`; two rows per key, `formula_id = bphs_93_20` value 352.351181 and `alt_96_40` value 355.684514, labelled in provenance text "Krishnamurti variant"), `esoteric_point_yogi_system.YOGI_GRAHA` (`ga_sensitive`, 93°20', Mercury / Revati) and `sensitive_point_yogi.YOGI` (`ga_sensitive_degree`, 352.351181, Mercury / Revati). The 93°20' values agree; the 96°40' variant also doubles `esoteric_point_avayogi` (179.018 Chitra vs 189.018 Swati) and the mṛtyu, brahma, vishnu and shiva categories carry similar `formula_id` variants (955 canonical rows in seven categories sit in same-key groups, 490 of them the two karaka reckonings). `ga_sensitive_degree` re-derives the point instead of reading `ga_sensitive`'s.

**Recommendation.**
1. **Yes**, correct the default: `_make_row` defaults to `UNVERIFIED_DEFAULT`; each verified stamp is earned per emitter through `two_pass_verdict(primary, independent)` with an independent path; table lookups and relays use `CLASSICAL_MATCH`. The first act is the per-emitter audit of the 6,970 positive-tolerance rows.
2. **A bounds or ordering invariant that can fail earns `classical_match`; an arithmetic re-evaluation of the same formula from the same inputs earns at most `classical_match`; only an independent re-derivation earns `two_pass_verified`.** So `ga_sade_sati` cycles and the Yogi arcsecond check move to `classical_match`; `ga_nakshatra`'s cross-ayanamsha agreement stays.
3. **A second derivation of the four pañcāṅga FORENSIC angas from `ga_positions` longitudes: yes, later**, as a genuinely different code path read from stored L1 facts; it does not guard against a backend error common to both (A-3), so the backend is recorded.
4. **Yogi authority:** `esoteric_point_yogi` with `formula_id = bphs_93_20` (the existing convention, SS rule 2); `alt_96_40` stays a named variant; `ga_sensitive_degree` reads it rather than re-deriving (§N.7 item 3).
5. Emit the canonical spelling `single`, never the alias `single_pass`.

**Effect.**
- (a) Accept 1 to 5 (R): stored tier changes on the S-L1 rebuild: up to 1,780 `ga_sensitive` rows to `single`, the audited remainder case by case, 320 + 60 to `classical_match`, 10,836 alias rows respelled; L2 weights move 1.00 to 0.85 or 0.90 for the demoted rows (an effect for the S-L2 batch). Rebuild: `ga_sensitive`, `ga_sade_sati`, `ga_sensitive_degree`, `ga_strength`, `ga_panchanga`, `ga_structural` (spelling).
- (b) Decline: 8,750 `ga_sensitive` rows keep a strongest tier that 20% of them cannot have earned.
- Sub-answer 3 alone: no change now.

**Citation.** The Yogi point `Sun + Moon + 93°20'` and the Avayogi offsets: citation not found in repo, needs bg_texts lookup (searches for Yogi, Avayogi, Yogi Sphuta in the corpus returned no passage): `unsourced`; the writer's "BPHS Ch.20" label is uncorroborated.

---

### Q-L1-04 — CF-02: who owns which `chart_facts` rows; what counts as a writer's `rows_written`

**SS ruling (2026-10-02):** accepted; `ga_structural` owns `bhava_bala_*`; ownership rows may ride 1219; `ga_condition` multi-table, `rows_written` counts everything it writes. Mandatory before S-L1. Track I: I-30.

**Question.** Which asset owns the 420 rows both `ga_strength`'s `count_sql` and `fact_category_ownership` claim, do the 41,042 rows with no ownership row get owners, and do the rows a writer puts on `chart_facts` count as its `rows_written` (`ga_condition`)?

**Facts `[db]` (canonical chart, 143,299 rows).**
- `fact_category_ownership` has 67 rows over three owners (`ga_structural` 64, `ga_ayurdaya` 1, `ga_condition` 2) and leaves **41,042 rows with no ownership row**.
- I split those 41,042 by the live `count_sql` predicates of the declared producers: 36,226 fall inside another asset's predicate (`ga_strength` 13,721, `ga_sensitive` 8,775, `ga_sade_sati` 6,287, `ga_nakshatra` 2,847, `ga_condition` 2,835, `ga_positions` 1,205, `ga_sensitive_degree` 335, `ga_panchanga` 221); **4,816 rows in 12 categories match no predicate and no ownership row**, and the writer grep puts all 12 in `ga_structural_writer.py` only (`virupa_drishti` 2,850, `karaka_web_per_varga` 1,100, `significator_path` 360, `panchadha_maitri` 210, `conjunction_special_point` 137, `nakshatra_lord_relationship` 45, `tara_bala` 43, `yoga_label` 34, `kendradhipati_dosha` 20, `upapada_lagna` 10, `dosha_label` 6, `nakshatra_co_tenancy` 1). Close to, but not equal to, the 4,670-row gap between `ga_structural`'s build record (106,707) and its live count (102,037): 102,037 + 4,816 = 106,853, 146 more than the record; not reconciled.
- **The 420 rows are `bhava_bala_*`** (7 categories x 60). `ga_strength`'s predicate has `LIKE '%bhava_bala%'`; the ownership table gives them to `ga_structural`, and the writer emitting them is `ga_structural_writer.py` (`:60`, `:1673`). `ga_strength`'s live count 14,141 minus 420 is 13,721, within 6 of its build record 13,715; the "426" gap is 420 plus 6 `[db][code]`.
- `ga_condition`: `count_sql` = 45 composite rows + 2,925 `chart_facts` rows; its per-varga avastha writer `_insert_per_varga_avastha_rows` returns nothing (`ga_condition_writer.py:1183-1215`, `:1692, 1701`), so `rows_written` = 45 beside 2,925 written `[code][db]`.

**Recommendation.** (1) `ga_structural` owns the `bhava_bala_*` rows; narrow `ga_strength`'s predicate to its own categories. (2) Complete `fact_category_ownership` for every producer (the migration-842 pattern): the 12 `ga_structural` categories, and the other eight producers' categories, so there is one ownership mechanism rather than two; add the writer-constants-to-ownership parity test. (3) Yes: the rows a writer puts on `chart_facts` count as its `rows_written` (`ga_condition` reports all it writes); per SS's earlier Q19 answer `count_sql` scopes to the primary table and the asset is declared multi-table.

**Effect.** Registry rows and counts only: no `chart_facts` row changes. The ownership additions can ride migration 1219 or take their own surgical number; floors re-declared in the same migration from the achieved counts (floors equal the achieved count): on the canonical chart `ga_condition` goes from 2,970 to 135 (composite plus its owned rows) or 45 (primary table only), `ga_strength` from 14,141 to 13,721, `ga_structural` from 102,037 to 106,853. `ga_condition`'s `rows_written` change takes effect on its next dispatch (S-L1).

**Citation.** Not classical. citation: n/a.

---

### Q-L1-05 — CF-06: is a fixed-vocabulary threshold grade narration for the Null/Narr gates

**SS ruling (2026-10-02):** accepted: narration; declare and golden-test. Now (pre-approved). Track I: I-40.

**Question.** Are `direction_impact` (`ga_vastu`), `indication_strength` (`ga_medical`) and `strength_label` (`ga_yoga`) narration under the Null/Narr gates?

**Facts.** Each is a fixed label that grades a stored value against thresholds: `ga_vastu_writer.py:52-67` (`< 0.4` weakened, `< 0.7` neutral, else strengthened; NULL gives `neutral`), `ga_medical_writer.py:75-98` (`< 0.4` strong, `<= 0.6` moderate, else mild; NULL gives `unknown`) `[code]`. CLAUDE.md §N.7 item 5: the sentence that grades a value needs its own golden test; §N.7 item 6: a default that reads as a judgment is invented. Declarations 1.6.0 leave `prose_fields` null for `ga_medical`, `ga_vastu`, and incomplete for `ga_yoga` (INDEX section 4, CF-06).

**Recommendation.** Yes, narration: declare `["direction_impact"]`, `["indication_strength"]` and extend `ga_yoga` to `derivation`, `strength_label`, `bhanga_na_reason`, with a golden-value test at each cut point. Reason: they grade a computed value in words.

**Effect.** Declaration plus tests only; no row change, no rebuild. Decline: three assets stay NO_DETECTOR on Null and Narr.

**Citation.** Not classical (project thresholds). citation: n/a.

---

### Q-L1-06 — CF-04: does Dens read per partition for the shared-table producers

**SS ruling (2026-10-02):** accepted: per partition; add the tier where missing. Now. Track I: I-41.

**Question.** Should the Dens inspector read the served surface per `fact_category` partition for the seven `chart_facts` producers, and which served selects still lack a tier column?

**Facts.** Seven producers declare `natural_key_partition` and a partition-scoped `count_sql` live `[db]`. The brief lists `get_argala.ts` among the served selects with no tier column; **its main select does carry `verification_pass_status`** (`platform/src/lib/retrieval/registry/layers/L1_ganita/get_argala.ts:135-136`); the two other selects in that file are aggregates (`:148`, `:169`), which is the likely source of the scanner's PARTIAL (inference, not run). `get_condition_composite.ts`, `get_transit_anchors.ts`, `get_vichara.ts`, `get_yoga_firings.ts`, `get_prashna_lagna.ts` do not select a tier (`grep`: 0 tier references) `[code]`. `uniform_authority` does not fit: stored tiers are mixed (A-3, Q-L1-03).

**Recommendation.** Yes, per partition via the declarations `carriage.served_surface`; add the tier to the selects that lack it (additive fields); correct the INDEX list for `get_argala.ts`; have the scanner read the primary select of a module. Reason: the rev-4 rule and the mixed-authority ruling (L0 Q2).

**Effect.** Inspector change (Track E) plus additive response fields; no row change; no rebuild.

**Citation.** Not classical. citation: n/a.

---

### Q-L1-07 — CF-10: does `ga_positions` need a clean asset-set rerun

**SS ruling (2026-10-02):** accepted: no standalone rerun; the abort cause is a read-only answer to SS before S-L1 (I-31).

**Question.** Is a separate clean rerun of `ga_positions` needed to clear its Build.history FAIL?

**Facts `[db]`.** The latest `ga_positions` run is an `asset_set` run on the canonical chart created 2026-09-19 22:48, state `aborted`, no error text; the runs before it (2026-09-07, four of them) are `complete`, and a 2026-09-05 `error` (UUID serialization, fixed) precedes them. `asset_throughput` reads `lit`, 1,205 rows, for all three charts. The ledger gives no cause for the abort (it post-dates the RLS cutover of 2026-09-18, but `ga_positions` does not read `chart_divisionals`). Under the L0 Q11 answer Build.history counts only runs since the last change to the writer or registry row.

**Recommendation.** No separate rerun. `ga_positions` is rebuilt in S-L1 anyway (the ephemeris fix sits at its choke point, A-3), and that clean run supersedes the abort; ask the run-ledger owner why the 09-19 run aborted before S-L1 starts.

**Effect.** None now; a standalone rerun would be a production run that S-L1 makes redundant.

**Citation.** Not classical. citation: n/a.

---

### Q-L1-08 — CF-12: the Idem claim for delete-then-insert writers

**SS ruling (2026-10-02):** accepted. Now (Track E). Track I: I-42.

**Question.** Is "no orphan rows under the writer's own partition" the Idem claim for L1 delete-then-insert writers whose delete scope follows the rows written?

**Facts.** Delete scopes are built from the rows about to be written: `replace_prior_chart_facts` deletes `chart_id` x categories present x ayanamshas present (`ga_writers/_idempotency.py:54-72`), `replace_prior_chart_dashas` by system, `replace_prior_chart_divisionals` by varga, `replace_prior_tajik_varsha` by exact year triples `[code]`. A category a rebuild stops emitting is never deleted. I did not run an orphan census; the only partition check I ran (A-2, Q-L1-04) found no category in the canonical chart that no writer emits (the 12 `ga_structural` categories are emitted, only unowned). The `ga_tajaka` window grows with the clock, so no orphans arise from it (Q-L1-14).

**Recommendation.** Yes, confirm: Idem PASS = zero live keys under the writer's own partition (`natural_key_partition`, migrations 868-874, or its table scope) that its produced-key set (dry run) does not contain; a prune is scoped to that partition; the proof is the rebuild-twice fingerprint.

**Effect.** Definition and Track E tooling only; no row change.

**Citation.** Not classical. citation: n/a.

---

### Q-L1-09 — CF-07: the verified subset as the Carr PASS population; D2 for āyurdāya

**SS ruling (2026-10-02):** accepted. Now (Track E). Track I: I-42.

**Question.** Is the verified subset the PASS population for D3 (never presence), and is D2 (three method rows, none an average) the carriage check for `ga_ayurdaya`?

**Facts.** Carr is NO_DETECTOR on all 19 (census). The second derivations in code are `_vimshottari_independent_verifier.py`, `compute_cross_ayanamsha_agreement` / `two_pass_verdict` (`ga_nakshatra`), the upagraha tolerance (`ga_sensitive`); `ga_sade_sati` and Yogi checks are invariants and arithmetic re-evaluations (Q-L1-03). A-3: a second call inside one process-global backend does not discriminate backends.

**Recommendation.** Yes to both. A D3 detector reports verified, unverified and divergent counts per asset partition and PASSES only on the verified subset; a detector built on an invariant or an arithmetic re-evaluation reads PARTIAL, not PASS; every detector ships a seeded mismatch it must catch; every detector records the backend (A-3). D2 for `ga_ayurdaya`: three method rows exist and none is an average (`ga_ayurdaya_writer.py:134-137`; stored `PINDAYU` 98.75, `NISARGAYU` 99.19, `AMSAYU` 36.34 years, canonical, Lahiri) `[db]`.

**Effect.** Track E tooling; no asset or row change.

**Citation.** Not classical. citation: n/a.

---

### Q-L1-10 — `ga_ayurdaya` (enrich): the harana enrichment, and may it read other producers' facts

**SS ruling (2026-10-02):** (R) accepted; NOW (pre-approved, display side): the served totals say they are unreduced base figures (I-36). The enrichment is OPTIONAL and only for rules at least `sourced_ocr_unverified` (the three Pindayu haranas); additive, each reduction named (I-32).

**Question.** Is the harana (cancellation) enrichment in the first L1 wave, and may it read `ga_structural` / `ga_condition` facts through new `depends_on` edges?

**Facts.** The writer stores base totals only (`apply_haranas=False`, `ga_ayurdaya_writer.py:134-137`; `harana_status: base_only_haranas_deferred_to_w3`, `:224, 242`) `[code]`. **The stored totals are unreduced**: canonical, Lahiri, Pindayu 98.75, Nisargayu 99.19, Amsayu 36.34 years, `harana_status` on each total, tier `single` `[db]`. `ga_ayurdaya` has 0 declared dependents and depends only on `ga_positions` `[db]`; its served reader is `get_ayurdaya.ts`. The inputs a harana needs exist as L1 facts: `graha_position.combustion_state` (`ga_positions`), dignity and sign-lordship facts (`ga_structural`, `ga_condition`) `[db]`.

**Recommendation.** Yes, in S-L1, staged: first the three BPHS Pindayu haranas computed from stored L1 facts (combustion, enemy sign, the 12th-to-7th house reduction, with the rule that only the largest reduction applies), emitted beside the base totals, never replacing them, each applied harana named; Nisargayu and Amsayu keep `base_only` until their rules are sourced; Krurodaya and Chakrapata follow Brihat Jataka Ch. 7. New edges: yes (to `ga_structural` and/or `ga_condition`; `ga_ayurdaya` has no dependents, so nothing downstream moves). Until then the served totals should say they are unreduced base figures. Reason: the tier text asks for cancellations; an unreduced near-100-year figure served without that note overstates (Ethical Framework: probabilistic, calibrated outputs).

**Effect.** (R) additive fact keys on 130 rows per chart (existing keys unchanged); `ga_ayurdaya` rebuild in S-L1; it moves from level 1 to a later level; `get_ayurdaya.ts` shows more keys; floor refresh. Decline: the base totals stay the only longevity figures.

**Citation.** BPHS Ch. 43 (Pindayu): `bphs_pg0420_c01` (the reduction method), `bphs_pg0420_c02` (Vyayadi Harana), `bphs_pg0421_c01`, `bphs_pg0422_c01`, `bphs_pg0423_c01` (only the highest reduction applies), `bphs_pg0424_c01` (Shatru-kshetra Harana worked example): `sourced_ocr_unverified`. Brihat Jataka Ch. 7: `brihat_jataka_pg0193_c01` (Krurodaya): `sourced_ocr_unverified`. Chakrapata: only a mention in the Dasa context was found (`brihat_jataka_pg0207_c01`), not the Ayurdaya rule itself: `unsourced`. The astangata (combustion) rule's exact wording was not isolated: `unsourced` until read.

---

### Q-L1-11 — `ga_yoga` (enrich): the 63 to 53 shortfall; the DP05 fields

**SS ruling (2026-10-02):** (R) accepted: offline dry run authorised, read-only (I-37, now); `partial_formation_pct` deferred; floor = achieved count after S-L1; activation periods and D9 lineage by natural key OPTIONAL (I-33).

**Question.** May SS authorise the read-only per-yoga comparison of the last two builds, and are `partial_formation_pct`, `activation_dasha_periods` and a D9 lineage id in the first wave?

**Facts `[db]`.** `ga_yoga_firings` holds one generation per chart (one `build_id` each); the writer deletes and reinserts, so "the last two builds" cannot be compared from the table. Rows: canonical 53 (11, 11, 10, 10, 11 per ayanamsha), Abhinandan 69, third chart 80; the registry floor 63 was set by migration 650 as the minimum across three charts on 2026-09-05. A floor over a chart-dependent count is a category error: a chart simply has the yogas it has. Of the 53 canonical firings only 3 cite D9 (one in each of three ayanamshas), so the corrected D9 positions can explain at most 3 of the 10 missing rows; the rest is unexplained. D9 loading degrades silently (`ga_yoga_writer.py:2435-2455`: `{}` on any error, "honest degradation, logged"). `chart_divisionals.id` is `gen_random_uuid()` at insert (`ga_vargas_writer.py:2650`) and the writer's semantic `fact_id` is not stored, so a D9 lineage by row id breaks at every `ga_vargas` rebuild.

**Recommendation.** (1) Authorise an offline dry run of the writer's detectors against the stored L1 facts to reproduce the 53 and list the D9-dependent firings (read-only, no DB write); do not spend more diagnosis on the 10 rows, and set the floor to the achieved count after S-L1 (floors aspirational, §N.4). (2) `activation_dasha_periods`: yes, read from stored `chart_dashas` rows of the constituent lords, never recomputed; Nabhasa yogas get null with a stated reason. `partial_formation_pct`: defer; it is a project field with no sourced clause weights. D9 lineage: yes, as a natural-key reference (chart, ayanamsha, varga, graha, category, key) in the existing `grounds_jsonb`, not a row uuid.

**Effect.** (1) none to data; registry floor edit later. (2) (R) additive fields on 53 rows per chart; `ga_yoga` rebuild in S-L1; `get_yoga_firings.ts` shows new keys; 4 direct and 51 transitive dependents execute anyway. Decline: the DP05 clauses stay unpopulated.

**Citation.** Brihat Jataka Ch. 8 sl. 20: yogas "must be duly assigned to the planets concerned in their respective dasas", Nabhasa yogas excepted: `brihat_jataka_pg0227_c01`; "Nabhasa yogas take effect at all times and periods irrespective of any dasa or bhukti": `brihat_jataka_pg0302_c01`: both `sourced_ocr_unverified`. `partial_formation_pct`: not classical. citation: n/a.

---

### Q-L1-12 — `ga_prashna` (qualify): N/A basis and the letter

**SS ruling (2026-10-02):** accepted; the N/A rule is prepared as an `NA_RULE_DECISIONS` entry (the engine session owns the list). Track I: I-38.

**Question.** Is the registry-recorded dormancy (`data_disposition = RETAINED_AS_CAPITAL` plus the R-1 text) a sufficient basis for an N-22 N/A rule on Build.completion, Complete and Vocab, and is `qualify` the right letter?

**Facts `[db]`.** `asset_registry.data_disposition = RETAINED_AS_CAPITAL`; the volume text records the native ruling R-1 (2026-09-05): dormant by design, 0 rows is correct, the cast route is mounted and "2 charts cast 2026-06-18". Live: `ga_prashna_lagna` 5 rows and `prashna_charts` 2 rows (last cast 2026-06-18), `ga_prashna_judgment` 0; the registry `count_sql` is chart-scoped and reads 0 for the three birth charts; `asset_throughput` `lit`, 0 rows, on all three. So the facility holds data for the two cast question-moment charts; a natal build writes none by design.

**Recommendation.** Yes to the N/A rule, with the cause stated precisely: "no question-moment chart is built for a natal chart (R-1)", through `NA_RULE_DECISIONS` with SS approval, not a blanket "empty is fine"; `qualify` is the right letter.

**Effect.** Registry/declaration and inspector only; no row change; do not "fix" the zero count.

**Citation.** Not classical. citation: n/a.

---

### Q-L1-13 — `ga_transit_anchors`: lineage as a column, a declaration, or integration into `chart_facts`

**SS ruling (2026-10-02):** (R) accepted; OPTIONAL. Track I: I-34.

**Question.** How should the restated positions carry lineage?

**Facts.** The table stores sign, `natal_house_from_moon` and `natal_degree_absolute` for 9 grahas x 5 ayanamshas (45 rows per chart) with no source `fact_id` (`pipeline/orchestrator/writers/ga_transit_anchors.py:182-215`) `[code]`. **The served tool already resolves lineage at read time**: `get_transit_anchors.ts:88-111` (F-D25) re-runs a `chart_facts` filter on `graha_position` / `graha_sign_attributes` x keys `sign, longitude_sidereal, nakshatra` per subject and returns `constituent_fact_ids`; that is a superset resolved at serve time, not the exact rows the writer read. No writer reads the table; only the served tool and tests reference it (grep) `[code]`.

**Recommendation.** Add the stored `source_fact_ids` column (additive, 45 rows per chart), written from the rows the writer actually read, and have the served tool read it, keeping the serve-time resolver only as a fallback until the rebuild. Reason: §N.7 item 1 (narration reads, never re-derives); the rebuild is in S-L1 anyway and costs 45 rows; integration into `chart_facts` adds a consumer-free view as a fact family for no gain.

**Effect.** (R, additive column) one surgical migration; `ga_transit_anchors` rebuild in S-L1; the served tool changes. Declaration-only alternative: no migration, lineage stays derived at serve time. Integration: a registry and writer change for an asset with no declared dependents.

**Citation.** Not classical. citation: n/a.

---

### Q-L1-14 — `ga_tajaka`: the clock-dependent hybrid window

**SS ruling (2026-10-02):** accepted; the `rolling_horizon` rule is prepared as an `NA_RULE_DECISIONS` entry. Track I: I-38.

**Question.** Is a window that follows the build clock acceptable for an L1 correctness asset (record the reference year), or must a rebuild reproduce its recorded window?

**Facts.** `reference_year` defaults to the build year and the orchestrator never passes it (`ga_writers/ga_tajaka_writer.py:72-76, 725-734, 756-766`) `[code]`. Stored windows `[db]`: canonical varsha 1..48, 240 rows; Abhinandan 1..47, 235; third chart 1..61, 305; registry floor 240 (the canonical achieved count of 2026-06-11).

**Recommendation.** Acceptable, as a declared rolling horizon (the L3 Q-L3-12 pattern): record the reference year in the build's `WriterResult.notes` and in the registry text; fingerprints and any reproduction fix the year; Count.floor reads N/A by cause `rolling_horizon` through `NA_RULE_DECISIONS` (SS approval). Reason: the window must follow the clock to stay useful; the defect would be an unrecorded year.

**Effect.** Notes and registry/declaration only; no row change. (A rebuild in 2027 writes 245 rows for the canonical chart, not 240.)

**Citation.** Not classical (project window, A7 Q4). citation: n/a.

---

### Q-L1-15 — `ga_condition`: the four NULL composite columns

**SS ruling (2026-10-02):** (R) accepted; OPTIONAL; speed stays NULL, null-by-design, `[EXTERNAL_COMPUTATION_REQUIRED]`; the column is not dropped. Track I: I-35.

**Question.** Populate `avastha_lajjitaadi`, `avastha_sayanadi`, `speed_degrees_per_day` and `graha_yuddha_result` from L1 facts, or drop them?

**Facts `[db]`.** All four are NULL on all 135 composite rows (45 per chart); `graha_yuddha_with` is NULL too; `motion_state` is filled on 10 of 45 canonical rows (`vakra`). L1 facts exist for two of them: `graha_avastha_sayanadi` and `graha_avastha_lajjitadi` (45 rows each per chart) and `graha_yuddha_per_varga` (14 rows canonical). No stored L1 fact carries a graha's daily speed (`graha_position` keys: pada, longitude_sidereal, sign_lord, sign, house_d1, combustion_state, nakshatra, nakshatra_lord, retrograde_flag).

**Recommendation.** Populate the three that have L1 facts by reading them (reference the `fact_id`, never re-derive); for `speed_degrees_per_day` either add the speed as an L1 fact in `ga_positions` first or drop the column (B.10: no invented value; `[EXTERNAL_COMPUTATION_REQUIRED]` until computed by the engine).

**Effect.** (R) composite rows change; `ga_condition` rebuild in S-L1, which re-executes `ga_medical` and `ga_vastu`; the composite score does not use these columns (breakdown weights: varga 0.20, baladi 0.10, deeptaadi 0.20, combustion 0.15, dignity_d1 0.35). Drop: a schema migration.

**Citation.** Sayanadi and Lajjitadi are existing L1 facts with their own citations; no new classical claim. citation: n/a.

---

### Q-L1-16 — CF-17, CF-14, CF-20: tier constants; legacy `_telemetry` sites; the `condition_score` cut points

**SS ruling (2026-10-02):** (R) accepted: (a) and (c) mandatory before S-L1 (I-27, I-28); (b) the eight sites kept, declared CLI-only, with the grep guard (I-39, now). **Deviation accepted by SS on (a):** (a) is SATISFIED by the sibling module `platform/python-sidecar/brahmagyan/verification_tiers.py` (constants derived from `verification_vocab` at import; `emit_tier()` rejects the deprecated `single_pass` alias; implementation PR #2854), NOT by editing `verification_vocab.py`: editing it moved 30 writer digests (1 L0, 15 L2 including the FROZEN `bo_laksana`, 4 L3, 10 L1) and made `NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE` false (the 29 frozen L0 capsules fail closed; the L0 pin readmission test went red). SS accepted the deviation: keep the sibling module, do NOT edit `verification_vocab.py`, do not pursue the L0 pin readmission.

**Question.** (a) Add named constants for the other vocabulary members to the shared L0 module, or use `entry_for()`? (b) Remove the eight legacy `_telemetry` sites with the CLI path, or keep them declared CLI-only? (c) Where do the `condition_score` cut points live, and may the vāstu and medical scales differ?

**Facts.**
- (a) The vocabulary exports four constants (`verification_vocab.py:274-282`); `single_pass`, `floored`, `computed_extension`, `documented_approximation`, `pending_w3_verification`, `not_defined_for_nodes`, `scope_cap_sentinel` have none. My recount of quoted tier strings per writer (comparisons included; indicative): `ga_strength` 23, `ga_vargas` 21, `ga_structural` 18, `ga_sensitive` 15, `ga_panchanga` 15, `ga_sade_sati` 10, `ga_dashas` 8, `ga_sensitive_degree` 7, `ga_tajaka` 4, `ga_condition` 6, `ga_yoga` 4, `ga_positions` 3, `ga_ayurdaya` 2 (the INDEX regex counts differ slightly). One guard exists (`tests/test_ga_dashas_f_a17_bare_tier_literals.py`). An L0 edit shifts the source hash of about 24 L1 and L2 writers (`ga_dashas_writer.py:54-72`) `[brief]`.
- (b) The eight sites sit under `if owns_conn` (the standalone path): `ga_dashas_writer.py:3078`, `ga_panchanga_writer.py:1315`, `ga_positions_writer.py:693`, `ga_sade_sati_writer.py:1876`, `ga_sensitive_writer.py:3038`, `ga_strength_writer.py:1961`, `ga_structural_writer.py:8143`, `ga_tajaka_writer.py:835`. The CLI `platform/python-sidecar/scripts/run_l1_ganita_build.py` and `ga_writers/build_runner.py` still exist and are named in the L1 closure documents (grep) `[code]`.
- (c) The two cut-point sets: vāstu `< 0.4` / `< 0.7` (`ga_vastu_writer.py:52-67`), medical `< 0.4` / `<= 0.6` (`ga_medical_writer.py:75-98`), over the same `condition_score`; the labels have opposite polarity by design (low score: medical "strong" indication, vāstu "weakened"). Canonical chart, 45 composite rows `[db]`: 5 below 0.4, 20 between 0.4 and 0.6, **15 between 0.6 and 0.7 (medical "mild", vāstu "neutral")**, 5 at 0.7 or more; third chart 5 in the 0.6 to 0.7 band; no score is NULL, so vāstu's invented `neutral` for NULL is unreached on stored data. Neither threshold set has a source.

**Recommendation.** (a) Add the constants to the L0 module BEFORE S-L1 starts, so the hash shift is absorbed by the batch (S-L1 and S-L2 execute everything); emit `single`, never the alias. (b) Keep the eight sites, declared CLI-only, with a grep guard that no `ga_writers` module calls `update_asset_throughput(` outside the declared CLI; remove them when the CLI is retired. (c) The cut points live in one declared band table at the score's owner (`ga_condition`), read by both writers; the label vocabularies may differ, the cut points may not; adopt 0.4 / 0.7 (a friend-sign planet scoring 0.6 stays in the middle band in both); NULL score gives NULL / `unknown`, never `neutral`. All thresholds are labelled project conventions (`unsourced`).

**Effect.** (a) strings only; rides S-L1. (b) a guard test; no data. (c) (R) `ga_medical`: the 15 canonical rows (and 5 on the third chart) between 0.6 and 0.7 move from "mild" to "moderate"; `ga_vastu` unchanged; rebuild `ga_medical` in S-L1.

**Citation.** The medical label cites BPHS Ch. 18 for the causation framework and the vāstu directions cite "Mayamata Ch.6" (no Mayamata text is in the corpus): `unsourced`; the thresholds themselves are not classical. citation: n/a.

---

### Q-L1-17 — dispositions

**SS ruling (2026-10-02):** accepted: keep 16, enrich 2 (`ga_ayurdaya`, `ga_yoga`), qualify 1 (`ga_prashna`).

**Question.** Accept keep for 16 assets, enrich for `ga_ayurdaya` and `ga_yoga`, qualify for `ga_prashna`?

**Facts.** The evidence behind the letters is in Q-L1-10, -11, -12. Two facts found while verifying bear on `keep` letters: `ga_condition` (X2: the composite fell back to D1 dignity on 90 of 135 rows) and `ga_dashas` (the third chart's `asset_throughput` state is `incomplete`, 505,348 rows, not investigated).

**Recommendation.** Accept all 19 letters, with `ga_condition` and `ga_dashas` kept subject to X2 and finding F-8.

**Effect.** Registry/doc only.

**Citation.** n/a.

---

## GROUP B-X · Two new questions found while verifying

### X1 — `ga_nakshatra` writes the 0°48' reading as plain `is_gandanta`

**SS ruling (2026-10-02):** (R) accepted; mandatory before S-L1. Track I: I-22.

**Question.** After the A-4 ruling, should `graha_gandanta.is_gandanta` follow the canonical 3°20' width, with the 0°48' reading kept as a named variant row?

**Facts.** See A-4: `graha_gandanta` is stored without a width label; on Abhinandan it reads `true` once while `sensitive_degree_check.gandanta` reads `gandanta` seven times, so two L1 assets answer "is this graha in gandanta" differently on the same chart. The variant mechanism (`formula_id`) exists.

**Recommendation.** Yes: `is_gandanta` computes from the shared L0 module (3°20'); the 0°48' reading is emitted as variant rows with `formula_id = strict_0_48`; the junction and side keys are kept.

**Effect.** (R) `graha_gandanta` 50 rows per chart change (Abhinandan `true` 1 to 7, `[calc]`) plus the variant rows; `ga_nakshatra` rebuild in S-L1; L2 `bo_laksana` reads the category (`bo_laksana.py:302`) and sees the change in S-L2. No-answer: the contradiction stays.

**Citation.** As A-4: `bphs_pg0111_c01` `sourced_ocr_unverified`; 0°48' `unsourced`.

---

### X2 — `ga_condition` ran on a D1 fallback for two of three charts

**SS ruling (2026-10-02):** (R) accepted; fallback made visible plus an integrity clause, mandatory before S-L1 (I-29); the two affected charts are rebuilt in S-L1b.

**Question.** Should the composite refuse to score (or flag) when the divisional-chart dignity is missing, and should the two affected charts be rebuilt in S-L1?

**Facts `[db]`.** `ga_condition_composite.varga_dignity_composite` is NULL on all 90 rows of Abhinandan and the third chart; `condition_score_breakdown.varga_fallback_used` is `true` on all 90 (and `false` on the canonical chart's 45). The writer substitutes the D1 dignity score for the missing varga score and records the flag (`ga_condition_writer.py:500-501, 529`), so `condition_score` and everything that reads it (`ga_medical`, `ga_vastu`) rest on D1 alone for those charts. The composites were written 2026-08-06 and 2026-07-27, while the divisional charts for both charts existed from 2026-07-26 and 2026-07-27 08:39 (the third chart's composite, 09:02, was built after them); the RLS window began 2026-09-18, so it does not explain these rows; the cause is not established. One Abhinandan row has `condition_score = 0`.

**Recommendation.** Yes to both: the flag stays but a fallback row must be visible to readers (a served field and a Dens facet), and both charts are rebuilt in S-L1 after `ga_vargas` so the composite reads the divisional dignity; add a clause to the composite's integrity check that a fallback row on a chart with divisionals is a failure.

**Effect.** (R) 90 composite rows, then `ga_medical` and `ga_vastu` (45 rows each per chart), change on the two charts; `ga_condition` rebuild in S-L1. No-answer: two charts keep scores built on D1 alone, labelled only in a JSON key.

**Citation.** Not classical. citation: n/a.

---
## SUMMARY TABLE (one page)

(R) = raises or defines a verdict, or changes stored outputs: provisional until J1. "Ruled" = SS ruled on 2026-10-02 (N-61) or earlier. All L1 rebuilds ride S-L1 after G-EPH and G-FLIP.

| id | short question | recommendation | (R) | SS ruling (N-62) |
|---|---|---|---|---|
| A-1 (ruled) | Argala: L1 authority, L2 references | Record; residuals ruled in B-0 | | |
| A-2 (resolved) | `chart_divisionals` RLS | Record: RLS off, 24,392 / 23,542 / 23,542, CF-16 closed as an access incident; briefs' "empty" text to be corrected; build-record gap noted (F-4) | | |
| A-3 (ruled) | Ephemeris: Swiss `.se1` canonical; L1 ran on Moshier | Record as first-class finding; L1 fix at the PyJHora choke point, engine and `ga_sade_sati`; record the backend per writer; one S-L1 rebuild after G-FLIP; D3 detectors must record the backend | (R) | Recorded; I-21 mandatory |
| A-4 (ruled) | Gandanta 3°20' each side; 0°48' variant; one L0 module | L1's `check_gandanta` conforms; move to L0; `ga_nakshatra` and `ga_structural` import it; contradiction on Abhinandan Mars (7 vs 1 rows) | (R) | Recorded; I-22 mandatory |
| A-5 (ruled) | MEAN node convention | Record; TRUE node a named variant; one unverified path (PyJHora paths outside `drik.sidereal_longitude`) | | |
| AR-1 | Argala pairing (L2 swaps 4 and 11 obstructors) | L1 owns 2-12, 4-10, 11-3, 5-9; outcome by count. **Ruled, accepted** | (R) | |
| AR-2 | Rahu/Ketu reversal | Both nodes when the node is the reference, in L1 graha-level rows. **Ruled, accepted** | (R) | |
| AR-3 | Empty source sign scores 1.0 (47.8% of cells) | NULL with `no_occupant`. **Ruled, accepted** | (R) | |
| AR-4 | `single` tier on argala rows | Keep; fix the provenance string. **Ruled, accepted** | | |
| AR-5 | BPHS Ch. 28 vs Ch. 31 | Chunk ids, `sourced_ocr_unverified`. **Ruled, accepted** | | |
| AR-6 | Canonical offsets; L2 consumes L1 rows | L1 canonical, graha-level D1 family, L2 reads and cites. **Ruled, accepted** | (R) | |
| Q-L1-01 | `chart_divisionals` residuals: F-A2 key, vacuous integrity check, cutover gate | Yes to all three; D30 60 to 10 measured; +250 rows per chart in S-L1 | (R) | Accepted (R); mandatory |
| Q-L1-02 | Edges `ga_dashas`/`ga_yoga` to `ga_vargas`; where daridra cancellation lives | Declare both; move cancellation to `ga_vichara`; third chart's Daridra order effect shown | (R) | Accepted (R); mandatory (edges and ga_vichara move) |
| Q-L1-03 | Earned tier: `ga_sensitive` default, invariants, Yogi authority | Default to `single`; invariant or arithmetic re-check earns `classical_match`; Yogi authority `bphs_93_20`; 8,750 / 9,320 `two_pass` rows are `ga_sensitive`; `ga_strength` stores none | (R) | Accepted (R); mandatory; audit table to SS |
| Q-L1-04 | Row ownership, 420 and 41,042 rows, `rows_written` | `ga_structural` owns `bhava_bala_*`; 4,816 more `ga_structural` rows unowned; complete ownership; count all rows written | | Accepted; mandatory |
| Q-L1-05 | Threshold grades as narration | Yes; declare and golden-test | | Accepted; now |
| Q-L1-06 | Dens per partition; tier-less selects | Yes per partition; `get_argala.ts` already selects the tier | | Accepted; now |
| Q-L1-07 | `ga_positions` rerun | No; S-L1 supersedes; ask why the 09-19 run aborted | | Accepted |
| Q-L1-08 | Idem claim for L1 | Yes: zero orphan keys under the writer's own partition | | Accepted; now |
| Q-L1-09 | Carr D3 verified subset; D2 for āyurdāya | Yes; invariant-only detectors read PARTIAL; record backend | | Accepted; now |
| Q-L1-10 | `ga_ayurdaya` harana enrichment | Yes, staged (Pindayu haranas first); new edges allowed; stored totals are unreduced | (R) | Accepted (R); display note NOW, haranas optional |
| Q-L1-11 | `ga_yoga` shortfall; DP05 fields | Offline dry run, not a two-build diff (one generation stored); activation periods yes; D9 lineage by natural key | (R) | Accepted (R); dry run now, rest optional |
| Q-L1-12 | `ga_prashna` N/A basis; letter | Yes, precise cause; qualify | | Accepted; NA entry prepared |
| Q-L1-13 | `ga_transit_anchors` lineage | Stored `source_fact_ids` column; serve-time resolver already exists | (R) | Accepted (R); optional |
| Q-L1-14 | `ga_tajaka` rolling window | Accept as `rolling_horizon`; record the reference year | | Accepted; NA entry prepared |
| Q-L1-15 | `ga_condition` NULL columns | Populate three from L1 facts; speed needs an L1 fact first or drop | (R) | Accepted (R); optional, speed null-by-design |
| Q-L1-16 | Tier constants, `_telemetry` sites, cut points | Constants before S-L1; keep sites declared CLI-only; one band table 0.4 / 0.7 | (R) | Accepted (R); (a) satisfied by sibling module `verification_tiers.py` (PR #2854, `verification_vocab.py` not edited; SS deviation), (c) mandatory, (b) now |
| Q-L1-17 | Dispositions | Accept 16 keep, 2 enrich, 1 qualify | | Accepted |
| X1 | `ga_nakshatra` 0°48' written as plain `is_gandanta` | Canonical width in `is_gandanta`; 0°48' as `formula_id` variant rows | (R) | Accepted (R); mandatory |
| X2 | `ga_condition` fell back to D1 on 90 rows | Make it visible; rebuild both charts in S-L1 after `ga_vargas` | (R) | Accepted (R); mandatory; other charts S-L1b |

---

## Findings beyond the briefs (found while verifying; each has its evidence above)

- **F-1 Argala (the B-0 block):** L2's 4th and 11th obstructors are swapped against the BPHS worked example (the flag differs on 7 of 9 edges, canonical Lahiri); 47.8% of argala-offset cells are empty-sign 1.0; the node reversal cannot be carried by the sign matrix; L2's malefic set omits the Sun; a provenance string names a PyJHora module that does not exist; `get_argala.ts:64-65` lists the obstruction offsets wrongly.
- **F-2 Moshier in L1 is wider than the briefs say:** `ga_sade_sati` points at a missing directory by name; the Carr D3 designs compare two calls in one process-global backend; 180 `midpoint` rows still say "from Swiss Ephemeris".
- **F-3 Gandanta:** four definitions across L0, L1 and L2; two L1 assets disagree on a real chart (Abhinandan Mars 7 rows vs 1).
- **F-4 `chart_divisionals` build records do not reconcile:** the last build records say 38,620 rows for Abhinandan and the third chart; each holds 23,542 (15,078 fewer, 39%); the canonical chart is consistent (24,400 vs 24,392). The briefs tested "intact" against the build records. The live counts sum to `reltuples` exactly. Unexplained; the S-L1 fingerprint should settle it.
- **F-5 Daridra cancellation order effect shown in data** (third chart uncancelled while stored dhana firings would cancel it; rows written 15 seconds before the firings).
- **F-6 The 4,816-row ownership gap is `ga_structural`'s own 12 categories; the 420-row "overlap" is `ga_strength`'s predicate over-claiming `bhava_bala_*`; `ga_strength` stores no `two_pass_verified` at all** (the brief's CF-19 reading of it does not hold on stored data); the `single_pass` alias is on 10,836 rows, not 437.
- **F-7 `ga_condition` composite fallback:** `varga_dignity_composite` NULL and `varga_fallback_used = true` on all 90 rows of two charts, with no RLS explanation.
- **F-8 `ga_dashas` for the third chart is `incomplete`** (505,348 rows) in `asset_throughput`; the latest `ga_positions` run (2026-09-19) aborted with no error text.
- **F-9 `ga_yoga` keeps one generation;** the proposed two-build comparison cannot be made from the table; the floor 63 is a cross-chart minimum for a per-chart count; `chart_divisionals.id` is a fresh uuid per insert, so a D9 lineage by row id would not survive a rebuild.
- **F-10 `get_transit_anchors.ts` already resolves lineage at serve time (F-D25);** the brief says the table has none and proposes a column; both are true, the column makes it stored.
- **F-11 `ga_ayurdaya` serves unreduced longevity totals (98.75, 99.19 years for the native)** with only a `harana_status` note; the Ethical Framework bears on how that is shown.
- **F-12 `ga_prashna` is not empty:** 5 `ga_prashna_lagna` rows and 2 `prashna_charts` exist for two cast question-moment charts; only the natal-chart build is empty by design.

## What I could not verify

- **Not re-run by me:** the ephemeris reproduction (A-3 rests on the investigation of PR #2840, read at its branch; I did not re-compute Moshier against `.se1`); the L2 CF-20 ruling status; the `chart_snapshot` canary (the coordinator's statement).
- **Not checked emitter by emitter:** whether each of the 6,970 positive-tolerance `ga_sensitive` rows ran a real second path (Q-L1-03); readers of `dosha_label` bhanga fields (Q-L1-02); the grain of `mv_chart_vargas_summary` after a wider key (Q-L1-01); whether `ka_yojaka` consumes `net_argala_per_varga` values (B-0).
- **Counts that need a rebuild, not a read:** the post-F-A2 row count (+250 per chart is arithmetic from the D30 table shape), the Daridra flip on the third chart (an inference from the rule and the stored firings), the flag changes in the L2 argala edges (a reproduction of L2's rule over stored L1 signs, not a `bo_karanajala` run), the Moon boundary margins outside Lahiri and the finer divisional charts.
- **Unfound corpus passages (`unsourced`):** Yogi / Avayogi Sphuta (93°20'); the fire-side Gandanta width in degrees; 0°48'; the Sarvartha Chintamani and L0 "BPHS Ch. 9" Gandanta pointers; the astangata harana wording; Mayamata; every threshold and the argala 1.0 / 0.25 score. Every passage I did find is OCR text read by me and not checked against print: `sourced_ocr_unverified`; nothing in this sheet is `sourced`.
- **Unexplained, flagged:** the 15,078-row build-record gap (F-4); the `ga_dashas` `incomplete` state on the third chart; the 2026-09-19 `ga_positions` abort; the cause of the `ga_condition` fallback (X2); the 146-row residue in the `ga_structural` count reconciliation.
- **Process note.** Rebuild effects assume SS's sequence (one S-L1 after G-EPH and G-FLIP, one S-L2); I have not read the rebuild plan or the flip report. The migration number for the key widening and the ownership rows is not allocated here (1219 is SS's for the argala ownership row only).

## Appendix · read-only evidence queries (as `suvarna_reader`, 2026-10-01 to 2026-10-02)

Run through a wrapper script that sources the credential file silently and runs `psql`; no credential is shown. All are `SELECT`.

```sql
-- A-2: RLS state, counts, index
select relname, relrowsecurity, relforcerowsecurity, reltuples::bigint from pg_class where relname='chart_divisionals';
select chart_id, count(*) from chart_divisionals group by 1;
select indexdef from pg_indexes where tablename='chart_divisionals' and indexdef ilike '%unique%';
select asset_id, target_floor, integrity_check_sql from asset_registry where asset_id='ga_vargas';
-- Q-L1-01: D30 collapse
select fact_category, count(*), count(distinct fact_subject), count(distinct (graha, varga))
  from chart_divisionals where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and ayanamsha_id='lahiri_chitrapaksha'
   and fact_category in ('varga_d30_lord_per_amsa','varga_ashtakavarga') group by 1;
-- A-4 / X1: the two Gandanta readings, all charts
select chart_id, fact_category, fact_key, fact_value_text, count(*) from chart_facts
 where (fact_category='graha_gandanta' and fact_key='is_gandanta') or (fact_category='sensitive_degree_check' and fact_key='gandanta') group by 1,2,3,4;
select canonical_id, formation_rule_jsonb::text from brahma_dosha_catalog where canonical_id='gandanta_dosha';
-- A-3: margins (graha_position.longitude_sidereal, Lahiri; distance to nearest sign, nakshatra, pada boundary, arcsec)
-- A-3: transitive dependents of ga_positions / ga_vargas / ga_dashas / ga_sensitive / ga_condition (recursive over asset_registry.depends_on, is_active)
-- A-5: RAH_MEAN / KET_MEAN subjects; no subject ilike '%true%'
-- Q-L1-02: registry depends_on; Daridra rows and firings
select chart_id, ayanamsha_id, fact_value_jsonb->>'fires', fact_value_jsonb->>'bhanga_active', fact_value_jsonb->>'bhanga_rule_fired'
  from chart_facts where fact_category='dosha_label' and fact_subject='daridra';
select chart_id, ayanamsha_id, yoga_canonical_id, constituent_planets from ga_yoga_firings where yoga_canonical_id ilike '%dhana%';
-- Q-L1-03: tier census by producer (canonical chart; producer = the live count_sql predicate of each asset)
select engine_version, verification_pass_status, count(*) from chart_facts where chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1,2;
select fact_category, count(*) from chart_facts where chart_id='482012f1-710e-4a25-994a-93821f5871aa'
   and verification_pass_status='two_pass_verified' and tolerance_arcsec=0 group by 1;   -- restricted to the ga_sensitive predicate
select fact_category, formula_id, count(*) from chart_facts where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and formula_id is not null group by 1,2;
-- Q-L1-04: ownership
select owning_asset_id, count(*) from fact_category_ownership group by 1;
select count(*), count(*) filter (where f.fact_category is null) from chart_facts c left join fact_category_ownership f using (fact_category) where c.chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- Q-L1-07: ga_positions runs
select a.state, r.created_at from build_run_assets a join build_runs r on r.id=a.run_id where a.asset_id='ga_positions' order by r.created_at desc limit 8;
-- Q-L1-11: ga_yoga_firings per chart / ayanamsha, builds
select chart_id, ayanamsha_id, count(*), count(distinct build_id) from ga_yoga_firings group by 1,2;
-- Q-L1-12: prashna tables
select (select count(*) from ga_prashna_lagna), (select count(*) from ga_prashna_judgment), (select count(*) from prashna_charts);
-- Q-L1-14: tajaka windows
select chart_id, count(*), min(varsha_year), max(varsha_year) from l1_tajik_varsha_year_lords group by 1;
-- Q-L1-15 / X2: composite
select chart_id, count(avastha_lajjitaadi), count(avastha_sayanadi), count(speed_degrees_per_day), count(graha_yuddha_result), count(varga_dignity_composite) from ga_condition_composite group by 1;
select chart_id, condition_score_breakdown->>'varga_fallback_used', count(*) from ga_condition_composite group by 1,2;
-- Q-L1-16: score bands
select chart_id, count(*) filter (where condition_score<0.4), count(*) filter (where condition_score between 0.4 and 0.6),
       count(*) filter (where condition_score>0.6 and condition_score<0.7), count(*) filter (where condition_score>=0.7) from ga_condition_composite group by 1;
-- corpus (all citations): classical_text_chunks(text_id, chunk_id, content_en) searched with ~* patterns
```
