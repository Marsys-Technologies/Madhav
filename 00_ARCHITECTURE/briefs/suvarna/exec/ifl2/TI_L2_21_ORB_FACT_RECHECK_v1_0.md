---
version: 1.0
status: CURRENT
lane: TI-i-fl2-004
item: TI-L2-21 (Q-L2-03 orb check, "re-check at execution")
branch: suvarna/land/TI-i-fl2-004
basis: origin/main adb0db29d; production DB read 2026-10-03, reader-only SELECT, chart 482012f1
changelog:
  - 1.0 -- re-check of which L1 aspect facts carry an orb. The brief's premise ("no orb fact was found for aspects") is incomplete: the Tajika aspect facts do. Evidence only.
---

# TI-L2-21: which aspect-class L1 facts carry an orb, and what L2 stores for them

SS ruling Q-L2-03 (N-59, TI-L2-21): "L1 stores `orb_deg` for conjunctions only (`conjunction_per_varga`,
`conjunction_within_orb`); no orb fact was found for aspects, so for aspect-class signals store None
and record this one Track I item (an L1 orb fact for aspects); **re-check at execution**." This is
the re-check.

## Answer

**The premise is partly wrong.** L1 *does* store an orb for one aspect family: the Tajika aspects.
`chart_facts.fact_category = 'aspect_tajik'` (ithasala / eesarpha / manaau) carries
`fact_value_jsonb = {"orb_deg": ..., "orb_strength": ..., "applying": ..., "deeptamsa_sum_deg": ..., "salience": ..., "house_diff": ...}`.
It is **not** true for the Parashari, Jaimini, virupa-drishti, special-point or lord-aspect families,
which store no orb. So TI-L2-27 / TI-L2-21 should not read as "no orb fact exists for aspects":
for the Tajika family the L1 fact exists and L2 ignores it.

## What was measured (canonical chart, production, 2026-10-03)

L1 aspect-class categories, whether the fact carries an orb, and the L2 signals that cite it
(`bodha_msr_signals.constituent_facts_array` joined to `chart_facts.fact_id`):

| L1 `fact_category` | facts | carries orb | L2 signals citing it | stored `orb_tightness` |
|---|---|---|---|---|
| `aspect_tajik` | 20 | **yes** (`orb_deg`, `orb_strength`) | 20 | 1.0 on all 20 |
| `conjunction_per_varga` | 549 | **yes** (`orb_deg` in `fact_value_num`, 0.000 to 9.385, mean 0.121) | 292 | 1.0 |
| `conjunction_within_orb` | 10 | **yes** (`orb_deg`) | 10 | 1.0 |
| `aspect_parashari_given` / `_received` / `_per_varga` | 95 / 95 / 2,850 | no | 95 / 45 / 150 | 1.0 |
| `aspect_jaimini` / `_per_varga` | 540 / 16,200 | no | 60 / 150 | 1.0 |
| `virupa_drishti` | 2,850 | no | 150 | 1.0 |
| `aspect_received_by_special_point` | 449 | no | 449 | 1.0 |
| `lord_aspects_lord_per_varga` | 959 | no | 909 | 1.0 |
| `aspect_matrix_summary`, `bhava_bala_aspectual`, `graha_effective_dignity_modified_by_aspects` | 60 / 60 / 45 | no | 25 / 15 / 45 | 1.0 |

322 distinct L2 signals (of 50,678) cite an L1 fact that carries an orb (Tajika 20 + conjunction
302), and all of them store `orb_tightness = 1.0`. In fact **all 50,678 rows store exactly
1.0** (no NULL, one distinct value, across all six producers), which is the default of
`SalienceInputs.orb_tightness` (`bodha_writers/formulas.py:127`: "1 = exact, 0 = at max orb"; the V2 dataclass repeats the default at `:587`).

The Tajika orbs the L2 rows ignore (identical across the five ayanamshas):

| L1 fact | pair | `orb_deg` | `orb_strength` (L1) | L2 `orb_tightness` stored |
|---|---|---|---|---|
| ithasala | MAR_SAT | 3.9128 | 0.7698 | 1.0 |
| ithasala | MER_SUN | 21.1239 | 0.0398 | 1.0 |
| eesarpha | JUP_VEN | 9.3852 | 0.4134 | 1.0 |
| manaau | JUP_MAR | 51.2683 | 0.1 | 1.0 |

## Why it matters

The condition term multiplies `orb_tightness` with `shadbala_norm` and `dignity_score` (v1 `deterministic_strength` at `formulas.py:158`; the V2 `condition_terms` product at `:671-676`, which is what the v2.0 rows use), so the
constant 1.0 *raises* the salience of every signal whose real orb is wider than exact. For the 20
Tajika signals that is not a rounding matter (a 21 degree "ithasala" is scored as exact). It is the
one place where the Q-L2-03 design choice "store None where no orb was computed" and the L1 data
disagree: an orb *was* computed, in L1, and is ignored.

## Consequences for the batched items (for SS; nothing is built here)

* TI-L2-27: for the Tajika and conjunction families the design can read the L1 orb instead of storing
  None. L1's `orb_strength` is already a 0 to 1 tightness for Tajika; conjunctions carry degrees only
  and need a stated normalisation (the formula's "max orb"). Either way the change **lowers**
  salience for wide-orb Tajika signals, so it belongs in the single rebuild with its own before/after.
* TI-L2-21's own residual (an L1 orb fact for Parashari / Jaimini / virupa aspects) stands for those
  families only.
* Reading `orb_strength` straight from L1 respects CLAUDE.md N.5 (L2 references the L1 value, does not
  re-derive it).

## What is NOT done

No writer, formula, stored value, declaration or registry change; no rebuild. Counts are a live
reading. Queries: `ti_l2_21_queries.sql` next to this note.
