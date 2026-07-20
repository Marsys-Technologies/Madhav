---
artifact: BRIEF_PF-1
canonical_id: PF1_ENGINE_RESURRECTION_BRIEF
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN) — WRITE WAVE
wave: PF-1 — Engine Resurrection + Teardown-Orphan Sweep
version: 1.0
status: FROZEN — awaiting native kickoff
authored_by: Claude (Cowork) 2026-07-19
governing: >
  00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md (v1.4)
  + ESCALATION_POLICY_v1_0.md (v1.1) + ADJUDICATOR_CHARGE_v1_0.md (v1.1)
predecessors: PG-1 (closed GREEN-qualified), PG-2 (closed GREEN 11/11)
mode: >
  WRITE WAVE. Product code IS touched — narrowly, per §F1. Full 8-step lifecycle
  with deploy, rebuild, and post-deploy gate. Two-phase verification mandatory.
autonomy: FULL — opens on kickoff, closes on REPORT. No human in the loop between.
gate: §G — 8 assertions on the DEPLOYED artifact, plus one falsifiable final proof.
blocks: >
  Everything. The chat engine is down; no reading can be produced, graded, or
  persisted until PF-1 lands. OT-12 (P0' scope) cannot be decided well without it.
addendum_2026-07-20: >
  Re-scope ruling (native, 2026-07-20, stash-triage close-out): this brief's
  §F1 bundle_hydrator.ts item is CARVED OUT to the retrieval campaign's W4 wave
  as a cross-campaign assignment (2026-07-20; evidence and full root-cause in
  REPORT_PG-2.md) — an unopened FROZEN wave cannot gate an active one, and the
  fix is W4's own precondition, needed now. PF-1 is NOT superseded; its
  remaining scope is the teardown-orphan sweep, including the
  outcome.py/phala_anchors schema mismatch (§F1's third defect — record_outcome
  has never been callable). Kickoff after retrieval W4 closes; native call.
---

# PF-1 — Engine Resurrection + Teardown-Orphan Sweep

## §0 — Orientation

### §0.1 What this wave fixes, and why it is one wave

PG-2 invoked the chat engine twice against the live deployed app and got a
deterministic **HTTP 500**, root-caused to `bundle_hydrator.ts` hardcoding a
retired `FORENSIC` asset deleted from the capability manifest and never removed
from that list.

**This is the second occurrence of the same disease.** LCA-2, six weeks earlier:
*"the consult path unconditionally queries the retired `reports` relation and
fails for every chart."* Same shape — a teardown removes something, a hardcoded
reference survives, the chat path 500s, and **nobody notices for weeks because
nothing exercises it.**

PG-2 surfaced a third instance in a different subsystem: `outcome.py` references
`phala_anchors` columns absent from the live schema, so the MCP `record_outcome`
tool — the mechanism that closes the calibration loop and lets L5 leave
STRUCTURAL mode — **would fail at runtime and never has been called.**

**The three defects share one root cause: no smoke test exercises these paths.**
Fixing the references without closing the detection gap guarantees a fourth
occurrence. That is why this is one wave and not three tickets.

### §0.2 A governance finding this wave must record

**WP-1.1 was recorded complete as "Prod consult resurrection" on 2026-07-13.**
The engine still returned 500 on 2026-07-19. Either WP-1.1 fixed the `reports`
reference and left the `FORENSIC` one, or its completion was never verified
end-to-end.

**Nothing in that remediation invoked the endpoint.** §F1.F-3 exists so that
"resurrection" can never again be claimed without a request having been sent
through. Lane F-4 dates the break and records the finding.

### §0.3 Autonomy contract

Opens on kickoff, ends with `REPORT_PF-1.md`, no human between. §5 pre-commits
every reachable fork.

**Write-wave escalation differs from PG-1/PG-2.** Per ESCALATION §0, deploy and
scope-limited rebuild are auto-proceed. But:

- **A schema migration is NOT auto-proceed in this wave.** §F1.F-2 may discover
  that `phala_anchors` genuinely lacks outcome columns rather than merely being
  misnamed. **If a migration is required, the lane PARKS and reports** — see
  PC-4. Rationale: the OT-11 ledger ruling is open, and a new conversational
  ledger may make those columns moot. Migrating now risks doing work the ruling
  discards.
- **Build-health failure → immediate rollback to the §B-2 pin.** No
  forward-fixing on a corrupted estate.

---

## §1 — Lifecycle

**Full 8 steps** (CONDUCTOR_PROTOCOL §2), unlike PG-1/PG-2's 7:

```
 1 OPEN → 2 SPAWN → 3 IMPLEMENT ∥ VERIFY → 4 INTEGRATE →
 5 DEPLOY → 6 REBUILD (scope-limited) → 7 GATE (post-deploy) → 8 CLOSE
```

**Two-phase verification is mandatory and is the point of this wave's rigour:**

- **Phase 1, pre-merge, per lane.** (a) diff review against the lane brief;
  (b) **the verifier runs the tests itself** — implementer-reported results are
  not evidence; (c) scope-warden on `git diff --stat`; (d) for a write wave,
  additionally: does the diff touch anything outside the named file set?
- **Phase 2, post-deploy, per wave.** §G runs against the **deployed** app, not
  a local build. **Phase 1 merges a lane; only Phase 2 closes the wave.**

**The rule that governs everything here:** a red gate is reported red. **A
half-passed gate stamped complete is the exact failure this protocol exists to
prevent** — and in this wave, "the engine works" is the claim most tempting to
overstate.

---

## §2 — State, findings, commit cadence

Per-lane shards at `00_ARCHITECTURE/pf1_fix/state/PF1_LANE_<lane>.md`; conductor
writes the index. Commits pushed at every transition.

```
git config user.email "pf1-fix-bot@madhav-astrology.iam.gserviceaccount.com"
git config user.name "PF-1 Fix Bot"
# chore(pf1/<lane>): <what> [PF1-BOT]
```

---

## §3 — Model and effort

| Lane | Implementer | Effort | Rationale |
|---|---|---|---|
| F-1 | sonnet | medium | The fix is small; the *verification* is what matters |
| F-2 | **opus** | **high** | Must distinguish "misnamed" from "genuinely missing" before writing anything |
| F-3 | sonnet | medium | CI wiring |
| F-4 | sonnet | low | Git archaeology |
| Q-2 | **opus** | **xhigh** | Grading a real reading against §J. **The highest-judgment task in the wave. Never dial down.** |
| Z-3 | **opus** | **high** | Synthesis |
| *verifiers* | **opus** | **high** | Floor. Non-negotiable. |
| *migration guard* | **opus** | **high** | Only if F-2 proposes schema work — which it may not do (PC-4) |

---

## §4 — Worktree discipline

```
branch:   pf1/<lane>
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-pf1-<lane>
base:     origin/main@<pinned at §B-1, fetched not assumed>
```

**Enforced as in PG-2** — the conductor verifies `git worktree list` before
dispatch. A lane committing from the shared checkout is an automatic REJECT.

---

## §5 — Pre-committed rulings

| # | Fork | **Ruling** |
|---|---|---|
| **PC-1** | The `bundle_hydrator` fix does not resurrect the engine — another 500 appears | **Root-cause and fix it too, if it is the same class** (a hardcoded reference to a retired asset). **If it is a different class, STOP** — record the second defect, ship the first fix, report the engine still down. Do not chase an unbounded defect chain in a write wave. |
| **PC-2** | The engine works but the reading is poor | **Both facts are reported.** "Works" is an engine claim; §J is a quality claim. Do not let a working engine soften Q-2's verdict, and do not let a poor reading obscure that the engine now runs. |
| **PC-3** | The engine works and the reading is good | **Same evidentiary standard.** A favourable §J verdict gets the identical scrutiny an unfavourable one would. |
| **PC-4** | F-2 finds `phala_anchors` genuinely lacks outcome columns (not merely misnamed) | **PARK the lane. Do not migrate.** Report the required schema change and its cost. The OT-11 ruling is open and may supersede it. **A migration executed now that the ruling discards is worse than a parked lane.** |
| **PC-5** | The smoke test is flaky | **A flaky smoke test is worse than none** — it trains you to ignore it. Make it deterministic or do not ship it. Report the difficulty. |
| **PC-6** | F-4 finds the break predates the Legacy Teardown, or postdates WP-1.1 | **Report the date as found.** The governance finding (§0.2) is calibrated to whatever the archaeology shows, not to the hypothesis. |
| **PC-7** | The fix requires touching more than the named files | **Automatic REJECT via scope-warden.** Raise it; do not widen scope silently. This is a write wave — scope creep is how a one-line fix becomes an outage. |
| **PC-8** | Deploy fails or the deployed build is unhealthy | **Immediate rollback to the §B-2 pin.** No forward-fixing. |
| **PC-9** | Time or budget pressure | Park lanes; **never lower the Opus floor**, and never skip Phase 2. |

---

## FROZEN §F1 — Lane map

### Lane F-1 — Resurrect the engine ⭐ *the unblocking fix*

**Defect:** `bundle_hydrator.ts` hardcodes a retired `FORENSIC` asset deleted
from the capability manifest. Deterministic HTTP 500 on every chat request.

**Charge:**

1. Read PG-2's Lane X-2 shard for the exact root-cause evidence and the failing
   request/response pair. **Do not re-derive it.**
2. Remove the retired reference. **Minimal diff** — this is not a refactor of
   the hydrator.
3. **Audit the same file and its siblings for other retired-asset references.**
   The manifest is authoritative; anything hardcoded that the manifest no longer
   carries is the same defect waiting to fire. Report what you find even if you
   do not fix it.
4. Local verification: the route returns 200 for the canonical chart.
5. **Phase-1 acceptance requires the verifier to reproduce the 200 itself.**

**Explicitly out of scope:** any other change to the consult route, the
hydrator's design, or the bundle contract. §19's route reorder is P0' work, not
this wave.

```
may_touch:
  - "platform/src/lib/**/bundle_hydrator.ts"
  - "00_ARCHITECTURE/pf1_fix/**"
```

---

### Lane F-2 — The `record_outcome` schema drift

**Defect (PG-2 Lane X-5):** `platform/python-sidecar/brahmagyan/mimamsa/outcome.py`
references `phala_anchors` columns absent from the live schema. It uses `id`,
`confidence`, `prediction_state`, `outcome_note`, `outcome_recorded_at`,
`updated_at`; the live table has `anchor_id`, `confidence_low`/`confidence_high`,
`posterior`, `computed_at`.

**Diagnose before writing. Two distinct cases:**

| Case | Meaning | Action |
|---|---|---|
| **Rename** — the live table has equivalent columns under different names | Code drifted from schema | **Fix the code to match the live schema.** Never alter the table. |
| **Genuinely missing** — outcome-capture columns (`prediction_state`, `outcome_note`, `outcome_recorded_at`) have no equivalent | The table was never built to record outcomes | **PARK per PC-4.** Report the required migration and its cost. Do not migrate. |

Expect a mix: `id`→`anchor_id` and `confidence`→`confidence_low/high` look like
renames; the three outcome fields look genuinely absent.

**Also:** `update_calibration()`'s body was never inspected by X-5. **Inspect
it** — if `record_outcome` has never run, its downstream may carry the same
drift.

**Acceptance:** either `record_outcome` executes end-to-end against a real
`phala_anchors` row without error, **or** the lane parks with a costed
migration spec. Both are valid outcomes.

```
may_touch:
  - "platform/python-sidecar/brahmagyan/mimamsa/outcome.py"
  - "00_ARCHITECTURE/pf1_fix/**"
```

---

### Lane F-3 — Close the detection gap ⭐ *the reason this is one wave*

**Two safety mechanisms exist and nothing runs them.** Same class of defect:
a check that was built and never wired.

**F-3.a — Chat smoke test.** `chat-v2-smoke.yml` already exists. Add a
post-deploy step that:

1. Authenticates against the deployed app.
2. Sends one request to `/api/chat/consult` for the canonical chart
   `482012f1-710e-4a25-994a-93821f5871aa`.
3. **Asserts HTTP 200**, a non-empty streamed body, and **a persisted
   `conversation_messages` row**.
4. Fails the deploy loudly on any of the three.

**Determinism requirements (PC-5):** a fixed question, a bounded timeout, and a
cleanup path so the smoke corpus does not accumulate indefinitely — **but the
rows are kept, not deleted, until a retention policy exists.** Early
serving-path data is scarce and valuable.

**F-3.b — Wire `codegen:check` into CI.** Item 1 of PG-1's recommended-fixes
list. `platform-mcp/package.json` carries the script; **no workflow invokes
it**, so contract drift between the registry and the generated envelope is
currently undetected. One line into `ci.yml`.

**Acceptance:** both run in CI; both demonstrably fail when given a broken
input (prove the test can fail, not merely that it passes).

```
may_touch:
  - ".github/workflows/chat-v2-smoke.yml"
  - ".github/workflows/ci.yml"
  - "platform/scripts/smoke/**"
  - "00_ARCHITECTURE/pf1_fix/**"
```

---

### Lane F-4 — Date the break; record the governance finding

**Charge:**

1. `git log` the capability manifest and `bundle_hydrator.ts`. **When did the
   `FORENSIC` entry leave the manifest?** Hypothesis to test, not assume: PR
   #187, the Legacy Teardown, 2026-06-03 (per CLAUDE.md §B, the FORENSIC v8.0
   markdown was deleted there).
2. **How long has the chat engine been returning 500?** If the manifest entry
   went at the teardown, the engine has been dead ~7 weeks — which would fully
   explain the empty conversation store, and would mean it never "worked then
   broke": it has been down since.
3. **What did WP-1.1 actually change on 2026-07-13?** It was recorded as
   completing "Prod consult resurrection." Did it fix the `reports` reference
   and leave this one? **Was any end-to-end invocation performed?**
4. Record the finding plainly per PC-6: **a remediation was marked complete
   without a request having been sent through the thing it resurrected.**

**Deliverable:** a dated timeline and a governance finding for
`MARSYS_DEFECT_GAP_REGISTER`.

```
may_touch:
  - "00_ARCHITECTURE/pf1_fix/**"
```

---

### Lane Q-2 — Grade the first real reading ⭐ *post-deploy; the long-open question*

**Runs only after F-1 is merged and deployed.** Sequenced, not parallel.

PG-1's Q-1 could not grade a real reading because none existed; it judged
build-pipeline proxies and found they *"describe the instrument's own machinery
— z-scores, salience, embedding distance, internal signal keys — in place of
reading the chart."* **Whether the synthesis layer built on top of those proxies
reads the chart is a different question, and it has never been askable.**

**Charge:**

1. Send **three substantive questions** through the resurrected engine against
   the canonical chart — one domain question (career or marriage), one timing
   question, one open/interpretive question.
2. Capture each reading in full, with its retrieval trace and persisted parts.
3. **Grade each against CLAUDE.md §J** — would an independent senior acharya say
   *"this is my own level"*, *"above my own level"*, *"this reveals things I
   wouldn't have seen"*? Or would they not?
4. Assess specifically against the failure modes Q-1 named: does the reading
   speak in internal register (§13.6)? Does it describe machinery instead of
   reading the chart? Does it hedge into vacuity? Do remedies drift prescriptive
   (§13.8)?
5. **Compare the observed SSE stream against §12.3's protocol design** — C-2's
   6–9 week estimate was derived from reading code with the engine dead. **Does
   the real stream change the estimate?** This directly informs OT-12.

**PC-2/PC-3 govern: the verdict is reported as-is, favourable or not, with
identical evidentiary standard.**

```
may_touch:
  - "00_ARCHITECTURE/pf1_fix/**"
```

---

### Lane Z-3 — Synthesis and close

1. **`PF1_REPORT_v1_0.md`** — what was fixed, what the engine now does, Q-2's
   verdict, F-4's timeline, F-2's disposition.
2. **Architecture → v0.8**: T-9 updated with the resolved answer (**the store
   was empty because the engine was down, not because writes were swallowed**);
   §16 gains the teardown-orphan defect class; OT-12 updated with Q-2's observed
   stream; §14 corrected — **`brahma_mimamsa_prediction_ledger` names no live
   table** (PG-2 X-5's finding, still unrecorded).
3. **The first reading, preserved** as an artifact in the audit trail. It is the
   project's first served output and the baseline every future §J assessment
   compares against.

```
may_touch:
  - "00_ARCHITECTURE/pf1_fix/**"
  - "00_ARCHITECTURE/PF1_REPORT_v1_0.md"
  - "00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md"
  - "00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md"
  - "00_ARCHITECTURE/CURRENT_STATE_v1_0.md"
  - "00_ARCHITECTURE/SESSION_LOG.md"
```

---

### §F1.9 — DAG

```
   F-1     F-2     F-3     F-4        (parallel)
    │       │       │       │
    └───────┴───────┴───────┘
                │
           INTEGRATE
                │
             DEPLOY  ←── rollback pin from §B-2 armed
                │
              Q-2     (requires the deployed, working engine)
                │
               Z-3
                │
            §G gate (post-deploy)
```

**Merge order:** F-1 first (it unblocks Q-2), then F-2/F-3/F-4 in any order.
**Q-2 cannot start before deploy.** This is a declared serialization, not an
oversight.

---

## FROZEN §F2 — must_not_touch

```
must_not_touch:
  - "platform/src/app/api/chat/consult/route.ts"   # §19 route reorder is P0' work
  - "platform/src/lib/pipelines/**"
  - "platform/src/lib/synthesis/**"
  - "platform/src/components/**"
  - "platform/migrations/**"                        # PC-4: park, do not migrate
  - "platform/supabase/migrations/**"
  - "platform-mcp/src/**"
  - "infra/**"
  - "00_ARCHITECTURE/llm_consumption_audit/**"      # Doctrine Waves territory
  - "00_ARCHITECTURE/pg1_audit/**"                  # sealed
  - "00_ARCHITECTURE/pg2_diagnostic/**"             # sealed
  - "CLAUDECODE_BRIEF.md"
  - "CLAUDE.md"
```

**Note on PR independence:** PG-1 (#613) and PG-2 (#620) touch
`00_ARCHITECTURE/**` almost exclusively; PF-1 touches `platform/**` plus its own
`pf1_fix/` tree. **Overlap is near zero** — PF-1 does not wait on either PR and
does not conflict with them. `CURRENT_STATE` and `SESSION_LOG` are the only
shared files; §B-5 handles them.

---

## §B — BIND-AT-OPEN

| # | Slot | Probe |
|---|---|---|
| **B-1** | **Base pin from `origin/main`, fetched** | `git fetch && git rev-parse origin/main`. Local `main` was 31 behind at PG-2's close — **do not use it.** |
| **B-2** | **Rollback pin** (protocol §8.4) | Current deployed image SHA + revision. **Armed before any deploy.** PC-8 rolls back to this. |
| **B-3** | **Worktree isolation verified** | `git worktree list` shows one entry per active lane before dispatch. Hard gate. |
| **B-4** | **Reproduce the 500** | Send one request to `/api/chat/consult` and confirm the failure still occurs at the pinned base. **If it does not, STOP** — something changed since PG-2 and the wave must re-diagnose before fixing. |
| **B-5** | **PR state** | Are #613/#620 merged? If not, note that `CURRENT_STATE`/`SESSION_LOG` edits may conflict; PF-1 appends rather than restructures in those two files. |
| **B-6** | **Working tree clean** | PG-2 left `pg1/wave` dirty with 5 modified + 9 untracked files. Confirm a clean base before spawning. |

---

## §G — Gate (post-deploy, on the deployed artifact)

| # | Assertion | `integrity` |
|---|---|---|
| **G.1** | `/api/chat/consult` returns **HTTP 200** for the canonical chart against the **deployed** app | **true** |
| **G.2** | A `conversation_messages` row is persisted, with non-empty `parts_json` | **true** |
| **G.3** | The smoke test runs in CI and **has been demonstrated to fail** on a broken input | **true** |
| **G.4** | `codegen:check` runs in CI | |
| **G.5** | `record_outcome` executes end-to-end **or** F-2 is parked with a costed migration spec | |
| **G.6** | Q-2's §J verdict is present and **unsoftened**, for all three readings | **true** |
| **G.7** | F-4's timeline dates the break and records the WP-1.1 governance finding | |
| **G.8** | `git diff --stat` touches **only** the union of the lanes' `may_touch` sets — zero paths under the §F2 list | **true** |

### Final proof (falsifiable)

> **A real reading, produced by the deployed engine, is persisted in
> `conversation_messages` and graded against §J in this wave's report.**
>
> **If no reading persists, the wave did not happen** — regardless of how clean
> the diff is.

Both branches pre-committed: a good reading and a poor one are equally valid
outcomes (PC-2/PC-3). **What is not valid is a green wave with an empty
conversation store.**

### Anti-gaming pass

Fresh-context adversarial verifier (opus, high). Charge: **find the assertion
passed on a local build rather than the deployed artifact, or the §J verdict
softened by the relief of a working engine.**

---

## §C — Close

**Sealed:** `REPORT_PF-1.md`, `PF1_REPORT_v1_0.md`, architecture → v0.8, the
first reading preserved as an artifact, `pf1_findings.jsonl`.

**Governance close:** as prior waves — machine-derivable, red-team verdict from
a fresh-context Opus agent, `drift_detector.py` + `schema_validator.py` with
exit codes recorded.

**Transfers forward:**
- Remaining items from PG-1's 10-fix list not covered here.
- F-2's migration spec if parked, pending the OT-11 ruling.
- Q-2's stream observation → OT-12 (P0' scope decision).
- **If Q-2's verdict is poor: that becomes the next workstream's subject,**
  ahead of any render work. A working engine that reads badly is a different
  problem from a broken one, and it is the more important of the two.

---

## §D — Kickoff prompt

```
Open wave PF-1 per 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_PF1_ENGINE_RESURRECTION_v1_0.md.

You are the PF-1 conductor. Read, in order:
  1. CLAUDE.md
  2. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md
  3. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/ESCALATION_POLICY_v1_0.md
  4. 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/ADJUDICATOR_CHARGE_v1_0.md
  5. this brief
  6. 00_ARCHITECTURE/pg2_diagnostic/REPORT_PG-2.md  (the diagnosis being acted on)
  7. PG-2 Lane X-2 and X-5 shards  (exact root-cause evidence — do not re-derive)

Then execute the full 8-step lifecycle end to end, autonomously.

This is a WRITE WAVE. Binding constraints:
  - Two-phase verification is mandatory. Phase 1 merges a lane; only Phase 2,
    on the DEPLOYED app, closes the wave.
  - Arm the rollback pin (§B-2) before any deploy. Build-health failure →
    immediate rollback, no forward-fixing.
  - NO SCHEMA MIGRATIONS. If F-2 needs one, it PARKS with a costed spec (PC-4)
    — the OT-11 ledger ruling is open and may supersede it.
  - Scope creep is an automatic REJECT (PC-7). §F2 is absolute — in particular
    consult/route.ts is NOT touched; the route reorder is P0' work.
  - Worktree isolation enforced (§B-3).
  - Opus verification floor is not a cost lever. Q-2 runs at xhigh.
  - §5 pre-committed rulings govern every fork.

At §B-4, reproduce the 500 before fixing anything. If it no longer reproduces,
STOP and re-diagnose — something changed since PG-2.

The wave succeeds only if a real reading, produced by the deployed engine, is
persisted and graded against §J. A clean diff with an empty conversation store
is a failed wave. Report the §J verdict as found — a working engine does not
soften it (PC-2).

End with REPORT_PF-1.md and the §C close. Do not ask for confirmation —
§5 has pre-ruled every fork you can reach.
```

---

*End of BRIEF_PF-1 v1.0 (2026-07-19) — FROZEN, awaiting native kickoff.*
