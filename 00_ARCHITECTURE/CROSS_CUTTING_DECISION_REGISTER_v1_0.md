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
| CCD-010 | 2026-09-12 | Codex | ACTIVE | Adopt Madhav Product Definition v3.0 as the final target for subsequent product planning; authorize its bounded documentation registration/local commit and one-time actual managed-profile exception. No application, campaign, data, deployment, product push or merge authority. |
| CCD-011 | 2026-09-14 | Codex | ACTIVE | Record the native-delegated MADHAV PŪRṆA ANVEṢAṆA source campaign: inspect, design, implement, test, document, commit, push and open focused/stacked PRs in isolated worktrees, while prohibiting merge, deployment, shared/production migration application, production mutation, credentials/infrastructure, retirement, doctrine ratification and unsupported acceptance claims. |
| CCD-012 | 2026-09-15 | Codex | ACTIVE | Supersede CCD-011's source-only ceiling for the governed Pūrṇa live-release wrap-up while retaining exact-candidate, safety, serialization, evidence and no-fabrication gates. |
| CCD-013 | 2026-09-27 | Codex → Claude Code | ACTIVE | Authorize the isolated Jātaka chart-workspace workstream to implement and commit plan Tasks 1–8 locally under an exact file allowlist, reserve cross-cutting migration 1120 through JATAKA-REQ-01, and keep browser/full-recompute acceptance blocked until a non-production Firebase project, disposable local PostgreSQL database and approved L0 seed/snapshot exist. |
| CCD-014 | 2026-09-27 | Native → Claude Code | ACTIVE | Authorize the narrow Jātaka Phase-A integrity-hardening follow-up (correction-history write doors, context staleness or stop-and-report, reading-door readiness parity, safe birthplace edits, persistence-boundary recheck) under the hardening addendum; reserve cross-cutting migration 1121 through JATAKA-REQ-02; Task 9 remains blocked. |
| CCD-015 | 2026-09-27 | Native → Claude Code | ACTIVE | Authorize the narrow Jātaka Phase-A2 integrity session (chart-context staleness end to end or stop-and-report per consumer, `prashna_ask` and `chat/build` reading-door gates, terminal/persistence/retry/stale/serving-impact correctness, migration 1121 security disposition) under the Phase-A2 addendum; reserve cross-cutting migration 1122 through JATAKA-REQ-03; Task 9 remains blocked. |
| CCD-016 | 2026-09-27 | Native → Claude Code | ACTIVE | Authorize the Jātaka Phase-A3 source-integrity pass (chart-context staleness for brahma_mimamsa_prediction_ledger, brahma_prospective_ledger, mimamsa_calibration_snapshot; a reviewed technical head with independent review) and two separately governed source-evidence refreshes at that head (a narrow Nirmāṇa L5 successor re-pin; a Pūrṇa Beyond-Ācārya v7 successor preserving v6) under the Phase-A3 addendum; reserve cross-cutting migration 1123 through JATAKA-REQ-04; Task 9 remains blocked. |
| CCD-017 | 2026-09-27 | Native → Claude Code | ACTIVE | Authorize a separately governed follow-up (Phase-A3 closed, not reopened) diagnosing and correcting the Nirmāṇa L0/L5 receipt-checker cross-layer coupling responsible for the two `nirmana-analysis-receipts.test.ts` failures the Phase-A3 close reported and did not fix; correction preferred over refreshing `L0_FROZEN_PINS`; no L0 evidence change, no further L5 re-pin unless L5 source identity genuinely changed, no database access, no Task 9. |
| CCD-018 | 2026-09-27 | Native → Codex | ACTIVE | Authorize a controlled production rollout of the reviewed Jātaka chart-workspace candidate, superseding only the prior Task 9 non-production-environment ceiling: protected integration, recoverable production backup and restore proof, governed additive migrations 1120–1123, exact-revision deployment, and authenticated live acceptance using one newly created disposable test chart with at most one bounded correction/recompute; preserve all safety, isolation, evidence and no-existing-chart-mutation constraints. |

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

## CCD-010 — Madhav product definition v3.0 adoption

- **Date/tool/session:** 2026-09-12; Codex; `MADHAV-PRODUCT-V3-20260912`.
- **Authority:** native directed a final, domain-rich, beyond-current-portal product pass, versioning, final registration, saving and commit. After the actual managed desktop profile failed the approved-profile validator, native explicitly answered **“Yes, authorized.”** to the one-time documentation-only exception. The exception is not retrospective success of the earlier blocked attempt.
- **Decision:** adopt [MADHAV_PRODUCT_DEFINITION_v3_0.md](MADHAV_PRODUCT_DEFINITION_v3_0.md), canonical ID `MADHAV_PRODUCT_DEFINITION`, as the final target product definition for this planning baseline. It directs subsequent planning, not present-capability certification. Future substantive revisions require an explicit successor/amendment. Existing data-plane and layer proposals require reconciliation; none is declared already aligned.
- **Narrow override:** the actual `tool_profile: managed` is permitted for this documentation-only session under SESSION_OPEN §3's explicit-native-override route. The unchanged validator's `handshake_codex_profile_invalid` failure is retained. Native also authorizes this exact non-lease documentation commit under GIP §P.4; no standing profile, tooling, protocol or commit-policy rewrite occurs.
- **Exact publication scope:** the final master; one review/adoption work-order record and validation evidence; seven directly relevant product antecedents with historical-status metadata only; CAPABILITY_MANIFEST admission and CCD fingerprint rotation; historical CANONICAL_ARTIFACTS audit pointer; CURRENT_STATE governance-aside pointer; and a validated SESSION_LOG entry. Original strategic-worktree changes are preserved. Independent review is read-only; the parent is the sole publication writer.
- **Prohibitions:** application code, data, migrations, provider/feature settings, credentials, frozen contracts, active campaign state, audience/research expansion, model activation, production rebuild/deploy, product-branch push, queue admission or merge. Existing consent posture and all safety/forecast firewalls remain unchanged. Documentation may later require the normal protected PR/deployment-authority path for shared integration.
- **Coordination:** documentation-only scope `MADHAV-PRODUCT-V3-20260912` on `origin/campaign-coordination`; claim remotely verified at `1f22b772bdb2856b603fd965265677a1704d9969`. Release proof belongs to the closing work-order/session record. No exclusive production lease was claimed.
- **Work order/evidence:** [review and adoption record](briefs/nirmana/MADHAV_PRODUCT_DEFINITION_V3_REVIEW_AND_ADOPTION_v1_0.md). Publication base `731e311f0b8f5f84db2f152b93951e1d3d50d89a`; source-audit baseline `0955849d1864a0f94cd746ab9706194831856a04`; no live/private-data or empirical certification.
- **Applicability at close:** this non-build documentation session does not serialize/upload production build-state. Record that N/A honestly, following the existing non-build-close precedent; do not create a production action to satisfy a generic close field. All applicable close validation, exact residual accounting and remote coordination release remain required.
- **Supersession:** product-level predecessor proposals only. Earlier CCD decisions, ratified architecture, campaign authorities/acceptance and output restrictions are not superseded. Native adoption and local registration/commit are distinct from protected-main integration.

## CCD-011 — MADHAV PŪRṆA ANVEṢAṆA source-campaign authority

- **Date/tool/session:** 2026-09-14; Codex; `MADHAV-PURNA-ANVESANA-W0-20260914`.
- **Authority:** direct native delegation titled `MADHAV PŪRṆA ANVEṢAṆA — SEMANTIC ESTATE COMPLETION AND INQUIRY INTELLIGENCE`, followed by the explicit instruction to set a goal and autonomously complete the entire supplied scope.
- **Decision:** establish a six-wave governed source campaign that freezes Foundation Candidate 0 at `codex/planner-knowledge-inquiry@fccfbb5ab11eadb33259ff987738068753d12ebc`, corrects and freezes reproducible denominators, decomposes work into independently reviewed packets, and may inspect, design, implement, test, document, commit, push and open focused or stacked PRs from isolated worktrees. PR #2597 remains unchanged and is the fixed stack base until separately advanced.
- **Exact ceiling:** no merge, deploy, shared or production migration application, production data/build/runtime mutation, traffic/scheduler action, credentials/secrets/infrastructure, asset retirement, doctrine ratification, frozen `WriterBase` or orchestrator-contract change, destructive cleanup, foreign campaign/worktree/ledger mutation, or claim of production/deployment/empirical acceptance from source, CI, PR, local or disposable evidence.
- **Disposable proof:** migration 1033, RLS/security/lifecycle/overlay/failure behavior and Portal/managed/raw MCP parity may be exercised only in isolated local or disposable environments created for this campaign. Such proof remains non-production evidence.
- **Coordination:** lease `MADHAV-PURNA-ANVESANA-20260914`, remotely verified at `origin/campaign-coordination@5c82e4813336b6454e3b63b485fefe47e84333b7`; Wave 0 worktree `/Users/Dev/.codex/worktrees/purna-anvesana-wave0`, branch `codex/purna-anvesana-wave0` based exactly on FC0.
- **Governance reconciliation:** for this campaign only, the native’s explicit source/commit/push/PR authority supersedes GIP §P.4’s generic lease-row-only commit restriction. It does not supersede §P.1–§P.3, any safety/evidence gate, or the ceiling above.
- **Supersession:** none. Existing Nirmāṇa production-elevation campaign state, database definitions/events, layer state files and historical autonomous authority remain separate and untouched.

## CCD-012 — MADHAV PŪRṆA ANVEṢAṆA live-release and complete-wrap-up authority

- **Date/tool/session:** 2026-09-15; Codex; `MADHAV-PURNA-ANVESANA-LIVE-WRAPUP-20260915`.
- **Authority:** direct native delegation delivered from the active Madhav product-strategy task to
  the existing Planner Knowledge and Inquiry task, followed by the native's instruction to set a
  goal, resume autonomously, and complete the entire supplied scope. The delegation explicitly
  authorizes protected integration and deployment; necessary reviewed additive/shared migrations;
  narrowly scoped signing-key and runtime configuration; real Portal, managed MCP and raw MCP
  validation; empirical evaluation; safe compatibility retirement; and true campaign closure.
- **Decision:** supersede CCD-011's `SOURCE_LOCAL_ACCEPTED` terminal ceiling for this campaign and
  execute the governed live wrap-up from current protected `origin/main` plus immutable Wave 7 head
  `facccfe4b518b997357c08ff7798b703459326df`. Build one aggregate candidate, preserve the original
  Wave 0–7 history and negative evidence, close PA-R01 through PA-R13 at the strongest applicable
  gate, and advance only on exact-candidate evidence. A source, PR, CI, staging, timestamp or
  dashboard result is never substituted for protected delivery, production health, expert review or
  empirical acceptance.
- **Delivery authority:** Codex may create, test, review, commit and push the aggregate branch; open
  or update a focused pull request; admit it through the repository's existing protected merge queue
  only after every required check and independent review is green; execute the existing governed
  canary/deployment path; apply only reviewed additive migrations through the established runner;
  provision or rotate only the dedicated inquiry signing ring without revealing key material; and
  make only the service configuration changes required by the reviewed inquiry runtime contract.
- **Safety and serialization:** production or shared mutation requires a fresh operation-specific
  exclusive coordination lease, a current protected/source/deployed revision check, a recoverable
  backup or rollback reference where applicable, no-traffic or revision-pinned canary verification,
  and post-step evidence. The active Data Plane RI-02 lease retains ownership of L0–L3 and migrations
  1035/1036 until released or expired; this campaign must not overlap its shared migration, key,
  traffic or rebuild operations. Applied migrations are immutable; any correction is a new
  collision-free forward migration.
- **Empirical authority and truth boundary:** the campaign may execute the frozen empirical protocol
  only with an eligible held-out corpus, valid consent/privacy custody, the required independent
  domain experts, conflict attestations and blinded receipts already available within approved
  channels. It may not invent participants, consent, data, scores, approval or signatures, and may
  not contact or recruit people without a separate instruction. Missing expert or corpus evidence is
  `NOT_RUN`, never a pass.
- **Prohibitions:** no administrator/ruleset/required-check bypass; no secret or sensitive-chart
  disclosure; no destructive shared rebuild; no broad IAM, infrastructure or model-budget expansion;
  no frozen WriterBase/orchestrator or Data Plane architecture takeover; no unrelated doctrine or
  campaign mutation; no external contact; and no `FULLY_COMPLETE` claim until every applicable gate
  has an accepted receipt.
- **Coordination:** live-wrap-up lease
  `MADHAV-PURNA-ANVESANA-LIVE-WRAPUP-20260915` was remotely verified at
  `origin/campaign-coordination@bc6699a1c6e1bcf46bc037d31583157a318b04a8`; initial status is
  source integration and stocktake only. Shared or production operations require a later fresh,
  operation-specific exclusive claim.
- **Execution record:**
  `briefs/nirmana/purna_anvesana/LIVE_RELEASE_AND_COMPLETE_WRAPUP_PLAN_v1_0.md` and
  `briefs/nirmana/purna_anvesana/LIVE_COMPLETION_MATRIX_v1.json` are the frozen plan and gap matrix.
- **Supersession:** CCD-011 is superseded only where its explicit external-action ceiling conflicts
  with this scoped live-release delegation. Its evidence discipline, source history, security
  boundaries and all unrelated decisions remain in force.

## CCD-013 — Jātaka chart-workspace parallel local-execution authority

- **Date/tool/session:** 2026-09-27; Codex governance bridge handing execution to Claude Code;
  `JATAKA-CHART-WORKSPACE-GOVERNANCE-20260927`.
- **Authority:** the native explicitly approved the recommended narrow governance amendment,
  migration-number correction and corrected implementation plan after Claude Code stopped at the
  active L3 scope, migration partition and safe-local-environment gates.
- **Decision:** permit local source implementation, tests and commits for Tasks 1–8 of
  `platform/docs/superpowers/plans/2026-09-27-jataka-chart-workspace.md` only in worktree
  `/Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav` on branch
  `codex/jataka-chart-workspace`, subject to the exact allowlist and stop conditions in
  `briefs/jataka/JATAKA_CHART_WORKSPACE_PARALLEL_EXECUTION_AMENDMENT_v1_0.md`.
- **Migration:** reserve `1120_jataka_conversation_archive_context.sql` through
  `JATAKA-REQ-01` on authoritative `origin/campaign-coordination`, after a fresh protected-main and
  complete open-PR migration sweep found no `1120+` claimant. Recheck immediately before creating
  the file; the coordination record, not the numeric guard alone, governs the partition.
- **Environment boundary:** Task 9 and browser/full-recompute acceptance remain blocked until a
  non-production Firebase Admin credential, workstream-owned disposable local PostgreSQL database,
  and approved L0 seed/snapshot are available. Do not copy the shared `.env.local`, use production,
  reuse another session's database, or add a Firebase emulator path without a successor decision.
- **Ceiling:** no push, PR, merge, deployment, production/shared migration application, database or
  chart mutation, real-user edit, credential/secret/IAM/infrastructure action, frozen orchestrator
  change, or foreign campaign/worktree/state mutation. Tasks 1–8 evidence cannot be represented as
  completed local-browser acceptance.
- **Coordination:** governance lease
  `MADHAV-JATAKA-CHART-WORKSPACE-GOVERNANCE-20260927`; migration request `JATAKA-REQ-01`;
  reservation commit `ed5f52294` on `origin/campaign-coordination`.
- **Supersession:** none. L3 Kāla, Pūrṇa Anveṣaṇa and all prior CCD decisions remain in force.

## CCD-014 — Jātaka Phase-A integrity-hardening follow-up

- **Date/tool/session:** 2026-09-27; Claude Code; `JATAKA-PHASE-A-HARDENING-20260927`.
- **Authority:** the native accepted the Tasks 1–8 result as "implemented and mock-tested locally;
  Task 9 and full browser/recompute acceptance remain blocked" and explicitly authorized a narrow
  Phase-A integrity-hardening follow-up in the same worktree and branch.
- **Decision:** permit local source changes, tests and local commits for the five hardening items
  and the exact file scope in
  `briefs/jataka/JATAKA_CHART_WORKSPACE_PHASE_A_HARDENING_ADDENDUM_v1_0.md`. Chart-context staleness
  proceeds only if every current-query consumer is enforceable inside that scope; otherwise the
  session stops on that item and reports the exact excluded dependency.
- **Migration:** reserve `1121_jataka_correction_archive_write_guard.sql` through `JATAKA-REQ-02`
  (coordination commit `3bd118621`) after a fresh `origin/main` and complete open-PR sweep.
  Authored only; never applied under this authority.
- **Ceiling:** unchanged from CCD-013 — no Task 9, browser acceptance, push, PR, merge, deploy,
  migration application, database access, credential/infrastructure action, `python-sidecar/**`
  or frozen-contract change, or L3 Kāla / Pūrṇa mutation.
- **Coordination:** lease `MADHAV-JATAKA-PHASE-A-HARDENING-20260927` on `origin/campaign-coordination`.
- **Supersession:** none. Extends CCD-013; the parent Jātaka amendment is unchanged.

## CCD-015 — Jātaka Phase-A2 integrity session

- **Date/tool/session:** 2026-09-27; Claude Code; `JATAKA-PHASE-A2-INTEGRITY-20260927`.
- **Authority:** the native accepted the Phase-A hardening report at `695401d31` ("Items 1, 3, 4
  and 5 are implemented and mock-tested. Item 2 and two reading doors remain open. Task 9 remains
  blocked.") and authorized a new, narrowly governed Phase-A2 integrity session.
- **Decision:** permit local source changes, tests and local commits for the work and exact file
  scope in `briefs/jataka/JATAKA_CHART_WORKSPACE_PHASE_A2_INTEGRITY_ADDENDUM_v1_0.md`: chart-context
  staleness marked in the correction transaction and enforced at every identified current-query
  consumer (named sidecar, retrieval and Pūrṇa files only — not blanket authority over those
  trees); the MCP `prashna_ask` and super-admin `chat/build` reading doors; terminal-event,
  persistence-result, retry, stale-readiness and serving-impact correctness; the migration 1121
  security disposition. A consumer that needs a frozen or actively leased contract is reported,
  and item 2 is then not claimed complete.
- **Migration:** reserve `1122_jataka_chart_context_staleness.sql` through `JATAKA-REQ-03` after a
  fresh `origin/main` (`6b26f3ff0`, max 1079) and complete open-PR sweep (21 PRs, 22 migration files,
  max 1090). Authored only; never applied under this authority. 1121 stays unapplied.
- **Ceiling:** no Task 9, browser acceptance, migration application, database or external-service
  access, credentials, push, PR, merge, deploy, production data or real-user mutation; frozen
  `WriterBase`, runner/`asset_runner` transaction contracts, governed `asset_registry` definitions,
  unrelated writers and L3 Kāla implementation stay excluded.
- **Coordination:** lease `MADHAV-JATAKA-PHASE-A2-INTEGRITY-20260927` on `origin/campaign-coordination`.
- **Supersession:** none. Extends CCD-013 and CCD-014; the parent amendment and the Phase-A
  addendum are unchanged.

## CCD-016 — Jātaka Phase-A3 source-integrity pass and evidence refreshes

- **Date/tool/session:** 2026-09-27; Claude Code; `JATAKA-PHASE-A3-SOURCE-INTEGRITY-20260927`.
- **Authority:** the native accepted the Phase-A2 report at `7673c96b8` as source-local, mock-tested
  evidence with four explicitly understood governance-artifact failures, and authorized a Phase-A3
  source-integrity pass followed by two separately governed source-evidence refreshes at one exact
  reviewed technical head.
- **Decision:** permit local source changes, tests and local commits for the work and exact file scope
  in `briefs/jataka/JATAKA_CHART_WORKSPACE_PHASE_A3_SOURCE_INTEGRITY_ADDENDUM_v1_0.md`: chart-context
  staleness for the three deferred surfaces and their identified current-query consumers (named files
  only — not blanket sidecar/MCP/retrieval/Pūrṇa/Nirmāṇa authority); establishing one reviewed
  technical head with an independent fresh-context review; then, ONLY after that head is approved and
  ONLY under their own narrow decision records, a Nirmāṇa L5 successor re-pin (source-provenance only)
  and a Pūrṇa Beyond-Ācārya v7 successor (v6 preserved immutable, source-local only, does not reopen or
  close the Pūrṇa campaign).
- **Migration:** reserve `1123_jataka_context_staleness_deferred_surfaces.sql` through `JATAKA-REQ-04`
  after a fresh `origin/main` (`6b26f3ff0`, max 1079) and complete open-PR sweep (21 PRs, max 1090).
  Authored only; never applied under this authority. 1120, 1121 and 1122 stay unapplied.
- **Ceiling:** no Task 9, browser acceptance, migration application, database or external-service
  access, credentials, push, PR, merge, deploy, production data, real-user mutation, or chart rebuild;
  no empirical/production acceptance claim; the Nirmāṇa re-pin is source-provenance only, never data/
  value acceptance; the Pūrṇa v7 successor never reopens/closes that campaign.
- **Coordination:** lease `MADHAV-JATAKA-PHASE-A3-SOURCE-INTEGRITY-20260927` on
  `origin/campaign-coordination`.
- **Supersession:** none. Extends CCD-013/014/015; the parent amendment and the Phase-A/Phase-A2
  addenda are unchanged.

## CCD-017 — Nirmāṇa L0/L5 receipt-checker coupling fix

- **Date/tool/session:** 2026-09-27; Claude Code; `NIRMANA-L0-L5-COUPLING-FIX-20260927`.
- **Authority:** native message starting from branch `codex/jataka-chart-workspace` at
  `a97fc8ffb0268954fb4bf8c7fb7e838c4bf6e558` (Phase-A3 closed, not reopened; lease released and
  remotely verified at `89cda9092`; migration 1123 unapplied; Beyond-Ācārya v7 complete, not
  revisited; Task 9 blocked), authorizing a separately governed follow-up for the two remaining
  `nirmana-analysis-receipts.test.ts` failures caused by `L0_FROZEN_PINS`.
- **Decision:** permit local source changes, tests and local commits for the work and exact file
  scope in `briefs/nirmana/NIRMANA_L0_L5_RECEIPT_COUPLING_FIX_ADDENDUM_v1_0.md`: diagnosis and
  correction of the cross-layer coupling that lets a legitimate L5 successor trigger an L0
  comparison/regeneration path; focused regression tests; necessary narrow generated-code or
  governance updates. `L0_FROZEN_PINS` stays byte-for-byte unchanged unless evidence proves the
  constant itself is incorrectly constructed; every historical L0 generation and binding is
  preserved; genuine L0 or unreviewed-L5 drift must still fail closed.
- **Migration:** none anticipated; if the investigation proves one necessary, this session stops
  and reports rather than reserving one under this authority.
- **Ceiling:** no L0 accepted-membership/hash/generation/receipt/evidence change; no further L5
  re-pin unless the fix genuinely changes L5 source identity; no weakening/deleting the failing
  assertions; no hand-edited generated JSON; no database access, migrations, rebuilds,
  credentials, push, PR, merge, deployment, or production work; no Task 9. If the true fix
  requires changing ratified L0 evidence rather than correcting cross-layer validation, this
  session stops and reports without proceeding.
- **Coordination:** lease `MADHAV-NIRMANA-L0-L5-COUPLING-FIX-20260927` on
  `origin/campaign-coordination`.
- **Supersession:** none. Phase-A3 (CCD-016) and its close remain unchanged and are not reopened.

## CCD-018 — Jātaka controlled production rollout authority

- **Date/tool/session:** 2026-09-27; Codex; `JATAKA-CONTROLLED-PROD-ROLLOUT-20260927`.
- **Authority:** direct native instruction in the continuing Jātaka conversation: use a
  controlled production rollout instead of creating a separate non-production Firebase and
  database environment. This is a deployment and bounded live-verification authorization, not a
  general production or infrastructure mandate.
- **Decision:** permit the reviewed Jātaka chart-workspace candidate on branch
  `codex/jataka-chart-workspace` to proceed through fresh source review, full required checks,
  push, focused pull request, required independent review and repository-protected integration;
  then through the established production deployment path at one exact accepted revision. Apply
  additive migrations `1120`–`1123` only through the governed migration runner and only after a
  current migration-collision sweep plus a fresh recoverable production backup and restore/rollback
  proof. Run authenticated production acceptance with one newly created and clearly named
  disposable test chart, including at most one bounded birth-detail correction and recompute.
- **Evidence gate:** before release, record the exact protected-main candidate, migration inventory,
  full verification results, backup identifier, restore/rollback proof and deployment mechanism.
  After release, verify service health, deployed revision, migration state, authorization boundaries,
  the dashboard-to-workspace flow, name-only edit behavior, correction confirmation, exactly one
  same-chart recompute, historical-conversation read-only behavior, readiness-gated actions,
  keyboard/responsive behavior and relevant production logs/database receipts. Local, CI or visible
  UI evidence alone does not establish production acceptance.
- **Safety and rollback:** never edit or rebuild an existing important production chart. Do not
  expose, copy, rotate or persist credentials; do not broaden IAM, networking, database or Firebase
  configuration. Stop on any backup/restore, migration, authorization, deploy-health, data-isolation
  or acceptance failure. Application rollback uses the last healthy revision or a reviewed revert;
  the additive migrations may remain only if backward-compatible and independently healthy. Keep
  the disposable chart isolated and retain or delete it only according to an explicitly recorded,
  recoverable disposition.
- **Coordination:** exclusive production lease
  `MADHAV-JATAKA-CONTROLLED-PROD-ROLLOUT-20260927`, remotely verified at
  `origin/campaign-coordination@0812b50f1444127c5057d535b984f3889b68c05c` before any
  production change.
- **Prohibitions:** no administrator/ruleset/required-check bypass; no existing-user chart mutation;
  no broad rebuild; no destructive schema/data operation; no unrelated database repair; no secret,
  IAM or infrastructure change; no frozen orchestrator or L3 campaign mutation; no claim of
  success without exact-revision live evidence.
- **Supersession:** supersedes CCD-013 through CCD-017 only where they prohibit Task 9, production
  access, push, PR, protected merge, governed migration application and deployment for this exact
  rollout. Their source-integrity conclusions, file boundaries, migration identities, historical
  evidence, safety constraints and all unrelated ceilings remain in force.

## CCD-019 — Jātaka protected migration schema-capability exception

- **Date/tool/session:** 2026-09-28; Codex; `JATAKA-CONTROLLED-PROD-ROLLOUT-20260927`.
- **Authority:** direct native authorization after the protected deploy stopped before service
  mutation because the ordinary `amjis_app` migration login had `USAGE` but not `CREATE` on the
  protected `public` schema. This entry registers the exact exception already recorded and closed
  in the controlled-rollout addendum.
- **Decision:** permit one reviewed, protected workflow to grant `CREATE ON SCHEMA public` to
  `amjis_app` only while applying migrations 1120–1123, revoke it on every exit path, and attest
  the closed privilege state before service deployment. The completed run applied the four
  migrations and confirmed `amjis_app` retained `USAGE=true`, `CREATE=false`.
- **Ceiling:** no permanent grant, role membership, credential/IAM change, direct SQL application,
  emergency override, different migration, unrelated database mutation or reuse of the exception.
- **Supersession:** none. The exception is exhausted and closed.

## CCD-020 — Jātaka shared-prerequisite repair and blocked-acceptance completion

- **Date/tool/session:** 2026-09-28; Codex; `JATAKA-SHARED-PREREQUISITE-REPAIR-20260928`.
- **Authority:** direct native instruction in the continuing Jātaka conversation to execute the
  separately authorized controlled production repair after the rollout's recomputation blocker was
  explained. This is a bounded repair-and-acceptance authority, not a broad data-plane mandate.
- **Corrected diagnosis gate:** read-only production evidence must distinguish a current writer
  failure from stale operational metadata and freshness receipts. Rule 133 and every cited
  `gochara_resonance_map` row must be preserved. The historical FK error may not be treated as a
  current failure without reproduction against the deployed writer.
- **Decision:** permit the smallest tested planner/readiness correction required for healthy
  service prerequisites; a focused protected PR and exact-revision deploy if source changes are
  necessary; a fresh recoverable production backup; explicit governed probe/rebuild operations only
  for the prerequisite identities proven to block the disposable chart; and one rerun of only the
  previously blocked correction/context-transition acceptance on synthetic chart
  `a0fa7e08-c758-4167-846b-b38054e5f768`.
- **Evidence gate:** prove the exact blockers, preserve referenced transit-rule identities, pass
  focused and full required tests plus independent review, verify backup and rollback readiness,
  deploy only through repository protection, confirm each repaired prerequisite is ready from live
  state/receipts, then prove exactly one same-chart recomputation and the remaining Task 9 context
  transition without cross-chart mutation.
- **Safety and rollback:** no direct production patch; no deletion, remap or ID churn for rule 133;
  no broad shared rebuild; no existing important chart edit/rebuild; no secret, IAM, network,
  Firebase, topology or frozen-orchestrator change. Stop on any unexpected candidate, row-count,
  identity, citation, service-health, deployment, isolation or acceptance difference. Application
  rollback uses the last healthy revision; shared-data rollback uses the fresh backup or a separately
  reviewed forward repair, never destructive ad-hoc SQL.
- **Coordination:** exclusive lease `MADHAV-JATAKA-BG-TRANSIT-REPAIR-20260928` on
  `origin/campaign-coordination`, claimed and remotely verified at
  `fad1e8fbd4e150a65c936626105ecd84893a1464`.
- **Supersession:** extends CCD-018 only for the separately authorized prerequisite repair and the
  acceptance items it left blocked. All other CCD-018 ceilings remain in force.


## CCD-021 — Reviewed Journey 1 deployment authority

- **Date/tool/session:** 2026-10-05; Codex; `MADHAV_JOURNEY1_RELEASE_20261005`.
- **Authority:** direct owner instruction in this portal-review task: “Go ahead and deploy it.” Given after the local implementation outcome, remaining checks and deployment distinction were disclosed.
- **Scope:** reviewed Journey1 pages03–09 and supporting username setup; necessary bounded release fixes/tests; source commits/push and focused PR; current protected merge queue/quality gates; existing zero-traffic web candidate/smoke/promotion process; live verification and rollback if the release fails. Journey2 is deferred.
- **Narrow reconciliation:** this explicit release authority supersedes GIP §P.4's lease-row-only publication ceiling only for this Journey1 delivery. No standing policy or quality/evidence gate is changed.
- **Coordination:** fresh operation-specific lease `L-PORTAL-JOURNEY1-RELEASE-20261005`, remotely verified at `a8bfa62111437164d062e078d412df5295665510`. Owned worktree `/Users/Dev/.codex/worktrees/portal-experience/Madhav`; primary/foreign worktrees remain untouched.
- **Boundaries:** no new migration/schema, chart rebuild, paid provider call, credentials, production account/permission mutation, infrastructure change, unrelated campaign takeover or independent-review claim. Real create/reset/approval workflows are not exercised by mutating production records.
- **Evidence:** `briefs/journey1/release/RELEASE.md`; baseline rollback web revision `amjis-web-probe-944ccf22c250-37310776256-1`; source/live acceptance must be separately verified.


## CCD-022 — Reviewed Consultation 10 deployment authority

- **Date/tool/session:** 2026-10-06 IST; Codex; `MADHAV_CONSULTATION10_RELEASE_20261006`.
- **Authority:** direct owner instruction in this portal-review task: “Please go ahead and deploy this.” after the local consultation implementation, test outcome and pending application database update were disclosed.
- **Scope:** reviewed consultation Paripraśna runtime and scoped integration/tests; source commit/push, focused PR and protected merge/CI; existing zero-traffic web candidate/smoke/promotion; additive migration `1307_consultation_tags.sql` through the established routine runner, verification and rollback. Necessary release reconciliation preserves current main and foreign work.
- **Narrow reconciliation:** this explicit release authority supersedes GIP §P.4's lease-row-only publication ceiling only for this consultation release. No standing policy, protection, required-check or evidence gate is changed. Earlier Journey1 release is not reopened.
- **Coordination:** lease `L-PORTAL-CONSULTATION10-RELEASE-20261006`, remotely verified at `1b24b2327d04c7bcc2339fba19db114704924790`. Owned worktree `/Users/Dev/.codex/worktrees/portal-experience/Madhav`; separate Journey3 source work may proceed, with exclusive web-release windows rechecked before merge/deploy.
- **Boundaries:** no engine/asset rebuild, unrelated schema or data repair, paid AI call, real chart/account/permission mutation, secret/IAM/infrastructure change, direct production patch, emergency CI bypass or foreign worktree edit. Existing owned history and UI preferences may be read/checked without generating new readings or share links.
- **Evidence:** `briefs/consultation10/release/RELEASE.md`; baseline web revision `amjis-web-probe-091362f315a2-37346348777-1` at100% desired and observed traffic. Numbering/SQL application, exact deployed revision and authenticated UI/API acceptance must be verified separately; pre-existing consultation HTTP400 engine residual is outside this UI release.

## CCD-023 — Reviewed Journey 3 implementation and deployment authority

- **Date/tool/session:** 2026-10-06; Codex; `MADHAV_JOURNEY3_20261006`. CCD-022 is reserved by the preceding Consultation review10 release on its governed branch.
- **Authority:** direct owner instruction, “Please go ahead and implement and deploy us,” after Journey3 / page14 Chart Preparation was inspected.
- **Scope:** six expandable preparation layers, live registry/status/counts, existing guarded build/refresh/clear controls, truthful readiness, responsive reviewed shared shell, tests and scoped evidence. Source commit/push, focused PR, protected integration and the established web candidate/smoke/promotion/live-verification process are authorized.
- **Narrow reconciliation:** supersedes GIP §P.4's lease-only source-publication ceiling for this delivery only. No standing policy, required check or deployment gate is changed.
- **Coordination:** `L-PORTAL-JOURNEY3-20261006`, remotely verified at `654cd93fba94702353bfe7ee169fa6294cbc58a0`; own worktree `/Users/Dev/.codex/worktrees/journey-three/Madhav`. Source work proceeds independently; merge/deployment waits for the preceding Consultation release window to close and is checked again immediately before integration.
- **Boundaries:** no migration/schema, engine/writer/orchestrator change, chart rebuild or data-clear execution, paid-provider call, account/permission/credential or infrastructure change, foreign-worktree mutation or other journey implementation. Preview/confirmation tests use fictional fixtures. Production acceptance is read-only.
- **Evidence and rollback:** `00_ARCHITECTURE/briefs/journey3/RELEASE.md`. Record fresh accepted main, serving revision/traffic and prior healthy rollback revision at release; a green CI result alone does not establish deployed acceptance.

## CCD-024 — Journey 5 design, implementation and deployment authority

- **Date/tool/session:** 2026-10-06; Codex; `MADHAV_JOURNEY5_DELIVERY_20261006`.
- **Authority:** direct owner instruction in this chat: build a plan for each block, get designs done using Claude Design, update the Review Hub/campaign, implement designs with backend support, and deploy.
- **Scope:** Journey5 pages18–24, compact My Account and AI Cockpit containers, Profile/Security/Preferences, Console/Personas/My Observatory/Consumption, their shared saved-setting and own-user metering consumers, necessary additive migrations and tests. Revise the existing Claude Design project; preserve earlier designs and unrelated journeys.
- **Publication/release:** scoped source commits/push, focused PRs, protected merge queue/required checks, governed additive migration application and existing candidate/smoke/promotion deployment. Before release claim an exclusive production lease, pin the accepted candidate, verify backup/rollback and actual migration application. Verify exact revision, traffic and authenticated screens after release.
- **Supersession:** GIP §P.4's lease-row-only publication ceiling is superseded only for this delivery. The earlier Journey5 analysis-only lease is closed; this is new explicit execution authority. No standing project policy changes.
- **Boundaries:** no unrelated engine/campaign takeover, chart rebuild, paid AI qualification, real user's credential or permission mutation, expanded IAM/network/Firebase privileges, destructive migration or naming/doctrine ratification. Provisional Sanskrit names remain marked as such. Security acceptance uses synthetic/local tests; actual password entry through UI remains human-owned.
- **Worktree/coordination:** `/Users/Dev/.codex/worktrees/journey-five/Madhav`, `codex/journey-five-delivery`; lease `L-PORTAL-JOURNEY5-DELIVERY-20261006` remotely verified at `d9f8a225650a903a5fbf4ab2c91891d7d498fe91`.
- **Work order:** `00_ARCHITECTURE/briefs/journey5/DELIVERY_PLAN.md`. Designs, implemented behavior, verified runtime and owner acceptance are tracked separately.


## CCD-025 — Journey 6 accepted-plan design, implementation and deployment authority

- **Date/tool/session:** 2026-10-06; Codex; `MADHAV_JOURNEY6_DELIVERY_20261006`.
- **Authority:** owner requested Journey6 reconciliation against built Journey5 and accepted the resulting final plan with “Please go ahead and do that.” The preceding plan explicitly proposed Claude Design, Review Hub updates, scoped frontend/backend, independent review, deployment and live verification.
- **Scope:** accepted `briefs/journey6/PLAN.md` (SHA256 `2d7e73a6b488ab18d4eb3298bfb2ef7deeae280994e7f445b4c12472f50f6547`): all15 Journey6 pages consolidated into overview/four blocks, canonical permission/accounting/configuration reuse, operational read adapters, accurate availability and evidence states. Revise only Journey6 operator designs and current Hub; preserve Journey5 personal configuration/activity and other journeys. Learning Review initially read-only.
- **Publication/release:** scoped source/evidence commits and push, focused PR, protected integration and required checks, necessary reviewed additive migrations, existing candidate/smoke/promotion and authenticated live verification. Claim an exclusive production lease and verify current predecessor/backup/migration receipts before release.
- **Narrow reconciliation:** this scoped explicit authority supersedes GIP §P.4's generic lease-row-only publication ceiling for this Journey6 delivery. No policy, role, required check or deployment protection is changed. It is independent of Journey5-only CCD-024.
- **Boundaries:** no real-user permission or credential mutation, paid AI qualification, broadened IAM/network privileges, chart/asset rebuild, engine/campaign takeover, tool-taxonomy/doctrine ratification or independent co-sign protocol invention. Preserve existing action permission boundaries and exact personal defaults. Do not activate unproven learning publication controls.
- **Worktree/coordination:** `/Users/Dev/.codex/worktrees/journey-six-delivery/Madhav`, branch `codex/journey-six-delivery`; source lease `L-PORTAL-JOURNEY6-DELIVERY-20261006` remotely verified.
- **Work order:** `00_ARCHITECTURE/briefs/journey6/DELIVERY_PLAN.md`. Designed, owner-reviewed, implemented, tested, deployed and live-verified remain separate evidence states.
