---
title: LLM Consumption Audit — Lane 6 Child Brief — Ranking-Quality Audit
canonical_id: LLM_CONSUMPTION_AUDIT_LANE6_BRIEF
version: 1.0
status: DRAFT (rubrics gated — see §3 below; do not execute until Cowork ratification lands)
source_plan: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md (lines 198-205)
source_charter: 00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md
generated_by: Brief Foundry session, 2026-07-11
---

# Lane 6 — Ranking-Quality Audit — Self-Contained Executor Brief

**This brief is self-contained.** A fresh session with NO other context than this file
(plus the charter it cites) can execute Lane 6 end to end. Do not re-derive doctrine,
taxonomy, finding schema, satisfaction criteria, or the execution DAG — they are cited
by reference below and MUST be read from the charter, never paraphrased from memory or
from this brief's summary language.

## 0 — Mandatory reading before any substantive work

Read, in full, before executing a single call:

1. `00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md` — the whole file. It carries:
   - §1 Doctrine (plan §2 + §2.1, verbatim) — the width/depth completeness axes and the
     examples-are-illustrative-never-limiting rule.
   - §2 9-class failure taxonomy (plan §4, verbatim) — every finding this lane produces
     gets exactly one primary class from this list.
   - §3 Finding schema (plan §6, verbatim) — the exact fields every finding record carries.
   - §4 Satisfaction criteria (plan §8, verbatim).
   - §5 RESUME protocol (derived from plan §12 items 3-4).
   - §6 Execution DAG (plan §12.7, verbatim) — Lane 6 runs in the fully-parallel EXECUTION
     block, sharded by ranked surface, conductor+worker-swarm pattern (see §8 below).
   - §7.4 Ranking-quality metrics — the DRAFT rubric this lane grades against (transcribed
     again in §3 below per this brief's self-containment mandate, but §7.4 is the
     authoritative source; if this brief and the charter ever diverge, the charter wins).
2. This brief, in full (you are reading it).
3. `00_ARCHITECTURE/llm_consumption_audit/ledgers/tools.jsonl` — the tool ledger this
   lane marks rows against (see §1 below).
4. `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` rows R-37..R-48 (anchor rows,
   lines 226-236) — calibration targets this lane MUST independently rediscover
   (see §2 below).

**Charts in scope (both, every surface):**
- Abhisek (native): `482012f1-710e-4a25-994a-93821f5871aa`
- Abhinandan: `1c826d5a-41cb-4450-b4dc-59d440e5f75a`

**DB access is READ-ONLY.** Use `mcp__postgres__query`, SELECT only. NEVER issue INSERT/
UPDATE/DELETE/DDL. This is a hard governance rule with no exceptions in this lane.

---

## 1 — Ledger: the artifact this lane marks rows against

**Primary ledger:** `00_ARCHITECTURE/llm_consumption_audit/ledgers/tools.jsonl`
(full path: `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/ledgers/tools.jsonl`)

Lane 6 audits the **ranked-surface subset** of this ledger — tools whose response is a
ranked/ordered list an acharya would scan top-down: orientation top-signals, domain
readings, signals, discoveries, convergence/windows/activation surfaces. As of this
brief's authoring, the following rows in `tools.jsonl` are identified ranked-surface
candidates (identify by `tool_name`, not by a fixed row_id, since the ledger may be
re-sharded between foundry and execution):

- `bodha_discoveries_get` (bodha) — discoveries surface (R-37 anchor: top-30 = 1 unique finding)
- `bodha_domain_reading_get` (bodha) — domain readings surface
- `bodha_signals_get` (bodha) — signals surface (R-44 anchor: 298/300 unattributed)
- `get_chart_orientation` (bodha) — orientation top-signals surface
- `get_domain_reading` (bodha) — domain readings surface (alias/parallel path — check
  for INCONSISTENT class 3 divergence against `bodha_domain_reading_get`)
- `get_signals` (bodha) — signals surface (alias/parallel path — cross-check against
  `bodha_signals_get`)
- `get_temporal_windows` (kala) — convergence/windows surface
- `kala_windows_get` (kala) — convergence/windows surface
- `kala_yoga_activation_get` (kala) — activation/convergence surface
- `yoga_activation_by_dasha` (kala) — activation/convergence surface

**This candidate list is illustrative, not exhaustive** (charter §2.1 applies here too:
never treat a native/foundry-supplied example list as the ceiling). Before marking any
row done, the lane conductor MUST re-query `tools.jsonl` itself for any tool whose
`tool_name`, description, or observed response shape is a ranked/ordered/top-K surface,
including any tool added to the ledger after this brief was authored, and any tool in
categories other than `bodha`/`kala` that turns out to rank/order its output (e.g. a
`phala` or `mimamsa` tool that returns a scored list is in scope even if not named above).
Query pattern:

```
python3 -c "
import json
rows=[json.loads(l) for l in open('<path>/tools.jsonl')]
for r in rows:
    print(r['row_id'], r['tool_name'], r['category'], r['status'])
"
```

**Marking protocol:** for each ranked-surface tool_name × each chart (2 charts), the
lane produces one ranking-quality record (schema in §3). Completeness is a count query:
`(# ranked-surface tool_names identified) × 2 charts` records exist and are non-pending.
The lane's own output ledger (see §6 deliverable) is the row-status source of truth for
this count — `tools.jsonl`'s own `status` field may optionally be updated to `done` for
rows this lane fully closes out, but the authoritative completeness record for Lane 6 is
its own ranking-quality ledger, not a mutation of the shared `tools.jsonl` file (avoid
write contention with other lanes reading/writing the same shared ledger — see §8 merge
protocol).

---

## 2 — Protocol (plan §5 Lane 6, TRANSCRIBED IN FULL — lines 198-205, verbatim, never
paraphrased or softened)

> ### Lane 6 — Ranking-quality audit
> For each ranked surface (orientation top-signals, domain readings, signals, discoveries,
> convergence): is the top-K what an acharya would put first? Measured: duplication rate,
> identical-score walls, descriptive-trivia share, family-collapse coverage, UNATTRIBUTED
> share (R-44: 298/300 unattributed; R-37: top-30 of discoveries = 1 unique finding).
> **Extension:** normative-bands check — strength values must arrive WITH their classical
> reference thresholds (shadbala required-minimum rupas, vimsopaka bands, ishta/kashta
> framing); a bare "7.96 rupas" fails the rubric (§10 gap 5).

This is the entire governing protocol text for this lane, transcribed verbatim from the
plan. Every clause above is binding and none may be weakened in execution:

- **"is the top-K what an acharya would put first?"** — the central judgment call of the
  lane. Grade using the classical-canon weighting (charter §2.1 source 1: shastra concept
  inventory) as the arbiter where the system itself provides no explicit weight — this is
  the same arbiter rule charter §7.4 clause 3 (descriptive-trivia share) specifies.
- **Five measured metrics, ALL five computed for EVERY ranked surface, per chart** —
  duplication rate; identical-score walls; descriptive-trivia share; family-collapse
  coverage; UNATTRIBUTED share. None may be skipped as "not applicable" without an
  explicit logged reason tied to the surface's actual response shape (e.g., a surface
  with no score field at all cannot have "identical-score walls" — log that as N/A with
  the reason, not silently omit the metric).
- **Calibration anchors (mandatory rediscovery targets):**
  - **R-44**: 298/300 unattributed — this lane MUST independently rediscover this finding
    (or a materially equivalent successor-state finding if the underlying defect has since
    been partially remediated) via its own UNATTRIBUTED-share measurement on the signals
    surface (`bodha_signals_get` / `get_signals`). Failure to rediscover R-44's class of
    defect (or to explicitly confirm-and-cite that it is now fixed, with evidence) is
    itself a lane-coverage hole per charter §3 "Known-findings anchor set."
  - **R-37**: top-30 of discoveries = 1 unique finding — this lane MUST independently
    rediscover this finding (or confirm remediation with evidence) via its own
    duplication-rate / family-collapse-coverage measurement on the discoveries surface
    (`bodha_discoveries_get`).
  - Cite both R-37 and R-38..R-48 register rows (`00_ARCHITECTURE/MARSYS_DEFECT_GAP_
    REGISTER_v2_0.md` lines 226-236) as the calibration anchor set per charter §3.

---

## 3 — Extension (plan lines 204-205, TRANSCRIBED IN FULL, never softened)

> **Extension:** normative-bands check — strength values must arrive WITH their classical
> reference thresholds (shadbala required-minimum rupas, vimsopaka bands, ishta/kashta
> framing); a bare "7.96 rupas" fails the rubric (§10 gap 5).

Operationalized as a MANDATORY sixth check, run on every ranked surface where a strength/
score value is served (not only shadbala — any normed numeric strength value: shadbala
rupas, vimsopaka bala scores, ishta/kashta phala, bhava bala, or any other classical
strength metric surfaced by a ranked surface in scope):

- **Normative-bands check** — for every strength/score value in the top-K, does the
  SAME response carry its classical reference threshold/band alongside the bare number?
  Concretely:
  - Shadbala: does the value arrive with the required-minimum rupas threshold for that
    graha (the classical pass/fail bar), not just the raw rupas figure?
  - Vimsopaka bala: does the value arrive with its classical band (e.g. the traditional
    strong/medium/weak vimsopaka cutoffs), not just the raw score?
  - Ishta/kashta phala: does the value arrive framed as ishta vs. kashta (benefic vs.
    malefic effect strength), not just a bare number with no framing?
  - **A bare "7.96 rupas" with no threshold context FAILS this check** (verbatim plan
    example — treat literally: if you observe any bare unframed strength number on a
    ranked surface, that is a fail, full stop, no benefit of the doubt).
- Cite `§10 gap 5` as the originating gap analysis reference for this extension (native
  observation that fragility/confidence/normative-band metadata is frequently absent from
  served strength values — this is the ranking-specific instance of that broader gap;
  Lane 4's fragility/confidence metadata check, plan lines 188-190, is the sibling audit
  for non-ranking surfaces — do not duplicate Lane 4's scope, but DO run this check for
  every strength value that appears WITHIN a ranked top-K under this lane's scope).
- Failing this check on a given row/surface is classed under charter §2 taxonomy as
  **class 6 (UNUSABLE FORM)** if the omission means the LLM cannot determine whether the
  strength value is strong/weak/decisive without external tribal knowledge (this maps
  directly to charter §7.1 clause 1's "undocumented tribal knowledge to interpret a
  field" PARTIAL-grade condition, escalated to a full finding when the surface is a
  ranked top-K that is supposed to be authoritative on its own).

---

## 4 — Rubric (reference by name; do not re-derive)

This lane grades against **Charter §7.4 — Ranking-quality metrics (Lane 6)**, the DRAFT
rubric derived from plan lines 198-205 and ratified/pending-ratification per the Cowork
review gate. Use the charter's five metric definitions VERBATIM as the computation
specification (duplication rate; identical-score walls; family-collapse coverage;
descriptive-trivia share; UNATTRIBUTED share) — do not invent alternate formulas. If a
metric's charter definition is ambiguous for a specific surface's actual shape, log the
ambiguity as a class-9 (UNGOVERNED JUDGMENT) finding per charter §2 item 9, note the
interpretation chosen, and proceed — do not block on rubric ratification if the review
gate has not yet completed, but flag every finding produced under an unratified rubric as
provisional (`rubric_status: DRAFT-UNRATIFIED`) in the finding record until the charter's
§7 status changes from DRAFT.

Also apply **Charter §7.1 — "Usable form" rubric** wherever a ranked-surface row's
individual content (not just its rank position) is being graded for class 6/7
determination — the two rubrics are complementary: §7.4 grades the LIST, §7.1 grades
each ROW's content.

---

## 5 — Finding schema (cite; do not restate in full — reference charter §3)

Every finding this lane produces uses the exact schema at **Charter §3 (plan §6,
verbatim)**: reproducible call (exact tool + args), verbatim evidence excerpt, primary
failure class (charter §2), severity, suspected layer (data plane / L-writer /
serving-query / envelope-trim / ranking / MCP contract / architecture), dedupe check
against the existing ~200 register rows (incl. R-37..R-48). Genuinely new rows are
appended to `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` following that file's
existing row format — read the file's existing R-37..R-48 rows (lines 226-236) as the
formatting template before appending.

Lane 6's per-finding record additionally carries (Lane-6-specific extension fields,
appended to the base schema, never replacing it):
- `ranked_surface`: the tool_name under test.
- `chart_id`: which of the two charts.
- `metric`: which of the five §7.4 metrics (or the §3 normative-bands extension) the
  finding derives from.
- `metric_value`: the computed rate/share/count.
- `rubric_status`: `DRAFT-UNRATIFIED` or `RATIFIED` (per §4 above).

---

## 6 — Deliverable spec (cross-reference plan §7, lines 307-323)

Lane 6 is directly responsible for the ranking-quality evidence that feeds into:

- **Deliverable 1** (`LLM_CONSUMPTION_AUDIT_v1_0.md`, plan line 309): Lane 6's per-surface
  findings section, plus its §4-class distribution contribution, plus its own coverage
  self-declaration (§7 below) as the Lane-6 slice of the report's overall TAP-9-style
  self-declaration.
- **Deliverable 2** (machine-readable findings JSON, plan line 312): every Lane 6 finding
  emitted per the schema in §5 above, in the same file/stream the other lanes append to
  (do not create a separate findings-JSON format for Lane 6 — same schema, same file,
  Lane-6-specific fields as documented extensions).
- **Deliverable 3** (register appends, plan line 314): any genuinely new register row Lane
  6 produces after the R-37..R-48 dedupe check.

Lane 6 does NOT own deliverables 4 (entity dossiers — Lane 8), 5 (question-coverage
matrix — Lane 2), 6 (Concept×Retrievability matrix — Lane 1b), 7 (MSR ingestion / graph
reports — Lane 9), 8 (Lane 2 evidence-plans), or 9 (Promise×Delivery ledger — Lane 10).
Do not produce those artifacts under this brief; if a Lane 6 finding is directly relevant
to one of those deliverables (e.g. a ranking defect that is also evidence for a Lane 10
promise-shortfall), cite the finding's row_id in that other lane's ledger rather than
duplicating the content.

**Concrete output file for this lane:**
`00_ARCHITECTURE/llm_consumption_audit/ledgers/lane6_ranking_quality.jsonl` — one JSON
object per finding/measurement record (schema §5), no trailing commas, no surrounding
array — mirroring the `.jsonl` convention already used by `tools.jsonl` and sibling
ledgers in `00_ARCHITECTURE/llm_consumption_audit/ledgers/`.

---

## 7 — Per-lane coverage self-declaration template (TAP-9 style)

Emit this table (fully filled in, no placeholder rows left as "TBD" at lane close) as
part of the lane's final checkpoint and as Lane 6's contribution to deliverable 1's
overall coverage-honesty section (satisfaction criterion 4, charter §4):

| surface | status (audited / deferred) | reason-if-deferred |
|---|---|---|
| orientation top-signals (`get_chart_orientation`) | | |
| domain readings (`bodha_domain_reading_get`) | | |
| domain readings — alias path (`get_domain_reading`) | | |
| signals (`bodha_signals_get`) | | |
| signals — alias path (`get_signals`) | | |
| discoveries (`bodha_discoveries_get`) | | |
| convergence/windows (`get_temporal_windows`) | | |
| convergence/windows (`kala_windows_get`) | | |
| yoga activation (`kala_yoga_activation_get`) | | |
| yoga activation by dasha (`yoga_activation_by_dasha`) | | |
| any additional ranked surface discovered during re-query of `tools.jsonl` (§1) | | |

Every row must resolve to `audited` (with its ranking-quality record complete for both
charts) or `deferred` with an explicit, specific reason (never a bare "deferred" with no
reason — that fails satisfaction criterion 4).

---

## 8 — MANDATORY Swarm decomposition (plan §12.7)

This section specifies the Lane 6 conductor+worker-swarm execution exactly, per plan
§12.7 (charter §6, verbatim) and its "Intra-lane sharding" clause: *"Lane 6 by ranked
surface."*

**(a) Conductor + worker pattern.** One Lane 6 **conductor** session owns this lane's
ledger (`lane6_ranking_quality.jsonl`), the §7 coverage self-declaration table, and the
lane's shard of `AUDIT_STATE.md` (`state/LANE6.md`, per §9 below). The conductor:
(i) re-queries `tools.jsonl` to finalize the ranked-surface shard list (§1); (ii) spawns
one fresh sub-agent **worker** per shard; (iii) gives each worker ONLY the charter excerpt
(charter §1/§2/§3/§4/§7.4/§7.1) plus this brief's §2/§3/§4/§5 (the protocol, extension,
rubric-reference, and finding schema) plus its own single shard assignment — full
attention, zero context decay, no visibility into other shards' progress; (iv) collects
each worker's shard trace file on completion; (v) merges all shard traces into the lane
ledger and the coverage table; (vi) updates `state/LANE6.md`.

**(b) Shard key: per ranked surface.** One shard = one ranked-surface tool_name (e.g.
`bodha_discoveries_get` is one shard, `get_chart_orientation` is another). Each shard's
worker computes all five §7.4 metrics + the §3 normative-bands extension check, for BOTH
charts, for that one surface, and emits the shard's findings + a per-surface summary row
for the coverage table (§7).

**(c) Concurrency cap + throttling rule.** The conductor runs **5–10 concurrent workers**
at a time (subscription-limit-bound, matching the plan's own stated example figure for
Lane 2 sharding, applied here as the general swarm concurrency default). If the lane has
more than 10 ranked-surface shards after the §1 re-query, the conductor batches them into
waves of up to 10 concurrent workers, launching the next wave only after the current
wave's shard traces are collected. The conductor throttles (reduces concurrent worker
count within a wave) on any observed rate-limit signal (tool-call errors indicating
throttling, MCP timeouts, or explicit rate-limit responses) — on such a signal, halve the
in-flight worker count for the remainder of the current wave and log the throttle event in
`state/LANE6.md`.

**(d) Merge protocol: no shared-file writes, no write contention.** Workers write
**ONLY their own shard trace file** at
`00_ARCHITECTURE/llm_consumption_audit/state/LANE6/shard-<tool_name>.md`
(one file per shard, named by the ranked-surface tool_name, e.g.
`state/LANE6/shard-bodha_discoveries_get.md`) — never `lane6_ranking_quality.jsonl`,
never `state/LANE6.md`, never `tools.jsonl`, never any other shared file. **The conductor
alone** reads all shard trace files and merges them into: (i) the lane ledger
(`ledgers/lane6_ranking_quality.jsonl`, appending each shard's finding records); (ii) the
coverage table (§7); (iii) `state/LANE6.md`. No worker ever writes to a file another
worker or the conductor also writes to concurrently — this is the entire mechanism that
makes concurrent execution safe with no write contention and no lost updates.

**(e) Per-shard RESUME semantics.** Exact pointer format: a shard trace file
`state/LANE6/shard-<tool_name>.md` is considered COMPLETE when it contains all five §7.4
metrics + the §3 extension check + coverage-row status, for BOTH charts, for its one
surface. A follow-on/resumed worker (or the conductor, on resume) determines resume state
by:
1. Listing `state/LANE6/shard-*.md` — any file present and marked complete (a trailing
   `STATUS: COMPLETE` line in the shard file) is done; do not re-run it.
2. Any shard tool_name from the §1 candidate list (plus any additional surfaces found on
   re-query) with NO corresponding shard file, or a shard file present but NOT marked
   `STATUS: COMPLETE`, is the resume boundary — re-run (or continue) that shard's worker.
3. The conductor's own resume pointer is `state/LANE6.md`'s `last_merged_shard` field
   (see §9) — on conductor resume, re-scan all shard files newer than that pointer's
   timestamp and merge any not yet merged, then update the pointer.
4. This RESUME semantics is identical whether the interruption is full-session-end or
   mid-lane crash, per charter §5 — checkpointing is incremental at the shard-file level,
   so no completed shard is ever re-done and no incomplete shard is ever silently skipped.

---

## 9 — Checkpoint / state ownership

This lane checkpoints exclusively to **`00_ARCHITECTURE/llm_consumption_audit/state/
LANE6.md`** (full path:
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/state/LANE6.md`),
owned exclusively by this lane's conductor — no other lane, worker, or session writes to
this file. Regeneration of this file is **atomic and idempotent**: every write replaces
the file's full content (derived fresh from the current set of shard trace files under
`state/LANE6/`), never a partial in-place patch — a torn/partial checkpoint write is
itself an execution defect, not an acceptable RESUME condition (charter §5 atomicity
contract).

`state/LANE6.md` MUST contain, at minimum, after every checkpoint:
- `lane: 6`
- `status`: NOT_STARTED / IN_PROGRESS / COMPLETE
- `ranked_surfaces_total`: count from the current §1 re-query
- `ranked_surfaces_shards_complete`: count of shard files marked `STATUS: COMPLETE`
- `findings_count`: total findings emitted so far into `lane6_ranking_quality.jsonl`
- `last_merged_shard`: the RESUME pointer — the tool_name of the last shard the conductor
  merged, plus its shard-file timestamp
- `coverage_table_status`: whether §7's table is fully resolved (all rows audited or
  deferred-with-reason) or still has open rows

**RESUME instructions for a fresh/follow-on conductor session:** read `state/LANE6.md`
first. If `status: COMPLETE`, verify via the count query in §1 before trusting it (a
stale `COMPLETE` marker that does not match the actual shard-file count is itself a
checkpoint-atomicity defect — log it as a class-9 finding and re-derive true status from
the shard files). If `status: IN_PROGRESS` or `NOT_STARTED`, resume per §8(e) above:
enumerate `state/LANE6/shard-*.md`, determine which shards are complete vs. missing vs.
incomplete, spawn workers only for the missing/incomplete shards (respecting the §8(c)
concurrency cap), and proceed.

`00_ARCHITECTURE/AUDIT_STATE.md` (the top-level index, per charter §5) is NOT owned by
this lane — the top-level index regenerates itself by reading all `state/LANE<k>.md`
shards, including this one; Lane 6 never writes to the top-level index directly.

---

*End of Lane 6 brief v1.0. Cites `LLM_CONSUMPTION_AUDIT_CHARTER` v1.0 for doctrine,
taxonomy, finding schema, satisfaction criteria, RESUME protocol, execution DAG, and
§7.4/§7.1 rubrics. Do not execute against unratified §7 rubrics without flagging findings
`rubric_status: DRAFT-UNRATIFIED` per §4 above.*
