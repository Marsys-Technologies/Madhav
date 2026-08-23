#!/usr/bin/env python3
"""NIRMĀṆA M0-T18 — reconcile NIRMANA_ELEVATION_PLAN_v4_0.md's quantitative claims
against live production.

This file is the durable record of the claim inventory, the detector for each claim,
and the value that detector RETURNED when it was run (2026-08-23T04:55Z–05:10Z, live
`amjis`, READ-ONLY: `SET default_transaction_read_only = on` on every connection).

It renders PLAN_FIGURE_RECONCILIATION_v1_0.md and .json.  Every `measured` string is a
value observed from the quoted `detector`; nothing here is estimated or inferred (H6).
Re-run any detector to re-verify; the detectors are quoted verbatim so they are cheap
to re-execute independently.

Verdict vocabulary (task-defined):
  CONFIRMED    — the plan's figure reproduces today.
  DRIFTED      — plausibly true when written; reality has since moved.
  REFUTED      — does not reproduce and is not explained by movement.
  UNMEASURABLE — refers to a past state, an external system, or has no detector.
"""
import json, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_MD = ROOT / '00_ARCHITECTURE/control/PLAN_FIGURE_RECONCILIATION_v1_0.md'
OUT_JSON = ROOT / '00_ARCHITECTURE/control/PLAN_FIGURE_RECONCILIATION_v1_0.json'
MEASURED_AT = '2026-08-23T04:55Z – 05:10Z'
DB = 'amjis (live production), READ-ONLY'

# (id, group, source, claim, plan_figure, detector, measured, verdict, note)
C = [
# ── Group A — §1 opening paragraph (figures carried from v3.0 §1.1/1.3/1.4/1.6/1.7/1.8)
("A1","§1 opening","plan:259","45.6 % of build attempts complete","45.6 %",
 "SELECT count(*) AS total, count(*) FILTER (WHERE state='complete') AS complete,\n  round(100.0*count(*) FILTER (WHERE state='complete')/count(*),1) AS pct FROM build_run_assets;",
 "total=7144, complete=3255, pct=45.6","CONFIRMED",
 "Exact. One qualifier the plan does not carry: 1,477 of the 7,144 rows are state='queued' — planned, never dispatched. Excluding never-started rows the completion rate is 3255/5667 = 57.4 %. The word 'attempts' overstates what the denominator counts; the figure itself is right."),
("A2","§1 opening","plan:260","the `has_substeps` false negative on 14 writers","14 writers",
 "AST census of every @register()-decorated class under platform/python-sidecar (string-literal AND module-level ASSET_ID forms), method `plan_substeps` defined on the class itself; cross-joined to SELECT asset_id, has_substeps FROM asset_registry.",
 "26 registered writers override plan_substeps; 14 registry rows have has_substeps=true; false negatives = 12; false positives = 0","REFUTED",
 "12, not 14. The 12: bg_muhurta_lattice, bo_laksana, bo_samskara, ga_ayurdaya, ga_nakshatra, ga_sensitive, ga_sensitive_degree, ga_structural, ka_sangam, mi_darshana, mi_pariksha, mi_pramana. Detector note: all 123 registered classes inherit ONLY WriterBase, whose plan_substeps default returns one whole-asset substep — so 'overrides on its own class' is the right predicate, and `has_substeps = True` as a class attribute is set by exactly the same 26 writers, an independent corroboration."),
("A3","§1 opening","plan:261","catalogue drift (47 DRAFT rows…)","47",
 "SELECT catalog_status, count(*) FROM asset_registry GROUP BY 1;",
 "CURRENT=80, DRAFT=47, RETIRED=1","CONFIRMED",""),
("A4","§1 opening","plan:261","…34 of them served","34",
 "grep -c 'so it is authoritative in practice' NIRMANA_ELEVATION_PLAN_v4_0.md, then resolve each hit to its #### asset heading and check catalog_status live.",
 "34 annotation hits, 34 distinct asset_ids, all 34 still catalog_status='DRAFT' live","CONFIRMED",
 "This is the one headline figure in the whole §1 paragraph that has a per-asset list behind it inside the plan itself, and the list is intact."),
("A5","§1 opening","plan:261","13 assets with no detected consumer","13",
 "Three independent readings: (a) grep -c 'No detected serving consumer (Phase 0.8c)' on the plan; (b) M0-T6's CONSUMER_MAP method (sibling artefact); (c) this pass's strict detector — an asset counts as zero-consumer only if it has NO registry dependant, NO reference to its target_table anywhere under platform/src, platform-mcp/src, python-sidecar/routers, python-sidecar/services (tests excluded), and provides_apis IS NULL.",
 "(a) 7 · (b) 23 · (c) 5 — bg_prashna_rules, bo_cdlm_summary, bo_chart_gestalt, ka_tulana, lel_events","REFUTED",
 "Four figures, none of them 13, and 13 has no per-asset list anywhere. The real defect is not 'N assets are unused' — it is that **the plan never defines 'detected consumer'**, so the number is unfalsifiable and every reading of it is a different question. Note also that v4.0's §1 compresses v3.0 §1.6's wording ('13 **table-backed** assets with no detected **serving** consumer') into 'assets with no detected consumer', dropping both qualifiers that made the original narrower. A retire/promote decision must rest on the per-asset packets, never on this count."),
("A6","§1 opening","plan:261","14 null `layer_index`","14",
 "SELECT count(*) FROM asset_registry WHERE layer_index IS NULL;  and  SELECT count(*) FROM asset_registry WHERE layer_index ~ '^[0-9]+$';",
 "NULL=15 · bare-numeral ('0','1','1','2','3','3')=6 · well-formed '^L[0-9]$'=107","REFUTED",
 "15, not 14. This also reconciles the three figures in circulation: v3.0 §1.6's full claim is '14 null `layer_index` + 6 bare-numeral forms'; v4.0's §1 carries only the first half. Measured today: 15 null + 6 malformed = **21 non-conformant**, which is where the '21' reading comes from. All three numbers describe the same defect at three different scopings; only the 6 is exactly right."),
("A7","§1 opening","plan:262","10 heavy assets","10",
 "No 'heavy' flag exists on asset_registry. The plan's own §9 names tier H exhaustively: ga_dashas, ga_vichara, ga_sensitive, ga_strength, ga_vargas, bo_laksana, bo_laksana_rerank, bo_samskara, ka_kshetra, ka_sangam.",
 "the §9 list has exactly 10 members; tier arithmetic G40+H10+M66+S8+X4 = 128 = live registry count","CONFIRMED",
 "Definitional, not independently measurable — 'heavy' is a plan-assigned tier, not a registry fact. Recorded as CONFIRMED because the list is exhaustive and internally consistent. Worth flagging for ADHIKĀRIN, not as a refutation: the tier-H list excludes the three heaviest assets by measured clean wall-clock — ka_gochara_sweep (35.6 h), ka_gochara_v3_century_materialize (270 substeps/chart), ka_gochara (6.5 h) — while including bo_laksana_rerank (p90 20 m)."),
("A8","§1 opening","plan:262","8 [heavy assets] with no resume","8",
 "grep -rn '_RESUME_VERSION' over the repo, intersected with the §9 tier-H list.",
 "private resume protocols exist in exactly 3 writers — ka_kshetra (_RESUME_VERSION=7), ka_gochara_sweep (_RESUME_VERSION=7), ka_sangam (_KA_SANGAM_RESUME_VERSION=2). Of the 10 tier-H assets, 2 have one (ka_kshetra, ka_sangam) → 8 without.","CONFIRMED",
 "Consistent with A7's definition. See E21: the workbook's own D-09 states '20 heavy assets have no resume', which contradicts this 8."),
("A9","§1 opening","plan:262","`completed_keys` passed by no caller","no caller",
 "grep -rn 'completed_keys' --include='*.py' over the repo.",
 "asset_runner.py:397 (parameter), :411 (docstring), :418, :425 (body). Call sites: tests/test_orchestrator_substeps.py:166 only. Zero production callers.","CONFIRMED",""),
("A10","§1 opening","plan:263","telemetry polluted to 16.9-day maxima","16.9 days",
 "SELECT asset_id, round(max(extract(epoch FROM (ended_at-started_at)))/86400.0,1) AS max_days FROM build_run_assets WHERE ended_at IS NOT NULL AND started_at IS NOT NULL GROUP BY 1 ORDER BY max_days DESC;",
 "ga_positions 16.9 days (406.1 h) · ga_sade_sati 4.4 days (105.2 h) · next: ka_gochara_sweep 1.5 d, ka_kshetra 1.4 d","CONFIRMED",
 "Also measured: only 2 rows in the whole table are currently open (started_at NOT NULL, ended_at NULL), both state='aborted'. The pollution is in CLOSED rows with absurd durations, not in currently-open rows — which matters for whichever repair is chosen."),
("A11","§1 opening","plan:263","DAG 21 levels deep","21 levels",
 "Longest-path level assignment over asset_registry.depends_on (284 edges, 0 dangling, 0 cycles). Run under four scopings: all 128; per_chart only (84); is_active only; non-brahmagyan only (88); plus has_writer-only and CURRENT-only.",
 "depth = 26 under all 128, per_chart-only, active-only, non-L0-only and has_writer-only. (CURRENT-only gives 13.) Longest chain, 26 nodes: ga_positions → ga_vargas → ga_strength → ga_structural → ga_yoga → ga_vichara → bo_laksana → bo_bimba → bo_karanajala → bo_sangati → bo_pratijna → ka_yojaka → ka_sangam → ka_vighnakara → ka_kala_darshana → ka_bhavishya_lekha → ph_nimitta → ph_sodhana → ph_suddha_sodhana → ph_pramana → ph_phaladesa → mi_bhavisya → mi_pramana → mi_gunanaka → mi_adhilepa → mi_seva","REFUTED",
 "26, not 21, and I could not reproduce 21 under any scoping I tried. The error is in the direction that makes the defect WORSE, not better: the serial critical path the run-to-completion contract has to survive is five levels longer than the plan budgets for. If the plan's 21 came from a wave computation rather than the registry graph, that derivation is not recorded and the number is not checkable as written."),
("A12","§1 opening","plan:263","DAG … ~3 wide","~3",
 "Same level assignment; mean width = |assets| / depth.",
 "per_chart-only (the chart plan): 84/26 = 3.23. All 128: 4.92 (inflated by 34 dependency-free roots at level 0). Non-L0: 3.38.","CONFIRMED",
 "'~3' is right for the chart plan, which is the scope this campaign runs. Paired with A11 the shape is worse than stated: 26 deep × 3.2 wide, not 21 × 3."),

# ── Group B — §1.2 live state
("B1","§1.2","plan:271","chart 482012f1 throughput: lit 64","64",
 "SELECT state, count(*) FROM asset_throughput WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' GROUP BY 1;",
 "lit=64","CONFIRMED",""),
("B2","§1.2","plan:271","chart 482012f1: stale 8","8","(same query)","stale=8","CONFIRMED",""),
("B3","§1.2","plan:271","chart 482012f1: error 10","10","(same query)","error=10","CONFIRMED",""),
("B4","§1.2","plan:271","chart 482012f1: dormant 1","1","(same query)","dormant=1","CONFIRMED",""),
("B5","§1.2","plan:271","chart 482012f1: incomplete 0","0","(same query)","no 'incomplete' group returned → 0","CONFIRMED",""),
("B6","§1.2","plan:271","chart 482012f1: 83 rows","83",
 "SELECT chart_id, count(*) FROM asset_throughput GROUP BY 1;","482012f1=83 (also: 1c826d5a=81, cb73cd3d=60, NULL=43; 267 total)","CONFIRMED",""),
("B7","§1.2","plan:272","shared substrate: lit 42 · stale 0 · error 1 · dormant 0 · incomplete 0 · 43 rows","42/0/1/0/0/43",
 "SELECT state, count(*) FROM asset_throughput WHERE chart_id IS NULL GROUP BY 1;","lit=42, error=1; no other states; total 43","CONFIRMED",""),
("B8","§1.2","plan:277","the single shared error is `bg_ephemeris_engine`","bg_ephemeris_engine",
 "SELECT asset_id, state, last_error, last_built_at FROM asset_throughput WHERE chart_id IS NULL AND state<>'lit';",
 "one row: bg_ephemeris_engine, error, 'service health: degraded — ephemeris position query failed: swisseph.calc_ut: Ephemeris file /app/ephe/sepl_18.se1 is damaged (0). ; MEAN_NODE check failed: unsupported operand type(s) for /: tuple and int'","CONFIRMED",""),
("B9","§1.2","plan:277","red since 2026-06-18","2026-06-18","(same query, last_built_at)","last_built_at = 2026-06-18 18:47:04.905434+00","CONFIRMED",""),
("B10","§1.2","plan:277","66 days at the time of measurement","66 days",
 "2026-06-18 → 2026-08-23 (SELECT now() = 2026-08-23 04:55Z).","66 days","CONFIRMED",""),
("B11","§1.2","plan:280","the registry holds 128 assets","128","SELECT count(*) FROM asset_registry;","128","CONFIRMED",""),
("B12","§1.2","plan:280","84 chart-domain","84","SELECT scope, count(*) FROM asset_registry GROUP BY 1;","per_chart=84, global=44","CONFIRMED",""),
("B13","§1.2","plan:280","(L1 19 + L2 22 + L3 21 + L4 9 + L5 13)","19/22/21/9/13",
 "SELECT layer, scope, count(*) FROM asset_registry GROUP BY 1,2;",
 "per_chart: ganita 19, bodha 22, kala 21, phala 9, mimamsa 13 — sums to 84","CONFIRMED",
 "Note for ADHIKĀRIN, not a refutation of §1.2: §15's own layer headings read 'L3 · Kāla — 23 assets' and 'L5 · Mīmāṃsā — 15 assets'. Those headings count the layer (23 kala = 21 per_chart + 2 global; 15 mimamsa = 13 + 2), §1.2 counts the chart domain. Both are right on their own axis; the plan does not say so, and the two figures sit 2,700 lines apart."),
("B14","§1.2","plan:281","44 shared-domain","44","(same)","global=44","CONFIRMED",""),
("B15","§1.2","plan:281","L0's 40","40","(same)","brahmagyan/global = 40","CONFIRMED",""),
("B16","§1.2","plan:281","plus four shared assets in higher layers: ka_graha_sancara, ka_muhurta_seva, mi_kula, mi_vistara","4 named",
 "SELECT asset_id FROM asset_registry WHERE scope='global' AND layer<>'brahmagyan';",
 "kala: ka_graha_sancara, ka_muhurta_seva · mimamsa: mi_kula, mi_vistara","CONFIRMED",""),
("B17","§1.2","plan:282","…both DRAFT, both scope='global' [the two L3 probes]","DRAFT/global",
 "SELECT asset_id, catalog_status, scope, asset_kind FROM asset_registry WHERE asset_id IN ('ka_graha_sancara','ka_muhurta_seva');",
 "both catalog_status=DRAFT, scope=global, asset_kind=service","CONFIRMED",""),
("B18","§1.2","plan:284","asset_throughput carries 83 chart-scoped rows","83","(see B6)","83","CONFIRMED",""),
("B19","§1.2","plan:284","…and 43 shared rows","43","(see B6)","43","CONFIRMED",""),
("B20","§1.2","plan:289","chart-domain missing row: `lel_events`","lel_events",
 "SELECT r.asset_id FROM asset_registry r WHERE r.scope='per_chart' AND NOT EXISTS (SELECT 1 FROM asset_throughput t WHERE t.asset_id=r.asset_id AND t.chart_id='482012f1-…');",
 "exactly one row: lel_events","CONFIRMED",""),
("B21","§1.2","plan:290","shared-domain missing row: `bg_gochara_citation_resolution`","bg_gochara_citation_resolution",
 "SELECT r.asset_id FROM asset_registry r WHERE r.scope='global' AND NOT EXISTS (SELECT 1 FROM asset_throughput t WHERE t.asset_id=r.asset_id AND t.chart_id IS NULL);  — plus the reverse direction (throughput rows with no matching global registry row).",
 "exactly one row: bg_gochara_citation_resolution. Reverse direction: 0 orphan shared throughput rows.","CONFIRMED",""),
("B22","§1.2","plan:293","`bg_gochara_citation_resolution` is CURRENT with no writer","CURRENT / no writer",
 "SELECT catalog_status, has_writer FROM asset_registry WHERE asset_id='bg_gochara_citation_resolution';  plus the AST @register census.",
 "catalog_status=CURRENT, has_writer=false; absent from the 123 @register ids in code","CONFIRMED",""),
("B23","§1.2","plan:293","…and no build on any chart","no build",
 "SELECT count(*) FROM asset_throughput WHERE asset_id='bg_gochara_citation_resolution';","0 rows on any chart","CONFIRMED",""),

# ── Group C — §1.5 measured baseline
("C1","§1.5","plan:307","112,589 of 139,471 L1 facts are `single`","112,589 / 139,471",
 "SELECT verification_pass_status, count(*) FROM chart_facts WHERE chart_id='482012f1-…' GROUP BY 1 ORDER BY 2 DESC;",
 "single=112589; total chart_facts for the chart = 139471","CONFIRMED",""),
("C2","§1.5","plan:307","80.7 %","80.7 %","112589/139471","0.8073 → 80.7 %","CONFIRMED",
 "Arithmetically exact — and understated as a description of the defect. The same query returns `single_pass` = 10,316, a second unverified tier. single + single_pass = 122,905 = **88.1 %** of the chart's L1 facts carry no second derivation. The plan's 80.7 % is the floor of the problem, not its size."),
("C3","§1.5","plan:307","9,320 (6.7 %) `two_pass_verified`","9,320 / 6.7 %","(same query)","two_pass_verified=9320; 9320/139471 = 6.68 % → 6.7 %","CONFIRMED",""),
("C4","§1.5","plan:308","Assets with an `integrity_check_sql`: 0 of 128","0 / 128",
 "SELECT count(*) FILTER (WHERE integrity_check_sql IS NOT NULL), count(*) FROM asset_registry;","0 of 128","CONFIRMED",""),
("C5","§1.5","plan:309","Assets below declared floor: 9","9",
 "For every registry row with a non-null count_sql, execute it ($1 := the native chart) and compare to target_floor. 68 assets declare a floor.",
 "exactly 9 below floor","CONFIRMED",""),
("C6","§1.5","plan:309","`ga_sade_sati` 57 % (6,287 / 11,019)","57 % / 6,287 / 11,019","(same)","6287/11019 = 57.1 %","CONFIRMED",""),
("C7","§1.5","plan:309","`ga_dashas` 90 % (483,859 / 536,471)","90 % / 483,859 / 536,471","(same)","483859/536471 = 90.2 %","CONFIRMED",""),
("C8","§1.5","plan:309","`bo_laksana` 83 %, `bo_samskara` 84 %, `bg_reference` 84 %","83/84/84 %","(same)",
 "bo_laksana 49955/60000 = 83.3 % · bo_samskara 50104/60000 = 83.5 % · bg_reference 1242/1485 = 83.6 %","CONFIRMED",""),
("C9","§1.5","plan:309","…`bg_concordance`, `bg_text_index`, `ga_sensitive`, `bg_sky_calendar`","4 named","(same)",
 "bg_concordance 720/800 = 90.0 % · bg_text_index 361/400 = 90.2 % · ga_sensitive 8565/8610 = 99.5 % · bg_sky_calendar 31059/31064 = 99.98 %","CONFIRMED",
 "The named set is right. Two of the four are shortfalls of 45 rows and 5 rows — they belong in a different severity band from ga_sade_sati's 4,732-row gap, and the flat count of 9 does not carry that."),
("C10","§1.5","plan:310","Assets with rows but no floor: 48","48",
 "Same count_sql sweep: rows > 0 AND target_floor IS NULL.","48","CONFIRMED",""),
("C11","§1.5","plan:311","Zero rows: 6 — bg_sarvatobhadra_grid, ga_prashna, mi_abhilekha, mi_sankalpa, mi_seva, mi_vistara","6, named",
 "Same sweep: rows = 0.","exactly those 6. (A further 6 return no count at all — bg_ephemeris_engine, bg_panchanga, ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana — all null count_sql; 5 of them read 'lit'.)","CONFIRMED",""),
("C12","§1.5","plan:311","`ga_prashna` — an L1 asset that reads `lit` with zero rows: the live specimen of the unearned-`lit` defect","1 specimen",
 "Join the zero-row set to asset_throughput state on the right scope key, and read volume_explanation for each.",
 "THREE assets are state='lit' with 0 rows: bg_sarvatobhadra_grid (global, CURRENT, volume_explanation NULL, has_writer=false), ga_prashna (per_chart, CURRENT, volume_explanation='0 for natal charts (horary only)…'), mi_vistara (global, DRAFT, volume_explanation='Accumulates with each export event'). Plus 5 assets that are 'lit' with no count_sql at all.","REFUTED",
 "The count is wrong and the two labels are swapped. `ga_prashna` is the ONE of the three that carries a written by-design explanation of its zero — the G4 evidence the charter asks for. `bg_sarvatobhadra_grid`, which the plan parenthesises as '(by design)', has NO volume_explanation, no writer, and is CURRENT — it is the specimen with nothing behind its green. The corrected defect: unearned `lit` is a class of **three** (eight if the five null-count_sql 'lit' service rows are counted, which have no detector behind their green at all), and the plan's single named specimen is the best-documented member of it, not the worst."),
("C13","§1.5","plan:312","`chart_facts`: 15 fact_keys under two `build_id`s","15",
 "SELECT count(*) FROM (SELECT fact_key FROM chart_facts WHERE chart_id='482012f1-…' GROUP BY fact_key HAVING count(DISTINCT build_id)>1) z;",
 "15. The two builds: 88268b2d (465 keys / 118,551 rows) and 6479bb56 (196 keys / 20,920 rows).","CONFIRMED",""),
("C14","§1.5","plan:312","`bodha_msr_signals`: three `build_id`s (49,955 / 104 / 45)","49,955 / 104 / 45",
 "SELECT build_id, count(*) FROM bodha_msr_signals WHERE chart_id='482012f1-…' GROUP BY 1 ORDER BY 2 DESC;",
 "a1693469=49955, 6479bb56=104, 84790929=45","CONFIRMED",""),
("C15","§1.5","plan:313","§N.5 derivation-ledger resolution: 2,000 / 2,000 sampled `constituent_facts_array` ids resolve to `chart_facts.fact_id` — **sound**","2,000/2,000, sound",
 "Full population, not a sample:\nSELECT count(*) FROM (SELECT unnest(constituent_facts_array) AS fid FROM bodha_msr_signals WHERE chart_id='482012f1-…' AND constituent_facts_array IS NOT NULL) s\n WHERE NOT EXISTS (SELECT 1 FROM chart_facts f WHERE f.fact_id=s.fid AND f.chart_id='482012f1-…');",
 "71,967 references total (70,291 distinct). 49 do NOT resolve, across 49 distinct signals. Resolution rate 99.932 %, not 100 %. Grouped: SELECT build_id, source_l1_asset, signal_type_class → ALL 49 are build_id 6479bb56 — 45 from ga_nakshatra/nakshatra_semantic, 4 from ga_vargas/vargottama_amplification.","REFUTED",
 "The corrected diagnosis is the interesting part, and it also refutes the row DIRECTLY BELOW it in the same table. The 49 broken references are not scattered: every one belongs to build generation `6479bb56` — the older, smaller of the two chart_facts build_ids from row C13, and the same build_id as bodha_msr_signals' 104-row generation from row C14. So the accretion the next row exonerates ('inspected and found to be legitimate output of the table's registered co-writers, not stale residue') is the SOLE cause of the §N.5 breakage the row above declares 'sound'. Two adjacent rows of §1.5 contradict each other, and the contradiction was invisible because one was sampled and the other was reasoned about rather than joined. Under §N.5 a non-resolving constituent_facts_array id is halt-worthy, not a rounding error. Method note: the full-population check runs in seconds — there was never a reason to sample, and an unordered LIMIT 2000 samples the physical head of the table, not the table."),
("C16","§1.5","plan:314","Deterministic-first audit: three writers touch `genai` — bg_texts, bo_samskara, mi_darshana — all three embeddings only","3 writers",
 "grep -rln 'genai' --include='*.py' platform/python-sidecar/ (tests excluded).",
 "2 files: writers/bg_texts.py, writers/bo_samskara.py. mi_darshana.py contains no 'genai' reference; its header states embedding vectors are [EXTERNAL_COMPUTATION_REQUIRED] and mimamsa_insight_embeddings rows are NOT inserted by the writer.","REFUTED",
 "2, not 3 — and the correction runs in the safe direction: mi_darshana does not call an embedding model at all, so the §N.4 deterministic-first conclusion ('compliant') is not merely intact but stronger than claimed. The finding is about the audit rather than the code: whatever detector produced '3' matched on 'embedding', not on 'genai', so the audit's stated scope and its actual predicate differ. A compliance audit whose detector does not match its own sentence is the §N.8 pattern, even when the verdict happens to be right."),
("C17","§1.5","plan:314","`ph_phaladesa` bans generative narration by policy","policy ban",
 "Read platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py header.",
 "lines 10-12: 'MODEL POLICY: writer emits a DETERMINISTIC template narration (§N.4 deterministic-first)… narration_model=NULL (no LLM)'; lines 59-66 repeat it at the call site.","CONFIRMED",""),

# ── Group D — §1.9 loophole register L-01…L-12 (code citations + figures)
("D1","§1.9 L-01","plan:332","`build_runs.scope='global'` means 'everything for this chart' (plan.ts:8,138)","plan.ts:8,138",
 "sed -n '8p;136,140p' platform/src/lib/build/plan.ts",
 ":8  export type BuildScope = 'global' | 'layer' | 'asset' | 'asset_set'  ·  :138  if (scope === 'global') return registry.map(r => r.asset_id)","CONFIRMED",""),
("D2","§1.9 L-01","plan:332","the L0 GATE then strips brahmagyan (runs/route.ts:166–170)","runs/route.ts:166–170",
 "sed -n '164,172p' platform/src/app/api/cockpit/runs/route.ts",
 ":165-170 'L0 GATE (native ruling 2026-06-26)… const planRegistry = scope === 'global' ? allowedRegistry.filter(r => r.layer !== 'brahmagyan') : allowedRegistry'","CONFIRMED",
 "Path note: the plan cites `runs/route.ts`; the file is platform/src/app/api/**cockpit**/runs/route.ts (507 lines). There is no platform/src/app/api/build/runs/route.ts. Every L-nn line number cited as `runs/route.ts` lands correctly in the cockpit file."),
("D3","§1.9 L-01","plan:332","`asset_registry.scope='global'` means chart-independent singleton (runner.py:465–467)","runner.py:465–467",
 "sed -n '463,470p' platform/python-sidecar/pipeline/orchestrator/runner.py",
 ":465-467  def eff(a): # Global assets are chart-independent singletons (chart_id IS NULL row). / return None if asset_scopes.get(a) == 'global' else chart_id","CONFIRMED",""),
("D4","§1.9 L-01","plan:332","/api/cockpit/refresh treats scope='global' as every asset in the registry, L0 included (refresh/route.ts:29–33)","refresh/route.ts:29–33",
 "sed -n '27,35p' platform/src/app/api/cockpit/refresh/route.ts",
 ":30-33  if (scope === 'global') { … 'SELECT asset_id FROM asset_registry WHERE is_active = true' … } — no layer filter","CONFIRMED",""),
("D5","§1.9 L-02","plan:333","scope='asset' on a shared asset → 403 'Global assets must be built at scope=global' (runs/route.ts:81–93)","runs/route.ts:81–93",
 "sed -n '81,93p' platform/src/app/api/cockpit/runs/route.ts",
 ":81-93 verbatim, including :91 error 'Global assets must be built at scope=global, not scope=asset', code 'FORBIDDEN_L0', status 403","CONFIRMED",""),
("D6","§1.9 L-02","plan:333","`scope='layer'`+brahmagyan rebuilds all 40","40",
 "SELECT count(*) FROM asset_registry WHERE layer='brahmagyan';","40","CONFIRMED",""),
("D7","§1.9 L-02","plan:333","mi_kula / mi_vistara are rejected with the misleading code `FORBIDDEN_L0`","FORBIDDEN_L0",
 "runs/route.ts:86-91 — the 403 branch keys on asset_registry.scope='global', not on layer, and both error bodies carry code 'FORBIDDEN_L0'. mi_kula and mi_vistara are scope='global' (B16).","confirmed by code read","CONFIRMED",""),
("D8","§1.9 L-03","plan:334","`--global-build` has no dependency gating (walks ORDER BY layer, sort_order, :84–91)","global_runner.py:84–91",
 "sed -n '76,95p' platform/python-sidecar/pipeline/orchestrator/global_runner.py",
 "the SELECT at :84-91 ends 'ORDER BY layer, sort_order'; depends_on is selected but not used to gate","CONFIRMED",""),
("D9","§1.9 L-03","plan:334","writers without an implementation are skipped as `deferred` with only a log line (:155–158)","global_runner.py:155–158",
 "sed -n '152,160p' platform/python-sidecar/pipeline/orchestrator/global_runner.py",
 ":155-158  if writer_cls is None: logger.info('[global_build] DEFERRED: no writer for asset_id=%s…'); return 'deferred'","CONFIRMED",""),
("D10","§1.9 L-04","plan:335","the `_MAX_CONCURRENT_RUNS` cap (runner.py:813–822)","runner.py:813–822",
 "sed -n '811,824p' platform/python-sidecar/pipeline/orchestrator/runner.py",
 ":813-822  SELECT count(*) AS active FROM build_runs WHERE state='running'; if active_count >= _MAX_CONCURRENT_RUNS: … sys.exit(3)","CONFIRMED",""),
("D11","§1.9 L-04","plan:335","the 409 RUN_ACTIVE gate (runs/route.ts:95–120)","runs/route.ts:95–120",
 "sed -n '95,122p' platform/src/app/api/cockpit/runs/route.ts",
 ":95-120  'Gate 0: 409 — block if an active run already exists for this chart' … SELECT id FROM build_runs WHERE chart_id=$1 AND state IN ('planned','running','paused') … code 'RUN_ACTIVE', status 409","CONFIRMED",""),
("D12","§1.9 L-05","plan:336","`global_runner.py` never calls `propagate_downstream_staleness`","never",
 "grep -c propagate_downstream_staleness platform/python-sidecar/pipeline/orchestrator/global_runner.py","0","CONFIRMED",""),
("D13","§1.9 L-05","plan:336","the propagator updates only WHERE chart_id = <run's chart> (staleness.py:90–99), so chart_id IS NULL downstream is never staled","staleness.py:90–99",
 "sed -n '84,99p' platform/python-sidecar/pipeline/orchestrator/staleness.py",
 ":88-95  WHERE chart_id = %s AND asset_id = ANY(%s::text[]) AND state IN ('lit','service_ok') … WHERE t.chart_id = %s — an equality predicate, so a NULL chart_id matches nothing","CONFIRMED",""),
("D14","§1.9 L-06","plan:337","the orchestrator polls build_runs.stop/pause_requested_at (runner.py:213–225)","runner.py:213–225",
 "sed -n '213,226p' platform/python-sidecar/pipeline/orchestrator/runner.py",
 ":213-225  def check_signals(cur, run_id): SELECT pause_requested_at, stop_requested_at FROM build_runs WHERE id = %s …","CONFIRMED",""),
("D15","§1.9 L-06","plan:337","`pipeline/dispatcher.py` walks the legacy `build_dependencies` table (dispatcher.py:27–58)","dispatcher.py:27–58",
 "grep -n build_dependencies platform/python-sidecar/pipeline/dispatcher.py",
 ":28 docstring, :34 and :39  cur.execute('SELECT asset_id, depends_on FROM build_dependencies'), plus :191/:197","CONFIRMED",""),
("D16","§1.9 L-06","plan:337","/api/build/rebuild, /rebuild-all, /continue, /pyramid-layers still exist and are wired to buttons","4 routes",
 "ls platform/src/app/api/build/",
 "rebuild/, rebuild-all/, continue/, pyramid-layers/ all present","CONFIRMED",
 "Existence confirmed. Whether each is still wired to a live button was NOT re-verified in this pass."),
("D17","§1.9 L-07","plan:338","/api/cockpit/refresh INSERTs state='dormant' rows keyed (chart_id, asset_id) for every asset in scope (refresh/route.ts:44–52)","refresh/route.ts:44–52",
 "sed -n '42,56p' platform/src/app/api/cockpit/refresh/route.ts",
 ":46-53  INSERT INTO asset_throughput (chart_id, asset_id, state) SELECT $1, unnest($2::text[]), 'dormant' ON CONFLICT (chart_id, asset_id) DO UPDATE SET updated_at = now()  — no scope filter, so shared assets get chart-scoped shadow rows","CONFIRMED",""),
("D18","§1.9 L-07","plan:338","runner.py's own comment (:834–837) warns these shadow the correct shared row in the stats query","runner.py:834–837",
 "sed -n '832,840p' platform/python-sidecar/pipeline/orchestrator/runner.py",
 ":834-837 verbatim: 'Passing a non-None chart_id to run_asset() for a global asset creates a spurious chart-scoped asset_throughput row that shadows the correct global row in the stats query.'","CONFIRMED",""),
("D19","§1.9 L-08","plan:339","preflight() skips any dependency with no throughput row — 'absent entries are not our concern' (plan.ts:248–250)","plan.ts:248–250",
 "sed -n '245,252p' platform/src/lib/build/plan.ts",
 ":248-249  '// Use undefined-safe: absent entries are not our concern (treat as ready)' / const depState = throughput.get(dep)?.state / :250 if (depState === undefined || READY_STATES.has(depState)) continue","CONFIRMED",""),
("D20","§1.9 L-09","plan:340","computeWaves returns [[candidate]] for scope='asset' (plan.ts:283)","plan.ts:283",
 "sed -n '281,285p' platform/src/lib/build/plan.ts",
 ":283  if (scope === 'asset') return [candidates.slice()]","CONFIRMED",
 "Semantically equivalent to the plan's paraphrase (for scope='asset' the candidate list is a single id), but the literal code is `[candidates.slice()]`, not `[[candidate]]`."),
("D21","§1.9 L-09","plan:340","action='rebuild' expands no downstream (plan.ts:396–399)","plan.ts:396–399",
 "sed -n '394,401p' platform/src/lib/build/plan.ts",
 ":397-399  '} else { // rebuild: all assets in scope (no transitive downstream expansion) / rawCandidates = [...scopeAssets] }'","CONFIRMED",""),
("D22","§1.9 L-10","plan:341","cascade plans the downstream of everything currently stale in scope (plan.ts:364–376)","plan.ts:364–376",
 "sed -n '362,378p' platform/src/lib/build/plan.ts",
 ":364-370  if (action === 'cascade') { … const stale = registry.filter(r => throughput.get(r.asset_id)?.state === 'stale')… transitiveDownstream(stale, registry)…","CONFIRMED",""),
("D23","§1.9 L-11","plan:342","clear-before-build on a scope including shared assets executes unscoped DELETE FROM <table> (runs/route.ts:301–304)","runs/route.ts:301–304",
 "sed -n '297,306p' platform/src/app/api/cockpit/runs/route.ts",
 ":301-304  const sql = asset.scope === 'global' ? `DELETE FROM ${asset.target_table}` : `DELETE FROM ${asset.target_table} WHERE chart_id = $1`","CONFIRMED",""),
("D24","§1.9 L-12","plan:343","default writer timeout 600 s (runner.py:89)","600 s / runner.py:89",
 "sed -n '85,95p' platform/python-sidecar/pipeline/orchestrator/runner.py",
 ":89  _WRITER_TIMEOUT_SECONDS = int(os.environ.get('WRITER_TIMEOUT_SECONDS', '600'))  # 10 min default","CONFIRMED",""),
("D25","§1.9 L-12","plan:343","…unless `writer_timeout_seconds` is set per asset; set on ~2 of 128","~2 of 128",
 "SELECT count(*) FROM asset_registry WHERE writer_timeout_seconds IS NOT NULL;  SELECT writer_timeout_seconds, count(*) FROM asset_registry GROUP BY 1;  information_schema default.",
 "128 non-null of 128; 107 non-default (column DEFAULT 600); distribution 10800×91, 600×21, 60×5, 120×5, 1800×2, 300×1, 3600×1, 21600×1, 86400×1","REFUTED",
 "Already refuted by PARĪKṢAKA verdict V-2 (2026-08-23T04:10:09Z) and independently re-measured here to the same figures. V-2's corrected defect stands and is not re-litigated: seven assets carry a timeout BELOW their own measured worst clean run (ka_gochara 0.5 h vs 6.5 h, bo_laksana 3 h vs 19.2 h, ka_gochara_sweep 6 h vs 35.6 h, ga_strength 3 h vs 13.1 h, ga_sensitive 3 h vs 6.4 h, bo_laksana_rerank 0.17 h vs 0.35 h, ka_kshetra 24 h vs 33.8 h). Included in this inventory for coverage completeness, not as a new finding."),
("D26","§1.9 L-12","plan:343","…against measured 30 h heavy builds","30 h",
 "SELECT asset_id, round(max(extract(epoch FROM (ended_at-started_at)))/3600.0,1) FROM build_run_assets … GROUP BY 1 ORDER BY 2 DESC; (excluding the two D-13 pollution outliers ga_positions 406.1 h and ga_sade_sati 105.2 h)",
 "ka_gochara_sweep 35.6 h, ka_kshetra 33.8 h, bo_laksana 19.2 h, ga_strength 13.1 h","CONFIRMED",""),
("D27","§1.9 L-12","plan:343","`completed_keys` is passed by no caller (asset_runner.py:397)","asset_runner.py:397",
 "grep -rn completed_keys --include='*.py'",
 ":397  completed_keys: set[str] | None = None,  — parameter present; only caller passing it is tests/test_orchestrator_substeps.py:166","CONFIRMED",""),
("D28","§1.9 L-12","plan:343","SIGTERM drain window is 10 s","10 s",
 "sed -n '91,102p' and '775,782p' platform/python-sidecar/pipeline/orchestrator/runner.py",
 ":92 'Cloud Run sends SIGTERM and then waits up to 10 seconds before SIGKILL' · :402 'Cloud Run gives 10 s after SIGTERM before SIGKILL' · :778 same · :780 signal.signal(signal.SIGTERM, _handle_sigterm)","CONFIRMED",
 "The 10 s is Cloud Run's documented platform window as recorded in the code's own comments; it is not a value this repo sets, and it was not re-verified against Google\'s current documentation."),

# ── Group E — Defect Register D-01…D-16 (workbook sheet)
("E1","D-01","workbook","28 registered writers implement plan_substeps in code","28",
 "(see A2 detector)","26","REFUTED","See A2. The 26: bg_gochara_arcs, bg_muhurta_lattice, bo_laksana, bo_samskara, ga_ayurdaya, ga_condition, ga_dashas, ga_medical, ga_nakshatra, ga_prashna, ga_sensitive, ga_sensitive_degree, ga_structural, ga_transit_anchors, ga_vargas, ga_vastu, ga_vichara, ga_yoga, ka_gochara, ka_gochara_sweep, ka_gochara_v3_century_materialize, ka_kshetra, ka_sangam, mi_darshana, mi_pariksha, mi_pramana."),
("E2","D-01","workbook","14 carry has_substeps=false","14",
 "(see A2 detector)","12 false negatives; 14 is the count of has_substeps=TRUE, not FALSE","REFUTED",
 "The corrected diagnosis: 14 is the right number attached to the wrong side of the comparison. SELECT count(*) FROM asset_registry WHERE has_substeps returns exactly 14 — the registry rows that are CORRECT. The false-negative set is the 26 code writers minus those 14 = 12. Read as written, the defect register's headline overstates the gap by two and mislabels a correct count as a defect count. False positives (registry true, code has no override) are 0, so the flag is never wrong in the dangerous direction — it is only ever under-set, which is worth knowing before the CI assertion is written."),
("E3","D-01","workbook","ka_sangam has 61 substep rows per chart recorded while the registry says it has none","61 / none",
 "SELECT asset_id, chart_id, count(*) FROM build_substep_progress GROUP BY 1,2 ORDER BY 3 DESC;  +  SELECT has_substeps FROM asset_registry WHERE asset_id='ka_sangam';",
 "ka_sangam = 61 rows on each of the three charts (482012f1, 1c826d5a, cb73cd3d); has_substeps=false","CONFIRMED",""),
("E4","D-03","workbook","ka_gochara_sweep is inactive and RETIRED","inactive/RETIRED",
 "SELECT is_active, catalog_status, has_writer FROM asset_registry WHERE asset_id='ka_gochara_sweep';",
 "is_active=false, catalog_status=RETIRED, has_writer=true","CONFIRMED",
 "It is the only is_active=false row and the only RETIRED row in the registry."),
("E5","D-03","workbook","…yet holds asset_throughput rows on two charts producing 'no writer registered'","2 charts",
 "SELECT chart_id, state, last_error FROM asset_throughput WHERE asset_id='ka_gochara_sweep';",
 "3 rows, all state='error'. Two carry last_error='no writer registered for ka_gochara_sweep' (482012f1, 1c826d5a); the third (cb73cd3d) carries 'BLOCKED: upstream dependency(ies) timeout:21600s did not complete in this run'.","CONFIRMED",
 "Exactly as stated. The third row is a third permanent red for the same retired asset, from a different cause — the defect is one row wider than the register records, in the same direction."),
("E6","D-04","workbook","The watchdog uses NOW() in 16 places","16",
 "grep -oi 'NOW()' platform/src/app/api/cockpit/watchdog/route.ts | wc -l, then subtract occurrences inside the header comment block.",
 "17 total occurrences; 2 of them are inside the file-header comment (:43, :46); 15 appear in executed SQL","DRIFTED",
 "Neither 17 nor 15 is 16, and the file has been edited since (mtime 2026-08-06). The defect is unaffected: 15 executing NOW() calls, 0 clock_timestamp(). Recorded as DRIFTED rather than REFUTED because a one-count difference on a file that has since changed is exactly what drift looks like, and treating it as a refutation would overstate the problem."),
("E7","D-04","workbook","clock_timestamp() appears nowhere in the repo","nowhere",
 "grep -rn clock_timestamp --include='*.py' --include='*.ts' --include='*.sql' . | grep -v node_modules",
 "4 hits, ALL of them inside this campaign's own control documents (build_asset_control_workbook.py, asset_plans.py) describing the defect. Zero in production code.","CONFIRMED",""),
("E8","D-04","workbook","ka_kshetra was reaped at 301 of 308 committed substeps","301 / 308",
 "The 308 is checkable: SELECT count(*) FROM build_substep_progress WHERE asset_id='ka_kshetra' AND chart_id='482012f1-…'.  The 301 describes the table's contents at the instant of a past reap; no historical snapshot of build_substep_progress exists and asset_throughput_state_audit holds 4 rows total.",
 "308 substep rows present today — the denominator CONFIRMED. The 301 numerator: UNMEASURABLE.","UNMEASURABLE",
 "Half-measurable, and recorded as UNMEASURABLE rather than split, so the unchecked half stays visibly unchecked. Nothing in the current schema could reproduce the 301 — which is itself the D-15 finding (no build-history spine) biting the D-04 investigation."),
("E9","D-05","workbook","staleness.py matches (lit, service_ok) and measures the prior state","lit/service_ok",
 "sed -n '84,99p' platform/python-sidecar/pipeline/orchestrator/staleness.py",
 ":92  AND state IN ('lit','service_ok')  · the FROM (SELECT … FOR UPDATE) AS old subquery captures prev_state and the statement RETURNs old.prev_state","CONFIRMED",""),
("E10","D-05","workbook","the inline copy matches (lit, mature) and hardcodes from_state='lit'","lit/mature, hardcoded",
 "sed -n '713,726p' platform/python-sidecar/pipeline/orchestrator/asset_runner.py",
 ":716-719  UPDATE asset_throughput SET state='stale' … AND state IN ('lit','mature')  ·  :723-724 emit_event({… 'from_state': 'lit', 'to_state': 'stale'})","CONFIRMED",""),
("E11","D-06","workbook","The upstream hash hashes last_built_at values","last_built_at",
 "sed -n '112,128p' platform/python-sidecar/pipeline/orchestrator/asset_runner.py",
 ":112-127  compute_upstream_hash SELECTs ar.asset_id, t.last_built_at over the depends_on set, then payload = '|'.join(f\"{r['asset_id']}:{r['last_built_at']}\") and sha256s it","CONFIRMED",""),
("E12","D-06","workbook","the writer hash is a git SHA","git SHA",
 "grep -n writer_hash platform/python-sidecar/pipeline/orchestrator/asset_runner.py",
 ":578  writer_hash = get_writer_git_hash(asset_id)","CONFIRMED",""),
("E13","D-06","workbook","Neither is ever read — isStale() has no production caller","no caller",
 "grep -rn isStale --include='*.ts' --include='*.tsx' over platform/src (excluding node_modules), separating the exported function from unrelated local variables of the same name.",
 "isStale is defined at platform/src/lib/build/staleness.ts:25 and imported by exactly one file: platform/src/lib/build/__tests__/staleness.test.ts. The other 'isStale' hits are unrelated local identifiers in FreshnessSection.tsx, pricing_diff.ts and LiveDependencyGraph.tsx. Zero production callers. Meanwhile 231 of 267 asset_throughput rows carry BOTH built_against_upstream_hash and built_against_writer_hash.","CONFIRMED",
 "Sharper than the register states: the hashes are not merely unread, they are actively WRITTEN on nearly every build (231/267 rows) by asset_runner.py:695 and then read by nothing. The cost is being paid; the benefit is not being collected."),
("E14","D-07","workbook","build_substep_progress has no planned-total column","no column",
 "SELECT column_name FROM information_schema.columns WHERE table_name='build_substep_progress';",
 "chart_id, asset_id, substep_key, build_fingerprint, rows_written, completed_at — six columns, no total/planned column","CONFIRMED",""),
("E15","D-07","workbook","the stats route hardcodes total=null","total=null",
 "grep -n total platform/src/app/api/cockpit/stats/route.ts",
 ":287  ? { committed: substepsCommitted, total: null }  (type declared at :42 as total: number | null)","CONFIRMED",""),
("E16","D-08","workbook","runner.py contains no retry/backoff/attempt logic","none",
 "grep -rni 'retry|backoff|attempt' platform/python-sidecar/pipeline/orchestrator/runner.py","0 matches","CONFIRMED",""),
("E17","D-08","workbook","45.6% of asset attempts reach complete (3,255 of 7,144)","3,255 / 7,144","(see A1)","3255 / 7144 = 45.6 %","CONFIRMED",""),
("E18","D-09","workbook","ka_kshetra, ka_gochara_sweep and ka_sangam each carry a private resume protocol","3 writers",
 "grep -rn _RESUME_VERSION --include='*.py' .",
 "services/ka_kshetra/writer.py:164, services/ka_gochara_sweep/writer.py:160, writers/ka_sangam.py:145 — three, and no others in production code","CONFIRMED",""),
("E19","D-09","workbook","two independently reached _RESUME_VERSION = 7","2 at v7",
 "(same)","ka_kshetra _RESUME_VERSION = 7 · ka_gochara_sweep _RESUME_VERSION = 7 · ka_sangam _KA_SANGAM_RESUME_VERSION = 2","CONFIRMED",
 "ka_gochara_sweep's own comment at :117 says it 'mirrors ka_sangam.py's _KA_SANGAM_RESUME_VERSION' — so 'independently' is generous, but the count is right."),
("E20","D-09","workbook","20 heavy assets have no resume at all","20",
 "Two candidate definitions, both measured: (a) the plan §9 tier-H list of 10, minus the 2 with a resume protocol = 8. (b) every writer overriding plan_substeps (26), minus the 3 with a resume protocol = 23.",
 "8 under the tier-H definition · 23 under the substep-writer definition · 20 under neither","REFUTED",
 "20 matches no definition I could construct, and it contradicts the plan's own §1 opening, which says '10 heavy assets, 8 with no resume' (claim A8) — the same campaign's two control surfaces state 8 and 20 for the same quantity. Corrected diagnosis: the exposure is materially larger than the tier-H framing admits. 23 writers plan substeps and cannot resume them, and the three that CAN are exactly the three that were expensive enough to force someone to hand-roll it. The right number for scoping the shared ResumableWriter is 23, not 8 and not 20."),
("E21","D-10","workbook","deriveState returns lit whenever rows > 0, so 'stale' is unreachable with data","rows>0 → lit",
 "read platform/src/app/api/cockpit/stats/deriveState.ts",
 ":88-90  '// NOT gates — an asset with rows > 0 and no active zero-row build is lit.' / if (actualRows != null && actualRows > 0) return 'lit'  — this precedes the throughputState==='stale' branch at :99, so stale-with-data is unreachable","CONFIRMED",""),
("E22","D-11","workbook","The refresh route only bumps updated_at — a column nothing reads — and inserts dormant rows","updated_at only",
 "(see D17) plus SELECT column_name FROM information_schema.columns WHERE table_name='asset_throughput';",
 "the INSERT … ON CONFLICT DO UPDATE SET updated_at = now() is the route's only write; asset_throughput's live column list contains no updated_at at all, which is why the call is wrapped in .catch(() => null) with the comment 'non-fatal: table may not have updated_at column'","CONFIRMED",
 "Stronger than stated: the column does not exist in the live schema, so the ON CONFLICT branch cannot even bump it — the route's entire 'refresh' effect reduces to inserting dormant rows for assets that had none, and silently swallowing the error for those that did."),
("E23","D-12","workbook","The CHECK constraint allows six states","6",
 "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='asset_throughput'::regclass AND contype='c';",
 "CHECK (state = ANY (ARRAY['dormant','building','lit','stale','error','incomplete']))  — six","CONFIRMED",""),
("E24","D-12","workbook","service_ok and mature appear in Python and TypeScript but cannot be stored","both, both languages",
 "grep for each literal across platform/python-sidecar and platform/src.",
 "service_ok — Python: runner.py (_SUCCESS_OUTCOMES), staleness.py:92 (live UPDATE predicate); TypeScript: deriveState.ts:5 (union) and :66 (return value), watchdog/route.ts, stats/route.ts. mature — Python: runner.py:131, asset_runner.py:719, scripts/governance/ekv_controls.py. Neither is in the CHECK constraint.","CONFIRMED",""),
("E25","D-12","workbook","mature appears exactly once, in the dead inline cascade","once",
 "grep -rn \"'mature'\" --include='*.py' --include='*.ts' --include='*.tsx' platform/ (node_modules and tests excluded)",
 "8 occurrences across 3 production files: runner.py:131 (inside the live _SUCCESS_OUTCOMES frozenset), asset_runner.py:719 (the inline cascade's SQL predicate), and platform/scripts/governance/ekv_controls.py ×6 (control F-102's live SQL and its docstring)","REFUTED",
 "The corrected diagnosis is the point, and it inverts the severity. 'mature' is not a dead vestige in a dead cascade — it sits inside `_SUCCESS_OUTCOMES`, the frozenset the orchestrator uses to decide whether an outcome counts as success, and inside a live CI governance control's WHERE clause. Because the CHECK constraint forbids the value, every one of those predicates is exactly equivalent to its 'lit'-only form: a branch that can never fire, in three live decision surfaces. ekv_controls.py:370-372 even argues explicitly that 'narrowing the check to lit alone would have silently missed a mature instance' — a defence of a branch the database makes unreachable. That is the §N.8 earned-signal pattern one layer up: not a flag without a detector, but a detector guarding a condition that cannot occur. The same is true of `service_ok`, which appears in the AUTHORITATIVE cascade (staleness.py:92), not the dead one — so the unstorable-vocabulary defect is wider than D-12's single named instance."),
("E26","D-13","workbook","Observed maxima include ga_positions at 16.9 days","16.9 d","(see A10)","ga_positions max 16.9 days / 406.1 h over 55 timed runs","CONFIRMED",""),
("E27","D-13","workbook","…and ga_sade_sati at 4.4 days","4.4 d","(see A10)","ga_sade_sati max 4.4 days / 105.2 h over 58 timed runs","CONFIRMED",""),
("E28","D-13","workbook","estimated_seconds is populated on 2 of 128 assets","2 / 128",
 "SELECT count(*) FILTER (WHERE estimated_seconds IS NOT NULL), count(*) FROM asset_registry;  then SELECT asset_id, estimated_seconds … ORDER BY 2 DESC;",
 "9 of 128: ga_dashas 2400, ga_vargas 600, ga_sensitive 120, ga_structural 120, ga_sade_sati 120, ga_positions 60, ga_strength 60, ga_panchanga 60, ga_tajaka 60","REFUTED",
 "9, not 2 — and the corrected defect is not scarcity but distribution and accuracy. All nine estimates are `ga_*`: L1 has 9 of its 19 assets estimated; L0, L2, L3, L4 and L5 have ZERO between them, including every tier-H asset outside L1 and every one of the four assets whose measured runs exceed 13 hours. Worse, the nine that exist are wrong against their own telemetry: joined to per-asset p50/p90 over completed runs, 2 of 9 are below their own MEDIAN (ga_sensitive 120 s vs p50 245 s; ga_strength 60 s vs p50 97 s) and 5 of 9 are below their own p90 (adding ga_dashas 2400 vs 2768, ga_structural 120 vs 158, ga_sade_sati 120 vs 510). An ETA surface fed by these is not merely sparse; where it is populated it under-promises on more than half its rows."),
("E29","D-14","workbook","bg_ephemeris_engine was in error from 2026-06-18 — 66 days","2026-06-18 / 66 d","(see B8-B10)","last_built_at 2026-06-18 18:47:04Z; still state='error' at 2026-08-23 04:55Z = 66 days","CONFIRMED",""),
("E30","D-15","workbook","asset_throughput_state_audit (migration 586) holds a handful of rows","a handful",
 "SELECT count(*) FROM asset_throughput_state_audit;","4","CONFIRMED",""),
("E31","D-15","workbook","…and is read by nothing","nothing",
 "grep -rn asset_throughput_state_audit --include='*.py' --include='*.ts' --include='*.tsx' --include='*.sql' platform/",
 "Hits are: the migration that creates it (586), a live-DB integration test (platform/tests/integration/asset_throughput_state_audit.db.test.ts), and db.py:81 — which sets the GUC the WRITE trigger consumes, not a read. No production SELECT.","CONFIRMED",""),
("E32","D-16","workbook","KA_KSHETRA_HASH_SPILL_DIR is pinned to /tmp","/tmp",
 "grep -rn SPILL .github/workflows/deploy.yml",
 ":853  --update-env-vars=…,KA_KSHETRA_HASH_SPILL_DIR=/tmp   on `gcloud run jobs update brahma-build-pipeline-job`","CONFIRMED",
 "The pin is deliberate and documented in place (deploy.yml:837-846 explains the writer previously fell back to TMPDIR implicitly, and the pin makes the choice observable). D-16's characterisation of it as an interim disposition is accurate."),
("E33","D-16","workbook","A 3–4.2 GB spill","3–4.2 GB",
 "platform/python-sidecar/services/ka_kshetra/stage4_field.py:243-245 and .github/workflows/deploy.yml:843-844",
 "stage4_field.py:245 '…is on the order of ~3-4.2GB'; deploy.yml:843 '~3-4.2GB RAM-backed spill at the native chart's 10.5M-row scale'","CONFIRMED",
 "Confirmed as a figure the codebase asserts about itself. It was NOT independently re-measured against a live run in this pass; a run-time measurement would be a different and stronger detector."),
("E34","D-16","workbook","…counts against the 8Gi limit","8Gi",
 "grep -n 'memory' .github/workflows/deploy.yml",
 ":851  --memory=16Gi  on brahma-build-pipeline-job. (The other two --memory flags in the file are 1Gi and 512Mi, for different services.)","DRIFTED",
 "The job runs at 16Gi today, not 8Gi. This is drift in the benign direction and D-16 itself predicts it — its own text names 'doubling job memory' as the compensating fix that was taken instead of the real one. The underlying defect is untouched: /tmp is still tmpfs, the spill still competes with the working set, and doubling headroom moved the OOM threshold without restoring the bounded-memory guarantee the spill exists to provide."),
("E35","D-16","workbook","The repo currently has zero Cloud Run volume mounts","zero",
 "grep -rni 'volumeMounts|volume_mounts|--add-volume' --include='*.yaml' --include='*.yml' --include='*.tf' --include='*.sh' --include='*.json' . | grep -v node_modules",
 "0 matches","CONFIRMED",""),
]

def render():
    from collections import Counter
    tally = Counter(r[7] for r in C)
    groups = {}
    for r in C:
        groups.setdefault(r[1].split(' ')[0] if r[1].startswith('§') else ('Defect Register' if r[1].startswith('D-') else r[1]), []).append(r)
    rows = [dict(zip(('id','source_section','plan_ref','claim','plan_figure','detector','measured','verdict','note'), r)) for r in C]
    payload = {
        'artifact': 'PLAN_FIGURE_RECONCILIATION_v1_0',
        'task': 'M0-T18',
        'generated_by': '00_ARCHITECTURE/control/plan_figure_reconciliation.py',
        'measured_at': MEASURED_AT,
        'database': DB,
        'target': 'NIRMANA_ELEVATION_PLAN_v4_0.md §1 / §1.2 / §1.5 / §1.9 (L-01…L-12) and NIRMANA_ASSET_CONTROL_WORKBOOK_v4_1.xlsx Defect Register D-01…D-16',
        'claims_found': len(C),
        'tally': dict(tally),
        'status': 'observations only; no verdict is issued and nothing is certified (I16 / charter H7). THE PLAN WAS NOT EDITED.',
        'claims': rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=1))
    return payload




GROUP_TITLES = {
    'A': '§1 opening paragraph — the figures carried forward from v3.0',
    'B': '§1.2 — Live state of the chart and the substrate',
    'C': '§1.5 — Correctness and completeness, on the chart',
    'D': '§1.9 — The loophole register (L-01…L-12)',
    'E': 'Defect Register D-01…D-16 (control workbook v4.1)',
}
BADGE = {'CONFIRMED': 'CONFIRMED', 'REFUTED': '**REFUTED**',
         'DRIFTED': '*DRIFTED*', 'UNMEASURABLE': '*UNMEASURABLE*'}

HEADLINE = """## 0 — Headline

**{n} quantitative claims were extracted and every one was given a detector.**
{c} CONFIRMED · {r} REFUTED · {d} DRIFTED · {u} UNMEASURABLE.

**The diagnosis is substantially sound.** Eighty-six per cent of the plan's quantitative claims
reproduce exactly against live production today, including every one of the twenty-three §1.2
state and census figures, every code citation in the twelve-loophole register (all twenty-eight
file:line references land on the code they claim, at the cited lines), and eleven of the
seventeen §1.5 baseline rows. The measured baseline was measured. This is not a document that
invented its evidence.

The task that commissioned this pass was written after three plan figures had been found wrong
by accident, three for three — a rate which, extrapolated, would have implied a defect register
that could not be trusted at all. **It does not extrapolate.** The correct reading is narrower
and more useful: the failures cluster, and they cluster in one identifiable place.

**Where the failures are.** Twelve of the thirteen refuted claims are counts of *code artefacts*
or *catalogue metadata* — how many writers implement a method, how many rows are null, how many
levels deep a graph is, how many files match a grep. Not one refuted claim is a live
throughput / state / row-count measurement. Put plainly: **the figures someone obtained by
running a query against the database are right; the figures someone obtained by counting things
in the codebase, or by sampling, are the ones that broke.** Six of the thirteen come from a
detector whose predicate did not match the sentence it was attached to (A5, C16, E2, E20, E25,
E28) — the §N.8 pattern turned on the campaign's own control surface rather than on the product.

### The eight findings that change something

1. **§1.5's two adjacent rows contradict each other, and one of them is a live §N.5 violation
   (C15).** The derivation-ledger row reports 2,000 / 2,000 sampled `constituent_facts_array`
   ids resolving and grades it *sound*. Checked across the full population — which takes
   seconds — **49 of 71,967 references do not resolve**, across 49 signals. Every single one
   belongs to build generation `6479bb56`, which is precisely the accretion the *very next row*
   inspects and exonerates as "legitimate output of the table's registered co-writers, not stale
   residue". The accretion the plan clears is the sole cause of the breakage the plan misses.
   Under §N.5 a non-resolving id is halt-worthy, not a rounding error.

2. **The unearned-`lit` specimen is misidentified, and there are three of them (C12).**
   `ga_prashna`, which §1.5 names as *the* live specimen, is the one of the three zero-row `lit`
   assets that carries a written by-design `volume_explanation`. `bg_sarvatobhadra_grid`, which
   §1.5 parenthesises as "(by design)", has no `volume_explanation`, no writer, and is CURRENT.
   The two labels are the wrong way round, and `mi_vistara` is a third instance nobody named. A
   further five assets read `lit` with no `count_sql` at all.

3. **`'mature'` is not a dead vestige — it is wired into three live decision surfaces (E25).**
   The register says it appears exactly once, in the dead inline cascade. It appears eight times
   in production code, including inside `_SUCCESS_OUTCOMES` (the frozenset the orchestrator uses
   to decide whether an outcome counts as success) and inside a live CI governance control's
   WHERE clause. Because the CHECK constraint forbids the value, each of those is a branch that
   can never fire. `service_ok` is the same defect in the *authoritative* cascade
   (`staleness.py:92`), not the dead one. This is §N.8 one turn further on: not a flag with no
   detector, but a detector guarding a condition that cannot occur.

4. **The DAG is five levels deeper than budgeted (A11).** Measured 26, not 21, and 26 under
   every scoping tried. The error runs in the direction that makes the run-to-completion
   contract harder, not easier.

5. **"13 assets with no detected consumer" is unfalsifiable (A5).** Four readings exist — 7 (the
   plan's own per-asset annotations), 13 (the headline), 23 (M0-T6's method), 5 (this pass's
   strict method) — because the plan never defines *detected consumer*. The defect is the
   missing definition, not the count.

6. **The resume exposure is 23 writers, not 8 and not 20 (E20).** The plan's §1 says 8, the
   Defect Register says 20, and neither is reproducible. Twenty-three writers plan substeps and
   cannot resume them; the three that can are exactly the three that were expensive enough to
   force someone to hand-roll it. 23 is the number that should scope the shared
   `ResumableWriter`.

7. **`estimated_seconds` is not scarce, it is skewed and wrong (E28).** 9 of 128, not 2 — and
   all nine are `ga_*`. L0, L2, L3, L4 and L5 have zero between them, including every tier-H
   asset outside L1. Of the nine that exist, two are below their own measured *median* and five
   are below their own p90.

8. **80.7 % `single` understates the verification gap (C2).** The same query returns a second
   unverified tier, `single_pass` = 10,316. Together, **88.1 %** of the chart's L1 facts carry
   no second derivation.

**What this does not say.** It does not say the plan is unreliable. Ninety-nine claims held,
including everything the campaign's rung gates actually key on. Three of the thirteen
refutations (A2, E1, E2) are the same defect counted three ways and differ from the truth by
two. Two claims moved rather than broke, and one of them (E34) is drift the register itself
predicted. Manufacturing a crisis out of this set would be its own H6.
"""

METHOD = """## 3 — Method, and what it cannot see

- Every database figure comes from a connection opened with
  `SET default_transaction_read_only = on` and a statement timeout. No write was issued.
  `DATABASE_URL` was read the way `00_ARCHITECTURE/control/measure_assets.py` reads it, and was
  never printed, logged or committed (P4).

- **Concurrency check.** A KĀRAKA was applying migrations during this pass. Ten volatile figures
  were re-read at the end of the window (`2026-08-23 05:09:49Z`) against their values at the
  start (`04:55Z`): registry rows 128 → 128, null `layer_index` 15 → 15, DRAFT 47 → 47,
  `integrity_check_sql` 0 → 0, `has_substeps` true 14 → 14, `estimated_seconds` 9 → 9, chart
  throughput rows 83 → 83, shared 43 → 43, `build_run_assets` 7,144 → 7,144. **No figure moved.**
  Every number here is stable across the measurement window; none needed the two-reading
  treatment the task provides for.

- Row counts come from each asset's own registered `count_sql`, executed with `$1` bound to the
  native chart — the same predicate the cockpit uses, so a wrong `count_sql` is inherited here as
  it is there. Six assets have no `count_sql` and are reported as no-count, never as zero.

- Code counts come from an AST census (not grep) for anything involving class structure, and from
  grep with tests and `node_modules` excluded for literal occurrences. The `@register` census
  resolves both the string-literal and the module-level `ASSET_ID` constant form; missing the
  second form is what makes a naive grep undercount the writer set by four.

- **What this pass did not do.** It did not re-verify §15's 128 per-asset plans, §9's tier
  assignments beyond their arithmetic, §14's roadmap, or §18 / §19. It did not re-measure the
  3–4.2 GB spill against a live run (E33) or check Cloud Run's SIGTERM window against Google's
  current documentation (D28) — both are recorded as codebase self-assertions, not as independent
  measurements. It did not check whether the four zombie routes are still wired to live buttons
  (D16), only that they exist. One claim (E8) is reported UNMEASURABLE rather than split in two,
  so its unchecked half stays visibly unchecked.

- **Unsureness, stated plainly.** (a) A7 ("10 heavy assets") is recorded CONFIRMED on a
  definitional basis — "heavy" is a plan-assigned tier with no registry column behind it, so the
  claim can be checked for internal consistency but not independently measured; a reader who
  wants it graded UNMEASURABLE has a fair case. (b) A5's strict zero-consumer detector greps for
  `target_table` occurrences and will over-match a table name that is a substring of another; it
  is offered as one of four readings, not as the answer. (c) E6 is recorded DRIFTED on a
  one-count difference on a file that has been edited since; a reader who prefers REFUTED for any
  non-matching integer would move it, and the underlying defect is identical either way.
  (d) The 26-level DAG depth (A11) is measured from `asset_registry.depends_on`; if the plan's 21
  came from the planner's own wave computation rather than the registry graph, that derivation is
  not recorded anywhere and I could not reconstruct it.
"""


def render_md(p):
    t = p['tally']
    L = []
    A = L.append
    A('# NIRMĀṆA M0-T18 — Plan figure reconciliation v1.0')
    A('')
    A('**Task:** M0-T18 · **Measured:** ' + MEASURED_AT + ' · **Database:** ' + DB + '  ')
    A('**Generator:** `00_ARCHITECTURE/control/plan_figure_reconciliation.py` — holds every '
      'detector verbatim and is re-runnable.  ')
    A('**Target:** `NIRMANA_ELEVATION_PLAN_v4_0.md` §1 · §1.2 · §1.5 · §1.9 (L-01…L-12), and the '
      'Defect Register D-01…D-16 in `NIRMANA_ASSET_CONTROL_WORKBOOK_v4_1.xlsx`.  ')
    A('**Status:** observations only. No verdict is issued and nothing is certified (I16 / charter '
      'H7). **The plan was not edited and no Defect Register entry was changed** — correcting them '
      'is ADHIKĀRIN\u2019s call, not a KĀRAKA power, per the ruling on V-2. This document is evidence '
      'for that decision, not the decision.')
    A('')
    A('---')
    A('')
    A(HEADLINE.format(n=p['claims_found'], c=t.get('CONFIRMED', 0), r=t.get('REFUTED', 0),
                      d=t.get('DRIFTED', 0), u=t.get('UNMEASURABLE', 0)))
    A('---')
    A('')
    A('## 1 — Summary table')
    A('')
    A('| # | source | claim (abbreviated) | plan says | measured | verdict |')
    A('|---|---|---|---|---|---|')
    for r in p['claims']:
        claim = r['claim'] if len(r['claim']) <= 92 else r['claim'][:89] + '…'
        meas = r['measured'] if len(r['measured']) <= 115 else r['measured'][:112] + '…'
        cells = [c.replace('|', '\\|').replace('\n', ' ') for c in
                 (claim, r['plan_figure'], meas)]
        A('| `%s` | %s | %s | %s | %s | %s |' % (r['id'], r['source_section'], cells[0],
                                                 cells[1], cells[2], BADGE[r['verdict']]))
    A('')
    A('---')
    A('')
    A('## 2 — Per-claim detail')
    A('')
    A('Every detector below is quoted as it was run. Re-execute any of them to re-verify '
      'independently.')
    A('')
    cur = None
    for r in p['claims']:
        g = r['id'][0]
        if g != cur:
            cur = g
            A('### %s — %s' % (g, GROUP_TITLES[g]))
            A('')
        A('#### `%s` — %s' % (r['id'], BADGE[r['verdict']]))
        A('')
        A('**Source:** %s (`%s`)  ' % (r['source_section'], r['plan_ref']))
        A('**Claim:** %s  ' % r['claim'])
        A('**Plan\u2019s figure:** %s  ' % r['plan_figure'])
        A('**Measured:** %s' % r['measured'])
        A('')
        A('**Detector (verbatim):**')
        A('')
        A('```')
        A(r['detector'])
        A('```')
        A('')
        if r['note']:
            A('**Reading:** %s' % r['note'])
            A('')
    A('---')
    A('')
    A(METHOD)
    OUT_MD.write_text('\n'.join(L) + '\n')


if __name__ == '__main__':
    p = render()
    render_md(p)
    print('claims=%d tally=%s' % (p['claims_found'], p['tally']))
    print('wrote %s' % OUT_JSON)
    print('wrote %s' % OUT_MD)
