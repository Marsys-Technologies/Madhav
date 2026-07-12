---
title: Lane 10 — Promise-vs-Delivery Audit — Child Brief
canonical_id: LANE10_PROMISE_BRIEF
version: 1.0
status: DRAFT (Section 7 rubrics of the charter are gated on Cowork ratification — see below)
source_plan: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md (§5 Lane 10, lines 272-288)
charter: 00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md (canonical_id LLM_CONSUMPTION_AUDIT_CHARTER)
generated_by: Brief Foundry session, 2026-07-11
---

# Lane 10 — Promise-vs-Delivery Audit — SELF-CONTAINED CHILD BRIEF

**This brief is executable by a FRESH session that has read nothing else.** It is
self-contained: it cites the charter for doctrine/taxonomy/finding-schema/satisfaction
criteria/rubrics rather than re-deriving them, and it supplies everything else — ledger
path, protocol (transcribed in full, not summarized), extensions, deliverable spec,
coverage-declaration template, checkpoint/RESUME mechanics, and swarm decomposition —
standalone in this document.

## 0 — Charter reference (READ THIS FIRST, then return here)

Before any work, read in full:
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md`
(canonical_id `LLM_CONSUMPTION_AUDIT_CHARTER`, v1.0).

Do NOT re-derive or paraphrase these — the charter is binding by reference:
- **§1 Doctrine** (charter §1, = plan §2 + §2.1 verbatim) — the two completeness axes
  (width, depth) and the "examples are illustrative, never limiting" doctrine.
- **§2 9-class failure taxonomy** (charter §2, = plan §4 verbatim) — every finding this
  lane logs gets exactly one primary class from this list (classes 1-9).
- **§3 Finding schema** (charter §3, = plan §6 verbatim) — every finding record's
  required fields: reproducible call, verbatim evidence excerpt, primary failure class,
  severity, suspected layer, dedupe check against the register.
- **§4 Satisfaction criteria** (charter §4, = plan §8 verbatim) — all five must hold;
  criterion 5 (Plannability) is this lane's direct responsibility for its own ledger rows.
- **§5 RESUME protocol** (charter §5) — the general AUDIT_STATE / shard discipline this
  lane's RESUME mechanics (Section 5 below) instantiate.
- **§6 Execution DAG** (charter §6, = plan §12.7 verbatim) — this lane's place in the
  overall audit: Lane10-compile runs PARALLEL with every other lane during EXECUTION;
  Lane10-grade is the ONE hard sequential edge, deferred to CONSOLIDATION (see Section 3
  below — this brief governs the compile pass only).
- **§7 Judgment rubrics, subsection 7.5** ("Promise-shortfall layer attribution rules
  (Lane 10)") — DRAFT, gated on Cowork ratification (Fable 5 + native) per plan §12 item
  4 before this lane's GRADING pass may execute against it. The COMPILE pass this brief
  governs does not require rubric ratification (it is transcription + citation, not
  judgment) — see Section 3.

If the charter's `status` frontmatter is not yet "Section 7 ratified" or equivalent, this
lane's conductor may still execute the **compile** phase (Section 3, Section 12.7
`Lane10-compile`) but MUST NOT execute the **grading** phase (`Lane10-grade`) until
ratification — that phase is owned by the consolidation session regardless.

## 1 — Ledger

**Primary ledger (this lane's completeness surface):**
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/ledgers/asset_promises.jsonl`

Format: JSONL, one JSON object per row, no trailing commas, no surrounding array. As of
Brief Foundry build time it contains **67 rows** (`AP-001` .. `AP-067`), one per asset
across all five layers plus services, matching the plan's "~55 assets (9 ga_* + 14 bo_*
+ 12 ka_* + 9 ph_* + 12 mi_* + services)" scope (the ledger enumerates a few more rows
than the plan's approximate count because it splits some service surfaces individually —
treat the ledger, not the plan's "~55," as the authoritative row count).

Row schema (as built by the Foundry):
```json
{"row_id": "AP-###", "asset_id": "<asset_id>", "layer": "L0|L1|L2|L3|L4|L5|SERVICE",
 "promise_quote": "<verbatim quote or NOT FOUND>",
 "promise_source_citation": "<file:line or 'none'>",
 "asset_registry_row_present": true|false,
 "status": "pending|compiled|graded"}
```

**The executor marks rows against this ledger; completeness is a count query**:
`SELECT COUNT(*) FROM ledger WHERE status != 'pending'` (conceptually — this is a JSONL
file, not a DB table; the conductor computes the equivalent by scanning line-by-line and
checking each row's `status` field) must equal the total row count for the compile phase
to be declared complete.

**Where `promise_quote` is `"NOT FOUND"` / `promise_source_citation` is `"none"`**: this
is itself the Foundry's honest finding for that asset — the compile pass MUST NOT
silently invent a promise. Instead, per the protocol (Section 2 below, plan step 1's
"with source citation"), the executor's compile step for that row re-runs the four-source
search (build brief, asset_registry row, layer handoff/closure doc, MCP tool description)
independently before accepting "NOT FOUND" as final; if the search still yields nothing,
the row is marked `promise_quote: "NOT FOUND (verified — no promise on record in any of
the four sources)"` and this absence is carried into the report as a finding in its own
right (an asset with no declared promise is a governance gap, not a pass).

## 2 — Protocol (plan §5 Lane 10, lines 272-288, TRANSCRIBED IN FULL — verbatim, never
paraphrased; anti-softening discipline)

> ### Lane 10 — Promise-vs-delivery audit (native review round 2)
>
> Every asset across the five layers was built against a DECLARED PROMISE — the value it
> committed to fulfill, recorded in its build brief (00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_
> <asset>_v*.md), the asset_registry row, the layer handoff/closure documents, and the MCP
> tool description that fronts it. The audit compiles, per asset, a **promise ledger**:
> (1) what was promised — verbatim, with source citation; (2) what the consuming LLM
> actually receives today — from the other lanes' evidence; (3) where the shortfall sits —
> data plane (never computed/written), retrieval plane (computed but unreachable/unusable),
> or ranking/form (reachable but drowned/mangled); (4) the finding refs that explain it.
> Grading is against the asset's OWN declared intent, not a generic rubric — an asset that
> delivers exactly its promise passes even if modest; an asset whose promise is served
> nowhere fails even if its tables are full (bo_anveshana R-37 and kala_activation R-45 are
> the type specimens: both promised "acharya-grade discoveries" / "activation points" and
> both fail at the consumption plane). Output: the **Promise×Delivery ledger** for all
> ~55 assets (9 ga_* + 14 bo_* + 12 ka_* + 9 ph_* + 12 mi_* + services), the planning
> session's asset-level prioritization input.

**This is the entirety of the plan's Lane 10 description. Nothing in it is optional, and
nothing below in this brief may weaken any clause above.** In particular, note the four
mandatory promise-record columns the protocol requires per asset:
1. what was promised — verbatim, with source citation;
2. what the consuming LLM actually receives today — from the OTHER LANES' evidence (this
   lane does not re-run consumption tests itself for delivery evidence; it consumes the
   evidence the other conductors produce — see Section 12.7 dependency note below);
3. where the shortfall sits — data plane / retrieval plane / ranking-form (three-way, not
   binary);
4. the finding refs (register row IDs / finding JSON record IDs) that explain the
   shortfall.

## 3 — Two-phase split: compile (this brief) vs. grade (consolidation)

Per charter §6 (plan §12.7 execution DAG, verbatim): `Lane10-compile` runs PARALLEL with
every other lane during EXECUTION; `Lane10-grade` is explicitly named as **"the ONE hard
sequential edge: promise-vs-DELIVERY grading consumes the other lanes' evidence, so its
grading pass runs at consolidation (its promise-ledger COMPILATION runs parallel, per
asset)."**

This brief governs **Lane10-compile ONLY**. Concretely, during EXECUTION (parallel with
all other lanes), this lane's conductor+swarm:
- fills protocol column (1) — the verbatim promise + citation — for every one of the 67
  ledger rows, sourced from the four documents named in the protocol (build brief,
  asset_registry row, layer handoff/closure doc, MCP tool description);
- does NOT attempt columns (2)-(4) during this phase — those require the other lanes'
  evidence, which does not yet exist mid-EXECUTION (Lane 1a/1b/1c/2/3-9 are running
  concurrently and have not landed findings yet);
- marks each ledger row's `status` field `"compiled"` once column (1) is filled (whether
  the promise was found or verified-NOT-FOUND per Section 1 above).

`Lane10-grade` (columns 2-4, the attribution-rules judgment call per charter §7.5) is
OUT OF SCOPE for this brief's conductor. It is picked up by the CONSOLIDATION session
after all other lanes have landed their evidence and the charter's §7 rubrics have been
Cowork-ratified. This brief's conductor's job ends when all 67 rows are `status:
"compiled"` and the compile trace is checkpointed (Section 4).

## 4 — Extensions

### 4.1 — Grading is against the asset's OWN declared intent (not a generic rubric)

This is a plan-level directive (line 282) that governs the eventual `Lane10-grade` pass,
but the compile pass must preserve it faithfully: when transcribing the verbatim promise
(protocol column 1), transcribe the asset's OWN stated intent exactly as written — do not
normalize, generalize, or substitute a project-wide expectation for what the asset "should
have promised." A promise that is narrow and modest (e.g., "persist the panchanga at the
birth instant") must be transcribed as narrow and modest, not upgraded to a broader claim
the asset never made. This is what makes the later grading pass fair: "an asset that
delivers exactly its promise passes even if modest."

### 4.2 — Type specimens (transcribe these into the ledger notes verbatim as calibration
anchors for the eventual grading pass)

- **bo_anveshana — R-37.** Promised "acharya-grade discoveries." Fails at the consumption
  plane: top-30 of discoveries collapses to 1 unique finding (charter §7.4 anchor,
  "family-collapse coverage" metric) — the promise is served nowhere despite full tables.
  This is the canonical example of a RANKING/FORM-layer shortfall (charter §7.5 step 3)
  masquerading as data presence — do not let "the table has rows" close this row's
  investigation.
- **kala_activation — R-45.** Promised "activation points." Serves nothing (see
  `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/briefs/ITEM0_R45_TRIAGE.md`
  for the Item-0 triage detail on this asset — read it if compiling the `ka_activation`
  ledger row, since Item-0's result is broadcast mid-flight per the execution DAG). This
  is the canonical example of a RETRIEVAL-PLANE or DATA-PLANE shortfall (charter §7.5
  steps 1-2) — an EMPTY SHELL (taxonomy class 4) at the point of consumption.

Both anchors must appear in the ledger with their promise columns filled from primary
sources (not from this brief's paraphrase above — that paraphrase is for orientation
only; the actual ledger row must cite the asset's own build brief / registry / handoff /
MCP description, per protocol column 1).

### 4.3 — Rubric reference (do not re-derive)

The judgment rubric that governs the (deferred) grading pass is charter §7.5,
**"Promise-shortfall layer attribution rules (Lane 10)"** — a 6-step decision tree (data
plane → retrieval plane → ranking/form → no-shortfall → compound-shortfall →
four-source-disagreement handling). This brief's conductor should read it now (Section 0
above) so the compile-phase promise transcriptions are captured in a form the grading pass
can consume directly (e.g., citing all four sources even when they agree, since charter
§7.5 step 6 requires checking all four and logging any disagreement as a class-3
INCONSISTENT finding on the promise-record itself).

## 5 — Checkpoint / RESUME instructions

**State file (owned exclusively by this lane's conductor):**
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/state/LANE10.md`

Per charter §5 (RESUME protocol) and §6 ("State discipline under parallelism"):
- This file is a **shard** of the top-level `AUDIT_STATE.md` index, owned exclusively by
  the Lane 10 conductor. No other lane's conductor writes to it; this lane's conductor
  writes to no other lane's shard.
- **Atomic idempotent regeneration:** every write to `state/LANE10.md` is a full
  regeneration from the ledger's current `status` field values (never a hand-edited diff)
  — i.e., the conductor recomputes rows-compiled / rows-total / rows-pending by scanning
  `asset_promises.jsonl` fresh each time, and writes the ENTIRE shard file in one atomic
  write (write-to-temp-then-rename, or equivalent), never a partial in-place edit. This
  makes concurrent/repeated regeneration safe and idempotent — re-running the same
  regeneration twice produces byte-identical output (given the same ledger state).
- **RESUME pointer = last completed shard id.** Concretely for this lane: the shard unit
  is the individual asset (Section 12.7 below: "Lane10 compile by asset"), so the RESUME
  pointer is the highest `row_id` (e.g., `AP-041`) whose ledger row has `status:
  "compiled"` AND whose per-shard trace file (Section 6 below) exists on disk. A
  resumed/fresh conductor session:
  1. reads `state/LANE10.md` for the last-checkpointed summary (rows-compiled count,
     last row_id touched);
  2. re-scans the ledger directly (never trusts the summary alone) to find the true set
     of `status: "compiled"` rows — the summary is derived, the ledger is truth;
  3. resumes dispatching workers only for rows still `status: "pending"`;
  4. never re-dispatches a worker for an already-`"compiled"` row (idempotent skip).
- **Atomicity contract** (charter §5): every checkpoint write must leave the shard
  self-consistent — rows-compiled count, findings/notes count, and status all updated
  together in the same write. A torn/partial write is itself a defect to be avoided, not
  a valid RESUME state.

### 5.1 — `state/LANE10.md` minimum content (regenerated each checkpoint)

```
# LANE10 (Promise-vs-Delivery, compile phase) — state
last_regenerated: <ISO8601 timestamp>
rows_total: 67
rows_compiled: <N>
rows_pending: <67-N>
last_row_id_compiled: AP-0##
shard_trace_dir: state/LANE10/
notes: <any cross-cutting compile-phase notes, e.g. rows where all four sources disagreed>
```

## 6 — Deliverable spec

Per plan §7 (Deliverables, lines 307-323), this lane is responsible for **deliverable 9**:

> 9. The **Promise×Delivery ledger** (Lane 10) — per asset: promise (cited) → delivered →
>    shortfall layer → finding refs.

This brief's compile phase produces the FIRST COLUMN of that deliverable (promise, cited)
for all 67 rows, checkpointed in `asset_promises.jsonl` itself (the ledger file IS the
deliverable's substrate — updated in place, `status` field advancing from `pending` to
`compiled`). The full four-column deliverable (promise → delivered → shortfall layer →
finding refs) is completed by the `Lane10-grade` consolidation pass (Section 3 above) and
is out of scope for this brief's conductor to finalize, though this brief's conductor MAY
pre-populate placeholder structure for columns 2-4 in each row's JSON object (e.g., empty
`delivered_evidence`, `shortfall_layer`, `finding_refs` keys) to make the grading pass's
job mechanical rather than requiring a schema migration mid-audit.

**Exact output**: the updated `asset_promises.jsonl` at
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/ledgers/asset_promises.jsonl`,
with every row's `promise_quote`, `promise_source_citation`, and `status` fields finalized
for the compile phase, plus the `state/LANE10.md` shard and its per-asset shard traces
(Section 12.7 below).

## 7 — Per-lane coverage self-declaration template (TAP-9 style)

Every surface this lane could plausibly touch is either AUDITED or explicitly DEFERRED
with reason — no silent gaps. Populate this table at lane close and carry it into the
final report per plan §7 deliverable 1 / §8 criterion 4 (Coverage honesty):

| surface | status (audited/deferred) | reason-if-deferred |
|---|---|---|
| ga_* asset promises (9 assets: L1 layer) | audited / deferred | |
| bo_* asset promises (14 assets: L2 layer) | audited / deferred | |
| ka_* asset promises (12 assets: L3 layer) | audited / deferred | |
| ph_* asset promises (9 assets: L4 layer) | audited / deferred | |
| mi_* asset promises (12 assets: L5 layer) | audited / deferred | |
| service-surface promises (remaining rows) | audited / deferred | |
| bo_anveshana (R-37 type specimen) | audited / deferred | must never be deferred — type specimen |
| kala_activation (R-45 type specimen) | audited / deferred | must never be deferred — type specimen |
| rows with promise_quote = "NOT FOUND" at Foundry build time | audited / deferred | re-verify per Section 1 before accepting |
| Lane10-grade (columns 2-4 of the deliverable) | deferred | out of scope for this brief — owned by consolidation session per charter §6 execution DAG |

Any row left "deferred" without a reason fails plan §8 criterion 4 (Coverage honesty) —
do not leave the reason column blank for a deferred row.

## 8 — Swarm decomposition (plan §12.7, MANDATORY section)

**(a) Conductor + worker pattern.** This lane runs as one CONDUCTOR session plus a
worker-swarm of fresh sub-agent sessions. The conductor: reads this brief and the charter
once; owns and shards `asset_promises.jsonl`; spawns one fresh sub-agent worker per shard,
handing each worker ONLY (i) the relevant excerpt of this brief (Sections 0-4, 6) plus
(ii) its assigned shard's ledger rows — never the full audit context, so each worker has
full attention on its narrow slice with zero context decay; collects each worker's shard
trace file on completion; merges results back into the ledger and into `state/LANE10.md`;
updates the RESUME pointer; and — only after ALL shards report `compiled` — declares the
compile phase done and hands off to the (later, separate) consolidation session for
`Lane10-grade`. The conductor never does per-asset promise research itself in-band; that
is the worker's job. The conductor's job is dispatch, shard tracking, merge, and state
regeneration.

**(b) Shard key: per asset, for promise-COMPILATION only.** Per charter §6 (plan §12.7
"Intra-lane sharding: ... Lane 10 compile by asset"), the shard unit is ONE ASSET (one
`row_id` in `asset_promises.jsonl`) per worker-task. This is explicitly the COMPILE-TIME
shard (column 1: promise, verbatim, cited) — it is NOT the grading pass. **The grading
pass — attributing shortfall layer and finding refs by consuming the other lanes'
evidence — is deferred to consolidation, per plan §12.7's statement that this is "the ONE
hard sequential edge."** This brief's swarm decomposition governs the compile shard only;
do not spawn workers to attempt column 2-4 attribution during EXECUTION — that evidence
does not exist yet from the other concurrently-running lanes.

**(c) Concurrency cap + throttling rule.** The conductor runs **5-10 concurrent workers**
at a time (subscription-limit-bounded, per charter §5 / plan §12.7's "concurrency-capped
batches, e.g. 5-10 workers, the conductor throttles to subscription limits" — the same
cap named for Lane 2 applies here as the project's standard default cap for per-row
sharded lanes). The conductor dispatches the first batch of up to 10 workers (one per
asset row), waits for the batch to report completion (each worker returns/writes its
shard trace and terminates), and only then dispatches the next batch of pending rows. If
the conductor observes rate-limit signals (e.g., tool-call throttling, session-budget
warnings, or explicit rate-limit errors) during a batch, it reduces the next batch's
concurrency (e.g., from 10 down to 5, or lower) before continuing — the cap is adaptive
downward on observed throttling signals, never adaptive upward beyond 10 without an
explicit native/Fable-5 directive to raise it.

**(d) Merge protocol: no shared-file writes, no write contention.** Workers write ONLY
their own shard trace file, at
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/state/LANE10/shard-<row_id>.md`
(e.g., `state/LANE10/shard-AP-014.md`) — a worker NEVER writes to `asset_promises.jsonl`
directly, and NEVER writes to `state/LANE10.md` directly. Each shard trace file records:
the row_id, the four-source search performed (build brief path checked, asset_registry
row checked, layer handoff/closure doc checked, MCP tool description checked), the
verbatim promise quote found (or the verified-NOT-FOUND determination per Section 1), the
source citation (file:line), and a completion marker. The CONDUCTOR ALONE reads all
completed shard trace files, applies their contents back into the single
`asset_promises.jsonl` ledger (updating `promise_quote`, `promise_source_citation`,
`status`), and regenerates `state/LANE10.md` from the updated ledger (Section 5's atomic
idempotent regeneration). No worker ever has write access to the ledger or to the
top-level shard-index file — this is what makes concurrent workers safe: they only ever
create NEW, uniquely-named files (their own `shard-<row_id>.md`), never edit a file
another process might also be touching.

**(e) Per-shard RESUME semantics: exact pointer format.** Each shard's completion is
self-evidenced by the EXISTENCE of its trace file
`state/LANE10/shard-<row_id>.md` — this is the exact per-shard RESUME pointer format. A
conductor resuming after interruption:
1. lists all files matching `state/LANE10/shard-*.md`;
2. extracts the set of `row_id`s already completed from the filenames present;
3. cross-checks against `asset_promises.jsonl` — any row_id with a completed shard trace
   file but NOT YET reflected in the ledger's `status` field is merged immediately (the
   conductor crashed after the worker finished but before the merge — no work is lost,
   only the merge step is redone);
4. any row_id with NEITHER a shard trace file NOR a `compiled` ledger status is treated as
   not-yet-dispatched and is re-queued for a fresh worker;
5. the conductor never re-dispatches a worker for a row_id that already has a shard trace
   file on disk (idempotent skip — trust the filesystem artifact, not memory of what was
   "in flight" before the interruption).

This shard-file-existence pointer is strictly more granular and more crash-safe than a
single "last completed row_id" counter (which loses information about workers that
finished out of dispatch order under concurrency) — with 5-10 concurrent workers, later
row_ids can complete before earlier ones, so the RESUME logic MUST scan the full set of
existing shard files rather than assume a contiguous prefix.

---

*End of LANE10_PROMISE.md v1.0. This brief cites `LLM_CONSUMPTION_AUDIT_CHARTER` v1.0 for
all doctrine/taxonomy/finding-schema/satisfaction-criteria/rubric content and does not
duplicate it. Its own scope is exhaustively self-contained: ledger path (Section 1),
protocol verbatim (Section 2), phase split (Section 3), extensions (Section 4),
checkpoint/RESUME (Section 5), deliverable spec (Section 6), coverage-declaration template
(Section 7), and swarm decomposition (Section 8).*
