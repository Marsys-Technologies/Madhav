---
artifact: CLAUDECODE_BRIEF_L4_PH_SUDDHA_SODHANA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L4_PH_SUDDHA_SODHANA
brief_for: ph_suddha_sodhana — Best Rectification (a living, self-correcting rectification verdict) [maximal capacity]
status: FINALIZED — built on prod-verified state (GATE A) + D42/D43; ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D42 elevations, D43 flag+stage propagation, B.10 no-auto-chart-change, D5 honest)
swarm_coordination:
  wave: W4 (immediately after ph_sodhana — its selection layer)
  blocked_by: [ph_sodhana]
  blocks: [ph_phaladesa]
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_suddha_sodhana.py
    - platform/python-sidecar/services/ph_suddha_sodhana/**
    - platform/supabase/migrations/334_phala_rectification_best.sql
    - platform/scripts/seed/asset_registry_seed.ts
    - platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  hard_internal_gate: "NO-AUTO-OVERRIDE gate (D43/B.10): a test MUST prove the writer NEVER mutates the canonical chart 482012f1 (no UPDATE to chart_facts/charts) — it only STAGES + flags. Non-negotiable."
---

# CLAUDECODE BRIEF — ph_suddha_sodhana (Best Rectification) [maximal capacity]

> **What it is, in one line:** ph_suddha_sodhana is NOT a one-line argmax — it is the rectification's
> LIVING VERDICT: how decisive the chosen birth time is, a self-correcting confidence that strengthens
> as future events occur, a transparent ledger of competing hypotheses + what evidence would resolve
> them, a falsifier for the verdict itself, and a STAGED (never auto-applied) chart-revision proposal
> that honors B.10.

## §0 — Input + the reframe
ph_sodhana (W4) emits the per-candidate scored grid (`phala_rectification`) with machinery/body/
consensus scores + the leakage-clean training fit + the fine-pass range. ph_suddha_sodhana consumes
that and produces the standing verdict. **A bare argmax is barely an asset (D42) — the value is the
living, honest, self-correcting verdict.** No existing structure to inherit (verified).

## §1 — The 4 ELEVATIONS (D42)

### SS1 — Decisiveness verdict (not just a winner)
Beyond the argmax, classify the verdict: `decisiveness ∈ {decisive, probable, unresolved}` from the
win-margin (top vs runner-up) + the absolute top score. A 0.78-vs-0.76 pair → **unresolved** (two
birth times fit nearly equally; do NOT treat either as final); 0.85-vs-0.55 → **decisive**. Store
`win_margin` + `decisiveness` + the reason. The honesty that separates rigor from a confident guess.

### SS2 — Standing verification loop (self-correcting)
The held-out validation events (ph_sodhana firewall) are SCORED here against the chosen time — and as
each FUTURE life event occurs, it becomes a fresh out-of-sample test. Maintain a running
`verification_state_jsonb`: {validation_events_tested, fit_count, confidence_trajectory}. "Since
choosing 10:43, 3 new events occurred; all 3 fit the chosen Lagna; confidence 0.78 → 0.84." The
confidence STRENGTHENS (or weakens) over real, non-circular evidence — the calibration discipline
applied to the birth time itself.

### SS3 — Competing-hypotheses ledger + what resolves it
Keep the top few candidates alive (not just the winner): `hypotheses_jsonb` =
[{candidate_time, lagna, score, distinguishing_evidence}], + `resolving_evidence_note` — "Aries 10:43
(0.78) vs early-Taurus 11:02 (0.71); decided by the father's-death (Mars H1+H8 from Aries) + the
head-symptom pattern; the NEXT event that would settle it is a 7th-house/relationship event." Tells
the native exactly what future evidence resolves the residual ambiguity.

### SS4 — Falsifier for the rectification itself
The chosen birth time carries a falsifiable claim: `rectification_falsifier` — "if 3+ of the next 10
events fit early-Taurus materially better than Aries, this rectification is CHALLENGED → re-open." Hand
it UP to L5 (via ph_pramana / the outcome hook) with the same outcome-tracking discipline as every
other prediction.

## §2 — Propagation: FLAG + STAGE, never auto-override (D43 / B.10)
> **THE SAFETY RAIL.** The canonical chart `482012f1` is the foundation ALL layers rebuild on; the fit
> confidence is partly CIRCULAR (L2 signals were built knowing this native's life). So:
- ph_suddha_sodhana records the chosen time + confidence but **NEVER mutates the canonical chart**
  (no UPDATE to `charts`/`chart_facts`). Enforced by the hard gate.
- If the rectified Lagna **differs materially** from the recorded 10:43 at high confidence, it PREPARES
  a staged revision: compute what the rectified chart WOULD be, store the diff in
  `staged_revision_jsonb`, and set `revision_recommended = true` + a plain-language flag ("rectification
  suggests 10:47, not 10:43 — adopting it would shift [N] facts; native decision + version bump
  required"). Adoption is a one-click native action elsewhere — NOT this asset's job.
- If the rectified Lagna AGREES with 10:43 (the likely case — legacy preliminary was Aries 0.72):
  `revision_recommended = false`; the asset CONFIRMS the recorded time.

## §3 — Schema (migration 334)
`phala_rectification_best`:
```
best_id                 uuid PK
chart_id                uuid NOT NULL
run_id                  uuid NOT NULL
chosen_rectification_id uuid REFERENCES phala_rectification(rectification_id)   -- the argmax (anti-drift FK)
chosen_time_low         time
chosen_time_peak        time
chosen_time_high        time
chosen_lagna_sign       text NOT NULL
chosen_confidence       double precision
win_margin              double precision        -- SS1
decisiveness            text CHECK (decisiveness IN ('decisive','probable','unresolved'))  -- SS1
decisiveness_reason     text                    -- SS1
verification_state_jsonb jsonb NOT NULL          -- SS2 (held-out + future events, confidence trajectory)
hypotheses_jsonb        jsonb NOT NULL           -- SS3 (top candidates + distinguishing evidence)
resolving_evidence_note text                     -- SS3 (what future event settles it)
rectification_falsifier text NOT NULL            -- SS4 (hands UP to L5)
revision_recommended    boolean NOT NULL DEFAULT false   -- D43
staged_revision_jsonb   jsonb                    -- D43 (the staged diff IF revision_recommended; chart NOT mutated)
revision_flag_note      text                     -- D43 (plain-language native-decision flag)
agrees_with_recorded    boolean                  -- D43 (true → confirms 10:43)
run_at                  timestamptz
derivation_ledger_jsonb jsonb NOT NULL
source_citation         text NOT NULL
computed_at             timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, run_id)
```

## §4 — Engine spec (`services/ph_suddha_sodhana/engine.py`)
1. Argmax over `phala_rectification` by `composite_fit_score`; record chosen + win_margin.
2. SS1: classify decisiveness from win_margin + top score.
3. SS2: score the held-out validation events against the chosen time; init the verification_state +
   confidence trajectory (future-event updates are re-runs of this asset).
4. SS3: assemble the top-few hypotheses + their distinguishing evidence + the resolving-event note.
5. SS4: generate the rectification falsifier; wire the outcome hook for L5.
6. D43: compare chosen Lagna to the recorded 10:43; if materially different + high confidence → compute
   + STAGE the revision diff, set revision_recommended + the flag. **NEVER UPDATE the canonical chart.**
7. Anti-drift: cite the chosen rectification_id + the event ids; write ONLY `phala_rectification_best`.

## §5 — Acceptance criteria [tagged; prod-verified]
1. `[pytest]` the chosen row is the true argmax of `phala_rectification.composite_fit_score`; win_margin recorded.
2. `[pytest — SS1]` decisiveness is `unresolved` when the top two are within a small margin; `decisive` when the margin is large.
3. `[pytest — SS2]` held-out validation events are scored against the chosen time (NOT used in the fit — they were the firewall); verification_state + trajectory populated; a re-run with a new event updates confidence.
4. `[pytest — SS3]` the top-few hypotheses are retained with distinguishing evidence + a resolving-event note.
5. `[pytest — SS4]` a rectification falsifier is emitted + wired to the L5 outcome hook.
6. `[pytest — D43 / HARD GATE]` the writer NEVER issues an UPDATE to `charts`/`chart_facts` (grep + a runtime assert); a materially-different high-confidence Lagna sets `revision_recommended=true` + a staged diff, but the canonical chart is UNCHANGED.
7. `[anti-drift]` writes only phala_rectification_best; zero `.commit()/.rollback()`; ledgers resolve; `WriterResult(asset_id='ph_suddha_sodhana', rows_inserted=N)`.
8. `[psql_prod + curl_prod]` lit with ≥1 verdict row; cockpit shows ph_suddha_sodhana; idempotent; FORENSIC 7/7 (canonical chart untouched).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l4-ph-suddha-sodhana
psql "$DATABASE_URL" -c "SELECT candidate_time, composite_fit_score FROM phala_rectification WHERE chart_id=:'NATIVE' ORDER BY composite_fit_score DESC;"
# prove no canonical-chart mutation
grep -rn "UPDATE charts\|UPDATE chart_facts" platform/python-sidecar/services/ph_suddha_sodhana/ || echo "CLEAN (no chart mutation)"
cd platform/python-sidecar && pytest -q services/ph_suddha_sodhana -k "suddha or best or decisive or verification or stage or no_override"
```

## §7 — Definition of done
- [ ] Migration 334: phala_rectification_best created.
- [ ] SS1 decisiveness + SS2 verification loop + SS3 hypotheses ledger + SS4 falsifier implemented + tested.
- [ ] D43: flag + STAGE on divergence; NO-AUTO-OVERRIDE hard gate passed (canonical chart never mutated).
- [ ] Anti-drift clean; registered/idempotent/FORENSIC-clean; cockpit lit; PR opened.

## §8 — VALUE ADDED BY THIS BRIEF
1. **A living rectification verdict, not a one-line argmax** — decisive-or-not, self-correcting as life
   unfolds, transparent about competing hypotheses + what resolves them, falsifiable.
2. **The standing verification loop** turns the held-out firewall events + future events into a
   non-circular, strengthening confidence — the calibration discipline applied to the birth time itself.
3. **The propagation safety rail (D43/B.10)** — stages a revision for one-click native adoption but
   NEVER silently mutates the foundation on a partly-circular score. The one place a human gate is most wanted.
4. **Honest about the likely outcome** — if the recorded 10:43 fits, it CONFIRMS it (not always casting doubt).

## §9 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [RESOLVED — Cowork default locked]:** decisiveness — `decisive` if win_margin ≥0.15 AND top
  ≥0.70; `unresolved` if win_margin <0.05; else `probable`.
- **R2 [RESOLVED — Cowork default locked]:** "materially different" (triggers the revision flag) = a
  DIFFERENT Lagna SIGN (e.g. Aries vs Taurus) at chosen_confidence ≥0.75. A within-sign degree shift
  does NOT trigger a chart revision (it refines the time, not the Lagna).

---
*End of CLAUDECODE_BRIEF_L4_PH_SUDDHA_SODHANA v1.0 — CLOSED. A living rectification verdict —
decisiveness, self-correcting verification loop, competing-hypotheses ledger, self-falsifier, and the
flag+stage propagation safety rail (never auto-override). R1–R2 resolved.*
