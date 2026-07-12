# Lane 6 — Ranking-Quality Audit — Shard 6-b3

**Worker:** Lane 6 RANKED-SURFACE-QUALITY (Charter §7.4, RATIFIED + raw-metrics-always amendment)
**Chart:** Abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a`
**Channel:** DEPLOYED MCP connector (read-only) — `get_domain_reading`, `get_chart_orientation`
**Surfaces:** get_domain_reading:{health, character, spirituality, education}
**Date:** 2026-07-12

Ranked-surface unit under test = `question_lenses[].all_relevant_ranked_jsonb.ranked_signals`
(each lens serves a top-20 ranked list). K = 20 per lens. Pooled-K = 20 × lenses_returned.

---

## Cross-surface structural facts (apply to all 3 live surfaces)

- **Ranked rows carry NO text and NO grounding.** Every ranked row is exactly:
  `{salience, signal_id(UUID), in_template, source_l1_asset, signal_type_class, non_template_significant}`.
  No `grounding.fact_ids`, no `constituent_facts_array`, no narration. IDs-without-text →
  **class 6 UNUSABLE FORM** co-present with the class 7 DROWNED ranking defect.
- **Ranker self-flags approximation:** every lens `verification_pass_status = "documented_approximation"`.
- **Every lens is bounded to top-20 of a huge pool** (total_count 772 → 10505) and 70% of that
  20 sits on ONE salience plateau (see score-walls). `signal_id_refs_capped:true`, 200 returned
  of up to 7283 total.
- **token_safety_note is a fixed template** ("Bounded to 3 lenses × 20 signals") even when only
  2 lenses exist (health) — minor class-5 self-description drift.

### R-44a anchor RE-DERIVED BLIND (from embedded orientation digest, education call)
`entity_profiles[0]` = **`UNATTRIBUTED`**, aggregate_score **84.797**, signal_count **298**,
peak 0.788 — the #1 ranked ENTITY of the whole chart. Next entities: VENUS 1.046 (1 signal),
JUPITER 0.637 (1 signal). The unattributed bucket outranks the top real graha by **~81×**.
R-44a independently confirmed and worse than the 298/300 anchor.

---

## SURFACE 1 — get_domain_reading:health  (lenses: health, longevity)

Raw §7.4 metrics (per-lens K=20; pooled K=40):
- **duplication_rate = 0.500** — `longevity` lens ranking is BYTE-IDENTICAL to `health` lens
  (20/20 same signal_ids, same order). Two "different questions", one ranking.
- **identical_score_walls = 0.70** (14/20 per lens): salience `2.3 × 10 rows` + `2.76 × 4 rows`.
  Bottom half of the top-20 is a dead-flat 2.3 plateau; ranker cannot discriminate 10 rows.
- **descriptive_trivia_share = 1.00** (40/40 `composite_state` from `ga_structural`) — every
  top row is a basic structural placement-state, zero yoga/dosha/convergence. Classical-canon:
  raw composite placement states are descriptive, not chart-defining.
- **family_collapse_coverage ≈ 0.17** — 1 signal_type_class (composite_state) of ≥6 present in
  underlying data (composite_state, varga_pattern, karaka_alignment, tradition_specific, yoga,
  dosha); 1 source asset (ga_structural) of the full L1 set. Collapsed onto one family.
- **UNATTRIBUTED_share = 1.00** (0/40 rows carry resolvable fact_ids).
- **DROWNED (class 7): YES.** Rationale: 70% score-wall + 100% single-family trivia + a fully
  duplicated second lens + 100% unattributed simultaneously exceed any acharya tolerance —
  the top-20 conveys no rankable acharya priority.

Verbatim top rows (health lens):
```
{"salience":2.99,"signal_id":"a7b7703a-...","source_l1_asset":"ga_structural","signal_type_class":"composite_state"}
{"salience":2.76,"signal_id":"b94f4cd0-...","signal_type_class":"composite_state"}   (×4 tied at 2.76)
...rows 11–20 all salience 2.3, composite_state...
```

## SURFACE 2 — get_domain_reading:character  (lenses: character, education, siblings)

Raw §7.4 metrics (per-lens K=20; pooled K=60):
- **duplication_rate = 0.500** — `character` ≡ `siblings` IDENTICAL 20/20 order; `education`
  lens overlaps 10/20. 30 extra-copy rows / 60.
- **identical_score_walls = 0.70** (14/20 each lens; 2.3×10 + 2.76×4).
- **descriptive_trivia_share = 0.83** (50/60 composite_state; +8 varga_pattern, +2 karaka_alignment).
- **family_collapse_coverage ≈ 0.50** — 3 signal_type_classes of ~6; still 1 source asset (ga_structural).
- **UNATTRIBUTED_share = 1.00** (0/60).
- **DROWNED (class 7): YES** — same rationale; the marriage/siblings-vs-character distinction
  is erased (identical rankings).

## SURFACE 3 — get_domain_reading:spirituality  (lenses: education, foreign_travel, spirituality)

Raw §7.4 metrics (per-lens K=20; pooled K=60):
- **duplication_rate = 0.500** — `foreign_travel` ≡ `spirituality` IDENTICAL 20/20; `education`
  overlaps 10/20.
- **identical_score_walls = 0.70** (2.3×10 + 2.76×4 each lens).
- **descriptive_trivia_share = 0.97** (58/60 composite_state; +2 karaka_alignment).
- **family_collapse_coverage ≈ 0.33** — 2 signal_type_classes of ~6; 1 source asset.
- **UNATTRIBUTED_share = 1.00** (0/60).
- **DROWNED (class 7): YES.**

## SURFACE 4 — get_domain_reading:education  (EMPTY)

`get_domain_reading(domain="education")` → `lenses_total:0`, `question_lenses:[]`,
`note:"Domain 'education' not found. Available domains listed."`
`available_domains` = career, character, health, relationship, spirituality, wealth (education ABSENT).

BUT `education` IS a first-class **lens** inside both `character` and `spirituality` domains,
with `total_count = 10505` — the LARGEST signal pool of any lens observed. A chart-defining
topic with 10,505 rankable signals is UNREACHABLE via its own natural domain path; it is only
reachable as a side-lens of unrelated domains (character/spirituality).
- Raw metrics: N/A (empty surface, 0 rows).
- **drowned_verdict: N/A (empty)** — this is not a class-7 burial but a **class-1 UNREACHABLE**
  (capability alive under 10505-signal `education` lens, no domain route serves it). The honest
  "not found" note keeps it out of class-4/5 territory, but the routing gap is real.

---

## Findings summary (severity ranked)
1. UNATTRIBUTED_share = 1.00 on every live ranked surface (class 7 / co-class 6). R-44a re-derived: top entity = UNATTRIBUTED 84.8 vs Venus 1.05.
2. education domain UNREACHABLE despite 10505-signal education lens (class 1).
3. identical_score_walls 0.70 on every lens — 10-row 2.3 plateau (class 7).
4. duplication_rate 0.50 — lenses serve byte-identical rankings (health≡longevity, character≡siblings, foreign_travel≡spirituality) (class 7).
5. descriptive_trivia_share 0.83–1.00 — top-K is single-family ga_structural composite_state, no yoga/dosha (class 7).
6. Ranked rows are IDs-without-text — un-synthesizable form (class 6).
