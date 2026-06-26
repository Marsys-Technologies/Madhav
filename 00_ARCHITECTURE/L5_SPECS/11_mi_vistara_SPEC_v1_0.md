---
artifact: 11_mi_vistara_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_VISTARA
asset_id: mi_vistara
asset_kind: data
scope: global
activation: v1
version: 1.0
status: DRAFT — build-ready spec
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [export-integrity ledger]
---

# mi_vistara — Export-Integrity Ledger

> Sanskrit: *Vistāra* ("extension / spreading out"). The audit boundary of what LEAVES the instrument.
> Every export — PDF reading, JSON bundle, MCP payload — is logged with what it contained, when, to whom,
> and crucially **which contribution-state + calibration disclosures were attached**. The traceability
> guarantee for the instrument's outputs.

## §1 — Purpose & value
Closes the epistemic-hygiene loop: an instrument that learns + adjusts must be able to prove *what it
told whom, under what disclosure*. If a reading is later questioned, the ledger reconstructs exactly what
left, in what mode (learning on/off, which families, what confidence + n disclosed). Supports the
§3.5.G calibration-disclosure obligation at the export boundary.

## §2 — Inputs
| source | what |
|---|---|
| every export event (portal/MCP/PDF/JSON) | the payload + its metadata |
| `mi_seva` `contribution_state` | which channels were active + calibration_mode at export |
| `mi_darshana` insight ids | which insight units were included |

## §3 — Output schema (build-ready)

### Table: `mimamsa_export_log`
```
export_id                text       primary key
chart_id                 uuid       not null
exported_at              timestamptz not null
export_format            text       not null     -- 'pdf'|'json'|'mcp_bundle'|'portal_view'
recipient_ref            text                     -- who/where (user id / channel)
included_insight_ids     jsonb      not null      -- which mi_darshana units left
contribution_state       jsonb      not null      -- channels on/off + how resolved (from mi_seva)
calibration_mode         text       not null      -- 'empirical'|'prior_only'|'structural_prior_only'
disclosures_attached     jsonb      not null      -- the n / confidence / leakage disclosures that accompanied it (§3.5.G)
payload_hash             text       not null      -- integrity hash of what left
lel_version              text       not null       -- freshness at export
export_formula_version   text       not null
```

## §4 — Computation logic (deterministic)
- One row per export event; deterministic capture (no LLM). `payload_hash` makes the export tamper-evident.
- `disclosures_attached` records that the calibration honesty (n, confidence, empirical-vs-prior) actually
  accompanied the output — so honesty is auditable at the boundary, not just internally.

## §5 — No-LEL behavior
- Exports still logged; `calibration_mode='structural_prior_only'` recorded so it's clear the export
  carried no empirical calibration claim.

## §6 — Determinism & seal gates
- No LLM (D-1). Frozen `export_formula_version` (D-2). `payload_hash` integrity.
- **Disclosure-present gate:** an export with `calibration_mode='empirical'` must carry
  `disclosures_attached` (no empirical claim leaves without its n/confidence disclosure — §3.5.G).
- Degenerate-distribution guard on `export_format`, `calibration_mode`.
- Registered with drift_detector + schema_validator (RL-5).

## §7 — Frozen-orchestrator conformance
`@register('mi_vistara')` `WriterBase`; global (append-only audit log); `conn=ctx.db_conn` never committed;
`count_sql`: `SELECT count(*) FROM mimamsa_export_log`. Append-only — idempotency by `export_id`.

## §8 — `depends_on`
`[]` (operational ledger; reads `mi_seva`/`mi_darshana` at export time). `[P2 reconcile]`.

## §9 — Matrix rows satisfied
export-integrity ledger ✅ · §3.5.G calibration-disclosure-at-boundary ✅ · no-LEL labeling ✅ ·
determinism + disclosure-present gate (§G) ✅.

*End 11_mi_vistara_SPEC v1.0.*
