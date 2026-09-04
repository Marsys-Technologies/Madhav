---
artifact: L4_W1_ANALYSIS_BATCH_B.md
canonical_id: NIRMANA_V21_L4_W1_BATCH_B
version: "1.0"
status: CURRENT
campaign_id: nirmana-elevation
session: L4
wave: W1 ANALYZE
assets: ph_muhurta, ph_sankrama (the L4 timing surfaces)
produced_on: 2026-09-05
method: read-only subagent analysis against live production; worktree at origin/main 20323fae4
---

# L4 W1 ANALYZE — BATCH B — `ph_muhurta` · `ph_sankrama`

**VERIFIED** = query run / line read. **INFERRED** = reasoned, not executed.

---

## PART A — `ph_muhurta`

### A1. Instrument fit

| Doctrine | Verdict | Evidence |
|---|---|---|
| **D-GROUNDING** | **FAIL — sruti label over yukti arithmetic** | 117/134 rows (87%) carry the Python string literal `'Muhūrta-Chintāmaṇi + Grahalaghava'` hardcoded at `ph_muhurta.py:149-150`; only 17 (`marriage`) got a real `brahma_activity_ontology.citations[0]`. The scored quantity is `panchanga × personalization × (tara×chandra)^0.5 × (1−penalty)` (`services/ph_muhurta/engine.py:79-89`) — a project-invented arithmetic no Muhūrta-Chintāmaṇi chapter states. Honest tier = **`yukti`**. The only genuinely `sruti` artifact is `_TARABALA_WEIGHTS` (`engine.py:56`) and it is **inert** (F-1). |
| **D-SYNTHESIS** | **FAIL** | `window_quality_verdict` is a singular verdict voice — but it is a **constant** (F-1). |
| **D-SALIENCE** | **FAIL** | No chart-intrinsic salience term stored. `composite_quality` is the only ranking key and its ceiling is structurally 0.375 on this chart. No `tail_watch`, no hard floor; the serving `LIMIT 100` (`query_phala_calibration.ts:96`) trims below the actual 134. |
| **D-TIME** | **FAIL — the seam** | No declared question (`provides_apis` NULL); no arbiter; duplicates a second live engine. See Part C. |
| **D-SERVICE** | **FAIL** | Consumer exists but declares no `density_contract`, no empty-reasons, and drops every honesty column (A3). |

**Still the right instrument?** As a *concept* yes — "which of MY predicted anchor windows are
actionable" is a real question nothing else answers. As *built* it is not an election engine; it is a
one-row-per-anchor annotation of `phala_anchors` that never iterates candidate slots
(`ph_muhurta.py:110-113` says so: *"full engine would iterate candidate timestamptz slots; we emit
one per anchor"*). `_WINDOW_DAYS = 365*3` (`:41`) is declared and never read — dead constant.

### A2. Real vs declared dependencies

Declared: `[ph_nimitta, ka_kalasutra, ga_panchanga, ka_vighnakara, ga_condition, ka_gochara, ga_positions, ka_sangam]`.

| Declared | Actually read? | Evidence |
|---|---|---|
| `ph_nimitta` | ✅ `phala_anchors` | `ph_muhurta.py:239-244` |
| `ka_vighnakara` | ✅ `kala_obstruction` | `:278-284` |
| `ka_sangam` | ✅ `kala_convergence` (JOIN, supplies the dates) | `:280-281` |
| `ga_condition` | ✅ `ga_condition_composite` | `:311-317` |
| `ka_gochara` | ❌ **NEVER** — `_load_gochara_transits` returns `{}` unconditionally | `:352-358` |
| `ka_kalasutra` | ❌ never — no `kala_activation` query in the file | grep |
| `ga_panchanga` | ❌ never — panchanga is a **proxy**: `panchanga_score = min(1.0, condition*0.8 + 0.2)` | `:134` |
| `ga_positions` | ❌ never — no `chart_positions` query | grep |

**Read but NOT declared:** `chart_facts` (L1) ×4 — `:452, :518, :577, :614`;
`brahma_activity_ontology` (L0) — `:479-482`; `panchang_engine` live ephemeris — `:665-671` (an
out-of-DAG runtime dependency).

**4 of 8 declared deps are fiction.** `estimated_seconds=1` reflects the real (tiny) work, not the
declared graph.

### A3. Leverage

Full-column NULL census, canonical chart (n=134): no all-NULL column
(`overlapping_obstruction_id` 37/134 and `fructification_anchor` 17/134 are the only partials).

**Populated at build, DROPPED at serve** (`query_phala_calibration.ts:86-93` SELECT list):
`panchanga_snapshot_jsonb`, `tarabala_chandrabala_jsonb`, `significators_met_jsonb`,
`fructification_anchor`, `follow_up_hook_jsonb`, `derivation_ledger_jsonb`, `source_citation`,
`personalization_graha`, `overlapping_obstruction_id`.

**The most load-bearing one is `tarabala_chandrabala_jsonb`** — it carries the honesty label
`source: 'placeholder_no_ephemeris'` on 100% of rows, both charts. **The build layer is honest; the
serving layer strips the honesty and ships a bare `composite_quality`.** §N.7 items 4/6 broken at the
seam, not in the writer.

**Upstream populated, never read:** `kala_gochara_windows` holds **17,240 rows** for the canonical
chart. `ph_muhurta.py:334-358` asserts in a long docstring that *"there is NO `kala_gochara` table…
ka_gochara is a compute-only L3 service (asset_kind='service', no persistence)"*. **That is now
false**: `asset_registry` shows `ka_gochara` with `asset_kind='data'`, `catalog_status='CURRENT'`,
`count_sql = SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='3.0'`. The
docstring is a stale correctness note that has become a stale-fact note — and it is the
*justification* for a hardcoded `0.5`.

### A4. Grounding labelability

- `classical_citation` — 87% a literal fallback (A1).
- `source_citation` (NOT NULL) — satisfied with a **row identifier**, not a citation:
  `f"ph_muhurta/{action_class}/{start_str}"` (`engine.py:236`).
- `derivation_ledger_jsonb` — 14 keys (verified via `jsonb_object_keys`): `action_class,
  adversity_penalty, chandrabala_score, chart_personalization, composite_formula, condition_score,
  fructification_rules, linked_anchor_id, obstruction_id, panchanga_score, personalization_graha,
  tarabala_chandrabala_source, tarabala_score, transit_score`. **Zero `fact_id` keys.** It records
  *values*, not *references*.
- The capability nevertheless declares `grounds_to: { l1_fact_ids: true }`
  (`query_phala_calibration.ts:55`). **Unearned** — no code path can produce an L1 fact_id from this
  table. §N.5 + §N.8.

Honest tier per output class: `panchanga_score` → **yukti** (proxy, not panchanga);
`tarabala/chandrabala` → **null** (placeholder); `composite_quality` → **yukti**;
`window_quality_verdict` → **null** (no live detector, F-1); `classical_citation` →
**sruti-labelled, yukti-earned**.

### A7. Measured cost

`asset_throughput` both charts: `rows_per_second` NULL, `measurement_count` 0, `history` `[]`,
`expected_rows` NULL. **`estimated_seconds = 1` has no measurement behind it** — a §N.8 unearned cost
signal. Indexes adequate: `phala_muhurta_chart_idx` btree(chart_id); `phala_muhurta_natural_key`
UNIQUE(chart_id, action_class, window_start).

### A8. Volume derivation (C12)

**Natural key:** `(chart_id, action_class, window_start)` — UNIQUE `phala_muhurta_natural_key`.
**Rows-per-what:** one attempted row per influenceable/semi_influenceable `phala_anchors` row, mapped
`domain → action_class` via the 7-entry `_DOMAIN_TO_ACTION` (`ph_muhurta.py:686-694`), then
**collapsed by the natural key**.

| chart | influenceable anchors | distinct natural keys | table count | `rows_written` |
|---|---|---|---|---|
| canonical `482012f1` | 139 | **134** | **134** | **139** ❌ |
| Abhinandan `1c826d5a` | 56 | (49) | **49** | **56** ❌ |

**Delta attributed, named cause:** the writer increments `rows_inserted += 1` (`:226`)
**unconditionally after an `ON CONFLICT DO NOTHING`** (`:202`). Every natural-key collision is a
silently discarded row reported as inserted — canonical over-reports by exactly 5, Abhinandan by
exactly 7. Root cause of the collisions: only 5 distinct `action_class` values are reachable from 7
anchor domains, and `_to_datetime` normalizes every `date` to **06:00 the same day** (`:703`), so two
anchors in the same domain with the same start date are one key.

**Honest proposal (no equality pin):**

```
expected_volume_formula:
  count(phala_muhurta WHERE chart_id=$1)
    = (SELECT count(DISTINCT (map_domain_to_action(domain), coalesce(window_start, peak_date)))
       FROM phala_anchors
       WHERE chart_id=$1 AND malleability IN ('influenceable','semi_influenceable'))
  AND count(*) <= LEAST(400, influenceable_anchor_count)
expected_volume_inputs:
  influenceable_anchor_count : SELECT count(*) FROM phala_anchors WHERE chart_id=$1
                               AND malleability IN ('influenceable','semi_influenceable')
  max_muhurta_anchors        : 400   -- MAX_MUHURTA_ANCHORS, ph_muhurta.py:44
  action_class_cardinality   : 7     -- |_DOMAIN_TO_ACTION|
```

**Real invariants** (each returns 0 offending rows on health):
1. **FK resolution + malleability**: every `linked_anchor_id` FULL-JOINs to a `phala_anchors` row of
   the *same* chart with `malleability IN ('influenceable','semi_influenceable')`.
2. **No silent drop**: every influenceable anchor's `(mapped_action, normalized_start)` key appears in
   `phala_muhurta`; any absent key must be a *duplicate* key, never a *missing* one.
3. **Ordering**: `window_start <= window_end` on every row.
4. **Fingerprint distinctness**: `count(DISTINCT source_citation) = count(*)` (VERIFIED 134/134).
5. **Vocabulary closure**: `action_class` ∈ image of `_DOMAIN_TO_ACTION` ∪ `{'new_venture'}`.
6. **Verdict liveness (the §N.8 one)**: `count(DISTINCT window_quality_verdict) > 1` **OR** an
   explicit stored `verdict_ceiling_reason` naming why not.

---

## PART B — `ph_sankrama`

### B1. Instrument fit

| Doctrine | Verdict | Evidence |
|---|---|---|
| **D-GROUNDING** | **PASS-with-gap** | `confidence_basis = 'structural_not_yet_empirical'` on 100% of rows — an *honest* label, exactly the §N.7-item-6 behaviour we want. But `source_citation` is again a row-identifier path (`engine.py:277`), and `derivation_ledger_jsonb` has 8 keys, **zero fact_ids**. Honest tier = **`yukti`** (CDLM linkage + activation-window intersection). No sruti claimed — correct. |
| **D-SYNTHESIS** | **FAIL** | `trajectory` is a 3-way voice with 2 dead branches (B5). |
| **D-SALIENCE** | **FAIL** | `linkage_strength` inherited verbatim from L2 — no chart-intrinsic salience term of its own. `spillover_confidence = min(0.80, source_conf × linkage)` is a **clamp**, not a salience. No hard floor; the consumer has **no LIMIT at all**. |
| **D-TIME** | **PARTIAL** | It genuinely derives its window by *intersection with real activation windows*, not a formula (`engine.py:83-130`) — the strongest D-TIME behaviour of the two. But it declares no question and feeds no arbiter. |
| **D-SERVICE** | **FAIL** | Consumer returns all 2,510 rows unbounded, no `density_contract`, no empty-reason, reads a 100%-NULL column. |

### B2. Real vs declared dependencies

`depends_on = [ph_nimitta, bo_sangati]`. **Both real:**
- `ph_nimitta` → `phala_anchors`, `ph_sankrama.py:161-168` (**no malleability filter, no LIMIT** —
  reads ALL anchors, unlike `ph_muhurta`).
- `bo_sangati` → `bodha_cdlm_cells`, `ph_sankrama.py:175-184`.

**Nothing read-but-undeclared. Nothing declared-but-unread. `ph_sankrama`'s dependency declaration is
the only clean one of the two.**

### B3. Leverage

Census (n=2510): `mitigation_ref` **0/2510**; `cascade_chain` 2195/2510; everything else 2510.
Distinct values: `source_domain` 5 · `target_domain` 11 · `relationship_type` 2 · **`trajectory` 1** ·
**`cascade_depth` 1** · `confidence_basis` 1 · `falsifier` 459 · `source_citation` 2510.

- **`mitigation_ref` is 100% NULL on both charts** and is **SELECTed and served**
  (`query_phala_calibration.ts:168`). The field comment says `# set post-facto by writer`
  (`engine.py:76`) — **no writer ever sets it.** Read-but-NULL, and the capability description
  advertises *"mitigation routing"* (`:126`) as a feature. §N.8: no code path could make it non-null.
- **Populated-but-unread:** `bridge_path_jsonb` (2510), `cascade_chain_jsonb` (2195),
  `derivation_ledger_jsonb` (2510), `source_citation` — none in the serving SELECT. The *actual
  mechanism evidence* is computed and never served; the caller gets `mechanism_text`, a string.
- **Served-but-constant:** `cascade_depth` (always 1), `trajectory` (always `'stable'`),
  `confidence_basis` (always one value).

### B4. Grounding

`falsifier` is genuinely good: 459 distinct, machine-shaped, names both REFUTED and CONFIRMED
conditions with a real deadline (`engine.py:176-190`). **The strongest artifact either asset produces.**

### B5. `trajectory` — a 3-way branch that is a constant

`_trajectory(evolution_gradient)` (`engine.py:135-141`) branches on `>0.1 / <-0.1 / else`. It is fed
`float(r.get('cell_evolution_gradient_score') or 0.0)` (`ph_sankrama.py:212`). Live:
`min(cell_evolution_gradient_score)` and `max(...)` are **both NULL** on both charts (280 and 75
cells). **The upstream L2 column is 100% NULL.** `or 0.0` converts "I don't know" into "flat", and
`'stable'` — a *favourable-sounding* judgment — is emitted for every one of 2,985 rows across both
charts. Precisely §N.7 item 6's named defect, one layer over.

`cascade_depth` is the same class one step further: `derive_cascade_chain` is documented *"chain up to
`_MAX_CASCADE_DEPTH`(=3) hops"* but **never recurses** — called once with `depth=0`
(`engine.py:249-251`), returns `{'depth': depth+1}` = always 1. `cascade_depth = cascade['depth'] if
cascade else 1` (`:271`) — **1 on both branches**. The CHECK constraint permits 1..3; only 1 is
reachable. `next_cells` (`:151`) is assigned from key `(target_domain, '')` which cannot exist and is
never used. `source_confidence` is a parameter `derive_cascade_chain` never reads. The registry
description leads with *"Grounded **multi-hop** cross-domain dynamics… **A→B→C cascades**"* —
verified unreachable.

### B7. Measured cost

`rows_per_second` NULL, `measurement_count` 0, `history` `[]`, `expected_rows` NULL, both charts.
`estimated_seconds = 5` unearned. Indexes: `phala_sankrama_chart_idx` + `phala_sankrama_source_anchor_idx`
— adequate for `count_sql`; the **unbounded** serving query returns 2,510 rows through the chart
index, so the cost is serialization, not scan.

### B8. Volume derivation (C12) — **exact, from first principles**

**Natural key:** `(chart_id, source_anchor_id, cdlm_cell_id, target_domain, relationship_type)`.
Because `cdlm_cell_id` functionally determines both `domain_col` (=target) and
`contradicting_pairs_count` (→relationship_type), the key **collapses to `(chart_id, anchor, cell)`**
— collisions are impossible, which is why this asset's `rows_written` is honest while
`ph_muhurta`'s is not.

```
rows = Σ_over_anchor_domains d [ anchors(d) × cells(domain_row = map(d), net_linkage_strength ≥ 0.25) ]
```

Live cross-check, canonical:

| anchor domain | anchors | matching cells | expected | actual |
|---|---:|---:|---:|---:|
| career | 29 | 55 | 1595 | **1595** |
| character | 5 | 45 | 225 | **225** |
| health | 5 | 30 | 150 | **150** |
| relationship | 18 | 25 | 450 | **450** |
| spirituality | 6 | 15 | 90 | **90** |
| **transition** | **50** | **5** | **250** | **0** ⚠ |
| **wealth** | **26** | **0** | **0** | **0** ⚠ |
| | | | **Σ = 2510** | **2510 ✓** |

Abhinandan, same formula: 225+80+60+40+70 = **475** = actual **475 ✓**.

**The formula is exact on both charts. The two ⚠ rows are the finding.**

- **`transition` — 250 rows (10% of the asset) actively destroyed by a stale mapping.**
  `_ANCHOR_TO_CDLM_DOMAIN['transition'] = 'general'` (`ph_sankrama.py:33`). `bodha_cdlm_cells.domain_row`
  for this chart is `{career, character, education, family, health, progeny, relationship, residence,
  spirituality, transition, travel}` — there is **no `general`**, and there **is** a `transition`
  (5 cells) that would have matched exactly. The map's own comment claims CDLM's vocabulary is
  *"career, relationship, wealth, spirituality, health, general, character"* — **wrong on 4 of 7
  terms.** The map was written against `ph_nimitta`'s old vocabulary; `phala_anchors.domain` now
  already stores CDLM-native terms, so three map entries are dead and the one live entry is the one
  that breaks a working match.
- **`wealth` — 26 anchors, 0 cells.** `bodha_cdlm_cells` has no `wealth` domain_row at all; the L2
  CDLM vocabulary and the L4 anchor vocabulary genuinely diverge here. This is an honest empty, not a
  bug — but nothing records it, and `query_spillover_cascades` returns `count: 0` for
  `source_domain='wealth'` with no empty-reason.

**Honest proposal:**

```
expected_volume_formula:
  count(phala_sankrama WHERE chart_id=$1)
    = (SELECT coalesce(sum(a.n * c.k),0)
       FROM (SELECT domain, count(*) n FROM phala_anchors WHERE chart_id=$1 GROUP BY 1) a
       JOIN (SELECT domain_row, count(*) k FROM bodha_cdlm_cells
             WHERE chart_id=$1 AND net_linkage_strength >= 0.25 GROUP BY 1) c
         ON c.domain_row = map_anchor_domain_to_cdlm(a.domain))
expected_volume_inputs:
  anchor_count_by_domain      : phala_anchors GROUP BY domain (chart-scoped)
  material_cell_count_by_row  : bodha_cdlm_cells WHERE net_linkage_strength >= 0.25 GROUP BY domain_row
  linkage_threshold           : 0.25   -- _LINKAGE_THRESHOLD, ph_sankrama.py:26 AND engine.py:27 (DUPLICATED, F-11)
```

**Real invariants:**
1. **Tiling, no gaps/overlaps**: `(source_anchor_id, cdlm_cell_id)` appears exactly once; and every
   (anchor, material-cell-of-its-mapped-domain) pair appears — a FULL JOIN against the two upstream
   tables returning 0 unmatched rows on either side. *This one invariant catches the entire
   transition→general loss.*
2. **§N.5 drift check (the important one)**: `phala_sankrama.linkage_strength =
   bodha_cdlm_cells.net_linkage_strength` and `phala_sankrama.target_domain =
   bodha_cdlm_cells.domain_col` for the joined `cdlm_cell_id`, same `chart_id`. **L4 must not have
   drifted from the L2 value it copied.**
3. **Vocabulary closure**: every `source_domain` ∈ `bodha_cdlm_cells.domain_row` for this chart —
   **fails today for `general`, which is the point.**
4. **Window containment**: `projected_window_start <= projected_window_end` and
   `[projected_start, projected_end] ⊆ [source_start, source_end]`.
5. **Fingerprint distinctness**: `count(DISTINCT source_citation) = count(*)` (VERIFIED 2510/2510).
6. **Liveness (§N.8)**: `count(DISTINCT trajectory) > 1` OR a stored reason naming
   `cell_evolution_gradient_score IS NULL` as the cause.

---

## PART C — D-TIME: the L3/L4 election seam (the cross-asset finding)

### C1. Overlap map

Four live surfaces answer election-adjacent temporal questions, and **none declares its question or
arbitrates against any other.**

| # | Surface | Question it actually answers | Substrate | Mode |
|---|---|---|---|---|
| 1 | `ph_muhurta` → `phala_muhurta` → `query_auspicious_windows` | "Which of MY 139 predicted anchor windows score well?" | build-time table, 134 rows | persisted |
| 2 | `brahmagyan/phala/muhurta.py` (asset **PH-4-4**) → `muhurta_finder.ts` → `kala_muhurta_get` (deprecated alias) / `kala_elect_get` (elevated facade) | "Given an undertaking and an arbitrary date range, rank act-times." 48h windows, `panchanga 40% + dasha 30% + transit 20% + activation 10%` | live compute over `panchanga_daily` / `chart_dashas` / `ephemeris_daily` / `bg_transit_rules` | live |
| 3 | `gochara_election_avoidance_get` | "Which windows should I AVOID?" | `kala_gochara_windows` (**17,240 rows**) | persisted |
| 4 | `ka_vighnakara` → `kala_obstruction` | "Which convergence windows are obstructed?" | persisted | persisted |

**Both #1 and #2 are L4 Phala assets carrying L3 Kāla tool names.** `kala_elect_get` is documented as
*"a THIN FACADE over the EXISTING muhūrta substrate: `handleMuhurtaFinder`… **asset PH-4-4**"*
(`platform-mcp/src/tools/kala_views/elect.ts:6-8`) and declares itself *"the **SOLE** server of Mode 3
(ACTIVITY ELECTION)"* (`:15-17`). **It has never heard of `phala_muhurta`** — verified:
`grep -c phala_ .../kala_views/elect.ts` → 0; `grep -c phala_muhurta .../muhurta_finder.ts` → 0.

### C2. The one place they touch — and it is dead code

`brahmagyan/phala/muhurta.py:1112-1129` reads `phala_muhurta` as a *"pre-computed cache"*, selecting
`action_type`, `auspiciousness_score`, `factors`. Live schema check:

```sql
SELECT count(*) FROM information_schema.columns
WHERE table_name='phala_muhurta' AND column_name IN ('action_type','auspiciousness_score','factors');
→ 0
```

**None of those three columns exists.** The real columns are `action_class`, `composite_quality`,
`panchanga_snapshot_jsonb`. This query raises `UndefinedColumn` on **every** call, is swallowed by
`except Exception` (`:1156`), logs a DEBUG-grade warning, and falls through to on-the-fly compute. The
envelope's `source` field is documented as `"phala_muhurta" | "on_the_fly"` (`:1109`) — **the
`"phala_muhurta"` branch is unreachable.** §N.8 in its purest form: a provenance signal whose
"cache hit" branch no code path can reach, and whose "miss" reads identically whether there were no
rows or the schema was wrong.

**Consequence for the campaign:** the build-time asset `ph_muhurta` spends its budget producing is
consulted by exactly zero live callers on the election path. `query_auspicious_windows` is its only
real reader.

### C3. Arbiter — there is none

```
grep -rn "partially_aligned|adjudicated_by|temporal_concordance|concordance_verdict"
  platform-mcp/src platform/src platform/python-sidecar   →  0 matches
tables LIKE '%concord%' / '%arbit%' / '%adjudic%'
  →  concordance_ayanamsha_flags (L1 ayanamsha), mimamsa_adjudication_log (L5)
```

**No (domain, range) temporal arbiter exists anywhere.** No `aligned | partially_aligned | disputed`
vocabulary. No adjudication profile is stored data. No cross-engine agreement feeds salience. D-TIME's
Temporal Concordance Contract is **0% implemented for the election domain**, and the two engines can
disagree freely and silently — `kala_elect_get` scoring a window gold while `query_auspicious_windows`
calls the same chart's every window `mediocre` produces two verdict voices with no drill pointer
between them (a D-SYNTHESIS violation as well).

### C4. Question declaration

`asset_registry.provides_apis` is **NULL for both `ph_muhurta` and `ph_sankrama`**, and NULL for
`ka_gochara`, `ka_sangam`, `ka_vighnakara`, `ka_kalasutra`, `ph_nimitta`, `ph_pramana` — the entire
temporal fleet. `english_description` is prose, not a question declaration, and both L4 descriptions
overstate what is built.

### C5. Service surface, both assets

`query_auspicious_windows` / `query_spillover_cascades`
(`platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`):

- **No `density_contract`.** The only L4_phala capability that declares one is
  `query_prospective_ledger.ts:143`.
- **No empty-reasons.** A `wealth` filter returns `count: 0` with nothing said.
- **Row-count claims in the descriptions are wrong by an order of magnitude**: *"phala_muhurta (100
  rows)"* — actual 134/49; *"phala_sankrama (73 rows)"* — actual **2510/475**. These strings
  propagate into `mcp_tool_registrations.generated.json`, `tool_search_index.generated.json`,
  `machine_census.generated.json` and `docs_resource_catalog.generated.json`, so the wrong number is
  what a planning LLM budgets against.
- `query_auspicious_windows` hard-`LIMIT 100` with `count: result.rows.length` — a caller reading
  `count: 100` believes it has all windows; **34 were silently trimmed**, no cursor, no truncation
  flag. §N.6 items 1/4.
- `query_spillover_cascades` has **no LIMIT at all** — 2,510 rows, ~20 columns, unbounded,
  `cost_class: 'cheap'`, `pre_fetch_priority: 25`, `cacheable: true`. The layer's largest asset
  shipped whole into a bulk-context pre-fetch.
- **≤2-hop drill to L1:** ✗ for both. Hop 1 lands on `phala_anchors` (good). Hop 2 needs an L1
  fact_id — neither ledger contains one, and neither ledger is served anyway.
  `grounds_to: { l1_fact_ids: true }` on both capabilities is unearned.
- **Second write path:** SQL function `seed_phala_muhurta_native_sample` still exists in production
  (`pg_proc` count 1), called at `muhurta.py:1702` — a non-orchestrator writer into `phala_muhurta`,
  outside the §N.3 delete-then-insert discipline.

---

## PART D — FINDINGS → W2

**F-1 · MUST · §N.8 + D-SYNTHESIS — `window_quality_verdict` is structurally incapable of reading
anything but `mediocre`.** `classify_verdict` (`engine.py:92-108`) needs `composite ≥ 0.55` for
`adequate`, `≥ 0.75` for `strong`. Because `tarabala = chandrabala = 0.5` on **100% of rows on both
charts** (`tarabala_chandrabala_jsonb->>'source' = 'placeholder_no_ephemeris'`, 134/134 and 49/49),
the geometric-mean factor is pinned at exactly 0.5, capping composite at 0.5 even if every other term
were 1.0. Observed range 0.0808–0.2614; observed verdicts: `mediocre` ×134 and ×49. *What code path
would have to run AND FAIL for this to read `adequate`?* **None exists.** The CHECK admits 4 values;
1 is reachable.

**F-2 · MUST · §N.7 item 6 — `trajectory` is `'stable'` for all 2,985 rows because the L2 column it
reads is 100% NULL.** `bodha_cdlm_cells.cell_evolution_gradient_score` min/max both NULL over 280 and
75 cells. `ph_sankrama.py:212` does `float(… or 0.0)`, converting unknown→0.0; `_trajectory` returns
the neutral-sounding `'stable'`. Two of three branches dead. The honest value is NULL with a reason.

**F-3 · MUST · D-TIME — the `phala_muhurta` cache read in `brahmagyan/phala/muhurta.py:1112-1129`
queries three columns that do not exist; its `source: "phala_muhurta"` branch is unreachable.**
Swallowed at `:1156`, silently degrades to on-the-fly. This is the *only* wire between the two
election engines and it has been severed since the schema changed. The build-time asset serves zero
live election callers.

**F-4 · MUST · D-TIME — no arbiter exists for the election (domain, range).** Four surfaces (C1),
zero concordance vocabulary anywhere, zero arbiter tables (C3). `kala_elect_get` claims to be *"the
SOLE server of Mode 3"* while `query_auspicious_windows` independently serves the same question from a
different substrate with a different verdict scale. **The fix is not to merge them — it is to declare
each engine's question and stand up one arbiter emitting `aligned | partially_aligned(reasons) |
disputed(adjudicated_by, reasons)`.**

**F-5 · MUST · C12 — `ph_sankrama` silently destroys 250 rows (10%) via a stale domain map.**
`_ANCHOR_TO_CDLM_DOMAIN['transition'] = 'general'` (`ph_sankrama.py:33`); CDLM has no `general`
domain_row and *does* have `transition` with 5 material cells; 50 transition anchors × 5 = 250 rows
lost. The map's inline comment misstates CDLM's actual vocabulary on 4 of 7 terms.

**F-6 · MUST · §N.4 + C12 — `asset_throughput.rows_written` over-reports `ph_muhurta` by exactly the
natural-key collision count.** 139 reported / 134 stored; 56 / 49. Cause: unconditional
`rows_inserted += 1` (`:226`) after `ON CONFLICT DO NOTHING` (`:202`). **Set `target_floor` from
`count_sql`, never from `rows_written`.** (`ph_sankrama` has the same pattern at `:154`; latent there
because its natural key cannot collide.)

**F-7 · MUST · §N.5 + D-SERVICE — `grounds_to: { l1_fact_ids: true }` on both capabilities is
unearned.** `query_phala_calibration.ts:55` and `:135`. Neither table stores a fact_id; both ledger
key sets were enumerated live and contain none. Either populate `constituent_facts_array`-style
references, or set the flag false.

**F-8 · NOW · §N.6 + D-SERVICE — neither consumer declares a `density_contract` or an empty-reason;
`query_auspicious_windows` silently truncates and `query_spillover_cascades` is unbounded.** Sibling
`gochara_election_avoidance_get` already does this correctly (`ELECTION_AVOIDANCE_DENSITY_CONTRACT`,
`not_covered` refusals, per-row `calibration_state`, `register_gochara_windows.ts:2024`) — copy it.

**F-9 · NOW · D-GROUNDING — the serving layer strips the build layer's own honesty labels.**
`tarabala_chandrabala_jsonb` (with `source: 'placeholder_no_ephemeris'` and its explicit *"NOT a
computed score"* note, `engine.py:194-205`) is populated on every row and **not selected** by
`query_auspicious_windows`. The writer is honest; the reader is not. Same for `bridge_path_jsonb` and
`cascade_chain_jsonb` (2195 rows) on the sankrama side. **Fix at the SELECT list, not the writer.**

**F-10 · NOW · Registry truth — four wrong facts that propagate into 4 generated projection files.**
`ph_muhurta.depends_on` names 4 assets it never reads while omitting 3 it does; "100 rows"/"73 rows"
vs 134/2510; `ph_sankrama`'s description advertises multi-hop cascades and mitigation routing, both
unreachable; `provides_apis` NULL on the whole temporal fleet.

**F-11 · NOW · `mitigation_ref` is a documented feature with no writer.** 0/2510 on both charts;
`engine.py:76` says *"set post-facto by writer"*; no writer sets it; it is served and advertised.
Either wire `ph_pratikara` → `phala_sankrama.mitigation_ref` or drop the column and the claim.
(Also: `_LINKAGE_THRESHOLD = 0.25` is defined twice — `ph_sankrama.py:26` and `engine.py:27` — a
drift hazard on a number that appears in the volume formula.)

**F-12 · NOW · §N.8 — `estimated_seconds` (1 and 5) has no measurement behind it.** `rows_per_second`
NULL, `measurement_count` 0, `history` `[]`, `expected_rows` NULL for both assets on both charts.

**F-13 · NEVER-LATER · latent-only, do not fix blind: the engine ignores the writer's career-lord
override.** `ph_muhurta.py:91-95` computes `action_graha_overrides` from the chart's real 10th lord
and passes it as `hora_lord`; `engine.py:169` then recomputes `graha =
ACTION_GRAHA_MAP.get(action_class, 'saturn')` from the static map for `personalization_graha` **and**
for `significators_met.personalization_graha_match`. Both live charts have Aries lagna → 10th =
Capricorn → Saturn = the static default, so `hora_lord = personalization_graha` on 134/134 rows and
**the bug is currently masked**. It will fire on the first non-Aries chart. Record it; fix it when a
third chart lands, with a golden-value test per §N.7 item 5.

**F-14 · NEVER-LATER · record the disposition, don't build: `ph_muhurta` is not an election engine and
should stop claiming to be one.** It emits one row per anchor by its own admission (`:110-113`), never
iterates candidate slots, uses a `condition × 0.8 + 0.2` proxy for panchanga (`:134`), and hardcodes
transit at 0.5 while 17,240 real gochara windows sit unread. The *live* election engine (PH-4-4 /
`kala_elect_get`) already does all of that properly. **The honest disposition is to re-scope
`ph_muhurta` to what it uniquely does — "anchor-window actionability annotation" — rename its question
accordingly, and let `kala_elect_get` own election.** Building a second full election engine here
would be the duplication D-TIME exists to prevent. Fold in: `_WINDOW_DAYS` (`:41`) is dead;
`seed_phala_muhurta_native_sample` is a live non-orchestrator write path into the same table (§N.3).

---

## Two things NOT verified

- Neither writer was executed; all build-behaviour claims are read from source and confirmed against
  the resulting rows, not from a live run.
- Whether `bodha_cdlm_cells.cell_evolution_gradient_score` is NULL *by design* at L2 or is itself an
  unbuilt L2 column was not determined. F-2 stands either way ("the L4 consumer converts NULL to a
  favourable-sounding constant"), but the upstream disposition belongs to whoever owns `bo_sangati`.
