---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.14"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "e65c60bd2 (campaign/pravaha)"
reviewed_heads:
  - {ref: "campaign/pravaha", head: "e65c60bd24a4da4ec44ced2e2d652a35cec27a5d"}
  - {ref: "origin/main — initial diff baseline", head: "75dbfd2bc399ef38d4737828562ffa81cf29fce9"}
  - {ref: "origin/main — subsequently observed diff baseline", head: "411c0549195ec761303133c36900fc8a0b66b138"}
  - {ref: "origin/pravaha/a53-am5-inventory", head: "2ae229c6f811222550216e2bddfcfac7fdc24d14"}
  - {ref: "writer round-14 comparison", head: "df65685d0b822a14b53270324c2f04a071cb3642"}
  - {pr: 2961, ref: "origin/pravaha/b6-act7-verifier-secret-isolation", head: "a87b3ba79dd905502054a25b8b91c3229a0a04cc"}
  - {pr: 2975, ref: "origin/pravaha/b6-gochara-seal-workflow", head: "ce4596314d71198fcf681ec96bab26ca08b0ddff"}
  - {pr: 2976, ref: "origin/pravaha/b6-gochara-verification-job-def", head: "a9616a9b4b6d6cbb1f256d7b0fcae77dec9e141b"}
  - {pr: 2981, ref: "origin/pravaha/b6-gochara-seal-gate-proof", head: "c3e16405f1bff0ed0d7ff3f1684f9f806a42af0d"}
  - {pr: 2963, ref: "origin/pravaha/b6-gochara-role-provisioning-oneshot", head: "9bbad986ab755044412354e437de52b37a219ada"}
  - {pr: 2949, ref: "origin/pravaha/b6-1241-verifier-sealer-grants", head: "5e080e9c157e3d97c596b8913c19e06508895682"}
  - {pr: 2867, ref: "origin/pravaha/b6-am5-inventory-migration", head: "e4d31c9ef82aa2e3874cd2095d295622f6756bf6"}
  - {pr: 2919, ref: "origin/pravaha/b6-am21-p1-anchor-1233", head: "728b91501ad5c3b653a6130c7cac792b381871da"}
  - {ref: "origin/pravaha/b6-composed-rehearsal-integration", head: "5525bd619d88665f66604d3d57a6ac17f39ca176"}
  - {pr: 2952, ref: "origin/pravaha/b6-composed-rehearsal", head: "52b6dd38b2109a2a4d960e8e8e4d4502c2fc0154"}
  - {pr: 2923, ref: "origin/pravaha/b6-stage1-candidate-measurement", head: "d52cbea971944454785480398aefa5da568b30f8"}
authority: "Review only; authorizes nothing."
---

## Verdict

**REJECT overall.** R14-1 and R14-2 are closed at source for a governed generation carrying `result_policy`. I found no remaining ordinary-builder route through those two reported SQL escapes.

The sealing chain nevertheless still has source blockers:

1. **R15-1:** inherited custom roles that can rewrite project/folder/organization IAM policy pass the isolation check.
2. **R15-2:** the deployment readback rejects the documented—and locally SDK-serialized—`timeoutSeconds` representation.
3. **R15-3:** secret references are checked by alias/name without validating their resolved resource; meanwhile the isolation preflight parses the real alias annotation using the wrong format.
4. **R15-5:** the operative documents still disagree, and W5 cannot establish the trigger coverage it claims.
5. **R15-6:** the first-seal input-stability rule and promised natal-tier disclosure are unfinished.

**This is not yet a case where only operational acts and execution receipts remain.**

The approval remains a steward AI-session action under the owner’s account. It is **not an independent human check**. Numerical activation remains disabled.

| Reviewed item | Verdict | Reason |
|---|---|---|
| Writer and 1240 | **ACCEPT_WITH_AMENDMENTS** | Reported contact/lifecycle escapes closed; historical scope, owner-TRUNCATE qualification, disclosure and evidence amendments below |
| #2961 | **REJECT** | R15-1 and R15-3 |
| #2975 | **REJECT** | R15-3; shared contract needs the R15-2 repair carried identically |
| #2976 | **REJECT** | R15-2 and R15-3 |
| #2981 | **ACCEPT** at source | Appropriate no-secret gate proof; actual gate behavior unobserved |
| #2963 | **ACCEPT** at source | Same reviewed head; operational provisioning and recovery evidence remain |
| #2949 / 1241 v6 | **ACCEPT** against current 1240 | No new grant defect found; external prerequisites and closure boundaries remain |
| Protected-window composition | **ACCEPT_WITH_AMENDMENTS** | Correct combined hashes; W5 and final merge/rehearsal controls need the amendments below |
| Runbook/design/rehearsal/packet | **ACCEPT_WITH_AMENDMENTS** | R15-5 and R15-6 |
| #2923 measurement tooling | **ACCEPT** at source, measurement only | No new source finding; execution/freeze prerequisites remain |

The frozen review heads remained as supplied. `origin/main` advanced during the review; both observed baselines are recorded above. Findings reference literal frozen commits.

## Item status table

“CLOSED at source” below does not mean independently rerun against PostgreSQL in this review.

| Adopted item | Status | Evidence and exact remainder |
|---|---|---|
| **R14-1 — sealed contacts and precision propagation** | **CLOSED at source** | 1240’s boundary guard takes the chart lock and refuses contact INSERT/UPDATE/DELETE and relationship-record UPDATE after a regime seal. The other-generation contact preparation now exercises the original schedule. Retain final-byte real-login race evidence; historical scope is expressly narrower than universal immutability. |
| **R14-2 — lifecycle and post-seal brief** | **CLOSED at source** | Sealed publication updates use a whitelist; brief INSERT checks the seal row directly; sealed rollback is metadata-only. Replace the fabricated test assertion and complete the lifecycle/upgrade evidence described below. |
| **R14-3 — changed command and omitted retries** | **CLOSED for the reported defects** | Exact-function probes now refuse both. The shared validator is byte-identical. New defects R15-2/R15-3 still prevent accepting the overall job contract. |
| **R14-4 — Key Admin with zero keys** | **PARTLY** | Exact zero-key Key Admin reproduction now refuses. Custom ancestor-policy rewrite permissions still pass: R15-1. Add those permissions and corresponding scoped tests; distinguish provisioning phases explicitly. |
| **R14-5 — one executable document set** | **PARTLY** | The ten steps and checkpoint table are reproduced literally. W5, stale guard descriptions, commented-out shell failure handling, capacity wording and log-access proof remain: R15-5. |
| **R14-6 — broken performance approval shape** | **CLOSED for the code defect** | File-free execution of the actual `execute_seal` function reproduces the old `KeyError: 'brief_id'`; the new probe’s approval reaches the sealing call with both required fields. This is not an end-to-end database timing. Actual-count capacity remains open. |
| **F-R14-1 — exact all-NULL disclosure** | **CLOSED** | `seal_brief.py:294–297` emits the promised §R13b sentence. The implementation lock matches. The separately promised single-tier disclosure is still absent: R15-6. |
| **F-R14-2 — document/code contradictions** | **PARTLY** | Receipt signature, producer binding, fresh/reuse explanation, command flags and dependency smoke improved. Operative contradictions remain under R15-5. |
| **F-R14-3 — publication statement-lock effects** | **PARTLY** | SQL comments now acknowledge the effects; W1/W2 are present. Finish the effective-writer/isolation audit and remove the operative assertion that 1240 was not edited. |
| **F-R14-4 — legacy TRUNCATE/statement-lock residue** | **PARTLY** | Conditional TRUNCATE guards exist; ordinary roles have no TRUNCATE grant. The condition is unsafe as a general owner-maintenance claim under an old Repeatable Read snapshot: R15-4. Statement-lock residue remains disclosed. |
| **F-R14-5 — fresh versus reuse** | **CLOSED** | Runbook §6, design §2 and `parse_approval` distinguish workflow-fresh briefs from lower-level reuse; cancellation must be confirmed terminal before retry. |
| **F-R14-6 — capacity** | **PARTLY** | Synthetic read-cost evidence and a reported one-class end-to-end seal exist. A valid full candidate at actual counts, including build and proxy-path seal cost, remains unmeasured. Correct estimated-versus-measured labels. |
| **F-R14-7 — login twice, hand zero times** | **CLOSED** | Design line 40 and the operative approval explanation state the limitation explicitly. |

## Migrations table

I independently hashed the files. All ten entries in `EXPECTED_WINDOW_SHA256.txt` match the writer, integration ref and exhibit.

| Migration | SHA-256 | Assessment |
|---|---|---|
| 1204 | `a0b267f7ef6002a1997c30d34595ec3b86147ca617bf70ef8a05de55b8407ca1` | ACCEPT |
| 1206, final PC-4 version | `941c79f59f2d3d3125dc5ca680430d4a91a7dcddb53fc6daa9a9da8819e410d7` | ACCEPT; preserve removal of builder verification writes and the candidate-rebuild cascade |
| 1232 | `f2ef6406604b819d5f443e32c1e70914f2337ead8867f12e0aecd96d13f1ec44` | ACCEPT |
| 1233 | `958b911703eee3528e1db75624984020964b8d31fe3fe286d64071368bd5a705` | ACCEPT; existing-P1-row refusal remains a prerequisite |
| 1240 | `9c9f113a97ac864d3a1908fb94a87df517b1d77616bf1e4e956c81f17df1a893` | ACCEPT_WITH_AMENDMENTS; ordinary-role fixes sound at source; R15-4 qualification |
| 1241 v6 | `6938d589a44db5308ccec24201092b71c02ee9282b0f0a3152e67e6d0592962e` | ACCEPT against current 1240; apply after the window |

**Merge qualification:** #2919’s branch still carries older 1206 bytes, hash `1ec9008f367820298c0973b20ef51fed5c789ea46ac6a044fadd4cfd584dcb92`. Those bytes retain the builder’s verification-table grant and omit the newer cascade. The composed result correctly carries `941c79…`. The final merge must preserve that result; accepting branch names is insufficient.

1241 remains the sole carrier of its file. It adds no objects or SECURITY DEFINER functions. Its closure checks effective table/column privileges and `ka_gochara_*` function execution for the verifier and sealer, including prohibited privileges.

Its limits remain material:

- Missing roles produce warnings, not deferred grants. Both principals must be reported present.
- L1 SELECT permissions are deliberately outside its specification.
- CONNECT, schema access, role attributes, memberships, ownership and RLS require their separate checks.
- Its closure does not inventory every view, sequence, schema privilege or unrelated SECURITY DEFINER function in the database.
- Builder prerequisites include the applicable 1216/1220/1234/1242 grants; 1241 is not the complete builder ACL specification.

The new boundary triggers do not themselves require granting their trigger functions to runtime callers. Their invoked helpers and relation reads must remain available.

## Post-seal immutability matrix

This is a source-level matrix for the reviewed schema, enabled triggers, ordinary provisioned roles, and a generation carrying `result_policy`.

Notation:

- **C→R:** acquire the transaction-scoped chart lock, then refuse the sealed generation. A concurrent writer waits through the sealer’s commit and checks the seal afterward.
- **S+C→R:** a BEFORE STATEMENT chart lock precedes tuple processing; the row guard also enforces refusal.
- **X:** unconditional refusal; waiting for the sealer is unnecessary.
- **G:** global-exclusive lock, conflicting with the sealer’s global-shared lock.
- **T:** `ka_gochara_refuse_truncate()` through the named table’s no-truncate trigger.
- **CT:** conditional boundary TRUNCATE guard; AccessExclusive table locking supplies serialization at READ COMMITTED. See R15-4.
- **—:** denied by the reviewed role grants.

The last column identifies granted mutation surfaces **before** seal. All other INSERT/UPDATE/DELETE/TRUNCATE operations for those roles are denied by ACL. Granted operations remain subject to the preceding trigger columns.

### Digest and candidate-boundary relations

| Relation | INSERT | UPDATE | DELETE | TRUNCATE | Builder / verifier / sealer mutation surface |
|---|---|---|---|---|---|
| `ka_gochara_relationship_record` | C→R, `ka_gochara_rr_1_write_guard` | S+C→R, `ka_gochara_rr_0_statement_lock` plus new boundary regime guard | S+C→R, RR guards | T, `ka_gochara_rr_no_truncate` | B: I, D, U(`admission_state`); V: —; S: — |
| `ka_gochara_record_prerequisite` | C→R, `ka_gochara_rpr_1_write_guard` | S+C→R, `result_only` | S+C→R, including cascades | T, `ka_gochara_rpr_no_truncate` | B: I, U(`result`), parent-driven cascade; V/S: — |
| `ka_gochara_contact` | C→R, boundary regime guard before old contact guard | S+C→R, contact statement lock plus boundary guard | S+C→R, both guard families | T, `ka_gochara_contact_no_truncate` | B: I,D; V/S: —. Direct enrichment UPDATE is not granted to the ordinary builder |
| `ka_gochara_eval_window` | C→R, `ka_gochara_ew_1_write_guard` | S+C→R | S+C→R | T, `ka_gochara_ew_no_truncate` | B: I,D; V/S: — |
| `ka_gochara_eval_window_record` | C→R, `ka_gochara_ewr_1_write_guard` | Statement lock, then `no_update` refusal | S+C→R | T, `ka_gochara_ewr_no_truncate` | B: I, parent-driven cascade; V/S: — |
| `ka_gochara_search_path_pin` | C→R, search guard; sealed-path check | Statement lock, then immutable-update refusal | S+C→R | T | B: I,D; V/S: — |
| `ka_gochara_search_inventory` | C→R, search guard | S+C→R; pre-seal finalization columns only | S+C→R | T | B: I,D, specified finalization U; V/S: — |
| `ka_gochara_search_input_snapshot` | C→R, search guard | Statement lock, then immutable-update refusal | S+C→R | T | B: I,D; V/S: — |
| `ka_gochara_search_obligation` | C→R, search guard; sealed-path check | Statement lock, then immutable-update refusal | S+C→R | T | B: I,D; V/S: — |
| `ka_gochara_search_interval` | C→R, search guard | Statement lock, then immutable-update refusal | S+C→R | T | B: I,D; V/S: — |
| `ka_gochara_search_inventory_verification` | C→R, search guard | Statement lock, then immutable-update refusal | S+C→R, including header cascade | T | B: no direct write; V: I; S: — |
| `ka_gochara_eval_window_verification` | C→R, `ka_gochara_ewv_1_write_guard` | Statement lock, then refusal | S+C→R | T, `ka_gochara_ewv_no_truncate` | B: —; V: I,D; S: — |
| `kala_gochara_coverage`, build kinds | C→R, boundary guard | C→R, both OLD and NEW checked | C→R | CT | B: I,D; V/S: — |
| `kala_gochara_publication` | C→R, boundary guard | Statement lock plus identity freeze and lifecycle whitelist | S+C→R | CT | B: I,U; V: —; S: U only four publication columns |
| `kala_gochara_contacts` | C→R, boundary guard | C→R | C→R | CT | B: I,D; V/S: — |
| `kala_gochara_windows` | C→R, boundary guard | C→R | C→R | CT | B: I,U,D under 1237; V/S: — |

For all six search relations, the exact trigger names are `<table>_0_statement_lock`, `<table>_1_write_guard`, and `<table>_no_truncate`; the row function is `ka_gochara_search_write_guard()`.

For the four `kala_` boundary relations, the row and truncate triggers are `ka_gochara_boundary_1_write_guard` and `ka_gochara_boundary_2_no_truncate`. Publication additionally has `ka_gochara_boundary_0_statement_lock`.

These protections cover all twelve SQL state-digest tables, build coverage, manifest identity and the required absence of legacy projection rows. Sources: [1240 boundary guards](https://github.com/Marsys-Technologies/Madhav/blob/2ae229c6f/platform/migrations/1240_gochara_window_verification_gate.sql#L951), [1206 search guards](https://github.com/Marsys-Technologies/Madhav/blob/2ae229c6f/platform/migrations/1206_gochara_search_inventory_completeness.sql#L576).

### Brief, seal and receipt

| Relation | INSERT | UPDATE | DELETE | TRUNCATE | Ordinary-role result |
|---|---|---|---|---|---|
| `ka_gochara_seal_brief` | `ka_gochara_seal_brief_attest`: chart-exclusive → global-shared → unconditional seal-row existence refusal | X, `ka_gochara_seal_brief_no_change` | X, same | X, `ka_gochara_seal_brief_no_truncate` | Only V has I; post-seal insertion refused |
| `ka_gochara_generation_seal` | Chart lock plus 1153, 1206 and 1240 seal guards; existing key cannot create a second seal | X, `ka_gochara_generation_seal_write_guard` | X, same | T | Only S has I; published replay can be a no-op |
| `ka_gochara_seal_approval` | Attestation, unique key, deferred seal FK, first-seal and current-brief checks | X, `ka_gochara_seal_approval_no_change` | X, same | X, `ka_gochara_seal_approval_no_truncate` | Only S has I; existing receipt cannot be replaced |

Receipt INSERT does **not** independently acquire the chart lock. The reviewed sealing flow already holds it; direct receipt insertion is constrained by the unique key, reciprocal deferred checks and immutable seal/brief state. It is inaccurate to describe every receipt operation as independently chart-serialized.

A first seal cannot commit without its receipt. A receipt must name the current verifier-persisted brief, matching manifest, digest, brief ID, execution and producer commit. SQL does not authenticate a GitHub approval or independently compute the claimed payload hash.

### Referenced, global and external relations

These require a different claim: referenced rows remain immutable, but the entire global catalogue is not frozen forever.

| Relation | INSERT | UPDATE | DELETE | TRUNCATE | Effect and role boundary |
|---|---|---|---|---|---|
| `ka_gochara_physical_object` | Chart-context statement trigger; new IDs allowed | X, `_immutable` | X | T | B can append; V/S cannot write. Referenced row cannot be replaced |
| `ka_gochara_contact_identity` | Chart-context and supersession checks; new IDs allowed | X, `_immutable` | X | T | B append only; identity reuse cannot overwrite an existing row |
| `ka_gochara_sky_convention` | Chart-context statement trigger; new conventions allowed | X, `_immutable` | X | T | B append only |
| `ka_gochara_convention_bridge` | Chart-context statement trigger | X, `_immutable` | X | T | B append only; existing bridge immutable |
| `ka_gochara_predicate` | G, `_write_guard` | X through global write guard | X | T | B may add a new version after seal; selected row immutable |
| `ka_gochara_factor` | G, `_write_guard` | X | X | T | Same |
| `ka_gochara_rule_path` | G, `_write_guard` | X | X | T | Same |
| `ka_gochara_rule_path_prerequisite` | Global membership guard; refuses membership added to an already sealed path | X, `ka_gochara_rp_prereq_write_guard` | X | T | New unsealed-path membership may be constructed |
| `ka_gochara_rule_path_soft_factor` | Same, `ka_gochara_rp_soft_factor_sealed_check` | X | X | T | Same |
| `ka_gochara_rule_path_seal` | G, `_write_guard`; new version seals allowed | X | X | T | Census can grow after generation verification; G2 applies |
| `ka_gochara_av_polarity_declaration` | Chart-context statement trigger; new declaration allowed | X, `_write_guard` | X | T | No write granted by the reviewed runtime sets; first candidate consumes none |
| `kala_gochara_convention` | New row allowed; no generation-seal lock | X, `kala_gochara_convention_immutable` | X | No local unconditional TRUNCATE trigger in 1081; FK/dependent guards and ACLs apply | B has I; V/S no write |
| `ka_gochara_sky_event` | Chart-context and supersession checks | Guarded enrichment remains possible with suitable privilege | X, mutation guard | T | Explicitly outside the P1–P4 candidate verification boundary; B’s reviewed grant is INSERT |
| `chart_facts` | No Gochara seal serialization | Same | Same | Same | External L1 producer may change it; V/S require separately managed reads |
| `chart_dashas` | No Gochara seal serialization | Same | Same | Same | Consumed-row digest detects changes when checked; no permanent upstream freeze |
| `_migrations_applied` | No Gochara chart/global lock | Same | Same | Same | V/S have only the specified column reads; migration owner remains outside runtime protection |
| `charts`, `chart_grants` | No Gochara generation freeze | Same | Same | Same | FK/RLS infrastructure, separately governed; no mutation granted by 1241 |
| `bg_transit_rules`, `bg_transit_av_gates` | No protection from the reviewed generation-seal guards | Same | Same | Same | Not consumed by this first candidate; enabling those paths changes the review boundary |

Role/ACL/trigger catalogues are likewise administrator-controlled, not sealed candidate data.

On-demand coverage kinds remain intentionally writable outside build identity. OLD/NEW checking prevents converting a protected build-coverage row into an excluded kind to evade the guard.

### Required edge cases

**Regime key and seal-row attacks.** After a regime seal, removing, replacing, nulling or changing `result_policy` cannot reopen the contact path: publication identity is protected independently of that key. The seal row cannot be updated/deleted/truncated by ordinary roles. The exhibit’s builder/sealer attacks support this source conclusion.

**A seal created before 1240.** Scope is determined by **stored vector shape, not migration chronology**:

- An old seal without `result_policy` retains the old contact INSERT/enrichment and precision-sync behavior.
- An old seal carrying the key receives the new regime refusal after 1240.
- Receipt enforcement is not retroactive.
- Brief INSERT now refuses whenever a seal exists.

The historical test in `test_a53_r14_sealed_contacts.py:90–105` removes the key using `session_replication_role=replica` after sealing. That tests shape-based behavior; it is not, by itself, a chronological pre-1240 upgrade test.

**Lifecycle.** The CHECK permits exactly `candidate`, `published`, `superseded`, `rolled_back`.

| Sealed status | Permitted next status |
|---|---|
| `published` | Same-status no-op, `superseded`, `rolled_back` |
| `superseded` | Same-status no-op only |
| `rolled_back` | Same-status no-op only |
| Artificially pre-existing `candidate` plus seal | Same-status no-op only; no new brief |

Other identity/publication fields must remain identical. Same-status updates cannot change `superseded_at`. `superseded → published` and `rolled_back → candidate` refuse. The sealer cannot update `superseded_at` under 1241.

A second seal row is prevented by the primary key. The helper’s published replay inserts nothing. Superseded/rolled-back generations fail its published-manifest prerequisite rather than becoming a new seal.

**Contact identity across generations, N6.** Reusing an identity in an unsealed generation does not mutate the sealed generation’s row. N6 rejects differing non-NULL solved readings. Contact precision propagation updates only the matching chart/generation/contact records; the new regime guards block both the originating sealed contact update and direct sealed-record precision updates.

**ON CONFLICT, COPY, rules and views.** BEFORE INSERT guards run before conflict handling; an upsert is not a post-seal insertion escape. UPDATE branches remain guarded. `COPY FROM` invokes row triggers. An ordinary role cannot install replacement rules, disable triggers, alter table ownership or create an elevated writer using the reviewed grants. A view routing ordinary DML to these base tables still encounters their guards. Existing privileged definer objects outside this reviewed namespace require the live ownership/privilege inventory; 1241 does not certify their absence.

**Sequences and identity columns.** Identity allocation does not bypass brief attestation. Supplying an explicit identity value cannot insert a post-seal brief. Sequence values are not part of the candidate digest. The builder’s legacy-window sequence USAGE permits advancing that sequence without changing sealed candidate rows; it is not a claim that every database byte is frozen. Verifier/sealer receive no sequence-maintenance grants from 1241.

**Function security.** The reviewed Gochara guard/gate helpers are SECURITY INVOKER and pin `search_path`; candidate relations are schema-qualified. The old convention refusal function performs no relation lookup. No reviewed helper grants ordinary callers an owner-rights route around the guards. Public-schema CREATE and elevated memberships must remain absent.

## New findings

### R15-1 — Custom ancestor-policy writers bypass the isolation model

**P1; blocks isolation/credential preparation.**

In [#2961, lines 53–66](https://github.com/Marsys-Technologies/Madhav/blob/a87b3ba79/platform/scripts/data-plane-secret-isolation-preflight.ts#L53), the resolved permission set includes service-account policy rewrite but omits:

```text
resourcemanager.projects.setIamPolicy
resourcemanager.folders.setIamPolicy
resourcemanager.organizations.setIamPolicy
```

Known predefined IAM-admin role names are caught. A custom role with the equivalent ancestor-policy permission is not. `assertVerifierInheritedControl` skips it at line 495.

I executed the actual TypeScript functions in memory:

| Probe | Result |
|---|---|
| Zero keys, allowed deployer binding | ACCEPT |
| Zero keys plus Key Admin | REFUSE |
| Custom `iam.serviceAccountKeys.create` | REFUSE |
| Custom `iam.serviceAccountKeys.upload` | REFUSE |
| Custom `iam.serviceAccounts.setIamPolicy` | REFUSE |
| Custom project policy writer on the project | **ACCEPT** |
| Custom folder policy writer on the ancestor folder | **ACCEPT** |
| Custom organization policy writer on the ancestor organization | **ACCEPT** |

An ancestor-policy writer can grant a credential-minting role on that ancestor. This is precisely the indirect control the packet claims to exclude. [Google’s IAM policy-change permissions](https://docs.cloud.google.com/iam/docs/granting-changing-revoking-access) support that interpretation.

**Closing change:** include all three ancestor policy-write permissions in the resolved-capability model; test each at its correct ancestor scope, with and without an exact named exception.

Also, the “per phase” validator currently accepts the union of staged and deployable policies on every call: lines 465–467 accept zero bindings even when a deployer is supplied. Add an explicit expected phase, or accurately describe this as a two-shape allow-list and separately enforce the act-10 postcondition.

Canonical Google service-agent exceptions work for their specified project resource and exact role/member pair. Do not replace them with a broad Google-domain exception. Normalize project ID/number resource representations before exception comparison: the current function rejects an otherwise identical allowed service-agent binding under `projects/<number>`.

### R15-2 — Deployment readback rejects the real timeout representation

**P2; blocks act 6 before the first execution.**

[Shared contract line 72](https://github.com/Marsys-Technologies/Madhav/blob/a9616a9b4/platform/scripts/gochara_verification_job_contract.py#L72) compares `task["timeoutSeconds"]` directly with an integer.

Cloud Run v1 represents this field as an **int64 string**. The installed Google SDK’s actual serializer produced:

```json
{"maxRetries": 0, "timeoutSeconds": "7200"}
```

The exact readback function rejected it:

```text
timeoutSeconds is '7200', expected 7200
```

The test fixture uses integer `7200`, hiding the mismatch. This follows the [documented TaskSpec representation](https://docs.cloud.google.com/run/docs/reference/rest/v1/TaskSpec).

**Closing change:** strictly normalize the documented int64 representation, rejecting booleans, fractional/non-finite values and malformed strings. Add SDK/API-shaped fixtures through deployment readback, pre-execution checking and executed-resource checking. Preserve byte identity between both PRs.

The shared contract hash is:

```text
5c9c062adcbe2101eb066024c107eb3605f9d542319cdb7414ca44feb4ec104a
```

### R15-3 — Secret aliases are not resolved, and the preflight parses their format incorrectly

**P1 for the credential-binding claim; conditional execution refusal also present.**

There are two defects.

**First:** [shared contract lines 69–71](https://github.com/Marsys-Technologies/Madhav/blob/ce4596314/platform/scripts/gochara_verification_job_contract.py#L69) validate `secretKeyRef.name`, not the secret resource that name resolves to. The surrounding validators ignore the secret-mapping annotation.

An executed resource retaining the expected name but adding:

```text
run.googleapis.com/secrets:
gochara-verifier-db-url:projects/foreign-project/secrets/another-database
```

was **accepted** by the actual executed-resource checker.

That does not prove access to such a secret exists. It proves the checker does not establish its claimed exact credential binding. Cloud Run explicitly supports these aliases. [SecretKeySelector documentation](https://docs.cloud.google.com/run/docs/reference/rest/v1/Container#SecretKeySelector).

**Second:** [#2961 lines 139–148](https://github.com/Marsys-Technologies/Madhav/blob/a87b3ba79/platform/scripts/data-plane-secret-isolation-preflight.ts#L139) call `JSON.parse` on this annotation. The actual format is comma-separated `alias:projects/.../secrets/...`, as confirmed by the installed SDK’s `secrets_mapping.ParseAnnotation`.

The actual preflight extractor rejected a valid example with:

```text
Cloud Run secrets annotation is not valid JSON.
```

The same-project short-name deployment need not emit this annotation. However, the preflight inventories other services/revisions/jobs too, so an existing legitimate alias-bearing resource can make it refuse.

**Closing change:**

- Parse the documented annotation format in the inventory preflight.
- Resolve aliases to a canonical project-and-secret resource.
- For this job, either explicitly forbid secret remapping annotations or require the resolved resource to equal the intended verifier secret.
- Validate the supported version/key policy and selector fields.
- Test foreign-project aliases, same-project aliases, duplicate/conflicting aliases and the SDK’s normal format.

The missing selector `key` also passes the current validator. The API may reject such a deployment, but the source should not claim a complete strict selector contract while accepting it.

### R15-4 — Conditional TRUNCATE protection depends on snapshot isolation

**P2 hardening; not an independent ordinary-role seal blocker.**

[1240 lines 1009–1018](https://github.com/Marsys-Technologies/Madhav/blob/2ae229c6f/platform/migrations/1240_gochara_window_verification_gate.sql#L1009) inspect rows with `SELECT EXISTS`, without enforcing READ COMMITTED.

At READ COMMITTED, table locking handles the requested arrival race:

- TRUNCATE gets AccessExclusive first: a later INSERT waits until truncation ends.
- INSERT commits first: the guard sees the governed row and refuses.

That reasoning does not cover an older Repeatable Read snapshot. The source-level counterexample is:

1. Maintenance transaction establishes a Repeatable Read snapshot while coverage contains only legacy rows.
2. Another transaction inserts governed coverage and commits; the generation can subsequently seal.
3. Maintenance obtains AccessExclusive and executes TRUNCATE.
4. Its conditional `EXISTS` can still see the old snapshot and miss the governed row.

TRUNCATE removes table contents rather than only snapshot-visible rows. PostgreSQL documents both its AccessExclusive locking and its lack of MVCC safety. [PostgreSQL TRUNCATE](https://www.postgresql.org/docs/15/sql-truncate.html).

**Closing change:** refuse non-READ-COMMITTED execution in this guard, or adopt unconditional refusal. Add the two-connection legacy-only→governed-arrival regression, including Repeatable Read. I did not execute this schedule.

Because builder/verifier/sealer have no TRUNCATE privilege, this is not a new ordinary-runtime escape. If deferred as owner-only hardening, narrow the protection claim explicitly; do not mark the general conditional guarantee proved.

### R15-5 — The document set still fails its executable-consistency claim

**P2; blocks the affected pre-window/post-window acts.**

Paths below are relative to `00_ARCHITECTURE/briefs/pravaha/`, except where stated.

| Location | Remaining problem | Exact correction |
|---|---|---|
| `runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md:65` | Says 1240’s bytes were not edited for the comment | State that they changed and cite current hash |
| Same, `:72` W5 | Inventory excludes eight digest relations while claiming every 1206/1240 trigger is checked | Include every relation/trigger in this review’s matrix and compare against an expected manifest |
| Same, `:72` | No namespace filter; inventory helper checks trigger names, not enabled state, function, events or arguments | Compare schema, relation, trigger, function, event/timing, arguments and enabled mode; missing expected entries must fail |
| Same, `:70` versus `:72` | W3 says missing boundary relation is STOP; W5 says report it | Keep one rule: missing required relation is STOP |
| Same, `:73` | Says TRUNCATE is outside the guard and proposes adding guards that now exist | Describe current conditional guards and R15-4 accurately |
| `design/SEAL_APPROVAL_PAYLOAD_v1_2.md:35` | Repeats “1240 is NOT edited” and obsolete TRUNCATE description | Same correction |
| Runbook `:32` | `|| { … exit 1; }` occurs after `#` and is therefore commented out | Move the comment to a separate line; retain the active checked invocation |
| Runbook `:187` versus checkpoint `:238` | Zero unrelated entries through a filtered view proves the filter, not denial of broader log access | Test the actual workflow identity against a known unrelated resource outside that view and inspect effective inherited permissions |
| Runbook `:245`, `:274–275` | Excludes capacity work from the sequence, then places it before approval and elsewhere before the first brief | One explicit checkpoint: controlled build/verification first; actual counts and disposable-clone seal timing before approval |
| Rehearsal plan `:85` | Calls the table measured while listing an estimated ≈0.7 s seal; says it fits the budgets | Label each measurement versus estimate and remove the unsupported complete-seal conclusion |
| `platform/.…` not applicable; actual `.github/workflows/gochara-seal-approved.yml:28–29` | Calls ≈0.7 s and ≈35 s measured sealing transactions | Correct to estimates; cite the separate reported one-class measurement |
| `platform/python-sidecar/services/gochara_kernel/seal_brief.py:422` | Calls ≈35 s a measured worst case | Correct the comment |
| Upstream decision `:29–30`, `:86` | Fact-ID and daśā-selection overstatements; already answered node question remains open | Apply the code-based qualifications below |

**Ten-step sequence:** I compared the text mechanically. The ten steps and checkpoint table at runbook lines 218–243 are **literal matches** to round 14. The contradictions are elsewhere in the operative set.

**W1–W5 assessment:**

- **W1:** predicate is appropriate for the canonical-chart limitation. Use schema-qualified names and run W3 first. A copyable regex outside a Markdown table is `'^([5-9]|[1-9][0-9]+)[.][0-9]+$'`. Zero rows is the required result.
- **W2:** useful but incomplete. Enumerate effective table **and column** UPDATE/DELETE holders, including inherited privileges and owners. Read role/database settings and the actual operating transaction isolation; `SHOW default_transaction_isolation` alone does not prove callers never override it.
- **W3:** correct relation-presence check; all four required relations must exist.
- **W4:** correct after the role exists; it cannot establish a pre-creation result.
- **W5:** insufficient as written. It omits prerequisites, windows, window memberships, path pins, inventory, snapshots, obligations and intervals. The helper’s booleans are presence hints, not a complete enforcement audit. Its production call also belongs after 1240; before then, the mirror provides the expected baseline.

### R15-6 — First-seal input stability and natal-tier disclosure remain unfinished

**P2; blocks the first seal, not the protected schema window.**

The new SETTLED-1 decision is sensible, but it does not alone guarantee that verification is still current at seal.

- The seal recomputes consumed L1 digests.
- It checks implementation identity.
- It does **not** rederive the live registry census or ephemeris identity.
- L1 writers do not share the Gochara chart lock.

The blanket statement that G1–G5 are only pre-numerical work is therefore too broad.

**Closing change before first seal:**

1. Add the promised natal-input tier disclosure to the digest-bearing brief; regenerate affected goldens and the implementation lock.
2. Adopt an executable input-stability rule from final verification through seal commit.
3. Either implement the proposed seal-time input recheck under the relevant locks, with any necessary 1241 grant changes, or explicitly freeze the relevant upstream/registry/corpus changes for that interval and record the identity readbacks.
4. Require fresh build/verification/brief/approval after any relevant change.

An immutable verifier image helps bind its ephemeris files; it does not establish that every external input remained unchanged.

## Exact-function probes and evidence limits

| Probe | Independent result |
|---|---|
| Changed verification command | REFUSED by shared contract and executed-resource check |
| Omitted `maxRetries` | REFUSED |
| Extra environment variable | REFUSED |
| Secret volume | REFUSED |
| Normal execution metadata/status fields | ACCEPTED |
| `timeoutSeconds: "7200"` | Execution check accepts; deployment readback **refuses** |
| Expected secret alias redirected by annotation | Executed-resource check **accepts** |
| Valid comma-separated secret annotation | Isolation extractor **refuses as invalid JSON** |
| Key Admin with zero keys | REFUSED |
| Custom ancestor policy writer | **ACCEPTED**, all three ancestor types |
| Old performance approval shape | `KeyError: 'brief_id'` reproduced |
| New performance approval shape | Reaches the sealing call with brief ID and execution ID |

The performance probe used the exact `execute_seal` function with dependencies stubbed at the database boundary. It proves argument plumbing, not a successful seal.

The strict unknown-field rule is applied to task/container objects, **not** the entire Job/Execution resource. Consequently, normal top-level status, conditions, timestamps and annotations are not generally rejected. `resources` and `timeoutSeconds` are allowed fields. The confirmed first-deployment problem is the timeout’s **type**, not an unmodeled field.

Conversely, ignoring all annotations is too permissive when an annotation changes secret resolution. Other unmodeled task/container behavior should remain refused until modeled deliberately.

The 60-module implementation digest independently recomputes to:

```text
be181fae4ae0722392394712059ab20d07c395dba89e7098216e9f49799e9e3c
```

The recorded stage digests and lock match.

The reported **344 passed**, and **43/38 rehearsal assertions**, remain author evidence. I verified the relevant bytes and inspected the attacks; I did not independently reproduce those database runs.

Two test qualifications must accompany their interpretation:

- `test_a53_r14_sealed_contacts.py:117–118` manually throws a `CheckViolation` for the `published → published` case. That is not a database assertion. Replace it with a real permitted no-op and real refused transitions for every CHECK value.
- The post-seal enrichment/precision cases include no-op assignments and owner connections. Retain the real-login insertion schedule, but add actual NULL→value enrichment, actual propagation, chronological upgrade, and conditional-TRUNCATE arrival cases where those behaviors are claimed.

## Lock order and liveness

The normal order remains **chart-exclusive → global-shared**. Registry insertion takes global-exclusive. The contact and relationship-record UPDATE/DELETE paths already have statement-level chart locking; the new regime guard does not introduce the originally feared tuple-first cycle on those ordinary paths.

Publication’s statement trigger deliberately locks every chart with a governed publication row before UPDATE/DELETE tuple processing. That prevents the ordinary publication tuple/chart inversion, but also explains W1/W2’s broad operational effects—including statements aimed at legacy rows or matching no rows.

The remaining legacy boundary row guards do not establish universal deadlock freedom. Transactions can hold other tuple/table/advisory locks before reaching the chart guard. Direct `SELECT … FOR UPDATE`, multi-statement transactions and privileged TRUNCATE can produce different lock orders. A blocked builder can retain those earlier locks.

For the reviewed sealing flow:

- `lock_timeout = 2min` and `statement_timeout = 15min` are installed inside the transaction before seal locks.
- Lock timeout, statement cancellation and ordinary database errors abort the transaction.
- Deferred receipt failure rolls back publication and seal with the receipt.
- PostgreSQL deadlock detection can abort a participant; retry requires the whole transaction.
- There is no source path here that intentionally commits half the sealing transaction.

These are **per-statement/per-lock bounds**, not a transaction-wide deadline. They do not bound initial connection establishment, Python work between SQL statements, or a backend left idle in transaction after a stalled/lost client. `seal_job.py:70` supplies no explicit connection timeout, and no idle-in-transaction timeout is installed.

Treat that as a disclosed liveness limitation: add bounded connection and idle-transaction handling if claiming a complete end-to-end bound. Workflow timeout alone is not proof of immediate backend termination. Reconciliation remains necessary after cancellation or lost commit acknowledgement; an `always()` step cannot be guaranteed to finish after runner loss.

## Upstream sequencing and G1–G5

**SETTLED-1 plus the daśā re-pin is the appropriate first-seal milestone.** The inspected first candidate does not consume the stored node-series outputs that motivate SETTLED-2. Before settlement, the authorized scope remains an unsealed disposable/dry-run build and verification.

The code supports the input-pinning claim with these corrections:

1. **Natal positions:** `chart_context.py:48–51` selects the relevant `chart_facts` rows without a tier floor. The snapshot digest covers the full **consumed rows**, excluding `computed_at`; `build_id`, values and verification tier remain included.
2. **Stable fact IDs:** `ga_positions_writer.py:92–99` derives identity from category/subject/key/chart/ayanāṃśa, not build ID. Its rebuild replaces the relevant rows. “Assume fact IDs change” is stale; changed `build_id` still changes the consumed-row digest.
3. **Population scope:** a digest over consumed IDs is not a digest of every possible matching row. An unrelated added row does not necessarily cause drift. A new conflicting value is rejected when the relevant reader reruns.
4. **Daśā constant:** the canonical build pin is in `DASHA_READ_CONTRACT` and therefore in the implementation identity. Changing it requires a new reviewed code identity and fresh candidate/verification.
5. **Daśā coexistence:** `dasha_read.py:42–47` accepts the pinned build while it remains present, even if other builds coexist. It does not refuse merely because *any* other build exists. The subsequent read is restricted to the selected build.

| Gap | Characterization | First all-NULL seal requirement |
|---|---|---|
| **G1 — no automatic sealed-generation staleness monitor** | Correct | Automation may remain deferred. First seal still requires SETTLED-1, re-pin, current checks and an explicit input-stability interval. Later upstream changes require a new generation, not mutation of the sealed one |
| **G2 — registry/ephemeris change after verification** | Correct; code identity is separately checked | **Must be addressed before first seal**, by the implemented recheck or explicit bounded freeze/readback procedure in R15-6 |
| **G3 — no natal tier floor** | Correct; actual current tier/build values are lane-reported, not independently read here | **Disclosure must land before first brief/seal.** Requiring a stronger tier or second derivation is the owner’s pre-numerical decision |
| **G4 — build timing absent** | Correct | Time the all-NULL build before relying on its planned runtime; obtain actual-count verification/brief and disposable-clone seal capacity before approval. No need to manufacture a production candidate before the schema window |
| **G5 — numerical path never run at scale** | Correct | May remain deferred while numerical activation stays disabled |

A sealed snapshot’s permanence and its freshness relative to later upstream data are separate claims. The matrix establishes the former within the ordinary-role boundary; it does not establish perpetual freshness.

## Measurement — step (d) only

#2923 remains diagnostic measurement tooling. Its candidate adapter retains unknown intensities, uses bounds rather than imputing values, and enforces the two-stage freeze. The inspected freeze logic rederives ephemeris coverage requirements and binds actual run inputs.

It does not authorize numerical activation or repair the outstanding governed `4.1` prerequisites.

Step (d) still requires:

- S1-REQ-EPHEMERIS, including the consumed bodies/horizon and actual component identity.
- Completed Stage-1 freeze and required readbacks.
- Applicable L1 settlement, daśā pin and donor/tier-policy evidence.
- Stage-2 extract hash binding before inspecting/scoring the extract.
- Requalification and actual measurement receipts.

The existing `4.1` T-honesty limitation remains **UNVERIFIABLE**; diagnostic results do not make that candidate flip-eligible.

## Ranked amendments

| Rank | Required closing change | Blocks |
|---|---|---|
| **1 — R15-1** | Detect custom project/folder/organization policy writers; test correct ancestor scopes and exceptions; make phase expectations explicit | Act-7/isolation preparation and credential chain; affected preparation for **(a)** and **(c)** |
| **2 — R15-3** | Resolve secret aliases to the intended resource; correct annotation parsing; test accepted API shapes and redirected resources | #2961/#2975/#2976 acceptance; **(c)** |
| **3 — R15-2** | Normalize API int64 timeout strictly; use real SDK-shaped fixtures through all callers; keep shared bytes identical | Act 6; **(c)** |
| **4 — R15-5** | Complete W5 and effective-writer checks; repair active shell command and operative contradictions | Affected pre-window checks, credential/log acts and approval preparation |
| **5 — R15-6** | Add natal-tier disclosure and first-seal input-stability rule; regenerate digest artifacts; complete SETTLED-1/re-pin chain | First brief/approval/seal; **(c)** |
| **6 — capacity evidence** | Valid actual-count build/verification/brief measurements and disposable-clone seal timing with honest labels | First approval/seal; not independently **(a)** |
| **7 — R15-4** | Refuse stronger isolation in conditional TRUNCATE guard and add arrival-race tests, or expressly narrow the owner-maintenance claim | Defence in depth; not an ordinary-role blocker under the reviewed ACLs |
| **8 — test evidence** | Remove manufactured assertion; complete real transition, enrichment and chronological-upgrade cases | Strength of the final-byte rehearsal claim |

If SQL, governed Python or shared contract bytes change, refresh the relevant hashes, implementation lock, goldens and composed evidence. Do not reuse this packet’s hash claims for changed files.

## Step lines

- **(a) BLOCKED BY R15-1 and R15-5 in pre-window preparation, followed by final composed-byte rehearsal and the ordered operational prerequisites. R14-1/R14-2 no longer independently block 1240 at source.**
- **(b) UNBLOCKED — registry binding remains accepted within the frozen input contract; G2 concerns freshness between verification and seal.**
- **(c) BLOCKED BY R15-1, R15-2, R15-3, R15-5 and R15-6; then SETTLED-1, daśā re-pin, capacity evidence and actual provisioning/verification/approval/seal receipts.**
- **(d) BLOCKED BY S1-REQ-EPHEMERIS, completion of the measurement freezes/readbacks and actual measurement evidence; measurement only.**

After source closure, the operational order remains:

1. Freeze combined bytes; validate all expected objects, enabled triggers, hashes and predecessors; rerun composed attacks and both window modes.
2. Land corrected isolation/provisioning code at the governed sitting boundary; perform **3 → 10 → 4 → 11**, with effective IAM and proxy prerequisites checked.
3. Perform combined **1 + 2a**; verify roles, secret version, memberships/ownership and password-null sealer; remove temporary act-11 power after every terminal outcome.
4. Configure act **5** and execute #2981’s no-secret gate proof.
5. Merge the protected train without 1241 or an intervening routine deployment; owner personally dispatches act **9**, `1204 → 1206 → 1232 → 1233 → 1240`.
6. Apply **1241 / act 8**; prove both principals present, exact ACL closure, CONNECT/schema/L1 reads and builder prerequisites.
7. Perform **2b**, verify activation and staging-secret deletion; deploy **6** from the same final commit as #2975; execute **6b**.
8. Prove actual-identity log access and denial, execution/override/read/cancel permissions, and proxy rights.
9. Build and independently verify. Before settlement this remains an unsealed dry run; after **SETTLED-1 and the reviewed daśā re-pin**, rebuild the final candidate, measure actual costs and establish the input-stability interval.
10. Produce the fresh brief, approve its exact digest/run/attempt/brief ID, seal, reconcile database state and verify cleanup.

None of these acts is authorized by this review.

## What I could not verify

- PostgreSQL concurrency, chronological upgrade, conditional-TRUNCATE and real-login suites were **not executed** in this review.
- No production database was contacted, and no principal, secret, permission, workflow or deployment was changed.
- Actual Cloud Run deployment/execution resources, Cloud Logging delivery, GitHub approval history and cancellation/reconciliation behavior remain unobserved.
- Production trigger inventory, effective ACLs/RLS, role attributes, ledger state and absence of alternative privileged write paths remain unverified.
- SETTLED-1, the replacement daśā build, live natal tiers and real candidate volumes remain unverified.
- The reported 344-test composed run, 43/38 window assertions and performance timings were not independently rerun.

The checkout remained clean. No file was written, moved or deleted.