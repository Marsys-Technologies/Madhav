---
artifact: ND_ORB_DECISION_PACKET
version: "1.0"
status: "SUPERSEDED by ND_ORB_DECISION_PACKET_v1_1.md (Codex round 6 R8: it conflated the admission/contact orb with the activity scale and mis-stated options A, D and E) — do not decide from this version"
date: 2026-10-02
author: Stream B (Śāstra), item B6.0
decision_needed: "Which 'orb' (how close, in degrees, a moving planet must be to an exact point in your chart before it counts as touching it), and how strongly it counts as it gets closer."
evidence_rule: "classical content below comes only from the served corpus, cited by locator; numbers about the project are from its own files; nothing from memory; no candidate measurement run was made"
---

# ND-ORB — how close is "touching"?

## In plain words
A transit "touches" a point in your chart (a planet's exact degree, a sensitive degree) over a *stretch of time*, not an instant: the planet
approaches, is exact, then leaves. The **orb** is how many degrees either side still count. It sets (a) how **long** each touch lasts, so
(b) how many **days** the engine calls "active" — which is exactly what the evaluation's false-positive test (T-FP) caps (270 days per
adverse class where one event is known, 540 where two). **Signs, houses and nakṣatras are not affected** (they use the in/out step already
ruled); this is only for true *point* targets.

## What the served corpus does and does not give us
* **No classical orb for transit contact was found.** Two searches for per-graha dīptāṁśa-style orbs and conjunction/aspect orbs returned
  none with a locator.
* The **only per-graha degree table found is for combustion** (distance from the Sun): Moon 12°, Mars 17°, Mercury 14° (12° retrograde),
  Venus 10° — `nadi_navamsa_patel:PG2524:C1` (a modern Nāḍī text, provenance MEDIUM; the Jupiter/Saturn lines were not in the retrieved
  chunk); a similar, OCR-garbled table in `yavana_jataka:PG943:C2` (Pingree, Hellenistic school). These are *Sun-closeness limits*; using
  them as general contact orbs would be an analogy, not a citation.
* **Aspects have a classical continuous rule with no orb at all:** Parāśara's *sphuṭa-dṛṣṭi* table in BPHS gives aspect strength in virupas
  as a smooth function of the angle between the planets (served as `bphs:PG257:C1`; the chunk is OCR-degraded but plainly monotone, starting
  at 30° → 0 and rising by 0.25 virupa per half-degree). Hora Sāra says the same thing in words — "aspect is formed only by longitudinal
  distance between planets" (`hora_sara:PG231:C2`). It governs **aspects**, not conjunctions.
* The project's own numbers, **none ratified as an activity orb**: 5.0° and 1.0° were "candidates" in the plan (`GOCHARA_PLAN_V3_AMENDMENT_v1_0.md:32`);
  the kernel's table (`gochara_kernel/convention.py:80–93`) uses 1.0° (slow planets) / 3.0° (Moon) for conjunction and aspect contact,
  0.5° / 2.0° for returns — each flagged *uncited extension*; the old '4.x' build used 5.0° and says "unratified".

## The options
| | What it rests on | Effect on how many point records | Effect on false-positive (T-FP) exposure, in principle |
|---|---|---|---|
| **A. No orb — exact degree only** | Cleanest reading of "uncited": invent nothing | A point touch becomes a single instant, so it cannot form a window: **point-target records effectively disappear**; signs/houses/nakṣatras stay | **Lowest** — but coverage (T-cover) falls too; the engine says less |
| **B. One flat orb you choose** (e.g. 1°, 3° or 5°) | Nothing in the corpus (uncited) — your decision alone | Contacts exist wherever the planet gets within the orb, so a bigger orb adds near-misses and merges neighbours | Active days grow roughly **in proportion to the orb**. Slow planets (Saturn moves about 1/30° a day on average) spend about a month per degree each side: 1° ≈ 2 months, 5° ≈ 10 months of "active" for **one** touch — against a 270-day budget. (General astronomy, not from the corpus.) |
| **C. Per-graha orbs borrowed from the combustion table** | Corpus has it, but for a different purpose (Sun-closeness); Jupiter/Saturn not retrieved | Different per planet; fast planets get wide orbs | Uneven and hard to reason about; borrowing = analogy |
| **D. Classical continuous rule for aspects + a separate choice for conjunctions** | Aspects: BPHS sphuṭa-dṛṣṭi table, Hora Sāra (served). Conjunctions: still no citation | Aspects need **no orb**; only conjunction still needs B or A | Aspects handled on classical footing; the conjunction question remains |
| **E. Adopt the orbs the engine already uses to find contacts** (1°/3° etc.) as a *declared uncited extension*, with your ruling granting it scoring (the project's rule for uncited rules, spec §0) | Project's own pinned table — no new number invented, one source for "is there a contact" and "how active" | Same as today's contact list; fewer than the old 5° build | **Low-to-moderate**; the 1° choice keeps one touch near 2 months for slow planets |

## Recommendation (mine, not a ruling)
**E for conjunction/point contacts, and D's classical rule for aspects when we get to it** — i.e. use the orb the contact was already found
with, declare it openly as an *uncited extension under your ruling*, and show it on every served answer as "orb: 1° (engine convention, not
classical)". It adds no new invented number, keeps false-positive exposure smallest among the options that keep point records alive, and
leaves the door open to replace it with a cited rule later (a new version, never an edit). If you prefer to invent nothing, **A** is the honest
alternative — at the price of silence on point targets. I would not choose B at 5° (the old build's number): it is the one most likely to
trip the false-positive test.

## What happens after your answer
Your choice is recorded as a ruling; the factor row's orb is set (`activity_kernel@1.1.0`, `orb_deg`) under a new version if needed; the point
branch becomes qualified; nothing already built changes. **Until you rule, point targets stay "unqualified"** (named, not zero).

## Open items recorded (not cited)
* **Human re-read owed:** BPHS lines the specification cites for the graduated aspect rule (`BPHS1:16496-16502`) were not retrievable by
  verse from the served corpus; a person should read them. Nothing here depends on them.
* The Jupiter and Saturn lines of the combustion table were not in the retrieved chunk (`nadi_navamsa_patel:PG2524` continues).
* No measurement was run; the effects above are principles, to be measured only after a ruling.
