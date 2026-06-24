---
artifact: L5_MIMAMSA_MASTER_ACTIVITY_LIST_v1_0.md
canonical_id: L5_MIMAMSA_MASTER_ACTIVITY_LIST
version: 1.0
status: CURRENT — the end-to-end execution checklist to get L5 Mīmāṃsā ready
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The single ordered activity list that turns the L5 design corpus into a built, sealed, supreme layer.
  Every activity traces to a decision/artifact already authored. Organized into phases (P-1 → P8) with
  dependencies, owners (Cowork-plans / Antigravity-builds), and gates. This is the "what do we actually
  DO" master list. Numbers/specs still marked [build-set] are deliberately deferred to P2.
corpus_consumed:
  - L5_MIMAMSA_INDEX (hub) · VISION · CAMPAIGN_PLAN · CONTRIBUTION_CONTROL · LEARNING_PROPAGATION
  - ELEVATION (lifecycle + external families + matrix + decisions) · GAP_ANALYSIS (5-quality gaps)
  - CALIBRATION_COMPARISON_MODEL (context-aware scorecard + manifestations) · GROUND_AUDIT brief
legend: "Owner: [CW]=Cowork plans/authors · [CC]=Claude Code in Antigravity builds · [NATIVE]=native action/gate"
---

# L5 Mīmāṃsā — Master Activity List (everything to get ready)

> Read top to bottom. Phases are mostly sequential; some activities parallelize (noted). Each phase ends
> in a **GATE** that must pass before the next begins. "✅ done" marks what this design session already
> completed.

---

## PHASE P-1 — DESIGN (mostly DONE this session) ✅

| # | activity | owner | status |
|---|---|---|---|
| P-1.1 | Vision/charter (6 pillars; n=1 honesty) | CW | ✅ VISION |
| P-1.2 | Campaign plan + per-asset specs + corrected DAG | CW | ✅ CAMPAIGN_PLAN |
| P-1.3 | Contribution-control framework (toggles, parity, conversational defaults) | CW | ✅ CONTRIBUTION_CONTROL |
| P-1.4 | Learning-propagation architecture (overlay, dedup, bounds, two-key lock) | CW | ✅ LEARNING_PROPAGATION |
| P-1.5 | Elevation (deterministic overlay, lifecycle, no-LEL, external-family matrix, neg-controls) | CW | ✅ ELEVATION |
| P-1.6 | Supreme-product gap analysis (5 qualities) | CW | ✅ GAP_ANALYSIS |
| P-1.7 | Context-aware calibration comparison model (scorecard + alternate manifestations) | CW | ✅ CALIBRATION_COMPARISON_MODEL |
| P-1.8 | All decisions closed (V/C/P/E/EL + lifecycle + manifestation) | NATIVE | ✅ ELEVATION Part F |

**Remaining P-1 (small, do before build):**
- [ ] **P-1.9 [CW]** — Author the ASSET-SPEC pack: a per-`mi_*` build spec hardened to the latest decisions
  (full frozen bundle incl. `manifestation_set[]`; scorecard columns; overlay tables; registry rows).
- [ ] **P-1.10 [CW]** — Register the 8 L5 design artifacts in the governance layer (CAPABILITY_MANIFEST +
  CANONICAL_ARTIFACTS) when they flip DRAFT→CURRENT (after the audit reconciles them).

**GATE P-1:** design corpus complete + internally consistent. ✅ (pending P-1.9 spec pack)

---

## PHASE P0 — PRECONDITIONS (native-gated; not L5 work, but L5 can't start without them)

| # | activity | owner | gate |
|---|---|---|---|
| P0.0 | **[ACTIVE BLOCKER 2026-06-23] Rebuild `ph_pratikara` from corrected `kala_convergence`** — the all-Jupiter bug (hardcoded `transit_trig.get('planet','Jupiter')` fallback) stamped all 660 convergence rows + every L4 mitigation as Jupiter-afflicted. Fix committed (worktree `worktree-agent-a166a6c0b42621818`): now looks up active mahadasha lord from `chart_dashas`. Rebuild in-flight (PID 62821). After it commits: verify ≥3 distinct lords → rebuild `kala_obstruction` (ka_vighnakara) → rebuild `ph_pratikara` → DB-state regression. **L4 CANNOT SEAL until ph_pratikara is rebuilt.** L3 seal NOT reopened (engine logic correct; only attribution was wrong). | CC/NATIVE | L4-seal precondition |
| P0.1 | **Close L4 Phala** — produce `L4_PHALA_CLOSE_v1_0.md`; seal `phala_pramana` column contract (after P0.0) | NATIVE/CC | L5 input contract is frozen |
| P0.2 | Update `CURRENT_STATE` to reflect L4 closed → L5 next (it's stale at v5.90) | CC | state truth restored |
| P0.3 | Confirm `PROD_DATABASE_URL` secret set; prod == main; CI green | CC | build env sane |

**GATE P0:** L4 sealed, `phala_pramana` contract final, env verified. **L5 cannot open until this passes.**

---

## PHASE P1 — GROUND-TRUTH AUDIT (read-only; the reality check)

Run the already-authored `ANTIGRAVITY_PASTE_L5_MIMAMSA_GROUND_AUDIT.md`.

| # | activity | owner |
|---|---|---|
| P1.1 | Live-registry reconciliation of the 6 `mi_*` rows (real depends_on vs proposed corrected DAG) | CC |
| P1.2 | Prod table inventory — which `mimamsa_*` exist, which empty, column shapes | CC |
| P1.3 | Deep per-file audit of ~12 legacy `brahmagyan/mimamsa/` files vs frozen contract (reuse/refactor/rewrite verdict each) | CC |
| P1.4 | Migration inventory + safe next number (check BOTH migration dirs) | CC |
| P1.5 | Extract the authoritative `phala_pramana → mi_bhavisya` column mapping from sealed `ph_pramana.py` | CC |
| P1.6 | Test inventory (`tests/l5/`) — what to keep vs discard | CC |
| P1.7 | Write `L5_MIMAMSA_GROUND_AUDIT_v1_0.md` + build-readiness verdict (wire-it vs build-it) | CC |

**GATE P1:** every design assumption either confirmed or flagged for revision; the real schema is known.

---

## PHASE P2 — HOLISTIC RECONCILE + NUMBERS (Cowork + native; harden the design to reality)

| # | activity | owner |
|---|---|---|
| P2.1 | Reconcile vision/specs against the audit; revise the corrected DAG; finalize per-asset schemas | CW |
| P2.2 | Set the deferred NUMBERS: P1 per-layer caps (CAP_layer), EL1 tier prior-weights, min-n gate value, literal-vs-alternate manifestation weights, two-key high-confidence threshold | NATIVE+CW |
| P2.3 | Finalize the signal-family catalog admitted at v1 (X-PHOTO, X-GEOMAG, T-NAKPADA + neg-control battery) with citations + prior weights | CW |
| P2.4 | Native ratifies the corrected DAG + the numbers | NATIVE |

**GATE P2:** specs + numbers ratified; nothing left as "[build-set]". Flip design artifacts DRAFT→CURRENT.

---

## PHASE P3 — DATA LAYER (migrations + registry; the foundation)

| # | activity | owner | notes |
|---|---|---|---|
| P3.1 | Migrations: the 6 `mimamsa_*` core tables reconciled to spec (predictions/calibration/multipliers/qa_eval/export_log + life_events view) | CC | surgical, next free number |
| P3.2 | Migrations: the **4 overlay tables** (`mimamsa_fact/signal/convergence/anchor_adjustment`) | CC | LEARNING_PROPAGATION §3 |
| P3.3 | Migrations: the **signal-family registry** + **per-user preference store** + **contribution channel** tables | CC | CONTRIBUTION_CONTROL + ELEVATION C |
| P3.4 | Migrations: the **prediction-bundle** schema (frozen bundle incl. `manifestation_set[]`, `driving_signals[]`, `base_rate`, `emitted_at`) + **scorecard** columns (timing/magnitude/domain/falsifier/manifestation + composite + recorded-channel) | CC | CALIBRATION_COMPARISON_MODEL |
| P3.5 | Fix the 6 `mi_*` registry rows: corrected `depends_on` (→ `phala_*`), chart-scoped `count_sql` ($1), multi-chart-keyed | CC | seed + manifest |
| P3.6 | Register all `mimamsa_*` tables with `drift_detector` + `schema_validator` (integrity substrate) | CC | GAP RL-5 |

**GATE P3:** migrations applied to prod (via push-to-main auto-migrate), ledger-reconciled, tables exist + registered.

---

## PHASE P4 — DETERMINISTIC COMPUTE ENGINE (the 6 writers, frozen contract)

Each is a `@register('mi_*')` `WriterBase` subclass; delete-then-insert idempotency; never commits ctx.db_conn; `rows_inserted`; service dir COPY'd in Dockerfile.

| # | activity | owner | implements |
|---|---|---|---|
| P4.1 | `mi_jivanaghatana` — LEL load + provenance/leakage tagging + held-out partition | CC | clean-evidence vault |
| P4.2 | `mi_bhavisya` — mirror `phala_pramana` into the **full frozen bundle**; generate `manifestation_set[]` (hybrid: classical-cited spine + citation-gated LLM additions); base-rate lookup | CC | prediction registry |
| P4.3 | `mi_pramana` — the **deterministic matcher** (many-to-many candidate match) + the **multi-dimensional scorecard** (incl. manifestation dimension, falsifier-as-judge) + reliability curves (base-rate-adjusted, null-model-checked, held-out-gated) | CC | calibration engine |
| P4.4 | `mi_gunanaka` — learned-weight register (LL.1 + structure for LL.2–8) + the **reverse-channel overlays** (bounded + evidence-scaled) in **suggestion mode** | CC | weights + reverse channel |
| P4.5 | `mi_pariksha` — **per-dimension + per-channel attribution** (LL.9 miss-tracing); negative-control battery harness | CC | self-exam |
| P4.6 | `mi_vistara` — export-integrity ledger | CC | export log |
| P4.7 | `mi_kula` ⭐ — signal-family registry (tier-tagged families + citations + negative-control battery) | CC | the controllable matrix (promoted asset) |
| P4.8 | `mi_adhilepa` ⭐ — the 4 overlay/adjustment tables (bounded, evidence-scaled, two-key-locked) | CC | reverse-channel surface (promoted asset) |
| P4.9 | `mi_seva` ⭐ — SERVICE: serve-time effective-value apply + contribution-control toggles + transit-current binding (+ owns `mimamsa_preferences`) | CC | serve service (asset_kind: service) |
| P4.10 | `mi_abhilekha` ⭐ — SERVICE: journal ingestion + due-sweep + debounced LEL-update recompute trigger | CC | journal/re-sync service (asset_kind: service) |
| P4.11 | The **frozen formulas** (versioned), **pinned external-data snapshots** (geomag/sunspot/ephemeris) | CC | GAP D-2/D-3 |

> **Asset count corrected (pre-build review):** L5 = **8 data + 2 service = 10 assets** (was 6). See
> `L5_MIMAMSA_ASSET_ARCHITECTURE_v1_0.md` for the table-ownership map, corrected DAG, and registry-seed
> spec. The 2 services (`mi_seva`, `mi_abhilekha`) are callable/triggered, not part of the build-DAG spine.

**GATE P4:** all 6 writers import clean (pkgutil), run via click-Build, populate their tables for `482012f1`.

---

## PHASE P5 — SERVE PATH + CONTRIBUTION CONTROL (where the user meets it)

| # | activity | owner | implements |
|---|---|---|---|
| P5.1 | Shared **contribution-control module** in the retrieval registry: channel registry + resolver (per-request → saved default → system-ON) | CC | CONTRIBUTION_CONTROL §4 |
| P5.2 | **Two serve-time gates**: `lel_citation` (suppress literal LEL facts when off) + `learning_influence` (read base vs effective) | CC | CONTRIBUTION_CONTROL §5 |
| P5.3 | **Effective-value read path** — cached `effective` views joining overlay, gated by `learning_influence`, refreshed per calibration session | CC | LEARNING_PROPAGATION + GAP P3 |
| P5.4 | **Per-family + tier-group + soundness-basis** controls (the segregated matrix) | CC | ELEVATION C |
| P5.5 | **Conversational defaults**: on MCP/convo start with unknown prefs, the assistant ASKS, then uses answers as session defaults | CC+CW | native C2 ruling |
| P5.6 | MCP optional tool args + **parity-gate extension** (`parity_check.ts` asserts portal==MCP controls) | CC | CONTRIBUTION_CONTROL §4 |
| P5.7 | `contribution_state` response metadata + provenance/"why" endpoint | CC | GAP S-2/S-4 |
| P5.8 | Wire L5 calibration view into Whole-Chart-Read (B.11) | CC | retrieval L5_mimamsa |
| P5.9 | **Transit-current binding** — serve path computes against today's sky/geomag, not a stale snapshot | CC | GAP C-1 |

**GATE P5:** a query through portal AND MCP honors all toggles identically (parity CI green); transit-current works.

---

## PHASE P5.5 — THE PREDICTION JOURNAL (the differentiator + evidence engine)

| # | activity | owner | why |
|---|---|---|---|
| P5.5.1 | Journal surface: stage due predictions; native answers "did this happen?" (portal + MCP) | CC+CW | GAP S-1 — the highest-leverage feature |
| P5.5.2 | Ingestion: journal answers become LEL events (with provenance tags) → trigger the LEL-update recompute | CC | grows the evidence base through use |
| P5.5.3 | **Prediction-due sweep** (background): detect windows closed + candidate evidence; surface for journaling | CC | GAP C-3 |
| P5.5.4 | LEL-update lifecycle: debounced (session-close + manual force) L5-only incremental recompute; freshness marker | CC | ELEVATION A.2 |

**GATE P5.5:** logging a journal answer grows the LEL and re-syncs L5 (L5-only, no L1–L4 rebuild); freshness visible.

---

## PHASE P6 — VALIDATION HARNESS (the honesty proofs; many are SEAL GATES)

| # | activity | owner | gate? |
|---|---|---|---|
| P6.1 | **Reproducibility test** — run L5 twice, assert byte-identical overlays + scorecards | CC | SEAL |
| P6.2 | **OFF==baseline test** — `learning_influence` off == pure L1–L4, byte-for-byte | CC | SEAL |
| P6.3 | **No-LLM-in-L5 test** — CI greps `mi_*` writers; zero generative-LLM calls | CC | SEAL |
| P6.4 | **Negative-control battery** — all NC-* score ~null; non-null BLOCKS seal/promotion | CC | SEAL (E3) |
| P6.5 | **Double-count path test** — a finding on one signal adjusts the dependent L4 prediction exactly once | CC | SEAL |
| P6.6 | **No-L0-touch test** — no overlay/edge targets any `bg_*` | CC | SEAL |
| P6.7 | **Pre-registration admissibility** — only pre-window-frozen predictions count toward calibration | CC | SEAL (HC-5) |
| P6.8 | **Falsifier-as-judge** — no `confirmed` without the frozen falsifier met; **no post-hoc manifestation widening** | CC | SEAL |
| P6.9 | **Insufficient-evidence honesty** — below min-n, reports "insufficient", never a number | CC | SEAL (B.12) |
| P6.10 | **Bounds + evidence-scaling** + **two-key lock** enforced (real impact only on gate-passed AND high-confidence) | CC | SEAL |
| P6.11 | **Meta-calibration** report (reliability curves / Brier / ECE) + **discriminative-validity headline** | CC | GAP HC-2/HC-3 |
| P6.12 | **Kill-switch + drift-alert** behavior (suspend degrading family; alert on learned-vs-classical divergence) | CC | GAP RL-4 |
| P6.13 | **Degenerate-distribution guard** — halt + flag if any computed attribution column (planet, house, signal-family, manifestation channel, etc.) collapses to a single value across all rows where diversity is expected. Cheap deterministic tripwire. | CC | SEAL (lesson from the 2026-06-23 all-Jupiter `kala_convergence` bug — a silent hardcoded fallback that only surfaced via distribution check; this guard catches that class at build time) |

**GATE P6:** every SEAL test passes against the LIVE prod build (not the branch).

---

## PHASE P7 — RETRIEVAL + WHOLE-CHART INTEGRATION

| # | activity | owner |
|---|---|---|
| P7.1 | `L5_mimamsa` retrieval primitives lit (tools/resources/prompts) in the canonical registry | CC |
| P7.2 | Calibration + manifestation-profile views exposed to the synthesis LLM via retrieval | CC |
| P7.3 | Confidence-ladder + provenance available at serve time for the two-key lock | CC |

**GATE P7:** the synthesis LLM can pull the deterministic L5 ingredients (overlay, scorecard, families, confidence) through retrieval, identically portal+MCP.

---

## PHASE P8 — CLEAN SEAL

| # | activity | owner |
|---|---|---|
| P8.1 | **Live-deployment guard**: assert `mimamsa == 6 lit` on the running prod API (`/api/cockpit/stats?chart_id=482012f1`), never the branch | CC |
| P8.2 | Red-team pass (IS.8(b) macro-close cadence) | CC |
| P8.3 | Write `L5_MIMAMSA_CLOSE_v1_0.md` with live-prod endpoint JSON evidence + all SEAL-gate results | CC |
| P8.4 | Flip `CURRENT_STATE`; register L5 artifacts CURRENT in CAPABILITY_MANIFEST | CC |
| P8.5 | Confirm the whole L0→L5 arc is complete (the instrument's top layer is live) | NATIVE |

**GATE P8 (FINAL):** L5 lit on live prod, every SEAL test green, sealed + documented. **L5 is ready.**

---

## Critical path (the dependency spine)

```
P0 (close L4) → P1 (audit) → P2 (reconcile + numbers, NATIVE ratify)
   → P3 (migrations/registry) → P4 (6 writers) → P5 (serve + control)
   → P5.5 (prediction journal) → P6 (validation/seal gates) → P7 (retrieval) → P8 (seal)
```

**Hard blockers:** P0 (L4 must close) gates everything. P2 native ratification gates the build. The P6
SEAL gates — especially negative-controls-null (E3), OFF==baseline (RL-2), reproducibility (RL-1),
pre-registration (HC-5), falsifier-as-judge — gate the seal.

## Parallelization notes
- Within P4, the 6 writers parallelize where file-disjoint (per the proven autonomous-wave model);
  the DAG order (`mi_jivanaghatana` → `mi_bhavisya` → `mi_pramana` → `mi_gunanaka`; `mi_pariksha`/`mi_vistara` side) constrains it.
- P5 serve-path + P5.5 journal can develop alongside P4 once P3 tables exist.
- The whole build (P3→P8) can run as ONE autonomous Antigravity session (isolated worktree, Conductor
  + swarm) per the L4 D47 precedent — one kickoff, env self-provision, maximal parallel.

## What's deferred to build (deliberately)
- Exact numbers: per-layer caps, tier prior-weights, min-n gate, manifestation weights, high-confidence
  threshold (all set + native-ratified in P2).
- LL.2–LL.10 machines: designed-in (registry-ready), switched on later as evidence grows (core-first, V1).

---

*End of L5_MIMAMSA_MASTER_ACTIVITY_LIST v1.0. Phases P-1 (design, ✅ done) → P0 (close L4) → P1 (audit) →
P2 (reconcile + numbers) → P3 (data) → P4 (6 deterministic writers) → P5 (serve + contribution control) →
P5.5 (prediction journal) → P6 (validation seal gates) → P7 (retrieval) → P8 (clean seal). The design is
done; the path to ready is gated, mostly autonomous, and blocked only on L4 closing first.*
