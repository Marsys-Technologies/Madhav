---
artifact: L3_W1_ANALYSIS_BATCH_A
canonical_id: L3_W1_ANALYSIS_BATCH_A
version: "1.0"
status: DRAFT-FOR-W2
produced_on: 2026-09-05
campaign_id: nirmana-elevation
layer: L3
batch: A
theme: "The gochara family — v1 archive, v2 materializer, v3 century monster, resonance root"
assets:
  - ka_gochara_resonance
  - ka_gochara
  - ka_gochara_sweep
  - ka_gochara_v3_century_materialize
measurement_basis: "live production DB via .l3-tools/q.sh (role amjis_app, SELECT-only), 2026-09-05; repo worktree /Users/Dev/nirmana-s/l3"
---

# L3 W1 ANALYSIS — BATCH A: the gochara family

> Every number below came from a query or a file read performed in this session. Anything
> not measured is written **unmeasured**. VERIFIED vs INFERRED is marked inline.

## Batch summary

1. **The v1 archive is NOT where the mandate says it is, and "17,240" is the wrong number.**
   VERIFIED: the `ka_gochara_sweep` v1 corpus lives **inside the live serving table**
   `kala_gochara_windows` under `generation='v1'` — **38,287 rows across 3 chart_ids**
   (native `482012f1` = 16,297; Abhinandan `1c826d5a` = 19,323; orphan `cb73cd3d` = 2,667).
   `kala_gochara_windows_archive_20260805` (35,620 rows) is a **byte-exact snapshot of the
   two canonical charts' v1 rows** — id-sets are md5-identical (`a6d0850…` / `7aa55c2…` on
   both sides). The mandate's **17,240 = 16,297 v1 + 943 gen-3.0** — i.e. the native chart's
   *whole-table* row count, not the v1 archive. **Corrected figure: v1 corpus = 38,287 rows;
   snapshotted = 35,620; UNSNAPSHOTTED = 2,667 (chart `cb73cd3d`).**

2. **The DB-level hard floor protecting that corpus was REMOVED on 2026-08-23 and nothing
   replaced it.** VERIFIED: migrations `588_remove_asset_build_protection.sql` (applied
   2026-08-23 05:33) + `589_drop_orphaned_protection_functions.sql` (05:34) dropped every
   trigger; `SELECT … pg_trigger … relname LIKE '%gochara%'` returns **0 rows**;
   `build_gen3_gochara_guard_row`, `build_protected_assets_guard_row`,
   `build_protected_assets_guard_truncate` **do not exist**; `build_protected_assets` is
   **empty (0 rows)**. The campaign's own "no destructive operation on the v1 corpus" rail is
   currently enforced by *discipline plus one snapshot table*, not by the database.

3. **97.3% of every served gochara row has no explanation attached.** VERIFIED: of the 1,884
   `generation='3.0'` rows (the authoritative served set for both canonical charts),
   **1,830 have `active_sentences` = empty and `contributing_systems` = empty**; only the 54
   stale orphan rows carry them. The v1 corpus, by contrast, is 99.5%/100% populated on the
   same two fields. **The cutover traded away the entire drill/attribution layer.** A claim
   served from a 3.0 row cannot drill to L1 in ≤2 hops — it cannot drill at all.

4. **`ka_gochara`'s cockpit count reads rows its writer never wrote.** VERIFIED: the writer
   (`writers/ka_gochara.py`) writes **only** `kala_gochara_windows_v2` at
   `GENERATION_V2='2.0'` (measured: 83 rows native / 25 Abhinandan). Its registry row says
   `target_table='kala_gochara_windows'` and
   `count_sql = … WHERE chart_id=$1 AND generation='3.0'` → **943 rows**, all of which were
   written by `ka_gochara_v3_century_materialize`. Both directions are wrong: the cockpit
   over-reports ka_gochara 11×, and ka_gochara's real output is counted by nobody. §N.4
   "Cockpit truth" / §N.8 Earned-Signal.

5. **The century materializer hardcodes the native's birth epoch — Abhinandan's century is
   13 months wrong.** VERIFIED: `BIRTH_JD = 2445736.5` and `BIRTH_YEAR = 1984` are module
   constants (writer lines 423/426), never read from `ctx.config['birth_params']`.
   `charts.birth_date` for `1c826d5a` is **1985-03-02**, yet his
   `kala_gochara_v2_build_state.horizon_start_date` is **1984-02-05** and his g3 windows start
   **1984-02-05 — 13 months before he was born**. §N.7 item 3 (a wrapper-local constant
   shadowing a computed value) and a per-chart-portability blocker for "click Build".

6. **Four of the century materializer's six declared dependencies are dead edges.** VERIFIED:
   `ka_moorti_nirnaya`, `ka_kota_chakra`, `ka_tithi_pravesha`, `bg_sky_calendar` are declared
   in `depends_on` but **no code path reads their tables**; the mechanisms that would
   (`w22`, `w25`, `w26`, `w27b`) are all `admission_state: candidate` and only `w23_tara_bala`
   + `w30_nodal_drishti` are imported by `engine.py`. `gochara_v3_calibration` independently
   confirms it: **all 30 rows have `weight_value = 0.000000`**.

7. **`kala_gochara_windows_v2` is never read by any serving code.** VERIFIED by grep across
   `platform/src` + `platform-mcp/src` (0 non-test hits). Both writers that target it
   (ka_gochara's 108 rows of gen-2.0, the century writer's 1,830 g3_utkarsha staging rows)
   produce output with **zero consumers**.

8. **No L3 asset has a provenance receipt and no gochara asset has an integrity check.**
   VERIFIED: `asset_provenance_receipts` holds **25 rows / 24 assets total, 0 of them `ka_*`**.
   All four batch assets have `integrity_check_sql = NULL`, `expected_volume_formula = NULL`,
   `expected_volume_inputs = NULL`, `target_floor = 0`. Meanwhile real invariant violations
   exist and are undetected: **16 rows** (15 v1 + 1 gen-3.0) where `peak_date` falls outside
   `[window_start, window_end]`.

---

## ka_gochara_resonance

**One-line identity:** The per-chart × event-class *target set* — which bhavas, lords, karakas,
transit-rule nodes, sensitive degrees, arudhas, yoga constituents and dasha-lord portfolios a
transiting graha must contact for a given life-event class to resonate. It is the **root** of the
entire gochara family: every downstream writer's `plan_substeps` is gated by what this table holds.

**Temporal question (D-TIME):** *"For this chart, WHICH natal targets must a transit touch before
event-class E can be said to be timing at all?"* — a question about the **standing structure of
susceptibility**, not about a date. It is the only member of this batch that answers a
time-independent question.

**Measured state:** `gochara_resonance_map` = **1,589 rows / 3 charts**: native 762 (27 classes),
Abhinandan 750 (27), orphan `cb73cd3d` 77 (3). 8 `target_type` values. Unique key
`(chart_id, event_class, target_type, target_ref)`.

1. **Instrument fit** — serves **D-GROUNDING P3** (it is the join point between L0 classical rule
   corpora and L1 chart facts), **D-TIME P6** (it defines what the temporal engines are allowed to
   look for), and **D-SALIENCE P5** (its `weight` column is the only prior in the family). Still
   the right instrument — but its *weighting* claim is thinner than its name implies (see 4).

2. **Dependencies (declared vs real)** — declared `depends_on = {bg_transit_rules}`. **Real reads,
   from `services/ka_gochara_resonance/writer.py`:** `brahma_event_ontology` (L0, owner
   `bg_ghatana`), `bg_transit_rules` (L0, declared ✓), `chart_facts` (L1, two separate queries —
   sensitive degrees and arudhas), `ga_yoga_firings` (L1, owner `ga_yoga`), `chart_dashas` (L1,
   owner `ga_dashas`). **Four undeclared hidden edges**, three of them L1 → this asset silently
   depends on the entire L1 chart build and the DAG does not know it. A rebuild ordering that
   runs this before `ga_yoga`/`ga_dashas` produces a silently thinner map with no error.

3. **Leverage / NULL check** — `weight IS NULL`: **0 rows** (good). `source_rule_id IS NULL`:
   **1,393 / 1,589 = 87.7%** — only `mechanism_node` rows (196) carry a rule id.
   **The weight column is 87.8% constant.** For the native chart:
   `bhava`/`karaka`/`lord` = 1.0 exactly (161 rows), `yoga_constituent` = 0.7 exactly (220),
   `sensitive_degree` = 0.5 exactly (176), `dasha_lord_portfolio` = 0.8 exactly (44),
   `arudha` = 0.6 exactly (68) — **669 of 762 rows carry one of five hardcoded literals**; only
   `mechanism_node` (93 rows) has a real distribution (min −1.0, max 1.0, mean 0.296). The
   asset's own manifest description calls these "classical-prior-weighted target sets"; the
   prior is real for 12.2% of rows and a constant for the rest. That is not a fabrication (the
   constants are declared, not invented per-row) but it *is* a signal with far less information
   than its consumers assume.
   **The genuine leverage loss:** its `weight` reaches serving **nowhere**. No TS file selects
   `gochara_resonance_map.weight`; the only serving read
   (`register_gochara_windows.ts:1007`) selects `DISTINCT event_class` for a coverage facet.
   The one column that carries salience is computed and never consumed.

4. **Grounding tier** — honestly self-labelling already, and this is the family's best example.
   `uncited_extension = true` ⟺ `classical_citation IS NULL` on **every one of the 1,056
   uncited rows** (496 + 508 + 52 — perfect correlation, VERIFIED). Tier mapping:
   `bhava`/`lord`/`karaka` (BPHS-cited via `brahma_event_ontology.citations`) → **śruti**;
   `mechanism_node` (verbatim `bg_transit_rules.classical_citation` + `source_rule_id`) →
   **śruti**; `sensitive_degree` / `arudha` / `yoga_constituent` / `dasha_lord_portfolio` →
   **pratyakṣa** (instrument-emergent linkage between an event class and an L1 primitive that
   is not keyed to that class anywhere in the source data). **66.7% of the native's map is
   pratyakṣa** and the writer already says so. This is what an honest label looks like.

5. **Temporal identity + arbitration** — it does not answer a *when* question, so it never
   disagrees with a temporal engine; it **constrains** them. Overlapping engines: none.
   **Arbitration role: it is the arbiter's substrate.** Every gochara engine's substep plan is
   `SELECT DISTINCT event_class FROM gochara_resonance_map WHERE chart_id = …`, so a class
   absent here is invisible to all of them — which is exactly why the S4-05 "I didn't look ≡
   there is nothing" defect had to be closed at this table. **For the Temporal Concordance
   Contract this asset is the single point where scope is declared**; the Contract should name
   it as the authoritative *scope register* and require every temporal engine to disclose its
   plan against it.

6. **Service** — no direct serving capability of its own. Read by
   `register_gochara_windows.ts` `computeGocharaCoverage` (coverage facet + `domain` refusal
   path) and whitelisted in `platform/src/app/api/mcp/db/query/route.ts` `ALLOWED_TABLES`.
   Read by 20 Python modules (measured), including every gochara writer, `ka_kshetra`,
   `permission_curve.py`, and `l0_transit.py`. **Real consumer, heavily so — not shelf
   inventory.** Its coverage read is the mechanism behind the `not_covered` honest refusal, so
   it *is* the family's empty-reason discipline.

7. **Measured cost** — `estimated_seconds = 1`. Real: all 762 native rows share
   `computed_at = 2026-08-12 22:24:17.693` (single-statement `executemany`), and
   `asset_throughput.last_built_at = 22:24:33.72` → **≈16 s wall clock** (INFERRED from the
   computed_at→last_built_at delta, which brackets the commit). 16× the estimate but
   absolutely cheap. Serve cost: one `SELECT DISTINCT` per gochara tool call, indexed by
   `idx_gochara_resonance_chart_event` — negligible.
   State: `asset_throughput` = `stale` on native (762 rows, 2026-08-12), `lit` on Abhinandan
   (750, 2026-08-11), `lit` on `cb73cd3d` (77, 2026-07-27).

8. **Findings**

   - **F-RESON-1 (MUST, D-GROUNDING P3 / C12)** — `depends_on` declares only `bg_transit_rules`;
     the writer really reads `brahma_event_ontology`, `chart_facts`, `ga_yoga_firings`,
     `chart_dashas`. Four hidden edges, three crossing into L1. Add them to `depends_on`.
     Without this, `compute_upstream_hash` (asset_runner.py:401, which hashes *declared* deps)
     cannot detect an L1 rebuild and the resonance map will silently serve a stale target set.
   - **F-RESON-2 (MUST, C12 / D-126)** — `integrity_check_sql IS NULL`. Real invariants
     available, none of them count-pins: (a) `uncited_extension = (classical_citation IS NULL)`
     must hold for every row — currently 100% true, so it is a live-and-passing check, not a
     pin; (b) every `target_type='mechanism_node'` row must have `source_rule_id` resolving to
     `bg_transit_rules.id`; (c) every `event_class` must resolve to
     `brahma_event_ontology.event_class_id` (currently 0 orphans); (d) `weight` must lie in
     [−1, 1] (currently true). Propose (a)+(c) as the check.
   - **F-RESON-3 (NOW, C12)** — `expected_volume_formula IS NULL`. Derivable from first
     principles: `rows ≈ Σ_over_event_classes (|bhavas(E)| + |lords(E)| + |karakas(E)|
     + |transit_rules matching E| + |sensitive_degrees| + |arudhas| + |yoga_firings ∩ E|
     + |distinct MD lords|)`, inputs `{brahma_event_ontology, bg_transit_rules, chart_facts,
     ga_yoga_firings, chart_dashas}`. If the exact form is contested, §N.4 permits the
     achieved-count floor: `target_floor = 762` (native, measured).
   - **F-RESON-4 (NOW, D-SALIENCE P5 / §N.6)** — `weight` is computed for every row and
     **read by no serving path**. Either surface it (the resonance targets behind a served
     window are exactly the drill layer §N.6 item 3 demands) or record honestly that it is
     an internal scoring input only.
   - **F-RESON-5 (NEVER-LATER, D-SALIENCE P5)** — 87.8% of weights are one of five hardcoded
     constants. Turning those into genuinely derived priors is a research task requiring
     outcome data (L5), not an L3 build task. Log with that reason; do not attempt in-layer.
   - **F-RESON-6 (NOW, hygiene)** — 77 rows for chart `cb73cd3d-9eba-4220-9902-0de91566e980`,
     which **does not exist in `charts`** (VERIFIED). Orphan per-chart data. Disposition
     decision needed; do not delete under W1.

**Route recommendation (W2 input):** `rebuild_only` — the writer's logic is sound and honestly
tiered; what it needs is registry truth (deps, integrity check, volume formula, floor) plus a
rebuild to clear the `stale` state on the canonical chart. It is a legitimate canary: cheap
(≈16 s), single-transaction, delete-then-insert idempotent, and its output is verifiable
row-for-row against a prior count (762). **Note for the E-GATE:** a rebuild of this asset
changes the substep plan of *both* downstream materializers, so run it as a canary in isolation
and re-measure before dispatching anything downstream.

---

## ka_gochara

**One-line identity:** The W2G/"GOCHARA-2.0" per-chart materializer — joins the chart-independent
monotone-arc contact stream (`bg_gochara_arcs`) against one chart's resonance targets, scores each
candidate instant through v1's unmodified `gochara_intensity.compute_lambda_e` grammar, and writes
a **±3-year progressive-horizon** window set.

**Temporal question (D-TIME):** *"Within the next three years either side of today, on which dates
does a real transit contact make event-class E's natal targets live?"* — the **near-horizon**
question.

**Measured state:** writes `kala_gochara_windows_v2` at `generation='2.0'`: **83 rows native
(27 substeps, 14 honestly skipped, 83 contacts evaluated, horizon 2023-08-13…2029-08-13), 25 rows
Abhinandan (6 substeps, 2 skipped, horizon 2023-08-06…2029-08-06)**, both `horizon_status =
'progressive_partial'`. Registry says `target_table = kala_gochara_windows`.

1. **Instrument fit** — designed for **D-TIME P6** at the actionable near horizon and
   **D-SERVICE P8**. In its current wiring it serves neither: its table is unread by serving,
   and its production-surface claim is held by a different writer. It is the right *idea*
   (a cheap, frequently-refreshable near-horizon layer beneath an expensive century layer),
   currently mis-plumbed.

2. **Dependencies (declared vs real)** — declared `{bg_gochara_arcs, ka_gochara_resonance}`.
   Real reads: `gochara_resonance_map` ✓ (via `services.gochara_grammar.resonance_map`),
   `bg_gochara_arcs` ✓ (`_fetch_arc_fingerprints`, and `DbArcSource`),
   `kala_gochara_v2_build_state` (own bookkeeping — not a DAG edge), plus everything
   `services/w2g/materialize.py` → `services/gochara_intensity/*` reaches (that subtree reads
   `chart_facts`; VERIFIED by grep that `gochara_intensity` and `gochara_grammar` are imported).
   **Declared set is essentially correct** — the only omission is the transitive `chart_facts`
   read through the intensity grammar. Best of the four on this axis.

3. **Leverage / NULL check** — this is the batch's clearest wasted-computation case.
   **`kala_gochara_windows_v2` is selected by zero non-test TypeScript files** (VERIFIED grep
   over `platform/src` + `platform-mcp/src`). All 108 rows this writer has ever produced are
   invisible to every consumer. Simultaneously, the cockpit attributes 1,884 rows it did not
   write to it (F-KAGO-1). The asset's *real* leverage — a cheap 2-minute refresh that could
   keep the near horizon current between expensive century runs — is entirely unrealised.
   Also: the writer populates `term_breakdown`, `lambda_v3_ci_low/high`, `ci_source`; the
   serving `ROW_COLUMNS` selects `term_breakdown` only — the three CI columns are never served
   from any table (see F-CENT-4).

4. **Grounding tier** — **pratyakṣa**, correctly. Its output is a λ threshold-crossing computed
   from ephemeris geometry × a resonance target set; the *targets* carry whatever tier
   `ka_gochara_resonance` assigned, but the window itself is instrument-emergent. It makes no
   classical claim and should not. `calibration_state='structural_prior'` on every row
   (measured across both generations) is an honest label: nothing here is empirically calibrated.

5. **Temporal identity + arbitration** — **it overlaps `ka_gochara_v3_century_materialize`
   directly and head-on.** Both answer "when does event-class E fire for this chart"; both
   consume the same resonance map; they use *different engines* (`gochara_intensity.
   compute_lambda_e` v1 grammar vs `gochara_v3.engine` λ_v3 with tara/nodal modifiers), produce
   *different peak_basis vocabularies* (`gochara_lambda_e_v1` vs `gochara_lambda_v3_*`), and
   write *different tables*. **Today nothing arbitrates them.** `kala_gochara_authority`
   arbitrates *generations within one table*, not *engines*: both charts are pinned to `'3.0'`,
   which is the century writer's production stamp, so ka_gochara loses by default and silently.
   Further overlaps: `kala_activation` (via `kala_windows_get` /
   `query_temporal_activation` — a dasha/signal-activation engine that answers the same
   user-facing question from a completely different substrate and is never reconciled with
   gochara at all), and `ka_vedha_gochara` (obstruction, consumed as a suppression term inside
   λ_v3 — correctly subordinated, not a peer).
   **Temporal Concordance Contract input:** the near-horizon engine and the century engine must
   either (a) be declared the same engine at two resolutions, or (b) carry an explicit
   precedence rule *by horizon distance*, not by generation label. The current mechanism
   arbitrates the wrong axis.

6. **Service** — **no consumer. Shelf inventory, measured.** No density contract, no
   empty-reason discipline, no drill path, because there is no served surface.

7. **Measured cost** — `estimated_seconds = 1`, `writer_timeout_seconds = 1800`.
   **Real (native, from `kala_gochara_v2_build_state.computed_at` span):
   2026-08-13 01:02:31.83 → 01:04:43.13 = 131.3 s for 27 substeps ≈ 4.9 s/substep**
   (VERIFIED). Estimate understated **131×**. Abhinandan: 2026-08-06 16:55:23 → 17:06:46 =
   **683.5 s for 6 substeps ≈ 114 s/substep** (the pre-arc-substrate run; INFERRED that the
   difference is the `bg_gochara_arcs` speed-up the manifest describes). Serve cost: n/a.
   `asset_throughput`: `stale` native (rows_written 83 ✓ matches table), `lit` Abhinandan
   (rows_written **821**, which matches **no** measured table count — 25 rows exist; a stale
   counter from a pre-cutover run, VERIFIED discrepancy).

8. **Findings**

   - **F-KAGO-1 (MUST, §N.4 Cockpit truth / §N.8 Earned-Signal)** — `asset_registry` declares
     `target_table='kala_gochara_windows'` and `count_sql = SELECT COUNT(*) FROM
     kala_gochara_windows WHERE chart_id=$1 AND generation='3.0'`. The writer writes
     `kala_gochara_windows_v2` at `generation='2.0'` **and the string `kala_gochara_windows`
     does not appear anywhere in the module** (that absence is itself a guarded invariant —
     `test_writer_source_never_references_the_protected_table`). Measured consequence: the
     cockpit reports **943** rows for an asset that produced **83**; the 943 were written by
     `ka_gochara_v3_century_materialize`. This is also what feeds `_data_rows_present`
     (asset_runner.py:430), the D-1.6 no-op-completion re-probe — so a ka_gochara build that
     wrote nothing at all would still probe "data present" off another writer's rows.
     PARIṢKĀRA MR-40 set these values deliberately (see
     `tests/test_mr06_cutover_durability.py`'s MR-40 note, which cites "89/85 real rows" —
     consistent with the gen-2.0 counts, not with 943), so the intent was to count *this
     writer's* rows and the table/generation pair chosen does not do that. Correct to
     `kala_gochara_windows_v2` / `generation='2.0'`, or formally merge the asset into the
     century writer. **The MR-07 test (`test_mr07_cockpit_count_sql.py`) actively locks the
     wrong value in and must be updated in the same change.**
   - **F-KAGO-2 (MUST, D-TIME P6)** — no arbitration exists between this near-horizon engine
     and the century engine. Both are `is_active=true`, both currently build, and the served
     surface takes only one of them by a generation label that does not encode "which engine".
     The Temporal Concordance Contract must resolve this explicitly.
   - **F-KAGO-3 (NOW, D-SERVICE P8 / §N.6)** — output table has zero serving consumers.
     Either wire `kala_gochara_windows_v2` into the near-horizon serving path, or route this
     asset `retired` and let the century writer own the whole horizon.
   - **F-KAGO-4 (NOW, C12)** — `integrity_check_sql`, `expected_volume_formula`,
     `expected_volume_inputs` all NULL; `target_floor = 0`. Proposed real invariants:
     (a) every `generation='2.0'` row's `(chart_id, event_class)` must appear in
     `kala_gochara_v2_build_state` with a non-null `class_fingerprint`;
     (b) `window_start <= peak_date <= window_end` (currently 0 violations in gen-2.0 —
     but 16 violations exist elsewhere in the family, so this is a live check);
     (c) every row's `event_class` must exist in `gochara_resonance_map` for the same chart.
     Volume: `rows ≤ Σ_E contacts_evaluated(E)`, inputs `{gochara_resonance_map,
     bg_gochara_arcs, progressive_horizon(now_date)}` — a genuine upper bound the writer
     already records per substep. Floor: 83 (native, achieved).
   - **F-KAGO-5 (NOW, §N.8)** — `asset_throughput.rows_written = 821` for Abhinandan against
     25 measured rows. A stale counter presented as a build fact.
   - **F-KAGO-6 (NEVER-LATER, honest scope)** — the writer's own docstring declares Tier-A
     (eager) bodies only and `temporal_shape=='point'` classes only; measured, it skipped 14
     of 27 native classes for exactly that reason and recorded `skipped_reason` for each.
     That is correct honest behaviour, not a defect — log the narrowness, do not "fix" it in L3.

**Route recommendation (W2 input):** `changed` — F-KAGO-1 is a registry correctness defect that
gates any honest capsule (the cockpit currently lies about this asset in both directions), and
F-KAGO-2 is a doctrine question the layer must answer. If W2 rules that the century writer owns
the whole horizon, the route becomes `retired` and F-KAGO-1 is resolved by deletion rather than
correction — that ruling should be made *before* any rebuild, because rebuilding this asset today
produces 83 rows nobody reads.

---

## ka_gochara_sweep  — THE V1 ARCHIVE (hard-floor protected)

**One-line identity:** The retired D-5 Lane G-4 forward sweep — birth→birth+100y **daily-grid**
λ_e intensity scan, shape-aware, the original century instrument. Superseded by `ka_gochara`;
`data_disposition = RETAINED_AS_CAPITAL`; `is_active = false`; `catalog_status = RETIRED`.

**Temporal question (D-TIME):** *"Across the native's whole life, on which days did / does the
transit field cross the intensity threshold for event-class E?"* — the **exhaustive daily
census**, and still the family's only exhaustive one.

### ⛔ ARCHIVE LOCATION VERDICT (the question this batch was asked)

| what | where | rows | measured how |
|---|---|---|---|
| **v1 corpus, LIVE** | `kala_gochara_windows` **`WHERE generation='v1'`** | **38,287** | `count(*) GROUP BY generation` |
| ↳ native `482012f1` | same | **16,297** | grouped count |
| ↳ Abhinandan `1c826d5a` | same | **19,323** | grouped count |
| ↳ orphan `cb73cd3d` | same | **2,667** | grouped count |
| **snapshot** | `kala_gochara_windows_archive_20260805` | **35,620** | `count(*)` |
| ↳ identity proof | md5 of ordered `id` list, per chart | `a6d0850…` (native) and `7aa55c2…` (Abhinandan) **match live v1 exactly**; min/max id also match | full-column md5 comparison |
| **NOT snapshotted** | `cb73cd3d`'s 2,667 v1 rows | **2,667** | archive has 0 rows for that chart |
| unrelated | `kala_gochara_windows__ssv_20260728c` | **1,267** | Abhinandan only, `computed_at` 2026-07-26, **no `generation` column** (pre-migration-527 schema), `window_end` max 2027-07-04 → a short-horizon **ŚUDDHA-VĀCA rollback anchor**, cited by `services/w2g_validations/v5_corpus_readiness.py` and `PARKED_FINDINGS_CLOSE_v1_0.md`. NOT the v1 century corpus. |

**On "17,240":** VERIFIED arithmetic — `16,297 (native v1) + 943 (native gen-3.0) = 17,240`. The
mandate's figure is **the native chart's total row count in `kala_gochara_windows`, all generations**,
mislabelled as the v1 archive. Correct the mandate to **38,287 (v1 corpus) / 35,620 (snapshotted)**.

**⚠ HARD-FLOOR ALERT (raise to the session):** the v1 rows are **not in a separate archive table** —
they are **interleaved in the live serving table**, distinguished only by a nullable `generation`
column, under a **unique index that includes `generation`** (`uq_kala_gochara_windows_natural_key`).
The DB triggers that used to refuse writes to them were **dropped 2026-08-23** (migrations 588/589,
both applied; `pg_trigger` on `%gochara%` returns 0 rows; `build_protected_assets` is empty). Any
`DELETE FROM kala_gochara_windows WHERE chart_id = …` without a `generation` predicate destroys
16,297–19,323 irreplaceable rows and **will not be refused**. The archive table covers 2 of 3 charts.

1. **Instrument fit** — served **D-TIME P6** exhaustively and **D-GROUNDING P3** (it is the
   frozen validation benchmark `services/w2g/equivalence_report.py` scores v2 against). As a
   *live* instrument it is correctly retired; as *capital* it is the only exhaustive daily-grid
   record in the system and the only corpus with populated `active_sentences` at scale.

2. **Dependencies (declared vs real)** — declared `{ka_gochara_resonance}`. The implementation
   (`services/ka_gochara_sweep/{writer,sweep,shape_output}.py`, all preserved intact) really
   reads `gochara_resonance_map` ✓ plus `gochara_grammar` (G-2) and `gochara_intensity` (G-3)
   module trees, which reach `chart_facts` and `brahma_event_ontology`. Moot for a retired
   asset, but note it for the equivalence harness, which still runs this code path.

3. **Leverage / NULL check** — **the inverse of the usual finding: the v1 corpus is DENSER
   than what replaced it.** Measured on `kala_gochara_windows`:
   | field | `generation='v1'` (38,287) | `generation='3.0'` (1,884) |
   |---|---|---|
   | `active_sentences` empty | **0.5%** | **97.3%** |
   | `contributing_systems` empty | **0.0%** | **97.1%** |
   | `milestone_id` NULL | 100.0% | 83.0% |
   | `continuity_state` NULL | 99.8% | 100.0% |
   | distinct `event_class` | **6** | **27** |
   | distinct `temporal_shape` | interval, point | interval, point, **chain** |
   The cutover bought **4.5× class breadth and a new shape** and paid with **the entire
   attribution layer**. Both facts are real; neither is currently disclosed to a caller.
   Separately: 2,667 v1 rows belong to a chart_id absent from `charts` — unreachable by any
   chart-scoped query, un-snapshotted, and un-dispositioned.

4. **Grounding tier** — **pratyakṣa** for the windows themselves; the populated
   `contributing_systems` / `active_sentences` are what let a v1 row *point back* at the
   śruti-tier configuration sentences that produced it. That pointer is the corpus's real
   value and is exactly what the v3 rows lack.

5. **Temporal identity + arbitration** — retired, so it should never arbitrate. But
   **it can still win by default**: `AUTHORITATIVE_GENERATION_FILTER`
   (`register_gochara_windows.ts:641`) is
   `generation = COALESCE((SELECT authoritative_generation FROM kala_gochara_authority WHERE
   chart_id = …), 'v1')`. **An absent authority row means v1 IS SERVED.** Measured:
   `kala_gochara_authority` holds exactly 2 rows (both `'3.0'`, flipped 2026-08-11 by
   `parishkara-mr24-battery` / `parishkara-mr08-operator`). So **any chart without an authority
   row serves the retired v1 engine's output** — today that is only `cb73cd3d`, which is not in
   `charts`, so **no live serving path reads v1 rows for a real chart** (VERIFIED). But the
   default is "retired engine wins", and every newly-built chart will start there.

6. **Service** — `count_sql` is `… generation='v1'` (correctly scoped by MR-07). Consumers of
   the *table* it lives in: `register_gochara_windows.ts` (3 tools) and
   `reading_checklist.ts::fetchGocharaSweep` (folded into every domain reading). Both apply
   the authority filter. So the sweep's rows are reachable but not currently reached.

7. **Measured cost** — `estimated_seconds = 1000`, `writer_timeout_seconds = 21600` (6 h).
   Real build wall-clock: **unmeasured** (no timing rows survive; `build_run_assets.started_at`
   is NULL on every row for this asset, and `asset_provenance_receipts` has none). What IS
   measured: v1 `computed_at` spans **2026-08-02 08:03:59 → 2026-08-05 06:31:56 for the native
   (≈70 h elapsed across attempts)** and 2026-08-02 08:05 → 2026-08-05 06:32 for Abhinandan —
   consistent with a multi-day, cross-attempt-resumed heavy build, but elapsed-time-across-runs,
   **not** CPU wall-clock; do not quote it as a build duration.
   `asset_throughput` state = `error` on all three charts:
   `"no writer registered for ka_gochara_sweep"` (native 2026-08-12 15:56, Abhinandan
   2026-08-12 16:30). **That is a retired asset still being dispatched**, five days after the
   `@register` was removed (`writers/ka_gochara_sweep.py` is a tombstone shim with `__all__ = []`)
   — `is_active=false` did not stop the run from attempting it.

8. **Findings**

   - **F-SWEEP-1 (MUST, campaign hard floor)** — the v1 corpus is unprotected at the DB level
     (588/589 applied 2026-08-23; 0 triggers; `build_protected_assets` empty) and lives
     interleaved in the live serving table. Any generation-blind DELETE on
     `kala_gochara_windows` destroys it. **Before any W2 rebuild touches this table**, either
     (a) restore a generation-aware BEFORE DELETE/UPDATE guard, or (b) snapshot the remaining
     2,667 un-archived rows and record the accepted risk in writing. This is a *raise-to-native*
     item, not an implementer's call.
   - **F-SWEEP-2 (MUST, §N.8 Earned-Signal)** — a `RETIRED`, `is_active=false` asset produced
     `asset_throughput.state='error'` with `last_error='no writer registered'` on both canonical
     charts on 2026-08-12. Either the dispatcher ignores `is_active`, or a stale queue entry
     survives. Whichever it is, the cockpit shows a permanent red error for an asset that is
     working exactly as designed — an error signal with no error behind it.
   - **F-SWEEP-3 (MUST, D-SERVICE P8)** — the serving default is `'v1'` when
     `kala_gochara_authority` has no row. A retired engine must not be the default authority for
     new charts. Invert the default to "no authority row ⇒ honest empty + `empty_reason:
     no_authoritative_generation_declared`", or seed authority at chart creation.
   - **F-SWEEP-4 (MUST, D-SERVICE P8 / §N.6)** — the v1→v3 cutover silently dropped
     `active_sentences`/`contributing_systems` from 99.5% populated to 2.7%. A caller reading a
     gen-3.0 forecast today gets a window with no attribution and no disclosure that attribution
     was ever available. Either restore the fields at the v3 writer (preferred; the data exists
     inside the engine) or disclose the loss via `judgment_flags`. **This is the batch's
     highest-value single finding.**
   - **F-SWEEP-5 (NOW, hygiene)** — 2,667 v1 rows + 77 resonance rows for chart
     `cb73cd3d-9eba-4220-9902-0de91566e980`, which is not in `charts`. Un-snapshotted
     irreplaceable data belonging to a deleted chart. Snapshot-then-disposition; do not delete.
   - **F-SWEEP-6 (NOW, C12)** — `integrity_check_sql IS NULL` on the corpus that most needs
     one, precisely because nothing will ever rebuild it. Propose a **census invariant**, not a
     count pin: `SELECT count(*) FROM kala_gochara_windows w WHERE w.generation='v1' AND NOT
     EXISTS (SELECT 1 FROM kala_gochara_windows_archive_20260805 a WHERE a.id = w.id)` must be
     **exactly 2,667** — i.e. the only unsnapshotted v1 rows are the known orphan-chart set.
     That is a cross-table consistency check, C12-legal, and it detects both loss and drift.
   - **F-SWEEP-7 (NEVER-LATER)** — `has_writer = true` in `asset_registry` while the shim
     deliberately does not `@register`. Cosmetic given the tombstone is documented; log it.

**Route recommendation (W2 input):** `static` — the corpus is retained capital, the writer is a
documented tombstone, and nothing should rebuild it. But `static` here is **conditional on
F-SWEEP-1**: as of today "static" is a description of intent, not of an enforced state, because the
DB no longer refuses a write. Route it `static` **and** carry F-SWEEP-1 as a gating hard-floor item.

---

## ka_gochara_v3_century_materialize  — THE MONSTER

**One-line identity:** The GOCHARA-UTKARSA W3.4/W5.4 heavy writer — root-solved λ_v3 threshold
crossings over a 100-year horizon, sliced into decades, with a peak-anchored era⊃month⊃day
resolution hierarchy, dual-written to a staging surface and the production surface.

**Temporal question (D-TIME):** *"Over this chart's entire century, when does λ_v3 for event-class
E cross its admission threshold, and — where the class's ontology shape permits — on which single
day does that crossing actually peak?"*

### Substep-plan profile (the question this batch was asked)

- **Grain:** `plan_substeps` returns **one SubStep per (event_class × decade_slice)**, key
  `'{event_class}::{era_slice_key}'`, e.g. `marriage::g3_1984_1994` (writer line 1709-1716).
- **event_class dimension:** **dynamic since MR-16** — `SELECT DISTINCT event_class FROM
  gochara_resonance_map WHERE chart_id=…`. The hardcoded `EVENT_CLASSES` list (7 entries) is
  documentation-only. Measured: **27 classes** for both canonical charts.
- **decade dimension:** **fixed 10 slices** from `build_decade_slices()`, `start_jd = BIRTH_JD +
  i·10·365.25`, labels `g3_{1984+10i}_{1984+10(i+1)}`.
- **Measured plan size: 27 × 10 = 270 substeps per chart** — VERIFIED against
  `kala_gochara_v2_build_state`, which holds exactly **270 `g3_utkarsha` rows per chart**.
  **The manifest and registry description both say "60 substeps (6 event classes × 10 decade
  slices)" — stale by 4.5× since MR-16.**
- **Skip semantics:** per-substep MD5 fingerprint (`compute_substep_fingerprint`) folding
  `ENGINE_VERSION` ("v3.2"), both INSERT templates' column lists (MR-38), and — since PARIŚEṢA
  F-52 — a live scoring-mechanism signature. Unchanged fingerprint **and** rows-exist ⇒ honest
  no-op. Stored in `kala_gochara_v2_build_state (chart_id, event_class, generation)`.
- **Parallelism under the FROZEN contract: NOT POSSIBLE.** `asset_runner._drive_substeps`
  (line 664) iterates `for idx, step in enumerate(substeps)` on the single caller-owned
  `psycopg.Connection`, one `SAVEPOINT writer_exec` + one commit per substep. Chunk-parallelism
  would require a second connection or a second driver — both orchestrator changes, which §N.2
  forbids ("if a writer seems to need a contract change → STOP and raise with the native").
  **What IS available and already implemented:** per-substep commits + `completed_keys`
  cross-attempt resumption, so a 270-substep build can legitimately be spread across several
  orchestrator runs. That is the correct lever, not parallelism.

1. **Instrument fit** — the layer's flagship for **D-TIME P6**; also **D-SALIENCE P5** (P90
   admission, greedy retention with `MIN_PEAK_SEPARATION_DAYS=90`, `MAX_PEAKS_PER_ERA_WINDOW=3`)
   and **D-GROUNDING P3** (R8.8 peak_basis vocabulary; R8.9 earned `is_timing_window`). The
   right instrument. Its problems are wiring and registry truth, not concept.

2. **Dependencies (declared vs real)** — declared
   `{ka_gochara_resonance, ka_vedha_gochara, ka_moorti_nirnaya, ka_kota_chakra,
   ka_tithi_pravesha, bg_sky_calendar}`.
   **Real reads** (writer + `services/gochara_v3/**` via `ClassContext`, VERIFIED by grep of
   every `FROM`/`JOIN` in the subtree): `gochara_resonance_map` ✓, `brahma_event_ontology`
   (undeclared), `chart_facts` ×2 — natal positions and sade-sati phases (undeclared, L1),
   `bg_transit_av_gates` (undeclared, L0), `kala_vedha_gochara` ✓,
   `bg_vedha_malefic_scale` (undeclared, L0).
   - **Undeclared hidden edges: 4** (`brahma_event_ontology`, `chart_facts`,
     `bg_transit_av_gates`, `bg_vedha_malefic_scale`).
   - **Declared-but-unread dead edges: 4** — `ka_moorti_nirnaya`, `ka_kota_chakra`,
     `ka_tithi_pravesha`, `bg_sky_calendar`. Their consumer mechanisms (`w22`, `w25`, `w27b`,
     `w26`) are all `admission_state: candidate` and **are not imported by `engine.py`**, which
     imports only `w23_tara_bala` and `w30_nodal_drishti`. Corroborated by data:
     `gochara_v3_calibration` fitted **all 10 registry mechanisms to `weight_value = 0.000000`**.
   **Net: 8 of the asset's real+declared edges are wrong in one direction or the other.**

3. **Leverage / NULL check** — the richest section in this batch. Measured over the 1,884
   served `generation='3.0'` rows:

   | column | % NULL / empty | served by `ROW_COLUMNS`? | verdict |
   |---|---|---|---|
   | `threshold_lambda` | **100.0%** | no | **dead column** (written never, read never) |
   | `threshold_percentile` | **100.0%** | no | dead column |
   | `implied_density` | **100.0%** | no | dead column |
   | `base_rate_cited` | **100.0%** | no | dead column |
   | `continuity_state` | **100.0%** | **yes** | **serving selects a column that is always NULL** |
   | `active_sentences` | **97.3% empty** | **yes** | attribution layer gone (F-SWEEP-4) |
   | `contributing_systems` | **97.1% empty** | **yes** | drill layer gone |
   | `lambda_v3_ci_low` / `_high` / `ci_source` | 59.7% NULL (**40.3% populated**) | **no** | **computed and never served** |
   | `term_breakdown` | 59.7% NULL | yes | partial |
   | `milestone_id` | 83.0% NULL | yes | expected (only milestone-offset rows) |
   | `parent_window_id` | 43.2% NULL | yes | expected (era rows have no parent) |
   | `resolution` | 33.7% NULL | yes | expected (R8.12 point-class flat rows) |

   Three distinct leverage failures, all VERIFIED:
   (a) **Four migration-564 columns are 100% NULL and unserved** — the MR-01 "schema parity"
   change added them and nothing ever populated or read them. §N.7 item 4: a column that can
   never hold a different value is not a clean result.
   (b) **The confidence interval is computed on 40.3% of rows and reaches no caller** —
   `lambda_v3_ci_low/high/ci_source` appear in `register_gochara_windows.ts` **only inside
   comments**; `ROW_COLUMNS` omits all three. This is the single clearest "designed consumer
   reading NULL where the asset already computed the answer" in the batch — except it is worse
   than NULL: the consumer does not even ask.
   (c) `continuity_state` is in `ROW_COLUMNS` and is 100% NULL on every served row.

   **Peak-basis honesty (measured):** of 1,884 served rows, `gochara_lambda_v3_argmax` = 1,070
   (56.8%, the only basis that earns `is_timing_window=true` per R8.9), `…_coarse_argmax` = 440,
   **`ontology_milestone_offset` = 320 (17.0%)** — a basis the writer's own source comment marks
   as *"deliberately excluded from GENUINE_PEAK_BASES"* — and `gochara_lambda_e_v1` = 54
   (the orphans below). So **43.2% of served rows are context, not timing**; the code does
   disclose this per-row via `resolution_disclosure.is_timing_window`, which is correct §N.6
   behaviour and should be preserved.

   **54 unrefreshable orphan rows in the production surface (VERIFIED):** `generation='3.0' AND
   era_slice_key IS NULL` — 29 native, 25 Abhinandan, all `computed_at = 2026-08-11 08:58:12`,
   all `peak_basis='gochara_lambda_e_v1'`, all `temporal_shape='point'`, spanning only
   2023-09-25…2029-07-25 (a ±3y progressive horizon — i.e. **`ka_gochara`'s engine output,
   promoted into the production surface**). The century writer's DELETE is
   `… AND generation='3.0' AND era_slice_key = %s` (line ~2169), so **no rebuild can ever
   delete or refresh them**: they accrete permanently. §N.3 "rebuild REPLACES, never accretes".
   They are also the only served rows carrying attribution, which makes the corpus internally
   inconsistent in exactly the field a caller would compare.

4. **Grounding tier** — **pratyakṣa**, and it labels itself well. `peak_basis_vocab.py` names
   three bases; `resolution` names three tiers; `calibration_state='structural_prior'` on 100%
   of rows honestly says "not empirically calibrated". The one dishonest surface is
   **`gochara_v3_calibration` itself**: 30 rows, `weight_value=0.000000`,
   `pooled_delta_hit_rate=0.000000`, `delta_native=0.000000`, `delta_abhinandan=0.000000`,
   `n_train_events_native=25`, **`n_train_events_abhinandan=0`**. A per-chart delta reported as
   `0.000000` from **zero training events** is an invented judgment where the honest value is
   NULL (§N.7 item 6), and a "pooled" statistic pooling one real chart with one empty one is not
   pooled. See F-CENT-5.

5. **Temporal identity + arbitration** — the century engine is the **broadest-horizon** temporal
   instrument in L3 and, as of the 2026-08-11 authority flip, the **de facto production
   authority** for both canonical charts. Overlapping engines it must be reconciled with:
   - `ka_gochara` — same question, near horizon, different λ engine, different table. **No
     arbitration exists** (see F-KAGO-2). The `kala_gochara_authority` table arbitrates
     *generation labels within one table*, and it currently resolves in this writer's favour by
     accident of stamp, not by rule.
   - `ka_gochara_sweep` (v1) — same question, daily grid, retired; arbitrated **only** by an
     authority row whose absence defaults to v1 (F-SWEEP-3).
   - `kala_activation` / `kala_bhavishya` via `kala_windows_get`
     (`registry/layers/L3_kala/query_temporal_activation.ts`) — the **dasha/signal-activation**
     engine. VERIFIED: it reads `kala_activation`, `kala_activation_predicates`,
     `kala_bhavishya` and **never touches `kala_gochara_windows`**. Two engines answer
     "when does X happen for this chart" from disjoint substrates with **no shared arbiter and
     no cross-reference**; `register_d9_judgment.ts:1459` even cross-points a caller from one to
     the other without reconciling them.
   - `ka_vedha_gochara` — correctly **subordinated** (consumed as a suppression term inside
     λ_v3 via `ClassContext.vedha_rows`), not a peer. This is the family's one working
     arbitration precedent and the Contract should generalise from it.
   **Contract inputs from this asset:** (i) arbitration must key on *horizon distance × engine*,
   not on a generation string; (ii) `kala_gochara_authority` is a two-row seed with the right
   *shape* (chart-scoped, `flipped_at`, `flipped_by`, `evidence_ref`) but the wrong *axis* — the
   Contract should keep the shape and widen the key to `(chart_id, question_class)`;
   (iii) the gochara↔kala_activation split is an unarbitrated boundary the Contract must name.

6. **Service** — served through `gochara_forecast_get` / `gochara_activation_get` /
   `gochara_election_avoidance_get` (`platform-mcp/src/tools/retrieval/register_gochara_windows.ts`,
   2,301 lines) and, compactly, through `reading_checklist.ts::fetchGocharaSweep` which folds a
   top-5-by-|intensity| summary into every domain reading. Serving reaches the DB through the
   platform proxy `/api/mcp/db/query` (`kala_gochara_windows` is whitelisted). Density: each tool
   declares a hand-rolled `DENSITY_CONTRACT` const with real empty-reason strings, `hardFloor`
   budget sections, `capActiveSentences`, and a `finalizeMcpBudget` whole-envelope trim — genuinely
   §N.6-conformant **in the tool**. But VERIFIED: **the three tools are not registered as
   `CapabilityDescriptor`s** in `platform/src/lib/retrieval/registry/` (grep returns only
   drill-pointer string mentions), so the §N.6 Part-2 census/CI harness cannot see their
   contracts — the deferral the file's own docstring named is still open.
   **Drill to L1 in ≤2 hops: NO, for 97.1% of rows** — `contributing_systems` is the hop and it
   is empty.

7. **Measured cost** — `estimated_seconds = 614`, `writer_timeout_seconds = 3600`,
   `has_substeps = true`.
   **Real, from `kala_gochara_v2_build_state.computed_at` min→max over the 270 `g3_utkarsha`
   substep rows (VERIFIED):**
   - **native `482012f1`: 2026-08-12 22:36:47.040 → 23:34:46.784 = 3,479.7 s (58 min 0 s),
     270 substeps, 914 rows ⇒ 12.89 s/substep, 0.263 rows/s.** Single `build_id`.
   - **Abhinandan `1c826d5a`: 2026-08-11 20:32:59.802 → 22:22:47.839 = 6,588.0 s (1 h 49 min 48 s),
     270 substeps, 916 rows ⇒ 24.40 s/substep.** **Two distinct `build_id`s** ⇒ the run was
     resumed, i.e. it did not complete inside one orchestrator attempt.
   - **`estimated_seconds=614` understates the measured native build by 5.67×.**
   - **`writer_timeout_seconds=3600` leaves 120.3 s of headroom (3.4%) over the fastest measured
     run, and the Abhinandan run exceeded it by 83%.** The timeout is effectively at the runtime.
   - **Date range covered:** `horizon_start_date=1984-02-05`, `horizon_end_date=2084-02-05`
     (measured, identical for both charts — see F-CENT-2), decade slices
     `g3_1984_1994` … `g3_2074_2084`.
   - **`contacts_evaluated = 0` on all 540 `g3_utkarsha` build_state rows** while
     `rows_written` = 914/916 — a shared bookkeeping column the century writer never populates
     (§N.8: a field that reads "0 evaluated" for a run that wrote 914 rows).
   - **Last real dispatch FAILED.** `asset_throughput` for the native reads
     `state='error'`, `last_built_at = 2026-08-21 13:37:44`, with the full traceback:
     `psycopg.errors.RaiseException: BUILD-PROTECTED: kala_gochara_windows row(s) for chart_id
     482012f1… (generation=3.0, asset_id=ka_gochara) are protected — DELETE is refused`, raised
     from `build_gen3_gochara_guard_row()` at `ka_gochara_v3_century_materialize.py:2166` — the
     writer's own production DELETE. **The writer's docstring asserts the opposite** ("the DB
     trigger … protects generation='v1' rows … generation='3.0' writes are explicitly allowed by
     the generation-aware guard (migration 556)"): migration **566** later added a *second*,
     gen-3.0 guard that the writer's own design never accounted for. Two remediation waves
     collided. **This error is now stale** — migrations 588/589 dropped both guards on
     2026-08-23 (VERIFIED: 0 triggers, 0 guard functions), so the writer should build again —
     but the `error` state has never been cleared and the cockpit still shows it red.
   - Serve cost: unmeasured (no live tool call made — read-only session, no MCP invocation).

8. **Findings**

   - **F-CENT-1 (MUST, §N.7 item 3 / portability)** — `BIRTH_JD = 2445736.5` and
     `BIRTH_YEAR = 1984` are hardcoded module constants; the century grid never reads
     `ctx.config['birth_params']`. Measured consequence: Abhinandan (born **1985-03-02**) was
     materialized over **1984-02-05…2084-02-05** with era keys labelled `g3_1984_…`. His 916
     century rows are anchored to **another person's birth epoch**, and 13 months of his
     windows precede his birth. Every third chart will be worse. Derive both from
     `birth_params`; the `era_slice_key` format already carries the year so no schema change is
     needed, but existing rows' keys become wrong-by-label and need a rebuild.
   - **F-CENT-2 (MUST, §N.3 idempotency)** — 54 `generation='3.0'` rows with
     `era_slice_key IS NULL` sit permanently in the production surface. The writer's DELETE is
     era-scoped, so they can never be replaced; they are the only served rows with attribution,
     and they came from a *different engine* (`peak_basis='gochara_lambda_e_v1'`, ±3y horizon).
     "Rebuild REPLACES, never accretes" is violated by construction. Fix the DELETE to also
     clear `era_slice_key IS NULL` for the generation, **or** disposition the 54 rows
     explicitly. Note the natural-key index does **not** include `era_slice_key`, so this is
     not caught by uniqueness either.
   - **F-CENT-3 (MUST, D-SERVICE P8 / §N.6 item 3)** — 97.1% of served rows have empty
     `contributing_systems` and 97.3% empty `active_sentences`. A window served today is an
     unexplainable number. This is the same finding as F-SWEEP-4 seen from the producer side and
     it is where the fix belongs: the engine computes the configuration sentences internally
     (`gochara_grammar.ConfigurationSentence` is imported by `engine.py`) and discards them at
     write time.
   - **F-CENT-4 (MUST, rubric-3 leverage)** — `lambda_v3_ci_low`, `lambda_v3_ci_high`,
     `ci_source` are populated on **40.3%** of served rows and appear in
     `register_gochara_windows.ts` **only in comments**; `ROW_COLUMNS` omits them. A computed
     confidence interval that reaches no caller. Add to `ROW_COLUMNS` (a serving-plane change,
     inside L3's write-set for L3-owned tools) — this is the cheapest real win in the batch.
   - **F-CENT-5 (MUST, §N.7 item 6 / §N.8)** — `gochara_v3_calibration`: all 30 rows have
     every fitted quantity at exactly `0.000000`, including `delta_abhinandan=0.000000` derived
     from `n_train_events_abhinandan=0`. A zero computed from no data is an invented judgment
     where NULL is the honest value; and a `pooled_delta_hit_rate` over {25 events, 0 events}
     is not pooled. Either null the per-chart deltas with no training events, or record the
     table as an honestly-empty fit and stop presenting `weight_value=0` as a fitted weight.
   - **F-CENT-6 (MUST, C12 / registry truth)** — `depends_on` declares 4 assets whose tables
     no code path reads (`ka_moorti_nirnaya`, `ka_kota_chakra`, `ka_tithi_pravesha`,
     `bg_sky_calendar`) and omits 4 it does read (`brahma_event_ontology`, `chart_facts`,
     `bg_transit_av_gates`, `bg_vedha_malefic_scale`). The dead edges make three built L3
     assets look consumed when they are not — a false leverage signal for the whole layer.
     **Hand-off note:** the *fix* for the dead edges is either admitting the candidate
     mechanisms (an L3 change) or removing the edges (an L3 registry change); either is
     in-layer. The undeclared L0/L1 edges are declarations only — also in-layer.
   - **F-CENT-7 (MUST, measured cost)** — `estimated_seconds=614` vs **3,479.7 s measured**;
     `writer_timeout_seconds=3600` vs a measured 3,479.7 s (native) and 6,588 s (Abhinandan,
     two attempts). Any capsule that budgets 614 s or trusts the 3,600 s timeout will fail on a
     chart marginally slower than the native. Set `estimated_seconds` to the achieved figure
     (§N.4: measured, never fabricated) and raise the timeout with real headroom.
   - **F-CENT-8 (MUST, §N.8 Earned-Signal)** — the asset's live `asset_throughput.state` on the
     canonical chart is `error` from a 2026-08-21 trigger that **no longer exists** (dropped
     2026-08-23). The red is stale; a rebuild is the only way to learn whether it is now green.
     Do not clear the state by hand — that would be a signal without a detector.
   - **F-CENT-9 (NOW, C12)** — `integrity_check_sql`/`expected_volume_formula`/
     `expected_volume_inputs` NULL, `target_floor=0`. Proposed real invariants (no count pins):
     (a) **hierarchy integrity** — every row with `resolution IN ('month','day')` must have a
     `parent_window_id` resolving to a row of the same `chart_id` and coarser `resolution`
     (currently 0 orphans, 0 chart mismatches — a live passing check);
     (b) **window sanity** — `window_start <= peak_date <= window_end` (currently **1 violation**
     in gen-3.0 and **15** in v1 → this check *fires today*, which is the point);
     (c) **slice tiling** — the distinct `era_slice_key` set per (chart, event_class) must equal
     the 10 declared decade keys with no gaps and no extras (this is what would have caught
     F-CENT-2's NULL-era orphans);
     (d) **plan/output agreement** — every `(chart_id, event_class)` with rows must have a
     `kala_gochara_v2_build_state` row at `generation='g3_utkarsha'` with a non-null
     `class_fingerprint`.
     Volume: `rows ≤ Σ_over_substeps ( N_era + 2·min(3·N_era, ceil(decade_days/90)) )` — the
     writer's own MR-45 corrected bound, inputs `{gochara_resonance_map (class count),
     DECADE_SLICES (10), brahma_event_ontology.temporal_shape}`. Floor: 914 (native, achieved).
   - **F-CENT-10 (NOW, C12 / registry truth)** — the frozen manifest label
     (`nirmana_evidence.nirmana_elevation_asset_labels`, revision `t0-2026-09-01-0e5b06fb`) and
     `asset_registry.english_description` both say **"plan_substeps returns 60 substeps
     (6 event classes × 10 decade slices)"**. Measured: **270 substeps, 27 classes**. The same
     label also claims era_slice_key writes to `kala_gochara_windows_v2` only, omitting the W5.4
     production dual-write. The manifest description for `ka_gochara` is stale in the mirror-image
     way ("Writes kala_gochara_windows_v2 (staging surface)" vs `target_table=kala_gochara_windows`).
   - **F-CENT-11 (NOW, §N.8)** — `kala_gochara_v2_build_state.contacts_evaluated = 0` on all 540
     g3 rows while `rows_written` is 914/916. A shared column the century writer never fills,
     presented as a measurement.
   - **F-CENT-12 (NEVER-LATER, §N.2 FROZEN contract)** — chunk-parallelism across the 270
     substeps is **not available**: `_drive_substeps` is a sequential loop on one caller-owned
     connection with one savepoint+commit per substep. Achieving parallelism would require an
     orchestrator change, which §N.2 forbids without a native ruling. Log with that reason. The
     supported lever is the one already built: per-substep commits + `completed_keys` resumption,
     which lets a 58-minute build be split across attempts. **Recommend W2 use resumption, not
     parallelism, to fit the build inside a capsule window.**
   - **F-CENT-13 (NEVER-LATER, hygiene)** — two applied migrations share the number 588
     (`588_samiksha_digest_journal.sql` 2026-08-22 23:42, `588_remove_asset_build_protection.sql`
     2026-08-23 05:33). A numbering collision in an applied set; not editable per §N.4. Log.

**Route recommendation (W2 input):** `changed` — F-CENT-1 (hardcoded birth epoch) and F-CENT-2
(unrefreshable orphans) are correctness defects that make the current corpus wrong for any chart
but the native, and F-CENT-3/F-CENT-4 are the layer's largest serving-value gaps. A `rebuild_only`
route would re-materialize the same wrong century grid for Abhinandan. **Sequencing note:** the
rebuild that follows the fix must be budgeted at the measured **≈3,480 s / 270 substeps** with
resumption enabled, not at the registry's 614 s, and must be preceded by F-SWEEP-1 (the v1 corpus
now sits unguarded in the same table this writer DELETEs from).

---

## Cross-asset input to the Temporal Concordance Contract

Recorded here because the Contract is the layer's headline deliverable and this batch holds one
of its two seed tables.

**Seed table 1 — `kala_gochara_authority` (2 rows, dumped in full):**

| chart_id | authoritative_generation | flipped_at | flipped_by | evidence_ref |
|---|---|---|---|---|
| `1c826d5a-…` | `3.0` | 2026-08-11 09:10:42 | `parishkara-mr24-battery` | PARISHKARA_LEDGER.md MR-24 rollback+re-flip exercise, 2026-08-11 |
| `482012f1-…` | `3.0` | 2026-08-11 09:44:07 | `parishkara-mr08-operator` | MR-24 final battery re-run 2026-08-11: rollback+re-flip exercise on native chart, post THE-ONE-rebuild + MR-40 cockpit fix |

**What it gets right** (generalise these): chart-scoped key; a *timestamp* and an *actor* for the
flip; a free-text `evidence_ref` pointing at the ledger entry that justified it; and a documented
default-on-absence so an unseeded chart is still answerable. **PK is `chart_id` alone.**

**What it gets wrong** (fix in the Contract): it arbitrates a **generation string within one
table**, not **which engine answers which temporal question**. Three engines
(`ka_gochara_sweep` v1, `ka_gochara` v2, `ka_gochara_v3_century_materialize` v3) write windows;
this table can only name one string, so "near-horizon v2 vs century v3" is unrepresentable and v2
loses silently. And the entirely separate `kala_activation` engine — which `kala_windows_get`
serves for the *same* user question from `kala_activation`/`kala_bhavishya` — is outside this
table's vocabulary altogether.
**Recommended generalisation:** widen the key to `(chart_id, question_class)` where
`question_class` names the temporal question (e.g. `event_window.near`, `event_window.century`,
`signal_activation`), keep `flipped_at`/`flipped_by`/`evidence_ref` verbatim, and keep the
absent-row default but make it an **honest refusal with an `empty_reason`**, not a silent fallback
to a retired engine (F-SWEEP-3).

**Seed table 2 — `gochara_v3_calibration` (30 rows, dumped in full above):** three `fit_run_id`s
(`57045e92…` 2026-08-10, `e98b6591…` 2026-08-11, `8d2925bc…` 2026-08-11), each × the same 10
`mechanism_id`s (`w21_av_gating`, `w22_moorti_nirnaya`, `w23_tara_bala`, `w24_sade_sati`,
`w25_kota_chakra`, `w26_real_eclipses`, `w27_annual_stack`, `w27a_tajaka_year_lord`,
`w27b_tithi_pravesha`, `w27c_sudarshana`), wave `W4.4`. **Every numeric column is 0.000000 in
every row**; `n_train_events_native=25`, `n_train_events_abhinandan=0` throughout.
**What it gets right:** the *shape* is exactly what a concordance arbiter needs — a versioned fit
run, a named mechanism, a weight, a per-chart delta, and an explicit training-event count that
makes the evidence base auditable. **What it gets wrong:** the training-event count and the delta
disagree — a `0.000000` delta backed by 0 events should be NULL (F-CENT-5) — and every mechanism
it "fits" is `admission_state: candidate` and unwired, so the table describes an ablation that
never ran. **Recommended generalisation:** keep the schema; make `delta_*` NULL when
`n_train_events_* = 0`; add an `admission_state` column so a fitted weight cannot be read as an
admitted one; and require `n_train_events` > 0 before any weight is served.

**The unarbitrated boundary the Contract must name:** `gochara_*_get`
(`kala_gochara_windows`, transit-driven, λ_v3) and `kala_windows_get`
(`kala_activation`/`kala_activation_predicates`/`kala_bhavishya`, signal/dasha-driven) answer the
same user question from disjoint substrates, cross-point at each other in prose
(`register_d9_judgment.ts:1459`, `reading_checklist.ts:530`), and have **no shared arbiter, no
shared vocabulary, and no reconciliation test**. That is the layer's largest concordance gap and
it is entirely outside `kala_gochara_authority`'s reach.
