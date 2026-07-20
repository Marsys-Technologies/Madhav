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

## §F gate ruling — native, 2026-07-19/20 (supersedes/refines the interim response mid-turn)

**APPROVED — W2 may open.** RS-2 authority exercised to amend the coverage doctrine itself:

1. **Disposition taxonomy amendment (RS-2, supersedes `RETRIEVAL_STRATEGY_v1_0.md` §5.2's
   SERVED/INTERNAL-BY-DESIGN/RETIRED three-way and this campaign's DARK/NEEDS-OWNER working
   labels).** DARK is abolished as a terminal state. Every table resolves to exactly one of:
   - **SERVED-DIRECT** — a capability serves this table's concepts directly.
   - **SERVED-VIA** — concepts fully covered by a *named* other surface (per-concept cover
     recorded in the concept_ledger, CI-verified — not merely asserted).
   - **OPERATIONAL** — no astrological concept (bookkeeping/journal/export/cosign/embedding
     infrastructure); declared, not a coverage gap.
   - **GATED** — an astrological concept deliberately withheld, with a cited doctrine reason
     (A-19 NO-LEAKAGE / the L5 structural seal / D-14 register safety — no ad hoc reasons), a
     named served aggregate that stands in for it, and a written revisit condition.
   - **RETIRED** — dead/superseded, no live consumer.
   **Default bias is SERVE: the burden of proof is on withholding.** Codified as a W1 addendum
   amending `RETRIEVAL_STRATEGY_v1_0.md` §5.2 and the plan's §9.6 lifecycle states in place.
2. **Mechanical resolution of all 51 former-NEEDS-OWNER tables, in W2 (not W1):** enumerate each
   table's concepts, run the concept-coverage test against the reachability matrix plus a live
   MARSYS-direct probe, assign the state the evidence dictates. No NEEDS-OWNER remains as a
   terminal state. Only a table requiring a genuinely NEW gate reason not already grounded in
   doctrine (A-19/L5-seal/D-14) returns to the native.
3. **Pre-ruled under the new taxonomy:**
   - `mimamsa_fact_adjustment` + `mimamsa_signal_adjustment` = **GATED** (reason: L5 STRUCTURAL
     seal + NO-LEAKAGE; public face: `mimamsa_calibration_get`; revisit: calibration-loop
     maturity or a Samīkṣā drill requirement).
   - Embedding tables = **SERVED-VIA** (`vector_search`).
   - Bookkeeping/journal/export/cosign ledgers = **OPERATIONAL**.
   - Tables holding uncovered astrological concepts = **SERVE**, wired in W2's dark-set lane.
4. **Before W2 opens:** census re-scan as a **W1 addendum**, `platform-mcp/src/tools/` included
   in the scan surface this time, re-checking **all 77** former-dark verdicts (not only the CGM
   four) under the new taxonomy.
5. **D-5 coexistence:** §I.2 fallback confirmed — W2 absorbs the gochara tools in its migration.
   Breaking-release deploys (alias cutover, single-bootstrap cutover) **wait for D-5
   stabilization to go quiet**; when ready, take the deploy mutex and **re-snapshot the baseline
   first**. Any G-4-owned defect found incidentally during migration is **reported to the
   doctrine ledger, never fixed in-flight** by this campaign.
6. **Misc:** live DB is the authoritative fact-category enumeration (design-only per
   must_not_touch on `chart_facts` semantics — no consumer migrated yet); `chart_ayanamsha_reports`
   is stale naming in the plan's own prose — doc correction only, no table exists to wire;
   `ka_muhurta_seva` joins W2's dark-set wiring scope (same stub shape as `ka_graha_sancara`,
   GT-50 sibling); the dead `pyjhora_adapter` Docker build target (zero git history) is deleted.

Review-packet corrections are absorbed as W1 addenda; W2 opens once the addendum lands.

## Note on scope

This table records adoption for autonomy purposes only. OT-3/OT-4/OT-8/OT-11/OT-12/OT-1 from
`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §2 are **not** in the §9.5 queue this campaign owns —
they belong to the Paripraśna workstream (render/planner rebuild) and are out of `may_touch`.
Not adjudicated here; not silently dropped — noted so a future reader does not mistake their
absence for an oversight.
