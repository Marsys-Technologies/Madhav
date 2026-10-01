---
artifact: SUVARNA_REOPEN_AGENDA_T3
canonical_id: SUVARNA_REOPEN_AGENDA_T3
version: "1.2"
status: DRAFT-HELD-FOR-J1
produced_on: 2026-10-02
produced_in: "Exec Suvarna Engine, Track E lane E2 (queue id E2.1-design-003); drafted by a Sonnet drafter"
tier: 3
tier_document: "00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md (SEALED 2026-09-25; reopened once, 2026-09-26)"
rows: 17
row_ids: [R08, R09, R10, R65, R67, R68, R71, R74, R93, R120, R201, R221, R94, R140, R185, R192, R208]
agenda_rows: 12
closing_rows: 5
deferred_not_rows: [R131, R210, R214]
verdict_changing_rows: [R10, R65, R71, R221, R94, R140, R185]
decision: "N-4.T3, Strategic Suvarṇa (plan §4.2 J1 rows 4 and 7), decided together with the T1 and T2 agendas; closes E2.2 (R71) with the T3 re-seal"
sources:
  - "TRACK_E_BRIEF_v1_0.md §6 (the spec); SUVARNA_CAMPAIGN_PLAN_v1_5.md §4.2 (J1 rows 4 and 7), §5.1 (E2)"
  - "nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md D2 (ruling 2026-09-27), D3 (R71 text) and D5 rev. 2.1 (R221)"
  - "NIKASHA_CHANGE_REGISTER_v2_0.md (v2.8), the seventeen rows"
  - "the tier-3 document, the tier-1/2/4 documents and the L0 instance at origin/campaign/nikasha-test @ 2a78ec64d"
changelog:
  - "1.2 (2026-10-02): SS rulings folded, each marked SS direction to be confirmed at J1: new section Rows that change what counts as PASS (grid movement computed where the saved censuses allow, else not computable today) and one Decisions required at J1 table; R65 Option A is primary, Option B the fallback; R71 is an annotation and no verdict value is added (open question removed, annotation wording drafted); R221 consequential T3 :467 edit flagged for explicit authorisation."
  - "1.1 (2026-10-02): independent-review changes. R65 re-tagged VERDICT-CHANGING with Option B and the dependency on unsealed T4; R93 rule 2 quotes the register example; R221 open question 3 rewritten (catalog_provenance.py is on main, identical blob); R120 role placed in 3.2/3.3; R74 wording labelled; D3 citations relabelled; tracker line cited."
  - "1.0 (2026-10-02): first issue. Twelve agenda rows plus five rows that close with them; R131, R210, R214 listed as deferred, not rows. Drafted replacement text; no tier document edited."
---

# Reopen agenda — Tier 3 (layer definition and strategy template) — v1.0 DRAFT, held for J1

**Purpose.** The D2 ruling of 2026-09-27 authorised one reopen per sealed founding document on a reviewed row-to-clause agenda. This is the agenda for Tier 3, `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`. It holds **12 agenda rows** (R08, R09, R10, R65, R67, R68, R71, R74, R93, R120, R201, R221) and **5 rows that close with them** (R94, R140, R185 with R71; R192, R208 with R120) = 17 sections. R71, the last freeze-blocking contradiction (J1 row 4, plan item E2.2), is here, with D3's replacement text copied verbatim. **Seven sections are VERDICT-CHANGING** (R10, R65, R71, R221 and R71's closers R94, R140, R185); read those first. T3 re-seals last, after T1 and T2, because its §0.1, §2.2, §2.3, §2.4 and §2.6 inherit from clauses T2 changes (D2 rule 3). The agenda is closed once opened (D2 rule 1).

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
| R08 | T3 §5.2 :585 cites "§7"; §2.5 :365 sits after §2.7 :330 | Define a Part 6 "Corrections with gates" and cite it; move the §2.5 block before §2.6 (no renumbering) | structural |
| R09 | T3 §2.7 :358–359 (layer scope only) | Per-asset carriage table in §2.7 (D1/D2/D3 or `NO_DETECTOR` with reason; never N/A) | structural |
| R10 | T3 §1.1 :169–172 | Shared-table sentence: list once, name every producer, scope counts per producer (with R06) | **VERDICT-CHANGING** |
| R65 | T3 §5.2 Build row :539; changelog :37 ("six static checks") | Option A: align on nine (T4 §4.2 and the tracker say nine; makes sealed T3 depend on unsealed T4). Option B: record the six-plus-three split | **VERDICT-CHANGING** |
| R67 | T3 §5.4 test 5 :629 ("eight-row map") | "nine-row map" | wording-only |
| R68 | T3 :359 and :520 (`NO DETECTOR`) | `NO_DETECTOR` (the closed-set spelling) | wording-only |
| R71 | T3 §5.4 test 4 :628 and §2.2 `measured_by` :278 | D3's two replacement texts, verbatim | **VERDICT-CHANGING** |
| R74 | T3 §5.1 :503–506 | Add the ruling-11 clause ("ten, not eleven") | wording-only |
| R93 | T3 §3.2 :396–406 | Evidence → disposition rules and an explicit preserved-kernel row | structural |
| R120 | T3 §4.4 :476 | Reword the role bullet (no new bullet): three values, assigned per asset by the instance with a reason | structural |
| R201 | T3 §2.3 :296–299 | Name the source of declared use (T2 §7.1 column, then registry) | structural |
| R221 | T3 §0.1 :99–116 (and its echoes) | Re-scope to catalog units produced and closure position, derived, never judged | **VERDICT-CHANGING** |
| R94, R140, R185 | the R71 clauses, as seen from L1, L3, L4 | Close with R71 (D3) | **VERDICT-CHANGING** (inherited) |
| R192, R208 | T4 §0 `role` cites "layer §4.4" | Close with R120 | structural |

Deferred to a second reopen round, **not agenda rows**: R131, R210, R214 (listed at the end). In the D2 "proceed now" list and already closed on their non-sealed halves: R65 (tracker comment, CLOSED 2026-09-28), R68 (T4 :278, CLOSED 2026-09-28).

## Rows that change what counts as PASS

*SS direction, to be confirmed at J1.* This section holds the VERDICT-CHANGING rows of Tier 3, one block per row: the wording before and after, and which cells of the 9 × 127 grid would move. 

**How the movement was computed (and what the numbers are).** The grid is the nine gates (Ldgr, Idem, Earn, Null, Vocab, Carr, Narr, Dens, Build) by the 127 active assets: **1,143 cells**. On 2026-10-02 the worktree's `platform/scripts/governance/asset_census.py` rollup (`build_rollup_output`, with `load_asset_declarations()`) was run offline over the saved Track A censuses `/Users/Dev/suvarna-evidence/census/census_L0.json` … `census_L5.json` (inspector `2a78ec64d`, chart `482012f1-710e-4a25-994a-93821f5871aa`); no database, nothing written. Caution: the saved measurements predate the E6 detectors, so most gates read NO_DETECTOR today. Baseline cells by verdict: Ldgr NO_DETECTOR 57 · PASS 69 · PARTIAL 1; Idem PASS 110 · PARTIAL 11 · NO_DETECTOR 5 · FAIL 1; Earn, Null, Carr, Narr NO_DETECTOR 127 each; Vocab NO_DETECTOR 126 · FAIL 1; Dens FAIL 59 · PASS 40 · NO_DETECTOR 28; Build FAIL 53 · PARTIAL 50 · NO_DETECTOR 18 · ERRORED 4 · PASS 2. A number below is computed from those files; where a movement needs a detector or a declaration that does not exist yet, the row says "not computable today: needs …" and gives no number.

**R10 — shared tables in the layer instance (T3 §1.1).**
- *Before* (:169–172): inventory lists each asset's target table(s), row counts and so on; no statement on shared tables.
- *After:* `**Shared tables.** Where one table has several producers … an asset's row count is the rows it writes, never the table's total, and a table is not assigned to one asset by default (Data plane §13.3 item 2).`
- *Cells:* the same cells as T2 R06, **not additive**: Build gate, `Build.count_integrity`, upper bound **25 of 127** (all PASS on that check today; five tables named in more than one asset's `count_sql`: `brahma_class_priors` 2 assets, `brahma_ontology` 4, `classical_text_chunks` 2, `chart_facts` 10, `bodha_msr_signals` 7). Actual movement: **not computable today: needs** a detector comparing each producer's `count_sql` scope with the rows it writes (R22 universes or R109 registry columns).

**R65 — Build check count (T3 §5.2 Build row :539; changelog :37).** (*SS direction, to be confirmed at J1:* Option A primary.)
- *Before:* `six static checks (registered · contract · dispatchable target · DAG resolvable · count/integrity · completion honesty) plus a runtime state`.
- *After, Option A (primary):* `the nine read-only checks of the tier-4 template §4.2 (… · exercised · history · dependency liveness) plus a runtime state`.
- *Cells moved against today's rollup under Option A:* **0 of 127 Build cells.** `CRITERION_REGISTRY` already has nine Build criteria (`Build.registered`, `contract`, `target`, `dag`, `count_integrity`, `completion`, `exercised`, `history`, `dep_liveness`) and the Build cell already rolls up all nine; Option A makes the text say what the rollup does. Build today: FAIL 53 · PARTIAL 50 · NO_DETECTOR 18 · ERRORED 4 · PASS 2.
- *Fallback, Option B (six-plus-three), if T4 does not seal in the same pass:* if the Build gate were computed on the six named checks only, **64 of 127 Build cells would differ from today's rollup, every one upward**: PARTIAL→PASS 50, NO_DETECTOR→PASS 9, FAIL→PASS 2, FAIL→PARTIAL 2, NO_DETECTOR→PARTIAL 1 (Build PASS 2 → 63; by layer L0 19, L1 14, L2 16, L3 7, L4 3, L5 5). That is the size of the divergence between T3's text and the census if B were sealed and the census left computing nine; it is why B keeps T4 §4.2's three checks named and defined outside T3.

**R71 — [TRANSFERS] contradiction (T3 §5.4 test 4 :628; §2.2 `measured_by` :278).** (*SS direction, to be confirmed at J1:* an annotation, no verdict value added.)
- *Before:* `4. **Presentation parity** holds for the layer's served surface.` and `measured_by: presentation-parity test (Data plane §12.2): both renderings from the consumed reading package, no recomputation, …`.
- *After:* D3's two texts, verbatim (see the R71 section): test 4 becomes `Presentation fields carried` (a producer-field contract test run in the layer) with end-to-end parity and delivery sentinel [TRANSFERS], recorded as an annotation where the owner or its test is not built.
- *Cells moved in the nine-gate grid:* **0.** Test 4 is an acceptance test of a layer instance, not one of the 1,143 asset cells; the `Dens` gate and the closed verdict set are untouched. Instance effect: the L0 instance records test 4 as `UNMET` (L0 :658); how many of the six instances change is **not computable today: needs** the L1–L5 instances, which do not exist.

**R221 — §0.1 re-scoped (T3 §0.1 :99–116).**
- *Before:* `List the P-needs and V-journeys for which this layer is **necessary** …`, `measured_by: none — definitional`.
- *After:* the catalog units the layer's assets produce, and the layer's place in the necessity closure (`catalog_provenance.py --closure`), derived, never judged (see the R221 section).
- *Cells moved in the nine-gate grid:* **0.** §0.1 is the origin of the alignment test and of the necessity-based dispositions, not an asset gate. The register's own closure measurement (R85) puts 111 of 127 active assets in the closure and 16 outside; that is a necessity figure, not a cell movement. Which dispositions or struck sections change: **not computable today: needs** the re-rendered §0.1 of each layer instance (L1–L5 not written) and the :467 consequential edit authorised (below).

**R94, R140, R185 — the R71 clauses seen from L1, L3, L4.** Inherited from R71: grid cells moved **0**; instance effect as R71.

## Decisions required at J1

*SS direction, to be confirmed at J1.* One table. R221 stays open exactly as drafted; the other rows are the remaining open questions of this agenda.

| Row | Decision | Options | Recommendation |
|---|---|---|---|
| R221 | **Explicit authorisation of the consequential edit at T3 :467** (§4.4 bullet 1, "the P-needs and V-journeys the asset serves (from 0.1, narrowed)"), and of the other echoes listed in the R221 section (T3 :123, :149, :182, :279, :306, :335, :461, :679; T4 :66, :90) | authorise the consequential edits with R221; hold R221 to round two (D2 names §0.1 only, so without authorisation :467 is out of scope) | Authorise: without the :467 edit the asset-brief derivation loses its first row. Needs SS's explicit word at J1; the draft does not apply it |
| R221 | Closure figures in the template | cite the instrument (`catalog_provenance.py --closure`, already on `main`) at a named revision; copy figures | Cite the instrument and revision, never the figures |
| R93 | Evidence → disposition rules 1–5 | confirm; supply rules for P, Q, C, H; defer to round two | Confirm 1–4 as written (the register's examples); defer P/Q/C/H rules; rule order U before E confirmed |
| R120 | Criterion for assigning `role` | instance assigns with a reason (drafted); SS supplies a criterion | As drafted |
| R65 | A or B | A primary, B fallback | **A** (*SS direction*); B only if T4 §4.2 does not seal in the same pass |
| R08 | May Part 6 carry DOCUMENT rows? | yes (L0 precedent); no (LAYER and SEALED PARENT only) | No: a document-level finding is fixed, not recorded (§5.4) |
| R09 | Is a pure-carrier asset `N/A` or `NO_DETECTOR` for Carr? | `NO_DETECTOR` (drafted; T4 says Carr applies always); `N/A` (T4 change) | `NO_DETECTOR` |
| R71 | Vacuous test 4 for a layer that owns no §3.4 field | `N/A`; pass | `N/A` with the reason, as T4 §4 requires for any N/A |

## R08 — §5.2 cites a "§7" the template never defines; §2.5 is ordered after §2.7

**Risk class:** structural.
**Register row.**

> §5.2 cites a "§7" the template never defines; §2.5 is ordered after §2.7
>
> **State in register:** **OPEN** — reopen needed: define the corrections section, fix the order — T3 reopen agenda (D2 ruling 2026-09-27)
> — REG R08 :133 (severity DEGRADES)

**Clause as it stands.**

> author would have to invent it. Report unfillable rows in §7 as corrections with gates.
> — T3 :585

> ### 2.6 · Vocabulary conformance
> — T3 :313

> ### 2.7 · Source carriage and reproduction — did we transmit it faithfully?
> — T3 :330

> ### 2.5 · Edges and order
> — T3 :365

> The template's §5.2 tells an instance to "report unfillable rows in §7", but the template defines no §6
> or §7. Recorded here rather than silently renumbered.
> — L0 :671–672

> | C-7 | template defines no §6/§7 though §5.2 cites §7; §2.5 is ordered after §2.7 | **template** (tier 3 is sealed — this is a reopen request, not an edit) | the L1 instance, which would inherit both |
> — L0 :682

**Remedy chosen by D2.**

> R08 (§5.2's "§7" defined; §2.5/§2.7 order)
> — D2 :128

**Chosen here.** (a) Define the missing section as **Part 6 · Corrections with gates**, which is what the L0 instance already did "rather than silently renumbered", and point §5.2 at it. (b) Fix the order by **moving the §2.5 block before §2.6**, not by renumbering: §2.6 and §2.7 are cited by number in the instances, the tracker, T4 (T4 :102, row 13 cites "layer §2.7") and the register, so renumbering would create echoes where moving creates none.

**Drafted replacement text.**
(a) New Part 6, after Part 5 (after :668) and before "Adapting the template per layer":

~~~~
## Part 6 · CORRECTIONS WITH GATES

```
inherits:    §5.2 (the gate map: a row the instance cannot fill), §5.4 (the two guards on ACCEPT_WITH_CORRECTIONS)
measured_by: the table below — every row names what it is about and the gate it blocks; nothing is counted that is not a row
traces_to:   0.4 — a correction that names no gate is not a correction (§5.4, guard 1)
```

What the instance could not fill, and what its review found, recorded rather than silently repaired or silently renumbered. One row per correction:

| # | correction | about the DOCUMENT, the LAYER, or a SEALED PARENT (a reopen request, not an edit) | gate it blocks |
|---|---|---|---|
| | | | |

A finding about the layer that the document correctly records is a work packet with a detector (§5.4). A finding about a sealed parent is a request to reopen it, never a local edit.
~~~~

(b) §5.2, the last sentence of the gate-map paragraph (:585):

~~~~
old: Report unfillable rows in §7 as corrections with gates.
new: Report unfillable rows in Part 6 as corrections with gates.
~~~~

(c) "How to use this template" kind table (:61): `| 1, 3, 4 | **Strategy** …` becomes `| 1, 3, 4, 6 | **Strategy** …` (Part 6 changes every campaign pass).

(d) Order: cut the §2.5 block (:365–375, heading through its last paragraph) and paste it between §2.4 and §2.6, i.e. before :313. No text changes.

**Cross-tier re-render hazards.**
- The L0 instance's Part 6 preamble (L0 :671–672) says the template defines no §6 or §7; it and its row C-7 become stale on re-render. Its §2.5 sits after §2.7 (L0 :430) and re-renders in order.
- T3 :674 "What changes per layer is the *content* of Parts 0-4" and :60–62 kind table: check Part 6 is consistent with them.
- T4's pilot clause says a brief "may register gaps in §5" and write certification records in "§7" (T4 :82–83): those are T4's own sections, not T3's; do not conflate when grepping "§7".
- Every citation of "§2.5" keeps its number.

**Open questions.**
1. T3 §5.4 says a document-level finding "is never deferred" yet the L0 precedent lists DOCUMENT rows in Part 6. The draft keeps L0's three kinds but drops "DOCUMENT" from the closing sentence; SS decides whether Part 6 may carry document rows at all (they then block acceptance) or only LAYER and SEALED PARENT rows.
2. Part number: 6 follows the L0 instance. Calling it Part 7 would leave an empty Part 6 and is not recommended.

## R09 — §2.7 assigns the carriage check at layer scope only

**Risk class:** structural.
**Register row.**

> §2.7 assigns the carriage check (a/b/c) at layer scope only; no instance can fill the per-asset row 13
>
> **State in register:** **OPEN** — reopen: §2.7 gains a per-asset assignment table, or the template states the brief author chooses and records why. CONFIRMED on L1–L5 in P4 (R92, R112, R144, R190, R204) — T3 reopen agenda (D2 ruling 2026-09-27)
> — REG R09 :134 (severity BLOCKS_LAYER)

**Clause as it stands.**

> For each obligation the layer owns (§2.4), state which of a–c applies, the detector, and its current
> result — `PASS` / `FAIL` / `PARTIAL` / **`NO DETECTOR`**. `NO DETECTOR` is never a pass; it is a gap.
> — T3 :358–359

> | 13 | **the Jyotish concepts it touches**, named, each with the carriage check it invites (a/b/c) | | layer §2.7, §4.4 |
> — T4 :102

> | C-9 | row 13 of the asset-brief inheritance (the concepts an asset touches, each with the carriage check it invites) **cannot be filled from this instance** — §2.7 names the three checks at layer scope and assigns none per asset. Pilot 1 had to choose D1 itself | document (this instance) | the next asset brief |
> — L0 :685

**Remedy chosen by D2.**

> R09 (§2.7 per-asset carriage table)
> — D2 :128–129

D2 chose the table (the register's other option, "the brief author chooses and records why", is not taken). Layer confirmations that close with it if SS says so: R92, R112, R144, R190, R204 (the register lists these in R09's state).

**Drafted replacement text** — a paragraph and table inserted after :359 (before "A reference layer is where this matters most", :361):

~~~~
**Per asset.** The checks are also assigned per asset, so that every asset brief can fill its Jyotish-concepts row (§4.4; tier-4 §0.1 row 13). The instance carries one row per asset listed in 1.1:

| asset | what it restates from a source, or computes | the one carriage check it invites — D1 source correspondence · D2 witness carriage · D3 independent re-derivation (§5.2's menu; checks a, b, c above) | detector | result (`PASS` / `FAIL` / `PARTIAL` / `NO_DETECTOR`) |
|---|---|---|---|---|

One check per asset: the one that fits what the asset actually does (§5.2). An asset to which none applies is recorded `NO_DETECTOR` with the reason. A row is never blank and a missing detector is never a pass.
~~~~
**Cross-tier re-render hazards.**
- Spelling: the draft uses `NO_DETECTOR`; apply R68 first so §2.7 and the new table agree.
- T4 §4 `Carr` row (T4 :229) says the gate applies "always"; the draft therefore offers `NO_DETECTOR`, not `N/A`, for an asset that restates nothing. T4 :236–238: "a bare N/A is a gap".
- T3 §5.2 carriage menu (:544–551) and gate map row **Carr** (:579) — consistent; T4 §0.1 row 13 gets its source.
- L0 instance C-9 and the five pilot briefs (Pilot 1 chose D1 itself).

**Open questions.**
1. Should an asset that neither restates a source nor computes anything (a pure carrier) be `N/A` rather than `NO_DETECTOR`? That would change the Carr verdict space and needs a T4 change; the draft does not take it.
2. Checks are labelled a–c in §2.7 and D1–D3 in §5.2; the column header equates them by name. A reader may want the equivalence stated once.

## R10 — §1.1 cannot express a shared table with several producers

**Risk class: VERDICT-CHANGING** (with R06 in the T2 agenda): it changes what an asset's row count and `count_sql` are measured over for any asset sharing a table (Build check 5, inventory counts).
**Register row.**

> §1.1 inventory cannot express a shared table with several producers
>
> **State in register:** **OPEN** — same reopen as R08/R09 — T3 reopen agenda (D2 ruling 2026-09-27)
> — REG R10 :135 (severity BLOCKS_LAYER)

**Clause as it stands.**

> Every asset and service the layer owns: registered, writer-backed, service (no table by design),
> residual, shared, historical. For each: target table(s) — a **set**, not one pointer, for multi-table
> assets — row counts in production, columns, contract fields live, last build, and whether current code
> on any live head differs from what is deployed.
>
> Three sources are reconciled, not one read: registry vs seed vs pin. Where they disagree, say so; the
> disagreement is itself a finding.
> — T3 :169–175

> | C-10 | §1.1 models one `target_table` per asset and cannot express a **shared table with several producers**. `brahma_ontology` has four (`l0_ontology.py` 414 rows / 14 classes, plus `l0_yogas.py`, `l0_doshas.py`, `l0_dasha_systems.py` supplying 327 more), and `bg_ontology`'s `count_sql` credits it with all 741 | document (this instance) + layer | the first asset certification |
> — L0 :686

**Remedy chosen by D2.**

> R10 (§1.1 multi-producer inventory, with R06)
> — D2 :129

**Drafted replacement text** — a paragraph inserted after :172 (after "…differs from what is deployed."), mirroring the T2 sentence for R06:

~~~~
**Shared tables.** Where one table has several producers (one table, several writers), list the table once and name every producer (writer module and asset id). Report each producer's own rows and the scope of its `count_sql` separately: an asset's row count is the rows it writes, never the table's total, and a table is not assigned to one asset by default (Data plane §13.3 item 2).
~~~~
**Cross-tier re-render hazards.** The T2 sentence (R06) must be sealed first or in the same pass; `inherits:` at :164 already cites §13.3 item 2. Register rows R95, R103, R136, R205 confirm the gap on L1, L2, L3, L5. T4 §1 "Storage" (T4 :127–128: "rows by the asset's **own `count_sql`**") agrees.

**Open questions.** Whether the four L0 producers' counts now change `bg_ontology`'s Count verdict is a consequence to expect, not to avoid; SS should know the sentence makes the current 741-row credit (L0 C-10) a finding.

## R65 — Build check count: T3 says six static checks, T4 lists nine

**Risk class: VERDICT-CHANGING.** Option A fixes, in the sealed text, that the Build gate includes the run-record checks 7–9 of T4 §4.2; check 8 (`history`) FAILs when the latest run errored or aborted. The census rollup already counts all nine Build criteria, so against today's rollup no cell moves (see "Rows that change what counts as PASS"); the row still decides what Build PASS means in the sealed template. *SS direction, to be confirmed at J1:* Option A is primary, because the combined reopen re-seals T3 and T4 together.
**Register row.**

> Build check-count disagreement: T3 §5.2/changelog and the tracker GATES comment say "six static checks"; T4 §4.2 lists nine. Align on nine, or explicitly record "T3 names the six static checks; T4 adds three run-record checks"
>
> **State in register:** OPEN — T3 half (§5.2/changelog) on the T3 reopen agenda, remedy chosen on the agenda; tracker-comment half proceeds now (D2 ruling 2026-09-27) Tracker-comment half CLOSED 2026-09-28 (wave 3, W3-1_REVIEW). T3 half unchanged — remains on the reopen agenda per the D2 ruling.
> — REG R65 :192 (severity BLOCKS_LAYER)

**Clause as it stands.**

> | **Build** · buildability | the orchestrator can dispatch the asset and a triggered rebuild produces the correct result — six static checks (registered · contract · dispatchable target · DAG resolvable · count/integrity · completion honesty) plus a runtime state proved by `ctx.dry_run`, never by `state = 'lit'` | — |
> — T3 :539

> six read-only static checks plus a runtime state that `ctx.dry_run` establishes without any production write
> — T3 :37

> All nine checks run read-only, and all nine can return false:
> — T4 :268

> | 8 | **history** | its recorded outcomes: `state ∈ complete / error / aborted / queued` and `disposition`. FAIL if the most recent run errored or aborted; PARTIAL if it has errored before and the latest run completed; N/A if never run (check 7 owns that). Measured: **13 of 40 L0 assets have errored or aborted**, 7 of them with the *identical* error — `post-write integrity check failed: integrity_check_sql → False` — which is one systemic finding, not seven |
> — T4 :279

T4's status, which matters for Option A:

> status: DRAFT_PENDING_REVIEW
> — T4 :5

**Remedy chosen by D2.**

> R65's T3 half (§5.2/changelog check count — "align on nine" or "record the six-plus-three split", chosen on the agenda)
> — D2 :129–130

**Two options. Option A, align on nine, is PRIMARY (SS direction, to be confirmed at J1: the combined reopen re-seals T3 and T4 together). Option B is the fallback if T4 does not seal in the same pass.** **Option A** (drafted below): the tier that defines the checks (T4 §4.2: "All nine checks run read-only, and all nine can return false"), T4's gate table (:232) and the tracker already say nine; the tracker's Build comment (`00_ARCHITECTURE/control/asset_elevation_tracker.py` :73 on `campaign/nikasha-test`) reads "nine static checks, all read-only (R65: aligned on nine per T4 §4.2; D2 reopen carries the T3 §5.2/changelog half)". Cost: sealed T3 depends on T4 §4.2, which is DRAFT_PENDING_REVIEW today, and the sealed Build gate includes check 8, which FAILs on an errored latest run; under SS's direction both seal in one pass, so T3 does not depend on an unsealed document at J1. Do not seal T3 under Option A unless T4 §4.2 is accepted in the same pass. **Option B, record the six-plus-three split** (the register's alternative, fully drafted below as the fallback): T3 keeps naming the six static checks and says that tier-4 §4.2 adds three run-record checks (exercised, history, dependency liveness) that it, not T3, defines; the sealed gate text does not change what Build PASS requires, but T3 and T4 then count differently by design and say so. The `ctx.dry_run` runtime state is separate in T4 (:286–290) under both options.

**Drafted replacement text.**
Option A, (a) §5.2 Build row (:539), inside the cell:

~~~~
old: six static checks (registered · contract · dispatchable target · DAG resolvable · count/integrity · completion honesty) plus a runtime state
new: the nine read-only checks of the tier-4 template §4.2 (registered · contract · dispatchable target · DAG resolvable · count/integrity · completion honesty · exercised · history · dependency liveness) plus a runtime state
~~~~

Option B (fallback), §5.2 Build row (:539), inside the cell:

~~~~
old: six static checks (registered · contract · dispatchable target · DAG resolvable · count/integrity · completion honesty) plus a runtime state
new: six read-only static checks (registered · contract · dispatchable target · DAG resolvable · count/integrity · completion honesty), which this template names, plus three run-record checks (exercised · history · dependency liveness) that the tier-4 template §4.2 adds and defines, plus a runtime state
~~~~

(b) Under Option A (primary), changelog :37 is history; annotate, do not rewrite (T2 precedent, T2 :45):

~~~~
old: six read-only static checks plus a runtime state that `ctx.dry_run` establishes without any production write
new: six read-only static checks [CORRECTED on the T3 reopen: nine read-only checks — these six plus exercised · history · dependency liveness, tier-4 §4.2] plus a runtime state that `ctx.dry_run` establishes without any production write
~~~~

**Cross-tier re-render hazards.** T4 :34 (changelog) and T4 :245 (`measured_by: six static checks …`) still say six: that is register row R252 (OPEN, not sealed, not on this agenda); fix it in the same pass or T3 and T4 will disagree again. T3 :518–521 and T4 :13, :232 say "nine gates"/"nine checks": consistent. Grep "six static" across tiers, instances and the tracker.

**Open questions.** 1. *SS direction, to be confirmed at J1:* A primary, B fallback. 2. The trigger for the fallback: T4 §4.2 not accepted in the same pass (J1 row 8 accepts Tier 4). 3. The sequencing with R252.

## R67 — §5.4 test 5 says "eight-row map"; the map has nine rows

**Risk class:** wording-only.
**Register row.**

> T3 §5.4 test 5: "§5.2's eight-row map" → "§5.2's nine-row map" (the map has nine rows)
>
> **State in register:** OPEN — T3 reopen agenda (D2 ruling 2026-09-27)
> — REG R67 :194 (severity BLOCKS_LAYER)

**Clause as it stands.**

> 5. **The gate map exists.** §5.2's eight-row map from gate to feeding section is written out in the
>    instance. An instance missing the map fails this test outright — the map is the derivability test
>    in tabular form, and demanding it without checking for it is how it goes unwritten.
> — T3 :629–631

> | gate | the section a brief author reads to answer it | what the instance must supply there |
> |---|---|---|
> | **Ldgr** | §2.3 contracts produced and consumed, with declared use | the asset's upstream `fact_id` sources, named |
> | **Idem** | §2.5 edges and order; §4.1 order and baseline | the asset's natural key, so "replaces its own rows" is decidable |
> | **Earn** | §2.4 coverage obligations and their states | which of the asset's emitted states are claims, and what would falsify each |
> | **Null** | §2.4 (the state vocabulary); §1.4 evidence states | the asset's own convention for an underivable value |
> | **Vocab** | §2.6 vocabulary conformance | the classes this asset owns or consumes, and the authority for each |
> | **Carr** | §2.7 source carriage and reproduction; §4.4's Jyotish-concepts row | what the asset restates or computes, and which menu item each invites |
> | **Narr** | §2.2 presentation fields | whether the asset emits prose, and which fields carry it |
> | **Dens** | §2.2 presentation fields; §3.4 the served boundary | whether the asset reaches a served surface, and which |
> | **Build** | §2.5 edges and order; §1.1 (writer, target table, build record); §4.3 generation and rollback | the asset's writer and registered id, its declared target, its edges, and its build record |
> — T3 :572–582

**Remedy chosen by D2.**

> R67
> — D2 :130

**Drafted replacement text** (:629):

~~~~
old: 5. **The gate map exists.** §5.2's eight-row map
new: 5. **The gate map exists.** §5.2's nine-row map
~~~~

**Cross-tier re-render hazards.** Grep "eight-row", "eight gates" across tiers and instances: T4 §4 heading/inherits already say nine; the L0 instance's `§4 · The eight gates` pilots are listed in T5V V17 (test artefacts). The `Build` row is the ninth row of the map (:582).
**Open questions.** None.

## R68 — Verdict spelling drift: `NO DETECTOR` against the closed set `NO_DETECTOR`

**Risk class:** wording-only (no tool matches the spaced form; the ledgers, tracker and census already use `NO_DETECTOR`, T5V A2).
**Register row.**

> Verdict spelling drift: T3 :359 and :520 use `NO DETECTOR` (space); T4 :278 uses bare `NA` — normalize to the closed set `NO_DETECTOR` / `N/A` that ledgers, tracker, census already use
>
> **State in register:** OPEN — T3 half (:359/:520) on the T3 reopen agenda; T4 half proceeds now (D2 ruling 2026-09-27) T4 half (:278) CLOSED 2026-09-28 (wave 3, W3-1_REVIEW). T3 half unchanged — remains on the reopen agenda per the D2 ruling.
> — REG R68 :195 (severity DEGRADES)

**Clause as it stands.**

> result — `PASS` / `FAIL` / `PARTIAL` / **`NO DETECTOR`**. `NO DETECTOR` is never a pass; it is a gap.
> — T3 :359

> claim with a detector that could return false; a gate without one is `NO DETECTOR`, which is an honest
> — T3 :520

> verdict ∈ { PASS | FAIL | PARTIAL | NO_DETECTOR | N/A }     — closed set, these spellings exactly
> — T3 :611

**Remedy chosen by D2.**

> R68's T3 half (:359/:520 spelling)
> — D2 :130–131

**Drafted replacement text.**

~~~~
old (:359): result — `PASS` / `FAIL` / `PARTIAL` / **`NO DETECTOR`**. `NO DETECTOR` is never a pass; it is a gap.
new (:359): result — `PASS` / `FAIL` / `PARTIAL` / **`NO_DETECTOR`**. `NO_DETECTOR` is never a pass; it is a gap.

old (:520): claim with a detector that could return false; a gate without one is `NO DETECTOR`, which is an honest
new (:520): claim with a detector that could return false; a gate without one is `NO_DETECTOR`, which is an honest
~~~~

**Cross-tier re-render hazards.** The T3 changelog (:41, history) also writes "NO DETECTOR"; leave it. T4 :278's bare `NA` was the T4 half (CLOSED 2026-09-28). Apply before R09 (whose new table uses the underscore form).

**Open questions.** The list at :359 omits `N/A` (§5.3's closed set has five values). Adding it would change the verdict space of §2.7 and is not drafted.

## R71 — The [TRANSFERS] contradiction (the last freeze-blocking clause row)

**Risk class: VERDICT-CHANGING.** The replacement turns acceptance test 4 from "parity holds" into a producer-field contract test plus a recorded `[TRANSFERS]-pending` state that is neither a pass nor a block. Closes plan item E2.2 and J1 row 4 with the T3 re-seal.
**Register row.**

> **[TRANSFERS] contradiction**: T2 §1 (:83-85, "a layer plan does not inherit it as its own work") + §12.2 (:614, Presentation parity [TRANSFERS]) vs T3 §5.4 test 4 (:628, "Presentation parity holds for the layer's served surface") — reword T3 test 4 to carry parity as a named [TRANSFERS] row, or un-mark it in T2
>
> **State in register:** OPEN — four layers hit this (R94 L1, R119 L2, R140 L3, R185 L4). Remedy fixed by D3 ruling 2026-09-27: T3 §5.4 test 4 → "Presentation fields carried" (producer-field contract test, binding; end-to-end parity and Delivery sentinel [TRANSFERS] — where the owner or its test is not built, record `[TRANSFERS]-pending` with obligation, owner and dependency, never a pass, never a block for the transferred part alone; where the owner runs it, link the result) and §2.2 `measured_by` re-worded the same way; the same tag at T2 §13.3 items 1/6 and T4 §1.2. Lands on the T3 reopen agenda (D2)
> — REG R71 :198 (severity BLOCKS_FREEZE)

**Clause as it stands** — the T3 clauses, and the T2 clauses they contradict:

> 4. **Presentation parity** holds for the layer's served surface.
> — T3 :628

> measured_by: presentation-parity test (Data plane §12.2): both renderings from the consumed reading package, no recomputation, identical finding / confidence / uncertainty
> — T3 :278

> Every obligation in this document that belongs to one of them is marked **[TRANSFERS]** — it moves to
> that plane's artefact, unchanged in substance, when that plane is elevated. A [TRANSFERS] obligation is
> not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work.
> — T2 :83–85

> | Presentation parity **[TRANSFERS]** |
> — T2 :614

> | Delivery sentinel **[TRANSFERS]** |
> — T2 :621

**Remedy chosen by D3 (the ruling; copied, not paraphrased).**

> - **The data layer must prove retention and hand-off of its assigned presentation fields.** T2 §3.4
>   makes this a data obligation, and it stays binding: every §3.4 field the layer owns is present in
>   its produced contracts, by contract test. "Never a block" never excuses a missing field.
> - **End-to-end Presentation parity and Delivery sentinel remain owned by the receiving plane**
>   ([TRANSFERS], T2 §12.2). Where that owner or its test is not built, the instance records
>   `[TRANSFERS]-pending — <obligation>; owner: <plane>; depends on: <artefact>` — no pass, and no block
>   on the instance for the transferred part alone. This does not discharge product acceptance. Where
>   the owner can run the test, its result is linked, never inherited as the layer's own acceptance:
>   the existence of a built plane is not an ownership assignment.
> — D2 :169–177 (D3 ruling, in the D2 file)

> T3 §5.4 test 4 → "4. **Presentation fields carried.** Every §3.4 field this layer owns (§2.2) is
> present in its produced contracts — a contract test, run here. End-to-end Presentation parity and
> Delivery sentinel are [TRANSFERS] (Data plane §12.2): where their owner or its test is not built,
> record `[TRANSFERS]-pending` with the obligation, owner and dependency — never a pass, never a block
> on this instance for the transferred part alone, never an invented verdict; where the owner runs it,
> link the result."
>
> T3 §2.2 `measured_by:` → "producer-field carriage test — each §3.4 field this layer owns is present in
> its produced contracts; the presentation-parity test itself (Data plane §12.2) is [TRANSFERS] and is
> linked when its owner runs it, never run as this layer's own acceptance".
> — D2 :181–190 (D3 replacement texts, in the D2 file)

> The same tag is applied at every inheritance point R119 names (T2 §13.3 items 1 and 6; T4 §1.2), so
> the class is fixed, not one row. R94, R119, R140 and R185 close with R71.
>
> — D2 :192–194 (D3, in the D2 file)

**Drafted replacement text.** Both replacements are D3's, character for character (extracted by script from the D3 text in the D2 file, :181–190):

(a) §5.4 test 4 (:628):

~~~~
4. **Presentation fields carried.** Every §3.4 field this layer owns (§2.2) is present in its produced contracts — a contract test, run here. End-to-end Presentation parity and Delivery sentinel are [TRANSFERS] (Data plane §12.2): where their owner or its test is not built, record `[TRANSFERS]-pending` with the obligation, owner and dependency — never a pass, never a block on this instance for the transferred part alone, never an invented verdict; where the owner runs it, link the result.
~~~~

(b) §2.2 `measured_by:` (:278):

~~~~
measured_by: producer-field carriage test — each §3.4 field this layer owns is present in its produced contracts; the presentation-parity test itself (Data plane §12.2) is [TRANSFERS] and is linked when its owner runs it, never run as this layer's own acceptance
~~~~

(c) **Annotation wording and its status** (*SS direction, to be confirmed at J1: an annotation, not a verdict value; no verdict value is added*). In the layer instance, on test 4 and on the asset brief's §2.2 and `Dens` rows, the record reads:

~~~~
test 4 — producer-field carriage: PASS | FAIL | PARTIAL | NO_DETECTOR
annotation (not a verdict): [TRANSFERS]-pending — <obligation>; owner: <plane>; depends on: <artefact>
~~~~

and one sentence is added to §5.3 after the closed-set line (:611): 
~~~~
A `[TRANSFERS]-pending` record (§5.4 test 4) is an annotation written beside a verdict, never a verdict: the set above is unchanged.
~~~~
The annotation is free text. It is not written to `asset_certs.jsonl`, not read by the tracker's `VERDICTS`, not emitted by the census, and T3 §5.3's closed set (`PASS | FAIL | PARTIAL | NO_DETECTOR | N/A`) is untouched.

(d) The same tag at the other inheritance points: T2 §13.3 items 1 and 6 and the DP rows (R119, T2 agenda); T4 §1.2 (D2 "proceed now").

**R94, R140 and R185 close with this row** (D3: "R94, R119, R140 and R185 close with R71"); each has its own section below.

**Cross-tier re-render hazards.**
- T2 (R119, R89): the "owns" in test 4 reads T2 §3.4's new "Carried by layer" column; the "producer-field carriage test" is defined in T2 only if R119 (d) is kept. Seal T2 first (D2 rule 3).
- T3 §2.2's body (:282–286) and the gate map's `Dens` row (:538, :581) do not mention parity; no change.
- Instances: L0 :329 (`measured_by: presentation-parity test … NOT RUN`), :341, :465, :525, :551, :658 ("UNMET"), :681 (C-6) all record parity as a layer test; they re-render to a producer-field result plus `[TRANSFERS]-pending`.
- The ledger/tracker: no verdict value is added (SS direction, to be confirmed at J1).

**Open questions.**
1. D3's test-4 text says "run here" for a contract test; where no §3.4 field is owned by the layer (a pure reference layer) the test is vacuous. State whether that is `N/A` or a pass (not drafted).
2. Whether "product acceptance" (D3: "This does not discharge product acceptance") needs a pointer in T1 §14 is a T1 question outside this agenda.

## R74 — "Ten obligations": T3 §5.1 lists ten with no reason for omitting Domain correctness

**Risk class:** wording-only.
**Register row.**

> "Ten obligations": T3 §5.1 lists ten with no reason for omitting Domain correctness; T1 §14 has 11 rows; only T2 §13.3 carries the reconciliation. Add the ruling-11 clause to T3 §5.1
>
> **State in register:** OPEN — T3 reopen agenda (D2 ruling 2026-09-27)
> — REG R74 :201 (severity DEGRADES)

**Clause as it stands.**

> The ten obligations are the product's, not the layer's: source and domain fidelity · computational
> correctness · concept and relationship completeness · interpretive fidelity · distinctive
> understanding · consumer understanding · temporal integrity · predictive performance · delivery
> fidelity · operational honesty. A layer scores on the subset its 0.2 row names.
> — T3 :503–506

> **Ten, not the parent's eleven, and deliberately:** `Domain correctness` is not a data-plane obligation
> (native ruling, 2026-09-25; data plane §13.3 item 1). Do not "correct" this count upward. What a layer
> does owe is §2.7's carriage and reproduction.
> — T3 :392–394

> | **Domain correctness** |
> — T1 :587

> **Ten, not eleven, and deliberately so:**
> — T2 :666

**Remedy chosen by D2.**

> R74 (§5.1 ruling-11 clause)
> — D2 :132

**Drafted replacement text** — appended to the paragraph ending at :506, built on T3 §3.1's sentence (:392–394); the phrases "the product's §14 table carries eleven rows", "discharged above the data plane" and "scored on no data-plane layer" are new wording (taken from T1 :587 and T2 :666), and §3.1's closing sentence is kept:

~~~~
**Ten, not the parent's eleven, and deliberately:** the product's §14 table carries eleven rows; `Domain correctness` is discharged above the data plane (native ruling, 2026-09-25; data plane §13.3 item 1) and is scored on no data-plane layer. Do not "correct" this count upward. What a layer does owe is §2.7's carriage and reproduction.
~~~~
**Cross-tier re-render hazards.** None to change: §3.1 (:392–394) and T2 :666 already say it; T4 :91 already says "ten, not eleven". Grep "eleven" for consistency.
**Open questions.** None.

## R93 — No rule maps census evidence to a disposition; the preserved kernel is not named

**Risk class:** structural (it changes how dispositions are reasoned, not any gate verdict).
**Register row.**

> Per-asset disposition (P/I/E/Q/C/H/R/U) and the preserved kernel; no rule maps census evidence to a disposition. Clause (T3 §4.4): "- its disposition and its "must add" list (3.2, 3.3) … - **the preserved kernel** — what of the asset must survive any rebuild unchanged (from 3.2)" → T3 §3.2 gains an evidence→disposition decision rule (e.g. exercised + served + history FAIL ⇒ E; exercised + 0 rows + 0 modules ⇒ U pending §0.1); §3.2 names each preserved kernel explicitly (table span/key, algorithm, conventions)
>
> **State in register:** OPEN — T3 reopen agenda (D2 ruling 2026-09-27)
> — REG R93 :265 (severity BLOCKS_LAYER)

**Clause as it stands.**

> ### 3.2 · Per asset — disposition
>
> For every asset and service in 1.1, one of the data plane's eight dispositions, with the evidence from
> Part 1 that justifies it:
>
> **P** preserve · **I** integrate · **E** enrich/correct · **Q** qualify/limit authority ·
> **C** consolidation candidate · **H** historical/restricted · **R** retire after migration ·
> **U** unresolved use
>
> No quota for keeping or removing. Smallest sufficient change. A whole asset can be preserved while one
> score, fallback or narration rule is replaced.
> — T3 :396–406

> - **the preserved kernel** — what of the asset must survive any rebuild unchanged (from 3.2)
> — T3 :477

> - Any asset ≈ 0 on all three terms is a candidate for disposition **R** or **H** in Part 3 — a
>   candidate, not a verdict; "lack of a caller in a bounded search is not redundancy." **This rule does
>   not apply to a reference layer:** there, an asset is retired only for failed fidelity (inauthentic,
>   unsourced, wrongly identified, superseded by a corrected authority), never for lack of a reader.
> - Any asset with a large individual term and no synergistic term is a candidate for **I** (integrate).
> — T3 :244–248

**Remedy chosen by D2.**

> R93 (§3.2 evidence→disposition rule and preserved kernels)
> — D2 :132–133

**Drafted replacement text** — inserted in §3.2 after the list of the eight dispositions (after :403) and before "No quota for keeping or removing." The rules reuse T3 §1.5 and data plane §10.1; the two examples are the register's own and are marked as such:

~~~~
**Evidence → disposition.** The disposition follows from the Part 1 evidence, and the instance cites, for every asset, the evidence rows it rests on. Apply in order; the first rule that matches governs; none is a quota.

1. **U** when the evidence is incomplete — exercised + 0 rows + 0 modules ⇒ U pending 0.1. Lack of a caller in a bounded search is not redundancy.
2. **E** when the asset is exercised, served and a recorded check fails — exercised + served + history FAIL ⇒ E.
3. **I** when its individual term is large and its synergistic term absent (1.5).
4. **R** or **H** only as candidates when the asset is about zero on all three terms (1.5); **R** only on the data plane's conditions (§10.1 item 7: identified successor, caller/runtime/audit/history analysis, compatibility, provenance transfer, reversible migration), and never for a reference layer for lack of a reader.
5. **P**, **Q**, **C** as the data plane defines them (§10.1); where rules 1–4 do not decide, the instance states the evidence it used. There is no default disposition.

**The preserved kernel.** For every asset not disposed **R**, §3.2 names its preserved kernel as a row — table span and natural key · algorithm · conventions — so that what must survive any rebuild unchanged is explicit and everything else may change (4.4).

| asset | disposition | evidence rows matched | preserved kernel (table span and natural key · algorithm · conventions) |
|---|---|---|---|
| | | | |
~~~~
**Cross-tier re-render hazards.** §4.4 (:477) and T4 §0.1 row 12 ("the preserved kernel … from layer §3.2", T4 :101) now have a source; T4 row 8 (disposition) too. T2 §10.1 is unchanged and is the definitions' authority.

**Open questions.**
1. Rules 1 and 2 are the register's two examples, reproduced as written ("exercised + served + history FAIL ⇒ E; exercised + 0 rows + 0 modules ⇒ U pending §0.1"). Note that T4 check 8, `history`, is about run outcomes (T4 :279), not about content, so rule 2 as the register words it is a build-history rule; whether content failures also give E is not stated by any source. The register gives no examples for P, Q, C or H, and the draft invents none (B.10). SS or a domain owner may want those rules supplied before the freeze or deferred to round two.
2. Rule order matters (U before E): confirm.

## R120 — The `role` value has no per-asset source

**Risk class:** structural.
**Register row.**

> (I-21) The `role` field value ("neither") — no tier assigns manifestation/temporal/neither per asset. Clause (T4 §0): "role: manifestation \| temporal \| neither (supplies what both rest on)   # from layer §4.4" → Layer §4.4 gains the per-asset role assignment it is cited as sourcing
>
> **State in register:** OPEN — T3 reopen agenda (D2 ruling 2026-09-27)
> — REG R120 :297 (severity DEGRADES)

**Clause as it stands.**

> - its manifestation or temporal role
> — T3 :476

> role:             manifestation | temporal | neither (supplies what both rest on)   # from layer §4.4
> — T4 :76

> inherits:    layer instance §4.4 (the thirteen inherited items)
> — T4 :64

**Remedy chosen by D2.**

> R120 (§4.4 role row; R192/R208 close with it)
> — D2 :133

**Chosen here: reword the existing bullet, add no new one.** T3 §4.4 has twelve bullets, not thirteen; the bullet at :476 already names the role but offers two values, assigns it nowhere and gives the brief no source. T4 counts "thirteen inherited items" (T4 :64, :86) by splitting some of §4.4's bullets, so adding a bullet to T3 would change T4's count in three places; rewording changes none. The role is per-asset content, so the draft places the assignment in §3.2/§3.3 (the per-asset sections), not in §3.4 (the intra-layer interplay matrix).

**Drafted replacement text** (:476):

~~~~
old: - its manifestation or temporal role
new: - its role — `manifestation`, `temporal` or `neither` (supplies what both rest on) — assigned per asset by this instance (in 3.2, beside the disposition, with a one-line reason); the brief copies it and does not choose it
~~~~

**Cross-tier re-render hazards.** T4 :76 (`role: … # from layer §4.4`) becomes true as written; T4 :64/:86/:105 ("thirteen") unchanged. T1 §16 and T2 §13.3 ("its manifestation or temporal role", T2 :686) say the brief states the role: unchanged.

**Open questions.**
1. No source gives the rule for assigning the role; T2 §5's present-interval row ("Activation is L3; expression … is L4") is the only layer-level hint. The draft makes the instance assign it with a reason rather than inventing a criterion; SS may want a criterion.
2. R192 states that §4.4's "thirteen rows contain no role row"; the thirteen are T4's (T4 :86) and T3 §4.4's twelve contain a role bullet. The defect is real but narrower than R192 words it.

## R201 — The source of a consumed contract's declared use is unnamed

**Risk class:** structural.
**Register row.**

> Declared use per consumed contract. Clause (T3 §2.3): "Every consumed input declares its use … **A citation with no declared use is not a contract.**" → T3 §2.3 names the source of declared uses (a per-contract use registry, or the census), so the instance transcribes rather than invents
>
> **State in register:** OPEN — T3 reopen agenda (D2 ruling 2026-09-27)
> — REG R201 :393 (severity BLOCKS_LAYER)

**Clause as it stands.**

> Two tables: DP contracts this layer **produces** (consumer, fields, grain, identity, generation) and
> DP contracts it **consumes** (producer, fields, declared use). Every consumed input declares its use
> — calculation, applicability, counter-evidence, uncertainty, interpretation, exclusion, navigation,
> evaluation. **A citation with no declared use is not a contract.**
> — T3 :296–299

**Remedy chosen by D2.**

> R201 (§2.3 names the source of declared use)
> — D2 :133–134

**Drafted replacement text** — appended to §2.3 after :299:

~~~~
**Where declared uses come from.** The instance transcribes declared uses; it does not invent them. The sources, in order: the declared-use column of Data plane §7.1 for the contract; then, once it exists, the registry's `consumes_contracts` field for the asset (the census reports it). A consumed input for which neither names a use is recorded `declared use: UNDECLARED` — a gap raised at its source, not filled by the instance.
~~~~
**Cross-tier re-render hazards.** Depends on T2's declared-use column (R186, shared draft D-7.1 in the T2 agenda) — seal T2 first. R109's registry columns are P9 data work. T4 §0.1 row 5 inherits.
**Open questions.** R109's columns do not exist yet; the draft names them conditionally ("once it exists"). If SS prefers, delete the second source.

## R221 — §0.1 re-scoped to catalog units produced and the layer's place in the necessity closure

**Risk class: VERDICT-CHANGING.** §0.1 is the origin of the alignment test (§0.4, §5.4 test 2): changing what §0.1 holds changes what a section can trace to and what is struck.
**Register row.**

> T3 §0.1 re-scoped on the T3 reopen agenda: "P-needs and V-journeys this layer is necessary for" → "the catalog units this layer's assets produce or part-produce, and the layer's place in the necessity closure" — a derived section filled from R85, never judged; retires the clause that produced the 130 P4 invention rows
>
> **State in register:** OPEN — per D5 rev. 2.1; on the D2 T3 agenda
> — REG R221 :423 (severity BLOCKS_LAYER)

**Clause as it stands.**

> ### 0.1 · What cannot be answered without this layer
>
> ```
> inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
> measured_by: none — definitional; but every P/V cited must exist in the parent under current numbering
> traces_to:   —  (this IS the origin)
> ```
>
> List the P-needs and V-journeys for which this layer is **necessary** — not "involved in", not
> "contributes to", but *cannot be answered without*. For each, one line: the distinction the customer
> would lose if this layer did not exist.
>
> This is ablation at layer scale. Remove the layer; what the customer loses is its value. A layer that
> is necessary to nothing has no value, however much it computes.
>
> | P / V | the distinction that disappears without this layer |
> |---|---|
> | | |
> — T3 :99–116

**Remedy chosen by D2 / D5 rev. 2.1.**

> R221 (§0.1 re-scoped to catalog units produced and closure position — D5 rev. 2.1)
> — D2 :134

> Tier-3 §0.1 is re-scoped on the T3 reopen agenda (R221): from "P-needs and V-journeys this layer is
> necessary for" to "the catalog units this layer's assets produce or part-produce, and the layer's
> place in the necessity closure" — a derived section, filled from parts 2–3, never judged. The clause
> whose unanswerability produced the 130 invention rows is retired with its cause. **No T2 §3.6 is
> — D2 :297–300

**Drafted replacement text** — §0.1 in full (heading unchanged):

~~~~
### 0.1 · What this layer produces for the catalog, and where it sits in the necessity closure

```
inherits:    Data plane §3.1 (the six contributions); the catalog's producer claims (`producer_output_claims`, `platform/src/generated/capability_knowledge.snapshot.json`) and the necessity closure over `asset_registry.depends_on` (register R85); the planner P-need test (R218)
measured_by: `catalog_provenance.py --closure` over the active population (`is_active AND dead_flag IS NOT TRUE`), at a named catalog and registry revision — the instrument and population are stated, the figures are copied, never re-judged
traces_to:   —  (this IS the origin)
```

Necessity is a property of the catalog, not of questions: an asset is necessary if it produces or part-produces a catalog unit, or lies upstream in the build DAG of an asset that does. This section is derived, never judged. Copy, for this layer:

| catalog unit (SCU) | produced or part-produced by (this layer's assets) | producer claim: reviewed or derived |
|---|---|---|

| asset | necessity: by production · by upstream dependence · outside the closure | reason code where outside |
|---|---|---|

An asset outside the closure is first a catalog-provenance finding; only once every unit names its producers is it a merge or retire candidate. The P-needs and V-journeys the layer serves are read from the planner test (each of P01–P24 resolved through `plan_retrieval` to catalog units with named producers), narrowed to this layer's units; they are not asserted here.
~~~~
**Cross-tier re-render hazards (the echo list — this one is large).** Every place that says §0.1 holds P/V rows:
- T3 :123 (0.2 `traces_to: 0.1`), :149 (0.4: "naming a 0.1 row"), :182 (1.2 "which rows this asset serves"), :279, :306, :335, :461, **:467** (4.4 bullet 1: "the P-needs and V-journeys the asset serves (from 0.1, narrowed)" — must now read from the planner test's units), :679 (the L0 row of the adaptation table: "0.1 is mostly *indirect*").
- T4 :66 (`traces_to: layer §0.1 (the P/V rows this asset serves)`), T4 :90 (§0.1 row 1 "layer §0.1, narrowed").
- T1 §16 ("the P-needs (§2) it serves") and T2 §13.3 item 1 and its asset-brief sentence (:662, :686): both assume instances name P-needs; they stay true if the planner test supplies them.
- Instances: the L0 instance's §0.1 (L0 :28) and every L1–L5 instance.

**Open questions.**
1. **The echo set decides the size of this row, and the :467 edit needs SS's explicit authorisation at J1** (it is outside D2's literal wording, which names §0.1 only; see "Decisions required at J1"). :467 (4.4 bullet 1) needs a consequential edit or the asset-brief derivation loses its first row; the draft does not rewrite it because D2 names §0.1 only. SS to widen or accept the consequence.
2. R218 and R85 closed on a snapshot (17/24 P-needs PASS; 111 of 127 assets in the closure, per R85's closure note); the template cites the instrument, not the figures.
3. The instrument is already on `main`: `platform/scripts/governance/catalog_provenance.py` has the same git blob (`8ef86fba5d96`) on `origin/main` and on `origin/campaign/nikasha-test` (checked 2026-10-02 with `git rev-parse <ref>:<path>`), so the re-seal precondition on the script is met. What differs is the data: `CLOSURE_REPORT.md` and `producer_provenance.derived.json` are on the nikasha-test branch only, and `main` carries `capability_knowledge.snapshot.json`; the closure figures must be re-run at a named revision, which the draft's `measured_by` already requires.

## R94 — Presentation-parity ownership seen from L1

**Risk class: VERDICT-CHANGING** (inherited from R71; no separate edit).
**Register row.**

> Whether the presentation-parity acceptance test is the layer plan's own work (§12.2 [TRANSFERS] vs T3 §5.4 test 4). Clauses (T2 §1): "A [TRANSFERS] obligation is not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work." vs (T3 §5.4): "4. **Presentation parity** holds for the layer's served surface." → T3 §5.4 test 4 gains: "run where the surface exists; where the owning plane is not built, record [TRANSFERS]-pending — never a pass, never a block"
>
> **State in register:** OPEN — closes with R71 per D3 ruling 2026-09-27 (T3 reopen)
> — REG R94 :266 (severity BLOCKS_LAYER)

**Clause and remedy.** T3 §5.4 test 4 (:628) as quoted under R71. The register's own remedy for R94 is the v1.0 wording ("run where the surface exists; where the owning plane is not built, record [TRANSFERS]-pending — never a pass, never a block"). D3 supersedes it: it removes "run where the surface exists" because "the existence of a built plane is not an ownership assignment" (D3, D2 file :176–177). R94 closes with R71 on D3's text, not on its own.

**Drafted replacement text.** None of its own: R71 (a) and (b).
**Cross-tier hazards and open questions.** As under R71.

## R140 — Presentation-parity ownership seen from L3

**Risk class: VERDICT-CHANGING** (inherited from R71; no separate edit).
**Register row.**

> Ownership of Presentation parity — [TRANSFERS] in T2 yet a layer acceptance test in T3. Clauses (T2 §1) vs (T3 §5.4 test 4): "Presentation parity holds for the layer's served surface" → Resolve: either §5.4 test 4 reads "holds, where the layer is the owner" or §12.2's row loses [TRANSFERS]
>
> **State in register:** OPEN — closes with R71 per D3 ruling 2026-09-27 (T3 reopen)
> — REG R140 :322 (severity BLOCKS_LAYER)

**Clause and remedy.** T3 §5.4 test 4 (:628). R140's two remedies were "holds, where the layer is the owner" or removing [TRANSFERS] from T2 §12.2. D3 takes neither: test 4 is reworded to "Presentation fields carried" and T2's tag stays (D3, D2 file :172–173). Closes with R71.

**Drafted replacement text.** None of its own: R71 (a) and (b).
**Cross-tier hazards and open questions.** As under R71.

## R185 — Presentation-parity ownership seen from L4

**Risk class: VERDICT-CHANGING** (inherited from R71; no separate edit).
**Register row.**

> Whether the presentation-parity test is L4's own work, given [TRANSFERS]. Clause (T3 §2.2): "measured_by: presentation-parity test (Data plane §12.2): both renderings from the consumed reading package, no recomputation, identical finding / confidence / uncertainty" → T3 §2.2 must carry the [TRANSFERS] marking: the layer states the fields it carries; the parity test belongs to the retrieval/conversation plane's artefact
>
> **State in register:** OPEN — closes with R71 per D3 ruling 2026-09-27 (§2.2 `measured_by` re-worded; T3 reopen)
> — REG R185 :372 (severity BLOCKS_LAYER)

**Clause and remedy.** T3 §2.2 `measured_by` (:278). D3's rewording of exactly that line (R71 (b)) states the fields the layer carries and moves the parity test to the owning plane: the remedy R185 asks for. Closes with R71.

**Drafted replacement text.** None of its own: R71 (a) and (b).
**Cross-tier hazards and open questions.** As under R71.

## R192 — Role per asset, seen from L4 (PH_MUHURTA)

**Risk class:** structural (inherited from R120; no separate edit).
**Register row.**

> (PH_MUHURTA §0) role: manifestation. Clause (T4 §0): "role:             manifestation \| temporal \| neither (supplies what both rest on)   # from layer §4.4" → §4.4's thirteen rows contain no role row; either add row 14 (role per asset) to T3 §4.4 or drop the "# from layer §4.4" citation
>
> **State in register:** OPEN — closes with R120 on the T3 reopen agenda (D2 ruling 2026-09-27)
> — REG R192 :379 (severity DEGRADES)

**Clause and remedy.** T4 :76's `# from layer §4.4`. Closes with R120's reword of T3 :476; R192's alternative ("drop the '# from layer §4.4' citation") is not taken. Premise note: the "thirteen rows" these rows cite are T4's (T4 :86), see R120 open question 2.

**Drafted replacement text.** None of its own: R120.
**Cross-tier hazards and open questions.** As under R120.

## R208 — Role per asset, seen from L5 (MI_KULA)

**Risk class:** structural (inherited from R120; no separate edit).
**Register row.**

> (MI_KULA §0) role (manifestation/temporal/neither) not assigned per L5 asset. Clause (T4 §0): "role: … # from layer §4.4" → T3 §4.4 gains a fourteenth row (asset role), or T4 §0 states the author assigns it and records why
>
> **State in register:** OPEN — closes with R120 on the T3 reopen agenda (D2 ruling 2026-09-27)
> — REG R208 :400 (severity DEGRADES)

**Clause and remedy.** The same T4 citation. R208's alternative ("T4 §0 states the author assigns it and records why") is the instance-assigns rule R120's text adopts, placed in T3 §4.4 rather than T4 §0. Closes with R120. Premise note: the "thirteen rows" these rows cite are T4's (T4 :86), see R120 open question 2.

**Drafted replacement text.** None of its own: R120.
**Cross-tier hazards and open questions.** As under R120.

## Deferred to a second reopen round — not agenda rows

D2: "Explicitly deferred to a second reopen round, after P9's derivability re-run makes their remedy text known: R131 (§0.2 external comparison), R210 (default per-obligation detectors), R214 (§0.3 migration-pin location). They stay OPEN; no sealed row is silently outside this ruling." (D2 :135–137.) Nothing is drafted for them.

> "What it computes that existing software does not". Clause (T3 §0.2): "Name what it computes that existing software does not, and what it hands the reasoning layer to read across." → Drop the external-comparison demand from the template, or supply a named comparison baseline per layer
>
> **State in register:** OPEN — sealed-clause edit explicitly deferred to D2 reopen round 2, after P9's derivability re-run; stays OPEN (D2 ruling 2026-09-27)
> — REG R131 :313 (severity DEGRADES)

> (MI_KULA §3) No detector for the layer's own scored obligation (predictive performance). Clause (T4 §3): "\| obligation \| what satisfied means for this asset specifically \| detector (named here, run in §4) \|" → T2/3 should name the per-obligation default detectors (as §2.7 does for carriage) so a layer scored on predictive performance is not NO_DETECTOR by construction
>
> **State in register:** OPEN — sealed-clause edit explicitly deferred to D2 reopen round 2, after P9's derivability re-run; stays OPEN (D2 ruling 2026-09-27)
> — REG R210 :402 (severity DEGRADES)

> Migration-pin source unavailable to the derivation; three-source reconciliation impossible from template-permitted inputs. Clause (T3 §0.3): "measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement" → T3 names the migration pin's location (or the census as its reader) so "three sources" is runnable, or relaxes the requirement to "available sources, absence recorded"
>
> **State in register:** OPEN — sealed-clause edit explicitly deferred to D2 reopen round 2, after P9's derivability re-run; stays OPEN (D2 ruling 2026-09-27)
> — REG R214 :406 (severity BLOCKS_LAYER)

Note: R210's clause is in T4 §3 (T4 is not sealed) though its remedy text speaks of "T2/3"; R214's clause is T3 §0.3 (:135).


## Re-seal mechanics (apply once, after the agenda is decided)

- **Order and gates (D2 rule 3, rule 4).** Re-seal parent-before-child: T1, then T2, then T3. One version bump per document, after its cross-tier re-render pass and an independent review (Astra or Kimi K3). The documents carry `version: "FINAL"`, so the "bump" is a dated changelog entry in the convention the two earlier reopens used (T2 changelog :40 and T3 changelog :37, "REOPENED AND AMENDED (date, native ruling — …)"), plus a restamp of the document's fingerprint in `CAPABILITY_MANIFEST.json` (the identity of record, T3 frontmatter :8).
- **Closed agenda (D2 rule 1).** Anything found while editing becomes a new register row for a second round; it is not added here.
- **Re-render pass (D2 rule 2).** Every count, gate name and section number named under "cross-tier re-render hazards" below is grepped across tiers, the L0 and L1 instances, the tracker and the census in the same commit as the redline. The L0 instance (v3.0) and the five pilot briefs are test artefacts that the register says are regenerated after the freeze (REG frontmatter `what_is_a_test_artefact`), so their echoes are listed for completeness, not as blockers.
- **Nothing here edits a tier document.** This file is a draft held for J1 (plan §4.2 rows 4 and 7); the tier documents are redlined only after the strategist's N-4 decision on this agenda.
