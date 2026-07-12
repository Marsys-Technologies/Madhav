---
artifact: REMEDIATION_PLAN_v1_0
type: REMEDIATION_MASTER_PLAN (plan §10 step 2 output — the Fable 5 planning session deliverable)
version: 1.0
status: SUPERSEDED by REMEDIATION_PLAN_v2_0.md (2026-07-12 second pass — retained in place per archival policy)
authored_by: Fable 5 (Cowork) + native, session LLM-CONSUMPTION-REMEDIATION-PLANNING-2026-07-12
consumes_from: PLANNING_SESSION_HANDOFF_v1_0.md (READY) · LLM_CONSUMPTION_AUDIT_v1_0.md ·
  deliverables/findings.jsonl (1,009) · GATE_RATIFICATION_v1_0.md (E-4/E-7c/E-8 bind) ·
  briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md §9 (P-1..P-13)
chart_ids: 482012f1 (Abhisek, native) · 1c826d5a (Abhinandan, verification chart)
native_rulings_incorporated:
  - "Repo unified: audit corpus merged to main (PR #551); planning artifacts land on main."
  - "P-capability split: P-10/P-11/P-12 design inside Wave 1; P-1..P-9/P-13 doctrine layers deferred to a post-re-audit campaign."
  - "Local bench (192 findings) in scope as a parallel low-risk Wave-1 lane."
changelog:
  - v1.0 (2026-07-12): initial draft from the ratified cluster analysis + wave structure.
---

# LLM Consumption Remediation — Master Plan v1.0

## §1 — Mission (native intent, verbatim from handoff)

The consuming LLM has completeness of information in width and depth, and can handle
narrow and broad questions generating small to huge input volumes for synthesis.

## §2 — Baseline the program must move (frozen 2026-07-12)

| Metric | Baseline | Instrument |
|---|---|---|
| Acharya questions fully SUFFICIENT | 4/328 (1.2%) | Lane-2 question matrix (the new acceptance surface; supersedes the 38-item battery's role) |
| Class-9 improvisation | 328/328 | Class-9 logs |
| Asset promise delivery | 28/67 (42%) | Lane-10 promise×delivery ledger |
| Value families reachable via real channels | 2,318/3,058 (76%) | Concept×Retrievability matrix (per-channel, E-8 schema) |
| Heavy-question synthesis | 0/7 (7/7 ceiling) | Lane-7 spec |
| Dossier depth | 73.5% avg; 1/20 SYNTHESIZABLE | Lane-8 facet matrices |

## §3 — Finding-cluster map (the plannable decomposition of 1,009 findings)

Clustering rule (reproducible from `deliverables/findings.jsonl`): band by
(failure_class × channel × lane × summary-keywords), as executed in the planning session.
Totals: **Band 1 Integrity = 9 (1 CRIT) · Band 2 Serving = 643 (27 CRIT) ·
Band 3 Data plane = 222 (2 CRIT) · Band 4 Doctrine/class-9 = 135 (0 CRIT).**

| Cluster | n | CRIT | Root cause | Type specimens |
|---|---|---|---|---|
| Integrity: wrong-chart substitution | 9 | 1 | get_chart_orientation cross-chart leakage under concurrent multi-chart load (LCA-17, entitlement-class) | F-0893 |
| Serving: unserved/unreachable (c1) | 193 | 6 | 23 computed-but-unserved assets; parameter-ignoring tools (dasha window/system_id; lel_query serves 0/57 events) | F-0354, F-0471, F-L10-021 |
| Serving: ranking/salience (c7) | 81 | 6 | 100% UNATTRIBUTED; domain-invariant top-K (wealth≈relationship 19/20); DROWNED walls | F-0903, F-0909 |
| Serving: synthesis ceiling (c8) | 52 | 7 | No staged retrieval/map-reduce; flat top-K over 13,364 signals; missing domains (education, moksha) | F-0949, F-0961, F-0974 |
| Serving: hollow stage payloads (c4/c0 deployed) | 53 | 7 | Stages return [] or the wrong analysis; some are downstream symptoms of Band-3 (attribute per-item at brief time) | F-0416, F-0421, F-0536 |
| Serving: form/budget + receipts (c5/c6) | 127 | 0 | Trim dishonesty (truncated:false at 200/7,014, null cursor); un-budgeted dumps; IDs-without-text | F-0963 |
| Serving: prod consult dead | (in c1/c4 counts) | 1 | LCA-2 (E-7c upgraded CRITICAL): live consult path queries retired `reports` relation — no chart servable via the product's own chat surface | GATE E-7c |
| Serving: local bench divergence | 192 | 1 | Dead surgical registry seam (45% tools dead) + broken :8000 sidecar (auth, jhora, DATABASE_URL); LCA-1/-4/-11/-13 re-scoped | Lane 1a/1c |
| Data: layer-writer empty shells | 104 | 0 | CDLM rollups/gradients/clusters, CGM topology, contradictions, RM tables, phala narration = 0 rows; cgm_motifs zero on native chart only (LCA-5/-6) | F-0112..F-0121 |
| Data: CGM graph poverty | 63 | 0 | Graha-only graph; 60/60 bhavas orphaned; no yoga nodes; no temporal hooks (LCA-9a-1) | Lane 9a |
| Data: MSR funnel | 40 | 1 | 15,660-signal single-category flood; 8 categories never ingested (incl. dosha_label, yoga_label); KP domain-mapping starve (LCA-9b, R-42, KP-4) | F-0003 |
| Data: L3 activation writer | 11 | 1 | R-45 final attribution: rows exist (66,836/66,747) but ~99% NULL activation dates — writer defect, survives rebuild; 602/638 obstruction windows unreachable | F-0982, F-L10-018 |
| Data: never-computed | 22 | 0 | Mrityu-bhaga, ayurdaya/longevity, sensitive degrees (R-47) — no writer exists | Lane 8 |
| Doctrine: class-9 corpus | 135 | 0 | Requirements spec for P-1..P-13; not defects | Lane 2 logs |

## §4 — Wave structure (ratified sequencing thesis)

```
W0 (queue-jumper)     LCA-17 isolation fix + regression test
W1 (serving plane)    WP-1.1 .. WP-1.6  ∥  WP-1.7 bench lane
W2 (writer wave)      WP-2.1 .. WP-2.5   — fix code first, no interim rebuilds
W3 (verification)     ONE Abhinandan rebuild (also clears stale state)
W4 (re-audit)         328-question matrix + Lane-8 dossiers + promise grading vs §2 baseline
```

Rationale (from the audit's own class→layer mapping): the serving plane is the weakest
link and the bulk of the win; writer fixes are batched so exactly one rebuild serves as
the verification event; the re-audit re-measures the §2 numbers with the same frozen
instruments (blind-anchor method + verification-swarm/E-6 depth gate as the standing
verification template).

## §5 — Work packages

Every WP inherits: FROZEN orchestrator contract (§N.2 — writers never extend the
orchestrator); §N.3 idempotency (L1+ delete-then-insert per chart × natural key); B.10
(no fabricated computation — external-computation gaps marked, Swiss Ephemeris path via
the existing sidecar writers); B.3 (derivation ledger on every L2+ claim — this is not
just governance, it is WP-1.2's product); findings-only history preserved (no editing
audit artifacts). Each WP ships with its own regression proof and maps its finding
coverage into TRACEABILITY_MATRIX at close.

### Wave 0 — Integrity (blocks everything)

**WP-0.1 — LCA-17 wrong-chart isolation fix.**
Scope: root-cause the nondeterministic cross-chart substitution in
`get_chart_orientation` (and audit every sibling tool sharing its chart-resolution
path) under concurrent multi-chart load; fix; add a permanent concurrent-load
regression test (two charts, interleaved calls, N≥100 iterations, zero substitutions).
Layer: serving-query / session-state. Coverage: 9 findings (F-0893 family).
Acceptance: regression test green in CI; both charts; entitlement-class sign-off.

### Wave 1 — Serving plane (the bulk of the win; six workstreams + parallel bench lane)

**WP-1.1 — Prod consult resurrection (LCA-2, CRITICAL).**
Scope: the consult/chat path unconditionally queries the retired `reports` relation and
fails for every chart. Decide-and-implement: re-point consult to the live retrieval
surfaces (not resurrect the retired table). Per E-7c(ii), consult-pipeline orchestration
was NOT covered by the audit — this WP includes its own smoke matrix.
Acceptance: consult serves both charts end-to-end; no reference to `reports` remains.

**WP-1.2 — Attribution + domain discrimination on every ranked surface.**
Scope: (a) every ranked row carries a resolvable derivation ledger (constituent
fact_ids resolving to `chart_facts.fact_id` per §N.5 — kills 100% UNATTRIBUTED, R-44a);
(b) fix the domain mapping so readings discriminate (kills domain-invariant top-K,
KP-4 starve); (c) add the missing domains (education/vidya, moksha as a real
domain over the 4-8-12 trikona + Ketu axis, not a bhava-9 alias); (d) de-DROWN:
salience re-tiering so per-varga trivia cannot occupy major tier (interacts with
WP-2.4 — the serving-side cap lands here, the ingestion-side fix lands there).
Layer: ranking/serving-query. Coverage: 81 (c7) + the c4 domain-collapse subset
(F-0470/0474/0477 family). Acceptance: Lane-6 rubric 7.4 raw metrics re-run — zero
UNATTRIBUTED rows; wealth/relationship top-20 overlap below the tolerance stated
inline (E-2 discipline: no silent thresholds); education + moksha lenses return
domain-specific heads on both charts.

**WP-1.3 — Serve the computed-but-unserved + fix parameter-ignoring tools.**
Scope: (a) the 23 computed-but-unserved assets from the Lane-10 ledger (kala_taranga
79,728 rows, kala_avadhi, ga_medical, ga_vastu, ga_yoga_firings, cgm_motifs/paths, …) —
each gets a serving path or an explicit native-ratified "not served, reason" entry;
(b) `query_dasha_periods` honors `system_id` (~437k non-vimshottari rows); (c) dasha
tools honor requested windows (kills the fixed today-centered-decade wall — exam-timing
and interruption questions structurally unanswerable today); (d) `lel_query` serves the
57 user-authored life events; (e) `get_temporal_windows` serving query fixed in concert
with WP-2.1 (writer) — this is the serving half of R-45's remediation;
(f) dead-tool registry purge + help-text honesty (LCA-12: 17 dead tools advertised).
Layer: MCP contract / serving-query. Coverage: 193 (c1) + c4 hollow subset.
Acceptance: Lane-10 promise re-grade on the 23 assets → DELIVERS; the four named
parameter defects have call-level regression tests; census re-run shows zero
advertised-dead tools.

**WP-1.4 — Large-N synthesis instrument (P-11 design + build; P-10 contract as input).**
Scope: staged retrieval-with-aggregation over the L2 pre-computed surfaces
(convergence, CDLM, CGM), producing narrative with a derivation ledger; one-pass or
incremental per native's standing acceptance. Includes the P-10 intent-decomposition
contract (compound question → evidence contract, not just a class) as the instrument's
front door. Design artifact first (this session's successor ratifies), then build.
Layer: new serving capability. Coverage: 52 (c8) incl. F-0949/0961/0973.
Acceptance: the Lane-7 seven heavy questions re-run — 0/7 at ceiling; marriage and
moksha factor universes composed with ledger; wall-free (no flat top-K path).
Dependency: consumes WP-2.2's populated CDLM/CGM stages for full depth — design and
serving skeleton land in W1, final acceptance re-measured at W4.

**WP-1.5 — Receipt honesty + budget discipline.**
Scope: every trim/truncation is declared (truncated flag + real cursor — F-0963 class);
un-budgeted dumps get ceilings (extend the R5.x budget discipline to all tools);
IDs-without-text eliminated (every served ID resolvable in-payload or one call away);
targeted deployed-channel receipt-honesty retest on `judgment_query` +
`ganita_yogas_get` (the inherited R-38/R-41 lane hole — closes the audit's declared
coverage gap). Layer: envelope/serving. Coverage: 127 (c5/c6) + R-38/R-41 residual.
Acceptance: Lane-4 re-run on the deployed channel — zero envelope-vs-payload
contradictions; R-38/R-41 retest verdicts filed.

**WP-1.6 — P-12 capability map seed (design + first cut).**
Scope: transform the Concept×Retrievability matrix (3,058 families, per-channel per E-8)
into the machine-readable concept→tool/service capability map; define the acquisition-
tracker record shape. Full demand-side planner behavior is doctrine work (deferred with
P-1..P-9), but the map itself is a Wave-1 artifact because WP-1.2/1.3/1.4 change what
is reachable and must update it as they land.
Acceptance: capability map artifact exists, keyed by concept family, regenerated
post-W1; every WP-1.3 newly-served asset appears in it.

**WP-1.7 — Local bench revival (parallel lane, independent blast radius).**
Scope: surgical-registry seam fix (45% dead tools), :8000 sidecar (auth 401, missing
`jhora` module, DATABASE_URL), local help-text parity with deployed. Explicitly NOT
consumer-channel work; it accelerates verification of every other WP.
Coverage: 192 (channel `surgical+8000`). Acceptance: Lane-1a census re-run local —
reachable-surgical count matches deployed-served equivalents; sidecar smoke green.

### Wave 2 — Writer wave (fix code first; rebuild once, in W3, as verification)

**WP-2.1 — L3 activation-date writer (R-45 final attribution).**
Scope: the ka_* activation writer emits ~99% NULL activation dates; fix the date
computation; obstruction windows (602/638 unreachable, F-L10-018) fixed in the same
writer family. FROZEN contract: `@register` WriterBase subclass changes only.
Acceptance (post-W3 rebuild): NULL-date rate ≈ 0 on both charts;
`get_temporal_windows` (WP-1.3e serving half) returns real windows for the native chart.

**WP-2.2 — Empty-shell stages (LCA-5) + native-chart silent zero (LCA-6).**
Scope: CDLM domain_rollups / evolution_gradients / pattern_clusters, CGM
chart_topology_summary, contradictions, RM tables, phala narration — writers produce
real rows or the stage is formally retired with its tool surface removed (no
advertised-empty middle ground). Root-cause the motif-stage zero on 482012f1 while
1c826d5a populates (LCA-6) — a per-chart conditional bug, not a capacity gap.
Coverage: 104. Acceptance (post-W3): zero advertised stages returning [] on either
chart; motif parity across charts.

**WP-2.3 — CGM graph completion (LCA-9a-1).**
Scope: graha↔bhava edges (60/60 bhavas currently orphaned), yoga nodes + membership
edges, temporal hooks (dasha/transit anchors) — per B.3 every edge cites L1 fact_ids.
Coverage: 63. Acceptance (post-W3): Lane-9a neighborhood traversal re-run — each graha
node reaches dispositor chain, yogas, bhava lords, temporal hooks in ≤2 calls.

**WP-2.4 — MSR ingestion redesign (LCA-9b).**
Scope: flood control (no single fact_category may emit an undifferentiated
15,660-signal wall — tier caps + per-category salience design); ingest the 8
never-consumed categories (dosha_label, yoga_label first — doshas/yogas absent from
MSR is doctrinally indefensible); fix R-42 (all doshas citing one constituent fact)
and KP domain-mapping starve. §N.5 discipline: signals REFERENCE L1 fact_ids, never
restate values (the MSR drift trap). Coverage: 40. Acceptance (post-W3): L1→MSR
ingestion matrix re-built — 0 BROKEN / 0 NOT_CONSUMED categories; max single-category
share within the ratified cap; dosha/yoga signals attributed and domain-mapped.

**WP-2.5 — Never-computed quantities (R-47).**
Scope: new ga_* writer work — mrityu-bhaga, sensitive degrees, ayurdaya/longevity
(ayurdaya method selection is a native ruling at brief time: which classical method(s),
served with method attribution per P-3's eventual doctrine). B.10 applies: computation
via the deterministic sidecar; no LLM-invented values.
Coverage: 22. Acceptance (post-W3): quantities present in chart_facts for both charts
with classical-rule re-derivation spot-checks; served via WP-1.3 paths.

### Wave 3 — The verification rebuild

**WP-3.1 — ONE Abhinandan (1c826d5a) full-cascade rebuild.**
Purpose: (a) verification event for every W2 writer fix; (b) clears stale state.
Protocol: orchestrator "click Build" only — zero manual writes; capture per-asset
row-count deltas vs the L1/L2 canonical counts; every WP-2.x post-W3 acceptance
executes against this rebuild. Native chart (482012f1) rebuild only after Abhinandan
verifies green — native ruling at that gate.

### Wave 4 — Re-audit (the program's exit measurement)

**WP-4.1 — Re-run the frozen instruments against the §2 baseline.**
Scope: 328-question matrix (primary acceptance surface) + Lane-8 dossiers (20) +
Lane-10 promise grading (67 assets) + Concept×Retrievability re-grade (E-8 per-channel;
the 583 down-pipeline families re-graded once consult is repaired per E-8's own
clause) + Lane-6 ranking metrics + Lane-7 heavy questions. Method: blind-anchor +
verification-swarm/E-6 depth gate (the standing template). Exit gates: **native to
ratify before W4 runs** — proposed: SUFFICIENT ≥ a native-set floor (the 1.2%→target
question), promise delivery ≥ 80%, truly-unreachable families only where ratified,
0/7→7/7 heavy-question composition, class-9 rate measured (its elimination is the
doctrine campaign's mission, not this program's gate).

### Deferred (explicitly out of this program)

P-1..P-9 + P-13 doctrine/method layers (vidhi, adjudication, negative knowledge,
adversarial retrieval, normative bands, longitudinal loop, fragility propagation,
gochara composition, narration vocabulary, services-composition doctrine) — a
dedicated post-W4 design campaign, specified against post-remediation reality, with
the 135-finding class-9 corpus + Lane-2 evidence-plan corpus as requirements input.
Portal/UI, rate limiting, cross-chart pool (the R5.1 deferred shelf) remain open on
their own track.

## §6 — Open residuals inherited (tracked, not blocking)

- R-38/R-41 deployed-channel receipt-honesty retest → owned by WP-1.5.
- 7-tool census gap → resolved at consolidation (ref_remedies_* family); no action.
- Fused verifier disagreement #1 (single-path) → retest folded into WP-1.5's Lane-4 re-run.
- `amjis-pending-stream-reaper` silent prod failure (found in R5.2 A4, out of scope
  there) → assign at W1 brief time; one-line Cloud Scheduler header fix, same class as
  the proven `x-marsys-cron-secret` pattern.

## §7 — Program mechanics

- Execution vehicle: Claude Code sessions under CLAUDECODE_BRIEF discipline; one brief
  per WP (Brief Foundry pattern); this plan is the parent artifact every brief cites.
- Verification: every WP carries independent verification (the E-5/E-6 swarm discipline
  where agentic; conductor-level live retest on any verifier disagreement — the R5.1
  rule: trust neither self-report).
- Traceability: at each WP close, its finding-IDs flip to REMEDIATED-PENDING-W4 in the
  register; W4 flips them to CLOSED or re-opens with evidence. MARSYS_DEFECT_GAP_REGISTER
  remains the permanent record; this plan does not duplicate it.
- Sequencing hard rule: no chart rebuild before W3; no gate-lowering at W4 (the R5.3
  precedent: gates are capability problems, not measurement problems).

*End of REMEDIATION_PLAN_v1_0 — drafted 2026-07-12; native ratification pending on:
WP decomposition, W4 exit-gate numbers, ayurdaya method selection (WP-2.5), and the
"not served, reason" dispositions WP-1.3 will surface.*
