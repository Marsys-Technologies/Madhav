---
artifact: CLAUDECODE_BRIEF_U3_CONVERGENCE_CURRENTS_ENRICHMENT_v1_0.md
canonical_id: CLAUDECODE_BRIEF_U3_CONVERGENCE_CURRENTS_ENRICHMENT
brief_for: U3 — Convergence Currents Enrichment (the deepest accuracy lever; reopens & re-seals L3)
status: FINALIZED — built on prod-verified state (GATE A); CLOSED 2026-06-21; ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D32 enrich, D33 weights-propose-tune, D27 L3-reseal, D35 6-now-school-later)
classification: UPSTREAM-ENABLER (L3 reopen) — enriches the I-16 convergence score; EVERY prediction inherits it
swarm_coordination:
  wave: W2 (with U2 — both reopen L3; U3 currents land BEFORE U2's lifetime run so lifetime windows also score on enriched currents — R3)
  blocked_by: []                                                    # the 6 shipped currents need only existing data/engine; school-consensus (C13) added post-U4 (R4)
  second_pass_after: [u4_school_consensus_activation]               # C13 school-consensus current added once U4 completes
  blocks: [ph_nimitta, ph_phaladesa, ph_sankrama]                    # all anchors inherit the enriched convergence score
  may_touch:
    - platform/python-sidecar/services/ka_sangam/engine.py            # SUPPORTING_WEIGHTS + the currents dict + independence-count
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py   # current assembly (feed new currents)
    - platform/python-sidecar/services/ka_gochara/**                  # surface eclipse/t2t/station events to the scorer (already computed)
    - platform/supabase/migrations/<33N>_kala_convergence_current_breakdown.sql  # OPTIONAL: store per-current contributions
    - 00_ARCHITECTURE/L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md  # the ratified-weights doc — version bump (D33)
    - 00_ARCHITECTURE/L3_KALA_CLOSE_v1_0.md                            # re-seal (D27)
  parallel_safe_with: [u2_lifetime]   # same engine; coordinate the SUPPORTING_WEIGHTS edit (serialize)
  hard_internal_gate: "Re-derive ONE known window end-to-end with the enriched currents and confirm convergence_score stays ∈ [0,1] + the new currents move the score in the classically-correct direction BEFORE re-running the full convergence build."
---

# CLAUDECODE BRIEF — U3 Convergence Currents Enrichment

> **The deepest accuracy lever in the program.** Every ph_nimitta anchor inherits its confidence from
> the I-16 convergence score. Code-verification (2026-06-21) found the score uses ONLY
> `constituent_lord_transit` among transit currents — yet `ka_gochara` ALREADY computes eclipse,
> transit-to-transit, stations, and multi-planet confluence (unused by the scorer), and we have
> ashtakavarga + vedha + Tājika data sitting unused. U3 adds these as weighted currents, making EVERY
> prediction (5-year and lifetime) sharper at the source — not one asset, the whole instrument.

## §0 — What this enabler IS
The I-16 convergence score combines NECESSARY conditions (multiplicative veto) with SUPPORTING currents
(additive-with-saturation). Today there are 6 supporting currents. U3 adds **7 more** — each grounded
in data/engine capability that ALREADY EXISTS — and re-normalizes the weight set. The convergence
math (the multiplicative-veto × saturating-sum form, I-16) is UNCHANGED; only the *current set* and
*weights* expand.

## §1 — VERIFIED ground truth (code + prod, 2026-06-21)
- **The current set + weights** (`ka_sangam/engine.py` line 27-33), `SUPPORTING_WEIGHTS`:
  `constituent_lord_transit 0.30 · benefic_dristi 0.20 · cross_dasha_agreement 0.18 ·
  panchanga_quality 0.12 · tara_bala 0.12 · nakshatra_subsystem 0.08` (sum 1.0).
- **The integration point:** `convergence_score(currents, ...)` (engine.py line 39); currents/
  `supporting` dict assembled at lines ~354 + ~461 in the writer/engine path. Independence-counting
  (engine.py line 134-168) already handles `transit + dasha` independent, `panchanga + transit`
  moderate coupling — EXTEND this for the new currents.
- **`ka_gochara` ALREADY computes (but the scorer ignores):** `find_eclipse_proximity`,
  `find_transit_to_transit`, `find_multi_planet_confluence`, `find_stations` (service.py line 77-109).
  **These are built capabilities — U3 routes their output into the currents, no new ephemeris code.**
- **Ashtakavarga data:** `chart_facts` (ga_strength writer): sarvashtakavarga = 7-graha bindu sum per
  house; 96 bindu rows/ayanamsha; classical sarva total = 337. Read-only.
- **Vedha rules:** `bg_transit_rules` (mig 266): `rule_type ∈ ('favourable','unfavourable','vedha')`,
  `vedha_house` column (Phaladeepika Ch.26 Gochara Vedha). Read-only.
- **Tājika annual:** `l1_tajik_varsha_year_lords` (240 rows): varṣeśa (year-lord) + muntha per varṣa.
- **School consensus:** from U4 (School Consensus Activation) — N-of-7 schools concurring per domain.

## §2 — The 7 new currents (each: what it is · data source · classical basis · direction)

| # | Current | What it measures | Data source | Classical basis | Effect on score |
|---|---|---|---|---|---|
| C7 | **ashtakavarga_transit_potency** | Bindus the transiting planet has in the sign it transits (8+ strong, ≤4 weak) | `chart_facts` sarvashtakavarga | Determines whether a transit DELIVERS (Parāśara/Ashtakavarga) | High bindu → amplify; low → damp |
| C8 | **eclipse_proximity** | A solar/lunar eclipse near a sensitive point in the window | `ka_gochara.find_eclipse_proximity` | Eclipses on sensitive points = major karmic timing | Near eclipse → amplify (esp. malefic windows) |
| C9 | **transit_to_transit** | Sky-level mutual aspect/conjunction (e.g. Jupiter-Saturn) in the window | `ka_gochara.find_transit_to_transit` + `find_multi_planet_confluence` | Outer-planet cycles are era-defining timing | Major t2t event → amplify |
| C10 | **station_retrograde** | A relevant planet stationing (retrograde turn) on a trigger point | `ka_gochara.find_stations` | A stationing planet intensifies its significations | Station on trigger → amplify |
| C11 | **vedha_cancellation** | Counter-transit (vedha) cancelling the favourable/unfavourable transit | `bg_transit_rules` (vedha_house) | Classical gochara vedha (Phaladeepika Ch.26) | Vedha present → DAMP (a NECESSARY-side modulator — see §3.2) |
| C12 | **tajika_annual_reinforcement** | The varṣa (annual) chart's varṣeśa/muntha reinforcing the window's theme | `l1_tajik_varsha_year_lords` | Vārṣaphala annual confirmation | Annual agrees → amplify |
| C13 | **school_consensus** *(2nd pass, post-U4 — R4/D35)* | N-of-7 schools (Parāśarī/Jaimini/KP/Yoginī/…) concurring on the domain | U4 school engine | Multi-school agreement = strongest trust signal | More schools concur → amplify |

> **SHIPPING ORDER (D35):** the FIRST U3 pass lands the 6 currents that need only existing data/engine
> (C7 ashtakavarga, C8 eclipse, C9 transit-to-transit, C10 station, C11 vedha, C12 tājika). The
> **school_consensus current (C13) is added in a fast SECOND pass once U4 completes** — its weight slot
> (0.10) is reserved in §3.1; until C13 lands, re-normalize the other 12 to sum 1.0, then re-introduce
> 0.10 for C13 and re-normalize again at the second pass.

## §3 — The build

### §3.1 — Extend the currents + re-normalize the weights (D33: Cowork proposes, swarm tunes within bounds)
**Cowork-proposed re-normalized SUPPORTING_WEIGHTS (sum = 1.0)** — initial values + tuning bounds:

| Current | Proposed weight | Tuning bound | Note |
|---|---|---|---|
| constituent_lord_transit | 0.18 | [0.14, 0.24] | still the primary transit current |
| ashtakavarga_transit_potency (C7) | 0.12 | [0.08, 0.16] | the "does it deliver" gate |
| cross_dasha_agreement | 0.12 | [0.09, 0.16] | multi-dāśā consensus (U1) |
| school_consensus (C13) | 0.10 | [0.06, 0.14] | strongest single trust signal (U4) |
| benefic_dristi | 0.10 | [0.07, 0.13] | |
| transit_to_transit (C9) | 0.08 | [0.05, 0.11] | outer-planet cycles |
| panchanga_quality | 0.07 | [0.05, 0.10] | |
| tara_bala | 0.06 | [0.04, 0.09] | |
| eclipse_proximity (C8) | 0.06 | [0.03, 0.09] | |
| nakshatra_subsystem | 0.05 | [0.03, 0.07] | |
| station_retrograde (C10) | 0.03 | [0.01, 0.05] | |
| tajika_annual_reinforcement (C12) | 0.03 | [0.01, 0.05] | |
| **(sum)** | **1.00** | — | re-normalize after tuning |

> **D33 rule:** the swarm MAY tune each weight WITHIN its bound using internal-consistency checks
> (e.g. re-derive known LEL-era activations and check the enriched score ranks them sensibly) and MUST
> re-normalize to sum 1.0. It may NOT move a weight outside its bound or drop/add a current without a
> native gate. Log the final tuned weights to the re-sealed weights doc.

### §3.2 — vedha as a NECESSARY-side modulator (not a supporting current)
`vedha_cancellation` (C11) is NOT additive — classically a vedha CANCELS a transit. So it enters the
NECESSARY (multiplicative) side as a `(1 − vedha_strength)` factor on the `constituent_lord_transit`
contribution, not the supporting sum. Document this; it's the one current that damps multiplicatively.

### §3.3 — Wire the already-computed ka_gochara events into the currents
For each window, the current-assembly step (engine.py ~354/461) calls the relevant `ka_gochara`
methods (`find_eclipse_proximity`, `find_transit_to_transit`, `find_stations`) over the window and
maps presence/orb-strength → the C8/C9/C10 current values ∈ [0,1]. **No new ephemeris computation —
these methods exist; U3 consumes them.** (D10 reuse rule.)

### §3.4 — Extend independence-counting (I-22)
The new currents need coupling rules in the independence counter (engine.py 134-168): e.g.
`ashtakavarga_potency` is coupled to `constituent_lord_transit` (same transit — count ~1, not 2);
`eclipse` + `transit_to_transit` are independent; `school_consensus` is independent (cross-method).
Document the coupling so the confidence (which discounts correlated evidence) stays honest.

### §3.5 — OPTIONAL: store the per-current breakdown
Value-add: store each window's per-current contributions in `kala_convergence.constituent_factors`
(JSONB — already exists) so a prediction can EXPLAIN "this scored high because of ashtakavarga + a
Jupiter-Saturn transit-to-transit + 5/7 school consensus." Highly recommended — it makes the
convergence auditable and feeds ph_nimitta's causal narrative. **[CONFIRM at review.]**

## §4 — Acceptance criteria [tagged; prod-verified]
1. `[pytest]` all 7 new currents compute ∈ [0,1] from their real data sources (ashtakavarga from
   chart_facts, eclipse/t2t/station from ka_gochara, vedha from bg_transit_rules, tajika from
   l1_tajik_varsha_year_lords, school from U4) — NO new ephemeris code (assert ka_gochara is called).
2. `[pytest]` `convergence_score` stays ∈ [0,1] with the enriched current set; the I-16 multiplicative-
   veto × saturating-sum FORM is unchanged.
3. `[pytest]` vedha enters multiplicatively (NECESSARY side), damping; not as a supporting addend.
4. `[pytest]` re-normalized weights sum to 1.0; each tuned weight is within its §3.1 bound (assert bounds).
5. `[pytest]` independence-counting handles the new couplings (ashtakavarga coupled to lord_transit; eclipse/t2t/school independent).
6. `[internal-consistency]` re-deriving known LEL-era windows ranks them sensibly with the enriched score (the swarm's tuning gate; no JH-parity).
7. `[HARD GATE]` the single-window enriched re-derivation passes ([0,1] + classically-correct direction) BEFORE the full convergence rebuild.
8. `[anti-drift]` all currents cite their source data; the writer writes only L3 tables.
9. `[re-seal]` the weights doc (`L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS`) + `L3_KALA_CLOSE` version-bumped with the final tuned weights (D27/D33).
10. `[FORENSIC]` 7/7 holds; only `482012f1`. `[cockpit]` L3 stays lit; convergence counts recomputed correctly.

## §5 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/u3-convergence-currents
# the weights + currents + scorer to extend
sed -n '27,75p;130,170p;340,470p' platform/python-sidecar/services/ka_sangam/engine.py
# the already-computed gochara events to wire in
sed -n '70,115p' platform/python-sidecar/services/ka_gochara/service.py
# ashtakavarga + vedha + tajika sources
psql "$DATABASE_URL" -c "SELECT fact_key,fact_value_num FROM chart_facts WHERE chart_id=:'NATIVE' AND fact_category LIKE '%ashtakavarga%' LIMIT 5;"
psql "$DATABASE_URL" -c "SELECT graha,rule_type,vedha_house FROM bg_transit_rules WHERE rule_type='vedha' LIMIT 5;"
cd platform/python-sidecar && pytest -q services/ka_sangam -k "current or weight or convergence or vedha or ashtakavarga or eclipse"
```

## §6 — Definition of done
- [ ] 7 new currents computed ∈ [0,1] from existing data/engine; no new ephemeris code (reuse ka_gochara).
- [ ] SUPPORTING_WEIGHTS re-normalized (sum 1.0); swarm-tuned within §3.1 bounds; vedha multiplicative.
- [ ] independence-counting extended for new couplings.
- [ ] convergence rebuilt; [0,1] preserved; spine re-derivation gate passed.
- [ ] per-current breakdown stored (if §3.5 confirmed); weights doc + L3_KALA_CLOSE re-sealed; FORENSIC 7/7.

## §7 — VALUE ADDED BY THIS BRIEF
1. **The single deepest accuracy improvement** — sharpens EVERY prediction at the source (the
   convergence score every anchor inherits), not one asset.
2. **Activates already-built, unused capability** — `ka_gochara` computes eclipse/t2t/station today and
   the scorer ignores them; ashtakavarga/vedha/Tājika data sit unused. U3 is mostly wiring, not new compute.
3. **Adds the classical "does the transit deliver" gate** (ashtakavarga potency) — the most important
   missing current; a transit without bindu support often doesn't manifest.
4. **Makes vedha cancellation honest** — a counter-transit correctly DAMPS multiplicatively, matching classical gochara.
5. **Brings annual (Tājika) + multi-school consensus into timing** — two whole independent confirmation
   systems the score didn't consult.
6. **Auditable** (§3.5) — per-current breakdown lets a prediction explain WHY it scored high, feeding ph_nimitta's narrative.

## §8 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [RESOLVED — Cowork default locked]:** YES — store the per-current breakdown in
  `constituent_factors` (JSONB, already exists) for explainability. Each window records its per-current
  contributions so a prediction can state WHY it scored high (feeds ph_nimitta's causal narrative).
- **R2 [RESOLVED — native accepted]:** the §3.1 proposed weights + bounds are the swarm's starting
  point; it tunes within bounds via internal-consistency and re-normalizes to 1.0.
- **R3 [RESOLVED — Cowork default locked]:** U3's current/weight edit lands BEFORE U2's lifetime run, so
  ONE enriched convergence build covers both the near tier and the lifetime tier. (Serialize the shared
  `ka_sangam`/SUPPORTING_WEIGHTS edit between U3 and U2.)
- **R4 [RESOLVED — native: 6-now, school-later (D35)]:** ship the 6 existing-data currents now;
  add the school_consensus current (C13) in a fast second pass once U4 completes. U3 is NOT blocked on U4.

---
*End of CLAUDECODE_BRIEF_U3_CONVERGENCE_CURRENTS_ENRICHMENT v1.0 — CLOSED. The deepest accuracy lever;
reopens + re-seals L3. 6 currents from existing data/engine now (+ school-consensus post-U4), accepted
weights+bounds, vedha-multiplicative, independence-counting, per-current explainability. R1–R4 resolved.*
