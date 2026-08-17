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
