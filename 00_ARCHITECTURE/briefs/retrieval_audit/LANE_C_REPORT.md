---
artifact: LANE_C_REPORT.md
lane: C — Planner & taxonomy reality (plan §1.3, R-3)
parent_brief: RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0.md §E Lane C
audit_subject: RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md (v1.2) §1.3
status: COMPLETE
model: opus (high effort)
authored: 2026-07-19
read_only_scope: platform/** platform-mcp/** (no source modified)
---

# Lane C — Planner & Taxonomy Reality

Verdict summary: **7 of 7 audited claims CONFIRMED** (2 carry a precision
nuance noted inline). Zero STALE, zero WRONG, zero UNVERIFIABLE. Plus one
NEW-GAP surfaced (registry_data double-copy divergence) and one structural
finding about the unified-taxonomy feasibility (see final section).

All file:line cites are against the `ret/strategy-s1` worktree checkout.

---

## Per-claim verdicts

### C-1 — Consult route does NOT call the Vidhi compiler — **CONFIRMED**

`platform/src/app/api/chat/consult/route.ts` runs its own planner stack and
never touches `platform/src/lib/vidhi/` nor the platform-mcp vidhi compiler.

- Planner is `pipeline_planner` (`route.ts:72` `import { callPipelinePlanner as runPlanner … } from '@/lib/pipeline/pipeline_planner'`; invoked `route.ts:436`).
- Budget/bundle path is `arbitrateBudgets` (`route.ts:74,492`) + `hydrateBundle` (`route.ts:75,689`).
- Tool resolution is `getToolByName` from `tool_name_bridge` (`route.ts:78,748`).
- A grep for `vidhi | compileContract | lib/vidhi` across the entire
  `api/chat/consult/` tree returns **zero hits**. No `compileContract`, no
  `IntentFloor`, no `ScopeTuple` import anywhere on this door.

The plan's statement "Paripraśna does not use the Vidhi engine at all" is
exact. The acharya-floor / machine-band / completeness-receipt machinery
exists only on the MCP `plan_retrieval` / `vidhi_plan` path
(`platform-mcp/src/resources/vidhi/`), never on the portal's consult route.

### C-2 — Hardcoded B.11 injection + dead tool names — **CONFIRMED (nuance)**

The hardcoded B.11 floor injection is `route.ts:513-546`. When no L2.5 tool
is present in the plan, the route **manually pushes** tool_calls:

- Predictive branch (`route.ts:527-537`) pushes `marsys://tool/L2/query_signals`,
  `vector_search`, and **`pattern_register`** (`route.ts:535`, reason
  `'B.11 predictive floor: R7a requirement'`).
- Non-predictive branch (`route.ts:539-544`) pushes `query_signals` +
  `traverse_chart_graph` (both resolve).

**Dead-tool verification** (`tool_name_bridge.ts`): `pattern_register`,
`resonance_register`, `cluster_atlas` are documented "**no registered cap**"
(`tool_name_bridge.ts:369`) and were explicitly REMOVED from both
`SURGICAL_TOOLS` and `MCP_TO_RETRIEVAL_TOOL` (`tool_name_bridge.ts:482`).
Confirmed absent from `platform/src/lib/retrieval/registry/layers/` (no
`@register`/descriptor) and absent from `TOOL_NAME_TO_URI`. Therefore
`getToolByName('pattern_register')` returns `undefined`, and consult's
executor drops it silently at `route.ts:749` (`const t = getToolByName(...)
… if (!t) return null`). The "R7a requirement" floor item is a **guaranteed
no-op** — B.11's predictive floor believes it injected a pattern surface; it
injected nothing.

**Nuance (plan phrasing imprecise, claim substantively true):** the plan
says the injection "pushes tool names (`pattern_register`, `cluster_atlas`)".
In fact only **`pattern_register` is actually pushed** into `tool_calls`.
`cluster_atlas` never appears in a `.push()`; it lives only in the L2.5
detection membership list (`route.ts:520`) and `inferLayer` (`route.ts:145`),
i.e. it is a dead *constant* the route matches against but never emits. Both
names are equally dead in the registry; the correction is which one reaches
the injection. The plan should read "pushes the dead `pattern_register`; also
carries dead `cluster_atlas`/`resonance_register` in its L2.5 detection
constants."

### C-3 — DR-8 ↔ compiler vocabulary disjunction + silent coerce collapse — **CONFIRMED**

The two vocabularies share **zero** intent strings, and `coerce` collapses
every DR-8 intent to `general_synthesis` and every DR-8 depth to `deepdive`.

- DR-8 producer: `platform-mcp/src/tools/intent_scope_classifier.ts:24-37`
  `INTENTS` = {dasha_timing, transit_analysis, yoga_identification,
  planet_strength, house_analysis, remedy_lookup, panchanga, classical_rule,
  chart_overview, prediction_calibration, domain_assessment, unknown} (12).
- Compiler `IntentClass`: `platform-mcp/src/resources/vidhi/types.ts:86-94`
  (mirror `scope_resolver.ts:33-42` `INTENT_CLASSES`) = {wealth_deepdive,
  career_deepdive, health_deepdive, marriage_deepdive, structure_read,
  panoramic_breadth, retrieval_only, general_synthesis} (8).
- Set intersection = ∅ (no shared member).

The collapse mechanism is `scope_resolver.ts:70-72`:
```
function coerce<T>(value, allowed, fallback) {
  return value !== undefined && allowed.includes(value) ? value : fallback;
}
```
In `resolveScopeTuple` path 1 (a *received* DR-8 tuple, `scope_resolver.ts:100-109`):
- `intent: coerce(input.intent, INTENT_CLASSES, 'general_synthesis')` — any
  DR-8 value ('dasha_timing' etc.) fails `.includes` → **'general_synthesis'**.
- `depth: coerce(input.depth, DEPTHS, 'deepdive')` — DR-8 depths are
  {shallow, standard, deep} (`intent_scope_classifier.ts:47`); compiler
  `DEPTHS` are {retrieval, structure, deepdive} (`scope_resolver.ts:44`) →
  intersection ∅ → **'deepdive'**.
- `horizon`: DR-8 {past,present,near,far,atemporal} vs compiler
  {natal,current,multi_year} → ∅ → all collapse to `'current'`.
- `width`: partial overlap — {narrow,standard} survive, DR-8 'broad' → 'standard'.
- `domains`: **not** enum-coerced (`scope_resolver.ts:103`), so domain strings
  pass through verbatim — this is the *only* DR-8 signal that survives.

**Wiring is real, not hypothetical.** `plan_retrieval` builds its plan via
`plan_builder.ts:54` `resolveScopeTuple(args.question, args.scope_tuple)`.
The advertised path is: `intent_classify` (DR-8) → caller feeds
`scope_tuple` into `plan_retrieval` → `resolveScopeTuple` path 1 → coerce.
The compiler then selects the floor strictly by intent
(`compiler.ts:105` `registry.floors.find(f => f.intent === tuple.intent)`),
so a collapsed `general_synthesis` intent selects the 6-item
`GENERAL_SYNTHESIS_ITEMS` floor — **never** a 26/12/10/9-item domain floor.
The plan's "never selects a domain floor" is exact. (Note: `domains` survives,
so the domain is *known* but unused for floor selection — the floor is chosen
by intent alone, and intent is always crushed to general_synthesis.)

### C-4 — The 3+1 intent taxonomies — **CONFIRMED (enumerated)**

Four distinct, non-reconciled vocabularies exist:

1. **DR-8 taxonomy** — `intent_scope_classifier.ts:24-37` `INTENTS` (12, above).
2. **Vidhi compiler `IntentClass`** — `types.ts:86-94` / `scope_resolver.ts:33-42` (8, above).
3. **pipeline_planner `query_class`** — `platform/src/lib/pipeline/types.ts:45-56`
   `QueryClassEnum` = {factual, interpretive, predictive, cross_domain,
   discovery, holistic, remedial, cross_native, classical_grounding,
   multi_school_triangulation} (10).
4. **The "dormant prompt"** — `intent_scope_classifier.ts:75-94`
   `INTENT_CLASSIFY_TEMPLATE`, retained verbatim as `fallback_prompt`
   (`renderFallbackPrompt`, `:96-98`). Its enumerated intents (11) are the
   DR-8 set **minus `domain_assessment`** — so the dormant prompt disagrees
   even with its own module's live `INTENTS` array. Emitted whenever
   `fallback_recommended` (`:273`, low-confidence/unmatched).

Pairwise literal intersections: (1∩2)=∅, (1∩3)=∅, (2∩3)=∅. Three live
taxonomies with **zero shared strings**, plus a dormant prompt that is a
lossy subset of #1. The plan's "three live taxonomies plus a dormant prompt,
and the flagship handoff between two of them is a silent no-op" is confirmed
verbatim.

### C-5 — Floor thinness numbers — **CONFIRMED exactly (26/12/10/9)**

Counted directly from `platform-mcp/src/resources/vidhi/registry_data.ts`
floor-item constants:

| Intent floor | Const (line) | Item count | Plan claim |
|---|---|---|---|
| wealth_deepdive | `WEALTH_DEEPDIVE_ITEMS` (510-547) | **26** | 26 ✓ |
| career_deepdive | `CAREER_DEEPDIVE_ITEMS` (549-562) | **12** | 12 ✓ |
| health_deepdive | `HEALTH_DEEPDIVE_ITEMS` (564-575) | **10** | 10 ✓ |
| marriage_deepdive | `MARRIAGE_DEEPDIVE_ITEMS` (577-587) | **9** | 9 ✓ |
| structure_read | `STRUCTURE_READ_ITEMS` (590-596) | 5 | (not claimed) |
| panoramic_breadth | `PANORAMIC_BREADTH_ITEMS` (599-608) | 8 | (not claimed) |
| retrieval_only | `RETRIEVAL_ONLY_ITEMS` (611-613) | 1 | (not claimed) |
| general_synthesis | `GENERAL_SYNTHESIS_ITEMS` (616-623) | 6 | (not claimed) |

All four plan numbers are exact. The asymmetry is confirmed and maps directly
onto RETRIEVAL_STRATEGY §2 design-rule-5 ("Symmetric effort … today's thin
non-wealth floors are an asymmetry defect"): wealth carries 21 acharya-floor +
5 machine-band atoms; marriage carries 7+2. A "career scan" and a "marriage
scan" do NOT cost the same shape of call — R-3.3's floor-completeness campaign
is warranted, not cosmetic.

### C-6 — Dark-primitive CR list (12 of 37) — **CONFIRMED exactly**

`registry_data.ts` defines exactly **37 `VidhiPrimitive` rows**, each with a
`known_gap` field (docstring `:4` "37 versioned primitives"; 37 `known_gap:`
occurrences). Exactly **12** carry a non-null OPEN-CR known_gap:

| Primitive (line) | known_gap CR |
|---|---|
| special_lagna_read (98) | CR-16 |
| dhana_yoga_scan (122) | CR-56 (#1 acharya-grade blocker) |
| taranga_curve (183) | CR-66 |
| lel_retrodiction (195) | CR-68 |
| intervention_synthesis (207) | CR-69 |
| nakshatra_semantics (257) | CR-64 |
| dasha_window (305) | CR-37 |
| mechanism_read (341) | CR-24 |
| arudha_read (353) | CR-61 |
| dosha_scan (365) | CR-73 |
| remedy_scan (389) | CR-67 |
| kp_cusp_sublord_read (487) | CR-30 |

All 12 CRs are present in `cr_status.ts` `OPEN_CRS` — cross-checked: CR-16,
CR-24, CR-30, CR-37, CR-56, CR-61, CR-64, CR-66, CR-67, CR-68, CR-69, CR-73
all appear in the OPEN list (`cr_status.ts:24-63`). "12 of 37 primitives are
dark-by-construction with open CRs" is exact. (The other 25 have `known_gap:
null`, several annotated CLOSED_WITH_EVIDENCE.)

### C-7 — cr_status snapshot staleness incl. CR-55 conflict — **CONFIRMED**

`cr_status.ts` is a **frozen hand-authored snapshot**, not derived live:

- Three hardcoded arrays `OPEN_CRS` / `LOGGED_CRS` / `CLOSED_CRS`
  (`cr_status.ts:24,66,73`), sourced from "BRIEF_D2.md §B0.1 … bind-time
  CR-status snapshot" (`:5-10`). No DB read, no register parse — pure literal.
- Self-documented as needing re-derivation: "A verifier/Binder pass should
  re-derive this list from the live register at merge time" (`:9-10`).

**CR-55 self-flagged contradiction — present verbatim** (`cr_status.ts:12-20`):
> "KNOWN CONFLICT (flag for the verifier, not silently resolved): BRIEF_D2.md
> §B0.1 lists CR-55 as CLOSED … but POST_REMEDIATION_CONSUMPTION_REGISTER
> v1.5 §G row CR-55 itself is still marked 'OPEN — ELEVATED' … This module
> follows the brief's explicit instruction (never cite a CLOSED CR) and
> therefore does NOT emit CR-55 as a known_gap anywhere."

And `CR-55` is indeed hardcoded into `CLOSED_CRS` (`:76`) despite the flagged
register-body conflict. The plan's "frozen snapshot with a self-flagged CR-55
contradiction" is exact. Cross-reference (do not duplicate): the live defect
register `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` row D-5 notes "CR-55 appears
already fixed live" (weakest_graha), which is a *third* status reading — so
CR-55 currently carries three non-agreeing states (snapshot=CLOSED,
consumption-register-body=OPEN-ELEVATED, defect-register=appears-fixed). This
tri-state is exactly the staleness the snapshot cannot self-correct.

---

## Gaps found (NEW — not in plan §1.3)

- **NEW-GAP C-G1 — the two `registry_data.ts` copies have already drifted.**
  `platform/src/lib/vidhi/registry_data.ts` and
  `platform-mcp/src/resources/vidhi/registry_data.ts` are NOT byte-identical
  (`diff` differs at the type-import line: `'./types'` vs `'./types.js'`).
  Content (primitives + floors) is identical today, but the divergence proves
  the "hand-synced copies" have no parity gate and one has already been edited
  independently. This is the R-1.5/§1.1 vidhi triple-copy risk **already
  materializing** in Lane C's territory — the floors that R-3.3 will extend
  live in two files that can silently disagree. (`cr_status.ts` copies ARE
  still byte-identical — `diff` clean — so the drift is uneven across the
  vidhi module, which is the worst case for reasoning about it.)

- **Observation (not a new gap, sharpens C-2):** the B.11 injection's dead
  `pattern_register` means consult's *predictive* floor is quietly weaker than
  its non-predictive floor: the non-predictive branch injects two tools that
  both resolve; the predictive branch injects three, one of which is dead. A
  predictive B.11 satisfaction can pass on `query_signals`+`vector_search`
  alone while believing the R7a pattern requirement was met.

---

## Unified-taxonomy mapping table (draft for R-3.1)

**Critical structural finding first, because it changes what R-3.1 must build:**
the three live vocabularies are **not three implementations of one taxonomy** —
they are **three orthogonal axes** each collapsed into a single flat "intent"
field:

- **DR-8** cuts by *astrological technique/subject* (dasha, transit, yoga,
  strength, house, panchanga…) and carries *domain* in a **separate sibling
  field** (`domains[]`).
- **Vidhi `IntentClass`** cuts by *domain × depth fused into one token*
  (`wealth_deepdive` = domain wealth + depth deepdive).
- **`query_class`** cuts by *epistemic answer-mode* (factual / interpretive /
  predictive / holistic / remedial…).

That orthogonality — not sloppiness — is why the literal intersection is empty.
A flat superset-rename enum (the naive reading of plan R-3.1 step 1) **cannot**
unify them, because DR-8's domain lives outside its intent field and Vidhi
fuses two axes into one token. The only faithful unification is a **decomposed
scope tuple** `(answer_mode × domain × depth × horizon)` — and DR-8's existing
`ScopeTuple` is already the closest to that shape; the compiler's `IntentClass`
is the outlier that fuses axes.

The table below therefore maps by **decomposing each vocab onto the shared
axes**, then names the proposed unified token. "Proposed" = my synthesis;
"exists" = already in code.

Legend: A = DR-8 intent · B = Vidhi IntentClass · C = query_class ·
◇ = no counterpart in that vocab · **[mine]** = proposed resolution ·
**[code]** = mapping already present somewhere.

| # | DR-8 intent (A) | Vidhi IntentClass (B) | pipeline query_class (C) | Proposed unified token **[mine]** |
|---|---|---|---|---|
| 1 | chart_overview | structure_read | interpretive/holistic† | `read.structure` |
| 2 | domain_assessment (+domains=wealth) | wealth_deepdive | interpretive | `deepdive.wealth` |
| 3 | domain_assessment (+domains=career) | career_deepdive | interpretive | `deepdive.career` |
| 4 | domain_assessment (+domains=health) | health_deepdive | interpretive | `deepdive.health` |
| 5 | domain_assessment (+domains=marriage) | marriage_deepdive | interpretive | `deepdive.marriage` |
| 6 | domain_assessment (+domains=other) | ◇ (falls to general_synthesis) | interpretive/cross_domain | `deepdive.<domain>` (NEW floors needed) |
| 7 | ◇ (width=broad heuristic) | panoramic_breadth | holistic | `panorama.breadth` |
| 8 | ◇ | retrieval_only | factual | `retrieval.fact` |
| 9 | ◇ | general_synthesis | discovery/interpretive | `synthesis.general` (fallback) |
| 10 | dasha_timing | ◇ (no timing floor; folds into domain deepdive machine_band) | predictive | `timing.dasha` **(axis: horizon, not intent)** |
| 11 | transit_analysis | ◇ | predictive | `timing.transit` |
| 12 | prediction_calibration | ◇ | ◇ (no query_class) | `calibration.review` |
| 13 | yoga_identification | ◇ (yoga is a *primitive* dhana_yoga_scan, not an intent) | interpretive | `technique.yoga` **(axis: technique)** |
| 14 | planet_strength | ◇ (dignity_scan/shadbala_rank primitives) | interpretive/factual | `technique.strength` |
| 15 | house_analysis | ◇ (bhava_condition primitive) | interpretive | `technique.house` |
| 16 | panchanga | ◇ | factual | `reference.panchanga` |
| 17 | classical_rule | ◇ | classical_grounding | `reference.classical` |
| 18 | remedy_lookup | ◇ (intervention is a tuple axis + remedy_scan primitive) | remedial | `intervention.remedy` **(axis: intervention)** |
| 19 | ◇ | ◇ | cross_native | `compare.cross_native` (multi-chart; own axis) |
| 20 | ◇ | ◇ | multi_school_triangulation | `method.triangulation` (M9; own axis) |
| 21 | ◇ | ◇ | cross_domain | `panorama.multi_domain` |
| 22 | unknown | (default general_synthesis) | (default interpretive) | `unknown` → fallback + `scope_unresolved` flag |

† `query_class` has no structure/overview member; a "read my whole chart"
query classifies `holistic` or `interpretive` there — one of the axis
mismatches that makes rows 1/7/9 many-to-one.

**What the table reveals for R-3.1:**

1. **Rows 1-5 are the only clean 3-way alignments** — and only *after* DR-8's
   `domains` sibling field is folded in. Vidhi's four domain deepdives + one
   structure_read are the anchor; everything else is a partial.
2. **Rows 10-18 have no Vidhi `IntentClass` counterpart** because Vidhi
   models technique/timing/intervention as **primitive-level or tuple-axis
   concerns**, not intents. DR-8 models them as intents. This is a genuine
   design disagreement, not a naming gap — R-3.1 must rule which layer owns
   technique/timing/intervention.
3. **Rows 19-20 exist only in `query_class`** (cross-native, multi-school) —
   these are whole separate *methods*, arguably a fourth axis.
4. The unified vocabulary should almost certainly be the DR-8 tuple shape
   `{answer_mode, domain[], depth, horizon, intervention, entitlement}`
   (which already exists at `intent_scope_classifier.ts:52-60`), with the
   compiler's `IntentClass` **derived** from `(domain × depth)` rather than
   stored as a peer enum. That inverts plan R-3.1's implicit "one flat
   superset enum" into "one tuple, derived projections" — consistent with the
   plan's own §2 principle 1 ("one compiled source, many generated
   projections") applied to the taxonomy itself.

**No such mapping table exists anywhere in code today** — this is net-new
synthesis. The nearest existing artifacts are the two disjoint enum
declarations (A and B) and the `coerce` function that silently bridges them by
destroying A. There is no lookup table, no adapter, no test asserting a
round-trip; the "bridge" is data loss.

---

## Model / effort ledger

- **Model:** opus (Opus 4.8, 1M), **high effort** — this lane is
  adjudication-heavy (taxonomy orthogonality is a judgment call, not a count).
- **Files read in full:** `consult/route.ts`,
  `intent_scope_classifier.ts`, `scope_resolver.ts`, `cr_status.ts`
  (platform-mcp), `registry_data.ts` floor block (505-628), `types.ts` (vidhi,
  IntentClass block), `pipeline/types.ts` (QueryClassEnum block),
  `tool_name_bridge.ts` (deadtool blocks + test).
- **Greps/counts:** vidhi imports in consult tree (0 hits); dead-tool
  resolution in `layers/` + `TOOL_NAME_TO_URI` (0 caps); floor-item counts per
  intent; 37 primitives / 12 non-null known_gaps; cr_status/registry_data
  double-copy `diff`; resolveScopeTuple/classifyScope caller wiring.
- **DB:** none queried (claims were all static-source-verifiable; no dev DSN needed).
- **Judgment calls (flagged as non-mechanical):**
  1. C-2 nuance — deciding the plan's "pushes … cluster_atlas" is *imprecise
     but substantively correct* (only pattern_register is pushed) rather than
     WRONG. Judgment: the load-bearing claim (a dead tool reaches the B.11
     floor) holds, so CONFIRMED-with-nuance, not WRONG.
  2. C-3 "never selects a domain floor" — verified the collapse *mechanism*
     and the *compiler floor-selection-by-intent*, then judged the end-to-end
     claim true even though `domains` survives coerce (domains is unused for
     floor selection, so the surviving field does not rescue the claim).
  3. The unified-taxonomy structural finding (three orthogonal axes, not three
     dialects) is entirely my synthesis — it is the single most consequential
     judgment in this lane and directly contradicts the naive reading of plan
     R-3.1 step 1 ("superset mapping … flat"). Flagged for reconciliation.
  4. CR-55 tri-state observation cross-references the defect register per the
     brief (never duplicates its row).

*End Lane C report.*
