# LANE5 — Wire-fidelity rollup (FUSED 1b+5 pass)

```
resume:
  lane_id: LANE5
  fused_with: LANE1b (single pass, shared shard substrate)
  substrate: 00_ARCHITECTURE/llm_consumption_audit/state/FUSED_1b5/shard-*.md
  paths_total: 134
  paths_audited: 134
  families_total: 3058
  findings_5: 19
  status: DONE
  checkpoint_ts: 2026-07-12 (native chart audit session, wave 1)
```

## Scope

Lane 5 answers, for families that ARE reachable on the wire: **does the value a consumer
actually receives faithfully represent the stored value?** It diffs DB truth against the wire
payload across four fidelity failure modes. Where the only front is a dead tool, no wire value
exists to diff and the family is **untestable by construction** (logged, not a fidelity pass).

## The four fidelity failure modes — incidence

| mode | class | description | headline incidence |
|---|---|---|---|
| Silent filter no-op | 6 (field/param dropped) | filter/projection params accepted but not applied | `query_chart_facts` (fact_category, fact_subject); `msr_sql` (sql param) |
| Budget-ceiling silent drop | 7 (DROWNED) | hard cap discards rows with no total-available disclosure | `query_chart_facts` (1000-of-5566); `msr_sql` (50-of-13364) |
| Field-dropped-in-pivot | 6 | fixed projection drops populated columns | `msr_sql` (~83 of 115 columns dropped) |
| Dishonest self-description | 5 | payload reports `truncated=False` while truncating | `msr_sql` (50-of-13364, truncated=False) |
| Untestable-by-construction | 1 (UNREACHABLE) | only front is a dead tool; no wire value to diff | all CGM graph families (bodha_cgm_paths etc.) |

## HIGH fidelity findings (19 Lane-5 findings; load-bearing subset)

### query_chart_facts (chart_facts)
- **Silent filter no-op (class 6, HIGH):** `fact_category` and `fact_subject` params accepted
  but **not applied**. `POST query_chart_facts {chart_id, fact_category:'anumukha_shani_period'}`
  → returned_count:100 with categories `{esoteric_point_sphuta_fertility, yoga_label, dosha_label, ...}`
  and ZERO `anumukha_shani_period` rows. `fact_subject:'CYCLE_1.ANUMUKHA'` → 100 unrelated subjects.
  A consumer **cannot target a family and must dump** the whole table.
- **Budget-ceiling silent drop (class 7, HIGH):** hard-caps at **1000 of 5566** distinct pivoted
  subjects (~82% silently discarded) for lahiri_chitrapaksha, with **no total-available disclosure**.
  `limit=3000` → returned_count:1000 (hard cap). Default limit=100. No `total` / `more available`
  count in payload; a family is reachable only if its subject sorts within the first 1000 by alpha order.

### msr_sql (bodha_msr_signals) — heterogeneity-escalated table
- **Field-dropped-in-pivot (class 6, HIGH, CONFIRMED):** `msr_sql` delivers a **fixed 17-field
  projection and IGNORES its `sql` param**, silently dropping ~83 of 115 columns. Requesting
  `SELECT signal_id, shadbala_norm ...` returns ok:true but the standard 17 keys only — `shadbala_norm`
  absent, `dignity_score` absent, though DB has them populated. Dropped: shadbala_norm, dignity_score,
  deterministic_strength, all salience component modifiers, remedy_hooks_array,
  contradicts_signals_array, active_dasha_periods_jsonb, activation_predicted_dates_jsonb,
  predicted_outcome_class, fact_kind, epistemic_tier, signature_class, ...
- **Dishonest self-description + budget-ceiling drop (class 5+7, HIGH, CONFIRMED):** returns
  **top-50 of 13,364 matching signals** (66,836 total DB rows for chart 482012f1) but reports
  **truncated=False**. 13,314 matching rows discarded silently. Top-50 shows an identical-salience
  wall at 2.99 with duplicate `graha_dignity_per_varga` headlines — decisive rows drowned.

### Untestable-by-construction (class 1) — direct confirmation of the native concern
- **bodha_cgm_paths** — DB holds 45 dispositor-chain path rows/chart but **no surgical wire path
  returns them**; the only front `get_cgm_subgraph` 500s (dead `cgm_graph_walk`). No wire value
  exists to diff, so **all four Lane-5 fidelity modes are untestable by construction**. This is the
  direct confirmation of the native's "data exists but is not retrieved" concern: the fidelity
  question cannot even be posed because the retrieval plane is dead. (Mirrors every CGM graph
  family — nodes/edges/motifs/sub_graphs/topology.)

## Cross-lane note

Lane-5 fidelity is only *testable* on families Lane-1b classifies **reachable-surgical**. The
large `served-only-by-down-pipeline` and `truly-UNREACHABLE` populations (see LANE1b.md) are
fidelity-untestable by construction — a retrieval-plane gap must be repaired before fidelity can
be assessed. Thus the two most damaging fidelity defects (`query_chart_facts` silent filter no-op,
`msr_sql` param-ignore + dishonest truncation) sit on the *reachable* families — the ones a
consumer trusts most — which is where fidelity failure does the most harm.

## Verifier coverage note

All findings DB-truth-grounded (read-only `mcp__postgres__query`) and wire-probed
(`curl POST /api/mcp/primitives/...`); the two CONFIRMED msr_sql findings carry verbatim
tool-envelope capture. Per-family fidelity verdicts and exemplar evidence live in
`FUSED_1b5/shard-*.md`.
