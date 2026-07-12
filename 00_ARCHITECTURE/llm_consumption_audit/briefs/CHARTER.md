---
title: LLM Consumption Audit — Master Charter
canonical_id: LLM_CONSUMPTION_AUDIT_CHARTER
version: 1.1
status: RATIFIED (Section 7 rubrics ratified by Cowork review gate — see GATE_RATIFICATION_v1_0.md v1.1, §1). Ratified 2026-07-12 by Fable 5 (Cowork) + native (Abhisek Mohanty).
source_plan: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md
generated_by: Brief Foundry session, 2026-07-11
---

# LLM Consumption Audit — Master Charter

This charter is referenced by name by every child lane brief. It transcribes, verbatim
(anti-softening discipline — this is a graded document, not a summary), the governing
sections of `LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md`: doctrine (§2/§2.1), the 9-class failure
taxonomy (§4), the finding schema (§6), the satisfaction criteria (§8), the RESUME protocol
(derived from §12 items 3-4), the execution DAG (§12.7, verbatim), and the DRAFT judgment
rubrics gated on Cowork review.

Every child brief MUST cite this charter by name and MUST NOT restate or paraphrase these
sections — reference them, do not duplicate them with drift risk.

---

## 1 — Doctrine (plan §2 + §2.1, verbatim)

### §2 — Audit doctrine (the constitution)

A **gap** is anything that prevents the consuming LLM from receiving **correct, complete,
consistent, usable, and proportionate** evidence over the wire. Data that exists but does
not arrive is absent. Data that arrives wrong, or twice contradicting itself, or as 300
unranked duplicates, or as raw IDs with no text, or as an un-budgeted 181KB dump, is a gap
of equal standing.

**Completeness has two axes (native directive):**
- **Width** — the span of data points relevant to a question. If ~20 relevant data points
  exist that the LLM never receives, the audit must find each and root-cause WHY it is not
  received.
- **Depth** — the full dossier of any entity that enters a synthesis (the Mercury
  standard, §5 Lane 8): strength, avastha, yoga/dosha membership, dispositor chain,
  varga-wise placement, temporal presence (MD/AD/PD), structural×temporal convergence
  past/near-future, bhava-sandhi/cusp flavor, combustion, and every other facet the system
  holds. Considering Mercury without its dossier is not synthesis.

### §2.1 — Examples are illustrative, never limiting (native directive, review round 1)

Every example given in this plan — the Mercury facet list, the "~20 missing data points",
the draft question themes — is ILLUSTRATIVE. The audit derives the full factor space from
three closed-loop sources and must never treat a native-supplied example list as the
boundary: (1) the classical canon (shastra concept inventory — every concept an acharya
could weigh, whether or not the system implements it); (2) the system's own asset
inventory (every asset × every fact_category × every value each asset emits, enumerated
from the DB and CAPABILITY_MANIFEST, not from memory); (3) the L2/L3 derived surfaces
(signals, graph, convergence, windows). Where (1) exceeds (2), that delta is itself a
finding (UNREACHABLE-by-nonexistence). Where (2) exceeds what any tool serves, that is
UNREACHABLE. The completeness test is against the union, never against the examples.

---

## 2 — 9-class failure taxonomy (plan §4, verbatim)

### §4 — Failure-class taxonomy (every finding gets exactly one primary class)

1. **UNREACHABLE** — exists in a table, no tool serves it (KP-3, mrityu-bhaga R-47 class).
2. **WRONG** — value served ≠ L1 truth (R-43 dignity class).
3. **INCONSISTENT** — two tools serve the same quantity differently (D-1/G-7/R-43 class).
4. **EMPTY SHELL** — tool advertises an analysis stage that returns nothing (R-39/R-40/R-45 class).
5. **DISHONEST SELF-DESCRIPTION** — receipts/counters/flags contradict the payload (R-38/R-41 class).
6. **UNUSABLE FORM** — arrives but cannot be synthesized: IDs without text, truncated narration, un-budgeted dumps (R-40/R-30/R-44c class).
7. **DROWNED** — correct data buried under duplication walls or trivia ranked as chart-defining (R-37/R-44a/b class).
8. **UN-SYNTHESIZABLE AT SCALE** — the question needs N-hundred factors and no path composes them (R-48/C-6 class).
9. **UNGOVERNED JUDGMENT** — the executor LLM had to improvise where the system should have governed: method/krama choice, evidence adjudication, question decomposition, taxonomy→life-language translation (§10 gaps 1/3/9/10). Logged every single time it happens; these findings are the requirements spec for the doctrine/method layers.

Class determines suspected remediation layer — that is what makes the report plannable.

---

## 3 — Finding schema (plan §6, verbatim)

### §6 — Cross-lane protocols

- **Finding discipline:** every finding carries — reproducible call (exact tool + args),
  verbatim evidence excerpt, primary failure class (§4), severity, **suspected layer**
  (data plane / L-writer / serving-query / envelope-trim / ranking / MCP contract /
  architecture), dedupe check against the existing ~200 register rows (incl. R-37..R-48).
  Genuinely new rows appended to MARSYS_DEFECT_GAP_REGISTER_v2_0.md.
- **Improvisation log (class 9):** the executor logs EVERY act of ungoverned judgment it
  performs while consuming — method/krama choice, conflict adjudication, silent question
  decomposition, taxonomy→life-language translation. First-class findings.
- **Checkpointing:** each lane writes findings incrementally to the report file; a session
  interruption never loses completed work; a RESUME protocol lets a follow-on session
  continue mid-lane. Open budget makes this mandatory, not optional.
- **Known-findings anchor set:** R-37..R-48 (this session) serve as calibration anchors —
  the audit MUST independently rediscover them via its lanes; any it misses indicates a
  lane-coverage hole (audit-of-the-audit).

Every finding record, per §7 deliverable 2 (machine-readable findings JSON), carries all
of the above fields plus the record's own identity/linkage metadata so the Fable 5
planning session can cluster/sort/prioritize without re-reading prose.

---

## 4 — Satisfaction criteria (plan §8, verbatim)

### §8 — Satisfaction criteria (all five must hold; "complete" ≠ "no gaps remain" — it
means NO GAP REMAINS FOR LACK OF LOOKING)

1. **Census completeness** — 100% of tools (1a), 100% of enumerated value families (1b),
   and 100% of services (1c) have retrievability records on both charts; the value-family
   enumeration itself is DB-derived and exhaustive, never from memory.
2. **Question-width completeness** — 100% of the approved question list traced end-to-end
   with an evidence-sufficiency verdict; every missing-but-relevant data point root-caused.
3. **Depth completeness** — 20/20 entity dossiers with full facet matrices; every
   held-but-not-received facet root-caused.
4. **Coverage honesty** — self-declaration lists every known surface as audited or
   explicitly deferred with reason.
5. **Plannability** — every finding machine-readable with class + suspected layer +
   reproducible evidence; the planning session never needs to re-derive.

---

## 5 — RESUME protocol (derived from plan §12 items 3-4)

This section derives operational RESUME mechanics from the state-discipline principles
laid down in plan §12 items 3 and 4 (the AUDIT_STATE.md pattern and the per-lane state
shard discipline codified more fully in §12.7's "State discipline under parallelism"
paragraph, transcribed in full in Section 6 below). The derivation:

- **AUDIT_STATE.md** is the standing top-level state file (CURRENT_STATE pattern):
  lane × status × rows-done/rows-total × findings-count, updated atomically at every
  checkpoint. Any fresh or resumed session reads it first and knows exactly where the
  audit stands; no lane can be silently skipped because its zero-count is visible on read.
- Under the swarm execution model (§12.7), AUDIT_STATE.md becomes an **index** over
  per-lane state shards at `state/LANE<k>.md`, each owned exclusively by its lane
  conductor. The top-level index is regenerated by whichever conductor checkpoints —
  regeneration is derived purely from shard counts, so it is idempotent and concurrent
  regeneration by multiple conductors is safe (no write contention, no lost updates).
- **Resume semantics:** a follow-on/resumed session (conductor or sub-agent) reads its own
  lane's shard (`state/LANE<k>.md`), determines the last completed row/shard boundary, and
  continues from there — never re-does completed rows, never silently skips undone ones.
  This holds identically whether the interruption is a full session end or a mid-lane
  crash: checkpointing is incremental (per plan §6 "Checkpointing"), so a session
  interruption never loses completed work.
- **Verifier sampling** (e.g. Lane 2's ~15% re-grade) runs as parallel verifier workers and
  checkpoints into the same shard discipline — verifier state is not a separate untracked
  side-channel.
- **Atomicity contract:** every checkpoint write to a shard must leave that shard in a
  self-consistent, immediately-resumable state (row counts, findings-count, and status all
  updated together) — a partial/torn checkpoint write is itself an execution defect, not an
  acceptable RESUME condition.

---

## 6 — Execution DAG (plan §12.7, TRANSCRIBED VERBATIM)

### §12.7 — Swarm execution model (native directive, review round 3) — parallel by default,
sequential only where a dependency edge forces it; sub-agent-driven throughout.

**Pattern:** every phase and lane runs as a CONDUCTOR + WORKER-SWARM. The conductor
owns the lane's ledger, shards it, spawns fresh sub-agents per shard (each worker gets
only the charter excerpt + its shard — full attention, zero context decay), collects
trace files, merges, updates state. Workers never write shared files; each writes its
own shard trace, the conductor merges — no write contention.

**Execution DAG (edges are the ONLY sequencing; everything else is parallel):**
```
FOUNDRY:  [8 ledger builders — PARALLEL sub-agents]
             └→ [charter + 11 briefs — PARALLEL per brief once its ledger lands]
                  └→ [traceability matrix + anti-softening diff]  (sequential tail)
REVIEW GATE (Cowork; sequential by nature)
EXECUTION: Item-0 ∥ Lane1a ∥ Lane1b ∥ Lane1c ∥ Lane2 ∥ Lane3 ∥ Lane4 ∥ Lane5 ∥
           Lane6 ∥ Lane7 ∥ Lane8 ∥ Lane9a ∥ Lane9b ∥ Lane10-compile
             — ALL PARALLEL, each a conductor+swarm; Item-0's result is broadcast to
               Lanes 2/7 mid-flight (timing verdicts annotated, not blocked)
           Lane10-grade  ← the ONE hard sequential edge: promise-vs-DELIVERY grading
               consumes the other lanes' evidence, so its grading pass runs at
               consolidation (its promise-ledger COMPILATION runs parallel, per asset)
CONSOLIDATION (sequential): merge → dedupe vs register → calibration-anchor test
           (R-37..R-48 rediscovery) → Lane10-grade → report + findings JSON
```

**Intra-lane sharding:** Lane 1a by tool batches; 1b by table × fact_category; 1c by
service; Lane 2 by question rows (concurrency-capped batches, e.g. 5–10 workers, the
conductor throttles to subscription limits); Lane 3 by graha; Lane 4 by tool; Lane 5 by
fact family; Lane 6 by ranked surface; Lane 7 one worker per heavy question; Lane 8 one
worker per dossier (20 workers); Lane 9a by node sample, 9b by fact_category; Lane 10
compile by asset.

**State discipline under parallelism:** AUDIT_STATE.md becomes an index over per-lane
state shards (`state/LANE<k>.md`), each owned exclusively by its lane conductor;
the top-level index is regenerated by whichever conductor checkpoints (counts only,
derived from shards — regeneration is idempotent, so concurrent regeneration is safe).
Verifier sampling (Lane 2's ~15% re-grade) runs as parallel verifier workers.

**Wall-clock consequence:** with worker swarms, the audit compresses from a chain of
long sessions to a few conductor sessions bounded mainly by subscription usage windows;
RESUME semantics unchanged (any conductor resumes from its shard).

---

## 7 — Judgment rubrics

**RATIFIED — Cowork review gate (Fable 5 + native) ratified all five rubrics 2026-07-12
(GATE_RATIFICATION_v1_0.md v1.1 §1). Lanes MAY now execute against them.**

These rubrics are derived (not verbatim-transcribed) from the plan sections cited under
each heading, to operationalize judgment calls the plan leaves as prose. All five (7.1–7.5)
were reviewed line-by-line and ratified in the Cowork review gate (plan §12 item 4). Ruling
summary (see gate record §1 for full text):
- **7.1 Usable form** — RATIFIED as written.
- **7.2 Synthesizability-as-received** — RATIFIED as written (first-contact discipline affirmed).
- **7.3 Evidence-sufficiency scale** — RATIFIED as written (INSUFFICIENT vs UNREACHABLE-BY-NONEXISTENCE distinction affirmed; "§J" = CLAUDE.md §J).
- **7.4 Ranking-quality metrics** — RATIFIED **with one binding amendment (applied below in-place):**
  raw metric values (all five) are ALWAYS reported per surface per chart; any tolerance
  judgment ("above what a reasonable acharya read would tolerate") MUST state its rationale
  inline in the finding — no silent thresholds.
- **7.5 Promise-shortfall attribution** — RATIFIED as written.

### 7.1 — "Usable form" rubric

*Derived from plan §4 class 6 (UNUSABLE FORM) and class 7 (DROWNED) definitions.*

Class 6, verbatim definition: "arrives but cannot be synthesized: IDs without text,
truncated narration, un-budgeted dumps (R-40/R-30/R-44c class)."
Class 7, verbatim definition: "correct data buried under duplication walls or trivia
ranked as chart-defining (R-37/R-44a/b class)."

Draft grading questions for any payload under test:
1. **Referential resolvability** — does every ID/key in the payload resolve to human-
   readable text within the SAME response, or require a chained lookup the LLM was not
   told to make? Unresolved IDs → fails class 6.
2. **Narration integrity** — is any narrative/explanatory field truncated mid-sentence or
   mid-clause (not at a natural boundary)? Truncation mid-meaning → fails class 6 (R-32
   analog).
3. **Budget proportionality** — is the payload size bounded in a way that is DISCLOSED to
   the consumer (a stated cap, with an honest "more available" flag) versus an un-budgeted
   dump that silently truncates or silently balloons (e.g., R-44c 181KB class)? Undisclosed
   over/under-budgeting → fails class 6.
4. **Signal-to-trivia ratio** — for ranked/listed payloads, is there a decisive top-K that
   an acharya would recognize as chart-defining, or is signal buried under duplicate rows
   / low-information trivia promoted to the same rank tier? Burial → fails class 7
   (DROWNED), not class 6 — the data is technically present and technically parseable, but
   not FINDABLE within the response.
5. A payload can fail BOTH 6 and 7 simultaneously (e.g., unresolved IDs buried in 300
   duplicate rows) — log the primary class per the finding's dominant defect, note the
   secondary in the evidence excerpt.

### 7.2 — "Synthesizability-as-received" rubric

*Derived from Lane 1a description, plan lines 136-141.*

Plan §5 Lane 1a (verbatim, for anchor): "Every MCP tool (~150), called ≥1× per chart with
realistic arguments. Record: response shape, byte size, honesty markers, synthesizability-
as-received (rubric in brief). Base rate observed so far: assets FAIL on first contact
(bo_anveshana R-37, kala_activation R-45 — both failed the first time anyone consumed
them)."

Draft grading scale for "synthesizability-as-received" (apply on FIRST CONTACT — no
follow-up calls, no prior knowledge of the tool beyond its MCP description):
- **PASS** — response shape is self-describing (field names/labels are meaningful without
  external schema knowledge); an LLM with no more context than the tool description and
  this one response could compose at least one correct, cited sentence of synthesis from
  it.
- **PARTIAL** — response is technically parseable and contains real data, but requires
  either (a) undocumented tribal knowledge to interpret a field, or (b) a second call to a
  DIFFERENT tool not implied by the first tool's description, to become usable.
  Undocumented-requirement instances are themselves class-9 (UNGOVERNED JUDGMENT)
  candidates — log both.
- **FAIL** — response is empty, an error, a bare ID/UUID list with no resolvable text, or
  its "honesty markers" (counters, flags, verdicts) contradict its own payload on
  inspection (this overlaps class 5, DISHONEST SELF-DESCRIPTION — log both classes if
  both are present).
- Honesty markers are graded separately and ALWAYS checked regardless of PASS/PARTIAL/FAIL
  on the synthesizability axis — a tool can be synthesizable AND dishonest about its own
  coverage simultaneously.

### 7.3 — Evidence-sufficiency grading scale (Lane 2)

*Derived from plan line 173: "Graded NOT 'did tools return rows' but 'did the retrievable
evidence suffice to answer at acharya grade' (§J)."*

Draft 4-point scale, applied per question after the FULL evidence-acquisition attempt
(all calls the plan's P-12 evidence-plan-then-acquire mode would make) is exhausted:
- **SUFFICIENT** — the evidence retrieved, taken together, would let an acharya-grade
  reading be composed at the width and depth doctrine (Section 1 above) requires for this
  question class, with no material gap the LLM had to paper over with a prior/guess.
- **SUFFICIENT-WITH-GAPS** — a usable answer is composable, but one or more relevant
  factors (per the width axis) were sought and not retrieved; the answer is honest about
  the gap rather than silently omitting it. Each gap is its own finding, classed per §4.
  Every chain break (plan line 173: "Every chain break is a finding") is logged here even
  if the overall verdict is SUFFICIENT-WITH-GAPS.
- **INSUFFICIENT** — the retrievable evidence, even fully exhausted, does not support an
  acharya-grade answer; the LLM would have to fabricate, guess, or fall back to generic
  astrology to respond. Root-cause each missing item into a §4 class.
  Distinguish INSUFFICIENT (evidence exists somewhere in the system but was not reachable
  by this lane's acquisition attempt — class 1/4/6/7/8 candidates) from
  UNREACHABLE-BY-NONEXISTENCE (plan §2.1: the classical canon calls for a concept the
  system never computed at all — a data-plane gap, not a retrieval gap).
- **UNANSWERABLE-BY-DESIGN** — the question itself falls outside any layer's declared
  scope (e.g., requires a system the platform does not model) — logged as a scope note,
  not a finding, but still recorded so the coverage-honesty criterion (§8 criterion 4) is
  satisfied.

Every verdict carries the full evidence-acquisition trace (what was sought, in what order,
via which calls, what was received) per the finding schema (Section 3) and per Lane 2's
"executor RUNS in exactly this mode manually: writes the evidence plan BEFORE any call,
tracks acquisition" discipline (plan §9 P-12 audit-hook row).

### 7.4 — Ranking-quality metrics (Lane 6)

*Derived from plan lines 198-205 (Lane 6 description).*

Plan §5 Lane 6 (verbatim, for anchor): "For each ranked surface (orientation top-signals,
domain readings, signals, discoveries, convergence): is the top-K what an acharya would
put first? Measured: duplication rate, identical-score walls, descriptive-trivia share,
family-collapse coverage, UNATTRIBUTED share (R-44: 298/300 unattributed; R-37: top-30 of
discoveries = 1 unique finding)."

Draft operational metrics, computed per ranked surface under test:
1. **Duplication rate** — fraction of top-K rows that are exact or near-exact duplicates
   of another row in the same top-K (same underlying fact/signal restated). Numerator:
   count of rows that are duplicates of an earlier-ranked row; denominator: K.
2. **Identical-score walls** — fraction of top-K rows sharing an identical rank/score with
   at least one other row (a "wall" = 3+ consecutive or co-tied rows at the same score),
   flagged as a discrimination failure — the ranker could not tell them apart.
3. **Descriptive-trivia share** — fraction of top-K rows that are low-decision-weight
   descriptive facts (e.g., basic placement restatements) ranked at the same tier as
   chart-defining findings (yogas, doshas, major convergences). Requires a reference
   "major vs. trivia" classification — use the classical-canon weighting (Section 1,
   source 1) as the arbiter where the system itself provides no weight.
4. **Family-collapse coverage** — for a ranked surface that should span multiple entity/
   topic families (e.g., multiple grahas, multiple yoga types), the fraction of DISTINCT
   families represented in top-K versus the total families present anywhere in the
   underlying data. Low coverage = the ranking collapsed onto one family and starved
   others (R-37 pattern: top-30 = 1 unique finding).
5. **UNATTRIBUTED share** — fraction of top-K rows lacking a resolvable derivation-ledger
   / constituent-fact attribution (per CLAUDE.md §I B.3 derivation-ledger mandate) — i.e.
   the row cannot be traced back to the L1 fact(s) that produced it. R-44 anchor:
   298/300 unattributed.
Each metric is reported per surface per chart. **[Gate v1.1 amendment, binding]** The raw
values of all five metrics are ALWAYS reported per surface per chart, unconditionally —
there is no silent tolerance threshold below which reporting is skipped. A surface whose
duplication rate, identical-score-wall share, or UNATTRIBUTED share is judged above what a
reasonable acharya read would tolerate is a DROWNED (class 7) finding at minimum; but any
such tolerance judgment MUST state its rationale inline in the finding record (why THIS
value on THIS surface exceeds acharya tolerance) — no silent thresholds, no un-justified
cutoffs.

### 7.5 — Promise-shortfall layer attribution rules (Lane 10)

*Derived from plan lines 272-288 (Lane 10 description).*

Plan §5 Lane 10 (verbatim, for anchor): "(3) where the shortfall sits — data plane (never
computed/written), retrieval plane (computed but unreachable/unusable), or ranking/form
(reachable but drowned/mangled)."

Draft attribution decision tree, applied per asset after its promise (verbatim, cited) and
current delivery (from other lanes' evidence) are both in hand:
1. **Data plane** — was the promised value ever computed and written to the DB by the
   asset's writer? Check via read-only DB query (SELECT only). If NO rows / NULL / table
   empty for the relevant chart → shortfall = DATA PLANE, regardless of what any MCP tool
   claims to serve.
2. **Retrieval plane** — if the value IS present in the DB, is there an MCP tool/service
   path that returns it at all (any shape, any form)? If NO reachable path in ≤ the calls
   a reasonable consuming LLM would make → shortfall = RETRIEVAL PLANE (class 1
   UNREACHABLE). If the value is technically reachable but only via a call sequence not
   implied by any tool description → still RETRIEVAL PLANE, cross-logged as a class 9
   (UNGOVERNED JUDGMENT) finding for the undocumented sequence.
3. **Ranking/form** — if the value IS reachable, is it delivered in a form that satisfies
   the "usable form" rubric (Section 7.1)? If it arrives but is drowned (class 7),
   malformed (class 6), wrong (class 2), inconsistent (class 3), or dishonestly described
   (class 5) → shortfall = RANKING/FORM, with the specific §4 class(es) attached.
4. **No shortfall** — if data plane, retrieval plane, and ranking/form all clear, the asset
   PASSES against its own declared promise (plan line 283: "an asset that delivers exactly
   its promise passes even if modest") — this is a valid, expected outcome, not evidence
   of an incomplete audit.
5. **Compound shortfalls** — an asset may fail at more than one layer (e.g., half its
   promised facets never computed AND the half that IS computed is drowned). Attribute
   EACH failing facet to its own layer independently; do not collapse to a single verdict
   per asset when the plan's own ledger (Concept×Retrievability matrix, Section 1b) is
   facet-grained.
6. Grading is always against the asset's OWN declared intent (plan line 282: "not a
   generic rubric"), sourced from: the build brief
   (`00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_<asset>_v*.md`), the `asset_registry` row,
   the layer handoff/closure document, and the MCP tool description fronting it — all four
   sources checked; where they disagree on what was promised, that disagreement is itself
   logged (class 3 INCONSISTENT, applied to the promise-record rather than the data).

---

*End of CHARTER v1.1. Every child lane brief cites this charter by canonical_id
`LLM_CONSUMPTION_AUDIT_CHARTER` and by section number for doctrine, taxonomy, finding
schema, satisfaction criteria, RESUME protocol, and execution DAG. Section 7 rubrics are
RATIFIED (GATE_RATIFICATION_v1_0.md v1.1 §1, 2026-07-12) with the 7.4 raw-metrics-always
amendment applied in-place; lanes may execute against them. Child briefs that still carry
"DRAFT pending ratification" / "PENDING-RUBRIC-RATIFICATION" language for §7 inherit this
ratification — those provisional flags are now discharged. Changelog: v1.1 (2026-07-12) —
§7 DRAFT→RATIFIED per gate record, 7.4 amendment applied; v1.0 (2026-07-11) — Brief Foundry.*
