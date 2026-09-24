---
artifact: KSHETRA_RULINGS_789_INDEPENDENT_RECOUNT
canonical_id: KSHETRA_RULINGS_789_INDEPENDENT_RECOUNT
version: "1.0"
status: INDEPENDENT_RECOUNT_COMPLETE
date: 2026-09-24
owner: "O-3, dispatched by the L3 Gochara session"
authority: >
  O-3 named in GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md §4 — "a fresh independent session,
  dispatched 2026-09-24 by this session, instructed to re-derive every count from the served table
  classical_text_chunks by count(*) with a stated predicate, never from SOURCE_DATA/classical_texts/
  and never from a search tool, and to report NOT_RUN honestly where it cannot reach the corpus
  rather than infer a number."
rules_on: KSHETRA_RULING_SHEET_v1_0.md v1.10 (origin/main, blob at 0dcf28d6d) rulings 7, 8, 9
method: >
  Finding F-32, the corpus method rule, followed without exception. The admitted corpus is the
  SERVED TABLE `classical_text_chunks` in production. It is NOT the source-data directory
  `00_ARCHITECTURE/SOURCE_DATA/classical_texts/` — the directory read that produced the original
  error, which this re-count exists to be free of — and it is NOT whatever a semantic or vector
  search tool returns. Every number below was produced by a `count(*)` (or a full read of the named
  chunk) with its exact predicate printed beside it. No absence is claimed except as a count(*) = 0
  with a stated predicate. No number in this report was remembered, inferred, carried from another
  artifact, or obtained from a search tool. Where a claim could not be measured it is NOT_RUN with
  the reason, per CLAUDE.md §N.8 (Earned-Signal Principle): an honest NOT_RUN is the correct
  deliverable; a plausible-sounding number is a campaign-grade defect.
access: >
  Read-only. Cloud SQL Auth Proxy on 127.0.0.1:5433 to
  madhav-astrology:asia-south1:amjis-postgres, queried through the read-only `postgres` MCP tool.
  Aggregate counts, schema introspection and verse-reference reads only. No private narrative row,
  no personal or native data, no chart-scoped row was selected. No write, no DDL, no dispatch. No
  credential, connection string or token appears in this file.
changelog:
  - "1.0 (2026-09-24) — initial independent re-count. 17 claims CONFIRMED, 7 CORRECTED, 4 NOT_RUN."
---

# Kṣetra rulings 7, 8 and 9 — independent corpus re-count

## 0. Why this document exists, and what it is not

Kṣetra's rulings 7, 8 and 9 were certified by reviewers who were themselves conflicted, and the
corpus counts underneath ruling 8 came from the Gochara family, which **twice had to correct them**.
The first error was a method error, not an arithmetic one: three sessions and one external review
read the source-data *directory* `00_ARCHITECTURE/SOURCE_DATA/classical_texts/` (four folders: BPHS,
Jaimini_Sutram, KP, KP_Reader) and reported it as the admitted corpus. On that premise Phaladīpikā
was "absent" and forty-one rules were "unsourced". The premise was wrong. The corpus is the served
table.

This is a re-count, not a code review. It does not re-open any ruling — it reports, per ruling,
whether the ruling still stands on numbers independently measured today. Two of the three rulings
turn out to carry **no corpus-count claim at all**, which is itself a material finding: the F-32
error cannot have contaminated them, and their certification rests on other evidence entirely.

## 1. Findings table

Predicates are given exactly as run. `TXT` abbreviates the all-text-field concatenation
`coalesce(content_en,'')||' '||coalesce(cleaned_translation_text,'')||' '||coalesce(content_summary,'')||' '||coalesce(content_sa,'')`,
used wherever a claim's own predicate was unstated, so that no hit is missed by reading only one
column. Where `content_en` alone and `TXT` agree, both are reported.

### 1.1 The corpus itself

| # | Claim | Predicate used | Measured | Verdict |
|---|---|---|---|---|
| C-1 | The served corpus is 15 texts | `select count(distinct text_id) from classical_text_chunks` | **15** | **CONFIRMED** |
| C-2 | The served corpus is 10,651 chunks | `select count(*) from classical_text_chunks` | **10,651** | **CONFIRMED** |
| C-3 | All 15 texts have content (the "15 texts with content" wording) | `count(distinct text_id)` / `count(*)` `where content_en is not null and length(trim(content_en))>0` | **15 texts / 10,651 chunks** — every served chunk has non-empty English content | **CONFIRMED** |
| C-4 | Phaladīpikā is present in the served corpus | `where text_id='phaladeepika'` | present | **CONFIRMED** |
| C-5 | Phaladīpikā is ~564 chunks | `count(*) where text_id='phaladeepika'` | **564** — exactly, not approximately | **CONFIRMED** |
| C-6 | ~17 Phaladīpikā chunks carry "vedha" | `where text_id='phaladeepika' and content_en ILIKE '%vedha%'` (and same under `TXT`) | **17** under both — exactly, not approximately. Refs: PG33, PG34, PG322, PG323, PG332, PG339, PG347, PG348, PG349:C1, PG349:C2, PG350, PG351:C1, PG351:C2, PG352, PG353, PG451:C2, PG463 | **CONFIRMED** |
| C-7 | KP returns 0 chunks | `count(*) where text_id ILIKE '%kp%'` | **0** | **CONFIRMED** |

The full served roster, for the record (`group by text_id order by count desc`): nadi_navamsa_patel
1850 · bphs 1459 · yavana_jataka 1298 · brihat_samhita 1171 · jataka_parijata 704 ·
bhrigu_nandi_nadi 608 · brihat_jataka 607 · **phaladeepika 564** · saravali 471 · hora_sara 460 ·
sarvartha_chintamani 342 · tajaka_neelakanthi 290 · uttara_kalamrita 289 · **muhurta_chintamani
274** · bphs_jaimini 264. Sum = 10,651. The four directory folders that caused the original error
(BPHS, Jaimini_Sutram, KP, KP_Reader) map onto two served texts and one absence: `bphs`,
`bphs_jaimini`, and no KP at all.

### 1.2 The house-vedha citation split — ruling 8's load-bearing count

| # | Claim | Predicate used | Measured | Verdict |
|---|---|---|---|---|
| H-1 | house_vedha has **41** rows in `bg_transit_rules` | `count(*) from bg_transit_rules where vedha_house is not null` | **42** | **CORRECTED** |
| H-2 | **39** rules cite BPHS Ch.29 alone | `... and classical_citation ILIKE '%BPHS%'` | **6** — and all six are the Rāhu/Ketu rows whose citation is an `UNSOURCED` stamp that names BPHS Ch.29 only to record that it *does not exist in this corpus*. Rows citing BPHS Ch.29 **as their source: 0** | **CORRECTED** |
| H-3 | exactly **2** (Rāhu, Ketu) cite Phaladīpikā Ch.26 | `... and classical_citation ILIKE '%phalad%'` | **42 of 42**. Every house-vedha row now carries a page-anchored Phaladīpikā citation (`phaladeepika:PG322:C1` / `PG323:C1`, Ādh. XXVI ślokas 3–8, Sastri trans. 1950). The two rows that once cited Phaladīpikā were **Rāhu/Ketu rows** — precisely the six rows that are now the *only* ones NOT sourced to it | **CORRECTED** |
| H-4 | **32** rows match the text exactly and become `applied` | full read of `phaladeepika:PG322:C1` and `PG323:C1`, then row-by-row comparison against `select graha, primary_house, vedha_house from bg_transit_rules where vedha_house is not null` | **36** | **CORRECTED** |
| H-5 | **3** Venus rows contradict the text and are DEFERRED (ids 35, 44, 45) | `where id in (35,44,45)` | ids 35 → `vedha_house` 1, 44 → 5, 45 → 11. **All three now match the text. Deferred count: 0** | **CORRECTED** |
| H-6 | **6** Rāhu/Ketu rows (187,188,189,196,197,198) stay `unqualified` | `where graha in ('rahu','ketu') and vedha_house is not null` | **6**, exactly those ids, each carrying the `UNSOURCED` stamp and retained (not deleted) per B.10 / N-14 | **CONFIRMED** |
| H-7 | PG322–323 ślokas 3–8 name only the seven classical grahas | full read of both chunks | Sun (śl.3), Moon (śl.4), Mars + Saturn (śl.5), Mercury (śl.6), Jupiter (śl.7), Venus (śl.8). **Seven. No Rāhu, no Ketu** | **CONFIRMED** |
| H-8 | `PG348:C1` gives an explicit Rāhu/Ketu vedha-direction rule, a *different* mechanism | full read of PG348:C1 | Verbatim: *"In the case of Rahu and Ketu, which are always retrograde, the (Vedha) will be on the right."* It is the Sarvatobhadra-chakra asterism-direction vedha under śl.48, not a house-transit pair. The ruling's characterisation is exact | **CONFIRMED** |
| H-9 | Ruling 8's stated *only* remaining reason: the producer stamp columns do not exist | `information_schema.columns where table_name='kala_vedha_gochara' and column_name in ('corpus_verifiable','source_qualification','precision_regime','claim_grain','completeness_state')` | **0 rows returned — none of the five columns exists.** `kala_vedha_gochara` itself holds 355 rows | **CONFIRMED** |

**The row-by-row derivation behind H-4, from the served text alone.** Each śloka lists transit houses
then vedha houses "respectively":

- **śl.3 Sun** — 11, 3, 10, 6 → 5, 9, 4, 12. Table: 3→9, 6→12, 10→4, 11→5. **4/4 match.**
- **śl.4 Moon** — 7, 1, 6, 11, 10, 3 → 2, 5, 12, 8, 4, 9. Table: 1→5, 3→9, 6→12, 7→2, 10→4, 11→8. **6/6 match.**
- **śl.5 Mars** — 3, 11, 6 → 12, 5, 9. Table: 3→12, 6→9, 11→5. **3/3 match.** *"The same remark applies to Saturn"* — table Saturn: 3→12, 6→9, 11→5. **3/3 match.**
- **śl.6 Mercury** — 2, 4, 6, 8, 10, 11 → [garbled token "Bill"], 3, 9, 1, 8, 12. Table: 2→5, 4→3, 6→9, 8→1, 10→8, 11→12. **6/6 match**, with one honest caveat recorded below.
- **śl.7 Jupiter** — 2, 11, 9, 5, 7 → 12, 8, 10, 4, 3. Table: 2→12, 5→4, 7→3, 9→10, 11→8. **5/5 match.**
- **śl.8 Venus** — 1, 2, 3, 4, 5, 8, 9, 12, 11 → 8, 7, 1, 10, 9, 5, 11, 6, 3. Table: 1→8, 2→7, 3→1, 4→10, 5→9, 8→5, 9→11, 11→3, 12→6. **9/9 match.**

4 + 6 + 3 + 3 + 6 + 5 + 9 = **36 matching**, + **6** Rāhu/Ketu unsourced = **42**.

**The caveat on Mercury, recorded rather than smoothed over (§N.7 item 6).** Mercury's *first* vedha
value in the served chunk is the OCR token **`Bill`**, not a house number. Row id 21 reads 2→5. The
value 5 is the standard printed reading of that śloka, and 5 is the only value consistent with the
remaining five pairs, but it is **not legible in the served chunk**. Row 2→5 is therefore
`corpus_verifiable` only at page grain with a stated OCR limit — not a clean verbatim match like the
other 35. If the admission rule is applied strictly at token grain, H-4 is 35 clean + 1 OCR-limited,
not 36 clean. This is a real distinction and no prior artifact records it.

**Why H-1..H-5 diverge, and why that is not a reviewer failure.** The ruling sheet's own changelog
v1.8 records that the L0 repair (PR #2727) was applied and verified live on 2026-09-24. This
re-count confirms it landed: Venus 35/44/45 repaired by `UPDATE`, the text's sixth Mercury pair 8→1
added as **id 569** (which is why 41 became 42), and the six node rows stamped `UNSOURCED`. The
39/2 split and the 32/3/6 outcome were the **pre-repair** state. What is wrong is not the
observation but the *tense*: ruling 8's body still publishes 39/2 and 32/3/6 as the **"Outcome WHEN
those land"** — i.e. as the post-repair prediction — on a 41-row base. The repair has landed, and
the post-repair figures are **42 / 36 / 0 / 6**. Even on the sheet's own 41-row base the arithmetic
never worked: 32 matching + 3 repaired = 35 applied and 0 deferred, never "32 applied / 3 deferred".
A number that describes the state before a fix must not be published as the state after it.

### 1.3 Sarvatobhadra

| # | Claim | Predicate used | Measured | Verdict |
|---|---|---|---|---|
| S-1 | **0** `sarvato*` rows in Muhūrta Cintāmaṇi | `count(*) where text_id='muhurta_chintamani' and TXT ILIKE '%sarvato%'` | **0** | **CONFIRMED** |
| S-2 | Muhūrta Cintāmaṇi is ~274 chunks | `count(*) where text_id='muhurta_chintamani'` | **274** — exactly. So the absence is 0 of 274, not 0 of an unknown denominator | **CONFIRMED** |
| S-3 | Phaladīpikā Ādhyāya XXVI śl. 48 at PG345–PG348 is a full primary construction of the grid | full read of PG345:C1, PG346:C1, PG347:C1, PG348:C1 | The construction is present and is primary — but it is at **PG346:C1**, not PG345. PG345:C1 carries only the announcement (*"I shall now describe the (Sarvato-bhadrachakra)"*) and the diagram legend. PG346:C1 carries the whole instruction verbatim: *"Draw ten lines vertically and another ten lines crosswise… You will have 81 squares… the 16 vowels… in the corner squares commencing from the outmost corner in the North-east… the 28 asterisms beginning with Krittika, so that each side will contain 7 asterisms… the 12 Rasis beginning with Vrishabha… the 5 groups of Tithis… The 7 week-days"*. PG347:C1 carries the malefic/benefic classification, the three-vedha aspect rule and the worked vedha-pair examples (Krittika, Rohiṇī, Mṛgaśiras). PG348:C1 carries the motion-direction rules and the letter/vowel pair-vedha rules. The page header on PG346 and PG348 reads `si. 48` / `Si. 48`, so śl.48 spans PG346–PG348 | **CONFIRMED, with the page anchor corrected** |
| S-4 | PG345 is the illegible diagram page; PG346:C1–PG352:C1 is clean prose ~1,400 chars/page | `select verse_ref, length(content_en) …` | PG345:C1 = **592** chars and heavily token-garbled — the only short page in the run, and it is the diagram page. PG346–PG352 = **1349, 1422, 1499, 1485, 1480, 1496, 1450**; mean **1454**. Neighbour PG344:C1 = 1375, PG353:C1 = 1243 | **CONFIRMED** |
| S-5 | `bg_sarvatobhadra_grid` was never populated | `select count(*) from bg_sarvatobhadra_grid` | **0** | **CONFIRMED** |
| S-6 | The vedha-pair partitions are transcribable from this prose; the vowel/consonant *letter* cell assignments are not | read of PG346–PG348 | The asterism / rāśi / tithi-group / weekday partitions are stated as plain instructions and are transcribable. The letter cells are given as Devanāgarī glyphs that survive OCR as fragments (`a*, q\`, |r and ^` in the East, etc.) and are **not** recoverable from the served text. The ruling's narrowing is correct as far as legibility goes; whether a transcription would actually succeed is NOT_RUN — see §3 | **CONFIRMED as to legibility** |

### 1.4 Kakṣyā

| # | Claim | Predicate used | Measured | Verdict |
|---|---|---|---|---|
| K-1 | **0** kakṣyā rows in Phaladīpikā under six phrasings | six counts, all `where text_id='phaladeepika' and TXT ILIKE …`: `'%kaksha%'` → **0**; `'%kakshya%'` → **0**; `'%kaksya%'` → **0**; `'%kakṣ%'` (Devanāgarī-transliterated) → **0**; `'%kaksh%'` (stem) → **0**; `'%orbit%'` → **9** | Five of six phrasings return **0**. The sixth, `'%orbit%'`, returns 9 — all generic English usage of the word, none of it kakṣyā doctrine. The kakṣyā-bearing absence in Phaladīpikā holds | **CONFIRMED, with the sixth phrasing's 9 hits recorded rather than suppressed** |
| K-2 | **6** rows in the nāḍī text carry kakṣyā | `count(*) where text_id='nadi_navamsa_patel' and TXT ILIKE '%kaksh%'` | **6** | **CONFIRMED** |
| K-3 | Those rows are at `PG1615`, `PG1616` | `select verse_ref …` same predicate | The six are at **PG80, PG1615, PG1616, PG1618, PG1623, PG1624**. Two of the six are at the named pages; four were not named | **CORRECTED** |
| K-4 | They carry per-contributor bindu semantics | full read of PG1615:C1, PG1616:C1 | Verbatim, PG1615: *"in respective Kakshyas (30° ÷ 8 = 3° 45') of those planets which have donated bindus in all the twelve Bhavas."* PG1616: *"When the Sun passes through a Kakshya which has a bindu in his P.A.V., in any Bhava, he produces beneficial effects; if he is passing through a kakshya without a bindu (i.e., a Kakshya having a rekha), the result is adverse."* Per-contributor bindu semantics, unambiguously | **CONFIRMED** |
| K-5 | *(new finding)* corpus-wide kakṣyā footprint | `where TXT ILIKE '%kaksh%'`, then read each hit | **14** corpus-wide: 6 nāḍī (the genuine aṣṭakavarga kakṣyā, K-2/K-4); **6 in `bphs_jaimini` — "Kakshya Hrasa", Jaimini's longevity *reduction* doctrine (PG4, PG146, PG147, PG153, PG154, PG155), a homonym with no relation to transit kakṣyā**; 1 in `saravali` PG130:C2 (*"Lokaksha"*, a preceptor's name); 1 in `uttara_kalamrita` PG46:C1 (*"Kakshatra"*, OCR garble for Nakshatra) | **NEW** |

K-5 matters because a bare stem count of 14 would look like a contradiction of "6 in the nāḍī text".
It is not. Disambiguated, the served corpus contains the aṣṭakavarga kakṣyā doctrine in **exactly
one text and exactly 6 chunks** — a stronger and narrower statement than the claim made, and one
that a future session running `'%kaksh%'` without reading the hits would have mis-read as a
correction.

### 1.5 Sade-Sati

| # | Claim | Predicate used | Measured | Verdict |
|---|---|---|---|---|
| D-1 | No primary Parāśari attestation | five counts, all `where text_id in ('bphs','bphs_jaimini')`: `TXT ILIKE '%sade%sati%'` → **0**; `'%sadesati%'` → **0**; `'%seven and a half%'` → **0**; `'%7 1/2%'` → **0**; `TXT ILIKE '%sani%' and '%moon%' and '%transit%'` → **0** | **0 under all five predicates.** No primary Parāśari attestation in the served corpus | **CONFIRMED** |
| D-2 | nāḍī rows at PG1334, PG786, PG1333 | `where TXT ILIKE '%sade%sati%' or TXT ILIKE '%sadesati%'` | **5 rows corpus-wide, all in `nadi_navamsa_patel`: PG1333, PG1334, PG1339, PG1340, PG1342.** PG1333 ✓ and PG1334 ✓. **PG786:C1 exists as a chunk but returns 0 hits under both predicates** — it is not a Sade-Sati row. PG1339, PG1340 and PG1342 were not named | **CORRECTED** |

### 1.6 The two vedha-count scales

| # | Claim | Predicate used | Measured | Verdict |
|---|---|---|---|---|
| V-1 | Two distinct 1–5 vedha-count scales in Ādhyāya XXVI, at PG349 (general) and PG353 ("at the time of a battle") | full read of PG349:C1, PG349:C2, PG353:C1 | Both scales exist and are distinct — **but there are three 1–5 scales across the two pages, and PG349's *count* scale is not unqualifiedly "general"**. See breakdown below | **CORRECTED** |
| V-2 | `bg_vedha_malefic_scale` cites PG353 | `select * from bg_vedha_malefic_scale` | **5 rows**, `table_version = 'phaladeepika_vedha_v01'`, `verse_ref = 'Adh.XXVI PG353'`, `source_citation … | PG353`, grades fear / failure / killing / death / ignominy — the PG353 sequence exactly | **CONFIRMED** |
| V-3 | …but is read as a general grade | `select effect_description from bg_vedha_malefic_scale` | **Corrected at the data layer.** Every one of the five rows' `effect_description` now carries, verbatim: *"This is the PG353 scale — explicitly a battle/muhurta-context vedha scale — distinct from the OTHER 1-5 malefic-count scale Adh. XXVI also carries, at PG349:C1 … a general-transit context. bg_vedha_malefic_scale seeds PG353 only."* The row no longer presents itself as general | **CORRECTED** |

**What PG349 and PG353 actually contain.** Three count-keyed 1–5 sequences, not two:

1. **PG349:C1, the juncture-effect scale (general).** *"The effects arising from these five are:-
   agitation or excitement from the first, fear from the second, loss from the third, disease from
   the fourth and death from the fifth."* This is the scale `bg_vedha_malefic_scale`'s own
   description names as PG349's.
2. **PG349:C1, the vedha-count scale.** *"When there are five Vedhas simultaneously, the individual
   will not live. A single (Vodha) will engender fear **in battle**; two Vedhs, loss of money;
   three, some obstacle; and four, death."* → 1 fear-in-battle / 2 loss of money / 3 obstacle /
   4 death / 5 will-not-live. **Its own first step carries a battle qualifier**, so calling this
   scale "general" in contrast to PG353's is not what the text says.
3. **PG353:C1, the malefic-count scale at battle.** *"When at the time of a battle, there is a
   (Vedha) caused by one, two, three, four or five malefics, the corresponding effects will be
   fear, failure, killing (blood-shed), death and ignominy respectively."* This is the one
   `bg_vedha_malefic_scale` seeds, and its battle framing is explicit and unambiguous.

So the two-scale claim is right that PG353 is battle-scoped and must not be served as a general
grade, and the L0 row descriptions now say so. It is wrong in two details: there are three
sequences, and the PG349 sequence that is actually count-keyed (2, not 1) is itself battle-flavoured
at its first step. A consumer distinguishing "general" from "battle" on the strength of the page
number alone would get PG349 wrong.

## 2. Does each ruling still stand?

### Ruling 7 — node frame (= Gochara N-4a). **STANDS. No corpus-count dependency whatsoever.**

Ruling 7 quotes as its decision: *"Under a MEAN hub ruling: disposition (b) — keep true-node knots,
derive mean in the L0 ephemeris service, `node_mode`/`epoch_convention` declared on the row beside
`ayanamsha_id`. Never Kṣetra-side."* Its evidence is ephemeris arithmetic and code reconciliation:
migration 624's `expected_mean_node_rahu_sign: 2` anchor, the mean node at 49.033044° against the
true node at 50.049248°, the 0.049° pāda margin, and `routers/ephemeris.py:82` /
`panchang_engine/planets.py` / `service_probes.py:339-340`.

**Corpus-count claims it depends on: none.** I looked for one and there is none. The F-32 directory
error cannot have touched this ruling, which is worth stating plainly because ruling 7 was bundled
with 8 and 9 for review on the strength of a shared reviewer conflict, not a shared evidence base.

The one numeric claim I *can* check without an ephemeris re-derivation, I checked, and it holds.
Rohiṇī spans 40°00′–53°20′, its pāda boundaries falling at 40°, 43°20′, 46°40′, **50°00′**, 53°20′.
Mean node 49.033044° → pāda 3. True node 50.049248° → pāda 4. Distance from the boundary:
50.049248 − 50 = **0.049248° ≈ 0.049°** — the corrected margin, and 0.045° was indeed wrong. Both
longitudes lie in sign 2 (30°–60°) and nakṣatra 4 (40°–53.333°). The anchor finding therefore holds
by arithmetic alone: a sign-level anchor **provably cannot** detect a mean/true slip that leaves
both sign and nakṣatra identical. That is a §N.8 detector-that-cannot-fail, correctly identified,
and the degree-level anchor disposition (b) adds is the right remedy. The independent re-derivation
of the two longitudes from Swiss Ephemeris is **NOT_RUN** (§3) — but the conclusion does not depend
on it, because it follows from the two stated longitudes whatever their provenance.

### Ruling 8 — shared vedha/moorti source + uniform admission. **THE DECISION STANDS. THE PUBLISHED OUTCOME ARITHMETIC IS WRONG AND MUST BE RESTATED.**

The **decision** — *"Ratify `ka_vedha_gochara` / `ka_moorti_nirnaya` as the layer's single producers.
Consumer admission uniform and mechanical: F06 `applied` iff the producer's `corpus_verifiable = true`
and geometry passes; else `unqualified`"* — stands untouched, and its stated reason is stronger after
measurement than before. Ruling 8 asserts that the *only* remaining reason every vedha row is
`unqualified` today is that the producer's stamp columns do not exist. That is an Earned-Signal
claim — a status with a specific detector behind it — and it earns its keep: **none of
`corpus_verifiable`, `source_qualification`, `precision_regime`, `claim_grain` or
`completeness_state` exists on `kala_vedha_gochara`** (information_schema returned zero rows), while
all 355 of its rows sit there waiting. The G-9 "admit Phaladīpikā" premise is confirmed MOOT:
Phaladīpikā is in the served corpus, 564 chunks, 17 of them vedha-bearing.

**What changes.** Ruling 8's body publishes, as the **"Outcome WHEN those land"**, a 41-row base
split 39/2 by citation and 32 `applied` / 3 `deferred` / 6 `unqualified` by geometry. Measured
today, post-repair, the house-vedha base is **42 rows**, **42 of 42** carry page-anchored
Phaladīpikā citations, **0** cite BPHS Ch.29 as a source, and the geometry split is **36 matching /
0 deferred / 6 unqualified**. Restated, the sentence should read:

> house_vedha's **42** `bg_transit_rules` rows: **42 cite Phaladīpikā Ādh. XXVI ślokas 3–8 at
> `phaladeepika:PG322:C1`–`PG323:C1`; 0 cite the refuted "BPHS Ch.29"** (six name it only inside an
> `UNSOURCED` stamp recording its absence). Outcome when the producer stamp columns land: **36
> `applied`** (Sun 4/4, Moon 6/6, Mars 3/3, Saturn 3/3, Mercury 6/6 — one of the six at page grain
> with an OCR limit on the śl.6 token — Jupiter 5/5, Venus 9/9), **0 `deferred`** (ids 35, 44, 45
> repaired to vedha 1/5/11; the text's sixth Mercury pair 8→1 added as id 569), **6 `unqualified`**
> (Rāhu/Ketu ids 187, 188, 189, 196, 197, 198).

Three sub-claims **stand exactly as written** and are worth saying so, since they are the ones most
often re-litigated: ślokas 3–8 name **only the seven classical grahas** (verified by reading both
chunks end to end — there is no Rāhu or Ketu anywhere in them); `PG348:C1` **does** carry an
explicit Rāhu/Ketu vedha rule, and it **is** a different mechanism (the Sarvatobhadra
asterism-direction vedha under śl.48, not a house-transit pair) — so "the corpus is silent on
Rāhu/Ketu vedha" would be false and the ruling correctly does not say it; and the sarvatobhadra
"buildable from prose" narrowing is right — PG346–PG352 is clean prose averaging 1,454 chars/page
carrying the asterism/rāśi/tithi/weekday partitions as plain instructions, while PG345 is a 592-char
OCR-degraded diagram page and the letter cells inside the prose survive only as fragments.
`bg_sarvatobhadra_grid` holds **0** rows, so "unqualified because unpopulated, not because doctrine
is absent" is the correct diagnosis.

One claim of ruling 8's supporting apparatus needs a note it does not currently carry: **Mercury row
2→5 is not verifiable at token grain**, because the served śl.6 chunk gives that vedha house as the
OCR token `Bill`. Under a *mechanical* admission rule — `applied` iff `corpus_verifiable = true` —
that row must not be stamped `corpus_verifiable` on the same footing as the other 35 without an
explicit page-grain-with-OCR-limit qualification in `rule_notes`. This is exactly the
`precision_regime` distinction the missing column exists to carry.

### Ruling 9 — G3 suppression semantics. **STANDS. No corpus-count dependency whatsoever.**

Ruling 9's decision — *"Route-scoped SM-R-7 Option B … hoist the `suppressed_keys` filter into
`hazard.evaluate`, passed explicitly; and require a byte-equality test field ≡ null ≡ projection
before any `null_p` is served from the W7 build"* — rests entirely on code semantics:
`layer1.py:15-21,29-30`, `hazard.py:347-350`, `layer0.py:57-60`, `stage4_field.py:561-565` and
`DHARA_ENGINE_SPEC_v1_0.md`. **Corpus-count claims: none.** Nothing I measured touches it, and the
F-32 error cannot have contaminated it. Its byte-equality requirement is itself a §N.8 correction of
exactly the kind this campaign exists to make — the PB-2 precedent was a byte-equality claim with no
byte comparison behind it — and I note approvingly that ruling 9 demands the comparison rather than
the claim. Verifying the five line references is a code review, not a re-count, and is outside O-3's
remit: **NOT_RUN** (§3).

## 3. What this changes

1. **Ruling 8's outcome arithmetic must be restated** to 42 / 42-cite-Phaladīpikā / 0-cite-BPHS-Ch.29
   / 36 applied / 0 deferred / 6 unqualified, per the wording in §2. This is the third correction to
   this figure, and the reason it drifted a third time is instructive and not arithmetic: the sheet
   published a **pre-repair measurement in a post-repair tense** ("Outcome WHEN those land"), and its
   own changelog v1.8 then recorded that the repair had landed without re-deriving the figures in
   the body. Even internally the published split never balanced — 32 matching plus 3 repaired is 35
   applied and 0 deferred, never "32 applied / 3 deferred". **The durable fix is not a fourth
   correction of the number; it is to stop storing it in prose.** The figure is a `count(*)` over a
   live table that a migration can change overnight. It belongs in a query that anyone can re-run,
   cited by predicate — which is the same lesson CLAUDE.md §C item 14 already learned about the L1
   row counts, and DVA Ruling 16 already ruled once. This report's §1 predicates are written to be
   re-runnable for exactly that reason.
2. **Nothing in rulings 7 or 9 changes.** Both are free of corpus-count dependency. The conflicted
   reviewer's declination bundled 7, 8 and 9 together because one session co-produced all three
   findings, not because they share an evidence base — and only ruling 8 was ever exposed to the
   F-32 error. That distinction should be on the record: re-counting the corpus can neither confirm
   nor disturb 7 and 9, and no future session should treat this report as having certified them.
3. **Ruling 8's decision and its stated reason are strengthened, not weakened.** The single-producer
   ratification, the mechanical admission rule and the "only reason is the missing stamp columns"
   claim all survive measurement. The last of these has a real detector behind it — the columns
   verifiably do not exist — which is what §N.8 asks of a status claim.
4. **One new admission-rule item, not previously recorded:** Mercury row 2→5 is page-grain
   verifiable only; its vedha house is the OCR token `Bill` in the served chunk. It needs a
   `precision_regime` / OCR-limit qualification and must not be stamped `corpus_verifiable` on the
   same footing as the other 35 clean matches.
5. **Three page-anchor corrections that would otherwise propagate as facts.** The kakṣyā nāḍī rows
   are at PG80, PG1615, PG1616, PG1618, PG1623, PG1624 — not just the two named. The Sade-Sati rows
   are at PG1333, PG1334, PG1339, PG1340, PG1342 — **PG786 is not one of them.** And the
   Sarvatobhadra construction instruction is at PG346:C1, not PG345:C1, which carries only the
   announcement and the diagram legend. A downstream citation to `PG786` for Sade-Sati or to
   `PG345:C1` for the grid construction would not resolve to the content claimed.
6. **One disambiguation that prevents a false future "correction".** A bare `'%kaksh%'` count returns
   **14** corpus-wide, which looks like it refutes "6 in the nāḍī text". It does not: 6 are Jaimini's
   unrelated *Kakshya Hrasa* longevity-reduction doctrine in `bphs_jaimini`, 1 is a preceptor's name
   (*Lokaksha*), 1 is OCR garble (*Kakshatra*). The aṣṭakavarga kakṣyā doctrine is in **exactly one
   text and exactly 6 chunks**. Recorded here so the next session that runs the stem count does not
   "fix" a correct number.
7. **The two-scale claim needs one qualifier.** PG353 is explicitly battle-scoped and
   `bg_vedha_malefic_scale`'s five rows now declare that in their own `effect_description` — the
   defect as originally framed is remediated at the data layer. But PG349 carries **two** 1–5
   sequences, and the count-keyed one opens with "fear **in battle**". "PG349 = general, PG353 =
   battle" is too clean a split to hang a consumer's grading on.

## 4. What I could not run, and why

Reported as **NOT_RUN** per the dispatch and §N.8, rather than inferred:

1. **Independent Swiss Ephemeris re-derivation of the mean and true node longitudes at the forensic
   JD (2445735.717361)** — ruling 7. I performed no ephemeris computation and will not state a
   number I did not compute (B.10). What I *did* verify is the arithmetic consequence of the two
   longitudes as stated: the 0.049° pāda margin re-derives exactly, and the shared sign-2 /
   nakṣatra-4 finding follows. The anchor conclusion does not depend on the re-derivation; the
   *value* 49.033044° / 50.049248° does, and I did not re-measure it.
2. **Ruling 9's five code line references** (`layer1.py:15-21,29-30`, `hazard.py:347-350`,
   `layer0.py:57-60`, `stage4_field.py:561-565`, and the `DHARA_ENGINE_SPEC_v1_0.md` contract) — a
   code review, not a corpus count, and outside O-3's remit as named in
   `GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md` §4. Unverified, and this report certifies nothing
   about them.
3. **Whether any live consumer code path still reads `bg_vedha_malefic_scale` as a general grade.** I
   measured the data: all five rows cite PG353 and now declare their battle scoping in
   `effect_description`. Whether a reader downstream ignores that description is a code question a
   `count(*)` cannot answer. The data-layer half of the claim is CORRECTED; the code-layer half is
   NOT_RUN.
4. **Whether the Sarvatobhadra vedha-pair partitions would actually transcribe successfully** into
   `bg_sarvatobhadra_grid` under migration 526's partition invariant. I confirmed the *legibility*
   premise — PG345 degraded at 592 chars, PG346–PG352 clean at a 1,454-char mean, partitions stated
   as plain instructions, letter cells surviving only as fragments. I did not attempt the
   transcription, so "buildable from prose today" is confirmed as to legibility and NOT_RUN as to
   buildability.

**On the method, finally.** Every figure in §1 came from a `count(*)` or a full read of a named chunk
against the served table, with the predicate printed. Nothing came from
`SOURCE_DATA/classical_texts/`, which I did not open, and nothing came from a semantic or vector
search tool, which I did not call. Where a claim's own predicate was unstated I ran it against the
all-text-field concatenation as well as `content_en` alone, so that no hit is missed by reading one
column; where the two disagree I said so. Seven claims came back **CORRECTED** and four **NOT_RUN** —
and the fact that the largest corrections are on ruling 8, the one ruling of the three that ever
touched a corpus count, is the strongest available evidence that the F-32 rule is the right rule and
that a fresh counter was the right instrument.
