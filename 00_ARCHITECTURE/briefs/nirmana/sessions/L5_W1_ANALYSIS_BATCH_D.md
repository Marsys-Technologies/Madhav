---
artifact: L5_W1_ANALYSIS_BATCH_D.md
canonical_id: NIRMANA_L5_W1_ANALYSIS_BATCH_D
version: "1.0"
status: CURRENT — W1 ANALYZE output, L5 (Mīmāṃsā)
session: L5
produced_on: 2026-09-05
scope: mi_vistara · mi_seva · mi_sankalpa (the three empty tables)
method: >
  Read-only fresh-context analysis subagent against the plan §4 W1 rubric, the five doctrines,
  charter C12, and CLAUDE.md §N.4/§N.6/§N.7/§N.8. No repo write, no DB write. The batch's central
  task was to distinguish, with evidence, between DELIBERATELY DORMANT / BUILT-BUT-UNPLUGGED /
  BROKEN for three zero-row assets.
---

# L5-W1 — Batch D: export, preferences, interventions (the three empty tables)

### `mi_vistara` — global, append-only export-integrity ledger (`mimamsa_export_log`); the audit boundary for what LEAVES the instrument

- **Purpose / doctrines:** P8 (D-SERVICE) and the epistemic-hygiene half of P3/D-GROUNDING: it exists
  so that *what the instrument told whom, under which disclosure* is reconstructable. Spec
  `00_ARCHITECTURE/L5_SPECS/11_mi_vistara_SPEC_v1_0.md` §1 ties it to the MACRO_PLAN §3.5.G
  calibration-disclosure obligation **at the export boundary**. Still the right instrument: the
  obligation is real and nothing else in the corpus discharges it.
- **Dependencies (declared → real):** declared `[]` → real `[]`. **Verified, not assumed:** the writer
  (`writers/mi_vistara.py:43-58`) issues exactly two statements — an `information_schema.tables`
  existence probe and `SELECT COUNT(*) FROM mimamsa_export_log`. No hidden edge, no false edge. **The
  only L5 asset whose declared dependency set is exactly correct.** Spec §8's `[P2 reconcile]` note
  ("reads mi_seva/mi_darshana at export time") is a *serve-time* relationship, correctly kept out of
  the build DAG.
- **Leverage:** **A real, unplugged export surface exists.**
  `platform-mcp/src/tools/register_p1_synthesis.ts:919-944` (`synth_chart_brief_get`) assembles and
  returns an MCP bundle carrying `calibration_mode`, `calibration_note`, `lel_disclosure`,
  `formula_version` and the served insight rows — *precisely* the tuple `mimamsa_export_log` is shaped
  to record. Nothing writes a ledger row. **Every MCP bundle that has ever left the instrument left
  unlogged.** Secondary: `register_p1_synthesis.ts:931` hardcodes `calibration_mode: 'STRUCTURAL'`,
  which is **not a member** of the spec's declared enum (`'empirical' | 'prior_only' |
  'structural_prior_only'`) — a vocabulary divergence that would make any future ledger row from this
  surface fail its own vocabulary check.
- **Grounding:** carries no interpretive claim; the table has no `grounding_tier` column and needs
  none. Every column is `pratyaksa` (hashes, timestamps, ids, mode labels). Labelling it
  `sruti`/`yukti` would be a category error, and adding a tier column would be noise.
- **Service:** consumer = **none today; disposition RECORDED twice.** (1)
  `asset_registry.english_description` carries an explicit, reasoned SCOPE EXCEPTION (PD-6 / BA-P0):
  `scope='global'` is correct because migrating to `per_chart` would let delete-then-insert wipe audit
  records on chart rebuild. (2) `platform/src/lib/cockpit/assetClearSpec.ts:179-188` sets
  `mi_vistara: null` with a written rationale — the auto-derived DELETE would be unscoped and wipe
  every chart's log. **Producer status:** the sole `INSERT INTO mimamsa_export_log` in the repo is
  `platform/python-sidecar/brahmagyan/mimamsa/export_to_bigquery.py:342`, which writes
  `(export_id, export_at, table_name, row_count, gcs_path, source_citation)` — the **brahma-era schema
  that migration `346a_drop_legacy_mimamsa.sql:16` DROPPED and migration 355 replaced with an entirely
  different column set.** That producer is dead code against a schema that no longer exists; it would
  throw `column "export_at" does not exist` if ever invoked. Not the ledger's defect, but it must not
  be mistaken for a live producer.
- **Cost:** estimated **1s** · **measured: 39 timed runs, mean 0.287s, min 0.019s, max 1.460s**
  (`build_run_assets`, through 2026-07-27). Writer shape: light `run(ctx)`, two statements, no
  substeps, no writes. Estimate honest.

- **STATE VERDICT — DELIBERATELY DORMANT, with one built-but-unplugged consumer-side defect.** The
  table is a designed append-only log whose trigger (an export delivery) has never fired; the writer
  is *specified* to originate zero rows (spec §7). It is **not broken**. It **is** true that an
  export-shaped surface exists and does not log — that defect lives in the serving plane, not in
  `mi_vistara`.

- **CANARY BUILD→VERIFY→FREEZE PATH (concrete):**
  1. **What the writer actually does:** asserts `mimamsa_export_log` exists (raises `RuntimeError` if
     not — a real fatal, unlike `mi_seva`), counts existing rows, logs the count, returns
     `WriterResult(rows_inserted=0, notes=...)`. It never writes.
  2. **What a build would produce:** zero rows. Side effects: (a) the existence assertion; (b) a log
     line; (c) `asset_throughput` promotion; (d) under O-wave WP-1, the **first provenance receipt any
     `mi_*` asset would ever have** — `SELECT … FROM asset_provenance_receipts WHERE asset_id LIKE
     'mi_%'` returns **zero rows** today.
  3. **Can it terminate honestly with 0 rows? YES — and it already has.** Live `asset_throughput`:
     `asset_id='mi_vistara', chart_id=NULL, state='lit', rows_written=0, last_built_at=
     2026-08-02T13:50:52Z`. The promotion is *earned*: `asset_runner.py:1026-1032` computes
     `zero_rows_is_complete = (chart_id is None) or (target_floor == 0)` and `mi_vistara` satisfies
     **both** limbs.
  4. **A non-fabricated integrity check.** Spec §6 already names the right invariant — the
     **disclosure-present gate** — and it survives C12's rewrite-floor test. Proposed, and **executed
     read-only against production, returning `true`**:
     ```sql
     SELECT
       (SELECT count(*) FROM mimamsa_export_log
          WHERE calibration_mode = 'empirical'
            AND (disclosures_attached IS NULL
                 OR disclosures_attached = '{}'::jsonb
                 OR disclosures_attached = '[]'::jsonb)) = 0
       AND (SELECT count(*) FROM mimamsa_export_log
             WHERE calibration_mode NOT IN ('empirical','prior_only','structural_prior_only')
                OR export_format   NOT IN ('pdf','json','mcp_bundle','portal_view')) = 0
       AND (SELECT count(*) FROM mimamsa_export_log
             WHERE btrim(payload_hash)='' OR btrim(lel_version)=''
                OR btrim(export_formula_version)='') = 0
       AND NOT EXISTS (SELECT 1 FROM mimamsa_export_log e
                        LEFT JOIN charts c ON c.id = e.chart_id WHERE c.id IS NULL)
       AND (SELECT count(DISTINCT export_id) FROM mimamsa_export_log)
         = (SELECT count(*) FROM mimamsa_export_log)
     AS ok;
     ```
     **Honesty caveat that MUST ride with it into the capsule:** on an empty table this passes
     **vacuously**. It constrains all future rows; it attests nothing about content today. A capsule
     claiming "integrity verified" without that sentence would be exactly the §N.8 defect.
  5. **W4 DISPATCH — the canary-blocking fact.** WP-3 domain scoping is **already landed** in
     `platform/src/lib/build/plan.ts`. `isLayerSweepExcludedDomain` (~:191) returns true for
     `domain='shared'`, and `computeLayerDispositions` (:441-444) assigns such rows the disposition
     **`out_of_domain`** — enumerated but never built. Therefore **a `scope='layer'`,
     `scope_target='mimamsa'` dispatch will NOT build `mi_vistara`.** It must be dispatched via
     **`scope='asset'` with `scope_target='mi_vistara'`** (:205), or `scope='asset_set'`, or
     `scope='global'` (:199). Chart binding is handled correctly and automatically:
     `pipeline/orchestrator/runner.py:691` (`return None if asset_scopes.get(a) == "global" else
     chart_id`) forces `chart_id=None`, and :1096 acquires the global-assets advisory lock. **No new
     code is needed to dispatch this canary — only the correct scope selector.**

- **Findings:**
  - `L5-F-D01` **[MUST]** Any W4 dispatch of `mi_vistara` must use `scope='asset'`/`'asset_set'`/
    `'global'`; a `scope='layer'` L5 sweep silently assigns it `out_of_domain` and it never builds. A
    canary that cannot be dispatched is not a canary. — *basis:* plan §3.3 WP-3 — *evidence:*
    `platform/src/lib/build/plan.ts:189-206, 441-444`.
  - `L5-F-D02` **[NOW]** Author `integrity_check_sql` = the disclosure-present gate above, and record
    in the same PR that it passes **vacuously** on an empty table. — *basis:* C12 + §N.8 — *evidence:*
    proposed SQL executed read-only, returned `ok=true`; `count(*) FILTER (WHERE integrity_check_sql
    IS NOT NULL)` over `layer='mimamsa'` → **0**.
  - `L5-F-D03` **[NOW]** Populate `expected_volume_formula`/`expected_volume_inputs` with the honest
    derived expectation for an append-only event log: `expected = count of logged export events`, i.e.
    **event-driven, unbounded-below, floor 0** — NOT a count pin. C12 names a NULL here as the defect;
    the honest fill is a formula saying "volume is exogenous," not an invented number. — *basis:* C12
    + §N.4 — *evidence:* live `expected_volume_formula IS NULL`, `volume_explanation = 'Accumulates
    with each export event — operational audit log'` (the prose is already correct; the
    machine-readable field is empty).
  - `L5-F-D04` **[NOW]** Retire or fence
    `platform/python-sidecar/brahmagyan/mimamsa/export_to_bigquery.py::_write_export_log` — it writes
    six columns none of which exist on the live table. A latent runtime error masquerading as the
    ledger's producer. — *basis:* D-SERVICE built-but-unplugged — *evidence:* `export_to_bigquery.py:342`
    vs `355_mimamsa_vistara.sql:6-20`; old schema dropped at `346a_drop_legacy_mimamsa.sql:16`.
  - `L5-F-D05` **[NOW]** `synth_chart_brief_get` emits `calibration_mode: 'STRUCTURAL'`, outside the
    ledger's declared enum. Align to `'structural_prior_only'` (or record the divergence as a
    deliberate second vocabulary). Cheap, and the *precondition* for D06 ever being correct.
    — *basis:* §N.7 item 3 — *evidence:* `register_p1_synthesis.ts:931` vs
    `11_mi_vistara_SPEC_v1_0.md` §3.
  - `L5-F-D06` **[NEVER/LATER]** Wiring an actual export→ledger write path. New service machinery on
    the P7 seam, not in the L5 mandate's five items. Park with the deferred register. — *basis:* plan
    §7.3; L5 mandate — *evidence:* zero `INSERT` into the live schema anywhere in `platform/src` or
    `platform-mcp/src`.
  - `L5-F-D07` **[NOW]** `mi_vistara.py`'s docstring calls it "a service asset"; `asset_kind='data'`.
    Correct the docstring (not the registry — `data` is right, since a genuine `service` kind would
    route it into the probe path it has no probe for). — *basis:* §N.7 item 1 — *evidence:*
    `mi_vistara.py:9`.
- **Proposed route:** `rebuild_only` — a two-statement existence assertion with no upstream, measured
  at 0.287s mean; one accepted execution (via `scope='asset'`) re-establishes `state='lit'` and
  captures **L5's first provenance receipt**. Nothing in its code needs to change to build; D02/D03
  are registry rows, D04/D05/D07 are disjoint files.

---

### `mi_seva` — declared serve-time contribution-control gateway (`mimamsa_preferences`); `asset_kind='service'`, `service_health IS NULL`

- **Purpose / doctrines:** P8 (D-SERVICE) end-to-end: per spec
  `00_ARCHITECTURE/L5_SPECS/10_mi_seva_and_mi_abhilekha_SPEC_v1_0.md` §A1–A4 it is *the* query-time
  entry point to L5 — effective-value resolution (base ⋈ `mi_adhilepa` overlay) under a
  `learning_influence` toggle, an `lel_citation` gate, per-family/tier/soundness filters,
  transit-current binding, `contribution_state` metadata on every response, and portal↔MCP parity.
  Doctrinally the most load-bearing L5 asset that exists; whether the *asset* is still the right
  instrument is a live question.
- **Dependencies (declared → real):** declared `['mi_adhilepa']` → **real: none.** The writer
  (`writers/mi_seva.py:36-58`) reads no data; it loops `information_schema.tables` over four names
  (`mimamsa_multipliers`, `mimamsa_signal_adjustment`, `mimamsa_insight_units`, `mimamsa_journal`).
  The edge is not merely unused but *mis-aimed*: `mi_adhilepa`'s own target table
  `mimamsa_load_bearing` is **not** among the four checked. It is a **catalog-lineage edge** (spec §A5
  says so explicitly), and it has a measured cost: `build_run_assets` shows **12 runs of `mi_seva`
  terminated `BLOCKED: upstream dependency(ies) mi_adhilepa did not complete in this run`**, for a
  writer that would not have read a single row from that upstream.
- **Leverage — the sharpest finding in this batch:** **The overlay `mi_seva` is supposed to *gate* is
  already being read directly, bypassing the gate.** `compute_spine_bundle.ts:180` reads
  `mimamsa_calibration`, `mimamsa_reliability`, `mimamsa_multipliers`;
  `L5_mimamsa/query_calibration.ts:4` does the same. Meanwhile
  `grep -rn "learning_influence\|lel_citation\|saved_state\|contribution_state"` across `platform/src`
  + `platform-mcp/src` returns **zero non-generated hits**. So: the overlay is consumed, and the
  toggle that is supposed to govern that consumption — including the spec §A4 **OFF==baseline gate
  (RL-2)** — does not exist anywhere. The consumer is not reading NULL; it is reading the value
  *without the control the design placed in front of it*.
- **Grounding:** N/A on rows (`mimamsa_preferences` is `user_id, channel_id, saved_state, updated_at`
  — pure per-user UI state, no chart, no claim). But the spec's `contribution_state` metadata is
  exactly a `pratyaksa` provenance label and *should* be one when built.
- **Service:** consumer = **none; the service itself does not exist.**
  `platform/python-sidecar/services/mi_seva/` **does not exist** (siblings `services/mi_bhara/`,
  `services/mi_sankalpa/`, `services/ka_muhurta_seva/` all do), so `mi_seva.py`'s docstring pointer to
  "`services/mi_seva/handler.py` (TypeScript retrieval layer)" is doubly wrong — wrong extension and
  a nonexistent path. Disposition **is** recorded for the destructive edge:
  `assetClearSpec.ts:171-177` sets `mi_seva: null`, blocking the derived unscoped
  `DELETE FROM mimamsa_preferences` that would have wiped every user's preferences (finding C-D2-10,
  `BUILD_PATH_RETRIEVAL_AUDIT_FINDINGS_v1_0.md:119`), and the comment names the proper fix as still
  outstanding.
- **Probing (charter C12) — what it means, whether a path exists, what it would assert:**
  - **A probe path does NOT exist, and cannot be reached without changing three things.**
    `platform/src/app/api/cockpit/plan/route.ts:52-60` admits a service to the probe path only if it
    is in `COCKPIT_DISPATCHABLE_SERVICE_PROBE_IDS` = `['bg_ephemeris_engine','bg_panchanga']`
    (`serviceProbeContract.ts:11-14`), **and** `scope='global'` **and** `has_writer !== true` **and**
    `health_probe IS NOT NULL`. `mi_seva` fails all four.
  - **The orchestrator forecloses it from the other side too.** `asset_runner.py:1412-1424`: for
    `is_service`, *if a registered WriterBase writer exists*, it routes to `_run_data_writer` and
    **returns before** `_run_service_health_probe` — so `service_health` / `last_selftest_at` /
    `last_invoked_at` are never written, by construction. This is why `service_health IS NULL`: not a
    missing probe spec, a foreclosed code path.
  - **The cockpit is nonetheless honest about it.** `deriveState.ts:73-81` requires
    `service_health='healthy'` AND a measured timestamp AND `throughputState IN ('lit','service_ok')`
    before showing `service_ok`; `mi_seva` therefore renders **`dormant`**, not a false green. No §N.8
    violation in the *display*. The violation is one layer down (F-D09).
  - **The in-repo precedent for the fix exists:** `writers/ka_graha_sancara.py:10, 55, 79, 179` — an
    L3 service *writer* that sets `service_health='healthy' + last_selftest_at=NOW()` on
    `asset_registry` from inside its own `run()` (no commit; orchestrator owns the transaction).
  - **What a truthful probe could assert TODAY, and no more:** "the four overlay/journal tables this
    service would read are present and reachable." That is falsifiable (drop or rename one → red) and
    it is the *entire* honest claim available, because the serve-time resolver does not exist.
    Asserting "contribution controls resolve correctly" would be an invented green.
- **Cost:** estimated **1s** · **measured: 39 timed runs, mean 0.461s, min 0.064s, max 1.725s**
  (through 2026-08-13; a further 12 runs terminated BLOCKED before starting and contribute no timing).
  Writer shape: light, four `information_schema` lookups, no writes.

- **STATE VERDICT — BUILT-BUT-UNPLUGGED, and more precisely: the *table* is deliberately dormant while
  the *service* is UNBUILT.** `mimamsa_preferences` having 0 rows is correct and expected (serve-time
  populated, as `L5_W9_W8_VERIFICATION_REPORT_v1_0.md:172` already records). But unlike `mi_sankalpa`
  — which has a live, tested write path awaiting a trigger — **nothing anywhere can ever write a
  preference row**, because the resolver, the toggles and the parity gate have no implementation in
  either the retrieval layer or MCP. The registry asset is a **placeholder for an unimplemented
  service**, not a facility awaiting its trigger. That is the D-SERVICE named defect class.

- **Findings:**
  - `L5-F-D08` **[MUST]** Registry/seed disagreement on the same field, **and a regression of a gate
    the L5 seal recorded as PASS**. `asset_registry_seed.ts:2882` declares `count_sql: null` and
    `target_floor: null`; live DB has `count_sql='SELECT count(*) FROM mimamsa_preferences'` and
    `target_floor=0`. `L5_SEAL_AND_SHIP_REPORT_v1_0.md:47,58,82` records commit `42738be0` setting
    these to null and gate **G11 "service assets count_sql=null — PASS"**. The live row contradicts
    the seal. — *basis:* §B.8 / GA.1 + §N.8 — **Note:** resolve in the *direction the seal ruled*
    (null) — do not "fix" the seed to match a live row that regressed a gate. `assetClearSpec.ts:171`
    already refuses to act on the live value, which is why the regression has been harmless.
  - `L5-F-D09` **[MUST]** The writer's success signal cannot go red on the exact failure it checks
    for. `mi_seva.py:47-58` returns `WriterResult(rows_inserted=0, notes="WARNING: missing tables …")`
    **instead of raising** when a required table is absent; with `target_floor=0` the orchestrator
    promotes it to `'lit'`. The warning is unreachable to the build system: `WriterResult.notes` is
    defined at `writers/__init__.py:39` and **is read nowhere in `pipeline/orchestrator/` outside the
    writers themselves** (verified by grep). A dropped `mimamsa_journal` would produce a green build.
    Contrast `mi_vistara.py:50-53`, which raises. — *basis:* §N.8.
  - `L5-F-D10` **[NOW]** Have `mi_seva.run()` write `service_health` + `last_selftest_at` from inside
    its own `run()`, mirroring `ka_graha_sancara.py:79/179` — `'healthy'` only when all four tables
    resolve, `'unhealthy'` otherwise (paired with D09's raise). The only way `mi_seva` can ever satisfy
    C12's "lit for a service = current GREEN probe", and it is service hygiene, explicitly in scope.
    — *basis:* C12 service addendum; L5 mandate.
  - `L5-F-D11` **[NOW]** Record a written disposition for the false/mis-aimed `mi_adhilepa` edge —
    either drop it or keep it as declared catalog lineage with the cost acknowledged. Today it costs
    12 recorded BLOCKED terminations. — *basis:* plan §4 rubric item 2; D-SERVICE.
  - `L5-F-D12` **[NOW]** State plainly in the L5 capsule that the `learning_influence` / OFF==baseline
    gate does **not** exist while the overlay it governs is read directly by
    `compute_spine_bundle.ts:180` and `query_calibration.ts`. A disclosure item, not a build item —
    the capsule must not let "mi_seva: lit" be read as "contribution controls are in force."
    — *basis:* §N.8 + D-SERVICE; mandate item 1 (this is the part that is *not* deliberate).
  - `L5-F-D13` **[NEVER/LATER]** Building the serve-time resolver itself (channel registry, toggle
    gates, transit-current binding, MCP parity gate). New service machinery, well outside parked-P7
    seam-keeping; hand to the future programme alongside §7.3's journal/outcome-intake item, which
    shares the same surface (`mi_abhilekha`). — *basis:* plan §7.3; L5 mandate.
  - `L5-F-D14` **[NOW]** Fix `mi_seva.py`'s docstring: it names `services/mi_seva/handler.py` as "(TypeScript
    retrieval layer)" — wrong extension, nonexistent path, and it is the sentence that makes this
    asset *look* plugged in to a reader. — *basis:* §N.7 item 1.
- **Proposed route:** `rebuild_only` — **not `probe`.** C12's probe route is unreachable for this
  asset (four independent gates, all failing), so routing it `probe` would be claiming a verification
  mechanism that does not exist. A rebuild re-runs the real table-existence self-test at 0.461s mean;
  D09+D10 land in W3 and make that rebuild's `'lit'` actually earned. If W2 prefers not to touch the
  writer, the honest fallback is `empty` with D08/D09/D12 carried as open disclosures — but **not**
  `probe`.

---

### `mi_sankalpa` — unified intervention ledger (`mimamsa_intervention_ledger`); the three-armed study of election itself

- **Purpose / doctrines:** the P7 *substrate* — every elected act (upāya · yajña · elected activity)
  with its frozen adjudication record, predicted differential, native attestation and outcome linkage,
  arranged as a four-arm study (`elected_pending`, `acted_with_election`, `elected_not_acted`,
  `acted_without_election`). Also serves D-GROUNDING directly: `efficacy_tier`, `source_citation` (NOT
  NULL, non-blank CHECK) and `paddhati_version` are per-row grounding fields. Still the right
  instrument, and notably **the only asset in this batch whose design was executed to completion.**
- **Dependencies (declared → real):**
  - **Declared:** `['ka_kshetra']`.
  - **Real (writer's actual SQL, `services/mi_sankalpa/db.py`):** `life_events` (:64) and
    `mimamsa_intervention_ledger` (:101, 147, 161, 176, 192, 209, 221, 322, 351). **That is all.**
    `arms.py` and `services/mi_bhara/living_lel.py` issue no SQL (pure functions over passed-in rows).
  - **`ka_kshetra` is a FALSE EDGE for the build.** `kala_field` is never read, never joined, never
    named. Its provenance is explicit and *design-intentional*: migration
    `532_mimamsa_intervention_ledger.sql:194-198` writes
    `UPDATE asset_registry SET depends_on = ARRAY['ka_kshetra']` under the comment "The one edge
    (§8.2 / KALA_W2_FIELD_DESIGN §9.1 / brief §2.5.3) … L3→L5, acyclic." The design's own reasoning
    (`KALA_W4_UPAYA_DESIGN_v1_0.md:1499-1501`) is that the design *specified* this edge, not that the
    writer reads it — and the same document at :668 concedes the field's λ "is empty in production
    today (N_e blocker) ⇒ the factor is reported `not_computed`… never imputed." So it is an
    **ordering/lineage edge asserting a semantic relationship consumed at serve time by a different
    surface (`kala_elect`/`kala_upaya`), not at build time by this writer.**
  - **Is depending on the 8.6M-row monster real?** **No, in the sense that matters for W4.** Live:
    `kala_field` holds **8,599,775 rows for the canonical chart** (11,012,657 across all charts), and
    `ka_kshetra`'s live `asset_throughput` for the canonical chart is **`state='stale'`** with
    `last_error` = the orphan-watchdog message ("301 substep(s) committed and 8599775 data row(s) are
    present, but this route cannot prove the plan finished, so the asset was NOT promoted to 'lit'").
    Since dependency-satisfaction requires `state IN ('lit','service_ok')`, **the declared edge means a
    ~1-second writer that reads zero bytes of `kala_field` is gated behind an un-promotable
    237s-estimated L3 monster.** A real scheduling cost paid for a semantic assertion.
  - **Hidden (undeclared) real edges:** `life_events` — owned by the registry asset **`lel_events`** —
    which is **not** in `depends_on`. Plus three FK edges the schema enforces but the registry does
    not declare: `event_class → brahma_event_ontology(event_class_id)` (L0 `bg_ghatana`),
    `prediction_id → brahma_prospective_ledger(prediction_id)`, `outcome_event_id → life_events(id)`.
- **Leverage:** one designed consumer exists and reads a hardcoded value rather than the table.
  `platform-mcp/src/lib/kala_upaya_diagnosis.ts:1052-1072` (`buildEfficacyReport`) is the §4.5/E6
  read-back; it returns a **compile-time constant** `{state:'honest_empty', n_elected_and_acted: 0,
  n_acted_without_election: 0, n_elected_not_acted: 0, n_outcome_linked: 0,
  n_resolved_prospective_hits: 0}` with a reason naming its own limit ("no MCP-exposed read path at
  this build tier"). Today those zeros are accidentally true. **The moment a native adopts one
  intervention, the function will still report five zeros** — five count fields with no detector
  behind them, presented in the same envelope as its honest `reason`.
- **Grounding:** the interpretive fields are labelable and **largely already are**, in a vocabulary
  that maps cleanly onto D-GROUNDING: `efficacy_tier ∈ {classically_attested, traditional,
  speculative_extension}` ≈ `sruti` / `yukti` / `pratyaksa`, backed by a NOT NULL non-blank
  `source_citation` and a `paddhati_version`, with `adjudication_record` a frozen judgment snapshot
  (§5.5, never recomputed). The `study_arm` classification is honestly `pratyaksa` — deterministic
  from `performed`/`performed_at`/`elected_window`, with `classify_study_arm` returning **`None`
  (leave unchanged)** for the one combination §4.3 left unspecified rather than inventing a
  disposition (`services/mi_sankalpa/arms.py:41-71`). **Should it be labelled?** It effectively already
  is; the only gap is that the mapping `efficacy_tier → grounding_tier` is not written down anywhere a
  doctrine reader would find it. A documentation item, not a schema change.
- **Service:** **a real, complete, tested serve-time WRITE path exists and is wired end to end**: MCP
  tool `kala_upaya_get` (`platform-mcp/src/tools/kala_views/upaya.ts:371`) →
  `recordInterventionLedgerEntry` (`platform-mcp/src/lib/intervention_filing.ts:313+`) →
  `callPlatformWrites('intervention_ledger_record', …)` (`platform-mcp/src/client.ts:288-310`) → route
  `platform/src/app/api/mcp/writes/[action]/route.ts:215,654` → `INSERT` at
  `platform/src/lib/mcp/intervention_ledger_writer.ts:65-78` with
  `ON CONFLICT ON CONSTRAINT mimamsa_intervention_ledger_natural_key DO NOTHING`. The path is guarded
  (mortality HARD EXCLUSION pre-network; `filed_by` stamped server-side; refuses to record when the
  adopted row cannot be resolved, rather than fabricating `efficacy_tier`/`source_citation`) and
  covered by `intervention_filing.test.ts`, `intervention_ledger_record.test.ts`,
  `upaya_weak_promise_gate.test.ts`, and 14 offline writer tests. Density/empty-reason:
  `buildEfficacyReport`'s `honest_empty` + `reason` is correct empty-reason discipline. Drill depth:
  `outcome_event_id → life_events` = 1 hop; `prediction_id → brahma_prospective_ledger` = 1 hop;
  grounding via `source_citation` in-row = 0 hops. Well inside ≤2. **Not unplugged on the write side.**
  The **read** side is unplugged (F-D18).
  - **Stale in-repo claim to correct:**
    `platform-mcp/src/tools/kala_views/intervention_ledger_filing_gate.test.ts:25-31` asserts in prose
    "THERE IS CURRENTLY NO SERVE-TIME WRITE PATH INTO `mimamsa_intervention_ledger` AT ALL." That was
    true when written and is now false. A W1 reader trusting that comment would mis-classify this asset.
- **Cost:** estimated **2s** · **measured: 5 timed completions, mean 1.005s, min 0.332s, max 1.708s**
  (2026-08-07 → 2026-08-13; plus 3 `aborted` and 2 `queued` rows that never started). Estimate honest
  and slightly conservative. Writer shape: light, `has_substeps=false`, four phases, status-preserving
  delete-then-reinsert scoped strictly to
  `study_arm='elected_pending' AND performed IS NULL AND outcome_event_id IS NULL`.

- **STATE VERDICT — DELIBERATELY DORMANT, and the DB already says so, but for the wrong reason.** Live
  `asset_throughput`: `mi_sankalpa, chart='482012f1…', state='dormant', rows_written=0,
  last_error=NULL`. That word is *semantically* right but is **not** an honest-dormancy signal — it is
  the orchestrator's "ran and produced nothing → data absent → **retry next build**" verdict, produced
  because `target_floor IS NULL` fails `asset_runner.py:1026-1032`'s
  `zero_rows_is_complete = (chart_id is None) or (target_floor == 0)`. Root cause is exact and dated:
  migration `364_mi_all_target_floor_zero.sql` swept `WHERE asset_id LIKE 'mi_%' AND target_floor IS
  NULL` — and its own header names the very hazard ("Without target_floor = 0, the orchestrator keeps
  state='dormant' for any per-chart writer that writes 0 rows, which causes DEP-ASSERT cascade
  failures") — but `mi_sankalpa` was created *afterwards*, by migration 532, with `target_floor NULL`,
  and was never swept. `mi_bhara` is the only other L5 asset in the same condition.

- **Is `mi_sankalpa` the deferred "remedy-efficacy ledger" of plan §7.3?** **No — determination, with
  the discriminator stated.** §7.3 parks a P7-loop bundle: "LEL data-ization, journal/outcome intake,
  retrodiction pass, **remedy-efficacy ledger**, insight embeddings." The discriminator is *what
  computes efficacy*. `mi_sankalpa` records **classical attestation tier** (`efficacy_tier`, inherited
  verbatim from the served row at filing time, never derived from outcomes) plus the raw arm
  assignments and outcome links. It computes **no efficacy rate, no confidence, no calibration
  value.** The thing §7.3 parks is the *analysis over* that substrate — precisely
  `buildEfficacyReport`'s absent `state:'computed'` branch, whose own comment says a rate before real
  calibration data "would be a LAW ZERO violation." **Therefore: `mi_sankalpa` (substrate) =
  deliberately dormant, correct, in scope for verification; the remedy-efficacy computation over it =
  the parked P7 item, correctly deferred.** Residual ambiguity is low but real — the two share a name
  in casual use — so the capsule should carry this discrimination in one sentence.

- **Findings:**
  - `L5-F-D15` **[MUST]** Set `target_floor = 0` for `mi_sankalpa` (and assess `mi_bhara`
    identically). `target_floor IS NULL` is what forces `state='dormant'`, which under
    `plan.ts:527/590` (`!t || t.state === 'dormant'`) makes it a **build candidate on every single
    pass** — a writer that correctly produces 0 rows re-queued indefinitely, exactly the DEP-ASSERT
    cascade migration 364 was written to prevent. — *basis:* §N.4 (floors = achieved count; the
    achieved count is 0 and 0 is correct) + §N.8 (the `dormant` signal currently claims "data absent,
    retry" when the truth is "designed empty, awaiting a native adoption").
  - `L5-F-D16` **[MUST]** Correct the stale in-repo claim at
    `intervention_ledger_filing_gate.test.ts:25-31` — the path landed and `client.ts:288-290` says so.
    A W1/W5 reader relying on that comment mis-classifies a plugged asset as unplugged. — *basis:*
    §N.7 item 1 + C12 (check provenance before ruling).
  - `L5-F-D17` **[NOW]** Declare the real dependency picture: add `lel_events` (which `db.py:64` reads
    on every run) and record a written disposition for `ka_kshetra` — keep it as a declared
    semantic/ordering edge with its cost acknowledged, or drop it, but do not leave it undocumented as
    a data edge it is not. Concrete cost: `ka_kshetra` is `state='stale'` on the canonical chart, so
    the declared edge can block a 1-second writer that reads none of its 8.6M rows. — *basis:* plan §4
    rubric item 2.
  - `L5-F-D18` **[NOW]** `buildEfficacyReport()`'s five count fields should be **`null`, not `0`**,
    while no read path exists. The `reason` string is honest; the numbers beside it are not — they are
    constants that will keep reading zero after the first real adoption. §N.7 item 6 exactly. **This
    is not calibration work — it removes a number, it does not add one.** — *basis:* §N.8 + §N.7 item 6.
  - `L5-F-D19` **[NOW]** Author `integrity_check_sql` from the invariants the schema and design
    already assert, so the check is a real detector and not a volume pin. Candidates, all falsifiable
    on real corruption and all vacuously true at 0 rows (state that caveat): every `outcome_event_id
    IS NOT NULL` row has `outcome_linked_at IS NOT NULL` and vice versa;
    `study_arm='acted_with_election'` ⟹ `performed IS TRUE AND performed_at <@ elected_window`;
    `study_arm='elected_not_acted'` ⟹ `performed IS FALSE`; `study_arm='elected_pending'` ⟹
    `performed IS NULL`; `NOT isempty(elected_window)` (the writer already carries a scar from
    `start==end` producing an EMPTY tstzrange — `writers/mi_sankalpa.py:207-210`);
    `performed IS NOT NULL ⟹ performed_attested_by IS NOT NULL`. — *basis:* C12.
    **These were NOT executed against production; they are proposals, and per C12 a check that has
    never been green is a proposal.**
  - `L5-F-D20` **[NOW]** Write the `efficacy_tier → grounding_tier` mapping down once
    (classically_attested→`sruti`, traditional→`yukti`, speculative_extension→`pratyaksa`; `study_arm`
    always `pratyaksa`). The data already carries the distinction; nothing states it where a doctrine
    reader looks. — *basis:* D-GROUNDING (plan §2).
  - `L5-F-D21` **[NOW]** Populate `expected_volume_formula` as event-driven/exogenous with floor 0
    (same shape as D03), and state in the capsule that `mi_sankalpa` is the P7 **substrate**, distinct
    from §7.3's parked "remedy-efficacy ledger" (the computation). — *basis:* C12 + plan §7.3.
  - `L5-F-D22` **[NEVER/LATER]** An MCP-exposed **read** path for the ledger, and the
    `state:'computed'` efficacy branch behind it. Squarely §7.3's parked remedy-efficacy item; §N.8
    absolute — no rate before real data. — *basis:* plan §7.3; L5 mandate item 5.
- **Proposed route:** `rebuild_only` — 5 clean completed runs at ~1s, idempotent by construction, and
  one accepted execution after D15's floor fix produces a *correctly* terminal `'lit'` at 0 rows
  instead of a perpetually-retried `'dormant'`. **W4 sequencing note:** the D15 registry fix should
  land **before** the build, or the build re-asserts the wrong state; and if the `ka_kshetra` edge is
  retained (D17), dispatch via `scope='asset'` to avoid gating a 1-second writer on a stale L3 monster.

---

## Batch notes

1. **Three empty tables, three genuinely different states — the distinction holds up under evidence.**
   `mi_vistara` = deliberately dormant (designed append-only log, no trigger has fired, writer
   *specified* to originate zero rows, already terminates honestly as `lit`/`chart_id NULL`).
   `mi_sankalpa` = deliberately dormant with a live, tested, guarded write path awaiting a real native
   adoption — but mislabelled by the orchestrator as retry-me `dormant` purely because a 2026-06 floor
   sweep predates its 2026-08 migration. `mi_seva` = built-but-unplugged, and the strong version: the
   table's emptiness is correct, but the service that would fill it *does not exist in any language
   anywhere in the repo*, while the overlay it was designed to gate is already being read around it.
   **None of the three is broken.** Two carry recorded dispositions; one (`mi_seva`) carries a partial
   disposition covering only the destructive-clear edge, not the missing service.

2. **`WriterResult.notes` is a write-only field across the entire codebase.** Writers populate it
   (`mi_seva`, `mi_sankalpa`'s `NOTE_LEDGER_TABLE_ABSENT`/`NOTE_NO_LEL`, `ka_gochara`,
   `mi_sambandha`, `ka_bhavishya_lekha`, …) and **nothing under `pipeline/orchestrator/` outside
   `writers/` ever reads it.** Every writer that reports honest degradation via `notes` instead of
   raising is reporting it into a void, and the build still shows green. **This is a cross-layer §N.8
   finding, not an L5 one**; it is the mechanism behind F-D09 and it will have siblings in every other
   batch. Escalate to the Conductor as a campaign-wide item.

3. **Every L5 asset is `catalog_status='DRAFT'` with `integrity_check_sql IS NULL` (15/15, confirmed
   live), and there is not a single provenance receipt for any `mi_*` asset**
   (`SELECT … FROM asset_provenance_receipts WHERE asset_id LIKE 'mi_%'` → 0 rows). L5 is therefore a
   clean, low-risk proving ground for O-wave WP-1's universal-receipt backfill — and `mi_vistara`, as
   a zero-dependency global asset costing 0.287s, is **the cheapest possible first receipt in the
   whole campaign.**

4. **The `domain='shared'` exclusion is live code, not a plan proposal.** WP-3's domain-aware scoping
   has landed in `platform/src/lib/build/plan.ts`. Any W4 dispatch script reaching for
   `scope='layer'`/`scope_target='mimamsa'` will silently give `mi_vistara` (and `mi_kula`)
   `out_of_domain` and build 13 of 15. This will bite the L0 batches harder — 44 registry rows are
   `scope='global'` per migration 590's own derivation table.

5. **A sealed gate has regressed and nothing detected it.** L5 seal gate G11 ("service assets
   count_sql=null — PASS", commit `42738be0`) is contradicted by the live `mi_seva` row. The seal
   recorded a PASS; no detector re-checks it; the seed file still holds the sealed value. This is the
   §N.8 pattern applied to a *governance* artifact rather than a data one, and it suggests **the L5
   capsule should re-verify its predecessor seal's gates rather than inherit them.**

6. **Correction to a standing brief fact (minor, worth propagating):** `ka_kshetra` at 8.6M rows is
   the **per-chart** figure for the canonical chart (8,599,775) and is correct as stated; the
   chart-agnostic total is 11,012,657. Separately, `ka_kshetra` is currently `state='stale'` on the
   canonical chart under the orphan-watchdog (301 substeps committed, plan-completeness unprovable) —
   relevant to any L5 wave that honours the `mi_sankalpa` edge.
