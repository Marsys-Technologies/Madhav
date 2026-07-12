---
artifact: LANE7_SYNTHESIS_CEILING
type: BRIEF (Brief Foundry output — Lane 7 child brief, self-contained per plan §12.7 Foundry
  discipline: "briefs -- PARALLEL per brief once its ledger lands")
version: 1.0
status: READY FOR EXECUTION — gated on Item 0 broadcast (annotates, does not block) and on
  the Cowork ratification of CHARTER.md §7 rubrics (DRAFT until ratified)
program: LLM_CONSUMPTION_AUDIT_PLAN_v1_0
plan_ref: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md §5 Lane 7 (lines 207-214)
charter_ref: 00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md (canonical_id
  LLM_CONSUMPTION_AUDIT_CHARTER) — doctrine, taxonomy, finding schema, satisfaction criteria,
  RESUME protocol, execution DAG, judgment rubrics ALL BY REFERENCE. This brief does not
  restate them — see Section 0 below for exact citation map.
charts_in_scope:
  - 482012f1-710e-4a25-994a-93821f5871aa   # Abhisek (native)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a   # Abhinandan
feeds_from: [Item 0 broadcast]   # per plan §12.7 DAG — "Item-0's result is broadcast to
  Lanes 2/7 mid-flight (timing verdicts annotated, not blocked)"
feeds_into: [Lane 10-grade, CONSOLIDATION, Fable 5 planning session (P-11 requirements spec)]
authored_by: Brief Foundry session (Claude Code), 2026-07-11
---

# LANE 7 — LARGE-N SYNTHESIS CEILING PROBE

## 0. How to use this brief (read this first — self-containment map)

This brief is executable by a FRESH session that has read nothing else in this program. It
is self-contained via CHARTER-BY-REFERENCE: every piece of shared doctrine is a named
citation into `00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md`
(canonical_id `LLM_CONSUMPTION_AUDIT_CHARTER`), not re-derived here. Before running any
question, READ CHARTER.md in full — it is short (382 lines) and every section below cites
it by number:

- Doctrine (width/depth completeness axes, examples-are-illustrative rule) — CHARTER §1.
- 9-class failure taxonomy — CHARTER §2. Every Lane 7 finding gets exactly one primary
  class from this list (class 8, UN-SYNTHESIZABLE AT SCALE, is Lane 7's signature class,
  but any of the 9 may apply to any individual composition step).
- Finding schema (the fields every finding record must carry) — CHARTER §3.
- Satisfaction criteria — CHARTER §4 (Lane 7 contributes chiefly to criterion 5,
  Plannability, and criterion 2, Question-width completeness, for its 10 questions).
- RESUME protocol — CHARTER §5.
- Execution DAG — CHARTER §6 (verbatim §12.7 transcription; Lane 7 runs as one of the
  fully-parallel execution-phase lanes, fed mid-flight by the Item 0 broadcast).
- Judgment rubrics — CHARTER §7, specifically:
  - §7.1 "Usable form" rubric — apply to every payload received during a heavy question's
    evidence acquisition.
  - §7.3 Evidence-sufficiency grading scale — apply the FINAL verdict per question.
  - §7.4 Ranking-quality metrics — apply to any ranked/top-K surface consulted mid-question.

Do not paraphrase any CHARTER section into this brief or into lane output — cite it by
section number. CHARTER §7 rubrics are DRAFT pending Cowork ratification (Fable 5 + native)
per plan §12 item 4; this brief inherits that gate — Lane 7 execution against §7.1/§7.3/§7.4
must wait for ratification, but the ledger-shard-and-ceiling-documentation WORK described
below (Section 3 of this brief) does not itself depend on a rubric — it is a mechanical
trace-and-measure protocol that the rubrics THEN grade. If ratification is pending, the
executor may run the acquisition passes and hold the final SUFFICIENT/PARTIAL/INSUFFICIENT
verdicts until ratification lands.

## 1. Plan §5 Lane 7 — TRANSCRIBED VERBATIM (plan lines 207-214)

> ### Lane 7 — Large-N synthesis ceiling probe
> Ten deliberately heavy questions (the wealth-magnitude question is the template). Document
> precisely where composition fails: what the LLM needed, what it could actually get, in how
> many calls, what got trimmed, where flat top-K walls replaced discrimination. This lane
> produces the REQUIREMENTS SPEC for the synthesis capability (R-48) that the planning
> session will design — including whether volume is handled in one pass or incrementally,
> per the native's framing: either is acceptable, but a strong system for high-volume
> multi-factor synthesis must exist.

Every sentence above is a binding instruction, not a paraphrase target. In particular:

- "Ten deliberately heavy questions" — the count is exactly ten question TYPES (each run
  narrow + broad × 2 charts per the ledger's existing shape — see Section 2), not ten
  total traces.
- "the wealth-magnitude question is the template" — question E1 (see Section 2) is the
  calibration anchor for what "deliberately heavy" means; every other of the ten questions
  must be selected/graded against that same bar of heaviness, not a lighter one.
- "Document precisely" — the four required documentation axes are non-negotiable and are
  each their own field in the required output (Section 4): (a) what the LLM needed,
  (b) what it could actually get, (c) in how many calls, (d) what got trimmed, PLUS
  (e) where flat top-K walls replaced discrimination.
- "REQUIREMENTS SPEC for the synthesis capability (R-48)" — Lane 7's deliverable is not
  merely a set of graded findings; it is a standalone requirements document the Fable 5
  planning session consumes directly to design remediation (P-11 in the plan's gap
  numbering — see plan §9, not transcribed here as Lane 7 does not need §9's other rows).
- "whether volume is handled in one pass or incrementally... either is acceptable, but a
  strong system... must exist" — Lane 7 must record, per question, whether the current
  system attempted single-pass or incremental composition (or neither — i.e. gave up), and
  must NOT grade "incremental" as inferior to "single-pass" in itself; the grading axis is
  whether SOME strong composition path existed, not which shape it took.

## 2. Ledger — the ten heavy questions (group L feeder + wealth-magnitude anchor)

Lane 7's question set is **group L** of the Lane-2 question ledger, **plus** the E1
wealth-magnitude anchor (E1 is Lane 7's named template per plan line 208 but lives in Lane
2's ledger under group E, not group L — it is pulled in explicitly here). The plan states
"ten deliberately heavy questions" verbatim (plan line 208) — this is a FLOOR, not a
target the executor may trade down. The ledger as it currently exists only names 7
heavy-type slots directly (6 group-L types L1-L6 + E1 wealth-magnitude, explicitly named as
the template). **This 7-vs-10 gap does NOT license the executor to proceed with 7.** The
executor's Item 1 (Section 3 below) is MANDATORY, not optional: locate at least 3 more
heavy-type questions already latent in the full 82-type Lane 2 ledger that meet the E1
heaviness bar (candidates to check first: any question requiring cross-domain convergence,
multi-decade windows, or explicit ranking across >5 factors — scan the full ledger at
`00_ARCHITECTURE/llm_consumption_audit/ledgers/questions.jsonl`) to reach ten. If, after an
exhaustive scan of all 82 ledger types, genuinely fewer than 10 questions meet the heaviness
bar, the executor logs this as a class-9 (UNGOVERNED JUDGMENT) finding AND escalates to the
lane's conductor/native before proceeding with fewer than ten — this is a HALT-and-escalate
condition on this specific point, not a silent-or-logged-and-continue option. The Lane 7
coverage self-declaration (Section 7) records which of the two outcomes occurred and why.

**Ledger file (Lane-7 feeder — group L rows):**
`00_ARCHITECTURE/llm_consumption_audit/ledgers/questions.jsonl`

Group L rows (row_id, question_code, question_text, variant, chart target — extracted
verbatim from the ledger; the executor marks each `status` field in place):

| row_id | code | question_text | variant | chart |
|---|---|---|---|---|
| 0305_L1_narrow_abhisek | L1 | whole-life arc narrative | narrow | Abhisek |
| 0306_L1_narrow_abhinandan | L1 | whole-life arc narrative | narrow | Abhinandan |
| 0307_L1_broad_abhisek | L1 | whole-life arc narrative | broad | Abhisek |
| 0308_L1_broad_abhinandan | L1 | whole-life arc narrative | broad | Abhinandan |
| 0309_L2_narrow_abhisek | L2 | five strongest + five weakest promises ranked | narrow | Abhisek |
| 0310_L2_narrow_abhinandan | L2 | five strongest + five weakest promises ranked | narrow | Abhinandan |
| 0311_L2_broad_abhisek | L2 | five strongest + five weakest promises ranked | broad | Abhisek |
| 0312_L2_broad_abhinandan | L2 | five strongest + five weakest promises ranked | broad | Abhinandan |
| 0313_L3_narrow_abhisek | L3 | central tension/contradiction | narrow | Abhisek |
| 0314_L3_narrow_abhinandan | L3 | central tension/contradiction | narrow | Abhinandan |
| 0315_L3_broad_abhisek | L3 | central tension/contradiction | broad | Abhisek |
| 0316_L3_broad_abhinandan | L3 | central tension/contradiction | broad | Abhinandan |
| 0317_L4_narrow_abhisek | L4 | notable ABSENCES (negative knowledge) | narrow | Abhisek |
| 0318_L4_narrow_abhinandan | L4 | notable ABSENCES (negative knowledge) | narrow | Abhinandan |
| 0319_L4_broad_abhisek | L4 | notable ABSENCES (negative knowledge) | broad | Abhisek |
| 0320_L4_broad_abhinandan | L4 | notable ABSENCES (negative knowledge) | broad | Abhinandan |
| 0321_L5_narrow_abhisek | L5 | whole-chart remedial stack | narrow | Abhisek |
| 0322_L5_narrow_abhinandan | L5 | whole-chart remedial stack | narrow | Abhinandan |
| 0323_L5_broad_abhisek | L5 | whole-chart remedial stack | broad | Abhisek |
| 0324_L5_broad_abhinandan | L5 | whole-chart remedial stack | broad | Abhinandan |
| 0325_L6_narrow_abhisek | L6 | unprompted acharya warnings | narrow | Abhisek |
| 0326_L6_narrow_abhinandan | L6 | unprompted acharya warnings | narrow | Abhinandan |
| 0327_L6_broad_abhisek | L6 | unprompted acharya warnings | broad | Abhisek |
| 0328_L6_broad_abhinandan | L6 | unprompted acharya warnings | broad | Abhinandan |

**Wealth-magnitude template anchor (group E, pulled in explicitly — the plan's own named
template, plan line 208: "the wealth-magnitude question is the template"):**

| row_id | code | question_text | variant | chart |
|---|---|---|---|---|
| 0105_E1_narrow_abhisek | E1 | wealth magnitude [anchor] | narrow | Abhisek |
| 0106_E1_narrow_abhinandan | E1 | wealth magnitude [anchor] | narrow | Abhinandan |
| 0107_E1_broad_abhisek | E1 | wealth magnitude [anchor] | broad | Abhisek |
| 0108_E1_broad_abhinandan | E1 | wealth magnitude [anchor] | broad | Abhinandan |

**Ledger file 2 — L2/CDLM/CGM asset promises (for grading whether the synthesis engines
Lane 7 leans on were even PROMISED the capability it is testing for):**
`00_ARCHITECTURE/llm_consumption_audit/ledgers/asset_promises.jsonl`

Relevant rows (asset_id, layer, promise_quote, citation — the assets most load-bearing for
large-N composition: the graph, the digest, the evidence-weighting engine, and the two
CDLM/CGM-named rows):

- `AP-024 bo_karanajala` (L2) — "bo_karanajala is the heavy writer that does the whole
  compute + owns edges/sub_graphs/motifs/topology/paths/contradictions." (source:
  `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_BO_KARANAJALA_BIMBA_v1_0.md:45-49`)
- `AP-018 bo_bimba` (L2) — "bo_bimba is a THIN nodes-only face that registers
  bodha_cgm_nodes from the same compute (it does not recompute the graph)." (source:
  `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_BO_KARANAJALA_BIMBA_v1_0.md:49-50`)
- `AP-029 bo_samvada` (L2) — "bo_samvada is the UCD — Unified Chart Digest — the LLM's
  FIRST retrieval: the call that gives it the whole chart's skeleton so its follow-up
  queries are TARGETED, not scattershot. ... it is the chart's GESTALT ... AND the
  navigable spine of the whole judgment substrate." (source:
  `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_BO_SAMVADA_v1_0.md:28-33`)
- `AP-030 bo_sangati` (L2) — "bo_sangati is ALSO the home of Move 1 — the weight-of-evidence
  engine: per domain, the full EVIDENCE LEDGER (support / oppose / independent-weight /
  cross-tradition / net-verdict / confidence / dissents). This is the asset that turns
  Bodha from a fact store into a judgment substrate." (source:
  `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_BO_SANGATI_v1_0.md:32-36`)
- `AP-019 bo_cdlm_summary` (L2) — promise_quote: `NOT FOUND` (source: `none`) — logged
  as-is; a NOT FOUND promise is itself evidence for Lane 7's requirements-spec output (if
  the CDLM summary asset never had a declared promise, that is a Lane-10 finding Lane 7
  should cross-reference, not silently paper over — see Section 5).
- `AP-020 bo_cgm_motifs` (L2) — promise_quote: `NOT FOUND` (source: `none`).
- `AP-021 bo_cgm_paths` (L2) — promise_quote: `NOT FOUND` (source: `none`).

Mark these `asset_promises.jsonl` rows against Lane 7's own findings when a heavy question's
composition failure traces to one of these six assets specifically (e.g., "L2 five
strongest/weakest promises ranked" failing because `bo_sangati`'s evidence ledger was
unreachable in the calls attempted → cite `AP-030` in the finding's evidence field).

**Completeness is a count query** — before closing Lane 7, run:

```
grep -c '"question_group": "L\.' 00_ARCHITECTURE/llm_consumption_audit/ledgers/questions.jsonl
```

(adjust the pattern to the ledger's actual `question_group` field values — see the sample
rows in Section "head questions" of this brief's authoring trace; the field observed at
authoring time was `"question_group": "L. <name>"`-shaped for other groups, verify against
live ledger) and confirm all 24 group-L rows plus the 4 E1 rows (28 total row targets) carry
a non-`pending` `status` field before Lane 7 reports itself complete. If the executor adds
the 3 additional heavy-question-type candidates per Section 2's Item 1(a) branch, their rows
must also reach non-`pending` before completion, and their new `row_id`s must be appended
to `questions.jsonl` (do not create a parallel file — one ledger, per CHARTER discipline).

## 3. Protocol (plan §5 Lane 7, operationalized step-by-step)

Run this protocol identically for EACH of the 7 (or 10, per Section 2's resolution) heavy
question types × narrow/broad × 2 charts = 28 (or 40) individual traces. Each trace is one
shard (see Section 8 for the swarm decomposition — one worker per heavy QUESTION, not per
trace; a worker runs all 4 chart×variant traces for its assigned question type).

### Step 1 — Evidence PLAN before any call (per CHARTER §7.3 discipline, plan P-12
audit-hook row: "writes the evidence plan BEFORE any call, tracks acquisition")

Before making any MCP call for a given trace, write down: what data/evidence this specific
question, at acharya grade, WOULD need — enumerated at the width and depth CHARTER §1
requires (the Mercury-standard depth axis generalizes to whatever entity/domain set the
question implicates; for L1 "whole-life arc narrative" this could mean every major
dasha-lord transition + every yoga/dosha + every divisional confirmation across a lifetime
— do not under-scope the plan before acquiring). This plan is itself part of the trace
record (Section 4 field `evidence_plan`).

### Step 2 — Acquire, tracking EVERY call

Execute the evidence plan via the public MCP channel (Lane 7 is NOT a DB-access lane per
plan §3 "All other lanes consume the public MCP channel exclusively" — no
`mcp__postgres__query` use in Lane 7 itself; Lane 5/Lane 8 own DB-access verification).
Record, per call: tool name, arguments, response byte size, and a running tally against the
evidence plan (satisfied / partially satisfied / unsatisfied per planned item). This IS the
"in how many calls" documentation axis (plan line 209) — the call count is not an
after-the-fact estimate, it is the literal count of calls made.

### Step 3 — Apply CHARTER §7.1 "usable form" rubric to every payload received

For each response, grade referential resolvability, narration integrity, budget
proportionality, and signal-to-trivia ratio (CHARTER §7.1 items 1-4, cited not restated).
Any payload failing is a class-6 (UNUSABLE FORM) or class-7 (DROWNED) finding per CHARTER
§2 — log it against the finding schema (CHARTER §3) immediately, do not batch to the end.

### Step 4 — Apply CHARTER §7.4 ranking-quality metrics to any ranked/top-K surface consulted

Any ranked surface touched mid-question (e.g., L2's "five strongest + five weakest promises
ranked" necessarily consults a ranking surface) gets the 5 CHARTER §7.4 metrics computed
(duplication rate, identical-score walls, descriptive-trivia share, family-collapse
coverage, UNATTRIBUTED share) and logged.

### Step 5 — Compose (or attempt to compose) the actual answer

Attempt the full synthesis a consuming LLM would produce. Document explicitly: did
composition succeed at acharya grade; if it failed, at what STEP did it fail (ran out of
calls, evidence insufficient, ranking walls prevented discrimination, no path existed to
combine N factors at all); did the system offer or require single-pass vs. incremental
composition (plan line 213 axis — record which, neither graded as inferior).

### Step 6 — Apply CHARTER §7.3 evidence-sufficiency verdict

Assign SUFFICIENT / SUFFICIENT-WITH-GAPS / INSUFFICIENT / UNANSWERABLE-BY-DESIGN per
CHARTER §7.3's exact definitions (cited, not restated) as the trace's final verdict.

### Step 7 — "What got trimmed" — mandatory explicit field

Separately from the sufficiency verdict, record every instance where evidence was
DELIBERATELY OR SILENTLY reduced along the way: budget ceilings truncating a payload,
top-K limits cutting off relevant rows, a call the executor chose not to make because of
volume, a response the system itself trimmed with or without disclosure (cross-reference
CHARTER §7.1 item 3, budget proportionality — an undisclosed trim is ALSO a class-6 finding,
but "what got trimmed" is tracked here even for DISCLOSED trims, since the requirements-spec
deliverable (Section 5) needs the full trim inventory regardless of disclosure honesty).

### Step 8 — "Where flat top-K walls replaced discrimination" — mandatory explicit field

Cross-reference CHARTER §7.4 item 2 (identical-score walls). Record, per trace, every
specific point where the system SHOULD have discriminated between factors (ranked them,
weighted them, chosen among them) but instead returned an undifferentiated tie/wall,
forcing the LLM to guess or arbitrarily pick.

## 4. Required per-trace output record

Every trace (28 or 40 total) produces one JSON record with, at minimum, these fields (all
CHARTER §3 finding-schema fields PLUS the Lane-7-specific documentation axes from plan line
209, all mandatory — Section 1's "non-negotiable" note applies):

```json
{
  "row_id": "<ledger row_id, e.g. 0105_E1_narrow_abhisek>",
  "question_code": "<e.g. E1>",
  "chart_id": "<chart>",
  "variant": "narrow|broad",
  "evidence_plan": "<what the LLM determined it needed, written BEFORE acquisition>",
  "calls_made": [{"tool": "...", "args": {...}, "response_bytes": 0}],
  "call_count": 0,
  "what_could_actually_get": "<summary of evidence actually retrieved>",
  "what_got_trimmed": "<explicit list, disclosed and undisclosed>",
  "topk_walls": "<explicit list of discrimination failures, CHARTER §7.4 item 2>",
  "composition_mode_observed": "single-pass|incremental|no-path-existed",
  "composition_outcome": "succeeded-at-acharya-grade|degraded|failed",
  "usable_form_grades": "<CHARTER §7.1 grades per payload>",
  "ranking_quality_metrics": "<CHARTER §7.4 metrics, if applicable>",
  "evidence_sufficiency_verdict": "SUFFICIENT|SUFFICIENT-WITH-GAPS|INSUFFICIENT|UNANSWERABLE-BY-DESIGN",
  "failure_classes": ["<one or more CHARTER §2 classes>"],
  "suspected_layer": "data plane|L-writer|serving-query|envelope-trim|ranking|MCP contract|architecture",
  "asset_promise_refs": ["<asset_promises.jsonl row_ids implicated, if any>"],
  "anchor_check": "<does this trace independently rediscover any of R-37..R-48? CHARTER §3 known-findings-anchor-set obligation>"
}
```

## 5. Extension — the REQUIREMENTS SPEC deliverable (plan line 210-214, this brief's Section
3 point)

Beyond the 28/40 per-trace records, Lane 7 produces ONE synthesized requirements-spec
document (this is the "R-48/P-11" deliverable named in the plan) that answers, across all
ten heavy questions combined:

1. What does high-volume multi-factor synthesis structurally NEED (call budget, evidence
   density, ranking discrimination, cross-asset composition) that the current system does
   not provide — enumerated as a checklist, not prose.
2. Precisely where composition fails today — aggregated across the ten questions: is there
   a common failure point (e.g., every question stalls after N calls; every ranked surface
   hits a tie-wall past top-5) or is failure question-specific?
3. Single-pass vs. incremental — does ANY current path support either mode for high-volume
   synthesis? If neither, that is the spec's headline finding (class 8, UN-SYNTHESIZABLE AT
   SCALE, at the whole-lane level, not just per-question).
4. Item-0-informed timing note: if the Item 0 broadcast (Section 6) resolved to
   WRITER_NO_OP or SERVING_PATH_BUG, annotate every L1/L4/L5/E1 trace whose composition
   depended on temporal/activation data as PROVISIONAL pending that resolution, per CHARTER
   §6 (execution DAG) "annotate, not block" discipline.

This document is written to
`00_ARCHITECTURE/llm_consumption_audit/LANE7_SYNTHESIS_REQUIREMENTS_SPEC_v1_0.md` (or
appended as a named section of the master report per whatever final report-assembly
convention CONSOLIDATION uses — Lane 7's conductor confirms the target at execution time
against the then-current deliverables directory structure).

## 6. Item 0 broadcast — mid-flight consumption

Per CHARTER §6 (execution DAG) and the ITEM0_R45_TRIAGE brief's own §6 output format
(`00_ARCHITECTURE/llm_consumption_audit/briefs/ITEM0_R45_TRIAGE.md`), Lane 7 is a named
broadcast target. On receipt of the Item 0 JSON broadcast:

- If `verdict` is `WRITER_NO_OP`: any Lane 7 trace whose evidence plan required
  `kala_activation`/`kala_activation_predicates` (temporal×structural convergence — directly
  relevant to L1 "whole-life arc narrative" and E1 "wealth magnitude") is annotated
  `"item0_status": "confirmed-writer-no-op — Abhinandan rebuild IS a meaningful
  verification event for this defect class"` in its trace record.
- If `verdict` is `SERVING_PATH_BUG` or `PARTIAL_SERVING_PATH_BUG`: same traces annotated
  `"item0_status": "confirmed-serving-path-bug — rebuild will NOT resolve; flag as
  retrieval-layer requirement in the Section 5 requirements spec"`.
- If the broadcast has not landed when a Lane 7 worker reaches a temporal-dependent trace:
  per ITEM0_R45_TRIAGE §6, treat as `"item0_status": "timing-unverified — provisional"` and
  proceed without blocking (CHARTER §6 "annotate, not block").

## 7. Coverage self-declaration (TAP-9 style — mandatory, plan §7 deliverable 1 format)

Lane 7's conductor emits this table at close, every row filled (audited or explicitly
deferred with reason — no silent omissions):

| surface | status (audited/deferred) | reason-if-deferred |
|---|---|---|
| L1 whole-life arc narrative × {narrow,broad} × 2 charts (4 traces) | | |
| L2 five strongest+weakest promises ranked × {narrow,broad} × 2 charts (4 traces) | | |
| L3 central tension/contradiction × {narrow,broad} × 2 charts (4 traces) | | |
| L4 notable ABSENCES (negative knowledge) × {narrow,broad} × 2 charts (4 traces) | | |
| L5 whole-chart remedial stack × {narrow,broad} × 2 charts (4 traces) | | |
| L6 unprompted acharya warnings × {narrow,broad} × 2 charts (4 traces) | | |
| E1 wealth magnitude [anchor/template] × {narrow,broad} × 2 charts (4 traces) | | |
| 3 additional heavy-question-type candidates (Section 2 Item 1a/1b resolution) | | |
| bo_karanajala / bo_bimba consumption within heavy-question traces | | |
| bo_samvada (UCD) first-retrieval consumption within heavy-question traces | | |
| bo_sangati evidence-ledger consumption within heavy-question traces | | |
| bo_cdlm_summary / bo_cgm_motifs / bo_cgm_paths consumption (NOT FOUND-promise assets) | | |
| Requirements-spec synthesis document (Section 5) | | |
| Item 0 broadcast annotation pass (Section 6) | | |

## 8. Swarm decomposition (plan §12.7, MANDATORY per Brief Foundry task instructions)

**(a) Conductor + worker pattern.** One Lane 7 conductor session owns
`ledgers/questions.jsonl` (group L rows) + the E1 rows from the same file, owns
`state/LANE7.md`, and owns the final requirements-spec compilation (Section 5). The
conductor shards the ten heavy question TYPES (floor per plan line 208 — see Section 2's
mandatory-completion-to-ten rule; the conductor does not proceed to sharding with fewer
than ten without having first exhausted Section 2's escalation path),
spawns one fresh sub-agent worker per question type, and gives each worker ONLY: (i) this
brief's Sections 1-6 (the protocol + ledger rows for its one question type — narrow, broad,
both charts = 4 traces), (ii) the CHARTER.md file by reference (workers read it themselves,
full attention, zero pre-chewed context), (iii) the Item 0 broadcast if it has landed. Each
worker runs its 4 traces (Section 3's 8-step protocol × 4) to completion, writes ONE trace
file, and returns. The conductor collects, merges into `state/LANE7.md`, and only the
conductor compiles the cross-question requirements spec (Section 5) once ALL workers report.

**(b) Shard key.** One worker per heavy question — exactly as plan §12.7 states verbatim:
"Lane 7 one worker per heavy question." The wealth-magnitude question (E1) is the template
worker — spawn it first if sequencing matters for calibrating the other workers' expected
heaviness bar, though per the DAG all lanes/shards are otherwise parallel.

**(c) Concurrency cap + throttling rule.** Maximum **7 concurrent workers** (one per heavy
question type in the 7-type baseline; if Section 2 resolves to 10 types, cap at **8
concurrent workers** and queue the remainder) — this sits within the plan's stated
"concurrency-capped batches, e.g. 5-10 workers" guidance (plan §12.7 Intra-lane sharding,
citing Lane 2's cap as the reference figure) applied to Lane 7's smaller worker count. The
conductor throttles by NOT spawning the next queued worker until an active worker returns or
until the conductor observes a rate-limit signal (429/subscription-usage-window warning) on
any in-flight MCP or agent-spawn call, at which point it pauses new spawns and waits for
active workers to drain before resuming — matching CHARTER §6's "bounded mainly by
subscription usage windows" framing.

**(d) Merge protocol.** Workers NEVER write a shared file. Each worker writes ONLY its own
shard trace file at `state/LANE7/shard-<question_code>.md` (e.g.
`state/LANE7/shard-E1.md`, `state/LANE7/shard-L1.md`, … `state/LANE7/shard-L6.md`, plus any
`shard-<new-code>.md` for Section-2-resolved additional heavy questions). The conductor
ALONE reads all shard files and merges them into the single top-level
`state/LANE7.md` index plus the per-trace JSON records (Section 4) and the requirements-spec
document (Section 5). No worker ever touches `state/LANE7.md` or another worker's shard
file — this is what makes concurrent worker execution safe with zero write contention.

**(e) Per-shard RESUME semantics.** Each shard file `state/LANE7/shard-<question_code>.md`
begins with a header block:

```
question_code: <code>
traces_total: 4          # narrow+broad x 2 charts
traces_done: <n>
last_completed_trace_row_id: <row_id or "NONE">
status: not-started|in-progress|complete
```

A resumed worker (fresh session picking up an interrupted shard) reads its own
`state/LANE7/shard-<code>.md` ONLY, finds `last_completed_trace_row_id`, and resumes at the
NEXT row_id in that question's 4-row narrow/broad × chart sequence (order: narrow-Abhisek →
narrow-Abhinandan → broad-Abhisek → broad-Abhinandan, matching the ledger's row_id
numbering) — never re-running a completed trace, never skipping an incomplete one. The
conductor's own resume reads `state/LANE7.md` (the index), determines which
`state/LANE7/shard-*.md` files report `status: complete`, and re-spawns workers only for
shards reporting `not-started` or `in-progress`. This exact pointer format
(`last_completed_trace_row_id`) is the RESUME contract CHARTER §5 requires ("determines the
last completed row/shard boundary, and continues from there").

---

*End of LANE7_SYNTHESIS_CEILING brief v1.0. Cites `LLM_CONSUMPTION_AUDIT_CHARTER` (CHARTER.md)
for all shared doctrine/taxonomy/schema/criteria/RESUME/DAG/rubrics. Self-contained: a fresh
session needs only this file + CHARTER.md + the two named ledger files
(`ledgers/questions.jsonl` group L + E1 rows, `ledgers/asset_promises.jsonl` L2/CDLM/CGM
rows) to execute Lane 7 end-to-end.*
