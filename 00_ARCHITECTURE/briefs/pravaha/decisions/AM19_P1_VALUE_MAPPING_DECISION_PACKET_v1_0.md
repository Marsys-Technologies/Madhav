---
artifact: AM19_P1_VALUE_MAPPING_DECISION_PACKET
version: "1.0"
status: "DRAFT FOR THE NATIVE — nothing here is decided. Until you rule, running-period (daśā-lord) windows are stored 'unqualified (value mapping undeclared)': directed where the classical text directs, never given an invented number."
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 (steward M20261002T025939-32d3)
evidence_rule: "classical content only from the served corpus, cited by locator; what the engine does today from its own files; no measurement was run; nothing from memory"
supersedes_nothing: true
---

# AM-19 — how should the engine score the "running-period planet's transit" path (P1)?

## In plain words
The daśā-lord path (called P1) asks: while a planet's period (daśā / bhukti / antara) is running, is that planet, **as it moves through the sky**, in a sign that helps or harms it? Today the engine can say *which direction* the classics give (good or bad) but has **no rule for how big** the effect is, so it stores these windows as "unqualified" rather than guess. Seven small questions turn that into a scored result. Each has a cheapest honest answer ("don't score it"), and I show what the books give so you can choose.

## What the classical text actually says (served corpus, read verbatim)
* **Phaladīpikā XX.37 (`phaladeepika:PG250:C1`):** if the planet whose period is running, *during his transit*, passes through his **depression (debility) sign or an inimical sign, or becomes eclipsed (combust)** — "there will be much misery"; if he passes through his **own or exaltation sign, or is retrograde** — "the effects will then be good". **XX.38:** for a period lord who is auspicious, the good shows when the **Sun enters that planet's exaltation sign** (the same when **Jupiter** transits it); for an inauspicious one, the evil shows when the **Sun** passes through that planet's **depression or inimical sign**.
  *What this is:* a **good / bad switch by the quality of the sign**, with three bad triggers and three good ones. It gives **no numbers and no ranking** between them, and does not say what happens when a good and a bad trigger hold at once (for example, exalted but combust).
* **Strength tables (for sizing, if you want sizing):** BPHS ch.27 ślokas 2–4 (`bphs:PG264:C1`) — a planet in its mūlatrikoṇa sign gets **45 virupas**, own sign **30**, great-friend's **20**, friend's **15**, neutral's **10**, enemy's **4**, great-enemy's **2** (for the sign; the same scale repeats for six sub-charts), and **exaltation strength is a separate scale that is at most 60 virupas = 1 rūpa** (zero at the deep-debilitation point). Uttara Kālāmṛta (`uttara_kalamrita:PG27:C2`) gives a rūpa scale: **exalted 1, mūlatrikoṇa ¾, own ½, friend ¼, great friend ¾ (as printed), neutral ⅛, enemy 1⁄16, bitter enemy 1⁄32**. They **agree** on mūlatrikoṇa, own and friend; they **disagree** on great friend (⅓ vs ¾ as printed — the printed ¾ is odd and may be a translation slip), neutral (⅙ vs ⅛), enemy and great enemy (small). Neither names a debility figure.
* **What the project already carries:** an "ordering anchor" copied from BPHS (the 45/30/20/15/10/4/2 figures, flagged "ordering only — no magnitude claim"), no entry for exaltation or debility, and **three different sign-quality vocabularies** (the registry's 6, that anchor's 7, the natal chart's 9).

## The decisions

**D1 — Which vocabulary of sign-quality?** The natal chart (L1) already classifies a planet in a sign as one of nine: exalted, mūlatrikoṇa, own, great friend, friend, neutral, enemy, great enemy, debilitated. *Recommend: use these nine for transit too* (one authority, natal and transit never disagree). Alternative: collapse to the registry's six.

**D2 — How big should each quality count?** Options: **(a) none — direction only** (cheapest, nothing invented; windows stay directed-but-unscored); **(b) a labelled "uncalibrated default" that only preserves the classical order**, taken from the cited tables: *exalted 1 · mūlatrikoṇa ¾ · own ½ · friend ¼ · … · debilitated 0* (as fractions of one rūpa; the two sources disagree on the middle-low values — you would pick BPHS's, which is the main Parāśari text, or Uttara Kālāmṛta's); **(c) equal rank steps** (same order, evenly spaced; invents the spacing). *Recommend (b) with BPHS for the middle values, labelled "ordering only, no magnitude claim", with exaltation 1 from Uttara Kālāmṛta and debilitated 0 from the strength-at-the-debilitation-point rule*; but (a) is the honest minimum.

**D3 — Are friendly and neutral signs good, bad or neither?** The text names only own/exaltation (good) and debility/inimical (bad). *Recommend: friendly = mildly good, neutral = no direction (unscored)* unless you prefer to leave both undirected.

**D4 — Combustion.** (i) Accept the system's own "too close to the Sun" table for transits (the same one the natal chart uses: Moon 12°, Mars 17°, Mercury 14° (12° retrograde), Jupiter 11°, Venus 10° (8° retrograde), Saturn 15°; nodes never)? A modern Nāḍī book gives Jupiter 12° — shown so you can decide (`design/P1_INPUTS_ANSWER_v1_0.md`). (ii) The text says combustion is a **bad trigger** (XX.37) with no grading — *recommend: a bad direction with a single yes/no level, no "deeply combust" grading*, since no served text grades it.

**D5 — When a good and a bad trigger hold at once** (exalted but combust; own sign but retrograde…). The text is silent. Options: **(a) the engine says "mixed" and does not net them** (the engine's rule is never to net opposite evidence); **(b) bad overrides good** (the text's "much misery" wording is the stronger); **(c) leave unscored (unqualified)**. *Recommend (c) until a source is found — it invents no priority.*

**D6 — Retrograde.** XX.37 says retrograde is a **good** trigger; the engine's factor list has no retrograde factor, so today it is silently ignored. Add it (cited), or note it as not used. *Recommend: add it as a named directional factor once D5 is ruled, since the conflict rule decides what it does.*

**D7 — "Auspicious" and "inauspicious" period lords (the Sun/Jupiter clause, XX.38).** How should the engine decide whether a period lord is auspicious? The text does not say; the nearest rule is the lord's natal relation to the event's houses (already computed). *Recommend: leave this clause unscored until you name the rule; the own-transit clause (XX.37) can be scored first.*

## What happens after your answer
Each ruling becomes an amendment and a new factor version (existing versions are never edited once bound); the engine then stores P1 windows with the chosen directions and sizes, always labelled "ordering only" if you choose (b). **Until you rule, nothing changes:** P1 windows stay "unqualified" and are never counted as passing evidence.

## Open items (recorded, not decided here)
* The OCR in `bphs:PG264:C1` is degraded (the Sanskrit lines are garbled); the English lines quoted are legible. A human should confirm the seven figures.
* `uttara_kalamrita:PG27:C2` prints great-friend = ¾ (equal to mūlatrikoṇa) — probably a slip; do not rely on it.
* Depression figures: neither text gives one for the sign itself.
* The Mercury/Moon mūlatrikoṇa one-degree finding (L0/L1) is with the data owner; it does not change this decision.
