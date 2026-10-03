---
artifact: SUVARNA_REOPEN_AGENDA_T1
canonical_id: SUVARNA_REOPEN_AGENDA_T1
version: "1.1"
status: DRAFT-HELD-FOR-J1
produced_on: 2026-10-02
produced_in: "Exec Suvarna Engine, Track E lane E2 (queue id E2.1-design-001); drafted by a Sonnet drafter"
tier: 1
tier_document: "00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md (SEALED 2026-09-25)"
rows: 3
row_ids: [R01, R72, R76]
verdict_changing_rows: []
decision: "N-4.T1, Strategic Suvarṇa (plan §4.2 J1 rows 4 and 7), decided together with the T2 and T3 agendas"
sources:
  - "TRACK_E_BRIEF_v1_0.md §6 (the spec); SUVARNA_CAMPAIGN_PLAN_v1_5.md §4.2 (J1 rows 4 and 7), §5.1 (E2)"
  - "nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md D2 (ruling 2026-09-27) and D3"
  - "NIKASHA_CHANGE_REGISTER_v2_0.md (v2.8), rows R01, R72, R76"
  - "the tier-1 document at origin/campaign/nikasha-test @ 2a78ec64d"
changelog:
  - "1.1 (2026-10-02): SS rulings folded, each marked as SS direction to be confirmed at J1: new sections Rows that change what counts as PASS (T1: none; grid movement 0) and Decisions required at J1; R72 seal-basis direction recorded (N-5.T1 covers all of T1; the review file exists on no ref). Appendix A updated: the plan model now reads 31."
  - "1.0 (2026-10-02): first issue. Three rows, one section each; drafted replacement text; no tier document edited. Appendix A reconciles the plan's 32 clause fixes with the Track E brief's 31 for all three agendas."
---

# Reopen agenda — Tier 1 (product definition) — v1.0 DRAFT, held for J1

**Purpose.** The D2 ruling of 2026-09-27 authorised one bundled reopen per sealed founding document, each on a reviewed row-to-clause agenda that names, for every row, the exact clause, the remedy chosen, and the replacement text. This is the agenda for Tier 1, `MADHAV_PRODUCT_DEFINITION_FINAL.md`. It holds **3 rows**: R01 (P23/P24 order), R72 (a `review_record` pointer to a file that does not exist) and R76 (one field rename and one glossary line). None of them changes an obligation, a contract, a count or a scope, so none is VERDICT-CHANGING; R72 carries a seal-basis question the strategist should read first. The agenda is closed once opened (D2 rule 1). The tier document is edited only after N-4.T1, only on a lane branch, and re-sealed first of the three (D2 rule 3).

Line numbers below are those of the blobs at `origin/campaign/nikasha-test` @ `2a78ec64d`; every quotation was copied from its source by script and verified against it.

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

| Row | Clause (location) | Remedy | Risk class |
|---|---|---|---|
| R01 | T1 §2 needs table, `P24` row :178 printed before `P23` row :179 | Swap the two rows so P23 precedes P24; no text change | wording-only |
| R72 | T1 frontmatter `review_record` :24 (echo: `seal.review_backing` :22) names `briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md`, which exists nowhere | Correct the pointer to an honest "not located" record (restoring is impossible); the N-5.T1 review is recorded there once it exists. **Seal-basis question for SS** | wording-only |
| R76 | T1 frontmatter `review_record` :24 (field name); no glossary section exists | Rename the field to `document_reviews`; one glossary line as a new last bullet of §16 | wording-only |

Not on this agenda for T1: nothing is deferred and nothing in T1 is in the D2 "proceed now" list.

## Rows that change what counts as PASS

*SS direction, to be confirmed at J1.* This section holds the VERDICT-CHANGING rows of Tier 1, one block per row: the wording before and after, and which cells of the 9 × 127 grid would move. 

**Tier 1 has no VERDICT-CHANGING row.** R01 (order), R72 (a pointer) and R76 (a field name and a glossary line) change no gate, obligation, test or verdict. **Grid cells that move: 0.** R72 carries a seal-basis decision, recorded below under "Decisions required at J1".


## Decisions required at J1

*SS direction, to be confirmed at J1.* One table; each row states the options and the drafter's recommendation.

| Row | Decision | Options | Recommendation |
|---|---|---|---|
| R72 | What the T1 seal rests on, given the review file is lost | (a) accept the changelog's record and apply the not-located correction only; (b) as (a), and require the N-5.T1 independent review to cover all of T1 FINAL, not only the three changed clauses | **(b)** — SS direction: accepted; the N-5.T1 review covers all of T1 |
| R72 | The seal record `ELEVATION_CHAIN_SEAL_2026-09-25_v1_0.md` lines 40–43 repeat the lost review's path and counts | edit them, or annotate them | Annotate (a seal record is history); same commit as the T1 redline |
| R76 | Does the glossary line also name the fifth field, `independent_review:` (T3 :32, T4 :31)? | four names (as the register), five names | Four names now; add the fifth in round two if SS wants it |

## R01 — P24 printed before P23 in the §2 needs table

**Risk class:** wording-only.

**Register row.**

> P24 printed before P23 in the §2 needs table
>
> **State in register:** OPEN — T1 reopen agenda (D2 ruling 2026-09-27)
> — REG R01 :116 (severity COSMETIC)

**Clause as it stands.**

> | P24 | "What is happening to me right now, and why does this period feel the way it does?" | The present-tense need: which mechanisms are active now, what they are doing, and how the current interval differs from the one before it. Neither a forecast nor a history. |
> | P23 | "What does the tradition say about lifespan?" | Āyurdāya as the classical discipline it is: the applicable method, its inputs, the schools' disagreement, the cancellations and the genuine uncertainty. Presented as the tradition's computation and its limits, never as a bare date. |
> — T1 :178–179

The frontmatter explains why P24 sits where it does (it was appended at FINAL as a new need):

> P24 at FINAL is a NEW need (present-tense), appended rather than renumbered.
> — T1 :25

**Remedy chosen by D2.**

> R01 (§2 P23/P24 order)
> — D2 :118 (the ruling names the row and the clause; the register gives the cosmetic fault only)

Chosen here: reorder, because the identifiers are cited by number everywhere and a table whose rows run P22, P24, P23 invites exactly the transposition the register records. The note at :25 says P24 was *appended*; in numeric order that means after P23.

**Drafted replacement text** (the two table rows, in the order P23 then P24, text unchanged):

~~~~
| P23 | "What does the tradition say about lifespan?" | Āyurdāya as the classical discipline it is: the applicable method, its inputs, the schools' disagreement, the cancellations and the genuine uncertainty. Presented as the tradition's computation and its limits, never as a bare date. |
| P24 | "What is happening to me right now, and why does this period feel the way it does?" | The present-tense need: which mechanisms are active now, what they are doing, and how the current interval differs from the one before it. Neither a forecast nor a history. |
~~~~

**Cross-tier re-render hazards.** None by number: T2 §2 cites P-needs by identifier (V12 → P23, V13 → P24, T2 :128–129) and its V-table is already in order; T3 §0.1 and T4 §0.1 cite identifiers, not order. Grep `P23` and `P24` across tiers, the L0 instance and the tracker before re-sealing and confirm no list depends on row order.

**Open questions.** None.

## R72 — `review_record` points to a file that does not exist

**Risk class:** wording-only. **Strategist attention: seal basis** (below).

**Register row.**

> T1 frontmatter `review_record: briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md` — the file does not exist anywhere; "11 MAJOR + 14 MINOR, all folded" unverifiable. Locate/restore or correct the pointer
>
> **State in register:** OPEN — T1 reopen agenda (D2 ruling 2026-09-27)
> — REG R72 :199 (severity DEGRADES)

**Clause as it stands** (the pointer, its echo in the seal block, and the changelog entry that names the file):

> review_record: briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md  # verdict ACCEPT, 11 MAJOR + 14 MINOR, all folded
> — T1 :24

> review_backing: "briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md — verdict ACCEPT, 11 MAJOR + 14 MINOR folded;
> — T1 :22

> "FINAL (2026-09-24): review REVIEW_PRODUCT_DEFINITION_v3_1.md returned ACCEPT with 11 MAJOR and 14 MINOR findings; all folded.
> — T1 :34

**Evidence that the file cannot be restored.** `git ls-tree -r --name-only origin/campaign/nikasha-test | grep -i REVIEW_PRODUCT_DEFINITION` and the same on `origin/main` return nothing (checked 2026-10-02), and a path search over every ref in the repository (`git log --all -- '*REVIEW_PRODUCT_DEFINITION*'`, 3,906 refs) finds no commit that ever touched such a file: it exists on no branch. The directory that should hold it contains only:

~~~~
00_ARCHITECTURE/briefs/reviews/KIMI_K3_PACKET_LAYER_TEMPLATE_v1_0.md
00_ARCHITECTURE/briefs/reviews/KIMI_K3_REVIEW_LAYER_TEMPLATE_v1_0.md
00_ARCHITECTURE/briefs/reviews/REVIEW_DATA_PLANE_FINAL_v1_0.md
00_ARCHITECTURE/briefs/reviews/REVIEW_DATA_PLANE_v3_0.md
00_ARCHITECTURE/briefs/reviews/REVIEW_L0_STRATEGY_v2_0.md
00_ARCHITECTURE/briefs/reviews/REVIEW_NIKASHA_DECISIONS_RECOMMENDATIONS_v1_0.md
~~~~

The same finding is recorded by the Nikaṣa T5 consistency check:

> - `find . -name "REVIEW_PRODUCT_DEFINITION*"` returns nothing; `00_ARCHITECTURE/briefs/reviews/` contains only KIMI_K3_*, REVIEW_DATA_PLANE_*, REVIEW_L0_STRATEGY_v2_0.md. "11 MAJOR + 14 MINOR" is NOT_MEASURED — needs the missing review file.
> — T5V :85

The seal record repeats the claim and is therefore a second echo (it states that the tier-1 seal rests on this review):

> ## The review each seal rests on
>
> Ruling 9 requires that a review happened, not that a particular party signs. For each:
>
> - **Tier 1** — `briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md`, verdict ACCEPT, 11 MAJOR + 14 MINOR
>   folded. Its two 2026-09-25 elevations (the three planes and the compositional identity in §1.3; the
>   Domain correctness obligation in §14, now carrying the owner that decision 11 gave it) are
>   native-directed content recorded in its own changelog.
> — SEAL :36–43

**Remedy chosen by D2.** D2 names the row only ("R72 (`review_record` pointer)", D2 :118) and does not choose between the register's two remedies, "Locate/restore or correct the pointer" (R72). The agenda must choose. **Chosen here: correct the pointer.** Restoration is not available (above), and inventing a replacement file or re-deriving "11 MAJOR + 14 MINOR" would be a fabricated record (B.10). The pointer becomes an honest not-located record that keeps the claim's provenance (the 2026-09-24 changelog entry) and says it cannot be re-verified. The independent review that D2 rule 4 requires before the T1 re-seal is then recorded in the same field, which also gives the seal a review file that exists.

**Drafted replacement text.** Line :24 (combined with R76's rename, so the field name changes once), and the first clause of :22:

~~~~yaml
document_reviews: []   # independent reviews OF this document (T2's field name; see the glossary line in §16)
# NOT LOCATED: briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md does not exist in the repository (checked on
# origin/campaign/nikasha-test and origin/main, 2026-10-02; register R72). "ACCEPT, 11 MAJOR + 14 MINOR, all folded"
# is carried from this document's own 2026-09-24 changelog entry and cannot be re-verified. The independent review
# of this reopen (N-5.T1) is listed here, by path, when it exists.
~~~~

Line :22, first clause only (the rest of the line is unchanged):

~~~~
old: review_backing: "briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md — verdict ACCEPT, 11 MAJOR + 14 MINOR folded;
new: review_backing: "the review recorded in this document's 2026-09-24 changelog entry (its file, briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md, is not located — see document_reviews) — verdict ACCEPT, 11 MAJOR + 14 MINOR folded as recorded there;
~~~~

The changelog entry at :34 is history and is left as written; a dated correction note is added to the T1 reopen changelog entry instead (T2 set the precedent at its changelog :45, "CORRECTED 2026-09-25: this entry originally claimed…").

**Cross-tier re-render hazards.**

- `00_ARCHITECTURE/briefs/nirmana/ELEVATION_CHAIN_SEAL_2026-09-25_v1_0.md` lines 40–43 repeat the path and the counts (quoted above); correct or annotate in the same commit, SS to say which (it is a seal record, not a tier).
- `NIKASHA_CHANGE_REGISTER_v2_0.md` R72 closes with this row; `PHASE6_ANALYSIS.md` row 7 and `NIKASHA_TEST_CAMPAIGN_REPORT_v1_0.md` :250 describe the defect and need no edit.
- No tool reads the key: `git grep review_record` over `platform/` and `00_ARCHITECTURE/control/` on `origin/campaign/nikasha-test` returns nothing.

**Open questions.** None open: the seal-basis question is settled by SS direction (below) and the remaining item is in "Decisions required at J1".

**SS direction, to be confirmed at J1: accepted.** Option (b): the pointer is corrected as drafted above, and the N-5.T1 independent review covers all of T1 FINAL, so the seal acquires a review file that exists. The earlier file, `REVIEW_PRODUCT_DEFINITION_v3_1.md`, exists on no branch (path search above), so nothing is restored and no replacement is invented.

## R76 — "Review record" names four different artefact patterns across tiers

**Risk class:** wording-only.

**Register row.**

> "Review record" names four different artefact patterns across tiers (`review_record` T1 / `source_review_record` + `document_reviews` + `review_backing` T2 / `*_VALIDATION_AND_REVIEW_RECORD` layer instances). Rename T1's field to `document_reviews` and add one glossary line fixing the four names
>
> **State in register:** OPEN — T1 reopen agenda (D2 ruling 2026-09-27); T1 has no glossary section — the agenda names where the line lands
> — REG R76 :203 (severity DEGRADES)

**Clause as it stands.** The field name (:24, quoted under R72) and, for the glossary, the absence of any glossary section in T1: its headings are §1–§16 and none is a glossary (`grep -n -i glossary` over the file returns nothing). §16 is the last section:

> ## 16. How this master governs subsequent work
>
> The sequence is:
> — T1 :637–639

> - **Execute with velocity: one record, not parallel ledgers.** Reuse working data, code, contracts and
>   tests; automate mechanical checks; keep one source of truth per thing. Two registries that disagree
>   are worse than one that is incomplete.
> — T1 :652–654

The other three patterns, as they stand in T2's frontmatter and in the layer-instance file names:

> review_backing: "reviews/REVIEW_DATA_PLANE_FINAL_v1_0.md — verdict REJECT on the version reviewed;
> — T2 :22

> source_review_record: MADHAV_DATA_PLANE_V2_REVIEW_RECORD_v1_0.md
> — T2 :35

> document_reviews:
> — T2 :36

**Remedy chosen by D2.**

> - **T1** (product definition): R01 (§2 P23/P24 order), R72 (`review_record` pointer), R76 (field
>   rename to `document_reviews` **and** one glossary line — T1 has no glossary section, so the
>   agenda names where the line lands, recommended §16).
> — D2 :118–120

Chosen here: the field rename is exactly the register's (`review_record` → `document_reviews`, mirroring T2, whose own changelog records that split at :42 item (g), "`the review record` split into the source record and the document reviews"). The glossary line lands in **§16**, as D2 recommends, as a new last bullet of its list (before the closing "**The standard:**" paragraph, T1 :656), because §16 is the section that tells later work how this master is used and the line is a usage rule.

**Drafted replacement text.**

Frontmatter: the key `review_record:` becomes `document_reviews:` (the combined text for :24 is given under R72). New bullet, to be inserted after T1 :654 (the end of the "Execute with velocity" bullet):

~~~~
- **Review artefacts keep four distinct names.** `source_review_record` — the research record of what was inspected while a document was written (a source record, not a review of the document); `document_reviews` — independent reviews OF the document, each with its verdict; `review_backing` (inside `seal:`) — the seal's own statement of which review it rests on; `*_VALIDATION_AND_REVIEW_RECORD` — a layer's validation-and-review record (for example `MADHAV_DATA_PLANE_L0_VALIDATION_AND_REVIEW_RECORD_v1_0.md`). A bare "review record" names none of them, and the field `review_record` is retired.
~~~~

**Cross-tier re-render hazards.**
- T2 already uses `source_review_record`, `document_reviews` and `review_backing` with these meanings (T2 :22, :35, :36), so T2 needs no edit for R76. The line's definitions are copied from T2's own comments (:35 "the SOURCE research record"; :36 "independent reviews OF this document") and from the L0 record's frontmatter (`review_owner: independent read-only reviewer`, `implementation_commits`), which is how the fourth pattern was read.
- `MADHAV_PRODUCT_DEFINITION_v3_0.md` (SUPERSEDED) also has `review_record`; it is history and is not touched.
- No tool reads the key (see R72).

**Open questions.**
1. The T3 and T4 frontmatters use a fifth name, `independent_review:` (T3 :32, T4 :31), which the register's "four patterns" does not count. Decide whether the glossary line should name it (then it is "five names"); this draft follows the register and leaves it out.
2. The fourth definition ("a layer's validation-and-review record") is read from one file's frontmatter, not from a rule; the owner of the layer instances should confirm the wording.

## Appendix A — Row-count reconciliation: the plan's "32" against the brief's "31" (applies to all three agendas)

**Finding in one paragraph.** The three agendas together hold **31** rows (T1 3, T2 11, T3 12 plus 5 closing rows). The Track E brief's 31 is right and the plan's "32" is the stale figure. "32" first appears in the D2 ruling document's own summary ("32 named rows"), which was never updated and which equals the number of distinct register ids the ruling's three tier bullets *name* — the 31 agenda rows **plus R109**, whose registry-column half the ruling explicitly says is "P9 data work, not a reopen". The row the plan's 32 would include that the brief's list lacks is therefore **R109**, and it is correctly absent. (R85 is a second candidate after the 2026-09-27 revision: it is still named in the ruling, as withdrawn from T2, and is CLOSED in the register.) Strategic Suvarṇa has since corrected the plan model (E2.1 now reads 31, R109 named as data work); the plan documents (§3.6 line :205, E2 line :353) and the D2 summary lines still carry 32 and should be corrected, not the brief.

**Per-tier rows, as drafted in these three files.**

| Tier | Rows | Count |
|---|---|---|
| T1 | R01, R72, R76 | 3 |
| T2 | R06, R73, R75, R88, R89, R90, R91, R119 (T2 half), R181 / R186 / R198 (§7.1 halves) | 11 |
| T3 | R08, R09, R10, R65 (T3 half), R67, R68 (T3 half), R71, R74, R93, R120, R201, R221 | 12 |
| T3 (closing with them) | R94, R140, R185 (with R71) · R192, R208 (with R120) | 5 |
| **Total** | | **31** |
| Deferred, not agenda rows | R131, R210, R214 (listed in the T3 agenda) | — |

**Evidence 1 — where "32" is written.**

> about 32 clause fixes; Track E §6 lists 31, E2.1 reconciles
> — PLAN v1.5 :205

> reconciling 31 listed vs 32 ruled
> — PLAN v1.5 :353

> {"id": "E2.1", "track": "E", "lane": "E2 Clause fixes", "title": "31 clause fixes drafted per document (R109 is data work, not a reopen), held for the combined reopen", "depends_on": ["N-1"], "done_by": "event"},
> — plan_model.json :148 (as read 2026-10-02: corrected to 31 after this packet's reconciliation, commit d97e6bb65 "E2.1 is 31 clause fixes, not 32 (R109 is data work)"; it read "32 clause fixes drafted per document" before)

> **What changed from v1.0:** agenda 12 → 32 named rows plus three explicit deferrals; seal order
> reversed to parent-before-child; cross-surface rows split; alternative remedies chosen on the agenda.
> — D2 :156–157

> | D2 | three reopens, 12 ids, T3→T2→T1 | three reopens, 32 named rows + 3 explicit deferrals, remedies chosen on the agenda, seal T1→T2→T3 | corrected |
> — D2 :427

> 1. **Clause fixes** (D2 ruling, 32 rows). Stale counts, a missing review record, the [TRANSFERS] contradiction (R71), verdict spelling, the ruling-11 clause, and others. All already written.
> — PLAN v1.0 :336

**Evidence 2 — the figure was already flagged.**

>   R120, R201, R221; closing with them R94, R140, R185, R192, R208. R131, R210, R214 stay deferred. That is **31** rows
>   against the plan's figure of 32 (Astra F18): the packet reconciles the two and reports the count it finds, and SS
> — Track E brief :207–208

> | 27 | MINOR | plan §3.6 l.274, §5.1 E2 l.431, plan_model E2.1 vs Track E §6 l.134–138 | Plan: "32 clause fixes". Track E lists 3 (T1) + 11 (T2) + 12 (T3) + 5 closing rows = 31, and says "The packet reconciles this list against the plan's figure of 32". | Reconcile now: name the 32nd row, or change the plan to 31 and cite Track E §6. |
> — REVIEW_PASS2_CONSISTENCY_v1_0 :43

> | **F18** | **MINOR** | Track E §§6–7, 9; Runbook §2.6; Runtime §5; `S/SUVARNA_DOCUMENT_MAP_v1_0.md` §§1, 7–8; Register §1 | **Residual document drift remains.** E5 is 30–50 h in its heading but 40–65 h in the estimate; 31 listed clause fixes remain unreconciled with 32; 45 minutes is described as warning before a three-by-ten-minute threshold; the document map calls this rebuilt package stale. The inherited register freeze language is broader than the master checklist. | Reconcile the canonical counts and freeze rule, distinguish historical snapshots from current instructions, and generate operational summaries from the same machine-readable specification. |
> — ASTRA review :50

**Evidence 3 — recount from the ruling text.** The ruling's three tier bullets name these ids (script: split the D2 ruling at its `> - ` bullets, extract `R\d+`, count distinct):

~~~~
D2 as first issued (commit 9931dc9fe, 2026-09-27, v2.0):
  T1 3 ids · T2 13 ids · T3 17 ids
  distinct across the three bullets (R06 appears in T2 and, "with R06", in T3): 32
  of which R109 = named in the T2 bullet as "not a reopen"; R85 = on the T2 agenda
  => agenda rows = 31 (excluding R109)
D2 as it stands (v2.1, after the D5 revision: R85 withdrawn from T2, R221 added to T3):
  T1 3 ids · T2 13 ids · T3 18 ids
  distinct: 33; minus R109 (not a reopen) minus R85 (withdrawn) => agenda rows = 31
Neither version of the ruling changed the agenda count: v2.1 swapped R85 out and R221 in. The "32 named rows" text was written for v2.0 and not touched by the v2.1 revision.
~~~~

Cross-check against the register: rows whose *state* cell contains the word "reopen" number **33** — the 30 agenda rows other than R221 (R221's state says "on the D2 T3 agenda") plus the three deferred rows R131, R210, R214. Adding R221 gives 31 agenda rows.

**Which document is wrong.** The plan (v1.0 through v1.5), `plan_model.json` E2.1 (since corrected) and the Nikaṣa start prompt inherited "32" from the D2 summary line; the Track E brief counted the rows it lists. The brief is right. Note also that the D2 ruling's own summary lines (D2 :156 and :427) are stale for the same reason and should be corrected when the register is next folded.

**A related gap the reconciliation exposed (SS to decide, not drafted here).** D2 closes the per-layer confirmation rows of exactly two clause families with their parent (R94, R140, R185 with R71; R192, R208 with R120). The register carries many more per-layer "confirmed on L1–L5" rows whose dependency column points at an agenda row but whose state is a bare OPEN and which D2 does not mention: with R09 — R92, R112, R144, R159, R174, R190, R204; with R06 — R95, R103, R136, R205; with R88 — R107, R138, R150, R165, R191, R199; with R89 — R108, R139, R151, R166, R184, R200; with R90 — R98, R110, R142, R187, R202; with R91 — R111, R143, R189, R203; with R93 — R115, R116, R147, R155, R170, R191, R207. (Found by script: register rows whose dependency column names an agenda row and which are not themselves on an agenda or in a tier-4/inspector section; the list is indicative, not audited, and R209 depends on several of these parents.) They are not agenda rows and do not change the 31, but J1's `register_freeze_clean` watches only R24, R34, R36, R39, R71 and R244, so they will not block a freeze; whether they close with their parent or stay for round two is the strategist's call.


## Re-seal mechanics (apply once, after the agenda is decided)

- **Order and gates (D2 rule 3, rule 4).** Re-seal parent-before-child: T1, then T2, then T3. One version bump per document, after its cross-tier re-render pass and an independent review (Astra or Kimi K3). The documents carry `version: "FINAL"`, so the "bump" is a dated changelog entry in the convention the two earlier reopens used (T2 changelog :40 and T3 changelog :37, "REOPENED AND AMENDED (date, native ruling — …)"), plus a restamp of the document's fingerprint in `CAPABILITY_MANIFEST.json` (the identity of record, T3 frontmatter :8).
- **Closed agenda (D2 rule 1).** Anything found while editing becomes a new register row for a second round; it is not added here.
- **Re-render pass (D2 rule 2).** Every count, gate name and section number named under "cross-tier re-render hazards" below is grepped across tiers, the L0 and L1 instances, the tracker and the census in the same commit as the redline. The L0 instance (v3.0) and the five pilot briefs are test artefacts that the register says are regenerated after the freeze (REG frontmatter `what_is_a_test_artefact`), so their echoes are listed for completeness, not as blockers.
- **Nothing here edits a tier document.** This file is a draft held for J1 (plan §4.2 rows 4 and 7); the tier documents are redlined only after the strategist's N-4 decision on this agenda.
