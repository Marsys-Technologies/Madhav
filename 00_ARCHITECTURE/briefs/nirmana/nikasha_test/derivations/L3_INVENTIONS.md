# L3 INVENTIONS — TEST ARTEFACT (Phase 4, nikasha-test)

Flat register of every invention across L3_INSTANCE_SKELETON.md (A), KA_KALASUTRA_BRIEF_TEST.md (B),
KA_DASHA_KALA_BRIEF_TEST.md (C). Format:
`INVENTION | <file §section> | <what> | <template clause verbatim> | <proposed text>`
Census basis throughout: L3_sandbox_20260926.json (sandbox; no L3 prod census JSON exists).

INVENTION | A §0.1 | per-layer P-need / V-journey assignment (only P24/V13 anchored via DP08) | "List the P-needs and V-journeys for which this layer is **necessary**" (template §0.1) | add to data plane §13.3 item 1: a P/V-to-layer necessity table, one row per layer, sealed |
INVENTION | A §0.2 | "what it computes that existing software does not" | "Name what it computes that existing software does not, and what it hands the reasoning layer to read across." (template §0.2) | drop the external-comparison demand from the template, or supply a named comparison baseline per layer |
INVENTION | A §0.3 | seed + migration-pin reconciliation sources | "registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement" (template §0.3 measured_by) | extend asset_census.py to emit the seed and pin reads per layer |
INVENTION | A §0.3 | edge type per edge | "Receives from: upstream layers, by edge type, by DP contract." (template §0.3) | add `edge_type` to the registry schema and census output |
INVENTION | A §1.1 | production row counts via own count_sql (census is sandbox; live_rows null ×23) | "the production probe (asset_elevation_tracker.py --layer <L> --env-file)" (template §1.1 measured_by) | the L3 production census must exist (L3_prod_20260926.json missing — only its log) |
INVENTION | A §1.1 | floor and delta-per-floor per asset | "rows by the asset's own `count_sql` (the cockpit instrument), floor, delta" (tier-4 §1, inherited by §1.1) | census must emit floor and Δ per asset |
INVENTION | A §1.1 | shared-table multi-producer model — kala_gochara_windows produced by ka_gochara (CURRENT) and ka_gochara_sweep (RETIRED), each credited with the same 40,117 rows | "For each: target table(s) — a **set**, not one pointer, for multi-table assets" (template §1.1) | C-10/R06/R10 CONFIRMED for L3: registry needs producer partition keys; census must scope count_sql per producer |
INVENTION | A §2.1 | per-rule detectors, incl. the L3 switch rule | "**For each rule, the detector.** A rule with no detector is a wish." (template §2.1) | template §2.1 should name the detector per §8.1 row, at least by class (schema scan / writer-source scan) |
INVENTION | A §2.1 | L3-specific switch ON/OFF behaviour and storage separation | "The life-event switch: what this layer may do when ON, what it emits when OFF, and the storage separation that makes OFF a selection rather than a rebuild." (template §2.1) | data plane §9.2 must carry a per-layer switch table; L3's row absent from the tier summary |
INVENTION | A §2.2 | full set of §3.4 presentation rows L3 carries | "including which §3.4 presentation rows this layer carries and which fields it hands onward for them" (data plane §13.3 item 6) | §3.4's carriage mapping is row→DP-contract; add row→layer assignment |
INVENTION | A §2.2 / §5.4 | ownership of Presentation parity — [TRANSFERS] in tier 2 yet a layer acceptance test in tier 3 | "A [TRANSFERS] obligation is not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work." (tier 2 §1) vs "Presentation parity holds for the layer's served surface" (template §5.4 test 4) | resolve: either §5.4 test 4 reads "holds, where the layer is the owner" or §12.2's row loses [TRANSFERS] |
INVENTION | A §2.3 | per-contract fields/grain/identity and declared use per consumed input | "Every consumed input declares its use … **A citation with no declared use is not a contract.**" (template §2.3) | census must emit field-level producer/consumer verification, or §2.3 is unfalsifiable as specified |
INVENTION | A §2.4 | five-state coverage verdicts per obligation | "per obligation: applied / inapplicable-with-reason / unavailable / unqualified / unresolved — the five states, never a blank" (template §2.4 measured_by) | no instrument maps assets to these states; add a coverage census check per §5 obligation |
INVENTION | A §2.6 | which of the sixteen entity classes L3 emits/accepts | "Which of the sixteen entity classes this layer emits or accepts" (template §2.6) | census local_map_candidates = -1 (no detector); tier 2 §13.3 item 1a must pre-assign classes per layer |
INVENTION | A §2.7 + §4.4 row 13 | per-asset carriage check assignment | "**the relevant Jyotish concepts** the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)" (template §4.4) | C-9/R09 CONFIRMED for L3 (census: Carr.detector NO_DETECTOR on 23/23): §2.7 must assign a/b/c per asset, not per obligation |
INVENTION | A §2.5 | topological order + cross-layer gate state under a frozen definition revision | "cross-layer gates via egate.sql scoped to the CURRENT frozen definition revision" (template §2.5 measured_by) | no frozen L3 definition revision exists; the clause is unsatisfiable before the instance exists — circular |
INVENTION | A §4.4 row 7 | three-way baseline per asset | "State the three-way baseline per asset: **deployed** … **current code** … **target**" (template §4.1) | census reads no current code and no deployed production for L3; add a code-head read to the census |
INVENTION | A §4.4 row 8 | dispositions and must-add lists | "one of the data plane's eight dispositions, with the evidence from Part 1 that justifies it" (template §3.2) | expected: Part 3 is authored strategy; recorded because §4.4 promises the brief author inherits it, and a skeleton derivation cannot |
INVENTION | A §4.4 row 12 | preserved kernel per asset | "**the preserved kernel** — what of the asset must survive any rebuild unchanged (from 3.2)" (template §4.4) | no tier text or census field defines any kernel; needs a per-asset registry field or a §3.2 rule for deriving it |
INVENTION | B §0.1 r1 | P/V set beyond P24/V13 for ka_kalasutra | as A §0.1 | as A §0.1 |
INVENTION | B §0.1 r3 | switch behaviour + detector for ka_kalasutra | "The life-event switch: what this layer may do when ON, what it emits when OFF" (template §2.1) | as A §2.1 |
INVENTION | B §0.1 r4 | field-level presentation mapping | "which §3.4 presentation rows this layer carries and which fields it hands onward for them" (data plane §13.3 item 6) | as A §2.2 |
INVENTION | B §0.1 r5 | per-asset (not per-layer) contract production + declared use | "for each contract, the fields and grain actually present in the producer's table and actually read by the consumer — verified both ends" (template §2.3) | layer instance must carry a per-asset contract matrix; currently unspecified who assigns DP08 to ka_kalasutra vs ka_sangam |
INVENTION | B §0.1 r6 | five-state coverage verdicts | "the five states, never a blank" (template §2.4) | as A §2.4 |
INVENTION | B §0.1 r7 | topological position + three-way baseline | "State the three-way baseline per asset: deployed … current code … target" (template §4.1) | as A §4.4 row 7 |
INVENTION | B §0.1 r8 | disposition + must-add | "one of the data plane's eight dispositions, with the evidence from Part 1 that justifies it" (template §3.2) | as A §4.4 row 8 |
INVENTION | B §0.1 r10 | synergy seam membership | "the layer's synergy binding if one exists" (template §1.3 inherits) | no L3 seam list exists; the inherits clause itself presumes an artefact no tier produces |
INVENTION | B §0.1 r11 | consumer-verified evidence state | "verified at the consumer, not asserted by the producer" (template §1.4 measured_by) | census never queries consumers; add a consumer-side probe |
INVENTION | B §0.1 r12 | preserved kernel | "**the preserved kernel** … (from 3.2)" (template §4.4) | as A §4.4 row 12 |
INVENTION | B §0.1 r13 | concepts + carriage check (author chose D3) | "the domain detector each invites" (template §4.4) | C-9/R09 CONFIRMED (5th confirmation) |
INVENTION | B §1 | actual-consumer grep census | "code that actually reads it, writer-side and serving-side, grep population stated" (tier-4 §1) | census does not run it; required per brief |
INVENTION | B §4 Null row | any verdict for the Null gate | "**Null** honest null … an underivable value is emitted as null, not as a plausible default" (tier-4 §4) | the inspector runs no Null check — add it to asset_census.py |
INVENTION | B §5 | ledger gap rows (ids, owners) | "This section is those rows for this asset, in the ledger's own fields … rendered, never retyped" (tier-4 §5) | "rendered, never retyped" is unsatisfiable when the ledger holds no rows for the asset; clause needs a first-registration path |
INVENTION | B §6 | may_touch / must_not_touch globs | "may_touch:      <exact globs>" (tier-4 §6) | expected authored content; logged because no census field supports it |
INVENTION | C §0.1 r1 | P/V set beyond P24/V13 for ka_dasha_kala | as A §0.1 | as A §0.1 |
INVENTION | C §0.1 r3 | switch behaviour + detector for a service | "For each rule, the detector. A rule with no detector is a wish." (template §2.1) | as A §2.1 |
INVENTION | C §0.1 r4 | service output fields carrying the temporal presentation row | "which §3.4 presentation rows this layer carries and which fields it hands onward for them" (data plane §13.3 item 6) | as A §2.2, plus: define "field" for a service |
INVENTION | C §0.1 r5 | how a service "produces" a DP contract | "Two tables: DP contracts this layer **produces** (consumer, fields, grain, identity, generation)" (template §2.3) | the row shape presumes a table; add a service contract shape |
INVENTION | C §0.1 r6 | five-state coverage verdicts | "the five states, never a blank" (template §2.4) | as A §2.4 |
INVENTION | C §0.1 r7 | topological position + baseline | "State the three-way baseline per asset" (template §4.1) | as A §4.4 row 7 |
INVENTION | C §0.1 r8 | disposition + must-add | "one of the data plane's eight dispositions" (template §3.2) | as A §4.4 row 8 |
INVENTION | C §0.1 r9 | what "ablate one" means for a table-less service | "the reading with it against the reading without it" (template §1.2) | define the removal procedure for a service (deregister? fence endpoint?) |
INVENTION | C §0.1 r11 | consumer-verified evidence state | "verified at the consumer, not asserted by the producer" (template §1.4) | as B r11 |
INVENTION | C §0.1 r12 | preserved kernel of a service (behaviour, not rows) | "**the preserved kernel** … (from 3.2)" (template §4.4) | as A §4.4 row 12, plus a service-kernel definition |
INVENTION | C §0.1 r13 | concepts + carriage check (author chose D3) | "the domain detector each invites" (template §4.4) | C-9/R09 CONFIRMED (6th confirmation) |
INVENTION | C §1 | service descriptor (endpoint, signature) the word "service" must carry | "or 'service'" (tier-4 §1 producer bullet) | tier-4 §1 names the kind and specifies nothing it must disclose |
INVENTION | C §1.1 | completeness question for a row-less asset | "a census against a DECLARED universe" (tier-4 §1.1) | undefined for services; pilot 4's N/A convention was also invented there |
INVENTION | C §4 Vocab row | vocabulary test for a service's output | "one canonical id per thing, one closed alias set" (tier-4 §4 Vocab row) | gate is table-oriented; no service output-vocabulary check exists |
INVENTION | C §5 | ledger gap rows (ids, owners) | "rendered, never retyped" (tier-4 §5) | as B §5 |

COUNT: 49 invention rows.
