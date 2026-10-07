# ND-H-20261005 — the eight classes: houses and significators (decision by delegate, SEALED 2026-10-05)
Authority: owner's delegation, verbatim: "I would like you to spin up a Fable 5.1 agent for me with high effort to take a decision on my behalf on all the five items, with the full context that we have, both from earlier Fable reviews and Astra reviews. Give the full context and let it take a call and seal this. Confirm to me when this is done."
Inputs given to the delegate: RULING10.txt; G10_DECISION_FABLE_v1_0.md; G10_DECISION_ASTRA_REVIEW_v1_0.md; G10_DECISION_RECONCILED_v1_0.md; the frozen specs, ST-H-UNKNOWN, the event registry, the 3.0 baseline, the rule registry on main. Recorded by the strategy session; text below is the delegate's decision unedited.

**DECISION BY DELEGATE — SEALED, 2026-10-05** (ruling id `ND-H-20261005`; Fable 5.1 for the owner, read-only)

**Basis facts I relied on.** `admission.py`: contact = residence or FULL aspect on a house (7th all; Mars 4/8; Jupiter 5/9; Saturn 3/10; nodes none), or conjunction/aspect within 5° on a lord's natal point; P3 unions over all agents; P4 = infl(Jupiter) ∧ infl(Saturn). Spec §0: a derived event rule scores only as `uncited_extension` under a ruling, however well its premises are cited — so every row below is `uncited_extension / scored / ruling_ref ND-H-20261005`, with premise loci in `sources`.

**New loci (served corpus, Uttara Kālāmṛta significator chapter, Sastri, HIGH; memo's "UK unusable" superseded):** 12th house "(28) Migrating to a different place, (29) Expenditure of all kinds" PG121:C1; Mars "(2) Land … (81) House" PG124:C1; Mercury "(19) Commerce" PG125:C1; Jupiter "(36) Penance, (38) Dharma, (53) Mantra, (34) honour from the king" PG127:C1; Saturn "(30) Telling lies" PG130:C1; Rāhu "(13) going to a different country, (17) Falsehood, (19) Perplexity" PG131:C1; Ketu "(6) Final salvation, (11) Great penance, (17) Mantra Shastra, (30) Renunciation" PG132:C1. These cite meanings; event rules stay derived.

**Three tiers.** CORE: in H for P1/P3/P4, all agents. DVI (double-transit-only): counts toward infl(g), g ∈ {Jupiter, Saturn}, house or its lord, in P4 and nowhere else. SUPPORT: annotation rows, `testimony`, outside H; O-RR-7 holds.
**Kāraka roles.** K-A (rank): factor `karaka_agent`, categorical_ordered {karaka > non_karaka}, `uncalibrated_default`, on transit records whose agent is a class kāraka; never admits, excludes or zeroes. K-B (admission, luminaries only): natal Sun/Moon, when kāraka of the class, is a target (`object_role karaka`, degree_point) for Jupiter/Saturn (conjunction or aspect, 5°) and Rāhu/Ketu (conjunction) in P3 and P4's infl(); fast agents never; non-luminary and node kārakas have no K-B.

| class | opens a window | condition | support-only | kārakas (role) | basis |
|---|---|---|---|---|---|
| achievement_recognition | 10 | 11 DVI | 5; 1, 9 | Sun K-A; Jupiter K-A | PhD I.15, BPHS 11.11, UK PG127 (meanings) + derivation; ratified |
| business_launch | 7, 10 | — | 6 | Mercury K-A | PhD I.15, BPHS 11.8; UK PG125 Commerce; derived; ratified |
| financial_deception | 2, 12 | 6 DVI | 8 | Rāhu K-A; Saturn excluded | PhD I.13/I.16, BPHS 24.18, UK PG121; Rāhu UK PG131; derived; ratified |
| foreign_settlement | 12 | 4 DVI | 9, 7 (10 noted) | Rāhu K-A; Saturn excluded | UK PG121 migrating, JP VIII.97; Rāhu UK PG131; derived; ratified |
| parental_event (father, `bhavat_bhavam:9`) | 9, 2 (offsets 1, 6) | — | 8th, 12th from 9th (lagna 4, 8) | Sun K-A + K-B | BPHS 7.39–43, 23.7, PhD II.1; offsets derived; ratified |
| property_acquisition | 4 | 11 DVI | 2 | Mars K-A | BPHS 11.5, 15.14, PhD I.12; Mars UK PG124; derived; ratified |
| psychological_arc | 4 | — | 5, 8 | Moon K-B | BPHS 11.5, PhD I.12, PhD II.2; derived; ratified |
| spiritual_turn | 9, 5 | — | 12 (practice; no śloka located) | Jupiter K-A; Ketu K-A; Saturn testimony on 12th contacts only | PhD I.14/I.12, BPHS 11.6/11.10, UK PG127/PG132; 12 by ratification only |

**Item 1 — AMENDED.** Rule: CORE houses per table; rows at `rule_version 1.2.0`, 1.1.0 untouched; a DVI member is read by P4's infl() only. Reason: single houses lose the recall the owner named as opportunity loss; Fable's triples rebuild the 3.0 union. The one path that is already slow-only and already `uncited_extension/scored` (D-P4) is where a second house enters with doctrine behind it and no fast-agent noise. Sign-bin P4 shares before lords: recognition 11→44%, property 11→39%, foreign 11→24%, deception 29→37%. Pre-registered guard: a class whose P4-alone admitted-day share exceeds the protocol's 40% gain band reverts its DVI member to SUPPORT in the next generation. Business and spiritual already hold two cited houses; the father row is adverse (2.61% budget) — no DVI there (adding its 8th lifts P4 44→62%). Foreign gets 4 (home left for a foreign land), not 9 (journey): settlement is a residence change, 9/7 are travel.

**Item 2 — AMENDED** (6, 11, 11, 4 moved to DVI; rest accepted). Spiritual 12 stays SUPPORT: in P4 it lifts the share to 56%, the logged turns are devotional (9/5), and no śloka was located. Father's 8th/12th-from-9th stay SUPPORT.

**Item 3 — AMENDED.** Rule: Mercury (business), Rāhu (deception, foreign) are kārakas with K-A only. No "Rāhu must be involved" gate: a conjunction gate is a design amendment the frozen spec forbids silently, and it would miss Saturn/Mars/Mercury-driven frauds; deceit is separated from ordinary loss by the 2nd (wealth exposed), the 6th DVI (adversary) and Rāhu's rank effect. Mercury is not added to deception. PhD XXVI.9 "Sun 2nd from Moon — duped" is reserved for a future P2 row. Wording "no verse" corrected: UK loci exist; the event application is what is ratified.

**Item 4 — AMENDED.** Rule: Jupiter and Ketu K-A for spiritual_turn (Ketu upgraded from commentary to UK PG132). Saturn is not a scored spiritual kāraka: it annotates (testimony) contacts to the 12th SUPPORT member only — the engine's only operational meaning of "austerity specifically indicated". Saturn is not a deception kāraka: UK PG130 "telling lies" is the liar's trait, not the victim's exposure (accepted).

**Item 5 — ACCEPTED, specified.** `_CLASS_AFFECTED_PERSON["parental_event"]="father"`; P2 emits no parental_event row (native Moon never evidences the parent, §1.2 inv 6); Sun K-A + K-B. Mother row registered now, unbuilt: anchor 4, offsets {1, 6} (lagna 4, 9), Moon K-A + K-B, state `unsupported` until a per-person selector exists; a mother-tagged event must fail to resolve, never resolve as father.

**Why kārakas get admission power only for luminaries.** Saturn/Rāhu over natal Moon and Saturn over natal Sun are the standard classical signatures for mind and father, and the texts use the luminaries as frames (BPHS 7/32). Transits over natal Mercury or Rāhu are not settling/business doctrine; those planets act as agents and daśā lords. Density cost of K-B: ~40° of 360° per slow agent per point.

**CONDITIONS OF THE SEAL**
1. This table recorded in `decisions/NATIVE_DIRECT_RULINGS_20261005` as `ND-H-20261005` before any 5.0 window or score for these classes is read; later changes are new generations, never edits.
2. Astra P1-3 to P1-6 executed and independently verified (tier-aware P1/P3/P4 enumerators and verifier; `karaka_agent` row; K-B edges; 1.2.0 selected in `BOUND/SELECTED_PATH_REFS`; H pinned to generation; digests/inventories regenerated; negative controls), plus: DVI admits nothing in P1/P3; the 40% reversion is computed by the scorer.
3. §AM-H in `GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT`: cites UK as a kārakatva source, qualifies YJ 49–50, declares the tiers and roles; one oracle per class.
4. Admitted-day share reported per class and per path (P3 fast / P3 slow / P4 with and without DVI / K-B) beside coverage and rank; adverse budgets unchanged; a density failure is an agent/grain question for the engine, never a licence to re-pick houses.

**WHAT REMAINS THE OWNER'S OWN**
- K-B as a uniform contract also reaches bereavement (Sun): accept or carve out.
- Whether a kāraka running as MD/AD lord satisfies P1's natal-relationship prerequisite (a P1 relation-kind ruling, outside this packet).
- P3's fast-agent union makes every class dense regardless of H; agent/grain policy, if measurement confirms, is his.

**WHAT I DID NOT VERIFY**
Sanskrit of any cited line; UK translation is OCR'd; UK 12th-house items 1–13 and Mercury items past 29 unread; YJ edition/verse numbering and BPHS "32" (Astra P2-8) unresolved; the sign-bin shares are geometry, not measured days; no test, build or DB touched. The Jaimini PG34 "Moksha" hit concerns the Ātmakāraka, not Ketu — checked and not cited.
---
## ERRATA 1 — citations checked against the served corpus (appended 2026-10-05; append-only, no rule changed)
Source: Stream B verification, /Users/Dev/pravaha/run/G10_VERSE_VERIFICATION_20261005.md (110 quoted claims: 101 confirmed, 8 different, 1 not found). No rule in this record falls: scored use rests on the owner's rulings and the derivation step, not on any of the loci below. Corrections:
1. Uttara Kalamrita locators one chunk off: Mars '(81) House' is PG125:C1, not PG124:C1; Mercury '(19) Commerce' is PG125:C2, not PG125:C1.
2. Phaladipika 'XV.22 PG186 heaven' is XIV.22. (Father as the Sun's lagna, XV.22-24, PG197-198: confirmed.)
3. Phaladipika XXIII.13 'exact degree / full effects' is the CONTENTS-page wording; the verse body says 'traverses through so much of the distance in that house'. It must not be quoted as the verse; the near-miss rule's lower standing rests on the owner's ruling as a product convention, not on this verse.
4. Phaladipika II.1 gives the Sun as significator of 'father' only; 'bereavement' is not in the verse (cited meaning; the death application is a derivation, as already stated).
5. Jataka Parijata PG562 is VIII.64, a bhava-result verse, not a karaka verse: not to be cited for Rahu and deceit.
6. BPHS 15.14 is a conveyances verse, not property: not to be cited for property_acquisition.
7. Yavana Jataka yatra PG710 v.29 is an election rule and requires the malefic qualifier (benefics in the 12th do not produce expense or fraud).
8. BPHS PG111: gandanta confirmed; the served 'Sandhya' means twilight, so the classical-sandhi basis stands for gandanta only.
9. BPHS PG880:C2 holds only the last sentence (the pinda rule is in C1); Patel PG2516 is Uttara Kalamrita II.6 on retrograde strength.
10. BPHS ch.70 Sun-month: NOT FOUND in the served corpus; not to be cited.
Open point: whether the Yavana Jataka planet-by-house chapters reckon from the lagna or from the Moon is not settled by the text read; it must be settled before any such verse is used as a cited basis for a lagna-transit rule.
The implementation specification (FINAL_BUILD_SCOPE) carries the corrected loci and source kinds.
