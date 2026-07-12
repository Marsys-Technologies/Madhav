---
artifact: LANE1_CENSUS
type: BRIEF (Brief Foundry output — child lane brief, self-contained, fresh-session executable)
version: 1.0
status: READY FOR EXECUTION — gated on Cowork ratification of CHARTER.md §7 rubrics (plan §12 item 4)
program: LLM_CONSUMPTION_AUDIT_PLAN_v1_0
plan_ref: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md §5 Lane 1 (lines 133-165)
charter_ref: 00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md (canonical_id LLM_CONSUMPTION_AUDIT_CHARTER)
charts_in_scope:
  - 482012f1-710e-4a25-994a-93821f5871aa   # Abhisek (native)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a   # Abhinandan
receives_broadcast_from: [Item 0]   # per plan §12.7 DAG — Item 0's R-45 triage verdict annotates this lane mid-flight; does not block start
authored_by: Brief Foundry session (Claude Code), 2026-07-11
---

# LANE 1 — FULL CONCEPT-AND-VALUE CENSUS (1a tools · 1b values · 1c services · extensions)

## 0. How to use this brief (read this first, then nothing else, before starting)

This brief is SELF-CONTAINED. A fresh session with no other context can execute Lane 1
from this document alone, plus the two files it points to:

- **Charter (doctrine/taxonomy/schema/rubrics)** — cite, do not re-derive:
  `00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md`, canonical_id
  `LLM_CONSUMPTION_AUDIT_CHARTER`. Sections used by this lane: §1 doctrine (plan §2/§2.1),
  §2 9-class taxonomy (plan §4), §3 finding schema (plan §6), §4 satisfaction criteria
  (plan §8), §5 RESUME protocol, §6 execution DAG (plan §12.7, verbatim), §7.2
  "synthesizability-as-received" rubric (the operative rubric for Lane 1a — apply it
  verbatim; it is DRAFT pending Cowork ratification per plan §12 item 4 — do not begin
  substantive grading until that ratification is confirmed by the conductor's session-open
  check of CHARTER.md's `status` frontmatter).
- **This brief** — the lane protocol, ledgers, extensions, deliverable spec, coverage
  template, and swarm decomposition below.

Do not paraphrase or soften anything transcribed below from the plan. Where this brief
quotes the plan, the quote is verbatim; treat any apparent gap between the quote and your
intuition as a signal to re-read the quote, not to fill in from memory.

**This is a BUILD-then-EXECUTE lane, not a fix lane.** Zero fixes, zero code changes, zero
data writes beyond: ledger row status updates, shard trace files, the lane's own
findings/report artifacts, and register appends of genuinely new findings (dedup checked)
per Charter §3. All DB access is READ-ONLY SELECT via `mcp__postgres__query` — no
INSERT/UPDATE/DELETE/DDL, no exceptions, ever.

---

## 1. Ledger files (the lane's ground truth — completeness is a count query against these)

All paths are absolute from repo root `/Users/Dev/Vibe-Coding/Apps/Madhav/`. Full paths:

| Ledger | Path | Rows (at Foundry time) | Used by |
|---|---|---|---|
| Tool census | `00_ARCHITECTURE/llm_consumption_audit/ledgers/tools.jsonl` | 134 | 1a |
| Value-family census | `00_ARCHITECTURE/llm_consumption_audit/ledgers/value_families.jsonl` | 3058 | 1b |
| Services census | `00_ARCHITECTURE/llm_consumption_audit/ledgers/services.jsonl` | 30 | 1c |

Each row carries a `row_id` (e.g. `T-001`, `VF-1`, `SVC-001`) and a `status` field
(initially `"pending"`). **The lane's job is to mark every row's `status` to a terminal
value** (`done`, or a specific fail/defer code per §6 below) **and attach a finding record
(Charter §3 schema) wherever the row's retrievability grade is not a clean PASS.**
Completeness for satisfaction criterion 1 (Charter §4 / plan §8.1) is verified by:

```
grep -c '"status": "pending"' <ledger file>   # must be 0 at lane close
```

on all three files, per chart (tools.jsonl and services.jsonl rows are chart-agnostic
definitions tested against BOTH charts; value_families.jsonl rows carry
`chart_ids_observed` listing which charts the family's presence was derived against —
verify retrievability against both charts listed).

Row schema reference (fields present in each ledger; do not invent additional required
fields, but DO add a `finding_row_id` cross-reference field when you attach a finding):

- **tools.jsonl**: `row_id, tool_name, category, param_schema_hash, expose_to_planner,
  linked_data_asset_ids, source, status`
- **value_families.jsonl**: `row_id, table_name, family_key, grain, chart_ids_observed,
  source, status`
- **services.jsonl**: `row_id, service_name, system_or_domain, compute_on_demand,
  invocation_tool, compute_on_demand_test_spec, source, status`

**Discovery-pass surprise, read before starting 1c**: at least one ledger row set
(`value_families.jsonl` rows for `kala_activation` / `kala_activation_predicates`, see
`00_ARCHITECTURE/llm_consumption_audit/briefs/ITEM0_R45_TRIAGE.md` §3) already carries a
documented ambiguity the Item 0 broadcast resolves — check the Item 0 broadcast (§12
below) before grading any `kala_activation*` family row, and cite the Item 0 verdict in
the finding rather than re-deriving it.

---

## 2. Protocol — TRANSCRIBED VERBATIM from plan §5 Lane 1 (lines 133-165)

Do not summarize the following; it is the literal governing text. Where the brief adds
operational detail, it is clearly marked as an ADDITION, never a replacement.

> ### Lane 1 — Full concept-and-value census (upgraded per native review round 1)
> Three nested censuses; nothing stays untested at ANY of the three grains:
>
> **1a. Tool census (first-contact protocol).** Every MCP tool (~150), called ≥1× per chart
> with realistic arguments. Record: response shape, byte size, honesty markers,
> synthesizability-as-received (rubric in brief). Base rate observed so far: assets FAIL on
> first contact (bo_anveshana R-37, kala_activation R-45 — both failed the first time anyone
> consumed them).
>
> **1b. Value census (per-asset, per-value retrievability).** The native directive: "every
> single asset we have, every single value each asset provides, across the layers — is it
> being successfully retrieved appropriately by the LLM?" Method: enumerate from the DB
> (access granted) the complete value inventory — every fact_category × fact_key in
> chart_facts; every column/row family in chart_dashas, chart_divisionals, bodha_*, kala_*,
> phala_*, mimamsa_* tables; every L0 catalog family — then for EACH value family attempt
> wire retrieval and grade it against §4. Output: the master **Concept×Retrievability
> matrix** (deliverable 6), the audit's most important artifact. Sampling within a family is
> permitted only where the family is homogeneous (identical serving path); the family list
> itself is exhaustive, never sampled.
>
> **1c. Services census (real-time computation reachability).** Every SERVICE (as opposed to
> stored-data asset) — ga_chart_service, natal-positions compute, ephemeris/retrograde/
> transit services, panchanga service, muhurta finder, tajaka/varshaphal, dasha services
> across all 7 systems (Vimshottari/Yogini/Ashtottari/Chara/Narayana/Shoola/Kalachakra),
> prashna — tested for: can the consuming LLM reach it, invoke it with a real computed-on-
> demand request (data NOT in the data layer), and receive a usable result? (Native
> directive: values that must be calculated at real time are as much a part of completeness
> as stored values.)
>
> **Extensions folded in:** (a) L5 negative-knowledge slots consumption test (§9 P-2);
> (b) the FULL outcome loop live: mimamsa_outcome_record → re-retrieve → does it reach the
> next orientation context (§9 P-6); (c) dissent surfaces (synth_tail_divergence_get)
> consumability (§9 P-4); (d) recall_session / session-memory round-trip.

**§4 reference above** = plan §4, the 9-class failure taxonomy, transcribed verbatim at
Charter §2 — grade every 1a/1b/1c retrievability test against those 9 classes, assigning
exactly one PRIMARY class per Charter §3's finding-discipline rule ("every finding carries
... primary failure class (§4)"), with secondary classes noted in the evidence excerpt per
Charter §7.1 rule 5 where a payload fails more than one class simultaneously.

**§4 (plan §4) note on "§4" also appearing in Lane 1b's own line** — plan line 148 reads
"grade it against §4"; this is the SAME 9-class taxonomy (plan §4 / Charter §2), not a
distinct rubric. Do not conflate with Charter §4 (satisfaction criteria) — the plan's own
internal numbering and the Charter's numbering diverge; when quoting, use the FULL citation
(`plan §4` vs `Charter §4`) to avoid this exact ambiguity in the lane's own output.

---

## 3. Extensions (TRANSCRIBED VERBATIM from plan lines 162-165, folded into 1c scope)

> **Extensions folded in:** (a) L5 negative-knowledge slots consumption test (§9 P-2);
> (b) the FULL outcome loop live: mimamsa_outcome_record → re-retrieve → does it reach the
> next orientation context (§9 P-6); (c) dissent surfaces (synth_tail_divergence_get)
> consumability (§9 P-4); (d) recall_session / session-memory round-trip.

Operational spec for each, cross-referencing plan §9 (the planning-phase register table,
lines 340-361) verbatim rows:

### 3a. L5 negative-knowledge slots test (P-2)

Plan §9 row P-2, verbatim: "**Negative knowledge** | Absence-with-evidence not first-class
retrievable ("no dhana yoga, and here is the near-miss distance") | Lane 1 extension (L5
slots)."

Test: identify the `mimamsa_*` (L5) table(s)/tool(s) that are designed to hold or serve
negative-knowledge slots (an asset stating "X yoga/dosha/condition is ABSENT, with the
near-miss evidence for why it almost applied but did not") for BOTH charts. For each
candidate slot: (i) does the DB hold a row expressing the absence-with-evidence (not merely
silence — silence is not evidence of negative knowledge, it is just missing data); (ii) is
that absence-with-evidence reachable over the wire via any MCP tool; (iii) is it usable form
(Charter §7.1). Grade PASS/FAIL/PARTIAL per Charter §7.2 scale. Every L5 asset in
`asset_promises.jsonl` tagged `mi_*` that claims a negative-knowledge capability is a
mandatory test row — do not sample.

### 3b. Full outcome loop live test (P-6)

Plan §9 row P-6, verbatim: "**Longitudinal loop** | Outcome recording exists but consumption
of it (next-session context) unproven; calibration mission dies without it | Lane 1 outcome-
loop test."

Test (live, end-to-end, both charts where the write path allows a read-only-safe test —
if the only available test requires a WRITE to `mimamsa_outcome_record`, this test becomes
OBSERVATIONAL ONLY: verify via READ-ONLY SELECT whether any existing outcome records exist
for either chart, and if so, trace whether a subsequent orientation/context-serving call
demonstrably incorporates that record. Do NOT write a synthetic outcome record — this
session is SELECT-only, no exceptions, per the DB-access hard rule stated in the dispatch
context. If zero outcome records exist for both charts, this is itself the finding: report
UNREACHABLE-by-absence-of-test-data, do not fabricate a record to force a test.):
1. SELECT existing rows (if any) from `mimamsa_outcome_record` for both chart_ids.
2. For each existing outcome record, identify what "next orientation context" tool/call is
   supposed to re-surface it (per the asset's declared promise in `asset_promises.jsonl` or
   the L5 seal doc `00_ARCHITECTURE/L5_SEAL_AND_SHIP_REPORT_v1_0.md`).
3. Call that re-surfacing tool/path live and check whether the outcome record's content (or
   a derived calibration signal from it) actually appears in the response.
4. If no outcome records exist for either chart, log the finding as: class 1 UNREACHABLE
   candidate is INAPPLICABLE (nothing to reach); log instead as a coverage-honesty note
   (Charter §4 criterion 4) that the outcome loop is UNTESTED-FOR-LACK-OF-DATA, and route a
   recommendation (not a fix) that this becomes a P-6 requirement for the Fable 5 planning
   session to design a safe test-data path for.

### 3c. Dissent-surface (synth_tail_divergence_get) consumability test (P-4)

Plan §9 row P-4, verbatim: "**Adversarial retrieval** | No claim-conditioned counter-
evidence instrument (cross-examine own conclusions) | Lane 1 dissent-surface test."

Test: locate the `synth_tail_divergence_get` tool (or its live equivalent name — confirm
against the current MCP tool listing and `tools.jsonl`; if the name has drifted, log the
drift as its own finding per the Item 0 brief's precedent for tool-name drift). Call it for
BOTH charts with realistic claim-conditioning arguments (a specific prior finding/claim from
this chart's own served data, e.g. a strong yoga or a dasha-lord verdict already retrieved
earlier in this same lane's 1a pass). Grade: (i) does it return ANY counter-evidence/dissent
content distinct from the original claim's supporting evidence; (ii) is the dissent
attributable (cites L1 facts per CLAUDE.md §I B.3); (iii) usable form (Charter §7.1). This
is the operative test for P-4's "cross-examine own conclusions" capability — a tool that
merely echoes the original claim's support (no genuine counter-evidence) FAILS as an
EMPTY SHELL (plan §4 class 4).

### 3d. recall_session / session-memory round-trip test (d)

No plan §9 P-number is attached to this sub-extension in the verbatim quote (plan line 165
lists it as a bare fourth item, not tied to a P-gap row) — treat it as its own first-class
test, not folded into P-2/P-4/P-6.

Test: identify the `recall_session` tool (or live equivalent name, confirm against
`tools.jsonl`) and any session-memory write path it depends on. Round-trip test, both
charts: (i) if a prior session-memory write already exists for either chart (SELECT-only
check against whatever table backs it — identify via `asset_promises.jsonl` /
`CAPABILITY_MANIFEST.json` cross-reference), call `recall_session` and verify the recalled
content matches what a plausible prior session would have written; (ii) if no session-memory
row exists, this test is OBSERVATIONAL ONLY per the same SELECT-only constraint as 3b — log
absence-of-test-data honestly rather than fabricating a session to recall. Grade
reachability + usable form regardless of whether live content exists to validate against.

---

## 4. Rubrics — reference by name (Charter §7; do not re-derive)

- **Lane 1a retrievability grading** → Charter §7.2 "Synthesizability-as-received rubric"
  (PASS / PARTIAL / FAIL scale, applied on FIRST CONTACT — no follow-up calls beyond what
  the tool's own MCP description implies). Apply to every `tools.jsonl` row, both charts.
- **Lane 1b / 1c "usable form" determination** (used whenever a value/service response is
  technically reachable and the lane must decide class 6 UNUSABLE FORM vs class 7 DROWNED
  vs a clean pass) → Charter §7.1 "Usable form rubric" (the five numbered grading
  questions: referential resolvability, narration integrity, budget proportionality,
  signal-to-trivia ratio, and the both-classes-can-apply rule).
- **9-class failure taxonomy** (assign exactly one primary class per finding, secondary
  classes logged in the evidence excerpt) → Charter §2 (plan §4, verbatim).
- **Finding schema** (every finding's required fields) → Charter §3 (plan §6, verbatim).
- These rubrics are DRAFT per Charter §7's header — confirm Cowork ratification status
  (CHARTER.md frontmatter `status` field) before treating any borderline grading call as
  final; if ratification has not landed, grade provisionally and flag every borderline call
  for re-grading once ratified, per Charter §5 RESUME-protocol atomicity discipline (a
  provisional grade is not a torn checkpoint as long as it is explicitly marked provisional).

---

## 5. Checkpoint / RESUME instructions

- **State file (exclusive to this lane):**
  `00_ARCHITECTURE/llm_consumption_audit/state/LANE1.md` — owned EXCLUSIVELY by Lane 1's
  conductor. No other lane, worker, or session writes to this file.
- **Regeneration discipline (per Charter §5 / plan §12 item 3):** `LANE1.md` is regenerated
  atomically and idempotently from the shard trace files (see §12 below) — it is NEVER
  hand-edited incrementally. Every regeneration recomputes rows-done/rows-total/
  findings-count PURELY from the shard files on disk, so a concurrent or repeated
  regeneration by the same conductor is always safe (idempotent) and produces the same
  output given the same shard state.
- **RESUME pointer = last completed shard id.** `LANE1.md` records, per sub-lane (1a/1b/1c),
  the highest-numbered shard id that has a COMPLETE (not partial) trace file at
  `state/LANE1/shard-<id>.md`. A resumed conductor session reads `LANE1.md`, identifies the
  last completed shard per sub-lane, and spawns workers ONLY for shards after that pointer —
  never re-does a completed shard, never silently skips an unstarted one.
- **Atomicity contract (Charter §5, verbatim rule):** "every checkpoint write to a shard
  must leave that shard in a self-consistent, immediately-resumable state (row counts,
  findings-count, and status all updated together) — a partial/torn checkpoint write is
  itself an execution defect, not an acceptable RESUME condition." A worker that is
  interrupted mid-shard MUST NOT leave a half-written `shard-<id>.md` file marked complete;
  if the harness cannot guarantee atomic file writes, the worker writes to a `.tmp` path and
  renames on completion, and the conductor only ever reads finalized (non-`.tmp`) shard
  files when computing the RESUME pointer.
- **Ledger status as the completeness cross-check:** independent of the shard/state-file
  RESUME mechanism, the conductor can always verify total completeness with the ledger
  count query in §1 above (`grep -c '"status": "pending"'`) — this is the audit-of-the-audit
  cross-check; the two mechanisms (shard pointer vs ledger status) must agree at lane close,
  and any disagreement is itself logged as a finding (an execution-integrity defect, not a
  data finding).

---

## 6. Deliverable spec (plan §7, lines 307-323 — cross-referenced)

Lane 1 is the primary producer of two numbered plan deliverables and a contributor to a
third:

- **Deliverable 6** (plan line 318-319, verbatim): "The **Concept×Retrievability matrix**
  (Lane 1b) — every asset × every value family × retrievability grade; doubles as the seed
  data for the P-12 capability map." — Lane 1 PRODUCES this in full. Format: one row per
  `value_families.jsonl` `row_id`, columns: `row_id, table_name, family_key, grain,
  chart_id, retrievability_grade (PASS/PARTIAL/FAIL/UNREACHABLE-by-nonexistence),
  primary_class (plan §4), suspected_layer, finding_row_id (if any), notes`. Write to
  `00_ARCHITECTURE/llm_consumption_audit/deliverables/CONCEPT_RETRIEVABILITY_MATRIX.md` (or
  `.csv`/`.jsonl` sibling — conductor's choice, but MUST be machine-parseable per plan §7
  deliverable 2's "machine-readable" spirit; if `.md`, use a single well-formed table, not
  prose).
- **Contributes to Deliverable 2** (plan line 312-313, verbatim): "Machine-readable findings
  file (JSON): one record per finding with all §6 fields — the direct input to the Fable 5
  planning session." Every Lane 1 finding (1a/1b/1c/extensions) is emitted as a record in
  this shared findings JSON, conforming to Charter §3's finding schema, tagged
  `"lane": "1a"` / `"1b"` / `"1c"` / `"1-ext-P2"` / `"1-ext-P6"` / `"1-ext-P4"` /
  `"1-ext-d"` for provenance. Lane 1's conductor writes its own shard of this file (never
  the shared consolidated file directly — per §12 merge protocol below, only the
  CONSOLIDATION session merges lane-level findings files into the final deliverable 2).
- **Contributes to Deliverable 3** (plan line 314, verbatim): "Register appends (new rows
  only, deduped)." Any genuinely new finding (dedup-checked against the ~200 existing
  register rows including R-37..R-48 per Charter §3) is queued for append to
  `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` — Lane 1's conductor stages proposed new rows in its
  own output, actual register append happens at CONSOLIDATION per the plan §12.7 DAG
  (sequential tail), NOT mid-lane, to avoid concurrent-writer collision on the shared
  register file from multiple parallel lane conductors.
- **1c services census output** feeds Deliverable 7's sibling concern (plan line 320-321
  covers Lane 9's L1→MSR matrix and graph-leverage report — NOT Lane 1's territory; Lane 1c's
  services census output is its own artifact, not folded into deliverable 7): write
  `00_ARCHITECTURE/llm_consumption_audit/deliverables/SERVICES_REACHABILITY_MATRIX.md`, one
  row per `services.jsonl` row_id: `row_id, service_name, system_or_domain,
  compute_on_demand, reachable (Y/N), invoked_successfully (Y/N), usable_form (PASS/PARTIAL/
  FAIL per Charter §7.1), finding_row_id, notes`.
- **1a tool census output**: write
  `00_ARCHITECTURE/llm_consumption_audit/deliverables/TOOL_CENSUS_MATRIX.md`, one row per
  `tools.jsonl` row_id × chart_id (i.e., 2 rows per tool): `row_id, tool_name, category,
  chart_id, response_shape_summary, byte_size, honesty_markers_present (Y/N),
  honesty_markers_consistent (Y/N/N-A), synthesizability_grade (PASS/PARTIAL/FAIL per
  Charter §7.2), finding_row_id, notes`.
- **Extensions output**: each of 3a/3b/3c/3d produces its own short findings block, folded
  into the Deliverable-2-contributing findings shard (tagged as above), plus a one-paragraph
  narrative summary per extension appended to `LANE1.md`'s closing section for the
  consolidation session to read without opening every shard file.

---

## 7. Per-lane coverage self-declaration (TAP-9 style — mandatory at lane close)

Lane 1's conductor MUST emit this table (or its structural equivalent) at lane close, per
plan §7 deliverable 1's coverage-honesty requirement and Charter §4 criterion 4. Every row
below is a MINIMUM required surface; the conductor adds rows for anything else it
encounters that this brief did not anticipate — omission is itself a coverage-honesty
failure.

| surface | status (audited/deferred) | reason-if-deferred |
|---|---|---|
| 1a — all `tools.jsonl` rows, chart 482012f1 | audited / deferred | |
| 1a — all `tools.jsonl` rows, chart 1c826d5a | audited / deferred | |
| 1b — all `value_families.jsonl` rows, per `chart_ids_observed` | audited / deferred | |
| 1c — all `services.jsonl` rows, both charts | audited / deferred | |
| 1c extension (a) — L5 negative-knowledge slots (P-2), both charts | audited / deferred | |
| 1c extension (b) — outcome loop live test (P-6), both charts | audited / deferred | |
| 1c extension (c) — dissent-surface consumability (P-4), both charts | audited / deferred | |
| 1c extension (d) — recall_session round-trip, both charts | audited / deferred | |
| Item 0 broadcast consulted for `kala_activation*` rows | audited / deferred | |
| Deliverable 6 (Concept×Retrievability matrix) emitted | audited / deferred | |
| Deliverable 2 shard (findings JSON) emitted | audited / deferred | |
| Deliverable 3 staged register-append candidates emitted | audited / deferred | |
| Services reachability matrix emitted | audited / deferred | |
| Tool census matrix emitted | audited / deferred | |
| Ledger status cross-check (0 pending rows across all 3 ledgers) | audited / deferred | |
| RESUME/shard atomicity self-check at close | audited / deferred | |

"Deferred" entries are ONLY acceptable with a concrete reason (e.g. "tool requires live
write access outside SELECT-only scope — see §3b/3d observational-only note") — "ran out of
time" is not an acceptable reason under the plan's open-budget ruling (plan §3 Fixed
Decisions: "Budget | OPEN — no call/time cap, as long as value is added. Checkpointing
mandatory").

---

## 8. Swarm decomposition (MANDATORY — plan §12.7)

### (a) Conductor + worker pattern

Lane 1 runs as ONE conductor session that owns the lane's three ledgers
(`tools.jsonl`, `value_families.jsonl`, `services.jsonl`) plus the four extension tests. The
conductor:
1. Reads this brief + Charter.md once.
2. Shards each of 1a/1b/1c (see (b) below) into worker-sized batches.
3. Spawns FRESH sub-agents per shard — each worker receives ONLY: (i) the relevant excerpt
   of this brief (the sub-lane's protocol section + the rubric it must apply, cited from
   Charter, not re-copied at length into the worker prompt beyond what's needed), and
   (ii) its specific shard's ledger rows. Workers do NOT receive the full charter, the full
   plan, or other shards' rows — full attention, zero context decay, per plan §12.7's
   explicit design rationale ("each worker gets only the charter excerpt + its shard — full
   attention, zero context decay").
4. Collects each worker's shard trace file (never a shared file — see (d)).
5. Merges shard traces into `LANE1.md` (idempotent regeneration, per §5 above).
6. Updates ledger row `status` fields as workers report completion (this IS a lane-owned
   ledger write — the conductor is the sole writer of ledger status updates for this lane's
   three files; workers report status back to the conductor, they do not edit the ledger
   files directly, to avoid concurrent-writer collision on `tools.jsonl` /
   `value_families.jsonl` / `services.jsonl`).

### (b) Shard key

Per plan §12.7 verbatim ("Intra-lane sharding: Lane 1a by tool batches; 1b by table ×
fact_category; 1c by service"):
- **Lane 1a** — sharded by **tool batches** (e.g. 10-15 tools per shard, ~134 tools total →
  roughly 9-14 shards; conductor's exact batch size choice, but batches should group tools
  by `category` field in `tools.jsonl` where practical, so a single worker's shard shares
  domain context).
- **Lane 1b** — sharded by **table × fact_category** (e.g. one shard = all
  `value_families.jsonl` rows where `table_name = "chart_facts"` AND a given
  `fact_category` prefix from `family_key`, or for non-`chart_facts` tables, one shard per
  `table_name`; conductor determines exact grouping from the live `family_key` distribution
  at run time — the plan does not fix an exact count, only the dimension).
- **Lane 1c** — sharded **by service** (one shard per `services.jsonl` row, or small
  batches of 2-3 closely related services, e.g. the 7 dasha systems as one shard, since
  `services.jsonl` has only 30 rows total — one worker per service is affordable).
- **Extensions (3a/3b/3c/3d)** — each of the four extensions is its OWN shard (4 shards
  total), since each has a distinct test protocol and is not naturally sub-divisible by
  table/tool/service.

### (c) Concurrency cap + throttling rule

Concurrency cap: **5–10 concurrent workers** (subscription-limit-bounded, per plan §12.7
"concurrency-capped batches, e.g. 5–10 workers, the conductor throttles to subscription
limits" — this line appears verbatim under Lane 2 in the plan, and Lane 1's conductor
applies the SAME concrete cap since no lane-specific override is given and Lane 1's shard
count is comparable in order of magnitude). The conductor throttles as follows:
1. Start with a batch of up to 10 concurrent shard workers.
2. If any worker call fails on a rate-limit signal (HTTP 429-equivalent, explicit
   rate-limit error text, or a harness-level "usage window" notification), the conductor
   HALVES the next batch's concurrency (e.g. 10 → 5 → 2) and does not restore the higher
   cap until at least one full batch completes cleanly at the lower cap.
3. The conductor never queues more than the current cap's worth of in-flight workers at
   once — remaining shards wait in a queue, dispatched as slots free up.
4. No sleep-loop polling for capacity — the conductor dispatches the next queued shard
   immediately when a slot frees, and only backs off (per point 2) on an explicit
   rate-limit signal, never speculatively.

### (d) Merge protocol

- Workers write ONLY their own shard trace file, at
  `00_ARCHITECTURE/llm_consumption_audit/state/LANE1/shard-<id>.md` (the `<id>` scheme:
  `1a-<batch-n>`, `1b-<table>-<category-slug>`, `1c-<service-slug>`, `ext-P2`, `ext-P6`,
  `ext-P4`, `ext-d` — human-readable, collision-free ids).
- **No worker ever writes to `state/LANE1.md` (the top-level lane state file), any ledger
  file, the shared findings JSON, the register, or any deliverable file directly.** Every
  worker's output is confined to its own `shard-<id>.md`.
- The CONDUCTOR ALONE reads all completed shard files and merges them into: `LANE1.md`
  (state index), the three deliverable matrices (§6), the findings-JSON shard, and the
  staged register-append candidates. This eliminates write contention entirely — at no
  point do two processes write the same file.
- A shard trace file's required content (so the conductor can merge mechanically): for each
  ledger row covered by the shard, the row_id, the retrievability grade, the primary §4
  class (if any finding), the finding record (Charter §3 schema, if any), and — for 1a
  specifically — the Charter §7.2 PASS/PARTIAL/FAIL grade. A shard file missing any of these
  for one of its assigned rows is INCOMPLETE and the conductor does not advance the RESUME
  pointer past it.

### (e) Per-shard RESUME semantics

- **Pointer format:** `state/LANE1.md` records, per sub-lane, a line of the form:
  `<sub-lane>: last_complete_shard=<id>; shards_done=<n>/<total>; findings=<count>`
  (e.g. `1a: last_complete_shard=1a-batch-07; shards_done=7/12; findings=14`).
- Because shard ids for 1a/1c/extensions are not strictly ordinal (1c and extensions are
  keyed by name, not sequence number), "last_complete_shard" for those sub-lanes is
  interpreted as "the last shard the conductor confirmed complete", and the AUTHORITATIVE
  resume state is the explicit list of shard ids present (as finalized, non-`.tmp` files)
  under `state/LANE1/`. A resuming conductor computes: `remaining = all_expected_shard_ids
  - {ids of finalized shard-<id>.md files present}`, and dispatches workers only for
  `remaining`. This list-difference method is the primary RESUME mechanism; the
  human-readable pointer line in `LANE1.md` is a cheap summary for a human/dashboard read,
  not the source of truth.
- A shard file is "finalized" only if it exists at its final (non-`.tmp`) path per the
  atomicity contract in §5 — a `.tmp` file left over from an interrupted worker is treated
  as NOT done, and that shard is re-dispatched from scratch (workers are expected to be
  idempotent re-runs — re-doing a shard produces the same grades against the same live
  system state, modulo genuine system changes between runs, which is itself worth noting if
  observed).

---

## 9. Item 0 broadcast consumption note

Per plan §12.7 DAG: "Item-0's result is broadcast to Lanes 2/7 mid-flight (timing verdicts
annotated, not blocked)." Lane 1 is not named as a broadcast recipient in that line, but
Lane 1b's `kala_activation*` value-family rows are directly implicated by the R-45 defect
class (see §1's discovery-pass-surprise note above and `ITEM0_R45_TRIAGE.md` in full). Lane
1's conductor SHOULD read the Item 0 broadcast JSON (once emitted) before finalizing grades
on any `kala_activation` / `kala_activation_predicates` value-family row, and cite the Item
0 verdict directly rather than re-deriving the writer-vs-serving fork. If Item 0 has not yet
completed when Lane 1 reaches those rows, grade provisionally and flag for re-check, per the
same provisional-grading discipline as §4 above.

---

*End of LANE1_CENSUS v1.0. Cites `LLM_CONSUMPTION_AUDIT_CHARTER` (CHARTER.md) for doctrine,
taxonomy, finding schema, satisfaction criteria, RESUME protocol, and execution DAG. Full
plan citation: `LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md` §5 Lane 1 (lines 133-165), §9 rows P-2/
P-4/P-6 (lines 349-355), §7 deliverables 2/3/6 (lines 312-319), §12.7 swarm execution model
(lines 411-452).*
