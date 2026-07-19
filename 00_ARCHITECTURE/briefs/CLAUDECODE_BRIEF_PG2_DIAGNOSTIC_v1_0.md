---
artifact: BRIEF_PG-2
canonical_id: PG2_DIAGNOSTIC_BRIEF
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN) — DIAGNOSTIC WAVE
wave: PG-2 — Paripraśna Open-Question Diagnostic
version: 1.0
status: BOUND — CLOSED. See REPORT_PG-2.md (00_ARCHITECTURE/pg2_diagnostic/) for the close record.
authored_by: Claude (Cowork) 2026-07-19
governing: >
  00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md (v1.4)
  + ESCALATION_POLICY_v1_0.md (v1.1) + ADJUDICATOR_CHARGE_v1_0.md (v1.1)
predecessor: PG-1 (closed GREEN-qualified 2026-07-19; REPORT_PG-1.md)
resolves: >
  Every open question PG-1 left: the chart_facts divergence, whether the chat
  engine works, G.4's 104 unexecuted capabilities, 14 unverifiable findings,
  3 unaudited assumptions, OT-11, the Bearer-key 401, and PG-1's own internal
  inconsistencies.
mode: >
  READ-ONLY on application source. DIAGNOSTIC probes permitted (§F2.1) — the
  wave may INVOKE endpoints and run read queries, but writes no product code.
  One controlled write is authorized and fenced (§F2.2).
autonomy: FULL — opens on kickoff, closes on REPORT. No human in the loop between.
gate: §G — 11 assertions. Diagnosis waves are graded on RESOLUTION, not on volume.
blocks: P0' scoping (OT-12) and any data-sizing-dependent wave.
---

# PG-2 — Open-Question Diagnostic (autonomous wave brief)

## §0 — Orientation

### §0.1 Why this wave exists

PG-1 closed GREEN-qualified and did its job: it ground the architecture in
reality and produced `RETRIEVAL_SYSTEM_TRUTH_v1_0.md`. **It also, correctly, did
not diagnose anything** — read-only discipline forbade it. PG-1 surfaced
questions; PG-2 answers them.

**PG-1's own report names the priority:** the `chart_facts` divergence is *"the
single most consequential undiagnosed item this wave surfaced… could silently
poison any downstream sizing work."*

### §0.2 A correction PG-2 inherits and must apply

**PG-1 did not cite two prior investigations of the same divergence that exist in
this repo.** Both are starting hypotheses, not noise:

- `llm_consumption_audit/REMEDIATION_RUN_LEDGER_v1_0.md:115` — native hypothesis
  2026-07-12: *"135,645 ≈ 27,554 × ~5 ayanamshas — the L1 closure count was
  likely PER-ayanamsha, and prod stores all 5."*
- `REPORT_D-1.6.md:48` — *"chart_facts growth (27,554→138,279) investigated and
  confirmed legitimate (zero duplicate rows, clean build_id separation —
  `ga_structural`'s correct combinatorial output, not an accumulation bug)."*

So **138,519 is already explained.** The unexplained facts are **276,206** and
**intra-session movement**. BIND explicitly did not probe `build_id`. Lane X-1
starts from these hypotheses rather than from zero.

**This is itself a finding about PG-1**: a wave that cited no prior work on a
number it called its most consequential item. §F1.M-1 audits it.

### §0.3 Autonomy contract

Identical to PG-1 §0.4. Opens on kickoff, ends with `REPORT_PG-2.md`, no human
between. §5 pre-commits every reachable fork.

**One escalation difference.** PG-2 may find a live data-integrity defect. If a
probe demonstrates **active corruption** (not divergence — corruption: rows being
written that should not be, or a build writing outside its chart), that is an
ESCALATION §2 HALT class. Write `MEMO_PG-2_1.md`, commit with ledger `blocked`,
**end cleanly.** Do not attempt repair.

---

## §1 — Lifecycle

Same 7 steps as PG-1 (§1 of BRIEF_PG-1), unchanged.

**One protocol correction, binding:** PG-1 ran all lanes in a single shared
checkout despite its own §4 mandating one worktree per lane. That caused the
R-1/D-3 commit race, a false-positive scope-warden REJECT, and left the critical
NO-LEAKAGE lane with no commit of its own.

**PG-2 enforces worktree isolation. A lane that commits from the shared checkout
is an automatic REJECT regardless of finding quality.** The conductor verifies
`git worktree list` shows one entry per active lane before dispatching.

**And: the wave branch is cut from `origin/main`, not local `main`.** PG-1's PR
contamination traces to this. Verify with `git fetch && git rev-parse origin/main`
at BIND.

---

## §2 — State, findings, commit cadence

Identical to BRIEF_PG-1 §2, with one addition.

**Diagnostic findings carry a resolution field.** PG-2 is graded on questions
closed, not findings emitted:

```json
{"id":"PG2-0001","lane":"X-1","resolves":"F-25u",
 "question":"Why does chart_facts diverge 5-10x from sealed closure?",
 "resolution":"resolved|partially_resolved|unresolved|refuted",
 "root_cause":"...","evidence":[{...}],
 "prior_work_cited":["REPORT_D-1.6.md:48","REMEDIATION_RUN_LEDGER_v1_0.md:115"],
 "residual_unknown":"...","recommended_action":"...","confidence":"high|medium|low"}
```

`prior_work_cited` is **mandatory and may not be empty** where prior work exists.
Its absence in PG-1 is the defect §F1.M-1 audits; PG-2 does not repeat it.

---

## §3 — Model and effort dialing

Opus verification floor unchanged and absolute.

| Lane | Implementer | Effort | Rationale |
|---|---|---|---|
| X-1 | **opus** | **high** | Data-integrity root-cause. Wrong answer poisons every sizing decision downstream. |
| X-2 | **opus** | **high** | Live engine probe — must interpret failure modes correctly, not just observe them |
| X-3 | sonnet | medium | Mechanical: execute the remaining 104 capabilities |
| X-4 | sonnet | medium | Close the 14 unverifiables + 3 unaudited assumptions |
| X-5 | **opus** | **high** | OT-11 ledger reconciliation — a wrong canonical choice bakes into the role design |
| M-1 | **opus** | **high** | Meta-audit of PG-1's own integrity. Adversarial by construction. |
| Z-2 | **opus** | **high** | Synthesis |
| *verifiers* | **opus** | **high** | Floor. Non-negotiable. |

---

## §4 — Worktree discipline (enforced)

```
branch:   pg2/<lane>
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-pg2-<lane>
base:     origin/main@<pinned at BIND, fetched not assumed>
```

Conductor verifies isolation before dispatch. Cleanup mandatory per lane on
merge and at wave close.

---

## §5 — Pre-committed rulings

| # | Fork | **Ruling** |
|---|---|---|
| **PC-1** | A diagnosis is inconclusive | Report `unresolved` with what was eliminated. **A ruled-out hypothesis is a result.** Do not speculate past the evidence. |
| **PC-2** | `chart_facts` divergence proves legitimate (ayanamsha ×5 / build_id separation) | **Report it as resolved-benign and say so plainly.** Retract F-25u's alarm in the architecture doc. A false alarm honestly retracted costs nothing; a false alarm left standing corrupts every future sizing estimate. |
| **PC-3** | `chart_facts` divergence proves a real defect | Report root cause. **Do not fix** (§F2). If it is *active corruption*, §0.3 HALT applies. |
| **PC-4** | The chat engine fails when probed | **That is the wave's most valuable finding.** Capture the exact failure — status, body, logs, DB state after. Do not fix. Do not retry more than 3 times. |
| **PC-5** | The chat engine works | Equally valuable. **Capture the full artifact** — the persisted rows, the parts_json shape, whether the prediction detector fired, whether trace rows landed. This becomes the first real datum about the serving path. |
| **PC-6** | M-1 finds PG-1 overstated or understated a finding | **Report it plainly.** PG-1's value came from candour about its own Q-1 error; PG-2 owes it the same treatment. Do not defend the predecessor. |
| **PC-7** | M-1 finds PG-1's gate should have been RED | **Say so.** G.4 is already self-flagged as an override candidate. The native asked for grounding, not reassurance. |
| **PC-8** | OT-11 has no clean answer | Report both ledgers' actual state and the cost of each choice. **Do not pick for the native** — it is a §2-class design decision. |
| **PC-9** | A probe would require a write | **Stop.** Only §F2.2's fenced write is authorized. Everything else is reported as blocked-by-scope with the probe design that *would* answer it. |
| **PC-10** | Time or budget pressure | Park lanes; **never lower the Opus floor.** |
| **PC-11** | Every open question resolves cleanly | Report that. §G grades resolution quality, not finding volume. |

---

## FROZEN §F1 — Lane map

### Lane X-1 — The `chart_facts` divergence ⭐ *highest consequence*

**Starting hypotheses (from §0.2 — do not re-derive from zero):**

| H | Hypothesis | Predicted signature |
|---|---|---|
| H1 | Per-ayanamsha multiplication (native, 2026-07-12) | `count / distinct(ayanamsha_id)` ≈ 27,554 |
| H2 | Legitimate `ga_structural` combinatorial growth (D-1.6) | zero duplicate `(chart_id, fact_key)`; clean `build_id` separation |
| H3 | **Multiple `build_id`s accumulating** — BIND never probed this | count per `build_id` ≈ 138,519; two builds present |
| H4 | **Chart conflation** — the same class that bit Q-1 | count without `chart_id` filter ≈ 276,206; with filter ≈ 138,519 |
| H5 | Active write during the session | row count rises again on a third probe; `max(created_at)` inside the session window |
| H6 | Non-deterministic count (view, or mid-rebuild read) | repeated identical query returns different values |

**Required probes, all read-only:**

```sql
-- discriminates H4 (the leading hypothesis)
SELECT count(*) FROM chart_facts;                                    -- all charts
SELECT count(*) FROM chart_facts WHERE chart_id = '482012f1-...';    -- one chart
SELECT chart_id, count(*) FROM chart_facts GROUP BY 1;

-- discriminates H3
SELECT build_id, count(*) FROM chart_facts WHERE chart_id='482012f1-...' GROUP BY 1;

-- discriminates H1
SELECT ayanamsha_id, count(*) FROM chart_facts WHERE chart_id='482012f1-...' GROUP BY 1;

-- discriminates H2
SELECT fact_key, count(*) FROM chart_facts WHERE chart_id='482012f1-...'
  GROUP BY 1 HAVING count(*) > 1 LIMIT 50;

-- discriminates H5/H6 — run the identical query 3× spaced ≥5 min, record each
SELECT count(*), now() FROM chart_facts WHERE chart_id='482012f1-...';
SELECT max(created_at), max(updated_at) FROM chart_facts;
```

**Also:** reconcile against `asset_registry.count_sql` for the `ga_*` assets —
§N.4 says the cockpit reads `count_sql`, so what does *it* report, and does it
agree with any of the three figures?

**Deliverable:** a resolution with root cause, and an explicit statement of which
of the three numbers (27,554 / 138,519 / 276,206) is correct for what scope.
**Update `L1_GANITA_CLOSURE`'s canonical figure recommendation** — if the sealed
number is per-ayanamsha or per-build, the seal's own statement of it is
misleading and should be re-expressed. Recommend; do not edit the seal.

```
may_touch:
  - "00_ARCHITECTURE/pg2_diagnostic/deliverables/**"
  - "00_ARCHITECTURE/pg2_diagnostic/state/PG2_LANE_X-1.md"
```

---

### Lane X-2 — Does the chat engine work? ⭐ *cheapest high-value probe in the wave*

**PG-1 never invoked the consult endpoint.** Every conclusion about the serving
path is an audit of an unexercised path — T-9's own words: *"'wired but 0 rows'
cannot be read as 'works'."*

**Also unresolved:** PG-1 never mentions **LCA-2** (the retired-`reports`-table
failure that broke consult for every chart until 2026-07-13). Whether WP-1.1's
fix actually landed is untested.

**Charge — send one real question through the live chat path and record
everything:**

1. Authenticate as the native against the deployed app. Send one substantive
   question about chart `482012f1-…` through `/api/chat/consult`.
2. **Capture the complete artifact**: HTTP status, full SSE stream verbatim,
   every event type and order, time-to-first-byte, time-to-first-text, total.
3. **Then query the DB**: did `conversations` / `conversation_messages` gain
   rows? What is the `parts_json` shape? Did `llm_call_log`,
   `tool_execution_log`, `query_trace_steps` populate? Did
   `mcp_predictions` gain a row (the detector is wired per `PG1-D3-0002`)?
4. **If it fails**: capture the exact failure. Check specifically whether the
   `reports` relation is still referenced (LCA-2 regression). Check server logs.
   Determine whether writes are silently swallowed — D-3's trilemma must be
   resolved to one branch.
5. **Repeat once** to distinguish first-run effects from steady state.

**This lane single-handedly answers:** whether the store is empty because of no
traffic or silent failure; whether LCA-2's fix landed; whether the prediction
detector fires in practice; whether C-2's protocol mapping matches the real
stream; and it produces **the first real reading the instrument has ever
persisted**, which Q-1 needed and could not have.

**If X-2 produces a reading, a fresh Opus-xhigh agent grades it against §J** —
the assessment Q-1 could only make against proxies.

```
may_touch:
  - "00_ARCHITECTURE/pg2_diagnostic/deliverables/**"
  - "00_ARCHITECTURE/pg2_diagnostic/state/PG2_LANE_X-2.md"
```

---

### Lane X-3 — Close G.4: the 104 unexecuted capabilities

PG-1 executed 35 of 139 MCP tool names (~25%), against one chart, mostly
`response_format=legacy`. G.4 passed on a "no silent omissions" reading and is
**self-flagged as the item most likely to warrant native override.**

**Charge:** execute the remaining ~104, recording the same seven dimensions
`RETRIEVAL_SYSTEM_TRUTH` §2 uses. Plus:

- **Both response formats** where supported — v3 is opt-in and no default
  consumer exercises it; it may be broken.
- **A second chart** (Abhinandan `1c826d5a`) on a representative subset —
  single-chart observation cannot detect chart-conflation defects, and this wave
  has two independent conflation symptoms already.
- **Resolve the Bearer-key 401** (`F-25v`): PG-1 could not sweep that face at
  all. Is it misconfigured, or is the key wrong?
- Confirm or refute the two known-broken tools: `phala_anchors_get` (422),
  `ref_dignity_reference_get` (400).

**Deliverable:** `RETRIEVAL_SYSTEM_TRUTH_v1_0` → **v2.0 with full coverage**, and
a clean G.4 that needs no interpretive gloss.

```
may_touch:
  - "00_ARCHITECTURE/pg2_diagnostic/deliverables/**"
  - "00_ARCHITECTURE/pg2_diagnostic/state/PG2_LANE_X-3.md"
  - "00_ARCHITECTURE/RETRIEVAL_SYSTEM_TRUTH_v1_0.md"
```

---

### Lane X-4 — Close the unverifiables and the unaudited

**14 findings marked `unverifiable` + 3 assumptions never audited.** Most were
scope or budget limits, not genuine impossibility.

| Item | Why it was open | How to close |
|---|---|---|
| `PG1-R1-0010` (A-10) | "out of this lane's time budget" | Read the conversation-store schema + provenance-stamp columns |
| `PG1-R2-0005` (A2) | Harness refuses to omit a required param | **Probe from outside the MCP client** — raw HTTP to `/api/retrieval/capability` omitting `chart_id`. The gate's claim is that no default is injectable; test it directly. |
| `PG1-S1-0003` (high) | Could not distinguish "no citations" from "different shape" | Read the app-code citation path; determine the persisted shape |
| `PG1-S1-0004/0005` (A-30, A-32) | Correctly scoped out | Query feedback/dispute tables; confirm F-25c's stub finding |
| `PG1-D1-0001` (A26) | **The brief named the wrong assumption** | Audit the intended one (A-08/F-25e) properly |
| A-13 | No lane's charge covered it | Audit the memoization/content-visibility mechanism |
| A-31 | No lane's charge covered it | Audit outcome-recording compliance mechanics |
| `PG1-R1-0005/0006/0008/0009` | Target state, not built | **Confirm as not-built and close** — these are correctly unverifiable-as-target; record so they stop recurring |

```
may_touch:
  - "00_ARCHITECTURE/pg2_diagnostic/deliverables/**"
  - "00_ARCHITECTURE/pg2_diagnostic/state/PG2_LANE_X-4.md"
```

---

### Lane X-5 — OT-11: which prediction ledger is canonical?

Two disjoint ledgers: `mimamsa_predictions` (L5 build-time, 384 rows, referenced
by `mimamsa_calibration` and `phala_anchors`) and `mcp_predictions` (chat-side
detector, 0 rows).

**Charge — establish facts, not a decision (PC-8):**

- Full schema of both. Where do they overlap, where do they diverge?
- What writes to each? What reads from each?
- Does `mimamsa_predictions` carry the fields §14.3 requires — window,
  confidence, technique attribution, provenance stamp, source message id?
- **Which one does `record_outcome` actually write against?**
- What would merging cost? What would documenting the split cost?
- Does either satisfy §14's design without schema change?

**Deliverable:** a decision memo with both options costed. **Do not choose.**

```
may_touch:
  - "00_ARCHITECTURE/pg2_diagnostic/deliverables/**"
  - "00_ARCHITECTURE/pg2_diagnostic/state/PG2_LANE_X-5.md"
```

---

### Lane M-1 — Meta-audit of PG-1 ⭐ *adversarial by construction*

**PG-1 audited the architecture. Nothing audited PG-1.** Its own §0.1 rationale —
*"a document that misdescribes its origin point misdirects every session that
executes from it"* — applies to PG-1's outputs exactly as it applied to v0.4.

**Charge — verify PG-1's own integrity. Report without defending it (PC-6/PC-7):**

1. **The 87/98 discrepancy.** The sealed audit report says 87 in four places
   including its own manifest; the file has 98. Severity counts also disagree
   (report: 5 critical; file: 6 — `PG1-Q1-0007` omitted). **Which artifact is
   authoritative, and does the sealed report need correcting?**
2. **The G.1 addendum.** G.1 came back RED; 11 rows were added to close it.
   Verify each addendum row corresponds to a *pre-existing* narrative verdict and
   was not authored to pass the gate. **This is the single most important
   integrity check in the wave** — if any addendum row is a post-hoc fabrication,
   the gate result is void.
3. **Protocol deviations.** All lanes in one checkout despite §4; D-3 (the
   critical NO-LEAKAGE lane) has no commit of its own; wave branch cut from local
   `main`; G.9's check modified mid-wave. Assess each for whether it compromises
   a finding.
4. **Spot-verify 10 findings independently**, weighted to `critical` and `high`.
   Re-run the query or re-read the file. **Do they hold?**
5. **G.4's gate call.** The runner and anti-gaming pass both stated the
   adversarial case for RED and declined to overturn. **Assess independently
   whether the "no silent omissions" reading was legitimate or a gloss** —
   ADJUDICATOR_CHARGE §4's named failure mode.
6. **The uncited prior work** (§0.2). Two prior investigations of `chart_facts`
   existed in-repo and were not cited. Is this isolated, or did other lanes also
   fail to consult prior work?
7. `drift_detector.py` and `schema_validator.py` both exited 3, not 0. Confirm
   none of the 35 schema violations touch PG-1 paths.
8. **Is `MEMO_PG-1_*.md` absent because no §2 class was reached, or because one
   was reached and not written?**

```
may_touch:
  - "00_ARCHITECTURE/pg2_diagnostic/deliverables/**"
  - "00_ARCHITECTURE/pg2_diagnostic/state/PG2_LANE_M-1.md"
```

---

### Lane Z-2 — Synthesis

**Deliverables:**

1. **`PG2_DIAGNOSTIC_REPORT_v1_0.md`** — one section per open question with its
   resolution, root cause, residual unknown, and recommended action.
2. **`RETRIEVAL_SYSTEM_TRUTH_v2_0.md`** — full capability coverage from X-3, plus
   the first real serving-path observation from X-2.
3. **Architecture corrections → v0.7**, per D-18 discipline. Specifically:
   - **F-25u updated with X-1's resolution.** If benign, *retract the alarm
     plainly* (PC-2).
   - **T-9 updated with X-2's result.** If the engine works, T-9's second clause
     ("wired but 0 rows cannot be read as works") is *resolved*, not merely
     noted.
   - **§16 corrections** for anything M-1 overturns.
   - **OT-11 costed**; OT-12 left for the native.
4. **Corrections to PG-1's sealed artifacts** if M-1 finds them misstated — the
   87/98 discrepancy at minimum. Append a `[CORRECTED 2026-07-XX / PG-2]` block;
   **do not rewrite history.**
5. **A revised P0' estimate** if X-2's observed stream materially changes C-2's
   6–9 week analysis.

```
may_touch:
  - "00_ARCHITECTURE/pg2_diagnostic/**"
  - "00_ARCHITECTURE/RETRIEVAL_SYSTEM_TRUTH_v1_0.md"
  - "00_ARCHITECTURE/RETRIEVAL_SYSTEM_TRUTH_v2_0.md"
  - "00_ARCHITECTURE/PG2_DIAGNOSTIC_REPORT_v1_0.md"
  - "00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md"
  - "00_ARCHITECTURE/PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md"
  - "00_ARCHITECTURE/pg1_audit/REPORT_PG-1.md"
  - "00_ARCHITECTURE/CURRENT_STATE_v1_0.md"
```

---

### §F1.9 — Lane DAG

```
   X-1     X-2     X-3     X-4     X-5     M-1        (all parallel — no
    │       │       │       │       │       │          inter-lane deps)
    └───────┴───────┴───────┴───────┴───────┘
                        │
                        ▼
                       Z-2  (synthesis)
                        │
                        ▼
                     §G gate
```

**No declared dependencies between diagnostic lanes** — each answers an
independent question. Maximum parallelism. **Undeclared serialization is a
close-report defect.**

---

## FROZEN §F2 — Scope

```
must_not_touch:
  - "platform/src/**"                   # READ-ONLY on source
  - "platform-mcp/src/**"
  - "platform/migrations/**"
  - "platform/supabase/migrations/**"
  - "infra/**"
  - ".github/workflows/**"
  - "00_ARCHITECTURE/llm_consumption_audit/**"
  - "CLAUDECODE_BRIEF.md"
  - "CLAUDE.md"
  - "00_ARCHITECTURE/CAPABILITY_MANIFEST.json"
  - "00_ARCHITECTURE/L1_GANITA_CLOSURE_v2_0.md"   # X-1 recommends; never edits
```

### §F2.1 — Diagnostic probes are authorized

PG-1 was observation-only. **PG-2 may invoke.** Specifically permitted:

- Read queries against production, including repeated timing probes.
- Live MCP tool calls (X-3 executes ~104).
- **Live invocation of `/api/chat/consult`** (X-2) — this is the wave's central
  probe.
- Raw HTTP against `/api/retrieval/capability` to test the chart-agnostic gate
  from outside the MCP harness (X-4).

**Still forbidden:** any write to product source, migrations, or infrastructure.

### §F2.2 — The one fenced write

X-2's probe **will** create conversation rows if the engine works. This is
authorized and is the point.

**Fence:**
- Confined to the native's own chart `482012f1-…` and the native's own account.
- **Maximum 3 questions.** Not a load test.
- Every created row's id recorded in X-2's shard, so it is identifiable and
  removable.
- **These rows are the first real serving-path data the project has.** They are
  not test pollution; they are the artifact. Do not delete them.

---

## §B — BIND-AT-OPEN slots

| # | Slot | Probe |
|---|---|---|
| **B-1** | **Base pin from `origin/main`** | `git fetch && git rev-parse origin/main`. **Not local `main`** — PG-1's PR contamination traces to exactly this. |
| **B-2** | **PG-1 PR status** | Is #613 merged, open, or closed? If unmerged, PG-2 bases on `origin/main` and its outputs will need rebasing. Record. |
| **B-3** | **Worktree isolation verified** | `git worktree list` shows one entry per active lane before dispatch. **Hard gate — PG-1 skipped its own equivalent.** |
| **B-4** | **Chat-path reachability** | Can the deployed app be authenticated against and reached? If not, X-2 parks and the wave's central question stays open — **report that prominently, do not proceed quietly.** |
| **B-5** | **Baseline `chart_facts` triple** | Run X-1's three count variants once at BIND, timestamped. Establishes the fourth data point in the series. |
| **B-6** | **PG-1 artifact fingerprints** | sha256 of the three PG-1 deliverables. M-1's audit targets these exact versions. |

---

## §G — Gate

**Diagnostic waves are graded on resolution, not volume.**

| # | Assertion | `integrity` |
|---|---|---|
| **G.1** | The `chart_facts` divergence has a stated root cause, or an explicit list of hypotheses eliminated with the evidence that eliminated each | **true** |
| **G.2** | X-1 cites both prior in-repo investigations (§0.2) and states whether each holds | **true** |
| **G.3** | The chat engine has been invoked and the outcome recorded — **works / fails / unreachable, with the full artifact** | **true** |
| **G.4** | If it works, at least one real reading is persisted and graded against §J by a fresh Opus-xhigh agent | |
| **G.5** | Every capability in R-1's inventory has recorded observed behaviour — **now literally, with no interpretive gloss** | **true** |
| **G.6** | All 14 PG-1 unverifiables and 3 unaudited assumptions are closed or re-stated as genuinely impossible with reasons | |
| **G.7** | OT-11 has both options costed; **no choice made** | |
| **G.8** | M-1 has verified the G.1 addendum rows against pre-existing narrative verdicts and reported whether any was authored to pass the gate | **true** |
| **G.9** | M-1 has independently re-verified ≥10 PG-1 findings and reported which hold | |
| **G.10** | Every diagnostic finding carries non-empty `prior_work_cited` where prior work exists | **true** |
| **G.11** | `git diff --stat` touches zero paths under `platform/src`, `platform-mcp/src`, migrations, `infra`, or `.github/workflows` | **true** |

### Final proof (falsifiable)

> **PG-2 must state, in one sentence each, the answer to: (a) why `chart_facts`
> diverges, and (b) whether the chat engine works. Both answers must be
> supported by a probe this wave ran, not by inference from code.**
>
> **If either sentence cannot be written from this wave's own evidence, PG-2
> reports that question unresolved and says why — it does not infer.**

Both branches pre-committed: "resolved benign" and "resolved defective" are
equally valid for (a); "works" and "fails" equally valid for (b). **What is not
valid is a confident answer without a probe** — the T-7 failure mode, which PG-1
partially repeated by not citing prior work.

### Anti-gaming pass

Fresh-context adversarial verifier (opus, high). Charge: **find the question
that was declared resolved on evidence that does not actually discriminate
between the hypotheses.** Per ADJUDICATOR_CHARGE §4 — *if you find yourself
reasoning toward why a partial answer is "really" a resolution, STOP.*

---

## §C — Close

**Sealed:** `REPORT_PG-2.md`, `PG2_DIAGNOSTIC_REPORT_v1_0.md`,
`RETRIEVAL_SYSTEM_TRUTH_v2_0.md`, architecture → v0.7, corrections appended to
PG-1's artifacts where M-1 found them misstated, `pg2_findings.jsonl`.

**Governance close:** as PG-1 §C — machine-derivable throughout. Red-team verdict
from a fresh-context Opus agent.

**One item PG-1 left undone that PG-2 completes:** `CURRENT_STATE_v1_0.md` §2 gets
its PG-1 pointer **and** PG-2's. If the concurrent-edit conflict persists, record
the conflict rather than deferring again.

**Cleanup:** all `pg2/*` worktrees removed. Stranded worktrees are a
close-report defect.

**Transfers forward:** PG-1's 10 recommended fixes, updated with anything PG-2
resolves or reprioritizes, become the fix session's brief.

---

## §D — Kickoff prompt

```
Open wave PG-2 per 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_PG2_DIAGNOSTIC_v1_0.md.

You are the PG-2 conductor. Read, in order:
  1. CLAUDE.md
  2. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md
  3. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/ESCALATION_POLICY_v1_0.md
  4. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/ADJUDICATOR_CHARGE_v1_0.md
  5. this brief
  6. 00_ARCHITECTURE/pg1_audit/REPORT_PG-1.md  (the predecessor's exit record)
  7. 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.6)

Then execute the §1 lifecycle end to end, autonomously, without pausing for input.

Binding constraints:
  - READ-ONLY on product source. Diagnostic probes ARE authorized (§F2.1).
    The one fenced write is X-2's chat probe (§F2.2) — max 3 questions,
    native's chart, rows recorded and kept.
  - WORKTREE ISOLATION IS ENFORCED. PG-1 violated its own §4 and paid for it.
    A lane committing from the shared checkout is an automatic REJECT.
  - Base the wave branch on origin/main, fetched — not local main.
  - §5 pre-committed rulings govern every fork.
  - Opus verification floor is not a cost lever.
  - prior_work_cited may not be empty where prior work exists (G.10).
  - Only verifier receipts constitute acceptance.

Two questions matter more than the rest: why chart_facts diverges, and whether
the chat engine works. Both must be answered from a probe this wave ran, not
from inference. End with REPORT_PG-2.md and the §C close. Do not ask for
confirmation — §5 has pre-ruled every fork you can reach.
```

---

*End of BRIEF_PG-2 v1.0 (2026-07-19) — FROZEN, awaiting native kickoff.*
