VERDICT: ACCEPT_WITH_AMENDMENTS

1. **P1 — Make a standalone lower-dignity window part of phase 1.**

   The owner chose inclusion and explicitly described “the dignity of that window that opens up” (`RULING10.txt:2`). Separate identity and storage honour that direction. **Annotations that can appear only beside existing contact windows would under-deliver it.**

   The memo is ambiguous: it describes a separate near-miss window, then says “Open a window alone? Phase 1 no,” and leaves standalone timeline rows optional (`G11_DECISION_FABLE_v1_0.md:18,44–46`).

   My judgement: **zero evaluation weight can be faithful; zero independent product presence is not.** Require a near-miss to open its own clearly labelled tentative opportunity interval, including when no contact window exists. Give it categorical dignity below a contact. Keep its geometry and explanation visible, while excluding it structurally from scored candidates, rankings and admission.

   That is the strongest immediate alternative that cannot inflate evaluation results by construction. The ruling does not specify a numerical weight, so a positive scoring coefficient should not be inferred.

2. **P1 — Separate contact, proved near-miss and unresolved geometry consistently.**

   The memo simultaneously calls `d_min < 0.005°` a contact and calls the interval between 1″ and 18″ unresolved (`memo:12`). These overlap. A positive closest approach of 0.002° is not an exact tangency merely because it falls below a safety threshold.

   Actual tangency—a zero attained at a station—is contact geometry in the code: endpoint roots are accepted (`gochara_kernel/contacts.py:78–88`). But support handling remains problematic: seam deduplication can discard a station-side candidate (`contacts.py:290–333`), consistent with the options note’s documented defect (`.brief/G11_GRAZE_CONTACT_OPTIONS_v1_0.md:60–68`).

   Amend the definition to:
   - contact: a verified exact root, including tangency;
   - near-miss: a complete rootless stretch with certified positive clearance;
   - unresolved: neither classification is established at the declared accuracy.

   The locally available `pr3143` code refuses graze classification below its threshold; it **does not turn such cases into contacts** (`pr3143:gochara_kernel/contact_certify.py:154–162`).

3. **P1 — Remove “exactly one reversal” from the general definition.**

   For a smooth, complete, rootless passage through a fixed band, entry and exit must occur on the same side of the target; an interior minimum therefore exists. **No station inside an observed clipped segment is possible, but that segment alone does not establish a complete near-miss.**

   “Exactly one” requires an additional body/domain/orb guarantee. The supplied list supports one station for its 24 reported grazes; it does not prove the claim for every permitted target and horizon. The generic kernel explicitly preserves close station pairs and merges adjacent in-band pieces across segments (`gochara_kernel/arcs.py:212–239`; `episodes.py:149–187`). A multiple-reversal stretch needs all extrema considered. A simple complete rootless stretch normally has an odd number of reversals; a two-station segment may instead be clipped or contain a contact.

   The body distinctions matter:
   - Mercury through Saturn: the single-station assumption may hold for the pinned one-degree cases, but no full-domain minimum-excursion proof is supplied.
   - Sun, Moon and the pinned **mean** nodes are stationless for this purpose; ordinary complete passages cross the target. Their clipped pieces must not become near-misses merely for lacking an observed root.
   - True-node behaviour is outside the current convention: contact geometry explicitly uses `MEAN_NODE` (`gochara_kernel/knots.py:14–17,169–173`).
   - Moon events are excluded from the global station substrate (`substrate.py:245–247,470–474`).

   Define the entity by a maximal rootless stretch, derive the global minimum over all extrema, and either support multiple station references or explicitly reject unsupported geometry with a named unresolved state.

4. **P1 — “Already Swiss-refined” is not established by the cited implementation.**

   This is a concrete factual error in `memo:12`.

   `build_arc_index` finds station times from roots of the **spline derivative** (`gochara_kernel/arcs.py:212–239,260–267`). The substrate then reads `index.stations`, evaluates the spline longitude, and stores those values with the literal label `swiss_refined` and `delta_t=1e-9`; the station loop performs no Swiss refinement (`substrate.py:527–545`).

   The label therefore cannot justify the proposed closest-approach accuracy. Require direct ephemeris refinement of the station/minimum and an independently checked uncertainty before using it for classification or certification. Merely comparing longitudes near a flat extremum also does not uniquely establish the station time.

5. **P1 — Complete the identity contract, especially the relationship-record key.**

   Separate near-miss ordinals protect contact ordinals, but the proposed hash is not sufficient by itself (`memo:9`).

   - **Relationship-record collision:** existing natural keys contain `contact_id`, but no `near_miss_id` (`gochara_kernel/evaluator.py:133–166`; `gochara_rules/records.py:30–34`). Two near-misses of the same object/class/role/path would otherwise have the same key with `contact_id=NULL`. Add a kind-qualified occurrence reference to the key, preserving existing contact serialization.
   - **Ordinal stability is conditional:** `substrate.py:142–163` sorts and enumerates the supplied set. It does not maintain an append-only registry. Adding a previously missed earlier occurrence renumbers later entries unless corrected under a new identity regime.
   - **Horizon versus domain:** extending a reporting horizon inside an unchanged, fully solved domain can preserve IDs. Changing either convention-domain endpoint changes the convention hash and therefore physical/contact IDs (`substrate.py:168–198`).
   - **Orb changes:** pin canonical orb serialization and namespace the ordinal set by that orb/policy. If the new identity table literally mirrors 1153’s uniqueness on `(physical_object_id, occurrence_ordinal)`, different orb-specific IDs can conflict unless their physical-object convention also changes (`1153_gochara_sky_event_substrate.sql:813–826`).
   - **NULL nearest instant:** the memo orders identities by `t_nearest` but permits it to be NULL at the domain edge. It needs an explicit provisional/boundary identity policy; “as N3 contacts” does not supply one for rootless stretches.

   Preserve collision detection, correction/supersession rules, and deterministic ordering across aspect rays. A hash collision is unlikely; semantic aliasing and renumbering are the immediate hazards.

6. **P1 — The migration requires more than replacing the transit/natal CHECK.**

   The coherent rule is: transit rows reference exactly one permitted geometric occurrence and carry precision; natal rows reference neither and carry no precision. Near-misses should initially be limited to the proposed point conjunction/aspect geometry, not silently include residence.

   The existing CHECK has both transit and natal branches (`1155_gochara_relationship_record.sql:575–581`). More importantly, its coverage trigger chooses the transit validation branch solely through `NEW.contact_id IS NOT NULL` (`1155:717–764`). A near-miss with NULL contact ID would otherwise bypass transit relation-search checks, convention bridging and precision restatement.

   Required additions include:
   - a composite FK binding near-miss ownership, body, relation and object to the record;
   - near-miss coverage and precision validation;
   - updated Python record validation, which currently rejects transit rows without a contact (`gochara_rules/records.py:72–76`);
   - explicit complete/truncated field combinations and finite numeric checks;
   - enforcement that a referenced sky event is a station of the same body/convention and is the relevant extremum.

   A plain FK to `event_id` does not establish the latter conditions. Cross-table assertions require suitable composite FKs or triggers.

7. **P1 — Extend the sealed-generation machinery to cover the new entities.**

   The proposed testimony CHECK does not protect near-miss geometry against mutation or make it part of a verified seal.

   Migration 1240 explicitly hashes records and contacts into the window derivation input, with a matching Python implementation (`1240_gochara_window_verification_gate.sql:307–366`; `gochara_kernel/window_gate.py:135–190`). Its seal-state digest enumerates a fixed table list that excludes the proposed tables (`1240:655–675`).

   Before sealing, require:
   - chart-lock ordering and sealed INSERT/UPDATE/DELETE/TRUNCATE guards for the new ledger;
   - immutable global identities;
   - near-miss links, geometry and verification results in the relevant versioned digests;
   - builder/verifier/serving permissions and implementation-digest registration;
   - stale-verification rejection after any relevant mutation;
   - a verified-empty result when the expected near-miss set is empty, and refusal for missing, extra, unresolved or reported-but-unstored stretches.

   Existing records are already frozen at sealing; near-misses cannot simply be attached afterwards (`1155:409–455`). Migration 1240 also closes older contact/precision enrichment exceptions for its sealing regime (`1240:940–988`).

8. **P1 — Phase 1 can preserve scored results; phase 2 is not inflation-proof.**

   The phase-1 exclusion is real: `window_sweep.py:759–768` excludes testimony before constructing members. Migration 1240 independently expects only admitted, scored members and rejects extras (`1240:535–578`).

   Thus unchanged evaluation follows **if the scored extract, coverage inputs and scoring policy remain identical**. It is a design consequence to test, not an already demonstrated result. Include the protocol’s fifth endpoint, **T-honesty**, in that comparison (`.brief/EVALUATION_PROTOCOL_v2_3.md:207–219`).

   The phase-2 claim in `memo:26` is overstated:
   - extending windows can turn misses into hits;
   - bridging two windows merges candidates and changes ranking denominators;
   - extension into another year can change that year’s candidate set;
   - P4 uses the intersection of Jupiter and Saturn supports, so adding a near-miss can create an intersection that no contact-only window previously had (`window_sweep.py:713–717,791–802`).

   A small weight does not constrain admitted duration. “Contains at least one contact-rooted member” is insufficient protection.

   Also, overlap counts and Δ day-fraction do not supply the specified **Δ-median-rank** promotion evidence (`.brief/GOCHARA_DESIGN_SPECS_v1_4.md:409–414`). Keep diagnostics in a separate artifact: EP’s cited `diagnostic_only` clause concerns void rank medians, not unrestricted new annotation blocks (`EP:185–188,244–250`). Do not tune coefficients on events the protocol defines as held out from calibration (`EP:294–300`).

9. **P2 — R2 is plausible, but “R1 keeps about 2 of 24” is only a narrow calculation.**

   My reading: **R1 is more literal linguistically; R2 is more plausible operationally in the context of choosing inclusion and a lower-dignity window.** R2 should be presented as the reconciled interpretation, not as something the quotation conclusively establishes.

   I independently parsed the supplied list:
   - 24 graze rows;
   - exactly two target longitudes within 1° of a sign boundary, both natal Mercury at 270.838758… (`GRAZE_REAL_CHART_COUNT_20261005.txt:32,45`);
   - no listed graze target within 1° of a nakshatra boundary;
   - **four additional aspect-ray levels** within 1° of a nakshatra boundary: 79.173° twice, 147.055°, and 267.055° (`list:12,21,24,42`).

   Consequently, a target-only spatial interpretation gives two; a ray-level spatial interpretation gives six when sign and nakshatra proximity are combined. Neither establishes proximity of the **actual station** to the junction. Dasha-junction times and junction tolerances are absent entirely.

   Remove the unqualified “2 of 24” consequence from the owner question.

10. **P2 — Separate tables are a sound choice, but two arguments for them overclaim.**

    The cited constraint family and ordinal FK are real (`1153_gochara_sky_event_substrate.sql:1062–1067,1085–1102`). An unchanged contact schema cannot honestly accommodate complete rootless near-misses. Separate tables minimise disturbance.

    However, a discriminated schema with kind-qualified identities and conditional constraints is not inherently unsafe. It would require a broader redesign. The irreversible mistake is **mixing occurrence orderings or changing published meanings**, not the mere existence of a kind column.

    The assertion that the current certifier would necessarily call a stored graze “invented” is also incorrect. It reconstructs **in-orb intervals** and compares their union; its ledger query does not read `t_exact` (`gochara_kernel/contact_certify.py:58–61,65–95,119–125`). A graze-shaped row matching that geometry is not intrinsically rejected as invented. Contact/near-miss classification must be an explicit new verification responsibility.

11. **P2 — Correct the remaining specification and branch claims.**

    - “Every uncited practice element” must start as testimony is too broad. The frozen specification permits scored uncited extensions when a native ruling grants scoring; the explicit promotion restriction names particular operators (`.brief/GOCHARA_DESIGN_SPECS_v1_4.md:57–67,409–414`).
    - The specification permits `uncalibrated_default` category mappings under stated restrictions. “Calibrated only” is a proposed stricter policy, not what the cited lines require (`spec:173–178`). An invented empirical claim and a transparently authorised engineering default are different.
    - Equal angular kernel values do not imply equal overall dignity. Geometry and interpretive status can remain separate. Calling `1−d/orb` “proximity” would avoid suggesting calibrated strength (`gochara_rules/kernel_factor.py:123–134`).
    - The frozen text specifically forbids **rounded** time hashing; it does not categorically forbid every timestamp-based identity (`spec:618–621`). AM-25’s full-precision timestamp remains refinement-sensitive, but the memo’s citation overstates the prohibition.
    - Contrary to the supplied checkout description, a local `pr3143` ref exists at `bd9dc966d40f850e6718b1e2f94d59c65cb2a45d`. I inspected its cited certifier through `git show`. It follows stretches **outside the builder’s domain**, whereas the memo limits its decision to that domain (`pr3143:contact_certify.py:136–140`). Resolve this explicitly.
    - That branch’s reported minimum is selected from approximately hourly samples (`pr3143:contact_certify.py:146–165`). Its no-crossing proof does not independently certify the reported minimum or station accuracy.

12. **P2 — Treat the estimate as a coding subtotal; specify the complete pre-seal acceptance work.**

    Two builder days plus one-to-two checker days may be a preliminary implementation estimate. It is not a supported estimate for adoption and sealing (`memo:30–35`).

    Missing work includes record-key/model changes, independent record derivation, coverage and precision triggers, permissions, digest compatibility, candidate cleanup/rebuild behaviour, standalone serving, and end-to-end evaluation isolation.

    Before the seal, require tests covering multiple extrema, clipping at both horizon and domain boundaries, near-zero ambiguity, true tangency, wrap seams, stationless bodies, multiple aspect rays, repeated near-miss records, orb/domain changes, omitted and invented rows, sealed mutations, and exact contact-ID preservation. Compare scored outputs with the near-miss layer present and absent; compare near-miss completeness separately.

    The real-list fixtures are useful, but their printed dates are interval boundaries—not verified `t_nearest` values (`list:22–23,45`). A wider unsealed reporting run may measure cost; it must not substitute for the completed build and verification required before sealing.

## RECONCILED RECOMMENDATION

- Store `near_miss` separately, with its own occurrence identity, orb/policy namespace and relationship-record key; preserve existing contact identity bytes.
- Adopt R2 provisionally and open standalone tentative near-miss windows from phase 1, categorically below contacts, with visible geometry and no claimed calibrated strength.
- Keep those windows structurally outside evaluation inputs. Any later scored use requires a separately versioned, preregistered promotion decision and full endpoint checks.
- Define near-misses by certified complete rootless stretches, considering all extrema; retain unresolved states and directly refine nearest approaches.
- Seal only after the storage, serving, identity, independent verification, permissions, mutation guards and digest contracts are complete and tested.

## What I did not verify

Reviewed checkout HEAD `9080c0fe1660898b0f08b5814c7876f1e21a0bcd` and the cited local `pr3143` certifier. File locators above refer to kernel/rules directories under `platform/python-sidecar/services/`, migrations under `platform/migrations/`, and the supplied `.brief` documents.

I did **not** run tests, ephemeris recomputation, database queries or network requests; verify applied migrations, live grants, publication state, migration-number availability, the protected-table inventory, the extended-horizon count, or classical textual claims. The count checks were arithmetic over the supplied list. No files were modified.

