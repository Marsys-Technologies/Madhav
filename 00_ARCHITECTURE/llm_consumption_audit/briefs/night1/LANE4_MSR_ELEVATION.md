---
artifact: NIGHT1_LANE4_MSR_ELEVATION
type: IMPLEMENTATION BRIEF (Sonnet-executable, self-contained)
version: 1.0
status: READY
campaign: Doctrine Campaign D-1 / Night-1
lane: L4 — MSR elevation (bo_laksana → bodha_msr_signals)
depends_on_lanes: LANE2 (merged — ratification_factor + valence rows come from chart_vichara)
register_rows: CR-81, CR-82 (→ CR-65 root), CR-83 (→ CR-54 root), CR-45, CR-76/77 (as AMENDED), CR-55 (weakest_graha, absorbed here — see §1.6)
design_ref: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §11 (all five mechanics + the ratification-aware weighting definition)
---

# LANE 4 — MSR elevation: live class-priors, ratification-aware tiers, judged valence, subject-bearing headlines, position-class resolution

## 0. Why (design §11, quoted)

> **Why it under-delivers (five located mechanics, not vague tuning):** 1. class-prior dead (`class_prior=1.0` literal, `brahma_class_priors` never queried). 2. blanket **tier ceiling** force-caps any `*_per_varga` or non-D1 fact at `supporting` — the varga layer is *structurally forbidden* from ranking high. 3. valence is a keyword-substring heuristic. 4. special-lagna/chara-karaka/arudha/KP/tajaka facts **ingested-then-starved** — position-class facts carry no graha/house resolution → default shadbala/dignity/bindus → sink to background. Fix = subject resolution + un-capping, not ingestion. 5. subject-anonymous headlines by design.
>
> **Elevate:** activate class-priors as data; valence from the §4 functional-lordship pass; **tiers from percentile distribution** (chart_defining ≈ top 1–2%) with the varga ceiling replaced by **ratification-aware weighting**; subject-bearing headlines; graha/house resolution for position-class facts… MSR then becomes the single judged, ranked corpus every surface trusts.

## 1. Exact scope — files and verified line anchors (they will drift; re-grep first)

- `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py` (2,211 lines)
- `platform/python-sidecar/bodha_writers/formulas.py` (586 lines — `SalienceInputsV2` + `salience_formula_v2` at ~:495–586)
- one additive migration on `bodha_msr_signals` (§5)
- asset contract UNCHANGED: `bo_laksana` stays the registered writer for `bodha_msr_signals`; §N.2 rails all hold (ctx.db_conn, never commit, delete-then-insert per chart, no asset_throughput).
- **DAG addition:** `bo_laksana.depends_on` must gain `ga_vichara` in `asset_registry` (same migration).

**Ground-truth corrections to the register you must respect (verified 2026-07-13):**
- `_tier_ceiling_for` is at **`bo_laksana.py:556-569`**, NOT `formulas.py:556-569` as CR-82's evidence cites. Tier assignment call site: `bo_laksana.py:~1370-1373` (`_signature_tier(computed_salience, _tier_ceiling_for(fact_cat, varga_id))`).
- `class_prior=1.0` literal: `bo_laksana.py:~1302-1306` with the comment "class_prior defaults to 1.0 until brahma_class_priors is queried per-substep in a future optimization pass" — tonight IS that pass.
- `_infer_valence`: `bo_laksana.py:269-282` (frozenset categories + `_MALEFIC_VALUE_SUBSTRINGS`/`_BENEFIC_VALUE_SUBSTRINGS`).
- `_build_headline_text`: `bo_laksana.py:~510-519` — builds from category/key/value only; `fact_subject` never enters.
- `_FLOOD_PRONE_FAMILIES` + `RATIFIED_FLOOD_CAP=12`: `bo_laksana.py:79-93`. The flood-collapse mechanism is GOOD (keep it — it's the §N.6 family-collapse precedent); only its tier-ceiling coupling changes.

## 2. Change 1 — activate class_prior as data (CR-81)

At the fetch stage of each substep, load `brahma_class_priors` once into a dict (the table exists; writer `bg_class_priors.py`, seed `brahmagyan/l0_class_priors.py` — read the seed to learn the key column: it will be a signal-class or fact-category key; match on whatever key the table actually uses, joined to the fact's category/signal class). Pass `class_prior=priors.get(key, 1.0)` into `_compute_salience` instead of the literal. Missing key → 1.0 **and** `inputs_complete=False` is NOT triggered by this (priors are optional by design) — but count misses and report the hit-rate in `WriterResult.notes` (if <50% of signals get a real prior, the key-join is wrong; stop and debug rather than shipping a silently-inert term again).

## 3. Change 2 — retire the tier ceiling; ratification-aware weighting + percentile tiers (CR-82 → CR-65)

Design §11 definition (quoted, binding — same text Lane 2 implements the producer side of):

> replace the flat "cap any non-D1 fact at `supporting`" rule with a multiplier `ratification_factor ∈ [0.6, 1.4]` applied to a per-varga fact's salience, `= 1.0 + 0.2 × (agreeing_operative_vargas − opposing_operative_vargas)` over the domain's operative varga set… A 2nd-lord dignity that holds across D1+D2+D9+D11 is *amplified* (approaches 1.4 and may reach `major`/`chart_defining`); one that flips sign between vargas is *damped* toward 0.6 and additionally emits a **`varga_ratification_divergence` signal** (CR-57)

Implementation:
1. Load `chart_vichara` rows `vichara_family='varga_ratification'` for the chart (Lane 2's output) into a lookup keyed by (subject, domain). For a per-varga fact whose subject resolves to a graha/lord with a ratification row in any of the fact's affected domains, multiply `computed_salience` by that `ratification_factor` (use the max-magnitude deviation from 1.0 across the fact's domains; record which domain's factor applied). Store the factor in the new column (§5). Facts with no ratification row → factor 1.0, column NULL.
2. **Delete the varga clause of `_tier_ceiling_for`** (the `endswith("_per_varga")` cap and the `varga_id not in ("D1","")` cap). KEEP a ceiling ONLY for flood-rollup aggregate signals (the `_FLOOD_PRONE_FAMILIES` rollups are genuinely one-facet aggregates; capping THOSE at `supporting` stays — the design's target is the varga cap, and un-capping 15,660 rashi-drishti boilerplate rows would recreate CR-65 in mirror image).
3. **Tiers from percentile distribution** (design: "chart_defining ≈ top 1–2%"): after all signals for the chart are computed (bo_laksana already has a second pass for `specificity`/`salience_pctl_in_class` — attach here), assign `signature_tier` by percentile of post-ratification salience within the chart: `chart_defining` = top 1.5% (design's 1–2% midpoint; make it a module constant), `major` = next 8.5% (i.e. top 10% cumulative), `notable` (if the existing `_TIER_ORDER` has such a tier — READ `_TIER_ORDER` and map onto the tiers that exist; do not invent tier names) …, `supporting` = the remainder. The flood-rollup ceiling from (2) still applies after percentile assignment.
4. **Divergence signals (CR-57):** for each `chart_vichara` row with `vichara_family='varga_ratification_divergence'`, emit a first-class MSR signal (signal class `varga_ratification_divergence`, valence from the divergence direction, `constituent_facts_array` = the vichara row's constituent fact ids, headline = the vichara row's `value_text`). Salience: run it through `salience_formula_v2` with the D1 subject's real shadbala/dignity inputs and `class_prior` from the priors table (seed a prior for this class in Lane 2's constants if absent → default 1.2, cited as design-§11-construction "high salience by construction").

## 4. Change 3 — judged valence (CR-83, CR-54-as-amended)

Replace the body of `_infer_valence` usage for lord-link and dignity-bearing signals: when a `chart_vichara` `valence_pass` row exists for (actor subject, target, varga), use its `value_text` mapped to MSR's valence vocabulary (strong_benefic/benefic → `benefic`; strong_malefic/malefic → `malefic`; else `neutral`) and store the signed `value_num` in `epistemic_jsonb.judged_valence`. When no vichara row exists (non-link facts: pure positions, panchanga, etc.), fall back to the existing keyword heuristic **with** `epistemic_jsonb.valence_source = "keyword_heuristic_v1"` vs `"ga_vichara_v1"` — the fallback must be visible, never silent (CR-42 class: silent degradation is the estate's worst defect family). Do not delete `_infer_valence`; demote it to the annotated fallback.

## 5. Change 4 — subject-bearing headlines (CR-45)

`_build_headline_text` gains `fact_subject`, `house`, and `varga_id` parameters and leads with them: `"VENUS (H9, D1): graha dignity per varga = own_star [ga_structural]"` — format: `{SUBJECT} ({house_part}{varga_part}): {category}: {key} = {value} [{asset}]`, omitting parts that are genuinely absent. House resolution: from the fact's `configuration_jsonb`/`fact_value_jsonb` house field when present, else from the Change-5 position-class resolution, else omitted. The register's bar (CR-45): "Headline must name subject + house + varga. Salience without subject is unusable evidence." Every call site updated; no headline regression to the anonymous form for facts that HAVE a subject.

## 6. Change 5 — graha/house resolution for position-class facts (CR-76/77 as AMENDED)

Register §I.1 (binding): "Special-lagna / chara-karaka / arudha / KP / tajaka facts are **NOT dropped** — MSR ingests every category. They are **ingested-then-starved**: position-class facts carry no graha/house resolution → default shadbala 1.0 / dignity 0.5 / bindus 4 → hit the CR-82 varga ceiling → sink to background. **Corrected fix:** subject-resolution + un-capping, not 'add ingestion.'"

Implementation: in the salience-input assembly (`_compute_salience`'s callers build `strength_lookup`/`dignity_lookup`/`av_lookup` keyed by graha subject), add a **subject-resolution step** for position-class categories (`special_lagna`, `karaka_chara_position`, `karakamsa_position`, `arudha_pada`, `kp_*`, tajaka families — enumerate by grepping the fetch SQL's category universe): resolve the fact to (a) its **anchor graha** where one exists (special lagna → its sign's lord and any tenant graha named in the fact jsonb; chara karaka → the graha holding the karaka; arudha → the pada's lord and tenants; KP → the significator graha), and (b) its **house**. Then the standard lookups fire with the resolved graha instead of defaulting. Record `epistemic_jsonb.subject_resolution = {resolved_graha, resolved_house, rule}`. Where genuinely unresolvable → keep defaults + `inputs_complete=False` (the existing trap-#17 mechanism, verified in `SalienceInputsV2` docstring). This is resolution of EXISTING ingested facts — write no new fetch of new categories (anti-scope).

Type specimens that must stop sinking (CR-76, 482012f1): Indu Lagna Scorpio-H8-with-exalted-Ketu (fact 32f67f15) → resolves to Ketu/H8; Sree Lagna Libra-H7-conjunct-exalted-Saturn (fact c178ff37) → Saturn/H7; AmK=Saturn (fact 3d8de38d) → Saturn.

## 6b. Change 6 — `weakest_graha` root-cause rider (CR-55, CRIT, cheapest on the register's top-5)

CR-55: `vw_chart_digest` reports `weakest_graha: "Mercury"` while shadbala says Venus 4.64 is weakest — a false fact at the top of nearly every reading. Root-cause where `weakest_graha` is computed (grep `weakest_graha` across python-sidecar AND platform/src — it may be a view over MSR aggregates, hence this lane): if it derives from MSR dignity/salience aggregates, fix it to rank by `graha_shadbala_total` facts; if it lives purely in a serving view, hand the finding to Lane 5 with the exact site named. Acceptance below either way: post-rebuild digest must say VENUS for 482012f1, or your lane report names the exact non-MSR site + hands off.

## 7. Migration

Next free number (coordinate with Lanes 2/3 via CONDUCTOR — migrations serialize). Additive-only, idempotent (`ADD COLUMN IF NOT EXISTS`), migration-guard review:
```sql
ALTER TABLE bodha_msr_signals ADD COLUMN IF NOT EXISTS ratification_factor numeric;
ALTER TABLE bodha_msr_signals ADD COLUMN IF NOT EXISTS valence_source text;
-- + asset_registry: append 'ga_vichara' to bo_laksana.depends_on (match the column's real type)
```
(`subject_resolution`/`judged_valence` ride in the existing `epistemic_jsonb` — no column needed. If you find `bodha_msr_signals` already has suitable columns, use them and skip the ALTER.)

## 8. Tests

- Unit: percentile tier assignment on a synthetic 1,000-salience distribution → exactly ~1.5% chart_defining; ratification multiplication (0.6/1.0/1.4 cases); valence mapping vichara→MSR incl. fallback tagging; headline format with/without house/varga; subject resolution per specimen category (fixture jsonb rows).
- Regression: flood-collapse behavior unchanged (rollup count for a >12-member family still 1); `salience_formula_v2` output keys unchanged (downstream columns depend on them).
- Integration (dev DB): writer runs on a chart with `chart_vichara` populated; every signal has `valence_source`; DEFECT-001 orphan-refs = 0.

## 9. Acceptance criteria (post-CONDUCTOR-rebuild on 482012f1, build against Lane-2 vichara data)

- [ ] `signature_tier` distribution: `chart_defining` between 0.5%–3%, `supporting` **< 85%** (was 95.7% — CR-65's number must visibly move), measured over the chart's full signal set.
- [ ] The 8L-Mars→H2 aspect signal (CR-54 specimen, facts 1ea14404/82cc6f52): `valence='malefic'`, `valence_source='ga_vichara_v1'`, tier ≥ `major`.
- [ ] `varga_ratification_divergence` signals exist for Venus-D9 and Saturn-D9 (wealth) and rank in the top-15 of `domain=wealth` by salience (the §G.0-conclusion-2 serving test).
- [ ] Vargottama-Mercury and Rahu-exalted-H2 class facts no longer tier-capped: at least one non-D1-varga fact reaches ≥ `major` (CR-82's structural prohibition demonstrably gone).
- [ ] Class-prior hit-rate ≥ 50% reported in notes; at least two distinct class_prior values ≠ 1.0 present in stored salience inputs (CR-81 demonstrably live).
- [ ] Indu/Sree/AmK specimen signals: non-default shadbala/dignity inputs (`inputs_complete=true`, `subject_resolution` recorded) and salience above the position-class median (CR-76/77 un-starved).
- [ ] Every stored headline for subject-bearing facts names the subject (sample-audit SQL: 0 rows where `fact_subject IS NOT NULL` in constituent config AND headline lacks it).
- [ ] `weakest_graha` = VENUS on 482012f1's digest, or the exact non-MSR computation site named + handed to Lane 5.
- [ ] Full suite green; DEFECT-001 = 0; migration-guard sign-off; Abhinandan build also completes clean.

## 10. Known traps

- **CR-82's evidence cite is stale** — the ceiling lives in bo_laksana.py, not formulas.py. Trust the code, keep formulas.py's single-canonical-site discipline (its own C5-fix note: "ONE canonical site").
- **Do not delete the flood cap** (RATIFIED_FLOOD_CAP) — it is ratified and is the §N.6 precedent. Only the varga tier-ceiling dies.
- **§N.5**: MSR references L1 (`constituent_facts_array` → `chart_facts.fact_id`, and now `chart_vichara` ids) — never restates values. If a vichara factor contradicts what you'd derive, the stored row wins; report, don't fork.
- **CR-42 class**: no silent fallback anywhere — every degraded path stamps its source field.
- **`lel_origin=False` stays** — LEL is L3-gated; nothing in this lane touches LEL (calibration is D-4).
- **Percentiles are per-chart, per-build** — never global across charts (population statistics are out of scope by native decision, design §1).

## 11. Anti-scope

No CGM→MSR structural_role wiring (CR-84 → D-2; leave the `structural_role` term as-is). No mechanism objects (D-2). No convergence/timing (D-3, incl. CR-88 — do NOT start feeding salience into ka_sangam tonight). No new ingestion categories. No serving-plane TS beyond the CR-55 investigation handoff (Lane 5). No orchestrator change. No rebuilds/deploys (CONDUCTOR).

## 12. Done-definition / handback

Worktree branch: 6 changes + migration + tests, green. Report: tier-distribution before/after numbers from your dev run, the specimen assertions, class-prior hit-rate, the weakest_graha root-cause finding, §9 checklist. Lane 5 needs your list of changed payload fields (`ratification_factor`, `valence_source`, headline shape) to update tool contracts.
