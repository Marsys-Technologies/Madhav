---
artifact: L1_W1_ANALYSIS_BATCH_E
session: L1
wave: W1
batch: E
assets: [ga_ayurdaya, ga_medical, ga_vastu, ga_tajaka, ga_prashna]
produced_on: 2026-09-05
status: DRAFT
canonical_chart: 482012f1-710e-4a25-994a-93821f5871aa
method: read-only (nq against live prod DB) + source read of writers, orchestrator adapters, retrieval registry, platform-mcp
---

# L1-W1 Analysis — Batch E (the small, specialized, and dormant assets)

**Scope note.** Everything numeric below was measured live during this pass unless the sentence
says otherwise. Where a defect is *latent* (the code permits it but today's data does not exhibit
it) that is said explicitly rather than reported as a live defect.

**Batch-level facts established once, cited throughout:**

- **0 of 19 `layer='ganita'` assets carry `integrity_check_sql`** — measured:
  `SELECT count(*) FILTER (WHERE integrity_check_sql IS NOT NULL), count(*) FROM asset_registry
  WHERE layer='ganita'` → `0|19`. All five batch-E assets are inside that zero.
- **`asset_throughput` carries no timing data for any batch-E asset.** For all 15 rows
  (5 assets × 3 charts) `rows_per_second` is NULL and `measurement_count = 0`; the single
  non-null `last_measured_at` in the batch is `ga_tajaka` / canonical, `2026-06-11 18:12:42+00`.
  So rubric point 7 has **no measured build cost anywhere in this batch** — only the declared
  `asset_registry.estimated_seconds`, which is an unearned number in the §N.8 sense (no detector
  measures it, nothing would make it read false).
- **Canonical-chart cockpit state, measured:** of all assets on `482012f1`, 16 `lit`, 56 `stale`,
  10 `error`, 1 `dormant`. Within batch E: `ga_ayurdaya` lit, `ga_medical` lit, `ga_vastu` lit,
  `ga_tajaka` **stale** (240 rows), `ga_prashna` **stale** (0 rows).
- **`dormant` is a real, live `asset_throughput` state**, not a hypothetical: `mi_sankalpa` sits
  in it today, and `pipeline/orchestrator/runner.py:154` declares it
  (`"dormant"  # asset_throughput: DECLARED outcome — ran, legitimately 0 rows`). This matters
  for the `ga_prashna` disposition (§ below).
- **`fact_category_ownership` has 59 rows and none for `ayurdaya`** — measured:
  `SELECT * FROM fact_category_ownership WHERE fact_category='ayurdaya' OR owning_asset_id IN
  ('ga_ayurdaya','ga_medical','ga_vastu','ga_tajaka','ga_prashna')` → **0 rows**. `ga_ayurdaya` is
  the only batch-E asset that writes into `chart_facts`, and its category is unowned.

---

## 1. `ga_ayurdaya` — Āyurdāya / Longevity (Three Methods)

**Registry:** `layer=ganita`, `sort_order=51`, `target_table=chart_facts`,
`count_sql = SELECT COUNT(*) FROM chart_facts WHERE chart_id=$1 AND fact_category='ayurdaya'`,
`target_floor=0`, `expected_volume_formula=NULL`, `depends_on={ga_positions}`,
`estimated_seconds=4`, `has_substeps=t`, `integrity_check_sql=NULL`.
**Writer:** `platform/python-sidecar/ga_writers/ga_ayurdaya_writer.py` (313 lines);
adapter `platform/python-sidecar/pipeline/orchestrator/writers/ga_ayurdaya.py:21`.

### 1. Pillar / doctrine service
**D-GROUNDING** first, **D-SERVICE** second — and the assignment is still right, unusually
clearly so. The writer's entire epistemic posture is delegation-with-citation: the base longevity
constants and the applicability rule come from PyJHora's shipped, cited `aayu` module
(`ga_ayurdaya_writer.py:50-51, 135-137`), never from a Claude-invented number (B.10), and the
§7.2 binding ruling — *serve all three methods, attributed; do not adjudicate the doctrinal
dispute* — is implemented literally: `build_ayurdaya_rows` loops
`for method in ("pindayu","nisargayu","amsayu")` and emits a separate `applicable_method` row
that reports the classical rule without acting on it (`:226-260`). This is a textbook §N.6
density-layering case: three method verdicts served side by side, plus a fourth row saying which
one the canon prescribes, rather than one flattened "your longevity is N".

### 2. Real vs declared dependencies
Declared `{ga_positions}`. Real: `load_positions()` (`:206-209`) delegates to
`ga_writers.ga_sensitive_degree_writer.load_positions`, which reads `chart_facts` graha positions
— i.e. `ga_positions`' output. **Declared and real match; no hidden or false edge found.** The
one non-obvious real dependency is the *code* dependency on `ga_sensitive_degree_writer` as the
shared position reader; that is a §N.7-item-1-compliant choice (single L1-authority reader,
referenced not re-derived) and is documented in the docstring at `:207`.

### 3. LEVERAGE — is anything reading NULL where this asset has the answer?
**No — this is a genuinely plugged-in asset, contrary to the "built-but-unplugged suspect"
prior.** Traced end to end:
- Serving capability `platform/src/lib/retrieval/registry/layers/L1_ganita/get_ayurdaya.ts`
  (`uri: marsys://tool/L1/get_ayurdaya`), registered in that layer's `index.ts:35`.
- MCP alias `ganita_ayurdaya_get` → `marsys://tool/L1/get_ayurdaya`
  (`platform-mcp/src/tools/register_p1_aliases.ts:918-922`).
- Routed by a real planner primitive: `platform/src/lib/vidhi/registry_data.ts:669`
  `primitive_id: 'ayurdaya_read'`, `live_tool: 'ganita_ayurdaya_get'` (`:674`), ordered into the
  `acharya_floor` band at `:1179` (`order: 16`), explicitly filling "the āyurdāya/longevity spine
  the audit found missing from health_deepdive" (`:668`).
- Governed by a real safety class: `sensitive_capabilities.ts:41-42` and
  `safety/classifier.ts:1044-1045` map both `get_ayurdaya` and `ganita_ayurdaya_get` to
  `hs4_mortality_window`; `prompt_policy.ts:31` carries the HS-4 aggregate-framing clause.

The one leverage *gap* is small but real and worth naming: `get_ayurdaya.ts` serves
`fact_subject`/`fact_key`/`fact_value_num`/`fact_value_text` but **not `fact_value_jsonb`** (the
SELECT at `:72-73` omits it). The per-method `per_graha` contribution map, `lagna_years`, the
`harana_status` flag, and the whole `maraka_grahas` payload (2nd/7th signs, lords, occupants) all
live only in `fact_value_jsonb`. So a caller gets the three totals and the bands, but the
evidence layer underneath them — which the writer computed and stored — is unreachable through
the tool. The vidhi primitive's own description (`registry_data.ts:672`) promises "the maraka
grahas"; the tool cannot deliver them.

### 4. Grounding — is a tier meaningful here?
**Yes, and this is the batch's strongest case for one.** Every one of the 130 rows carries
`verification_pass_status='single'` (measured: `single|130`, the only value present) — which is
honest under the §N.4 S7 ruling (an honest tier beats a broadcast claim) but is a *verification*
tier, not a *grounding* tier, and it collapses three epistemically different things into one
label:
- the three method totals are **delegated-and-cited computation** — the constants are PyJHora's
  `pindayu_full_longevity_of_planets` / `nisargayu_full_longevity_of_planets` traceable to BPHS /
  Varāhamihira; `citation_human` names the module and the text (`:231-236`). A `sruti`-tier label
  is meaningful and would resolve to *cited classical method, delegated implementation*.
- the **applicability rule** row (`:254-260`) carries an explicit BPHS-adhyāya citation string
  (`APPLICABILITY_CITATION`, `:87-91`) — also `sruti`-labelable.
- the **classification bands** (alpāyu/madhyāyu/pūrṇāyu at 32/64) are a `yukti` convention: the
  citation at `:97-101` says they are "aligned to PyJHora `const.longevity_years`
  `[[32,36,40],[64,72,80],[96,108,120]]`", but `classify_ayus` (`:104-110`) uses a flat
  32/64 tri-partition that is *not* any single column of that 3×3 band table. The label is
  honest-adjacent but the arithmetic is the writer's own simplification of the cited source.
- the `harana_status` is `base_only_haranas_deferred_to_w3` on every method row (`:241`) — a
  correctly-disclosed incompleteness (astaṅgata / śatru-kṣetra / cakrapāta / krūrodaya reductions
  are not applied). **This is served in `fact_value_jsonb` and therefore, per §3 above, is
  invisible to every consumer of `get_ayurdaya`.** A caller reads `98.75 years / purnayu` with no
  indication that the classical reductive haranas were never applied.

**Measured substance worth flagging** (this is a chart finding, not a code finding): the three
methods disagree by a factor of ~2.7, and the amsāyu band **flips class across ayanamshas**:

| ayanamsha | PINDAYU | NISARGAYU | AMSAYU | amsāyu band |
|---|---|---|---|---|
| lahiri_chitrapaksha | 98.7521 | 99.1851 | 36.3448 | madhyayu |
| true_chitra | 98.7540 | 99.1842 | 36.3779 | madhyayu |
| krishnamurti | 98.7642 | 99.1792 | 36.5514 | madhyayu |
| raman | 98.9328 | 99.0968 | 39.4302 | madhyayu |
| surya_siddhanta_classical | 99.1223 | 99.0041 | **30.6638** | **alpayu** |

`applicable_method` = `pindayu` under all five ayanamshas (measured). So the served answer is
stable, but the amsāyu row is one ayanamsha away from a different life-class — exactly the kind
of cross-ayanamsha divergence a `two_pass`/concordance flag exists to surface, and nothing
surfaces it today.

### 5. (temporal) — n/a
Not a temporal engine. Longevity is a lifetime scalar; the time-indexing of the maraka verdict is
`ga_dashas`/L3's job and this writer correctly does not attempt it (`MARAKA_CITATION` `:92-96`
names dasha activation as the mechanism without computing it).

### 6. Service — consumer, floor, density, drill
- **Consumer:** real (§3).
- **Floor: WRONG, and this is the batch's clearest floor defect.** `target_floor = 0` while the
  live count is **130** and has been 130 on every chart ever built (measured `asset_throughput`:
  `ga_ayurdaya` = 130 rows for `482012f1`, `1c826d5a`, and `cb73cd3d` alike). §N.4 says floors are
  the *achieved* count set after build; 0 is not that, and a floor of 0 is unfalsifiable — the
  asset could emit zero rows on a future chart and nothing would notice. The count is exactly
  structural and I verified the arithmetic against the data: per ayanamsha 26 rows
  = 3 method totals + 21 per-graha contributions (7 grahas × 3 methods) + 1 `applicable_method`
  + 1 `maraka_grahas`; × 5 ayanamshas = 130 (measured `C_ayurdaya_per_aya` → `26` for each of the
  five). `expected_volume_formula` is NULL where it could honestly read
  `AYANAMSHAS * (3 + 3*SEVEN_GRAHAS + 2)`.
- **Single-generation guaranteed:** `_idempotency.replace_prior_chart_facts` (`:40-57`) deletes by
  `(chart_id, fact_category, ayanamsha_id)` *across all build_ids* before insert, so the 130 is
  one generation (measured: `count(DISTINCT build_id) = 1` per ayanamsha). This matters because
  `get_ayurdaya.ts` does **not** filter on `build_id` — it is safe today only because the write
  path guarantees it, which is the correct division of labour per §N.7 item 2's honest-scope note.
- **Density (§N.6):** partial. The tool has a real `empty_reason` (`get_ayurdaya.ts:93-95`), a
  standing `disclaimer`, and a `note` explaining the num/text split. It has **no
  `density_contract`** (measured: `grep density_contract` → 0 hits in the file), and it flattens
  three method verdicts + evidence rows + the applicability verdict into one undifferentiated
  `rows` array ordered `ayanamsha_id, fact_subject, fact_key`. A caller reading `count: 130` has
  no machine-readable way to know that 3 of those rows are verdicts and 105 are evidence.
- **Drill in ≤2 hops:** the totals, yes. The maraka significators and per-graha contributions,
  **no — zero hops reach them** (§3), because the only tool that serves this category omits the
  jsonb column.

### 7. Measured build + serve cost
`estimated_seconds = 4` (declared). **No measured figure exists** — `asset_throughput` for this
asset shows `rows_per_second = NULL`, `measurement_count = 0` on all three charts;
`last_built_at` = `2026-08-08 00:24:26+00` (canonical), `2026-07-26` (1c826d5a),
`2026-07-27` (cb73cd3d). Serve cost is one indexed `chart_facts` scan plus a COUNT, both bounded
to ≤200 rows; `llm_hints.agentic.cost_class = 'cheap'` (`get_ayurdaya.ts:51`).

### 8. Findings
F-E1 (MUST), F-E2 (NOW), F-E3 (NOW), F-E4 (NOW) — see consolidated table.

---

## 2. `ga_medical` — Vaidya-phala / Medical Indications

**Registry:** `target_table=ga_medical`, `count_sql = SELECT COUNT(*) FROM ga_medical WHERE
chart_id = $1`, `target_floor=45`, `expected_volume_formula='GRAHAS * AYANAMSHAS'`,
`volume_explanation='9 grahas × 5 ayanamshas = 45 indication rows per chart.'`,
`depends_on={ga_condition, ga_positions}`, `estimated_seconds=2`, `integrity_check_sql=NULL`.
**Writer:** `ga_writers/ga_medical_writer.py` (381 lines); adapter
`pipeline/orchestrator/writers/ga_medical.py:24`.

### 1. Pillar / doctrine service
**D-GROUNDING + D-SERVICE.** Still right. The asset's whole job is to join an L0 classical
mapping table to an L1 computed condition score and label the result with a
non-negotiable epistemic tier — every row carries `indication_tier='jyotish_indication'` and
`not_diagnosis=TRUE` (`:331-332`, measured: 45/45 rows have both). That is D-GROUNDING doing
real work: the tier is not decoration, it is the thing that makes a "Sun → heart/bones, strong
indication" row honest to serve at all.

### 2. Real vs declared dependencies
Declared `{ga_condition, ga_positions}`. Real reads, from source:
- `ga_condition_composite` (`:111-116`) → `ga_condition` ✓ declared.
- `chart_facts` `fact_category IN ('graha_sign_attributes','graha_position')` (`:171-178`) →
  `ga_positions` ✓ declared.
- **`bg_medical_mappings` (`:139-143`) — L0, NOT declared.**
- **`bg_nakshatra_medical` (`:213-217`) — L0, NOT declared.**

**Two hidden edges.** Both are load-bearing: `dosha_aggravated`, `organ_watch`,
`body_part_watch` and `classical_citation` all come from `bg_medical_mappings`, and every one of
them is wrapped in a `try/except` that logs a warning and returns `{}` (`:153-156`). If
`bg_medical_mappings` were empty or absent, the writer would still insert 45 rows — with empty
arrays and the fallback `MEDICAL_GA_CITATION` — and report success. Nothing detects that
(§N.8: a status with no detector behind the specific claim). Measured today the mappings are
present: `empty_dosha=0, empty_organ=0` across all 45 rows.

### 3. LEVERAGE
**Plugged in, with one real gap.** Live chain: `ga_medical` →
`retrieval/registry/layers/L1_ganita/get_medical_indications.ts` (`marsys://tool/L1/
get_medical_indications`) → `tool_name_bridge.ts:190,478,581` → MCP alias `ganita_medical_get`
(`register_p1_aliases.ts:899-902`) → vidhi primitive `medical_read`
(`vidhi/registry_data.ts:683`, `live_tool: 'ganita_medical_get'` `:688`, `acharya_floor` band
order 17 at `:1180`) → safety class at `sensitive_capabilities.ts:53-54`.

**The gap:** `nakshatra_body_part` is populated for **Moon only** — measured, 40 of 45 rows have
it NULL, and the 5 non-null are the 5 Moon rows (`left_side`, from Purva Bhadrapada). This is by
construction: `:317` reads `if graha == "Moon" and natal_nakshatra:`. But every one of the nine
grahas has a stored `natal_nakshatra` (measured: `null_nak = 0` across all 45 rows), and
`bg_nakshatra_medical` is keyed by nakshatra alone. The join that would fill the other 40 rows is
one line of the same lookup already in the file. That is a designed consumer field reading NULL
where the inputs to compute it are already present in the same transaction — the rubric's
highest-value question, answered affirmatively.

### 4. Grounding
**Meaningful, and partly already carried.** `classical_citation` is a real per-row column and
resolves to the `bg_medical_mappings` row's own citation, falling back to
`"BPHS Ch.18 / Ashtanga Hridayam / Charaka Samhita — via bg_medical_mappings L0 reference"`
(`:63-66, 333`). A grounding tier here would resolve to **`sruti` for the body-part / dosha /
organ mapping** (it is a cited classical correspondence, inherited from L0, not computed) and
**`pratyaksa` for `indication_strength`** (a pure threshold over the L1 `condition_score`). Those
two halves of every row have genuinely different epistemic status and the table has one citation
column covering both.

**Two concrete grounding/narration defects found in the writer:**

(a) **A build-fatal assertion justified by a false classical claim.** `:22-25` and `:286-293`
assert, for the canonical chart under lahiri only, that Sun's `indication_strength` must be
`'strong'` because *"Sun = Capricorn (debilitated)"*. **Sun is not debilitated in Capricorn — Sun
debilitates in Libra.** This exact error was already found and removed from the sibling
`ga_vastu_writer.py`, which now carries the correction in a comment at `:169-172`
("Sun assertion removed: 'Sun debilitated in Capricorn' was astrologically incorrect — Sun
debilitates in Libra, not Capricorn"). `ga_medical` kept the assertion *and* the wrong rationale.
It passes today for a different, correct reason: measured, Sun's `dignity_d1` in Capricorn is
`enemy_sign` with `condition_score = 0.26` → `'strong'`. So a **build-fatal gate is passing on a
number the writer's own stated reason does not explain** — §N.7 item 1 (a sentence that grades a
computed value must trace to the fact it reads) and §N.8 (the gate does not measure the claim it
asserts).

(b) **A latent, currently-dormant fact-selection ambiguity.** `_load_graha_positions` (`:171-178`)
selects `fact_category IN ('graha_sign_attributes','graha_position')` with `fact_key IN
('sign','nakshatra')`, **no `build_id` filter and no `ORDER BY`**, then last-write-wins into
`result[graha][key]` in an unordered `for` loop (`:188-194`). §N.7 item 2 requires a pinned
`fact_key` (satisfied) *and* a total `ORDER BY` (absent). Measured today: for the canonical chart
under lahiri, every `(fact_category, fact_key, fact_subject)` triple returns exactly 1 row from
1 build, and `graha_sign_attributes` contributes **zero** rows for these keys — the second
category in the `IN` list is a dead branch. **So this is latent, not live.** I flag it as latent
risk, not a present defect.

### 5. (temporal) — n/a
Static natal indication summary; no time axis.

### 6. Service
- **Consumer:** real (§3).
- **Floor:** `45` = live `45`. See the **exact-floor assessment** section — this one is case (a):
  a genuinely structural invariant, `len(ALL_GRAHAS) × len(CANONICAL_AYANAMSHAS)` with both
  constants in the file (`:49-60`) and a straight-line insert loop with no filtering. Verified
  across all three built charts (measured: 45 for `1c826d5a`, `482012f1`, `cb73cd3d`).
  `expected_volume_formula='GRAHAS * AYANAMSHAS'` is correct and evaluates to 45. This is the
  cleanest floor in the batch.
  But note what the floor therefore *cannot* do: 45 rows all reading
  `indication_strength='unknown'` and `dosha_aggravated='{}'` would pass it. The floor has
  approximately zero detection power over content, which is exactly the hole
  `integrity_check_sql` exists to fill and which is NULL here.
- **Density (§N.6):** weakest in the batch. `get_medical_indications.ts` has **no
  `density_contract`** and — measured by reading the full handler, `:83-103` — **no
  `empty_reason` at all**. A 0-row response returns
  `{chart_id, rows: [], count: 0, total_matching: 0, more_available: false, filters,
  disclaimer, provenance}` — a populated-looking envelope carrying a medical disclaimer and a
  provenance block over nothing. §N.6 item 3 makes this a real defect: the honest gap is not
  reported, it is dressed as a result.
- **Drill:** 1 hop to the rows; but the two upstream authorities (`bg_medical_mappings`,
  `ga_condition_composite`) are not named in `provenance.tables` (`:97` lists `['ga_medical']`
  only), so a caller cannot drill from an indication to the classical mapping that produced it.

### 7. Cost
`estimated_seconds = 2` declared; **unmeasured** (`measurement_count = 0`).
`last_built_at`: canonical `2026-08-08 00:33:43+00`, `1c826d5a` `2026-08-12 16:28:01+00`,
`cb73cd3d` `2026-07-27 09:02:34+00`. Note the writer re-reads all of `bg_medical_mappings` once
per ayanamsha substep (`:271`) — 5× a 21-row table, negligible.

### 8. Findings
F-E5 (MUST), F-E6 (NOW), F-E7 (NOW), F-E8 (NOW), F-E9 (NEVER-LATER).

---

## 3. `ga_vastu` — Vastu Planet Direction Map

**Registry:** `target_table=ga_vastu_planet_direction_map`, `target_floor=40`,
`expected_volume_formula='GRAHAS * AYANAMSHAS'`,
`volume_explanation='Up to 9 grahas × 5 ayanamshas = 45; Ketu skipped (no Vastu direction
mapping) → 40 rows.'`, `depends_on={ga_condition}`, `estimated_seconds=1`,
`integrity_check_sql=NULL`.
**Writer:** `ga_writers/ga_vastu_writer.py` (185 lines); adapter
`pipeline/orchestrator/writers/ga_vastu.py:12`.

### 1. Pillar / doctrine service
**D-SERVICE**, weakly, with a D-SALIENCE claim it does not currently earn. The asset computes a
per-graha `direction_impact` (weakened/neutral/strengthened) which is a salience judgment about
*where in a dwelling* the chart's stress lands. That is a genuinely useful, genuinely actionable
output — and, per §3, nothing downstream acts on it. So the pillar assignment is right in
intent and unrealized in fact.

### 2. Real vs declared dependencies
Declared `{ga_condition}`. Real: `ga_condition_composite` (`:110-117`) ✓ — and **that is the only
DB read in the writer.** No hidden edge in the DAG sense.

**But there is a documentation/authority mismatch that matters.** The registry's own
`english_description` says the asset "Maps each classical graha to its ruling Vastu direction
(**per `bg_vastu_directions`**)". It does not. The mapping is a **hardcoded Python dict**,
`GRAHA_TO_DIRECTION` at `ga_vastu_writer.py:42-52`, and `bg_vastu_directions` is never queried.
I measured the L0 table and the two **agree exactly today** — 8 rows, North→Mercury,
South→Mars, East→Sun, West→Saturn, Northeast→Jupiter, Southeast→Venus, Northwest→Moon,
Southwest→Rahu, no Ketu — so there is no live divergence. But this is §N.7 item 3 precisely:
*no wrapper-local constant may shadow a stored authoritative value, even when the constant's
current value happens to be correct — a constant can drift from its source, a reference cannot.*
The `classical_citation` written on every row is likewise the module-level string
`VASTU_CITATION` (`:54`) rather than the L0 row's own `classical_citation`, so the Southwest/Rahu
row is served with `"Vastu Shastra (Mayamata Ch.6)"` when the L0 table's own citation for that
row is the different and more honest `"Vastu Shastra tradition (Nairitya corner)"` (measured).
The writer is broadcasting a Mayamata citation over a row L0 itself declines to attribute to
Mayamata.

### 3. LEVERAGE — **this is the batch's real leverage finding**
The tool exists and is deployed: `get_vastu_directions.ts` →
`tool_name_bridge.ts:191,479,582` → MCP alias `ganita_vastu_get`
(`register_p1_aliases.ts:909`) → it is even a **canonical face**
(`retrieval/registry/canonical_faces.json:38`). So it is reachable *by name*.

**But nothing routes to it and nothing consumes its output.** Measured:
- `grep -rn "ga_vastu_planet_direction_map" platform/src platform-mcp/src`, excluding generated
  projections and tests, returns exactly **two** hits, both in the serving file itself
  (`get_vastu_directions.ts:74, 82`) plus a comment in the L0 sibling
  `query_vastu_directions.ts:9`. Nothing else in the codebase reads this table.
- `direction_impact` — the computed judgment, the whole point of the asset — is referenced in
  exactly **two** non-generated lines, both inside `get_vastu_directions.ts` (`:24` description,
  `:73` SELECT). Zero consumers.
- **No vidhi primitive exists for vastu.** Measured: `registry_data.ts` declares **245**
  `primitive_id:` entries; `grep -i "vastu"` over it returns **zero**. Contrast `ayurdaya_read`
  and `medical_read`, which are both present and both in the `acharya_floor` band. So no planner
  path can ever select `ganita_vastu_get`; it can only be called if a caller names it directly.

**And the half-answer is the sharp part.** L0 ships `bg_vastu_direction_remedials` — 24 rows of
classical per-direction remedy, served chart-agnostically at
`retrieval/registry/layers/L0_brahmagyan/query_vastu_direction_remedials.ts`. L1 computes, per
chart, *which* directions are weakened (measured for the canonical chart under lahiri:
Sun/East `weakened`, Moon/Northwest `weakened`; Jupiter/Northeast, Rahu/Southwest, Saturn/West
`strengthened`). **Nothing joins them.** The instrument holds "your East is afflicted" in one
table and "here is the classical remedy for an afflicted East" in another, and no surface, no
primitive, and no `bo_upaya`/remedy path puts them in the same response. That is a designed
consumer reading NULL where the answer is already computed — the exact shape the rubric asks for.

### 4. Grounding
Tier is meaningful but thin. The direction↔graha correspondence is `sruti`-labelable (Mayamata
Ch.6 / Bṛhat Saṃhitā Ch.53, and L0 carries the per-row citation the writer discards — §2). The
`direction_impact` label is `pratyaksa`: a pure threshold over the L1 `condition_score`
(`compute_direction_impact`, `:58-73`). `indication_tier='traditional_vastu'` is present on all
40 rows (measured) and is doing honest work — it marks the whole surface as tradition-tier rather
than computed-Jyotish-tier.

**Threshold inconsistency worth recording:** `ga_vastu` and `ga_medical` grade the *same*
`ga_condition_composite.condition_score` with **different cutpoints** —
vastu `<0.4 weakened / <0.7 neutral / ≥0.7 strengthened` (`:69-73`) vs
medical `<0.4 strong / ≤0.6 moderate / >0.6 mild` (`ga_medical_writer.py:88-94`). A graha scoring
0.65 is `neutral` to vastu and `mild` (i.e. already in the top band) to medical. Neither is wrong
in isolation; but the divergent 0.6/0.7 boundary is undocumented and nothing reconciles it.

### 5. (temporal) — n/a
Static natal map.

### 6. Service
- **Consumer:** the tool exists; **no routed consumer** (§3). This is the disposition W2 must
  decide: served-by-name-only.
- **Floor:** `40` = live `40`, verified across all three built charts (measured: 40 for each). See
  the exact-floor section — case (a), structurally invariant
  (`len(ALL_GRAHAS) - 1 Ketu) × 5 = 40`, from constants in the file.
  **But `expected_volume_formula` is wrong:** it reads `'GRAHAS * AYANAMSHAS'`, which evaluates to
  **45**, while the floor and the truth are **40**. The `volume_explanation` beside it correctly
  explains the Ketu exclusion. So the machine-readable formula and the human-readable
  explanation disagree in the same registry row — a GA.1-class registry disagreement, and the
  formula is the half a tool would read.
- **Build-fatal canonical assertion:** `:173-179` raises `AssertionError` if Saturn's
  `direction_impact != 'strengthened'` on the canonical chart. It passes (measured: Saturn
  `condition_score = 0.775`, `dignity_d1='exalted'` → `strengthened`), but the margin to the 0.7
  cutpoint is 0.075 — a legitimate re-tune of `ga_condition`'s composite would halt the whole
  ayanamsha's build. Same class as the `ga_sensitive` `single`-tier guard the S7 ruling relaxed.
- **Density (§N.6):** `get_vastu_directions.ts` has **no `density_contract`** and — measured by
  reading `:84-100` — **no `empty_reason`**. Identical defect to `ga_medical`'s tool.
- **Drill:** 1 hop to the rows; 0 hops to the remedy (§3).

### 7. Cost
`estimated_seconds = 1` declared; **unmeasured**. `last_built_at`: canonical
`2026-08-08 00:33:42+00`; `1c826d5a` `2026-08-12 16:29:39+00`; `cb73cd3d` `2026-07-27 09:02:33+00`.
Cheapest asset in the batch — one bulk `ga_condition_composite` read per ayanamsha plus 8 inserts.

### 8. Findings
F-E10 (MUST), F-E11 (MUST), F-E12 (NOW), F-E13 (NOW), F-E14 (NOW).

---

## 4. `ga_tajaka` — Tājaka Vārṣaphala (annual / solar-return engine)

**Registry:** `target_table=l1_tajik_varsha_year_lords`,
`count_sql = SELECT count(*) FROM l1_tajik_varsha_year_lords WHERE chart_id = $1`,
`target_floor=240`, `expected_volume_formula=NULL`,
`volume_explanation='target_floor = 240 = achieved canonical count for chart 482012f1
(2026-06-11): A7 hybrid window varsha 1..48 × 5 ayanamshas. Hybrid storage — varshas outside the
precomputed window are computed on-demand by the retrieval tool via
ga_tajaka_writer.compute_varsha().'`, `depends_on={ga_positions, ga_dashas, ga_sensitive}`,
`estimated_seconds=14`, `has_substeps=f` (light writer), `integrity_check_sql=NULL`.
**Writer:** `ga_writers/ga_tajaka_writer.py` (852 lines — by far the batch's largest); adapter
`pipeline/orchestrator/writers/ga_tajaka.py:7`.

### 1. Pillar / doctrine service
**D-TIME**, unambiguously, with a secondary D-GROUNDING claim (the FORENSIC Muntha gate). Still
the right instrument: it is the only engine in the system that materialises the *solar-return
annual plane*, and it is genuinely two-pass verified — measured,
`verification_pass_status='two_pass_verified'` on **240/240** rows for the canonical chart, and
the build halts on any `divergent_flagged` row before insert (`:780-782`). That is the batch's
only asset with a real, earned verification tier.

### 2. Real vs declared dependencies
Declared `{ga_positions, ga_dashas, ga_sensitive}`. Real DB reads — measured by grepping every
`SELECT` in the writer — there is exactly **one**: `_read_trirashipathi` (`:450-458`) reading
`chart_facts` `fact_category='tajik_triraashipathi'`, which is `ga_sensitive`'s output. ✓

**Two false edges:**
- **`ga_dashas` is never read.** No reference to `chart_dashas` anywhere in the file (measured:
  `grep -n "chart_dashas" ga_tajaka_writer.py` → no match). The Mudda annual daśā the docstring
  mentions at `:11` is `ga_dashas` System 6, computed *by that asset*, and this writer neither
  reads nor writes it.
- **`ga_positions` is never read either** — and worse, its output is **re-derived**. `:689` and
  `:745` both call `natal = compute_chart({**bp}, ayanamsha_id=aya_adapter)`, recomputing the
  natal chart from `birth_params` via PyJHora rather than reading the stored L1 longitudes. §N.5
  is explicit: an L1+ consumer *references* the stored fact and inherits its value; it does not
  re-derive it. Here the natal Sun longitude that anchors every solar-return root-find
  (`natal_sun`, `:746-748`) is a fresh PyJHora computation, not `ga_positions`' stored value. They
  presumably agree (same engine, same adapter, same params) — but nothing checks, and "presumably
  agrees because it's the same engine" is exactly the reasoning §N.8 rejects.

### 3. LEVERAGE
**Best-connected asset in the batch — genuinely leveraged, and by a different layer.** Chain:
- `retrieval/registry/layers/L1_ganita/get_tajik.ts` (`marsys://tool/L1/get_tajik`), aliased
  `query_varshaphala` (`tool_name_bridge.ts:88`) and served as MCP `ganita_tajaka_get`.
- **L3 consumes it rather than duplicating it**: `platform-mcp/src/tools/kala_views/ahead.ts`
  reads the varsha row *through the L1 capability*, not by re-deriving —
  `fetchTajikVarshaForDate` (`:585+`) calls
  `callRegistryCapability('marsys://tool/L1/get_tajik', {...varsha_date...})`, with the comment
  at `:510-519` naming it a `[J]`-kind JOIN over two already-computed substrates, "no new
  astrological computation." This is a model §N.5 citation, and it was *fixed* into that shape:
  `:522-543` records that the reader previously asked for flat `muntha_sign`/`muntha_house`
  columns that do not exist, silently produced `null` on every chart, and leaked "Muntha in
  unknown" into served 90-day prose with no coverage disclosure. It now parses
  `muntha_position_jsonb` verbatim (`parseMunthaPosition`, `:565-583`).
- `platform/src/lib/schools/chart_data_adapter.ts:393-405` also reads the table directly for
  varṣeśa + muntha.

**The one leverage hole is on the write side, not the read side:** the hybrid window's "present"
is a frozen literal. `DEFAULT_REFERENCE_YEAR = 2026` (`:76`) and
`max_varsha = current_varsha + 5` where `current_varsha = reference_year - birth_year + 1`
(`:729-731`). Nothing derives `reference_year` from the clock. Today (2026-09-05) that is
coincidentally correct. In 2027 the same build produces the same varsha 1..48 window — i.e.
present+4, then present+3, and by 2032 the "past→present+5" window would stop *before* the
current year, with no error and no signal. The materialised window silently degrades with wall
time. (Measured corroboration that the window is reference-year-driven and not chart-invariant:
canonical `482012f1` has varsha 1..48 = 240 rows; `1c826d5a` has 1..47 = 235; `cb73cd3d` has
1..61 = 305.)

### 4. Grounding
`verification_pass_status='two_pass_verified'` on all 240 rows, and it is earned — `_compute_one`
flags divergence and the build refuses to insert if any row diverges (`:773-782`). The FORENSIC
Muntha gate (`:753-771`) is a real detector: for canonical × lahiri × varsha 43 it asserts
Muntha = Libra / 7th from natal Lagna / lord Venus and raises `RuntimeError("FORENSIC HALT: …")`
otherwise. Measured, varsha 43 = `2026-02-04 23:59:03+00 → 2027-02-05 06:03:58+00`, `year_lord`
Venus under all five ayanamshas. That is a §N.8-compliant signal: there is a code path that would
make it read false.

**One §N.7-item-2 defect, latent:** `_read_trirashipathi` (`:450-458`) uses `LIMIT 1` with **no
`ORDER BY`** — it pins `fact_category` *and* `fact_key` (so `fact-category-pin-lint` passes) but
the ordering half of the rule is missing, so across `build_id` generations the selected row is
arbitrary. Measured today: exactly 1 row and 1 `build_id` per `(chart_id, ayanamsha_id)` for all
three charts, and 1 distinct value — **latent, not live.** Its failure is also quiet: the read is
wrapped in `try/except` returning `None` (`:459-462`), so a broken candidate feed degrades the
`candidate_lord_jsonb` scoring silently.

### 5. (temporal) — the D-TIME concordance question
**The temporal question this engine answers, stated:** *"For the solar year running from this
native's sidereal-solar birthday return to the next, what is the annual chart — Muntha position,
Vārṣeśa (year-lord) by `tajik_classical` and `panchavargiya` with candidate scoring, and which
Tājik yogas fire in it?"* Grain: one row per `(chart_id, ayanamsha_id, varsha_year)`; boundary:
the instant the sidereal Sun returns to its natal longitude (`_solar_return`, `:235-280`, a real
Swiss-Ephemeris-backed bisection, not an anniversary approximation — measured, varsha 43 starts
`2026-02-04 23:59:03+00`, not on the birthday date).

**Does it duplicate or conflict with L3?** No — and the boundaries are declared in L3's own
registry rows, which I read:
- `ka_tithi_pravesha` (L3, `kala_tithi_pravesha`) describes itself as *"the lunar-return
  counterpart to Tājika Vārṣaphala (**ga_tajaka**) — the annual chart cast for the instant the
  transiting Moon returns to its exact natal sidereal longitude nearest each solar-birthday
  anniversary."* Different return body, different instant, explicitly named as the counterpart.
- `ka_sudarshana_varsha` (L3, `kala_sudarshana_varsha`) is *"the rotating annual house-per-year
  progression of the tri-lagna framework (Janma/Chandra/Sūrya Lagna) … pure arithmetic over natal
  chart_facts."* A progression, not a return.
- The Mudda annual daśā — the sub-annual clock inside a varsha — lives in `ga_dashas` System 6,
  and `ahead.ts` item 30 joins it to this varsha plane rather than either engine recomputing it.

So three annual clocks coexist with **non-overlapping definitions**, and L3 reads L1's rather than
re-deriving. That is what D-TIME's concordance contract wants. **What is missing is only the
declaration:** the concordance is stated in *L3's* prose (`ka_tithi_pravesha.english_description`
names ga_tajaka), never in `ga_tajaka`'s own registry row, and nowhere machine-readably. If
`ka_tithi_pravesha`'s description were edited, nothing would notice the concordance had lost its
only written form.

### 6. Service
- **Consumer:** real, multi-layer (§3).
- **Floor: `240` is the batch's genuine "equality wearing a floor's name."** It is not
  structural — it is `((reference_year − birth_year + 1) + 5) × 5`, i.e. a function of a
  hardcoded constant *and* the chart's birth year. Measured proof that it does not hold across
  charts: `1c826d5a` = **235** rows and `cb73cd3d` = **305** rows against the same global
  `target_floor = 240`. So for `1c826d5a` the asset is 5 rows *below* a floor it can never reach,
  and for `cb73cd3d` it is 65 above. A per-chart-varying quantity is being asserted as a global
  constant. And the moment anyone honestly updates `DEFAULT_REFERENCE_YEAR` to 2027, the canonical
  count becomes 245 and the floor false-alarms. Both halves of the C12/D-126 warning apply.
  `expected_volume_formula` is NULL where it could honestly read
  `((REFERENCE_YEAR - BIRTH_YEAR + 1) + 5) * AYANAMSHAS`.
- **A registry claim with no implementation behind it (§N.8).** `volume_explanation` states
  varshas outside the window "are computed on-demand by the retrieval tool via
  `ga_tajaka_writer.compute_varsha()`". Measured: `grep -rn "compute_varsha"` across `platform/`
  and `platform-mcp/` returns **three** hits — the `def` itself
  (`ga_tajaka_writer.py:669`), a self-referential string in the writer's own return payload
  (`:817`), and the registry seed line that makes the claim
  (`platform/scripts/seed/asset_registry_seed.ts:1340`). **There is no caller.** `get_tajik.ts` is
  a pure `SELECT` (`:206-222`) with no fallback compute path — a TS serving route could not call a
  Python function in any case. So "hybrid storage" is a documented capability that does not exist;
  the storage is simply windowed. To its credit the *tool* is honest where the *registry* is not:
  `get_tajik.ts:266-272` emits an `empty_reason` saying Varṣaphala "has genuinely not been
  computed/stored for this chart+filter combination" — it does not pretend an on-demand path
  exists. The false claim lives only in the registry.
- **Cockpit state:** `stale` on the canonical chart (measured), `lit` on the other two.
- **Density (§N.6):** the best in the batch and still incomplete. `get_tajik.ts` separates
  `hadda_lord_facts` from `varsha_year_lords` with independent `{offset, limit, total}` per
  section (the R-25 fix, `:153-163`), keeps a deprecated flat `rows` as an *honest* concatenation
  (`:255-262`), defaults to current-year-first ordering, and emits a real `empty_reason`. It has
  **no `density_contract`** (measured: 0 hits).
- **Drill:** ≤2 hops, and demonstrated live by `ahead.ts` calling the capability by URI.

### 7. Cost
`estimated_seconds = 14` declared — the batch's highest, and plausibly the batch's only
non-trivial one: 5 ayanamshas × 48 varshas × (2 solar-return bisections + 1 full annual chart
cast) ≈ 240 ephemeris-backed chart computations per build. **The only measured timing anywhere in
the batch is here**, and it is stale metadata rather than a duration:
`last_measured_at = 2026-06-11 18:12:42+00`, `measurement_count = 0`, `rows_per_second = NULL`.
`last_built_at` canonical `2026-08-12 15:25:49+00`.

### 8. Findings
F-E15 (MUST), F-E16 (MUST), F-E17 (NOW), F-E18 (NOW), F-E19 (NOW), F-E20 (NEVER-LATER).

---

## 5. `ga_prashna` — Praśna-viveka (Horary Judgment)

Full disposition in the dedicated section below. Rubric points, briefly:

**1. Pillar.** D-SERVICE — it is a *facility*, not a corpus: zero rows on a natal chart is its
correct output, and the pillar question is whether the facility's presence is honestly signalled.
**2. Dependencies.** Declared `{ga_positions, bg_prashna_rules}`. Real reads (from
`ga_prashna_writer.py`): `prashna_charts` (`:126-130`), `chart_facts fact_category='graha_position'`
(`:139-148`) → `ga_positions` ✓, `bg_prashna_significators` (`:179-183`) → one of the five tables
`bg_prashna_rules` seeds ✓. **`prashna_charts` is an undeclared edge** — it is neither an asset's
target table nor in `depends_on`, and it is the gating input (no row → 0 rows, `:131-134`).
**3. Leverage.** Two real consumers, detailed below. **4. Grounding.** Every judgment row carries
`classical_citation = "Tājika Nīlakaṇṭhī, Ch. 4–5 (Ithashāla + Phala adhyāya); Prashna Mārga
Ch. 6–7"` and every lagna row `"Tājika Nīlakaṇṭhī, Ch. 1 (Prashna Lagna Nirūpaṇa)"` (measured) —
`sruti`-labelable. **5.** n/a (the horary "clock" is the question instant, supplied by the caller).
**6/7/8.** below.

---

## `ga_prashna` dormant disposition

**Ruling context.** R-1 is settled and this section proposes no change to it: `bg_prashna_rules` /
`ga_prashna` are a **dormant horary facility by design, native-confirmed**. Nothing below is a
proposal to open, populate, or build out the facility. The purpose here is to record the
disposition against what is actually there — and what is actually there is materially different
from "an empty asset that has never run."

### D.1 — What exists today

**Tables (all measured):**

| table | rows | note |
|---|---|---|
| `prashna_charts` | **2** | PK `chart_id`; **no FK to `public.charts`** (measured `pg_constraint`: `prashna_charts_pkey` only) |
| `ga_prashna_lagna` | **5** | unique `(chart_id, ayanamsha_id, lagna_method)` |
| `ga_prashna_judgment` | **5** | unique `(chart_id, ayanamsha_id)` |
| `bg_prashna_significators` | 12 | L0, one row per `question_class` |
| `bg_prashna_lagna_methods`, `bg_prashna_tajik_yogas`, `bg_prashna_fructification_rules`, `bg_prashna_special_techniques` | (the other four `bg_prashna_rules` tables) | `bg_prashna_rules.target_floor = 41` summed across all five |

The asset's `count_sql` spans two tables —
`(SELECT COUNT(*) FROM ga_prashna_lagna WHERE chart_id=$1) + (SELECT COUNT(*) FROM
ga_prashna_judgment WHERE chart_id=$1)` — so a prashna chart counts 2 (1 lagna + 1 judgment) per
ayanamsha. For the canonical natal chart it is correctly **0**.

**Code:**
- `ga_writers/ga_prashna_writer.py` (362 lines) — judgment computation + `seed_prashna_judgment`.
- `ga_writers/ga_prashna_cast.py` (227 lines) — a **separate, orchestrator-bypassing cast path**
  ("The orchestrator adapter is bypassed; the caller supplies question-moment birth params
  directly"), with a 12-member `VALID_QUESTION_CLASSES` frozenset and a deterministic
  question-validator (`_REJECTION_PATTERNS` / `_FORWARD_MARKERS`) that rejects
  "what is / describe / explain"-shaped questions as non-horary.
- `pipeline/orchestrator/writers/ga_prashna.py:20` — the in-DAG `@register('ga_prashna')`
  WriterBase adapter, 5 substeps (one per ayanamsha).

**The facility door is open, not merely built.** `platform/python-sidecar/routers/prashna.py`
defines `POST /cast` and `platform/python-sidecar/main.py:71` mounts it:
`app.include_router(prashna_router.router, prefix="/api/compute/prashna",
dependencies=[Depends(verify_api_key)])`. So **`POST /api/compute/prashna/cast` is a live,
API-key-gated endpoint in the deployed sidecar** that will cast a question-moment chart, run
`build_ga_positions`, run the judgment, and `conn.commit()` — outside the orchestrator's
transaction. This is the single most important fact for the disposition: "dormant" describes a
*decision not to use it*, not an *absence of a usable path*.

**And it has been used.** Two prashna charts were cast on **2026-06-18** (measured
`prashna_charts.created_at`): `1789595b-…` ("Will I get this job offer before the end of the
month?", 17:25) and `b35046d8-…` ("Will I get the promotion I applied for this quarter?", 17:50),
both `question_class='career'`, both `prashna_lagna_method='tajik_moment_lagna'`, both with
`querent_natal_chart_id = 482012f1-…` (the native).

### D.2 — Would the L1 side consume `bg_prashna_rules` correctly if opened?

`bg_prashna_rules` is `catalog_status=CURRENT`, `is_active=t`, `target_floor=41`, `depends_on={}`.
Partially, and the honest answer has three parts:

1. **The significator lookup works but reads only the first name.** `:179-192` selects
   `querent_planet, quesited_planet` for the `question_class`, then takes
   `.strip().split(",")[0].strip()`. For `career` the L0 row is
   `quesited_planet = 'Saturn, Sun'` (measured) — **Sun is silently discarded**, and for
   `marriage` (`'Venus, Jupiter'`) Jupiter is discarded. The L0 table's own
   `significator_rule` prose says the additional karakas and the house lords are part of the rule.
   So the facility would consume the seed *lossily*.
2. **Four of the five `bg_prashna_rules` tables are never read at all.** The writer touches only
   `bg_prashna_significators`. `bg_prashna_lagna_methods`, `bg_prashna_tajik_yogas`,
   `bg_prashna_fructification_rules`, `bg_prashna_special_techniques` have no reader — the
   fructification rule is a hardcoded movable/fixed/dual sign-quality branch in Python
   (`:237-250`) rather than a read of `bg_prashna_fructification_rules`, the same
   constant-shadows-L0-table pattern as `ga_vastu` (§N.7 item 3).
3. **Mean motion is used where actual motion matters, and the retrograde flag is read then
   discarded.** `PLANET_DAILY_MOTION` (`:56-66`) is a mean-speed constant table used to decide
   which significator is "faster" and therefore whether the aspect is applying (Ithasala, → YES)
   or separating (Eesarpha, → NO) — the entire verdict hinges on it. Meanwhile the writer
   *does* read the real retrograde flag into `positions[...]["retrograde"]` at `:150` and then
   **never uses it again** anywhere in the file. A retrograde Mercury or Venus inverts the
   applying/separating direction; the code cannot see it.

### D.3 — What the dormancy costs today

**Build-time cost: effectively zero, and honestly so.** `ga_prashna` is `is_active=t` and runs on
every chart build: 5 substeps, each calling `seed_prashna_judgment` → `compute_prashna_judgment`,
whose *first* statement is `SELECT … FROM prashna_charts WHERE chart_id = %s` and which returns
`None` on no row (`:126-134`). Five PK-indexed misses. `estimated_seconds = 1`. Nothing is
recomputed, nothing is written. **This is the right design for a dormant facility and should not
be changed.**

**Cockpit-signal cost: real but small.** Measured `asset_throughput` for `ga_prashna`:
`1c826d5a` → `lit`/0 rows, `cb73cd3d` → `lit`/0 rows, `482012f1` → **`stale`**/0 rows. Three
charts, identical zero-row outcome, two different states, neither of which is `dormant` — even
though `dormant` exists in the vocabulary, is documented in `runner.py:154` as exactly this case
("DECLARED outcome — ran, legitimately 0 rows"), is honoured by `staleness.py:76` ("Assets with
state 'dormant' (no data to be stale about)"), and is in live use by `mi_sankalpa`. The
promotion logic at `asset_runner.py:1033`
(`final_state = 'lit' if (rows_written > 0 or zero_rows_is_complete) else 'dormant'`) resolves a
correct 0-row prashna build to `lit` via `zero_rows_is_complete` — defensible, but it means the
cockpit shows a dormant-by-design facility as *lit*, indistinguishable from a populated asset, on
two charts and as *stale* on the third. `asset_registry.data_disposition` — which already carries
a vocabulary (`RETAINED_AS_CAPITAL`, 6 assets) — is **NULL** for `ga_prashna`. **There is
currently no machine-readable record anywhere that R-1 exists.**

**Serving-surface cost: two live tools, and the §N.6-item-3 question resolves differently for
each.**

- `get_prashna_lagna` (`retrieval/registry/layers/L1_ganita/get_prashna_lagna.ts`) — **honest.**
  It emits a real `empty_reason` on 0 rows (`:93-95`), its description states plainly that
  "chart_id here references prashna_charts (the horary-question chart), not the natal chart", and
  it is registered in `L1_ganita/index.ts:48` but **not bridged to any MCP tool name** (measured:
  no entry in `tool_name_bridge.ts`) — registry-reachable only. No misleading envelope.
- `prashna_undertaking_get` (`platform-mcp/src/tools/register_p1_synthesis.ts:955+`) — **a live
  MCP tool that reads `ga_prashna_judgment` directly** (`:1011`). Its handling of the missing
  verdict is exemplary and explicitly documented (`:1074-1082`): it refuses to synthesise a
  numeric strength from the categorical `judgment_text`, floors `verdictStrength` to `null` with
  a stated reason, and averages the composite over only the components that have values. **But
  two lines later it does the opposite for its other two inputs:**
  `const bestElection = (…composite_quality…) ?? 0.5` and
  `const bestPosterior = (…posterior…) ?? 0.1`. On a chart with no `phala_muhurta` and no
  `phala_anchors` rows the "composite undertaking score" is `(0.5 + 0.1)/2 = 0.3` —
  a number computed entirely from two invented defaults, reported as a score. That is §N.7 item 6
  (a plausible-sounding default standing in for "I don't know") sitting directly beside a
  textbook-correct implementation of the same rule.
- **A naming collision that a reader will get wrong.** The MCP tools `prashna_ask` /
  `prashna_status` have **nothing to do with `ga_prashna`**. They are the pariprashna
  natural-language consultation pipeline (`platform/src/app/api/mcp/prashna_ask/route.ts` — "the
  prashna_ask↔engine bridge", planner + floor-compilation + NO-LEAKAGE + cost caps;
  `platform-mcp/src/tools/register_prashna_status.ts` polls that job). Measured: **zero**
  references to `ga_prashna` anywhere under the `prashna_ask` route or
  `lib/pipeline/prashna_ask_synthesis.ts`. So the tool list presents `prashna_ask`,
  `prashna_status`, and `prashna_undertaking_get` adjacently, and only the third touches horary.
  Anyone auditing "is the horary facility open?" from the tool list alone will answer wrongly in
  either direction.

**Data-integrity cost: five orphaned served rows.** This is the concrete harm the dormancy has
already produced, and it is measured, not inferred:
- `ga_prashna_judgment` and `ga_prashna_lagna` hold 5 rows each, all for `b35046d8-…`.
- `SELECT count(*) FROM chart_facts WHERE chart_id IN ('1789595b-…','b35046d8-…')` → **0 rows**.
- `SELECT * FROM charts WHERE id IN (…)` → **0 rows** (the six rows in `charts` are Abhisek,
  Abhinandan, Kiran Shenoy, Arunima Samantray, Steve Jobs, Elon Musk).
- `SELECT * FROM asset_throughput WHERE chart_id IN (…)` → **0 rows**.

So the writer's own precondition — "prashna chart exists but chart_facts has no graha_position
rows → return None" (`:155-163`) — was satisfied when these rows were written and is *not*
satisfied now. The positions were removed afterwards; `ga_prashna` declares **no `clear_tables`**
(measured: NULL — though note this is the project-wide norm, 1 of 128 assets has any), and there
is no FK on either prashna table, so nothing cascaded. **The result is five rows carrying
`querent_longitude` / `quesited_longitude` / `longitudinal_gap` that are served by a live MCP tool
and cannot be re-grounded to any L1 fact.** That is a B.3 / §N.5 break — a served claim whose
constituent facts do not resolve.

Also worth recording: `1789595b-…` has a `prashna_charts` row but **0** judgment and **0** lagna
rows — a cast that half-completed. And the surviving judgment shows a real cross-ayanamsha
divergence: four ayanamshas give `lagna_rashi = Capricorn` → `fructification_unit = 'days'`, while
`surya_siddhanta_classical` gives `Aquarius` → `'months'` (measured). Same question, same instant,
a 30× difference in the answer's time unit, with nothing flagging the disagreement. All five rows
read `tajik_yoga='no_direct_aspect'`, `judgment_text='UNCERTAIN'` (gap 56.42° against a mutual orb
of (12+9)/2 = 10.5) — which is honest, and is what the facility should say.

### D.4 — Proposed DORMANT disposition record (for W2 to adopt verbatim)

> **`ga_prashna` — DORMANT BY DESIGN (native ruling R-1, reaffirmed 2026-09-05).**
> The horary facility (`ga_prashna` + its L0 substrate `bg_prashna_rules`) is retained,
> built, and wired, and is **not to be opened, populated, or extended**. Its correct output on a
> natal chart is 0 rows; `target_floor = 0` is therefore correct, not a gap. It costs ~nothing at
> build time (5 PK-indexed misses per build) and this must not be "optimised" away — the in-DAG
> writer is what keeps the facility runnable if the ruling is ever revisited.
> The disposition is **not** "unbuilt": `POST /api/compute/prashna/cast` is a live mounted
> endpoint, two prashna charts were cast on 2026-06-18, and `prashna_undertaking_get` is a
> deployed MCP tool reading `ga_prashna_judgment`. Dormancy here is a decision, not a state of
> the code.
> Recorded machine-readably as `asset_registry.data_disposition = 'DORMANT_BY_DESIGN_R1'` (the
> column is NULL today and already carries a vocabulary), so that no future audit re-derives this
> question from row counts.

### D.5 — Deferred register (NOT work to do; the shape of a go-live rehearsal if R-1 were ever revisited)

Stated as register entries only, per the mandate:
- **DR-1.** Re-ground or retire the 5 orphaned `ga_prashna_judgment` / `ga_prashna_lagna` rows for
  `b35046d8-…`; decide whether prashna chart_ids should exist in `public.charts` (they do not) and
  whether `prashna_charts` should carry an FK.
- **DR-2.** Multi-significator handling: `split(",")[0]` currently discards the second and third
  karaka the L0 rule names.
- **DR-3.** Read the four unread `bg_prashna_rules` tables — in particular replace the hardcoded
  movable/fixed/dual fructification branch with `bg_prashna_fructification_rules`.
- **DR-4.** Use real (signed, retrograde-aware) motion instead of the mean-speed constant table;
  the retrograde flag is already read and discarded at `:150`.
- **DR-5.** Cross-ayanamsha divergence signalling for a horary verdict (the days/months split
  observed above).
- **DR-6.** Disambiguate `prashna_ask` / `prashna_status` (consultation) from
  `prashna_undertaking_get` / `get_prashna_lagna` (horary) in tool descriptions.
- **DR-7.** Whether the orchestrator-bypassing cast path (`ga_prashna_cast.py`, which commits its
  own transaction) is acceptable long-term against the §N.2 freeze.

---

## Exact-floor assessment — `ga_medical` 45, `ga_vastu` 40, `ga_tajaka` 240

Charter C12 / D-126 warns about "an equality wearing a floor's name." The three exact matches in
this batch are **not the same thing**, and the difference is decisive for W2:

| asset | floor | live | what the number is | verdict |
|---|---|---|---|---|
| `ga_medical` | 45 | 45 | `len(ALL_GRAHAS)=9 × len(CANONICAL_AYANAMSHAS)=5`, both constants in the writer; unconditional insert loop, no filter | **(a) correct §N.4 floor.** Structurally invariant. Verified 45 on all 3 built charts. |
| `ga_vastu` | 40 | 40 | `(len(ALL_GRAHAS) − 1 Ketu) × 5`; the skip is an unconditional `GRAHA_TO_DIRECTION.get()` miss | **(a) correct §N.4 floor.** Verified 40 on all 3 built charts. *But `expected_volume_formula` says 45.* |
| `ga_tajaka` | 240 | 240 | `((DEFAULT_REFERENCE_YEAR − birth_year + 1) + 5) × 5` — depends on a **hardcoded wall-clock constant** and on the **chart's birth year** | **(b) brittle equality.** Measured counter-evidence: 235 (`1c826d5a`), 305 (`cb73cd3d`) against the same global floor. |

**The distinction that matters:** for `ga_medical` and `ga_vastu` the count is a property of the
*writer's code* — it cannot change unless someone edits a constant, in which case the floor
*should* be updated in the same change. For `ga_tajaka` the count is a property of *when the build
ran and whose chart it is* — it changes without anyone touching the writer, and it is already
wrong for two of the three charts in the database.

**The distinction that does NOT save any of the three:** an exact floor over a deterministic count
has almost no detection power. All three pass with 100% of their rows semantically empty. 45
`ga_medical` rows with `indication_strength='unknown'` and `dosha_aggravated='{}'` (the exact
outcome of a silent `bg_medical_mappings` failure, §2.2) satisfy the floor perfectly. That hole is
what `integrity_check_sql` is for, and it is NULL on **0/19** L1 assets. The floors are doing the
job §N.4 assigns them (an honest record of what was achieved) and nothing more — which is correct;
the gap is that nothing else is doing the other job.

---

## Consolidated findings

| id | asset | finding | evidence | proposed triage | doctrine cited |
|---|---|---|---|---|---|
| **F-E1** | ga_ayurdaya | `target_floor = 0` while the asset has produced exactly **130** rows on every chart ever built. A floor of 0 is unfalsifiable. | registry `target_floor=0`; `asset_throughput.rows_written = 130` for `482012f1`, `1c826d5a`, `cb73cd3d`; live `count_sql` = 130; per-ayanamsha = 26 × 5 | **MUST** — set floor to achieved 130; populate `expected_volume_formula` as `AYANAMSHAS * (3 + 3*SEVEN + 2)` | §N.4 (floors are achieved counts) |
| **F-E2** | ga_ayurdaya | The only tool serving `fact_category='ayurdaya'` omits `fact_value_jsonb`, so `maraka_grahas` (2nd/7th signs, lords, occupants), `per_graha` contributions, `lagna_years` and the `harana_status` disclosure are **unreachable at 0 hops** — while the vidhi primitive that routes to it advertises "the maraka grahas". | `get_ayurdaya.ts:72-73` SELECT list; writer stores them at `ga_ayurdaya_writer.py:239-241, 263-265`; `vidhi/registry_data.ts:672` | **NOW** — add `fact_value_jsonb` to the SELECT | LEVERAGE; §N.6 (drill in ≤2 hops) |
| **F-E3** | ga_ayurdaya | `harana_status = 'base_only_haranas_deferred_to_w3'` is a real, correct incompleteness disclosure that **no consumer can see** (it lives only in the omitted jsonb). Callers read `98.75 / purnayu` with no sign the classical reductive haranas were never applied. | `ga_ayurdaya_writer.py:223-224, 241`; same SELECT omission as F-E2 | **NOW** — surface as a top-level flag on the response, not only inside jsonb | §N.7 item 4/6 (honest disclosure must be visible); §N.6 item 3 |
| **F-E4** | ga_ayurdaya | `fact_category='ayurdaya'` has **no row in `fact_category_ownership`** (59 rows, none for this category or this asset). Cross-ayanamsha `AMSAYU` band flips `madhyayu → alpayu` under `surya_siddhanta_classical` (30.66 vs 36.34) with nothing flagging the divergence. | `SELECT * FROM fact_category_ownership WHERE fact_category='ayurdaya'` → 0 rows; measured totals table in §1.4 | **NOW** — add the ownership row; record the band-flip as a known cross-ayanamsha divergence | §N.5 (L1 authority must be attributable) |
| **F-E5** | ga_medical | **Build-fatal assertion justified by a false classical claim.** `:286-293` halts the build if Sun's indication ≠ `'strong'`, on the stated ground that "Sun debilitated in Capricorn" — Sun debilitates in **Libra**. The identical error was already found and removed from `ga_vastu_writer.py:169-172`. It passes today for an unrelated correct reason (Capricorn is Sun's `enemy_sign`, score 0.26). | `ga_medical_writer.py:22-25, 286-293`; `ga_vastu_writer.py:169-172`; measured `dignity_d1='enemy_sign'`, `condition_score=0.26` | **MUST** — correct the rationale; downgrade the halt to a warning per the §N.4 S7 precedent | §N.7 item 1; §N.8 (the gate does not measure the claim it asserts) |
| **F-E6** | ga_medical | `nakshatra_body_part` is NULL on **40 of 45** rows — populated for Moon only — although all 9 grahas already have a stored `natal_nakshatra` and `bg_nakshatra_medical` is keyed by nakshatra alone. The answer is computable in the same transaction. | writer `:317` (`if graha == "Moon"`); measured `null_nbp = 40`, `null_nak = 0` | **NOW** — extend the existing lookup to all nine grahas | LEVERAGE (designed field reading NULL) |
| **F-E7** | ga_medical | Two **undeclared L0 dependencies** (`bg_medical_mappings`, `bg_nakshatra_medical`), both read inside `try/except` that degrade to empty and still insert 45 rows reporting success. No detector distinguishes "45 correct rows" from "45 empty rows". | `depends_on={ga_condition,ga_positions}`; reads at `:139-143` and `:213-217`; swallow at `:153-156` | **NOW** — declare both edges; add `integrity_check_sql` asserting non-empty `dosha_aggravated`/`organ_watch` | §N.8 (earned signal); §N.4 (cockpit truth) |
| **F-E8** | ga_medical | The serving tool emits **no `empty_reason`** — a 0-row response returns a populated-looking envelope carrying a medical `disclaimer` and a `provenance` block over an empty `rows`. No `density_contract`. | `get_medical_indications.ts:83-103` read in full; `grep density_contract` → 0 | **NOW** — add `empty_reason` + `density_contract`; name the two upstream authorities in `provenance.tables` | §N.6 items 3 and 4 |
| **F-E9** | ga_medical | Latent §N.7-item-2 defect: `_load_graha_positions` selects two `fact_category` values with no `build_id` filter and no `ORDER BY`, last-write-wins into a dict. Today unambiguous (1 row / 1 build per key) and `graha_sign_attributes` contributes zero rows for these keys — a dead branch. | `:171-194`; measured `PIN` query → 19 rows, all `count=1, builds=1`, all `graha_position` | **NEVER-LATER** — record as latent; not a live defect | §N.7 item 2 (with its honest scope note) |
| **F-E10** | ga_vastu | **Zero routed consumers.** `ga_vastu_planet_direction_map` has exactly two non-generated readers, both inside its own serving file; `direction_impact` is referenced nowhere else; and of 245 vidhi primitives **none** mention vastu (vs `ayurdaya_read` and `medical_read`, both in the `acharya_floor` band). The tool is a canonical face reachable only by explicit name. | greps quoted in §3.3; `vidhi/registry_data.ts` — 245 `primitive_id:`, 0 vastu; `canonical_faces.json:38` | **MUST** — W2 route decision: either add a `vastu_read` primitive or record an explicit no-consumer disposition | D-SERVICE; LEVERAGE |
| **F-E11** | ga_vastu | The per-chart weakened directions (L1) and the 24-row classical per-direction remedies (`bg_vastu_direction_remedials`, L0, separately served) are **never joined**. The instrument holds both halves of "your East is afflicted, here is the classical remedy" and no surface puts them together. | `get_vastu_directions.ts` vs `L0_brahmagyan/query_vastu_direction_remedials.ts`; no file references both tables | **MUST** — highest-value leverage item in the batch | LEVERAGE; D-SALIENCE |
| **F-E12** | ga_vastu | The graha→direction mapping is a **hardcoded Python dict shadowing the L0 `bg_vastu_directions` table** (which the registry description claims is the source). Values agree today; per-row citations do **not** — the writer broadcasts `"Mayamata Ch.6"` onto the Southwest/Rahu row whose L0 citation is `"Vastu Shastra tradition (Nairitya corner)"`. | `ga_vastu_writer.py:42-52, 54`; measured `bg_vastu_directions` 8 rows incl. the differing Rahu citation; registry `english_description` | **NOW** — read the L0 table (values *and* per-row citation) | §N.7 item 3 (no constant may shadow a stored value) |
| **F-E13** | ga_vastu | `expected_volume_formula = 'GRAHAS * AYANAMSHAS'` evaluates to **45**; `target_floor` and reality are **40**; the adjacent `volume_explanation` correctly explains the Ketu exclusion. The machine-readable field and the human-readable field disagree inside one registry row. | registry row, measured; live count 40 on all 3 charts | **NOW** — correct the formula to `(GRAHAS - 1) * AYANAMSHAS` | §B.8 / GA.1 (registries must not disagree) |
| **F-E14** | ga_vastu | Build-fatal canonical assertion (`Saturn must be 'strengthened'`) sits **0.075 above** its `≥0.7` cutpoint; a legitimate `ga_condition` re-tune halts the ayanamsha's build. Also: `ga_vastu` and `ga_medical` band the **same** `condition_score` with different boundaries (0.7 vs 0.6), undocumented. | `ga_vastu_writer.py:69-73, 173-179` (measured Saturn 0.775); `ga_medical_writer.py:88-94` | **NOW** — downgrade to warning per S7 precedent; document or reconcile the two threshold sets | §N.4 S7 precedent (honest tier over build-fatal); §N.7 item 6 |
| **F-E15** | ga_tajaka | **The batch's genuine "equality wearing a floor's name."** `target_floor=240` is `((DEFAULT_REFERENCE_YEAR − birth_year + 1) + 5) × 5` — a function of a hardcoded constant *and* the chart's birth year, asserted as a global constant. It is already wrong for two of three charts. | writer `:76, 729-731`; measured counts 240 / **235** (`1c826d5a`) / **305** (`cb73cd3d`) | **MUST** — replace the scalar floor with the formula, or scope the floor per chart | C12 / D-126; §N.4 |
| **F-E16** | ga_tajaka | **`DEFAULT_REFERENCE_YEAR = 2026` is a frozen wall-clock literal.** The "past→present+5" window silently degrades every year that passes without an edit — by 2032 the materialised window would end *before* the current varsha, with no error and no signal. Correct today (2026) by coincidence. | `ga_tajaka_writer.py:73-76, 729-731`; measured max `varsha_year = 48` = 2031-32 | **MUST** — derive from the build clock, or add a detector that fails when the window no longer covers the current varsha | §N.8 (a signal with no code path that could read false) |
| **F-E17** | ga_tajaka | **A registry claim with no implementation.** `volume_explanation` states out-of-window varshas "are computed on-demand by the retrieval tool via `ga_tajaka_writer.compute_varsha()`". `compute_varsha` has **no caller** — 3 grep hits: its own `def`, a self-referential string, and the seed line making the claim. `get_tajik.ts` is a pure SELECT. (The *tool* is honest — its `empty_reason` says the data "has genuinely not been computed"; only the registry lies.) | `ga_tajaka_writer.py:669, 817`; `scripts/seed/asset_registry_seed.ts:1340`; `get_tajik.ts:206-222, 266-272` | **MUST** — correct the `volume_explanation` to describe windowed storage | §N.8; §B.8 |
| **F-E18** | ga_tajaka | **Two false declared edges + a §N.5 authority inversion.** `depends_on` names `ga_dashas` (never read — no `chart_dashas` reference exists) and `ga_positions` (never read — the natal chart is **re-derived** via `compute_chart(bp)` at `:689, 745` rather than referenced from stored L1 longitudes). Only `ga_sensitive` (`tajik_triraashipathi`) is genuinely consumed. | greps in §4.2; `_read_trirashipathi:450-458` | **NOW** — correct `depends_on`; read the stored natal positions or add a divergence check against them | §N.5 (reference, never re-derive); §N.4 (cockpit truth) |
| **F-E19** | ga_tajaka | `_read_trirashipathi` uses `LIMIT 1` with **no `ORDER BY`** (pins `fact_category` + `fact_key`, so the CI lint passes; the ordering half of the rule is absent), and its failure is swallowed to `None`, silently degrading `candidate_lord_jsonb` scoring. Latent today: 1 row / 1 build per (chart, ayanamsha) across all 3 charts. | `:450-462`; measured `TRP` query → 15 rows, all `count=1, builds=1, distinct_vals=1` | **NOW** — add a total `ORDER BY`; log rather than swallow | §N.7 item 2 |
| **F-E20** | ga_tajaka | The three annual clocks (`ga_tajaka` solar-return, `ka_tithi_pravesha` lunar-return, `ka_sudarshana_varsha` tri-lagna progression) are genuinely non-overlapping and L3 **reads** L1 rather than re-deriving (`ahead.ts` calls `marsys://tool/L1/get_tajik`). But the concordance is declared **only in L3's prose** (`ka_tithi_pravesha.english_description` names `ga_tajaka`); `ga_tajaka`'s own row declares no temporal question, and nothing is machine-readable. | registry rows for all three, measured; `kala_views/ahead.ts:510-519, 585+` | **NOW** — record the temporal question on `ga_tajaka`'s own row | D-TIME (every temporal engine declares its question) |
| **F-E21** | ga_prashna | **The dormant facility's door is open and has been used.** `POST /api/compute/prashna/cast` is mounted (`main.py:71`) behind an API key; two prashna charts were cast 2026-06-18; `prashna_undertaking_get` is a deployed MCP tool reading `ga_prashna_judgment`. "Dormant" describes a decision, not the state of the code. | `routers/prashna.py`; `main.py:71`; measured `prashna_charts` 2 rows with `created_at` 2026-06-18; `register_p1_synthesis.ts:1011` | **MUST** — record the R-1 disposition against this reality (see §D.4); do **not** open further | R-1; D-SERVICE |
| **F-E22** | ga_prashna | **Five orphaned served rows.** `ga_prashna_judgment` / `ga_prashna_lagna` hold 5 rows each for `b35046d8-…` while that chart has **0** rows in `chart_facts`, **0** in `charts`, and **0** in `asset_throughput`. The stored `querent_longitude` / `quesited_longitude` cannot be re-grounded to any L1 fact, and a live MCP tool serves them. No FK on either table. | measured: 4 separate count queries; `pg_constraint` on both tables shows PK + UNIQUE only | **MUST** — re-ground or retire the rows (recorded as DR-1) | B.3 (derivation ledger must resolve); §N.5 |
| **F-E23** | ga_prashna | **No machine-readable record that R-1 exists.** `data_disposition` is NULL (the column already carries a vocabulary — `RETAINED_AS_CAPITAL`, 6 assets), and the throughput state for an identical 0-row outcome is `lit` on two charts and `stale` on the canonical one — never `dormant`, though `dormant` is a live state (`mi_sankalpa`) documented for exactly this case at `runner.py:154`. | measured `asset_throughput` 3 rows; `data_disposition` NULL; `runner.py:154`; `staleness.py:76`; `asset_runner.py:1033` | **NOW** — set `data_disposition = 'DORMANT_BY_DESIGN_R1'`; consider resolving a declared-dormant asset's 0-row build to `dormant` rather than `lit` | §N.8 (a signal must mean what it says) |
| **F-E24** | ga_prashna | `prashna_undertaking_get` floors the missing prashna verdict to `null` with an exemplary documented reason, then **two lines later** substitutes `?? 0.5` and `?? 0.1` for its other two inputs — so a chart with no muhurta and no anchor rows yields a "composite undertaking score" of 0.3 computed entirely from invented defaults. | `register_p1_synthesis.ts:1074-1082` (the correct half) vs the `?? 0.5` / `?? 0.1` lines immediately following | **NOW** — floor both to null with reasons, as the verdict already is | §N.7 item 6 (an honest null beats an invented judgment) |
| **F-E25** | ga_prashna | **Naming collision.** `prashna_ask` / `prashna_status` are the pariprashna NL-consultation pipeline and contain **zero** references to `ga_prashna`; only `prashna_undertaking_get` and `get_prashna_lagna` touch horary. The tool list presents them adjacently, so "is the horary facility open?" is unanswerable from tool names. | `api/mcp/prashna_ask/route.ts` header + measured 0 `ga_prashna` refs; `register_prashna_status.ts`; `register_p1_synthesis.ts:1011` | **NOW** — disambiguate in tool descriptions (recorded as DR-6) | §N.6 item 4 (machine-readable honesty) |
| **F-E26** | ga_prashna | The L1 side would consume `bg_prashna_rules` **lossily** if ever opened: `split(",")[0]` discards the second/third karaka (career `'Saturn, Sun'` → Sun dropped); 4 of 5 `bg_prashna_rules` tables have no reader at all; fructification is a hardcoded sign-quality branch shadowing `bg_prashna_fructification_rules`; and the retrograde flag is read at `:150` then never used, while mean motion decides the applying/separating verdict. | `ga_prashna_writer.py:150, 179-192, 237-250`; measured `bg_prashna_significators` 12 rows | **NEVER-LATER** — deferred register only (DR-2/3/4); **not** work to do under R-1 | §N.7 item 3; R-1 |
| **F-E27** | batch | **0 of 19 L1 assets carry `integrity_check_sql`**, and **no batch-E asset has any measured build cost** (`rows_per_second` NULL, `measurement_count = 0` on all 15 throughput rows). The exact floors (§ exact-floor assessment) all pass with 100% semantically-empty rows; nothing else checks content. `estimated_seconds` (4/2/1/14/1) is declared, never measured. | measured registry + `asset_throughput` queries quoted at the top | **NOW** — batch-level: `integrity_check_sql` is the correct instrument for the hole the floors structurally cannot cover | §N.8; §N.4 (cockpit truth) |
| **F-E28** | batch | **No batch-E serving capability declares a `density_contract`** (0/5: `get_ayurdaya`, `get_medical_indications`, `get_vastu_directions`, `get_tajik`, `get_prashna_lagna`), so no CI/census harness can assert byte caps or empty-reason coverage for any of them. Two (`get_medical_indications`, `get_vastu_directions`) have no `empty_reason` at all. | `grep density_contract` over all five → 0; `empty_reason` present in 3 of 5 | **NOW** | §N.6 item 4 |

---

*End of L1-W1 Batch E analysis. Read-only pass — no repository file other than this one was
created or modified, no build was dispatched, and every DB access was a SELECT.*
