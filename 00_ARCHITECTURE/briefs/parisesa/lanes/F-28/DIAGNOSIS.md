# F-28 — DIAGNOSIS

Stream: S2 MĀTRĀ (assigned per LEASES.json) · Class: CL-05 · Severity: TIER2-HONESTY ·
2× diagnosis budget (DIAGNOSIS-INCOMPLETE list) · Chart: `482012f1-710e-4a25-994a-93821f5871aa`
(Abhisek Mohanty, canonical)

**Headline result: the mechanism is now closed, but the fix site is NOT in S2's lease.**
The true root cause lives in `platform/src/lib/retrieval/registry/tool_name_bridge.ts`
(S1 DVĀRA's lease). See §6 LEASE VERDICT and `NEEDS_LEASE.md`.

## 1. Live reproduction — REPRODUCES, exactly as claimed (not "roughly")

`mimamsa_calibration_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa')` called live this
session. Full raw JSON saved to `evidence_live.json` in this lane dir. Relevant excerpt:

```json
"results": [{"content": "{\"chart_id\":\"482012f1-710e-4a25-994a-93821f5871aa\",\"verdict_distribution\":[{\"composite_verdict\":\"UNRESOLVED\",\"n\":25,\"mea…[truncated for budget]"}]
```

Measured the string preceding the `…[truncated for budget]` marker: **exactly 120 characters**
(`python3 -c "print(len(s))"` on the captured substring → `120`). The corpus's "roughly 120" is
precise, not approximate — it matches the code's own `MAX_STRING_CHARS = 120` constant
byte-for-byte (see §3).

**DB cross-check (live `mcp__postgres__query`, not from the archived evidence file):**
```sql
SELECT composite_verdict, count(*) FROM mimamsa_calibration
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' GROUP BY 1
```
→ `CONFIRMED=2, PARTIAL=23, REFUTED=7, UNRESOLVED=25` — **57 rows, 4 verdict classes**, exactly
matching the claim's "57-row/4-verdict-class" figure. Additionally queried the three other
tables `query_calibration` reads: `mimamsa_reliability` = 6 rows, `mimamsa_multipliers` = 9 rows,
`mimamsa_qa_eval` = **168 rows** for this chart — the QA harness table is the dominant
contributor to the payload size that trips the 40KB ceiling (see §3).

**Live JSONSchema for `mimamsa_calibration_get`** (fetched via ToolSearch, not read from a
stale doc): `{chart_id: uuid required, domain: string, limit: integer 1-1000, offset: integer,
additionalProperties: false}`. **No `budget_kb`, `response_format`, or verbosity parameter
exists.** Confirms the "no override parameter" sub-claim directly from the live schema, not by
inference.

## 2. Claim decomposition

The finding's `claim` field: *"mimamsa_calibration_get's response content is unconditionally
hard-truncated to roughly 120 characters with no override parameter, making the real underlying
57-row/4-verdict-class calibration data practically unrecoverable through this tool even though
it demonstrably exists in the DB."* Four distinct sub-assertions:

- **F-28a (truncation is real and ~120 chars):** CONFIRMED — exactly 120, live-measured.
- **F-28b (no override parameter):** CONFIRMED — live JSONSchema has `additionalProperties:
  false` and no budget/format/verbosity field. Also confirmed at the handler level:
  `query_calibration.ts`'s `input_schema` (L5_mimamsa) declares only `chart_id`,
  `include_held_out`, `promoted_only` — and the MCP-facing alias schema in
  `register_p1_aliases.ts` doesn't even expose `include_held_out`/`promoted_only` to the caller,
  exposing `domain`/`limit`/`offset` instead, none of which the handler reads (see §3, a
  related-but-distinct no-op gap, likely F-27's territory not F-28's, flagged for the record).
- **F-28c (real data exists in DB):** CONFIRMED — 57/4-class calibration rows, plus 6+9+168 rows
  across the other three tables the tool is supposed to surface, all live-verified via direct SQL.
- **F-28d (practically unrecoverable through this tool):** CONFIRMED — the only recovery hint the
  response offers is `trim_report[0].recover_via = {"instrument": "response_format:legacy",
  "hint": "full untrimmed response"}`, but `response_format` is not a parameter this tool's
  schema accepts at all (§1). The hint points at a lever the caller cannot pull. `drill_pointers`
  (top-level) is `[]` — empty, no alternate path offered either. There is no way, via this tool,
  to retrieve `reliability_curve`, `multipliers`, or `qa_results`/`qa_summary` at all — the
  truncation happens before any of the four named data sections separately exist in the response;
  they are all inside the one collapsed string.

## 3. Mechanism → file:line — the DIAGNOSIS-INCOMPLETE gap is now closed

**Important correction to the mechanism note in the corpus.** The corpus's `mechanism` field said
only "DIAGNOSIS-INCOMPLETE on exact file:line ... same recovery caveat as F-27 (concurrent-write
race deleted the original finding's full detail)." In fact the archived audit evidence file
(`git show audit/paripurna2-evidence:pp2-audit/evidence/mimamsa_calibration_get__valid_domain_native.json`)
survived the race intact and already names two exact file:line sites — `response_budget.ts:454`
and `register_p1_aliases.ts:188-201` — which I independently re-derived and confirmed still
accurate at `origin/main` tip. **What the archived note did NOT have, and what this DIAGNOSE pass
adds, is the actual upstream root cause** — the archived note stops at "truncation fires because
no override param exists"; it does not explain *why the entire calibration payload is a single
opaque string in the first place*, which is the real defect. Traced three layers deep:

### 3a. The truncation lever itself — `response_budget.ts:454` (S2's own HOT file, working as designed)

```ts
// response_budget.ts:447-454
/**
 * Bounded-depth walk that truncates any string value longer than `MAX_STRING_CHARS`
 * ...Only touches string VALUES...the true last-resort lever once every declared array
 * section and the trim_report/drill_pointers machinery have already given everything
 * they can.
 */
const MAX_STRING_CHARS = 120
```
Called from `finalizeMcpBudget` at `:424`, only inside the `if (estimateBytes(content) >
maxBytes)` branch reached AFTER: (1) all declared array sections have been floored to 0
(`applyResponseBudget`'s two-pass `runPass('declared')`/`runPass('zero')`, `:260-280`), (2)
`trim_report` itself has been progressively shrunk to a single summary entry (`:396-410`), and
(3) `drill_pointers` merges have been reverted (`:412-415`). **This function is doing exactly
what its doc-comment says: a genuine last resort.** It is not itself misconfigured — it correctly
identifies that after every other lever has been pulled, the response is still over budget, and
the only remaining thing to cut is scalar string bytes. **This is NOT the bug.**

### 3b. Why nothing else was available to trim — the real defect, `tool_name_bridge.ts:237-262` (S1's lease)

`query_calibration.ts`'s handler (`platform/src/lib/retrieval/registry/layers/L5_mimamsa/
query_calibration.ts:127-139`) returns the STANDARD, DOCUMENTED `ToolResult` shape
(`platform/src/lib/retrieval/registry/types.ts:533`: `content: string | object`) — a rich
**object** with four separate arrays:
```ts
return {
  content: {
    chart_id,
    verdict_distribution: verdictResult.rows,   // 4 rows (grouped)
    reliability_curve:    relResult.rows,        // 6 rows
    multipliers:          multResult.rows,       // 9 rows
    qa_results:           qaResult.rows,         // 168 rows
    qa_summary:           { total: ..., fail_count: ... },
    filters:              { include_heldout, promoted_only },
  },
  is_error: false,
}
```
This crosses into the legacy "ToolBundle" wire shape via `capabilityResultToToolBundle` →
`toToolBundleResults`, which the file's own doc-comment (`:211-232`) calls **"the ONLY place the
ToolBundle ↔ ToolResult shape conversion lives."** Its branch logic:
```ts
// tool_name_bridge.ts:237-262
function toToolBundleResults(content: unknown): ToolBundleResult[] {
  if (content == null) return []
  if (Array.isArray(content)) { ... }                       // not this shape
  if (typeof content === 'object' && 'results' in content) { ... }  // not this shape either
                                                              //  (outer object has content/is_error, no results key)
  // Single ToolResult (content: string | object)
  if (typeof content === 'object' && 'content' in content) {
    const inner = (content as Record<string, unknown>)['content']
    const str = typeof inner === 'string' ? inner : JSON.stringify(inner)
    return [{ content: str }]
  }
  ...
}
```
For `query_calibration`'s result, `content` = `{content: {chart_id, verdict_distribution, ...},
is_error: false}`. It does NOT have a top-level `results` key, so the middle branch is skipped.
It DOES have a `content` key, so the **"Single ToolResult"** branch fires: `inner` = the whole
four-array object, `typeof inner !== 'string'`, so `JSON.stringify(inner)` collapses
`verdict_distribution`/`reliability_curve`/`multipliers`/`qa_results`/`qa_summary`/`filters` —
**everything** — into ONE opaque string, wrapped in a 1-item `results` array:
`[{content: "<huge JSON string>"}]`.

This happens **before** the response ever reaches `dualOutput`/`finalizeMcpBudget` in
`register_p1_aliases.ts`. By the time the budget mechanism sees the payload, the real structure
(four independently-sized arrays, one of them 168 rows) is already gone — flattened into a single
string field inside a 1-item array. `autoDetectTrimmableSections` only declares a section for a
top-level array **longer than 10 items** (`response_budget.ts` comment block, confirmed in
F-46's sibling diagnosis at `:495-521`); a 1-item `results` array never qualifies. So
`applyResponseBudget` runs with `sections = []` — no structural trimming is possible — and the
**entire** ~168-QA-row + 9-multiplier + 6-reliability + 4-verdict payload's fate is decided by
the blind 120-char scalar slice in §3a. The live response's `trim_report` shows exactly this
degrade path: a single `(trim_report)`-path entry reading "full trim_report omitted to fit
budget" (the whole-response fallback from `applyResponseBudget:283-289`, not a per-field entry) —
proof no per-section trim ever ran.

### 3c. The registration/schema layer — `register_p1_aliases.ts:1845-1857` + `:183-201` (S5's lease)

```ts
// register_p1_aliases.ts:1844-1857
server.tool(
  'mimamsa_calibration_get',
  '[Phase-1 alias] Query calibration stats for a chart (same as query_calibration).',
  {
    chart_id: z.string().uuid().describe('Chart UUID'),
    domain:   z.string().optional(),
    ...GlobalBase,
  },
  async ({ chart_id, domain, limit, offset }) => {
    try {
      const data = await callPlatformPrim('query_calibration', { chart_id, domain, limit, offset }, principal)
      return dualOutput(data)
    } catch (err) { return errOut('mimamsa_calibration_get', String(err), { chart_id }) }
  }
)
```
This is where the "no override parameter" sub-claim (F-28b) is structurally true: the schema
exposes `chart_id`/`domain`/`limit`/`offset` and nothing else. `dualOutput` (`:183-198`, this
same file) is what invokes `finalizeMcpBudget` with a fixed `maxKb: 40` and no caller-supplied
`budgetKbRequested` — there is no parameter on this tool a caller could even pass to raise the
ceiling. Note this file's `dualOutput` doc-comment (`:171-179`) already documents an **earlier,
partial fix** for a closely-related shape ("D-1.6 S-5... the surgical-primitives ToolBundle shape
`{result:{results:[{content:"<json string>"}]}}`... routing through `finalizeMcpBudget` instead
... adds its last-resort bounded-depth long-string truncation fallback, which DOES reach that
shape"). That prior fix ensured the response doesn't error or silently drop data — it made the
truncation *fire safely* — but did not address the upstream collapse in `tool_name_bridge.ts`
that makes truncation the only option in the first place. F-28 is the residual the D-1.6 S-5 fix
left behind.

### Net: three files, three streams

| Layer | File:line | Role | Lease |
|---|---|---|---|
| Root cause | `tool_name_bridge.ts:237-262` (`toToolBundleResults`, "Single ToolResult" branch) | Collapses a structured multi-array `ToolResult.content` object into one opaque string before any array-based trimmer can see it | **S1 DVĀRA** |
| Truncation lever | `response_budget.ts:447-454` (`MAX_STRING_CHARS=120`, `truncateLongStringsInPlace`) | Correct, working-as-designed last resort; not itself defective | S2 MĀTRĀ (already owned) |
| Schema/registration | `register_p1_aliases.ts:1844-1857` + `:183-198` (`mimamsa_calibration_get` + `dualOutput`) | No override param exposed; fixed `maxKb:40`, no `budgetKbRequested` threaded | **S5 MŪLA** |
| Possible alternate fix site | `L5_mimamsa/query_calibration.ts:127-139` (handler return shape) | Could pre-shape its own response as `{results: [...]}` (the escape hatch `toToolBundleResults` already recognizes) instead of a flat object, or thread `limit`/`offset`/`domain` itself | **S3 SATYA** |

## 4. Sibling census

### 4a. The truncation-lever file (`response_budget.ts`) has exactly one `MAX_STRING_CHARS`
definition and one call site (`:424`, inside `finalizeMcpBudget`) — not a repeated-pattern defect
at that layer. No further siblings there.

### 4b. The root-cause file (`tool_name_bridge.ts`) — `toToolBundleResults` is used by
**every** surgical-primitive tool call, via `capabilityResultToToolBundle`, which is what
`getToolByName(...).retrieve()` (the function every `callPlatformPrim` call in
`register_p1_aliases.ts` ultimately reaches) calls internally. Checked the contract:
`ToolResult.content: string | object` (`types.ts:533`) is the standard, documented handler return
shape for **every** registry capability across L0–L5:

```
$ find platform/src/lib/retrieval/registry/layers -name "*.ts" -not -path "*__tests__*" -not -name index.ts | wc -l
172
$ grep -rl "content: {" ... | xargs grep -l "results:\s*\[" 2>/dev/null | wc -l
0
```

**Zero of the 172 capability handler files pre-shape their own response as `{results: [...]}`**
(the one escape hatch in `toToolBundleResults` that avoids the collapse). Every one of them
returns the standard `{content: <object|string>, is_error}` shape. This means the collapse-to-
string defect is not narrow to `query_calibration` — it is the **default behavior of the adapter
for the entire registry** the moment a handler's `content` is an object (which is the norm, not
the exception). The defect is only **observable** when two conditions both hold: (a) the tool is
in the `MCP_TO_RETRIEVAL_TOOL` surgical-primitive whitelist (~70+ entries,
`tool_name_bridge.ts:512-...`) so it's reachable via `register_p1_aliases.ts`'s `callPlatformPrim`
at all, and (b) the collapsed JSON string is large enough to exceed the 40KB ceiling once
wrapped in the full MCP envelope, so `truncateLongStringsInPlace` actually engages.

**Named same-shape siblings within S3's `L5_mimamsa/**` lease** (same `{chart_id, rows:
rowsRes.rows, count, total_matching, more_available, ...}` return pattern as `query_calibration`,
confirmed by file inspection, **not independently reproduced live in this DIAGNOSE pass** — flagged
honestly rather than guessed, since live-confirming each one's actual row count/byte size is a
SPEC-stage-scale task given ~70 whitelisted tools × handler inspection):
`query_attribution.ts`, `query_insight_embeddings.ts`, `query_journal.ts`,
`query_load_bearing.ts`, `query_mimamsa_discoveries.ts`, `query_manifestation_sets.ts`.
`query_insights.ts` and `query_signal_families.ts` share the object-content shape too (different
field names, same structural exposure). A full whitelist-wide byte-size audit (which of the
~70 surgical primitives actually produce >40KB responses today) is recommended as a SPEC-stage
task, not attempted here — it is a straightforward but wide mechanical sweep (call each tool live
with a data-rich chart, measure response bytes), better done once the fix's shape is decided
(§6) than guessed at now.

### 4c. F-27 relationship (the corpus's own cross-reference)
F-27 is in the same DIAGNOSIS-INCOMPLETE list and the corpus's `mechanism` field for F-28
explicitly says "same recovery caveat as F-27." Based on the recovered archived evidence file's
`mechanism_trace.alias_forwards_domain`/`handler_ignores_domain` fields (register_p1_aliases.ts
forwards `domain` but `query_calibration.ts`'s handler never reads it), **F-27 is almost
certainly the `domain`-parameter-no-op finding**, a CL-03-shaped defect (S5's lease,
`register_p1_aliases.ts` + capability SQL) — mechanically distinct from F-28's truncation
mechanism, sharing only the same tool and the same archived-evidence-file recovery story. Not
this lane's claim to fix; noted for the conductor in case F-27's own DIAGNOSE lane wants this
cross-reference.

## 5. Blast radius

- **§N.6 Serving Density Principle (violated, item 4 "density signaling is data, not
  narration"):** the caller has zero machine-readable indication that `verdict_distribution`
  (4 rows) / `reliability_curve` (6) / `multipliers` (9) / `qa_results` (168) exist as four
  independently-sized fields — they are invisible, flattened into one truncated string before any
  density signal could be attached to them individually.
- **§N.8 Earned-Signal Principle (adjacent violation):** `trim_report[0].recover_via.instrument =
  "response_format:legacy"` is a recovery pointer this specific tool's schema cannot honor
  (§1/§2 F-28d) — a signal naming a lever that doesn't exist for the caller who received it. Not
  as clean an instance as the named §N.8 cases (this is a generic fallback message shared by
  every tool going through this degrade path, not a bespoke false-positive flag), but the same
  family: a "here's how to recover" claim with no real path behind it for this caller.
- **CL-00 controls:** not assessed against the 27-control list in this DIAGNOSE pass (out of
  scope per plan §3; SPEC stage checks `parisesa_gate.py`'s cheap subset before build).
- **`tool_name_bridge.ts` (S1's file) — high fan-out risk:** any fix to `toToolBundleResults`
  affects every surgical-primitive tool (§4b), including all of S1's own findings that touch this
  file (F-11, F-25, F-67, F-73, F-09, F-17, F-18, F-43, F-123, F-38) plus, per LEASES.json's own
  notes, F-09's mechanism is ALREADY routed to live in S2's `response_budget.ts` while F-123 lives
  in S4's `kala_views/{now,explain}.ts` — meaning `tool_name_bridge.ts` is a genuine multi-lane
  hotspot even before F-28 is added to it. Any fix here must be scoped narrowly (e.g., only the
  "Single ToolResult, object content" branch) and coordinated with S1 to avoid colliding with
  their in-flight lanes on the same file.
- **`response_budget.ts` (S2's own HOT file):** shared with F-13, F-56, F-111, F-112, F-122,
  F-12, F-36, F-37, F-45, F-44, F-14, F-15, F-46, F-124, F-125 (same file-sharing note F-46's own
  diagnosis records) — sequence within S2, don't parallelize edits. F-28's own likely SPEC
  direction does NOT require editing `response_budget.ts` at all (§3a concludes it's working
  correctly) — this reduces contention risk for this specific lane.
- **`register_p1_aliases.ts` (S5's file):** already has a known S1↔S5 ordered-handoff in
  `LEASES.json` (S1 goes first on the ~19 `dualOutput` toolName-default sites, CL-11, then
  re-leases to S5). F-28's touch on this file (if the SPEC decides to add a `budget_kb` param to
  `mimamsa_calibration_get`'s schema) would need to sequence after that handoff completes, per
  the existing plan.
- **`L5_mimamsa/**` (S3's file):** F-28's possible alternate fix site
  (`query_calibration.ts`'s handler pre-shaping its own response) sits in S3's lease alongside
  S3's own CL-13 disclosure lanes (F-31/F-33/F-34/F-35/F-78/F-134) and CL-08/CL-09 lanes. No
  direct line-level conflict identified (different function in the same directory), but S3 should
  be aware a fourth stream may propose a spec touching this directory.

## 6. LEASE VERDICT

**`LEASES.json` (`git show origin/par/coordination:00_ARCHITECTURE/briefs/parisesa/LEASES.json`)
confirms F-28 is formally assigned to S2_MATRA's `findings` list**, and S2's `owns` array is:
`platform-mcp/src/lib/response_budget.ts`, `platform-mcp/src/tools/registry_bridge.ts`, and five
named `kala_views/*.ts` files. **None of these is where F-28's root cause lives.**

The mechanism this DIAGNOSE pass traced spans three files across three streams:
1. **Root cause — `platform/src/lib/retrieval/registry/tool_name_bridge.ts:237-262`** —
   S1 DVĀRA's lease (explicitly named in S1's `owns` list in LEASES.json).
2. **Schema/registration — `platform-mcp/src/tools/register_p1_aliases.ts:1844-1857,183-198`**
   — S5 MŪLA's lease (explicitly named).
3. **Possible alternate fix site — `platform/src/lib/retrieval/registry/layers/L5_mimamsa/
   query_calibration.ts:127-139`** — S3 SATYA's lease (`L5_mimamsa/**` explicitly named).

**S2's own file (`response_budget.ts`) contains the truncation lever, which this diagnosis
concludes is working as designed — not the defect.** S2 has no file in its lease that is the
actual fix site for F-28's claim.

**Verdict: PAR-F-28-NEEDS-LEASE.** Per the plan's own rule ("a lane that discovers its mechanism
lives in another stream's file does not edit it — it posts `PAR-<F-nn>-NEEDS-LEASE <path>` and
the conductor either re-leases or routes the build to the owning stream with the completed spec
attached"), this lane does not proceed to Stage S with an S2-owned fix. See `NEEDS_LEASE.md` for
the formal flag and the two dispositions offered to the conductor.

## Evidence

Live JSON captured this session for `mimamsa_calibration_get(chart_id=...)` — saved to
`evidence_live.json` in this lane dir, including the live JSONSchema, the DB cross-check queries
and results, and the exact 120-character measurement. Archived corpus evidence recovered via
`git show audit/paripurna2-evidence:pp2-audit/evidence/mimamsa_calibration_get__valid_domain_native.json`
(read-only, this file survived the "concurrent-write race" the corpus's `mechanism` field
referenced intact — its `mechanism_trace`/`truncation_mechanism` fields independently corroborate
this DIAGNOSIS's §3a/§3c file:line citations; this DIAGNOSIS adds §3b, the upstream
`tool_name_bridge.ts` root cause, which the archived note did not have).
