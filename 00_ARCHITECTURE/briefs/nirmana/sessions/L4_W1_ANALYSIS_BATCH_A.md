---
artifact: L4_W1_ANALYSIS_BATCH_A.md
canonical_id: NIRMANA_V21_L4_W1_BATCH_A
version: "1.0"
status: CURRENT
campaign_id: nirmana-elevation
session: L4
wave: W1 ANALYZE
asset: ph_nimitta (the L4 root)
produced_on: 2026-09-05
method: read-only subagent analysis against live production; worktree at origin/main 20323fae4
---

# L4 W1 ANALYZE — BATCH A — `ph_nimitta` (Phala anchors, L4 ROOT)

Worktree `~/nirmana-s/l4` @ `20323fae4`. All DB figures from live production, canonical chart
`482012f1-…` unless stated. **No writes performed.**

---

## 0. Orientation: what actually runs

The registry's declared source is `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py`
(846 ln), but the derivation logic is **not** in `platform/python-sidecar/brahmagyan/phala/`. The
writer imports `services.ph_nimitta.engine` and `services.ph_nimitta.base_rate`:

- `platform/python-sidecar/services/ph_nimitta/engine.py` (769 ln) — all derivation, DB-free
- `platform/python-sidecar/services/ph_nimitta/base_rate.py` (81 ln) — JL-009 normalized age-band prior
- `platform/python-sidecar/services/ph_nimitta/dasha_consensus.py` (164 ln) — **never imported by the writer** (see F-6)

`brahmagyan/phala/anchors.py` (616 ln) and `l4_anchors.py` (1241 ln) are a **separate legacy FastAPI
estate**, not the orchestrator writer — `anchors.py` is mounted live at `/api/compute/phala/*` via
`main.py:50-52`. This matters a great deal (F-11, F-12).

---

## 1. Instrument fit

| Doctrine | Fit | Evidence |
|---|---|---|
| **D-GROUNDING** | **Partial — no tier vocabulary exists** | `phala_anchors` has no `grounding_tier`, no `classical_sources_array`, no `constituent_facts_array`. Only `source_citation` (text, L3-pointing: `mode_d/av_bindhu/Jupiter@Libra/SAV=34/2029-08-24`) and `derivation_ledger_jsonb` (cites `convergence_id`/`signal_id`, **never an L1 `fact_id`**). Verified by `information_schema.columns` census. |
| **D-SYNTHESIS** | **Violated at the serving boundary** | Two live surfaces read the same table with *contradictory* posterior policy — `query_predictive_anchors.ts` nulls `posterior`/`confidence_*`/`lift_vector` on 100% of rows; `brahmagyan/phala/anchors.py:189-205` (`event_anchors` → MCP `phala_anchors_get`) serves all of them raw. Two voices, same rows. (F-2, F-11) |
| **D-SALIENCE** | **Serves it structurally, breaks it in ordering** | Chart-intrinsic terms *are* stored at build (magnitude, malleability, horizon_tier, posterior). But the only serving order is `ORDER BY magnitude DESC` on a **TEXT** column, which inverts the salience ladder (F-3). No `tail_watch` section and no `hardFloor` anywhere in the L4 serving path. |
| **D-TIME** | **Serves it; one open arbiter overlap** | `ph_nimitta` *is* the L4 arbiter for (domain, range) — 139 anchors, each with `window_start/peak_date/window_end`. But it inherits all of `kala_bhavishya` (D37) while `kala_bhavishya` remains independently served by the L3 `kala_*` tools, so the same projection can be voiced twice at different granularity. No aligned/partially_aligned/disputed field exists on `phala_anchors`. |
| **D-SERVICE** | **Consumers exist; density/empty-reason partial; ≤2 hops partial** | 9 downstream consumers verified (§6). `query_predictive_anchors` has an exemplary `empty_reason` block (4 distinguished cases, `backing_data_reachable`) but declares **no `density_contract`**. The ≤2-hop L1 drill works for 135/139 rows and fails for 4 (F-9). |

**Is it still the right instrument?** Yes. It is the only deterministic surface that converts L2
signals + L3 windows into falsifiable, dated, magnitude-graded claims, and 9 assets plus the
retrieval spine depend on it. The problem is not the instrument — it is that roughly half of what it
computes is either constant, dark at serve time, or unpopulated.

---

## 2. Real vs declared dependencies

Declared (9): `bo_anveshana, bo_bimba, bo_cgm_paths, bo_karanajala, bo_laksana, bo_samskara,
bo_sangati, ka_bhavishya_lekha, ka_sangam`.

**Actual table reads** (exhaustive; `ph_nimitta.py` line refs — the engine and `base_rate.py`
contain zero SQL, verified by grep):

| Line | Table | Declared dep it satisfies |
|---|---|---|
| `:311`, `:681` | `kala_convergence` | ✅ `ka_sangam` |
| `:331` | `kala_bhavishya` | ✅ `ka_bhavishya_lekha` |
| `:364` | `bodha_discoveries` | ✅ `bo_anveshana` |
| `:395`, `:502` | `bodha_msr_signals` | ✅ `bo_laksana` |
| `:500` | `bodha_cgm_paths` | ✅ `bo_cgm_paths` |
| `:545` | `bodha_contradictions` | ✅ `bo_sangati` (assumed owner) |
| `:576` | `bodha_signal_embeddings` | ✅ `bo_bimba` (assumed owner) |
| `:426` | **`brahma_event_ontology`** | ❌ **UNDECLARED** (L0 global ref table) |
| `:435` | **`bodha_pratijna`** | ❌ **UNDECLARED** (`bo_pratijna` is not in `depends_on`) |
| `:450` | **`kala_activation_predicates`** | ❌ **UNDECLARED** (`ka_yojaka`) |
| `:129` | `phala_anchors` (DELETE) | own target |

**Declared but never read:** `bo_bimba` and `bo_sangati` are satisfied only by inference (table→asset
mapped by convention, not by reading their writers); **`bo_karanajala` and `bo_samskara` have no
corresponding table read at all** — 2 of 9 declared deps are unused.

**Undeclared but load-bearing:** `bodha_pratijna` supplies `promise_lift` (up to 2.18×) and
`kala_activation_predicates` supplies `activation_lift` (2.0× on 135/139 rows). These are the two
largest multipliers in the posterior and neither gates the build. A `bo_pratijna` failure would
silently degrade every posterior to the fabricated 1.75 default rather than blocking.

---

## 3. Leverage — computed but unread / read but NULL

### 3a. Column census, canonical chart (139 rows)

| Column | Populated | Status |
|---|---|---|
| `karmic_frame`, `karmic_note` | **0 / 139** | read by 2 serving surfaces → always NULL |
| `subsystem_source` | **0 / 139** | never written by any code path; never read |
| `school_consensus_jsonb` | 139 × `{}` | hardcoded `None` at `ph_nimitta.py:729` |
| `dasha_consensus_count` | 139 × `0` | hardcoded `0` at `ph_nimitta.py:728` |
| `ayanamsha_robustness` | 139 × `3` | hardcoded default at `ph_nimitta.py:730` |
| `posterior`, `lift_vector_jsonb`, `confidence_low/high` | 139 / 139 | **computed, then suppressed at serve time** |
| everything else | 139 / 139 | populated |

Cross-checked on Abhinandan `1c826d5a` (56 rows): `karmic_frame` 0/56, `subsystem_source` 0/56,
`school_consensus` 56×`{}`, 1 distinct `dasha_consensus_count`, 1 distinct `ayanamsha_robustness`.
**Systematic, not chart-specific.**

### 3b. The largest leverage finding: 100% posterior suppression

`platform/src/lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts:27`:
```ts
export const CALIBRATED_CONFIDENCE_BASES: Set<string> = new Set([])
```
Every row's `isCalibrated` is therefore `false`, so `posterior`, `confidence_low`,
`confidence_high`, `lift_vector_jsonb` are all replaced with `null` before serving (`:200-208`).
Live: `confidence_basis = 'structural_not_yet_empirical'` on **139/139** rows.

The entire BA-P5B posterior model — base_rate × promise × activation × trigger × robustness — is
computed at build and never reaches a caller through this capability, nor through
`phala_predictive_anchors_get` (`register_p1_aliases.ts:1298`), nor through the retrieval **spine
bundle** (`compute_spine_bundle.ts:109-115`, `top_k:150`). The spine's `phala_anchors` section
carries `posterior: null` on every anchor for every chart.

This is *honest* (`posterior_provenance_note` correctly says "suppressed at serve time"), but the
layer's headline output is dark on its primary surface while the second, older surface
(`fetch_anchors`, `brahmagyan/phala/anchors.py:189-205`) serves the same values unsuppressed.

### 3c. `karmic_frame` — a 100%-miss key lookup

`ph_nimitta.py:722` passes `cgm['paths'][0]['path_label_human']` into `engine.py:186`'s
`_KARMIC_FRAME.get(root_graha.lower().strip())` — a bare-planet dict. Live values are
`"Saturn → Venus → Jupiter (final dispositor)"`, `"Ketu → Mars → Venus → Jupiter (final dispositor)"`.
**Zero hits, 100% of the time, on both charts.** Meanwhile `query_predictive_anchors.ts:143` SELECTs
`karmic_frame, karmic_note`, and both the capability and MCP tool descriptions promise "karmic frame"
per anchor (`register_p1_aliases.ts:1299`).

### 3d. `trigger_lift` is constant 1.0 while its input sits in the fetched row

`ph_nimitta.py:415-418` states: *"av_transit_potency has no real scalar source anywhere in the
codebase… fabricating one would violate B.10."* Consequence verified: `trigger_lift = 1.0` on 139/139.

But `_load_convergence` (`:301`) already SELECTs `constituent_factors`, whose live key set is
`dignity_score, mode, planet, sav_bindhu, sav_score, sav_threshold, sign, signature_class, sign_num`.
`sav_bindhu`/`sav_score`/`sav_threshold` is precisely an AV-transit gate scalar, already in hand,
discarded. *(This asserts a source exists, NOT that the mapping is trivially correct — that is a W2
design question.)*

### 3e. `direction` is a constant for 94% of rows

**0 / 14,868** `kala_convergence` rows have a `direction` key (or a `domain` key) in
`constituent_factors`. `engine.py:461`'s `raw_dir = cf.get('direction')` is always `None` →
`direction='mixed'` on all 131 convergence anchors. Confirmed: `convergence → mixed` (131),
`bhavishya → elevated` (4), `discovery → elevated` (4). The P0-11 "honest neutral" fallback is not a
fallback; it is the only branch. `direction` is an input filter on the serving tool
(`query_predictive_anchors.ts:70`) that can only ever return two partitions.

### 3f. Axis 5 (`precedent_refs_jsonb`) is self-referential

`ph_nimitta.py:564-597` — docstring says *"Axis 5: nearest embedding neighbors (top-3 per signal)"*.
The SQL does no vector search; it selects `e.signal_id` to "just confirm signal existence" (`:572`)
and returns `{'nearest_signal_ids': [sid], 'precedent_dates': []}` — **the signal cites itself as its
own precedent**. Verified on a live row where `nearest_signal_ids[0]` equals the row's own
`signal_id`. `ph_phaladesa.py:337` reads this column.

### 3g. Axis 3 (`causal_chain_jsonb`) is chart-constant

`_load_cgm_meta` returns a chart-level aggregate (correctly documented as CONTRACT-3), so every
anchor carries the identical 10 `cgm_path_ids` and identical `root_graha`. Per-anchor causality is
not modeled; the field's shape implies it is.

---

## 4. Grounding labelability

**No tier column exists.** No `grounding_tier`, no `classical_sources_array`, no
`constituent_facts_array`, no `text_citation` on `phala_anchors` (full census run). Only:

- `source_citation` (NOT NULL) — always populated, points **L3** (`kala_convergence/…`,
  `kala_bhavishya/{id}`, `bodha_discoveries/{id}`, or an inherited `mode_d/av_bindhu/…`). Never an
  L1 `fact_id`, never a classical text.
- `derivation_ledger_jsonb` (NOT NULL, never `{}`) — carries `convergence_id`, `signal_id`,
  `axes_applied`, `elevations`, `posterior_inputs`. Again no L1 fact reference.

**Honest tier per output class, if the vocabulary were added:**

| Output class | Honest tier | Why |
|---|---|---|
| `window_start/peak_date/window_end`, `convergence_id` | **`yukti`** | inherited unchanged from L3 computation |
| `magnitude` / `magnitude_basis` | **`pratyaksa`** | `rarity_years × effective_score` with hardcoded 0.60/0.40/0.20 cut-points (`engine.py:157-166`) — instrument-invented banding |
| `posterior` / `lift_vector_jsonb` | **`pratyaksa`** | BA-P5B product model is the instrument's own; `_promise_lift`'s 2.5× ceiling and `_activation_lift`'s 5-system cap are engineering constants |
| `karmic_frame` / `karmic_note` | **`sruti`** if populated | `_KARMIC_FRAME` (`engine.py:171-181`) is classical graha-karaka doctrine — but carries **no citation** and is 0% populated |
| `malleability` | **`pratyaksa`** | `_INFLUENCEABLE_DOMAINS = {career, health, transition, wealth}` (`engine.py:200`) is an undocumented instrument choice |
| `falsifier` / `structured_falsifier_jsonb` | **`pratyaksa`** | template-generated refutation condition, instrument-native, correct as such |
| `direction`, `dasha_consensus_count`, `ayanamsha_robustness`, `school_consensus_jsonb` | **none — these are constants, not claims** | §3e / §3a |

Of ~7 output classes, exactly one (`karmic_frame`) would earn `sruti`, and it is the one that never
fires. **Nothing in L4 is currently labelable without a schema addition.**

---

## 5. Temporal consumption (Discovery D-7) — **VERDICT: NOT CONSUMED**

**Proven absence.** Exhaustive case-insensitive grep for
`varshaphala|varsha|tajaka|tithi_prave|muntha|patyayini|saham|annual` across
`writers/ph_nimitta.py` and all four `services/ph_nimitta/` files → **ZERO MATCHES.** None of the 9
declared deps nor the 3 undeclared reads is a Tajaka/varsha asset. The 11 table reads in §2 contain
no varsha table.

**Meanwhile the upstream data exists and is built for this chart:**

| table | rows | asset | state |
|---|---:|---|---|
| `l1_tajik_varsha_year_lords` | 240 | `ga_tajaka` | stale, built 2026-08-12 |
| `kala_tithi_pravesha` | 120 | `ka_tithi_pravesha` | lit, built 2026-08-12 |
| `kala_sudarshana_varsha` | 120 | `ka_sudarshana_varsha` | lit, built 2026-08-08 |

**The near-misses, precisely:**

1. **`ka_sangam` reads it; `ph_nimitta` cannot see it.** `ka_sangam.py:1066` reads
   `l1_tajik_varsha_year_lords (varsha_year, varshesha, muntha)`; `:46` defines a `saham_activation`
   additive current. That evidence never reaches the anchor: **0/14,868** `kala_convergence` rows
   carry `varsha`/`muntha`/`tajak` in `constituent_factors`; 1,994 carry `saham`, of which only
   **10** back a surviving anchor — and the engine reads `constituent_factors` only for
   `.get('domain')` and `.get('direction')`, both always absent. Even those 10 discard the evidence.
2. **The subsystem tag is one unselected column away.** `bodha_msr_signals.source_subsystem` is the
   taxonomy `bo_laksana.py:193` populates (`"ga_tajaka" → "tajaka"`) and `mi_adhilepa.py:73` reads.
   `ph_nimitta._load_signal_meta` (`:388-398`) selects only
   `ayanamsha_id, domains_affected_array[1], signature_class, computed_salience` — **not
   `source_subsystem`**. That is exactly why `phala_anchors.subsystem_source` is 0/139. *(On this
   chart the built signal subsystems are structural, nakshatra, sade_sati, panchanga, varga, yoga,
   jaimini, special_lagna — no `tajaka` signals present, so this is a plumbing gap, not a data gap,
   today.)*

**For the record: NOT consumed. Zero code path.** The absence is at `ph_nimitta.py:388-398` (signal
meta select) and in `depends_on` (no varsha asset declared).

---

## 6. Service

**Downstream writers (9, all verified):**

| Consumer | Reads |
|---|---|
| `ph_sodhana.py:105-109` | `confidence_low/high/basis, magnitude, falsifier, derivation_ledger, dasha_consensus_count, ayanamsha_robustness, convergence_id` |
| `ph_pramana.py:128-131` | `falsifier, windows, magnitude, confidence_high, derivation_ledger` |
| `ph_pratikara.py:202` | `domain, magnitude, malleability` |
| `ph_muhurta.py:239` | `domain, malleability, dates` |
| `ph_sankrama.py:163` | `domain, confidence_high, dates` |
| `ph_suddha_sodhana.py:123` | `anchor_id` |
| `ph_phaladesa.py:334-344` | + `precedent_refs_jsonb, contradiction_jsonb` |
| `mi_pariksha.py:187-188, 472` | **`posterior, lift_vector_jsonb`** — L5 *does* consume the posterior |
| `mi_bhavisya.py:73`, `mi_adhilepa.py:317`, `mi_kula` | `SELECT *` / `anchor_id` |

**Serving surfaces (3):** `query_predictive_anchors` → `phala_predictive_anchors_get` (MCP);
`compute_spine_bundle` (`SPINE_SOURCE_ASSET_IDS` includes `ph_nimitta`, `constants.ts:50`);
`event_anchors` / `phala_anchors_get` (legacy sidecar path).

**Floor:** `target_floor` / `expected_volume_formula` / `expected_volume_inputs` /
`integrity_check_sql` all NULL — identically so on all nine `ph_*` assets. `expected_rows` NULL in
`asset_throughput` too. There is no volume assertion of any kind, so C12 is not *violated* — it is
unaddressed. A DERIVED formula is now computable (F-13).

**`density_contract`:** absent. `query_predictive_anchors.ts:159-192` has an excellent 4-branch
`empty_reason` + `known_gap: 'CR-66'` + `backing_data_reachable`, and
`register_p1_aliases.ts:1326-1332` adds a defensive floor — but no `density_contract` declaration, so
none of it is machine-assertable, and there is no `hardFloor` on any section.

**≤2-hop L1 drill:** `phala_anchors.signal_id` → `bodha_msr_signals.constituent_facts_array` →
`chart_facts.fact_id` = 2 hops. Verified: 11 distinct signals back all 135 signal-bearing anchors;
11/11 have `constituent_facts_array`. Works for **135/139**. The **4 discovery-sourced anchors have
`signal_id` NULL** (`SELECT NULL::uuid AS signal_id`, `ph_nimitta.py:352`) — no ≤2-hop path to L1 at
all. Also: 139 anchors resting on **11** distinct L2 signals is a very narrow grounding base.

---

## 7. Measured cost

**Build cost: unmeasured.** `asset_throughput` for all three charts: `rows_per_second` NULL,
`measurement_count` 0, `last_measured_at` NULL. `estimated_seconds=3` is a declaration with zero
measurements behind it. `built_against_writer_hash` is `'unknown'` (canonical) / `''` (Abhinandan) —
the staleness detector has no real baseline for either.

**Work actually done** (derived from live source cardinalities): 260 convergence candidates
(`PARTITION BY domain, rn≤50` over domains sized 9221/4153/956/478-null/27/25/8) + 100 bhavishya
(ALL, per D37) + 100 discoveries = **~460 anchors derived → 139 stored (≈70% rejected)** by the T-5
clip gate (`:766`) and the CR-46 content dedup (`:207`). Plus 6 per-signal batch lookups and one
per-discovery proximity subquery. `SET LOCAL statement_timeout = 0` (`:127`) means a pathological
chart cannot time out.

**Serve cost:** cheap and well-indexed. 8 indexes on `phala_anchors`, including `(chart_id,domain)`
**twice** (`phala_anchors_domain_idx` and `idx_phala_anchors_domain` are byte-identical duplicates —
a free drop), `(chart_id,peak_date)`, and a partial `(chart_id,malleability) WHERE
malleability='influenceable'`. `ORDER BY magnitude DESC` is unindexed but trivial at 139 rows.
`query_predictive_anchors` issues a second `count(*)` only on empty results — correct.

---

## 8. Prediction-provenance hygiene (parked-P7 seam) — **VERIFIED, NOT MODIFIED**

**Identity columns present:** `anchor_id` (uuid PK), `convergence_id`, `discovery_id`,
`bhavishya_id`, `signal_id`, `derivation_ledger_jsonb`, `structured_falsifier_jsonb`, `falsifier`
(NOT NULL), `source_citation` (NOT NULL), `computed_at` (NOT NULL). All populated except `signal_id`
(135/139) and `discovery_id`/`bhavishya_id` (source-specific, correct).

**The forward chain to the falsifiability loop is INTACT and complete:**

```
phala_anchors.anchor_id  →  phala_pramana.anchor_id  →  mimamsa_predictions.source_pramana_id
      139 rows                139 rows / 139 with anchor_id      139 rows / 139 with source_pramana_id
```

1:1:1 across the whole chart. `phala_sodhana` (97), `phala_sankrama.source_anchor_id`,
`phala_suddha_sodhana` all key on `anchor_id`. No L5 table carries `anchor_id` directly, so an
outcome→anchor join is 2 hops via `phala_pramana` — reachable, but not obvious.

**Two seam defects found (report only, do not touch):**

1. **`brahma_prospective_ledger` (19 rows for this chart) has no `anchor_id`, no `pramana_id`, no
   `prediction_id` FK to `mimamsa_predictions`.** Its identity space (`prediction_id`,
   `generator_class`, `configuration_signature`) is disjoint from the L4 anchor space. A prediction
   filed into the live ledger cannot be traced back to the anchor that motivated it.
   `registry_data.ts:797-799` records that `standing_predictions_read` was *repointed off*
   `phala_predictive_anchors_get` onto this ledger precisely because they are different things — the
   repoint is correct, but it leaves the two surfaces unjoined.
2. **A second, orphaned write path into `phala_anchors` exists and is live-routed.**
   `seed_native_phala_anchors(uuid)` is a deployed plpgsql function that inserts **hand-authored,
   hardcoded, native-specific predictions with hand-assigned scores**, citing the *deleted* FORENSIC
   v8.0 markdown. It targets columns (`theme`, `confidence`, `contributing_dashas`,
   `contributing_signals`, text `anchor_id`) that **no longer exist** — migration 330 replaced them.
   It is therefore currently broken-by-schema, but reachable at
   `POST /api/compute/phala/seed_anchors` (`brahmagyan/phala/anchors.py:588-597`, router mounted
   `main.py:52`) and from `seedNativeAnchors()` in `platform-mcp/src/tools/phala_event_anchors.ts:221-225`.
   `anchors.py:511-517`'s acceptance gate exercises it. **This is the seam's worst condition:
   hand-written predictions with fabricated confidence, presented as built output, have a live named
   endpoint, held back only by a schema mismatch.**

   > **CORRECTION (2026-09-05, W3).** This finding originally also claimed the AC5 acceptance gate
   > *"asserts idempotency PASS over a function that cannot succeed"* — and that claim was carried
   > into adjudication #1739 and repeated in the Conductor's ruling. **It is wrong.** The call
   > raises, `except Exception` catches it, and the check appends `"passed": False` with the error
   > text: AC5 reported FAILED, correctly and loudly, every time it ran. Verified by executing the
   > function against production in a rolled-back transaction (`ERROR: column "theme" of relation
   > "phala_anchors" does not exist`). The finding's substance — a live fabrication path held back
   > only by a schema mismatch — stands and was ruled on; the false-PASS characterisation does not.
   > Corrected in PR #1771 and on #1739. A third call site the ruling did not name
   > (`brahma_pipeline._l4_phala`) was also found and severed there.

---

## 9. Findings → W2

| # | Finding | Triage | Doctrine | Evidence |
|---|---|---|---|---|
| **F-1** | `_spine_gate`'s docstring claims it verifies "ALL 5 elevations… (magnitude, confidence range, **karmic_frame**, malleability, falsifier)" but the code checks `magnitude, posterior, lift_vector, malleability, falsifier, derivation_ledger` — **`karmic_frame` is never checked**. Had it been, the gate would fail on 100% of builds. A D26 hard gate whose stated claim has no detector. | **MUST** | §N.8 | `ph_nimitta.py:826-846` vs `karmic_frame` 0/139, 0/56 |
| **F-2** | `CALIBRATED_CONFIDENCE_BASES` is an empty `Set`, nulling `posterior`/`confidence_low`/`confidence_high`/`lift_vector_jsonb` on **139/139** served rows — including inside the retrieval spine bundle. The layer's headline computation is 100% dark on its primary capability, while `event_anchors`/`phala_anchors_get` serves the same values raw. Two surfaces, contradictory policy. | **MUST** | D-SYNTHESIS, D-SERVICE | `query_predictive_anchors.ts:27,200-208`; `confidence_basis` ×139; `anchors.py:189-205` |
| **F-3** | `ORDER BY magnitude DESC` on a **TEXT** column sorts `pivotal > moderate > minor > major`. Verified: the default `top_k=50` page returns **45 minor + 5 moderate + 0 of the 3 `major` anchors**. The densest rows are exactly the ones the trim discards. | **MUST** | §N.6 (2) | `query_predictive_anchors.ts:151`; re-ran the serving ORDER BY |
| **F-4** | `karmic_frame` lookup passes a full path label (`"Saturn → Venus → Jupiter (final dispositor)"`) into a bare-planet dict → **0% hit rate on both charts**, while two tool descriptions advertise "karmic frame" per anchor. | **MUST** | §N.7 (4), §N.8 | `ph_nimitta.py:722` + `engine.py:186`; `bodha_cgm_paths.path_label_human` |
| **F-5** | `pratijna_grade=5.0` / `pratijna_status='conditional'` are applied when **no** `bodha_pratijna` row exists, yielding `promise_lift = 1.75` — a **75% posterior amplification derived from no evidence**. 54/139 rows sit at exactly 1.75. The honest neutral (`status='no_evidence'` → lift 1.0) already exists in `_promise_lift`. | **MUST** | §N.7 (6) | `ph_nimitta.py:745-746`; `engine.py:249-251`; `lift_vector_jsonb` census |
| **F-6** | Three context fields are hardcoded constants marked "for now": `dasha_consensus_count=0` (139×0), `school_consensus_jsonb=None` (139×`{}`), `ayanamsha_robustness=3` (139×3, comment says "real value comes from kala_convergence row" — it does not). `ph_sodhana`'s G-LADDER confidence-inflation check consumes two of them, so that check grades against a constant. **`services/ph_nimitta/dasha_consensus.py` (164 ln, fully tested) is never imported by the writer.** | **MUST** | §N.8, §N.7 (6) | `ph_nimitta.py:728-730`; `ph_sodhana/engine.py:115-139`; grep: zero import |
| **F-7** | `direction` is constant `'mixed'` on all 131 convergence anchors because `kala_convergence.constituent_factors` has **0/14,868** rows with a `direction` key. The serving tool exposes `direction` as a filter that can only partition two ways. Separately, `derive_anchor_from_discovery` still hardcodes `direction='elevated'` — the exact favorable-sounding default P0-11 fixed for convergence. | **MUST** | §N.7 (6) | `engine.py:461-462`, `:744`; `constituent_factors ? 'direction'` → 0 |
| **F-8** | `av_transit_potency=0.0` is justified as "no real scalar source anywhere in the codebase" → `trigger_lift=1.0` on 139/139. But `_load_convergence` already fetches `constituent_factors` containing `sav_bindhu`, `sav_score`, `sav_threshold`. The claimed absence is falsified by the row in hand. | **NOW** | §N.7 (3), B.10 | `ph_nimitta.py:415-418, 301`; `jsonb_object_keys` census |
| **F-9** | 4 discovery-sourced anchors have `signal_id NULL`, so they have **no ≤2-hop L1 drill path**. All 139 anchors rest on just **11** distinct L2 signals. | **NOW** | D-SERVICE, §N.5 | `ph_nimitta.py:352`; `COUNT(DISTINCT signal_id)`=11 |
| **F-10** | No `derivation_ledger_jsonb` entry cites an L1 `fact_id`; the ledger cites `convergence_id` + `signal_id` only and `source_citation` points L3. §N.5's "REFERENCE the L1 fact_id" is satisfied only transitively. **(I found NO case of an L1 value being re-derived — §N.5's inversion trap is clean.)** | **NOW** | §N.5, B.3, D-GROUNDING | `jsonb_pretty(derivation_ledger_jsonb)` sample |
| **F-11** | Two independent serving estates read `phala_anchors` with different column sets, filters and provenance envelopes. `phala_event_anchors.ts:8-11`'s header still documents the **pre-migration-330 schema**. | **NOW** | D-SYNTHESIS | `anchors.py:186-205`; `phala_event_anchors.ts:8-19` |
| **F-12** | `seed_native_phala_anchors()` — hand-authored predictions with hand-assigned confidences inserted into `phala_anchors`, citing the deleted FORENSIC v8.0 — is live-routed at `/api/compute/phala/seed_anchors` and blocked only by a schema mismatch. Its acceptance gate asserts idempotency PASS over a function that cannot run. **Verify-only per the P7 parking; do not modify in W2 without an explicit ruling.** | **MUST** (raise, don't fix) | §N.8, B.10, prediction-provenance | `pg_get_functiondef`; `anchors.py:386-400, 511-517, 588-597`; `main.py:52` |
| **F-13** | `target_floor` / `expected_volume_formula` / `expected_volume_inputs` / `integrity_check_sql` all NULL — identically on all 9 `ph_*`. A DERIVED formula is computable: `Σ_domain min(50, |kala_convergence(domain)|) + |kala_bhavishya| + min(100,|bodha_discoveries|)`, minus gate/dedup attrition (~460 → 139). Never a `count(*) = 139` pin. | **NOW** | C12, D-SERVICE | registry query; source cardinalities `14868 / 100 / 856` |
| **F-14** | The ~70% attrition (T-5 clip + CR-46 dedup: 100 bhavishya→4, 100 discoveries→4) is logged to stdout only. Nothing in the DB or the served envelope records what was rejected or why, so `anchor_count: 139` is a post-rejection number a caller cannot interrogate. The dedup key deliberately excludes `bhavishya_id`/`discovery_id`/`signal_id`, so distinct upstream projections agreeing on content collapse. | **NOW** | §N.6 (1,3) | `ph_nimitta.py:42-87, 766-824` |
| **F-15** | `subsystem_source` is declared on `AnchorRecord`, bound in the INSERT, and **set by nothing** — 0/139 and 0/56. `bodha_msr_signals.source_subsystem` is one unselected column away in `_load_signal_meta`. This is also the concrete plumbing gap behind D-7. | **NOW** | D-GROUNDING, §N.8 | `engine.py:405`; `ph_nimitta.py:225,256,388-398` |
| **F-16** | **D-7 / varshaphala: NOT CONSUMED.** Zero references in the writer or any `services/ph_nimitta/` file. `l1_tajik_varsha_year_lords` (240), `kala_tithi_pravesha` (120), `kala_sudarshana_varsha` (120) are all built for this chart and none is a declared dep or a table read. The only trace is `saham` in 1,994 convergence rows, of which 10 back a surviving anchor — and the engine reads that JSONB only for two keys that are never present. | **MUST** (named L4 mandate) | D-TIME | exhaustive grep = ZERO; three `count(*)` + `asset_throughput` |
| **F-17** | `bo_karanajala` and `bo_samskara` are declared deps with no table read; conversely `bodha_pratijna`, `kala_activation_predicates`, `brahma_event_ontology` are read but undeclared — and supply the two largest posterior multipliers. A `bo_pratijna` failure degrades every posterior silently instead of blocking. | **NOW** | D-SERVICE | `depends_on` vs the 11 verified reads |
| **F-18** | Axis 5 `precedent_refs_jsonb` returns the signal's **own id** as its nearest precedent (`precedent_dates` always `[]`); the docstring promises "nearest embedding neighbors (top-3)". No vector search is performed. `ph_phaladesa` reads this column. | **NOW** | §N.8, §N.7 (4) | `ph_nimitta.py:564-597`; sampled row |
| **F-19** | Axis 3 `causal_chain_jsonb` is chart-constant (same 10 `cgm_path_ids`, same `root_graha` on every anchor) — correctly documented in code as CONTRACT-3, but the per-anchor field shape implies per-anchor causality it does not have. | **NEVER-LATER** | §N.6 | `ph_nimitta.py:481-530, 709-711` |
| **F-20** | `rows_inserted += 1` unconditional after `ON CONFLICT DO NOTHING` against a 6-column unique natural key; `cur.rowcount` never consulted. On this chart the number happens to be right (139 == 139) — an unearned signal that is not currently lying. | **NEVER-LATER** | §N.8 | `ph_nimitta.py:252,270`; `phala_anchors_natural_key` |
| **F-21** | No build-cost measurement exists on any chart; `built_against_writer_hash` is `'unknown'`/`''`, so the staleness detector has no baseline. `estimated_seconds=3` is undeclared-provenance. `SET LOCAL statement_timeout = 0` removes the only backstop. | **NEVER-LATER** | §N.8 | `asset_throughput` |
| **F-22** | `phala_anchors_domain_idx` and `idx_phala_anchors_domain` are byte-identical duplicate indexes on `(chart_id, domain)`. | **NEVER-LATER** | hygiene | `pg_indexes` |
| **F-23** | `query_predictive_anchors` has best-in-class `empty_reason`/`known_gap`/`backing_data_reachable` disclosure but declares **no `density_contract`** and no `hardFloor` — so none of it is machine-assertable, and F-3's trim has no floor to respect. | **NOW** | §N.6 (4) | `query_predictive_anchors.ts:159-192` |
| **F-24** | Canonical `ph_nimitta` is `state='stale'` (built 2026-08-13) while served descriptions across 9 generated projections hardcode "phala_anchors (150 rows)" — actual 139. | **NEVER-LATER** | C12-adjacent | `asset_throughput`; `query_predictive_anchors.ts:35` |

---

## 10. Verified vs inferred

**Verified** (query or `file:line` given above): every row count, every column census, the empty
allowlist and its 100% suppression, the magnitude sort inversion (re-ran the exact serving ORDER BY),
the karmic_frame key mismatch, the `constituent_factors` key set, the promise_lift distribution, the
D-7 absence (exhaustive grep) and the presence/population of the three varsha tables, the
`seed_native_phala_anchors` body, the anchor→pramana→prediction 1:1:1 chain, all 11 table reads, all
9 downstream consumers, and the index list.

**Inferred, not verified:** the mapping `bodha_contradictions`→`bo_sangati` and
`bodha_signal_embeddings`→`bo_bimba` (matched by convention, not by reading those writers) — so
F-17's "2 of 9 unused" could be "4 of 9" if those attributions are wrong. Also unverified: whether
`sav_bindhu` is a *correct* `av_transit_potency` input (F-8 claims only that a source exists), and
whether `ph_muhurta`/`mi_kula` read additional columns beyond their visible SELECT.
