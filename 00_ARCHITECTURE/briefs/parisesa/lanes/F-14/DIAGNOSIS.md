---
lane: F-14
stream: S2 (MĀTRĀ)
stage: D — DIAGNOSE
status: REPRODUCES (worse than claimed — deeper/wider than the audit's own mechanism text)
diagnosed: 2026-08-16
files_owned_this_lane: platform-mcp/src/tools/registry_bridge.ts (S2 HOT lease)
companion_lanes: F-15, F-124 (same file, overlapping/identical mechanism — see §6)
---

# F-14 DIAGNOSIS — assess_health never returns the W7 substance-inline reading digest

## 1. Live reproduction

**Reproduce_cmd (verbatim):**
```
mcp__marsys-jis-direct__assess_health({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', reading_depth: 'deep_dive'})
```

Ran against the live MCP server (`mcp__marsys-jis-direct__assess_health`), canonical chart
`482012f1-710e-4a25-994a-93821f5871aa`. Raw output saved to
`evidence_deep_dive.json` in this directory. Top-level `object` keys:

```
{"kernel": {...}, "composition_report": {...}}
```

**No `reading`, `domain_completeness`, or `completeness_directive` key anywhere in the
response — confirmed absent.** `composition_report.omitted_sections` = `["grounding",
"evidence"]`, `included_layers` = `["kernel"]` only.

**Verdict: REPRODUCES.** The finding's claim ("assess_health never returns … reading digest
/ domain_completeness / completeness_directive fields") is true today, live, exactly as
stated. This is not `ALREADY-FIXED`.

**Important correction to scope, found during live repro:** at the literal `deep_dive`
setting the reproduce_cmd specifies, the entire `grounding` layer (not just `reading`) is
missing — for a *reason the finding does not name* and that also affects `assess_career`
(which the finding says works). See §3.3. I re-ran at default (`standard`) depth as well
(`evidence_standard_depth.json`) to isolate the domain-family-specific defect from this
budget-side effect. At standard depth, `grounding` IS present but still carries no `reading`
key (the key itself is absent, not empty) and no `domain_completeness`/`completeness_directive`
key — this isolates and confirms the finding's actual claim.

## 2. Claim decomposition

The F-14 claim decomposes into four distinct sub-assertions:

| # | Sub-claim | Verified? |
|---|---|---|
| C1 | `assess_health` never returns a `reading` field | TRUE — key is absent (not empty) at every depth/budget tried |
| C2 | `assess_health` never returns `domain_completeness` | TRUE — but for a **broader** reason than C4 states (see §3.2/§3.4) |
| C3 | `assess_health` never returns `completeness_directive` | TRUE — same broader reason as C2 |
| C4 | Root cause is "`DOMAIN_READING_FAMILIES` has no `'health'` entry" | TRUE but **incomplete** — this is the second of two independent gates that both block C1, and C2/C3 have a THIRD, separate cause not named by the finding at all (see §3.4) |

## 3. Mechanism to file:line (traced, code quoted)

### 3.1 — `DOMAIN_READING_FAMILIES` missing `'health'` (confirms cited :1034)

`platform-mcp/src/tools/registry_bridge.ts:1020-1037` (read in the read-only checkout):

```ts
const WEALTH_READING_FAMILIES = [ /* 13 entries */ ] as const
const CAREER_READING_FAMILIES = [ /* 12 entries */ ] as const

const DOMAIN_READING_FAMILIES: Record<string, readonly string[]> = {
  wealth: WEALTH_READING_FAMILIES,
  career: CAREER_READING_FAMILIES,
}
```

**Line 1034 confirmed exact** — `DOMAIN_READING_FAMILIES` has exactly two keys, `wealth` and
`career`. No `health` key exists. The companion maps at lines 1040-1043
(`DOMAIN_READING_VARGAS`, `DOMAIN_READING_HOUSES`, `DOMAIN_READING_KARAKA_CODE`,
`DOMAIN_READING_KARAKA_LABEL`) are likewise `wealth`/`career`-only.

### 3.2 — `attachDomainReading`'s early-return (confirms cited :1568-1574, now :1569-1573)

`platform-mcp/src/tools/registry_bridge.ts:1569-1575`:

```ts
export async function attachDomainReading(
  response: Record<string, unknown>, domain: string, chart_id: string, ayanamsha_id: string, principal: Principal,
): Promise<void> {
  const { reading, families_served, families_total } = await buildDomainReading(domain, chart_id, ayanamsha_id, response, principal)
  if (families_total === 0) return
  response['reading'] = reading
  ...
```

And `buildDomainReading` (line ~1505):
```ts
const families = DOMAIN_READING_FAMILIES[domain]
if (!families) return { reading: [], families_served: 0, families_total: 0 }
```

**Cited line range confirmed correct** (drift of ~1 line from comment/formatting churn, not
a real discrepancy) — `domain='health'` → `DOMAIN_READING_FAMILIES['health']` is `undefined` →
`families_total=0` → `attachDomainReading` returns before ever setting
`response['reading']`, `response['domain_completeness']`, or `response['completeness_directive']`.

### 3.3 — THE MORE PROXIMATE CAUSE the finding does not name: the call sites themselves don't exist for `assess_health`

This is the load-bearing correction to the finding's mechanism. Reading the actual
`assess_health` tool handler, `registry_bridge.ts:3040-3077`:

```ts
async ({ chart_id, ... }) => {
  if (!chart_id) return errorOutput('assess_health', 'chart_id is required')
  try {
    const effectiveVerbosity = resolveEffectiveVerbosity(verbosity, reading_depth)
    const [{ orientation_context, orientation_ok }, data] = await Promise.all([
      fetchOrientationContext(chart_id, normalizeAyanamsha(ayanamsha_id), principal, effectiveVerbosity),
      callRegistryCapability('marsys://tool/L-DOMAIN/assess_health', {...}, chart_id, principal),
    ])
    const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
    return dualOutputBudgeted(buildAssessResponse(response, 'assess_health', budget_kb, effectiveVerbosity))
  } catch (err) { ... }
}
```

Compare `assess_career`'s handler, `registry_bridge.ts:3010-3037`, which is otherwise
identical EXCEPT for two extra lines before the final return (lines 3029-3032):

```ts
const response = { orientation_context, orientation_ok, ...data as Record<string, unknown> }
// Elevation α: back the naive-caller entrypoint with dossier's 100%-accounted territory.
attachDomainCompleteness(response, 'career', chart_id)
// SATYA-ŚEṢA W7: serve the reading itself, inline, not just a pointer to one.
await attachDomainReading(response, 'career', chart_id, normalizeAyanamsha(ayanamsha_id), principal)
return dualOutputBudgeted(buildAssessResponse(response, 'assess_career', budget_kb, effectiveVerbosity))
```

**`assess_health`'s handler never calls `attachDomainCompleteness` or `attachDomainReading`
at all.** Even if `DOMAIN_READING_FAMILIES['health']` existed and were fully populated,
`assess_health` would still never surface `reading`/`domain_completeness`/
`completeness_directive`, because the functions that set those fields are simply not
invoked in this handler. `assess_wealth`'s handler (`registry_bridge.ts:3110-3117`) has the
same two calls as career, plus a third (`attachLeverageIndex`, wealth-only by design).

**So there are two independent, both-necessary gates, not one:**
1. The handler must call `attachDomainCompleteness(response, 'health', chart_id)` +
   `await attachDomainReading(response, 'health', ...)` — currently it calls neither.
2. `DOMAIN_READING_FAMILIES` (and the four companion maps) must carry a `'health'` key —
   currently none do.

Both must be fixed together; fixing only #2 (as the finding's mechanism text implies) would
still leave `assess_health` silent, because the call sites (#1) don't exist.

### 3.4 — A THIRD, separate, newly-discovered defect: `domain_completeness`/`completeness_directive` are dropped for ALL FOUR assess_* tools, not just health/marriage

`attachDomainCompleteness` (line 835) sets `response['domain_completeness']` (line 838) and
`attachDomainReading` (line 1589) sets `response['completeness_directive']`. Both mutate the
transient `response` object built before `buildAssessResponse` runs.

But `buildAssessResponse` (`registry_bridge.ts:2886-2951`), the Sāra-composition function
that assembles the final `kernel`/`grounding`/`evidence` envelope for ALL FOUR assess_* tools
(added by the merged `ekv/a-09-sara-kernel` work, per its own comment "A-09 (F-56/F-111):
Sāra composition for assess_* tools"), builds `grounding` from an explicit allow-list
(lines 2908-2927):

```ts
const grounding: Record<string, unknown> = {
  orientation_context: response['orientation_context'],
  orientation_ok: response['orientation_ok'],
  domain: response['domain'],
  chart_id: response['chart_id'],
  ayanamsha_id: response['ayanamsha_id'],
  reading_checklist: response['reading_checklist'],
  step_results: response['step_results'],
  gochara_sweep: response['gochara_sweep'],
  contradictions: response['contradictions'],
  house_analysis: response['house_analysis'],
  citations: response['citations'],
  provenance: response['provenance'],
  yoga_fact_ids: response['yoga_fact_ids'],
}
// assess_career/wealth: reading + completeness injected by attachDomainReading/Completeness
if (response['reading'] !== undefined) grounding['reading'] = response['reading']
if (response['completeness'] !== undefined) grounding['completeness'] = response['completeness']
```

**Line 2925 checks `response['completeness']`. Nothing ever sets that key.**
`attachDomainCompleteness` sets `response['domain_completeness']` (not `'completeness'`) and
`response['completeness_directive']` (never referenced by `buildAssessResponse` at all).
Both are silently dropped when the Sāra envelope is assembled — **for every assess_* tool,
including `assess_career` and `assess_wealth`, which the finding claims DO surface
`domain_completeness`.**

Live-verified: `assess_career` and `assess_wealth` at standard depth (see
`evidence_career_comparison.json`) both populate `grounding.reading` correctly, but neither
response contains a `domain_completeness` or `completeness_directive` key anywhere, top-level
or nested. This is a real, separate regression — most likely introduced when the
Sāra-kernel/`buildAssessResponse` layer was merged on top of the older flat-bundle shape the
original audit evidence (`evidence/E2_q2_raw_assess_career.json`) was captured against; the
allow-list was never updated to track the two fields' actual key names.

**This means F-14's C2/C3 sub-claims ("never returns domain_completeness /
completeness_directive") are currently true for `assess_health` for TWO stacked reasons: (a)
the health-specific gap in §3.3/§3.1, AND (b) this universal §3.4 defect that would still
suppress those two fields even after (a) is fixed, and that also independently breaks
`assess_career`/`assess_wealth` today.** A remediation spec for F-14 that stops at "add
`'health'` to `DOMAIN_READING_FAMILIES`" will restore `reading` but NOT
`domain_completeness`/`completeness_directive` — those need the `buildAssessResponse`
key-mismatch fixed as well, and that fix has a wider blast radius than F-14/F-15/F-124 alone
(§6).

## 4. Sibling census

`grep -n "DOMAIN_READING_FAMILIES\|DOMAIN_READING_VARGAS\|DOMAIN_READING_HOUSES\|DOMAIN_READING_KARAKA" platform-mcp/src/tools/registry_bridge.ts`:

| Map | File:line | Keys present | Keys missing |
|---|---|---|---|
| `DOMAIN_READING_FAMILIES` | `registry_bridge.ts:1034` | `wealth`, `career` | `health`, `relationship` |
| `DOMAIN_READING_VARGAS` | `registry_bridge.ts:1040` | `wealth`, `career` | `health`, `relationship` |
| `DOMAIN_READING_HOUSES` | `registry_bridge.ts:1041` | `wealth`, `career` | `health`, `relationship` |
| `DOMAIN_READING_KARAKA_CODE` | `registry_bridge.ts:1042` | `wealth`, `career` | `health`, `relationship` |
| `DOMAIN_READING_KARAKA_LABEL` | `registry_bridge.ts:1043` | `wealth`, `career` | `health`, `relationship` |

There are exactly four `assess_*` tools registered in this file (`assess_marriage:2960`,
`assess_career:2999`, `assess_health:3042`, `assess_wealth:3081`) — no fifth domain exists to
worry about.

**Call-site census** (which handlers call `attachDomainCompleteness`/`attachDomainReading`):

| Tool | `attachDomainCompleteness` | `attachDomainReading` | `attachLeverageIndex` |
|---|---|---|---|
| `assess_career` (`:2999`) | YES (`:3030`) | YES (`:3032`) | no (by design) |
| `assess_wealth` (`:3081`) | YES (`:3112`) | YES (`:3114`) | YES (`:3117`, wealth-only) |
| `assess_marriage` (`:2960`) | **NO** | **NO** | no |
| `assess_health` (`:3042`) | **NO** | **NO** | no |

This is a clean, complete 2-of-4 pattern — confirms the finding's own suspected mechanism for
F-124 ("wired to assess_career only; sibling handlers still return the older bundle shape")
almost exactly, except it's 2-of-4 (career+wealth), not 1-of-4.

**Cross-file check** — is the underlying L-DOMAIN data capability itself missing
health/relationship support (i.e., is this a deeper data-layer gap)? No.
`platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts:184-188`'s
`DOMAIN_DIRECT_VARGAS` map — the analogous map one layer down, for the underlying
`assess_marriage`/`assess_health` capabilities themselves — already has all four keys:

```ts
export const DOMAIN_DIRECT_VARGAS: Record<string, string[]> = {
  wealth: ['D2', 'D11'],
  career: ['D10'],
  relationship: ['D9'],
  health: ['D6'],
}
```

So the L-DOMAIN capabilities (`marsys://tool/L-DOMAIN/assess_marriage`,
`.../assess_health`) already compute real domain-specific data for these two domains. The
gap is entirely confined to `registry_bridge.ts`'s MCP-server-side W7 reading-digest
composition layer (`DOMAIN_READING_FAMILIES` + the missing `attachDomain*` calls) — a wiring
gap in the presentation layer, not a missing computation.

## 5. Blast radius

- **The 27 CL-00 controls:** this affects the "domain reading substance-inline" contract
  (W7/SATYA-ŚEṢA), which is not itself one of the 27 CL-00 controls, but a fix here
  interacts directly with **S2's own CL-05/CL-06 budget work** (below) because
  `buildAssessResponse`/`assembleSaraContent` is the shared choke point for ALL FOUR
  assess_* tools' response shape.
- **F-15** (`assess_marriage`) — identical mechanism, same file, same three gates (§3.1-3.4).
  One spec closes both. See `../F-15/DIAGNOSIS.md`.
- **F-124** — same file, same mechanism; F-124 additionally asks "is this the same cause or
  a deeper wiring gap" — answer: **it is exactly this gap, described more completely than
  the finding's own suspected text.** See `../F-124/DIAGNOSIS.md`.
- **F-56 / F-111** (CL-05, this stream's own lane) — the code comment at
  `registry_bridge.ts:2881-2884` explicitly says `buildAssessResponse` was built to close
  F-56/F-111 ("Replaces the object-blind applyMcpBudgetAuto path"). That part is confirmed
  working (verdict_skeleton/activating_dasha correctly routed to `evidence`, not silently
  surviving the old array-only trimmer). Not reopened by this diagnosis.
- **F-112** (CL-06, "counts die structurally under composition") — also looks closed:
  `composition_report.counts` is computed BEFORE layer omission (§`assembleSaraContent`
  docstring, response_budget.ts:700-702) and verified honest live (`reading_families:0` for
  health even though `grounding` itself was entirely omitted at deep_dive). Not reopened.
- **NEW, not one of the three lanes assigned to this diagnosis, flagged for the conductor:**
  at `reading_depth:'deep_dive'`, `assembleSaraContent`'s greedy include-all-or-nothing
  algorithm (`response_budget.ts:781-800`) drops the ENTIRE `grounding` layer for ALL FOUR
  assess_* tools (including `assess_career`, which otherwise works) once
  `fetchOrientationContext`'s forced full-form B.11 pre-fetch (huge — 10k+ MSR signals,
  entity_profiles, convergence_domains) pushes `kernel+grounding` past the 40KB ceiling. This
  is NOT what F-14/F-15/F-124 describe (their claims and reproduce_cmds are about the
  domain-family gap), but it means the LITERAL reproduce_cmd (which specifies
  `reading_depth:'deep_dive'`) currently makes `assess_career` fail the same way
  `assess_health`/`assess_marriage` fail — a strictly worse symptom than any of the three
  findings describe. Recommend a new finding/spec, separately scoped, for
  `assembleSaraContent`'s all-or-nothing layer inclusion vs. the deep_dive-forced orientation
  payload size. Out of scope for this diagnosis's fix (adding health/relationship wiring)
  but the SPEC stage should not claim F-14/F-15/F-124 fully closed if this budget interaction
  is left unaddressed, since a caller using `reading_depth:'deep_dive'` — the literal
  reproduce_cmd — would still see no `reading` on ANY domain post-fix.
- **§N.8 Earned-Signal angle:** `composition_report.counts.reading_families` is a real,
  honest detector (confirms §N.8 discipline is respected here) — it correctly reports 0 for
  health/marriage today and would correctly report >0 once wired. Good precedent to preserve
  in the fix.
