---
artifact: LANE4_RECEIPT_HONESTY
type: BRIEF (Brief Foundry output — Lane 4 child brief; self-contained, executable by a fresh session)
version: 1.0
status: READY FOR EXECUTION — gated on Cowork ratification of CHARTER.md §7 draft rubrics
  (charter §7 note: "No lane may treat these as final without that ratification.")
program: LLM_CONSUMPTION_AUDIT_PLAN_v1_0
plan_ref: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md §5 Lane 4 (lines 184-190)
charter_ref: 00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md (canonical_id LLM_CONSUMPTION_AUDIT_CHARTER)
register_anchors: R-38 (line ~227-ish, varga_confirmed dishonesty), R-41 (verdict-vs-content mismatch)
charts_in_scope:
  - 482012f1-710e-4a25-994a-93821f5871aa   # Abhisek (native)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a   # Abhinandan
db_access: mcp__postgres__query, READ-ONLY (SELECT only). NEVER issue INSERT/UPDATE/DELETE/DDL.
  This is a BUILD/AUDIT-execution brief — fix-forbidden per plan §3 "Fix-forbidden: Absolute.
  Findings only."
authored_by: Brief Foundry session (Claude Code), 2026-07-11
---

# LANE 4 — RECEIPT-HONESTY SWEEP

## 0. How to use this brief (read this first — self-containment statement)

This brief is SELF-CONTAINED. A fresh session with no other context can execute Lane 4 from
this document alone, EXCEPT for doctrine, taxonomy, finding schema, satisfaction criteria,
and the execution DAG, which are NOT re-derived here — they are governed by
`00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md` (canonical_id
`LLM_CONSUMPTION_AUDIT_CHARTER`) and this brief cites that charter BY SECTION NUMBER rather
than restating it (charter's own anti-drift instruction: "Every child brief MUST cite this
charter by name and MUST NOT restate or paraphrase these sections — reference them, do not
duplicate them with drift risk.").

Before executing, read (in this order):
1. This brief, in full.
2. `CHARTER.md` §1 (doctrine, incl. §2.1 examples-are-illustrative), §2 (9-class taxonomy),
   §3 (finding schema), §4 (satisfaction criteria), §5 (RESUME protocol), §6 (execution DAG,
   verbatim), §7.1 (usable-form rubric — the closest drafted rubric to this lane's subject
   matter; see §5 below for why it is adjacent, not identical, and for the derived
   class-5-specific grading protocol this brief supplies to fill that gap).
3. The Lane 4 ledger (§1 below).

## 1. Ledger — the executor's ground truth

**Ledger file:** `00_ARCHITECTURE/llm_consumption_audit/ledgers/tools.jsonl`

Every MCP tool the audit knows about is one JSONL row in this file. As of Brief Foundry
time it holds **134 rows** (`wc -l` verified), each shaped like:

```json
{"row_id": "T-001", "tool_name": "apex_career_assess", "category": "phala", "param_schema_hash": "none", "expose_to_planner": true, "linked_data_asset_ids": [], "source": "code:platform-mcp/src/tools/register_p1_aliases.ts", "status": "pending"}
```

Lane 4 executes AGAINST this ledger, not against memory or a fresh tool listing composed
ad hoc. Do not skip a `row_id`. Do not add tools this ledger omits without also appending a
new ledger row for them (if the live MCP surface has grown since Foundry time, that drift is
itself worth a one-line note in the Lane 4 state shard, but the row-by-row sweep still runs
against the ledger as the enumeration of record — completeness is a count query against
THIS file, per charter §4 criterion 1 and plan §12 item 2: "Lanes execute AGAINST their
ledger, marking rows; completeness becomes a count query, not a judgment.").

**Marking protocol:** for each ledger row, after the tool is exercised (§2 below) and graded
(§4/§5 below), update that row's `status` field from `pending` to one of:
- `honest` — no self-descriptive claim in the response contradicted its own payload, AND (if
  applicable) fragility/confidence metadata was present where the tool's domain warrants it.
- `dishonest` — at least one self-descriptive claim (receipt, verdict counter, coverage
  block, provenance note, "✓" mark, judgment_flag) contradicted its own payload. Log the
  finding per §6 below; the finding's `row_id` back-reference is this ledger row's `row_id`.
- `no_receipts` — the tool's response contains no self-descriptive claims to check at all
  (a bare data payload with no receipts/verdicts/flags) — not a failure, but record it so
  the coverage self-declaration (§7) is honest about what WAS and WASN'T checkable.
- `unreachable` — the tool could not be invoked at all for either chart (auth failure,
  missing required args not documented, hard error unrelated to the honesty question). Cross-
  file this as a Lane 1a finding too (tool-census first-contact failure) — Lane 4 does not
  own tool-reachability grading, only receipt-honesty grading, but must not silently drop an
  unreachable tool from its own completeness count.

Completeness for Lane 4 = 134/134 ledger rows marked with a terminal status (`honest` /
`dishonest` / `no_receipts` / `unreachable`), on BOTH charts where the tool is chart-scoped
(most tools take a `chart_id` argument; tools that are not chart-scoped are checked once and
noted as such).

## 2. Protocol — plan §5 Lane 4, TRANSCRIBED IN FULL (lines 184-190, verbatim)

The following is the plan's own text, character-for-character, per the anti-softening rule:
every sentence below MUST be present or strengthened in this brief's execution instructions,
never diluted into vagueness.

> ### Lane 4 — Receipt-honesty sweep
> Every self-descriptive claim any tool makes — receipts, verdict counters, coverage blocks,
> provenance notes, "✓" marks, judgment_flags — checked against its own payload in the same
> response. (R-38: varga_confirmed "D10✓" with zero varga rows; R-41: verdict says 0 fired
> while content serves 32 rows.) **Extension:** fragility/confidence metadata presence check
> — which serving paths carry ayanamsha_fragility, rectification-confidence, birth-time
> sensitivity at all (§10 gap 7).

Operationalized, this means: for EVERY tool in the ledger (§1), on EVERY call made to it
(realistic arguments, both charts where chart-scoped), the executor:

1. **Enumerates every self-descriptive claim in the response** — this is an exhaustive scan
   of the payload, not a spot-check. Self-descriptive claims include, but are explicitly NOT
   limited to (per charter §2.1 — examples never limit the search): receipt objects, verdict
   fields, verdict counters (e.g. "N fired", "N confirmed"), coverage blocks (e.g. "D10✓",
   "varga_confirmed"), provenance notes, checkmark/status glyphs, `judgment_flags`,
   `*_confirmed` booleans, `*_count` fields that summarize an array elsewhere in the same
   response, any field whose name or value asserts something ABOUT the rest of the payload
   rather than being data itself.
2. **Cross-checks each claim against the payload it describes, in the SAME response** — no
   follow-up call, no external verification at this step. Does the array the claim
   summarizes actually contain what the claim says it contains? Does the count match the
   array length? Does the "✓" correspond to actual non-empty, non-null underlying rows?
3. **Logs every mismatch as a class 5 (DISHONEST SELF-DESCRIPTION) finding**, per the finding
   schema (charter §3), citing the exact reproducible call and a verbatim evidence excerpt
   showing BOTH the claim and the contradicting payload side by side.
4. **Anchors against R-38 and R-41 as calibration cases** — per charter §4/plan §6
   "known-findings anchor set", the Lane 4 sweep MUST independently rediscover the R-38
   pattern (a coverage/confirmation flag asserting presence — e.g. `varga_confirmed:
   "D10✓"` — while the underlying row set for that claim is empty) and the R-41 pattern (a
   verdict/counter field asserting zero — e.g. "0 fired" — while the response's own content
   array serves populated rows, e.g. 32 rows) WHEREVER those patterns recur across the 134
   tools, not only on the two tools where they were originally observed. Failure to
   independently rediscover a live recurrence of either pattern where one exists is a
   lane-coverage hole per charter §5 "audit-of-the-audit."

## 3. Extension — fragility/confidence metadata presence check (plan lines 189-190, P-7)

Transcribed from the plan, verbatim: "**Extension:** fragility/confidence metadata presence
check — which serving paths carry `ayanamsha_fragility`, rectification-confidence, birth-time
sensitivity at all (§10 gap 7)."

This maps to plan §9 gap **P-7 — Fragility propagation**: "Birth-time sensitivity /
rectification confidence / ayanamsha fragility not attached to served claims." (P-7's audit
hook is explicitly "Lane 4 extension" per the plan's own P-gap table — this brief is the
implementing instrument for that hook.)

Operationalized: for EVERY tool in the ledger whose domain touches a claim that COULD be
sensitive to birth-time precision or ayanamsha choice — this includes, at minimum, any tool
serving: lagna-dependent facts (house placements, lagna-relative computations), any
timing/dasha-window computation, any nakshatra/pada boundary-sensitive value, any varga
(divisional chart) computation, any KP-system (sub-lord) computation, any yoga/dosha whose
constitution depends on exact cusp or degree — the executor:

1. **Checks whether the response carries ANY of the three named fragility/confidence fields**
   — `ayanamsha_fragility`, a rectification-confidence field (any naming variant — record the
   actual field name found, if any), a birth-time-sensitivity field (any naming variant) —
   attached to the specific claim(s) that would be affected by birth-time or ayanamsha
   uncertainty.
2. **Records presence or absence per tool, per fragility-dimension** (three yes/no columns:
   ayanamsha_fragility present? rectification-confidence present? birth-time-sensitivity
   present?) — this is a presence check, NOT a correctness check of the fragility values
   themselves (grading whether a given fragility SCORE is accurate is out of Lane 4's scope;
   Lane 4 only establishes whether the metadata channel exists at all for that serving path).
3. **Logs absence as a finding.** Per plan §4, absence of governed metadata the LLM needs to
   weight a claim correctly is itself a gap ("Data that arrives wrong... is a gap of equal
   standing" — extended here to data that arrives UNQUALIFIED where qualification is
   structurally required). Classify per charter §2: if the tool's domain is sensitivity-
   relevant and NO fragility field of any kind is ever served by ANY tool for that fact
   family, this is closer to class 1 (UNREACHABLE — the qualifying metadata simply does not
   exist anywhere in the serving surface) or class 9 (UNGOVERNED JUDGMENT — the consuming LLM
   is left to improvise its own confidence weighting with no system guidance); pick whichever
   the evidence supports and note the alternative class as a secondary tag per charter §7.1
   guidance for dual-class findings ("log the primary class per the finding's dominant
   defect, note the secondary in the evidence excerpt").
4. This extension check does NOT require its own separate ledger — mark the three presence
   columns as part of the same tools.jsonl row's Lane 4 pass (append them into the finding
   record or the state shard row for that tool; do not create a second ledger file for this
   sub-check, to avoid a second completeness-count surface to maintain).

## 4. Rubric — cite by name, do not re-derive

Per this brief's mandate: reference the relevant CHARTER.md §7 rubric by name rather than
inventing a new one. The closest drafted rubric is:

**CHARTER.md §7.1 — "Usable form" rubric** (derived from charter §2 class 6 UNUSABLE FORM
and class 7 DROWNED definitions). Its grading question 3 ("Budget proportionality — is the
payload size bounded in a way that is DISCLOSED to the consumer... versus an un-budgeted dump
that silently truncates or silently balloons... Undisclosed over/under-budgeting → fails
class 6") is directly adjacent to receipt-honesty: an undisclosed truncation is itself a
species of dishonest self-description (the response implicitly claims completeness by not
flagging incompleteness). Apply §7.1 question 3 as a SECONDARY check within Lane 4's sweep:
whenever a payload is truncated or capped, verify the response HONESTLY discloses that cap
(a "more available" flag or equivalent) — silent capping is a class-5/class-6 dual finding,
log both per §7.1's own dual-class instruction.

**Gap this brief fills:** CHARTER.md §7 does NOT contain a rubric drafted specifically for
class 5 (DISHONEST SELF-DESCRIPTION) — sections 7.1 through 7.5 cover usable form,
synthesizability-as-received, evidence-sufficiency, ranking-quality, and promise-shortfall
attribution respectively, but none is titled or scoped to receipt/verdict honesty. Section 2
above (the transcribed protocol) IS this lane's operative grading procedure, derived directly
from the plan's own verbatim Lane 4 description and the R-38/R-41 anchor cases, in the same
"derived, not verbatim-transcribed, to operationalize a judgment call the plan leaves as
prose" spirit that CHARTER.md §7's own preamble uses for its five rubrics. Per charter §7's
own gating rule, this derived protocol is likewise DRAFT and subject to the same Cowork
ratification gate (Fable 5 + native) before Lane 4 executes against it — this brief's
`status` frontmatter field reflects that gate explicitly.

## 5. Checkpoint / RESUME

**State shard (owned exclusively by this lane's conductor):**
`00_ARCHITECTURE/llm_consumption_audit/state/LANE4.md`

Per CHARTER.md §5 (RESUME protocol) and §6 (execution DAG, "State discipline under
parallelism"), transcribed operationally for Lane 4:

- `state/LANE4.md` is regenerated atomically at every checkpoint by the Lane 4 conductor —
  never partially written. A torn checkpoint write is itself an execution defect (charter §5
  atomicity contract), not an acceptable RESUME condition.
- Regeneration is IDEMPOTENT: `state/LANE4.md` is derived purely from the merged shard trace
  files (§8 below) plus the ledger's own `status` field counts — re-running the regeneration
  step twice from the same shard set produces the same file.
- **Content of `state/LANE4.md`** (minimum fields, atomic together):
  - `lane: 4`
  - `rows_total: 134` (ledger row count at last count — re-verify with `wc -l` each
    checkpoint in case the ledger grew)
  - `rows_done: <n>` (count of ledger rows with a terminal status, per §1)
  - `findings_count: <n>` (class 5 findings logged so far)
  - `fragility_check_rows_done: <n>` (count of sensitivity-relevant tools with the §3
    three-column presence check recorded)
  - `last_completed_shard_id: <shard-id>` — the RESUME pointer (see §8 for exact shard-id
    format)
  - `status: NOT_STARTED | IN_PROGRESS | COMPLETE`
- **RESUME semantics:** a follow-on/resumed Lane 4 conductor session reads `state/LANE4.md`
  first, reads `last_completed_shard_id`, and resumes shard assignment from the NEXT shard
  in sequence — never re-dispatches a completed shard, never silently skips an undone one.
  This holds identically for a clean session end or a mid-lane crash.
- Lane 4 does NOT write to the top-level `AUDIT_STATE.md` index directly — per charter §5,
  that index is regenerated by whichever conductor checkpoints, derived from ALL lane shard
  counts; Lane 4's conductor only ever writes `state/LANE4.md`.

## 6. Finding output

Every class-5 (and any secondary-class, per §4 dual-logging) finding follows the finding
schema at CHARTER.md §3, verbatim fields: reproducible call (exact tool + args), verbatim
evidence excerpt (the claim AND the contradicting payload, side by side), primary failure
class, severity, suspected layer, dedupe check against the register's existing ~200 rows
INCLUDING R-37..R-48 (charter §5/§2 anchor set). Genuinely new rows append to
`00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md`. Findings ALSO feed the machine-readable
findings JSON (plan §7 deliverable 2) at consolidation — Lane 4 does not build that file
itself; it produces per-finding records in its own shard traces (§8) that the consolidation
step merges in, per the execution DAG (charter §6): "CONSOLIDATION (sequential): merge →
dedupe vs register → calibration-anchor test (R-37..R-48 rediscovery) → Lane10-grade → report
+ findings JSON."

## 7. Deliverable spec (cross-referenced to plan §7)

Lane 4 is the primary implementing lane for plan §7 deliverable **3 — Register appends (new
rows only, deduped)**, specifically the class-5 subset of new rows, and it is a direct
contributor (not the sole owner) of deliverable **2 — the machine-readable findings JSON**
(its class-5 + fragility-absence records feed that file at consolidation, per §6 above).
Lane 4 also feeds the per-lane coverage self-declaration required for deliverable **1 — the
report** (§8 below is Lane 4's contribution to that self-declaration table). Lane 4 does NOT
own deliverables 4 (entity retrievability matrices — Lane 8), 5 (question-coverage matrix —
Lane 2), 6 (Concept×Retrievability matrix — Lane 1b), 7 (L1→MSR ingestion matrix /
graph-leverage report — Lane 9), 8 (Lane 2 evidence-plans), or 9 (Promise×Delivery ledger —
Lane 10) — Lane 4's output is exclusively: (a) class-5 register rows, (b) class-5 + fragility-
absence findings records for the findings JSON, (c) its `state/LANE4.md` shard, (d) the
coverage self-declaration row(s) below.

## 8. Coverage self-declaration template (TAP-9 style)

At Lane 4 close, populate this table (one row per surface swept; expand rows as needed — this
is a TEMPLATE, not the final content) into the report's coverage self-declaration section
(plan §7 deliverable 1, "per-lane coverage self-declaration: every surface audited or
explicitly deferred with reason"):

| surface | status (audited/deferred) | reason-if-deferred |
|---|---|---|
| All 134 `tools.jsonl` rows — receipt/verdict/coverage-block honesty check, chart 482012f1 | audited / deferred | |
| All 134 `tools.jsonl` rows — receipt/verdict/coverage-block honesty check, chart 1c826d5a | audited / deferred | |
| Non-chart-scoped tools (subset of the 134) — single-call honesty check | audited / deferred | |
| Sensitivity-relevant tools (subset — lagna, timing/dasha, nakshatra/pada, varga, KP,
  yoga/dosha domains) — ayanamsha_fragility presence check | audited / deferred | |
| Sensitivity-relevant tools — rectification-confidence presence check | audited / deferred | |
| Sensitivity-relevant tools — birth-time-sensitivity presence check | audited / deferred | |
| R-38 pattern (coverage-flag-vs-empty-rows) recurrence sweep across all 134 tools | audited / deferred | |
| R-41 pattern (verdict-zero-vs-populated-content) recurrence sweep across all 134 tools | audited / deferred | |
| §7.1 question-3 (undisclosed truncation) secondary check, applied within Lane 4 scope | audited / deferred | |

Every row MUST resolve to `audited` with a completeness count, or `deferred` with an
explicit, specific reason (per charter §4 criterion 4, "Coverage honesty") — a blank or
silently-omitted surface fails satisfaction criterion 4 for the whole audit, not just Lane 4.

## 9. Swarm decomposition (plan §12.7 — MANDATORY section)

Per plan §12.7 (native directive, review round 3), transcribed and applied specifically to
Lane 4:

**(a) Conductor + worker pattern.** Lane 4 runs as ONE conductor session plus a swarm of
fresh, short-lived worker sub-agents. The conductor owns the Lane 4 ledger view (the
`tools.jsonl` rows not yet terminal-status), shards the remaining work, and for each shard
spawns a FRESH sub-agent that receives ONLY: (i) the relevant excerpt of CHARTER.md (doctrine
§1/§2.1, taxonomy §2, finding schema §3, and §7.1 usable-form rubric — the worker does not
need §7.2-7.5, which belong to other lanes), (ii) this brief's §2 (protocol, verbatim), §3
(fragility extension), and §4 (rubric), and (iii) its own shard's ledger rows (tool
name/category/row_id, nothing more). Each worker gets full, undecayed attention on its shard
only — it never sees the other lanes' material and never sees other shards' rows. The worker
calls its assigned tool(s) for both charts, performs the §2/§3 checks, and writes ONE shard
trace file (§8(d) below). The conductor collects trace files, merges them into
`state/LANE4.md`, appends any new class-5 findings to the register, and updates the ledger
`status` field per row.

**(b) Shard key: per tool.** Each shard is a contiguous or conductor-chosen batch of
`tools.jsonl` `row_id`s (e.g., `T-001` through `T-010`, or a category-grouped batch such as
"all `phala` category tools") — one worker per shard, one shard covers one or more whole
tools (never split a single tool's honesty check across two workers — the same worker checks
both charts for a given tool, so the claim-vs-payload cross-check in §2 step 2 is always done
by an agent holding both responses).

**(c) Concurrency cap + throttling rule.** The conductor runs **5–10 concurrent workers**
(subscription-limit-bound, matching the plan's own stated figure for Lane 2's identical
concurrency-capped batching, per charter §6: "concurrency-capped batches, e.g. 5–10 workers,
the conductor throttles to subscription limits"). If the conductor observes rate-limit
signals (429s, throttling responses, or Claude Code subscription usage-window warnings), it
reduces the in-flight worker count (halving is a reasonable default) and re-queues any
shard whose worker was interrupted mid-call as NOT yet dispatched — an interrupted shard is
never marked done.

**(d) Merge protocol — no shared-file writes, no write contention.** Workers write ONLY their
own shard trace file, at `00_ARCHITECTURE/llm_consumption_audit/state/LANE4/shard-<id>.md`
(one file per shard, created fresh by that shard's worker, never appended to by any other
worker). No worker ever writes to `state/LANE4.md` (the lane-level index) or to the register
file directly — the CONDUCTOR ALONE reads all completed `state/LANE4/shard-<id>.md` files,
merges their findings and per-row statuses, appends deduped new findings to
`MARSYS_DEFECT_GAP_REGISTER_v2_0.md`, and regenerates `state/LANE4.md`. This guarantees zero
write contention: many workers can run concurrently because each owns an exclusive file path,
and exactly one process (the conductor) ever writes the shared index or the register.

**(e) Per-shard RESUME semantics — exact pointer format.** `last_completed_shard_id` in
`state/LANE4.md` holds the shard-id string exactly as used in its trace filename, e.g.
`"T-001-T-010"` for a range shard or `"phala-category-batch-1"` for a category-grouped shard
— the same string that appears in that shard's `state/LANE4/shard-<id>.md` filename (with the
`shard-` prefix and `.md` suffix stripped for the pointer value). A resumed conductor: (i)
reads `state/LANE4.md` for `last_completed_shard_id`; (ii) lists
`state/LANE4/shard-*.md` to confirm which shard trace files actually exist on disk (the
source of truth is the file, not just the pointer — if a shard trace file exists but was
never merged, i.e. `state/LANE4.md`'s counts don't yet reflect it, the conductor merges it
before dispatching new shards); (iii) computes the ledger rows NOT yet covered by any
existing shard trace file, and dispatches new shards only for those rows — this makes
resumption idempotent even if the pointer itself is stale, because the shard trace files on
disk are the authoritative record of completed work, and the pointer is only a fast-path
hint.

---

*End of LANE4_RECEIPT_HONESTY brief v1.0. Self-contained per §0. Governed by CHARTER.md
(canonical_id LLM_CONSUMPTION_AUDIT_CHARTER) for doctrine/taxonomy/finding-schema/
satisfaction-criteria/RESUME-protocol/execution-DAG. DRAFT status pending Cowork ratification
of both CHARTER.md §7 rubrics and this brief's §4 derived class-5 grading protocol, per plan
§12 item 4.*
