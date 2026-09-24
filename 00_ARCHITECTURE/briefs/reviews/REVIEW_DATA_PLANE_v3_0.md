---
artifact: REVIEW_DATA_PLANE_v3_0
reviewed: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v3_0.md (commit 45a4f7f9c)
parent: 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md
predecessor_for_cleanse_check_only: MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md
produced_on: 2026-09-24
mode: independent, read-only, fresh context
verdict: REJECT
---

# Review: Data Plane Value Architecture v3.0

**Verdict: REJECT.** Two blockers, both small to fix: the document asserts its P-citations are current and four of them are not (a layer plan derived from V05 would serve "read the texts" instead of "method selection"), and §12.1 still enforces the medical/mortality exclusion the parent removed and P23 reverses. The realignment is otherwise sound; the additions (§3.4, V12, V13, switch, ablation, learning output) are right in substance. Once findings 1–3 land the document is adoptable; the MAJORs are where the derivation would otherwise have to invent.

Line numbers are the file's own.

## Findings

**1. BLOCKER — §12.1 L452 re-imposes the removed exclusion and contradicts P23.**
Text: "Excluded medical/mortality requests must remain excluded through every intermediary."
Parent P23 puts āyurdāya in scope; the parent's 3.1 changelog removed "the death, illness and fertility exclusions"; this document's own V12 (L88) serves them. A layer plan reading §12.1 as the proving portfolio would gate lifespan at every intermediary.
Replace with: "An āyurdāya request is answered as V12 requires — method, inputs, cancellations, disagreement, uncertainty — through every intermediary; never a bare date."

**2. BLOCKER — §2 P-citations are wrong under FINAL numbering while L73 asserts they are current.**
Text (L73): "Any V-journey citation of P20–P24 in v2.0 referred to the old numbering; the citations below are current."
Under FINAL: P20 = method selection, P21 = day/period, P22 = texts, P23 = lifespan, P24 = present-tense. Four rows still carry v3.0-era numbers:
- L81 `V05 Calendar, action and method selection | P11, P21–22` — P22 is texts; method selection (P20) is missing from the row named for it. Replace with `P11, P20–21`.
- L82 `V06 Honest history and forecast review | P12, P20` — old P20 (observation briefs) was removed; new P20 is method selection. Replace with `P12`.
- L84 `V08 Source learning and scholarly depth | P15, P23` — P23 is now lifespan. Replace with `P15, P22`.
- L86 `V10 Continuing and portable understanding | P12–13, P19–20; master §§5–6,10` — same P20 error. Replace with `P12–13, P19; master §§5–6,10`.
Also L71–72: "They were remapped at v3.0: the product definition removed its old P20 at v3.1" mixes this document's version with the parent's. Replace the two sentences with: "Citations follow the parent's FINAL numbering (see its `p_identifier_note`)."

**3. MAJOR — §1.2 L67 names the superseded parent as governing.**
Text: "The [Product Definition v3.0](../../MADHAV_PRODUCT_DEFINITION_v3_0.md) governs the target."
Frontmatter L7 says FINAL. Replace with: "The [Product Definition FINAL](../../MADHAV_PRODUCT_DEFINITION_FINAL.md) governs the target."

**4. MAJOR — §3.4 mapping is checkable in shape but three rows point at contracts that do not carry what the row claims, and the temporal half is absent.**
(a) L151 row: "The prerequisites actually tested and the exceptions actually checked, including those that passed silently | DP02, DP05 formation ledger". DP05 (L304) carries "Formation, participants, partial/failing clauses and cancellation" — failing clauses only. Passed clauses are exactly what the acharya rendering needs and DP05 does not hand them onward. Amend DP05 to: "Formation, participants, every clause tested with its result (passed, partial, failed) and cancellation; hydrate actual configuration before timing."
(b) L150 row maps "where authorities disagree" to DP02, but DP02 (L301) reads "Exact rule clauses, method, prerequisites, exceptions and executable scope". Amend DP02 to: "Exact rule clauses, method, school/tradition, prerequisites, exceptions, disputed readings and executable scope; invocation is not application."
(c) L155 row: "The competing readings and which classical authority each rests on | DP06 structural relationship, DP17 controlled comparison". DP17 (L317) is "Real changed computation/application" — a second run. Competing readings within one analysis are DP06's "variants and ancestry" resting on DP02's witnesses. Replace the cell with `DP06, DP02`.
(d) The table stops at structure. A timing or manifestation finding rendered for the acharya needs the geometry, the activation rule, the named criterion and the bridge/falsifier. Add one row: "The clock geometry, activation rule and named criterion behind a window; the bridge and falsifier behind a manifestation | DP07, DP08, DP09".
With (a)–(d) the contract is a real data obligation: each row names a field a layer plan must bind under §13.3 item 6.

**5. MAJOR — §3.4's acceptance test (L163–164) has no test row in §12.2 and no binding in §13.3.**
Parent §14 Delivery fidelity now requires "both presentation modes". §12.2's table has "Delivery sentinel" but nothing that measures the two-mode promise. Add a §12.2 row: "Presentation parity | Both renderings produced from the consumed reading package (§11) without recomputation; same finding identity, confidence and uncertainty; every §3.4 row present in the acharya rendering and openable from the plain-language one." And in §13.3 item 6 append: "including which §3.4 rows this layer carries."
Also replace "one stored analysis" (L164) with "the consumed reading package (§11)" so the test names an object the document already defines.

**6. MAJOR — P24 has a V-row and nothing beneath it.**
V13 (L89) requires "the active-clock set, its participants and the preceding interval for contrast". No §5 row, no §6.4 sentence and no DP carries the present or preceding interval, and "what each is doing" straddles L3 (activation) and L4 (expression) without assignment. A Kāla plan must invent it (see derivability test). Add to DP08 (L307): "...alternate routes, horizon, and for the present-tense need the interval now active and the one preceding it." Add to §6.4 after L262: "The present interval is served from the same mechanisms: the active clock set, its engaged participants and the preceding interval for contrast; what each mechanism is doing is L3's activation state, what it may mean is L4's."

**7. MAJOR — Parent §3.3 narration-vs-arithmetic verification has no data obligation here.**
Parent: "Narration of a number requires semantic verification separate from arithmetic verification". The only echo is L408 "narration rule is replaced". Append to §12.2 Numeric/context (L466): "; the sentence that grades or labels a figure is verified separately from the figure."

**8. MAJOR — Parent §7.3 chronology-reset leak is absent.**
Parent: "A rebuild must not reset chronology: re-stamping emission time turns a frozen claim into a hindsight leak." §9.3 covers the observation side only (L389 `recorded_at`). Append to DP15a (L314): "A rebuild never re-stamps an issued claim's emission time."

**9. MAJOR — The switch rewrite dropped the one data obligation the switch depends on.**
v2.0 L319 carried "keep event-conditioned overlays separate from event-free structural/temporal products". §9.2 keeps the presentation rule ("must never be presented as event-free chart structure") but not the storage rule. Without it OFF is a rebuild, not a selection, and a reading cannot honestly carry its switch state. Add after L376: "Event-free structural and temporal products are materialized independently of any event-conditioned overlay, so OFF is a selection over stored products, not a rebuild, and ON adds overlays without rewriting them."

**10. MAJOR — §13.3's asset-brief sentence omits what the parent §16 requires of every asset brief.**
Parent: "Every layer and asset brief states: the P-needs (§2) it serves and the §14 obligations it is scored on ... and its manifestation or temporal role." L520 lists "actual tables/services/columns, current algorithm and consumers, preserved kernels/tests, exact delta and expected semantic difference". Replace with: "Each **asset brief** then supplies the P-needs and obligations it inherits from its layer plan, its manifestation or temporal role, actual tables/services/columns, current algorithm and consumers, preserved kernels/tests, exact delta and expected semantic difference."

**11. MAJOR — Orphans of the removed compliance regime and observation briefs.**
- L313 DP14 title "Historical comparison and voluntary observation brief" and "...voluntary burden and exposure." → title "DP14 Historical comparison"; drop "voluntary burden and".
- L315 DP15b "C3 never enters provider synthesis." → "admitted outcomes never enter provider synthesis."
- L387 "excluded from prediction detection under PPR-19." → "excluded from prediction detection."
- L450 "Route protected C3 adjudication separately from provider-facing historical explanation." → "Route adjudication separately from provider-facing historical explanation."
- L494 W08 "voluntary discriminating observation brief and" → delete.
- L527 "with product v3.0's exact C1/C3/PPR-31 separation" → "with the parent's switch and §8.1 correctness rules".

**12. MINOR — `permitted` and `exclusions` left without referent** (the changelog claims this was done). L224 "Qualified permitted guidance only ... Horizon qualification cannot bypass exclusions." → "Attributed guidance only; source testimony is not demonstrated remedial efficacy." L272 "specific permitted forecast is earned" → "specific forecast is earned". L446 "emits a permitted forecast only when earned" → "emits a forecast only when earned". L313 "permitted comparison" → "comparison". L450 "a permitted event-free" → "an event-free". L531 "permitted non-natal horizons" → "non-natal horizons".

**13. MINOR — `purpose` survives the removal of the purpose paths without a definition.** L375–376: "the minimum complete purpose-qualified projection when the switch is ON." Replace "purpose-qualified" with "projection its declared use (retrospective comparison or protected evaluation) requires". Same word at L418, L432; acceptable once defined here.

**14. MINOR — Research residue.** L87 "or automatic cohort admission" → delete. L284 "belong in the research design" → "belong in the evaluation design". L391 "any affected research artifact" → "any affected evaluation artifact". L540 "research/model activation" → "model activation".

**15. MINOR — §14 does not earn its place.** A "v2.0 alignment or correction" table in a v3.0 document, citing the removed regime (L527) and a dangling row (L528 "Companion C15/W07: possible context-conditioned forecasting | Remains an amendment proposal") whose vehicle (DP18, purpose path 4) is gone. Cut §14 to its last paragraph (L534), and add one sentence to §9.2: "Conditioning a forecast on pre-cutoff practical context is not a data obligation of this plan; if ever proposed it is a switch-ON overlay under §8.1's L5 rule."

**16. MINOR — Scale hook.** §12.2 L456–460 is sufficient for ablation to be the method, but the six evidence states (L436) and ablation are never joined, and L460 "An asset that cannot be ablated because nothing reads it has already answered the question" is the only bridge. Add after L460: "An asset's evidence state (§11) bounds its position: ablation applies from `consumed` upward; below that, the state is the score. An identity or constant asset whose removal breaks computation rather than changes a reading is scored by its DP01 parity tests, not ablation." Two sentences; without them a scale must decide both.

**17. MINOR — §5 Āyurdāya row (L223) leaves the computation's owner ambiguous.** "L1 computed inputs" reads as though the figure is computed elsewhere; `ganita_ayurdaya` exists. Replace with "L1 āyurdāya computed under each applicable method".

**18. MINOR — L73 "Each obligation has a named owning contribution" is false: no V-row names a layer.** Either delete the sentence or append a bracketed layer list to each row (e.g. V13 `[L3, L4]`).

**19. MINOR — Unlocatable references.** L264 "The six-view design is not a target constraint." and W05 (L491) "Reconcile previous Kāla plan" — a fresh session cannot find either. Name the artifact or delete L264.

**20. MINOR — §9.3 L391 (withdrawal/tombstone/law) and §1.2 L67 "Nothing here pauses or dispatches another session." are compliance and ceremony residue.** Cut L391 to: "Withdrawal propagates to derived views and caches under DP16." Delete the §1.2 sentence.

**21. MINOR — Frontmatter.** `produced_on: 2026-09-13` and `session_id: ...V2-20260913` predate the v3.0 realignment; `companions` lists v2.0 artifacts as if current.

## Derivability test — L3 Kāla

Attempted: derive the Kāla layer plan from this document plus the parent, against §13.3's eight elements.

Derivable without invention: responsibility and non-claims (§3.1); the obligation scored on (parent §11: Temporal integrity, bound by §13.3 item 1); the contracts consumed (DP05, DP06) and produced (DP07, DP08, inputs to DP09); the qualified coverage list (§5 Kāla row); the no-window semantics, ranking rule and coarse-to-exact discipline (§6.4); the switch-ON use and the L3 prohibition (§9.2); dispositions (§10.1); generation and invalidation (§4.4, §11, DP16); the work packet (W05); the test shapes (§12.2).

Where I had to invent:
1. **P24.** V13 says the present interval needs "the preceding interval for contrast" and "what each is doing". Nothing at L3 or in any DP carries either; I had to decide that DP08 gains two fields and that "doing" is activation state, not meaning. (Finding 6.)
2. **Which V-journeys L3 serves.** No row names a layer; I inferred V02 timing, V04, V05, V06 (alignment), V13. (Finding 18.)
3. **Placement of the parent's named temporal instruments.** Parent §3.10 names Tājaka, tithi-praveśa and Sudarśana; the §5 Kāla row has "annual/return conventions" and §6.2 puts Tājaka at L1. Whether Sudarśana and tithi-praveśa are L1 foundations or L3 clocks is a decision I made, not read.
4. **The acharya rendering of a window.** §3.4 has no temporal row, so which L3 fields must be handed onward for the acharya (geometry, criterion) was my choice. (Finding 4d.)
5. **"Previous Kāla plan" and "six-view design"** — W05 tells me to reconcile against something I cannot locate. (Finding 19.)

Everything else derived cleanly. Items 1 and 4 are the ones that would produce a different Kāla plan from two competent sessions.

## What the cleanse may have cost

One essential clause was lost: v2.0's "keep event-conditioned overlays separate from event-free structural/temporal products" (finding 9). It is the storage obligation that makes the switch a selection rather than a rebuild; the presentation half survived, the data half did not.

Everything else on the removal list is either deliberate and correctly gone, or survives in substance under a different name: the outcome-firewall idea of C1/C3 lives in DP15b, §6.6 and the §12.2 Historical/firewall row; hindsight and exposure live in DP13 and §9.3; the fourth purpose path's disposition is now merely dangling in §14 (finding 15). DP18's removal leaves edge 5 (L124) without a named contract, but §4.4's "evaluation qualification change" class, §6.6 and DP16 cover its obligations; a four-word pointer in edge 5 — "(governed by §4.4 and DP16)" — closes it without restoring DP18.

Nothing else essential was lost.
