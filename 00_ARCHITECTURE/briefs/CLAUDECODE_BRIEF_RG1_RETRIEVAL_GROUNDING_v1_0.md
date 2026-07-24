---
artifact: BRIEF_RG-1
canonical_id: RG1_RETRIEVAL_GROUNDING_BRIEF
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN) — READ-ONLY RE-GROUNDING WAVE
wave: RG-1 — Retrieval / MCP / Data-Plane Re-Grounding
version: 1.0
status: FROZEN — awaiting native kickoff
authored_by: Claude (Cowork) 2026-07-24
governing: >
  00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md (v1.4)
  + ESCALATION_POLICY_v1_0.md (v1.1) + ADJUDICATOR_CHARGE_v1_0.md (v1.1)
predecessors: PG-1, PG-2 (both closed 2026-07-19)
re_grounds: >
  PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.10) and
  briefs/MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md against the working tree AS IT IS
  NOW — after the Retrieval Plane Elevation (W0–W6) + Residual Closure
  (RC-01–RC-17) campaigns landed, and after D-4a/D-5 shipped the Gochara surface.
mode: READ-ONLY on application code. Diagnostic probes permitted (§F2.1). No product writes.
autonomy: FULL — opens on kickoff, closes on REPORT. No human in the loop between.
gate: §G — 10 assertions. Graded on RECONCILIATION completeness, not finding volume.
blocks: >
  Every Paripraśna implementation decision that touches the MCP channel, the
  retrieval plane, or the data plane. The target architecture cannot be
  implemented from registers that are stale in the opposite direction.
---

# RG-1 — Retrieval / MCP / Data-Plane Re-Grounding

## §0 — Orientation

### §0.1 Why this wave exists — the staleness has inverted

PG-1/PG-2 (2026-07-19) ground the target architecture and added `[CORRECTED]`
verdicts saying, correctly at the time, that `prashna_ask`, the registry
projections, and NO-LEAKAGE were **unbuilt**. **Then a full 6-wave Retrieval
Plane Elevation campaign (W0→W6) plus a Retrieval Residual Closure campaign
(RC-01→RC-17) landed and deployed 2026-07-19→07-23, building them.**

So the architecture doc now carries corrections that are **stale in the opposite
direction** — they say "unbuilt" of things that shipped. A Cowork grounding
sweep (2026-07-24) surfaced the deltas but **deliberately did not hand-edit the
register rows**, because correcting a document from a summary rather than the
code is exactly the T-7 failure that started this whole audit chain.

**RG-1 is the grounded version of that fix.** It re-baselines every
MCP/retrieval/data-plane claim against the working tree as it is now, and
produces `PARIPRASHNA_TARGET_ARCHITECTURE` **v0.11**.

### §0.2 The prior work this wave MUST consult (G.10 discipline)

PG-2 was created partly because PG-1 failed to cite existing in-repo
investigations. **RG-1 does not repeat that.** Every lane cites, and reconciles
against, the campaign's own sealed records:

- `00_ARCHITECTURE/briefs/retrieval_impl/STATE.md` — the W0→W6 wave ledger.
- `00_ARCHITECTURE/briefs/retrieval_impl/FINAL_REPORT.md` — `AWAITING_NATIVE_REVIEW`; §H.1 is the built-item table.
- `00_ARCHITECTURE/briefs/RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md` — campaign charter, wave sequence §E.
- `00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` — RC-01→RC-17.
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 — live pointer (current_wave, cross-campaign notes).
- `00_ARCHITECTURE/RETRIEVAL_STRATEGY_v1_0.md`, `RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md`, `RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md`.

**A finding that contradicts a sealed campaign record without citing it is a
lane REJECT.** The point is reconciliation, not a fresh audit from zero.

### §0.3 A caution the wave must hold

The retrieval campaign's `FINAL_REPORT.md` is **`AWAITING_NATIVE_REVIEW`** — code
is merged, deployed, and SHA-verified, but the governance seal has not flipped.
**RG-1 grounds against the deployed code, not the seal.** "Merged and deployed"
is the reality Paripraśna must build on, regardless of whether the V6 gate has
been formally read. Where code and the not-yet-sealed report disagree, **the
code is the ground truth and the disagreement is a finding.**

### §0.4 Autonomy contract

Opens on kickoff, ends with `REPORT_RG-1.md`, no human between. §5 pre-commits
every reachable fork. Read-only means §2 HALT is nearly unreachable.

---

## §1 — Lifecycle, state, cadence

Same 7-step read-only lifecycle as PG-2 (§1). Worktree isolation **enforced**
(the PG-1 lesson): `git worktree list` shows one entry per active lane before
dispatch; a lane committing from the shared checkout is an automatic REJECT.
Wave branch cut from `origin/main`, **fetched not assumed**.

Findings to `deliverables/rg1_findings.jsonl`, append-only, with a
reconciliation field:

```json
{"id":"RG1-0001","lane":"E-1","targets":"A-07",
 "doc_claim":"prashna_ask has ZERO source hits; two doors is one door",
 "current_reality":"BUILT & deployed W6; single-pass job, not agentic loop",
 "verdict":"doc_stale_unbuilt_now_built | doc_stale_built_now_removed | doc_correct | partial",
 "evidence":[{"file":"...","line":123,"quote":"..."}],
 "prior_work_cited":["retrieval_impl/FINAL_REPORT.md:154","STATE.md:2247"],
 "shape_delta":"what shipped differs from what the doc's design assumed, precisely",
 "recommended_correction":"the exact v0.11 edit","confidence":"high|medium|low"}
```

`prior_work_cited` **mandatory and non-empty** where a campaign record exists.
`shape_delta` is the load-bearing field: **"built" is not enough — the wave must
state how what shipped differs from what the architecture assumed**, because
the gap between A-07-as-designed (agentic loop) and prashna_ask-as-shipped
(single-pass job) is exactly the thing that will surprise implementation.

Commit identity `rg1-ground-bot@…`; `chore(rg1/<lane>): … [RG1-BOT]`.

---

## §2 — Model and effort

Opus verification floor absolute.

| Lane | Implementer | Effort | Rationale |
|---|---|---|---|
| E-1 | **opus** | **high** | `prashna_ask` shape reconciliation — the highest-consequence delta; "built vs built-as-designed" is a judgment call |
| E-2 | sonnet | medium | Projection/surface census — mechanical but must be exact |
| E-3 | **opus** | **high** | Planner reconciliation (A-06/`VidhiPlan`/`PlanReceipt`) — namespace-map claims need care |
| E-4 | sonnet | medium | NO-LEAKAGE arm-by-arm; session/provenance tools |
| E-5 | sonnet | medium | Gochara/temporal surface + its operational fragility |
| E-6 | sonnet | low | Data-plane deltas: new migrations, OT-11 ledger state |
| Z-4 | **opus** | **high** | Synthesis → v0.11 |
| *verifiers* | **opus** | **high** | Floor |

---

## §5 — Pre-committed rulings

| # | Fork | **Ruling** |
|---|---|---|
| **PC-1** | Code and the not-yet-sealed `FINAL_REPORT` disagree | **Code wins; the disagreement is a finding.** Ground against what is deployed (§0.3). |
| **PC-2** | A shipped feature is narrower than the architecture's design (e.g. prashna_ask) | **Record both: that it shipped, AND the precise `shape_delta`.** "Built" without the delta is an incomplete finding (G.6). Do not let "it exists" paper over "it is not what §6 assumes." |
| **PC-3** | A doc correction (`[CORRECTED PG-1]`) is now itself stale | **Add a second correction layer** `[RE-GROUNDED RG-1 2026-07-24]` — do not delete PG-1's block. The layered history is the audit trail (D-18). Both errors stay visible. |
| **PC-4** | The `/health` count (79) and `tools/list` count (102) disagree | **Probe both live and reconcile.** State which is the deployed surface, which is profile-expanded, and why they differ. Do not pick one silently. |
| **PC-5** | NO-LEAKAGE arm-1 is still 0% | **Report it plainly as the standing critical gap.** arm-2 shipping does not close A-19; the trust boundary the doc cares about is still open. |
| **PC-6** | The Gochara surface serving gap (`DATABASE_URL not set`) is live | **Record as a current defect** with evidence; do not fix (read-only). It is a data-plane finding for §7, not an RG-1 repair. |
| **PC-7** | OT-11 is still unresolved | **Confirm the three-ledger state and that no choice was made.** `brahma_prospective_ledger` now live changes the inputs, not the decision. Still native's call (PC-8 lineage). |
| **PC-8** | A campaign record is itself wrong about the code | **Trust the code, cite the record, flag the discrepancy.** Sealed records can be stale too — that is the entire premise of this audit chain. |
| **PC-9** | The reconciliation is larger than expected | **Park lanes rather than rush.** A partial-but-grounded v0.11 beats a complete-but-guessed one. Never lower the Opus floor. |
| **PC-10** | A delta is embarrassing to the architecture (a design that shipped differently than proposed) | **Report plainly.** The value is in surprises surfaced now, not at implementation time. |

---

## FROZEN §F1 — Lane map

### Lane E-1 — `prashna_ask`: built-vs-designed reconciliation ⭐

**The single most consequential delta.** A-07/§6.3/§6.4/§6.5 describe "one
agentic loop, two doors." What shipped is narrower.

**Charge — read the actual implementation and state the shape precisely:**

1. `platform/src/app/api/mcp/prashna_ask/route.ts` — the engine route. Confirm:
   is it planner → floor → **sequential dispatch** → **one synthesis LLM call**
   ("single, non-agentic LLM call over the gathered floor evidence"), or a
   multi-turn agentic loop? Quote the synthesis section.
2. `platform-mcp/src/tools/register_prashna_ask.ts` + `register_prashna_status.ts`
   + `prashna_ask_bridge.ts` — the MCP surface. Confirm the job-handle model,
   the in-memory `JobRegistry`, and the documented `notifications/progress`
   undeliverability.
3. **Which pre-commit gates run on this route?** §6.4 stage 9 credits
   `prashna_ask` with grounding gate, register lint, sentinel rewrite. **Are
   they in the route?** Grep the route and its synthesis path for each.
4. **Does it share code with the web consult loop, or is it a parallel
   implementation?** §6.5's design test — "the engine must never branch on which
   door" — is it honoured, or are there two engines?
5. Entitlement: profile-gated (`consult` rejected) or role-gated? Quote.

**Deliverable:** the `shape_delta` for A-07 in full — what the second door
actually is, and the exact list of §6 claims it does and does not satisfy. This
determines whether Paripraśna's §6 can be implemented as written or must be
re-specified.

```
may_touch:
  - "00_ARCHITECTURE/rg1_ground/deliverables/**"
  - "00_ARCHITECTURE/rg1_ground/state/RG1_LANE_E-1.md"
```

---

### Lane E-2 — Projection / surface census (A-03, OT-10, tool counts)

**Charge:**

1. The three profiles: `full`/`compact`/`consult`. Read
   `mcp_surface_profile_builder.ts` and the projection compiler. Are they
   generated from one source with a CI parity gate? Confirm "consult provably
   cannot reach full-only tools."
2. **Reconcile the counts (PC-4):** live `/health` census, a live `tools/list`
   per profile, and the `server.ts` census comment. State the deployed surface
   size per profile and why `/health` (79) and `tools/list` (102) differ.
3. The alias cutover (RC-14): confirm 43 legacy names removed, 6 deferred
   renamed in place, all resolving. Confirm `COMPILER_VERSION` 2.0.0.
4. Compaction mechanism: `tool_search`, spine bundles (`463_bodha_spine_bundles`),
   `bodha_bundle_get`/`kala_bundle_get`. **`marsys_drill` was the doc's proposed
   mechanism — confirm it did NOT ship and the profiles+bundles replaced it.**
5. Verdict on A-03, A-05 (density_contract coverage now), OT-10.

```
may_touch:
  - "00_ARCHITECTURE/rg1_ground/deliverables/**"
  - "00_ARCHITECTURE/rg1_ground/state/RG1_LANE_E-2.md"
```

---

### Lane E-3 — Planner reconciliation (A-06, PlanReceipt, VidhiPlan)

**Charge:**

1. What did W4 "One Planner" actually land? Is there now one planner path or
   still the `PipelinePlan` (web) vs `VidhiPlan` (MCP) split PG-1 found?
2. **Does `PlanReceipt` exist in code now**, or is `VidhiPlan` +
   `CompletenessReceipt` still its de-facto analogue? Grep.
3. Is B.11-by-construction (the acharya floor) enforced on both doors? PG-1's
   §9.5 said the namespace map + web-route wiring was the real cost — did any of
   it land?
4. Scope-tuple round-trip (RC-01): confirm live parity was probed.
5. Verdict on A-06 and §9.

```
may_touch:
  - "00_ARCHITECTURE/rg1_ground/deliverables/**"
  - "00_ARCHITECTURE/rg1_ground/state/RG1_LANE_E-3.md"
```

---

### Lane E-4 — NO-LEAKAGE + session/provenance (A-19, D-16)

**Charge:**

1. **arm-by-arm on A-19's four arms:** arm-1 (5 DB roles — grep migrations;
   confirm still 0%), arm-2 (`no_leakage_filter.ts` — confirm built, on **both**
   doors, and that it closed the `/api/chat/consult` fail-open seam), arm-3
   (out-of-process ledger writer), arm-4 (CI canary). State each as built/partial/
   absent with evidence.
2. Session tools: `session_list`/`session_recall` (renamed from M3). Confirm the
   D-16 `provenance_stamp` restructure landed (RC-13/W-17) — does `session_recall`
   return `{priors_version, formula_versions, ranking_config, build_id,
   now_context_date}` for an explicit chart_id, with drift flag?
3. Verdict on A-19, A-10, D-16, and §7.4.

```
may_touch:
  - "00_ARCHITECTURE/rg1_ground/deliverables/**"
  - "00_ARCHITECTURE/rg1_ground/state/RG1_LANE_E-4.md"
```

---

### Lane E-5 — The Gochara / temporal surface (new; not in the doc)

**Charge:**

1. `gochara_activation_get` / `gochara_forecast_get` /
   `gochara_election_avoidance_get` / `kala_bundle_get` /
   `mechanism_retrodiction_get` — what layer, what tables (`kala_gochara_windows`
   460, `gochara_resonance_map`, `gochara_grammar`, D-4b mechanisms)?
2. **The operational fragility (PC-6):** confirm `register_gochara_windows.ts`
   reads `DATABASE_URL` directly (bypassing the primitive proxy), the live
   `DATABASE_URL not set` serving gap, and the `ka_gochara_sweep` build state
   (reported 165/300 `error`). This is a current data-plane defect.
3. `mechanism_retrodiction_get`: confirm the hard `event_date < 2020-01-01`
   NO-LEAKAGE guard and that it must not feed prediction pipelines.
4. **Recommend where this surface belongs in the architecture** — it is new
   §7/§8 material the doc does not mention.

```
may_touch:
  - "00_ARCHITECTURE/rg1_ground/deliverables/**"
  - "00_ARCHITECTURE/rg1_ground/state/RG1_LANE_E-5.md"
```

---

### Lane E-6 — Data-plane deltas + OT-11

**Charge:**

1. New migrations since 2026-07-19 (456, 458, 460, 461, 462, 463, 464). What
   each added; which are live.
2. OT-11: confirm the three-ledger state (`mimamsa_predictions` 384,
   `mcp_predictions` 0, `brahma_prospective_ledger` 5) and that no canonical
   choice was made. Confirm the dead `update_calibration`/`record_outcome` path
   was retired (464) — **does this change PF-1's F-2 charge?** (PF-1's F-2 was to
   fix `outcome.py`/`phala_anchors` drift; if 464 already retired it, F-2 may be
   moot.)
3. chart_facts: confirm PG-2's benign resolution still holds (ayanamsha ×5).
4. Verdict on §7, OT-11, and the PF-1 F-2 interaction.

```
may_touch:
  - "00_ARCHITECTURE/rg1_ground/deliverables/**"
  - "00_ARCHITECTURE/rg1_ground/state/RG1_LANE_E-6.md"
```

---

### Lane Z-4 — Synthesis → v0.11

**Deliverables:**

1. **`RETRIEVAL_MCP_GROUND_TRUTH_v1_0.md`** — the current, grounded state of the
   MCP channel, retrieval plane, and the Gochara/temporal surface. The companion
   to `RETRIEVAL_SYSTEM_TRUTH` that reflects what shipped.
2. **`PARIPRASHNA_TARGET_ARCHITECTURE` → v0.11** — every stale `[CORRECTED PG-1]`
   verdict gets a `[RE-GROUNDED RG-1]` second layer (PC-3); the §0 banner is
   updated from "to be verified by RG-1" to "grounded by RG-1"; OT-2/OT-10 move
   from §2 to §1 as resolved-in-code; the Gochara surface is added to §7/§8;
   A-19's arm-2 recorded built, arm-1 recorded standing-critical; §6.3–§6.5
   re-specified against the actual `prashna_ask` shape.
3. **The `shape_delta` register** — a standalone table: for every item that
   shipped differently than designed, what the implementation must reckon with.
   **This is the "no surprises at implementation time" deliverable the native
   asked for.**
4. Corrections to the MCP handoff, or a recommendation to retire it as
   superseded-by-reality.

```
may_touch:
  - "00_ARCHITECTURE/rg1_ground/**"
  - "00_ARCHITECTURE/RETRIEVAL_MCP_GROUND_TRUTH_v1_0.md"
  - "00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md"
  - "00_ARCHITECTURE/briefs/MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md"
  - "00_ARCHITECTURE/CURRENT_STATE_v1_0.md"
  - "00_ARCHITECTURE/SESSION_LOG.md"
```

---

### §F1.9 — DAG

```
   E-1   E-2   E-3   E-4   E-5   E-6      (parallel — independent questions)
    └─────┴─────┴─────┴─────┴─────┘
                    │
                   Z-4  (synthesis → v0.11)
                    │
                  §G gate
```

---

## FROZEN §F2 — Scope

```
must_not_touch:
  - "platform/src/**"                   # READ-ONLY
  - "platform-mcp/src/**"
  - "platform/migrations/**"
  - "platform/supabase/migrations/**"
  - "infra/**"
  - ".github/workflows/**"
  - "00_ARCHITECTURE/llm_consumption_audit/**"
  - "00_ARCHITECTURE/briefs/retrieval_impl/**"   # sealed campaign records — READ, cite, never edit
  - "00_ARCHITECTURE/pg1_audit/**"
  - "00_ARCHITECTURE/pg2_diagnostic/**"
  - "CLAUDECODE_BRIEF.md"
  - "CLAUDE.md"
```

### §F2.1 — Diagnostic probes authorized

Live `tools/list` per profile, live `/health`, live MCP tool calls (incl.
`prashna_ask` → `prashna_status` poll on the canonical chart), read queries
against production. **No writes.** If a `prashna_ask` probe would persist a job
row, that is acceptable job-state, not a product write — but do not invoke the
web consult path (that is PF-1's fenced write, not RG-1's).

---

## §B — BIND-AT-OPEN

| # | Slot | Probe |
|---|---|---|
| **B-1** | Base pin from `origin/main`, fetched | Not local `main`. |
| **B-2** | Worktree isolation verified | `git worktree list`, hard gate. |
| **B-3** | Campaign seal status | Is `retrieval_impl/FINAL_REPORT.md` still `AWAITING_NATIVE_REVIEW`? Record — it frames PC-1. |
| **B-4** | Live surface probe | `/health` count + one `tools/list` per profile at BIND, recorded. The E-2 reconciliation baseline. |
| **B-5** | `prashna_ask` reachability | One live `prashna_ask`→`prashna_status` round-trip on the canonical chart. If it fails, E-1 grounds from code alone and records the runtime failure. |
| **B-6** | Doc fingerprints | sha256 of `PARIPRASHNA_TARGET_ARCHITECTURE` v0.10 + the MCP handoff — Z-4's edits target these exact versions. |

---

## §G — Gate

Graded on reconciliation completeness.

| # | Assertion | `integrity` |
|---|---|---|
| **G.1** | Every stale `[CORRECTED PG-1]` verdict (A-03, A-06, A-07, A-08 at minimum) has a `[RE-GROUNDED RG-1]` second layer with evidence | **true** |
| **G.2** | The `prashna_ask` `shape_delta` is stated in full — what shipped vs what §6 designed, gate-by-gate | **true** |
| **G.3** | The `/health` (79) vs `tools/list` (102) count discrepancy is probed live and reconciled | **true** |
| **G.4** | NO-LEAKAGE is reported arm-by-arm; arm-1's 0% state is stated as the standing critical gap | **true** |
| **G.5** | The Gochara/temporal surface is documented and its live serving gap recorded | |
| **G.6** | No finding says only "built" — every "built" carries its `shape_delta` or an explicit "matches design" | **true** |
| **G.7** | OT-2 and OT-10 are moved to §1 (resolved-in-code) with the implementation cited | |
| **G.8** | Every finding contradicting a campaign record cites that record (`prior_work_cited` non-empty) | **true** |
| **G.9** | `PARIPRASHNA_TARGET_ARCHITECTURE` is at v0.11; `RETRIEVAL_MCP_GROUND_TRUTH_v1_0.md` exists | |
| **G.10** | `git diff --stat` touches zero paths under any `must_not_touch` glob | **true** |

### Final proof

> **RG-1 must state, in one table, every place where the shipped
> MCP/retrieval/data-plane reality differs from what `PARIPRASHNA_TARGET_
> ARCHITECTURE` assumes — with the implementation consequence of each.**
>
> **If that table does not exist, the wave did not re-ground anything.** A v0.11
> that merely flips "unbuilt" to "built" without the `shape_delta`s is a failed
> wave — the surprises live in the deltas, not the booleans.

### Anti-gaming pass

Fresh-context adversarial verifier (opus, high): **find the "built" finding that
omits how the implementation differs from the design.** That omission is the
exact failure this wave exists to prevent.

---

## §C — Close

Sealed: `REPORT_RG-1.md`, `RETRIEVAL_MCP_GROUND_TRUTH_v1_0.md`, architecture
v0.11, `rg1_findings.jsonl`. Governance close machine-derivable; red-team verdict
from a fresh Opus agent. `CURRENT_STATE` §2 gets the RG-1 pointer. Worktrees
cleaned.

**Transfers forward:**
- The `shape_delta` register → the P0'/implementation planning session.
- The PF-1 F-2 interaction (E-6) → PF-1, in case migration 464 mooted its charge.
- Any new open fork the deltas raise → architecture §2 as `OT-` items.

---

## §D — Kickoff prompt

```
Open wave RG-1 per 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_RG1_RETRIEVAL_GROUNDING_v1_0.md.

You are the RG-1 conductor. Read, in order:
  1. CLAUDE.md
  2. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md
  3. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/ESCALATION_POLICY_v1_0.md
  4. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/ADJUDICATOR_CHARGE_v1_0.md
  5. this brief
  6. 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.10 — read the ⚠ banner first)
  7. 00_ARCHITECTURE/briefs/retrieval_impl/STATE.md + FINAL_REPORT.md (the campaign that landed)
  8. 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2 (live pointer)

Then execute the §1 lifecycle end to end, autonomously, without pausing for input.

The staleness has INVERTED: PG-1/PG-2's corrections say "unbuilt" of things the
Retrieval Plane Elevation campaign (W0-W6) + Residual Closure (RC-01-17) then
shipped. Re-ground every MCP/retrieval/data-plane claim against the DEPLOYED
code — not the not-yet-sealed FINAL_REPORT (PC-1: code wins).

Binding constraints:
  - READ-ONLY. Diagnostic probes authorized (§F2.1): live tools/list per profile,
    /health, prashna_ask→prashna_status round-trip. Do NOT invoke the web consult
    path (that is PF-1's fenced write).
  - "Built" is never a complete finding. Every built item carries its shape_delta
    — how what shipped differs from what the architecture designed. The gap
    between A-07-as-designed (agentic loop) and prashna_ask-as-shipped
    (single-pass job) is the model for this. (G.6, PC-2.)
  - Do NOT delete PG-1's [CORRECTED] blocks. Add a [RE-GROUNDED RG-1] second
    layer. The layered history is the audit trail (PC-3, D-18).
  - prior_work_cited non-empty where a campaign record exists (G.8). A finding
    that contradicts a sealed record without citing it is a REJECT.
  - Worktree isolation enforced; base on origin/main fetched.
  - Opus verification floor is not a cost lever.

The wave succeeds only if it produces one table of every place the shipped
reality differs from what the architecture assumes, with each delta's
implementation consequence. A v0.11 that flips booleans without the deltas is a
failed wave. End with REPORT_RG-1.md and the §C close. Do not ask for
confirmation — §5 has pre-ruled every fork you can reach.
```

---

*End of BRIEF_RG-1 v1.0 (2026-07-24) — FROZEN, awaiting native kickoff.*
