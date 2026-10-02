---
artifact: P1_FRAME_ANSWER
version: "1.0"
status: ANSWER (not a spec version; no code). Recommendations marked MINE are not rulings; the anchor question is SILENT in the frozen text and therefore becomes a native decision (ND-P1-FRAME) with candidate amendment AM-20.
date: 2026-10-02
author: stream-B (Exec B)
question: steward M20261002T022539-d267 (Stream A round-7 [3]) — for a P1 transit record in frame `dasha_lord`, what is `house_from_frame` counted from?
sources: "S = GOCHARA_DESIGN_SPECS_v1_4 · O = GOCHARA_TEST_ORACLES_v1_4 · F = services/gochara_rules/frames.py (main) · 1155 = migration 1155 · A = pravaha/a53-am5-inventory @3677cccae, ka_gochara_v5.py:218–229 · AM = amendments draft v0.15. Corpus read this pass (served): phaladeepika:PG250:C1 (ślokas 37–39, verbatim), brihat_jataka:PG215:C1 (VIII.10, verbatim)."
---

# P1 transit record — what is `house_from_frame` counted from?

## 1. What the frozen text, the frames module and the oracles actually say
* **S §0 (frame enum):** `moon | lagna | graha:<X> | dasha_lord | bhavat_bhavam:<house>`; counting is **inclusive of the reference sign**; "every count in an oracle shows it". **No sentence defines the reference sign of `dasha_lord`.**
* **S §2.2 P1:** "**Frame: `dasha_lord` / natal sign positions.**" — the only anchor wording. Read literally it names the *natal sign position of the daśā lord* as the frame's reference; it can also be read as "natal relation, counted from natal sign positions" (AM-15's lagna reading, ruled for the **natal relationship predicate** only). The text does not choose.
* **S §1.2 inv 5:** "House counts are computed from the row's **own `frame`**, arithmetic stored at evaluation time." 1155 enforces it: `kgrr_evaluated_has_house_ck` — a computed row needs `house_from_frame` (1..12). That is why A mints nothing when the anchor is unknown.
* **F (`frames.py`, mine, on main):** `dasha_lord` resolves to the **natal sign of the period lord named in `frame.arg`** ("spec §2.2 P1: natal sign positions"). That is a *reading* I wrote, never ruled; F is the only code that answers.
* **A (`ka_gochara_v5.py:218–229`):** the resolver handles `lagna`, `moon`, `bhavat_bhavam:<h>` and returns `None` for `dasha_lord` (the edge carries no period-lord argument, and the anchor is unruled) ⇒ no P1 record is minted.
* **Oracles:** none exercises a P1 *transit* record's house count. O-PP-1/2 pin the permission context and the natal occupancy relation (Mars in Libra = natal 7th, lagna Aries — a lagna-frame natal fact); O-RP-3 is **P4** (childbirth; Saturn conjunct natal Sun 5L) not P1; O-RP-7 flips a dignity operand (no house); O-RP-8 is enumeration. **So: silent in S, silent in O; only F speaks, as an unruled reading.**

## 2. What the classical text asks for (served corpus, read verbatim)
* **Phaladīpikā XX.37 (`phaladeepika:PG250:C1`):** "If the planet whose Bhukti is in progress should during the course of his transit … pass through his depression or inimical house or become eclipsed; there will be much misery. Should he pass through his own, or exaltation house or be retrograde, the effects will then be good." **XX.38:** "In the case of a planet whose Bhukti is auspicious, the good effect will be manifested when the Sun enters the planet's exaltation sign. The same effect will be felt when Jupiter transits the place. … [for an inauspicious Bhukti] the evil effects will be felt when the Sun in his transit passes through the Bhukti lord's depression or inimical sign."
  Every condition is a **property of the sign** relative to the bhukti lord (its own / exaltation / depression / inimical sign) — **no house is counted from anything**. P1's two scored transit factors (dignity of the transit sign, combustion) need no `house_from_frame`.
  *(Open, not mine to add: XX.37 also says "or be retrograde, the effects will be good" — the P1 factor inventory has no motion factor; flagged for the gate.)*
* **Brihat Jātaka VIII.10 (`brihat_jataka:PG215:C1`):** counting **from the lord of the daśā** exists classically — "when the Rāśi occupied by the Moon happens to be the exaltation sign of the lord of the dasa, or a friendly house, an Upachaya, a Trikona, or the 7th house **with respect to the lord of the dasa**, the effects will be happy" — and the lord's own position counted **from the Lagna** ("in an Upachaya position, viz. 3rd, 10th, 6th or 11th with respect to the Lagna"). Both are **natal** relations; neither is a transit-of-the-lord-from-its-own-natal-sign rule.
* **Gocara counted from the janma-rāśi** (Phaladīpikā XXVI.1, "Gocharapala to be predicted with reference to this [Janma Rasi] alone") governs the **house-transit** results of P2, not the daśā-lord path.
* **Not found:** any served text counting a *transit* house of the daśā lord from the lord's own natal sign, or from the signature house. (The Nāḍī transit-over-navamsa-of-lords passages, `nadi_navamsa_patel:PG736/PG2010`, MEDIUM provenance, are a different technique.)

## 3. The options
| anchor | basis | what it would mean | consequence |
|---|---|---|---|
| **(a) lagna** | S §0 "P3 table is the lagna frame"; AM-15; BJ VIII.10 (lord's position from Lagna) | "which house of the native is the sign the lord is transiting?" | consistent with AM-15 and with H (the signature-house set, counted from the lagna); a P1 record's house then reads in the same frame as its natal relation; but the frame label `dasha_lord` would be a misnomer |
| **(b) janma-rāśi** | Phaladīpikā XXVI.1 | the gocara count | applies to P2's gocara results, not to the daśā-lord path; nothing in XX.34–38 uses it |
| **(c) the period lord's NATAL sign** | S §2.2 P1 "natal sign positions" read literally; F; BJ VIII.10 (counting from the lord of the daśā, natal) | "how far, in signs, is the lord's transit from where it was born" | matches the frame's own name; the only reading under which the label means what it says; requires the edge to carry **which period lord** anchors the frame (for Sun/Jupiter "transiting the bhukti lord's exaltation sign" the lord is the *object*, not the agent) |
| **(d) the sign of the signature house** | none | — | no served basis; would make the frame depend on the class |

## 4. What matters for the build — and MINE
**No P1 predicate, factor, admission test or channel assignment reads `house_from_frame`** (direction comes from dignity/combustion of the sign, S §2.2 P1; the natal relation is AM-15). The number is a *stored descriptor* required by 1155's CHECK. So the choice cannot change a window — only what a reader is told the house number means. It is therefore a **labelled-convention decision**, not a scoring one, and it must not be guessed silently.
**MINE:** adopt **(c)** — it is the literal reading of the one anchor phrase the spec gives, it is what `frames.py` already does, and BJ VIII.10 shows classical counting from the daśā lord. Record it as **candidate AM-20 / ND-P1-FRAME**: *for a P1 transit record `house_from_frame` is the inclusive count from the natal sign of the period lord that anchors the record (`dasha_lord:<graha>`; for the Sun/Jupiter-in-the-lord's-exaltation-sign relation the anchoring lord is the bhukti lord named by the record's `period_lord` object); it is a stored descriptor only — nothing in P1 reads it; the natal relation to H stays AM-15's lagna count.* If the native prefers (a), the same descriptor is simply counted from the lagna and the `dasha_lord` frame label is retired for transit records — equally harmless, and equally to be written down.
**What Stream A needs now (no decision required to prepare):** `RecordEdge` for P1 must carry the **period-lord graha and level** that anchors the frame (so a `dasha_lord:<graha>` frame can be formed); the resolver then needs only the lord's natal sign — a pure lookup F already implements. Until the decision lands A should keep P1 unminted (a stated state), not mint with a guessed anchor.
