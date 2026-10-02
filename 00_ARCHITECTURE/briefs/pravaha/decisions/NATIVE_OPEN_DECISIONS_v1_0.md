---
artifact: NATIVE_OPEN_DECISIONS
version: "1.1"
status: LIVING — the one place the native's open decisions for the Gochara build are listed (steward M20261002T004621-2b84)
date: 2026-10-02
author: Stream B (Śāstra)
rule: "Plain language. One paragraph each. Nothing here is decided; until you rule, the engine says 'unqualified' (named), never a made-up number."
---

# Decisions only you can make

**ND-ORB — how close is "touching"?** When a planet moves toward an exact point in your chart (a planet's degree, a sensitive degree), how many
degrees either side still count as touching it? The classical books we can read give no such number for transit contact. Until you decide, every
true-point contact is marked "unqualified" (the engine declines to score it); signs, houses and nakṣatras are not affected. The options, what each
rests on, and their effect on how long things look "active" are in `decisions/ND_ORB_DECISION_PACKET_v1_0.md`; my recommendation there is to adopt
the orb the engine already uses to find contacts, openly labelled "engine convention, not classical".

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
