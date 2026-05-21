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

## Summary Table

| ID | Item | Source Session | Severity | Est. Sessions |
|---|---|---|---|---|
| CF.V13.1 | MSR signal-grounding gap (419/573 signals) | ICR-S2 | HIGH | 5–8 |
| CF.V13.2 | bootstrap build_manifests auto-registration | Phase 4C close | MEDIUM | 1 |
| CF.V13.3 | PLANNER_PROMPT pending-patch warning R-rule | ICR campaign scoping | LOW | 1 |
| CF.V13.4 | §N detector leaf vs networked signal classification | M5 close (MSR.387 fix) | LOW | 1 |

**Total carry-forward:** 4 items across 8–11 estimated sessions.
**V1.2 audit shipped:** 55 defects across 21 sessions (COV×10, PERF×5, ICR×6).

---

*End of V1_3_AUDIT_QUEUE_v1_0.md v1.0 — produced at M5 Coverage Campaign close 2026-05-21.*
