---
artifact: ND_ORB_DECISION_PACKET
version: "1.1"
status: "READY FOR NATIVE — two separate open decisions (ND-ORB-ADMISSION, ND-ORB-SCALE); until ruled, true-point targets stay 'unqualified'"
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 — corrected per Codex round 6 R8
supersedes: "v1.0 (conflated the two decisions below; its options A, D and E were mis-stated; it implied the corpus search was exhaustive)"
evidence_rule: "classical content comes only from the served corpus, cited by locator; project numbers from project files; no candidate measurement was run"
---

# ND-ORB — two questions, not one

A transit "touches" a point in your chart (a planet's degree, a sensitive degree) over a stretch of time. Two different things hang on "how close":

1. **ND-ORB-ADMISSION — when does a contact exist at all?** The angular distance within which the engine counts a transiting planet as touching the point. This sets how **long** each touch lasts and therefore how many **days** the engine calls active — the quantity the false-positive test (T-FP) caps. Changing it changes which contacts and supports exist, so everything built on them must be rebuilt (a new convention and geometry invalidation).
2. **ND-ORB-SCALE — how strongly does an already-counted contact weigh as it nears exact?** The angle over which the "activity" ranking falls from full to zero. It orders contacts; with the supports fixed and no score threshold, **it changes no day counts** and cannot, by itself, alter T-FP.

You may rule **one value for both** (say so explicitly) or two. A ranking-only change can never silently change a support.
Signs, houses and nakṣatras are not affected (they already use the in/out step); this is for true point targets only. Until you rule, those targets are "unqualified" — named, never zero.

## What the served corpus gives (stated searches only — "not found in the stated searches", not "does not exist")
* **Searches made:** English queries for dīptāṁśa/orb values (two), for conjunction/aspect orb and planetary war (one), for combustion limits (two); and a **Devanagari** query (दीप्तांश with the per-graha numbers) against the whole served corpus.
* **Found — a per-graha orb table with a locator, from another system:** *Tājaka Nīlakaṇṭhī* (served in Devanagari, OCR-degraded Hindi commentary), `tajaka_neelakanthi:PG40:C1` (verses 59–60) and `PG49:C1`: **dīptāṁśa — Sun 15°, Moon 12°, Mars 8°, Mercury 7°, Jupiter 9°, Venus 7°, Saturn 9°; Rāhu/Ketu like Saturn (9°); "by another view all grahas 12°"**. It governs when an applying aspect/relationship (*ithaśāla*) between two planets gives its full result in the **annual** chart — an orb for planetary relationships, but in the Tājaka system, not Parāśara's. (The repository file `platform/scripts/bootstrap/lib/tajaka_corpus.ts:27` repeats the same numbers but calls itself a *derived internal summary* — it is not a translation and is not a source.)
* **Found — combustion limits** (Moon 12°, Mars 17°, Mercury 14° / 12° retro, Venus 10° / 8° retro, Jupiter 12°, Saturn 15°; `nadi_navamsa_patel:PG2524–2525`, a modern Nāḍī book, MEDIUM provenance; a garbled Greek-influenced table, `yavana_jataka:PG943:C2`, Jupiter 11°). These are closeness-to-the-Sun limits, a different question.
* **Found — aspects have a classical *strength* rule that depends on the angle** (Parāśara's sphuṭa-dṛṣṭi table, served as `bphs:PG257:C1`; OCR-degraded; the "virupas" rise and fall in segments — an earlier version of this packet called it "plainly monotone"; **that statement is withdrawn**). Hora Sāra: "aspect is formed only by longitudinal distance between planets" (`hora_sara:PG231:C2`).
* **Not found in the stated searches:** any Parāśari statement of an orb for *transit contact* (conjunction or aspect of a transiting planet with a natal point). The project's own numbers — 5.0°/1.0° "candidates" in the plan, and the engine's 1.0° (slow planets) / 3.0° (Moon) contact orbs — are labelled uncited or unratified.

## The options, corrected
| | For ADMISSION (does a contact exist; how long) | For SCALE (ranking inside a contact) |
|---|---|---|
| **A. Exact contact only** | A contact is a single instant. That is **not** "records disappear": a one-instant range is a valid non-empty range, the database does not forbid it, and the evaluation counts it as an inclusive calendar day. We would have to specify its representation and its consequences (one day per exact crossing; many fewer overlapping supports). | Undefined at one instant — activity is 1 at the instant; nothing to rank within a contact. |
| **B. One flat orb you choose** (any value — small values are allowed, e.g. 0.5°, 1°) | Nothing in the stated searches supports a number: your decision alone. Active days grow with the orb; **how much** depends on retrograde loops, stations, overlapping contacts and the span-based paths — the durations in the earlier packet were constant-speed illustrations, **not** predictions. | The scale may equal the admission orb or be smaller/larger. |
| **C. Per-graha orbs borrowed** | Two sources now exist (the Tājaka dīptāṁśa table above — an orb for relationships, other tradition; the combustion table — a Sun-closeness limit). Either is an **analogy**, not a Parāśari transit rule. | Same. |
| **D. Classical angle-dependent aspect strength (sphuṭa-dṛṣṭi)** | Not an "orb removed" variant of the present kernel — a **different strength model**. To use it we would need the complete piecewise rule, the direction (applying/separating), its normalisation, the specials, the treatment of the nodes, the angular domain in which an aspect exists, and how it combines with the quarter/half/three-quarter strength so the same strength is **not counted twice**. Conjunctions still need a separate choice. | Natural home for it, once fully specified. |
| **E. Adopt the engine's own contact orbs** (1° slow planets / 3° Moon) as a declared uncited extension under your ruling | One source for "is there a contact" and "how active", no new invented number; but it is **not demonstrably the lowest-exposure** option that keeps point records — B allows smaller values. | Binds the scale to the same number. |

## Recommendation (mine, not a ruling)
Decide the two questions separately, and say so on the record. For **admission**: E (the orb the engine already uses), openly labelled "engine convention, not classical", is the least-new-number choice; if you prefer fewer active days, B with a smaller value is equally legitimate — neither is cited. For **scale**: either bind it to the admission value or leave ranking inside point contacts unqualified until D is specified. I would not choose 5° (the old build's figure).

## What happens after your answer
Each ruling is recorded; the factor rows are then versioned: **a new factor version and new consuming path versions once the existing rows have been bound** — an unratified, immutable row cannot later acquire an orb in place. An admission change triggers the convention and geometry invalidation; a scale-only change does not touch supports. Until you rule, point targets stay "unqualified".

## Open items (recorded, not cited)
* **Human re-read owed:** the BPHS lines the specification cites for the graduated aspect rule (`BPHS1:16496-16502`) were not retrievable by verse from the served corpus; and the local BPHS text at lines 16605–16630 alternates rising and falling segments — a person should read both.
* The Jupiter and Saturn lines of the combustion table were not in the chunk retrieved (`nadi_navamsa_patel:PG2524` continues at `PG2525`).
* The Tājaka dīptāṁśa chunks are OCR-degraded Devanagari; a human read should confirm the seven numbers.
* No measurement was run; effects are stated as principles.
