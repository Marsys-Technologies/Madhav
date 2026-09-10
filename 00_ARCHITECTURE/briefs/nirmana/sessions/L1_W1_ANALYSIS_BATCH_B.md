---
artifact: L1_W1_ANALYSIS_BATCH_B
canonical_id: L1_W1_ANALYSIS_BATCH_B
campaign: NIRMĀṆA
session: L1
wave: W1 (ANALYZE)
batch: B
assets: [ga_nakshatra, ga_panchanga, ga_sensitive, ga_sensitive_degree]
chart_under_measurement: 482012f1-710e-4a25-994a-93821f5871aa (canonical)
produced_on: 2026-09-05
status: DRAFT
mode: READ-ONLY (no repo file mutated; no build dispatched; no DB write)
---

# L1 W1 ANALYSIS — Batch B

> **Measurement discipline.** Every number below is either (a) a live query result run this
> session against production via `~/nirmana-s/bin/nq`, or (b) a `file:line` citation. Where a
> quantity is inferred rather than measured, the sentence says so explicitly. Nothing in this
> document is a recalled or estimated figure.

---

## 0. Batch-level measured baseline

| asset | target_table | live `count_sql` | `target_floor` | writer `rows_written` | `estimated_seconds` | measured avg (s) | state (canonical chart) |
|---|---|---|---|---|---|---|---|
| `ga_nakshatra` | `chart_facts` | 2,847 | 1,802 | 2,847 | 16 | **58.8** (max 395.1, n=48) | `stale` |
| `ga_panchanga` | `chart_facts` | 437 | 221 | 437 | 3 | **10.1** (max 56.5, n=50) | `lit` |
| `ga_sensitive` | **NULL** | 8,565 | 8,610 | **8,775** | 246 | **407.3** (max 2,109.5, n=45) | `stale` |
| `ga_sensitive_degree` | `chart_facts` | 275 | **0** | **335** | 23 | 22.6 (max 55.9, n=15) | `lit` |

`rows_written` from `asset_throughput`; timings from `build_run_assets` (`ended_at - started_at`,
`state='complete'` only). `integrity_check_sql` is **NULL for all four** (consistent with the
established 0/19 L1 figure).

Two of the four assets **write more rows than their own `count_sql` counts**:

- `ga_sensitive`: 8,775 written − 8,565 counted = **210 rows** (`bhava_arudha`, 42/ayanamsha × 5).
- `ga_sensitive_degree`: 335 written − 275 counted = **60 rows** (`sensitive_point_yogi`, 12/aya × 5).

Both gaps are §N.4 "Cockpit truth" defects: the served surface serves rows the cockpit does not
know exist.

---

## 1. `ga_sensitive` — Sūkṣmabindu / Sensitive points

### 1.1 Pillar / doctrine service

Primary: **D-GROUNDING (P3)**. This is the largest pure-computation fact family in L1 (8,775 rows,
34 fact_categories, 5 ayanamshas) and every row is a longitude or a lord-assignment derived by a
cited classical formula. Secondary: **D-SALIENCE (P5)** via `saham_position` (560/aya — the Arabic
Parts are the densest domain-salience substrate in the instrument) and **D-SERVICE (P8)** via
`get_sensitive_points` / `get_karakas` / `get_kp_cusps` / `get_tajik`.

Still the right instrument? **Yes, but the grounding half is not wired.** The natural D-GROUNDING
artefact for a 5-ayanamsha asset is its cross-ayanamsha divergence surface. That surface exists
(`mv_sensitive_points_cross_ayanamsha`, created in
`platform/supabase/migrations/209_ga5_sensitive_points_mv.sql:203`), holds **0 rows**, and is
refreshed by **nothing** — a repo-wide grep for the view name returns only its own `CREATE`
statement. The asset also carries a `cross_ayanamsha_divergence_arcsec` column on every row
(`chart_facts` col 24) which no serving code reads.

### 1.2 Real vs declared dependencies

Declared: `{ga_positions, bg_reference}`.

| edge | reality |
|---|---|
| `bg_reference` | **REAL.** `ga_writers/ga_sensitive_writer.py:111` `SELECT canonical_name_en, lord FROM reference_signs`; `:114` `SELECT lord FROM reference_nakshatras`. |
| `ga_positions` | **ORDERING-ONLY, not a read edge.** The writer never `SELECT`s from `chart_facts`; it re-derives everything from `birth_params` via `pyjhora_adapter.compute.compute_chart` (`:2616`, `:3088`) and imports helper code from `ga_writers.ga_positions_writer` (`:46`). |

**Measured drift test (this session, first-principles):** `esoteric_point_bhrigu_bindu` is defined as
`midpoint(Moon, Rahu)` (`ga_sensitive_writer.py:780`). Re-deriving from `ga_positions`' own stored
longitudes on the canonical chart, lahiri:

```
MOON            = 327.055230133129
RAH_MEAN        =  49.033044100281
naive midpoint  = 188.044137116705
stored bhrigu   =   8.044137116705
delta           = -180.0000000000000200
```

The residual on the 180° short-arc correction is **2.0e-14°** (≈7e-11 arcsec). So `ga_sensitive`'s
recomputation currently agrees with `ga_positions` to floating-point noise — no live drift. But
nothing *enforces* that, which is exactly the `integrity_check_sql` gap (F-B9): the query above is
a ready-made, runnable integrity check that would have caught an MSR-class authority inversion.

### 1.3 LEVERAGE — designed consumers reading nothing

Coverage sweep of all 34 emitted categories against
`platform/src/lib/retrieval/registry/layers/L1_ganita/*.ts` and `platform-mcp/src/tools/*.ts`:

- **`bhava_arudha` (210 rows) — SERVED but UNCOUNTED.** `get_karakas.ts` serves it; no asset's
  `count_sql` counts it (verified: `SELECT asset_id FROM asset_registry WHERE count_sql LIKE
  '%bhava_arudha%'` → 0 rows).
- **`esoteric_point_yogi_system` (25 rows) — COMPUTED, REACHABLE BY NOTHING NAMED.** Repo-wide
  grep across `platform/src` + `platform-mcp/src` (excluding generated/census/test) returns zero
  hits. Not in `SP_CATEGORIES`, not in `concept_aliases.ts`, not in `coverage_matrix.ts`. Only
  reachable by a caller who already knows the literal string and types it into
  `ganita_chart_facts_get(category=...)`.
- `sun_derived_upagraha` (140 rows): **is** reachable — `platform-mcp/src/tools/register_p1_aliases.ts:402`
  maps keyword `upagraha → ['upagraha_position','sun_derived_upagraha']`. Not a gap.
- `sensitive_point_gulika_mandi` (70) / `esoteric_point_sphuta_fertility` (70) / `special_lagna`
  (245): present only in `concept_aliases.ts` (a name→category resolver, not a row-serving
  handler). Reachable via the generic reader once resolved; no dedicated leaf. **Soft gap.**
- **False advertising in the reverse direction:** `get_sensitive_points.ts:23–31` lists
  `esoteric_point_chatushphuta`, `esoteric_point_panchasphuta`, `esoteric_point_trisphuta` in
  `SP_CATEGORIES`, and its description promises "Trisphuta, Panchasphuta … Chatushphuta". All three
  have **0 rows** in production. §N.7 item 6 — the tool describes facts the instrument does not have.

`mv_chart_sensitive_points_summary` (1,515 rows) is `REFRESH MATERIALIZED VIEW CONCURRENTLY`'d on
**every** `ga_sensitive` build (`ga_sensitive_writer.py:2959`, fallback `:2965`) and is read by no
serving code — pure recurring build cost on the slowest asset in the batch.

### 1.4 Grounding

Correct answer for this asset is largely "not applicable — this is computation". Live tier
distribution (source_calculation `pyjhora_adapter.sensitive%`, canonical chart):

| tier | per ayanamsha | total |
|---|---|---|
| `two_pass_verified` | 1,750 | 8,750 |
| `floored` | 5 | 25 |

The 5 floored subjects per ayanamsha are `SRI_YANTRA_LAGNA`, `SRI_YANTRA_MOON`, `SRI_YANTRA_SUN`,
`TRIKONA_DASHA_SPHUTA`, `GULIKA_HINDU` — the B.10 fabricated-formula purge from PR #525
(`563221d60`, 2026-07-10). This is doctrine working correctly: an honest 1-row `floored` evidence
row instead of a 7-key fabricated point-set. **`single` tier: 0 rows.**

### 1.5 (D-TIME) — n/a for this asset.

### 1.6 Service — floor correctness, density, drill path

**SPECIAL ASSIGNMENT (a): the −45 row deficit, derived not picked.**

**(i) Expected volume from first principles.** The writer's output is a pure structural constant:
Σ over its 34 categories of (subjects × fact_keys), times 5 ayanamshas. Measured:
**1,755 rows/ayanamsha × 5 = 8,775**, which equals `asset_throughput.rows_written` exactly. The
same 1,713-per-ayanamsha counted figure was measured **independently on all three production
charts** (`482012f1`, `1c826d5a`, `cb73cd3d` — all five ayanamshas, 15/15 rows identical at 1,713),
and every category is identical across all five ayanamshas. There is no chart-dependent branching
in the row count and no partial-build asymmetry. **The build is complete and symmetric.**

**(ii) Attribution of the 45, to a named cause.** The 45 is *not a deficit of rows*; it is the
difference between two quantities of different vintage measured over different category sets.

- `target_floor = 8610` was set by
  `platform/migrations/307_l1_enrichment_target_floors.sql:56`, whose own comment reads *"Achieved
  count for chart 482012f1: 8,610"* — an achieved measurement on **2026-06-18**, taken with that
  migration's `count_sql`, which used `fact_category LIKE 'kp_%'`.
- The `count_sql` was later **narrowed** at ṢAḌ-DARŚANA Gate W3K (`platform/scripts/seed/asset_registry_seed.ts:1188–1201`,
  2026-08-06) because the `kp_%` wildcard had started swallowing `kp_house_significators` +
  `kp_planet_significations` — categories **`ga_nakshatra`** emits. Re-measured live this session:
  those two are 540 + 505 = **1,045 rows**, matching the seed comment's stated over-count exactly.
- Between the floor's vintage and today the writer's own emitted composition also changed by
  doctrine: PR #525 (2026-07-10, `563221d60`) replaced 5 fabricated multi-key sphuta point-sets
  with single `floored` evidence rows, while PRs #786/#1069 and others added rows back.

**Named cause: floor-vintage mismatch.** The floor was never re-measured after either
doctrine-mandated change to the counted set — the B.10 fabricated-sphuta purge (writer emits fewer,
by design) or the W3K wildcard narrowing (cockpit counts fewer, by design). §N.4 defines a floor as
*the achieved count after build*; a floor that survives a `count_sql` rewrite untouched is stale by
construction, and nothing in CI re-measures it.

**Explicitly ruled out, with evidence:**
- *"Stale floor" as a default guess* — not a default here; the specific two revisions that moved
  the counted set are named above with commit and file:line.
- *"Broken writer"* — refuted: 8,775 written = 8,565 counted + 210 uncounted `bhava_arudha`;
  identical on 3 charts; no error rows; no ayanamsha asymmetry.
- **The S7 `single`-tier relaxation (CLAUDE.md §N.4, 2026-08-06) explains 0 of the 45.** Measured:
  `ga_sensitive` has **zero rows** at `single` tier on this chart. The relaxed guard has never
  fired here.
- *`expected_volume_formula`* — refuted as a derivation source: `ACTUAL(bg_reference) * AYANAMSHAS`
  evaluates live to **1,242 × 5 = 6,210**, which matches neither the floor (8,610), the count
  (8,565), nor the writer (8,775). It is a fabricated formula (F-B3).

**(iii) Ruling.** The −45 is **not a build defect and not a data-loss event.** It is a registry
truth defect with three separable parts, all in `asset_registry`/seed, none in the writer:
re-measure the floor to the achieved count, add `bhava_arudha` to `count_sql`, and replace the
false `expected_volume_formula` with the structural derivation.

Other service facts: `target_table` is **NULL** while the asset writes `chart_facts` (the count_sql
proves it). Density (§N.6): `get_sensitive_points.ts:102` does select `verification_pass_status`, so
the floored/verified split is at least legible; no `density_contract` is declared.

### 1.7 Cost

Declared `estimated_seconds = 246`. Measured on `build_run_assets`: **45 complete runs, avg 407.3 s,
max 2,109.5 s** — 1.7× the declared estimate. Reliability is the real story: **9 `error` + 2
`aborted` runs out of 56 (19.6%)**, the worst in the batch. Last errors:
`orphaned_by_crash: prior orchestrator terminated while asset was in-flight` (2026-08-08) and
`BLOCKED: upstream dependency(ies) timeout:600s did not complete in this run` (×2, 2026-07-13/14).
One error run recorded a 22,878 s (6.4 h) wall time. `asset_throughput.rows_per_second` is NULL and
`history` is `[]` despite 56 recorded runs.

---

## 2. `ga_sensitive_degree` — Marma Aṃśa Parīkṣā / Sensitive-degree checks

### 2.1 Pillar / doctrine service

**D-GROUNDING (P3)** primarily, **D-SALIENCE (P5)** secondarily. This asset answers "is *this
graha* sitting on a classically flagged degree?" — mrityu-bhaga, gandanta, kartari, pushkara,
kranti, neecha-bhanga, khareshwara, sarvatobhadra-vedha. Right instrument: **yes**, and it is the
best-built asset in the batch — its serving surface is the only one that gets §N.6 right.

### 2.2 Real vs declared dependencies

Declared: `{ga_positions}`.

| edge | reality |
|---|---|
| `ga_positions` | **REAL** — `ga_sensitive_degree_writer.py` reads `FROM chart_facts`. |
| `bg_nakshatra` / `bg_reference` | **HIDDEN, undeclared** — reads `FROM reference_nakshatra` and `FROM reference_signs`. |
| `ga_yoga` | **HIDDEN, undeclared, and silently optional** — `:695` `from ga_writers.ga_yoga_writer import detect_neecha_bhanga` inside a bare `try/except` that sets the detector to `None` on failure. `:750` then guards row emission on `detect_neecha_bhanga is not None`. |

The `ga_yoga` edge is the sharp one. If that import ever breaks, the writer emits **7 fewer rows per
ayanamsha (35 total) with no error, no `detector_unavailable` row, and no signal** — the absence of
a neecha-bhanga row becomes indistinguishable from "no neecha-bhanga applies". The `except` branch
at `:769` that *does* emit an honest `detector_unavailable` row only fires if the detector runs and
throws; an import failure bypasses it entirely. §N.8: the silent path has no detector.

### 2.3 LEVERAGE

`get_sensitive_degrees.ts` serves **both** written categories (`SERVED_FACT_CATEGORIES` at `:31`),
with a real `total_matching`, `more_available`, and `empty_reason` — the correct §N.6 shape, and the
only capability in this batch that has it. But:

- **The asset's `count_sql` counts only `sensitive_degree_check`.** `sensitive_point_yogi` (60 rows)
  is written by the writer, served by the tool, and invisible to the cockpit
  (`SELECT asset_id FROM asset_registry WHERE count_sql LIKE '%sensitive_point_yogi%'` → 0 rows).
- **`verification_pass_status` is not in the SELECT list** (`get_sensitive_degrees.ts:~99`). The
  caller therefore receives 225 `single`, 50 `pending_w3_verification` and 60 `two_pass_verified`
  rows **flattened into one undifferentiated array** — the precise §N.6 violation ("flattening
  confirmed and catalog-only rows into one array with no distinguishing field"). `fact_category` is
  returned so the two *families* are separable; the *density* is not.
- The file's own docstring (`:6`) says "275 rows/chart" — stale; it serves 335.

### 2.4 Grounding

Exemplary. Measured tiers on the canonical chart:

| fact_key | rows/aya | tier |
|---|---|---|
| gandanta, kartari, mrityu_bhaga, pushkara | 9 each | `single` |
| neecha_bhanga | 7 | `single` |
| khareshwara_22nd_drekkana, khareshwara_64th_navamsa, sarvatobhadra_vedha | 1 each | `single` / `pending_w3_verification` |
| **kranti** | 9 | **`pending_w3_verification`** |
| **sarvatobhadra_vedha** | 1 | **`pending_w3_verification`** |
| `sensitive_point_yogi` (all 12) | 12 | `two_pass_verified` |

The two `pending_w3_verification` facets are exactly the two the writer's own docstring names as
input-incomplete (`kranti`: celestial latitude β not in L1, so β=0; `sarvatobhadra_vedha`: full
28-nakshatra SBC vedha table absent). This is §N.7 item 6 done correctly — an honest deferred
status rather than a plausible-sounding verdict. `pending_w3_verification` **is** a legal member of
`brahmagyan/verification_vocab.py` (line 158); no vocab violation.

### 2.5 (D-TIME) — n/a.

### 2.6 Service — floor correctness

**SPECIAL ASSIGNMENT (b): floor 0, `expected_volume_formula` NULL.**

Derived from the measured emission grain (canonical chart, lahiri, per ayanamsha):

```
sensitive_degree_check, per ayanamsha:
  5 per-graha facets  × 9 grahas          = 45   (gandanta, kartari, kranti, mrityu_bhaga, pushkara)
  1 per-graha facet   × 7 non-nodal       =  7   (neecha_bhanga — Rahu/Ketu excluded by rule)
  3 chart-level facets × 1                =  3   (khareshwara_22nd_drekkana,
                                                  khareshwara_64th_navamsa, sarvatobhadra_vedha)
                                            ---
                                             55  × 5 ayanamshas = 275   ✓ matches live count_sql

sensitive_point_yogi, per ayanamsha:
  YOGI            × 4 keys (point_longitude, sign, nakshatra, assigned_graha) = 4
  AVAYOGI         × 4 keys                                                    = 4
  DUPLICATE_YOGI  × 2 keys (sign, assigned_graha)                             = 2
  SAHAYOGI        × 2 keys                                                    = 2
                                                                              ---
                                              12  × 5 ayanamshas =  60   ✓ matches rows_written − 275

TOTAL WRITTEN = 335   ✓ matches asset_throughput.rows_written on all three charts
```

**Proposal (both, not either):**
1. `count_sql` → `fact_category IN ('sensitive_degree_check','sensitive_point_yogi')`, matching what
   the writer writes and the tool serves.
2. `target_floor = 335` (achieved count, §N.4 — aspirational, not a gate).
3. `expected_volume_formula = '(FACETS_PER_GRAHA*GRAHAS + NEECHA_FACET*NON_NODAL_GRAHAS +
   CHART_LEVEL_FACETS + YOGI_SUBJECT_KEYS) * AYANAMSHAS'`, with `expected_volume_inputs =
   {FACETS_PER_GRAHA:5, GRAHAS:9, NEECHA_FACET:1, NON_NODAL_GRAHAS:7, CHART_LEVEL_FACETS:3,
   YOGI_SUBJECT_KEYS:12, AYANAMSHAS:5}` → 67 × 5 = 335. This is a genuine derivation with named
   inputs, not a picked number; it is the C12-correct fix for the NULL formula.

A floor of `0` is not "unset in a harmless way": it makes the asset unfalsifiable — every possible
build outcome, including zero rows, satisfies it.

### 2.7 Cost

Declared `estimated_seconds = 23`; measured avg **22.6 s** over 15 complete runs (max 55.9 s), **0
errors, 0 aborts**. The only estimate in the batch that is accurate, and the only asset with a clean
run history.

---

## 3. `ga_sensitive` vs `ga_sensitive_degree` — SPECIAL ASSIGNMENT (c): are they the same asset twice?

**They are coherently distinct. The split is not duplication — but it is under-signposted, and one
real duplication exists across a *different* asset pair.**

| | `ga_sensitive` | `ga_sensitive_degree` |
|---|---|---|
| Question answered | "*Where* is this derived point?" | "*Is this graha on* a flagged degree?" |
| Grain | one row per (derived point × attribute) | one row per (graha × classical check) |
| Row subject | a computed longitude (Saham, midpoint, upagraha, arudha, sphuta) | a graha, judged against a rule |
| Categories | 34 | 2 |
| Rows | 8,775 | 335 |
| `target_table` | **NULL** (writes `chart_facts`) | `chart_facts` |
| Serving | `get_sensitive_points` + `get_karakas` + `get_kp_cusps` + `get_tajik` + `get_positions` | `get_sensitive_degrees` |

**Category-level overlap: zero.** The 34 categories of one and the 2 of the other are disjoint sets
(verified by the `source_calculation LIKE 'pyjhora_adapter.sensitive%'` group-by vs the
`sensitive_degree_check`/`sensitive_point_yogi` group-by).

**One genuine near-duplication, deliberately reconciled:** `ga_sensitive`'s
`esoteric_point_yogi` (14/aya, two formula variants `bphs_93_20` + `alt_96_40`) and
`ga_sensitive_degree`'s `sensitive_point_yogi` (12/aya, single authoritative formula) compute the
same BPHS Ch.20 construct. This is *documented and regression-locked* —
`ga_sensitive_writer.py:793–812` records the live-production comparison (agreement to ~4e-7°) and
names the permanent guard test. This is the correct handling of a deliberate variant-preservation
split. Not a finding.

**One genuine UNreconciled duplication, across the batch boundary:** gandanta is computed twice by
two different assets, in two different vocabularies, with nothing binding them:

```
ga_nakshatra.graha_gandanta            → 10 subjects (incl. LAGNA), fact_key='is_gandanta', value 'false'
ga_sensitive_degree.sensitive_degree_check[gandanta] → 9 subjects (no LAGNA), value 'not_gandanta'
```

They agree today (all negative on this chart), so nothing is currently wrong — but they disagree on
*scope* (LAGNA), disagree on *vocabulary*, and no `integrity_check_sql` or test compares them. This
is the shape of the documented MSR computed-value-drift trap one layer earlier.

**The real coherence problem is naming and cockpit truth, not overlap:** `ga_sensitive` has a NULL
`target_table` while writing `chart_facts`, and each asset's `count_sql` undercounts its own writer.
A reader consulting the registry cannot tell what either asset produces.

---

## 4. `ga_nakshatra` — Nakshatra / KP joins

### 4.1 Pillar / doctrine service

**D-GROUNDING (P3)** (nakshatra/pada/lord joins, 5-ayanamsha cross-check) and **D-SERVICE (P8)**.
The KP significator ladder it now carries (`kp_house_significators` 540, `kp_planet_significations`
505) is a **D-TIME (P6)** feed — `platform-mcp/src/tools/kala_views/explain.ts:200` consumes
`kp_house_significators` for the KP voice in `kala_explain`.

Still the right instrument? Yes — but it is **the most mis-served asset in L1**, see 4.3.

### 4.2 Real vs declared dependencies

Declared: `{bg_nakshatra, ga_positions, bg_kp_sublord_division}`.

| edge | reality |
|---|---|
| `ga_positions` | **REAL** — `pipeline/orchestrator/writers/ga_nakshatra.py` reads `FROM chart_facts`. |
| `bg_nakshatra` | **REAL** — `FROM reference_nakshatra`, `FROM reference_nakshatra_pada`. |
| `bg_kp_sublord_division` | **REAL and explicitly load-bearing** — `ga_nakshatra.py:31` `from brahmagyan.l0_kp_sublord_division import load_divisions`; `:415` comments that `load_divisions` raises if unbuilt and the DAG edge guarantees ordering. Correct §N.5 posture: star lords are *referenced* from L0, not restated. |
| `bg_reference` | **HIDDEN, undeclared** — the writer also reads `FROM reference_signs`, which belongs to `bg_reference`'s own `count_sql`. |

### 4.3 LEVERAGE — the highest-value finding in this batch

**The MCP tool named for this asset does not serve this asset.**

`platform-mcp/src/tools/register_p1_ganita.ts:896–921` registers `ganita_nakshatra_get`, described
as "Retrieve Nakshatra-based strength data for a chart (L1 Gaṇita)". It routes to
`marsys://tool/L1/get_tara_chandra_bala`. That capability
(`platform/src/lib/retrieval/registry/layers/L1_ganita/get_tara_chandra_bala.ts:46`) queries exactly
two categories:

```ts
const params: unknown[] = [chartId, ['tara_bala_natal_baseline', 'chandra_bala_natal_baseline'], limit, offset]
```

Measured: those two categories hold **195 rows** (135 + 60) — and **both belong to `ga_panchanga`'s
`count_sql`, not `ga_nakshatra`'s.** `ga_nakshatra`'s own `graha_tara_bala` (150 rows) is a
different category and is not queried by it.

So: a caller who asks for "the nakshatra data" gets 195 rows from a *different* asset, and
**`ga_nakshatra`'s 2,847 computed rows are not reachable through the tool bearing its name.**

Per-category reachability sweep across the whole serving surface:

| category | rows | reachable by |
|---|---|---|
| `graha_nakshatra_join` | 700 | **nothing named** — no capability, no alias, absent from `coverage_matrix.ts` |
| `kp_house_significators` | 540 | `kala_views/explain.ts` (L3 consumer) |
| `kp_planet_significations` | 505 | `resources/school_conventions.ts` only (documentation, not a query) |
| `cusp_kp_lords` | 240 | `get_kp_cusps.ts` ✓ |
| `graha_kp_lords` | 200 | `get_kp_cusps.ts` ✓ |
| `nakshatra_dispositor` | 200 | `concept_aliases.ts` only (resolver, not a handler) |
| `graha_pada_join` | 200 | **nothing named** |
| `graha_tara_bala` | 150 | `concept_aliases.ts` only |
| `graha_gandanta` | 50 | **nothing named** |
| `nakshatra_statistics` | 34 | **nothing named** |
| `nakshatra_cross_ayanamsha` | 17 | `get_positions.ts` / `coverage_matrix.ts` ✓ |
| `nakshatra_cogravity` | 10 | **nothing named** |
| `nakshatra_conjunction` | 1 | **nothing named** |

**995 rows in 6 categories have no named serving capability, no concept alias, and no
`coverage_matrix` entry.** Honest caveat: they *are* retrievable through the generic
`ganita_chart_facts_get(category='<exact string>')`
(`platform-mcp/src/tools/register_p1_aliases.ts:1541`), so this is a **discoverability** failure,
not an unreachability one — a caller must already know the internal category name to get them.

### 4.4 Grounding

`nakshatra_cross_ayanamsha` (17 rows, `ayanamsha_id='INVARIANT'`) is a genuine cross-ayanamsha
agreement check — the grounding instrument `ga_sensitive` is missing. `ga_kp_significators.py:232`
logs a real divergence message when `bg_kp_sublord_division` and `compute_kp_lords` disagree, and
`ga_nakshatra.py:21` imports `two_pass_verdict` from the settled vocab. Correct posture throughout.

Two unexplained asymmetries, flagged not adjudicated:
- `nakshatra_conjunction`: **1 row total**, only under `surya_siddhanta_classical`. Plausibly
  correct (a conjunction that only obtains under one ayanamsha's boundaries), but nothing asserts it.
- `nakshatra_statistics`: 7 rows under four ayanamshas, **6** under `surya_siddhanta_classical`.

Three of the 16 categories named in `count_sql` have **0 rows**: `graha_degree_flags`,
`nakshatra_exchange`, `nakshatra_lord_placement`.

### 4.5 (D-TIME) — indirect, via `kp_house_significators` into `kala_explain`.

### 4.6 Service

Floor 1,802 vs live 2,847 — a 58% surplus, and the `volume_explanation` still describes the
*pre-enrichment* shape ("357 rows per ayanamsha × 5 + 17 cross-ayanamsha = 1802"). The W3K
enrichment that added 1,045 KP rows never re-measured the floor. Same §N.4 stale-floor mechanism as
`ga_sensitive` (F-B1), independently instantiated. `count_sql` itself is **correct and complete**:
the 13 populated categories sum to exactly 2,847, matching `rows_written`.

Density (§N.6): `get_tara_chandra_bala.ts:62` returns `total: result.rows?.length ?? 0` — the
**page** length, not the matching total, with no `more_available` and no `empty_reason`. A caller
receiving `total: 200` at `limit: 200` cannot tell a complete answer from a truncated one.

### 4.7 Cost

Declared `estimated_seconds = 16`; measured avg **58.8 s** over 48 complete runs (max 395.1 s) — a
**3.7× underestimate**, the worst ratio in the batch. 4 error runs, all before 2026-06-25. State on
the canonical chart is `stale` (writer/upstream hash moved since the 2026-08-08 build).

---

## 5. `ga_panchanga` — Pañcāṅga

### 5.1 Pillar / doctrine service

**D-TIME (P6)** — the temporal-primitive feed — plus **D-GROUNDING (P3)**: it owns **4 of the 7
FORENSIC birth anchors**. Verified live this session:

| anchor | stored | ayanamsha | tier |
|---|---|---|---|
| Tithi | `Shukla Tritiya` | `INVARIANT` | `single` |
| Vara | `Ravivara` | `INVARIANT` | `single` |
| Yoga | `Shiva` | `INVARIANT` | `single` |
| Karana | `Garaja` | `INVARIANT` | `single` |

Independently re-derived from `ga_positions` this session: Moon 327.055230°, Sun 291.962617° →
elongation 35.0926° → tithi index `floor(35.09/12)+1 = 3` = **Shukla Tritiya ✓**; (Sun+Moon) mod 360
= 259.018° → yoga index `floor(259.018/13.333)+1 = 20` = **Shiva ✓**. The anchors are correct.

Storing the ayanamsha-independent limbs under `ayanamsha_id='INVARIANT'` is right and is a model
the rest of L1 does not follow.

### 5.2 Real vs declared dependencies

Declared: `{ga_positions, bg_panchanga}`. Both real (the writer delegates to `panchang_engine`,
`ga_panchanga_writer.py:1339`, and resolves birth params via
`pipeline.orchestrator.birth_params`). No hidden table reads found.

**One FROZEN-contract hazard, currently inert.** `ga_panchanga_writer.py:36` imports
`update_asset_throughput` from `ga_writers._telemetry`, and `:1481` calls it — §N.2 states writers
must not write `asset_throughput`. Read in full, the call is guarded:

```python
    # Update asset_throughput
    if owns_conn:
        _update_asset_throughput(chart_id, build_id, written)
```

`owns_conn` is false on the orchestrator path (the orchestrator passes `ctx.db_conn`), so the
FROZEN contract is **not** violated in production. It is a latent standalone-path violation, not a
live one. (Nine `ga_writers/*.py` files import `_telemetry`; only `ga_panchanga` was traced here.)

### 5.3 LEVERAGE — **`arambha_iso` stores the END of the anga, not its beginning**

`ga_panchanga_writer.py:354`:

```python
    arambha_iso = _ts_iso(t.end_utc)  # end of tithi
```

The value is stored under `fact_key = 'arambha_iso'` (`:382`) — *ārambha* meaning **beginning** —
while the accompanying `citation_human` correctly reads `"Tithi ends: ..."` (`:384`). The key and
the citation contradict each other on the same row. Five emission sites carry the same inversion:
`:354` tithi, `:449` yoga, `:485` karana, `:637` (the generic anga loop, which emits
`{anga}_arambha_iso` for four more), `:1008` nakshatra.

**Proved from data, not from reading the code.** Birth is 1984-02-05 10:43 IST = **05:13 UTC**.
Measured elongation at birth is 35.0982°; tithi 3 spans 24°–36°, so the birth is **92.5% of the way
through** the tithi. The beginning of that tithi therefore lies roughly a day *before* birth. The
stored value is:

```
panchanga_tithi.arambha_iso      = 1984-02-05T07:12:47+00:00   (1h 59m AFTER birth)
panchanga_karana.arambha_iso     = 1984-02-05T07:12:47+00:00   (identical — Garaja is the first half of tithi 3)
panchanga_yoga.arambha_iso       = 1984-02-05T19:29:13+00:00   (14h 16m AFTER birth)
nakshatra_arambha_iso            = 1984-02-05T17:55:22+00:00   (12h 42m AFTER birth)
```

A timestamp **after** the birth cannot be the beginning of an anga that was already 92.5% elapsed
at birth. Every one of these is the anga's **end**. Independently corroborated: yoga 20 is 42.6%
elapsed at birth and the residual 7.65° at ~13.2°/day predicts an end ≈19:07 UTC vs 19:29 stored;
Purva Bhadrapada has 6.28° remaining at birth, predicting an end ≈17–18 UTC vs 17:55 stored.

**Current blast radius:** no serving code keys on `arambha_iso` today (repo-wide grep returns only
an unrelated `vidya_arambha` event class in `muhurta_finder.ts:498`). But `chart_facts` *is* the
LLM-facing surface — the fact_key is the label the reading agent reads. Any question of the form
"how far into the tithi was the birth?" inverts. §N.7 item 1/6: a label that asserts what the value
is not.

### 5.4 Grounding

**Zero `two_pass_verified` rows in the entire asset.** Measured distribution across its 38
categories:

| tier | categories | rows |
|---|---|---|
| `single` | 12 | 260 |
| `single_pass` | 26 | 177 |

Two consequences:

1. The four FORENSIC anchors — the instrument's highest-stakes hard facts, the ones the whole
   L1 build gate is measured against — carry the *lowest* available verification tier. The FORENSIC
   7/7 PASS is asserted elsewhere; nothing at the row level records that a second derivation ran.
   §N.8: "what code path would have to run — and fail — for this signal to correctly read false?"
   For these four rows, none.
2. The asset speaks **two spellings of one tier**. `verification_vocab.py:110–114` defines
   `single_pass` as `deprecated_alias_of="single"`. Any consumer grouping by
   `verification_pass_status` splits one epistemic tier into two buckets.

### 5.5 D-TIME feed — what it answers, and what would arbitrate a disagreement

`ga_panchanga` answers the **instantaneous** temporal question: *what were the five limbs, the
auspicious/inauspicious windows, and the calendrical coordinates at this one birth moment?* It is a
point-in-time snapshot, not an interval engine. Its 33 `panchanga_*` categories divide cleanly:

- **ayanamsha-independent (stored `INVARIANT`, 1 ayanamsha):** tithi, vara, yoga, karana, all
  muhurta/kalam windows, calendrical, solar context, sandhyas — 25 categories. Correct: these
  depend on Sun/Moon geometry and civil time, not on the sidereal zero-point.
- **ayanamsha-dependent (5 ayanamshas):** `panchanga_nakshatra_moon`, `panchanga_panchaka_classification`,
  `panchanga_special_yoga_combinations`, `tara_bala_natal_baseline`, `chandra_bala_natal_baseline`,
  `eclipse_proximity_natal`, `panchaka_flag`. Also correct.
- **inconsistent:** `bhadra_flag` is stored **six times** — once under `INVARIANT` and once under
  each of the 5 ayanamshas — with identical `fact_subject` (`BHADRA_FLAG_BIRTH`), identical
  `fact_key` (`active_at_birth_flag`) and identical value (`false`). Vishti/Bhadra is a karana
  property and therefore ayanamsha-invariant; the 5 per-ayanamsha copies are redundant. This is the
  only category in the asset that straddles both conventions.

**What would arbitrate a disagreement with another temporal engine.** Three candidate arbiters exist
and none is currently binding:

1. **Against L3 Kāla / `panchang_engine`:** the writer already delegates to `panchang_engine`
   (`:1339`), so a disagreement between `chart_facts` and a live `kala_now_get` reading is a
   *staleness* question, not a doctrine question — arbitrated by rebuilding. No check enforces this.
2. **Against `ga_positions` (§N.5, L1-is-authority):** every panchanga limb is a function of the
   Sun/Moon longitudes L1 already computed. Measured this session:
   `panchanga_sun_moon_dynamics.sun_moon_separation_deg = 35.0982` vs re-derivation from
   `ga_positions` = `327.055230133129 − 291.962617284992 = 35.0926` — a **0.0056° (20 arcsec)**
   divergence. Small, but it is a *restatement* where §N.5 requires a *reference*, and it is
   precisely the class of value that drifts silently.
3. **Against FORENSIC:** the four anchors are the arbiter of last resort, and they hold. But they
   are asserted at build-gate level, not encoded as an `integrity_check_sql` on the asset.

Recommended arbiter, in priority order: **(2) then (3)** — an `integrity_check_sql` that re-derives
tithi/yoga index from `ga_positions`' own longitudes and asserts the stored name matches, plus an
assertion that every `*_arambha_iso` precedes the birth instant (which would have caught §5.3
immediately).

### 5.6 Service

Floor **221** vs live **437** — a 98% surplus. `volume_explanation` is unusually honest about it
("the legacy 'one panchanga row per ayanamsha' formula predates the enriched natal panchanga fact
family") — but `expected_volume_formula` is still literally `'AYANAMSHAS'`, i.e. **5**, against 437
live rows. Third instance in this batch of a false `expected_volume_formula` (C12).

`count_sql` is correct and complete: the 38 measured categories sum to exactly 437 =
`rows_written`.

Density (§N.6): `get_panchanga.ts:100` returns `total: result.rows?.length ?? 0` — same
page-length-as-total defect as `get_tara_chandra_bala`; no `more_available`, no `empty_reason`, no
`density_contract`. It *does* select `verification_pass_status` (`:88`), so the tier is legible —
but as noted, that tier is `single`/`single_pass` for every row, and the two spellings split it.

Drill path: good — `limb` is a first-class input with a `limbMap` (`:71–83`) grouping the 33
categories into tithi/vara/nakshatra/yoga/karana/muhurta/time_window/special.

### 5.7 Cost

Declared `estimated_seconds = 3`; measured avg **10.1 s** over 50 complete runs (max 56.5 s) — a
3.4× underestimate. 1 error run (2026-06-12). Cheapest asset in the batch; the estimate is wrong by
a factor that matters only for scheduling.

---

## 6. Cross-cutting: two claimed guards with nothing behind them (§N.8)

**(a) The R3 coverage gate cannot see most of L1.**
`platform/src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts:4–10` describes itself as
"Used by the R3 CI gate to enforce coverage completeness … Phase R2 target: every category maps to
≥1 tool", authored 2026-06-16. Measured: the file declares **169** categories; the live canonical
chart has **219** distinct `fact_category` values. Of the 21 batch-B categories checked, **19 are
absent from the list**, including all 6 of the unreachable `ga_nakshatra` categories and both
`ga_sensitive_degree` categories. A gate that enumerates a hand-maintained list cannot report a gap
for a category it does not know exists — the §N.8 defect class exactly.

**(b) A cited CI check that does not exist.**
`concept_aliases.ts:13–16` states: *"The CI regression check in
`platform/scripts/census/schema_map_alias_coverage_check.ts` asserts every LIVE fact_category has at
least one alias entry, so a category added without any alias fails loudly instead of silently
degrading `concept_locate` coverage."* That file **does not exist** (`ls` → No such file;
repo-wide grep for `alias_coverage` returns only this docstring's own mention). Consistent with the
observed reality: `esoteric_point_yogi_system` has no alias and nothing failed.

**(c) Throughput telemetry is declared but never measured.** All four assets carry
`rows_per_second = NULL`, `measurement_count = 0`, `history = []` in `asset_throughput`, while
`build_run_assets` holds **174 real timed runs** for them. The `estimated_seconds` column is a
hand-written guess that three of four assets exceed by 1.7×–3.7×, with a live measurement source
sitting unused one table away.

---

## 7. Consolidated findings

Triage key — **MUST**: fix in this campaign, a truth defect a reader can be misled by.
**NOW**: fix in this campaign, correctness/leverage improvement. **NEVER-LATER**: record and
schedule; do not fix in W2/W3.

| id | asset | finding | evidence | proposed triage | doctrine cited |
|---|---|---|---|---|---|
| **F-B1** | `ga_sensitive` | The −45 is **not** a build deficit. Floor 8,610 is an achieved measurement of 2026-06-18 taken under a `count_sql` that no longer exists; the counted set has since changed twice by doctrine (B.10 sphuta purge PR #525; W3K `kp_%` narrowing). Writer emits 8,775, identically on 3 charts. | `migrations/307_...sql:56` "Achieved count … 8,610"; `asset_registry_seed.ts:1188–1201`; `asset_throughput.rows_written = 8775` ×3 charts; 1,713/aya identical across 5 ayanamshas ×3 charts | **MUST** — re-measure floor to achieved count; no writer change | §N.4 (floors = achieved counts) |
| **F-B2** | `ga_sensitive` | `bhava_arudha` — 210 rows — is written by the writer and **served** by `get_karakas.ts`, but counted by **no** asset's `count_sql`. | `source_calculation LIKE 'pyjhora_adapter.sensitive%'` → `bhava_arudha 42/aya`; `SELECT asset_id FROM asset_registry WHERE count_sql LIKE '%bhava_arudha%'` → 0 rows | **MUST** | §N.4 Cockpit truth |
| **F-B3** | `ga_sensitive` | `expected_volume_formula = 'ACTUAL(bg_reference) * AYANAMSHAS'` is false. Live `bg_reference` = **1,242** → formula yields 6,210, matching neither floor (8,610), count (8,565) nor writer (8,775). | bg_reference `count_sql` run live = 1242 | **MUST** — replace with the structural point×key×ayanamsha derivation | C12 (derive, never pick) |
| **F-B4** | `ga_sensitive` | `target_table` is NULL while the asset demonstrably writes `chart_facts`. Registry cannot answer "where does this asset land?" | `asset_registry.target_table` NULL; `count_sql` selects `FROM chart_facts` | **NOW** | §N.4 Cockpit truth |
| **F-B5** | `ga_sensitive` | `mv_sensitive_points_cross_ayanamsha` — the cross-ayanamsha divergence surface, i.e. the asset's natural D-GROUNDING instrument — holds **0 rows** and is refreshed by nothing in the repo. | `pg_matviews` count = 0; repo-wide grep returns only `supabase/migrations/209_...sql:203` (its `CREATE`) | **NOW** | D-GROUNDING (P3); §N.8 |
| **F-B6** | `ga_sensitive` | `mv_chart_sensitive_points_summary` (1,515 rows) is `REFRESH`ed on every build of the batch's slowest asset and read by **no** serving code. | `ga_sensitive_writer.py:2959`, `:2965`; grep of `platform/src`+`platform-mcp/src` → 0 hits | **NEVER-LATER** (drop the refresh, or wire F-B5 on top of it) | — |
| **F-B7** | `ga_sensitive` | `get_sensitive_points` advertises `esoteric_point_trisphuta`, `_panchasphuta`, `_chatushphuta` in both `SP_CATEGORIES` and its description; all three have **0 rows**. | `get_sensitive_points.ts:23–31` + description; live category census | **NOW** | §N.7 item 6 (honest null over invented) |
| **F-B8** | `ga_sensitive` | `esoteric_point_yogi_system` (25 rows) has **no** capability, **no** concept alias, **no** `coverage_matrix` entry. Reachable only by typing the literal category into the generic reader. | repo-wide grep of `platform/src`+`platform-mcp/src` → 0 non-generated hits | **NOW** | §N.6 (density/serving); D-SERVICE (P8) |
| **F-B9** | `ga_sensitive` | No `integrity_check_sql`, and a real one is trivially derivable and passes today: `bhrigu_bindu == shorter-arc midpoint(Moon, Rahu)` from `ga_positions` agrees to **2.0e-14°**. | live query, §1.2 above | **MUST** | §N.5, §N.8 (a signal needs a detector) |
| **F-B10** | `ga_sensitive` | **19.6% run failure rate** (9 error + 2 aborted of 56) and `estimated_seconds=246` vs measured avg **407 s** (max 2,110 s complete; one 22,878 s error run). | `build_run_assets` group-by | **NOW** | §N.8 |
| **F-B11** | `ga_sensitive` | `depends_on: ga_positions` is an **ordering** edge, not a read edge — the writer re-derives positions from `birth_params` via `compute_chart` rather than reading L1's stored longitudes. No drift measured today (F-B9). | `ga_sensitive_writer.py:2616`, `:3088`; no `SELECT … FROM chart_facts` | **NEVER-LATER** — document the edge semantics | §N.5 |
| **F-B12** | `ga_sensitive_degree` | `count_sql` counts only `sensitive_degree_check`; `sensitive_point_yogi` (**60 rows**) is written by the writer **and served** by `get_sensitive_degrees` yet invisible to the cockpit. | `asset_registry.count_sql`; `get_sensitive_degrees.ts:31`; `rows_written`=335 vs count=275 | **MUST** | §N.4 Cockpit truth |
| **F-B13** | `ga_sensitive_degree` | `target_floor = 0` (unfalsifiable — a zero-row build passes) and `expected_volume_formula` NULL. Derived: **(5×9 + 1×7 + 3 + 12) × 5 = 335**. | per-facet grain measured live (§2.6) | **MUST** — floor 335 + the named-input formula | §N.4; C12 |
| **F-B14** | `ga_sensitive_degree` | `get_sensitive_degrees` does **not** select `verification_pass_status`, so 225 `single` + 50 `pending_w3_verification` + 60 `two_pass_verified` rows are served as one flat array. | `get_sensitive_degrees.ts` SELECT list; live tier group-by | **MUST** | §N.6 item 1 |
| **F-B15** | `ga_sensitive_degree` | Undeclared deps: `reference_nakshatra`/`reference_signs` (bg_*), and `ga_yoga` via a **best-effort** import. If that import fails, 7 rows/aya vanish with **no error and no `detector_unavailable` row** — the `except` that emits an honest row only covers a *runtime* throw, not an import failure. | `ga_sensitive_degree_writer.py:695–698`, `:750`, `:769` | **NOW** — emit the honest row on the import-failure path too | §N.8 |
| **F-B16** | `ga_sensitive_degree` ∩ `ga_nakshatra` | Gandanta computed **twice** by two assets, two vocabularies (`'false'` vs `'not_gandanta'`), different scope (LAGNA covered by one only), with no cross-check. Agrees today. | live rows, §3 | **NOW** — one cross-asset `integrity_check_sql` | §N.5 (MSR drift trap) |
| **F-B17** | `ga_sensitive_degree` | File docstring says "275 rows/chart"; it serves 335. | `get_sensitive_degrees.ts:6` | **NEVER-LATER** | §N.7 |
| **F-B18** | `ga_nakshatra` | **`ganita_nakshatra_get` does not serve `ga_nakshatra`.** It routes to `get_tara_chandra_bala`, which queries 2 categories (195 rows) that belong to **`ga_panchanga`**'s `count_sql`. The asset's own 2,847 rows are unreachable through the tool named for it. | `register_p1_ganita.ts:896–921`; `get_tara_chandra_bala.ts:46`; `ga_panchanga.count_sql` includes both categories | **MUST** — highest-leverage item in the batch | D-SERVICE (P8); §N.6 |
| **F-B19** | `ga_nakshatra` | **995 rows / 6 categories** (`graha_nakshatra_join` 700, `graha_pada_join` 200, `graha_gandanta` 50, `nakshatra_statistics` 34, `nakshatra_cogravity` 10, `nakshatra_conjunction` 1) have no named capability, no alias, no coverage-matrix entry. Retrievable only via `ganita_chart_facts_get(category='<exact string>')`. | per-category grep sweep, §4.3 | **MUST** | D-SERVICE (P8) |
| **F-B20** | `ga_nakshatra` | 3 of the 16 categories named in `count_sql` have **0 rows**: `graha_degree_flags`, `nakshatra_exchange`, `nakshatra_lord_placement`. | live category group-by | **NOW** — build them or drop them from `count_sql` | §N.4 |
| **F-B21** | `ga_nakshatra` | Unexplained ayanamsha asymmetries: `nakshatra_conjunction` = 1 row, `surya_siddhanta_classical` only; `nakshatra_statistics` = 6 there vs 7 elsewhere. Possibly correct; nothing asserts it. | live group-by | **NOW** — assert or document | §N.8 |
| **F-B22** | `ga_nakshatra` | `estimated_seconds = 16` vs measured avg **58.8 s** (max 395.1 s) — 3.7×, worst in batch. State `stale` on the canonical chart. | `build_run_assets`; `asset_throughput.state` | **NOW** | — |
| **F-B23** | `ga_nakshatra` | Undeclared read of `reference_signs` (belongs to `bg_reference`). | `pipeline/orchestrator/writers/ga_nakshatra.py` `FROM reference_signs` | **NEVER-LATER** | §N.2 DAG hygiene |
| **F-B24** | `ga_panchanga` | **`*_arambha_iso` stores the anga's END, not its beginning.** `arambha_iso = _ts_iso(t.end_utc)`; the `citation_human` on the same row says "Tithi ends". Proved from data: birth 05:13 UTC, elongation 35.0982° = 92.5% through tithi 3, stored "arambha" = 07:12 UTC (**after** birth). 5 emission sites. | `ga_panchanga_writer.py:354, 449, 485, 637, 1008`; live values §5.3 | **MUST** — highest-severity correctness item | §N.7 items 1 & 6 |
| **F-B25** | `ga_panchanga` | `bhadra_flag` stored **6×** — once `INVARIANT` plus once per ayanamsha — identical subject/key/value. Only category in the asset straddling both conventions. | live rows §5.5 | **NOW** | §N.3 idempotency scoping |
| **F-B26** | `ga_panchanga` | **Zero `two_pass_verified` rows.** The 4 FORENSIC anchors it owns (Tithi/Vara/Yoga/Karana) all carry `single` — the lowest tier available — so no row-level detector could ever report them false. | live tier group-by | **MUST** | §N.8 Earned-Signal |
| **F-B27** | `ga_panchanga` | Two spellings of one tier inside one asset: `single` (260 rows, 12 categories) and its **deprecated alias** `single_pass` (177 rows, 26 categories). Any status-grouped consumer splits one tier into two buckets. | live group-by; `verification_vocab.py:110–114` (`deprecated_alias_of="single"`) | **NOW** | §N.4 (vocab via named constants); §N.6 item 4 |
| **F-B28** | `ga_panchanga` + `ga_nakshatra` | `get_panchanga` and `get_tara_chandra_bala` both return `total: result.rows?.length` — the **page** size, not the matching total — with no `more_available`, no `empty_reason`, no `density_contract`. A truncated answer is indistinguishable from a complete one. | `get_panchanga.ts:100`; `get_tara_chandra_bala.ts:62` | **MUST** | §N.6 items 3 & 4 |
| **F-B29** | `ga_panchanga` | `sun_moon_separation_deg = 35.0982` vs re-derivation from `ga_positions` = **35.0926** (Δ 0.0056° ≈ 20″). A restatement where §N.5 requires a reference. | live query §5.5 | **NOW** | §N.5 (L1 is authority) |
| **F-B30** | `ga_panchanga` | Writer imports and calls `update_asset_throughput`; §N.2 forbids writers writing build state. **Inert in production** — gated by `if owns_conn:`, false on the orchestrator path. Latent standalone-path violation only. | `ga_panchanga_writer.py:36`, `:1313`, `:1481` | **NEVER-LATER** | §N.2 FROZEN contract |
| **F-B31** | `ga_panchanga` | Floor **221** vs live **437**; `expected_volume_formula = 'AYANAMSHAS'` (= 5) against 437 rows. Third false volume formula in the batch. | `asset_registry`; live count | **MUST** | §N.4; C12 |
| **F-B32** | cross-cutting | `coverage_matrix.ts` — cited as the input to "the R3 CI gate [that] enforce[s] coverage completeness" — declares **169** categories against **219** live. 19 of the 21 batch-B categories checked are absent, including all 6 F-B19 categories. The gate cannot report a gap for a category it does not list. | `coverage_matrix.ts:4–10`; `count(DISTINCT fact_category)` = 219 | **MUST** | §N.8 Earned-Signal |
| **F-B33** | cross-cutting | `concept_aliases.ts` cites a CI regression check at `platform/scripts/census/schema_map_alias_coverage_check.ts` asserting every live category has an alias. **That file does not exist** anywhere in the repo. | `concept_aliases.ts:13–16`; `ls` → No such file; grep `alias_coverage` → 1 hit, its own docstring | **MUST** | §N.8; §N.7 item 4 |
| **F-B34** | cross-cutting | All four assets have `rows_per_second = NULL`, `measurement_count = 0`, `history = []` in `asset_throughput`, while `build_run_assets` holds **174** real timed runs for them. `estimated_seconds` is a hand-written guess exceeded by 1.7×–3.7× on three of four. | `asset_throughput`; `build_run_assets` | **NOW** | §N.8 |
| **F-B35** | all four | **0 `integrity_check_sql`.** Three concrete, derivable checks are named in this document and one is proven to pass today: bhrigu-bindu ↔ `ga_positions` (F-B9), gandanta cross-asset agreement (F-B16), tithi/yoga index re-derived from `ga_positions` + "`arambha_iso` < birth instant" (which would have caught F-B24 on day one). | §1.2, §3, §5.5 | **MUST** | §N.8; C12 |

---

## 8. Uncertainty register (read before W2 routes anything)

Stated explicitly so W2 does not treat inference as measurement.

1. **F-B1, residual 9 rows/ayanamsha.** The 45 is fully accounted for as a floor-vintage mismatch,
   and both changes that moved the counted set are named with commits. What is **not** measured is
   the exact per-category arithmetic of the 2026-06-18 → today delta: the writer changed 10 times in
   that window (adds *and* removes), and reconstructing the historical per-category composition
   would require checking out and running the old writer. **Confidence that the −45 is not a build
   defect: high** (three independent charts, symmetric ayanamshas, `rows_written` > floor).
   **Confidence in a single-cause attribution of exactly 9 rows/aya: low — do not claim one.**
2. **F-B21** (`nakshatra_conjunction` = 1 row, `surya_siddhanta` only; `nakshatra_statistics` 6 vs 7)
   may be entirely legitimate — a real conjunction under one ayanamsha's nakshatra boundaries and
   not others. This is flagged as *unasserted*, not as *wrong*. W2 should route it to a check, not a fix.
3. **F-B29** (20″ separation delta) is small enough to be an epoch/precision artefact between
   `panchang_engine` and the position writer rather than a defect. Flagged as a §N.5 *restatement*
   issue regardless of which value is right.
4. **F-B30**: only `ga_panchanga`'s `_telemetry` path was traced in full. Eight other
   `ga_writers/*.py` files import `_telemetry`; their guard conditions were **not** verified here.
5. **F-B19 reachability**: the 995 rows are unreachable by any *named* capability, alias, or
   coverage-matrix entry, but **are** retrievable via `ganita_chart_facts_get(category=…)`. The
   finding is discoverability, not absence.
6. `cb73cd3d`'s `ga_nakshatra.rows_written` is 1,813 vs 2,847/2,858 on the other two charts —
   suggesting that chart predates the KP enrichment. Not investigated; out of batch scope, noted so
   W2 does not read it as a `ga_nakshatra` defect.

---

*End of L1_W1_ANALYSIS_BATCH_B (DRAFT, 2026-09-05). Read-only pass: no repo file other than this
one was written, no build dispatched, no DB write issued.*
