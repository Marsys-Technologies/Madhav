---
artifact: NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md
canonical_id: NIRMANA_UNIFIED_ELEVATION_PLAN
version: "2.1"
status: NATIVE-RATIFIED — governing plan for the data-plane elevation programme
campaign_id: nirmana-elevation
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
produced_on: 2026-09-04
authorized_by: >
  Native (Abhisek Mohanty). Rulings incorporated: full decision delegation (2026-09-01, execution
  prompt §2); depth-per-layer structure with sub-waves (2026-09-03); pillar rulings — P2 and P7
  PARKED, P3 flexibility clause, P4 enrich-not-confuse, P5 strong-plus-tail, P6 resolution
  mechanism, P8 strengthen (2026-09-03); orchestrator approach B APPROVED and §N.2 freeze
  exception AUTHORIZED, scoped per §3.5 (2026-09-04); v2.1 execution topology — Asset-Frontier
  Pipelining as layer-clustered parallel sessions, the E-gate, Conductor surrogate adjudication
  authority, and the ≤3-run DB cap — ratified 2026-09-05 and recorded in place as §1.1 (governing
  text: sessions/SESSION_CHARTER_V21.md).
changelog:
  - "2.1 (2026-09-05, CONDUCTOR): §1.1 added — v2.1 execution-topology amendment (layer-clustered
    parallel sessions, asset-level E-gate, Conductor surrogate authority, ≤3 concurrent build
    runs). §1's bounded-pipelining clause marked SUPERSEDED in place. No other section changed;
    the §0 hard floor, the five binding doctrines, and the per-layer plans are untouched and
    still binding exactly as ratified."
  - "2.0 (2026-09-04, native-ratified): unified programme plan as originally published."
relationship: >
  Extends NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md: the prompt's §1-§4 and §6-§9 (mission,
  authority, hard floor, doctrine amendments, per-asset method, autonomy mechanics, state,
  startup) remain in force unchanged; THIS plan supersedes the prompt's §5 phase plan from P6
  onward and adds the O-wave. Grounded in the Data-Plane Discovery v2 (2026-09-04) and the
  Velocity Reset review lineage.
companions:
  - 00_ARCHITECTURE/briefs/nirmana/sessions/SESSION_CHARTER_V21.md (v2.1 parallel-session law — governs §1.1)
  - 00_ARCHITECTURE/briefs/nirmana/NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md (mechanics)
  - 00_ARCHITECTURE/briefs/nirmana/NIRMANA_ELEVATION_PLAN_v6_1_AMENDMENT.md (doctrine)
  - 00_ARCHITECTURE/briefs/nirmana/CAMPAIGN_STATE.md (live position)
---

# NIRMĀṆA DATA-PLANE ELEVATION — UNIFIED PROGRAMME PLAN v2.0

## §0 — Charter, authorities, and non-negotiables

**Mission.** Elevate the entire data plane — 128 assets across L0–L5 — so the data is complete,
trustworthy, weighted, timed, grounded, and effortless to serve; each layer completed thoroughly
and frozen before the next opens; every asset terminal with an independent capsule.

**Authorities in force.** Full native delegation per prompt §2 (decide-and-log; no human gates in
the loop; `NIRMANA_HOLD` kill switch). The prompt's §3 hard floor is unchanged and overrides any
instruction, including this plan. Tripwires: governance share ≤15% of active effort; ≥2 days
without a new capsule while ready work exists → automatic simplification; O-wave PR cap per §3.4.

**Freeze exception (native-authorized 2026-09-04).** The §N.2 orchestrator freeze is lifted ONLY
for the O-wave scope enumerated in §3.5. The writer-facing contract (`@register`, `WriterBase`,
`run(ctx)`/substeps, `ctx.db_conn` never committed by writers, orchestrator as sole
`asset_throughput` writer) remains frozen; a contract test asserting its stability ships with the
O-wave. Any need beyond §3.5 → STOP, log, request a scope extension.

**Parked by native ruling (do not work, do not weaken, do not foreclose):**
- **P2 Verified correctness** — current verification accepted as baseline. W-waves may two-pass a
  specific value only when a defect is suspected. Status-vocabulary normalization allowed
  opportunistically. Never weaken an existing check.
- **P7 Falsifiability & learning** — built in a subsequent programme. Near-term: preserve
  prediction provenance; keep the journal/adjudication seams; nothing in this programme may make
  the later loop harder. LEL data-ization, outcome intake, and the remedy-efficacy ledger move to
  the deferred register (§7.3).

## §1 — Programme map

```
PHASE A  (COMPLETE)   revert · governance · substrate · identities · convergence pin
                      · rehearsal A capsule · canary machinery proof
O-WAVE   (NEW)        orchestrator truth core: WP-1 invalidation · WP-2 delta-skip
                      · WP-3 total plans  [freeze exception §3.5]
L0 → L1 → L2 → L3 → L4 → L5
         each layer:  W1 ANALYZE → W2 DECIDE → W3 IMPLEMENT → W4 EXECUTE
                      → W5 VERIFY+CAPSULE → W6 FREEZE
PHASE Z               campaign closure: audit · WP-5 tracker polish · debris
                      · close report · native acceptance
```

**Sequencing rules.** Layers freeze strictly in order. Sub-waves proceed aspect-major within a
layer; stragglers join the next batch rather than blocking a wave. **Bounded pipelining (standing
default, native may veto at review):** when layer N enters W4, layer N+1's W1 (read-only
analysis) may begin; N+1's W4 always waits for N's W6. — *SUPERSEDED by §1.1 (v2.1, 2026-09-05):
every layer's W1–W3 now runs from the start, and W4 is gated per ASSET by the E-gate rather than
per LAYER by the predecessor's W6. Layers still FREEZE in order.* Rebuild-avoidance economics: within-layer
improvements land BEFORE downstream layers execute (the invalidation-cascade rule) — this is why
depth-per-layer is also the cheap order.

### §1.1 — v2.1 AMENDMENT: execution topology and the E-gate (native-ratified 2026-09-05)

Native-ratified 2026-09-05, recorded by the CONDUCTOR session. This amendment **replaces §1's
execution topology only** — the programme map, the per-layer W1→W6 structure, the sequencing
rule that layers FREEZE strictly in order, and everything in §0 and §2–§7 remain binding
exactly as written. Governing text: `sessions/SESSION_CHARTER_V21.md` (this amendment is its
summary in the plan; on any conflict the charter governs).

**What changed, in one line:** the unit of gating moves from the LAYER to the ASSET. Layers still
freeze in order; assets no longer wait for their layer's turn to start.

**1. Layer-clustered parallel sessions.** The programme runs as **seven concurrent Claude Code
sessions**, each in its own worktree with permissions bypassed: the pre-existing **L0** session
(finishes L0, then ends), a **CONDUCTOR**, and **L1…L5** — one per layer, each owning all six
waves W1–W6 for its layer. No session touches another's write-set. This supersedes v2.0 §1's
"bounded pipelining" clause, which allowed only layer N+1's read-only W1 to overlap layer N's W4;
under v2.1 every layer's W1–W3 runs from the start, and W4 is governed by the E-gate below rather
than by the predecessor layer's W6.

**2. The E-gate (asset-frontier execution).** An asset may enter **W4 EXECUTE** iff all three hold:

  1. every DAG ancestor in its transitive `depends_on` closure (per the FROZEN definition) has an
     `asset_frozen` event in `nirmana_evidence.nirmana_elevation_campaign_events` — established by
     the gate SQL in charter §C10, **queried, never assumed**;
  2. its own W2 route is recorded (`asset_analysis_accepted` + `optimization_verdict_accepted`);
  3. its analysis generation-pins still match (writer digest + upstream generation) — on mismatch,
     a delta re-review first, which is normally minutes rather than a redo.

W1 and W2 are **never** gated. W3 is gated only by capability-deltas (charter C6) and write-set
disjointness (C5). **W6 layer-freeze CEREMONIES remain strictly ordered L0→L1→L2→L3→L4→L5** — the
Conductor grants each ordering ack — but asset-level work is never held for the ceremony.

The rebuild-avoidance economics of §1 are preserved, not traded away: the E-gate's ancestor-frozen
condition is precisely the invalidation-cascade rule enforced per asset instead of per layer, so
within-layer improvements still land before anything downstream of them executes.

**3. Conductor surrogate authority.** The CONDUCTOR session holds the native's adjudication
authority for the duration of the campaign (charter C3/C7): it rules on `nirmana-adjudication`
issues in writing with reasons, and its rulings bind under ADHIKĀRIN precedent. **Reserved to the
native alone** — lifting the §0 hard floor, stopping the campaign, or scope beyond this ratified
plan; the Conductor PARKs those in the issue with evidence and designs around them. The `§0` hard
floor and the `NIRMANA_HOLD` kill switch are unchanged and override this amendment.

**4. The ≤3-run DB cap.** Database connections (max 50) are the campaign's scarcest shared
resource, so **at most three build runs may be in flight campaign-wide at any moment**, and a
heavy/monster writer counts double and therefore runs solo. Slots are claimed and released by
comment on the Conductor's coordination issue **before** dispatch and **after** completion; the
Conductor audits occupancy every loop and arbitrates contention (a starving layer wins; ties break
to L2 as the critical path). Per-layer migration ranges — L1 650–659 · L2 660–669 · L3 670–679 ·
L4 680–689 · L5 690–699 · Conductor 645–649 — make migration numbering collision-free by
construction rather than by coordination.

## §2 — The north star and the five binding doctrines

Eight pillars define beyond-acharya (Discovery v2 §II): P1 breadth (STRONG — maintain), P2
(PARKED), P3 grounding, P4 synthesis, P5 salience, P6 time, P7 (PARKED), P8 service. The five
emphasized pillars carry binding design doctrines; every W2 decision cites them:

**D-GROUNDING (P3).** Every interpretive claim carries a `grounding_tier`: `sruti` (text-direct:
verse refs via rule-antecedent match or concordance pointers) · `yukti` (principle-derived: cited
principles + derivation chain — the native's flexibility clause made structural; first-class,
never second-best) · `pratyaksa` (instrument-emergent: computational provenance, no classical
claim). Grounding is applied selectively — interpretive signal classes, yoga/dosha firings,
remedies, verdicts, dasha-phala, transit quality — never as a uniform per-row mandate. A
fabricated citation is a hard-floor violation; an honest `yukti`/`pratyaksa` label is success,
not failure.

**D-SYNTHESIS (P4).** Cross-system output enriches and elevates; it never confuses. The verdict
voice is always singular. Convergence amplifies salience and stated confidence (fixed schedule);
divergence changes confidence and produces a drill pointer, never a second voice. Adjudication is
a stored, reasoned ruling (authority profile × strength-in-chart), inspectable via a lens drill
only on explicit request. No new intent, no new modality.

**D-SALIENCE (P5).** Two engines, division of labor: chart-intrinsic terms (argala, AV support,
vargottama, cancellations) live in stored salience, computed at build; contextual terms (topic
relevance, temporal activation) live in the query-time composite ranker, where they already run.
The tail is constitutional: every umbrella envelope reserves a hard-floored `tail_watch` section
(top consequence-bearers below the salience fold + rare-class leaders via percentile-in-class +
`low_salience_high_consequence` anomalies) that no budget trim may zero. Demotion (noise side)
and promotion (tail side) are both disclosed on-row.

**D-TIME (P6).** The Temporal Concordance Contract: (1) every temporal engine declares its
question in the registry; (2) one arbiter surface per (domain, range) emits
`aligned | partially_aligned(reasons) | disputed(adjudicated_by, reasons)` with per-engine
testimony as drill; (3) adjudication profiles are stored data (generalize
`kala_gochara_authority` / `kala_paddhati_profile`); (4) duplications get explicit dispositions;
(5) cross-engine agreement feeds salience as a temporal-confidence multiplier. Many instruments,
one clock.

**D-SERVICE (P8).** Strong means: every active asset has a consumer or a recorded disposition;
every capability declares density + empty-reasons; every claim drills to L1 in ≤2 hops and to its
grounding tier in ≤1 more; the tail survives every trim; one temporal voice; measured
consultation latency inside budget. Built-but-unplugged is a named defect class
(`bg_concordance`, `bodha_anomalies`, shadowed vidhi pair are the standing instances).

## §3 — THE O-WAVE (approved 2026-09-04): orchestrator truth core

Runs immediately after the convergence-regen/rehearsal work completes and BEFORE L0-W4 (L0-W1
analysis may run concurrently — it is read-only and needs no orchestrator).

### §3.1 WP-1 — Truthful invalidation (one staleness authority)

*Defect:* `staleness.py` propagates `stale` on upstream COMPLETION, not on upstream OUTPUT
CHANGE → phantom staleness; a second TS-side freshness system (receipts vs generated digest
inventory) disagrees with the first and reads mostly `expected_code_digest_missing` (receipt
coverage ~8/128; inventory drifts — the convergence-pin incident class).

*Build:*
1. Receipts universal: every writer completion captures a provenance receipt
   (`capture_and_persist_receipt` exists — make its invocation unconditional across data
   writers; probes already covered). The campaign's own rebuild pass backfills coverage.
2. Delta-directional propagation: on completion, compare new `output_digest` against the
   previous complete receipt; propagate `stale` downstream ONLY on delta; on no-delta emit a
   `refreshed_no_delta` event (visible, not silent).
3. One authority: `asset_throughput.state` derives from the receipt comparison; the TS freshness
   join reads receipt-vs-previous-receipt (or live `get_writer_source_hash`) — the generated
   json inventory is retired as a RUNTIME authority (it remains campaign-evidence pinning, with
   its CI drift detector).
4. Unknown is honest: missing previous receipt → `unknown_no_baseline`, never fake-stale, never
   fake-fresh (§N.8).

*Acceptance:* rebuild an unchanged upstream → zero downstream staled, `refreshed_no_delta`
observed; change one input constant → exactly the true transitive downstream staled, reasons
carry the delta source; TS tracker and sidecar agree on every row of one full layer plan.

### §3.2 WP-2 — Delta-skip (rebuild avoidance)

*Defect:* `rebuild` executes all scope assets unconditionally; no pre-execution generation check;
time burned on no-delta rebuilds — the user-named waste.

*Build:* pre-execution gate in the scheduler path: if `code_digest` + `config_digest` +
`upstream_digest` all match the last COMPLETE receipt for the same partition scope → do not
execute; record disposition `skip_no_delta` (run row + tracker), count it toward plan
completion. `force=true` overrides per dispatch. Fail-open: any missing/unknown digest →
execute (a wasted build is recoverable; a wrongly skipped one is silent corruption). Campaign
builds under `rebuild_only` route may pass `force` when the route demands one accepted
execution regardless.

*Acceptance:* build → immediate rebuild of the same asset: second run records `skip_no_delta`
in <2s with zero writer invocation; `force` executes; a genuine upstream delta executes.

### §3.3 WP-3 — Total plans (no silent drops)

*Defect:* plans expose only what they will run. `update`/`cascade` membership keys off the
(currently lying) `stale` state; `global_runner` DEFERs writerless assets to logs; the
`'incomplete'`-unreachability class (DVA Ruling 10) showed states can fall between selectors.
Chart scope ignores the `domain` column, so shared L0 assets ride along on chart rebuilds.

*Build:* a plan enumerates EVERY asset in scope with exactly one disposition:
`build | skip_no_delta | deferred_no_writer | withheld_protected | dormant | out_of_domain |
blocked_dependency(reason)`. Disposition taxonomy is enum-validated (M-04 discipline). Chart and
layer scopes exclude `domain='shared'` assets unless explicitly included; `global` scope owns
shared. The cockpit run view renders dispositions (minimal now; polish in WP-5). A selector gap
(any state matching no disposition) throws rather than drops.

*Acceptance:* a layer plan's dispositions sum to the layer's registry count, always; the
DEFERRED set is visible in the run record; a chart rebuild plans zero shared assets by default.

### §3.4 Scope cap and rehearsal

Target ≤3 PRs; hard tripwire at 5 (breach → stop, one decision entry, re-scope). Sequencing
(WP-4) and tracker polish (WP-5) are explicitly OUT of the O-wave. Exit rehearsal: (a)
rehearsal-B asset built twice — second run `skip_no_delta`; (b) one true-delta propagation
demonstrated end-to-end into tracker reasons; (c) one full-layer plan snapshot showing total
dispositions; (d) writer-contract stability test green.

### §3.5 Freeze-exception register (exhaustive)

| Surface | Permitted change |
|---|---|
| `pipeline/orchestrator/staleness.py` | delta-directional propagation; `refreshed_no_delta` event |
| `pipeline/orchestrator/asset_runner.py` | universal receipt capture; pre-execution delta gate |
| `pipeline/orchestrator/provenance.py` | previous-receipt lookup helpers (read-side) |
| `pipeline/orchestrator/runner.py` / `global_runner.py` | disposition-total plan walk; DEFERRED surfacing |
| `platform/src/lib/build/plan.ts` | disposition taxonomy; `domain`-aware scoping; selector-gap throw |
| `platform/src/app/api/cockpit/runs/route.ts` | receipt-authoritative freshness read; disposition pass-through |

Everything else — above all the writer-facing contract — remains frozen. WP-4's later scheduler
tuning (width, LPT ordering) touches `runner.py` scheduling constants/ordering only and rides
this same exception, per-layer, with its own logged decision.

## §4 — The layer template (W1–W6, binding for every layer)

- **W1 ANALYZE** (parallel, unbounded; read-only; reuse committed analysis bases where writer
  digest + registry contract + dependencies are unchanged). The rubric, per asset: (1) which
  pillars/doctrines does it serve — still the right instrument? (2) real vs declared
  dependencies; (3) **leverage: is any designed consumer reading NULL where this asset already
  computed the answer?** (4) **grounding: are its interpretive outputs labelable
  sruti/yukti/pratyaksa — and should they be?** (5) **temporal identity (L3): which question does
  it answer; who arbitrates its disagreements?** (6) service: consumer, floor, density, drill;
  (7) measured build + serve cost; (8) findings → W2.
- **W2 DECIDE** — one route per asset (`changed | rebuild_only [L0 default] | verified_reuse
  [expensive assets, full lineage proof] | probe | producer_covered | static | empty | retired`);
  every finding triaged `MUST` (correctness — gates the capsule) / `NOW` (in-layer improvement —
  admitted by clear value, bounded cost, or the last-cheap-chance cascade rule) / `NEVER/LATER`
  (logged with reason, closed). Chapter/doctrine citation required on every NOW. Decisions are
  one-line ledger entries.
- **W3 IMPLEMENT** — batched PRs on disjoint write-sets; one deploy per layer as target;
  migrations split from writer changes; serving-plane (TS) items land here too (no freeze
  exception needed for retrieval-layer code).
- **W4 EXECUTE** — DAG tiers inside the layer; delta-skip live (post O-wave); `rebuild_only`
  no-code-change assets go straight to build (no release pipeline); monsters scheduled solo;
  WP-4 measures first, tunes only where measured (width/LPT when L1 opens; substep chunking at
  L3 which owns the monsters).
- **W5 VERIFY + CAPSULE** — per asset: scripted mechanical checks (integrity SQL, digests,
  counts, consumer reachability) + fresh-context judgment verification; verifier identity
  appends the capsule (route allowlist enforced); rejection = fix or re-route, never argued in.
- **W6 FREEZE** — layer capsule (`stage_transition_accepted`); closure-safe sync
  (main == production, queue drained); close report: assets/routes taken, findings triage
  ledger, **pillar movement** (what this layer changed per doctrine), measured cost actuals vs
  forecast, backlog handed forward. Tracker totals derive from capsules. *(Standing default
  unless the native adds requirements: the close report is the whole W6 ceremony.)*

## §5 — Per-layer plans

### L0 — Brahmagyan (40 assets; waves 25/12/3 from the frozen definition)
Mandate: the grounding and service foundation. Named work:
- **Concordance bridge** (D-SERVICE/D-GROUNDING): verify `bg_concordance` pointer freshness
  against the 10,651-chunk corpus (its 721 rows must resolve); its consumer lands at L2 —
  disposition here is WIRE (not retire).
- **Chunk citation keys**: `classical_text_chunks` rows verified addressable for verse-level
  refs (text_id + source_citation integrity baselines exist — extend to key coverage).
- **Prashna corpus decision**: `bg_prashna_rules`/`ga_prashna` are a dormant horary FACILITY by
  design (native-confirmed). W2 records the disposition: keep dormant with a documented go-live
  rehearsal plan, or open the build-out — native's product call, presented once with costs.
- **SBC school adjudication** (`bg_sarvatobhadra_grid`, deliberately empty per ADJUDICATION-11):
  W2 presents the school-selection decision with sources; populate only on a ruling.
- Zero-consumer dispositions for the CONSUMER_MAP readings (INPUT-ONLY confirmed as design;
  SHADOWED vidhi pair re-pointed or re-declared); floors set to achieved counts (§N.4); class
  priors + cohort verified real (D-SALIENCE feed); ephemeris/sky-calendar verified (D-TIME
  feed); per-asset integrity checks where W2 accepts proposals (R0-T01 Conform work reusable).
- Routes: overwhelmingly `rebuild_only` (5–52-row reference writers); `verified_reuse`
  candidates: `bg_texts`, `bg_text_index` (corpus + embeddings — full lineage proof);
  2 probes; 3 producer-covered; 1 static; 1 empty.

### L1 — Gaṇita (19 assets)
Mandate: certify the feeds the doctrines consume. Named work: argala/AV/vargottama source facts
verified (D-SALIENCE static terms); convergence-count facts verified (D-SYNTHESIS feed); transit
anchors + AV transit gating verified (D-TIME feed); floors + count_sql completeness; opportunistic
status-vocabulary normalization (parked-P2 carve-out); `ga_prashna` dormant disposition recorded.
Little new computation; mostly verification + service hygiene. Routes: `rebuild_only` default;
`verified_reuse` where recent build evidence + lineage holds (L1 has real orchestrator history).

### L2 — Bodha (22 assets) — THE PAYOFF LAYER
- **Salience completion** (D-SALIENCE): the three static terms (argala from 41,760 facts; AV
  support from bindu/kakshya; vargottama amplification) computed into stored salience;
  cancellation modifiers verified; re-rank cascade re-runs downstream consumers.
- **Synthesis rollups** (D-SYNTHESIS): `bo_samvada` populates `system_convergence_count`,
  `cross_system_consensus_count`, `contradicts_signals_array` from existing L1 facts; the
  adjudication-rule table lands (authority profile × strength-in-chart).
- **Grounding matcher** (D-GROUNDING): signal configuration → sutravali `antecedent_jsonb`
  match → verse refs; concordance topic → chunk pointers; populates
  `classical_sources_array` + corroboration counts + `grounding_tier` on the interpretive
  signal classes (~15–20 classes, not 50,104 rows uniformly).
- **Tail lane** (D-SALIENCE): `bodha_anomalies`' `low_salience_high_consequence` promoted to a
  first-class serving input; `tail_watch` hard-floored section added to umbrella envelopes;
  serving-plane siblings land in W3: consensus chip, `resolve_grounding` spine extension, lens
  drill.
- Hygiene: UCN→UCD retirement completed per the L2 handoff; `__ssv_*` L2 shadow tables
  dispositioned; signal-embedding serve path verified.

### L3 — Kāla (23 assets)
- **Temporal Concordance Contract** (D-TIME): engine question-declarations in registry; the
  arbiter surface (extend `kala_explain`/`kala_now`); authority profiles generalized from the
  two seed tables; concordance verdict wired as salience temporal multiplier.
- **Dispositions**: gochara v1 archive (17,240 rows, retired writer, snapshot-only) formally
  archival — standing snapshot rule §3.5 of the hard floor applies; v2/v3 confirmed authority;
  `kala_taranga` decided (derived view of the field vs independent witness); all `__ssv_*`
  Kāla shadows dispositioned.
- **WP-4 heavy-writer pass**: `ka_kshetra` (8.6M rows) and gochara century materializer
  profiled; substep chunk-parallelism where the writer contract allows; scheduler width/LPT
  tuned from measured L1 data.
- Quality overlays (moorti, kota, vedha, sudarshana, tithi-praveśa) verified as consumed
  modulation, not shelf inventory.

### L4 — Phala (9 assets)
Verdict surfaces adopt the doctrines: one agreement line + strongest śruti quote per verdict
(D-SYNTHESIS + D-GROUNDING); varshaphala/tithi-praveśa consumption into anchors proven (the
Discovery's D-7); `tail_watch` in outlooks; honest probability surfaces preserved; prediction
provenance hygiene (P7 seam) verified untouched.

### L5 — Mīmāṃsā (15 assets)
Parked-P7 seam-keeping only: STRUCTURAL mode re-documented as deliberate; provenance retention
verified; adjudication-log and journal seams confirmed intact; insight-embedding serve path
noted for the future programme. No calibration values invented (§N.8). Routes: mostly
`verified_reuse`/`static` against existing build evidence; freeze closes the build arc.

## §6 — Phase Z: campaign closure
128/128 capsule audit against the final frozen definition; full cost report (actuals vs the
forecast lineage from rehearsal B onward); **WP-5 tracker polish** (dispositions, delta results,
duration-vs-estimate, staleness reasons humanized); debris: branch/worktree purge (snapshots
untouchable), `__ssv_*` final sweep, monitor disposition (event-driven + dead-man alarm);
campaign close report; native acceptance.

### §7.3 Deferred programme register (named, not forgotten)
P2 verification drive (88.1% single-pass recorded) · P7 loop: LEL data-ization, journal/outcome
intake, retrodiction pass, remedy-efficacy ledger, insight embeddings · prashna go-live
rehearsal (if kept dormant) · multi-chart modalities · SBC population (if unresolved at L0).

## §8 — Measurement
Primary: terminal capsules/day; cost per accepted asset (tokens + wall-clock, in ops state);
capsule cadence tripwire. Per layer: pillar movement statement in W6; forecast refresh after
every wave. Never proxies: PRs, commits, agents, tokens, heartbeats (prompt §7.5 list).

## §9 — Execution mechanics
The executor session runs this plan under prompt v1 mechanics (resume protocol, failure
taxonomy, verification independence, state file, identities: executor/verifier SAs with
`--include-email`). CAMPAIGN_STATE.md records position at sub-wave granularity
(`L2-W3` style). This plan lands via the governance PR that also updates CAMPAIGN_STATE and
records the freeze-exception grant; the O-wave opens immediately after.

*End v2.0 — the plan is total: every asset of every layer reaches terminal through W1–W6; the
orchestrator earns its truth in the O-wave; the doctrines bind every decision; the parked
pillars wait, undamaged, for their own programme.*
