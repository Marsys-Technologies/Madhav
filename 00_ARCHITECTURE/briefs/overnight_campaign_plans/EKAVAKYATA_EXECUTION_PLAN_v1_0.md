---
campaign: EKAVĀKYATĀ (एकवाक्यता — one-voice-ness; Mīmāṃsā's principle of unified purport)
version: 1.0
status: PLAN-OF-RECORD for the overnight autonomous execution, 2026-08-15 → 16
authored_by: Fable 5 desk session (plan) — execution by the swarm defined in §3
source_of_truth: pp2-audit/ corpus at aa0227abc (141 findings, 23 classes) +
  the elevated remediation arc (artifact cbfe5ced) + the desk's direct-verification pass
mode: FULLY AUTONOMOUS — no human gates. PRATINIDHI (§3.2) holds the native's proxy.
---

# EKAVĀKYATĀ — OVERNIGHT EXECUTION PLAN

## §0 MISSION, END-STATE, AND THE THREE INVARIANT RULES

**Mission.** Execute the elevated Paripūrṇa-2 remediation arc: make the instrument speak
with one voice (P1), deliver its answers (P2), be classically right (P3), speak as an
acharya (P4), claim only earned confidence (P5), close the prediction loop (P6), on clean
substrate (P7) — via three load-bearing mechanisms: the One-Voice Spine, Essence-First
Serving, and the Earned-Knowledge Economy.

**End-state tonight (the gate's definition, §7):**
- Wave 0 fully MERGED + DEPLOYED + LIVE-VERIFIED.
- Waves 1–3 lanes merged in dependency order, each live-verified; unfinished lanes exist
  ONLY as clean branches with handoff notes — never half-merged.
- `origin/main` == production: `mcp_server_info.catalog_version` embeds the git sha
  (observed format `catalog-1+t152+r<sha12>`) — the gate verifies the deployed sha IS
  the main tip. This is the mechanical "production in sync with main" check.
- The 27 CL-00 controls green after every merge batch (regression baseline).
- `ekv_gate.py verify` exit 0 for the waves claimed complete.

**Three invariant rules (every agent, every decision):**
1. **Merged-and-live-verified, nothing less.** A lane counts only when its sha is an
   ancestor of origin/main AND a live post-deploy probe evidence file exists. (PR #1287
   lesson — authored ≠ shipped.)
2. **Sarvatra.** No fix lands at fewer than all its sibling sites (census, not memory),
   and each fix ships with the lint/test that makes the next divergence fail closed.
3. **FM-09.** A ledger assertion is never evidence. Call the tool, run the query, read
   the code. Verifiers re-derive; they never inherit.

**Goal fixed, path adaptive.** Agents may re-sequence, re-scope lanes, or route around a
blocked dependency — they may NOT change the end-state definition, the invariant rules,
or the isolation rules (§4). Judgment calls that would have gone to the native go to
PRATINIDHI (§3.2), who logs a numbered EKV-R ruling in the campaign ledger.

## §1 CONTEXT EVERY AGENT MUST LOAD (verified facts — do not re-derive)

Read before coding: `CLAUDE.md` (§N standards), this plan, your stream kickoff, and the
finding texts for your lanes in `pp2-audit/manifest.json` (jq by finding id).

**Canonical charts:** native `482012f1-710e-4a25-994a-93821f5871aa` · comparison
`1c826d5a-41cb-4450-b4dc-59d440e5f75a`. DB port 5433. Never write product tables except
via the migrations this plan names (§C-lanes) — everything else is read-only.

**Desk-verified mechanics (trust these; they were read from source hours ago):**
- **Object-blind trimmer (F-56/F-111 root cause, CLOSED):**
  `platform-mcp/src/lib/response_budget.ts:508-536` `autoDetectTrimmableSections`
  declares only top-level ARRAYS >10 items. `assess_*`'s dominant sections
  (`activating_dasha` ~62KB, `verdict_skeleton` ~43KB) are OBJECTS — invisible to
  PASS 1/2. Ships-anyway path `:280-300`, flag emit `:439`. Composition replaces
  subtraction; do not attempt trimmer tuning.
- **timing_hooks (F-51):** trim sections `platform-mcp/src/tools/registry_bridge.ts:3512`
  (`checklist.timing_hooks.current`) and `:3531` (`mahadasha_windows_by_graha`) carry NO
  hardFloor today; every existing `hardFloor:true` in that file: 3437/3457/3475. History:
  timing_hooks once ballooned to ~51KB (comment at
  `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:759`) — fix =
  `hardFloor:true` + SMALL minKeep (3–4), not a copy of bearing_yogas' config.
- **PACT spine exists:** closed typed vocabulary in
  `platform/src/lib/retrieval/registry/layers/register_d10_pact.ts` — `denied_at_promise`
  :257, `denied_at_confirmation` :310, `denied_at_activation` :362,
  `chain_pending_activation` :387, `chain_incomplete_infra` :442, `chain_complete` :456.
  `kala_upaya_diagnosis.ts` already consumes it (`platform-mcp/src/lib/`, pact_status
  handling ~:266-300, remedy fan-out :507-511 — mitigation_map gets NO domain/graha).
- **Domain aliasing precedent:** `SHASTRA_MAP` in `register_d9_judgment.ts` — keys
  marriage/relationship/partnership → one spec {bhava 7, karakas [Venus], varga D9,
  signal_domain 'relationship'}; progeny/children → signal_domain 'other' (F-57's
  mechanism). Charter generalises THIS, it does not invent.
- **probability_tier is upstream data:** `platform-mcp/src/tools/kala_views/ahead.ts:14`
  — pre-computed in the Kāla field (ka_kalasutra.py). The promise join belongs at
  serve-time, in the composition layer. TIER_LABEL map :1134-1139; narration sites
  :1404, :1528-1543.
- **Whitelist (F-02/F-07):** `platform/src/lib/retrieval/registry/tool_name_bridge.ts`
  — `MCP_TO_RETRIEVAL_TOOL` keys only `read_classical_text` (:95 in-object). The four
  missing keys: `read_chapter`, `list_classical_texts`, `find_verses_about`,
  `search_classical_texts` (their URIs already exist in `TOOL_NAME_TO_URI` :107-112).
  The file header (:29) already plans TOOL_NAME_TO_URI's retirement — finish it.
- **Dignity (F-62, diagnosis completed):** the L1 writer is
  `platform/python-sidecar/ga_writers/ga_structural_writer.py:4872-4884` — a 4-value
  if/elif (exalted/debilitated/own/neutral). Live vocabulary confirmed by SQL: exactly
  those 4. The repo already holds the correct material:
  `pipeline/orchestrator/writers/bg_dignity_reference.py` (moolatrikona degree ranges
  per graha, :108-125+) and a working MT classifier
  `pipeline/orchestrator/writers/bo_pratijna_v4_engine.py:272`. A third classifier,
  `ga_writers/ga_vargas_writer.py::_compute_dignity` (~:464-476), emits MT sign-level,
  checks MT BEFORE Own, no degree gate (over-emits). Remediation = ONE oracle (§B-1).
- **Nodal (CL-07):** correct table `ga_structural_writer.py:564`
  `NODE_PARASHARI_ASPECTS={5:1.0,7:1.0,9:1.0}` (used :595/:1135/:4652). Broken:
  `services/gochara_grammar/primitives.py:189-194` SPECIAL_DRISHTI_DEG (Mars/Jup/Sat
  only) + `_DEFAULT_DRISHTI_DEG=[180.0]` fallback (call sites :208, :340);
  `ga_writers/ga_yoga_writer.py:1499-1504` NB_GRAHA_DRISHTI + NB_DEFAULT_DRISHTI={7}
  (consumer :1591); `ga_vargas_writer.py::_compute_aspect_matrix` local `special` dict
  (dead today, latent).
- **Yoga predicate (F-66, sharpened):** `ga_yoga_writer.py:644` —
  `if len(placed) >= 5 and all(p in ps_in_houses for p in placed)` — fires at ≥5-in-
  window. Correct rule: exactly 7 planets, 7 distinct houses, one per house. The sibling
  exact-count branch (:548-555 `distinct_signs_occupied`) is the in-file correct pattern.
- **F-29 (worse than filed):** stored enum (SQL-confirmed) =
  {CONFIRMED, PARTIAL, REFUTED, UNRESOLVED}. The FILTERs at
  `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts:118-120`
  compare lowercase 'confirmed'/'partial'/'denied' — case AND value mismatch
  ('denied' ≠ REFUTED) and UNRESOLVED is absent from the served schema. Serve all four.
- **Loop (live SQL tonight):** brahma_prospective_ledger `lifecycle_status`: 35 open /
  1 matched / 0 terminal ever; `mcp_prediction_outcomes` 0 rows; empty-daterange rows
  now **6 (was 4 at audit time — ACTIVE LEAK; find the writer via the new rows'
  generator_class/filing_method)**. Crash paths:
  `platform/src/lib/lel/prospective_ledger.ts:758-760` (parseDaterange throw; call
  sites :592/:718/:725) and mi_bhara float(None) (state='error' live, TypeError in
  asset_throughput.last_error). Existing fix branch: PR #1287, worktree
  `/Users/Dev/Vibe-Coding/Apps/pp-fix1`, commit 525188467 — rebase, extend, merge.
- **False zero (F-140):** `noLelCalibrationMaturity()` call sites: kala_views/
  priority.ts:434, explain.ts:699, elect.ts:761, upaya.ts:427, ahead.ts:99 (+import
  lines). Real data live: kala_field_skill 7 rows, n_events=14, weights_version
  v0_classical for the native.
- **Ayanamsha (F-59):** `platform-mcp/src/tools/register_p1_aliases.ts:39-43` local
  AYANAMSHA_ALIAS + `na()` — correct helper `resolveChartFactsAyanamsha` ALREADY
  imported (:26), wired at 1 of 11 sites (:1347). Fix the other 10 (audit lists sites:
  382, 494, 572, 650, 702, 920, 970, 1199, 1244, 1290).
- **transit_quality (F-48):** `brahmagyan/phala/muhurta.py:420`
  `_transit_quality_for_window` — lunar-cycle JD arithmetic only, docstring admits
  approximation, no action_type. `_dasha_quality_for_chart` :372 takes no action_type
  either. `compute_muhurta_score` :202; `_panchanga_quality_for_action` :231 IS
  action-aware (:303-329) — the in-file correct pattern.
- **leakage 'clean' literals (F-104):** mi_darshana.py lines 136, 183, 214, 246, 365,
  508 (INSERT at ~:527-540). Honest tier precedent: mi_adhilepa 'not_assessed'.
- **ph_nimitta tag (F-68):** engine.py:418 dataclass default
  `confidence_basis='structural_not_yet_empirical'`; numerics attached unconditionally
  (:472-480, :579-587, :685-693). Serving passthrough:
  `layers/L4_phala/query_predictive_anchors.ts`.
- **Bundle (F-30/74):** `platform/src/lib/mcp/bundle_adapters.ts` callPrimitive :131-151
  (discards upstream status), fan-out :320+; the 5 failing sub-caps are all
  scope:'per_chart' hitting `authorizeChartAccess` in
  `platform/src/app/api/mcp/primitives/[tool]/route.ts:200-218` with a loopback
  principal; the 3 global-scope survive.
- **Deploy-sync mechanical check:** `mcp_server_info` → `catalog_version` embeds the
  deployed git sha. After each deploy batch, assert it equals origin/main tip.
- **Governance numbers:** drift_detector exit 3 / 216 findings; schema_validator
  exit 2-3 / 43-44; CURRENT_STATE.last_session_id vs SESSION_LOG tail mismatch (F-95);
  CAPABILITY_MANIFEST 115 governance ids, 0 data-asset ids (F-81); migration 456 SQL
  deleted (F-79).

**The 27 CL-00 regression controls** (must stay green; ids):
F-32,72,75,76,77,80,82,83,84,85,86,87,88,91,96,97,98,99,100,101,102,103,105,106,109,137,138.
Cheap-to-run subset for per-batch CI: F-75/76/83/84/85/87 (SQL invariants) + F-96 (lint
self-test) + a 3-tool live probe. Full set at wave close.

## §2 STREAMS — PARALLEL SESSIONS AND THEIR LANES

Five streams = five parallel Claude Code sessions + three standing roles (conductor,
PRATINIDHI, SENTINEL). Path ownership is EXCLUSIVE (§4). Lanes list: id · scope ·
findings · exit test. Wave tags: [W0] tonight-first, [W1..W3], [C]=continuous.

### STREAM A — SEVĀ (serving core; TypeScript; the largest stream)
OWNS: `platform-mcp/**`, `platform/src/lib/retrieval/registry/**` EXCEPT
`layers/L4_phala/query_prospective_ledger.ts` (→C), `platform/src/lib/mcp/**`,
`platform/src/app/api/mcp/**`.

- A-01 [W0] timing_hooks hardFloor+minKeep(3) at registry_bridge.ts:3512/:3531 ·
  F-51 · test: §N.6 invariant — no answer-bearing section floors to 0 while hora/
  catalog rows survive; judgment marriage timing non-empty at 12KB budget.
- A-02 [W0] whitelist 4 keys + begin TOOL_NAME_TO_URI retirement · F-02/07 · test:
  four tools return content live; census: every surgical contract callable.
- A-03 [W0] F-16/F-128 typed unwrap helper for callRegistryCapability + count-equality
  test · bodha_discoveries_get serves rows at top level.
- A-04 [W0] F-140 facades: delete noLelCalibrationMaturity at 5 sites, wire
  kala_field_skill · test: facades serve n_events=14 for native.
- A-05 [W0] F-29 enum fix in query_insights.ts (4 uppercase buckets incl UNRESOLVED)
  · golden: 2/23/7(/+unresolved) distribution served.
- A-06 [W0] F-119 TS half: attach resolution_disclosure/{resolution,is_timing_window}
  to assess gochara_sweep rows; suppress bare point dates (no prob/interval) ·
  test: zero temporal_shape='point' rows without disclosure in assess_health.
- A-07 [W1] Domain Charter module (single registry: id, aliases, bhāva, kārakas,
  varga, signal_domain, reading_families, promise_hook) generalising SHASTRA_MAP;
  consumers: judgment, gochara_* domain resolution, assess family, kala_upaya,
  intent_classify regex retirement · F-53/55/57/58/24/40/41/42 · test: typed
  UNKNOWN_DOMAIN on every handler; 'marriage' resolves everywhere Venus/7th does.
- A-08 [W1] One-Voice Spine: promise-join helper (reads pact_query result for
  (chart,domain)) + INV-1 enforcement in the composition kernel; reconciliation
  object {projection, promise_verdict, shared_fact_ids, stance} · F-110/49/51-pair ·
  test: kala_ahead × kala_upaya (native, relationship) one reconciled verdict;
  no_contradictions certification impossible in a denied domain.
- A-09 [W1] Sāra composition layer: kernel(≤2KB: verdict+flags+promise+pointers) →
  grounding → evidence → corpus; counts computed at assembly; composition_report;
  convert assess_* + judgment_query + kala_now/explain/ahead/upaya first, then
  kala_elect/story/priority/ritual (F-13/122/28 die here), then remaining GAP tools
  · F-56/111/112/45/12/37/44 · test: 125 tools at budget_kb=8 parseable, under
  ceiling, verdict-bearing; concise strictly smaller.
- A-10 [W1] Middleware: uniform chart-existence+entitlement precondition (F-38);
  reading-family parity via Charter (F-14/15/31/124); B.11 orientation on upaya
  path (F-125); budget-echo unified (F-46).
- A-11 [W1] Bundle principal fix + real upstream status surfaced (F-30/74/127) ·
  test: 8/8 subsystems both charts.
- A-12 [W1] INV-2 determinism: total ORDER BY + pk tiebreak on reducing queries
  (F-92 dedup tiebreaker, F-60 stable pagination incl. graha_shadbala_total
  reachability, F-115 pinned rank-1); result_hash repeat-equality harness top-20.
- A-13 [W1] Error boundary at dispatch edge (F-89/90): typed, path-free errors;
  raw text server-side only. + F-39 template fix ('this chart exists' claim).
- A-14 [W3] Register/gloss enforcement in kernel+grounding (v3 register mechanism
  everywhere) + F-126 split (retrieval-determinism vs evidential-weight) + F-132/
  129/130 template fixes · lint hook from D-03 · test: zero raw signal_type_id/
  enum/JSON in *_text/*_thesis/*_statement across 125-tool sweep.
- A-15 [W1] F-59 ayanamsha: wire resolveChartFactsAyanamsha at the 10 remaining
  sites; delete local map · control probe: bogus id still errors; true_chitra rows
  (longitude 12.4467 LAGNA) served and echoed truthfully.
- A-16 [W3] F-113 TS: direct natal D1 7th-house/7th-lord/kāraka dignity join in
  assess_marriage (spec from B-05) + checklist units assert their fact join ·
  test: 'exalted' Saturn 7th present in response.
- A-17 [W1] kala_upaya remedy scoping (F-49/118/115): thread PACT targeted_graha
  into mitigation_map call; fallback to resonance rank-1 when diagnosis names none;
  dedupe the 50-identical-rows slate; efficacy_tier → honest provenance field.
- A-18 [W2] gochara URI registration (F-73): register the L4 capability URI +
  forbid transport-failure→epistemic-verdict conversion (typed infra_error).

Internal parallelism: A-01..A-06 six builders at once (disjoint files). A-09 is the
serial backbone (response_budget.ts + registry_bridge.ts) — ONE senior builder owns
those two files end-to-end; others queue behind via lead's file-lease board. A-07/A-08
(new modules) parallel to A-09 early, integrate after kernel API stabilises (lead
freezes the kernel interface FIRST — write the type + doc comment before anything).

### STREAM B — ŚĀSTRA (classical engines; Python only)
OWNS: `platform/python-sidecar/**`.

- B-01 [W1] Dignity oracle: one module (brahmagyan/) with degree-gated MT from
  bg_dignity_reference data; consumers: ga_structural_writer :4872 region,
  ga_vargas_writer._compute_dignity, bo_pratijna_v4_engine (import, don't fork) ·
  F-62 · goldens: Jup 9.79° Sag→moolatrikona; Jup 15° Sag→own; nodes per §2.1
  neutral-default; Sthana Bala 45/30 split downstream.
- B-02 [W1] Nodal: shared constant (import NODE_PARASHARI_ASPECTS or hoist to
  brahmagyan/aspects.py); fix primitives.py SPECIAL_DRISHTI_DEG (+nodes 5/7/9),
  ga_yoga NB_GRAHA_DRISHTI, ga_vargas local dict · F-19/20/21/52/64/65 · test:
  unit — Ketu-in-Leo casts 5th onto Venus-in-Sagittarius case from F-52; census:
  no local graha→aspect dict outside oracle (pairs with D-01 lint).
- B-03 [W1] Yoga predicates: exact 7-planet/7-distinct/one-per-house for the
  consecutive-house branch (:628-649) · F-66 · golden: native 4-house cluster
  non-firing for Chatra/Ardhachandra; Kedara still fires.
- B-04 [W1] mi_darshana 6× 'clean' → 'not_assessed' (F-104); mi_bhara isempty/None
  guard in falsifier-resolution (F-71; C-01 repairs data, this guards code).
- B-05 [W1] Classical spec pack for A-16/A-14: 7th-house join spec; register
  glossary entries for the leaked token families (F-114/131 vocab); checklist
  not_built units for bhavat-bhavam + cross-varga (F-107/108) registered in the
  checklist source (locate: reading_checklist emitter; likely bo_laksana) ·
  disclosure-first: units exist tonight even with computation absent.
- B-06 [W2] muhurta honesty (F-47/48): action_type threading into dasha/transit
  legs where real computation exists; transit_quality either wired to the sidecar
  ephemeris (docstring's own instruction) or renamed lunar_phase_quality with
  composite reweighted + disclosure · §N.8 test: no signal named for a computation
  that doesn't exist.
- B-07 [W2] ph_nimitta: adopt unified epistemic enum value (keep numerics in DB —
  suppression is serve-side A-09/A-14; B ensures tag correctness + cardinality_note
  stays) · F-68 python half.
- B-08 [W3] Salience/ranker (F-114/131): domain-affinity weighting (Charter kārakas/
  bhāva), servable=false for abstention markers (floored:*), tie-break by relevance
  then pk; plateau test: no byte-identical top-10 salience; marriage∩progeny top-10
  ≤3 · touches bo_* lens writers / signal emission.
- B-09 [W2] Rebuild prep: identify exact dispatch for gochara-window rebuild (use
  existing platform/scripts/dispatch_* patterns + SAMPURTI canary discipline);
  hand E the runbook: canary class first, then full; 35-min stall rule.

### STREAM C — ṚTA (the loop's data path)
OWNS: `platform/src/lib/lel/**`, `platform/src/lib/retrieval/registry/layers/
L4_phala/query_prospective_ledger.ts`, `platform/migrations/**` (new files only),
`platform/scripts/` (new repair script only), the pp-fix1 worktree/PR #1287.

- C-01 [W0] Ledger repair: migration — nullify/repair the 6 isempty rows +
  `CHECK (NOT isempty(observation_window))` (guarded, idempotent); surgical +
  verified per §N.4 (assert applied in _migrations_applied AND live behaviour).
  PRATINIDHI sign-off logged before merge (product-table write).
- C-02 [W0] Writer hunt: the leak is ACTIVE (4→6 tonight). Read the 2 newest empty
  rows' generator_class/filing_method/filed_by/as_of → locate the filing call site
  → fix it to file real ranges or refuse · test: negative-insert rejected by
  constraint AND writer files a valid range in a dry-run.
- C-03 [W0] PR #1287 adoption: rebase 525188467 onto main; extend guards to BOTH
  call paths (prospective_ledger.ts :592/:718/:725 + query_prospective_ledger.ts
  toServed) · test: standing_predictions_read returns clean live (the audit's own
  reproduce_cmd).
- C-04 [W1] Outcomes path: mimamsa_outcome_record smoke on comparison chart via a
  synthetic prediction driven open→resolved→dismissed through the REAL lifecycle
  (C4-LOOP precedent, leaves DB clean); evidence saved · unlocks Mechanism-3
  promotion path (consumed by A-09's gate).
- C-05 [W2] Auto-filing cadence (R28): served kernel projections file ledger rows
  (dedupe by configuration_signature); cadence job spec handed to E · may land
  morning-after per degrade order.

### STREAM D — DHARMA (guards, lints, CI, governance record)
OWNS: `platform/scripts/governance/**`, `.github/**`, new lint/test files anywhere
(new files only — never edits stream-owned source), `00_ARCHITECTURE/` governance
docs named below.

- D-01 [W1] Lints (fact-category-pin-lint pattern): no-local-aspect-dict,
  no-local-dignity-table, no-local-ayanamsha-map, dualOutput-requires-toolName,
  no-raw-internal-token-in-narrative (signal_type_id/enum/JSON in *_text fields) ·
  each with hermetic self-test (F-96 pattern) + allowlist for pre-fix sites that
  shrinks as A/B land.
- D-02 [W1] Param-parity generator: from each tool's JSONSchema, a table-driven
  test asserting every declared param changes result_hash or is marked advisory ·
  kills CL-03 class; run against the canonical chart snapshot fixtures.
- D-03 [W1] Reachability CI: every registered contract with annotations.surgical is
  a whitelist key AND live-callable (the audit's whitelist_sweep as a permanent CI
  census); every callRegistryCapability URI resolves.
- D-04 [W1] CL-00 harness: the 27 controls as a runnable battery
  (scripts/governance/ekv_controls.py) with the cheap subset flag for per-batch use.
- D-05 [W2] Governance record: enumerate drift/schema validator baselines into
  explicit whitelists (fail-closed beyond); reconcile CURRENT_STATE.last_session_id
  ↔ SESSION_LOG tail; migration-456 formal disposition (restore-from-git-history to
  _archive/ if recoverable, else RECORDED-IRRECOVERABLE note); CAPABILITY_MANIFEST
  scope amendment (extend to data assets or amend §C-2 claim) · F-94/95/79/81.
- D-06 [W2] Build-state honesty: asset_throughput invariant — state='lit' with
  non-empty last_error is a contradiction; add detector to D-04 battery (F-141);
  document as §N.8 instance.
- D-07 [C] Dead-path census (CL-02): every fallback_reason/'no such table' literal
  checked against information_schema; wire nakshatra/dasha-systems/tantric/
  saptavargaja consumers or file precise gap notes (F-04/05/22/61) — wiring PRs
  route to A (serving) with D providing the census.
- D-08 [C] Pointer integrity (CL-11): recover_via derived from target schema;
  required-args on drill/tri_plane pointers (F-09/17/18/43/123); implementation in
  A's files → D writes the failing tests FIRST, A makes them pass (cross-stream
  TDD handshake via coordination markers).

### STREAM E — SAṄGAMA (integration, release, production sync) — SINGLE-WRITER on main
OWNS: merges, deploys, rebuilds, rollbacks. No source authorship.

- E-01 [C] Merge queue in dependency order: W0 singles fast (small diffs, immediate);
  then kernel (A-09 core) before its dependents; B engine fixes before E-03 rebuild;
  C-01/02/03 as one batch. Rebase-based, never merge-commit chains; conflicts beyond
  mechanical → PRATINIDHI ruling. Branch-protection livelock → PŪRṆATĀ precedent
  (admin-merge) ONLY on PRATINIDHI ruling, logged.
- E-02 [C] Deploy per batch: push main → pipeline deploys (migrate.ts runs; §N.4:
  verify migrations ACTUALLY applied via _migrations_applied delta) → verify
  catalog_version sha == main tip → run cheap-control subset + the batch's lane
  probes → post EKV markers. Any red: rollback (revert merge), quarantine lane,
  continue queue.
- E-03 [W2] Gochara rebuild both charts (after B-01/02/03 merged+deployed): canary
  event-class first (marriage), assert nodal terms appear in native marriage window
  (F-52's own reproduce_cmd flipped to expect-present), then full dispatch; 35-min
  stall watch (S7/SM-R-4 discipline); if still running at hand-back, mark
  DATA-REBUILD-IN-FLIGHT honestly (gate treats P3 as CODE-LIVE, rebuild pending).
- E-04 [W3] Morning battery: all 25 T1 reproduce_cmds + all W0 lanes + 20% random
  sample of remaining findings + full CL-00 27 · feeds ekv_gate.py verify.
- E-05 [C] End-of-night: origin/main == deployed sha; unfinished lanes → branches
  pushed with HANDOFF.md each; ledger closed with honest per-lane states.

## §3 THE SWARM — ROLES, MODELS, EFFORT (cost-optimized)

Principle: sonnet builds, haiku sweeps, opus judges. Opus is spent ONLY where a wrong
call is expensive to reverse (rulings, merge arbitration, wave verdicts). Never Fable.

| Role | Session/Agent | Model | Effort | Notes |
|---|---|---|---|---|
| SŪTRADHĀRA (conductor) | 1 session | sonnet | high | Seeds ledger, leases, spawns streams, sequences waves, sole writer to CAMPAIGN_COORDINATION. |
| PRATINIDHI (native surrogate) | 1 standing session | **opus** | high (self-escalate on irreversible) | The human-replacing agent: doctrine rulings, scope calls, merge arbitration, deploy risk, DB-write sign-offs. Every ruling = numbered EKV-R entry with rationale + the CLAUDE.md/§0 rule it applied. Bounded: cannot change §0. |
| SENTINEL (verifier+watchdog) | 1 standing session | sonnet | high | FM-09 enforcement: re-runs gates, samples reproduce_cmds behind every VERIFIED marker (15%), hang-watch (35-min stall), cost meter (§6), stuck-stream nudges. Escalates disputes to PRATINIDHI; **wave verdicts co-signed by an opus subagent it spawns** (decider≠verifier both ways). |
| Stream leads A–E | 5 sessions | sonnet | high | Own stream ledger + intra-stream file-lease board; review every diff vs lease before commit. |
| Builders | 2–6/stream, ephemeral | sonnet | medium | One worktree each (§4). TDD: failing exit-test first. |
| Census/mechanical | 1–3/stream | haiku 4.5 | low | Sarvatra site-lists, grep sweeps, evidence filing, boilerplate from an approved template. |
| Test authors | 1–2/stream | sonnet→haiku | medium→low | Sonnet writes the first of a family; haiku replicates the pattern. |
| Verify-before-merge | 1/stream | sonnet | high | Runs lane exit-test + relevant reproduce_cmds INSIDE the lane worktree pre-handoff. The anti-rework shift-left. |

Intra-session mechanics: leads use the Agent tool with `isolation:'worktree'` for
builders; parallel where files disjoint, serialized via lease board where shared.
Effort passed per-agent. Background agents preferred; leads never idle-poll.

## §4 WORK ISOLATION — HIGHEST-IMPORTANCE RULES

1. **Branch topology:** all work from `origin/main` tip at T0. Branches:
   `ekv/<stream>-<lane>` (e.g. ekv/a-09-sara-kernel). NO work on main, NO work on
   audit/paripurna2-evidence (read-only corpus; conductor pushes it to origin at T0
   as backup).
2. **Worktrees:** every builder in its own worktree
   `.claude/worktrees/ekv-<stream>-<lane>`. Leads may batch trivial W0 singles in
   one worktree sequentially. The stale worktree fleet from prior campaigns is
   UNTOUCHABLE.
3. **Path leases:** conductor seeds `00_ARCHITECTURE/briefs/ekavakyata/LEASES.json`
   from §2's OWNS map. A diff touching an unleased path fails the lane (verifier
   greps `git diff --name-only` vs lease before every commit). Cross-stream needs →
   marker request → conductor re-leases explicitly. Known hot files pre-assigned:
   registry_bridge.ts + response_budget.ts = A-09's single senior builder ONLY;
   kala_views/* = A (C requests via marker for anything there — C-05 will);
   tool_name_bridge.ts = A-02 then frozen.
4. **Coordination writes:** one file per writer, ALWAYS. Per-stream ledger
   `briefs/ekavakyata/LEDGER_<X>.md` (lead-only). CAMPAIGN_COORDINATION.md
   (conductor-only, via coord-edit worktree, rebase-retry loop). Marker grammar:
   `EKV-<lane>-{CLAIMED|BUILT|VERIFIED|MERGED|LIVE|BLOCKED|HANDOFF}` + ISO time.
   Manifest-style shared JSON (leases, gate manifest) written ONLY by its named
   single writer (conductor / E respectively). This is the PP2 write-race lesson.
5. **DB:** read-only everywhere except C-01/C-02 migration + C-04's lifecycle smoke
   (real mechanism, cleaned up) + E-03 rebuild dispatch. Port 5433. Any other write
   intent → PRATINIDHI, logged, or refused.
6. **Commit hygiene:** small commits per lane, `ekv(<lane>): <what>` +
   `Co-Authored-By:` house line; push lane branches early and often (crash safety);
   PRs by lead; merges by E only.

## §5 CADENCE, DEPENDENCIES, DEGRADE ORDER

T0 conductor: fetch, backup-push audit branch, seed briefs/ekavakyata/ (ledger, LEASES,
gate manifest skeleton), spawn PRATINIDHI+SENTINEL, launch streams A–E.
T0+15m: all W0 lanes CLAIMED. W0 target: BUILT+VERIFIED ≤2h, E merges/deploys as they
land (don't batch W0 — each is independent).
Then: A-09 kernel interface freeze (A posts EKV-KERNEL-API-FROZEN marker — B-08, A-14,
A-16 consume it). B engine lanes parallel throughout. E-03 rebuild after B W1 merged.
W3 lanes ride the kernel. E-04 battery from T0+7h or when queues drain.

DEGRADE ORDER (cost/time pressure — cut from the bottom, never thin verification):
1. W0 (all) → 2. A-09 on assess+judgment+kala core + A-08 spine → 3. B-01/02/03 +
E-03 canary → 4. A-07 charter + A-10..A-13 + A-15/17 → 5. P5 gate pieces (A-06 done
in W0; A-14) → 6. B-08 ranker → 7. C-04/05 economy → 8. D-05..08 (D-01..04 are not
cuttable — they're the anti-rework rails) → 9. A-18, B-06/07, remaining GAP-tool
composition conversions.

BLOCKED protocol: 2 real attempts → post EKV-<lane>-BLOCKED with evidence → SENTINEL
triages → PRATINIDHI rules (reroute/rescope/park). No agent burns >30min silent on a
blocker (FM-27 discipline).

## §6 BUDGET (FM-28: nets, not stopwatches)

Targets: A $90 · B $45 · C $20 · D $30 · E $35 · conductor $15 · PRATINIDHI $20 ·
SENTINEL $25 ≈ **$280 target · warn $340 · hard cap $420.** SENTINEL meters hourly
(ccusage or session cost lines) and posts EKV-COST markers; at warn, degrade order
activates; at cap, E lands what's verified, everything else → HANDOFF branches.
Speed levers already encoded: haiku for sweeps, medium-effort builders, one senior
builder on the hot files instead of merge-conflict churn, W0 singles merged
immediately for early wins.

## §7 MECHANICAL GATE — ekv_gate.py (no prose completion)

`/Users/Dev/shad_overnight/ekv_gate.py` (built tonight alongside this plan). Manifest
`briefs/ekavakyata/ekv_manifest.json` (E is sole writer). Per lane: {lane, branch,
merged_sha, files_touched, lease_ok, exit_test_path, exit_test_result,
live_probe_evidence (existing non-empty JSON), wave}. `verify --wave N` exits 0 only if
every claimed lane: merged_sha ancestor of origin/main · lease_ok · exit test recorded
PASS · live evidence exists · AND deployed catalog_version sha == origin/main tip ·
AND CL-00 cheap subset last-run PASS. Terminal marker
`RUN-TERMINAL: SESSION-EKAVAKYATA-NIGHT1-COMPLETE` may post ONLY after verify exit 0
for waves 0–1 minimum + SENTINEL's independent re-run + PRATINIDHI countersign ruling.

## §8 FAILURE NETS (inherited, binding)

FM-09 evidence-not-assertion · FM-27 no silent stalls · FM-28 envelope-not-stopwatch ·
S7/SM-R-4 35-min build-stall rule (E-03) · PP2 write-race → one-file-per-writer ·
PŪRṆATĀ livelock precedent (admin-merge only by ruling) · §N.4 migration-verified ·
PR#1287 counting rule · deploy red → revert-first, diagnose-second (revert is always
safe; forward-fix needs a ruling). Crash of any stream session: SENTINEL detects
(ledger heartbeat stale 20min) → conductor relaunches with same kickoff — worktrees +
pushed branches + ledger make every session resumable. Conductor crash: SENTINEL holds
the resume duty (mirror instruction in its kickoff).

*End of plan. The corpus is the spec; the gate is the judge; the swarm is the hands.
Ekavākyatā — one instrument, one voice, by morning as much of it as honesty allows.*
