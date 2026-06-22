---
artifact: CLAUDECODE_BRIEF_L4_PH_PRAMANA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L4_PH_PRAMANA
brief_for: ph_pramana — Falsifiability Scaffolding (the instrument's testability seam; NON-scoring) [maximal capacity]
status: FINALIZED — built on prod-verified state (GATE A) + D45 elevations; ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: DRAFT_CLAUDECODE_BRIEF_L4_PH_PRAMANA_v0_1.md
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D5 scaffolding-not-scoring, D6 hands-up-to-L5, D7 the L4/L5 test, D45 elevations)
swarm_coordination:
  wave: W5 (after all prediction-emitting assets exist)
  blocked_by: [ph_nimitta, ph_sankrama, ph_muhurta, ph_pratikara, ph_sodhana, ph_suddha_sodhana]
  blocks: [ph_phaladesa]
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py
    - platform/python-sidecar/services/ph_pramana/**
    - platform/supabase/migrations/336_phala_pramana.sql
    - platform/scripts/seed/asset_registry_seed.ts    # NEW asset registration
    - platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json
    - 00_ARCHITECTURE/L5_MIMAMSA_ONBOARDING_CONTRACT_v1_0.md   # NEW (PR2 — defines L5's input interface)
  hard_internal_gate: "NO-SCORING gate (D5): a test MUST prove ph_pramana computes NO hit/miss/calibration verdict — every row is outcome_status='pending'; the engine contains zero scoring against the LEL (it only STAGES). Non-negotiable boundary."
---

# CLAUDECODE BRIEF — ph_pramana (Falsifiability Scaffolding) [maximal capacity]

> **THE BOUNDARY (D5/D6/D7).** ph_pramana makes every L4 prediction machine-checkably falsifiable and
> hands the testable predictions UP to L5 — it does **NOT** backtest, score, or calibrate (that is L5
> Mīmāṃsā). The test: "does it improve a prediction NOW (L4) or score predictions OVER TIME (L5)?"
> Making a prediction falsifiable + staging it for evaluation = L4. Computing the verdict = L5.

## §0 — Why it matters (the architectural seam)
A prediction you cannot mechanically refute is a horoscope, not a forecast. And right now the
outcome-hooks are scattered across the layers in FIVE different empty shapes; L5 has no consumption
contract. ph_pramana is the single point that makes the WHOLE instrument's predictions uniformly +
mechanically testable, and writes the interface L5 will read. This is the project's mission spine —
"calibrated, correctable predictions testable against lived reality" — built to the point where L5 can
do the testing.

## §1 — VERIFIED ground truth (code, 2026-06-21)
Scattered falsifiability/outcome hooks, all EMPTY, all in different shapes:
- `kala_bhavishya.falsifiability` jsonb ({confirm_observable, deny_observable, evaluation_date}) +
  `outcome_recorded` (L3, the L3→L5 hook).
- `bodha_discoveries.falsifier_jsonb` + `calibration_hook` (L2).
- `bodha_rm_remedy_prescriptions.outcome_tracking_placeholder_jsonb` (L2 remedies).
- `bodha_msr_signals.epistemic_jsonb.calibration_hook` (L2 signals).
- The L4 assets each carry a `falsifier` (ph_nimitta, ph_sankrama, …) + outcome hooks.
**L5 (`mi_pramana`) has NO consumption contract yet** (grep: not built). ph_pramana DEFINES it (PR2).

## §2 — The 4 ELEVATIONS (D45 — all strictly NON-scoring)

### PR1 — Unify + make falsifiers MACHINE-EVALUABLE
Normalize EVERY L4 prediction's free-text falsifier into ONE canonical structured schema:
`structured_falsifier = {metric, comparison, threshold, observation_window, data_source}`. E.g.
"career_role_change == false within [2027-01-01, 2027-12-31] per LEL" — mechanically checkable, not
prose. This replaces the 5 inconsistent scattered hook shapes with ONE, so L5 consumes a single thing.
The architectural core that makes calibration possible at all.

### PR2 — Define the L5 onboarding contract (the producer writes the interface)
Author `L5_MIMAMSA_ONBOARDING_CONTRACT_v1_0.md` + the `phala_pramana` schema as the EXACT thing L5's
`mi_pramana` reads: the canonical falsifier shape, `outcome_status` enum (pending|confirmed|denied|
partial), the `evaluation_date` semantics, the per-stratum grouping (PR4), and the return channel
(PR4). ph_pramana is the producer; it defines the interface so L5 has an unambiguous, single input.

### PR3 — Evaluation-staging vs the LEL (FLAG, do NOT score)
For each pending prediction whose `evaluation_date` is now in the PAST: search the LEL for candidate
matching evidence and FLAG `evaluation_ready = true` + `candidate_evidence_jsonb` (the LEL event ids
that *might* confirm/deny). **It does NOT compute the verdict** — it stages "this one is ready, here's
the candidate evidence" for L5 to adjudicate. (A test asserts no hit/miss is computed — the D5 line.)

### PR4 — Portfolio view + the reverse calibration channel
- **Portfolio:** group predictions by `{domain, confidence_tier, evaluation_date}` so L5 can calibrate
  PER STRATUM ("are high-confidence career predictions better calibrated than speculative health ones?").
  Store the stratum key on each row.
- **Reverse channel:** define `calibration_prior_jsonb` (EMPTY at L4) — the slot where L5's eventual
  per-stratum calibration flows BACK so ph_nimitta can consult it ("career predictions run 0.7-confident
  but 0.55-accurate → damp future career confidences"). The return interface is defined now; L5 fills it.

## §3 — Schema (migration 336)
`phala_pramana`:
```
pramana_id              uuid PK
chart_id                uuid NOT NULL
prediction_ref_id       uuid NOT NULL          -- the ph_* row being made falsifiable
prediction_asset        text NOT NULL          -- ph_nimitta | ph_sankrama | ph_muhurta | ph_pratikara | ph_sodhana | ...
domain                  text
confidence_tier         text                   -- PR4 stratum (high/moderate/speculative)
structured_falsifier_jsonb jsonb NOT NULL      -- PR1 {metric, comparison, threshold, observation_window, data_source}
evaluation_date         date NOT NULL          -- when L5 should check (window_end + grace)
evaluation_ready        boolean NOT NULL DEFAULT false   -- PR3 (date past + candidate evidence)
candidate_evidence_jsonb jsonb                 -- PR3 (LEL event ids that MIGHT confirm/deny — NOT a verdict)
stratum_key             text                   -- PR4 (domain × confidence_tier × eval-period)
outcome_status          text NOT NULL DEFAULT 'pending' CHECK (outcome_status IN ('pending','confirmed','denied','partial'))  -- L5 WRITES these
outcome_recorded_at     timestamptz            -- NULL until L5 fills
outcome_evidence_jsonb  jsonb                  -- NULL until L5 fills
calibration_prior_jsonb jsonb                  -- PR4 reverse channel (EMPTY at L4; L5 fills; ph_nimitta reads)
l5_handoff_ref          text                   -- pointer to the mi_pramana record that will score it
derivation_ledger_jsonb jsonb NOT NULL
source_citation         text NOT NULL
computed_at             timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, prediction_ref_id)
```
> `outcome_*` + `calibration_prior_jsonb` are WRITTEN BY L5, not L4. L4 creates the row `pending`.

## §4 — Engine spec (`services/ph_pramana/engine.py`)
1. For EVERY prediction row across the ph_* assets: parse its free-text `falsifier` → the canonical
   `structured_falsifier_jsonb` (PR1).
2. Set `evaluation_date` = prediction window_end + a documented grace; set `confidence_tier` +
   `stratum_key` (PR4).
3. PR3: if evaluation_date is past, search the LEL for candidate evidence → set `evaluation_ready` +
   `candidate_evidence_jsonb`. **Do NOT compute a verdict.**
4. Register `outcome_status='pending'`, `l5_handoff_ref` placeholder, empty `calibration_prior_jsonb`.
5. **NO scoring. No LEL hit/miss. No calibration.** (Hard boundary — the gate.)
6. Anti-drift: cite the prediction_ref_id; write ONLY `phala_pramana`.

## §5 — Acceptance criteria [tagged; prod-verified]
1. `[pytest]` every prediction across all ph_* assets gets exactly one `phala_pramana` row.
2. `[pytest — PR1]` `structured_falsifier_jsonb` is machine-evaluable (has metric + comparison + threshold + window + data_source); a downstream evaluator could check it without human interpretation.
3. `[pytest — NO-SCORING HARD GATE / D5]` every row is `outcome_status='pending'`; grep the engine → ZERO hit/miss/calibration computation; a Vimarśaka boundary check confirms no LEL scoring.
4. `[pytest — PR2]` `L5_MIMAMSA_ONBOARDING_CONTRACT_v1_0.md` exists + documents the exact schema/semantics; the `phala_pramana` schema matches it.
5. `[pytest — PR3]` a prediction with a past evaluation_date + matching LEL evidence gets `evaluation_ready=true` + candidate_evidence — but NO verdict.
6. `[pytest — PR4]` predictions are stratified (stratum_key set); the empty `calibration_prior_jsonb` return-channel slot exists.
7. `[anti-drift]` writes only phala_pramana; zero `.commit()/.rollback()`; ledgers resolve.
8. `[psql_prod + curl_prod]` lit; cockpit shows ph_pramana; idempotent; FORENSIC 7/7.

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l4-ph-pramana
# the scattered hooks to unify
grep -rn "falsifiability\|falsifier_jsonb\|outcome_tracking\|calibration_hook" platform/supabase/migrations/249_l3_ka_bhavishya_lekha.sql platform/migrations/325_l2_bodha_enriched_schema.sql
# the LEL (evaluation-staging source — read for candidate evidence, NOT scoring)
sed -n '1,60p' 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md
cd platform/python-sidecar && pytest -q services/ph_pramana -k "pramana or falsifier or staging or no_scoring or contract"
```

## §7 — Definition of done
- [ ] Migration 336: phala_pramana created; ph_pramana registered (NEW asset).
- [ ] PR1 unified machine-evaluable falsifiers; PR2 L5 contract authored; PR3 evaluation-staging (no verdict); PR4 portfolio + reverse channel.
- [ ] NO-SCORING hard gate passed (zero LEL scoring/calibration in L4).
- [ ] Anti-drift clean; registered/idempotent/FORENSIC-clean; cockpit lit; PR opened.

## §8 — VALUE ADDED BY THIS BRIEF
1. **Makes the WHOLE instrument's predictions uniformly + mechanically testable** — one canonical
   machine-evaluable falsifier replacing 5 scattered empty hook shapes. The precondition for any honest calibration.
2. **Writes L5's input interface** — the producer defines the contract, so L5 Mīmāṃsā onboards against
   an unambiguous single input (unblocks the next layer cleanly).
3. **Stages evaluations without scoring** — flags what's ready + the candidate evidence, doing maximum
   useful prep while scrupulously holding the D5 no-scoring line (statistically unsound + a boundary violation to score in L4).
4. **Defines the calibration return channel** — so once L5 scores, the priors flow back to sharpen ph_nimitta — closing the correctable-prediction loop the mission demands.

## §9 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [RESOLVED — Cowork default locked]:** evaluation grace = **window_end + 90 days** (a predicted
  event may manifest slightly after its window; the grace avoids premature "denied" before L5 even checks).
- **R2 [RESOLVED — Cowork default locked]:** PR3 stages **ALL past-due predictions** for L5, **flagging
  the subset** that have candidate LEL evidence (`evaluation_ready=true`). L5 gets the full pending set,
  with the ready-to-adjudicate ones marked.

---
*End of CLAUDECODE_BRIEF_L4_PH_PRAMANA v1.0 — CLOSED. Falsifiability scaffolding at maximal capacity:
unified machine-evaluable falsifiers, the L5 onboarding contract, evaluation-staging (no verdict),
portfolio + reverse calibration channel. Strictly non-scoring (D5). R1–R2 resolved.*
