---
artifact: BRIEF_D2
type: WAVE BRIEF (three-part: PRE-BOUND + FROZEN + BIND-AT-OPEN)
wave: D-2 — Vidhi Engine + Mechanism wave
version: 2.0
status: FROZEN — §B slots bind at wave open (Fable Binder, per CONDUCTOR_PROTOCOL §2 step 1);
  §B0 slots are PRE-BOUND (resolved 2026-07-16 against repo + register HEAD; Binder spot-verifies,
  does not re-derive)
governing: CONDUCTOR_PROTOCOL.md (v1.3) + DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §5 +
  DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3/§6/§12
prerequisite: >
  D-1.5b gate GREEN (met — 17/17) AND D-1.6 "Śuddhi" CLOSED (met — Gate Ś 11 green + 4
  by-construction + 1 parked, REPORT_D-1.6.md). Track-3 pre-work (vidhi floors/primitives/
  canonical-face-list authoring) was NEVER LAUNCHED — verified 2026-07-16: the designated
  directory briefs/doctrine_waves/track3/ does not exist and no drafted floors/primitives exist
  anywhere in the repo. Per this brief's own fallback rule, V-1 absorbs the floors+primitives
  authoring and V-3 absorbs the canonical-face-list authoring (schedule cost, not a blocker —
  already reflected in the two-cycle staging in §F1.5).
gate: the design-§8 MASTER ACCEPTANCE TEST run by a FLOOR-MODEL (Sonnet) reading agent (§G).
  6/6 required — unchanged, not weakenable.
changelog:
  - v2.0 (2026-07-16, pre-D-2 brief surgery, docs/pre-d2-brief-d2-alignment): reconciled to
    post-freeze reality (D-1.5a/D-1.5b/D-1.6 all closed AFTER v1.0 froze). (a) Every cited CR
    re-verified against POST_REMEDIATION_CONSUMPTION_REGISTER v1.5 + MARSYS_DEFECT_GAP_REGISTER
    v2/v3 + code: CR-7, CR-51(calibration-alias instance), CR-55, CR-57, CR-58, CR-60, A7-PARK,
    D15b-F3(min_weight alias), D15b-F2(CI collection) are CLOSED and no longer planned here;
    CR-72's shared-stub half closed by D-1.6 S-2 (V-6 scope narrowed to bespoke detection +
    cancellation, CR-73). (b) New §F0 substrate-delta table (what D-1.5b/D-1.6 shipped that the
    lanes now build ON, not build). (c) New §F1.5 parallel-execution design: provably-disjoint
    per-lane may_touch globs, shared-file append-only discipline, declared merge order, 2-cycle
    staging with rationale (the D-1.5b pattern). (d) §B split: stable answers PRE-BOUND into §B0;
    §B keeps only genuinely-runtime slots, each with precise binding instructions (incl. the
    orchestrator state-commit-race VERIFY, the fresh census baseline, and the post-D-1.6
    row-count baseline). (e) V-0 hardened for the deployed connector's rate limiting (the
    D-1.5b 429 cascade; harness client now retries 429 — D-1.6 D15b-F1 — but a 126-tool sweep
    still needs pacing/batching by design). (f) Track-3 absence + CR-27 corpus location made
    explicit. Gate unchanged (design-§8, 6/6).
  - v1.0 (2026-07-15): initial frozen brief.
---

# D-2 — Vidhi Engine + Mechanism

## §F0 — Substrate deltas since v1.0 froze (build ON these; do not re-plan them)

Shipped and live (deployed connector + Abhisek estate) by D-1.5b (REPORT_D-1.5b.md) and D-1.6
(REPORT_D-1.6.md). Lanes and the Binder treat these as existing capability:

| Delta | Where | D-2 relevance |
|---|---|---|
| §N.6 Serving Density Principle (prose) + `Density Census (§N.6)` CI job + `platform/scripts/audit/density_harness/` | CLAUDE.md §N.6; ci.yml | V-0 extends this harness, never duplicates it; every V-2/V-3 surface must comply |
| `ganita_dasha_lord_capability_get` (B8 derived view; CR-60 CLOSED_WITH_EVIDENCE) | live tool | V-1's `dasha_spine + lord_capability` floor primitive maps to a LIVE tool now |
| `signal_type_class` param on `bodha_signals_get` (pre-LIMIT class filter) | live tool | V-5's classes are verifiable per-class regardless of global salience rank; V-0 assertions use it |
| `divisional_facts` section on `ganita_chart_facts_get(divisional_chart=…)` — serves `chart_divisionals` EAV incl. D2 `varga_hora_class` (CR-58 CLOSED) | live tool | V-1 floor primitives for varga/hora reads have a live face |
| Ayanamsha-INVARIANT facts served; response budgets on former oversize tools; positions default ordering; B9 dosha catalog gate; kala_sarpa facet | serving layer | baseline behavior V-3 must not regress |
| New L1/L2 data: chalit (`bhava_cusps`/`house_chalit`/`sandhi_flag`), real KP cusps + sub-lords, `house_bhava_bala_total`, `ashtakavarga_bindu_sign`, `karakamsa_position`, `varga_hora_class`, `sudarshana_agreement` signals (bo_sudarshana asset), `bhavat_bhavam_amplifier` signals | DB + serving | MANDATORY floor content for V-1 (see §B0.4); inputs for V-5 |
| `varga_ratification_divergence` signal class live (CR-57 CLOSED); `ganita_sensitive_degrees_get` live (R-47 closed) | live | V-1 primitive mappings |
| D-1.6 "Śuddhi": filter honesty (planet-scoped remedies), calibration-alias unification (CR-51 instance), live muhurta citations, degenerate-ranking honesty flag, dosha shared-stub fix (22 doshas now carry real per-chart `constituent_facts_array` — CR-72's stub half), assess_* wired to firings-authoritative data, duplicate-yoga-firing fix, truncated-page fabrication fix, ~14K NULL activation dates recovered + flat-0.5 dasha-alignment fixed, aspects-facet routing fix (A7 PARK CLOSED), 4 more oversize tools <64KB, R-18 param-honesty CI harness (263 params/0 flags), `sidecar_available` dead-route fix, CR-90..107 register reconciliation | REPORT_D-1.6 | these items are DONE — no lane re-plans them |
| Salience DR precedent: DR-3 (DIS.016) set `sudarshana_agreement=1.15`, `bhavat_bhavam_amplifier=0.85` | DISAGREEMENT_REGISTER | template for V-5's §B.2 binding |
| Harness client retries 429 honoring `retry_after_seconds` (D15b-F1, `doctrine_harness/lib/mcp_client.ts`); `bodha_writers/__tests__` collected by CI pytest (D15b-F2); `min_weight`→`min_salience` alias fixed with test (D15b-F3) | code, verified 2026-07-16 | V-0 builds on the 429-retry; the two D15b residuals named in v1.0-era notes are DEAD — not lane scope |

## FROZEN §F1 — Lane map (7 lanes)

### Lane V-0 — Gate harness extension
The master-acceptance harness, extending `platform/scripts/audit/doctrine_harness/` (canonical per
protocol §8.8(v)) and reusing `density_harness/` where it already asserts §N.6: (a) the 6 §G.0
load-bearing wealth conclusions (register §G.0 table) as executable presence checks ("conclusion N
traceable to a served signal/verdict in the top-15 of its domain surface"); (b) census battery
(~126-tool full sweep, PASS/DEGRADED/EMPTY/FAIL counts vs the baseline the Binder records at open
per §B.5 — the register-§F 2026-07-13 sweep is OBSOLETE as a baseline, the estate has changed
across three waves); (c) completeness-receipt validator; (d) alias-count check vs the canonical-face
list V-3 declares.
**HARD DESIGN REQUIREMENT — rate limiting:** the deployed connector rate-limits under sustained
assertion load (D-1.5b Gate B: 429 cascade at a 32-assertion sequential run; 17-assertion batches
ran clean). The client-side 429-retry (D15b-F1) is necessary but NOT sufficient for a 126-tool
sweep: V-0 must build proactive pacing — batches sized under the observed threshold (≤~17 calls),
inter-batch throttle, per-batch checkpointing so an interrupted sweep resumes rather than restarts,
and TRANSPORT-vs-TOOL error separation per protocol §6.4. A census that trips the limiter and
reports false reds is a harness defect, not an estate defect.

### Lane V-1 — Vidhi registry + compiler (+ absorbed Track-3 authoring)
~30 primitives as versioned registry rows (each: definition, live-tool mapping + args, fallback
face, `known_gap` ref into the CR register per §B0.1's reconciled state); per-intent-class acharya
floors + machine bands as data (worked example `floor(wealth_deepdive)` in design §3 is the
template); the compiler: question → scope_tuple(intent, domains, width, depth, horizon,
intervention?, entitlement) → contract. Deterministic: identical tuple → identical contract.
**Track-3 authoring is absorbed here** (never launched — see prerequisite): V-1 authors the floors
+ primitives from scratch, into the registry as data plus source drafts under
`00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/track3/` (the directory Track-3 was
chartered to fill; keep its DONE-CHECK: every intent class has a floor; every primitive names its
live tool + known_gap; the CR-27 corpus mapped to floor items).
**REQUIRED INPUT — the CR-27 improvisation corpus:** register row CR-27 (status LOGGED) in
`00_ARCHITECTURE/llm_consumption_audit/POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` §A — the four
logged Class-9 instances (diff-answered-fresh; supply-shaped plans ×2; chain missed; nakshatra
omitted) — plus the CR-36 buried-evidence specimen and the §G.0 six-conclusion table in the same
file. Each logged improvisation must be prevented by a floor item or explicitly noted as
out-of-contract. Primitive mappings use the §F0 live faces (dasha_lord_capability, divisional_facts,
varga_ratification_divergence, sensitive_degrees, signal_type_class) — a `known_gap` citing a CLOSED
CR is a defect.

### Lane V-2 — MCP delivery + receipts
Vidhi registry as MCP resource; compiled plans as MCP prompt (+ `plan_retrieval` meta-tool
fallback); scope tuple echoed for correction before execution; **completeness receipt** on every
synthesis (served/empty/dark per floor item, each dark citing its CR row); `capability_version` +
`tools/list_changed` staleness kill.
**Deploy-path flag (from REPORT_D-1.5b):** deploy.yml rebuilds amjis-mcp only on `platform-mcp/`
path changes — a `platform/`-only change does NOT re-point the MCP image (harmless while amjis-mcp
proxies amjis-web's capability API, but V-2/V-3 change MCP-server code where it WOULD matter).
V-2's verifier confirms the deployed amjis-mcp image SHA advanced after each cycle-2 deploy; if a
cycle ships platform/-side payload changes consumed via the proxy, confirm intended behavior
explicitly rather than assuming.

### Lane V-3 — Channel: two-pass + capability map (+ absorbed canonical-face-list authoring)
Pass-1 SCAN face (ultra-dense subject-bearing index lines, ~60B/row) + Pass-2 FETCH-by-id; the
capability map gets a live source — **CR-9 still OPEN, root cause verified 2026-07-16:**
`platform/src/proxy.ts` isPublic allowlist lacks `/api/cockpit/registry` so `asset_registry_all/_l0`
still 401 (the `bg_transit_rules` whitelist half of R-16 WAS fixed in D-1.6 — do not re-fix);
**twin-alias dedup → the canonical-face list, authored HERE** (Track-3 absent): draft the ~30
canonical faces from the live `tools/list` census the Binder records (§B.5), deprecated faces
removed from the LLM-visible list — the broad CR-30 dedup remains OPEN; the CR-51
calibration-alias INSTANCE is already fixed (D-1.6 S-1) and is the pattern to follow, not work to
redo; description-vs-payload CI audit (CR-44, still OPEN — extend D-1.6's R-18 param-honesty
harness precedent from param-filtering to description-vs-payload); errors-that-teach (return the
corrected call — design-§6 capability; note the original CR-7 specimen is CLOSED, the CLASS is
what V-3 builds); per-chart reading-notes (CR-38/71/80, LOGGED — content lives in those register
rows) as MCP resources; chart-keyed special-lagna access (CR-16 still OPEN — verified:
`query_special_lagnas` still takes `BirthDataSchema` only); pact MD-lord naming (CR-15, OPEN);
holistic bundle sub-tool repair, non-ok on sub-errors (CR-14/39, both OPEN); intent_classify as
the scope-tuple classifier (CR-28, OPEN — routed to Opus engineering adjudication at D-1.6 bind
and NOT ruled; D-2 obtains that ruling first (§B.7), then wires per it).

### Lane V-4 — Mechanism object + CGM elevation
Mechanism = named, valenced CGM subgraph, first-class table + serving face; real edge-strength
formula from the ga_vichara valence pass (retire hardcoded literals, CR-86); arudha + special-lagna
nodes; chain/circuit motifs (the 10→8→12→10 specimen MUST exist as a served mechanism — CR-24);
completed centralities (eigenvector/betweenness/harmonic); CGM astrological salience joining
composite ranking (CR-25 — graph no longer structurally subordinate to MSR); **close both dead
links**: CGM metrics → MSR `structural_role` (post-CGM re-rank pass, CR-84) and centrality →
convergence consumption stub-removal (CR-85; full consumption is D-3); **retire `bo_anveshana`**
(CR-78) — discoveries become mechanism-derived (retirement = registry removal + data disposition
via migration WITH a migration-guard receipt; anything beyond the idempotent delete-then-insert
pattern is PARK class 2); D10 lord-placement/karaka joins into the career lens (CR-62 multi-varga
map: wealth {D1,D2,D9,D11}, career {D1,D9,D10}). All seven cited CRs re-verified OPEN at register
HEAD (CR-84/85/86 explicitly "→ D-2/§12").
**Bounded pickup (sanctioned):** PARK-#4 / CR-90 — the 5 residual `keyword_heuristic_v1` valence
rows, parked since D-1.5a, excluded from D-1.6 by the bucket-7 ruling ("MSR valence internals stay
in their designed waves"); their designed wave (D-1) is closed, and V-4 already works the same
valence substrate for the re-rank pass — re-emit from the fixed builder or prove the rows
unreachable dead data.

### Lane V-5 — Semantic signal classes
Nakshatra-semantic (own-star, dispositor chains, tara bala, end-degree flags — CR-26/64), arudha
(AL conjunctions, A2/A11, AL–bhāva relations — CR-61), special-lagna (Indu/Sree/Ghati/Hora with
domain salience — CR-76), and vargottama + dhana-axis classes (vargottama amplification as a
first-class signal; complete-2/11-axis tenancy — CR-36): each a NEW emitter module folding into the
signal-class registry (append-only; no shared-file edits with V-4's re-rank pass — mirror the
bo_sudarshana separate-writer pattern, and respect the D-1.5b `owned_signal_type_classes` delete
allowlist so a rebuild never wipes a sibling class). All four cited CR clusters re-verified OPEN.
Inputs now live per §F0: `karakamsa_position`, special-lagna facts, `signal_type_class` filter for
per-class verification. Salience/priors per §B.2 binding (DR-3 is the precedent).
**Bounded pickup (Binder dispositions at open, §B.8):** Gate Ś item 8 residual — the yoga
signal-class's `dasha_eligibility_rule` construction (74 rows on 482012f1, 0 dated; birth-moment/
catalog yoga signals lack a natal constituent_lord to match forward windows; REPORT_D-1.6 offers it
to D-2 as a bounded item). Fits this lane's signal-class registry work; the firings-authoritative
yoga surface is unaffected either way.

### Lane V-6 — Doctrine completions
Upapada wiring (BPHS ch.30 rules from L0 corpus × computed A12 — CR-101); Nārāyaṇa Daśā (CR-104);
pañcadhā-maitrī compound matrix (CR-105) — all three re-verified routed-to-D-2 at register §N;
Chara Daśā wired as a timing witness (CR-77 amended — wiring, not build; CR-77 OPEN);
kendrādhipati-doṣa + per-lagna functional-benefic completion (D-1.5 deferral; **Adjudicator-doctrine
required** — extends the valence matrix, DR-n recorded; must be consistent with DR-4's NBRY-grounds
taxonomy); bespoke detection for remaining catalog doshas — **scope NARROWED post-D-1.6:** the
CR-72 shared-stub half is CLOSED (S-2: all 22 `dosha_label` rows now carry real per-chart
constituent fact_ids) and the B9 catalog gate (D-1.5b) governs serving; what remains is CR-73
(OPEN): per-chart bespoke detection WITH cancellation/bhaṅga checks, so every served dosha is
either per-chart computed with cancellation or catalog-gated.

## §F1.5 — Parallel execution design (the D-1.5b discipline, made explicit)

Every lane runs as an **isolated-worktree sub-agent** (`wave/D-2/<lane>` branch) with an
independent fresh-context Opus verifier (protocol Phase-1) before integration. Scope-warden
(protocol §3(d)): a diff touching any path outside the lane's globs below is an automatic
REJECTION.

**Per-lane `may_touch` globs (provably disjoint except the declared shared files):**

| Lane | may_touch |
|---|---|
| V-0 | `platform/scripts/audit/doctrine_harness/**` · `platform/scripts/audit/density_harness/**` · `.github/workflows/ci.yml` (census-battery job block only) |
| V-1 | `platform/src/lib/vidhi/**` (new) · `platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi*.py` (new) · `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/track3/**` (new) · own migrations `platform/migrations/<allocated>_vidhi_*.sql` |
| V-2 | `platform-mcp/src/resources/**` (new) · `platform-mcp/src/prompts/**` (new) · `platform-mcp/src/tools/register_vidhi*.ts` (new) · `platform-mcp/src/lib/completeness_receipt.ts` (new) · [shared] server registration index |
| V-3 | `platform/src/lib/retrieval/registry/**` · `platform/src/proxy.ts` (CR-9 allowlist line) · `platform-mcp/src/tools/**` EXCLUDING `register_vidhi*.ts` · `platform-mcp/src/lib/scan_fetch*.ts` (new) · [shared] server registration index |
| V-4 | `.../writers/bo_karanajala.py` · `.../writers/bo_cgm_*.py` · `.../writers/bo_yantra*.py` (new mechanism writer) · `.../writers/bo_laksana.py` (EXCLUSIVE — the re-rank pass) · `.../writers/bo_anveshana.py` (retirement) · `.../writers/ka_yojaka.py` (CR-85 stub-removal only) · own migrations |
| V-5 | `platform/python-sidecar/bodha_writers/*_emitter.py` (new files) · new `bo_*` writer modules for its classes (new files only) · own migrations · [shared] `brahmagyan/l0_class_priors.py`, `CHART_FACTS_SCHEMA.json`-equivalent signal-class registry (append-only) |
| V-6 | `.../writers/ga_structural.py` (EXCLUSIVE) · `.../writers/ga_sensitive.py` · dasha-system modules for Nārāyaṇa/Chara wiring · L0 corpus rule files for upapada/maitrī · own migrations · [shared] `l0_class_priors.py`, schema declaration files (append-only) |

**Shared files (identified up front; APPEND-ONLY; expected-conflict notes):**
- `brahmagyan/l0_class_priors.py` — V-5 + V-6 both append class priors. Expected merge conflict;
  resolution = keep both appends (exact D-1.5b B-3/B-4 precedent).
- MCP server registration index (`platform-mcp/src/server.ts` or tool index) — V-2 + V-3 both
  append registrations. Append-only; keep both.
- `CHART_FACTS_SCHEMA.json` / schema-declaration surfaces — any lane adding a new fact/signal
  category MUST declare it (the D-1.5b cycle-1 drift_detector trap); append-only.
- Migration numbering — no shared file, but the Binder allocates per-lane number blocks at open
  (§B.6) so parallel lanes never collide; single directory `platform/migrations/` only.
- `asset_registry` rows — each lane's migration touches only its own asset ids (incl. correct
  chart-scoped `count_sql` per §N.4).

**Cycle staging — TWO cycles (recommended, with reasons):** 7 lanes cannot be one batch because
V-2 serves V-1's registry (schema + rows must exist and be deployed to write receipt/prompt code
against reality) and V-3's capability map + alias dedup must mark the live faces V-1's primitives
name; V-0's final alias-count/receipt assertions read V-2/V-3's output. Everything else IS
parallel. Therefore, mirroring D-1.5b's clean 2-cycle merge:
- **Cycle 1 (5 parallel lanes — build substrate + data):** V-0, V-1, V-4, V-5, V-6. Integrate in
  merge order below → deploy → scope-limited rebuild (Binder-computed asset_set per §8.2
  MINIMAL-CASCADE: the mechanism/CGM/vidhi assets + MSR re-rank consumers + V-6's `ga_*` writers +
  their true DAG closure via `asset_registry.depends_on`; protocol expects "L2/serving, NOT a full
  L3+", but V-6's ga_structural/dasha edits pull an L1-subset cascade — Binder computes, records,
  and does not default to layer-wide).
- **Cycle 2 (2 parallel lanes — serving):** V-2, V-3. Integrate → deploy. No rebuild expected
  (serving-only); if a cycle-2 diff touches any writer, the Binder expands scope explicitly.
- **Gate:** V-0-final-run on the deployed connector (not a merge step).

**Merge order (declared):** V-0 → V-1 → V-4 → V-5 → V-6 ‖ then cycle-2: V-2 → V-3 ‖ then
V-0-final-run. (Harness first — §8.8(v) makes its assertions canonical; registry before graph;
graph before classes that read it; doctrine data last in cycle 1; serving last overall.)

## FROZEN §F2 — must_not_touch
FROZEN orchestrator contract (PARK class 1) — **including the state-commit race fix: owned by a
parallel session, D-2 VERIFIES only (§B.3), never patches** · Gate-A/B/Ś surfaces' semantics
(regression-guarded by re-running those batteries in this wave's gate) · ka_* convergence internals
beyond V-4's CR-85 stub-removal (D-3) · L5 calibration (D-4) · KP sub-lord engine (deferred;
consumes B-1's real cusps when it comes) · bucket-7 items dispositioned to D-3/D-4 per
BRIEF_D1_6 scope_ruling (convergence engine, hardcoded natal constants CR-87/88/89/107,
calibration loop, LEL retrodiction).

## §B0 — PRE-BOUND slots (resolved 2026-07-16; Binder spot-verifies against register/repo HEAD)

1. **`known_gap` reconciliation (was BIND-AT-OPEN "what D-1.5 actually closed"):** system of
   record = `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` v1.5 (CR-1..89 + CR-107 row statuses;
   CR-90..106 superseded to the §N pointer table) + `MARSYS_DEFECT_GAP_REGISTER_v2_0.md`.
   Verified state of every CR this brief cites: **OPEN** = CR-9, 14/39, 15, 16, 24, 25, 26/64,
   28, 30(broad dedup), 36, 44, 61, 62, 73, 76, 77, 78, 84, 85, 86, 90(PARK-#4);
   **CLOSED — cite as closed in known_gap, do not re-plan** = CR-7, CR-51(instance), CR-55,
   CR-57, CR-58, CR-60, CR-72(stub half), A7/R-17, R-47, D15b-F2, D15b-F3; **LOGGED (inputs, not
   defects)** = CR-27, CR-38/71/80; **routed-to-D-2 injections confirmed** = CR-101, CR-104,
   CR-105 (register §N pointer table).
2. **Track-3 pre-work:** ABSENT (see prerequisite). V-1/V-3 absorb. No Binder probe needed beyond
   confirming `track3/` is still absent at open.
3. **CR-27 improvisation corpus path:** register §A row CR-27 + §G.0 + CR-36 specimen (see V-1).
4. **Floor-content mandatory-surface list (was "Track-3 floors reviewed against D-1.5b
   surfaces"):** the relevant intent-class floors MUST contractually consume: chalit/bhava-cusp
   facts, Sudarśana agreement, Bhavat Bhavam, bhāva-bala atoms (`house_bhava_bala_total`),
   `ashtakavarga_bindu_sign`, D2 `varga_hora_class` via `divisional_facts`, `karakamsa_position`,
   real KP cusps + sub-lords, `dasha_lord_capability`, `varga_ratification_divergence`,
   sensitive-degree checks. This is §5-of-plan step 3: capabilities become contractually consumed
   here. V-1's verifier asserts the list.
5. **Harness client rate-limit state:** 429-retry with `retry_after_seconds` honor is SHIPPED
   (D15b-F1). V-0's remaining obligation is proactive pacing/batching/checkpointing (see V-0).
6. **Rebuild transport:** rebuilds go via the Cloud Run job path (`brahma-build-pipeline-job`,
   `POST /api/cockpit/runs`), NEVER the laptop proxy — O8_LOCAL_PROXY_KILL_ROOT_CAUSE_v1_0.md +
   STATE_D-1.5b precascade_rebuild. Standing fact, not a per-wave probe.

## §B — BIND-AT-OPEN slots (Fable Binder; read-only remit per protocol §1.1 — outputs are
BIND_D-2.md + this brief's status stamp ONLY)

1. **Rollback pin + prior-battery regression green (§8.8(i)):** record the three service image
   SHAs (`gcloud run services describe … --format='value(spec.template.spec.containers[0].image)'`
   for amjis-web/amjis-mcp + job image) and Abhisek's current build_id; then re-run the Gate-A,
   Gate-B, AND Gate-Ś batteries on the deployed connector. Expected residual reds ONLY: PARK-#4
   (absorbed by V-4 this wave) and Gate Ś #8 (dispositioned per §B.8). Any OTHER red = regression
   incident, route to Adjudicator-engineering, do not spawn lanes.
2. **V-5 salience constants + class priors:** probe `bodha_signals_get` tier/salience spread per
   `signal_type_class` on 482012f1's CURRENT estate (post-D-1.6 rebuild — never a cached
   distribution); Adjudicator-doctrine (Fable) sets the four classes' constants as a recorded DR-n
   (DR-3's 1.15/0.85 rulings are the calibration precedent).
3. **Orchestrator state-commit race — VERIFY the fix landed (do not fix):** the race documented in
   REPORT_D-1.6 (asset_throughput `state` never transitioning to `lit` despite a correct data
   write, cascading DEP-ASSERT/BLOCKED under narrow-scope rebuilds) is being fixed by a parallel
   session. Binder checks main's commit history / the state-write path for that fix and records
   landed|not-landed. If NOT landed: record as a rebuild-operations risk with the manual recovery
   runbook (verify data → correct stuck flag → resume, per REPORT_D-1.6) — it is NOT a lane item
   (FROZEN orchestrator, PARK class 1).
4. **V-4 edge-strength formula terms:** probe `ganita_vichara_get` for the shipped valence-pass
   output shape (fields/classes actually emitted — `valence_pass` / `varga_ratification` /
   divergence rows); Fable rules the formula's terms/weights as a DR-n. The shape is inspectable
   in `pipeline/orchestrator/writers/ga_vichara.py`; the live probe guards against shape drift
   since the last deploy.
5. **Fresh census baseline + canonical-face input:** run `tools/list` + the V-0-style sweep
   (paced per V-0's rules) against the deployed connector; record tool count and per-tool
   PASS/DEGRADED/EMPTY/FAIL as THE baseline the gate's "census ≥ baseline" clause reads. This
   census is also V-3's input for authoring the canonical-face list (Track-3 absent).
6. **Migration number allocation:** read `platform/migrations/` HEAD (≥440 post-D-1.6), allocate
   disjoint per-lane number blocks (V-1, V-4, V-5, V-6), record in BIND_D-2.md.
7. **CR-28 engineering ruling:** obtain the Opus engineering adjudication (routed at D-1.6 bind,
   never ruled) — prompt-delegation ratified as the P-10 contract, or redesign to return a
   classification — BEFORE V-3 wires intent_classify as the scope-tuple classifier.
8. **Gate Ś #8 pickup disposition:** conductor + Binder decide at open whether V-5 has capacity
   for the yoga-class `dasha_eligibility_rule` residual (see V-5); if not, it stays tracked in
   MARSYS_DEFECT_GAP_REGISTER_v2_0.md — explicitly non-blocking for this wave's gate.
9. **Build-health row-count baseline (§8.7 override):** the L1_GANITA_CLOSURE counts are
   SUPERSEDED for the ±1% check — D-1.6's rebuild legitimately grew chart_facts 27,554 → 138,279
   (investigated clean, REPORT_D-1.6). Binder records current per-table counts at open as the
   baseline, plus expected deltas from this wave's new fact/signal categories.
10. **Rebuild scope ruling (§8.2):** compute the minimal cycle-1 asset_set (changed writers + true
   `depends_on` closure) and record `{scope, layers, full: bool, rationale}`; expected NON-full.

## §G — Gate (the wave's defining test — UNCHANGED from v1.0 in substance; 6/6 stays)

1. **Master acceptance, floor-model:** a FRESH Sonnet reading agent, given only the served surfaces
   + the compiled vidhi (no priors, no register, no hand-derivation), produces the 482012f1 wealth
   reading; harness asserts each of the 6 §G.0 conclusions is traceable to a served top-15
   signal/verdict. 6/6 required. (Floor-model rule: if Sonnet passes, the instrument does the work.)
   **Isolation spawn recipe (mandatory):** the reading agent runs OUTSIDE the repo (empty cwd, no
   repo file access — it must not read CLAUDE.md/the register/close reports), tool allowlist = the
   deployed MCP connector ONLY, model=Sonnet, and receives a verbatim prompt stored in this brief's
   BOUND appendix at wave open (shape: "You are reading chart <uuid> for a full financial
   assessment. Use the vidhi plan the server provides. Produce the reading with citations to served
   signal/fact ids."). The harness — not the agent — judges conclusion coverage afterward.
2. Census battery ≥ the §B.5 open-recorded baseline (no regressions); alias count = the canonical
   list; completeness receipt present on the reading; **Gate-A + Gate-B + Gate-Ś batteries still
   green** (regression) — the §B.1 expected-residual reds are green-or-absorbed by close (PARK-#4
   via V-4; Gate Ś #8 per its §B.8 disposition). The gate runner paces its battery per V-0's
   rate-limit rules.
3. A second synthesis probe on a NON-wealth domain (career) to prove the vidhi generalizes: floor
   items served or honestly dark-cited, receipt validates.
