---
artifact: 07_mi_pariksha_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_PARIKSHA
asset_id: mi_pariksha
asset_kind: data
scope: per_chart
activation: v1 core + tiered discovery
version: 1.0
status: DRAFT — build-ready spec
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [§C per-dim/per-channel attribution, §F neg-control harness blocking, §G degenerate-distribution guard, §A G1 emergent-law, §A G4 contradiction-dominance, §A G5 temporal rhythm, §A G7 residual discovery]
---

# mi_pariksha — Attribution, Self-Examination & Discovery Engine

> Sanskrit: *Parīkṣā* ("examination / testing"). The self-examining mind of L5. Three jobs: (1)
> **attribute** each scorecard back to the signals that drove it, per dimension AND per channel; (2) run
> the **negative-control battery harness** (the blocking lie-detector) + the **degenerate-distribution
> guard**; (3) **the discovery engine** — mine the outcome corpus for emergent per-native laws,
> contradiction-dominance, temporal rhythms, and residual candidate signals (G1/G4/G5/G7). This is where
> L5 becomes superhuman, not just honest. Discovery is outcome-mining → activation-tiered by evidence.

## §1 — Purpose & value
- **Attribution (Pillar 2 / LL.9):** turns "the prediction missed" into "signal X on the timing dimension
  is what failed" — the precise, per-dimension credit/blame that lets learning be surgical.
- **Self-examination harness:** runs the negative controls (must score null → blocks seal if not) and the
  degenerate-distribution guard (catches the all-Jupiter class).
- **Discovery (the mind):** mines the whole scored corpus for patterns no acharya could compute — emergent
  reliability laws (G1), which side of a contradiction wins (G4), temporal rhythms/lead-lag (G5), and
  residual-driven new candidate signals (G7). All deterministic; discovery proposes, the honesty gates
  dispose.

## §2 — Inputs
| source | what |
|---|---|
| `mimamsa_calibration` + `mimamsa_reliability` (`mi_pramana`) | the scorecards + curves to attribute + mine |
| `mimamsa_predictions.driving_signals` (`mi_bhavisya`) | the signal lineage per prediction |
| `mimamsa_signal_families` + `mimamsa_negative_controls` (`mi_kula`) | family defs + the trap battery |
| L2 contradictions / CDLM (`bodha_*`) | the tensions whose dominance G4 resolves |
| `mi_pramana.manifestation_channel` | feeds the channel attribution (and `mi_sambandha`) |
| all computed attribution columns (any asset) | the degenerate-distribution guard scans these |

## §3 — Output schema (build-ready)

### Table: `mimamsa_attribution` (per-dimension + per-channel credit/blame)
```
chart_id, match_id, signal_id, family_id,
dimension                text     -- 'timing'|'magnitude'|'domain'|'falsifier'|'manifestation'
credit_blame             numeric  -- signed: + when the dimension scored well, − on miss
channel_fired            text     -- which manifestation channel (feeds mi_sambandha)
attribution_formula_ver  text
PRIMARY KEY (chart_id, match_id, signal_id, dimension)
```

### Table: `mimamsa_qa_eval` (harness results — neg-control + distribution)
```
chart_id, check_id,
check_type               text     -- 'negative_control'|'degenerate_distribution'|'reproducibility'
target                   text     -- the NC id, or the column scanned
result_score             numeric
status                   text     -- 'pass'|'FAIL'   (FAIL blocks seal)
detail                   jsonb
checked_at               timestamptz
PRIMARY KEY (chart_id, check_id)
```

### Table: `mimamsa_discoveries` (the emergent insight — G1/G4/G5/G7)
```
chart_id, discovery_id,
discovery_class          text     -- 'emergent_law'(G1)|'contradiction_dominance'(G4)|'temporal_rhythm'(G5)|'residual_candidate'(G7)
statement                text     -- the law in structured form
evidence_refs            jsonb    -- the calibration rows/strata behind it
strength                 numeric  -- effect size / consistency
n_support                int      -- how many events support it (R5)
confidence_band          numrange
activation_status        text     -- 'candidate'|'supported'|'promoted'  (tiered by n)
citation_required        boolean  -- G7 residual candidates need a classical citation before use
citation_ref             jsonb
discovery_formula_ver    text
PRIMARY KEY (chart_id, discovery_id)
```

## §4 — Computation logic (deterministic)

### 4.1 — Per-dimension + per-channel attribution
- For each scored match, distribute credit/blame to its `driving_signals` **by the dimension each signal
  drives**: a signal tagged `role='when'` gets the timing score; `role='what'` gets domain; etc. Record
  `channel_fired` (→ `mi_sambandha`). A miss is traced to the specific signal × dimension that failed.
  Deterministic mapping; no LLM.

### 4.2 — Negative-control harness (BLOCKING) + degenerate guard
- **Neg-control:** compute each `mimamsa_negative_controls` definition against the chart/dates and score it
  like a real signal. `status='FAIL'` if `|result_score| > tolerance` (it fired when it must not). **Any
  FAIL blocks the seal and blocks all promotion (E3)** — written back so `mi_gunanaka.neg_control_clear`
  reflects it.
- **Degenerate-distribution guard (RL-6):** scan every computed attribution column across L5 (planet,
  family, manifestation channel, domain, verdict, confidence tier…). If any collapses to a single value
  where diversity is expected → `FAIL` + flag. (Catches the all-Jupiter class at build time.)

### 4.3 — Discovery engine (G1/G4/G5/G7) — outcome-mining, activation-tiered
All deterministic statistical mining over the scored corpus; **proposes**, honesty-gates **dispose**.
- **G1 emergent laws:** per (family × domain × confidence-tier), compute reliability deviations from the
  global rate → "family F fires 0.8 in career, 0.2 in health for this native"; "confirmed events share a
  ≥3-family convergence." Stored as `emergent_law` with effect size + n.
- **G4 contradiction-dominance:** for each L2 contradiction (signal A vs B), compute which side's
  predictions actually confirm more often → the empirical dominance order. Stored as
  `contradiction_dominance`.
- **G5 temporal rhythm/lead-lag:** time-series mine the confirmed-event sequence for rhythms (clustering
  at dāśā-lord changes, lead-lag between domains). Stored as `temporal_rhythm`. (Most data-hungry → highest
  activation tier.)
- **G7 residual candidate:** where misses cluster on a chart feature NOT in the current family set, flag a
  `residual_candidate` — a hypothesis. **`citation_required=true`: it cannot be used/promoted until a
  classical citation is attached** (same discipline as manifestation additions; bounded discovery).
- **Activation tiering:** `candidate` (any signal) → `supported` (n ≥ threshold + held-out) → `promoted`
  (full gate, like weights). At n=1 today most stay `candidate` — correct; value compounds with the journal.

### 4.4 — No-LEL behavior
- Attribution + discovery produce nothing empirical (no scored matches). The harness still validates
  structure (degenerate guard runs on structural columns; neg-controls report `untested`). Discovery tables
  empty until events accrue.

## §5 — Retrievability contract (feeds mi_darshana)
- **Discoveries are prime retrievable insight units** — the emergent laws, dominance maps, rhythms — each
  with strength + n + activation_status + confidence (R5). This is the superhuman insight the LLM
  synthesizes. Attribution feeds the provenance chain (R4). Harness FAILs + residual candidates feed
  negative knowledge (R6).

## §6 — Determinism & seal gates
- No LLM in attribution/harness/mining (D-1); LLM may only *propose* a G7 candidate's interpretation,
  citation-gated before use. Frozen formula versions (D-2); re-run identical (RL-1).
- **Negative-control blocking gate (E3):** any NC FAIL → no seal, no promotion. THIS asset owns the harness.
- **Degenerate-distribution gate (RL-6):** owned here; scans all L5 attribution columns.
- **Reproducibility check** (`check_type='reproducibility'`) runs here too.
- Registered with drift_detector + schema_validator (RL-5).

## §7 — Frozen-orchestrator conformance
`@register('mi_pariksha')` `WriterBase`; per_chart; `plan_substeps`+`run_substep` (attribution → harness →
discovery); delete-then-insert per `(chart_id × key)`; `conn=ctx.db_conn` never committed; `count_sql`:
`SELECT count(*) FROM mimamsa_qa_eval WHERE chart_id = $1`.

## §8 — `depends_on`
`['mi_pramana', 'mi_kula']` (+ reads `mi_bhavisya`, L2 contradictions). `[P2 reconcile]`.

## §9 — Matrix rows satisfied
per-dimension + per-channel attribution (§C) ✅ · neg-control harness BLOCKING (§F/E3) ✅ ·
degenerate-distribution guard (§G/RL-6) ✅ · G1 emergent-law (§A) ✅ · G4 contradiction-dominance (§A) ✅ ·
G5 temporal rhythm (§A) ✅ · G7 residual discovery citation-gated (§A) ✅ · reproducibility check (§G) ✅ ·
R4/R6 sources ✅ · determinism (§G) ✅.

*End 07_mi_pariksha_SPEC v1.0.*
