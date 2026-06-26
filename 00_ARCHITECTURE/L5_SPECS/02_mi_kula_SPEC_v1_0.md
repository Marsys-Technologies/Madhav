---
artifact: 02_mi_kula_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_KULA
asset_id: mi_kula
asset_kind: data
scope: global
activation: v1
version: 1.0
status: DRAFT — build-ready spec (reconcile [P2] items against ground-truth audit + native number-ratification)
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [§A G6 family-interaction, §F external-family catalog, §F negative-control battery defs, §C manifestation classical source, §G D-3 pinned external data, §E family defs]
---

# mi_kula — Signal-Family Registry & Negative-Control Battery

> Sanskrit: *Kula* ("family / lineage"). The governing registry of **what is allowed to influence a
> reading at all** — every classical and external signal-family, tier-tagged, citation-backed,
> independently controllable — plus the **negative-control battery** that lets the instrument prove it
> isn't fooling itself. This is the controllable matrix; it governs admission, not scoring.

## §1 — Purpose & value
- Defines the universe of **signal-families** (sources of hunches): classical Jyotish families + the
  curated external-knowledge families (astrophysics/chronobiology/etc.) + the negative-control traps.
- Each family is **tier-tagged** (evidence strength), **soundness-tagged** (scientific/astrological/both),
  **citation-backed**, **independently switchable**, and carries its **prior weight** + **calibration
  status**.
- Hosts the **negative-control battery** (known-false signals that MUST score null — the lie-detector).
- Computes **family-interaction value** (G6): does a family add predictive power *on top of* others, or is
  it redundant?

**Value:** this is the single point of governance over influence. "More signals" never means "less
control," because everything that could ever touch a reading is enumerated, tiered, and switchable here.

## §2 — Inputs
| source | what |
|---|---|
| `bg_rules`, house/karaka significations, `brahma_yoga_catalog`, `bg_texts` (L0) | the classical family definitions + citations |
| the ELEVATION external-knowledge catalog (X-PHOTO, X-SOLARYR, X-GEOMAG, X-SEASON, X-LUNAR…) | external families + their real citations + binding kind |
| the negative-control catalog (NC-BIORHYTHM, NC-FLIESS, NC-CARLSON, NC-CFEPP, NC-TWINS, NC-SUNSIGN, NC-BODYTIDE…) | the trap definitions |
| pinned external-data snapshots (geomag Kp/Ap, sunspot number, ephemeris) | dated, frozen (D-3) |
| `mi_pramana` (feedback) | per-family calibration status updates (prior→earning→promoted→suspended) |

## §3 — Output schema (build-ready)

### Table: `mimamsa_signal_families`  (global catalog)
```
family_id               text        primary key   -- e.g. 'X-GEOMAG','T-NAKPADA','NC-BIORHYTHM','C-SAT-AFFLICT'
display_name            text        not null
layman_name             text        not null       -- plain-language ("cite my life events"-style)
family_class            text        not null       -- 'classical' | 'external_science' | 'tradition' | 'negative_control'
evidence_tier           text        not null       -- 'TIER1_SCIENCE'|'TIER2_PLAUSIBLE'|'TRADITION'|'NEGATIVE_CONTROL'|'CLASSICAL_CITED'
soundness_basis         text        not null       -- 'scientific'|'astrological'|'both'
binding_kind            text        not null       -- 'natal'|'event_date'|'lifetime_index'|'meta'
default_state           text        not null       -- 'ON'|'OFF'|'CONTROL_ONLY'
prior_weight            numeric     not null       -- classical/scientific prior (pre-calibration) [P2 numbers]
calibration_status      text        not null       -- 'prior_only'|'earning'|'promoted'|'suspended'
citation_refs           jsonb       not null       -- real sources; classical → bg_texts ids; science → DOI/author/journal/year
binding_spec            jsonb       not null       -- how it binds to chart/time (deterministic recipe)
data_source_pin         jsonb                      -- for external: the pinned snapshot id/version (D-3)
apply_point             text                       -- which overlay surface it can modulate (→ mi_adhilepa)
interaction_value       numeric                    -- G6: incremental predictive value over other families [computed]
interaction_status      text                       -- 'redundant'|'additive'|'untested'
is_active               boolean     not null
formula_version         text        not null       -- versioned (D-2)
created_at              timestamptz not null
updated_at              timestamptz not null
```

### Table: `mimamsa_negative_controls`  (the lie-detector battery)
```
control_id              text        primary key    -- 'NC-BIORHYTHM' ...
known_false_basis       text        not null        -- why it's known-false (debunked/physically-negligible)
citation_refs           jsonb       not null        -- the debunking source (Rotton&Kelly 1985, Carlson 1985, …)
binding_spec            jsonb       not null         -- how it's computed from chart/date (so it CAN be scored)
expected_score          text        not null        -- 'null' (must score ~zero)
tolerance               numeric     not null         -- the null-band; exceeding it = harness failure [P2]
last_harness_score      numeric                      -- filled by mi_pariksha harness
last_harness_status     text                          -- 'pass'|'FAIL' (FAIL blocks seal)
formula_version         text        not null
```

## §4 — Computation logic (deterministic)

### 4.1 — Family registration (seeded, citation-gated)
- Classical families: derived deterministically from `bg_rules` + significations; `citation_refs` resolve
  to `bg_texts` ids. (No family without a citation.)
- External families: registered from the ELEVATION catalog with real DOIs; `binding_spec` is the exact
  deterministic recipe (e.g. X-GEOMAG → "Ap index on event_date ±1–3d from the pinned snapshot").
- **Citation-gate:** a family with no resolvable citation cannot be `is_active=true` (it may exist as
  `prior_only`/inactive for review). This mirrors the manifestation-set citation rule.

### 4.2 — Negative-control definitions
- Each NC has a `binding_spec` so it IS computable from the chart/date (it must be scorable to be a valid
  trap), an `expected_score='null'`, and a `tolerance`. The harness lives in `mi_pariksha`; this asset
  owns the definitions + the latest result + the blocking semantics.

### 4.3 — Family-interaction value (G6) — activation-tiered
- **v1 (structural):** `interaction_status='untested'` for all (no outcome data yet).
- **As evidence grows (tiered):** compute, per family, the **incremental predictive value** over the set
  of already-promoted families (does it explain calibration variance the others miss?). Deterministic:
  compare held-out calibration error with vs without the family. Sets `interaction_value` +
  `redundant/additive`. This sharpens promotion (a redundant family doesn't earn separate weight) and the
  negative-control logic (a "useful" family that's actually redundant with a confound is flagged).

### 4.4 — Pinned external data (D-3)
- Geomag/sunspot/ephemeris series are stored as **dated, frozen snapshots**; `data_source_pin` records the
  exact version used. A re-run uses the same snapshot → deterministic. Refresh is an explicit, versioned event.

### 4.5 — No-LEL behavior
- All families remain at `prior_only`; the registry is fully populated and controllable; negative controls
  are defined but the harness reports `untested` until evidence exists. Families still contribute at prior
  weight through the overlay (governed by `mi_seva` toggles).

## §5 — Retrievability contract (feeds mi_darshana)
- Emits the **family catalog as retrievable units**: each family's tier, soundness, status, prior weight,
  citations, and (when computed) interaction value. The LLM can pull "which families are active and trusted
  for this native, and which are ruled out."
- **Negative knowledge (R6):** the negative-control results + any `suspended` families are the core of the
  retrievable "what's been ruled OUT for this native" surface — sourced here, served by `mi_darshana`.

## §6 — Determinism & seal gates
- No LLM in registration/scoring (D-1). External LLM may *propose* a candidate family, but it cannot be
  `is_active` without a citation (citation-gate) — same discipline as manifestation additions.
- Frozen `formula_version` + pinned data (D-2/D-3); re-run identical (RL-1).
- **Negative-control blocking gate:** if any `mimamsa_negative_controls.last_harness_status='FAIL'`, L5
  cannot seal and no weight may promote (E3). This asset holds the flag the seal reads.
- Degenerate-distribution guard on `evidence_tier`, `family_class`, `calibration_status`.
- Registered with drift_detector + schema_validator (RL-5).

## §7 — Frozen-orchestrator conformance
`@register('mi_kula')` `WriterBase`; `run(ctx)`; global scope; `count_sql`:
`SELECT count(*) FROM mimamsa_signal_families`. Idempotency: families are a global catalog → upsert /
delete-then-insert at global scope (not per-chart). Service dir COPY'd if a new top-level dir is added.

## §8 — `depends_on`
`['bg_rules']` (classical family definitions + citations). External families + NCs are seed/config data.
`[P2 reconcile]`.

## §9 — Matrix rows satisfied
external-family catalog (§F) ✅ · negative-control battery defs + blocking flag (§F/E3) ✅ · soundness/tier
tagging + per-family controls source (§E) ✅ · classical source for manifestation_set (§C) ✅ · G6
family-interaction (§A) ✅ · D-3 pinned external data (§G) ✅ · R6 negative-knowledge source (§B) ✅ ·
determinism/citation-gate/degenerate guard (§G) ✅.

*End 02_mi_kula_SPEC v1.0.*
