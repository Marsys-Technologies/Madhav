---
artifact: REVIEW_DATA_PLANE_FINAL
reviewed: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md (commit 76236bd74, unchanged at HEAD c6541829d; sha256 236b6c72…c94b, matches CAPABILITY_MANIFEST entry 131)
parent: 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md (sha256 c36bd0b2…7383, matches manifest)
child_checked_for_inheritance_only: 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md (manifest version 1.1)
predecessor_for_fold_check_only: MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v3_0.md (deleted at e97bf81f4) via reviews/REVIEW_DATA_PLANE_v3_0.md
produced_on: 2026-09-25
mode: independent, read-only, fresh context; every one of the document's live-state claims re-measured against production (read-only SQL, 2026-09-25); every one of the 21 findings of REVIEW_DATA_PLANE_v3_0 checked against the file rather than against the changelog's account of it
verdict: REJECT
amended_after_native_ruling: "Native decision 11 of 2026-09-25 (NATIVE_DECISIONS_2026-09-25_v1_0.md v1.2) rules that Domain correctness is not a data-plane obligation. Finding 1 is restated as a MAJOR and finding 12 is WITHDRAWN, in place, with the ruling as the reason. Verdict unchanged: two blockers stand."
---

# Review: Data Plane Value Architecture FINAL

**Verdict: REJECT.** Two blockers, both created by the two in-place elevations of 2026-09-25 rather than
by the v3.0 realignment. (A third, the obligation count, was raised here as a blocker and resolved the
same day by native ruling 11 — the data plane is correctly scored on ten of the parent's eleven, because
whether the astrology is *right* is formed above it, in the reasoning layer. What survives of it is a
MAJOR: the exclusion is nowhere written down, and one test row and one whole template section now sit in
the data plane claiming an obligation it does not carry. See finding 1.) (1) §1 declares that obligations crossing into the retrieval
or conversation planes are "DEMANDS on those planes, stated as such" — the word appears in no
obligation anywhere in the document, while the whole of §8, §12.1's managed-door sentence and two §12.2
rows are retrieval- and conversation-plane obligations. (2) The parent makes the synergy term the thing
that makes a plane a plane and requires it to be measured or recorded as an absent instrument; this
document quotes the identity in §1 and then assigns the term to nobody — its own child template
inherits "the layer's synergy binding **if one exists**", which is the child conceding the parent has
none.

Beneath the blockers, the changelog's "all 21 findings folded" (L27) is not true: seven of the twenty-one
are unfolded in whole or in part, and two more were folded somewhere weaker than the finding asked for.
That sentence is the §N.8 defect class in a governance document — a status with no detector behind it.

What is sound: the P-citations are now correct under FINAL numbering on all thirteen V-rows (the v3.0
blocker); the exclusion is gone and §12.1 now states the āyurdāya obligation positively; storage
separation is restored, so OFF is a selection; §3.4 is a real data obligation with a temporal row; §4.1
is the strongest section in the document and the only one making claims a query can falsify. Its claims
are also the ones that fail (finding 9).

Line numbers are the file's own.

## Findings

**1. MAJOR (raised as BLOCKER; superseded in part by native ruling 11 of 2026-09-25) — the
ten-obligation count is right, is nowhere explained, and leaves an orphaned test row here and an
orphaned section in the template.**
Text (L580): "**which of the product definition's ten proof obligations this layer is scored on**, per
its §11 layer table." Same count at L594 and in changelog L28.
Parent §14 (L570–582) is eleven rows — Domain correctness was added by the parent's own FINAL elevation
on 2026-09-25, the same day as this document's two elevations. This review originally read the count as
stale and prescribed adding the eleventh. **Native ruling 11 reverses the prescription and keeps the
count:** the data plane is data engineering and faithful carriage; the astrological verdict is formed
above it. The data plane is scored on ten, deliberately.
What remains wrong is threefold, and all three are the same defect — an exclusion nobody wrote down:
(a) **The reason is unrecorded.** L580 and L594 say "ten" beside a parent that visibly has eleven, and
the next session to notice will "correct" it. Add to §13.3 item 1: "Ten, not eleven: Domain correctness —
whether the astrology is right — is not a data-plane obligation (native ruling, 2026-09-25). This plane
computes faithfully and carries the tradition's testimony, its witnesses and their disagreements intact;
the verdict is formed above it. Carriage of that evidence is required; judgement of it is not."
(b) **§12.2's Domain correctness row (L535) is now orphaned** — a test for an obligation this plane does
not hold, written as four verdicts it is not entitled to reach. Remove it, or replace it with the
carriage test that *is* this plane's: "Source carriage | The cited passage, the witness set with its
recorded disagreement, and any second derivation are present and handed onward, unresolved and unjudged;
a silently settled disagreement is a failure."
(c) **The template carries a whole section for it.** `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`
§2.7 (four checks, `NO DETECTOR` state, "a reference layer is where this matters most") and the `Dom`
gate in its §5.2 instrument govern data-plane layer plans, none of which is scored on this. Both come
out. Checked: the L0 instance (v2.1) never absorbed §2.7, so nothing is unwound downstream.
Unchanged by the ruling: the parent's §14 row itself stands — the *product* must not be astrologically
wrong — and needs one line naming where it is discharged. That is a tier-1 decision; the recorded
default is "above the data plane, in the reasoning layer."

**2. BLOCKER — §1's DEMAND convention has no instance, and §8 is an entire section of other planes'
obligations.**
Text (L61–63): "Where this document says 'the plane', it means the data plane; obligations that cross
into retrieval or conversation are DEMANDS on those planes, stated as such."
Grep: the token appears at L63 and nowhere else as an obligation (L45 "on demand", L161 "demand more
than", L558 "W01 Demand and preservation baseline", L590 "Upstream demand", L605 "L3 demands").
Parent §1.3 (L101–102) gives the retrieval plane "discovery, hydration, capability contracts, coverage
and the omission challenge" and the conversation plane "Paripraśna and the managed MCP door … with
their parity, continuity and delivery obligations". §8.1 is titled "Discover, hydrate, apply, deliver"
and legislates the capability registry, hydration, the investigator, the omission challenge and the
question compass. §8.3 legislates the two managed doors. §12.1 L504: "Both managed doors deliver the
full connected finding." §12.2's Delivery sentinel (L543) and Presentation parity (L536) rows test
conversation-plane behaviour.
A layer plan reading §8 cannot tell whether it must build a capability contract or demand one. Either
mark them — a `DEMAND:` prefix on each obligation in §8.1/§8.2/§8.3 that lands outside L0–L5, and on
the two §12.2 rows — or delete the L61–63 sentence and state plainly that this document legislates the
intermediaries until the retrieval and conversation planes have artefacts of their own (which parent
L106–107 says they do not: "not yet elevated to the standard the data plane now holds"). The second
option is honest and is probably the true state; what cannot stand is a convention with no instances.

**3. BLOCKER — the plane's synergy term is assigned to nobody, and the child template says so.**
Text (L59–61): "Its value composes by the identity in product §1.3 — `plane = Σ layers + Σ synergies
between them` — and the synergy term between planes belongs to the product definition, not here."
The document correctly disclaims the *between-planes* term and then never picks up its own: the word
"synerg" occurs at L60, L61 and L397 (a tool named `synergy`) and nowhere else. Parent L90–94: "At each
level the **synergy term is what makes the level a thing rather than a collection** … The term is
measurable — it is what remains when the parts are summed and the whole is measured — and where it
cannot yet be measured, that is recorded as an absent instrument, never as a number." This document
records neither a measurement nor an absent instrument for Σ synergies between L0–L5.
The child has already paid for this. Template §1.3 (L184) reads `inherits: Data plane §3.4
(presentation contract), §7 (DP contracts), the layer's synergy binding if one exists` — "if one
exists" is the template working around a missing parent obligation, and the L0 instance then invented
its own three-seam synergy measurement (its §1.3 L364–404). Two more layer plans will invent two more.
Fix: add to §3 a subsection naming the plane-level term — which cross-layer seams constitute it (the
shared vocabulary of §4.1, the DP contracts of §7, the ordering of §3.2's five edges), its instrument
(cross-layer ablation: hold every asset in place, break the seam), and its current state as an absent
instrument where no harness exists. Add a §12.2 row: "Synergy | The measured plane value against the sum
of the six layer values; the residual is named, and where no harness exists it is recorded as an absent
instrument, never as a number." Add a §13.3 element requiring each layer plan to state its own three
terms (individual, synergistic, cross-layer handoff) — the template already specifies the shape at its
§1.5 L219; this document should hand it down rather than receive it upward.

**4. MAJOR — changelog L27 "Both fixed, all 21 findings folded" is false; of the 21 numbered findings,
10 are fully folded, 6 are partial or folded somewhere weaker, and 5 are not folded at all.**
Checked one by one against the file, not against the changelog:
- **Fully folded (10):** 1 (exclusion gone, §12.1 L510 positive), 2 (all thirteen V-rows correct under
  FINAL numbering; L89–90 now cites `p_identifier_note`), 3 (L85 names FINAL), 7 (L534
  narration/arithmetic), 8 (DP15a L368 chronology), 9 (L432–434 storage separation), 10 (L594 asset
  brief), 16 (L518–520 joins ablation to the evidence states, and the suggested identity/constant
  carve-out was generalized into the reference-layer carve-out at L523–529), 17 (L277 "under each
  applicable school"), 18 (false sentence deleted — the underlying gap, that no V-row names a layer,
  survives and reappears as invention 3 of the derivability test below).
- **Partial or folded somewhere weaker (6):** 4 (b and d folded; a moved the passed-clause record into
  DP02's L0 lane instead of DP05 — finding 5; c dropped DP17 but now claims DP06 carries source
  witnesses — finding 6), 5 (the §12.2 parity row landed, the §13.3 item 6 append did not — finding 11),
  6 (P24 answered in §5 L274, which binds obligations, not in a contract, which binds fields — finding
  7), 11 (five of six orphans gone; DP14 L367 still reads "voluntary burden and exposure"), 14 (three of
  four; L614 still "research/model activation"), 21 (a comment added at L11; `session_id`, `companions`
  and the review-record ambiguity unchanged).
- **Not folded (5):** 12 (`permitted` without referent — all six sites survive; finding 13 below), 13
  (`purpose-qualified` — L429, L476), 15 (§14 not cut — L596–607 intact, including the C15/W07 row), 19
  (L318 "six-view design" and W05 L562 "previous Kāla plan" both still unlocatable), 20 (§9.3 L449
  law/tombstone sentence and §1.2 L85 "Nothing here pauses or dispatches another session." both intact).

Fix: replace "Both fixed, all 21 findings folded" with "Both blockers fixed; 10 of 21 findings folded,
6 partially, 5 outstanding — listed in REVIEW_DATA_PLANE_FINAL_v1_0" — or fold them, which is mostly
deletion and takes less space than the sentence claiming it was done.

**5. MAJOR — DP02 L355 carries a chart-scoped record in an L0-producer lane.**
Text: "DP02 Rule qualification | L0 → calculation, interpretation and investigator | Exact rule clauses,
method, school/tradition, **prerequisites tested (including those that passed)**, exceptions, unresolved
alternatives and executable scope".
Which prerequisites were tested, and which passed, is per-chart evidence; L0 cannot produce it. The v3.0
review asked for this in DP05 ("every clause tested with its result (passed, partial, failed)"); the fold
put it in DP02 instead and left DP05 (L358) at "Formation, participants, partial/failing clauses and
cancellation". A layer plan binding DP02's fields under §13.3 item 6 would look to L0 for a result only
L1/L2 can produce, and the acharya rendering's "prerequisites actually tested … including those that
passed silently" (§3.4 L169) would have no producer.
Fix: DP02 → "Exact rule clauses, method, school/tradition, the prerequisites and exceptions that **must
be** tested, unresolved alternatives and executable scope; invocation is not application." DP05 →
"Formation, participants, **every clause tested with its result (passed, partial, failed)** and
cancellation; hydrate actual configuration before timing." §3.4 L169 → "DP02 (the clause set that had to
be tested), DP05 (each clause's actual result)".

**6. MAJOR — §3.4 L173 attributes source witnesses to DP06, which does not carry them.**
Text: "The competing readings and which classical authority each rests on | DP06 structural relationship
(variants and their source witnesses)". DP06 (L359) carries "Actor/relation/target, all relevant
domains, constituent facts/signals, signed support/opposition, condition/occurrence ledgers, variants and
ancestry" — no witness. This is the exact defect class of the v3.0 review's finding 4: a §3.4 row
pointing at a contract that does not carry what the row claims. The witness lives in DP02.
Fix: either cite `DP06, DP02` as the v3.0 review directed, or amend DP06 to "…variants, ancestry and the
source witness each variant rests on".

**7. MAJOR — P24 has a V-row, a §5 row and no contract.**
V13 (L107) requires "the active-clock set, its participants and the preceding interval for contrast".
§5's Present interval row (L274) assigns ownership: "L3 owns the interval set and its boundaries; L4 owns
the expression". DP07 (L360) and DP08 (L361) carry neither the present interval nor the preceding one,
and §6.4 (L308–318) is silent. §5 binds *obligations* ("The layer plans must bind each applicable
obligation to exact source clauses, supported operator scope and tests", L260); §7 binds *fields*, and it
is §7 that §13.3 item 6 sends a layer plan to. §12.2's Temporal boundary row does not test it either.
Fix: append to DP08 — "…alternate routes, horizon, and for the present-tense need the interval now
active and the one immediately preceding it, with each engaged participant." Append to §6.4: "The
present interval is served from the same mechanisms: the active clock set at `as_of`, its engaged
participants and the preceding interval for contrast; what each mechanism is doing is L3's activation
state, what it may mean is L4's."

**8. MAJOR — §4.3 L246 grants a reconstruction path the parent removed.**
Text: "An allegedly lost doctrine needs identified witnesses and explicit reconstruction status, never an
AI-invented verse."
Parent §13 L559–562: "**No cross-population hypothesis testing and no source reconstruction.** … Recovery
of lost knowledge and the proposing and testing of new astrological hypotheses across populations of
subjects are not features of this product." Under the parent there is no reconstruction to carry a
status; the sentence is residue of the lost-knowledge horizon the parent's 3.1 cleanse removed, and as
written it reads as a permission with a condition attached. §4.3's own survey ("Distinguish supported,
readable-but-not-executable, disputed, unsupported and method-inapplicable rules") already handles the
honest case.
Fix: "A doctrine known only by report is recorded as unsupported with its witnesses named; reconstruction
is out of scope (parent §13), and an AI-composed verse is never a source."

**9. MAJOR — §4.1 rule 1's detector tests the alias half of the rule and not the identity half; both
halves fail live.**
Text (L203): "| 1 | **One canonical id, one closed alias set, per thing.** … | every ontology entity
carries a non-empty alias set; a class with none is a finding |"
Re-measured today, read-only, against production:
- `SELECT count(*), count(DISTINCT canonical_id) FROM brahma_ontology` → **741 rows, 730 distinct, 11
  duplicate ids**: `ashtakavarga` (concept+school), `balarishta` (concept+dosha), `daridra` (dosha+yoga),
  `dhaiya` (concept+dosha), `kemadruma` (dosha+yoga), `kp` (dasha_system+school),
  `neecha_bhanga_raja_yoga` (concept+yoga), `phaladeepika` (school+text), `sade_sati` (concept+dosha),
  `sthira_dasha` (concept+dasha_system), `vyatipata` (upagraha+yoga). The rule's first clause — one
  canonical id per thing — has no detector, and the identity owner fails it.
- Alias coverage by class: 16 classes, and `dosha` is **79 rows of 79 with an empty alias set**; every
  other class is 0. So the detector that does exist is failing for one class, which happens to be the
  class a doṣa lookup by name must resolve through.
- Confirmed correct in passing: the sixteen classes named at L210–213 are exactly the sixteen
  `entity_class` values in the table, and `planet` is 11 rows with aliases on all 11 — L212's "eleven
  planets and nothing else" is a fair description of code-side adoption, not of the ontology.
Fix: rule 1's detector → "per class and across classes, `count(*) = count(DISTINCT canonical_id)`; **and**
every entity carries a non-empty alias set. A duplicate id is a rule-1 failure even when both rows are
individually correct, because a resolver returns two rows and the caller picks one." (An id that must
name two things needs two ids, or a class-qualified key declared as the canonical form — that decision
belongs to the L0 plan, the detector does not.)

**10. MAJOR — the document is registered and cited as governing, and still asks to be adopted.**
`status: CURRENT`, `version: FINAL`, CAPABILITY_MANIFEST entry 131 CURRENT with a fingerprint that
matches the live file, and parent §1.3 L100 names it as the data plane's governing artefact. Against
that: L83 "This is the **proposed** master for deriving six layer definitions"; frontmatter L17
"Authorization to prepare this proposal is not adoption of its recommendations or implementation
authority"; L616 "**Recommended decision:** adopt this value architecture as the basis for the six layer
plans". The L0 plan has already been derived from it (v2.1, manifest version 2.2) and the template it
produces is at 1.1. A layer plan cannot tell whether it is deriving from an adopted authority or citing a
proposal.
Fix: frontmatter `authority:` → the actual adoption record; L83 → "This is the master for deriving six
layer definitions"; §15 → replace the recommendation with the adoption fact and keep only what genuinely
remains unresolved (the list at L614 is still correct and still unresolved).

**11. MAJOR — §13.3 is nine elements called eight, and item 6 never received the §3.4 binding.**
Items run 1, 1a, 2, 3, 4, 5, 6, 7, 8 (L579–592) — nine; changelog L28 still lists "§13.3's eight
layer-plan elements" among what was retained deliberately. The v3.0 review's finding 5 asked for a §12.2
parity row **and** an append to item 6; the row landed (L536) and the append did not, so the test
("the acharya rendering exposes every §3.4 field its layer owns") checks a declaration no plan is
required to make.
Fix: renumber 1a as 2 and the rest onward (or state nine), correct L28, and append to item 6: "…named
owners and tests, **including which §3.4 rows this layer carries and which fields it hands onward for
them**."

**12. WITHDRAWN by native ruling 11 of 2026-09-25.** As raised, this finding said that §12.2's
reference-layer carve-out (L523–527) defines L0's individual term as fidelity over four dimensions —
authentic, sourced, correctly identified, within its method boundary — none of which is "the astrology is
right", and that this re-opened for L0 the hole the same day's other elevation had just closed.
Under the ruling the carve-out is **correct as written**: those four dimensions *are* the data plane's
whole half of the question, and the half it was accused of dropping was never its to hold. Nothing to fix
here. Retained rather than deleted so the reasoning is on the record: if the reasoning layer is ever
elevated to a governing artefact, the obligation this finding was reaching for belongs in it, and the
four dimensions here are what it may assume has already been guaranteed beneath it.

**13. MINOR — `permitted` still has no referent, and one sentence still points at removed exclusions.**
L278 "Qualified permitted guidance only … Horizon qualification cannot bypass exclusions." → "Attributed
guidance only; source testimony is not demonstrated remedial efficacy." (The exclusions the clause
referred to were removed by the parent's 3.1 cleanse; the parent replaced `permitted` with `earned`.)
L326 "specific permitted forecast is earned" → "specific forecast is earned". L367 "→ permitted
comparison" → "→ comparison". L504 "emits a permitted forecast only when earned" → "emits a forecast only
when earned". L508 "a permitted event-free" → "an event-free". L605 "permitted non-natal horizons" →
"non-natal horizons". Legitimate uses stay: "rights-permitted" (L102), "permitted surface" (L191, L204),
"permitted count" (L208), "permitted export" (L543).

**14. MINOR — `purpose-qualified` survives the removal of the purpose paths.** L429 "the minimum complete
purpose-qualified projection when the switch is ON" → "the minimum complete projection its declared use
requires"; L476 "purpose-qualified observations" → "observations carrying their declared use".

**15. MINOR — §4.1's tail duplicates the rules the elevation put above it, and re-opens a decision rule 1
has taken.** L219–221 ("The identity problem, concretely…") and L223 ("The Sun problem illustrates a
systemic requirement…") are the same sentence twice, the second being the pre-elevation paragraph. L227
restates rule 4. L225 "The L0 plan must decide the exact authority boundary from producer/consumer
evidence" contradicts rule 1, which already decided it: "`bg_ontology` is the identity owner; specialized
`bg_*` assets own their specialized semantics" — and the L0 plan has since been written on that basis.
Fix: delete L223 and L227; cut L225 to its two surviving instructions ("Do not indiscriminately merge
these assets or replace every local constant with a runtime database request"), attributed to rule 1's
boundary rather than to an open decision.

**16. MINOR — unlocatable references.** L318 "The six-view design is not a target constraint." and W05
L562 "Reconcile previous Kāla plan against accepted upstream outputs" — a fresh session can find neither
artefact. Name them or delete the clause; W05's work packet is otherwise self-contained.

**17. MINOR — surviving orphans.** DP14 L367 "voluntary burden and exposure" → "burden and exposure"
(the voluntary observation brief is gone). L614 "research/model activation" → "model activation". V11
L105 "No invented entity birth ." — stray space before the period.

**18. MINOR — ceremony and law residue.** L85 "Nothing here pauses or dispatches another session." —
delete. L449's "under existing law/policy; snapshot retention is not unlimited access. A hash/tombstone
is not assumed anonymous." → "Withdrawal propagates to derived views, caches and affected evaluation
artifacts under DP16." These belong in the intake/correction brief, which the same line already says.

**19. MINOR — §14 does not earn its place in a FINAL document.** A table headed "v2.0 alignment or
correction" (L598), including L602's "Companion C15/W07: possible context-conditioned forecasting |
Remains an amendment proposal" whose vehicle (DP18, the purpose paths) no longer exists. Cut to the
closing paragraph at L608; if the C15/W07 disposition must survive, one sentence in §9.2: "Conditioning a
forecast on pre-cutoff practical context is not a data obligation of this plan; if proposed it is a
switch-ON overlay under §9.2's correctness rules."

**20. MINOR — "the review record" names two different artefacts.** Frontmatter L23 `review_record:
reviews/REVIEW_DATA_PLANE_v3_0.md`; L482, L550 and L612 mean
`MADHAV_DATA_PLANE_V2_REVIEW_RECORD_v1_0.md`. L550 — "All tests listed here are planned unless the review
record explicitly reports a documentation check actually run" — is therefore unresolvable, and it is the
sentence that governs whether any test in §12.2 may be called run. Parent §16: "one record, not parallel
ledgers." Fix: call them "the source review record" and "the document review" throughout, and make L550
name the one it means.

**21. MINOR — frontmatter.** `produced_on: 2026-09-24` on a document twice elevated on 2026-09-25;
`session_id: MADHAV-DATA-PLANE-V2-20260913`; `companions:` still lists the v2.0 review record and
register as if current; `source_revision` / `application_source_base` are bare hashes with no statement
of what they pin. Adjacent, for the registry owner rather than this document: the manifest's `supersedes`
for entry 131 names `…_v2_0.md`, but the immediate predecessor was `…_v3_0.md`, deleted at e97bf81f4.

**22. MINOR — §12.2 L519–520 overstates ablation's reach.** "ablation is how the last two states,
'served' and 'value evaluated', are measured" — 'served' is measured by the Delivery sentinel row (L543);
ablation measures the last state only. Replace "the last two states, 'served' and 'value evaluated'" with
"the last state, 'value evaluated'".

## Derivability test — L1 Gaṇita

Attempted: derive the L1 layer plan from this document plus the parent, against §13.3's nine elements.

Derivable without invention: responsibility and non-claim (§3.1 L118); the layer story and its asset
families (§6.2); contracts consumed (DP01, DP02) and produced (DP03, DP04, DP05 jointly with L0, DP07
primitives) with their required distinctions (§7.1); the coverage obligations whose L1 half is named
(§5 rows for graha roles, rāśi/bhāva, bala/dignity, varga, yoga/doṣa formation, nakshatra/KP, āyurdāya);
the epistemic-typing rule that keeps `ga_vichara` honest (§3.3 L154); dispositions (§10.1); generation,
compatible dependency sets and invalidation (§11, §4.4, DP16); the work packet (W03); the test shapes
(§12.2); vocabulary conformance (§4.1 + §13.3 1a).

Where I had to invent:
1. ~~**Ten obligations or eleven, and whether L1 owns Domain correctness.**~~ **Settled by native ruling
   11 after this test was run:** ten, and L1 does not own it. Retained as the record of what a session
   deriving L1 one day earlier would have had to invent — and as the reason the exclusion must be written
   into §13.3 rather than left as a bare number (finding 1). What L1 *does* keep is the arithmetic half:
   a classical quantity reproducing when derived a second way is Computational correctness, which it
   already owns and already has machinery for.
2. **L1's synergy term.** The template demands three terms; this document supplies no binding, so I had
   to choose the seams (fact-identity joins across varga/strength/condition? the clock boundaries shared
   with L3?) and the instrument. (Finding 3.)
3. **Which V-journeys L1 serves.** No V-row names a layer; the v3.0 review's finding 18 was resolved by
   deleting the false claim rather than by naming owners, so §13.3's "inherited … V-journeys" has no
   source to inherit from. I inferred V01, V02, V04, V05, V07, V12.
4. **Whether §8.1's intermediary obligations are L1's or DEMANDS.** DP10 makes every producer owe
   capability metadata, which is clearly L1's; "hydrate the exact relevant records after candidate
   discovery" is clearly not. Nothing in §8 marks the line. (Finding 2.)
5. **Where the passed-prerequisite record lives** — DP02's L0 lane as written, or DP05. (Finding 5.)
6. **Tājaka, tithi-praveśa and Sudarśana.** Parent §3.10 names all three under Kāla; this document's
   §6.2 L294 puts Tājaka in L1's foundations and §5's Kāla row (L275) says only "annual/return
   conventions". Whether tithi-praveśa and Sudarśana are L1 foundations or L3 clocks is a decision I
   made, not read. The v3.0 review raised this as its L3 invention 3; it is unchanged, and it now bites
   from the L1 side as well.

Items 1, 2 and 6 would produce materially different L1 plans from two competent sessions.

## Measurement re-run

This is an architecture document: almost every statement in it is a target, not a measurement, and is
correctly marked as such (L83, L550, L612). Four live-state claims are checkable, all in §4.1, and they
were re-run read-only against production on 2026-09-25:

| claim | source | re-run | result |
|---|---|---|---|
| one canonical id per thing (rule 1) | L203 | `count(*)` vs `count(DISTINCT canonical_id)` on `brahma_ontology` | **FAIL** — 741 / 730 / 11 duplicate ids in two classes each |
| every entity carries a non-empty alias set (rule 1 detector) | L203 | per-class null/empty `synonyms` census | **FAIL for one class** — `dosha` 79/79 empty; 15 other classes clean |
| sixteen entity classes | L210–213 | `GROUP BY entity_class` | **PASS** — exactly the sixteen named, no others |
| "implemented for eleven planets and nothing else" | L212 | `planet` class | 11 rows, aliases on all 11; the sentence is about code-side adoption and is fair |

The two failures are the same defect the L0 instance's review found independently; they reproduce, and
they are reported here because the rule that should catch them is in *this* document (finding 9).
Nothing else in the document asserts a number about live state, and it should stay that way.

## Parent conformance

| Parent obligation | Carried here |
|---|---|
| §1.3 three planes named, data plane is one of them | §1 L57–63 — carried, but the DEMAND half is unused (finding 2) |
| §1.3 compositional identity, synergy measurable or absent-instrument | **absent** (finding 3) |
| §2 two presentation modes over one analysis | §3.4 — carried well; the acceptance test names the consumed reading package |
| §3.3 narration verified separately from arithmetic | §12.2 L534 — carried |
| §3.4 shared roots are not independent confirmations | §7.1 L377, §12.2 Dependence control — carried |
| §3.10 named temporal instruments | partial — Tājaka assigned to L1 (§6.2), tithi-praveśa and Sudarśana unassigned |
| §7.2 emission record carries the switch state | §9.2 L426–427 — carried |
| §7.3 no chronology reset | DP15a L368 — carried |
| §7.3 learning's output is a visible change to a claim family | §6.6 L330–334 — carried |
| §8 one switch, two states, no third | §9.2 — carried, with the storage-separation clause that makes OFF a selection |
| §8.1 per-layer correctness rules | §9.2 L436–439 — carried |
| §13 no source reconstruction | **contradicted** at §4.3 L246 (finding 8) |
| §14 obligations | **ten, correctly** — Domain correctness excluded by native ruling 11; the exclusion itself is unwritten and its test row is orphaned (finding 1) |
| §14.1 ablation as the per-asset scoring method | §12.2 — carried, with a principled reference-layer carve-out that needs finding 12's sentence |
| §16 every asset brief states P-needs and obligations | §13.3 L594 — carried (with the stale count) |
| §16 one record, not parallel ledgers | partial — "the review record" names two artefacts (finding 20) |

## What the 2026-09-25 elevations left behind

Both elevations are right on the merits and both were made in place without a version change, by
instruction. What they did not do is sweep the document they changed:

- The **controlled vocabulary** elevation (§4.1) wrote a new governing section above three paragraphs
  that already said parts of it, leaving a duplicated Sun paragraph and an open authority decision that
  the new rule 1 closes (finding 15). Its rule 1 detector was written for the alias half only, and the
  identity half fails live (finding 9). Everything else about it is the strongest work in the document:
  six rules each with a detector, sixteen classes, external inputs typed, and the join to §3.4.
- The **reference-layer carve-out** (§12.2) is a real principle — judging perennial knowledge by this
  quarter's readers would retire the tradition one unread chunk at a time — and its four-dimension
  fidelity list silently drops the obligation the *other* elevation added the same day (finding 12).
- Neither elevation reached §13.3's counts or §8's plane boundary. The consequence is an inversion: the
  child template carries the compositional identity (its §1.3–§1.5) while this document assigns the
  synergy term to nobody, so the template inherits "the layer's synergy binding **if one exists**". A
  tier-3 template inventing what tier 2 owes it is the documentation form of the computed-value authority
  inversion this project has already been bitten by once.
- The template also absorbed Domain correctness (its §2.7) and pointed its inheritance at `Data plane §5`,
  which never carried it. Native ruling 11 resolves that in the opposite direction from what this review
  first proposed: the section leaves the template rather than arriving in this document (finding 1c).

## What does not earn its place

§14's alignment table (finding 19). §4.1's L223/L225/L227 tail (finding 15). L85's dispatch sentence and
L449's law clause (finding 18). Nothing else is padding: §5, §7 and §12.2 are the three sections a layer
plan actually binds against, and they are dense rather than long.

## What the cleanse did not cost

Checked against the v3.0 predecessor for silent loss, independently of the fold check: nothing essential
was removed between v3.0 and FINAL. The storage-separation clause that v3.0 had lost is back (L432); the
eight dispositions, five edges, six evidence states, DP01–DP17 and the two load-bearing aphorisms ("a
citation with no declared use does not prove utilization", "lack of a caller in a bounded search is not
redundancy") all survive. The document's problems are additions not swept and a parent that moved on the
same day — not amputations.

---

## Application record — 2026-09-25

**Authorised by:** the native ("Go ahead and apply it"), under native rulings 9, 10 and 11 of
`NATIVE_DECISIONS_2026-09-25_v1_0.md` v1.2. **Signed under ruling 9** — the review was done by an
independent fresh-context pass and folded in the same session, which that ruling permits.

**Applied in full.** All 22 findings are discharged: 20 by edit, 1 restated by ruling 11 and then edited
to match it (finding 1), 1 withdrawn by the same ruling (finding 12).

| document | what changed |
|---|---|
| `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md` | New §3.5 (the synergy term, its four seams, cross-layer ablation as its instrument, absent-instrument rule); §1 plane boundary restated per the native — the retrieval and conversation planes are **not built**, so this document legislates their data-facing obligations and marks them **[TRANSFERS]**; §8 and two §12.2 rows marked; §12.2 Domain correctness row replaced by **Source carriage and reproduction**; §12.2 gains a **Synergy** row; §13.3 states ten elements, records *why* the obligation count is ten, gains item 1b (the three value terms) and the §3.4 binding on item 6; DP02/DP05 clause-result split; §3.4 witness row repointed to DP02; DP08 and §6.4 gain the present interval and its predecessor; §4.1 rule 1's detector now tests identity uniqueness as well as alias coverage; §4.3's reconstruction clause replaced per parent §13; §5's exclusion hook deleted (ruling 10); adoption state corrected in frontmatter, §1.2 and §15; `permitted`, `purpose-qualified`, the duplicated Sun paragraph, the already-taken authority decision, the §14 delta table, the two unlocatable references, the law/ceremony residue and the review-record ambiguity all resolved; the 2026-09-24 changelog entry's "all 21 findings folded" corrected in place to what was actually folded. |
| `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` → v1.2 | §2.7 rescoped from "is the astrology right?" to **source carriage and reproduction**, keeping the three mechanical checks and dropping the seeded negative case with the verdict framing (ruling 11); gate `Dom` → `Carr` and its menu likewise; §3.1's obligation count carries its reason; §5.4 item 6 replaced by ruling 9's signature rule; `independent_review:` corrected from NOT YET to the K3 review that has been folded. |
| `MADHAV_PRODUCT_DEFINITION_FINAL.md` | §14's Domain correctness row keeps its place and names where it is discharged — above the data plane, in the reasoning layer — with the mechanical half left explicitly to this plane. |
| `CAPABILITY_MANIFEST.json` | The three edited documents' `fingerprint_sha256` rotated **in the same session as the edit** (the failure mode two existing WARN tickets in `drift_detector.py` were opened for), `last_verified_*` stamped, template version 1.2, and the data-plane entry's `supersedes` corrected from v2_0 to its actual predecessor v3_0. |

**Deliberately not done, each for a stated reason:**

1. **§13.3 was not renumbered.** Items 1a and 1b stay lettered because the template and the L0 instance
   cite these numbers; renumbering would silently break live inheritance lines to fix a cosmetic defect.
2. **The manifest's own root `fingerprint` and `generated_at` were not touched.** They are maintained by
   whichever governance session regenerates the manifest, and no generator for them exists in the repo.
   Inventing a value for a field whose algorithm is unknown is the defect this review spent twenty-two
   findings on; the rotation that matters — per-entry, verified against the live files — is done.
3. **The parent's P24/P23 row order was left alone** (P24 is printed before P23 in its §2 table). It is a
   tier-1 cosmetic defect and reordering a parent's need table is the native's call, not a fold.
4. **Nothing was committed.** The five changed files are in the working tree of the
   `l3/kala-layer-briefs` worktree.

**Re-verification after the edits:** all three rotated fingerprints recomputed and matched their files;
the residue greps return only the changelog entries that record the history and the legitimate uses
(`rights-permitted`, `permitted surface`, `permitted count`, `permitted export`); the document's section
structure is intact with §3.5 added and §14 reduced to its closing paragraph.
