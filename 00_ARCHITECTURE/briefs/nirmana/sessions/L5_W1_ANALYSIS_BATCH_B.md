---
artifact: L5_W1_ANALYSIS_BATCH_B.md
canonical_id: NIRMANA_L5_W1_ANALYSIS_BATCH_B
version: "1.0"
status: CURRENT — W1 ANALYZE output, L5 (Mīmāṃsā)
session: L5
produced_on: 2026-09-05
scope: mi_abhilekha · mi_pariksha · mi_sambandha · mi_darshana (journal / evaluation / insight seams)
method: >
  Read-only fresh-context analysis subagent against the plan §4 W1 rubric, the five doctrines,
  charter C12, and CLAUDE.md §N.4/§N.6/§N.7/§N.8. No repo write, no DB write. Findings carry
  file:line or live-SQL evidence; unresolved items are recorded as UNKNOWN with what would settle
  them, never as an assumed green.
---

# L5-W1 — Batch B: journal / evaluation / insight seams

### `mi_abhilekha` — L5 journal re-sync **service**; declared owner of `mimamsa_journal` (0 rows)

- **Purpose / doctrines:** P7 (PARKED) outcome-intake seam + D-SERVICE/P8. Stated job: read answered
  native journal entries and propagate them into `mimamsa_predictions.lifecycle_status`. Right
  instrument in shape — but the answer it re-derives from free text is already computed correctly
  one table over.
- **Dependencies (declared → real):** declared `["mi_bhavisya"]`. Real and correct — reads
  `mimamsa_journal` (its own target) and UPDATEs `mimamsa_predictions` (mi_bhavisya's table).
  **Hidden WRITE edge:** it mutates another asset's table (`mimamsa_predictions.lifecycle_status`),
  which the registry records nowhere; `mi_bhavisya` is the sole populator and this the sole mutator
  (corroborated by `00_ARCHITECTURE/pg2_diagnostic/deliverables/pg2_findings_X-5.jsonl` PG2-X5-0002).
- **Leverage:** **YES — the highest-value finding in this batch.**
  `platform/src/app/api/clients/[id]/learning/route.ts:63-79` already computes a clean adjudication
  verdict (`happened→CONFIRMED`, `partial→PARTIAL`, `didnt→REFUTED`, `cant_say→UNRESOLVED`) and
  persists it to `mimamsa_adjudication_log`. `mi_abhilekha` ignores that table entirely and instead
  re-derives a verdict from free text with
  `"confirmed" if "yes" in answer or "confirmed" in answer else "denied"` (`mi_abhilekha.py:66-67`)
  — a substring match that maps *every* non-matching answer to `denied` and matches "yes" inside
  "yesterday". The computed answer exists; the consumer reads a different, empty table and guesses.
- **Grounding:** `pratyaksa` throughout — no classical claim, pure instrument bookkeeping. Correctly
  so; no `sruti`/`yukti` label is owed.
- **Service:**
  - **Consumers:** read path live and healthy — `query_journal.ts` (registered in
    `L5_mimamsa/index.ts`), chart-scoped, `LIMIT 50` with a disclosed `total_matching` /
    `more_available`, and a real `empty_reason`. One of only 6/16 L5 capabilities carrying
    `empty_reason`.
  - **Drill depth:** journal row → `prediction_id` → `mimamsa_predictions` → `driving_signals` → L1
    = 3 hops; exceeds the ≤2-hop D-SERVICE target.
  - **Unplugged? Partially — and this is the mandate-item-3 verdict.** Not "broken", not purely
    "parked":
    - Table + schema + indices: **INTACT** (`platform/migrations/354_mimamsa_seva_abhilekha.sql:17-34`).
    - Read/serve path: **INTACT AND LIVE.**
    - Build-time drain (journal → predictions): **INTACT** (0.07–1.7s measured).
    - **APPEND path: DOES NOT EXIST.** Full-repo grep finds **zero** `INSERT INTO mimamsa_journal`.
      `mi_seva.py:6` claims "Writes a journal entry to mimamsa_journal when a prediction is
      surfaced" and `mi_seva.py:29` points at `services/mi_seva/handler.py` — **that file does not
      exist**. The journal is empty because **nothing can ever write to it**, not because a live
      producer is idle.
    - The serve-time resync trigger is dead: `learning/route.ts:92` POSTs to
      `${sidecar}/mimamsa/abhilekha-resync`; the sidecar registers no such route
      (`main.py:56-111` mounts `/api/brahma`, `/brahma/mimamsa`, `/api/compute` only). The
      `catch {}` swallows the 404 on every adjudication. Noted as an aside in
      `00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/PARKED_FINDINGS_CLOSE_v1_0.md:90`;
      never actioned.
  - **C12 probe — what probing this service concretely means:** `service_health`, `last_selftest_at`,
    `health_probe`, `selftest_detail` are all NULL, yet `asset_throughput.state = 'lit'`
    (Abhinandan) / `'stale'` (canonical). Root cause: `asset_runner.py:1401-1412` routes any service
    *that has a registered WriterBase writer* through `_run_data_writer`, which sets `state='lit'`
    but never touches `service_health`/`last_selftest_at` — only the legacy
    `_run_service_health_probe` path (`asset_runner.py:604-610`) writes those. The in-repo working
    pattern is `ka_graha_sancara.py:73-79,179-193`: the service writer runs its own selftest and
    writes the three columns on `ctx.db_conn`. Every other registry service
    (`bg_ephemeris_engine`, `bg_panchanga`, `ka_dasha_kala`, `ka_muhurta_seva`, `ka_tulana`,
    `ka_graha_sancara`) carries real probe evidence; **`mi_abhilekha` and `mi_seva` are the only two
    NULL across all four columns.** The cockpit's `deriveState.ts:74-82` already fails honest
    (renders `dormant`, not `service_ok`), so the *display* is not lying — but the dependency-assert
    path treats `state='lit'` as satisfied, which is a promotion with no detector behind it.
- **Cost:** estimated 1s (registry) · **measured** from `build_run_assets`: 0.06s–1.69s across 20+
  completed runs; last complete 2026-08-13T01:16:30Z. Light `run(ctx)`, two SELECTs + N UPDATEs, no
  substeps. Estimate honest.
- **Findings:**
  - `L5-F-01` **[MUST]** The journal seam has **no writer anywhere in the repo** — the only two code
    paths that claim to write it are a docstring (`mi_seva.py:6`) and a pointer to a nonexistent
    file (`mi_seva.py:29`). The seal's claim that `mimamsa_journal` is "seeded at serve time"
    (`L5_SEAL_AND_SHIP_REPORT_v1_0.md:162`) is **not true today**. Must be recorded as a *documented
    deferred seam* (P7 register, plan §7.3), not left as an implied-live claim. — *basis:* §N.8 /
    hard floor §3.6 — *evidence:* repo-wide `grep -rn "INSERT INTO mimamsa_journal"` → nothing;
    `ls platform/python-sidecar/services/` has no `mi_seva`.
  - `L5-F-02` **[MUST]** `mi_seva.py`'s docstring asserts two behaviours the code does not have.
    Correct it to state what runs (a table-existence check). — *basis:* §N.7 item 1 — *evidence:*
    `pipeline/orchestrator/writers/mi_seva.py:6,29` vs `run()` at :34-72.
  - `L5-F-03` **[NOW]** Give `mi_abhilekha` (and `mi_seva`) a real selftest writing
    `service_health`/`last_selftest_at`/`selftest_detail`, copying `ka_graha_sancara.py:179-193`.
    Zero orchestrator change, no freeze exception. This is what C12's "lit = current GREEN probe"
    requires. — *basis:* C12 + §N.8 — *evidence:* registry query (only 2 of 8 services NULL);
    `asset_runner.py:1401-1412`.
  - `L5-F-04` **[NOW]** Replace the free-text verdict heuristic with a read of
    `mimamsa_adjudication_log.verdict_mapped`, or record the disposition explicitly and stop
    guessing. — *basis:* §N.7 item 6 — *evidence:* `mi_abhilekha.py:66-67`; `learning/route.ts:63-68`.
  - `L5-F-05` **[NOW]** `learning/route.ts:92`'s best-effort POST targets a nonexistent sidecar
    endpoint and fails silently on every adjudication. Remove it or point it at a real route.
    — *basis:* D-SERVICE (built-but-unplugged) — *evidence:* `learning/route.ts:88-101` vs
    `main.py:56-111`.
  - `L5-F-06` **[NEVER/LATER]** Building the journal *producer* (prompt-surfacing → journal append →
    outcome intake) is P7 loop machinery. Defer, plan §7.3 "journal/outcome intake". — *basis:* L5
    mandate.
- **Proposed route:** `probe` — produces no rows by design; needs a real GREEN health probe (F-03)
  plus honest-labelling fixes, not a rebuild.

---

### `mi_pariksha` — attribution engine + QA harness + retrodiction suite (7 substeps → `mimamsa_qa_eval` 174 / `mimamsa_attribution` 1,425 / `mimamsa_discoveries` 71)

- **Purpose / doctrines:** P7 falsifiability substrate (PARKED) + D-SERVICE. Evaluates negative
  controls, control windows, per-family ablation, salience-tail skill, degenerate score
  distribution; plus analytic credit attribution and discovery mining. Right instrument; its honesty
  labelling is the best in the layer.
- **Dependencies (declared → real):** declared `["mi_pramana","mi_kula","bg_formula_constants"]`.
  - Real, confirmed: `mimamsa_calibration` · `mimamsa_signal_families` · `brahma_formula_constants`
    (`_load_dim_weights`, :66-79).
  - **Undeclared real reads (4 hidden edges):** `mimamsa_event_provenance` at :152-160, :283-291 —
    *load-bearing*: no events → zero retrodiction and zero control_window rows;
    `mimamsa_predictions` at :460; `phala_anchors` (L4) at :183-196, :477-486; `bodha_msr_signals`
    (L2) at :768-777. All `_table_exists`-guarded, so they degrade silently rather than fail.
  - **False edge:** none.
- **Leverage:** **YES, two.**
  1. `query_calibration.ts:150-151` computes `qa_fail_count` as `.filter(r => r.status === 'FAIL')`
     — **exact equality**. The writer emits `'FAIL_event_too_close'` (`mi_pariksha.py:317`), of which
     the canonical chart holds **61 live rows**. So `mimamsa_calibration_get` reports
     `qa_summary.fail_count: 0` while 61 FAIL-prefixed rows sit in the array it just returned.
  2. `mimamsa_qa_eval` is read only by `query_calibration.ts`; three retrieval-spine test files still
     mock a `FROM mimamsa_qa_eval` branch no production spine file contains — a stale test-only edge.
- **Grounding:** **`pratyaksa`**, correctly. Every row is instrument-emergent; nothing makes a
  classical claim. The writer goes further than a tier label: `status='structural_proxy'` for
  ablation/tail_only (:415-421, :752-757) and `status='not_implemented'` for negative controls
  (:582-595, JL-019) are exemplary §N.8 conduct — a check with no detector is labelled as such
  rather than passed.
- **Service:** consumer = `query_calibration` → MCP `mimamsa_calibration_get`
  (`tool_name_bridge.ts:158`); `mimamsa_attribution` → `query_attribution.ts`;
  `mimamsa_discoveries` → `query_mimamsa_discoveries.ts` + build-time `mi_darshana`. All registered.
  Density: `query_calibration` declares **no `density_contract`, no `empty_reason`**, and returns
  `qa_results` **unbounded and unpaginated** (all 174 rows); the 40KB presentation budget trims it
  downstream, but the capability makes no density declaration. Drill: qa row → `target` → source
  table = 2 hops. Not unplugged.
- **Cost:** estimated 2s · **measured** over 42 completed runs: min 0.13s / **avg 4.24s** /
  **max 32.91s**. The estimate is ~2× low on the mean and 16× low on the tail — the only materially
  wrong estimate in this batch. Heavy: 7 substeps, batched `executemany` (1,000-row batches).
- **Findings:**
  - `L5-F-07` **[MUST]** `qa_summary.fail_count` under-reports failures: exact `=== 'FAIL'` misses
    the writer's own `'FAIL_event_too_close'`. Fix to a prefix/allowlist match and disclose the
    status vocabulary. — *basis:* §N.8 + §N.6 item 1 — *evidence:* `query_calibration.ts:150-151`;
    DB: 61 rows `status='FAIL_event_too_close'` on `482012f1`.
  - `L5-F-08` **[MUST]** The `degenerate_distribution` check emits `status='pass'` on a chart with
    **zero calibration rows**. `mi_pariksha.py:597` guards on `if baseline > 0.0`, but `baseline`
    falls back to the literal `0.5` when the AVG returns NULL (:576-580) — so an empty chart passes
    with `mean_score: 0.5, is_degenerate: false` and no `n` recorded. Verified live: chart
    `1c826d5a` has 0 calibration rows and carries `degen_dist_1c826d5a` → `pass`. Emit
    `not_implemented`/`insufficient_data` with `n` when `cal_rows` is empty. — *basis:* §N.8 ("what
    code path would have to run and fail for this to read false?" Answer: none) + §N.7 item 6 —
    *evidence:* `mi_pariksha.py:576-580,597-605`; DB row `degen_dist_1c826d5a`.
  - `L5-F-09` **[NOW]** `_substep_neg_control`'s DELETE is
    `WHERE check_type NOT IN ('control_window','ablation')` (:566-571) — it also wipes `tail_only`
    rows. It survives only because `tail_only` runs *after* it in `plan_substeps`. Any substep-level
    resume/re-dispatch of `neg_control` alone silently destroys the `tail_only` row and drops
    `count_sql`. Scope the DELETE to its own `check_type`s. — *basis:* §N.3 — *evidence:*
    `mi_pariksha.py:566-571` vs `plan_substeps` at :99-107.
  - `L5-F-10` **[NOW]** Declare the 4 hidden edges — or record an explicit disposition for why they
    stay undeclared. `mimamsa_event_provenance` is load-bearing: chart `1c826d5a` has 0 provenance
    rows and consequently 0 retrodiction + 0 control_window rows, which reads as "the harness passed
    with 6 checks" rather than "the harness had almost nothing to check." — *basis:* rubric item 2 +
    §N.6 item 3 — *evidence:* `mi_pariksha.py:152-160,283-291,183-196,460,768-777`; qa_eval 168 vs 6.
  - `L5-F-11` **[NOW]** Correct `estimated_seconds` 2 → measured (avg 4.24s, max 33s), and populate
    `expected_volume_formula`/`expected_volume_inputs` — currently NULL, which C12 names as the
    defect condition for any future volume check. Do **not** author a `count(*) = 174` pin (C12
    forbids equality-as-floor). — *basis:* C12 + §N.4 — *evidence:* registry row;
    `build_run_assets` over 42 runs.
  - `L5-F-12` **[NEVER/LATER]** Making ablation and tail_only *real* (a serve-time R-pipeline rerun
    with a family masked) and building the synthetic-injection harness behind the negative controls
    are P7 loop machinery. Both are already labelled honestly in place; leave them labelled. Defer,
    plan §7.3. — *basis:* L5 mandate item 5 — *evidence:* `mi_pariksha.py:415-421,582-595,752-757`.
- **Proposed route:** `rebuild_only` — no writer change is required for row correctness; the MUSTs
  are one serving-plane fix (F-07) and one small writer guard (F-08). Canonical-chart data is
  `state='error'` (BLOCKED 2026-08-21) and must be re-run either way.

---

### `mi_sambandha` — manifestation-channel propensity grammar (`mimamsa_manifestation_grammar`, 47 rows: 24 canonical / 23 Abhinandan)

- **Purpose / doctrines:** P7 learning substrate (PARKED) + D-GROUNDING. Learns per-native channel
  firing propensity from `manifestation_sets × calibration`, seeded from priors where empirical data
  is absent.
- **Dependencies (declared → real):** declared `["mi_pramana","mi_pariksha","mi_bhavisya"]`.
  - Real: `mimamsa_manifestation_sets` (`mi_bhavisya.py:249` is the sole INSERT) and
    `mimamsa_calibration`.
  - **FALSE EDGE: `mi_pariksha`.** The writer reads nothing mi_pariksha produces — not
    `mimamsa_attribution`, not `mimamsa_qa_eval`, not `mimamsa_discoveries`. Confirmed against every
    cursor in `mi_sambandha.py:107-125`. Not free: `asset_throughput` shows the canonical chart's
    last run BLOCKED on `mi_bhavisya, mi_pariksha, mi_pramana` — a spurious dependency gating a real
    build.
  - **Undeclared:** `mi_kula` is *claimed* in the citation but never read.
- **Leverage:** none of the "consumer reads NULL" kind — `query_manifestation_grammar.ts` reads every
  column the writer writes. The *inverse* problem is severe: the consumer serves rows the writer's
  current code would no longer produce (F-14).
- **Grounding:** should be **`pratyaksa`**, and the honest-null discipline in current code
  (`_PROPENSITY_UNMEASURED`, `citation_ref.propensity_null_reason`, :62-88,144-157) is exactly right.
  **But the stored `citation_ref` says `{"method": "prior_from_kula"}` (:214) — a false provenance
  claim on two counts:** (a) nothing from `mi_kula` is read; (b) `mimamsa_signal_families` contains
  *technique* families (`fam_anchor`, `fam_yoga`, `fam_msr_signal`, …), not manifestation
  *channels* — it has no channel priors to give. The priors are a module-local hardcoded dict
  (`_PRIOR_PROPENSITIES`, :90-99).
- **Service:** consumer = `query_manifestation_grammar.ts` (registered; `top_k`-bounded). **No
  `density_contract`, no `empty_reason`, no `total_matching`** — a caller cannot distinguish
  "top_k truncated" from "that's all there is". It serves `evidence_grade` and `channel_propensity`
  **raw, with no serve-time suppression** — unlike its sibling `query_insights.ts`, which has
  `suppressIfNotCalibrated`. Drill: grammar row → `channel_id`/`domain` →
  `mimamsa_manifestation_sets` → `prediction_id` → L1 = 3+ hops. Not unplugged.
- **Cost:** estimated 1s · **measured** over 42 completed runs: min 0.07s / avg 0.67s / max 4.70s.
  Estimate honest. Light `run(ctx)`, two queries + `executemany`.
- **Findings:**
  - `L5-F-13` **[MUST]** **The prior table's channel vocabulary has zero intersection with the
    channel vocabulary that actually exists.** `_PRIOR_PROPENSITIES` (:90-99) declares 20 channels
    (`ch_career_material`, `ch_rel_partnership`, `ch_fin_income`, …). `mi_bhavisya` emits exactly 7,
    all `ch_<domain>_verbal` (DB: `ch_career_verbal` 38, `ch_transition_verbal` 71,
    `ch_relationship_verbal` 22, `ch_wealth_verbal` 26, `ch_spirituality_verbal` 20,
    `ch_character_verbal` 9, `ch_health_verbal` 9). Consequences, all visible live: every real row's
    `prior` falls through to the bare `0.5` default (:139); the seed loop emits **17 orphan
    `prior_only` rows** for channels that can never appear (verified: all 17 rows with
    `opportunity_count=0` carry ids absent from `manifestation_sets`); and `propensity_delta` —
    "learned minus prior" — is measured against a prior unrelated to the channel. Additionally
    mi_bhavisya assigns **exactly one channel per domain**, so "channel propensity" is structurally
    degenerate: with a single channel, `fire/opp` can only be 0 or 1 and no channel discrimination is
    possible. — *basis:* §N.7 item 3 + §N.8 — *evidence:* `mi_sambandha.py:90-99,139,186-215`;
    `mi_bhavisya.py:249`; DB `mimamsa_manifestation_sets` GROUP BY domain, channel_id.
  - `L5-F-14` **[MUST]** **The entire served table is stale and carries the exact defect the merged
    fix removed.** All 47 live rows are `grammar_formula_version = 'mi_sambandha_v1.0'`; HEAD is
    `v1.2` (F-147, PR #1439, commit `44f42fe94`, 2026-08-21 — *after* the last successful L5 build on
    2026-08-12/13; the 2026-08-21 rebuild was BLOCKED). **10 live rows carry
    `evidence_grade='empirical'` with `scored_count = 0` and a non-NULL `channel_propensity` of
    0.0** — precisely the "measured, and it never fires" invention the F-147 addendum was written to
    replace with an honest NULL. Nothing in the serving path suppresses them. — *basis:* §N.8 +
    §N.7 item 6 — *evidence:* `git log` on `mi_sambandha.py`; DB GROUP BY
    `evidence_grade, grammar_formula_version` → `empirical / v1.0 / scored_count=0` × 10.
  - `L5-F-15` **[NOW]** `citation_ref` claims `prior_from_kula` on all 17 seeded rows. Rename to what
    it is (`prior_hardcoded_module_constant`) or read a real prior source. A false provenance tag is
    worse than a bare one because it survives audit. — *basis:* §N.7 item 1 — *evidence:*
    `mi_sambandha.py:214`; `mimamsa_signal_families` contents.
  - `L5-F-16` **[NOW]** Remove the `mi_pariksha` false edge from `depends_on`; a real build-gating
    hazard, not cosmetic. — *basis:* rubric item 2 + WP-3 — *evidence:* `mi_sambandha.py:107-125`;
    `asset_throughput.last_error` for `482012f1`.
  - `L5-F-17` **[NOW]** Dead code: `covered_domains` (:187) is computed with an acknowledged-wrong
    index and never used. Delete. — *basis:* hygiene.
  - `L5-F-18` **[NOW]** Add `empty_reason` + a disclosed `total_matching` to
    `query_manifestation_grammar.ts`, matching `query_journal.ts`. — *basis:* D-SERVICE —
    *evidence:* `query_manifestation_grammar.ts:104-120` vs `query_journal.ts:76-95`.
  - `L5-F-19` **[NEVER/LATER]** Deriving genuine channel priors and expanding mi_bhavisya's channel
    vocabulary beyond one-per-domain are P7/multi-chart work. Defer, plan §7.3. — *basis:* L5
    mandate item 5.
- **Proposed route:** `changed` — F-13/F-15/F-16/F-17 are writer edits and F-14 requires the rebuild
  that follows them. The one asset in the batch where `verified_reuse` would be actively wrong: the
  stored rows carry an unearned `empirical` grade the current code cannot produce.

---

### `mi_darshana` — insight retrieval surface (`mimamsa_insight_units` 150: 115 canonical / 35 Abhinandan; `mimamsa_insight_embeddings` **0**)

- **Purpose / doctrines:** D-SERVICE/P8 (the L5 read face), D-GROUNDING (evidence-grade tiering),
  D-SYNTHESIS (one verdict voice per event class). Deepest node in the L5 DAG. Right instrument.
- **Dependencies (declared → real):** declared 8 — `mi_pramana, mi_adhilepa, mi_sambandha,
  mi_pariksha, mi_gunanaka, mi_kula, mi_jivanaghatana, bo_pratijna`.
  - **Real reads (6+ tables):** `mimamsa_reliability` (mi_gunanaka) :204-209 ·
    `mimamsa_manifestation_grammar` :255-262 · `mimamsa_discoveries` :345-352 ·
    `mimamsa_load_bearing` :388-393 · `bodha_pratijna` + `brahma_event_ontology` :425-436 · plus
    `bodha_msr_signals`, `bodha_contradictions`, `bodha_triangulation`.
  - **FALSE EDGES (3):** `mi_pramana` (`mimamsa_calibration` never read directly — arrives via
    mi_gunanaka's reliability strata), `mi_kula` (`mimamsa_signal_families` never read),
    `mi_jivanaghatana` (`mimamsa_event_provenance` never read — reaches here via mi_pariksha's
    discoveries).
  - **UNDECLARED real edges (3):** `bodha_msr_signals`, `bodha_contradictions`,
    `bodha_triangulation` — L2 tables read directly at :443-476, materially shaping
    `ranked_evidence`, `contradictions`, and the verdict note.
- **Leverage:** **YES — the embedding path (mandate item 4), plus a stale-data leverage loss.**
  1. `count_sql` sums `insight_units + insight_embeddings`, and `assetClearSpec.ts:145-146` clears
     both — the asset *owns* the embeddings table, but `_substep_embeddings` (:715-741) is a pure
     logging no-op emitting `[EXTERNAL_COMPUTATION_REQUIRED]` and returning `rows_inserted=0`.
     **This is correct B.10 conduct, not a defect** — no fabricated vectors. But nothing anywhere in
     the repo calls an embedding service against `mimamsa_insight_units`.
  2. `query_insights.ts` reads all 150 rows — none NULL. But every row is
     `surface_formula_version='mi_darshana_v1.0'` while HEAD is `v1.2`, so the *served narration* is
     pre-fix (F-21).
- **Grounding:** **`pratyaksa`** for `calibrated_outlook`, `emergent_law`, `load_bearing`,
  `retrodiction` — correctly so. `verdict_object` is the one class with a genuine `sruti`/`yukti`
  claim: its `provenance_chain.ranked_evidence` carries `classical_sources` (from
  `bodha_msr_signals.classical_sources_array`) and `tradition_concordance` across
  parashari/jaimini/kp/tajika. Those rows *should* carry a grounding tier; today all 54 are flattened
  to `evidence_grade='structural'`, which describes the *derivation method* and says nothing about
  classical grounding. Two axes served on one field.
- **§N.7 ŚUDDHA-VĀCA fix check (mandate): the fixes are PRESENT IN CODE at HEAD, and the code no
  longer re-derives — but the SERVED DATA predates them.**
  - Present and verified in source: the SV-5 `question_class`-keyed dead-lookup removal + dual-axis
    verdict note (:606-643); the P0-10 `pr.get("grade") or 5.0` truthiness fix, now
    `float(_raw_grade) if _raw_grade is not None else 5.0` (:539-541,553); the `no_evidence` early
    branch refusing to fabricate a "grade 5.0/10. Conditional." from a NULL grade (:518-552); the
    F-143 per-class `_discovery_evidence_grade` (:83-157); the F-147 unmeasured-propensity narration
    (:277-303); the F-148 echo-don't-restate disclosure (:98-114); the P3-b duplicate-key leak
    removal (:330-336). All trace to cited facts they *read*.
  - **Not in the data.** 51 `retrodiction` insight units carry `evidence_grade='prior_only'`, but
    `_discovery_evidence_grade` at HEAD returns `_GRADE_STRUCTURAL` for that class unconditionally —
    proof the rows predate F-143. And all 10 `manifestation_grammar` units read, verbatim:
    *"For career events, the 'ch_career_verbal' channel fires with 0% propensity (n=37, empirical
    learning)."* That is the exact sentence F-147's addendum exists to prevent, live and served
    today. The 54 `verdict_object` rows happen to be correct (all carry real `tradition_concordance`),
    but that is luck of the data, not the fix.
- **Service:**
  - `mimamsa_insight_units` → `query_insights.ts` → MCP **`mimamsa_insight_get`**
    (`register_p1_synthesis.ts:607-649`). LIVE and reachable, with real serve-time discipline:
    `suppressIfNotCalibrated`, `redactEmbeddedNumericEvidence`, a present-grades-only
    `evidence_grade_legend`. But **no `density_contract`, no `empty_reason`**, and it returns
    `total_returned` with **no total-available count**.
  - `mimamsa_insight_embeddings` → `query_insight_embeddings.ts`. **Built-but-unplugged, twice
    over:** registered in `L5_mimamsa/index.ts` but with **no entry in `TOOL_NAME_TO_URI` or
    `MCP_TO_RETRIEVAL_TOOL`**, so unreachable from any MCP tool name; and the table has 0 rows. Its
    own header (:26-33) is honest about the second half.
  - Drill: insight → `provenance_chain.ranked_evidence[].fact_ids` → `chart_facts` = **2 hops.**
    Meets D-SERVICE.
- **Cost:** estimated 1s · **measured** over 39 completed runs: min 0.13s / avg 1.42s / max 6.02s.
  Slightly low on the tail; broadly honest. Heavy: 3 substeps, 500-row batches. `asset_throughput`
  for canonical is `error` (BLOCKED on 5 upstreams, 2026-08-21) with 115 rows from the earlier run.
- **Findings:**
  - `L5-F-20` **[MUST — insight-EMBEDDING serve path note, mandate item 4]** Record precisely, for
    the future programme: **the serve path is built and correct; the producer does not exist.**
    1. **Schema/index — DONE.** `mimamsa_insight_embeddings`, 768-dim `vector`, ivfflat index
       (`platform/migrations/353_mimamsa_darshana.sql`).
    2. **Serve path — DONE and honest.** `query_insight_embeddings.ts` exposes the only two
       non-fabricated uses of a populated embedding table: provenance lookup by `insight_id`
       (`embed_model_version`, `embedded_at` — never the raw vector), and pgvector `<=>` cosine NN
       **from one already-embedded insight to its neighbours**. It deliberately does *not* embed an
       arbitrary query string, because no live text-embedding service exists at query time anywhere
       in this codebase (`query_signals.ts`'s `semantic_query` path falls back for the identical
       reason). That restraint is correct B.10 conduct and must be preserved.
    3. **Producer — MISSING.** `_substep_embeddings` (`mi_darshana.py:715-741`) logs
       `[EXTERNAL_COMPUTATION_REQUIRED]` and writes nothing. A P7 programme must supply: an embedding
       service call over `mimamsa_insight_units.statement WHERE chart_id = …`; an INSERT recording
       `embed_model_version` + `embedded_at` (both already served as provenance); a stated model +
       dimensionality matching the 768-dim column; and re-embedding on `surface_formula_version`
       change, since `_substep_insight_units` DELETEs embeddings on every rebuild (:679-681) —
       embeddings are therefore *always* zero after any build, by construction.
    4. **Reachability — MISSING.** Add `query_insight_embeddings` to `TOOL_NAME_TO_URI` +
       `MCP_TO_RETRIEVAL_TOOL` (a `mimamsa_insight_neighbors_get`-shaped alias), or the populated
       table stays MCP-invisible.
    5. **Cost note:** 150 statements/chart at 2 charts — trivial; the blocker is service provisioning
       and model-version governance, not volume.
    — *basis:* L5 mandate item 4 + D-SERVICE + B.10 — *evidence:* `mi_darshana.py:715-741,679-681`;
    `query_insight_embeddings.ts:15-33`; `tool_name_bridge.ts:516-612` (absent); DB 0 rows.
  - `L5-F-21` **[MUST]** All 150 served insight units are `mi_darshana_v1.0`; HEAD is `v1.2`. F-143
    (`ca9214f2c`), F-147 (`44f42fe94`) and F-148 (`e5ef0bc66`) all landed *after* the last successful
    build (2026-08-12/13), and the 2026-08-21 rebuild was BLOCKED. The layer is serving narration the
    merged fixes already corrected. A `verified_reuse` route against this data would certify text the
    codebase itself has repudiated. — *basis:* §N.7 items 1 & 6; §N.8 — *evidence:* `git log`;
    `surface_formula_version` = `v1.0` on 150/150 rows; live statement text quoted above;
    `asset_throughput.last_error`.
  - `L5-F-22` **[NOW]** Declare the 3 hidden L2 edges and drop the 3 false ones. The false edges
    materially widen the BLOCKED set — the canonical chart's failure named `mi_pramana` among its
    blockers for an asset that never reads it. — *basis:* rubric item 2 + WP-3 — *evidence:*
    `mi_darshana.py:204-209,255-262,345-352,388-393,425-476`; `asset_registry.depends_on`.
  - `L5-F-23` **[NOW]** `_substep_views_verify` (:743-765) is named "verify" but has **no detector**:
    it counts four views, swallows every exception into a `"ERROR: …"` *string stored as a count*,
    and returns success unconditionally. A dropped view produces a cheerful note, not a failure.
    Either make it assert (counts reconcile against `mimamsa_insight_units`) or rename it to
    `views_report`. — *basis:* §N.8 + §N.7 item 4 — *evidence:* `mi_darshana.py:743-765`.
  - `L5-F-24` **[NOW]** `_substep_embeddings` reads `getattr(self, "_insight_count", 0)` (:722), set
    by the *previous* substep on the same instance. Under any substep-resume or fresh-instance
    dispatch it silently reports `0 insight units need embedding` while 150 exist. Query the count
    instead of caching it across substeps. — *basis:* §N.7 item 6 — *evidence:*
    `mi_darshana.py:697,722`.
  - `L5-F-25` **[NOW]** Add `empty_reason` and a total-available count to `query_insights.ts` so
    `top_k` truncation is distinguishable from exhaustion. — *basis:* §N.6 item 4 — *evidence:*
    `query_insights.ts:255-266`.
  - `L5-F-26` **[NEVER/LATER]** Splitting `verdict_object`'s grounding tier (`sruti`/`yukti`) from
    its derivation tier (`structural`) is a D-GROUNDING schema change spanning L2→L5. Genuinely
    valuable, out of L5's parked-seam scope; carry to the D-GROUNDING workstream. — *basis:* L5
    mandate + plan §2 D-GROUNDING.
- **Proposed route:** `rebuild_only` — the writer code is already correct at HEAD; what is wrong is
  that no build has run since the fixes merged. The two serving-plane items (F-25, and F-20's bridge
  entry) are small TS additions that ride W3.

---

## Batch notes

**1. The single dominant, cross-batch fact: the code is fixed, the data is not.** Every table in this
batch carries a formula version *behind* its writer's HEAD version (`mi_sambandha_v1.0` vs code
`v1.2`; `mi_darshana_v1.0` vs code `v1.2`). The last successful L5 build was **2026-08-12/13**; the
three ŚUDDHA-VĀCA/PARIŚEṢA narration-fidelity fixes landed **2026-08-21/22**; the **2026-08-21
rebuild was BLOCKED** on upstream dependencies and never completed. The layer is therefore *serving
today* the exact defective sentences those PRs were merged to remove — verifiable verbatim in
`mimamsa_insight_units.statement`. **This is the L5 capsule's gating fact.** The mandate's
"STRUCTURAL mode is deliberate, not unfinished" re-documentation is correct and should be written —
but it must not be allowed to launder *this*, which is not deliberate structural emptiness but an
un-run rebuild. Concretely: **no L5 asset in this batch may take a `verified_reuse` route.**

**2. Mandate item 3 — journal seam: INTACT-BUT-INERT; adjudication seam: INTACT-WRITE, SEVERED-READ.**
- *Journal:* table/indices ✓, read+serve path ✓ (`query_journal.ts`, one of only 6/16 L5 capabilities
  with a real `empty_reason`), build-time drain ✓. **Append path: does not exist anywhere in the
  repo.** `mi_seva`'s docstring points at a nonexistent `services/mi_seva/handler.py`. Empty because
  *unwritable*, not because parked.
- *Adjudication:* `mimamsa_adjudication_log` exists; `learning/route.ts` writes it correctly with a
  proper closed-vocabulary verdict map, behind a real `requireChartPermission({access:'write'})`
  gate; its GET anti-joins it to hide already-adjudicated windows. **But nothing ever reads
  `verdict_mapped` back into L5** — not `mi_abhilekha` (which reads the empty journal instead and
  re-derives the verdict from free text), not `mi_pramana`. The one bridge meant to close it,
  `POST /mimamsa/abhilekha-resync`, targets a route the sidecar does not register and fails silently
  on every call. 0 rows, so nothing has been lost yet — the seam is intact structurally and severed
  functionally.
- *Provenance retention (mandate item 2):* **VERIFIED HEALTHY.** `mimamsa_event_provenance` = 64 rows
  on the canonical chart with `admissible_clean`/`held_out` intact and actively consumed by
  `mi_pariksha`'s retrodiction and control-window substeps. All 195 `mimamsa_predictions` are
  `lifecycle_status='pending'` — internally consistent with a parked loop and no fabricated
  transitions. The genuinely-live outcome loop runs on a *different* table,
  `brahma_mimamsa_prediction_ledger` (5 rows: 4 `dismissed`, 1 `unverifiable`) via the Samīkṣā
  portal, and both sidecar/MCP `record_outcome` paths are deliberately RETIRED (410 Gone at
  `brahmagyan/mimamsa/outcome.py:607-618`; `mcp_predictions` dropped in migration 471). The L5
  build-time journal loop and the live serving loop are two disjoint subsystems — worth stating
  plainly in the seal, because the seal's current phrasing invites reading them as one.

**3. `mimamsa_outcome_record` is a dead MCP tool.** The alias (`register_p1_aliases.ts:2081-2101`)
POSTs to `/api/mcp/primitives/record_outcome`, but `record_outcome` has **no entry in
`MCP_TO_RETRIEVAL_TOOL`**, so `isAllowedSurgicalTool()` rejects it and the route fails closed with a
400. Also a schema mismatch: the alias forwards `{chart_id, prediction_id, outcome, verdict}` while
the writes route expects `body.entry = {prediction_id, outcome_text, verified}`. Given the deliberate
retirement above, the right disposition is almost certainly **retire the alias**, not wire it — but
it should be a *recorded* disposition, since `muhurta_finder.ts:361,905-907` still tells callers, in
served prose, to "close this election by calling `mimamsa_outcome_record`." That is a live
instruction pointing at a tool that 400s.

**4. Layer-level D-SERVICE gap: zero `density_contract` across all 16 L5 capabilities**, and
`empty_reason` on only 6/16. The three highest-traffic faces — `query_calibration`, `query_insights`,
`query_manifestation_grammar` — have neither. Cheap, bounded, in-scope, and the precondition for any
CI/census harness asserting §N.6 Part 2 coverage on this layer.

**5. Registry hygiene, layer-wide.** All 15 L5 assets: `integrity_check_sql IS NULL`,
`catalog_status='DRAFT'`, `target_floor=0`, `expected_volume_formula IS NULL` (except
`mi_jivanaghatana`). Per C12 the NULL `expected_volume_formula` **is itself the defect condition** for
any future volume assertion; the correct fix is a derived formula or a §N.4 achieved-count floor —
never a `count(*) = 174` pin. Both service writers' docstrings claim "GLOBAL scope" while the registry
says `domain='chart'`, `scope='per_chart'` — a GA.1-class registry-vs-code disagreement.

**6. A third chart exists and is broken.** `cb73cd3d-9eba-4220-9902-0de91566e980` has `mi_pariksha`
and `mi_darshana` in `state='error'` (BLOCKED, 2026-08-07) with `rows_written = NULL` and zero rows in
every L5 table. It is not one of the two charts named in the standing facts. W2 should give it an
explicit disposition rather than let it sit as an unexplained error row that will appear in any
layer-plan disposition total under WP-3.

**7. Honest gaps not closed.**
- `UNKNOWN — whether the canonical chart's 2026-08-21 BLOCKED run was a one-off scheduling artifact
  or a persistent upstream failure.` Settled by: the `build_run_assets` rows for
  `mi_pramana`/`mi_adhilepa`/`mi_gunanaka` in that same `run_id`.
- `UNKNOWN — whether any live traffic actually calls mimamsa_insight_get / mimamsa_calibration_get.`
  `asset_registry.last_invoked_at` is NULL for every L5 asset, but that column is only written by the
  legacy service-probe path, so its NULL is uninformative. Settled by: MCP request logs or
  `retrieval_step` telemetry keyed by tool name.
- F-13's degeneracy claim was **not** verified against `mi_bhavisya`'s channel-assignment code — only
  its INSERT target and the resulting data. The data is unambiguous (one channel per domain across
  195 rows and 2 charts) but the *cause* is inferred from the table, not read from `mi_bhavisya.py`.

**8. Nothing in this batch recommends inventing a calibration value, and nothing recommends weakening
a check.** Every MUST is either a stale-data rebuild, a summary under-reporting real failures (F-07),
a PASS with no possible failure path (F-08), an unearned `empirical` grade at rest (F-14), or an
honest recording of a seam that does not exist (F-01, F-20). The three most impressive things in this
layer — `mi_pariksha`'s `structural_proxy`/`not_implemented` statuses, `mi_sambandha`'s
`_PROPENSITY_UNMEASURED` null, and `query_insight_embeddings.ts`'s refusal to embed a query string it
cannot honestly embed — are all §N.8 conduct that should be **preserved verbatim**, cited as
precedent, and explicitly protected from any future "make it green" pressure.
