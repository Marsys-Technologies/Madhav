---
lane: F-31
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE
author: S3 builder (sonnet), DIAGNOSIS-INCOMPLETE lane (2x budget)
---

# F-31 — assess_health omits reading/domain_completeness/completeness_directive with no judgment_flag disclosure

## 1. Live reproduction (today, 2026-08-16)

`assess_health(chart_id=482012f1-710e-4a25-994a-93821f5871aa, reading_depth='deep_dive')` and the
same call against Abhinandan (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`). Raw JSON saved to
`raw_repro.json` in this lane dir. Both calls returned byte-identical shape:

```json
{"kernel":{"verdict":"","flags":[],"promise":null,"pointers":[...]},
 "composition_report":{"budget_kb":40,"kernel_bytes":314,"included_layers":["kernel"],
   "counts":{"contradictions":0,"yoga_fact_ids":0,"reading_families":0},
   "omitted_sections":["grounding","evidence"]}}
```

**CONFIRMS REPRODUCES** — `kernel.flags` (the live `judgment_flags` surface) is an empty array on
both charts; there is no `reading`, `domain_completeness`, or `completeness_directive` field
anywhere in the response, and nothing in `kernel.flags` discloses their absence. Not ALREADY-FIXED.

**Important correction to the audit's framing, found only by reading the code:** the response shape
has changed substantially since the audit was written. `assess_health` no longer goes through the
old `applyMcpBudgetAuto` trimmer that emits `budget_exceeded_after_trim` — it was migrated to the
"sāra kernel" composition architecture (`ekv/a-09-sara-kernel`, merged to `origin/main` via PR #1301,
F-56/F-111) sometime after the audit ran. **The primary checkout at
`/Users/Dev/Vibe-Coding/Apps/Madhav` (branch `ekv/b-01-dignity-oracle-fix`) does NOT have this
architecture at all** — `registry_bridge.ts` on this checkout has no `composition_report`, no
`assembleSaraContent`, no `attachDomainCompleteness`. All code citations below are read from
`origin/main` (fetched fresh this session), which is what the live MCP server is actually running.
Every file:line in this diagnosis is an `origin/main` line number — a builder must open a fresh
worktree from `origin/main`, not from this checkout's HEAD, when this lane reaches Stage B.

The `budget_exceeded_after_trim` flag (`platform-mcp/src/lib/response_budget.ts:439`) is real and
still fires for tools still on the old `applyMcpBudgetAuto` path, but `assess_health` is not one of
them any more — so the audit's specific comparison point is stale. The underlying sub-claim
(disclosure mechanism exists and fires for other gaps, not this one) is still true, just via a
different, newer mechanism — see §3.

## 2. Claim decomposition

- **C1** — `assess_health` omits the `reading` / `domain_completeness` / `completeness_directive`
  fields that the F-14 finding says are "documented" for the health domain.
- **C2** — no `judgment_flag` (or, in the current architecture, no `kernel.flags` entry) discloses
  that omission.
- **C3** — the disclosure mechanism itself is not hypothetical — it is live code, exercised for a
  *different* gap in the *same tool family* (assess_career / assess_wealth), proving the omission
  for health is a wiring gap, not an architectural impossibility.

## 3. Mechanism (file:line, read directly from `origin/main`)

All in `platform-mcp/src/tools/registry_bridge.ts` unless noted.

**The disclosure function exists and works — but is never called for health.**
`attachDomainCompleteness` (defined :835-874) is the ONLY code path that sets
`response['domain_completeness']`, `response['completeness_directive']`, and pushes the
`complete_domain_accounting_attached` / `domain_accounting_incomplete` entry onto
`response['judgment_flags']` (:857-869). Its two and only call sites:

```
:3030   attachDomainCompleteness(response, 'career', chart_id)   // inside assess_career handler
:3112   attachDomainCompleteness(response, 'wealth', chart_id)   // inside assess_wealth handler
```

The `assess_health` handler (server.tool block starting :3041, async body :3053-3075) and the
`assess_marriage` handler (:2960-2992) never call it. Same pattern for `attachDomainReading`
(defined :1569, populates `response['reading']`): called only at :3032 (career) and :3114 (wealth),
never for health or marriage.

`DOMAIN_READING_FAMILIES` (:1034-1037) is hardcoded to two keys:
```ts
const DOMAIN_READING_FAMILIES: Record<string, readonly string[]> = {
  wealth: WEALTH_READING_FAMILIES,
  career: CAREER_READING_FAMILIES,
}
```
No `health` or `marriage` key exists. `buildDomainReading` (:1569) early-returns
`{ reading: [], families_served: 0, families_total: 0 }` (:1578) when `DOMAIN_READING_FAMILIES[domain]`
is undefined — so even if `attachDomainReading('health', ...)` were called, it would presently be a
silent no-op for the `reading` array specifically (the vargas/houses/karaka companion maps at
:1038-1041 are equally wealth/career-only).

`buildAssessResponse` (:2886-2951, the function that assembles the final `SaraLayeredContent` for
all four `assess_*` tools) pulls `kernel.flags` straight from whatever `response['judgment_flags']`
already contains at :2896 (`flags: (response['judgment_flags'] as JudgmentFlagEntry[]) ?? []`) — it
does not itself compute any completeness-gap flag. Confirms C2: the empty `flags: []` I observed
live is the direct, provable consequence of `attachDomainCompleteness` never having run for health.

**Second-order finding (goes one layer deeper than C1/C2 — relevant to Stage S):** even if
`assess_health` gained the two missing call sites, `attachDomainCompleteness` would likely still
no-op, because it depends on `assembleDomainCompleteness` → `runDossier({domain, chart_id, ...})`,
which reads precompiled slice bundles from
`platform-mcp/src/resources/vidhi/dossier_slices/`. Listing that directory on `origin/main` shows
only:
```
career_1c826d5a.json  career_482012f1.json  wealth_1c826d5a.json  wealth_482012f1.json
```
No `health_*` or `marriage_*` bundle exists. `assembleDomainCompleteness` returns `null` when
`runDossier` reports `!page.ok` (`gate_reason: 'slice_not_precomputed'`,
`platform-mcp/src/tools/dossier.ts:613-624`), and `attachDomainCompleteness` no-ops silently on a
`null` completeness (:837 `if (!completeness) return`) — itself a smaller instance of the exact same
defect class this finding is about (a silent absence with no disclosure), one level deeper in the
call chain. A wiring-only fix (add the two call sites) would not by itself produce a populated
`domain_completeness` for health/marriage; it needs a precompiled dossier slice for those domains
too, or `attachDomainCompleteness` needs its own `null`-case disclosure. Flagging both for Stage S.

## 4. Sibling census

Search scope: all four `assess_*` tool handlers in `registry_bridge.ts` (the file that owns this
mechanism), since that's where `DOMAIN_READING_FAMILIES` / `attachDomainCompleteness` /
`attachDomainReading` are wired per-tool.

| Tool | `attachDomainCompleteness` called? | `attachDomainReading` called? | `DOMAIN_READING_FAMILIES` entry? | Verdict |
|---|---|---|---|---|
| `assess_career` (:2999) | yes, :3030 | yes, :3032 | yes (`CAREER_READING_FAMILIES`) | fully wired — not affected |
| `assess_wealth` (:3081) | yes, :3112 | yes, :3114 | yes (`WEALTH_READING_FAMILIES`) | fully wired — not affected |
| `assess_health` (:3041) | **no** | **no** | **no** | **F-31, this finding** |
| `assess_marriage` (:2961) | **no** | **no** | **no** | **genuine sibling — same defect, not separately filed as far as this session found in the manifest excerpt given** |

`judgment_query` (`register_d9_judgment.ts`-equivalent block, :3600-3676) is a *different, already-
honest* case worth noting for contrast, not as a sibling defect: it calls
`buildDomainCompletenessPointer(domain, chart_id)` (:878, a compact variant of the same dossier join)
generically for whatever `domain` string the caller passes — including `'health'` — and DOES push a
`complete_domain_accounting_available` judgment_flag when a pointer resolves (:3664-3669). But
because no `health_*` dossier slice bundle exists (§3 second-order finding), `buildDomainCompletenessPointer`
returns `null` for domain='health' via the same `runDossier` gate, so `judgment_query` on health
today produces no flag either — not from a wiring gap, but from the shared missing-slice-bundle
root. This is the same second-order gap reappearing through a second call site, not a third distinct
finding — worth citing to SPEC as evidence the missing dossier slice is the deeper, shared blocker.

No other file was searched for this pattern — `DOMAIN_READING_FAMILIES` / `attachDomainCompleteness`
/ `attachDomainReading` are all defined and called exclusively within `registry_bridge.ts`.

## 5. Blast radius

- **File-lease conflict — this is the load-bearing finding of this diagnosis.** The entire
  mechanism (`DOMAIN_READING_FAMILIES`, `attachDomainCompleteness`, `attachDomainReading`,
  `buildAssessResponse`, all four `assess_*` handlers) lives in
  `platform-mcp/src/tools/registry_bridge.ts`, which plan §2 assigns to **S2 (MĀTRĀ) as a HOT,
  exclusive-single-builder file** ("`platform-mcp/src/lib/response_budget.ts`,
  `platform-mcp/src/tools/registry_bridge.ts`"), not to S3. Plan §2.1's lease-conflict table
  states this exact scenario directly: *"S3's CL-13 predicate flips live in the L4/L5 capability
  files (S3's lease); if a flip is needed inside the bridge, S3 posts a spec and S2's builder
  applies it."* **This lane cannot be built by S3 in `registry_bridge.ts` — Stage S must produce a
  spec and hand it to S2's builder, or the conductor must re-lease.** S3's own OWNS list
  (`L4_phala/**`, `L5_mimamsa/**`, `ph_nimitta/**`, `muhurta.py`) contains none of the files this
  fix touches.
- Also touches `platform-mcp/src/resources/vidhi/dossier_slices/` (a generated-data directory, not
  source) if the second-order dossier-slice gap is addressed in the same spec — that generation
  pipeline is not in any stream's OWNS list found in the plan; likely a separate governance/data-
  build concern (possibly S6 ĀDHĀRA territory, or a dedicated dossier-slice-generation job) rather
  than a code edit in any of the six streams' leased files. Flag to PRATINIDHI if Stage S wants to
  close the second-order gap rather than defer it.
- CL-00 controls: `platform/scripts/governance/` has no control asserting on `assess_health`'s
  `domain_completeness`/`judgment_flags` shape (checked `serialize_build_state.py`,
  `schema_validator.py`, `drift_detector.py`, `v13_production_gate.py` — none mention `dasha`,
  `assess_health`, or `domain_completeness`). Low risk of control regression from this fix.
- Other lanes sharing `registry_bridge.ts`: S2's CL-05/CL-06 lanes (F-13/F-28/F-56/F-111/F-12/F-36/
  F-37/F-45/F-44) all live in this same file — a build here must sequence behind/alongside S2's
  work on the file, not in parallel with an S3 builder editing it directly.
- The assess_marriage sibling (§4) should be raised to the conductor as a probable 7th CL-13
  beneficiary (mirroring F-34's own "possible seventh" note for its own class) — it is not currently
  named in the finding text handed to this lane, so it is reported here rather than assumed in
  scope.
