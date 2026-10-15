# 035_DISCOVERY_LAYER — Instructions

Cross-domain discovery registers: patterns, resonances, clusters, contradictions (see `README.md`).

- `REGISTERS/INDEX.json` names the current version of each register; JSON is canonical, `.md` files are human-readable companions (JSON wins on disagreement).
- Registers are append-only: set `status: superseded` instead of deleting entries.
- Edit registers only deliberately in a doc-authoring session, never as a side-effect of pipeline or build work.
- Every register claim links back to L1 `fact_id`s via `LEDGER/`.
