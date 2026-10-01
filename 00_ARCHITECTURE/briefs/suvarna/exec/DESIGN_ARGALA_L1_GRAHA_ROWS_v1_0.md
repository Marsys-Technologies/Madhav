---
artifact: DESIGN_ARGALA_L1_GRAHA_ROWS
version: "1.0"
status: DRAFT-FOR-REVIEW (all (R) provisional until J1)
produced_by: exec-suvarna
produced_on: 2026-10-02
asset_id: ga_structural (L1) with the L2 follow-on for bo_karanajala
track_i_item: "TI-ARGALA: L1 graha-level argala rows"
ruling: "SS decision N-61 (2026-10-01): AR-1..AR-6 of DECISION_SHEET_L1_v1_0.md (origin/suvarna/land/A-L1-decisions-001)"
base_commit: "origin/main bf6fe712b"
scope: "DOCS ONLY. No code, no migration, no DB write. DB reads as suvarna_reader. No rebuild is run or triggered."
evidence_dir: "/Users/Dev/suvarna-evidence/TrackI/argala_l1/ (outside the repo): offline_edge_counts.py (+ .out), show_lahiri.py (+ .out), check_flags.py (+ .out), signs_canonical.psv"
changelog:
  - "1.0 (2026-10-02): first draft."
---

# Design review: L1 graha-level argala rows (AR-1 to AR-6 as ruled)

## 0. What is ruled, and what goes to J1 by name

AR-1: L1 owns the pairing **2-12, 4-10, 11-3, 5-9**; obstruction applies to benefic and malefic argala; outcome by count only (argala count > obstructor count = `argala_prevails`; fewer = `obstructed`; equal = `undetermined`). AR-2: for **both nodes**, when the node is the reference, argala and obstruction are counted in reverse, in the L1 graha-level rows (`count_direction`); Ketu-only is the named stricter variant; the sign matrix stays forward-only. AR-3: an empty source sign is NULL with `no_occupant`; the 1.0 / 0.25 formula stays as a labelled project convention (`unsourced`). AR-4: tier stays `single`, provenance string corrected. AR-5: chapter 31 chunk ids, `sourced_ocr_unverified`. AR-6: {2,4,5,11} / {12,10,9,3} canonical, {2,4,11} a named filter; L1 adds a graha-level family, D1 only; L2 builds from those rows; vipareeta and the 3rd-house evil argala are recorded, not built.

**Goes on the J1 reviewers' list by name:** (1) the pairing 2-12, 4-10, 11-3, 5-9 (the 11-3 pair rests on the worked example, because the translator's note is OCR-garbled; the 5-9 pair rests on one sentence); (2) the reversal for both Rahu and Ketu.

**Finding the ruling does not state (for SS/J1).** The BPHS worked example (`bphs_pg0312_c01`) calls all three argalas "countered". Under the ruled count-only rule they come out: Mars (1) vs Saturn (1) = `undetermined`; Sun-Mercury (2) vs Venus (1) = `argala_prevails`; Jupiter (1) vs Moon-Rahu (2) = `obstructed`. The text's own prevailing rule is "stronger OR more numerous" (`bphs_pg0311_c01`); with "stronger" left null (no sourced measure), the example's wording and the rule are not the same thing. What the example does prove is the **pairing and the identification of the obstructors**; the golden test (Part 2) asserts those, and asserts the outcomes only as the ruled count rule gives them, and says so.

## 1. (a) L1 graha-level rows

**Category** `argala_graha_natal` (AR-6's working name), owner `ga_structural`, D1 only, per ayanamsha (the writer already runs one substep per ayanamsha). One row per (target graha T, source graha B) where B stands in an argala sign of T. No rows for non-argala pairs and none for empty argala signs (an honest absence, not a stored 0).

| field | value |
|---|---|
| `fact_subject` | `D1_<T>` with `T` = `PLANET_TO_SUBJECT` code (SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN): the same `{varga}_{code}` shape as `graha_dignity_per_varga`, which `fact_identity_parser` already reads |
| `fact_key` | `from_<B>_offset_<k>` (k in 2, 4, 5, 11), unique per (T, B): B stands in one sign |
| `fact_value_text` | outcome: `argala_prevails` / `obstructed` / `undetermined` |
| `fact_value_num`, `unit` | `argala_count` (grahas in the argala sign), `graha_count` |
| `fact_value_jsonb` | `varga`, `ayanamsha_id`, `target_graha`, `source_graha`, `target_sign_num`, `argala_offset`, `obstruction_offset`, `argala_sign_num`, `obstruction_sign_num`, `count_direction` (`forward`/`reverse`), `argala_grahas`, `argala_count`, `obstructor_grahas`, `obstructor_count`, `outcome`, `outcome_basis` (`count_only`), `strength_comparison` (**null**: "stronger" stays null, no sourced measure), `offset_class` (`basic` for 2/4/11, `extended` for 5: the {2,4,11} filter, never a second definition), `pair_rule` |
| `verification_pass_status` | `single` (S7 ruling; no second derivation exists, so no upgrade) |
| `source_calculation` | the real function: `ga_structural_writer._build_argala_graha_rows/<engine>`; the sign-matrix rows change from `pyjhora_adapter.argala` / `.virodha_argala` (no such module) to `ga_structural_writer._build_argala_rows/<engine>`. Both start with `ga_structural`, which is what `bo_laksana._infer_source_l1_asset` keys on, so L2 classifies them the same |
| `formula_provenance_text` | citation block: BPHS Ch. 31 `bphs_pg0310_c01`, `_pg0311_c01`, `_pg0311_c02`, `_pg0312_c01`; Jaimini Su. 5-10 `bphs_jaimini_pg0023_c01`, `_pg0028_c01`, `_pg0028_c02`; `sourced_ocr_unverified`; the 1.0 / 0.25 score is stated as `unsourced` project convention. This needs the writer's INSERT to carry the column (it is not in `_CF_INSERT_COLS` today) |

Node reversal: for T in {Rahu, Ketu} the source sign of offset k is `((sign_T - 1) - (k - 1)) mod 12 + 1`, for the argala offset and for its paired obstruction offset. Nodes as **source** are unaffected (the worked example counts them forward). The sign-level matrix (`argala_natal_matrix`, `virodha_argala_natal_matrix`) stays forward-only and its `formula_provenance_text` says so.

**Sign-matrix changes that ride along (AR-3, AR-4, AR-5).** An argala-offset cell with no occupant in the source sign stores `fact_value_num = NULL`, `fact_value_text = 'no_occupant'` (still 144 rows per varga, so the writer's count assertion and conjunct (h27) hold); occupied cells keep the formula. Virodha cells keep their occupant-based 1.0 / 0.0. `no_occupant` is a **sign-matrix** marker: a graha row exists only because B occupies the argala sign, so it cannot be empty on that side; an empty obstruction side is `obstructor_count = 0` with `obstructor_grahas = []` (outcome `argala_prevails`).

**Idempotency.** `_insert_chart_facts_rows` calls `replace_prior_chart_facts` over the (chart, ayanamsha, category) scope present in the batch, so the new category is deleted and re-inserted per chart x natural key with no new code; `fact_id` is `sha256(category|subject|key|chart|ayanamsha)`, stable across builds. One residual: a batch with zero rows of the category would not delete prior ones; impossible for D1 (nine grahas cannot all stand in one sign).

**Registration (migration 1219, as allocated).** `fact_category_ownership` row `('argala_graha_natal', 'ga_structural')`, mirroring 842 (`ON CONFLICT DO NOTHING`). `ga_structural.count_sql` already joins that table (migration 410), so no `count_sql` edit; `target_floor` (98,446) is aspirational and is re-baselined after the one governed rebuild, not bumped now (1086 precedent). **Additional item, flagged:** `asset_output_digest_specs` holds one active ga_structural spec (`b2490646...`, 81 categories, `where_in`); a category outside that list is not digested, so changes to the new rows would not move the output digest or stale dependents. 1219 therefore also retires that spec and inserts a 82-category one, computed with `provenance.canonical_digest` (1086 pattern). Not in 1219, proposed as follow-ups: new `integrity_check_sql` conjuncts (conjunct (e27) is vacuously true on a NULL score, so nothing detects a wrongly-NULL cell today) and a `CHART_FACTS_SCHEMA.json` entry (that file already lacks `net_argala_per_varga`).

## 2. (b) L2: naming, consumers, and the one malefic definition

**`virodha` means obstruction everywhere.** L2's `argala_virodha` means "argala by a malefic" (`bo_karanajala.py:543`) while L1 and `get_argala.ts` use virodha for the obstruction. Proposal: **`argala_by_malefic`**, with `argala_by_benefic` replacing `argala_positive` for symmetry (both name the causer and claim no valence; BPHS itself says a malefic's argala can be favourable, `bphs_pg0314_c02`). `argala_virodha` is then reserved for an obstructor edge, which is not built. I did not pick the classical pair subhargala / papargala: `subhargala` is in the corpus (`bphs_pg0311_c02`, `bphs_pg0314_c02`), `papargala` is not. Minimal-blast alternative: rename only `argala_virodha` and keep `argala_positive`.

**Reader trace of `bodha_cgm_edges.relationship_class` (argala values) and `cancelled_flag`** (grep over python, ts, sql, json; nothing branches on the value outside this list):

| consumer | what it does | breaks on rename / ruling? |
|---|---|---|
| `bo_karanajala.py:168`, `:543` | `argala_virodha` forces valence `antagonistic`; class chosen by `MALEFIC_GRAHAS` | **yes**: both lines change; after the rename the forced valence is dropped and valence comes from `edge_valence` for every argala edge (values change) |
| migration 763 (`bo_karanajala` integrity SQL, line 106) | `cancelled_flag = true` only with `relationship_class = 'argala_virodha'` | **yes**: false-fails on the new name and on any cancelled benefic edge; needs a replacement migration in the L2 batch |
| `bo_pramana_mapa.py:599-604` | a cancelled edge must carry `original_polarity` (-1/1), `resulting_role`, non-empty `cancelling_roots` | no, if the L2 rewrite keeps that payload shape (it must) |
| `services/ka_kshetra/stage2_promise.py:337-339` | reads argala edges with `cancelled_flag = FALSE` | no; `undetermined` stays uncancelled, `obstructed` becomes cancelled |
| migration 976 (output digest) | hashes `relationship_class` | digest moves: expected |
| `tests/l2/test_bo_a2_fixes.py:375,395,398,413` | asserts the two names | **yes**, tests change |
| `scripts/census/generate_tci.ts:133`, `src/generated/harvest/e4_signal_classes.json` | census of distinct values | regenerate |
| `platform-mcp/.../vidhi/dossier_slices/*.json` (+ `.generated.ts`) | static snapshots of edges | stale until regenerated |
| `traverse_chart_graph.ts:1208` | selects `cancelled_flag` only | no |

**L2 `bo_karanajala` (the later batch):** build one edge per L1 `argala_graha_natal` row (from B to T), set `constituent_fact_ids_array` to that row's `fact_id` (the 119 empty arrays become resolvable), `cancelled_flag = (outcome == 'obstructed')`, delete `ARGALA_POSITIONS`, `VIRODHA_POSITIONS`, `ARGALA_TO_VIRODHA`, `MALEFIC_GRAHAS`, and its own pairing and offset loop; cite chapter 31 chunk ids instead of `BPHS_Ch28/argala`.

**One benefic / malefic definition.** Today there are four: L1 `ga_structural_writer.py:4704` {Saturn, Mars, Sun, Rahu, Ketu}; L2 `MALEFIC_GRAHAS` {Saturn, Mars, Rahu, Ketu}; `valence_doctrine._NATURAL_NATURE` (a signed local table); and the L0 table `reference_planets.natural_benefic` (a boolean: Moon and Mercury true; Sun, Mars, Saturn and both nodes false), read by `bo_pratijna_v4_engine`. `graha_vocabulary.py` and `l0_semantic_release_v1.json` carry identity and roles only. BPHS (`bphs_pg0343_c01`): malefics are the Sun, Saturn, Mars; Mercury and the Moon are conditional; the nodes are stated separately. Proposal: add `natural_class` (`benefic` / `malefic` / `conditional` / `node`) to the L0 `reference_planets` seed (`brahmagyan/l0_reference.py`) with an accessor in `graha_vocabulary.py`, read by L1 (not needed by the rows) and by L2; `valence_doctrine` and the L1 set migrate to it later. That is an L0 change (new column, `bg_reference` digest-spec revision, a migration), so it is **not** in the L1 batch; the L1 rows carry no label.

## 3. (c) Expected change on the canonical chart (reproduced offline)

Method: stored L1 `graha_sign_attributes/sign_num` (MEAN nodes) for chart 482012f1, an independent implementation (`offline_edge_counts.py`), today's L2 rule reproduced first (it matches the stored 24 edges: 15 + 9, 2 cancelled). Signs are the pre-ephemeris-fix stored values; the Moshier-path flips could change them.

| | today (L2) | ruled model |
|---|---|---|
| argala edges per ayanamsha, Lahiri / KP / Raman / True Chitra | 24 (15 benefic + 9 malefic) | **32** L1 graha rows (6 at the 5th house, 7 node-targeted) |
| surya_siddhanta (Moon in Aquarius to Pisces) | 23 (15 + 8) | **28** |
| malefic-source edges cancelled (Lahiri) | 2 of 9 | pairing only, any obstructor: 5 of the same 9 (flag differs on 7: the 2 old cancels are not cancels, 5 are new) |
| outcomes (Lahiri, all 32) | 2 cancelled | 27 `argala_prevails`, 3 `undetermined`, 2 `obstructed` |
| by source {Sun, Saturn, Mars, Rahu, Ketu} (19 of 32) | 9 edges, 2 cancelled | 16 prevail, 3 undetermined, **0 obstructed** |
| benefic obstruction (new; L2 never cancelled a benefic) | 0 | 2: Moon's argala on Mercury and on the Sun, obstructed by Jupiter-Venus in the 12th |
| node reversal effect | n/a | rows 28 (forward only) to 29 (Ketu only) to 32 (both): 7 rows are node-targeted |

Total new L1 rows on the canonical chart: 4 x 32 + 28 = **156** (D1, 5 ayanamshas; upper bound 360) against today's 45,000 argala-family rows, which are unchanged in number (43,200 sign-matrix + 1,800 net). Sign matrix, D1 Lahiri: 24 of 48 argala-offset cells become NULL (all vargas and ayanamshas: 3,444 of 7,200, per the decision sheet). Per-edge detail: `show_lahiri.out`.

## 4. (d) Readers, risks, and the pre-approved fix

- **`get_argala.ts` (pre-approved, done in Part 2).** Its description says the obstruction offsets are "3rd/12th/10th/3rd"; the 9th is missing and the 3rd repeated. Corrected to "12th/10th/9th/3rd (paired 2-12, 4-10, 5-9, 11-3)". The tool serves the sign matrix only; the new category has no served reader until a tool or facet is added (also `coverage_matrix.ts`, `concept_aliases.ts`, `signal_register_glossary.py`). Its `all_zero` flag is unaffected by NULL cells (a NULL is not 0), but its text should say NULL / `no_occupant` once the rebuild lands.
- **`ga_sade_sati_writer._lookup_argala_for_sign`** reads `argala_natal_matrix` with `fact_value_num IS NOT NULL AND != 0`: NULL-safe, but its `argala_during_period_jsonb` loses the empty-source activations (today scored 1.0). A real, correct change that executes when ga_sade_sati rebuilds.
- **`bo_laksana`** ingests every category: the new one defaults to `fact_kind = 'configuration'` unless the L2 batch adds it to `_RELATIONSHIP_CATS`; it already consumes `net_argala_per_varga` (unchanged here; the net family keeps its own local offset lists and no pairing, untouched on purpose).
- **`contradiction_pair`** derives valence from the category, not the value, so every sign already pairs argala with virodha; unaffected, and the new category stays out of `CATEGORY_FAMILY`.
- **Governance pins.** `asset_declarations.json` and `test_e6_1_declarations.py` pin ga_structural's `citation_human` site census (189 / 5 / 0 / 6) and the line numbers 1303, 1702, 4659, 4871, 4880; the new citation strings change the census and the edit moves the lines. Updated in Part 2. The writer-code digest (`nirmana-writer-digests.json`) and the capability census move.
- **Risks.** (1) The count-only outcome is the ruled reading, not the text's full rule (section 0). (2) Everything is `single` and `sourced_ocr_unverified`: the pairs for 11-3 and 5-9 stand on OCR text and one worked example. (3) `ga_structural` runs through the adapter whose L1 path used the Moshier fallback, so the stored signs behind section 3 may flip; the one rebuild with the ephemeris fix (after G-EPH and G-FLIP) recomputes all of this. (4) No rebuild is run here.

## 5. Not verified

The live `integrity_check_sql` combined result was not run (it is red today for documented reasons); no migration was applied; the 3,444 / 7,200 and 45,000 figures are the decision sheet's `[db]` numbers except the D1 Lahiri 24 / 48, re-derived from the stored signs.
