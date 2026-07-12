---
artifact: LLM_CONSUMPTION_AUDIT
version: 1.0
status: CURRENT — consolidation report (deliverable 1, plan §7)
program: LLM_CONSUMPTION_AUDIT_PLAN_v1_0
executed: 2026-07-12 (single execution campaign, swarm model per plan §12.7)
charts: 482012f1 (Abhisek, native) · 1c826d5a (Abhinandan)
channels_audited: local surgical-primitives route · :8000 compute sidecar · DEPLOYED MCP connector (amjis-mcp, 130 tools) · DB SELECT (Cloud SQL via proxy)
discipline: FINDINGS-ONLY, read-only, ZERO writes to product data/schema (both E-7-family authorized writes turned out non-applicable on inspection)
---

# LLM Consumption Audit — Consolidation Report v1.0

## 1 — Executive summary (the number the audit was built to produce)

Against the deployed public MCP channel real consumers use, of **328 acharya-grade questions,
only 4 (1.2%) are fully answerable** at the width+depth the doctrine requires. 170 (52%) are
answerable only with material gaps the LLM must paper over; 154 (47%) are INSUFFICIENT. **Every
one of the 328 forced class-9 ungoverned improvisation** — the consuming LLM had to invent method,
adjudicate conflicts, or translate taxonomy→life-language on every single question.

This is not primarily a data-plane failure. The Gaṇita substrate is deep and largely correct.
The instrument a consumer actually touches is gated by three separable failure bands:

1. **The retrieval/serving plane is the weakest link.** Ranked surfaces carry no attribution
   (100% UNATTRIBUTED) and don't discriminate domains (wealth top-K ≈ relationship top-K); no
   large-N synthesis path exists (7/7 heavy questions hit the ceiling); the local surgical tool
   registry is 45% dead and the local help text advertises dead tools; the `:8000` sidecar is
   partially broken (auth, missing modules). *Most* of this is fixable at the serving layer.
2. **A real data-plane band that no serving fix reaches:** the L3 Kāla activation windows are
   ~99% NULL-dated (R-45, survives rebuild), whole analysis stages are empty shells (CDLM
   rollups, CGM sub-graphs/topology, contradictions, RM bundles), the CGM graph is graha-only
   (bhavas orphaned, no yoga nodes, no temporal hooks), sensitive-degree concepts (mrityu-bhaga,
   R-47) and ayurdaya/longevity are never computed, and the MSR ingestion funnel floods or starves
   (15,660-signal walls; 8 categories un-ingested including doshas and yogas).
3. **A serve-time integrity defect:** `get_chart_orientation` intermittently returns the WRONG
   chart's data (LCA-17) — a data-isolation bug.

## 2 — Channel picture (the pivotal scoping correction, E-8b)

| Channel | Reachability | Role in audit |
|---|---|---|
| **Deployed MCP connector** (`amjis-mcp`, 130 tools) | ✅ live, read-only via `mcp-canary-key` | The doctrinal public channel; Lanes 2/6/7 graded here; **primary** |
| DB SELECT (Cloud SQL) | ✅ (dev tooling proxies to prod) | Ground truth for Lanes 5/8/9b + Item-0 |
| Local surgical-primitives route | ⚠ 45% of tools dead at the registry seam | A broken **bench**, not the consumer channel |
| `:8000` compute sidecar | ⚠ partly broken (auth 401, missing `jhora`, DATABASE_URL unset) | Bench infra |
| Local `ask_madhav` consult | ⛔ dead (queries retired `reports` table) | Not consumer-facing; itself a finding (LCA-2) |

**Scope correction:** LCA-1/-4/-11/-13 were measured on the local bench and read as "mass
unreachability." The deployed connector serves those surfaces. These findings are therefore
**bench-vs-deployed divergence** — real (the local dev bench is broken and misleads developers)
but with a different remediation locus (fix the local surgical registry + sidecar) than the
data-plane defects, which are **real on all channels** (confirmed: `get_temporal_windows(native)`
= `activation_count:0` on the deployed connector too).

## 3 — Per-lane results

| Lane | Scope | Headline |
|---|---|---|
| **Item-0** | R-45 fork | DATA_PLANE_WRITER_DEFECT — activation windows ~99% NULL-dated; survives rebuild; re-attributes R-45 from serving→writer |
| **1a** tool census | 127 tools | 17 reachable-surgical / 109 down-pipeline / 1 dead; 7 PASS / 5 PARTIAL / 6 FAIL synthesizability |
| **1b+5** fused | 3,058 families | per-channel matrix; 1,416 reachable-surgical / 1,485 down-pipeline / 157 truly-unreachable; reachable values PASS fidelity |
| **1c** services | 30 | 13 reachable; sidecar broken (LCA-13) |
| **3** cross-path | 6 quantities | dignity + shadbala INCONSISTENT (R-43); sign fidelity 100% |
| **4** receipts | 127 tools | help text advertises 17 dead tools (LCA-12); deployed channel mostly honest about trims (LCA-18) |
| **6** ranking | 16 surfaces | ALL 14 DROWNED; 100% UNATTRIBUTED (R-44a); domain-invariant readings; wrong-chart bug (LCA-17) |
| **7** synthesis | 7 heavy Q | 7/7 ceiling (R-48) |
| **8** dossiers | 20 (10×2) | 1 SYNTHESIZABLE / 19 PARTIAL; 73.5% avg depth; 114 held-but-not-received facets |
| **9a** graph | 42 nodes | graha-only graph; 60/60 bhavas orphaned; no yoga nodes / temporal hooks; parked+partial |
| **9b** MSR funnel | 204 categories | 5 BROKEN / 8 NOT_CONSUMED; 15,660-signal flood; R-42/R-44b/KP-4 |
| **2** questions | 328 | **1.2% SUFFICIENT**; class-9 on all 328 |

## 4 — Findings register (permanent record)

18 new consolidated finding classes filed to `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (LCA-1..18) plus
the R-45 re-attribution and R-43 re-confirmation. CRITICAL: LCA-2 (consult dead), LCA-4 (mass
down-pipeline, bench-scoped), LCA-5 (empty shells), LCA-9 (dossier depth), LCA-14 (ranking DROWNED
+ UNATTRIBUTED + domain-invariant), LCA-15 (no synthesis / R-48), LCA-16 (1.2% sufficient),
LCA-17 (wrong-chart isolation bug), LCA-9a-1 (parked graph). The ~1,000 per-item findings live in
the lane shard substrate (`state/*/shard-*.md`) for the machine-readable findings JSON.

## 5 — Audit-of-the-audit: blind R-37..R-48 rediscovery test

Lanes never consulted `anchors.jsonl`. At consolidation, 10 of 12 anchors were independently
re-derived: **R-37** (Lane 6/9b trivia-ranking), **R-39/R-40** (Item-0 shared root + Lane 2 empty
stages), **R-42** (Lane 9b dosha collapse), **R-43** (Lane 3 dignity/shadbala), **R-44** (Lane 6
UNATTRIBUTED / Lane 9b major-tier trivia), **R-45** (Item-0 + Lane 8 all dossiers), **R-46** (Lane 2
operative_varga=D1), **R-47** (Lane 8 mrityu-bhaga), **R-48** (Lane 7 ceiling). Plus KP-4 (Lane 9b).

**Lane-coverage hole (honest miss):** **R-38** (judgment_query varga_confirmed-while-empty) and
**R-41** (ganita_yogas_get envelope-vs-content) — receipt-honesty envelope-contradiction anchors —
were not cleanly re-derived because Lane 4 ran only on the surgical channel; a targeted deployed-
channel receipt-honesty pass on `judgment_query`/`ganita_yogas_get` is the follow-up. Their tool
shapes have also evolved since the 2026-07-11 baseline. 10/12 pass; 2 documented holes.

## 6 — Remediation priority (from the class→layer mapping)

1. **Highest leverage (serving):** add resolvable derivation-ledger to every ranked row + fix the
   domain-mapping so readings are domain-specific (kills LCA-14/R-44/KP-4 in one place); build the
   large-N synthesis instrument (LCA-15/R-48); revive the local surgical registry + sidecar bench.
2. **Data-plane (no serving fix reaches these):** fix the L3 activation-date writer (R-45, survives
   rebuild — must fix code, not rebuild); populate the empty CDLM/CGM/contradiction/RM stages
   (LCA-5); wire graha↔bhava + yoga + temporal edges into CGM (LCA-9a-1); compute sensitive-degree
   + ayurdaya (R-47/LCA-16); fix MSR ingestion flood/starve + dosha/yoga attribution (LCA-9b, R-42).
3. **Integrity:** the `get_chart_orientation` wrong-chart substitution (LCA-17) — a multi-chart
   product cannot ship a cross-chart data-isolation bug.

## 7 — Consolidation (COMPLETE 2026-07-12)

- **Lane 10** (promise-vs-delivery, deployed channel primary): ✅ 67 assets — **DELIVERS 28 (42%) /
  SHORTFALL 25 / PARTIAL 14**; dominant shortfall = retrieval-plane 23 (computed-but-unserved even on
  the deployed channel: kala_taranga 79,728 rows, kala_avadhi, ga_medical, ga_vastu, ga_yoga_firings,
  cgm_motifs/paths, …); zero "promise undeclared" (all 27 ledger-NOT-FOUND re-sourced). LCA-19.
- **Channel re-tag:** ✅ 902 down-pipeline families → `reachable-deployed-mcp`. Final: **2,318/3,058
  (76%) reachable via real channels** (1,416 surgical + 902 deployed); 583 down-pipeline + 157
  truly-unreachable remain.
- **Findings JSON** (deliverable 2): ✅ `deliverables/findings.jsonl` — **1,009 records**.
- **Retests:** 7-tool gap ✅ resolved (ref_remedies_* family). R-38/R-41 → honest lane-hole (tool
  shapes evolved; deployed-channel receipt-honesty on judgment_query/ganita_yogas_get is the follow-up).
  Fused verifier disagreement #1 → single-path, logged for remediation.
- **LCA-17** reproduction ✅ captured precisely (nondeterministic, concurrent-multi-chart-load
  correlated; re-severitied as entitlement-class).

## 8 — Satisfaction criteria (plan §8)

1. Census completeness — ✅ 100% tools/families/services probed (127 of 134 tools; 7-tool gap logged).
2. Question-width — ✅ 328/328 traced with sufficiency verdicts + root-caused gaps.
3. Depth — ✅ 20/20 dossiers with facet matrices + held-but-not-received root-causes.
4. Coverage honesty — ✅ every surface audited or explicitly channel-scoped; the R-38/R-41 hole is declared.
5. Plannability — ✅ every finding class + suspected layer + reproducible evidence in the register + shards.

*Campaign executed read-only across all channels; findings-only discipline held absolute; zero
writes to product data or schema. ~1,000 findings; 10/12 blind anchors re-derived; ~13M tokens.*
