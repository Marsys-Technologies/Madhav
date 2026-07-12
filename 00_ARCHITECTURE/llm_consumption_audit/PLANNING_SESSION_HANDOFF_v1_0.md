---
artifact: PLANNING_SESSION_HANDOFF_v1_0
type: PHASE_HANDOFF (audit → remediation planning; plan §10 step 2)
version: 1.0
status: READY
authored_by: Fable 5 (Cowork) + native, 2026-07-12
consumes_from: LLM-CONSUMPTION-AUDIT-EXECUTION-2026-07-12 (SESSION_LOG, formally closed)
---

# Handoff: Remediation-Planning Session (Fable 5 + native, Cowork)

## Mission
Design the full implementation plan from the audit findings — architecture changes,
tweaks, and everything between — cutting across data plane, layer writers, retrieval/
serving, MCP contract, and new supporting layers. End objective (native, verbatim
intent): the consuming LLM has completeness of information in width and depth, and can
handle narrow and broad questions generating small to huge input volumes for synthesis.

## Inputs (read in this order)
1. `00_ARCHITECTURE/llm_consumption_audit/LLM_CONSUMPTION_AUDIT_v1_0.md` — consolidation report.
2. `deliverables/findings.jsonl` — 1,009 findings (28 CRIT / 622 HIGH), machine-readable.
3. `state/CONCEPT_RETRIEVABILITY_MATRIX.jsonl` — 3,058 families, per-channel (post re-tag).
4. `state/LANE9.md` — L1→MSR ingestion matrix + graph-leverage report.
5. Lane 10 promise×delivery ledger; Lane 2 evidence-plan corpus (P-12 requirements);
   Lane 7 synthesis-ceiling requirements spec (P-11).
6. `00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md` §9 — the 13 planning-phase
   capabilities P-1..P-13 (vidhi, adjudication doctrine, adversarial retrieval, normative
   bands, longitudinal loop, fragility propagation, gochara composition, narration
   vocabulary, intent decomposition, large-N synthesis, demand-side planner+capability
   map+tracker, services) — design work the audit deliberately did NOT do.
7. `GATE_RATIFICATION_v1_0.md` — rulings that bind remediation framing (esp. E-7c, E-8).

## Baseline (the numbers remediation must move)
- 1.2% of 328 acharya questions fully SUFFICIENT (4/328); class-9 improvisation on all 328.
- 42% of assets deliver their promise (28/67); 23 computed-but-unserved.
- 76% of value families reachable via real channels.

## The three bands (pre-clustered)
1. **Integrity (queue-jumper):** LCA-17 — get_chart_orientation cross-chart data leakage
   under concurrent multi-chart load. Entitlement-class. Fix + regression test first.
2. **Serving plane (bulk of the win):** ranked-surface attribution/discrimination
   (100% UNATTRIBUTED, DROWNED walls), 23 computed-but-unserved assets, receipt honesty,
   budget/trim discipline, large-N synthesis absence (7/7 ceiling), local-bench registry
   divergence (LCA-1/-4/-11/-13 re-scoped), dead-tool registry, LCA-3-EXT subject cap +
   single-ayanamsha serving.
3. **Data plane (survives rebuild — writers first, rebuild once, as verification):**
   R-45 NULL activation dates (L3 writer); LCA-5 empty shells (contradictions, CDLM
   rollups, CGM topology, RM tables, phala narration); LCA-6 motif-stage silent zero on
   native chart; LCA-9a-1 graha-only graph (60/60 bhavas orphaned, no yogas/temporal);
   LCA-9b MSR flood/starve (15,660-signal wall; dosha_label/yoga_label never ingested);
   R-47 mrityu-bhaga/ayurdaya/sensitive-degrees never computed.

## Sequencing thesis (validated by audit, to be ratified in planning)
LCA-17 → serving-plane wave → writer wave → ONE Abhinandan rebuild (verification event,
also clears stale state) → re-audit: re-run the 328-question matrix + Lane-8 dossiers +
promise grading against the baseline numbers above.

## Standing assets (reuse, don't rebuild)
Concept×Retrievability matrix = P-12 capability-map seed. 328-question matrix = the new
acceptance surface (supersedes the 38-item battery's role). Blind-anchor method +
verification-swarm/E-6 depth-gate discipline = template for all future verification.

## Open residuals inherited
R-38/R-41 deployed-channel receipt-honesty retest (lane hole, honestly logged);
7-tool census gap noted at consolidation; verifier disagreement #1 retest disposition.

*Start the planning session by proposing the Cowork thread name, then cluster
findings.jsonl by (band × suspected_layer × root-cause) and present the wave structure
for native debate.*
