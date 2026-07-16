---
artifact: BRIEF_D2
type: WAVE BRIEF (three-part: PRE-BOUND + FROZEN + BIND-AT-OPEN)
wave: D-2 — Vidhi Engine + Mechanism wave
version: 2.2
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
  - v2.2 (2026-07-16, docs/pre-d2-definition-of-done): new §F1.7 Definition of DONE — anti-D-1-recurrence: Binder-emitted promise→assertion ledger (total over §F1, bind failure if not), three mandatory verification altitudes (per-lane / integration-cross-lane / post-deploy LIVE per cycle), scale realism, data-over-flags, anti-vacuous tests, truncation honesty, ledger-complete close discipline; §G scoped as a subset of the ledger, never a substitute.
  - v2.1 (2026-07-16, docs/pre-d2-orchestration-economy): new §F1.6 — native-granted
    orchestration-economy discretion: Workflow-based multi-agent fan-out where shape-appropriate,
    per-agent effort dials (down for mechanical, up for verification/doctrine), per-agent model
    dials, with the non-dialable invariants named (independent full-scrutiny verifier receipts,
    6/6 gate, FLOOR-MODEL Sonnet gate reader, Fable adjudication, reds-are-reds).
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

## §F1.6 — Orchestration economy: workflows, effort dials, model dials (native-granted, 2026-07-16)

The native has granted the conductor explicit discretion to balance COST against QUALITY by
choosing the orchestration mechanism, per-agent reasoning effort, and per-agent model — dialing
each up or down judiciously per task. The grants, and the hard limits the dials may never cross:

1. **Workflow orchestration (opt-in granted).** Where a phase is fan-out-shaped, the conductor
   SHOULD prefer a Workflow script (deterministic `pipeline()`/`parallel()` orchestration with
   per-agent `model`/`effort` overrides and structured-output schemas) over hand-spawned agent
   sequences: per-lane Phase-1 verification panels, the §G gate assertion battery + 126-tool
   census sweep, discover→transform→verify passes, judge panels on design choices (e.g. V-1's
   floor-content review, V-4's mechanism-shape alternatives). Deep single-lane implementation
   stays ONE isolated-worktree agent per lane (worktree isolation composes with workflow agents
   but is expensive — reserve it for agents that genuinely mutate files in parallel). Any
   live-connector fan-out MUST carry the throttle/backoff discipline (the deployed connector
   429s under sustained load; the harness client retries only 5xx) — a workflow that hammers
   the MCP in parallel is itself a defect, not a speedup.

2. **Effort dial.** Default: inherit. Dial DOWN (`low`/`medium`) for mechanical stages — greps,
   census probes, receipt collection, schema-declaration checks, count/paging sweeps, formatting.
   Dial UP (`high`/`xhigh`) for adversarial verification, root-cause analysis, cross-lane
   integration review, and anything that feeds a doctrine ruling.

3. **Model dial.** Cheaper/faster models for mechanical fan-out stages; stronger models for
   verification, judgment, and doctrine-adjacent work — same judgment the conductor already
   applies to its own model selection. Two fixed points that are NOT dialable: adjudicator-
   doctrine rulings remain Fable (protocol §1.1), and the §G gate reading agent remains
   FLOOR-MODEL Sonnet **by design** — that constraint IS the test (can a floor model reach the
   6 conclusions from served surfaces alone), not a cost lever.

4. **Invariants the dials may never weaken:** every lane and every substantive hotfix still gets
   an INDEPENDENT fresh-context verifier at full scrutiny before merge — a cheap/low-effort agent
   may draft, scan, or collect, but the ACCEPT/REJECT receipt must come from a verifier dialed UP,
   never down. Gate thresholds (6/6) and reds-are-reds honesty are untouchable; PARKs still need
   documented evidence. Rule of thumb: economize on discovery and mechanical transforms; spend on
   verification and irreversible steps.

## §F1.7 — Definition of DONE + verification altitudes (anti-D-1-recurrence, native-ordered 2026-07-16)

**Why this section exists.** D-1 closed with its promises "verified", yet three unplanned
remediation waves (D-1.5a, D-1.5b, D-1.6) had to run to make them true. The post-mortem across
those waves identified exactly where agent verification fails, and this section hard-codes the
countermeasures. **A phase is DONE only when everything it promised is LIVE on the deployed
connector — not merged, not tests-green, LIVE.** The five documented failure classes this
section exists to kill: (1) code-level verification passing while real-scale behavior fails
(B-4's amplifier: verified ACCEPT on synthetic fixtures, then 22,000 duplicate rows + 100%
insert failure on the real chart); (2) per-lane correctness hiding destructive cross-lane
interaction (bo_laksana's blanket delete silently destroying bo_sudarshana's rows); (3) success
flags lying (asset_throughput `lit/rows_written=45` over ZERO actual rows); (4) built-but-not-
served (four D-1.5b features with perfect table data invisible to every deployed MCP surface);
(5) vacuous tests (an empty-array fixture passing a "<100KB" size test while live served 155KB;
brief type-specimens that don't match the real chart).

1. **Promise ledger (Binder, at open — before any lane spawns).** The Binder enumerates EVERY
   commitment in §F1 — per lane: deliverables, type specimens, servability claims, "closes CR-N"
   claims — into a numbered promise→assertion table committed with the bind record. V-0 turns
   every row into an executable harness assertion (or marks it structurally-verified-by-
   construction with the exact evidence recipe). A §F1 promise with no ledger row is a BIND
   FAILURE — the wave does not spawn until the ledger is total. At close, the wave may not close
   while any ledger row is neither GREEN on the deployed connector nor a native-visible PARK
   with documented evidence and an owner. "The gate passed" is not done; **the LEDGER is the
   gate's scope** — §G's 6/6 master test is one (load-bearing) subset of it, never a substitute
   for the rest.

2. **Three verification altitudes — all mandatory, none substitutable for another:**
   a. **Phase-1 per-lane (pre-merge):** fresh-context verifier, diff review, OWN test run,
      scope-warden. Catches code defects. D-1 effectively had only this — necessary, insufficient.
   b. **Integration (pre-deploy):** full suite on the integrated tree PLUS explicit cross-lane
      interaction checks: shared-table delete/count scopes for every writer emitting to a shared
      table (the bo_laksana/bo_sudarshana class), schema-declaration completeness vs actual
      emission (the B-1 drift-detector class), append-only conflict resolutions verified keep-both.
   c. **Post-deploy LIVE (per CYCLE, not only at wave end):** after each cycle's deploy(+rebuild
      where applicable), the ledger rows that cycle claims to satisfy are re-run against the
      DEPLOYED connector with REBUILT data before the next cycle spawns. Built-but-not-served
      is NOT done and must surface here, not at wave close.

3. **Scale realism.** Verifiers must exercise real chart-scale data (the live DB via the proxy or
   postgres tool, read-only), never only synthetic fixtures. Any lane whose writer emits to a
   shared table (`bodha_msr_signals`, `chart_facts`, …) gets an explicit cross-writer scope check
   on BOTH its delete path and its `count_sql`.

4. **Data over flags.** No verifier or gate accepts a success STATE (asset_throughput row,
   register status, report checkmark, implementer's "done") as evidence — probe the underlying
   rows/serving surface. Flags are claims; rows are facts (§N.4 cockpit truth).

5. **Anti-vacuous tests.** Fixtures must model live payload shape AND volume. Type specimens must
   be re-derived from the actual chart's data at verification time — three D-1.5b brief specimens
   did not match the live chart and had to be replaced by what actually holds; a specimen that
   "must fire" is verified by firing it, not by asserting it.

6. **Truncation honesty.** No absence claim from a truncated/trimmed/paginated response (the
   Gate-Ś Śaśa-fabrication class): any "X is not present" assertion pages to exhaustion or uses
   an authoritative total/count field.

7. **Close discipline.** REPORT_D-2.md must carry the full promise ledger with per-row
   disposition (GREEN + evidence pointer | PARKED + evidence + owner + native visibility).
   `current_wave` advances ONLY after the ledger is complete. An unmet promise silently dropped
   at close is a governance breach — it is the precise D-1 failure mode this section exists
   to kill.

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
3. **Orchestrator state-commit "race" — RESOLVED pre-open (this slot is now spot-verify only):**
   fixed and adversarially verified 2026-07-16 (commit `b13640d1`, merged with this brief's own
   PR). Root cause was NOT a race — deterministic: ka_sangam's same-day resume (fingerprint keyed
   on `today`, not run_id) yields a zero-substep plan → old logic marked 'dormant' despite complete
   data → DEP-ASSERT cascade. Fix: data-presence probe via `count_sql` before accepting 'dormant'
   (savepoint-isolated, abstains on probe failure) + loud safety nets (`asset.noop_completion`,
   `asset.state_write_anomaly`, DEP-ASSERT data-present diagnostics). Binder spot-verifies the
   commit is on main, then carries the verifier's four NON-BLOCKING findings as Binder agenda:
   **F1** monitor `asset.noop_completion` events from non-resumable writers (a §N.3 delete-then-
   insert violation could be probed 'lit' over stale rows — loud, but worth alerting); **F2**
   `bo_laksana.count_sql` is over-broad (counts bo_sudarshana's rows in shared bodha_msr_signals —
   same class as PR #574's delete-scope bug, count-side; currently unreachable but tighten via a
   surgical migration when V-4 touches bo_laksana anyway); **F3** the probe abstains (fail-safe)
   on ~11 multi-`$1` and 4 literal-`%` count_sqls — fine today, but if resumption spreads to
   those assets the protection won't follow; **F4** the 0-row-recovery upsert drops
   `built_against_*`/`rows_written` (rare path, could confuse staleness detection). Forced
   same-day ka_sangam recompute semantics remain resume-by-design (writer-level, deferred).
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

**Scope rule (v2.2, §F1.7):** §G is the wave's defining test, but it is a SUBSET of the close
condition — the wave closes on the FULL §F1.7 promise ledger (every §F1 commitment green on the
deployed connector or native-visibly PARKed with evidence), of which the items below are the
load-bearing core. Passing §G with unledgered or silently-dropped promises is NOT a close.

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
