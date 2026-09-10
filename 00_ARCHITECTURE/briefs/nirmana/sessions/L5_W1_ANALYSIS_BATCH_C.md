---
artifact: L5_W1_ANALYSIS_BATCH_C.md
canonical_id: NIRMANA_L5_W1_ANALYSIS_BATCH_C
version: "1.0"
status: CURRENT — W1 ANALYZE output, L5 (Mīmāṃsā)
session: L5
produced_on: 2026-09-05
scope: mi_kula · mi_gunanaka · mi_adhilepa · mi_bhara (families, multipliers, load-bearing, field weights)
method: >
  Read-only fresh-context analysis subagent against the plan §4 W1 rubric, the five doctrines,
  charter C12, and CLAUDE.md §N.4/§N.6/§N.7/§N.8. No repo write, no DB write. Includes the
  §N.8 determination on the two post-seal PROMOTED multipliers that the L5 session raised as
  finding F-L5-G.
---

# L5-W1 — Batch C: families, multipliers, load-bearing, field weights

## The §N.8 determination on `mi_gunanaka`'s promoted multipliers (F-L5-G, answered)

**Verdict: BOTH halves are true, and the defect is worse than either framing.** The events are real;
the *badge* is fabricated; and the seal's honesty label is stale in the permissive direction.

**1. What is an "observation"?** The chain is `phala_anchors → mi_bhavisya (predictions +
driving_signals) → mi_pramana (match against mimamsa_event_provenance) → mimamsa_calibration →
mi_gunanaka`.
- `mimamsa_event_provenance` for the canonical chart carries **64 rows, all `lel_source='db'`** (51
  `admissible_clean AND NOT held_out`, 13 `held_out`), dates 1984-02-05 → 2026-08-01. These are
  **real lived LEL events**, not synthetic. So the evidence is *not* pure self-scoring.
- **But `n_observations` does not count observations.** `mi_gunanaka.py:145-151` appends
  `composite_score` **once per entry in `driving_signals`**, and `mi_bhavisya.py:113-116` stamps
  **exactly the top-5 MSR signals per domain** into `driving_signals`. Arithmetic proof: canonical has
  **57** `mimamsa_calibration` rows; 57 × 5 = **285**; live `n_observations` = 271 (`fam_graha_natal`)
  + 14 (`fam_transit`) = **285 exactly**. `n_observations` is literally *5 × the number of
  prediction-event matches*, partitioned by family.
- So "271 observations" = **at most 57 prediction×event matches, drawn from at most 51 distinct real
  events** (one of which is the birth date itself). Pseudo-replication by a factor of 5, on top of
  match multiplicity.
- No verdict filter is applied: `composite_verdict` is SELECTed at `mi_gunanaka.py:104` and **never
  read**. Live verdict mix: **25 UNRESOLVED, 23 PARTIAL, 7 REFUTED, 2 CONFIRMED**. Twenty-five rows
  the adjudicator could not resolve are pooled as evidence identically to the two it confirmed.

**2. What does the promotion gate measure?** Volume alone, and one field cannot fail at all.
`mi_gunanaka.py:211`: `promotion = "promoted" if n >= 3 else "earning"`, and in the evidence branch
the tuple hardcodes `gate_passed=True` (literal, :222) and `confidence_high = n >= 5`. Applying
§N.8's test — *what code path would have to run and fail for this to read false?* — **`gate_passed`
has none: it is a Python literal `True` on every evidence-bearing row.** `promotion_status='promoted'`
requires only `n ≥ 3`, i.e. ≥1 calibration match. Nothing about verdict quality, hold-out, or negative
controls enters the gate.

**3. `held_out_validity='pass'` and `neg_control_clear=true` — real detectors?** **Neither. Both are
null-worthy.**
- `held_out_validity`: literal `"pass"` at :221. A **genuine hold-out partition exists** (13
  `held_out=true` provenance rows) and `mi_pramana._substep_match` deliberately excludes it — but
  **nothing ever scores against it.** The flag names a check the data supports and the code never
  runs. §N.7 item 4 exactly.
- `neg_control_clear`: literal `True` at :224, on **all 18 rows**. The decisive evidence is that the
  same database *already contradicts it*: `mimamsa_qa_eval` on the canonical chart holds **4 rows
  `check_type='negative_control'`, `status='not_implemented'`**, written by
  `mi_pariksha._substep_neg_control`, whose own comment (JL-019) says "the comparison is a tautology
  that can never fail… every row is reported `not_implemented` rather than a misleading 'pass'."
  **mi_pariksha tells the truth about the battery; mi_gunanaka asserts it passed.**
- Bonus, same class: `mi_gunanaka.py:126-141` carries an elaborate §N.8-citing comment about excluding
  rows "explicitly marked `'leaked'`". **No code path in the repo ever writes `'leaked'`.** Upstream,
  `mi_pramana.py:384` computes `leakage = "clean" if ev.admissible_clean and not ev.held_out else
  "held_out"` — but the match substep already filtered `WHERE admissible_clean=true AND
  held_out=false`, so **`'clean'` is tautological**, and all 64 provenance rows carry
  `disclosure_timing='unknown'`, the very field that would decide leakage.

**4. Is n=14 above the writer's own threshold?** The writer's thresholds are **n ≥ 3** (promoted) and
**n ≥ 5** (confidence_high). **The seal's "n ≥ 10 per domain" appears nowhere in the code.** Read
honestly, 14 slots ≈ ≤14 matches ≈ far fewer distinct events. Not defensible as stated.

**5. Why 2 promoted on canonical, 0 on `1c826d5a`?** **A real data difference, not build recency.**
`1c826d5a` has **56 predictions but zero `mimamsa_event_provenance` rows and zero
`mimamsa_calibration` rows** (no LEL for Abhinandan) → `evidence` dict empty → all 9 families take
the prior-only branch.

**Triage:** `L5-F-05` **MUST (correctness)**; `L5-F-06` **MUST (documentation)**.

---

### `mi_kula` — global signal-family registry (9 astrological + 2 negative-control families) + a 4-row negative-control battery

- **Purpose / doctrines:** The governing taxonomy every L5 pooling surface keys off. Serves
  **D-GROUNDING (P3)** (where `evidence_tier` / `soundness_basis` / `citation_refs` live) and
  **D-SALIENCE (P5)** (`prior_weight` is the per-family salience prior). Still the right instrument —
  but it is a *hand-authored catalogue*, not a derived one, and its grounding labels are wrong on two
  rows.
- **Dependencies (declared → real):** Declared `[bg_rules, bg_class_priors]`.
  - `bg_class_priors` → **REAL and live**. `_load_registry_priors` (`mi_kula.py:43-78`) reads
    `brahma_class_priors` and overrides `prior_weight`. Proven live: every one of the 9 catalog
    defaults differs from the served value (yoga 0.9→**1.4**, ashtakavarga 0.7→**0.95**, msr
    1.0→**1.4**, divisional 0.8→**0.95**, …).
  - `bg_rules` (`sutravali_rules`, 3,003 rows) → **FALSE EDGE. Never read.**
  - Hidden edge: none.
- **Leverage:** **One NULL-read.** `query_signal_families.ts:87` SELECTs `apply_point`; the writer's
  INSERT (`mi_kula.py:311-318`) never supplies it — live `count(apply_point)=0 / 11`. A
  *schema-vs-serve* gap rather than a lost computation, but the served column is dead weight.
- **Grounding:** Labelable, and **currently mislabelled**. Seven families are genuine `sruti`
  (`BPHS §3/§7/§36/§46/§49/§67`, `Saravali`, `Phaladeepika`, `Jaimini`, `Mansagari`, `Sarvartha
  Chintamani`). **Two are not:** `fam_msr_signal` (`citation_refs: ["MARSYS MSR §1"]`) and
  `fam_anchor` (`["MARSYS Phala §2"]`) are stamped `family_class='classical'`,
  `evidence_tier='CLASSICAL_CITED'`, `soundness_basis='astrological'` while citing **the instrument's
  own internal documents**. These are textbook `pratyaksa`. Per plan §2 D-GROUNDING, "a fabricated
  citation is a hard-floor violation; an honest `pratyaksa` label is success, not failure." The two
  negative-control families are honestly labelled (`NEGATIVE_CONTROL` / `scientific`).
- **Service:** Consumers real and plural — **writers:** `mi_gunanaka.py:120`, `mi_pariksha.py:368`,
  `mi_pariksha.py:565`; **serve:** `query_signal_families`
  (`marsys://tool/L5/query_signal_families`, registered `L5_mimamsa/index.ts:17`, present in
  `mcp_tool_registrations.generated.json:5533`, a D5-fanout member at `register_d5_fanout.ts:104`).
  Not built-but-unplugged. **Density/empty-reason: NO.** Drill depth: `binding_spec` names the source
  table → **L1 in 1 hop**, but as an unstructured JSON hint, not a resolvable fact_id.
- **Cost:** estimated **1s**. Measured: **UNKNOWN** — `asset_throughput.measurement_count = 0`,
  `rows_per_second` NULL, `build_run_assets.started_at` NULL for every L5 row. Recorded:
  `state='lit'`, `chart_id=NULL`, `rows_written=15`, `last_built_at 2026-08-02`. Writer shape: LIGHT.
- **Findings:**
  - `L5-F-01` **[MUST]** `fam_msr_signal` and `fam_anchor` carry `evidence_tier='CLASSICAL_CITED'` +
    `family_class='classical'` while citing MARSYS-internal documents. A classical-citation badge on a
    non-classical source. — *basis:* plan §2 **D-GROUNDING** + §N.7 item 6 — *evidence:*
    `mi_kula.py:186-212`; live `SELECT family_id, evidence_tier, citation_refs FROM
    mimamsa_signal_families`.
  - `L5-F-02` **[NOW]** `depends_on` declares `bg_rules`, which the writer never reads — a false DAG
    edge that makes every `sutravali_rules` rebuild spuriously invalidate `mi_kula`. — *basis:* plan
    §4 rubric item 2; O-wave WP-1/WP-2 — *evidence:* `grep -n "sutravali\|bg_rules" mi_kula.py` → no
    hits.
  - `L5-F-03` **[NOW]** "11" is **picked, not derived**. Against its own declared source space it is
    demonstrably coarse: `brahma_class_priors` holds **27 distinct `signal_type_class`** and **24
    distinct `source_subsystem`**; `bodha_msr_signals` holds **19 distinct classes**; canonical
    `chart_facts` holds **219 distinct `fact_category`**. All collapses into **at most 5 families in
    practice** — live `mimamsa_signal_adjustment`: `fam_graha_natal` 47,059 (94%), `fam_transit`
    2,871, `fam_yoga` 80, `fam_divisional` 49, `fam_msr_signal` 45; **4 of 9 families are never
    assigned to a single row.** The correct C12 disposition is a **derived**
    `expected_volume_formula` over the class/subsystem partition plus an attributed delta.
    — *basis:* C12 "derive, never pick" + "NULL is the defect".
  - `L5-F-04` **[NOW]** `integrity_check_sql IS NULL`; `target_floor = 0`. A real invariant is cheap:
    *every `family_id` in `_FAMILY_TO_PRIOR_KEY` resolves to a live `brahma_class_priors` row* (FULL
    JOIN, zero unmatched) **and** `family_class='negative_control' ⇒ prior_weight = 0 AND
    default_state='CONTROL_ONLY'` **and** `count(DISTINCT family_id) = count(*)`. Passes the C12
    **rewrite floor test**: it fails on a silent prior-lookup regression (the `except` at
    `mi_kula.py:71-77` currently degrades to catalog defaults with only a `logger.warning`, invisible
    to any check) — corruption a `count(*)=11` pin could never detect. Set `target_floor` to the
    achieved 11 per §N.4. — *basis:* C12 + §N.4.
  - `L5-F-05a` **[NOW]** `query_signal_families` serves `apply_point` as NULL for all 11 rows and
    declares no `empty_reason` / density facets. Drop the column from the projection or populate it.
    — *basis:* D-SERVICE (P8); §N.6 item 4.
  - `L5-F-05b` **[NEVER/LATER]** The `prior_weight` fallback path (registry lookup fails → silent
    hardcoded catalog value, warning-log only, no on-row provenance marker) would ideally stamp a
    `prior_source` column. Deferred: a schema addition on the calibration surface. — *basis:* plan
    §7.3; L5 mandate. Note the path is **dormant today** — all 9 families received live overrides.
- **W4 dispatch (WP-3, plan §3.3):** `mi_kula` is `domain='shared'`, `scope='global'`. Therefore:
  (a) an L5 **layer** plan must NOT silently sweep it in — it must appear with disposition
  `out_of_domain` unless explicitly included; (b) a **chart** rebuild must plan **zero** shared
  assets; (c) the only correct dispatch is a **`global`-scope run with `chart_id = NULL`** — exactly
  what its `asset_throughput` row records today. If W4 dispatches it inside the per-chart L5 tier it
  will (i) violate WP-3's acceptance criterion and (ii) `DELETE FROM mimamsa_signal_families`
  mid-build for **all** charts, since the writer's idempotency is a global unqualified DELETE
  (`mi_kula.py:308-309`). **Flag to the Conductor as a dispatch constraint, not a preference.** Same
  applies to `mi_vistara`.
- **Proposed route:** **`changed`** — F-01 is a row-value correction requiring a writer edit plus a
  global re-seed; F-02/F-03/F-04 are registry-side and land in the same PR.

---

### `mi_gunanaka` — per-chart learned multipliers over the 9 non-control signal families

- **Purpose / doctrines:** The one surface that turns calibration evidence into a weight. Serves the
  parked **P7** loop and, via the spine, **D-SALIENCE (P5)**. Right instrument for a *future* P7
  programme; today its structural honesty is compromised by fabricated flags.
- **Dependencies (declared → real):** Declared `[mi_pramana, mi_kula, bg_formula_constants]` — **all
  three real**, no false edges. **Hidden edge:** `mimamsa_predictions` (LEFT JOIN at :106-109, for
  `driving_signals`) — produced by **`mi_bhavisya`**, **not** in `depends_on`. The entire
  family-attribution of evidence flows through that join; without it every score would key to
  `"unknown"`. Real, load-bearing, undeclared. **Second write target:**
  `mimamsa_calibration_snapshot` (`_publish_snapshot`, :325-388) — an accretion table, correctly
  documented as a ratified §N.3 exception (F-188) and correctly reflected in `count_sql`. Live: 5 rows.
- **Leverage — the highest-value finding in this batch:** **A designed consumer reads NULL where the
  asset computed the answer.** `compute_spine_bundle.ts:127`:
  `const domainMultipliers = allMultipliers.filter(m => m['domain'] === domain)`.
  `mimamsa_multipliers.domain` is **NULL on every row** — the writer passes `None` at tuple index 5 in
  **both** branches (:216, :257). Live: `count(*), count(domain)` → **18, 0**. Therefore
  `domainMultipliers` is **unconditionally empty for every chart and every domain**, and the spine
  bundle's `calibration.multipliers` section ships empty forever, with **no `empty_reason`** for that
  section (it only fires when `signals.length === 0`, :159-163).
  The damning part: the sibling capability **already knows and deliberately refuses to do this**.
  `query_calibration.ts:168-171`: *"`mimamsa_multipliers.domain` is a real column, but filtering on it
  would EMPTY a populated section rather than narrow it wherever the writer left it NULL (global
  scope)."* — and reports `multipliers_with_domain` as measured data instead. The spine bundle
  re-introduces exactly the filter its own composed-from capability documented as forbidden.
- **Grounding:** Honestly `pratyaksa` and should stay so. The `prior_only` rows are a special case:
  their `applied_multiplier` **is** the L0 classical class prior restated verbatim, so those rows are
  `sruti`-derived-via-`bg_class_priors` and should carry the family's own tier by reference, not a new
  claim. **What must not survive is the empirical badge on rows that are not empirical.**
- **Service:** Real consumers exist. `query_calibration.ts:130-137` selects `promotion_status,
  gate_passed, kill_switch_state, divergence_from_classical` — i.e. **the honest disclosure fields ARE
  served**, the one thing keeping this from being a broadcast lie. `compute_spine_bundle.ts` (broken,
  above). `mi_adhilepa._load_multipliers` (:141-147). `mi_seva` table-existence probe only. **Not**
  built-but-unplugged. Density: `query_calibration` declares `domain_filtered_sections` /
  `domain_unfiltered_sections` / `multipliers_with_domain` — a genuinely good §N.6-item-4
  machine-readable density contract. Drill depth: `audit_trail` JSON → `mimamsa_calibration.prediction_id`
  → `mimamsa_predictions.driving_signals` → `bodha_msr_signals` → L1 = **>2 hops**.
- **Cost:** estimated **1s**. Measured: **UNKNOWN** (`measurement_count=0`). Recorded:
  `rows_written=9` per chart; `state='lit'` on `1c826d5a` (2026-08-12), `state='error'` on canonical
  (2026-08-21, `BLOCKED: upstream dependency(ies) mi_pramana did not complete`). Writer shape: LIGHT.
- **Findings:**
  - `L5-F-05` **[MUST]** Three flags on `mimamsa_multipliers` are asserted with no detector behind
    them: `gate_passed` (literal `True`, :222), `held_out_validity` (literal `"pass"`, :220),
    `neg_control_clear` (literal `True`, :224, on **all 18 rows**). The DB itself contradicts the
    third: `mimamsa_qa_eval` holds 4 `negative_control` rows with `status='not_implemented'` on the
    same chart. A real hold-out partition exists (13 rows) and is never scored. These must become
    **null / an honest named state**, not `pass`/`true`. — *basis:* **§N.8** + **§N.7 items 4 and 6**
    — *evidence:* `mi_gunanaka.py:220-224` (and :262-266 for the prior-only branch); SQL;
    `mi_pariksha.py:582-586` (JL-019).
  - `L5-F-06` **[MUST]** `L5_SEAL_AND_SHIP_REPORT_v1_0.md` §1/§4 asserts "all 9 multipliers carry
    `promotion_status='prior_only'`" and "`gate_passed=false` for all 9". Live: canonical carries
    **2 `promoted`/`gate_passed=true`** rows (`updated_at 2026-08-13`, post-seal). The STRUCTURAL
    honesty label is stale **in the permissive direction**. — *basis:* §N.8; L5 mandate item 1.
  - `L5-F-07` **[MUST]** `compute_spine_bundle.ts:127` filters on the always-NULL `domain` column,
    zeroing `calibration.multipliers` for every chart and every domain, with no `empty_reason`,
    against the explicit written warning in the capability it composes from. — *basis:* plan §4 rubric
    item 3 + **§N.6 item 3** + **D-SERVICE**.
  - `L5-F-08` **[NOW]** `evidence_factor` on the 16 prior-only rows is `prior_weight / 2.0` (:250) — a
    plausible-reading number in a column named for evidence, on rows with `n_observations = 0` (live:
    0.475, 0.55, 0.575, 0.6, 0.7). Likewise `float(cr.get("composite_score") or 0.5)` at :150
    substitutes a neutral 0.5 for a missing score. Both should be NULL. — *basis:* **§N.7 item 6** +
    §N.8.
  - `L5-F-09` **[NOW]** `n_observations` counts driving-signal *slots*, not observations (proof: 285 =
    57 × 5). `composite_verdict` is selected and never used, so 25 UNRESOLVED + 7 REFUTED rows pool
    identically with 2 CONFIRMED. Rename/redefine honestly (`n_signal_slots`) or de-duplicate to
    distinct `(prediction_id, event_id)`. — *basis:* §N.7 item 1 + §N.8.
  - `L5-F-10` **[NOW]** `expected_volume_formula IS NULL`, `integrity_check_sql IS NULL`,
    `target_floor = 0`. Both **derivable exactly**: expected rows per chart =
    `(SELECT count(*) FROM mimamsa_signal_families WHERE is_active AND default_state <> 'CONTROL_ONLY')`
    = 9 today, confirmed live (9 × 2 = 18). A real invariant surviving the C12 rewrite-floor test:
    *no `mimamsa_multipliers` row whose `target_ref` is missing from `mimamsa_signal_families`* (FULL
    JOIN, both directions) AND *`n_observations = 0 ⇒ promotion_status='prior_only' AND
    applied_multiplier = the family's `prior_weight`*. The second clause fails on real corruption a
    count pin cannot see. — *basis:* C12 + §N.4.
  - `L5-F-11` **[NOW]** Undeclared dependency on `mi_bhavisya`. — *basis:* rubric item 2; WP-1/WP-2.
  - `L5-F-12` **[NEVER/LATER]** Everything that would make the promotion gate *real* — a hold-out
    scorer, a synthetic-injection negative-control harness, a leakage detector that can write
    `'leaked'` — is P7 machinery. Do **not** build it here. Record in the deferred register alongside
    the JL-019 residual. — *basis:* L5 mandate; plan §7.3.
- **Proposed route:** **`changed`** — F-05 and F-07 are correctness MUSTs; F-05 requires a writer edit
  + per-chart rebuild (the flag values live in stored rows), F-07 is a serving-plane (TS) fix.

---

### `mi_adhilepa` — calibration overlay across L1–L4 (4 adjustment tables) + a 9-row "load-bearing" map

- **Purpose / doctrines:** Two jobs in one asset. (a) The **overlay**: project family multipliers onto
  every L2 signal / L1 fact / L3 convergence / L4 anchor — ~112k rows per chart. (b) The
  **load-bearing map** (`mimamsa_load_bearing`, the declared `target_table`): interpretability
  metadata answering "which signals carry the weight of this conclusion." (a) serves the parked P7
  loop; (b) is aimed at **D-SERVICE (P8)** / **D-SYNTHESIS (P4)** drill. **The instrument for (b) is
  wrong.**
- **Dependencies (declared → real):** Declared `[mi_gunanaka, bo_laksana, ka_sangam, ph_nimitta,
  ga_positions]`.
  - `mi_gunanaka` → `mimamsa_multipliers` (:141-147) ✓ — **and it is the ONLY input to the
    load-bearing map.**
  - `bo_laksana` → `bodha_msr_signals` (:230-238) ✓ (overlay only)
  - `ka_sangam` → `kala_convergence` (:293-298) ✓ (overlay only)
  - `ph_nimitta` → `phala_anchors` (:313-317) ✓ (overlay only)
  - `ga_positions` → **narrower than real.** The writer reads
    `SELECT fact_id, fact_category FROM chart_facts WHERE chart_id=%s` **unfiltered** (:267-273) — the
    *entire* fact set (219 distinct categories), not just `ga_positions`' three. **Hidden edges** on
    the remainder.
  - Also an implicit edge on `mi_kula`, transitively satisfied via `mi_gunanaka`.
  - **Net: 4 of 5 declared deps do not feed the declared `target_table` at all.**
- **Leverage:** No NULL-reading consumer for `mimamsa_load_bearing`. **But the four overlay tables are
  effectively unplugged**: 224,746 live rows, and **no serving-plane reader** (`grep` over
  `platform/src` + `platform-mcp/src` returns only the writer, migrations, and `assetClearSpec.ts`).
  They are documented as GATED in `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` per `query_load_bearing.ts:4-14`
  — a **recorded disposition**, so disposition-covered rather than a bare P8 violation, but it should
  be re-confirmed at W2.
- **Grounding:** `pratyaksa` — and the honest label exposes the problem. **"Load-bearing" here is not a
  sensitivity analysis.** `mi_adhilepa.py:333-352`: take family multipliers with `applied_multiplier
  >= 1.0`, sort desc, take `[:5]`, set `sensitivity = applied_multiplier / 2.0`, and assign `role`
  **by rank position** (`i == 0 → 'load_bearing'`, `i < 3 → 'supporting'`, else `'redundant'`). There
  is no conclusion (`conclusion_id = f"concl_{target_ref}"` — the family's own name), no signal
  (`signal_id = target_ref` — the family again), and no measured dependence of anything on anything.
  `sensitivity` is a rescaled prior, not `∂conclusion/∂signal`.
  Live consequence, the sharpest single fact in this batch: **on the canonical chart,
  `fam_graha_natal` — the ONE family with real evidence (n=271) and 94% of all signal overlays — is
  EXCLUDED from the load-bearing map**, because shrinkage moved it to 0.9924, just under the hardcoded
  1.0 cut. Meanwhile `fam_yoga` (n_observations **0**, 80 overlay rows) is declared **THE**
  `load_bearing` signal. The map is also chart-independent: the two charts' 9 rows are identical
  except for that one exclusion.
- **Service:** `query_load_bearing` (registered `L5_mimamsa/index.ts:33`, present in
  `mcp_tool_registrations.generated.json:4056`). This capability is a **model of the D-SERVICE
  standard** — bounded `MAX_LIMIT=100`, `total_matching`, `more_available`, a real parameterised
  `empty_reason`, and `provenance.tables`. Density + empty-reason: **YES**. Drill depth: `signal_id`
  is a family_id, not a `bodha_msr_signals.signal_id` — a caller cannot drill from a load-bearing row
  to a signal at all. **Drill depth: ∞ (broken).** Unplugged: no (served); but the *content* is hollow.
- **Cost:** estimated **11s** — **wrong by roughly an order of magnitude and provably so.**
  `asset_throughput.rows_written` = **112,270** (canonical) / **112,481** (`1c826d5a`), reconciling
  exactly with live per-chart counts (50,104 + 61,523 + 500 + 139 + 4 = 112,270). Writer shape: LIGHT
  (no substeps) but scans the full `chart_facts` set (~138k rows) plus ~50k MSR signals, and issues
  `executemany` of ~112k tuples across 4 tables inside one transaction. Measured wall-clock:
  **UNKNOWN** — `measurement_count=0`, `build_run_assets.started_at` NULL. `writer_timeout_seconds` is
  10,800. **What would settle it:** one instrumented rebuild with O-wave receipt capture.
- **Findings:**
  - `L5-F-13` **[MUST]** `mimamsa_load_bearing` reports rank-ordered prior weights as measured
    `sensitivity` and `role`. No sensitivity is computed; `role` is a list index. The
    `applied_multiplier >= 1.0` cut excludes the only empirically-grounded family on the canonical
    chart while promoting an n=0 family to `role='load_bearing'`. — *basis:* **§N.8** (`role` cannot
    disagree with rank) + **§N.7 item 2** + **D-SALIENCE (P5)** — *evidence:*
    `mi_adhilepa.py:333-352`; live 9 rows; `applied_multiplier = 0.9924` for `fam_graha_natal`.
  - `L5-F-14` **[MUST]** `kala_convergence` overlay is `LIMIT 500` **with no ORDER BY** (:293-298)
    against **14,868** live convergences on the canonical chart (17,957 on `1c826d5a`) — a silent,
    nondeterministic 3.4% sample, undisclosed on-row and in the result notes. The writer's own comment
    at :265-274 records that exactly this defect ("its `LIMIT 200` with no `ORDER BY` was additionally
    nondeterministic") was fixed for `chart_facts` — and left standing here. — *basis:* **§N.6** +
    §N.8 — *evidence:* live `mimamsa_convergence_adjustment` = exactly 500 per chart.
  - `L5-F-15` **[NOW]** 9 rows is **not a full result** — it is `≤5 per chart × 2 charts`, capped by
    `[:5]` and further cut by the `>= 1.0` threshold (canonical 4, `1c826d5a` 5). Any floor or volume
    expectation must be written as `min(5, |families with applied_multiplier >= 1.0|)` per chart.
    — *basis:* C12.
  - `L5-F-16` **[NOW]** Declared `ga_positions` understates the real edge (219 categories read).
    Narrow the writer's SELECT or widen `depends_on`. — *basis:* rubric item 2; WP-1/WP-2.
  - `L5-F-17` **[NOW]** `estimated_seconds = 11` against ~112k rows written and a ~190k-row read. In
    W4 this asset must be scheduled on measured cost. — *basis:* plan §4 rubric item 7 + §8.
  - `L5-F-18` **[NOW]** `integrity_check_sql IS NULL` / `expected_volume_formula IS NULL` /
    `target_floor = 0`. Proposed real invariant: *every `mimamsa_load_bearing.signal_id` resolves to a
    `mimamsa_multipliers.target_ref` for the same `chart_id`* (FULL JOIN, zero unmatched) **and**
    *`role='load_bearing'` appears at most once per `(chart_id, conclusion_id)`* **and** *`sensitivity`
    is monotone-decreasing with role rank*. Passes the rewrite floor test: fails if the multiplier set
    changes without a re-overlay — the actual live risk. — *basis:* C12; §N.4.
  - `L5-F-19` **[NOW]** `mimamsa_load_bearing.signal_id` holds a **family_id**, so `query_load_bearing`'s
    rows cannot drill to a signal or to L1 — the drill contract is unsatisfiable as data is shaped. At
    minimum the capability must disclose that `signal_id` is a family reference. — *basis:*
    **D-SERVICE (P8)**.
  - `L5-F-20` **[NEVER/LATER]** A genuine sensitivity analysis is P7 machinery and out of scope. The
    in-scope fix for F-13 is **honest relabelling** (`role → prior_rank`, `sensitivity →
    prior_weight_scaled`, or NULL) — not building the analysis. — *basis:* L5 mandate; plan §7.3.
- **Proposed route:** **`changed`** — F-13/F-14 are correctness MUSTs requiring writer edits; the asset
  then needs a per-chart rebuild (also required independently: canonical `state='error'`).

---

### `mi_bhara` — Stage 9 of the temporal-field pipeline: fits field weights against the LEL, publishes skill + goodness-of-fit

- **Purpose / doctrines:** Serves **D-TIME (P6)** — the calibration end of the hazard-field pipeline
  and the CIRCULARITY GUARD's single LEL aperture. Also the deferred **P7** loop. **This is by a
  distance the most honest writer in the batch**: named non-fatal degradation states
  (`kala_field_absent`, `no_lel_events`, `biographical_join_deferred`, `skill_tables_absent`), an
  explicit refusal to fabricate a fit basis (:230-237), an `"unpinned"` sentinel chosen to be
  *visibly wrong* rather than plausible (:383-391), a deterministic non-RNG null grid so hash-replay
  holds (:366-375), and §N.5-cited reads-not-recomputes throughout.
- **Dependencies (declared → real):** Declared `[ka_kshetra]` — real (`kala_field` at :119, :395).
  **Four undeclared real reads:** `life_events` — the LEL (`services/mi_bhara/db.py:137-148`), the
  single most load-bearing input, undeclared; `brahma_prospective_ledger` (:162-167);
  `kala_field_weight_versions` (`weights.py:74-82`, read-only); `insight_units` (:358). Also writes
  `kala_field_skill` and `kala_field_gof` (migration 497).
- **Leverage — the finding the brief asked for:** **The writer does NOT own
  `kala_field_weight_versions`. It has never written a row to it, and the code that would is
  unreachable.**
  - `services/mi_bhara/db.py:223` defines `insert_weights_version` and :272
    `supersede_previous_active`. `grep -rn` returns **only the two definitions and one docstring
    mention — zero callers, not even in tests.** Built-but-unplugged.
  - `_fit_and_publish` states why (`mi_bhara.py:230-237`): the θ-independent per-segment basis is
    Lane C's stage-4 emission and does not exist yet, so the method "publishes skill and GOF against
    the AS-BUILT field… It does not fabricate a basis in order to look complete." **Phase 2 (FIT → new
    weights version) is deliberately not executed.** Correct call, honestly documented — but the
    declared `target_table` describes an aspiration, not a behaviour.
  - Live proof: `kala_field_weight_versions` holds **exactly one row**, `version_id='v0_classical'`,
    `scope='global'`, `fitted_from_chart_id=NULL`, `activated_at 2026-07-30 18:11 UTC` — the
    **migration-491 seed**, predating any `mi_bhara` run. `kala_field_weights` holds 29 rows, also
    seeded.
  - The registry half-knows: `count_sql` is `SELECT COUNT(*) FROM kala_field_skill WHERE chart_id=$1`
    — **a different table from `target_table`.** `asset_registry_seed.ts:2990` even carries a comment
    acknowledging the split. Live `kala_field_skill` = 7 rows (all canonical), `kala_field_gof` = 6.
- **Write-set collision with L3 — the adjudication question:** **A true shared write-set exists, but
  the collision risk is on the *read* side, and it is real.**
  - `kala_field_weight_versions` is **created and seeded by migration 491** (L3/Lane C's), **read by
    `ka_kshetra`** (`services/ka_kshetra/stage4_field.py:1099-1105`, which halts if absent), and
    **read by `mi_bhara`** (`weights.py:79`). Today **nothing writes it at runtime.**
  - The intended design is an explicit cross-build cycle (`weights.py:14-30`): `ka_kshetra → mi_bhara
    → ka_kshetra` would be a DAG cycle `topoSort` rejects, so **the loop is closed by version pin, not
    by DAG edge**. `assert_no_weights_cycle` positively asserts `'mi_bhara' NOT IN
    ka_kshetra.depends_on` **and** that a plan containing `{ka_kshetra, mi_bhara, mi_sankalpa}`
    topo-sorts.
  - **The W3/W4 hazard:** if L3 touches `ka_kshetra`, migration 491, or the pin-resolution path — or
    if either session adds the "obvious missing" `depends_on` edge in either direction — the
    acyclicity guard breaks **every plan containing either asset**, i.e. every future chart build. And
    when `insert_weights_version` is eventually wired, `mi_bhara` will begin mutating `status` on rows
    `ka_kshetra` pins mid-build; `weights.py`'s sub-rule 5 (resolve-once-in-`plan_substeps`) is the
    only thing preventing a straddling build from writing one `kala_field` snapshot under two models.
  - **Recommendation: YES — raise a Conductor adjudication issue for write-set arbitration with L3.**
    Specifically: (a) declare `kala_field_weight_versions` **L3-owned, L5-read-only for this
    campaign**, and correct `mi_bhara.target_table` to `kala_field_skill`; (b) put migration 491,
    `stage4_field.py`'s pin read, and `services/mi_bhara/weights.py` on a **shared-surface list**
    neither session edits without the other's ack; (c) record the acyclicity guard as a campaign-level
    invariant with `assert_no_weights_cycle` as its detector.
- **Grounding:** `pratyaksa`, correctly and explicitly. The one `sruti`-adjacent element — the
  "classical structural priors" the shrinkage targets — is inherited by version pin from migration
  491, i.e. **referenced, not restated** (§N.5-conformant).
- **Service:** `kala_field_skill` / `kala_field_gof` — serving-plane readers **UNKNOWN**; `grep`
  surfaced only `kala_views/priority.ts` in the neighbourhood, unconfirmed. **Assessment: at least
  partially built-but-unplugged, pending W2 confirmation.**
- **Cost:** estimated **2s**. Measured: **UNKNOWN**, and the recorded state is contradictory.
  `asset_throughput`: `rows_written=0`, `state='error'` on **both** charts. **Yet `kala_field_skill`
  holds 7 rows and `kala_field_gof` 6, all canonical** — so a *successful* run happened and its state
  was later overwritten by a blocked one. Writer shape: LIGHT, `has_substeps=False`, but it integrates
  over segments drawn from an **11,012,657-row `kala_field`** and runs a bootstrap per event class. 2s
  is not credible.
- **Findings:**
  - `L5-F-21` **[MUST]** `target_table = 'kala_field_weight_versions'` is a table this writer has
    never written and whose write path has **zero callers**. Its `count_sql` already counts a
    different table. The registry declares a write-set the asset does not have — misleading WP-3
    disposition planning, staleness propagation, and cross-layer write-set arbitration. Correct
    `target_table` to `kala_field_skill` (+ `kala_field_gof`); leave `kala_field_weight_versions`
    documented as an L3-owned **read**. — *basis:* §N.8 + plan §3.3 WP-3 + D-SERVICE.
  - `L5-F-22` **[MUST]** Raise a **Conductor adjudication issue** for `kala_field_weight_versions` /
    migration 491 / `weights.py` / `stage4_field.py` as a shared L3↔L5 surface. Collision is latent
    today but the acyclicity guard is load-bearing for **every** future chart build. — *basis:* C12 +
    plan §4 W3 (disjoint write-sets) + D-TIME.
  - `L5-F-23` **[NOW]** `target_floor IS NULL` is **honest, but for the wrong reason, and must be
    re-anchored.** Honest because the correct floor for `kala_field_weight_versions` is genuinely
    zero-from-this-writer. Once `target_table` is corrected (F-21), the floor becomes the achieved
    `kala_field_skill` count, itself **derivable**: `|event_classes with ≥1 field segment| + 1` — live
    7. — *basis:* §N.4 + C12.
  - `L5-F-24` **[NOW]** Four undeclared real reads. The `life_events` omission is the serious one — the
    LEL is this asset's primary input and the CIRCULARITY GUARD's whole subject, yet the DAG cannot see
    it. — *basis:* rubric item 2; WP-1.
  - `L5-F-25` **[NOW]** `asset_throughput` reports `state='error'`/`rows_written=0` on both charts
    while 13 rows of its real output exist for the canonical chart — a build-state signal that
    disagrees with the data. Re-derive state from a real detector (the O-wave WP-1 receipt).
    — *basis:* **§N.8 instance 4** (same defect class, inverted: here a *failure* signal outlives a
    success).
  - `L5-F-26` **[NOW]** `integrity_check_sql IS NULL`. Proposed real invariant: *for every
    `(chart_id, weights_version, field_snapshot_id)` in `kala_field_skill`, the referenced
    `weights_version` exists in `kala_field_weight_versions`*, **and** *no row carries
    `field_snapshot_id='unpinned'` while a non-null `kala_field.field_snapshot_id` exists for that
    chart* — i.e. the honest sentinel is only used where it is honest. Passes the rewrite floor test:
    fails on a straddled build (the `weights.py` sub-rule-5 hazard). — *basis:* C12; §N.5.
  - `L5-F-27` **[NEVER/LATER]** Wiring `insert_weights_version` requires Lane C's stage-4 basis columns
    and is P7/ṢAḌ-DARŚANA work. The writer's refusal to fabricate a basis is correct current behaviour
    and should be **recorded as deliberate**, not carried as a defect. — *basis:* L5 mandate; plan §7.3.
- **Proposed route:** **`changed`** — registry-only for the MUSTs, no writer edit needed; F-22 is an
  adjudication issue, not code. If the Conductor prefers to hold the registry correction pending L3
  arbitration, fall back to **`probe`** and re-route at W2.

---

## Batch notes

1. **The batch splits cleanly into two moral halves.** `mi_bhara` was written to the §N.7/§N.8
   standard — named degradation states, a visibly-wrong sentinel over a plausible fake, an explicit
   refusal to fabricate a fit basis, deterministic nulls for hash-replay. `mi_gunanaka` and
   `mi_adhilepa` were not: between them they carry **five** literal-valued flags/grades that no code
   path can make false (`gate_passed`, `held_out_validity`, `neg_control_clear`, `role`,
   `sensitivity`). Same layer. The difference is authorship era, and it is the clearest argument in
   this batch for the earned-signal doctrine being applied as a *lint*, not a review habit.

2. **The system already contains its own contradiction, in one database.** `mi_pariksha` writes
   `mimamsa_qa_eval` rows saying `negative_control | not_implemented` and documents in-code (JL-019)
   that the comparison "is a tautology that can never fail." `mi_gunanaka` writes
   `neg_control_clear = true` on every row of the surface those controls exist to police. Two L5
   writers, same chart, same build, opposite claims about the same check. **Any W5 mechanical script
   should include a cross-writer flag-consistency check** — this class of defect is detectable by SQL
   alone.

3. **A dead §N.8 comment is worse than no comment.** `mi_gunanaka.py:126-141` carries a careful,
   correct, §N.8-citing rationale for admitting `not_assessed` rows and excluding `'leaked'` ones.
   `'leaked'` is written by **nothing in the repo**, and upstream `mi_pramana.py:384` computes
   `leakage` tautologically. The comment is now load-bearing *documentation of a safeguard that does
   not exist* — it reads to a future maintainer as evidence the path was thought through and is safe.
   Worth a doctrine note: **a §N.8 rationale should name its detector, and if the detector is absent,
   say so in the same breath.**

4. **The `domain`-column NULL is a two-consumer story with opposite outcomes.** `query_calibration`
   met the NULL, understood it, refused to filter, and published `multipliers_with_domain` as measured
   data — exemplary §N.6-item-4 conduct. `compute_spine_bundle`, which *composes from that very
   capability*, then applied the filter anyway and silently zeroes the section for every chart. The
   lesson for W2: **a composing surface can re-introduce a defect its source deliberately avoided**,
   and nothing in the current test suite catches it (`compute_spine_bundle.test.ts` mocks
   `FROM mimamsa_multipliers` to `{ rows: [] }`, so an always-empty result is indistinguishable from
   the fixture).

5. **Two assets are chart-independent while presenting as per-chart.** `mimamsa_load_bearing` is
   byte-identical across the two built charts except for one threshold exclusion;
   `mimamsa_multipliers` is 16/18 global-prior restatements. Neither is wrong to exist — but W2 should
   ask whether `domain='chart'` / `scope='per_chart'` is the honest scope declaration for surfaces
   whose content is currently global, and whether WP-2's delta-skip will correctly recognise that a
   chart rebuild changes nothing in them.

6. **All four assets have `integrity_check_sql IS NULL`, `catalog_status='DRAFT'`, and
   `expected_volume_formula IS NULL` — and all four have a real, derivable volume formula and a real
   invariant available** (F-04, F-10, F-18, F-26). None needs a `count(*) = N` pin. Two of the four
   volumes are *exactly* derivable and the derivation was verified against live data: `mi_gunanaka` =
   `|active non-control families|` per chart (9, confirmed 9×2=18) and `mi_kula` = `|families| +
   |controls|` (15, matching `rows_written`).

7. **Cost data and W4 scheduling.** *(Note 7 as originally written claimed
   `build_run_assets.started_at` is NULL for every L5 row. **That claim is FALSE and is corrected
   here by the L5 session**, which re-measured directly: `started_at` is populated on 38–45 rows per
   L5 asset, and batches B and D were right to quote measured means from it. The batch generalised
   from a bad sample. The original note's practical warning, however, was correct — and understated.)*

   `asset_throughput.measurement_count = 0` and `rows_per_second IS NULL` for all four assets, so
   that surface carries nothing. But `build_run_assets` does, and the measured picture is worse than
   this batch guessed:

   | asset | registry `estimated_seconds` | measured avg | measured max | tail error |
   |---|---|---|---|---|
   | `mi_adhilepa` | 11 | **31.2 s** | **843.1 s** | **77×** |
   | `mi_bhara` | 2 | **17.3 s** | **596.5 s** | **298×** |
   | `mi_pariksha` | 2 | 4.2 s | 32.9 s | 16× |
   | `mi_bhavisya` | 2 | 2.7 s | 15.6 s | 8× |

   **W4 scheduling for L5 must not consume `estimated_seconds` as if measured** — that conclusion
   stands, and `mi_adhilepa` and `mi_bhara` are the two assets that would break a slot plan built on
   the registry's numbers. The O-wave's universal receipt capture is the campaign-wide fix; the
   per-asset correction lands in L5-W3.

8. **Three charts exist in the build state, not two.** `cb73cd3d-9eba-4220-9902-0de91566e980` appears
   in `asset_throughput` (`mi_adhilepa`, `state='error'`, BLOCKED on `ph_nimitta`, 2026-08-07) and
   holds 2,540 `kala_convergence` rows, but has no L5 data. Worth a one-line disposition at W2 so it
   does not surface as an unexplained partial during the capsule audit.
