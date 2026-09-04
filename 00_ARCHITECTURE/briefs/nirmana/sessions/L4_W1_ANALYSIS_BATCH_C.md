---
artifact: L4_W1_ANALYSIS_BATCH_C.md
canonical_id: NIRMANA_V21_L4_W1_BATCH_C
version: "1.0"
status: CURRENT
campaign_id: nirmana-elevation
session: L4
wave: W1 ANALYZE
assets: ph_sodhana, ph_suddha_sodhana, ph_pratikara (purification + remedial chain)
produced_on: 2026-09-05
method: read-only subagent analysis against live production; worktree at origin/main 20323fae4
---

# L4 W1 ANALYZE — BATCH C — purification + remedial chain

`CANON` = `482012f1-…5871aa`, `ABH` = `1c826d5a-…40f75a`. All DB figures are live production reads.
Nothing was written.

---

## 0. Headline

1. **`ph_pratikara` ships 1,277 rows (536 CANON + 741 ABH) of *structurally empty* remedy
   programs — 100.0%, both charts.** `program_jsonb.total_scheduled = 0`, every
   `tradition_options_jsonb` bucket `[]`, every `recommended_tier_jsonb` bucket `[]`,
   `cross_tradition_corroboration = 0` on all rows. Root cause is a *known, already-code-fixed*
   defect (F-173, commit `5f097e738`, 2026-08-21) — the writer SELECTed six nonexistent columns and a
   `SAVEPOINT/except` swallowed the `UndefinedColumn`. **The fix landed in code; the rerun never
   ran.** Live data (`last_built_at` 2026-08-12/13) is entirely pre-fix.
2. **Every one of those rows carries a fabricated classical citation** — the hardcoded string
   `'Brihat Parashara Hora Shastra — Upaya chapter'` (`services/ph_pratikara/engine.py:257`),
   invented because no prescription was loaded. `phala_mitigation.classical_citation` is `NOT NULL`,
   so the invented string is structurally guaranteed. Downstream, `kala_upaya_diagnosis.ts:481`
   grades every one of those rows `efficacy_tier = 'classically_attested'` **on the strength of that
   invented string**, and `phala_mitigation_map.ts:219` reports `all_cited: true` from a check that
   can never read false. Meanwhile real, chapter-level citations sit populated on all 135
   `bodha_rm_remedy_prescriptions` rows one hop upstream.
3. **The purification chain does NOT drop rows — but its output is computed and then ignored by the
   one selection it exists to govern.** 6 of 7 domains' `top_anchor_id` in `ph_phaladesa` is a
   `staged_revision` anchor, selected by `ORDER BY confidence_high DESC` — the exact field
   `ph_sodhana` flagged as inflated on 90/139 CANON anchors.

---

## 1. `ph_sodhana` — Śodhana (anomaly registry)

**Files:** `writers/ph_sodhana.py` (139 L) · `services/ph_sodhana/engine.py` (369 L)

### 1.1 Instrument fit

| Doctrine | Verdict |
|---|---|
| **D-GROUNDING** | **N/A-by-kind, correctly.** Emits *QA findings about L4's own rows*, not interpretive claims — not one of the plan §2 named grounding classes. Its `source_citation` is a self-referential provenance string (`ph_sodhana/<detector>/<anchor_id>`), which is honest. ✅ |
| **D-SYNTHESIS** | ✅ Singular voice: one `recommendation_text` per finding, deterministic. |
| **D-SALIENCE** | ⚠️ **Half.** Demotion disclosed on-row (`anomaly_severity`, `detected_field`, expected-vs-observed). No `tail_watch` / promotion side, no hard floor. The 4 `critical` rows have no structural protection against a trim (§1.6). |
| **D-TIME** | N/A — build-time findings. Correct. |
| **D-SERVICE** | ⚠️ Consumer exists (`query_anomaly_flags`), but no `density_contract`, no `empty_reason`, no pagination, and a **severity-inverting sort** (§1.6). |

**Still the right instrument?** Yes — a deterministic self-QA registry over `phala_anchors` is the
correct shape. But two of its five detectors are degenerate on live data (§1.5).

### 1.2 Real vs declared dependencies

`depends_on = ['ph_nimitta', 'bo_laksana']`.

| Declared | Actually read? |
|---|---|
| `ph_nimitta` | ✅ `phala_anchors` — the only query in the file (`:104-114`) |
| `bo_laksana` | ❌ **Declared but NEVER read.** No `bodha_*` reference in writer or engine. |

→ **`bo_laksana` is a phantom DAG edge** (F-1).

### 1.3 Drop-vs-label

**LABELS. Does not drop.** The writer's only `DELETE` is chart-scoped on its own table (`:53`), per
§N.3. It never touches `phala_anchors`. Anchors in = 139 / 56; anchors out = 139 / 56, unchanged.

### 1.4 Leverage

```
CANON phala_sodhana: 97 rows
  confidence_inflation / major     90  (90 distinct anchors)
  falsifier_absent    / critical    4
  magnitude_drift     / minor       3
ABH: 41 rows (34 major / 6 critical / 1 minor)
leakage_class IS NOT NULL   = 0    -- 100% NULL, both charts
DISTINCT auto_action        = 1    -- 'stage_for_review', DB-CHECK-pinned
```

- `leakage_class` — 100% NULL by design (non-NULL means the firewall failed to halt). Correct, and a
  *usable* invariant (§1.8).
- **Unread by any consumer:** `derivation_ledger_jsonb`. `query_anomaly_flags` does not SELECT it
  (`query_phala_calibration.ts:308-310`), so the
  `check_basis: 'confidence_high_proxy_not_convergence_score'` disclaimer that `detect_magnitude_drift`
  deliberately writes (`engine.py:191-194`) **never reaches a consumer.** The honest-labelling work is
  done and then discarded at the serving boundary.

### 1.5 Detector integrity (§N.8 — "what would have to run AND FAIL?")

**(a) The G-LADDER ceiling is a chart-wide constant, not a per-anchor ceiling.**
`SELECT DISTINCT dasha_consensus_count, ayanamsha_robustness` → **exactly one row `(0, 3)`** for all
139 anchors. `_g_ladder_ceiling` (`engine.py:115-119`) → `n = min(max(int(0 or 1),1),6) = 1`;
`rob_factor = 0.80 + 0.04·3 = 0.92`; `ceiling = min(0.80, 0.55·0.92) = **0.506**` for every anchor.
Confirmed arithmetically: anchors with `confidence_high > 0.506` are exactly
`0.694(×50) + 0.8(×36) + 0.775(×4) = 90` — **matching the 90 flagged rows to the unit.**
Yet `expected_value_text` narrates `'<= 0.506 (G-LADDER ceiling for n=0, rob=3)'` — a per-anchor
calibration claim over inputs that never vary (§N.7 item 1). Note also `int(n_independent or 1)`: a
genuine `dasha_consensus_count = 0` is silently promoted to 1 — the falsy-zero coercion defect class
of §N.7 item 6.

**(b) `detect_confidence_degenerate` watches the wrong field.** It fires only on ~zero stddev of
`confidence_high` (`engine.py:291-299`), which has 10 distinct values on CANON → passes. But the two
*inputs* to the ceiling it exists to protect **are** fully degenerate, and no detector looks at them.
The detector was written to catch "a posterior model fed hardcoded defaults" and the model *is* fed
hardcoded defaults — on a different axis. §N.8: the signal checks a proxy, not the claim.

**(c) The LEAKAGE-FIREWALL has a NULL/empty blind spot.** `engine.py:252-253`:
`if basis and basis != 'structural_not_yet_empirical'`. A writer that omits `confidence_basis`
entirely (NULL or `''`) trips **nothing**.

**(d) `detect_ledger_gap`** requires exactly one key (`_MINIMUM_LEDGER_KEYS = {'anchor_source'}`) and
fired 0 times on both charts. Close to a no-op, but honestly scoped — noted, not graded a defect.

### 1.6 Service

- **Consumer:** `queryAnomalyFlagsCapability` — `query_phala_calibration.ts:259-327`, registered at
  `L4_phala/index.ts:42`.
- **No `density_contract`, no `empty_reason`, no `limit`/`offset`.**
- **Severity-inverting sort — VERIFIED.** `ORDER BY anomaly_severity DESC` on TEXT sorts
  `minor` → `major` → `informational` → `critical`. Live CANON result order: 3 minor, 90 major,
  **4 critical last**. §N.6 item 2 exactly inverted. Currently unbounded so nothing is lost — but any
  budget trim or added `LIMIT` zeroes the criticals first.
- **Stale description:** claims *"phala_sodhana (200 rows)"* twice (`index.ts:10`,
  `query_phala_calibration.ts:267`). Actual 97 / 41.
- **Drill to L1:** `anchor_id_refs` → `phala_anchors` → `derivation_ledger_jsonb` → L1 = **2 hops** ✅
  (`grounds_to.l1_fact_ids: false` is declared, honestly).

### 1.7 Measured cost

CANON `stale`/97, ABH `lit`/41; `rows_per_second` NULL, `measurement_count` 0, `history` `[]` on
both. **No cost measurement exists on any chart.** Indexes cover the serving query ✅.

### 1.8 Volume derivation (C12)

- **Natural key:** `(anchor_id, anomaly_type, detected_field)` — DB-enforced unique.
- **This is an anomaly registry — fewer rows is better.** A floor here would be an incentive to
  fabricate findings (§N.4). The honest expectation is a **ceiling plus invariants**.

```
expected_volume_formula: 'rows BETWEEN 0 AND (5 * n_anchors) + 1'
expected_volume_inputs:  {"n_anchors": "SELECT count(*) FROM phala_anchors WHERE chart_id = $1"}
```
Observed: CANON 97 ≤ 696 ✅ · ABH 41 ≤ 281 ✅

```sql
-- 1. FIREWALL EARNED-SIGNAL: an l5_calibration_attempted row can only exist if the
--    build-halt failed. Must be 0.
SELECT count(*) FROM phala_sodhana
 WHERE chart_id = $1 AND leakage_class = 'l5_calibration_attempted';

-- 2. CHART-SCOPE INTEGRITY: the FK is on anchor_id ALONE (no chart_id) — a row can
--    legally point at another chart's anchor today. Must be 0.
SELECT count(*) FROM phala_sodhana s
  LEFT JOIN phala_anchors a ON a.anchor_id = s.anchor_id
 WHERE s.chart_id = $1 AND (a.anchor_id IS NULL OR a.chart_id <> s.chart_id);

-- 3. CEILING RE-DERIVATION: every confidence_inflation row must still be inflated
--    when the ceiling is recomputed from the anchor it cites (§N.5).
SELECT count(*) FROM phala_sodhana s JOIN phala_anchors a USING (anchor_id)
 WHERE s.chart_id = $1 AND s.anomaly_type = 'confidence_inflation'
   AND a.confidence_high <= LEAST(0.80,
       (0.50 + 0.05 * LEAST(GREATEST(COALESCE(a.dasha_consensus_count,1),1),6))
       * (0.80 + 0.04 * LEAST(GREATEST(COALESCE(a.ayanamsha_robustness,3),0),5))) + 1e-6;

-- 4. DETECTOR-INPUT NON-DEGENERACY (closes §1.5(b)). Must be 0.
SELECT count(*) FROM (
  SELECT 1 FROM phala_anchors WHERE chart_id = $1
   HAVING count(*) >= 5
      AND count(DISTINCT dasha_consensus_count) = 1
      AND count(DISTINCT ayanamsha_robustness) = 1) z;
```

---

## 2. `ph_suddha_sodhana` — Śuddha-śodhana (cleansed disposition)

**Files:** `writers/ph_suddha_sodhana.py` (170 L) · `services/ph_suddha_sodhana/engine.py` (171 L)

### 2.1 Instrument fit

| Doctrine | Verdict |
|---|---|
| **D-GROUNDING** | N/A-by-kind, correctly — a disposition ledger over L4's own QA output. ✅ |
| **D-SYNTHESIS** | ✅ **The best-behaved asset of the three.** One row per anchor, one `cleanliness_status`, from a single pure function (`classify_cleanliness`, `engine.py:72-78`). No competing voices. |
| **D-SALIENCE** | ✅ **Demotion disclosed on-row and never applied.** `staged_revision_jsonb` proposes; `revision_approved_by`/`revision_applied_at` are hard-NULLed by engine constant *and* writer `assert` (`:65-66`) *and* SQL-literal `NULL, NULL` (`:85`). **Triple-locked D43 rail. The correct doctrinal shape — the rest of L4 should copy it.** |
| **D-TIME** | N/A. |
| **D-SERVICE** | ⚠️ Consumer exists but unbounded, no `density_contract`, no empty-reason. |

### 2.2 Real vs declared dependencies

`depends_on = ['ph_sodhana', 'ph_nimitta']` — **both actually read** (`phala_anchors` `:123`,
`phala_sodhana` `:134-142`). No undeclared reads. **✅ The only one of the three with a correct
dependency declaration.**

### 2.3 Drop-vs-label — the decisive measurement

**LABELS. 1:1 exact tiling. Zero drops, zero orphans, both directions, both charts.**
```
anchors with no suddha row (CANON)  = 0
suddha rows with no anchor (CANON)  = 0
count(phala_anchors) CANON=139 ABH=56 ; count(phala_suddha) CANON=139 ABH=56
```
CANON split: `clean` 44 · `flagged` 3 · `staged_revision` 92 (66.2%). `staged_revision_jsonb`
populated on all 92; `revision_approved_by` non-NULL on 0.

### 2.4 Leverage

- **`magnitude_delta_if_applied` — 0/139 populated.** Structural dead field:
  `_estimate_magnitude_delta` returns non-None only for a `magnitude_drift` flag, but `mag_d` is
  gated on `if staged` (`engine.py:146`), and `staged` requires a major/critical flag —
  `magnitude_drift` is `minor`. So it can only populate for an anchor carrying *both*, which happens
  on neither chart. **It is served** (`query_phala_calibration.ts:498`) and is always NULL.
- **`informational_count` is computed and then dropped on the floor.** Incremented
  (`ph_suddha_sodhana.py:167`), feeds `classify_cleanliness` (`engine.py:76`) — but has **no DB
  column**. An informational-only anchor would be stored `cleanliness_status='flagged'` with
  `critical=major=minor=0` — a status whose evidence is unreconstructable. Latent (no detector emits
  `informational` today) but a genuine silent-loss path in a chain whose whole claim is "nothing is
  dropped silently."
- **Populated-but-unread:** `derivation_ledger_jsonb` (carries the D43 rail attestation) and
  `source_citation` — neither SELECTed by the consumer.
- **Silent-suppression hazard:** `_load_flags_grouped` wraps its entire query in
  `try/except → logger.debug` (`:168-169`). If the `phala_sodhana` read fails, **every anchor is
  silently classified `clean`.** This is the exact pattern F-173 removed from the sibling
  `ph_pratikara` — and the pattern `ph_pratikara.py:172` itself now names "the bug pattern." It
  survives here.

### 2.6 Service

- **Consumer:** `queryCleasedAnchorsCapability` — `query_phala_calibration.ts:441-523`.
- No `density_contract`, no `empty_reason`, **no LIMIT** — returns all 139 rows with
  `staged_revision_jsonb` inline. A real response-budget hazard.
- `ORDER BY cleanliness_status, critical_flag_count DESC` → alphabetical: `clean`(44) first,
  `staged_revision`(92) **last.** Same §N.6 density inversion as §1.6.
- `note: 'revision_approved_by is always NULL — native sign-off required.'` — honest *and* backed by
  a real triple-lock. ✅ **A good example of an earned claim.**
- **Second consumer (build-time):** `ph_phaladesa.py:345` — see §4.2.
- Drill: 2 hops ✅.

### 2.7 Measured cost

`rows_per_second` NULL, `measurement_count` 0, both charts. CANON `stale`/139, ABH `lit`/56.
Indexes: unique `(chart_id, anchor_id)`, `(chart_id, cleanliness_status)`, `anchor_id` FK ✅.

### 2.8 Volume derivation (C12)

- **Natural key:** `(chart_id, anchor_id)`, DB-unique. **Exact 1:1 tiling of `phala_anchors`.**

```
expected_volume_formula: 'rows = n_anchors'
expected_volume_inputs:  {"n_anchors": "SELECT count(*) FROM phala_anchors WHERE chart_id = $1"}
```
A *derived* equality against a live upstream count, not a `count(*) = 139` pin. Observed 139=139,
56=56 ✅

```sql
-- 1. NO-GAP TILING (both directions). Must be 0.
SELECT count(*) FROM phala_anchors a
  FULL OUTER JOIN phala_suddha_sodhana s
    ON s.anchor_id = a.anchor_id AND s.chart_id = a.chart_id
 WHERE COALESCE(a.chart_id, s.chart_id) = $1
   AND (a.anchor_id IS NULL OR s.anchor_id IS NULL);

-- 2. STATUS RE-DERIVATION. Must be 0.
SELECT count(*) FROM phala_suddha_sodhana WHERE chart_id = $1
   AND cleanliness_status <> CASE
       WHEN critical_flag_count > 0 OR major_flag_count > 0 THEN 'staged_revision'
       WHEN minor_flag_count > 0 THEN 'flagged' ELSE 'clean' END;

-- 3. CROSS-TABLE FLAG-COUNT CONSISTENCY vs phala_sodhana (also the detector for the
--    §2.4 silent-classify-clean path). Must be 0.
SELECT count(*) FROM phala_suddha_sodhana s
  LEFT JOIN (SELECT anchor_id,
               count(*) FILTER (WHERE anomaly_severity='critical') c,
               count(*) FILTER (WHERE anomaly_severity='major')    m,
               count(*) FILTER (WHERE anomaly_severity='minor')    n
             FROM phala_sodhana WHERE chart_id = $1 GROUP BY 1) f USING (anchor_id)
 WHERE s.chart_id = $1
   AND (s.critical_flag_count, s.major_flag_count, s.minor_flag_count)
    IS DISTINCT FROM (COALESCE(f.c,0)::smallint, COALESCE(f.m,0)::smallint, COALESCE(f.n,0)::smallint);

-- 4. D43 RAIL (an earned detector for a real claim). Must be 0.
SELECT count(*) FROM phala_suddha_sodhana WHERE chart_id = $1
   AND (revision_approved_by IS NOT NULL OR revision_applied_at IS NOT NULL);
```

---

## 3. `ph_pratikara` — Pratīkāra (mitigation programme)

**Files:** `writers/ph_pratikara.py` (266 L) · `services/ph_pratikara/engine.py` (289 L).
*(The brief named `brahmagyan/phala/mitigation.py` + `l4_mitigation.py` — neither is imported by this
writer or engine; they are legacy/parallel modules. The live path is `services.ph_pratikara.engine`.)*

### 3.1 Instrument fit

| Doctrine | Verdict |
|---|---|
| **D-GROUNDING** | ❌ **HARD FAIL.** Remedies are a plan §2 named class where grounding is **required**. `phala_mitigation` has **no `grounding_tier`, no `classical_sources_array`, no `source_id`** — only `classical_citation TEXT NOT NULL`, populated on 100% of rows with an engine-invented string. |
| **D-SYNTHESIS** | ❌ Not a verdict — 536 near-identical rows: 1 distinct `intensity_tier`, 1 distinct `linked_anchor_id`, 1 distinct citation, 1 distinct `cross_tradition_corroboration`. No singular voice because there is no differentiated content. |
| **D-SALIENCE** | ❌ Nothing layered. Every row served flat, every row empty. |
| **D-TIME** | ⚠️ Partial. `window_start`/`window_end` inherited from `kala_convergence` (44/536 NULL on CANON); `re_evaluation_date` NOT NULL. But `initiation_muhurta_ref` is **NULL on 100% of rows, both charts**, despite an FK to `phala_muhurta` and 134 live muhurta rows (§3.6 F-17). |
| **D-SERVICE** | ⚠️ Two consumers, both bounded, but no `density_contract`; `domain` facet structurally broken (§3.6). |

**Still the right instrument?** The *design* is right (obstruction-keyed, prescription-consuming,
muhūrta-timed, proportional). The *implementation* currently produces nothing. **This is a repair,
not a redesign.**

### 3.2 Real vs declared dependencies

`depends_on = ['ph_nimitta','bo_upaya','ka_vighnakara','ka_sangam']` — **all four genuinely read:**
`kala_obstruction` (`:184`) · `kala_convergence` LEFT JOIN (`:189`) ·
`phala_anchors WHERE malleability='influenceable'` (`:204`) · `bodha_rm_remedy_prescriptions` (`:232`).
No undeclared reads. **Declaration is correct.** ✅

### 3.3 The empty-programme defect (VERIFIED, both charts)

```
CANON: n=536  DISTINCT linked_anchor=1  graha_null=44  DISTINCT graha=1
       initiation_muhurta_ref NULL=536  DISTINCT intensity_tier=1
       DISTINCT classical_citation=1    DISTINCT cross_tradition_corroboration=1
       program_jsonb->>'total_scheduled' = '0'  → 536/536  (100%)
ABH:   n=741  … total_scheduled='0' → 741/741  (100%)
```
Every row, verbatim:
```json
program_jsonb      {"scheduled_ids": [], "sequence_basis": "prerequisite_topo_sort + incompatible_exclusion", "total_scheduled": 0}
tradition_options  {"vastu":[],"vedic":[],"modern":[],"tantra":[],"ayurvedic":[],"lal_kitab":[]}
recommended_tier   {"free":[],"low_cost":[],"high_investment":[]}
classical_citation "Brihat Parashara Hora Shastra — Upaya chapter"
```
**Root cause, fully traced:** commit `5f097e738` (2026-08-21) — *"`ph_pratikara` SELECTs nonexistent
columns → empty prescriptions for every chart (#1454)"*. Six wrong column names + a `SAVEPOINT/except`
swallow turned the `UndefinedColumn` into `{}`. That commit's own body states: *"Does not touch
phala_mitigation data or dispatch a rerun — GA-3 queues the ph_pratikara rerun."* **The rerun never
happened** — `last_built_at` 2026-08-12/13, nine days before the fix.

Data confirms the fix *would* work: `bodha_rm_remedy_prescriptions` holds 135 CANON rows across 9
grahas including 15 for `Saturn`, and `Saturn`.lower() = `saturn` matches the `afflicting_graha`
value actually stored. The lookup key is correct in the fixed code.

### 3.4 The degenerate-anchor defect (independent of F-173; **survives the fix**)

`ph_pratikara.py:94-99` — the first anchor of the first domain bucket wins, and the same one wins for
every obstruction in the chart. No domain match, no window overlap, no graha relation.

**Measured:** all 536 CANON rows link to a single anchor `98660c88-…` (domain `career`, magnitude
`minor`) — chosen from **107 influenceable candidates across 4 domains** (career 29 · transition 50 ·
wealth 26 · health 2). Consequences:
1. **P4 proportionality is degenerate.** `intensity_tier = f(severity, anchor_magnitude)` with a
   frozen `minor` magnitude → all 536 rows `light`, including all 396 `medium`-severity ones.
   `intensive` is structurally unreachable on this chart.
2. **The L5 outcome loop is mis-keyed.** `outcome_hook_jsonb.linked_anchor_id` is the same anchor on
   all 536 rows.
3. **§N.7 item 6 violation** — a plausible-looking non-null standing in for "no domain-relevant
   anchor was determined." An honest NULL is available (column nullable, FK `ON DELETE SET NULL`).
4. **32 CANON anchors are excluded outright** by `malleability = 'influenceable'` — all 3 `major` and
   all 5 `moderate` anchors are `semi_influenceable` and can never receive a mitigation link. That
   filter is undisclosed on-row and at the serving layer.

### 3.5 Grounding labelability — the heaviest item

**Schema:** `classical_citation TEXT NOT NULL` + `cross_tradition_corroboration SMALLINT CHECK 0..6`.
**No `grounding_tier`. No `classical_sources_array`. No `source_id`.**

**Provenance trace:** `bo_upaya` → `bodha_rm_remedy_prescriptions.classical_sources_jsonb` =
`{"source_id": …, "citation": …}` — **populated on 135/135 CANON rows**, with genuine chapter-level
references:
```
{"citation":"BPHS Ch.93 (Chandra dana)","source_id":"BPHS"}
{"citation":"Rigveda 7.59.12; BPHS Ch.88 (Shani health upaya)","source_id":"BPHS"}
{"citation":"Phaladeepika remedial section; Mahabharata Anushasana Parva 149","source_id":"Phaladeepika"}
{"citation":"Valmiki Ramayana, Yuddha Kanda 107; BPHS Ch.88 (Surya upaya)","source_id":"BPHS"}
```
The upstream table *also* carries `citation_ref`, `citation_human`, `classical_source_text_jsonb`,
`estimated_time_minutes_daily`, `phase_duration_days`. **The engine propagates none of these.** It
reads only `classical_sources_jsonb->>'citation'` (`:263`), never `source_id`, and
`estimated_time_minutes` is never SELECTed → `recommended_tier_jsonb[*].estimated_time_min` is `null`
on every entry that will ever be emitted.

**The fabrication:** `engine.py:255-258` — with `prescriptions = []` the `next(…, default)` always
returns the invented string, and `NOT NULL` means there is no schema path to an honest null. **This
is the hard-floor violation.**

**Propagation into served grades — two compounding §N.8 defects:**
- `kala_upaya_diagnosis.ts:472,481` — `citation = nonBlank(row.classical_citation)` →
  `assignEfficacyTier({hasCitation: true, …})` → `:385 if (params.hasCitation) return
  'classically_attested'`. **All 536 rows served as `classically_attested` on an invented string.**
- `phala_mitigation_map.ts:196-219` — `all_cited: uncited.length === 0` where `uncited` filters on
  `!classical_citation && !source_citation`. Since `classical_citation` is `NOT NULL` and always
  populated by the fallback, **`all_cited` cannot read false.** The docstring (`:87`, `:128`) calls
  this an enforced "Grounding contract" — it is enforced by a DB constraint plus an invented default.

**Honest tier per remedy class, once repaired:**

| Class | Honest tier | Basis |
|---|---|---|
| Prescription-derived citation (japa/mantra/charity/gemstone from `bo_upaya`) | **`sruti`** | `classical_sources_jsonb.source_id` + chapter/verse resolve to the L0 corpus. Must be *propagated*, not restated (§N.5). |
| Sequencing (`program_jsonb.scheduled_ids`, topo-sort + incompatibility) | **`yukti`** | Deterministic derivation over prerequisite/incompatibility arrays; no text prescribes this sequence. |
| Cost/feasibility tiering (free/low_cost/high_investment, ₹5,000 cut) | **`pratyaksa`** | The 5,000 INR boundary (`engine.py:142`) is an instrument convention, never classical. |
| Intensity proportionality (`_SEVERITY_MAGNITUDE_TO_INTENSITY`, `:28-41`) | **`yukti`** | A 12-cell hand-built table — honest as a principle-derived rule; dishonest if cited to a text. |
| `cross_tradition_corroboration` | **`pratyaksa`** | A count over the instrument's own buckets. |

**Getting to `yukti`/`pratyaksa` labels here IS the success condition — not a downgrade.** A row whose
only citation is the invented BPHS string must resolve to `classical_citation = NULL` +
`grounding_tier = 'pratyaksa'`, not to `classically_attested`.

### 3.6 Service

**Consumers:** (1) `queryRemedyProgramCapability` — `query_phala_calibration.ts:333-436`, bounded
(`LIMIT ≤ 50`), discloses `total_matching` + `more_available` ✅. (2) `phala_mitigation_map` MCP tool.
(3) `kala_upaya_get` via `lib/kala_upaya_diagnosis.ts`.

- **The `domain` facet is structurally broken.** `:381-391` filters via `EXISTS (… phala_anchors a
  WHERE a.anchor_id = linked_anchor_id AND a.domain = $n)`. Since `linked_anchor_id` is one constant
  `career` anchor: `domain='career'` → all 536; **every other domain → 0 rows, no empty-reason.**
- **Severity-inverting sort (latent).** `ORDER BY obstruction_severity DESC NULLS LAST` over
  `low`/`medium`/`high` sorts alphabetically: `medium` → `low` → **`high` last**. With `LIMIT 50` of
  536, a chart carrying `severe`→`high` obstructions would lose its most severe rows off page 1.
  Latent today (neither chart has a `severe` obstruction) but a live §N.6 item-2 defect in code.
- **Vocabulary drift at the serving boundary.** The writer maps kala's `mild/moderate/severe` →
  `low/medium/high` (`:76`) and **stores the mapped value**. A caller filtering on the kala vocabulary
  matches nothing, undisclosed.
- **Inconsistent unknown-severity defaults.** Writer `:86` → `'low'`; engine `:163` → `'medium'`. Two
  different plausible-sounding constants for the same "I don't know" (§N.7 item 6).
- **Silently-ignored filters.** `phala_mitigation_map.ts:167-172` forwards `anchor_id` and
  `mitigation_type`; `query_remedy_program`'s schema accepts neither. Both dropped without notice.
- **The one doctrine-aware consumer already routes around this asset.** `upaya.ts:315-322` +
  `kala_upaya_diagnosis.ts:433-447` (F-118) explicitly detect the empty programme — *"on the canonical
  chart every phala_mitigation row is a severity classification with a provably empty remedy
  program"* — and quarantine all 536 rows into `non_prescriptive_rows`, never counted as
  interventions. **`ph_pratikara` therefore contributes exactly zero actionable interventions to
  `kala_upaya_get` today**, while consuming budget as 536 rows of noise mass. The serving layer's
  honesty is doing the work the producer should have done; **the fix belongs at the producer.**
- Drill: 2 hops ✅ structurally; substantively meaningless per §3.4.

### 3.7 Measured cost

CANON `stale`/536, ABH `lit`/741; no cost measurement. Indexes cover the serving query ✅.

**Idempotency hazard:** the natural key includes the *derived* `intensity_tier`, so a rebuild whose
tier changes cannot conflict-match its predecessor — only the chart-scoped `DELETE` (`:64`) keeps this
clean. Coupled with `ON CONFLICT DO NOTHING` on a `gen_random_uuid()` PK (so the conflict clause is
dead code and can never fire), `rows_inserted` is incremented unconditionally at `:163` — a claimed
count with no measurement. Same pattern at `ph_sodhana.py:96`. Accurate today; not *earned* (§N.8).

### 3.8 Volume derivation (C12) — including the inversion

**Natural key:** `(chart_id, obstruction_id)` in substance (the DB key also pins `intensity_tier`,
which it should not — §3.7).
**Driving population:** `kala_obstruction`, **not** `phala_anchors`. Verified exact 1:1, zero orphans
both directions: `kala_obstruction` CANON=536 ABH=741; `phala_mitigation` CANON=536 ABH=741.

**The inversion, attributed to a named cause.** The brief's framing — "the SMALLER chart has MORE
rows" — is true only along the *anchor* axis and is a coincidence of that axis:

| | CANON | ABH |
|---|---|---|
| `kala_convergence` | 14,868 | **17,957** |
| `kala_obstruction` | 536 | **741** |
| `phala_mitigation` | **536** | **741** |
| `phala_anchors` | **139** | 56 |

`phala_mitigation` is a **strict 1:1 image of `kala_obstruction`** (writer loops `for obs in
obstructions`, `:80`), which is driven by `kala_convergence` (`ka_sangam`). Abhinandan has ~21% more
convergence windows → ~38% more obstructions → 38% more mitigation rows. `phala_anchors` enters the
writer **only** as a one-row lookup whose entire result collapses to a single `linked_anchor_id`;
anchor count has **zero** influence on row count. **Named cause: `kala_convergence` volume →
`kala_obstruction` cardinality.**

```
expected_volume_formula: 'rows = n_obstructions'
expected_volume_inputs:  {"n_obstructions": "SELECT count(*) FROM kala_obstruction WHERE chart_id = $1"}
volume_explanation:      'One row per kala_obstruction row (1:1). Row count tracks
                          kala_convergence → kala_obstruction cardinality, NOT phala_anchors.'
```
*(Current registry `volume_explanation` — "One row per remedy recommendation, sequenced by feasibility
tier" — is wrong; it describes a per-remedy grain the table does not have.)*

```sql
-- 1. NO-GAP TILING over kala_obstruction (both directions). Must be 0.
SELECT count(*) FROM kala_obstruction o
  FULL OUTER JOIN phala_mitigation m ON m.obstruction_id = o.id AND m.chart_id = o.chart_id
 WHERE COALESCE(o.chart_id, m.chart_id) = $1 AND (o.id IS NULL OR m.mitigation_id IS NULL);

-- 2. ANCHOR-LINK NON-DEGENERACY (closes §3.4). Must be 0.
SELECT count(*) FROM (
  SELECT 1 FROM phala_mitigation WHERE chart_id = $1
   HAVING count(DISTINCT linked_anchor_id) = 1
      AND (SELECT count(*) FROM phala_anchors
            WHERE chart_id = $1 AND malleability = 'influenceable') > 1) z;

-- 3. PROGRAMME NON-EMPTINESS (closes §3.3). Must be 0.
SELECT count(*) FROM phala_mitigation m
 WHERE m.chart_id = $1
   AND COALESCE((m.program_jsonb->>'total_scheduled')::int, 0) = 0
   AND EXISTS (SELECT 1 FROM bodha_rm_remedy_prescriptions p
                WHERE p.chart_id = m.chart_id
                  AND lower(p.target_graha) = COALESCE(lower(m.afflicting_graha), 'jupiter'));

-- 4. CITATION PROVENANCE (closes §3.5). Must be 0.
SELECT count(*) FROM phala_mitigation m
 WHERE m.chart_id = $1 AND m.classical_citation IS NOT NULL
   AND NOT EXISTS (
     SELECT 1 FROM bodha_rm_remedy_prescriptions p
      WHERE p.chart_id = m.chart_id
        AND p.prescription_id::text IN (
              SELECT jsonb_array_elements_text(m.program_jsonb->'scheduled_ids'))
        AND p.classical_sources_jsonb->>'citation' = m.classical_citation);

-- 5. SEVERITY-VOCABULARY CONSISTENCY with the upstream it restates (§N.5).
SELECT count(*) FROM phala_mitigation m JOIN kala_obstruction o ON o.id = m.obstruction_id
 WHERE m.chart_id = $1
   AND m.obstruction_severity IS DISTINCT FROM
       CASE o.severity WHEN 'mild' THEN 'low' WHEN 'moderate' THEN 'medium'
                       WHEN 'severe' THEN 'high' END;
```
**Explicitly NOT proposed:** any `count(*) = 536` pin.

---

## 4. Cross-asset: the purification chain's drop-vs-label semantics

### 4.1 Nothing is dropped. Everything is labelled. (VERIFIED)

| Stage | Input | Output | Anchors dropped |
|---|---|---|---|
| `phala_anchors` (ph_nimitta) | — | CANON 139 · ABH 56 | — |
| `ph_sodhana` | 139 / 56 anchors | 97 / 41 **flag rows** (additive registry, not a filter) | **0** |
| `ph_suddha_sodhana` | 139 / 56 anchors | 139 / 56 **disposition rows** | **0** |

Neither writer issues any `DELETE`/`UPDATE` against `phala_anchors`; both delete only their own
chart-scoped rows — correct §N.3. `ph_suddha_sodhana` produces an **exact 1:1 tiling**. The demotion
is disclosed on-row exactly as D-SALIENCE requires: `cleanliness_status` + three severity counts +
`flag_ids_jsonb` (back-pointers to the specific `phala_sodhana` rows) + `staged_revision_jsonb`
(marked `approval_required: true`, `auto_apply: false`). No correction is ever applied — triple-locked.
**D43 is genuinely earned.**

**Doctrinal verdict: `ph_sodhana` / `ph_suddha_sodhana` are LABEL-not-DROP; §N.6 / B.10 are satisfied
at the write path. There is no first-order silent-exclusion finding here.**

### 4.2 …but the label is computed and then ignored where it matters most

`ph_phaladesa` is the only build-time consumer of `cleanliness_status`. It reads it (`:339`) and uses
it **only for two aggregate counters** (`:360-364`). The domain's headline anchor is selected by a
*separate* ordering that ignores disposition entirely: `:348` `ORDER BY pa.domain, pa.confidence_high
DESC NULLS LAST` → `if s.top_anchor_id is None: s.top_anchor_id = aid` (`:365`).

**Measured on the canonical chart — 6 of 7 domains lead with a flagged anchor:**
```
domain        top anchor    conf_high  cleanliness_status  crit  major
career        60fbe639…       0.372    clean                 0     0
character     917e2d0c…       0.800    staged_revision       1     1
health        057a97fa…       0.775    staged_revision       0     1
relationship  c0fa3e1e…       0.800    staged_revision       0     1
spirituality  d91f6db5…       0.800    staged_revision       0     1
transition    0a4f4a76…       0.694    staged_revision       0     1
wealth        36353bce…       0.800    staged_revision       0     1
```
The selection key is `confidence_high` — **the exact field `ph_sodhana` flagged as inflated on 90/139
anchors.** Sorting descending by an inflation-suspect field systematically *promotes* the anchors the
purification pass flagged. **The chain's whole output is available and is not consulted by the one
decision it was built to inform.**

`ph_pramana` reads `phala_anchors` alone (`:131`) — it does not know that 4 CANON anchors carry a
`critical` `falsifier_absent` flag.

### 4.3 Where a *real* silent drop does live: `ph_pratikara`

The one genuine undisclosed exclusion in this trio is not in the purification pair — it is
`ph_pratikara.py:204`'s `WHERE malleability = 'influenceable'`, removing **32 of 139 CANON anchors**
(all 3 `major`, all 5 `moderate`, 24 `minor`) with no on-row flag, no `empty_reason`, no serving
disclosure. Compounded by §3.4, the effective exclusion is 138 of 139.

---

## 5. Findings → W2

| # | Tag | Finding | Doctrine | Evidence |
|---|---|---|---|---|
| **F-1** | **NOW** | `ph_sodhana.depends_on` declares `bo_laksana`, never read. Phantom DAG edge. | deps honesty | one SELECT only, on `phala_anchors` (`:104-114`) |
| **F-2** | **MUST** | **`ph_pratikara` serves 1,277 rows of provably empty remedy programmes.** F-173's code fix (`5f097e738`) landed; the queued rerun never ran; live data is 9 days pre-fix. | §N.8; B.10 | `total_scheduled='0'` on 536/536 and 741/741; `last_built_at` vs fix date; commit body |
| **F-3** | **MUST** | **Fabricated classical citation on 100% of `phala_mitigation` rows**, made structurally unavoidable by `classical_citation NOT NULL`. | **Hard-floor violation**; §N.7 item 6; D-GROUNDING | `engine.py:255-258`; `DISTINCT classical_citation = 1`; `is_nullable='NO'` |
| **F-4** | **MUST** | The fabricated citation is laundered into a served *grade*: all 536 rows come back `efficacy_tier='classically_attested'`. | §N.8; §N.7 item 4 | `kala_upaya_diagnosis.ts:472,481,385` |
| **F-5** | **MUST** | `phala_mitigation_map`'s `all_cited` **cannot read false**, yet the docstring calls it an enforced "Grounding contract". | §N.8 | `phala_mitigation_map.ts:196-219`, docstring `:87`,`:128` |
| **F-6** | **MUST** | `phala_mitigation` has **no `grounding_tier` / `classical_sources_array` / `source_id`** — remedies cannot carry a tier at all. Meanwhile `bo_upaya` holds real chapter-level citations plus `estimated_time_minutes_daily` / `phase_duration_days` on 135/135 rows, **all unpropagated**. Leverage + grounding in one. | D-GROUNDING; §N.5 | `information_schema` both tables; live values in §3.5 |
| **F-7** | **MUST** | **`linked_anchor_id` is a single constant across every mitigation row** — 536 rows → 1 anchor from 107 candidates in 4 domains. Collapses P4 proportionality, mis-keys the L5 outcome hook, breaks the `domain` facet. **Survives the F-173 fix.** | §N.7 item 6; D-SYNTHESIS | `:94-99`; `DISTINCT linked_anchor_id = 1` both charts |
| **F-8** | **MUST** | `query_remedy_program`'s `domain` filter returns **0 rows for every domain except `career`**, no `empty_reason`. Consequence of F-7. | D-SERVICE; §N.6 item 3 | `:381-391` |
| **F-9** | **MUST** | **The purification verdict is computed and then ignored by the one selection it governs.** `ph_phaladesa` picks `top_anchor_id` by `ORDER BY confidence_high DESC` — the field flagged inflated on 90/139 anchors — so **6 of 7 CANON domains lead with a `staged_revision` anchor.** | D-SALIENCE; §N.6 item 2 | `ph_phaladesa.py:348,365`; §4.2 table |
| **F-10** | **MUST** | Severity-inverting sorts on two capabilities. `query_anomaly_flags`: minor→major→**critical last** (verified 3/90/4). `query_remedy_program`: `high` **last** under `LIMIT 50` of 536 (latent). | §N.6 item 2 | `:313`, `:414` |
| **F-11** | **NOW** | No `density_contract` / `empty_reason` on any of the three; `query_anomaly_flags` and `query_cleansed_anchors` entirely unpaginated (139 rows with inline `staged_revision_jsonb`). `query_prospective_ledger.ts:143` is the only L4 capability declaring one. | §N.6 item 4 | grep across `L4_phala/` |
| **F-12** | **NOW** | **`ph_sodhana`'s G-LADDER ceiling is a chart-wide constant (0.506), not a per-anchor calibration** — both inputs invariant across all 139 anchors — yet `expected_value_text` narrates it as per-anchor. `int(n or 1)` silently promotes a genuine `0` to `1`. | §N.7 items 1 & 6; §N.8 | `engine.py:115-119,133-134`; `DISTINCT (0,3)`; 90 reproduces at 0.506 |
| **F-13** | **NOW** | **`detect_confidence_degenerate` watches the wrong field** — guards `confidence_high` variance while the ceiling's *inputs* are the degenerate ones. Misses the live instance it exists to catch. | §N.8 (proxy, not claim) | `engine.py:278-326` vs F-12 |
| **F-14** | **NOW** | **LEAKAGE-FIREWALL blind spot:** a NULL or empty `confidence_basis` passes silently. | §N.8 | `engine.py:252-253` |
| **F-15** | **NOW** | `ph_pratikara` silently excludes 32 CANON anchors (`malleability='influenceable'`) with no flag and no serving disclosure. **The chain's one genuine undisclosed drop.** | §N.6 / B.10 | `:204`; magnitude × malleability crosstab |
| **F-16** | **NOW** | `ph_suddha_sodhana._load_flags_grouped` wraps its `phala_sodhana` read in `try/except → logger.debug`. On failure **every anchor is silently classified `clean`.** Identical to the pattern F-173 removed from the sibling, which `ph_pratikara.py:172` now names "the bug pattern." | §N.8; F-173 precedent | `ph_suddha_sodhana.py:131,168-169` |
| **F-17** | **NOW** | `initiation_muhurta_ref` NULL on 100% of rows despite an FK to `phala_muhurta` and 134 live muhurta rows. Engine comment says *"writer sets this after ph_muhurta insert"* — the writer never does. | Leverage; D-TIME | `engine.py:280`; `count(phala_muhurta)` = 134 |
| **F-18** | **NOW** | `recommended_tier_jsonb[*].estimated_time_min` structurally always `null` — `estimated_time_minutes` is never SELECTed, while the upstream columns are live. | Leverage | `engine.py:53,136`; `:226-236` |
| **F-19** | **NOW** | Two different plausible defaults for the same unknown severity (writer `'low'`, engine `'medium'`/`'moderate'`); plus stored-vocabulary drift so a caller filtering on kala's `mild/moderate/severe` matches nothing, undisclosed. | §N.7 item 6; D-SERVICE | `:76,86`; `engine.py:163-165` |
| **F-20** | **NOW** | `rows_inserted` incremented unconditionally alongside `ON CONFLICT DO NOTHING` in both `ph_sodhana` and `ph_pratikara` — a claimed "inserted" count with no measurement (accurate today only because the conflict target is a uuid PK, making the clause dead code). | §N.8 | `ph_sodhana.py:85,96`; `ph_pratikara.py:147,163` |
| **F-21** | **NOW** | `FlagSummary.informational_count` feeds `classify_cleanliness` but has **no DB column** — an informational-only anchor stores `flagged` with all counts `0`, unreconstructable. Latent, but a real silent-loss path in the chain whose claim is "nothing silently dropped." | §N.6 / B.10 | `:167`; `engine.py:76`; column list |
| **F-22** | **NOW** | Three stale/wrong registry `volume_explanation`s (two describe `ph_rectification`; one contradicts delete-then-insert; `ph_pratikara`'s states the wrong grain) plus two stale serving descriptions ("200 rows" vs 97/41; "sparse" vs 600+). | B.8 | `asset_registry`; `index.ts:10-12`; `:267,338,454,373` |
| **F-23** | **NOW** | `phala_sodhana.anchor_id` FK targets `phala_anchors(anchor_id)` **without `chart_id`** — a row can legally carry a `chart_id` disagreeing with its anchor's. Currently clean; needs the invariant. | Integrity | `pg_constraint`; invariant 2 in §1.8 |
| **F-24** | **NEVER-LATER** | `rows_per_second=NULL`, `measurement_count=0`, `history=[]` for all three on both charts. No cost signal to regress against. | measured cost | `asset_throughput` |
| **F-25** | **NEVER-LATER** | `phala_mitigation_natural_key` includes the *derived* `intensity_tier`; the honest key is `(chart_id, obstruction_id)`. Harmless under delete-then-insert, wrong as a stated key. | §N.3 / C12 | `pg_indexes` |
| **F-26** | **NEVER-LATER** | `ph_sodhana.derivation_ledger_jsonb` carries genuinely useful honesty metadata (notably `check_basis: 'confidence_high_proxy_not_convergence_score'`) and is **not SELECTed by any consumer** — the disclaimer never reaches a caller. | §N.6 item 4 | `engine.py:191-194` vs `:308-310` |
| **F-27** | **NEVER-LATER** | `phala_mitigation_map` forwards `anchor_id` / `mitigation_type` filters that `query_remedy_program` does not accept; both silently dropped. | D-SERVICE | `:167-172` vs `:355-368` |

### Sequencing note for W2

**F-2 (rerun) must land AFTER F-3 / F-6 / F-7 are fixed in code.** Rerunning today would replace
1,277 empty rows with 1,277 rows carrying *real* remedy content still linked to one wrong anchor and
still stamped with a fabricated-or-unpropagated citation — **a worse state than an obviously-empty
one.** Order: fix the writer (F-3, F-6, F-7, F-17, F-18) → add `grounding_tier` and drop
`classical_citation`'s `NOT NULL` so an honest null is expressible → rerun → set `target_floor` to
the achieved count (§N.4).
