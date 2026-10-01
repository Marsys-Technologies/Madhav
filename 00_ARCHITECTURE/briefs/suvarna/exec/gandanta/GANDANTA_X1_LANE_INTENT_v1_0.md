---
artifact: GANDANTA_X1_LANE_INTENT
version: "1.0"
status: DRAFT-FOR-REVIEW (committed locally on suvarna/land/TI-l1-gandanta-x1-001; not pushed; no PR)
produced_by: exec-suvarna (worker)
produced_on: 2026-10-02
lane: gandanta
plan_item: S-L1 mandatory lane I-22 (decision sheet A-4 + X1; SS rulings N-61/N-62)
base: origin/main 925e96a5d
scope: "one new L0 module, three L1 writer edits, tests, the lane's attribution hook, digest inventory and E6 pins. No migration, no database write, no Kāla production file, no rebuild."
changelog:
  - "1.0 (2026-10-02): first version."
---

# Gandanta shared module + X1 (lane `gandanta`, Track I item I-22)

## 0. What this lane does, in four lines

1. ONE definition of Gandanta (3°20' each side of the three water|fire junctions) lives in a new L0 module, `platform/python-sidecar/brahmagyan/gandanta.py`, imported by the three L1 writers `ga_sensitive_degree`, `ga_structural` and `ga_nakshatra`.
2. X1: `ga_nakshatra`'s unqualified `graha_gandanta.is_gandanta` now follows that width. The 0°48' reading it used to store unlabelled is emitted beside it as variant rows with `formula_id = 'strict_0_48'` (junction and side keys kept).
3. `ga_structural`'s bare `except Exception: fires = False` around the Gandanta import no longer hides a wiring error: the import is at module level, and a raise in the legacy dosha fallback is counted (`DOSHA_FALLBACK_EVAL_ERRORS`) and logged with a traceback.
4. Nothing is rebuilt here. Stored rows change only when `ga_nakshatra` is rebuilt in S-L1 (section 7).

## 1. The definitions found (finding F-3) and how far they disagree

| # | where | what it says | width |
|---|---|---|---|
| 1 | **L0** `brahmagyan/l0_doshas.py:747` (`brahma_dosha_catalog` `gandanta_dosha`) | "Moon at a water-fire sign junction (last 3deg20' of Cancer/Scorpio/Pisces or first 3deg20' of Leo/Sagittarius/Aries) OR nakshatra junction"; the rule is a narrative string the generic evaluator never executes (no `gandanta` row in any stored `dosha_label`) | 3°20' (text only) |
| 2 | **L1** `ga_sensitive_degree_writer.py` (`GANDANTA_ARC = 30.0 / 9.0`, `check_gandanta`; also `ga_structural`'s legacy dosha fallback and, via it, `ka_vighnakara`) | last arc of Cancer/Scorpio/Pisces, first arc of Leo/Sagittarius/Aries, edges inclusive | **3°20'** (200') |
| 3 | **L1** `ga_nakshatra_compute.py` (`GANDANTA_ORB_ARCMIN = 48.0`) stored by `ga_nakshatra_emitters.py` as plain `graha_gandanta.is_gandanta` | within 48' of 0°, 120°, 240° | **0°48'** (48') |
| 4 | **L2** `bodha_writers/nakshatra_semantic_emitter.py:68-103` (`_gandanta_flag`, `threshold_deg = 0.8`) | pāda 4 of Ashlesha/Jyeshtha/Revati within 0.8° of the nakshatra end, pāda 1 of Magha/Mula/Ashwini within 0.8° of its start | 0°48' (geometrically the same zone as 3, restricted to the end/start pāda) |

Disagreement. The two L1 assets differ by a factor of 4.17 (3°20' against 0°48' = 152' per side). Definitions 2 and the L0 text agree; definitions 3 and 4 agree with each other. On a real chart the two L1 assets contradict each other: Abhinandan (`1c826d5a`), Mars, Lahiri, 3.18° before the end of Pisces: `sensitive_degree_check.gandanta` reads `gandanta` on 7 rows (Mars in 5 ayanamshas, Venus in raman and surya_siddhanta), `graha_gandanta.is_gandanta` reads `true` on 1 row.

Two further statements I found that the sheet's "four" does not count: (a) L0 `brahmagyan/l0_nakshatra.py` (`bg_nakshatra`) carries a boolean `is_gandanta` on 6 of the 27 nakshatras (Ashlesha, Jyeshtha, Revati, Magha, Mula, Ashwini): a whole-nakshatra flag, 13°20' wide, not a degree test, no code path joins it to a chart longitude; (b) `ka_vighnakara` used to carry a wrong local table (the first 3°20' of the water signs); PR #2836 already replaced it by `check_gandanta`, so it is not a live fifth definition. **This lane unifies definitions 2 and 3 (both L1 writers). Definition 4 (L2) and the L0 catalog text are not edited here** (L2 is out of scope; the catalog is an L0 data row; both are listed as follow-ups).

## 2. Design

**Placement.** New file `platform/python-sidecar/brahmagyan/gandanta.py` (precedent: `domain_vocabulary.py`, `graha_vocabulary.py`). Standard library only, no import from the repository. No existing L0 module is edited (an edit to `l0_ephemeris.py` or another widely imported file would move dozens of writer digests); the module is imported only by the three writers.

**API (all pure).**

| name | meaning |
|---|---|
| `GANDANTA_ARC = 30.0 / 9.0` | 3°20', the float the writers have always used (edges are float-exact to it); `GANDANTA_ARC_EXACT = Fraction(10, 3)`, `GANDANTA_ARC_ARCMIN = 200` |
| `GANDANTA_STRICT_ARC`, `GANDANTA_STRICT_ARC_ARCMIN = 48.0`, `GANDANTA_STRICT_FORMULA_ID = "strict_0_48"` | the named stricter variant |
| `GANDANTA_JUNCTIONS` | three `GandantaJunction(name, cusp_deg, water_sign, fire_sign, nakshatra_pair)`: `water_fire_0` Meena\|Mesha (Revati\|Ashwini), `water_fire_120` Karka\|Simha (Ashlesha\|Magha), `water_fire_240` Vrischika\|Dhanu (Jyeshtha\|Mula) |
| `GANDANTA_WATER_SIGNS = {3, 7, 11}`, `GANDANTA_FIRE_SIGNS = {4, 8, 0}` | public (the Kāla window design note, Q3, asked for a public accessor) |
| `GANDANTA_CITATION` | text unchanged |
| `check_gandanta(sign_num, degree_in_sign)` | the exact dict `ga_sensitive_degree` has always stored (keys and values unchanged) |
| `locate_gandanta(longitude_deg, arc_deg=None)` | the same predicate from a sidereal longitude, returning `fired`, `junction_type`, `junction_deg`, `junction_signs`, `side`, `distance_deg`, `arc_minutes_from_junction`, `zone` |
| `locate_gandanta_strict(longitude_deg)` | `locate_gandanta` at 0°48' |

**One predicate.** `check_gandanta`, `locate_gandanta` and `locate_gandanta_strict` all go through one private function, so there is one place where the arc is applied (`degree >= 30 - arc` on the water side, `degree <= arc` on the fire side, both inclusive: the L1 semantics, unchanged). The strict variant uses the same junction table and predicate with its own named width.

**Kāla compatibility (no behaviour change on their side).** `ga_sensitive_degree_writer.py` re-exports `GANDANTA_ARC`, `GANDANTA_CITATION` and `check_gandanta` from the shared module under their historical names; `ka_vighnakara` (`from ga_writers.ga_sensitive_degree_writer import GANDANTA_CITATION, check_gandanta`) and its tests are untouched and pass. The design note's windows builder can import `brahmagyan.gandanta` directly later (`GANDANTA_JUNCTIONS`, `GANDANTA_WATER_SIGNS`, `GANDANTA_ARC`). No Kāla file was edited. One consequence: `ka_vighnakara`'s writer source digest moves because it imports `ga_sensitive_degree_writer` (section 5).

**Side at the exact cusp.** The shared definition follows the sign: the fire sign starts at the cusp, so a longitude of exactly 0°/120°/240° is `departing`, distance 0. The old `ga_nakshatra` code tie-broke exactly-on-cusp to `approaching`. This differs only at the exact cusp longitude (a measure-zero set for ephemeris longitudes); it is recorded and pinned by a test, not hidden.

**X1 row emission (`ga_nakshatra_emitters.emit_gandanta_flags`).** Per body, canonical rows exactly as before in shape (`formula_id` NULL): `is_gandanta` (true/false, from the shared 3°20' function), and when true `arc_minutes_from_junction`, `junction_type`, `side`. Then the strict variant: `is_gandanta` (true/false) for every body, and when true the same three detail keys, all with `formula_id = 'strict_0_48'` and `source_calculation = ga_nakshatra:gandanta:strict_0_48:longitude=...`. Per ayanamsha that is +10 variant `is_gandanta` rows (+3 per strict-true body).

**No duplicate identity.** `chart_facts` has two partial unique indexes: `chart_facts_unique_null_formula` (…, build_id) WHERE formula_id IS NULL and `chart_facts_unique_with_formula` (…, build_id, formula_id) WHERE formula_id IS NOT NULL, and `fact_id` is the primary key. `ga_nakshatra._fact_id` now appends `|formula_id` only when one is set, so variant rows get a distinct `fact_id` and every canonical `fact_id` is byte-identical to before (asserted against the old hash input). `citation_ref` gains `:formula=strict_0_48` and `citation_human` gains ` (variant strict_0_48)` for variant rows only. Insert: canonical rows use the unchanged statement (`ON CONFLICT … WHERE formula_id IS NULL`); variant rows use a second statement with the `formula_id` column and `ON CONFLICT (…, build_id, formula_id) WHERE formula_id IS NOT NULL`. This is the same two-partition mechanism the Yogi/Avayogi, karaka and mṛtyu variant rows already use.

**Idempotency (N.3).** Unchanged: `replace_prior_chart_facts` deletes the chart's rows for the (category, ayanamsha) scope present in the rows, with no `formula_id` filter, so a rebuild deletes the variant rows as well and re-inserts exactly one copy per natural key.

**Tier.** Both readings stay `single` (`UNVERIFIED_DEFAULT`): nothing re-derives them independently (N.8; migration 742 conjunct (b) still holds). No bare literal was added; `ga_nakshatra` already took the tier from `verification_vocab`.

**`ga_structural`.** The legacy dosha fallback (only reached when `brahma_dosha_catalog` is unavailable; no stored `dosha_fires` Gandanta row exists on any chart) now uses the module-level shared import; `check_mrityu_bhaga` stays a lazy import from the sensitive-degree writer, so a failure there can no longer take the Gandanta test down with it. On a raise: `logger.error(..., exc_info=True)` and `DOSHA_FALLBACK_EVAL_ERRORS[dosha_name] += 1`; the pass still reports "not fired" rather than regress (the honest-null alternative would change the legacy path's contract; flagged below).

## 3. Old-vs-new counts (offline, read-only; `offline_old_vs_new.py`, report `offline_old_vs_new_report.json`)

Method: stored sidereal longitudes (`graha_position.longitude_sidereal`, 10 subjects per chart per ayanamsha) re-run through (a) the OLD `ga_nakshatra` algorithm (verbatim copy) to prove the reconstruction against the stored `graha_gandanta` rows, then (b) the shared module. Reads were SELECT-only as the read-only reader.

**Reconstruction proof.** 150 subject-readings (3 charts x 5 ayanamshas x 10 subjects) reconstructed by the old algorithm: **0 mismatches** against the stored `graha_gandanta` rows (`is_gandanta`, and for the one true row `arc_minutes_from_junction` = 12.97, `junction_type` = `water_fire_0`, `side` = `approaching`; floats compared to 0.01'). 135 `sensitive_degree_check.gandanta` rows re-derived from the same longitudes through the shared module: **0 differ**. Stored `dosha_fires` rows with a Gandanta subject: 0, and no stored `graha_gandanta` variant row exists today.

**The decision sheet's Abhinandan figure is reproduced exactly:** `sensitive_degree_check.gandanta` = `gandanta` on 7 rows (Mars x5 ayanamshas, Venus x2); old `graha_gandanta.is_gandanta` true on 1 row (Mars, surya_siddhanta, 12.97'); new canonical `is_gandanta` true on **7** rows. Agreement of the two L1 assets over the 45 non-Lagna readings per chart: Abhinandan old 39/45 agree (6 disagree), new 45/45; canonical and third chart 45/45 both before and after.

| chart | ayanamsha | old true | new true | `is_gandanta` flips | detail rows appearing | variant rows added |
|---|---|---|---|---|---|---|
| canonical `482012f1` | all five | 0 | 0 | 0 | 0 | 10 each (50) |
| third `cb73cd3d` | all five | 0 | 0 | 0 | 0 | 10 each (50) |
| Abhinandan `1c826d5a` | krishnamurti | 0 | 1 (Mars 356.9187°, 184.9') | 1 | 3 | 10 |
| | lahiri_chitrapaksha | 0 | 1 (Mars 356.8219°, 190.7') | 1 | 3 | 10 |
| | raman | 0 | 2 (Mars 358.2682°, 103.9'; Venus 357.5887°, 144.7') | 2 | 6 | 10 |
| | surya_siddhanta_classical | 1 | 2 (Mars unchanged at 12.97'; Venus 359.1044°, 53.7') | 1 | 3 | 13 (10 + 3 detail for the strict-true Mars) |
| | true_chitra | 0 | 1 (Mars 356.8374°, 189.8') | 1 | 3 | 10 |
| **Abhinandan total** | | **1** | **7** | **6** | **18** | **53** |

Rows that would change per chart on a `ga_nakshatra` rebuild (appear / disappear / change value), counting the 50 canonical `is_gandanta` rows as unchanged except the flips:

* canonical `482012f1`: **50 rows added, 0 changed, 0 removed** (50 `strict_0_48` `is_gandanta` rows, all `false`). The 50 canonical `graha_gandanta` rows keep their value and `fact_id`.
* third `cb73cd3d`: **50 added, 0 changed, 0 removed**.
* Abhinandan `1c826d5a`: **77 = 6 `is_gandanta` value changes (false to true) + 18 canonical detail rows appearing + 53 variant rows added**; 0 removed. Lagna never falls in a Gandanta arc on any chart.

No other L1 asset's rows move: `sensitive_degree_check` (0 of 135) and `dosha_fires`/`dosha_label` (no stored Gandanta row) are unchanged. Per ayanamsha figures are in the JSON report; the hook's expected counts come from `hook_simulation_report.json` (the detector's own `compare_states` over old-vs-new states: canonical 50, third 50, Abhinandan 65 detector-visible changes, 0 unattributed under `gandanta.json`).

## 4. Attribution hook

`00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/gandanta.json` (lane name kept; extends the seed that exists on `suvarna/land/TI-ephemeris-flip-report-001`, which listed only `graha_gandanta`/`is_gandanta` with no count). Three entries: (1) `is_gandanta` `occurrence_count`, exact 50 per chart (each key gains its `strict_0_48` twin); (2) `is_gandanta` `value/appeared/disappeared/tier`, no count (the six Abhinandan flips are masked by the detector's sorted-occurrence pairing, so any detector-visible value change here would be unexpected); (3) `arc_minutes_from_junction` / `junction_type` / `side` `appeared`/`occurrence_count`, 0..15 (canonical 0, third 0, Abhinandan 15). `sensitive_degree_check` is deliberately not listed: it must not move, and a change there should surface as UNATTRIBUTED. Validated with that branch's `flip_detector.py --validate-hooks --require-lanes argala,gandanta` (valid) and its `test_flip_detector.py` (12 passed), from a scratch copy; the seed file on that branch will conflict with this one when both land: take this one.

## 5. Writer-digest inventory (`platform/src/generated/nirmana-writer-digests.json`)

Regenerated; 7 digests moved, nothing else:

| asset | layer | why it moves |
|---|---|---|
| `ga_nakshatra` | L1 | edited (writer, emitters, compute) |
| `ga_sensitive_degree` | L1 | edited (`ga_sensitive_degree_writer.py`) |
| `ga_structural` | L1 | edited (`ga_structural_writer.py`) |
| `ga_yoga` | L1 | shares the `ga_structural_writer` source set (same digest as `ga_structural` and `ga_sensitive_degree` before and after) |
| `ga_sensitive` | L1 | imports a changed module |
| `ga_ayurdaya` | L1 | imports a changed module |
| **`ka_vighnakara`** | **L3 (Kāla)** | **imports `ga_sensitive_degree_writer` (transitive source digest); no Kāla file was edited, behaviour unchanged. FLAG for the Kāla owner: its provenance receipt and output-digest history re-key on the next build.** |

No L0 (`bg_*`) digest moved. No L2, L4 or L5 digest moved. E6 declaration pins re-pinned (`test_e6_1_declarations.py` + `asset_declarations.json`, following 271290c25): line numbers for `ga_structural` (+9 / +20), `ga_nakshatra` (+10), `ga_sensitive_degree` (-21); and two census facts that really changed: `ga_nakshatra` now has **3** `INSERT INTO chart_facts … citation_human` sites (the new variant statement; was 2), and `ga_sensitive_degree`'s citation census reads `[0, 22, 1, 1]` (was `[0, 23, 1, 0]`: the Gandanta citation is now an imported name, which the AST census classes as `other` instead of a local constant; the text is identical). `capability_estate_census.json` regenerated (separate commit).

## 6. Consumers of the rows this lane touches

`graha_gandanta` (changes on rebuild): L1 served `get_nakshatra.ts` (`marsys://tool/L1/get_nakshatra`, `ganita_nakshatra_get`; flat read of 15 categories; it selects `citation_ref` but not `formula_id`, so a variant row is distinguishable only by its `fact_id` and the `:formula=strict_0_48` suffix of `citation_ref`: **follow-up: select `formula_id` there**, out of this lane); L2 `bo_laksana` (fetches every `chart_facts` row, `graha_gandanta` is in its position-category list; each variant row becomes a source fact in the next S-L2 `bo_laksana` run); its downstream signals follow. No L3/L4 writer reads `graha_gandanta`. Any future reader that reduces `(graha_gandanta, subject, is_gandanta)` to one row must now pin `formula_id IS NULL` (N.7 item 2; the fact-category-pin lint only checks `fact_key`).

`sensitive_degree_check.gandanta` (does not change): `reading_checklist.ts`, `composite_ranker.ts` (`sensitive_degree_check:gandanta` boost), `ka_gochara_resonance/writer.py` (sensitive targets), served `get_sensitive_points.ts`.

Users of the Gandanta function: `ga_structural` legacy dosha fallback (no stored row), `ka_vighnakara` `_check_gandanta` (L3, via the re-export), `ga_nakshatra` (this lane). L2 `nakshatra_semantic_emitter._gandanta_flag` keeps its own 0.8° pāda rule (definition 4, untouched) and L0 `gandanta_dosha` keeps its narrative text.

## 7. What a rebuild changes

* `ga_nakshatra` rebuild (S-L1): the three row groups of section 3, per chart. Canonical chart: +50 rows, no existing value changes. Abhinandan (S-L1b): 6 flips, 18 appearing detail rows, +53 variants. `target_floor`/`count_sql` for `ga_nakshatra` count all of its categories including the new rows; floors are aspirational and re-declared from achieved counts after S-L1 (N.4); the `coverage_matrix.ts` comment "graha_gandanta=50" (line ~615) is documentation of a past count, not a gate.
* `ga_sensitive_degree`, `ga_structural` rebuilds: no row value changes; digest-only.
* `ka_vighnakara`: no rows change; digest only.
* Downstream: L2 `bo_laksana` sees +50 rows on the canonical chart in S-L2. No migration is needed (the partial unique index for formula rows already exists; `fact_category_ownership` for `graha_gandanta` is unchanged).

## 8. Tests

* New `platform/python-sidecar/tests/test_gandanta_shared_module.py` (38 tests): exact boundary values just inside, exactly on and just outside 3°20' on both sides of each of the three junctions (float-exact in sign+degree form; 3°19'/3°21' in longitude form); the Pisces|Aries wrap; 0°48' cases (strict and canonical; canonical only; strict edge); strict is a subset of canonical over 36,000 longitudes; the shared module equals the pre-I-22 `ga_sensitive_degree` function on a dense sign x degree grid plus every edge, and reproduces the pre-I-22 `ga_nakshatra` 0°48' reading over 36,000 longitudes (differences only at the exact cusp tie-break); the three writers call the same function (object identity; patching the one predicate flips `ga_sensitive_degree`, `ga_structural`'s fallback and `ga_nakshatra` together; patching the one width widens all three); non-gandanta rows of `build_sensitive_degree_rows` and `emit_gandanta_flags` unmoved, gandanta `value_jsonb` byte-equal to the old dict; canonical rows keep their old shape and `fact_id` (hash input asserted), variant rows get distinct `fact_id`/`citation_ref`; insert-statement selection; the `ga_structural` error count/log.
* Full sidecar suite (`cd platform/python-sidecar && PYTHONPATH=. /Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3 -m pytest -q`, run before the last comment-only edit; the Gandanta-relevant files were re-run after it): 10938 passed, 423 skipped, 21 xfailed, 2 xpassed, **4 failed, all outside this lane**: `scripts/kala_admission/tests/test_w44_weight_fitting.py::...test_all_10_admitted_toggle_keys_are_currently_unwired` (three extra toggle keys w28/w29/w30) and three `tests/l3/gochara/test_wp10_cutover.py` tests (no `kala_gochara_windows` rows for the generation; the cutover precondition). I did not run them on the base commit; none imports a changed module or reads Gandanta.
* Governance: `PYTHONPATH=platform/python-sidecar python -m pytest platform/scripts/governance/__tests__ -q`: 2249 passed, 87 skipped (6 initially failed on E6 pins; re-pinned). `check_fact_category_pinning.py`: 0 new violations (65 pre-existing, allowlisted). `provenance_inventory --check`: current. `npm run codegen:capability-estate-census:check`: OK after regeneration.

## 9. Not verified

* **No rebuild was run and no database was written.** Everything in section 3 is an offline reconstruction from stored longitudes; the real `ga_nakshatra` run recomputes longitudes through `compute_chart` (PyJHora). The stored `graha_position.longitude_sidereal` matched the old stored `graha_gandanta` rows on all 150 readings, which supports but does not prove they are identical to the adapter's `longitude_deg` in every case; the ephemeris lane (G-EPH, I-21) can move a longitude, so a boundary-near reading could differ after that lane (Abhinandan Mars sits 0.16-0.25° inside the 3°20' edge in lahiri, true_chitra and krishnamurti).
* The new variant INSERT statement and the `ON CONFLICT … WHERE formula_id IS NOT NULL` arbiter were not executed against a database (the sidecar tests use no DB); the arbiter text matches the live partial unique index `chart_facts_unique_with_formula` read from `pg_indexes`, and the same two-partition mechanism is used by other writers, but a first real write is the proof.
* The `graha_gandanta` `count_sql` / floor, the migration-742 integrity SQL and the `ga_nakshatra` output-digest spec (migration 889: `key_columns [fact_id]`) were read, not executed; none needs a change (distinct `fact_id`, no per-key cardinality conjunct), but a live integrity run after the rebuild is the proof.
* Citation states: the 3°20' water side is `sourced_ocr_unverified` (BPHS Santhanam, `bphs_pg0111_c01`, from the decision sheet); the fire side and 0°48' are `unsourced`; I did not re-search the corpus.
* Whether `bo_laksana`'s natural key tolerates two `graha_gandanta` rows per (subject, key) was not traced to the table constraint; variant rows from other formula families already flow through the same fetch.
* The legacy dosha fallback still reports "not fired" on a raise (counted and logged); whether it should fail the pass instead is a contract question I did not decide.
* Not done, by instruction: any Kāla file (`ka_vighnakara`'s own import can move to `brahmagyan.gandanta` in the Kāla lane), `get_nakshatra.ts` `formula_id` select, the L2 0.8° rule, the L0 catalog text.
