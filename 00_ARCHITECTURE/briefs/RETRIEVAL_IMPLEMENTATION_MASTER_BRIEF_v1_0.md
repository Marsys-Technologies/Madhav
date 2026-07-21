---
artifact: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md
canonical_id: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF
version: 1.0
status: ACTIVE
type: CLAUDECODE_BRIEF (governing scope for the retrieval-elevation implementation campaign)
authored_by: Claude (Cowork, Fable 5) 2026-07-19, native-directed
authority: >
  Native directive 2026-07-19. This brief converts
  RETRIEVAL_PLANE_ELEVATION_PLAN v1.8 into execution. It governs every
  session launched against it; its may_touch/must_not_touch override all
  other scope guidance. The root CLAUDECODE_BRIEF.md (D-4 pointer) does NOT
  govern these sessions and must not be modified; D-4 is not opened here.
run_mode: >
  FULLY AUTONOMOUS, conductor + multi-agent swarm, ONE human gate (§F Wave-1
  exit — native reviews the concept/tool mapping packet). Native runs with
  bypass permissions. Everything recorded; commits are checkpoints; a wave
  is DONE only when its independent VERIFIER agent returns ACCEPT.
may_touch:
  - "platform/** and platform-mcp/** source (THIS is the implementation campaign)"
  - "platform/supabase/migrations/** (surgical migrations only, §N.4)"
  - "00_ARCHITECTURE/RETRIEVAL_*.md, briefs/retrieval_impl/** (NEW), CURRENT_STATE, SESSION_LOG"
  - "git branches/worktrees for this campaign; merge to main; push; deploy per §E.6"
must_not_touch:
  - "FROZEN orchestrator + WriterBase contract + all ga_*/bo_*/ka_*/ph_*/mi_* writer build logic (§N.2). The §9.6 post-build verifier sits BESIDE the build, never inside it."
  - "CLAUDECODE_BRIEF.md (root); doctrine-wave briefs/ledgers (read-only)"
  - "chart_facts semantics / chart computation; LEL content"
  - "Paripraśna UI/streaming/render (parallel workstream; only the §D
     cross-cited seams: consult/route.ts floor adoption + audience_tier
     excision per C-2)"
status_field_semantics: >
  status: COMPLETE only when §H final criteria all pass (incl. main ==
  production and environment cleanup).
---

# Retrieval Plane Elevation — Master Implementation Brief

## §A — Mission

Implement `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` (**v1.8 — read it in
full; it is the specification**) end to end: phases R-0…R-5 including every
§7 industry amendment, every §8 strategy amendment, and every §9 register
row (§9.1 safety, §9.2 rulings, §9.4 W-1..W-19, §9.6 Concept Spine
W-20..W-27, §9.7 scale/QoS W-28..W-31). Companion specs:
`RETRIEVAL_STRATEGY_v1_0.md` (v1.1 — doctrine + acceptance),
`RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md` (vendor constraints),
`briefs/retrieval_audit/GROUND_TRUTH_REGISTER.md` (code ground truth),
`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §1/§4/§6/§13 (consumer contract).

## §B — The live instrument (LEVERAGE IT — native directive)

The deployed MARSYS-JIS MCP connector ("MARSYS direct") gives this campaign
real-time access to the production retrieval engine and data plane. Use it
**significantly and continuously**:

1. **W0 baseline probe suite.** Before changing anything, record the live
   behavior of a representative probe set (≥25 tools spanning every layer +
   both charts 482012f1/1c826d5a): tools/list snapshot, envelope shapes,
   flag vocabularies, response sizes, latencies, error shapes. Committed as
   `briefs/retrieval_impl/BASELINE_PROBES.md` + raw JSON. This is the
   before-picture every later verification diffs against.
2. **Per-wave live verification.** After each wave's deploy, the VERIFIER
   re-runs the probe suite + wave-specific probes against the DEPLOYED
   connector (not just local tests). A wave whose live probes regress the
   baseline does not close.
3. **Implementation-time inspection.** Agents use MARSYS direct to inspect
   real served payloads while designing (e.g. actual envelope bytes, actual
   facet behavior) instead of reasoning from source alone.
4. If the connector is unreachable at any point: fall back to the local
   runtime harness, record the outage in STATE.md, and re-run the live
   probes when it returns. Never silently substitute local for live.

## §C — Delegated rulings (adopted at W0; native may override at the §F gate)

To preserve full autonomy, the standing §9.5 queue is resolved by adopting
the recommendations already recorded in the plan/consult/strategy docs.
Record each in `briefs/retrieval_impl/RULINGS_ADOPTED.md` with its source
pointer:

- **OT-7**: one registry, many generated projections (best-surface-per-
  channel reading). **OT-10**: (b)+(c) — connect-time profiles enforced by
  OAuth scope. **OT-2**: job-handle-FIRST with progress notifications
  layered (per plan §9.7 analysis). **OT-5**: keep self-issued OAuth (a)
  for this campaign; run a ≤1-day Firebase-OIDC spike and record findings
  for a future ruling — do not block on it. **OT-6**: no journaling this
  campaign; pin/provenance-stamp only (D-05 safe because prashna_ask
  ships). **RC-1**: ≤20 umbrellas for non-Claude families; Claude-family
  compact 25–35 + tool-search metadata. **RC-2**: ChatGPT search/fetch
  connector projection = DEFERRED (recorded, not built). **RC-3**: DeepSeek
  = consult-profile only. **RS-1/RS-2/RS-3**: approved as specified
  (layering ruling; coverage doctrine + disposition authority per §9.6
  states; efficiency targets as gate criteria). RS-4 + C-1..C-6 +
  F-R1/F-R7 + AMBIG-1..4: already ruled (plan §9.2/§9.3) — implement as
  written.

## §D — Execution model

**Conductor + swarm.** The kickoff session is the conductor. It implements
nothing itself: it sequences waves, spawns lane agents and verifier agents,
adjudicates, merges, deploys, and keeps the ledger.

- **Isolation:** each lane runs in its own worktree/branch
  (`impl/w<N>-<lane>`); lane → wave branch (`impl/wave-<N>`) → main. Merge
  to main ONLY after the wave verifier's ACCEPT. Push to GitHub at every
  wave close; deploy per §E.6.
- **Model/effort selection (yours, per task):** fable/opus + high effort
  for design-heavy lanes (descriptor/compiler design, taxonomy, envelope
  semantics, verification); sonnet-class for mechanical migration of
  many-handler patterns; cheap models for scouts/greps. Verifiers are
  ALWAYS opus-or-stronger at high effort and are NEVER the implementer of
  what they verify. Log every model/effort choice in the wave ledger.
- **Verification doctrine ("done = verified"):** every lane ships with
  tests; every wave closes with an independent verifier agent that (a)
  reruns tests + CI gates, (b) runs the live-MCP probe suite (§B), (c)
  checks the wave's acceptance criteria from plan §6/§7-metrics/§9
  verbatim, (d) hunts adversarially for the wave's likely failure modes.
  Verifier verdict + evidence goes in `briefs/retrieval_impl/VERIFY_W<N>.md`.
  REJECT → conductor respawns fix cycles until ACCEPT (record every cycle).
- **Parallelize** lanes inside a wave wherever files don't collide;
  sequential only where a dependency or shared file forces it.
- **Failure discipline:** a stalled agent is respawned once with narrowed
  scope; twice-failed work is re-planned by the conductor (fable, high) —
  never silently dropped. Hard blockers that would require violating
  must_not_touch: STOP that lane, record, continue others.
- **Ledger:** `briefs/retrieval_impl/STATE.md` — waves, lanes, branches,
  commits, deploys, model choices, anomalies, probe-suite diffs. Updated
  and committed at every transition.

## §E — Waves

### W0 — Foundations (sequential, small)
1. Merge the audit branch `ret/strategy-s1` into main (docs only) and
   commit the current working-tree doc set (plan v1.8, strategy v1.1,
   this brief). Verify main is the single source; delete merged branch.
2. Record §C rulings → RULINGS_ADOPTED.md.
3. **§9.1 safety items S-1..S-5** (the ONLY production code in W0): PII
   scrub + gate extension; 13-file fail-closed token via one shared guard;
   plan-surface entitlement; parity_check disposition; description-hygiene
   scan v1. Deploy. Live-probe the PII fix specifically.
4. Build the §B baseline probe suite + harness; provision the read-only
   DSN (W-18); wire the envelope codegen parity test into CI (GT-8 residual).
**Verifier gate V0:** safety items live-verified; baseline committed; CI
green; main==deployed SHA.

### W1 — Concept Spine + Census (the mapping wave) → HUMAN GATE
Lanes (parallel where marked ∥):
- **L1a ∥ Concept ledger infrastructure** (W-24): `concept_ledger` +
  projection generators + hardcoded-list lint. Descriptor extension design
  from R-1.1 (display/annotations/register/density/mutation/
  projection_tags/family_overrides/data_source/demand_ranking/
  calibration_context_only) — DESIGN + types landed behind the compiler
  flag; full migration of all capabilities happens in W2.
- **L1b ∥ Harvest pipeline** (W-25, E1–E4): extractors, cross-diff,
  adjudication queue. Uses MARSYS direct + DSN for E1/E3 truth.
- **L1c ∥ Service manifests + probes** (W-22 service half): all ~12 sidecar
  routers manifested (`provides_apis`/`health_probe` complete), committed
  OpenAPI surface, `ka_graha_sancara` disposition (W-16) DESIGNED (wired in
  W2), per-engine concurrency caps declared.
- **L1d (after L1b)** Census + reachability matrix v1 (W-20/W-21/W-14/W-15
  /W-23): eight-axis tool census, concept-level coverage, enumeration
  reconciliation (147/158/37 → one generated source), lifecycle states
  assigned, table/service dispositions (SERVED/INTERNAL/RETIRED), dark-set
  wiring PLAN (execution in W2).
- **L1e (after L1d)** **The native review packet** — see §F.
**Verifier gate V1:** matrix completeness (every concept has a state + a
disposition; zero unexplained dark), harvest exceptions all adjudicated or
queued-with-owner, lint live, generators reproduce byte-identical outputs.
Then **STOP → §F human gate.**

### W2 — One Catalog (R-1 + dark-set wiring)
Lanes: descriptor migration of ALL capabilities to the extended contract ∥
projection compiler (chat defs + MCP registrations + census + docs resource
+ per-family schema dialects §7.1 + cache-stable output §7.3) → single
bootstrap (W-1) → alias cutover (W-2, 55+6, one breaking release,
list_changed) ∥ codegen de-mirror (vidhi + session-pin, W-4) ∥ dark-set
wiring per W1 dispositions (W-15/W-16 incl. `ka_graha_sancara`,
`kala_timeline`, CDLM rollups, dasha-windowed remedies, L0 catalog stratum,
mimamsa read candidates) ∥ G-1/S-3/SC-2..5 structural closes (serving-side
only — no writer changes; anything requiring writer work is recorded for a
native-sanctioned build session, must_not_touch holds).
**V2:** compiler parity gates green; census machine-derived (AMBIG-1/2
resolved by construction); live tools/list matches generated projection;
baseline probes improved not regressed; commissioning contract (W-27) CI
live and demonstrated on one asset.

### W3 — One Envelope (R-2)
Lanes: v3 universal + chart_header fail-loud (W-9) ∥ flags closed enum +
d8/hollow-emitter migration (W-6/W-7) ∥ register block + reading_contract +
signal_reader_text editorial pass (C-3; generate draft reader text per
signal class, flag for native polish post-campaign) ∥ cursor fingerprints ∥
budget unification (~36 unclamped, W-5/W-8, result_clipper eviction from
MCP path only) ∥ density_contract 100% + verbosity knob WITH the C-4 guard
∥ demand_ranking + timing hooks + prediction shape (§8 R-2 rows) ∥
response cache (W-28 envelope half: cache-safe determinism + ledger_version
in pin/envelope).
**V3:** schema validation over live tools/call output for the full surface;
W4-rubric battery rerun no-regression; §N.6 checks; trim honesty
adversarial pass.

### W4 — One Planner (R-3)
Sequential core (shared files): decomposed scope tuple (W-10) →
ClarificationRequest third outcome (C-5) → Paripraśna floor adoption WITH
audience_tier excision precondition (C-2; coordinate the excision commit as
its own PR labeled for the Paripraśna workstream) → completeness receipts
on both channels → orientation front-door redesign. Parallel: floor
completeness campaign (career/health/marriage to mandatory tag set; CR-55
resolution W-11; cr_status re-derivation) ∥ floor precompilation (W-28
planner half) ∥ **prashna_ask spike** (C-6/F-R1: question → headless engine
→ synthesized answer; proves the boundary; no transport polish).
**V4:** scope-tuple round-trip for every intent; B.11-by-construction
demonstrated (hardcoded injection deleted); receipts live on both channels;
spike E2E on 1c826d5a; ≤10-call / ≤3-to-first-verdict targets measured.

### W5 — Adaptive Serving + Scale (R-4 + W-29/W-30)
Lanes: surface-spec enforcement + projections live (full/compact≤20/
consult) + profile=OAuth scope ∥ annotations + family_overrides +
input_examples/search_result emissions ∥ tool-search metadata ∥ spine
bundles as post-build materialized views ∥ funnel N+1 batching + pooling/
replica + sidecar memoization/caps ∥ QoS priority classes + fairness +
job queue ∥ listCapabilities filters (W-13) ∥ readback + tool-selection
battery built and baselined across families (incl. concurrency runs, W-31).
**V5:** per-family tools/list conforms in CI; battery scores recorded as
the regression baseline; load test passes the four §9.7 pressure points;
consult profile provably cannot reach raw tools.

### W6 — prashna_ask + Seal (R-5)
prashna_ask full contract (C-1 signature, job-handle + notifications,
cost caps, NO-LEAKAGE arm-2 exclusion F-R7 + CI canary) → resilience/chaos
→ quality-under-load battery at concurrency → session-semantics rename
(W-17) → PARIPRASHNA §6.1 diagram fix (W-19, authorized) → docs seal:
CURRENT_STATE §2 update, SESSION_LOG entries, plan status flip, supersede
stale coverage map (W-15 doc half), CAPABILITY_MANIFEST regeneration.
**V6 (final):** §H below.

## §F — THE HUMAN GATE (only one)

At W1 close the conductor produces the **Native Review Packet**
(`briefs/retrieval_impl/NATIVE_REVIEW_PACKET_W1/`):
1. **Asset & concept map** — every asset/service → the concepts it holds
   (from the harvested ledger), with lifecycle states and dispositions.
2. **Concept → tool mapping** — the reachability matrix rendered readably:
   concept → serving tool(s) → umbrella path → vidhi primitive.
3. **Tool-shape design** — the proposed umbrella/drill/bundle topology and
   the extended descriptor contract, with 3 worked examples (one per §9.6
   lifecycle scenario: existing asset, elevated asset, new asset).
4. **A self-contained HTML visualization** (single file, no build step):
   the layer-wise concept lattice, coverage states color-coded, tool
   topology graph, and the adjudication-queue summary — so the native can
   *see* the system, not read 3,000 rows.
Then STOP with a clear summary message and wait. Resume only on native
approval (any corrections are absorbed as W1 addenda before W2 opens). If
the native replies with approval + corrections, apply corrections first.

## §G — Standards that bind every wave

Plan §2 principles + strategy §3.5/§3.6 + §N.6 + B-series (esp. B.1, B.8,
B.10). Surgical migrations only. No secrets in code or logs. Every PR
message cites its plan row (R-x.y / W-nn / C-n). Descriptions/labels pass
the chart-agnostic + PII gates. Any discovered defect outside scope:
record in the defect register pattern, do not chase. Red-team cadence: the
per-wave verifier discharges it; note in SESSION_LOG entries.

## §H — Final acceptance (campaign COMPLETE)

1. Plan §6 success criteria 1–6 + strategy §7 targets: all green, measured,
   recorded in `briefs/retrieval_impl/FINAL_REPORT.md`.
2. Reachability: 100% concepts at a terminal healthy state
   (PLANNER_KNOWN, or INTERNAL/RETIRED by disposition); drill-crawl zero
   dead ends; commissioning contract demonstrated.
3. Live instrument: full probe suite vs W0 baseline — every intended
   change present, zero unintended regressions; battery baselines stored.
4. All waves verifier-ACCEPTed; every REJECT→fix cycle documented.
5. Git/env hygiene: all lane/wave branches merged + deleted; all worktrees
   removed; main pushed; **main SHA == deployed production SHA**; local
   checkout clean. CURRENT_STATE, SESSION_LOG, this brief's status:
   COMPLETE.
6. Post-campaign handoff note: residuals (e.g. deferred RC-2, OT-5 spike
   findings, writer-side items excluded by must_not_touch, signal_reader
   native-polish queue) listed with owners — nothing silently dropped.

## §I — Coexistence with the doctrine campaign (D-4a → D-5 → D-4b)

Native-approved parallelism policy (2026-07-19):

1. **W0–W1 MAY run in parallel with D-4a.** Scopes are near-disjoint
   (measurement kernel vs harvest/census). Both campaigns declare their
   `may_touch` globs in their STATE ledgers at open; the sole expected
   contact point (A-0 serving-substrate files vs the S-2 token guard) is
   resolved by the retrieval side taking the shared-guard file and the
   doctrine side consuming it.
2. **W2–W3 MUST NOT run concurrently with D-5's serving lane (G-4).**
   Preferred order: W2–W3 land BEFORE D-5's serving lane opens, so
   Gochara-Chitra tools are commissioned under the new contract (compiled
   projections + concept-ledger + W-27 CI) — D-5 becomes the commissioning
   contract's first live test, and D-4b inherits spine bundles + battery.
   If the native sequences D-5 first instead: retrieval pauses at the §F
   gate until G-4 closes, and W2 absorbs the gochara tools in its
   migration. The conductor checks CURRENT_STATE §2 at every wave open and
   enforces this rule.
3. **Deploy mutex.** Only one campaign merges-to-main/deploys in any given
   window; ownership is recorded in both STATE ledgers before deploying.
4. **Baseline re-snapshot.** Whenever the doctrine campaign deploys, the
   retrieval verifier re-snapshots the §B probe baseline before its next
   diff, so intended doctrine changes are never misread as retrieval
   regressions (and vice versa).
5. **Surface ownership while both are active:** doctrine campaign owns
   `kala_*` serving semantics; retrieval owns the plane (registry,
   envelope, budget, edge, planner). Cross-needs are raised as notes in
   the other campaign's ledger, never edited directly.
6. **Breaking-release hold, independent of the deploy mutex (native ruling,
   2026-07-21, W5).** A breaking rename or bootstrap-source cutover (e.g.
   W5 L0's `RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED` default flip — legacy tool
   names stop being served the moment it lands) must NEVER deploy while
   another campaign has a live agent swarm actively executing against the
   deployed connector, even if that campaign's own file footprint is
   disjoint and §I.3's deploy mutex reads clear. The risk isn't a merge
   conflict — it's that the OTHER campaign's live agents may be calling
   the legacy names on the running connector at the exact moment the
   rename takes effect, with no way for those agents to know the rename
   happened mid-flight. This is a strictly narrower, additional gate on
   top of §I.3: §I.3 governs when code may merge/deploy; this item governs
   when a SPECIFIC KIND of already-merged, already-deployable change may
   actually take effect in production. Concretely: the additive nine-tenths
   of a wave carrying a breaking piece MAY split and deploy under §I.3's
   normal mutex rules (per-lane, file-disjoint) the moment the mutex is
   free — the breaking piece itself waits, separately, for an explicit
   confirmation that the other campaign has no live agents currently
   executing (not just "no open PR" — a running swarm can exist without an
   open PR). Precedent: W5's D-5-unpark lane (alias cutover + single-
   bootstrap default) was built, tested, and ready while D-4b was actively
   executing (live gochara-perf branches + concurrent `worktree-agent-*`
   sessions, confirmed via `git branch -a` / `gh pr list`, not assumed);
   it was split onto a held branch (`impl/w5-breaking`) and paused at its
   feature-flag default (back to `false`, fully tested either way) while
   the other ten, non-breaking lanes deployed. Re-check via the same
   evidence class (live branches + open PRs, not a stale STATE.md read)
   immediately before un-pausing.

*End of RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF v1.0 (§I coexistence policy
added 2026-07-19; §I.6 breaking-release hold added 2026-07-21). One
kickoff, one human gate, verified done.*
