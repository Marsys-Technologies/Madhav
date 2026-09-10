---
artifact: CROSS_CUTTING_DECISION_REGISTER_v1_0.md
version: 1.0
status: LIVING
role: >
  Append-only, tool-neutral register for decisions not owned by a live campaign ledger.
  CCD identifiers are resolved from this file at session close.
update_rule: >
  Append only. Never renumber, rewrite, or delete entries. Supersede a decision with a
  later CCD entry that names the earlier identifier.
---

# Cross-Cutting Decision Register

## How to use this register

Use this register only for a decision that is not owned by an active campaign ledger.
At session close, resolve the next `CCD-NNN` identifier from the live register, append
the decision with tool/date provenance, and reference the session, work-order, and
coordination lease that produced it.

| ID | Date | Tool | Status | Decision |
|---|---|---|---|---|
| CCD-001 | 2026-08-15 | Codex | ACTIVE | Establish Claude Code/Codex shared-brain parity: tool-neutral state, decision, lease, and session-log protocol; exclusive env-authenticated `marsys-jis` Codex MCP surface; Codex instruction and skill bridges. |
| CCD-002 | 2026-08-15 | Codex | ACTIVE | Round-trip acceptance marker: Codex wrote this bounded state change; a fresh Claude Code session must cite CCD-002 before appending its successor. |
| CCD-003 | 2026-08-15 | Claude Code | ACTIVE | Round-trip acceptance successor: Claude Code consumed CCD-002 and wrote CCD-003; a fresh Codex session must cite both identifiers. |
| CCD-004 | 2026-08-15 | Codex | ACTIVE | Close the onboarding verification: the canonical `.claude/skills` inventory is four active skills, not five; retain the MCP credential-rotation and validator-debt follow-ups as shared owner-visible work. |
| CCD-005 | 2026-08-17 | Codex + Autonomous Executive Pratinidhi (Sol Ultra independent review) | ACTIVE | Establish the standing PARIŚEṢA Autonomous Executive Pratinidhi and reconcile the historical MACRO_PLAN canonical-record drift to the independently verified v2.1 source on origin/main. |
| CCD-006 | 2026-08-17 | Codex / PARIŚEṢA Phase −1 | ACTIVE | Bootstrap the user-authorized PARIŚEṢA autonomous recovery under its exact runbook scope after the validated canonical-provenance handshake. |
| CCD-007 | 2026-08-17 | Codex | ACTIVE | Authorize PARIŚEṢA–RĀTRI V4 execution-first remediation under the operator-approved V4 prompt, while keeping V3 suspended and its state immutable. |
| CCD-008 | 2026-08-19 | Codex | ACTIVE | Record the owner-authorized PARIŚEṢA V4 Governance Bridge close: adopt the Closure Factory plan and hand off safely to Claude Code without beginning implementation; the exact bridge lease was released before evidence-only close finalization under the owner’s 2026-08-19 ordering ruling. |
| CCD-009 | 2026-08-20 | Claude Code | ACTIVE | Record the real-time owner authorization for a Claude-Code-driven PARIŚEṢA V4 Phase 0 truth-cut and bounded repair-wave session, closing the gap CCD-007 (Codex-scoped) and CCD-008 (close-mechanics-only, explicitly not exercising CCD-007) left open; no merge/deploy/data/infra exception granted. |

## CCD-001 — Cross-tool onboarding and operating protocol

- **Authority:** native approval in the Codex onboarding session, 2026-08-15.
- **Rationale:** project-wide decisions previously had no canonical, monotonic, tool-neutral
  home. Codex and Claude Code need one durable state surface rather than chat-history handoffs.
- **Affected surfaces:** this register; `CURRENT_STATE_v1_0.md`; governance protocol; session
  templates and validator; Codex profiles; instruction/skill bridges.
- **Coordination:** L-11 on `campaign-coordination`; documentation/tooling only, no deploy,
  build/rebuild, database, migration, or application-code scope.
- **Supersession:** none.

## CCD-002 — Round-trip acceptance marker

- **Date:** 2026-08-15.
- **Tool:** Codex.
- **Status:** ACTIVE.
- **Decision:** Round-trip acceptance marker: Codex wrote this bounded state change; a fresh Claude Code session must cite CCD-002 before appending its successor.

## CCD-003 — Round-trip acceptance successor

- **Date:** 2026-08-15.
- **Tool:** Claude Code.
- **Status:** ACTIVE.
- **Decision:** Round-trip acceptance successor: Claude Code consumed CCD-002 and wrote CCD-003; a fresh Codex session must cite both identifiers.

## CCD-004 — Onboarding closure verification and standing follow-ups

- **Authority:** native closure instruction in the Codex onboarding session, 2026-08-15.
- **Skill-inventory correction:** the canonical `.claude/skills` tree contains exactly four
  active, valid skills — `create-migration`, `pr-description`, `run-checks`, and
  `session-close`. The reported fifth skill was an audit-count error: no fifth directory,
  `SKILL.md`, hidden entry, archived entry, or ignored entry exists in the worktree or
  `origin/main`. Codex discovery through `.agents/skills` is therefore complete at four,
  not a symlink-discovery failure.
- **SECURITY — owner action:** the pre-existing global Codex configuration contains an inline
  MCP credential in a URL. Rotate that credential and convert the global configuration to
  environment-sourced authentication; this is not repository work and was not changed here.
- **DEBT — shared dual-tool follow-up:** repository-wide validation retains schema 43 and drift
  218 findings. They predate this onboarding, are shared debt under the dual-tool protocol, and
  are a candidate first owner-authorized Codex assignment.
- **Supersession:** none.

## CCD-005 — PARIŚEṢA Autonomous Executive Pratinidhi and macro-plan provenance reconciliation

- **Authority:** direct native instruction, 2026-08-17; applies to the controlling PARIŚEṢA runbook.
- **Standing mandate:** the conductor remains the sole orchestration authority. The Autonomous
  Executive Pratinidhi is its independent executive, domain, governance, and recovery partner:
  it challenges evidence, makes ordinary in-scope decisions, keeps verification elastic, records
  material decisions/dissent/actions, and classifies surprises for bounded recovery. High-blast
  governance, migration, security, production-data, and architecture actions require two-key
  agreement between conductor and an appropriately escalated independent Pratinidhi reviewer.
- **Model routing:** Terra High is the routine executive default; Luna/deterministic tooling
  handles mechanical work; Sol High handles bounded difficult rulings; Sol XHigh terminal
  red-team; Sol Ultra exceptional high-blast adjudication. Pools scale by measured bottleneck and
  are retired when idle.
- **Decision:** reconcile the historical `CANONICAL_ARTIFACTS_v1_0.md` MACRO_PLAN row from
  v2.0 / `2fef28fdcfa54c425ce96c0dd82e8016a47d907545915139c39688f19ab451c3` to v2.1 /
  `8e98ad46d7f0ba5ee4a9605f17f8ef21ba6da6d126092f7e0c52d318bc9e6c6e`; do not alter the
  macro-plan bytes. The registry is superseded for tooling by CAPABILITY_MANIFEST after the
  2026-04-27 cutover, but remains a session-provenance and audit surface.
- **Evidence:** origin/main at `f003bf3af3b372eb5c1365ca4753a95aba4b7551` contains the
  v2.1 bytes. Independent Sol Ultra review approved the transition after reading `ee5bf081`,
  `055165b`, `43ff2f1`, `96f30bc`, and `449d2c3`; the changes are governed naming, layer,
  metadata, and factual-count corrections, not an unreviewed hash substitution.
- **Coordination:** `PARISESA-PREFLIGHT-AUTHORITY-2` on origin/campaign-coordination;
  documentation/governance only. No application code, migration, deployment, rebuild,
  production data, or campaign takeover authority is granted by this decision.
- **Dissent:** none. The Pratinidhi noted that the pre-cutover baseline commit is
  `18566190` in origin/main's lineage; `6982a24` is byte-equivalent context rather than its
  ancestor.
- **Supersession:** none.

## CCD-006 — PARIŚEṢA Phase −1 bootstrap authority

- **Authority:** direct native owner instruction in
  `PARISESA_CODEX_AUTONOMOUS_EXECUTION_PROMPT_V3_SOL_ULTRA.md`, SHA-256
  `f2bc25ae0ff080434179271efeeada492fde33d72234cf0fe7bf85e1b9f0d6b9`; validated
  Phase −1 continuation handshake under `PARISESA-PREFLIGHT-AUTHORITY-3`.
- **Decision:** authorize the PARIŚEṢA recovery runbook's campaign-only bootstrap sequence,
  including subsequent governed production/deployment/migration actions only when every later
  runbook gate and the applicable coordination lease permits them. There is no monetary hard cap.
- **Exact bootstrap may-touch:** the coordination lease row; this append-only CCD register entry;
  required session provenance; temporary Phase −1 receipts and tracker canary.
- **Bootstrap must-not-touch:** application code, database/data, migrations, deployment,
  rebuilds, production writes, legacy-process control, and campaign takeover before every hard
  preflight completes.
- **Supersession:** solely for this campaign's one bootstrap operation, supersedes
  `GOVERNANCE_INTEGRITY_PROTOCOL §P.4`'s lease-row-only restriction. No other governance rule
  is superseded.
- **Evidence:** PR #1317 merged through the required queue at
  `origin/main@8ee2c7d6774a9599bc5aa0b7c423b8faf5b8b153`; the reconciled MACRO_PLAN
  fingerprint is `8e98ad46d7f0ba5ee4a9605f17f8ef21ba6da6d126092f7e0c52d318bc9e6c6e` and the
  refreshed Phase −1 handshake validates it.
- **Dissent:** none.

## CCD-007 — PARIŚEṢA–RĀTRI V4 execution-first remediation authority

- **Authority:** operator-approved `PARISESA_CODEX_EXECUTION_FIRST_PROMPT_V4_SOL_XHIGH.md`,
  SHA-256 `de10ade728e0402608d7783f9bf6db9348653b6487b64cf98222f185b818ef65`,
  2026-08-17.
- **Scope:** V4 may perform local diagnosis, fresh-worktree implementation, focused tests,
  independent review, run-owned branch/PR work, and—only with separately recorded proof—governed
  merges, deploys, migrations, and bounded data repair. The live V4 tracker and append-only
  receipts live under `/Users/Dev/shad_overnight/par-night/state/codex-v4/`.
- **Prohibitions:** do not restart, revive, or mutate V3 supervisor/worker/lease/recovery state;
  do not alter frozen orchestrator contracts, perform broad chart rebuilds, touch credentials or
  infrastructure, delete broadly, or change the immutable 141-finding corpus.
- **Supersession:** for V4 work mechanics only, supersedes the prior GIP P.3/P.4 lease-before-work
  requirement. It does not supersede product, safety, migration, deployment, or evidence controls.

## CCD-008 — PARIŚEṢA V4 Governance Bridge close and Claude Code handoff

- **Authority:** direct owner authorization, 2026-08-19, titled
  `OWNER AUTHORIZATION — PARIŚEṢA V4 GOVERNANCE BRIDGE CLOSE`.
- **Decision:** acquire and release one isolated, remote-verified governance lease; adopt the
  exact Closure Factory plan; record the blocked Codex drain and preservation manifest; and
  establish a safe Claude Code handoff. This decision authorizes only governed close mechanics.
- **Exact scope:** session-open/close validation, CCD and registry synchronization, canonical plan
  adoption, CURRENT_STATE and SESSION_LOG synchronization, superseding handoff receipt, and lease
  release.
- **Prohibitions:** Phase 0, finding remediation, worker dispatch, application or platform code,
  migrations, database/data activity, deploys, scheduler or infrastructure changes, credentials,
  customer action, and any mutation of preserved or foreign worktrees.
- **Coordination:** lease
  `PARISESA-V4-GOVERNANCE-BRIDGE-CLOSE-20260819T181916Z` on
  `origin/campaign-coordination`, acquisition commit
  `a45a09066366d67a68df64d42ec2781a8acc075f`, released and remotely verified
  at `1d5a378bd171bae15bd6b5b3c89437d22de18827`.
- **Ordering ruling:** `OWNER RULING — PARIŚEṢA V4 POST-RELEASE CLOSE
  FINALIZATION`, 2026-08-19, supersedes only the prior instruction that this
  bridge lease be released after merge. For this already-released bridge it
  authorizes evidence-only close finalization, checklist validation, and
  SESSION_LOG synchronization before the normal protected documentation PR and
  merge path. It does not alter the general SESSION_CLOSE schema or authorize
  campaign implementation.
- **Predecessor evidence:** blocked receipt
  `PARISESA_V4_CODEX_STOP_RECEIPT_20260819T175939Z.md` SHA-256
  `2c1401a5d86a7feefe4372cb3a44f2b5dc3ed877c35b827d2aa2a4d523b830e7`;
  preservation manifest SHA-256
  `bd0fbc1c47dcdc53f9e86364419b797dbae48b271e805e67279757c595f9b08d`.
- **Supersession:** none. CCD-007 remains the future execution authority but is not exercised by
  this bridge.

## CCD-009 — PARIŚEṢA V4 Claude Code execution authorization (Phase 0 + bounded repair waves)

- **Authority:** direct, real-time owner instruction in the live PARISESA-V4-CONDUCTOR-20260820T005119Z
  Claude Code session (2 turns: the full campaign kickoff prompt, then explicit confirmation
  "Go ahead and from here on don't ask me any questions. Autonomously execute the entire thing
  without any interruptions or questions."). Given after this session had already independently
  read the Closure Factory plan v1.0 and surfaced, in-session, that neither CCD-007 (scoped to
  Codex-run V4 only) nor CCD-008 (the Governance Bridge close that opened this Claude Code
  session, whose own Prohibitions clause explicitly bars Phase 0 and finding remediation) grants
  execution authority to a Claude-Code-driven Phase 0/repair wave, and that the plan's own §13.5
  Gate A calls for an owner approval pause between Phase 0 and any repair wave.
- **Decision:** this session proceeds into Phase 0 truth-cut reconciliation and bounded repair
  waves (code/test/review/PR-open only) under the real-time owner authorization above. The
  Closure Factory plan itself specifies no self-ratification mechanism for skipping a live Gate
  A sign-off (its §13.5 reserves that pause for the owner) -- this session instead applies, as
  its OWN compensating construct in lieu of Gate A (not something the plan grants or contains),
  a self-devised truth-cut check: mechanical invariants pass + 3-subagent default-REFUTED panel
  majority non-refutation. This distinction is recorded here precisely so a future reader does
  not mistake this session's own substitute check for a plan-granted exemption -- GA-5 review of
  PR #1362 (this CCD's own PR) flagged the original wording as attributing to the plan an
  authority it does not contain; corrected before merge, not after.
- **Exact scope:** Phase 0 reconciliation (read-only), Phase 1 tracker-spine build, Phases 2-5
  repair waves through independent review and PR-open-and-frozen only, on the 141-finding corpus
  at `/Users/Dev/shad_overnight/par-night/state/codex-v4/closure-matrix.json` (immutable per
  CCD-007's own prohibition — this session re-verifies row *disposition*, it does not add, remove,
  or renumber corpus rows).
- **Prohibitions (unchanged from every other governing document tonight — this CCD grants no
  exception to any of these):** merge-queue admission, production deployment, protected-data
  packet execution, any production-sync action, credentials/infrastructure changes, V3
  supervisor/worker/lease state, frozen orchestrator contract changes, broad chart rebuilds,
  broad deletes, mutation of any foreign or sibling-campaign worktree/branch/namespace.
- **Coordination:** session-open/lease-supersession entry on `origin/campaign-coordination`,
  commit `a8e5c03f7`. Full reasoning recorded as PROVISIONAL_RULING PR-001 in this session's own
  journal, `parisesa/campaign-state` commit `7298884e9`, flagged for morning ratification.
- **Supersession:** none of CCD-005 through CCD-008. This is additive authority for the specific
  gap those left open, not a revision of their own stated scopes.
