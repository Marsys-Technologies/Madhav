---
lane: B
title: Envelope & budget reality
status: COMPLETE
authored_by: Claude (Sonnet 5), 2026-07-19
parent_brief: 00_ARCHITECTURE/briefs/RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0.md
scope: >
  Verify RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0 §1.2 claims against primary source
  (platform/src/lib/retrieval/envelope.ts, platform-mcp/src/lib/response_budget.ts,
  and all registered-tool handler files) as of 2026-07-19. READ-ONLY audit; no
  production source touched.
constraints_honored:
  - "READ-ONLY on platform/** and platform-mcp/**: confirmed, zero edits made."
  - "Only new file written: this report."
---

# Lane B Report — Envelope & Budget Reality

## Per-claim verdicts

### 1. "6 of ~123 handlers import envelope.ts" — **CORRECTED (adoption is narrower and differently shaped than the count implies)**

Actual direct importers of `buildRetrievalEnvelope` (canonical home
`platform/src/lib/retrieval/envelope.ts:361`, mirrored/codegen'd at
`platform-mcp/src/generated/envelope.ts:351`):

- `platform/src/lib/retrieval/synthesis/capability.ts:15,85` — `compose_large_n` (1 registry-side capability).
- `platform-mcp/src/tools/registry_bridge.ts:47,269` — a **shared internal wrapper** (`envelope()` helper at line 269) that itself is called from many `server.tool()` sites in that one 3000+-line file, not from 6 separate files.
- `platform-mcp/src/tools/register_p1_ganita.ts:21,116` — a similar shared wrapper used by multiple tools in that file.

Two more files import only `buildHonestPagination` (not the full envelope
builder): `L0_brahmagyan/list_entities.ts:12`, `L3_kala/query_convergence_windows.ts:15`.

**Correction to the plan's framing:** "6 of 123" undercounts by conflating
*files* with *handlers*. The real picture is worse for the plan's point (fewer
than 6 distinct authoring sites) but the tools reached through those sites are
more than 6 — e.g. `registry_bridge.ts`'s one `envelope()` wrapper is invoked
by at least 6 `server.tool()` registrations in that file alone (`get_chart_orientation`,
`get_signals`, `assess_marriage/career/health/wealth`-adjacent paths, `graha_portrait`,
`pact_query` and others — grep hits at lines 834, 1074, 2049, 2744, 2976).
Total registered MCP tools counted live: **115** `server.tool(` call sites across
21 files (brief's own corrected count elsewhere is 120 registered / 126 raw
`server.tool(` — the discrepancy is normal registry churn over the session
window, not a contradiction). Registry-layer `CapabilityDescriptor` count in
`platform/src/lib/retrieval/registry/layers/**`: **116** typed descriptors
(96 files exporting `CapabilityDescriptor`-shaped consts, several files
exporting more than one). The plan's "123" is in the right neighborhood but
not exactly reproducible from a single grep today — flag as **approximate,
not a precise invariant**.

**Verdict: CONFIRMED IN SPIRIT, STALE IN THE EXACT NUMBER.** Envelope adoption
is a small minority of the estate either way; the precise "6 of 123" ratio
should be replaced with "3 authoring sites (`capability.ts`, `registry_bridge.ts`'s
`envelope()` wrapper, `register_p1_ganita.ts`'s wrapper) feeding a low double-digit
count of tools, out of 115+ total registered tools."

### 2. Exact v3-default set — **CONFIRMED, exactly 3, plan is correct**

Grep for `resolveEnvelopeFormat(... ?? 'v3')` (i.e. defaults to v3 rather than legacy):

- `platform-mcp/src/tools/registry_bridge.ts:1857` → tool `judgment_query` (registered `registry_bridge.ts:1810`)
- `platform-mcp/src/tools/registry_bridge.ts:2422` → tool `graha_portrait` (registered `registry_bridge.ts:2405`)
- `platform-mcp/src/tools/registry_bridge.ts:2827` → tool `pact_query` (registered `registry_bridge.ts:2776`)

Every other `resolveEnvelopeFormat` call site defaults to `'legacy'` (e.g.
`register_p1_ganita.ts:516,823`; `registry_bridge.ts:720,977` — no `?? 'v3'`).
**Plan's claim exactly matches.**

### 3. `judgment_flags` full emitter census + d8 object-shape violation — **CONFIRMED**

Every file with a `judgment_flags` array construction/push (excluding type
declarations and pure pass-through re-exports):

- `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts` (many push sites: 512, 533, 561, 629, 632-637, 667, 670-681, 777, 789, 815, 822, 1007, 1010-1016) — `judgment_query`.
- `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts:595-620` — shared assess-domain builder (feeds `assess_marriage/career/health/wealth`).
- `platform/src/lib/retrieval/registry/layers/register_d10_pact.ts:192,243,257,293,345,369,418,432` — `pact_query`.
- `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dasha_lord_capability.ts:203-264` — `ganita_dasha_lord_capability_get`.
- `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts:424-552` — `get_dashas`.
- `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts:1236-1238` — pass-through merge, not an originator.
- `platform/src/lib/retrieval/session_pin.ts:78-208` (feeds `chart_selection.ts`, `session_tools.ts`, `api/mcp/session/route.ts`) — `chart_rebuilt_mid_session_pin_refreshed`.
- `platform-mcp/src/tools/registry_bridge.ts:799,1040-1042,2034,2728-2731,2961` — `get_chart_orientation`, `get_signals`, `graha_portrait`.
- `platform-mcp/src/tools/register_p1_ganita.ts:560-561,923-927` — chart-facts/signals-style tools.
- `platform-mcp/src/tools/register_p1_synthesis.ts:82` / `register_p1_reference.ts:87` — both emit `judgment_flags: []` (static empty — no honest-gap machinery wired at all).
- `platform-mcp/src/lib/response_budget.ts:284,346-350` — `finalizeMcpBudget` **injects its own** flag `` `response_still_over_${maxKb}kb_budget_after_full_trim` `` directly into whatever `judgment_flags` field the caller names — a cross-cutting emitter the plan's census didn't name.

**d8 object-shape violation — CONFIRMED exactly as claimed.**
`register_d8_assess_domain.ts:595-620` (function feeding `assess_career`/`assess_marriage`/
`assess_health`/`assess_wealth`) builds:
```ts
judgment_flags: [
  { claim: judgment_flag_note, requires_acharya_validation: true },
  ...(bearingYogaFirings.length === 0 ? [{ claim: '...', requires_acharya_validation: false }] : ...),
  { claim: '...', requires_acharya_validation: false },
]
```
— an array of `{claim, requires_acharya_validation}` **objects**, while every
other emitter (and the `envelope.ts:302,346` type declaration) treats
`judgment_flags: string[]`. This is a real, load-bearing type violation on
four of the plan's named "canonical assessment tools" (line comments at
1409/1441/1473/1505 in `registry_bridge.ts` confirm these are the current
canonical, non-alias names). **Confirmed, file:line matches the plan exactly.**

### 4. `envelope_version` stuck at v1 — **CONFIRMED, does not flip**

`envelope.ts:391,421` (`buildV3Envelope`/base builder) hardcodes
`envelope_version: 'v1'` in the object literal regardless of the `format`
argument — the field is never read from `format`/`resolveEnvelopeFormat`'s
output anywhere in the file. A v3-format response is distinguished only by
`response_format: 'v3'` plus the presence of the extra fields
(`chart_header`, `verdict`, etc.), never by `envelope_version`. Grepped every
assignment to `envelope_version` in both `envelope.ts` and its generated
mirror `platform-mcp/src/generated/envelope.ts` — both hardcode `'v1'`, no
conditional path exists. **Confirmed as stated; not stale.**

### 5. Cursor contents — **CONFIRMED exactly**

`envelope.ts:201-203`:
```ts
export function encodeCursor(nextOffset: number): string {
  return Buffer.from(JSON.stringify({ offset: nextOffset }), 'utf8').toString('base64')
}
```
and `decodeCursor` (206-214) only ever extracts `.offset`. No filter hash,
sort-order token, or facet fingerprint is encoded anywhere in the cursor.
**Confirmed exactly as claimed** — a cursor replayed against a call with
different `domain`/`facet`/`min_salience` etc. args would silently paginate
into a different logical result set with no detection.

### 6. `density_contract` exact declarations — **CONFIRMED count (6), CONFIRMED empty_reason split (3/3)**

Live grep for `density_contract:` object literals (excluding the type
declaration in `registry/types.ts:207`) — exactly 6 files:

1. `register_d9_judgment.ts:418` → `empty_reason: false` — comment: *"judgment_flags[] carries the honest-gap disclosures instead"* (this one has a principled *reason* for `false`, not a "not yet added" note — see below).
2. `L1_ganita/get_dasha_lord_capability.ts:148-152` → `empty_reason: true`.
3. `L1_ganita/get_vichara.ts:124-129` → `empty_reason: true`.
4. `L1_ganita/get_yoga_dosha.ts:71` → `empty_reason: false` — comment: *"explicit empty_reason string not yet added on this tool"*.
5. `L1_ganita/get_yoga_firings.ts:64` → `empty_reason: true`.
6. `L2_bodha/query_signals.ts:230` → `empty_reason: false` — comment: *"explicit empty_reason string not yet added"*.

**Correction to the plan's "three of the six declare empty_reason:false with a
'not yet added' note":** only **2 of the 3** `false` declarations carry a
literal "not yet added" note (`get_yoga_dosha.ts:71`, `query_signals.ts:230`).
The third `false` (`register_d9_judgment.ts:418`) is a **deliberate design
choice** (judgment_flags is the honest-gap channel for that tool instead),
not an unfinished stub. This is a real, citable distinction the plan blurs —
one gap is "not built yet," the other is "built differently, on purpose."
Net split is still 3 `false` / 3 `true`, count of 6 confirmed against both the
plan and the MCP handoff brief's cross-check.

### 7. `still_over_budget` unread callers — **CONFIRMED, exactly 4**

`response_budget.ts:83,226` defines `BudgetResult.still_over_budget`, set at
line 147 (`false` short-circuit) and 226 (`stillOverBudgetAfterSections`).
Grepped every call site of `applyResponseBudget` (the function that returns a
raw `BudgetResult`, as opposed to `finalizeMcpBudget`, which returns `T`
directly and internally re-derives its own over-budget check via
`estimateBytes` rather than reading `result.still_over_budget` — see
`response_budget.ts:288-351`). Direct `applyResponseBudget` callers that
receive a `BudgetResult` and read only `.content`/`.trim_report`, never
`.still_over_budget`:

1. `platform-mcp/src/tools/retrieval/holistic_bundle.ts:183-197` (`holistic_bundle_chart_facts`).
2. `platform-mcp/src/tools/phala_outlook.ts:278-289` (`phala_outlook_get`).
3. `platform-mcp/src/tools/phala_event_anchors.ts:350-351` (`phala_anchors_get`).
4. `platform-mcp/src/tools/register_p1_aliases.ts:433-434` (a signals-alias tool).

All 4 destructure `budgeted.trim_report` and `budgeted.content` but never
`budgeted.still_over_budget`. **Confirmed exactly — 4 callers, matching the
plan's number precisely.** Worth noting as an additional finding: even the
callers that *do* eventually get an honest signal (via `finalizeMcpBudget`,
used by `registry_bridge.ts` and part of `register_p1_aliases.ts`) get it
through a **second, independently-computed** check
(`response_budget.ts:344-351`, `response_still_over_${maxKb}kb_budget_after_full_trim`)
that does not read `BudgetResult.still_over_budget` either — meaning that
field is effectively **dead output on every call path in the codebase**, not
just unread by 4 callers. This is a gap the plan under-states.

### 8. Unclamped tool list — **CONFIRMED and broader than named**

Checked every `platform-mcp/src/tools/*.ts` file that registers at least one
`server.tool(...)` for any call to `applyResponseBudget`/`finalizeMcpBudget`/
`applyAutoBudgetToEnvelope`/`autoDetectTrimmableSections`. Files with **zero**
budget-trimmer calls (i.e. every tool they register is entirely unclamped):

`bo_2-8.ts` (1 tool), `chart_selection.ts` (2: `select_chart`, related),
`l0_brahmagyan.ts` (5), `l0_ephemeris.ts` (5), `mimamsa_lel_intake.ts` (1),
`mimamsa_outcome.ts` (2), `muhurta_finder.ts` (1), `phala_mitigation_map.ts` (1),
`read_classical_text.ts` (5), `reading_notes.ts` (1),
**`register_p1_reference.ts` (7: all `ref_*` reference tools — `ref_rules_search`,
`ref_yogas_get`, `ref_doshas_get`, `ref_dignity_reference_get`,
`ref_dasha_systems_get`, `ref_nakshatra_get`, `ref_transit_rules_get`)**,
`register_p2_dasha_lord.ts` (1), `register_vidhi_plan.ts` (1),
`scan_fetch_signals.ts` (1), `session_tools.ts` (2).

**Correction to the plan:** "reference tools entirely unclamped" is
CONFIRMED for `register_p1_reference.ts` specifically, but the plan's phrasing
implies this is the exception — it is not. **15 of 21 tool-registration files**
(covering roughly 36 of ~115 registered tools) never touch the budget
trimmer at all. This is a materially larger gap than "the reference tools."

### 9. `result_clipper.ts` orphan status — **WRONG — it is NOT orphaned**

`platform/src/lib/retrieval/adapters/shared/result_clipper.ts` (77 lines,
exports `clipString`, `clipResult`, `exceedsLimit`) has a live caller:
`platform/src/lib/retrieval/adapters/bulk_context/bundler.ts:10,47` —
`clipResult(result.content, { max_kb: SECTION_MAX_KB, strategy: 'truncate_end' })`.
`bundler.ts` is itself imported by `adapters/bulk_context/synthesizer.ts` and
`adapters/hybrid/adapter.ts` — both real, non-test modules on the bulk-context/
hybrid retrieval path. `response_budget.ts:12` explicitly documents the
distinction ("a sibling utility for a different consumer: LLM-context
trimming"), consistent with the MCP handoff brief's framing, but the plan's
§1.2 line ("two incompatible clippers coexist") did not assert orphan status
directly — this verdict corrects an implicit reading some downstream
consumers might draw. **Verdict: not orphaned; it is a live, narrower-purpose
clipper on the bulk-context/hybrid path, distinct from and non-overlapping
with `response_budget.ts`'s MCP-facing trimmer.**

### 10. `chart_header` best-effort paths — **CONFIRMED silent-null, no honesty flag**

Two layers of best-effort swallowing, neither of which emits a
`judgment_flags` entry on failure:

- **Inner:** `platform/src/lib/retrieval/chart_header.ts:30-97`
  (`fetchChartHeader`) wraps its 3 queries in `try {...} catch { }` (line 90-93)
  with the comment *"a failure here must never fail the instrument's own
  response. Fields stay null."* — on any DB error, the returned `ChartHeader`
  object has all content fields `null` but is otherwise indistinguishable from
  a legitimately-empty chart. No flag is added to signal the failure.
- **Outer:** `registry_bridge.ts:810-817` (`get_chart_orientation`), `:1052-1058`
  (`get_signals`), `:2037-2043` (`graha_portrait`) each independently call the
  `marsys://tool/L1/get_chart_header` capability via `callRegistryCapability`
  inside a `try {...} catch { chart_header = null }` — again silent, no
  `judgment_flags` push, no distinguishing signal between "chart genuinely has
  no header data" and "the header fetch threw."

**Confirmed as a real, citable gap** (not explicitly a plan §1.2 claim, but
squarely inside Lane B's brief and directly relevant to A-05/§N.6 honesty
discipline) — chart_header failures are the one place in the envelope where
"best-effort" degrades to "silent," contradicting the density/honesty
doctrine applied everywhere else in the same files (e.g. the very next lines
in these same handlers build honest `judgment_flags` for zero-row cases).

---

## Gaps found (beyond the plan's named claims)

1. **`BudgetResult.still_over_budget` is dead code on every path**, not just
   unread by 4 callers — even `finalizeMcpBudget`'s own internal honesty check
   recomputes independently rather than reading the field it's named for.
2. **Unclamped-tool surface is ~15 files / ~36 tools**, not just "reference
   tools" — a materially bigger gap than the plan's framing suggests.
2b. Two of the four "canonical assessment tools" naming comments in
    `registry_bridge.ts` (1409/1441/1473/1505) explicitly flag that their
    former `apex_*` aliases were retired — worth cross-referencing with Lane
    C's dark-primitive/alias-cutover findings.
3. **`register_p1_synthesis.ts:82` and `register_p1_reference.ts:87`** emit a
   static `judgment_flags: []` — these tools have the *field* present in their
   envelope shape but no honest-gap machinery behind it at all (a stub, not
   even a partial implementation) — distinct from, and worse than, the
   `density_contract`/`empty_reason:false` "not yet added" gap already named.
4. **`chart_header` best-effort failure is silent**, at both the DB-query
   layer and the capability-call layer — no `judgment_flags` entry ever
   fires for a header fetch failure, in contradiction to the honesty
   discipline the same files apply elsewhere.
5. **`result_clipper.ts` is misdiagnosable as dead code** from a shallow grep
   of `platform-mcp/**` alone (it is `platform/**`-only, MCP-side files never
   import it) — worth flagging so downstream doc work doesn't repeat the
   error the other direction.
6. Precise handler/descriptor counts ("123", "6 of 123") do not reproduce
   exactly from a single fresh grep today (115 `server.tool(` sites, 116
   `CapabilityDescriptor`-typed consts) — close enough to not be "wrong," but
   not an exact, re-derivable invariant either. Treat all such counts in the
   plan as approximate census snapshots, not frozen facts, and prefer the
   codegen'd census (once R-1's projection compiler lands) as the source of
   truth going forward.

---

## Closed flag-enum candidate list (raw material for R-2.2)

Classified **token** (short, snake_case, machine-checkable, stable across
calls) vs **prose** (a full sentence / templated narrative — the anti-pattern
RETRIEVAL_STRATEGY_v1_0 §3 flags) vs **hybrid** (`token: <prose detail>` —
the token prefix before the colon is machine-checkable, the remainder is not).

**Pure tokens:**
- `zero_rows_returned` (`register_p1_ganita.ts:561,924`)
- `zero_entity_profiles` (`registry_bridge.ts:799`)
- `response_size_truncated` (`registry_bridge.ts:1042`)
- `partial_portrait_section_errors` (`registry_bridge.ts:2729`)
- `no_parivartana_or_catalog_matches_for_graha` (`registry_bridge.ts:2730`)
- `no_mahadasha_periods_for_graha` (`registry_bridge.ts:2731`)
- `partial_page_more_available` (`register_p1_ganita.ts:925`)
- `chart_rebuilt_mid_session_pin_refreshed` (`session_pin.ts:98`)

**Hybrid (`token: prose` — the templated-prefix pattern that dominates the codebase):**
- `unmapped_lord_graha: '<graha>' ...` (`get_dasha_lord_capability.ts:208`)
- `house_class_unresolved: ...` (`get_dasha_lord_capability.ts:247`)
- `ratification_unavailable: ...` (`get_dasha_lord_capability.ts:250`)
- `zero_rows: no Vimśottarī level-1 MD lords ...` (`get_dasha_lord_capability.ts:255`)
- `karaka_unresolved: <name> — <error>` (`register_d9_judgment.ts:512`)
- `from_moon_resolution_failed: <error>` (`register_d9_judgment.ts:533`)
- `varga_confirmation_failed: <error>` (`register_d9_judgment.ts:561`)
- `yoga_firings_fetch_failed: <error>` (`register_d9_judgment.ts:629`)
- `bearing_yogas_empty: ...` (`register_d9_judgment.ts:632`)
- `bearing_yogas_no_domain_match: ...` (`register_d9_judgment.ts:637`)
- `yoga_signal_corroboration_fetch_failed: <error>` (`register_d9_judgment.ts:667`)
- `bearing_yogas_corroboration_caveat: ...` (`register_d9_judgment.ts:670`)
- `notably_absent_not_checked: ...` (`register_d9_judgment.ts:681`)
- `kala_activations_trimmed: ...` (`register_d9_judgment.ts:777`)
- `kala_activations_single_cycle: ...` (`register_d9_judgment.ts:789`)
- `timing_anchored_false: ...` (`register_d9_judgment.ts:815`)
- `timing_hook_failed: <error>` (`register_d9_judgment.ts:822`)
- `afflictions_fetch_failed: <error>` (`register_d9_judgment.ts:1007`)
- `catalog_only_rows_present: <n> row(s) ...` (`register_p1_ganita.ts:928`)
- `response_still_over_<N>kb_budget_after_full_trim` (`response_budget.ts:349` — the one cross-cutting injected flag)

**Full-prose only (no stable token prefix at all — pure sentence):**
- register_d8_assess_domain.ts's object-shaped entries (see §3 above) —
  `{claim: "...", requires_acharya_validation: bool}` where `claim` is always
  a full sentence with no leading token; this is simultaneously the
  object-shape violation and the worst "prose-only" offender since there
  isn't even a colon-delimited prefix to salvage.

**Assessment for R-2.2:** the hybrid `token: prose` pattern is already
~80% of the way to a closed vocabulary — the token prefix is consistent
enough (snake_case, stable across calls for the same failure mode) that a
mechanical extraction (split on first `: `, canonicalize the prefix) would
recover a real enum for most emitters with no semantic loss. The
register_d8 object-shaped entries are the one family that needs an actual
rewrite, not just extraction, since they carry no token at all.

---

## Model/effort ledger

- Model: Sonnet 5 (agent invocation), default reasoning effort.
- Files read/grepped (non-exhaustive list of the load-bearing ones):
  `platform/src/lib/retrieval/envelope.ts`,
  `platform/src/lib/retrieval/chart_header.ts`,
  `platform/src/lib/retrieval/session_pin.ts`,
  `platform/src/lib/retrieval/synthesis/capability.ts`,
  `platform/src/lib/retrieval/registry/catalog.ts`,
  `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`,
  `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts`,
  `platform/src/lib/retrieval/registry/layers/register_d10_pact.ts`,
  `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dasha_lord_capability.ts`,
  `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts`,
  `platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_dosha.ts`,
  `platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_firings.ts`,
  `platform/src/lib/retrieval/registry/layers/L1_ganita/get_vichara.ts`,
  `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts`,
  `platform/src/lib/retrieval/adapters/shared/result_clipper.ts`,
  `platform/src/lib/retrieval/adapters/bulk_context/bundler.ts`,
  `platform-mcp/src/lib/response_budget.ts`,
  `platform-mcp/src/generated/envelope.ts`,
  `platform-mcp/src/tools/registry_bridge.ts` (multiple sections, ~3000 lines),
  `platform-mcp/src/tools/register_p1_ganita.ts`,
  `platform-mcp/src/tools/register_p1_synthesis.ts`,
  `platform-mcp/src/tools/register_p1_reference.ts`,
  `platform-mcp/src/tools/retrieval/holistic_bundle.ts`,
  `platform-mcp/src/tools/phala_outlook.ts`,
  `platform-mcp/src/tools/phala_event_anchors.ts`,
  `platform-mcp/src/tools/register_p1_aliases.ts`,
  plus every `platform-mcp/src/tools/*.ts` file for the budget-clamp census.
- ~25 grep/read tool calls; no writes/edits to any production source; no DB
  access; no deploys.
- Zero claims silently skipped — all 10 numbered items + the flag-enum output
  have an explicit verdict above.
