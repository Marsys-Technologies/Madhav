# Lane 6 — RANKED-SURFACE-QUALITY shard-6-b1

Charter §7.4 (RATIFIED, raw-metrics-always amendment). Read-only deployed MCP connector.
Tool: `get_domain_reading`. Chart requested (all calls): `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek).
top-K = 20 (matches connector's own `token_safety_note` bound: 3 lenses × 20 signals).
Surfaces: health, character, spirituality, education.

Ranked surface = `question_lenses[*].all_relevant_ranked_jsonb.ranked_signals`.
Row schema (ALL rows, ALL lenses): `{salience, signal_id, in_template, source_l1_asset, signal_type_class, non_template_significant}`.
NO `grounding.fact_ids`, NO derivation ledger, NO description text on any ranked row — only an opaque `signal_id` UUID handle.

---

## HEADLINE — DOMAIN-INVARIANT RANKED HEAD (class 7 DROWNED, confirmed)

The IDENTICAL top-8 `signal_id`s head EVERY lens across health / longevity / character / education / siblings / foreign_travel / spirituality:
```
09471d69, cd8ea294, 3aff17b5, b46dc8f5, d17891e1, b68927dd, 43118e69, 7babaa81
```
(only cd8ea294↔3aff17b5 positions 2/3 swap in some lenses; set is identical.)

Cross-lens identical-position overlap vs health baseline (top-20):
- health:health = 20/20 · health:longevity = **20/20** (the two health lenses are the SAME list)
- character:character 8/20 · character:siblings 8/20 · character:education 6/20
- spirituality:spirituality 7/20 (set overlap **19/20**) · foreign_travel 7/20 (set 19/20)

Every lens returns the SAME salience spine:
`[2.99, 2.645, 2.645, 2.5415, 2.415, 2.415, 2.3805, 2.346, 2.3×12]`

A "health reading" and a "spirituality reading" lead with the same 8 signals. The domain-specific
signal is DROWNED by a domain-invariant global salience head. VERDICT: class 7 DROWNED — YES for
health, character, spirituality.

---

## RAW METRICS (top-K=20, per surface)

### health  (chart returned: 482012f1 on recall — SEE WRONG-CHART FINDING)
lenses: health, longevity (both 20/20 identical to each other)
1. duplication_rate (intra-lens dup signal_ids): **0/20 = 0.0%**. Cross-lens: top-8 = 100% shared with all other domains.
2. identical_score_walls (≥3 co-tied): **1 wall of 12/20 rows @ salience 2.3 (60% of top-K)**. (2.645×2, 2.415×2 are sub-threshold.) distinct salience values in top-20 = 7.
3. descriptive_trivia_share: signal_type_class = {composite_state: 20}. No raw graha-in-house placement class present → **0% by class-label**, but UNVERIFIABLE (no content text exposed; caveat inline).
4. family_collapse_coverage: source_l1_asset = {ga_structural: 20} = **1 of 9 L1 assets**; signal_type_class families = **1 (composite_state only)**. Graha/yoga identity NOT exposed on rows → graha-family coverage uncomputable (itself a finding).
5. UNATTRIBUTED_share: **20/20 = 100%** — zero rows carry grounding.fact_ids/derivation ledger (only signal_id handle). R-44a anchor confirmed at this surface.
drowned_verdict: **DROWNED (class 7) = YES**.

### character  (chart 482012f1 correct)
lenses: character, education, siblings
1. duplication_rate: 0/20 = 0.0% intra-lens.
2. identical_score_walls: 1 wall of 12/20 @ 2.3 (each lens). distinct sal=7.
3. descriptive_trivia_share: class mix {composite_state 15-18, varga_pattern 2, karaka_alignment 5} → 0% raw-placement trivia by label (unverifiable caveat).
4. family_collapse_coverage: source_l1_asset {ga_structural:20} = 1/9; signal_type_class families = 2-3 of many.
5. UNATTRIBUTED_share: 60/60 = **100%** across the 3 lenses.
drowned_verdict: **DROWNED = YES** (top-8 identical to health).

### spirituality  (chart 482012f1 correct)
lenses: education, foreign_travel, spirituality
1. duplication_rate: 0/20 = 0.0% intra-lens.
2. identical_score_walls: 1 wall of 12/20 @ 2.3 (each lens). distinct sal=7.
3. descriptive_trivia_share: {composite_state 15-20, karaka_alignment up to 5} → 0% by label (caveat).
4. family_collapse_coverage: {ga_structural:20} = 1/9; classes 1-2.
5. UNATTRIBUTED_share: **100%**.
drowned_verdict: **DROWNED = YES** (set overlap 19/20 with health baseline).

### education  — SURFACE DOES NOT EXIST
`get_domain_reading(domain=education)` returns: `note: "Domain 'education' not found. Available domains listed."`, `lenses_total=0, lenses_returned=0`.
available_domains = [career, character, health, relationship, spirituality, wealth]. (Note: an *education* question_type DOES exist internally — it appears as a lens inside the character & spirituality domains — but there is no education *domain*. Taxonomy mismatch.)
All five metrics: N/A (empty surface). drowned_verdict: N/A.

---

## WRONG-CHART CONTAMINATION (nondeterministic, severe)

FIRST `get_domain_reading(chart_id=482012f1, domain=health)` call returned `chart_id = 1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan Mohanty — a DIFFERENT native), with its own provenance (`defect_001` derived live for 1c826d5a). Immediate re-calls returned the correct 482012f1. Intermittent wrong-native contamination on the deployed connector. Two subsequent recalls = correct chart. Reproduced once, non-deterministic. Severity: high (serves another person's chart under the requested id).

---

## RECEIPT-HONESTY (capping IS disclosed — good)

- `signal_id_refs_capped=True`; totals: health 752→200 returned, character 7290, spirituality 3338.
- `token_safety_note`: "Bounded to 3 lenses × 20 signals..."
- `provenance.bounding_note`: "signal_id_refs capped at 200 of 752 total".
- `lenses_total`/`lenses_returned` present. Trimming is honestly reported — no silent truncation.
- `provenance.defect_001`: DEFECT-001 MOSTLY_RESOLVED, 845/67508 (1.3%) constituent_facts orphaned — BUT derived for chart 1c826d5a, NOT the requested Abhisek chart (stale/cross-chart provenance on the first health payload).

## Notes on §7.4 tolerance judgments (no silent thresholds)
- identical_score_walls threshold = 3+ co-tied (charter). The 2.3 wall covers 12/20 = 60% of top-K; this is well past any reasonable tolerance — a majority of the "chart-defining" surface is a flat tie carrying no rank information.
- UNATTRIBUTED counted at the SURFACE (what the LLM consumer receives): 100%, because no fact_ids ship on rows. signal_id is a resolvable handle via query_signals, but resolution is a SECOND round-trip the consumer must make — the ranked surface itself grounds nothing. Reported blind per R-44a.
- descriptive_trivia_share reported as 0%-by-label but flagged UNVERIFIABLE: the surface exposes no human-readable content, so whether composite_state rows are genuinely chart-defining or dressed-up trivia cannot be adjudicated from this surface.
