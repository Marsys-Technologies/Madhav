# F-46 — DIAGNOSIS

Stream: S2 MĀTRĀ · Class: CL-14 (with siblings F-14, F-15, F-124, F-125) ·
Files: `platform-mcp/src/lib/response_budget.ts` (S2 HOT) +
`platform-mcp/src/tools/register_p1_ganita.ts` / `register_p1_synthesis.ts` (see §5, lease note)
Stage: D (DIAGNOSE) · Chart: `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek Mohanty, canonical)

## 1. Live reproduction — REPRODUCES

`ganita_planet_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, planet='Saturn')`. Full
response captured; relevant excerpt (envelope header + tail):

```json
{
  "envelope_version": "v1",
  "tool": "ganita_planet_get",
  "verdict": null,
  "drill_pointers": [],
  "judgment_flags": [],
  "content": { "...": "position/dignity/shadbala/avasthas/aspects/yogas/dispositor" },
  "trim_report": [
    {"path": "dispositor.rows", "original_count": 224, "kept_count": 10, "reason": "dispositor.rows: trimmed to 10", "recover_via": {"instrument": "ganita_planet_get", "hint": "call ganita_planet_get again with a narrower filter/date_range, or a smaller top_k/limit, to reach the rest of \"dispositor.rows\""}},
    {"path": "shadbala.rows", "original_count": 137, "kept_count": 10, "reason": "shadbala.rows: trimmed to 10", "recover_via": {"instrument": "ganita_planet_get", "hint": "..."}},
    {"path": "yogas.firings_authoritative", "original_count": 20, "kept_count": 10, "reason": "yogas.firings_authoritative: trimmed to 10", "recover_via": {"instrument": "ganita_planet_get", "hint": "..."}},
    {"path": "dignity.rows", "original_count": 54, "kept_count": 10, "reason": "dignity.rows: trimmed to 10", "recover_via": {"instrument": "ganita_planet_get", "hint": "..."}},
    {"path": "position.rows", "original_count": 45, "kept_count": 10, "reason": "position.rows: trimmed to 10", "recover_via": {"instrument": "ganita_planet_get", "hint": "..."}},
    {"path": "avasthas.rows", "original_count": 30, "kept_count": 10, "reason": "avasthas.rows: trimmed to 10", "recover_via": {"instrument": "ganita_planet_get", "hint": "..."}}
  ]
}
```

Confirmed exactly as claimed: 6 real, per-section trim_report entries (genuine trimming
happened — 224→10, 137→10, 20→10, 54→10, 45→10, 30→10) yet:
- **No `budget_kb_applied` field anywhere in the response** (grepped the full captured JSON —
  absent).
- **No `budget_kb_requested` field** (absent — though this tool's schema doesn't even expose a
  `budget_kb` input parameter to request against, a separate, smaller gap noted in §5).
- **Top-level `drill_pointers` is `[]`** — empty, despite 6 real `recover_via` pointers sitting
  in `trim_report` two levels down that were never merged up.

For contrast, the corpus's suspected siblings were live-probed too:
- `kala_projections_get(chart_id=..., )` (no other args) — trimmed `content.projections`
  50→25, and its response DOES carry `"budget_kb_applied": 40` and a populated top-level
  `"drill_pointers": [{"instrument": "kala_projections_get", "hint": "..."}]`. **This tool does
  NOT reproduce F-46's defect** — see §4, it is wired through the strong mechanism, not the weak
  one the corpus suspected.
- `ganita_condition_get` — live call attempted with `facet: 'graha_yuddha'`, which is not a
  valid enum value for this tool (`dignity`/`avasthas`/`karakas` only); did not get a live
  payload in this session, but the defect is confirmed by file inspection (§3) — it is wired
  through the same `dualOutput` → `applyAutoBudgetToEnvelope` path as `ganita_planet_get`.
- `kala_life_arc_get(chart_id=...)` — live call returned a response small enough that no
  trimming fired (no `trim_report` in the response), so this call did not exercise the defect
  live, but the file-level wiring (§3, §4) is confirmed identical to `ganita_planet_get`'s.

## 2. Claim decomposition

- **F-46a (no `budget_kb_applied`/`budget_kb_requested` echo):** a response that genuinely
  trimmed data under `applyAutoBudgetToEnvelope` never discloses the ceiling that was applied,
  nor (for tools that expose a `budget_kb` param) what the caller asked for.
- **F-46b (recover_via not merged into top-level `drill_pointers`):** each trim's per-section
  `recover_via` pointer is buried inside `trim_report[].recover_via` and never surfaced into the
  envelope's own `drill_pointers` array, where the stronger mechanism puts it.
- **F-46c (scope claim — "and per the file's own doc-comment, likely … others sharing the same
  wiring"):** an implicit third claim that the defect class extends beyond `ganita_planet_get` to
  a named list of siblings. This is addressed in §4 — **partially confirmed, partially
  refuted** (two of the four named suspects are false positives).

## 3. Mechanism → file:line — TWO DIFFERENT FUNCTIONS, confirmed as genuinely separate

**F-46's mechanism is NOT the same code path as F-44's.** F-44 lives inside
`finalizeMcpBudget`/`applyResponseBudget`'s own internal fallback logic (`response_budget.ts:287-293`,
`:402-410`). F-46 lives in a THIRD, weaker function, `applyAutoBudgetToEnvelope`
(`response_budget.ts:584-598`), which never calls `finalizeMcpBudget` at all:

```ts
// response_budget.ts:584-598
export function applyAutoBudgetToEnvelope(
  envelopeObj: Record<string, unknown>,
  toolName: string,
  maxKb = 40,
): void {
  const content = envelopeObj['content']
  if (!content || typeof content !== 'object' || Array.isArray(content)) return
  const sections = autoDetectTrimmableSections(content as Record<string, unknown>, toolName)
  if (sections.length === 0) return
  const result = applyResponseBudget(content as Record<string, unknown>, maxKb, sections)
  if (result.trim_report) {
    const existing = Array.isArray(envelopeObj['trim_report']) ? (envelopeObj['trim_report'] as TrimReportEntry[]) : []
    envelopeObj['trim_report'] = [...existing, ...result.trim_report]
  }
}
```

This calls `applyResponseBudget` DIRECTLY (bare, not wrapped in `finalizeMcpBudget`) and, after
trimming, does exactly one thing: append `result.trim_report` onto `envelopeObj['trim_report']`.
It never touches `budget_kb_applied`, `budget_kb_requested`, or `drill_pointers` — those three
behaviors live ONLY inside `finalizeMcpBudget` (`response_budget.ts:361-444`), specifically:
- `budget_kb_applied`/`budget_kb_requested` set at `:380-381`:
  ```ts
  mutable['budget_kb_applied'] = opts.maxKb
  if (opts.budgetKbRequested !== undefined) mutable['budget_kb_requested'] = opts.budgetKbRequested
  ```
- `drill_pointers` merge at `:384` (via `mergeTrimPointersIntoPointers`, defined `:816-830`):
  ```ts
  mutable[drillPointersField] = mergeTrimPointersIntoPointers(existingPointers, result.trim_report)
  ```

`applyAutoBudgetToEnvelope` was built (per its own doc-comment, `:571-583`) as a lighter-weight
mechanism for "thin PROXY" tools whose response shape this lane doesn't hand-declare
`TrimmableSection`s for — it reuses `autoDetectTrimmableSections` (the array-discovery helper)
but was wired to the WEAKER of the two entry points (`applyResponseBudget`) rather than the
self-verifying, echo-producing one (`finalizeMcpBudget`). This looks like an oversight at the
call-site-selection level, not a bug inside either function individually — both functions do
exactly what they're individually documented to do; the wiring choice made in
`register_p1_ganita.ts`/`register_p1_synthesis.ts` picked the wrong one of the two for tools that
turn out to trim real data routinely.

**Caller-side wiring, `register_p1_ganita.ts:155-170`** (`dualOutput`, exact function; finding
cited `155-168`, off by ~2 lines from a since-drifted file — content matches):
```ts
function dualOutput(data: unknown) {
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    const toolName = typeof obj['tool'] === 'string' ? (obj['tool'] as string) : 'unknown_tool'
    applyAutoBudgetToEnvelope(obj, toolName)
  }
  const structuredContent = { type: 'object' as const, object: data }
  const json = JSON.stringify(data)
  ...
}
```
`ganita_planet_get`'s handler returns `dualOutput(envelope(data, 'ganita_planet_get'))`
(`register_p1_ganita.ts:1303`) — this `dualOutput` is what every tool registered in this file
routes through.

**Byte-identical sibling function, `register_p1_synthesis.ts:170-184`**, same
`applyAutoBudgetToEnvelope(obj, toolName)` call at line 177, its own doc-comment explicitly
naming `kala_life_arc_get` as a beneficiary ("covers `kala_life_arc_get` and the rest of this
file's tools").

### Answer to the plan's explicit question: ONE spec or TWO?

**Two specs, but with a shared root cause.** F-44 and F-46 are mechanically independent defects
in independent functions (`finalizeMcpBudget`'s/`applyResponseBudget`'s internal fallback
strings vs. `applyAutoBudgetToEnvelope`'s missing echo/merge step) that happen to live in the
same file and share a family resemblance (both are "the budget-trim honesty mechanism isn't
fully honest under some condition"). They can be fixed independently and in either order without
either fix depending on the other:
- F-44's fix is entirely inside `finalizeMcpBudget`/`applyResponseBudget` (lines 287-293,
  402-410) plus a caller-side resync in `kala_story_get` — touches neither
  `applyAutoBudgetToEnvelope` nor its two call sites.
- F-46's fix is either (a) inside `applyAutoBudgetToEnvelope` itself — make it also set
  `budget_kb_applied`/merge `drill_pointers`, i.e. give it the same self-verifying behavior
  `finalizeMcpBudget` has (the cleanest fix — one function, all its callers inherit it for
  free), or (b) at the two call sites — replace `applyAutoBudgetToEnvelope` with
  `finalizeMcpBudget` (which already does everything (a) would add, since
  `finalizeMcpBudget` itself calls `applyResponseBudget` under the hood — see
  `response_budget.ts:370`). Route (b) is likely the SPEC-preferred fix since it deletes a
  redundant weaker code path instead of duplicating `finalizeMcpBudget`'s logic inside
  `applyAutoBudgetToEnvelope`, but that's a SPEC-stage decision, not a DIAGNOSE-stage one.

Neither fix requires touching the other's lines. **A shared SPEC section noting the common
root ("this file has two independently-broken honesty mechanisms; here is why they're separate
functions and separate fixes") is reasonable, but the exit tests, sibling coverage, and file
diffs must be tracked as two distinct SPEC deliverables** — collapsing them into one spec risks
a reviewer approving F-46's fix and missing that F-44's chapter_count/recover_via defects were
never touched, or vice versa.

## 4. Sibling census — `applyAutoBudgetToEnvelope` call sites (F-46's exact weak-path defect class)

Grep, `platform-mcp/src` (read-only main-tip checkout), excluding `*.test.ts`:

```
platform-mcp/src/tools/register_p1_ganita.ts:43:   import { applyAutoBudgetToEnvelope } ...
platform-mcp/src/tools/register_p1_ganita.ts:162:  applyAutoBudgetToEnvelope(obj, toolName)
platform-mcp/src/tools/register_p1_synthesis.ts:17:  import { applyAutoBudgetToEnvelope } ...
platform-mcp/src/tools/register_p1_synthesis.ts:177: applyAutoBudgetToEnvelope(obj, toolName)
platform-mcp/src/lib/response_budget.ts:584:         export function applyAutoBudgetToEnvelope(...)
```

**Exactly 2 real call sites, both `dualOutput` helpers.** Every MCP tool registered through
either file's `dualOutput` inherits the defect. Enumerated by grepping each file's
`server.tool('<name>', ...)` registrations and confirming each one's handler returns
`dualOutput(envelope(...))`:

**`register_p1_ganita.ts`'s `dualOutput` — 13 tools:**
`ganita_strength_get`, `ganita_structural_get`, `ganita_condition_get`, `ganita_kp_cusps_get`,
`ganita_sade_sati_get`, `ganita_tajaka_get`, `ganita_nakshatra_get`, `ganita_yogas_get`,
`phala_rectification_get`, `ganita_transit_anchors_get`, `ganita_database_schema_get`,
`ganita_concept_locate`, `ganita_planet_get` (confirmed live above).

**`register_p1_synthesis.ts`'s `dualOutput` — 6 tools:**
`mimamsa_insight_get`, `bodha_discoveries_get`, `kala_life_arc_get`, `synth_tail_divergence_get`,
`synth_chart_brief_get`, `prashna_undertaking_get`.

**19 tools total** share the exact mechanism (`dualOutput` → `applyAutoBudgetToEnvelope`), though
in practice the defect is only OBSERVABLE on a given call when `autoDetectTrimmableSections`
finds an array >10 items AND that array actually needs trimming to fit the (default 40KB)
ceiling — not every call to every one of the 19 will show it, but every one of them is
structurally exposed to it the moment its payload is large enough (confirmed live for
`ganita_planet_get`; confirmed by identical wiring, not yet triggered live, for the other 18).

### Corpus-named suspects — confirmed / refuted individually

The task brief named 4 specific suspects (`ganita_condition_get`, `kala_life_arc_get`,
`kala_projections_get`, `mimamsa_lel_query`) plus "and others sharing the same wiring."

| Suspect | Verdict | Evidence |
|---|---|---|
| `ganita_condition_get` | **CONFIRMED** | `register_p1_ganita.ts:742` registration, `:769` `dualOutput(envelope(...))` — same file, same `dualOutput`, same `applyAutoBudgetToEnvelope` call as `ganita_planet_get`. |
| `kala_life_arc_get` | **CONFIRMED** | `register_p1_synthesis.ts:664` registration, `:696` `dualOutput(envelope(...))` — this file's `dualOutput` (`:170-184`) doc-comment (`:172-173`) explicitly names `kala_life_arc_get` as a beneficiary of the (weak) mechanism. |
| `kala_projections_get` | **REFUTED** | Registered in `register_p1_aliases.ts:943` (a THIRD file, not `register_p1_ganita.ts`/`register_p1_synthesis.ts`). That file's own `dualOutput` (`register_p1_aliases.ts:183-...`) calls `finalizeMcpBudget` directly (imports it at line 29), NOT `applyAutoBudgetToEnvelope` — confirmed by grep (`applyAutoBudgetToEnvelope` does not appear in `register_p1_aliases.ts` at all) and live reproduction: the live call showed `"budget_kb_applied": 40` and a correctly-merged top-level `drill_pointers` entry pointing at `kala_projections_get`. **This tool already uses the STRONG mechanism and does not share F-46's defect.** |
| `mimamsa_lel_query` | **REFUTED (same reasoning)** | Registered in `register_p1_aliases.ts:1808`, routes through the same strong `dualOutput`/`finalizeMcpBudget` wiring as `kala_projections_get`. Not confirmed live in this session (no live call made), but the file-level wiring is identical to the confirmed-refuted `kala_projections_get` case — same file, same `dualOutput` definition, same import. |

**Net correction to the corpus:** 2 of the 4 named suspects are real siblings; 2 are false
positives that already use the strong mechanism. The corpus's "likely" hedge was warranted —
the doc-comment that named the suspects (`response_budget.ts:576-578`, describing
`autoDetectTrimmableSections`'s consumers as "every `dualOutput()` in `register_p1_ganita.ts` /
`register_p1_synthesis.ts` / `register_p1_aliases.ts`") is itself slightly imprecise: all three
files DO use `autoDetectTrimmableSections`, but only two of the three (`register_p1_ganita.ts`,
`register_p1_synthesis.ts`) pair it with the weak `applyAutoBudgetToEnvelope`; the third
(`register_p1_aliases.ts`) pairs the same array-discovery helper with the strong
`finalizeMcpBudget`. **The defect class is `applyAutoBudgetToEnvelope`'s callers specifically,
not "everything using `autoDetectTrimmableSections`."**

### A smaller, related, but distinct gap noted for the record (not part of F-46's stated claim)

`budgetMcpContent` (`response_budget.ts:611-617`) — used by ~30 additional tools across
`l0_ephemeris.ts`, `l0_brahmagyan.ts`, `chart_selection.ts`, `reading_notes.ts`,
`read_classical_text.ts`, `session_tools.ts`, `muhurta_finder.ts`, `register_p2_dasha_lord.ts`,
`register_p1_reference.ts`, `phala_mitigation_map.ts`, `bo_2-8.ts`, `mimamsa_lel_intake.ts`,
`register_vidhi_plan.ts`, `retrieval/remedy_tools.ts`, `retrieval/kala_temporal.ts`,
`scan_fetch_signals.ts`, `mimamsa_outcome.ts` — DOES call `finalizeMcpBudget` internally
(`:616`), so it DOES get `budget_kb_applied` and merged `drill_pointers`. But it never passes
`budgetKbRequested` in its own call (`finalizeMcpBudget(obj, { maxKb, sections })` — no
`budgetKbRequested` key), so `budget_kb_requested` never appears on any of these ~30 tools'
trimmed responses even when the underlying tool does accept a `budget_kb` input param. This is
NOT the defect F-46 describes (F-46 is about the wrong function being called entirely;
`budgetMcpContent`'s callers use the RIGHT function, just don't thread one optional field
through) — flagging it here only so the SPEC stage doesn't conflate the two, and so it isn't
lost: it's a legitimate, narrower, sibling-of-a-different-shape worth a one-line mention in the
SPEC's "considered but out of scope" note, or its own separate finding.

## 5. Blast radius

- **§N.6/§N.7/§N.8 controls touched:** §N.6 (Serving Density) — `drill_pointers` failing to
  surface a trim's real recovery instrument is exactly the "density signaling is data, not
  narration" violation (§N.6 item 4): the caller has no machine-readable way to know more data
  exists beyond re-reading `trim_report` by hand. §N.7 item 4 (verification flag needs a real
  detector) is adjacent but not directly on point — `budget_kb_applied`'s ABSENCE isn't a false
  positive flag, it's a missing honest-disclosure field; closer fit is §N.6 item 2/4 generally.
- **CL-00 controls:** not directly assessed against the 27 CL-00 control list in this DIAGNOSE
  pass (out of scope here); SPEC stage should check `parisesa_gate.py`'s CL-00 cheap subset
  before build, per §3's plan contract.
- **Lease risk — REAL, not enumerated in the plan's §2.1 table:** §2 assigns
  `platform-mcp/src/lib/response_budget.ts` to S2 (HOT, exclusive) but ALSO assigns "the
  `dualOutput`/pointer helpers" and "tool registration files" to **S1** (DVĀRA). F-46's fix
  necessarily touches BOTH: the shared mechanism in `response_budget.ts` (S2) AND the two
  `dualOutput` call sites in `register_p1_ganita.ts`/`register_p1_synthesis.ts` (arguably S1's
  "tool registration files" + "dualOutput helpers" domain). §2.1's four-row lease-conflict table
  does not list either of these two files. **This should be flagged to the conductor before
  BUILD** — either S2 gets an explicit one-time lease extension into these two files for this
  one finding (cleanest, since the change is a one-line swap of which budget function
  `dualOutput` calls, not a `dualOutput`-redesign), or S2 posts a spec and hands the two-line
  call-site edit to S1 per the plan's own stated rule ("a lane that discovers its mechanism
  lives in another stream's file does not edit it — it posts `PAR-F-46-NEEDS-LEASE <path>`").
  `register_p1_synthesis.ts` carries an ADDITIONAL known conflict already documented in §2.1
  (S5 holds it first for CL-03 predicate fixes, then hands to S4) — a third stream now has a
  plausible claim on this file. Recommend: conductor resolves as an ordered same-file handoff,
  not a parallel edit, regardless of which stream ends up building it.
- **Other lanes sharing `response_budget.ts`:** same S2 file-sharing note as F-44's own
  diagnosis — F-44, F-13, F-28, F-56, F-111, F-112, F-122, F-12, F-36, F-37, F-45, F-14, F-15,
  F-124, F-125 are all S2 findings that may touch this file; sequence within S2, don't
  parallelize edits to `response_budget.ts`.
- **A-09 sāra-kernel:** same finding as F-44's diagnosis — `response_budget.ts` on
  `ekv/a-09-sara-kernel` is byte-identical to `origin/main`'s copy; the `SaraKernel`/
  `assembleSaraContent` region (`:641-830`) is unrelated to `applyAutoBudgetToEnvelope`
  (`:584-598`) or `finalizeMcpBudget` (`:361-444`) and is not touched by any plausible fix to
  this finding.
- **S6's F-141:** no file overlap, same doctrinal family only (§N.8), as noted in F-44's
  diagnosis.

## Evidence

Live JSON captured in this session's tool-call transcript for:
`ganita_planet_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, planet='Saturn')` (defect
confirmed), `kala_projections_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa)` (defect
refuted — strong mechanism), `kala_life_arc_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa)`
(no trim fired, wiring confirmed by file inspection instead), `ganita_condition_get` (invalid
`facet` argument on this session's attempt — schema requires `dignity`/`avasthas`/`karakas`;
defect confirmed by file inspection, not live payload).
