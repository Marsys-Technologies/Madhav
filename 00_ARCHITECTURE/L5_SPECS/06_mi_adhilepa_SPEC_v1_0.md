---
artifact: 06_mi_adhilepa_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_ADHILEPA
asset_id: mi_adhilepa
asset_kind: data
scope: per_chart
activation: v1
version: 1.0
status: DRAFT — build-ready spec ([P2] per-layer caps)
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [§D overlay model, §D 4 overlay tables, §D single-origin dedup, §D bounded+evidence-scaled, §D L1→L4-never-L0, §D two-key apply, §A G3 load-bearing/sensitivity, §G double-count/no-L0 gates]
---

# mi_adhilepa — Overlay Surface, Propagation & Load-Bearing Map

> Sanskrit: *Adhilepa* ("an overlay / coating laid on top"). The reverse-channel surface. It writes
> L5's learned adjustments to its **own overlay tables** keyed to upstream ids — never mutating L1–L4 —
> so the deterministic base and the adapted value stay strictly segregated. It applies adjustments
> **once per consumption path** (single-origin dedup), **bounded + evidence-scaled**, and only to a real
> reading under the **two-key lock**. It also computes the **load-bearing/sensitivity map** (G3).

## §1 — Purpose & value
- The ONLY layer with a downward arrow: learned weights flow back to damp/boost L1–L4 values **as an
  overlay**, read-side, never as mutation.
- Solves the cross-layer **double-counting** problem (the `bodha_msr_signals` keystone fans out to 15+
  consumers) via single-origin attribution.
- Computes, cheaply and superhumanly, **which signals are load-bearing vs redundant** for each conclusion
  (G3) — a counterfactual map no acharya could hold.

## §2 — Inputs
| source | what |
|---|---|
| `mimamsa_multipliers` (`mi_gunanaka`) | the bounded applied_multiplier + the two keys (gate_passed, confidence_high) |
| L1–L4 base tables (read-only) | `chart_facts`, `bodha_msr_signals` (asset `bo_laksana`), `kala_convergence` (asset `ka_sangam`), `phala_anchors` (asset `ph_nimitta`) — the base values + lineage. NOTE: these are TABLE reads, not `depends_on` edges; `depends_on` uses asset-ids (audit §2) |
| `mi_pramana` derived_from refs | the calibration verdicts behind each adjustment (attribution ledger) |

## §3 — Output schema (build-ready) — the 4 overlay tables + sensitivity

All four share the overlay shape (keyed to the **origin** id they adjust). **No L1–L4 row is ever written.**

### `mimamsa_signal_adjustment` (origin: bodha_msr_signals.signal_id — the keystone)
### `mimamsa_fact_adjustment` (origin: chart_facts.fact_id)
### `mimamsa_convergence_adjustment` (origin: kala_convergence.convergence_id)
### `mimamsa_anchor_adjustment` (origin: phala_anchors.anchor_id)
```
chart_id                 uuid       not null
origin_layer             text       not null     -- 'L1'|'L2'|'L3'|'L4'  (NEVER 'L0')
origin_asset_id          text       not null
origin_id                text       not null     -- the single origin this adjustment attaches to
weight_id                text       not null     -- FK → mimamsa_multipliers (the source weight)
multiplier               numeric    not null     -- bounded final (after per-layer cap)
raw_multiplier           numeric    not null     -- pre-bound (audit)
applied_bound            numeric    not null     -- the CAP_layer used [P2]
evidence_n               int        not null
leakage_status           text       not null
applies_to_reading       boolean    not null     -- the TWO-KEY result (gate_passed AND confidence_high)
derived_from_pramana_ids jsonb      not null     -- the calibration verdicts behind it (dedup ledger)
overlay_formula_version  text       not null
created_at               timestamptz not null
PRIMARY KEY (chart_id, origin_id, weight_id)
```

### `mimamsa_load_bearing` (G3 — sensitivity map per conclusion)
```
chart_id                 uuid       not null
conclusion_id            text       not null     -- a prediction/anchor/window
signal_id                text       not null     -- a driving signal
sensitivity              numeric    not null     -- Δconfidence if this signal removed (load-bearing vs redundant)
role                     text       not null     -- 'load_bearing'|'supporting'|'redundant'
formula_version          text       not null
PRIMARY KEY (chart_id, conclusion_id, signal_id)
```

## §4 — Computation logic (deterministic)

### 4.1 — Overlay write (segregation; L1→L4 never L0)
- For each promoted/earning weight in `mi_gunanaka`, write ONE overlay row keyed to its **single origin**
  id, in the matching table. `origin_layer ∈ {L1,L2,L3,L4}` — **a write targeting L0 is a halt** (no-L0
  gate). The base table is never touched.
- `multiplier` = clamp(applied_multiplier, by `CAP_layer` — tight at L1, wider at L4 `[P2]`). The
  evidence-scaling already happened in `mi_gunanaka`; the cap is the final bound.
- `applies_to_reading` = the **two-key** result (gate_passed AND confidence_high). If false → the overlay
  row still exists (suggestion mode, auditable) but serve-time reads base.

### 4.2 — Single-origin attribution = the dedup solution (PROPAGATION §4)
- A calibration finding attaches to exactly ONE origin (the asset the evidence is about). Everything
  downstream inherits it by **reading the corrected origin** — NOT by a second overlay.
- **The dedup ledger:** before writing a downstream overlay (e.g. an anchor adjustment), check
  `derived_from_pramana_ids`: if the same evidence already adjusted an upstream origin that this node
  consumes, do NOT write a second overlay (the node inherits via read-side propagation). A downstream
  overlay is written ONLY for evidence genuinely about that node (e.g. a composition error, not a signal
  error).
- Net: one signal → one row → one overlay → applied once everywhere it's read. No asset duplicated; no
  correction double-counted.

### 4.3 — Effective value (read-side; serves via mi_seva)
- `effective_value = clamp(base_value × multiplier, base×(1−CAP), base×(1+CAP))`, computed at read time
  (or in a cached `effective` view refreshed per calibration session — P3). The base column is never
  overwritten; effective and base are separate. `mi_seva` chooses which to serve per the toggle.

### 4.4 — Load-bearing / sensitivity map (G3, deterministic)
- For each conclusion, recompute its confidence with each driving signal **removed** (the base computation
  is deterministic, so this is a cheap re-evaluation). `sensitivity` = the confidence delta. Classify
  load_bearing / supporting / redundant. This is pure combinatorial computation — the superhuman "which
  signals actually hold this up" map. **v1-active** (it needs only the structural base, not outcomes).

### 4.5 — No-LEL behavior
- Only prior-tier weights exist → overlays carry prior-tier multipliers with `applies_to_reading` per the
  two keys (which, with no empirical confidence, generally stays in suggestion mode unless a prior is
  itself high-confidence by config). The load-bearing map still computes (structural).

## §5 — Retrievability contract (feeds mi_darshana)
- The overlay + load-bearing map are retrievable: "for this conclusion, here's what's load-bearing vs
  redundant, and here's the (suggested/applied) adjustment with its evidence." The
  `derived_from_pramana_ids` chain feeds R4 (provenance). `applies_to_reading` + bound + n = R5 trust-metadata.

## §6 — Determinism & seal gates
- No LLM (D-1). Frozen `overlay_formula_version` (D-2); re-run identical (RL-1).
- **No-L0-touch gate:** assert no overlay row has `origin_layer='L0'` (or targets a `bg_*` id).
- **Double-count gate:** path test — a single calibration finding adjusts a dependent L4 prediction
  **exactly once** (no second overlay on the path).
- **OFF==baseline:** with the toggle off (mi_seva), serving base must equal pre-L5 byte-for-byte (the base
  is never mutated, so this is structurally guaranteed; test asserts it).
- **Bounds gate:** no effective value exceeds `base ± CAP_layer`.
- Degenerate-distribution guard on `origin_layer`, `role`, `applies_to_reading`.
- Registered with drift_detector + schema_validator (RL-5).

## §7 — Frozen-orchestrator conformance
`@register('mi_adhilepa')` `WriterBase`; per_chart; delete-then-insert on `(chart_id × origin_id × weight_id)`;
`conn=ctx.db_conn` never committed; `count_sql`: chart-scoped count across the 4 overlay tables (or a
unified view) `WHERE chart_id = $1`.

## §8 — `depends_on`
`['mi_gunanaka']` (+ reads L1–L4 base + `mi_pramana`). `[P2 reconcile]`.

## §9 — Matrix rows satisfied
overlay model + segregation (§D) ✅ · 4 overlay tables (§D) ✅ · single-origin dedup + ledger (§D) ✅ ·
bounded + evidence-scaled (§D) ✅ · L1→L4 never L0 (§D/no-L0 gate) ✅ · two-key apply (§D/V4) ✅ · G3
load-bearing/sensitivity (§A) ✅ · double-count + OFF==baseline + bounds gates (§G) ✅ · R4 provenance +
R5 trust source ✅ · determinism (§G) ✅.

*End 06_mi_adhilepa_SPEC v1.0.*
