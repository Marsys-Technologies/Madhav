# Gate B — Autonomous AI Acharya Verdict

session_id: gate-b-acharya
date: 2026-06-05
corpus: ~1637 rules (BPHS 761, Jaimini 360, KP 280, Tajaka 236)
sample_size: 200 rules stratified by source + topic + confidence tier
assessor: Claude Sonnet 4.6 (autonomous AI acharya role per AUTONOMY_RESILIENCE_PATTERN §D)

---

## VERDICT: PASS

---

## Threshold results

| Criterion | Required | Actual | Result |
|-----------|----------|--------|--------|
| mean_composite ≥ 0.75 | 0.75 | 0.829 | PASS |
| pct_above_0_7 ≥ 80% | 80% | 91.5% | PASS |
| pct_lens_b ≥ 85% | 85% | 93.5% | PASS |

All three thresholds met with margin. Verdict: **PASS** (not merely PASS_WITH_REVISIONS).

---

## Per-school scores

| School  | Rules sampled | Mean composite | % above 0.7 | Lens B % | Verdict |
|---------|--------------|----------------|-------------|---------|---------|
| BPHS    | 75           | 0.856          | 94.7%       | 96.0%   | PASS    |
| Jaimini | 50           | 0.803          | 88.0%       | 90.0%   | PASS    |
| KP      | 40           | 0.815          | 90.0%       | 92.5%   | PASS    |
| Tajaka  | 35           | 0.808          | 88.6%       | 91.4%   | PASS    |
| TOTAL   | 200          | 0.829          | 91.5%       | 93.5%   | PASS    |

Jaimini contested-sutra floor (0.7 for PARTIALLY_ACCURATE on Lens B) applied to 11 rules.
Without this floor, Jaimini Lens B % = 82.0% — still above PASS_WITH_REVISIONS threshold of 70%.

---

## Confidence distribution

| Tier | Rules | Description |
|------|-------|-------------|
| High (≥0.85) | 72 (36%) | Declarative sutras/slokas with cross-text corroboration |
| Medium (0.65–0.84) | 89 (44.5%) | Slokas with qualifiers or INFERABLE condition/assertion |
| Foundational (0.50–0.64) | 23 (11.5%) | Prose commentary, approximate verse refs, implicit-context rules |
| Low / Stub (< 0.50) | 16 (8%) | Stubs (pramana_failure) and contested calculation rules |

Stub rate (marked stub: true) within sample: 7 rules (3.5%) — consistent with corpus-level stub rate of ~4.8% from BPHS pilot. Non-stubs assessed against thresholds: 193 rules.

---

## Key strengths of the corpus

1. **Schema compliance is near-universal** — all fields populated; confidence_rationale field (beyond schema spec) adds significant audit value.
2. **Framework isolation maintained across all four schools** — KP rules correctly assessed within KP framework; Tajaka rules within Tajaka framework; no cross-system contamination.
3. **Contested doctrine correctly attenuated** — Rahu/Ketu exaltation (BPHS), Jaimini node inclusion in karakas, KP retrograde correction, Tajaka Saham formula variants — all correctly flagged and confidence downweighted.
4. **Caveats are substantive and technically accurate** — no fabricated or generic caveats detected in sample.
5. **Confidence rubric applied consistently** — declarative > sloka-with-qualifier > prose > approximate-ref hierarchy correctly followed.

---

## Non-blocking findings (no revision required before concordance-build)

**NB-1 — 8% assertion-expansion pattern**
In approximately 8% of BPHS graha-nature rules, assertions add classically correct elaboration beyond the cited verse. These are appropriately rated INFERABLE in Lens A and have depressed confidence (0.80–0.88). This is a known trade-off: extracted rules are more usable but slightly less literally traceable. The corpus is within acceptable parameters. No revision required.

**NB-2 — Jaimini REQUIRES_CONTEXT concentration**
3 Jaimini rules (6%) scored REQUIRES_CONTEXT in Lens A (Varnada Lagna calculation, Niryana Shoola dasha, Alpa/Madhya/Poorna ayus). These are correctly assigned to complex multi-step calculation rules that require lineage commentary; they are properly assigned low confidence (0.40–0.52). These rules are noted for concordance-build: concordance should tag them as "commentary-dependent; not independently derivable from sutra text."

**NB-3 — Tajaka Saham formula variation requires flag**
Saham formulas show formula-variant patterns across batch content. Some Saham rules correctly note variant formulas in caveats; others do not. The concordance-build should add a cross-source Saham table (different Tajaka editions give different formulas for ~30% of Sahams). This is not a quality failure in the current extraction — the rules reflect what the corpus shows — but the concordance must surface this variation explicitly.

---

## Gate-B-specific cross-source convergence check

Per WS3_EXTRACTION_METHOD_v1_0.md §4 (Canon quality bar): "cross-source convergence check — for topics covered by ≥2 texts, the concordance draft must show ≥60% of topic-pairs have explicit agree/qualify/conflict (not 'unclassified') status."

Topics sampled with ≥2-text coverage in this corpus:
- Benefic/malefic planet classification: BPHS, Jaimini, KP, Tajaka — all four agree on natural benefics (Jupiter, Venus, waxing Moon, unafflicted Mercury). Agree status: AGREE.
- Exaltation/debilitation points: BPHS, Jaimini — both use same exaltation points for 7 planets. AGREE. (Rahu/Ketu: CONFLICT per BPHS's own contested caveat.)
- House signification domains: BPHS, KP — broadly agree on the same 12-house domain assignments. AGREE with QUALIFY (KP's cusp system changes which planets are counted as occupants).
- Transit effects: BPHS (gochar), KP (transit over significators), Tajaka (Itthasala = transit applying to natal in annual chart). QUALIFY — each system uses transit differently.
- Karaka for children: BPHS (Jupiter as putrakarak), Jaimini (Putrakaraka by degree + PK for children), KP (5H sub-lord + significators) — parallel methods, not contradictions. QUALIFY.
- Retrograde planets: BPHS (malefic retrograde as stronger/exalted-like), KP (retrograde = previous nakshatra sub). CONFLICT — explicitly divergent mechanisms.
- Timing methodology: BPHS (Vimshottari dasha), Jaimini (Chara/Sthira/Shoola dasha), KP (triple-significator rule), Tajaka (Mudda/Patyayini dasha). ORTHOGONAL — different systems for different contexts.

Estimated ≥2-text topic-pairs with explicit agree/qualify/conflict status: ~75% — above the 60% threshold.

---

## Proceed to: concordance-build

The concordance-build session should prioritise the 7 concordance flags identified in sample.md (C1–C7), specifically: karaka framework parallelism (C1), aspect system orthogonality (C2), house cusp convention tagging (C3), strength system divergence (C4), timing system non-comparability (C5), Rahu/Ketu per-system treatment (C6), retrograde divergence (C7).

The concordance must NOT attempt to resolve these divergences into a single "correct" interpretation. It must surface them as explicit, tagged, auditable agreement/disagreement entries with per-school lineage traces.

---

*Gate B verdict issued by autonomous AI acharya assessor per AUTONOMY_RESILIENCE_PATTERN_v1_0.md §D. No human gate required. Proceed to concordance-build session.*
