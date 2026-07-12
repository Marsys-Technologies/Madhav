---
title: Lane 5 — Wire-fidelity diff (the DB-access lane)
canonical_id: LANE5_WIRE_FIDELITY_BRIEF
version: 1.0
status: DRAFT (Section 7 rubrics gated on Cowork ratification — see Charter §7)
source_plan: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md (§5 lines 192-196; §3 line "DB access")
charter: 00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md (canonical_id LLM_CONSUMPTION_AUDIT_CHARTER)
generated_by: Brief Foundry session, 2026-07-11 (recovery run — prior swarm attempt failed on a
  transient API connection error; this is a clean regeneration, not a continuation of partial
  output)
---

# Lane 5 — Wire-fidelity diff (the DB-access lane)

This brief is SELF-CONTAINED: a fresh session with no other context can execute Lane 5
from this file alone plus the two artifacts it cites by reference (the Charter, for
doctrine/taxonomy/finding-schema/satisfaction-criteria/rubrics; and its own ledger file,
`ledgers/value_families.jsonl`). Do not re-derive Charter content — cite it. Do not skip
reading this brief's transcribed protocol below on the theory that it can be paraphrased
from memory; the plan text is reproduced in full below and every sentence in the cited
line range (192-196) must be present here, never softened.

## 0 — Charter reference (read first)

Cite `00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md`, canonical_id
`LLM_CONSUMPTION_AUDIT_CHARTER`, for:
- **Doctrine** — Charter §1 (plan §2 + §2.1, verbatim): the gap definition ("Data that
  exists but does not arrive is absent. Data that arrives wrong, or twice contradicting
  itself, or as 300 unranked duplicates, or as raw IDs with no text, or as an un-budgeted
  181KB dump, is a gap of equal standing") — Lane 5 is the lane that directly instruments
  this definition by comparing table contents to wire contents; and the examples-are-
  illustrative rule (§2.1) — the fact families sampled below are illustrative starting
  points, never a ceiling on what Lane 5 may investigate.
- **9-class failure taxonomy** — Charter §2 (plan §4, verbatim). Every Lane 5 finding gets
  exactly one primary class. Lane 5's own subject matter maps most directly onto class 1
  (UNREACHABLE — field dropped entirely), class 6 (UNUSABLE FORM — trims cutting meaning
  mid-narration), and class 7 (DROWNED — budget ceilings silently discarding decisive
  rows), but any of the 9 classes may apply to a given diff; do not force-fit.
- **Finding schema** — Charter §3 (plan §6, verbatim): reproducible call, verbatim evidence
  excerpt, primary failure class, severity, suspected layer, dedupe check against the
  register (incl. anchor rows R-37..R-48), plus identity/linkage metadata for the Fable 5
  machine-readable findings JSON.
- **Satisfaction criteria** — Charter §4 (plan §8, verbatim). Lane 5 contributes primarily
  to criterion 1 (census completeness — the value-family enumeration itself is DB-derived
  and exhaustive) and criterion 5 (plannability — every finding machine-readable with
  class + suspected layer + reproducible evidence).
- **RESUME protocol** — Charter §5.
- **Execution DAG / swarm model** — Charter §6 (plan §12.7, verbatim) — this brief's
  Section 8 below instantiates it concretely for Lane 5's per-fact-family shard.
- **Rubric** — Charter §7.1, "Usable form" rubric — this is the rubric Lane 5 applies to
  grade every wire-side value against its table-side original. Charter §7.1 is DRAFT
  pending Cowork ratification per the Charter's own gating note; Lane 5 may not treat it
  as final without that ratification, and must flag any grading done against it as
  provisional until ratification lands.

## 1 — Protocol, transcribed in full (plan §5 lines 192-196)

The following is TRANSCRIBED VERBATIM from the governing plan. Do not paraphrase; do not
soften any clause.

> ### Lane 5 — Wire-fidelity diff (the DB-access lane)
> For sampled fact families: read-only comparison of table contents vs what arrives over the
> wire. Fields dropped in pivots, subjects merged across categories (KP-6), trims cutting
> meaning mid-narration (R-32), budget ceilings silently discarding decisive rows. Direct
> implementation of the native's "data exists but is not retrieved" concern.

Unpacked, without softening any clause, this protocol commits the executor to four
specific, non-optional failure modes to hunt for on every sampled fact family, each with
its own named anchor:
1. **Fields dropped in pivots** — a value present in the source table's row is silently
   absent from a pivoted/reshaped wire response (no explicit "field omitted" disclosure).
2. **Subjects merged across categories** — distinct subjects (e.g., distinct fact
   categories or distinct entities) that are separate in the table get collapsed/merged
   into one wire-side bucket, losing the subject boundary (the KP-6 class, named
   explicitly in the plan — treat KP-6 as the calibration anchor for this failure mode,
   the same way R-37..R-48 anchor the taxonomy generally).
3. **Trims cutting meaning mid-narration** — a narrative/explanatory text field is
   truncated at a byte/character boundary that falls mid-sentence or mid-clause, not at a
   natural boundary (the R-32 class, named explicitly in the plan — treat R-32 as this
   failure mode's calibration anchor).
4. **Budget ceilings silently discarding decisive rows** — a response-size or row-count
   cap drops rows without disclosing that rows were dropped, and without any guarantee
   that the dropped rows were the least decisive ones (i.e., a decisive/chart-defining row
   may be silently discarded while a low-information row survives the cap).

The plan is explicit that this lane is the **direct implementation of the native's
"data exists but is not retrieved" concern** — this is not a generic QA sweep; it is the
one lane purpose-built to answer that specific native concern with read-only DB evidence,
which is why it is one of only two lanes (with Lane 8) granted DB access (see Section 0.5
below).

## 0.5 — DB access grant (plan §3, cited explicitly per task instruction)

Plan §3 "Fixed decisions" table, DB access row (verbatim): **"GRANTED, read-only (SELECT
only), for Lane 5 wire-fidelity and Lane 8 facet enumeration. All other lanes consume the
public MCP channel exclusively."**

Lane 5 is therefore one of exactly two lanes in the entire audit with a native-granted
exception to the public-MCP-channel-only rule that governs every other lane. This grant is
load-bearing for Lane 5's method: the table-side half of every diff in Section 1 above is
only possible because Lane 5 may run read-only SELECT queries directly against the
database, via the `mcp__postgres__query` tool, to establish ground truth before comparing
it to what the same fact family returns over the MCP wire.

**Absolute constraint on this grant:** SELECT only. Never issue INSERT, UPDATE, DELETE, or
any DDL statement against the database, under any circumstance, for any reason, at any
point in this lane's execution — including inside a worker sub-agent, including as part of
a "helper" query, including for cleanup. This is a read-only audit lane; the grant is
scoped exclusively to reading the current state of the tables, never to modifying it. Any
worker or conductor action that would write to the database is a protocol violation, not a
judgment call — halt and report rather than execute it.

## 2 — Ledger file (the executor's row-marking surface)

**Path:** `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/ledgers/value_families.jsonl`

This ledger already exists (built by the Foundry ledger-builder pass) with **3,058 rows**,
one row per `(table_name, family_key)` sampled fact family observed across both charts.
Each row is one JSON object, one per line (JSONL — no surrounding array, no trailing
commas). Observed schema (from the ledger's own rows):

```json
{
  "row_id": "VF-1",
  "table_name": "chart_facts",
  "family_key": "anumukha_shani_period::duration_days",
  "grain": "per-chart",
  "chart_ids_observed": [
    "482012f1-710e-4a25-994a-93821f5871aa",
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
  ],
  "source": "SELECT fact_category, fact_key, bool_or(chart_id=Abhisek), bool_or(chart_id=Abhinandan) FROM chart_facts WHERE chart_id IN (Abhisek,Abhinandan) GROUP BY fact_category, fact_key",
  "status": "pending"
}
```

**Executor obligation per row.** For every ledger row, the executor:
1. Runs the row's `source` SELECT (read-only; per Section 0.5) — or an equivalent
   read-only query scoped to the same `table_name` × `family_key` × the two in-scope
   `chart_ids_observed` — to establish the **table-side ground truth**: the exact value(s)
   this fact family holds in the database, for both charts where present.
2. Retrieves the same fact family **over the wire**, as a consuming LLM would — via
   whichever MCP tool(s) plausibly front this table/family (consult
   `CAPABILITY_MANIFEST.json` for the tool-to-table mapping where it is not obvious from
   the tool description alone).
3. Diffs table-side vs wire-side and classifies the diff, adding these fields to the row
   (the ledger's schema is extended in-place by the executor as it works; do not create a
   parallel ledger):
   - `wire_value_matches_table`: boolean — does the wire-delivered value match the
     table-side ground truth exactly (accounting only for legitimate, disclosed
     formatting transforms — never silent value changes)?
   - `failure_mode`: one of `null` (no failure), `"field_dropped_in_pivot"`,
     `"subjects_merged_across_categories"` (the KP-6 class), `"trim_cuts_meaning_mid_narration"`
     (the R-32 class), `"budget_ceiling_silently_discards_row"`, or `"other"` (with a free-text
     note) — per the four named failure modes in Section 1.
   - `failure_class`: the Charter §2 (plan §4) primary failure class (1-9) attached to
     this row if `wire_value_matches_table=false` or `failure_mode` is non-null.
   - `status`: one of `pending` → `in_progress` → `done`. Rows never silently regress from
     `done`.
4. Any row where `wire_value_matches_table=false`, or `failure_mode` is non-null, MUST be
   root-caused into exactly one Charter §2 (plan §4) failure class, with a finding record
   written per the Charter §3 finding schema, appended to
   `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` after a dedupe check against the
   existing ~200 rows (including anchor rows R-37..R-48, and specifically checked against
   the KP-6 and R-32 anchors named in the plan's own Lane 5 description).
5. **New family rows** discovered mid-execution (a fact family the DB-derived enumeration
   pass surfaces that was not in the original 3,058-row ledger) get fresh `row_id`s
   continuing the `VF-####` sequence and are graded identically — per Charter §1 / plan
   §2.1's "examples are illustrative, never limiting" doctrine, the 3,058 rows are a floor,
   not a ceiling.

**Completeness is a count query.** At any point, run a count over the JSONL (e.g. via
`jq` or Python — not literal SQL against the file itself) of `status=="done"` rows versus
total row count (3,058 + any discovered rows). This is the lane's completeness percentage
and is what makes this brief's "completeness is a count query" mandate machine-checkable
without re-reading prose.

## 3 — Rubric reference

Apply **Charter §7.1 — "Usable form" rubric** (derived from plan §4 classes 6 UNUSABLE
FORM and 7 DROWNED) whenever a diff surfaces a wire-side value that is present but
degraded rather than cleanly absent — in particular:
- Rubric point 2 ("Narration integrity") is the direct instrument for this lane's
  "trims cutting meaning mid-narration" failure mode (R-32 class).
- Rubric point 3 ("Budget proportionality") is the direct instrument for this lane's
  "budget ceilings silently discarding decisive rows" failure mode.
- Rubric point 4 ("Signal-to-trivia ratio") applies where a budget ceiling drops a
  decisive row while a low-information row survives — this is simultaneously a class 7
  (DROWNED) candidate per the rubric's own point 4/5 interaction rule.

Do not re-derive the rubric here — read it from the Charter at execution time; it is DRAFT
pending Cowork ratification per the Charter's own gating note, and Lane 5 inherits that
gate (grading against it must be flagged as provisional in the shard trace file until
ratification lands).

## 4 — Checkpoint / RESUME instructions

**State file (owned exclusively by this lane's conductor):**
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/state/LANE5.md`

Per Charter §5 (RESUME protocol, derived from plan §12 items 3-4):
- `state/LANE5.md` is a shard-index file, regenerated **atomically and idempotently** by
  the Lane 5 conductor at every checkpoint, derived purely from the current state of the
  per-shard worker trace files (Section 8 below) plus the `value_families.jsonl` ledger's
  own `status` column counts. Regeneration is a pure function of those inputs — safe to
  re-run, safe if interrupted mid-write (a torn/partial write is itself a defect per
  Charter §5's atomicity contract, not an acceptable RESUME state).
- `state/LANE5.md` content (minimum fields): per-shard (one row per fact-family shard
  dispatched so far) — shard id, shard trace file path, rows-done/rows-total for that
  shard, findings-count so far, status (`not_started` / `in_progress` / `done`), and a
  **RESUME pointer = last completed shard id** at the top of the file — i.e., which shard
  the conductor should treat as the resumption point if the lane was interrupted mid-run.
  Within a partially-done shard, the worker's own trace file carries the last completed
  `row_id` (Section 8(e)).
- **On a fresh/resumed session (this recovery run included):** read `state/LANE5.md`
  first. If it does not yet exist or is empty (as expected for this recovery — the prior
  swarm run failed on a transient API connection error before Lane 5 produced this brief,
  let alone began executing it), the lane has not started and dispatch begins from shard
  1 of the full 3,058-row ledger. For any shard marked `done`, do not re-dispatch. For any
  shard marked `in_progress` or `not_started`, dispatch (or re-dispatch) a fresh worker for
  exactly that shard, which itself resumes from its own shard trace file's last completed
  row (Section 8(e)).
- **Never** re-does completed rows; **never** silently skips undone ones — both directions
  are checked by reading `value_families.jsonl`'s `status` column directly (ground truth)
  against `state/LANE5.md`'s claims (index) — a mismatch between the two is itself flagged
  and reconciled before new dispatch, not silently trusted.
- This lane's checkpointing must be **incremental** (per Charter §3 "Checkpointing"): a
  session interruption at any point never loses completed rows already written to
  `value_families.jsonl` or to a shard trace file.

## 5 — Deliverable spec (cross-referenced to plan §7, lines 307-323)

Plan §7 lists 9 audit deliverables. Lane 5 is not named by number the way Lane 8 is
(deliverable 4) or Lane 9 (deliverable 7) or Lane 10 (deliverable 9), but it is the sole
source of ground truth for the wire-fidelity dimension threaded through the other
deliverables. Concretely, Lane 5 produces:
1. **The completed `value_families.jsonl` ledger** (all rows `status="done"`, all diff
   fields populated per Section 2 above, plus any `VF-####`-tagged discovered rows added
   under the floor-not-ceiling clause) — this is the primary data artifact.
2. **Finding records** for every diff where `wire_value_matches_table=false` or
   `failure_mode` is non-null, appended to
   `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (new, deduped rows only) per
   Charter §3 — these feed deliverable 2 (plan §7 item 2, the machine-readable findings
   JSON, the direct input to the Fable 5 planning session) and deliverable 3 (plan §7
   item 3, register appends, new rows only, deduped).
3. Lane 5's findings also feed, but Lane 5 does not own: deliverable 1
   (`LLM_CONSUMPTION_AUDIT_v1_0.md` report — Lane 5's section within it, covering the four
   named failure modes and their incidence across the 3,058 sampled families) and
   deliverable 6 (the Concept×Retrievability matrix, plan §7 item 6 — Lane 5's per-family
   `wire_value_matches_table` verdicts are direct retrievability-grade evidence for any
   family the matrix also covers).
4. Lane 5's contribution to Charter §4 satisfaction criterion 1 ("Census completeness...
   the value-family enumeration itself is DB-derived and exhaustive, never from memory")
   is satisfied when: 100% of `value_families.jsonl` rows show `status="done"`, AND every
   row with a failure pattern (`wire_value_matches_table=false` or non-null
   `failure_mode`) has exactly one Charter §2 failure class attached via its finding
   record. It contributes to criterion 5 (plannability) identically — every finding
   machine-readable with class + suspected layer + reproducible evidence, no re-derivation
   needed by the planning session.

## 6 — Per-lane coverage self-declaration template (TAP-9 style)

At lane close, the conductor emits a table with this exact column structure, one row per
audited surface, no surface omitted. The row set below is illustrative of the minimum
required grain (per-table rollup); the conductor MAY (and should) add finer rows if a
table's family count is large enough to warrant sub-breakdown, but MAY NOT collapse the
minimum grain below one row per distinct `table_name` present in the ledger:

| surface | status (audited / deferred) | reason-if-deferred |
|---|---|---|
| `chart_facts` — sampled families | | |
| `chart_dashas` — sampled families | | |
| `chart_divisionals` — sampled families | | |
| `bodha_*` tables — sampled families | | |
| `kala_*` tables — sampled families | | |
| `phala_*` tables — sampled families | | |
| `mimamsa_*` tables — sampled families | | |
| KP-6 subject-merge anchor class — rediscovery check | | |
| R-32 mid-narration-trim anchor class — rediscovery check | | |
| Budget-ceiling-silent-discard failure mode — coverage | | |
| Discovered fact families beyond the 3,058-row floor (if any) | | |

Every row must be marked `audited` or `deferred`; a `deferred` row without a stated reason
fails Charter §4 satisfaction criterion 4 (coverage honesty) and the lane does not close.
The conductor fills in the exact `table_name` values present in `value_families.jsonl`
(the rows above are the known table families as of this brief's writing; if the ledger
contains additional distinct `table_name` values, add a row per additional table before
declaring this section complete).

## 7 — Swarm decomposition (MANDATORY; plan §12.7)

This section specifies Lane 5's instantiation of the Charter §6 execution DAG's
conductor+worker-swarm pattern, exactly as plan §12.7 requires every phase and lane to
run.

**(a) Conductor + worker pattern.** Lane 5 runs as one CONDUCTOR session plus a swarm of
WORKER sub-agents. The conductor owns the lane's ledger (`value_families.jsonl`) and state
index (`state/LANE5.md`); it shards the 3,058-row workload by fact family (Section 7(b)
below), spawns a fresh sub-agent per shard (each worker receives ONLY the Charter excerpt
it needs — doctrine, taxonomy, finding schema, and the Charter §7.1 rubric — plus this
brief's Sections 1-3 above and its own single shard's row set from
`value_families.jsonl`; full attention, zero context decay, no need to hold the other
shards' rows in context). Workers execute, per assigned row: the read-only table-side
SELECT (Section 0.5), the wire-side MCP retrieval, the diff and classification (Section
2), populate their assigned ledger rows, write findings, and produce a shard trace file.
The conductor collects all shard traces, merges them into `state/LANE5.md`, and updates
lane-level status.

**(b) Shard key.** **Per fact family** — this is the plan's own stated sharding for Lane 5
(§12.7 "Intra-lane sharding": "Lane 5 by fact family"). Concretely, each worker's shard is
a contiguous batch of `value_families.jsonl` rows grouped so that no single fact family
(same `table_name` × `family_key` pair, potentially spanning both charts'
`chart_ids_observed`) is ever split across two workers — a family's table-side query and
its wire-side retrieval for both charts stay together in one worker's shard, since the
diff is only meaningful when both charts' evidence for that family is assembled by the
same worker. The conductor batches shards at a size that keeps worker context light (e.g.
on the order of tens to low hundreds of rows per shard, batched by `table_name` to keep
each shard's read-only SELECT surface coherent) — exact batch size is a conductor
judgment call, logged in `state/LANE5.md`, not fixed by this brief.

**(c) Concurrency cap + throttling rule.** The conductor runs **5-10 concurrent workers**
at any one time (subscription-limit-bound, per plan §12.7's "concurrency-capped batches,
e.g. 5-10 workers, the conductor throttles to subscription limits" standard, stated there
for Lane 2 and adopted here identically for Lane 5's per-fact-family shard pool).
Concretely: the conductor dispatches workers in waves of up to 10, and throttles (reduces
the in-flight count, inserts a wait, or retries with backoff) on any rate-limit signal it
receives from the harness, from the `mcp__postgres__query` tool, or from any other MCP
tool surface the workers call — this includes the class of transient API connection error
that caused the prior swarm run to fail before this brief was written; a worker or
conductor that hits such an error retries with backoff rather than treating it as a
lane-level failure. No more than 10 shards are ever in-flight simultaneously; the
remaining shards queue until a slot frees.

**(d) Merge protocol.** Workers write ONLY their own shard trace file at
`state/LANE5/shard-<id>.md` (shard id = a stable identifier the conductor assigns at
dispatch time, e.g. `chart_facts-0001` or a sequential `S###` — recorded in
`state/LANE5.md` at dispatch so the mapping from shard id to row range is always
recoverable) — **never** a shared file. Workers append their graded rows directly to
`value_families.jsonl` (each row keyed by its unique `row_id`, so concurrent appends from
different workers touch disjoint keys — no write contention on a per-row basis) and write
findings to their own trace file, not directly to the shared defect register. The
conductor ALONE reads all shard traces plus the ledger's current state and merges into
`state/LANE5.md` (the index) and, at lane-close, performs the single dedupe-and-append
pass into `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (register writes are
conductor-only, precisely to make the dedupe-against-~200-existing-rows check in Charter
§3 a single serialized operation rather than a race between concurrent workers). No
worker writes to a file another worker also writes to; no worker writes to the shared
state index or the shared register.

**(e) Per-shard RESUME semantics.** Each worker's trace file (`state/LANE5/shard-<id>.md`)
records, at minimum: the shard id, the ordered list of `row_id`s (`VF-####`) it has
completed so far, and an explicit **RESUME pointer** field of the exact form
`resume_after_row_id: VF-####` (the `row_id` of the last ledger row this shard fully
graded — `wire_value_matches_table`, `failure_mode`, `failure_class` where applicable, and
`status="done"` all set — before any interruption). A re-dispatched worker for an
already-partially-done shard reads its own trace file, finds `resume_after_row_id`, and
continues grading from the next `row_id` in its shard's row set (sorted by the ledger's
original row order) — it never re-grades rows at or before the pointer, and never skips
rows after it. If a shard trace file does not yet exist for a shard (as is the case for
every shard at the start of this recovery run), the worker starts fresh with
`resume_after_row_id: null` (equivalent to "before the first row of this shard").

---

*End of Lane 5 brief v1.0. Self-contained per Brief Foundry instruction: charter-by-
reference for doctrine/taxonomy/schema/criteria/rubrics; full transcription of plan §5
Lane 5 (lines 192-196) and plan §3's DB-access grant in Sections 1-0.5 above; ledger,
rubric reference, checkpoint/RESUME, deliverable spec, coverage self-declaration, and
mandatory swarm decomposition in Sections 2-7. Written as a clean recovery regeneration
after the prior swarm run failed on a transient API connection error before this brief
existed — no partial prior output to reconcile.*
