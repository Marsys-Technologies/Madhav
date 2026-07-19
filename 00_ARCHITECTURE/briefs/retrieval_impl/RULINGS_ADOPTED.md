---
artifact: RULINGS_ADOPTED.md
canonical_id: RETRIEVAL_IMPL_RULINGS_ADOPTED
version: 1.0
status: LIVE
type: campaign ruling ledger (§C delegated rulings, adopted at W0)
---

# §C Delegated Rulings — Adopted at W0

Per master brief §C: the standing §9.5 ruling queue is resolved by adopting the
recommendations already recorded in the plan/consult/strategy docs, to preserve full autonomy.
Native may override any of these at the §F gate.

| ID | Ruling adopted | Source pointer |
|---|---|---|
| OT-7 | One registry, many generated projections (best-surface-per-channel reading) | `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` §2.1, §R-1; `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` D-08/OT-7 |
| OT-10 | (b)+(c) — connect-time profiles (MCP-consult / MCP-expert), enforced by OAuth scope | plan §R-4.2; `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` OT-10 lean |
| OT-2 | Job-handle-FIRST with progress notifications layered | plan §9.7 analysis; `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` OT-2 lean "(b) with (c) as fallback" |
| OT-5 | Keep self-issued OAuth (a) for this campaign; run a ≤1-day Firebase-OIDC spike, record findings for a future ruling, do not block | plan §9.5; `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` OT-5 |
| OT-6 | No journaling this campaign; pin/provenance-stamp only (D-05 safe because `prashna_ask` ships in this campaign's arc) | plan §9.5; `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` OT-6, contingent on A-07 (`prashna_ask`) shipping |
| RC-1 | ≤20 umbrellas for non-Claude families; Claude-family compact 25–35 + tool-search metadata | `RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md` §3.1 |
| RC-2 | ChatGPT search/fetch connector projection = DEFERRED (recorded, not built) | `RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md` §3.2 |
| RC-3 | DeepSeek = consult-profile only | `RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md` §3.3 |
| RS-1 | Layering ruling approved: data stays layered, access is flat, navigation is guided | `RETRIEVAL_STRATEGY_v1_0.md` §5.1 |
| RS-2 | Coverage doctrine + dark-table disposition authority approved | `RETRIEVAL_STRATEGY_v1_0.md` §5.2 |
| RS-3 | Efficiency targets (≤10-call deepdive, ≤3-to-verdict, ≤2000-token orientation) approved as gate criteria | `RETRIEVAL_STRATEGY_v1_0.md` §7 |
| RS-4 | Already RULED + executed 2026-07-19 (CLAUDE.md v6.4, PROJECT_ARCHITECTURE v2.2 amended) — proportionality carve-out | `RETRIEVAL_STRATEGY_v1_0.md` §3.6 |
| C-1..C-6, F-R1, F-R7, AMBIG-1..4 | Already RULED by native 2026-07-19 (plan §9.2/§9.3) — implemented as written, not re-adjudicated here | plan §9.2/§9.3 |

## Note on scope

This table records adoption for autonomy purposes only. OT-3/OT-4/OT-8/OT-11/OT-12/OT-1 from
`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §2 are **not** in the §9.5 queue this campaign owns —
they belong to the Paripraśna workstream (render/planner rebuild) and are out of `may_touch`.
Not adjudicated here; not silently dropped — noted so a future reader does not mistake their
absence for an oversight.
