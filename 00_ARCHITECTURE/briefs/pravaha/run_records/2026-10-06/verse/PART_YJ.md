# PART_YJ: Yavana Jataka (text_id `yavana_jataka`, Pingree) citation check

Method: served corpus only, read-only. Quoted text below is the served `content` verbatim.

IMPORTANT retrieval note: for this text the `chapter` argument of `read_chapter` is the PDF PAGE number, not Pingree's adhyaya. `read_chapter(yavana_jataka, 44..51)` returns only Introduction pages 44-51 (manuscript lists, no transit verses). The transit verses sit on pages 645-659 and carry inline "CHAPTER n" headings. I read pages 645, 646, 648, 650, 651, 652, 655, 657, 659 and 710 with `read_chapter` (page = `chapter`), plus search hits that return explicit `citation_ref` values. Chunk labels C1, C2 are the order of chunks within a page as served; this order is consistent with the explicit refs I saw (PG647:C3, PG653:C1, PG654:C2, PG658:C1/C3, PG708:C1).

## Verdict table

Frame note: v.1-3 = planet in its own place; v.4-24 = transit through the 12 places counted from each planet's natal place (Sun, Saturn, Jupiter, Mars, Mercury, Moon etc.; v.19-24 in the Jupiter chapter are "from the Moon"); v.25-30 = the 12 houses counted "from the ascendent". Every claim except 46.24 cites a v.25-30 (ascendent-frame) verse.

| # | Claim (memo) | Locator as served | Verdict | Served text / locus |
|---|---|---|---|---|
| 1 | YJ 45.29 Saturn 10th "honor... position" | PG648:C2, ch.45 v.29 | CONFIRMED | "in the tenth honor, joy in one's actions, position, and prosperity" (9th clause: "long wanderings, diseases, bodily confinement by one's enemies, and hatred") |
| 2 | YJ 46.29 Jupiter 10th "honor from kings" | PG650:C2, ch.46 v.29 | CONFIRMED | "in the tenth authority, the acquisition of wealth and honor from kings, and success in business" |
| 3 | YJ 49.30 Mercury 11th "publicity, praise of wise men" | PG657:C2, ch.49 v.30 | CONFIRMED | "in the eleventh Mercury gives the acquisition of women, friends, happiness, sons, and money, publicity, and the praise of wise men; and in the twelfth from the ascendent it produces strife and infamy" |
| 4 | YJ 46.27 Jupiter 5th "dignity, honor... fame" | PG650:C2, ch.46 v.27 | CONFIRMED | "in the fifth from the ascendent Jupiter gives dignity, honor, sons, fame, and wealth" |
| 5 | YJ 45.25 "honor" (Saturn, 1st) | PG648:C1, ch.45 v.25 | CONFIRMED | "Saturn in the ascendent always causes honor from the rulers of cities, towns, and tribes ..., (the possession of) metals, and the acquisition of wealth". Note it is the 1st house (the memo calls it "1 or 9" in the dispute line) |
| 6 | YJ 47.29 "honor" (Venus, 9th) | PG653:C1, ch.47 v.29 | CONFIRMED | "in the ninth Venus gives reverence, wealth, and honor from the lords (isvara)" |
| 7 | YJ 46.29 Jupiter 10th "success in business" | PG650:C2, ch.46 v.29 | CONFIRMED | same verse as row 2: "...honor from kings, and success in business" |
| 8 | YJ 50.29 Moon 10th "success in business" | PG659:C2, ch.50 v.29 | CONFIRMED | "in the tenth success in business, happiness, the acquisition of wealth, and respect" |
| 9 | YJ 48.30 PG655:C1 Mars 12th "robberies" | PG655:C1, ch.48 v.30 | CONFIRMED | "and in the twelfth place from the ascendent it produces diseases of the feet and eyes, wounds, and robberies" |
| 10 | YJ 47.30 PG653:C1 Venus 12th "loss of one's wealth... delusion" | PG653:C1 (explicit citation_ref), ch.47 v.30 | CONFIRMED | "in the twelfth place from the ascendent it causes the loss of one's wealth, wandering, and mental delusion" |
| 11 | YJ yatra PG710:C2 v.29, 12th "expense, fraud" | PG710:C2 (page 710, 2nd chunk), v.29 of the expedition chapter (after "CHAPTER 76" on PG708) | DIFFERENT | Served: "29. Benefic planets in the twelfth place from the ascendent do not produce evil, expense, fraud, weak points, falls, an impassible road, or wandering; malefics do the opposite of what has just been described." The verse is about BENEFICS in the 12th NOT producing those things; malefics are the ones who "do the opposite" (i.e. would produce them). The memo's "12th = expense, fraud" is therefore only the malefic-case inference, and the context is an expedition (yatra) election rule, not a natal or transit result. Locator PG710:C2 and v.29 are right |
| 12 | YJ 48.28 Mars 8th "thieves... losses" | PG655:C1, ch.48 v.28 | CONFIRMED | "in the eighth Mars gives bilious (diseases), fevers, blood-(sickness), fatigue, thieves, sword-wounds, losses, and distress" |
| 13 | YJ 46.24 PG650:C2 Jupiter 12th from Moon "travel in foreign countries" | PG650:C2, ch.46 v.24 (v.24 begins at the end of PG650:C1) | CONFIRMED | "...and in the twelfth from the Moon it causes travel in foreign countries, weariness, and poverty" (the only Moon-frame verse among the claims) |
| 14 | YJ 46.30 Jupiter 12th "profitless journeys" | PG650:C2, ch.46 v.30 | CONFIRMED | "and in the twelfth it gives profitless journeys and expenses" |
| 15 | YJ 45.29 Saturn 9th "long wanderings" | PG648:C2, ch.45 v.29 | CONFIRMED | "in the ninth Saturn causes long wanderings, diseases, bodily confinement by one's enemies, and hatred" |
| 16 | YJ 50.29 Moon 9th "wandering" | PG659:C2, ch.50 v.29 | CONFIRMED | "in the ninth the Moon causes one's dependence on others, wandering, aversion, greed, delusion, impotence, and dishonor" |
| 17 | YJ 45.28 PG648:C1 Saturn 7th "exile to a foreign land" | PG648:C1, ch.45 v.28 | CONFIRMED | "in the seventh Saturn gives the death of one's wife, weariness, exile to a foreign land, and illness" |
| 18 | YJ 45.26 Saturn 4th "houses" | PG648:C1, ch.45 v.26 | CONFIRMED | "in the fourth place from the ascendent Saturn produces houses, money, friendship with one's relatives, and power" |
| 19 | YJ 46.26 Jupiter 4th "houses" | PG650:C2, ch.46 v.26 | CONFIRMED | "in the fourth success with regard to one's own dharma, strings of pearls, houses, and money" |
| 20 | YJ 47.26 Venus 4th "houses" | PG652:C2, ch.47 v.26 | CONFIRMED | "in the fourth it gives cows, houses, ornaments, women, prosperity, and honor from one's relatives and friends" |
| 21 | YJ 46.30 Jupiter 11th "lands... houses" | PG650:C2, ch.46 v.30 | CONFIRMED | "in the eleventh Jupiter causes the acquisition of cows, lands, grain, clothes, gold, children, knowledge, houses, and food" |
| 22 | YJ 49.28 Mercury 8th "mental distraction" | PG657:C1, ch.49 v.28 | CONFIRMED | "in the eighth it causes diseases, mental distraction, wanderings, and quarrels, and takes away friendship and intelligence" |
| 23 | YJ 50.28 Moon 8th "delusions" | PG659:C2, ch.50 v.28 | CONFIRMED | "in the eighth one's own death, hunger, wandering, imprisonment, fever, sword(-wounds), and delusions" |
| 24 | YJ 46.29 "dharma" (spiritual_turn) | PG650:C2, ch.46 v.29 | CONFIRMED | "in the ninth Jupiter causes the acquisition of position, money, knowledge, sons, and righteousness (dharma), and happiness". The word "dharma" is in the 9th-house clause, not the 10th |
| 25 | YJ 49.29 "dharma" (spiritual_turn) | PG657:C1 to PG657:C2 (verse is split across the chunk break), ch.49 v.29 | CONFIRMED | "in the ninth Mercury gives the appearance of adoration, good health, [chunk break] and strength, and success with regard to righteousness (dharma) and money; in the tenth the acquisition of eloquence, ..." Again the 9th-house clause |

Counts: 25 rows. CONFIRMED 24, NOT FOUND 0, DIFFERENT 1 (row 11).

## Chapter-to-planet map as served

Taken from the inline "In the Yavanajataka: the transits of X. CHAPTER n" headings.

| Adhyaya | Planet | How established |
|---|---|---|
| 44 | Sun | Sun verses (v.25-30 on PG646) end "the transits of the Sun. CHAPTER 45". The heading "CHAPTER 44" itself is on a page I did not read (before PG645), so 44 is inferred from 45 = Saturn |
| 45 | Saturn | "CHAPTER 45 1. Saturn in its own place..." (PG646); closes "the influence of the transits of Saturn. CHAPTER 46" (PG648) |
| 46 | Jupiter | "CHAPTER 46 1. Jupiter in its own place..." (PG648) |
| 47 | Venus | explicit "CHAPTER 47 1. Venus in its own place..." (PG651); closes "the transits of Venus. CHAPTER 48" (PG653) |
| 48 | Mars | "CHAPTER 48 1. Mars in (its own) place..." (PG653); closes "the transits of Mars. CHAPTER 49" (PG655) |
| 49 | Mercury | "CHAPTER 49 1. Mercury in its own place..." (PG655); closes "the transits of Mercury. CHAPTER 50" (PG657) |
| 50 | Moon | "CHAPTER 50 1. The Moon in its own place..." (PG657); v.31-32 on hora and sign follow on PG659 |

Verdict on the memo's map: RIGHT on every planet (Sun 44, Saturn 45, Jupiter 46, Venus 47, Mars 48, Mercury 49, Moon 50). The verse numbers cited (45.25-29, 46.24-30, 47.26-30, 48.28-30, 49.28-30, 50.28-29) all land on the planets the memo says. Whether 49-50 lie outside the frozen spec's range 45-48 is a statement about the spec, which I did not read; arithmetically the served map puts Saturn, Jupiter, Venus, Mars in 45-48 and Sun (44), Mercury (49), Moon (50) outside it, so the memo's statement is consistent with the served text.

## Notes

1. Do not use `read_chapter(chapter=44..51)` to fetch these verses. For this text `chapter` equals page number, so chapters 44-51 return the Introduction manuscript lists (Anup/Mysore/BORI etc., pp. 32-39 of the book). Transit verses need chapter=645..659 (or text search).
2. `find_verses_about` returns chunk text but no `citation_ref`; locators were fixed by `read_chapter` page reads (chunk order) and by `read_classical_text` hits that print the `citation_ref`. Several of the C1/C2 labels (PG648, PG650, PG652, PG655, PG657, PG659) are inferred from served chunk order, not from a printed ref. The two I confirmed by printed ref and by order agree (PG653:C1; PG654:C2, PG647:C3, PG658:C1/C3, PG708:C1).
3. Frame caution for the memo: all claims except row 13 (46.24, Moon frame) rest on v.25-30, the "from the ascendent" frame. The same planet-house pairs in v.4-24 (counted from the natal place of another planet) read differently; for example Jupiter 12th from the Moon (46.24) is "travel in foreign countries" but Jupiter 12th from the ascendent (46.30) is "profitless journeys and expenses". Jupiter 10th from the Moon (46.23) is "eye-diseases, the loss of one's goods ... the death of one's sons", the opposite of 46.29.
4. Row 11 is the only discrepancy: the served v.29 of the expedition chapter is conditional on benefics versus malefics and is phrased negatively for benefics. It should not be cited as "12th: expense, fraud" without the malefic qualifier.
5. OCR damage seen in these pages (none changes a verdict): "Tavanajataka" for Yavanajataka (PG646), "puragramaga:r;iadhipa}:i" (PG648), "know ledge" and "fourt~" (PG650, PG652, PG648), an incomplete clause "in the twelfth pai" for Venus 12th in v.9 (PG651), Mercury v.22 "in the seventh ... in the seventh" (PG657, the first should be sixth; not cited), "~ne's" (PG657), "navarµsa" (PG659). The Sanskrit text is not served for this chunk set (verse_text_sa null); all checks are against the English translation only.
6. 46.29 "success in business" (row 7) and 46.29 "honor from kings" (row 2) are the same verse; 45.29 supplies both the Saturn-10th "honor" and the Saturn-9th "long wanderings" claims.
