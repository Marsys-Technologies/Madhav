---
artifact: CLAUDECODE_BRIEF_L3_KA_BHAVISHYA_LEKHA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_BHAVISHYA_LEKHA
brief_for: ka_bhavishya_lekha — Bhaviṣya-lekhā / THE PREDICTION-RECORD EMITTER (L3 Kāla; the L5 learning hook) [NEW]
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.13.D + I-24 (feature-tagged falsifiable calibratable prediction records → L5), §5.4 (the eval SPLIT: L3 MAKES predictions, L5 calibrates), §14.1 (L3 emits → L5 mi_bhavisya/mi_pramana consume), QT-6 (diagnostic/retrodiction is the same record run backward), §5.11.6 (confidence vocabulary)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K6
  blocked_by: [ka_sangam, ka_vighnakara, ka_kala_darshana]   # predictions are emitted FROM the scored windows + discoveries
  blocks: []   # the LAST L3 producer; hands UP to L5 (mi_bhavisya) — which is a different layer, not an L3 dependency
  may_touch:
    - platform/python-sidecar/services/ka_bhavishya_lekha/**            # NEW (the emitter)
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py  # writer (the prediction records)
    - platform/supabase/migrations/<next>_kala_prediction_records.sql   # NEW L3 table (the emitted records, pre-L5)
    - platform/scripts/seed/asset_registry_seed.ts                      # register ka_bhavishya_lekha (artifact-kind)
  must_not_touch:
    - mimamsa_predictions / mimamsa_calibration tables   # L5 OWNS these; L3 emits records SHAPED for them, L5 ingests
  parallel_safe_with: [ka_tulana, ka_jivana_parva]   # all K6 derived; disjoint
---

# CLAUDECODE BRIEF — ka_bhavishya_lekha (The Prediction-Record Emitter) [NEW]

## §0 — What this asset IS
`ka_bhavishya_lekha` (Bhaviṣya-lekhā, "the inscription/record of what is to come") is the **prediction-
record emitter** — the L3→L5 LEARNING HOOK. For each consequential window L3 produces (opportune from
`ka_sangam`, danger from `ka_vighnakara`, discovery from `ka_kala_darshana`), it emits a **feature-tagged,
falsifiable, calibratable PREDICTION RECORD**: a datable, confidence-bearing, falsifier-carrying claim,
shaped so L5 Mīmāṃsā can validate it against lived reality (the LEL) and feed weights BACK (plan §5.13.D).
**This is what makes the whole MARSYS learning loop REAL** — without it, L3's windows are unfalsifiable and
L5 can learn nothing. Per the eval split (plan §5.4): **L3 MAKES the prediction; L5 JUDGES it.**

## §1 — Why it matters / strategic role
- **It closes the learning loop (plan §5.13.D).** L3's predictions become L5's calibration corpus
  (reliability curves, Brier scores); the I-7/I-16 weights become LEARNABLE. The instrument IMPROVES.
- **It is an L3 DESIGN OBLIGATION, not an L5 afterthought (plan §5.13.D).** If L3 emits bare windows, L5
  can't calibrate. The records must carry their FEATURES (which triggers, magnitudes, convergence score,
  rarity, confidence, independent-current count) so a wrong prediction is a learnable signal, not a mystery.
- **It powers QT-6 (diagnostic/retrodiction).** The same record run BACKWARD answers "*why* was [past
  event] happening" — replaying a known LEL event through the predicates (the eval-gate input, plan §5.4).

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **The L5 target schema EXISTS and defines the contract** (`mimamsa_predictions`): `prediction_id,
  chart_id, predicted_at, horizon_date, domain, prediction_text, confidence (CHECK 0<c<1), falsifier,
  source_citation`, + the L5-FILLED outcome fields `outcome_observed bool, brier_score (CHECK [0,1]),
  outcome_recorded_at`. A CHECK enforces `horizon_date >= predicted_at` and brier-requires-outcome.
  **L3's emitted records MUST be shaped to drop into this table** (L5 ingests them).
- **`mimamsa_calibration`** keys on `technique` + `ayanamsha_id` + `brier_score` + `sample_size` → L5
  calibrates PER TECHNIQUE. So each L3 record should tag the `technique` (the signature_class / template
  that produced it) so L5 can calibrate per archetype.
- **`mi_bhavisya` is registered** `depends_on: ['bo_laksana','ka_kalasutra']` — confirming L5 reads L2 +
  the L3 temporal artifact. `ka_bhavishya_lekha` is the producer of the records it ingests.
- **The pairing is intentional:** L3 `Bhaviṣya-lekhā` (the record) ↔ L5 `Bhaviṣya` (the prediction store).

## §3 — The build (the feature-tagged record + the hand-up)
**3.1 — The PREDICTION RECORD schema (I-24).** An L3 table `kala_prediction_records`, one row per emitted
prediction, carrying BOTH the L5-target fields AND the L3 features:
- L5-target (so it drops into `mimamsa_predictions`): `chart_id, predicted_at, horizon_date` (the window
  peak), `domain` (from the signal's `domains_affected`), `prediction_text` (the datable claim),
  `confidence ∈ (0,1)` (from `ka_sangam` confidence_score, clamped open-interval), `falsifier` (the
  condition that would prove it WRONG — non-null, plan B6 discipline), `source_citation`.
- L3 features (so L5 can calibrate per driver): `signal_id` (L2 ref), `signature_class` (the `technique`),
  `mode` (A/B), `convergence_score`/`severity`, `rarity_years`, `independent_current_count`,
  `constituent_triggers_jsonb` (which transit/daśā/panchāṅga factors fired), `window_ref` (→ ka_sangam/
  ka_vighnakara/ka_kala_darshana row).
- The L5-filled fields (`outcome_observed`, `brier_score`, `outcome_recorded_at`) are LEFT NULL by L3 —
  L5 fills them (the symmetry of the L2 NULL-hook discipline). **L3 NEVER writes the outcome.**

**3.2 — Emit from every consequential window.** Walk `ka_sangam` (top opportune), `ka_vighnakara` (top
danger), `ka_kala_darshana` (the discoveries) and emit one record each (above a consequence threshold —
do not flood L5 with trivia; the threshold is native-ratifiable). Each record is DATABLE (horizon_date =
peak) and FALSIFIABLE (the falsifier states what observation would refute it).

**3.3 — The LEL toggle (plan §9).** Honor `lel_enabled`/`lel_origin`: when LEL is enabled, records may be
calibrated against past LEL events (the QT-6 retrodiction path); when disabled, records are forward-only
and carry no LEL contamination. The emitter tags `lel_origin=false` for all forward predictions.

**3.4 — The hand-up contract (plan §14.1 / R-4).** Define + document the interface by which L5
`mi_bhavisya` ingests `kala_prediction_records`. L3 writes ONLY its own table; L5's writer reads it. **L3
does NOT write `mimamsa_predictions`** (that's L5's table — see must_not_touch). This keeps the make/judge
separation clean (plan §5.4).

**3.5 — Retrodiction mode (QT-6).** Provide the backward path: given a known past LEL event, run the
predicates to produce "what was active then + would L3 have predicted it" — the input to L3's own
COMPUTATIONAL eval gate (plan §5.4) and to L5's calibration.

## §4 — Asset registration (NEW, artifact-kind)
`ka_bhavishya_lekha`: `asset_kind='artifact'`, `layer:'kala'`, sanskrit `'Bhaviṣya-lekhā'`, english
`'Prediction-record emitter'`, `target_table:'kala_prediction_records'`, chart-scoped count_sql,
`depends_on: ['ka_sangam','ka_vighnakara','ka_kala_darshana']`. Per-chart, ×5 ayanamsha. Idempotent
delete-then-insert (plan §N.3).

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: pytest]** every emitted record has the L5-target fields populated (horizon_date >=
   predicted_at; 0<confidence<1; non-null falsifier) AND the L3 features (signature_class as technique,
   convergence/rarity/independent-count, constituent_triggers).
2. **[verify: pytest]** a record drops cleanly into the `mimamsa_predictions` shape (a transform test:
   the L3 record → a valid mimamsa_predictions row, all CHECKs satisfied).
3. **[verify: pytest]** the outcome fields (`outcome_observed`, `brier_score`) are NULL on emission —
   L3 never writes them (L5 owns the outcome).
4. **[verify: pytest]** retrodiction (QT-6): a known past LEL event replayed produces "what was active +
   would-have-predicted" — the eval-gate input. LEL toggle honored (lel_origin tagged).
5. **[verify: anti-drift]** each record references a resolving L2 `signal_id` + the L3 window_ref; no
   writes to `mimamsa_predictions`/`mimamsa_calibration` (L5 tables — grep → 0); no L2 writes.
6. **[verify: threshold]** only consequential windows emit records (no L5 flooding); the threshold is
   documented + native-ratifiable.
7. **[verify: psql_prod + curl_prod]** registered artifact-kind; cockpit count; the hand-up interface to
   `mi_bhavisya` documented (R-4); idempotent rebuild; FORENSIC chart unaffected.
8. **[contract]** the writer never commits/rolls back `ctx.db_conn` (plan §9 / Vimarśaka-RED).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-bhavishya-lekha
# the L5 target contract
sed -n '/CREATE TABLE IF NOT EXISTS public.mimamsa_predictions/,/);/p' platform/supabase/migrations/0001_brahma_baseline.sql
# tests
cd platform/python-sidecar && pytest -q services/ka_bhavishya_lekha -k "bhavishya or prediction or record or retrodict"
```
> Branch/merge: Madhav human-gated PR. L3 emits records; it must NOT write the L5 tables (separation).

## §7 — Definition of done
- [ ] Prediction-record schema (L5-target fields + L3 features); records drop into mimamsa_predictions shape.
- [ ] Emit from ka_sangam/ka_vighnakara/ka_kala_darshana above a documented threshold; falsifier non-null.
- [ ] Outcome fields NULL on emission (L5 fills); LEL toggle honored.
- [ ] Retrodiction (QT-6) path for the eval gate.
- [ ] Hand-up interface to mi_bhavisya documented (R-4); no L5/L2 writes.
- [ ] Registered artifact-kind; idempotent; FORENSIC-clean; PR opened.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Makes the entire MARSYS learning loop real** — without feature-tagged calibratable records, L3's
   windows are pretty but unfalsifiable and L5 has nothing to calibrate; this brief is the single hinge
   that turns the instrument from static to SELF-IMPROVING.
2. **Honors the eval split structurally** — L3 emits, L5 judges; by shaping records for `mimamsa_predictions`
   but NEVER writing the outcome fields or the L5 tables, it enforces make/judge separation in code, not
   just in doctrine (plan §5.4).
3. **Carries the FEATURES, not just the verdict** — tagging each record with its signature_class
   (technique), convergence/rarity/independence so L5 can calibrate PER ARCHETYPE is what lets the
   weights become learnable; a bare prediction would make L5's calibration uninterpretable.
4. **Reuses the proven L5 schema** — the registered `mimamsa_predictions` already encodes the
   falsifier-required + Brier-calibration discipline; the emitter targets that contract exactly, so L3
   and L5 interlock without a translation layer.
5. **Delivers retrodiction (QT-6) for free** — the same record run backward both answers "why was that
   happening" AND provides L3's own computational eval-gate input (replay a known LEL event), so one
   mechanism serves diagnosis, self-test, and calibration.
6. **Respects the LEL toggle at the prediction boundary** — tagging lel_origin and gating LEL use means
   forward predictions stay contamination-free, preserving the falsifiability that makes calibration meaningful.

---
*End of CLAUDECODE_BRIEF_L3_KA_BHAVISHYA_LEKHA v1.0. The record of what is to come — the L5 learning hook.*
