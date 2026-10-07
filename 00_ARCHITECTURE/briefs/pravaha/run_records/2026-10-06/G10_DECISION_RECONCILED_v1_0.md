# G10 eight classes without cited houses — reconciled decision (strategy session, 2026-10-05)
Status: RECONCILED RECOMMENDATION for the owner to ratify; not yet ruled. Inputs: owner Ruling 10 (RULING10.txt); Fable 5.1 memo (G10_DECISION_FABLE_v1_0.md: houses, karakas, loci); Astra review at high effort, ACCEPT_WITH_AMENDMENTS (G10_DECISION_ASTRA_REVIEW_v1_0.md). Astra had no access to the classical-text store: quotations rest on Fable's corpus reading and are unverified by the reviewer.

## Reconciled table (Astra's narrow sets adopted; Fable's wider members become supporting, annotate-only)
| class | scored H (opens windows) | supporting (annotate only) | karakas | note |
|---|---|---|---|---|
| achievement_recognition | 10 | 11; 5 only for an intellectual/creative subtype | Sun; Jupiter supporting | |
| business_launch | 7, 10 | — | Mercury (practice) | neither house separates launch from ongoing business |
| financial_deception | 2, 12 | 6 (adversary); 8 conditional | Rahu (practice); Saturn NOT as deception significator | Fable's {12,6,8} read as generic adversity and omitted the wealth house |
| foreign_settlement | 12 | 4 (home), 9 (journey); 7/10 only with stated context | Rahu (practice); Saturn conditional (exile) | travel is not settlement |
| parental_event | father: 9 and 2 (offsets 1, 6 from the 9th) | 8, 12 from the parent's house conditional | Sun (father); Moon (mother) | father-only execution now; mother (4, 9; Moon) reported unsupported until a per-person selector exists |
| property_acquisition | 4 | 11 (gain), 2 (funding) | Mars (derived step) | |
| psychological_arc | 4 | 5 (cognition), 8 (distress) for defined subtypes | Moon; Mercury supporting | |
| spiritual_turn | 9, 5 | 12 (renunciation/moksha, practice) | Jupiter; Ketu (practice); Saturn only for an austerity condition | |

## Why narrower than Fable (Astra P1-2)
Windows open on ANY qualifying house or lord contact. Fable's sets let Jupiter touch a signature house from 8-10 of the 12 sign positions and Saturn from 6-11 of 12, before lords are added: the same always-open failure as 3.0 (22 classes open 99.87% of days). The adverse-class budget for financial deception and parental events is 2.61% of days each and must not be relaxed.

## Corrections to Fable's grading and claims (Astra P1-1, P1-7, P2)
- A verse that supports a house's MEANING is K1 for the meaning only; the step to an EVENT rule (and from Moon- or dasha-relative statements to a lagna transit rule) is a derivation, K3. 'Every class has at least two K1 houses' is NOT established. So nothing scores automatically: the owner authorises the derived rules for scored use (provenance uncited_extension/scored by ruling), exactly the footing of the double-transit ruling.
- Citation forms: Phaladipika I.12-16, II.1-7 and BPHS 11/15/24 plausible; several BPHS locators and all Yavana Jataka chapter numbers cannot be judged without edition, headings and full conditions; BPHS '32' verse unconfirmed. To be resolved or carried explicitly as derived/practice premises before adoption.
- psychological_arc and spiritual_turn currently get NO edges from path P2; 'all eight become P1-P4 computed' was overstated.

## Implementation facts the operating steward needs (Astra P1-3 to P1-6) — this is NOT registry data only
- signature_houses() reads only house sets and anchors; enumerate_p3_edges() hardcodes verse_cited/scored. A 'testimony' house placed inside H would still open windows: supporting houses stay OUTSIDE scored H until member-level roles exist and are verified through P1, P3, P4.
- _karaka_row() requires a locator and hardcodes phaladeepika/verse_cited; KARAKA_SETS has no production consumer: karakas need an honest representation AND a defined effect before they recover anything.
- _CLASS_AFFECTED_PERSON holds only bereavement->father; signature_houses() has no person argument; P2 emits adverse rows as affected_person native from the native's Moon: must not be presented as evidence of a parent's illness.
- BOUND_PATH_REFS/SELECTED_PATH_REFS default to 1.0.0: adding rows does not select them; H/karaka dictionaries are unversioned globals: pin content to the generation; update the independent verifier's own tables; regenerate identity, bindings, digests, inventories.
- Negative controls: testimony changes no admission or rank; mother never resolves as father; native Moon never establishes parental illness; unrelated gains never pass as property acquisition.
- Freeze the revised rules BEFORE reading candidate outcomes; report admitted-day share and false positives beside coverage and rank.

## Ratification list for the owner (ruling id proposed ND-H-20261005)
1. Adopt the scored houses in the table above for the eight classes, as derived rules authorised for scored use by this ruling, in the next generation.
2. Supporting houses annotate only; the 12th for spiritual_turn is retained as a practice-based association with no power to open a window.
3. Mercury for business; Rahu for financial deception and foreign settlement: practice-based significators, with a defined tested effect and no window-opening power of their own.
4. Jupiter and Ketu for spiritual turns; Saturn only under an explicit austerity/dispassion condition; Saturn not a deception significator.
5. Parental events: father only for now (houses 9 and 2, Sun); mother reported as unsupported until built.
6. Authorise the needed specification and code amendment (honest provenance, member-level roles, karaka effect, per-person selection, version binding, independent verification).
7. Rules frozen before any 5.0 outcome for these classes is read; admission density reported with the score.
