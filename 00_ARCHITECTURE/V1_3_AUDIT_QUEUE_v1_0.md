---
artifact: V1_3_AUDIT_QUEUE_v1_0.md
canonical_id: V1_3_AUDIT_QUEUE
version: "1.0"
status: LIVING
produced_during: M5_COVERAGE_CAMPAIGN_CLOSE_2026-05-21
produced_on: "2026-05-21"
authoritative_side: claude
role: >
  Carry-forward defect queue from the M5 Coverage Remediation Campaign v1.2 audit.
  Items in this queue were NOT resolved by the campaign's 21 sessions and are
  explicitly deferred to the next audit cycle (v1.3). Read before authoring the
  next CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0 revision.
predecessor_audit: 00_ARCHITECTURE/CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md (v1.2, SUPERSEDED-AS-COMPLETE)
mirror_obligations:
  claude_side: 00_ARCHITECTURE/V1_3_AUDIT_QUEUE_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  rationale: >
    Execution-planning artifact in Claude-resident governance layer. No Gemini-side
    counterpart; mirror_enforcer.py emits PASS_DECLARED_CLAUDE_ONLY.
changelog:
  - v1.0 (2026-05-21, M5_COVERAGE_CAMPAIGN_CLOSE): Initial queue; 3 carry-forward items
    deferred from M5 Coverage Campaign close.
  - v1.0.1 (2026-05-21, M5_COVERAGE_CAMPAIGN_CLOSE post-seal): Added Item 4 (CF.V13.4) —
    §N detector leaf vs networked signal classification, surfaced via MSR.387 manual fix
    verification. Queue now carries 4 items across 8–11 estimated sessions.
  - v1.0.2 (2026-05-24, R11.F_AUDIT_PRE_MERGE): Added Item 5 (CF.V13.5) —
    Lifecycle tab synthesis-stage tool call counter missing. Queue carries 5 items.
  - v1.0.3 (2026-05-24, R11.F_ROLLOUT_COMPLETE): Added Items 6+7 (CF.V13.6, CF.V13.7) —
    GitHub Actions no PR-level CI trigger; session discipline grep-all-SDK-sharing-adapters.
    Queue now carries 7 items across 9–13 estimated sessions.
  - v1.0.4 (2026-05-30, CI_AUDIT): Added Item 8 (CF.V13.8) —
    Python sidecar tests unconditionally soft-pass in ci.yml. Queue now carries 8 items.
  - v1.0.5 (2026-05-31, DOC_CLEANUP): CF.V13.1 partial resolution noted (DB layer RESOLVED,
    B.3 markdown layer OPEN). CF.V13.2 status check added (OPEN — CLAUDE.md §E claim
    unverified by commit ref). CF.V13.8 marked CLOSED (sidecar soft-pass removed 2026-05-30/31).
---

# V1.3 Audit Queue v1.0

Carry-forward defects from the **M5 Coverage Remediation Campaign** (21 sessions, v1.2 audit).
These items were explicitly surfaced but not resolved. Address before the next audit cycle.

---

## Item 1 — MSR Signal-Grounding Gap

**ID:** CF.V13.1
**Surfaced at:** ICR-S2 (L1 Truth Index scorer — MSR grounding coverage baseline)
**Severity:** HIGH (419 of 573 MSR signals lack explicit FORENSIC/LEL citations)

**Description:**
The ICR-S2 L1 Truth Index scorer computed that 419 of 573 MSR signals in MSR_v5_0.md
do not have explicit `l1_sources` citations anchored to FORENSIC_ASTROLOGICAL_DATA_v8_0.md
or LIFE_EVENT_LOG_v1_2.md. These signals rely on "as is known classically" or inherited
body text without a traceable L1 fact reference — a B.3 Derivation-Ledger violation per
PROJECT_ARCHITECTURE_v2_2.md §B.3.

**Scope of work:**
- Batch-review all 573 signals in MSR_v5_0.md
- For each signal lacking a `derivation_ledger` entry: either (a) add one pointing to
  a specific FORENSIC line, or (b) mark the signal `[EXTERNAL_COMPUTATION_REQUIRED]`
  with a spec for what L1 verification is needed per B.10

**Why deferred:** ICR-S2 was scoped to build the scoring infrastructure; the actual
signal backfill is a separate multi-session effort (estimated 5–8 sessions). DIS.013
was the highest-priority single signal, resolved in MSR-377-LIBRA-7H-CORRECTION.

**2026-05-26 partial resolution:** GISMCP Remediation (commit c6ff8ca5) verified
573/573 signals have non-null `source_citation` in the `msr_signals` DB table
(test: `msr_grounding.integration.test.ts`). This closes the DB-layer grounding gap.
The B.3 derivation-ledger gap (explicit FORENSIC/LEL citation IDs in the MSR
markdown file's `derivation_ledger` fields) remains open. These are distinct:
DB grounding = non-null source_citation; B.3 = traceable derivation path in the
markdown. Update the 419 figure by running a fresh B.3 audit against MSR_v5_0.md.
**Status: PARTIALLY RESOLVED (DB layer); OPEN (B.3 markdown layer)**

**Prerequisite for:** M6 Prospective Testing (predictions must trace to L1-grounded signals).

---

## Item 2 — Bootstrap `build_manifests` Auto-Registration Gap

**ID:** CF.V13.2
**Surfaced at:** Phase 4C close-out (2026-05-21); documented in CURRENT_STATE v5.28
  `open_followups` block and `00_ARCHITECTURE/CONDUCTOR/cv2final/B5_BOOTSTRAP_AUDIT.md`
**Severity:** MEDIUM

**Description:**
`platform/scripts/bootstrap_panchanga.py` does not auto-register a row in the
`build_manifests` database table when a bootstrap run completes. The gap was discovered
because build_id `phase-4c-20260519-153426` required manual rollback — the bootstrap
writer never registered its run, so the atomic swap guard couldn't distinguish it from
a prior partial run.

**Scope of work:**
- Add `INSERT INTO build_manifests (build_id, asset_id, status, row_count, created_at)`
  call to the bootstrap script's success path (after final verification count)
- Add `UPDATE build_manifests SET status='rolled_back', rolled_back_at=now()` on the
  rollback path
- Test: run a bootstrap with the new script; confirm `build_manifests` has the row;
  run rollback path; confirm status updates correctly

**Why deferred:** Non-blocking for the live enrichment dataset (73,414 rows currently
live and healthy). Manual rollback procedure is documented and operable. Fix is a
maintenance item, not a blocker.

**2026-05-31 status check:** CLAUDE.md §E Universal Parity Campaign claims this was
fixed in UDA-4. However, Phase 4C §E open follow-up (2026-05-21) documented this
as an audit item, and no subsequent session has explicitly marked CF.V13.2 resolved
with a commit reference. Until a session verifies the bootstrap script has auto-
registration and provides a commit SHA, this item remains OPEN.
**Action for next CI-hygiene session:** grep bootstrap_panchanga.py and
bootstrap_ephemeris.py for `INSERT INTO build_manifests`; if present, close with commit ref.
**Status: OPEN (conservative — defer to this queue over CLAUDE.md §E claim)**

---

## Item 3 — PLANNER_PROMPT: Warn on Pending-Patch Signal Citation

**ID:** CF.V13.3
**Surfaced at:** ICR campaign design phase (M5 Coverage Campaign scoping)
**Severity:** LOW

**Description:**
When the planner selects a signal (e.g., SIG.MSR.377) that has an open PROPOSED patch
in `00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/`, it currently has no mechanism to warn
that the signal may be under active correction. A query answered using a pre-correction
signal produces a response that is still erroneous even after the ICR patch system is
deployed and populated.

**Scope of work:**
Add to PLANNER_PROMPT_v2_0.md a new R-rule (e.g., R-PATCH-WARN):
> "Before citing SIG.MSR.NNN or any signal, check if a PROPOSED patch exists for that
> signal_id in CONFLICT_PATCHES/PROPOSED/. If yes, prepend a note: '[SIGNAL UNDER
> CORRECTION: see DIS.NNN]' to the signal citation."

The ICR weekly cron (deployed in ICR-S6) already populates PROPOSED/ automatically.
This R-rule ensures the planner surfaces the patch status to the user.

**Why deferred:** PLANNER_PROMPT edits require careful testing against the existing
few-shot suite (14 routing tests pass in CI). The R-rule is low-complexity but requires
a regression run. Deferred per ICR-S6 scope agreement.

---

## Item 4 — §N Detector Refinement: Leaf vs Networked Signal Classification

**ID:** CF.V13.4
**Surfaced at:** M5 Coverage Campaign close (2026-05-21) — MSR.387 manual fix verification
**Severity:** LOW

**Description:**
The §N detector's propagation walker currently treats every signal as networked — it
walks UCN/CGM/RM cross-refs unconditionally during an apply pass. For "leaf" signals
(those with no inbound references in UCN/CGM/RM), this propagation pass is wasted work:
there is nothing to walk. The detector should classify signals before walking and skip
the propagation pass for leaves.

**Proof case:** MSR.387's manual fix at commit `0ba67610` (M5 close 2026-05-21,
"Muntha embedded references — Virgo 6H → Libra 7H") had zero downstream cross-refs.
Verified via `git grep "MSR.387"` against UCN_v4_0.md, CGM_v9_0.md, and RM_v2_0.md —
all three returned empty. The single-file edit to MSR_v5_0.md was sufficient and
complete; a propagation walk would have been a no-op. Contrast with MSR.377 (DIS.013),
which is networked and required the full ICR-S5 atomic-apply path across multiple
surfaces.

**Scope of work:**
- Add a `classify_signal(signal_id)` function to the §N detector that returns
  `"leaf"` or `"networked"` by grepping UCN/CGM/RM (and any future cross-ref-bearing
  surfaces) for inbound references
- Branch the apply path: leaf signals get a single-file edit + `transaction_journal`
  entry with `propagation: none (leaf)`; networked signals continue through the
  existing full atomic-apply walker
- Unit tests: MSR.387 as the leaf gold standard; MSR.377 as the networked gold
  standard; one synthetic signal added to UCN mid-test to confirm reclassification
  on re-scan

**Why deferred:** Optimization, not a correctness gap. The current implementation
walks every signal but the walker is idempotent and fast — wasted work, not wrong
work. Improvement reduces apply latency and clarifies the transaction journal.

---

## Item 5 — Lifecycle tab does not count synthesis-stage (agentic loop) tool calls

**ID:** CF.V13.5
**Surfaced at:** R11.F PR #156 pre-merge audit (2026-05-24)
**Severity:** LOW

**Description:**
The Query Trace Lifecycle tab's RETRIEVAL row counts only pre-synthesis pipeline retrieval
calls (the deterministic `tool_fetch` stage). Tool calls fired by the R11.F agentic loop
during synthesis are emitted as `data-tool` events (route.ts:1060–1065) but do not
increment the RETRIEVAL counter. This means:

- In production, "0 tools fired" in the Lifecycle RETRIEVAL row is consistent with a
  fully-functional agentic loop response.
- To confirm tool execution post-R11.F, an operator must infer it from response content
  (specific dates, IKP/TRS citation anchors, sub-dasha tables) rather than reading a counter.
- Cloud Run log watch is the fallback: `[google-adapter]`, `[anthropic-adapter]` tool_use
  events are logged at DEBUG level.

**Scope of work:**
Add a synthesis-stage tool call counter to the Lifecycle tab. Route options:
1. Increment a separate "agentic loop tools fired" counter from the `tool_use_complete`
   event handler (route.ts:1060) and emit as a new `data-stage` part (`agentic_tools`)
2. Or extend the existing `data-tool` event to carry a `stage` field (`retrieval` vs
   `synthesis`) and update the Lifecycle UI to display both rows

Either option is additive/non-breaking. The Phase 2 post-R11.F log-watch procedure
(10-minute compressed monitoring) is the current operational substitute.

**Why deferred:** Not a correctness gap — tools are called and results used correctly.
Pure observability improvement. Appropriate scope for a Chat V2 R12 polish session or
a standalone P0 if a production debugging incident makes the gap acute.

---

## Item 6 — GitHub Actions: No CI on Feature Branches

**ID:** CF.V13.6
**Surfaced at:** R11.F rollout 2026-05-24 (3 consecutive failed deploys: PRs #156, #157, #158)
**Severity:** LOW

**Description:**
The GitHub Actions workflow has no `pull_request:` trigger. CI runs only on pushes to `main`. This means every PR-level regression is discovered post-merge, during Cloud Build/Deploy, rather than pre-merge. PRs #156, #157, and #158 each landed a regression that a PR-level CI run would have caught (TypeScript type error, import error, NVIDIA stream-type narrowing). Three failed deploys in sequence is a productivity and reliability signal.

**Scope of work:**
- Add `pull_request:` trigger to the existing test workflow (`.github/workflows/test.yml` or equivalent)
- Confirm the workflow runs `pnpm test` (or `vitest`) on the PR branch
- Optionally add branch protection rule requiring CI to pass before merge

**Why deferred:** Low-complexity fix but touches CI pipeline configuration. Appropriate for a hygiene session or v1.4 backlog item, not a blocking correctness issue.

---

## Item 7 — Session Discipline: Grep All SDK-Sharing Adapters Before Patching

**ID:** CF.V13.7
**Surfaced at:** R11.F rollout 2026-05-24 (NVIDIA hotfix 2a4e3c55 — extra hotfix cycle)
**Severity:** LOW (learning / process)

**Description:**
When triage identifies a regression pattern across multiple adapter files that share a common SDK base, the session discipline must include grepping ALL adapter files for the pattern before authoring the patch — not just the adapter where the symptom was first observed.

In R11.F, a stream-type narrowing error was patched in the Anthropic, Google, OpenAI, and DeepSeek adapters. The NVIDIA adapter was missed because it uses the OpenAI SDK as its base (not a standalone SDK). The oversight cost one extra hotfix cycle (PR #158, commit `2a4e3c55`).

**Scope of work:**
- Codify the following in the project's session-discipline checklist (GOVERNANCE_INTEGRITY_PROTOCOL or ONGOING_HYGIENE_POLICIES): "When patching a pattern across adapter files: (1) identify the SDK base for each affected adapter; (2) grep all adapters that share the same SDK base; (3) include all SDK-sharing adapters in the same patch, even if they showed no immediate symptom."
- The NVIDIA adapter's SDK base (`import ... from 'openai'`) is the canonical example to cite.

**Why deferred:** Process improvement, not a code defect. Current adapter files are in the correct state post-`2a4e3c55`. The learning is captured here for operationalization in the next governance pass.

---

## Item 8 — Python Sidecar Tests Unconditionally Soft-Pass in CI

**ID:** CF.V13.8
**Surfaced at:** CI/CD audit 2026-05-30
**Severity:** MEDIUM

**Description:**
`ci.yml` contains the following guard on the Python sidecar test step (line ~249):

```yaml
run: pytest ... || (echo "py-sidecar tests reported failures; treating as soft for now..." && true)
```

All failures from `natal_engine/tests/`, `pipeline/__tests__/`, and `tests/` are unconditionally swallowed. The comment "soft for now" has persisted across multiple workstreams with no target session to harden. The gate currently provides no signal — a complete sidecar breakdown would pass CI silently.

**Scope of work:**
1. Determine which sidecar tests require a live DB or external service and mark them with a skip guard (e.g., `pytest.mark.integration`) rather than swallowing all failures
2. Split the step into two: `pytest -m "not integration"` as a hard gate; `pytest -m integration` with `continue-on-error: true` and a clear label
3. Remove the `|| (... && true)` entirely from the hard-gate step
4. Confirm the hard gate exits non-zero on a real test failure before merging

**Target session:** Next ci-hygiene session or standalone `fix/sidecar-ci-gate` branch. Do not defer past the next sidecar-touching workstream.

**Why deferred (from today):** Requires understanding which sidecar tests need live infrastructure. Safe to do in isolation but not worth blocking the current CI audit PR.

**RESOLVED 2026-05-31:** `|| true` soft-pass removed from ci.yml governance-gates
pytest step (CI/CD cleanup session 2026-05-30). schema_validator gate also hardened
(continue-on-error removed) in Action A7 of CI cleanup session 2026-05-31. See
ci.yml governance-gates job. **Status: CLOSED**

---

## Summary Table

| ID | Item | Source Session | Severity | Est. Sessions |
|---|---|---|---|---|
| CF.V13.1 | MSR signal-grounding gap (419/573 signals) | ICR-S2 | HIGH | 5–8 |
| CF.V13.2 | bootstrap build_manifests auto-registration | Phase 4C close | MEDIUM | 1 |
| CF.V13.3 | PLANNER_PROMPT pending-patch warning R-rule | ICR campaign scoping | LOW | 1 |
| CF.V13.4 | §N detector leaf vs networked signal classification | M5 close (MSR.387 fix) | LOW | 1 |
| CF.V13.5 | Lifecycle tab synthesis-stage tool call counter missing | R11.F audit 2026-05-24 | LOW | 1 |
| CF.V13.6 | GitHub Actions: no `pull_request:` CI trigger | R11.F rollout 2026-05-24 | LOW | 0.5 |
| CF.V13.7 | Session discipline: grep all SDK-sharing adapters before patching | R11.F rollout 2026-05-24 | LOW | 0.5 |
| CF.V13.8 | Python sidecar tests unconditionally soft-pass in CI | CI audit 2026-05-30 | MEDIUM | **CLOSED 2026-05-31** |

**Total carry-forward:** 7 open items (CF.V13.1–CF.V13.7) across 9–13 estimated sessions. CF.V13.8 CLOSED.
**V1.2 audit shipped:** 55 defects across 21 sessions (COV×10, PERF×5, ICR×6).

---

*End of V1_3_AUDIT_QUEUE_v1_0.md v1.0.5 — CF.V13.1 partial resolution noted; CF.V13.2 status check added; CF.V13.8 CLOSED at doc cleanup 2026-05-31.*
