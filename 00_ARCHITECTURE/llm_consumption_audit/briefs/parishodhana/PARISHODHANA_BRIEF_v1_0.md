---
artifact: PARISHODHANA_BRIEF (Full Reconciliation + Clean Sweep)
canonical_id: PARISHODHANA_BRIEF
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-07-27
author: Fable (Cowork planning session)
source_documents:
  - 00_ARCHITECTURE/llm_consumption_audit/PROGRAM_LEDGER_AND_ELEVATION_ROADMAP_v1_0.md
    (THE work order — §0 is the mission's premise, §1 the item inventory, §3 the phase plan.
     READ IT FIRST AND IN FULL.)
  - LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md (ADDRESSED-v1.2)
  - ELEVATION_REGISTER_v1_0.md · POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md ·
    uat_darpana/UAT_DARPANA_REGISTER_v1_0.md · ledgers/elevation_v2/OVERFLOW_QUEUE.md ·
    capability_map/{DARK_CORPUS_REPORT,OMEGA8_FLOOR_WIRING_PARKED_HONEST}_v1_0.md
mode: >
  FULLY AUTONOMOUS · Conductor (Opus) + a Phase-A verification swarm (8 parallel Sonnet probers)
  + Phase-B builders (Sonnet base; Opus where §5 flags or after 2 failed verify cycles) + ONE
  dedicated Opus Verifier that never writes code + ONE Dvārapāla escalation agent that resolves
  any would-be human gate with a documented conservative decision · no human gates · in-repo git
  worktrees (.worktrees/parishodhana-*) · PR + auto-merge only · explicit deploy with the §6
  traffic discipline · full cleanup · wall-clock cap 10h · PRIME RULE: truth over completion —
  PARKED-HONEST with evidence is a legitimate close for any item.
authorization_grant: >
  Launching this brief authorizes: live read-probes against production for every register item;
  serving-side and planner-side code changes; the Ω8 floor-wiring consumer changes (T1-3); doc/
  register annotation in place; deploy of amjis-mcp. It does NOT authorize: a Bodha (L2) or L1
  rebuild, any write to kala_gochara_windows data, or opening the VIDHI-PŪRṆATĀ /
  GOCHARA-SWEEP-2.0 build waves (those are separate commissions with their own briefs).
---

# PARIŚODHANA — Full Reconciliation and Clean Sweep

## §0 — The premise (why this campaign is verify-first)

The corpus describes ~90 items as open. **It is wrong in both directions and nobody knows by how
much.** Four spot-checks during the ledger sweep found **three already-fixed items still written
as open** — including two labelled CRITICAL (CR-87 hardcoded native constants: fixed, with a
forbidden-token regression test; LCA-2 consult/`reports`: fixed, past tense in the code) and a
register wrongly reported as un-annotated (it reads `status: ADDRESSED-v1.2`).

The post-remediation register names the cause itself: a confirmed drift class,
**"ships-but-register-never-flips"**, ≥3 prior instances. Registers accumulate; nothing sweeps
them when a fix lands elsewhere. The elevation register says so in its own disposition:
*"this register only ACCUMULATES — no item is closed here."*

**Therefore: no builder writes a line of fix code until Phase A has proven the defect is live.**
Building a fix for a defect that no longer exists is the single most likely way to waste this
campaign, and the Verifier will reject any Phase-B work whose Phase-A evidence is missing.

The campaign's deliverable is as much a **reconciled corpus** as a set of fixes: every item ends
with a live-evidenced disposition written back into its source register **in place**, so this
reconciliation never has to be re-derived.

## §1 — Phase A: Reconciliation (blocks Phase B; ~2h; 8 parallel Sonnet probers)

Each prober owns one cluster from the ledger §1, probes **live production** (and the working tree
where the claim is about code), and returns a disposition table. **No code changes in Phase A.**

Every item resolves to exactly one of:
- **LIVE-OPEN** — reproduced against production; evidence attached (call + response excerpt).
- **ALREADY-FIXED (register stale)** — the defect does not reproduce; the fix is identifiable in
  code/history. Evidence: the commit/comment/test that closed it.
- **NOT-REPRODUCIBLE** — cannot be reproduced and no fix is identifiable; state what was tried.
- **NATIVE-GATED** — closure requires the native (ledger Tier 3); no further action.

| Prober | Cluster (ledger §1 Tier 2 unless noted) | Notes for the prober |
|---|---|---|
| **A1** | Receipt-honesty — CR-1, CR-2, CR-63, AS-1 (R-38/R-41 deployed-channel hole) | **Strong false-alarm candidate:** a live deep-dive on 2026-07-26 saw `varga_confirmed: D10✓/D2✓` **with** populated per-varga dignity rows, contradicting CR-2. Check `timing_hooks` population directly. |
| **A2** | Empty-join — CR-5 (`active_dasha_periods_jsonb: []`), CR-12 (0 activated yogas / 3y), CR-48 (`activation_start: null`), CR-37 | Several plausibly closed by D-2/D-3. `kala_yoga_activation_get` served dated windows in a live 2026-07-26 probe — verify. |
| **A3** | Filter-fallthrough — CR-42 (4 `ref_*` tools silently ignoring documented filters — *"worst defect class in the estate"*), CR-10, **`mimamsa_lel_query` `query`/`offset`** | The `lel_query` member is independently re-confirmed live (identical `result_hash` across differing inputs) and deferred across **four** campaigns — treat as LIVE-OPEN unless it now reproduces clean. |
| **A4** | Decorative data — CR-72 (`dosha_label` decorative, 22 rows), CR-73 (labels astrologically false, no cancellation check), CR-74 (Kāla-Sarpa label vs computed per-varga fact) | Partially closed by EL-18; verify **per-dosha**, especially Kuja/Manglik. |
| **A5** | Wealth-layer emptiness — CR-19/CR-66/EL-17 (**zero** wealth-domain L4 phala anchors, re-confirmed 3×), CR-20/CR-67 (`bo_upaya` wealth resonances 0), R-09 (`associated_doshas_array` + `estimated_cost_inr_range_jsonb` 100% NULL), R-10 (`leverage_index` absent from response shape) | The 0/64 wealth anchors persisted **through a completed rebuild** — if still LIVE-OPEN, root-cause why a rebuild yields zero. |
| **A6** | Sidecar/auth + bundle honesty — CR-8, CR-9 (registry inventory tools 401), CR-40, AS-7, CR-39/CR-14 (`holistic_bundle` 5/8 sub-tools erroring under `ok`) | ŚODHANA T2 shipped `status: degraded` on the envelope — **verify whether the sub-tools themselves were repaired or only the disclosure.** |
| **A7** | Small serving residuals — R-08 (`mechanism_retrodiction_get` unresolvable — *note it IS in the current tool catalog, likely stale*), R-27/EL-19 (bare `saham` alias), R-29/EL-51 (`chart_id` filter + `maraka_contraindication_verdict` sub-field), R-42/EL-58 (**SQL already written, needs running**), R-43/EL-60a, R-44, EL-31 (`query_house` never built), EL-07 (15 ungrounded absence candidates) | Highest expected false-alarm rate. Several are ready-to-ship rather than open. |
| **A8** | Tier-1 confirmations + second-chart coverage — T1-2 (dark corpus, re-measure headline vs final head), T1-3 (Ω8 floor state), T1-7 (CR-81 inert class-prior, CR-82 tier-ceiling — **grep the literal `1.0` and `_tier_ceiling_for`**), T1-8 (CR-84/85/86 CGM), T1-11 (gochara health event class), chart `1c826d5a` staleness | Confirm the structural items are still structurally true before Phase B commits to the reachability triangle. |

**Phase A output (Conductor assembles):** `PARISHODHANA_RECONCILIATION_v1_0.md` — one row per item,
disposition, evidence, and the Phase-B assignment (or none). **Annotation is mandatory and part of
Phase A**, not deferred: every `ALREADY-FIXED` item gets an append-only annotation in its source
register naming the closing evidence. This is the anti-drift deliverable.

## §2 — Phase B: Fix what Phase A confirmed

### B1 · Cluster fixes (Sonnet ×N, one worktree per cluster, scoped by Phase A)
Only LIVE-OPEN items. Batch by cluster so related fixes share a PR. Each fix ships with a
regression test that would have caught the defect. If a cluster comes back fully ALREADY-FIXED,
that builder is not spawned — say so in the report rather than inventing work.

### B2 · The reachability triangle (design: Opus · impl: Sonnet, effort high) — the campaign's centerpiece
Ledger T1-1 + T1-3 + T1-2 are one problem: the instrument computes ~12,450 wealth concepts and
serves ~700 (5.58% bright; career 8.47%).

1. **Discoverability (T1-1).** Make `dossier` reachable: surface it in the served MCP catalog and
   the live `tool_search` index (γ proved a tool-searching agent currently cannot find it), and
   **implement γ's named bridge, which no document owns** — have `assess_wealth` /
   `assess_career` / `judgment_query` route through or inline dossier's coverage so the naive
   consumer gets completeness without knowing to ask. This composes with, and must not regress,
   SAMĀPANA's `reading_depth: deep_dive` contract.
2. **Ω8 floor wiring (T1-3).** Land the five parked edits in **both** consumer copies —
   `platform/src/lib/vidhi/registry_data.ts` **and** the DB seed (migration-440 lineage,
   `bg_vidhi_primitives.py` / `bg_vidhi_floors.py`) — from `REGENERATED_FLOORS_v1_0.json`:
   per-domain `floor_vargas` (wealth D1/D2/D9/D11, career D1/D9/D10, marriage D1/D9, health
   D1/D6/D9/D30, spirituality D1/D9/D20, education D1/D9/D24, progeny D1/D7/D9); `ashtakavarga_scan`
   across the full per-varga family (504 concepts/domain); `special_lagna_read` widened to 7 lagnas
   + 70 sahams + Upapada (78 concepts); and register the four unwired primitives — `argala_read`
   (1044/domain), `dispositor_closure_read` (607/domain), `mechanism_read` 10-class set,
   `cross_ayanamsha_agreement`. Re-run the generator + `check_floor_coverage.mjs` → **14/14 PASS**.
   **Add the CI gate** so the two copies can never drift again (its absence is why this parked).
   *Read `BRIEF_VIDHI_PURNATA_v1_0.md` §1 first — it documents the three-copy trap and the
   `codegen:vidhi` + parity-test flow. This track touches the registry data ONLY; it does not open
   the VIDHI-PŪRṆATĀ wave.*
3. **Re-measure (T1-2).** After 1+2 deploy, re-run the dark-corpus measurement for wealth and
   career on **both** canonical charts against the final head — the existing report is stale
   (pre-dates a merge that changed `assess_*` content) and covered only one chart. Report the new
   bright/dark numbers honestly, whatever they are.

**Acceptance (Verifier, live):** a naive single-turn "how is my wealth?" through the **unmodified**
sealed harness reaches materially more of the frozen concept list than the 11/13 baseline;
`tool_search` surfaces `dossier`; floor coverage 14/14 with the CI gate present and failing on an
induced drift; dark-corpus bright % measurably improved on both charts. **If the flagship bar
still isn't met, PARK-HONEST with the new number** — a real improvement honestly disclosed beats a
forced one (the standing W7 pattern).

### B3 · Ready-to-ship (Sonnet, effort low)
R-42's already-written `lapsed_unobserved` migration; the bare `saham` serving alias; the
`ref_remedies_chart_get` `chart_id` filter in `register_d7_channel.ts`; the last 2
`STRICT_SCHEMA_GATE_EXCLUDED_TOOL_NAMES` entries; the 8 stale local arc branches; the stale
`defect_001_alert` prose; `bodha_discoveries_get`'s misleading deprecated-alias `judgment_flags`;
`ka_avadhi.py`'s stale `_DASHA_SYSTEMS` tuple. Each trivially verifiable; batch into one or two PRs.

## §3 — Phase C: Institutionalize (so §0 never recurs)

1. **Reconciliation cadence** — implement the drift class's own prescribed fix: a scheduled check
   that greps every `known_gap: 'CR-N'` / register-cited defect id against live disposition and
   reports divergence. This is the mechanism that keeps the Phase-A work true.
2. **Deploy-pipeline parity** — give `amjis-mcp` the `--no-traffic` → smoke → promote pattern
   `amjis-web` already has, with a **Secret-Manager-held verification token** (its absence is the
   structural reason a real pre-traffic canary was impossible and the traffic-pin class recurred
   twice). Assert the service tracks **LATEST**, never a pinned revision name.
3. **Certify the harness graders** — execute `evals/k2/consumption_grader.ts` and
   `evals/r5-w4-full-battery/llm_grader.ts` rather than manual good-faith grading, and
   **reconcile the two disagreeing baselines** (2/13 naive-routing vs ≥12/13 dossier-paging).
   Until this lands, "11/13 against the 12/13 bar" is not a well-posed statement — say which
   consumer regime the bar describes, in the harness doc.

## §4 — Explicitly OUT of scope (named so the swarm doesn't absorb them)

VIDHI-PŪRṆATĀ and GOCHARA-SWEEP-2.0 build waves (separate commissions) · any L1/L2 rebuild ·
KP sub-lord engine · gochara health event class · near-miss yoga detection · birth-time
rectification · WL-7/WL-8 native data · the T3 native-gated rulings (N5 lock granularity, CR-23
doctrine, EL-25 ratification, β's authorization-chain concern). Carry each into the close report's
open list — do not silently drop them.

## §5 — Swarm topology, model & effort policy

- **Conductor (Opus)** — Phase-A dispatch, disposition assembly, Phase-B scoping from A's output,
  merge order, deploy, cleanup, close. Writes no feature code.
- **Phase-A probers: Sonnet, effort low-medium.** This is disciplined probing, not judgment.
- **Phase-B builders: Sonnet.** Opus for **B2's design** only, or by step-up rule: **2 failed
  Verifier cycles on the same item → re-spawn as Opus.** Effort medium default; high only for B2
  and the Verifier's final battery; low for B3 and mechanical annotation.
- **Verifier: ONE Opus agent, never writes code.** Accepts against LIVE production post-deploy.
  Four dispositions, no "passed with caveats." **Rejects any Phase-B item lacking Phase-A
  evidence.**
- **Dvārapāla (Sonnet)** — resolves any would-be human gate with a documented conservative
  decision logged in the report's `decisions[]`. Bias: PARKED-HONEST over irreversible action.

## §6 — Rails (absolute)

1. **Untouchables:** `kala_gochara_windows` data · `build_substep_progress` · the sealed evaluator
   harness (Phase C *runs* the graders; it never modifies the harness, its prompts, or its grading
   list — a fix requiring a grader change is not a fix).
2. **No rebuilds.** No L1 or L2 (Bodha) rebuild under this authorization. Serving-, planner-, and
   registry-data-side only, plus the one already-written migration in B3.
3. **Verify-before-fix.** No Phase-B change without a Phase-A LIVE-OPEN disposition.
4. **Git:** main is protected (4 required checks, enforce_admins) — PR + auto-merge ONLY, never a
   direct push. Branches `parishodhana/<phase>-<slug>`; worktrees under `.worktrees/parishodhana-*`,
   removed at close. **Never spawn a builder from inside a worktree** (β's isolation incident).
5. **Deploy discipline (the twice-learned lesson):** build the candidate from **merged main** →
   verify with a **real authenticated call** and check the response correlates to the new build →
   canary → cutover → confirm traffic tracks **LATEST, not a pinned revision**. A green CI badge
   is not evidence of anything.
6. **Any registration-time gate/monkeypatch needs an integration test against the REAL SDK**, not a
   mock (the #812 crash-loop shipped because its test used a mock).
7. **Merge-state ≠ verification state.** The close ledger asserts both separately; "Verifier-PASSED"
   never implies merged (γ's process error 2). Likewise **verify agent state directly** rather than
   trusting the Conductor's own todo list (γ's process error 1).
8. **Annotate in place, append-only.** Never rewrite an original observation; add a dated
   annotation beneath it.
9. **No fabrication.** Honest-empty over invented data; LEL entries are native-only; if a probe
   can't run, say so rather than inferring the result.
10. **Preserve-list regression check** after every merge (chart_snapshot, judgment_query
    decomposition, special lagnas, AV gating, kala_windows families, yoga-firings grounds_jsonb,
    gemstone acharya-review gating, the honesty-field vocabulary).

## §7 — Close protocol

1. All PRs merged; `amjis-mcp` deployed per §6.5; production == main HEAD confirmed by a real
   authenticated call; traffic on LATEST.
2. `.worktrees/parishodhana-*` removed; branches deleted; `git status` clean.
3. **`PARISHODHANA_RECONCILIATION_v1_0.md`** — the full disposition table (every ledger item, one
   row, with evidence). This is the campaign's primary artifact.
4. **`PARISHODHANA_REPORT_v1_0.md`** — phase outcomes, `decisions[]`, deploy revisions, the new
   dark-corpus numbers, the certified harness numbers + baseline reconciliation, preserve-list
   result, and the carried-forward open list (§4 + anything PARKED).
5. Source registers annotated in place; `PROGRAM_LEDGER_AND_ELEVATION_ROADMAP_v1_0.md` updated to
   v1.1 with each item's final disposition, so it remains the single "what is actually open" doc.
6. Consumption register → ADDRESSED-v2 if any of its items moved.

## §D — Kickoff prompt (single paste)

```
You are the CONDUCTOR of PARIŚODHANA (Full Reconciliation + Clean Sweep), FULLY AUTONOMOUS, no
human available. Read, in order:
(1) 00_ARCHITECTURE/llm_consumption_audit/briefs/parishodhana/PARISHODHANA_BRIEF_v1_0.md — this
    brief; its §0 premise and §6 rails BIND you;
(2) 00_ARCHITECTURE/llm_consumption_audit/PROGRAM_LEDGER_AND_ELEVATION_ROADMAP_v1_0.md — the work
    order: §0 explains why this is verify-first, §1 is the item inventory, §3 the phase plan;
(3) the source registers it cites, as needed per cluster.
THE PREMISE: the registers are provably wrong in BOTH directions — three of four spot-checked
"critical open" items were already fixed and never annotated. NO BUILDER WRITES FIX CODE UNTIL
PHASE A PROVES THE DEFECT IS LIVE; the Verifier rejects any fix lacking Phase-A evidence.
Execute Phase A: eight parallel Sonnet probers (A1..A8 per §1), live probes only, no code changes,
each item dispositioned LIVE-OPEN / ALREADY-FIXED / NOT-REPRODUCIBLE / NATIVE-GATED with evidence,
and every ALREADY-FIXED annotated append-only into its source register. Assemble
PARISHODHANA_RECONCILIATION_v1_0.md. Then Phase B in parallel Sonnet builders in
.worktrees/parishodhana-*: B1 cluster fixes (only LIVE-OPEN items), B2 the reachability triangle
(Opus design — dossier discoverability + tool_search index + the assess_*/judgment_query inline-
coverage bridge, Ω8 floor wiring in BOTH consumer copies to 14/14 with a new CI drift gate, then
re-measure dark corpus on both canonical charts), B3 ready-to-ship trivia. Then Phase C:
reconciliation cadence, amjis-mcp --no-traffic→smoke→promote parity with a Secret-Manager token,
and certify the harness graders + reconcile the two disagreeing baselines.
ONE Opus Verifier that never writes code accepts every item against LIVE production post-deploy —
four dispositions, no "passed with caveats". ONE Dvārapāla resolves any would-be human gate with a
documented conservative decision. PR + auto-merge only (main is protected); deploy amjis-mcp
explicitly via merged-main → real authenticated verify → canary → cutover, and CONFIRM traffic
tracks LATEST not a pinned revision. Untouchables: kala_gochara_windows data,
build_substep_progress, the sealed evaluator harness (run the graders, never modify them). NO L1
or L2 rebuild. Never touch root CLAUDECODE_BRIEF.md. Never spawn a builder from inside a worktree.
Wall-clock cap 10h. Close per §7 with both artifacts, registers annotated in place, the ledger
bumped to v1.1, worktrees/branches cleaned, production == main. Truth over completion — a
PARKED-HONEST with evidence beats a false close. Begin.
```

---

*The one-line version: prove what is actually broken before fixing anything, close the gap between
what the instrument computes and what it serves, and leave behind a mechanism that keeps the
registers honest — so the next session can trust the documents instead of re-deriving the truth.*
