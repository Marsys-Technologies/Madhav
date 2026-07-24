---
artifact: BRIEF_SARVA_SIDDHI
type: CAMPAIGN BRIEF (close ALL open serving/data gaps before UAT-DARPANA)
campaign: SARVA-SIDDHI ("all-accomplishment") — nothing dark, nothing stale, nothing unserved
version: 1.0
status: DESIGN-COMPLETE — native-commissioned via Cowork 2026-07-24. Native ruling supersedes
  all prior accept-as-dark dispositions (A-5/A-6 rescinded): EVERY open item closes with a real
  fix before Darpana opens. "What good is an asset which we have built which is dark and not
  servable — especially the crown jewel."
governing: CLAUDE.md §N · GOVERNANCE_INTEGRITY_PROTOCOL · PRE_DARPANA_READINESS_v1_1.md (state
  inherited) · STATIC_VIDHI_AUDIT_v1_1.md · this brief
exit: PRE_DARPANA_READINESS v2.0 = ALL items CLOSED-WITH-EVIDENCE (no accept-as-dark rows) +
  full Tier-B battery green → UAT-DARPANA unlocks.
---

# SARVA-SIDDHI — close everything, then hold up the mirror

## §0 — Native doctrine for this campaign (binding)

1. **No accept-as-dark.** Every open item gets a REAL fix. Disclosure of a gap is a stopgap,
   not a resolution; the instrument's value is served depth, and dark surfaces on default-
   compiled floors are product defects.
2. **Truth before work.** The register has produced stale rows twice (CR-56, and the suspected
   CR-68/CR-16 below). EVERY item is live-probed before being worked; stale items close as
   register-drift with evidence, not as engineering.
3. **Honesty in fixes.** Real computation only (§N B.10). A ranking axis is deterministic from
   existing data or it is not built. No fabricated rows to make a surface look alive. If an
   item genuinely cannot close without fabrication, HALT and present the evidence to the
   native — do not quietly re-dark it.
4. **The 165/300 question is settled by evidence.** The native's recollection: scoring moved
   event-driven (true — D-4b §0 reconciliation) and a successful full execution under new
   logic followed (unconfirmed). W-0 pulls the complete `build_run` history for
   `ka_gochara_sweep` + live row-spans of `kala_gochara_windows` and states what actually
   exists, per year-band, before any dispatch is sized.

## §1 — Wave plan (dependency-ordered; parallel where independent)

### W-0 — TRUTH PASS (first; blocks sizing of everything temporal)
Live-probe ALL 16 items; emit a verdict table (REAL-OPEN / STALE-CLOSED / PARTIAL + evidence).
Specifics: `build_run` history + substep ledger for `ka_gochara_sweep` (what ran, when, under
which logic, what errored); `kala_gochara_windows` live row-spans per year-band + event-class
(what serving data EXISTS today); CR-68 probe (`mechanism_retrodiction_get` — D-4b PR #688
suggests SHIPPED); CR-16 probe (`ganita_special_lagnas_get` chart_id mode — tool doc cites
CR-16 as addressed); re-confirm each remaining CR's factual premise. Register corrections for
every stale row. **Output: SARVA_SIDDHI_TRUTH_TABLE_v1_0.md — the campaign's work order.**

### W-1 — TEMPORAL CORE (crown jewel; starts on W-0's temporal verdict)
- **T-1** `DATABASE_URL` fix for the three gochara serving tools + redeploy + live-verify
  against EXISTING data (whatever W-0 found materialized serves immediately).
- **T-2-PRE (blocker; native+Fable firsthand-confirmed via Nirmāṇa 2026-07-24):** an ORPHANED
  `build_run` row for chart 482012f1 (the ~July-21 gochara sweep, `c9d722d5`/job `n68qz`) is
  stuck in `building` state — Nirmāṇa shows it "BUILDING" with ~70h elapsed (physically
  impossible; the job died at its 6h ceiling ~64h ago). Consuming ZERO compute (confirmed: 70h
  elapsed impossible for Cloud Run; graceful UI Stop found no worker to acknowledge). The UI
  graceful Stop was requested but CANNOT reconcile it (no live worker); a global refresh
  confirms the DB row itself is stuck non-terminal. **This blocks any fresh T-2 dispatch** via
  the application-level "a build is already running" guard (note: the pg advisory lock already
  auto-released when the dead job's connection closed — session-scoped). **Action:** force the
  orphaned `build_run` row terminal (`state → error`/`cancelled`, `ended_at → now`) via proper
  tooling (cockpit-admin reconcile endpoint or a governed DB write — NOT a hand-written row),
  verify Nirmāṇa clears the "BUILDING" banner, THEN proceed to T-2. Reconciliation-of-stale-
  build_run is a known class (BUILD_TRACKER_HARDENING_HANDOFF) — if a reusable reaper/force-
  abort affordance is cheap, add it so this self-heals in future.
- **T-2** Complete `kala_gochara_windows` materialization for 482012f1 across the FULL
  birth→birth+100y span (whatever W-0 shows missing; only AFTER T-2-PRE clears the zombie
  row): resumable dispatches sized from W-0's
  real per-substep timing (no inherited estimates), job timeout raised/split so no 6h death,
  §N.3-safe. This ALSO satisfies D-6's hard precondition (v1 corpus complete) — record that
  linkage. Then all three views live-verified: real, shape-correct rows in past AND forward
  spans.
- **T-3** CR-37: yoga-activation dating — root-cause why activations are undated; fix the
  ka_* join (firings × dasha periods) so catalog+fired yogas carry real activation windows.
- **T-4** CR-66: Phala domain anchors — root-cause zero-anchor state; extend/repair the ph_*
  anchor build so wealth/career/health/marriage/spirituality anchors exist with real derivations
  (FROZEN contract respected; delete-then-insert; NO-SCORING gate honored — anchors are
  deterministic phala, not calibration).
- **T-5** §N.6 disclosure repairs: `phala_predictive_anchors_get` silent empty → honest
  empty_reason; `yoga_activation_scan` floored. (Small; do first inside W-1.)

### W-2 — PREDICTION LOOP (independent; parallel with W-1)
- **P-1** Standing predictions end-to-end: locate the campaign's filed claims (artifacts vs
  ledger rows), create/repair `brahma_prospective_ledger` rows with ORIGINAL pre-registration
  provenance (`backfilled_from_artifact: true`, source + original date — never fresh-filed),
  fix the serving chain, live-verify `standing_predictions_read` returns Sat–Jupiter Apr–Aug
  2027 + Ketu-MD shape + Venus-MD 2034 on a wealth/timing plan. Opus review on provenance.

### W-3 — REMEDY CORE (independent; parallel)
- **R-1** CR-67 real fix: root-cause why `bodha_remedies_search`/bo_upaya contributes nothing
  domain-joined (join bug vs missing domain tagging vs empty upstream); repair so a domain
  deepdive's remedy band serves real, cited, domain-relevant remedy rows.
- **R-2** CR-69: leverage_index — deterministic composite (domain load-bearing weight ÷ graha
  capability × forward daśā runway) computed from EXISTING L1/L2 data; lands on the serving
  rank; formula documented + citation-backed where classical weights are claimed.

### W-4 — DETECTORS + RANKINGS (independent; parallel; the long tail closed for real)
- **D-1** CR-130: Jaimini spiritual yoga family — pravrajyā/sannyāsa detectors added to the
  yoga engine (same extension pattern as D-1.6's detector additions), BPHS/Jaimini citations
  mandatory, firings-authoritative surface, verified against 482012f1 + a control chart.
- **D-2** CR-61: arudha/UL ranking — deterministic salience rank (AL/UL/A2/A11 prominence ×
  occupancy/aspect load) on the arudha serving surface.
- **D-3** CR-64: nakshatra-semantic ranking — deterministic (own-star/dispositor-chain/tara
  weight) so the layer ranks instead of dumping.
- **D-4** CR-24: mechanism chain/circuit motifs served first-class (the 10→8→12→10 specimen
  class as named, valenced rows, not raw subgraph).
- **D-5** CR-73: bespoke dosha cancellation — close the narrowed-open residual (per-chart
  cancellation checks live, not stub-half).
- **D-6** CR-30: KP cusp/sub-lord dedicated face (first-class tool face over the existing
  chart_facts category route).
- (Items W-0 proves stale — expected CR-68, CR-16 — close as register-drift here, no code.)

### W-R — RELOCATED (native ruling 2026-07-24): the retrieval-plane full audit is NOT part of
this campaign. It executes as **UAT-DARPANA Phase 0.7** (see UAT_DARPANA_DESIGN_v1_0.md §5,
v1.3) — same six-lane spec (R-0..R-5), moved so the in-flight SARVA-SIDDHI closes on its
original scope without late injection. W-5's exit does NOT require W-R; the retrieval audit
gates Darpana's Phase 1 instead, inside Darpana's own governance. The spec text below is
retained for reference only and is SUPERSEDED by the Darpana design's §0.7.

*(superseded reference text follows)*

The concurrently-elevated retrieval engine (its own W-0..W-6 waves + residual layers, parallel
session) is the substrate EVERY Darpana query rides — its correctness must be a CONTROLLED
variable before the UAT. Fable strategy ruling stands: correctness gates deterministically
here; the EXPERIENCE face is Darpana's §6.3 track. Sub-lanes:

- **R-0 — Audit scope map.** Read `RETRIEVAL_STRATEGY_v1_0.md` (the yardstick — every doctrine
  commitment RS made: depth classes, RS-4 valve, density contracts, envelope v3, budgets) +
  the retrieval-plane elevation plan and its W-0..W-6 + residual wave records. Emit the audit
  checklist: every capability, every RS commitment, every envelope contract — the analogue of
  STATIC_VIDHI_AUDIT's finding frame.
- **R-1 — Conformance battery, LIVE.** Full battery against the DEPLOYED server (density
  census §N.6, planner regression, per-tool smoke, response-budget tests) + the census harness
  asserting every capability's density_contract (byte budgets, facets, empty_reason) on real
  chart data (482012f1).
- **R-2 — CONCEPT-COVERAGE CENSUS (native-directed; DR-18 at the serving layer; the wave's
  heart).** Enumerate the FULL astrological-concept inventory FROM THE DATA ITSELF (distinct
  fact_category × fact_key families across chart_facts, chart_divisionals, bodha_*, kala_*,
  phala_*, mimamsa_* + reference tables): ashtakavarga bindus natal + per-varga +
  sarvāṣṭakavarga, special lagnas (Indu/Śrī/Ghaṭī/Horā/Bhāva), upagrahas, sahams, sphuṭas,
  arudhas A1–A12 + UL + graha-arudhas, chara/sthira karakas, avasthās, tārā-bala, deity
  attributions, horā classes, vimśopaka, puṣkara/gaṇḍānta/mṛtyu-bhāga/22nd-drekkana,
  kāla-sarpa per varga, graha-yuddha, argalā, parivartana, sambandha, aspect families
  (Parashari/Jaimini/Tājaka), KP cusps + sub-lords, ayurdāya, vaidya-medical, yoga catalog +
  firings + NBRY grounds, doṣas + cancellations, all dasha systems, sade-sati, transit rules,
  muhurta, panchanga, and EVERY other concept family the enumeration surfaces — the list
  above is a floor, not a ceiling. For EACH concept: map → serving capability → live probe →
  verdict **SERVED / REACHABLE-BUT-EMPTY / UNREACHABLE**, with the probe receipt. Output: the
  Concept-Coverage Matrix (full, per-concept, appendix-grade). UNREACHABLE concepts get a
  serving route built or a CR with a named owner — never silence. (Temporal surfaces: census
  grades REACHABILITY here; W-1 fixes materialization in parallel — verdicts cross-referenced,
  not blurred.)
- **R-3 — PERSONA + VOICE AUDIT (native-directed; §N.1 lexicon law enforced at serving).**
  The defect: astrological questions answered with technical internals (DB volumes, table
  names, fact_id strings in prose, CR numbers, internal layer-speak — a violation of the
  LOCKED §N.1 external-lexicon standard, not a style issue). Three parts: (a) INVENTORY —
  probe a representative capability sample in user-voice; collect verbatim leakage specimens
  classified by type (schema-speak / provenance-speak / register-speak / layer-speak /
  volume-speak); (b) ENVELOPE HYGIENE — structurally separate astrological payload from
  technical metadata in the envelope (provenance/diagnostics machine-consumable, clearly
  demarcated, never interleaved with payload prose) so an answerer can serve a clean
  astrological voice by construction; (c) PERSONA AXIS — `intent_classify` gains a persona
  dimension (user | developer/operator) inferred from the question's own language, DEFAULT
  user; technical blocks served only on developer intent. Fixes land in this wave; Darpana's
  JARGON tag later measures whether they held.
- **R-4 — Fix everything found.** Every red from R-1, every UNREACHABLE from R-2, every
  leakage class from R-3: real fixes per §0 doctrine, re-run to green.
- **R-5 — THE REPORT (Fable-consumption contract, per the native).**
  `RETRIEVAL_AUDIT_REPORT_v1_0.md` at the same rigor as this campaign's own close reports,
  designed for Fable 5's analysis in the native's Cowork session: audit frame + per-item
  verdicts each traceable to a committed probe receipt; the full Concept-Coverage Matrix as
  appendix (no summarized-only rows); the leakage-specimen inventory VERBATIM; before/after
  evidence for every fix; register deltas; the live-conformance receipt naming the
  retrieval-plane version/commit Darpana will assess; honest residual list (anything not
  closed, with reason + owner — expected: none, per §0). Nothing summarized-only; any
  unprobeable item says `not_probed: <reason>`, never silently absent.

*(end of superseded reference text — W-5's exit does NOT include these requirements; they
live in UAT-DARPANA §0.7's exit gate.)*

### W-5 — FULL RE-VERIFICATION + EXIT (after all waves)
Re-run the complete Tier-B battery (all 8 floor smokes — zero silent empties, zero darks on
default floors), plus one targeted probe per item fixed in W-1..W-4 (the fix serves REAL rows
through the live connector on a compiled plan). Fresh-context Opus adversarial verifier over
the whole battery; no green on the primary runner alone. Publish PRE_DARPANA_READINESS v2.0:
every item CLOSED-WITH-EVIDENCE; registers reconciled (no row contradicts live truth — the
recurring drift class gets a standing note); SESSION_LOG close. **Exit met → Darpana unlocks.**

## §2 — Execution model
Sonnet base Coordinator; agentic swarm, one lane per worker, parallel across W-1/W-2/W-3/W-4
after W-0. Opus step-up for: W-0 verdicts, all root-cause analyses, detector/ranking design
(astrological correctness), provenance design (P-1), and every verifier. Effort medium,
raised only where strained; step-ups recorded. Halts ONLY per §0.3 (fix impossible without
fabrication) or sealed-split contact. Long-running dispatches (T-2) are monitored, chunked,
resumable — the campaign does not claim close while any dispatch is unfinished.

## §3 — Scope guards
FROZEN orchestrator untouched (new/changed writers conform to WriterBase); sealed split +
§11 untouched; three-copy vidhi parity if any registry file is touched; calibration values
untouched (T-4 anchors are deterministic phala, not calibration; L5 stays structural).
Each lane its own worktree/PR; CI green; dependency-ordered merges.
