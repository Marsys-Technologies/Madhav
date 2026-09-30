---
artifact: PROMISE_NATURE_YOGA_MAP
canonical_id: PROMISE_NATURE_YOGA_MAP
version: "1.1"
status: CURRENT
supersedes: "design/PROMISE_NATURE_YOGA_MAP_v1_0.md (commit 1a85ce862; retained as history — v1.1 adds the cited ṣaḍbala pūrṇa-bala thresholds and bhāva-bala rule, Phaladīpikā IV.22–24)"
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
item: "B5.2 — promise as strength + condition; agent nature and maitrī; cited yoga→event map"
spec: "design/GOCHARA_DESIGN_SPECS_v1_4.md (FROZEN) §0, §1.2 inv 8, §2.2 P1 factor inventory, §2.3 inv 8"
doctrine: "sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md (SEALED) — promise strength AND condition; nature/maitrī as interpretive modifiers; yogas only with a cited yoga→event relation"
corpus: "Postgres amjis.classical_text_chunks, read-only; every absence claim carries count(*) and predicate (F-32)"
evidence_labels: "[D] served corpus text:page · [P] practice, uncited_extension with ruling · [R] native ruling · [U] unverified"
---

# B5.2 — promise, agent nature & maitrī, cited yoga→event map

Scope discipline (v3.0, sealed): yogas enter the rule paths **only with a cited yoga→event
relation**; natural/functional nature and maitrī are **interpretive modifiers** — named factors
in the P1 inventory (spec §2.2), `calibration_status = uncalibrated_default`, rank-only,
entering no served claim of magnitude. Nothing here promotes any `testimony` operator to
`scored`; promotion is the §2.2 gate (B5.4 ablation evidence) alone.

## 1. Promise = strength × condition (spec §2.3 inv 8, O-RP-6)

Doctrine statement (v3.0 L0 layer): a chart's promise for an event class is the product of a
**strength** factor and a **condition** predicate — "an afflicted 7L promises marriage *with
difficulty*, it does not deny it" (Codex B, sealed v3.0 §5). Constant-presence promise is the
#1 defect; O-RP-6 fails any implementation where promise survives a false condition.

### 1.1 Strength factors (named, each with its citation)

| factor_id | content | numeric mapping | source |
|---|---|---|---|
| `dignity_sign` | transit/natal sign dignity for the object lord: exaltation > mūlatrikoṇa > own > extreme friend's > friend's > neutral's > enemy's > debility | doctrine-ordered categories; the saptavargaja-bala virūpa scale is the cited numeric anchor: mūlatrikoṇa 45, own 30, extreme friend's 20, friend's 15, neutral's 10, enemy's 4, extreme enemy's 2 virūpas | [D] BPHS ch.27 śl.2–4 (`bphs` PG264:C1, verbatim §4.1 below); categories [D] BPHS ch.3 śl.49–55 (§4.2/§4.3) |
| `combustion` | graha eclipsed by the Sun (astāṅgata) — strength loss; BPHS ch.45 (?) avasthās list Kopa = "eclipsed by the Sun" | categorical (combusted / not) | [D] BPHS PG449:C1 śl.8–10 ("…in being eclipsed by the Sun — Kopa"); transit-side combustion/dignity per Phaladīpikā XXVI.30–32 as cited in v3.0 §5 |
| `sad_bala_summary` | ṣaḍbala / bhāva-bala summary as L1 operands | L1 operand values, never recomputed here; the cited sufficiency thresholds (pūrṇa-bala): Sun 6.5, Moon 6, Mars 5, Mercury 7, Jupiter 6.5, Venus 5.5, Saturn 5 rūpas; bhāva-bala = lord's strength + 1 rūpa + dig-bala + dṛg-bala of the bhāva | [L] L1; thresholds [D] Phaladīpikā IV.22–24 (`phaladeepika` PG79:C1, PG80:C1, verbatim §4.11); structure [D] BPHS ch.27–28, values are chart operands |

The virūpa scale is the **ordering anchor only** while `uncalibrated_default`: it fixes the
doctrine's stated order (exaltation > own > friendly > neutral > inimical > debility, per the
factor schema); it enters no magnitude claim until L5 calibration (spec §2.1 factor contract).
The same discipline holds for the pūrṇa-bala thresholds: they declare what "strong" means in
the text; the binary strong/weak predicate they induce is citable, any finer scaling is not.

### 1.2 Condition predicates

The condition side is the **affliction predicate** of spec §1.2 inv 8 evaluated on the class's
promise objects (signature house, its lord, its occupants, its kārakas): `afflicted(x) ⇔ ∃` a
row with agent ∈ {Saturn, Mars, Rahu, Ketu — per the citing rule}, relation ∈ {conjunction
within orb | aspect}, object = x. Unevaluated ⇒ `unqualified`, never assumed false.

Cited exemplar — the marriage-class condition, Phaladīpikā X.15 **[D] `phaladeepika`
PG145:C1** (verbatim §4.4): "If the lord of the 7th house occupies an inimical or depression
sign, or be eclipsed, or be aspected by malefics and if the 7th house be associated with or
aspected by malefics, there will be loss of wife; so say the wise." — lord condition
(inimical/debility sign, combustion, malefic aspect) AND house condition (malefic
occupation/aspect), both named, mapping to the `separation` class's promise-condition row.

## 2. Agent nature — natural benefic/malefic (named interpretive factor)

**[D] BPHS ch.3 śl.11 (`bphs` PG26:C1, verbatim §4.5):** "Among these, the Sun, Saturn, Mars,
decreasing Moon, Rahu and Ketu … are malefics while the rest are benefics. Mercury, however, is
a malefic if he joins a malefic."

- Malefics: Sun, Saturn, Mars, **waning** Moon, Rahu, Ketu; Mercury when conjunct a malefic.
- Benefics: Jupiter, Venus, **waxing** Moon, unaffiliated Mercury.
- Moon's pakṣa rule, translator's note quoting Saravali at the same chunk (PG26:C2): waning
  (Kṛṣṇa pakṣa) malefic, waxing (Śukla) benefic; "Should the Moon be conjunct a benefic or
  aspected by a benefic, she turns a benefic, even if in a waning state."

Factor rows: `agent_nature` (direction: benefic → favourable channel; malefic → adverse
channel, class-relative per spec §3.1), `mercury_affiliation` (condition predicate on Mercury),
`moon_paksa` (operand from L0/L1 Sun–Moon elongation). All `uncalibrated_default`; they modify
channel assignment/valence annotation, never admission (spec §2.3 inv 3 — no soft factor
zeroes an admitted window).

## 3. Maitrī (relationship) modifiers

Three tiers, all [D] BPHS ch.3 (`bphs` PG39:C1–PG40:C2):

### 3.1 Naisargika (natural) maitrī — śl.55 [D] PG39:C1

Rule (verbatim §4.6): "Note the signs which are the 4th, 2nd, 12th, 5th, 9th and the 8th from
the Moolatrikona of a planet. The planets ruling such signs are its friends apart from the lord
of its exaltation sign. Lords other than these are its enemies. If a planet becomes its friend
as well as its enemy … then it is neutral or equal."

The printed table (PG39:C2, verbatim §4.7) is **OCR-degraded** (columns interleaved; the
"Equals" column partially lost). The table below is therefore **derived from the śl.55 rule**
applied to the mūlatrikoṇa/exaltation data of §4.2 (themselves [D] PG37:C1–PG38:C2), cell by
cell, and cross-checked against the readable fragments of PG39:C2 (Sun row "Moon, Mars, Jupiter
/ Venus, Sat[urn]"; Mercury row friend "Sun…", enemy "Moon"; Saturn row friends "Mercury,
Venus" — all match). Derivation, not transcription — recorded honestly:

| planet | friends | enemies | neutral |
|---|---|---|---|
| Sun | Moon, Mars, Jupiter | Venus, Saturn | Mercury |
| Moon | Sun, Mercury | — (none) | Mars, Jupiter, Venus, Saturn |
| Mars | Sun, Moon, Jupiter | Mercury | Venus, Saturn |
| Mercury | Sun, Venus | Moon | Mars, Jupiter, Saturn |
| Jupiter | Sun, Moon, Mars | Mercury, Venus | Saturn |
| Venus | Mercury, Saturn | Sun, Moon | Mars, Jupiter |
| Saturn | Mercury, Venus | Sun, Moon, Mars | Jupiter |

Check against the rule, worked once in full (Moon): Moon's mūlatrikoṇa is Taurus (§4.2, śl.53 —
the MT-degree phrase for the Moon is itself OCR-degraded in PG38:C1/C2; the *sign* Taurus is
unambiguous from the standard reading and from the śl.53 residue "the first 12 degrees in
Aries" belonging to Mars). From Taurus: 2nd = Gemini (Mercury), 4th = Leo (Sun), 5th = Virgo
(Mercury), 8th = Sagittarius (Jupiter), 9th = Capricorn (Saturn), 12th = Aries (Mars);
exaltation sign = Taurus (own — no new lord). Friendship candidates: Mercury, Sun, Jupiter,
Saturn, Mars. Enemies would be the 3rd/6th/7th/10th/11th lords: Cancer (Moon — self, excluded),
Virgo (Mercury — already friend ⇒ neutral? no:) — Mercury appears in **both** computations for
Moon (2nd/5th lord = friend; 6th lord = enemy) ⇒ by śl.55's last clause Mercury should be
**neutral**, yet the PG39:C2 fragment prints Mercury under Moon's friends with enemies "—" and
the translator's note (PG40:C1) records Parāśara's statement that "the Moon does not consider
anyone as her enemy … the Sun and Mercury are Moon's friends while others are her neutrals".
**Ruled content:** the Moon row follows the printed table + translator's Parāśara citation
(friends Sun, Mercury; no enemies) — the śl.55 mechanical derivation for Moon is overridden by
the text's own exception; recorded as [D] PG39:C2 + PG40:C1 with this note. All other rows
follow śl.55 exactly (each checked, arithmetic of the same shape, available on request).

### 3.2 Tatkālika (temporary) maitrī — śl.56 [D] PG40:C1

"The planet posited in the 10th, 4th, 11th, 3rd, 2nd or the 12th from another becomes mutual
friend. There is enmity otherwise. (This applies to a given horoscope.)" — a chart-dependent
predicate on natal positions (L1 operand).

### 3.3 Pañcādha (compound) maitrī — śl.57–58 [D] PG40:C2

"Should two planets be naturally and temporarily friendly, they become extremely friendly.
Friendship on one count and neutrality on another count make them friendly. Enmity on one count
[and friendship on the other ⇒ neutral; enmity on both ⇒ extreme enmity]" (chunk truncates;
the standard five-fold result {extreme friend, friend, neutral, enemy, extreme enemy} matches
the saptavargaja scale's "extreme friend"/"extreme enemy" categories of §4.1 — the truncated
tail is flagged, not reconstructed as citation).

**Node maitrī:** the PG40:C1 "Rahu/Ketu" friendship lists are the **translator's** appended
note ("As for Rahu and Ketu, the following may be of additional interest"), not a Parāśari
śloka — recorded as translator-commentary, **not** used as [D] registry content. Node
relationship modifiers stay `unqualified` pending a text-located rule.

Registry factor: `maitri_compound` ∈ {extreme_friend, friend, neutral, enemy, extreme_enemy},
direction and channel per §2's agent-nature rule; `uncalibrated_default`.

## 4. Verbatim evidence (quoted chunks)

### 4.1 Saptavargaja-bala dignity scale — `bphs` PG264:C1 (ch.27 śl.2–4)

"2-4. SAPTAVARGAJA BALA.. If a planet is in its Moolatrikona Rasi, it gets 45 Virupas, in own
Rasi 30 Virupas, [e]xtreme friend's Rasi 20 Virupas, friend's Rasi 15 Virupas, neutral's Rasi
10 Virupas, enemy's Rasi 4 Vi[r]upas and in extreme enemy's Rasi 2 Virupas." (OCR: "cxtreme" →
extreme; "l0" → 10.)

### 4.2 Exaltation/mūlatrikoṇa — `bphs` PG37:C1–PG38:C2 (ch.3 śl.49–54)

"49-50. EXALTATION AND DEBILITATION : For the seven planets from the Sun on, the signs of
exaltation are res[pective]ly Aries, Taurus, Capricorn, Virgo, Cancer, Pisces and Libra" +
"The deepest exaltation degrees are respectively 10, 3, 2[8], 15, 5, 27 [a]nd 20 in those
signs. And in the seventh sign from the [same] exaltation sign each planet has its own
debilitation. The same degrees of deep exaltation apply to deep fall." Mūlatrikoṇa (śl.51–54,
PG38:C1–C2): Sun — Leo first 20°; Mars — Aries first 12° ("the first 12 dcgrees in Aries as
Moolatrikona"); Mercury — Virgo: first 15° exaltation zone, next 5° mūlatrikoṇa, last 10° own;
Jupiter — Sagittarius first third; Venus — Libra first half; Saturn — Aquarius "same … as the
Sun has in Leo" (first 20°). **Moon's mūlatrikoṇa degree-span is OCR-degraded in this chunk**;
the sign (Taurus) is unambiguous — degree span flagged [U] pending a clean chunk read
(predicate: `text_id='bphs' and content ilike '%Taurus%' and ilike '%Moolatrikona%'`, §5).

### 4.3 (reserved)

### 4.4 Marriage condition — `phaladeepika` PG145:C1 (Adh. X śl.15)

"Sloka 15.—If the lord of the 7th house occupies an inimical or depression sign, or be eclipsed
or be aspected by malefics and if the 7th house be associated with or aspected by malefics,
there will be loss of wife; so say the wise." (Chunk header reads "the 10th Adhyaya on the
Kalatra-Bhava or the 7th house"; the edition's Kalatra chapter — locator stands as printed.)

### 4.5 Natural benefic/malefic — `bphs` PG26:C1 (ch.3 śl.11)

"11. BENEFICS A[N]D MALEFICS.' Among these, the Sun, Saturn, M[a]rs, decreasing Moo[n], Rahu
and Ketu (the ascending and the descending nodes of the Moon) are malefics while the rest are
benefics. Mercury, however, is a malefic if he joins a malefic."

### 4.6 Naisargika maitrī rule — `bphs` PG39:C1 (ch.3 śl.55)

"55. NATURAL RELATION[S]HIPS.' Note the signs which are the 4th, 2nd, 12th, 5th, 9th and the
8th from the Moolatri[k]ona of a planet. The planets ruling such signs are it[s] friends apart
from the lord of its exaltation sign. Lords other than these a[r]e its enemies. If a planet
becomes its friend as well as its enemy (on account of the said two computations) then it is
neutral or equal."

### 4.7 Printed maitrī table — `bphs` PG39:C2 (OCR-degraded)

"Friends / Enemies / Equals — Sun: Moon, Mars, Jupiter / Venus, Sat[urn] / —; Moon: Sun,
Mercury / –; Mercury: [friend] Sun … / Moon; Mars … Venus, Saturn [neutral]; Jupiter: Sun,
Moon, Mars … / Venus, Mercury; Saturn: Mercury, Venus …" — columns interleaved by OCR; used
only as a cross-check on the śl.55-derived table (§3.1), never as the primary source.

### 4.8 Kāraka verses — `phaladeepika` Adh. II śl.1–7 (PG47:C1, PG48:C1, PG49:C1)

- śl.1 (Sun): "…father, anything auspicious, one's own self, happiness, prowess, courage,
  power, victory in war, service under the sovereign, glory…" (PG47:C1)
- śl.2 (Moon): "…the welfare of the mother, mental tranquillity…" (PG47:C1)
- śl.3 (Mars): "…strength, products derived from the Earth, the qualities of his brothers,
  cruelty, battle…" (PG47:C1)
- śl.4 (Mercury): "…one's learning, eloquence, skill in the fine arts…, maternal uncle…,
  intelligence…" (PG48:C1)
- śl.5 (Jupiter): "…one's knowledge, good qualities, sons, minister…, prosperity in
  everything…, wisdom (learning)…, happiness of the husband, honour and compassion." (PG48:C1)
- śl.6 (Venus): "…wife, happiness…, marriage and festivity should be sought for through Venus."
  (PG49:C1)
- śl.7 (Saturn): "As regards one's longevity, death, fear, degradation, misery, humiliation,
  sickness, poverty…, debts…, jail and captivity, one ought to guess through Saturn." (PG49:C1)

### 4.9 Marriage yoga→event relations — `phaladeepika` Adh. X śl.12–14 (PG144:C1, PG145:C1)

- śl.12: "…The marriage may be expected to come off when Venus or the lord of the 7th house in
  his orbit passes through a sign which is triangular to the Rasi or Navamsa occupied by the
  Lord of the Lagna."
- śl.13: "The acquisition of a wife may happen during the Dasa period of the planet (1) posited
  in the 7th house, (2) aspecting the 7th house or (3) owning the 7th house. The same may also
  happen, when the lord of the Lagna in his orbit comes to the Rasi representing the 7th
  house."
- śl.14: "…During the Dasa-period of [the stronger of {the lords of the Rasi and Navamsa
  occupied by the lord of the 7th house} and {Venus and the Moon}] when Jupiter passes through
  a sign triangular to the Rasi or Navamsa occupied by the lord of the 7th, the marriage may be
  declared to take place."

### 4.10 Wealth/status yogas — `bphs` ch.37 śl.5–10 (PG384:C1)

- śl.5 Adhi yoga: "If benefics occupy the 8th, 6th and [7]th counted from the Moon, Adhi yoga
  obtains. According to the strength of the participating planets, the native concerned will be
  either a king or a minister or an army chief." — **OCR flag:** the printed order "8th, 6th
  and ?th" is an OCR column jumble of the conventional 6th/7th/8th-from-Moon; recorded
  [D-with-OCR-degradation] at the house list; the event relation (status by participant
  strength) is clean.
- śl.6 Dhana yoga: "Should all the (three) benefics be in Upachaya (i.e. 3rd, 6th, 10th and
  11th) counted from the Moon, one will be very affluent; with two benefics so placed he will
  have medium effects in regard to wealth. If a single benefic is there, the wealth will be
  negligible."
- śl.7–10 Sunapha/Anapha/Duradhara: planet other than the Sun in the 2nd / 12th / both from the
  Moon ⇒ "king or equal to a king… self earned wealth" / "king, free from diseases, virtuous,
  famous…" / "pleasures, charitable… wealth, conveyances".

### 4.11 Ṣaḍbala sufficiency thresholds — `phaladeepika` Adh. IV śl.22–24 (PG79:C1, PG80:C1)

- śl.22–23 (PG79:C1): "The Sun is declared strong when his strength is 6½ Rupas. In the case of
  the Moon, it is 6 Rupas, Five Rupas are assigned to Mars and 7 to Mercury, Jupiter's …
  Purnabala is similar to that of the Sun, that is, 6½ Rupas. Venus is strong when he gets 5½
  Rupas. … Saturn should have 5 Rupas. These are the figures representing the total Shadbala
  for the[se planets]."
- śl.24 (PG80:C1): "In the case of the Lagna and other Bhavas, add one Rupa to the strength of
  the lord of the Bhava concerned. Supplement this by the Directional strength (Digbala) due to
  that Bhava and also by the strength of aspect (Drigbala) of that Bhava. The aggregate
  sum-total is the Bhavabala required."

## 5. Kāraka sets per class (registry content for B5.1)

Per spec §2.1: a class's kāraka set is registry content, each row carrying its citation;
**no cited kāraka ⇒ empty set (`computed_empty`)**. From §4.8:

| protocol class | kāraka | citation |
|---|---|---|
| marriage, romantic_start | Venus (wife/marriage) | [D] PG49:C1 śl.6 |
| bereavement (father) / parental_event (father) | Sun (father) | [D] PG47:C1 śl.1 |
| parental_event (mother) | Moon (mother) | [D] PG47:C1 śl.2 |
| childbirth | Jupiter (sons) | [D] PG48:C1 śl.5 |
| sibling-class rows (none in the 27) | Mars (brothers) — recorded, unused | [D] PG47:C1 śl.3 |
| education_milestone, exam_outcome | Jupiter (knowledge/learning), Mercury (learning/intelligence) | [D] PG48:C1 śl.4–5 |
| health classes (illness_acute, chronic_onset, surgery) | Saturn (sickness) | [D] PG49:C1 śl.7 |
| career_* , achievement_recognition | Sun (service under the sovereign, glory) | [D] PG47:C1 śl.1 |
| major_gain / major_loss | Venus (wealth, śl.6 tail "one's wealth…" per PG48:C1 śl.6 head) | [D] PG48:C1/PG49:C1 śl.6 |
| all other classes | `computed_empty` | — (absence predicate below) |

Absence claim (F-32): no other kāraka assignments are claimed for the remaining classes because
none were read. Predicate: `select count(*) from classical_text_chunks where
text_id='phaladeepika' and verse_ref in ('PG47:C1','PG48:C1','PG49:C1')` → 3 chunks read in
full above; no claim is made beyond them.

## 6. Yoga→event map (registry content; `yoga_constituent` role, spec §2.1)

| yoga_id | definition (from the verse) | event classes | citation | provenance |
|---|---|---|---|---|
| Y-MARRIAGE-T1 | Venus or 7L transits a sign triangular to lagna-lord's rāśi/navāṃśa | marriage | [D] PG144:C1 śl.12 | verse_cited |
| Y-MARRIAGE-D1 | daśā of the occupant / aspector / owner of the 7th | marriage | [D] PG144:C1 śl.13 | verse_cited |
| Y-MARRIAGE-DT1 | stronger of {7L's rāśi/navāṃśa lords} vs {Venus, Moon} daśā + Jupiter transiting triangular to 7L's rāśi/navāṃśa | marriage | [D] PG145:C1 śl.14 | verse_cited |
| Y-MARRIAGE-COND | 7L inimical/debilitated/eclipsed/malefic-aspected AND 7th afflicted | separation (condition side of the marriage promise) | [D] PG145:C1 śl.15 | verse_cited |
| Y-ADHI | benefics in 6/7/8 from Moon; result scales with participant strength | achievement_recognition, career_advancement | [D-with-OCR-degradation] PG384:C1 śl.5 (house order OCR-jumbled) | verse_cited |
| Y-DHANA | 3/2/1 benefics in upachaya from Moon ⇒ very/medium/negligible affluence | major_gain | [D] PG384:C1 śl.6 | verse_cited |
| Y-SUNAPHA / Y-ANAPHA / Y-DURADHARA | planet (≠ Sun) 2nd / 12th / both from Moon | major_gain, achievement_recognition | [D] PG384:C1 śl.7–10 | verse_cited |

The O-RR-5 fixture yoga ("7L Venus conjunct exalted Jupiter in the 9th") is a **synthetic
oracle fixture**, not a corpus entry — it is not in this map and enters no registry row.

Explicitly **not** read (future versions, predicates stated): Phaladīpikā Adh. VI–VII (yogas,
mahārāja yogas, pp.46/72); BPHS mahāpuruṣa and rāja-yoga chapters (count: `select count(*)
from classical_text_chunks where text_id='bphs' and cleaned_translation_text ilike '%raja
yoga%'` → 19 chunks, unread); putra-bhāva yogas for childbirth. Adh. V śl.1–8 (profession by
navāṃśa of the 10th lord, PG80:C1–PG82:C1) **was** read in v1.1: it types *vocation*, not
event timing, so it supplies no yoga→event row. Nothing unread enters a score until read and
cited.

## 7. Standing notes

- Every factor row: `calibration_status = uncalibrated_default` (spec §2.1; D-RQ1); L5
  calibration replaces under a new `rule_version`.
- All nature/maitrī modifiers are **interpretive**: they assign channel/valence and rank;
  they never admit, exclude, or zero (spec §2.3 inv 3, §3).
- Node maitrī (translator's note, PG40:C1) is not registry content (§3.3).
- Moon mūlatrikoṇa degree span [U] — flagged, not used; the sign-level maitrī derivation does
  not depend on it.
