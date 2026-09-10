---
artifact: L1_W1_ANALYSIS_BATCH_C
campaign: NIRMĀṆA
session: L1
wave: W1 (ANALYZE)
batch: C
assets: [ga_strength, ga_structural, ga_condition]
produced_on: 2026-09-05
status: DRAFT
mode: READ-ONLY (no repo file mutated other than this artifact; no build dispatched)
canonical_chart: 482012f1-710e-4a25-994a-93821f5871aa
comparison_charts: [1c826d5a-41cb-4450-b4dc-59d440e5f75a, cb73cd3d-9eba-4220-9902-0de91566e980]
---

# L1 W1 ANALYZE — Batch C (`ga_strength` · `ga_structural` · `ga_condition`)

Batch C owns the source facts the **D-SALIENCE** pillar (P5) consumes. Everything below is
measured against live production via `~/nirmana-s/bin/nq`, or read from source at a cited
`file:line`. Numbers I did not measure are marked as such.

**Headline (read this if nothing else):**

1. The plan's **41,760 argala facts figure is CORRECT** and traceable — but every one of those
   facts carries `verification_pass_status = 'single'`, and **`bodha_msr_signals.argala_modifier`
   is NULL on 150,150 / 150,150 signals across all three charts.** The largest single L1 fact
   family in the corpus is computed and stored and read by nothing.
2. **`vargottama_amplification` = 0 on 150,150 / 150,150 signals**, while `ga_structural` already
   emits `graha_vargottama_amplification_factor` per graha per ayanamsha. And the L1 fact's
   *units* (1.0 / 1.25, multiplicative) are **incompatible** with the salience formula's
   `(1 + vargottama_amplification)` consumption (additive increment) — wiring them naively would
   double-count.
3. **The AV support term is a degenerate constant.** `ashtakavarga_support_multiplier` = 1.15 on
   49,841 / 50,104 canonical signals because `_build_av_lookup` feeds **SARVA** bindus (23–34, a
   0–56 scale) into `_av_multiplier`, whose bands (`>=7 → 1.15`) are written for **BHINNA** bindus
   (0–8). Every house saturates the top band. The term *looks* wired and is functionally dead.
4. **The ŚUDDHA-VĀCA ṣaḍbala selector fix is NOT still correct.** It is correct on the canonical
   chart only, by coincidence. On the other two production charts it returns the wrong graha.
   The 2026-07-28/29 "verified live" pass was run on the one chart where the defect cannot
   manifest. Full evidence in §5.
5. **`ga_condition.varga_dignity_composite` is NULL on 135 / 135 rows** — a designed, served,
   advertised column with a real formula behind it, silently dead from a label-casing mismatch.
6. **`ga_condition`'s floor 2,880 equals its live count exactly** — the C12/D-126 "equality
   wearing a floor's name" pattern. Confirmed by arithmetic, §4.6.

---

## 0. Registry baseline (measured)

| field | `ga_strength` | `ga_structural` | `ga_condition` |
|---|---|---|---|
| `catalog_status` / `is_active` | CURRENT / t | CURRENT / t | CURRENT / t |
| `rung` / `domain` / `scope` | R1 / chart / per_chart | R1 / chart / per_chart | R1 / chart / per_chart |
| `has_substeps` | f (light `run(ctx)`) | t | t (1 substep per ayanamsha) |
| `target_table` | — (writes `chart_facts`) | — (writes `chart_facts`) | `ga_condition_composite` + `chart_facts` |
| `depends_on` (declared) | `ga_positions, ga_vargas` | `ga_dashas, ga_nakshatra, ga_panchanga, ga_positions, ga_sensitive, ga_strength, ga_vargas` | `ga_positions, ga_vargas, ga_dashas` |
| `target_floor` | 11,936 | 77,821 | 2,880 |
| live `count_sql` (canonical) | **13,621** | **98,542** | **2,880** |
| `expected_volume_formula` | `(6*GRAHAS + 8*GRAHAS*SIGNS + 6*BHAVAS) * AYANAMSHAS` | **NULL** | **NULL** |
| `integrity_check_sql` | **NULL** | **NULL** | **NULL** |
| `estimated_seconds` | 97 | 99 | 30 |
| `natural_key_partition` | NULL | NULL | NULL |
| `asset_throughput.state` (canonical) | `lit` | **`stale`** | `lit` |
| `asset_throughput.rows_written` | 13,195 | 103,489 | **45** |
| `asset_throughput.expected_rows` | NULL | NULL | NULL |

`fact_category_ownership` rows: `ga_structural` owns **57** categories; `ga_condition` owns
**2** (`graha_avastha_lajjitadi`, `graha_avastha_sayanadi`); `ga_strength` owns **0** — it
counts via `LIKE` patterns instead.

---

## 1. `ga_strength` — Ṣaḍbala · Ashtakavarga · Bhāva Bala

### 1.1 Pillar / doctrine service

**D-SALIENCE (primary, and correctly assigned)** + D-GROUNDING (secondary).
`ga_strength` is the source of *two* of D-SALIENCE's five multiplicative condition terms:
`shadbala_norm` and `ashtakavarga_support_multiplier` (`bodha_writers/formulas.py:562-572`).
It also anchors the "weakest graha" claim on every orientation surface (§5).
Assignment is still right. Nothing else in L1 computes strength.

### 1.2 Real vs declared dependencies

Declared: `ga_positions`, `ga_vargas`. Read of `ga_writers/ga_strength_writer.py:41-56` confirms
both are real: `compute_chart` / `pyjhora_strength` are re-derived from birth params, and the
FORENSIC gate is inherited from `ga_positions` (`forensic_gate` imported at line 50-57).
**No hidden edge found. No false edge found.** This is the cleanest dependency declaration
in the batch.

Note the *reverse* edge: `ga_structural` declares `ga_strength` as an upstream, and
`ga_structural_writer.py` does read `graha_shadbala_*` — real.

### 1.3 LEVERAGE — **the highest-value finding in this batch**

**(a) The AV term is dead, and looks alive.** `pipeline/orchestrator/writers/bo_laksana.py:957-985`
(`_build_av_lookup`) loads `ashtakavarga_bindu` rows with `fact_subject LIKE 'SARVA-HOUSE_%'` —
**sarva** (total-across-7-grahas) bindus. Measured, canonical/lahiri:

```
SARVA-HOUSE_1..12 bindus = 29,29,27,32,30,26,34,32,25,27,23,23
```

That value is fed to `bodha_writers/formulas.py:90-99`:

```python
def _av_multiplier(bindus: int) -> float:
    if bindus >= 7:  return 1.15
    ...
```

Those bands are written for **bhinna** bindus (0–8) — confirmed by the unit test itself,
`bodha_writers/__tests__/test_formulas.py:107,113` (`ashtakavarga_bindus=7` → asserts 1.15).
Every sarva house value (23–34) saturates `>= 7`. Result, measured live:

| chart | signals | `ashtakavarga_support_multiplier = 1.15` |
|---|---|---|
| 482012f1 | 50,104 | **49,841** (99.5%) |
| 1c826d5a | 50,171 | 49,909 |
| cb73cd3d | 49,875 | 49,625 |

The remaining rows are 1.0 (writer overrides) or NULL (emitters passing `null`). **The term
carries zero discriminating information.** A prior fix (documented in the `_build_av_lookup`
docstring as the "B2-fix") correctly repaired the *house* dimension and left the *scale*
mismatch untouched — a textbook §N.8 case: a detector that measures a proxy (a number was
fetched) rather than the claim (the number is on the multiplier's scale).

The correct feed exists and is unused: `ashtakavarga_bindu` with `fact_subject` prefixes
`SUN|MOON|MAR|MER|JUP|VEN|SAT` (60 rows each, canonical) is the bhinna layer, and
`ashtakavarga_kakshya_boundary` (120 rows) is the kakshya layer.

**(b) `check_fact_category_pinning.py` allowlists the very query.** Running the guard:
`0 new violations (27 pre-existing, allowlisted). PASS.` — and `bo_laksana.py:2390` (the
`ashtakavarga_bindu` SARVA select) is one of the 27. The guard PASSes on the exact read that
carries the defect.

### 1.4 Grounding

Correctly **not** `sruti`/`yukti` territory — this is computation, and the writer is honest
about it. `ga_strength_writer.py:15-20` explicitly says Pass 2 is "sanity checks on that real
output (NOT a second independent recomputation … not a 'verification' claim of independent
provenance)". Measured tier distribution over the full `count_sql` set (13,621 rows, canonical):

| tier | rows |
|---|---|
| `single_pass` | 10,055 |
| `floored` | **2,205** |
| `computed_extension` | 525 |
| `single` | 490 |
| `documented_approximation` | 300 |
| `not_defined_for_nodes` | 32 |
| `classical_match` | 14 |
| `two_pass_verified` | **0** |

Zero `two_pass_verified` matches the docstring — **this is honest, not a gap.** Good §N.7/§N.8
behaviour, and worth recording as a positive.

The 2,205 `floored` rows are all placeholders with `fact_value_num IS NULL`:
`graha_cheshta_bala_per_varga` (735), `graha_drik_bala_per_varga` (735),
`graha_kala_bala_per_varga` (735). They are honestly tiered — but they are counted
undifferentiated inside `count_sql`'s 13,621 (see 1.6).

Where a `yukti` label *would* be meaningful and is absent: `graha_ishta_phala` /
`graha_kashta_phala` are classical *interpretive* gradings derived from computed strength, not
raw computations. They currently ride the generic `single_pass` tier alongside pure arithmetic.

### 1.5 Temporal identity (D-TIME)

`ga_strength` is natal-static. The one time-bearing consumer surface is `graha_kala_bala_*`
(kāla bala is time-of-birth-dependent, not transit-dependent) — its per-varga family is entirely
`floored`/NULL, so D-TIME will find nothing usable there today.

### 1.6 Service

- **Real consumer: YES, multiple.** `get_strength.ts`, `get_ashtakavarga.ts`, `get_bhava_bala.ts`,
  `l1_context_fetcher.ts` (ranking), `query_ucd.ts` (weakest-graha), `bo_laksana` salience.
- **Floor:** 11,936 vs live 13,621 — a genuine floor (achieved ≥ floor, not equality). §N.4 OK.
  `expected_volume_formula` is populated and the only one in the batch. Good.
- **Density (§N.6):** `get_strength.ts` does the layering well — `total` (page) vs
  `total_available` (real `COUNT(*)`) vs `total_available_basis` with an explicit warning that
  `total_available` overstates the servable maximum by ~2.3× under the `all:false` default
  (`get_strength.ts:241-274`). This is exemplary. **But** it declares no `density_contract` field,
  so no CI/census harness can assert it (§N.6 item 4). Same for `get_ashtakavarga.ts`.
- **Cockpit density gap:** `count_sql` returns one flat 13,621 that silently includes 2,205
  NULL-valued `floored` placeholders. A reader cannot distinguish "13,621 strength facts" from
  "11,416 real + 2,205 floored". §N.6 item 1 violation at the registry layer.
- **Drill path ≤2 hops:** yes — `ganita_strength_get` → `get_strength.ts` → `chart_facts`.

### 1.7 Measured build + serve cost

`build_run_assets`, complete runs only:

| asset | n | min s | **median s** | max s | `estimated_seconds` |
|---|---|---|---|---|---|
| `ga_strength` | 49 | 6.7 | **96.9** | 1251.6 | **97** |

`estimated_seconds` = the historical median, to one decimal. Honestly derived. Recent runs
(2026-08-07/08) are 39–48s, i.e. the estimate is now ~2× conservative but not wrong.

---

## 2. `ga_structural` — the argala / aspect / dispositor / contradiction layer

### 2.1 Pillar / doctrine service

**D-SALIENCE (primary — it owns argala AND vargottama)** + **D-SYNTHESIS** (it owns
`contradiction_pair`, `convergence_count`, `sambandha_grade`, `chart_center_of_gravity`,
`graha_centrality`, `chart_cluster` — the graph-theoretic layer). Assignment still right; if
anything the plan under-credits its D-SYNTHESIS role, which is 1,810 `contradiction_pair` +
105 `convergence_count` rows per the registry's own `volume_explanation`.

### 2.2 Real vs declared dependencies

Declared 7 upstreams. All plausible from source, but note two things:

- `ga_structural_writer.py` reads **`ga_condition`'s** territory: it contains the string
  `graha_avastha_baladi` / `_deepta` / `_jagrad` / `_sayanadi` / `_lajjitadi` **and** so does
  `ga_condition_writer.py`. `fact_category_ownership` assigns `graha_avastha_baladi/deepta/jagrad`
  to **`ga_structural`** and `_sayanadi/_lajjitadi` to **`ga_condition`** — a split of one
  classical scheme family across two assets, with no declared edge `ga_structural → ga_condition`
  in either direction. This is an **undeclared adjacency**, not a cycle (each writes its own
  categories), but it makes "who owns avasthā" unanswerable from the registry alone.
- `ga_condition` is **not** in `ga_structural`'s `depends_on` and vice versa. Correct as long as
  the split above is intentional; flag it for W2 to rule on.

### 2.3 LEVERAGE — argala is fully computed and read by nothing that matters

**Measured, canonical chart:**

| `fact_category` | rows (canonical) | rows (each of 3 charts) | tier |
|---|---|---|---|
| `argala_natal_matrix` | **20,880** | 20,880 | `single` (100%) |
| `virodha_argala_natal_matrix` | **20,880** | 20,880 | `single` (100%) |
| **subtotal = the plan's figure** | **41,760** | 41,760 | |
| `net_argala_per_varga` | 1,740 | 1,740 | `single` (100%) |
| **argala family total** | **43,500** | 43,500 | |

Meanwhile:

```
bodha_msr_signals.argala_modifier — NON-NULL COUNT
  482012f1 : 0 / 50,104
  1c826d5a : 0 / 50,171
  cb73cd3d : 0 / 49,875
```

`bo_laksana.py:1300` hardcodes `"argala_modifier": None`, and the v2 salience formula
(`formulas.py:563-571`) does not include an argala term at all — only the v1 formula did
(`formulas.py:169`, `* (1 + s.argala_modifier)`), and v1 is not what production runs
(`salience_formula_version = 'v1.0'` is stored, but the code path is `salience_formula_v2`;
see F-C13). **43,500 facts, zero consumption.** This is the single largest leverage item in L1.

Same story for vargottama — see §4.3.

**One real consumer does exist** and is well built: `get_argala.ts`. Its header
(`get_argala.ts:5-7`) is where the plan's 41,760 figure originates ("live-verified against chart
482012f1: 41,760 rows across 29 vargas"), and my measurement reproduces it exactly. It also
already fixed a non-total `ORDER BY` (line 16-19) and added an `all_zero` disclosure flag
(line 30-35) — good §N.6 behaviour, though again with no `density_contract`.

### 2.4 Grounding

Measured tier distribution over the 98,542 owned rows:

| tier | rows | share |
|---|---|---|
| `single` | 97,936 | 99.4% |
| `computed_extension` | 540 | 0.5% |
| `single_pass` | 66 | 0.1% |

**Where a `sruti`/`yukti` label would be meaningful and is absent — this is the honest gap:**
`ga_structural` is *not* purely deterministic computation. `sambandha_grade`,
`graha_effective_dignity_modified_by_aspects`, `graha_composite_state_classification`,
`graha_special_state_rollup`, `house_strength_classification_rollup`, `karaka_bhava_concordance`
and `contradiction_pair` are all **graded/classified** outputs — rule applications, not
arithmetic. Each has a nameable classical rule (BPHS aspect/sambandha chapters) and each is
currently stamped `single`, which says "nothing double-checked this" but says nothing about
*what rule it applies*. Argala is the clearest case: `_build_argala_rows` implements BPHS Ch. 28
(cited in `bo_karanajala.py:393-396` from the L2 side), yet the 41,760 rows carry no
`classical_match` tier and no rule id. If any L1 category deserves a `yukti`/`sruti` axis, it is
this one.

### 2.5 Temporal identity (D-TIME)

`chandra_bala_natal_baseline` and `tara_bala_natal_baseline` are explicitly *baselines* — the
natal anchors D-TIME's transit machinery counts from. They are owned here, tiered `single`, and
D-TIME will consume them. Flag for the D-TIME batch: `tara_bala` (43 rows) is **unowned**
(see 2.6) and therefore invisible to this asset's own count.

### 2.6 Service — the cockpit undercounts this asset by ~5,000 rows

`ga_structural`'s `count_sql` joins `fact_category_ownership`. Measured:

```
count_sql live                                 : 98,542
asset_throughput.rows_written (2026-08-10 build): 103,489
delta                                          :   4,947
```

The delta is real and attributable. Categories the writer emits that have **no**
`fact_category_ownership` row, measured on the canonical chart:

```
virupa_drishti                     2,755
karaka_web_per_varga               1,052
significator_path                    360
panchadha_maitri                     210
conjunction_special_point            137
bhava_bala_{aspectual,directional,lord,occupant,positional,temporal,total_extended}  60 × 7 = 420
nakshatra_lord_relationship           45
tara_bala                             43
graha_saptavargaja_bala_component     35
vimsopaka_bala_per_graha              35
yoga_label                            34
kendradhipati_dosha                   20
upapada_lagna                         10
nakshatra_co_tenancy                   1
                            TOTAL = 5,157  (measured)
```

5,157 vs the 4,947 delta — within writer-attribution noise (the two figures come from different
builds). **These rows are built, correct, and structurally invisible to the cockpit.**
Repository-wide the problem is larger: **40,839 of the canonical chart's facts have no
`fact_category_ownership` row at all.**

Other service notes:
- **Floor:** 77,821 vs live 98,542. Genuine floor (§N.4 OK) but *stale by 20,721* —
  `volume_explanation` is dated "post-Phase-2 rebuild (2026-06-18)".
- **`expected_volume_formula` is NULL** despite the `volume_explanation` containing a full
  per-category breakdown that is literally a formula in prose.
- **`asset_throughput.state = 'stale'` for the canonical chart** (last built 2026-08-10). The
  other two charts are `lit`. This is a live cockpit-truth item.
- Drill path ≤2 hops: yes (`ganita_structural_get` → `get_argala.ts` / `get_aspects.ts` /
  `get_dispositors.ts` → `chart_facts`).

### 2.7 Measured build + serve cost

| asset | n complete | min s | **median s** | max s | `estimated_seconds` |
|---|---|---|---|---|---|
| `ga_structural` | 52 | 61.6 | **98.3** | 228.1 | **99** |

Recent runs 107–117s. Estimate honest and current.

---

## 3. `ga_condition` — planetary condition composite + per-varga avasthā

### 3.1 Pillar / doctrine service

**D-GROUNDING (primary)** + D-SALIENCE (secondary). It produces the only unified per-graha
0–1 `condition_score` in the whole corpus, with a stored `condition_score_breakdown`. It is not
currently a D-SALIENCE feed but it is the natural home for one.

### 3.2 Real vs declared dependencies

Declared `ga_positions, ga_vargas, ga_dashas` — all three verified real in
`ga_condition_writer.py` (`_load_graha_positions`, `_load_varga_dignity_spread` reading
`chart_divisionals`, `_load_dasha_periods`). **One hidden dependency:** it reads four L0
reference tables directly (`_load_dignity_ref`, `_load_motion_thresholds`,
`_load_combustion_orbs`, `_load_naisargika_friendships` at lines 606/635/657/684) with no
declared `bg_*` upstream. Not a cycle, but the DAG understates its inputs.

### 3.3 LEVERAGE — a served column that is NULL on 100% of rows

`ga_condition_composite.varga_dignity_composite` is **NULL on 135 / 135 rows** (all 3 charts ×
9 grahas × 5 ayanamshas), while `varga_dignity_spread` is populated on **135 / 135** with a rich
29-varga JSON per graha.

Root cause, traced to source — two independent faults, either sufficient:

1. **Case/vocabulary mismatch.** `_compute_varga_composite` (`ga_condition_writer.py:812-840`)
   resolves a score via `DIGNITY_SCORES.get(dignity)`. `DIGNITY_SCORES`
   (`ga_condition_writer.py:53-63`) is keyed `"exalted"`, `"moolatrikona"`, `"own"`,
   `"friend_sign"`, `"neutral_sign"`, `"enemy_sign"`, `"debilitated"`. The stored spread's labels
   are Title-Case bare words — measured from a live row:
   `{"D1":{"sign":"Capricorn","dignity":"Enemy"}, "D2":{...,"dignity":"Moolatrikona"}, ...}`.
   `"Enemy"` ≠ `"enemy_sign"` — and not even case-insensitively, because of the `_sign` suffix.
   **Every varga misses.**
2. **`score` is never present.** `_load_varga_dignity_spread` (line 765-810) requests
   `fact_key IN ('sign','dignity','overall_dignity_score')`, but no live spread row contains a
   `score` key — only `sign` and `dignity`. So the `data.get("score")` fast path never fires.

With every varga contributing nothing, `total_w == 0` → `return None` (line 838-840). Silent,
deterministic, 100%.

**Why this is a LEVERAGE finding and not just a bug:** `get_condition_composite.ts:76` SELECTs
the column, and its `description` (lines 29-31) advertises "varga_dignity_spread/**composite**"
to every caller. A designed consumer is reading NULL where the asset has the input data and the
formula in hand. Exactly §N.8: no detector ever asserted this column, so it has read NULL since
it shipped.

(Minor, same file: `get_condition_composite.ts:5` says the table has "90 rows". Live is 45 per
chart, 135 total. Stale doc figure.)

### 3.4 Grounding — **the most interpretive asset in the batch, with the weakest labelling**

Measured tiers over the 2,835 `chart_facts` rows in `count_sql`:

| tier | rows |
|---|---|
| `computed_extension` | 2,700 |
| `floored` | 135 |

Zero `two_pass_verified`, zero `classical_match`, zero `single_pass`.

**Where a `sruti`/`yukti` label WOULD be meaningful and is absent — plainly:** the five avasthā
schemes are *classical doctrine*, not computation. `avastha_baladi_from_degree`,
`avastha_jagradadi_from_dignity`, `avastha_deeptaadi_from_dignity_and_state`,
`_sayanadi_from_degree`, `_lajjitadi_from_context` (lines 260/277/291/1203/1209) each implement a
named BPHS scheme with a citable verse. They are all stamped `computed_extension`, which is a tier
about *provenance of arithmetic*, not about *which ācārya's rule this is*. `compute_panchadha_maitri`
and `compute_tatkalika_relation` are the same. This asset is where a `sruti` axis would buy the
most; today the classical rule identity is carried only in `citation_ref`/`citation_human`, not in
any queryable grading axis.

`condition_score` itself (`compute_condition_score_v1`, line 455) is a **synthetic composite** —
a weighted blend that is neither `pratyaksa` observation nor a single classical rule. It carries
`condition_formula_version = 'condition_formula_v1'` (good — versioned), range 0.235–0.775 on the
canonical chart, populated 45/45. But it has no epistemic tier of its own.

### 3.5 Temporal identity (D-TIME)

`peak_dasha_periods` (populated on 20/45 canonical rows) and `weak_dasha_periods` (5/45) are the
time-bearing outputs: dasha windows gated on `condition_score` crossing
`_PEAK_CONDITION_THRESHOLD = 0.65` / `_WEAK_CONDITION_THRESHOLD = 0.35`
(`ga_condition_writer.py:844-847`). D-TIME should consume these. The NULLs are honest (a graha
whose score never crosses a threshold correctly gets none) — but there is no `empty_reason`
distinguishing "no window" from "not computed".

### 3.6 Service — the floor is an equality wearing a floor's name

**This is the C12 / D-126 pattern, confirmed by arithmetic, not by inference.**

`count_sql` = `ga_condition_composite` + four `chart_facts` predicates. Measured components,
canonical chart:

```
ga_condition_composite                     45
graha_avastha_baladi_per_varga          1,305
graha_avastha_deeptaadi_per_varga       1,305
graha_avastha_jagradadi_per_varga          45
graha_avastha_lajjitadi_per_varga          45
graha_avastha_sayanadi_per_varga           45
graha_avastha_sayanadi                     45
graha_avastha_lajjitadi                    45
graha_yuddha                                0   ← no rows exist for this chart
                                    ---------
                              TOTAL      2,880   ==  target_floor 2,880
```

Not "≥ floor". **Identically equal**, and it must be — every term is a fixed product of
(9 grahas × 5 ayanamshas × a fixed varga count). There is no chart on which this number can
differ, *except* via `graha_yuddha`, which is chart-dependent and currently contributes 0. So:

- On any chart with a graha yuddha, live count would **exceed** 2,880 (fine).
- On this chart the "floor" is a tautology — it can never detect a partial build, only a total
  one. Per §N.8, a gate that cannot read false for the failure it claims to detect is not a gate.
- Worse, **`asset_throughput.rows_written = 45`** for all three charts — the orchestrator records
  only the composite-table rows and none of the 2,835 `chart_facts` rows, because
  `run_substep` returns `build_ga_condition_substep`'s return value (composite rows only).
  `rows_written` (45) and `count_sql` (2,880) disagree by 64×.

Other service notes:
- **`expected_volume_formula` NULL** — despite the `volume_explanation` stating the exact
  arithmetic ("45 D1 composite + 2,835 per-varga avastha = 2,880").
- Real consumers: `get_condition_composite.ts` (serving), `ph_muhurta.py:306-313` (reads
  `condition_score` per graha). Both real. Drill path ≤2 hops: yes.
- No `density_contract`; `get_condition_composite.ts` does carry one `empty_reason`.
- `ga_condition` owns only 2 fact_categories in `fact_category_ownership` while its `count_sql`
  counts 7 — the other 5 (`*_per_varga`) are **unowned**. Its counting works only because it uses
  `LIKE` predicates rather than the ownership join. If it were ever migrated to the ownership-join
  pattern (as `ga_structural` was), it would silently drop to 90 rows.

### 3.7 Measured build + serve cost — **the estimate is 10× stale**

| asset | n complete | min s | median s | max s | `estimated_seconds` |
|---|---|---|---|---|---|
| `ga_condition` | 51 | 10.6 | 29.6 | **297.0** | **30** |

The median matches the estimate — but the median is dominated by old fast runs. **Every run since
2026-08-06 has been 277–298s**: 279.0, 279.8, 277.7, 297.0, 279.6. The asset now costs ~9.3× its
declared estimate, and the build UI's ETA is wrong by that factor. `ga_condition` is the *most
expensive* asset in this batch in wall-clock, while being declared the cheapest.

---

## 4. D-SALIENCE source-fact certification

The four questions the batch was asked, answered with measured counts. **Bottom line: all four
source families exist in L1 except cancellation; none of the three static terms is actually
consumed.**

### 4.1 Argala — the plan's 41,760 figure is **CONFIRMED**

| owning asset | `fact_category` | canonical rows | all 3 charts | tier | L2-readable today? |
|---|---|---|---|---|---|
| `ga_structural` | `argala_natal_matrix` | 20,880 | 20,880 each | `single` | **yes** — `get_argala.ts` |
| `ga_structural` | `virodha_argala_natal_matrix` | 20,880 | 20,880 each | `single` | **yes** — `get_argala.ts` |
| `ga_structural` | `net_argala_per_varga` | 1,740 | 1,740 each | `single` | partially (not in `get_argala.ts`'s category list) |

**41,760** = the two natal matrices exactly. The plan's figure is right and its provenance is
`get_argala.ts:5-7`. The full argala family is **43,500** — `net_argala_per_varga` is the 1,740
the plan's figure omits, and it is arguably the *most* directly usable of the three (it is the
already-netted result rather than the raw matrix).

Stable key for an L2 consumer: `fact_subject` = `{VARGA}_SIGN_{1-12}` (e.g. `D9_SIGN_4`),
`fact_key` = `from_sign_N_offset_M`. Both are stable and parseable
(`get_argala.ts:47` `SUBJECT_RE`). **Reachable today: YES.**

**Consumed today: NO.** `bodha_msr_signals.argala_modifier` = NULL on 150,150/150,150 rows.
`bo_laksana.py:1300` hardcodes `None`; `salience_formula_v2` has no argala term at all
(`formulas.py:563-571`). Note ~67% of matrix cells are a structurally intentional 0.0
(`get_argala.ts:30-35`) — so a naive wiring must not read "0.0" as "missing".

### 4.2 Ashtakavarga (bindu + kakshya) — **present, both levels, not consumed meaningfully**

Owner: **`ga_strength`** (writes them; `ga_structural` reads them). Measured canonical:

| `fact_category` | canonical | all charts | level |
|---|---|---|---|
| `ashtakavarga_bindu` | 480 | 1,440 | bhinna (7 grahas) + SARVA, D1 |
| `ashtakavarga_bindu_per_varga` | 6,720 | 20,160 | bhinna, all vargas |
| `ashtakavarga_bindu_sign` | 480 | 1,440 | per-sign |
| `ashtakavarga_kakshya_boundary` | **120** | 360 | **kakshya** (`KAKSHYA_1..8` × `{start_deg,end_deg,lord}` × 5 ayanamshas) |
| `ashtakavarga_pinda_sarva` | 40 | 120 | sarva pinda |
| `ashtakavarga_pinda_sarva_per_varga` | 560 | 1,680 | |
| `ashtakavarga_pinda_bhinna` / `_sodhita` / `_raasi` | 40 each | 120 each | |
| `ashtakavarga_trikona_shodhana` | 420 | 1,260 | reduction |
| `ashtakavarga_ekadhipathya_shodhana` | 420 | 1,260 | reduction |
| **AV total (canonical)** | **9,240** | | |

**Both bindu and kakshya are present.** Bindu is present at sarva, bhinna, per-sign, and
per-varga granularity. Kakshya is present as boundaries + lords (120 rows) — but note it is
*boundaries only*: there is no per-kakshya bindu-occupancy fact, which is what a transit-gating
consumer would actually want.

Reachable today: **yes** via `get_ashtakavarga.ts` (`AV_CATEGORIES` at line 25-37, with
`ashtakavarga_bindu_per_varga` / `_pinda_sarva_per_varga` opt-in at line 38).

Consumed today: **nominally yes, effectively no** — see §1.3(a). The `ashtakavarga_support_multiplier`
term is a constant 1.15 because sarva values are fed to a bhinna-scaled band function.
**None of these 9,240 AV facts have `fact_category_ownership` rows**, so they are invisible to any
ownership-join count.

### 4.3 Vargottama — **present in three separate places, with a units problem**

| owner | `fact_category` | canonical | all charts | shape |
|---|---|---|---|---|
| `ga_structural` | `graha_vargottama_amplification_factor` | **35** (7 grahas × 5 ayanamshas) | 105 | `fact_key='amplification_factor'`, `fact_value_num ∈ {1.0, 1.25}` |
| `ga_structural` | `vargottama_per_varga` | 1,260 | 3,780 | `fact_key='is_vargottama'`, text `vargottama` (101) / `not_vargottama` (1,159) |
| `ga_structural` | `tajik_vargottama_specific` | 15 | 45 | Tājika-specific |
| (also) | `chart_facts.vargottama_flag_at_point` | — | — | a boolean **column** on every fact row |

**Present per-planet: YES** — `graha_vargottama_amplification_factor` is one row per classical
graha per ayanamsha (7 × 5 = 35; nodes excluded). Measured canonical/lahiri: MER = 1.25, all
others = 1.0.

**Two problems an L2 consumer must resolve before wiring:**

1. **Units are incompatible with the formula that consumes them.** `salience_formula_v2` uses
   `(1 + s.vargottama_amplification)` (`formulas.py:569`) — i.e. it expects an *additive
   increment* (0 = none). The L1 fact is a *multiplier* (1.0 = none, 1.25 = vargottama). Passing
   the fact through unchanged turns 1.25 into ×2.25. The correct wiring is `factor - 1.0`.
2. **The serving description already documents a third, different scale.** `get_dignity.ts:31`
   says "vargottama amplification factor (**0 / 0.20 / 0.50** based on how many vargas share same
   rashi)". Measured distinct values across the whole table: **1.0 (88 rows) and 1.25 (17 rows)**.
   Neither 0.20 nor 0.50 exists anywhere. The narration and the data disagree — a §N.7 item 1
   defect on the serving surface.

Consumed today: **NO.** `bodha_msr_signals.vargottama_amplification` = **0 on 150,150 / 150,150
rows**, all three charts. `bo_laksana.py:1299` hardcodes `0.0`; the live tag key
(`bo_laksana.py:1913`, `tags.get("vargottama_amp")`) is never populated.

### 4.4 Cancellation modifiers (nīcabhaṅga et al.) — **NOT computed in L1**

Searched `chart_facts.fact_category` across the whole DB for `%bhanga%`, `%neecha%`, `%cancel%`.
**The only match is `sade_sati_cancellation_check` (40 rows canonical, owned by `ga_sade_sati`).**
There is **no nīcabhaṅga fact_category in L1 at all.**

Where cancellation *does* live:

| location | layer | shape | canonical state |
|---|---|---|---|
| `ga_yoga_firings.bhanga_active` / `bhanga_rule_fired` / `bhanga_na_reason` | L1, `ga_yoga` (**not batch C**) | boolean + rule | 3 active(t) w/ rule, 20 false, **40 NULL** |
| `brahma_yoga_catalog.bhanga_rules_jsonb`, `.cancellation_conditions` | L0 | rule text | — |
| `brahma_dosha_catalog.cancellation_conditions` | L0 | rule text | — |
| `bg_parihara_rules.cancellation_condition_text` / `.cancellation_index` | L0 | rule text | — |
| `bodha_msr_signals.neechabhanga_modifier` / `.cancellation_modifier` | L2 | numeric | see below |

Measured L2 state, canonical chart:
```
neechabhanga_modifier : 1.0 on 50,101 rows ; 1.3 on 3 rows
cancellation_modifier : 1.0 on 50,104 rows  (constant — no row differs)
```
The 3 rows at 1.3 correspond to the 3 `bhanga_active = true` yoga firings — so *nīcabhaṅga* has a
thin real signal path (via `ga_yoga`, not batch C). **`cancellation_modifier` has none at all** —
it is a constant 1.0 everywhere, with no L1 source and no detector. Per §N.8 that is an
unimplemented check wearing a neutral value's clothes.

Also note `ga_yoga_firings.bhanga_active` is **NULL on 40 of 63** canonical rows — for most yoga
firings the bhaṅga question was never asked, and NULL is honest, but a consumer reading
`bhanga_active IS NOT TRUE` as "not cancelled" would be wrong on 40 rows.

**Answer: cancellation modifiers are NOT verified, and for the generic (non-nīcabhaṅga) case they
are not computed anywhere.** The D-SALIENCE plan line "cancellation modifiers verified" cannot be
satisfied from L1 today.

### 4.5 Summary certification table

| D-SALIENCE term | L1 owner | fact_category | canonical rows | L2-reachable today | actually consumed |
|---|---|---|---|---|---|
| argala | `ga_structural` | `argala_natal_matrix` + `virodha_argala_natal_matrix` (+ `net_argala_per_varga`) | **41,760** (43,500 incl. net) | YES (`get_argala.ts`) | **NO — NULL 150,150/150,150** |
| AV support | `ga_strength` | `ashtakavarga_bindu*` (+ kakshya, pinda, shodhana) | **9,240** | YES (`get_ashtakavarga.ts`) | **degenerate constant 1.15** |
| vargottama | `ga_structural` | `graha_vargottama_amplification_factor` (35) + `vargottama_per_varga` (1,260) | **1,295** | YES (`get_dignity.ts`) | **NO — 0 on 150,150/150,150** |
| cancellation | *(none)* | — | **0** | n/a | constant 1.0, no source |
| nīcabhaṅga | `ga_yoga` (not batch C) | `ga_yoga_firings.bhanga_*` | 23 non-NULL of 63 | yes | 3 signals at 1.3 |

`bodha_msr_signals.salience_inputs_complete = false` on **150,150 / 150,150 rows, all three
charts.** The system's own honest flag already says every salience value in production is built
from incomplete inputs. That flag is §N.8-correct behaviour and should be preserved, not papered
over, when the terms are wired.

---

## 5. §N.7 precedent re-verification: the ṣaḍbala selector

**Instruction was to re-verify the ŚUDDHA-VĀCA ṣaḍbala serving-layer fix is still correct, live,
with evidence. It is NOT. Reporting in full.**

### 5.1 What the fix is

`platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts:64-83`,
`deriveShadbalaWeakestGraha`:

```sql
SELECT fact_subject, fact_value_num
FROM chart_facts
WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_shadbala_total'
  AND fact_value_num IS NOT NULL
  AND fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN')
ORDER BY fact_value_num ASC
LIMIT 1
```

Documented in `platform/src/lib/vidhi/cr_status.ts:17-34` as CR-55 CLOSED-WITH-RESIDUAL,
"VERIFIED LIVE (postgres, chart 482012f1): shadbala MIN = Venus (0.8436) → served correctly".

### 5.2 The defect: `fact_category = 'graha_shadbala_total'` holds **three** `fact_key`s

Measured, whole table:

| `fact_key` | rows | min | max |
|---|---|---|---|
| `rupa` | 135 | 0.375 | 9.69 |
| `ratio` | 105 | 0.8436 | 1.786 |
| `required_rupa` | 21 | 5 | 7 |

The query pins **no `fact_key`**. Its `ORDER BY fact_value_num ASC` therefore ranks *across
incommensurable units*. Because every `ratio` (0.84–1.79) is smaller than every non-node `rupa`
(4.64–9.69), the MIN **always** comes from the `ratio` set. The function is not "weakest by
ṣaḍbala"; it is "weakest by ṣaḍbala-to-required ratio" — and it labels its return field
`shadbala_rupa`.

### 5.3 Live evidence: it returns the wrong graha on 2 of 3 production charts

```
chart                                 ayanamsha              weakest_by_ratio  weakest_by_rupa   min_rupa  min_ratio
1c826d5a-41cb-4450-b4dc-59d440e5f75a  krishnamurti           JUP               SAT               5.73      1.0615
1c826d5a-41cb-4450-b4dc-59d440e5f75a  lahiri_chitrapaksha    JUP               SAT               5.73      1.0615
1c826d5a-41cb-4450-b4dc-59d440e5f75a  raman                  MOON              SAT               6.22      1.0850
1c826d5a-41cb-4450-b4dc-59d440e5f75a  surya_siddhanta_...    JUP               SAT               5.73      1.0615
1c826d5a-41cb-4450-b4dc-59d440e5f75a  true_chitra            JUP               SAT               5.73      1.0615
482012f1-710e-4a25-994a-93821f5871aa  (all 5)                VEN               VEN               4.64      0.8436
cb73cd3d-9eba-4220-9902-0de91566e980  (all 5)                JUP               SAT               5.48      0.9262
```

- **Chart 1c826d5a (Abhinandan Mohanty):** served answer **Jupiter** (Moon under Raman).
  True weakest by ṣaḍbala rupa: **Saturn**. **WRONG on 5/5 ayanamshas.**
- **Chart cb73cd3d:** served **Jupiter**. True weakest: **Saturn**. **WRONG on 5/5.**
- **Chart 482012f1 (canonical):** Venus by both measures. **RIGHT — by coincidence.**

**The 2026-07-28 fix and the 2026-07-29 re-verification were both performed on the single chart
where the defect is invisible.** This is §N.8 in its purest form: the verification measured a
proxy (does the canonical chart give the expected name?) rather than the claim (does this selector
rank ṣaḍbala?).

Secondary: even on the canonical chart the *value* is mislabeled. The function returns
`shadbala_rupa: 0.8436`. Venus's actual ṣaḍbala is **4.64 rupa**; 0.8436 is the ratio
(4.64 / 5.5 required — internally consistent, so `ga_strength` itself is correct). The CR-55
close note's own phrase "shadbala MIN = Venus (0.8436)" carries the mislabel forward.

Tertiary: `ORDER BY fact_value_num ASC LIMIT 1` with no tiebreak is not a **total** order — §N.7
item 2's second requirement is unmet independently of the `fact_key` problem.

Quaternary (stale doc): `cr_status.ts:26` records the residual as "`vw_chart_digest.weakest_graha`
STILL returns Mercury". Measured today: it returns **Venus** on 4 ayanamshas and **Mars** on 1.
The recorded residual is stale — the view's behaviour changed and nobody re-measured it.

### 5.4 Why the CI guard did not catch this

`platform/scripts/governance/check_fact_category_pinning.py` PASSes today
(`0 new violations (27 pre-existing, allowlisted)`). It misses this for two structural reasons:

1. **Its TypeScript scanner only matches JS array methods.** `_TS_CALL_RE = re.compile(r"\.(find|filter)\s*\(")`
   (line 266; used at line 301-305). Raw SQL in a TS template literal is never scanned. So
   `query_ucd.ts`'s SQL is outside the guard's reach entirely — the guard's Python-side SQL rule
   has no TypeScript counterpart.
2. **Its own acceptance rule would have passed it anyway.** The guard's docstring (lines 36, 222)
   treats "a deterministic `ORDER BY ... LIMIT 1`" as sufficient **without** a `fact_key` pin, and
   line 66-68 admits it "does not attempt to prove uniqueness". An `ORDER BY` over a mixed-`fact_key`
   set satisfies that branch while being exactly the ambiguity the guard exists to prevent.

**Compliance of batch-C consumers with §N.7 item 2:** `get_strength.ts:171` has a total
`ORDER BY fact_category, ayanamsha_id, fact_key` and no single-row reduction — compliant.
`get_argala.ts:131` has `ORDER BY ayanamsha_id, fact_subject, fact_key` (a prior fix, documented at
line 16-19) — compliant. `get_ashtakavarga.ts:107` likewise. `l1_context_fetcher.ts:88-96` does no
single-row reduction — compliant. The non-compliant reads are `query_ucd.ts:70-76` (§5) and
`bo_laksana.py:2390` (allowlisted, §1.3).

---

## 6. Consolidated findings

| id | asset | finding | evidence | proposed triage | doctrine cited |
|---|---|---|---|---|---|
| **F-C1** | `ga_strength` | **Ṣaḍbala weakest-graha selector returns the wrong graha on 2 of 3 production charts.** `deriveShadbalaWeakestGraha` pins no `fact_key`; `graha_shadbala_total` holds `rupa`/`ratio`/`required_rupa`, and the MIN always lands in `ratio`. Prior "verified live" pass ran only on the chart where the bug is invisible. | `query_ucd.ts:64-83`; live: 1c826d5a served JUP vs true SAT (5/5 ayanamshas), cb73cd3d served JUP vs true SAT (5/5), 482012f1 VEN both ways; `cr_status.ts:17-34` | **MUST** | §N.7 items 1,2,5; §N.8 (verification measured a proxy) |
| **F-C2** | `ga_structural` | **41,760 argala facts (43,500 with `net_argala_per_varga`) are computed and consumed by nothing.** `bodha_msr_signals.argala_modifier` NULL on 150,150/150,150 rows, all 3 charts. `salience_formula_v2` has no argala term. | measured counts; `bo_laksana.py:1300`; `formulas.py:563-571` | **MUST** (this is the D-SALIENCE P5 mandate itself) | plan §5 D-SALIENCE; §N.5 |
| **F-C3** | `ga_strength` | **AV support term is a degenerate constant.** SARVA bindus (23–34) fed to a BHINNA-scaled band function (`>=7 → 1.15`); 49,841/50,104 canonical signals = 1.15. Term carries zero information. | `bo_laksana.py:957-985`; `formulas.py:90-99`; `test_formulas.py:107,113`; live SARVA-HOUSE values 23–34 | **MUST** | §N.8 (detector measures a proxy); §N.6 |
| **F-C4** | `ga_structural` | **`vargottama_amplification` = 0 on 150,150/150,150 signals** while 35 per-graha amplification facts exist. | `bo_laksana.py:1299,1913`; live | **MUST** | plan §5 D-SALIENCE |
| **F-C5** | `ga_structural` | **Vargottama units are incompatible with their consumer.** L1 stores a multiplier (1.0/1.25); `salience_formula_v2` consumes `(1 + x)` expecting an increment. Naive wiring double-counts. | live distinct values {1.0×88, 1.25×17}; `formulas.py:569` | **MUST** (blocks F-C4's fix) | §N.5 (L1 is the authority; consumer must inherit, not reinterpret) |
| **F-C6** | `ga_structural` | **`get_dignity.ts` narrates a scale that does not exist in the data** — "0 / 0.20 / 0.50" vs live {1.0, 1.25}. | `get_dignity.ts:31`; live | **NOW** | §N.7 item 1 (narration must restate the cited fact) |
| **F-C7** | *(none / `ga_yoga`)* | **Cancellation modifiers have no L1 source.** No `%bhanga%`/`%neecha%`/`%cancel%` fact_category in L1 except `sade_sati_cancellation_check`. `bodha_msr_signals.cancellation_modifier` = 1.0 on 100% of rows with no detector. Nīcabhaṅga exists only in `ga_yoga_firings.bhanga_*` (NULL on 40/63). | full-DB category scan; live modifier distribution | **MUST** (D-SALIENCE says "cancellation modifiers verified" — unsatisfiable today) | §N.8 (a flag with no detector is null, not green) |
| **F-C8** | `ga_condition` | **`varga_dignity_composite` NULL on 135/135 rows** — served and advertised. Two independent causes: `DIGNITY_SCORES` keys are lowercase+`_sign`-suffixed while stored labels are Title-Case bare (`"Enemy"` vs `"enemy_sign"`); and `overall_dignity_score` never lands in the spread. | `ga_condition_writer.py:53-63, 812-840, 765-810`; live spread JSON; `get_condition_composite.ts:29-31,76` | **MUST** | §N.8; §N.7 item 6 |
| **F-C9** | `ga_structural` | **~5,000 built rows are invisible to the asset's own `count_sql`.** Ownership-join count 98,542 vs `rows_written` 103,489; the ga_structural-exclusive unowned categories measure **5,157** (`virupa_drishti` 2,755, `karaka_web_per_varga` 1,052, `significator_path` 360, …). Repo-wide, 40,839 canonical facts have no ownership row. | live; measured category list §2.6 | **MUST** | §N.4 cockpit-truth |
| **F-C10** | `ga_condition` | **`target_floor` 2,880 is identically equal to a fixed arithmetic product**, not an achieved-count floor with headroom. It cannot read false for a partial build. Confirmed by full component arithmetic (45 + 1,305 + 1,305 + 45×5 + 0). | live component counts §3.6 | **MUST** | C12/D-126; §N.4; §N.8 |
| **F-C11** | `ga_condition` | **`asset_throughput.rows_written = 45` vs `count_sql` 2,880 (64× disagreement)** — the substep return value counts only composite rows, not the 2,835 `chart_facts` rows. | live `asset_throughput`; `pipeline/orchestrator/writers/ga_condition.py:39-46` | **NOW** | §N.8; §N.4 cockpit-truth |
| **F-C12** | `ga_condition` | **`estimated_seconds` = 30 but every run since 2026-08-06 took 277–298s (~9.3×).** Median (29.6) is dominated by stale fast runs. Build ETA is wrong by an order of magnitude. | `build_run_assets`: 279.0, 279.8, 277.7, 297.0, 279.6 | **NOW** | §N.4 (measured, not asserted) |
| **F-C13** | *(cross)* | **`salience_formula_version` stores `'v1.0'` on 150,150 rows while the executing code is `salience_formula_v2` (`VERSION_SALIENCE_FORMULA_V2`).** The stored provenance names a formula that includes an argala term the running formula does not have. | live `salience_formula_version`; `formulas.py:541-604` | **NOW** — flagged with uncertainty: I did not trace every writer's version literal, only the dominant stored value | §B.8; §N.7 item 1 |
| **F-C14** | *(guard)* | **`check_fact_category_pinning.py` cannot see the F-C1 defect class.** Its TS scanner only matches `.find(`/`.filter(` (line 266) — raw SQL in TS is unscanned; and its own rule (lines 36, 222) accepts `ORDER BY … LIMIT 1` *without* a `fact_key` pin, which is exactly F-C1's shape. | source lines cited; guard PASSes today with 27 allowlisted | **MUST** (a guard that cannot fail on the live defect is the §N.8 pattern one layer up) | §N.7 item 2; §N.8 |
| **F-C15** | all 3 | **`integrity_check_sql` is NULL on all three** (and on all 19 L1 assets). Combined with F-C9/F-C10, no asset in this batch has any check that can distinguish a partial build from a complete one. | live registry | **MUST** | §N.8 |
| **F-C16** | `ga_structural`, `ga_condition` | **`expected_volume_formula` is NULL** on both, despite each `volume_explanation` containing the exact arithmetic in prose. | live registry (both `volume_explanation` fields quoted §0) | **NOW** | §N.4 |
| **F-C17** | `ga_structural` | **`asset_throughput.state = 'stale'` for the canonical chart** (other two charts `lit`). Floor 77,821 is also 20,721 behind live 98,542, dated 2026-06-18. | live | **NOW** | §N.4 |
| **F-C18** | `ga_structural`, `ga_condition` | **Avasthā ownership is split across two assets with no declared edge.** Ownership gives `baladi/deepta/jagrad` → `ga_structural`, `sayanadi/lajjitadi` → `ga_condition`; both writers contain all five names; `*_per_varga` variants are unowned entirely. `ga_condition` owns 2 categories but counts 7. | `fact_category_ownership`; both writer files; §3.6 | **NOW** | §N.4 cockpit-truth; B.8 |
| **F-C19** | `ga_condition` | **The five avasthā schemes and pañcadhā-maitrī are classical rule applications tiered `computed_extension`, with no `sruti`/`yukti` axis.** Same for `ga_structural`'s `sambandha_grade`, `contradiction_pair`, and the 41,760 argala rows (all `single`, no `classical_match`) despite implementing BPHS Ch. 28. | live tier distributions §1.4/§2.4/§3.4; `ga_condition_writer.py:260,277,291,1203,1209` | **NEVER-LATER** (a real gap, but a doctrine-design decision, not a defect to patch in this wave) | §B.1, §B.3 |
| **F-C20** | `ga_strength` | **`count_sql` flattens 2,205 NULL-valued `floored` placeholder rows into one undifferentiated 13,621.** Honest at row level (`verification_pass_status='floored'`), undisclosed at cockpit level. | live tier breakdown §1.4 | **NOW** | §N.6 item 1 |
| **F-C21** | all 3 | **No serving surface in this batch declares `density_contract`** (`get_strength.ts`, `get_argala.ts`, `get_ashtakavarga.ts`, `get_dignity.ts`, `get_avasthas.ts`, `get_condition_composite.ts` — 0 occurrences each), so no census harness can assert their byte caps / facet / empty-reason discipline. `get_strength.ts`'s `total_available_basis` disclosure is exemplary and is exactly the thing that goes unasserted. | grep, all six files | **NOW** | §N.6 item 4 |
| **F-C22** | `ga_condition` | `get_condition_composite.ts:5` documents "90 rows"; live is 45/chart, 135 total. Stale doc figure on a live serving surface. | live | **NEVER-LATER** | §B.8 |
| **F-C23** | `ga_condition` | **Four L0 reference tables read with no declared upstream** (`bg_*` dignity ref, motion thresholds, combustion orbs, naisargika friendships). DAG understates real inputs. | `ga_condition_writer.py:606,635,657,684`; registry `depends_on` | **NOW** | §B.3 |
| **F-C24** | *(cross)* | `ga_yoga_firings.bhanga_active` is **NULL on 40 of 63** canonical rows. Honest, but no `bhanga_na_reason` discipline is enforced and a consumer reading `IS NOT TRUE` as "not cancelled" is wrong on those 40. Batch-C-adjacent (feeds F-C7). | live | **NEVER-LATER** (belongs to the `ga_yoga` batch) | §N.8 |

### 6.1 Positives worth preserving (do not "fix" these)

- `ga_strength` emits **zero** `two_pass_verified` rows and its docstring says exactly why
  (`ga_strength_writer.py:15-20`). Honest tier over a broadcast claim — §N.4/§N.8 exemplary.
- All three writers are **FROZEN-contract conformant**: `conn.commit()` and
  `update_asset_throughput` in `ga_strength_writer.py:1842-1850` are both gated on `owns_conn`,
  which is False on the orchestrator path (`pipeline/orchestrator/writers/ga_strength.py:16-22`
  passes `ctx.db_conn`). No writer commits, closes, or writes build state under the orchestrator.
- `get_strength.ts`'s `total` / `total_available` / `total_available_basis` triple
  (lines 241-274) is the best density disclosure I found in L1.
- `get_argala.ts`'s `all_zero` page flag and its prior total-`ORDER BY` fix (lines 16-19, 30-35)
  are both correct §N.6/§N.7 work.
- `estimated_seconds` is, for `ga_strength` and `ga_structural`, the measured historical median
  to one decimal — derived, not asserted.

### 6.2 Explicit uncertainty

- Writer attribution in §2.6 used substring matching over `ga_writers/*.py`; a category name can
  appear in a writer that only *reads* it. The 5,157 total is measured from the DB and is exact;
  the *attribution* of each category to `ga_structural` is high-confidence but not proven for
  every row. The 4,947 `rows_written` delta is from a 2026-08-10 build and the 98,542 count is
  from today, so the two are not from the same instant.
- F-C13 (`salience_formula_version = 'v1.0'` vs `salience_formula_v2`) is reported from the
  dominant stored value and the formula source; I did not enumerate every emitter's version
  literal. Treat as a lead, not a settled finding.
- I did not execute any MCP tool (`ganita_strength_get` etc.) — serving behaviour is inferred
  from source read plus direct SQL against the same tables, not from a live tool call.
- `graha_yuddha` contributes 0 rows on all three charts, so §3.6's floor-equality argument is
  demonstrated on charts where the one chart-dependent term happens to vanish. On a chart with a
  graha yuddha the count would exceed 2,880 — the finding is that the floor is a tautology *for
  the 2,880 part*, not that it can never be exceeded.
