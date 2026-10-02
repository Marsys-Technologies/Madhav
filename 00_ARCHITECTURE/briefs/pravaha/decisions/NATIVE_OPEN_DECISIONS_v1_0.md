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

**ND-COMBUSTION — how close to the Sun is "burnt"?** The daśā-lord path asks whether the period-ruling planet is "combust" (too close to the Sun to give its
results). The only table of distances our readable texts give comes from a modern Nāḍī book (Moon 12°, Mars 17°, Mercury 14°, Venus 10°, Jupiter 12°, Saturn 15°; slightly
smaller for Mercury and Venus when moving backward) and a garbled Greek-influenced table — and they **disagree about Jupiter** (12° vs 11°); neither is the Parāśara school the
rest of the system cites. Until you decide, that whole path stays "unqualified". Decision: adopt one table (which, and with what label), let the factor drop out of the score
openly ("not scored" disclosed) until a classical source is read, or leave the path unqualified. Details: `design/P5_P1_SWEEP_ANSWER_v1_0.md`.
