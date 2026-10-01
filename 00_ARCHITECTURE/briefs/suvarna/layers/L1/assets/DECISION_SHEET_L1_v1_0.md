---
artifact: DECISION_SHEET_L1
layer: L1 Gaṇita (ga_*)
version: "1.0"
status: "DRAFT-FOR-RULING (group B-0, the argala block, RULED by SS 2026-10-02, decision N-61; the rest awaits ruling)"
produced_by: exec-suvarna
produced_on: 2026-10-02
plan_item: A.L1 (decision sheet over the briefs; one pass for Strategic Suvarṇa)
source_branch: "suvarna/land/A-L1-briefs-001 (PR #2832, open) at f315b2dc2 (code and briefs read here); the SS rulings on the argala block are recorded in the briefs and INDEX on suvarna/land/A-L1-briefs-001-rulings (c5c3c284f, a fast-forward of the briefs branch); this sheet (suvarna/land/A-L1-decisions-001) is rebased on that tip"
source_files: "00_ARCHITECTURE/briefs/suvarna/layers/L1/assets/INDEX.md (section 7, the 17 questions) and the 19 per-asset briefs in the same directory"
scope: "docs only; no code, registry, migration or database write"
provisional: "every ruling taken from this sheet is provisional until the J1 independent review"
changelog: "1.0-early rulings (2026-10-02): SS rulings on group B-0 (decision N-61) recorded: Rulings section, a ruling line per item AR-1..AR-6, summary column; the rulings are also recorded in the L1 INDEX and the ga_structural brief on suvarna/land/A-L1-briefs-001-rulings (c5c3c284f), on which this sheet is rebased. 1.0-early (2026-10-02): first commit carries ONLY Group B-0 (the six argala items), put first at SS's priority request so they can be ruled ahead of the rest. The remainder (Group A, Group B, the full summary table) follows in the next commit of this file."
---

# L1 Gaṇita decision sheet (for one ruling pass by Strategic Suvarṇa)

> **Early commit.** This version holds the argala block only (Group B-0, items AR-1 to AR-6). Group A (already ruled), Group B (the 17 open questions of the L1 INDEX) and the one-page summary of everything follow in the next commit of this same file. The argala block is self-contained: it can be ruled on its own.

## 0 · How to read this sheet

**Structure.** Group B-0 (this commit) holds the six argala items SS asked for. Every item has the same fields: question, facts, recommendation, effect of each possible answer (outputs, which assets rebuild, doc/registry only), citation. A summary of the block closes it; the final commit replaces it by the one-page table for the whole sheet.

**Rules SS gave for rulings (applied throughout).** (1) A classical fact needs a `bg_texts` corpus citation (B.3). (2) Where traditions differ, the project's existing L1/engine convention is the authority (CLAUDE.md §N.5) and the alternative is recorded as a named variant. (3) Every ruling is provisional until the J1 independent review. (4) Items that raise or define a verdict, or change stored outputs, are marked **(R)**.

**Citation states (SS rule, applied to every citation).** An OCR text-search hit not checked against print is `sourced_ocr_unverified`. A passage I looked for and did not find is `unsourced`. Only a citation verified at passage level counts toward a PASS on Ldgr; nothing in this sheet is above `sourced_ocr_unverified`.

**Evidence tags.** `[code]` = read in the repository at `f315b2dc2` (file:line). `[db]` = read-only `SELECT` as `suvarna_reader` (2026-10-01 to 2026-10-02; queries in the appendix; no write, no credential shown). `[corpus]` = text search of `classical_text_chunks` (the chunk table of the `bg_texts` corpus); the chunk id is given so the passage can be re-found; the text is OCR and I read it, but it is not checked against the printed book. `[calc]` = a figure I computed offline from stored L1 facts read with `[db]` (method stated; not a rebuild result). `[brief]` = quoted from a brief or INDEX and not re-verified.

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

## GROUP B-0 · Argala (priority block; the bo_karanajala fix and the single batched L2 rebuild wait on this)

### What L1 and L2 hold today (shared facts for AR-1 to AR-6)

- **L1 writes three argala families, all owned by `ga_structural`** (`fact_category_ownership`: `argala_natal_matrix`, `virodha_argala_natal_matrix`, `net_argala_per_varga` -> `ga_structural`) `[db]`. (a) `argala_natal_matrix` and (b) `virodha_argala_natal_matrix`: a 12 x 12 sign matrix per divisional chart, 144 rows each (`ga_writers/ga_structural_writer.py:4670-4781`, with a halt if the count is not 144, `:4771-4781`); (c) `net_argala_per_varga`, a house-level net count (`:7259-7295`). Offsets: `ARGALA_OFFSETS = [2, 4, 5, 11]`, `VIRODHA_OFFSETS = [12, 10, 9, 3]`, comment "per Jaimini Sutram" (`:614-616`) `[code]`.
- **Stored (canonical chart):** 21,600 argala rows + 21,600 virodha rows + 1,800 net rows = 45,000 `chart_facts` rows (30 divisional charts x 5 ayanamshas), every one `verification_pass_status = single` `[db]`.
- **L2 computes its own argala** from graha signs, graha to graha: `ARGALA_POSITIONS = {2, 4, 11}`, `VIRODHA_POSITIONS = {12, 3, 10}`, a pairing `{2: 12, 4: 3, 11: 10}`, malefic set `{Saturn, Mars, Rahu, Ketu}` (`pipeline/orchestrator/writers/bo_karanajala.py:387-390, 409, 548`). Stored edges, canonical chart, Lahiri: 24 (15 `argala_positive`, 9 `argala_virodha`, 2 cancelled); the same shape in the other four ayanamshas (surya_siddhanta 15 + 8) `[db]`. All 119 canonical-chart argala edges carry `constituent_fact_ids_array = {}` (empty), citation `BPHS_Ch28/argala`, tier `documented_approximation` `[db]`; the writer defaults the array to empty (`:1521-1522`) `[code]`. No `bo_*` writer reads any of the three L1 argala categories (grep over `platform/` for the three category names finds only L1 migrations and comments in `ka_yojaka.py`) `[code]`.
- **Rebuild blast radius** (live `asset_registry.depends_on`, transitive closure, `is_active`) `[db]`: a `ga_structural` rebuild reaches 55 declared dependents (3 L1, 20 L2, 12 L3, 9 L4, 11 L5); a `bo_karanajala` rebuild reaches 44 (13 L2, 11 L3, 9 L4, 11 L5). `bo_karanajala` declares no edge to `ga_structural`, but `ga_structural` is in its transitive closure through `ga_vichara`, so a new read of `ga_structural`'s categories needs no new edge (the reads-match detector accepts any producer in the declared transitive closure) `[db][brief]`.
- **Hold already in force (SS, 2026-10-01):** any L1 rebuild is held until the ephemeris boundary-flip report is reviewed (Group A of the full sheet, A-3 in the next commit). `ga_structural` computes through the PyJHora adapter, whose L1 `chart_facts` path the investigation (PR #2840) shows ran on the Moshier fallback. An argala-only `ga_structural` rebuild now would therefore have to be repeated after the ephemeris fix; the economical order is one `ga_structural` rebuild that carries both (recommendation under AR-6).

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
- (a) **L1 graha-level rows, L2 reads them (recommended) (R).** L1: at most 72 ordered pairs per ayanamsha for D1 (360 rows per chart; 9 grahas x 8 sources x 5 ayanamshas), of which only those at argala offsets are meaningful (28 per ayanamsha on the canonical chart in Lahiri); the new category must be added to `fact_category_ownership` by a surgical migration (otherwise it joins the 4,816 `ga_structural` rows that are already unowned; see CF-02 in the full sheet) and to `ga_structural`'s `count_sql`/floor (floors aspirational, CLAUDE.md §N.4). L2: edges change from 24 to 28 argala pairs per ayanamsha on the canonical chart before AR-1 and AR-2 effects, gain the 9th-house obstruction, and gain real `constituent_fact_ids_array` (the 119 empty become resolvable). Rebuilds: `ga_structural` (55 declared dependents) then `bo_karanajala` (44); the single batched L2 rebuild is this one.
- (b) **L2 reads L1 sign-level cells plus `graha_position` and applies L1's pairing and reversal.** No new L1 category; L1 still adds the paired-offset key (AR-1a) and the reversal has to be coded in L2, which then holds a classical rule; `ga_structural` and `bo_karanajala` still rebuild.
- (c) **Keep L2's own set, record {2, 4, 11} as a named class (the Q-L2-21 option b).** No L1 change; L2 keeps its recomputation, contradicting the ruling that L1 is the authority; about 24 duplicated edges per ayanamsha.
- (d) **Status quo.** No rebuild; L2 stays at 24 of 28 pairs with a swapped pairing and no L1 citation.

**Citation.** BPHS Ch. 31, `bphs_pg0311_c01`, `bphs_pg0312_c01`: `sourced_ocr_unverified`. Jaimini Su. 5-10, `bphs_jaimini_pg0023_c01`, `bphs_jaimini_pg0028_c01`, `bphs_jaimini_pg0028_c02`, `bphs_jaimini_pg0029_c01`: `sourced_ocr_unverified`. Natural malefics, `bphs_pg0343_c01`, `bphs_pg0343_c02`: `sourced_ocr_unverified`. Strength basis for "stronger obstructor": `unsourced` (BPHS names strength but gives no measure here).

---

### Argala block summary (replaced by the one-page table of the full sheet in the next commit)

| id | short question | recommendation | (R) | rebuilds | SS ruling (2026-10-02) |
|---|---|---|---|---|---|
| AR-1 | Who owns the argala/obstructor pairing; L2's 4->3 and 11->10 contradict BPHS | L1 owns 2-12, 4-10, 11-3, 5-9 (paired offset on rows, obstruction facts); L2 reads | (R) | `ga_structural` then `bo_karanajala` |
| AR-2 | Reverse the count for Rahu and Ketu | Yes, both nodes, when the node is the reference, in L1 graha-level rows | (R) | same two |
| AR-3 | Empty source sign scores 1.0 (3,444 of 7,200 cells) | NULL with `no_occupant`; formula stays, labelled `unsourced`; count grading is a separate ruling | (R) | `ga_structural` |
| AR-4 | `single` tier on the 45,000 L1 argala rows | Keep `single`; fix the `pyjhora_adapter.argala` label; no upgrade | no | string only, rides the others |
| AR-5 | "BPHS Ch. 28" vs Ch. 31; L1 rows have no citation | Replace by chunk ids, `sourced_ocr_unverified`; L1 uses `formula_provenance_text` | no | string only, rides the others |
| AR-6 | Canonical offsets; does L2 consume L1 rows | L1 {2,4,5,11}/{12,10,9,3} canonical, {2,4,11} named variant; L1 adds graha-level rows, L2 reads and cites them; one batched `ga_structural` rebuild (with the ephemeris fix), then one `bo_karanajala` rebuild | (R) | same two; 55 and 44 dependents |

---

## Appendix (argala block) · read-only evidence queries

Run through a subshell that sources the credential file silently; no credential is shown. All are `SELECT`, as `suvarna_reader`.

```sql
-- tier, counts, ownership of the three L1 argala families
select fact_category, verification_pass_status, count(*) from chart_facts
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa'
   and fact_category in ('argala_natal_matrix','virodha_argala_natal_matrix','net_argala_per_varga') group by 1,2;
select fact_category, owning_asset_id from fact_category_ownership
 where fact_category in ('argala_natal_matrix','virodha_argala_natal_matrix','net_argala_per_varga');
-- L2 edges (class, cancelled, citation, constituent ids)
select ayanamsha_id, relationship_class, count(*), count(*) filter (where cancelled_flag)
  from bodha_cgm_edges where chart_id='482012f1-710e-4a25-994a-93821f5871aa'
   and relationship_class in ('argala_positive','argala_virodha') group by 1,2;
select citation_ref, verification_pass_status, count(*) from bodha_cgm_edges
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and relationship_class in ('argala_positive','argala_virodha') group by 1,2;
select count(*), count(*) filter (where constituent_fact_ids_array is null or cardinality(constituent_fact_ids_array)=0)
  from bodha_cgm_edges where chart_id='482012f1-710e-4a25-994a-93821f5871aa'
   and relationship_class in ('argala_positive','argala_virodha');
-- AR-3: argala-offset cells with an empty source sign, all divisional charts x ayanamshas
--   occupants per (ayanamsha, varga, sign_number) from chart_divisionals(varga_position, sign) for the 9 grahas,
--   left-joined to argala_natal_matrix cells (offset parsed from fact_key 'from_sign_<s>_offset_<o>');
--   cells with offset in (2,4,5,11) and no occupant = 3,444 of 7,200, all scored 1.0
-- AR-1/AR-2/AR-6: graha signs, canonical, from chart_facts(graha_position, sign) for
--   SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN; offsets computed as ((src - tgt) % 12) + 1;
--   L2 rule reproduced (9 malefic edges, 2 cancelled, Lahiri) before the BPHS pairing was applied
-- blast radius: recursive closure over asset_registry.depends_on (is_active) from ga_structural and bo_karanajala
-- corpus: classical_text_chunks, text_id in (bphs, bphs_jaimini), pattern search on 'Argala' and 'malefic'
```
