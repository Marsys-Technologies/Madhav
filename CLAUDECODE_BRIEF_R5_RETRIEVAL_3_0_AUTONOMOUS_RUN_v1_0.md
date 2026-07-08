---
canonical_id: CLAUDECODE_BRIEF_R5_RETRIEVAL_3_0_AUTONOMOUS_RUN
version: 1.2
status: READY-FOR-KICKOFF — gated on Phase-0 self-checks + the two §7 kickoff-precondition artifacts
created: 2026-07-07
changelog:
  - v1.2 (2026-07-08): PREFLIGHT DELTAS FOLDED (R5_PREFLIGHT_REPORT_v1_0.md, GO verdict, commit
    43e607b6). §7 added — twelve numbered deltas binding on Phase-0/W0 scope. Headlines: mig-325/
    valence-vocab item REPLACED by the real finding (native chart Bodha staleness — canary scoped to
    Abhinandan until native is current); TWO deploy-truth pre-checks added (amjis-mcp 37 commits
    behind; mig 424 undeployed); S6 re-scoped (index EXISTS — planner choice, low priority); S3
    UPGRADED (2.4× measured, not 20-30%); logger one-liner is a telemetry prerequisite; Q1–Q9
    taxonomy must be AUTHORED not extracted; golden-eval assets are NOT a battery seed corpus;
    MARO normalizer is the format-negotiation precedent; footprint baseline = 124 tools/55.6KB/
    ~13.9K tokens (medium confidence); security flag contextualized (M0 gate upstream — narrower
    residual); test credential provisioning = W0a first step (preflight was BLOCKED on it).
  - v1.1 (2026-07-08): ADVERSARIAL-REVIEW AMENDMENTS (native-directed critique; design doc now v1.6 —
    Part VII is additional governing law). Eight mechanics hardenings in §6 below: W0 split for
    progressive value, strangler codegen with parity gates, consumer format negotiation, the battery
    FROZEN and pre-authored by Cowork (never in-run self-authored), Pratinidhi-R dossier-grounded,
    per-wave design-conformance attestation, W0 rollback rehearsal, run burn budget + heartbeat.
    New v1.6 scope absorbed: §31.4 time-sensitivity ladder (Pratinidhi-R implements w/ citations),
    §31.1 tool-list footprint metric, §31.2 selection eval, §32 spec adoptions (outputSchema in W1,
    elicitation in W3, Task-compatible Mahā-Brief in W4).
author: Cowork (Beyond-Acharya program) — native-directed fully-autonomous R5 implementation
program: RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md **v1.5** = THE GOVERNING LAW of this run.
  Parts I–VI are binding: §18 premise verdicts, §19 single-source mandate, §20 fix sites, §21/§25/§30
  wave absorption, §24 SLOs, §28 shastra navigation. No wave may contradict the design doc.
ratification: NATIVE RATIFIES BY KICKOFF — launching this brief ratifies the v1.5 design as governing
  law, incl. the 17-instrument estate, budget seeds (§6), judgment checklist (§28.1), shastra map
  (§28.5), and the min-instances spend (S2, capped: min-instances=1 on amjis-web + amjis-mcp only).
  Record as JL-⟦next⟧ at run open. All in-run judgment rulings carry native retrospective veto.
execution_mode: FULLY AUTONOMOUS — one kickoff, no human gates, conductor + swarm, worktree-isolated,
  per-wave prod deploys, terminal cleanup. Modeled on BA_AUTONOMOUS_RUN_CHARTER_v1_0.md; deltas below.
slots: ⟦HEAD_SHA_AT_KICKOFF⟧ ⟦NEXT_MIGRATION_NUMBERS⟧ ⟦POST_R4_PROBE_RESULTS⟧
may_touch: ["platform/src/lib/retrieval/**", "platform/src/app/api/{retrieval,mcp}/**", "platform-mcp/src/**", "surgical migrations (full-path cited per §20)", "deploy.yml min-instances lines ONLY", "python-sidecar serving modules named in §20 (anchors.py, mitigation.py)", "eval harness + battery assets", "00_ARCHITECTURE run ledgers/reports"]
must_not_touch: ["orchestrator/planner + ALL writers (build plane is sealed)", "chart data (all L0-L5 tables read-only; no chart builds)", "salience/priors/formula constants (frozen)", "LEL rows", "CLAUDE.md/governance protocol files", "anything in deploy.yml beyond the two min-instances flags"]
---

# BRIEF R5-AUTORUN — RETRIEVAL 3.0, ONE KICKOFF TO SEAL

## §1 — SWARM TOPOLOGY (roles; conductor spawns all)

- **CONDUCTOR** — sequences waves, spawns lanes, gate-checks rings, owns the RUN_LEDGER
  (`00_ARCHITECTURE/R5_RUN_LEDGER_v1_0.md`, create at open). Writes no implementation code.
- **PRATINIDHI-R (the authority swarm — the native's no-gate mandate).** A dedicated
  judgment/clarification agent loaded with DEEP context at spawn: the v1.5 design doc (all six parts),
  both Part-IV audit transcripts, the Part-V latency trace, the §14 probe evidence, MCP_CHANNEL_AUDIT,
  the L0 ontologies (shastra map source), and the registry/serving code map. EVERY in-run question,
  ambiguity, confirmation, or judgment routes here — never to the native, never guessed by a lane.
  Constitution (strict precedence): (1) design doc v1.5; (2) pillar order when in tension —
  ASTROLOGY > answer-correctness > honesty > latency/tokens > code convenience; (3) classical citation
  for any astrological call (canonical-or-floor — no uncited substitute, floor with reason);
  (4) mainstream-with-contested-flag for genuinely disputed points. Every ruling → R5_JUDGMENT_LEDGER
  entry (id, question, ruling, basis, reversibility) for native retrospective veto.
- **IMPLEMENTATION LANES** — per-wave subagents in ISOLATED WORKTREES (one worktree per lane, branch
  `r5/w<N>-<lane>`), scoped file lists, no cross-lane file overlap (conductor enforces at spawn).
- **VERIFIER RING** — separate agents, never the implementer: contract-verifier (facet round-trip
  through the seam, §19 codegen integrity), battery-runner (canary + answer rubric; synthesis judged
  via product-policy LLM Gemini/DeepSeek per D-1 — Anthropic stays banned in product paths),
  perf-verifier (p50/p95 vs §24 SLOs vs W0 baseline), astro-verifier (classical-completeness receipts,
  frame correctness, PACT chain honesty — consults Pratinidhi-R on disputes), red-team (Ring 3).

## §2 — WORKTREE + BRANCH + DEPLOY POLICY (the native's mechanics, made precise)

Per wave: branch `r5/w<N>` off main → lanes work in per-lane worktrees off that branch → lane commits
at coherent boundaries (compiling, tested) → Ring-1 lane merge into the wave branch → Ring-2 wave
promotion: verifier ring green → PR to main, CI-gated, merge → **prod deploy** → post-deploy prod
verification re-runs the wave's ACs against LIVE prod (`[verify-against: prod]` — the
worktree-complete-only trap is a named failure mode; ACs verified only in a worktree do not count).
Migrations: surgical, full-path cited (§20 dual-root rule). **Terminal cleanup (Ring 3, mandatory):**
all worktrees removed + `git worktree prune`, all `r5/*` branches deleted after merge, `git branch -r`
= origin/main only, tree clean — cleanup is an EXIT GATE of the run, not housekeeping.

## §3 — PHASES

**PHASE 0 — SELF-GATING PREFLIGHT (the only place the run can decline to start).**
(a) CURRENT_STATE confirms the Phase-4 runway CLOSED (native rebuild done) — if not, HALT-AND-REPORT
(never run retrieval waves against pre-rebuild data or inside the runway's freeze). (b) Re-run the
§14 eight-probe audit against the rebuilt charts over live MCP; record ⟦POST_R4_PROBE_RESULTS⟧ in the
RUN_LEDGER; strike healed findings from W0 scope (expected heals: P2 degenerate band, stale-note
substance, percentile degeneracy); confirm surviving defects. (c) Quiesce check: no other stream
holds prod. (d) Open ledgers, record the ratification-by-kickoff JL entry, spawn Pratinidhi-R.

**W0 — FOUNDATIONS + HONESTY** (design §20/§21/§25). Lanes: (1) punch-list fixes at the named sites —
dead `/api/mcp/db/query` (create-or-repoint), 401 headers, as_of_date mapping, phala serving SQL vs
mig-330 + anchor_id type conflict, valence vocab reconciliation, citation empty-with-reason;
(2) single-source contract codegen (registry descriptor → generated Zod shims + name maps; CI
round-trip test) — THE keystone; (3) unified populated envelope (one shape, both processes, §10
fields incl. chart_header + epistemic + timing); (4) perf quick wins: min-instances (pre-authorized),
serialization tax (measure-without-stringify, no pretty-print, no dual-payload), UCD pre-fetch
parallelization, salience index EXPLAIN+add; (5) canary battery + system_health + p50/p95 baseline.
**Ring-2 gate:** all 8 probes pass or fail honestly on prod; baseline recorded; codegen round-trip green.

**W1 — SQL IDIOM + ADDRESS RESOLVER.** Lanes: (1) the ADDRESS RESOLVER (§27.2 — pure per-chart
function, resolution chains served); (2) chart_query w/ EAV crosstab + `about` facet; (3) dasha_query
(system/level/window facets, as-of semantics); (4) signals_query + synthesis_query on the generated
contract (E-6: digest consumes composite ranking + hierarchical aggregation); (5) budget facet via
wired result_clipper. **Gate:** lagna ≤2KB/1 call · current-dasha ≤1KB/1 call · resolver chains
verified against chart_facts on both charts · facet-conformance suite green · SLOs met.

**W2 — GRAPH + CORPUS IDIOMS + FRAMES.** Lanes: (1) traverse_chart_graph EXT (path patterns,
direction, strength floors, `about` seeds); (2) corpus: hybrid vector+keyword post-401, inline
citations at interpretation intent (top-k≈5 verse-in-hand); (3) `frame` facet (lagna/chandra/arudha/
karakamsha) on positional/strength/signal/judgment surfaces; (4) `paradigm` facet + per-tradition
coherence. **Gate:** 10th-lord→Moon paths = 1 call · from-Moon judgment = 1 facet · citation arrives
with verse text · paradigm unmixed (astro-verifier).

**W3 — THE ASTROLOGICAL SURFACE.** Lanes: (1) `judgment_query` (§28.1 full classical checklist,
graded, receipts); (2) `graha_portrait`; (3) estate consolidation ~70→17 (aliases kept, param names
reconciled per §18, apex folds into judgment_query); (4) shastra map + intent-default tables +
description engineering on the capabilities card; (5) astrologically typed drill_pointers across all
instruments. **Gate:** "how is the marriage?" = ONE judgment_query with complete classical receipt ·
all legacy names still answer (alias regression) · card teaches both protocols.

**W4 — INVESTIGATION HARDENING + TERMINAL SEAL.** Lanes: (1) PACT protocol end-to-end (typed
pointers chain through all four stages; denied-promise halts honestly); (2) coverage stamps →
receipts; (3) session pin serving; (4) FULL battery: ~40 questions × both charts × answer rubrics +
astrological acceptance class + frame-safety canary (the D1 regression) + SLO + utilization ≥90%.
**Ring 3:** red-team pass (adversarial questions: contradictory-header canary, entitlement probes,
paradigm-mixing bait, budget-abuse attempts) → seal report `R5_RETRIEVAL_3_0_SEAL_v1_0.md` (headline
metrics vs W0 baseline) → CURRENT_STATE + SESSION_LOG close → **worktree/branch cleanup gate** →
final native report.

## §4 — HALT CONDITIONS (the only stops; everything else self-heals via Pratinidhi-R)
(1) Phase-0 preflight fails · (2) any prod deploy breaks a previously-green canary and rollback also
fails · (3) an entitlement/security regression (the §23 capability-route flag may be FIXED in-run as
a W0 item if Pratinidhi-R rules it in-scope; it may never be WIDENED) · (4) any write detected against
chart data or frozen constants · (5) Pratinidhi-R deadlock (a question its constitution cannot resolve)
— log, park the lane, continue siblings; report parked items in the seal.
New non-blocking findings → R5_PUNCHLIST, never scope creep. Wave boundaries are strictly serial;
lanes within a wave are parallel.

## §6 — v1.1 MECHANICS AMENDMENTS (binding; supersede conflicting lines above)

1. **W0 SPLITS: W0a then W0b.** W0a = the punch-list fixes + perf quick wins + canary/baseline —
   independently shippable, immediate product value even if the run halts after it. W0b = codegen +
   unified envelope. EVERY wave's Ring-2 report states its standalone-value-if-halted-here.
2. **STRANGLER CODEGEN, never big-bang.** The generated-shim path lands ALONGSIDE handwritten shims;
   instruments migrate one at a time behind a parity gate (recorded request corpus replayed through
   old + generated shim → byte-identical structured content). Handwritten shims are deleted only
   after their instrument's parity gate is green. No single PR regenerates the estate.
3. **CONSUMER FORMAT NEGOTIATION.** Columnar wire format + new envelope are consumer-visible.
   `response_format: legacy | v3` per call, DEFAULT legacy until the W4 battery passes on v3; the
   default flips at seal, legacy retained one deprecation cycle. No silent breaking change to any
   live client (portal, Claude, GPT channel).
4. **THE BATTERY IS FROZEN AND EXTERNAL.** Cowork authors the full battery BEFORE kickoff as a
   committed artifact (`R5_ANSWER_BATTERY_v1_0.md`: ~40 questions × expected-property assertions ×
   deterministic checks first, LLM rubric second, spot dual-graded). The run may ADD regression items
   but may never edit or re-grade existing ones. Kills self-authoring/self-grading bias. **KICKOFF
   PRECONDITION: this artifact exists and is committed.**
5. **PRATINIDHI-R IS DOSSIER-GROUNDED, not context-resident.** Its knowledge lives in a committed
   dossier (`R5_AUTHORITY_DOSSIER_v1_0.md` — Cowork authors pre-kickoff: design §-index, audit
   evidence digests, shastra map, constitution, §31.4 time-sensitivity ladder w/ classical citations).
   Every consultation re-reads the dossier fresh — immune to long-run context decay. **KICKOFF
   PRECONDITION: dossier committed.**
6. **DESIGN-CONFORMANCE ATTESTATION per Ring-2.** The verifier ring re-reads the design sections
   bound to that wave (the §21/§25/§30/Part-VII absorption tables) and attests item-by-item —
   silent scope reinterpretation across five autonomous waves is the failure mode this kills.
7. **ROLLBACK REHEARSAL in W0a.** One deliberate Cloud Run revision-pin rollback exercised and
   timed on amjis-mcp before any deeper wave deploys; the rollback runbook lands in the RUN_LEDGER.
8. **BURN BUDGET + HEARTBEAT.** Soft budgets (wall-clock per wave, subagent-spawn count); each
   Ring-2 report includes burn vs budget; breach = report-and-continue (informational, never a gate)
   unless doubled (then Pratinidhi-R rules on scope trim).

## §7 — v1.2 PREFLIGHT DELTAS (binding; from R5_PREFLIGHT_REPORT_v1_0.md §4, all twelve adopted)

**Phase-0 additions (before W0a):** (P0-i) deploy-truth reconciliation — bring amjis-mcp's deployed
revision current with HEAD and confirm migration 424's status resolved by the runway; NO Ring-2
prod gate is trusted before this. (P0-ii) native-chart Bodha staleness check — if 482012f1's
salience_pctl_in_class/typed-edge columns remain unpopulated (R4 should heal; verify), the canary
battery runs against Abhinandan ONLY, with an honest scope note; no silently-misleading pass/fail.
(P0-iii) provision the test API credential FIRST (the preflight's BLOCKED items — live p50/p95,
protocol negotiation — become W0a's opening measurements).

**Scope corrections:** mig-325/valence-vocab punch-list item DELETED (premise unfounded). S6
re-scoped to verify-planner-behavior (index exists), low priority. S3 PRIORITIZED UP (measured 2.4×
tax). Logger fix (`logger.ts` logs method not tool name) = one-line W0a prerequisite for all §31.6
telemetry. Security ticket to MCP-elevation carries the M0-gate-upstream nuance (narrower residual,
not an open door).

**Battery/dossier consequences (Cowork-side, pre-kickoff):** Q1–Q9 taxonomy AUTHORED from scratch
inside the battery artifact (it was only ever referenced, never written); golden-eval assets are NOT
a seed corpus (stale, legacy-named — battery written fresh against the 124-tool reality); shastra
map scoped as a BUILD in W3's lane estimate (L0 ontologies carry 22 event classes, not the full
correspondence set — Pratinidhi-R fills gaps with cited rulings). Format negotiation cites the MARO
normalizer precedent. Footprint baseline recorded: 124 tools / 55.6KB / ~13.9K tokens (medium
confidence; W1 re-measures).

## §5 — STANDING RULES
Design doc v1.5 is law; §18 verdicts bind implementation choices; migrations full-path cited; every
AC `[verify-against: prod | repo | battery | ledger]`; verifier ≠ implementer, always; scoring/eval
paths LLM-free except the battery's synthesis step (Gemini/DeepSeek); envelope changes additive only;
checkpoint report to the native at each Ring-2 close (informational — the run does NOT wait for a
reply); ledgers append-only.
