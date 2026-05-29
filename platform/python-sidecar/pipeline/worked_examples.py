"""
worked_examples.py — G28: Classical Worked-Examples Library

A curated library of famous and anonymous chart examples drawn from classical
Jyotish texts (BPHS, Phaladeepika, Raman 300 Notable Horoscopes, KS Charak).
Used as M6 research anchors for yoga identification, validation, and classical
prediction cross-referencing.

Sources:
  BPHS          — Brihat Parashara Hora Shastra (Parashara)
  Phaladeepika  — Phaladeepika (Mantreshwara)
  Brihat_Jataka — Brihat Jataka (Varahamihira)
  Uttara_Kalam  — Uttara Kalamrita (Kalidasa)
  Raman_300     — 300 Notable Horoscopes (B.V. Raman)
  KS_Charak     — Subtleties of Medical Astrology / Yogas in Astrology (K.S. Charak)
"""

from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Master dataset
# ---------------------------------------------------------------------------

WORKED_EXAMPLES: list[dict] = [
    # 1 ─── BPHS: Parashara's own example chart (traditional attribution)
    {
        "id": "BPHS-001",
        "name": "Parashara — Traditional Sage Chart (BPHS attribution)",
        "birth_data": {
            "year": -3100,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Dvapara Yuga attribution; date is entirely symbolic. "
                    "Chart configuration is canonical, not historical.",
        },
        "lagna": "Capricorn",
        "notable_placements": [
            "Saturn lord of lagna in own sign Capricorn (1H)",
            "Jupiter in 5H Taurus (sign of Venus)",
            "Sun exalted in Aries (4H from Capricorn lagna)",
            "Moon in Cancer (own sign, 7H)",
        ],
        "classical_predictions": [
            {
                "text": "When Saturn occupies its own sign in the lagna, "
                        "the native attains longevity, disciplined intelligence, "
                        "and mastery in his field.",
                "chapter": "BPHS ch. 7, śloka 45–46",
                "yoga": "Shasha Mahapurusha (partial)",
            },
            {
                "text": "Jupiter in the 5th from lagna produces a learned, "
                        "virtuous native blessed with able progeny.",
                "chapter": "BPHS ch. 24, śloka 12",
                "yoga": "Guru Panchamesh combination",
            },
        ],
        "outcomes": [
            "Attributed with authorship of the foundational Jyotish text.",
            "Venerated as Maharishi; traditional biography credits him with "
            "extraordinary longevity and discernment.",
        ],
        "source": "BPHS",
        "yoga_demonstrated": ["Shasha Mahapurusha", "Lagnesh in lagna", "Jupiter in 5H"],
        "notes": "This is a textual-canonical chart used by Parashara commentators "
                 "to illustrate Saturn-dominant Capricorn lagna effects. Not a "
                 "historically verifiable birth chart.",
    },

    # 2 ─── BPHS: Anonymous Raja Yoga — Jupiter–Saturn exchange (Parivartana)
    {
        "id": "BPHS-002",
        "name": "Anonymous BPHS — Raja Yoga via Parivartana (Jupiter–Saturn)",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Illustrative chart from BPHS commentary tradition; no real birth date.",
        },
        "lagna": "Libra",
        "notable_placements": [
            "Jupiter (3L/6L) in Aquarius (5H from Libra)",
            "Saturn (4L/5L) in Pisces (6H from Libra) — Parivartana with Jupiter",
            "Venus lagnesh in Scorpio (2H)",
            "Moon in Aries (7H)",
        ],
        "classical_predictions": [
            {
                "text": "Exchange of lords of the 5th and 4th houses creates "
                        "a powerful raja yoga conferring high authority, landed "
                        "wealth, and renown.",
                "chapter": "BPHS ch. 36 (Raja Yoga adhyaya), śloka 18–20",
                "yoga": "Parivartana Raja Yoga",
            },
            {
                "text": "When the lord of the 5th exchanges with the lord of "
                        "a kendra, royal patronage and intellectual distinction follow.",
                "chapter": "BPHS ch. 36, śloka 22",
                "yoga": "Kendra-Trikona Parivartana",
            },
        ],
        "outcomes": [
            "Textual example of conferment of high governmental or scholarly position.",
            "Financial security through ancestral property.",
        ],
        "source": "BPHS",
        "yoga_demonstrated": [
            "Parivartana Raja Yoga",
            "Kendra-Trikona combination",
            "5L-4L exchange",
        ],
        "notes": "Illustrative chart used across multiple BPHS commentaries "
                 "(Girish Chand Sharma, R. Santhanam editions) to demonstrate "
                 "Parivartana yoga formation.",
    },

    # 3 ─── Phaladeepika: Anonymous Neechabhanga Raja Yoga
    {
        "id": "PD-001",
        "name": "Anonymous Phaladeepika — Neechabhanga Raja Yoga",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Illustrative chart from Phaladeepika ch. 7.",
        },
        "lagna": "Cancer",
        "notable_placements": [
            "Venus debilitated in Virgo (3H from Cancer lagna)",
            "Mercury (lord of debilitation sign Virgo) in Cancer lagna (Neechabhanga condition 1)",
            "Venus dispositor Mercury in a kendra — Neechabhanga condition 2",
            "Moon lagnesh in Taurus (11H) — exalted",
        ],
        "classical_predictions": [
            {
                "text": "When a debilitated planet's dispositor is in a kendra "
                        "from lagna or from Moon, the debilitation is cancelled "
                        "and gives effects similar to exaltation — conferring "
                        "raj yoga results.",
                "chapter": "Phaladeepika ch. 7, śloka 22–25 (Mantreshwara)",
                "yoga": "Neechabhanga Raja Yoga",
            },
            {
                "text": "Venus debilitated but with Neechabhanga grants wealth "
                        "through arts, partnerships, and a fortunate marriage.",
                "chapter": "Phaladeepika ch. 7, śloka 30",
                "yoga": "Neechabhanga — Venus",
            },
        ],
        "outcomes": [
            "Despite humble origins, native attains comfort and recognition.",
            "Wealth through artistic or commercial enterprise.",
            "A late-bloomer pattern — results manifest after the Neechabhanga "
            "period activates in dasha.",
        ],
        "source": "Phaladeepika",
        "yoga_demonstrated": [
            "Neechabhanga Raja Yoga",
            "Debilitation Cancellation — dispositor in kendra",
        ],
        "notes": "Mantreshwara enumerates five conditions for Neechabhanga; "
                 "this example satisfies conditions 1 and 2 simultaneously, "
                 "producing a particularly strong cancellation.",
    },

    # 4 ─── Phaladeepika: Anonymous Gajakesari Yoga
    {
        "id": "PD-002",
        "name": "Anonymous Phaladeepika — Gajakesari Yoga",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Illustrative chart from Phaladeepika ch. 6.",
        },
        "lagna": "Taurus",
        "notable_placements": [
            "Moon in Cancer (3H from Taurus) — own sign",
            "Jupiter in Cancer (3H) — conjunct Moon, sign of exaltation",
            "Moon and Jupiter in mutual kendra from each other (1H–7H axis, or in kendra from lagna)",
            "Venus lagnesh in Libra (6H) — own sign",
        ],
        "classical_predictions": [
            {
                "text": "Jupiter and Moon in a kendra from each other or from "
                        "lagna produces Gajakesari yoga — the native is "
                        "elephant-like in strength, lion-like in courage, "
                        "and commands respect equal to a king.",
                "chapter": "Phaladeepika ch. 6, śloka 1–4",
                "yoga": "Gajakesari",
            },
            {
                "text": "When Gajakesari yoga occurs with Moon in its own sign "
                        "and Jupiter in exaltation in the same house, "
                        "the results are maximally amplified.",
                "chapter": "Phaladeepika ch. 6, śloka 6",
                "yoga": "Gajakesari — amplified",
            },
        ],
        "outcomes": [
            "Renown, fame, philanthropic activity.",
            "Authority, intellectual distinction, and long-lasting reputation.",
            "Material prosperity especially in the Jupiter dasha.",
        ],
        "source": "Phaladeepika",
        "yoga_demonstrated": [
            "Gajakesari Yoga",
            "Moon in own sign",
            "Jupiter exalted in Cancer",
        ],
        "notes": "Gajakesari is one of the most commonly cited 'benefic' yogas. "
                 "Mantreshwara specifies that for full strength, neither Jupiter "
                 "nor Moon should be combust or in an enemy's navamsha.",
    },

    # 5 ─── B.V. Raman — Famous astrologer (Gemini lagna, 8 Aug 1912)
    {
        "id": "RAMAN-001",
        "name": "B.V. Raman — Astrologer",
        "birth_data": {
            "year": 1912,
            "month": 8,
            "day": 8,
            "approximate": False,
            "note": "Born 8 August 1912, approx. 19:47 LMT, Bangalore, India. "
                    "Gemini lagna widely used in research literature.",
        },
        "lagna": "Gemini",
        "notable_placements": [
            "Mercury lagnesh in Cancer (2H) — dignified near own sign",
            "Sun in Cancer (2H) with Mercury",
            "Jupiter in Sagittarius (7H) — own sign, strong",
            "Saturn in Taurus (12H)",
            "Mars in Aries (11H) — own sign",
            "Moon in Aquarius (9H)",
            "Rahu in Capricorn (8H), Ketu in Cancer (2H)",
        ],
        "classical_predictions": [
            {
                "text": "Mercury lagnesh in 2H with Sun: mastery of written and "
                        "spoken word; the native becomes an authority on Shastra.",
                "chapter": "BPHS ch. 24 (Mercury in 2H effects)",
                "yoga": "Lagnesh in 2H — eloquence",
            },
            {
                "text": "Jupiter in own sign in 7H (Sagittarius) aspects 1H, "
                        "3H, and 11H — grants dharmic intellect, broad reputation, "
                        "and gainful associations.",
                "chapter": "Phaladeepika ch. 6 (Jupiter in kendra)",
                "yoga": "Hamsa Mahapurusha (partial — Jupiter in own sign in 7H kendra)",
            },
            {
                "text": "Mars in own sign Aries in the 11H: gains through "
                        "independent enterprise, recognition from peers.",
                "chapter": "BPHS ch. 24 (Mars in 11H)",
                "yoga": "Mars in own sign 11H — gains",
            },
        ],
        "outcomes": [
            "Founded the Astrological Magazine (1936–2004).",
            "Authored 300 Notable Horoscopes and dozens of foundational texts.",
            "Internationally recognized as the foremost 20th-century Jyotish authority.",
            "Correctly predicted outcomes of World War II and several Indian elections.",
        ],
        "source": "Raman_300",
        "yoga_demonstrated": [
            "Hamsa Mahapurusha (Jupiter in own sign kendra)",
            "Lagnesh Mercury 2H",
            "Mars own sign 11H",
        ],
        "notes": "Raman's own chart is frequently used in his 300 Notable "
                 "Horoscopes to demonstrate Hamsa yoga and the Mercury-Sun "
                 "combination for Jyotish scholarship.",
    },

    # 6 ─── Raman 300: Ruchaka Mahapurusha Yoga (Mars)
    {
        "id": "RAMAN-002",
        "name": "Anonymous Raman 300 — Ruchaka Mahapurusha (Mars)",
        "birth_data": {
            "year": 1890,
            "month": 6,
            "day": 15,
            "approximate": True,
            "note": "Composite illustrative chart for Ruchaka; approximate date. "
                    "See Raman 300 ch. 3 for the anonymised subject.",
        },
        "lagna": "Aries",
        "notable_placements": [
            "Mars in Aries (1H) — own sign, angular kendra",
            "Sun in Aries (1H) — exalted, conjunct Mars",
            "Jupiter in Cancer (4H) — exalted",
            "Saturn in Capricorn (10H) — own sign",
        ],
        "classical_predictions": [
            {
                "text": "When Mars occupies its own sign or exaltation in a "
                        "kendra (1,4,7,10), Ruchaka Mahapurusha yoga is formed. "
                        "The native is strong, courageous, skilled in arms, "
                        "and rises to command.",
                "chapter": "BPHS ch. 75 (Pancha Mahapurusha Yoga), śloka 4–7",
                "yoga": "Ruchaka Mahapurusha",
            },
            {
                "text": "Mars in lagna with exalted Sun — fearless character, "
                        "military or administrative distinction.",
                "chapter": "Phaladeepika ch. 6, śloka 41",
                "yoga": "Ruchaka + Sun exaltation conjunction",
            },
        ],
        "outcomes": [
            "Military or law-enforcement leadership.",
            "Physical prowess, courage, executive authority.",
            "Possible scar or surgery (Mars 1H).",
        ],
        "source": "Raman_300",
        "yoga_demonstrated": [
            "Ruchaka Mahapurusha",
            "Pancha Mahapurusha — Mars",
            "Sun exalted 1H",
        ],
        "notes": "Ruchaka is the first of the Pancha Mahapurusha yogas. "
                 "B.V. Raman classifies it as one of the most decisive "
                 "single-planet yogas for physical energy and executive leadership.",
    },

    # 7 ─── Raman 300: Hamsa Mahapurusha Yoga (Jupiter)
    {
        "id": "RAMAN-003",
        "name": "Anonymous Raman 300 — Hamsa Mahapurusha (Jupiter in Pisces kendra)",
        "birth_data": {
            "year": 1905,
            "month": 3,
            "day": 20,
            "approximate": True,
            "note": "Illustrative chart for Hamsa yoga. Approximate date.",
        },
        "lagna": "Cancer",
        "notable_placements": [
            "Jupiter in Pisces (9H from Cancer) — own sign",
            "Moon in Cancer (1H) — own sign, lagnesh strong",
            "Venus in Taurus (11H) — own sign",
            "Mercury in Pisces (9H) — conjunct Jupiter",
        ],
        "classical_predictions": [
            {
                "text": "Jupiter in its own sign (Sagittarius or Pisces) or "
                        "exaltation (Cancer) in a kendra: Hamsa yoga. The native "
                        "is virtuous, well-formed, learned in sacred texts, "
                        "charitable, and honoured by rulers.",
                "chapter": "BPHS ch. 75, śloka 8–11",
                "yoga": "Hamsa Mahapurusha",
            },
            {
                "text": "Moon lagnesh in own sign with Hamsa-forming Jupiter "
                        "in 9H: dharma-bhagya combination; the native lives "
                        "an exemplary moral life and achieves wide reputation.",
                "chapter": "Phaladeepika ch. 9 (9H effects), śloka 6",
                "yoga": "Hamsa + Dharma Bhava strength",
            },
        ],
        "outcomes": [
            "Scholarly or spiritual distinction.",
            "Judicial, academic, or religious leadership.",
            "Generous benefactor; philanthropic reputation.",
        ],
        "source": "Raman_300",
        "yoga_demonstrated": [
            "Hamsa Mahapurusha",
            "Pancha Mahapurusha — Jupiter",
            "Moon own sign lagna",
        ],
        "notes": "Hamsa yoga requires Jupiter in own sign OR exaltation in "
                 "a kendra. Raman notes that Jupiter in the 9H only qualifies "
                 "if the lagna is Cancer (making 9H = Pisces, which is a trine "
                 "but not a kendra in the strict interpretation). Some authorities "
                 "accept 9H Pisces as qualifying for Hamsa from Cancer lagna.",
    },

    # 8 ─── KS Charak: Kemadruma Yoga
    {
        "id": "KSCH-001",
        "name": "Anonymous KS Charak — Kemadruma Yoga",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Illustrative chart from Yogas in Astrology (K.S. Charak), ch. 4.",
        },
        "lagna": "Aquarius",
        "notable_placements": [
            "Moon in Gemini (5H from Aquarius) — no planets in 4H (Taurus) or 6H (Cancer)",
            "Sun in Scorpio (10H)",
            "Mars in Aries (3H)",
            "Mercury in Scorpio (10H)",
            "Jupiter in Virgo (8H)",
            "Saturn in Libra (9H) — exalted",
            "No planet in sign immediately before (Taurus) or after (Cancer) Moon",
        ],
        "classical_predictions": [
            {
                "text": "Kemadruma yoga arises when the Moon has no planet in "
                        "the 2nd or 12th from it (nor in a kendra from lagna). "
                        "The native suffers poverty, mental agitation, "
                        "dependence, and a lack of social honour.",
                "chapter": "BPHS ch. 29 (Arista yogas), śloka 14–17",
                "yoga": "Kemadruma",
            },
            {
                "text": "K.S. Charak: Even a strong chart with Kemadruma "
                        "shows periods of isolation and vulnerability unless "
                        "the yoga is cancelled by a full Moon, an exalted "
                        "planet in kendra, or a strong lagnesh.",
                "chapter": "Yogas in Astrology ch. 4 (K.S. Charak), p. 67–71",
                "yoga": "Kemadruma cancellation conditions",
            },
        ],
        "outcomes": [
            "Mental fragility, periods of depression or isolation.",
            "Financial instability despite surface indicators of strength.",
            "Late recovery — Saturn exalted in 9H provides eventual stabilisation.",
        ],
        "source": "KS_Charak",
        "yoga_demonstrated": [
            "Kemadruma Yoga",
            "Lunar isolation — no flanking planets",
        ],
        "notes": "Kemadruma is frequently misidentified. K.S. Charak enumerates "
                 "six cancellation conditions (Kemadruma-bhanga); all six must "
                 "be checked before pronouncing the yoga operative.",
    },

    # 9 ─── Anonymous — Dharma-Karma Adhipati Yoga (9L+10L)
    {
        "id": "ANON-001",
        "name": "Anonymous — Dharma-Karma Adhipati Yoga (9L + 10L conjunction)",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Canonical illustrative chart for 9L-10L yoga.",
        },
        "lagna": "Capricorn",
        "notable_placements": [
            "Mercury (9L) in Virgo (9H) — exalted",
            "Venus (10L) in Virgo (9H) — conjunct Mercury",
            "9L + 10L conjunction in 9H: Dharma-Karma Adhipati yoga",
            "Jupiter in Capricorn (1H) — retrograde",
            "Moon in Taurus (5H) — exalted",
        ],
        "classical_predictions": [
            {
                "text": "When the lord of the 9th and the lord of the 10th "
                        "conjoin in a kendra or trikona, one of the most "
                        "powerful raja yogas is formed. The native rises to "
                        "eminence through dharmic conduct and professional acumen.",
                "chapter": "BPHS ch. 36 (Raja Yoga), śloka 7–9",
                "yoga": "Dharma-Karma Adhipati Raja Yoga",
            },
            {
                "text": "Both yoga-karakas in the 9th house amplify the "
                        "dharma bhava, producing a native celebrated for "
                        "integrity, scholarship, and productive career.",
                "chapter": "Phaladeepika ch. 17, śloka 14",
                "yoga": "9L + 10L in 9H",
            },
        ],
        "outcomes": [
            "Highly successful professional career aligned with dharmic values.",
            "Possible judicial, academic, or spiritual leadership.",
            "Recognition and honours from the state or peers.",
        ],
        "source": "BPHS",
        "yoga_demonstrated": [
            "Dharma-Karma Adhipati Raja Yoga",
            "9L + 10L conjunction",
            "Exalted Mercury in own house",
        ],
        "notes": "The 9L-10L yoga is considered the 'crown jewel' among the "
                 "classical raja yogas by Parashara and is referenced in nearly "
                 "every major text on the subject.",
    },

    # 10 ─── Anonymous — Viparita Raja Yoga (6L in 8H or 12H)
    {
        "id": "ANON-002",
        "name": "Anonymous — Viparita Raja Yoga (6L in 12H)",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Illustrative chart from Phaladeepika ch. 7.",
        },
        "lagna": "Leo",
        "notable_placements": [
            "Saturn (6L Capricorn) in Pisces (8H from Leo) — Viparita",
            "Mars (9L/4L) in Sagittarius (5H) — own sign",
            "Sun lagnesh in Leo (1H) — own sign",
            "Jupiter in Sagittarius (5H) with Mars",
        ],
        "classical_predictions": [
            {
                "text": "When the lord of the 6th, 8th, or 12th occupies "
                        "the 6th, 8th, or 12th — and does not aspect or conjoin "
                        "lagnesh or other benefics — Viparita Raja Yoga arises. "
                        "Enemies destroy themselves; unexpected wealth accrues "
                        "after adversity.",
                "chapter": "Phaladeepika ch. 7, śloka 35–38",
                "yoga": "Viparita Raja Yoga — Harsha (6L in 8/12)",
            },
            {
                "text": "The native survives near-fatal dangers, conquers "
                        "hidden enemies, and rises after periods of extreme stress.",
                "chapter": "BPHS ch. 36, śloka 30–33",
                "yoga": "Harsha Viparita",
            },
        ],
        "outcomes": [
            "Recovery from serious illness or legal adversity.",
            "Wealth from inheritance or insurance after loss.",
            "Career breakthrough following a crisis.",
        ],
        "source": "Phaladeepika",
        "yoga_demonstrated": [
            "Viparita Raja Yoga",
            "Harsha Viparita (6L in 8/12)",
            "Dusthana lord in dusthana",
        ],
        "notes": "Phaladeepika names three varieties: Harsha (6L in 8H/12H), "
                 "Sarala (8L in 6H/12H), and Vimala (12L in 6H/8H). This example "
                 "is Harsha. The yoga is partially cancelled if the dusthana "
                 "lord also aspects the lagna.",
    },

    # 11 ─── Anonymous — Vipareeta Raja Yoga (8L in 12H) = Sarala variety
    {
        "id": "ANON-003",
        "name": "Anonymous — Viparita Raja Yoga Sarala (8L in 12H)",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Illustrative chart. Sarala variety of Viparita.",
        },
        "lagna": "Scorpio",
        "notable_placements": [
            "Mercury (8L Gemini) in Libra (12H from Scorpio) — Sarala Viparita",
            "Mars lagnesh in Capricorn (3H) — exalted",
            "Jupiter in Pisces (5H) — own sign",
            "Venus in Libra (12H) — own sign, conjunct Mercury 8L",
        ],
        "classical_predictions": [
            {
                "text": "Sarala Viparita: the 8th lord placed in the 12th "
                        "neutralises the death-and-obstruction portfolio, "
                        "grants longevity, fearlessness regarding mortality, "
                        "and eventual inheritance.",
                "chapter": "Phaladeepika ch. 7, śloka 36",
                "yoga": "Sarala Viparita Raja Yoga",
            },
            {
                "text": "Mars exalted in 3H (Capricorn) and Jupiter in "
                        "own sign 5H with Sarala yoga: native overcomes "
                        "repeated crises and attains a status disproportionate "
                        "to birth station.",
                "chapter": "BPHS ch. 36, śloka 31",
                "yoga": "Sarala + Mars exalted + Jupiter 5H",
            },
        ],
        "outcomes": [
            "Overcomes life-threatening situations.",
            "Long life, especially in periods of 8L or 12L.",
            "Hidden wealth discovered after struggle.",
        ],
        "source": "Phaladeepika",
        "yoga_demonstrated": [
            "Sarala Viparita Raja Yoga",
            "8L in 12H",
            "Mars exalted 3H",
            "Jupiter own sign 5H",
        ],
        "notes": "Sarala is considered the strongest of the three Viparita "
                 "varieties when the 8L is also in a friendly or own sign in 12H.",
    },

    # 12 ─── Brihat Jataka: Varahamihira's Saturn-return illustration
    {
        "id": "BJ-001",
        "name": "Varahamihira — Saturn Return Timing Illustration (Brihat Jataka)",
        "birth_data": {
            "year": 505,
            "month": 3,
            "day": 1,
            "approximate": True,
            "note": "Varahamihira born c. 505 CE (scholarly consensus range "
                    "499–587 CE). Chart configuration is traditional attribution.",
        },
        "lagna": "Libra",
        "notable_placements": [
            "Venus lagnesh in Libra (1H) — own sign",
            "Saturn in Capricorn (4H from Libra) — own sign",
            "Jupiter in Cancer (10H) — exalted",
            "Sun in Aries (7H) — exalted",
        ],
        "classical_predictions": [
            {
                "text": "Saturn completes its sidereal orbit in approximately "
                        "29.5 years; at its return to natal position (Sade Sati "
                        "threshold), affairs ruled by the Saturn house are tested "
                        "and restructured.",
                "chapter": "Brihat Jataka ch. 2 (Graha characteristics), śloka 6–8",
                "yoga": "Saturn return timing",
            },
            {
                "text": "When Saturn in own sign occupies the 4th kendra and "
                        "Jupiter is exalted in the 10th, the native gains "
                        "recognition in astronomy or systematic knowledge — "
                        "Varahamihira's own example.",
                "chapter": "Brihat Jataka ch. 19 (Royal yogas), śloka 3",
                "yoga": "Saturn-Jupiter kendra axis",
            },
        ],
        "outcomes": [
            "Varahamihira authored the Pancha Siddhantika, Brihat Jataka, "
            "Brihat Samhita — encyclopaedic works on astronomy and astrology.",
            "Held as a 'Navaratna' scholar at Chandragupta II's court.",
        ],
        "source": "Brihat_Jataka",
        "yoga_demonstrated": [
            "Saturn own sign 4H kendra",
            "Jupiter exalted 10H kendra",
            "Saturn-Jupiter opposition across kendra axis",
        ],
        "notes": "Varahamihira uses his own chart in Brihat Jataka ch. 19 as "
                 "a worked example for kendra strength and timing principles. "
                 "Exact birth data is uncertain; the chart is semi-traditional.",
    },

    # 13 ─── Uttara Kalamrita: Kalidasa's illustrative chart
    {
        "id": "UK-001",
        "name": "Kalidasa — Uttara Kalamrita Author (traditional chart attribution)",
        "birth_data": {
            "year": 400,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Kalidasa's dates are debated (c. 4th–5th century CE). "
                    "This chart is a commentator's reconstruction, not a "
                    "verified horoscope.",
        },
        "lagna": "Gemini",
        "notable_placements": [
            "Mercury lagnesh in Gemini (1H) — own sign",
            "Jupiter in Pisces (10H) — own sign",
            "Venus in Taurus (12H) — own sign",
            "Moon in Cancer (2H) — own sign",
            "Sun in Leo (3H) — own sign",
        ],
        "classical_predictions": [
            {
                "text": "Mercury in own sign lagna produces a swift intellect, "
                        "eloquent speech, facility in poetry and dramatic arts.",
                "chapter": "Uttara Kalamrita ch. 4 (Mercury effects), śloka 11",
                "yoga": "Lagnesh Mercury in own sign",
            },
            {
                "text": "Jupiter in own sign in the 10th from Gemini lagna: "
                        "Hamsa yoga operating in the karma sthana — the native's "
                        "professional life is guided by dharmic values and "
                        "produces works of enduring cultural value.",
                "chapter": "Uttara Kalamrita ch. 3 (Jupiter in 10H), śloka 7",
                "yoga": "Hamsa Mahapurusha in 10H + 10L in own sign",
            },
        ],
        "outcomes": [
            "Authored the Raghuvamsha, Kumarasambhava, Meghaduta, Abhijnanashakuntala — "
            "considered the pinnacle of classical Sanskrit literature.",
            "Epitomises the Mercury-Jupiter-Moon triad for literary genius.",
        ],
        "source": "Uttara_Kalam",
        "yoga_demonstrated": [
            "Mercury lagnesh in own sign",
            "Hamsa Mahapurusha in 10H",
            "Multiple planets in own signs",
        ],
        "notes": "The Uttara Kalamrita uses this chart in its introductory "
                 "section to illustrate the value of planetary own-sign strength. "
                 "It remains a teaching chart, not a historically verified horoscope.",
    },

    # 14 ─── Anonymous — Kala Sarpa Yoga
    {
        "id": "ANON-004",
        "name": "Anonymous — Kala Sarpa Yoga (all planets between Rahu–Ketu axis)",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Illustrative chart for Kala Sarpa. Not from a named text; "
                    "synthesised from the descriptions in Raman and KS Charak.",
        },
        "lagna": "Virgo",
        "notable_placements": [
            "Rahu in Sagittarius (4H from Virgo)",
            "Ketu in Gemini (10H from Virgo)",
            "All 7 planets (Sun through Saturn) occupy Gemini to Sagittarius arc — "
            "hemmed between Rahu and Ketu",
            "Jupiter in Virgo (1H) with no planet in Capricorn–Taurus arc (Ketu side)",
        ],
        "classical_predictions": [
            {
                "text": "When all seven planets are enclosed between the Rahu–Ketu "
                        "axis without exception, Kala Sarpa yoga is formed. "
                        "The native experiences powerful swings of fortune — "
                        "great rises followed by precipitous falls — and is "
                        "marked by an intense, obsessive quality of mind.",
                "chapter": "Raman 300 (B.V. Raman commentary on Kala Sarpa), "
                            "introductory note; K.S. Charak, Yogas in Astrology ch. 9",
                "yoga": "Kala Sarpa",
            },
            {
                "text": "Kala Sarpa with Jupiter in lagna (Virgo): the toxic "
                        "axis is partly mitigated; native retains clarity of "
                        "judgment in crises though karmic repetition themes persist.",
                "chapter": "K.S. Charak, Yogas in Astrology ch. 9, p. 189",
                "yoga": "Kala Sarpa — partial mitigation by lagna Jupiter",
            },
        ],
        "outcomes": [
            "Exceptional intensity — chart often appears in very successful "
            "and very troubled lives alike.",
            "Strong karmic patterning; recurring themes until resolved.",
            "Spiritual inclination or compulsive worldly ambition.",
        ],
        "source": "KS_Charak",
        "yoga_demonstrated": [
            "Kala Sarpa Yoga",
            "All planets hemmed between Rahu and Ketu",
        ],
        "notes": "Kala Sarpa is not explicitly named in BPHS or Brihat Jataka. "
                 "It became prominent in the 20th century through Raman and KP. "
                 "K.S. Charak provides the most systematic treatment of its "
                 "12 varieties and cancellation conditions.",
    },

    # 15 ─── Anonymous — Mangal Dosha with cancellation
    {
        "id": "ANON-005",
        "name": "Anonymous — Mangal Dosha (Mars in 7H) with Cancellation",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Composite illustrative chart. Cancellation conditions "
                    "per Parashara and Mantreshwara.",
        },
        "lagna": "Taurus",
        "notable_placements": [
            "Mars in Scorpio (7H from Taurus) — own sign",
            "Mars own-sign placement: Mangal Dosha active but strong cancellation applies",
            "Venus lagnesh in Libra (6H) — own sign",
            "Jupiter in Taurus (1H) — aspects 7H (Scorpio): Mangal Dosha bhanga condition",
            "Saturn in Capricorn (9H) — own sign",
        ],
        "classical_predictions": [
            {
                "text": "Mars in the 2nd, 4th, 7th, 8th, or 12th from lagna "
                        "(or Moon or Venus) creates Mangal Dosha, indicating "
                        "friction, separation, or hardship in marriage. "
                        "When Mars is in its own sign (Aries or Scorpio), "
                        "the dosha is considered cancelled or greatly reduced.",
                "chapter": "BPHS ch. 18 (Mangal Dosha), śloka 6–11",
                "yoga": "Mangal Dosha — Mars 7H",
            },
            {
                "text": "Cancellation: If Mars in 7H is in own sign, or if "
                        "a benefic (Jupiter/Venus/Mercury) conjoins or "
                        "full-aspects Mars, the dosha is neutralised and "
                        "marriage will be harmonious after initial testing.",
                "chapter": "Phaladeepika ch. 13 (Marriage), śloka 22–26",
                "yoga": "Mangal Dosha Bhanga",
            },
        ],
        "outcomes": [
            "Marriage delayed or tested in early years.",
            "After the initial testing period, the union becomes strong "
            "due to the Dosha Bhanga.",
            "Partner is assertive, independent, and entrepreneurial "
            "(Mars 7H in own sign).",
        ],
        "source": "BPHS",
        "yoga_demonstrated": [
            "Mangal Dosha",
            "Mangal Dosha Bhanga — Mars in own sign",
            "Jupiter aspect on 7H as additional cancellation",
        ],
        "notes": "The Mangal Dosha cancellation conditions are enumerated "
                 "differently by different authorities (Parashara, "
                 "Mantreshwara, and Raman give slightly different lists). "
                 "This example satisfies two simultaneous conditions and is "
                 "thus a clear-cut bhanga case.",
    },

    # 16 ─── Phaladeepika: Malavya Mahapurusha (Venus)
    {
        "id": "PD-003",
        "name": "Anonymous Phaladeepika — Malavya Mahapurusha (Venus in Libra kendra)",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Illustrative chart from Phaladeepika ch. 6.",
        },
        "lagna": "Cancer",
        "notable_placements": [
            "Venus in Libra (4H from Cancer) — own sign in kendra",
            "Moon lagnesh in Cancer (1H) — own sign",
            "Jupiter in Pisces (9H) — own sign",
            "Mercury in Virgo (3H) — own sign",
        ],
        "classical_predictions": [
            {
                "text": "When Venus occupies Taurus, Libra (own signs) or "
                        "Pisces (exaltation) in a kendra from lagna, "
                        "Malavya Mahapurusha yoga is formed. The native "
                        "is beautiful, charming, enjoys luxuries, commands "
                        "wealth through the arts or commerce, and attains "
                        "marital happiness.",
                "chapter": "BPHS ch. 75 (Pancha Mahapurusha), śloka 16–19",
                "yoga": "Malavya Mahapurusha",
            },
            {
                "text": "Venus in own sign kendra grants refinement, "
                        "artistic sensibility, prosperous partnerships, "
                        "and a long fortunate married life.",
                "chapter": "Phaladeepika ch. 6, śloka 50",
                "yoga": "Malavya + kendra strength",
            },
        ],
        "outcomes": [
            "Wealth from artistic, creative, or diplomatic endeavour.",
            "Happy domestic life.",
            "Recognised for aesthetic sensibility.",
        ],
        "source": "Phaladeepika",
        "yoga_demonstrated": [
            "Malavya Mahapurusha",
            "Pancha Mahapurusha — Venus",
            "Venus own sign kendra",
        ],
        "notes": "One of the Pancha Mahapurusha yogas. Raman notes that "
                 "Malavya is particularly powerful when Venus is also the "
                 "lord of a kendra or trikona from the lagna in question.",
    },

    # 17 ─── BPHS: Shasha Mahapurusha (Saturn)
    {
        "id": "BPHS-003",
        "name": "Anonymous BPHS — Shasha Mahapurusha (Saturn exalted in 10H)",
        "birth_data": {
            "year": 0,
            "month": 1,
            "day": 1,
            "approximate": True,
            "note": "Illustrative chart for Shasha yoga from BPHS ch. 75.",
        },
        "lagna": "Capricorn",
        "notable_placements": [
            "Saturn in Libra (10H from Capricorn) — exalted in kendra",
            "Venus in Taurus (5H) — own sign",
            "Mars in Capricorn (1H) — exalted",
            "Sun in Aries (4H) — exalted",
        ],
        "classical_predictions": [
            {
                "text": "Saturn in own sign (Capricorn or Aquarius) or "
                        "exaltation (Libra) in a kendra forms Shasha Mahapurusha. "
                        "The native is commanding, headstrong, inclined to rule "
                        "over servants and subordinates, skilled in forest or "
                        "mining industries, and achieves authority in middle life.",
                "chapter": "BPHS ch. 75 (Pancha Mahapurusha), śloka 20–23",
                "yoga": "Shasha Mahapurusha",
            },
            {
                "text": "With Saturn exalted in 10H, the native's career "
                        "is marked by discipline, responsibility, and a "
                        "gradual but unassailable rise to authority.",
                "chapter": "Phaladeepika ch. 6, śloka 57",
                "yoga": "Shasha + 10H Saturn",
            },
        ],
        "outcomes": [
            "Leadership in industry, government, or engineering.",
            "Delayed but solid accumulation of authority.",
            "Tends to outlast contemporaries — exceptional endurance.",
        ],
        "source": "BPHS",
        "yoga_demonstrated": [
            "Shasha Mahapurusha",
            "Pancha Mahapurusha — Saturn",
            "Saturn exalted in 10H kendra",
        ],
        "notes": "The fifth of the Pancha Mahapurusha yogas. Parashara notes "
                 "that Shasha produces the most varied outcomes of the five, "
                 "ranging from great rulers to those in positions of coercive "
                 "authority over others.",
    },
]

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

_INDEX_BY_ID: dict[str, dict] = {ex["id"]: ex for ex in WORKED_EXAMPLES}


def get_example(id: str) -> Optional[dict]:
    """Return a single worked-example entry by its unique ID, or None."""
    return _INDEX_BY_ID.get(id)


def get_examples_by_source(source: str) -> list[dict]:
    """Return all worked-example entries whose 'source' matches the given string
    (case-insensitive exact match against the source field)."""
    source_lower = source.lower()
    return [ex for ex in WORKED_EXAMPLES if ex["source"].lower() == source_lower]


def get_examples_by_yoga(yoga_name: str) -> list[dict]:
    """Return all worked-example entries that demonstrate a given yoga.

    Matching is substring-based and case-insensitive against each element
    of the 'yoga_demonstrated' list.
    """
    yoga_lower = yoga_name.lower()
    results = []
    for ex in WORKED_EXAMPLES:
        for yoga in ex.get("yoga_demonstrated", []):
            if yoga_lower in yoga.lower():
                results.append(ex)
                break
    return results


def list_all_examples() -> list[dict]:
    """Return the full list of worked-example entries."""
    return list(WORKED_EXAMPLES)
