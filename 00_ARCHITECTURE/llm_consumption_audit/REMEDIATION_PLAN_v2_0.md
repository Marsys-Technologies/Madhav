---
artifact: REMEDIATION_PLAN_v2_0
type: REMEDIATION_MASTER_PLAN (plan §10 step 2 output — SUPERSEDES REMEDIATION_PLAN_v1_0.md)
version: 2.0
status: SUPERSEDED by REMEDIATION_PLAN_v3_0.md (2026-07-12 third pass; §5 WP text + §6.1-6.4 verification architecture remain NORMATIVE, incorporated into v3 by reference — retained in place)
authored_by: Fable 5 (Cowork) + native, session LLM-CONSUMPTION-REMEDIATION-PLANNING-2026-07-12
consumes_from: PLANNING_SESSION_HANDOFF_v1_0.md · LLM_CONSUMPTION_AUDIT_v1_0.md ·
  deliverables/findings.jsonl (1,009) · MARSYS_DEFECT_GAP_REGISTER_v2_0.md (LCA-1..19, R-37..48, KP-4) ·
  GATE_RATIFICATION_v1_0.md (E-2/E-4/E-5/E-6/E-7c/E-8 bind) ·
  briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md §9 (P-1..P-13) · state/LANE9.md · Lane-10 ledger
coverage_manifest: deliverables/wp_coverage.jsonl — ALL 1,009 finding_ids → exactly one WP
  (or DOCTRINE-DEFERRED); 0 unmapped; regenerable via the §3 clustering rule
chart_ids: 482012f1 (Abhisek, native) · 1c826d5a (Abhinandan, verification chart)
changelog:
  - v2.0 (2026-07-12): second pass per native directive — (a) machine-verified coverage:
    every finding_id assigned, manifest shipped; register sweep added explicit ownership for
    R-43, R-46, LCA-3/-3-EXT/-7/-8, LCA-9b-5 referential integrity, LCA-1 CI invariant,
    LCA-16 data gaps (ayurdaya, organ taxonomy, character/buddhi domain), LCA-11 apex/assess
    dedup, LCA-18 residuals, ka_gochara/ka_tulana; new WP-1.8 (cross-path fidelity + verdict
    formula); WP-2.5 substantially widened per LCA-10. (b) Full per-WP context: root cause,
    fix locus, register-sourced fix guidance, evidence citations. (c) Execution model rebuilt:
    fully autonomous sub-agent swarm, parallel-first DAG, per-intervention domain-specific
    verification, NO human gates — all formerly-native mid-run decisions pre-ratified in §7.
  - v1.0 (2026-07-12): initial wave structure + 13 WPs (superseded in place).
---

# LLM Consumption Remediation — Master Plan v2.0

## §1 — Mission (native intent, verbatim from handoff)

The consuming LLM has completeness of information in width and depth, and can handle
narrow and broad questions generating small to huge input volumes for synthesis.

Success is measured, not asserted: §2's baseline numbers re-measured at W4 with the same
frozen instruments, against the §7.1 pre-ratified exit gates.

## §2 — Baseline the program must move (frozen 2026-07-12)

| Metric | Baseline | Instrument | W4 gate (§7.1) |
|---|---|---|---|
| Acharya questions fully SUFFICIENT | 4/328 (1.2%) | Lane-2 question matrix | ≥ 60% SUFFICIENT; ≤ 10% INSUFFICIENT |
| Class-9 improvisation | 328/328 | Class-9 logs | measured + categorized (gated by the doctrine campaign, not here) |
| Asset promise delivery | 28/67 (42%) | Lane-10 ledger | ≥ 85% DELIVERS (≥57/67) |
| Families reachable via real channels | 2,318/3,058 (76%) | Concept×Retrievability matrix (E-8 per-channel) | ≥ 95%; residual truly-unreachable each carries a ratified disposition |
| Heavy-question synthesis | 0/7 | Lane-7 spec | 7/7 composed with derivation ledger |
| Ranked-surface attribution | 0% attributed | Lane-6 rubric 7.4 raw metrics | 100% rows carry resolvable ledger |
| Domain discrimination (wealth∩relationship top-20) | 95% overlap | Lane-6 | ≤ 25% overlap, rationale stated inline (E-2) |
| Dossier synthesizability | 1/20; 73.5% avg depth | Lane-8 facet matrices | ≥ 18/20 SYNTHESIZABLE; ≥ 90% avg depth |
| Envelope-vs-payload contradictions | multiple classes | Lane-4 re-run (deployed) | 0 |

## §3 — Coverage guarantee (the "not one point missed" mechanism)

1. **Finding-level:** `deliverables/wp_coverage.jsonl` maps every one of the 1,009
   `finding_id`s to exactly one WP (or `DOCTRINE-DEFERRED`). Zero unmapped, machine-checked.
   Distribution: WP-1.3=295 · WP-1.7=172 · DOCTRINE-DEFERRED=135 · WP-1.2=79 · WP-1.5=78 ·
   WP-2.3=66 · WP-1.4=48 · WP-2.4=40 · WP-2.5=29 · WP-2.1=27 · WP-2.2=19 · WP-1.8=10 ·
   WP-1.1=7 · WP-0.1=4. CRITICALs: 30/30 owned (WP-0.1:1, WP-1.2:5, WP-1.3:7, WP-1.4:7,
   WP-1.7:1, WP-2.1:2, WP-2.2:5, WP-2.4:1, WP-2.5:1).
2. **Register-level:** every OPEN register class from the audit is named in exactly one WP
   below — LCA-1..19 (incl. -3-EXT, -9a-1, -9b-1..5), R-37..R-48, KP-4. The v2 sweep added
   explicit ownership for items v1 covered only implicitly (see changelog).
3. **Ledger-level:** the Lane-10 shortfall list (25 SHORTFALL + 14 PARTIAL assets) is
   enumerated inside WP-1.3/WP-2.2; the 114 held-but-not-received dossier facets (LCA-9)
   resolve through WP-1.3+WP-1.7 (they are the depth-axis view of the same retrieval gap).
4. **Residual-level:** the audit's declared holes (R-38/R-41 retest, verifier disagreement
   #1, consult-pipeline behaviors deferred under E-7c(ii)) each appear in §8 with an owner.
5. **Enforcement:** the W4 conductor recomputes the manifest against the then-current
   register; any finding without a REMEDIATED/CLOSED/DEFERRED disposition blocks program
   close (this check is itself autonomous — §6).
6. **Doctrine boundary:** the 135 class-9 findings are NOT remediated here by design —
   they are the requirements corpus for the post-W4 doctrine campaign (P-1..P-9, P-13).
   Deferral is a tracked disposition, not a gap.

## §4 — Wave DAG (parallel-first; sequential only where physics demands)

```
W0: WP-0.1 ──────────────────────────────┐  (blocks everything: no swarm runs
                                          │   concurrent multi-chart calls until
                                          ▼   isolation is proven)
W1 (all seven lanes PARALLEL, worktree-isolated, merge-ordered):
    WP-1.1  WP-1.2  WP-1.3  WP-1.4(design+skeleton)  WP-1.5  WP-1.8  ∥  WP-1.7(bench)
    WP-1.6 (capability map) runs LAST in W1 — consumes 1.2/1.3/1.4/1.5 landed state
                                          │
W2 (writer families PARALLEL — disjoint writer files, shared-nothing):
    WP-2.1(ka_*)  WP-2.2(bo_cdlm/cgm/rm/samvada + ph_narration)  WP-2.3(bo_cgm graph)
    WP-2.4(bo_laksana)  WP-2.5(ga_* new writers + L0 reference seed)
                                          │
W3: WP-3.1 Abhinandan rebuild (SEQUENTIAL — single verification event)
     └─ on green: WP-3.2 native-chart rebuild (autonomous, §7.4 safety rails)
                                          │
W4: WP-4.1 re-audit (lanes PARALLEL, per the audit's own swarm DAG) → program close
```

Sequencing rationale: W0 is an entitlement bug that also poisons swarm testing itself.
W1 before W2 because serving fixes are verifiable immediately against existing data,
while writer fixes are only fully verifiable at the W3 rebuild — batching them avoids
interim rebuilds. W2's five packages touch disjoint writer families and parallelize
cleanly. W3 is one event by ratified thesis. Cross-wave dependencies that do NOT block:
WP-1.3e (temporal-windows serving half) lands in W1 but its full acceptance re-runs
post-W3 (writer half WP-2.1); WP-1.4's deep acceptance re-measures at W4 once WP-2.2's
populated stages exist; WP-1.2d's serving-side salience cap is verified fully after
WP-2.4's ingestion-side fix rebuilds.

## §5 — Work packages (full context)

Every WP inherits the standing constraints: FROZEN orchestrator contract (§N.2 — writers
are `@register` WriterBase subclasses; a needed contract change is a HALT, the one
legitimate stop); §N.3 idempotency (delete-then-insert per chart × natural key); B.10 (no
fabricated computation — deterministic sidecar computes; LLM never invents values); B.3/§N.5
(derivation ledgers; L2+ references L1 fact_ids, never restates); no gate-lowering; no edits
to audit artifacts (findings history is immutable); every intervention verified per §6.3
before it counts as done.

### Wave 0

**WP-0.1 — LCA-17: wrong-chart substitution (CRITICAL, entitlement-class).**
- Root cause (register-guided): nondeterministic, load-correlated — manifested only under
  concurrent different-chart calls (Lane-6 swarm), never in 5/5 isolated probes. Signature
  = a cache/session in the orientation path keyed on something other than chart_id
  (candidates: auth.ts 60s validation cache, orientation/digest caches).
- Fix: reproduce under controlled concurrency (N workers, alternating chart_ids); audit
  EVERY cache on the orientation/digest path for chart_id-inclusive keys; add a server-side
  chart_id echo-back assertion (reject/refetch on mismatch) as defense-in-depth.
- Deliverables: fix + permanent concurrent-load regression test (2 charts, interleaved,
  N≥100 iterations, 0 substitutions) in CI.
- Coverage: 4 findings (F-0893 family). Verifier: **security/entitlement agent** (§6.4) —
  re-runs the concurrency harness independently, fresh context, quoted payloads.

### Wave 1 — Serving plane

**WP-1.1 — LCA-2: prod consult resurrection (CRITICAL).**
- Root cause (register-verbatim): `consult/route.ts` L300 unconditionally SELECTs from
  `reports`; relation absent from deployed Cloud SQL (DDL only in migrations/_archive);
  error mislabeled `SYSTEM_DB_UNAVAILABLE {retry:true}` — chart-independent, kills the
  product's flagship surface for every chart.
- Fix: (a) remove/none-safe the retired-`reports` lookup — re-point consult to live
  retrieval surfaces; (b) stop mapping permanent missing-relation errors to the transient
  retry class (the class-5 dishonesty half); (c) consult orchestration smoke matrix (both
  charts × {orientation, domain question, timing question}) — E-7c(ii) left this pipeline
  unaudited, so this WP audits-by-testing what it touches.
- Coverage: 7. Verifier: **serving-wire agent** — live consult calls, both charts, verbatim
  payload evidence; plus a **jyotish-domain agent** sanity-grading one consult answer per
  chart against chart_facts ground truth.

**WP-1.2 — Ranked-surface attribution, domain discrimination, salience de-drowning (LCA-14, R-44, KP-4 serving half, LCA-9b-2 serving cap).**
- Root cause: 0 rows carry `grounding.fact_ids` (100% UNATTRIBUTED — orientation top
  entity is literally `UNATTRIBUTED` at 84.8 salience vs Venus 1.05); domain readings are
  domain-invariant (wealth∩relationship 19/20 — the domain/salience mapping, same root as
  KP-4); almanac trivia at major tier drowns chart-defining signals.
- Fix: (a) resolvable derivation ledger on EVERY ranked row (fact_ids resolving to
  chart_facts per §N.5); (b) domain-mapping fix so readings discriminate; (c) new domains:
  education/vidya; moksha as a real domain (4-8-12 trikona + Ketu axis, not a bhava-9
  alias); character/buddhi domain in judgment_query + un-collapse its bhava→domain map
  (bhava-5 = progeny only today; bhava-4 mislabeled education — F-0756); (d) serving-side
  salience demotion: descriptive fact_keys (akshara, symbol, yoni) and per-varga granular
  data barred from major/chart_defining candidacy (ingestion half in WP-2.4);
  (e) `get_domain_reading` rows hydrated with headline text (kills IDs-without-text at
  this surface; LCA-18c).
- Coverage: 79 (5 CRIT). Verifier: **jyotish-domain agent** (are the discriminated
  readings classically sane? is moksha's factor universe right?) + **serving-wire agent**
  (rubric-7.4 raw metrics re-run per E-2 — no silent thresholds; per-surface per-chart).

**WP-1.3 — Serve everything computed; honor every declared parameter (LCA-19, LCA-4-deployed-residue, LCA-3/-3-EXT/-7 param no-ops, LCA-11, LCA-12, R-40 stages).**
- Root cause: the dominant Lane-10 shortfall is retrieval-plane — computed-but-unserved
  even on the deployed channel; plus a family of tools that silently ignore their own
  declared parameters (the worst class for an LLM consumer: it cannot know its scope
  request was dropped).
- Fix, enumerated:
  (a) serving paths for the 23 computed-but-unserved assets — kala_taranga (79,728
      rows/chart), kala_avadhi (1,571), kala_sangam rigor-stratum (6,484), ga_medical (45),
      ga_vastu_planet_direction_map (40), ga_yoga_firings (bhanga + activation detail),
      bodha_cdlm_chart_summary, bodha_cgm_motifs/paths, bo_chart_gestalt, ka_gochara
      transit-event search, ka_tulana compare-verdict, + the remainder of the Lane-10
      SHORTFALL list; disposition rule per §7.3 (serve; parking requires flag, not
      autonomous retirement);
  (b) `query_dasha_periods` honors `system_id` (~437k non-vimshottari rows dark — F-0354);
  (c) dasha tools honor requested windows (the fixed today-centered decade makes
      exam-timing/interruption questions structurally unanswerable — F-0471/0485 family);
  (d) `lel_query` serves the 57 user-authored life events (F-L10-021) — this also unblocks
      the L5 calibration loop's consumption side;
  (e) `get_temporal_windows`/`kala_windows_get` serving half: honor date params, echo the
      filter applied (writer half = WP-2.1; full acceptance post-W3);
  (f) `query_chart_facts`: `fact_category`/`fact_subject` filters actually filter
      (LCA-3); invalid category → error/empty, not 119KB dump; disclosed pagination with
      `total` + `more_available` over the 5,566 subjects (LCA-3-EXT'ს 1000-cap silent
      drop); serve ALL 6 ayanamshas, not lahiri-only;
  (g) `msr_sql` honors its `sql`/projection param (LCA-7 — fixed 17-of-115-column
      projection today);
  (h) dead-tool registry purge + help-text regeneration from the live registry (LCA-12);
  (i) apex_*/assess_* duplicate-family dedup (LCA-11) + R-40: assess_* budget/trim
      discipline and the empty verdict_skeleton stages root-caused (shared root with R-45
      → coordinate with WP-2.1).
- Coverage: 295 (7 CRIT) — the largest package; the brief foundry splits it into
  sub-briefs (a)-(i) which parallelize internally per §6.2.
- Verifier: **serving-wire agent** per sub-brief (call-level regression: every fixed
  parameter has a test proving the filter narrows the payload; every new surface returns
  rows matching DB ground truth counts) + **data-plane agent** cross-checking served
  values against SQL on the same rows (fidelity, not just reachability).

**WP-1.4 — Large-N synthesis instrument (LCA-15/R-48; P-11 build, P-10 contract as front door).**
- Root cause: no serving path composes N-hundred factors — flat top-K walls (13,364
  signals), un-budgeted dumps, IDs-without-text; the L2 pre-computation (convergence,
  CDLM, CGM) exists precisely for this and nothing consumes it.
- Design (W1, autonomous — design review by the verifier swarm, not a human gate):
  staged retrieval-with-aggregation: (1) P-10 intent decomposition — compound question →
  evidence contract; (2) plan against pre-aggregated L2 surfaces first (convergence
  tables, CDLM cells, CGM paths, family composites), atomic signals only for drill;
  (3) map-reduce over signal families with running state; (4) narrative output with
  derivation ledger (every claim → fact_ids/signal_ids). One-pass or incremental —
  native's standing acceptance covers either.
- Build (W1 skeleton against existing surfaces; full depth lights up when WP-2.2's stages
  populate at W3).
- Coverage: 48 (7 CRIT — incl. F-0949 flat-wall, F-0961 marriage universe, F-0973/0974
  moksha). Verifier: **jyotish-domain agent** grades composed answers on the 7 Lane-7
  heavy questions against CHARTER §7 rubrics (real rubric grading, the restored-grader
  path from R5.3 §B); **serving-wire agent** verifies ledger resolvability on every claim.

**WP-1.5 — Receipt honesty + budget discipline, everywhere (LCA-18 residuals, LCA-8, R-38/R-41 retest, F-0963 class).**
- Root cause: envelope lies — `truncated:false` at 200/7,014 with null cursor; orientation
  serves 10 of ~13.3k with `pagination.total:null`; `ganita_yogas_get` verdict counters
  contradict its own served rows (R-41); `judgment_query` varga_confirmed-while-empty
  (R-38); `list_entities` silently drops 552/652 (whole entity classes invisible);
  non-monotonic salience rank; digest counts as strings.
- Fix: a single program-wide envelope contract — every trim declared (true `truncated`,
  real `total`, working cursor/`more_available`); ceilings on all un-budgeted tools
  (extend the proven R5.x budget pattern); IDs resolvable in-payload or one declared call
  away; v3 verdict counters count served rows; type + monotonicity hygiene; the
  R-38/R-41 deployed-channel retest executes here (closes the audit's declared lane hole).
- Coverage: 78. Verifier: **serving-wire agent** — Lane-4 protocol re-run on the deployed
  channel across ALL tools (not a sample): zero envelope-vs-payload contradictions, quoted.

**WP-1.6 — P-12 capability map (machine-readable concept→tool/service) + acquisition-tracker schema.**
- Context: Lane-1b's Concept×Retrievability matrix (3,058 families, per-channel per E-8)
  is the ratified seed. MCP_USAGE_GUIDE is prose — not keyed by concept — hence the
  demand-side planner has nothing to plan against.
- Build: transform matrix → capability map keyed by concept family with per-channel
  serving routes; define the acquisition-tracker record (needed/received/exhausted per
  evidence-plan item); regenerate AFTER WP-1.2/1.3/1.4/1.5 land (their fixes change
  reachability — hence last in W1). Full demand-side planner behavior = doctrine campaign;
  the map is built here because W4's re-grade needs it and every W1 WP feeds it.
- Coverage: enabler (no direct finding IDs; P-12 partial). Verifier: **data-plane agent** —
  samples map entries, executes the claimed route, confirms the concept actually arrives.

**WP-1.7 — Local bench revival (parallel lane; LCA-1, LCA-13, bench-scoped LCA-4/-11/-12 residue).**
- Root cause: `MCP_TO_RETRIEVAL_TOOL` whitelists 19 tools whose targets are absent from
  `TOOL_NAME_TO_URI` → `getToolByName` undefined → 500 on every call (45% of the surgical
  surface dead, incl. cgm_graph_walk/kp_query/temporal/timeline_query); :8000 sidecar —
  auth 401 (`Invalid API key`), `No module named jhora`, `DATABASE_URL` unset, plus
  `query_ephemeris` reporting ok:true/high-confidence while returning nothing.
- Fix: register the 19 URIs (or remove dead whitelist entries where the deployed twin is
  canonical); **CI/startup invariant: every whitelist value must resolve via
  getToolByName — fail CI otherwise** (register-mandated, prevents recurrence); sidecar
  key + jhora install + DATABASE_URL; honest empty-confidence on ephemeris.
- Coverage: 172 (1 CRIT). Independent blast radius — pure-parallel lane; a working bench
  accelerates every other WP's verification. Verifier: **infra agent** — Lane-1a census
  re-run local, sidecar smoke, CI invariant proven by mutation (remove a URI, CI must fail).

**WP-1.8 — Cross-path fidelity + varga-aware verdicts (R-43, R-46, Lane-3 c2/c3, AVAYOGI collapse, cross-surface inconsistency).** *(new in v2)*
- Root cause: (R-43, third instance of the D-1/G-7 family) denormalized
  `chart_dashas.lord_natal_dignity_d1` wrong (Saturn "own" in Scorpio) or NULL,
  `lord_natal_shadbala_total` never populated — dasha-lord strength invisible to judgment;
  (R-46) the deterministic verdict composite weights ONLY D1 — varga evidence structurally
  cannot move a verdict (Parashara: D9 is the fruit of the promise); multi-formula rows
  (AVAYOGI Virgo-vs-Libra) silently collapse to one in the pivot; assess_health top-10
  buries what get_signals surfaces (cross-surface INCONSISTENT).
- Fix: extend the D-1/G-7 re-derivation to dignity + shadbala columns with a permanent
  verifier cross-check (`dignity == chart_facts dignity` — the register's own
  prescription); add varga terms to the verdict formula (operative-varga dignity of
  bhāveśa/kāraka minimum) — sequenced AFTER WP-1.5 fixes R-38 so varga rows exist to
  weigh; multi-formula disclosure (serve both rows + formula_id); reconcile assess_*
  ranking with get_signals so surfaces agree.
- Coverage: 10 + register rows. Verifier: **jyotish-domain agent** (varga weighting is
  classical-doctrine work — graded against cited shastra, B.3) + **data-plane agent**
  (column re-derivation vs chart_facts on every dasha row, both charts).

### Wave 2 — Writer wave (code first; verification completes at W3)

**WP-2.1 — L3 activation-date writer (R-45 final attribution; LANE0 root cause).**
- Root cause (Item-0, precise): the ka_* activation writer emits ~99% of kala_activation
  rows with NULL `activation_start/end` and no fallback in
  `activation_predicted_dates_jsonb`; the serving query is CORRECT and correctly excludes
  them (native chart: 0/13,364 dated → served 0). Survives rebuild — a naive re-run
  cannot fix it. Confirmed shared root of R-39 (empty timing_hooks) and R-40
  (activating_dasha=0). Obstruction windows: 602/638 unreachable (F-L10-018), same family.
- Fix: writer date-population logic (the predicate→date resolution stage); obstruction
  window emission; edge temporal hooks feed WP-2.3 (cgm edge `active_dasha_periods_jsonb`
  shares this fix per the register).
- Coverage: 27 (2 CRIT). Verifier (post-W3): **data-plane agent** — NULL-date rate ≈0 both
  charts; **serving-wire agent** — get_temporal_windows returns real windows for the
  native chart on default ayanamsha; R-39/R-40 downstream re-probed (timing_hooks +
  activating_dasha now populate).

**WP-2.2 — Empty-shell writers (LCA-5) + native-chart motif zero (LCA-6) + bo_sangati.**
- Root cause: writers ran and emitted nothing — bodha_cdlm_domain_rollups /
  evolution_gradients / pattern_clusters, bodha_cgm_chart_topology_summary / sub_graphs,
  bodha_contradictions (the engine is inert — R-44e's contradiction_count=0 is this),
  bodha_rm_chart_summary / dasha_windowed_prescriptions / dosha_remedy_bundles /
  pattern_remedies, phala_phaladesa.narration_jsonb (NULL, status=pending, all rows);
  bo_sangati per-domain evidence ledger never computed (Lane-10 data-plane subset).
  LCA-6: the native chart's motif stage emitted 0 while the SAME pipeline produced 6 for
  Abhinandan an hour earlier — a chart-conditional writer bug (the native chart is
  documented to hold chain configurations, so 0 is a defect, not absence).
- Fix: root-cause each writer (ran-and-no-op'd vs never-invoked); populate or formally
  retire WITH tool-surface removal (no advertised-empty middle ground; retirement is a
  §7.3 flagged disposition, not silent); debug the native-chart motif conditional
  (parivartana/stellium detection).
- Coverage: 19 (5 CRIT). Verifier (post-W3): **data-plane agent** — count(*)>0 per stage
  per chart, motif parity, contradiction rows exist where MSR holds contradiction_pairs;
  **jyotish-domain agent** spot-grades emitted contradictions/rollups for classical sanity.

**WP-2.3 — CGM graph completion (LCA-9a-1).**
- Root cause: graph is graha-to-graha only — 60/60 bhava nodes have 0 edges; no
  `node_type='yoga'` exists; `active_dasha_periods_jsonb` never populated on any edge
  (shares WP-2.1's fix); 42/42 sampled nodes fail the plan's own Mercury probe.
- Fix: graha↔bhava edges (lordship, occupancy, aspect), yoga first-class nodes +
  membership edges, temporal hooks on edges; every edge cites L1 fact_ids (B.3);
  then re-enable graph consumption (cgm_graph_walk revives via WP-1.7's registry fix —
  cross-WP dependency noted, both sides tested together at W3).
- Coverage: 66. Verifier (post-W3): **jyotish-domain agent** re-runs the Lane-9a
  neighborhood protocol — each graha reaches dispositor chain, yogas, bhava lords,
  temporal hooks in ≤2 calls, edges cite resolving fact_ids.

**WP-2.4 — MSR ingestion redesign (LCA-9b-1..5, R-42, R-44b ingestion half, KP-4 ingestion half).**
- Root cause, enumerated from the register: (9b-1) `aspect_jaimini_per_varga` 1:1-emits
  15,660 identical-salience signals/chart — the funnel floods instead of narrowing;
  (9b-2) per-varga/granular categories promoted to major/chart_defining
  (aspect_parashari_per_varga chart_defining=229!); (9b-3) KP cusp-lords domain-mapped
  character|relationship only — 2nd/11th-cusp wealth significators can never surface in a
  wealth query, 63% of cusp facts un-consumed; (9b-4) EIGHT categories entirely
  un-ingested including dosha_label (220 facts, 0 signals) and yoga_label (75, 0) — the
  two most chart-defining structures in Jyotish absent from MSR; (9b-5) all 220 dosha
  signals cite 10 constituent fact_ids that resolve to NOTHING — a referential-integrity
  break violating §N.5.
- Fix: aggregation/tiering for per-varga families (no 1:1 flat emission; ratified caps);
  salience re-tiering (divisional/granular barred from top tiers — serving cap is
  WP-1.2d, this is the source fix); KP house-aware domain inheritance + ingest the
  un-consumed 63%; ingest the 8 missing categories; real per-dosha/yoga constituent
  attribution; **permanent referential-integrity validator: every
  constituent_facts_array entry MUST resolve to chart_facts.fact_id — CI-enforced**
  (register-mandated; also guards the MSR-drift trap §N.5).
- Coverage: 40 (1 CRIT). Verifier (post-W3): **data-plane agent** rebuilds the L1→MSR
  ingestion matrix — 0 BROKEN / 0 NOT_CONSUMED; flood caps hold; 100% constituent
  resolution; **jyotish-domain agent** grades the new salience tiering (does an acharya's
  chart-defining list now sit at chart_defining?).

**WP-2.5 — Never-computed quantities (R-47, LCA-10, LCA-16 data gaps).** *(widened in v2)*
- Root cause: UNREACHABLE-by-nonexistence — the canon calls for them, no writer computes
  them. Full LCA-10 enumeration (Venus spot-check had 7 canonical facets at 0 rows):
  per-graha mrityu-bhaga degree checks, neecha-bhanga check, kartari (papa/shubha),
  Sarvatobhadra vedha, 22nd drekkana + 64th navamsa (khareshwara), pushkara-bhaga +
  pushkara-navamsa, declination/kranti/shara, per-graha gandanta proximity. Plus LCA-16's
  two: **ayurdaya/longevity** (Pindayu/Nisargayu/Amsayu, maraka-dasha linkage,
  alpa/madhya/purna classification) and the **organ/body-system taxonomy**
  (graha/sign→body-part reference map — L0 seed + L1 per-chart application; without it
  no disease question can be answered doctrinally).
- Fix: new L1 category `sensitive_degree_check` (graha × concept with degree evidence,
  per the register's prescription) via new ga_* writers on the deterministic sidecar;
  ayurdaya per §7.2 (all three classical methods, method-attributed — no autonomous
  method adjudication); L0 reference seed for the medical map (B.10: classical sources
  cited, no LLM invention); wire into dosha firing + judgment aspecting-graha condition.
- Coverage: 29 (1 CRIT). Verifier (post-W3): **jyotish-domain agent** — classical-rule
  re-derivation spot-checks per quantity per chart (e.g., recompute Venus mrityu-bhaga
  by hand from the cited rule and diff); **data-plane agent** — presence + served via
  WP-1.3 paths.

### Wave 3 — Verification rebuild (sequential)

**WP-3.1 — Abhinandan (1c826d5a) full-cascade rebuild.**
- Purpose: single verification event for all of W2 + stale-state clear.
- Protocol: pre-rebuild DB snapshot (the R6A precedent — golden-catch failures restore
  from snapshot); orchestrator "click Build" only, zero manual writes; per-asset
  row-count deltas captured vs canonical counts; then the ENTIRE post-W3 acceptance
  suite (every WP-2.x verifier block above) executes against the rebuilt chart, plus
  golden catches: FORENSIC-equivalent anchors for Abhinandan, zero-regression diff on
  the R6A yoga-integrity tests, WP-0.1 concurrency harness re-run (rebuild must not
  reintroduce leakage).
- On ANY golden-catch failure: auto-restore snapshot, HALT the wave, file the defect,
  re-enter W2 for the failing writer — autonomously (no human gate; the loop is
  fix → rebuild → re-verify).

**WP-3.2 — Native chart (482012f1) rebuild (autonomous, gated only by WP-3.1 green).**
- Runs only after WP-3.1's full verifier suite passes. Same snapshot/golden-catch/
  auto-restore protocol; golden catches = the 7 FORENSIC birth anchors (7/7 PASS
  mandatory), canonical row-count classes, LCA-6 motif check (native motifs > 0 —
  the defining test of WP-2.2's chart-conditional fix), documented chain configurations
  present in cgm (register CGM/G-2 Mars+Rahu+Mercury→11H reachable in the graph).

### Wave 4 — Re-audit (the exit measurement; lanes parallel)

**WP-4.1 — Frozen-instrument re-run vs §2 gates.**
- Scope: 328-question matrix (primary acceptance surface) · 20 Lane-8 dossiers · Lane-10
  promise re-grade (67 assets) · Concept×Retrievability re-grade (E-8 per-channel; the
  583 down-pipeline + 157 truly-unreachable families re-graded now that consult and the
  bench are repaired) · Lane-6 rubric-7.4 raw metrics on all 16 surfaces · Lane-7 heavy
  questions · Lane-4 receipt honesty (deployed, all tools) · class-9 rate measured and
  categorized (input to the doctrine campaign).
- Method: identical to the audit — blind-anchor discipline (the W4 conductor plants
  anchors from W1/W2 fix claims; lanes must rediscover them), E-5 verification swarm
  (≥15% re-execution sampling, 100% of CRIT/HIGH re-verified, PASS rows sampled for
  false-negatives), E-6 depth gate (quoted payloads or it didn't happen).
- Close: gates per §7.1 evaluated mechanically; coverage manifest recomputed (§3.5);
  register dispositions flipped REMEDIATED-PENDING-W4 → CLOSED or re-opened with
  evidence; CURRENT_STATE + SESSION_LOG close per governance. If a gate fails: the
  program does NOT lower it (R5.3 precedent, native-ruled immutable) — the conductor
  files the per-item root-cause map and loops the owning WP, autonomously, up to the
  §6.6 iteration budget; past budget, it halts and reports honestly.

### Deferred (tracked dispositions, not gaps)

- **Doctrine campaign (post-W4):** P-1..P-9 + P-13 (vidhi, negative knowledge,
  adjudication, adversarial retrieval, normative bands, longitudinal loop, fragility
  propagation, gochara composition, narration vocabulary, services doctrine) — designed
  against post-remediation reality; requirements corpus = the 135 class-9 findings +
  Lane-2 evidence-plan corpus + W4's fresh class-9 measurement.
- **R5.1 deferred shelf** (portal/UI, rate limiting, cross-chart pool, branch hygiene,
  JL-022 Option B) — separate track, unchanged.

## §6 — Autonomous execution architecture (sub-agent swarm; no human gates)

### §6.1 — Swarm model
Extends BUILD_GUARANTOR_SWARM_CHARTER (the proven 12-role pattern) with the audit's own
E-5/E-6 verification discipline:
- **Program Conductor** (one, persistent per wave): owns the DAG, dispatches WP
  conductors, resolves verifier disagreements by direct live retest (the R5.1 rule —
  trust neither self-report), owns HALT/restore decisions, writes the run ledger.
- **WP Conductor** (one per WP): decomposes the WP into intervention-sized briefs,
  dispatches implementation agents into isolated git worktrees (the proven R5.3
  five-lane pattern), sequences merges, dispatches verification per intervention.
- **Implementation agents** (N per WP, parallel where file-scopes are disjoint):
  execute one intervention each under CLAUDECODE_BRIEF discipline — may_touch /
  must_not_touch scoped per brief; never merge their own work.
- **Verifier agents** (§6.4 — domain-matched, fresh-context): verify every intervention
  before merge AND re-verify live post-deploy. A verifier NEVER sees the implementer's
  self-report before forming its own verdict (blind verification, E-5c).

### §6.2 — Parallelization rules
Parallel by default; sequential only when: (a) shared file surface (merge-order instead),
(b) semantic dependency declared in §4/§5 (e.g., WP-1.8 varga terms after WP-1.5's R-38
fix; WP-1.6 last in W1), (c) the W3 rebuild (single event by ratified thesis). Within
WP-1.3, sub-briefs (a)-(i) parallelize across worktrees; within W2, all five packages run
concurrently (disjoint writer families). The WP-0.1 → everything edge is absolute.

### §6.3 — Per-intervention verification protocol (the native's mandate, made mechanical)
EVERY intervention — fix, enhancement, elevation, new capability — is DONE only when:
1. **Implementer proof:** regression/unit test written and green; live call evidence
   (verbatim payload, both charts where chart-scoped) attached to the brief.
2. **Blind independent verification:** a domain-matched verifier agent (§6.4), fresh
   context, re-executes the reproducible call(s) from the ORIGINAL finding(s) — the exact
   failing call the audit recorded must now succeed/change as specified — plus its own
   adversarial probes (E-6: quoted payloads, both charts, negative cases: does the fix
   break the neighboring behavior?).
3. **False-negative guard (E-5c):** verifiers also sample interventions graded trivially
   green — a superficial "all clear" is the primary verification failure mode.
4. **Disagreement:** implementer-vs-verifier conflict escalates to the WP conductor's own
   live retest; unresolved → Program Conductor; the artifact records the episode
   (conflicting-verifier discipline, R5.1).
5. **Ledger:** every verification writes verified-agree / verified-disagree-resolved to
   the WP run ledger; a WP below 100% intervention-verification coverage cannot close.
6. **Post-merge live re-verification:** after deploy, the verifier re-runs the probe set
   against the deployed channel (the audit proved local-green ≠ deployed-green).

### §6.4 — Domain-specific verifier roster
| Verifier | Domain | Verifies for |
|---|---|---|
| **jyotish-domain agent** | classical doctrine, chart ground truth | WP-1.1/1.2/1.4/1.8/2.2/2.3/2.4/2.5 — is the output classically correct, shastra-cited (B.3), acharya-grade (§J)? |
| **serving-wire agent** | MCP/HTTP payload truth | WP-1.1/1.2/1.3/1.4/1.5/2.1 — does the wire deliver what's claimed, envelope-honest, budget-bounded, param-faithful? |
| **data-plane agent** | SQL ground truth, row-level fidelity | WP-1.3/1.6/1.8/2.1/2.2/2.4/2.5 — do served values equal stored truth; do counts, joins, referential integrity hold (§N.5)? |
| **security/entitlement agent** | isolation, authz | WP-0.1 + a standing check on every WP touching chart-scoped serving (no fix may widen entitlement) |
| **infra agent** | registries, CI, sidecar, deploy | WP-1.7 + the CI invariants (LCA-1 resolver check, §N.5 referential validator) proven by mutation testing |
Verifier assignments per WP are declared in §5; a WP with two listed verifiers requires
both verdicts green.

### §6.5 — No human gates: what replaces them
- All formerly-native mid-run decisions are pre-ratified in §7 at plan ratification.
- Native visibility is asynchronous: run ledgers + wave-close reports are written
  continuously; the native may read anytime but nothing waits for approval.
- The ONLY halts are safety halts (§6.6) — and they halt to a state, not to a question:
  snapshot-restored, defect filed, loop re-entered or program stopped with an honest
  report.

### §6.6 — Safety rails (autonomous ≠ unguarded)
- **HALT conditions:** FROZEN orchestrator contract change needed (§N.2 — hard stop,
  never autonomous); golden-catch failure at W3 (auto-restore + loop); W4 gate failure
  past iteration budget; entitlement regression detected by the standing security check.
- **Iteration budget:** each WP gets 3 fix-iterations per failed acceptance criterion;
  each wave-loop (W3 golden-catch, W4 gate) gets 2 re-entries. Past budget → honest halt
  report (the R5.2/R5.3 precedent: honest NOT-MET beats gate-gaming).
- **Data safety:** DB snapshot before ANY rebuild; writers only via orchestrator; no
  manual DML against product tables, ever; native chart rebuild only behind WP-3.1 green.
- **Merge safety:** worktree isolation; conductor-owned merges; zero-regression diff
  (the frozen R6A yoga-integrity tests + WP-0.1 harness + canary battery) on every merge
  to main.

## §7 — Pre-ratified decisions (ratify once with this plan; then the run is autonomous)

**§7.1 — W4 exit gates** (immutable once ratified; per-metric table in §2):
SUFFICIENT ≥60% and INSUFFICIENT ≤10% on the 328; promise DELIVERS ≥85%; reachability
≥95% with ratified dispositions on the remainder; heavy questions 7/7; attribution 100%;
wealth∩relationship overlap ≤25% with inline rationale; dossiers ≥18/20 SYNTHESIZABLE at
≥90% avg depth; envelope contradictions 0. Class-9 measured, not gated.

**§7.2 — Ayurdaya method:** compute ALL THREE classical methods (Pindayu, Nisargayu,
Amsayu) with per-method attribution and the classical applicability rule served alongside
(which method the canon prescribes for which chart class) — no autonomous adjudication of
a doctrinal dispute; adjudication doctrine is P-3's mandate, post-W4.

**§7.3 — Unserved-asset disposition rule:** default = SERVE (with budget discipline).
An agent may PARK an asset (flag `parked_pending_native_review`, excluded from W4's
promise denominator with the flag disclosed in the close report) only when serving is
blocked by a genuine design question; autonomous RETIREMENT is forbidden.

**§7.4 — Native-chart rebuild:** autonomous, strictly after WP-3.1 full-green, under the
§5 WP-3.2 golden catches (FORENSIC 7/7 mandatory) + snapshot/auto-restore.

**§7.5 — Empty-shell retirement (WP-2.2):** populating is the default; formal retirement
of a stage requires the same §7.3 parking flag — the no-advertised-empty rule is absolute
either way (tool surface goes with the stage).

**§7.6 — The one standing human touchpoint:** ratification of THIS plan (including these
numbers). After that, the program runs to W4 close or honest halt without human gates.

## §8 — Inherited residuals (owned)

| Residual | Owner |
|---|---|
| R-38/R-41 deployed receipt-honesty retest | WP-1.5 (executes it) |
| Fused verifier disagreement #1 (single-path) | WP-1.5 Lane-4 re-run |
| Consult-pipeline behaviors unaudited (E-7c(ii)) | WP-1.1 smoke matrix + W4 re-audit |
| `amjis-pending-stream-reaper` silent prod cron failure (R5.2 A4 discovery) | WP-1.7 (one-line header fix, proven `x-marsys-cron-secret` pattern) |
| 583 down-pipeline + 157 truly-unreachable families | W4 re-grade per E-8; dispositions per §7.3 |
| LCA-16's Lane-2 evidence-plan corpus + class-9 logs | Doctrine campaign (deferred, tracked) |

## §9 — Program mechanics

- Vehicle: Claude Code autonomous sessions per WP under CLAUDECODE_BRIEF discipline; the
  Brief Foundry pattern authors the briefs FROM this plan (each brief cites its §5 block,
  its coverage slice from wp_coverage.jsonl, its verifier assignment, its §7 rulings).
- Traceability: WP close flips its finding IDs → REMEDIATED-PENDING-W4 in the register;
  W4 flips → CLOSED/re-opened. wp_coverage.jsonl is the join key; the register stays the
  permanent record. TRACEABILITY_MATRIX extends with a remediation column at W4 close.
- Governance: session-open/close per protocol on every execution session; CURRENT_STATE
  updated at each wave close; red-team cadence per §M applies to the program's own
  sessions; this plan carries B.8 versioning and never mutates silently.

*End of REMEDIATION_PLAN_v2_0 — supersedes v1.0 in place (v1 retained per retain-in-place
archival). Single pending act: native ratification of the plan including §7. On
ratification: Brief Foundry authors WP-0.1's brief and the program launches.*
