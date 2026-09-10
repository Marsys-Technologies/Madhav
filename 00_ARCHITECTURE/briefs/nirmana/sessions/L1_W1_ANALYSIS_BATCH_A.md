---
artifact: L1_W1_ANALYSIS_BATCH_A
campaign: NIRMĀṆA
session: L1
wave: W1 (ANALYZE)
batch: A
assets: [ga_positions, ga_vargas, ga_dashas]
produced_on: 2026-09-05
status: DRAFT
mode: READ-ONLY (no repo file mutated other than this artifact; no build dispatched; no git state changed)
canonical_chart: 482012f1-710e-4a25-994a-93821f5871aa
comparison_charts: [1c826d5a-41cb-4450-b4dc-59d440e5f75a, cb73cd3d-9eba-4220-9902-0de91566e980]
live_build_analysed: 6479bb56-e0b1-4294-9bb2-d2fb1c987bb6 (2026-08-08 00:17–00:29 UTC)
---

# L1 W1 ANALYZE — Batch A (`ga_positions` · `ga_vargas` · `ga_dashas`)

Batch A is the L1 root (`ga_positions`) and the two heavy assets that hang off it. Every number
below was measured live via `~/nirmana-s/bin/nq` against production, or read from source at a
cited `file:line`. Where I could not measure something, I say so explicitly.

---

## Headline — read this if nothing else

1. **`ga_vargas` computes every graha's longitude for the wrong instant.**
   `_compute_varga_positions` calls `drik.sidereal_longitude(jd_ut, planet)` with a **local-time**
   JD and **no `Place`** (`ga_vargas_writer.py:844`), while `ga_positions` routes through
   `drik.dhasavarga(jd_ut, place, …)` (`pyjhora_adapter/positions.py:53`), which is place-aware.
   The result is that every D1 graha longitude in `chart_divisionals` is **birth time +
   `tz_offset_hours`** (+5h30m for this chart). Measured, per-graha, as an offset exactly
   proportional to each body's daily motion (Sun +0.2324°, Moon +2.7169°, Saturn +0.0075°,
   Rahu −0.0121° — every one of them 0.229 day of motion). `Lagna` is unaffected (`drik.ascendant`
   *is* place-aware) and agrees with `chart_facts` to 6 decimals, which is why the FORENSIC gate
   (D1 Sun = Capricorn, D1 Lagna = Aries) passes anyway.
   **Consequence, measured:** 266 of 1,215 `varga_position` sign rows (21.9%) disagree with the
   sign implied by `ga_positions`' own L1 longitude, and the mismatch rate scales with the varga
   divisor exactly as a constant longitude error must — D4 2%, D9 4%, D12 18%, D60 38%, D150 56%,
   D2700 96%. Everything derived from `varga_position` (dignity, vargottama, ashtakavarga,
   vimsopaka, karaka, rollup) inherits it. → **F-A1, MUST.**

2. **`ga_vargas` silently discards 15,078 of the 38,620 rows it computes (39%).**
   `asset_throughput.rows_written = 38,620`; live `count(*) = 23,542`. Two proven mechanisms:
   (a) `chart_divisionals_unique_idx` is `(chart_id, graha, ayanamsha_id, varga, fact_category,
   fact_key)` — **`fact_subject` is not in it**, so rows that differ only by subject collapse under
   `ON CONFLICT … DO NOTHING`; `_build_d30_lord_per_amsa_rows`' own docstring says "5-lord chain ×
   12 signs = 60 rows" and exactly **10** survive (only `D30.S1` and `D30.S2`); `varga_house_lord`
   emits 12 rows/varga with constant `fact_key='lord'` and only 7 survive in D1.
   (b) `replace_prior_chart_divisionals` deletes at `(chart_id, ayanamsha_id, varga)` grain while
   the writer inserts at a six-column grain and calls `_write_rows_batch` five separate times per
   ayanamsha — so the D30-lords pass **deletes the D30 rows the main loop just wrote** (live: D30
   has 10 rows and 1 category; its peers have 147–163 rows and 10–16 categories).
   `_write_rows_batch` returns `len(rows)` on the happy path, so nothing detects any of it.
   → **F-A2 / F-A3, MUST.**

3. **The `ga_dashas` −52,612 floor deficit is fully attributed and the floor is the stale party —
   but not for the convenient reason.** The whole delta decomposes into five named causes summing
   to exactly −52,612, dominated by **kalachakra −70,996**, which is *fabricated repetition that a
   classical-correctness fix deliberately removed* (register M-6, PR #527). Detail in §`ga_dashas`
   / C12 below. → **F-A9.**

4. **83,740 `yogini` dasha rows carry a computed lord natal condition that `get_dashas` throws
   away and cannot re-derive** — its `GRAHA_NAME_TO_FACT_SUBJECT` map only knows the 9 graha
   display names, and yogini rows store the Yogini name (`Pingala`, `Bhadrika`, …) in
   `lord_graha`. The writer already resolved them correctly (`Pingala → 8.47 = Sun's rupa`, live).
   → **F-A11, the batch's cleanest leverage finding.**

5. **Two L1 surfaces disagree about the same fact for the same chart+ayanamsha.**
   `chart_divisionals` D1 `varga_dignity` says the Sun is `Enemy`; `chart_facts`
   `graha_dignity_per_varga.D1_SUN.dignity_state` says `neutral`. `ga_dashas` reads the first and
   stores `enemy_sign`; `get_dashas.ts` re-derives from the second and serves `neutral`, on
   **28,923** rows. → **F-A12, MUST** (§N.5 is explicit that this is halt-worthy, not a stored
   divergence).

6. **0 of the 3 assets carry `integrity_check_sql`, and 0 carry `expected_volume_inputs`.**
   Confirmed by direct registry read. For `ga_positions` I *derived* an exact closed-form volume
   (below) that reproduces 1,205 to the row — so the NULL is not "unknowable", it is unwritten.
   → **F-A14 / F-A15.**

---

## `ga_positions`

Registry: `layer=ganita · scope=per_chart · target_table=chart_facts · target_floor=50 ·
estimated_seconds=5 · catalog_status=CURRENT · has_substeps=f · domain=chart · depends_on={}`.
Writer: `pipeline/orchestrator/writers/ga_positions.py` (thin adapter) →
`ga_writers/ga_positions_writer.py` (688 lines).

**1 — Pillar / doctrine service.** D-GROUNDING (P3) foundationally: this is the asset every other
L1 fact and every L2+ `constituent_facts_array` ultimately resolves back to, and it is the one
that runs the FORENSIC gate (`forensic_gate(chart_output, canonical_id)`,
`ga_positions_writer.py:626`, asserted only for the native chart). Also D-SERVICE (KP cusps,
dignity, positions surfaces). Still the right instrument: a deterministic PyJHora compute →
atomic-fact-row writer is exactly what an L1 root should be, and it is the only one of the three
that reads nothing from the DB, so it cannot inherit anyone's error.

**2 — Real vs declared dependencies. MATCH.** `depends_on = {}` and the writer performs **zero**
`SELECT`s (grep for `SELECT`/`FROM` in `ga_positions_writer.py` returns nothing but the INSERT).
Its only inputs are `ctx.config['birth_params']` (orchestrator-fetched from `public.charts`) and
PyJHora. `built_against_upstream_hash = e3b0c44298fc1c14…` in `asset_throughput` — the empty-input
hash — which is honest and consistent. No hidden edge, no false edge.

**3 — LEVERAGE.** The writer owns **five** `chart_facts` categories, live counts for the canonical
chart: `graha_position` 430 · `bhava_cusps` 360 · `house_chalit` 225 · `graha_sign_attributes` 100
· `sandhi_flag` 90 = **1,205**, matching `asset_throughput.rows_written` exactly.
- `graha_position`, `graha_sign_attributes`, `bhava_cusps` all have real, live consumers
  (`L1_ganita/get_kp_cusps.ts:37,230`, `get_dignity.ts:13`, `get_av_transit_gating.ts:272`,
  `coverage_matrix.ts:227`, MCP `ganita_kp_cusps_get` / `ganita_positions_get`).
- **`house_chalit` (225 rows) and `sandhi_flag` (90 rows) have no live consumer.** Grepping the
  whole retrieval + MCP tree, the only hits are a description string
  (`platform-mcp/src/resources/vidhi/registry_data.ts:515`, "Chalit (bhāva-cuspal) chart facts:
  bhava_cusps, house_chalit, sandhi_flag"). The one code reader,
  `platform/src/lib/ganita/facts_store.ts:160`, does `get('HOUSE_CHALIT')` where `get` matches
  `fact_id === 'PLN.<PLANET>.HOUSE_CHALIT'` (`facts_store.ts:154`) — a legacy `fact_id` scheme this
  writer never emits (it writes `fact_category='house_chalit'`, `fact_key='chalit_house_sripati'`,
  `ga_positions_writer.py:481`). Its only caller path is `forensic_render.ts`, which CLAUDE.md §B
  records as **RETIRED**. So DR-2's whole bhāva-chalit second data layer is computed, stored, and
  read by nobody. Textbook built-but-unplugged.

**4 — Grounding.** Not applicable, and correctly so. These are `pratyaksa`-class instrument
outputs (Swiss Ephemeris/PyJHora longitudes and cusps). Forcing a `grounding_tier` onto a sidereal
longitude would be a category error. The row-level honesty signal that *does* belong here is
`verification_pass_status`, which is present. The genuine grounding artefact is the FORENSIC gate
(7/7), and it lives in the right place.

**5 — Temporal identity.** N/A. Natal-instant only; no window, no arbitration question.

**6 — Service.** Real consumers for 3 of 5 categories (point 3).
- **`target_floor = 50` vs achieved 1,205 — 24× stale.** §N.4 says the floor is the achieved count
  after build; 50 is the ancient `ganita_positions` figure, not this asset's.
- **`count_sql` is wrong**: `… fact_category IN ('graha_position','graha_sign_attributes',
  'bhava_cusps')` counts **890** and misses `house_chalit` + `sandhi_flag` = **315 rows, 26% of the
  asset**. This is exactly the "cockpit truth" trap §N.4 names — the stats route reads `count_sql`,
  so the cockpit under-reports this asset by a quarter.
- Density (§N.6): rows are uniformly `pratyaksa`; no catalog-vs-confirmed layering needed. Drill
  path to L1 fact ids exists (`fact_id` is emitted and referenced by Bodha).

**7 — Measured cost.** Registry `estimated_seconds = 5`. **Measured from `build_run_assets`: 54
completed runs, mean 17 s, max 165 s; the three most recent real builds took 98 s, 145 s, 165 s**
(2026-08-07/08). So the declared estimate is **20–33× under** current reality. `asset_throughput`
carries `rows_per_second = NULL`, `measurement_count = 0`, `history = []` for all three assets in
this batch — the throughput measurement surface is declared but never populated.

**8 — Findings.** F-A4 (count_sql omits 2 categories, MUST), F-A5 (floor 50 vs 1,205, NOW),
F-A6 (`house_chalit`/`sandhi_flag` zero live consumers, NOW), F-A16 (`estimated_seconds` 5 vs
measured 98–165 s, NOW), F-A14/F-A15 (no `integrity_check_sql`, no `expected_volume_inputs`).

---

## `ga_vargas`

Registry: `target_table=chart_divisionals · target_floor=22092 · estimated_seconds=94 ·
has_substeps=t · depends_on={ga_positions} · expected_volume_formula='VARGAS * GRAHAS *
AYANAMSHAS' · volume_explanation='60 vargas × 9 grahas × ayanamsha count — structural'`.
Writer: `ga_writers/ga_vargas_writer.py` (3,097 lines), driven per-ayanamsha as 5 substeps.
Live: **23,542** rows, identical for all three charts (structural, chart-independent).

**1 — Pillar.** D-GROUNDING (P3) + D-SALIENCE (P5): the varga picture is what dignity, vargottama,
vimsopaka and ashtakavarga salience all rest on. Still the right instrument in *shape* — a
deterministic per-varga fact table is correct — but see point 2: it should be consuming
`ga_positions`, not recomputing longitudes, and the recomputation is where F-A1 came from.

**2 — Real vs declared dependencies. FALSE EDGE + hidden L0 edge.**
- **False edge:** `depends_on = {ga_positions}` but the writer never reads `chart_facts`. Its only
  `SELECT`s are `bg_shashtiamsha_deities` (`ga_vargas_writer.py:584`) and its own
  `chart_divisionals` (`:2639`, the `_check_already_written` guard). D1 positions are recomputed
  from scratch in `_compute_varga_positions` (`:814–850`) from `birth_params`. The declared edge is
  scheduling-correct-by-accident but data-false.
- **Hidden edge:** `bg_shashtiamsha_deities` is an L0 table and is not declared anywhere in
  `depends_on`.
- This is not a bookkeeping nit. Because the edge is false, `chart_facts.graha_position` and
  `chart_divisionals` D1 are **two independent computations of the same quantity with no
  cross-check** — and they disagree (F-A1). Had the declared edge been real (§N.5: reference the
  L1 fact, do not re-derive it), the timezone defect could not have existed.

**3 — LEVERAGE.** `get_divisionals.ts` is a real consumer. Two concrete losses:
- **`house_from_varga_lagna` is already persisted and the serving layer recomputes it.**
  `get_divisionals.ts:5–19` states "Persistence of this value is explicitly out of scope (serving
  leg only)" and computes it on read plus an extra `Lagna`-lookup query. Live measurement: **1,450
  rows** already carry `fact_key='house_from_varga_lagna'` (50 per varga × 29 vargas). The comment
  is stale; the work is duplicated.
- **Its declared varga coverage is under-stated.** The tool description enumerates "the 16 standard
  vargas (D1–D60 …)"; the table actually holds **33** distinct `varga` values including D11, D14,
  D15, D21, D32, D33, D50, D54, D108, D150, D2700 and `CROSS`. A caller reading the description
  will not know D108/D150/D2700 are reachable. Its `~2,465/21,635 rows have house populated` note
  is also stale — live is **3,940 / 23,542**.

**4 — Grounding.** Not applicable to the positional rows (`pratyaksa` computation). Two categories
lean interpretive-adjacent — `varga_deity_attribution` (630 rows, sourced from the L0
`bg_shashtiamsha_deities` table) and `varga_dignity` (1,305) — but both are classical lookup/rule
applications, not judgments, so an honest read is: no `grounding_tier` on this asset; the
`source_citation` / `formula_provenance_text` columns already carry what a lookup needs.

**5 — Temporal identity.** N/A — natal snapshot only.

**6 — Service.** Real consumer, but three defects:
- **`target_floor = 22,092` vs achieved 23,542** — stale (and, per §N.4, floors are set to the
  achieved count, so this one is simply behind, not fabricated).
- **`expected_volume_formula = 'VARGAS * GRAHAS * AYANAMSHAS'` = 60 × 9 × 5 = 2,700, which is
  8.7× off the real 23,542**, and wrong on both factors: there are 33 vargas not 60, and the row
  grain is (graha × varga × **fact_category × fact_key**), not one row per graha-varga.
  `expected_volume_inputs` is NULL. Under C12 that NULL is itself the defect.
- **`rows_written = 38,620` is not a measurement of rows written** — see F-A2/F-A3.

**7 — Measured cost.** Registry `estimated_seconds = 94`; measured mean 256 s over 48 completed
runs, but the three most recent real builds were **87 s, 91 s, 90 s** — so the current estimate is
accurate and the historical mean is inflated by old slow runs (max 3,536 s). 5 errors / 11 aborts
out of 69 recorded runs.

**8 — Findings.** F-A1 (tz defect, MUST), F-A2 (unique-index grain loses rows, MUST), F-A3
(`replace_prior` deletes intra-build, MUST), F-A7 (false edge + hidden L0 edge, NOW), F-A8
(`house_from_varga_lagna` recomputed though persisted; stale tool description, NOW), floor +
formula items above.

### Detail: the timezone defect (F-A1)

Measured offset, `chart_divisionals` D1 `degree_in_sign` minus `chart_facts`
`graha_sign_attributes.degree_in_sign`, identical across all 5 ayanamshas:

| graha | offset (°) | ÷ daily motion |
|---|---|---|
| Sun | +0.23242 | 0.229 d |
| Moon | +2.71686 | 0.229 d |
| Mercury | +0.32222 | 0.229 d |
| Venus | +0.28153 | 0.229 d |
| Mars | +0.10210 | 0.229 d |
| Jupiter | +0.04501 | ~0.23 d |
| Saturn | +0.00753 | ~0.23 d |
| Rahu/Ketu | −0.01214 | 0.229 d (retrograde) |

0.229 day = **5 h 30 m** = this chart's `tz_offset_hours`. `Lagna` offset is **0.000000**.

Code: `ga_vargas_writer.py:844` `raw_lon = drik.sidereal_longitude(jd_ut, planet_map[pid])` — no
`place`, so PyJHora treats the local-wall-clock JD as UT. Two lines earlier,
`ga_vargas_writer.py:828` `asc = drik.ascendant(jd_ut, place)` **does** pass `place`, which is
exactly why Lagna is right and every planet is wrong. Contrast `pyjhora_adapter/positions.py:53`,
`drik.dhasavarga(jd_ut, place, …)`.

Sign-level impact (comparing stored `varga_position.sign` against
`floor(chart_facts.longitude_sidereal × n / 30) mod 12`, which is `_compute_general_varga`'s own
formula at `ga_vargas_writer.py:491–500`; D2/D3 excluded because they use special formulas):

| varga | rows | mismatches | | varga | rows | mismatches |
|---|---|---|---|---|---|---|
| D1 | 45 | 1 | | D27 | 45 | 11 |
| D4 | 45 | 1 | | D32 | 45 | 12 |
| D9 | 45 | 2 | | D45 | 45 | 14 |
| D12 | 45 | 8 | | D54 | 45 | 17 |
| D15 | 45 | 9 | | D60 | 45 | 17 |
| D16 | 45 | 7 | | D108 | 45 | 22 |
| D24 | 45 | 10 | | D150 | 45 | 25 |
| — | | | | D2700 | 45 | 43 |

**Overall 266 / 1,215 = 21.9%.** The one D1 mismatch is the Moon under `raman`:
divisionals say Pisces 1.218°, `chart_facts` says Aquarius 28.502°.

*Honest scoping:* I did not re-run the writer, so I am inferring the fix's effect, not verifying
it. What I verified is (a) the constant tz-proportional offset, (b) the two call sites' differing
`place` argument, and (c) that the FORENSIC varga gate only checks D1 Sun sign + D1 Lagna sign
(`forensic_gate_vargas`, `ga_vargas_writer.py:2705–2727`), both of which survive a 5.5 h shift.

---

## `ga_dashas`

Registry: `target_table=chart_dashas · target_floor=536471 · estimated_seconds=564 ·
has_substeps=t · depends_on={ga_positions} · expected_volume_formula='(9 + 81 + 729) *
AYANAMSHAS'` (the `volume_explanation` already admits this formula "under-counts by ~130×").
Writer: `ga_writers/ga_dashas_writer.py` (3,672 lines); orchestrator adapter plans
8 systems × 5 ayanamshas + 1 post-pass = 41 substeps.
Live: **483,859** rows, one `build_id` (`6479bb56…`), computed 2026-08-08 00:20:28→00:27:28.

**1 — Pillar.** D-TIME (P6) primarily — this is the substrate every Kāla engine and every
dasha-phala claim rests on — with D-SALIENCE (P5) support via the `lord_natal_*` and
`convergence_count_at_start` columns. Still the right instrument.

**2 — Real vs declared dependencies. TWO HIDDEN EDGES, one of them raced.**
Declared `depends_on = {ga_positions}`. Actually reads:
- `chart_facts` `graha_position` (`ga_dashas_writer.py:525`) → ga_positions ✔ declared.
- `chart_facts` `graha_shadbala_total` (`:563`) → **written by `ga_strength`, not `ga_positions`.
  Undeclared hidden edge.**
- `chart_divisionals` D1 `varga_dignity` (`:549`) → **written by `ga_vargas`. Undeclared hidden
  edge, and this one races**: `build_run_assets` shows `ga_vargas` and `ga_dashas` both starting
  at `2026-08-08 00:20:27` (same second) with `ga_vargas` ending 00:21:56 while `ga_dashas` was
  already writing rows from 00:20:28. Because `ga_vargas` does delete-then-insert inside its own
  transaction, a concurrently-running `ga_dashas` reads the **previous build's** D1 dignity under
  MVCC. Live dignity is populated on all 292,344 eligible rows, so nothing crashed — which is
  precisely the problem: the race is silent.
- `reference_nakshatras` (`_load_nakshatra_lords_l0`, `:110`) → undeclared L0 edge.

**3 — LEVERAGE.** `get_dashas.ts` (692 lines) is the main consumer; `L3_kala/query_active_dashas.ts`
and `L5_mimamsa/query_mechanism_retrodiction.ts` also read the table. Four measured losses:
- **Yogini lord condition, 83,740 rows (17.3% of the corpus), served as NULL.**
  `get_dashas.ts:459–465` builds `GRAHA_NAME_TO_FACT_SUBJECT` from the nine graha display names
  only, then at `:519–526` unconditionally overwrites `lord_natal_dignity_d1` /
  `lord_natal_shadbala_total` with the re-derived value ("Authoritative re-derived values override
  the (NULL/wrong) denormalized columns"). Yogini rows store `lord_graha = 'Pingala' | 'Bhadrika'
  | …`, so the map misses and both fields serve `null`. The writer had already resolved them:
  live, `Pingala → 8.47` (= Sun's rupa), `Ulka → 7.83` (= Saturn's), `Sankata → 0.375` (= Rahu's).
- **The premise of that override block is now false.** `get_dashas.ts:449–451` says the
  denormalized columns are "wrong or NULL for every row (native chart: 100% NULL on both)". Live:
  they are populated on **292,344 / 483,859 rows (60.4%)** — the V-1/G-7/D-1 fix (PR #521,
  2026-07-10) made `_activate_natal_context` populate them. I checked the values:
  `lord_natal_shadbala_total` agrees with `chart_facts.graha_shadbala_total` on **208,604 / 208,604
  compared rows, zero disagreements.** The remaining 191,515 NULLs are exactly
  `chara_karaka + kalachakra + narayana` (155,135 + 35,053 + 1,327 = 191,515) — the three *rāśi*
  daśās whose lord is a sign, not a graha. That is an honest N/A, not a gap.
- **`narayana` is unreachable through `get_dashas`.** `KNOWN_SYSTEMS` (`get_dashas.ts:42–44`) lists
  8 systems and omits `narayana`; a caller passing `system=narayana` falls into
  `systemRequestedButUnknown` (`:349`), which adds **no** filter, so they silently get every
  system instead of the one they asked for. `L3_kala/query_active_dashas` *does* know all 9
  (its test asserts them at `query_active_dashas.test.ts:46`), so this is a `get_dashas`-local gap
  covering 1,327 live rows.
- **`concurrent_system_lords_jsonb` / `convergence_count_at_start` exist only at level 1.**
  Populated on **839** rows — exactly the sum of all level-1 rows across the 8 systems. Any
  consumer wanting cross-system convergence below mahādaśā grain gets nothing.

**4 — Grounding.** Not applicable as a tier — these are computed period boundaries. The honest
signal here is `verification_pass_status`, and it is *thin but honest*: only `vimshottari` is
`two_pass_verified` wholesale (45,664, backed by `_vimshottari_independent_verifier.py`, 1,483
lines, wired into the write path by PR #1056). For every other system the verifier stamps only the
level-1 rows and everything deeper is `single`: ashtottari 65 `classical_match` / 32,895 `single`;
yogini 175 / 83,565; chara_karaka 106 / 155,029; naisargika 40 / 21,905; mudda 240
`two_pass_verified` / 102,125 `single`; narayana 105 / 1,222; kalachakra **35,053 all `single`**.
That is ~88% of the corpus at the lowest honest tier, which is the correct S7 answer, not a defect
— but it should be *disclosed* at serve time, and §N.6 layering would say so.
**Doctrine violation found:** §N.4's S7 bullet requires tiers be emitted via
`brahmagyan/verification_vocab.py` named constants, never bare literals. `ga_dashas_writer.py`
passes bare string literals into `_build_row` at (at least) lines 1172, 1205, 1236, 1265, 1370,
1413, 1498, 1531, 1562, 1592, 1676 (`"two_pass_verified"`), 2246/2265 (`"single"`, narayana) and
2846 (`"two_pass_verified"`, kalachakra — note the DB shows kalachakra as 100% `single`, i.e. a
later verifier demotes it, so the literal at the call site is also *misleading*). The constants are
imported at `:41–46` and simply not used at these sites.

**5 — Temporal identity (D-TIME).** This asset answers *"which lord governs which interval, under
which system, under which ayanamsha"* over a declared window `[1950-01-01, 2100-12-31]`
(`ga_dashas_writer.py:66–67`). Three arbitration facts a D-TIME consumer needs and currently is not
told:
- **The window is not uniform across systems.** `vimshottari` genuinely spans 1950-01-01 →
  2100-12-31. `kalachakra` spans **birth (1984-02-05) → 2055–2079 depending on ayanamsha** — by
  deliberate classical design (paramāyuṣ is the system's own ceiling; see C12 below). Nothing in
  the row or the registry discloses that two systems answer over different horizons.
- **`sandhi_flag` is true on 436,738 / 483,859 rows (90.3%).** It is now honestly defined
  (`duration_days < 20`, set once in `_build_row`; the old always-true tautology was killed by V-11,
  `compute_sandhi_post_pass` docstring at `:2903–2917`) — but at level 4 nearly every period is
  under 20 days, so the flag carries almost no information while `get_dashas.ts:184–191` narrates
  it as *"the ${name} is in its sandhi (junction) window — classically a transitional caution
  period"*. A caution sentence that fires on 90% of rows is a §N.7-class narration hazard.
  The genuinely informative companions, `sandhi_with_next_dasha_lord` / `next_dasha_start_iso`,
  exist on **799** rows only (839 L1 rows minus one terminal per system×ayanamsha = 40 — exact).
- **Who arbitrates disagreement between systems** is undefined at L1 and that is correct (L1
  emits, L3/L4 adjudicate) — but `convergence_count_at_start` being level-1-only means the
  adjudication surface is thinner than the corpus.

**6 — Service.** Real consumers.
- `count_sql` is correct and chart-scoped.
- **`target_floor = 536,471` is below live (483,859) by 52,612 — see C12.**
- `anchored_solar_return_iso` is populated on **45** rows — the 9 kalachakra level-1 rows × 5
  ayanamshas, set as a "coarse elapsed-time marker" (`ga_dashas_writer.py:2833–2836`). It is
  **NULL on all 102,365 `mudda` rows**, even though Mudda *is* the annual varṣa system, the writer
  has `_mudda_solar_return_jd` (`:2467`), and `varsha_year_lord` is populated on exactly those
  102,365 rows. That is a computed-but-unstored gap on the one system the column was named for.
- **The two scope-cap sentinels never land — for two reasons, one of them undocumented.**
  Live: `SELECT chart_id, count(*) FROM chart_dashas WHERE system_id='scope_cap' GROUP BY 1`
  returns **0 rows for all three charts**, despite PR #919 (2026-07-31) landing the orchestrator
  path and this build running 2026-08-08. `write_dasha_scope_cap_sentinels`' own docstring
  (`:3413–3424`) discloses the first reason honestly (the Prāṇa row's `level_n=5` violates
  `cd_level_n_max4`) and says SD-DASHA-1 stays open. It does **not** disclose the second: both
  rows set `verification_pass_status = 'scope_cap_sentinel'` (`:3339`), and the live table
  constraint is `CHECK (verification_pass_status = ANY (ARRAY['two_pass_verified',
  'classical_match','divergent_flagged','single']))`. So the **KP** sentinel — which the docstring
  implies still writes — also fails, and the function's declared return of "0, 1, or 2" is
  always 0. §N.8: a signal with no detector behind it. (Same defect class as commit 78ebadbaf,
  2026-07-17, "Narayana verification_pass_status enum violation".)
- `narayana` is 2 levels only (105 L1 + 1,222 L2, no L3/L4), against the writer's own CRITICAL
  OVERRIDE 1 ("DEPTH = 4-level Sukshma"). The docstring declares this honestly
  (`:2185–2191`: "sufficient for the CR-104 wiring deliverable … without expanding scope"), so this
  is a disclosed scope decision, not a silent gap — but it is not disclosed at serve time.

**7 — Measured cost.** Registry `estimated_seconds = 564`; measured 482 s / 491 s / 501 s on the
three most recent real builds — accurate and slightly conservative. Historical: 56 completes,
mean 1,118 s, max 4,199 s, **20 errors and 11 aborts out of 121 recorded runs (26% non-success)**,
including a `KeyError: 1` in `_run_concurrency_post_pass_db` and `worker_crash: OperationalError`.
Note also that `asset_throughput` currently shows `ga_dashas` for chart `cb73cd3d` in state
`incomplete` with the SATYA-DĪPA §N.8 message — *"0 substep(s) committed and 505348 data row(s) are
present, but this route cannot prove the plan finished"* — i.e. the earned-signal fix is visibly
working in production. Good.

**8 — Findings.** F-A9 (floor deficit, ruled), F-A10 (scope-cap sentinels both fail; docstring
under-states, MUST), F-A11 (yogini leverage, MUST), F-A12 (dignity divergence, MUST), F-A13
(hidden edges + build race, MUST), F-A17 (bare tier literals, NOW), F-A18 (`narayana` unreachable
via `get_dashas`, NOW), F-A19 (`sandhi_flag` 90% + narration, NOW), F-A20 (mudda solar-return
NULL, NOW).

---

### C12 SPECIAL ASSIGNMENT — the `ga_dashas` floor deficit, derived not picked

**(a) Expected volume from first principles.** The writer emits 8 systems × 5 ayanamshas (plus the
`vimshottari_kp` namespace split off vimshottari), 4 levels max, over `[1950-01-01, 2100-12-31]`,
delete-then-insert per `(chart, system, ayanamsha)`. A per-system closed form exists and checks
out on the live data — e.g. `vimshottari` under `lahiri`: 120-y cycle over a 151-y window ⇒ 13
mahādaśās, then ×9 per level with window clipping ⇒ 13 / 104 / 923 / 8,165 (observed exactly);
×5 ayanamshas + the KP namespace ⇒ 51,334. Crucially, **the count is chart-dependent** — the Moon's
nakshatra balance at birth shifts how many periods fall inside a fixed window. Live proof: the
same code produces **505,348** rows for `cb73cd3d`, **483,859** for `482012f1` and **471,767** for
`1c826d5a`, a ±3.5% spread. A single scalar `target_floor` is therefore the wrong instrument for
this asset regardless of which scalar you pick.

**(b) Attribution of the −52,612 to named causes.** The 536,471 figure has a surviving per-system
breakdown: `00_ARCHITECTURE/L4_PHALA_PROD_RECONCILIATION_v1_0.md` §Q1, authored 2026-06-21 from
live prod, whose seven rows sum to exactly 536,471. Comparing it to today's measurement:

| system | 2026-06-21 | 2026-08-08 (live) | Δ | named cause |
|---|---:|---:|---:|---|
| vimshottari + vimshottari_kp | 51,037 | 51,334 | **+297** | V-9 full-precision `start_iso` changed window-edge clipping (PR #521); KP split is namespace-only |
| yogini | 83,740 | 83,740 | **0** | untouched |
| ashtottari | 32,960 | 32,960 | **0** | untouched |
| naisargika | 21,945 | 21,945 | **0** | untouched |
| mudda | 102,205 | 102,365 | **+160** | M-21 varṣa-praveśa solar-return precision (PR #527) |
| chara_karaka | 138,535 | 155,135 | **+16,600** | M-7 native-fallback removal + the `dict_row`/`tuple_row` unpack fix (PRs #518, #523) — `CHARA_YEARS` is now derived per (chart, ayanamsha) from that chart's own facts, so `cycle_total` differs per ayanamsha (live: `surya_siddhanta` yields 22 L1 rows vs 21 for the other four) and more periods fall in the window |
| kalachakra | 106,049 | **35,053** | **−70,996** | **register M-6, PR #527 (2026-07-10): fabricated cycle repetition removed** |
| narayana | — | 1,327 | **+1,327** | new system, CR-104 / D-2 V-6, PR from 2026-07-16 |
| **TOTAL** | **536,471** | **483,859** | **−52,612** | sums exactly |

**(c) The ruling.** The dominant cause is not staleness and not a regression — it is a deliberate
correctness fix that **deleted fabricated rows**. Pre-M-6, `compute_kalachakra_system` "walked 12
contiguous zodiac signs forward from Moon's navamsha index, with a hardcoded flat total-years
paramayush and no savya/apasavya group selection, no deha/jeeva pada transition, no gati"
(`ga_dashas_writer.py:2753–2765`), and tiled the 1950–2100 window with repeated ~100–146 y cycles.
The current implementation delegates to `jhora.horoscope.dhasa.raasi.kalachakra` and emits **one**
paramāyuṣ-scoped 9-sign progression per depth, on the stated ground that "a life window not fully
covered by one progression is a genuine classical boundary, not a bug to paper over with fabricated
repetition" (`:2769–2772`). Live data confirms the shape: kalachakra is now exactly 9 / 81 / 729 /
~6,200 per ayanamsha, spanning birth → 2055-01-04 (krishnamurti) … 2079-05-30 (raman), while
vimshottari still spans the full 1950→2100 window.

Therefore:
- **The writer is right and the floor is wrong** — but the reason is the opposite of "the floor is
  just old": the floor **encodes ~71,000 rows the project has since ruled fabricated**. Keeping
  536,471 as a gate would be an instruction to re-fabricate them. §N.4: *"never fabricate rows to
  hit a number."*
- **Replacing 536,471 with 483,859 would be the same mistake one iteration later**, because the
  count is legitimately chart-dependent (505,348 / 483,859 / 471,767 across the three live charts).
  The correct W2 move is to populate `expected_volume_formula` + `expected_volume_inputs` with the
  per-system derivation and demote `target_floor` to a per-chart *observed* value, or drop the
  scalar gate for this asset entirely.
- Corroboration: CLAUDE.md's own v6.7 changelog entry records a 2026-07-30 live re-measurement of
  **484,387** (a 52,084 decrease) and assigns it as an open investigation item attached to
  C3-BUILDSTATE-RECON. Today's 483,859 is the same state one rebuild later (a 528-row difference,
  within the window-clipping noise this table shows between builds). **This analysis closes that
  investigation item.**
- **Where I am uncertain, stated plainly:** the two small deltas (+297 vimshottari, +160 mudda) are
  attributed by mechanism and commit date, not by re-executing the pre-change code. What would
  settle them is a single instrumented rebuild at commit `98fa03a50^` vs `HEAD` on the same chart,
  comparing per-(system, ayanamsha, level) counts. The three large ones (−70,996, +16,600, +1,327)
  are each independently corroborated by live row *shape*, not just by arithmetic.

**Registry C12 status for all three assets:** `expected_volume_inputs` is **NULL on all three**;
`expected_volume_formula` is present on all three but **wrong on two** (`ga_dashas`' own
`volume_explanation` already concedes it "under-counts by ~130×"; `ga_vargas`' is off by 8.7×) and
**unusable on the third** (`ga_positions`' `GRAHAS * AYANAMSHAS * FACT_KEYS` names no values —
though the true formula is exactly derivable and reproduces 1,205 to the row:
`5 × [ (9 grahas × 9 keys + Lagna × 5 keys) + (10 subjects × 2 keys) + (12 houses × 2 systems × 3
keys) + (9 grahas × 5 chalit keys) + (9 grahas × 2 sandhi keys) ] = 5 × 241 = 1,205` ✓).

---

## Consolidated findings

| id | asset | finding | evidence | triage | doctrine |
|---|---|---|---|---|---|
| F-A1 | ga_vargas | Every graha's D1 longitude is computed for birth time **+ tz_offset** (+5h30m here); Lagna is correct, so the FORENSIC gate passes. 266/1,215 (21.9%) varga sign rows disagree with `ga_positions`; error scales with divisor (D9 4% → D2700 96%). | `ga_vargas_writer.py:844` (`drik.sidereal_longitude(jd_ut, …)`, no `place`) vs `:828` (`drik.ascendant(jd_ut, place)`) vs `pyjhora_adapter/positions.py:53` (`drik.dhasavarga(jd_ut, place, …)`); measured per-graha offsets all = 0.229 d of motion; Lagna offset 0.000000 | **MUST** | §N.5 (L1 authority), §B.10, §N.8 |
| F-A2 | ga_vargas | `chart_divisionals_unique_idx` omits `fact_subject`, so rows differing only by subject collapse under `ON CONFLICT … DO NOTHING`. D30 lords: docstring says 60 rows, **10** survive (only `D30.S1`/`D30.S2`). `varga_house_lord`: 12 emitted, 7 survive in D1. | `ga_vargas_writer.py:1521` docstring "5-lord chain × 12 signs = 60 rows"; `:1197–1220` (`fact_key='lord'` constant, subject `D1.H<n>`); index def read live; D30 live = 10 rows / 1 category vs peers 147–163 / 10–16 | **MUST** | §N.8, §B.10 |
| F-A3 | ga_vargas | `replace_prior_chart_divisionals` deletes at `(chart, ayanamsha, varga)` while the writer inserts at 6-column grain and calls `_write_rows_batch` 5× per ayanamsha — the D30-lords pass deletes the main loop's D30 rows. `_write_rows_batch` returns `len(rows)`, so `rows_written=38,620` vs live 23,542 (39% loss) is invisible. | `_idempotency.py:81–96`; `ga_vargas_writer.py:2650` + call sites `:2956,:2977,:2987,:3032,:3081`; `:2676` `return len(rows)`; `asset_throughput.rows_written=38620` vs `count(*)=23542` | **MUST** | §N.3, §N.8 |
| F-A4 | ga_positions | `count_sql` omits `house_chalit` (225) + `sandhi_flag` (90) → cockpit reads 890 where the asset owns 1,205; under-reports 26%. | registry `count_sql`; live category counts; writer emits both at `ga_positions_writer.py:481,511` | **MUST** | §N.4 "cockpit truth" |
| F-A5 | ga_positions | `target_floor = 50` vs achieved **1,205** (24× stale; 50 is the retired `ganita_positions` figure). | registry vs `asset_throughput.rows_written=1205` (all 3 charts) | NOW | §N.4 floors-are-achieved |
| F-A6 | ga_positions | `house_chalit` (225) + `sandhi_flag` (90) have **no live consumer**: the only reader is `facts_store.ts` keying `fact_id='PLN.<X>.HOUSE_CHALIT'`, a scheme this writer never emits, reachable only via the RETIRED `forensic_render.ts`. | `facts_store.ts:154,160`; repo-wide grep finds only a description string at `platform-mcp/src/resources/vidhi/registry_data.ts:515`; CLAUDE.md §B records `forensic_render.ts` RETIRED | NOW | D-SERVICE (built-but-unplugged) |
| F-A7 | ga_vargas | `depends_on={ga_positions}` is a **false edge** (writer never reads `chart_facts`); `bg_shashtiamsha_deities` (L0) is a **hidden edge**. The false edge is why two uncrossed-checked computations of D1 exist (→ F-A1). | `ga_vargas_writer.py:814–850` (recomputes), `:584` (only external read); no `chart_facts` query anywhere in the file | NOW | §N.5, DAG integrity |
| F-A8 | ga_vargas | `get_divisionals.ts` recomputes `house_from_varga_lagna` on read and declares persistence "out of scope" — but **1,450 rows already persist it**. Tool description also under-declares coverage (says 16 vargas; table has 33) and cites a stale 21,635 total / 2,465 house-populated (live: 23,542 / 3,940). | `get_divisionals.ts:5–19, 94–118`; live `count(*) WHERE fact_key='house_from_varga_lagna'` = 1,450 across 29 vargas | NOW | D-SERVICE, §N.6 |
| F-A9 | ga_dashas | Floor deficit −52,612 **fully attributed**; dominated by kalachakra −70,996 = fabricated cycle repetition deliberately removed by register M-6. Floor 536,471 encodes ~71k fabricated rows; 483,859 is the honest count but is itself chart-dependent (505,348 / 483,859 / 471,767). | `L4_PHALA_PROD_RECONCILIATION_v1_0.md` §Q1 (2026-06-21) vs live; `ga_dashas_writer.py:2753–2772`; kalachakra live shape 9/81/729/~6,200 spanning birth→2055–2079 | **MUST** (registry correction) | C12, §N.4 |
| F-A10 | ga_dashas | **Both** scope-cap sentinels fail, not one. The KP row fails on `verification_pass_status='scope_cap_sentinel'` vs the table CHECK (`two_pass_verified\|classical_match\|divergent_flagged\|single`) — undocumented; the docstring discloses only the Prāṇa `level_n=5` failure. Function's "returns 0, 1, or 2" is always 0. Live: 0 `scope_cap` rows on all 3 charts. | `ga_dashas_writer.py:3339` + live `pg_constraint` on `chart_dashas`; docstring `:3413–3424`; live `SELECT … WHERE system_id='scope_cap'` → 0 rows | **MUST** | §N.8 earned-signal, §N.7 item 4 |
| F-A11 | ga_dashas | **83,740 yogini rows** carry a correctly-resolved `lord_natal_*` (verified: `Pingala→8.47`=Sun) that `get_dashas` overwrites with NULL, because its name→subject map only knows the 9 graha display names. | `get_dashas.ts:459–465, 519–526`; live `count(lord_natal_shadbala_total)` on yogini = 83,740/83,740 | **MUST** | LEVERAGE / D-SERVICE |
| F-A12 | ga_dashas + ga_vargas | Two L1 surfaces disagree on the same fact: `chart_divisionals` D1 `varga_dignity` Sun = **`Enemy`**; `chart_facts` `graha_dignity_per_varga.D1_SUN` = **`neutral`**. `ga_dashas` stores `enemy_sign`; `get_dashas` serves `neutral`, on **28,923** rows. (Separately, the two vocabularies differ — `neutral` vs `neutral_sign` — on 4 more grahas.) | live both tables, lahiri; `ga_dashas_writer.py:549–560` (`_DIVISIONAL_DIGNITY_NORMALIZE`); `get_dashas.ts:481–493` | **MUST** | §N.5 ("halt-worthy bug, not a stored divergence"), MSR drift handoff |
| F-A13 | ga_dashas | Two hidden edges (`ga_strength` via `graha_shadbala_total`; `ga_vargas` via D1 `varga_dignity`) + L0 `reference_nakshatras`. Because `ga_vargas` is undeclared, the scheduler runs it **concurrently** with `ga_dashas` (both started `00:20:27`; ga_vargas ended `00:21:56`; ga_dashas wrote from `00:20:28`), so `ga_dashas` reads the *previous* build's divisionals under MVCC — silently. | `ga_dashas_writer.py:525,549,563`, `:110`; `build_run_assets` timestamps for build `6479bb56…` | **MUST** | DAG integrity, §N.5 |
| F-A14 | all 3 | `integrity_check_sql` is **NULL on all three** (and on all 19 L1 assets per the wave brief). Several cheap, high-value checks are now specified by this document (F-A1 cross-table longitude equality; F-A12 dignity equality; F-A2 subject-count invariants). | live registry read | **MUST** | C12, §N.8 |
| F-A15 | all 3 | `expected_volume_inputs` NULL on all three; `expected_volume_formula` wrong on `ga_vargas` (2,700 vs 23,542) and self-admittedly wrong on `ga_dashas` (~130×); `ga_positions`' names no values though the exact formula is derivable (5 × 241 = 1,205 ✓). | live registry read + derivation reproduced against live counts | **MUST** | C12 ("a NULL there is itself the defect") |
| F-A16 | ga_positions | `estimated_seconds = 5` vs measured **98 / 145 / 165 s** on the three most recent real builds (mean 17 s over 54 runs, max 165 s). `ga_vargas` (94 vs 87–91 s) and `ga_dashas` (564 vs 482–501 s) are accurate. `asset_throughput.rows_per_second` is NULL and `history=[]` for all three. | `build_run_assets` durations; `asset_throughput` | NOW | D-SERVICE cost truth |
| F-A17 | ga_dashas | Verification tiers passed as **bare string literals** at ≥13 `_build_row` call sites despite the named constants being imported at `:41–46`. The kalachakra site passes `"two_pass_verified"` while the DB shows kalachakra 100% `single` — the literal is also misleading about what is stored. | `ga_dashas_writer.py:1172,1205,1236,1265,1370,1413,1498,1531,1562,1592,1676,2246,2265,2846`; live tier counts | NOW | §N.4 S7 bullet |
| F-A18 | ga_dashas | `narayana` (1,327 live rows) is absent from `get_dashas.KNOWN_SYSTEMS`; `system=narayana` silently returns **all** systems instead of erroring or filtering. L3's `query_active_dashas` already knows all 9. | `get_dashas.ts:42–44, 342–352`; `query_active_dashas.test.ts:46` | NOW | D-SERVICE, §N.6 (honest empty over hollow envelope) |
| F-A19 | ga_dashas | `sandhi_flag` is true on **436,738 / 483,859 (90.3%)** rows (honest `duration_days<20`, but near-uninformative at level 4), while `get_dashas.ts:184–191` narrates it as a classical caution. The informative fields `sandhi_with_next_dasha_lord` / `next_dasha_start_iso` exist on **799** rows only. | live counts; `ga_dashas_writer.py:2903–2917`; `get_dashas.ts:181–196` | NOW | §N.7 (narration fidelity) |
| F-A20 | ga_dashas | `anchored_solar_return_iso` populated on **45** rows (kalachakra L1 only, self-described "coarse marker") and **NULL on all 102,365 mudda rows** — the one system it was named for, whose `varsha_year_lord` is populated on exactly those rows and which has a real `_mudda_solar_return_jd` helper. | live counts; `ga_dashas_writer.py:2833–2836`, `:2467` | NOW | LEVERAGE / D-TIME |
| F-A21 | ga_dashas | `concurrent_system_lords_jsonb` + `convergence_count_at_start` populated on **839** rows = exactly the level-1 total. Cross-system convergence is unavailable below mahādaśā grain to any D-TIME consumer. | live counts (65+106+45+240+40+105+63+175 = 839) | NEVER-LATER (disclose, don't expand) | D-TIME |
| F-A22 | ga_dashas | `narayana` is 2 levels (105 L1 + 1,222 L2), against the writer's own "CRITICAL OVERRIDE 1: DEPTH = 4-level Sukshma". Honestly disclosed in the writer docstring; **not** disclosed at serve time. | `ga_dashas_writer.py:2185–2191`; live level pivot | NEVER-LATER (disclose) | §N.6 |
| F-A23 | ga_dashas | Build reliability: **20 errors + 11 aborts / 121 recorded runs (26% non-success)**, incl. `KeyError: 1` in `_run_concurrency_post_pass_db` and `worker_crash: OperationalError`. Chart `cb73cd3d` currently sits `incomplete` with the SATYA-DĪPA honest message (the §N.8 fix visibly working). | `build_run_assets`; `asset_throughput` | NEVER-LATER (context for W2 cost) | §N.8 |

---

## Notes on method and residual uncertainty

- Everything labelled "live" was read from production through `~/nirmana-s/bin/nq` on 2026-09-05
  against build `6479bb56-e0b1-4294-9bb2-d2fb1c987bb6`.
- **F-A1's magnitude** is measured (266/1,215 sign mismatches); its *fix effect* is inferred from
  the two call sites' differing `place` argument and was not verified by re-running the writer.
- **F-A2/F-A3 mechanisms** are each proven by an exact instance (D30 60→10; D30's 147-row peer
  profile reduced to 10). The *full* 15,078-row loss is not itself decomposed per category — doing
  that requires instrumenting `_write_rows_batch` to compare `len(rows)` against `cur.rowcount`,
  which is a write-path change and out of scope for a read-only wave. I am asserting the mechanism
  and two instances, not a per-category ledger.
- **F-A9's** two small deltas (+297, +160) are attributed by mechanism and commit date only; the
  three large ones are corroborated by live row shape. The total reconciles exactly.
- I did not measure `ga_condition` / `ga_strength` (batch B/C) even though F-A12's counterparty
  fact (`graha_dignity_per_varga`) is written there — the divergence is reported from my side and
  flagged as a cross-batch linkage for W2.
