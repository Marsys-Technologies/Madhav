---
brief_id: RETRIEVAL_11C_b
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-29
authored_for: Claude Code execution
session_type: implementation (TypeScript router prompt + schema + tests; deploy; verify)
related_plan: 00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md (§2.3 fixes F3.3 + F3.4)
predecessor: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_a.md (status: COMPLETE; F3.2 graph topology fix landed; valid edges 21 → 126, orphans 105 → 0)
target_branch: redesign/r0-foundation
parallel_stream_note: |
  A separate UI/UX modernization stream is running R1 Roster + R2 Chart Profile
  briefs on the same branch (redesign/r0-foundation). Their scope is the UI
  surface (components/, app/, hooks/). This brief is router-side only —
  platform/src/lib/router/. We share the branch but never the same files.
  The active root brief CLAUDECODE_BRIEF.md belongs to the UI/UX stream and is
  off-limits.
estimated_time: 1–2 days

scope_summary: |
  Make cgm_graph_walk fire reliably and useful by teaching the classifier to
  emit real CGM node IDs in graph_seed_hints (F3.3) and to pick edge_type_filter
  per query intent (F3.4). The graph topology is now rich (369 nodes, 126 valid
  edges) thanks to brief 11C_a — but the classifier still emits placeholder
  strings like ["career_dharma", "relationships"] that don't match any row in
  l25_cgm_nodes. PROBE 8 from 2026-04-29 showed cgm_graph_walk firing in only
  1 of 17 queries (and that one errored). After this brief, the tool should
  fire non-empty in ≥ 30% of queries that name a chart entity.

  Concrete changes:
    • types.ts: add edge_type_filter?: string[] to QueryPlan
    • prompt.ts: add CGM_NODE_REFERENCE block listing valid node-id prefixes;
      add EDGE_TYPE_REFERENCE block; rewrite few-shot examples to use real
      node IDs; update prompt rules to instruct extraction
    • router.test.ts: add 10+ tests covering entity extraction across query
      forms (planet, house, yoga, karaka, dasha, divisional, UCN section)
    • verify cgm_graph_walk.ts already consumes the new fields (no edits)
    • npm test, deploy, capture verification trace data

may_touch:
  - platform/src/lib/router/types.ts                                       # add edge_type_filter
  - platform/src/lib/router/prompt.ts                                      # main rewrite — reference table + better few-shot + extraction rules
  - platform/src/lib/router/__tests__/router.test.ts                       # extend with seed-extraction tests
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_b.md             # status update at session end
  - 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_b.txt          # CREATE post-deploy verification
  # Read-only references (do NOT edit):
  - platform/src/lib/router/router.ts                                      # caller; understand flow only
  - platform/src/lib/retrieve/cgm_graph_walk.ts                            # consumer; verify field usage only
  - platform/src/lib/retrieve/types.ts                                     # consumer types
  - 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md                                     # source of node-id taxonomy
  - 035_DISCOVERY_LAYER/cgm_supports_edges_manifest_v1_0.json              # reference for valid edge types
  - 035_DISCOVERY_LAYER/cgm_contradicts_edges_manifest_v1_0.json
  - platform/scripts/retrieval_diagnostic_probes.sql                       # for re-running PROBE 8

must_not_touch:
  - CLAUDECODE_BRIEF.md                                                    # ROOT — UI/UX stream owns this
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_PROBES.md        # COMPLETE; do not re-edit
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_a.md             # COMPLETE; do not re-edit
  - 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_2026-04-29.txt          # historical artifact
  - 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_a.txt          # historical artifact
  - 00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md              # reference only
  - EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER_v1_0.md                           # belongs to UI/UX stream
  - EXEC_BRIEF_PORTAL_REDESIGN_R2_CHART_PROFILE_v1_0.md                    # belongs to UI/UX stream
  - platform/src/components/**                                             # UI/UX scope
  - platform/src/app/**                                                    # UI/UX scope
  - platform/src/hooks/**                                                  # UI/UX scope
  - platform/src/lib/retrieve/**                                           # consumer code is correct as-is; do NOT edit
  - platform/src/lib/bundle/**                                             # not in scope
  - platform/src/lib/synthesis/**                                          # not in scope
  - platform/python-sidecar/**                                             # F3.2 work just landed; do not disturb
  - platform/migrations/**                                                 # NO schema migrations
  - 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md                                     # source-of-truth; read-only
  - Any TypeScript file not explicitly listed in may_touch

acceptance_criteria:
  AC.1: types.ts gains edge_type_filter?: string[] on QueryPlan, placed alphabetically near graph_traversal_depth. No change to required fields. Schema_version stays "1.0" (additive optional field; no breaking change).
  AC.2: prompt.ts contains a new CGM_NODE_REFERENCE block enumerating every valid node-id prefix (PLN, HSE, SGN, NAK, YOG, KRK, SEN, DSH, DVS, UCN.SEC, KARAKA) with the canonical naming convention for each, plus 2–3 concrete examples per prefix.
  AC.3: prompt.ts contains an EDGE_TYPE_REFERENCE block enumerating valid edge types currently in the live graph (DISPOSITED_BY, NAKSHATRA_LORD_IS, ASPECTS_3RD/4TH/8TH, SUPPORTS, CONTRADICTS, plus YOGA_MEMBERSHIP, DASHA_ACTIVATION, DIVISIONAL_CONFIRMATION, KARAKA_ROLE if known to exist), with one-line per-type guidance on when to set each.
  AC.4: prompt.ts ROUTER_SYSTEM_PROMPT contains explicit extraction rules: "Extract every chart entity named in the query and map each to a valid CGM node ID using the reference table. graph_seed_hints contains 0–4 mapped IDs. If query is generic, leave empty []." Equivalent rule for edge_type_filter.
  AC.5: prompt.ts FEW_SHOT_EXAMPLES rewritten: every example that includes graph_seed_hints uses real CGM node IDs (no more "career_dharma" placeholders). At minimum: factual planet query → ["PLN.<NAME>"]; factual house query → ["HSE.<N>"]; cross_domain Mercury+Saturn → ["PLN.MERCURY","PLN.SATURN"]; yoga query → ["YOG.<NAME>"]; karaka contradiction query → ["KARAKA.DUAL_SYSTEM_DIVERGENCE"]. At least one example uses edge_type_filter.
  AC.6: router.test.ts adds ≥10 new test cases covering entity extraction. Each test mocks the LLM response with a representative QueryPlan and asserts that the parsed graph_seed_hints / edge_type_filter match expected values for queries like: "What does my Mercury support?" → ["PLN.MERCURY"]; "Tell me about Saraswati yoga" → ["YOG.SARASWATI"]; "What does the 7th house show?" → ["HSE.7"]; "Saturn dasha effects" → ["PLN.SATURN", "DSH.MD.SATURN"]; "the karaka contradiction in my chart" → ["KARAKA.DUAL_SYSTEM_DIVERGENCE"]; "describe my chart" → seeds=[]. Tests must pass.
  AC.7: cgm_graph_walk.ts is read-only-verified to consume both graph_seed_hints (already does) and edge_type_filter (already does per its existing implementation; if not, halt and report — do NOT modify). Document the verification result in the closing summary.
  AC.8: npm test passes at the pre-existing baseline (no NEW failures introduced; pre-existing failures unchanged is acceptable). Report exact passed/failed counts.
  AC.9: Cloud Run revision amjis-web is rebuilt and serving 100% via bash platform/scripts/cloud_build_submit.sh.
  AC.10: Post-deploy verification — send 5 representative test queries through the deployed amjis-web Consume tab (or via curl to /api/chat/consume), wait ~30s, then query query_trace_steps for each. Capture results to 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_b.txt. Expectation: ≥3 of 5 queries that name a chart entity have cgm_graph_walk in the trace AND with item_count > 0. (Compare to baseline 1 of 17 queries with non-empty cgm_graph_walk.)
  AC.11: This brief's frontmatter `status` is updated to COMPLETE.
  AC.12: `git status` after the session shows ONLY: types.ts, prompt.ts, router.test.ts (modifications), this brief (status flip), the new RETRIEVAL_PROBE_RESULTS_POST_11C_b.txt (created). No platform/python-sidecar/**, no platform/src/components/**, no platform/src/app/**, no platform/src/hooks/**, no platform/src/lib/retrieve/** changes.
---

# CLAUDECODE_BRIEF — RETRIEVAL_11C_b (F3.3 + F3.4 classifier seed extraction)

## §1 — Why this session

Brief 11C_a expanded the CGM graph from 21 valid edges to 126 (and orphans dropped from 105 to 0). But that win is currently invisible to users because the classifier still emits placeholder strings like `["career_dharma", "relationships"]` in `graph_seed_hints` instead of real CGM node IDs. PROBE 8 from 2026-04-29 showed `cgm_graph_walk` firing in only 1 of 17 queries — and that one errored. The tool's hard gate at line ~88 of `cgm_graph_walk.ts` returns immediately when seeds don't match any row in `l25_cgm_nodes`, so unmappable seeds are functionally identical to no seeds.

This session teaches the classifier to extract real entities from query text and emit them as valid CGM node IDs. It also adds `edge_type_filter` to the schema so the classifier can narrow traversal per query intent.

## §2 — Architecture confirmation (r0-foundation, post-11C_a)

The codebase is on `redesign/r0-foundation`. The retrieval pipeline is:

```
classify  →  compose_bundle  →  retrieve(parallel)  →  context_assembly  →  synthesize  →  audit
   ↑
  THIS SESSION
```

Files relevant to this session, all confirmed present on the branch:

- `platform/src/lib/router/router.ts` — calls Claude with the prompt, validates response. **Read-only this session.**
- `platform/src/lib/router/prompt.ts` — system prompt + user message builder + few-shot examples. **Main edit target.**
- `platform/src/lib/router/types.ts` — `QueryPlan` interface. **One additive field.**
- `platform/src/lib/router/__tests__/router.test.ts` — existing tests. **Extend, don't replace.**
- `platform/src/lib/retrieve/cgm_graph_walk.ts` — the consumer. **Read-only verification this session.**

Live graph state in `l25_cgm_nodes` (per 11C_a closing summary): **369 nodes** spanning these prefixes:

- `PLN.*` — 9 planets + LAGNA
- `HSE.*` — 12 houses
- `SGN.*` — 12 signs
- `NAK.*` — 15 nakshatras (with chart placements)
- `YOG.*` — 19 yogas
- `KRK.*` — 18 karakas
- `SEN.*` — 42 sensitive points
- `DSH.*` — 30 dasha periods
- `DVS.*` — 77 divisional positions
- `UCN.SEC.*` — 134 UCN section nodes (newly added by 11C_a)
- `KARAKA.*` — 1 meta-node (`KARAKA.DUAL_SYSTEM_DIVERGENCE`, newly added by 11C_a)

Live valid edge types in `l25_cgm_edges` (status='valid', count 126): primarily `DISPOSITED_BY`, `NAKSHATRA_LORD_IS`, `ASPECTS_3RD/4TH/8TH`, `SUPPORTS`, `CONTRADICTS`. Verify exact distribution by running this in a psql shell against the Auth Proxy before authoring the EDGE_TYPE_REFERENCE block:

```sql
SELECT edge_type, COUNT(*) FROM l25_cgm_edges
WHERE status = 'valid' GROUP BY edge_type ORDER BY count DESC;
```

## §3 — Implementation steps

### §3.1 — Read the consumer first

Open `platform/src/lib/retrieve/cgm_graph_walk.ts` and confirm two things WITHOUT modifying it:

1. The tool reads `plan.graph_seed_hints: string[]`. (Yesterday's static analysis confirmed this; verify by inspection.)
2. The tool reads `plan.edge_type_filter: string[]` OR `params.edge_type_filter`. If the field is absent from the consumer, halt and report — adding the field to QueryPlan without a consumer that reads it is a no-op.

If verification fails, stop here and report. The brief assumes the consumer is correct as-is per yesterday's static analysis.

### §3.2 — Extend QueryPlan schema (types.ts)

Add the following field to the `QueryPlan` interface, placed in the optional-fields block alphabetically near `graph_traversal_depth`:

```ts
  edge_type_filter?: string[]
```

Add a one-line JSDoc comment above it: `/** Edge types the classifier wants cgm_graph_walk to traverse. Empty/undefined = all edge types. */`

Do not change the schema_version. This is an additive optional field; existing QueryPlan instances remain valid.

### §3.3 — Rewrite the router prompt (prompt.ts)

This is the main edit. Three sub-changes:

#### §3.3.1 — Add CGM_NODE_REFERENCE block

Inside the system prompt, BEFORE the few-shot examples section, add a new block:

```
## CGM Node ID reference

Valid node-id prefixes the classifier may emit in graph_seed_hints:

- PLN.<PLANET>            — planets. PLN.SUN, PLN.MOON, PLN.MARS, PLN.MERCURY,
                            PLN.JUPITER, PLN.VENUS, PLN.SATURN, PLN.RAHU,
                            PLN.KETU, PLN.LAGNA.
- HSE.<N>                 — houses 1–12. HSE.1, HSE.7, HSE.10.
- SGN.<SIGN>              — signs. SGN.ARIES, SGN.LIBRA, SGN.CAPRICORN, etc.
- NAK.<NAKSHATRA>         — nakshatras with chart placements (15 of 27).
                            Examples: NAK.ASHWINI, NAK.HASTA, NAK.PUSHYA.
- YOG.<NAME>              — named yogas. Examples: YOG.SARASWATI, YOG.LAKSHMI,
                            YOG.GAJAKESARI, YOG.SASHA. Use the yoga's canonical name.
- KRK.<C8|C7>.<KARAKA>    — karakas. C8 = 8-karaka system, C7 = 7-karaka system.
                            Examples: KRK.C8.AK (Atmakaraka), KRK.C8.AmK
                            (Amatyakaraka), KRK.C8.DARA, KRK.C8.PK, KRK.C8.GK.
- SEN.<NAME>              — sensitive points: arudhas, special lagnas, sahams,
                            yogi/avayogi/mandi/gulika. Examples: SEN.AL (Arudha
                            Lagna), SEN.UL (Upapada Lagna), SEN.GULIKA, SEN.YOGI,
                            SEN.SAHAM_VIVAHA.
- DSH.MD.<PLANET>         — Vimshottari mahadashas. DSH.MD.MERCURY, DSH.MD.SATURN,
                            DSH.MD.KETU. Use the dasha lord planet.
- DSH.AD.<PLANET>         — Vimshottari antardashas; same naming.
- DVS.<DIVISIONAL>.<ENT>  — divisional placements. DVS.D9.MOON, DVS.D10.SATURN,
                            DVS.D27.LAGNA, DVS.D60.MERCURY. <ENT> is usually a
                            planet or LAGNA.
- UCN.SEC.<PART>.<SUB>    — UCN section nodes. UCN.SEC.III.4, UCN.SEC.IV.1,
                            UCN.SEC.VI.3. Use only when query references a
                            specific UCN section by name or part number.
- KARAKA.<NAME>           — karaka meta-concepts. KARAKA.DUAL_SYSTEM_DIVERGENCE
                            represents the 7-karaka vs 8-karaka divergence.
```

#### §3.3.2 — Add EDGE_TYPE_REFERENCE block

Immediately after the CGM_NODE_REFERENCE block:

```
## CGM Edge type reference

Valid edge_type values the classifier may emit in edge_type_filter:

- DISPOSITED_BY      — dispositor relationships. Use for "who governs", "what
                       rules", "who is the lord of".
- NAKSHATRA_LORD_IS  — nakshatra lordship. Use for nakshatra-specific queries.
- ASPECTS_3RD        — Vedic 3rd-house aspect (Mars-special).
- ASPECTS_4TH        — 4th-house aspect (Saturn-special).
- ASPECTS_8TH        — 8th-house aspect (Saturn-special).
- SUPPORTS           — pattern-supports relationships from the Discovery Layer.
                       Use for queries asking "what reinforces", "what amplifies".
- CONTRADICTS        — pattern-contradicts relationships. Use for queries asking
                       "what conflicts with", "what challenges", "tensions".
- YOGA_MEMBERSHIP    — planet/house belongs to yoga. Use for yoga drill-downs.
- DASHA_ACTIVATION   — dasha activates pattern. Use for dasha-windowed queries.
- DIVISIONAL_CONFIRMATION — varga corroboration. Use for divisional cross-checks.

Leave edge_type_filter empty [] when the query is general or you are unsure.
A narrow filter when one is wrong is worse than no filter.
```

#### §3.3.3 — Rewrite extraction rules + few-shot examples

In the existing "## Rules" numbered list, replace rule 10 (`graph_seed_hints: array of CGM node IDs relevant to the query (may be empty []).`) with:

```
10. graph_seed_hints: extract every chart entity named in the query (planet,
    house, sign, nakshatra, yoga, karaka, sensitive point, dasha, divisional
    placement, UCN section, karaka meta-concept) and map each to a valid
    CGM node ID using the CGM Node ID reference. 0–4 IDs typical; 5+ allowed
    when query is dense. If the query is generic ("explain my chart"), leave
    empty []. Never invent prefixes or node IDs not in the reference.
13. edge_type_filter: optional list of CGM edge types to constrain
    cgm_graph_walk traversal. Use sparingly — only set when the query
    clearly asks about one type of relationship (e.g., dispositor questions
    → ["DISPOSITED_BY"]; "what supports X" → ["SUPPORTS"]). When unsure,
    leave empty/undefined.
```

(Renumber subsequent rules accordingly if needed.)

Then **rewrite every few-shot example** that has `graph_seed_hints` to use real CGM node IDs:

- **factual** Mercury query: `"graph_seed_hints": ["PLN.MERCURY"]` (add this — currently no graph_seed_hints field on this example).
- **interpretive** career query: `"graph_seed_hints": ["HSE.10", "PLN.MERCURY"]` (Mercury is the chart's career significator per FORENSIC; HSE.10 is the career house). Add a comment in the example noting this is chart-specific.
- **predictive** career-change query: keep `graph_seed_hints` minimal (the predictive class is dasha-driven, not graph-driven): `["DSH.MD.SATURN", "PLN.SATURN"]`.
- **cross_domain** career+marriage: replace `["career_dharma", "relationships"]` with `["HSE.7", "HSE.10", "PLN.MARS", "PLN.SATURN"]` and add `"edge_type_filter": ["CONTRADICTS", "SUPPORTS"]`.
- **discovery** patterns query: `"graph_seed_hints": []` is correct (pattern-level meta-question; no specific entities).
- **holistic** comprehensive: `"graph_seed_hints": []` (too broad to seed; let other tools do the work).
- **remedial** Saturn: `"graph_seed_hints": ["PLN.SATURN"]`.
- **cross_native** Saturn placements: `"graph_seed_hints": ["PLN.SATURN"]`.

Add ONE entirely new few-shot example that exercises a UCN section seed:

```json
#### interpretive (UCN section reference)
Query: "Explain section IV.1 of my unified chart narrative."
Output:
{
  "query_plan_id": "00000000-0000-0000-0000-000000000009",
  "query_text": "Explain section IV.1 of my unified chart narrative.",
  "query_class": "interpretive",
  "domains": [],
  "forward_looking": false,
  "audience_tier": "client",
  "tools_authorized": ["msr_sql", "cgm_graph_walk", "vector_search"],
  "history_mode": "synthesized",
  "panel_mode": false,
  "expected_output_shape": "three_interpretation",
  "manifest_fingerprint": "__PLACEHOLDER__",
  "schema_version": "1.0",
  "graph_seed_hints": ["UCN.SEC.IV.1"]
}
```

### §3.4 — Update tests (router.test.ts)

Open `platform/src/lib/router/__tests__/router.test.ts` and find the existing pattern for testing parsed QueryPlan output (the test file contains existing tests for each `query_class` value per the agent's earlier inspection). Add at least 10 new tests using the same mock pattern. Required test cases:

| query | expected graph_seed_hints | expected edge_type_filter |
|---|---|---|
| "What does my Mercury support?" | `["PLN.MERCURY"]` | `["SUPPORTS"]` (or omitted) |
| "Tell me about my Saraswati yoga." | `["YOG.SARASWATI"]` | unset |
| "Which dispositor governs my Saturn?" | `["PLN.SATURN"]` | `["DISPOSITED_BY"]` |
| "What does the 7th house show in my chart?" | `["HSE.7"]` | unset |
| "How does my Saturn dasha affect my career?" | `["PLN.SATURN", "DSH.MD.SATURN", "HSE.10"]` (any subset) | unset or `["DASHA_ACTIVATION"]` |
| "Are there contradictions in my karaka assignment?" | `["KARAKA.DUAL_SYSTEM_DIVERGENCE"]` | `["CONTRADICTS"]` |
| "Describe section IV.1 of my unified narrative." | `["UCN.SEC.IV.1"]` | unset |
| "What does my chart say about life direction?" (generic) | `[]` (empty) | unset |
| "How do my Mars and Saturn interact?" | `["PLN.MARS", "PLN.SATURN"]` | unset |
| "What's my Atmakaraka?" | `["KRK.C8.AK"]` (factual class) | unset |

Each test mocks the LLM call to return a stub QueryPlan matching the expected output, then asserts via `expect(plan.graph_seed_hints).toEqual(expected)` (or `.toContain()` for subset assertions). Reuse the existing test helper if there is one; do not duplicate setup boilerplate.

### §3.5 — Run npm test

Run `npm test` from `platform/`. Capture the exact passed/failed counts. Compare to the pre-existing baseline (which had ~9 failures across pre-existing test files unrelated to router work per yesterday's session reports). Acceptable: same failure count, no new failures. If new failures appear, investigate and fix in scope.

### §3.6 — Deploy

```
bash platform/scripts/cloud_build_submit.sh
```

Confirm via `gcloud run revisions list --service amjis-web --region asia-south1 --project madhav-astrology --limit 3` that a new revision is serving 100%.

### §3.7 — Post-deploy verification

Send 5 representative test queries through the deployed app. Two paths — pick whichever is faster:

**Path A — UI:** open the Consume tab, send each query, then query the DB.

**Path B — curl:** post to `/api/chat/consume` with a test session cookie. Less reliable due to auth; use Path A unless you have a known-good cookie.

The 5 queries to send:

1. "What does my Mercury support in my chart?"
2. "How do my Mars and Saturn interact?"
3. "What does my Saturn dasha bring next?"
4. "Are there contradictions in my chart?"
5. "Explain my chart in general terms." (control — should NOT seed cgm_graph_walk)

Wait ~30 seconds after the last query, then query `query_trace_steps` via psql against the Auth Proxy:

```sql
SELECT
  query_id,
  step_seq,
  step_name,
  status,
  COALESCE(jsonb_array_length(payload->'items'), 0) AS item_count
FROM query_trace_steps
WHERE created_at > NOW() - INTERVAL '10 minutes'
  AND step_name = 'cgm_graph_walk'
ORDER BY query_id, step_seq;
```

Expectation: queries 1–4 should produce `cgm_graph_walk` rows with `status='done'` AND `item_count > 0`. Query 5 may produce a row with `item_count=0` (no seeds → empty bundle, that's correct behavior).

Capture the full output (plus a SELECT of the corresponding query_plans entries showing graph_seed_hints) to `00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_b.txt`.

If `query_plans` table doesn't exist (it didn't in PROBE 7 from 2026-04-29), get the seeds from `payload->'graph_seed_hints'` on the relevant trace step instead.

### §3.8 — Close

1. Set this brief's `status: COMPLETE` in the frontmatter.
2. In the closing message, print:
   - Pre-fix baseline (PROBE 8 from 2026-04-29): cgm_graph_walk fired non-empty in 1 of 17 queries.
   - Post-fix verification: cgm_graph_walk fired non-empty in N of 5 test queries.
   - Test results: passed/failed counts.
   - Cloud Run revision deployed.
   - List of files modified.

## §4 — Hard constraints

- **Router only.** This session edits exactly three TypeScript files: `types.ts`, `prompt.ts`, `router.test.ts`. No other source-code edits are permitted.
- **Do not modify the consumer.** `cgm_graph_walk.ts` is verified-only. If the consumer needs changes, halt and report — that's a separate brief.
- **Do not modify the writers / extractors.** The Python sidecar is finished work from 11C_a. Off-limits.
- **No migrations, no schema changes.** Adding `edge_type_filter?: string[]` to a TypeScript interface is not a DB migration — it's a code-only addition that the JSONB-shaped `query_trace_steps.payload` and the in-memory QueryPlan can carry without DB change.
- **The active root brief** `CLAUDECODE_BRIEF.md` belongs to the UI/UX stream. Do not read or modify it.
- **The two untracked R1/R2 EXEC briefs** at the repo root belong to the UI/UX stream. Do not touch.
- **Halt-and-report on blockers.** If `cgm_graph_walk.ts` doesn't already read `edge_type_filter`, do not add code to make it. Stop and report. (Yesterday's static analysis said it does; if reality disagrees, that's a finding, not a license to expand scope.)

## §5 — Closing checklist

- [ ] AC.1 verified — `edge_type_filter?: string[]` field on QueryPlan.
- [ ] AC.2 verified — CGM_NODE_REFERENCE block present in prompt.
- [ ] AC.3 verified — EDGE_TYPE_REFERENCE block present in prompt.
- [ ] AC.4 verified — extraction rules updated.
- [ ] AC.5 verified — few-shot examples use real node IDs; new UCN.SEC example present.
- [ ] AC.6 verified — ≥10 new test cases pass.
- [ ] AC.7 verified — `cgm_graph_walk.ts` already consumes both fields (read-only check documented).
- [ ] AC.8 verified — npm test at baseline.
- [ ] AC.9 verified — Cloud Run revision deployed.
- [ ] AC.10 verified — POST_11C_b.txt exists with verification data.
- [ ] AC.11 — this brief's status set to COMPLETE.
- [ ] AC.12 verified — `git status` shows only the expected files.

---

*End of CLAUDECODE_BRIEF_RETRIEVAL_11C_b. Status: PENDING.*
