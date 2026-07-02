---
canonical_id: REQUEST_RETRIEVAL_MSR_REBUILD_FOR_MCP_G10
version: 1.0
status: OPEN REQUEST — from the MCP-elevation workstream TO the retrieval / L2 Bodha fork
created: 2026-07-01
author: Cowork (MCP-elevation workstream) — for native Abhisek Mohanty
classification: cross-fork request (MCP → retrieval), honoring the frozen §4 seam
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4 (retrieval owns the data; MCP consumes)
relates_to: ISSUE-4 / DEFECT-001 (MSR computed-value drift), MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0
gates: MCP goal clause G10 ("superlative grounded insight") — cannot be witnessed until this lands
---

# REQUEST TO THE RETRIEVAL / L2 BODHA FORK — MSR REBUILD (gates MCP G10)

> Filed per the §4 direction-of-dependency rule: the MCP channel does NOT reimplement retrieval or touch L2
> data. This is a request, with evidence, for the data-owning fork to act. The MCP side is otherwise done.

## §1 — The ask (one sentence)
Rebuild the L2 Bodha MSR signals against the CURRENT L1 Gaṇita epoch so `bodha_msr_signals` is populated and
`constituent_facts_array` resolves to live `chart_facts.fact_id`, on the charts served through the MCP
(at minimum the 4 entitled: Abhinandan `1c826d5a`, Abhisek `482012f1`, Arunima `acdf0d66`, Kiran `cb73cd3d`).

## §2 — Evidence (from the live MCP connector probe, 2026-07-01)
A real external LLM client (Claude Code) connected to prod `amjis-mcp` and called the insight tools:
- `get_chart_orientation` (chart 482012f1 AND 1c826d5a) → `is_error:false` but EMPTY: `digest:{}`,
  `top_signals:[]`, `convergence_domains:[]`.
- `get_signals` → `returned_count:0`, and the tool's OWN provenance block self-reports:
  > `DEFECT-001 OPEN: constituent_facts_array has 91.5% orphan rate ... bodha_msr_signals: 0 rows currently ...
  > this is expected until L2 rebuild.`
The MCP channel is working correctly — it faithfully returns what the data layer holds (nothing). The gap is
the data, not the channel.

## §3 — Why this is the retrieval fork's, not the MCP's
- Per §4: retrieval is FROZEN + chart-agnostic + owns the chart data + SQL; the MCP is a thin adapter that
  consumes registry capabilities. The MCP MUST NOT run its own chart SQL or repopulate L2.
- This is the pre-existing MSR-vs-L1-epoch drift documented in `MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0`
  (MSR built against a prior L1 epoch; L1 later rebuilt; cited fact_ids no longer resolve). The §N.5 detector
  reporting 91.5% orphan is the instrument working as designed.

## §4 — Definition of done (how the MCP side will witness the fix)
Once the rebuild lands, the MCP re-runs the live connector probe (no MCP code change needed):
- `get_signals` (482012f1) returns NON-empty signals ranked by computed_salience.
- `get_domain_reading` (482012f1, domain=relationship/career) returns active signals whose
  `constituent_facts_array` RESOLVE to real `chart_facts` rows (orphan rate well below the current 91.5% —
  target the handoff's ≥80% resolution).
- The MCP's env-gated `RUN_G10` integration test (in `platform-mcp/src/__tests__/m8_e2e_proof.test.ts`, written
  in PR #372 as the living proof-of-fix) is switched on and PASSES.
That is the moment MCP goal clause G10 ("superlative grounded insight, fact-cited") is witnessed end-to-end.

## §5 — What the MCP side has already done (so the fork knows the channel is ready)
- Channel proven live: connect, 45 tools, `list_my_charts` by name, entitlement gate, real deterministic data.
- PR #372 (M8.1) fixes the two MCP-side insight-surface defects (L0/L1 runtime registration for
  get_positions/get_dashas/get_classical_citation; holistic_bundle bundle-routing). After it deploys, G9 is lit.
- The ONLY remaining blocker to the full goal is this MSR rebuild. The MCP will consume the rebuilt data with
  zero further channel changes.

## §6 — Not in scope for this request
- No MCP code change is requested or needed. No change to the frozen §4 seam. No entitlement/auth change.
- Scheduling + method of the MSR rebuild are the retrieval / L2 Bodha fork's call (this request states the
  need + the acceptance witness, not the how).

*End of REQUEST_RETRIEVAL_MSR_REBUILD_FOR_MCP_G10 v1.0 — the last external blocker to witnessing the MCP goal.*
