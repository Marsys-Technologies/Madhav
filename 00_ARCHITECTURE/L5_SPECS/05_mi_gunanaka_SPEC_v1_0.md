---
artifact: 05_mi_gunanaka_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_GUNANAKA
asset_id: mi_gunanaka
asset_kind: data
scope: per_chart
activation: v1
version: 1.0
status: DRAFT — build-ready spec ([P2] numbers: min-n, caps, high-confidence threshold)
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [§D bounded weight source, §D two-key gate, §F learning-eligible hard gate E1, §F very-strict n-aware promotion E2, §G kill-switch/drift RL-4]
---

# mi_gunanaka — Learned-Weight Register (shadow → promoted, hard-gated)

> Sanskrit: *Guṇānaka* ("multiplier / that which scales"). The home of every **learned weight** — the
> empirical multipliers L5 derives from calibration. It governs the prior→earning→promoted→suspended
> lifecycle with a **very strict, n=1-aware promotion gate**, and supplies the two-key lock with both
> keys (gate-passed + high-confidence). Nothing here moves a reading by itself — it hands weights to the
> overlay (`mi_adhilepa`) under strict conditions.

## §1 — Purpose & value
- Holds the LL.1 signal/family weights (active) and the **structure** for LL.2–LL.8 (designed, dormant).
- Implements the **hard promotion gate** (E1/E2): a weight only graduates from prior to empirical-trusted
  after enough clean+held-out evidence and passing the negative-controls.
- Provides the **two keys** the overlay needs: `gate_passed` AND `confidence_high`.
- Runs **kill-switches**: suspends a weight/family whose calibration degrades; alerts on learned-vs-
  classical divergence.

**Governing principle embedded:** strict unless high-confidence; default restraint; almost nothing
promotes at n=1, and that is correct.

## §2 — Inputs
| source | what |
|---|---|
| `mimamsa_reliability` + `mimamsa_calibration` (`mi_pramana`) | the calibration that earns/loses weight |
| `mi_kula` | family definitions, prior weights, interaction value, neg-control pass/fail |
| `mi_jivanaghatana` | n + held-out validity per stratum |

## §3 — Output schema (build-ready)

### Table: `mimamsa_multipliers`  (the learned-weight register; per chart × weight)
```
chart_id                 uuid       not null
weight_id                text       not null     -- e.g. 'signal:SIG.x@career' or 'family:X-GEOMAG@health'
mechanism                text       not null     -- 'LL1'|'LL2'..'LL8' (LL1 active; others dormant-structured)
target_kind              text       not null     -- 'signal'|'family'|'edge'|'window'  (what it modulates)
target_ref               text       not null     -- the origin id it attaches to (single-origin attribution key)
domain                   text                    -- stratum
raw_multiplier           numeric    not null     -- from calibration (predicted vs observed)
evidence_factor          numeric    not null     -- g(n, leakage, evidence_strength) ∈ [0,1]; 0 below min_n
applied_multiplier       numeric    not null     -- 1 + (raw-1)*evidence_factor  (the bounded-input value)
n_observations           int        not null
held_out_validity        text       not null     -- 'pass'|'fail'|'insufficient_n' (from mi_pramana)
promotion_status         text       not null     -- 'prior_only'|'earning'|'promoted'|'suspended'
gate_passed              boolean    not null      -- E1/E2 hard gate result (KEY 1 of two-key lock)
confidence_high          boolean    not null      -- is the resulting confidence high? (KEY 2)
neg_control_clear        boolean    not null      -- did the battery pass? (E3 precondition)
kill_switch_state        text       not null      -- 'active'|'suspended_degrading'|'suspended_divergence'
divergence_from_classical numeric                 -- learned vs classical prior gap (alert if > tol)
audit_trail              jsonb      not null       -- versioned history (reversible)
weight_formula_version   text       not null
updated_at               timestamptz not null
PRIMARY KEY (chart_id, weight_id)
```

## §4 — Computation logic (deterministic)

### 4.1 — Weight derivation (LL.1 active)
- For each stratum with sufficient clean calibration, `raw_multiplier` = deterministic function of
  (observed_rate vs predicted_prob) — a signal that over-fired gets `raw < 1`, under-fired `raw > 1`.
- `evidence_factor = g(n, leakage_status, evidence_strength)`, **0 below `min_n`** (thin n → no shift).
- `applied_multiplier = 1 + (raw_multiplier - 1) * evidence_factor` (the value the overlay will further
  clamp by per-layer cap). `[P2: min_n, the g() shape]`.

### 4.2 — The hard promotion gate (E1 + E2 + E3)
```
gate_passed =
      held_out_validity == 'pass'                 -- held-out, not just in-sample
  AND n_observations    >= min_n_promote           -- very strict, n-aware [P2]
  AND neg_control_clear == true                    -- the battery passed (E3)
  AND divergence_from_classical <= max_divergence  -- doesn't violate priors-locked (#1)
promotion_status: prior_only → earning (some evidence) → promoted (gate_passed) ; → suspended (kill-switch)
```
- At n=1 today, `gate_passed` will almost always be false → almost nothing promotes. **Correct behavior.**

### 4.3 — The two keys (for mi_adhilepa)
- `gate_passed` (KEY 1) and `confidence_high` (KEY 2, = resulting confidence ≥ `high_conf_threshold [P2]`).
- The overlay applies a weight to a **real reading** only when BOTH are true. Otherwise the weight is
  computed + stored (suggestion mode) but the overlay reads base, not effective.

### 4.4 — Kill-switches + drift (RL-4)
- `suspended_degrading`: if a weight's calibration error worsens over a rolling window of N updates.
- `suspended_divergence`: if `divergence_from_classical` exceeds tolerance (priors-locked #1 protection).
- A suspended weight reverts the overlay to base for its origin; the suspension + reason are auditable +
  reversible (audit_trail).

### 4.5 — LL.2–LL.8 structure (dormant)
- Rows for higher mechanisms are schema-supported (`mechanism` column) but not computed at v1
  (`promotion_status='prior_only'`, no derivation). Designed-in; switched on as evidence + native sign-off
  arrive. Keeps the register future-proof without activating un-earnable learning at n=1.

### 4.6 — No-LEL behavior
- All weights `prior_only`; `gate_passed=false` everywhere; the register reflects only prior weights. No
  empirical multiplier exists; the overlay applies prior-tier modulation only (governed by toggles).

## §5 — Retrievability contract (feeds mi_darshana)
- The register is retrievable as "what the instrument has learned to trust/distrust for this native,"
  each weight carrying promotion_status + n + held_out_validity (R5). **Suspended weights = negative
  knowledge (R6)** ("we tried to trust X and it didn't hold up").

## §6 — Determinism & seal gates
- No LLM (D-1). Frozen `weight_formula_version` (D-2); re-run identical (RL-1).
- **Promotion-gate integrity:** assert no `promoted` without all gate conditions (E1/E2/E3).
- **Priors-locked:** assert no weight overwrites a classical prior (modulate-only) — divergence cap.
- Reversibility: every status change is in `audit_trail` (LL discipline #5).
- Degenerate-distribution guard on `promotion_status`, `kill_switch_state`.
- Registered with drift_detector + schema_validator (RL-5).

## §7 — Frozen-orchestrator conformance
`@register('mi_gunanaka')` `WriterBase`; per_chart; delete-then-insert on `(chart_id × weight_id)`;
`conn=ctx.db_conn` never committed; `count_sql`: `SELECT count(*) FROM mimamsa_multipliers WHERE chart_id = $1`.

## §8 — `depends_on`
`['mi_pramana']` (+ reads `mi_kula`, `mi_jivanaghatana`). `[P2 reconcile]`.

## §9 — Matrix rows satisfied
bounded weight source (§D) ✅ · two-key gate keys (§D/V4) ✅ · learning-eligible hard gate E1 (§F) ✅ ·
very-strict n-aware promotion E2 (§F) ✅ · kill-switch + drift RL-4 (§G) ✅ · priors-locked + reversible
(§G) ✅ · LL.2–LL.8 dormant structure ✅ · R6 negative-knowledge (suspended) ✅ · determinism gates (§G) ✅.

*End 05_mi_gunanaka_SPEC v1.0.*
