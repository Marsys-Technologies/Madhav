---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.13"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "50b871cef (campaign/pravaha)"
reviewed_heads:
  - {ref: "campaign/pravaha", head: "50b871cefc29185315ef25574068de0ac0d5fbda"}
  - {ref: "origin/main", head: "0bf602f33afbe2ad4a345ad0b5173a90ff0491d3"}
  - {ref: "origin/pravaha/a53-am5-inventory", head: "df65685d0b822a14b53270324c2f04a071cb3642"}
  - {pr: 2975, ref: "origin/pravaha/b6-gochara-seal-workflow", head: "8a71fde5072a62d9205adc5f33f0746f56ddf6b9"}
  - {pr: 2976, ref: "origin/pravaha/b6-gochara-verification-job-def", head: "1e735d2655258191e982ab49e513546d9baf165e"}
  - {pr: 2981, ref: "origin/pravaha/b6-gochara-seal-gate-proof", head: "c3e16405f1bff0ed0d7ff3f1684f9f806a42af0d"}
  - {pr: 2963, ref: "origin/pravaha/b6-gochara-role-provisioning-oneshot", head: "9bbad986ab755044412354e437de52b37a219ada"}
  - {pr: 2961, ref: "origin/pravaha/b6-act7-verifier-secret-isolation", head: "84331f7042825bd7e86b5ea8909173c3b8e0a9bc"}
  - {pr: 2949, ref: "origin/pravaha/b6-1241-verifier-sealer-grants", head: "5e080e9c157e3d97c596b8913c19e06508895682"}
  - {pr: 2867, ref: "origin/pravaha/b6-am5-inventory-migration", head: "e4d31c9ef82aa2e3874cd2095d295622f6756bf6"}
  - {pr: 2919, ref: "origin/pravaha/b6-am21-p1-anchor-1233", head: "728b91501ad5c3b653a6130c7cac792b381871da"}
  - {ref: "origin/pravaha/b6-composed-rehearsal-integration", head: "440f0e06aad61b093543e1f298a33a435704ace8"}
  - {pr: 2952, ref: "origin/pravaha/b6-composed-rehearsal", head: "f4809ba3357adcc39e29126df3db527a20dcc180"}
  - {pr: 2923, ref: "origin/pravaha/b6-stage1-candidate-measurement", head: "d52cbea971944454785480398aefa5da568b30f8"}
authority: "Review only; authorizes nothing."
---

## Verdict

**REJECT for the protected window and first seal as submitted.** The original late-coverage-write race is repaired, and the transport, approval selection, producer fields and sealer identity checks have improved substantially. However:

1. An ordinary builder can still append a digested contact **after sealing**.
2. A status-only update can return a sealed manifest to `candidate`, permitting another persisted brief.
3. The executed-resource checker accepts a changed entry point and treats missing retry configuration as zero retries.
4. The isolation preflight accepts an unexpected principal capable of creating keys for the verifier service account.

These are source defects. **This packet has not reached the point where only operational acts and execution receipts remain.**

The approval arrangement is assessed exactly as ruled: **the steward, an AI agent session, approves under the owner’s account. It is not an independent human check.** Numerical activation remains disabled.

| Component | Verdict |
|---|---|
| Writer / final 1240 | **REJECT** — R14-1, R14-2 |
| #2975 sealing workflow | **REJECT** — R14-3 |
| #2961 isolation preflight | **REJECT** — R14-4 |
| #2976 verification-job definition | **ACCEPT_WITH_AMENDMENTS** — acceptable deployment/readback design; depends on corrected isolation gate and operational checks |
| #2981 no-secret gate proof | **ACCEPT** for its limited proof purpose |
| #2963 provisioning | **ACCEPT_WITH_AMENDMENTS** — source improvements accepted; operational-document corrections remain |
| #2949 / 1241 v6 | **ACCEPT** for the inspected grant surface |
| Runbook v1.10 and accompanying specifications | **ACCEPT_WITH_AMENDMENTS** — R14-5 |
| Capacity evidence | **ACCEPT_WITH_AMENDMENTS** — sufficient for a controlled next execution after source repairs; R14-6 and actual-count measurement remain |
| #2923 measurement tooling | **ACCEPT** for the existing, diagnostic `(d)` scope |

No later head was observed in the local refs inspected. This review uses the frozen objects above; remote-head freshness was not independently established.

## Item status table

“CLOSED” below means the identified source defect is closed. It does not mean the corresponding production act has occurred.

| Adopted item | Status | Verdict | Exact remaining change or closure evidence |
|---|---|---|---|
| **R13-1 — incompatible producer/transport/consumer** | **CLOSED** | ACCEPT | Versioned compact result, chunk reconstruction, root-Struct handling and strict canonical bytes now agree. Actual Cloud Run transport remains an execution check. |
| **R13-2 — state stability through COMMIT** | **PARTLY** | REJECT | New coverage/publication/legacy guards and brief-owned locks close the original schedule. Close **R14-1 and R14-2** before applying 1240. |
| **R13-3 — actual producer provenance** | **PARTLY** | REJECT | Brief ID, producer commit, image and execution binding now exist. Finish validation of the **executed configuration**, particularly command and retry defaults: **R14-3**. |
| **R13-4 — approval order and retry contract** | **CLOSED** | ACCEPT | Reversed histories give the same decision; ambiguity is refused; artifacts identify run and attempt; reconciliation exists. Hard interruption still requires the documented unknown-state procedure. |
| **R13-5 — sealer prohibited capabilities** | **CLOSED** | ACCEPT | Owner-role membership, including NOINHERIT membership, and excessive table/column write capabilities are refused without verification-table exemptions. |
| **R13-6 — inconsistent operational documents** | **PARTLY** | ACCEPT_WITH_AMENDMENTS | **R14-5**. Bootstrap, DSN separation, lifetime and recovery sections improved, but executable contradictions remain. |
| **F-R13-1 — checker rejects actual brief** | **CLOSED** | ACCEPT | Actual emitter and consumer now share the persisted/producer/versioned contract. |
| **F-R13-2 — oversized single-entry transport** | **CLOSED** | ACCEPT | Chunking exists and reconstruction is tested. The documentation-built fixture is correctly disclosed; live delivery remains unproved. |
| **F-R13-3 — stale writer-carried 1241** | **CLOSED** | ACCEPT | Stale 1241 is absent from the writer branch; #2949 is the sole carrier. Correct the ineffective runbook tree-check command under **R14-5**. |
| **F-R13-4 — verifier attribution** | **CLOSED** | ACCEPT | Receipt validation explicitly requires database-attested `produced_by = 'gochara_verifier'`. |
| **F-R13-5 — approval API ordering** | **CLOSED** | ACCEPT | Selection is attempt-bound and order-independent; conflicting/duplicate decisions fail closed. |
| **F-R13-6 — `default=str` canonicalization** | **CLOSED** | ACCEPT | The brief path uses explicit canonical serialization; unsupported values are refused. |
| **F-R13-7 — ten documentation corrections** | **PARTLY** | ACCEPT_WITH_AMENDMENTS | Several are fixed; current approval grammar, transport prose, receipt description and all-NULL sentence still disagree. **R14-5** enumerates the residues. |
| **F-R13-8 — operational prerequisites/self-check** | **PARTLY** | ACCEPT_WITH_AMENDMENTS | Own-checkout verification is implemented and its lock recomputes correctly. Correct IAM/readback and dependency-proof instructions under **R14-5**; discharge the live prerequisites. The newly found isolation defect is **R14-4**. |
| **F-R13-9 — full-generation cost** | **PARTLY** | ACCEPT_WITH_AMENDMENTS | Synthetic 26-class density measurements are useful. Repair the stale end-to-end benchmark input, then record actual candidate counts and costs before approval/seal: **R14-6**. |

## Migrations table

I independently recomputed the ten rehearsal-file hashes against the integration ref. The protected five match the packet.

| Migration | SHA-256 | Assessment |
|---|---|---|
| **1204** | `a0b267f7ef6002a1997c30d34595ec3b86147ca617bf70ef8a05de55b8407ca1` | ACCEPT at source |
| **1206** | `941c79f59f2d3d3125dc5ca680430d4a91a7dcddb53fc6daa9a9da8819e410d7` | ACCEPT at source, including the revised builder verification grant |
| **1232** | `f2ef6406604b819d5f443e32c1e70914f2337ead8867f12e0aecd96d13f1ec44` | ACCEPT at source |
| **1233** | `958b911703eee3528e1db75624984020964b8d31fe3fe286d64071368bd5a705` | ACCEPT at source |
| **1240** | `af70ab4197913e1fd52cc4d463362a665bfb6c25566db894815c4b0f087abefc` | **REJECT — R14-1, R14-2** |
| **1241 v6**, after the window | `6938d589a44db5308ccec24201092b71c02ee9282b0f0a3152e67e6d0592962e` | ACCEPT for the inspected ACL surface; revalidate against amended 1240 |

**1241 versus the present 1240:** I found no missing grant required by the added producer/receipt columns or boundary triggers. Existing table grants cover the new columns; existing helper grants cover the nested calls. Trigger invocation does not require granting runtime principals general EXECUTE on every trigger function. Do not add broad grants to resolve this review.

The sealer’s permitted writes remain seal/receipt insertion and the intended publication columns. Database CONNECT, schema USAGE and the separately governed L1 reads remain operational prerequisites. Creating a role after a conditional-grant migration does not retroactively grant it privileges; the documented role-before-window, 1241-after-window sequence matters.

The #2952 exhibit at `f4809ba33` does **not** carry the current 1206 and 1240 bytes. Use `440f0e06a` for the final composed-byte claim; retain #2952 as a supporting exhibit.

## The sealing chain

### Reproductions and independently checked evidence

I executed the pinned Python entry points and consumer functions in memory, with database/ephemeris adapters stubbed. This exercised the actual CLI emission and consumer code, but was **not** a database integration run.

The file-free reproduction produced **25 passing checks**, covering:

- CLI stdout → modeled root `jsonPayload` Struct → extractor → checker → execution/envelope binding → approval → seal caller.
- Lost key order, integral numbers represented as doubles, reversed entry arrival and identical duplicate chunks.
- Refusal of missing/conflicting chunks, fractional or boolean indices, unknown transport contracts and unsupported canonical values.
- Wrong producer commit/image/execution, wrong brief ID and wrong run attempt.
- Approval histories in both orders, with duplicate approvals, conflicting decisions, stale decisions and malformed history.
- Receipt-call arguments and rollback on the tested mismatches.

The checked-in golden stdout and log fixture reconstruct identical **17,511-byte** payloads. Its producer revision is the deliberate placeholder `cli-sha`, which the real checker rejects. The composed test explicitly expects that rejection. For the positive chain I supplied a valid full reviewed revision through the actual emitter; the resulting payload was **17,544 bytes**. Thus the golden fixture demonstrates transport shape, not by itself a successful production-shaped approval chain.

Additional exact-function probes reproduced:

- acceptance of a changed execution command;
- acceptance of omitted `maxRetries`;
- acceptance of verifier-SA Key Admin access with zero existing keys;
- `KeyError: 'brief_id'` from the current performance test’s obsolete approval input.

I also independently recomputed all **60 implementation modules** against the writer’s lock. The combined digest matches:

`0e8b451d7085114de7f9a28463a252701a0979498450d9d70898ee2cece47aac`

### Enforcement boundaries

| Layer | Enforced | Not established by that layer |
|---|---|---|
| **Database** | Attested brief manifest/state/login/time; latest brief; verifier login; receipt brief ID, execution and producer-commit equality; first-seal/receipt relationship; append-only receipt; chart locking for the inspected mutation paths | Authentic Cloud Run image/execution, GitHub approval, who operated the shared account, honest computation, or universal permanence while R14-1/R14-2 remain |
| **Verifier/sealer code** | Independent derivation, candidate gate, canonical payload, current-state recomputation, identity checks, own-checkout lock, approval schema and run/attempt matching | Protection against an administrator changing trusted code/configuration, or an authenticated verifier deliberately fabricating its computation |
| **Workflow** | Executed-resource/image binding, current-attempt envelope/artifacts, mechanical approval selection, sealer invocation and reconciliation | Complete executed-template validation until R14-3 is fixed |
| **GitHub configuration** | Required environment reviewer, branch restriction, secret release and bypass settings—**if configured and live-proved as specified** | A second human, or proof that the steward actually inspected the displayed digest |
| **Procedure only / no technical proof** | Steward’s review and report under the owner’s ruling | Attribution beyond the shared login; independent human judgment; the approver’s understanding |

Branch protection can require the PR/check/queue path. The stated ruleset does not itself prove that Codex reviewed a change. Environment approval behavior and bypass settings must be established from configuration and the no-secret proof. [GitHub environment documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)

**Older brief and rerun behavior:**

- A brief superseded by a newer persisted brief is refused even if its digest represents identical state.
- Another execution’s brief cannot silently substitute for the execution named by the workflow envelope and receipt checks.
- A different image digest is refused by workflow binding; the database does not independently authenticate images.
- The lower-level sealer intentionally permits a **still-current older brief** named by a **fresh, matching approval**, with unchanged state and matching producer/sealing commit.
- The workflow is stricter: a seal-only rerun has a new attempt number and lacks that attempt’s brief artifact, so it fails closed. A full rerun must produce its own artifact and approval.

Those rules are coherent as different interface policies. Document them explicitly; neither is a database-enforced age/TTL guarantee.

### Digested tables against their guards

The SQL state digest in `1240:655–688` covers the following. “Frozen” refers to ordinary permitted DML with enabled triggers, not a hostile schema owner.

| Table | Database serialization / guard | After seal |
|---|---|---|
| `ka_gochara_relationship_record` | 1155 chart statement lock and `ka_gochara_chart_write_guard` | **Precision-sync exception remains: R14-1** |
| `ka_gochara_record_prerequisite` | 1155 chart statement lock and chart write guard | Frozen |
| `ka_gochara_contact` | 1153 statement lock for UPDATE/DELETE; row guard locks INSERT too | **INSERT and permitted enrichment remain writable: R14-1** |
| `ka_gochara_eval_window` | 1156 chart statement/write guards | Frozen |
| `ka_gochara_eval_window_record` | 1156 chart statement/write guards | Frozen |
| `ka_gochara_search_path_pin` | 1206 statement lock and search write guard | Frozen |
| `ka_gochara_search_inventory` | 1206 statement lock and search write guard | Frozen |
| `ka_gochara_search_input_snapshot` | 1206 statement lock and search write guard | Frozen |
| `ka_gochara_search_obligation` | 1206 statement lock and search write guard | Frozen |
| `ka_gochara_search_interval` | 1206 statement lock and search write guard | Frozen |
| `ka_gochara_eval_window_verification` | 1240 statement lock and verification guard | Frozen |
| `ka_gochara_search_inventory_verification` | 1206 statement lock and search write guard | Frozen |
| `kala_gochara_coverage` | New 1240 boundary row guard for build partitions | Build rows frozen; on-demand rows excluded |
| `kala_gochara_publication` | New 1240 statement lock and boundary row guard | Identity frozen; status exception is too broad: R14-2 |
| `kala_gochara_contacts` | New boundary row guard, if relation exists at migration time | Governed legacy count protected against ordinary DML |
| `kala_gochara_windows` | Same | Same |

The twelve kernel tables have explicit TRUNCATE refusal. The four newly guarded boundary relations do not acquire equivalent TRUNCATE triggers in this change.

The brief is outside the state-digest table list but controls which attestation is current. Its INSERT trigger now acquires **chart EXCLUSIVE → global SHARED** itself. That fixes reliance on a cooperative Python caller; its post-seal refusal remains vulnerable to R14-2.

**Lock order and deadlocks.** The publication statement trigger correctly addresses the identified publication tuple-lock/chart-lock inversion. The brief trigger follows the existing chart-then-global order. The chart helper rejects incompatible global-exclusive-first acquisition.

This is not a general deadlock-free design. Coverage and legacy UPDATE/DELETE paths still acquire tuple locks before their row trigger requests the chart lock. Another transaction holding the chart lock and then deleting the same row can form a cycle. PostgreSQL aborts a participant; integrity is preserved, but operators need whole-transaction retry after reconciliation. The sealer’s ordinary coverage read does not itself form that particular cycle.

The publication statement trigger scans **all governed publication charts**, including for a legacy-only or zero-row UPDATE. Consequently the comment that legacy writers neither lock nor need helper privileges is too broad once governed rows exist. The current canonical-single-chart restriction bounds this design; test legacy callers and their effective helper privileges, and do not advertise general multi-chart compatibility.

**Supersede, rollback and replay.** A metadata-only supersede retains the seal and its data. A metadata-only rollback can also retain them, but the existing `ledger.rollback()` first deletes coverage at `ledger.py:675`; it therefore fails on a sealed generation under the new guard. The supported sealed-withdrawal path needs explicit definition and tests. Replay does not create another first seal or fabricate a historical receipt. Pre-1240 seals remain exempt from the new first-receipt requirement; that does not imply every historical mutation remains permitted by the new boundary guard.

**Moon exclusion.** The exclusion is honest within the inspected contract: on-demand coverage is omitted from the SQL digest and candidate output identity, and the guard excludes those partition kinds deliberately. OLD and NEW are both examined, so changing a sealed build partition into an on-demand partition does not evade the build guard. This exclusion must remain a named limit on what the seal attests.

**Other write paths and trust limits:**

- `COPY FROM` invokes insertion triggers; it follows the same guards and therefore also exposes the contact hole. [PostgreSQL COPY](https://www.postgresql.org/docs/15/sql-copy.html)
- Row DML triggers do not cover TRUNCATE. Runtime roles lack TRUNCATE in the inspected grant closure; an owner’s TRUNCATE is a separate boundary. [PostgreSQL TRUNCATE](https://www.postgresql.org/docs/15/sql-truncate.html)
- An owner able to disable user triggers can defeat these protections. Runtime owner-role exclusion is therefore material, including NOINHERIT memberships. This arrangement is not owner-proof. [PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/15/sql-altertable.html)
- The `to_regclass` attachment loop skips absent legacy relations. A relation created later receives no guard automatically. Before the window, establish the expected relation/trigger inventory; any future creation must attach the guard before granting writes. 1241’s table-existence/grant checks do not establish trigger presence.

### Capacity and composed rehearsal

The author’s reported 26-class density measurements materially improve the evidence:

| Scale | Obligations / intervals; relationship rows | State digest | Python payload build | Estimated complete seal |
|---|---:|---:|---:|---:|
| ×1 | 3,276 each; 182 | ~0.065 s | ~0.27 s | ~0.7 s |
| ×10 | 32,760 each; 1,820 | ~0.60 s | ~2.6 s | ~6 s |
| ×50 | 163,800 each; 9,100 | ~3.55 s | ~15.3 s | ~35 s |

These are author-reported measurements, not timings I reproduced. The multiplied datasets exercise read cost; they are deliberately not complete, valid independently verified candidates. The full-seal column is an estimate assembled from measured components.

Hash-of-hashes substantially reduces aggregate size and reported backend RSS. It does **not** eliminate PostgreSQL’s field-size bound: the ordered `string_agg` of per-row hashes still grows with row count. The Python path also materializes substantial data. Fresh-backend RSS observations are useful, but are not peak-memory guarantees.

The **15-minute statement timeout** and **2-minute lock timeout** are per-statement controls inside the sealing transaction, not a 15-minute transaction deadline. The workflow’s 30-minute seal limit and reconciliation address a different boundary. Verification’s 7,200-second task limit, 125-minute wait and 150-minute workflow limit are consistent starting limits, not demonstrated full-generation capacity.

**Capacity does not introduce another prerequisite to manufacture a real candidate before the protected window.** After source repairs, these measurements support a controlled first candidate/verification execution. Before approval/seal, record actual class/grain counts, row counts and widths, brief bytes, proxy-path latency, memory and lock duration, with headroom against the configured limits. Repair R14-6 so that measurement is repeatable.

The reported composed result—**307 passed in one run**, plus **43/38 window checks and zero findings**—supports the composition of the inspected schema, grants and application paths under its fixture. Its source includes real verifier/sealer logins, the modeled log transport, actual consumer/wrapper paths and receipt/reconciliation checks.

It does **not** establish Cloud Run, Cloud Logging, GitHub configuration or production IAM behavior. It also retains disclosed schema/L1 stand-ins and selected derivation adapters. It neither tests the post-seal contact append identified here nor makes the obsolete performance invocation pass. I verified the byte alignment and inspected the test paths; I did not rerun that PostgreSQL suite.

## New findings

### R14-1 — Digested contacts remain mutable after sealing

**P1. Blocks final 1240, (a) and (c).**

The new migration asserts that the twelve kernel tables already refuse sealed writes. That assertion is false for contacts.

[1153, `ka_gochara_contact_guard`, lines 1115–1179](https://github.com/Marsys-Technologies/Madhav/blob/df65685d0/platform/migrations/1153_gochara_sky_event_substrate.sql#L1115) checks sealing on DELETE, but its INSERT/UPDATE branch takes the chart lock and proceeds without a sealed-generation test. Migration 1216 grants `data_plane_builder` INSERT on this table at line 96.

The source-level late-write schedule is:

1. Prepare a valid contact identity and identical solved reading in another unsealed governed generation before the brief.
2. The sealer takes chart/global locks, validates and writes publication/seal/receipt, then executes **`SET CONSTRAINTS ALL IMMEDIATE`**.
3. The builder INSERTs that contact into `5.0`; its trigger waits for the chart lock.
4. The sealer COMMITs.
5. The builder wakes. The INSERT branch performs no sealed check; identical cross-generation values satisfy N6. The INSERT can commit.
6. The receipt remains, but the digested contact set has changed.

The write no longer slips **before** the sealer’s COMMIT. It violates the equally necessary refusal **after** COMMIT.

There is also an enrichment path: ordinary enabled-trigger contact enrichment can change digested fields and invoke relationship precision propagation. `1155:453–455` deliberately permits sealed `precision_sync`; `1155:840–864` implements that propagation. This is distinct from an administrator disabling triggers.

**Closing change:** add the milestone’s sealed-state refusal to contact INSERT/enrichment and relationship precision mutation in the unapplied 1240, with deliberate historical scope. Add real-login/two-connection tests for the exact immediate-constraint schedule, post-seal contact append and precision propagation, plus a guard-disabled mutation test. Preserve and test legitimate pre-1240/replay behavior. Refresh hashes and the full composed rehearsal.

### R14-2 — A sealed manifest can become a candidate again

**P2, blocking because its repair changes 1240. Blocks (a) and (c).**

[1240:938–940](https://github.com/Marsys-Technologies/Madhav/blob/df65685d0/platform/migrations/1240_gochara_window_verification_gate.sql#L938) permits any publication UPDATE whose differences are confined to `status` and `superseded_at`. It does not limit the transition to withdrawal states.

The publication CHECK permits `candidate`, and the builder has publication UPDATE. Thus a sealed `published` manifest can return to `candidate`.

[1240:733–752](https://github.com/Marsys-Technologies/Madhav/blob/df65685d0/platform/migrations/1240_gochara_window_verification_gate.sql#L733) then permits another brief: the attest trigger checks candidate status but never independently checks whether a generation seal exists. The normal verification precondition is insufficient because direct brief insertion—and the separate brief path—must be protected by SQL.

This can change the latest persisted brief after the receipt was established. It also disproves the trigger comment that status alone guarantees post-seal refusal.

**Closing change:** whitelist the intended sealed lifecycle transitions; forbid return to `candidate`; independently refuse brief insertion whenever the generation is sealed. Define/test metadata-only withdrawal of sealed generations, retaining their attested rows. Reconcile that behavior with `ledger.rollback():665–680`, whose deletion-first implementation currently fails for a sealed generation.

### R14-3 — Executed-resource validation is incomplete

**P2. Blocks (c)’s workflow.**

The pinned [execution checker, lines 59–96](https://github.com/Marsys-Technologies/Madhav/blob/8a71fde50/platform/scripts/gochara_seal_execution_check.py#L59) accepts:

- a changed `containers[0].command`, which it never examines;
- absent `maxRetries`, because line 90 substitutes zero.

Both acceptances were reproduced against the actual function. Cloud Run documents a default of **three** retries when this setting is unspecified. [Cloud Run TaskSpec](https://docs.cloud.google.com/run/docs/reference/rest/v1/TaskSpec)

The checker also limits its secret inspection to environment `secretKeyRef` entries; it is not a complete check of credential-bearing mounts or unexpected environment configuration. #2976’s strict deployment-time readback does not prove that a later execution used the same complete template.

**Closing change:** share a strict validator between deployment and executed-resource checks. Require the expected entry point, explicit zero retries, expected arguments/environment and permitted credential surfaces. Add changed-command, omitted-retry, extra-environment and secret-volume mutations. Validate the actual returned execution representation.

### R14-4 — Isolation preflight ignores verifier key-creation capability

**P1. Blocks acceptance of #2961 and credential/isolation preparation.**

[The verifier policy check, lines 450–464](https://github.com/Marsys-Technologies/Madhav/blob/84331f704/platform/scripts/data-plane-secret-isolation-preflight.ts#L450) checks that no user-managed key exists, then filters bindings through `grantsImpersonation`.

Its permission set at lines 33–37 omits `iam.serviceAccountKeys.create`. The inherited-policy check at lines 495–512 uses the same filter.

I executed the pinned TypeScript function with:

- the expected runtime/secret configuration;
- the permitted deployment `serviceAccountUser` binding;
- **zero current keys**;
- an additional `roles/iam.serviceAccountKeyAdmin` binding for an unexpected principal.

**The check passed.** That role permits creating credentials for the verifier identity. This is a capability defect; I did not find or claim such a binding in production. [IAM roles and permissions](https://docs.cloud.google.com/iam/docs/roles-permissions/iam), [service-account security guidance](https://docs.cloud.google.com/iam/docs/best-practices-service-accounts)

**Closing change:** enforce the intended exact verifier-SA policy for each provisioning phase, and account for inherited key-creation/key-upload and relevant policy-rewrite capabilities outside the explicitly trusted control-plane exceptions. Alternatively, a claimed organization-policy prohibition must itself be read and asserted. Add zero-existing-key/Key-Admin and inherited-binding negative tests.

### R14-5 — The runbook is still not one consistent executable document

**P2. Blocks the affected acts; not all entries below are independent source blockers.**

Here **RB** means `00_ARCHITECTURE/briefs/pravaha/runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md` at `50b871cef`.

| File and line | Remaining contradiction / exact correction |
|---|---|
| **RB:73–76** | Act 3 creates the verifier SA but never performs the required `roles/cloudsql.client` grant. Add the scoped grant, readback and compensation for a newly added binding. §5.4:204 naming “Cloud SQL access” is not an executable grant step. |
| **RB:125–129** | Act 2a is now verification of the combined act-1 run, but still requires the role to be absent. Replace that precondition with the combined-run result; describe `PASSWORD NULL` evidence consistently. |
| **RB:153,157,236** | Unconditional compensation/rollback language contradicts the acknowledged SIGKILL, runner-loss and lost-acknowledgement cases. Say “verified compensation” only when its evidence exists; otherwise classify and reconcile unknown state. |
| **RB:178–180** | The current predefined execution-with-overrides role includes cancellation; the proposed two-permission fallback does not. Neither statement inventories the read rights used to describe/poll jobs and executions. List required effective permissions, distinguish pre-existing rights from added grants, and test execution/read/cancel. [Cloud Run IAM roles](https://docs.cloud.google.com/iam/docs/roles-permissions/run) |
| **RB:187** | P-SC still says the own-checkout check is requested/not implemented, and describes image-tag equality. Replace with the landed pre-DB lock check and immutable-image/producer bindings. |
| **RB:189** | P-REQ claims dependency installation is proved by the live-gate dry run. #2981 does not check out/install/import the sealing code. Name a separate dependency smoke or the actual sealing-job install check. |
| **RB:212** | `git ls-tree origin/main platform/migrations \| grep 1241` does not recurse. Use recursive name-only listing against the frozen ref and check the exact 1241 path. |
| **RB:227** | The approval example omits mandatory `brief-id`; following it produces a refused approval. Use the current complete grammar. |
| **RB:239** | `--brief-chunks` does not exist. Chunking is automatic; the configurable flag is `--brief-chunk-bytes`. Replace the obsolete flag and compact-result description with ST-WIRE-4. |
| **RB:240** | The ~0.7/~35-second totals are described as measured complete transactions; they are estimates. Distinguish synthetic density measurements from actual candidate measurement and state precisely whether the first brief may supply that measurement before approval. |
| **RB:246–247** | “Passwords generated inside the run” and verifier memory lasting only seconds contradict the staging process and persistent secret/database state. Make the correct five-place account at **192–198** authoritative throughout. |
| **`design/SEAL_APPROVAL_PAYLOAD_v1_2.md:24–31`** | Receipt signature omits `brief_id` and `producer_execution_id`; SQL-enforcement prose omits the new producer-commit/execution predicates. Update both. |
| **`reviews/REVIEW_REQUEST_A5_5_GATE_v1_16.md:42–52`** | Closure rows retain intermediate heads and pending/not-reviewed descriptions beside the final-head statement. Refresh them or label them explicitly historical. |
| **Packet:33–35; kernel `seal_brief.py:294–300`** | The adopted all-NULL disclosure sentence still differs from the emitted “no numerical result exists” sentence. Close F-R13-7(j) with one exact, scoped statement. |
| **`runbooks/PROTECTED_WINDOW_REHEARSAL_PLAN_v1_0.md:41,79–80`** | S3c still says only 1233/all four after a failure although 1240 follows; O4 retains closed design work; O5 omits 1240 from the receipt list. Update to the five-file window. |

The socket-form verifier DSN versus loopback sealer DSN is now correctly separated, and #2963 refuses the socket-form sealer input. The five-place credential lifetime and explicit unknown-state inventory are also improvements. The contradictions elsewhere must not override those corrected sections.

### R14-6 — The current end-to-end cost probe cannot run as written

**P2. Blocks the claimed repeatable end-to-end capacity check before sealing; does not independently block the window.**

At [performance script:163–188](https://github.com/Marsys-Technologies/Madhav/blob/df65685d0/platform/python-sidecar/tests/l3/gochara/perf_a53_seal_cost.py#L163), `_brief_as_verifier` returns the persisted producer identity, but the test retains only its digest. It calls `execute_seal` with an approval missing `brief_id` and `producer_execution_id`.

The current caller therefore raises **`KeyError: 'brief_id'`**, reproduced with that approval shape. The density/read-cost measurements remain useful; this defect does not invalidate them retrospectively.

**Closing change:** construct the current approval contract from the returned brief identity, rerun the focused end-to-end probe at the final head, and record its actual phase counts/timings. Correct the “no field-size limit” hash-of-hashes wording and distinguish estimated complete-seal cost from measured cost.

## Ranked amendments

| Rank | Closing work | Blocks |
|---|---|---|
| **1 — R14-1** | Freeze every digested contact/precision mutation after seal; real-login late-write tests and mutation test | Final 1240; **(a), (c)** |
| **2 — R14-2** | Constrain sealed lifecycle transitions; refuse any post-seal brief; define/test sealed withdrawal | Final 1240; **(a), (c)** |
| **3 — R14-4** | Close verifier key-creation/policy capability gap; exact-policy and inherited-capability tests | Credential/isolation preparation; **(c)** |
| **4 — R14-3** | Validate complete executed entry point/retry/credential template | First approved sealing workflow; **(c)** |
| **5 — R14-5** | Publish one consistent runbook/design/packet with executable commands and accurate recovery claims | Affected pre-window and post-window acts |
| **6 — R14-6** | Repair benchmark approval; record final-head and actual-count capacity evidence | First seal approval; **not independently (a)** |

After source closure, the ordered operational acts are:

1. **PRE-WINDOW:** freeze the corrected combined bytes; regenerate hashes; rerun the new attacks, full composed suite and both window modes. Establish expected tables/enabled triggers, routine predecessors and 1206’s unapplied status.
2. **PRE-WINDOW:** at the already governed sitting boundary, land corrected #2961 and #2963. Perform acts **3 → 10 → 4 → 11**, including the explicit verifier Cloud SQL grant and effective IAM readback.
3. **PRE-WINDOW:** perform combined **1 + 2a**. Verify both roles, verifier secret version, memberships/ownership and password-null sealer state. Remove act 11 after every terminal outcome; inventory unknown state after ambiguous outcomes.
4. **PRE-WINDOW:** configure act **5** and run #2981’s no-secret proof: protected-branch waiting, unprotected-branch refusal, steward approval under the owner’s account, continuation and captured approval-history shape.
5. **PRE-WINDOW:** merge the protected train without 1241 and without an intervening routine deployment. Reconfirm exact bytes and prerequisites. **Act 9 remains the owner’s personal dispatch** of `1204 → 1206 → 1232 → 1233 → 1240`.
6. **POST-WINDOW:** apply **1241 / act 8** through the ordinary path; verify both principals were found and exact ACL closure. Establish CONNECT/schema/L1 reads and builder prerequisites.
7. **POST-WINDOW:** perform **2b** behind the proven gate; verify activation and staging-secret deletion. Deploy **6** by digest from the same final commit used for #2975, then perform read-only bootstrap **6b**.
8. **POST-WINDOW:** prove act **12** using actual workflow-identity positive and negative log-view reads. Establish effective execute/override/read/cancel rights for **13**, and proxy rights for **14**.
9. **POST-WINDOW:** build the held all-NULL candidate, independently verify all required grains after the last build, and measure actual counts/costs. Capture the first real brief’s logs and executed resource; compare their representation with the modeled contract before approving.
10. **POST-WINDOW:** run brief → exact digest/run/attempt/brief-ID approval → seal → reconciliation. Record the persisted brief/execution/commit, publication, seal and receipt. Complete specified temporary-resource cleanup; do not mistake IAM expiry or run completion for password expiry.

The following checks require actual executions or live configuration and are **operational preconditions**, not substitutes for source repairs:

| Checkpoint | Required observation |
|---|---|
| GitHub gate | Actual waiting/refusal/approval behavior and returned review-history fields |
| Cloud SQL provisioning | Actual role attributes, authentication, ACL/RLS behavior and verified compensation or unknown-state inventory |
| Verification job bootstrap | Imports, ephemeris assets, socket connection, runtime identity and terminal execution/log evidence |
| Log access | Positive result through the narrow view and negative result for unrelated resources using the actual workflow identity |
| First complete verification | Every required class/grain verified after the last build, with genuine runner identities and no omitted subset |
| First real brief | Actual root JSON shape, number representation, execution-name form, chunk delivery/reconstruction and returned execution configuration |
| Real capacity | Candidate counts/widths, brief size, runtime, memory and lock duration on the deployed and proxy paths |
| Seal outcome | Database publication/seal/receipt agreement; reconciliation after any lost acknowledgement or cancellation |
| Cleanup | Verified staging-secret and temporary-IAM removal; explicit treatment of lasting credentials |

## Step lines

- **(a) BLOCKED BY R14-1 and R14-2, affected R14-4/R14-5 pre-window preparation, refreshed final-byte rehearsal and the listed operational prerequisites.**
- **(b) UNBLOCKED.** The merged registry binding is present in the inspected source; this is not a fresh production-state attestation.
- **(c) BLOCKED BY R14-1, R14-2, R14-3 and R14-4; R14-5/R14-6 must close before their affected acts, followed by the real provisioning, verification, approval and seal receipts.**
- **(d) BLOCKED BY S1-REQ-EPHEMERIS and the uncompleted Stage-1/Stage-2 freezes.** #2923’s reviewed diagnostic tooling remains acceptable.

For **(d) only**, the inspected tooling retains the `4.1` diagnostic boundary, typed frozen inputs, live input reconciliation and input-digest binding. It does not authorize `5.0` measurement or numerical activation.

`measurement/STAGE1_FREEZE_PREP_4_1_v1_0.md:42` still requires the shared ephemeris identity: opened `.se1` hashes, library version/artifact hash, platform and series-probe coverage for **every consumed body including the Moon**, over the consumed horizon ±1 day. A backend-only probe is insufficient. The freeze remains a draft with placeholders. At line 41, **T-honesty remains UNVERIFIABLE**, so `4.1` remains diagnostic and is not flip-eligible regardless of other measured endpoints.

## What I could not verify

- No PostgreSQL integration run was performed. The concurrent SQL schedules and post-seal paths above are source-level deductions requiring the specified real-login regressions.
- I did not independently reproduce the author’s 307-test run, 43/38 window runs or performance timings.
- No production database, principal, credential, IAM policy, GitHub environment, Cloud Run deployment or live execution was inspected or changed.
- The Cloud Logging fixture is modeled from documentation, not captured execution evidence.
- No actual candidate verification, approval, seal, receipt, measurement freeze or numerical activation occurred during this review.
- No file was created or edited, and no git write command was run.