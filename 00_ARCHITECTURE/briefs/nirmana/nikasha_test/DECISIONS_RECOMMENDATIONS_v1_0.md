---
artifact: NIKASHA_TEST_DECISIONS_RECOMMENDATIONS
canonical_id: NIKASHA_TEST_DECISIONS_RECOMMENDATIONS
version: "1.0"
status: DRAFT_FOR_REVIEW — Kimi reviews; the native finalizes; then the register, plan and decisions file are updated to match
produced_on: 2026-09-27
campaign_id: nikasha-test
responds_to: DECISIONS_FOR_THE_NATIVE.md (v1.0, six decisions, AWAITING_NATIVE)
authored_by: Claude session NIKASHA-VERIFY-20260927, at the native's request
decision_owner: Native
cross_campaign_evidence: >
  /Users/Dev/madhav-engine (branch campaign/nirmana-engine): engine/STATE.md v0.5, engine/DECISIONS_FOR_THE_NATIVE.md v1.3,
  engine/EVENTS.jsonl (B1 gate verdicts 2026-09-26T18:25Z and 19:05Z), commits f4a6f9541 (A2), 8edba0533 (A1), 551d5ecad (A3).
  196 commits ahead of origin/main; no PR; nothing merged or deployed.
changelog:
  - "1.0 (2026-09-27, pre-review correction): B1 row updated — B1 was committed (`17e5a1257`) after this draft was written; it was REJECT/in-flight at drafting time."
  - "1.0 (2026-09-27): first draft. Agrees with the campaign on D2, D3 and the shape of D5; disagrees on D1 (already done elsewhere), D4 (which namespace) and D6 (what NULL means after instrumentation). Every disagreement cites the evidence that produced it."
---

# Recommendations on the six decisions

Written for the Nikaṣa reviewer first, then the native. One section per decision. Each gives: what the
campaign recommended · what is recommended here · the evidence where they differ · a ruling the native
can adopt, strike or edit. Nothing in the register, plan or decisions file is changed by this document;
those edits follow finalization and are listed at the end as mechanical work.

The one finding that reshapes the set: **D1 asks for authorization of work that a second campaign has
already carried out.** The Nikaṣa campaign and the Nirmāṇa engine campaign ran the same day in
different worktrees and neither read the other's state. Three of D1's four rows are closed on the
engine branch with independent reviewer acceptance; the fourth is in flight. That collapses D1 into a
reconciliation, and it changes D6's answer, because the engine campaign measured what a NULL rate
means after instrumentation and the census's proposed rule would be wrong on the day it landed.

---

## D1 · Authorize orchestrator behaviour edits for R35–R38

**Campaign recommended:** authorize, as packets P1 (R34/R35, 7 h), P2 (R36, 4 h), P8 (R37/R38, 16 h).

**Recommended here: no new ruling — D1 is already authorized and largely executed.** The native
authorized the Nirmāṇa engine elevation campaign on 2026-09-26 with full autonomy and no human gates.
Its packets are D1's rows:

| Nikaṣa row | engine packet | state on `campaign/nirmana-engine` | independent gate | what landed / what did not |
|---|---|---|---|---|
| R34 rate + duration | **A1** | CLOSED, commit `8edba0533` | ACCEPT after two correction rounds | engine times the writer itself (monotonic clock), sole timing authority; migration 1094 adds the duration column. **Honest partial:** the legacy `ga_writers/_telemetry.py` path (8 `ga_*` call sites) still writes NULL — engine decision **D-1** |
| R35 error text on every failure | **A2** | CLOSED, commit `f4a6f9541` | ACCEPT on re-review | `terminalizeFailedRun.ts`, seven call sites routed through it; 295 of the 301 silent records were one already-computed message being dropped one statement later. Carried: A2b (`mark_asset_error` empty-exception) |
| R36 run-killer | **A3** | CLOSED, commit `551d5ecad` | ACCEPT after three rounds | validator reports every divergence, only the diverged asset fails, dependents block by cascade. **Fixes 2 of the 8 runs** (Family A). The other 6 (Family B) were dispatched with no manifest at all — carried as A3b |
| R38 cascade reporting | **B1** | CLOSED on branch, commit `17e5a1257` (after a REJECT at 19:05Z) | accepted after the rejected round | per its commit: 8 of 8 currently-blocked production assets now render `blocked`; 18 badges flip off green (13 → blocked, 4 pre-existing false-greens repaired, 1 timeout) |
| R37 crash / orphan / guardian | **C1** | not started | — | engine diagnostician: `guardian_cleanup` (310 records) and `manual reap` (77) have **zero source hits in this codebase** — an external process or operator SQL. C1 must not start by assuming the code is here |

**The finding the native should hear now, from B1's rejected round:** the reviewer ran the real
`deriveState` against the ten real production blocked assets. **Nine render `lit` (green), one
`dormant`, zero `blocked`, zero `error`. Seven of the nine are on the native's own chart.** The cockpit
today shows blocked assets as successes because the stats route never reads `last_error` — a
pre-existing defect worse than the one B1 set out to fix, found only because the gate refused the
packet twice. B1 has since fixed it on the engine branch (`17e5a1257`); it stays live in production until that branch is merged and deployed.

**What this means for the Nikaṣa plan:** P1 and P2 are redundant (already done); P8's R38 half is B1
and its R37 half is C1. ~27 h of proposed work is removed from the plan. The proof queries P1 named
(`rows_per_second IS NULL` falling below 268/268; empty `last_error` reaching 0 for post-build runs)
remain correct as the **merge-and-deploy acceptance** for the engine branch — they cannot pass today
because nothing from the engine branch is merged or deployed. Production still has NULL rates and
silent failures this morning.

**What genuinely still needs the native in this area** — the engine campaign's own two open decisions,
which D1 should be re-pointed at rather than duplicated:

- **Engine D-1 (legacy telemetry path).** Recommend **(b)**: wire the duration through the 8 `ga_*`
  call sites inside the asset campaign (it is writer editing, which the engine campaign may not do),
  and amend CLAUDE.md §N.2 in the same pass to say what is true today — the "orchestrator is the sole
  build-state writer" guarantee has a pre-existing breach. (c) retire-the-path is right in principle
  and wrong in timing while the asset contract is still moving.
- **Engine D-2 (analysis-receipt pins).** Recommend **(a)**: leave the three attributable red tests on
  the engine branch; the pins reference commits that exist in no branch here and L4/L5 have no pin at
  all, so re-pinning needs the workstream that owns the pins. (c) revert would re-break the CI gate
  that demanded the regeneration.

**Proposed ruling:**
> D1 is closed as ALREADY AUTHORIZED (engine campaign, 2026-09-26). R34/R35/R36 are re-owned to engine
> packets A1/A2/A3 with state `CLOSED_ON_BRANCH — pending merge`; R38 to B1 `CLOSED_ON_BRANCH — pending merge`; R37 to C1
> `OPEN`. P1 and P2 are withdrawn from the plan; P8 becomes "consume B1/C1". The freeze precondition
> "instrument the builder before the from-scratch run" is satisfied by **merging and deploying the
> engine branch and observing one instrumented build**, not by a ruling. Engine D-1 → option (b) in
> the asset campaign; engine D-2 → option (a). Governance row to add: a campaign checks
> CURRENT_STATE for concurrent campaigns on the same surface at session open.

---

## D2 · Reopen the sealed tiers for the clause-level batch

**Campaign recommended:** one bundled reopen per document, the register's per-row replacement text as
the agenda.

**Recommended here: agree, with three rules attached** so the reopen does not become a rewrite and does
not recreate cluster C7 on the way out.

First, the honest size. C7 is 16 rows, but only some of them touch a sealed document; the rest are
editable today with no ruling:

| document | rows needing a reopen | rows editable without one |
|---|---|---|
| Tier 1 (product definition) | R72 (phantom review-record pointer), R76 (field rename) | — |
| Tier 2 (data plane) | R73, R75 (frontmatter counts), **R85 (D5 — the necessity table)** | — |
| Tier 3 (layer template) | R65, R67 (eight→nine), R68 (verdict spelling), **R71 (D3)**, R74 (ruling-11 clause), R08/R09 (carriage-check assignability) | — |
| Tier 4, L0 instance, pilots, tracker | — | R63, R64, R66, R69, R70, R77 (and R82, done) |

So it is three reopen rulings covering roughly a dozen clause-level edits, and D3 and D5 both land
inside them — neither needs a ruling of its own beyond being named on the agenda.

**The three rules:**
1. **Closed agenda.** The reopen edits exactly the rows named. Anything discovered mid-edit goes to the
   register as a new row and waits for the next reopen. This is what keeps a reopen a repair.
2. **Re-render pass before re-seal.** The campaign's own diagnosis is that C7 exists because ruling 17
   changed prose "without a re-render pass" — nine gates in one place, eight in four others. After each
   reopen, grep every count, gate name and section number the changed clauses touch, across all tiers,
   instances and the tracker, and fix the echoes in the same commit. This fixes the cause, not the rows.
3. **One version bump per document, in order T3 → T2 → T1.** T3 first because it holds the only
   BLOCKS_FREEZE row (R71) and the most edits; T2 next because D5 lands there; T1 last and smallest.

**Proposed ruling:**
> Three bundled reopens are authorized — T3 (R65, R67, R68, R71, R74, R08, R09), T2 (R73, R75, R85),
> T1 (R72, R76) — each with a closed agenda, a re-render pass before re-seal, and one version bump. The
> six non-sealed rows (R63, R64, R66, R69, R70, R77) proceed now without a ruling.

---

## D3 · Resolve the [TRANSFERS] contradiction (R71)

**Campaign recommended:** reword tier-3 §5.4 test 4.

**Recommended here: agree.** The contradiction is real and verified against the text: tier-2 §1 (:83–85)
says a [TRANSFERS] obligation "is not a data-plane layer's to build alone, and a layer plan does not
inherit it as its own work"; tier-2 §12.2 (:614) marks Presentation parity [TRANSFERS]; tier-3 §5.4
test 4 (:628) then requires "Presentation parity holds for the layer's served surface" as an acceptance
test. Three layers hit it (R94, R119, R140, R185). Un-marking it in tier 2 instead would hand every
layer an acceptance test against a plane that does not exist — a test that can only fail or be faked.

**Proposed replacement text for tier-3 §5.4 test 4:**
> 4. **Presentation parity** — run only where the layer's served surface exists in a built plane. Where
> the owning plane (retrieval, conversation) is not built, the instance records `[TRANSFERS]-pending`
> with the obligation named — never a pass, never a block, never an invented verdict.

**One addition:** tier-2 §12.2 also marks **Delivery sentinel** [TRANSFERS] (:621). The T3 reopen should
check every §5.4 test against every [TRANSFERS] row in §12.2 and apply the same wording wherever the
same collision exists, so this is fixed as a class and not as one row.

---

## D4 · Choose the ledger namespace (R78–R81)

**Campaign recommended:** option (a) — hand-style ids (`<asset>-G<nn>`) are the single namespace; the
census stops writing rows and becomes a detector reference that attaches measurements by a substance
key, with an alias table (`Vocab.rule1.alias` ≡ `Vocab.alias`, `Dens.density_contract` ≡ `Dens.served`,
`Carr.D1|D2|D3` ≡ `Carr.detector`, `Completeness.*` ≡ `Complete.*`).

**Recommended here: option (d) — the census's criterion-keyed ids are the single namespace for
gap rows; hand-written rows conform to it.** Not (a), for three reasons, each from the system's own
doctrine:

1. **A gap is defined by (asset, criterion) — that is already the census id.** `bg_ontology-Earn.build_record`
   says what is measured; `bg_ontology-G02` says only that it was the second thing a brief author wrote
   down. The deterministic id is the one that can be re-measured. Making the sequential id the key and
   then maintaining an alias table to find the criterion behind it is building the census id back by
   hand.
2. **The alias table exists only because hand rows spelled criteria loosely.** The fix for loose
   spelling is a closed vocabulary — exactly what the system already does for verdicts (`PASS · FAIL ·
   PARTIAL · NO_DETECTOR · N/A`). A brief author picks the criterion from the census's list; if the gap
   they found has no criterion yet, they add one line to the census's criterion list (`<Gate>.<check>`),
   with or without a detector. A criterion with no detector reads `NO_DETECTOR` on every census run
   until someone writes one — which is the honest state and a visible "detector wanted" item, instead
   of a hand row nothing re-measures.
3. **The census must stay a writer, or the closure loop has no author.** Test T3 ("a fix closes a row")
   fails in production tooling today (R57/R58) precisely because `emit_gaps` skips existing ids and
   never re-emits. The sandbox port that proves T3 re-emits the row with the new verdict. Under (a) the
   census "stops being a writer" — then nothing flips a row to CLOSED without a human, and §N.8
   (a status needs a detector that could return false) is violated by the ledger's own state field.

**What stays from the campaign's proposal:** the `superseded_by` field (R80) is needed under (d) too;
the fold of the 11 measured pairs (R81) is the same mechanical work, in the other direction — the hand
row's richer `change`/`owner` text is carried onto the census id, the hand id is WITHDRAWN with
`superseded_by`, and the ledger stays append-only. Opportunities keep hand ids (`<asset>-O<n>`) because
the census never emits them (R26); layer-scope rows keep `_layer_all-BT<nn>`.

**Cost:** the same ~4 h the campaign priced for R81; the five pilot briefs re-key their G-rows once; no
alias table, ever. The one thing lost is the per-brief G-counter, which carried no information.

**Proposed ruling:**
> Gap-kind rows use the census id `<asset>-<Gate>.<check>` as the single namespace; hand-written gap
> rows must use it, choosing the criterion from the census list or adding a declared criterion to it.
> Opportunity and layer-scope rows keep their hand idioms. The census re-emits a row when its verdict
> changes (the R57/R58 port) and never overwrites hand-written `change` text. `superseded_by` is added
> (R80); the 11 pairs are folded onto the census ids (R81, reversed direction); R79's alias table is
> withdrawn.

---

## D5 · Who authors the P-need / V-journey → layer necessity mapping (R85)

**Campaign recommended:** the native authors the necessity column; the semantics "necessary — not
involved in, not contributes to" stand.

**Recommended here: the judgement is the native's — agreed — but the mechanics are wrong.** Asking the
native to author 37 needs × 6 layers from a blank page is a 222-cell matrix and twelve hours. The right
split is **the session drafts, the native ratifies by exception**:

- **The draft is derivable to a first pass.** Tier-2 §3.1's "the question it owns" column is already a
  necessity statement per layer (L1 "what is actually calculated", L3 "which structures are engaged,
  when", L5 "what withstands challenge"). Each P/V need maps to the layer whose question it cannot be
  answered without, with one line of reason per cell. That draft is measurable against the parent text.
- **The native strikes and adds.** That is an hour's read, and the result is the native's decision, not
  a derived table with a signature on it.
- **Where it lives:** a new **tier-2 §3.2 "Necessity — P/V × layer"**, not a fifth column on §3.1 and
  not tier 1 (tier 1 owns the needs; the data plane owns the layer decomposition). It lands inside the
  T2 reopen (D2).
- **Semantics stand.** "Necessary" is what makes tier-3 §0.1 falsifiable by ablation. Involvement lists
  are what the 130 invented rows already are; necessity sets are smaller and sharper, and a layer
  instance then narrows from the table and never invents.
- **One row the campaign's framing misses — synergy.** Some needs are necessary to no single layer but
  to a pair: P12 ("which events fit this interpretation") needs L3 *and* L5 together; P09 ("does this
  yoga form, and when") needs L1 *and* L3. Tier-2 §3.5 already names the layer-synergy term at the
  native's instruction. The table should carry a row per adjacent pair so that necessity-to-the-pair is
  recordable rather than forced onto one layer or dropped.

This is the largest single lever in the register: cluster C8 (~150 rows) collapses onto ~20 primaries,
and R85 is the biggest of them.

**Proposed ruling:**
> The session drafts tier-2 §3.2 (P01–P24, V01–V13 × L0–L5, plus one row per adjacent layer pair) with a
> one-line reason per "necessary" cell, derived from §3.1's owned questions. The native ratifies by
> exception inside the T2 reopen. Tier-3 §0.1's necessity semantics stand unchanged.

---

## D6 · Align the Earn/Cost verdict scale with tier 4 (R55)

**Campaign recommended:** the census reads a NULL rate as PARTIAL ("not instrumented — R34 pending")
until R34 lands, then FAIL; and collapse `Earn.build_record` / `Cost.baseline` into one row since they
read one column and cannot disagree.

**Recommended here: grade NULL by its cause, and do not collapse the two gates.** Both halves of the
campaign's proposal are correct about today and wrong about the day A1 merges — and A1 is already
written. The engine campaign's A1 review enumerated every path that leaves `rows_per_second` NULL
*after* instrumentation (engine D-1, "the residual NULL paths"):

| why the rate is NULL | how common | honest verdict |
|---|---|---|
| `_skip_no_delta` — healthy skip, nothing ran | common steady state on every rebuild | **N/A** |
| `_mark_probe_green` — the writer never runs | common steady state | **N/A** |
| health-probe service asset (8 `storage_type='service'`) | always | **N/A** |
| fully-resumed writer, duration sums to 0 | occasional | **N/A** |
| environment lacks the duration column (migration 1094 not applied) | environment-wide when it bites | **NO_DETECTOR** |
| legacy `_telemetry` path — 8 `ga_*` call sites | until engine D-1 (b) lands | **FAIL** — the one real defect |
| **today, before merge: nothing writes the column at all** | 268 / 268 | **NO_DETECTOR** — not PARTIAL |

"FAIL when NULL after R34" would fail every skipped asset on every rebuild of a built chart — a FAIL
with no defect behind it, which is §N.8's defect class in reverse. And PARTIAL is the wrong word for
today: nothing was partly measured; the instrument does not exist yet. `NO_DETECTOR` is what the
vocabulary already provides for that.

**Why not collapse Earn and Cost:** they are one detector today only because the census reads one
column. After A1, they diverge on purpose: **Earn.build_record** asks "did the engine record this build"
and reads `duration_seconds` + `last_built_at`; **Cost.baseline** asks "is there a rate to judge
improvement against" and reads `rows_per_second`, definable only when `rows_written > 0`. A writer that
legitimately writes zero rows is Earn PASS, Cost N/A. Collapsing them would throw away exactly the
distinction A1 just created. R55 is resolved by re-keying Earn, not by merging the rows.

**Proposed ruling:**
> The census grades a NULL rate by cause: N/A for skip / probe-green / service / fully-resumed; NO_DETECTOR
> where the duration column is absent or, as today, where nothing writes the column; FAIL only where a
> writer ran and no rate was recorded. `Earn.build_record` is re-keyed to `duration_seconds` +
> `last_built_at`; `Cost.baseline` stays on `rows_per_second` gated by `rows_written > 0`. The two are
> not collapsed. This lands in the census before the engine branch merges, so the first instrumented
> build is graded correctly on day one.

---

## Summary

| D | campaign | recommended here | agree? |
|---|---|---|---|
| D1 | authorize R35–R38 as P1/P2/P8 | already authorized and executed by the engine campaign; re-point at engine D-1 (b) and D-2 (a); merge-and-deploy is the real precondition | **no — redundant** |
| D2 | one bundled reopen per document | same, with closed agenda · re-render pass · T3→T2→T1 order | yes, sharpened |
| D3 | reword T3 §5.4 test 4 | same text, applied as a class across all [TRANSFERS] rows | yes, widened |
| D4 | hand ids as namespace, census becomes reference | census criterion ids as namespace, census stays the writer, no alias table | **no** |
| D5 | native authors the necessity column | session drafts, native ratifies by exception; new T2 §3.2; add layer-pair rows | shape yes, mechanics no |
| D6 | NULL = PARTIAL until R34, then FAIL; collapse Earn/Cost | NULL graded by cause; NO_DETECTOR today; Earn re-keyed to duration; not collapsed | **no** |

## Mechanical work after finalization (not done here)

- Register: re-own R34/R35/R36/R37/R38 to engine packets with the states above; withdraw R79; add the
  concurrent-campaign governance row; mark D3/D5 rows as landing inside the D2 reopens.
- Plan: withdraw P1, P2; rewrite P8 as "consume engine B1/C1"; add the D6 census change to P4; add the
  D5 draft to P9.
- DECISIONS_FOR_THE_NATIVE.md: status → RULED, with the adopted text per decision.
- Engine campaign: D-1 (b) and D-2 (a) recorded in `engine/DECISIONS_FOR_THE_NATIVE.md`; B1 resumes
  from its rejected round with the cockpit-green finding as a named in-scope defect.
