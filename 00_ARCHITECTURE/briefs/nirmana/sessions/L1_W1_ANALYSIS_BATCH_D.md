---
artifact: L1_W1_ANALYSIS_BATCH_D
canonical_id: NIRMANA_L1_W1_ANALYSIS_BATCH_D
version: "1.0"
status: DRAFT
campaign_id: nirmana-elevation
session: L1
wave: W1
batch: D
assets: [ga_yoga, ga_vichara, ga_sade_sati, ga_transit_anchors]
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
produced_on: 2026-09-05
method: read-only (nq DB queries + source reading + git history). No repo file mutated except this one.
governing_plan: 00_ARCHITECTURE/briefs/nirmana/NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §4 (W1 rubric), §5 (L1 mandate)
---

# L1-W1 Analysis — Batch D (D-SYNTHESIS / D-TIME feeds)

`ga_yoga` · `ga_vichara` · `ga_sade_sati` · `ga_transit_anchors`

Every number below was measured this pass unless explicitly marked as quoted from a prior
artifact. Where a cause could not be established read-only, it is stated as unresolved rather
than guessed (charter C12).

---

## 1. `ga_yoga`

**Registry (live):** `layer=ganita`, `catalog_status=CURRENT`, `target_table=ga_yoga_firings`,
`target_floor=5`, `estimated_seconds=7`, `has_substeps=t`, `depends_on={ga_structural,ga_dashas}`,
`count_sql = SELECT COUNT(*) FROM ga_yoga_firings WHERE chart_id = $1::uuid`,
`expected_volume_formula = YOGAS_IN_CATALOG * AYANAMSHAS_COUNT`, `integrity_check_sql = NULL`.
**Live count: 63.**

### 1. Pillar / doctrine service
**D-GROUNDING (P3) primarily, D-SYNTHESIS (P4) secondarily.** Yoga/dosha firings are named
explicitly in D-GROUNDING as one of the interpretive classes that SHOULD carry a
`grounding_tier`. It is also a D-SYNTHESIS feed: `ga_vichara`'s `leverage_index` reads
`ga_yoga_firings` as its domain-participation signal
(`ga_vichara_writer.py:105-115`). Still the right instrument — a deterministic per-chart
catalog-rule evaluator over a 233-row classical catalog is the correct shape; the gap is in what
it *labels*, not in what it *computes*.

### 2. Real vs declared dependencies
Declared: `{ga_structural, ga_dashas}`. Real reads, from
`platform/python-sidecar/ga_writers/ga_yoga_writer.py`:

| read | source table/category | owning asset | declared? |
|---|---|---|---|
| `graha_position`/`planet_position` (`house_d1`, `sign`, `longitude_sidereal`) | `chart_facts` | `ga_positions` | **no** (transitive via ga_structural) |
| `karakamsa_position` (`sign`, `atmakaraka_graha`) — writer's own comment names `ga_sensitive_writer` | `chart_facts` | **`ga_sensitive`** | **NO — hidden edge** (`ga_yoga_writer.py:384-392`) |
| `graha_shadbala_total` (`rupa`, `required_rupa`) | `chart_facts` | **`ga_strength`** | **NO — hidden edge** (`ga_yoga_writer.py:183-206`; writer docstring names `ga_strength_writer` explicitly) |
| `brahma_yoga_catalog` | L0 table | `bg_yogas` | no (L0-bedrock class — the BA audit's guard-exempt category) |
| `yoga_family_members` | L0 table | L0 | no (same class) |
| `chart_divisionals` D9 + lazy `from ga_writers.ga_structural_writer import _load_varga_positions` (`ga_yoga_writer.py:2436-2441`, `:2841`) | — | `ga_structural` / `ga_vargas` | ga_structural yes; ga_vargas no |

**Two hard hidden edges: `ga_strength` and `ga_sensitive`.** Both are load-bearing: without
`graha_shadbala_total` every firing's `strength` is honestly NULL (`_compute_constituent_bala_strength`
returns five Nones), and without `karakamsa_position` the Jaimini kāraka̍ṃśa yoga cannot fire —
and `jaimini_karakamsha_moon` *is* one of the 15 yogas firing live. `ga_dashas` is declared;
`activation_dasha_periods` is a live column so the edge is presumed real (not re-verified in code
this pass — **stated as unverified**).

### 3. LEVERAGE — the highest-value finding in this batch
**Every one of the 15 firing yogas already has a real classical citation sitting one join away,
and no serving surface reads it.**

- `brahma_yoga_catalog.classical_citations` is populated for **233/233** catalog rows (measured).
  For the 15 yogas that fire on the canonical chart the values are real text+chapter refs, e.g.
  `sasa → [{text_id: bphs, chapter: 75}, {text_id: saravali, chapter: 27}]`,
  `raja_yoga_kendra_trikona → [{text_id: bphs, chapter: "Ch.39 Raja Yoga adhyaya"}]`.
- `ga_yoga_firings.citation_ref` for **13 of the 15** carries instead a self-referential
  instrument string:
  `ga_yoga.strength:<yoga>:constituent_bala_v1@chart=...:bala_gate=graha_shadbala_total`.
  That is computational provenance, not a citation. Only `neecha_bhanga_raja_yoga`
  (`bphs:ch39_raja_yoga_adhyaya:...`) and `jaimini_karakamsha_moon`
  (`jaimini_sutram:1.2...;bphs:ch34...`) carry text-shaped refs.
- This is **deliberate and documented** — `ga_yoga_writer.py:1211-1214`: *"Firing rows'
  citation_ref/citation_human continue to carry the JL-012 strength-derivation citation (set
  uniformly in the main loop); the formation citation is authoritative on the catalog row
  itself."* So the design says "join to the catalog for the classical claim".
- **Nobody performs that join.** `get_yoga_firings.ts` (the handler behind
  `ganita_yoga_firings_get`) queries `ga_yoga_firings` alone — no `brahma_yoga_catalog` join
  anywhere in the file (verified by grep). A caller receives `citation_ref` and reads a
  strength-formula id where a BPHS chapter reference exists and is free.

### 4. Grounding — can firings be labeled `sruti` / `yukti` / `pratyaksa` today?
**Partly yes, today, with no new computation — and the honest ceiling is chapter-level, not
verse-level.**

What exists:
- `brahma_yoga_catalog.classical_citations`: 233/233 populated. Across the whole catalog,
  254 citation entries resolve to 8 distinct `text_id`s. Measured resolvability against the
  10,651-chunk `classical_text_chunks` corpus:

  | text_id | citations | corpus chunks |
  |---|---:|---:|
  | bphs | 143 | 1,459 |
  | saravali | 59 | 471 |
  | phaladeepika | 31 | 564 |
  | **jaimini_sutram** | **12** | **0 — unresolvable** |
  | jataka_parijata | 4 | 704 |
  | sarvartha_chintamani | 3 | 342 |
  | **classical_tradition** | **1** | **0 — not a text** |
  | brihat_jataka | 1 | 607 |

  241/254 (94.9%) resolve at text level; 13 do not. The corpus carries `bphs` chapters
  30/34/35/39/41/75 (all the chapters the 15 firing yogas cite), at 1–2 chunks each.
- `brahma_yoga_catalog.source_chunk_ids`: present as a column on all 233 rows but
  **non-empty on 0 of 233**. The dedicated bridge table `brahma_yoga_source_chunks`
  (`canonical_id`, `source_chunk_id`) **exists and holds 0 rows.**

What that means concretely:
- **`sruti` at chapter granularity is derivable now** for the ~95% of citations whose `text_id`
  is in the corpus — the label is a join, not a build.
- **Verse-level `sruti` is NOT available** and would have to be built: the
  catalog→chunk bridge is an empty table. This is the same work L0's mandate names as
  "chunk citation keys" (plan §5 L0), so it is an L0/L2 dependency, not an L1 fix.
- **`yukti` is the honest label for the strength/bhaṅga layer**: `constituent_bala_v1` is
  explicitly declared "not a classical per-yoga formula, B.10" in the writer's own
  `citation_human`. Labeling it `sruti` would be a fabricated citation (hard-floor violation).
- **`pratyaksa`** is right for `partial_formation_pct` and the fired/not-fired boolean derived
  purely from computed placements.
- 12 `jaimini_sutram` citations (incl. the firing `jaimini_karakamsha_moon`) point at a `text_id`
  with zero corpus chunks — the corpus has `bphs_jaimini` (264 chunks) instead. Either an alias
  gap or a genuine corpus gap; **unresolved read-only.**

Coverage of the existing grounds machinery: `grounds_jsonb` is populated on **3 of 63** firing
rows (all `neecha_bhanga_raja_yoga`). `strength` is populated on **63/63** — note this
*contradicts* `BA_AUDIT_FIX_PLAN_v1_0.md` MINOR item 5 ("strength/is_partial/bhanga_active
NULL/false for 100% of firings"), which has since been fixed by JL-012; that backlog item is
stale and can be closed on this evidence.

### 5. Temporal identity (D-TIME)
Not a temporal engine. It carries one temporal *field* — `activation_dasha_periods` — which
answers "during which dāśā windows is this yoga live". That question is properly L3 Kāla's
(`kala_yoga_activation_get`); L1's copy is a per-firing convenience. **D-TIME item 4
(duplication disposition) applies**: if `kala_yoga_activation_get` and
`ga_yoga_firings.activation_dasha_periods` can disagree, one must be declared the arbiter. Not
tested this pass — **flagged, not asserted.**

### 6. Service
- **Real consumers:** yes, three. MCP `ganita_yoga_firings_get`
  (`platform-mcp/src/tools/register_p1_aliases.ts:975`) → `get_yoga_firings.ts`;
  `ga_vichara`'s `leverage_index`; and `compiled_floor_adapter.ts:162` maps
  `ganita_yoga_firings_get → get_yoga_firings` for the `dhana_yoga_scan`/`nbry_scan` floors.
- **Floor is badly wrong.** `target_floor=5` vs 63 live. `volume_explanation` still reads
  *"only Yuga Nabhasa yoga fires for chart 482012f1 (5 rows = 1 yoga × 5 ayanamshas)"* — false
  now: **15 distinct yogas fire**, 12–13 per ayanamsha. Per §N.4 floors are achieved counts, so
  the floor is stale by 12.6×. But note the count is genuinely volatile — `asset_throughput`
  shows 80 (chart cb73cd3d, 2026-07-27) → 69 (1c826d5a, 2026-08-06) → 63 (482012f1, 2026-08-10)
  as catalog rules were fixed. A hard count floor here is the wrong instrument; an
  `integrity_check_sql` (every firing's `yoga_canonical_id` resolves to a `brahma_yoga_catalog`
  row; every `fired=true` row has non-empty `constituent_fact_ids`) is the right one.
- **Density (§N.6):** `density_contract` IS declared (`get_yoga_firings.ts:144-148`,
  `paginated: true`, 5 facets, `empty_reason: true`). Two real defects behind it:
  1. **`paginated: true` is not true.** The input schema has `limit` (max 50) and **no `offset`**
     (`get_yoga_firings.ts:118-128`). With 63 rows and no ayanamsha filter, **rows 51–63 are
     unreachable** through this tool. `total` is disclosed honestly, so the caller can see rows
     are missing — but cannot fetch them. That is a `density_contract` claim with no
     implementation behind it (§N.8: a signal needs a real detector / a claim needs the code path).
  2. **Non-total `ORDER BY`** (`:187`): `ORDER BY strength DESC NULLS LAST, yoga_canonical_id`.
     Each yoga fires up to 5 times (one per ayanamsha) with tied strength; `ayanamsha_id` is not
     in the sort key, so which 50 of 63 rows come back is not deterministic. §N.7 item 2
     discipline (total `ORDER BY` whenever a set is reduced).
- **Drill in ≤2 hops:** yes to L1 facts (`constituent_fact_ids` → `chart_facts.fact_id`).
  **No** to grounding — there is no hop from a firing to its classical citation (finding above).
- **D-SYNTHESIS duplication (measured):** `ga_structural` writes `yoga_label` (34 rows /
  7 distinct labels) and `dosha_label` (6 rows) into `chart_facts` for the same chart, while
  `ga_yoga_firings` holds 63 rows / 15 yogas. This IS already dispositioned in serving —
  `get_yoga_dosha.ts:36-40,166-173` explicitly names `ganita_yoga_firings_get` as
  "firings-authoritative" and flags its own rows as single-pass catalog matches. Good §N.6
  behavior; recorded here as a satisfied duplication disposition, not a defect.

### 7. Measured build + serve cost
`estimated_seconds = 7`. Measured from `build_run_assets` (51 completed runs, all charts):
min 2.3s, max 41.5s, **avg 9.5s**. Last four completes: 20.9s (2026-08-10), 13.9s, 12.8s, 13.6s.
Estimate is ~2× low against recent runs but the right order of magnitude — the least-wrong
estimate in this batch. Serve cost declared `cost_class: 'cheap'`, consistent with a ≤50-row
single-table read.

### 8. Findings → W2
- **MUST** F-D1 (citation leverage), F-D2 (unreachable rows 51–63).
- **NOW** F-D3 (hidden `ga_strength`/`ga_sensitive` edges), F-D4 (floor 5 → integrity check),
  F-D5 (non-total ORDER BY), F-D6 (grounding_tier labelability).
- **NEVER/LATER** F-D7 (verse-level chunk bridge — L0-owned, empty table),
  F-D8 (`jaimini_sutram` text_id unresolvable — L0 corpus/alias question).

---

## 2. `ga_vichara`

**Registry (live):** `catalog_status=**DRAFT**`, `target_table=chart_vichara`,
`target_floor=0`, `estimated_seconds=30`, `has_substeps=t`,
`depends_on={ga_structural,ga_strength,ga_dashas,ga_yoga}`,
`count_sql = SELECT COUNT(*) FROM chart_vichara WHERE chart_id = $1`,
`expected_volume_formula = GRAHAS x DOMAINS x AYANAMSHAS_COUNT (approx; families vary)`,
`integrity_check_sql = NULL`. **Live count: 8,249.**

### 1. Pillar / doctrine service
**D-SYNTHESIS (P4) + D-SALIENCE (P5).** It is the L1 "judged structure" layer: valence,
cross-varga ratification, varga consistency, and `leverage_index` (the number remedy/intervention
timing ranks on). Still the right instrument, and arguably the single most doctrine-load-bearing
L1 asset after `ga_structural`.

### 2. Real vs declared dependencies
Declared `{ga_structural, ga_strength, ga_dashas, ga_yoga}` — **all four confirmed real** from
`ga_vichara_writer.py`:

| read | category/table | asset | declared |
|---|---|---|---|
| `bhava_significance_link`, `graha_dignity_per_varga`, `graha_functional_class_per_ascendant` | `chart_facts` | `ga_structural` | ✔ |
| `graha_shadbala_total` (`rupa`) | `chart_facts` | `ga_strength` | ✔ |
| `chart_dashas` level_n=1 | table | `ga_dashas` | ✔ |
| `ga_yoga_firings` (fired) | table | `ga_yoga` | ✔ |
| `brahma_vichara_constants` (7 rows) | L0 table | L0 | ✗ (L0-bedrock class) |

**Cleanest dependency declaration in this batch** — no false edges, one L0-bedrock omission of
the already-dispositioned class.

### 3. Leverage
Real and heavy. Consumers verified in source:
- `bo_laksana.py` — `_load_varga_ratification` (`:1043-1075`), `_load_valence_pass`
  (`:1124-1162`), and a first-class MSR emitter per `chart_vichara` row (`:1184-1340`).
- `bo_karanajala.py` — three loaders (`:224-282`) for valence_pass / varga_consistency /
  varga_ratification.
- `bo_upaya.py` — `leverage_index` domain=wealth, read not recomputed (`:1154-1161`,
  provenance string at `:2117`).
- MCP `ganita_vichara_get` → `get_vichara.ts`.
- **Live evidence of consumption:** 9 rows in `bodha_msr_signals` for the canonical chart carry
  `citation_ref LIKE 'chart_vichara%'` — exactly matching the 9
  `varga_ratification_divergence` rows. (Total MSR signals for this chart: 50,104.)

No NULL-where-computed leverage gap found on this asset. One shape note: the divergence family
exists for only 3 of 5 ayanamshas (lahiri, true_chitra, krishnamurti — 3 rows each; raman and
surya_siddhanta have none). That is plausible real ayanamsha-dependence (a varga flips D1's
dignity direction only under some frames) but is served with no note distinguishing "no
divergence" from "not computed". **Unresolved read-only.**

### 4. Grounding
Rows are deterministic transforms of cited L1 facts — `constituent_fact_ids` /
`constituent_facts_array` are real columns and the writer is §N.5-disciplined ("read, never
restate"). `pratyaksa` is the honest tier for valence_pass / varga_consistency / leverage_index.
`varga_ratification`'s `ratification_factor ∈ [0.6,1.4]` band and the `leverage_index` weighting
are principle-derived — those are **`yukti` candidates**, sourced from
`brahma_vichara_constants` (7 rows), which is exactly the right shape for a stated derivation
chain. No fabricated-citation risk observed.

### 5. Temporal identity (D-TIME)
One temporal term: `leverage_index` is "forward-weighted by dāśā runway", built from
`chart_dashas` level-1 rows. That is a *derived-from-time* quantity, not a temporal engine; it
answers "how much does this subject matter going forward", not "when". It has no arbiter
relationship with `ga_sade_sati`/`ga_transit_anchors`. `bo_upaya.py:2133` already notes it does
NOT reuse the embedded runway sub-field — a duplication of intent worth one line in W2, no more.

### 6. Service — SPECIAL ASSIGNMENT 3, resolved
**Verdict: (a) real and mis-labeled. `catalog_status=DRAFT` is wrong and should be `CURRENT`.**

Evidence for "real":
- 8,249 rows, arithmetically exact: 5 ayanamshas × (1,595 valence_pass + 35 leverage_index +
  9 varga_consistency + 9 varga_ratification = 1,648) = 8,240, plus 9
  `varga_ratification_divergence` rows (3 ayanamshas × 3) = **8,249.** Measured, reconciles to
  the row.
- Three L2 production writers read the table (§3 above), one of them (`bo_laksana`) emitting
  first-class MSR signals from it. `bo_laksana.py:1031` states plainly: *"chart_vichara SHIPPED
  2026-07-14 and is live — this is no longer a [stub]."*
- Built repeatedly and cleanly by the orchestrator: `asset_throughput` shows 8,249 / 8,247 /
  8,240 across three charts, 18 completed `build_run_assets` runs.
- Its serving surface is the **best §N.6 citizen in the batch** — full `density_contract`,
  byte caps, loud facet rejection, structured `empty_reason`, graceful missing-table degradation
  (`get_vichara.ts`).

Evidence that DRAFT is doing harm rather than nothing: `catalog_status` is read in
`platform/src/app/api/cockpit/registry/route.ts:36,68`, rendered as a `DRAFT` pill in
`PlanModal.tsx:207-228` and `AssetRow.tsx:283-323`. So every operator planning a build sees the
one L1 asset that L2's three biggest writers depend on flagged provisional. It is the only
`DRAFT` in the layer (18 CURRENT, 1 DRAFT, measured). It does **not** block builds — the label is
purely advisory — which is precisely why it is a truth defect rather than an outage: the cockpit
says one thing, the DAG does another.

`target_floor = 0`: per §N.4 floors are achieved counts, so 0 is simply unset. Set to 8,249
(or better, formula-derived, since valence_pass scales with `ga_structural` output).

Drill: ≤2 hops to L1 via `constituent_fact_ids`. `get_vichara.ts` `ORDER BY vichara_family,
domain NULLS FIRST, subject` is **not total** — 1,595 valence_pass rows per ayanamsha share
(family, domain=null, subject) values, and `varga`/`varga_id`/`ayanamsha_id` are not in the sort
key. With `LIMIT/OFFSET` pagination over 8,249 rows this is non-deterministic paging; same defect
class as `ga_yoga`'s.

### 7. Measured build + serve cost
`estimated_seconds = 30`. Measured (18 completes): min 14.1s, max 1,272.2s, **avg 307.1s**.
The distribution is bimodal and the split is by date, not by row count:

| date | secs | rows |
|---|---:|---:|
| 2026-07-16 → 07-27 (8 runs) | 17–31 | 8,240 |
| 2026-08-06 → 08-10 (4 runs) | 653, 679, 805, 619 | 8,247–8,249 |

~22× slowdown for a 0.1% row change. `ga_sade_sati` shows the *same* jump over the same window
(31s → 510s, §3.7). Two assets, same date boundary, same magnitude → this looks environmental
(DB latency / connection path / runner change between 2026-07-27 and 2026-08-06), not
algorithmic. **Cause not determinable read-only — stated as unresolved.** Either way
`estimated_seconds=30` is stale by ~20× against the most recent evidence, which matters for W4
scheduling.

### 8. Findings → W2
- **MUST** F-D9 (DRAFT → CURRENT).
- **NOW** F-D10 (floor 0 → 8,249), F-D11 (non-total ORDER BY), F-D12 (estimated_seconds 30 →
  measured; shared with `ga_sade_sati`).
- **NEVER/LATER** F-D13 (divergence-family ayanamsha asymmetry note).

---

## 3. `ga_sade_sati`

**Registry (live):** `catalog_status=CURRENT`, **`target_table=NULL`**, `target_floor=11,019`,
`estimated_seconds=65`, `has_substeps=f`, `depends_on={ga_positions, ga_strength, ga_panchanga,
ga_vargas, ga_dashas, ga_structural, ga_nakshatra}`, `integrity_check_sql=NULL`,
`expected_volume_formula = AYANAMSHAS`. `count_sql` counts 15 `chart_facts` categories.
**Live count: 6,287 — 4,732 below floor (−43%).**

### 1. Pillar / doctrine service
**D-TIME (P6).** It is a temporal engine: Saturn transit windows relative to the natal Moon over
1950–2100. Also feeds D-SYNTHESIS via overlays (concurrent dāśā, argala-during-period, tāra bala
at Janma peak). Still the right instrument.

### 2. Real vs declared dependencies
The writer's own `_verify_upstream_rows` (`ga_sade_sati_writer.py:1435-1483`) gates on five
upstreams — GA3 `graha_position`, GA4 `tara_bala*`, GA6 `%varga%`, GA7 `chart_dashas`,
GA8 `argala_natal_matrix` — plus reads of `varga_position` and `varga_karya_bhava_per_varga`
and `chart_divisionals` (D9).

| declared | real? | evidence |
|---|---|---|
| `ga_positions` | ✔ | `graha_position` MOON/SAT |
| `ga_dashas` | ✔ | `chart_dashas` (`_lookup_dasha_lord_at`, 7 systems × 3 phases per cycle) |
| `ga_vargas` | ✔ | `%varga%` gate + `chart_divisionals` D9 (`:1657`) |
| `ga_structural` | ✔ | `argala_natal_matrix` (`:1478`, `:1634`), `varga_karya_bhava_per_varga` (`:1693`) |
| `ga_nakshatra` | ✔ | `tara_bala_natal_baseline` (`:1605`) |
| **`ga_strength`** | **NO** | zero `shadbala` reference anywhere in the file (grepped) |
| **`ga_panchanga`** | **doubtful** | the only `panchanga` reference is the *engine import* for swisseph Saturn transit detection (`:44`) and a comment mirroring `ga_panchanga_writer.NAKSHATRA_SHORT` (`:231`). No `chart_facts` panchanga category is read. |

So: **2 false/over-declared edges** (`ga_strength` definitely, `ga_panchanga` as a code-import
rather than a data edge). Over-declaration is not a correctness bug but it inflates the DAG,
delays this asset behind two upstreams it does not consume, and violates the derivation-ledger
spirit (§I B.3). `target_table` is NULL while rows live in `chart_facts` — the cockpit's
`target_table` column is simply wrong here (same class as the BA audit's
`bo_cdlm_summary`/`bo_chart_gestalt` MINOR item 8).

### 3. Leverage
Real consumers: `bo_laksana.py`, `bo_karanajala.py`, `bo_upaya.py`, `ka_sangam.py`,
`mi_adhilepa.py` (grep on `sade_sati` across the writer tree), plus MCP `ganita_sade_sati_get`
→ `get_sade_sati.ts`, plus `L4_PHALA_DECISIONS_LEDGER_v1_0.md:79` records it as a READ input.
Well plugged in. No NULL-where-computed gap found.

One serving gap: `get_sade_sati.ts` line 97 —
`ORDER BY fact_category, ayanamsha_id, fact_key` omits `fact_subject`. With
4 cycles × 3 phases × 4 quarters all sharing (category, ayanamsha, key), and the `all:true` path
applying LIMIT/OFFSET directly to this query, paging is non-deterministic. The default path is
safe (it fetches 20,000 internally then filters/slices in JS — a deliberate MC-014 fix), so the
exposure is limited to `all:true` callers. Same §N.7-item-2 class as the other two.

### 4. Grounding
`pratyaksa` throughout, correctly: these are swisseph/DE441-computed transit windows. The
overlays (modifier, cancellation_check) apply classical rules and are `yukti` candidates but the
writer's `citation_human` already narrates the derivation. **No grounding change recommended for
this asset** — D-GROUNDING is explicitly selective, and a per-row tier here would be uniform
noise.

### 5. Temporal identity (D-TIME) — see §5 below for the concordance analysis.

### 6. Service
Consumers: yes (§3). Floor: **the central question — §5 below.** Density: `get_sade_sati.ts`
carries **no `density_contract`** despite serving the largest fact family in L1 outside
`ga_structural`/`ga_dashas`; it does implement the substance (window filter, disclosed
`total_before_window_filter` / `periods_dropped_outside_window` / `drill_uri`) — so this is a
missing *declaration*, not missing behavior. Drill: `emits_references: true`,
`grounds_to.l1_fact_ids: true`, rows carry `fact_id` — 1 hop. Good.

Registry/serving category-list duplication: the 15 categories are hand-maintained in **two**
places — `asset_registry.count_sql` and `SS_CATEGORIES` in `get_sade_sati.ts:15-21`. They agree
today (verified name-by-name). This is exactly the drift hazard the BA audit flagged for
`ga_structural` ("silently drifted twice, migrations 364/368"). A `fact_category_ownership` row
set would fix both — and note **`fact_category_ownership` has 0 rows for all four batch-D
assets** (measured), so that table is not yet the SSoT the campaign brief expects it to be.

### 7. Measured build + serve cost
`estimated_seconds = 65`. Measured (51 completes): min 18.4s, max 783.0s, **avg 141.9s**.
Recent completes: 510.3s (2026-08-10), 547.7s, 541.0s, 557.5s — vs 31.4s / 26.8s / 30.7s in
late July. Same date-boundary jump as `ga_vichara`. Estimate stale by ~8× against current
evidence. `build_run_assets` also shows a long tail of `error`/`aborted` rows for this asset
across 2026-07-05 → 2026-08-05 (the R6 rebuild campaign) — historical, not current.

### 8. Findings → W2
- **MUST** F-D14 (floor −43%: see §5, resolved as stale-floor-from-a-defective-writer).
- **NOW** F-D15 (2 over-declared edges), F-D16 (`target_table` NULL), F-D17 (category list
  duplicated in registry + TS), F-D18 (no `density_contract`), F-D19 (`estimated_seconds`),
  F-D20 (`all:true` non-total ORDER BY).

---

## 4. `ga_transit_anchors`

**Registry (live):** `catalog_status=CURRENT`, `target_table=ga_transit_anchors`,
`target_floor=45`, `estimated_seconds=1`, `has_substeps=t`, `depends_on={ga_positions}`,
`count_sql = SELECT COUNT(*) FROM ga_transit_anchors WHERE chart_id = $1`,
`expected_volume_formula = GRAHAS * AYANAMSHAS`, `integrity_check_sql=NULL`.
**Live count: 45 (exact).**

### 1. Pillar / doctrine service
**D-TIME (P6)** — declared as "Transit/Gochara Subsystem Gate-1", the natal reference substrate
gochara is reckoned against. See §5: whether it is still the right instrument is genuinely open,
because nothing reads it.

### 2. Real vs declared dependencies
Declared `{ga_positions}`. Real: `chart_facts` `fact_category IN ('graha_position',
'graha_sign_attributes')`, `fact_key IN ('sign','longitude_sidereal')`
(`ga_transit_anchors.py:106-127`) — that is `ga_positions`. **Exact match, no hidden or false
edges.** The only other import is `brahmagyan.graha_vocabulary.to_title` (an L0 code SSoT, not a
data edge).

### 3. Leverage — the second-biggest finding in this batch
**`ga_transit_anchors` has exactly one reader in the entire codebase: its own MCP serving
capability. No writer at any layer reads the table.** Measured by grepping the whole repo for
`ga_transit_anchors` and grouping by file — the only non-doc, non-migration, non-test hits are
its own writer (11), `get_transit_anchors.ts` (3), and `asset_registry_seed.ts` (4). No L3 Kāla
gochara writer, no L4, no L5.

And there is a **designed consumer reading nothing where this asset already has the answer**:
- `bg_vidhi_primitives.py:78` defines the acharya-floor vidhi primitive `from_moon_view` —
  *"Chandra-lagna re-derivation of house/karaka reads (bhāva reckoned from Moon, not just
  Lagna)"* — dispatching `ganita_chart_facts_get` with
  `tool_args: {chart_id, reference_point: 'moon'}`.
- **No tool anywhere reads a `reference_point` argument.** Grepping `reference_point` across
  `platform/src` and `platform-mcp/src` returns exactly two hits, both the vidhi registry rows
  themselves (`platform/src/lib/vidhi/registry_data.ts:86`,
  `platform-mcp/src/resources/vidhi/registry_data.ts:71`). The argument is silently dropped at
  the tool boundary — a CR-42-class silent-degradation to the unfiltered corpus.
- Meanwhile `ga_transit_anchors.natal_house_from_moon` holds precisely that answer, for all
  9 grahas × 5 ayanamshas, verified live (lahiri: moon=1, mercury/sun=12, jupiter/venus=11,
  ketu=10, mars/saturn=9, rahu=4).
- A third independent re-derivation of the same quantity exists at serve time:
  `register_d9_judgment.ts:780-807` resolves the chandra frame via `resolveAddress(..., frame:
  'chandra')` and pushes `from_moon_resolution_failed` when it throws.

So: one stored asset with the answer, one designed consumer whose argument is inert, and one
serving-layer re-derivation — the classic §N.6/D-SERVICE "built-but-unplugged" shape, with a live
consumer pointing at the wrong door.

### 4. Grounding
`pratyaksa` — natal positions and a modular arithmetic house count. `natal_house_from_moon` is a
classical reckoning convention (`gochara` counted from Janma Rāśi) that could carry a `yukti`
label with a one-line derivation, but per D-GROUNDING's selectivity clause this is not an
interpretive class and should stay unlabeled.

### 5. Temporal identity (D-TIME) — see §6 below, SPECIAL ASSIGNMENT 2.

### 6. Service
- **Consumer:** only `ganita_transit_anchors_get`. `canonical_faces.json:37` lists it as a
  canonical face, so it is exposed, not hidden — but nothing in the data plane consumes it.
- **Floor:** `target_floor = 45`, live 45, formula `GRAHAS * AYANAMSHAS` — **the only fully
  consistent floor+formula+achieved triple in this batch.** Derivation confirmed against the
  writer: `_SUBJECT_TO_GRAHA` maps exactly 9 subjects
  (SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN — mean nodes only, no true nodes),
  `_AYANAMSHAS` is exactly 5, one row per (graha, ayanamsha). 9 × 5 = 45, and the live table
  is 9 distinct grahas in each of 5 ayanamshas (measured).
  One integrity gap: if a graha's `chart_facts` row is missing the writer logs a warning and
  **skips the row** (`:170-181`), returning a short count with no failure. There is no
  `integrity_check_sql` asserting 45; the floor is the only backstop and floors are aspirational
  by §N.4. This is a §N.8 shape — a "complete" build signal with no detector for the specific
  claim "all 9 grahas present in all 5 ayanamshas".
- **Density:** `get_transit_anchors.ts` has **no `density_contract`**, no `empty_reason`, and
  `grounds_to: { l1_fact_ids: false }` — it serves derived values with no pointer back to the
  `chart_facts` rows they came from, even though the writer read specific `fact_id`s to build
  them. Drill to L1 is therefore **0 hops in the wrong direction**: a caller cannot get from an
  anchor row to the position fact.
- Positive note: the writer carries a real FORENSIC assertion (Moon must be Aquarius for the
  canonical chart under any ayanamsha, `:135-144`) that raises `AssertionError` — a genuine
  detector, §N.8-compliant. **But see §6 below: it fires against the *lahiri-family* answer and
  the surya_siddhanta row legitimately stores `pisces`, so the assertion is checked before the
  per-ayanamsha divergence is honored.** Measured: the surya_siddhanta anchor row for moon reads
  `pisces`. Since the assertion runs per-substep (per ayanamsha) and demands `aquarius`, the
  surya_siddhanta substep should raise — yet the row exists. Either the assertion path is not
  reached for that ayanamsha or the rows predate it. **Unresolved read-only; flagged as a
  correctness question for W2, not asserted as a bug.**

### 7. Measured build + serve cost
`estimated_seconds = 1`. Measured (47 completes): min 0.2s, max 12.6s, **avg 2.3s**; recent:
9.8s / 10.0s / 9.2s (August), 2.0–2.2s (July). Cheapest asset in the batch by an order of
magnitude; the estimate is low but the absolute error is seconds. Serve: declared
`cost_class: 'cheap'`, 45-row single-table read — accurate.

### 8. Findings → W2
- **MUST** F-D21 (`from_moon_view` inert `reference_point` → wire to this asset),
  F-D22 (FORENSIC assertion vs surya_siddhanta pisces row — resolve or explain).
- **NOW** F-D23 (zero data-plane consumer: WIRE or record a disposition),
  F-D24 (no integrity check for the 9×5 completeness claim),
  F-D25 (no `density_contract` / `grounds_to.l1_fact_ids: false`).

---

# SPECIAL ASSIGNMENT 1 — `ga_sade_sati` −4,732 rows, derived

Charter C12: derive, never pick. Three steps: derive the expected volume, attribute the delta to
a named cause, then rule.

## (i) Derivation from first principles

`target_table` is NULL; `count_sql` shows the rows live in `chart_facts` under 15 fact
categories. Measured breakdown, canonical chart, per ayanamsha (`lahiri_chitrapaksha`):

| fact_category | rows | scales with |
|---|---:|---|
| sade_sati_cycle | 32 | 4 cycles × 8 keys |
| sade_sati_phase | 304 | 4 × (25+26+25) |
| sade_sati_phase_quarter | 336 | 4 × 3 phases × 4 quarters × 7 keys |
| sade_sati_saturn_retrograde_subset | 120 | 4 × 30 |
| sade_sati_modifier_overlay | 60 | 4 × 15 |
| sade_sati_concurrent_dasha_overlay | 28 | 4 × 7 |
| sade_sati_downstream_cross_reference | 12 | 4 × 3 |
| sade_sati_cancellation_check | 8 | 4 × 2 |
| janma / vishakha / anumukha_shani_period | 20 each | 4 × 5 |
| **cycle-scaling subtotal** | **240 per cycle** | |
| dhaiya_period | 138 | flat |
| ardha_ashtama_shani_period | 69 | flat |
| ashtama_shani_period | 52 | flat |
| kantaka_shani_period | 40 | flat |
| **flat subtotal** | **299** | |

**Volume model: `rows_per_ayanamsha = 240 × N_cycles + 299`.**
At N=4: 240×4 + 299 = **1,259** — matches the measured lahiri total exactly.
Across 5 ayanamshas: 5 × 1,259 = 6,295. Measured total is **6,287**; the 8-row difference is
`sade_sati_saturn_retrograde_subset` = 112 under `surya_siddhanta_classical` vs 120 elsewhere
(two fewer RETRO_3 groups × 4 keys), which is a real consequence of that ayanamsha placing the
Moon in Pisces rather than Aquarius (measured). **6,287 reconciles to the row.**

Now derive N_cycles independently of the code. The native's Moon is Aquarius (4 of 5 ayanamshas).
Sāḍe-sātī = Saturn transiting the 12th/1st/2nd from natal Moon = Capricorn → Aquarius → Pisces.
Saturn's sidereal period is ~29.46y, so the 1950–2100 window (`WINDOW_START`/`WINDOW_END`,
`ga_sade_sati_writer.py:69-70`) spans 150/29.46 ≈ **5.09 cycles**. The writer then applies the
D-2 birth clip (`:2003-2020`): drop any cycle whose `cycle_end` precedes the native's birth
(1984-02-05). The 1961–1969 Capricorn→Pisces passage ends ~15 years before birth and is dropped.
**Expected N after clip = 4.**

Measured cycle boundaries confirm it exactly (lahiri):
`CYCLE_1 1990-03-20 → 1998-04-17`, `CYCLE_2 2020-01-24 → 2027-06-02`,
`CYCLE_3 2049-03-06 → 2057-04-07`, `CYCLE_4 2079-01-14 → 2086-05-21`.
Four cycles, ~29.5y apart, all post-birth. **The derivation and the live data agree. 6,287 is
the astronomically correct volume for this native under the current writer.**

## (ii) Attribution of the delta to a named cause

The floor's own `volume_explanation` reads: *"target_floor = 11,019 = achieved canonical count
for chart 482012f1 (2026-06-11)."* So 11,019 is a June-11 achieved count, not a spec.
The trajectory, from repo artifacts and live measurement:

| date | count | chart | source |
|---|---:|---|---|
| 2026-06-11 | 11,019 | 482012f1 | floor set (`L1_GANITA_BUILD_CLOSE_v1_0.md:169,253`) |
| 2026-07-05 | 9,790 | 1c826d5a | `BA_FULL_ASSET_AUDIT_REGISTER_v1_0.md:221-222` |
| 2026-07-10 | 6,280 / 6,287 | both | `R6_RUN_LEDGER_v1_0.md:253` |
| 2026-08-10 | **6,287** | 482012f1 | measured this pass, single `build_id` |

The named cause is **PR #522 / commit `8c2af1468` (2026-07-10), "fix(r6-0d): lifetime-clip
integrity — pre-birth anchors/parvas + sade-sati dedup — T-5/T-9/D-2/V-13"** — two deliberate
correctness fixes to a demonstrably defective writer, documented in
`R6_RUN_LEDGER_v1_0.md:579-586`:

1. **D-2/V-13 retrograde-shadow duplicate cycles.** *"Saturn retrograde sign-boundary dance
   produced duplicate forward vishakha_entry candidates resolving to the same downstream chain
   (same cycle_end, different cycle_start) — reproduced live on both charts (e.g. CYCLE_3/CYCLE_4
   sharing cycle_end=1998-04-17 on 482012f1)."* The pre-fix writer emitted phantom cycles.
   Migration 428/429's guard query subsequently confirmed **0 duplicate `sade_sati_cycle` rows
   across all 4 charts in the DB**, and the ledger records *"both charts clean 160-row sets"* —
   160 = 4 cycles × 8 keys × 5 ayanamshas, matching this pass's measurement exactly.
2. **T-9/D-2 pre-birth clip.** `birth_params` was accepted but unused; cycles that ended before
   the native was born were being served as the native's own. Removing the 1961–1969 cycle costs
   240 × 5 = **1,200 rows** by the volume model above.

Two further row-shape changes fall between the floor date and now and account for the rest of the
gap in a direction I can name but not quantify read-only:
3. `3a488219b` (2026-07-05) wired the `natal_facts` scaffold to real GA3/GA4/GA6/GA7/GA8 data
   (+419/−39 lines). Every enriched key is now emitted **conditionally** (`if val is not None`,
   e.g. `:2064-2094`) where the scaffold previously emitted placeholders unconditionally.
4. `88f10a80d` (2026-06-29, "Wave 3 — grounding violations, false attribution, inert guards")
   and `31009f219` (2026-08-04, "honest verification-tier emission") both removed
   fabricated/over-claimed rows.

**Honest limit:** I can attribute 1,200 rows to the birth clip arithmetically and the remainder
(≈3,530) to the dedup plus the conditional-emission and honesty fixes, but I cannot decompose
that remainder exactly without checking out and executing the June-11 writer, which is outside
this pass's read-only scope. Attempting to solve for it algebraically fails cleanly and says so:
if the June writer had today's per-cycle shape, 5×(240N+299)=11,019 gives N=7.94 — not an
integer, i.e. the per-cycle row shape *also* changed, exactly as commits 3 and 4 predict. That
non-integer is itself the evidence that this is not a pure cycle-count story.

## (iii) Ruling

**The −43% is NOT a regression and NOT a bare stale floor. It is a stale floor whose value was
achieved by a writer since proven defective.** 11,019 counted phantom retrograde-shadow cycles
and a Sāḍe-sātī the native never lived through. Re-baselining to a lower number here is a
*correctness improvement being recorded*, not a shortfall being papered over — the same
distinction §N.4 draws when it says floors are achieved counts, and the same distinction the R6
ledger drew for `ga_structural` when `yoga_label` legitimately dropped 409→34.

Recommended W2 disposition:
- Route `rebuild_only`; re-baseline `target_floor` 11,019 → **6,287** with a
  `volume_explanation` that states the model (`5 × (240 × N_cycles + 299)`, minus ayanamsha-
  specific retrograde variance) and names PR #522 as the reason the number moved. A bare number
  swap would reset the same clock that produced this finding (DVA Ruling 16's lesson).
- Prefer, and this is the durable fix: an `integrity_check_sql` asserting the *invariants* rather
  than the count — every `sade_sati_cycle` has `cycle_end >= birth_date`; no two cycles share a
  `cycle_end` within an ayanamsha (migration 429's indexes already enforce this at write time, so
  the check is cheap); `count(DISTINCT cycle) per ayanamsha` is consistent across ayanamshas.
  A count floor cannot distinguish "4 correct cycles" from "4 wrong cycles"; these invariants can.
- **Cross-check the other two below-floor L1 assets against this template before assuming the
  same answer.** `ga_dashas` (−52,612) is a different shape: its floor 536,471 is also a June
  achieved count, but the R6 ledger records a *rebuild* to 553,307 rows on this chart
  (`R6_RUN_LEDGER_v1_0.md:251-252`) — higher than both the floor and the current live count.
  That is a genuinely different and unexplained trajectory and must be derived separately, not
  by analogy. (Noted for the batch owner; `ga_dashas` is not in batch D.)

---

# SPECIAL ASSIGNMENT 2 — D-TIME feed certification

## 2a. What `ga_transit_anchors` actually produces — 45 of what?

**45 = 9 grahas × 5 ayanamshas**, one row per pair, derived from the writer not assumed:
`_SUBJECT_TO_GRAHA` (`ga_transit_anchors.py:32-36`) builds exactly 9 entries from
`(SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN)`; `_AYANAMSHAS` (`:39-45`) is exactly
the 5 canonical ids; `plan_substeps` emits one substep per ayanamsha, each inserting one row per
graha found. Live: 9 distinct grahas in each of 5 ayanamshas = 45 (measured).
`expected_volume_formula = GRAHAS * AYANAMSHAS` is **consistent with the real 45**, and
`volume_explanation` states it correctly. This is the one clean formula/floor/achieved triple in
the batch.

Two scope facts worth recording rather than treating as defects: the node set is **mean nodes
only** (`RAH_MEAN`/`KET_MEAN`, no true-node rows), and per-row content is
(`natal_sign`, `natal_house_from_moon`, `natal_degree_absolute`) — a *natal* substrate, not a
transit ephemeris. Nothing in the asset knows where Saturn is today; it knows what today's
Saturn must be measured against.

## 2b. Where AV transit gating actually lives — plainly

**It is NOT `ga_transit_anchors`, and it is not one asset.** Traced end to end:

- `ganita_av_transit_gating_get` is an **alias** registered at
  `platform-mcp/src/tools/register_p1_aliases.ts:995`, pointing at the registry capability
  `marsys://tool/L1/get_av_transit_gating`.
- That capability is
  `platform/src/lib/retrieval/registry/layers/L1_ganita/get_av_transit_gating.ts`. Its own header
  (`:6-8`) names its source: *"Consumes the sign-keyed Aṣṭakavarga facts shipped in D-1.5b Lane
  B-2 (`ga_strength_writer.py` → chart_facts categories `ashtakavarga_bindu_sign` and
  `ashtakavarga_kakshya_boundary`)."*
- Measured live for the canonical chart: `ashtakavarga_bindu_sign` = **480** rows,
  `ashtakavarga_kakshya_boundary` = **120** rows. Both are counted under
  **`ga_strength`**, not under `ga_transit_anchors`.

So mode `sav_bav_gating` reads stored `ga_strength` facts and classifies them at serve time
against the classical mean 337/12 ≈ 28.08 bindus/sign (`SAV_MEAN_BINDUS`, `:66`).

Mode `kakshya_windows` is the more consequential finding: **it computes at serve time, from L0,
using a documented approximation.** Per the handler's own header (`:19-31`), it builds dated
kakṣyā sub-windows from BRAHMA's L0 daily ephemeris, *"tropical, converted to sidereal via a
documented Lahiri mean-rate approximation (see estimateLahiriAyanamshaDeg below) — the raw
ephemeris_daily cache stores tropical rows only (verified live this pass; no pre-computed
sidereal cache exists)."*

**Plain statement for the D-TIME certification:** the "AV transit gating" D-TIME feed does not
live in a single stored L1 asset. Its *gating* half is stored `ga_strength` ashtakavarga facts
read verbatim; its *timing* half is computed in TypeScript at request time from L0
`ephemeris_daily` with a mean-rate ayanamsha approximation. `ga_transit_anchors` participates in
neither. That matters for the campaign in three ways:
1. The stored half is certifiable by an L1 integrity check on `ga_strength` (480 = 12 signs ×
   (1 SARVA + 7 BAV grahas) × 5 ayanamshas is the obvious model to verify — **not verified this
   pass**, `ga_strength` is another batch's asset).
2. The computed half is **not** covered by any L1 asset's `count_sql`, `target_floor`, or
   staleness signal. A change to `estimateLahiriAyanamshaDeg` silently changes every kakṣyā
   window with no build, no receipt, and no invalidation. That is a real D-TIME gap and belongs
   in the W2 ledger even though the code is serving-plane (and therefore lands in W3 without a
   freeze exception).
3. Honest credit: the handler is unusually well-behaved about it — it declares the approximation
   in prose, refuses to fabricate (CR-87: no default chart/planet/date), computes real per-planet
   durations from actual daily speed rather than a fixed day-count, and carries a full
   `density_contract` with `empty_reason`. The gap is governance coverage, not honesty.

## 2c. Temporal Concordance Contract — which question does each asset answer, and who arbitrates?

Per D-TIME (1) every temporal engine declares its question; (4) duplications get explicit
dispositions.

| asset / surface | question it answers | range | frame |
|---|---|---|---|
| `ga_transit_anchors` | "Against what natal positions is any transit reckoned — and what house from the Moon does each graha natally occupy?" | timeless (natal) | per-ayanamsha |
| `ga_sade_sati` | "When is Saturn in the 12th/1st/2nd from this native's natal Moon, at cycle/phase/quarter grain, 1950–2100?" | 150y | per-ayanamsha |
| `get_av_transit_gating` (`ga_strength` + serve-time) | "How much should a transit window through sign X be damped or amplified, and which kakṣyā sub-arc is a planet in on date D?" | caller-supplied | Lahiri-approximate for the dated half |
| `ga_yoga.activation_dasha_periods` | "In which dāśā windows is this yoga live?" | lifetime | per-ayanamsha |

**Do `ga_sade_sati` and `ga_transit_anchors` agree? Measured: they are consistent, and they both
diverge from the lahiri-family answer in the same direction under one ayanamsha.**

The natal Moon sign is genuinely ayanamsha-dependent for this native — an AQ/PI boundary case the
`ga_sade_sati` writer documents in code (`:2093`, *"cross-ayanamsha divergence at AQ/PI boundary
is REAL"*). Measured `graha_position` MOON sign: Aquarius under lahiri_chitrapaksha, true_chitra,
krishnamurti, raman; **Pisces under surya_siddhanta_classical.**

Both assets honor it, consistently:
- `ga_transit_anchors`: under surya_siddhanta every `natal_house_from_moon` shifts by one
  (moon=1 in both; saturn 9→8, jupiter 11→10, sun 12→11, rahu 4→3 — measured).
- `ga_sade_sati`: the surya_siddhanta cycles are **entirely different windows** —
  `CYCLE_1 1993-03-05 → 2000-06-06` and `CYCLE_2 2022-04-29 → 2029-08-08`, versus lahiri's
  `1990-03-20 → 1998-04-17` and `2020-01-24 → 2027-06-02` (measured).

**This is exactly the duplication D-TIME item 4 requires a disposition for**, and it is sharper
than a mere duplication: two stored L1 assets both make a Saturn-relative-to-Moon claim, both are
internally correct, and they give a native two answers to "is my Sāḍe-sātī running now?" that
differ by **~3 years and 2 months** at cycle start. On 2026-09-05: under lahiri the native is
mid-cycle (2020-01-24 → 2027-06-02); under surya_siddhanta also mid-cycle (2022-04-29 →
2029-08-08) — so today they agree on *whether*, but disagree on when it ends by over 2 years.

**Who arbitrates today: nobody.** There is no arbiter surface emitting
`aligned | partially_aligned | disputed` for this pair, and no stored adjudication profile
(D-TIME item 3 names `kala_gochara_authority`/`kala_paddhati_profile` as the things to
generalize — neither is consulted by either asset or by `get_sade_sati.ts`). `get_sade_sati.ts`
serves all ayanamshas' rows side by side with no note that they encode contradictory windows;
`get_transit_anchors.ts` likewise. The serving layer *does* have the right machinery one layer
up — `register_d9_judgment.ts:794-805` emits a `moon_frame_ayanamsha_sensitive` judgment flag
precisely when the Moon's sign disagrees across ayanamshas, disclosing rather than picking — but
that flag lives in D9 judgment, not in either L1 surface.

**Recommended disposition (W2):** declare `ga_transit_anchors` the natal-frame authority (it is
the substrate both the gochara reckoning and `ga_sade_sati`'s Moon-sign read depend on) and
`ga_sade_sati` the Saturn-window authority within a declared ayanamsha; then require both serving
surfaces to carry the same `moon_frame_ayanamsha_sensitive`-class disclosure `register_d9_judgment`
already emits, so a cross-ayanamsha Sāḍe-sātī answer is never served as a single voice
(D-SYNTHESIS: "the verdict voice is always singular" — which here means one *declared frame*, not
one silently-picked row). This is a disclosure fix, not a ruling on which ayanamsha is right, and
should not be resolved by picking one.

---

# Consolidated findings

| id | asset | finding | evidence | proposed triage | doctrine cited |
|---|---|---|---|---|---|
| F-D1 | ga_yoga | Classical citations exist for all 15 firing yogas in `brahma_yoga_catalog.classical_citations` (233/233 populated) but no serving surface joins them; `ga_yoga_firings.citation_ref` carries a self-referential strength-formula id for 13/15 rows | measured catalog coverage; `ga_yoga_writer.py:265-273` (ref construction), `:1211-1214` (intent), `get_yoga_firings.ts` (no catalog join) | **MUST** — join or project the catalog citation onto the firings surface | D-GROUNDING; §N.6 pt.3; plan §4 rubric 3 |
| F-D2 | ga_yoga | `density_contract.paginated: true` with no `offset` input and `MAX_LIMIT=50` against 63 live rows → rows 51–63 unreachable | `get_yoga_firings.ts:118-128,144-148`; live count 63 | **MUST** — add `offset`, or drop the paginated claim | §N.6 pt.4; §N.8 (claim without a code path) |
| F-D3 | ga_yoga | Hidden dependencies: reads `graha_shadbala_total` (`ga_strength`) and `karakamsa_position` (`ga_sensitive`); neither declared | `ga_yoga_writer.py:183-206`, `:384-392`; registry `depends_on={ga_structural,ga_dashas}` | **NOW** — add both edges | §I B.3; D-SERVICE |
| F-D4 | ga_yoga | `target_floor=5` vs 63 live; `volume_explanation` still claims only 1 yoga fires. Count is volatile (80→69→63 across charts) so a count floor is the wrong instrument | registry; `asset_throughput` measured | **NOW** — re-baseline + add `integrity_check_sql` (catalog resolvability, non-empty `constituent_fact_ids`) | §N.4; §N.8 |
| F-D5 | ga_yoga | Non-total `ORDER BY strength DESC NULLS LAST, yoga_canonical_id` — `ayanamsha_id` absent, ties across 5 ayanamshas | `get_yoga_firings.ts:187` | **NOW** — add `ayanamsha_id, id` to the sort key | §N.7 pt.2 |
| F-D6 | ga_yoga | Firings are labelable `sruti`(chapter-level)/`yukti`/`pratyaksa` today from existing data; no `grounding_tier` exists | 241/254 catalog citations resolve to real corpus text_ids (measured); `constituent_bala_v1` self-declared "not a classical formula" | **NOW** — add `grounding_tier`, chapter-level `sruti` only | D-GROUNDING |
| F-D7 | ga_yoga | Verse-level grounding is not available: `brahma_yoga_source_chunks` exists with **0 rows**; `source_chunk_ids` non-empty on **0/233** catalog rows | measured | **NEVER/LATER** — L0-owned ("chunk citation keys", plan §5 L0) | D-GROUNDING; plan §5 L0 |
| F-D8 | ga_yoga | 12 catalog citations use `text_id='jaimini_sutram'` (0 corpus chunks; corpus has `bphs_jaimini`, 264) + 1 `classical_tradition` (not a text) — 13/254 unresolvable, incl. the live-firing `jaimini_karakamsha_moon` | measured resolvability join | **NEVER/LATER** — L0 corpus/alias question; record, do not fix at L1 | D-GROUNDING (no fabricated citation) |
| F-D9 | ga_vichara | `catalog_status=DRAFT` on an asset with 8,249 exact rows, 3 L2 production consumers, 9 live MSR signals citing it, and the batch's best §N.6 serving surface. Only DRAFT in the layer (1 of 19) | measured counts + reconciliation; `bo_laksana.py:1031` ("SHIPPED 2026-07-14 and is live"); cockpit reads it at `registry/route.ts:36,68`, `PlanModal.tsx:207` | **MUST** — flip to CURRENT | D-SERVICE (built-but-unplugged is a defect class; the inverse mislabel is the same truth defect) |
| F-D10 | ga_vichara | `target_floor=0` (unset) despite 8,249 achieved and an exactly-reconciling volume model | 5×(1595+35+9+9)+9 = 8,249, measured | **NOW** — set to 8,249 with the model in `volume_explanation` | §N.4 |
| F-D11 | ga_vichara | Non-total `ORDER BY vichara_family, domain NULLS FIRST, subject` over 8,249 rows with LIMIT/OFFSET (1,595 valence_pass rows/ayanamsha share the sort key) | `get_vichara.ts` rowsSql | **NOW** — add `ayanamsha_id, varga_id, id` | §N.7 pt.2 |
| F-D12 | ga_vichara, ga_sade_sati | `estimated_seconds` stale by ~20× / ~8×. Both jumped at the same date boundary (2026-07-27 → 2026-08-06) with unchanged row counts — looks environmental, cause not determinable read-only | `build_run_assets`: vichara 17–31s → 619–805s; sade_sati 27–31s → 510–558s | **NOW** — re-baseline estimates; flag the shared jump for W4 scheduling; investigate cause separately | plan §4 rubric 7; §3.2 delta-skip |
| F-D13 | ga_vichara | `varga_ratification_divergence` present for only 3 of 5 ayanamshas (9 rows total); served with no note distinguishing "no divergence" from "not computed" | measured breakdown | **NEVER/LATER** — add an `empty_reason`-style note if cheap | §N.7 pt.6 (honest null) |
| F-D14 | ga_sade_sati | **−4,732 (−43%) ruled: stale floor achieved by a since-proven-defective writer, not a regression.** 6,287 = 5×(240×4+299) − 8 reconciles exactly; N=4 cycles is the astronomically correct post-birth count; the delta is attributable to PR #522 (retrograde-shadow dedup + pre-birth clip) plus two honesty passes | full derivation in Special Assignment 1; `R6_RUN_LEDGER_v1_0.md:253,579-586`; measured cycle boundaries | **MUST** — re-baseline 11,019 → 6,287 **with** the model recorded, and prefer invariant `integrity_check_sql` over a count floor | §N.4; charter C12; DVA Ruling 16 |
| F-D15 | ga_sade_sati | 2 over-declared dependencies: `ga_strength` (zero shadbala reads in the writer) and `ga_panchanga` (code import of the transit engine, not a data edge) | grep of `ga_sade_sati_writer.py`; `_verify_upstream_rows:1435-1483` gates only GA3/4/6/7/8 | **NOW** — drop or re-declare; inflates the DAG and delays the asset behind non-consumed upstreams | §I B.3 |
| F-D16 | ga_sade_sati | `target_table = NULL` while rows live in `chart_facts` | registry | **NOW** — set, or record why NULL is right for a fact-family asset | D-SERVICE (cockpit truth) |
| F-D17 | ga_sade_sati | The 15-category list is hand-maintained in two places (`asset_registry.count_sql` and `get_sade_sati.ts:15-21`). They agree today. `fact_category_ownership` has **0 rows for all four batch-D assets** | measured both; `ga_structural`'s twice-drifted precedent (BA audit ENHANCEMENT 4) | **NOW** — populate `fact_category_ownership` for these assets and derive both lists from it | §N.4 cockpit truth; D-SERVICE |
| F-D18 | ga_sade_sati | No `density_contract` on `get_sade_sati.ts` despite implementing the substance (window filter, disclosed drop counts, `drill_uri`) | `get_sade_sati.ts` | **NOW** — declare it; behavior already qualifies | §N.6 pt.4 |
| F-D19 | ga_sade_sati | see F-D12 | | | |
| F-D20 | ga_sade_sati | `all:true` path applies LIMIT/OFFSET to a non-total `ORDER BY fact_category, ayanamsha_id, fact_key` (`fact_subject` absent) | `get_sade_sati.ts:97` | **NOW** — add `fact_subject, fact_id` | §N.7 pt.2 |
| F-D21 | ga_transit_anchors | The acharya-floor vidhi primitive `from_moon_view` dispatches `ganita_chart_facts_get` with `reference_point:'moon'` — **an argument no tool reads anywhere** (2 repo hits, both the registry rows themselves) — while this asset already stores `natal_house_from_moon` for 9 grahas × 5 ayanamshas | `bg_vidhi_primitives.py:78`; `registry_data.ts:86`; measured anchor rows | **MUST** — re-point the primitive at `ganita_transit_anchors_get`, or implement `reference_point`; a silently-dropped filter is CR-42-class | plan §4 rubric 3 (leverage); D-SERVICE; §N.6 |
| F-D22 | ga_transit_anchors | The writer's FORENSIC assertion demands `moon natal_sign == 'aquarius'` per ayanamsha, but the live `surya_siddhanta_classical` row correctly stores `pisces` (a real AQ/PI boundary divergence). Either the assertion is not reached for that substep or the rows predate it — **unresolved read-only** | `ga_transit_anchors.py:135-144`; measured anchors + `graha_position` MOON per ayanamsha | **MUST** — resolve; a FORENSIC guard that cannot fire, or fires wrongly, is either dead or a live build hazard | §N.8 (a signal needs a detector that measures the claim) |
| F-D23 | ga_transit_anchors | **Zero data-plane consumers.** Only readers are its own writer and its own MCP capability; no L2–L5 writer reads the table. Meanwhile `register_d9_judgment.ts:780-807` independently re-derives the chandra frame at serve time | repo-wide grep grouped by file; measured | **NOW** — WIRE (via F-D21) or record an explicit disposition; do not retire silently | D-SERVICE (built-but-unplugged is a named defect class) |
| F-D24 | ga_transit_anchors | Missing-graha rows are skipped with a warning and a short count; no `integrity_check_sql` asserts 9 grahas × 5 ayanamshas. The floor is the only backstop and floors are aspirational | `ga_transit_anchors.py:170-181`; `integrity_check_sql=NULL` (all 19 L1 assets) | **NOW** — add the 9×5 completeness check (cheapest integrity check in L1) | §N.8; §N.4 |
| F-D25 | ga_transit_anchors | `get_transit_anchors.ts` has no `density_contract`, no `empty_reason`, and `grounds_to.l1_fact_ids:false` — serves derived values with no drill back to the `chart_facts` rows they were built from | `get_transit_anchors.ts` | **NOW** — add all three; the writer already reads specific facts | §N.6; D-SERVICE (≤2 hops to L1) |
| F-D26 | AV transit gating (cross-asset) | The D-TIME "AV transit gating" feed is **not** an L1 stored asset: the gating half is `ga_strength` facts (`ashtakavarga_bindu_sign` 480 / `ashtakavarga_kakshya_boundary` 120, measured); the dated `kakshya_windows` half is computed at serve time from L0 `ephemeris_daily` via a Lahiri mean-rate approximation, covered by **no** `count_sql`, floor, or staleness signal | `register_p1_aliases.ts:995`; `get_av_transit_gating.ts:6-8,19-31`; measured category counts | **NOW** — record the split in the W2 ledger; the serving-plane half lands in W3 (no freeze exception needed) | D-TIME items 1–2; O-wave WP-1 (one staleness authority) |
| F-D27 | ga_sade_sati + ga_transit_anchors | **Explicit D-TIME duplication with no arbiter.** Both make Saturn-vs-natal-Moon claims; both correctly honor the real AQ/PI ayanamsha divergence (Moon = Aquarius ×4, Pisces under surya_siddhanta), producing Sāḍe-sātī windows that differ by ~3y2m at cycle start (lahiri `2020-01-24→2027-06-02` vs surya `2022-04-29→2029-08-08`). No arbiter surface, no stored adjudication profile, no disclosure on either serving surface | measured cycle boundaries + anchor houses; `ga_sade_sati_writer.py:2093`; `register_d9_judgment.ts:794-805` (the disclosure machinery that exists one layer up) | **NOW** — declare each asset's question in the registry; disclose frame sensitivity on both L1 surfaces rather than picking an ayanamsha | D-TIME items 1/2/4; D-SYNTHESIS (singular voice = one declared frame) |
| F-D28 | all four | `integrity_check_sql = NULL` on all four (and on all 19 L1 assets). Given F-D4/F-D14/F-D24, invariant checks are a better instrument than count floors for three of the four | measured | **NOW** — propose per-asset integrity SQL in W2 (R0-T01 Conform-stage work is reusable) | §N.8; plan §5 L0 ("per-asset integrity checks where W2 accepts proposals") |
| F-D29 | ga_yoga (housekeeping) | `BA_AUDIT_FIX_PLAN_v1_0.md` MINOR item 5 ("strength/is_partial/bhanga_active NULL/false for 100% of firings") is **stale** — `strength` is populated on 63/63 rows | measured | **NEVER/LATER** — close the backlog item on this evidence | ONGOING_HYGIENE_POLICIES (staleness register) |

## Triage roll-up

- **MUST (6):** F-D1, F-D2, F-D9, F-D14, F-D21, F-D22.
- **NOW (18):** F-D3, F-D4, F-D5, F-D6, F-D10, F-D11, F-D12, F-D15, F-D16, F-D17, F-D18, F-D20,
  F-D23, F-D24, F-D25, F-D26, F-D27, F-D28.
- **NEVER/LATER (4):** F-D7, F-D8, F-D13, F-D29.

## Route recommendations for W2

| asset | recommended route | reason |
|---|---|---|
| `ga_yoga` | `changed` | F-D1/F-D2 need code (catalog citation projection + offset); rebuild follows |
| `ga_vichara` | `rebuild_only` | data is correct and reconciles exactly; all findings are registry/serving metadata |
| `ga_sade_sati` | `rebuild_only` | current data is the *correct* data; the floor is what is wrong |
| `ga_transit_anchors` | `changed` | F-D21/F-D22 need code (consumer re-point + assertion resolution) |

## Explicit uncertainties (not resolved read-only)

1. The exact decomposition of `ga_sade_sati`'s ~3,530 non-birth-clip rows between the retrograde
   dedup and the two honesty/conditional-emission passes. Requires executing the pre-#522 writer.
2. Why `ga_vichara` and `ga_sade_sati` both slowed ~8–22× between 2026-07-27 and 2026-08-06 with
   unchanged row counts.
3. Whether `ga_transit_anchors`' FORENSIC Moon assertion can actually fire on the
   surya_siddhanta substep (F-D22).
4. Whether `ga_yoga`'s declared `ga_dashas` edge is real in code (the `activation_dasha_periods`
   column exists; the read path was not traced this pass).
5. Whether the 12 `jaimini_sutram` citations are an alias gap against `bphs_jaimini` or a genuine
   corpus gap.
