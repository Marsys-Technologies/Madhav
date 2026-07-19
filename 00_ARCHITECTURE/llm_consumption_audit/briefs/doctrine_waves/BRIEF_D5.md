---
artifact: BRIEF_D5
type: WAVE BRIEF (FROZEN — §B slots bind at wave open)
wave: D-5 — Gochara-Chitra (the configuration-scanning temporal engine)
version: 1.0
status: BOUND — wave OPENED 2026-07-19T08:31:47Z on native kickoff directive. Binder pass
  (BIND_D-5.md) re-confirmed gate-zero + all §B slots live; CR-113 closed, CR-114 dispositioned
  non-blocking. §B slot values below remain the FROZEN-at-freeze snapshot (2026-07-19, pre-D-5
  readiness pass); BIND_D-5.md is the re-confirmation record.
governing: CONDUCTOR_PROTOCOL.md · ESCALATION_POLICY_v1_0.md · ADJUDICATOR_CHARGE_v1_0.md ·
  TEMPORAL_ENGINE_ARC_PLAN_v1_0.md §4 (engineering decomposition) ·
  SANKALPA_GOCHARA_CHITRA_v1_0.md (vision/doctrine framing) · DIS.027/028/029 (DR-14/15/16,
  ratified) · REPORT_D-4A.md + STATE_D-4A.md (shipped-reality source)
prerequisite: D-4a gate GREEN (confirmed — REPORT_D-4A.md §3, 7/7). Pre-D-5 readiness pass
  (this document's companion checklist) re-probed every D-4a deliverable live on 2026-07-19 —
  all PASS, two non-blocking infra flags recorded (§B.8 below), one D-4a bug found and fixed
  (item #3 correction, previously mis-quarantined, now live — see the readiness report).
gate_class: engine-integrity + specimen + no-degradation vs the A-5 dry-run baseline —
  EXPLICITLY NOT a calibration claim (D-4b's DR-12 adjudication remains untouched by this wave)
---

# BRIEF_D5 — Gochara-Chitra (the engine)

## §0 — What this wave builds (vision recap; full text: SANKALPA_GOCHARA_CHITRA_v1_0.md)

The engine that answers RETRODICTION / ACTIVATION / FORECAST / ELECTION-AVOIDANCE as four views
over one object: the per-chart, per-event-class intensity function λ_e(t | chart). The chart is a
sparse filter (the resonance map); the sky's permutations are projected onto it, not enumerated.
Events unfold in the DR-13 grammar (point / interval / chain with irreversibility milestones); the
engine never speaks with more temporal precision than an event-class's shape supports (BINDING,
see §3 below). Classical standing: the Sarvatobhadra Chakra is the tradition's manual build of
this exact engine (CR-21 completes it here); dvi-pramāṇa (daśā promise × gochara delivery)
generalizes to DR-14's full timing-system plurality.

## §1 — Lane map (G-1 through G-5)

| Lane | Name | Builds | may_touch (disjoint) | Verifier requirement |
|---|---|---|---|---|
| **G-1** | Resonance map | `gochara_resonance_map` table (per chart × event-class), classical-prior-weighted target sets (bhavas/lords/karakas, mechanism nodes, sensitive degrees, arudhas, yoga constituents, dasha-lord portfolios) sourced from `bg_transit_rules` + BPHS, citations mandatory | `platform/python-sidecar/pipeline/orchestrator/writers/ka_*resonance*` (new writer file(s)), `platform/migrations/<NNN>_gochara_resonance_map.sql`, `00_ARCHITECTURE/GOCHARA_RESONANCE_MAP_SPEC.md` (new doc) | Opus, live query of `gochara_resonance_map` for ≥3 event-classes confirming non-empty target sets with real citations, no `uncited_extension` on a primitive that has a known classical source |
| **G-2** | Configuration grammar | 12 contact-primitive families (degree-contact, drishti-contact, sign-ingress, nakshatra-ingress/tara-state, kakṣyā-cell crossing, AV-threshold state, gochara-vedha pairs, Sarvatobhadra vedha [CR-21 centerpiece], station/retro-loop, eclipse-degree, returns, Sāde-Satī phase) + 6 composition operators (simultaneity, double-transit, kartari, cancellation, amplification, dasha-coincidence across DR-14 plurality) | `platform/python-sidecar/services/gochara_grammar/` (new), `platform/python-sidecar/pipeline/orchestrator/writers/ka_*grammar*` (new writer file(s)) | Opus, live-generate ≥1 real "sentence" (grounded configuration with fact_ids) per primitive family, confirm every sentence carries a classical citation OR an honest `uncited_extension` flag (B.10 — zero silent invention) |
| **G-3** | Intensity engine | λ_e = PROMISE × PERMISSION(DR-14 plurality, all systems as independent generators — NOT Vimśottarī-gated) × exp(β_e·X(t)) − suppression; β = disclosed structural priors (`calibration_state: structural_prior`) until D-4b fits them; adverse classes get identical machinery, signed valence per D-2's doctrine | `platform/python-sidecar/services/gochara_intensity/` (new); consumes G-1 + G-2 outputs read-only | Opus, live-compute λ_e for ≥1 point/interval/chain event-class each, confirm PERMISSION genuinely sums across ≥2 independent timing systems (not Vimśottarī-only) |
| **G-4** | Forward sweep + serving | Daily-grid sweep, chart-relative **birth → birth+100y**, into standing table `kala_gochara_windows` (window, event_class, signed intensity, active sentences w/ fact_ids, contributing systems, suppression state, `peak_basis` provenance per DR-10); shape-aware output semantics (BINDING, §3); activation/forecast/election-avoidance views; muhurta_finder becomes a view over the signed field; §N.6 budgets from day one | `platform/migrations/<NNN>_kala_gochara_windows.sql`, `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_sweep.py` (new `WriterBase` subclass, FROZEN-contract-conformant), `platform-mcp/src/tools/retrieval/register_*gochara*.ts` (new serving tools) | Opus, live scope-limited Cloud Run job rebuild for chart 482012f1 restricted to the new `ka_gochara_sweep` asset only, then live MCP calls proving activation/forecast/election views each return real, shape-correct rows |
| **G-5** | Ledger integration | Engine claims filed into `brahma_prospective_ledger` with `configuration_signature` populated (column already live + nullable — B6, confirmed); adverse claims per DR-16 honest-clarity gate | `platform/src/lib/lel/prospective_ledger.ts` (extend, do not rewrite — same file A-4 built), `platform/src/app/api/mcp/writes/[action]/route.ts` (extend the existing `prospective_ledger_file` handler path) | Opus, live-file ≥1 real `generator_class=engine` claim with a populated non-null `configuration_signature`, confirm an adverse-valence claim carries the full DR-16 payload (falsifier + mitigation-paired + confidence-honest, not bare) |

**Merge order:** G-1 → G-2 (grammar consumes resonance-map targets) → G-3 (intensity consumes both)
→ G-4 (sweep consumes G-3's λ_e) → G-5 (ledger consumes G-4's served windows). No lane may merge
ahead of a hard upstream dependency; parallelization only where the DAG allows (e.g. G-1's writer
work and G-2's grammar-primitive authoring can start concurrently since G-2 only needs G-1's
*schema*, not its populated data, until G-2's own live-verification step).

**Isolation:** every lane in its own `wave/D-5/<lane>` git worktree per CONDUCTOR_PROTOCOL §2/§3.
Any path outside a lane's declared `may_touch` glob is automatic scope-warden REJECTION.

## §2 — Test-first construction discipline (BINDING on every lane, ARC PLAN §4.5)

No D-5 lane merges unmeasured — this is the D-3 lesson made law. Every lane's acceptance
criteria (in addition to its own functional deliverable above) includes BOTH:

1. **Mini-retrodiction check against the A-5 baseline.** Score the lane's contribution (once G-3
   exists — earlier lanes G-1/G-2 check via a stub curve or defer this specific sub-check to G-3,
   recorded explicitly, not silently skipped) through the SAME `a3_scoring_harness` A-5 used
   (`platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/` — unmodified since A-3,
   confirmed live-reproducible byte-for-byte this session, see §B.3 below). Compare CRPS skill on
   the relevant event-class(es) against A-5's committed baseline (`artifacts/D-4a/A-5/
   dry_run_receipt_v1_0.json` — 55 scorable events, 5 domains: general/health/marriage/career/
   wealth, pratyantar_lord meanCRPS/skill per domain tabulated in §B.3). Result recorded
   per-lane as **diagnostic, not a pass/fail gate** — "improve or not-degrade" is the target,
   not a hard blocker, per ARC PLAN §4.5's own framing ("recorded per-lane, diagnostics not
   gates"). A lane that clearly DEGRADES skill without explanation is a red flag for the Binder
   to investigate before merge, not an automatic reject.
2. **Named LEL specimens.** The engine must reproduce three specific, already-known configurations
   from the live LEL/mechanism data (re-derived fresh at verification time, never cached/assumed
   per protocol's evidence rules):
   - **Sarvatobhadra vedha states around 2025-05** (the G-2 grammar's classical centerpiece,
     CR-21) — the vedha-cancellation primitive must show its states in this window.
   - **The 2010-07 → 2011-03 windfall interval** (chart `482012f1`, `event_id bd7f5711…`,
     `shape='interval'`, confirmed live per D-4a A-1 — the engine's interval-shaped output must
     show elevated intensity spanning this window, not a single point).
   - **Double-transit specimen = marriage, 2013-12-11** (the G-2 double-transit composition
     operator — two grahas' drishti on one natal target — must produce a configuration near this
     date; marriage is `point`-shaped per the live ontology, §B.5 below).

## §3 — Shape-aware output semantics (BINDING serving rule, ARC PLAN §4.4/§7)

The engine emits in the event-class's canonical shape (27 classes, live-enumerated §B.5 below;
13 point / 9 interval / 5 chain): point-class → a dated window with a peak; interval-class → an
elevated-hazard SPAN with duration drawn from the ontology's `duration_prior` (never a single
asserted day); chain-class → per-milestone sub-windows, each scored on its OWN configuration (an
enrollment fires on different primitives than a result-declaration), with the class's
`irreversibility_milestone` (where the ontology declares one) flagged as the primary claim. This
is an ARC-WIDE invariant (ARC PLAN §7): "a system that scores intervals but predicts points has
not implemented the doctrine." G-4's serving views (activation/forecast/election-avoidance) and
G-5's ledger claims must both obey this — never more temporal precision than the shape supports.

## §4 — DR-16 honest-clarity gate on adverse serving

Every adverse/inauspicious window G-4 serves (and every adverse claim G-5 files) is governed by
DIS.029 (DR-16, ratified): honest clarity co-equal with restraint (no euphemism/withholding);
always probabilistic, never fatalistic (no death/ruin/doom point-claims — the uniform birth→
birth+100y horizon exists specifically so no infrastructure encodes a longevity opinion);
falsifier-bearing (adverse claims enter the ledger like any other claim, per G-5); mitigation-
paired (suppression + BPHS-cited remedy ship in the SAME payload, never bare); confidence-honest
(`calibration_state`/n_observations/control-delta disclosed alongside the claim); tiered per
MACRO_PLAN's Ethical Framework for non-native consumers, full-detail default for the native. **No
adverse-serving code in G-4/G-5 merges without a live demonstration that a specific adverse claim
carries all five of these properties in one served payload** — this is a hard acceptance item,
not a diagnostic.

## §5 — §N.6 Serving Density Principle (from day one)

G-4's serving views inherit CLAUDE.md §N.6 without exception: confirmed/firings-authoritative
rows (a materialized `kala_gochara_windows` row with real intensity above threshold) are never
flattened together with catalog-only/corroboration-only rows; a response-budget trim protects the
densest layer first (`hardFloor`); an honest empty result reports via a flags field, never a
silently-substituted hollow envelope; `density_contract` is populated on every new
`CapabilityDescriptor` G-4/G-5 register — not deferred to a later hygiene pass.

## §6 — Sweep horizon + citation discipline

**Sweep horizon: chart-relative birth → birth+100y, uniform for every chart** (ARC PLAN §10 Q3,
ratified) — explicitly NOT tied to computed longevity/ayurdaya (using it to bound the sweep would
encode a lifespan claim, an Ethical Framework violation). `curve()` remains unbounded beyond the
materialized horizon for on-demand ranges. **Every grammar primitive (§1 G-2) carries a classical
citation (bg_transit_rules/BPHS chapter+verse where the codebase has it) OR an explicit
`uncited_extension: true` flag** — B.10's no-fabricated-computation discipline extended to rule
provenance, not just numeric values. A primitive with neither is a lane-failing defect, not a
style note.

## §7 — Exclusions (verbatim, ARC PLAN §4.6) + must_not_touch

**Explicitly OUT of D-5:** KP sub-lord engine (CR-75 — no substrate exists; enters only if
independently built first, never as a D-5 side-quest) · any FITTED β (structural priors only —
D-4b fits, not D-5) · any DR-12 ruling (the model bakeoff/adjudication is D-4b's, not D-5's, even
though D-5's engine becomes one of the contenders scored there) · new ayanamsha/astronomy code
beyond the sidecar's EXISTING capabilities (confirmed live-reachable, §B.8 below — no new
ephemeris features, no new astronomical computation classes).

**must_not_touch (scope-warden enforced, every lane):** the FROZEN orchestrator contract
(`WriterBase`/`run(ctx)`/`ctx.db_conn` — §N.2, unconditional STOP-and-raise-with-native if a
writer seems to need a contract change) · the sealed LEL test split (events ≥2020-01-01 — a
circuit-breaker class per ESCALATION_POLICY §4, structurally detected) · prior gate surfaces
(A-0 through A-5's own serving code and the `a3_scoring_harness` files — G-lanes CONSUME these,
never modify them; if a lane finds a bug in prior-wave code, it reports to the Binder, it does not
patch across the boundary the way D-4a's A-1 fixed A-2's migration — that was logged as a
tolerated deviation under wave-close time pressure, not a precedent to repeat routinely) · the
raw LEL corpus (G-5 files ledger predictions and reads matched outcomes via A-1's hook; it does
not write directly to `life_events`).

## §8 — §G gate (engine-integrity, NOT a calibration claim)

D-5's gate proves: (1) every G-1..G-5 lane's functional deliverable live per §1's per-lane
verifier column; (2) every lane's §2 test-first mini-check recorded (diagnostic, not blocking
unless a Binder-flagged unexplained degradation); (3) all three §2 named specimens reproduced
live; (4) §3's shape-aware semantics demonstrated on ≥1 example per shape (point/interval/chain);
(5) §4's DR-16 five-property demonstration on ≥1 real adverse claim; (6) §5's density-contract
population confirmed on every new served capability; (7) zero exclusion violations (§7); (8) all
prior batteries green (D-4a's own gate, re-probed — not re-litigated, same reading as BIND_D-4A
§2's precedent: no NEW regression since D-4a's sealed GREEN state). **This gate explicitly does
NOT adjudicate DR-12** — a D-5 engine that reproduces the specimens and improves/holds CRPS skill
is "measured and working," not "the winning model." That ruling stays D-4b's alone.

## §9 — §F3-class execution discipline (inherited verbatim from CONDUCTOR_PROTOCOL, D-1.5a→D-4a)

Every lane in an isolated worktree (`wave/D-5/<lane>`); disjoint `may_touch` (§1 table); shared
files append-only with expected conflicts named in advance; merge in declared order (§1); every
lane independently verified by a fresh-context Opus verifier BEFORE merge — implementer "done" is
a claim, never an acceptance (CONDUCTOR_PROTOCOL's non-negotiable). Rebuilds go via the Cloud Run
job path only (never local cloud-sql-proxy for a chart rebuild — proxy-kill cycle risk); scope-
limited to whatever asset(s) a lane's migration actually touches (G-4's `ka_gochara_sweep` is the
only lane expected to need a chart rebuild at all — G-1/G-2/G-3 are pure service/schema work
consumed at query time, no orchestrator asset). Deployed connector rate-limits under sustained
assertion load (429 cascade) — gate batteries throttle/batch. Orchestration-economy dials
(native-granted): Workflow fan-out for verification panels/gate batteries; effort down for
mechanical stages, up for adversarial verification/root-cause/doctrine-feeding work; model dial
cheaper-for-mechanical/stronger-for-judgment; non-dialable: independent verifier receipt per lane,
gate thresholds, reds-are-reds honesty. Definition of DONE: promise ledger (§10 below) enumerated
at open, gate harness turns every row into an executable check; three altitudes (pre-merge +
integration + post-deploy live re-run on the DEPLOYED connector with rebuilt data — built-but-
not-served is not done); evidence rules (real chart scale, data over flags, specimens re-derived
fresh not cached, no absence claim from a truncated page); close report carries full ledger with
per-row disposition (GREEN+evidence | PARKED+evidence+owner).

## §10 — Promise-ledger pre-enumeration (every §F1 commitment as a ledger-row template)

The D-5 Binder's job at open is VERIFICATION of these rows against reality at that moment, not
authoring new ones — this list is the complete, closed set unless the Binder discovers the ARC
PLAN itself changed between this freeze and open (flag, don't silently add scope):

- [ ] G-1: `gochara_resonance_map` table live, populated for ≥3 event-classes, every target
      carries a classical-prior weight sourced from `bg_transit_rules`/BPHS with a citation.
- [ ] G-1: served with provenance (queryable, not just internal to the writer).
- [ ] G-2: 12 contact-primitive families implemented, each producing ≥1 real grounded sentence
      with fact_ids.
- [ ] G-2: 6 composition operators implemented and demonstrated (simultaneity, double-transit,
      kartari, cancellation, amplification, dasha-coincidence across DR-14 plurality).
- [ ] G-2: Sarvatobhadra vedha completion (CR-21) — the classical centerpiece — demonstrated live
      for the 2025-05 specimen window.
- [ ] G-2: every primitive/sentence carries a citation or an honest `uncited_extension` flag —
      zero silent gaps.
- [ ] G-3: λ_e = PROMISE × PERMISSION × exp(β·X) − suppression implemented, β disclosed as
      `calibration_state: structural_prior`.
- [ ] G-3: PERMISSION genuinely sums ≥2 independent DR-14 timing systems (not Vimśottarī-gated).
- [ ] G-3: adverse event-classes use identical machinery with signed valence (D-2 doctrine).
- [ ] G-4: `kala_gochara_windows` standing table live, birth→birth+100y materialized, scope-
      limited Cloud Run rebuild for chart 482012f1 completed and verified.
- [ ] G-4: shape-aware output semantics demonstrated on ≥1 point/interval/chain example each.
- [ ] G-4: activation/forecast/election-avoidance views all live and returning real rows;
      `muhurta_finder` re-pointed as a view over the signed field.
- [ ] G-4: §N.6 density_contract populated on every new served capability from first merge.
- [ ] G-5: `configuration_signature` populated (non-null) on ≥1 real `generator_class=engine`
      ledger filing.
- [ ] G-5: ≥1 adverse claim demonstrating all 5 DR-16 properties in one served payload.
- [ ] All lanes: mini-retrodiction check recorded (diagnostic) against the A-5 baseline
      (§B.3 numbers below) — degradations flagged to Binder, not silently accepted or blocked.
- [ ] All lanes: the 3 named specimens (Sarvatobhadra ~2025-05, windfall 2010-07→2011-03,
      marriage double-transit 2013-12-11) reproduced live, fresh, at verification time.
- [ ] Zero exclusion violations (§7), zero must_not_touch violations.
- [ ] Anti-gaming pass on all of the above.
- [ ] All prior batteries green — no new regression since D-4a's sealed GREEN gate.

## §B — BIND-AT-OPEN slots (values are D-4a's SHIPPED, LIVE-VERIFIED reality — pre-D-5 readiness
pass, 2026-07-19; the Binder's job is to RE-confirm these still hold at actual open, not
re-derive them from scratch)

**§B.1 — Ontology (G-1/G-2/G-3/G-5's shared vocabulary, the vision's "e"):** `brahma_event_ontology`
live, **27 classes** (13 point / 9 interval / 5 chain). Full table, live-queried 2026-07-19:

| shape | classes |
|---|---|
| point (13) | achievement_recognition, bereavement, birth_anchor*, career_advancement, career_entry, childbirth, exam_outcome, illness_acute, marriage, property_acquisition, romantic_start*, surgery, travel_event |
| interval (9) | career_setback*, chronic_onset, financial_deception*†, major_gain, major_loss, parental_event, psychological_arc*†, relocation, spiritual_turn*† |
| chain (5) | business_launch, career_change, education_milestone*, foreign_settlement, separation |

(`*` = has a kill-switch; `†` = `self_report_non_discriminating=true`.) `platform/src/lib/lel/
event_ontology_shapes.ts`'s `validateClaimShape`/`assertClaimShape`/`checkKillSwitch` confirmed
importable and functioning.

**§B.2 — Substrate (A-0's CR-109/110/111, live-reprobed):** full-span birth→birth+100y activation
windows confirmed non-empty at the far edge (2080-2085 range returned 50 real rows). Single
disclosed dasha spine confirmed (Mercury MD under `vimshottari`/`lahiri_chitrapaksha`: exactly 1
row). Convergence windows confirmed served (`kala_temporal_bundle` 2026-2027: `convergence_count
=50`, matches the `kala_convergence` table). **All 3 PASS, live, this session.**

**§B.3 — Harness + A-5 baseline (G-lanes' mini-check target):** `a3_scoring_harness` (A-3) and
the A-5 runner reproduce byte-identically on a fresh live run this session (200,920-byte receipt,
exact match). Substrate: 62 LEL events, 55 scorable, 9205 dasha periods (unchanged from D-4a
close, confirmed by the pre-D-5 correction adding exactly 1 event — see the readiness report).
Baseline numbers per domain (pratyantar_lord, the only currently-scoreable model; midpoint_
triangle/transit_kernel remain `NotImplementedModelError` gaps — G-3's own model, once built,
becomes a 4th contender for D-4b, NOT scored here):

| domain | n | meanCRPS | skill vs shuffled | skill vs antiphase |
|---|---|---|---|---|
| general | 24 | 2419.03 | −2.0011 | 0.2486 |
| health | 6 | 2319.16 | −1.9292 | 0.3549 |
| marriage | 9 | 2494.68 | −2.2046 | 0.1508 |
| career | 11 | 2985.49 | −2.4026 | 0.0021 |
| wealth | 5 | 2765.95 | −2.3002 | 0.1226 |

`artifacts/D-4a/A-5/dry_run_receipt_v1_0.json` holds full per-event granularity (55 entries) —
this is the file G-lanes score against, not the summary tables above.

**§B.4 — Prospective ledger (G-5's target surface):** `brahma_prospective_ledger` live, 5 rows,
chart 482012f1, `configuration_signature` column confirmed `is_nullable=YES`, currently null on
all 5 — ready for G-5 to populate. LEL-append→outcome-matching hook confirmed still wired
(`matchOpenPredictionsForLelEvent` called from the live write route; the A-4 test-fixture row is
`lifecycle_status='matched'`, proving the hook fires end-to-end).

**§B.5 — Infra health (G-4's Cloud Run rebuild dependency):** sidecar reachable (live
`compute_natal_positions` call succeeded, PyJHora engine responding). `brahma-build-pipeline-job`
healthy (`Ready: True`, `executionCount: 209`, last execution succeeded). **Two flags carried
forward, not blocking, but the Binder should disposition them before G-4's rebuild step:**
(1) an orphaned `build_runs` row (`372b5cfa…`, D-3-era, `state='running'`, `ended_at=NULL`, tied
to a failed execution `lj545`) is still stuck — sweep/reconcile before G-4 trusts a clean
`build_runs` table state. (2) `amjis-mcp`/`amjis-sidecar`/`brahma-build-pipeline-job` images are
7-10 commits behind `origin/main` HEAD (last synced at D-4a's A-0/A-0-fix merges); confirmed the
gap contains zero `platform-mcp/`/`python-sidecar/` source changes (pure docs/migrations/
TypeScript-app-layer commits), so this is inert today — but G-2/G-3's new `platform/python-
sidecar/services/gochara_*` code WILL require a fresh sidecar deploy before it can run live; the
Binder should not assume the currently-stale sidecar image auto-picks up G-lane sidecar code.

**§B.6 — Item #3 correction (pre-D-5 hygiene, not a D-5 deliverable but affects G-lane inputs):**
the dialogues-2001 spiritual-arc correction (mis-quarantined during D-4a) is now live: chart
482012f1's `life_events` grew from 62→63; the correction is `spiritual_turn`-shaped (interval,
2001→present), chain-linked to 4 existing milestone rows. G-1's resonance map and G-3's λ_e for
the `spiritual_turn` class should reflect this corrected substrate, not the pre-correction state.

## §11 — Data-governance principle (ARC PLAN §11, binding arc-wide, restated for G-5's benefit)

Calibration/learning/scoring draws from exactly two sources for every user: (1) their LEL —
ground-truth events they deliberately provide; (2) explicitly registered ledger predictions (any
`generator_class`, including `native_intuition` — always an intentional, opt-in filing act). Chat/
consultation content is NEVER mined. G-5's engine-filed claims (`generator_class=engine`) are
themselves an instance of (2) — the engine files them as explicit acts via the same
`fileProspectivePrediction` path A-4 built, never as a side-channel write.
