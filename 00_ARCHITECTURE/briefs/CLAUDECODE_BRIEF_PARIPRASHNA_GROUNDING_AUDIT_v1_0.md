---
artifact: BRIEF_PG-1
canonical_id: PARIPRASHNA_GROUNDING_AUDIT_BRIEF
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN) — READ-ONLY AUDIT WAVE
wave: PG-1 — Paripraśna Grounding Audit
version: 2.0
status: BOUND — PG-1 open, lifecycle step 2 (SPAWN); see BIND_PG-1.md (00_ARCHITECTURE/pg1_audit/) and STATE_PG-1.md
supersedes: v1.0 (2026-07-19, prose brief; never activated — restructured into conductor form)
authored_by: Claude (Cowork) 2026-07-19
governing: >
  00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md (v1.4)
  + ESCALATION_POLICY_v1_0.md (v1.1) + ADJUDICATOR_CHARGE_v1_0.md (v1.1)
audits: 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.5)
mode: READ-ONLY on application code. ZERO product writes. Findings-only discipline absolute.
autonomy: FULL — opens on kickoff, closes on REPORT. No human in the loop between.
gate: §G — 9 assertions, all machine-checkable, plus one falsifiable final proof.
blocks: nothing. Informs P0' of PARIPRASHNA_TARGET_ARCHITECTURE §19.
prerequisite: >
  Native ruling on §0.3 concurrency with the Doctrine Waves campaign (current_wave D-4a).
  READ-ONLY posture makes concurrent operation safe; the ruling is a formality, not a risk.
---

# PG-1 — Paripraśna Grounding Audit (autonomous wave brief)

## §0 — Orientation

### §0.1 Why this wave exists

`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` (v0.5) is a target architecture built
across several design conversations. **It has already been wrong once in a way
that mattered**: v0.1–v0.4 asserted the two-process envelope mirror was
hand-maintained and "the codegen lane never landed," when the mirror had already
been deleted and generated, with `codegen:check` sitting in `package.json`. Four
counts were also wrong. Recorded as T-7 / D-18.

**This wave is the systematic fix.** It grounds every load-bearing assumption in
the working tree and produces the artifact Paripraśna most needs and does not
have: a truthful description of what the retrieval system actually does.

### §0.2 Two deliverables, one primary

| | Artifact | Nature |
|---|---|---|
| **PRIMARY** | `00_ARCHITECTURE/RETRIEVAL_SYSTEM_TRUTH_v1_0.md` | Observed behaviour of the real surface against a real chart. **This is what Paripraśna gets designed against.** |
| Secondary | `00_ARCHITECTURE/PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md` | Assumption verdicts, new defects, recommended fixes |

Corrections to the architecture document (→ v0.6) fall out of both.

### §0.3 Concurrency ruling required before kickoff

The root `CLAUDECODE_BRIEF.md` governs the **Doctrine Waves** campaign
(`current_wave: D-4a`, incoming). PG-1 reads overlapping surfaces (retrieval
registry, MCP tools, envelopes).

**PG-1 writes zero product code (§F2), so concurrent operation is safe.** The
ruling required is only: does PG-1 run now, or after D-4a closes? Absent a
ruling, **PG-1 defaults to running — read-only cannot corrupt a wave.**

`CLAUDECODE_BRIEF.md` is `must_not_touch` for this wave: PG-1 does **not**
advance `current_wave` and does **not** claim the root dispatcher.

### §0.4 Autonomy contract

**PG-1 opens on the native's kickoff directive and ends with `REPORT_PG-1.md`.
There is no human in between.**

- Escalation follows `ESCALATION_POLICY_v1_0.md` §0/§1/§2 unmodified.
- **§2 HALT-AND-REPORT is nearly unreachable for this wave** — its three classes
  are a red integrity gate, contested behaviour-changing doctrine, and a
  circuit-breaker trip. A read-only audit changes no behaviour. §5 below
  pre-commits rulings for every fork PG-1 can realistically hit, so the wave
  does not stall.
- If a §2 class is genuinely reached: write `MEMO_PG-1_<n>.md`, commit with the
  ledger in `blocked`, **end the session cleanly. No agent polls for an answer.**
- All state lives in files and git. A fresh session must be able to resume PG-1
  at any lifecycle point with zero loss (protocol §6.2).

---

## §1 — Lifecycle (adapted from CONDUCTOR_PROTOCOL §2)

The standard 8-step lifecycle has no deploy or rebuild — nothing is shipped.
PG-1's lifecycle is **7 steps, none skippable**:

```
  1 OPEN        conductor reads governing set; resolves §B bind slots;
                writes BIND_PG-1.md; pins base SHA; writes STATE_PG-1.md
                       │
  2 SPAWN       creates worktrees + branches per lane (§4); dispatches
                implementers with model/effort per §3
                       │
  3 INVESTIGATE ∥ VERIFY   lanes run in parallel per the §F1.9 DAG;
                each lane's findings are verified by a FRESH-CONTEXT
                verifier at the Opus floor before acceptance
                       │
  4 INTEGRATE   receipted lanes merge to the wave branch in §F1.9 order;
                per-lane worktrees cleaned on merge
                       │
  5 SYNTHESIZE  Lane Z-1 composes RETRIEVAL_SYSTEM_TRUTH + AUDIT_REPORT
                + architecture corrections (v0.6)
                       │
  6 GATE        §G's 9 assertions + final proof, run by a fresh-context
                gate runner at the Opus floor
                       │
  7 CLOSE       REPORT_PG-1.md sealed; SESSION_LOG appended;
                CURRENT_STATE updated; worktrees cleaned; PR opened+merged
```

**Acceptance rule, inherited verbatim:** the conductor accepts **only verifier
receipts**. An implementer's "done" is a claim, never an acceptance.

**Receipt format** (protocol §3.2, machine-checkable — emit exactly this):

```json
{"lane":"R-2","verifier_model":"opus","diff_reviewed":"<sha>",
 "findings":{"emitted":N,"schema_valid":N,"evidence_complete":N},
 "assertions":{"script":"<path>","green":[...],"red":[...]},
 "scope_warden":"pass|fail","verdict":"ACCEPT|REJECT","diagnosis":"..."}
```

**Scope warden:** `git diff --stat` must touch only the lane's `may_touch`
globs. **Any stray path is automatic REJECTION regardless of finding quality.**

**Circuit breakers:** 3 verification attempts per lane → PARK the lane and
continue the wave. >50% lanes parked → halt; the brief was mis-bound. **A parked
lane is reported parked. A half-done lane stamped complete is the exact failure
this protocol exists to prevent.**

---

## §2 — State and concurrency

**Per-lane state shards.** Lifted wholesale from the LLM Consumption Audit's
design: `state/PG1_LANE_<lane>.md` is written **only** by that lane.
`STATE_PG-1.md` is a regenerable index — counts and lane statuses, derived by
reading the shards. **No shared-file write contention, because no lane writes
the index.** Only the conductor writes `STATE_PG-1.md`.

**Machine-readable findings.** Every lane appends to
`deliverables/pg1_findings.jsonl`, one JSON object per line, append-only:

```json
{"id":"PG1-0001","lane":"C-1","assumption":"A13","class":"stale|confirmed|partial|unverifiable|new_defect",
 "claim":"...","reality":"...","evidence":[{"file":"...","line":123,"quote":"..."}],
 "severity":"critical|high|medium|low|informational",
 "affects":["§16.1 F-04"],"recommended_action":"...","confidence":"high|medium|low"}
```

`evidence` MUST be non-empty for any verdict other than `unverifiable`. A
finding with an empty evidence array is a **schema violation and fails the
lane's receipt.**

**Commit cadence.** State ledger and shard commits are **pushed at every
lifecycle transition**. An unpushed checkpoint is not a checkpoint. Bot
identity:

```
git config user.email "pg1-audit-bot@madhav-astrology.iam.gserviceaccount.com"
git config user.name "PG-1 Audit Bot"
# commit message convention:
#   chore(pg1/<lane>): <what> [PG1-BOT]
```

---

## §3 — Model and effort dialing (ESCALATION §5)

**The Opus verification floor is absolute: every verifier, the gate runner, and
the adjudicator seat run Opus-or-stronger at HIGH effort, never below.**

Implementer seats choose freely per §F1.6 economics — *economize on discovery
and mechanical transforms; spend on verification, judgment, and irreversible
steps.*

| Lane | Implementer | Effort | Rationale |
|---|---|---|---|
| A-0 | sonnet | medium | Harness scaffolding, mechanical |
| R-1 | haiku → sonnet | low | Machine-derivation of the declared surface |
| R-2 | sonnet | medium | Execution + recording across ~120 capabilities |
| R-3 | **opus** | **high** | The unified-plan-type exercise is real reasoning; a wrong "this is easy" is expensive |
| C-1 | sonnet | medium | Verification against known `file:line` anchors |
| C-2 | **opus** | **high** | P0' feasibility is the load-bearing judgment of the whole revised sequence |
| C-3 | haiku → sonnet | low | Mechanical importer census |
| D-1 | sonnet | medium | DB sampling + classification |
| D-2 | sonnet | low | Metric collection |
| D-3 | sonnet | medium | Schema + grants inspection |
| O-1 | sonnet | low | Ops inspection |
| S-1 | sonnet | medium | Signal sampling + readability assessment |
| **Q-1** | **opus** | **xhigh** | **Judging readings against the acharya bar is the highest-judgment task in the wave. Never dial this down.** |
| Z-1 | **opus** | **high** | Synthesis; authors the primary deliverable |
| *all verifiers* | **opus** | **high** | Floor. Non-negotiable. |

**Non-dialable fixed points:** Q-1's assessment and every ACCEPT/REJECT receipt.
A cheap agent may draft, scan, or collect; **the receipt comes from a verifier
dialed up, never down.**

---

## §4 — Worktree and branch discipline

```
branch:   pg1/<lane>                     e.g. pg1/R-2
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-pg1-<lane>
base:     origin/main@<pinned sha from §B-1>
```

Lanes run in parallel in isolated worktrees along independent DAG branches
(§F1.9). **Cleanup is mandatory** at two points: per-lane on merge, and at wave
close. **Stranded worktrees are a close-report defect.**

Wave integration branch: `pg1/wave`. Final PR to `main`, opened and merged
autonomously once §G is green (ESCALATION §0 — the full git cadence is
auto-proceed).

---

## §5 — Pre-committed rulings

**This section is what makes PG-1 autonomous.** Every fork the wave can
realistically hit is ruled here, in advance, so no agent stalls and no agent
improvises a decision that belongs to the native.

| # | Fork | **Pre-committed ruling** |
|---|---|---|
| **PC-1** | An assumption cannot be verified | Record `unverifiable` with the reason. **Do not estimate and present the estimate as measurement.** B.10 applies to this wave's own output — that is exactly how T-7 happened. |
| **PC-2** | The P0' shim requires engine changes (§F1.C-2) | **Report it as a finding; do NOT redesign the sequence.** D-17's revision is the native's call. The audit's job is to say YES or NO with evidence, not to author P0''. |
| **PC-3** | The unified plan type (§F1.R-3) proves hard or contradictory | **A negative result is a valid, high-value outcome.** Report the contradiction. **Do not design a workaround** — that is P2' work, not audit work. |
| **PC-4** | A capability is dead, broken, or 500s | **Record. Do not fix.** Findings-only discipline is absolute (§F2). |
| **PC-5** | A finding invalidates a settled D-item in the architecture doc | Write `MEMO_PG-1_<n>.md` stating the conflict, **continue the wave**, and surface it in `REPORT_PG-1` §native-disposition. **Do not silently revise a D-item** (protocol §K). Read-only means this is never urgent. |
| **PC-6** | A finding is embarrassing to the architecture or to prior sessions | **Report it plainly.** The wave's value is inversely proportional to its diplomacy. T-7 exists because a document was confident and wrong. |
| **PC-7** | Q-1 judges the readings poor against the acharya bar | **That verdict stands and is reported as-is.** It is not softened, not averaged with the good ones, and not reframed as "early days." A pre-committed unfavourable branch is the point of pre-commitment. |
| **PC-8** | Q-1 judges the readings good | **Equally reported as-is, with the same evidentiary standard.** A favourable result gets no lighter scrutiny than an unfavourable one. |
| **PC-9** | Two lanes disagree on the same fact | The conductor routes to the **Adjudicator seat** (opus, high, fresh context) per ESCALATION §1. Adjudicator's governing principle applies: *be the party that does not want the wave to be green.* |
| **PC-10** | A lane exceeds 3 verification attempts | PARK the lane, continue the wave, report parked with diagnosis. Do not lower the verification bar to pass it. |
| **PC-11** | The audit finds the architecture broadly sound with few corrections | **Report that.** Do not manufacture findings to justify the wave. **A low finding count with strong evidence is a valid outcome** — but §G.9 requires the *evidence*, not the count. |
| **PC-12** | Budget or time pressure | Lanes may be parked; **the Opus verification floor may never be lowered** to save cost. §3's floor is not a cost lever. |

---

## FROZEN §F1 — Lane map

### Lane A-0 — Harness (prerequisite for every other lane's verification)

**Deliverables:**
- `deliverables/pg1_findings.jsonl` schema + a validator script that exits
  non-zero on schema violation or empty `evidence`.
- `state/PG1_LANE_<lane>.md` shard template.
- A machine-derivation script for the capability inventory (feeds R-1).
- The `§G` assertion harness — each of the 9 assertions executable, emitting
  green/red.

**Acceptance:** validator rejects a malformed finding; assertion harness runs
and reports 9 results.

**Sequencing:** **A-0 merges before any other lane's Phase-1 verification.**

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/**"
  - "00_ARCHITECTURE/pg1_audit/scripts/**"
```

---

### Lane R-1 — Declared retrieval surface (machine-derived)

**Deliverables** — derived, never hand-counted:
- Every registered capability: `marsys://` URI, MCP name(s), every alias.
- Full descriptor metadata per capability: `scope`, `archetype`,
  `traversal_level`, `tool_role`, `drill_children`, `emits_references`,
  `grounds_to`, `lel_capable`, `density_contract` present/absent.
- Registration path per tool: registry-backed / sidecar / alias / direct.
- **Reconciliation against the `server.ts` census comment, reporting every
  disagreement.** Known wrong in both directions (architecture §16.4).
- Verdicts on assumptions **A1, A3, A4, A5, A6, A9, A10**.

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_R-1.md"
```

---

### Lane R-2 — Observed retrieval behaviour ⭐ *the part nobody has*

Executes every capability against the canonical chart
`482012f1-710e-4a25-994a-93821f5871aa`.

**Per capability, record:**

| Dimension | Why |
|---|---|
| Rows / empty / error | The remediation plan once counted 19 dead tools. **Still dead?** |
| Byte size (legacy and v3) | Context budgeting; `response_budget` interaction |
| Latency, cold and warm | The acharya floor's time cost is currently unknown |
| `judgment_flags` actually emitted | Only 3 emitters documented; find the real vocabulary |
| Epistemic grade distribution | What grades this chart's data actually produces |
| Coverage stamp — is `total` ever non-null? | B.10 honesty in practice |
| Do `drill_pointers` resolve? | F1 reference-don't-repeat depends on it |

**Failures are findings, not blockers.** A capability that 500s is among the most
useful things this lane can discover.

**Also:** verify **A2** (`chart_agnostic_gate` — is a default chart UUID truly
uninjectable?) by attempting injection in a scratch context.

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_R-2.md"
```

---

### Lane R-3 — Planning path + unified-plan-type falsification

**Deliverables:**
- One real question traced through **all three live planners** (D2 router,
  `pipeline_planner`, vidhi compiler); record what each produces for identical
  input.
- Verdicts on **A7, A8** — are `adapters/agentic_loop/` and `single_pass`
  genuinely dead? Report every importer.
- A real captured `PlanReceipt` for a career, a health, and a timing question.
- **How many `dark` items does a typical receipt carry, and which open CRs do
  they cite?** This is the honest measure of the instrument's completeness.
- **§2.4 falsification exercise — attempt to write the unified plan type.** It
  must express: floor and machine-band items as one addressable set; per-item
  served/empty/dark with CR refs; tool+args resolved against
  `capability_version`; a **subsumption relation** making "does this plan satisfy
  that floor?" decidable. Report honestly: a day, a week, or a contradiction.
  **PC-3 governs.**

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_R-3.md"
```

---

### Lane C-1 — Chat-layer forensic verification

Walk architecture §16.1 and §16.6. Verdicts on **A11–A25**. **Add any defect not
already in §16** — the appendix is append-only and this is how it grows.

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_C-1.md"
```

---

### Lane C-2 — P0' shim feasibility ⭐ *the load-bearing judgment*

The revised sequence (architecture §19, D-17) rests entirely on one assumption:
**that a translation shim can re-emit `run_adapter_dispatch`'s existing event
stream as the new typed SSE protocol without touching the engine.**

**Answer concretely:**
- Enumerate every event `run_adapter_dispatch` emits; map each to a §12.3
  protocol event. **Which have no mapping?**
- The protocol needs `turn.open` before the planner runs; today the stream opens
  after (A11). **Can the stream open early without restructuring the route — or
  does the shim require an engine change?** *If it requires one, D-17's "no
  engine work" premise is false.* **PC-2 governs: report, do not redesign.**
- Can `activity.upsert` be synthesized from the existing `toolEventLog` and stage
  parts?
- Can citation sentinels be introduced by prompt change alone?
- Can client-side stable-prefix segmentation (A-21) be achieved with the current
  markdown stack — memoized frozen prefix plus one volatile tail?
- **Estimate the shim honestly.** D-17's entire value is that it is cheap; if it
  is not 3–4 weeks, that is the finding.

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_C-2.md"
```

---

### Lane C-3 — Dead-code census

Two dead islands were found by accident. Sweep systematically: every module with
no live importer, every feature flag with no call site, every route with no
caller, across the chat and retrieval layers.

**Deliver a deletion-candidate list in dependency order** — F-15 proved deletion
order matters (a hook with type-only importers inside a dead cluster requires the
cluster to go first).

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_C-3.md"
```

---

### Lane D-1 — Conversation data reality

Decides whether the P1' migration is a script or a salvage operation.

- Conversation and message counts.
- **Sample `parts_json` across the date range.** What part shapes exist? Can SDK
  version be inferred from shape (v4 `toolInvocation` vs v5 typed `tool-*`)?
  What fraction is confidently classifiable?
- How many carry custom data parts that must be dropped rather than migrated?
- **Size the unmigratable residue** — §19 P1' says accept and quarantine it.
- Do `conversation_message_embeddings` cover the corpus or only part?
- Verdict on **A26**.

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_D-1.md"
```

---

### Lane D-2 — Cost and latency baseline

**Prerequisites for §14A.2 spend caps and §17.4 latency budgets to be anything
other than guesses.**

- Cost per turn by model and by phase (planner / retrieval / synthesis).
- Planner latency distribution; tool-fetch distribution; total time-to-answer.
- Verdict on **A29**.

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_D-2.md"
```

---

### Lane D-3 — Prediction substrate + NO-LEAKAGE grants

- Do `brahma_mimamsa_prediction_ledger`, `mimamsa_calibration`,
  `brahma_mimamsa_answer_quality`, `brahma_phala_anchors` exist with the columns
  §14 assumes? **Row counts?**
- Does `prediction_detector.ts` currently fire, and on what fraction of turns?
- **Are the NO-LEAKAGE grants enforceable?** What DB roles exist today, and what
  is the serving role's grant set? §7.4/§14A designs four arms — **arm 1 may be
  entirely aspirational.** This is a `severity: critical` finding if so.

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_D-3.md"
```

---

### Lane O-1 — Ops truth

- **Is Cloud SQL PITR actually enabled? Retention window?** Nobody in the repo
  knows. This is the difference between having backups and believing you do.
- Where do backups live? Has a restore ever been tested?
- Current deploy/rollback mechanism — **can a route be flag-gated the way §19 P1'
  assumes?**
- Verdicts on **A27, A28**.

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_O-1.md"
```

---

### Lane S-1 — Signal editorial sizing

- Sample 20 `bodha_msr_signals` rows; quote `signal_headline_text` and
  `signal_summary_text` **verbatim**.
- **How unreadable are they actually?** §13.6 assumes they cannot be shown to a
  reader. **Verify rather than assume** — the answer sizes a multi-week
  workstream.
- Which signals are cited most often in existing conversations? → the top-50
  priority list §19 P5' calls for.
- Verdicts on **A30, A32**.

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_S-1.md"
```

---

### Lane Q-1 — Reading quality against the acharya bar ⭐ *highest judgment*

**Every other artifact in this workstream reasons about architecture. None
reasons about whether the readings are any good.**

- Sample 10 real past conversations end-to-end.
- Assess each against CLAUDE.md §J: would an independent senior Jyotish acharya
  say *"this is my own level"*, *"above my own level"*, or *"this reveals things
  I wouldn't have seen"*? Or would they not?
- Identify the failure modes that are **not** architectural: generic phrasing,
  hedging that says nothing, grounded-but-wrong conclusions, cross-domain
  signals surfaced without judgment, remedies that drift prescriptive (§13.8).
- **PC-7 and PC-8 both govern: the verdict is reported as-is, favourable or
  not, with identical evidentiary standard.**

```
may_touch:
  - "00_ARCHITECTURE/pg1_audit/deliverables/**"
  - "00_ARCHITECTURE/pg1_audit/state/PG1_LANE_Q-1.md"
```

---

### Lane Z-1 — Synthesis (runs last; consumes all)

**Deliverable 1 — `RETRIEVAL_SYSTEM_TRUTH_v1_0.md`** (the primary artifact):

1. The real capability inventory — declared and observed side by side.
2. Behavioural profile per capability, **including the dead ones**.
3. The planning path as it actually runs, with a real `PlanReceipt`.
4. What the acharya floor costs in tools, bytes, milliseconds.
5. **Known-dark territory** — what the instrument cannot answer, with the CRs
   that explain why.
6. **A recommended chat projection** — given observed behaviour, which
   capabilities should the agentic loop see per route class. Direct input to
   architecture §8.3.
7. **Envelope self-sufficiency assessment.** §6.4.1 argues that on raw-tools MCP
   the envelope is the *only* epistemic defense. **Test it:** take three real
   envelopes to a fresh LLM with no system prompt and ask what they mean. Does it
   read `catalog_only` correctly? Notice `judgment_flags`? **Report verbatim.**

**Deliverable 2 — `PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md`:** assumption
verdict table (A1–A32), new defects with `F-` numbers continuing the sequence,
findings by severity, and a **prioritized recommended-immediate-fixes list which
becomes the next session's brief.**

**Deliverable 3 — architecture corrections → v0.6**, following §0.5/D-18
discipline: in place, error visible, marked `[CORRECTED]`, §16 append-only,
changelog entry. New tensions → §18. New forks → §2 as `OT-` items.

```
may_touch:
  - "00_ARCHITECTURE/RETRIEVAL_SYSTEM_TRUTH_v1_0.md"
  - "00_ARCHITECTURE/PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md"
  - "00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md"
  - "00_ARCHITECTURE/briefs/MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md"
  - "00_ARCHITECTURE/pg1_audit/**"
```

---

### §F1.9 — Lane DAG and merge order

```
        A-0  (harness — merges first, gates all Phase-1 verification)
         │
    ┌────┴─────┬──────┬──────┬──────┬──────┬──────┬──────┐
    ▼          ▼      ▼      ▼      ▼      ▼      ▼      ▼
   R-1        C-1    C-3    D-1    D-2    D-3    O-1    S-1     Q-1
    │                                                            │
    ▼                                                            │
   R-2 ──► R-3                                                   │
    │       │                                                    │
    └───────┴──────────────────┬─────────────────────────────────┘
                               ▼
                              Z-1  (synthesis — consumes all)
                               │
                               ▼
                              §G gate
```

**Declared dependencies** (all others are parallel; *undeclared serialization is
a close-report defect*):

- **A-0 → everything** — the harness gates Phase-1 verification.
- **R-1 → R-2** — the inventory is needed before capabilities can be executed.
- **R-2 → R-3** — observed behaviour informs the planning trace.
- **all → Z-1** — synthesis consumes every lane's findings.

Merge order: `A-0` first; the parallel band in any order as receipts land;
`R-1 → R-2 → R-3`; `Z-1` last.

---

## FROZEN §F2 — must_not_touch (all lanes)

```
must_not_touch:
  - "platform/src/**"                        # READ-ONLY. Zero product writes.
  - "platform-mcp/src/**"
  - "platform/migrations/**"
  - "platform/supabase/migrations/**"
  - "platform/scripts/**"
  - "infra/**"
  - "00_ARCHITECTURE/llm_consumption_audit/**"   # Doctrine Waves territory
  - "CLAUDECODE_BRIEF.md"                        # the other campaign's dispatcher
  - "CLAUDE.md"
  - "00_ARCHITECTURE/CAPABILITY_MANIFEST.json"
  - "00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md"
  - ".github/workflows/**"                       # see §F2.1
```

### §F2.1 — On `codegen:check`

v1.0 of this brief proposed wiring `codegen:check` into CI as a single
allowlisted fix. **v2.0 removes it.** Findings-only discipline is absolute, and
the LLM Consumption Audit's "**ZERO product writes all campaign**" precedent is
the house standard. The wiring is recorded as the **first item of the
recommended-immediate-fixes list** and executed by the follow-up session.

**Rationale, recorded so it is not relitigated:** a wave that both diagnoses and
repairs will under-report what it could not fix.

---

## §B — BIND-AT-OPEN slots

Resolved by the conductor at step 1 against live state; recorded in
`BIND_PG-1.md`.

| # | Slot | Probe |
|---|---|---|
| **B-1** | **Base pin** | `origin/main` SHA at open. Every worktree bases here. Recorded in `STATE_PG-1.md.base_pin`. |
| **B-2** | **Concurrency status** | Read `CLAUDECODE_BRIEF.md:current_wave`. If a Doctrine wave is mid-flight (`STATE_<wave>.md` lifecycle_step ∉ {closed}), record it. **Do not halt** — §0.3, read-only is safe. Record the coexistence in BIND. |
| **B-3** | **Live capability count** | Derive the actual registered tool count from a live `tools/list` (or equivalent). This becomes R-1's denominator, replacing every hand-maintained census. |
| **B-4** | **DB access confirmation** | Confirm read access to the production database for lanes D-1/D-2/D-3/S-1/Q-1. If unavailable, those lanes PARK with `unverifiable` findings **rather than the wave halting** (PC-1). |
| **B-5** | **Canonical chart build state** | Confirm `482012f1-710e-4a25-994a-93821f5871aa` is built and current; record its `build_id`. R-2's observations are meaningless against a stale build. |
| **B-6** | **Architecture doc fingerprint** | `sha256` of `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` at open. Z-1's corrections must apply to this exact version; a mid-wave change is a conflict requiring re-read. |

---

## §G — Gate

Nine assertions, all machine-checkable, run by a **fresh-context gate runner at
the Opus floor**. Plus one falsifiable final proof.

| # | Assertion | `integrity` |
|---|---|---|
| **G.1** | Every assumption A1–A32 carries a verdict in `pg1_findings.jsonl` | |
| **G.2** | Every finding with a verdict other than `unverifiable` has a **non-empty `evidence` array with at least one `file:line`** | **true** |
| **G.3** | `RETRIEVAL_SYSTEM_TRUTH_v1_0.md` exists and covers all 7 items of §F1.Z-1 deliverable 1 | |
| **G.4** | Observed behaviour is recorded for **every** capability in R-1's inventory — no silent omissions | **true** |
| **G.5** | The C-2 shim-feasibility question is answered **YES or NO with evidence** — not "it depends" | **true** |
| **G.6** | The R-3 unified-plan-type exercise is attempted and its result reported, including a negative result | |
| **G.7** | `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` is at v0.6 with a changelog entry, and every correction is marked `[CORRECTED]` with the original visible | |
| **G.8** | Q-1's quality verdict is present and **unsoftened** — the report contains the verdict, not a summary of it | **true** |
| **G.9** | `git diff --stat` across the wave touches **zero** paths under `platform/src`, `platform-mcp/src`, `platform/migrations`, `infra`, or `.github/workflows` | **true** |

**`integrity: true` assertions may never be re-baselined by the Adjudicator**
(ADJUDICATOR_CHARGE §4). If G.2, G.4, G.5, G.8 or G.9 is red, **the wave reports
red.**

### Final proof (falsifiable)

> **PG-1 must resolve the P0' feasibility question to a binary with evidence, and
> must move at least one A1–A32 assumption from its v0.5 verdict — or report,
> with the evidence supporting it, that every assumption held.**
>
> **If neither happens, the wave did not audit anything.**

**Both branches are pre-committed** (PC-11): "every assumption held" is a valid
outcome *if the evidence is there*. G.2's evidence requirement is what makes the
favourable branch unfakeable.

### Anti-gaming pass

A fresh-context adversarial verifier (opus, high) reviews the gate result with
one charge: **find the assertion that was passed by weakening its meaning.**
Per ADJUDICATOR_CHARGE §4 — *if you find yourself reasoning toward why a marginal
result is "really" a pass, STOP; that reasoning is the failure mode.*

---

## §C — Close

**Sealed artifacts:**
- `REPORT_PG-1.md` — `status: closed | blocked | parked`, following
  `REPORT_D-1.5a.md`'s structure: status line with counts, summary with the
  headline finding, lanes table (lane / verdict / receipt-with-verifier-hash),
  new-defects table, gate result, parked items with diagnosis, native
  disposition items, what transfers forward.
- `RETRIEVAL_SYSTEM_TRUTH_v1_0.md`, `PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md`
- `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` → v0.6
- `pg1_findings.jsonl` — machine-readable, the durable record

**Governance close (all machine-derivable — §0.4 autonomy holds):**
- `SESSION_LOG.md` append: `session_open` block (sha256 fingerprints of the
  mandatory reading set, read timestamps) + body + `session_close` block
  (`files_touched` with sha256 before/after from `git diff --name-status`,
  `within_declared_scope` from the scope-warden run, registry-update entries or
  an explicit "none required" with rationale).
- `drift_detector.py` (exit 0 or 3), `schema_validator.py` (exit 0) — recorded
  with exit codes.
- **`red_team.verdict` comes from a fresh-context Opus agent, not the working
  session** — consistent with the §3 floor.
- `CURRENT_STATE_v1_0.md` §2 updated.
- **`CLAUDECODE_BRIEF.md` is NOT touched** — PG-1 does not claim the root
  dispatcher and does not advance `current_wave`.

**Cleanup:** all `pg1/*` worktrees removed; all `pg1/*` branches merged or
deleted. **Stranded worktrees are a close-report defect.**

**Transfers forward:** the recommended-immediate-fixes list becomes the brief for
the follow-up **fix** session, `codegen:check` wiring as item 1.

---

## §D — Kickoff prompt (paste to start the wave)

```
Open wave PG-1 per 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_PARIPRASHNA_GROUNDING_AUDIT_v1_0.md.

You are the PG-1 conductor. Read, in order:
  1. CLAUDE.md
  2. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md
  3. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/ESCALATION_POLICY_v1_0.md
  4. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/ADJUDICATOR_CHARGE_v1_0.md
  5. this brief
  6. 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.5 — the object of audit)

Then execute the §1 lifecycle end to end, autonomously, without pausing for input.

Binding constraints:
  - READ-ONLY on application code. §F2 must_not_touch is absolute. Zero product writes.
  - §5 pre-committed rulings govern every fork. Do not improvise a decision they cover.
  - Opus verification floor (§3) is not a cost lever.
  - Only verifier receipts constitute acceptance. An implementer's "done" is a claim.
  - Commit and push STATE + shards at every lifecycle transition.
  - Findings without file:line evidence fail their lane's receipt (G.2).

Run lanes in parallel per the §F1.9 DAG in isolated worktrees. Dial model and
effort per §3. End with REPORT_PG-1.md and the §C close. Do not ask for
confirmation at any point — §5 has pre-ruled every fork you can reach.
```

---

*End of BRIEF_PG-1 v2.0 (2026-07-19) — FROZEN, awaiting native kickoff.*
