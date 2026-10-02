---
artifact: AM19_P1_VALUE_MAPPING_DECISION_PACKET
version: "1.1"
status: "v1.1 — CORRECTS v1.0, which said the classics give no sizing: a fuller read found a six-step ladder in the same chapter (Phaladīpikā XX.30) and Brihat Jātaka XX.11. DRAFT FOR THE NATIVE — nothing here is decided. Until you rule, running-period (daśā-lord) windows are stored 'unqualified (value mapping undeclared)': directed where the classical text directs, never given an invented number."
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 (steward M20261002T025939-32d3)
evidence_rule: "classical content only from the served corpus, cited by locator; what the engine does today from its own files; no measurement was run; nothing from memory"
supersedes_nothing: true
---

# AM-19 — how should the engine score the "running-period planet's transit" path (P1)?

## In plain words
The daśā-lord path (called P1) asks: while a planet's period (daśā / bhukti / antara) is running, is that planet, **as it moves through the sky**, in a sign that helps or harms it? Today the engine can say *which direction* the classics give (good or bad) but has **no rule for how big** the effect is, so it stores these windows as "unqualified" rather than guess. Seven small questions turn that into a scored result. Each has a cheapest honest answer ("don't score it"), and I show what the books give so you can choose.

## What the classical text actually says (served corpus, read verbatim)
* **The switch (Phaladīpikā XX.37–38, `phaladeepika:PG250:C1`):** if the planet whose period (bhukti) is running, *during his transit*, passes through his **depression or an inimical sign, or becomes eclipsed (combust)** — "much misery"; through his **own or exaltation sign, or is retrograde** — "the effects will then be good". **XX.34 (`phaladeepika:PG249:C1`):** the planet whose **Dasa** is running, passing in transit through his own, exaltation **or a friendly** house, "will promote the prosperity of the Bhava it represents when counted from the Lagna, provided the said planet is endowed with full strength at the birth time as well"; **XX.35:** a Dasa lord who is weak, eclipsed, in depression or an inimical house **at birth** destroys that Bhava when transiting any house. **XX.38:** for an auspicious bhukti lord the good shows when the **Sun** enters his exaltation sign (likewise **Jupiter**); for an inauspicious one the evil shows when the **Sun** passes through his depression or inimical sign.
* **The ladder (Phaladīpikā XX.30, `phaladeepika:PG247:C1`, and Brihat Jātaka XX.11, `brihat_jataka:PG425:C1` — both served, both read):** "**The good influence of planets is at its maximum, three quarters, a half, a quarter, at its minimum or nil** according as the planets are in the **exaltation sign, Mūlatrikoṇa, Swakshetra (own), friendly sign, inimical sign or depression sign** respectively." Brihat Jātaka adds a seventh position — "**(combustion) conjunction with the Sun**" — at the low end, and the translator's note: "**this order should be reversed for the malefics**" (i.e. a malefic's *evil* follows the ladder the other way). So: **exalted 1 · mūlatrikoṇa ¾ · own ½ · friendly ¼ · inimical "minimum" · depression nil (combustion at the nil end)**. *The text gives no number for "minimum", and no rung for a neutral sign.*
* **Other served strength tables (alternatives, if you prefer them):** BPHS ch.27 ślokas 2–4 (`bphs:PG264:C1`) — mūlatrikoṇa 45, own 30, great-friend 20, friend 15, neutral 10, enemy 4, great-enemy 2 virupas (60 virupas = 1 rūpa; exaltation a separate scale, zero at the debilitation point); Uttara Kālāmṛta (`uttara_kalamrita:PG27:C2`) — exalted 1, mūlatrikoṇa ¾, own ½, friend ¼, neutral ⅛, enemy 1⁄16, bitter enemy 1⁄32 (it prints great-friend ¾, probably a slip). **Phaladīpikā's own ladder and Uttara Kālāmṛta agree on 1, ¾, ½, ¼.** The ladder in the path's own source chapter is the natural default.
* **What the project already carries:** an "ordering anchor" copied from BPHS (no exaltation or debility entries) and **three different sign-quality vocabularies** (the registry's 6, that anchor's 7, the natal chart's 9).

## The decisions

**D1 — Which vocabulary of sign-quality?** The natal chart (L1) already classifies a planet in a sign as one of nine: exalted, mūlatrikoṇa, own, great friend, friend, neutral, enemy, great enemy, debilitated. *Recommend: use these nine for transit too* (one authority, natal and transit never disagree). Alternative: collapse to the registry's six.

**D2 — How big should each quality count?** Options: **(a) none — direction only** (nothing invented); **(b) the Phaladīpikā's own ladder, labelled "uncalibrated default — ordering only"**: *exalted 1 · mūlatrikoṇa ¾ · own ½ · friendly ¼ · inimical (the text says "minimum" — you pick the number, e.g. ⅛, or 0 and rank it just above depression) · depression 0*, with the combustion rung at 0 (Brihat Jātaka XX.11); **(c) equal rank steps**; **(d) a BPHS / Uttara Kālāmṛta scale** instead (shown above). *Recommend (b)*: it is in the path's own source chapter, two other texts agree on its upper rungs, and the only missing number is "minimum" — which you can set or leave as a rank.

**D3 — Friendly and neutral signs.** The text names **friendly** as good (XX.34 "a friendly house"; the ladder's ¼ rung) and says nothing of **neutral** (the ladder has no neutral rung; BPHS and Uttara Kālāmṛta do). *Recommend: friendly = good at ¼; neutral = leave unscored* (or place it between friendly and inimical by your choice).

**D4 — Combustion.** (i) Accept the system's own "too close to the Sun" table for transits (the natal chart already uses it: Moon 12°, Mars 17°, Mercury 14° (12° retrograde), Jupiter 11°, Venus 10° (8° retrograde), Saturn 15°; nodes never)? A modern Nāḍī book gives Jupiter 12° — shown for your decision (`design/P1_INPUTS_ANSWER_v1_0.md`). (ii) **Level:** Brihat Jātaka XX.11 puts combustion at the **nil end of the same ladder** (with depression) and Phaladīpikā XX.37 lists "eclipsed" among the bad triggers — *so recommend: combustion = the nil rung (0), a single yes/no, no "deeply combust" grading* (none served).

**D5 — When two rungs hold at once** (a planet exalted but combust; own sign but retrograde…). In Brihat Jātaka XX.11 combustion is an *alternative position on the ladder*, not a separate multiplier, and the text never combines rungs. **Also: the translator's note says the ladder is reversed for malefics** — so benefic/malefic nature (already a factor) decides whether a high rung means good or evil. Original question: **when a good and a bad trigger hold at once** (exalted but combust; own sign but retrograde…). The text is silent. Options: **(a) the engine says "mixed" and does not net them** (the engine's rule is never to net opposite evidence); **(b) bad overrides good** (the text's "much misery" wording is the stronger); **(c) leave unscored (unqualified)**. *Recommend (c) until a source is found — it invents no priority.*

**D6 — Retrograde.** XX.37 says retrograde is a **good** trigger; the engine's factor list has no retrograde factor, so today it is silently ignored. Add it (cited), or note it as not used. *Recommend: add it as a named directional factor once D5 is ruled, since the conflict rule decides what it does.*

**D7 — "Auspicious" and "inauspicious" period lords (the Sun/Jupiter clause, XX.38).** How should the engine decide whether a period lord is auspicious? The text does not say; the nearest rule is the lord's natal relation to the event's houses (already computed). *Recommend: leave this clause unscored until you name the rule; the own-transit clause (XX.37) can be scored first.*

## What happens after your answer
Each ruling becomes an amendment and a new factor version (existing versions are never edited once bound); the engine then stores P1 windows with the chosen directions and sizes, always labelled "ordering only" if you choose (b). **Until you rule, nothing changes:** P1 windows stay "unqualified" and are never counted as passing evidence.

## Open items (recorded, not decided here)
* The OCR in `bphs:PG264:C1` is degraded (the Sanskrit lines are garbled); the English lines quoted are legible. A human should confirm the seven figures.
* `uttara_kalamrita:PG27:C2` prints great-friend = ¾ (equal to mūlatrikoṇa) — probably a slip; do not rely on it.
* Depression figures: neither text gives one for the sign itself.
* The Mercury/Moon mūlatrikoṇa one-degree finding (L0/L1) is with the data owner; it does not change this decision.

## Added in v1.1 (found while answering Stream A's questions)
* **The Dasa lord's natal condition matters in the text:** XX.34 (good transit effect only "provided the said planet is endowed with full strength at the birth time") and XX.35 (weak/eclipsed/depressed/inimical **at birth** ⇒ destruction of the Bhava on any transit). That is exactly the candidate **AM-12** (`sad_bala_sufficient` as a soft factor); it is a **natal precondition**, separate from the transit sign-quality ladder.
* **Levels:** the verses speak of the **Dasa** (XX.34–35) and the **Bhukti** (XX.37–38) lords only; the **pratyantara (PD) level has no verse** in these ślokas — the specification's "MD/AD/PD" is its own extension (`design/GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md` §AM-21 part 2). Decision for you: score PD-level windows (as an uncited extension), mark them testimony, or leave them out. *Recommend: testimony until a source is named.*
