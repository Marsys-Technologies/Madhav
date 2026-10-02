---
artifact: ND_NODE_RETROGRADE_VEDHA
version: "1.0"
status: "FOR THE NATIVE — nothing here is decided. Needed before the node-series switch (step 3) rebuilds the vedha rows."
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 (steward M20261002T061832-8c7c)
evidence_rule: "classical text only from the served corpus, cited by locator (read from `classical_text_chunks` today); row counts are read-only production figures for the canonical chart plus the MEAN series computed with pyswisseph 2.10.03 — an ESTIMATE, no build was run."
---

# Should a retrograde Rāhu/Ketu be marked "intensified" when it blocks a transit?

## In plain words
Our vedha rows carry a small label, `retrograde_malefic`, on an obstruction made by a harmful planet **while it is moving backwards** (the classical idea: a harmful planet moving backwards does more harm). It is a label only — it carries **no weight, and nothing in the system reads it** (checked: only the writer mentions it). The switch of Rāhu/Ketu from the "true" to the "mean" orbit makes the nodes move backwards **every single day** (the true node is backwards ~74 % of days and forwards the rest). So the label would now appear on **every** node obstruction. You are asked whether that is right.

## What the served corpus says
* **Phaladīpikā XXVI.48, locator `phaladeepika:PG348:C1`:** *"In the case of Rahu and Ketu, which are always retrograde, the (Vedha) will be on the right, and in the case of the Sun and the Moon which move direct … the (Vedha) will be on the left. Owing to there being no uniformity in motion among the other planets, three kinds of Vedhas have been mentioned. **Malefics when retrograde will cause intense evil if they are in (Vedha) position, while benefics will do immense good.**"* And `PG350:C1`: *"…death if the motion be retrograde. If the motion be direct, the sickness will soon subside."*
* So the **same passage that gives the intensifier calls the nodes "always retrograde"** and does not carve them out. It does **not** say "natural motion is not a condition".
* **Honest limit:** that passage belongs to the **Sarvatobhadra wheel's** vedha (stars, letters, vowels), not to the twelve-house transit obstruction our rows record. Using it for house-vedha rows is an extension the project already made (ruling M-2: typed testimony, no weight). Our own reference table already says the same of the nodes ("always vakra", `bg_dignity_reference.py:311–313`). One more weak echo: `nadi_navamsa_patel:PG2122:C1` (provenance MEDIUM) speaks of the nodes' "backward" transits.

## What the rows do today (TRUE series), canonical chart
* 127 house-vedha rows. A node sits in the blocking sign during **19** of them; **16** carry the label today (Rāhu: 15 of 18; Ketu: 1 of 1). The other Rāhu rows lack it only because the true node happened to be moving forwards on those days.
* **A data defect found on the way:** the stored Ketu rows have the **opposite** backward/forward flag and speed sign to Rāhu on **all 91 676 dates** (checked: Rāhu −0.1791 °/day, Ketu +0.1791 on 2026-11-25). Ketu = Rāhu + 180° must move the same way. Today's Ketu label is therefore wrong in principle (it happened not to change the one Ketu row). L0 must fix this in the MEAN rows.
* All 127 production rows are in the old (pre-"interval") shape, so the served engine currently **ignores them** (§ spec 12); the label would matter only after the rebuild.

## Options
| | what it means | rows with the label after a MEAN rebuild (estimate) | vs today (16) |
|---|---|---|---|
| **(a)** nodes never carry it | "natural motion is not a condition" | 0 | −16 |
| **(b)** nodes always carry it | follows the passage's own premise; the label becomes constant for nodes | 18 | +3, −1 |
| **(c)** keep the true-orbit flags for this one purpose | two orbit conventions in one system; also carries the Ketu defect | 15 | −1 |
(The "−1" in (b) and (c) is one real change unrelated to the label: on 2026-11-28/29 the Moon row's Rāhu obstruction disappears under the mean orbit, because the mean Rāhu is still in Aquarius — see the step-3 spec, O-NS-3.) In every option **no served number changes**, because nothing reads the label.

## Recommendation: **(b), always — recorded with its basis**
The corpus premise ("always retrograde") is exactly what the mean orbit encodes, so (b) is the only option that follows the text without inventing an exemption (a) or a second convention (c). Store the label's basis on the row (`node_always_retrograde:PG348:C1`) and say plainly that for nodes it carries no information. If you prefer (a), it needs a doctrinal source for the exemption — none was found in the served corpus.

## Both readings, no advocacy from L0
Suvarṇa (L0) first leaned to **(a) "never for nodes"** (a flag true on every node row carries no information; true-orbit flags would put two node conventions in one row) and **withdrew that lean after the corpus citation** (M20261002T062318-29c1). The two readings that remain, with no advocate from L0: **(a)** is the cleaner data (no constant label) but needs a doctrinal source for exempting the nodes, and the served passage calls them "always retrograde" without exempting them; **(b)** follows the passage's premise but stores a constant. Stream B's recommendation stays (b), recorded with its basis; the native decides.

## Decision needed
(1) a, b or c. (2) *(settled)* L0 accepted the Ketu inversion as F-L0-08: MEAN Ketu rows carry Rāhu's speed and flag; the vedha writer derives Ketu's retrograde days from Rāhu's rows whatever happens to the old TRUE Ketu rows (step-3 spec §12a).
