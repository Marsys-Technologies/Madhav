# G11 near-misses — reconciled decision (strategy session, 2026-10-05)
Status: RECONCILED RECOMMENDATION for the owner to close; not yet ruled. Inputs: owner Ruling 10 (RULING10.txt); Fable 5.1 memo (G11_DECISION_FABLE_v1_0.md); Astra review at high effort, ACCEPT_WITH_AMENDMENTS (G11_DECISION_ASTRA_REVIEW_v1_0.md). Where they differ, the Astra amendments below are adopted.

## The decision
1. A near-miss is its OWN kind (`near_miss`), stored in its own tables with its own occurrence identity, orb/policy namespace and its own key in the relationship record. Existing contact identities and rows do not change by one byte.
2. From the first release a near-miss OPENS ITS OWN WINDOW: a clearly labelled, tentative, lower-dignity interval that appears even where no contact window exists. Its geometry (entry, closest approach, exit) is visible. The number 1 - d/orb is called proximity, not strength. (Astra P1-1: Fable's 'opens nothing in phase 1' under-delivers the owner's words 'the window that opens up'.)
3. Those windows are structurally OUTSIDE the evaluation: not candidates, not ranked, not admitted. No scored figure may move; proven by running the scorer with the near-miss layer present and absent, including the T-honesty endpoint.
4. Any later scored use is a separate, versioned, pre-registered promotion decision with full endpoint checks. Fable's 'support-only cannot inflate' claim is withdrawn (Astra P1-8: extension can turn misses into hits, bridge windows, and create P4 intersections).
5. Reading of 'sandhi': R2 adopted provisionally (a near-miss is itself the in-between state); the stored name is near_miss, 'sandhi' stays the owner's description. The owner is asked to confirm. The '2 of 24 under R1' figure is withdrawn: it is 2 by target-near-a-sign-boundary, 6 if aspect-ray levels near a sign or nakshatra boundary are counted, and dasha junctions were not computed.

## Binding amendments for the implementers (Astra, all P1 unless marked)
- Definition in three states: CONTACT = a verified exact root, tangency included; NEAR-MISS = a complete rootless stretch with certified positive clearance; UNRESOLVED = neither established at the declared accuracy (named refusal). No threshold turns a small positive distance into a contact.
- Do not assume exactly one reversal: define by the maximal rootless stretch and take the global minimum over ALL extrema; stationless bodies (Sun, Moon, mean nodes) and clipped pieces must never become near-misses for lack of an observed root.
- Closest approach must be refined directly on the ephemeris with an independently checked uncertainty; the stored station rows are spline-derivative roots labelled swiss_refined with delta_t 1e-9 and no Swiss refinement (substrate.py:527-545) — a labelling defect to fix in its own right.
- Identity: add a kind-qualified occurrence reference to the relationship-record natural key; state the rules for ordinal stability when an earlier occurrence is added, for horizon versus convention-domain changes, for orb changes, and for a NULL nearest instant at the domain edge.
- Migration: more than the transit/natal CHECK — the coverage trigger branches on contact_id IS NOT NULL (1155:717-764); composite FKs, near-miss coverage and precision validation, Python record validation (records.py:72-76), station-is-the-extremum enforcement.
- Sealing: chart-lock ordering and sealed-mutation guards for the new tables, their inclusion in the versioned digests and the seal-state table list (1240:307-366, 655-675), permissions, stale-verification rejection, a verified-empty result, refusal on missing/extra/unresolved/reported-but-unstored stretches.
- P2: separate tables are the right choice (minimum disturbance), not because a kind column is inherently unsafe; the certifier would not by itself reject a graze-shaped contact row, so classification is an explicit new verification duty; resolve inside-domain versus beyond-domain stretch following (PR 3143 follows beyond).
- P2: the estimate (about a week) is a coding subtotal; the pre-seal test list in the Astra review item 12 is the acceptance list.

## Sequencing
May follow the small test and an unsealed full build (near-misses reported, not stored). Must be complete before the FINAL sealed build; the storage change goes in the second protected window.

## Questions for the owner to close it
1. Confirm the reading: a near-miss is itself the in-between (sandhi) state — or did you mean only near-misses that fall at a junction of signs, nakshatras or periods?
2. Confirm: it opens its own lower-dignity window from day one, shown and labelled, carrying no weight in scoring until separately promoted on evidence.
