---
artifact: CLAUDECODE_BRIEF_QP_S3.md
status: COMPLETE
session_id: QP-S3
phase: Pipeline Gap Closure — Golden Set Expansion (v1.1 → v1.2)
executor: claude-opus-4-6 (anti-gravity VS Code)
run_from_worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-eval
branch: fix/golden-set-qp-s3
authored_by: Cowork (Abhisek session 2026-05-11)
authored_on: 2026-05-11
acceptance_criteria_count: 5
parallel_safe: true
parallel_siblings: QP-S1 (fix/planner-gap-qp-s1), QP-S2 (fix/cleanup-qp-s2)
depends_on: Pipeline-Transform-S1 merged to main (commit 85dfca5)
master_plan: 00_ARCHITECTURE/PIPELINE_GAP_PLAN_v1_0.md §4/QP-S3
---

# QP-S3 — Golden Set Expansion

## §0 — HOW TO READ THIS BRIEF

**Run from the worktree:** `/Users/Dev/Vibe-Coding/Apps/Madhav-eval`
(branch `fix/golden-set-qp-s3`).

**One file only.** This session touches exactly one file:
`platform/tests/eval/planner_golden_set.json`. Everything else is out of scope.

When all 5 ACs are GREEN, commit, push, and set `status: COMPLETE` in this
file's frontmatter. Do not emit SESSION_OPEN or SESSION_CLOSE artifacts.

---

## §1 — CONTEXT AND PROBLEM

The current golden set (`planner_golden_set.json` v1.1, 29 entries) was
designed to verify the existing prompt rules. Post-Transform-S1, it has zero
coverage for four of the eight query classes:

| Class | Current entries | Problem |
|-------|----------------|---------|
| `discovery` | 0 | No entries validate R-DISC rule QP-S1 is adding |
| `cross_domain` | 0 | No entries validate R-CDOM rule QP-S1 is adding |
| `factual` | 0 | No entries validate R-FACT rule QP-S1 is adding |
| `cross_native` | 0 | No native-2 data — deferred to M5; one stub entry to hold slot |

Additionally, the new fields `time_window` and `graph_seed_hints` introduced
by Pipeline-Transform-S1 have zero golden entries asserting on their population.
The smoke runner currently has no way to verify these fields are correctly set.

**What this session does:** Add 17 new entries (GT.030–GT.046) to fill these
gaps. Bump `$schema_version` to `"1.2"`. Update `category_distribution`.

**What this session does NOT do:** Edit any prompt file. Edit any source code.
Run the eval. Those belong to QP-S1 and QP-S4 respectively.

**Dependency note:** QP-S3 entries are authored against the rules that QP-S1
is *adding* to the prompt. The entries describe what the correct plan *should*
look like once R-DISC, R-CDOM, R-FACT, R-TW1, R-TW2, R-GSH, and the R14a
amendment are in place. The full eval validating these entries runs in QP-S4
after both QP-S1 and QP-S3 are merged to main.

---

## §2 — MANDATORY READING BEFORE WRITING ANYTHING

```
platform/tests/eval/planner_golden_set.json          ← THE ONLY FILE TO EDIT
platform/tests/eval/planner_smoke_runner.ts          ← Read to understand entry schema (read-only)
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md               ← Read §3 for rule context (read-only)
00_ARCHITECTURE/PIPELINE_GAP_PLAN_v1_0.md §4/QP-S3  ← Full entry specs (read-only)
```

Do NOT touch any other file.

---

## §3 — WORK TO DO: ADD GT.030–GT.046 (17 entries)

### Schema requirements per entry

Every entry must include:
- `id`: string (e.g. `"GT.030"`)
- `query`: string (the natural language query being tested)
- `query_class`: one of the 8 valid enum values
- `category`: string label (e.g. `"factual"`, `"discovery"`, `"cross_domain"`, `"predictive"`, `"holistic"`, `"interpretive"`, `"deferred"`)
- `expected_tools`: string[] (ordered by priority — what the planner should produce)
- `required_tools`: string[] (subset that must be present — eval fails if any are absent)
- `forbidden_tools`: string[] (eval fails if any of these appear in the plan)
- `required_asset_ids`: string[] (FORENSIC, CGM, UCN, CDLM, LEL as applicable)
- `notes`: string (explains why this plan is correct; cite rule IDs where applicable)

**Extension field for new schema fields:** For entries that assert on `time_window`
or `graph_seed_hints` population, add:
- `required_plan_fields`: string[] (e.g. `["time_window"]`, `["graph_seed_hints"]`)

The smoke runner's existing degenerate-entry guard skips entries with empty
`expected_tools[]` — the GT.046 cross_native stub will be skipped automatically.

---

### GT.030–GT.032: factual class (3 entries)

```json
{
  "id": "GT.030",
  "query": "What is my lagna?",
  "query_class": "factual",
  "category": "factual",
  "expected_tools": ["msr_sql"],
  "required_tools": ["msr_sql"],
  "forbidden_tools": ["cgm_graph_walk", "cluster_atlas", "resonance_register", "vector_search"],
  "required_asset_ids": ["FORENSIC", "CGM"],
  "notes": "R-FACT: single chart-lookup — one msr_sql call, no synthesis_guidance, no discovery register. expected_output_shape: single_answer."
}
```

```json
{
  "id": "GT.031",
  "query": "Which house is Jupiter placed in?",
  "query_class": "factual",
  "category": "factual",
  "expected_tools": ["msr_sql"],
  "required_tools": ["msr_sql"],
  "forbidden_tools": ["vector_search", "pattern_register", "cgm_graph_walk"],
  "required_asset_ids": ["FORENSIC", "CGM"],
  "notes": "R-FACT: positional chart lookup — one msr_sql call sufficient. No interpretation layer needed."
}
```

```json
{
  "id": "GT.032",
  "query": "What gemstone does the Marakacharya prescribe for Venus?",
  "query_class": "factual",
  "category": "factual",
  "expected_tools": ["remedial_codex_query"],
  "required_tools": ["remedial_codex_query"],
  "forbidden_tools": ["msr_sql", "vector_search", "pattern_register"],
  "required_asset_ids": ["FORENSIC", "CGM"],
  "notes": "R-FACT codex-lookup branch: remedial codex query, not chart analysis. No msr_sql needed."
}
```

---

### GT.033–GT.035: discovery class (3 entries)

```json
{
  "id": "GT.033",
  "query": "What's the most interesting or unusual thing about my chart?",
  "query_class": "discovery",
  "category": "discovery",
  "expected_tools": ["pattern_register", "contradiction_register", "resonance_register", "cluster_atlas"],
  "required_tools": ["pattern_register", "contradiction_register"],
  "forbidden_tools": ["remedial_codex_query"],
  "required_asset_ids": ["FORENSIC", "CGM", "UCN", "CDLM"],
  "notes": "R-DISC: open-ended discovery — all four L2.5 registers. No domain anchor so msr_sql is not added. Open exploration language triggers all four registers."
}
```

```json
{
  "id": "GT.034",
  "query": "Surprise me — what patterns in my chart haven't I asked about yet?",
  "query_class": "discovery",
  "category": "discovery",
  "expected_tools": ["pattern_register", "contradiction_register", "resonance_register", "cluster_atlas"],
  "required_tools": ["pattern_register", "cluster_atlas"],
  "forbidden_tools": ["remedial_codex_query", "msr_sql"],
  "required_asset_ids": ["FORENSIC", "CGM", "UCN", "CDLM"],
  "notes": "R-DISC: classic discovery trigger ('surprise me', 'patterns'). No domain signal — msr_sql explicitly forbidden. All four L2.5 registers required."
}
```

```json
{
  "id": "GT.035",
  "query": "What stands out in my career domain that I might be overlooking?",
  "query_class": "discovery",
  "category": "discovery",
  "expected_tools": ["pattern_register", "contradiction_register", "resonance_register", "cluster_atlas", "msr_sql"],
  "required_tools": ["pattern_register", "msr_sql"],
  "forbidden_tools": ["remedial_codex_query"],
  "required_asset_ids": ["FORENSIC", "CGM", "UCN", "CDLM"],
  "notes": "R-DISC with domain anchor: discovery query naming 'career' domain — msr_sql added at priority 3 per R-DISC exception rule. All four L2.5 registers remain required."
}
```

---

### GT.036–GT.038: cross_domain class (3 entries)

```json
{
  "id": "GT.036",
  "query": "How does my Mars affect both my career and my relationships?",
  "query_class": "cross_domain",
  "category": "cross_domain",
  "expected_tools": ["msr_sql", "vector_search"],
  "required_tools": ["msr_sql", "vector_search"],
  "forbidden_tools": ["remedial_codex_query"],
  "required_asset_ids": ["FORENSIC", "CGM", "UCN", "CDLM"],
  "notes": "R-CDOM: two named domains (career, relationships) — msr_sql + vector_search x2 (one per domain). No explicit interaction language so cgm_graph_walk not required."
}
```

```json
{
  "id": "GT.037",
  "query": "What is the relationship between my spiritual growth and financial stability in my chart?",
  "query_class": "cross_domain",
  "category": "cross_domain",
  "expected_tools": ["msr_sql", "vector_search", "cgm_graph_walk"],
  "required_tools": ["msr_sql", "vector_search"],
  "forbidden_tools": ["remedial_codex_query", "pattern_register"],
  "required_asset_ids": ["FORENSIC", "CGM", "UCN", "CDLM"],
  "notes": "R-CDOM: two named domains + 'relationship between' interaction language — cgm_graph_walk added at priority 2 per R-CDOM. vector_search fires once per domain."
}
```

```json
{
  "id": "GT.038",
  "query": "Tell me how career, health, and relationships are connected in my chart.",
  "query_class": "cross_domain",
  "category": "cross_domain",
  "expected_tools": ["msr_sql", "vector_search", "cgm_graph_walk"],
  "required_tools": ["msr_sql", "cgm_graph_walk"],
  "forbidden_tools": ["remedial_codex_query", "pattern_register"],
  "required_asset_ids": ["FORENSIC", "CGM", "UCN", "CDLM"],
  "notes": "R-CDOM: three named domains + 'connected' interaction language — cgm_graph_walk required per explicit interaction trigger. msr_sql + vector_search fire per domain."
}
```

---

### GT.039–GT.040: time_window population (2 entries)

```json
{
  "id": "GT.039",
  "query": "Will there be any significant lunar eclipses affecting me in the next 3 months?",
  "query_class": "predictive",
  "category": "predictive",
  "expected_tools": ["msr_sql", "pattern_register"],
  "required_tools": ["msr_sql", "pattern_register"],
  "forbidden_tools": ["vector_search", "cgm_graph_walk"],
  "required_asset_ids": ["FORENSIC", "CGM", "LEL"],
  "required_plan_fields": ["time_window"],
  "notes": "R-TW1: eclipse keyword in predictive query — time_window must be populated with 90-day forward window. planets: ['Moon']. R7c transit ban: vector_search forbidden. required_plan_fields asserts time_window presence in emitted plan."
}
```

```json
{
  "id": "GT.040",
  "query": "What can I expect during my Mercury antardasha from 2025 to 2027?",
  "query_class": "predictive",
  "category": "predictive",
  "expected_tools": ["msr_sql", "pattern_register"],
  "required_tools": ["msr_sql", "pattern_register"],
  "forbidden_tools": ["vector_search", "remedial_codex_query"],
  "required_asset_ids": ["FORENSIC", "CGM", "LEL"],
  "required_plan_fields": ["time_window", "dasha_context_required"],
  "notes": "R-TW2: named antardasha (Mercury) + explicit date range (2025–2027) — time_window: {start: '2025-01-01', end: '2027-12-31'}, dasha_context_required: true. required_plan_fields asserts both fields populated."
}
```

---

### GT.041–GT.042: graph_seed_hints population (2 entries)

```json
{
  "id": "GT.041",
  "query": "Map out the architectural role of my Atmakaraka and Amatyakaraka across all major yogas.",
  "query_class": "holistic",
  "category": "holistic",
  "expected_tools": ["msr_sql", "cgm_graph_walk", "cluster_atlas", "pattern_register"],
  "required_tools": ["msr_sql", "cgm_graph_walk"],
  "forbidden_tools": ["remedial_codex_query", "resonance_register"],
  "required_asset_ids": ["FORENSIC", "CGM", "UCN", "CDLM"],
  "required_plan_fields": ["graph_seed_hints"],
  "notes": "R-GSH: explicit AK/AmK + yoga mapping — graph_seed_hints must be populated with KRK.* and YOG.* namespace node IDs. required_plan_fields asserts graph_seed_hints presence."
}
```

```json
{
  "id": "GT.042",
  "query": "How do Lakshmi Yoga and Sasha Yoga interact with my current Mercury mahadasha?",
  "query_class": "interpretive",
  "category": "interpretive",
  "expected_tools": ["msr_sql", "pattern_register", "cgm_graph_walk"],
  "required_tools": ["msr_sql", "pattern_register"],
  "forbidden_tools": ["remedial_codex_query", "resonance_register"],
  "required_asset_ids": ["FORENSIC", "CGM", "UCN"],
  "required_plan_fields": ["graph_seed_hints"],
  "notes": "R-GSH: named yogas (Lakshmi Yoga, Sasha Yoga) + named dasha lord (Mercury mahadasha) — graph_seed_hints should include YOG.LAKSHMI, YOG.SASHA, DSH.MD.MERCURY. required_plan_fields asserts graph_seed_hints non-empty."
}
```

---

### GT.043–GT.044: predictive edge cases (2 entries)

```json
{
  "id": "GT.043",
  "query": "When is the most favorable window for career advancement in the next 2 years?",
  "query_class": "predictive",
  "category": "predictive",
  "expected_tools": ["msr_sql", "pattern_register"],
  "required_tools": ["msr_sql", "pattern_register"],
  "forbidden_tools": ["vector_search", "cgm_graph_walk"],
  "required_asset_ids": ["FORENSIC", "CGM", "LEL"],
  "notes": "R7a: predictive with temporal window — pattern_register required. No transit language so R7c transit ban does not apply; vector_search forbidden regardless (no domain document signal in a timing query)."
}
```

```json
{
  "id": "GT.044",
  "query": "Will my health improve after my Saturn mahadasha ends in 2027?",
  "query_class": "predictive",
  "category": "predictive",
  "expected_tools": ["msr_sql", "pattern_register"],
  "required_tools": ["msr_sql", "pattern_register"],
  "forbidden_tools": ["vector_search", "remedial_codex_query"],
  "required_asset_ids": ["FORENSIC", "CGM", "LEL"],
  "notes": "Mahadasha-end event + health domain + year-anchored → time_window encouraged but not required (year implicit, not explicit range). No remedial prescription asked — remedial_codex_query forbidden."
}
```

---

### GT.045: life-path R14a variant (1 entry)

```json
{
  "id": "GT.045",
  "query": "Give me an overview of the arc of my life across all major domains.",
  "query_class": "holistic",
  "category": "holistic",
  "expected_tools": ["msr_sql", "cgm_graph_walk", "cluster_atlas", "pattern_register"],
  "required_tools": ["msr_sql", "cgm_graph_walk"],
  "forbidden_tools": ["remedial_codex_query", "resonance_register"],
  "required_asset_ids": ["FORENSIC", "CGM", "UCN", "CDLM"],
  "notes": "R14a amended trigger: 'arc of my life' is a new trigger phrase added in QP-S1 for cgm_graph_walk. Variant of GT.017 ('Give me a comprehensive overview of my life path') using synonym phrasing to verify R14a trigger list breadth."
}
```

---

### GT.046: cross_native deferred stub (1 entry)

```json
{
  "id": "GT.046",
  "query": "[DEFERRED — M5] Compare my chart with my partner's chart for relationship compatibility.",
  "query_class": "cross_native",
  "category": "deferred",
  "expected_tools": [],
  "required_tools": [],
  "forbidden_tools": [],
  "required_asset_ids": [],
  "notes": "No native-2 data exists. Deferred to M5 per GAP-7. This entry holds the cross_native class slot to satisfy all-8-classes coverage in the header. Smoke runner skips entries with empty expected_tools via degenerate-entry guard."
}
```

---

### Header and category_distribution update

Update the file header:
```json
{
  "$schema_version": "1.2",
  "category_distribution": {
    "remedial": 6,
    "interpretive": 7,
    "predictive": 9,
    "holistic": 6,
    "planetary": 3,
    "edge_case": 5,
    "factual": 3,
    "discovery": 3,
    "cross_domain": 3,
    "deferred": 1
  }
}
```

Total entries after additions: **46** (29 original + 17 new).
Verify `interpretive` count is 7 — GT.042 is interpretive class, upgrading from 6.
Verify `predictive` count is 9 — GT.039/040/043/044 add 4 to the original 5.
Verify `holistic` count is 6 — GT.041/045 add 2 to the original 4.

---

## §4 — ACCEPTANCE CRITERIA (5 items)

- [ ] **AC-1** All 8 query classes now have ≥ 2 entries with non-empty `expected_tools[]` in the file (the deferred cross_native stub GT.046 is exempt by virtue of empty `expected_tools`).
- [ ] **AC-2** `time_window` requirement is captured via `required_plan_fields: ["time_window"]` on at least 2 entries (GT.039, GT.040).
- [ ] **AC-3** `graph_seed_hints` requirement is captured via `required_plan_fields: ["graph_seed_hints"]` on at least 2 entries (GT.041, GT.042).
- [ ] **AC-4** The file header `"$schema_version"` reads `"1.2"` and `category_distribution` sums to 46 entries matching the counts above.
- [ ] **AC-5** `JSON.parse(fs.readFileSync('planner_golden_set.json', 'utf-8'))` succeeds — file is valid JSON with no syntax errors. Verify with: `node -e "JSON.parse(require('fs').readFileSync('platform/tests/eval/planner_golden_set.json','utf-8')); console.log('valid')"`.

---

## §5 — MAY TOUCH / MUST NOT TOUCH

### may_touch
```
platform/tests/eval/planner_golden_set.json    (all edits go here)
CLAUDECODE_BRIEF.md                            (set status: COMPLETE at end)
```

### must_not_touch
```
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md         (QP-S1 owns this)
platform/tests/eval/planner_smoke_runner.ts    (runner is frozen)
platform/src/**                                (source code FROZEN for this session)
platform/tests/eval/eval_results_*.json        (QP-S4 creates eval output)
00_ARCHITECTURE/CURRENT_STATE_v1_0.md          (QP-S4 owns governance)
00_ARCHITECTURE/SESSION_LOG.md                 (QP-S4 owns governance)
```

---

## §6 — KNOWN OUT-OF-SCOPE

1. **Eval run** — QP-S4 runs the full eval after QP-S1 + QP-S3 are merged.
2. **Smoke runner changes** — if the runner needs extending to support `required_plan_fields`,
   that is out of scope for QP-S3. QP-S3 adds the extension field to the JSON entries; the
   runner extension can be done in QP-S4 if needed.
3. **Planner prompt edits** — QP-S1 owns the rules. QP-S3's entries assume QP-S1's rules
   are in place; they will show as failures until QP-S1 is merged.
4. **Code cleanup** — QP-S2 owns StreamingAnswer.tsx, useChatSession.ts, route.ts.
5. **Governance close** — SESSION_LOG + CURRENT_STATE are QP-S4's responsibility.

---

## §7 — COMPLETION SEQUENCE

When all 5 ACs are PASS:

1. Set `status: COMPLETE` in this file's frontmatter.
2. Commit:
   ```bash
   git add platform/tests/eval/planner_golden_set.json CLAUDECODE_BRIEF.md
   git commit -m "test(eval): expand golden set v1.1→v1.2 — GT.030-GT.046

   +17 entries across 4 previously-uncovered query classes:
   - GT.030-032: factual class (R-FACT validation)
   - GT.033-035: discovery class (R-DISC validation)
   - GT.036-038: cross_domain class (R-CDOM validation)
   - GT.039-040: time_window field population (R-TW1, R-TW2)
   - GT.041-042: graph_seed_hints field population (R-GSH)
   - GT.043-044: predictive edge cases
   - GT.045: life-path R14a variant (cgm_graph_walk trigger)
   - GT.046: cross_native deferred stub (M5 placeholder)
   Total: 46 entries. schema_version 1.2."
   git push -u origin fix/golden-set-qp-s3
   ```
3. Notify: session QP-S3 COMPLETE on branch `fix/golden-set-qp-s3`.

---

*CLAUDECODE_BRIEF_QP_S3.md · Pipeline Gap Plan QP-S3 · 2026-05-11*
*5 acceptance criteria: 17 new golden entries → planner_golden_set.json v1.2*
*Parallel with: QP-S1 (planner prompt), QP-S2 (code cleanup)*
