---
artifact: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md
canonical_id: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF
version: 1.0
status: COMPLETE
closed_on: 2026-07-23 (RC-14 closure addendum: 2026-07-23, follow-on session)
closure_summary: >
  All 17 residuals (RC-01..RC-16 plus RC-17, discovered mid-campaign per §G)
  are CLOSED with cited, independently-verified evidence — zero residuals
  remaining. RC-14 (the impl/w5-breaking alias-cutover + single-bootstrap
  flip + query_spine_bundle activation) was left BLOCKED at this brief's
  original 2026-07-22/23 seal per §D.6/§J's own anticipated exception
  (D-4b genuinely active throughout that window), then CLOSED in a
  dedicated 2026-07-23 follow-on session once D-4b's campaign-close commit
  (cd5ad175) landed and was live-reverified quiet. Per native correction,
  impl/w5-breaking (found ~178 commits stale) was never landed directly —
  the flip was re-implemented fresh on res/rc14-breaking-flip against
  current main, reconciled live against canonical_faces.json rather than
  trusting the stale branch's targets, merged PR #726 (7a0954b4). Live
  DONE-bar evidence: all 43 legacy MCP tool names + the 6 pre-rename
  originals return "not found"; the 6 DEFERRED renames resolve live; a
  direct /api/retrieval/capability call returned query_spine_bundle's real
  pre-joined signal->window->anchor chain for chart 482012f1; a stale
  client_capability_version triggered a live tools/list_changed
  notification. §H final gate passes: main SHA (7a0954b4) == deployed
  amjis-web AND amjis-mcp production SHA (gcloud-verified, both services
  now current since RC-14 touched platform-mcp/); impl/w5-breaking and
  res/rc14-breaking-flip deleted local+origin; zero res/* branches remain;
  worktrees clean. Full record:
  00_ARCHITECTURE/briefs/retrieval_residual/STATE.md,
  00_ARCHITECTURE/briefs/retrieval_residual/RESIDUAL_CLOSURE_FINAL_REPORT.md
  (§2 RC-14 row + §8 addendum).
type: CLAUDECODE_BRIEF (governing scope for the residual-closure campaign)
authored_by: Claude (Cowork, Fable 5) 2026-07-22, native-directed
authority: >
  Native directive 2026-07-22. Mandate: close EVERY residual left by the
  Retrieval Plane Elevation campaign (W0–W6 + W6.1/6.2/6.3) so that nothing
  is deferred to "post-campaign." The campaign flips to COMPLETE only when
  zero residuals remain open. This brief governs every session launched
  against it; its may_touch/must_not_touch override all other scope guidance.
  The root CLAUDECODE_BRIEF.md (doctrine-wave pointer) does NOT govern this
  session; do not modify it; do not open or touch the D-4b doctrine campaign
  except under the read-only coexistence rules in §J.
run_mode: >
  FULLY AUTONOMOUS — conductor + multi-agent verifier-gated swarm, NO human
  intervention. Any input a task needs is supplied by a dedicated swarm agent
  (the "Native-Proxy Resolver," §D.5), not by pausing for the native. Native
  runs with bypass permissions. Everything recorded; commits are checkpoints;
  a task is DONE only when its dedicated VERIFIER agent returns ACCEPT with
  cited evidence.
source_of_residuals: >
  00_ARCHITECTURE/briefs/retrieval_impl/FINAL_REPORT.md §H.6 (R-1..R-10) +
  the three W6.x fix-cycle findings (dead-tool class, synthesis truncation,
  synthesis cost-cap) + §H.1 criterion-6 live parity + §H.2/§H.3 re-verify.
  This brief is the authoritative closure tracker; FINAL_REPORT §H.6 is its
  input, not a competing list.
may_touch:
  - "platform/** and platform-mcp/** source (this IS the implementation campaign)"
  - "platform/supabase/migrations/** (surgical only, §N.4; none expected — flag if one seems needed)"
  - "00_ARCHITECTURE/briefs/retrieval_residual/** (NEW — all lane artifacts, ledger, reports)"
  - "00_ARCHITECTURE/briefs/retrieval_impl/FINAL_REPORT.md + STATE.md (residual status updates)"
  - "00_ARCHITECTURE/RETRIEVAL_*.md (only if a residual mandates a doctrine amendment)"
  - "00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (W-17 naming coordination only)"
  - "00_ARCHITECTURE/CURRENT_STATE_v1_0.md, SESSION_LOG.md (append/close)"
  - "00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md (CR-118 / defect status)"
  - "git branches/worktrees for this campaign; merge to main; push; deploy per §I"
  - "platform/tests/eval/** (load battery, golden set recalibration)"
  - "PLANNER_PROMPT_v2_x.md (dead-tool sweep, §E R-DEAD)"
must_not_touch:
  - "FROZEN orchestrator + WriterBase + ga_*/bo_*/ka_*/ph_*/mi_* writer build logic (§N.2)"
  - "CLAUDECODE_BRIEF.md (root); the D-4b doctrine-wave briefs/ledgers/branches (READ-ONLY, §J)"
  - "chart_facts semantics / chart computation; LEL content"
  - "kala_*/gochara serving semantics owned by the doctrine campaign (§J §I.5 line)"
status_field_semantics: >
  status: COMPLETE only when EVERY residual row in §E is VERIFIER-ACCEPTED or
  formally native-proxy-dispositioned as WONTFIX-with-rationale, the §H final
  gate passes, main == production, and the environment is clean.
---

# Retrieval Plane Elevation — Residual Closure Brief

## §A — Mission

Close every residual from the Retrieval Plane Elevation campaign so the
campaign can flip to COMPLETE with an **empty residual register**. Native
directive 2026-07-22: nothing is deferred to "post-campaign." Each residual
is either (a) implemented + verifier-accepted + deployed, or (b) formally
dispositioned WONTFIX/NOT-APPLICABLE by the Native-Proxy Resolver (§D.5) with
a written, evidence-backed rationale recorded in the ledger. There is no
third state. "Carried forward" is not permitted.

## §B — Mandatory context load (before any work)

Read in order: `CLAUDE.md` (v6.4); `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2
(campaign position — **D-4b doctrine campaign is ACTIVE**, this is the
parallel infra track); `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md` (v1.8 — the
built plan, §9 registers); `RETRIEVAL_STRATEGY_v1_0.md` (v1.1 — §3.5/§3.6/§5,
§9.7 QoS doctrine, §N.6); `briefs/retrieval_impl/FINAL_REPORT.md` (**the
residual source, §H.6 R-1..R-10**) and its `STATE.md` (the full W0–W6.3
ledger — read the W4/W5/W6 close sections and every R-n origin); the
`GROUND_TRUTH_REGISTER.md` (GT-F28/W-17, dead-tool findings);
`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (CR-118). Do not relitigate settled
findings; verify their current status and close them.

## §C — The live instrument (leverage continuously)

The deployed MARSYS-JIS MCP connector + the `amjis-web`/`amjis-mcp` Cloud Run
services are the verification ground truth. Every residual whose acceptance
is "works live" is proven against the DEPLOYED connector, not local tests
alone. The conductor's environment must establish an authenticated
connector/API-key session (see R-1 in §E — this is itself residual work: if
no credential is reachable, the Native-Proxy Resolver provisions a
scoped test/service key rather than deferring). NOTE FROM COWORK: the native
independently confirmed `prashna_ask` end-to-end live on 2026-07-22 (job
`cbc2a8d8-e089-4fea-b19c-b3e37f75c774`, chart 482012f1): `unresolved_tools:[]`,
timing correctly anchored to Mercury MD / Saturn AD, real 5,991-char grounded
reading — R-1's prashna_ask leg is ALREADY functionally verified; this
campaign formalizes and records it (and closes the load-test + probe-suite
legs bundled under R-1/R-2/R-3).

## §D — Execution model

**Conductor + verifier-gated swarm.** The kickoff session is the conductor;
it implements nothing itself — it plans, spawns lane + verifier agents,
integrates, commits, merges, deploys, and keeps the ledger
(`00_ARCHITECTURE/briefs/retrieval_residual/STATE.md`).

1. **Isolation:** each residual (or tight cluster) runs in its own
   worktree/branch `res/<id>-<slug>`; lane → wave-integration branch
   `res/integration` → main. Merge to main only after that residual's
   verifier ACCEPT.
2. **Parallel vs sequential:** the §F dependency graph governs. Independent
   residuals run as parallel subagents in one message; file-colliding or
   dependency-linked ones serialize. Maximize parallelism within the graph.
3. **Model/effort selection (conductor's judgment, per task):** fable/opus +
   high effort for design-heavy or judgment work (dead-tool sweep semantics,
   dark-table dispositions, load-threshold setting, W-17 naming); sonnet for
   mechanical multi-file edits and test authoring; cheap models for
   grep/scout. Verifiers are ALWAYS opus-or-stronger, high effort, and NEVER
   the agent that implemented the thing they verify. Log every model/effort
   choice in the ledger.
4. **"Done = verified" (non-negotiable):** every residual ships with tests;
   every residual closes only when a dedicated independent VERIFIER agent
   (a) reruns tests + CI, (b) runs the live-connector probe where acceptance
   is "works live," (c) checks the residual's specific acceptance criteria
   from §E verbatim, (d) adversarially hunts the residual's likely failure
   mode. Verdict + evidence → `retrieval_residual/VERIFY_<id>.md`. REJECT →
   conductor respawns fix cycles until ACCEPT; every cycle logged.
5. **Native-Proxy Resolver (the "no human intervention" mechanism):** a
   dedicated high-effort (opus/fable) swarm agent empowered to make the
   rulings the native would otherwise be asked for — bounded strictly by
   written policy: it may (i) provision scoped test/service credentials for
   live verification; (ii) set load-test thresholds by deriving them from the
   first real run as the baseline (per R-2's own note); (iii) rule W-17 and
   dead-tool substitutions using the doctrine already on record
   (RETRIEVAL_STRATEGY, §N.6, the WP-1.7 dead-capability precedent, the
   five-state coverage taxonomy); (iv) disposition dark tables using the
   native's already-ruled five-state taxonomy (SERVED-DIRECT / SERVED-VIA /
   OPERATIONAL / GATED / RETIRED, default-bias SERVE). It MAY NOT: change
   frozen contracts, weaken a security control, or mark a residual WONTFIX
   without a written rationale citing existing doctrine. Every Resolver ruling
   is recorded in `retrieval_residual/RESOLVER_RULINGS.md` with its policy
   citation and is itself subject to verifier review.
6. **Failure discipline:** a stalled agent is respawned once with narrowed
   scope; twice-failed work is re-planned by the conductor (fable/high).
   A residual that genuinely cannot be closed autonomously (e.g. requires a
   credential the Resolver cannot mint, or a frozen-contract change) is
   marked BLOCKED with the exact blocker and the single question the native
   must answer — and is the ONLY class of item allowed to remain open at
   campaign end, surfaced loudly at the top of the final report.
7. **Ledger:** `retrieval_residual/STATE.md` — every residual's status,
   branch, commits, deploys, model/effort, verifier verdict, resolver
   rulings, anomalies. Updated + committed at every transition.

## §E — The residual register (every item; each is a closable unit)

Legend for acceptance: each row states its DONE bar. A residual closes on
that bar being VERIFIER-ACCEPTED, or on a Resolver WONTFIX with rationale.

### Cluster 1 — Live verification (R-1, R-2, R-3, §H.1-crit-6)

- **RC-01 (R-1) — Authenticated live E2E, formalized.** Establish an
  authenticated connector session (Resolver provisions a scoped key if none
  reachable). Run `prashna_ask`→`prashna_status` full round-trip on a
  non-native chart (Abhinandan `1c826d5a`) AND re-confirm on native
  `482012f1`. **DONE:** both return a synthesized reading (`reading` +
  `chart_header` populated), correct dasha anchoring, `unresolved_tools:[]`,
  NO-LEAKAGE flag present, completeness receipt intact; transcript saved.
  (Native already confirmed the native-chart leg 2026-07-22 — record it and
  add the 1c826d5a leg.)
- **RC-02 (§H.1 crit-6) — Live two-door parity.** Fire the identical question
  at `/api/chat/consult` (Paripraśna door) and `prashna_ask` (MCP door); diff
  the resulting floor, receipts, and gate flags. **DONE:** the two responses
  carry the same floor item set + same gate flags (prose may differ; the
  deterministic floor/receipt/gates must match); diff report saved.
- **RC-03 (R-2) — Real §9.7 four-point load test.** Run the built harness
  (`platform/tests/eval/w6_load_battery/`) against the deployed connector at
  the four pressure points (funnel, DB fan-out, sidecar, long-running queue).
  Resolver sets thresholds from this first run as the recorded baseline.
  **DONE:** test executes live, results + newly-set thresholds recorded as
  `W6_LOAD_BASELINE_v1_0.md`; QoS doctrine (§9.7: quality never thinned under
  load) confirmed by inspecting that no floor item was dropped under load.
- **RC-04 (R-3) — Cumulative reachability/census + probe-suite re-run.**
  Re-run the concept census + reachability matrix against the current
  post-W6.3 state (needs Next.js runtime — spawn with runtime access; the
  generator has a `server-only` guard). Re-run the full probe suite vs the
  W0 baseline. **DONE:** 100% concepts at a terminal healthy state (or each
  exception dispositioned via the five-state taxonomy), drill-crawl zero dead
  ends, probe-suite diff shows only intended changes; `CENSUS_v2_0.md` +
  `PROBE_DIFF_v2_0.md` saved.

### Cluster 2 — The dead-capability class (the substantive engineering item)

- **RC-05 (R-DEAD) — Sweep ALL dead-tool floor injections.** `pattern_register`
  was fixed for predictive/career (W6.3) at both sites (compiled_floor_adapter.ts
  + PLANNER_PROMPT_v2_8). `resonance_register` and `cluster_atlas` are the
  identical defect, still MANDATORY in the discovery-class (R-DISC) and
  remedial (R7b) floors — a discovery- or remedy-class query on either door
  will still surface `unresolved_tools`. Sweep BOTH injection sites (code
  adapter + planner prompt) for EVERY dead capability across EVERY query
  class (predictive already done; do discovery, remedial, and audit each
  remaining class against `tool_name_bridge.ts` for any capability with no
  registered backing). Substitute per the W6.3 precedent (use `vector_search`
  where the rule doesn't separately ban it; drop with no substitute where it
  does). **DONE:** a live discovery-class AND a live remedy-class
  `prashna_ask` trace each return `unresolved_tools:[]`; regression tests on
  the floor adapter assert no floor of ANY class contains an unresolvable
  required item; planner prompt version-bumped with changelog.
- **RC-06 (golden set) — `planner_golden_set.json` recalibration.** ~99
  `pattern_register` references, several as `required_tools`. Recalibrate
  each affected gold case per-case (this is judgment work — Resolver rules
  ambiguous cases using the substitution doctrine from RC-05). **DONE:** zero
  dead-capability references remain in the golden set; the planner regression
  gate passes against the recalibrated set; a diff report explains every
  changed case.

### Cluster 3 — Synthesis-stage completion

- **RC-07 (synthesis cost-cap) — Track the synthesis LLM call in
  `CostCapTracker`.** The W6.2 synthesis call currently escapes the dual
  cost-cap enforcement — a cost path outside the caps. Wire it in so both
  the tool-call-count and wall-clock caps (and their fail-honest behavior)
  cover the synthesis stage. **DONE:** a synthesis call that would breach a
  cap degrades honestly (partial reading + completeness receipt + cap
  judgment flag), never silently; regression test proves the synthesis stage
  is inside the cap accounting; live trace shows the synthesis cost recorded.
- **RC-08 (synthesis truncation) — Right-size `synthesis_evidence_truncated`.**
  The flag fires on real readings; investigate whether the 8000-char/item cap
  is too aggressive and starving the synthesis model of load-bearing evidence.
  Tune the cap and/or make truncation bearing-aware (drop lowest-bearing
  evidence first, per §3.5 distillation doctrine — never the verdict-bearing
  rows). **DONE:** a standard deepdive no longer trips the flag OR trips it
  only when genuinely over budget with the highest-bearing evidence retained;
  the dissent/tail rows are provably never the ones truncated; live trace +
  test.

### Cluster 4 — Carried-forward defects and dark data

- **RC-09 (R-8) — Resolve all 51 W1 dark tables.** Confirm each of the 51
  NEEDS-OWNER tables from the W1 census now has a terminal five-state
  disposition (Resolver rules any still-open using the native's ruled
  taxonomy; the two large L5 calibration ledgers = GATED per the native's
  2026-07-22 ruling already on record). **DONE:** zero tables in NEEDS-OWNER;
  `DARK_TABLE_DISPOSITIONS_v3_0.md` shows all 51 terminal; the two mimamsa
  ledgers recorded GATED with the calibration-maturity revisit condition.
- **RC-10 (R-9) — Re-measure the MCP↔web namespace gap.** At W4 close only
  ~4/23 MCP tools had web equivalents (~10% floor coverage); W5's generated
  bridge (Lane L1) likely closed most of it. Measure the CURRENT coverage.
  **DONE:** a real number recorded; if <100%, either close the remaining gap
  (generated-bridge extension) or Resolver-disposition each un-bridged tool
  with rationale; `NAMESPACE_COVERAGE_v2_0.md` saved.
- **RC-11 (R-10 / CR-118) — Close the mid-stream fast-fail tool errors.**
  `msr_sql`, `get_yoga_firings`, `cgm_graph_walk` single-digit-ms fast-fails
  (seen in W4/W6 traces). Root-cause each against LIVE behavior, fix, and
  update the defect register. **DONE:** each of the three resolves cleanly on
  a live trace (no fast-fail); CR-118 marked RESOLVED in
  `MARSYS_DEFECT_GAP_REGISTER` with evidence; regression tests added.
- **RC-12 (R-7) — `authorizeChartAccess` Rule-1 hardening.** super_admin is
  granted any `chart_id` without an existence check first. Add the existence
  check so a non-existent chart_id is rejected even for super_admin (defense
  in depth; pre-existing, carried since W0). **DONE:** super_admin request
  for a non-existent chart_id returns a clean not-found, not a silent grant;
  regression test; existing super_admin flows unaffected.

### Cluster 5 — Naming, breaking release, hygiene

- **RC-13 (R-4 / W-17) — `session_pin` → `provenance_stamp` rename.** Execute
  the rename across the ~13 files. Resolver rules the naming (it was
  NEEDS-RULING only for lack of ratification; the Resolver ratifies using the
  D-16 session-semantics doctrine on record, coordinating the
  PARIPRASHNA_TARGET_ARCHITECTURE §6.x vocabulary in the same change so the
  two don't diverge). Internal-only; zero behavior/contract/UX change.
  **DONE:** rename complete + consistent across code and the PARIPRASHNA doc;
  full suite green (no behavior delta); envelope/pin field consumers updated;
  a grep for the old name outside changelogs returns zero.
- **RC-14 (R-5) — The `impl/w5-breaking` flip (alias cutover + single-bootstrap
  default).** This is the ONLY residual gated on an external condition: the
  D-4b doctrine campaign is ACTIVE (confirmed: `wave/D-4b/*` branches live),
  and §J forbids landing a breaking rename while D-4b agents may be calling
  legacy tool names on the connector. **Closure path:** the conductor
  monitors D-4b at every wave checkpoint (read-only, §J). The moment D-4b is
  genuinely quiet (no open D-4b PRs, no active `wave/D-4b/*` work — verified
  live, not from a stale ledger), land the flip under §J deploy discipline
  (mutex, baseline re-snapshot, `notifications/tools/list_changed`),
  activating the dormant `query_spine_bundle`. **DONE:** flip merged +
  deployed; a live trace shows canonical-only tool names resolving and
  `query_spine_bundle` returning a real pre-joined chain on 482012f1; the 6
  DEFERRED aliases resolved. **If D-4b is STILL active at this campaign's
  final gate:** this is the sole permitted BLOCKED item — surfaced loudly with
  the exact unblock condition ("D-4b quiet"), with the flip fully built,
  tested, and staged on `impl/w5-breaking` ready to land in one command. The
  Resolver may NOT force it while D-4b is live (that would break the other
  campaign's running agents — a safety rule, not a preference).
- **RC-15 (R-6) — Branch/worktree hygiene.** After all above land: delete
  `impl/wave-6`, the merged W6.x fix branches
  (`fix/w6-1-*`, `feat/w6-2-*`, `fix/w6.3-*`), all `res/*` lane branches, and
  every stale worktree. **DONE:** `git worktree list` shows only main (+ any
  legitimately-active D-4b worktrees, which this campaign does not touch); no
  orphaned `res/*` or `w6*` branches on origin.

### Cluster 6 — The seal

- **RC-16 — Final campaign seal.** Only after RC-01..RC-15 are ACCEPTED (or
  RC-14 formally BLOCKED-on-D-4b): update `FINAL_REPORT.md` §H.6 so the
  residual table is EMPTY (every R-n marked CLOSED with its closing evidence,
  or RC-14 as the single documented BLOCKED item); regenerate
  CAPABILITY_MANIFEST; update CURRENT_STATE §2 and SESSION_LOG; flip the
  campaign status to COMPLETE. **DONE:** §H final gate (§H below) passes.

## §F — Dependency graph (drives parallel/sequential scheduling)

- **Wave R-A (parallel, no cross-deps):** RC-05 (dead-tool sweep), RC-07
  (synthesis cost-cap), RC-08 (synthesis truncation), RC-12 (authz hardening),
  RC-13 (W-17 rename). These touch disjoint files; run concurrently.
- **Wave R-B (parallel, after R-A merges where noted):** RC-06 (golden set —
  after RC-05, since substitutions must match), RC-09 (dark tables), RC-10
  (namespace re-measure), RC-11 (CR-118 fast-fails). RC-11 may need a live
  connector (Cluster-1 credential) — sequence after RC-01's credential is
  established.
- **Wave R-C (live verification — after all code residuals deploy):** RC-01,
  RC-02, RC-03, RC-04. These verify the DEPLOYED cumulative state, so they run
  after R-A/R-B have merged + deployed. RC-05's discovery/remedy live traces
  (its DONE bar) fold into this wave.
- **Wave R-D (gated / terminal):** RC-14 (D-4b-gated flip), RC-15 (hygiene,
  after everything merges), RC-16 (seal, last).

Deploys are batched: R-A/R-B land and deploy once (mutex per §J) before Wave
R-C's live verification, so the live probes see the full cumulative fix set.

## §G — Standards (bind every lane and every subagent)

Plan §2 principles; strategy §3.5 (distillation boundary — tools curate, never
generatively summarize; truncation is bearing-aware and lossless-in-
reachability), §3.6 (proportionality), §9.7 (QoS: capacity absorbs load,
quality is never thinned); §N.6 (serving density, honest flags, no hollow
envelopes). Surgical migrations only (none expected — flag if one seems
needed rather than deploying a bulk migration). No secrets in code/logs/
ledger. Every PR cites its RC-id. Descriptions/labels pass the chart-agnostic
+ PII gates. The FROZEN orchestrator/WriterBase is never touched (all
verification machinery sits beside the build). Any defect discovered outside
the residual set is recorded in the defect register and, if in scope of "no
residuals left," opened as a new RC-row rather than deferred.

## §H — Final acceptance (campaign COMPLETE)

1. Every RC-01..RC-16 is VERIFIER-ACCEPTED, or RC-14 is the single formally-
   BLOCKED item (D-4b active) with the flip staged and the unblock condition
   named — nothing else open, nothing "carried forward."
2. `FINAL_REPORT.md` §H.6 residual table is EMPTY (all CLOSED, or RC-14
   BLOCKED-documented); every close carries cited evidence.
3. Live: the full probe suite vs W0 baseline shows only intended changes;
   `prashna_ask` verified live on BOTH charts; two-door parity confirmed;
   load baseline recorded; discovery + remedy classes show no unresolved
   tools.
4. Reachability: 100% concepts terminal-healthy (or dispositioned); zero dead
   ends; commissioning contract still holds.
5. Git/env: all `res/*`, `w6*`, W6.x-fix branches merged + deleted; worktrees
   removed; **main SHA == deployed `amjis-web` AND `amjis-mcp` production
   SHA** (verified via `gcloud run revisions describe` commit-sha labels);
   local checkout clean.
6. CURRENT_STATE §2 + SESSION_LOG updated; campaign status COMPLETE;
   `RESIDUAL_CLOSURE_FINAL_REPORT.md` written, independently fact-checked by a
   second agent against source (the FINAL_REPORT precedent).

## §I — Deploy discipline

Batched deploys (§F): one deploy after R-A/R-B, one after RC-14 if it lands,
one final if the seal changes served code. Each deploy: verify the target
(`amjis-web` and/or `amjis-mcp` — MCP only redeploys if `platform-mcp` source
changed), confirm the Cloud Run revision's commit-sha label == the merged SHA,
re-snapshot the probe baseline. Never deploy while a D-4b deploy is in flight
(§J mutex).

## §J — Coexistence with the ACTIVE D-4b doctrine campaign (READ-ONLY)

D-4b is live (many `wave/D-4b/*` branches). Rules (from the elevation
campaign's own §I.5/§I.6, reaffirmed):

1. **Read-only on D-4b:** never edit its branches, briefs, ledgers, or
   `kala_*`/gochara serving semantics. Cross-needs are raised as notes in the
   doctrine ledger, never direct edits.
2. **Deploy mutex:** only one campaign merges-to-main/deploys in any window;
   ownership recorded in both ledgers before deploying; re-snapshot the probe
   baseline whenever D-4b deploys so its changes aren't misread as retrieval
   regressions.
3. **The breaking flip (RC-14) waits for D-4b quiet — a hard safety rule.** A
   breaking tool-name rename must never deploy while D-4b agents may be
   calling legacy names on the connector. Verified live at each checkpoint,
   not from a stale ledger. This is the one residual permitted to remain
   BLOCKED at campaign end.
4. Additive residuals (everything except RC-14) may merge/deploy under the
   mutex without waiting for D-4b, since they don't rename or remove anything
   D-4b calls.

*End of RETRIEVAL_RESIDUAL_CLOSURE_BRIEF v1.0. One kickoff, verifier-gated,
zero residuals at close — except a single, loudly-surfaced, D-4b-gated flip
if and only if D-4b is still running.*
