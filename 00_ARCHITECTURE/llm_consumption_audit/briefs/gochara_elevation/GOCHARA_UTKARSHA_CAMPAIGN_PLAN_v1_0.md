---
artifact: GOCHARA_UTKARSHA_CAMPAIGN_PLAN_v1_0.md
campaign: GOCHARA-UTKARSA
version: 1.0
status: LIVE
created: 2026-08-10 (W5.3 docs-of-record lane)
ledger: LEDGER.md  # cross-link: campaign ledger in same directory
---

<!-- LEDGER CROSS-LINK: see LEDGER.md in this directory for the live wave-position
     table, adjudicator ruling record, and I-invariant restatement. -->

# GOCHARA-UTKARSA CAMPAIGN PLAN v1.0

Campaign: Gochara v3 elevation — bounded lambda formula + 12-mechanism grammar +
calibrated weight fitting + serving/DAG integration + replacement cutover.

Ledger: `LEDGER.md` (same directory — live wave-position table, ruling record, log)
Cross-campaign coordination: `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md`

## OBJECTIVE

Replace the v1 gochara scoring system (gochara_grammar + gochara_intensity + ka_gochara_sweep)
with a calibrated, classically-grounded v3 grammar that:
1. Implements a bounded [0,1] lambda formula with signed channels and self-normalizing thresholds
2. Wires 10 admitted mechanisms (classically cited, unit-tested, weight-fitted) + 2 structural-only
3. Integrates into the Kala layer DAG as a first-class asset
4. Replaces the v1 sweep writer as the authoritative gochara window source (Wave 6)

## I-INVARIANTS (binding)

| ID | Rule |
|---|---|
| I2 | NEVER edit services/gochara_grammar/, services/gochara_intensity/, services/ka_gochara_sweep/ |
| I5 | NEVER touch orchestrator code (FROZEN per ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md) |

## WAVE PLAN

### Wave 0 — Foundations
- W0.1: Campaign registry entry
- W0.2: Baseline builds (kala_gochara_windows_v2, kala_gochara_windows_v1 census)
- W0.3: Schema migration bundle (migration 556: kala_gochara_windows_v3, gochara_v3_calibration)
- W0.4: Grammar-v3 catalog (grammar_v3_registry.yaml, mechanisms/registry/*.yaml)

### Wave 1 — lambda-v3 bounded formula
- W1.1: Bounded [0,1] lambda core
- W1.2: Signed channels (positive/negative)
- W1.3: Vedha suppression
- W1.4: Self-normalizing thresholds
- W1.5: Decomposition (term_breakdown for ablation)

### Wave 2 — Mechanism wiring (9 waves, 12 mechanism toggle_keys)
- W2.1: w21_av_gating — Ashtakavarga bindu gating (BPHS)
- W2.2: w22_moorti_nirnaya — 4-tier sign-ingress quality (Phaladeepika Ch.27)
- W2.3: w23_tara_bala — 9-cycle Nava Tara modifier (Muhurta Chintamani)
- W2.4: w24_sade_sati — phase-quarter intensity + cancellation (BPHS)
- W2.5: w25_kota_chakra — malefic siege ring modifier (Kota Chakra tradition)
- W2.6: w26_real_eclipses — real bg_sky_calendar eclipse amplification (BPHS grahana)
- W2.7: w27_annual_stack + w27a/b/c — Tajaka year-lord, Tithi Pravesha, Sudarsana (3 sub-mechanisms)
- W2.8: w28_bhava_degrees — bhava cusp degrees from L1 chart_facts (structural_only)
- W2.9: w29_citation_resolution — citation string to verse_ref catalog (structural_only)

### Wave 3 — Infrastructure
- W3.1: Event coverage extension 6->27 event classes in gochara_resonance
- W3.2: Interval solver (root-solved threshold crossings + chain milestone scoring)
- W3.3: Multi-resolution hierarchy (era/month/day parent_window_id)
- W3.4: Century horizon materializer writer (decade-slice plan_substeps + delta fingerprinting)

### Wave 4 — Calibration
- W4.1: Lambda contenders (TemporalCurveModel for v1+v3 in scoring harness)
- W4.2: Negative control/noise floor (bootstrap 2-sigma CIs)
- W4.3: Ablation runner (ADJUDICATOR input) + UTK-R3 ruling: 10 admitted + 2 structural-only
- W4.4: Cross-chart pooled weight fitting (migration 561: gochara_v3_calibration)
- W4.5: Post-fit rebuild + calibration stamper + prospective ledger seeding
- W4.6: LEL mining (staged candidates from LIFE_EVENT_LOG + corpus artifacts)

### Wave 5 — Serving elevation + docs (IN PROGRESS)
- W5.1: Serving elevation (gochara3/w51)
- W5.2: DAG integration — v3 asset depends_on + count_sql + sibling registry (migration 562) — MERGED
- W5.3: Docs-of-record — mechanism_register.yaml + CURRENT_STATE update + LEDGER cross-link (this lane)
- W5.4: Writer repoint (gochara3/w54)

### Wave 6 — v3 replacement cutover (PENDING Wave 5 PASS)
- W6: Authority-seam cutover: ka_gochara_sweep -> kala_gochara_windows_v3 as authoritative source

## ADMITTED MECHANISMS (UTK-R3 ADJUDICATOR RULING)

See `mechanism_register.yaml` at `platform/python-sidecar/services/gochara_v3/mechanism_register.yaml`
for the full finalized register with all required fields per each mechanism.

| toggle_key | admission_state | weight_type |
|---|---|---|
| w21_av_gating | admitted | fitted |
| w22_moorti_nirnaya | admitted | fitted |
| w23_tara_bala | admitted | fitted |
| w24_sade_sati | admitted | fitted |
| w25_kota_chakra | admitted | fitted |
| w26_real_eclipses | admitted | fitted |
| w27_annual_stack | admitted | fitted |
| w27a_tajaka_year_lord | admitted | fitted |
| w27b_tithi_pravesha | admitted | fitted |
| w27c_sudarshana | admitted | fitted |
| w28_bhava_degrees | structural_only | structural_modifier=1.0 |
| w29_citation_resolution | structural_only | structural_modifier=1.0 |

## MIGRATIONS CLAIMED

| migration | purpose | status |
|---|---|---|
| 556 | gochara_generation schema (kala_gochara_windows_v3 + gochara_v3_calibration) | MERGED to main (#1138) |
| 561 | gochara_v3_calibration fitted weights (W4.4) | MERGED |
| 562 | gochara_v3_dag_integration (W5.2 DAG asset + count_sql) | MERGED |

## CROSS-CAMPAIGN NOTES

Per `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` (2026-08-10):
- R-COORD-1 (PROPOSED): SAMPURTI's Wave-2 G11 retirement of gochara-family legacy temporal surfaces
  is DEFERRED until UTKARSA's W6 cutover completes — joint execution required.
- R-COORD-2: After migration 556 merges, SAMPURTI re-derives sweep-corpus detectors
  generation-filtered before citing baselines.
- Yield policy: SAMPURTI yields during UTKARSA W6; UTKARSA yields otherwise under contention.
