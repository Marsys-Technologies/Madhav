---
artifact: PROGRAM_LEDGER_AND_ELEVATION_ROADMAP
canonical_id: PROGRAM_LEDGER_v1_0
version: 1.1
status: LIVING — supersedes scattered per-campaign residual lists as the single "what is actually open" document
created: 2026-07-27
author: Fable (Cowork), from an exhaustive sweep of the full llm_consumption_audit corpus
  (~140 non-shard documents) + live spot-verification against the working tree
method: >
  Three parallel deep-read agents swept (a) the five recent campaign close-reports + the
  consumption register, (b) every defect register and deferral queue including the elevation
  register, UAT-DARPANA register, post-remediation CR register, overflow queues, dark-corpus
  report and CI-state ledger, (c) the doctrine-wave reports, stream closes, and forward design
  documents. Their claims were then SPOT-VERIFIED against live code and file state. Four checks
  were run; three of the sweep's most alarming claims proved FALSE. §0 is therefore the most
  important section of this document.
changelog:
  - "v1.1 (2026-07-28): PARIŚODHANA campaign closed. Every Tier-1/Tier-2 item in §1 below now
    has a live-evidenced final disposition — see PARISHODHANA_RECONCILIATION_v1_0.md v1.1 §1/§6
    (the authoritative row-by-row table) and PARISHODHANA_REPORT_v1_0.md (the close report) for
    full detail, evidence, and PR references. Net: 21 item-groups were ALREADY-FIXED (register
    drift, now annotated in their source registers); of the remainder, most LIVE-OPEN items were
    fixed and deployed this campaign (12 PRs); a handful are PARKED-HONEST as genuinely
    out-of-scope (L1/L2/L4 writer changes, capability-additions, native-gated decisions) or
    still-open after two fix attempts (holistic_bundle's residual self-call bug). This document's
    §1 table itself is NOT rewritten row-by-row (that duplication is exactly the drift class this
    campaign exists to prevent) — treat PARISHODHANA_RECONCILIATION_v1_0.md as authoritative for
    current status of every item listed below; this ledger's §1 reflects the pre-campaign sweep
    and is retained for historical/audit trail."
---

# MARSYS-JIS — Program Ledger & Elevation Roadmap

## §0 — Read this first: the registers cannot be trusted in either direction

The sweep surfaced roughly **90 items** described somewhere in the corpus as open, parked,
deferred, or blocked. Before writing any of them down as fact, I spot-checked the four most
alarming against the live tree. **Three of the four were already fixed and the documents had
never been updated:**

| Sweep claim | Live check | Verdict |
|---|---|---|
| "CR-87 CRITICAL: one native's natal constants (`_NATIVE_JANMA_NAK_IDX=24`, `_NATIVE_LOCATION`=Bhubaneswar) hardcoded into SHARED convergence-engine code — contaminates every other native's readings. Highest-severity un-dispositioned item found." | `ka_sangam.py:111` carries an explicit **"CR-87 fix"** comment; a dedicated regression test `tests/test_cr87_native_chart_context.py` exists with a `_FORBIDDEN_TOKENS` guard asserting zero hits for those symbols | **FALSE ALARM — fixed, guarded** |
| "AS-4 LCA-2 CRITICAL: `/api/chat/consult` references the retired `reports` table; consult is broken against the deployed schema; no later campaign touches it." | `consult/route.ts:317` reads *"The prior code unconditionally SELECTed `domain, title, version FROM reports`"* — past tense, i.e. remediated | **FALSE ALARM — fixed** |
| "The register is still `status: LIVING`, changelog v1.0, **zero** `ADDRESSED` strings — three campaigns assert an unverifiable fact." | `status: ADDRESSED-v1.2`, 8 `ADDRESSED` occurrences. (The agent misread the `version: 1.0` field, which is the artifact's schema version, not its disposition.) | **FALSE ALARM — annotated correctly** |
| "`SHODHANA_REPORT_v1_0.md` ends at §10 despite later reports citing §11/§12/§13 as delivered evidence." | §11 (tally reconciliation), §12 (MC-001 re-verification), §13 (Decision-2 close) all present at lines 271/380/446 | **FALSE ALARM — sections exist** |

**This is the actual state of the program, and it is more important than any individual item.**
The post-remediation register itself names the cause: a confirmed recurring drift class —
*"ships-but-register-never-flips"* — already observed in ≥3 instances (CR-56, CR-54/59,
CR-16/61/64/68). Registers **accumulate**; nothing sweeps them when a fix lands elsewhere. The
elevation register says so explicitly in its own closing disposition: *"this register only
ACCUMULATES — no item is closed here."*

The consequence is uncomfortable and worth stating plainly: **I told you the program had "zero
open campaigns and three small tickets." That was wrong** — it was true of the *recent* campaign
chain and false of the corpus as a whole. But the opposite reading is equally wrong: the ~90
items are not 90 real defects. **Nobody currently knows which is which**, and no document in the
repo can tell you, because document-state and live-state have measurably diverged in both
directions.

**Therefore the clean sweep you asked for cannot begin with fixing. It must begin with
reconciliation** — a verify-first pass that converts every claimed-open item into a
live-evidenced disposition. That is Phase A of the campaign in §3, and it is the single highest-
value thing left to do, because it is the precondition for trusting anything else in this file.

Everything below is therefore labelled by **evidence grade**:
**[LIVE]** = verified against running code/production in this session ·
**[DOC]** = asserted by a document, unverified ·
**[DESIGN]** = a design that was authored and never built (these are reliable — an unbuilt design
is not subject to drift).

---

## §1 — The residual ledger

### Tier 1 · Structural gaps that are certainly real (design-level, not drift-prone)

| # | Item | Evidence | What it is |
|---|---|---|---|
| T1-1 | **γ flagship discoverability (R-38)** — a naive consumer asking "how is my wealth?" never reaches the planner at all; even a tool-searching agent cannot discover `dossier` because the live `tool_search` index does not surface it. 3 of 5 charter criteria NOT MET; `flagship_self_verified: false`. | [DOC] γ close §2, corroborated by SAMĀPANA's 11/13 | **The single highest-leverage open residual in the corpus, and it is owned by no active design.** Two named remedies: make `dossier` prominent in the served catalog/`tool_search` index; and/or have `assess_wealth`/`judgment_query` inline dossier's coverage. |
| T1-2 | **Dark corpus: the instrument serves ~6–8% of what it computes.** Wealth 11,755 of 12,450 concepts dark (5.58% bright); career 11,400 of 12,455 (8.47%). ~98% of the darkness sits behind two tools: `ganita_chart_facts_get` (~10.3k) and `bodha_signals_get` (~1.2k). | [DOC] DARK_CORPUS_REPORT, 21/21 replay, both flagship domains | Measured, honest, and **never re-measured against the final head**. Only 1 of 2 canonical charts and 2 of 4 domains were ever measured. Marked Ω7 PARKED-HONEST. |
| T1-3 | **Ω8 floor wiring (5 parked sub-items)** — `divisional_facts` floors are D1-only/thin (wealth=D2 only, should be D1/D2/D9/D11); `ashtakavarga_scan` is D1-only (per-varga AV = **504 concepts/domain**); `special_lagna_read` limited to `['indu','sree']` (should be 7 lagnas + 70 sahams + Upapada = **78 concepts**); four floor primitives unregistered (`argala_read` **1044/domain**, `dispositor_closure_read` **607/domain**, `mechanism_read`, `cross_ayanamsha_agreement`); and both consumer copies (TS `registry_data.ts` + DB seed migration 440) are hand-synchronized with **no CI gate** to stop drift. | [DOC] OMEGA8_FLOOR_WIRING_PARKED_HONEST | This is the **mechanical cause** of a large share of T1-2. The floors that would guarantee the dark concepts get served are written and unwired. Ownership was itself disputed (γ said blocked-on-α; α said it was in γ's manifest). |
| T1-4 | **KP system half-built and fully dark (CR-75)** — no KP sub-lord engine exists at all; the 249-fold sub-lord division, the cornerstone of KP, is absent. Explicitly excluded from two consecutive waves (D-5 and GOCHARA-SWEEP-2.0). | [DOC] post-remediation §H, ELEVATED, native-flagged | A whole missing capability, not a defect. No campaign has ever claimed it. |
| T1-5 | **Calibration chain never closed** — `mimamsa_outcome_record` has no table and no live write path; `update_calibration()` is dead code against a column that doesn't exist; `mimamsa_calibration` = 0 rows; all multipliers `n_observations=0`. L5 has never ingested an outcome. Everything serves `calibration_state: structural_prior`. | [DOC] REPORT_D4B §0/§3, CR-79 | **Correctly deferred, not neglected** — B-1's bakeoff honestly returned NO_WINNER, so the one-shot backfill never fired. The unlock path is: accrue real prospective outcomes → build the write surface against real requirements → B-2/B-3. |
| T1-6 | **Sarvatobhadra vedha grid has zero rows** (migrations 140/144 empty); the shipped implementation is an honest algorithmic approximation flagged `uncited_extension=true`. | [DOC] REPORT_D-5 §2/§4/§5 | The arc's self-named *"classical centerpiece"* is the one primitive with no real classical data behind it. |
| T1-7 | **MSR ranking is ~93% noise (CR-65)** with both mechanical roots still open: the class-prior term is **inert** (literal `1.0` passed, CR-81) and the tier-ceiling is mis-shaped (CR-82). 14 of 15 served wealth rows were one signal type. | [DOC] post-remediation §G/§I, ELEVATED | Directly upstream of T1-2's 1,195 dark `msr_signal_type` concepts. | **ALREADY-FIXED (register stale) — PARISHODHANA Phase-A Prober A8, 2026-07-27:** both named mechanical roots are closed in code (`bo_laksana.py`, commit `4bebb622`, 2026-07-14) — `_load_class_priors`/`_resolve_class_prior` activate `class_prior` from `brahma_class_priors` (CR-81 no longer inert) and `_tier_ceiling_for` + `_assign_tiers_by_percentile` retire the blanket varga-ceiling for ratification-aware percentile tiers (CR-82). Full evidence + annotation on the CR-81/CR-82 rows in `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md`. Whether the 95.7%/93%-noise *distribution number itself* has moved is a live re-measurement Phase B should run — this annotation confirms the mechanical root cause is closed, not that the headline percentage has been re-verified. |
| T1-8 | **CGM never feeds ranking** — `bo_laksana` runs before CGM in the DAG and reads no `bodha_cgm_*` table (CR-84); the CGM→convergence bridge is a dead passenger field (CR-85); edge strengths are hardcoded literals with a version label but no formula (CR-86). | [DOC] post-remediation §I | The causal-graph layer exists and influences nothing. | **PARTIALLY ALREADY-FIXED — PARISHODHANA Phase-A Prober A8, 2026-07-27:** CR-84 is CLOSED (annotated on its POST_REMEDIATION_CONSUMPTION_REGISTER row) — a post-CGM `bo_laksana_rerank` asset now feeds real CGM centrality into `structural_role_score`. CR-85 and CR-86 remain **LIVE-OPEN**, each partially: CR-85's flat-0.5 normalization bug is fixed (`ka_yojaka.py` Title-Case graha-key fix) but `cgm_centrality_weight` is still never read by `ka_sangam`/`services/ka_sangam/engine.py`'s `SUPPORTING_WEIGHTS` or any current — still a dead passenger field per the original claim. CR-86's edge-strength literals ARE replaced by a real formula (`_edge_strength_v1`, `bo_karanajala.py:188-368`) and all 4 centralities (pagerank/eigenvector/betweenness/harmonic) ARE now computed via networkx (`bo_karanajala.py:~1669-1719`) — but the declared `sade_sati` edge type still has NO builder function anywhere in the codebase (only appears in valence/relationship-class constant dicts), so the "dead type" sub-claim still reproduces live. Net: T1-8 as a compound item is NOT fully closed — CR-85/CR-86's residual claims are LIVE-OPEN. |
| T1-9 | **W7 flagship bar unmet** — sealed n=3 median 11/13 vs the ≥12/13 bar; `special_lagnas` (3/3 runs) and `all_chart_mechanisms_and_chains` (2/3) served but not reflected in naive prose. | [LIVE] SAMĀPANA, verified by Opus Verifier | My standing recommendation: **dispose rather than chase** — the residual is foregrounding, and engineering the digest to satisfy the grader's specific families is teaching to the test. Note this interlocks with T1-1: the same phenomenon. |
| T1-10 | **DP-3 audit-completion gate** — DARPANA's single-pass grading missed both trust-breaking vetoes; ~32 of 45 answers were never independently audited; the report states the true false-confidence count *"is unknown and empirically ≥2"* and installs an audit-completion gate **blocking any future ACCEPT**. | [DOC] UAT report §4/§12 | The campaign's own disposition was **NOT ACCEPT**, pending audit completion + a re-run battery against the closed baseline. That re-assessment has never been run. |
| T1-11 | **DP-4 gochara sweep has no health/adverse event class** — models only career_advancement / marriage / major_gain. This is the *data* root of the S4-05 health false-confidence veto; SATYA-ŚEṢA closed the *serving-voice* harm (attestation + cross-pointer) but stated building the class was "explicitly out per the brief." | [DOC] UAT §12 gap 4, SATYA-ŚEṢA §4 | Latent trust-breaking: the guardrail is honest, the underlying blindness remains. |

### Tier 2 · Claimed open, verification-cheap (the reconciliation backlog)

These are the ~50 register rows most likely to contain further false alarms. Grouped by cluster
so they can be verified in batches rather than one at a time:

- **Receipt-honesty cluster** [DOC] — CR-1 (`timing_hooks` empty while receipt says `timing_anchored:true`), CR-2 (`varga_confirmation.rows` `[]` while receipt claims D10✓/D2✓), CR-63, AS-1 (blind anchor test 10/12, R-38/R-41 deployed-channel hole). *Note: my own live deep-dive this session saw `varga_confirmed: D10✓/D2✓` **with** populated per-varga dignity rows — so CR-2 is a strong false-alarm candidate.*
- **Empty-join cluster** [DOC] — CR-5 (`active_dasha_periods_jsonb: []`), CR-12 (0 activated yogas over 3 years), CR-48 (`activation_start: null` on every row), CR-37. Several likely closed by the D-2/D-3 waves.
- **Filter-fallthrough cluster** [DOC] — CR-42 (*"worst defect class in the estate"*: 4 `ref_*` tools accept a documented filter and silently ignore it), CR-10, and **`mimamsa_lel_query`'s `query`/`offset` returning an identical `result_hash` regardless of input** — the one member of this cluster independently re-confirmed live during ŚODHANA T9, deferred across **four** consecutive campaigns.
- **Decorative-data cluster** [DOC] — CR-72 (`dosha_label` is decorative, not computed — all 22 rows), CR-73 (labels astrologically false, no cancellation check), CR-74 (Kāla-Sarpa served label contradicts the computed per-varga fact). Partially closed by EL-18; needs per-dosha verification.
- **Wealth-layer emptiness cluster** [DOC] — CR-19/CR-66/EL-17 (**zero** wealth-domain L4 phala anchors — the layer built to answer "when, for money," empty exactly there, re-confirmed three times), CR-20/CR-67 (`bo_upaya` wealth resonances 0), R-09 (`associated_doshas_array` + `estimated_cost_inr_range_jsonb` 100% NULL for every chart).
- **Sidecar/auth cluster** [DOC] — CR-8 (`ref_*` family 401/500/404), CR-9 (registry inventory tools 401 — the system's own asset inventory dead to a consuming LLM), CR-40 (ELEVATED), AS-7 (bench-vs-deployed divergence).
- **Bundle honesty** [DOC] — CR-39/CR-14 (`holistic_bundle` 5 of 8 sub-tools error while returning `ok`). ŚODHANA T2 shipped `status: degraded` for this; **needs a live re-check** to confirm the sub-tools themselves were repaired, not just the envelope.
- **Small serving residuals** [DOC] — R-08 (`mechanism_retrodiction_get` not resolvable on the MCP surface despite PR #688 — *note: it IS in the current tool catalog, so likely stale*), R-10 (`leverage_index` field absent from the response shape), R-27/EL-19 (bare `saham` serving alias), R-29/EL-51 (`ref_remedies_chart_get` missing `chart_id` filter), R-42/EL-58 (a **ready-written SQL migration** that only needs running), R-43/EL-60a, R-44, EL-31 (`query_house` never built).

  > **PARIŚODHANA A7 disposition (2026-07-27), Phase A reconciliation — probed live against production + working tree, per item:**
  > - **R-08 → ALREADY-FIXED (register stale).** Live `mechanism_retrodiction_get(chart_id=482012f1)` returns `ok:true` with full per-house mechanism/fired_events/unmapped_events/not_confirmed_events payload — this ledger's own "likely stale" hedge was correct. No code fix needed; the tool has been reachable and correct all along. See `ganita_database_schema_get`/tool catalog — it is registered and callable today.
  > - **R-27/EL-19 → ALREADY-FIXED (register stale).** β.D2 (2026-07-25, `ledgers/BETA_D2.md`) had already disproven the "never computed" half and shipped the alias fix in `register_p1_aliases.ts` (`SPECIAL_LAGNA_CATEGORY_MAP`, EL-41/B-1 comment block) + `address_resolver.ts` (`saham` → `saham_position`). Live-reverified this session: `ganita_special_lagnas_get(chart_id=482012f1, categories:['saham'])` returns 560 `saham_position` rows with `category_receipts:[{fact_category:'saham', confirmed_count:560, receipt_state:'CONFIRMED'}]`. Fully closed, not merely partial.
  > - **R-29/EL-51 → LIVE-OPEN.** Confirmed against production: `bodha_remedies_get(chart_id=482012f1, graha=Saturn)` still returns only 3 prescriptions (2 mantra + 1 charity) against BPHS's ≥8-remedy catalog for Saturn served by the global corpus tool (`ref_remedies_chart_get(affliction=saturn)` returns 29 rows including a gemstone remedy the chart-scoped engine omits); `associated_doshas_array`/`estimated_cost_inr_range_jsonb` remain NULL (self-disclosed `data_gap_note`); no `maraka_contraindication_verdict` field exists anywhere in the codebase (grepped) — contraindication is still catalog prose (`contraindications` text field), never a computed verdict. Note `ref_remedies_chart_get`'s "missing chart_id filter" is BY DESIGN (`register_d7_channel.ts`: "chart_id (provenance only, not used for data filtering)" — a global corpus lookup, not a defect); the real chart-scoped gap is in `bodha_remedies_get`/`bo_upaya` as above.
  > - **R-42/EL-58 → LIVE-OPEN, B3 ready-to-ship candidate (precise state, not a code-level defect).** The additive migration text is fully written (`LAPSED_UNOBSERVED_MIGRATION_SQL` in `platform/src/lib/retrieval/registry/layers/L5_mimamsa/prediction_lifecycle_sweep.ts`) but has NOT been created as a numbered migration file or run: live `SELECT pg_get_constraintdef(...)` on `brahma_prospective_ledger_lifecycle_status_check` confirms the constraint still lacks `lapsed_unobserved` (only open/matched/confirmed/falsified/withdrawn). Live `standing_predictions_read(chart_id=482012f1, status=open)` reproduces the exact defect: prediction `8d85d0c7-…` ("major_gain window 2011-02-15..2011-03-10") is still `lifecycle_status:"open"` today (2026-07-27). Routing note: this is pure "run the migration + wire the sweep" execution work, not investigation — Phase B should treat it as a B3 fast-track, not a design task.
  > - **R-43/EL-60a → LIVE-OPEN.** `platform-mcp/src/tools/reading_notes.ts` is still a single hardcoded markdown blob (`READING_NOTES_482012F1`) with no write/accretion path (grepped for INSERT/UPDATE/accrete — none). Live `reading_notes_get(chart_id=482012f1)` returns that identical static content. Matches `STREAM_GAMMA_CLOSE_v1_0.md`'s "PARKED-HONEST, blocked-on-α (needs tools/**)" disposition from 2026-07-25 — still unactioned.
  > - **R-44 → ALREADY-FIXED (register stale).** The anchor's "298/300 UNATTRIBUTED, empty grounding.fact_ids" no longer reproduces on either canonical chart. Live `bodha_chart_digest_get` for BOTH 482012f1 and 1c826d5a now returns `attribution:{served_unattributed_entities:0, served_unattributed_share:0}` with the explicit note "0% UNATTRIBUTED on the served ranked surface" and a resolved, non-empty `grounding.fact_ids` set (489 / 308 resolved facts respectively). The WP-1.2(a)/(β) entity-attribution work closed this after the anchor was recorded.
  > - **EL-31 → LIVE-OPEN (confirmed via code, not a false alarm).** `platform/src/lib/retrieval/registry/layers/L1_ganita/index.ts` carries the comment "query_house (the house-entity face) is PARKED-HONEST this session — not yet built; only query_planet is wired." No `query_house`/`ganita_house_get` tool exists anywhere in `platform-mcp/src` or the registry. `query_planet` (EL-31's other half) is live.
  > - **EL-07 (15 ungrounded absence candidates) → LIVE-OPEN, but a documentation/audit-hygiene item, not a runtime API defect.** Ran `absence_lint_gate.ts` live against the current working tree: **37 total candidates, 19 ungrounded** (up from the 15 recorded at merge #3) — the underlying condition reproduces and has not improved. However this is a non-blocking, report-only static lint (`ABSENCE_LINT_STRICT` unset ⇒ WARN only, never fails CI) scanning source comments/strings for absence-phrasing heuristically — it is not a live MCP response defect. Route to Phase-B hygiene tier (T4), not the urgent-fix tier.
  >
  > **UPDATE 2026-08-01 (CI campaign, §6.12–§6.13 of `CI_EFFICIENCY_AUDIT_v1_0.md`) — EL-07 is
  > CLOSED, and the counts above are superseded.** The lint's scope was narrowed: it matched raw
  > source lines, so it fired on comments, docblocks and Postgres error-matching regexes
  > (`/column ".*" does not exist|.../` — code that *detects* a DB error, the opposite of
  > claiming absence). `servedTextOnly()` now strips comments and regex literals before matching
  > while deliberately keeping string literals in scope. **STRICT-mode findings went 21 → 2**, and
  > a full triage found **both survivors are working-as-intended**: a tool description advising
  > the model to search "before assuming a needed capability does not exist", and an honest
  > disclosure ("bhanga_checked reports false, not fabricated"). There is no ungrounded
  > absence-claim defect here to route anywhere. The gate stays report-only **by decision**, not
  > pending triage; the detector remains sound (re-proven post-narrowing) so a genuinely new
  > absence claim would still surface.
  >
  > Annotation-applied: R-08, R-27/EL-19, R-44 (register-stale closures, cross-annotated in `ELEVATION_REGISTER_v1_0.md` and/or `ledgers/elevation_v2/ELEVATION_V2_COVERAGE_MATRIX_FINAL_v1_0.md` where those items have their own canonical entry). R-29/EL-51, R-42/EL-58, R-43/EL-60a, EL-31, EL-07 remain open per above — no annotation applied to their entries per protocol (annotations are for closures only).
- **Second-chart systematic under-coverage** [DOC] — chart `1c826d5a`'s `ka_gochara_sweep` stale (blocked on an incomplete upstream run); Ω7 dark-corpus never executed for it; several verifications only ever ran on 482012f1.

### Tier 3 · Native-gated (only you can close these)

| # | Item | What's needed |
|---|---|---|
| T3-1 | **WL-7 financial LEL enrichment** — and note the audit's key correction: the LEL has **57 point events** (not 65), of which **13 are financially load-bearing**. 5 of WL-7's 6 requested classes are already covered. | Four small answers: (1) any business/personal loan or mortgage, ever, with rough dates — the *only* class with zero coverage; (2) coarse revenue/profit figures for the Jul-2025 Marsys Technology contract and its Mar-2026 close (numeric enrichment of two events that already exist — *"converts structural verdicts to calibrated ones"*); (3) when Marsys Technology was formed as a partnership, distinct from Marsys Group's Jul-2023 founding; (4) exact US job-loss date pre-May-2023. **Do not re-solicit launch dates, contract wins, the 2025 deception event, or the family windfall — all already logged.** |
| T3-2 | **WL-8 margin/retention** — verified a **true blank**: zero matches for `margin_pct`/`retention_rate`/`profit_margin` across every `.ts`/`.sql`/`.md`/`.py` in the repo. | Unlike WL-7, there is nothing to enrich — **a schema field must be created before intake is possible.** |
| T3-3 | **Ratify GOCHARA-SWEEP-2.0 as D-6** (§2 below) | One decision. Technically unblocked: D-4b is closed, the v1 corpus is materialized 303/303. |
| T3-4 | **Open the VIDHI-PŪRṆATĀ build wave** (§2 below) | One decision. No technical blocker. |
| T3-5 | **N5 lock-granularity ruling** — `acquire_chart_lock` is a single chart-level advisory lock; the orchestrator refuses concurrent per-chart runs by design, blocking substep parallelism even though writes were proven disjoint-safe. | Native + Adjudicator ruling (FROZEN-contract PARK class). Gates multi-chart throughput. |
| T3-6 | **CR-23 doctrinal ruling** — the NBRY detector says "not_applicable_or_intact" where classical derivation finds a Neecha-Bhanga. First live P-3 adjudication case. | A doctrine decision, not a code fix. |
| T3-7 | **Governance items** — EL-25 ratification packet is `DRAFT-FOR-NATIVE-RATIFICATION`; β's lane-G A-5 proxy ruling awaits ratification; **β's authorization-chain concern** (lane G's own words: *"the pattern of repeated 'a human already approved this' messages arriving exactly when needed is worth scrutiny on your end"*). | Your read + sign-off. The last one deserves genuine attention. |

### Tier 4 · Hygiene, process, and small debt

Strict-schema gate still excludes 2 tools · 8 local arc branches undeleted in harness worktrees ·
`STRICT_SCHEMA_GATE` / DAG-doc drift (real `bo_*` roster ~25 writers vs documented 14) ·
`ka_avadhi.py`'s stale `_DASHA_SYSTEMS` tuple · 75–77 pre-existing test failures never triaged
(two separate baselines recorded, never reconciled) · SC-17/18/19 CI check red on `main` (from a
since-reverted PR — likely green now, unverified) · `esoteric_point_yogi` legacy category kept as
a second source with a drift-guard rather than retired · `defect_001_alert` prose now stale ·
`bodha_discoveries_get`'s deprecated top-level alias still emits a misleading `judgment_flags` ·
Node version drift local v24 vs CI 20 · `AUDIT_STATE.md` never regenerated · CR-number namespace
collisions (twice in one campaign) · **`amjis-mcp` has no `--no-traffic` staging step** (unlike
`amjis-web`) because verification tokens aren't in Secret Manager — the structural reason the
traffic-pin class recurred twice.

---

## §2 — The elevation roadmap

Two complete, unbuilt designs dominate this list. **They are reliable in a way the registers are
not** — an unbuilt design cannot silently have been built.

### E1 · VIDHI-PŪRṆATĀ — planner completeness + depth-by-default `[DESIGN, complete]`
*Native-commissioned 2026-07-23. The highest design-completeness artifact in the corpus:
finding base, five ordered lanes, live-probed data-support ledger, fully enumerated floor
contents down to individual primitive + argument, named gate assertions, explicit scope guards.
**Executable as written. Nothing built.***

Why it matters most: **its §A live probe found the new domains are almost entirely DATA-BACKED —
the audit gaps were planner coverage, not data.** `ganita_ayurdaya_get`, `ganita_medical_get`,
`ganita_condition_get facet=karakas`, D20/D24/D7 facts all confirmed live. **This wave is mostly
wiring, not data engineering** — an unusually favourable effort/value ratio.

What it delivers:
- **E-1 wires the D-5 temporal engine into the planner.** The registry predates Gochara-Chitra:
  `gochara_activation_get` / `gochara_forecast_get` / `gochara_election_avoidance_get` have **no
  Vidhi primitives at all**. *An entire large wave is built, deployed, live-verified — and
  structurally unreachable from the planner.* This is the brief's own "highest-value gap."
- **Depth becomes the default**, per your stated product identity — full floor + machine band +
  intervention + elevation bands for every question except an unmistakably pointed lookup;
  ambiguity breaks toward *more* depth, never less. (This is the doctrine your "beyond acharya"
  instruction implies, written down as law rather than a per-call flag.)
- **Three new reachable domains** — spirituality (mandatory), education, progeny — each with a
  worked floor, all data-backed today.
- **E-0 Pūrṇa-Ādhāra foundational floor** — when the planner doesn't recognise the territory it
  lays the *entire* foundation out, layered and prioritized (not a dump), and lets the
  intelligence judge. Replaces a thin 6-item `general_synthesis` floor.
- **E-2 makes every reading falsifier-bearing by construction** — which converts the standing
  prediction loop from a discipline into a mechanism, and that loop is **the only path** to
  unblocking the calibration chain (T1-5).
- **E-7 the insight band** — contradiction scan, tail-divergence (where this chart diverges from
  typical), mechanism/chain motifs, statistical context, and an explicit INSIGHT MANDATE,
  `hardFloor`-protected so insight surfaces are never the first rows trimmed.
- **Unblocks the whole UAT-DARPANA chain** (which cannot meaningfully run against an incomplete
  planner) and closes STATIC_VIDHI_AUDIT F1–F7 + F9.

### E2 · GOCHARA-SWEEP-2.0 — event-driven temporal rearchitecture `[DESIGN, ratification-ready]`
*Your own idea from the 2026-07-21 session — "use our understanding of how the planets move…
jump to the likely points without scanning everything; mind the Moon's intra-day motion" —
formalized into a complete architecture. Zero implementation, by the design's own instruction.*

The inversion: v1 samples a daily midnight grid and asks "what is active?"; 2.0 **enumerates
transitions** and derives intervals, because planetary motion is smooth and piecewise-monotonic.
Six specified components: cubic-spline position substrate (zero live Swiss-Ephemeris calls in the
sweep path); a **chart-independent global event calendar** — *"the sky's own diary, every chart
reads the same one"*; per-chart contact root-finding; interval-intersection algebra for
composition; **classically-shaped multi-rate refinement** (slow layers eager, Moon/lagna lazy —
*"exactly how an acharya drills down; exactly where compute belongs"*); serving contract
unchanged plus sub-day precision fields.

What it delivers:
- **~31 CPU-hours per chart per century → target minutes.** This is the gating constraint on the
  entire multi-chart research mission — and therefore on hierarchical calibration ever becoming
  meaningful (T1-5).
- **Sub-day claims become computable and honest** — a capability the system does not have at all
  today. v1's grid undersamples the Moon (~13°/day); hour-level muhūrta/election answers grounded
  in the same λ field become possible.
- **The false-precision defect class becomes structurally impossible** — window edges become
  astronomical facts rather than chunk artifacts.
- A **reusable global sky-diary asset** every future chart consumes at zero marginal cost.

Its verification discipline is the best-specified in the corpus: v1's materialized century table
is the equivalence corpus, and a documented-divergence protocol classifies every difference —
with *"v1 Moon-undersampling miss"* named in advance as the expected headline finding.

**The two interlock and neither subsumes the other:** VIDHI-PŪRṆATĀ makes the temporal engine
*reachable*; 2.0 makes it *fast and sub-day accurate*. Build 2.0 alone and users still can't
reach it; build E-1 alone and you expose an engine honest only at ≥1-day resolution costing 31
CPU-hours/chart. **VIDHI-PŪRṆATĀ is the cheaper, higher-immediate-value build; GOCHARA-SWEEP-2.0
is the strategic unlock.** Neither addresses T1-1 (discoverability) — that third piece is unowned.

### E3 · The reachability triangle (my recommendation for what to do first)

T1-1, T1-2, and T1-3 are **one problem seen from three angles**: the instrument computes ~12,450
wealth concepts, serves ~700, because (a) naive consumers never reach the planner, (b) the floors
that would guarantee coverage are written but unwired, and (c) the deepest instrument isn't
discoverable in the tool catalog. Fixing any one alone moves little. Fixing all three is, on the
evidence, **the largest single quality jump available to this platform** — and γ already named
the missing bridge nobody owns: *have `assess_wealth`/`judgment_query` themselves route through
or inline dossier's coverage.*

### E4 · Capability additions (ranked by value/effort)

1. **KP sub-lord engine** (T1-4) — a whole classical system currently half-built and dark; you
   flagged it yourself. Highest capability-per-build of anything here.
2. **Health/adverse event class in the gochara sweep** (T1-11) — closes the data root of the only
   trust-breaking veto class the product has produced.
3. **Near-miss yoga detection** (WL-4) — "one leg short" dhana/raja yogas are *precisely* where
   remedial intervention could act. Never built, never mentioned in any campaign.
4. **Multi-cycle daśā activation** (WL-5) — the recurrence ladder **already exists** in
   `activation_predicted_dates_jsonb`; only the top-level window is single-cycle. This is
   surfacing, not computing.
5. **Muhūrta unification** — make `muhurta_finder` a view over the signed λ field (argmax of
   favorable − adverse) rather than a parallel scorer; plus intra-day sub-windows from
   `panchanga_daily`, which already holds them.
6. **Birth-time rectification closure** (WL-6) — 185 candidates, confidence "unresolved," and
   `lel_fit_score: 0` across all of them (CR-47) with 0 of 36 LEL training events matching. That
   zero is itself a bug worth root-causing; sub-period precision at the 2027 boundary depends on it.
7. **Forward daśā windows** — `kala_windows_get(domain=wealth)` returns `forward_window_count: 0`;
   forward windows are still hand-assembled from the dasha table.
8. **Per-varga Ashtakavarga** — confirmed absent live; 504 concepts/domain sit behind it.
9. **Serve the 157 truly-unreachable fact families** (of 3,058; only 76% reachable) — or honestly
   retire them.
10. **Extend dark-corpus + Ω-routing coverage to marriage and health** — only wealth and career
    are flagship; the other two domains have never been measured at all.

### E5 · Instrument-quality work (from my own consumption of the product)

- **Foregrounding, not just serving** (the lesson of T1-9 and DP-5): substance buried in JSON
  doesn't reach the answer. The composed `reading` digest was the right idea; it needs the
  *narrative* prominence that argala's numeric score has and special lagnas lack.
- **A single `reading_depth: deep_dive` contract** already exists as of SAMĀPANA — extend it so
  every heavy tool honours one request rather than four flags.
- **Guaranteed-fits compact form** (MC-004/006, deferred **three** times) — needed for endpoints
  without file access, and the hard-guard against it applying to deep dives is already built and
  waiting for something to bind.
- **Certify the sealed-harness graders** — every flagship number in the corpus rests on manual
  good-faith grading; `evals/k2/consumption_grader.ts` has never been executed in-session, and
  two historical baselines (2/13 naive vs ≥12/13 dossier-paging) disagree about what the bar even
  measures. **Until this is reconciled, "11/13 vs the 12/13 bar" is not a well-posed statement.**
- **A standing reconciliation cadence** — the CR-drift class's own recommended fix (a periodic
  grep of every `known_gap: 'CR-N'` in `registry_data.ts` against live disposition) was never
  implemented. This is what stops §0 from happening again.

---

## §3 — The recommended campaign: PARIŚODHANA (full reconciliation + sweep)

**Phase A — Reconciliation (verify-first, blocks everything).** Take every Tier-1/Tier-2 item and
probe it live. Output: a single disposition table where each item is `LIVE-OPEN`,
`ALREADY-FIXED (register stale)`, or `NOT-REPRODUCIBLE`. Annotate the source registers **in
place** so this never has to be re-derived. Expect a large fraction of Tier 2 to close on
evidence — three of my four spot-checks did.

**Phase B — Fix the genuinely open, in this order:** (1) the Tier-2 items Phase A confirms, batched
by cluster; (2) the reachability triangle (T1-1 + T1-3), which is the quality jump; (3) the
ready-to-ship trivia — R-42's already-written migration, the saham alias, the `chart_id` filter,
the 2 remaining strict-schema exclusions, the 8 stale branches.

**Phase C — Institutionalize:** implement the reconciliation cadence; give `amjis-mcp` the
`--no-traffic` → smoke → promote pipeline `amjis-web` already has; certify the harness graders.

**Then, as separate commissioned waves:** VIDHI-PŪRṆATĀ (cheaper, higher immediate value, unblocks
UAT-DARPANA) → GOCHARA-SWEEP-2.0 (the strategic unlock) → the E4 capability list.

---

*The honest one-line summary: the platform is in far better shape than its registers say, and its
registers are in far worse shape than the platform. Reconcile them once, and the real backlog —
which is mostly two excellent unbuilt designs and one unowned discoverability problem — becomes
small enough to see.*
