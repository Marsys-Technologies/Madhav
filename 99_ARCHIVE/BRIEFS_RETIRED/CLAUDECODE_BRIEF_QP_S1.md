---
artifact: CLAUDECODE_BRIEF_QP_S1.md
status: PENDING
session_id: QP-S1
phase: Pipeline Gap Closure — Planner Prompt (v2.0.1 → v2.1)
executor: claude-opus-4-6 (anti-gravity VS Code)
run_from_worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-gap
branch: fix/planner-gap-qp-s1
authored_by: Cowork (Abhisek session 2026-05-11)
authored_on: 2026-05-11
acceptance_criteria_count: 5
parallel_safe: true
parallel_siblings: QP-S2 (fix/cleanup-qp-s2), QP-S3 (fix/golden-set-qp-s3)
depends_on: Pipeline-Transform-S1 merged to main (commit 85dfca5)
master_plan: 00_ARCHITECTURE/PIPELINE_GAP_PLAN_v1_0.md §4/QP-S1
---

# QP-S1 — Planner Prompt Gap Closure

## §0 — HOW TO READ THIS BRIEF

**Run from the worktree:** `/Users/Dev/Vibe-Coding/Apps/Madhav-gap`
(branch `fix/planner-gap-qp-s1`).

**One file only.** This session touches exactly one file:
`00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`. Everything else is out of scope.

When all 5 ACs are GREEN, commit, push, and set `status: COMPLETE` in this
file's frontmatter. Do not emit SESSION_OPEN or SESSION_CLOSE artifacts.

---

## §1 — CONTEXT AND PROBLEM

Pipeline-Transform-S1 (PR #15, commit 85dfca5) replaced the dual
`classify()+callLlmPlanner()` architecture with a single
`callPipelinePlanner()` that emits a `PipelinePlan` containing
`asset_bundle[]`, `tool_calls[]`, `synthesis_guidance`, **`time_window`**,
and **`graph_seed_hints`**.

The new planner prompt (`PLANNER_PROMPT_v2_0.md` at v2.0.1) reaches
recall=0.963 / precision=0.986 on the existing 29-entry golden set.
However the post-merge commit analysis exposed **6 semantic gaps**:

| Gap | Problem | Root cause |
|-----|---------|-----------|
| GAP-1 | `time_window` never populated for eclipse queries | `099937e` fix was in deleted `router/prompt.ts`, never ported |
| GAP-2 | `time_window` never populated for named antardasha + date range | Same — `099937e`, never ported |
| GAP-3 | `graph_seed_hints` never populated for karaka/yoga architectural queries | `884b99c` fix in deleted file, never ported |
| GAP-4 | `discovery` class: only 2 sentences of definition, no tool-selection rule | New class added in v2.0 but under-specified |
| GAP-5 | `cross_domain` class: no explicit tool-selection rule | Same |
| GAP-6 | `factual` class: no explicit tool-selection rule | Same |
| GAP-6b | GT.017 recall residual: life-path holistic misses `cgm_graph_walk` | R14a trigger list too narrow |

**Schema status:** `time_window` and `graph_seed_hints` both exist in
`PipelinePlan` (types.ts). The contract is complete; the prompt-level
behavioral specification is missing.

---

## §2 — MANDATORY READING BEFORE WRITING ANYTHING

```
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md       ← THE ONLY FILE TO EDIT
00_ARCHITECTURE/PIPELINE_GAP_PLAN_v1_0.md §4/QP-S1  ← Full work spec
platform/src/lib/pipeline/types.ts           ← PipelinePlan schema (read-only)
platform/tests/eval/planner_golden_set.json  ← Golden set (read-only — QP-S3 owns edits)
```

Do NOT touch any other file.

---

## §3 — WORK TO DO (8 items)

For every edit, state the hypothesis: **"This edit enables/fixes [behaviour]
by [mechanism]."** If you cannot state this, do not make the edit.

### 3A. R-TW1 — time_window for eclipse queries (closes GAP-1)

Add a new rule in the TOOL_CALLS HARD RULES section (after R16, before the
Style rules block):

```
R-TW1. ECLIPSE TEMPORAL SCOPE: For PREDICTIVE queries that contain the
word "eclipse" (solar or lunar), populate `time_window` with the window
that brackets the queried eclipse event:
  - If the query states explicit dates or a month/year, use those as
    start/end (ISO 8601: "YYYY-MM-DD").
  - If no dates are stated, default window: start=today, end=today+90 days.
Set `planets: ["Moon"]` for lunar eclipse queries; `planets: ["Sun","Moon"]`
for solar. Set `forward_looking: true`. Apply R7c transit ban — tools are
`msr_sql` + `pattern_register` only.
Hypothesis: restores F016 eclipse temporal scoping lost from commit 099937e.
```

### 3B. R-TW2 — time_window for named antardasha + date range (closes GAP-2)

Add immediately after R-TW1:

```
R-TW2. ANTARDASHA TEMPORAL SCOPE: For PREDICTIVE queries that name a
specific antardasha period AND state a date range or year span (e.g.
"Mercury antardasha from 2025 to 2027", "my Ketu antardasha 2027–2034"),
populate `time_window: { "start": "<start-year>-01-01", "end": "<end-year>-12-31" }`
using the stated years. Set `dasha_context_required: true`. When no
explicit dates are stated but the named period is resolvable from the
native's known dasha schedule, still populate time_window with the
resolved window.
Hypothesis: restores F019 named-antardasha date-range scoping lost from
commit 099937e.
```

### 3C. R-GSH — graph_seed_hints for karaka/yoga/dasha-lord architectural queries (closes GAP-3)

Add immediately after R-TW2:

```
R-GSH. GRAPH SEED HINTS: For HOLISTIC or INTERPRETIVE queries that
explicitly reference one or more of:
  (a) karakas by name (Atmakaraka, Amatyakaraka, AK, AmK, Darakaraka, etc.)
  (b) named yogas (Lakshmi Yoga, Sasha Yoga, Gajakesari, Hamsa, Ruchaka,
      Malavya, Bhadra, Shasha — any named yoga formation)
  (c) dasha lords in an architectural/mapping context ("my Mercury
      mahadasha lord", "the current dasha lord's role")
populate `graph_seed_hints` with the relevant node IDs:
  - Karakas → "KRK.C8.AK", "KRK.C8.AmK", "KRK.C8.DK", etc.
  - Yogas → "YOG.LAKSHMI", "YOG.SASHA", "YOG.GAJAKESARI", etc.
  - Dasha lords → "DSH.MD.MERCURY", "DSH.MD.KETU", etc.
Do NOT populate graph_seed_hints for queries that do not name specific
karaka, yoga, or dasha-lord nodes.
Hypothesis: restores F022/F024 holistic graph-seed-hint pattern lost from
commit 884b99c.
```

### 3D. R-DISC — discovery class tool-selection rule (closes GAP-4)

In the QUERY CLASS RULES section, replace the current 2-sentence discovery
definition with a full tool-selection rule:

```
"discovery" — open-ended exploration: "what's interesting", "what stands
              out", "surprise me", "what's notable", "what haven't I asked
              about". No specific domain or planet focus.
              TOOL RULE (R-DISC): always produce all four L2.5 discovery
              registers as a set:
                pattern_register      (priority 1)
                contradiction_register (priority 1)
                resonance_register    (priority 2)
                cluster_atlas         (priority 2)
              Add msr_sql at priority 3 ONLY when the discovery query
              explicitly names a domain. Do NOT add cgm_graph_walk or
              vector_search to discovery queries.
              ASSET BUNDLE: FORENSIC + CGM (floors) + UCN (priority 2) +
              CDLM (priority 2).
```

### 3E. R-CDOM — cross_domain class tool-selection rule (closes GAP-5)

In the QUERY CLASS RULES section, expand the cross_domain definition:

```
"cross_domain" — multi-domain analysis with a defined scope (not
                 open-ended). E.g. "how does my Mars affect both career
                 and relationships".
                 TOOL RULE (R-CDOM): default set is msr_sql (priority 1)
                 + vector_search (priority 1, one call per named domain
                 with domain-specific query_text). Add cgm_graph_walk at
                 priority 2 when the query contains explicit domain-
                 interaction language: "how does X affect Y", "interaction
                 between", "relationship between X and Y domains",
                 "connected", "how X and Y interact". Do NOT add
                 cluster_atlas or resonance_register unless the query
                 explicitly triggers R11 or R15.
                 ASSET BUNDLE: FORENSIC + CGM (floors) + UCN (priority 2)
                 + CDLM (priority 2, cross-domain linkage surface).
```

### 3F. R-FACT — factual class tool-selection rule (closes GAP-6)

In the QUERY CLASS RULES section, expand the factual definition:

```
"factual" — single factual lookup ("what is my lagna", "which house is
            Saturn in"). One or two tools. No synthesis_guidance.
            TOOL RULE (R-FACT): use exactly ONE tool:
              - msr_sql for chart-position lookups (house, planet, degree,
                dignity, aspect counts)
              - remedial_codex_query for codex-lookup factual questions
                ("what gemstone does the codex prescribe for Venus")
            NEVER add vector_search, pattern_register, cgm_graph_walk,
            cluster_atlas, or any register to a factual query.
            expected_output_shape: "single_answer". Omit synthesis_guidance.
            ASSET BUNDLE: FORENSIC + CGM floors only.
```

### 3G. R14a amendment — GT.017 life-path holistic (closes GAP-6b)

In rule R14a, extend the trigger phrase list. Current text ends with
"domain interaction (R20)". Append:

```
Also include cgm_graph_walk for holistic queries containing life-path
language: "life path", "life arc", "arc of my life", "overall life
direction", "life trajectory", "how my life has unfolded", "life-wide
synthesis". These phrases signal a request for cross-domain structural
linkage, not just signal-level synthesis.
Hypothesis: enables cgm_graph_walk on GT.017-style life-path holistic
queries (recall 0.75 → expected 1.0 after this amendment).
```

### 3H. Version bump + §4 few-shot additions

1. **Frontmatter**: change `version: 2.0.1` → `version: 2.1`, update
   `patched_on:` to 2026-05-11, add a `gap_closure_patch:` block listing
   the 7 changes (R-TW1, R-TW2, R-GSH, R-DISC, R-CDOM, R-FACT, R14a).

2. **§4 few-shots**: add six new examples numbered **4.12–4.17** after
   the existing eleven (4.11 is the last current example). Each must
   contain a complete `expected_plan` with `asset_bundle[]`, `tool_calls[]`,
   `synthesis_guidance`, and the relevant new fields where applicable.

   **4.12 — Eclipse predictive** (`time_window` + `planets: ["Moon"]`):
   ```json
   {
     "user_query": "Will there be any lunar eclipses affecting me in the next 3 months?",
     "expected_plan": {
       "query_class": "predictive",
       "query_intent_summary": "Predictive scan for lunar eclipse impact over next 90 days.",
       "asset_bundle": [
         { "asset_id": "FORENSIC", "priority": 1, "reason": "Floor: chart facts for Moon placement and eclipse sensitivity." },
         { "asset_id": "CGM",      "priority": 1, "reason": "Floor: structural Moon connectivity." },
         { "asset_id": "LEL",      "priority": 1, "reason": "R26: LEL for eclipse-event ground-truth calibration." }
       ],
       "tool_calls": [
         {
           "tool_name": "msr_sql",
           "params": { "planets": ["Moon"], "forward_looking": true },
           "token_budget": 800, "priority": 1,
           "reason": "Pull Moon signals for eclipse sensitivity assessment."
         },
         {
           "tool_name": "pattern_register",
           "params": { "planets": ["Moon"], "forward_looking": true },
           "token_budget": 400, "priority": 2,
           "reason": "R7a: recurring Moon patterns for eclipse-period projection."
         }
       ],
       "synthesis_guidance": "Ground the eclipse impact in Moon's natal placement and current dasha. Flag the orb window and whether the eclipse falls on a sensitive degree. Cite confidence caveat.",
       "time_window": { "start": "2026-05-11", "end": "2026-08-11" },
       "planets": ["Moon"],
       "forward_looking": true,
       "expected_output_shape": "time_indexed_prediction"
     }
   }
   ```

   **4.13 — Named antardasha + date range** (`time_window` + `dasha_context_required`):
   ```json
   {
     "user_query": "What can I expect during my Mercury antardasha from 2025 to 2027?",
     "expected_plan": {
       "query_class": "predictive",
       "query_intent_summary": "Forward projection for Mercury antardasha 2025–2027.",
       "asset_bundle": [
         { "asset_id": "FORENSIC", "priority": 1, "reason": "Floor: natal Mercury placement and dignity." },
         { "asset_id": "CGM",      "priority": 1, "reason": "Floor: Mercury structural connectivity." },
         { "asset_id": "LEL",      "priority": 1, "reason": "R26: life event log for Mercury-period calibration." }
       ],
       "tool_calls": [
         {
           "tool_name": "msr_sql",
           "params": { "planets": ["Mercury"], "forward_looking": true },
           "token_budget": 900, "priority": 1,
           "reason": "Pull Mercury-domain signals for antardasha projection."
         },
         {
           "tool_name": "pattern_register",
           "params": { "planets": ["Mercury"], "forward_looking": true },
           "token_budget": 400, "priority": 2,
           "reason": "R7a: recurring Mercury patterns for antardasha period arc."
         }
       ],
       "synthesis_guidance": "Project the Mercury antardasha arc 2025–2027. Ground in LEL Mercury-period events. Lead with the dominant domain Mercury will activate. Cite dasha sub-period boundaries.",
       "time_window": { "start": "2025-01-01", "end": "2027-12-31" },
       "planets": ["Mercury"],
       "forward_looking": true,
       "dasha_context_required": true,
       "expected_output_shape": "time_indexed_prediction"
     }
   }
   ```

   **4.14 — Holistic karaka/yoga architectural** (`graph_seed_hints`):
   ```json
   {
     "user_query": "Map out the architectural role of my Atmakaraka and Amatyakaraka across all major yogas.",
     "expected_plan": {
       "query_class": "holistic",
       "query_intent_summary": "Karaka architectural mapping: AK/AmK role across active yogas.",
       "asset_bundle": [
         { "asset_id": "FORENSIC", "priority": 1, "reason": "Floor: chart facts for karaka identification." },
         { "asset_id": "CGM",      "priority": 1, "reason": "Floor: structural map for karaka-yoga connectivity." },
         { "asset_id": "CDLM",     "priority": 1, "reason": "R24: cross-domain linkage primary holistic surface." },
         { "asset_id": "UCN",      "priority": 2, "reason": "R23: interpretive synthesis for karaka domain expression." }
       ],
       "tool_calls": [
         {
           "tool_name": "msr_sql",
           "params": { "limit": 15 },
           "token_budget": 900, "priority": 1,
           "reason": "Pull signals for AK and AmK across all domains."
         },
         {
           "tool_name": "cgm_graph_walk",
           "params": { "graph_traversal_depth": 2 },
           "token_budget": 600, "priority": 1,
           "reason": "R-GSH: karaka architectural query — walk from KRK seed nodes."
         },
         {
           "tool_name": "pattern_register",
           "params": {},
           "token_budget": 400, "priority": 2,
           "reason": "Named yoga patterns (Lakshmi, Sasha, etc.) for AK/AmK role."
         },
         {
           "tool_name": "cluster_atlas",
           "params": {},
           "token_budget": 700, "priority": 2,
           "reason": "R11: cluster surface for holistic karaka-yoga architecture."
         }
       ],
       "synthesis_guidance": "Map AK and AmK as the primary and secondary soul-drivers. Show how each karaka's placement shapes the dominant yogas. Connect to 2–3 specific life domains. One structural arc, not a list.",
       "graph_seed_hints": ["KRK.C8.AK", "KRK.C8.AmK", "YOG.LAKSHMI", "YOG.SASHA"],
       "expected_output_shape": "three_interpretation"
     }
   }
   ```

   **4.15 — Discovery class** (all four L2.5 registers):
   ```json
   {
     "user_query": "What's the most interesting or unusual thing about my chart?",
     "expected_plan": {
       "query_class": "discovery",
       "query_intent_summary": "Open-ended exploration for unusual or salient chart patterns.",
       "asset_bundle": [
         { "asset_id": "FORENSIC", "priority": 1, "reason": "Floor: chart facts for pattern discovery." },
         { "asset_id": "CGM",      "priority": 1, "reason": "Floor: structural topology for unusual configuration detection." },
         { "asset_id": "UCN",      "priority": 2, "reason": "R-DISC: discovery interpretive synthesis layer." },
         { "asset_id": "CDLM",     "priority": 2, "reason": "R-DISC: cross-domain linkage for unusual cross-system patterns." }
       ],
       "tool_calls": [
         {
           "tool_name": "pattern_register",
           "params": {},
           "token_budget": 500, "priority": 1,
           "reason": "R-DISC: named cross-domain patterns — primary discovery surface."
         },
         {
           "tool_name": "contradiction_register",
           "params": {},
           "token_budget": 400, "priority": 1,
           "reason": "R-DISC: contradictions reveal unusual chart tensions."
         },
         {
           "tool_name": "resonance_register",
           "params": {},
           "token_budget": 400, "priority": 2,
           "reason": "R-DISC: cross-system resonances for unusual alignment patterns."
         },
         {
           "tool_name": "cluster_atlas",
           "params": {},
           "token_budget": 700, "priority": 2,
           "reason": "R-DISC: cluster surface for dominant unusual patterns."
         }
       ],
       "synthesis_guidance": "Lead with the single most unusual or surprising cross-domain pattern. Explain why it is unusual — what norm it breaks or what paradox it creates. No exhaustive listing.",
       "expected_output_shape": "single_answer"
     }
   }
   ```

   **4.16 — Cross_domain class** (two named domains, interaction language):
   ```json
   {
     "user_query": "How does my Mars affect both my career and my relationships?",
     "expected_plan": {
       "query_class": "cross_domain",
       "query_intent_summary": "Mars influence across career and relationships domains.",
       "asset_bundle": [
         { "asset_id": "FORENSIC", "priority": 1, "reason": "Floor: Mars placement and dignity facts." },
         { "asset_id": "CGM",      "priority": 1, "reason": "Floor: Mars structural connectivity across domains." },
         { "asset_id": "UCN",      "priority": 2, "reason": "R23: interpretive synthesis for multi-domain Mars reading." },
         { "asset_id": "CDLM",     "priority": 2, "reason": "R24: cross-domain linkage for career-relationship interaction." }
       ],
       "tool_calls": [
         {
           "tool_name": "msr_sql",
           "params": { "planets": ["Mars"], "domains": ["career", "relationships"] },
           "token_budget": 900, "priority": 1,
           "reason": "Pull Mars signals across both named domains."
         },
         {
           "tool_name": "vector_search",
           "params": { "query_text": "Mars career domain influence", "doc_type": ["domain_report"], "top_k": 5 },
           "token_budget": 500, "priority": 1,
           "reason": "L3 career domain narrative for Mars cross-domain reading."
         },
         {
           "tool_name": "vector_search",
           "params": { "query_text": "Mars relationships domain influence", "doc_type": ["domain_report"], "top_k": 5 },
           "token_budget": 500, "priority": 1,
           "reason": "L3 relationships domain narrative for Mars cross-domain reading."
         }
       ],
       "synthesis_guidance": "Show how Mars expresses differently in career vs relationships. Identify the common thread (the Mars signature) and the domain-specific manifestation in each. Cross-reference D1 and D10 for career, D1 and D9 for relationships.",
       "planets": ["Mars"],
       "domains": ["career", "relationships"],
       "expected_output_shape": "three_interpretation"
     }
   }
   ```

   **4.17 — Factual class** (single tool, no synthesis_guidance):
   ```json
   {
     "user_query": "Which house is Jupiter placed in?",
     "expected_plan": {
       "query_class": "factual",
       "query_intent_summary": "Single chart-position lookup: Jupiter's house placement.",
       "asset_bundle": [
         { "asset_id": "FORENSIC", "priority": 1, "reason": "Floor: chart facts for Jupiter house lookup." },
         { "asset_id": "CGM",      "priority": 1, "reason": "Floor: structural context for Jupiter placement." }
       ],
       "tool_calls": [
         {
           "tool_name": "msr_sql",
           "params": { "planets": ["Jupiter"] },
           "token_budget": 200, "priority": 1,
           "reason": "R-FACT: single chart-position lookup — one msr_sql call only."
         }
       ],
       "expected_output_shape": "single_answer"
     }
   }
   ```

---

## §4 — ACCEPTANCE CRITERIA (5 items)

- [ ] **AC-1** All seven changes (R-TW1, R-TW2, R-GSH, R-DISC, R-CDOM, R-FACT, R14a amendment) are present in the §3 system prompt verbatim body, each with an explicit `Hypothesis:` line.
- [ ] **AC-2** The §2 output schema block (the `interface PipelinePlan` section) is NOT modified — no new fields, no type changes.
- [ ] **AC-3** Rules R1–R20 and R21–R26 governing categories with passing golden entries are not altered except: R14a trigger list extension (additive only) and the discovery/cross_domain/factual QUERY CLASS RULES expansions (which replace the existing stub definitions, not the rule engine).
- [ ] **AC-4** YAML frontmatter `version:` reads `2.1` and `gap_closure_patch:` block lists all 7 changes.
- [ ] **AC-5** Six new few-shot examples (4.12–4.17) are present in §4, each with a complete `expected_plan` containing `asset_bundle[]`, `tool_calls[]`, and all relevant new fields (`time_window`, `graph_seed_hints` where applicable). The existing 11 examples (4.1–4.11) are not modified.

---

## §5 — MAY TOUCH / MUST NOT TOUCH

### may_touch
```
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md    (all edits go here)
CLAUDECODE_BRIEF.md                        (set status: COMPLETE at end)
```

### must_not_touch
```
platform/src/**                            (source code FROZEN for this session)
platform/tests/eval/planner_golden_set.json   (QP-S3 owns this)
platform/tests/eval/planner_smoke_runner.ts   (do not touch)
platform/src/lib/pipeline/types.ts            (schema frozen)
00_ARCHITECTURE/CURRENT_STATE_v1_0.md         (QP-S4 owns governance)
00_ARCHITECTURE/SESSION_LOG.md                (QP-S4 owns governance)
```

---

## §6 — KNOWN OUT-OF-SCOPE

1. **Eval run** — QP-S4 runs the eval after QP-S1 + QP-S3 are merged.
2. **Golden set edits** — QP-S3 owns `planner_golden_set.json`.
3. **Code cleanup** — QP-S2 owns StreamingAnswer.tsx, useChatSession.ts, route.ts.
4. **cross_native class** — No native-2 data exists; deferred to M5.
5. **Governance close** — SESSION_LOG + CURRENT_STATE updates are QP-S4's responsibility.

---

## §7 — COMPLETION SEQUENCE

When all 5 ACs are PASS:

1. Set `status: COMPLETE` in this file's frontmatter.
2. Commit:
   ```bash
   git add 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md CLAUDECODE_BRIEF.md
   git commit -m "fix(planner): close GAP-1..6b — PLANNER_PROMPT v2.1

   R-TW1: eclipse time_window population (restores F016 from 099937e)
   R-TW2: antardasha date-range time_window (restores F019 from 099937e)
   R-GSH: graph_seed_hints for karaka/yoga/dasha-lord queries (restores F022/F024 from 884b99c)
   R-DISC: discovery class full tool-selection rule (4 L2.5 registers)
   R-CDOM: cross_domain class tool-selection rule
   R-FACT: factual class tool-selection rule (single tool, no synthesis_guidance)
   R14a: extended trigger list for life-path holistic cgm_graph_walk (GT.017 fix)
   6 new few-shots added (4.12-4.17)"
   git push -u origin fix/planner-gap-qp-s1
   ```
3. Notify: session QP-S1 COMPLETE on branch `fix/planner-gap-qp-s1`.

---

*CLAUDECODE_BRIEF_QP_S1.md · Pipeline Gap Plan QP-S1 · 2026-05-11*
*5 acceptance criteria: 7 prompt rules + 6 few-shots → PLANNER_PROMPT v2.1*
*Parallel with: QP-S2 (cleanup), QP-S3 (golden set)*
