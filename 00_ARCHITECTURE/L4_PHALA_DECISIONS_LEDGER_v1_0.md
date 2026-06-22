---
artifact: L4_PHALA_DECISIONS_LEDGER_v1_0.md
canonical_id: L4_PHALA_DECISIONS_LEDGER
version: 1.0
status: DRAFT — authoritative record of every L4 Phala design decision + rationale from the planning conversation; spine for all draft briefs
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The single durable record of WHAT was decided and WHY across the L4 Phala supreme-expansion
  planning conversation. Every native ruling, every code-verified correction, every architectural
  choice — captured with its rationale so nothing is lost to chat-context decay. All draft briefs
  (ph_* enriched/new, M9 activation, U1/U2 upstream) reference the decision IDs here. Marked DRAFT
  because the final plan is gated on L4_PHALA_PROD_RECONCILIATION_v1_0.md.
related:
  - 00_ARCHITECTURE/L4_PHALA_AUDIT_v1_0.md (the initial 6-asset audit + 3 corrections)
  - 00_ARCHITECTURE/L4_PHALA_CAMPAIGN_PLAN_v1_0.md (draft 6-asset plan — to be SUPERSEDED by the 9-asset revision)
  - 00_ARCHITECTURE/L4_PHALA_SUPREME_EXPANSION_v1_1 (the 8 value-adds + M9 + upstream enablers)
  - 00_ARCHITECTURE/L4_PHALA_PROD_RECONCILIATION_v1_0.md (the verification gate before final authoring)
---

# L4 Phala — Decisions Ledger v1.0 (DRAFT)

> Every decision below is tagged `[NATIVE-RULED]` (the native decided), `[CODE-VERIFIED]` (a fact
> established from the actual code/schema), or `[COWORK-PROPOSED]` (Cowork's recommendation, pending).
> The rationale column is the point of this document — it preserves the *why*.

---

## §1 — Scope & sequencing decisions

| ID | Decision | Type | Rationale |
|---|---|---|---|
| **D1** | L4 Phala built to **FULL AMBITION** (Tier 1+2+3 of the supreme expansion) | `[NATIVE-RULED]` | The substrate (embeddings, graph, discoveries, multi-dāśā, multi-school) is already built across L0–L3; building a thin L4 would leave genuine capability unused. "Make it supreme using any tech/infra." |
| **D2** | **Upstream reopens FIRST**, then L4: U1 (L1 multi-dāśā) → U2 (L3 lifetime+Prāṇa) → re-seal L1/L3 → then 9-asset L4 on the enriched substrate | `[NATIVE-RULED]` | Cleanest dependency order. L4 consumes finished inputs; no wiring half-built features into a moving target; no rework. Slower to first L4 output but correct. |
| **D3** | **Prod-truth reconciliation BEFORE authoring U1/U2/the L4 revision** | `[NATIVE-RULED]` | The documented build-state was wrong FOUR times this session (see §4). U1's true size (heavy reopen vs. build-run vs. already-done) is a data-plane fact unreadable from code. Verify, then plan. |
| **D4** | Legacy 2026-06-05 WS-2 `phala.*` code = **audit-then-mostly-rebuild** (harvest logic, rebuild architecture against the frozen orchestrator) | `[NATIVE-RULED]` | Legacy predates the frozen orchestrator + underscore convention + uses the retired FORENSIC-via-forensic_render source. The *logic* (calibration ladder, leakage discipline) is gold; the *architecture* is a dead-end. |

## §2 — The calibration boundary (the hardest call)

| ID | Decision | Type | Rationale |
|---|---|---|---|
| **D5** | **Calibration: falsifiability SCAFFOLDING in L4, ALL SCORING in L5.** L4 makes every prediction impeccably falsifiable (structured falsifier + evaluation date + empty outcome hook) and ships confidence **honestly labeled as structural, not-yet-empirical**. NO backtest in L4. | `[NATIVE-RULED]` (after full discussion) | Three reasons won the call: (1) **57 LEL events are statistically too thin** to calibrate per-domain (~9/domain) — a prior from 9 points is noise dressed as rigor, potentially worse than none. (2) **Leakage/circularity** — the same events ground `ph_sodhana`, seed the LEL, were partly disclosed post-framework, and the L2 signals were built *knowing* this native's life; a clean backtest may need a non-native chart = L5 apparatus. (3) **Layer discipline** — L5 Mīmāṃsā EXISTS to own scoring; "just one backtest in L4" is the camel's nose; and L5 is the very next campaign. |
| **D6** | `ph_pramana` is therefore a **falsifiability-scaffolding asset**, NOT a calibration asset. It emits machine-checkable falsifiers + eval dates + outcome hooks and hands them UP to L5. | `[NATIVE-RULED]` | Direct consequence of D5. Keeps the L4/L5 line clean: L4 makes predictions *L5-ready*; L5 does the scoring loop. |
| **D7** | The L4/L5 test: **"does it improve a prediction NOW (L4) or score predictions OVER TIME (L5)?"** | `[COWORK-PROPOSED]`, accepted | The clean discriminator. The first backtest scores predictions → L5. Making a prediction falsifiable → L4. |

## §3 — Asset set & reuse decisions

| ID | Decision | Type | Rationale |
|---|---|---|---|
| **D8** | Asset set grows **6 → 9**. Enriched: `ph_nimitta`, `ph_phaladesa`, `ph_pratikara`. New: `ph_sankrama` (cross-domain spillover), `ph_pramana` (falsifiability scaffolding), `ph_anudhyana` (discovery-deep-prediction — optional; may fold into ph_nimitta). Unchanged: `ph_muhurta`, `ph_sodhana`, `ph_suddha_sodhana`. | `[NATIVE-RULED]` (full ambition) + `[COWORK-PROPOSED]` shape | The latent substrate demands new surfaces (spillover, falsifiability) and enrichment of the existing anchors with graph/discovery/embedding/robustness/consensus axes. |
| **D9** | Add **`ph_phaladesa`** (composite outlook dossier) — the native-facing whole-chart-read surface | `[NATIVE-RULED]` (earlier in session) | The 5 registered placeholders had no composite; this is the "dish, not ingredients" surface, proven by legacy `phala.outlook`. |
| **D10** | **Reuse rule: READ-asset → CALL-service → RECOMPUTE-PyJHora-ONLY-if-absent.** Stated as a documented PRINCIPLE in the campaign plan, NOT a per-brief hard gate. | `[NATIVE-RULED]` | Code-verified that zero-duplication is achievable (every subsystem is a readable per-chart asset). PyJHora call justified ONLY for `ph_sodhana` rectification (hypothetical birth-times not in L1) + Tājaka varsha 49+. Trust the swarm to follow the principle rather than gate every asset. |
| **D11** | **Time-index EVERY parallel subsystem into the prediction stream** — not just the structural convergence spine. Medical, vastu, nakshatra, yoga, sade-sati, tajaka each produce domain-tagged time-indexed predictive anchors. | `[NATIVE-RULED]` | The subsystems were readable but the draft predicted only off structural signals. The native's concern: use the FULL BREADTH. Mechanism already exists (subsystems → `bodha_msr_signals` → `ka_yojaka` predicate binding → `ka_sangam` scoring); the work is ensuring subsystem signals are IN the binding and surfaced as domain anchors. No rebuild. |
| **D12** | **Rectification compute via PyJHora** (`ph_sodhana`) — `[NATIVE-RATIFY]` pending. `compute_ascendant` is in-process; turn the legacy stub into a real computation, leakage discipline preserved. | `[COWORK-PROPOSED]`, recommended | Code-verified `pyjhora_adapter/houses.compute_ascendant(jd_ut, ayanamsha, lat, lon, tz)` returns the ascendant to fractional degree at any time; PyJHora is the sealed engine (no JH-parity gate). This is the single biggest value-add and the ONE legitimate PyJHora call. |
| **D13** | **G-LADDER** — anchor confidence = deterministic transform over `ka_sangam`'s real I-16 convergence score + independence count, NOT hand-assigned. `[NATIVE-RATIFY]` pending the exact mapping. | `[COWORK-PROPOSED]`, recommended | The legacy hand-assigned confidences + hand-typed `SIG.MSR.*` constants violate anti-drift. Derive from real windows; cite real ids. |

## §4 — Code-verified corrections (the doc was wrong; trust code+prod)

| ID | Correction | Type | Detail |
|---|---|---|---|
| **D14** | **Migrations start at 330, not 251.** | `[CODE-VERIFIED]` | `migrate.ts` reads BOTH `platform/migrations/` (max 329) AND `platform/supabase/migrations/` (L3 ended 250), merged in lexical filename order. Cross-dir collisions already exist (174,223,239,240,250). Collision-safe L4 = 330+ in `supabase/migrations/`. The "two-174 trap." First migration also drops deprecated `kala_timeline` (CF.L3.2). |
| **D15** | **Legacy L4 `phala.*` code EXISTS** (2026-06-05 WS-2). | `[CODE-VERIFIED]` | The handoff was silent on it. `brahmagyan/phala/l4_*.py` + `brahma_phala_*.sql` + `platform-mcp/phala_*.ts`. Reference-only; harvest logic per D4. |
| **D16** | **Multi-dāśā is largely BUILT, not definitions-only.** | `[CODE-VERIFIED]` | `ga_dashas_writer.py` has `SYSTEMS = [vimshottari, yogini, ashtottari, chara_karaka, naisargika, mudda, kalachakra]` (7) with real `compute_*_system` functions; orchestrator plans 35 substeps (7×5 ayanāṃśas). CONFLICT: L1 seal attributes 536,471 rows to Vimśottarī; `l1_dashas.py` comments "MD ONLY" for non-Vim. **UNVERIFIABLE from code — gated on reconciliation Q1.** So U1 = verify-then-complete, NOT a heavy reopen. |
| **D17** | **A whole MULTI-SCHOOL engine exists (M9 macro-phase)** — built, tested (78 green), CLOSED, but DORMANT + partly hardcoded. | `[CODE-VERIFIED]` | `platform/src/lib/schools/` — 7 school engines (Parāśarī/Jaimini/Tājika/KP/Nāḍī/BNN/Yoginī) + `convergence_calculator` + `school_runner`. Headline result: "5/5 domains HIGH convergence." NOT wired/persisted (migrations 057–060 in `_archive/`); signal scores partly hardcoded to this native via `defaultSignals()`. |
| **D18** | **Make M9 chart-general + wire into L4** as a first-class consensus confidence axis. | `[NATIVE-RULED]` | De-hardcode the engines to read real L1–L3 data live; persist convergence per domain; wire into `ph_nimitta`/`ph_phaladesa`; resolve [VARSHA_KUNDALI_PENDING] (via `ga_tajaka`) + [TRANSIT_DATA_PENDING] (via `ka_gochara`). Exact lift sized by reconciliation Q3/C2. |
| **D19** | **The meta-lesson:** this project's docs misstate build-state in BOTH directions (L3 "engines exist"=false; L4 "only Vimśottarī"=undersold). | `[CODE-VERIFIED]` (pattern) | Always verify against code + prod, never the handoff/inventory. This is why D3 (reconciliation-first) is non-negotiable. |

## §5 — The reuse map (code-verified; D10/D11 basis)

Every parallel subsystem is a READABLE per-chart asset (no recompute):

| Subsystem | Asset / table | What L4 reads | Action |
|---|---|---|---|
| Nakshatra | `chart_facts` (ga_nakshatra, 1,802 rows) | KP lords (star/sub/sub-sub), dispositor chains, Tāra Bala, gandanta, padas | READ |
| Astrovastu | `ga_vastu_planet_direction_map` (40) | graha→direction impact (weakened/neutral/strengthened) | READ |
| Medical | `ga_medical` (45, disclaimered) | dosha aggravation, organ/body-part watch, indication strength | READ |
| Yoga | `ga_yoga_firings` | fired yogas + constituent_fact_ids + strength + activation hooks | READ |
| Dignity/Condition | `ga_condition_composite` (45) | condition_score, avastha, motion, friendship, peak/weak dasha hooks | READ |
| Sade Sati | `chart_facts` (ga_sade_sati, 11,019) | cycle/phase/quarter/dhaiya/kantaka/ashtama/janma + overlays + cancellation | READ |
| Tājaka (annual) | `l1_tajik_varsha_year_lords` (240) | muntha, varshesha, tajik yogas per varsha 1–48 (49+ on-demand) | READ (HYBRID for 49+) |
| Prashna | `ga_prashna_judgment` (0 for native) | — horary-only — | SKIP (out of scope) |

Services callable by L4 (don't reimplement): `ka_graha_sancara` (positions at any T),
`ka_dasha_kala` (active dasha periods + cross-system agreement), `ka_gochara` (transit search),
`ka_muhurta_seva` (panchāṅga/muhūrta + Tāra Bala), `ka_tulana` (cross-pattern prioritization, I-11).
PyJHora adapter: CALL ONLY for `ph_sodhana` rectification + Tājaka varsha 49+ (D10).

## §6 — Inherited frozen standards (unchanged, carried from L3)
- Frozen orchestrator contract: `@register('ph_*')` `WriterBase`; `run(ctx)`; never commit
  `ctx.db_conn`; never write `asset_throughput`; `WriterResult(asset_id=, rows_inserted=)` (kwarg is
  `rows_inserted` — L3 BUG-3 was `rows_written`); delete-then-insert idempotency; `$1` count_sql.
- Ratified params inherited unchanged: I-7, I-8, I-11, I-16, I-17, confidence labels.
- Anti-drift: every L4 row references a lower-layer id and inherits its value; ZERO writes outside `phala_*`.
- The HARD SEAL GATE: the live VISUAL cockpit (Cloud Run revision == merge SHA; assets lit with real
  counts; zero error/missing_table) is the ONLY seal signal — green JSON / "SEALED" reports /
  unmerged-branch fixes are all false positives. (The #1 L3 lesson, burned ~4×.)
- Model policy: Gemini/DeepSeek (Anthropic banned unless native asks). Deterministic-first.
- Cowork plans/authors; Claude Code in Antigravity implements.

## §7 — What's still OPEN (pending) — RESOLVED at §8 (2026-06-21 reconciliation + ratification)
- ~~The reconciliation (D3)~~ → COMPLETE (GATE A). ~~Two NATIVE-RATIFY gates~~ → ratified (D12→D20, D13→D21).
  ~~ph_anudhyana~~ → FOLDED (D22). The 9→**8**-asset plan + briefs → finalize at GATE C.

## §8 — GATE A reconciliation results + GATE B ratifications (2026-06-21)

### §8.1 — Reconciliation findings (prod-true; from `L4_PHALA_PROD_RECONCILIATION_v1_0.md`, status COMPLETE)

| ID | Finding | Impact |
|---|---|---|
| **D20a** | **U1 = WIRE ONLY.** All 7 dāśā systems are at level 4 in prod (vimshottari 51,037 · yogini 83,740 · ashtottari 32,960 · chara_karaka 138,535 · kalachakra 106,049 · mudda 102,205 · naisargika 21,945 = 536,471). The L1 seal's "536k Vimśottarī" was the all-systems total, mislabeled. | U1 = zero code/schema. Consume `dasha_consensus_count` in ph_nimitta Axis 6 + M9. **U1 needs NO L1 re-seal.** Corrects D16. |
| **D20b** | **M9 = FULL ACTIVATION.** Tables 057–060 are in `_archive/`, NOT applied to prod; no `%school%` table exists; `school_runner` has zero callers outside `lib/schools/`; all 7 engines hardcoded to `ABHISEK_CHART`/`defaultSignals`. | M9 Tasks A+B+C+D all required (de-hardcode + resolve-pending + persist + wire). Confirms D17/D18. |
| **D20c** | **All L4 inputs PRESENT.** convergence 660 · obstruction 60 · bhavishya 50 · darshana 300 · jivana_parva 739 · activation 66,738 · signals 66,738 · embeddings 66,738 · **discoveries 1,505 (was 1,411 — UPDATE EVERYWHERE)** · cdlm_cells 70 · yoga_firings 5 · condition 45 · medical 45 · vastu 40 · tajaka 240. | No upstream input gaps. **`bodha_discoveries` = 1,505** in ph_nimitta Axis 4 + plan. |
| **D20d** | **U2 = score enrichment + lifetime + Prāṇa.** `chart_dashas` ceiling = level 4; `kala_jivana_parva` (739 rows) has `avg_effective_score = NULL` throughout (`parva_quality='transitional'`). Scoring never applied. Prāṇa (level 5) genuinely net-new. | U2 is real work: (1) score the null jivana_parva, (2) lifetime expansion, (3) Prāṇa level-5 (selective). **U2 reopens L3 → L3 re-seal authorized (D27).** |
| **D20e** | **Migrations: prod max = 325; 326–329 authored but NOT applied.** 326 (L2 floors), 327 (is_active), 328 (RETIRED constraint), 329 (drop ka_transit_almanac). `kala_timeline` exists with 0 rows. | **GATE A7/F5 OPERATOR ACTION:** apply 326–329 to prod before kickoff. L4 starts at **330** (confirms D14); mig 330 DROPs `kala_timeline` (CF.L3.2). |

### §8.2 — GATE B ratifications (native, 2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D20** (was B1) | **G-RECT** — PyJHora `compute_ascendant` as rectification oracle for ph_sodhana | **RATIFIED YES** | Only sealed, deterministic, non-JH option; rectification value depends on it entirely. |
| **D21** (was B2) | **G-LADDER** confidence multiplier within ladder ceilings | **RATIFIED: `f = max(0.5, convergence_score)`** (clipped at 1.0). Cowork default; native may override to pure-linear `f = convergence_score` at brief-finalization. | The ladder ceiling already encodes evidence strength; the multiplier should MODULATE, not annihilate. The 0.5 floor prevents double-penalizing a weak-but-REAL convergence window (it exists because the structure fired). |
| **D22** (was B3) | **ph_anudhyana** — own asset or fold? | **FOLD into ph_nimitta Axis 4** | Axis 4 already does full discovery-seeding (1,505 discoveries → phala_anchors tagged `discovery_seeded` with the discovery's own falsifier + why_an_acharya_misses_it). A separate asset duplicates it. |
| **D23** (was B4) | **ph_sankrama lag model** | **DETERMINISTIC RULE, no native gate.** `lag_days = round(90 × (1 − linkage_strength) × (1 + asymmetry_score))` | Monotone in the right directions (stronger + more asymmetric → shorter, more confident lag). Swarm implements + documents; no halt. |
| **D24** (was B5) | **U2 infra** | **SELECTIVE.** Coarse lifetime always-stored + Prāṇa only for top-N convergence windows (e.g. top 50). No dedicated Cloud Run batch. | Keeps row/compute budget bounded; no new infra. Coarse-lifetime + fine-5-year tiers coexist in chart_dashas via level_n semantics. |
| **D25** (was B6) | **Final asset count** | **8 assets.** Enriched: ph_nimitta, ph_phaladesa, ph_pratikara. New: ph_sankrama, ph_pramana. Unchanged: ph_muhurta, ph_sodhana, ph_suddha_sodhana. | Follows from D22 (ph_anudhyana folds). |
| **D26** (was B7) | **Launch scope** | **SINGLE autonomous wave** with internal wave DAG: U1 (wire) → U2 (score+lifetime+Prāṇa) → re-seal L3 → M9 (activate) → 8×L4 → visual seal. **+ internal SPINE-FIRST hard gate after ph_nimitta** (prove one anchor across all 8 axes before fan-out). | U1 trivial; self-healing pattern handles M9's de-hardcode lift; Conductor enforces ordering. Spine gate = the L2/L3 discipline that made autonomous builds safe. |
| **D27** (was B8) | **Re-seal authority** | **YES on L3** for U2 (genuinely reopens L3 — swarm may version-bump `L3_KALA_CLOSE` when U2 ACs pass). **NO L1 re-seal** (U1 wire-only changes no chart_dashas rows). | Upstream-first reopens sealed L3; U1 touches no L1 data (D20a). |
| **D28** (was B9) | **M9 chart-generality proof** | **SYNTHETIC FIXTURE NOW** + Abhinandan `1c826d5a` as later real-chart validation when Phase E opens. | The de-hardcode generality risk ("does a different chart yield different scores?") is integrity-critical and must be GATED inside the autonomous run — deferring lets the central M9 failure mode through ungated. A synthetic fixture gates it without coupling L4 kickoff to the Phase E operator gate. |

### §8.2b — GATE C brief-finalization decisions (2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D29** | **Prāṇa (level-5) DROPPED from U2.** U2 = lifetime convergence + jivana_parva null-score fix ONLY. | **native-ruled** | (1) The birth time is itself being rectified (ph_sodhana) — daśā-boundary-derived sub-week precision would EXCEED the input certainty (false precision), contradicting the calibrated-honesty discipline. (2) `ka_sangam`'s transit `peak_date` already delivers fine timing on CERTAIN ephemeris ground (not birth-time-sensitive daśā boundaries). (3) Classical Prāṇa-daśā is muhūrta-grade on a VERIFIED birth time, not life-prediction. Preserves the sealed L1 `max_level≤4` invariant; no `chart_dashas_prana` table. If post-rectification electional Prāṇa is wanted, it becomes its own enabler on a verified birth time. |
| **D30** | **U1 = ZERO new storage.** Surface dāśā consensus via the EXISTING `chart_dashas.concurrent_system_lords_jsonb` (L1, mig 211) → `KaDashaKalaService` → ph_nimitta chain. No column on kala_convergence/chart_dashas. | **native-steered** ("leverage the existing convergence architecture") | The cross-system concurrency is ALREADY computed + stored at L1 (the ga_dashas concurrency post-pass) and derived per-window by the service. Adding a column would duplicate an existing fact. Only new write = `dasha_consensus_count` on phala_anchors (L4's own table). |
| **D31** | **U2 lifetime tier defaults:** daśā-boundary-anchored windows + a `horizon_tier` ('near'\|'lifetime') column on kala_convergence; jivana_parva null-fix in-scope. | **Cowork default, native-locked** | Keeps the lifetime row budget bounded (one eval per daśā boundary, not calendar sampling); the two tiers coexist queryably; the null-fix resolves automatically from the lifetime run. |

### §8.2c — Convergence enrichment + naming (2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D32** | **NEW upstream enabler U3 — Convergence Currents Enrichment.** Enrich the I-16 convergence score with the missing currents: ashtakavarga transit potency, eclipse proximity, transit-to-transit, stations/retrograde, vedha cancellation, Tājika annual reinforcement, school consensus. | **native-ruled** | Code-verified: the I-16 score uses ONLY `constituent_lord_transit` (transit-to-natal of the activated lord, weight 0.30) among transit currents. But `ka_gochara` ALREADY computes eclipse/transit-to-transit/stations/multi-planet-confluence (unused by the scorer), and we have ashtakavarga (`chart_facts`, 96 bindu/ayanamsha) + vedha (`bg_transit_rules` mig 266) + Tājika (`ga_tajaka`) data. Enriching the currents makes EVERY prediction (5yr + lifetime) more accurate at the SOURCE — every ph_nimitta anchor inherits the convergence score. Highest-leverage accuracy improvement found. |
| **D33** | **U3 weight authority: Cowork proposes, swarm tunes within bounds.** | **native-ruled** | Re-opening the ratified I-7/I-16 weights is deliberate. Cowork proposes a re-normalized weight set (old+new currents summing to 1.0) with per-current rationale + documented bounds; the swarm tunes within those bounds via internal-consistency checks (no per-value native gate). Preserves the weights-are-native-judgment discipline while enabling autonomous refinement. |
| **D34** | **"M9" is DEAD legacy naming — purge it.** The multi-school triangulation engine (`platform/src/lib/schools/`) is referred to by what it IS, not its legacy macro-phase tag. Workstream renamed **"School Consensus Activation"** (enabler code: U4). | **native-ruled** | "M9" was the legacy build-phase label; the legacy was retired. The engine code is real; the name is dead. All briefs/plans use "School Consensus Activation" / the 7-school triangulation engine. |
| **D35** | **U3 ships 6 currents now, school-consensus (C13) in a 2nd pass post-U4.** U3 weights ACCEPTED as proposed (§3.1, swarm tunes within bounds); per-current breakdown stored for explainability; U3's currents land BEFORE U2's lifetime run (one enriched build covers both tiers). | **native-ruled** | The 6 currents (ashtakavarga/eclipse/t2t/station/vedha/tājika) need only existing data/engine → U3 unblocked. C13 needs U4. Serialize the shared ka_sangam/SUPPORTING_WEIGHTS edit between U3 and U2. |

### §8.2d — U4 elevation (2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D36** | **U4 ELEVATED beyond agreement-count to a structured weighted-expert panel.** Add 4 elevations (all mostly wiring of already-computed engine output): (E1) **disagreement intelligence** — use the 4 disagreement types (esp. `temporal_scope` = agree-WHAT-differ-on-WHEN, a timing-refinement signal) + `resolution_verdict`, not a bare flag; (E2) **per-domain school-authority weighting** — weight each school by classical authority per domain (KP=timing, Jaimini=career/longevity, Tājika=annual, …), swarm tunes within bounds (D33-style); (E3) **direction+magnitude** — feed the mean domain score + σ the engine computes, not just agreement-count; (E4) **persist+surface the NL reasoning** (`buildConvergenceNarrative`). | **native-ruled** | Seven independent expert opinions contain far more than a headcount. The engine ALREADY computes mean/σ, divergence detection, NL narrative; the `school_disagreements` table ALREADY defines 4 disagreement classes + resolution verdicts — all currently discarded. Surfacing disagreement-type (esp. timing-only disagreement), weighting by domain authority, and carrying direction + reasoning makes the consensus acharya-grade, not a vote. Mostly USE-existing-output, not new compute. |

### §8.2e — ph_nimitta elevation + kala_bhavishya relationship (2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D37** | **ph_nimitta INHERITS `kala_bhavishya` (correctness, not optional).** ph_nimitta consumes L3's existing 50 `kala_bhavishya` projections (probability_tier, domain, peak_date, falsifiability, source_chain, narrative, outcome_recorded) as ONE anchor source — enriching them with the 8 axes + the elevations + extending to lifetime scope. It does NOT ignore or duplicate them. | **must-fix** | `kala_bhavishya` is already L3's 3-yr forward-projection emitter (50 rows, prod) that "hands prediction-records UP to L5." Two prediction tables that disagree = the L2/L3 duplication trap. ph_nimitta is its L4 enrichment+lifetime successor, by inheritance. |
| **D38** | **ph_nimitta ELEVATED with 4 value-adds + contradiction-carry** beyond the 8 axes: (V1) **magnitude/severity** as a first-class field distinct from confidence (from rarity_years + effective_score); (V2) **probability + date RANGES** not point estimates (from MSR `salience_confidence_interval_jsonb`); (V3) **karmic-arc framing** (debt-surfacing/reward-ripening/desire-entanglement from the convergence-root graha lordship); (V4) **actionability/malleability tag + counterfactual** (fated vs influenceable; what raises/lowers it; route influenceable → ph_pratikara); (V5) **carry contradiction in the anchor** (read `bodha_contradictions`; "net positive with countervailing malefic thread", not flattened). | **native-ruled** | The 8 axes make anchors accurate; these make them acharya-grade: how-big (not just how-sure), as a range (honest), placed in the soul's arc (profound), influenceable-or-not (useful), and honest about contested windows. Mostly uses already-computed data. |

### §8.2f — ph_muhurta elevation (2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D39** | **ph_muhurta ELEVATED beyond a panchāṅga calculator.** The `panchang_engine` is ALREADY classically deep (per-event Muhūrta-Chintāmaṇi rule tables w/ MC citations, Panchaka, Anandadi, Vasa, Homa windows) — REUSE it, don't rebuild. Add 4 elevations the engine lacks (all about native-chart + prediction connection): (M1) **personalize to chart strength + live transits** — score whether the action's RELEVANT planet is strong/well-placed natally AND transiting favorably now (ka_gochara + ga_condition), not just the day's panchāṅga; (M2) **avoid the native's PERSONAL danger windows** (ka_vighnakara + Sade-Sati/affliction), not just universal rahu-kalam; (M3) **fuse muhūrta to the PREDICTION** — find the best moment WITHIN a ph_nimitta predicted window (the muhūrta rides the prediction); (M4) **honest 'no good window'** reporting — say when the best available is mediocre, don't imply false quality. Event coverage: expose the engine's existing event tables + add native-relevant events (career/business, travel, signing, medical, ceremony, spiritual initiation). | **native-ruled** | A free app scores the day's panchāṅga; an acharya personalizes to YOUR chart, avoids YOUR adverse periods, and times to your actual opportunity windows. Items 4–5 (electional completeness, purpose-specific rules) are already built in the engine → reuse. The supreme gap is the native+prediction connection. |

### §8.2g — ph_pratikara elevation (2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D40** | **ph_pratikara ELEVATED from remedy-lookup to a managed remedy PROGRAM.** The `bodha_rm_remedy_prescriptions` store is far richer than the draft used (cost/feasibility/time, incompatible-with + prerequisite graphs, 6 traditions, classical_strength, hora/choghadiya/pranapratishtha, requires_acharya_review, outcome_tracking hook). Add 4 elevations (mostly USING that richness) + cross-tradition choice: (P1) **economics + feasibility optimization** — rank by effectiveness AND native constraints (cost/time/complexity), offer tiers; (P2) **coherent program** — use prerequisite + incompatible-with graphs → an ORDERED non-conflicting schedule, not a flat list; (P3) **muhūrta-timed initiation** — hand remedy-start to ph_muhurta (hora/choghadiya/pranapratishtha) for the auspicious BEGIN moment; (P4) **proportionality + outcome loop** — match remedy intensity to obstruction severity, tie to the window with a re-evaluation point, carry the falsifiable outcome hook for L5; (P5) **cross-tradition choice** — present options across the 6 traditions with corroboration count, native chooses per comfort. | **native-ruled** | A remedy you can't afford/sustain, that conflicts with another, started at a bad moment, disproportionate to the danger, and never re-checked is useless. The store was DESIGNED for all this; the draft used only the basic join. This makes mitigation a managed loop a family astrologer runs over years — at machine scale across a lifetime of windows. |

### §8.2h — ph_sodhana elevation (2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D41** | **ph_sodhana ELEVATED from a Lagna-fit time-scan to whole-instrument rectification.** PyJHora `compute_ascendant` computes the ascendant per candidate birth time (the one legitimate compute-not-read place). Add 4 elevations + strict firewall: (S1) **score against the FULL prediction machinery** — per candidate, rebuild the dāśā timeline + run the convergence engine against the 57 LEL events; the candidate whose dāśās/transits best align with WHEN events happened wins (far more discriminating than ascendant-sign); (S2) **iterative fine resolution + confidence interval** — coarse→fine→finer (sub-5-min); report a birth-time RANGE + confidence, not a point; (S3) **test chronic patterns + period summaries** (8 patterns + 5 summaries — headaches→head→Aries vs throat→Taurus; body/temperament are sharp 1st-house Lagna witnesses); (S4) **cross-check vs multi-school + multi-dāśā consensus** (the candidate that maximizes 7-school agreement + 7-dāśā alignment is likeliest correct). Firewall: **strict** (post-2020 + late-disclosed events held out of fitting, validation-only) + **discriminating-power weighting** (each training event weighted by date-confidence × Lagna-sensitivity). **Cost guard:** TIERED scorer — cheap Lagna+body filter narrows candidates, expensive full-machinery scoring only on survivors (bounded compute). | **native-ruled** | A basic time-scan checks ascendant-sign vs events. Supreme rectification uses the WHOLE instrument (dāśā + convergence + 7 schools + 7 dāśā systems) as the scorer — a wrong birth time shifts every dāśā boundary, so whole-machinery alignment is far more discriminating. The leakage firewall keeps it non-circular (the integrity core). Body/temperament patterns are the clearest Lagna witnesses. The tiered design keeps the per-candidate chart-rebuild cost bounded. |

### §8.2i — ph_suddha_sodhana elevation + the propagation safety rail (2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D42** | **ph_suddha_sodhana ELEVATED from argmax-selector to a LIVING rectification verdict.** Add 4 elevations: (SS1) **decisiveness verdict** (decisive/probable/unresolved + win-margin — a 0.78-vs-0.76 top pair is UNRESOLVED, not "winner 0.78"); (SS2) **standing verification loop** — test the chosen time against held-out events + each FUTURE event as it occurs; confidence updates over time (self-correcting); (SS3) **competing-hypotheses ledger** — keep the top few candidates alive with their distinguishing evidence + "the next event that would resolve the ambiguity"; (SS4) **falsifier for the rectification itself** ("if 3+ of next 10 events fit early-Taurus better, re-open") handed UP to L5. | **native-ruled** | A bare argmax is barely an asset. The value is a living, self-correcting, honest verdict: decisive-or-not, strengthening as life unfolds, transparent about competing hypotheses + what resolves them, and falsifiable like every other prediction. |
| **D43** | **Rectification propagation = FLAG + STAGE, one-click adopt; NEVER silently mutate the canonical chart.** If the rectified Lagna differs from the recorded 10:43 at high confidence, ph_suddha_sodhana PREPARES the override (computes the rectified chart, stages the diff, surfaces "rectification suggests a revision — adopt?") but the canonical chart changes ONLY on explicit native approval + version bump. NO auto-override. | **native-ruled (deferred to Cowork recommendation)** | The canonical chart is the foundation ALL layers rebuild on. The fit confidence is partly CIRCULAR (L2 signals built knowing this native's life) → auto-override risks a self-reinforcing error with no human to catch it. B.10 forbids chart change without native + version bump. Staging gives near-auto speed (one-click) while keeping the foundation from silently shifting on a possibly-circular score. The one place a human gate is most wanted. |

### §8.2j — ph_sankrama elevation (2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D44** | **ph_sankrama ELEVATED from a synthetic lag-formula to a grounded multi-hop cross-domain dynamics engine.** The CDLM (`bodha_cdlm_cells`) is far richer than the draft's 2-column lag-formula used — it carries `predicted_activation_dasha_windows`, `cgm_bridge_edge_seeds` (the graph path between domains), `cell_evolution_gradient_score`, `contradicting_signal_pairs`, asymmetry. Add 4 elevations: (SK1) **ground the lag in real activation windows + trace the spillover PATH through the graph bridge** (mechanism, not a formula guess) — RETIRES the invented `lag_days = round(90×…)` formula (D23); (SK2) **multi-hop cascades** (A→B→C: career→health→relationships, chaining cells in overlapping windows); (SK3) **cross-domain CONTRADICTIONS** (two domains conflict, not just spill — from contradicting_signal_pairs); (SK4) **evolution trajectory** (strengthening/weakening = urgency) + link to source ph_nimitta anchor + route to ph_pratikara (pre-emptive remedy for the target domain). | **native-ruled** | The draft INVENTED the lag from a formula and used 2 columns; the CDLM already holds WHEN linkages fire (activation windows) and WHICH planet/house mediates (graph bridge) — so the spillover can be GROUNDED + given a mechanism, not estimated. Multi-hop cascades are the "correlation depth beyond a human mind" the project is built for. SUPERSEDES D23's lag formula. |

### §8.2k — ph_pramana elevation (2026-06-21)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D45** | **ph_pramana ELEVATED from per-prediction falsifier-stamping to the instrument's falsifiability SEAM — all strictly NON-scoring (D5/D6 boundary preserved).** Add 4 elevations: (PR1) **unify + machine-evaluable** — one canonical falsifier schema `{metric, comparison, threshold, observation_window, data_source}` that EVERY L4 prediction (anchor/spillover/muhūrta/mitigation/rectification) conforms to, replacing the 5 scattered inconsistent hook shapes (kala_bhavishya.falsifiability, bodha_discoveries.falsifier_jsonb, bodha_rm.outcome_tracking, epistemic.calibration_hook); (PR2) **define the L5 onboarding contract** — the exact schema + semantics `mi_pramana` will read (pending/due/confirmed/denied/partial), since L5 doesn't exist yet (producer defines the interface); (PR3) **evaluation-staging vs LEL** — FLAG which pending predictions are due (evaluation_date past) + have candidate LEL evidence, WITHOUT computing the verdict (stages for L5, respects no-scoring); (PR4) **portfolio view + reverse calibration channel** — organize predictions by domain/confidence-tier/eval-date (so L5 calibrates per stratum) + define the return channel so L5's eventual priors flow BACK to damp ph_nimitta confidences (empty until L5 runs). | **native-ruled** | The outcome-hooks are scattered across layers in 5 different empty shapes; L5 has no consumption contract. ph_pramana makes the WHOLE instrument's predictions uniformly + mechanically testable and writes L5's input interface — the architectural value far exceeds per-row falsifier stamping. Every elevation makes scoring POSSIBLE and CLEAN without doing any scoring (the D5 line strictly held). |

### §8.2l — ph_phaladesa elevation (2026-06-21) — the finale

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D46** | **ph_phaladesa ELEVATED from a composite concatenation to a master-acharya READING (the finale + native-facing surface).** Add 4 elevations: (PD1) **narrative WEAVE** — connect prediction→spillover→mitigation→muhūrta→life-arc into ONE flowing reading (B.11 made legible), not 5 lists; (PD2) **the apex 'if you read nothing else' item** — surface the single most important thing now (via ka_tulana I-11 ranking) then the supporting structure; (PD3) **honest confidence + contradiction framing** — 'confident about / contested / speculative', carrying the layer-wide honesty up; (PD4) **multi-horizon + multi-lens + person-anchor + traceability** — compose per horizon (near/lifetime) + per question-lens (bodha_question_lenses), frame against the L2 gestalt (who they ARE), every claim traceable through anchor→window→signal→L1 fact→citation. **Correctness item:** CONSUME the existing `bodha_chart_gestalt`/`vw_chart_digest` (the timeless structural 'who you are') as the backdrop — do NOT duplicate it; ph_phaladesa adds the time-bound delivered outlook the gestalt deliberately lacks. **Deterministic-first guard:** structure/ranking/pointers/traceability are DETERMINISTIC (ka_tulana + composed rows + gestalt); generative LLM (Gemini/DeepSeek, Anthropic banned) does ONLY the serve-time NARRATION over the fixed scaffold — it cannot invent claims, only narrate the real composition. | **native-ruled** | The finale must read like a master acharya sat the native down, not a database dump. The other 7 assets are ingredients; this is the dish (the 'supremely valuable product' surface). The one legitimate place for generative synthesis — bounded so it narrates, never fabricates. |

### §8.2m — Fully-autonomous execution model (2026-06-22)

| ID | Decision | Ruling | Rationale |
|---|---|---|---|
| **D47** | **FULLY AUTONOMOUS, one-kickoff execution — NO human gates.** The operator pre-flight (OP1–OP5: apply migs 326–329, CI-green, prod==main, branch, rails) is ABSORBED into a Conductor-run **Phase 0** (env self-provisioning). A NEW **Sthāpati** role (15th) owns Phase 0 (worktree, branch, CI health, pre-req migrations, prod==main, proxy/deps, pre-fan-out). The build runs in an **isolated worktree** (`MadhavL4Phala`), **maximally parallel**: P1 (U1‖U4‖U3-pass1, file-disjoint) → P2 (ka_sangam serial: U3-school→U2→re-seal) → P3 (ph_nimitta spine) → P4 (muhurta‖pratikara‖sankrama‖sodhana) → P5 (suddha) → P6 (pramana) → P7 (phaladesa). ONE kickoff paste triggers env→build→seal. The only async native events: the $5k Tier-3 ceiling + the chart-revision flag (staged, non-blocking). All commit/merge/deploy/build/data-gen autonomous. | **native-ruled** | Native directive 2026-06-22: fully autonomous via Conductor + the 14-role agentic swarm, no human gates/interruptions, maximal parallelization, isolated worktree, one kickoff, env self-setup. Reuses the PROVEN AUTONOMY_RESILIENCE_PATTERN (the 2026-06-04 Brahma 4-parallel-wave model). The v1.0 operator-pre-flight was the only thing standing between "launch-ready" and "one-paste autonomous" — now absorbed. Artifacts: `L4_PHALA_AUTONOMOUS_EXECUTION_v2_0.md` + session_queue v2.0 + KICKOFF v2.0. |

### §8.3 — Consequent updates to prior decisions
- **D8/D9 → D25:** asset set is now **8**, not 9 (ph_anudhyana folded).
- **D16 → D20a:** multi-dāśā is not "build-run-the-6" — it is fully built; U1 = wire only.
- **discoveries count:** **1,505** everywhere (was 1,411) — D20c.
- **D12 → D20, D13 → D21:** the two NATIVE-RATIFY gates are now ratified.

---
*End of L4_PHALA_DECISIONS_LEDGER v1.0. §8 records GATE A (prod-true reconciliation) + GATE B (all 9
ratifications, D20–D28). Next: GATE C (finalize the 8 briefs + M9 + U2) on verified ground.*
