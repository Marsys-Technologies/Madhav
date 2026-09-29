---
artifact: CORPUS_READS
version: "1.0"
status: CURRENT
date: 2026-09-29
author: "Stream B (Śāstra)"
context: >
  Read-only verification pass against the served corpus (Postgres `amjis`,
  table `classical_text_chunks`) for the Pravāha campaign, resolving the
  `[U]` register of FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md §8.
  F-32 discipline: every absence claim carries its count(*) and exact
  predicate; every positive read quotes chunk text verbatim with locator.
---

# CORPUS_READS v1.0 — served-corpus verification, Stream B (doctrine)

## 0. Schema and locator scheme (for reproducibility)

```
select column_name, data_type from information_schema.columns
 where table_name='classical_text_chunks' order by ordinal_position;
```
Columns: `id uuid`, `text_id text`, `chunk_id text`, `verse_ref text`,
`chapter smallint`, `verse_start/end smallint`, `content_sa`, `content_en`,
`content_summary`, `topics[]`, `source_citation`, `translator`,
`cleaned_translation_text`, `cleaned_devanagari_text`, `ocr_confidence_score`,
`low_confidence_flag`, plus OCR-pipeline metadata and an `embedding` column.
Best available display text per chunk: `coalesce(cleaned_translation_text, content_en)`
(English texts) / `coalesce(cleaned_devanagari_text, content_sa)` (Tājaka).

Locator scheme (all texts): `verse_ref = 'PG<page>:C<chunk>'`, zero-padded
`chunk_id = '<text_id>_pg%04d_c%02d'`. `chapter` is unreliable (carries page
numbers in some texts). **The brief's `bphs_vol2` locator space
(`3256-3262`, `3593-3596`, `40799-41558`) does not exist in the served
table** — there is a single `bphs` text_id (1459 chunks); the target passages
were located by content predicates instead (§6, §9).

`select text_id, count(*) from classical_text_chunks group by 1 order by 1;`
→ 15 texts, 10,651 chunks total: bhrigu_nandi_nadi 608, bphs 1459,
bphs_jaimini 264, brihat_jataka 607, brihat_samhita 1171, hora_sara 460,
jataka_parijata 704, muhurta_chintamani 274, nadi_navamsa_patel 1850,
phaladeepika 564, saravali 471, sarvartha_chintamani 342,
tajaka_neelakanthi 290, uttara_kalamrita 289, yavana_jataka 1298.

---

## 1. Phaladīpikā XXVI.25–29 — sign-third fruition, saptaśalākā, Abhijit, eclipses — [D]

**Predicate:** `select verse_ref, coalesce(cleaned_translation_text,content_en) from classical_text_chunks where text_id='phaladeepika' and verse_ref in ('PG331:C1','PG332:C1','PG333:C1','PG334:C1') order by verse_ref;`

**Evidence (verbatim):**

- PG331:C1 (śl.25): "Sloka 25.—Mars and the Sun produce effect (during their passage) when they are in the initial lOdegreos or first decanate of a sign. Jupiter and Venus become effective when they are in the middle portion of a sign (2nd decanate) while the Moon and Saturn bear fruit when in the last portion. Mercury and Baku produce effect throughout their passage," — and (śl.26): "Sloka 26,—Draw seven lines horizontally (from west to east) and over them draw seven lines vertically, The 28 extremities or points reckoned from the north-east are to be assorted to the 28 stars (including Abhijit)"
- PG332:C1 (saptaśalākā grid; Abhijit between Śravaṇa and U.Aṣāḍha): "Sravana … Abhiiit … U. Asliadha … counted from Krittika … If the star ..occupied by the Sun at the time happens to be the Vedha asterism to the natal star, danger to life has to be apprehended ; if to the (Adhana Nakshatra, 19th from Janmanakshatra) f there will be fear and anxiety ; if to the (10th from …"
- PG333:C1 (śl.27–29): "Sloka 27.—If any one of the three astorisms referred to above be thus marred by the occupation of other malefics (other than the Sun), death may happen ; if by benefica, there will be no danger to life. … Sloka 28 .— If the 19th, I Oth, 3rd, 1st, the 23rd, the 5th or the 7lli (all reckoned from the Janma-tara) are afflicted by malefics during their tramsit, there will bo danger to life, But if Lhe idanei be bonefic, failure in business will be {he only result. … Sloka 29 —The three asterism (w/„ Janma, (Anujanmal, (Trijanma), 1st, 10th, and 19th) falling on a day identical with the Sun's Sankramana (Sun's entry into a new Rasi) or at a time when any of the other planets transit from one Rasi to another, or when there is an eclipse, planetary war (Grahayuddha) or a fall of meteors …"
- PG334:C1 (śl.29 cont.): "Ulkanipata) or other unexpected occurrence, death or a similar untoward event should be expected."

**Verdict:** [D]. Śl.25 = sign-third (decanate) fruition keyed by planet; śl.26–28 = saptaśalākā with the 28-star Abhijit scheme and janma/ādhāna/karma (1st/19th/10th) star-vedha; śl.29 = janma/anujanma/trijanma stars coinciding with saṅkrānti, ingress, eclipse, grahayuddha or ulkā → death-grade event.

**Consequence:** P12 (star-limb/sign-third/saptaśalākā) and the eclipse limb of P7 are corpus-admissible; the Abhijit 28-star grid is the operative scheme.

## 2. Phaladīpikā XXVI.30–32 — transit-to-transit modification — [D]

**Predicate:** as §1, PG334:C1.

**Evidence (verbatim), PG334:C1:** "Sloka 30.—A planet yielding unfavourable result when aspocted by a benefic, or the one that gives good resulLs if aspected by a malefic, both become void of effect. The same will be the case if they are aspected by their respective inimical planets. … Shka 3L—A planet in an untoward Bhava, if he is in exaltation or Swakshetra, will not do any harm* If in such favourable position, he should also occupy a favourable Bhava, he will give full beneficial results (effect) to the native during his transit in that Bhava. … Sloka 32—Planets in their transit through favourable places (houses wherein they should give good effects) become void of effect if they happen to be at the time in their depression or inimical houses or be in an eclipsed state. But if the houses transitted be also unfavourable, they give bad effects and that too in an aggravated form."

**Verdict:** [D]. The already-counted claim (§8 register "transit-to-transit modification — PG334 (śl.30)") is confirmed verbatim; śl.31–32 add dignity (uccha/svakṣetra vs nīca/śatru) and combustion/eclipsed-state ("eclipsed state") modifiers.

**Consequence:** P11 (transit-to-transit) admission stands with four named operators: aspect-reversal, inimical-aspect nullification, exaltation/own-sign rescue, debilitation/combustion nullification-or-aggravation.

## 3. Muhūrta Cintāmaṇi — tārā-bala and chandrāṣṭama — tārā [D]; generic chandrāṣṭama-avoidance absent by predicate (0)

**Predicates (counts against `text_id='muhurta_chintamani'`, 274 chunks):**

```
select count(*) filter (where coalesce(cleaned_translation_text,'')||' '||coalesce(content_en,'')
  ~* 'tara.?bala|nine.?fold|janma.?tara|sampat|vipat') … → 2
select count(*) filter (where coalesce(cleaned_translation_text,'')||' '||coalesce(content_en,'')
  ~* 'chandra.?ashtama|chandrashtama|eighth from the moon|8th from the moon|8th house from the moon') … → 0
select count(*) filter (where coalesce(content_sa,'')||coalesce(cleaned_devanagari_text,'')
  ~ 'चन्द्राष्टम|चंद्राष्टम|चन्द्राष्ट|चंद्राष्ट') … → 0
```

**Evidence (verbatim):**

- PG67:C1: "The parihāra (remedial cancellation) of the evil tārās in a necessary undertaking … In the first cycle, the whole of vipat, pratyari and mṛtyu gives no good; in their second [cycle the portions to be avoided are] the first, middle and last thirds respectively [?]; and in the third, all are held to be auspicious. ‖ 13 ‖ [ṭīkā] … in the vadha (7th) tārā give sesame and gold; in vipat (3rd), jaggery, sugar and the like; in the janma tārā, greens (śāka); in pratyari (5th), salt."
- PG79:C1: "When the tārā (the \"star\", i.e. the nakṣatra of the day reckoned in the nine-fold count from the janma-nakṣatra) is defective, then if the Moon occupies a trikoṇa (trine) or is exalted, or stands in the ṣaḍvarga … of a benefic … kṣaura (shaving/tonsure) is still proper. When the Moon is in an auspicious nakṣatra … even a duṣṭa-tārā … is to be known as commended for such acts as kṣaura and yātrā."

Nearest 8th-from-Moon material (context-specific, not a generic avoidance rule):

- PG50:C2: "It is especially so when the Moon stands in the 4th, 8th or 12th by transit [from the natal rāśi]." (ārtava/illness-fatality context, v.47)
- PG72:C1 (garbhādhāna exclusions): "जन्मरग्न जन्मरारिमें अष्टम रग्न … गर्भाधानमे बजित करे" (8th sign from janma-lagna/janma-rāśi to be avoided for garbhādhāna)

**Verdict:** nine-fold tārā-bala with the āvṛtti-cycle refinement and parihāra: [D]. Chandrāṣṭama-as-general-avoidance: **0 by three independent predicates** (English lemma, Devanagari compound, Devanagari co-occurrence) — the absence claim stands; only context-bound 8th-from-Moon rules exist (sickness, garbhādhāna).

**Consequence:** navatārā admission is safe with the MC cycle/thirds refinement; any generic "avoid Moon-in-8th" election filter must remain `uncited_extension` unless another text supplies it.

## 4. Tājaka Nīlakaṇṭhī — saham ACTIVATION rule — [D]

**Predicates (counts against `text_id='tajaka_neelakanthi'`, 290 chunks; English predicates return 0 — Devanagari only):**

```
select count(*) filter (where coalesce(content_sa,'')||' '||coalesce(cleaned_devanagari_text,'') like '%सहम%') … → 28
select count(*) filter (… like '%मुन्था%') … → 2   [brief's "5" used broader मुन्थ/मुंथ/मुथ stems: 6 chunks]
select count(*) filter (… like '%वर्षेश%') … → 4
```

**Evidence (verbatim; OCR-degraded Devanāgarī/Hindi ṭīkā, quoted as served):**

- PG95:C1 (v.25 — the activation rule, end of the saham-definition chapter): "उपजा०-स्वनाथदीनं सदमं तदंशाः स्वीयोदयत्रा विहताशः शत्या ॥ तत्सद्यपाको दिवसंहिं ग्धः स्यात्तदशाय तदसंभवेवा ॥ २५ ॥ सहमका फ पाकसमय कहते हँ कि, सहमका फर पाकसमय चाहिये स्वामीका अंश करकं स्वदेशीय कर देना यह सयं स्पष्ट जिस समयपर आवे वह समय सहम्‌ फर पाकका जानना कोद कहते है, कि, हीनांश पात्यांश कमस जब ॒सहमेशकी दशा हो.तब फर होगा, यह सवं संमत हे।" — "when the daśā of the sahameśa runs, then the fruit; this is agreed by all" (with the alternative pāka-time view recorded beside it).
- PG147:C1 (putra, 5th-bhāva chapter): "पंचमभाव वा पुत्रसहम बठसहित्‌ हो तो पूत्ापि होती है शुमगरहकी इष्टि भी उसपर हो तो अति सुख पुतरसेवंधी होता है,जो वर्षेशं भी पंचम हो तो फट देता है" — putra-saham strong + benefic aspect, and varṣeśa in the 5th → delivery.
- PG155:C1 (vivāha, v.12): "जन्मके वा वषके श्ीसहममं मगर शक्रकी दि हा तो विवाहापि होती हे ओर श्नीसहमपर शुक तथा सहमेशकी ृष्टिसे यही फ है ॥१२॥" — Mars/Venus dṛṣṭi on the strī-saham (natal or annual), or Venus + sahameśa dṛṣṭi → marriage.
- PG160:C1 (mṛtyu, v.19–20): "वषटग्रसे अष्टमेश अष्टमगत हो तो मृत्यु होता है ॥ १९॥ … मुथदेशोऽब्दपोवापिमृत्युतत्रविनिदिशत्‌ ॥ २० ॥ पण्यसहममे पापुग्रह हो ओर अष्टमेश तरिकस्थान ६। < । १२महा मृत्यु होवे ओर वषश वा मृथेश पापाक्रांत त्रिकस्थान ६ । < । १२ मं हो तो मृत्यु देता है कहना ॥ २० ॥" — muntheśa (मुन्थेश) or varṣeśa malefic-afflicted in trika 6/8/12 → death.
- PG132:C1 (v.13, 16): "जन्मट्भरेश वषश ओर मुंथा तीनौ बारहवे चौथे आवै ओरचक्डे स्थानामंसे किमे साथी हो तो भृत्यतुल्य कष्ट हेव … स्वदशायां निधनदो … ठभ्रमे जिसका हदा तत्कार हो वह ओर ठ्ेश सप्तम अष्टम वा बारह पापयुक्तं हो तो अपनी दशाम मृत्यु देते है" — munthā co-located with janmeśa/varṣeśa in dusthānas; "स्वदशायां निधनदः" — delivers in its own daśā.

**Verdict:** [D]. Activation is stated in three modes, all in the served chunks: (i) **sahameśa-ki-daśā** (PG95:C1, "सर्वसम्मत" — daśā of the saham lord delivers the saham's fruit); (ii) **varṣeśa contact** (PG147, PG160); (iii) **munthā/muntheśa contact** (PG132, PG160). Mudda-daśā per se: the word मुद्दा does not occur (predicate `मुद्द|मुद्दा` → 0 outside unrelated stems); the daśā spoken of is the varṣa daśā — consistent with Mudda but not named as such.

**Consequence:** P9 (annual path) admission: saham delivery = sahameśa daśā + varṣeśa/munthā contact, with the pāka-day alternative recorded. The un-named-Mudda gap is a labelling [U], not a doctrinal one.

## 5. Phaladīpikā Moon-relative NODE results recount (D-RQ3) — [D]

**Predicates:**

```
select count(*) filter (where coalesce(cleaned_translation_text,'')||' '||coalesce(content_en,'') ~* 'rahu|ketu') … → 89
select count(*) filter (where … ~* 'rahu|ketu' and … ~* 'from the moon|janmarasi|janma.?rasi|moon.?s lagna') … → 5
```

**Evidence (verbatim):**

- PG321:C1 (XXVI.1–2): "Sloka l—Of all the Lagnas it is only the Moon's Lagna that is most important for ascertaining the (Gocharaphala-effect of transits), One ought therefore to calculate and predict from the Moon's place … Sloka 2,—During transit, the Sun gives good results when he is in the 6th, 3rd and 10th houses (counted from the Moon), … all planets in the 11th; Venus in all places other than the 10th, 7th and 6th. Hahu and Ketu are similar to the Sun."
- PG331:C1 (XXVI.24): "Sloka 24. —The following are the effects in their order caused by Rahu during his transit through the 12th house counted from the Janmarasi (1) sickness or death (2) loss oi wealth (3) happiness (4) sorrow (S) financial loss (6) happiness (7) loss 8) danger to life (9) loss (10) gain (11) happiness and (12) expenditure,"

**Verdict:** [D]. The served chunks carry Moon-lagna primacy (XXVI.1), the per-planet favourable-house table with "Rāhu and Ketu are similar to the Sun" (XXVI.2), and a 12-house Moon-relative (janmarāśi) Rāhu result list (XXVI.24, PG331:C1). (Ketu's own list is not separately served — subsumed by the XXVI.2 equivalence; PG331:C2 does not exist in the table.)

**Consequence:** D-RQ3 recount complete: Moon-relative node gochara results exist in the served corpus; per N-14, no nodal aspect is thereby authorised.

## 6. Aṣṭottarī daśā applicability — BPHS — [D], but at relocated locators

**Locator discovery:** the brief's `bphs_vol2:3256-3262, 3593-3596` does not resolve — `select … where chunk_id like '%3256%' or source_citation like '%3256%'` → 0 rows; the served `bphs` is one volume with PG locators. Content predicates (`~* 'a[st]+o+t+[a3]r'` on translation, `'paksha'` window PG505–512) located the chapter-46 passage at **PG505:C1, PG506:C1, PG508:C1**.

**Evidence (verbatim):**

- PG505:C1 (vv.17–20): "17-20. The Sage said-O Brahmin, the learneds have 'ecommended the adoption of Astottari Dasa, when Rahu not 'ireing in Lagna, in any other Kendra (quadrant) or trikona"
- PG506:C1 (cont.): "(trine) to the lord of the Ascendant (Lagna). From 4 nakshatras from Aridra commences the Dasa of the sun …"
- PG508:C1 (v.23, OCR-degraded but legible in structure): "23. It will be advisable to adopt the Astqllp1i Dasa if the birth be in the dav i1 lllgfura putsrfi- … in Shukla Paksha (Br, … of the month)."

**Verdict:** [D] on both conditions as served: (i) Rahu not in lagna, in a kendra/trikoṇa **from the lagna lord** (vv.17–20, PG505:C1–PG506:C1); (ii) the pakṣa condition at v.23 (PG508:C1) — day-birth/Kṛṣṇa-pakṣa and night-birth/Śukla-pakṣa wording survives OCR only partially ("birth be in the day [in Kṛṣṇa pakṣa] … in Shukla Paksha"), so the *fine grain* of v.23 is [D-with-OCR-degradation]; the canonical reading (day birth in Kṛṣṇa, night birth in Śukla) is the only reading consistent with the surviving halves.

**Consequence:** RQ-7 stands: on the canonical chart (Rahu 8th from lagna lord; day birth in Śukla pakṣa) both conditions fail and the Aṣṭottarī vote must be *absent*. The pakṣa operand itself comes from L1, not the corpus.

## 7. Venus vedha pairs — PG323:C1 śl.8 — [D]; KP Reader discrepancy recorded

**Predicate:** `select … where text_id='phaladeepika' and verse_ref='PG323:C1';`

**Evidence (verbatim), PG323:C1:** "Sloka 8.—Venus will give bad effects during his transit through 1st, 2nd, 3rd, 4th, 5th, 8th 9 th, 12th and 11th, if he is marred by planets in the corresponding (Vedha) places, viz., 8th, 7th, 1st, 10th, 9th, 5th, 11th, 6th and 3rd respectively."

Reading the correspondences in order: 1→8, 2→7, 3→1, 4→10, 5→9, 8→5, 9→11, **12→6, 11→3**.

**Verdict:** [D]. The served Phaladīpikā gives **12th-transit ↔ 6th-vedha** and **11th-transit ↔ 3rd-vedha**. The KP Reader vol.5:1330–1337 transcription (11→6, 12→3) is a transcription-order discrepancy against the served text; per D-RQ8 the served reading governs.

**Consequence:** `bg_transit_rules.rule_notes` for the Venus vedha rows should record: "KP Reader v5 transcribes 11→6/12→3; served Phaladīpikā PG323:C1 śl.8 reads 12→6, 11→3 (verbatim above); served text adopted."

## 8. Kakṣyā by contributor — Phaladīpikā XXIII, PG301 — [D]

**Evidence (verbatim), PG301:C1 (Adh. XXIII, śl.18–19):** "Sloka 18.—The Lagna, the Moon, Mercury, Venus, the Sun, Mars, Jupiter and Saturn are the lords of the divisions indicated in the eight rows extending from south to north of each sign, and every one of them yields the effect of the benefic dot appearing against it in any of the 12 houses when the planet whose Ashtakavarga is under consideration transits in the house the particular division of the planet yielding the benefic dot … Sloka 19.—Divide the Rasi into 8 equal divisions* The first division belongs to Saturn; the 2nd to Jupiter, that i% any benefic dot put forth by Jupiter will como to fnutitin during the transit over the 2nd division of the liaM,"

**Verdict:** [D]. Fruit is delivered in the kakṣyā (⅛-sign division) **owned by the mark-donor**, when the AV-owning planet transits that division; division order begins Saturn, Jupiter, … (śl.19).

**Consequence:** the kakṣyā-by-donor key for the T0-10 L1 kakṣyā work is corpus-verified.

## 9. Piṇḍa-nakṣatra timing — Phaladīpikā XXIV (PG304, PG307) [D]; BPHS Sun-AV father procedure [D], relocated

**Phaladīpikā evidence (verbatim):**

- PG304:C1 (śl.2–3): "Sloka &—-The figure thus arrived at should be divi-ded by 27. When Saturn transits through the asterism counted from Aswint indicated by this remainder, some thing untoward to the father will without doubt come to pass. … Sloka 3.—Or, when Saturn traverses through an asterism which is trine to the aforesaid asterism, the demise of the father or one similarly situated will happen. The sum-total of the figures remaining after the 2 reductions is known as (Sodhyapinda),"
- PG307:C1 (śl.13): "Sloka 13.—In Saturn's Ashtakavarga, multiply the (Sodhyapinda) figure by the number indicat-ing the benefic dots in the 8th house from the Lagna and divide the product by 27. When Jupiter or Saturn in his transit passes through the star (counted from Aswini) signified by the remainder, the demise of the native may be expected."

**BPHS side — locator discovery:** brief's `bphs_vol2:40799-41558` does not resolve (see §6). Content predicate (`ashtakavarga AND 9th AND sun`) located the passage at **PG874:C1–PG876:C1**; the served edition heads it "Chapter 70" at PG875:C1 — i.e. the chapter number matches even though the locator space does not.

- PG874:C1 (vv.7–9): "7-9. The 9th house iiom the Sun at the time of birth deals with father. The ;ekhas of the rasi (of that house) as marked in the Suu's Ashtakavarga should be multiplied by tho Yoga Pinda and the'product be divided by 27 (the number of nakshatras). The rcmainder will denote the number of nakshatra begirrning from Ashwini. The father will be in dis-tress or he will otherwise suffer when Saturn in transit passes through that nakshatra. Even when Saturn passes in transit the trikona nakshatras (5th and 9th), father or relatives lilte father may die or suffer."
- PG875:C1 (worked example + v.10–11 ÷12 rāśi variant): "Illustration-See the Sun's Ashtakavarga given earlier' Ttre Sun is in Capricorn, iht qih tusi from which is Virgo' There-fore, the Ashtakavarga rekha number of Virgo 2 may bc multipliedby 148 … the remainder *tli;;\ 26' The i6th nakshatra from Aswini is Uttarabhadra … the deathliin fntt will take place if an inaus-picious Dasa be it … Should the Dasa be auspicious o, f\"no.uro'bi, the father will be in great distress … I G' I I . If the Ashtakavarga rekha lumber is urultiplied b1 tn\" voga pinda and;;;;ffi is divided bv f2'.the'r\"t-iT5] will denote the rasr through which-or through the rasts ri trikona to it, the ,run'i'oi 5u'urn will cause harm or unfavourable efrects to father … if th Dasa prevailing at tnai time be unfavourable' If the Dasa b favourable father *itt foo only adverse effects (like seriou illness)."
- PG876:C1 (v.12–14): "12-14. The death.of the father may be cxpect:d if Rahu, Saturn or Mars are in the Cth from tne Sim at thc time of transit ofSatum through any ofthe tbovc thrce Rasis (trikona Rrsis). … Thc death docs not take pracc if a favourabre Dasa be in brce at thc timc of saturn's transit."

**Verdict:** [D] both texts. Phaladīpikā XXIV gives śodhya-piṇḍa × marks ÷ 27 → nakṣatra from Aśvinī; Saturn (father, PG304) and Jupiter/Saturn (self, PG307) over it or trine times the event. BPHS ch.70 (served at PG874–876) carries the Sun-AV father procedure: 9th from natal Sun (worked example: Sun in Capricorn → Virgo), rekhas × Yoga-piṇḍa (148) ÷ 27 → star (worked: Uttarabhadra), Saturn over it or trine (Puṣyamī/Anurādhā), daśā-gated.

**Consequence:** the §4 father-event investigation is fully operable from the served corpus: both operand sets (9th-from-Sun rāśi; Sun-AV rekha count; Yoga-piṇḍa 148; ÷27 and ÷12 variants; trikona stars; daśā gate) are [D].

## 10. Double-transit joint rule — Phaladīpikā XVII.12, PG216 — [D]; only joint rule by predicate

**Evidence (verbatim), PG216:C1:** "Shka 12.—.Ascertain the Navamsa, the Dwadasamsa and the Drekkana indicated by the figures for Mandi. When Jupiter arrives at the Navamsa, Saturn at the Dwadasamsa and the Sun at a triangular sign from the Drekkana in question, and when the Lagna is the Rasi occupied by the lord of the sign denoted by the aggregate of the figures for the Lagna, the Moon and Mandi, death will take place."

**Absence claim (other joint Jupiter+Saturn passages), with own predicates:**

```
select count(*) from classical_text_chunks where text_id='phaladeepika'
 and t ~* 'jupiter' and t ~* 'saturn'                                        → 93
 … and t ~* 'transit|gochara|passes through|arrives at'                      → 24
 … and t ~* 'death|die|demise|decease'                                       → 16
```
(t = coalesce(cleaned_translation_text,'')||' '||coalesce(content_en,''))

All 24 transit-co-mention chunks were enumerated by locator; the Adh. XVII cluster (PG213:C1, PG214:C1, PG215:C1, PG216:C1, PG217:C1) was read in full. PG213–215, PG217 are **single-planet** rules (Saturn alone over the derived rāśi/navāṃśa; Jupiter alone). Only **PG216:C1 śl.12 states a joint condition** (Jupiter at the Māndi-navāṃśa AND Saturn at the Māndi-dvādaśāṃśa, with Sun at drekkana-trikona). The register's "11 co-mention chunks, only PG216 is a joint rule" used a tighter predicate than reproduced here; under the broader, reproducible predicates above (93/24/16) the substantive conclusion is unchanged: one joint rule, at PG216.

**Verdict:** [D] for the rule; [D] for its uniqueness as a *joint* Jupiter+Saturn rule in the served Phaladīpikā.

**Consequence:** P4 (double transit) has exactly one corpus anchor; per RQ-8 the "§double-gochara" citation string is struck in favour of `[P]` + PG216 precedent, and any generic double-transit scorer is `uncited_extension`.

---

## Summary table

| # | Read | Locator(s) | Verdict |
|---|------|-----------|---------|
| 1 | Phaladīpikā XXVI.25–29 — sign-third, saptaśalākā, Abhijit, eclipses | PG331:C1, PG332:C1, PG333:C1, PG334:C1 | [D] |
| 2 | Phaladīpikā XXVI.30–32 — transit-to-transit modification | PG334:C1 | [D] |
| 3 | Muhūrta Cintāmaṇi tārā / chandrāṣṭama | PG67:C1, PG79:C1 (tārā); chandrāṣṭama-avoidance 0 by 3 predicates | tārā [D]; generic chandrāṣṭama absent (0) |
| 4 | Tājaka saham activation | PG95:C1 (sahameśa daśā), PG147:C1, PG155:C1, PG160:C1, PG132:C1 | [D] (Mudda un-named: 0 by predicate — labelling [U]) |
| 5 | Moon-relative node results (D-RQ3) | PG321:C1, PG331:C1 | [D] |
| 6 | Aṣṭottarī conditions (BPHS) | PG505:C1, PG506:C1, PG508:C1 (brief's bphs_vol2 locators do not resolve) | [D] (v.23 OCR-degraded) |
| 7 | Venus vedha pairs | PG323:C1 śl.8: 12→6, 11→3 | [D]; KP Reader discrepancy recorded |
| 8 | Kakṣyā by contributor | PG301:C1 | [D] |
| 9 | Piṇḍa-nakṣatra timing (both texts) | PG304:C1, PG307:C1; BPHS PG874:C1–PG876:C1 | [D] |
| 10 | Joint Jupiter+Saturn rule | PG216:C1; uniqueness under stated predicates (93/24/16) | [D] |

All queries were read-only `select` statements against `classical_text_chunks`. No writes were issued; no other file was modified.
