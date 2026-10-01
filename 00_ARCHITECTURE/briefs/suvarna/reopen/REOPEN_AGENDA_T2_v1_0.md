---
artifact: SUVARNA_REOPEN_AGENDA_T2
canonical_id: SUVARNA_REOPEN_AGENDA_T2
version: "1.0"
status: DRAFT-HELD-FOR-J1
produced_on: 2026-10-02
produced_in: "Exec Suvarna Engine, Track E lane E2 (queue id E2.1-design-002); drafted by a Sonnet drafter"
tier: 2
tier_document: "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md (SEALED 2026-09-25; reopened once, 2026-09-26)"
rows: 11
row_ids: [R06, R73, R75, R88, R89, R90, R91, R119, R181, R186, R198]
verdict_changing_rows: [R06, R88, R89, R90, R91, R119]
decision: "N-4.T2, Strategic Suvarṇa (plan §4.2 J1 rows 4 and 7), decided together with the T1 and T3 agendas"
sources:
  - "TRACK_E_BRIEF_v1_0.md §6 (the spec); SUVARNA_CAMPAIGN_PLAN_v1_5.md §4.2 (J1 rows 4 and 7), §5.1 (E2)"
  - "nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md D2 (ruling 2026-09-27) and D3"
  - "NIKASHA_CHANGE_REGISTER_v2_0.md (v2.8), the eleven rows"
  - "the tier-2 document, the tier-3 and tier-4 templates and the L0 instance at origin/campaign/nikasha-test @ 2a78ec64d"
changelog:
  - "1.0 (2026-10-02): first issue. Eleven rows; drafted replacement text; no tier document edited. R85 is not a row (withdrawn from the T2 agenda by D2 rev. 2.1; CLOSED in the register); R109's registry columns are P9 data work, not a reopen."
---

# Reopen agenda — Tier 2 (data plane value architecture) — v1.0 DRAFT, held for J1

**Purpose.** The D2 ruling of 2026-09-27 authorised one reopen per sealed founding document on a reviewed row-to-clause agenda. This is the agenda for Tier 2, `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md`. It holds **11 rows**: two frontmatter count corrections (R73, R75); the multi-producer clause (R06); four per-layer statements the tier is missing and the layer template asks for (R88 switch behaviour, R89 §3.4 carried-by-layer, R90 §5 obligation ownership, R91 entity classes); the [TRANSFERS] tag at the points where a layer plan reads it (R119, T2 half); and the §7.1 text halves of R181, R186 and R198. **Six rows are VERDICT-CHANGING** (R06, R88, R89, R90, R91, R119) because each adds a population, a detector or an ownership a gate or a layer test is then measured over; the strategist should read those first. R90 and R91 cannot be drafted to completion from the source text alone (they need an ownership decision) and say so. The agenda is closed once opened (D2 rule 1); T2 is edited only after N-4.T2, on a lane branch, and re-sealed second (after T1, before T3).

Line numbers are those of the blobs at `origin/campaign/nikasha-test` @ `2a78ec64d`; every quotation was copied from its source by script and verified against it. Row-count reconciliation (31 against 32) is in Appendix A of the T1 agenda.

## Sources

| Tag | Document | Where it was read |
|---|---|---|
| T1 | `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md` (tier 1, SEALED 2026-09-25) | `git show origin/campaign/nikasha-test:<path>` @ `2a78ec64d` |
| T2 | `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md` (tier 2, SEALED, reopened once 2026-09-26) | same |
| T3 | `00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` (tier 3, SEALED, reopened once 2026-09-26) | same |
| T4 | `00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md` (tier 4, DRAFT_PENDING_REVIEW; cited only for echoes) | same |
| REG | `00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md` (frontmatter `version: "2.8"`) | same |
| D2 | `00_ARCHITECTURE/briefs/nirmana/nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md` (v2.1; sections D2 and D3 are the ruling) | same |
| Track E brief | `00_ARCHITECTURE/briefs/suvarna/tracks/TRACK_E_BRIEF_v1_0.md` §6 (the spec for this packet) | `/Users/Dev/madhav-suvarna-plan` (read-only) |


**Risk classes.** *wording-only* — corrects text and changes no obligation, test or verdict a tool or reviewer could read off the clause. *structural* — adds, moves or re-points a section, column or rule, so instances, tools and other tiers must follow, but no existing PASS/N/A/pending outcome changes by itself. **VERDICT-CHANGING** — the replacement could change what counts as PASS, N/A, FAIL, NO_DETECTOR or "pending" for an asset, a layer or an instance (it adds a detector, an obligation, a ruled-out test, a new pending state, or a population a gate is measured over). Strategic Suvarṇa reviews every VERDICT-CHANGING row first.

## Summary

| Row | Clause (location) | Remedy chosen | Risk class |
|---|---|---|---|
| R06 | T2 §13.3 item 2 :678 (inventory); T3 §1.1 inherits it | New sentence in §13.3 item 2: a shared table is listed once, every producer named, each producer's count and `count_sql` scoped to its own rows. (§7.1 considered and rejected) | **VERDICT-CHANGING** |
| R73 | T2 frontmatter `document_reviews` :37 | "2 BLOCKER + 10 MAJOR + 11 MINOR" → "2 BLOCKER + 9 MAJOR + 10 MINOR (21 findings)" | wording-only |
| R75 | T2 changelog item (f) :42 ("nine elements") | Dated correction note in the entry (T2's own :45 precedent); text kept | wording-only |
| R88 | T2 §9.2 table :498–501 and storage-separation paragraph :510 | Per-layer switch table; L1 computes identically under both states, with the register's detector | **VERDICT-CHANGING** |
| R89 | T2 §3.4 table :188–197 | Third column "Carried by layer", from §7.1's producer column and the register's assignments | **VERDICT-CHANGING** |
| R90 | T2 §5 table :325–339 | Fourth column "Owned by (layer → what it owns)", filled only where T2 already says; the rest UNASSIGNED pending an owner decision | **VERDICT-CHANGING** (needs decision) |
| R91 | T2 §4.1 Scope :268–271; §13.3 item 1a :672–674 | L0 owns all sixteen classes; every other layer declares its classes from its §7.1 contracts, the census measures them (the register's literal per-layer matrix needs an owner decision) | **VERDICT-CHANGING** (needs decision) |
| R119 | T2 §13.3 items 1 and 6 :662, :682; §7.1 DP10–DP12 :429–431; §12.2 rows :614, :621 | Add the [TRANSFERS] mark and the D3 `[TRANSFERS]-pending` rule at each point a layer plan reads them | **VERDICT-CHANGING** |
| R181 | T2 §7.1 table :418–437 and its lead-in :414–416 (T3 §0.3 asks for the index) | Edge-type column and per-layer produced/consumed index (shared draft D-7.1) | structural |
| R186 | T2 §7.1 :416, :418–437 (T3 §2.3 asks for declared use) | Declared-use column (shared draft D-7.1) | structural |
| R198 | T2 §13.3 item 6 :682 and §7.1 | Per-layer index in §7.1 (shared draft D-7.1); the fallback (name where the index lives) is given | structural |

Not rows here: R85 (withdrawn from the T2 agenda; CLOSED), R109 (registry columns `produces_contracts` / `consumes_contracts`, P9 data work), the T4 §1.2 half of R119 (the D2 "proceed now" list).

## R06 — Multi-producer shared tables have no expression in the contract vocabulary

**Risk class: VERDICT-CHANGING.** It adds a rule about what an asset's row count and `count_sql` are measured over, so Build check 5 (count and integrity, T4 §4.2) and any inventory count can change for assets that share a table. It is the T2 parent of R10 in the T3 agenda: decide the two together.

**Register row.**

> Multi-producer shared tables (one table, several writers, e.g. `brahma_ontology` with four) have no expression anywhere in the contract vocabulary
>
> **State in register:** **OPEN** — needs a clause in §7.1 or §13.3: a shared table declares its producers and each producer's `count_sql` is scoped to its own rows. CONFIRMED L1/L2/L3/L5 in P4 (R95, R103, R136, R205); refuted for L4 — T2 reopen agenda, clause §7.1 or §13.3 chosen on the agenda (D2 ruling 2026-09-27)
> — REG R06 :126 (severity BLOCKS_LAYER)

**Clause as it stands.** There is no clause: that is the defect. The two candidate homes, as they stand — §7.1's envelope (producer and consumer owners are recorded per use, :414) and §13.3 item 2 (the inventory element, which T3 §1.1 inherits):

> Every material use records: consumer question/distinction; producer/consumer owners;
> — T2 :414

> 2. Complete owned inventory including accepted, residual, service, shared and historical capital; source/runtime evidence levels separated.
> — T2 :678

> inherits:    Data plane §13.3 item 2
> — T3 :164

The concrete failure the register cites for L0 (the L0 instance, correction C-10):

> | C-10 | §1.1 models one `target_table` per asset and cannot express a **shared table with several producers**. `brahma_ontology` has four (`l0_ontology.py` 414 rows / 14 classes, plus `l0_yogas.py`, `l0_doshas.py`, `l0_dasha_systems.py` supplying 327 more), and `bg_ontology`'s `count_sql` credits it with all 741 | document (this instance) + layer | the first asset certification |
> — L0 instance (`MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md`) :686

**Remedy chosen by D2.**

> R06 (multi-producer clause — §7.1 or §13.3, chosen on the agenda)
> — D2 :121–122

**Chosen here: §13.3 item 2**, one sentence, and not §7.1. Reasons: (1) the property is about inventory and measurement — what a row count means — not about a contract's fields; (2) T3 §1.1, where R10 lands the layer-instance half, already declares `inherits: Data plane §13.3 item 2`, so the inheritance chain stays intact without a second pointer; (3) §7.1 is being edited by R181/R186/R198 and keeping R06 out of it keeps those three rows reviewable as one change. If SS prefers §7.1, the same sentence goes after the envelope paragraph at :414, and T3 §1.1's `inherits` line gains `§7.1`.

**Drafted replacement text** — item 2 of §13.3 (:678) with one sentence appended; the original text is unchanged:

~~~~
2. Complete owned inventory including accepted, residual, service, shared and historical capital; source/runtime evidence levels separated. **Shared tables:** where one table has several producers (one table, several writers), the inventory lists the table once and names every producer; each producer's row count and its `count_sql` are scoped to the rows that producer writes. A producer credited with rows another producer wrote is a measurement defect, not a count.
~~~~

**Cross-tier re-render hazards.**
- T3 §1.1 (R10, this round): the same property at layer-instance level; wording must agree.
- T4 §4.2 check 5 ("`count_sql` present, correctly scoped") already says the right thing in general; no T4 edit, but the census check that reads it should be re-run for the shared tables once the clause is sealed.
- Register rows that confirm the gap per layer and close with this clause only if SS says so: R95 (L1), R103 (L2), R136 (L3), R205 (L5); R22 (declaring universes) is "R06-adjacent" per its own state.
- L0 instance C-10 (`bg_ontology` credited with all 741 `brahma_ontology` rows); the other three L0 producers are named there.
- Element count: §13.3 stays "Ten elements" (the sentence is added inside item 2).

**Open questions.**
1. §7.1 vs §13.3 (above) — SS to confirm.
2. Is a shared table with one *writer* per partition (for example by `entity_class`) in scope, or only several writers? The register's words are "one table, several writers"; the draft follows them.

## R73 — T2 frontmatter misstates the v3.0 review's finding counts

**Risk class:** wording-only.

**Register row.**

> T2 frontmatter document_reviews misstates the v3.0 review as "2 BLOCKER + 10 MAJOR + 11 MINOR"; the file measures 2+9+10 = 21 findings (matches the FINAL review's own line 8). Correct the counts
>
> **State in register:** OPEN — T2 reopen agenda (D2 ruling 2026-09-27)
> — REG R73 :200 (severity COSMETIC)

**Clause as it stands.**

> document_reviews:                                                    # independent reviews OF this document
>   - reviews/REVIEW_DATA_PLANE_v3_0.md      # REJECT, 2 BLOCKER + 10 MAJOR + 11 MINOR; 10 folded at FINAL, 6 partly, 5 outstanding
>   - reviews/REVIEW_DATA_PLANE_FINAL_v1_0.md  # REJECT, 2 BLOCKER + 9 MAJOR + 10 MINOR; all folded by this revision, 1 restated and 1 withdrawn by native ruling 11
> — T2 :36–38

**Evidence (re-measured 2026-10-02).** `grep -E '^\*\*[0-9]+\. '` over each review file at the same snapshot, counting the severity word that follows the number:

~~~~
REVIEW_DATA_PLANE_v3_0.md      : 2 BLOCKER (findings 1-2) + 9 MAJOR (3-11) + 10 MINOR (12-21) = 21 findings
REVIEW_DATA_PLANE_FINAL_v1_0.md: 2 BLOCKER (2,3) + 9 MAJOR (1,4-11; #1 restated as MAJOR) + 10 MINOR (13-22) + 1 WITHDRAWN (12) = 22 findings
~~~~

The FINAL review itself states that it checked "every one of the 21 findings of REVIEW_DATA_PLANE_v3_0" (the register cites its line 8), and T2's own entry for the FINAL review (:38) already reads "2 BLOCKER + 9 MAJOR + 10 MINOR", matching. Only the v3.0 line (:37) is wrong: 2 + 10 + 11 sums to 23, not 21. The tail of the same line, "10 folded at FINAL, 6 partly, 5 outstanding", sums to 21 and agrees with the fix.

**Remedy chosen by D2.**

> R73 and R75 (frontmatter counts)
> — D2 :121–122

D2 names R73 and R75 as "frontmatter counts" and does not otherwise choose; the register's remedy ("Correct the counts") is a single option, adopted.

**Drafted replacement text** (line :37):

~~~~yaml
  - reviews/REVIEW_DATA_PLANE_v3_0.md      # REJECT, 2 BLOCKER + 9 MAJOR + 10 MINOR (21 findings); 10 folded at FINAL, 6 partly, 5 outstanding
~~~~

**Cross-tier re-render hazards.** `ELEVATION_CHAIN_SEAL_2026-09-25_v1_0.md` already says "its predecessor's 21 findings" (SEAL :46–47) and needs no edit. T2's FINAL changelog entry (:42) says "10 fully folded, 6 partial … 5 not folded at all" (21) — consistent. No other tier cites the 23.

**Open questions.** None.

## R75 — T2 changelog says §13.3 is nine elements; §13.3 says ten

**Risk class:** wording-only.

**Register row.**

> T2 changelog item (f) says "§13.3 is nine elements"; §13.3 says and has "Ten elements" (1, 1a, 1b, 2–8). Fix the changelog or annotate 1b's later addition
>
> **State in register:** OPEN — T2 reopen agenda (D2 ruling 2026-09-27)
> — REG R75 :202 (severity COSMETIC)

**Clause as it stands.**

> (f) §13.3 is nine elements and says so (1a kept rather than renumbered, because the template and the L0 instance cite these numbers); item 6 gains the §3.4 binding the parity test needs.
> — T2 :42

> **Ten elements.** Item 1a is the vocabulary element added by the 2026-09-25 elevation and item 1b the
> — T2 :658

Item 1b is the value-terms element, and the same changelog entry adds it in its item (d):

> §12.2 gains a Synergy row and §13.3 a required element.
> — T2 :42

**Remedy chosen by D2.** D2 says only "R73 and R75 (frontmatter counts)" (D2 :121–122). The register offers two remedies, "Fix the changelog or annotate 1b's later addition". **Chosen here: annotate, keep the original words.** A changelog is history; T2 already corrects its own history by dated annotation rather than rewriting (:45, "CORRECTED 2026-09-25: this entry originally claimed all 21 findings were folded"). The annotation does not say 1b was added *later* (the entry cannot show the order: (d) and (f) sit in the same change); it says only what is checkable — the count omits 1b.

**Drafted replacement text** (inside :42, item (f); the rest of the entry is unchanged):

~~~~
old: (f) §13.3 is nine elements and says so (1a kept rather than renumbered,
new: (f) §13.3 is nine elements and says so [CORRECTED on the T2 reopen: this count omits item 1b, the value-terms element that (d) of this same entry adds; §13.3 as it stands has ten elements — 1, 1a, 1b, 2–8 — and says so] (1a kept rather than renumbered,
~~~~

**Cross-tier re-render hazards.** T3 and the L0 instance cite §13.3 items by number ("the template and the L0 instance cite these numbers"); the numbering is not changed, so no echo. Grep "nine elements" and "eight" near "§13.3" across tiers before sealing.

**Open questions.** None.

## R88 — Per-layer behaviour of the life-event switch (what a layer emits when OFF)

**Risk class: VERDICT-CHANGING.** It names a detector (L1 birth-fact immutability) where T3 §2.1's rule row currently has none, so an L1 correctness rule can move from `NO_DETECTOR` to PASS or FAIL.

**Register row.**

> L1's life-event switch behaviour (what a computation layer emits when the switch is OFF). Clause (T3 §2.1): "The life-event switch: what this layer may do when ON, what it emits when OFF, and the storage separation that makes OFF a selection rather than a rebuild." → State in T2 §9.2, per layer: L1 computes identically under both states; the switch binds consumers (L2+), not the fact layer; detector: birth-fact immutability per (chart_id, input revision)
>
> **State in register:** OPEN — T2 reopen agenda (D2 ruling 2026-09-27)
> — REG R88 :260 (severity BLOCKS_LAYER)

**Clause as it stands** — what T3 §2.1 asks the instance to state, and what T2 §9.2 currently gives:

> The product's per-layer "what must not happen" row, verbatim. The life-event switch: what this layer
> may do when ON, what it emits when OFF, and the storage separation that makes OFF a selection rather
> than a rebuild. The prohibition on invented computation, source, detector, confidence or score. **For
> each rule, the detector.** A rule with no detector is a wish.
> — T3 :269–272

> | Switch | What the plane may do | What every reading must carry |
> |---|---|---|
> | **ON** | L0 event vocabulary; L1 separate event-time context; L2 structural alternatives compared against reported history; L3 alignment of reported intervals against independently established mechanisms, and inspection of unmatched windows; L4 manifestation distinctions; L5 adjudication of frozen claims against admitted observations. | The switch state, recorded in the emission record beside the information cutoff. |
> | **OFF** | Nothing derived from life events, anywhere. Every reading emits only what the chart, sources and methods produce on their own. No life events appear in any inquiry surface. | The switch state, as above. |
> — T2 :498–501

> **Storage separation, which is what makes OFF a selection rather than a rebuild:**
> — T2 :510

T2 gives ON per layer and OFF only globally ("Nothing derived from life events, anywhere"); a computation layer's OFF behaviour is therefore not stated, which is the gap the L1 instance hit.

**Remedy chosen by D2.**

> R88 (§9.2 per-layer switch behaviour)
> — D2 :122–123

D2 says "§9.2 per-layer switch behaviour". The register gives the L1 content and its detector; the other layers' OFF behaviour follows from T2's own rows (ON overlays are deselected, not recomputed, :510), and their detectors are, per T3 §2.1, named by the layer instance.

**Drafted replacement text.** New paragraph and table inserted after the §9.2 table (after :501), before the "Across all layers" paragraph (:503):

~~~~
**Per layer, what the switch does.** The switch binds the consumers of life-event material; it never changes how a fact layer computes its event-free products. Read the table with the storage-separation rule below: OFF deselects overlays and never requires recomputing event-free products.

| Layer | Switch ON — what it may do (as the table above states it) | Switch OFF — what the layer emits | Detector |
|---|---|---|---|
| L0 | event vocabulary | The same vocabulary: a vocabulary is not an event store and is not derived from life events (§6.1). | Named by the layer instance (T3 §2.1: for each rule, the detector). |
| L1 | separate event-time context | Computes identically under both states. The switch binds consumers (L2 and above), not the fact layer; event-time context is a separate overlay that OFF deselects. | Birth-fact immutability per (chart_id, input revision): the L1 fact rows for a (chart_id, input revision) are identical with the switch ON and OFF. |
| L2 | structural alternatives compared against reported history | Its event-free products only; the ON overlay named in the previous column is deselected, never recomputed. | Named by the layer instance (T3 §2.1: for each rule, the detector). |
| L3 | alignment of reported intervals against independently established mechanisms, and inspection of unmatched windows | Its event-free products only; the ON overlay named in the previous column is deselected, never recomputed. | Named by the layer instance (T3 §2.1: for each rule, the detector). |
| L4 | manifestation distinctions | Its event-free products only; the ON overlay named in the previous column is deselected, never recomputed. | Named by the layer instance (T3 §2.1: for each rule, the detector). |
| L5 | adjudication of frozen claims against admitted observations | Its event-free products only; the ON overlay named in the previous column is deselected, never recomputed. | Named by the layer instance (T3 §2.1: for each rule, the detector). |
~~~~

**Cross-tier re-render hazards.**
- T3 §2.1 (`inherits: … Data plane §9.2`, :264) needs no edit; each layer instance's §2.1 can now transcribe the row. L1 instance: the detector row. T3 §2.1's text ("what it emits when OFF") is satisfied by the new column.
- The L0 row ("same vocabulary") is a reading of §6.1, not a quoted rule; see open question 1.
- Product §8.1 (the per-layer "what must not happen" row, cited by T3 §2.1) is T1 and unchanged.

**Open questions.**
1. L0: does OFF remove the L0 event vocabulary? §6.1 says "a vocabulary is not a private event store"; the draft reads that as the vocabulary staying. SS or the L0 owner to confirm.
2. Detectors for L0 and L2–L5 are not specified by the register or by D2; the draft leaves them to each layer instance (T3 §2.1), which is a weaker claim than the register's "State in T2 §9.2, per layer" for L1. If SS wants all six in T2, a detector owner must supply four more.

## R89 — Which layer carries each §3.4 presentation row

**Risk class: VERDICT-CHANGING.** D3's replacement for T3 §5.4 test 4 tests that "Every §3.4 field this layer owns" is present in its produced contracts; this column is what defines "owns". It therefore decides, per layer, what the producer-field carriage test passes or fails. Decide R89 together with R71 (T3 agenda).

**Register row.**

> Assignment of §3.4 presentation rows to layers (T2 maps fields→contracts, never rows→layers). Clause (T2 §13.3 item 6): "including which §3.4 presentation rows this layer carries and which fields it hands onward for them" → Add to T2 §3.4 a "carried by layer" column per row (conventions → L1 via DP01/DP03; intermediate quantities → L1 via DP03/DP04; dignity components → L1 via DP04; method/school, passed clauses, competing readings, typed chains, clock rows → L0/L2/L3 as named)
>
> **State in register:** OPEN — T2 reopen agenda (D2 ruling 2026-09-27)
> — REG R89 :261 (severity BLOCKS_LAYER)

**Clause as it stands** — T2 §3.4 (rows :190–197) and the T3 clause that asks for the assignment:

> | What the acharya presentation renders | Which contract must carry it |
> |---|---|
> | The method and school a finding rests on, and where authorities disagree | DP02 rule qualification, amended to carry school/tradition and unresolved alternatives |
> | The prerequisites actually tested and the exceptions actually checked, including those that passed silently | DP02 (the clause set that must be tested), DP05 (each clause's actual result — passed, partial, failed) |
> | Conventions in force - ayanamsha, node, house system, varga construction | DP01 identity/release, DP03 chart facts |
> | Intermediate quantities, not only the graded result | DP03, DP04 condition decomposition |
> | Dignity, strength and condition components **separately**, with their units and their disagreements | DP04 |
> | The competing readings and which classical authority each rests on | DP06 structural relationship (variants and ancestry), DP02 (the source witness each variant rests on) |
> | The chain of influence with its typed relations, not a summarized verdict | DP06 |
> | The clock geometry, the activation rule, the named nearest-versus-better-supported criterion, and the manifestation bridge or its falsifier | DP07 clocks/contacts, DP08 temporal mechanism, DP09 manifestation |
> — T2 :188–197

> including which §3.4 presentation rows this layer carries and which fields it hands onward for them
> — T2 :682

**Remedy chosen by D2.**

> R89 (§3.4 carried-by-layer column)
> — D2 :123

**Drafted replacement text.** The §3.4 table gains a third column; the first two columns are unchanged:

~~~~
| What the acharya presentation renders | Which contract must carry it | Carried by layer |
|---|---|---|
| The method and school a finding rests on, and where authorities disagree | DP02 rule qualification, amended to carry school/tradition and unresolved alternatives | L0 (DP02 is produced by L0, §7.1) |
| The prerequisites actually tested and the exceptions actually checked, including those that passed silently | DP02 (the clause set that must be tested), DP05 (each clause's actual result — passed, partial, failed) | L0 for the clause set (DP02); L2 for each clause's result (DP05, the configuration hydrated before timing) |
| Conventions in force - ayanamsha, node, house system, varga construction | DP01 identity/release, DP03 chart facts | L1 (via DP01 identity/release and DP03 chart facts) |
| Intermediate quantities, not only the graded result | DP03, DP04 condition decomposition | L1 (via DP03, DP04) |
| Dignity, strength and condition components **separately**, with their units and their disagreements | DP04 | L1 (via DP04) |
| The competing readings and which classical authority each rests on | DP06 structural relationship (variants and ancestry), DP02 (the source witness each variant rests on) | L2 (DP06 variants and ancestry), with the source witness each variant rests on from L0 (DP02) |
| The chain of influence with its typed relations, not a summarized verdict | DP06 | L2 (DP06) |
| The clock geometry, the activation rule, the named nearest-versus-better-supported criterion, and the manifestation bridge or its falsifier | DP07 clocks/contacts, DP08 temporal mechanism, DP09 manifestation | L3 for clocks, contacts and the activation rule (DP07, DP08); L4 for the manifestation bridge or its falsifier (DP09); clock primitives from L0 and L1 (DP07) |

A layer owns a §3.4 row when it appears in that row's third column. A layer carries and hands onward the fields of the rows it owns; the producer-field carriage test (§12.2; see R119 (d)) and T3 §2.2 read this column.
~~~~

Basis for each cell: the register's own assignments ("conventions → L1 via DP01/DP03; intermediate quantities → L1 via DP03/DP04; dignity components → L1 via DP04; method/school, passed clauses, competing readings, typed chains, clock rows → L0/L2/L3 as named") for rows 3–5 and the layer set; the "as named" layers for rows 1, 2, 6, 7, 8 are read from §7.1's Producer → consumer column (DP02 L0 :421; DP05 "L0+L1 → L2 → L3" :424; DP06 L2 :425; DP07 "L0/L1/L3 primitives" :426; DP08 "L2+qualified clocks → L3" :427; DP09 "L3+… → L4" :428).

**Cross-tier re-render hazards.**
- T3 §2.2 (R71's `measured_by` rewording) and the new §5.4 test 4 rely on "owns"; T3 §2.2's body ("Which §3.4 fields **this layer** must retain", :282) now has a lookup.
- T4 §0.1 row 4 ("presentation fields it must carry", from layer §2.2) is unchanged.
- T2 §3.4's own acceptance sentence ("both renderings must be producible from the consumed reading package", :205–206) is untouched.
- Layer instances: each instance's §2.2 should list the rows whose third column names the layer; the L0 instance records "parity test state: NOT RUN" (L0 :329–341) and will re-render.

**Open questions.**
1. Row 2: DP05's producer cell reads "L0+L1 → L2 → L3" (:424), which does not say which layer *produces* the clause results. The draft assigns the result to L2 (the configuration layer, §6.3) and the clause set to L0 (DP02, which says "each clause's *result* for a chart is DP05", :421). Owner to confirm.
2. Row 8: DP09's cell reads "L3+qualified structural/rule evidence → L4" (:428); the draft treats the manifestation bridge and falsifier as carried by L4 (§6.5). The register assigns "clock rows" to L3 and says nothing of L4. Owner to confirm.
3. Conventions (row 3): DP01 is an L0 contract, but the *conventions in force for a chart* are carried in L1's chart facts; the draft follows the register ("→ L1 via DP01/DP03").

## R90 — Per-layer enumeration of the coverage obligations (so width is measurable)

**Risk class: VERDICT-CHANGING, and not draftable to completion from the source text.** The enumeration defines each layer's coverage universe; the inspector's width measure and every layer's `Earn`/coverage states are then measured over it. Where T2 does not already say which layer owns an obligation, no source does, so the draft marks the cell UNASSIGNED rather than inventing an owner (B.10).

**Register row.**

> Enumerated list of coverage obligations L1 owns (Product §3 names substance, not owned obligations; width NOT_GENERIC on all 19). Clause (T3 §2.4): "Which of the product's coverage obligations this layer owns, with prerequisites, variants, exceptions, negative cases and uncertainty. Each ends in one of the five states." → Data plane §5 gains a per-layer obligation enumeration; the inspector declares each asset's universe so width is measurable
>
> **State in register:** OPEN — T2 reopen agenda (D2 ruling 2026-09-27)
> — REG R90 :262 (severity BLOCKS_LAYER)

**Clause as it stands** — T3 §2.4 asks the instance which obligations the layer owns; T2 §5 is the table it draws from, with a column on cross-asset contribution but none on owning layer:

> Which of the product's coverage obligations this layer owns, with prerequisites, variants, exceptions,
> negative cases and uncertainty. Each ends in one of the five states. A tool name, an empty result or a
> populated confidence field is not "applied".
> — T3 :309–311

> | Domain obligation | Data that must survive | Cross-asset contribution |
> |---|---|---|
> | Graha contextual roles | Natural/functional role, lordship, kāraka, placement, condition and relevant relations separately. | L0 meaning → L1 computed roles/placements → L2 mechanism → L3 participating roles → L4 domain-specific interpretation. |
> | Rāśi/bhāva/lord/kāraka | Reference frame, occupants, lord/associated houses and significators; sign is not silently house. | Combine primary-domain evidence with qualified adjacent domains; do not reduce to occupant lists. |
> | Bala/dignity/avasthā | Components, units, condition causes, verification, positive/negative contributions and missingness. | Capacity, ease, prominence and inhibition remain separate; no universal favourability or probability conversion. |
> | Sambandha | Actor → typed relation → target; aspect school/orb where applicable; conjunction, exchange, dispositors, nakshatra chains, argalā/virodha; source and fact IDs. | Investigate decisive chains, cycles, alternative routes and shared dependencies. A path's meaning must survive graph compression. |
> | Bhāvat Bhāvam | Qualified derived-house scope, primary/derived identities, prerequisites, relevant participants, exceptions and actual application status. | Limited existing amplifier and shared derived-house map remain qualified parts, not assumed full concept coverage. No removal of doctrine limits without review. |
> | Varga and reference perspectives | Varga method, domain, sensitivity, relationship to D1, reference lagna and exceptions; arūḍha/special-lagna meaning. | Distinguish resources from appearance/standing and stable versus input-sensitive support; multiple views of one input are not independent votes. |
> | Yoga/doṣa/bhaṅga | Catalog definition, actual formed/partial/not-formed states, participants, failed clauses, cancellation conditions and further manifestation qualifications. | Nīcha-bhaṅga is not automatically a fully effective Rāja Yoga; temporalize the configuration and its conditions, not just a planet label. |
> | Nakshatra/KP | Nakshatra/pada relationships and scope; symbolic/source layer distinct from calculated chains; method-native cusp/sub-lord/nodal-agency prerequisites. | Specialized evidence joins only within qualified contexts, then compares coherently with other methods. |
> | Present interval (P24) | The active clock set at `as_of`, each active clock's participants and what it is doing, and the immediately preceding interval retained for contrast. Activation is L3; expression of what it is doing is L4. | L3 owns the interval set and its boundaries; L4 owns the expression; neither may infer the other's half. |
> | Kāla | Daśā hierarchy, contact geometry, reference sign/house, transit conditions, applicable AV/vedha, annual/return conventions and precise coverage. | Background period, enablement, trigger, inhibition and recurrence are distinct contributors to the same structural mechanism. |
> | Praśna/Muhūrta/calendar | Correct question/undertaking, location/time, method eligibility and constraints. | Preserve existing services; do not relabel conversational Paripraśna as a completed Praśna method or birth pañcāṅga as arbitrary future election data. |
> | Ayurdaya and constitution | Method and school identity, its required inputs, the cancellations and exceptions each school applies, the disagreement between authorities, and the uncertainty carried by each step. Retain the computation and its limits together; a bare figure without its method and its cancellations is not a qualified result. | L0 method/source -> L1 ayurdaya computed under each applicable school -> L2 constitutional structure -> L3 applicable intervals -> L4 expression, with the tradition's own caveats preserved at every hop. |
> | Voluntary practice and wider tradition | Attributed practice, scope, burden, suitability, contraindication and evidence class; proper spatial/collective/non-natal inputs. | Attributed guidance only; source testimony is not demonstrated remedial efficacy. |
> — T2 :325–339

**Remedy chosen by D2.**

> R90 (§5 per-layer obligation enumeration)
> — D2 :123–124

**Drafted replacement text.** The §5 table gains a fourth column, filled only from what T2 already states (each cell cites its section), and a rule is added after the table:

~~~~
| Domain obligation | Data that must survive | Cross-asset contribution | Owned by (layer → what it owns) |
|---|---|---|---|
| Graha contextual roles | Natural/functional role, lordship, kāraka, placement, condition and relevant relations separately. | L0 meaning → L1 computed roles/placements → L2 mechanism → L3 participating roles → L4 domain-specific interpretation. | L0 meaning → L1 computed roles and placements → L2 mechanism → L3 participating roles → L4 domain-specific interpretation (the chain this row already states). |
| Rāśi/bhāva/lord/kāraka | Reference frame, occupants, lord/associated houses and significators; sign is not silently house. | Combine primary-domain evidence with qualified adjacent domains; do not reduce to occupant lists. | L1 computes the reference frame and placements (§6.2). Further layer ownership: UNASSIGNED. |
| Bala/dignity/avasthā | Components, units, condition causes, verification, positive/negative contributions and missingness. | Capacity, ease, prominence and inhibition remain separate; no universal favourability or probability conversion. | L1 (DP04 condition decomposition, §7.1), read by L2, L3, L4. |
| Sambandha | Actor → typed relation → target; aspect school/orb where applicable; conjunction, exchange, dispositors, nakshatra chains, argalā/virodha; source and fact IDs. | Investigate decisive chains, cycles, alternative routes and shared dependencies. A path's meaning must survive graph compression. | L2 (DP06 structural relationship, §7.1). |
| Bhāvat Bhāvam | Qualified derived-house scope, primary/derived identities, prerequisites, relevant participants, exceptions and actual application status. | Limited existing amplifier and shared derived-house map remain qualified parts, not assumed full concept coverage. No removal of doctrine limits without review. | UNASSIGNED — T2 §5 and §6 name no owning layer. |
| Varga and reference perspectives | Varga method, domain, sensitivity, relationship to D1, reference lagna and exceptions; arūḍha/special-lagna meaning. | Distinguish resources from appearance/standing and stable versus input-sensitive support; multiple views of one input are not independent votes. | L1 computes varga (§6.2). Arūḍha and special-lagna meaning: UNASSIGNED. |
| Yoga/doṣa/bhaṅga | Catalog definition, actual formed/partial/not-formed states, participants, failed clauses, cancellation conditions and further manifestation qualifications. | Nīcha-bhaṅga is not automatically a fully effective Rāja Yoga; temporalize the configuration and its conditions, not just a planet label. | L0 holds the rule and clause set (DP02); L1 holds the yoga assets (§6.2); L2 holds formed / partial / not-formed configurations and clause results (DP05). |
| Nakshatra/KP | Nakshatra/pada relationships and scope; symbolic/source layer distinct from calculated chains; method-native cusp/sub-lord/nodal-agency prerequisites. | Specialized evidence joins only within qualified contexts, then compares coherently with other methods. | L1 holds the nakshatra assets (§6.2). Method-native cusp, sub-lord and nodal-agency prerequisites: UNASSIGNED. |
| Present interval (P24) | The active clock set at `as_of`, each active clock's participants and what it is doing, and the immediately preceding interval retained for contrast. Activation is L3; expression of what it is doing is L4. | L3 owns the interval set and its boundaries; L4 owns the expression; neither may infer the other's half. | L3 owns the interval set and its boundaries; L4 owns the expression (this row; §6.4). |
| Kāla | Daśā hierarchy, contact geometry, reference sign/house, transit conditions, applicable AV/vedha, annual/return conventions and precise coverage. | Background period, enablement, trigger, inhibition and recurrence are distinct contributors to the same structural mechanism. | L3 (§6.4); clock primitives from L0 and L1 (DP07). |
| Praśna/Muhūrta/calendar | Correct question/undertaking, location/time, method eligibility and constraints. | Preserve existing services; do not relabel conversational Paripraśna as a completed Praśna method or birth pañcāṅga as arbitrary future election data. | L0 calendar and astronomy substrate (§6.1); L1 pañcāṅga and specialized services (§6.2). Praśna / Muhūrta method ownership: UNASSIGNED. |
| Ayurdaya and constitution | Method and school identity, its required inputs, the cancellations and exceptions each school applies, the disagreement between authorities, and the uncertainty carried by each step. Retain the computation and its limits together; a bare figure without its method and its cancellations is not a qualified result. | L0 method/source -> L1 ayurdaya computed under each applicable school -> L2 constitutional structure -> L3 applicable intervals -> L4 expression, with the tradition's own caveats preserved at every hop. | The chain this row already states: L0 method and source → L1 under each school → L2 constitutional structure → L3 applicable intervals → L4 expression. |
| Voluntary practice and wider tradition | Attributed practice, scope, burden, suitability, contraindication and evidence class; proper spatial/collective/non-natal inputs. | Attributed guidance only; source testimony is not demonstrated remedial efficacy. | UNASSIGNED — §6.5 places the electional and remedial assets in Phala, but §5 names no owning layer for this obligation. |

Each layer owns the obligations whose fourth column names it. The layer plan (§13.3 item 4) enumerates those obligations, and the inspector declares each asset's universe from that enumeration so that width is measurable. A cell marked UNASSIGNED is a tier-2 gap: a layer instance does not assign it for itself; it records `owner unassigned` and raises it here.
~~~~

**Cross-tier re-render hazards.**
- T3 §2.4 and T4 §1.1 (width and depth against a declared universe, T4 :160) read this enumeration; T4's census `NOT_GENERIC` (width) state is what it makes measurable.
- T1 §11's "Proof that matters" column (T1 :498–505) names the *proof obligation* per layer, not the domain obligations; do not confuse the two.
- Layer instances: the L1 instance's §2.4 (R110, R142, R187, R202 depend on R90; the register's R22 state cites R90, R110, R123 as the L1–L3 confirmations).

**Open questions.**
1. **Needs a decision.** Two obligations (Bhāvat Bhāvam; Voluntary practice) have no owning layer in T2 at all, and four more (Rāśi/bhāva, Varga, Nakshatra/KP, Praśna/Muhūrta/calendar) carry only a partial assignment. Either an owner (the domain owner of each layer) assigns them, or Track A's harvest (A.H) supplies the answers before the agendas are combined (Track E §6 "Combine"). This draft is a complete structure with the sourced cells filled, not a finished enumeration.
2. Whether a layer may own an obligation jointly with another (rows 1, 7, 12 name chains) or only one owner per obligation is allowed; the draft reproduces the chains T2 already states.

## R91 — Which of the sixteen entity classes each layer emits or accepts

**Risk class: VERDICT-CHANGING, and not draftable to completion from the source text.** It fixes the population the `Vocab` gate and the per-class independent-map census are measured over for each layer. The register's literal remedy (T2 names each layer's classes) needs an ownership decision no source provides; the draft gives a rule that needs none, and the matrix as an alternative.

**Register row.**

> Which of the sixteen entity classes L1 emits/accepts; the per-class independent-map census (`local_map_candidates: -1`). Clause (T3 §2.6): "Which of the sixteen entity classes this layer emits or accepts; for each, whether every name resolves through the controlled set … how many independent maps the layer's code carries (permitted: one)" → Census emits per-class alias coverage and the map census per class; T2 names each layer's emitted/accepted classes
>
> **State in register:** OPEN — T2 reopen agenda (D2 ruling 2026-09-27)
> — REG R91 :263 (severity BLOCKS_LAYER)

**Clause as it stands.** T3 §2.6 asks for the classes per layer; T2 §4.1 lists the sixteen classes and says L0 owns the set; T2 §13.3 item 1a already requires each layer plan to state its classes:

> Which of the sixteen entity classes this layer emits or accepts; for each, whether every name resolves
> through the controlled set, whether an unlisted name is raised, how many independent maps the layer's
> code carries (permitted: one), and whether each Python/TypeScript snapshot it depends on is generated
> from the authority, pinned by release id and digest, and joined to it by a parity test.
> — T3 :321–324

> **Scope.** All six semantic families of §4.2 and all sixteen entity classes of the ontology — planets,
> signs, houses, nakshatras, vargas, karakas, aspect types, upagrahas, yogas, doṣas, daśā systems,
> domains, concepts, remedy types, texts, schools. A principle implemented for eleven planets and
> nothing else has not been implemented.
> — T2 :268–271

> 1a. **Vocabulary conformance (§4.1):** which entity classes the layer emits or accepts; that every
>    one resolves through the controlled set; the independent-map census per class; and, for L0
>    only, that it *owns* the set and its releases.
> — T2 :672–674

**Remedy chosen by D2.**

> R91 (per-layer entity classes)
> — D2 :124

**Chosen here: a derivation rule (Option A), with the matrix (Option B) as an alternative.** T2 §13.3 item 1a already makes the layer plan state its classes, so what is missing is a rule for what the answer is derived from and a statement of L0's position. Option A states them without assigning any layer a class that no source assigns.

**Drafted replacement text — Option A.** A new paragraph after the Scope paragraph of §4.1 (after :271):

~~~~
**Per layer.** L0 owns the controlled vocabulary and therefore all sixteen entity classes (rule 1). Every other layer declares, in its plan (§13.3 item 1a), the entity classes it emits or accepts, listed from the DP contracts it produces and consumes (§7.1): a class is declared if and only if a canonical id of that class appears in a field of one of those contracts. The inspector reports, per declared class, alias coverage and the independent-map census (rule 6), and reports any class the layer's code touches that its declaration omits.
~~~~

**Alternative — Option B** (the register's literal remedy): a table in §4.1 with one row per layer and the classes it emits or accepts. L0 = all sixteen (rule 1, sourced). L1–L5 cannot be filled from T2's text: §6 names assets and contributions, not classes. It would be filled by the layer owners or by the census itself (alias coverage by class is already something the census can emit), then sealed.

**Cross-tier re-render hazards.**
- T3 §2.6 (`measured_by`: "alias-set coverage per entity class the layer touches", :317) already measures per class; Option A gives it the declaration to measure against. T4's `Vocab` row (T4 :228) names which of §4.1's six rules apply to an asset and needs no edit.
- §13.3 item 1a stays at the same number (no renumbering).
- Register rows that confirm the gap per layer: R111, R143, R189, R203 (and L0's own).

**Open questions.**
1. Option A or B (SS). A is the smaller edit and cannot misassign a class; B is what the register asked for and what makes the per-layer population reviewable in one place.
2. Is a class "accepted" when it appears only in a consumed contract's field list, or only when the layer's code resolves a name of that class? The draft says contract fields (derivable from §7.1); the T3 §2.6 text says "emits or accepts" without defining it.

## R119 — [TRANSFERS] material embedded without the mark where a layer plan reads it (T2 half)

**Risk class: VERDICT-CHANGING.** It decides, at the points a layer plan inherits, which obligations are the layer's own and which are the receiving plane's, and it makes `[TRANSFERS]-pending` a recorded non-pass, non-block state. It is the T2 half of D3; decide it with R71.

**Register row.**

> (I-20) [TRANSFERS] material embedded without the mark at the point of obligation (§13.3 items 1 and 6, template §2.2 measured_by, T4 §1.2). Clause (T2 §1): "A [TRANSFERS] obligation is not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work." → Every §13.3 item, DP contract row and §12.2 row carries its [TRANSFERS] tag at the point where a layer plan reads it, not only where it is defined
>
> **State in register:** OPEN — T2 half (§13.3 items 1/6, DP rows) on the T2 reopen agenda; T4 §1.2 half proceeds now; per D3 and D2 ruling 2026-09-27
> — REG R119 :296 (severity BLOCKS_LAYER)

**Clause as it stands.** The definition of the mark (§1), the two §12.2 rows that already carry it, the section-level mark on §8, and the two §13.3 items that do not:

> Every obligation in this document that belongs to one of them is marked **[TRANSFERS]** — it moves to
> that plane's artefact, unchanged in substance, when that plane is elevated. A [TRANSFERS] obligation is
> not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work.
> — T2 :83–85

> | Presentation parity **[TRANSFERS]** |
> — T2 :614

> | Delivery sentinel **[TRANSFERS]** |
> — T2 :621

> **[TRANSFERS] — read this before the section.** Almost everything below belongs to the **retrieval plane**
> (discovery, hydration, capability contracts, coverage, the omission challenge) or the **conversation
> plane** (Paripraśna, the managed MCP door, their parity and delivery obligations). Neither plane is built
> yet and neither has a governing artefact, so their data-facing obligations are stated here — and they move
> to those artefacts, unchanged in substance, when those planes are elevated (§1). A layer plan does not
> inherit this section as its own build work. The one permanent data-plane obligation inside it is what a
> — T2 :451–456

> 1. Consumer value and distinctive layer responsibility; the inherited P-needs, V-journeys and DP
>    contracts; and **which of the product definition's ten proof obligations this layer is scored on**,
>    per its §11 layer table. A layer plan that names its own criteria instead of inheriting these is
>    not derived from the product definition.
> — T2 :662–665

> 6. Upstream demand and downstream offers with field/grain/context/lineage contracts, named owners and tests, **including which §3.4 presentation rows this layer carries and which fields it hands onward for them**.
> — T2 :682

The DP rows a layer plan reads for those obligations carry no tag:

> | DP10 Capability discovery | All producers → registry/investigator/build consumers | Concepts/fields, prerequisites, exact access path, scope, permission, qualification, pagination/freshness and gaps. Support both question→data and field→actual consumer. |
> | DP11 Investigation completeness and question compass | Capabilities/evidence → planner/omission audit | Expandable concept and relationship obligations; real application states; low-ranked decisive evidence; independent challenge; consequential uncertainty → smallest admissible discriminating next step and burden. |
> | DP12 Complete delivery | Findings → managed channels/export/replay | Every relevant authorized fact and conjoint interpretation mapped to delivered parts; material counter-evidence survives budgets and resumption. |
> — T2 :429–431

**Remedy chosen by D2** (D2's R119 text and D3's rule):

> R119's T2 half (the [TRANSFERS] tag at §13.3 items 1 and 6 and on the §12.2/DP rows where a layer plan reads them)
> — D2 :124–125

> - **End-to-end Presentation parity and Delivery sentinel remain owned by the receiving plane**
>   ([TRANSFERS], T2 §12.2). Where that owner or its test is not built, the instance records
>   `[TRANSFERS]-pending — <obligation>; owner: <plane>; depends on: <artefact>` — no pass, and no block
>   on the instance for the transferred part alone. This does not discharge product acceptance. Where
>   the owner can run the test, its result is linked, never inherited as the layer's own acceptance:
>   the existence of a built plane is not an ownership assignment.
> — D2 :172–177

**Drafted replacement text.**

(a) Item 1 of §13.3 — a new sentence after "…is not derived from the product definition." (after :665, before the "**Ten, not eleven**" paragraph):

~~~~
Where the end-to-end test of an obligation is **[TRANSFERS]** (§12.2: Presentation parity; Delivery sentinel), the layer plan marks it so at that point, states what the layer itself carries and proves (the §3.4 fields it owns, by producer-field contract test), and records `[TRANSFERS]-pending — <obligation>; owner: <plane>; depends on: <artefact>` where the owning plane or its test is not built. It never inherits the end-to-end test as its own work, and a built plane is not an ownership assignment.
~~~~

(b) Item 6 of §13.3 (:682) — the bold clause is extended; the rest of the item is unchanged:

~~~~
old: **including which §3.4 presentation rows this layer carries and which fields it hands onward for them**
new: **including which §3.4 presentation rows this layer carries and which fields it hands onward for them** (the layer's own, proved by its producer-field contract test); end-to-end Presentation parity and Delivery sentinel on those rows are **[TRANSFERS]** (§12.2) and are not this layer's to inherit
~~~~

(c) §7.1 rows DP10, DP11, DP12 (:429–431) — append to the last cell of each, derived from the §8 header (:451–456), which places capability contracts, coverage and the omission challenge in the retrieval plane and "their parity and delivery obligations" in the conversation plane, and keeps DP10 capability metadata as the one permanent data-plane obligation:

~~~~
DP10: append  **[TRANSFERS]** except what a producer owes about itself — its capability metadata, real scope and honest gaps (§8).
DP11: append  **[TRANSFERS]** (retrieval and conversation planes, §8).
DP12: append  **[TRANSFERS]** (conversation plane, §8).
~~~~

(d) **Optional, outside D2's literal list — SS to keep or strike.** D3 makes the producer-field proof "binding" ("every §3.4 field the layer owns is present in its produced contracts, by contract test", D2 :169–171) and T3's new test 4 and §2.2 `measured_by` name a "producer-field carriage test", but T2 §12.2 has no row for it: the only parity row (:614) is tagged [TRANSFERS] and folds the producer half ("the acharya rendering exposes every §3.4 field its layer owns") into the end-to-end test. A row that is not [TRANSFERS] closes that:

~~~~
| Presentation fields carried | Every §3.4 field this layer owns (third column of §3.4) is present in its produced contracts — a contract test run in the layer, not transferred. |
~~~~

**Cross-tier re-render hazards.**
- T3 §5.4 test 4 and §2.2 `measured_by` (R71, T3 agenda) carry the same tag and the D3 wording; the three must read alike.
- T4 §1.2 (the T4 half; D2 "proceed now") already marks reachability [TRANSFERS] (T4 :174: "The requirement — that all of the width and depth be reachable — is a [TRANSFERS] obligation on the retrieval plane").
- T4 §0.1 row 5 and the Dens gate read DP12; check that no gate row treats DP12 as the layer's own work.
- `CAPABILITY_MANIFEST`/inspector: any detector that reads "DP10–DP12" as layer obligations.
- L0 instance :329, :341, :658, :681 record the parity test as NOT RUN / UNMET (re-render).

**Open questions.**
1. **Which DP rows carry the tag (SS).** D2 says "the §12.2/DP rows where a layer plan reads them" and does not list the rows; (c) is derived from §8's header. DP11 and DP12 are fully tagged and DP10 split on that reading; the owner of the retrieval and conversation planes' obligations may disagree.
2. §12.2's "Omission challenge" row (T2 :620) is named in §8's header as a retrieval-plane obligation ("the omission challenge") but is not tagged. The draft does not tag it (D2 lists none); flagged for the second round if SS agrees it is [TRANSFERS].
3. Is `[TRANSFERS]-pending` a recorded annotation or a new verdict value? See R71 open question 1 in the T3 agenda; this agenda assumes an annotation (the closed verdict set of T3 §5.3 is not touched).
4. Item (d) is a new row, not a tag; if SS holds the agenda to D2's wording it is struck and T3's "producer-field carriage test" needs a definition elsewhere (T3 §2.2 body is the natural place).

## Shared draft D-7.1 — the §7.1 additions that close R181, R186 and R198

Three register rows ask for three parts of one change to T2 §7.1. They are drafted once here and each row below states which part answers it. The registry-column half stays with R109 (P9 data work, not a reopen).

**Clause as it stands.**

> Every consumer declares whether an input contributes to calculation, applicability, counter-evidence, uncertainty, interpretation, exclusion, navigation or evaluation. A citation with no declared use does not prove utilization. Not every useful input changes a score.
> — T2 :416

> | Contract | Producer → consumer | Required use and preserved distinction |
> |---|---|---|
> | DP01 Identity/release | L0 → all adapters and writers | Canonical entities, qualified aliases, units and released definitions; local representations cannot diverge in meaning. |
> — T2 :418–420

**Part A — two columns on the §7.1 table**, "Edge type (§3.2)" and "Declared use (consumer)". Values are PROPOSED from each row's own wording (the third column of the table below shows the words relied on; it is not part of the pasted text). Edge types follow §3.2's own definitions: Definition (shared identity, unit, method or rule meaning); Computational (reproducible dependency from pinned producer output to consumer output); Serving-context (hydration, source drill, whole-chart context, query relevance); Evaluation (frozen claims and admitted observations into protected comparison). Declared use is one or more of the eight uses §7.1 already names (:416).

| Contract | Edge type (§3.2) | Declared use (consumer) | Basis (row's own words — agenda only) |
|---|---|---|---|
| DP01 | Definition | calculation; navigation | units and released definitions · qualified aliases |
| DP02 | Definition | applicability; interpretation | executable scope · unresolved alternatives |
| DP03 | Computational | calculation | grain/value/unit |
| DP04 | Computational | calculation; uncertainty | constituents and reasons · Retain zeros as zeros and unavailable as unavailable |
| DP05 | Computational | applicability; counter-evidence | passed, partial, failed · and cancellation |
| DP06 | Computational | interpretation; counter-evidence | Actor/relation/target · signed support/opposition |
| DP07 | Computational | calculation; uncertainty | actual interval boundaries · coverage and uncertainty |
| DP08 | Computational | applicability; exclusion | qualified necessary/optional conditions · enablement/inhibition |
| DP09 | Computational | interpretation; counter-evidence | competing expressions · falsifier |
| DP10 | Serving-context | navigation | exact access path |
| DP11 | Serving-context | navigation; counter-evidence | smallest admissible discriminating next step · low-ranked decisive evidence |
| DP12 | Serving-context | interpretation; counter-evidence | conjoint interpretation · material counter-evidence survives budgets and resumption |
| DP13 | Evaluation | evaluation | event/knowledge/confirmation clocks |
| DP14 | Evaluation | evaluation | Fit/misfit/unassessable |
| DP15a | Evaluation | evaluation | Capture/seal original proposition |
| DP15b | Evaluation | evaluation | Independent adjudication |
| DP16 | Computational | exclusion | Dependency-specific stale marking |
| DP17 | Computational | interpretation | changed/unchanged/unsupported findings |

Paste form: two columns appended to each §7.1 row, headed `Edge type (§3.2)` and `Declared use`, holding the second and third columns above.

**Part B — per-layer produced / consumed index**, a new §7.1a after the table, derived mechanically from the Producer → consumer column (layer names as that column writes them; where it names a kind of consumer, not a layer, the cell says so):

~~~~
### 7.1a Per-layer index of the contracts

| Layer | Produces (producer side of §7.1) | Consumes (consumer side of §7.1) |
|---|---|---|
| L0 | DP01, DP02; DP05 (with L1); DP07 primitives (with L1, L3) | — |
| L1 | DP03, DP04; DP05 (with L0); DP07 primitives (with L0, L3) | DP01 (all adapters and writers); DP02 (calculation) |
| L2 | DP05 (the L0+L1 → L2 hop); DP06; DP08 (with qualified clocks) | DP01; DP02 (interpretation); DP03, DP04 |
| L3 | DP07 primitives (with L0, L1); DP09 (with qualified structural/rule evidence) | DP01; DP02; DP03, DP04; DP05; DP06; DP07 (primitives from L0, L1); DP08 |
| L4 | none named in §7.1 | DP01; DP02; DP03, DP04; DP09 |
| L5 | none named in §7.1 | DP13 (observation owner); DP14; DP15a, DP15b |

The index is read from §7.1's Producer → consumer column. A layer plan lists its produced and consumed contracts (§13.3 item 6) and is checked against this table; the registry columns `produces_contracts` and `consumes_contracts` will carry the same index as data.
~~~~

**Part C — the fallback for R198.** If SS prefers not to hand-author an index that R109 will generate, §13.3 item 6 can instead name where the index lives: append "; the per-layer produced and consumed index is the registry's `produces_contracts` / `consumes_contracts` columns, and until they exist the layer plan states it from §7.1's Producer → consumer column". This answers R198's own alternative ("or §13.3 item 6 names where that index lives") and nothing else.

**Cross-tier re-render hazards (shared).**
- T3 §0.3 ("Receives from … by edge type, by DP contract", :139–140), §2.3 (R201) and §1.4 read these columns; T4 §0.1 row 5 ("contracts produced and consumed, with declared use") inherits them.
- T2 §3.2's five edge types: Part A uses four of them (Definition, Computational, Serving-context, Evaluation). The fifth (Next-generation artifact) has no DP row; check that no DP contract is meant to be one.
- The contract count in §7 (DP01–DP17 with DP15a/b = 18 rows) is unchanged; grep "DP01" ranges and "seventeen" across tiers.

**Open questions (shared).**
1. The edge-type and declared-use values are proposals; they have a basis in the row text but are judgements. A domain owner should confirm all 18 rows, or SS can defer the column to R109's registry data and seal only the structure.
2. L4 and L5 "produces" are not named in §7.1 at all: L4 (manifestation) hands onward to L5 and to the served reading, and L5's outputs are claims and evaluations. This is exactly the gap R181 reports for L4 ("Which DP contracts L4 produces (vs consumes)"). It cannot be closed by transcription; a contract row (or an explicit statement that L4 produces DP09 and L5 produces DP15a/b) is a content decision.
3. DP05's chain "L0+L1 → L2 → L3" is read as L2 producing the configuration; owner to confirm (same question as R89 open question 1).

## R181 — Which DP contracts each layer produces versus consumes, and the edge type of each (L4 case)

**Risk class:** structural.

**Register row.**

> Which DP contracts L4 produces (vs consumes), and the edge type of each L4 edge. Clause (T3 §0.3): "- **Receives from:** upstream layers, by edge type, by DP contract.\n- **Hands onward to:** downstream layers, by edge type, by DP contract." → T2 §7.1 gains a per-layer rollup: contracts produced and consumed, each with its §3.2 edge type
>
> **State in register:** OPEN — §7.1 text half on the T2 reopen agenda; the registry-column half stays with R109 in P9 (D2 ruling 2026-09-27)
> — REG R181 :368 (severity BLOCKS_LAYER)

**Clause as it stands.** §7.1 as quoted under D-7.1; the T3 clause that asks for it:

> - **Receives from:** upstream layers, by edge type, by DP contract.
> - **Hands onward to:** downstream layers, by edge type, by DP contract.
> — T3 :139–140

**Remedy chosen by D2.**

> the §7.1 text halves of R181/R186/R198 (per-layer produced/consumed index with edge type and declared-use column)
> — D2 :125–126

**Drafted replacement text.** Parts A (edge-type column) and B (the per-layer index). Row L4 of Part B reads "none named in §7.1", which is the defect R181 reports, now visible; closing it needs the content decision in open question 2 above. The registry-column half stays with R109.

**Cross-tier re-render hazards and open questions.** As listed under D-7.1.

## R186 — The declared use of every consumed contract

**Risk class:** structural.

**Register row.**

> The declared use of every consumed contract. Clause (T3 §2.3): "Every consumed input declares its use … **A citation with no declared use is not a contract.**" → T2 §7.1 gains a declared-use column per contract, so instances inherit rather than assign
>
> **State in register:** OPEN — §7.1 text half on the T2 reopen agenda; the registry-column half stays with R109 in P9 (D2 ruling 2026-09-27)
> — REG R186 :373 (severity BLOCKS_LAYER)

**Clause as it stands.** §7.1 as quoted under D-7.1; the T3 clause that asks for it:

> Two tables: DP contracts this layer **produces** (consumer, fields, grain, identity, generation) and
> DP contracts it **consumes** (producer, fields, declared use). Every consumed input declares its use
> — calculation, applicability, counter-evidence, uncertainty, interpretation, exclusion, navigation,
> evaluation. **A citation with no declared use is not a contract.**
> — T3 :296–299

**Remedy chosen by D2.**

> the §7.1 text halves of R181/R186/R198 (per-layer produced/consumed index with edge type and declared-use column)
> — D2 :125–126

**Drafted replacement text.** Part A (declared-use column). With it, T3 §2.3's "declared use" can be transcribed from T2 rather than assigned by the instance (that is R201 in the T3 agenda). The registry-column half stays with R109.

**Cross-tier re-render hazards and open questions.** As listed under D-7.1.

## R198 — Per-layer produced/consumed assignment assembled by the reader (L5 case)

**Risk class:** structural.

**Register row.**

> Per-layer produced/consumed DP-contract assignment assembled by reader. Clause (T2 §13.3 item 6): "Upstream demand and downstream offers with field/grain/context/lineage contracts, named owners and tests" → T2 §7.1 gains a per-layer produced/consumed index, or §13.3 item 6 names where that index lives
>
> **State in register:** OPEN — §7.1 text half on the T2 reopen agenda; the registry-column half stays with R109 in P9 (D2 ruling 2026-09-27)
> — REG R198 :390 (severity BLOCKS_LAYER)

**Clause as it stands.** §7.1 as quoted under D-7.1; the T3 clause that asks for it:

> 6. Upstream demand and downstream offers with field/grain/context/lineage contracts, named owners and tests, **including which §3.4 presentation rows this layer carries and which fields it hands onward for them**.
> — T2 :682

**Remedy chosen by D2.**

> the §7.1 text halves of R181/R186/R198 (per-layer produced/consumed index with edge type and declared-use column)
> — D2 :125–126

**Drafted replacement text.** Part B (the per-layer index) or, as the register's own alternative, Part C (name where the index lives). The registry-column half stays with R109.

**Cross-tier re-render hazards and open questions.** As listed under D-7.1.


## Re-seal mechanics (apply once, after the agenda is decided)

- **Order and gates (D2 rule 3, rule 4).** Re-seal parent-before-child: T1, then T2, then T3. One version bump per document, after its cross-tier re-render pass and an independent review (Astra or Kimi K3). The documents carry `version: "FINAL"`, so the "bump" is a dated changelog entry in the convention the two earlier reopens used (T2 changelog :40 and T3 changelog :37, "REOPENED AND AMENDED (date, native ruling — …)"), plus a restamp of the document's fingerprint in `CAPABILITY_MANIFEST.json` (the identity of record, T3 frontmatter :8).
- **Closed agenda (D2 rule 1).** Anything found while editing becomes a new register row for a second round; it is not added here.
- **Re-render pass (D2 rule 2).** Every count, gate name and section number named under "cross-tier re-render hazards" below is grepped across tiers, the L0 and L1 instances, the tracker and the census in the same commit as the redline. The L0 instance (v3.0) and the five pilot briefs are test artefacts that the register says are regenerated after the freeze (REG frontmatter `what_is_a_test_artefact`), so their echoes are listed for completeness, not as blockers.
- **Nothing here edits a tier document.** This file is a draft held for J1 (plan §4.2 rows 4 and 7); the tier documents are redlined only after the strategist's N-4 decision on this agenda.
