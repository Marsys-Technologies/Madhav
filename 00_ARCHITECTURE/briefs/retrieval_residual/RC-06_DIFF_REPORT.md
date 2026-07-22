---
artifact: RC-06_DIFF_REPORT.md
residual: RC-06 (golden set) — planner_golden_set.json recalibration
brief: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E Cluster 2
branch: res/rc06-golden-set
base: main @ a81f4cd6 (includes RC-05 dead-tool sweep — PLANNER_PROMPT_v2_0.md v2.9)
status: COMPLETE — regression gate PASSING
date: 2026-07-22
---

# RC-06 — `planner_golden_set.json` Recalibration — Diff Report

## Summary

`platform/tests/eval/planner_golden_set.json` and its mirror
`platform/tests/eval/fixtures/regression_baseline.json` contained gold test
cases that mandated three dead-capability tool names as
`expected_tools`/`required_tools` — `pattern_register`, `resonance_register`,
`cluster_atlas` — none of which resolve through `getToolByName()`
(`tool_name_bridge.ts`, WP-1.7 finding, reconfirmed by RC-05). A golden case
requiring a dead tool encodes an assertion no real planner can ever satisfy;
the regression gate was silently testing against a stale/impossible target.

**43 of 86 golden entries changed.** Every changed case was read individually
— query text, `query_class`, and the governing `PLANNER_PROMPT_v2_0.md` v2.9
rule (R7a/R7b/R7c/R7d/R11/R15/R17/R-DISC) — and recalibrated per the RC-05
substitution doctrine: substitute `vector_search` where the entry's own
`forbidden_tools` list (or its governing rule) doesn't separately ban it;
drop with no substitute where it does. This is the same live/dead-tool split
RC-05 established at the prompt level; RC-06 propagates it into the test
fixtures RC-05 didn't touch.

Additionally:
- `available_tools` (the golden set's own primary-tool catalog) had the 3
  dead names removed: `19 → 16` tools.
- `fixtures/regression_baseline.json`'s `mock_tool_calls` were resynced to
  match each changed entry's new `expected_tools` (the test file's own
  docstring: "the baseline mirrors each golden-set entry's `expected_tools`"),
  preserving the tool's original `token_budget`/`priority` where the
  surviving tool was already present.
- `forbidden_tools` references to dead tools (found in 19 additional
  factual/cross_domain/classical_grounding-class entries — GT.030-032,
  GT.037-038, GT.047, GT.058-061, GT.066-067, GT.069, GT.072, GT.074-075,
  GT.078, GT.083-084) were **left unchanged, deliberately**. The golden
  set's own `field_notes.forbidden_tools` documents this as by design:
  *"May reference non-primary names — those are inert under a planner
  restricted to primary tools, but preserved for documentation."* Forbidding
  a now-unresolvable tool is harmless and was already the pattern used for
  other non-primary conceptual names in this file (`temporal`,
  `domain_report_query`, `timeline_query`). Rewriting these would fabricate
  new test assertions outside RC-06's mandate (removing dead-tool
  *requirements*, not auditing every forbid-list). One entry, **GT.003**, is
  the exception — see below, where a forbidden_tools change was forced by a
  direct new conflict with a promoted-to-required substitute.

## Test results

```
$ npx vitest run tests/eval/planner_regression_gate.test.ts
 ✓ tests/eval/planner_regression_gate.test.ts > planner regression gate (mocked) > baseline covers every planner_golden_set entry by id
 ✓ tests/eval/planner_regression_gate.test.ts > planner regression gate (mocked) > avg_tool_recall ≥ 0.80 and avg_tool_precision ≥ 0.90
 Test Files  1 passed (1)
      Tests  2 passed (2)

$ npx vitest run tests/eval/
 Test Files  4 passed (4)
      Tests  73 passed (73)
```

Aggregate scores recomputed against the recalibrated set (mirrors what the
gate itself computes internally):

| metric | value | threshold |
|---|---|---|
| avg_tool_recall | 0.997 | ≥ 0.80 |
| avg_tool_precision | 0.996 | ≥ 0.90 |

(Not 1.000 — two pre-existing, deliberately-preserved imperfect-score
fixtures remain: GT.065's baseline mock intentionally omits one tool to
exercise the recall<1.0 path, and GT.086's baseline mock has an extra tool
to exercise the precision<1.0 path. Both predate RC-06 and are untouched by
it, except that GT.065's own dead-tool entry was still fixed in
`expected_tools`, as documented in its row below.)

Zero dead-capability references remain in `expected_tools`/`required_tools`
anywhere in the file, verified programmatically:

```python
dead = {'pattern_register','resonance_register','cluster_atlas'}
# 0 hits across all 86 entries' expected_tools/required_tools
# 0 hits across all 86 baseline mock_tool_calls tool_name fields
```

## Substitution rules applied (per PLANNER_PROMPT_v2_0.md v2.9 / VERIFY_RC-05.md)

| Governing rule | Query context | Dead tool(s) | Resolution |
|---|---|---|---|
| R7a | predictive (general) | pattern_register | → `vector_search` |
| R7b | remedial (all) | pattern_register, resonance_register | → `vector_search` (unconditional) |
| R7c | predictive + literal transit keyword | pattern_register | → `vector_search` (one of only 2 tools R7c allows) |
| R7d | interpretive, single-planet scope | pattern_register, resonance_register | DROP, no substitute (`vector_search` banned) |
| R11 main branch | holistic, comprehensive/overview | cluster_atlas | → `vector_search`; pattern_register DROP (already excised in W6.3) |
| R11 signal-density exception | holistic, "currently lit/ripening" | pattern_register | DROP, no substitute (`vector_search` banned) |
| R15 | holistic/interpretive, literal "themes"/"resonance"/"alignment" keyword | resonance_register | → `vector_search` (folds with R11 into one call where both fire) |
| R17 | interpretive, chart-level multi-layer scope (yogas/Lagna/divisionals) | pattern_register | → `vector_search` |
| R-DISC | discovery (all) | pattern_register, resonance_register, cluster_atlas | DROP, no substitute — `contradiction_register` is the sole surviving live L2.5 discovery register |
| (per-entry `forbidden_tools`) | any class where the entry itself already bans `vector_search` | pattern_register | DROP, no substitute — used as the operative "does this rule ban the substitute" signal for cases (mostly pure-timing/state predictive queries) where the entry's own author had already forbidden `vector_search` for domain reasons independent of R7c's literal-keyword trigger |

## Full per-case diff

| id | query_class | old expected_tools | new expected_tools | old required_tools | new required_tools | forbidden_tools delta |
|---|---|---|---|---|---|---|
| GT.001 | remedial | remedial_codex_query, msr_sql, vector_search, resonance_register | remedial_codex_query, msr_sql, vector_search | remedial_codex_query, resonance_register | remedial_codex_query, vector_search | — |
| GT.002 | remedial | remedial_codex_query, msr_sql, vector_search, resonance_register | remedial_codex_query, msr_sql, vector_search | remedial_codex_query, resonance_register | remedial_codex_query, vector_search | — |
| GT.003 | remedial | remedial_codex_query, msr_sql, resonance_register | remedial_codex_query, msr_sql, vector_search | remedial_codex_query, msr_sql, resonance_register | remedial_codex_query, msr_sql, vector_search | `[vector_search, domain_report_query]` → `[domain_report_query]` |
| GT.004 | remedial | remedial_codex_query, msr_sql, resonance_register | remedial_codex_query, msr_sql, vector_search | remedial_codex_query, msr_sql, resonance_register | remedial_codex_query, msr_sql, vector_search | — |
| GT.005 | remedial | remedial_codex_query, msr_sql, pattern_register | remedial_codex_query, msr_sql, vector_search | remedial_codex_query, msr_sql, pattern_register | remedial_codex_query, msr_sql, vector_search | — |
| GT.006 | remedial | remedial_codex_query, msr_sql, vector_search, resonance_register | remedial_codex_query, msr_sql, vector_search | remedial_codex_query, vector_search, resonance_register | remedial_codex_query, vector_search | — |
| GT.008 | interpretive | msr_sql, vector_search, pattern_register | msr_sql, vector_search | msr_sql | msr_sql | — |
| GT.009 | interpretive | pattern_register, msr_sql | vector_search, msr_sql | pattern_register | vector_search | — |
| GT.013 | predictive | vector_search, msr_sql, pattern_register | vector_search, msr_sql | vector_search, msr_sql, pattern_register | vector_search, msr_sql | — |
| GT.014 | predictive | msr_sql, pattern_register | msr_sql, vector_search | msr_sql, pattern_register | msr_sql, vector_search | — |
| GT.015 | predictive | msr_sql, pattern_register, vector_search | msr_sql, vector_search | msr_sql, pattern_register | msr_sql, vector_search | — |
| GT.016 | predictive | msr_sql, pattern_register, vector_search | msr_sql, vector_search | msr_sql, pattern_register | msr_sql, vector_search | — |
| GT.017 | holistic | cluster_atlas, vector_search, pattern_register, cgm_graph_walk | vector_search, cgm_graph_walk | cluster_atlas, vector_search | vector_search | — |
| GT.018 | holistic | pattern_register, contradiction_register, resonance_register, cluster_atlas | contradiction_register, vector_search | contradiction_register, pattern_register | contradiction_register, vector_search | — |
| GT.019 | holistic | cgm_graph_walk, vector_search, cluster_atlas, msr_sql | cgm_graph_walk, vector_search, msr_sql | cgm_graph_walk, vector_search | cgm_graph_walk, vector_search | — |
| GT.020 | holistic | msr_sql, pattern_register | msr_sql | msr_sql | msr_sql | — |
| GT.021 | interpretive | msr_sql, pattern_register, cgm_graph_walk | msr_sql, cgm_graph_walk | msr_sql | msr_sql | — |
| GT.022 | interpretive | msr_sql, pattern_register | msr_sql | msr_sql | msr_sql | — |
| GT.023 | interpretive | pattern_register, resonance_register, msr_sql | msr_sql | pattern_register | msr_sql | — |
| GT.024 | interpretive | pattern_register, cluster_atlas | contradiction_register | (none) | (none) | — |
| GT.025 | holistic | pattern_register, contradiction_register, resonance_register, cluster_atlas | contradiction_register | (none) | contradiction_register | — |
| GT.026 | predictive | msr_sql, pattern_register, vector_search | msr_sql, vector_search | msr_sql, pattern_register | msr_sql, vector_search | — |
| GT.029 | holistic | msr_sql, pattern_register, cluster_atlas, cgm_graph_walk, vector_search | msr_sql, cgm_graph_walk, vector_search | (none) | (none) | — |
| GT.033 | discovery | pattern_register, contradiction_register, resonance_register, cluster_atlas | contradiction_register | pattern_register, contradiction_register | contradiction_register | — |
| GT.034 | discovery | pattern_register, contradiction_register, resonance_register, cluster_atlas | contradiction_register | pattern_register, cluster_atlas | contradiction_register | — |
| GT.035 | discovery | pattern_register, contradiction_register, resonance_register, cluster_atlas, msr_sql | contradiction_register, msr_sql | pattern_register, msr_sql | contradiction_register, msr_sql | — |
| GT.039 | predictive | msr_sql, pattern_register | msr_sql | msr_sql, pattern_register | msr_sql | — |
| GT.040 | predictive | msr_sql, pattern_register | msr_sql | msr_sql, pattern_register | msr_sql | — |
| GT.041 | holistic | msr_sql, cgm_graph_walk, cluster_atlas, pattern_register | msr_sql, cgm_graph_walk, vector_search | msr_sql, cgm_graph_walk | msr_sql, cgm_graph_walk | — |
| GT.042 | interpretive | msr_sql, pattern_register, cgm_graph_walk | msr_sql, vector_search, cgm_graph_walk | msr_sql, pattern_register | msr_sql, vector_search | — |
| GT.043 | predictive | msr_sql, pattern_register | msr_sql | msr_sql, pattern_register | msr_sql | — |
| GT.044 | predictive | msr_sql, pattern_register | msr_sql | msr_sql, pattern_register | msr_sql | — |
| GT.045 | holistic | msr_sql, cgm_graph_walk, cluster_atlas, pattern_register | msr_sql, cgm_graph_walk, vector_search | msr_sql, cgm_graph_walk | msr_sql, cgm_graph_walk | — |
| GT.053 | predictive | lel_query, msr_sql, pattern_register, cgm_graph_walk | lel_query, msr_sql, cgm_graph_walk | lel_query, msr_sql | lel_query, msr_sql | — |
| GT.054 | predictive | temporal, lel_query, msr_sql, pattern_register | temporal, lel_query, msr_sql | temporal, lel_query, msr_sql | temporal, lel_query, msr_sql | — |
| GT.055 | predictive | lel_query, msr_sql, resonance_register, cgm_graph_walk | lel_query, msr_sql, vector_search, cgm_graph_walk | lel_query, msr_sql, resonance_register | lel_query, msr_sql, vector_search | — |
| GT.056 | predictive | query_signal_state, msr_sql, pattern_register | query_signal_state, msr_sql, vector_search | query_signal_state | query_signal_state | — |
| GT.057 | predictive | query_signal_state, temporal, msr_sql, pattern_register | query_signal_state, temporal, msr_sql | query_signal_state, temporal | query_signal_state, temporal | — |
| GT.062 | predictive | query_varshaphala, msr_sql, pattern_register, lel_query | query_varshaphala, msr_sql, lel_query | query_varshaphala, msr_sql | query_varshaphala, msr_sql | — |
| GT.063 | predictive | query_varshaphala, msr_sql, pattern_register, resonance_register | query_varshaphala, msr_sql, vector_search | query_varshaphala, msr_sql | query_varshaphala, msr_sql | — |
| GT.064 | predictive | query_varshaphala, temporal, lel_query, msr_sql, pattern_register | query_varshaphala, temporal, lel_query, msr_sql | query_varshaphala, temporal, lel_query | query_varshaphala, temporal, lel_query | — |
| GT.065 | predictive | lel_query, msr_sql, query_ephemeris, pattern_register | lel_query, msr_sql, query_ephemeris, vector_search | lel_query, msr_sql, query_ephemeris | lel_query, msr_sql, query_ephemeris | — |
| GT.068 | predictive | msr_sql, query_ephemeris, pattern_register | msr_sql, query_ephemeris, vector_search | msr_sql, query_ephemeris, pattern_register | msr_sql, query_ephemeris, vector_search | — |

## Per-case rationale

### GT.001 — What gemstone should I wear to strengthen my career?
resonance_register was a dead capability (WP-1.7/tool_name_bridge.ts:417, RC-05 finding) — replaced with vector_search, R7b's unconditional live substitute for the remedial alignment lens.

### GT.002 — Which mantra should I recite to support spiritual progress?
resonance_register was a dead capability — replaced with vector_search per R7b's unconditional alignment-lens substitute.

### GT.003 — Should I wear a yellow sapphire?
resonance_register was a dead capability — replaced with vector_search. R7b now unconditionally mandates vector_search for every remedial query (not conditionally banned for structured single-stone lookups), which supersedes this entry's prior "vector_search forbidden — dilutes codex-grounded prescription" design; vector_search removed from forbidden_tools accordingly (domain_report_query remains forbidden — never a primary tool). **This is the one case where an existing forbidden_tools entry had to change**, because the substitute directly collided with a pre-existing forbid.

### GT.004 — What planetary remedies are recommended for my Mars?
resonance_register was a dead capability — replaced with vector_search per R7b's unconditional alignment-lens substitute.

### GT.005 — Recommend a daily ritual to strengthen my chart's weakest planet.
pattern_register was a dead capability. R7b's "pattern vs resonance lens" distinction no longer exists in the current rule (R7b unconditionally mandates vector_search for every remedial query regardless of framing) — replaced with vector_search.

### GT.006 — Are there fasting practices that would help my health?
resonance_register was a dead capability — replaced with vector_search per R7b's unconditional alignment-lens substitute (already present in expected_tools; deduplicated).

### GT.008 — Tell me about my Lagna and overall chart strength.
pattern_register was a dead capability. Lagna + overall chart strength is chart-level multi-layer scope under R17, whose vector_search mandate already covered this call — pattern_register dropped (deduplicated against the existing vector_search entry).

### GT.009 — What yogas are present in my chart?
pattern_register was a dead capability (the L2.5 named-yoga register). "Yogas" is a literal R17 chart-level-multi-layer-scope trigger — replaced with vector_search (R17's live substitute); msr_sql (signal_type=yoga) remains the structured confirmation surface per the original notes.

### GT.013 — What can I expect from the upcoming Ketu Mahadasha starting in 2027?
pattern_register was a dead capability — dropped (deduplicated against the existing required vector_search entry, R7a's live cross-domain-lens substitute).

### GT.014 — Where is Saturn transiting in my chart right now and what should I expect?
pattern_register was a dead capability. This is a literal R7c transit query ("transiting... right now") whose ABSOLUTE BAN allows only msr_sql + vector_search — replaced with vector_search accordingly.

### GT.015 — Will the next year bring career growth?
pattern_register was a dead capability — dropped (deduplicated against the existing vector_search entry); vector_search promoted to required as R7a's live cross-domain-lens substitute.

### GT.016 — When is my next favorable period for starting a new venture?
pattern_register was a dead capability — dropped (deduplicated against the existing vector_search entry); vector_search promoted to required as R7a's live cross-domain-lens substitute.

### GT.017 — Give me a comprehensive overview of my life path across all major domains.
cluster_atlas and pattern_register were dead capabilities. cluster_atlas → vector_search (R11 main-branch live substitute, already present in expected_tools; deduplicated). pattern_register dropped with no substitute — R11 excised it entirely in W6.3/v2.8 (no in-class substitute).

### GT.018 — What are the central themes and contradictions in my chart?
resonance_register and cluster_atlas were dead capabilities; pattern_register also dead. Query literally contains "themes" (R15 keyword trigger) and matches R11's own "themes and contradictions" example phrase — one vector_search call now covers both the R11 and R15 mandates, promoted to required. pattern_register dropped with no substitute (R11 excised it, no in-class substitute). contradiction_register remains required per R12 (explicit "contradictions").

### GT.019 — Synthesize how my career, marriage, and health interact in my chart.
cluster_atlas was a dead capability — dropped (deduplicated against the existing required vector_search entry, R11's live substitute).

### GT.020 — What signals are currently lit or ripening in my chart?
pattern_register was a dead capability — dropped with no substitute. This is R11's SIGNAL-DENSITY EXCEPTION branch ("currently lit or ripening"), which bans vector_search unconditionally (use ONLY msr_sql); no live substitute exists in this branch.

### GT.021 — Tell me everything about Jupiter in my chart.
pattern_register was a dead capability — dropped with no substitute. This is R7d's single-planet interpretive scope (Jupiter), which bans vector_search/cluster_atlas/resonance_register/contradiction_register unconditionally; no live substitute exists in this rule.

### GT.022 — What is Mars's role across my divisional charts?
pattern_register was a dead capability — dropped with no substitute. This query is R7d's own worked example (single-planet Mars scope across divisionals), which bans vector_search unconditionally.

### GT.023 — What patterns and resonances surface for Saturn in my chart?
pattern_register and resonance_register were dead capabilities — both dropped with no substitute. This is a single-planet (Saturn) query, so R7d governs despite the literal "patterns and resonances" phrasing — the R7d/R15 overlap resolves in R7d's favor (VERIFY_RC-05 non-blocking note 1), and R7d's prior "resonance_register on literal resonance/themes/alignment keyword" conditional clause was removed in RC-05 (moved to the permanent NEVER-add list); vector_search remains banned in R7d. msr_sql promoted to required — R7d's actual mandate is "the default tool set is msr_sql only", and leaving required_tools empty after dropping the sole required dead entry would make this case vacuously pass.

### GT.024 — Give me a high-level read of the chart.
pattern_register and cluster_atlas were dead capabilities. Despite the interpretive class label, the notes' own framing ("L2.5 discovery surfaces") matches R-DISC — replaced with contradiction_register, the sole live L2.5 discovery register post-RC-05 (vector_search is banned for discovery by the same rule).

### GT.025 — Tell me something interesting about the chart.
pattern_register, resonance_register, and cluster_atlas were dead capabilities. Replaced with contradiction_register, now the SOLE live L2.5 discovery register post-RC-05 (R-DISC dropped the other two with no substitute — vector_search is banned for discovery). Promoted to required: with only one live register left, the prior "any non-empty subset of the four is acceptable" framing collapses to "contradiction_register is the unconditional R-DISC mandate".

### GT.026 — According to my Vimshottari Dasha sequence, when does my Mercury period begin and what will it activate?
pattern_register was a dead capability — dropped (deduplicated against the existing vector_search entry); vector_search promoted to required as R7a's live cross-domain-lens substitute.

### GT.029 — Tell me everything about everything in my entire chart in full detail with all possible combinations and permutations and every possible interpretation
pattern_register and cluster_atlas were dead capabilities. cluster_atlas → vector_search (R11 main-branch live substitute, already present; deduplicated). pattern_register dropped with no substitute (R11 excised it). required_tools remains empty — budget arbitration may legitimately prune any single tool.

### GT.033 — What's the most interesting or unusual thing about my chart?
pattern_register, resonance_register, and cluster_atlas were dead capabilities. R-DISC dropped all three with no substitute (vector_search is explicitly banned for discovery) — contradiction_register is now the sole live L2.5 discovery register.

### GT.034 — Surprise me — what patterns in my chart haven't I asked about yet?
pattern_register, resonance_register, and cluster_atlas were dead capabilities. R-DISC dropped all three with no substitute (vector_search is explicitly banned for discovery) — contradiction_register is now the sole live L2.5 discovery register; msr_sql stays forbidden (no domain anchor).

### GT.035 — What stands out in my career domain that I might be overlooking?
pattern_register, resonance_register, and cluster_atlas were dead capabilities. R-DISC dropped all three with no substitute (vector_search is explicitly banned for discovery) — contradiction_register is now the sole live L2.5 discovery register; msr_sql remains required via the R-DISC domain-anchor exception ("career" named).

### GT.039 — Will there be any significant lunar eclipses affecting me in the next 3 months?
pattern_register was a dead capability — dropped with no substitute (this entry's own forbidden_tools already bans vector_search under the R7c transit-ban posture R-TW1 pairs with).

### GT.040 — What can I expect during my Mercury antardasha from 2025 to 2027?
pattern_register was a dead capability — dropped with no substitute (vector_search is forbidden in this entry).

### GT.041 — Map out the architectural role of my Atmakaraka and Amatyakaraka across all major yogas.
cluster_atlas and pattern_register were dead capabilities. cluster_atlas → vector_search (R11 main-branch live substitute; vector_search is not forbidden in this entry). pattern_register dropped with no substitute (R11 excised it entirely, no in-class substitute).

### GT.042 — How do Lakshmi Yoga and Sasha Yoga interact with my current Mercury mahadasha?
pattern_register was a dead capability. Named yogas + named dasha lord is chart-level multi-layer scope under R17 — replaced with vector_search, R17's live substitute.

### GT.043 — When is the most favorable window for career advancement in the next 2 years?
pattern_register was a dead capability — dropped with no substitute (vector_search is forbidden in this entry regardless of transit-keyword absence, per its own "no domain document signal in a timing query" rationale).

### GT.044 — Will my health improve after my Saturn mahadasha ends in 2027?
pattern_register was a dead capability — dropped with no substitute (vector_search is forbidden in this entry).

### GT.045 — Give me an overview of the arc of my life across all major domains.
cluster_atlas and pattern_register were dead capabilities. cluster_atlas → vector_search (R11 main-branch live substitute; vector_search is not forbidden in this entry). pattern_register dropped with no substitute (R11 excised it entirely).

### GT.053 — When did major shifts happen in my career?
pattern_register was a dead capability — dropped with no substitute (vector_search is forbidden in this entry — narrative L3 retrieval would dilute the LEL ground-truth anchor).

### GT.054 — What's the next major dasha transition I should watch for?
pattern_register was a dead capability — dropped with no substitute (vector_search is forbidden in this entry).

### GT.055 — Tell me about my marriage and family history from a chart perspective.
resonance_register was a dead capability — replaced with vector_search (R7's live cross-domain-lens substitute; not forbidden in this entry).

### GT.056 — What MSR signals are lit for me today?
pattern_register was a dead capability — replaced with vector_search (R7a's live cross-domain-lens substitute for predictive queries; not forbidden in this entry). Remains optional (not required).

### GT.057 — Which signals are ripening over the next 12 months?
pattern_register was a dead capability — dropped with no substitute (vector_search is forbidden in this entry — narrative retrieval would dilute a structured state-table scan).

### GT.062 — What does my 2026 Varshaphala say?
pattern_register was a dead capability — dropped with no substitute (vector_search is forbidden in this entry — Varshaphala is structured substrate, not narrative).

### GT.063 — Compare my annual charts from 2024 to 2028.
pattern_register and resonance_register were dead capabilities — both replaced by a single vector_search call (R7's live cross-domain-lens substitute; vector_search is not forbidden in this entry, only temporal is).

### GT.064 — What's coming up for me astrologically next year?
pattern_register was a dead capability — dropped with no substitute (vector_search is forbidden in this entry).

### GT.065 — What was Mars doing when I changed jobs in 2018?
pattern_register was a dead capability — replaced with vector_search (R7a's live cross-domain-lens substitute; not forbidden in this entry). Remains optional (not required) — the regression_baseline mock for this id intentionally omits the 4th tool to exercise the recall<1.0 scoring path; left unchanged, so this entry continues to score recall=0.75 in the mocked gate exactly as it did pre-RC-06.

### GT.068 — What's the current transit picture for my career?
pattern_register was a dead capability. Literal R7c transit query ("current transit picture") whose ABSOLUTE BAN allows only msr_sql + vector_search — replaced with vector_search, still required.

## `available_tools` metadata change

```diff
- "pattern_register",
- "resonance_register",
- "cluster_atlas",
```
removed from the 19-entry `available_tools` catalog (now 16). This field is
pure documentation inside the golden set (no test asserts
`expected_tools ⊆ available_tools`); the deprecated code-level
`PRIMARY_TOOL_NAMES` constant in `manifest_compressor.ts` is explicitly
marked "Retained for backward compatibility... do not add new tools here"
and was left untouched — out of RC-06's scope (golden-set data, not
platform source).

## Files changed

- `platform/tests/eval/planner_golden_set.json` (43 entries + `available_tools`)
- `platform/tests/eval/fixtures/regression_baseline.json` (42 entries — all
  except GT.065, whose mock was deliberately preserved unchanged)

## DONE bar (brief §E RC-06, verbatim) vs. what shipped

1. "zero dead-capability references remain in the golden set" — **MET** for
   `expected_tools`/`required_tools`/`available_tools` (the assertable,
   test-consumed surfaces). `forbidden_tools` references to dead names are
   retained by deliberate, documented design (see Summary) — this is a
   scoped judgment call, not an oversight; flagged here for the RC-16 sealer
   to ratify or override.
2. "the planner regression gate passes against the recalibrated set" — **MET**,
   verified live (see Test results above).
3. "a diff report explains every changed case" — **MET** (this document).
