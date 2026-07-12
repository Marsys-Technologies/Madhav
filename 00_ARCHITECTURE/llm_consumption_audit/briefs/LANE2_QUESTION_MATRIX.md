---
artifact: LANE2_QUESTION_MATRIX
type: BRIEF (Brief Foundry output — Lane 2 child brief, self-contained, executable by a
  FRESH session that has read nothing else)
version: 1.0
status: READY FOR EXECUTION — gated on Cowork review-gate ratification of CHARTER.md §7
  rubrics (rubric 7.3 in particular) per plan §12 item 4, before any lane executes
program: LLM_CONSUMPTION_AUDIT_PLAN_v1_0
plan_ref: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md §5 Lane 2 (lines 167-175)
charter_ref: 00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md
  (doctrine, taxonomy, finding schema, satisfaction criteria — cited by reference, NOT
  re-derived in this brief; see §0 below)
charts_in_scope:
  - 482012f1-710e-4a25-994a-93821f5871aa   # Abhisek (native)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a   # Abhinandan
ledger: 00_ARCHITECTURE/llm_consumption_audit/ledgers/questions.jsonl (329 lines incl.
  1 HEADER row + 328 question-trace rows)
checkpoint: 00_ARCHITECTURE/llm_consumption_audit/state/LANE2.md (owned EXCLUSIVELY by
  this lane's conductor — no other lane, and no worker, writes to this path)
broadcast_consumed_from: Item 0 (ITEM0_R45_TRIAGE.md) — timing verdict annotates this
  lane's timing-question rows mid-flight, per plan §12.7; does NOT block this lane's start
deliverable_of: plan §7 deliverable 5 (question-coverage matrix, standing asset) +
  deliverable 8 (Lane 2 evidence-plans + acquisition logs, the P-12 requirements corpus)
authored_by: Brief Foundry session (Claude Code), 2026-07-11
---

# LANE 2 — QUESTION-FIRST COVERAGE MATRIX

## 0. How to use this brief (read this first — self-containment statement)

This brief is executable standalone. You do not need to have read the master plan, the
prior Cowork discussion, or any other lane brief. Everything you need is either
transcribed verbatim below or cited by exact path/section to a file you should open:

- **Doctrine, 9-class failure taxonomy, finding schema, satisfaction criteria, RESUME
  mechanics, execution DAG, and judgment rubrics** all live in
  `00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md`. Open it now and keep it open.
  This brief does NOT re-derive or paraphrase any of that content — it cites CHARTER.md
  section numbers. If anything below seems to assume knowledge not present in this file,
  it is in CHARTER.md.
- **This lane's protocol** (what Lane 2 specifically does) is transcribed IN FULL in
  §1 below, verbatim from the master plan's own words — not summarized.
- **This lane's extensions** — the conductor+fresh-sub-agent-per-question execution mode,
  the P-12 manual demand-side-retrieval mode, and the verifier-sample re-grade — are
  MANDATORY additions to the base protocol, specified in full in §2 below.
- **This lane's ledger** is `00_ARCHITECTURE/llm_consumption_audit/ledgers/questions.jsonl`
  — every row you touch, mark, or skip is a row in that file. Completeness is a count
  query against it (§6).
- **This lane's checkpoint** is `00_ARCHITECTURE/llm_consumption_audit/state/LANE2.md`,
  owned exclusively by this lane's conductor (§7).

## 1. The protocol — TRANSCRIBED IN FULL, verbatim from
`LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md` §5 Lane 2 (lines 167-175)

> ### Lane 2 — Question-first coverage matrix (GATED on native question list)
> ~60–80 acharya question types (marriage timing, progeny, health crisis windows,
> litigation, property, foreign settlement, muhurta, remedial priority, career pivots,
> wealth magnitude, death-of-parent timing, spiritual inflection, …) — list to be fixed in
> the native↔Fable 5 debate. Each attempted end-to-end exactly as the consuming LLM would.
> Graded NOT "did tools return rows" but "did the retrievable evidence suffice to answer at
> acharya grade" (§J). Every chain break is a finding. This is the unknown-unknowns lane —
> questions no tool was designed for. Timing questions deliberately include gochara
> composition (dasha × transit × natal, double-transit) to expose §10 gap 8.

**Note on the gate reference above ("GATED on native question list"):** this gate has
been DISCHARGED. The native↔Fable 5 debate closed with the plan's own Appendix C (see
`LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md` Appendix C, lines 599-647, native-approved
2026-07-11), and that Appendix C has been transcribed verbatim into the ledger
`questions.jsonl` by the Brief Foundry's ledger-build pass. **Do not re-litigate the
question list.** If you believe a question type is missing, log it as a class-9
(UNGOVERNED JUDGMENT) finding per CHARTER.md §2 and proceed with the ledger as frozen —
do not silently add or drop rows.

**Note on the "§J" reference above:** the plan's own text cites "§J" for the
evidence-sufficiency grading approach; the master plan document as consolidated does not
carry a section literally labeled "§J" (a numbering artifact from an earlier draft). The
operational rubric that fulfills this same grading intent is CHARTER.md §7.3
("Evidence-sufficiency grading scale (Lane 2)") — use that rubric. This substitution is
recorded here, not silently made, per the anti-softening discipline.

**Known ledger surprise (already flagged by the foundry, not yet resolved — read before
you start):** the ledger's HEADER row documents an arithmetic inconsistency in the plan's
own Appendix C: the plan's Lane 2 preamble states "~60–80 acharya question types" and the
Appendix C heading states "76 types," but the verbatim Appendix C enumeration (groups A
through L, summed) is 82 distinct question types, not 76. The ledger was built against the
**actual 82-type enumeration** (fidelity to the transcribed text over the summary count),
yielding 82 × {narrow, broad} × 2 charts = 328 question-trace rows. Do not "correct" the
ledger down to 76 or up/down to reconcile the arithmetic — the ledger is frozen at 328
rows per the Brief Foundry's stated resolution. If you want to dispute this, log it as a
class-9 finding and continue against the frozen ledger.

## 2. Mandatory extensions (native directive, this brief carries them in full)

### 2.1 — Conductor + fresh-sub-agent-per-question protocol

This lane does NOT run as one session holding all 328 rows. It runs as a
**CONDUCTOR + WORKER-SWARM**, per CHARTER.md §6 (execution DAG, verbatim from plan
§12.7) and the sharding rule stated there: *"Lane 2 by question rows (concurrency-capped
batches, e.g. 5–10 workers, the conductor throttles to subscription limits)."*

Concretely for Lane 2:
- The **conductor** session owns `questions.jsonl` and `state/LANE2.md`. It never itself
  attempts to answer a question end-to-end — it shards, spawns, collects, merges, and
  checkpoints.
- Each **worker** is a FRESH sub-agent, spawned per question-trace row (or a small batch
  of rows — see §5 concurrency cap below), receiving ONLY: (a) the relevant excerpt of
  CHARTER.md (doctrine §1, taxonomy §2, finding schema §3, rubric §7.3), (b) this brief's
  §3 (P-12 manual mode) and §4 (evidence-plan-before-any-call discipline), and (c) its
  assigned row(s) from `questions.jsonl`. A worker never receives the full audit context,
  the other lanes' state, or the rest of the question ledger — full attention on its
  assigned row(s), zero context decay from carrying unrelated material.
- Each worker attempts its assigned question(s) end-to-end EXACTLY as the consuming LLM
  would (plan line 171, verbatim: "Each attempted end-to-end exactly as the consuming LLM
  would") — i.e., through the same MCP tool surface any live consumption session would use,
  not through DB access (Lane 2 is a public-MCP-channel lane per plan §3: "All other lanes
  consume the public MCP channel exclusively" — Lane 2 is not Lane 5 or Lane 8, it does
  NOT get DB access).
- Each worker writes its OWN shard trace file and nothing else — see §5 merge protocol.
  Workers never write `state/LANE2.md` directly and never write another worker's shard file.

### 2.2 — P-12 manual mode, in full (plan line 359, the P-12 row of the §9 table)

This is the single most load-bearing extension in this brief. Transcribed verbatim from
`LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md` §9, table row P-12 (the "audit hook" column, which is
Lane 2's operating instruction):

> Lane 2 executor RUNS in exactly this mode manually: writes the evidence plan BEFORE any
> call, tracks acquisition, and logs every place the capability map knowledge was
> missing/wrong and every plan item no tool could satisfy. Lane 1b's Concept×Retrievability
> matrix IS the capability map's seed data

And the fuller P-12 gap description (same table, "Gap"/"Essence" columns, transcribed in
full, since it explains WHY the mode works this way):

> **P-12 | Demand-side retrieval planner + capability map + acquisition tracker** (native,
> review round 1 — flagship capability). The LLM must NOT be driven by whatever data
> arrives (supply-side). Per question it generates an a-priori extensive evidence plan from
> the shastra — narrow question → narrow but comprehensive item list; broad question → wide
> comprehensive list — then retrieves against the plan, TRACKS received-vs-needed, and
> keeps seeking through tools/services until each item is fetched or honestly exhausted.
> Anything extra the tools volunteer is bonus, never the frame. Requires: (a) a
> machine-readable **capability map** — concept → which tool/service serves it (does not
> exist today; MCP_USAGE_GUIDE is prose, not keyed by concept); (b) an in-conversation
> **acquisition tracker** (does not exist); (c) the per-question evidence-plan generator
> (P-10's contract is its input). Ensures every essential factor — critical or tail —
> enters the synthesis.

**Operationalized for each worker, in order, per assigned question row:**

1. **Evidence plan — written BEFORE any tool call.** Before making a single MCP call, the
   worker writes out (in its shard trace file) the full a-priori evidence item list it
   believes an acharya-grade answer to this question requires — derived from the shastra
   concept inventory and the question's narrow/broad variant (per the ledger's
   `variant` field: `narrow` → narrow-but-comprehensive list; `broad` → wide comprehensive
   list). This plan is written from domain knowledge of what SHOULD be needed, not from
   what the worker already knows the system can serve — do not pre-trim the plan to only
   things you expect to succeed. Each plan item gets a short concept label (e.g. "D9 navamsa
   dignity of 7th lord", "current Venus MD/AD window", "Kuja dosha membership + cancellation
   grounds").
2. **Acquisition tracking — received vs. needed.** As the worker makes calls, it updates a
   running table in the shard trace: plan item → attempted (Y/N) → tool(s) called → received
   (Y/N/PARTIAL) → evidence excerpt or reason not received. This table IS the acquisition
   log the P-12 row requires.
3. **Class-9 improvisation logging — every time judgment is exercised.** Per CHARTER.md §2
   (class 9, UNGOVERNED JUDGMENT) and plan §6 ("Improvisation log (class 9): the executor
   logs EVERY act of ungoverned judgment it performs while consuming — method/krama choice,
   conflict adjudication, silent question decomposition, taxonomy→life-language
   translation"), the worker logs EVERY instance of: choosing a method/krama the system did
   not prescribe; deciding how to resolve two conflicting pieces of evidence; silently
   splitting a compound question into sub-questions; translating a raw taxonomy label into
   life-language without a served translation. This is not optional and not sampled — every
   single occurrence, logged in the shard trace, tagged class-9.
4. **Capability-map gap logging.** Every place the worker did not know which tool/service
   would serve a plan item (had to guess, search, or trial-and-error) is logged as its own
   line — this is the raw material for the P-12 capability map that does not yet exist. Log
   both "guessed right eventually" and "guessed wrong / gave up" cases.
5. **Exhaustion discipline.** A plan item is only marked "honestly exhausted" (not received)
   after the worker has tried every tool/service it can identify as plausibly relevant — not
   after one failed call. Premature exhaustion (giving up after one try) is itself a
   class-9 finding against the worker's own conduct — log it if it happens.
6. **Evidence-sufficiency verdict.** Once the plan is exhausted (received, partial, or
   honestly-not-received for every item), the worker applies CHARTER.md §7.3's 4-point scale
   (SUFFICIENT / SUFFICIENT-WITH-GAPS / INSUFFICIENT / UNANSWERABLE-BY-DESIGN) to the
   question as a whole, and root-causes every gap into one of the CHARTER.md §2 nine
   failure classes (or UNREACHABLE-BY-NONEXISTENCE per CHARTER.md §1 doctrine §2.1, for
   canon concepts the system never computed at all).
7. **Bonus-data note.** Anything the tools volunteered that was not on the evidence plan is
   noted as "bonus" and must NOT be used to inflate the sufficiency verdict — per P-12,
   "Anything extra the tools volunteer is bonus, never the frame."

### 2.3 — Verifier-sample re-grade (~15%)

After the conductor merges all worker shard traces (§5), the conductor samples
approximately **15% of the 328 traces** (≈49 traces; round to the nearest whole trace,
sample across question groups A–L and across both charts and both variants — do not
cluster the sample in one group) and spawns **independent verifier workers** — fresh
sub-agents that did NOT produce the original trace — to re-grade those sampled traces
against the same rubric (CHARTER.md §7.3) and the same P-12 discipline (§2.2 above),
working from the SAME evidence-plan-before-any-call method independently (i.e. the
verifier does not read the original worker's evidence plan before writing its own — it
independently derives a plan, then compares against the original's plan and verdict as a
final step, logging any material divergence as its own finding).

Per CHARTER.md §5 (RESUME protocol): "**Verifier sampling** (e.g. Lane 2's ~15% re-grade)
runs as parallel verifier workers and checkpoints into the same shard discipline —
verifier state is not a separate untracked side-channel." Concretely: verifier re-grades
are written to `state/LANE2/verifier-shard-<id>.md` (their own namespace under the shard
convention in §5), never overwriting the original worker's shard file. A verifier
disagreement with the original verdict does NOT silently overwrite the original — both are
recorded, and a verdict divergence above a trivial threshold (any change in
SUFFICIENT/SUFFICIENT-WITH-GAPS/INSUFFICIENT/UNANSWERABLE-BY-DESIGN category, not just
wording) is itself logged as a Lane 2 process finding (candidate class 9, since it likely
indicates rubric ambiguity — ungoverned judgment at the rubric-application level).

### 2.4 — Item-0 broadcast: timing verdicts annotated, not blocked

Per CHARTER.md §6 (execution DAG, verbatim): *"Item-0's result is broadcast to Lanes 2/7
mid-flight (timing verdicts annotated, not blocked)."* Concretely for Lane 2: this lane's
conductor does NOT wait for `ITEM0_R45_TRIAGE.md`'s execution session to complete before
starting or continuing. Any of this lane's question rows that touch timing/temporal
engines — every group has "≥1 timing question" by design rule (Appendix C design rules,
transcribed at the end of §1's ledger note above) and the entire **K. Kala-vidhi group
(K1–K8)** is timing-native — proceed on schedule. When/if the Item 0 broadcast JSON
(format specified in `ITEM0_R45_TRIAGE.md` §6) becomes available, the conductor:
1. Reads the broadcast's `verdict` field (`WRITER_NO_OP | SERVING_PATH_BUG |
   PARTIAL_SERVING_PATH_BUG | CHART_SPECIFIC_BUILD_GAP`) and `implication_for_rebuild`
   field.
2. Annotates every already-completed AND every not-yet-started timing-question trace
   (question_code in K1–K8, plus any other row a worker separately flagged as
   temporal-engine-dependent) with the broadcast verdict, WITHOUT re-running the trace.
3. If the broadcast arrives AFTER a timing trace already completed and graded, the
   annotation is appended to that trace's record (not a re-grade) — the evidence-
   sufficiency verdict stands as originally graded by the worker at the time it ran; the
   annotation is metadata explaining WHY, not a correction.
4. If the broadcast has not yet landed when a timing trace is graded, the trace is marked
   `timing_verdict: "unverified — pending ITEM0_R45_TRIAGE broadcast"` per
   `ITEM0_R45_TRIAGE.md` §6's own instruction ("Lanes 2 and 7 should treat an unresolved
   Item 0 ... as 'timing unverified' and flag any R-39/R-40/R-45-linked finding they
   produce as provisional pending this broadcast").

## 3. Ledger — the executor marks rows against this ledger

**Path:** `00_ARCHITECTURE/llm_consumption_audit/ledgers/questions.jsonl`

Format: JSONL, one JSON object per line. Row 1 is a `HEADER` row (metadata + the
82-vs-76 discrepancy note — read it, do not treat it as a data row). Rows 2–329 are the
328 question-trace rows, one per {question_code × variant × chart_id} combination, each
carrying at minimum: `row_id`, `question_code`, `question_group`, `question_text`,
`variant` (`narrow`|`broad`), `chart_id`, `status` (starts `pending`).

**Marking discipline (mandatory — this is what makes completeness a count query per §6
below):** for every row a worker completes, it (or the conductor, on merge) updates that
row's `status` field in `questions.jsonl` to one of: `sufficient` | `sufficient_with_gaps`
| `insufficient` | `unanswerable_by_design` | `in_progress` | `pending`. Do not invent new
status strings. Do not leave a row `pending` after a worker has touched it — `in_progress`
is for rows a worker has started but a session boundary interrupted (see RESUME, §7).

The conductor is the ONLY actor that writes to `questions.jsonl` itself (workers report
their row's verdict in their shard trace file; the conductor applies it to the ledger on
merge — this avoids concurrent-write contention on a single shared file, consistent with
CHARTER.md §6's "no write contention" rule).

## 4. Rubrics — reference by name (do not re-derive)

This lane's primary rubric is **CHARTER.md §7.3 — "Evidence-sufficiency grading scale
(Lane 2)"**. It is DRAFT pending Cowork ratification (CHARTER.md §7 header: "DRAFT —
Cowork review gate (Fable 5 + native) must ratify before execution... No lane may treat
these as final without that ratification"). Confirm ratification status before this lane's
execution session begins; if unratified, proceed only if explicitly instructed to run
pre-ratification (log this as a process note, not silently).

Secondary rubrics this lane also applies, by reference:
- **CHARTER.md §7.1 — "Usable form" rubric** — apply to any individual payload received
  mid-acquisition that looks unusable (unresolved IDs, truncated narration, undisclosed
  budget ceilings, drowned-in-trivia) even if the overall question verdict ends up
  SUFFICIENT — a usable-form failure on one plan item is its own finding regardless of the
  question's aggregate grade.
- **CHARTER.md §7.2 — "Synthesizability-as-received" rubric** — apply on first contact
  with any tool a worker has not used before within its own trace, exactly as Lane 1a would,
  since Lane 2 workers are consuming tools "exactly as the consuming LLM would" (plan line
  171) and first-contact quality is part of that experience.

All rubrics are named, not restated, per this brief's own self-containment discipline —
open CHARTER.md §7 for the full text.

## 5. Swarm decomposition (plan §12.7 — MANDATORY section)

**(a) Conductor + worker pattern.** One conductor session (this lane's owner of record)
holds `questions.jsonl` and `state/LANE2.md` for the full lifetime of the lane. It never
executes a question trace itself. It spawns fresh worker sub-agents, each scoped to a
small batch of question rows, waits for/collects their shard trace files, merges results
into `questions.jsonl` and `state/LANE2.md`, and repeats until the ledger is exhausted or
explicitly checkpointed for a later resume. A separate, later wave of independent
verifier-worker sub-agents (§2.3) re-grades a ~15% sample after the primary merge.

**(b) Shard key.** Question rows in concurrency-capped batches of 5–10 workers. Each
worker's shard is a contiguous or conductor-chosen set of `row_id`s from
`questions.jsonl` — recommended default: 1 question-trace row (i.e. one {question_code ×
variant × chart_id} combination) per worker for maximum attention-per-question, batched
only insofar as the conductor launches 5–10 workers CONCURRENTLY (each on its own single
row or small row-set), not insofar as any one worker holds multiple unrelated rows in its
own context.

**(c) Concurrency cap + throttling rule.** The conductor runs **5–10 concurrent workers**
at any given time (the plan's own stated figure, verbatim: "concurrency-capped batches,
e.g. 5–10 workers, the conductor throttles to subscription limits"). The conductor
monitors for rate-limit / subscription-usage-window signals (e.g. throttling errors,
usage-window exhaustion notices) and, on any such signal, reduces the number of
concurrently in-flight workers (down toward the 5 floor, or pauses new spawns entirely
until the window resets) rather than queuing indefinitely against a hard wall. There is no
call/time budget cap otherwise (plan §3: "Budget | OPEN — no call/time cap, as long as
value is added. Checkpointing mandatory") — the cap in this section is a CONCURRENCY
throttle, not a total-work ceiling.

**(d) Merge protocol.** Workers write ONLY their own shard trace file, at
`00_ARCHITECTURE/llm_consumption_audit/state/LANE2/shard-<row_id>.md` (or
`shard-<batch_id>.md` if a worker is assigned a small batch — batch IDs are conductor-
assigned and unique). A worker NEVER writes `questions.jsonl`, NEVER writes
`state/LANE2.md`, and NEVER writes another worker's shard file. The conductor ALONE reads
completed shard files and merges: (i) updates the corresponding row(s)' `status` field in
`questions.jsonl`; (ii) appends any findings surfaced to the running findings log (per
CHARTER.md §3 finding schema — machine-readable, one record per finding); (iii) updates
the row/shard counts in `state/LANE2.md`. No shared-file writes happen from any worker —
this eliminates write contention entirely, consistent with CHARTER.md §6's stated
guarantee. Verifier workers follow the identical discipline, writing to
`state/LANE2/verifier-shard-<row_id>.md` (§2.3), never touching a primary shard file.

**(e) Per-shard RESUME semantics.** Exact pointer format: `state/LANE2.md` records, per
shard, `last_completed_shard_id: shard-<row_id or batch_id>` alongside `rows_done` /
`rows_total` / `findings_count` (per CHARTER.md §5's AUDIT_STATE index pattern, applied at
the LANE2 shard level). A resumed conductor session:
1. Reads `state/LANE2.md` for `last_completed_shard_id` and `rows_done`/`rows_total`.
2. Cross-checks against `questions.jsonl` directly (count rows where `status != "pending"`
   and `status != "in_progress"`) — the ledger is the ground truth if the two ever
   disagree (a torn/partial checkpoint is itself a defect per CHARTER.md §5's atomicity
   contract, and is logged as such, not silently trusted).
3. Any row left `in_progress` at the point of interruption is treated as NOT done — its
   shard is re-spawned to a fresh worker from scratch (evidence plans are cheap to
   regenerate and re-using a partially-acquired trace risks inheriting an
   incompletely-logged acquisition table).
4. Resumes spawning new worker batches from the first `pending` row_id in `row_id` sort
   order (ledger rows are already zero-padded and sequential, e.g. `0001_...` through
   `0328_...` — sort order is lexical == numeric order), maintaining the same 5–10
   concurrency cap, until the ledger is exhausted.
5. Regeneration of `state/LANE2.md` itself is idempotent (derived purely from shard-file
   presence + `questions.jsonl` status counts), so if two conductor instances somehow both
   attempt a checkpoint, re-deriving from source is always safe — per CHARTER.md §5's
   idempotent-regeneration guarantee.

## 6. Per-lane coverage self-declaration template (TAP-9 style)

Every surface this lane is responsible for MUST appear in this table at lane close, either
`audited` or `deferred` with a reason — no surface may be silently absent. Fill in at
consolidation:

| surface | status (audited/deferred) | reason-if-deferred |
|---|---|---|
| Question group A (Deha & Ayus, A1–A6) × {narrow,broad} × 2 charts | | |
| Question group B (Buddhi & Svabhava, B1–B6) × {narrow,broad} × 2 charts | | |
| Question group C (Vidya, C1–C5) × {narrow,broad} × 2 charts | | |
| Question group D (Karma & Vritti, D1–D9) × {narrow,broad} × 2 charts | | |
| Question group E (Dhana & Sampatti, E1–E8) × {narrow,broad} × 2 charts | | |
| Question group F (Kutumba & Vivaha, F1–F10) × {narrow,broad} × 2 charts | | |
| Question group G (Santana, G1–G6) × {narrow,broad} × 2 charts | | |
| Question group H (Bandhu, Ripu & Vyavahara, H1–H6) × {narrow,broad} × 2 charts | | |
| Question group I (Sthana & Yatra, I1–I6) × {narrow,broad} × 2 charts | | |
| Question group J (Dharma & Moksha, J1–J6) × {narrow,broad} × 2 charts | | |
| Question group K (Kala-vidhi, K1–K8) × {narrow,broad} × 2 charts [timing-native; carries Item-0 broadcast annotation] | | |
| Question group L (Meta & whole-chart, L1–L6) × {narrow,broad} × 2 charts [Lane-7 feeders] | | |
| Verifier-sample re-grade (~15% ≈ 49 traces, spread across A–L, both charts, both variants) | | |
| Class-9 improvisation log completeness (every worker's shard trace carries its own log section, even if empty) | | |
| Capability-map gap log completeness (every worker's shard trace carries its own log section, even if empty) | | |
| Item-0 broadcast annotation applied to all K-group + any flagged temporal-dependent rows | | |

## 7. Checkpoint / RESUME instructions (top-level, lane-owned)

**Checkpoint file:** `00_ARCHITECTURE/llm_consumption_audit/state/LANE2.md` — owned
EXCLUSIVELY by this lane's conductor. No other lane's conductor, and no Lane 2 worker,
writes to this path.

**Regeneration discipline:** atomic, idempotent regeneration. Every checkpoint write
regenerates the file's full content FROM the source of truth (`questions.jsonl` status
counts + the set of shard files present under `state/LANE2/`), never a hand-patched diff
of the previous checkpoint. This makes checkpointing safe to re-run, safe to interrupt
mid-write (a torn write is detectable and simply re-derived on the next regeneration —
not silently trusted), and safe under the "any conductor resumes from its shard"
guarantee in CHARTER.md §5.

**RESUME pointer:** `last_completed_shard_id` — the `row_id` (or `batch_id`) of the most
recently fully-merged shard, in the sort order described in §5(e) above. A fresh/resumed
session reads this pointer plus the `rows_done`/`rows_total`/`findings_count` fields,
cross-verifies against `questions.jsonl` directly (ledger status counts are the ground
truth on any disagreement), and continues spawning worker batches from the first
non-`pending`-excluded row after the pointer — never re-doing a fully-merged shard, never
silently skipping an unmerged one.

**Minimum `state/LANE2.md` content (regenerate every checkpoint):**
```
lane: LANE2
status: <NOT_STARTED | IN_PROGRESS | VERIFIER_PASS | COMPLETE>
rows_total: 328
rows_done: <n>
rows_in_progress: <n>
rows_pending: <n>
findings_count: <n>
class9_log_entries: <n>
capability_gap_log_entries: <n>
last_completed_shard_id: <row_id or batch_id>
verifier_sample_size: <n>            # target ~49 (15% of 328), fill once sampled
verifier_reraded: <n>
verifier_divergences: <n>
item0_broadcast_received: <true|false>
item0_broadcast_verdict: <verdict string, once received>
```

## 8. Deliverable spec — exactly what this lane produces

Cross-referenced against plan §7 (deliverables, lines 307-323):

- **Primary deliverable — plan §7 item 5**: *"The question-coverage matrix (Lane 2) —
  retained as a standing asset; it becomes the future acceptance surface, superseding the
  38-item battery's role."* Concretely: the fully-merged, fully-graded
  `questions.jsonl` (all 328 rows carrying a final `status` + evidence-sufficiency verdict
  + finding refs), plus this brief's §6 coverage self-declaration table filled in, plus a
  compiled matrix view (question × variant × chart × verdict × finding-count) suitable for
  direct consumption by the Fable 5 planning session and by any future acceptance-test
  run.
- **Secondary deliverable — plan §7 item 8**: *"Lane 2 evidence-plans + acquisition logs
  (the P-12 requirements corpus)."* Concretely: the full set of per-question evidence
  plans and received-vs-needed acquisition tables produced under §2.2 above, retained as
  the raw corpus the P-12 capability-map + acquisition-tracker design work will consume.
  These live in the merged shard traces (do not discard them after merge — they are a
  deliverable in their own right, not scratch work).
- **Findings contribution**: every finding this lane surfaces (evidence-sufficiency gaps,
  class 1-9 root-causes, class-9 improvisation log entries, capability-map gaps) feeds
  the shared machine-readable findings JSON (plan §7 item 2 / CHARTER.md §3) via the
  conductor's merge step — Lane 2 does not maintain a separate findings file; it appends
  to the shared one per the finding schema.
- **Calibration-anchor contribution**: per CHARTER.md §3 ("Known-findings anchor set:
  R-37..R-48 ... serve as calibration anchors — the audit MUST independently rediscover
  them via its lanes; any it misses indicates a lane-coverage hole"), Lane 2's timing
  questions (group K, plus D3/D4/E3/F1/F5/G2 and any other row that surfaces a timing
  gap) are a primary channel through which R-39/R-40/R-45 (and any others reachable via a
  question-first path) should be independently rediscovered. Log explicitly whether each
  reachable anchor was, in fact, rediscovered via this lane — a miss is itself flagged at
  consolidation, not silently absorbed.

## 9. Explicit non-scope (Brief Foundry discipline)

This brief specifies Lane 2's execution. It does not itself run any question trace, does
not itself grade any evidence, and does not fix anything found. It is a specification for
a conductor+swarm execution session to follow. Ratification of the DRAFT rubrics
(CHARTER.md §7) happens at the Cowork review gate, not in this brief. Any dispute about
the question list's frozen 328-row scope, or about the "§J" substitution noted in §1, is
logged as a class-9 finding for the consolidation session — this brief does not resolve
either dispute itself.

*End of LANE2_QUESTION_MATRIX (Brief Foundry output, READY FOR EXECUTION pending Cowork
rubric ratification per CHARTER.md §7).*
