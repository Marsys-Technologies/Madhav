---
artifact: CLAUDECODE_BRIEF_BG_RULES_v1_0
canonical_id: L0_BG_RULES_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
amended_by: Racayitā (Build-Guarantor gap-author) 2026-06-08 — added §3a yield-projection + HARD STOP (floor 3,000 emergent; reject-not-pad if pattern coverage underperforms); migration 188
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_rules writer (deterministic rule extraction)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 3000  # sutravali_rules rows
dependencies: [bg_texts, bg_ontology, bg_yogas, bg_dasha_systems]
llm_cost: $0  # v1.1 removed LLM-assisted extraction; pure-Python regex pattern library
document_number: 8 of 15
---

# bg_rules — Writer Brief (deterministic classical-rule extraction)

> **The extracted-rule base.** Each row is a templated classical statement mined from a `bg_texts` verse: an `antecedent` (the chart condition), a `predicate`/`prediction` (the stated result), the source verse, a quality score, and (where applicable) cross-references to a yoga or dasha system. Rules differ from yogas: a yoga is a NAMED pattern (`bg_yogas`); a rule is ANY extracted verse-statement (holistic design §2.3). ZERO LLM — v1.1 removed the LLM-assisted extraction the v1.0 design described; this is a pure-Python regex pattern library.

## §0 — Asset summary

- **Asset ID:** `bg_rules`. **Backing:** `sutravali_rules`. **Scope:** `global`. **Tier:** 3.
- **Target floor:** **≥3,000 rules** (design §3.6; the existing corpus has ~1,213 from prior work — this brief expands via pattern-library growth + the 10 newly-ingested texts).
- **Source category:** deterministic regex extraction over `classical_text_chunks`.

## §3a — Floor Achievement Arithmetic (Racayitā amendment; floor ≥3,000 — EMERGENT + HARD STOP)

| Bucket | What | Count | Provable from |
|---|---|---|---|
| `closed_set_inline` | the pattern library is INFRASTRUCTURE, not rows (the ~50 templates are the extractor, not data) | 0 (rows) | — |
| `deterministic_generated` | existing `sutravali_rules` from prior Stream-D extraction | **~1,213** | live table count |
| `structured_extraction` | NEW rules from the §3 pattern library (target ~50 templates) over the 15-text corpus (~14,000 chunks), quality-gated ≥0.6, deterministic rule_id | **≥1,800 projected** | yield ≈ (chunks 14,000 × avg matches/chunk ~0.25 × quality-pass ~0.55) ≈ 1,900; +10 new texts vs the 5 that yielded 1,213 |
| **TOTAL** | | **≥3,000 projected (EMERGENT)** | 1,213 + ≥1,800 ≈ ≥3,000 |

> **Yield is a PROJECTION, not a guarantee** (the floor depends on corpus completeness + pattern coverage). **HARD STOP (§8):** if live rules < 3,000 after the FULL corpus + the full ~50-pattern library, the writer REJECTs and emits the coverage report (chunks with zero extractions) — it does NOT loosen the ≥0.6 quality gate to pad. **CONDITIONAL** if the 3 manual-upload PDFs are absent (rerun after full corpus). The ~50 patterns must be authored to the §3 families (only ~12 are shown); reaching 3,000 with only ~12 patterns is NOT assumed. Migration **188** carries `depends_on`.


## §1 — Schema reference (migration 081 + 177, verified)

```
sutravali_rules (
  rule_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text_id            TEXT NOT NULL,
  verse_ref          TEXT NOT NULL,
  antecedent_jsonb   JSONB NOT NULL DEFAULT '[]',   -- [{planet, house|sign, relation}, ...]
  predicate_jsonb    JSONB NOT NULL DEFAULT '{}',
  prediction_jsonb   JSONB NOT NULL DEFAULT '{}',
  confidence         NUMERIC(4,3) NOT NULL DEFAULT 0,
  extracted_by       TEXT NOT NULL DEFAULT 'stream_d',  -- use 'python_regex_v2' (no llm_* values — v1.1)
  extraction_pass_log JSONB NOT NULL DEFAULT '[]',
  quality_score      NUMERIC(4,3),                  -- migration 177
  yoga_canonical_id  TEXT,                           -- migration 177; FK-by-convention → brahma_yoga_catalog
  dasha_system_id    TEXT,                           -- migration 177; → brahma_dasha_systems
  transit_marker     BOOLEAN,                        -- migration 177
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
```

Idempotency key: a deterministic `rule_id` derived from `(text_id, verse_ref, sha256(antecedent+prediction))` so re-extraction produces the SAME rule_id → `ON CONFLICT (rule_id) DO NOTHING`. (Do NOT rely on the random `gen_random_uuid()` default — compute the id in Python for determinism per design §4.5.)

## §2 — Source references

Rules are extracted from `bg_texts` chunks (all 15 texts). Each rule cites its `text_id` + `verse_ref` + `source_chunk_id` (store the chunk id in `extraction_pass_log` or add it to antecedent metadata). No external source.

## §3 — Embedded content — the pattern library (~50 templates)

Author `platform/python-sidecar/brahmagyan/l0_sutravali_extractor.py` (design §3.6: "currently missing"). The pattern library is an ordered list of `(name, compiled_regex, builder_fn)` where `builder_fn(match) -> (antecedent, predicate, prediction)`.

```python
# Pattern families (design §3.6). Each compiled against chunk.content_en with planet/house/sign
# name+synonym alternations sourced from bg_ontology. ~50 patterns:
PATTERN_FAMILIES = [
  # 1. Single placement: "<planet> in the <ord> house gives <result>"
  ("planet_in_house", r'\b(?P<planet>{PLANETS})\b.{0,30}\b(?P<house>{ORDINALS})\s+(?:house|bhava)\b.{0,60}?\b(?P<result>{RESULT_CLAUSE})',
   build_planet_house),
  # 2. Planet in sign: "<planet> in <sign> ..."
  ("planet_in_sign", r'\b(?P<planet>{PLANETS})\b.{0,20}\bin\b.{0,10}\b(?P<sign>{SIGNS})\b.{0,60}?(?P<result>{RESULT_CLAUSE})', build_planet_sign),
  # 3. Lord placement: "lord of the <ord> in the <ord>"
  ("lord_placement", r'\blord\b.{0,10}\b(?P<from>{ORDINALS})\b.{0,30}\b(?P<to>{ORDINALS})\b.{0,60}?(?P<result>{RESULT_CLAUSE})', build_lord),
  # 4. Conjunction: "<planet> with/conjunct <planet> ..."
  ("conjunction", r'\b(?P<p1>{PLANETS})\b.{0,15}\b(?:with|conjunct|joined by|and)\b.{0,10}\b(?P<p2>{PLANETS})\b.{0,60}?(?P<result>{RESULT_CLAUSE})', build_conjunction),
  # 5. Aspect: "<planet> aspecting/aspected by ..."
  ("aspect", r'\b(?P<p1>{PLANETS})\b.{0,15}\baspect(?:s|ing|ed by)\b.{0,30}?(?P<result>{RESULT_CLAUSE})', build_aspect),
  # 6. Parivartana (exchange): "lord of <ord> in <ord> and lord of <ord> in <ord>"
  ("parivartana", r'\blord of\b.{0,30}\bin\b.{0,30}\band lord of\b.{0,30}\bin\b', build_parivartana),
  # 7. Sanskrit placement: "<SA_planet> ... bhave/sthane/gata"
  ("sanskrit_placement", r'\b(?P<planet>{SA_PLANETS})\b.{0,20}\b(?:bhave|sthane|gata|sthita)\b', build_sanskrit),
  # 8. Yoga-cited rule: "when <YogaName> yoga forms ..." → sets yoga_canonical_id
  ("yoga_rule", r'\b(?P<yoga>{YOGA_NAMES})\s+yoga\b.{0,60}?(?P<result>{RESULT_CLAUSE})', build_yoga_rule),
  # 9. Dasha rule: "during <planet>'s (maha)dasha ..." → sets dasha_system_id, transit_marker handling
  ("dasha_rule", r'\bduring\b.{0,15}\b(?P<planet>{PLANETS})\b.{0,5}\b(?:maha)?dasha\b.{0,60}?(?P<result>{RESULT_CLAUSE})', build_dasha_rule),
  # 10. Transit rule: "when <planet> transits <target> ..." → transit_marker=True
  ("transit_rule", r'\bwhen\b.{0,10}\b(?P<planet>{PLANETS})\b.{0,10}\btransit', build_transit),
  # 11. Karaka rule: "<chara_karaka> in the <ord> ..."
  ("karaka_rule", r'\b(?P<karaka>{KARAKAS})\b.{0,15}\b(?P<house>{ORDINALS})\b.{0,60}?(?P<result>{RESULT_CLAUSE})', build_karaka),
  # 12. Conditional negation: "<placement>, unless aspected by <benefic>, gives ..."
  ("conditional_negation", r'(?P<cond>.{0,40}),?\s+unless\b.{0,30},\s+(?P<result>{RESULT_CLAUSE})', build_conditional),
  # ... continue to ~50 patterns covering compound antecedents, nakshatra placements,
  #     varga placements, strength conditions, house-from-house, etc. (design §3.6 lever 1).
]
# {PLANETS},{SIGNS},{ORDINALS},{SA_PLANETS},{YOGA_NAMES},{KARAKAS},{RESULT_CLAUSE} are
# alternation macros expanded from bg_ontology + bg_yogas at load time (NOT hardcoded).
```

## §4 — Writer implementation

`pipeline/orchestrator/writers/bg_rules.py` (`@register('bg_rules')`):

1. Build the alternation macros from `brahma_ontology` (planet/sign/karaka names+synonyms) + `brahma_yoga_catalog` (yoga names) + `brahma_dasha_systems`.
2. Stream all `classical_text_chunks` (text_id, verse_ref, content_en, id).
3. For each chunk, run every pattern; each match → `(antecedent, predicate, prediction)` via its `builder_fn`. A chunk can yield multiple rules.
4. **Quality score** (design §3.6 lever 5, deterministic): +1 each for (antecedent.planet ∈ ontology), (antecedent.house ∈ 1-12), (predicate non-empty noun), (verse_ref resolves in bg_texts), (prediction has a time/place/event marker). `quality_score = sum/5`. Rules scoring ≥0.6 (≥3/5) → `sutravali_rules` (live); 0.4-0.6 → `sutravali_review`; <0.4 → reject (log only).
5. Compute deterministic `rule_id` (§1). `ON CONFLICT (rule_id) DO NOTHING`. Set `extracted_by='python_regex_v2'`, `yoga_canonical_id`/`dasha_system_id`/`transit_marker` where the pattern produced them.
6. **Coverage report** (design §3.6 lever 4): emit a count of chunks with ZERO extractions → `extraction_pass_log` summary, so native/next-pass can add patterns. Do NOT use an LLM to fill the gap (v1.1).

## §5 — FK validation

- `yoga_canonical_id` (when non-null) MUST resolve in `brahma_yoga_catalog` → so **bg_rules depends_on bg_yogas**. Validate before insert; if absent, null the field + log (don't reject the whole rule).
- `dasha_system_id` (when non-null) MUST resolve in `brahma_dasha_systems` → **depends_on bg_dasha_systems**.
- antecedent planet/sign/karaka ids resolve in `brahma_ontology` → **depends_on bg_ontology**.
- chunk source resolves in `classical_text_chunks` → **depends_on bg_texts**.
- **depends_on:** `UPDATE asset_registry SET depends_on = ARRAY['bg_texts','bg_ontology','bg_yogas','bg_dasha_systems']::text[] WHERE asset_id='bg_rules';` (migration 179 didn't set this — this brief adds it).

## §6 — Unit tests

`test_bg_rules.py`: (1) ≥3,000 live rules; (2) every rule has non-empty `antecedent_jsonb` + `prediction_jsonb` + `verse_ref` + `quality_score`; (3) every non-null `yoga_canonical_id`/`dasha_system_id` resolves in its catalog; (4) a known BPHS Saturn-7th chunk yields a rule with antecedent `{planet:saturn, house:7}`; (5) re-extraction inserts 0 (deterministic rule_id); (6) `extracted_by` never contains `llm` (v1.1).

## §7 — Vimarśaka check

APPROVE iff: ≥3,000 live rules; all source-cited (text_id+verse_ref); quality_score present on all; FK fields resolve; deterministic re-run inserts 0; zero `llm`-derived rows. **If <3,000 because the corpus is incomplete** (manual PDFs missing → fewer chunks), CONDITIONAL with "rerun after full corpus". If <3,000 with the full corpus, the pattern library needs more families (design §3.6 lever 1) — REJECT with the coverage report; do NOT loosen quality gates to pad.

## §8 — Hard stops + scope discipline

- Tempted to lower the quality gate to hit 3,000 → STOP. The floor is met by more/better PATTERNS over the full corpus, never by admitting low-quality rules. Report the coverage gap.
- Do NOT use an LLM for extraction or gap-filling (v1.1 removed it; design v1.0 body's Gemini-Flash extraction is SUPERSEDED).
- Do NOT use the random uuid default for rule_id (breaks deterministic rebuild). Compute it.
- Out of scope: per-chart rule firing (L1), concordance (bg_concordance Doc 10).

---

*End of bg_rules brief (Document 8 of 15).*
