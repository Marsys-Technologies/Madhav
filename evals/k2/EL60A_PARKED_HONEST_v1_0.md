---
artifact: EL60A_PARKED_HONEST
version: 1.0
status: PARKED-HONEST — verified gap, fix is outside γ Lane K2's manifest
lane: Elevation Campaign v2.1, Stream γ (PŪRṆA), Lane K2 · EL-60a
verified_by: evals/k2/reading_notes_accretion_check.ts + a live mcp__marsys-jis-direct__
  reading_notes_get call against chart_id 482012f1-710e-4a25-994a-93821f5871aa (2026-07-25)
---

# EL-60a — `reading_notes_get` auto-accretion: PARKED-HONEST

## The ask (charter, §γ.K2)

> **EL-60a** `reading_notes_get` auto-accretion per domain per session.

`ELEVATION_REGISTER_v1_0.md` EL-60 names `reading_notes_get` as "the single highest-value-per-
token response of the session" in the Fable serving-session that seeded this register, and asks
that it "accrete reading notes automatically per domain per session so the appendix compounds."

## What was checked

1. **Tool schema** (fetched live via `ToolSearch: select:mcp__marsys-jis-direct__reading_notes_get`):
   the tool takes exactly one parameter, `chart_id` (UUID). No `session_id`, no `domain`, no
   write/append parameter of any kind.
2. **Live call**: `mcp__marsys-jis-direct__reading_notes_get({chart_id:
   "482012f1-710e-4a25-994a-93821f5871aa"})` returns a `reading_notes_markdown` string.
3. **Source** (`platform-mcp/src/tools/reading_notes.ts`, read-only — outside γ's manifest to
   edit): the tool is a pure lookup —

   ```ts
   export const READING_NOTES_482012F1 = `# Verified Reading-Notes — chart 482012f1 ...`  // hardcoded

   export function readingNotesFor(chartId: string): string | null {
     return chartId === CANONICAL_CHART_ID ? READING_NOTES_482012F1 : null
   }
   ```

   The markdown is a **hardcoded, chart-keyed constant** sourced (per its own header comment)
   "Verbatim from POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md rows CR-38 / CR-71 / CR-80." There
   is no database table backing it, no `INSERT`/`UPDATE` call anywhere in the tool, and no
   parameter through which a caller (or a session) could contribute a new note.
4. **Cross-check**: the live call's `reading_notes_markdown` was byte-identical to the source's
   `READING_NOTES_482012F1` constant — confirming the live server is genuinely serving exactly
   this static string, not something a source-only read would miss.
5. **Automated verdict**: `evals/k2/reading_notes_accretion_check.ts` reproduces this
   mechanically (regex scan for write calls / session-or-domain scoping params) and returns
   `STATIC_MANUAL_LOOKUP_ONLY`. Re-runnable any time this tool's source changes, so this
   PARKED-HONEST disposition self-invalidates the moment accretion actually ships.

## The gap, stated exactly

`reading_notes_get` is currently a **manual, on-demand, single-chart, single-snapshot lookup
surface**, not an accreting appendix:

- **Per-chart**, not per-domain-per-session: the single markdown blob mixes wealth (CR-71),
  dasha-spine (CR-38/71), and yoga/karaka (CR-80) content into one undifferentiated document —
  there is no domain-scoped slicing, so a caller cannot ask for "just the wealth notes" or "just
  what accrued in the last session."
- **No write path exists**: nothing in this tool (or, so far as this read-only check could see,
  anywhere in `platform-mcp/src/tools/**`) can append a new finding to the notes as a reading
  session produces one. The content only changes if a future EDIT to the source file's hardcoded
  string is committed by hand.
- **No session boundary**: there is no concept of "this session's" notes vs. the standing
  appendix — every call for the same `chart_id` returns the identical static blob, forever, until
  someone edits the source.

## Why this is PARKED, not fixed, by Lane K2

The fix (a write path + domain/session-scoped storage for `reading_notes_get`) requires editing
`platform-mcp/src/tools/reading_notes.ts` and very likely a new DB table + migration under
`platform-mcp/src/lib/**` / `platform/migrations/**` — **both outside γ Lane K2's manifest**
(`platform/scripts/answer_eval.ts`, `evals/**`, `bench/**`,
`00_ARCHITECTURE/llm_consumption_audit/capability_map/**`). The charter's own rule (§γ.K2 lists
K2 as "consumption metric + standing battery upgrades," not a tools/** lane) and this lane's
explicit RULES ("Do NOT touch `platform-mcp/src/lib/**`/`tools/**` outside carve-outs") both
say the same thing: K2 verifies and documents this gap; it does not implement the fix.

## Disposition

**PARKED-HONEST.** Verified, reproducible (automated check + live cross-check), and out of
scope for this lane to remediate. Recommended follow-up shape for whichever lane/session DOES
own `platform-mcp/src/tools/**`:

1. A `reading_notes` (or similarly named) DB table keyed by `(chart_id, domain, session_id?,
   created_at)`, written to at the END of a reading (not mid-flight, to avoid partial/
   contradictory notes accreting).
2. `reading_notes_get` gains an optional `domain` filter and returns notes ordered
   newest-first, still degrading honestly to today's "no verified reading-notes are logged"
   empty state for a chart/domain with nothing accrued yet.
3. A write surface (new tool or an internal hook off the synthesis pipeline) that proposes a
   candidate note at session end for either auto-commit (deterministic, fact_id-grounded content
   only, per B.10) or human ratification, mirroring how `POST_REMEDIATION_CONSUMPTION_REGISTER`
   rows CR-38/71/80 were curated by hand into the current static constant.

## Reproduce this check

```
npx tsx evals/k2/reading_notes_accretion_check.ts
```
