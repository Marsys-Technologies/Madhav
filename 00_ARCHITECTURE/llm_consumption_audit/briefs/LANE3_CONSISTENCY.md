---
title: Lane 3 — Cross-tool consistency sweep — Child Brief
canonical_id: LANE3_CONSISTENCY_BRIEF
version: 1.0
status: DRAFT (Section 7 rubric ratification pending — see Charter §7 gate)
source_plan: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md (Lane 3, lines 177-182)
source_charter: 00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md
generated_by: Brief Foundry session, 2026-07-11
---

# Lane 3 — Cross-tool consistency sweep — Child Brief

**This brief is SELF-CONTAINED. A fresh session with no other context can execute this
lane from this document alone**, save for the one mandatory read below.

## 0 — Mandatory pre-read

Before doing anything else, read in full:
`00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md`

The Charter is cited BY REFERENCE throughout this brief for doctrine, the 9-class failure
taxonomy, the finding schema, the satisfaction criteria, the RESUME protocol, the
execution DAG, and the judgment rubrics. **Do not re-derive or paraphrase any of that
material — it lives in the Charter, not here.** Specifically, this brief relies on:

- Charter §1 — Doctrine (plan §2 + §2.1, verbatim): what counts as a "gap."
- Charter §2 — 9-class failure taxonomy (plan §4, verbatim): every finding gets exactly
  one primary class.
- Charter §3 — Finding schema (plan §6, verbatim): the fields every finding record carries.
- Charter §4 — Satisfaction criteria (plan §8, verbatim).
- Charter §5 — RESUME protocol (derived from plan §12 items 3-4).
- Charter §6 — Execution DAG (plan §12.7, TRANSCRIBED VERBATIM): this lane's place in the
  swarm, its intra-lane sharding directive ("Lane 3 by graha"), and the state-discipline
  rules this brief's §6 below operationalizes for Lane 3 specifically.
- Charter §7.1 — "Usable form" rubric (the rubric this lane grades against; see §4 below).

**Note on Charter status:** the Charter's judgment rubrics (its §7) are DRAFT, gated on
Cowork ratification (Fable 5 + native) before execution per Charter §7 preamble. If this
lane is dispatched before that ratification lands, the conductor halts and reports rather
than executing against unratified rubrics — this is not a lane-local decision to waive.

---

## 1 — Charter (doctrine, taxonomy, schema, satisfaction criteria): by reference only

Per the instruction above — do not restate. If any instruction in this brief appears to
conflict with the Charter, the Charter wins; halt and flag the conflict rather than
resolving it locally.

---

## 2 — Lane 3 protocol, TRANSCRIBED IN FULL (plan lines 177-182, verbatim)

> ### Lane 3 — Cross-tool consistency sweep
> Fixed quantity set — dignity, house, sign, nakshatra+pada, shadbala, dasha-lord
> denormalized metadata — per graha × per chart, pulled through EVERY path that serves it
> (chart_facts, dashas, judgment_query, graha_portrait, signals, snapshot, orientation).
> Any diff is a finding. Mechanical, scriptable, exhaustive. (R-43 proved this class is
> still live post-D-1/G-7 "FIXED" status — fixed rows regress.)

Every sentence above is binding, in full strength, with no softening:

- **"Fixed quantity set"** — exactly six quantity families: dignity, house, sign,
  nakshatra+pada, shadbala, dasha-lord denormalized metadata. Not a sample of these — all
  six, for every graha, for every chart in scope.
- **"per graha × per chart"** — all 9 grahas (Sun, Moon, Mars, Mercury, Jupiter, Venus,
  Saturn, Rahu, Ketu) × both charts in scope (Abhisek `482012f1-710e-4a25-994a-
  93821f5871aa`, Abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a`). Lagna is NOT part of
  this lane's graha set per the plan's literal wording (Lagna enters via Lane 8, not
  Lane 3) — do not narrow or widen the set from what the plan states.
- **"pulled through EVERY path that serves it"** — the word is EVERY, not "a sample of
  paths," not "the paths already in the ledger." The plan names seven serving paths
  explicitly: `chart_facts`, `dashas` (chart_dashas), `judgment_query`, `graha_portrait`,
  `signals` (get_signals), `snapshot`, `orientation`. **This is not an exhaustive list by
  construction — it is the plan's illustrative floor** (Charter §1's "examples are
  illustrative, never limiting" doctrine applies here exactly as everywhere else). If the
  executor discovers additional tools/paths that also serve any of the six quantities for
  a graha (e.g. a dasha service variant, a different snapshot tier, a divisional-chart
  view that also denormalizes dignity), those paths MUST be added and pulled too — do not
  stop at the seven named paths if more exist.
- **"Any diff is a finding."** Verbatim, absolute, no exceptions of any kind: no threshold,
  no "material difference" carve-out, no rounding tolerance, no decimal-precision
  allowance — a shadbala rupas value of `7.96` from one path and `7.960001` or `7.9` from
  another IS a diff and IS a finding, full stop, regardless of whether the executor
  believes the underlying computation is "the same value at different precision." The
  executor has no authority to adjudicate whether a diff is material; that adjudication
  belongs to the grading/consolidation phase, not this lane. When in doubt, log the diff
  and let it be graded — never silently pass it, never round it away, never normalize it
  before comparing.
- **"Mechanical, scriptable, exhaustive."** This lane is not a sampling exercise and not a
  judgment-call exercise in the way Lane 2 or Lane 6 are. It is a full cross-product sweep
  — every (quantity × graha × chart × path) cell gets pulled and compared. Script the
  pulls and diffs; do not hand-spot-check.
- **"(R-43 proved this class is still live post-D-1/G-7 'FIXED' status — fixed rows
  regress.)"** This is a standing warning, not decorative context: rows previously marked
  FIXED in the defect register are NOT exempt from this sweep and are NOT presumptively
  correct. Pull them exactly like every other row. A regression on a "FIXED" row is a
  first-class finding, cited against its prior fix record.

---

## 3 — Ledger: `quantities.jsonl`

Full path:
`00_ARCHITECTURE/llm_consumption_audit/ledgers/quantities.jsonl`

**Format:** JSONL, one row per (quantity × graha × chart × serving_path) cell. Row shape
observed in the seeded ledger (234 rows as of this brief's authoring):

```json
{"row_id": "Q-0001", "quantity": "dignity", "graha": "Sun", "chart_id": "482012f1-710e-4a25-994a-93821f5871aa", "serving_path": "chart_facts", "status": "pending"}
```

Fields: `row_id` (unique, `Q-####`), `quantity` (one of the six families), `graha`,
`chart_id`, `serving_path`, `status` (`pending` → `done` | `finding_logged`, set by the
executor as it works — add a `finding_ref` field pointing to the register row / findings
JSON record when a diff becomes a finding).

**Ledger completeness gap the conductor MUST resolve before/while executing (do not treat
silently):** the seeded ledger's `serving_path` values currently cover only three paths —
`chart_facts` (90 rows), `chart_dashas` (108 rows), `get_signals` (36 rows) — against the
seven paths named in the plan (`chart_facts`, `chart_dashas`/dashas, `judgment_query`,
`graha_portrait`, `get_signals`/signals, `snapshot`, `orientation`). Per §2 above ("EVERY
path"), the conductor's first act is to **extend `quantities.jsonl`** with the missing
rows for `judgment_query`, `graha_portrait`, `snapshot`, and `orientation` (and any
further paths discovered per the "illustrative floor" note in §2), following the exact
row shape above, before or as part of shard dispatch — a ledger that stops at 3 of 7 named
paths does not satisfy "EVERY path" and must not be executed against as-is without this
extension. Extension is additive only (append new rows with fresh sequential `row_id`s,
never mutate or renumber existing rows) — this keeps the ledger idempotent under
re-generation per §5 below.

**Completeness is a count query.** At any point, the following gives lane-progress and
proves nothing was silently skipped:

```
total rows        = count(*) in quantities.jsonl
done               = count(status == "done")
finding_logged     = count(status == "finding_logged")
pending            = count(status == "pending")
```

The lane is NOT complete until `pending == 0` for every row present at final extension
(i.e., after the completeness-gap extension above has landed and been swept).

---

## 4 — Rubric

Grade every pulled value pair under **Charter §7.1 — "Usable form" rubric** (referenced by
name; do not re-derive it here). In particular, apply Charter §7.1 question 1
("referential resolvability") when the diff under test involves an ID/key that resolves
differently — e.g. a dasha-lord reference that resolves to a different name string on two
paths is BOTH a Lane-3 consistency finding (the diff itself) AND potentially a class-6
usable-form finding on whichever path fails to resolve. Log both classes when both apply,
per Charter §7.1's own instruction for dual-class findings.

Primary failure class for a confirmed cross-path diff is, by default, the taxonomy class
in Charter §2 that best matches the diff's nature (e.g. an outright wrong value on one
path vs. the others is a correctness/data-fidelity class; a value present on one path and
silently absent on another is likely the ABSENT-ON-ARRIVAL class). Consult Charter §2's
verbatim class list and assign exactly one primary class per finding, with secondary
classes noted in the evidence excerpt where applicable (per Charter §3 finding schema).

---

## 5 — Checkpoint / RESUME instructions

State file (owned EXCLUSIVELY by this lane's conductor — no other lane or worker writes
to it):

`00_ARCHITECTURE/llm_consumption_audit/state/LANE3.md`

Rules (derived from Charter §5 RESUME protocol and Charter §6 execution DAG, applied to
this lane):

- **Atomic, idempotent regeneration.** `state/LANE3.md` is regenerated from the ledger's
  `status` column counts plus the shard trace files (§6 below) — never hand-edited as a
  running log. Regeneration must be idempotent: running it twice with no intervening work
  produces byte-identical output (modulo a timestamp field).
- **RESUME pointer = last completed shard id.** Since this lane shards **per graha**
  (§6 below), the RESUME pointer is the last graha shard fully swept (all its rows across
  all quantities × both charts × all paths reached `done` or `finding_logged`). A
  resuming conductor reads `state/LANE3.md`, finds the last completed graha shard, and
  dispatches the next undone graha shard — it never re-dispatches a completed shard and
  never skips an undone one.
- **Every checkpoint write leaves `state/LANE3.md` self-consistent** (row counts per
  status, findings-count, and per-shard completion list all updated together in the same
  write) — a partial/torn checkpoint is itself an execution defect per Charter §5's
  atomicity contract, not an acceptable resume condition.
- **Interruption safety.** A session interruption at any point — after N of 9 graha
  shards complete — loses zero completed work. The follow-on session reads
  `state/LANE3.md`, confirms the ledger's `status` column agrees with the shard trace
  files (§6 merge protocol), and resumes at graha shard N+1.

---

## 6 — MANDATORY: Swarm decomposition (plan §12.7 / Charter §6)

This lane executes as a **conductor + worker-swarm**, per Charter §6's execution DAG
directive "Lane 3 by graha" and the general conductor+worker pattern mandated for every
lane.

**(a) Conductor + worker pattern.** One conductor session owns `quantities.jsonl`, owns
the ledger-extension step (§3 above), shards the (now-extended) ledger by graha, and
spawns one fresh sub-agent worker per graha shard. Each worker receives ONLY: (i) this
brief's §2 (protocol, verbatim), §4 (rubric reference), and its own shard's ledger rows
(the rows where `graha == <its assigned graha>`) — full attention, zero context decay,
no need to re-read the full ledger or other shards. The worker pulls every serving path
for every quantity for its graha, across both charts, diffs the values, logs findings per
Charter §3 schema, marks ledger rows `done` / `finding_logged`, and writes its own shard
trace file (§6d below). The conductor collects all 9 shard traces, merges them, updates
`state/LANE3.md`, and re-sweeps `quantities.jsonl` status counts to confirm `pending == 0`
before declaring the lane complete.

**(b) Shard key: per graha.** Exactly 9 shards — one per graha (Sun, Moon, Mars, Mercury,
Jupiter, Venus, Saturn, Rahu, Ketu) — each spanning both charts and all six quantity
families and all serving paths for that graha. This matches Charter §6's explicit
intra-lane sharding directive ("Lane 3 by graha") verbatim — do not reshard by quantity,
by chart, or by path instead.

**(c) Concurrency cap + throttling rule.** The conductor runs **up to 5 concurrent graha
workers at a time** (subscription-limit-bounded, matching the plan's stated 5–10 worker
band for capped concurrency; this lane fixes the cap at the conservative end of that band
because each worker performs multiple tool calls per quantity × path cell, multiplying
call volume faster than Lane 2's single-question workers). If the conductor observes
rate-limit signals (429s, throttling errors, or MCP-layer backpressure) from any worker,
it reduces the live concurrent count by at least 1 (down to a floor of 1 sequential
worker) before dispatching the next shard, and only restores concurrency upward once a
full shard completes cleanly at the reduced level. The conductor never exceeds 5
concurrent workers even if no throttling has yet been observed — the cap is a hard
ceiling, not a target reached only after failure.

**(d) Merge protocol — no shared-file writes, no write contention.** Each worker writes
ONLY its own shard trace file:

`00_ARCHITECTURE/llm_consumption_audit/state/LANE3/shard-<graha>.md`

(e.g. `state/LANE3/shard-mercury.md`, `state/LANE3/shard-sun.md`, …). A worker NEVER
writes to `state/LANE3.md` (conductor-owned index) and NEVER writes to another worker's
shard file. The conductor ALONE reads all 9 shard trace files and merges them into
`state/LANE3.md`. This eliminates write contention by construction — no two agents ever
write the same file. If a worker needs to log a finding, it appends the finding record
(per Charter §3 schema) to its own shard trace file and/or the designated findings-JSON
output location as specified by the master plan's Deliverable 2 mechanism; it does not
write directly into the shared register file — register append is a conductor-level or
consolidation-level act per Charter §6's consolidation phase ("merge → dedupe vs register"
runs at consolidation, not per-worker).

**(e) Per-shard RESUME semantics — exact pointer format.** Each shard trace file
`state/LANE3/shard-<graha>.md` carries, at minimum, a pointer line in the exact form:

```
RESUME: quantity=<quantity_family> path=<serving_path> last_row_id=<Q-####> status=<done|in_progress>
```

e.g. `RESUME: quantity=shadbala path=judgment_query last_row_id=Q-0187 status=in_progress`.

A worker resuming a partially-complete shard (its own crash-recovery, or a fresh worker
picking up an interrupted shard) reads this line, resumes ledger sweep from the row
immediately after `last_row_id` within the stated `quantity`/`path` pair, and continues
in the shard's fixed iteration order (quantity family, then serving path, then chart) —
never re-pulls a row already marked `done`/`finding_logged` in `quantities.jsonl`, never
skips a `pending` row that sorts before the resume point. The conductor's own resume
pointer (§5 above, "last completed shard id") is simply the highest graha shard whose
trace file's final line reads `status=done` for its last row — i.e. the shard-level
pointer is derived FROM the per-shard pointers, not maintained independently, keeping the
two levels of RESUME state from ever disagreeing.

---

## 7 — Deliverable spec

Per plan §7 (deliverables, lines 307-323), this lane is the primary producer of evidence
feeding **Deliverable 2** (machine-readable findings file — Lane 3's diff-findings are
individual records in that file, each carrying the full Charter §3 finding schema) and
**Deliverable 3** (register appends — new, deduped rows only, appended at consolidation,
not per-worker per §6d above). Lane 3 does not own a standalone named deliverable of its
own (unlike, e.g., Lane 8's 20 retrievability matrices or Lane 9's ingestion matrix/graph
report) — its deliverable IS the completed, `pending == 0` `quantities.jsonl` ledger plus
its contribution of diff-findings to Deliverables 2 and 3, cross-referenced against the
calibration-anchor set (R-37..R-48, per Charter §4/§6 — Lane 3 must independently
rediscover R-43, the "FIXED rows regress" anchor named in its own protocol text, or its
own coverage is provably incomplete).

**Concretely, at lane close, the following must exist:**
1. `quantities.jsonl` with every row (including the extended rows from §3's completeness
   gap) at `status ∈ {done, finding_logged}` — zero `pending`.
2. 9 shard trace files at `state/LANE3/shard-<graha>.md`, each ending in a `status=done`
   resume-pointer line.
3. `state/LANE3.md` (conductor-merged index) showing all 9 shards complete, total
   findings count, and confirmation that R-43 was independently rediscovered (or an
   explicit note if it was NOT rediscovered, which is itself a lane-coverage finding per
   Charter §6's calibration-anchor test).
4. Lane 3's diff-findings appended to the shared machine-readable findings file
   (Deliverable 2) and, after consolidation-phase dedupe, to the defect/gap register
   (Deliverable 3) — both per Charter §3 schema, both conductor-level acts per §6d.

---

## 8 — Per-lane coverage self-declaration (TAP-9 style)

To be filled in and appended at lane close, matching the plan §7 Deliverable 1 /
Charter §4 "coverage honesty" requirement. Template:

| surface | status (audited / deferred) | reason-if-deferred |
|---|---|---|
| dignity — all 9 grahas × 2 charts × all serving paths | | |
| house — all 9 grahas × 2 charts × all serving paths | | |
| sign — all 9 grahas × 2 charts × all serving paths | | |
| nakshatra+pada — all 9 grahas × 2 charts × all serving paths | | |
| shadbala — all 9 grahas × 2 charts × all serving paths | | |
| dasha-lord denormalized metadata — all 9 grahas × 2 charts × all serving paths | | |
| chart_facts path | | |
| chart_dashas path | | |
| judgment_query path | | |
| graha_portrait path | | |
| get_signals path | | |
| snapshot path | | |
| orientation path | | |
| any additional path discovered beyond the named seven (§2 "illustrative floor" note) | | |
| R-43 calibration-anchor rediscovery | | |

Every row must resolve to `audited` (with the shard/finding evidence it rests on) or
`deferred` with an explicit, specific reason — a blank or vague reason fails Charter §4
criterion 4 (coverage honesty) and fails this lane's close.

---

*End of Lane 3 child brief. Self-contained per Brief Foundry instruction; Charter
(`00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md`) is the sole external
dependency, cited by reference throughout, never restated.*
