---
artifact: CLAUDECODE_BRIEF_LLM_CONSUMPTION_REMEDIATION
type: CLAUDECODE_BRIEF (master conductor kickoff — single-prompt, fully autonomous program)
version: 1.0
status: ACTIVE  # ratified by native, 2026-07-12, via Cowork session LLM-CONSUMPTION-REMEDIATION-PLANNING-2026-07-12
# ── STATUS GATE (binding): if status is STAGED, DO NOT EXECUTE. Report readiness and stop.
#    The native flips status to ACTIVE as the single ratification act (plan §8.5).
#    ACTIVE status IS the standing authorization for commit/merge/push/deploy/rebuild
#    within the plan's scope. On program close, the conductor sets status: COMPLETE.
#    Predecessor brief (AUDIT_BRIEF_FOUNDRY v1.1, COMPLETE 2026-07-12) preserved in git
#    history at commit 1a00cbee.
authored_by: Fable 5 (Cowork) + native, session LLM-CONSUMPTION-REMEDIATION-PLANNING-2026-07-12
session_type: claude_code_autonomous_conductor (no human gates; async native visibility via run ledger)
governing_plan: 00_ARCHITECTURE/llm_consumption_audit/REMEDIATION_PLAN_v3_0.md
normative_wp_text: 00_ARCHITECTURE/llm_consumption_audit/REMEDIATION_PLAN_v2_0.md §5 + §6.1-6.4
coverage_manifest: 00_ARCHITECTURE/llm_consumption_audit/deliverables/wp_coverage.jsonl
chart_ids: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek, native) · 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan, verification)
run_ledger: 00_ARCHITECTURE/llm_consumption_audit/REMEDIATION_RUN_LEDGER_v1_0.md (create at kickoff)
may_touch:
  - platform/**                                  # serving, MCP contract, writers, sidecar, registries
  - platform/migrations/**                       # SURGICAL migrations only (§N.4)
  - 00_ARCHITECTURE/llm_consumption_audit/**     # run ledger, reports, coverage updates
  - 00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md   # disposition flips only
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md        # wave-close updates
  - 00_ARCHITECTURE/SESSION_LOG.md               # session closes
  - CLAUDECODE_BRIEF.md                          # status field only
must_not_touch:
  - platform/python-sidecar/pipeline/orchestrator/core/**   # FROZEN contract (§N.2) — HALT if a change seems needed
  - 00_ARCHITECTURE/llm_consumption_audit/deliverables/findings.jsonl   # audit history immutable
  - 00_ARCHITECTURE/llm_consumption_audit/state/**                      # audit shards immutable
  - 00_ARCHITECTURE/llm_consumption_audit/LLM_CONSUMPTION_AUDIT_v1_0.md # immutable
  - 00_ARCHITECTURE/llm_consumption_audit/GATE_RATIFICATION_v1_0.md     # immutable
  - CLAUDE.md
  - 01_FACTS_LAYER/**                            # LEL is native-authored
  - "eval battery grading criteria (any file)"   # no gate-gaming (R5.3 precedent)
---

# CONDUCTOR KICKOFF — LLM Consumption Remediation (W0 → W4, one run)

## 0 — Status gate
If frontmatter `status` ≠ ACTIVE: emit "STAGED — awaiting native ratification (plan
§8.5)" and stop. Do not execute anything below.

## 1 — Mission
Execute REMEDIATION_PLAN_v3_0 end-to-end, fully autonomously: W0 → W1 → W2 → W3 → W4 →
cleanup+close. The end state is the plan's §1 constitution (E1-E7) — every intervention
and every verification is graded against it. Exit: W4 gates (plan §2/§8.1) pass, or
honest halt within the §8.4 iteration budgets. No human gates exist; the §8 rulings are
your pre-ratified authority for every decision the plan anticipates. Decisions the plan
does NOT anticipate that would change scope, contract, or entitlement → HALT per §8.6.

## 2 — Read order (before any work)
1. This brief. 2. REMEDIATION_PLAN_v3_0.md (whole). 3. REMEDIATION_PLAN_v2_0.md §5+§6
(normative WP + verification text). 4. wp_coverage.jsonl (your coverage contract).
5. MARSYS_DEFECT_GAP_REGISTER_v2_0.md rows LCA-1..19, R-37..48, KP-4. 6. The audit
consolidation report + GATE_RATIFICATION (E-2/E-4/E-5/E-6/E-7c/E-8). 7. Standard session
mandatory reading per CLAUDE.md §C (CURRENT_STATE, governance protocol, orchestrator
convergence close, L2 traps — MSR drift + UCN contamination).

## 3 — Self-provisioning (first acts)
a. Repo: fetch; assert main == origin/main and clean tree (else reconcile or HALT).
b. Create REMEDIATION_RUN_LEDGER_v1_0.md (state machine: wave → WP → intervention →
   verification verdicts → merge/deploy records). Every sub-session opens by reading it,
   closes by appending. It is the program's memory (plan §7.7).
c. Probe (read-only): DB via proxy; deployed MCP channel (both charts, one call each);
   deploy credentials; CI. Record results in the ledger.
d. Session governance: emit session_open handshake per §G (session_id
   LLM-CONSUMPTION-REMEDIATION-W0-<date> and per-wave thereafter).

## 4 — Execution (delegate; never implement in the conductor context)
Per wave, per plan §4 DAG:
- Spawn WP-conductor sub-sessions (fresh context each, re-grounded from ledger+plan).
- WP conductors decompose into intervention briefs, spawn implementation agents in git
  worktrees (one lane per disjoint file scope; parallel-first per §6.2), then spawn the
  assigned DOMAIN VERIFIERS (v2 §6.4 roster: jyotish-domain, serving-wire, data-plane,
  security/entitlement, infra) for BLIND per-intervention verification (v2 §6.3: the
  original failing audit call re-executed + adversarial probes + quoted payloads + both
  charts; false-negative sampling; disagreement → conductor live retest).
- Merge per WP close (conductor-owned; zero-regression suite on merge result: R6A
  yoga-integrity tests + WP-0.1 concurrency harness once it exists + canary battery).
- Wave close: push → DEPLOY per plan §7.4 (W0, W1, W2, final) → live prod
  re-verification of the wave's full acceptance suite by verifiers → CURRENT_STATE +
  SESSION_LOG close → next wave.
- W3: plan §7.5 verbatim (snapshot → Abhinandan cascade on deployed W2 code → full
  acceptance suite → golden catches → native-chart rebuild behind green, FORENSIC 7/7
  mandatory → auto-restore on any failure).
- W4: plan WP-4.1 — frozen instruments, E-5 swarm + E-6 depth gate, demand-side mode
  against the WP-1.6 capability map; gates evaluated mechanically; loop owning WPs
  within budget; never lower a gate.

## 5 — Non-negotiables (inherited, enforced per intervention)
FROZEN orchestrator (§N.2 — needed change = HALT) · §N.3 idempotency · B.10 no
fabricated computation · B.3/§N.5 derivation ledgers + referential integrity
(constituent fact_ids MUST resolve — CI validator ships in WP-2.4) · surgical
migrations only (§N.4) · no manual DML on product tables · no entitlement widening
(standing security-agent check on every chart-scoped change) · no gate-lowering ·
audit artifacts immutable · commit format: conventional, citing WP + finding IDs
(e.g. `fix(wp-1.3b): honor system_id in query_dasha_periods [F-0354]`) · honest
NOT-MET beats gate-gaming.

## 6 — Cleanup + close (plan §7.6, all five steps, in order)
Branches/worktrees audited and removed (ledger-reconciled; no orphans on origin) ·
main pushed and clean · **main↔production sync PROOF (deployed commit SHA(s) ==
origin/main HEAD, recorded verbatim in the close report — "probably deployed" does not
close the program)** · post-deploy canary + one demand-side consumption session green
on production · register dispositions + TRACEABILITY remediation column +
CURRENT_STATE + SESSION_LOG atomic close · this brief → status: COMPLETE · ledger
sealed.

## 7 — Kickoff line (for the native, after flipping status to ACTIVE)
> Execute CLAUDECODE_BRIEF.md.

*End of brief v1.0 — STAGED.*
