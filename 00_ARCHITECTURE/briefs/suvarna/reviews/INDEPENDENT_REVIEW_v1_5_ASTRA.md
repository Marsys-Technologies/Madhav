# INDEPENDENT_REVIEW_v1_5_ASTRA.md

## Verdict

**DO NOT APPROVE**

The proposed design does not yet make unattended authority trustworthy. Strategic Suvarṇa can change policy, release the enforcing code and record approvals while running as the owner’s account. The swarm retains a credential capable of bypassing the local merge gate. Launch evidence can be fabricated without performing its claimed drill. The setup script also contains concrete permission and verification defects. These are shortcomings in the proposed controls as well as gaps in implementation; implementing CODE-36–65 exactly as written would not close all of them. N-28 can be preserved by separating AI decisions from deterministic enforcement without restoring routine owner review. Sources: Charter §§2, 12–13; Architecture §§2.4, 5.5; Disposition §5, CODE-36, 43, 47, 60; `T/runtime/native_setup.sh::ns4_apply`, `ns4_do_move_decisions`, `run_verify_mode`.

### Scope, references and verification

This report assesses the bundled pre-final v1.5 set under review-package version **2.3**. It does not approve a deployment or confirm live infrastructure. The package explicitly distinguishes implemented code from specifications and says native setup has not been performed. Sources: Package frontmatter, §§2, 6a–7.

Paths are relative to the bundle root:

- `S/` = `00_ARCHITECTURE/briefs/suvarna/`
- `T/` = `platform/scripts/governance/suvarna_tracker/`

| Reference | File |
|---|---|
| Package | `S/SUVARNA_REVIEW_PACKAGE_v1_0.md` |
| Plan | `S/SUVARNA_CAMPAIGN_PLAN_v1_5.md` |
| Charter | `S/SUVARNA_AUTONOMY_CHARTER_v1_0.md` |
| Architecture | `S/SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md` |
| Setup | `S/NATIVE_SETUP_v1_0.md` |
| Disposition | `S/reviews/INDEPENDENT_REVIEW_ASTRA_DISPOSITION_v1_0.md` |
| Previous review | `S/reviews/INDEPENDENT_REVIEW_GPT6_ASTRA_v1_0.md` |
| Track E / Track A | `S/tracks/TRACK_E_BRIEF_v1_0.md` / `TRACK_A_BRIEF_v1_0.md` |
| Runbook / Runtime | `S/SUVARNA_RUNBOOK_v1_0.md` / `runtime/INTERIM_RUNTIME_v1_0.md` |
| Families | `S/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` |
| Model | `00_ARCHITECTURE/control/suvarna/plan_model.json` |
| Register | `00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md` |

No files were created, modified or deleted. No network, database, credential or other reviewer’s report was accessed. Verification consisted of manifest hashing, Python AST parsing, model and register analysis, and in-memory counterexamples with filesystem/network operations replaced by mocks. The full pytest suite was **not run**, because its fixtures write files; the package’s reported test results are not independently reproduced here. Sources: `MANIFEST.txt`; `T/tests/test_native_setup.py`; `T/tests/test_detectors_v15.py`; Package §§6–6a.

## Findings

| # | Severity | Where | Finding, with evidence | Recommended fix |
|---|---|---|---|---|
| F1 | **BLOCKER** | Charter §§2, 12–13; Architecture §§2.4, 5.5; Disposition CODE-36, 60 | **The decision-maker controls its own enforcement boundary.** SS writes amendments and control releases, records decisions and runs unattended as `Dev`. Independent review is required in prose, but no specified mechanism binds an authorized independent reviewer’s acceptance to the exact amendment and enforcing release. SS also shares the identity allowed to clear native holds. | Run SS without owner credentials. Keep policy activation, action authorization and native-veto clearing in a separate deterministic service. Bind required reviews to exact policy, code and evidence hashes; SS must not be able to manufacture the independent acceptance. |
| F2 | **BLOCKER** | `T/gates.py::evaluate_decision_gate`; `T/state.py::build_snapshot`; `T/detectors.py::d_evidence_verified`; Model decision items and LG.*; Disposition CODE-36, 47 | **Approval and drill evidence can become unearned permission.** An in-memory record with `state: decided`, detail `DO NOT APPROVE` and a corrupt-log count returned `done`. None of the Model’s 41 decision items has a revision pin. Fabricated `{"result":"PASS","cases":null}` passed `evidence_verified` with `cases` required and an empty commit pin. CODE-47 would still trust a claimant-written PASS even after fixing null checks. | Require typed outcomes, mandatory revision binding, authenticated writers, valid prerequisite snapshots and corruption refusal. Generate drill results through trusted execution, with raw results and configuration identity protected from the claimant. Empty required pins must block. |
| F3 | **BLOCKER** | Charter G11, R7, §13; Plan §6.4; Model L.16b; Disposition CODE-40, 43 | **The merge gate is a convention, not an exclusive enforcement point.** The swarm can read its repository Write token. The specified server rules require checks and a queue, but do not require the local ACCEPT/hold decision. A direct API merge can bypass that wrapper. The path guard’s own implementation and policy inputs also need protection. Model L.16b pins only the new path-guard context, not the four existing required checks. | Remove merge authority from worker-readable credentials or require a protected, independently issued server-side authorization check. Bind authorization to the exact merge candidate and recheck holds at execution. Protect the guard, its dependencies and ownership maps; verify all required checks and merge-queue behavior. |
| F4 | **BLOCKER** | Setup Steps 2–5, Appendix NS.2–NS.8; `T/runtime/native_setup.sh::ns3_find_readable_secrets`, `ns4_do_folders`, `ns4_do_move_decisions`, `p_ns4_holds_ready`, `run_verify_mode`; `T/tests/test_native_setup.py` | **Native setup can report progress while leaving authority writable or verification incomplete.** NS.4 grants swarm ownership/ACLs to `run/`, then moves the decisions log into `authority/` without resetting its owner/ACL. Checks inspect directory owners but not effective write access to that log or its ancestry. NS.3 scans world-readable permission bits, not effective group/ACL access. `--verify` omits NS.5–NS.7 and emits lowercase subcheck keys rather than the Model’s `NS.1`…`NS.9`. Failed verification returns success. | Correct migration order and ownership/ACL normalization; test effective access as each identity, including parent replacement and symlinks. Pin the native home. Implement one complete verification schema with nonzero failure exit status. Prove it on real macOS before use. |
| F5 | **BLOCKER** | Charter §§6, 8; Plan §6.4b; `T/hold_guard.py`; `T/hold_guard.sh`; Disposition CODE-39, 43, 53 | **Holds and dispatch checks are incomplete, and recovery conflicts with holding.** Current hook enforcement classifies command text; its fallback needs the same potentially missing interpreter. The proposed broker checks hold, scope and image, but does not explicitly enforce every Charter §6 precondition. “Hold, then revert/rebuild” conflicts with unconditional refusal of merges/builds while held. Owner and SS share the identity for native clears. | Enforce the complete action contract at the sole credential-bearing boundary. Authenticate native veto clearance separately. Define a narrowly scoped recovery authorization that can execute the recorded reversal while ordinary work stays held. Test corrupt ledgers, indirect dispatch and already-queued actions. |
| F6 | **BLOCKER** | `T/conductor_lock.py::acquire`, `_write_lock`, `update_pid`; `T/monitor.py::check_conductor_heartbeat`, `apply_stage`; `T/detectors.py::d_monitor_check_ok`; Disposition CODE-41–42, 63 | **Runtime exclusivity and readiness are not proven.** Lock acquisition is read-then-replace, not atomic exclusion; an in-memory simultaneous interleaving let two callers acquire the same session. A never-started Conductor can read healthy. Launch-stage normalization turns an unprovisioned builder into `ok`, which an unqualified `monitor_check_ok` can consume. Proposed fencing covers queue commits but needs to cover external effects too. | Use atomic locking and generation-based fencing for every dispatch. Distinguish healthy, absent and not-applicable. Bind checks to an explicit required stage. Test simultaneous starts, crash points, stale holders, restart and external-action reconciliation. |
| F7 | **MAJOR — before production-visible changes** | Plan §§6.4b–c; Charter §6(8); Track E E5.8–E5.9; `S/l3_recon/KSHETRA_RECON.md` §§1.4–1.5 | **Serving protection does not yet cover the complete affected output.** The guard is framed around served tables written by the action and canonical-chart MCP canaries. Cascades, indirect consumers, other charts, caches and already-derived downstream rows can be affected without being direct writes. The inventory and implemented authority mechanisms are absent. | Define the transitive serving footprint, per chart and generation. Enforce the guard in serving infrastructure, including process-loss behavior. Maintenance must produce an unmistakably qualified or unavailable response, and remain active until the entire affected footprint is valid. |
| F8 | **MAJOR — before R3 or global L0 operations** | Charter R3; Plan §§3.1–3.4, 6.4b; Track E E5.6–E5.7; Register R236; Kṣetra recon §§1.2–1.3 | **“Regenerable” is broader than the evidence.** `lel_events` explicitly has no writer. External priors and calibration inputs require a source-retention contract. Fingerprints cannot reconstruct lost input data. Re-running previous code does not necessarily remove rows inserted by new upsert logic or reverse a schema migration. A production-seeded rehearsal can conceal missing regeneration paths. | Classify derived outputs separately from irrecoverable inputs, event history and schema. Preserve the latter selectively. Prove regeneration into empty targets from pinned inputs, and test reversal of insertions, deletions and schema changes. |
| F9 | **MAJOR — before any MSR rebuild** | Plan §§3.8, 5.3; Track E §4a, E5.9; Model F3.FK/GUARD/PROOF | **N-32 removes one destructive edge but does not prove end-to-end integrity.** Dropping eight incoming keys prevents their cascades; it does not remove cascades below `kala_convergence` or `phala_anchors`. Stable signal IDs do not prove unchanged meaning or handle removed signals. Proof must exercise changed and disappearing signals, not only identical delete/reinsert. | Test all seven referencing tables and the transitive CASCADE/SET NULL footprint. Require correct invalidation, withheld/qualified serving and restored downstream integrity. Bind live FK and guard checks to deployment and the exact proof. |
| F10 | **BLOCKER — reconcile the executable plan before N-1** | Model L.17/LG.7, NS.*, J1.6, F3.GUARD, B.F*/B.FR.*; Plan §§5.0b, 5.3; Track E §§4a, 7–8 | **An acyclic graph still contains operational contradictions.** L.17 says release activation follows LG.7, while LG.7 depends on L.17. NS evidence has an incompatible producer schema. F3.GUARD asks for first-writer counts while MSR dispatch requires F3.GUARD. The broker excludes family readers, but their certification needs rebuilds; J1.FO’s transfer to ordinary work has no complete membership/authorization transition. | Specify bootstrap and rehearsal states explicitly. Align evidence producers and consumers. Provide authorized reader/family handover paths and valid empty-population semantics. Test representative journeys through N-1, J1, G2, family handover and closure. |
| F11 | **MAJOR — before using certification/deployment completion** | `T/detectors.py::d_levels_elevated`, `d_elevated_interface_ok`, `d_wave_deployed`, `_fetch_main`, `get`; Disposition CODE-44–45, 50–52 | **Several strict detector claims remain weaker than their labels.** Incorrect hash pins were ignored in an in-memory `levels_elevated` call. A constant empty-set implementation passed `elevated_interface_ok`. Current wave detection accepts a branch prefix and lacks the specified writer-hash/serving checks. Failed fetches can still be followed by reads of stale refs; malformed cached timestamps retain the old result. | Enforce every pin and complete population; mutation-test semantic correctness, not only interface shape. Bind deployment to exact artifacts and component identities. Failed refresh, malformed time or expired evidence must block dependent action. |
| F12 | **MAJOR — before accepting Pravāha milestones** | `T/detectors.py::d_peer_tracker_item`; Model F1.G, F2.*, F3.G*; Plan §5.3; Disposition CODE-54 | **A peer’s status string is treated as proof.** A mocked response from the wrong campaign, dated 2000, with an item marked `done` and no evidence passed. The Model’s peer items do not require evidence. Loopback location does not authenticate campaign identity or a production flip. | Require campaign identity, schema/version, freshness and immutable evidence references. Independently verify build, deployment, generation and serving facts where Suvarṇa relies on them. Treat peer downtime as unavailable measurement. |
| F13 | **MAJOR — before certification and layer closure** | Architecture §12.16; Plan §5.4(8); Track E E5.5; Families §7 | **The currency contract improves safety but is not a termination argument.** External family changes can continue indefinitely. “Watermark at least the ledger ref” needs an actual ordering definition. Certificate-ID churn can invalidate unchanged downstream semantics. Two re-walks followed by escalation bounds automation, not time to ELEVATED. | Define immutable acceptance epochs, ordered invalidation offsets and stable semantic generations. Freeze or lease upstream versions for an epoch. Specify termination assumptions and what qualified/nonterminal outcomes mean for campaign closure. |
| F14 | **MINOR** | Package §§1, 5, 6a–7; Disposition §1 F18, CODE-64; Track E §§7–9; Plan §§4.2, 5.1, 6.6; Document Map §§1, 5 | **Published counts and implementation status are inconsistent.** Track E retains 200–340 h, E5 40–65 h and E7 8–15 h against larger Plan figures. Three “pending” detector types exist. The J1 table has 18 rows including 6a, despite “17 criteria”; Q25 is omitted from the report-format range. Historical 98 kept assets versus current 97 is not reconciled. | Generate current status and counts from the pinned bundle/model; label historical figures; reconcile estimates and the retained-asset identity difference. Do not represent reported test counts as proof of this release. |

## Answers

### Q1 · Who checks Strategic Suvarṇa?

The proposed combination is insufficient. Rationale is an explanation, an owner veto is reactive, and typed decisions validate record structure rather than decision quality. Independent reviews could supply the missing check, but their required acceptance is not enforced as an independently authenticated, revision-bound prerequisite. **F1–F2.** Sources: Charter §§2, 12; Plan §4.2; Disposition CODE-36.

The widest propagation comes from an incorrect standard/applicability re-seal or J1 approval: the same weakened criterion could affect all **1,143 asset–gate cells**. An erroneous global-L0 authorization additionally affects other charts. The missing check is a protected policy-activation boundary requiring independent acceptance of the exact change and a deterministic action validator that SS cannot rewrite during that decision. Sources: Plan §§1.1, 4.2, 6.4b; Architecture §6.5; Disposition CODE-45, 49.

### Q2 · Can SS widen its own authority?

**Technically, yes; normatively, the charter prohibits some such changes.** SS can author an amendment, release the corresponding control code and record the decision under the same owner identity. An independent-review requirement in Charter §12 is not an OS or service-level restriction on that identity. Merely adding a `writer: strategic-suvarna` field does not constrain what SS can authorize. **F1.** Sources: Charter §§2, 12–13; Architecture §§2.4, 5.5; Disposition CODE-36, 60.

Keep scope changes reserved to the owner, while allowing routine SS decisions unattended. A protected activation service must reject missing independent review, changed hashes, prohibited scope expansion and attempted native-veto clearance by SS. Source basis: Charter reserved acts and §12; Plan §§4.2, 8.

### Q3 · Does anything still depend on the owner being present?

Yes. The following dependencies remain explicit or unresolved:

| Dependency | Effect | Source |
|---|---|---|
| NS.1–NS.4 and NS.8–NS.9 | Administrator setup, accounts, permissions, services and machine settings | Setup Steps 1–2; Appendix |
| NS.5 and NS.7 | GitHub account/token and Claude subscription authentication | Setup Steps 3–4 |
| NS.6 | Ruleset change after the path-guard control PR | Setup Appendix, mapping table |
| NS.10 / N-1 | Final launch signal | Setup Step 5; Plan §4.2 |
| NP.1 / E7.2 | Administrator provisioning of the builder after E7.1; E7.3 then blocks E3.7 and J1 | Setup Appendix NP.1; Model E7.2, E7.3, E3.7, J1.6 |
| Credential expiry, rotation or revocation; possible API key at G2 | Work needing that identity parks until owner action | Setup “What else could ever need you”; Charter R10 |
| Scope/end-state changes | Owner decision remains required | Charter reserved acts; Setup “What else could ever need you” |
| Clearing a native veto | Intentionally owner-only | Charter §8; Setup §3 |
| Recovery requiring unavailable administrator/authentication access | Autonomous recovery is not demonstrated | Setup safety notes; Architecture §5.5; Disposition CODE-41, 60 |
| Pravāha N-FLIP and separately owned family work | Suvarṇa depends on another campaign’s decision process | Plan §5.3; Model F2.4, F3.Gc |

The 72-hour notification is explicitly informational; it is not a guaranteed recovery or decision mechanism. “No native latency” therefore overstates the plan even though routine reviews and merges no longer wait for the owner. Sources: Plan §§6.6–6.7; Charter §7.

The retired Gochara prompt still contains historical owner gates, but its retirement banner makes those historical text, not current Suvarṇa instructions. Source: `S/prompts/L3_GOCHARA_FINAL_BRIEF_PROMPT_v1_0.md`, retirement banner.

### Q4 · Is native setup complete, correctly ordered and executable?

**Not yet. F4 is a launch blocker.** The simplified guide is useful, but several checks do not establish their stated properties:

- **Authority migration:** moving a previously swarm-owned, ACL-writable file into an owner-owned directory does not itself make that file unwritable. Post-move normalization and effective-access tests are missing. Sources: `native_setup.sh::ns4_do_folders`, `ns4_do_move_decisions`, `ns4_verify`.
- **Credential isolation:** `NS3_OWN_DIRS` uses `$HOME` during a root invocation, whereas the intended native home is pinned elsewhere. The scan’s `-perm -o=r` misses group/ACL-readable files and deliberately excludes directories and depths. It does not prove “every native secret unreadable.” Sources: `native_setup.sh`, NS.3 functions; Setup Appendix NS.3.
- **Append-only holds:** `p_ns4_holds_ready` checks existence and ownership, not the `uappnd` flag or effective clear-ledger permissions. It can skip repair of an incorrectly configured file. Source: `native_setup.sh::p_ns4_holds_ready`.
- **Sudoers:** syntax validation is good, but the script’s installed-rule predicate does not establish the Appendix’s stronger claim that `sudo -n -l` exposes exactly one authorized command. Sources: `native_setup.sh::p_sudoers_installed`, `ns2_verify`; Setup Appendix NS.2.
- **Services:** missing plist sources are skipped. Already-installed files do not establish successful bootstrap, correct runtime identity, pinned executable/settings or SS-runtime readiness. Sources: `native_setup.sh::ns8_apply`, `ns8_verify`; Disposition CODE-41, 60.
- **Claude verification:** an existing binary is accepted without checking the pinned version; the no-op command does not explicitly load the token file just written. Source: `native_setup.sh::mode_claude_token`.
- **Verification contract:** lowercase subcheck output cannot satisfy Model NS.*; NS.5–NS.7 are not verified, and failures do not produce a failing exit status. Sources: `native_setup.sh::run_verify_mode`; `T/tests/test_native_setup.py::test_verify_flags_missing_setup_as_fail`; Model NS.1–NS.9.
- **Undo:** account deletion is not tied to a durable record proving this invocation created the account. An undo after encountering a pre-existing account needs a stricter ownership-of-changes contract. Source: `native_setup.sh::ns1_undo`, `ns2_undo`.

Whether the documented GitHub invitation/token flow is eligible for the actual organization and account configuration **cannot determine from the bundle**. Exact identity, permissions, organization approval and negative server tests would establish it. Sources: Setup Step 3; Disposition CODE-40; Model LG.5.

### Q5 · Is the serving guard sufficient?

It is a sound requirement but an incomplete implementation contract. It needs to cover the complete affected output, not just directly written served tables. A canonical-chart canary does not prove safety for other charts or indirect consumers. **F7.** Sources: Plan §§6.4b–c; Charter §6(8); Track E E5.8–E5.9.

The bundle names Gochara authority and L2 producer generations. Kṣetra’s reconciliation says W7 publication is unbuilt and identifies envelope, priority, explain and ahead readers. The complete list of surfaces lacking authority mechanisms **cannot determine from the bundle** because the serving inventory and serving implementations are absent. Sources: Track E E5.8; Kṣetra recon executive summary, §1.5.

A disclosed window can satisfy N-29’s explicitly permitted alternative, provided the disclosure is inseparable from every affected response and communicates the actual limitation. A notice attached to an otherwise confident, internally inconsistent answer is inadequate protection. Recommend suppressing affected conclusions or returning clearly unavailable/qualified output until the entire affected dependency closure is valid. Source basis: Package §1, N-29; Plan §6.4c; Charter P15 and §6(8).

### Q6 · Are destructive operations without dumps sufficiently protected?

**Only for outputs whose regeneration and reversal have been proved.** R3’s blanket treatment of data and schema is not supported by that proof. `lel_events` has no orchestrator writer; Kṣetra uses external actuarial priors, classical weights and L5 event-dependent calibration. The bundle does not establish complete, immutable sources for all such material. **F8.** Sources: Charter R3; Plan §3.1–3.4; Register R236; Kṣetra recon §§1.2–1.3.

A fingerprint proves identity or difference, not recoverability. Rebuilding a production-seeded copy can pass while relying on rows that were never regenerated. E5.7 should start with empty target outputs and pinned retained inputs. Schema reversal and removal of newly introduced rows need separate cases. This calls for selective preservation of irrecoverable inputs, not automatic whole-database dumps. Sources: Track E E5.6–E5.7; Plan §6.4b.

### Q7 · Is F-3 correct and complete?

**Directionally defensible, not complete enough to authorize.** Dropping the eight keys stops those direct MSR cascades and removes the refusal dependency. Deterministic IDs preserve references only for identities that remain valid; they do not establish unchanged semantics or replace deleted signals. Sources: Plan §5.3; Track E §4a.

Downstream rebuilds can still cascade through `kala_convergence` into `kala_darshana`, `kala_obstruction` and `phala_anchors`, then into the listed Phala tables, with additional SET NULL effects. Those rows need invalidation, serving protection and recovery proof. **F9.** Source: Plan §3.8.

Bare `ON DELETE SET NULL` on all eight keys is rightly rejected as an immediate substitution because four columns are NOT NULL. That does not prove all alternatives to dropping every key are unsuitable; choosing among changed nullability, deferred integrity or generation-based references requires the absent writer/schema evidence. Sources: Plan §§3.8, 5.3; Track E §4a.

### Q8 · Is serving other charts against stale L0 inputs acceptable?

**Conditionally under N-29, but not yet demonstrated.** The policy explicitly permits disclosed maintenance. It must identify the chart’s actual input generation and the resulting limitation, without implying that stale and current components form a coherent current result. The notice must persist until repair, rather than ending when only the canonical-chart canary passes. **F7.** Sources: Plan §§6.4b–c; Charter §6(8).

Whether existing serving code carries that qualification through every output **cannot determine from the bundle**. A per-chart dependency inventory and serving tests would settle it. Source: Track E E5.8.

### Q9 · Did the previous blockers F1–F6 close?

These are the **previous review’s** finding numbers.

| Previous finding | Assessment of v1.5 documents plus CODE specs |
|---|---|
| F1 — false gate completion | **Partial.** CODE-36 addresses typed outcomes, corruption and prerequisites. Mandatory revision pins, trustworthy evidence and reviewer authentication remain missing. Current code still accepts refusal prose and ignores the corrupt-log count. Sources: Disposition §1 F1, CODE-36/47; `T/gates.py::evaluate_decision_gate`; Model decision items. |
| F2 — authority/isolation | **Not closed.** Separate swarm identity helps, but native-account SS restores a privileged unattended failure domain; setup migration can preserve swarm write access. Sources: Disposition §1 F2; Architecture §§2.4, 5.5; `native_setup.sh::ns4_apply`. |
| F3 — Monitor contradiction | **Partial.** Explicit `not_applicable` and stage composites are the right specification. Current code converts earlier-stage failures to `ok`, and callers do not pin the required stage. Sources: CODE-38; `monitor.py::apply_stage`; `detectors.py::d_monitor_check_ok`. |
| F4 — holds | **Not closed.** Append-only storage improves persistence, but exclusive action-boundary enforcement, native-clear authentication, corruption handling and recovery under hold remain incomplete. Sources: CODE-39/43/53; Charter §§6, 8. |
| F5 — main protection | **Not closed.** Changing the intended authority to autonomous merging is legitimate; a worker-readable merge token still bypasses the local gate. Sources: Disposition §1 F5; Charter §13; CODE-40/43. |
| F6 — runtime | **Partial.** Durable services and atomic lane claims are appropriate. Actual conductor locking races; crash recovery and fencing must protect remote effects, not only local queue commits. Sources: CODE-41/42/63; `conductor_lock.py::acquire`; Architecture §5.5. |

### Q10 · Can the swarm merge harmful changes?

**Yes, under the specified credential and enforcement arrangement.** Required CI and a queue do not themselves require the local gate’s ACCEPT or hold check. A post-merge audit discovers damage after code may already have deployed. **F3.** Sources: Plan §§3.8, 6.4; Charter §13; Disposition CODE-43.

The guard must run from protected code and protected ownership data. Its implementation, imported helpers, `FAMILY_ASSETS.json`, coordination rules and executable policy inputs need equivalent protection. Paths outside a denylist and migrations inside 1200–1299 can still affect another workstream semantically. Sources: Track E §2 boundaries, E0.2; CODE-43.

Squash merging also requires exact binding between reviewed head, tested merge candidate, resulting commit and deployment. Authorization must be checked when the queued change executes; a hold introduced after enqueue must not be ignored. Sources: Plan §§5.4, 6.4; CODE-43/52.

### Q11 · What does the OS boundary protect?

If correctly installed, it separates worker code from native authority files and the builder credential. Worker code still owns its worktrees, events/evidence and runtime state, and can read its own reader, GitHub and Claude credentials. **F1, F3–F4.** Sources: Charter §13; Architecture §2.4.

A tightly scoped read-only reader is a reasonable residual if its database privileges are continuously verified. A worker-readable token that can authorize repository merges is not acceptable as the supposed exclusive merge gate’s underlying credential. Running SS as `Dev` also places the owner’s available permissions inside unattended execution. Sources: Charter §13; `S/D6_SUVARNA_READER_RUNBOOK_v1_0.md`; Architecture §5.5.

Live ACLs, inherited permissions, Keychain access and effective database grants **cannot determine from the bundle**. Negative tests under the actual identities are required. Sources: Setup Appendix NS.2–NS.4; Model LG.2.

### Q12 · Can holds be lost, bypassed or cleared incorrectly?

Current hooks can be bypassed by dispatch performed inside an allowed indirect program; command-marker matching is not the execution boundary. If the interpreter is missing, the shell fallback also cannot classify the request and reaches its permissive ending. Sources: `T/hold_guard.py`; `T/hold_guard.sh`, fallback classification.

The proposed append-only ledger is better, but malformed set/clear records must fail closed, its filesystem protection must be verified, and SS must not share the native-veto clearance identity. Broker and merge enforcement are specified, not shown as implemented. **F5.** Sources: Charter §8; CODE-39/43/53; Package §6a.

Recovery needs explicit treatment: Plan §6.4b says hold, revert, redeploy and rebuild, while the gate/broker refuse held operations. Granting a specific reversal while retaining the hold resolves this without allowing ordinary work to resume. Sources: Plan §6.4b; Charter §6; CODE-43/53.

### Q13 · Does each launch gate prove its condition?

**No.** Most LG items inspect a claimant-written JSON `result`, and their control-commit pins are blank. Supplying the correct public commit hash would bind a statement to a release, but would still not prove the drill occurred. **F2.** Sources: Model LG.*; `T/detectors.py::d_evidence_verified`; CODE-47.

| Gate | Additional proof required |
|---|---|
| LG.1 | Trusted execution of refusal, corruption, wrong-revision, premature-approval and forged-event cases against the released evaluator. |
| LG.2 | Effective negative access tests as the actual swarm UID, including file contents, ACLs, parent replacement, symlinks and builder-secret access. |
| LG.3 | Explicit S1 composite; required unmeasurable checks block; builder is `not_applicable`, not healthy. |
| LG.4 | Real ledger protections and refusal of indirect, direct-token, malformed-payload, missing-interpreter and queued-action bypasses. |
| LG.5 | Attempt to merge a green PR directly with the worker credential; test self-modified guard code, exact required checks and merge-queue behavior. |
| LG.6 | Simultaneous starts, crash points around claim/spawn/action/record, stale fencing and watchdog recovery. |
| LG.7 | Independently generated regression and real-CLI results for the exact release and effective settings; resolve the L.17 activation ordering. |
| LG.8 | Semantic plan checks as well as graph lint: mandatory pins, evidence schemas, stage requirements and executable family/recovery paths. |
| LG.9 | No standalone Model item exists. Its condition intentionally moved to E5.6, E5.7 and F3.PROOF before J1/W0; those still need trustworthy drill evidence. |
| LG.10 | A completed SS park with measured latency and usage, plus duplicate, failure and unavailable-runtime cases. One successful response is not sustained availability. |

Sources for the table: Disposition §2 and CODE-36–63; Model LG.1–LG.8, LG.10; Track E E5.6–E5.7.

### Q14 · Are there deadlocks or unreachable items?

The explicit **211-item graph has no missing dependencies or cycles** in my read-only traversal. That does not establish operational reachability. Sources: Model `items[].depends_on`.

The material conflicts are:

1. **L.17/LG.7 activation ordering:** the narrative requires LG.7 before moving control, while LG.7 depends on L.17. Test a candidate release first, then atomically activate it. Sources: Model L.17, LG.7.
2. **NS producer/consumer mismatch:** the supplied setup verifier cannot produce the fields NS.* requires. Sources: Model NS.1–NS.9; `native_setup.sh::write_verify_json`.
3. **Pre-go runtime drills:** “no session starts before N-1” needs an explicit restricted drill mode for LG.6/LG.10 and a clear distinction between testing readiness and enabling campaign work. Sources: Plan §5.0b; Model LG.6, LG.10; CODE-41/60.
4. **F3.GUARD’s first-run evidence:** the brief requires counts from the first MSR writer, but the writer cannot run until F3.GUARD is done. Define rehearsal evidence as sufficient for that component, followed by a separate live postcondition. Sources: Track E §4a; Charter §6(6).
5. **Family/readers dispatch:** `family_set` includes readers; the broker rejects that set, while B.FR.* requires their certification. J1.FO can transfer Saṅgam/Kṣetra to ordinary work without specifying all corresponding membership and grant changes. Sources: Track E E5.3, E6.3, E7.1; Families §7; Model B.FS, B.FK, B.FR.*.
6. **Empty populations:** current detectors reject empty wave/family populations. Any legitimate exclusion or handover yielding an empty set needs an explicit completed-with-zero-obligation outcome, while missing population evidence must still block. Whether the final frozen map produces such a case **cannot determine from the bundle**. Sources: `detectors.py::d_levels_elevated`, `d_assets_elevated`; Track E E6.3.
7. **Hold/recovery ordering:** reversal cannot use ordinary held merge/build paths. Sources: Plan §6.4b; CODE-43/53.

The supposed pending detector types are not an actual registration blocker: `evidence_verified`, `ci_job_passed`, `elevated_interface_ok` and `peer_tracker_item` are implemented. Their incomplete semantics are the problem. Sources: `T/detectors.py`, corresponding methods; Model `notes.code_types_pending`; CODE-64.

F2.4 and F3.Gc depend on Pravāha’s flip/retirement sequence. SS cannot safely force those decisions. E3.7→E7.3→E7.2 is an explicit post-N-1 owner provisioning dependency, not a graph cycle. Sources: Model F2.4, F3.Gc, E3.7, E7.3, E7.2; Plan §5.3.

### Q15 · Are the estimates and calendar honest?

Deferring a dated calendar until rehearsal and G2 is honest. Publishing broad effort ranges is useful only if their exclusions and controlling assumptions remain visible. The least defensible bound is **Tracks I/B at 10²–10³ hours**, because their scope includes unresolved per-asset work and potentially transferred family implementation. The 60–110-hour launch estimate also lacks demonstrated runtime/security integration throughput. Sources: Plan §6.6; Track E §9; Families §7.

The required numerical cross-checks produced these results:

| # | Figure checked | Result and source |
|---|---|---|
| 1 | Active assets | **40+19+23+21+9+15=127**, consistent. Plan §§1, 3.1–3.4. |
| 2 | Core gate cells | **127×9=1,143**, consistent. Plan §§1.1, 5.5. |
| 3 | Current retained assets | **40+19+22+12+0+4=97**, internally consistent. Historical supersession says **98**; the identity-level reconciliation is absent. Plan §3.1–3.4; Document Map §5; decisions snapshot `NIRMANA-SUPERSESSION`. |
| 4 | Dependency depth | Levels **0–26 = 27**, consistent. Architecture §6.1; Model wave ranges. |
| 5 | Wave populations | **65+13+14+17+9+9=127**, consistent with the stated wave partition. Architecture §6; Model I.W0–I.W5. |
| 6 | Broad depth groups | **55+23+49=127**, consistent. Architecture §6.1. |
| 7 | L0 groups | **24+11+4+1=40**, four levels, consistent. Plan §5.4. |
| 8 | Register states | Parsed **180 OPEN+2 CLOSED_ON_BRANCH+16 DONE+51 CLOSED+2 PARTIAL+1 MEASURED=252**. Header agrees. Register §0.1 and rows; `detectors.py::parse_register`, `register_counts`. |
| 9 | Open-row severity | **4+95+71+10=180**, consistent. Register §0.2; Plan §3.1–3.4. |
| 10 | MSR FK population | Eight keys from seven tables, four NOT NULL columns, consistently stated. Their live truth is not independently verified. Plan §3.8; Track E §4a. |
| 11 | Track E effort | Brief components total **198–340 h**, rounded to **200–340**; Plan says **250–450**. E5 differs **40–65 versus 55–90**; E7 **8–15 versus 15–30**. This contradicts Disposition F18’s “everywhere” claim. Track E §§7–9; Plan §§5.1, 6.6; Disposition §1 F18. |
| 12 | Track A effort | **157+130–250+30–65=317–472 h**, consistent. Track A estimate; Plan §6.6. |
| 13 | Kṣetra field rows | **8,570,075+2,412,882=10,982,957**, consistent. Kṣetra recon §1.2. |
| 14 | Synthetic canonical windows | **15,024/17,528≈85.7%**, consistent. Kṣetra recon summary, §1.2. |
| 15 | J1 checklist size | **18 rows**, numbered 1–17 plus 6a; Package §1 calls it **17 criteria**. Plan §4.2. |
| 16 | Model populations | **211 items, 81 decision definitions, 41 decision-bound items; zero revision pins on those 41 items.** Model `items`, `decisions`. |
| 17 | Launch gates | **Nine LG items**: LG.1–LG.8 and LG.10. This is intentional in Disposition §2, despite introductory references to “ten launch gates.” Model LG.*; Disposition introduction and §2. |
| 18 | Questions | **25 questions**, but report-format §5 still says Q1–Q24. Package §§4–5. |
| 19 | Bundle integrity | **93 included payload files; all 93 hashes match.** Five `NOT-INCLUDED` entries are intentional exclusions, not missing payloads. `MANIFEST.txt`. |
| 20 | Code-status counts | Package reports **822 tests**; Document Map/Disposition retain **685/686** and pending-type language. The three listed pending types exist. The current parametrized test result **cannot determine from the bundle** without executing the suite. Package §§6a–7; Document Map §1; CODE-64; `T/detectors.py`. |

The register’s broader freeze sentence remains inconsistent with the narrowed current rule, although Plan §3.5 explicitly declares precedence and assigns its correction. That is known, unresolved document drift rather than an additional hidden gate. Sources: Register §1; Plan §3.5; Disposition F18.

### Q16 · Is there a convergence argument?

There is a better **currency and bounded-retry policy**, not a complete convergence argument. Semantic fingerprints can prevent unnecessary invalidation; watermarks can prevent accepting results before invalidation processing catches up. Their ordering and semantic equivalence rules must be precise. **F13.** Sources: Architecture §12.16; Track E E5.5.

Termination additionally needs a finite population, stable upstream inputs during an acceptance epoch, deterministic or bounded-equivalence rebuilds, and fixes that eventually discharge obligations. Continually changing family production violates the stability assumption. Two retries then an SS park prevents endless automatic retries but does not make the asset ELEVATED. Sources: Families §7; Plan §5.4(8); Charter §10.

### Q17 · Is the Saṅgam/Kṣetra ownership plan sound?

Owning design immediately is sensible. Ownership at J1 needs an explicit acceptance and handover protocol; “acknowledged a notice **or shown commits**” is too weak to establish that a live session accepts responsibility and can deliver. **F10, F13.** Sources: Plan §5.3; Model J1.FO.

A later session must not implicitly seize ownership. Require a lease transfer, compatible brief/version, migration reservations, updated protected family/dispatch maps, and invalidation of affected evidence. A previously frozen map cannot silently become a different authorization policy. Sources: Architecture §12.4; Families §7; Disposition CODE-45.

### Q18 · Can the seven named signals be made falsely complete?

Yes for several current implementations; some current mismatches fail closed instead. The distinction matters.

| Signal | Current code and attempted counterexample | Remaining specification issue |
|---|---|---|
| Gate evaluator | **Reproduced `done`** for refusal prose with `state: decided` and a corrupt-log count. Revision checking is optional; the real Model has no decision-item pins. `gates.py::evaluate_decision_gate`; Model decision items. | CODE-36 should replace prose semantics, require pins and authenticated prerequisite evidence. Its recording-time snapshot must not be mistaken for continuing action permission. |
| `evidence_verified` | **Reproduced `done`** for fabricated PASS, null required value and blank commit pin. `detectors.py::d_evidence_verified`; `tests/test_detectors_v15.py::test_evidence_verified_empty_commit_pin_is_skipped_not_checked`. | CODE-47’s nonempty fields and commit equality still do not prove execution. Protect the producer and raw results. |
| `ci_job_passed` | Current code binds the named job to current local `origin/main`, stronger than merely choosing an older successful completed run. A failed fetch can nevertheless leave that ref stale. `d_ci_job_passed`, `_fetch_main`. | CODE-50 must retain exact-current-revision semantics and prove trusted test execution, including mutation cases. Successful execution of weakened tests is not substantive acceptance. |
| `peer_tracker_item` | **Reproduced `done`** for wrong campaign, old generation timestamp and no evidence. `d_peer_tracker_item`. | CODE-54 needs identity, freshness and evidence validation, not only status equality. |
| `wave_deployed` v2 | Current code checks PR files and merge ancestry, but accepts a head-ref prefix and lacks v2 writer-hash/serving checks. A recorded packet can describe an unrelated matching-prefix PR. `d_wave_deployed`. | CODE-52 improves binding; also require a complete authorized packet and tie hashes to the actual deployed artifact, including serving components. |
| `main_protected` v2 | The actual v2 Model configuration lacks the current implementation’s `allowed_logins`/`bypass_only` keys, so it returns pending. That is **not** a reproduced false PASS. `d_main_protected`; Model L.16b. | CODE-40 does not make the local merge gate exclusive. Pin the full rule set, trusted authorization check and exact bot privileges. |
| `levels_elevated` with pins | **Reproduced `done`** with incorrect level/family hash pins and a supplied one-asset population. The pins are ignored. Separately, a constant empty-set function passed `elevated_interface_ok`. `d_levels_elevated`, `d_elevated_interface_ok`. | CODE-44/45 must test complete membership, unreadable inputs, stale certificates and deliberately wrong ELEVATED results—not only a callable returning a set. |

These were in-memory counterexamples or source-level constructions, not live GitHub/database tests. The full suite’s reported pass count does not discharge them. Sources: methods and tests cited in the table; Package §6a.

### Q19 · What runtime failures remain, and should SS run as the owner?

**SS should not run with the owner’s ambient authority.** Keep its unattended decision function, but give it only the ability to submit typed proposals and read necessary evidence. Policy activation and action execution belong behind the protected validator. **F1, F6.** Sources: Architecture §5.5; CODE-60; Charter §§12–13.

Remaining failure cases include simultaneous acquisition, process death between intent/spawn/PID recording, death after a remote action but before local completion, stale-holder side effects, PID reuse, poisoned requests, duplicate decision triggers, and self-generated heartbeat/metric events causing unnecessary passes. Sources: `conductor_lock.py`; `lane_launch.py`; Architecture §§5.1–5.5; CODE-41/42/60/62.

CODE-63 also needs per-heartbeat receipt tracking. Shared event-log modification time alone can advance because another actor writes while a Conductor is dead. An unavailable Mac must not cause a cloud maintenance guard to clear or leave queued production changes unguarded. Source basis: CODE-63; Charter §6(8); Plan §6.4c.

### Q20 · What is the standing token spend?

Using Architecture §5.5’s **50–100k reread tokens per Conductor pass**:

`daily input ≈ (engine passes + exec passes) × 50–100k + SS input + worker/reviewer input`

With true deterministic idle filtering, idle Conductor model spend can approach zero; periodic script checks do not require a model invocation. If each Conductor runs every ten minutes while busy, that is **288 passes/day**, or **14.4–28.8 million input tokens/day**, before SS and workers. If both unnecessarily invoke a model every 30 minutes, it is **4.8–9.6 million/day**. These are scenarios, not forecasts. Sources: Architecture §5.5; CODE-41/59/60.

Actual SS pass frequency, context size, cache treatment and monetary cost **cannot determine from the bundle**. Subscription billing is not evidence of zero consumption or unlimited capacity. Sources: Plan §6.7; Charter §9; CODE-59.

Per-pass metrics are a useful start, but failed/killed runs and SS usage must also be counted. Show running totals and rates promptly; a daily digest alone can lag rapid consumption. This respects N-15’s no-ceiling decision while satisfying visible spend. Sources: Charter §9; Architecture §12.8; CODE-59/60.

### Q21 · What must be true before N-1?

Ranked:

1. SS and workers cannot bypass the protected authority, veto, merge or action boundary.
2. Gates and evidence fail closed, with mandatory release/revision binding and trustworthy producers.
3. Corrected setup is proved under the actual identities.
4. The durable runtime passes concurrent-start and crash-recovery drills.
5. The final Model has executable bootstrap, recovery and family transitions.
6. The exact control release passes independent regression and real-CLI integration.
7. Later production stages remain technically locked until serving, regeneration, F-3 and builder proofs pass.

The current bundle does not establish these conditions. **F1–F12.** Sources: Package §6a–7; Plan §§4.2, 5.0b; Disposition §2; Model FI-7, J1.6.

### Q22 · What is the single biggest risk and cheapest high-value change?

**The same automated trust domain can author the rule, supply its evidence and authorize the resulting action.** Owner-account SS makes that problem extend beyond the campaign worker boundary. Sources: Charter §§2, 12–13; Architecture §5.5; CODE-36/47/60.

The cheapest structural improvement is to make SS an unprivileged proposer and concentrate authorization in one small, protected deterministic service. Remove merge-capable credentials from workers. That reduces several independent bypass paths without requiring the owner to review routine work. Source basis: F1–F5; Charter §6; CODE-43/53.

### Q23 · Is the Pravāha interface sound?

A peer tracker is useful for scheduling; it is insufficient as sole acceptance evidence. Suvarṇa appropriately retains independent certification, but upstream milestones still need authenticated, versioned facts. **F12.** Sources: Plan §5.3; Families §7; CODE-54.

If the peer is wrong, current status-string acceptance can advance work prematurely. If it is down, current code returns pending rather than the spec’s unknown; both prevent completion, but the reason should be explicitly “unavailable measurement.” Preserve previously accepted immutable proof while requiring fresh safety facts before new actions. Sources: `d_peer_tracker_item`; CODE-54.

Pravāha’s migration report already differs from the bundled production observation. That illustrates why a peer assertion must remain distinct from independently checked deployment/database state. Whether the discrepancy has since resolved **cannot determine from the bundle**. Sources: Plan §3.8; Package §7.

### Q24 · Do you agree with each v1.5 decision?

| Decision | Assessment | Cost of being wrong; source |
|---|---|---|
| N-31 — global-L0 builder grant | **Agree conditionally.** Server-scoped automation is preferable to recurring owner dispatch, but must enforce impact, serving and regeneration prerequisites. | Every chart can be affected. Plan §6.4b; Charter R9; Track E E7.1. |
| N-32 — drop eight MSR keys | **Do not accept as fully proved.** Plausible remedy; require F9’s mutation and transitive recovery proof. | Dangling or semantically stale references and downstream loss. Plan §§3.8, 5.3; Track E §4a. |
| N-33 — serving guard | **Agree with the principle; reject the current incompleteness.** | Incorrect or partial product output despite a nominal maintenance notice. Plan §6.4c; Charter §6(8). |
| N-34 — durable runtime | **Agree.** Replace bespoke non-atomic ownership logic and prove recovery. | Duplicate actions, stalled work and repeated spend. Architecture §5.5; CODE-41/42. |
| N-35 — append-only holds | **Agree conditionally.** Separate native-clear identity and allow bounded recovery under hold. | Lost veto, unauthorized continuation or recovery deadlock. Charter §8; CODE-39. |
| N-36 — build broker | **Agree.** It must enforce the complete action contract, not only a subset. | Scope-valid but premature or unsafe production rebuild. Charter §6; CODE-53. |
| N-37 — authority/control isolation | **Agree for workers; disagree with native-account SS as implemented in the wider design.** | Unattended access to owner-level authority and available credentials. Charter §13; Architecture §§2.4, 5.5. |
| N-38 — merge gate | **Agree only with exclusive server/credential enforcement.** | Harmful code reaches shared main and deploys before audit. Plan §6.4; CODE-43. |
| N-12 — canonical chart only | **Agree as a certification scope.** Explicitly manage L0’s effects on other charts. | Unqualified stale output outside the measured chart. Plan §§5.4, 6.4b. |
| G16 — Steward brief approvals | **Agree conditionally.** Approved classes and output boundaries need a versioned, enforceable contract. | Quiet expansion or weakening of asset obligations. Charter G16; Plan §5.4(1). |
| SEAL-G — adopt Pravāha doctrine | **Agree conditionally.** Pin the actual sealed artifact and map it independently to Suvarṇa’s gates. | Wrong generation/doctrine accepted as the certification basis. Plan §5.3; Families §1. |
| J1.FO — family ownership rule | **Agree with explicit assignment at J1; disagree with commits alone constituting ownership acceptance.** | Orphaned work, conflicting writers or unauthorized handover. Plan §5.3; Model J1.FO. |

The costliest failure is **N-37’s isolation claim combined with owner-account SS**, because it exposes the authority that can weaken the remaining safeguards. N-38 is the most direct route from ordinary worker compromise to shared production code. Sources: Architecture §§2.4, 5.5; Charter §13; CODE-43/60.

### Q25 · Is the control apparatus proportionate, and what is the simplest safe design?

The required safety functions are proportionate; the overlapping custom machinery is not yet demonstrated to be. The proposed system already needs roughly thirty code specifications before its engine work, while still relying on mutable claimant evidence and duplicated enforcement logic. That complexity can conceal rather than reduce risk. Sources: Package §6a; Disposition §5; Plan §6.6.

The following controls can be removed, combined or narrowed without weakening the four priorities:

| Current mechanism | Simplification | Property retained; source basis |
|---|---|---|
| SS running as `Dev` | Unprivileged SS decision worker submitting proposals | Unattended decisions; protected owner credentials and veto. Architecture §5.5; Charter §§2, 13. |
| Separate custom broker and merge authorization logic | One protected action validator with narrow build/merge adapters and separate scoped credentials | Consistent Charter §6 checks and exclusive execution. CODE-43/53. |
| Multiple queue/claim/decision state mechanisms | A small transactional journal plus OS locking and idempotent action IDs | Durable ownership and crash recovery. CODE-36/41/42/62. |
| Prompt/hook command parsing as a primary barrier | Keep the hook only as early feedback; enforce at credential-bearing services | Holds cannot be bypassed by indirect programs. CODE-39/43/53. |
| Always-running expensive Conductor reasoning | Deterministic readiness checks and bounded model jobs on actionable changes | Progress with low idle spend. Architecture §5.5; CODE-41/59. |
| Standalone SS orchestration stack | One bounded decision-job type in the supervised runner, with different permissions | Decision SLA without owner credentials. CODE-60. |
| Swarm-written PASS JSON as acceptance | Trusted job artifacts and a read-only dashboard projection | Earned evidence and visible progress. CODE-47; Plan §9. |
| Broad secret-name scanning as principal isolation proof | Restrict native directories by identity; retain scans as drift detection | Credential protection without pretending a pattern scan is exhaustive. Setup NS.3; Charter §13. |
| Parallel ownership inferred from activity | One explicit owner and transfer record per protected asset | No competing writers. Plan §5.3; Architecture §12.4. |
| Generalized candidate/publication machinery for every asset | Use existing generation mechanisms where present; use explicit maintenance/unavailable responses where suitable | N-29’s serving priority with less implementation surface. Plan §6.4c. |
| Blanket recovery assumptions or universal dumps | Preserve irrecoverable inputs selectively; rehearse derived-output regeneration | Recoverability without unnecessary copies. Charter R3; Track E E5.7. |
| Duplicated narrative counts/status | Generate them from the pinned model and release manifest | Reviewability with less drift. Package §7; Model notes; Document Map §1. |

Do **not** remove worker identity isolation, scoped credentials, trusted required checks, current-action authorization, the owner veto, serving protection or proof of regeneration. Those address the stated priorities directly. Sources: Package §1, N-29; Charter §§6, 8, 13.

The simplest safe design is: unprivileged AI workers produce code and typed decisions; trusted CI produces evidence; a protected deterministic service validates the pinned policy, required independent reviews, holds, ownership, deployment, inputs and serving state, then executes an idempotent scoped action. A standard supervisor restarts bounded jobs. The dashboard reads the journal. Owner involvement remains limited to physical credentials/setup, scope changes, N-1 and deliberate veto actions. Source basis: Charter §§2, 4, 6, 8; Plan §§4.2, 6.7; CODE-36/41/43/53/60.

The highest-risk unnecessary complexity is the **owner-account autonomous decision runtime coupled to self-modifiable control releases**. The next is duplicated authorization spread across prompts, shell parsing, JSON assertions, local wrappers and server checks. **F1–F6.** Sources: Architecture §§2.4, 5.5; Disposition CODE-36–63.

## Conditions for launch

These conditions are **before N-1**. They permit later-stage implementation only behind enforceable stage barriers; they do not require all 127 assets to be elevated before launch.

1. **Separate authority:** demonstrate that workers and SS cannot alter active enforcement policy, fabricate required independent acceptance, read native/builder secrets or clear a native veto. Test policy activation against wrong/missing review hashes. Sources: F1/F4; Charter §§12–13; Model LG.2.
2. **Close authorization bypasses:** with the actual worker credential, refuse direct merge and production dispatch outside the protected service, including a green PR lacking ACCEPT and an action queued before a hold. Sources: F3/F5; CODE-40/43/53.
3. **Make evidence trustworthy:** pass negative tests for refusal, corrupt logs, missing prerequisites, wrong revisions, blank pins, fabricated PASS, null required fields and stale evidence. Acceptance artifacts must be produced and retained outside claimant control. Sources: F2/F11; LG.1, LG.7–LG.8; CODE-36/47/51.
4. **Prove corrected setup on macOS:** verify effective permissions, ACLs, ancestry, append-only flags, sudo scope, exact identities and CLI version; emit Model-compatible NS.1–NS.9 results and fail the command on any failed check. Sources: F4; Setup Appendix; CODE-57.
5. **Prove durable execution:** concurrent starts yield one owner; kill/restart at each dispatch boundary does not duplicate external actions; stale tokens cannot act; absent sessions and unprovisioned builders cannot read healthy. Sources: F6; LG.6; CODE-41/42/63.
6. **Prove holds and recovery:** malformed/unreadable ledgers and unavailable hooks cannot permit action; native veto survives restarts; a specific authorized reversal works while all ordinary actions remain held. Sources: F5; LG.4; Charter §§6, 8.
7. **Reconcile the executable plan:** eliminate bootstrap ordering conflicts, align evidence schemas, define family-reader/ownership transitions and empty populations, and pass representative N-1→J1→G4 state-machine scenarios. Sources: F10; Model; CODE-58.
8. **Lock production stages:** demonstrate that J1/build/global-L0 authority cannot activate without trusted serving-inventory, transitive-footprint, F-3, empty-target regeneration, reversal and builder-scope proofs. Sources: F7–F9; Charter §6; Track E E5.6–E5.9, E7.
9. **Bind peer and currency evidence:** reject wrong-campaign, wrong-generation, stale and evidence-free peer states; prove semantic-generation and invalidation behavior under unchanged rebuilds and concurrent family changes. Sources: F12/F13; CODE-54; Track E E5.5.
10. **Review one final pinned release:** reconcile both independent reviews and all finding dispositions; correct the count/status/estimate drift; show SS latency and usage metrics from drills; only then obtain N-1 on that exact final set. Sources: F14; Package §2; Model L.20a–L.22, LG.10, FI-7.

## What could not be assessed

| Matter | Assessment and evidence needed |
|---|---|
| Actual native setup and operating-system enforcement | **Cannot determine from the bundle.** Need effective-identity tests on the intended Mac, including ACLs, sudoers, launchd and credential access. Setup Appendix; Package §7. |
| Live GitHub permissions, queue enforcement and required checks | **Cannot determine from the bundle.** Need ruleset/API captures and negative tests using the actual scoped identities, including direct merge attempts. Plan §3.8; CODE-40/43; LG.5. |
| Current production FKs, grants, guard definitions, images and serving state | **Cannot determine from the bundle.** The Plan supplies dated observations, not independently executable live evidence. Need read-only captures bound to the reviewed action/release. Plan §3.8 and Appendix A. |
| Full standard, census, ledger and ELEVATED correctness | **Cannot determine from the bundle.** Tier documents, certification/gap ledgers and census artifacts are excluded. Need pinned inputs and independent mutation/coverage tests. Package §3; Plan §§1–2; Track E E6. |
| Actual serving coverage and regenerability | **Cannot determine from the bundle.** Need the completed inventory, retained-source manifests, empty-target rebuild results and reversal drills. Track E E5.6–E5.9. |
| Pravāha doctrine, decisions and production milestones | **Cannot determine from the bundle.** Its repository is excluded; need immutable versioned artifacts and independent production checks for relied-upon facts. Package §3; Plan §5.3. |
| Full test-suite pass count and deployed control behavior | **Cannot determine from the bundle.** I did not run file-writing fixtures or live integrations. Need independent results from the exact candidate release, followed by activation verification. Package §6a; LG.7. |
| Completion date, actual token use and monetary cost | **Cannot determine from the bundle.** Need measured rehearsal/G2 throughput, SS and worker usage, cache accounting and the applicable billing records. Plan §§6.6–6.7; CODE-59. |