---
artifact: CLAUDECODE_BRIEF_L4_PH_SODHANA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L4_PH_SODHANA
brief_for: ph_sodhana — Birth-Time Rectification (whole-instrument, leakage-clean) [maximal capacity]
status: FINALIZED — built on prod-verified state (GATE A) + D41 elevations; ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: CLAUDECODE_BRIEF_L4_PH_SODHANA_v1_0.md (the 6-asset draft)
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D12 G-RECT PyJHora, D41 elevations, D10 reuse, D5 honest-confidence)
swarm_coordination:
  wave: W4 (after the prediction spine + the consensus enablers; it SCORES using them)
  blocked_by: [ph_nimitta, u1_dasha_consensus, u3_convergence_currents, u4_school_consensus_activation]
  blocks: [ph_suddha_sodhana, ph_phaladesa]
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_sodhana.py
    - platform/python-sidecar/services/ph_sodhana/**          # the tiered rectification scorer
    - platform/supabase/migrations/333_phala_rectification.sql
    - platform/scripts/seed/asset_registry_seed.ts
    - platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  hard_internal_gate: "LEAKAGE FIREWALL gate: a test MUST prove no post-2020/late-disclosed event contributes to the fit score (only to validation) — BEFORE any rectification verdict is emitted. Non-negotiable integrity gate."
---

# CLAUDECODE BRIEF — ph_sodhana (Birth-Time Rectification) [maximal capacity]

> **What it is, in one line:** ph_sodhana asks "is the recorded 10:43 IST birth time correct?" — and
> answers it not by ascendant-sign guessing but by using the WHOLE instrument as the judge: for each
> candidate birth time it rebuilds the dāśā timeline + runs the convergence engine against the native's
> 57 dated life events, weights events by their discriminating power, holds out post-disclosure events
> as a firewall, and reports a birth-time RANGE with honest confidence. The chart's own predictive
> machinery becomes the rectification oracle.

## §0 — PyJHora computes (the one legitimate compute-not-read place; D12)
**Code-verified:** `pyjhora_adapter/houses.compute_ascendant(jd_ut, ayanamsha_id, lat, lon, tz)` returns
the ascendant to fractional degree at ANY time. Rectification is NOT `[EXTERNAL_COMPUTATION_REQUIRED]`
anymore — PyJHora is the sealed engine (G-RECT ratified, D12/D20). ph_sodhana CALLS it per candidate.
Legacy `brahmagyan/phala/l4_rectification.py` is reference-only (harvest the train/test logic; rebuild
the architecture).

## §1 — The candidate grid + the LEL corpus
- **Candidate birth-time grid:** 10:13–11:13 IST (±30 min around reported 10:43), iteratively refined
  (S2). Birth facts: 1984-02-05, Bhubaneswar (20.27°N, 85.84°E, UTC+5:30).
- **The judge corpus:** LEL (`01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`, v1.7) — **57 dated point-events +
  5 period summaries + 8 chronic patterns**, each with `date_confidence` + `retrodictive_match` signal
  pointers. This is the empirical truth the candidate times are scored against.

## §2 — The 4 ELEVATIONS + the firewall (D41)

### S1 — Score against the FULL prediction machinery (the supreme move)
For each surviving candidate birth time (after the S0 cheap filter): rebuild the dāśā timeline (all 7
systems via the ga_dashas logic) + run the convergence engine (`ka_sangam`, U3-enriched) for the dates
of the training events. Score = how well the candidate's dāśās/transits ALIGN with WHEN each event
actually happened (career events in career-favorable periods; the father's death in the right
8th-house/transit configuration; etc.). A wrong birth time shifts every dāśā boundary → poor alignment.
**This is far more discriminating than ascendant-sign and uses the whole instrument as the oracle.**

### S2 — Iterative fine resolution + confidence interval
Coarse pass (5-min grid) → fine pass (1-min) near the best candidate → report a birth-time RANGE +
confidence ("most likely 10:41–10:47 IST, peak 10:43, confidence 0.78"), NOT a single time. Honest
about residual uncertainty (mirrors the D5 discipline). Store `time_low`/`time_peak`/`time_high` + confidence.

### S3 — Test chronic patterns + period summaries (the body is the clearest Lagna witness)
Use the 8 chronic patterns + 5 period summaries as Lagna discriminators: headaches → head → Aries (1st)
vs throat/neck → Taurus; phobias, stammering, temperament → 1st-house/Lagna-lord signatures. These
body/temperament signals discriminate Lagna sharply where fuzzy-dated point-events cannot.

### S4 — Cross-check vs multi-school + multi-dāśā consensus
Score each candidate by whether it maximizes (a) 7-school agreement (U4) on the native's known life
themes and (b) 7-dāśā-system alignment (U1) with the events. The birth time that makes the most methods
COHERE with lived reality is likeliest correct. Uniquely possible because the consensus machinery exists.

### THE LEAKAGE FIREWALL (the integrity core) — strict + discriminating-power weighting
- **Strict hold-out:** events dated post-2020 OR disclosed after the framework date (the M5-A-S1
  enrichment events) are VALIDATION-ONLY — they NEVER contribute to the fit score. (A test asserts this.)
- **Discriminating-power weighting:** within the training set, each event's contribution =
  `date_confidence × lagna_discriminating_power` (a precise, Lagna-sensitive event like the father's
  death counts far more than a fuzzy, Lagna-neutral one). Document the weighting.

### S0 — The cost guard (tiered scorer)
The full-machinery score (S1) is expensive (chart rebuild + convergence per candidate). Run a CHEAP
filter first — ascendant-sign (S1-lite) + body-pattern fit (S3) — to narrow ~13 candidates to the top
few, THEN run the expensive S1 full-machinery + S4 consensus scoring on the survivors only. Keeps
compute bounded.

## §3 — Schema (migration 333)
`phala_rectification`:
```
rectification_id        uuid PK
chart_id                uuid NOT NULL
run_id                  uuid NOT NULL                 -- one rectification search run
candidate_time          time NOT NULL
candidate_jd            double precision
computed_asc_longitude_deg double precision NOT NULL  -- from PyJHora (real, not placeholder)
computed_lagna_sign     text NOT NULL
is_cusp_boundary        boolean
machinery_score         double precision              -- S1 (dāśā+convergence alignment vs events)
body_pattern_score      double precision              -- S3 (chronic-pattern fit)
consensus_score         double precision              -- S4 (school + dāśā coherence)
composite_fit_score     double precision              -- weighted blend
event_breakdown_jsonb   jsonb                         -- per training-event contribution (with weights)
leakage_status          text NOT NULL                 -- 'CLEAN' (firewall enforced)
is_survivor             boolean                       -- passed the S0 cheap filter → got full scoring
derivation_ledger_jsonb jsonb NOT NULL
source_citation         text NOT NULL
computed_at             timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, run_id, candidate_time)
```
> The chosen birth-time RANGE + confidence + the validation-set result live in `ph_suddha_sodhana`
> (the argmax + verification-state asset). ph_sodhana emits the per-candidate scored grid.

## §4 — Engine spec (`services/ph_sodhana/engine.py`)
1. Build the candidate grid (S2 coarse). For each: PyJHora `compute_ascendant` → lagna + degree.
2. S0 cheap filter: ascendant-sign + body-pattern (S3) → mark `is_survivor` for the top few.
3. For survivors: S1 (rebuild dāśā + convergence vs training events) + S4 (school+dāśā consensus).
4. Apply the FIREWALL: only training events (pre-2020, pre-disclosure) score; weight by
   date_confidence × lagna-discriminating-power. Validation events scored separately, not in the fit.
5. S2 fine pass (1-min) near the best survivor; compute the range + confidence (handed to ph_suddha_sodhana).
6. Anti-drift: cite the PyJHora params + the LEL event ids + the dāśā/convergence ids; write ONLY
   `phala_rectification`. `WriterResult(asset_id='ph_sodhana', rows_inserted=N)`.

## §5 — Acceptance criteria [tagged; prod-verified]
1. `[pytest]` `compute_ascendant` called per candidate; `computed_asc_longitude_deg` is a real fractional degree (B.10 — no fabricated value).
2. `[pytest — FIREWALL, HARD GATE]` NO post-2020/late-disclosed event contributes to `machinery_score`/`composite_fit_score` (assert the training set is strictly the eligible subset) — gate before any verdict.
3. `[pytest — S1]` per candidate, the dāśā timeline is rebuilt + convergence run against training events; a deliberately-wrong candidate scores materially lower than the best.
4. `[pytest — S3]` chronic patterns discriminate Lagna (a head-symptom event favors Aries over Taurus); body-pattern score populated.
5. `[pytest — S4]` consensus score uses real U4 school agreement + U1 dāśā alignment (not stubbed).
6. `[pytest — S2]` output is a RANGE + confidence (low/peak/high), not a single time; fine pass refines near the best survivor.
7. `[pytest — S0]` the tiered scorer runs full-machinery scoring ONLY on survivors (assert the cheap filter narrows first — bounded compute).
8. `[anti-drift]` writes only phala_rectification; zero `.commit()/.rollback()`; ledgers resolve.
9. `[psql_prod + curl_prod]` phala_rectification lit with the scored candidate grid; cockpit shows ph_sodhana; idempotent; FORENSIC 7/7 (the canonical chart itself is NOT mutated — rectification is a hypothesis product, B.10 / no chart rewrite without native + version bump).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l4-ph-sodhana
# the compute engine + the harvest-logic legacy
sed -n '1,60p' platform/python-sidecar/pyjhora_adapter/houses.py
sed -n '1,140p' platform/python-sidecar/brahmagyan/phala/l4_rectification.py   # harvest train/test logic only
# the LEL judge corpus
sed -n '1,80p' 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md
cd platform/python-sidecar && pytest -q services/ph_sodhana -k "sodhana or rectif or leakage or firewall or machinery or ascendant"
```

## §7 — Definition of done
- [ ] Migration 333: phala_rectification created.
- [ ] PyJHora computes ascendant per candidate; S0 tiered scorer; S1 full-machinery + S2 range + S3 body + S4 consensus.
- [ ] LEAKAGE FIREWALL enforced (hard gate) + discriminating-power weighting.
- [ ] Canonical chart NOT mutated (hypothesis product); anti-drift clean; registered/idempotent/FORENSIC-clean; cockpit lit; PR opened.

## §8 — VALUE ADDED BY THIS BRIEF
1. **The whole instrument becomes the rectification oracle** — scoring candidate birth times by dāśā +
   convergence + 7-school + 7-dāśā alignment with 57 real events is vastly more discriminating than
   ascendant-sign, and is uniquely possible because we built all of it.
2. **Methodologically honest** — strict leakage firewall (non-circular), discriminating-power weighting,
   a confidence INTERVAL not a false-precise time, and it can CONFIRM a good birth time, not only doubt it.
3. **Uses the body as the clearest Lagna witness** — chronic patterns/temperament, which point-events miss.
4. **Bounded** — the tiered scorer keeps the per-candidate chart-rebuild cost in check.
5. **Turns the legacy stub into a real computation** — the legacy framework marked the degree external;
   PyJHora now computes it; the framework's train/test discipline is harvested + hardened.

## §9 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [RESOLVED — Cowork default locked]:** candidate grid = **±30 min** (10:13–11:13), coarse 5-min;
  **auto-widen only** if the best survivor sits at the grid edge (then extend that side + re-run).
- **R2 [RESOLVED — Cowork default locked]:** `composite_fit_score` blend = **machinery 0.55 : body 0.20
  : consensus 0.25** (the whole-machinery alignment dominates; body-pattern + cross-method consensus corroborate).
- **R3 [RESOLVED — Cowork default locked]:** `lagna_discriminating_power` per event = derived from
  whether the event's `retrodictive_match` signals are **Lagna-sensitive** (house- or lagna-lord-based →
  high power) vs **Lagna-neutral** (e.g. the Gemini-anchored nexus, independent of Aries/Taurus → low power).

---
*End of CLAUDECODE_BRIEF_L4_PH_SODHANA v1.0 — CLOSED. Rectification at maximal capacity: whole-instrument
scoring, leakage firewall, body-witness, consensus cross-check, confidence interval, tiered cost guard.
R1–R3 resolved.*
