---
artifact: TIER_GAP_HARVEST
canonical_id: SUVARNA_TIER_GAP_HARVEST
version: "1.1"
status: "PROVISIONAL: harvest for the combined reopen agendas; may register and assign gaps, may not certify, decide or edit any tier"
produced_on: 2026-09-30
produced_in: "Exec Suvarṇa"
plan_item: "A.H (Track A brief §7)"
source_commit: "8d13c29249c31d2c6b64e725430c6ee9df3d10ad"   # git -C /Users/Dev/suvarna-lane-A-all rev-parse HEAD (branch suvarna/land/A-step2-layers)
inspector_commit: "2a78ec64d88e59438bd6527b4c99826432102c57"   # /Users/Dev/suvarna-census, detached at origin/campaign/nikasha-test; every layer draft rests on this run"
tiers_and_register_read_at: "/Users/Dev/suvarna-census @ 2a78ec64d (T1, T2, T3, T4, NIKASHA_CHANGE_REGISTER_v2_0.md v2.8, 252 rows)"
inputs:
  - 00_ARCHITECTURE/briefs/suvarna/layers/L0/L0_TIER_GAPS_v1_0.md
  - 00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_TIER_GAPS_v1_0.md
  - 00_ARCHITECTURE/briefs/suvarna/layers/L2/L2_TIER_GAPS_v1_0.md
  - 00_ARCHITECTURE/briefs/suvarna/layers/L3/L3_TIER_GAPS_v1_0.md
  - 00_ARCHITECTURE/briefs/suvarna/layers/L4/L4_TIER_GAPS_v1_0.md
  - 00_ARCHITECTURE/briefs/suvarna/layers/L5/L5_TIER_GAPS_v1_0.md
  - the six layer instances beside them (read for cross-checks only; no row is taken from them)
  - 00_ARCHITECTURE/briefs/suvarna/tracks/TRACK_A_BRIEF_v1_0.md (§7 the harvest) and TRACK_E_BRIEF_v1_0.md (§6, the D2-ruled agenda list)
changelog:
  - "1.1.1 (2026-09-30): re-review (independent Sonnet, 2026-09-30) corrections applied: T2-11 section cite (§1 not §2), T3-05 R113 wording, T3-27 R08 pointer, proposed-wording labels on three unsourced quoted phrases and on option T2-07(a), and the row-level tally caveat (substance count 124). No item, tier or count changed."
  - "1.1 (2026-09-30): gate review corrections applied (independent Sonnet review 2026-09-30): 9 defects. (1) The two detector-only rows (TG-L0-006, TG-L1-010) moved from TGH-T2-06 to TGH-T3-15, the L1 event-time-identity facet kept as a rider on TGH-T2-06. (2) Multi-clause items split: TGH-T2-01 into ownership (kept) and the declared universe (TGH-T4-04, with the three rows that need it); TGH-T2-03 into the layer-by-class table (kept), the rule 4 and 6 population (TGH-T2-20) and the event-class omission (TGH-T2-21); TGH-T3-14 into the undefined section 7 and section order (kept) and the count mismatches (TGH-T3-27); TGH-T3-08 title corrected (L0 has three unmapped instruments, not none). (3) TG-L5-018 re-tiered from T3 to T4 as TGH-T4-05. (4) R94 and R119 taken out of TGH-T2-02's same-gap list, R113 out of TGH-T3-05 and TGH-T3-12. (5) TGH-T2-11 cites T2 L58, not L174, for L0 as the global foundation. (6) Instrument-class label re-derived from the register remedy wording for every item (section 1.7): 3 items instrument-class, 7 T3 items mixed; the SS-ruling bullet restated on that set. (7) Counting convention stated beside each tally; adjacency, item statuses and class labels derived by the check script, not hard-coded. (8) Ordering rule restated and every item re-ranked mechanically; ids are now stable labels (new items take the next number); the scope of TGH-T3-01's 254 figure stated. (9) Wording: TGH-T2-05 and TGH-T3-08 titles; near-label quotes in TGH-T3-08, -10 and -12 paraphrased; TGH-T3-04 option (b) labelled withdrawn; TGH-T2-09 and TGH-T3-19 statuses derived; the script claim and the script corrected (U+2011 hyphens normalised, every table count column checked). Four premises of the review were not applied as stated (section 3.5). Counts after: 159 TG rows folded into 54 items (T1 1 · T2 21 · T3 27 · T4 5); 161 ids in the sources = 159 folded + 2 ledger-only."
  - "1.0 (2026-09-30): first issue. 159 TG rows folded into 49 harvest items (T1 1 · T2 19 · T3 26 · T4 3); 2 further ids (recast and withdrawn by their own drafts) listed in section 3; accounting check in section 6."
---

# Tier gap harvest (A.H)

**What this file is.** The single list of every clause the six layer drafts needed and the four tiers did not supply, folded across layers into one item per missing clause, checked against the change register, and assigned to exactly one tier with a proposed remedy direction. It is the input the Nikaṣa Engine's E2 folds into the combined reopen agendas; Strategic Suvarṇa decides them (N-4.Tx). Nothing here edits a tier, the register, a ledger or any layer draft, and no remedy below is replacement text: each is a direction or an option list, and the reopen agendas decide.

**Conventions.** T1 `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md`; T2 `…/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md`; T3 `…/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`; T4 `…/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md`. Line numbers ("L588") are those of the files at census commit `2a78ec64d`, copied from the layer drafts, never re-derived here. `R##` is a row of `NIKASHA_CHANGE_REGISTER_v2_0.md` v2.8. `TG-Lx-nnn` is a row of `Lx/Lx_TIER_GAPS_v1_0.md`. An asterisk after an `R##` marks a row on the D2-ruled E2.1 list (below); a bracket after it gives a non-OPEN register state. Every figure in evidence lines is quoted from the layer drafts; every count in this file is computed by counting source rows (computed by script, then re-derived independently by the check in section 6). Item ids (`TGH-Tn-nn`) are stable labels assigned at v1.0 in rank order and are not renumbered; items added at v1.1 take the next number in their tier, and rank is the position in section 1.4 under the ordering rule below. Section 2 lists the items in id order within a tier.

**How the fold was made.** (1) All 161 `TG-*` ids were parsed from the six files (159 counted gap rows plus two ids that their own L0 draft recast to a proposal and withdrew, section 3.1). (2) Rows that name the same missing clause were folded into one item; a row that touches two clauses sits in the item of its primary clause and the other item lists it under "also touches" (an also-touch is not membership). (3) Each item's register status was read from the register's own rows as the drafts cite them. (4) Each item was assigned one tier; where layers named different tiers the item states the decision and the reason. (5) Items are ordered by consequence (section 1.4) and grouped by tier (section 2). At v1.1 the gate review found rows placed by their headline rather than by the clause they need; rows now sit with the clause they need: TGH-T3-15 takes the two detector-only rows, and TGH-T4-04 takes the three rows that also need a declared universe, whose ownership half stays visible in TGH-T2-01 under "also touches" (section 3.5).

**Against the E2.1 agendas.** The three agenda files (`reopen/REOPEN_AGENDA_T{1,2,3}_v1_0.md`, Track E §6 item E2.1) do not exist yet: there is no `reopen/` directory under `briefs/suvarna/` in the exec worktree (HEAD `aec3058e2`) or in the layers branch. Overlap is therefore computed against the list Track E §6 gives for them from the D2 ruling: T1 R01, R72, R76 · T2 R06, R73, R75, R88, R89, R90, R91, R119, R181, R186, R198 · T3 R08, R09, R10, R65, R67, R68, R71, R74, R93, R120, R201, R221 · closing with them R94, R140, R185, R192, R208 (31 rows); R131, R210 and R214 are deferred to D2 round 2. The same 31 were cross-checked against the register: every one of the 27 register rows whose state text says "reopen agenda" is in the list; the four list rows without that phrase in the state cell (R94, R140, R185, R221) are the ones the register describes as closing with R71 or as re-scoped on the T3 agenda. Track E §6: "each agenda gains the harvested tier gaps assigned to it (v1.1)"; once an agenda opens, later gaps go to the second-round list (section 5).

**Ordering rule.** Keys are applied in this order; all descend except the last, and the check in section 7 recomputes the order from the items (section 1.4 and each item's rank line must match it). (1) Layers touched by the item's folded rows. (2) TG rows folded. (3) Active assets in the touched layers (L0 40 · L1 19 · L2 23 · L3 21 · L4 9 · L5 15 = 127, the SUMMARY.md figures quoted in the internal-references row of the L1 tier-gap file). (4) The item's headline count of gate cells no instrument can read, as its rank line states it (only where the drafts measure one: TGH-T3-01 254, which counts the Null and Narr rows only, its Earn and Ldgr readings being shown beside it and not added; TGH-T3-02 127; TGH-T4-04 127; 0 elsewhere). (5) The number of the item's listed same-gap register rows that the register grades BLOCKS_LAYER, in any register state. (6) The number of the item's rows that have no same-gap register row (adjacent-only or none). (7) Id, ascending as a string, so a T2 id precedes a T3 id. Ties on the first four keys are common (several items touch all six layers with six rows) and are not a judgement of relative importance.

## 1. Summary

### 1.1 Items per tier, and coverage against the register

"Same-gap" = the source draft cites a register row as the same gap; "adjacent only" = the draft names only a neighbouring row; "none" = the draft says no row carries it (each read from the register cell of the source row and verified by the check in section 7).

**Counting conventions.** Two conventions are used and each tally says which.
- *Row level* (columns "rows: same-gap row cited / adjacent row only / no register row", and every same-gap / adjacent / none triple in this file): read from the source row's own register cell. None = the cell begins with none or NEW, which includes the 5 rows worded "NEW (adjacent: …)", counted as their own drafts count them. Adjacent-only = the cell is not none and says nearest, adjacent or no exact row, or cites only rows that the item's Register line records as adjacent (L4's rows for R124 and R51). Same-gap = every other row whose cell cites a register row. The sets are derived by the check in section 7, not listed in it. Counting the 5 "NEW (adjacent: …)" rows as adjacent-only instead gives 126 / 12 / 21.
- *Caveat on the row-level same-gap count:* it follows each source row's own register cell, so rows whose item text says no register row carries their exact clause (two L5 rows, and the T2-09/T2-20/T2-21 register lines) are counted same-gap by convention; on the substance reading the count is 124 (independent re-review).
- *Item level* (columns "items on the D2-ruled E2.1 list / covered by an open row, not on the list / new"): derived from the item's own "Same-gap rows cited" list, which holds only the register rows whose clause is the item's clause. A row a draft cited for another clause is listed apart as cited for another clause and is carried by the item that owns that clause, so an item's row-level triple and its item-level status can differ (TGH-T2-09, TGH-T2-21). On the list = the list holds a row on the D2-ruled 31 (asterisk); covered = it holds an open (not CLOSED) row and none on the list; new = it holds no open row. No item carries an override at v1.1; the v1.0 differences (TGH-T2-09, TGH-T3-01, TGH-T3-19) came from cites made for other clauses and are resolved that way.

| tier | items | TG rows folded | rows: same-gap row cited | rows: adjacent row only | rows: no register row | items on the D2-ruled E2.1 list | items covered by an open row, not on the list | items new (no open same-gap row) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| T1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 1 |
| T2 | 21 | 47 | 32 | 2 | 13 | 8 | 0 | 13 |
| T3 | 27 | 97 | 80 | 5 | 12 | 8 | 12 | 7 |
| T4 | 5 | 14 | 14 | 0 | 0 | 0 | 5 | 0 |
| **total** | **54** | **159** | **126** | **7** | **26** | **16** | **17** | **21** |

Rows by the tier each layer draft gave (before this harvest's decisions): T1 1 · T2 51 · T3 97 · T4 10 = 159; after the decisions in section 1.5: T1 1 · T2 47 · T3 97 · T4 14. 23 of the 159 rows carry a different tier from their own draft's.

### 1.2 TG rows per layer, folded into how many items

Same-gap / adjacent only / none: row-level convention (section 1.1). "Folded into items" counts the distinct items that hold the layer's rows.

| layer | active assets | TG rows counted | folded into items | same-gap / adjacent only / none | rows by own draft tier T1·T2·T3·T4 | rows by assigned tier T1·T2·T3·T4 | rows re-tiered | ids not counted |
|---|---:|---:|---:|---|---|---|---:|---|
| L0 Brahmagyan | 40 | 28 | 27 | 22 / 0 / 6 | 0·10·17·1 | 0·7·19·2 | 3 | 2 (section 3.1) |
| L1 Gaṇita | 19 | 24 | 24 | 19 / 0 / 5 | 1·6·14·3 | 1·5·15·3 | 4 | none |
| L2 Bodha | 23 | 24 | 24 | 19 / 3 / 2 | 0·5·18·1 | 0·7·16·1 | 2 | none |
| L3 Kāla | 21 | 27 | 25 | 21 / 0 / 6 | 0·11·15·1 | 0·11·14·2 | 3 | none |
| L4 Phala | 9 | 25 | 25 | 18 / 4 / 3 | 0·9·15·1 | 0·7·16·2 | 5 | none |
| L5 Mīmāṃsā | 15 | 31 | 30 | 27 / 0 / 4 | 0·10·18·3 | 0·10·17·4 | 6 | none |
| all layers | 127 | 159 | 155 (each layer's count; items shared by layers counted once per layer) | 126 / 7 / 26 | 1·51·97·10 | 1·47·97·14 | 23 | 2 |

### 1.3 Dedupe ratio

- **159 TG rows -> 54 items: 2.94 rows per item; 66.0% fewer entries** (159 -> 54).
- Items folding rows from two or more layers: **33** (138 rows); from one layer only: 21 (21 rows). Items touching all six layers: 7 (42 rows).
- Rows per item: 1 row x 21, 2 rows x 5, 3 rows x 9, 4 rows x 3, 5 rows x 7, 6 rows x 9. Single-row items: 21.
- Register duplication (row-level convention, section 1.1): 126 of the 159 rows cite a register row as the same gap. The other 33 rows (26 with no row, 7 with only an adjacent row) sit in 25 items; 20 of the 21 new items hold at least one such row (item-level convention), and 5 items are otherwise covered but carry at least one uncovered row. The new item with no uncovered row (TGH-T2-21) holds a row that cites a register row for another clause only.

### 1.4 Ranked list of all items (by consequence)

Order recomputed by the check in section 7 from the ordering rule above; ids are not in rank order any more (section 1.4 is the rank order, section 2 the id order).

| rank | id | tier | item | layers | rows | assets | status vs register |
|---:|---|---|---|---|---:|---:|---|
| 1 | TGH-T3-01 | T3 | The gate map's right-hand column (Ldgr sources, Earn claims, Null convention, Narr flag) has no source; the … | L0-L5 | 6 | 127 | open row, not on list |
| 2 | TGH-T3-02 | T3 | Per-asset carriage check (D1 / D2 / D3): the template assigns it at layer scope only | L0-L5 | 6 | 127 | open row, on E2.1 list |
| 3 | TGH-T3-03 | T3 | No rule maps measured evidence to one of the eight dispositions | L0-L5 | 6 | 127 | open row, on E2.1 list |
| 4 | TGH-T3-04 | T3 | T3 §0.1 asks for the P-needs and V-journeys a layer is necessary for; no tier maps any P or V to a layer | L0-L5 | 6 | 127 | open row, on E2.1 list |
| 5 | TGH-T2-02 | T2 | Which of the eight §3.4 presentation rows a layer carries (rows map to contracts, never to layers) | L0-L5 | 6 | 127 | open row, on E2.1 list |
| 6 | TGH-T3-05 | T3 | "Registry seed" and "migration-governed pin": named by T3, defined by no tier; three-way `depends_on` … | L0-L5 | 6 | 127 | open row, not on list |
| 7 | TGH-T3-06 | T3 | "The CURRENT frozen definition revision" for cross-layer gates: undefined, and inherited from a superseded … | L0-L5 | 6 | 127 | open row, not on list |
| 8 | TGH-T2-04 | T2 | Per-layer (and per-asset) roll-up of DP contracts produced and consumed; who produces DP07/DP08/DP09 | L0 L2 L3 L4 L5 | 6 | 108 | open row, on E2.1 list |
| 9 | TGH-T3-15 | T3 | "For each rule, the detector": no tier names a detector, or a class of detector, for any T1 §8.1 correctness … | L0 L1 L3 L4 L5 | 6 | 104 | open row, not on list |
| 10 | TGH-T2-05 | T2 | One table with several producers: no expression in the contract vocabulary, and no declared write set where the … | L0 L1 L2 L3 L5 | 5 | 118 | open row, on E2.1 list |
| 11 | TGH-T3-07 | T3 | Presentation parity: T2 marks it [TRANSFERS] ("a layer plan does not inherit it as its own work"), T3 makes it … | L0 L1 L2 L3 L4 | 5 | 112 | open row, on E2.1 list |
| 12 | TGH-T3-08 | T3 | T3 §3.1 asks where a layer stands on each obligation it is scored on, measured; L0 has three unmapped … | L0 L2 L3 L4 L5 | 5 | 108 | open row, not on list |
| 13 | TGH-T3-09 | T3 | "Whether current code on any live head differs from what is deployed": "live head" and the deployed reading are … | L0 L1 L2 L4 L5 | 5 | 106 | open row, not on list |
| 14 | TGH-T3-10 | T3 | "Verified at the consumer": no consumer-side probe or definition of a "live" field | L0 L1 L2 L4 L5 | 5 | 106 | open row, not on list |
| 15 | TGH-T3-11 | T3 | The manifestation / temporal / neither role of each asset is assigned by no tier (and T3 has 12 bullets where … | L0 L1 L2 L4 L5 | 5 | 106 | open row, on E2.1 list |
| 16 | TGH-T4-01 | T4 | The `kind` vocabulary has no place for a view, an UPDATE-only writer, an undeclared-target writer, a no-writer … | L1 L2 L4 L5 | 5 | 66 | open row, not on list |
| 17 | TGH-T3-12 | T3 | Edge type per edge: T2 §3.2 defines five types; no source records or assigns them | L0 L2 L3 L5 | 4 | 99 | open row, on E2.1 list |
| 18 | TGH-T3-13 | T3 | No layer-level synergy seams and no ablation harness (the synergistic term cannot be computed) | L0 L2 L3 L5 | 4 | 99 | open row, not on list |
| 19 | TGH-T2-03 | T2 | Which of the sixteen entity classes a layer emits or accepts, and the independent-map census | L1 L2 L3 L4 | 4 | 72 | open row, on E2.1 list |
| 20 | TGH-T3-14 | T3 | T3 §5.2 tells the instance to report unfillable rows in §7, which T3 does not have; §2.5 is ordered after §2.7 | L0 L2 L5 | 3 | 78 | open row, on E2.1 list |
| 21 | TGH-T4-04 | T4 | The declared universe a completeness count divides by: T4 §1.1 says to declare it and names no place to declare … | L0 L1 L4 | 3 | 68 | open row, not on list |
| 22 | TGH-T3-16 | T3 | Where an asset's natural key is declared (the Idem gate cannot decide "replaces its own rows" without it) | L0 L1 L4 | 3 | 68 | open row, not on list |
| 23 | TGH-T2-01 | T2 | Which coverage obligations a layer owns: T2 §5 assigns no owner and no state | L2 L3 L5 | 3 | 59 | open row, on E2.1 list |
| 24 | TGH-T2-07 | T2 | May an upstream rebuild physically delete downstream rows (foreign-key CASCADE across layers)? No tier says | L2 L3 L4 | 3 | 53 | new |
| 25 | TGH-T3-17 | T3 | T3 §0.2 demands "what it computes that existing software does not"; no tier supplies a baseline to establish it | L1 L3 L4 | 3 | 49 | open row, not on list |
| 26 | TGH-T2-06 | T2 | Life-event switch: per-table classification (event-free versus event-conditioned overlay) and the identity of … | L3 L4 L5 | 3 | 45 | open row, on E2.1 list |
| 27 | TGH-T2-08 | T2 | Declared use of each consumed input ("a citation with no declared use is not a contract") exists nowhere as data | L3 L4 L5 | 3 | 45 | open row, on E2.1 list |
| 28 | TGH-T4-02 | T4 | Assets with no table (services): the storage, completeness, ablation, contract and vocabulary clauses assume … | L0 L3 | 3 | 61 | open row, not on list |
| 29 | TGH-T3-18 | T3 | What the Idem claim ("a rebuild replaces its own rows; it never accretes") means for upsert writers and … | L0 L5 | 2 | 55 | new |
| 30 | TGH-T3-19 | T3 | What defines an asset's "preserved kernel" (sourced "from 3.2", which lists dispositions only) | L2 L3 | 2 | 44 | open row, not on list |
| 31 | TGH-T3-20 | T3 | Three coverage-state vocabularies: five in T3, six in T1, three-plus in T2 | L2 L3 | 2 | 44 | new |
| 32 | TGH-T4-03 | T4 | A writer-backed asset that is empty: no clause says how "empty by design" is declared or graded | L1 L5 | 2 | 34 | open row, not on list |
| 33 | TGH-T2-09 | T2 | Three unreconciled lists of epistemic kinds, and no layer-template home for typing outputs by kind | L1 L5 | 2 | 34 | new |
| 34 | TGH-T2-20 | T2 | The population behind T2 §4.1 rules 4 and 6 (which code-side representations, which independent maps) is … | L0 | 1 | 40 | open row, on E2.1 list |
| 35 | TGH-T2-10 | T2 | Four disposition vocabularies across T1, T2, T3, T4 (and a fifth in the campaign brief) | L0 | 1 | 40 | new |
| 36 | TGH-T2-11 | T2 | What an L0 "generation" is and how an L0 change reaches charts other than the canonical one | L0 | 1 | 40 | new |
| 37 | TGH-T2-12 | T2 | No tier defines a "release" of the controlled vocabulary (identity, digest, minter, consumer pin) | L0 | 1 | 40 | new |
| 38 | TGH-T3-21 | T3 | Meaning of `catalog_status = DRAFT` for certification | L0 | 1 | 40 | new |
| 39 | TGH-T2-13 | T2 | L2's own correctness rule (shared roots are not independent confirmations): the carrier field and counting … | L2 | 1 | 23 | new |
| 40 | TGH-T2-14 | T2 | The criterion separating "nearest" from "better-supported later" windows, and who declares it | L3 | 1 | 21 | new |
| 41 | TGH-T2-15 | T2 | T2 W05 tells the reader to reconcile an artefact it never identifies | L3 | 1 | 21 | new |
| 42 | TGH-T3-27 | T3 | T3's own counts disagree with its neighbours: "six static checks", an "eight-row map", "9 × 129 assets" | L1 | 1 | 19 | open row, on E2.1 list |
| 43 | TGH-T1-01 | T1 | Computational correctness: "independent verification where required", sensitivity and "declared tolerance" have … | L1 | 1 | 19 | new |
| 44 | TGH-T2-16 | T2 | Which L1 rows owe a unit is stated nowhere | L1 | 1 | 19 | new |
| 45 | TGH-T3-22 | T3 | The Ldgr claim for a computed root whose inputs are birth parameters and L0, not upstream `fact_id`s | L1 | 1 | 19 | new |
| 46 | TGH-T2-17 | T2 | The companion register cites a contract (DP18) that T2 FINAL eliminated; L5's "next-generation artifact edge" … | L5 | 1 | 15 | new |
| 47 | TGH-T2-18 | T2 | Ownership of admitted observations, protected claims, generated candidates and filing ledgers is deferred to a … | L5 | 1 | 15 | new |
| 48 | TGH-T3-23 | T3 | No tier enumerates tables in a layer's namespace that no asset owns (inventory is per asset) | L5 | 1 | 15 | new |
| 49 | TGH-T2-21 | T2 | T2 §4.1 governs "event class" in its opening sentence and leaves it out of its Scope list of sixteen classes | L5 | 1 | 15 | new |
| 50 | TGH-T3-24 | T3 | Which record carries L5's "learning output" (a visible change to scope, confidence or availability, with the … | L5 | 1 | 15 | open row, not on list |
| 51 | TGH-T4-05 | T4 | The idempotency convention for global-scope assets: T4 §6 names L0 upsert and L1+ delete-then-insert on chart x … | L5 | 1 | 15 | open row, not on list |
| 52 | TGH-T2-19 | T2 | "No unqualified composite score" is stated only at layer level; the asset-level rule, column classification and … | L4 | 1 | 9 | new |
| 53 | TGH-T3-25 | T3 | Which layer carries the "bridge or falsifier" row: T3 says "temporal layers", T2 and T4 say L4 | L4 | 1 | 9 | new |
| 54 | TGH-T3-26 | T3 | Who owns a `Dens` FAIL: the gate is T3's, but serving and delivery are [TRANSFERS] in T2 | L4 | 1 | 9 | new |

### 1.5 Same gap, different tiers: decisions

Where the layer drafts named different tiers for the same missing clause, the item is assigned one tier and the reason is on the item; this table lists them. The tier a draft named is the tier whose text the draft found failing; the assigned tier is the one whose text the harvest proposes the remedy edit first, with riders to the others named on the item.

| item | tiers named by the drafts (rows) | assigned | reason in one line |
|---|---|---|---|
| TGH-T2-05 One table with several producers: no expression in the … | T2 x2 (L0 L1) · T3 x3 (L2 L3 L5) | T2 | producer declaration is contract vocabulary (R06); the T3 §1.1 inventory half stays as R10 on the T3 agenda |
| TGH-T2-07 May an upstream rebuild physically delete downstream rows … | T2 x1 (L3) · T3 x1 (L2) · T4 x1 (L4) | T2 | the rule concerns producer-to-consumer coupling, which T2 §11/DP16 governs; T3 Idem and T4 check 6 inherit |
| TGH-T2-08 Declared use of each consumed input ("a citation with no … | T2 x2 (L3 L4) · T3 x1 (L5) | T2 | obligation stated at T2 §7.1; the missing content is per-contract, so it lives with the contracts (R186 and R201 are both on the agenda: keep one) |
| TGH-T2-09 Three unreconciled lists of epistemic kinds, and no … | T2 x1 (L5) · T3 x1 (L1) | T2 | three plane-level lists disagree; reconcile them before a template home exists; flagged for SS if T1 §5.2 must change |
| TGH-T3-04 T3 §0.1 asks for the P-needs and V-journeys a layer is … | T2 x1 (L0) · T3 x5 (L1 L2 L3 L4 L5) | T3 | D5 withdrew the P/V-by-layer matrix and moved the fix to T3 §0.1 (R221, on the T3 agenda) |
| TGH-T3-11 The manifestation / temporal / neither role of each asset … | T3 x3 (L0 L2 L4) · T4 x2 (L1 L5) | T3 | role is "from layer §4.4" and R120 (T3 agenda) leads; R192 and R208 close with it |
| TGH-T3-12 Edge type per edge: T2 §3.2 defines five types; no source … | T2 x1 (L5) · T3 x3 (L0 L2 L3) | T3 | T3 clauses request the type; T2 §3.2 defines an adequate vocabulary |
| TGH-T3-13 No layer-level synergy seams and no ablation harness (the … | T2 x1 (L3) · T3 x3 (L0 L2 L5) | T3 | T2 already defines the plane seams and the absent-instrument rule; what fails is T3's per-layer binding and harness |
| TGH-T3-15 "For each rule, the detector": no tier names a detector, or … | T2 x3 (L0 L1 L4) · T3 x3 (L0 L3 L5) | T3 | the detector clause is T3 §2.1; the L0 and L1 rows were narrowed to the detector only and the L4 referent is a T2 rider inside the item |
| TGH-T3-17 T3 §0.2 demands "what it computes that existing software … | T2 x1 (L4) · T3 x2 (L1 L3) | T3 | the failing clause is T3's demand; the per-layer T2 text is one remedy option |
| TGH-T4-01 The `kind` vocabulary has no place for a view, an … | T2 x1 (L5) · T3 x1 (L4) · T4 x3 (L1 L2 L5) | T4 | the kind list is T4 §0; T3 and T2 only reference it |
| TGH-T4-02 Assets with no table (services): the storage, completeness, … | T3 x1 (L3) · T4 x2 (L0 L3) | T4 | R14 is a T4 §1 row and the storage bullets carry the table assumption; T3 carries riders |
| TGH-T4-03 A writer-backed asset that is empty: no clause says how … | T3 x1 (L5) · T4 x1 (L1) | T4 | check 6 is T4 §4.2; T3 §5.2 carries only the Build gate row |
| TGH-T4-04 The declared universe a completeness count divides by: T4 … | T2 x3 (L0 L1 L4) | T4 | the failing sentence is T4 §1.1's ("declare the universe first"; R98 and R123 quote it); the ownership half stays in TGH-T2-01 |

13 of 54 items had layer drafts naming more than one tier; 1 further item (TGH-T4-04) had every draft name one tier and was assigned another; the other 40 had a single named tier throughout, equal to the assigned one.

### 1.6 Items needing an SS ruling

- **TGH-T2-07** · May an upstream rebuild physically delete downstream rows (foreign-key CASCADE …: Whether the plane needs a rule at all once F-3 removes the eight keys, or whether F-3 is the whole answer (option b), is a scope decision for SS.
- **TGH-T2-09** · Three unreconciled lists of epistemic kinds, and no layer-template home for …: If the reconciliation must change T1 §5.2 (the product definition) instead of mapping T2's lists onto it, the item belongs to the T1 agenda and needs SS's ruling on which list is authoritative.
- **TGH-T1-01** · Computational correctness: "independent verification where required", …: T1 is sealed and its agenda (T1 R01, R72, R76 per Track E §6) is cosmetic only. Whether T1 opens for a substantive edit, and whether the optional L0 proposal rides with it, is SS's call (N-4.T1).
- **Class-level policy, instrument remedies** (derived per item in section 1.7): **3 items are instrument-class** (every register remedy cited for them changes the inspector, the census, the registry or a consumer probe, none asks for tier text): TGH-T3-01, TGH-T3-06, TGH-T3-10. **7 T3 items are mixed** (an instrument remedy beside tier-text remedies): TGH-T3-03, TGH-T3-05, TGH-T3-09, TGH-T3-12, TGH-T3-13, TGH-T3-16, TGH-T3-19. The layer drafts took different views of this class: the L3 draft filed two of these clauses (the three-way baseline, TGH-T3-09, and the consumer probe, TGH-T3-10) as instrument items and not tier gaps, and the L2 draft filed absent detectors as honest-null packets, while the other layers registered the same clauses as gaps. This harvest keeps them as T3 gaps because the register carries them as tier rows. SS decides whether an instrument-class item goes on the T3 agenda at all and, for a mixed item, whether its instrument half stays with Track E (proposed default: only the sentence stating what an instance records while the instrument is absent goes to T3; the instrument stays with Track E). TGH-T3-08 and TGH-T3-15, which v1.0 labelled instrument-class, are not: the register rows cited for them ask for tier text (R210 and the neighbour R124; R117, R137, R183).

No other item needs a ruling to be assigned; the agendas decide their remedies.

### 1.7 Remedy class of each item (from the register's own remedy wording)

The class of a register row is read from the wording of its own remedy (the text after the arrow in the register), not from what this harvest proposes. **Instrument**: the remedy changes the inspector or census, the registry schema or a field in it, a consumer-side probe or a harness. **Tier text**: the remedy changes the wording of a tier, a template section or the content a layer instance must carry. **Both**: the remedy names an instrument or registry change and a tier-text change together. **No remedy stated**: the row records a defect, a data finding or a decision and names no change. Where a remedy offers alternatives the first option decides its class (R193: the inspector gains a Null check, or the gate map states the detector; R196; R148, R158). An item is **instrument-class** when it lists at least one instrument row and no tier-text or both row; **mixed** when it lists at least one instrument-or-both row together with at least one tier-text-or-both row (a both row counts on each side); **tier text** when it lists at least one tier-text row and no instrument or both row; otherwise its rows state no remedy. CLOSED rows are set aside. The row classes below are this harvest's reading and are data for the check in section 7, which derives each item's class from them.

| class of the register row's own remedy | register rows listed as same-gap by an item |
|---|---|
| instrument | R22, R86, R87, R102, R104, R106, R109, R113, R122, R123, R126, R132, R133, R136, R141, R142, R146, R148, R153, R154, R157, R158, R161, R168, R169, R172, R188, R193, R194, R196, R206 |
| both | R90, R91, R111, R116, R173, R182 |
| tier text | R06, R08, R09, R10, R14, R16, R65, R67, R71, R88, R89, R92, R93, R94, R95, R96, R97, R98, R99, R100, R101, R103, R105, R107, R108, R110, R112, R115, R117, R119, R120, R125, R130, R131, R137, R138, R139, R140, R143, R144, R149, R150, R151, R152, R159, R164, R165, R166, R167, R171, R174, R175, R176, R177, R179, R180, R181, R183, R184, R185, R186, R187, R189, R190, R191, R192, R197, R198, R199, R200, R201, R202, R203, R204, R205, R207, R208, R210, R211, R213, R214, R221 |
| no remedy stated | R145, R147, R155, R156, R170, R236, R247 |

Items by class: instrument-class (3) TGH-T3-01, TGH-T3-06, TGH-T3-10 · mixed (17) TGH-T2-01, TGH-T2-03, TGH-T2-04, TGH-T2-05, TGH-T2-08, TGH-T2-20, TGH-T3-03, TGH-T3-05, TGH-T3-09, TGH-T3-12, TGH-T3-13, TGH-T3-16, TGH-T3-19, TGH-T4-01, TGH-T4-02, TGH-T4-03, TGH-T4-04 · tier text (13) TGH-T2-02, TGH-T2-06, TGH-T3-02, TGH-T3-04, TGH-T3-07, TGH-T3-08, TGH-T3-11, TGH-T3-14, TGH-T3-15, TGH-T3-17, TGH-T3-24, TGH-T3-27, TGH-T4-05 · no same-gap row (21) TGH-T1-01, TGH-T2-07, TGH-T2-09, TGH-T2-10, TGH-T2-11, TGH-T2-12, TGH-T2-13, TGH-T2-14, TGH-T2-15, TGH-T2-16, TGH-T2-17, TGH-T2-18, TGH-T2-19, TGH-T2-21, TGH-T3-18, TGH-T3-20, TGH-T3-21, TGH-T3-22, TGH-T3-23, TGH-T3-25, TGH-T3-26.

## 2. Items, by tier and by consequence

### 2.1 T1: Product definition (1 item, 1 row)

Only one item is assigned to T1. T1's D2 agenda (R01, R72, R76) is cosmetic; this item is a substantive proposal and is for SS to admit or decline.

#### TGH-T1-01 · Computational correctness: "independent verification where required", sensitivity and "declared tolerance" have no owner

- **Rank / consequence:** rank 43 of 54; L1 (1); 1 TG row; 19 active assets in those layers.
- **Folded rows (1; L1):** TG-L1-022
- **Clause that failed to provide:** T1 §14 (L588): Computational correctness = "Authoritative inputs, reproducible calculations, units and conventions, sensitivity, independent verification where required". T3 §2.7 check c (L356) "beyond a declared tolerance". T2 §12.2 (L612, L613, L629): thresholds are "predeclared" by layer/asset briefs. T1 §11 (L501) scores L1 on this obligation.
- **What the drafts needed:** For L1's one scored obligation: which outputs REQUIRE independent verification, what sensitivity is owed, and who declares the tolerance. T3's own rule (L28-31: an instance may not invent a criterion) forbids the instance from declaring them; T2 delegates to the briefs; T1 leaves "where required" open.
- **Evidence:**
  - L1, chart 482012f1: `chart_facts.verification_pass_status` `two_pass_verified` 9,320 of 143,299 rows (6.5%); `chart_dashas` `two_pass_verified` 46,009 of 483,870 (9.5%); `single` 115,807 and 437,474 respectively. `tolerance_arcsec` populated on 8,775 of 143,299 rows (6.1%; the count equals `ga_sensitive`'s live rows, an equality the L1 draft did not trace to cause). `Carr.detector` NO_DETECTOR on 19 of 19 assets.
  - Related, not counted: L0 proposal (dropped list, section 3). T1 §14's fidelity evidence is worded for source-to-rule correspondence and does not say what "correct method identity" means for a computed quantity; L0's five computed assets (`bg_ephemeris` 825,084 · `bg_muhurta_lattice` 173,219 · `bg_gochara_arcs` 33,933 · `bg_sky_calendar` 31,081 · `bg_cohort` 110,000 live rows) are scored on fidelity while "Computational correctness" is scored on L1 (T1 L501). The L0 draft offered this to T1's owner as optional.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: R55. R55 concerns a different "sensitivity direction" (the L1 draft's own search); no row carries this gap. Remedy class: none (no same-gap register row).
- **Tier:** T1. Every draft named T1.
- **Proposed remedy (direction or options; not text):**
  - (a) T1 §14 states who declares "where required" (product-level default, or the layer instance, or the asset brief) and leaves the values to that owner.
  - (b) T1 unchanged; T2 §12.2 carries the declaration rule (the item then moves to T2 and out of this section).
  - (c) No edit: record "where required" as a delegation and have T3 §2.7 say so, so an instance reports that the tolerance is not declared (proposed wording) instead of inventing one.
- **SS ruling needed:** T1 is sealed and its agenda (T1 R01, R72, R76 per Track E §6) is cosmetic only. Whether T1 opens for a substantive edit, and whether the optional L0 proposal rides with it, is SS's call (N-4.T1).

### 2.2 T2: Data plane value architecture (21 items, 47 rows)

#### TGH-T2-01 · Which coverage obligations a layer owns: T2 §5 assigns no owner and no state

- **Rank / consequence:** rank 23 of 54; L2 L3 L5 (3); 3 TG rows; 59 active assets in those layers.
- **Folded rows (3; L2 L3 L5):** TG-L2-012, TG-L3-013, TG-L5-011
- **Also touches (not folded):** item TGH-T3-20 (the five-state vocabulary itself); item TGH-T4-04 (the declared-universe half: the L0, L1 and L4 rows folded there name this ownership half as well).
- **Clause that failed to provide:** T3 §2.4 (L301-311): "Which of the product's coverage obligations this layer owns … five states, never a blank". T2 §5 (L319-341) names a layer only inside cross-asset cells (L327 graha roles; L335 present interval; L336 Kāla; L337 Praśna/Muhūrta/calendar; L338 Āyurdāya) and assigns no owner and no state. T1 §3 gives substance, not owners.
- **What the drafts needed:** Per layer, the list of owned obligations with one of five states each.
- **Evidence:**
  - L2: T2 §5 names L2 in two rows (L327, L338) and §13.1 W04 (L640) gives it "Bhāvat Bhāvam scope … configuration and contradiction hydration"; the other eleven rows do not name L2; no per-obligation five-state detector exists. L3: five rows name L3 but nothing says they ARE its owned set. L5: no row is assigned to it (T2 §5 searched for "L5", "Mīmāṃsā", "evaluation").
  - Read from the rows folded in TGH-T4-04, which need this half too: L4 is named in three of thirteen rows (L327, L335, L338), none carrying an owner or state; L1 in two (L327, L338); L0 has no owner layer assigned to any §5 row.
  - The census has no coverage-state criterion (L2: no per-obligation five-state detector; L3: none in the census criteria). Its `Complete.width` reading (NOT_GENERIC on 23 of 23, 21 of 21 and 15 of 15 in these three rows' evidence) is the universe half, carried in TGH-T4-04.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 3 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R90*, R110, R142, R153, R168, R187, R202. Adjacent only: none. Cited by the L2 row for the universe half, carried in TGH-T4-04: R22. Remedy class: mixed (instrument: R142, R153, R168; both: R90; tier text: R110, R187, R202; see 1.7).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §5 gains an owner-layer column (R110's wording) and the per-obligation state convention.
  - (b) T3 states that an instance derives ownership only from the T2 §5 cells that name it and marks the remaining rows unassigned (the reading L3 and L4 had to make).

#### TGH-T2-02 · Which of the eight §3.4 presentation rows a layer carries (rows map to contracts, never to layers)

- **Rank / consequence:** rank 5 of 54; L0-L5 (6); 6 TG rows; 127 active assets in those layers.
- **Folded rows (6; L0 L1 L2 L3 L4 L5):** TG-L0-005, TG-L1-012, TG-L2-010, TG-L3-009, TG-L4-012, TG-L5-009
- **Also touches (not folded):** item TGH-T2-04; item TGH-T3-07; item TGH-T3-25 (the temporal row L3 finds supplied is the row L4 finds assigned to itself).
- **Clause that failed to provide:** T2 §13.3 item 6 (L682): the layer plan states "which §3.4 presentation rows this layer carries and which fields it hands onward for them". T2 §3.4 (L178-205; rows L188-197) maps rows to DP contracts only; T2 §7.1 (L418-437) maps contracts to producers. T3 §2.2 (L274-286).
- **What the drafts needed:** An assignment of the eight §3.4 rows to layers, or an explicit "none" per layer.
- **Evidence:**
  - L1 derived its rows by joining §3.4 to §7.1: clean for conventions (DP01/DP03), intermediate quantities (DP03/DP04) and dignity components (DP04); not clean for DP05 ("L0+L1 -> L2") and DP07 ("L0/L1/L3 primitives"), where which fields are L1's is unstated.
  - L0 chose three rows (method/school, conventions, alias set) without a clause; `Vocab.alias` FAIL: `bg_ontology`, dosha alias sets empty 79 of 79 (the row the alias set serves).
  - L2: derivable are "competing readings" (DP06 + DP02) and "chain of influence" (DP06); not derivable whether L2 must retain rows produced at L1 or L3. L3: the temporal row is supplied (T2 L197; T3 L284-286), the other rows are not. L4: no row-to-layer assignment. L5: no row maps to L5 (T2 §3.4 covers DP01-DP09 only); L5 also asks whether presentation parity (T3 §5.4 test 4 vs T2 §1 [TRANSFERS]) is its own work (see item TGH-T3-07).
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 6 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R89*, R108, R139, R151, R166, R184, R200. Adjacent only: none. Cited by the L5 row for its parity facet, carried in TGH-T3-07: R94*, R119*. Remedy class: tier text (R89, R108, R139, R151, R166, R184, R200; see 1.7).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §3.4 gains a "carried by layer" column (the direction R89 records for the T2 agenda).
  - (b) The per-layer roll-up in the item TGH-T2-04 supplies it by derivation; T2 then states that §3.4 rows are derived by the join and marks the DP05/DP07 shares.
  - (c) T3 §2.2 states that an instance derives its rows by the join and reports the un-joinable shares as unassigned.

#### TGH-T2-03 · Which of the sixteen entity classes a layer emits or accepts, and the independent-map census

- **Rank / consequence:** rank 19 of 54; L1 L2 L3 L4 (4); 4 TG rows; 72 active assets in those layers.
- **Folded rows (4; L1 L2 L3 L4):** TG-L1-014, TG-L2-013, TG-L3-015, TG-L4-016
- **Also touches (not folded):** item TGH-T2-20 (the population behind rules 4 and 6, folded from the L0 row); item TGH-T2-21 (the L5 row, which also asks which classes L5 emits, folded there for its event-class omission).
- **Clause that failed to provide:** T3 §2.6 (L313-328); T2 §4.1 rules 1 and 4-6 (L259-266) and its Scope sentence listing sixteen classes (L268-271); T2 §13.3 item 1a. T2 lists the classes plane-wide and assigns none to a layer.
- **What the drafts needed:** A layer-by-class table, alias coverage and the independent map per class.
- **Evidence:**
  - `local_map_candidates` in the census header: L1, L2, L3 and L4 each -1 (not measured).
  - L1: `Vocab.identity` measures only row identity (15 PASS, 2 NO_DETECTOR, no cell for 2 assets); no L1 cell tests that a name resolves through the controlled set; `brahmagyan/verification_vocab.py` is a controlled vocabulary for one field only. L2: `Vocab.identity` on 22 of 23 assets (none for `bo_samvada`). L4: only rule 1(i) (declared-key uniqueness) is measured, by `Vocab.identity`; no detector for rules 4, 5, 6.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 4 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R91*, R111, R143, R189, R203. Adjacent only: none. Remedy class: mixed (both: R91, R111; tier text: R143, R189, R203; see 1.7).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §4.1 gains the layer-by-class table (R91 puts this on the T2 agenda).

#### TGH-T2-04 · Per-layer (and per-asset) roll-up of DP contracts produced and consumed; who produces DP07/DP08/DP09

- **Rank / consequence:** rank 8 of 54; L0 L2 L3 L4 L5 (5); 6 TG rows; 108 active assets in those layers.
- **Folded rows (6; L0 L2 L3 L4 L5):** TG-L0-004, TG-L2-004, TG-L3-003, TG-L3-011, TG-L4-003, TG-L5-003
- **Also touches (not folded):** item TGH-T3-12 (L4 row also asks for the edge type per L4 edge); item TGH-T2-08; item TGH-T3-10.
- **Clause that failed to provide:** T2 §7.1 (L418-437) lists contracts as producer -> consumer with no per-layer roll-up; T2 §13.3 item 6 (L682); T3 §0.3 (L139-142) and §2.3 (L288-299) ask for contracts "produced" and "consumed" with field and grain.
- **What the drafts needed:** Per layer, the contracts produced and consumed with field, grain and identity; per asset, the mapping. Specific holes: which layer PRODUCES the temporal contracts, and what "consumed side" means.
- **Evidence:**
  - L3: DP08 reads "L2+qualified clocks -> L3 consumers" (L427), DP07 "L0/L1/L3 primitives -> temporal integrators" (L426), DP09 "L3+qualified structural/rule evidence -> L4" (L428); nothing states the DP08 producing layer. Register search for DP07/DP08/DP09 finds only rows that mention DP08 as an anchor; none records the producer/consumer ambiguity (the only row of this item with no register row).
  - L4: DP09 is named "Manifestation" (L4's own output) yet its cell reads L4 as consumer; DP12 (L431), DP14 (L433), DP15a (L434) name no producing asset; T2 §3.2 (L151) asserts direct qualified L0 reference use by L4 while the registry records only computational edges (41 declared edges: 19 intra-L4, 22 inbound from 16 assets).
  - L0: T2 names L0 for DP01, DP02, DP05, DP07; DP10 "All producers" includes L0; DP16 names no layer. What no clause supplies is which of them an instance states per asset and the consumed side. `F-05`: 0 of 46 L0 capability modules declare a `density_contract`.
  - L2: `asset_registry.provides_apis` empty on all 23 L2 rows; no produces/consumes column (42 columns). L5: only DP15b names "protected L5" (L435); the companion T2c §7 gives DP ids per L5 asset but no field or grain.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 5 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: R109, R141, R152, R167, R181*, R186*, R198*, R201*. Adjacent only: R130. Remedy class: mixed (instrument: R109, R141; tier text: R152, R167, R181, R186, R198, R201; see 1.7).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §7.1 gains a per-layer roll-up of contracts produced and consumed, each with its §3.2 edge type (the direction R198 and R181 record).
  - (b) Correct the DP07/DP08/DP09 producer cells so the L3 and L4 roles are explicit (the facet the L3 and L4 rows add).
  - (c) Registry `produces_contracts`/`consumes_contracts` columns (R109) are a registry/instrument change and stay with Track E.

#### TGH-T2-05 · One table with several producers: no expression in the contract vocabulary, and no declared write set where the registry carries one target pointer

- **Rank / consequence:** rank 10 of 54; L0 L1 L2 L3 L5 (5); 5 TG rows; 118 active assets in those layers.
- **Folded rows (5; L0 L1 L2 L3 L5):** TG-L0-010, TG-L1-005, TG-L2-005, TG-L3-024, TG-L5-019
- **Also touches (not folded):** item TGH-T3-16; item TGH-T3-18.
- **Clause that failed to provide:** T3 §1.1 (L161-175): "target table(s) — a set, not one pointer" (T3 already allows a set of tables per asset; it says nothing for many assets per table, or for where an asset's set is declared when the registry field holds one pointer). T2 §7.1 (L410 onward) and §13.3 (L662-690) carry no shared-table or per-producer count-scope clause.
- **What the drafts needed:** A way to declare a table with several producers, to scope each producer's `count_sql` to its own rows, and to list every table a multi-table asset writes.
- **Evidence:**
  - L0: three tables named by two or more assets: `brahma_ontology` (bg_ontology, bg_yogas, bg_doshas, bg_dasha_systems), `brahma_class_priors` (2), `classical_text_chunks` (2); `bg_prashna_rules.target_table` NULL over a 5-table `count_sql`.
  - L1: `chart_facts` is the declared target of 7 L1 assets and is also written by 3 more; `fact_category_ownership` names only 3 owners; 41,042 of the chart's 143,299 rows have no owner row; the `ga_strength` predicate matches 420 rows the ownership table assigns to `ga_structural`. Depth and provenance census cells are computed over the whole table (421,096 rows, all charts) for each producer.
  - L2: `bodha_msr_signals` has 7 registry producers, 6 owning rows (50,529 + 45 + 45 + 25 + 20 + 14 = 50,678 on the canonical chart) and one UPDATE-only; `bodha_cgm_nodes` has two writers (bo_bimba 255 + bo_karanajala 130 = 385 live); census depth prints 150,724 rows under all seven MSR producers.
  - L3: `kala_gochara_windows` has three registry producers (two inactive); `kala_insights` is inserted by two writers in two layers; `ka_kshetra` writes 15 tables while its structured registry fields name one. L5: `mi_bhara` writes five tables and declares one (`kala_field_skill`; the seed says `kala_field_weight_versions`).
  - L4: refuted (its draft §2.1 read every writer: no live second producer for any `phala_*` table), so L4 contributes no row.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 5 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R06*, R10*, R95, R97, R103, R136, R205, R240 [CLOSED], R247. Adjacent only: none. Remedy class: mixed (instrument: R136; tier text: R06, R10, R95, R97, R103, R205; no remedy stated: R247; see 1.7).
- **Tier:** T2. Drafts named: T2 x2 (L0 L1) · T3 x3 (L2 L3 L5). Sources: L0 and L1 say T2 (following R06), L2, L3 and L5 say T3 (the inventory clause they had to fill). Assigned T2: producer declaration is a contract-vocabulary rule and T3 §1.1 inherits from T2 §13.3. The T3 §1.1 half stays as R10 on the T3 agenda, so the merged agenda holds both halves of one decision.
- **Proposed remedy (direction or options; not text):**
  - (a) A clause in T2 §7.1 or §13.3 under which a shared table declares its producers and each producer's `count_sql` is scoped to its own rows (R06 leaves the exact clause to the agenda).
  - (b) T3 §1.1 inventory rows for a producer set (R10's half, already on the T3 agenda).
  - (c) Producer-scope columns in the registry are Track E.

#### TGH-T2-06 · Life-event switch: per-table classification (event-free versus event-conditioned overlay) and the identity of an event-time context

- **Rank / consequence:** rank 26 of 54; L3 L4 L5 (3); 3 TG rows; 45 active assets in those layers.
- **Folded rows (3; L3 L4 L5):** TG-L3-007, TG-L4-009, TG-L5-007
- **Also touches (not folded):** item TGH-T3-15 (the detector half: it folds the L0 and L1 rows that v1.0 placed here, narrowed to the detector only). The L1 row's second facet, what an event-time context's identity is, stays here as a rider (see remedy (c)); it is not a folded row of this item.
- **Clause that failed to provide:** T3 §2.1 (L261-272): "what this layer may do when ON, what it emits when OFF, and the storage separation that makes OFF a selection rather than a rebuild". T2 §9.2 (L493-517) supplies the ON row per layer (L500), the OFF row (L501) and the storage separation once for the plane (L510-512); T1 §8.1 (L422-427) the per-layer rules; T1 §7.2 (L382) the switch state in the emission record; T2 §6.2 (L359) "separate context identities".
- **What the drafts needed:** NARROWED by four layer drafts (L0, L1, L2, L5): the layer-grain ON/OFF is supplied. What no tier supplies is the per-table classification that makes the OFF state a selection rather than a rebuild checkable and, as a rider from L1, what an event-time context's identity is.
- **Evidence:**
  - L3: `find *circularity*` returns 3 test files (2 of 21 L3 assets by file name; contents not verified). L4: literal `life_events`/`lel_` reads in `ph_pramana.py` and `ph_rectification/__init__.py` only; no column named for switch state or information cutoff across ten `phala_*` tables.
  - L5: every hit for a switch-state term is `kill_switch_state` (a claim-family kill switch), none a life-event switch; a differently named mechanism was not assessed (T2c §8 L205 names `lel_capable`, `registry/types.ts:180`).
  - L2 (not a gap row): its draft found T2 §9.2's ON row per layer supplies the switch; what remains, that no L2 asset yet implements the ON comparison, is a layer finding.
  - Rider, from the L1 row folded in TGH-T3-15: none of the 19 L1 assets is named event-time, and whether any writes an event-time context is not measured; T2 §6.2 says event-time calculations use "separate context identities" without saying what an event-time context's identity is.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 3 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R88*, R107, R138, R150, R165, R191, R199. Adjacent only: none. Remedy class: tier text (R88, R107, R138, R150, R165, R191, R199; see 1.7).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §9.2 gains the per-layer, per-table table R88 records (the register notes its own remedy is partly satisfied by the ON/OFF rows above).
  - (b) T3 §2.1 says the instance classifies its tables and reports the unclassifiable ones.
  - (c) Define an event-time context's identity (T2 §6.2) so the OFF selection has a key (the L1 rider). The detector half is in the item TGH-T3-15.

#### TGH-T2-07 · May an upstream rebuild physically delete downstream rows (foreign-key CASCADE across layers)? No tier says

- **Rank / consequence:** rank 24 of 54; L2 L3 L4 (3); 3 TG rows; 53 active assets in those layers.
- **Folded rows (3; L2 L3 L4):** TG-L2-022, TG-L3-027, TG-L4-023
- **Clause that failed to provide:** T2 §11 (L564-576) and DP16 (L436) speak of dependency-specific stale marking, not deletion; T2 §3.3 (L172), §4.4 (L313-315); T3 §4.3 (L448-454); T3 §5.2 Idem row (L532: "a rebuild replaces its own rows; it never accretes") bounds accretion but not collateral deletion; T4 §4.2 check 6 (L277) and T3 Build gate (L539) do not classify why a build record and live count differ.
- **What the drafts needed:** A clause on whether an upstream rebuild may delete downstream rows through a foreign key, and what the Idem and Build gates report when it does.
- **Evidence:**
  - L2 (Q2): eight `ON DELETE CASCADE` keys from seven tables onto `bodha_msr_signals`, five cross-layer (`kala_*`), the closure reaching `phala_anchors` (L4). An L2 rebuild passes the Idem detector while a foreign key deletes L3 rows; R246's detector is scoped to restrictive keys, so CASCADE keys have no detector row.
  - L3: the five L3 tables under those keys (`kala_activation`, `kala_bhavishya`, `kala_convergence`, `kala_darshana`, `kala_obstruction`) belong to assets (`ka_kalasutra`, `ka_bhavishya_lekha`, `ka_sangam`, `ka_kala_darshana`, `ka_vighnakara`) whose live rows are 0 on the canonical chart; cause inferred from the keys, not measured.
  - L4: `ph_nimitta`, `ph_pramana`, `ph_suddha_sodhana` each record 139 rows written against 4 present (`Build.completion` FAIL); `phala_anchors.convergence_id` is a CASCADE key to `kala_convergence` (0 rows while `ka_sangam` records 14,868 written); the pattern is consistent with cascade removal of 135 anchors, not proven; `ph_muhurta`'s 5-row gap has no cascade path and is unexplained.
  - Context: Track A brief §4 records that F-3 (decision N-32) drops the eight keys, so the concrete instance is being removed by F3.FK; no tier states the rule the keys broke.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 2 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: R237, R243, R244, R246, R249. R237 is the 139-versus-4 data finding (open); R243/R244 are the L2 side; R246 is scoped to restrictive keys only; R249 is adjacent. Remedy class: none (no same-gap register row).
- **Tier:** T2. Drafts named: T2 x1 (L3) · T3 x1 (L2) · T4 x1 (L4). Sources: L2 says T3 (Idem row), L3 says T2 (§11/DP16), L4 says T4 (check 6). Assigned T2: the rule concerns producer-to-consumer coupling across layers, which T2 §11 governs; the T3 and T4 gate wording follows from it.
- **Proposed remedy (direction or options; not text):**
  - (a) one option, since the sources only ask whether: T2 §11 gains a rule that an upstream rebuild marks dependents stale and does not delete them; T3 Idem and T4 check 6 inherit it.
  - (b) Treat F-3/N-32 as the resolution and record the gap as closed by construction (no plane clause).
  - (c) T4 §4.2 check 6 / T3 Build gate gain a cause classification (writer over-reported versus rows removed by another asset) and an owner for the repair (the L4 row's second facet; hand to the T4 revision).
- **SS ruling needed:** Whether the plane needs a rule at all once F-3 removes the eight keys, or whether F-3 is the whole answer (option b), is a scope decision for SS.

#### TGH-T2-08 · Declared use of each consumed input ("a citation with no declared use is not a contract") exists nowhere as data

- **Rank / consequence:** rank 27 of 54; L3 L4 L5 (3); 3 TG rows; 45 active assets in those layers.
- **Folded rows (3; L3 L4 L5):** TG-L3-012, TG-L4-013, TG-L5-010
- **Also touches (not folded):** item TGH-T3-10 (L1 and L2 rows also carry the declared-use facet); item TGH-T2-04.
- **Clause that failed to provide:** T2 §7.1 (L415-416): "Every consumer declares whether an input contributes to calculation, applicability, counter-evidence, uncertainty, interpretation, exclusion, navigation or evaluation". T3 §2.3 (L288-299): "A citation with no declared use is not a contract."
- **What the drafts needed:** A declared use for each consumed input: L3 has 52 cross-layer plus 31 intra-layer `depends_on` edges for its 21 active assets; L5 has 18 cross-layer and 21 intra-layer edges; L4 needs a use per consumed contract per asset.
- **Evidence:**
  - `depends_on` is a bare asset-id array with no use attribute; `Build.dag` reports edge counts and resolvability only; no `produces_contracts`/`consumes_contracts` column on `asset_registry` (L3, L4, L5 reads). L5's companion T2c §7 lists receiving contracts, not uses.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 3 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R109, R186*, R201*. Adjacent only: none. Remedy class: mixed (instrument: R109; tier text: R186, R201; see 1.7).
- **Tier:** T2. Drafts named: T2 x2 (L3 L4) · T3 x1 (L5). Sources: L3 and L4 say T2, L5 says T3. Assigned T2: the obligation is stated at T2 §7.1 (L415-416) and T3 §2.3 restates it; what is missing is the content of the uses per contract, which is contract-level and belongs where the contracts are. R186 (T2 §7.1) and R201 (T3 §2.3) both sit on the D2-ruled agenda; the merged agenda should keep one of them.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §7.1 gains a declared-use column per contract, so instances inherit rather than author (R186's direction).
  - (b) T3 §2.3 names the source of declared uses (a per-contract use registry, or the census) (R201's direction).
  - (c) A per-edge use attribute in the registry (R109), which is Track E. The agenda should pick one of (a) and (b); both are on the reopen agendas.

#### TGH-T2-09 · Three unreconciled lists of epistemic kinds, and no layer-template home for typing outputs by kind

- **Rank / consequence:** rank 33 of 54; L1 L5 (2); 2 TG rows; 34 active assets in those layers.
- **Folded rows (2; L1 L5):** TG-L1-020, TG-L5-014
- **Clause that failed to provide:** T2 §3.3 (L176): L1 outputs are typed as "astronomical calculation, classical-rule application, engineered/native judgment, approximation, observation or empirical/model result" (six kinds). T1 §5.2 (L324-326): "deterministic fact, structural prior, classical prior, empirically calibrated claim and unresolved interpretation" (five). T2 §6.6 (L402): "stored evidence, structural estimates, actual measured performance and service readiness" (four); T2 §12.2 (L626) "Empirical performance" test. No T3 section receives the typing (nearest: §2.7, §4.4).
- **What the drafts needed:** One vocabulary, a home for it in the layer template, and a detector, so an instance can type its outputs without inventing kinds.
- **Evidence:**
  - L1: `ga_writers/data_plane_contracts.py:48-55` defines an `EpistemicClass` of seven members that differs from T2's six (`observation` and `empirical/model result` absent; three code members absent from T2); `epistemic_class` is used in two files only and none of the `ga_*_writer.py` assigns one.
  - L5: row-level labels found: `mimamsa_reliability.evidence_grade` {empirical 4, prior_only 2}; `mimamsa_multipliers.promotion_status` {promoted 2, prior_only 7}; `mimamsa_signal_families.calibration_status` prior_only 11 of 11; `mimamsa_qa_eval.status` {structural_proxy 10, not_implemented 4, control_baseline 92, FAIL_event_too_close 61, pass 1}; `mimamsa_calibration_snapshot.publication_status` proposed 4 of 4; `mi_pramana.py:535-536` `grade = "empirical" if n >= 5 else "prior_only"` (a count threshold). `Count.floor` N/A 15 of 15.
- **Register:** new: no open same-gap register row. Rows: 1 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. Cited by the L5 row for other clauses (its own wording: it adds the state vocabulary itself): R99 [PARTIAL] (empty by design) and R210 (no detector for the layer's own scored obligation). No row carries the vocabulary. Remedy class: none (no same-gap register row).
- **Tier:** T2. Drafts named: T2 x1 (L5) · T3 x1 (L1). Sources: L1 says T3 (no template section), L5 says T2 (the lists differ). Assigned T2: the defect is three plane-level lists that disagree, and reconciling them precedes any template home. The fold is borderline: the L1 row asks for a template home for per-asset typing and the L5 row for a reconciled vocabulary; they share only the reconciliation step, and E2 may split them.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 designates one list canonical (mapped to T1 §5.2) and maps the others onto it.
  - (b) T3 gains a per-layer/per-asset epistemic-kind field (proposed name) in §2.2 or §4.4.
  - (c) Adopt the code's seven-member vocabulary as the reference and map T1/T2 lists to it (owners to accept).
- **SS ruling needed:** If the reconciliation must change T1 §5.2 (the product definition) instead of mapping T2's lists onto it, the item belongs to the T1 agenda and needs SS's ruling on which list is authoritative.

#### TGH-T2-10 · Four disposition vocabularies across T1, T2, T3, T4 (and a fifth in the campaign brief)

- **Rank / consequence:** rank 35 of 54; L0 (1); 1 TG row; 40 active assets in those layers.
- **Folded rows (1; L0):** TG-L0-002
- **Clause that failed to provide:** T1 §11.1 (L516-517): "preserve, wrap, enrich, qualify, consolidate, replace only the inadequate part, or retire". T2 §10.1 (L531-544), T3 §3.2 (L396-406) and T4 §0.1 row 8 (L97): P/I/E/Q/C/H/R/U.
- **What the drafts needed:** One vocabulary to disposition 40 L0 assets and a stated crosswalk (P = keep).
- **Evidence:**
  - Text comparison of the four clauses (no measurement). "Wrap" and "replace only the inadequate part" have no letter; "integrate", "historical" and "unresolved" are absent from T1. The Track A brief §5 (a campaign document, not a tier) uses a fifth wording: keep/integrate/enrich/qualify/consolidate/historical/retire/unresolved. Terms searched: "wrap", "keep" in T2/T3/T4.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: R93*. R93 concerns evidence-to-disposition (the item TGH-T3-03), a different gap. Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T1 §11.1 wording aligned to the eight letters.
  - (b) T2 §10.1 adds a one-line crosswalk from T1's wording to the letters.
  - (c) Campaign documents adopt the letters (outside the tiers).

#### TGH-T2-11 · What an L0 "generation" is and how an L0 change reaches charts other than the canonical one

- **Rank / consequence:** rank 36 of 54; L0 (1); 1 TG row; 40 active assets in those layers.
- **Folded rows (1; L0):** TG-L0-009
- **Clause that failed to provide:** T2 §11 (L566-568) and DP16 (L436): a consumer pins the producer generation it consumed and gets dependency-specific stale marking; T2 §1 (L58) "L0 remains the global foundation"; T3 §4.3 (L448-454).
- **What the drafts needed:** The L0 generation and invalidation statement, and the impact of an L0 change on other charts.
- **Evidence:**
  - `build_runs` has 734 rows, 0 with a null `chart_id`; L0 assets appear in 118 `build_run_assets` rows across 51 runs (scope `asset_set` 50, `layer` 1), all carrying a chart id (482012f1 x50, 1c826d5a x1); the 61 runs with scope `global` touch no L0 asset (Q-10, CEN-H).
  - Charts 1c826d5a and cb73cd3d hold 3,777,160 and 910,263 rows in the 86 L1-L5 tables the census names (canonical: 9,645,121), built against L0 as it then stood (Q-13). Track A brief §4 records N-12 (canonical chart only; the others served from stale L0 inputs, disclosed per N-33).
  - A pin exists for L0 code: `nirmana-analysis-layer-pins.json` current generation `l0:d2369b888e76:3dda261170ee`; it pins writers, not consumers' recorded generations. L1 adds that `l1_data_plane_generations` (migration 1035) exists but the reader login cannot read it (measurement finding).
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: R87. R87 (deployed versus code) is a different gap. Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §11 defines an L0 generation and the pin a consumer records.
  - (b) Adopt the existing writer-pin generation identifier as the L0 generation if its owners accept it (fact from the L0 draft, not a tier statement).
  - (c) State that L0 changes are disclosed rather than propagated (the N-12/N-33 position) and say so in T2 §11.

#### TGH-T2-12 · No tier defines a "release" of the controlled vocabulary (identity, digest, minter, consumer pin)

- **Rank / consequence:** rank 37 of 54; L0 (1); 1 TG row; 40 active assets in those layers.
- **Folded rows (1; L0):** TG-L0-008
- **Clause that failed to provide:** T2 §4.1 rules 1, 3, 4 (L261, L263, L264), §4.4 (L313-315), DP01 (L420), W02 (L638) all use "release", "release id", "content digest", "governed release"; nowhere is a release defined. T2 §15 (L703) lists "per-field release bindings" as unresolved. T3 §2.6 (L326-328) makes L0's section 2.6 "state the authority, its releases".
- **What the drafts needed:** The release of the controlled vocabulary L0 owns: what identifies it, its digest, where stored, who mints it, how a consumer records the one it consumed.
- **Evidence:**
  - L0 (Q-09): `brahma_ontology` has 9 columns (id, entity_class, canonical_id, canonical_name_en, canonical_name_sa, synonyms, description, source_citation, created_at), none a release or version; no table in `public` has a name matching `release` or `vocab`; 24 of 66 L0 tables carry some version/build/digest-like column, the ontology not among them.
  - Q-11: `asset_provenance_receipts` holds 37 L0 rows (35 proven, 2 unknown), a possible mechanism the tiers never name (searched T1-T4 for "provenance_receipt", "release id").
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §4.4 (or DP01) defines a release: identity, digest, minter and the consumer's recorded pin.
  - (b) Name an existing mechanism as the release record if the owners accept it (the only candidate the L0 draft found is the receipts table above).
  - (c) Leave as §15's open item and record it as unresolved.

#### TGH-T2-13 · L2's own correctness rule (shared roots are not independent confirmations): the carrier field and counting procedure are unsupplied

- **Rank / consequence:** rank 39 of 54; L2 (1); 1 TG row; 23 active assets in those layers.
- **Folded rows (1; L2):** TG-L2-021
- **Clause that failed to provide:** T1 §3.4 (L222-224), T1 §11 (L502), T3 adaptation row (L681), T4 (L506), T2 §4.2 (L297), §5 (L323, L330), DP06 (L425), §12.2 Dependence control (L618). The tiers supply the unit of independence (a placement) and the principle (do not manufacture independent evidence). Not supplied: which field carries a root, and how independent support is counted for a signal from a composite of placements.
- **What the drafts needed:** The data-level carrier of a shared root and the counting rule.
- **Evidence:**
  - Columns named for it exist and read NEVER populated: `shared_factor_keys_jsonb` and `cross_domain_shared_factor_count` on `bodha_msr_signals`, `shared_factor_keys_jsonb` and `shared_signals_high_convergence_count` on `bodha_cdlm_cells` (`Complete.depth`, `bo_arudha`, `bo_sangati`); both MSR columns are null on all 50,678 canonical-chart rows (Q3).
  - A different pair, `system_convergence_count` and `cross_system_consensus_count`, is filled on 50,023 of 50,678 rows by `bo_laksana_rerank`, which counts signals sharing a `chart_facts.fact_subject` (`bo_laksana.py` 3726-3752): the code's unit of sharing is an engineering choice no tier states.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. No row found (register searched for root, ancestry, dependence, independent confirmation). Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 (§4.2 or DP06) names the carrier field family and states the counting rule.
  - (b) T2 states only the counting rule and leaves the carrier to the asset brief.

#### TGH-T2-14 · The criterion separating "nearest" from "better-supported later" windows, and who declares it

- **Rank / consequence:** rank 40 of 54; L3 (1); 1 TG row; 21 active assets in those layers.
- **Folded rows (1; L3):** TG-L3-018
- **Clause that failed to provide:** T1 §3.10 (L267-268), §7.1 (L375-377), §11 (L503); T2 §3.4 (L197), §6.4 (L382 "using declared criteria"), §12.2 (L629 "Layer/asset briefs predeclare appropriate thresholds"); T3 adaptation table (L682). All say "under a named criterion".
- **What the drafts needed:** The criterion or admissible criteria, a bound on the admissible set, and whether the L3 instance or an asset brief declares it. PARTLY supplied as a delegation: T2 L382 and L629 hand the choice to the briefs (L629 is worded for accuracy thresholds, so it delegates by analogy only).
- **Evidence:**
  - Search: "criterion" in T2 hits L197, L298 (a different use) and L382; T1/T3 give the requirement only. Register keyword search ("named criterion", "nearest", "better-supported") finds nothing. The L3 instance therefore cannot state its temporal-integrity comparison rule and must not invent one.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §6.4 states who declares the criterion (instance or asset brief): minimal.
  - (b) T2 supplies an admissible-criteria set. This needs domain content the harvest must not supply; it is for the owner of the L3 design.

#### TGH-T2-15 · T2 W05 tells the reader to reconcile an artefact it never identifies

- **Rank / consequence:** rank 41 of 54; L3 (1); 1 TG row; 21 active assets in those layers.
- **Folded rows (1; L3):** TG-L3-026
- **Clause that failed to provide:** T2 §13.1 W05 (L641), §14 (L690-693), §15 (L701): "reconcile the Kāla layer's existing temporal plan and its recorded gap assertions"; "Historical L3 research remains preserved in the original strategic worktree".
- **What the drafts needed:** The path, version or commit of the artefact W05 reconciles. The L3 instance §4.2 (the only work packet the tiers supply for L3) cannot cite its input.
- **Evidence:**
  - Search for "strategic worktree" / "existing temporal plan" in T1-T4 hits T2 L641, L693, L701 only; no identifier. Register keyword search finds nothing.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 W05 names the artefact (path/commit). This is a fact the harvest does not have; the owner of the L3 plan must supply it.
  - (b) T2 states the artefact is superseded by the current L3 work and W05 lapses.

#### TGH-T2-16 · Which L1 rows owe a unit is stated nowhere

- **Rank / consequence:** rank 44 of 54; L1 (1); 1 TG row; 19 active assets in those layers.
- **Folded rows (1; L1):** TG-L1-024
- **Also touches (not folded):** item TGH-T1-01 (T1 §14 "units and conventions" is the same sentence).
- **Clause that failed to provide:** T1 §14 (L588) and §11 (L501) name "units and conventions" / "values, units, precision"; T2 §7.1 DP03 (L422) carries "grain/value/unit"; T2 §5 (L295, L329) lists units inside calculation-convention and bala/dignity rows; T2 §7 (L410) leaves unnamed fields "to bind in layer/asset briefs".
- **What the drafts needed:** A rule for which L1 rows owe a unit and which are unit-free by nature (a sign or nakshatra name).
- **Evidence:**
  - `chart_facts.unit` is non-empty on 82,611 of 143,299 rows (57.6%); which of the remaining 60,688 are correctly unit-free is stated by no tier, so the figure cannot be graded either way. Every hit for "unit(s)" in T1-T4 demands units as a field or convention; none says which rows owe one. The register has no row containing "unit".
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §7.1 DP03 states which fact classes owe a unit and that unit-free classes declare so.
  - (b) Leave to asset briefs (T2 §7 already defers unnamed fields) and have T3 record the rule.

#### TGH-T2-17 · The companion register cites a contract (DP18) that T2 FINAL eliminated; L5's "next-generation artifact edge" has no live contract id

- **Rank / consequence:** rank 46 of 54; L5 (1); 1 TG row; 15 active assets in those layers.
- **Folded rows (1; L5):** TG-L5-004
- **Clause that failed to provide:** T2c §7 (L176-192) and T2 FINAL changelog (L46): "ELIMINATED … DP18 future-qualification … RETAINED deliberately: DP01-DP17". T2 §3.2 edge 5 (L164).
- **What the drafts needed:** A live contract id for L5's next-generation artifact edge, which the companion assigns to DP18.
- **Evidence:**
  - 10 of the 15 L5 rows in T2c §7 cite DP18 (`mi_pramana`, `mi_kula`, `mi_gunanaka`, `mi_adhilepa`, `mi_pariksha`, `mi_sambandha`, `mi_darshana`, `mi_seva`, `mi_bhara`, `mi_sankalpa`; `grep -E "DP[0-9/]*18"` on L176-192); T2 FINAL defines DP01-DP17 only; T2c also cites an unsplit DP15 where FINAL has DP15a/DP15b (0 hits for either in T2c). Register: no row mentions DP18.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) Correct T2c (the companion; status PROPOSED, not a tier) to DP01-DP17 and DP15a/b. This is outside the three tier agendas.
  - (b) Give T2 §3.2 edge 5 a contract home in DP01-DP17 or state that it has none.

#### TGH-T2-18 · Ownership of admitted observations, protected claims, generated candidates and filing ledgers is deferred to a contract that does not exist

- **Rank / consequence:** rank 47 of 54; L5 (1); 1 TG row; 15 active assets in those layers.
- **Folded rows (1; L5):** TG-L5-006
- **Clause that failed to provide:** T2 §9.1 (L487-491) "Choose the canonical owner in the L5/intake contract" and §15 (L703); W08 (L644) is the packet; DP13 (L432). T3 has no section that receives a decision T2 defers to it.
- **What the drafts needed:** Ownership of (a) admitted observations, (b) protected issued claims, (c) generated candidates, (d) explicit-filing and detection ledgers, and which layer plan holds each.
- **Evidence:**
  - Six claim/observation tables measured for chart 482012f1: `life_events` 63, `brahma_prospective_ledger` 18, `brahma_mimamsa_prediction_ledger` 5, `mimamsa_predictions` 139, `mimamsa_intervention_ledger` 0, `mimamsa_journal` 0. No active asset declares either `brahma_*` ledger as a target or in a `count_sql`.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. No row found (the Phase-4 skeleton noticed the question in prose). Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §9.1/§15 resolves the owner (a decision, not text the harvest can draft).
  - (b) Hand it to W08 and give T3 a section that receives deferred decisions.

#### TGH-T2-19 · "No unqualified composite score" is stated only at layer level; the asset-level rule, column classification and detector are unsupplied

- **Rank / consequence:** rank 52 of 54; L4 (1); 1 TG row; 9 active assets in those layers.
- **Folded rows (1; L4):** TG-L4-019
- **Also touches (not folded):** item TGH-T3-15.
- **Clause that failed to provide:** T1 §11 (L504); T2 §3.1 (L143), §6.5 (L392), §13.1 (L642); T3 adaptation (L683); T4 (L508); typed confidence T1 §5.2 (L324-326); T1 §3.3 (L209-211). No tier names `ph_pramana`'s gate or any asset-level rule; "D5" appears in no tier; no tier says which L4 columns are scores, probabilities or grades.
- **What the drafts needed:** For the `ph_pramana` NO-SCORING gate and for L4 generally: the asset-level rule, the column classification and a detector.
- **Evidence:**
  - The tiers state it in three strengths ("no unqualified composite score", "does not calibrate itself", T2c "retain hard no-scoring"). The gate exists only in code (`ph_pramana.py` `_d5_gate()`: build-halt on eight forbidden field names) and the L4 close record.
  - Measured tension (recorded, not resolved): the gate scopes to `phala_pramana` (14 columns, none forbidden) while `phala_anchors.posterior` is populated on 4 of 4 chart rows (`services/ph_nimitta/base_rate.py:10` "posterior = base_rate x lifts") and `phala_muhurta.composite_quality` on 134 of 134; score-bearing columns exist in five L4 tables. T1 §3 (L186-188) defines "qualified" but no tier names the record to test these columns against. `Carr.detector` NO_DETECTOR x9; no census check for score absence.
  - Namespace note from the L4 draft: the code decision "D5" is unrelated to the campaign's "D5 rev. 2.1" (R85, R218-R221).
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. No row found (register searched for composite, D5, no-scoring). Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §6.5 states the asset-level rule and what a "qualified composite" is by reference to T1 §3 (L186-188).
  - (b) The column classification (scores / probabilities / grades) is made in L4 asset briefs.
  - (c) The detector is the item TGH-T3-15's.

#### TGH-T2-20 · The population behind T2 §4.1 rules 4 and 6 (which code-side representations, which independent maps) is undefined

- **Rank / consequence:** rank 34 of 54; L0 (1); 1 TG row; 40 active assets in those layers.
- **Folded rows (1; L0):** TG-L0-011
- **Also touches (not folded):** item TGH-T2-03 (the layer-by-class table, whose rows cite the same register row).
- **Clause that failed to provide:** T2 §4.1 rules 4-6 (L264-266): "parity test per snapshot per language" and "a census detector per entity class that … fails above one". T3 §2.6 (L323-324) repeats them. Neither defines the population of code-side snapshots or what counts as an independent map.
- **What the drafts needed:** A measurable reading of rules 4 and 6 for L0. The L0 v3.0 draft reported 6 candidate sites; the inspector reports 32 under a different, unstated population.
- **Evidence:**
  - `local_map_candidates` in the census header: L0 32 (11 of the 32 in `l0_*` files); the inspector counts every `.py` file under `platform/python-sidecar/brahmagyan` (125 files, which holds L0-L5 code) that contains a quoted `Sun` followed by `,` or `:` and a quoted `Venus`: a text heuristic, not a per-class map detector (F-08, F-09). 10 vocabulary/parity test files sit at the top of `python-sidecar/tests`; whether every snapshot has one is unmeasurable without a snapshot inventory (F-10).
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 1 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R91*, R111, R203. Adjacent only: none. R91 asks for a per-class map census; no register row carries the population behind rules 4 and 6 (the facet the L0 draft adds). Remedy class: mixed (both: R91, R111; tier text: R203; see 1.7).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §4.1 defines the population for rules 4 and 6 (which code-side representations are in scope, what makes a name-to-id map independent): the facet the L0 draft adds to R91.
  - (b) The census then counts against that population (R91's census half; Track E).

#### TGH-T2-21 · T2 §4.1 governs "event class" in its opening sentence and leaves it out of its Scope list of sixteen classes

- **Rank / consequence:** rank 49 of 54; L5 (1); 1 TG row; 15 active assets in those layers.
- **Folded rows (1; L5):** TG-L5-012
- **Also touches (not folded):** item TGH-T2-03 (the same row also asks which classes L5 emits or accepts).
- **Clause that failed to provide:** T2 §4.1 (L247-248): every "entity, concept, method, convention, unit and event class" has one canonical identifier and one closed alias set; its Scope sentence (L268-271) lists sixteen classes: planets, signs, houses, nakshatras, vargas, karakas, aspect types, upagrahas, yogas, doṣas, daśā systems, domains, concepts, remedy types, texts, schools. Event class is not among them. T3 §2.6 (L313-328) asks which of the sixteen classes a layer emits.
- **What the drafts needed:** L5's emitted vocabularies mapped to classes (domain, event class, lifecycle state, verdict, study arm, evidence grade), which needs the omission resolved.
- **Evidence:**
  - L5 columns naming event classes: `mimamsa_intervention_ledger.event_class`, `kala_field_skill.event_class`, `mimamsa_event_provenance.event_class_id` (`census: mi_jivanaghatana Complete.depth`: never populated). `census: local_map_candidates` = -1 (map census not measured).
- **Register:** new: no open same-gap register row. Rows: 1 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: none. Adjacent only: none. Cited by the L5 row for its layer-by-class facet, carried in TGH-T2-03: R91*, R111, R203. None of them records that event class is governed by the opening paragraph of §4.1 and absent from its Scope list. Remedy class: none (no same-gap register row).
- **Tier:** T2. Every draft named T2.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §4.1 adds event class to the Scope list, or states that it is outside the rule's scope.

### 2.3 T3: Layer definition and strategy template (27 items, 97 rows)

#### TGH-T3-01 · The gate map's right-hand column (Ldgr sources, Earn claims, Null convention, Narr flag) has no source; the census registers no Null or Narr criterion

- **Rank / consequence:** rank 1 of 54; L0-L5 (6); 6 TG rows; 127 active assets in those layers; 254 gate cells the census cannot grade (the Null and Narr rows only: 2 gates x 127 active assets; `Earn.build_record` NO_DETECTOR on 127 of 127 and `Ldgr.source_presence` with no reading for 42 of the 103 L0-L3 assets are counted separately and not added).
- **Folded rows (6; L0 L1 L2 L3 L4 L5):** TG-L0-025, TG-L1-019, TG-L2-020, TG-L3-025, TG-L4-020, TG-L5-031
- **Also touches (not folded):** item TGH-T3-14; item TGH-T3-22.
- **Clause that failed to provide:** T3 §5.2 (L567-585): the instance "fills the right-hand column and reports any row it cannot fill", nine rows (Null L577, Narr L580); §5.4 test 5 (L629). T4 §4 (L227, L230): Null "always", Narr "if it emits prose".
- **What the drafts needed:** Per asset: the upstream `fact_id` sources (Ldgr), which emitted states are claims and what falsifies each (Earn), the asset's null convention, whether and where it emits prose, and a decision on the unit of a cell (per asset or per gate: L1 counted 19 x 9 = 171).
- **Evidence:**
  - The census `CRITERION_REGISTRY` registers no `Null` and no `Narr` criterion (F-08): 2 of the 9 gates x 127 active assets = 254 cells unreadable across the six layers (L0 alone: 80 of 360). `Earn.build_record` NO_DETECTOR on every asset read (40, 19, 23, 21, 9, 15).
  - `Ldgr.source_presence` reads 24 of 40 (L0; no reading for 16 including `bg_rules`, whose citation column is `verse_ref`), 13 of 19 (L1; absent for `ga_condition`, `ga_prashna`, `ga_strength`, `ga_structural`, `ga_transit_anchors`, `ga_vargas`), 16 of 23 (L2) and 8 of 21 (L3): 42 of the 103 L0-L3 assets have no reading; the L4 and L5 drafts give none. L3: `Vocab.identity` declared keys exist for 17 assets, 8 declare only a surrogate, and the registry's `natural_key_partition` gives a different key for three (`ka_sangam`, `ka_bhavishya_lekha`, `ka_kala_darshana`).
  - L4: `phala_phaladesa` has `narration_status`, `narration_requested_at`, `narration_model`, `narration_jsonb` (the census reports the second and third NEVER populated and the fourth dark), yet no Narr row exists. L5: 20 distinct criterion keys, none for Null or Narr; the instance marks both rows "cannot fill".
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 4 same-gap / 1 adjacent-only / 1 none. Same-gap rows cited: R161, R193, R194. Adjacent only: R65*, R67*, R128. Cited by the L3 row for other clauses and carried where the clause lives: R08* (TGH-T3-14), R92 and R144 (TGH-T3-02), R143 (TGH-T2-03). R161, R193, R194 (Null, Narr) and the adjacent R128 are open and not on the D2-ruled 31; the adjacent R65 and R67 (the counts, TGH-T3-27) are on it. Remedy class: instrument-class (R161, R193, R194; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §5.2 states the source of each right-hand cell (registry field, instance author, or the honest "cannot fill").
  - (b) A per-asset null-convention and prose declaration in the registry or T4 §1.
  - (c) Census criteria for Null and Narr (R193, R194) are Track E.

#### TGH-T3-02 · Per-asset carriage check (D1 / D2 / D3): the template assigns it at layer scope only

- **Rank / consequence:** rank 2 of 54; L0-L5 (6); 6 TG rows; 127 active assets in those layers; 127 gate cells the census cannot grade (NO_DETECTOR, NOT_GENERIC or no criterion).
- **Folded rows (6; L0 L1 L2 L3 L4 L5):** TG-L0-018, TG-L1-015, TG-L2-014, TG-L3-016, TG-L4-017, TG-L5-013
- **Clause that failed to provide:** T3 §2.7 (L330-363): "For each obligation the layer owns, state which of a–c applies"; §4.4 (L477-478) and T4 §0.1 row 13 (L102) require it per asset; T3 §2.7 `inherits` (L333) names T1 §11's L0 and L1 proof rows only; T4 adaptation, L1 row (L505) "`Carr` D3 dominates".
- **What the drafts needed:** Per asset, the Jyotish concept and the one carriage check (D1 source correspondence, D2 witness carriage, D3 independent re-derivation).
- **Evidence:**
  - `Carr.detector` NO_DETECTOR ("no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics") on 40 of 40 (L0), 19 of 19 (L1), 23 of 23 (L2), 21 of 21 (L3), 9 of 9 (L4), 15 of 15 (L5): 127 of 127 active assets. C-9 (the earlier campaign's finding) is confirmed on all six layers.
  - L1: the hint "D3 dominates" does not cover Ayurdāya (D2; T2 §5 L338) or specialised rule applications (D1; T2 §3.3 L176); existing D3-shaped code not in the census: `ga_writers/_vimshottari_independent_verifier.py` (1,483 lines). L0: five pilot briefs each had to choose (v3.0 C-9). L4: T3 §2.7 `inherits` links no carriage check to L4's rows (interpretive fidelity, distinctive understanding).
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 6 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R09*, R16, R92, R112, R144, R159, R174, R190, R204. Adjacent only: none. Remedy class: tier text (R09, R16, R92, R112, R144, R159, R174, R190, R204; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §2.7 gains a per-asset assignment table.
  - (b) T3 states the brief author chooses and records why (the two options R09 records for the T3 agenda).

#### TGH-T3-03 · No rule maps measured evidence to one of the eight dispositions

- **Rank / consequence:** rank 3 of 54; L0-L5 (6); 6 TG rows; 127 active assets in those layers.
- **Folded rows (6; L0 L1 L2 L3 L4 L5):** TG-L0-019, TG-L1-017, TG-L2-017, TG-L3-020, TG-L4-007, TG-L5-023
- **Also touches (not folded):** item TGH-T3-19; item TGH-T2-10.
- **Clause that failed to provide:** T3 §3.2 (L396-406): a disposition "with the evidence from Part 1 that justifies it"; §4.4 (L474-477) disposition and preserved kernel; T2 §10.1 (L531-544) the eight-letter hierarchy and "smallest sufficient change"; T4 §0.1 rows 8 and 12.
- **What the drafts needed:** Dispositions (and must-add lists) for every asset by rule rather than by author choice.
- **Evidence:**
  - L0: the census has no criterion that yields a disposition; registry `data_disposition` is set on 5 of 40 (RETAINED_AS_CAPITAL), `natural_key_partition` on 21 of 40. L1: 1 of 19 and 7 of 19. L2: §3.3 depends on §2.2-§2.4, which are themselves unfilled. L4: no ablation harness, so the instance carries T2c's provisional codes labelled as such. L5: T2c §7 provisional codes (P/E/I/Q/H) and kernels in prose, pre-FINAL and unevidenced.
  - L3: T2 §6.4 (L369-384) gives family-level preservation words (`ka_kshetra` "a mechanism-qualified candidate substrate, not … a universal authority", L373). The Track A brief §5 places dispositions in a separate `<Lx>_DISPOSITIONS_v1_0.md`, so the instances record evidence and leave the letter.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 6 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R93*, R115, R116, R147, R155, R170, R191, R207. Adjacent only: none. Remedy class: mixed (both: R116; tier text: R93, R115, R191, R207; no remedy stated: R147, R155, R170; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §3.2 gains an evidence-to-disposition decision rule (the direction R93 records for the T3 agenda).
  - (b) Until then T3 states a "provisional" convention for a disposition carried without a harness (L4's ask).

#### TGH-T3-04 · T3 §0.1 asks for the P-needs and V-journeys a layer is necessary for; no tier maps any P or V to a layer

- **Rank / consequence:** rank 4 of 54; L0-L5 (6); 6 TG rows; 127 active assets in those layers.
- **Folded rows (6; L0 L1 L2 L3 L4 L5):** TG-L0-003, TG-L1-001, TG-L2-001, TG-L3-001, TG-L4-001, TG-L5-001
- **Clause that failed to provide:** T3 §0.1 (L99-116): "List the P-needs and V-journeys for which this layer is necessary". T1 §2 (P01-P24, L154-179), T2 §2 (V01-V13, L115-129), T2 §3.1 (L135-144), T1 §11 (L496-505): none is keyed to layers.
- **What the drafts needed:** The P/V rows each layer is necessary for, one distinguishing line each.
- **Evidence:**
  - Tiers give role in prose but assert necessity of no row. L1: only T2 L327, L338, L500, L582 name L1. L2: T2 L141, L327, L338, L367, L582 and T1 L308. L3: P24/V13 only (T1 L178; T2 L129, L335, L427). L4: P24 (T2 L335), T2 L445, L582. L5: T1 §7.3, §9.7, §12.3 and T2 §6.6, §9.3, §12.1 in prose.
  - The only measured necessity signal is `blocking_radius`: L0 26 of 40 assets have a transitive active dependent (`bg_ontology` 4 direct / 69 transitive), 14 have none; L1 13 of 19 have downstream dependents, 6 have 0/0; L5 `mi_jivanaghatana` 9, `mi_kula` 9, `mi_bhavisya` 8 (L5 notes R85's closure figures are not in the census output). A build-graph reach is not a necessity statement.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 6 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R85 [CLOSED], R100, R130, R149, R164, R179, R197, R221*. Adjacent only: none. Remedy class: tier text (R100, R130, R149, R164, R179, R197, R221; see 1.7).
- **Tier:** T3. Drafts named: T2 x1 (L0) · T3 x5 (L1 L2 L3 L4 L5). Sources: L0 says T2 (following R197), L1-L5 say T3. Assigned T3: D5 (register v2.1) withdrew the P/V-by-layer matrix and moved the fix to T3 §0.1 (R221, on the T3 agenda). R130, R197, R100, R179 still carry T2-table remedies and are open in v2.8; E2 should record them as overtaken by R221.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §0.1 re-scoped to the catalog units a layer's assets produce and the layer's place in the necessity closure, as R221 records for the T3 agenda.
  - (b) Withdrawn by D5 and listed for the record only: keep the P/V wording and have T2 supply a P/V-to-layer table (R130, R197). The register's change log (v2.1) says D5 withdrew this direction for R85; R130, R197, R100 and R179 still carry it and are open in v2.8.

#### TGH-T3-05 · "Registry seed" and "migration-governed pin": named by T3, defined by no tier; three-way `depends_on` reconciliation cannot be done

- **Rank / consequence:** rank 6 of 54; L0-L5 (6); 6 TG rows; 127 active assets in those layers.
- **Folded rows (6; L0 L1 L2 L3 L4 L5):** TG-L0-014, TG-L1-003, TG-L2-002, TG-L3-004, TG-L4-004, TG-L5-002
- **Clause that failed to provide:** T3 §0.3 (L133-145) and §1.1 (L161-175): "registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement".
- **What the drafts needed:** The seed reading and the migration-pin reading of the dependency graph beside the live one, and a rule for which wins. No tier says where either lives or how it is read.
- **Evidence:**
  - L0: seed and live agree on `target_table` and `depends_on` for 40 of 40; differ on `target_floor` for 4 (`bg_gochara_arcs` 34,553/33,933 · `bg_muhurta_lattice` 91,477/164,575 · `bg_parihara_rules` 439/449 · `bg_transit_rules` 75/76) and `catalog_status` for 1 (`bg_vidhi_primitives` DRAFT/CURRENT). The seed's own upsert SQL declares `depends_on`, `count_sql`, `target_floor`, `catalog_status`, `has_writer` migration-governed once a row exists, so seed-versus-live is not like-for-like for those fields. 28 of 40 L0 ids are named by registry-modifying migrations. An L0 pin exists (`nirmana-analysis-layer-pins.json`, generation `l0:d2369b888e76:3dda261170ee`) but pins writers, not `depends_on`.
  - L1: 45 edges among the 19 assets; only 2 of 19 writer classes declare `depends_on`; migration 416 added and 419 removed `ga_structural -> ga_condition`; the other 18 assets not measured (would need replaying 176 registry-touching migrations). L3: SEED versus live for the 23 `ka_*` ids: 18 identical, 5 differ (`ka_gochara`, `ka_kshetra`, `ka_muhurta_seva`, `ka_sangam`, `ka_vighnakara`).
  - L4: pin file pins L4 membership (receipt_count 9, `l4:d2369b888e76:e73988c0dd03`), not `depends_on`. L5: seed `depends_on` agrees with live for 15 of 15; three other fields differ (`mi_jivanaghatana.scope`, `mi_adhilepa.target_table`, `mi_bhara.target_table`) and `lel_events.catalog_status` (seed DRAFT, live CURRENT); the frozen-manifest `depends_on` reading (migration 690 L9-13) was not located. L2: live registry only.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 6 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R86, R102, R132, R214. Adjacent only: none. Cited by the L4 row beside R86 (seed/pin reconciliation); R113 is the T3 §2.5 frozen-revision row, carried in TGH-T3-06. R214 (this clause; L5-facing) is deferred to D2 reopen round 2. R86, R102, R132 are open and not on the D2-ruled 31. Remedy class: mixed (instrument: R86, R102, R132; tier text: R214; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §0.3/§1.1 define seed and pin (where each lives, which is authoritative, and that migration-governed fields are exempt from seed-versus-live comparison).
  - (b) The instrument that emits all three readings (R86) is Track E; T3 states the honest-null an instance records until it exists.

#### TGH-T3-06 · "The CURRENT frozen definition revision" for cross-layer gates: undefined, and inherited from a superseded campaign

- **Rank / consequence:** rank 7 of 54; L0-L5 (6); 6 TG rows; 127 active assets in those layers.
- **Folded rows (6; L0 L1 L2 L3 L4 L5):** TG-L0-026, TG-L1-016, TG-L2-015, TG-L3-017, TG-L4-015, TG-L5-029
- **Also touches (not folded):** item TGH-T3-05.
- **Clause that failed to provide:** T3 §2.5 (L365-375): "cross-layer gates via egate.sql scoped to the CURRENT frozen definition revision"; "State the frozen definition revision the gate was evaluated against".
- **What the drafts needed:** What a frozen definition revision is, where recorded, and when one exists. No tier defines it.
- **Evidence:**
  - `egate.sql` (`platform/scripts/nirmana/egate.sql`) reads `nirmana_evidence.nirmana_elevation_campaign_definitions`, the Nirmāṇa campaign's manifest; plan v1.5 and architecture v1.5 do not carry the concept (L1 searched by phrase); plan v1.5 §1.1 says "Frozen by Nirmāṇa is not elevated" (L2 draft).
  - L2 (Q6): one frozen revision `t3-2026-09-11-8b884eac` (five superseded); its manifest holds 22 L2 assets (`bo_grounding` absent); `egate.sql -v layer=L2` returns 14 assets, all BLOCKED-ANCESTORS; 8 carry an `asset_frozen` event. L5: same revision; BLOCKED for 15 of 15 (13 BLOCKED-ANCESTORS, 2 BLOCKED-NO-ROUTE); circular for a layer with no accepted instance. L3: the instance is itself the artefact that would define it; egate not run.
  - L0: `nirmana-analysis-layer-pins.json` `definition_bindings.L0` carries `membership_sha256` e136c56d…139bbd and `snapshot_commit` 5142109f…, which no tier names as the frozen revision. L1 and L4: intra-layer order derived from the live registry (no cycle; six levels for L1, five for L4); the census reports only edge counts.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 6 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R86, R113, R145, R188. Adjacent only: none. Remedy class: instrument-class (R86, R113, R188; no remedy stated: R145; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §2.5 says what the clause means under Suvarṇa: the Nirmāṇa revision, the pin record, or a statement that it is not applicable until the layer is accepted (proposed wording; the sources only ask the question).
  - (b) The census emits the edge list and names the revision it evaluated against (R113; Track E).

#### TGH-T3-07 · Presentation parity: T2 marks it [TRANSFERS] ("a layer plan does not inherit it as its own work"), T3 makes it an acceptance test

- **Rank / consequence:** rank 11 of 54; L0 L1 L2 L3 L4 (5); 5 TG rows; 112 active assets in those layers.
- **Folded rows (5; L0 L1 L2 L3 L4):** TG-L0-022, TG-L1-011, TG-L2-011, TG-L3-010, TG-L4-010
- **Also touches (not folded):** item TGH-T3-26 (same defect class: a [TRANSFERS] obligation that also appears as a T3 gate).
- **Clause that failed to provide:** T2 §1 (L83-85) and §12.2 (L614): Presentation parity [TRANSFERS]. T3 §2.2 `measured_by` (L278) and §5.4 test 4 (L628): "Presentation parity holds for the layer's served surface".
- **What the drafts needed:** A single answer to whether presentation parity is a layer's own work.
- **Evidence:**
  - Both texts unchanged in the sealed files read by five of six layers. L0: no test file marking a two-rendering parity test of the L0 surface among the 37 files matching `parity|vocab` (absence by name is not proof); the draft marks it UNMET. L2: no parity test exists (none in the census). The D3 ruling of 2026-09-27 fixes the remedy but T3 is unchanged in the checkout.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 5 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R71*, R94*, R119*, R140*, R185*. Adjacent only: none. Fully on the D2-ruled agenda: R71, with R94, R140, R185 closing with it and R119 (T2 half). Remedy class: tier text (R71, R94, R119, R140, R185; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) Apply the D3 ruling recorded at R71 to T3 §5.4 test 4 (no new direction).

#### TGH-T3-08 · T3 §3.1 asks where a layer stands on each obligation it is scored on, measured; L0 has three unmapped instruments for one question, L2-L5 have no instrument (L1 has no row)

- **Rank / consequence:** rank 12 of 54; L0 L2 L3 L4 L5 (5); 5 TG rows; 108 active assets in those layers.
- **Folded rows (5; L0 L2 L3 L4 L5):** TG-L0-012, TG-L2-016, TG-L3-019, TG-L4-018, TG-L5-026
- **Clause that failed to provide:** T3 §3.1 (L387-394); T1 §11 (L498-505) and §14 (L585-596) assign the obligations per layer; T2 §12.2 (L601-629): "All tests listed here are planned" (L629).
- **What the drafts needed:** A measured standing per scored obligation (or an explicit convention for an obligation no instrument measures): L0 fidelity; L2 concept and relationship completeness and interpretive fidelity; L3 temporal integrity; L4 interpretive fidelity and distinctive understanding; L5 predictive performance and operational honesty.
- **Evidence:**
  - L0: three instruments for one question (T3 §1.2 L192-196 four fidelity dimensions; T2 §12.2 L601-607; T3 §2.7 L330-363 and the `Carr` gate L536) with no mapping and no scale for "authentic" or "method boundary stated"; `Ldgr.source_presence` reads 24 of 40, all PASS, and passes `bg_doshas` 79 of 79 although 53 cite the placeholder `classical_tradition` (Q-04), so a populated citation column is not "source present and qualified"; `Carr.detector` NO_DETECTOR 40 of 40.
  - L2, L4: none of the census's 20 criteria measures either obligation; no seeded case set, question set or scoring instrument. L3: the nine gates are per-asset engineering claims, none is temporal integrity; T2 L622 gives only a planned "Temporal boundary" test shape. L5: no criterion for either scored obligation; row data exists but no denominator rule (63 events, 13 `held_out` and 50 not; 62 with `outcome_observed`; `disclosure_timing = 'unknown'` on 63 of 63).
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 1 same-gap / 2 adjacent-only / 2 none. Same-gap rows cited: R210. Adjacent only: R117, R124, R142. R210 (L5) is deferred to D2 reopen round 2. R124 (asset-level, L2), R117 and R142 are neighbours only. Remedy class: tier text (R210; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §3.1 states the convention for an obligation with no instrument, so an instance records that the obligation is not measured because no instrument exists (T3 already prescribes the honest null for the value terms, L189-190 and L249-251).
  - (b) T2 §12.2 promotes planned tests to instruments: outside the harvest.
  - (c) L5 denominator definition for an incomplete history (T1 §8.2, T2 §9.1 L489).

#### TGH-T3-09 · "Whether current code on any live head differs from what is deployed": "live head" and the deployed reading are undefined

- **Rank / consequence:** rank 13 of 54; L0 L1 L2 L4 L5 (5); 5 TG rows; 106 active assets in those layers.
- **Folded rows (5; L0 L1 L2 L4 L5):** TG-L0-015, TG-L1-004, TG-L2-006, TG-L4-005, TG-L5-025
- **Clause that failed to provide:** T3 §1.1 (L170-175) and §4.1 (L431-435): the three-way baseline (deployed / current code newest on any live head incl. unmerged / target); risk = current code - deployed. Neither T3 nor T4 §1 defines "live head".
- **What the drafts needed:** Per asset: the deployed structure, the newest code on any live head, and their difference.
- **Evidence:**
  - L0: no per-asset deployed-versus-head field in the census; v3.0 asserted "risk = 0" from an unstated head check; the L0 pin was superseded once (seven assets changed).
  - L1: one head read (`origin/main` e2352f881); commit 8edba0533 (R34's fix) is in `origin/campaign/nirmana-engine` and not in `main`; migration 1094 is not in `main`. L2: L2 writer files byte-identical between the inspected checkout and `origin/main`; one unmerged live head exists (PR #2773, `bo_upaya`, head 5ca4af860, OPEN, BLOCKED); deployed image tag not measured.
  - L4: `git diff --stat` empty over the nine `ph_*` writer paths; other heads not enumerated; deployed version not observable from the reader login. L5: the inspector checkout is a single branch and cannot show other heads.
  - Dissent: the L3 draft classed the three-way baseline (R146/R87) as an instrument item, not a tier gap; five layers registered it as a gap and the register carries it as tier rows (R87, R104, R146, R154, R169, R182, R207).
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 5 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R87, R104, R146, R154, R169, R182, R207. Adjacent only: none. Remedy class: mixed (instrument: R87, R104, R146, R154, R169; both: R182; tier text: R207; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §1.1/§4.1 define "live head" (which refs count) and where the deployed version is read.
  - (b) The per-asset census field (R87) is Track E; T3 states what an instance records while it is absent.

#### TGH-T3-10 · "Verified at the consumer": no consumer-side probe or definition of a "live" field

- **Rank / consequence:** rank 14 of 54; L0 L1 L2 L4 L5 (5); 5 TG rows; 106 active assets in those layers.
- **Folded rows (5; L0 L1 L2 L4 L5):** TG-L0-016, TG-L1-009, TG-L2-009, TG-L4-022, TG-L5-022
- **Also touches (not folded):** item TGH-T2-08 (L1 and L2 rows carry the declared-use facet).
- **Clause that failed to provide:** T3 §1.4 (L215-226): each produced contract's position on the six evidence states, "verified at the consumer, not asserted by the producer"; §1.1 (L170) "contract fields live"; T2 §11 (L572).
- **What the drafts needed:** The evidence-state position of each produced contract at its consumer; a definition of a live field.
- **Evidence:**
  - L0: 34 declared cross-layer edges (kala 21, mimamsa 7, ganita 5, bodha 1) onto 18 of 40 L0 assets; the nine L0 tables counted are read in 27-71 files each (a reader count); `reach` mean width 0.509 over 37 assets, 11 at zero, 252 dark columns. L1: `Reach.fields` NOT_GENERIC x19. L2: registry dependents outside L2 for 9 of 23 assets, none for 14; `Dens.served` and `Reach.fields` disagree on `bo_cdlm_summary` and `bo_samskara` (measurement finding).
  - L4: census `Dens.served` modules disagree with the catalog snapshot `producer_semantic_bindings` (`ph_nimitta`: `query_phala_calibration.ts`, `query_predictive_anchors.ts` versus `scu.catalog.query_prashna_special_techniques`; `ph_sankrama` -> `scu.catalog.query_planet_transit`; snapshot 2026-09-20). L5: `reach.modules` counts modules and does not verify reads; zero modules for `mi_jivanaghatana`, `mi_sankalpa`, `mi_seva`, `mi_vistara`.
  - Dissent: the L3 draft classed the consumer probe (R157/R106) as an instrument item, not a tier gap.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 4 same-gap / 1 adjacent-only / 0 none. Same-gap rows cited: R106, R109, R157, R172. Adjacent only: R51 [CLOSED]. Remedy class: instrument-class (R106, R109, R157, R172; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §1.4 names the consumer-side probe or states that an instance records the honest null (not verified at the consumer) until one exists.
  - (b) The probe itself (R106) is Track E.

#### TGH-T3-11 · The manifestation / temporal / neither role of each asset is assigned by no tier (and T3 has 12 bullets where T4 counts 13 rows)

- **Rank / consequence:** rank 15 of 54; L0 L1 L2 L4 L5 (5); 5 TG rows; 106 active assets in those layers.
- **Folded rows (5; L0 L1 L2 L4 L5):** TG-L0-020, TG-L1-018, TG-L2-019, TG-L4-024, TG-L5-024
- **Clause that failed to provide:** T3 §4.4 (L476): "its manifestation or temporal role"; T4 §0 (L76) `role: manifestation | temporal | neither`, "from layer §4.4"; T4 §0.1 (L86, rows L90-102) has thirteen rows and omits role while T3 §4.4 lists twelve bullets.
- **What the drafts needed:** A role value for each asset, and one agreed count.
- **Evidence:**
  - L0: v3.0 said "L0 has no manifestation or temporal role" for all 40 (text only). L1: T2 §6.2 (L355) supplies it for four names ("Daśā, transit-anchor, pañcāṅga, Tājaka and specialized services") and DP07 for clocks; nothing assigns the others. L2: layer default derivable ("neither": T2 §3.1 puts activation in L3, manifestation in L4) but per-asset exceptions (`bo_pratijna`, `bo_upaya`) cannot be judged and no tier gives a method.
  - L4: T2 §6.5 (L388) calls all nine "the Phala asset family", L390 names six only as an overlap list and L392 separates electional/remedial/rectification; none is a role assignment in T4's vocabulary. R192's premise ("§4.4 has no role row") is inexact (the role bullet exists; the mismatch is 12 versus 13). L5: none assigned; same 12-versus-13 mismatch.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 5 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R120*, R192*, R208*. Adjacent only: none. Remedy class: tier text (R120, R192, R208; see 1.7).
- **Tier:** T3. Drafts named: T3 x3 (L0 L2 L4) · T4 x2 (L1 L5). Sources: L0, L2, L4 say T3, L1 and L5 say T4. Assigned T3: the role is "from layer §4.4" and R120 (T3 agenda) leads, with R192 and R208 closing with it; T4 inherits.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §4.4 gains a role row or a per-asset role assignment (R120).
  - (b) T4 §0 states the author assigns the role and records why (R208's alternative).
  - (c) Align T3 §4.4 and T4 §0.1 on the row count (R192).

#### TGH-T3-12 · Edge type per edge: T2 §3.2 defines five types; no source records or assigns them

- **Rank / consequence:** rank 17 of 54; L0 L2 L3 L5 (4); 4 TG rows; 99 active assets in those layers.
- **Folded rows (4; L0 L2 L3 L5):** TG-L0-030, TG-L2-003, TG-L3-005, TG-L5-005
- **Also touches (not folded):** item TGH-T2-04 (its L4 row also asks for the edge type per L4 edge).
- **Clause that failed to provide:** T3 §0.3 (L139-140) "Receives from … by edge type" and §2.5 (L373-374) "the edge type of every edge"; T2 §3.2 (L146-166) five edge types.
- **What the drafts needed:** The edge-type column of each layer's dependency table, and a rule for reads that have no registry edge.
- **Evidence:**
  - `asset_registry` has no edge-type column (42 columns read); `depends_on` is a bare `text[]`. L0: 25 intra-L0 edges and 34 cross-layer edges onto L0 are unclassified in every source. L3: every registry edge reads as computational (T2 §3.2 item 2, L161); nothing types the definition, serving-context, evaluation or next-generation edges. L2: the only L0 upstream of the layer is `bg_rules`, so definition edges (DP01) are recorded nowhere.
  - L5: 39 registered edges (21 intra-layer, 18 cross-layer); reads with no edge: `life_events` is read by `mi_jivanaghatana.py:215`, `services/mi_bhara/db.py:143`, `services/mi_sankalpa/db.py:64` and L4 `ph_rectification` while `lel_events.blocking_radius` is 0/0; `brahma_prospective_ledger` is read by `services/mi_bhara/db.py:177`; migration 691 (L1447-1451) records "32 DAG corrections — 19 undeclared-but-read, 13 declared-but-unread — NONE is applied".
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 4 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R122, R133, R181*. Adjacent only: none. Cited by the L5 row for the edge list, carried in TGH-T3-06: R113. R133 is open and not on the D2-ruled 31; R181 (T2 §7.1 half) is. Remedy class: mixed (instrument: R122, R133; tier text: R181; see 1.7).
- **Tier:** T3. Drafts named: T2 x1 (L5) · T3 x3 (L0 L2 L3). Sources: L0, L2, L3 say T3, L5 says T2 (L4's row, folded elsewhere, asks both). Assigned T3: the T3 clauses are the ones that request the type; T2 §3.2 supplies an adequate vocabulary. The T2 §7.1 roll-up half is R181 in the item TGH-T2-04.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 states that an instance types an edge only where a source records the type and otherwise reports it as a depends_on edge with no recorded type.
  - (b) A registry edge-type column (R133) is a registry/instrument change (Track E).
  - (c) T2 §3.2 states how a read with no registry edge (evaluation edge, serving-context read) is assigned a type (the L5 facet).

#### TGH-T3-13 · No layer-level synergy seams and no ablation harness (the synergistic term cannot be computed)

- **Rank / consequence:** rank 18 of 54; L0 L2 L3 L5 (4); 4 TG rows; 99 active assets in those layers.
- **Folded rows (4; L0 L2 L3 L5):** TG-L0-013, TG-L2-008, TG-L3-006, TG-L5-021
- **Clause that failed to provide:** T3 §1.2 (L177-196), §1.3 (L198-213; "the layer's synergy binding if one exists", L201), §1.5 (L228-251; L249-251 "only where an ablation harness exists"); T2 §3.5 (L207-241) defines four plane-level seams and names cross-layer ablation.
- **What the drafts needed:** A layer seam list and a harness, or the honest absent-instrument recording.
- **Evidence:**
  - L2, L5: the census has no ablation or synergy criterion (20 criteria read; L5 `scoring = contribution`). L3: no synergy field. L0: the draft chose three L0-internal joins (catalogue-to-identity, rules-to-concepts, remedies-to-source-identity): 741 ontology rows / 741 distinct `(entity_class, canonical_id)` / 730 distinct `canonical_id`; 17 of 3,002 rules carry `yoga_canonical_id`; 52 of 341 remedies resolve exactly.
  - T2 §13.3 item 1b (L675-676) already requires "each with the instrument that measured it, or an explicit absent instrument. A synergy figure without a harness is an invented computation."
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 4 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R105, R156, R171, R206. Adjacent only: none. Remedy class: mixed (instrument: R206; tier text: R105, R171; no remedy stated: R156; see 1.7).
- **Tier:** T3. Drafts named: T2 x1 (L3) · T3 x3 (L0 L2 L5). Sources: L0, L2, L5 say T3, L3 says T2 (plane seams live at T2 §3.5). Assigned T3: T2 already defines the seams and the absent-instrument rule; what fails is T3's per-layer binding and harness.
- **Proposed remedy (direction or options; not text):**
  - (a) No clause change: the honest null the tiers already prescribe (T3 L189-190, L249-251; T2 §13.3 1b) is the answer until a harness exists.
  - (b) T3 §1.3 states where a layer's seam binding is written.
  - (c) The harness is an instrument packet (R105 asks T3 to prescribe a minimum one).

#### TGH-T3-14 · T3 §5.2 tells the instance to report unfillable rows in §7, which T3 does not have; §2.5 is ordered after §2.7

- **Rank / consequence:** rank 20 of 54; L0 L2 L5 (3); 3 TG rows; 78 active assets in those layers.
- **Folded rows (3; L0 L2 L5):** TG-L0-021, TG-L2-023, TG-L5-028
- **Also touches (not folded):** item TGH-T3-27 (the same-file count mismatches, folded from the L1 row, which also carries this facet); item TGH-T3-01 (the L3 row folded there cites the same missing §7).
- **Clause that failed to provide:** T3 §5.2 (L584-586) "Report unfillable rows in §7", but T3's headings run §0-§5 plus "Adapting the template per layer" (L672); §2.5 is ordered after §2.7 (L313-377).
- **What the drafts needed:** A section in which to record document-level corrections and gated packets, and a stable section order.
- **Evidence:**
  - L0 put corrections in its own Part 6 and logged the order; L2 reports the unfillable rows in its own gate-map table; L5 read the template headings 2.1, 2.2, 2.3, 2.4, 2.6, 2.7, 2.5.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 3 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R08*. Adjacent only: none. R08 is on the D2-ruled agenda; R65, R67 and R220 (the counts) are carried in TGH-T3-27. Remedy class: tier text (R08; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) Apply R08 as recorded on the T3 agenda.

#### TGH-T3-15 · "For each rule, the detector": no tier names a detector, or a class of detector, for any T1 §8.1 correctness rule

- **Rank / consequence:** rank 9 of 54; L0 L1 L3 L4 L5 (5); 6 TG rows; 104 active assets in those layers.
- **Folded rows (6; L0 L1 L3 L4 L5):** TG-L0-006, TG-L0-017, TG-L1-010, TG-L3-008, TG-L4-008, TG-L5-008
- **Also touches (not folded):** item TGH-T2-06 (the switch statement itself: the L0 and L1 rows here were narrowed to the detector only, and the event-time context's identity travels there as a rider); item TGH-T2-19.
- **Clause that failed to provide:** T3 §2.1 (L261-272): "For each rule, the detector. A rule with no detector is a wish." T1 §8.1 (L422-427) states the rule per layer. T2 §9.2 (L493-517; ON row L500, OFF row L501, storage separation L510-512) supplies the switch statement for L0 and L1; no tier supplies a test that could read either statement false.
- **What the drafts needed:** A named detector per layer correctness rule. For L0, also a detector for its ON/OFF statement; for L1, a detector for T1 §8.1's L1 row and for the T1 §13 / T2 §6.2 rules.
- **Evidence:**
  - L0: rule "private observations becoming global doctrine" (T1 L422); 0 of 66 tables carry a chart/subject column (Q-09; a measured fact, not a verdict, which the L0 draft also reports for its ON/OFF statement); no detector for "no invented computation, source, detector, confidence or score" (T1 L566) beyond `assert_legal()`.
  - L1: T1 §8.1's L1 row "Altering birth facts or chart calculations to fit biography" has no census criterion; FORENSIC anchor gates exist in five writers plus `panchanga_forensic_gate` and `forensic_gate_vargas` but test that birth anchors reproduce, not that no biography touched a fact; whether any registered L1 asset writes an event-time context is not measured (none of the 19 is named event-time).
  - L3: "Using the observed event to choose the supposedly prior trigger" (T1 L425); three `*circularity*` test files by name. L5: no census criterion for outcome leakage, chronology reset or firewall; code-side checks exist by filename (`test_mi_adhilepa_leakage.py`, `calibration_leak_guard.ts`, `no_leakage_filter.ts`) and are not registered as detectors.
  - L4 (a facet on the referent): the rule is "Rewriting the original forecast to fit the eventual story" (T1 L426); all nine L4 writers rebuild by per-chart delete-then-insert (`Idem.pattern` PASS x9; `computed_at` DEFAULT now()), so no L4 row can be "the original forecast"; T2 §9.1 (L491) calls `ph_nimitta` output "rebuildable candidates, not protected issuance history" and DP15a (L434) places the freeze at issuance. Which object the rule binds to is unsupplied.
  - Dissent: the L2 draft recorded absent detectors as NO_DETECTOR layer packets because T3 prescribes the honest null (§2.1 "a wish"; §2.7 "an honest null, never a pass") and did not register a row.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 6 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R117, R137, R183. Adjacent only: none. Cited by the L0 and L1 rows for the switch statement, carried in TGH-T2-06: R88*, R107, R199. R117, R137 and R183 are open and not on the D2-ruled 31. Remedy class: tier text (R117, R137, R183; see 1.7).
- **Tier:** T3. Drafts named: T2 x3 (L0 L1 L4) · T3 x3 (L0 L3 L5). Sources: L0 (its detector-only row), L1 and L4 say T2; L0 (its other row), L3 and L5 say T3. Assigned T3: the detector clause is T3 §2.1; the L0 and L1 rows were narrowed to the detector only (T2 §9.2 supplies the switch); the L4 referent is recorded as a T2 rider inside this item, not a separate item.
- **Proposed remedy (direction or options; not text):**
  - (a) Accept the honest null the template prescribes (L2's reading): no clause change, detectors become Track E packets.
  - (b) T3 §2.1 asks for a named detector registry per rule (R117's direction), each entry allowed to open as NO_DETECTOR.
  - (c) L4 referent: T2 §9.1/DP15a states which L4 object the rule protects (a rider on the T2 agenda).

#### TGH-T3-16 · Where an asset's natural key is declared (the Idem gate cannot decide "replaces its own rows" without it)

- **Rank / consequence:** rank 22 of 54; L0 L1 L4 (3); 3 TG rows; 68 active assets in those layers.
- **Folded rows (3; L0 L1 L4):** TG-L0-027, TG-L1-006, TG-L4-025
- **Also touches (not folded):** item TGH-T2-05; item TGH-T3-19; item TGH-T4-05 (global-scope keys).
- **Clause that failed to provide:** T3 §5.2 gate-map Idem row (L574-575): "the asset's natural key, so 'replaces its own rows' is decidable"; T4 §6 (L396-397) "chart x natural key"; T4 adaptation, L1 row (L505). No tier says where the key is declared.
- **What the drafts needed:** The natural key per asset and, for a shared table, each writer's delete scope.
- **Evidence:**
  - L0: `natural_key_partition` is set on 21 of 40 L0 registry rows and NULL on 19 (including `bg_ontology`, `bg_reference`, `bg_remedies`, `bg_nakshatra_medical`, `bg_medical_mappings`).
  - L1: unique keys include `build_id` (`_idempotency.py` L3-6); replacement is the writer's delete scoped to the categories present in the rows about to be written (L44-105), so a rebuild that stops emitting a category leaves the old rows (a layer finding, not a clause). L4: the registry declares a natural key for 9 of 9; the census "declared key" is the surrogate PK for 6 of 9; 0 duplicate groups on the registry key at the canonical chart.
  - A candidate authority exists and no tier names it: the registry free-text field `natural_key_partition` (populated on 67 of 129 rows; L3 read it; 0 hits for the field name in T1-T4 and the register).
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 2 same-gap / 1 adjacent-only / 0 none. Same-gap rows cited: R96, R116. Adjacent only: R213. Remedy class: mixed (both: R116; tier text: R96; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §5.2/T4 §6 name the declaring artifact (registry `natural_key_partition`, or the layer instance) and state what the census reads.
  - (b) The registry declares it per asset, including immutable columns (R116's direction).

#### TGH-T3-17 · T3 §0.2 demands "what it computes that existing software does not"; no tier supplies a baseline to establish it

- **Rank / consequence:** rank 25 of 54; L1 L3 L4 (3); 3 TG rows; 49 active assets in those layers.
- **Folded rows (3; L1 L3 L4):** TG-L1-002, TG-L3-002, TG-L4-002
- **Clause that failed to provide:** T3 §0.2 (L126-127): "Name what it computes that existing software does not". Plane-level contrast exists at T1 §1 (L51-59) and T2 §1 (L60-67); T2 §3.1 (L140-143) gives each layer's owned question, hand-onward and must-not-claim; T2 §6.5 (L386-392) describes what L4 preserves, not its differentiator.
- **What the drafts needed:** A layer-specific statement. What no tier supplies is any way to establish that a given computation is one "existing software does not" produce: no baseline, no software named; T1 §13 forbids an invented claim.
- **Evidence:**
  - Searches for "existing software" / "conventional" in T1-T4 hit only T1 L51-59 and T2 L60-67.
  - L2 is the counter-example (not a row): its draft found T2 §6.3 supplies the L2 paragraph, so per-layer text at T2 is achievable. The gap is live for L1, L3 and L4.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 3 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R101, R131, R180. Adjacent only: none. R131 is explicitly deferred to D2 reopen round 2 (register); this item is evidence for that round. R101 and R180 are open and not on the D2-ruled 31. Remedy class: tier text (R101, R131, R180; see 1.7).
- **Tier:** T3. Drafts named: T2 x1 (L4) · T3 x2 (L1 L3). Sources: L1 and L3 say T3, L4 says T2 (following R180). Assigned T3: the failing clause is T3's demand; whether the answer is per-layer T2 text is one of the options.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §0.2 drops or reframes the external-comparison demand (R131's first option).
  - (b) T2 carries a per-layer differentiator sentence as §6.3 does for Bodha (R101 and R180 point to T2 narratives).
  - (c) T3 names a comparison baseline per layer (R131's second option); no such baseline exists today.

#### TGH-T3-18 · What the Idem claim ("a rebuild replaces its own rows; it never accretes") means for upsert writers and preserved records

- **Rank / consequence:** rank 29 of 54; L0 L5 (2); 2 TG rows; 55 active assets in those layers.
- **Folded rows (2; L0 L5):** TG-L0-023, TG-L5-017
- **Also touches (not folded):** item TGH-T3-16; item TGH-T2-05; item TGH-T4-05 (the global-scope facet, folded from the other L5 Idem row).
- **Clause that failed to provide:** T3 §5.2 Idem row (L532) and T4 §4 (L225): "a rebuild replaces its own rows; it never accretes"; T4 §6 (L396) "L0 upsert; L1+ delete-then-insert scoped to (chart_id x natural key)"; T3 cites §N.3, which is `CLAUDE.md`, not a tier. Clauses that recognise records a rebuild must not replace: T2 §6.6 (L402), DP15a (L434), T1 §7.3 (L390-391).
- **What the drafts needed:** An L0 idempotency detector for the upsert convention (which cannot remove a row) and the behaviour when a source shrinks; a reconciliation of the preservation clauses with "never accretes" per L5 asset.
- **Evidence:**
  - L0: `Idem.pattern` 28 upsert, 7 delete-then-insert (`bg_compendium_index`, `bg_concordance`, `bg_dasha_systems`, `bg_doshas`, `bg_gochara_arcs`, `bg_nakshatra`, `bg_yogas`), 1 update-in-place (`bg_text_index`, PARTIAL), 4 no writer. Migration 703 (applied 2026-09-06) records that `bg_parihara_rules`' upsert-only writer "accrete[s] forever" when a source shrinks and deletes 9 orphaned rows by hand; the registry floor stayed 449 against 440 live (`Count.floor` FAIL, -9).
  - L5: `mi_gunanaka.py:340-365` inserts `mimamsa_calibration_snapshot` with a time-based id (ratified exception, `briefs/parisesa/F188_ACCRETION_EXCEPTION_v1_0.md`); `services/mi_bhara/db.py:36,234,281` append-only weight versions; `mi_sankalpa` deletes only `study_arm='elected_pending' AND performed IS NULL AND outcome_event_id IS NULL`; `mi_bhavisya.py:230` deletes only `lifecycle_status IN ('pending','due')`; `mi_abhilekha.py:70` UPDATEs `lifecycle_status`. Campaign rule N-46 exists outside the tiers.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 2 none. Same-gap rows cited: none. Adjacent only: R20 [CLOSED]. R213 and R96 (the global-scope keying case only) are carried in TGH-T4-05; R20 concerns delegation. Remedy class: none (no same-gap register row).
- **Tier:** T3. Every draft named T3 (the L5 global-scope row, which named T4, is folded in TGH-T4-05). Assigned T3: the semantics of the claim are the T3 gate's (T3 §5.2 Idem row); T4 §4's Idem row restates the same sentence.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §5.2 Idem defines an accretion test for upsert writers and the behaviour on shrink.
  - (b) T3 lists the classes of legitimate non-replacing write (append-only history, status-preserving update, ratified exception) and the evidence each carries.
  - (c) The global-scope form of the convention is the item TGH-T4-05's.

#### TGH-T3-19 · What defines an asset's "preserved kernel" (sourced "from 3.2", which lists dispositions only)

- **Rank / consequence:** rank 30 of 54; L2 L3 (2); 2 TG rows; 44 active assets in those layers.
- **Folded rows (2; L2 L3):** TG-L2-018, TG-L3-021
- **Also touches (not folded):** item TGH-T3-03; item TGH-T3-16.
- **Clause that failed to provide:** T3 §4.4 (L477): "the preserved kernel — what of the asset must survive any rebuild unchanged (from 3.2)"; T3 §3.2 (L396-406); T4 §0.1 row 12.
- **What the drafts needed:** How a kernel is identified and where it is declared.
- **Evidence:**
  - L2: the registry's `natural_key_partition` gives a natural key for 20 of 23 assets and is blank for `bo_anveshana`, `bo_karanajala`, `bo_samvada`; immutable columns are declared nowhere. L3: the word "kernel" occurs in T2 at L170, L355, L390, L402, L535, L539, L544, L550, L639, L686, L692, L703 (general preservation wording; L686 tells the asset brief to state "preserved kernels/tests", which says where, not how); the census carries no kernel field; the declared key (`Vocab.identity`, 17 assets) is identity, not kernel.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 2 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R116, R148, R158, R173. Adjacent only: none. R116 is open and not on the D2-ruled 31. R93 (on the list) also names the kernel in its remedy and R116 lists it as its dependency, but no folded row cites R93, so it is not counted here; TGH-T3-03 carries it. Remedy class: mixed (instrument: R148, R158; both: R116, R173; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §3.2 names each preserved kernel explicitly (R93's wording covers it).
  - (b) The kernel is declared per asset in the registry (grain, key, immutable columns) and the instance reads it (R116).

#### TGH-T3-20 · Three coverage-state vocabularies: five in T3, six in T1, three-plus in T2

- **Rank / consequence:** rank 31 of 54; L2 L3 (2); 2 TG rows; 44 active assets in those layers.
- **Folded rows (2; L2 L3):** TG-L2-024, TG-L3-014
- **Also touches (not folded):** item TGH-T2-01.
- **Clause that failed to provide:** T3 §2.4 (L303-311): applied / inapplicable-with-reason / unavailable / unqualified / unresolved. T1 §5.1 (L317-319): applied, inapplicable with reason, unavailable, unqualified, **contradictory**, **still unexplored**. T2 §5 (L341): applied, inapplicable, or "unavailable/unqualified/unresolved".
- **What the drafts needed:** One coverage-state vocabulary for the layer's obligations.
- **Evidence:**
  - Read at the lines cited: "contradictory" and "still unexplored" (T1) have no counterpart in T3, and "unresolved" (T3) has no exact counterpart in T1. The L2 and L3 instances use T3's five because the `measured_by` line is the template's own; no result is written under any vocabulary (all "not measured"). Register search finds only instrument rows (R90, R142, R153, R168, R187, R202) that use T3's five and none records the mismatch.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 2 none. Same-gap rows cited: none. Adjacent only: R90*, R142, R153, R168, R187, R202. No row records the mismatch; R142 and the per-layer copies are adjacent. Remedy class: none (no same-gap register row).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §2.4 aligns to T1 §5.1's six (T1 is the parent).
  - (b) T3 states a mapping from T1's six to its five.

#### TGH-T3-21 · Meaning of `catalog_status = DRAFT` for certification

- **Rank / consequence:** rank 38 of 54; L0 (1); 1 TG row; 40 active assets in those layers.
- **Folded rows (1; L0):** TG-L0-024
- **Clause that failed to provide:** T3 §1.1 (L161-175) lists statuses "registered, writer-backed, service, residual, shared, historical"; DRAFT is not among them. Terms searched: "catalog_status", "DRAFT" in T1-T4.
- **What the drafts needed:** A rule for `bg_vidhi_floors`, the only DRAFT L0 asset: can a DRAFT asset be ELEVATED, and what does its certification read.
- **Evidence:**
  - L0: 39 CURRENT, 1 DRAFT (`bg_vidhi_floors`, 423 rows = 14 intent floors + 409 items); migration 642 records 12 of 14 floors MANDATORY, 2 CANDIDATE; the census shows the asset with the same gate readings as its CURRENT siblings.
  - Also seen, not folded: L4 records `ph_pratikara` DRAFT ("no tier defines DRAFT or requires that it be resolved"); L5 records `mi_seva` and `mi_abhilekha` DRAFT and `lel_events` DRAFT in the seed versus CURRENT live.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: R84 [MEASURED]. R84 only measured the split. Remedy class: none (no same-gap register row).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §1.1 states what DRAFT means for certification and whether a DRAFT asset can be elevated.
  - (b) T3 forbids DRAFT in an accepted instance, forcing the owner to resolve each DRAFT asset.

#### TGH-T3-22 · The Ldgr claim for a computed root whose inputs are birth parameters and L0, not upstream `fact_id`s

- **Rank / consequence:** rank 45 of 54; L1 (1); 1 TG row; 19 active assets in those layers.
- **Folded rows (1; L1):** TG-L1-021
- **Clause that failed to provide:** T3 §5.2 Ldgr row (L531): "every derived value names the upstream `fact_id` it reads, and those ids resolve"; T4 §4 Ldgr row (L224) "for a reference layer, every row names its source".
- **What the drafts needed:** What an L1 root asset names. Neither T3 nor T4 gives a third form of the claim.
- **Evidence:**
  - `ga_positions` has `depends_on = {}`; its inputs are birth parameters and L0 constants. `chart_facts` has no column that holds upstream fact identifiers (25 columns; provenance columns `citation_ref`, `citation_human`, `source_calculation`, `formula_id`, `formula_provenance_text`). The only Ldgr cell, `Ldgr.source_presence`, is the reference-layer form: PASS for 13 of 19 and absent (no cell) for `ga_condition`, `ga_prashna`, `ga_strength`, `ga_structural`, `ga_transit_anchors`, `ga_vargas`.
  - A generation-and-partition ledger exists in code (`ga_writers/data_plane_runtime.py`, migration 1035, `l1_data_plane_*` tables) but the reader login cannot read it.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: R128. No row for the claim; R128 records only that L2 verdict cells are silently missing. Remedy class: none (no same-gap register row).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §5.2/T4 §4 state the claim for a computed root (inputs named as birth parameters and L0 ids) or state it N/A with reason.
  - (b) Census emits a verdict cell for every gate row, N/A-with-reason included (R128; Track E).

#### TGH-T3-23 · No tier enumerates tables in a layer's namespace that no asset owns (inventory is per asset)

- **Rank / consequence:** rank 48 of 54; L5 (1); 1 TG row; 15 active assets in those layers.
- **Folded rows (1; L5):** TG-L5-020
- **Clause that failed to provide:** T3 §1.1 (L169) "every asset and service the layer owns"; T2 §13.3 item 2 (L678) "Complete owned inventory including accepted, residual, service, shared and historical capital".
- **What the drafts needed:** A complete table-level inventory of L5, including tables with no asset.
- **Evidence:**
  - L5: `mimamsa_adjudication_log`, `mimamsa_pool_contributions`, `mimamsa_resonance_feedback`, `mimamsa_snapshot_cosign` have no owning asset (0 rows for chart 482012f1); nine `*__ssv_20260728a/b` shadow copies likewise (`mimamsa_calibration__ssv_20260728b`, `mimamsa_insight_units__ssv_20260728a`, `mimamsa_insight_units__ssv_20260728b`, `mimamsa_journal__ssv_20260728b`, `mimamsa_load_bearing__ssv_20260728b`, `mimamsa_manifestation_grammar__ssv_20260728b`, `mimamsa_multipliers__ssv_20260728b`, `mimamsa_predictions__ssv_20260728b`, `mimamsa_qa_eval__ssv_20260728b`); shadow-copy row counts were not measured.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. Remedy class: none (no same-gap register row).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §1.1 / T2 §13.3 item 2 state whether the inventory is table-level.
  - (b) Unowned tables are classed "residual" or "historical" (statuses T3 §1.1 already lists).

#### TGH-T3-24 · Which record carries L5's "learning output" (a visible change to scope, confidence or availability, with the reason)

- **Rank / consequence:** rank 50 of 54; L5 (1); 1 TG row; 15 active assets in those layers.
- **Folded rows (1; L5):** TG-L5-027
- **Also touches (not folded):** item TGH-T3-15.
- **Clause that failed to provide:** T1 §7.3 (L395-399), T2 §6.6 (L396-402), T3 adaptation L5 row (L684): "learning's defined output — a visible change to a claim family's scope, confidence or availability, with the reason stated".
- **What the drafts needed:** Where the learning output is recorded and how a reviewer would see it.
- **Evidence:**
  - `mimamsa_calibration_snapshot.delta_from_prior_jsonb` is NULL on 4 of 4 rows; `mimamsa_multipliers.audit_trail` is non-empty on 9 of 9; `promotion_status` {promoted 2, prior_only 7}. Which, if any, constitutes the "visible change" is not stated.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 1 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R117. Adjacent only: none. Only R117 (generic detector row) is cited. Remedy class: tier text (R117; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T2 §6.6 / T3 adaptation name the carrying record or field.
  - (b) Leave to the L5 asset briefs and add the detector under the item TGH-T3-15.

#### TGH-T3-25 · Which layer carries the "bridge or falsifier" row: T3 says "temporal layers", T2 and T4 say L4

- **Rank / consequence:** rank 53 of 54; L4 (1); 1 TG row; 9 active assets in those layers.
- **Folded rows (1; L4):** TG-L4-011
- **Also touches (not folded):** item TGH-T2-02.
- **Clause that failed to provide:** T3 §2.2 (L283-286) lists "the bridge or falsifier" under "for temporal layers"; T3 adaptation table (L683), T4 (L508), T2 §3.4 (L197, DP09) and T2 §6.5 (L388) assign the manifestation bridge and its falsifier to L4.
- **What the drafts needed:** One statement of which layer carries the row.
- **Evidence:**
  - Both readings cannot hold. L4 holds the fields: `phala_anchors.falsifier`, `structured_falsifier_jsonb`, `causal_chain_jsonb`; `phala_sankrama.falsifier`, `bridge_path_jsonb`; `phala_pramana.falsifier_text`. The L3 draft finds the temporal row supplied to L3 by the same lines (T2 L197; T3 L284-286): both layers claim the row.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: none. No row found (register searched for "bridge or falsifier"). Remedy class: none (no same-gap register row).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §2.2 states the row by role (manifestation versus temporal) and names both layers' shares.
  - (b) Settle it through the presentation-row assignment (item TGH-T2-02) and have T3 inherit.

#### TGH-T3-26 · Who owns a `Dens` FAIL: the gate is T3's, but serving and delivery are [TRANSFERS] in T2

- **Rank / consequence:** rank 54 of 54; L4 (1); 1 TG row; 9 active assets in those layers.
- **Folded rows (1; L4):** TG-L4-021
- **Also touches (not folded):** item TGH-T3-07; item TGH-T2-04.
- **Clause that failed to provide:** T3 §5.2 (L538, L581): Dens conditional on "reaches a served surface"; T2 §1 (L83-85) and §8 (L451-457): serving and delivery obligations are [TRANSFERS], except a producer's DP10 metadata about itself.
- **What the drafts needed:** Whether closing a Dens FAIL is the layer's work.
- **Evidence:**
  - L4: `Dens.served` FAIL on 9 of 9, "declaring density_contract: 0", over three retrieval-plane capability modules (`query_phala_calibration.ts`, `query_predictive_anchors.ts`, `query_domain_result.ts`). The L0 draft made the same observation (0 of 46 L0 capability modules declare a `density_contract`, F-05) but filed it under the item TGH-T2-04.
- **Register:** new: no open same-gap register row. Rows: 0 same-gap / 0 adjacent-only / 1 none. Same-gap rows cited: none. Adjacent only: R71*, R232 [CLOSED], R234. R71 covers parity only; R232 and R234 are detector rows. Remedy class: none (no same-gap register row).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) T3 §5.2/T2 §8 state which part of Dens is the producer's DP10 metadata (layer-owned) and which is serving (transferred), and split the gate accordingly.
  - (b) Handle together with the parity contradiction in one [TRANSFERS] sweep of the T3 gates.

#### TGH-T3-27 · T3's own counts disagree with its neighbours: "six static checks", an "eight-row map", "9 × 129 assets"

- **Rank / consequence:** rank 42 of 54; L1 (1); 1 TG row; 19 active assets in those layers.
- **Folded rows (1; L1):** TG-L1-023
- **Also touches (not folded):** item TGH-T3-14 (the same row also carries the undefined §7 and the section order).
- **Clause that failed to provide:** T3 L539 "six static checks" versus T4 §4.2 (nine); T3 L629 "eight-row map" versus the nine-row table (L572-582); T3 L521 "9 × 129 assets" versus 127 active assets measured (SUMMARY.md: L0 40 · L1 19 · L2 23 · L3 21 · L4 9 · L5 15).
- **What the drafts needed:** Consistent counts. For L1 the asset count (19) agrees with the registry; only the cross-layer figure differs.
- **Evidence:**
  - The L1 instance writes a nine-row gate map and carries its unfillable rows in a closing "Corrections with gates" section.
- **Register:** covered by an open register row that is on the D2-ruled E2.1 list. Rows: 1 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R65*, R67*, R220 [CLOSED]. Adjacent only: none. R65 and R67 are on the D2-ruled agenda (T3 halves); R220 (the 129-versus-127 figure) is closed. The L1 row also cites R08 for §7 and the section order (carried in TGH-T3-14). Remedy class: tier text (R65, R67; see 1.7).
- **Tier:** T3. Every draft named T3.
- **Proposed remedy (direction or options; not text):**
  - (a) Apply R65 and R67 as recorded on the T3 agenda (the 129-versus-127 figure is R220's, closed).

### 2.4 T4: Asset elevation template (5 items, 14 rows)

T4 has no D2 agenda: Track E §6 lists agendas for T1-T3 only, and plan v1.5 §3.6 lists Tier 4 as a draft, to be accepted at decision N-7.T4. These items therefore go to the T4 revision, not to an agenda that exists.

#### TGH-T4-01 · The `kind` vocabulary has no place for a view, an UPDATE-only writer, an undeclared-target writer, a no-writer asset, or a service with a table

- **Rank / consequence:** rank 16 of 54; L1 L2 L4 L5 (4); 5 TG rows; 66 active assets in those layers.
- **Folded rows (5; L1 L2 L4 L5):** TG-L1-007, TG-L2-007, TG-L4-006, TG-L5-016, TG-L5-030
- **Also touches (not folded):** item TGH-T3-21; item TGH-T4-03.
- **Clause that failed to provide:** T4 §0 (L74): `kind: data | service (no table by design) | multi-table | rider (producer_covered) | static (migration-seeded)`. T3 §1.1 (L169-170) lists statuses "registered, writer-backed, service, residual, shared, historical"; the registry carries a third vocabulary; none of the three is defined against the others.
- **What the drafts needed:** One kind per asset for the cases below, and the gate applicability (Build, Idem) each implies.
- **Evidence:**
  - L1: `ga_strength` (writes a partition of `chart_facts`, `target_table` NULL) and `ga_structural` (target NULL, `count_sql` over two tables) fit neither `data`-with-target, a declared `multi-table` set, nor `rider`; the census `Build.target` now reads PASS with explanatory text.
  - L2: `bo_samvada` (`storage_type` `postgres_view`, a writer with no INSERT or DELETE, `count_sql` = `SELECT 0 AS count`), an UPDATE-only writer (`bo_laksana_rerank`), and 6 of 23 assets whose writer writes tables their `count_sql` does not count.
  - L4: registry `asset_kind` = `artifact` on 9 of 9, `asset_type` `data`, `domain` `chart`, `rung` `R4` (the word `rung` appears in none of T1-T4), `catalog_status` CURRENT x8 and DRAFT x1; `ph_rectification` is two-table by its `count_sql`.
  - L5: `lel_events` has no writer (`has_writer = f`, `asset_kind = data`, no target, `expected_volume_formula = EXOGENOUS(native-authored source corpus, floor 0)`); decision N-14.R236 (2026-09-29) says Build and Idem are N/A by registry rule, the census reads `Build.completion` FAIL ("live=63 and no build record at all"), and R236 still reads OPEN in register v2.8. `mi_seva` and `mi_abhilekha` are `asset_kind = service` with target tables and DRAFT status, while T4's service means "no table by design".
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 5 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R14, R97, R125, R182, R196, R211, R236, R247. Adjacent only: none. R14, R97, R125, R182, R196, R211, R236 (native/data-plane decision), R247 are open and not on the D2-ruled 31. Remedy class: mixed (instrument: R196; both: R182; tier text: R14, R97, R125, R211; no remedy stated: R236, R247; see 1.7).
- **Tier:** T4. Drafts named: T2 x1 (L5) · T3 x1 (L4) · T4 x3 (L1 L2 L5). Sources: L1, L2, L5 (one row) say T4, L4 says T3, L5 (one row) says T2 (its cited clause is T2 §11 L572 on service proofs). Assigned T4: the kind list is T4 §0 (L74); T3 and T2 only reference it.
- **Proposed remedy (direction or options; not text):**
  - (a) T4 §0 extends the kind list (candidates the register names: `view`, R125; UPDATE-only; no-writer; service-with-table) with the gate applicability of each.
  - (b) A one-line crosswalk between T3 §1.1 statuses, T4 kinds and the registry's `asset_kind` (the L4 facet).

#### TGH-T4-02 · Assets with no table (services): the storage, completeness, ablation, contract and vocabulary clauses assume rows

- **Rank / consequence:** rank 28 of 54; L0 L3 (2); 3 TG rows; 61 active assets in those layers.
- **Folded rows (3; L0 L3):** TG-L0-029, TG-L3-022, TG-L3-023
- **Clause that failed to provide:** T4 §1 storage bullets (L127-129; producer bullet "or 'service'"), §1.1 ("a census against a DECLARED universe"), §4 Vocab row; T3 §1.1 (L171-172), §1.2 (L185-190), §2.3 (L288-292), §4.4 (L477).
- **What the drafts needed:** What "rows in production", "ablate", "produces a DP contract", "kernel", completeness and a vocabulary test mean for a service; the service descriptor a brief must disclose.
- **Evidence:**
  - L0: `bg_ephemeris_engine` and `bg_panchanga` are `asset_kind = service` with `count_sql`, `target_table`, `target_floor` NULL; `Dens.served` FAIL for both although neither has a table (6 modules; 1 module); `Earn.service_state` is registered with `detector: NONE`.
  - L3: four services (`ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva`, `ka_tulana`): `Build.target` N/A on 4, `Count.floor` N/A on 2 (no entry on the other 2), `Idem.pattern` PARTIAL on all 4 ("nothing to replace; not graded N/A"); `Complete.width` NOT_GENERIC on all 21 assets.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 3 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R14, R165, R166, R167, R171, R173, R175, R176, R177. Adjacent only: none. R14 (primary) and its P4 extensions are open and not on the D2-ruled 31. Remedy class: mixed (both: R173; tier text: R14, R165, R166, R167, R171, R175, R176, R177; see 1.7).
- **Tier:** T4. Drafts named: T3 x1 (L3) · T4 x2 (L0 L3). Sources: L0 and L3 (one row) say T4, L3 (the other row) says T3. Assigned T4: R14 is a T4 §1 row and the storage bullets are where the table assumption sits; T3 carries riders.
- **Proposed remedy (direction or options; not text):**
  - (a) T4 §0/§1/§3/§4/§6 gain service-shaped fills (the direction R14 records, extended by R165-R167, R171, R173, R175-R177).
  - (b) T3 §1.1, §1.2, §2.3, §4.4 state the service reading of each clause (a rider).

#### TGH-T4-03 · A writer-backed asset that is empty: no clause says how "empty by design" is declared or graded

- **Rank / consequence:** rank 32 of 54; L1 L5 (2); 2 TG rows; 34 active assets in those layers.
- **Folded rows (2; L1 L5):** TG-L1-008, TG-L5-015
- **Also touches (not folded):** item TGH-T4-01 (no-writer and service-with-table kinds).
- **Clause that failed to provide:** T4 §4.2 check 6 (L277): completion honesty covers "a populated table" ("`rows_written = 0` against a populated table is a status with no measurement behind it") and "a service"; the empty writer-backed data table is a third case. T3 §5.2 Build gate (L539). The phrase "layer-plan claim that the emptiness is by design" is the census's own wording, not a T3 or T4 clause.
- **What the drafts needed:** A verdict rule, and a declarable state, for a writer-backed asset that is legitimately empty; who may make the claim, on what evidence, by what detector.
- **Evidence:**
  - L1: `ga_prashna` `lit`, `rows_written` 0, 0 chart rows; census2 `Build.completion` PARTIAL ("indistinguishable from a writer that has never produced a row"), `Count.floor` N/A (`target_floor` 0), `Complete.depth` and `Vocab.identity` NO_DETECTOR; census1 read the same cell ERRORED (permission). `ga_vargas`: `lit` with `rows_written` 24,400 but 0 chart rows now; `Build.completion` FAIL and `Count.floor` FAIL (live 0, floor 22,092): the CLAUDE.md §N.8 defect class observed on one asset.
  - L5: empty on chart 482012f1: `mimamsa_journal` 0, `mimamsa_intervention_ledger` 0, `mimamsa_insight_embeddings` 0; whole table: `mimamsa_preferences` 0, `mimamsa_export_log` 0. `Build.completion` PARTIAL for `mi_abhilekha`, `mi_seva`, `mi_vistara`, FAIL (`dormant`) for `mi_sankalpa`. The registry `expected_volume_formula` carries "EXOGENOUS(...)" for these (e.g. `EXOGENOUS(append_only_event_log, floor 0)`), a registry convention no tier defines.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 2 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R99 [PARTIAL], R126. Adjacent only: none. R99 is PARTIAL in v2.8 (the by-design detector and `ga_prashna`'s case); R126 is L2's same case. Neither is on the D2-ruled 31. Remedy class: mixed (instrument: R126; tier text: R99; see 1.7).
- **Tier:** T4. Drafts named: T3 x1 (L5) · T4 x1 (L1). Sources: L1 says T4, L5 says T3. Assigned T4: check 6 is T4 §4.2 (L277) and T3 §5.2 only carries the Build gate row.
- **Proposed remedy (direction or options; not text):**
  - (a) T4 §4.2 check 6 adds the third case and how emptiness-by-design is declared (who, evidence, detector).
  - (b) Adopt the registry's EXOGENOUS marker as the declaration (a fact from the L5 draft; its owners must accept).
  - (c) T3 §5.2 Build row is edited to match (a rider).

#### TGH-T4-04 · The declared universe a completeness count divides by: T4 §1.1 says to declare it and names no place to declare it

- **Rank / consequence:** rank 21 of 54; L0 L1 L4 (3); 3 TG rows; 68 active assets in those layers; 127 gate cells the census cannot grade (`Complete.width` NOT_GENERIC on 127 of 127 active assets, read over all six layers' rows).
- **Folded rows (3; L0 L1 L4):** TG-L0-007, TG-L1-013, TG-L4-014
- **Also touches (not folded):** item TGH-T2-01 (the ownership half of the same three rows); item TGH-T4-02 (its L3 evidence reads `Complete.width` NOT_GENERIC on all 21 assets, services included).
- **Clause that failed to provide:** T4 §1.1 (L145-162): "measured_by: a census against a DECLARED universe" and "Declare the universe first, from a source or from the ontology". The section does not say who records the declaration (layer instance, asset brief or registry) or where the census reads it.
- **What the drafts needed:** A declared universe per asset, so that width and depth can be measured against something.
- **Evidence:**
  - `Complete.width` NOT_GENERIC ("no declared universe for this asset") on 40 of 40 (L0), 19 of 19 (L1) and 9 of 9 (L4); the same reading on 23 of 23 (L2), 21 of 21 (L3) and 15 of 15 (L5) sits in the evidence of the rows folded in TGH-T2-01: 127 of 127 active assets. The census's own wording adds: "declaring one is the first width gap".
  - L0: `Complete.depth` 9 PARTIAL, 1 NO_DETECTOR (a table with 0 rows). L1: `Complete.depth` is measured but over the whole table for the 8 chart-table assets.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 3 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R22, R98, R123. Adjacent only: none. Cited by the same rows for the ownership half, carried in TGH-T2-01: R90*, R110, R187, R202. R22 records that a place to declare a universe is needed first (R06-adjacent). Remedy class: mixed (instrument: R22, R123; tier text: R98; see 1.7).
- **Tier:** T4. Drafts named: T2 x3 (L0 L1 L4). Sources: all three say T2, because each row's headline ask is the ownership half; the L1 row adds "also T4 §1.1: who declares a universe, layer or brief". Assigned T4: the sentence that fails is T4 §1.1's, R98 and R123 quote it, and the ownership half stays in TGH-T2-01.
- **Proposed remedy (direction or options; not text):**
  - (a) T4 §1.1 names the declaring artifact (registry field, layer instance §2.4 or asset brief) and what the census reads: R22 and R123 point to a registry or instance field, R98 to the layer instance naming each asset's universe source with the brief citing it.
  - (b) T3 §2.4 states that an instance names each asset's universe source where one exists and otherwise reports that none is declared (R98's direction).
  - (c) The registry or census field itself (R22, R123) is Track E.

#### TGH-T4-05 · The idempotency convention for global-scope assets: T4 §6 names L0 upsert and L1+ delete-then-insert on chart x natural key, and nothing for an asset with no chart key

- **Rank / consequence:** rank 51 of 54; L5 (1); 1 TG row; 15 active assets in those layers.
- **Folded rows (1; L5):** TG-L5-018
- **Also touches (not folded):** item TGH-T3-18 (the Idem claim itself); item TGH-T3-16 (where the natural key is declared).
- **Clause that failed to provide:** T4 §6 (L396-397): "the layer's convention: L0 `ON CONFLICT` upsert; L1+ delete-then-insert scoped to `(chart_id × natural key)`". T2 §3.3 (L174) retains registered scope for shared L5 qualification/model resources and global services.
- **What the drafts needed:** The idempotency scope for global L5 assets.
- **Evidence:**
  - `registry: scope = global` for `mi_kula` and `mi_vistara` (`mi_kula.py:312-313` deletes both tables without a WHERE); `mi_seva` (`mimamsa_preferences`, keyed `(user_id, channel_id)`, no `chart_id` column) and `mi_bhara` (`id`) also lack the chart key.
- **Register:** covered by an open register row that is not on the D2-ruled E2.1 list. Rows: 1 same-gap / 0 adjacent-only / 0 none. Same-gap rows cited: R96, R213. Adjacent only: none. R213 is a T4 §6 row; R96 is the shared-table natural-key row. Both are open and not on the D2-ruled 31. Remedy class: tier text (R96, R213; see 1.7).
- **Tier:** T4. Every draft named T4. R213 is itself a T4 §6 row, and the convention list at L396-397 has no global case.
- **Proposed remedy (direction or options; not text):**
  - (a) T4 §6 gains a form of the convention for global-scope assets (R213's direction: scoped to the declared key alone, without the chart key, with the scope stated per asset in §0).
  - (b) Where that declared key lives is the item TGH-T3-16's (R96).

## 3. Dropped, withdrawn, recast and narrowed rows

### 3.1 Ids not counted in the 159 (ledger; each appears here once and in no item)

| status | id | what its own draft says | where its residue went |
|---|---|---|---|
| DROPPED | TG-L0-001 | Recast at rev1 (gate review) from a claimed gap to a **proposal to T1**, not a missing clause: T1 L500 already places L0's ephemeris and calendar foundations under Source and domain fidelity, and T2 §13.3 item 1 (L662-665) forbids a layer adding obligations; the three obligations v3.0 added were struck. The only residue is an optional proposal for T1's owner: T1 §14's fidelity evidence does not say what "correct method identity" means for a computed quantity. | Carried as a "related, not counted" note on TGH-T1-01, where SS decides whether T1 opens. |
| DROPPED | TG-L0-028 | Withdrawn at rev1 as a tier gap: T4 §0 `kind` (L74) has `rider (producer_covered)` and T4 §1 Producer (L129) offers "or the asset it rides on", so an id that rides a sibling's writer has a place. What remains is a layer finding (for `bg_nakshatra_medical` and `bg_transit_engine` the code registers a writer while the registry says `has_writer = false`; `bg_sign_medical` was never dispatched), recorded in the L0 instance §1.1.5 and C-12, C-13. | None: not a tier gap. Its mirrored direction (a declared writer with no code) is R211/R212. |

### 3.2 Kept, at a scope a later review narrowed or corrected

These rows are folded into items at their **narrowed** scope; the broader first-issue claim is not carried.

| row (layer draft) | change recorded in its own changelog or text | item |
|---|---|---|
| TG‑L0‑006 | narrowed at rev1 to the detector only: T2 §9.2 (L500, L501, L510-512) supplies L0's ON row, OFF row and storage separation; moved at v1.1 from TGH-T2-06 (section 3.5) | TGH-T3-15 |
| TG‑L0‑004 | narrowed at rev1: T2 §7.1 names L0 for DP01, DP02, DP05, DP07 (DP10 "All producers"); only the per-asset and consumed-side assignment is missing | TGH-T2-04 |
| TG‑L0‑020 | citation corrected at rev1 (T3 L476, not L479) | TGH-T3-11 |
| TG‑L0‑017, TG‑L0‑007 | evidence re-worded at rev1 so no verdict rests on the draft's own detector | TGH-T3-15, TGH-T4-04 |
| TG‑L1‑010 | narrowed from R88: T2 §9.2 (L493-517) does supply the switch; only the detector and the event-time context's identity remain; moved at v1.1 from TGH-T2-06 to the detector item, the identity kept as a rider on TGH-T2-06 (section 3.5) | TGH-T3-15 |
| TG‑L1‑012 | narrowed: the join of T2 §3.4 and §7.1 is clean except the DP05/DP07 shares | TGH-T2-02 |
| TG‑L1‑008 | rewritten in rev1 from the after-grant census (`ga_prashna` `Build.completion` PARTIAL, not ERRORED) | TGH-T4-03 |
| TG‑L1‑021 | rev1 added the `classical_citation` and `source_citation` forms of `Ldgr.source_presence` | TGH-T3-22 |
| TG‑L2‑021 | narrowed at v1.1: the unit of independence (a placement) is supplied by T1 222, T3 681, T4 506; only the carrier field and the counting rule remain | TGH-T2-13 |
| TG‑L3‑018 | re-scoped at v1.1 as a delegation (T2 L382 and L629 hand the choice of criterion to the briefs); the criterion, its bounds and who declares remain | TGH-T2-14 |
| TG‑L3‑021 | search record corrected at v1.1 (twelve T2 hits for "kernel", not eight) | TGH-T3-19 |
| TG‑L4‑024 | evidence restated at v1.1: T2 L388/L390 give no role; the role is the gap for all nine assets; R192's premise (no role row) is inexact (12 versus 13) | TGH-T3-11 |
| TG‑L5‑007 | narrowed at v1.1 to the per-table overlay separation (T2 L500-501 already bind L5) | TGH-T2-06 |
| TG‑L5‑015 | v1.1: the "layer-plan claim that the emptiness is by design" wording attributed to the census, T4 L277 quoted | TGH-T4-03 |
| TG‑L5‑017 | v1.1: restated as an unreconciled conflict (T2 L402, DP15a L434, T1 L390-391 versus "never accretes") | TGH-T3-18 |
| TG‑L5‑024 | v1.1: T3 L476 has the role bullet; the gap is that no tier assigns the value | TGH-T3-11 |
| TG‑L5‑029 | v1.1: refiled from T2 to T3 (line 369) | TGH-T3-06 |
| TG‑L5‑009 | v1.1: corrected to DP01-DP09 | TGH-T2-02 |

The ids in the first column of sections 3.2, 3.3 and 3.5 are cross-references written with non-breaking hyphens; they are not ledger entries. The check in section 7 normalises the hyphens and requires each id to be folded exactly once in section 2 (its item's "Folded rows" line) and to appear once in the ledger.

### 3.3 Rows added by a review (already inside the 159)

TG‑L0‑030 (v1.1, edge type per edge), TG‑L1‑024 (rev1, units), TG‑L2‑023 and TG‑L2‑024 (v1.1, undefined §7; three state vocabularies), TG‑L5‑031 (v1.1, Null and Narr rows). They are folded like any other row.

### 3.4 Recorded by the drafts as not tier gaps (not harvested)

- L1: 2 layer gaps (LG-L1) and 12 measurement findings (MF-L1). L2: 13 measurement findings (MF-L2). L4: five findings (section 3 of its file). L5: findings F-01..F-12 (its instance, Part 6). L0: layer findings recorded in its instance with no action. L3: one registered-writer anomaly and seven register rows it judged instrument or data items (R134, R135, R146/R87, R157/R106, R160/R122, R237, R240).
- Two of the seven L3 judgements differ from what five other layers registered as tier gaps (R87 three-way baseline, R106 consumer probe): see TGH-T3-09 and TGH-T3-10. The harvest keeps the five-layer view and records the dissent on the items.
- Clauses the drafts checked and found supplied, so no row exists (do not reopen without new evidence): L2 §0.2 (T2 §6.3 supplies the Bodha paragraph; contradicts R101's premise), the life-event switch at layer grain (T2 §9.2 L500-501, L510-512; four drafts), L2 "for each rule, the detector" (T3's honest-null convention), L3 owned question and correctness rule (T2 §3.1 L142; T1 L425), and the L0 `rider`/`producer_covered` kind.

### 3.5 Moves and review corrections at v1.1 (independent Sonnet review 2026-09-30)

Rows that changed item (the tier of each item is its id's tier):

| row | from item | to item | why |
|---|---|---|---|
| TG‑L0‑006, TG‑L1‑010 | TGH-T2-06 | TGH-T3-15 | both rows were narrowed to the detector only (their own changelogs); the clause is T3 §2.1's "For each rule, the detector"; L1's event-time-identity facet stays on TGH-T2-06 as a rider |
| TG‑L0‑007, TG‑L1‑013, TG‑L4‑014 | TGH-T2-01 | TGH-T4-04 | the three rows whose own Needed line also asks for a declared universe (T4 §1.1); the ownership half is carried in full by the three ownership-only rows left in TGH-T2-01 |
| TG‑L0‑011 | TGH-T2-03 | TGH-T2-20 | its new part is the population behind T2 §4.1 rules 4 and 6 |
| TG‑L5‑012 | TGH-T2-03 | TGH-T2-21 | its new part is the event-class omission in T2 §4.1's Scope list |
| TG‑L1‑023 | TGH-T3-14 | TGH-T3-27 | the only row that carries the "six" checks, "eight-row" map and 129-asset mismatches (R65, R67, R220) |
| TG‑L5‑018 | TGH-T3-18 | TGH-T4-05 | R213 is a T4 §6 row and the convention list at T4 L396-397 has no global case; the row named T4 in its own draft |

Register citations that changed item list (no row moved): R94 and R119 from TGH-T2-02 to TGH-T3-07; R113 from TGH-T3-05 and TGH-T3-12 to TGH-T3-06; R08, R92, R143, R144 out of TGH-T3-01's same-gap list to the items that own their clauses (TGH-T3-14, TGH-T3-02, TGH-T2-03); R22, R98, R123 from TGH-T2-01 to TGH-T4-04; R65, R67, R220 from TGH-T3-14 to TGH-T3-27; R213 and R96 from TGH-T3-18 to TGH-T4-05; R99 and R210 out of TGH-T2-09's same-gap list (cited by the L5 row for other clauses); R117 from TGH-T2-06 to TGH-T3-15. The item statuses in sections 1.1 and 1.4 follow from these lists.

Review premises not applied as stated:
1. **R94 in TGH-T2-02.** The review says no source row of the item cites R94. The L5 row for the presentation rows cites R094 and R119, in the parenthesis "parity vs [TRANSFERS]". They are taken out of the item's same-gap list anyway, because their own remedies concern parity ownership and the [TRANSFERS] tag and not the row-to-layer assignment; TGH-T3-07 already lists both.
2. **T2 L139 for "L0 remains the global foundation" (TGH-T2-11).** The sentence is at T2 L58; L139 is L0's row of the §3.1 table and does not say it. Only L58 is cited.
3. **"Ldgr absent on 57 assets" (TGH-T3-01).** The drafts support 42 of the 103 L0-L3 assets with no `Ldgr.source_presence` reading (L0 16, L1 6, L2 7, L3 13); the L4 and L5 drafts give no Ldgr reading, so 57 is not derivable. The item states 42 of 103 and does not add it to the 254.
4. **"TGH-T3-14 recorded not on list".** v1.0 recorded TGH-T3-14 as on the list (R08, R65, R67 are on it). The inconsistent items were TGH-T3-01 (not on list although it cited R08, for another clause) and TGH-T3-19 (on list through R93, which no folded row cites); both now follow the derived rule.

## 4. Observations for the E2 fold

1. **One sweep for [TRANSFERS].** TGH-T3-07 (parity) and TGH-T3-26 (Dens) are the same defect class: an obligation T2 marks [TRANSFERS] appears as a gate or test in T3. One pass over the T3 gate map can settle both.
2. **3 items are instrument-class and 17 are mixed** (sections 1.6 and 1.7, derived per item from the register remedy wording); the registry or census half of a mixed item is the half that stays with Track E.
3. **The gap file is not always mirrored in the instance.** Six gap rows are cited by no text of their own layer instance (TG‑L1‑007; TG‑L5‑015, TG‑L5‑018, TG‑L5‑019, TG‑L5‑027, TG‑L5‑030). This was found by grepping each of the six instances for each id of its layer; the rows are folded like any other, and the instance authors should mark them at the next revision.
4. **Register housekeeping the harvest implies (not done here).** R130, R197, R100, R179 carry T2-table remedies that D5 withdrew (TGH-T3-04); R236 reads OPEN in v2.8 although decision N-14.R236 exists (TGH-T4-01); the register's 27 "reopen agenda" rows and Track E's 31-row list agree once R94, R140, R185 and R221 are counted as they are described (the E2.1 paragraph above section 1).
5. **New-to-register items** (21): TGH-T2-07, TGH-T3-18, TGH-T3-20, TGH-T2-09, TGH-T2-10, TGH-T2-11, TGH-T2-12, TGH-T3-21, TGH-T2-13, TGH-T2-14, TGH-T2-15, TGH-T1-01, TGH-T2-16, TGH-T3-22, TGH-T2-17, TGH-T2-18, TGH-T3-23, TGH-T2-21, TGH-T2-19, TGH-T3-25, TGH-T3-26. E2 needs a register row for each before its agenda entry, and should confirm none is already carried by an E2.1 draft row.

## 5. Second-round list

Empty at v1.1. Per Track A brief §7 and Track E §6, once an agenda opens it is closed; later gaps go here as a list in this same file.

## 6. Accounting check

`check_harvest.py` (reproduced in section 7) re-parses the six source files, the change register and this document independently of the generator. It confirms that every `TG-*` id in the six files appears exactly once in the items (in a "Folded rows" line of section 2) and exactly once in the ledger (a "Folded rows" line or the section 3.1 table); that ids cited elsewhere (sections 3.2, 3.3, 3.5) are cross-references to known ids, non-breaking hyphens being normalised to plain hyphens before any id is counted; that the row classes (same-gap, adjacent-only, none), the item statuses, the remedy-class labels and the instrument-class set are derived from the sources, the register and the item lists and equal what every item line and table states; that every count column of sections 1.1, 1.2, 1.3, 1.4 and 1.5, every item's rank line and the rank order of section 1.4 equal a recomputation; and that the new-to-register list of section 4 equals the set of new items. Output for this version:

```
PASS  ids found in the six files: 161 (161 = 159 counted + 2 not counted)
PASS  counted rows (excluding TG-L0-001, TG-L0-028): 159
PASS  per-layer counted rows L0..L5 = [28, 24, 24, 27, 25, 31] (the drafts state 28/24/24/27/25/31)
PASS  the D2-ruled E2.1 list parsed from the file: 31 rows
PASS  items with a Folded rows line: 54 of 54 items
PASS  ids folded into items: 159, distinct 159
PASS  ids in the dropped ledger: ['TG-L0-001', 'TG-L0-028']
PASS  every source id is in the ledger exactly once (ledger ids not in sources 0, source ids not in ledger 0)
PASS  section 2: every counted id appears exactly once, in a Folded rows line (max multiplicity 1)
PASS  section 2: no id is cited by id outside a Folded rows line
PASS  ids cited elsewhere (sections 3.1-3.5, after hyphen normalisation): 36 distinct, all known; 44 occurrences
RESULT  159 in, 159 accounted
PASS  159 in, 159 accounted (159 folded + 2 ledger-only = 161 ids)
PASS  rows folded per layer = source rows per layer: [28, 24, 24, 27, 25, 31]
PASS  every rank line says "of 54" (the number of items)
PASS  rank lines: layers, row counts and active-asset sums equal the Folded rows lines (mismatches: [])
PASS  asterisks in every Same-gap / Adjacent list = membership of the D2-ruled 31
info    row classes derived from the source cells: same-gap 126 / adjacent-only 7 / none 26
info    adjacent-only rows: ['TG-L2-016', 'TG-L2-020', 'TG-L2-022', 'TG-L4-018', 'TG-L4-022', 'TG-L4-023', 'TG-L4-025']
info    "NEW (adjacent: ...)" rows counted as none: ['TG-L2-024', 'TG-L3-003', 'TG-L3-014', 'TG-L3-019', 'TG-L3-027'] -> as adjacent-only the triple would be 126 / 12 / 21
PASS  every item "Rows: a same-gap / b adjacent-only / c none" equals the derived row classes
PASS  every item status sentence equals the status derived from its Same-gap list (no overrides)
PASS  every open same-gap register row listed by an item has a remedy class in section 1.7
PASS  every item "Remedy class" label equals the label derived from the 1.7 row classes
PASS  section 1.6 class-level bullet lists the derived instrument-class items ['TGH-T3-01', 'TGH-T3-06', 'TGH-T3-10'] and the 7 mixed T3 items
PASS  every item rank line equals the rank recomputed from the ordering rule
PASS  section 1.4: 54 rows; rank, order, tier, layers, rows, assets and status all equal the recomputation
PASS  table 1.1 T1: items 1, rows 1, same/adj/none 0/0/1, on/covered/new 0/0/1 (table [1, 1, 0, 0, 1, 0, 0, 1])
PASS  table 1.1 T2: items 21, rows 47, same/adj/none 32/2/13, on/covered/new 8/0/13 (table [21, 47, 32, 2, 13, 8, 0, 13])
PASS  table 1.1 T3: items 27, rows 97, same/adj/none 80/5/12, on/covered/new 8/12/7 (table [27, 97, 80, 5, 12, 8, 12, 7])
PASS  table 1.1 T4: items 5, rows 14, same/adj/none 14/0/0, on/covered/new 0/5/0 (table [5, 14, 14, 0, 0, 0, 5, 0])
PASS  table 1.1 total: [54, 159, 126, 7, 26, 16, 17, 21] (table [54, 159, 126, 7, 26, 16, 17, 21])
PASS  rows by draft tier T1 1 · T2 51 · T3 97 · T4 10; by assigned tier T1 1 · T2 47 · T3 97 · T4 14; re-tiered 23
PASS  section 1.1 states the alternative triple 126 / 12 / 21 for the 5 "NEW (adjacent: ...)" rows
PASS  table 1.2: every column of the six layer rows (assets, rows, items, same/adj/none, draft tiers, assigned tiers, re-tiered) equals the recomputation
PASS  table 1.2 "all layers" row = [127, 159, 155], 126 / 7 / 26, re-tiered 23
PASS  table 1.3 dedupe ratio (2.94 rows per item, 66.0% fewer), multi-layer / one-layer / six-layer counts = [33, 138, 21, 21, 7, 42]
PASS  table 1.3 rows-per-item distribution and single-row items (21)
PASS  table 1.3 register duplication: 126 same-gap rows; 33 other rows in 25 items; 20 of 21 new items hold one; 5 covered items carry one
PASS  table 1.5 lists exactly the 14 items whose drafts named another tier than the assigned one, with the tiers named and the assigned tier as derived
PASS  section 1.5 sentence: 13 of 54 items named more than one tier, 1 further item assigned another tier
PASS  section 4 new-to-register list = the 21 items with status new
SUMMARY PASS (0 failed checks)
```

## 7. Check script

```python
#!/usr/bin/env python3
"""A.H accounting check v1.1. Re-parses the six source files, the change register and the harvest,
independently of the generator. Usage: python3 check_harvest.py <layers_dir> <harvest.md> <register.md>   (exit 0 = PASS)
Nothing below is a hard-coded id set: adjacency, statuses, class labels, ranks and every table count are derived."""
import re, sys
from collections import Counter

LAYERS_DIR, HARVEST, REGISTER = sys.argv[1:4]
ID = re.compile(r'TG-L[0-5]-\d{3}')
ASSETS = {0: 40, 1: 19, 2: 23, 3: 21, 4: 9, 5: 15}
fails = []
def check(cond, msg):
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    if not cond: fails.append(msg)
def cells(line): return [c.strip() for c in re.split(r'(?<!\\)\|', line)][1:-1]
def rn(s): return sorted({int(x) for x in re.findall(r'R0*(\d{1,3})', s)})
def num(s): return int(re.sub(r'[^\d]', '', s))

# ---- 1. sources: ids, draft tier, register cell ----
src_ids, src_tier, src_reg = {}, {}, {}
for l in range(6):
    txt = open('%s/L%d/L%d_TIER_GAPS_v1_0.md' % (LAYERS_DIR, l, l), encoding='utf-8').read()
    for i in sorted(set(re.findall(r'TG-L%d-\d{3}' % l, txt))): src_ids[i] = l
    if l == 1:
        for m in re.finditer(r'^### (TG-L1-\d{3}).*?\n(.*?)(?=^### |^## Part B)', txt, re.M | re.S):
            src_tier[m.group(1)] = re.search(r'\*\*Tier:\*\*\s*(T\d)', m.group(2)).group(1)
            src_reg[m.group(1)] = re.sub(r'\*', '', re.search(r'\*\*Register:\*\*(.*)', m.group(2)).group(1).strip())
        continue
    for line in txt.splitlines():
        m = re.match(r'^\|\s*\**(TG-L%d-\d{3})\**' % l, line)
        if not m: continue
        c = cells(line)
        t = re.sub(r'\*', '', c[1] if l == 4 else c[-2])
        src_tier[m.group(1)] = re.match(r'(T\d)', t).group(1) if re.match(r'(T\d)', t) else 'none'
        src_reg[m.group(1)] = re.sub(r'\*', '', c[-1])
l0txt = open('%s/L0/L0_TIER_GAPS_v1_0.md' % LAYERS_DIR, encoding='utf-8').read()
NOT_COUNTED = set(re.findall(r'^\|\s*\**(TG-L0-\d{3})\**\s*\*\((?:PROPOSAL|WITHDRAWN)', l0txt, re.M))
counted = [i for i in src_ids if i not in NOT_COUNTED]
lay = lambda i: int(i[4])
per_layer_src = Counter(lay(i) for i in counted)
check(len(src_ids) == 161, 'ids found in the six files: %d (161 = 159 counted + 2 not counted)' % len(src_ids))
check(len(counted) == 159, 'counted rows (excluding %s): %d' % (', '.join(sorted(NOT_COUNTED)), len(counted)))
check([per_layer_src[l] for l in range(6)] == [28, 24, 24, 27, 25, 31], 'per-layer counted rows L0..L5 = %s (the drafts state 28/24/24/27/25/31)' % [per_layer_src[l] for l in range(6)])

# ---- 2. register: severity and the D2-ruled list ----
sev = {}
for line in open(REGISTER, encoding='utf-8'):
    m = re.match(r'^\| (R\d{2,3}) \|', line)
    if m: sev[int(m.group(1)[1:])] = cells(line)[3]
doc = open(HARVEST, encoding='utf-8').read().replace('‑', '-').replace('‐', '-')   # non-breaking hyphens -> '-'
m = re.search(r'from the D2 ruling: (.*?) \(31 rows\)', doc)
LIST31 = set(rn(m.group(1)))
check(len(LIST31) == 31, 'the D2-ruled E2.1 list parsed from the file: %d rows' % len(LIST31))
body = doc.split('## 6. Accounting check')[0]
sec2 = body[body.index('## 2. Items'):body.index('## 3. Dropped')]

# ---- 3. ledger: each id once in the items (Folded rows line) and once in the ledger ----
fold_lines = [ln for ln in sec2.splitlines() if ln.startswith('- **Folded rows')]
drop_lines = [ln for ln in body.splitlines() if ln.startswith('| DROPPED |')]
folded = [i for ln in fold_lines for i in ID.findall(ln)]
dropped = [i for ln in drop_lines for i in ID.findall(ln.split('|')[2])]
ledger = Counter(folded + dropped)
blocks = re.split(r'^#### (TGH-T\d-\d\d) ', sec2, flags=re.M)
ITEM = {}
for k in range(1, len(blocks), 2): ITEM[blocks[k]] = blocks[k + 1]
check(len(fold_lines) == len(ITEM), 'items with a Folded rows line: %d of %d items' % (len(fold_lines), len(ITEM)))
check(len(folded) == 159 and len(set(folded)) == 159, 'ids folded into items: %d, distinct %d' % (len(folded), len(set(folded))))
check(sorted(dropped) == sorted(NOT_COUNTED), 'ids in the dropped ledger: %s' % sorted(dropped))
check(set(ledger) == set(src_ids) and all(v == 1 for v in ledger.values()), 'every source id is in the ledger exactly once (ledger ids not in sources %d, source ids not in ledger %d)' % (len(set(ledger) - set(src_ids)), len(set(src_ids) - set(ledger))))
in_items = Counter(ID.findall(sec2))
check(all(in_items[i] == (0 if i in NOT_COUNTED else 1) for i in src_ids) and set(in_items) <= set(src_ids), 'section 2: every counted id appears exactly once, in a Folded rows line (max multiplicity %d)' % max(in_items.values()))
check(not ID.findall('\n'.join(l for l in sec2.splitlines() if not l.startswith('- **Folded rows'))), 'section 2: no id is cited by id outside a Folded rows line')
outside = Counter(ID.findall(body.replace(sec2, '')))
check(set(outside) <= set(src_ids), 'ids cited elsewhere (sections 3.1-3.5, after hyphen normalisation): %d distinct, all known; %d occurrences' % (len(outside), sum(outside.values())))
acc = sum(1 for i in counted if ledger[i] == 1)
print('RESULT  %d in, %d accounted' % (len(counted), acc))
check(acc == len(counted) == 159, '159 in, 159 accounted (%d folded + %d ledger-only = %d ids)' % (len(set(folded)), len(set(dropped)), len(src_ids)))
assigned = {}; tier_of = {}
for i, b in ITEM.items():
    tier_of[i] = i[4:6]
    for r in ID.findall([x for x in b.splitlines() if x.startswith('- **Folded rows')][0]): assigned[r] = i
check(Counter(lay(i) for i in folded) == per_layer_src, 'rows folded per layer = source rows per layer: %s' % [Counter(lay(i) for i in folded)[l] for l in range(6)])

# ---- 4. item lines: rank line, register line ----
IT = {}
for i, b in ITEM.items():
    rl = re.search(r'^- \*\*Rank / consequence:\*\* rank (\d+) of (\d+); (.*?) \((\d+)\); (\d+) TG rows?; (\d+) active assets in those layers(?:; (\d+) gate cells)?', b, re.M)
    rg = re.search(r'^- \*\*Register:\*\* (.*)$', b, re.M).group(1)
    rr = re.match(r'(?P<st>.*?\.) Rows: (\d+) same-gap / (\d+) adjacent-only / (\d+) none\. Same-gap rows cited: (?P<same>.*?)\. Adjacent only: (?P<adj>.*?)\..*Remedy class: (?P<lab>instrument-class|mixed|tier text|no remedy stated|none) ', rg)
    same = [(int(x), s, t) for x, s, t in re.findall(r'R(\d{2,3})(\*?)(?: \[([A-Z]+)\])?', rr.group('same'))]
    adj = [(int(x), s, t) for x, s, t in re.findall(r'R(\d{2,3})(\*?)(?: \[([A-Z]+)\])?', rr.group('adj'))]
    IT[i] = dict(rank=int(rl.group(1)), n=int(rl.group(2)), layers=rl.group(3), nl=int(rl.group(4)), nrows=int(rl.group(5)), assets=int(rl.group(6)),
                 cells=int(rl.group(7) or 0), status=rr.group('st'), counts=tuple(int(rr.group(k)) for k in (2, 3, 4)), same=same, adj=adj,
                 lab=rr.group('lab'), rows=[r for r in ID.findall([x for x in b.splitlines() if x.startswith('- **Folded rows')][0])])
N = len(IT)
check(all(v['n'] == N for v in IT.values()), 'every rank line says "of %d" (the number of items)' % N)
bad = [i for i, v in IT.items() if not ({int(x) for x in re.findall(r'L(\d)', v['layers'])} if v['nl'] < 6 else set(range(6))) == {lay(r) for r in v['rows']} or v['nl'] != len({lay(r) for r in v['rows']}) or v['nrows'] != len(v['rows']) or v['assets'] != sum(ASSETS[l] for l in {lay(r) for r in v['rows']})]
check(not bad, 'rank lines: layers, row counts and active-asset sums equal the Folded rows lines (mismatches: %s)' % bad)
check(all(all((s == '*') == (n in LIST31) for n, s, t in v['same'] + v['adj']) for v in IT.values()), 'asterisks in every Same-gap / Adjacent list = membership of the D2-ruled 31')

# ---- 5. row classes (derived) ----
def rclass(r):
    cell = src_reg[r]; it = IT[assigned[r]]
    if re.match(r'\W*(none|new)\b', cell, re.I): return 'none'
    if re.search(r'nearest|adjacent|no exact row|no layer-level row', cell, re.I): return 'adj'
    nums = set(rn(cell)); a = {n for n, s, t in it['adj']}; sm = {n for n, s, t in it['same']}
    return 'adj' if nums and nums <= a and not (nums & sm) else 'same'
cls = {r: rclass(r) for r in counted}
cc = Counter(cls.values())
newadj = [r for r in counted if cls[r] == 'none' and re.search('adjacent', src_reg[r], re.I)]
print('info    row classes derived from the source cells: same-gap %d / adjacent-only %d / none %d' % (cc['same'], cc['adj'], cc['none']))
print('info    adjacent-only rows: %s' % sorted(r for r in counted if cls[r] == 'adj'))
print('info    "NEW (adjacent: ...)" rows counted as none: %s -> as adjacent-only the triple would be %d / %d / %d' % (sorted(newadj), cc['same'], cc['adj'] + len(newadj), cc['none'] - len(newadj)))
check(all(v['counts'] == tuple(Counter(cls[r] for r in v['rows'])[k] for k in ('same', 'adj', 'none')) for v in IT.values()), 'every item "Rows: a same-gap / b adjacent-only / c none" equals the derived row classes')

# ---- 6. item status, remedy class (derived) ----
def dstatus(v):
    if any(n in LIST31 for n, s, t in v['same']): return 'on'
    if any(t not in ('CLOSED', 'MEASURED') for n, s, t in v['same']): return 'cov'
    return 'new'
STX = {'on': 'covered by an open register row that is on the D2-ruled E2.1 list.', 'cov': 'covered by an open register row that is not on the D2-ruled E2.1 list.', 'new': 'new: no open same-gap register row.'}
STT = {'on': 'open row, on E2.1 list', 'cov': 'open row, not on list', 'new': 'new'}
ds = {i: dstatus(v) for i, v in IT.items()}
check(all(IT[i]['status'] == STX[ds[i]] for i in IT), 'every item status sentence equals the status derived from its Same-gap list (no overrides)')
s17 = doc[doc.index('### 1.7'):doc.index('## 2. Items')]
RC = {}
for line in s17.splitlines():
    m = re.match(r'^\| (instrument|both|tier text|no remedy stated) \| (.*) \|$', line)
    if m:
        for n in rn(m.group(2)): RC[n] = {'instrument': 'I', 'both': 'IT', 'tier text': 'T', 'no remedy stated': 'O'}[m.group(1)]
def dlabel(v):
    ns = [n for n, s, t in v['same'] if t != 'CLOSED']
    if not ns: return 'none'
    I = any(RC[n] in ('I', 'IT') for n in ns); T = any(RC[n] in ('T', 'IT') for n in ns)
    return 'instrument-class' if I and not T else 'tier text' if T and not I else 'mixed' if I and T else 'no remedy stated'
check(all(n in RC for v in IT.values() for n, s, t in v['same'] if t != 'CLOSED'), 'every open same-gap register row listed by an item has a remedy class in section 1.7')
check(all(IT[i]['lab'] == dlabel(IT[i]) for i in IT), 'every item "Remedy class" label equals the label derived from the 1.7 row classes')
instr = sorted(i for i in IT if dlabel(IT[i]) == 'instrument-class'); t3mixed = sorted(i for i in IT if dlabel(IT[i]) == 'mixed' and i[4:6] == 'T3')
s16 = doc[doc.index('### 1.6'):doc.index('### 1.7')]
m = re.search(r'\*\*(\d+) items are instrument-class\*\*.*?: (TGH[^.]*?)\. \*\*(\d+) T3 items are mixed\*\*.*?: (TGH[^.]*?)\. The layer drafts', s16, re.S)
check(bool(m) and sorted(re.findall(r'TGH-T\d-\d\d', m.group(2))) == instr and sorted(re.findall(r'TGH-T\d-\d\d', m.group(4))) == t3mixed, 'section 1.6 class-level bullet lists the derived instrument-class items %s and the %d mixed T3 items' % (instr, len(t3mixed)))

# ---- 7. ranks (derived) ----
def key(i):
    v = IT[i]; uncovered = sum(1 for r in v['rows'] if cls[r] != 'same')
    return (-v['nl'], -v['nrows'], -v['assets'], -v['cells'], -sum(1 for n, s, t in v['same'] if sev.get(n) == 'BLOCKS_LAYER'), -uncovered, i)
order = sorted(IT, key=key)
check(all(IT[i]['rank'] == k for k, i in enumerate(order, 1)), 'every item rank line equals the rank recomputed from the ordering rule')
s14 = doc[doc.index('### 1.4'):doc.index('### 1.5')]
t14 = [cells(l) for l in s14.splitlines() if re.match(r'^\| \d+ \| TGH', l)]
ok14 = len(t14) == N and all(int(c[0]) == k and c[1] == order[k - 1] and c[2] == c[1][4:6] and int(c[5]) == IT[c[1]]['nrows'] and int(c[6]) == IT[c[1]]['assets'] and (6 if c[4] == 'L0-L5' else len(c[4].split())) == IT[c[1]]['nl'] and c[7] == STT[ds[c[1]]] for k, c in enumerate(t14, 1))
check(ok14, 'section 1.4: %d rows; rank, order, tier, layers, rows, assets and status all equal the recomputation' % len(t14))

# ---- 8. summary tables ----
dtier = lambda r: src_tier[r]
def t_rows(t): return [r for r in counted if tier_of[assigned[r]] == t]
tab = {}
s11 = doc[doc.index('### 1.1'):doc.index('### 1.2')]
for l in s11.splitlines():
    m = re.match(r'^\| (T[1-4]|\*\*total\*\*) \| (.*) \|$', l)
    if m: tab[m.group(1).replace('*', '')] = [num(x) for x in m.group(2).split('|')]
for t in ('T1', 'T2', 'T3', 'T4'):
    its = [i for i in IT if tier_of[i] == t]; rs = t_rows(t); c = Counter(cls[r] for r in rs); d = Counter(ds[i] for i in its)
    exp = [len(its), len(rs), c['same'], c['adj'], c['none'], d['on'], d['cov'], d['new']]
    check(tab.get(t) == exp, 'table 1.1 %s: items %d, rows %d, same/adj/none %d/%d/%d, on/covered/new %d/%d/%d (table %s)' % ((t,) + tuple(exp) + (tab.get(t),)))
exp = [N, 159, cc['same'], cc['adj'], cc['none']] + [sum(1 for i in IT if ds[i] == k) for k in ('on', 'cov', 'new')]
check(tab.get('total') == exp, 'table 1.1 total: %s (table %s)' % (exp, tab.get('total')))
srct = Counter(src_tier[r] for r in counted)
m = re.search(r'the tier each layer draft gave \(before[^:]*\): T1 (\d+) · T2 (\d+) · T3 (\d+) · T4 (\d+) = (\d+); after the decisions in section 1\.5: T1 (\d+) · T2 (\d+) · T3 (\d+) · T4 (\d+)\. (\d+) of the 159', s11)
asg = Counter(tier_of[assigned[r]] for r in counted); retier = sum(1 for r in counted if src_tier[r] != tier_of[assigned[r]])
check(bool(m) and [int(x) for x in m.groups()] == [srct['T1'], srct['T2'], srct['T3'], srct['T4'], 159, asg['T1'], asg['T2'], asg['T3'], asg['T4'], retier], 'rows by draft tier T1 %d · T2 %d · T3 %d · T4 %d; by assigned tier T1 %d · T2 %d · T3 %d · T4 %d; re-tiered %d' % (srct['T1'], srct['T2'], srct['T3'], srct['T4'], asg['T1'], asg['T2'], asg['T3'], asg['T4'], retier))
m = re.search(r'includes the (\d+) rows worded "NEW \(adjacent: …\)".*?gives (\d+) / (\d+) / (\d+)\.', s11, re.S)
check(bool(m) and [int(x) for x in m.groups()] == [len(newadj), cc['same'], cc['adj'] + len(newadj), cc['none'] - len(newadj)], 'section 1.1 states the alternative triple %d / %d / %d for the %d "NEW (adjacent: ...)" rows' % (cc['same'], cc['adj'] + len(newadj), cc['none'] - len(newadj), len(newadj)))
s12 = doc[doc.index('### 1.2'):doc.index('### 1.3')]
ok12 = True
for l in range(6):
    rs = [r for r in counted if lay(r) == l]; c = Counter(cls[r] for r in rs)
    exp = [ASSETS[l], len(rs), len({assigned[r] for r in rs}), '%d / %d / %d' % (c['same'], c['adj'], c['none']), '·'.join(str(Counter(src_tier[r] for r in rs)['T%d' % k]) for k in range(1, 5)), '·'.join(str(Counter(tier_of[assigned[r]] for r in rs)['T%d' % k]) for k in range(1, 5)), sum(1 for r in rs if src_tier[r] != tier_of[assigned[r]])]
    row = [c_ for c_ in cells(next(x for x in s12.splitlines() if re.match(r'^\| L%d ' % l, x)))][1:8]
    g = [num(row[0]), num(row[1]), num(row[2]), row[3], row[4], row[5], num(row[6])]
    if g != exp: ok12 = False; print('        layer %d: table %s expected %s' % (l, g, exp))
check(ok12, 'table 1.2: every column of the six layer rows (assets, rows, items, same/adj/none, draft tiers, assigned tiers, re-tiered) equals the recomputation')
ta = [c_ for c_ in cells(next(x for x in s12.splitlines() if x.startswith('| all layers')))]
exp_all = [127, 159, sum(len({assigned[r] for r in counted if lay(r) == l}) for l in range(6))]
check([num(ta[1]), num(ta[2]), num(ta[3].split()[0])] == exp_all and ta[4] == '%d / %d / %d' % (cc['same'], cc['adj'], cc['none']) and ta[5] == '·'.join(str(srct['T%d' % k]) for k in range(1, 5)) and ta[6] == '·'.join(str(asg['T%d' % k]) for k in range(1, 5)) and num(ta[7]) == retier, 'table 1.2 "all layers" row = %s, %s, re-tiered %d' % (exp_all, ta[4], retier))
s13 = doc[doc.index('### 1.3'):doc.index('### 1.4')]
lset = lambda i: {lay(r) for r in IT[i]['rows']}
multi = [i for i in IT if len(lset(i)) >= 2]; one = [i for i in IT if len(lset(i)) < 2]; six = [i for i in IT if len(lset(i)) == 6]
rpi = Counter(IT[i]['nrows'] for i in IT)
uncov = [i for i in IT if any(cls[r] != 'same' for r in IT[i]['rows'])]; newi = [i for i in IT if ds[i] == 'new']
exp13 = [N, 159 / N, 100 * (159 - N) / 159, len(multi), sum(IT[i]['nrows'] for i in multi), len(one), sum(IT[i]['nrows'] for i in one), len(six), sum(IT[i]['nrows'] for i in six)]
m = re.search(r'159 TG rows -> (\d+) items: ([\d.]+) rows per item; ([\d.]+)% fewer.*?two or more layers: \*\*(\d+)\*\* \((\d+) rows\); from one layer only: (\d+) \((\d+) rows\)\. Items touching all six layers: (\d+) \((\d+) rows\)', s13, re.S)
g = m.groups() if m else None
check(bool(m) and int(g[0]) == N and g[1] == '%.2f' % exp13[1] and g[2] == '%.1f' % exp13[2] and [int(x) for x in g[3:]] == exp13[3:], 'table 1.3 dedupe ratio (%.2f rows per item, %.1f%% fewer), multi-layer / one-layer / six-layer counts = %s' % (exp13[1], exp13[2], exp13[3:]))
m = re.search(r'Rows per item: (.*?)\. Single-row items: (\d+)\.', s13)
check(bool(m) and m.group(1) == ', '.join('%d row%s x %d' % (k, '' if k == 1 else 's', rpi[k]) for k in sorted(rpi)) and int(m.group(2)) == rpi[1], 'table 1.3 rows-per-item distribution and single-row items (%d)' % rpi[1])
m = re.search(r'(\d+) of the 159 rows cite a register row as the same gap\. The other (\d+) rows \((\d+) with no row, (\d+) with only an adjacent row\) sit in (\d+) items; (\d+) of the (\d+) new items hold at least one such row \(item-level convention\), and (\d+) items are otherwise covered', s13)
check(bool(m) and [int(x) for x in m.groups()] == [cc['same'], 159 - cc['same'], cc['none'], cc['adj'], len(uncov), sum(1 for i in newi if i in uncov), len(newi), sum(1 for i in uncov if ds[i] != 'new')], 'table 1.3 register duplication: %d same-gap rows; %d other rows in %d items; %d of %d new items hold one; %d covered items carry one' % (cc['same'], 159 - cc['same'], len(uncov), sum(1 for i in newi if i in uncov), len(newi), sum(1 for i in uncov if ds[i] != 'new')))
s15 = doc[doc.index('### 1.5'):doc.index('### 1.6')]
want = {}
for i in IT:
    d = {}
    for r in IT[i]['rows']: d.setdefault(src_tier[r], []).append('L' + r[4])
    if len(d) > 1 or list(d)[0] != tier_of[i]: want[i] = ' · '.join('%s x%d (%s)' % (t, len(d[t]), ' '.join(sorted(d[t]))) for t in sorted(d))
got = {}
for l in s15.splitlines():
    if l.startswith('| TGH'):
        c = cells(l); got[re.match(r'TGH-T\d-\d\d', c[0]).group(0)] = (c[1], c[2])
check(set(got) == set(want) and all(got[i] == (want[i], i[4:6]) for i in want), 'table 1.5 lists exactly the %d items whose drafts named another tier than the assigned one, with the tiers named and the assigned tier as derived' % len(want))
m = re.search(r'(\d+) of (\d+) items had layer drafts naming more than one tier; (\d+) further item', s15)
nm = sum(1 for i in IT if len({src_tier[r] for r in IT[i]['rows']}) > 1)
check(bool(m) and [int(x) for x in m.groups()] == [nm, N, len(want) - nm], 'section 1.5 sentence: %d of %d items named more than one tier, %d further item assigned another tier' % (nm, N, len(want) - nm))
s4 = doc[doc.index('## 4. Observations'):doc.index('## 5. Second-round')]
m = re.search(r'New-to-register items\*\* \((\d+)\): (.*?)\. E2 needs', s4, re.S)
check(bool(m) and int(m.group(1)) == len(newi) and sorted(re.findall(r'TGH-T\d-\d\d', m.group(2))) == sorted(newi), 'section 4 new-to-register list = the %d items with status new' % len(newi))
print('SUMMARY %s (%d failed checks)' % ('PASS' if not fails else 'FAIL', len(fails)))
sys.exit(1 if fails else 0)
```
