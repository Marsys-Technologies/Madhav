# Signature houses and kārakas for the eight H-unknown classes

**Memo v1.0 · 2026-10-05 · Fable 5.1, effort high · READ-ONLY (no file, test, or DB write)**
Scope: lift `ST-H-UNKNOWN-20261002` class by class (gap G10). Rule overridden: "No H is assigned here without a citation" (specs v1.4 §2.2). Every assignment below carries a source kind: **K1** citation with text+locus (= [D]), **K2** owner ratification (= [P]), **K3** derivation with named premises (= [R]; generator: this memo; method: cited significations → stated step; version 1.0). Corpus = served `classical_text_chunks`, read-only SQL with stated predicates (CORPUS_READS discipline). Abbreviations: BPHS (Santhanam), PhD = Phaladīpikā (Sastri), JP = Jātaka Pārijāta, YJ = Yavana Jātaka; `PGn:Cm` = served locator.

## Summary table

| class | H (lagna frame unless stated) | kārakas | grade / kind | confidence |
|---|---|---|---|---|
| achievement_recognition | {10, 11, 5} | Sun [D]; Jupiter | all K1 | high (10,11), medium (5) |
| business_launch | {10, 7} | Mercury | H K1; Mercury K2 | high (10), med-high (7) |
| financial_deception | {12, 6, 8} | Saturn; Rahu | H K1; Saturn K1; Rahu K2 | medium |
| foreign_settlement | {12, 9, 7} | Rahu; Saturn | H K1; Rahu K2; Saturn K3 | high (12), medium (9,7) |
| parental_event | father: `bhavat_bhavam:9`, offsets {1,6,8,12}; mother: `bhavat_bhavam:4`, same offsets | Sun, Moon [D] | anchor K1; offsets K3 | high / medium |
| property_acquisition | {4, 11} | Mars | H K1; Mars K1 text + K3 step | high |
| psychological_arc | {4, 5, 8} | Moon [D]; Mercury | all K1 | medium |
| spiritual_turn | {9, 5} + 12 | Jupiter; Ketu; Saturn | 9,5 K1; 12 K2; Jupiter K3; Ketu, Saturn K2 | high (9), med (5), K2 (12) |

## Per-class notes

**1. achievement_recognition** (gain). 10: BPHS 11.11 PG121:C1 "honour"; PhD I.15 PG45:C1 "Aspada (rank), Mana (honour), Kirti (fame)"; JP I.52 PG62:C1 "Mana"; transit: YJ 45.29 PG648:C2 Saturn 10th "honor… position", YJ 46.29 PG650:C2 Jupiter 10th "honor from kings". 11: PhD I.15 "Slaghyata (commendation), Siddhi"; YJ 49.30 PG657:C2 Mercury 11th "publicity, praise of wise men". 5: BPHS 11.6 PG121:C1 "royalty (authority)"; YJ 46.27 Jupiter 5th "dignity, honor… fame". Jupiter kāraka: PhD II.5 PG48:C1 "honour". Single type. Dispute: an acharya may add 1 or 9 (YJ 45.25, 47.29 "honor" there too); I kept |H|≤3.

**2. business_launch** (gain). 10: PhD I.15 "Vyapara (commerce), Jeevana (livelihood), Pravritti"; JP I.52 "Vyapara"; BPHS 11.11 "profession"; YJ 46.29 Jupiter 10th / 50.29 PG659:C2 Moon 10th "success in business". 7: BPHS 11.8 PG121:C1 "trade"; Saravali PG108:C2 Moon+Jupiter in 7th "good businessman". Versus career classes {10,6}: 7 (trade/public dealing) vs 6 (service) is the cited discriminator; no further split. Mercury: predicate `mercury×(trade|merchant|commerce)` over 8 texts found daśā results only (BPHS PG773:C1, Saravali PG158:C2), no kārakatva → **K2**, else leave `computed_empty`.

**3. financial_deception** (adverse; victim frame). 12: PhD I.16 PG45:C1 "Kshaya (loss), Suchaka (spy), Daridrya"; YJ 48.30 PG655:C1 Mars 12th "robberies"; YJ 47.30 PG653:C1 Venus 12th "loss of one's wealth… delusion"; YJ yātrā PG710:C2 v.29 12th "expense, fraud". 6: PhD I.13 PG43–44:C1 "Rina (debt), Chora (thief), Dushkritya"; BPHS 11.7 "enemies"; BPHS 24.18 PG193:C1 2L in 6th + malefic "loss through enemies". 8: PhD I.14 PG44:C1 "Parabhava (defeat/insult), Apavada (scandal)"; YJ 48.28 Mars 8th "thieves… losses". Differs from major_loss {12,8} by the 6th (adversary). Saturn K1: PhD II.7 PG49:C1 "degradation… humiliation… poverty, debts". Rahu: no kārakatva verse (JP PG562:C1 ambiguous) → K2. The deceiver's frame is not a class; engine uses one frame. Finding for a later P2 row: PhD XXVI.9 PG324:C1, Sun transiting 2nd from Moon → "loss of wealth… duped by others" (Moon-frame K1, outside H).

**4. foreign_settlement** (gain). 12: YJ 46.24 PG650:C2 Jupiter 12th from Moon "travel in foreign countries"; YJ 46.30 Jupiter 12th "profitless journeys"; BPHS 52.60–61 PG629:C1 Ketu 12th from daśā lord "foreign journey"; BPHS 53.62 PG641:C1 Venus 12th from daśā lord "foreign lands" (clause OCR-broken); JP VIII.97 PG582–583:C1 Moon in 12th "live in a foreign country". 9: YJ 45.29 Saturn 9th "long wanderings"; YJ 50.29 Moon 9th "wandering"; Saravali PG114:C1/116:C2 natal 9th combinations "live in foreign countries". 7: YJ 45.28 PG648:C1 Saturn 7th "exile to a foreign land"; BPHS 11.8 "travel"; PhD I.13 "Adhvan, Marga (road)". Found, not adopted: 10 (BPHS 11.11 "living in foreign lands"); 4 (relocation precedent). Saturn K3 (YJ agent of exile/wandering → significator; inference stated); Rahu K2. Dispute: 10 vs 12 as videśa house.

**5. parental_event** (adverse) — **needs an explicit frame per `affected_person`** (enum exists, §1.1). Anchor K1: BPHS 7.39–43 PG102:C1 "The 9th from the ascendant and the 9th from the Sun deal with one's father"; BPHS 32 PG320:C1 "9th from the Sun denotes father, the 4th from the Moon mother"; BPHS 11.5 PG120:C1 4th "mother"; PhD I.14 "Pitru"; JP I.51 "Guru (father)". Offsets K3: illness/distress of the parent = the health row {6,8,12} counted from the parent's house, by BPHS 23.7 PG186:C1 ("similar deductions be made… from the 3rd and other houses") with BPHS 11.7/9/13 as premises → father {9,2,4,8}, mother {4,9,11,3}. (Bereavement's {1,2,7,8} is māraka logic — different event.) Found, not adopted: BPHS 11.4 3rd "parent's death"; 11.11 10th "father"; `graha:Sun` frame (BPHS 7/32) as a later supporting frame. The log's one event is the father's (2013); build father now, register mother. Kārakas Sun/Moon already [D].

**6. property_acquisition** (gain). 4: BPHS 11.5 "lands and houses"; PhD I.12 PG43:C1 "House, land"; JP I.50 PG61:C1 "Kshiti (land), Geha"; BPHS 15.2–4 PG141:C1; YJ 45.26/46.26/47.26 Saturn/Jupiter/Venus 4th "houses". 11: PhD I.15 "Agamana (acquisition), Labha, Prapthi"; YJ 46.30 Jupiter 11th "lands… houses"; BPHS 15.14 PG143:C1 4L–11L exchange. Mars: PhD II.3 PG47:C1 "products derived from the Earth" (K1 text; K3 step: earth-products → land/mine; registry already holds Mars as `KARAKA_UNATTACHED`). Dispute: 2 omitted.

**7. psychological_arc** (non-adverse; a **state**). 4: BPHS 11.5 "happiness"; PhD I.12 "Sukha". 5: PhD I.12 "Dhi (intelligence), Athman". 8: PhD I.14 "Adhi (mental pain), Klesa (sorrow)"; YJ 49.28 Mercury 8th "mental distraction"; YJ 50.28 Moon 8th "delusions". Found, not adopted (admission breadth): 1 (BPHS 11.2 "happiness, grief, innate nature"), 12 (PhD I.16 "Duhkha"; Hora Sara 24.49 PG283:C1). Moon K1: PhD II.2 PG47:C1 "mental tranquillity"; Mercury II.4 "intelligence". Engine: windows are arcs; valence `unqualified` unless record content supplies it (§3.2 inv 3); natal Moon enters as `karaka` promise object, no new frame. Dispute: Moon-frame primacy (P2 already carries it).

**8. spiritual_turn** (non-adverse; a **state**). 9: PhD I.14 "Acharya, Daivata, Puja, Tapas, Japa"; JP I.51 "Dharma, Tapas"; BPHS 11.10 "visits to shrines"; BPHS 41.23–27 PG407:C1 9L in Pāravatāṃśa "greatest of ascetics", Devalokāṃśa "mendicant that has renounced all mundane attachments"; YJ 46.29/49.29 "dharma". 5: BPHS 11.6 "amulets, sacred spells" (mantra — fits SPR.C/D/F devatā adoptions); PhD I.12 "Athman, Sruti, Smriti". 12: **no śloka located**; only translator notes (BPHS PG324:C2 "12th… final emancipation… Ketu"; PhD XV.22 PG186:C1 "heaven" is after-death) → **K2**. Jupiter K3 (PhD II.5 "knowledge, wisdom"; 9th "Acharya"); Ketu, Saturn K2 (UK PG84:C1/PG119:C1 commentary only). Dispute: 12 as mokṣa-sthāna is near-universal practice; 8 (tantra) arguable.

## Rule-row form (same pattern as the 18)

Registry data, not a contract change: new `P3_TRUTH_TABLE`/`ROW_MEMBERSHIP` rows, `_karaka_row` entries with loci, and P1/P3/P4 re-issued at `rule_version "1.2.0"` (1.1.0 rows untouched → `SUPERSEDED_PATHS`). Worked row:

```python
"foreign_settlement": {"H": {12, 9, 7}, "maraka_lords_of": set(),
  "provenance": "verse_cited", "operator_role": "scored", "ruling_ref": None,
  "sources": {12: "K1 yavana_jataka 46.24 PG650:C2; bphs 52.60-61 PG629:C1; jataka_parijata VIII.97 PG583:C1",
               9: "K1 yavana_jataka 45.29 PG648:C2; saravali PG114:C1",
               7: "K1 yavana_jataka 45.28 PG648:C1; bphs 11.8 PG121:C1"}},
# K2 member (spiritual_turn 12): provenance="uncited_extension", operator_role="testimony", ruling_ref="ND-H-20261005"
```

Polarity per `CLASS_UNIVERSE` (unchanged). parental_event: `_CLASS_AFFECTED_PERSON["parental_event"]="father"`, anchor row like bereavement with offsets {1,6,8,12}.

**Appendix — the 18 already-cited classes:** marriage, romantic_start {7} · separation {7,12,6} · bereavement `bhavat_bhavam:9` {1,2,7,8} · childbirth {5} · career_entry/advancement/change/setback {10,6} · education_milestone, exam_outcome {4,5} · major_gain {11,2} · major_loss {12,8} · relocation, travel_event {4,12,9} · illness_acute, chronic_onset, surgery {6,8,12} — all sourced at **path level** ("[D] Yavana Jātaka ch.45–48 + Parāśari bhāva doctrine", `source_page=None`). The eight above carry per-house loci, a stricter standard than the 18 meet.

## (a) How they enter

K1 houses enter `verse_cited/scored` at once — the §0 admission rule puts them in the same class as the 18; no ablation gate applies. K2 items enter `uncited_extension`, `ruling_ref=ND-H-20261005`, **testimony-first** (D-PADMIT pattern): a testimony house annotates and never admits, so it costs nothing and waits for B5.4 Δ-median-rank evidence. This recovers the opportunity: every class has ≥2 K1 houses, so all eight gain P1/P3/P4 scoring without any K2 scoring. The owner may rule K2 scored (D-P4 pattern); I advise against for houses (admission-changing), acceptable for kārakas (promise-condition only).

## (b) Before the FINAL sealed build

A class with new H is built in a **new generation**; a sealed one is never edited (sequencing §0 item 4; ST-H-UNKNOWN "lifting"). Landing before the one full build makes it part of `'5.0'`; after, it is `'5.1'` with `'5.0'` superseded. Must be true: (i) owner's numbered ruling recorded in `decisions/NATIVE_DIRECT_RULINGS_…` with id matching `^[A-Za-z0-9._-]+$`; (ii) registry rows above + `inventory_verifier.py:220` frame map generalised; (iii) `standing_exclusions()` stops applying the H-unknown exclusion to lifted classes (ruling file unedited); (iv) tests that hard-assert eight unknown classes updated (`test_a53_inventory`, `test_b52_registry` spiritual_turn `computed_empty`); (v) specs v1.4 FROZEN → §AM-H in `GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT` (YJ ch.49–50 citations lie outside the frozen "45–48" range — cite as supporting only, or widen); (vi) one oracle per lifted class in `GOCHARA_TEST_ORACLES`; (vii) protocol coverage reading notes the eight become P1–P4 computed.

## (c) Questions for the owner

1. spiritual_turn: ratify the 12th (K2), or build {9,5} only?
2. parental_event: father frame built now, mother frame registered but not built — acceptable?
3. K2 kārakas (Mercury, Rahu, Ketu, Saturn): testimony-first (recommended) or scored by ruling?

## Ready-to-sign ratification list (proposed ruling id `ND-H-20261005`)

- **ND-H.1** Lift ST-H-UNKNOWN-20261002 for all eight classes on the K1/K3 rows above, in the next generation.
- **ND-H.2** business_launch kāraka Mercury (trade) — no verse; OWNER-RATIFIED.
- **ND-H.3** financial_deception kāraka Rahu (deceit) — no verse; OWNER-RATIFIED.
- **ND-H.4** foreign_settlement kāraka Rahu (videśa) — no verse; OWNER-RATIFIED.
- **ND-H.5** spiritual_turn signature house 12 (mokṣa-sthāna) — translator note only; OWNER-RATIFIED.
- **ND-H.6** spiritual_turn kāraka Ketu (mokṣa) — commentary only; OWNER-RATIFIED.
- **ND-H.7** spiritual_turn kāraka Saturn (vairāgya) — commentary only; OWNER-RATIFIED.
- **ND-H.8** Operator role for ND-H.2–7: testimony until B5.4 ablation (default) / scored.

## What I did not verify

Sanskrit originals (English translations only, OCR-degraded; BPHS 53.62 clause broken). BPHS ch.32 verse number inferred from position before vv.25–30. YJ chapter/verse numbering as served (Sun = ch.44; Mercury/Moon = 49–50, outside the spec's range). Hora Sara ch.17 lists excluded as K1 (translator compilation, PG174:C1). Uttara Kālāmṛta and Sārvārtha Cintāmaṇi returned no usable house lists (OCR). Not read: PhD sannyāsa yogas, BPHS pravrajyā. Not checked: whether evaluator supports two frames per class; no test or build run; no DB write.