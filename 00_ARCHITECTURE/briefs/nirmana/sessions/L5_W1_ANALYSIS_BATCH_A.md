---
artifact: L5_W1_ANALYSIS_BATCH_A.md
canonical_id: NIRMANA_L5_W1_ANALYSIS_BATCH_A
version: "1.0"
status: CURRENT — W1 ANALYZE output, L5 (Mīmāṃsā)
session: L5
produced_on: 2026-09-05
scope: lel_events · mi_jivanaghatana · mi_bhavisya · mi_pramana (the P7 provenance core)
method: >
  Read-only fresh-context analysis subagent against the plan §4 W1 rubric, the five doctrines,
  charter C12, and CLAUDE.md §N.4/§N.6/§N.7/§N.8. No repo write, no DB write. Findings carry
  file:line or live-SQL evidence; unresolved items are recorded as UNKNOWN with what would settle
  them. L5-F-15 was independently re-verified by the L5 session before being escalated as #1732.
---

# L5-W1 — Batch A: the P7 provenance core

### `lel_events` — the user-authored Life Event Log source corpus (`life_events`); the L5 no-writer exception

- **Purpose / doctrines:** P7 (PARKED) ground truth + P8 service. It is the *only* observed-reality
  corpus in the whole instrument — every falsifiability claim L5 can ever make terminates here. The
  registry `english_description` states its two governing rules exactly right: "Source data, NOT a
  built asset (`has_writer=false`); intaken via the LEL save API. Availability-driven calibration
  input; never a prediction-generation source (no-leakage)." Still the right instrument, and
  correctly *not* a writer.
- **Dependencies (declared → real):** `depends_on = []`, `target_table = NULL`, `has_writer = false`.
  Real: no upstream; its write path is the LEL intake API
  (`platform/src/lib/lel/prospective_ledger.ts` + the save route), not the orchestrator.
  **Hidden downstream edge (false-negative in the DAG):** `mi_jivanaghatana` reads `life_events` as
  its *sole* source (`mi_jivanaghatana.py:194`) but does **not** declare `lel_events` in
  `depends_on` (it declares only `bg_ghatana`). The one real producer→consumer edge in the P7 core
  is absent from the registry DAG.
- **Leverage:** **Two real NULL-reads.**
  1. `life_events.significance` is **NULL on all 64 rows** (SQL-verified) and there is no
     `magnitude` column — while the markdown source of truth carries
     `magnitude: [trivial|moderate|significant|major|life-altering]` on *every* event block
     (`LIFE_EVENT_LOG_v1_2.md:85`). The magnitude the LEL already records never reaches the DB, so
     `mimamsa_event_provenance.event_magnitude` is NULL 64/64 and `mimamsa_calibration.score_magnitude`
     is the constant 0.5 on all 57 rows. The answer exists in the source; the consumer reads NULL.
  2. `life_events` has no `subcategory`, `disclosure_timing`, or `shaped_predictor` column, though
     the markdown carries `subcategory` and the disclosure/predictor semantics the admissibility
     firewall is written against.
- **Grounding:** `pratyaksa` in the strictest and best sense — direct native testimony, no classical
  claim, no instrument derivation. Labelling it `sruti`/`yukti` would be a category error; there is
  no interpretive output here to tier.
- **Service:** Real consumer, live: `lel_query` (`marsys://tool/L5/lel_query`,
  `query_life_events.ts`) — registered (`L5_mimamsa/index.ts:45`) and present in all three tool
  projections; MCP alias `mimamsa_lel_query` → platform primitive `lel_query`
  (`register_p1_aliases.ts:2067`). Also read by `mi_jivanaghatana`, `mi_sankalpa`,
  `prediction_lifecycle_sweep`, `query_mechanism_retrodiction`, `kala_views/story.ts`. **Not**
  built-but-unplugged. Density: bounded at 50 rows/page, but **no `empty_reason`** (8 of 16 sibling
  L5 capabilities have one; this one does not) and **no `density_contract`**. Drill depth: 1 hop to
  the LEL markdown via `source_section`/`provenance.lel_id`; correctly declares
  `grounds_to: { l1_fact_ids: false }`. Destructive-clear protection is real and correctly reasoned
  (`assetClearSpec.ts:223` — `lel_events: null` disables the auto-derived per-chart DELETE, citing
  the JL-010/JL-020 irreplaceable-loss class).
- **Cost:** estimated `NULL`. Measured: **no build cost exists** — zero `asset_throughput` rows and
  zero `asset_provenance_receipts` rows. That is the correct signature of a source-acceptance asset,
  not a gap. Serve cost UNKNOWN — settled by a timed `lel_query` call.
- **What "source acceptance" can honestly mean, and the CANARY path.** The frozen manifest pins
  `execution_obligation: 'source_acceptance'` with a hard guard (`definitions.ts:19`, `:274` — "The
  legacy `lel_events` identity is permitted only as the L5 user-authored source disposition", plus
  `:277` requiring the adjudicated obligation be retained and `:281` forbidding any un-adjudicated
  asset from claiming an acceptance obligation). Projection maps it to the single event
  `source_accepted` (`projection.ts:354`), and `dispatch_nirmana_campaign_wave.py:415` selects only
  `execution_obligation == 'build'` — so **`lel_events` is structurally undispatchable by the wave
  dispatcher**. Its honest terminal disposition is: *analysed → decided → source_accepted →
  verified → frozen*, with **no build and no rebuild step at all**. The capsule can truthfully
  carry: (a) the `count_sql` result (64 rows, canonical; 0 for Abhinandan `1c826d5a`); (a2) the
  chart-scoping proof (`count_sql` is chart-keyed and the second chart honestly returns 0); (b) the
  clear-protection proof (`assetClearSpec.lel_events === null`); (c) the no-leakage proof (no
  writer, no build row, no orchestrator path); (d) the intake-path identity (LEL save API); (e) a
  reconciliation of DB rows against the markdown source of truth. What it must **not** carry: any
  `integrity_check_sql` that is a bare `count(*) = 64` (C12/D-126, "an equality wearing a floor's
  name").
- **Findings:**
  - `L5-F-01` **[MUST]** `mi_jivanaghatana.depends_on` omits `lel_events`, the asset whose table is
    its sole input. Any invalidation/staleness reasoning (O-wave WP-1's `upstream_digest`) cannot
    see LEL changes at all — a native LEL append will never mark `mi_jivanaghatana` stale.
    — *basis:* plan §4 rubric item 2; O-wave §3.1 — *evidence:*
    `asset_registry.depends_on('mi_jivanaghatana') = {bg_ghatana}`; `mi_jivanaghatana.py:194`.
  - `L5-F-02` **[MUST]** The LEL→DB intake drops `magnitude` and `subcategory`.
    `life_events.significance` is NULL 64/64 and no magnitude column exists, while the markdown
    carries `magnitude` per event. Root cause of the constant `score_magnitude = 0.5` across every
    calibration row. — *basis:* §N.7 item 6 (the pipeline turns a *known* value into a
    neutral-looking 0.5); C12 "derive, never pick" — *evidence:*
    `SELECT significance, count(*) FROM life_events GROUP BY 1` → `{null: 64}`;
    `LIFE_EVENT_LOG_v1_2.md:85`. **Recommended disposition: document the gap; do NOT backfill
    magnitudes in this campaign** — the fill is an intake-schema change with P7 consequences and
    belongs with the parked programme.
  - `L5-F-03` **[MUST]** One non-LEL demo row is in the production corpus:
    `event_id 5278d97c-e769-529a-b0c2-be1e965c2d6b`, `source_section = 'D-4a-A4-append-hook-demo'`,
    `provenance.caller_context = 'D-4a-A4-append-hook-demo'`, `event_date 2026-07-31`, category
    `travel_event`. It is counted by `count_sql`, propagated into `mimamsa_event_provenance`, and
    marked `admissible_clean = true` — i.e. live ground truth for calibration. — *basis:* hard floor
    §3.6; §N.8 (a "clean" flag with no detector that could reject a demo row) — *evidence:* SQL over
    `life_events` / `mimamsa_event_provenance`. **Disposition is the native's call** (delete vs
    flag); the honest minimum for this campaign is to *record* it and exclude it from any volume
    derivation, never to silently absorb it into the count.
  - `L5-F-04` **[NOW]** `lel_query` / `query_life_events.ts` have no `empty_reason` and no
    `density_contract`, while 8 sibling L5 capabilities have the former. A caller cannot distinguish
    "this chart has no events" (true for Abhinandan) from "the filter matched nothing".
    — *basis:* D-SERVICE (P8); §N.6 item 4 — *evidence:* `grep empty_reason …/L5_mimamsa/*.ts`
    (8 hits, none in `query_life_events.ts`).
  - `L5-F-05` **[NOW]** `query_life_events.ts:5` states "57 rows for the canonical chart"; live count
    is 64. Same stale constant in `assetClearSpec.ts:216` ("the 57 native events"). — *basis:*
    §N.7 item 3 — *evidence:* SQL count 64 vs those two lines.
  - `L5-F-06` **[NOW]** `integrity_check_sql IS NULL`; `catalog_status='DRAFT'`. A real invariant is
    available and would be a genuine detector, not a volume pin: *every `life_events` row for a
    chart must be reachable from a `mimamsa_event_provenance` row of the same chart, and vice versa*
    (FULL JOIN, zero one-sided rows) — verified live as 0/0 today. — *basis:* C12 (real invariants +
    rewrite-floor test: this *can* fail on real corruption — a partial provenance build, a stray
    chart-id).
  - `L5-F-07` **[NEVER/LATER]** LEL data-ization / richer intake schema (magnitude, subcategory,
    disclosure_timing, shaped_predictor as first-class columns). — *reason:* explicitly on the
    deferred register (plan §7.3); P7 PARKED by native ruling.
- **Proposed route:** `static` — no writer, no build, undispatchable by the wave dispatcher; its
  terminal evidence is a reconciliation + protection proof, not an execution. (`empty` would be
  wrong: the corpus is populated and load-bearing. `static` still emits a real `source_accepted`
  milestone, which is precisely what the manifest guard was written for.)

---

### `mi_jivanaghatana` → `mimamsa_event_provenance` (64 rows) — the LEL→DB provenance bridge and leakage firewall

- **Purpose / doctrines:** P7 seam (PARKED) — partitions the observed-event corpus into
  held-out/training and admissible/inadmissible so a future falsifiability loop cannot score itself
  on evidence that shaped its own predictors. Serves the no-leakage clause directly. Still the right
  instrument; the *design* (deterministic MD5 partition, chart-scoped-only source path, structural
  native-contamination gate) is sound and well-reasoned in code.
- **Dependencies (declared → real):** Declared `{bg_ghatana}`. Real reads:
  `information_schema.columns` (schema probe, :185), **`life_events`** (:194 — the sole source,
  **undeclared**), `brahma_event_ontology` (:133 — **declared, but a dead edge**: the query filters
  on `category`/`subcategory`, columns that **do not exist** on `brahma_event_ontology`; the live
  schema has `domain` and `lel_category`). **Hidden edge:** `lel_events`. **False/dead edge:**
  `bg_ghatana` — declared, attempted, and guaranteed to fail.
- **Leverage:** **The highest-value one in this batch.** `_lookup_event_class` (:126-149) wraps its
  query in a SAVEPOINT + bare `except: return None`. Against the live schema it raises
  `column "category" does not exist` — the writer's exact predicate was run against production and
  errors. Therefore `event_class_id` is **NULL on 64/64 rows**, silently, forever. Downstream,
  `mi_pramana._load_base_rates` then falls back to `0.10` for every calibration row. The event
  ontology *does* carry the bridge (`brahma_event_ontology.lel_category`, `.domain`,
  `.magnitude_floor`, `.base_rate_by_age`) — an entire designed classification layer is being read
  as NULL because of a column-name mismatch swallowed by an exception handler.
- **Grounding:** `pratyaksa` throughout, and it should be. Every column is either copied from native
  testimony (`event_date`, `domain_primary`) or computed by a stated instrument formula (`held_out`
  = MD5(event_id) mod 10 ≥ 8; `partition_seed_version = 'v1_md5_mod10'`; `provenance_formula_ver =
  'mi_jivanaghatana_v2.0'`). No classical claim is made or implied.
- **Service:** No dedicated capability reads `mimamsa_event_provenance` directly on the serving
  plane. Its real consumer is `mi_pramana._substep_match` (`mi_pramana.py:298-304`), and it surfaces
  indirectly through `query_calibration`'s `event_id`. Drill depth:
  `mimamsa_event_provenance.event_id` → `life_events.event_id` → `provenance.lel_id` → LEL markdown
  block = 2 hops to source; **verified 0 orphans**. Not built-but-unplugged — it has a real in-layer
  consumer — but it has **no recorded serving disposition**, which is the honest gap.
- **Cost:** estimated 1s. Measured: **UNKNOWN** — `asset_throughput` carries no duration column,
  `rows_per_second` NULL, `measurement_count = 0` for both charts, and **zero
  `asset_provenance_receipts` rows**. Last builds: canonical `2026-08-08T00:18:13Z`, 64 rows, state
  **`stale`**; Abhinandan `2026-07-26T21:18:01Z`, 0 rows, state `lit`. Writer shape: light
  `run(ctx)`, single pass, ~64 `executemany` inserts + one `_lookup_event_class` round-trip per row
  (64 doomed queries — the only meaningful cost, and it buys nothing).
- **Volume-formula verification (the assigned task — full derivation, per C12 "derive, never pick"):**

  | quantity | value | how derived |
  |---|---|---|
  | `expected_volume_formula` | `FILE_COUNT('01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md','EVT')` | registry |
  | `expected_volume_inputs.file_count` | **56** | registry |
  | actual `^EVT\.…:$` block headers in the file | **58** | `grep -cE "^EVT\.[A-Za-z0-9.]+:$"` |
  | …minus the §1.4 schema template `EVT.YYYY.MM.DD.XX` (line 76) | **57** | all 57 live in §3 EVENT LOG; 0 duplicates |
  | file frontmatter `total_events_logged` | 57 ("46 prior + 10 new", which sums to 56 — the frontmatter's own arithmetic is internally inconsistent; the v1.7 changelog says "Total events 47→57") | `LIFE_EVENT_LOG_v1_2.md:22`, `:34` |
  | `life_events` rows (canonical chart) | **64** | SQL |
  | `mimamsa_event_provenance` rows | **64** (canonical) + **0** (Abhinandan) | SQL |

  **The 64 reconciles exactly, with every row attributed:**
  - **57** rows carrying a distinct `provenance.lel_id` — 1:1 with the 57 EVT blocks in the file.
  - **+1** dual-role split: `928a1f56…-fs`, a second row for the *same* `lel_id`
    `EVT.2019.05.XX.01` re-typed `event_type = 'foreign_settlement'` (58 rows carry a `lel_id`, 57
    distinct).
  - **+5** native date-tightening corrections ingested 2026-07-17/18 from
    `NATIVE_DATE_TIGHTENING_RESPONSES_v1_0.md` (D-4a Lane A-1), `event_id` suffixed `-corr-*`, each
    carrying `corrects_event_id` + `native_quote` + `original_event_date`.
  - **+1** demo row `5278d97c…` (`D-4a-A4-append-hook-demo`) — see `L5-F-03`.
  - **57 + 1 + 5 + 1 = 64.**

  **Verdict: the formula is wrong on three independent counts, and the row count is *not* a bug.**
  1. The pinned input **56 ≠ 57**, the true EVT-block count (56 is what you get by excluding
     `EVT.CURRENT.01`, which the frontmatter says is "not counted as a point event" — a *narrative*
     exclusion the formula does not encode).
  2. The formula names the **wrong source entirely.** The writer has **no markdown branch at all** —
     `lel_source` is hardcoded `"db"` and `lel_file_sha` hardcoded `None` (:179-180), and the only
     read is `SELECT * FROM life_events WHERE chart_id = %s`. A `FILE_COUNT` over a markdown file
     cannot govern the volume of a table the writer reads instead. The `volume_explanation` —
     "Deterministic given the source-of-truth file. Re-runs MUST match the file count exactly;
     divergence is a bug" — is now false in both halves.
  3. The true derivation is `count(life_events WHERE chart_id = $1)`, which is chart-scoped and
     **correctly 0 for Abhinandan** — the file-count formula would declare that healthy build a
     56-row shortfall.
- **Findings:**
  - `L5-F-08` **[MUST]** `event_class_id` is NULL on 64/64 rows because `_lookup_event_class` queries
    non-existent columns (`category`, `subcategory`) on `brahma_event_ontology` and a bare `except`
    swallows the error. A designed classification layer reads as universally absent, and the failure
    is invisible. — *basis:* §N.8; §N.7 item 4 — *evidence:* `mi_jivanaghatana.py:132-137` vs live
    `information_schema.columns` for `brahma_event_ontology`; the writer's exact predicate run
    against production errors; `count(*) FILTER (WHERE event_class_id IS NOT NULL)` = 0.
  - `L5-F-09` **[MUST]** `expected_volume_formula` / `expected_volume_inputs` are wrong and point at
    a source the writer does not read (derivation above). Under C12 this is the "pin
    stale/underived → correct the check with the derivation in the PR" branch, **not** a writer fix
    — the writer is producing exactly the right 64 rows. — *basis:* C12 — *evidence:* the
    reconciliation table; `mi_jivanaghatana.py:179-199`.
  - `L5-F-10` **[MUST]** `admissible_clean = true` on **64/64** rows, and no live code path can
    produce `false`. `_admissibility` (:100-107) tests three conditions: `shaped_predictor` (no such
    column → always `False`), `disclosure_timing == 'post_framework_undated'` (no such column →
    always the literal `'unknown'`, verified on all 64 rows), and `event_date is None` (populated on
    all 64). A leakage firewall whose every gate is un-wired reports 100% clean by construction.
    — *basis:* §N.8 verbatim; §N.7 item 4 — *evidence:* `life_events` column list; `count(*) FILTER
    (WHERE admissible_clean)` = 64; all 64 rows read `disclosure_timing = 'unknown'`. **Correct
    disposition: NULL the flag or rename it to what it measures (`has_event_date`), and document the
    missing detector. Never a fill, never a weakening.**
  - `L5-F-11` **[NOW]** The 5 `-corr-*` correction rows and their 5 corrected originals are **both**
    present and **both** `admissible_clean = true`, with no supersession represented in
    `mimamsa_event_provenance` (the `corrects_event_id` link lives only in `life_events.provenance`
    JSONB and is not carried across). A future calibration loop double-counts the same lived event at
    two different dates — e.g. `EVT.1995.XX.XX.02` at 1995-06-30 *and* its congenital correction at
    1984-02-04. `mi_pramana` already consumes both (24 distinct events matched). — *basis:* plan §5
    L5 mandate item 2; §N.6 item 1 — *evidence:* SQL over `mimamsa_event_provenance` +
    `life_events.provenance->>'corrects_event_id'`.
  - `L5-F-12` **[NOW]** Three columns are dead by construction, not by data: `lel_file_sha`
    (hardcoded `None` at :180, NULL 64/64 — a BA-P6 pinning field the v2.0 DB-only rewrite
    orphaned), `event_magnitude` (NULL 64/64, root cause `L5-F-02`), `disclosure_timing`
    (`'unknown'` 64/64). The writer docstring still advertises "BA-P6 EXT: `lel_file_sha` pinning,
    `lel_source` tagging, `event_class_id` mapping" — of those three, only `lel_source` works.
    — *basis:* §N.7 item 4 + §N.8 — *evidence:* `mi_jivanaghatana.py:157-158, 180`; SQL.
  - `L5-F-13` **[NOW]** `integrity_check_sql IS NULL`; `catalog_status='DRAFT'`. Real invariants
    available that pass the C12 rewrite-floor test: (a) FULL JOIN `life_events` ↔
    `mimamsa_event_provenance` per chart, zero one-sided rows (live 0/0); (b) `event_id`
    distinctness within `(chart_id)`; (c) held-out partition reproducibility — `held_out` must equal
    `MD5(event_id) mod 10 ≥ 8` for every row, recomputable in SQL, which would catch a silent
    seed-version change (live: 13/64 held out ≈ 20%, consistent). — *basis:* C12.
  - `L5-F-14` **[NEVER/LATER]** Restore a markdown-source branch / re-pin `lel_file_sha`.
    — *reason:* the DB-only source path is the *structural* native-contamination gate (:174-178);
    re-adding a file branch would reopen the cross-chart leakage hole the v2.0 rewrite closed.
    Deferred register (plan §7.3).
- **Proposed route:** `changed` — the registry-side volume derivation (F-09), the missing
  `lel_events` edge (F-01) and the honest-labelling of `admissible_clean` (F-10) are
  registry/writer corrections that must land before a truthful capsule; F-08 is a two-line
  column-name fix. Data itself does not need regenerating for the count (64 is correct), but a
  rebuild after the `event_class_id` fix is worth folding in.

---

### `mi_bhavisya` → `mimamsa_predictions` (195 rows: 139 canonical + 56 Abhinandan) — the frozen prediction bundle

- **Purpose / doctrines:** P7 seam (PARKED) — freezes L4 Phala anchors into an immutable, falsifiable
  prediction bundle so a later loop has something specific to be wrong about. This is the asset
  mandate item 2 is about. Still the right instrument.
- **Dependencies (declared → real):** Declared
  `{ph_pramana, ph_nimitta, ph_phaladesa, mi_kula, mi_jivanaghatana, bo_laksana}`. Real reads:
  `phala_anchors` (→ `ph_nimitta` ✅), `bodha_msr_signals` (→ `bo_laksana` ✅, though that table has
  **7** registered producers — the edge is real but under-specified). **False edges (4):**
  `ph_pramana`, `ph_phaladesa`, `mi_kula` (the `family_id` comes from the pure function
  `_signal_family_key` imported from `mi_adhilepa`, `mi_bhavisya.py:23`), `mi_jivanaghatana` (this
  writer is upstream of matching, not downstream). **Hidden edge:** a *code-level* import dependency
  on `mi_adhilepa`, undeclared, which silently changes prediction provenance if `_signal_family_key`
  changes.
- **Leverage:** `mimamsa_predictions.base_rate` is written as `None` by this writer (:186, comment
  "computed by `mi_pramana`") and **`mi_pramana` never writes back** — `base_rate IS NULL` on
  **195/195** rows. `query_predictions.ts` then builds a 12-line `base_rate_provenance` block that is
  `null` for every row ever served, above a comment asserting "`base_rate` here is populated by
  `mi_pramana.py`'s `_load_base_rates()` … read from `brahma_event_ontology.base_rate`". That claim
  is false twice over: no write-back exists, and `brahma_event_ontology` **has no `base_rate` column**
  (live schema: `base_rate_by_age`).
- **Grounding:** `pratyaksa`, and it should be. Every field is inherited from an L4 anchor or an L2
  MSR signal with the id retained. One *narration* seam: `outcome_claim` is composed in-writer when
  `karmic_note` is absent (:145-150) — deterministic and traceable, so `pratyaksa` remains honest,
  but it is a sentence the instrument writes and should be flagged as such.
- **Service:** Real consumer: `query_predictions` (`marsys://tool/L5/query_predictions`), registered
  (`index.ts:42`), present in chat-tool-defs + MCP registrations (absent from the web bridge).
  `emits_references: true`, `prediction_id → source_pramana_id → ph_pramana` drill declared. **But**
  `standing_predictions_read` does **not** read this table: it resolves to
  `query_prospective_ledger` over `brahma_prospective_ledger` (30 rows), deliberately and with a
  documented reason (`query_prospective_ledger.ts:11-19` — repointed off
  `phala_predictive_anchors_get` in SARVA-SIDDHI W-2 P-1). So **two prediction stores exist**, both
  live, serving different surfaces; `prediction_lifecycle_sweep.ts:12-58` documents this correctly.
  Density: **no `empty_reason`, no `density_contract`**.
- **Cost:** estimated 2s. Measured: **UNKNOWN** — no receipts; `rows_per_second` NULL,
  `measurement_count = 0`. Last builds: canonical `2026-08-21T02:36:53Z` rows_written 278
  (= 139 predictions + 139 manifestation_sets) but state **`error`** — `"BLOCKED: upstream
  dependency(ies) ph_phaladesa, ph_pramana did not complete in this run"`, i.e. blocked on two of the
  four **false** edges; Abhinandan `2026-08-12T17:11:48Z`, 112 rows, state `lit`. Writer shape:
  light, one anchors query + one MSR query + two `executemany` batches — genuinely cheap.
- **Prediction provenance retention (mandate item 2) — verified field by field.** Each row retains:
  **what generated it** (`source_pramana_id` = the L4 `anchor_id`;
  `bundle_formula_version = 'mi_bhavisya_v1.0'`), **from which facts** (`driving_signals` JSONB —
  MSR `signal_id` + `strength` + `family_id`, populated on **195/195**), **for which window**
  (`observation_window` daterange + `eval_date`, non-null on all), **at what stated confidence**
  (`confidence_band` numrange), plus `magnitude_expected` (real values: `major`/`minor`/`moderate`,
  not a single default), `falsifier_jsonb` (non-empty on **195/195**), `emitted_at`,
  `frozen_bundle_hash`, `lifecycle_status`. **Referential integrity is currently perfect**:
  `mimamsa_calibration → mimamsa_predictions` 0 orphans, `mimamsa_calibration →
  mimamsa_event_provenance` 0 orphans, `mimamsa_attribution → mimamsa_calibration` 0 orphans,
  `mimamsa_event_provenance → life_events` 0 orphans. The idempotency guard is genuinely careful
  (:215-225: only `lifecycle_status IN ('pending','due')` rows are deleted; adjudicated rows are
  preserved as irreplaceable). **The provenance retained is good. The identity it is retained under
  is not — see `L5-F-15`, the one thing here that actively makes the later loop harder.**
- **Findings:**
  - `L5-F-15` **[MUST — the load-bearing finding of this batch; ESCALATED as issue #1732]**
    **`prediction_id` is not stable across an upstream rebuild, so a routine L4 rebuild destroys the
    entire P7 provenance chain.** `prediction_id = f"pred_{anchor_id}"` (`mi_bhavisya.py:124`);
    `phala_anchors.anchor_id` has DB default `gen_random_uuid()` and **is not in `ph_nimitta`'s
    INSERT column list** (`ph_nimitta.py:223-235`), while `ph_nimitta` opens with
    `DELETE FROM phala_anchors WHERE chart_id = %s` (:129). So every `ph_nimitta` rebuild mints
    brand-new random anchor_ids → brand-new prediction_ids → every `mimamsa_calibration.prediction_id`
    and every `mimamsa_attribution.match_id` (`= prediction_id + '_' + event_id`) becomes
    unresolvable. Worse, the protective `DELETE … lifecycle_status IN ('pending','due')` guard would
    *preserve* any adjudicated row under its now-dead id while fresh `pending` rows appear alongside
    — turning the safeguard into an orphan-generator. This programme plans exactly such rebuilds.
    — *basis:* plan §0 P7 parking clause verbatim ("nothing in this programme may make the later loop
    harder"); plan §5 L4 ("prediction provenance hygiene (P7 seam) verified untouched"); §N.5
    — *evidence:* `phala_anchors.anchor_id` default `gen_random_uuid()`; `ph_nimitta.py:129`,
    `:223-235`; `mi_bhavisya.py:124`; live 195 predictions ↔ 195 anchors, 0 orphans.
    **Independently re-verified by the L5 session before escalation.** The fix is a deterministic
    natural key on `phala_anchors`; its shape is L4's W2 call.
  - `L5-F-16` **[MUST]** `frozen_bundle_hash` is not content-addressed: `_hash_bundle` mixes in
    `emitted_at = datetime.utcnow()` (:30-33, :116). Live: **195 rows, 195 distinct hashes, 1
    distinct `emitted_at` per chart** — so the hash is a per-run nonce, not a bundle fingerprint. A
    field named "frozen bundle hash" that cannot detect an unchanged bundle defeats its own purpose
    and defeats O-wave WP-2's delta-skip (`output_digest` can never match) and WP-1's
    delta-directional propagation (every rebuild looks like a true delta). — *basis:* §N.8; O-wave
    §3.1/§3.2 — *evidence:* `mi_bhavisya.py:30-33, 116, 173`; SQL.
  - `L5-F-17` **[MUST]** Four false `depends_on` edges — and this is not cosmetic: the canonical
    chart's last build **failed** with `"BLOCKED: upstream dependency(ies) ph_phaladesa, ph_pramana
    did not complete in this run"`, i.e. it was blocked by two dependencies it never reads. One
    undeclared code-import edge on `mi_adhilepa`. — *basis:* plan §4 rubric item 2; O-wave §3.3
    (`blocked_dependency(reason)` must be a *true* reason) — *evidence:* `asset_registry.depends_on`;
    `mi_bhavisya.py:23, 71-100`; `asset_throughput` row.
  - `L5-F-18` **[NOW]** `query_predictions.ts` ships three untrue statements: a hardcoded
    `sparse_note: 'mimamsa_predictions: 50 rows'`, a description claiming "50 rows per chart" (live:
    139 / 56), and the `base_rate_provenance` comment asserting a `_load_base_rates()` population
    path that does not exist and could not. — *basis:* §N.7 items 3 and 4 — *evidence:*
    `query_predictions.ts:23, 116-129`; SQL.
  - `L5-F-19` **[NOW]** `lifecycle_status` vocabulary disagrees across three surfaces: writer
    writes/protects `{pending, due, confirmed, denied, partial}`, `query_predictions.input_schema.enum`
    allows `{pending, confirmed, denied, expired}`, `prediction_lifecycle_sweep` writes `expired`.
    `due` and `partial` are unreachable through the query filter; there is **no DB CHECK constraint**
    on the column. — *basis:* §N.6 item 4; C12 M-04 enum-validation discipline — *evidence:*
    `pg_constraint` returns none for `mimamsa_predictions`.
  - `L5-F-20` **[NOW]** `prediction_lifecycle_sweep` — the one piece of live P7 seam machinery that
    closes lapsed windows — is registered in the retrieval registry (`index.ts:54`) but appears in
    **zero** tool projections. **Built-but-unplugged.** With 12 canonical + 8 Abhinandan predictions
    whose windows have fully elapsed and 195/195 still `pending`, nothing reachable can transition
    them. — *basis:* D-SERVICE; plan §5 L5 mandate item 3 — *evidence:* grep over the three generated
    projection files; SQL.
  - `L5-F-21` **[NOW]** No `empty_reason`, no `density_contract` on `query_predictions`. Zero of 16 L5
    capabilities declare a `density_contract` (L1 has 8, L2 4, L4 2). — *basis:* D-SERVICE; §N.6 item 4.
  - `L5-F-22` **[NEVER/LATER]** Reconciling the two prediction stores into one. — *reason:* both are
    live, both documented, and the duplication is *already* explicitly dispositioned in
    `prediction_lifecycle_sweep.ts:12-58`. D-TIME item 4 ("duplications get explicit dispositions") is
    **already satisfied** — record the disposition, do not act on it. Deferred register (plan §7.3).
- **Proposed route:** `changed` — F-15 (cross-layer, resolves in L4's wave) plus F-16/F-17 are
  correctness items that gate the capsule; F-18/F-19/F-21 are cheap serving-plane honesty fixes.
  **A rebuild is not safe until F-15 is settled** — rebuilding first would itself execute the harm.

---

### `mi_pramana` → `mimamsa_calibration` (57 rows) + `mimamsa_reliability` (6 rows) — the STRUCTURAL-mode heart

- **Purpose / doctrines:** P7 (PARKED) — matches frozen predictions against observed events and
  produces the calibration scorecard. §N.8 is absolute here. Still the right instrument in *shape*;
  the honest question is what its numbers currently mean, and the answer is more mixed than "empty
  structure".

**Q1 — Is `mimamsa_calibration` structural or empirical? What do the rows contain?**
**Neither label is currently accurate; it is *retrodictive-structural*, and no served field says so.**
The 57 rows are **not** NULL placeholders — they contain genuinely computed numbers. But of the five
scored dimensions, **three are constants**:

| dimension | live values (57 rows) | real or constant |
|---|---|---|
| `score_timing` | 43 distinct values, 0.0–1.0 | **real** — computed from window geometry vs event date |
| `score_domain` | `{0, 1}`; 10 hits / 47 misses | **real but structurally broken** (`L5-F-25`) |
| `score_falsifier` | 1 distinct value: `1.0` on all 57 | **constant** |
| `score_magnitude` | `0.5` on **57/57** | **constant** (root cause `L5-F-02`) |
| `score_manifestation` | `0.5` on **57/57** | **constant, and honestly disclosed in code** (JL-018) |
| `base_rate` | `0.10` on **57/57** | **constant** (root cause `L5-F-08`) |
| `brier_vs_null` | populated 57/57 | **derived from the constant 0.10** (`L5-F-24`) |
| `base_rate_adjusted_skill` | **NULL on 57/57** | never computed (`L5-F-26` context) |

`composite_score` range 0.2785–0.841; verdicts: **CONFIRMED 2 · PARTIAL 23 · REFUTED 7 · UNRESOLVED
25**. All rows: `leakage_status='clean'`, `evidence_admissibility='clean'`,
`scoring_formula_version='mi_pramana_v2.0'`. Coverage: **13 of 139** canonical predictions matched,
against **24 of 64** events. Abhinandan: **0 rows** (0 life events → 0 provenance → 0 matches),
correctly and gracefully. **Live `evidence_grade` distribution (`mimamsa_reliability`, 6 strata,
canonical only):** `empirical` **4 strata** (n = 13, 12, 18, 7) · `prior_only` **2 strata** (n = 4, 3).
`held_out_validity`: `pass` **4** · `insufficient_n` **2**. **`structural_no_calibration` does not
appear — see Q3.**

**Q2 — Does anything record a real OUTCOME? Traced to source table and column.**
**No prediction in this instrument has a recorded outcome.**
- `mimamsa_predictions.lifecycle_status` = `'pending'` on **195/195** rows, both charts. Rows ≠
  `pending`: **0**.
- `mimamsa_journal` — the native's answer surface, and the *only* write path that moves
  `lifecycle_status` past `pending` (`mi_bhavisya.py:217-218`) — has **0 rows**.
- `mimamsa_predictions` has **no outcome column at all**. `outcome_claim` is the *prediction's* claim
  text, not a result.
- What `mi_pramana` actually consumes as "outcome" is `mimamsa_event_provenance` — i.e. **real lived
  events**, so the corpus side is genuine `pratyaksa`. But the linkage is a **machine retrodictive
  match** (`_substep_match`, :309-327: does any admissible non-held-out event fall inside this
  prediction's window?), never a human adjudication. `_verdict_v2` then grades that match. **So
  `composite_verdict = 'CONFIRMED'` means "an event of some kind occurred inside this window and the
  composite cleared 0.65" — not "this prediction came true."**
- Two adjacent fields that look like outcomes and are not: `life_events.outcome_observed` (62 true /
  1 false / 1 null) and `life_events.provenance->>'outcome'` (`yes|partial|pending`) — the latter is
  the LEL's `retrodictive_match.predicted_by_chart` field, which grades a *2026 Deep-Analysis signal
  set*, not a `mimamsa_predictions` row. Neither is read by `mi_pramana`.

**Q3 — Is `evidence_grade` an earned signal? What would have to fail for it to read otherwise?**
**Partly earned, and materially mislabelled — and the seal's claim about it is false.**
- The detector is one line: `grade = "empirical" if n >= 5 else "prior_only"` (`mi_pramana.py:474`).
  That *is* a real detector — it measures bin population and it does change value. Not a hardcoded
  green.
- **But it measures the wrong thing.** `empirical` asserts empirical evidence; the only thing tested
  is that ≥5 machine-derived matches landed in a probability bin. No observed outcome underlies any
  of them (Q2). All four `empirical` strata today have zero adjudicated predictions in them.
- **`structural_no_calibration` does not exist in the codebase.** `grep -rn` across the entire repo
  returns **four hits, all in governance markdown** — `L5_SEAL_AND_SHIP_REPORT_v1_0.md:79` (gate G8,
  marked PASS), `:108` ("No honesty bug found…"), `CURRENT_STATE_v1_0.md:1613`, `SESSION_LOG.md:29741`.
  **Zero hits in `.py`, `.ts`, or `.sql`.** And the code path the seal describes cannot produce it:
  when `cal_rows = 0`, `_substep_reliability` returns early at :447-450 and writes **zero** reliability
  rows — so it emits no `evidence_grade` at all. The G8 PASS is a green with no detector behind it:
  §N.8's defect class, in the seal that certifies the layer.
- **`held_out_validity` is worse and is not earned at all.** Its computation is
  `"pass" if n >= 5 else "insufficient_n"` (:473) — the same bin-count test, with nothing about
  held-out status in it. And it cannot be about held-out data: `_substep_match` filters to
  `held_out = false` (:301), so **every** scored row is by construction *not* held out. Four strata
  read `held_out_validity = 'pass'` over a sample with zero held-out members.

**Q4 — Given a post-seal harness cycle evidently ran (2026-08-13), is what it consumed still
reconstructible?** **Today: yes, fully. On the next rebuild: no — and one number already does not
reconcile.**
- **Reconstructible now.** Full referential integrity, verified by live LEFT JOIN, all four links
  zero orphans. `mimamsa_attribution` holds 1425 rows over 2 families (`fam_graha_natal` 1355 / 57
  matches; `fam_transit` 70 / 7 matches).
- **Already lossy in one place.** The two promoted multipliers carry `n_observations` **271** and
  **14**, which reconcile with no live quantity found here. **UNKNOWN — settled by** `mi_gunanaka`'s
  aggregation SQL (handed to Batch C, which resolved it: 285 = 57 calibration rows × 5 top signals).
- **Lossy on the next rebuild, structurally.** `_substep_score` opens with
  `DELETE FROM mimamsa_calibration WHERE chart_id = %s` (:342) and `_substep_reliability` the same on
  `mimamsa_reliability` (:445). There is **no calibration history, version, or snapshot table**
  anywhere in the schema. Combined with `L5-F-15`, a single `ph_nimitta` rebuild both breaks every
  stored `prediction_id` reference **and** deletes the rows that held them — nothing archived.

- **Dependencies (declared → real):** Declared
  `{mi_bhavisya, mi_jivanaghatana, bg_ghatana, bg_formula_constants}`. Real reads:
  `mimamsa_predictions` + `mimamsa_manifestation_sets` ✅, `mimamsa_event_provenance` ✅,
  `brahma_formula_constants` ✅, `brahma_event_ontology` (→ `bg_ghatana` — **declared but dead**:
  `_load_base_rates` selects a `base_rate` column that does not exist; its exact SQL run against
  production errors, and the bare `except` returns `{}` every time). **One dead edge; no hidden edges.**
- **Leverage:** **Three.** (a) The `base_rate` NULL-write-back originates here — :407 says
  `base_rate_adjusted_skill` is "computed in reliability", and `_substep_reliability` never touches
  `mimamsa_calibration`, so it is NULL 57/57 forever. (b) `brahma_event_ontology.base_rate_by_age`,
  `.magnitude_floor`, `.lel_category`, `.domain` are all populated and all unread. (c)
  `query_calibration` serves `ece` from `mimamsa_reliability`, which the writer explicitly passes
  `None` (:485) — the served scorecard advertises an Expected Calibration Error that is never computed.
- **Grounding:** `pratyaksa` — and doing so plainly is the *right* answer, not a concession. **But
  `pratyaksa` obliges the provenance to be real**, and three of the six numeric fields are constants
  dressed as computations. An honest `pratyaksa` label plus a per-row `dimensions_constant`
  disclosure would be a genuine success; the current unlabelled mix is not.
- **Service:** Real, live consumer: `query_calibration`, registered, in all three projections; MCP
  alias `mimamsa_calibration_get`, with a documented CR-51/CR-30 fix that collapsed a divergent
  sidecar path into this one. The capability is unusually good on §N.6 discipline —
  `verdict_row_count`, `domain_filtered_sections` / `domain_unfiltered_sections`,
  `multipliers_with_domain` are honest measured coverage counters. **Not unplugged and not lazy.**
  Its gap is that it faithfully serves fields whose *values* are hollow, and it has **no
  `empty_reason`** and no `density_contract`. Drill depth: `match_id → prediction_id →
  source_pramana_id (L4 anchor)` = 2 hops to L4; to L1 it is 3+ hops, so the ≤2-hop-to-L1 target is
  **not** met — though `grounds_to: { l1_fact_ids: false }` is honestly declared.
- **Cost:** estimated 1s. Measured: **UNKNOWN** — no receipts. Last builds: canonical
  `2026-08-21T02:36:53Z`, rows_written 63, state **`error`** (`BLOCKED: … mi_bhavisya did not
  complete`, cascaded from `mi_bhavisya`'s block on its two false edges); Abhinandan
  `2026-08-12T17:11:55Z`, 0 rows, state `lit`. Writer shape: **heavy** — 3 substeps. Real cost driver
  is the O(preds × events) nested match loop (:309-327), currently 139 × 24 — trivial now, quadratic
  later.
- **Findings:**
  - `L5-F-23` **[MUST]** `held_out_validity` is an unearned signal: it claims held-out validity and
    computes `n >= 5`, over a sample from which held-out rows are *excluded by the query that built
    it*. Four strata read `'pass'`. No code path could make it read otherwise. — *basis:* §N.8
    verbatim; §N.7 item 4 — *evidence:* `mi_pramana.py:473` vs :301; SQL. **Disposition: rename to
    what it measures (`sample_size_validity`) or NULL it, and document. Never a fill; never a
    weakening.**
  - `L5-F-24` **[MUST]** `brier_vs_null` is populated 57/57 and computed against a **hardcoded
    climatology prior of 0.10** on every row, because `_load_base_rates` queries a non-existent
    column and `event_class_id` is NULL 64/64 — so **both** branches of
    `base_rates.get(event_class_id, 0.10) if event_class_id else 0.10` resolve to the literal. A
    "skill versus climatology null" number whose null is invented is an invented calibration value.
    — *basis:* §N.8 (absolute here per the L5 mandate item 5); §N.7 item 6 — *evidence:*
    `mi_pramana.py:84-85, 388, 390-392`; live SQL. **Disposition: NULL `brier_vs_null` and
    `base_rate` and record the missing prior source. Do not substitute a different plausible prior —
    that would be the same violation with a nicer number.**
  - `L5-F-25` **[MUST]** `_score_domain` is exact string equality between two **unreconciled
    vocabularies**: predictions use `{career, character, health, relationship, spirituality,
    transition, wealth}`, events use LEL categories `{career, creative, education, family, finance,
    health, loss, other, psychological, relationship, residential+travel, spiritual, travel,
    travel_event}`. Overlap is **3 of 7**. `spirituality` never matches `spiritual`; `wealth` never
    matches `finance`; `character`/`transition` match nothing. Result: **47 of 57 rows score
    `domain = 0`**, and `domain` carries weight **0.278** — the second-largest term — so
    `composite_score` and every verdict derived from it is systematically depressed by a naming
    mismatch, not by evidence. The bridge already exists and is unused:
    `brahma_event_ontology.lel_category` + `.domain`. — *basis:* §N.7 item 1; C12 "derive, never
    pick" — *evidence:* SQL distinct-value lists; `dom_hit = 10`, `dom_miss = 47`;
    `mi_pramana.py:135-136, 55`.
  - `L5-F-26` **[MUST]** The L5 seal's gate **G8 is a false PASS**. `L5_SEAL_AND_SHIP_REPORT_v1_0.md:79`
    records "mi_pramana evidence_grade correct for structural mode | PASS —
    `structural_no_calibration` when cal_rows=0" and :108 "No honesty bug found." The string exists
    nowhere in the codebase, and the `cal_rows = 0` path writes zero rows and therefore no grade.
    — *basis:* §N.8; C12 ("a check that has never been green is a PROPOSAL" — here, a check that was
    *recorded* green and never existed) — *evidence:* `grep -rn "structural_no_calibration"` → 4
    hits, all `.md`, 0 in code; `mi_pramana.py:447-450`. **Correct in the seal record, in place, as
    part of mandate item 1.**
  - `L5-F-27` **[MUST — mandate item 1, the documentation route]** **The STRUCTURAL declaration's
    stated justification is stale and its stated evidence is now false, and both must be rewritten as
    *deliberate*.** (a) The seal frames STRUCTURAL as transitional — "it transitions to empirical mode
    after L4 seals and the first harness cycle runs" (:25) — and precondition 1 has **been met** (L4
    Phala CLOSED 2026-06-29, two days after the seal), so to any fresh reader the layer now reads as
    unfinished work waiting on a cleared dependency. (b) The seal's evidence — "all 9 multipliers …
    carry `promotion_status = 'prior_only'`" — is **factually false live**: 18 multipliers,
    **16 `prior_only` + 2 `promoted` with `gate_passed = true`**. (c) The seal says "12 `mi_*`
    assets"; the registry carries **15** L5 assets. **The correct current justification, supportable
    from evidence:** STRUCTURAL is deliberate because *no prediction in the instrument has a recorded
    outcome* — 195/195 `pending`, `mimamsa_journal` empty, no outcome column, and the only reachable
    adjudication path never exercised — **and** because P7 is PARKED by native ruling to a subsequent
    programme (plan §0, §7.3). Not "L4 hasn't sealed." An empirical calibration surface without
    outcome data would be fabricated; the structural surface is the honest one. — *basis:* plan §5 L5
    mandate item 1; §N.8; §N.4.
  - `L5-F-28` **[NOW]** `evidence_grade = 'empirical'` on 4 strata overstates what the detector
    measures (bin population ≥5, over zero adjudicated outcomes). The grade vocabulary needs a value
    meaning "structurally matched, no outcome adjudicated" — which is what the seal *thought*
    `structural_no_calibration` was. — *basis:* §N.8; §N.7 item 5 — **a labelling correction, not a
    value change; no number moves.**
  - `L5-F-29` **[NOW]** Three permanently-constant or permanently-NULL served fields with no
    disclosure: `score_magnitude` 0.5 on 57/57, `score_falsifier` 1.0 on 57/57,
    `base_rate_adjusted_skill` NULL on 57/57 (:407 promises "computed in reliability";
    `_substep_reliability` never writes to `mimamsa_calibration`). `query_calibration` serves
    `mean_magnitude` from the first with no flag. `score_manifestation` is the model to follow — also
    constant 0.5, but *explicitly disclosed* in a 10-line JL-018 comment with its weight removed from
    the composite (:42-55). — *basis:* §N.7 item 6; §N.6 item 1.
  - `L5-F-30` **[NOW]** `mimamsa_reliability.ece`, `.log_loss`, `.ci_low`/`.ci_high` are written
    `None` unconditionally (:482-485) yet `ece` is named in `query_calibration`'s SELECT and in its
    own description ("reliability curve (ECE/Brier)"). — *basis:* §N.7 item 4.
  - `L5-F-31` **[NOW]** `integrity_check_sql IS NULL`; `catalog_status='DRAFT'`;
    `expected_volume_formula IS NULL` with `volume_explanation` "Accumulates as prediction outcomes
    are recorded — not a deterministic target" — honest and correct, which means the right check here
    is **invariants, not volume**. Available and passing live: (a) zero-orphan FULL JOIN
    `mimamsa_calibration ↔ mimamsa_predictions` and `↔ mimamsa_event_provenance`; (b)
    `match_id = prediction_id || '_' || event_id` for every row; (c) `mimamsa_attribution.match_id`
    fully covered by `mimamsa_calibration`; (d) every scored row satisfies
    `leakage_status='clean' AND NOT held_out` — the leakage invariant the layer exists to protect,
    and one that *can* fail on real corruption. **Never a `count(*) = 57`.** — *basis:* C12; §N.4.
  - `L5-F-32` **[NOW]** No `empty_reason` and no `density_contract` on `query_calibration` — and this
    surface needs it most, since a 0-row return is the *expected* state for any chart without a LEL.
    — *basis:* D-SERVICE; §N.6 item 3.
  - `L5-F-33` **[NEVER/LATER]** Computing real ECE / log-loss / confidence intervals, wiring the
    outcome-intake loop, per-event-class base rates, a calibration-history/snapshot table.
    — *reason:* every one **adds calibration or learning machinery**, out of scope per the L5 mandate.
    Deferred register (plan §7.3). **The calibration-history table is the one most worth naming
    there**, since `L5-F-15` + the unconditional DELETEs make its absence load-bearing.
- **Proposed route:** `changed` — **explicitly not `rebuild_only`, and not `verified_reuse`.** The
  honest-labelling corrections (F-23, F-26, F-27, F-28, F-29, F-30) move **no number**; F-24 and F-25
  are correctness items that gate the capsule. A rebuild must wait on F-15: with `prediction_id`
  non-deterministic and no calibration history, rebuilding *is itself* the provenance loss the
  mandate forbids.

---

## Batch notes

1. **One root defect explains most of this batch, and it is a swallowed exception.**
   `mi_jivanaghatana._lookup_event_class` and `mi_pramana._load_base_rates` both query columns that do
   not exist on `brahma_event_ontology` (`category`/`subcategory` and `base_rate`; the live schema has
   `domain`, `lel_category`, `base_rate_by_age`). Both are wrapped in `try/except` returning a
   fallback. Both predicates were run against production and both error. The cascade: `event_class_id`
   NULL 64/64 → `base_rate` 0.10 on 57/57 → `brier_vs_null` computed against an invented prior on
   every row. **Two broken column names, silently absorbed, produce the layer's only
   fabricated-looking calibration numbers.** Worth naming for the campaign: *a bare `except` around a
   schema-coupled read converts a loud schema drift into a quiet constant.* Both declared `bg_ghatana`
   edges are therefore dead edges.

2. **`L5-F-15` is the only finding here that crosses layers, and it left this batch as a
   capability-delta (charter C6) to L4** — escalated as issue **#1732** after independent
   re-verification by the L5 session.

3. **The two `error`-state canonical builds are both blocked by false edges.** `mi_bhavisya`
   (2026-08-21) was blocked on `ph_phaladesa` and `ph_pramana` — neither of which it reads — and
   `mi_pramana` cascaded off that. Fixing F-17 unblocks two real builds. For WP-3's disposition
   taxonomy: `blocked_dependency(reason)` is only as truthful as `depends_on`, and here it
   demonstrably is not.

4. **STRUCTURAL mode is real but the label is doing less work than it appears.** The 57 calibration
   rows are not empty scaffolding — `score_timing` genuinely varies across 43 values and the verdict
   spread (2/23/7/25) is genuinely computed. What is missing is not *structure*, it is **outcome**.
   The correct re-documentation is narrower and stronger than "structural placeholder": *the matching
   and scoring machinery is live and computing real values from real lived events; no prediction has
   been adjudicated, and none can be until P7's outcome-intake programme runs.*

5. **Serving discipline is bimodal across L5 and the split is informative.** `query_calibration` and
   `prediction_lifecycle_sweep` are among the most carefully-reasoned files in the layer. Meanwhile
   **zero of 16** L5 capabilities declare a `density_contract` (L1 has 8, L2 4, L4 2), 8 of 16 have
   `empty_reason`, and the **three headline P7 surfaces** (`query_calibration`, `query_predictions`,
   `lel_query`) are all in the missing half. The gap is not carelessness; the `density_contract` field
   never propagated to L5 — a cheap, bounded, in-scope `NOW` sweep rather than a redesign.

6. **Stale hardcoded counts recur across four surfaces and all say 50 or 57.**
   `query_predictions.ts` ("50 rows per chart", twice), `query_life_events.ts:5` ("57 rows"),
   `assetClearSpec.ts:216` ("the 57 native events"), and the L5 seal ("50 rows", "9 multipliers",
   "12 assets"). Live: 139/56 predictions, 64 life events, 18 multipliers, 15 assets. Individually
   cosmetic; collectively a §N.7-item-3 pattern worth a single sweep, since three of the four are
   strings a caller or a reader is expected to trust.

7. **Honest gaps.** Measured build/serve cost for all four assets is **UNKNOWN**: zero
   `asset_provenance_receipts` rows exist for any of them (consistent with the O-wave's ~8/128
   receipt-coverage finding), `asset_throughput` has no duration column, and
   `rows_per_second`/`measurement_count` are NULL/0 throughout. One instrumented rebuild with receipt
   capture would settle all four — but per note 2, **not before `L5-F-15` is resolved.**
