---
artifact: SATYA_DIPA_BRIEF (Satya-Dīpa — Make `lit` Mean Lit)
canonical_id: SATYA_DIPA_BRIEF
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-07-28
author: Cowork (Opus) planning session — native-commissioned
native_directive: >
  Authored after the ka_gochara_sweep self-correction: a dispatch loop reported success, an
  independent Verifier caught that `state='lit'` was a false positive, and the underlying defect was
  traced to the frozen orchestrator itself. The native authorized a dedicated wave to repair it —
  correctly refusing to let it be hot-patched inside an unrelated campaign.
source_documents:
  - platform/python-sidecar/pipeline/orchestrator/asset_runner.py:596–630 (the defect itself)
  - PARKED_FINDINGS_CLOSE_v1_0.md (the six parked items this wave inherits)
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_BRIEF_v1_0.md
    (THE METHOD — audit-first, adversarial verify, test-first, fix-at-origin, PARKED-HONEST.
     Reuse it verbatim; this wave applies it to build integrity instead of narration.)
  - 00_ARCHITECTURE/BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md §C (safety rails, inherited)
  - 00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (the FROZEN contract this wave
    is NARROWLY authorized to amend — see §9.1)
mode: >
  FULLY AUTONOMOUS · ONE Claude Code session · Conductor (Opus) + parallel Sonnet auditors +
  Sonnet fix builders in .worktrees/satyadipa-* + ONE dedicated Opus Verifier that NEVER writes
  code + ONE Dvārapāla that resolves every would-be human gate with a documented conservative
  decision · NO HUMAN GATES · PR + auto-merge only · wall-clock cap 10h ·
  PRIME RULE: truth over completion — PARKED-HONEST with evidence is a legitimate close.
authorization_grant: >
  Authorizes, without further human confirmation: a NARROW, surgical amendment to the FROZEN
  orchestrator promotion predicate in asset_runner.py (§9.1 — this is the one and only freeze
  exception); read-probes of production build state; corrective UPDATEs to dishonest
  asset_throughput rows, each snapshot-guarded; asset rebuilds where contamination is proven;
  a schema migration ONLY if a new honest state value is required (§4.3). Does NOT authorize:
  any other orchestrator change, modification of the sealed evaluator harness, edits to
  build_substep_progress data, or any Anthropic model in a production path.
---

# SATYA-DĪPA — Make `lit` Mean Lit

*Satya* = truth. *Dīpa* = lamp. An asset marked `lit` must actually be lit.

---

## §0 — The mission in one paragraph

The orchestrator promotes an asset to **`state='lit'`** whenever *any* data rows exist, without ever
checking whether the asset's substep plan actually finished. A partially-built asset — observed at
**78 of 303 substeps** — is therefore reported as complete. This is not merely a wrong status field:
`runner.py:439` and `staleness.py:77` both read `state IN ('lit','service_ok')` as
dependency-satisfied, so a falsely-`lit` asset **unblocks downstream DEP-ASSERTs** and lets other
assets build on incomplete upstream data. The rescue that causes this was written for a real and
correct reason (the D-1.6 incident: a resumable writer legitimately reports 0 rows because prior
substeps already committed, and marking it `dormant` poisoned 24 downstream assets). The intent was
right; the **predicate is weaker than the claim it licenses**. This wave repairs the predicate,
finds and honestly restates every asset currently mis-marked, assesses and remediates downstream
contamination, and sweeps the whole build layer for the same class of unearned success signal.

**This is the same disease as Śuddha-Vāca, one level up.** That campaign fixed prose asserting a
grade the facts didn't support. This one fixes the build system asserting *its own completion* from
a proxy that doesn't measure completion.

---

## §1 — Prime directives

1. **A PASS signal must have a detector behind it that measures the claim itself.** If it doesn't,
   it must be null / not-computed — never a clean-looking default. This is the doctrine the whole
   wave enforces.
2. **Preserve D-1.6.** The rescue exists to prevent *false blocking*. A resumable writer reporting
   0 rows whose substep plan **is complete** must still be promoted to `lit`. Any fix that
   reintroduces the ka_sangam→24-BLOCKED failure is a failed fix. This is a blocking acceptance
   criterion, not a nicety.
3. **Fix at origin, then repair the record.** Correcting the predicate does NOT fix rows already
   written dishonestly. Both are in scope; the second is the harder half.
4. **Never fabricate completion.** No asset is marked `lit` to make a number look right. If an
   asset is genuinely incomplete, it is recorded as incomplete and rebuilt or parked.
5. **Minimal surgical change to frozen code.** The freeze exception in §9.1 is a scalpel, not a
   licence. One predicate. Nothing else in the orchestrator.
6. **Truth over completion.** PARKED-HONEST with evidence is a legitimate close. No "passed with
   caveats."

---

## §2 — Phase 0 — RECONCILE & ARM

**0.1 Orientation.** Read CLAUDE.md §C chain, `CURRENT_STATE_v1_0.md §2`, this brief,
`PARKED_FINDINGS_CLOSE_v1_0.md`, and the Śuddha-Vāca brief (for method).

**0.2 Concurrency reconciliation (BLOCKING).** Determine, from branches / open PRs / campaign
artifacts, the live state of: **PARIPRAŚNA BUILD** (PB-4 may be pending or running), **PARISHODHANA**
(PRs #827/#828 were still open), and **ŚUDDHA-VĀCA** (status PARTIAL — two pre-authorized lanes,
`lane:serve-shadbala` and `lane:ga-tajaka`, waiting on those PRs). Dvārapāla issues a written
ruling: DISJOINT-PARALLEL / QUEUE-BEHIND / PROCEED-CLEAR, with a file-level disjointness proof.
**Satya-Dīpa holds rebuild exclusivity while it runs** — no other campaign may rebuild concurrently.
Preserve any uncommitted work under a named stash; never discard.

**0.3 Governance.** Emit the SESSION_OPEN handshake (`must_not_touch` non-empty), validate with
`schema_validator.py`.
**If root `CLAUDECODE_BRIEF.md` does not name SATYA-DĪPA, it is stale — commit the correct pointer
as your FIRST commit.** (A prior pointer was written to disk but never git-committed and was
silently reverted by a branch change. Do not repeat that.)

**0.4 Safety baseline (BLOCKING before any write).** Snapshot `asset_throughput` and every table a
candidate rebuild would touch. **Test the restore once and prove it works** — an untested rollback
is not a rollback. Record canonical invariants to re-assert: `chart_facts=27,554`,
`chart_dashas=536,471`, `chart_divisionals=21,635`, and FORENSIC 7/7.

---

## §3 — Phase A — AUDIT (read-only, parallel, adversarially verified)

**A.1 — Size the falsely-`lit` population (forensic lead: use the telemetry).**
Every false promotion emitted an event: `{"type": "asset.noop_completion", chart_id, asset_id,
run_id, rows_present}` (`asset_runner.py:616–622`). **Query the full history of that event type
first** — it is a near-complete register of every time this code path fired. Then, independently of
the events, reconcile directly: for every asset row at `state IN ('lit','service_ok')`, compare
completed substeps in `build_substep_progress` against the asset's full substep plan. Produce
`SATYA_DIPA_LIT_AUDIT_v1_0.md`: one row per (chart_id, asset_id) with substeps_done / substeps_planned
/ current state / honest state / whether an `asset.noop_completion` event exists.
**Read-only. `build_substep_progress` is evidence — never edited.**

**A.2 — Downstream contamination assessment.** For each falsely-`lit` asset, determine which
downstream assets consumed it while it was mis-marked (dependency edges + build timestamps + the
staleness graph). Classify each: **CONTAMINATED** (built on incomplete upstream, needs rebuild) ·
**CLEAN** (built before/after, or independently corroborated) · **UNDETERMINED** (say so plainly;
do not guess). Note: builds corroborated by row counts + FORENSIC + double-build determinism —
notably the Śuddha-Vāca rebuilds — should be re-confirmed CLEAN rather than assumed either way.

**A.3 — Sweep the class (the generalization).** Audit **every** status / PASS / completion signal in
the build and orchestration layer — `asset_runner.py`, `runner.py`, `global_runner.py`,
`staleness.py`, `dag_edge_guard.py`, `kala_derivation_completeness_guard.py`, `service_probes.py`,
and the cockpit's `count_sql` surface — asking of each: *what exactly does this measure, and does
that equal what it asserts?* Flag every proxy, tautology, hardcoded-clean literal, and detector-less
boolean. This is the Śuddha-Vāca D1–D7 method applied to build integrity.

**A.4 — Adversarial verification.** Every finding from A.1–A.3 is re-checked by a second agent
instructed to **REFUTE** it. Default to REJECTED when not concretely reproducible. Only
CONFIRMED / PLAUSIBLE enter the ledger. (In Śuddha-Vāca this caught a hallucinated finding — it is
not optional.)

---

## §4 — Phase B/C — FIX (test-first; the freeze exception)

**4.1 — Write the tests FIRST, prove they fail.** At minimum:
  - A partially-complete substep plan with rows present must **NOT** become `lit`.
  - **The D-1.6 regression:** a resumable writer reporting 0 rows with a **complete** substep plan
    **MUST** still become `lit`, and downstream deps must stay unblocked. *(Directive §1.2.)*
  - An asset with no substep plan defined behaves as before.
  - A run producing no rows and no prior data is still `dormant`.

**4.2 — The predicate.** In `asset_runner.py:607–624`, promotion becomes:
`rows present AND (substep plan complete OR no substep plan defined)`. The substep truth already
exists in `build_substep_progress` — the rescue simply never reads it. Keep the loud warning log and
the `asset.noop_completion` event for the legitimate path; emit a **distinct** event for the newly
rejected path so the telemetry stays diagnostic.

**4.3 — The honest state for a partial build.** It must NOT satisfy downstream dependency gating,
and it must NOT be `dormant` (that reintroduces the D-1.6 poisoning). Choose deliberately and record
the reasoning. **If a new enum value is required, it needs a migration AND the corresponding CHECK
constraint updated** — apply the enum-vocabulary audit pattern from the last wave (writer vocabulary
and CHECK constraint must agree) so this fix does not itself become a vocabulary-drift defect.

**4.4 — Secondary lanes (P1, independent worktrees).**
  - `ka_bhavishya_lekha.py` stale domain vocabulary — **can fail a live build**; highest-priority
    non-orchestrator item.
  - The silently-swallowed `chart_dashas` CLI-only sentinel.
  - The second L1 writer carrying the D1_MISSELECT class (unpinned `fact_key`).
  - Any P0/P1 promoted out of Phase A.

**4.5 — Discipline.** Opus Verifier adversarially reviews every diff and never writes code.
MAX_FIX_ATTEMPTS = 5 → PARKED-HONEST with a written spec. PR + auto-merge on green CI only.

---

## §5 — Phase D — REPAIR THE RECORD (snapshot-guarded)

1. **Restate** every falsely-`lit` row to its honest state, each with a diagnostic note recording
   substeps_done/planned and the evidence. Snapshot before, verify after.
2. **Rebuild** assets classified CONTAMINATED in A.2, in dependency order, on the canonical chart
   `482012f1-710e-4a25-994a-93821f5871aa` and the operator E2E chart `1c826d5a`.
   §N.3 idempotency: delete-then-insert per (chart_id × natural key); no accretion.
3. **Any failure → restore from snapshot, park the lane, continue others.** Never leave the DB
   half-written.
4. Assets that are genuinely incomplete and cannot be completed in this wave are left in an
   **honest** failed state with a diagnostic note — never cosmetically promoted.

---

## §6 — Phase E — PROVE (evidence, not assertion)

1. **D-1.6 does not recur** — the resumable-writer-with-complete-plan case still promotes to `lit`
   and unblocks downstream. *Demonstrate it, don't assert it.*
2. **Re-run the A.1 reconciliation** — zero assets remain `lit` with an incomplete substep plan.
3. **`ka_gochara_sweep` on the operator chart** reports its true state; if still incomplete, it says
   so honestly (78/303 was the observed reality — a green here without a real build is a failure).
4. FORENSIC 7/7 PASS · canonical row counts hold or every delta explained · zero regressions across
   all suites · `drift_detector` + `schema_validator` green · the Śuddha-Vāca `fact_key` CI lint and
   the new vocabulary-drift CI job both still passing.
5. **A new permanent guard** exists so this class fails in CI, not in production.

---

## §7 — Phase F — CLOSE

`SATYA_DIPA_REPORT_v1_0.md` with a disposition table over every finding — **VERIFIED-FIXED /
PARKED-HONEST / REJECTED / NOT-APPLICABLE**, no "passed with caveats" — opening with a plain-language
answer to: *can `lit` now be trusted as evidence of completion, and where can it not?* Include the
falsely-`lit` population size, before/after states, and the D-1.6 regression proof.

Add **CLAUDE.md §N.8 — Earned-Signal Principle**, drawn from what the code now enforces: *every
status, grade, or PASS must be computed by a detector that measures the claim it asserts; a signal
without such a detector is null, not green.* Cite the five known instances (Ṣaḍbala selector, the
two `bo_pramana_mapa` flags, the PB-2 byte-equality gate, this `lit` promotion) as the evidentiary
basis.

Governance close: SESSION_CLOSE checklist → `schema_validator` → atomic SESSION_LOG append →
CURRENT_STATE update → registry hygiene → worktree cleanup → restore any Phase-0.2 stash.
**Carry forward, do not drop:** ŚUDDHA-VĀCA remains PARTIAL with two pre-authorized lanes
(`serve-shadbala`, `ga-tajaka`) pending PARISHODHANA #827/#828. Re-check those PRs and, if landed,
say so in the report so the next session can release them immediately.

---

## §9 — Hard boundaries

**9.1 — THE FREEZE EXCEPTION (the only one).** This wave may modify the promotion predicate in
`asset_runner.py:596–630` and nothing else in the orchestrator. Any other orchestrator change →
Dvārapāla records `CONTRACT-CHANGE-REQUIRED` + `PARKED-HONEST` with a written spec; the lane stops,
others continue. The amendment must be documented in `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` as an
authorized, dated exception so the freeze record stays truthful.

- **`build_substep_progress` is READ-ONLY evidence.** Read it; never write it. It is the ground truth
  this entire wave depends on — mutating it would destroy the only honest record of what was built.
- The sealed evaluator harness is never modified.
- No Anthropic model in any production path.
- Surgical migrations only (§4.3 is the sole anticipated case).
- No JH-parity oracle anywhere.
- main via PR + auto-merge only, CI green.
- Budgets: inherit AUTONOMOUS_MODE §C ceilings; 10h wall-clock; MAX_FIX_ATTEMPTS=5 → park.

---

## §10 — Acceptance criteria

1. The promotion predicate consults the substep plan; a partial build can never be `lit`.
2. **The D-1.6 regression test passes** — resumable-writer-with-complete-plan still promotes and
   unblocks. (Blocking. A fix that trades false-unblocking for false-blocking is not a fix.)
3. The falsely-`lit` population is fully enumerated (telemetry + independent reconciliation) and
   every row restated honestly, snapshot-guarded.
4. Downstream contamination is classified CONTAMINATED / CLEAN / UNDETERMINED, with CONTAMINATED
   assets rebuilt or explicitly parked. UNDETERMINED is stated, never guessed.
5. The build-layer class sweep (A.3) is complete; every detector-less PASS signal is fixed or nulled.
6. `ka_bhavishya_lekha` vocabulary drift fixed and covered by the CI job.
7. FORENSIC 7/7 PASS; canonical invariants hold or deltas explained; zero regressions.
8. A permanent CI guard for this class is merged and passing.
9. `SATYA_DIPA_REPORT_v1_0.md` with a complete four-disposition table.
10. Governance closed atomically; ŚUDDHA-VĀCA's two parked lanes explicitly carried forward.

---

## §11 — What the native wakes to

A report that opens by answering, in plain language: **can `lit` be trusted now, how many assets were
lying, and what was built on top of them.** Then the disposition table. Then the D-1.6 proof. Nothing
that requires him to reconstruct the reasoning himself.

*End of SATYA_DIPA_BRIEF v1.0.*
