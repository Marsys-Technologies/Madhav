---
finding: F-125
stream: S2 MĀTRĀ
class: CL-14 (family-parity / cross-tool contract honesty)
severity: TIER3-EXPERIENCE
stage: D COMPLETE
disposition: OPEN — mechanism traced to file:line; cannot proceed to Stage S/B under S2's own
  lease (see §5 lease verdict below).
lease_conflict: >
  PAR-F125-NEEDS-LEASE platform-mcp/src/tools/kala_views/upaya.ts (S4 VĀCA, explicit per plan
  §2.1 kala_views split table) AND PAR-F125-NEEDS-LEASE platform-mcp/src/tools/register_p1_aliases.ts
  (S5 MŪLA's primary lease per plan §2.1 lease-conflict row 4, ordered-handoff-to-S1 only for the
  unrelated dualOutput/toolName CL-11 sweep). Neither file is on S2's OWNS list
  (response_budget.ts, registry_bridge.ts, kala_views/{elect,story,ritual,priority,shared}.ts).
  S2 diagnoses+specs this finding; build must be routed to S4 (upaya.ts hunk) and S5
  (register_p1_aliases.ts hunk), or the conductor re-leases both files to S2 for the duration of
  this one lane. See §5 for the fuller reasoning, including the one piece of this fix that IS
  legitimately S2's (extracting the shared gate out of registry_bridge.ts, which S2 already owns).
---

## 1. Live reproduction

Ran the finding's `reproduce_cmd` (domain substituted `career` for `relationship` — immaterial to
the envelope-shape question under test) plus the assess_* contrast call, against canonical chart
`482012f1-710e-4a25-994a-93821f5871aa`.

**`kala_upaya_get`** — top-level keys of the live response:
```
['reading', 'question_frame', 'field_snapshot_id', 'field_snapshot_state', 'field_snapshot_reason',
 'tri_plane', 'coverage', 'freshness', 'calibration_maturity', 'tool', 'chart_id', 'event_class',
 'diagnosis', 'interventions', 'intervention_count', 'uncited_remedy_rows',
 'uncited_remedy_row_count', 'uncited_remedy_note', 'alternate_routes', 'eligibility_pointer',
 'efficacy_report', 'filing_state', 'adoption_basis', 'filed_prediction_id', 'filing_ready_payload',
 'filing_detail', 'intervention_ledger', 'disclosure', 'composed_text']
```
`grep -c "orientation"` over the full 100,952-char raw response (saved to a scratch file this
session) = **0**. No `orientation_context`, no `orientation_ok`, no `b11_note` — confirmed absent,
not merely renamed.

**`bodha_remedies_get`** — full response is `{content: {...}, is_error: false}`; the `content`
object's keys are `chart_id, ayanamsha_id, narration, resonances, resonance_count, prescriptions,
prescription_count, filters, drill_pointers, provenance`. No `orientation_context`/`orientation_ok`
anywhere in the envelope — confirmed absent.

**`assess_career`** (contrast) — top-level `object` carries `kernel`, `composition_report`,
`grounding`, `evidence`. `grounding.orientation_context` is a full L2 UCD digest object (msr
signal_count 10003, entity_profiles, convergence_domains, etc.), and `grounding.orientation_ok:
true` sits alongside it. Confirmed present and `true`.

**Verdict: reproduces exactly as claimed.** Both sub-claims (kala_upaya_get absent, bodha_remedies_get
absent, assess_career present-and-true) are live-confirmed, not just corpus-inherited.

## 2. Claim decomposition

The manifest's F-125 claim (`git show audit/paripurna2-evidence:pp2-audit/manifest.json`, id F-125)
breaks into these distinct sub-assertions:

1. **A1** — `assess_marriage`/`assess_career`/`assess_health` all carry `orientation_ok:true`. →
   CONFIRMED for `assess_career` live (§1); source-confirmed for the other two (§3, same
   `fetchOrientationContext` call site pattern at lines 2980/3062).
2. **A2** — `kala_upaya_get` carries NO `orientation_context` and NO `orientation_ok` field at all,
   despite serving "the single most interpretively-loaded output" (a PACT promise-denial verdict). →
   CONFIRMED live (§1) and CONFIRMED at the mechanism level (§3b — zero orientation code in the file).
3. **A3** — `bodha_remedies_get` likewise returns none. → CONFIRMED live (§1) and CONFIRMED at the
   mechanism level (§3b).
4. **A4** — this is squarely interpretive work, not a `depth:'retrieval'` lookup exempt under the
   RS-4 carve-out (CLAUDE.md §I B.11). → Not independently re-litigated this pass; accepted as given
   — a remedy prescription and a PACT-chain verdict are definitionally interpretive synthesis, not
   pinpointed factual lookups, and neither tool's own description frames itself as `retrieval`-tier.
5. **A5 (the mechanism claim)** — "the B.11 orientation pre-fetch is implemented per-handler on the
   assess_* family rather than as a cross-cutting gate on interpretive capabilities" and "nothing...
   required, performed, or flagged the missing Whole-Chart-Read routing." → CONFIRMED, and sharpened
   in §3: it's not merely "per-handler" in the sense of duplicated code — the single shared function
   that does exist (`fetchOrientationContext`) is **module-private to `registry_bridge.ts`, not
   exported**, so no file outside that one module could call it even if a developer remembered to.
   The gap is structural, not a forgotten call.

A fix that only wires orientation into `kala_upaya_get` closes A2 but leaves A3 (and the much larger
sibling set in §4) open — this is exactly the "classic partial remediation" the plan's Stage D
contract warns about.

## 3. Mechanism → file:line

### 3a. Where B.11 orientation IS implemented (the assess_* / registry_bridge.ts side)

`platform-mcp/src/tools/registry_bridge.ts`:
- `fetchOrientationContext` — defined at **line 2061**, `async function fetchOrientationContext(chart_id,
  ayanamsha_id, principal, verbosity?): Promise<{orientation_context, orientation_ok}>` — **not
  exported** (no `export` keyword; contrast `resolveOrientationFetchParams` at 1964 and
  `assessOrientationPayload` at 2004, which ARE exported but only compute pure logic — they don't
  perform the actual `callRegistryCapability('marsys://tool/L2/query_ucd', ...)` fetch).
- It is called at 15 sites, all inside this one file, each individually written into the relevant
  tool's handler body: line 2307 (`get_domain_reading`), 2415 (`get_signals`), 2546
  (`traverse_graph`), 2665 (`get_temporal_windows`), 2699 (`get_projections`), 2772 (`get_remedies`
  — the *legacy* name, contrast §3b), 2799 (`get_chart_quality`), 2980 (`assess_marriage`), 3019
  (`assess_career`), 3062 (`assess_health`), 3101 (`assess_wealth`), 3206 (`get_cgm_subgraph`), 3469
  (`judgment_query`), 4109 (`graha_portrait`), 4574 (`pact_query`).
- The doc comment directly above the registration block (line ~2108) states the design intent
  plainly: *"B.11 enforcement: all per_chart domain tools call fetchOrientationContext() before
  executing their domain query."* This is true only for tools registered inside
  `registerRegistryBridgeTools` in this one file — it does not hold for tools registered anywhere
  else in the codebase, and nothing enforces that boundary.

### 3b. Where it is ABSENT — the two named tools

**`kala_upaya_get`** — `platform-mcp/src/tools/kala_views/upaya.ts`:
```ts
// lines 494-528
export function registerKalaUpayaGet(server: McpServer, principal: Principal): void {
  server.tool(
    'kala_upaya_get',
    KALA_UPAYA_DESCRIPTION,
    KalaUpayaInputShape,
    async ({ chart_id, domain, bhava, event_class, as_of_date, adopt_intervention, question_frame }) => {
      if (!chart_id) { /* ...error... */ }
      const response = await buildKalaUpayaResult(
        { chart_id, domain: domain ?? null, bhava: bhava ?? null, event_class: event_class ?? null,
          as_of_date: as_of_date ?? null, adopt_intervention: adopt_intervention ?? null,
          question_frame: question_frame ?? null },
        principal,
      )
      return { content: [{ type: 'text' as const, text: JSON.stringify(response, null, 2) }] }
    },
  )
}
```
`grep -c "orientation" platform-mcp/src/tools/kala_views/upaya.ts platform-mcp/src/lib/kala_upaya_diagnosis.ts`
= **0/0**. Neither the registration nor `buildKalaUpayaResult`'s implementation (in
`kala_upaya_diagnosis.ts`, which composes `reading`/`diagnosis`/`interventions`/`disclosure`) ever
touches orientation. Registered from `registry_bridge.ts:4729` (`registerAllKalaViews(server,
principal)`) → `kala_views/register_all.ts:58` (`registerKalaUpayaGet(server, principal)`) — i.e. it
IS reached from `registry_bridge.ts`'s registration pass, but the handler body itself lives entirely
in `upaya.ts` and never calls (or imports) `fetchOrientationContext`.

**`bodha_remedies_get`** — `platform-mcp/src/tools/register_p1_aliases.ts:1015-1025`:
```ts
regAlias(server, 'bodha_remedies_get',
  'L2 remedy recommendations via Bodha (PRIMARY Phase-1 name for get_remedies)',
  'marsys://tool/L2/query_remedies',
  { domain: z.string().optional(), graha: z.string().optional(), planet: z.string().optional(),
    tradition: z.string().optional(), fields: z.enum(['compact', 'all']).optional() },
  principal, { paramAliases: { planet: 'graha' } })
```
`regAlias` itself (defined `register_p1_aliases.ts:351-384`) is a generic thin wrapper: it strips
`chart_id`/`ayanamsha_id`/`limit`/`offset`, calls `callRegistryCapability(uri, {...}, principal)`
directly, and returns `dualOutput(data, name)` — **no orientation fetch anywhere in the helper**.
This is the sharper finding than the raw claim states: `bodha_remedies_get` targets the **exact same
capability URI** (`marsys://tool/L2/query_remedies`) as `registry_bridge.ts`'s own `get_remedies`
tool (line 2760, which DOES call `fetchOrientationContext` at line 2772) — but because
`bodha_remedies_get` is a *second, independent* MCP tool registration built through `regAlias`
instead of delegating to `get_remedies`'s handler, it silently drops the orientation wrapper that
its sibling name applies to the identical underlying query. Same data, same URI, two tool names,
only one has the B.11 floor.

### 3c. Lease location (for §5)

- `kala_upaya_get`'s handler is 100% inside `platform-mcp/src/tools/kala_views/upaya.ts` — per plan
  §2.1's explicit kala_views split table, this file is **S4 VĀCA's** lease, not S2's (S2 owns
  `elect.ts, story.ts, ritual.ts, priority.ts, shared.ts`; S4 owns `now.ts, explain.ts, ahead.ts,
  upaya.ts`).
- `bodha_remedies_get`'s handler is 100% inside `platform-mcp/src/tools/register_p1_aliases.ts` —
  per plan §2.1's lease-conflict table row 4, this file is **S5 MŪLA's** primary lease (its CL-03
  param-plumbing findings); the only carve-out is S1 going first for the ~19 `dualOutput` toolName
  sites (CL-11), unrelated to this finding.
- The one shared piece that IS inside S2's own lease: `fetchOrientationContext` and its two exported
  helpers live in `registry_bridge.ts`, which S2 owns outright. Extracting/exporting that function
  (or a thin wrapper) is legitimately S2's to build; wiring the resulting import into the two
  handlers above is not.

## 4. Sibling census

Grepped every `server.tool(` registration file under `platform-mcp/src/tools/**` (38 files,
excluding tests) for the string `orientation`. Files with zero hits, i.e. registering at least one
chart-scoped, verdict/prescription-bearing tool with no B.11 orientation call of any kind:

| File | Tool(s) registered | Interpretive weight |
|---|---|---|
| `kala_views/ahead.ts` | `kala_ahead_get` | high — dasha/transit activation forecast narrative |
| `kala_views/dasha_sandhi.ts` | `kala_dasha_sandhi_get` | high — junction-period risk verdict |
| `kala_views/elect.ts` | `kala_elect_get` | high — muhurta/election timing verdict |
| `kala_views/explain.ts` | `kala_explain_get` | high — causal-chain explanation verdict |
| `kala_views/now.ts` | `kala_now_get` | high — "what's active right now" synthesis |
| `kala_views/priority.ts` | `kala_priority_get`, `kala_priority_ranking_get` | high — ranked-attention verdict |
| `kala_views/ritual.ts` | `kala_ritual_get` | high — yajña/vrata prescription |
| `kala_views/story.ts` | `kala_story_get` | high — life-arc narrative (has 1 `orientation` hit, but it is only a `drill_pointers` **pointer string** to `get_chart_orientation`, `line 748` — it never fetches or reports orientation itself, so it fails the same way as the two named tools) |
| `kala_views/upaya.ts` | `kala_upaya_get` | **named in this finding** |
| `phala_mitigation_map.ts` | `mitigation_map` (served as `phala_mitigation_get`) | high — mitigation-lever verdict |
| `phala_outlook.ts` | (TOOL_NAME) `phala_outlook_get` | high — predictive outlook verdict |
| `phala_event_anchors.ts` | (TOOL_NAME) `phala_anchors_get`/`phala_predictive_anchors_get` | high — predictive-anchor verdict |
| `mechanism_retrodiction.ts` | `mechanism_retrodiction_get` | high — retrodictive-mechanism verdict |
| `register_p1_aliases.ts` | multiple `regAlias(...)`-registered tools (generic mechanism — see below) | mixed |

**`register_p1_aliases.ts` deserves its own line item**, because it is the same generic-helper
defect as `bodha_remedies_get`, applied uniformly: `regAlias`/`globalAlias` never call orientation,
so EVERY tool registered through them lacks it — including, most notably, **`bodha_domain_reading_get`**
(line 503), which targets the identical URI (`marsys://tool/L2/query_domain_reading`) as
`registry_bridge.ts`'s `get_domain_reading` (line 2274, which DOES carry orientation via the 2307
call site). Per this file's own naming convention comments, the `bodha_*_get` names are documented
as the **"PRIMARY Phase-1 name"** — i.e. the name callers are steered toward — while the orientation-
bearing name is the "legacy" one. This is the same shape of defect as F-125's own `bodha_remedies_get`
finding, on the domain-reading capability instead of the remedies one, and arguably higher-impact
since domain reading is the more central Bodha capability. Full `regAlias(server, ...)` roster in
this file (16 total registrations): `bodha_domain_reading_get`, `ganita_medical_get`,
`ganita_vastu_get`, `ganita_ayurdaya_get`, `ganita_sensitive_degrees_get`, `ganita_vichara_get`,
`ganita_yoga_firings_get`, `ganita_av_transit_gating_get`, `kala_priority_ranking_get`,
`ganita_dashas_get`, `bodha_remedies_get`, `bodha_remedies_search`, `bodha_quality_get`,
`standing_predictions_read`, `ganita_dasha_periods_get`, `query_dasha_periods` — not all of these
are equally "interpretive" (several are L0/L1 factual reference lookups plausibly RS-4-exempt), but
`bodha_domain_reading_get`, `bodha_remedies_search`, and `bodha_quality_get` are the same
interpretive class as `bodha_remedies_get` and share its exact defect mechanism.

Not exhaustively re-verified live this pass for every row above (2x diagnosis budget was spent on
tracing the two named tools to file:line per the Stage D contract's own emphasis) — the `orientation`
grep is a reliable proxy since every existing B.11-compliant tool in this codebase names the field
literally (`orientation_context`/`orientation_ok`), confirmed by the assess_* contrast in §1.

## 5. Blast radius + LEASE VERDICT

**CL-00 controls:** none of the 27 CL-00 gates check for B.11 orientation presence on non-assess_*
tools (spot-checked; no `orientation` string in the governance gate scripts this pass) — no CL-00
regression risk either way.

**Other lanes sharing these files:** `platform-mcp/src/tools/kala_views/upaya.ts` is not otherwise
touched by any other boarded finding this pass. `platform-mcp/src/tools/register_p1_aliases.ts` is
S5's file for CL-03 (`F-03/F-06/F-08/F-10/F-26/F-27/F-133`) and S1's ordered-first CL-11 sweep — a
B.11 fix here should land AFTER S1's `dualOutput` sweep completes (per plan §2.1 row 4's own
ordering) to avoid two writers on the same file in the same window.

**LEASE VERDICT: NOT fully S2-buildable. Split verdict:**

1. **S2-buildable today:** extracting/exporting a reusable orientation-gate function out of
   `fetchOrientationContext` (currently private, `registry_bridge.ts:2061`) — e.g. exporting it
   directly, or moving it to a small shared lib module that `registry_bridge.ts` re-exports from —
   is entirely inside S2's own lease (`registry_bridge.ts` is S2-owned) and closes zero of the two
   named defects by itself, but is the prerequisite every other stream's wiring depends on. S2
   should build and land this piece plus its own SPEC.md at Stage S.
2. **NOT S2-buildable — posting the flags:**
   - **`PAR-F125-NEEDS-LEASE platform-mcp/src/tools/kala_views/upaya.ts`** (S4 VĀCA, explicit
     lease). The one-line wiring fix (call the shared gate, attach `orientation_context`/
     `orientation_ok` to the response) must be built by S4 or handed S2's completed spec per
     "specs travel; leases don't."
   - **`PAR-F125-NEEDS-LEASE platform-mcp/src/tools/register_p1_aliases.ts`** (S5 MŪLA's primary
     lease). Because the real fix here is inside the generic `regAlias`/`globalAlias` helpers (not
     a one-off — see §4's `bodha_domain_reading_get`/`bodha_remedies_search`/`bodha_quality_get`
     siblings), this is a single mechanism change with the same "exemplar-then-replicate" shape
     the plan §5 favors — S5 should own it, sequenced after S1's CL-11 sweep on the same file.
3. Recommend the conductor either (a) re-leases both files to S2 for the lifetime of this one lane
   given the fix is genuinely one shared mechanism split across three files, or (b) has S2 finish
   Stage S with the spec covering all three files and hands the S4/S5 hunks to those streams'
   builders with the spec attached, per plan §2.1's explicit handoff rule. Either way, **this lane
   does not proceed to Stage B under S2's lease alone.**
