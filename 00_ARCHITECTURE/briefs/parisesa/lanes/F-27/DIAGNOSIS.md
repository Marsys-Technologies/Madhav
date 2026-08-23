---
lane_id: F-27
stream: S5 MŪLA
status: CONFIRMED-LIVE
severity: TIER2-HONESTY
diagnosis_incomplete_resolved: true
---

# F-27 — `mimamsa_calibration_get` domain param no-op

## 1. Live reproduction

`mcp__marsys-jis-direct__mimamsa_calibration_get` called with
`chart_id: 482012f1-710e-4a25-994a-93821f5871aa`, with and without
`domain: 'career'`.

- No domain: `result_hash: sha256:8e64ba7d16a7a2aa6f1155a250acafcaa717397aa6927fe90b496f33e1e833b5`
- `domain: 'career'`: `result_hash: sha256:8e64ba7d16a7a2aa6f1155a250acafcaa717397aa6927fe90b496f33e1e833b5`

**Identical.** Defect is real and live, not fixed. Raw responses saved to
`/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/a025ddc3-60fc-4e4f-914a-5f61252972b9/scratchpad/repro_no_domain.json`
and `repro_with_domain_career.json` (worktree is documents-only; scratchpad used
per session convention — contents pasted below for the record).

## 2. Claim decomposition

- (a) domain param exists in schema — TRUE: `register_p1_aliases.ts` declares
  `domain: z.string().optional()` on the `mimamsa_calibration_get` tool (line 1854).
- (b) result_hash identical with/without it — TRUE, confirmed live above.
- (c) real 57-row calibration data across 4 verdict classes exists — VERIFIED via
  `mcp__postgres__query` against `mimamsa_calibration` for this chart_id:
  `CONFIRMED=2, PARTIAL=23, REFUTED=7, UNRESOLVED=25` → total 57. Matches the
  finding's claim exactly.

## 3. Mechanism — file:line (the recovered gap)

Two-file mechanism, alias → primitive:

**`platform-mcp/src/tools/register_p1_aliases.ts:1849-1861`** — the
`mimamsa_calibration_get` tool declares and forwards `domain`:
```ts
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

**`platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`** —
the `query_calibration` primitive this alias calls **never declares `domain` in
`input_schema` (lines 27-43) and never reads `args.domain` in the handler
(lines 64-138)**. The handler only reads `chart_id`, `include_held_out`,
`promoted_only`:
```ts
async handler(args: Record<string, unknown>, _ctx: unknown) {
  const chart_id       = String(args.chart_id)
  const include_heldout = Boolean(args.include_held_out ?? false)
  const promoted_only  = Boolean(args.promoted_only ?? false)
  ...
```
The four SQL queries (`verdictSql` L72-84, `reliabilitySql` L86-92,
`multiplierSql` L94-101, `qaSql` L103-108) filter only on `chart_id` (plus
`leakageFilter`/`multFilter` derived from `include_held_out`/`promoted_only`).
None references a `domain` predicate. `domain` silently vanishes at the
alias→primitive boundary — the alias forwards it, the primitive drops it on
the floor.

**Root cause runs one layer deeper than "forgot to add a WHERE clause":** the
`mimamsa_calibration` table itself has **no `domain` column**
(confirmed via `information_schema.columns`: chart_id, match_id,
prediction_id, event_id, score_timing, score_magnitude, score_domain,
score_falsifier, score_manifestation, manifestation_channel,
composite_verdict, composite_score, base_rate_adjusted_skill,
evidence_admissibility, n_for_stratum, leakage_status,
scoring_formula_version, scored_at, base_rate, brier_vs_null). `score_domain`
is a *scoring dimension* (0-1 quality-of-domain-match score), not a life-domain
label. A real domain filter would need to `JOIN mimamsa_predictions ON
mimamsa_calibration.prediction_id = mimamsa_predictions.prediction_id` and
filter on `mimamsa_predictions.domain` (that table does carry a proper
`domain` column — confirmed via `query_predictions.ts:54-56,73,82`, which
correctly implements `domain = $n` filtering as a positive counter-example
in the same layer). So this isn't just an unwired parameter — the primitive
was never built with the join needed to honor it.

**Bonus finding, same mechanism:** `limit` and `offset` are likewise declared
and forwarded by the alias (`register_p1_aliases.ts:1857`, via `GlobalBase`)
but are equally never read by `query_calibration.ts`'s handler — also silent
no-ops, same root cause, same fix radius.

## 4. Sibling census

Within `platform/src/lib/retrieval/registry/layers/L5_mimamsa/`,
`query_calibration.ts` is the **only** file that fails to implement `domain`.
Every other domain-bearing file in the same layer implements it correctly with
a real `WHERE domain = $n` (or equivalent) predicate:
`query_life_events.ts:140`, `query_insights.ts:96`,
`query_manifestation_grammar.ts:87`, `query_manifestation_sets.ts:72`,
`query_predictions.ts:82`, `lel_intake_checklist.ts` (in-memory filter),
`query_mechanism_retrodiction.ts:317` (prefix-match filter). This is a
localized defect, not a layer-wide pattern.

One adjacent lead, **not independently verified** (out of this lane's
budget — flagging per Earned-Signal discipline rather than asserting): the
same alias file declares `domain` on `phala_mitigation_get`
(`register_p1_aliases.ts:1738-1747`, forwarding to primitive `mitigation_map`)
using the identical shape (`{ chart_id, domain } → callPlatformPrim(...,
{ chart_id, domain })`). The `mitigation_map` primitive lives in L4 Phala,
not L5 Mīmāṃsā, and was not located/read in this pass — worth a follow-up
lane to confirm or rule out the same no-op.

## 5. Blast radius

Does **not** share a file with F-10. F-10's mechanism (per the sibling lead)
is in `platform-mcp/src/tools/register_p1_synthesis.ts:950-955`
(`actionClass` computed but only applied to one of two queries). F-27's
mechanism spans `platform-mcp/src/tools/register_p1_aliases.ts` (alias) and
`platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`
(primitive) — a different alias file and a different primitive file from F-10.

Both are still the same **defect class** (declared-but-unapplied filter
param, alias/primitive silently drops it) and both are legitimate targets for
one shared CL-03 param-parity contract test: a generated test per capability
that asserts every declared optional filter param, when varied, changes
`result_hash` (or documents why it legitimately shouldn't, e.g. `limit`
with fewer total rows than the limit). F-27 adds a second confirmed instance
plus the `limit`/`offset` bonus no-op strengthening the case for that
generated harness over manual per-tool checks.
