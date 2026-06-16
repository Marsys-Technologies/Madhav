---
artifact: CLAUDECODE_BRIEF_BODHA_B1_FULL_PROJECTION_v1_0.md
canonical_id: BODHA_B1_FULL_PROJECTION_BRIEF
version: 2.0
status: READY_TO_EXECUTE
authored_by: Cowork (planning) 2026-06-16
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
v2_changes: >
  CODE-VERIFIED corrections + native rulings from the B1–B5 review session (2026-06-16):
  (1) PROJECTION SOURCE FIX — bo_laksana projects the chart_facts SIGNAL-CATEGORY POPULATION (union of
      all 5 L1 chart_facts writers: ga_structural + ga_strength-as-input + ga_sensitive + ga_sade_sati +
      ga_panchanga), NOT "ga_structural" specifically. ga_structural is a pure emitter with empty
      depends_on and does NOT contain ga_sensitive/ga_sade_sati/ga_panchanga (~19,295 rows). Count-parity
      is defined against the chart_facts signal population, never the ga_structural row count alone.
  (2) FULL L0 BRIDGE (native ruling) — populate every signal's classical_sources_array from
      brahma_yoga_catalog + bg_rules + bg_texts. New §B1.5. Highest-value depth move.
  (3) E1–E8 retrieval-depth enhancements folded in as explicit tasks (§E-PHASES). Real embeddings,
      lossless signal-summary text, convergence/contradiction + deep-digest tools, provenance contract
      tests, weak-tail reachability.
  (4) EVAL HARNESS gates L2 seal (native ruling) — semantic-completeness eval, not just per-table
      coverage. New §B6. L2 does NOT seal until it passes.
execution_mode: CONTINUOUS / AUTONOMOUS — phase-by-phase, no human gate between phases. Stop only on a real dependency miss or a Tier-3 event (destructive op, genuine ambiguity, needed architecture change → raise to native). Native reviews retrospectively via cockpit/Atlas + Smṛti.
data_plane: ALWAYS prod via the Cloud SQL Auth Proxy (platform/scripts/start_db_proxy.sh, 127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - BODHA_BUILDOUT_CONTEXT_HANDOFF_v1_0.md (the self-contained context — read it first)
  - L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md (the projection model — intrinsic L1 vs population-level L2)
  - A10_MSR_SPEC_v1_0.md (§4 salience_formula_v1, §11 MVs) + A11/A12/A13/A14 specs
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase contract) + §5 (conformance checklist)
  - MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md (Trap 1) + MSR_UCN_CONTAMINATION_AUDIT_v1_0.md (Trap 2)
supersedes_for_b1: >
  CLAUDECODE_BRIEF_WAVE3_4_RETRIEVAL_AND_BODHA_v1_0.md §PHASE B1 is REVISED by this brief.
  Wave-4 B2–B5 still stand; this brief restates them (§B2–§B5) so it is a complete arc. The B1
  difference is the NATIVE DECISION below (full-enumeration parity, not the merged 32-category subset).
native_decision_2026_06_16:
  projection_scope: FULL_ENUMERATION_PARITY
  meaning: >
    bo_laksana projects EVERY ga_structural fact row (and the other projected ga_* categories) to one
    MSR signal — NOT the curated 32-category allow-list the merged writer currently hardcodes. MSR
    signal count tracks the ga_structural fact count (handoff acceptance read literally). Salience is
    still computed per signal (salience_formula_v1) but strength is a COLUMN, never a FILTER — the
    weak tail is kept (no-threshold-drop). This is the single most important change in §B1.
---

# Bodha B1 — bo_laksana as FULL Projection + the anti-drift spine, then B2–B5 to L2 seal

> **Read order before you touch code:** (1) `BODHA_BUILDOUT_CONTEXT_HANDOFF_v1_0.md`; (2)
> `L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md`; (3) `A10_MSR_SPEC_v1_0.md`; (4) both trap docs;
> (5) `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 + §5`. Verify live state from `CURRENT_STATE_v1_0.md`
> §2 + `git log`, never a frozen doc. Then execute.

## §0 — Why this brief exists (the one thing the prior brief got wrong)

The Wave-4 brief said: *"signal count tracks ga_structural fact count, not a predicate catalog."* But
the **merged** `bo_laksana.py` reads `chart_facts WHERE fact_category = ANY(<hardcoded 32-item list>)`
— a curated subset, not the full enumeration. Cowork verified (2026-06-16) that all 32 names match L1
output exactly (no silent-zero drift) — **but a curated subset is not full projection.** It would
populate `bodha_msr_signals` with the salient signals and silently leave the long tail of raw
per-varga aspect / argala / dispositor rows un-projected.

**Native ruled (2026-06-16): FULL ENUMERATION PARITY.** Every projected L1 fact → one MSR signal.
That makes the projection model literally provable (count parity), keeps the weak tail (no-threshold-
drop, §N.4), and removes the "which 32 categories?" curation judgment from the deterministic base
(Trap 2 — no human/LLM judgment in what fires). This brief makes that the core of B1.

**CODE-VERIFIED CORRECTION (v2.0) — "project ga_structural" ≠ "project all of L1".** The handoff's
shorthand is loose. Verified in code: `bo_laksana` reads `chart_facts` directly (NOT ga_structural as a
table); `ga_structural` declares `depends_on = ARRAY[]::text[]` and is a pure EMITTER — it does NOT
contain `ga_sensitive` (8,055), `ga_sade_sati` (11,019), or `ga_panchanga` (221) facts (~19,295 rows
written by other writers). So the projection SOURCE is **the full chart_facts signal population (the
union of all 5 L1 chart_facts writers)**, and **count-parity is defined against THAT population, never
against the ga_structural row count alone.** An executor who reads "track the ga_structural fact count"
literally will UNDER-project by ~19k rows. Do not.

**Inherited non-negotiables (every phase):** deterministic-first (Python, no generative LLM in the
build; embeddings-as-transform OK); no audience tier; no silent drops (errors surfaced/flagged, never
hidden); per-chart isolation by `chart_id`; **real `fact_id` references, never mock**; FROZEN
orchestrator contract (`@register('bo_*')` WriterBase, runs on `ctx.db_conn`, NEVER commits/closes it,
NEVER writes `asset_throughput`, gets `chart_id`+`birth_params` from `ctx.config`); `count_sql` is
data-truth; floors aspirational (`target_floor` = achieved after build, never fabricate to a number).
**If a writer seems to need an orchestrator-contract change → STOP, raise with the native.**

---

## §B1 — bo_laksana: FULL projection of ga_structural (the root; everything fans from it)

### B1.0 — Preconditions (verify before writing code; fix-forward if any fail)
1. **Cloud SQL proxy up.** `platform/scripts/start_db_proxy.sh`; confirm `127.0.0.1:5433` reachable.
   The build cannot run without it (this was the B5 blocker — `CURRENT_STATE` v5.75).
2. **Migrations 226 + 230 actually applied to prod.** Don't infer from file presence — query prod:
   confirm `bodha_msr_signals` exists at full spec schema (the ~50 cols the INSERT targets), and that
   the registry rows for the 8 `bo_*` assets carry the spec `count_sql` / `target_table` (mig 230).
   If a migration is on disk but not applied, apply it **surgically** (psql against prod, not deploy.yml
   auto / bulk migrate.ts — [[feedback-deploy-migrations-silent-noop]]); readback after apply.
3. **L1 is built on the native chart.** ALL 5 L1 chart_facts writers have emitted for `482012f1` across
   all vargas × 5 ayanamshas: ga_structural (74,644), ga_strength (2,184), ga_sensitive (8,055),
   ga_sade_sati (11,019), ga_panchanga (221). If L1 isn't built, STOP — B1 has nothing to project.
   (FORENSIC 7/7 is the L1 authority gate; do not proceed past a FORENSIC fail.)
4. **Pin the projection count BEFORE coding the build (the "load-bearing number" is knowable now).**
   Run `SELECT count(*) FROM chart_facts WHERE chart_id=native AND fact_category = ANY(<signal categories>)`
   against prod and record it. This is the count B1 must hit (parity). It does NOT require the build to
   run — it's one query. Capture it so B1.3's parity check has a target.

### B1.1 — Convert bo_laksana from curated-subset to full-enumeration projection
This is the load-bearing change. In `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py`:

- **Remove the hardcoded category allow-list as a FILTER.** The merged writer fetches only rows whose
  `fact_category` ∈ the 32-item `ALL_SIGNAL_CATEGORIES`. Replace that with a fetch of **the full
  ga_structural fact population** for `(chart_id, ayanamsha_id)` — every relationship/conjunction/
  aspect/argala/dispositor/parivartana/composite/avastha row ga_structural emits, plus the other
  genuinely-projected ga_* categories the spec wants as signals (sensitive, panchanga, sade-sati).
  - **Decision rule for "which categories are signals":** project every `fact_category` emitted by ANY
    of the 5 L1 chart_facts writers (ga_structural relational fabric ∪ ga_sensitive ∪ ga_sade_sati ∪
    ga_panchanga signal categories). Do **NOT** project the pure *helper* lookups from ga_strength
    (`graha_shadbala_total`, `graha_dignity_per_varga`, `ashtakavarga_pinda_sarva`) — those are salience
    INPUTS, not signals; keep them as the lookup dicts they already are. **Open decision flagged for the
    native:** other ga_strength facts (shadbala/ashtakavarga/bhava-bala, ~2,184 rows) are currently
    neither projected as signals nor used as inputs everywhere — if the native wants strength facts
    retrievable as first-class signals, widen the projection; default for this build is inputs-only.
    Make the include/exclude boundary a single documented constant (`SIGNAL_SOURCE_CATEGORIES` +
    `EXCLUDED_HELPER_CATEGORIES`) so it is auditable, not scattered.
  - **Net effect:** the allow-list stops being a curation gate. If ga_structural enumerates it, it
    becomes a signal. The 32 categories become a *domain/tradition mapping table* (keep
    `CATEGORY_DOMAIN_MAP` / `CATEGORY_TRADITION_MAP` for the categories you can map; for an unmapped
    category, default `domains_affected = ['general']`, `tradition = 'parashari'`, and **flag it** in
    the writer notes so the native can extend the maps — do not drop the row for lacking a mapping).

- **Keep salience as a column, never a filter.** `salience_formula_v1` still runs per signal;
  `computed_salience` + the decomposition columns are stored; `top_k_salience_rank` is assigned across
  the full population per `(chart_id, ayanamsha_id)`. **No `WHERE salience > x`, no `LIMIT N` drop.**
  Every projected row is inserted. (This is the no-threshold-drop pillar + Trap 2 anti-contamination.)

- **constituent_facts_array = the real L1 fact_id, always.** Each signal references its source
  `chart_facts.fact_id` (it already does: `constituent_facts_array = [fact_id]`). It must NEVER restate
  the L1 computed value as its own truth (Trap 1) — it inherits by reference. FORENSIC-anchored signals
  inherit L1 values (e.g. Muntha = Libra/7H/Venus is read from L1, not re-derived).

- **Heavy-writer shape stays:** `plan_substeps` = one SubStep per ayanamsha; `run_substep` builds the
  lookups, fetches the full fact population, builds one row per fact, ranks, DELETE-then-INSERT scoped
  to `(chart_id, ayanamsha_id)` (per-layer idempotency, §N.3). Do NOT commit/close `ctx.db_conn`.

- **Performance:** full enumeration is ~15× the curated subset. Keep the `_batch_insert` batching;
  if a single ayanamsha's row build is large, stream/iterate rather than holding everything before
  ranking is fine (ranking needs the full per-ayanamsha set in memory — acceptable at this scale, but
  log row counts so a regression is visible). Do not introduce a row cap to "make it fast."

### B1.2 — Update the unit/contract tests for bo_laksana to the parity model
- Tests must assert: **(a)** no category allow-list gates the fetch (projection is by source-asset, not
  a curated name list); **(b)** salience is never used as an insert filter; **(c)** every built row
  carries a non-empty `constituent_facts_array` whose element is a real `fact_id` string;
  **(d)** unmapped categories still produce rows (flagged, not dropped). Keep the existing salience-
  formula unit tests green (the formula itself is unchanged).

### B1.3 — Run B1 and PROVE THE ANTI-DRIFT SPINE before anything else fans out
Run **only** `bo_laksana` for the native chart first (single-asset run, not the whole layer):
`POST /api/cockpit/runs scope=asset/bo_laksana` for `482012f1` (or the orchestrator's single-asset
entry). Then verify, against **prod**, in this order — and **HALT on any failure; do not fan out onto
a broken root**:

1. **Spine resolves (the load-bearing acceptance).** Every `bodha_msr_signals.constituent_facts_array`
   element resolves to a real `chart_facts.fact_id` row for this chart. Query for any signal whose
   array element has no matching `chart_facts` row → **must be zero**. `[verify-against: prod] [via: psql_prod]`
2. **Count parity (the native decision).** `count(bodha_msr_signals WHERE chart_id=native)` ==
   the B1.0-step-4 pinned count = `count(chart_facts WHERE chart_id=native AND fact_category = ANY(signal
   categories))`. The MSR signal count **tracks the full chart_facts signal population** (all 5 L1
   writers — NOT just ga_structural, NOT a curated subset, NOT a predicate catalog). Record both numbers
   in the run notes; they must be equal (minus any rows the writer explicitly logged as skipped, which
   must be zero in a clean run). `[verify-against: prod]`
3. **No re-derivation / no value-restatement (Trap 1).** Spot-check ≥10 signals across categories:
   the signal's stored configuration reflects the L1 value it cites, not a recomputed one. Pick the
   FORENSIC anchors explicitly (Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries, + Muntha) and
   confirm the signal inherits the L1 value. `[verify-against: prod]`
4. **Weak tail present (no-threshold-drop).** Confirm low-`computed_salience` signals ARE in the table
   (query the bottom decile of `computed_salience`; it must be non-empty and far below the top). A
   curated build would be missing these. `[verify-against: prod]`
5. **Idempotency.** Re-run bo_laksana for one ayanamsha; row count is stable (delete-then-insert
   replaced, did not accrete). `[verify-against: prod]`

**If 1 or 2 fail, the projection is wrong — fix the projection, do NOT proceed to B2.** Everything
downstream inherits from this root; a broken root contaminates the whole layer.

### B1.4 — Build the A10 §11 materialized views
`mv_top_signals`, `mv_recurring_patterns`, `mv_domain_summary` (or the names the spec/migration use).
Refresh after the insert. These are read-optimization over the now-complete signal set.

### B1.5 — THE L0 CLASSICAL BRIDGE (native ruling 2026-06-16 — highest-value depth move)
**Problem this fixes:** today only `bo_upaya` reads L0; the classical corpus (`bg_texts` 8,193 chunks,
`bg_rules` 1,976 verse-traceable rules, `brahma_yoga_catalog` 409, `brahma_dosha_catalog` 85) is a
parallel island — never joined to a signal. The synthesis LLM gets the geometric FACT but not the
classical VOICE that says what it MEANS. `bodha_msr_signals.classical_sources_array` exists in the
schema but is currently written `None`.

**The task:** in `bo_laksana` (or a deterministic post-pass over the inserted signals), **populate
`classical_sources_array` for every signal that can be matched**, by a deterministic join — NO LLM:
- **Named yogas/doshas** (`yoga_label`/`yoga_fires`/`dosha_label`/`dosha_fires`): match the signal's
  yoga/dosha name → `brahma_yoga_catalog` / `brahma_dosha_catalog` row → carry its `source_citation` /
  `classical_ref` + the catalog `id`. (The catalog is the canonical name+citation source — handoff §1.)
- **Rule-traceable configurations**: match the signal's configuration against `bg_rules` (1,976
  verse-traceable rules) on the rule's structural predicate → attach the rule id + verse ref where a
  deterministic match exists.
- **Classical text chunks**: attach the most relevant `bg_texts` chunk id(s) for the signal's
  yoga/dosha/configuration via the deterministic catalog→text linkage already in L0 (do NOT do semantic
  similarity here — that's a retrieval-time op; here use the existing id-linkage so it stays
  deterministic). Where no deterministic link exists, leave it for the embedding-time bridge (E1/E6).
- **Unmatched signals** (raw aspects/argala with no classical name): `classical_sources_array` stays
  empty — that is CORRECT and must not be faked. Flag the matched-vs-unmatched ratio in run notes.

**B1.5 acceptance [verify-against: prod]:** every named-yoga/dosha signal carries ≥1 resolvable
classical source (catalog id + citation that resolves to a real L0 row); the match is deterministic
(re-run → identical); unmatched raw signals are empty, not fabricated; run notes report the coverage
ratio. **This is the single biggest lever on whether the synthesis LLM retrieves grounded meaning vs
bare geometry.**

---

## §B2 — Fan-out (parallel on bo_laksana; only AFTER B1.3 + B1.5 pass)

All project/aggregate from the now-complete `bodha_msr_signals`. Each populates its A11/A12/§14 tables.

- **`bo_sangati` (CDLM, A11):** `bodha_cdlm_cells`, `_domain_rollups`, `_chart_summary`,
  `_pattern_clusters` via `linkage_formula_v1`, **plus `bodha_convergence`** (convergence-density-per-
  domain via `convergence_formula_v1`, §13.1). Convergence rows are **first-class rows**, not just
  columns — N independent L1 signals → one domain = weight of evidence.
- **`bo_karanajala` (CGM edges, A12):** `bodha_cgm_edges`, `_sub_graphs`, `_motifs`, `_chart_summary`,
  **plus `bodha_contradictions`** (signals in tension — doubles as the drift guardrail) **and
  `bodha_cgm_paths`** (§13.1). This is the graph — **invest deepest**: final-dispositor (chart's center
  of gravity), parivartana cycle structure, weighted centrality via `centrality_formula_v1` (most
  consequential factor), significator path-analysis. (A12 is ONE igraph compute; `bo_bimba` is a thin
  nodes face on the same compute — confirm against the DAG executor.)
- **`bo_bimba` (CGM nodes, A12):** `bodha_cgm_nodes` (graha + bhava + domain nodes per ayanamsha).
- **`bo_samskara` (embeddings):** `bodha_signal_embeddings`, **1:1 with MSR signals.** Note: the
  merged writer uses `placeholder_hash_v1` (deterministic 768-dim, NOT real semantic embeddings).
  **Keep the placeholder for this build** (deterministic-first; it satisfies the 1:1 + schema), but
  **flag explicitly in the run notes + L2_BODHA_CLOSE** that real semantic embeddings are a follow-up
  before retrieval quality depends on them. Do not silently present the placeholder as semantic.
- **`bo_samvada` (UCD, A14) = Option A:** a read-side join — `vw_chart_digest` view + `query_ucd` tool.
  **NOT a per-chart writer.** (UCN narrative writer is retired per A14.)

**B2 acceptance [verify-against: prod]:** each fan-out asset's tables populated; convergence +
contradiction are first-class ROWS; CGM graph metrics present (centrality, paths, final-dispositor);
embeddings 1:1 with MSR; `query_ucd` returns the digest. Convergence/contradiction formulas stamped
with their `_v1` version on each row.

---

## §B3 — bo_upaya (RM); depends_on bo_laksana + bo_sangati
All 6 `bodha_rm_*` tables via `resonance_score_v1` + `resonance_match_score_v1`. Every remedy is
**labelled from `brahma_remedy_corpus` (L0)** — grounded, never invented; each carries a classical
citation. **Acceptance [verify-against: prod]:** 6 RM tables populated; every remedy row resolves to a
`brahma_remedy_corpus` citation; resonance scored deterministically (formula-versioned).

## §B4 — bo_pramana_mapa (global scorecard) + the UCD read surface
- `bo_pramana_mapa` → global `synthesis_quality_scorecard` + the **Trap-1 audit baked in** (the
  scorecard itself re-checks that constituent_facts resolve — the spine becomes a standing CI-able
  metric, not a one-time check).
- Confirm the UCD read surface (`vw_chart_digest` + `query_ucd`) returns the unified digest.
- **Acceptance:** scorecard populated; Trap-1 audit reports zero unresolved fact_ids; `query_ucd` works.

## §B5 — Orchestrator full-layer build + cockpit verify + retrieval tools + L2 seal
1. **Full-layer run via the orchestrator:** `POST /api/cockpit/runs scope=layer/bodha` for `482012f1`.
   The orchestrator self-orders from `depends_on` (bo_laksana → fan-out → bo_upaya → bo_pramana_mapa).
   Confirm the whole layer builds from ONE run in DAG order (not asset-by-asset by hand).
2. **Cockpit/Atlas truth:** 8 `bo_` assets lit; each headline count = the **summed `count_sql`** over
   all that asset's tables (per handoff §4 — e.g. `bo_sangati` = cdlm_cells + domain_rollups +
   chart_summary + pattern_clusters + bodha_convergence, all `WHERE chart_id=$1`). Atlas shows real
   sample rows + astrological notes. Fix any NOT-MIGRATED/zero-count surface at its `count_sql`, not
   the UI ([[reference-cockpit-v1-v2-split]] — trace from the registry/route, the cockpit's the v2 tree).
3. **target_floors:** set each `bo_*` `target_floor` = the achieved summed count (floors aspirational).
4. **Retrieval tools for Bodha outputs (Wave-3 gate extension):** add ≥1 retrieval tool per new
   `bodha_*` table to the existing retrieval layer (`platform/src/lib/retrieval` +
   `python-sidecar/pipeline/retrieval`) and extend `tests/retrieval/coverage_gate.test.ts` so every
   `bodha_*` table is covered (the gate fails if one is orphaned). Do NOT build a parallel retrieval
   layer; no tier gating; weak tail retrievable (paginate, never LIMIT-drop).
5. **Promote + seal:** flip the 8 `bo_*` registry rows DRAFT→CURRENT (the same flip L1 had — only
   AFTER the build verifies). Reconcile the registry to the §14 map. Author/finalize
   `L2_BODHA_CLOSE_v1_0.md` with the validated state + the **L3 Kāla onboarding contract** (§4).
   Update `CURRENT_STATE_v1_0.md` §2 + append `SESSION_LOG.md` atomically at close.

**B5 acceptance:** layer builds from one orchestrator run in DAG order; FORENSIC 7/7 still passes; no
silent drops; cockpit/Atlas reflect true summed counts; Bodha retrieval tools + CI gate green;
`L2_BODHA_CLOSE` written; CURRENT_STATE + SESSION_LOG updated. **NOTE: L2 does NOT seal until §B6 (eval
harness) passes — see §B6.**

---

## §E-PHASES — Retrieval-depth enhancements (native-approved 2026-06-16; the synthesis-quality layer)
These are NOT optional polish — they are what make the difference between the LLM retrieving
column-soup and retrieving acharya-grade, grounded, semantically-reachable context. Sequence them with
the build (E1/E2 at B1; E3/E4 at B2; E5/E8 across B5; E6/E7 fast-follow).

### E2 (do at B1) — Lossless deterministic `signal_summary_text` on every MSR signal
Add a deterministic, template-generated natural-language summary column to `bodha_msr_signals` (or a
1:1 side table). **Lossless requirement:** render all typed columns THEN iterate EVERY key in
`configuration_jsonb` (the current `_build_input_summary` only pulls 5 hardcoded keys — that is lossy;
fix it). Example output: "Jupiter–Venus conjunction in D1 Sagittarius (Lahiri), orb 2°, salience 0.81,
rank 12/anch, supports career+spirituality, two-pass verified, cites Phaladeepika 6.12." No LLM (pure
template). This is the dense citable surface the synthesis LLM reasons over AND the input text for E1.
**Acceptance:** every signal has a non-empty summary; a fuzz test confirms no `configuration_jsonb` key
is omitted from the text (losslessness).

### E1 (do at B1, after E2) — Real semantic embeddings (replace `placeholder_hash_v1`)
`bo_samskara` already builds the input text + writes a 768-dim vector; only the hash→model line changes.
Swap `_text_to_deterministic_vec` for a real embedding of the E2 `signal_summary_text`. **Determinism is
preserved by PINNING model + version** (embeddings are a ratified deterministic transform): store
`embedding_model` + `embedding_model_version` on the row (columns exist); a model change = version bump +
rebuild. **Prefer a LOCAL/offline embedding model** (keeps the build air-gapped + 100% reproducible, and
avoids the Anthropic-banned / cost-gated API issue — [[feedback-llm-model-selection]]). **Acceptance:**
embeddings are real (semantic neighbors are astrologically related — spot-check that two "career
weakness" signals are cosine-near, which a hash CANNOT achieve); model+version stamped; 1:1 with signals.

### E3 (do at B2) — Convergence + contradiction as FIRST-CLASS retrieval targets
Add retrieval tools `query_chart_convergences(chart_id, domain?, top_k)` and
`query_chart_contradictions(chart_id, domain?)` that return rich shapes: each convergence with its N
constituent signals + their citations; each contradiction with both sides + the deterministic tension
basis. This is the "weight of evidence" surface — where the LLM stops sounding like rule-lookup and
starts weighing evidence like an acharya. **Acceptance:** both tools return real rows for the native;
returns include constituent signal ids + citations.

### E4 (do at B2) — The "deep digest" first-call tool over UCD
Make `query_ucd` / `vw_chart_digest` the LLM's orientation call: one return with top-N salient signals,
the domain convergence map, active contradictions, the graph center-of-gravity (final dispositor +
top-centrality nodes), and weakest-graha resonance targets — each a citable summary with drill-down ids.
Orientation-before-drill makes the LLM's follow-up queries targeted, not scattershot. **Acceptance:**
one call returns the chart skeleton with drill-down ids that resolve.

### E5 (do at B5) — Provenance contract test (every tool return carries tier + citation + fact_ids)
Add a CI retrieval-contract test: call every Bodha tool; FAIL if any return is missing `epistemic_tier`,
`salience/computed_salience`, `citation_human`, or constituent `fact_id`s. Makes "the LLM can always
cite + state confidence" a property the build cannot regress past. **Acceptance:** the test exists +
passes; a deliberately-stripped return fails it.

### E6 (fast-follow) — Graph path as a narratable reasoning chain
Expose a tool returning the `bodha_cgm_paths` path between two significators/domains as an ordered,
citable chain ("10th-lord → dispositor Saturn → aspected by Jupiter → ..."), so the LLM narrates the
MECHANISM, not just the conclusion. **Acceptance:** returns an ordered, citable path for a known pair.

### E7 (fast-follow) — Cross-ayanamsha consistency surfaced as confidence
Ensure `cross_ayanamsha_consistency_score` is computed at B1 (column exists) and RETURNED by retrieval,
so the LLM prioritizes 5/5-ayanamsha-stable signals and caveats 2/5 ones. Within-chart, deterministic
(L2, not L5). **Acceptance:** the score is populated + returned; a 5/5 and a 2/5 signal are
distinguishable in a tool return.

### E8 (do at B5) — Weak-tail REACHABILITY proof (completeness meets retrievability)
The coverage gate proves a tool EXISTS per table; it does NOT prove the weak tail is REACHABLE. Add a
completeness test: identify the lowest-`computed_salience` signal for the native, assert it is
returnable via pagination (never `LIMIT N`-dropped). **Acceptance:** the known weak-tail signal is
retrieved; the test fails if any tool truncates the distribution.

---

## §B6 — SEMANTIC-COMPLETENESS EVAL HARNESS (native ruling — GATES the L2 seal)
**L2 does NOT seal on §B5 alone.** Per-table coverage (B5) proves SYNTACTIC coverage (a tool exists per
table). It does NOT prove SEMANTIC completeness — that the planner actually RETRIEVES everything
relevant for a real question and assembles the complete picture. That gap is where synthesis quality
lives, so the native ruled it a seal gate.

**Build the eval harness:**
- A curated set of known chart questions for the native (e.g. "what does this chart say about career?",
  "what are the strongest yogas?", "what contradicts the wealth indications?", "what remedies for the
  weakest graha and when?") — span domains, convergence, contradiction, graph, remedies, classical
  grounding.
- For each, a **known-complete answer-set**: the specific signals / convergences / contradictions /
  citations a thorough acharya-grade answer MUST include (derived deterministically from the corpus —
  this is the ground truth).
- Run each question through the LIVE retrieval + planner; **score recall** ("did it retrieve all the
  required items?") + provenance ("did each come with tier + citation?"). Seed from the existing
  `answer:eval` baseline ([[project-ganga-baseline]]) — extend it with the known-complete answer-sets.
- **Seal gate:** L2 seals only when the harness passes the native's recall threshold. A sub-threshold
  run is a planner/retrieval fix, not a seal. Author the harness as a committed, re-runnable suite (not
  a one-off), so it becomes the standing regression gate for synthesis completeness.

**B6 acceptance:** the eval harness exists as a committed suite; runs against live retrieval+planner;
scores recall + provenance per question; meets the native's threshold; a deliberately-removed tool
drops the score (proving the harness measures real retrieval). **Only then does L2_BODHA_CLOSE seal.**

---

## §FINAL — Whole-arc acceptance
- [ ] **B1 (the spine):** bo_laksana is a FULL projection — constituent_facts_array resolves for every
      signal (zero unresolved); MSR signal count tracks the ga_structural fact count (parity, not a
      curated subset, not a predicate catalog); FORENSIC anchors inherit L1 values; weak tail present;
      idempotent. **Proven on bo_laksana ALONE before any fan-out.**
- [ ] **B2:** convergence + contradiction first-class ROWS; CGM graph built deepest (centrality / paths
      / final-dispositor); embeddings 1:1 (placeholder flagged); UCD read surface live.
- [ ] **B3/B4:** RM grounded to L0 corpus (every remedy cited); scorecard + standing Trap-1 audit.
- [ ] **B5:** one orchestrator run builds the layer in DAG order; cockpit/Atlas true; Bodha retrieval
      tools + CI gate; DRAFT→CURRENT; L2_BODHA_CLOSE sealed with L3 onboarding; CURRENT_STATE/SESSION_LOG.
- [ ] Ran continuously phase-by-phase — no human gate fired (dependency gates + Tier-3 rails only).
- [ ] Migration numbers fresh (no collisions); surgical apply + post-apply readback held.

## §OUT OF SCOPE (named so they aren't pulled in)
L3 Kāla / dasha-temporal activation (the time layer — when a relationship is active/dormant by period);
any `ga_structural` re-amendment (it is complete at 74,644 rows — do not re-open it); cross-chart
correlation (L5 Mīmāṃsā — never compute it in L2, it contaminates the deterministic base, Trap 2). Do
NOT reintroduce the predicate-firing model or G52 as a firing engine. Do NOT change the FROZEN
orchestrator contract.

---
*End of BODHA_B1_FULL_PROJECTION v1.0. The one delta from the prior Wave-4 brief: bo_laksana is a FULL
enumeration projection (native decision 2026-06-16), MSR count tracks ga_structural fact count, the
weak tail is kept, and the anti-drift spine is PROVEN on bo_laksana alone before B2 fans out. Then the
fan-out (convergence/contradiction first-class, graph deepest), bo_upaya grounded to L0, scorecard with
a standing Trap-1 audit, full orchestrator layer build, Bodha retrieval tools, and the L2 seal.*
