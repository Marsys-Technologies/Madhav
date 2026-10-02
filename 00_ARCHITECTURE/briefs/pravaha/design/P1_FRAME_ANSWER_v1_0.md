---
artifact: P1_FRAME_ANSWER
version: "1.2"
status: "ANSWER — AM-20 is RULED: the P1 transit record's house is counted from the LAGNA (steward, Codex round 8). Not a spec version; no code."
date: 2026-10-02
author: stream-B (Exec B)
question: steward M20261002T022539-d267 (Stream A round-7 [3]) — for a P1 transit record in frame `dasha_lord`, what is `house_from_frame` counted from?
sources: "S = GOCHARA_DESIGN_SPECS_v1_4 · O = GOCHARA_TEST_ORACLES_v1_4 · 1154/1155 = migrations · AM = amendments draft v0.20. Corpus (served, verbatim): phaladeepika:PG247:C1, PG249:C1, PG250:C1, PG256:C1; brihat_jataka:PG215:C1."
history: "v1.0 recommended counting from the lord's natal sign (option c) after a narrow read (PG250 + BJ VIII.10). v1.1 withdrew it after a fuller read of Adhyāya XX. v1.2 (this) restates the answer without the withdrawn text."
---

# P1 transit record — what is `house_from_frame` counted from?

## 1. What the frozen text, the registry and the oracles say
* **S §0:** the frame enum includes `dasha_lord`; counting is inclusive of the reference sign; **no sentence defines the reference sign of `dasha_lord`.** **S §2.2 P1:** "Frame: `dasha_lord` / natal sign positions."
* **S §1.2 inv 5 + 1155 `kgrr_evaluated_has_house_ck`:** a computed row stores a house, counted from the row's own frame.
* **1154 `ka_gochara_frame_ok`:** `frame_arg` is NULL for `dasha_lord` — the period lord is therefore **never** carried by the frame (it is carried by the anchor, AM-21 part 2 / migration 1233).
* **Oracles:** none exercises a P1 transit record's house count (O-PP-1/2 pin permission and the natal Mars-in-Libra 7th from lagna; O-RP-3 is P4; O-RP-7 flips dignity; O-RP-8 is enumeration).

## 2. What the classical text says (served corpus, verbatim)
* **XX.34 (`phaladeepika:PG249:C1`):** "When a planet whose **Dasa** is in progress happens to pass through (in transit) his Swakshetra, exaltation or a friendly house, he will promote the prosperity of the **Bhava it represents when counted from the Lagna**, provided the said planet is endowed with full strength at the birth time as well." **XX.35:** a Dasa lord weak, eclipsed, in depression or an inimical house **at birth** destroys that Bhava on transit.
* **XX.59 (`PG256:C1`):** "If the lord of the Dasa in his transit comes to the **Lagna** or if the 3rd, 6th, 10th or 11th house from it … the Dasa will prove auspicious." **XX.60:** the good or evil effect is determined with reference to the house **counted from the Moon** which the Dasa lord occupies (the ordinary house-transit path).
* **XX.36 / XX.61:** the *Moon's* place counted from the lord of the Dasa. **Brihat Jātaka VIII.10 (`PG215:C1`):** natal relations counted from the lord of the daśā and the lord's position from the Lagna.
* **XX.37–38 (`PG250:C1`):** the transit conditions themselves are **sign-qualities** (own/exaltation/depression/inimical; the Sun/Jupiter in the bhukti lord's exaltation sign) — no house is counted.
**No served text counts a graha's transit from that graha's own natal sign.**

## 3. AM-20 (RULED)
**`house_from_frame` of a P1 transit record is the inclusive count from the lagna** — the same count as AM-15 and the P3 frame, and the count XX.34 and XX.59 use. It is a **stored descriptor**: no P1 predicate, factor, admission test or channel assignment reads it (the verifier tests that changing it cannot alter any of them). The period lord and level that license the record are carried by the **anchor** (AM-21 part 2), not by the frame. `frames.py`'s `dasha_lord:<graha>` reading (the lord's natal sign) has no served basis and is not used for P1 records. The native's confirmation is recorded as ND-P1-FRAME (a label convention; nothing is held pending it).

## 4. Open, not decided here
XX.37 says a retrograde bhukti lord gives good effects; the P1 factor inventory has no motion factor. **A named limitation** of the first candidate: if ever adopted it changes which readings exist (an admission amendment), not only a score.
