---
artifact: DRAFT_CLAUDECODE_BRIEF_L4_PH_SANKRAMA_v0_1.md
canonical_id: DRAFT_CLAUDECODE_BRIEF_L4_PH_SANKRAMA
brief_for: ph_sankrama (NEW) — Cross-domain spillover prediction [transmission]
status: SUPERSEDED (2026-06-22) by CLAUDECODE_BRIEF_L4_PH_SANKRAMA_v1_0.md (FINALIZED; lag-formula RETIRED per D44). Retained-in-place for audit trail only — do NOT build from this draft.
version: 0.1
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D8 §2.3)
swarm_coordination:
  wave: P3 (after ph_nimitta spine + P2)
  blocked_by: [ph_nimitta]
  blocks: [ph_phaladesa]
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py
    - platform/python-sidecar/services/ph_sankrama/**
    - platform/supabase/migrations/336_phala_sankrama.sql   # [RECON — number after global max]
    - platform/scripts/seed/asset_registry_seed.ts          # REGISTER new asset
---

# DRAFT BRIEF — ph_sankrama (Cross-Domain Spillover Prediction) — NEW

> **Saṅkrama** — "transmission / crossing-over." Predicts how a window in one life-domain LOADS onto
> another, time-lagged, along the chart's measured cross-domain linkages.

## §0 — What this asset IS
The supreme move an acharya cannot hold: a **second-order, time-lagged, cross-domain prediction.**
For each primary `ph_nimitta` anchor in domain A, project a spillover prediction into domain B using
the chart's measured `bodha_cdlm_cells` linkage strength + **asymmetry** (career→health flows but not
the reverse), with a lag derived deterministically from the linkage. E.g. "this 2027 career-stress
window will, given your measured career→health asymmetry of 0.7, load onto health 3–6 months later."

## §1 — Why it matters
Requires holding the whole cross-domain linkage matrix at once — the chains across domains that an
acharya gestures at ("career stress affects health") but cannot quantify or time. The CDLM already
computed the linkage + asymmetry; this asset turns it into time-lagged predictions.

## §2 — VERIFIED ground truth
- `bodha_cdlm_cells` (sealed L2) holds: `domain_row`, `domain_col`, `net_linkage_strength`,
  `computed_linkage_strength`, `asymmetric_linkage_flag`, `asymmetry_score`,
  `shared_signal_ids_array`, `contradicting_signal_pairs_*`. These are the linkage edges.
- `ph_nimitta` (P1) produces the primary anchors. These are the spillover sources.
- `[RECON Q4]` confirms cdlm_cells row count for the native.

## §3 — Schema (migration 336 `[RECON]`)
`phala_sankrama`:
```
sankrama_id           uuid PK
chart_id              uuid NOT NULL
source_anchor_id      uuid REFERENCES phala_anchors        -- the primary window
cdlm_cell_id          uuid REFERENCES bodha_cdlm_cells     -- the linkage edge (anti-drift FK)
source_domain         text NOT NULL
target_domain         text NOT NULL
linkage_strength      double precision
asymmetry_score       double precision
direction_of_flow     text CHECK (direction_of_flow IN ('source_to_target','mutual'))
source_window_start   date
source_window_end     date
projected_lag_days_min integer                              -- deterministic lag model
projected_lag_days_max integer
projected_window_start date
projected_window_end   date
spillover_confidence   double precision CHECK (<=0.80)      -- discounted from source × linkage
falsifier             text NOT NULL
confidence_basis      text NOT NULL DEFAULT 'structural_not_yet_empirical'
derivation_ledger_jsonb jsonb NOT NULL
source_citation       text NOT NULL
computed_at           timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, source_anchor_id, target_domain)
```

## §4 — Engine spec (`services/ph_sankrama/engine.py`)
1. For each `phala_anchors` row, find `bodha_cdlm_cells` where its domain is `domain_row` and the
   linkage is non-trivial (above a documented threshold).
2. Lag model (deterministic, documented): `lag = f(linkage_strength, asymmetry_score)` — stronger,
   more asymmetric linkage → shorter, more confident lag. Propose the exact lag curve `[NATIVE-RATIFY
   if it's a judgment]`; default to a documented monotone mapping.
3. Spillover confidence = source anchor confidence × linkage_strength × asymmetry-directionality
   factor, capped 0.80, labeled structural.
4. Emit one spillover per (source anchor × qualifying target domain). Falsifier = "no observable
   change in [target_domain] within [projected_window]."
5. Anti-drift: cite the `source_anchor_id` + `cdlm_cell_id`; write ONLY `phala_sankrama`.

## §5 — Acceptance criteria
1. `[pytest]` every spillover references a real `phala_anchors.source_anchor_id` + a real `bodha_cdlm_cells.cdlm_cell_id`.
2. `[pytest]` asymmetric cells produce one-directional spillover (source→target only when asymmetry warrants); mutual cells produce both.
3. `[pytest]` the lag model is deterministic + documented; projected_window derived from source_window + lag.
4. `[pytest]` spillover_confidence ≤ source confidence (discount); labeled structural.
5. `[anti-drift]` writes only phala_sankrama; zero `.commit()/.rollback()`.
6. `[psql_prod + curl_prod]` lit; cockpit shows ph_sankrama; idempotent; FORENSIC 7/7.

## §6 — Asset registration (NEW)
Add `ph_sankrama` / `Saṅkrama` / `Cross-domain spillover` / `phala_sankrama` / depends_on
`['ph_nimitta']` (+ reads `bodha_cdlm_cells`) / `$1` count_sql / `asset_kind='artifact'` /
delete-then-insert / `target_floor: null`. Serialize seed edit (CS1).

## §7 — VALUE ADDED
The only asset that predicts the chart's *internal contagion* — how one domain's window propagates to
another, on a measured lag. A genuinely second-order prediction surface no acharya produces.

---
*End of DRAFT ph_sankrama v0.1.*
