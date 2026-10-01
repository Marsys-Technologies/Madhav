---
artifact: INVESTIGATION_L1_DUPLICATE_KEYS
version: 1.0
status: DRAFT_FOR_REVIEW
date: 2026-10-02
lane: suvarna/land/TI-l1-dupkeys-001
origin: BOUNDARY_FLIP_REPORT_v1_0.md section 7.3 (origin/suvarna/land/TI-ephemeris-flip-report-001)
mode: READ-ONLY (no code change, no DB write, no build). DB reads as suvarna_reader only.
changelog:
  - "1.0 (2026-10-02): first issue. Answers (a) legitimate variants vs true duplicates, (b) which row every reader picks and whether that is deterministic, (c) the smallest fix."
---

# L1 `chart_facts` duplicated natural keys: variants, readers, smallest fix

## 0. Answer in ten lines

1. **All 460 duplicated keys per chart are legitimate named variants. Zero are true duplicates.** Every duplicate key is written once per `formula_id` by one writer (`ga_sensitive`) in one `build_id`. Grouped by `(chart, ayanamsha, category, subject, key, COALESCE(formula_id,''))` the three charts hold **0** groups with more than one row.
2. The 159 / 127 / 160 "contradictory" keys (native / chart 2 / chart 3, reproduced exactly) are contradictions **between named formulas**, not between writers, builds or ephemerides.
3. Cause: `ga_sensitive_writer` deliberately emits every classical variant (WP-1.8) as separate rows. It is not two writers, not build generations, not a narrow delete scope, and not the 41,042 unowned rows (those are bookkeeping; they do not cause it).
4. **`formula_id` is already a column and already part of the unique key** (`chart_facts_unique_with_formula` / `chart_facts_unique_null_formula`, migration 215 lineage), and `fact_id` hashes it. The L1 capture trigger identifies rows by `fact_id`, so it is formula-aware. **No migration and no unique-index change is needed.**
5. The defect is on the **read side**: of the readers that can reach these categories, **2 are nondeterministic** (`chart_facts_query` default pivot, `address_resolver.fetchKarakaRow`), **2 serve both variants with a non-total ORDER BY** (`get_karakas` also hides `formula_id`; `get_sensitive_points` discloses it), **1 is dead code** (`bo_upaya._fetch_chara_roles` returns `{}` on production), **2 are pinned or total** (`ga_structural` karaka-web reader, `chart_reader_v4.special_points`), **1 emits both variants as separate signals** (`bo_laksana`, 541 native signals cite these facts), and **2 materialized views silently collapse variants** (no code consumer found).
6. The code comment in `address_resolver.fetchKarakaRow` ("both canonical charts verified to agree") is **false on production today** (section 3.3).
7. **The fix is small, and it is reader-side only.** Mandatory minimum: one canonical-formula table (a constant mirrored TS and Python) plus four reader edits (section 5). Row-count effect: **0**. No D6 owner-path step is required.
8. **Three formula choices need an acharya or SS ruling** (Yogi/Avayogi, Mrityu, karaka school). Repo evidence supports defaults for two of them; Mrityu has none.
9. F-A2 (PR #2858) widens `chart_divisionals`, a different table with a different key; it neither blocks nor is blocked by this. The argala rows in `chart_facts` carry no `formula_id` and hold no duplicate keys.
10. A rebuild does not need to wait for this: the rebuild reproduces the same variants (the flip report already found the Moshier run emits them in the same order), and pinning readers needs no rebuild.

## 1. Method and scope

- Charts: `482012f1-710e-4a25-994a-93821f5871aa` (native, 143,299 rows), `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (139,717), `cb73cd3d-9eba-4220-9902-0de91566e980` (138,080).
- Natural key tested: `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)`, build_id excluded, so a cross-generation duplicate would also appear.
- All queries filter by `chart_id`, run as `suvarna_reader` through a scratchpad wrapper, and read only.
- `chart_facts` has `computed_at`, not `created_at`; examples use `computed_at`.
- Table owner: `data_plane_l1_owner`. Triggers: `l1_data_plane_capture` (identity argument `'fact_id'`), `l1_data_plane_mutation_guard`. `chart_fact_identity` is owned by `amjis_app`, keyed by `fact_id`, and holds **0 rows** for the seven affected categories (their subjects are dimensionless special-point tokens), so it is neither a reader nor affected.

## 2. (a) Variants versus true duplicates

### 2.1 Totals (per chart)

| Chart | Duplicated keys | Rows in them | Contradictory keys | Keys spanning more than 1 build_id | Keys with more than 1 distinct `formula_id` | True duplicates (same key AND same formula) |
|---|---|---|---|---|---|---|
| native 482012f1 | 460 | 955 | 159 | 0 | 460 | **0** |
| chart 2 1c826d5a | 460 | 955 | 127 | 0 | 460 | **0** |
| chart 3 cb73cd3d | 460 | 955 | 160 | 0 | 460 | **0** |

The seven categories hold 990 rows per chart in a single `build_id`, a single `source_calculation` (`pyjhora_adapter.sensitive/pyjhora/1.0.0`) and a single `engine_version`. The 35 rows outside duplicated keys are the 8th karaka (`STRIKARAKA`), which exists only under `kn_rao_rahu_included`.

### 2.2 Per (writer asset, fact_category): keys, rows, contradictory keys

Writer asset for every row: **`ga_sensitive`** (registry `natural_key_partition` lists all seven categories; `source_calculation` matches). Contradictory = more than one distinct value among the variant rows.

| fact_category | Variant `formula_id`s | Keys / chart | Rows / chart | Contradictory: native | chart 2 | chart 3 |
|---|---|---|---|---|---|---|
| karaka_chara_position | `parashari_rahu_excluded` (7 karakas), `kn_rao_rahu_included` (8) | 245 | 490 | 80 | 60 | 95 |
| esoteric_point_mrityu | `bphs_ch39`, `saravali`, `tajik_aapamrityu` | 35 | 105 | 35 | 35 | 35 |
| esoteric_point_yogi | `bphs_93_20`, `alt_96_40` | 35 | 70 | 15 | 12 | 12 |
| esoteric_point_avayogi | `bphs_93_20`, `alt_96_40` | 35 | 70 | 29 | 20 | 18 |
| esoteric_point_brahma | `parashari_rahu_excluded`, `kn_rao_rahu_included` | 40 | 80 | 0 | 0 | 0 |
| esoteric_point_shiva | same two | 35 | 70 | 0 | 0 | 0 |
| esoteric_point_vishnu | same two | 35 | 70 | 0 | 0 | 0 |
| **Total** | | **460** | **955** | **159** | **127** | **160** |

About two thirds of the duplicate keys (301 / 333 / 300 of 460) carry **identical** values across variants (Brahma/Shiva/Vishnu entirely, plus the sub-keys where the schools or formulas agree). They are duplicates only in the row-count sense.

### 2.3 Per key (contradictory keys per chart; 5 ayanamshas each; native / chart 2 / chart 3)

| Category | Key | Native | Chart 2 | Chart 3 |
|---|---|---|---|---|
| esoteric_point_yogi | longitude_sidereal, pada | 5 / 5 | 5 / 5 | 5 / 5 |
| esoteric_point_yogi | sign, sign_lord, house_d1 | 1 each | 0 | 0 |
| esoteric_point_yogi | nakshatra, nakshatra_lord | 1 | 1 | 1 |
| esoteric_point_avayogi | longitude_sidereal, pada | 5 | 5 | 5 |
| esoteric_point_avayogi | nakshatra, nakshatra_lord | 5 | 5 | 4 |
| esoteric_point_avayogi | sign, sign_lord, house_d1 | 3 each | 0 | 0 |
| esoteric_point_mrityu | all 7 keys | 5 each | 5 each | 5 each |
| karaka_chara_position | assigned_graha, degree_in_sign, house_d1, longitude_sidereal, sign | 9 each | 5 each | 12 each |
| karaka_chara_position | karaka_school | 35 | 35 | 35 |
| karaka_chara_position | karaka_rank | 0 | 0 | 0 |

`karaka_school` is trivially "contradictory" because its value text is the formula id itself (a redundant second encoding of the discriminator).

### 2.4 Example rows (native, `lahiri_chitrapaksha`; all in build `3ea96f6a-e0d9-49fe-a316-6a219aae0186`)

| fact_id | category / subject / key | value | formula_id | computed_at |
|---|---|---|---|---|
| 1ab369a4dca61235 | esoteric_point_yogi / YOGI_POINT / longitude_sidereal | 352.351180718121 | bphs_93_20 | 2026-09-07 11:18:34.612884 |
| 8ed0713d195cc400 | same | 355.68451411812 | alt_96_40 | 2026-09-07 11:18:34.612952 |
| a1b7bf97746ef03f / 3142d7aba6a9b2e3 | esoteric_point_avayogi / AVAYOGI_POINT / sign | Virgo / Libra | bphs_93_20 / alt_96_40 | 11:18:34.613026 / .613092 |
| 8fca8f53f8e3adbd | esoteric_point_mrityu / MRITYU_SPHUTA / longitude_sidereal | 96.4418410650319 | bphs_ch39 | 11:18:34.61315 |
| 978b2ee3709d60d6 | same | 8.00640374694672 | saravali | 11:18:34.613221 |
| ab797429df2f3476 | same | 247.80790552491 | tajik_aapamrityu | 11:18:34.613285 |
| 0aa0001f8b1188e3 | karaka_chara_position / DARAKARAKA / assigned_graha | Mercury | parashari_rahu_excluded | 11:18:34.620025 |
| 130f96d334c42797 | same | Jupiter | kn_rao_rahu_included | 11:18:34.620479 |
| 55267e8a460fd92d | karaka_chara_position / GNATIKARAKA / assigned_graha | Jupiter | parashari_rahu_excluded | 11:18:34.619961 |
| 6c2253d9e5b43720 | same | Rahu | kn_rao_rahu_included | 11:18:34.620416 |

The Yogi pair differs by exactly 3.3333 degrees (93 deg 20 min versus 96 deg 40 min). Same pattern on the other charts: chart 2 Yogi 124.4507 (`bphs_93_20`) / 127.7840 (`alt_96_40`), DARAKARAKA Saturn / Saturn; chart 3 Yogi 182.4986 / 185.8320, DARAKARAKA Mars (parashari) / Sun (kn_rao). The `sensitive_point_yogi` category written by `ga_sensitive_degree` (formula-less, YOGI/AVAYOGI subjects) holds 352.351181, equal to `bphs_93_20` (MC-029 already records this).

### 2.5 How the duplicates arise

- **One writer, deliberate multi-emit.** `ga_sensitive_writer.py` (module header: "Variant-family (Yogi/Mrityu/Panchasphuta): both/all emitted as separate formula_id rows"; lines ~800-890 Yogi/Avayogi/Mrityu; ~1076-1135 Brahma/Vishnu/Shiva per school; ~1214-1304 karaka both schools). `_fact_id()` hashes `category|subject|key|chart|ayanamsha|formula_id`, so each variant gets its own stable `fact_id`; the `INSERT ... ON CONFLICT (fact_id)` lets both land.
- **Not generations.** The chart carries up to 10 `build_id`s, but each is a different asset's run; no key spans two builds (`multi_build = 0` across all 460 keys on all three charts). The delete helper (`_idempotency.replace_prior_chart_facts`) is scoped to `(chart, category, ayanamsha)`, formula-agnostic, so a rebuild replaces all variants together.
- **Not two writers.** `ga_sensitive_degree` writes a different category (`sensitive_point_yogi`) with different subjects/keys; it is a sibling, not a duplicate of the same key.
- **Not the unowned rows.** None of the seven categories has a `fact_category_ownership` row (0 of 67 rows name them), so they sit inside the 41,042 unowned rows. That matters only because nothing in the ownership/registry layer declares them multi-formula, so no gate asks readers to pin.
- **Two conventions for "named variant" coexist in one table.** `ga_sensitive` puts the variant in the `formula_id` column. `ga_structural` puts it in `fact_key` (`bphs_weighted`, `simple_multiplication`, `raman_variant`; none of those strings appear in `formula_id` on the native chart). Only 12 distinct `formula_id` values exist on the native chart, on 1,295 of 143,299 rows.

## 3. (b) Which row each reader picks

Reader set: every `chart_facts` reader reaching the seven categories, found by category name, by `fact_key` (`assigned_graha`, `karaka_school`), by generic category-agnostic fetches, and in the live DB's views, materialized views and functions. TS: `platform/src`, `platform-mcp/src`. Python: `platform/python-sidecar`. L3 `ka_*`, L4 `ph_*`, L5 `mi_*` writers and services: **no reader of these categories found.**

### 3.1 Selection logic per reader

| # | Reader | Selection logic | Pinned by fact_key + formula? | Total ORDER BY? | Verdict |
|---|---|---|---|---|---|
| R1 | `chart_facts_query` (register_d7_channel.ts ~1015-1200; serves `ganita_chart_facts_get` / `query_chart_facts`) | Default `shape=pivoted`: `entry.facts[key] = value` per `fact_subject`, **last row wins**. SQL `ORDER BY fact_subject, fact_category, fact_key LIMIT n` | key yes, formula no; `formula_id` not even selected | **No** (ties on the formula dimension) | **NONDETERMINISTIC.** Which variant "wins" is physical-order dependent. `shape=rows` returns both rows with no discriminator. |
| R2 | `address_resolver.fetchKarakaRow` (address_resolver.ts ~578-606) | `SELECT ... fact_key IN (assigned_graha, house_d1, sign)`, loop keeps the **first** non-null | key yes, formula no | **No ORDER BY at all** | **NONDETERMINISTIC**, and the result is labelled with a `school` (default `parashari_rahu_excluded`) that the query never applied, so the label can disagree with the value. |
| R3 | `get_karakas` (get_karakas.ts) | Flat page of all rows for the category | no; `formula_id` not projected | `category, ayanamsha, key` (no subject, formula, fact_id) | Serves both variants, **indistinguishable**; page order not total. |
| R4 | `get_sensitive_points` (get_sensitive_points.ts) | Flat page plus a `multi_formula` disclosure grouping variants by `formula_id` | disclosed, never collapsed | `category, ayanamsha, key, formula_id` (no subject, fact_id) | Deterministic as a set; **page boundaries not total** (8 karaka subjects tie). Best-practice surface. |
| R5 | `ga_structural_writer` karaka-web (ga_structural_writer.py ~5683-5700) | `fact_key='assigned_graha' AND formula_id='kn_rao_rahu_included'` | **yes, both** | one row per (subject, aya) after the pin | **DETERMINISTIC.** Establishes the repo's only canonical karaka school. |
| R6 | `chart_reader_v4.special_points` (chart_reader_v4.py ~384) | all rows for the category | no, by design (docstring says it surfaces both) | `fact_subject, fact_key, computed_at, fact_id` | Deterministic and total; no production caller found. |
| R7 | `bo_laksana` (`_FETCH_SQL`, ~1876) | Whole chart, every fact row becomes its own MSR signal; `formula_id` is fetched but never used | n/a | `fact_category, fact_key` (non-total, but per-row emission) | Both variants flow into Bodha as separate signals: **541 of 50,678 native signals** cite facts of these categories. Whether the derived signal identity (`bodha_signal_identity`) separates value-identical variants is unverified. |
| R8 | `bo_upaya._fetch_chara_roles` (~393) | reads all rows of the category; `graha = fact_key.split(':')[0]` | no | none | **Dead code.** `fact_key` is `assigned_graha`/`sign`/..., never a graha, so the map is always `{}`. Verified: `bodha_rm_resonances.is_chara_karaka_role` is NULL on all 45 native rows. If repaired as written it would be last-wins across schools. |
| R9 | `mv_chart_sensitive_points_summary` (SQL) | `GROUP BY chart, aya, category, subject, build_id` with `max(CASE fact_key ...)` | no | n/a | Deterministic but **collapses variants into a hybrid** (e.g. `max` longitude from one formula, `max` sign text from another). Only code touch is the refresh. |
| R10 | `mv_cross_ayanamsha_consensus` (SQL) | groups by chart, build, category, subject, key | no | n/a | `all_ayanamshas_agree` conflates formula variance with ayanamsha variance for these keys. Only code touch is the refresh. |
| R11 | `facts_store.query_chart_facts` (platform/src/lib/ganita) | `ORDER BY cf.category, cf.fact_id` | n/a | yes | References columns absent from live `chart_facts` (`category`, `is_stale`, `value_text`); cannot run against it. Legacy. |
| R12 | `fact_identity_parser` / `chart_fact_identity` | not a reader of these facts | n/a | n/a | No rows for these categories; unaffected. |

Not affected (checked): `get_sensitive_degrees` (reads `sensitive_point_yogi`, formula-less and single-valued), `concept_locate` / `resolve_concept` (list categories only), `reading_checklist.ts` (YOGI subjects of `sensitive_point_yogi`), L3/L4/L5.

### 3.2 What the shared SQL does today (emulation, not a live app call)

Running R1's ORDER BY against production returns ties in physical order: Yogi `bphs_93_20` then `alt_96_40`; Mrityu `bphs_ch39`, `saravali`, `tajik_aapamrityu`; karaka `parashari_rahu_excluded` then `kn_rao_rahu_included`. So R1's last-wins pivot currently serves `alt_96_40` (355.68), `tajik_aapamrityu` (247.81) and `kn_rao_rahu_included`, while R2's first-wins serves `parashari_rahu_excluded`. Two serving paths therefore disagree today for DARAKARAKA (Jupiter versus Mercury) and GNATIKARAKA (Rahu versus Jupiter) on the native chart. This tie order is not guaranteed; a different plan or a vacuum can change it.

### 3.3 The "schools agree" comment is false in production

`address_resolver.ts` justifies reading unpinned rows because "both canonical charts were verified to have the parashari/kn_rao schools agree on assigned_graha/house/sign". Measured on `assigned_graha` (7 subjects shared by both schools, per ayanamsha):

| Chart | Subjects disagreeing, per ayanamsha (krishnamurti / lahiri / raman / surya_siddhanta / true_chitra) |
|---|---|
| native | 2 / 2 / 1 / 2 / 2 |
| chart 2 | 0 / 0 / 0 / 5 / 0 |
| chart 3 | 3 / 3 / 2 / 1 / 3 |

### 3.4 Why the CI guard did not catch it

`check_fact_category_pinning.py` accepts a query that pins `fact_category` plus `fact_key`. R1 and R2 pin both and pass. The guard is fact_key-level by design; it cannot see the formula dimension, so "single row per key across variants" is out of its scope (CLAUDE.md section N.7 item 2's own caveat).

## 4. (c) The natural key: what exists

- `chart_facts.formula_id TEXT NULL` exists (migration 215, `platform/supabase/migrations/215_chart_facts_formula_id.sql`).
- Unique indexes in production: `chart_facts_unique_null_formula (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id) WHERE formula_id IS NULL` and `chart_facts_unique_with_formula (..., build_id, formula_id) WHERE formula_id IS NOT NULL`, plus `chart_facts_pkey (fact_id)` and two sade_sati partial uniques. (The migration-215 index `chart_facts_unique_dedup` was later replaced by these two.)
- `fact_id` for `ga_sensitive` includes `formula_id`. The capture trigger is created with `('fact_id')` as its identity argument, so L1 capture identity is already formula-aware.
- `build_id` is inside every unique key, so the database permits cross-generation duplicates; only the writers' delete helper prevents them. On the three charts that holds today (0 cross-build keys).

**So SS's expectation ("`formula_id` becomes part of the natural key") is already true in the schema.** What is missing is the reader contract and a declaration of which formula is canonical.

## 5. The smallest fix

### 5.1 Mandatory minimum (every reader's choice pinned and deterministic)

Size: small. Roughly four reader edits, one constant, tests. No migration, no owner path, no rebuild, **0 row-count change**.

| # | Change | Where |
|---|---|---|
| M0 | One canonical-formula table, `fact_category -> formula_id` (and optionally `fact_key` scope), as a single constant mirrored in TS and Python with a parity test. | new small module, e.g. `platform/src/lib/retrieval/canonical_formula.ts` and `platform/python-sidecar/brahmagyan/canonical_formula.py` |
| M1 | R1 `chart_facts_query`: select `formula_id`; make the ORDER BY total (`fact_subject, fact_category, fact_key, formula_id, fact_id`); in the pivot, when a (subject, key) has more than one formula, pin the canonical formula and emit the others under a `variants` field (same disclosure shape as R4). `shape=rows` returns `formula_id`. | register_d7_channel.ts |
| M2 | R2 `fetchKarakaRow`: add `AND formula_id = <school>` (school from `expr.school`, else the canonical one), `ORDER BY fact_subject, fact_key, fact_id`; delete the false comment; report the school actually applied. | address_resolver.ts |
| M3 | R3 `get_karakas`: project `fact_subject` and `formula_id`; ORDER BY `category, ayanamsha, subject, key, formula_id, fact_id`. | get_karakas.ts |
| M4 | R4 `get_sensitive_points`: extend ORDER BY with `fact_subject, fact_id`. | get_sensitive_points.ts |

Within the minimum, also: add `fact_id` as the last ORDER BY term in R7 (hygiene) and fix or delete R8 (it is silently empty; fixing it needs a formula pin or it becomes last-wins).

### 5.2 Optional

- **Extend the CI guard** so a read of a category listed in M0's multi-formula set must pin `formula_id` or carry the disclosure. This is the only thing that stops the class from recurring.
- **R7 `bo_laksana`:** carry `formula_id` into the signal's configuration/ledger so variant signals are distinguishable (and check the identity tuple does not collapse value-identical variants).
- **R9/R10 matviews:** pin to the canonical formula or add `formula_id` to the GROUP BY. Requires an owner-path migration only if the matview definitions change.
- **Stricter database key:** a unique index without `build_id`, `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, COALESCE(formula_id,''))`, would be satisfiable on all three charts today (0 violations measured; other charts not checked). It would make cross-generation duplicates impossible instead of writer-policed. This needs `data_plane_l1_owner` (D6-style plan). Not needed for determinism.
- **Unify the two variant encodings** (`formula_id` column versus variant inside `fact_key` in `ga_structural`). Larger, touches writers and digests; not recommended for this fix.
- **Do not collapse the rows.** Deleting non-canonical variants would remove 495 rows per chart (955 minus 460) and discard the WP-1.8 disclosure of genuine classical disagreement. Not recommended.

### 5.3 Decisions needed (not mine to make)

| Category | Evidence for a default | Status |
|---|---|---|
| Yogi / Avayogi | `bphs_93_20` equals `sensitive_point_yogi` (single-valued, `ga_sensitive_degree`) to about 4e-7 degrees; MC-029 already says to prefer it for a single answer. `alt_96_40` is a documented second tradition. | Default `bphs_93_20`; confirm. |
| karaka and Brahma / Vishnu / Shiva | `ga_structural` pins `kn_rao_rahu_included` (BA-P3 fix) and it is the only school with `STRIKARAKA`; `address_resolver` defaults the opposite way (`parashari_rahu_excluded`). Brahma/Vishnu/Shiva follow the school and show 0 contradictions. | **Conflict in the repo.** Needs one ruling. |
| Mrityu | None established. Three formulas, all five ayanamshas disagree on all keys. | **Needs an acharya ruling**; I have not picked one. |

### 5.4 Writers that would change

None for the minimum. `ga_sensitive` keeps emitting all variants. If the optional unification or a canonical flag column were wanted, `ga_sensitive` (and `ga_structural` for the encoding) would change and need a rebuild; neither is required.

### 5.5 Interplay with F-A2 (PR #2858) and the argala rows

- F-A2 widens the **`chart_divisionals`** unique key `(chart_id, graha, ayanamsha_id, varga, fact_category, fact_key) NULLS NOT DISTINCT` by adding `fact_subject`; its stated gain (+14,204 rows on the canonical chart: ashtakavarga, house_lord, d30_per_amsa, sentinels) is in that table. `chart_divisionals` has **no `formula_id` column** and no build_id in its key; its variant convention (D2/D3 `sign_{formula_id}` in `fact_key` / `{vid}.{subject}.{formula_id}` in `fact_subject`, `ga_vargas_writer.py` ~1499-1542) is the same "variant in the key text" encoding as `ga_structural`.
- The two fixes touch different tables, different writers and different layers of the stack; they can land in either order. The shared lesson is the same: a key that omits the discriminator silently drops or merges rows. The D6 owner-path plan in PR #2858 is the template if a `chart_facts` index change is ever wanted; the minimum here needs none.
- **Argala rows in `chart_facts`** (native: `argala_natal_matrix` 21,600, `virodha_argala_natal_matrix` 21,600, `net_argala_per_varga` 1,800): one build, no `formula_id`, **0 duplicate keys**. The PR #2858 plan does not mention argala. No interplay.

### 5.6 Expected row-count effect

| Option | chart_facts rows | chart_divisionals rows |
|---|---|---|
| Mandatory minimum | **0** | 0 |
| Optional guard / matview / bo_laksana changes | 0 | 0 |
| Collapse to canonical (not recommended) | -495 per chart | 0 |
| F-A2 (separate PR) | 0 | +14,204 on the canonical chart (per PR body) |

## 6. Unverified

- The tie order in section 3.2 is emulated with the readers' SQL against production, not observed through the running app or MCP tools; it is plan and storage dependent.
- Only the three named charts were measured; other charts were not checked.
- Consumer search covered `platform/src`, `platform-mcp/src`, `platform/python-sidecar`, and the live DB's views, matviews and functions. `platform/scripts`, `00_ARCHITECTURE` tooling and ad hoc SQL were not searched exhaustively.
- Whether `bodha_signal_identity` separates value-identical variants (R7), and whether any of the 541 native signals cite both variants of one key, were not checked.
- `facts_store.ts` (R11) is judged legacy from its column list; whether any live path calls it was not established.
- The classical correctness of any formula (which Mrityu reckoning is right) is not assessed.
- The `l1_data_plane_capture_row` function was read only to the point of its identity argument; its remaining branches were not audited.
