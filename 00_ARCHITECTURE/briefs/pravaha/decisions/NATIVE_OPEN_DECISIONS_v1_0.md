---
artifact: NATIVE_OPEN_DECISIONS
version: "1.7"
status: LIVING — the one place the native's open decisions for the Gochara build are listed (steward M20261002T004621-2b84)
date: 2026-10-02
author: Stream B (Śāstra)
rule: "Plain language. One paragraph each. Nothing here is decided; until you rule, the engine says 'unqualified' (named), never a made-up number."
---

# Decisions only you can make

**ND-ORB-ADMISSION — how close must a moving planet come for a "touch" to exist at all?** When a planet moves toward an exact point in your chart (a planet's
degree, a sensitive degree), within how many degrees does the engine count it as touching? This decides how **long** each touch lasts and so how many **days**
look "active" — the number the false-alarm test caps. Change it and every touch and its duration changes, so everything built on them must be rebuilt.
In the places we searched, the classical books we can read **gave no such number for transit contact** (*not found in the stated searches* — that is a statement
about those searches, not proof that no book has one; a Tājaka orb table from another system and a combustion table were found and are shown as analogies only).
Until you decide, every true-point contact is marked "unqualified" (the engine declines to score it); signs, houses and nakṣatras are not affected.

**ND-ORB-SCALE — once a touch exists, how strongly does it count as the planet nears exact?** This is the angle over which the "activity" falls from full to
nothing. It only **orders** touches against each other: with the touches already fixed it changes **no day counts** and cannot by itself change the false-alarm test.
Until you decide, the ranking inside a point contact is "unqualified".

**One ruling or two?** You may give **one value for both** (say so in the ruling) or **two separate values**; a ruling must state which. A ranking-only (SCALE)
change can never silently change which touches exist (ADMISSION). The options, what each rests on, and the corrected effects are in
`decisions/ND_ORB_DECISION_PACKET_v1_1.md` (v1.0 is superseded and must not be used); the recommendation there is to decide the two questions separately — for
admission the orb the engine already uses, openly labelled "engine convention, not classical", is the least-new-number choice, a smaller chosen value is equally
legitimate, and neither is cited.

**ND-VIPAREETA — is "cancelled obstruction" used, and on what authority?** In transit practice, an obstruction (vedha) of a good transit can be
said to be cancelled in special circumstances. The passages of Phaladīpikā we can read (chapter XXVI, verses 3–8) say that an occupied obstructing
place cancels the good result, and mention exceptions between certain planet pairs, but contain **no cancellation of the obstruction itself**, and
our other served texts gave none either. Until you name a source (or decide to use it as an uncited practice), the engine never marks an obstruction
as cancelled — it stays an obstruction. Decision: use it (on which citation), use it as a labelled uncited practice, or leave it out.

**ND-NODE-VEDHA — do Rāhu and Ketu obstruct?** The verses we can read speak of "planets other than…" without saying whether the two nodes count as
obstructors, and our database itself marks the node rows as unsourced. For now, whenever a node sits in the obstructing place and no ordinary planet
does, the engine says "unqualified" for that stretch — neither "obstructed" nor "clear". Decision: nodes obstruct, nodes do not obstruct, or leave
undecided (the current honest state).

**Human re-read of the Bṛhat Pārāśara passage on graduated aspects.** The specification cites lines of Parāśara's text for the quarter / half /
three-quarter / full aspect rule. Our reading tool could not retrieve those lines, so the code cites other texts we could read instead (Bṛhat Jātaka
ii.13 and Jātaka Pārijāta). A person should read the Parāśara passage and confirm it says the same. Nothing is blocked on this; it is a
confirmation owed.

**ND-COMBUSTION — do you accept the system's own "too close to the Sun" table for transits?** The system already holds one table of how close to the Sun each
planet must be to count as "burnt" (the Moon 12°, Mars 17°, Mercury 14°, Jupiter 11°, Venus 10°, Saturn 15°; Mercury 12° and Venus 8° when moving backward; the two
nodes never). It sits in the base reference data, and the natal chart already uses it — so transits should use the same one, not a second table. What you are
asked to accept: (1) that table for transit use; (2) its source is only labelled at chapter level ("Saravali ch.6 / Parāśara ch.3"), and the one other table we could read
(a modern Nāḍī book) says Jupiter 12° rather than 11° — shown so you can decide. Until you decide, the daśā-lord path stays "unqualified" (named, not scored). Details:
`design/P1_INPUTS_ANSWER_v1_0.md`.

**ND-P1-FRAME — when the engine states "which house" a running-period planet's transit is in, counted from where?** The books we can read (Phaladīpikā XX.34 and XX.59) count the period lord's
transit **from the ascendant**; none counts from the planet's own birth sign. **The engine uses the ascendant** (ruled as AM-20). This is a label only: nothing in the scoring reads the number, so the choice changes no
result. You are asked only to confirm or object; nothing waits on you. Details: `design/P1_FRAME_ANSWER_v1_0.md`.

**AM-19 — how should the running-period planet's transit be scored?** Seven small questions (which sign-quality vocabulary; how big each quality counts; whether friendly/neutral signs are good, bad or neither; combustion; what happens when a good and a bad trigger hold together; the retrograde clause; what makes a period lord "auspicious") are laid out in plain language, with the passages we can read and what the two strength tables say, in `decisions/AM19_P1_VALUE_MAPPING_DECISION_PACKET_v1_0.md`. The cheapest honest answer to each is "don't score it"; until you rule, these windows stay "unqualified".

**ND-ROLES — who holds the "verified" stamp and the "published" seal?** Today neither exists as a separate key, and the builder is even allowed to write the verification stamp itself, so the stamp would prove nothing. This **blocks the first candidate build**: it must be built and held without database-level independence until you decide. Four options (separate credentials with no role switching — recommended; the pipeline switching role inside its own session; one job holding two logins; keep today's arrangement and disclose it), what each needs built and what each costs, the governance rules each must respect (one would be reverted by an existing deploy gate), and what happens to the builder's current permission to write the verification stamp, are in `decisions/ND_ROLES_DECISION_PACKET_v1_0.md`.
