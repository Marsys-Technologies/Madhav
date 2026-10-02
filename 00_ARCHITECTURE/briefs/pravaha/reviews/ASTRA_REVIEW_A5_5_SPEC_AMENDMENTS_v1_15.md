---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.15"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "d6d4525c0 (campaign/pravaha; detached)"
reviewed_heads:
  origin/pravaha/a53-am5-inventory: "1e6e55534"
  PR_2961: "2b91a1e5f"
  PR_2975: "aa3c72259"
  PR_2976: "668718fc3"
  PR_2949: "c26743b5d"
  PR_2919: "ada3a8fbe"
  PR_2981: "c3e16405f"
  PR_2963: "9bbad986a"
  origin/pravaha/b6-composed-rehearsal-integration: "ef99ba070"
  PR_2952: "f7bc0f321"
  PR_2923: "d52cbea97"
comparison_refs:
  origin/main: "55a666f8943bcda313f1e9bc52f3ea3d47916c96"
  writer_round_15: "2ae229c6f"
  PR_2961_round_15: "a87b3ba79"
authority: "Review only; authorizes nothing."
---

# Verdict

**REJECT the complete executable set as presently written. ACCEPT the protected-window migration source, including final 1240, independently of the first-seal ceremony. ACCEPT 1241 v7 against that 1240.**

The principal SQL defects identified by both round-15 reviews are repaired. The registry recheck runs under the appropriate transaction locks, and the five additional sealer SELECT grants are justified.

Source work nevertheless remains:

1. **#2961’s composed preflight still rejects valid representations:** project-number normalization stops at the verifier-specific check, and an earlier validator still parses the documented secrets annotation as JSON.
2. **The new phase and exception configuration is not fully executable through the documented workflow.**
3. **§5.5 contains a SQL type mismatch and an undefined comparison between different digest schemes.** Its descriptions also lag the implemented protections.
4. **W5/W6 do not yet establish everything their acceptance language claims.**

These are distinct from the outstanding operational requirements: SETTLED-1, the reviewed daśā re-pin, actual capacity evidence, provisioning, deployment, independent verification, approval and committed receipts.

The approval remains **a steward AI-session action under the owner’s account**, not an independent human check. Numerical activation remains disabled.

## Item status table

“CLOSED” below means closed at source unless explicitly qualified.

| Item | Status | Judgment and exact remainder |
|---|---|---|
| **R15-1 — ancestor policy writers and phase** | **PARTLY** | Custom project/folder/organization policy-writer permissions are detected, and phase mismatches refuse. Normalize resources consistently through **all** isolation checks and normalize declared exception resources; finish phase configuration and exception delivery. **R16-1/2.** |
| **R15-2 — int64 timeout representation** | **CLOSED** | `"7200"` passes deployment readback, pre-execution and executed-resource checks. Invalid timeout representations refuse. Separate parser hardening remains under **R16-5**. |
| **R15-3 — aliases and annotation syntax** | **PARTLY** | The resolver understands comma-separated mappings; redirected credentials cannot pass the reviewed verification-job contract. But `assertAnnotationsSurface` still requires JSON, so the complete #2961 preflight rejects valid annotated resources. **R16-1.** |
| **R15-4 — conditional TRUNCATE snapshot hole** | **CLOSED** | Final 1240 refuses every non-READ-COMMITTED invocation before examining rows. The source tests include the two-connection counterexample and both READ COMMITTED arrival orders. Operative documentation remains stale. |
| **R15-5 — executable documents and W5** | **PARTLY** | W1–W4, the expected inventory, merge control, log-access proof and capacity checkpoint are materially improved. Remaining manifest/procedure/document corrections: **R16-2/3/4**. |
| **R15-6 — first-seal input stability** | **PARTLY** | Registry digest+census recheck, implementation check and digest-bearing natal/ephemeris disclosures are implemented. Repair §5.5’s SQL, comparison contract and stale enforcement description. The actual freeze/readbacks remain operational evidence. **R16-3.** |
| **Rank 6 — real capacity** | **NOT CLOSED** | Actual build, verification, brief and disposable-clone seal measurements remain absent. Required before approval, not an independent migration-source blocker. |
| **Rank 7** | **CLOSED** | Same closure as R15-4. |
| **Rank 8 — meaningful test evidence** | **PARTLY** | Manufactured assertion removed; genuine enrichment/precision tests and a chronological upgrade test added. The lifecycle test covers **12**, not 16, status pairs; the chronological test does not execute the claimed historical enrichment/precision behavior. **R16-6.** |
| **F-R15-1 — JSON numeric rendering mutation** | **CLOSED** | Textual identity comparison now refuses `2 → 2.0/2.00`; tests exercise the builder’s actual UPDATE path. |
| **F-R15-2 — first seal without result policy** | **CLOSED** | First-seal branch raises `seal_manifest_without_result_policy`; historical replay branches before that requirement. |
| **F-R15-3 — first-use refusals and remedies** | **PARTLY** | Retry-presence and unknown-field remedies are documented. The inherited-exception remedy does not necessarily pass the other isolation gates; direct-policy exceptions are not supported; phase configuration and additional representation refusals need explicit handling. **R16-2.** |
| **F-R15-4 — natal disclosure** | **CLOSED at source** | Observed consumed-row tiers control the disclosure and enter the digest. Implementation lock rederives correctly. This does not make external L1 state immutable. |
| **F-R15-5 — documents/evidence** | **PARTLY** | Both workflow files are now included; no-concurrent-build and post-supersede reconciliation statements are present; the granted-column attack is genuine. Remaining stale descriptions and a missing v7 static test in the integration exhibit are identified below. |
| **F-R15-6 — three legacy statement locks** | **NOT CLOSED; optional** | No new statement locks on coverage/contacts/windows. The tuple-lock/chart-lock deadlock possibility remains disclosed; whole-transaction retry is required. It is not an independent first-seal blocker. |

| Component | Verdict |
|---|---|
| Protected migrations, including final 1240 | **ACCEPT at source** |
| 1241 v7 | **ACCEPT at source** |
| Writer’s seal-time registry and disclosure changes | **ACCEPT at source**, subject to the external-input procedure |
| #2961 as a complete preflight | **REJECT pending R16-1/2** |
| #2975/#2976 shared contract | **ACCEPT_WITH_AMENDMENTS**; R16-5 is bounded hardening, with real-resource qualification still outstanding |
| Runbook/design/rehearsal/decision set | **REJECT as an executable set pending R16-2/3/4** |
| #2963 provisioning and #2981 gate-proof source | **ACCEPT at source**; operational behavior unverified |
| #2923 | **ACCEPT for measurement tooling only** |

# Migrations table

I independently recomputed the hashes from the frozen Git objects.

| Migration | SHA-256 / verification | Judgment |
|---|---|---|
| **1153–1157** | All five match `EXPECTED_WINDOW_SHA256.txt` | Accepted prerequisite contracts; actual deployed state must be checked |
| **1204** | `a0b267f7ef6002a1997c30d34595ec3b86147ca617bf70ef8a05de55b8407ca1` | **ACCEPT** |
| **1206** | `941c79f59f2d3d3125dc5ca680430d4a91a7dcddb53fc6daa9a9da8819e410d7` | **ACCEPT**; #2919 now carries these exact bytes |
| **1232** | `f2ef6406604b819d5f443e32c1e70914f2337ead8867f12e0aecd96d13f1ec44` | **ACCEPT** |
| **1233** | `958b911703eee3528e1db75624984020964b8d31fe3fe286d64071368bd5a705` | **ACCEPT**; existing-row preconditions still apply |
| **1240** | `05a8f897a0b8ae6b955915eced717ad30c98af485d490185333a88355707bc6b` | **ACCEPT at source** |
| **1241 v7** | `a3480710c7498065892965f23d9bee43dc700d4d8f16eb46ac8fb0ee601efefa` | **ACCEPT against final 1240**; routine application after the window |
| **1230/1234/1236/1242** | Packet reports applied | Re-read the actual ledger; this review does not establish their production application |

### Final 1240: three new behaviors

- **Textual manifest identity:** `1240_gochara_window_verification_gate.sql:975–980` compares the identity projection as text before considering lifecycle transitions. Numeric scale changes can no longer pass JSONB semantic equality while changing the attested rendering.
- **Required regime marker:** `:1147–1153` requires `result_policy` for a first seal. The requirement follows the replay branch, preserving the expressly narrower historical regime.
- **TRUNCATE isolation:** `:1022–1026` refuses stronger isolation before the conditional row check. At READ COMMITTED, governed rows still cause refusal; ordinary principals still hold no TRUNCATE privilege.

I found no source regression in the previously closed contact boundary, precision propagation refusal, lifecycle whitelist, post-seal brief refusal, deferred receipt enforcement or historical replay behavior.

### 1241 v7: least privilege

The five new privileges are **SELECT only** on:

- `ka_gochara_rule_path`
- `ka_gochara_rule_path_prerequisite`
- `ka_gochara_rule_path_soft_factor`
- `ka_gochara_predicate`
- `ka_gochara_factor`

`ka_gochara_rule_path_seal` was already readable. The digest implementation uses whole-row JSON projections, so these table reads are justified by the implemented query. No registry write, registry function execution or new verifier privilege accompanies them.

I parsed the grant specification: **67 origin-1241 grants**, comprising verifier 13 table/12 function entries and sealer 20 table/22 function entries. Effective privileges, ownership, membership, CONNECT, schema access and external L1/RLS behavior still require actual-role checks.

# Exact-function probes

I executed the frozen TypeScript/Python functions in memory, using synthetic API documents and in-memory file reads. These were **not live GCP calls or PostgreSQL tests**.

The shared contract is byte-identical in both PRs:

`2919bf044f63e4aee7deaec0f9cea6d8686ce81827edaabb0bf41f5ca444788a`.

## IAM and annotation probes

| Probe | Observed result |
|---|---|
| Custom `resourcemanager.projects.setIamPolicy` role at project scope, no exception | **REFUSE** |
| Custom `resourcemanager.folders.setIamPolicy` role at folder scope, no exception | **REFUSE** |
| Custom `resourcemanager.organizations.setIamPolicy` role at organization scope, no exception | **REFUSE** |
| Each preceding binding with its exact unconditional declared exception | Verifier-specific check **ACCEPTS** |
| Conditional binding with otherwise matching exception | **REFUSE** |
| `staged` with zero bindings / with deployer binding | **ACCEPT / REFUSE** |
| `deployable` with zero bindings / exact deployer binding | **REFUSE / ACCEPT** |
| Missing or invalid phase once the verifier account exists | **REFUSE** |
| Project policy identified by ID or number; exception identified by project ID | Verifier-specific check **ACCEPTS** |
| Same policy; exception identified by project number | **REFUSE** for either policy representation |
| Declared project owner, project-ID resource, complete relevant isolation checks | **ACCEPT** |
| Same owner, project-number resource | Verifier-specific check accepts; shared check **REFUSES** |
| Canonical Cloud Run service agent, project-ID resource | **ACCEPT** |
| Same service agent, project-number resource | Shared check **REFUSES** |
| Folder owner with exact verifier-control exception | Verifier check accepts; shared builder-impersonation check **REFUSES** |
| Comma-separated annotation through the new resolver | Correctly resolves same-project and foreign-project targets |
| Conflicting duplicate alias | **REFUSE** |
| Valid comma-separated annotation through `assertNoLiteralCredentials` | **REFUSE: “Cloud Run secrets annotation is not valid JSON.”** |
| Same valid annotation through `assertEffectiveIsolation` | **REFUSE** at that earlier literal-credential check |

The last two results apply to an ordinary annotated resource as well as the named verifier job. They are not explained by the verifier job’s deliberate annotation ban.

## Shared-contract probes

`D / P / E` means deployment readback / pre-execution / executed-resource check.

| Input | D / P / E |
|---|---|
| `timeoutSeconds: "7200"` | **ACCEPT / ACCEPT / ACCEPT** |
| `timeoutSeconds: 7200` | **ACCEPT / ACCEPT / ACCEPT** |
| Boolean, float `7200.0`, `"7200.0"`, `"07200"`, `"+7200"`, whitespace, exponent, null | **REFUSE / REFUSE / REFUSE** |
| Memory `8Gi`, `8192Mi` or `8589934592`, with CPU `2` or `2000m` as applicable | **ACCEPT / ACCEPT / ACCEPT** |
| CPU `"2.0"`, `"2e0"`, `"+2"`; memory `"8.0Gi"` or `"0.0078125Ti"` | **REFUSE / REFUSE / REFUSE** |
| Wrong-case memory `"8gi"` | **REFUSE / REFUSE / REFUSE** |
| Retries absent in both representations | **REFUSE / REFUSE / REFUSE** |
| v1 absent, v2 `0`; v1 `0`, v2 absent; both `0` | **ACCEPT / ACCEPT / ACCEPT** |
| v1/v2 disagree as `0/1` or `1/0` | **REFUSE / REFUSE / REFUSE** |
| v1 `0`, v2 `false` or `"garbage"` | **ACCEPT / ACCEPT / ACCEPT — malformed v2 is discarded** |
| Malformed v1, v2 `0` | **REFUSE / REFUSE / REFUSE** |
| Foreign, same-project, empty or comma-separated secrets annotation in v1 | **REFUSE / REFUSE / REFUSE** |
| Secrets annotation only in supplied v2 document | **REFUSE / ACCEPT / REFUSE** |
| Missing secret version, pinned version `"1"`, extra `optional:false`, qualified selector name | **REFUSE / REFUSE / REFUSE** |
| Changed command, extra environment variable, secret volume, volume mount, `envFrom`, sidecar, tag image or wrong service account | **REFUSE / REFUSE / REFUSE** |

The timeout repair matches Google’s documented v1 string-int64 representation. Both API versions document retry presence and a default of three when unset. [TaskSpec](https://docs.cloud.google.com/run/docs/reference/rest/v1/TaskSpec), [TaskTemplate](https://docs.cloud.google.com/run/docs/reference/rest/v2/TaskTemplate).

### Is the annotation ban compatible with `--set-secrets`?

**Yes, for the exact short-name deployment authored in #2976. It is not compatible with every valid same-project representation.**

The installed Google Cloud SDK 576.0.0 mapping code distinguishes a short local secret from a qualified secret path. Its mapping functions produce:

- `gochara-verifier-db-url:latest` → the short selector, without a remapping annotation.
- `projects/<number>/secrets/gochara-verifier-db-url:latest` → an alias and annotation, even when that number names the same project.

Google’s documented YAML form also permits the annotation. Consequently, the ban is a defensible restriction on **this deployment contract**, not evidence that annotated same-project resources are invalid. Actual server readback remains unobserved. [Cloud Run job secrets](https://docs.cloud.google.com/run/docs/configuring/jobs/secrets).

# New findings

References to `runbooks/`, `design/`, `decisions/` and `reviews/` below are under `00_ARCHITECTURE/briefs/pravaha/`. Code references identify the frozen PR or writer head.

## R16-1 — #2961 repairs individual helpers but not the complete validation path

**P2; source blocker for acceptance of the isolation preflight.**

In `platform/scripts/data-plane-secret-isolation-preflight.ts`:

1. **`:304–318` still parses `run.googleapis.com/secrets` with `JSON.parse`.**  
   `assertEffectiveIsolation` invokes this path at `:648–653` before using the repaired resolver. A valid documented annotation therefore fails before its secret identity can be evaluated.

2. **`:535–544` normalizes only the encountered verifier-policy resource.**  
   Declared exception strings remain unnormalized at `:532`.

3. **`:613–616` and `:629–636` retain raw project-resource comparisons.**  
   The same `effective` inventory reaches these checks at `:794–797`. A correctly declared project owner or canonical service agent that passes the verifier check can fail the shared check solely because the resource uses the project number.

**Closing change:** use one resource canonicalizer throughout policy collection, exception parsing and every shared/verifier comparison. Use one documented annotation parser in both literal-surface validation and secret resolution. Retain rejection of malformed/conflicting mappings and redirected verifier credentials.

Add tests through the **composed check sequence**, including a valid annotated ordinary resource. Passing only `extractRunIdentityAndSecrets` or `assertVerifierInheritedControl` is insufficient.

I did not establish that production currently returns the number form or contains an affected annotation. These are demonstrated valid-representation failures, not claims about observed production failures.

## R16-2 — Phase and exception remedies are not fully wired or accurately documented

**P2; blocks the affected pre-window preparation and first-use acts.**

The runbook contains no operative setting/readback sequence for `DATA_PLANE_VERIFIER_PHASE`. Yet #2961 requires it after account creation, and four `deploy.yml` invocations read the repository variable. #2976 separately hard-codes `deployable`.

The exception remedy also has three problems:

- Neither inspected workflow exports `DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS` to the preflight. Declaring a repository variable alone does not supply that process environment.
- Runbook `:213` suggests an inherited owner exception closes the refusal. It may pass the verifier check and still fail the existing secret-access or builder-impersonation checks.
- Runbook `:214` offers the preceding exception route for a legitimate **direct service-account binding**. The direct-policy validator has no exception mechanism; it permits only the exact phase-specific policy.

**Closing change:**

- Specify and verify `staged` at act 3, `deployable` after act 10, and the corresponding rollback transition, for both local invocation and workflow configuration.
- If declared exceptions remain supported, explicitly pass the reviewed value through every workflow invocation.
- State that an exception must satisfy **all** isolation gates. Do not silently exempt it from builder/secret protections.
- For direct service-account policy, require restoration of the exact policy; remove the unsupported exception remedy.

### First-real-use refusal assessment

| Correct or potentially legitimate resource condition | Current handling | Does the table provide an adequate remedy? |
|---|---|---|
| Owner/service agent represented by project number | False refusal in shared gate | **No; R16-1 source repair** |
| Valid comma-separated annotation on another inspected resource | False JSON refusal | **No; R16-1 source repair** |
| Correct verifier policy but missing/stale phase setting | Refusal | **No explicit configuration sequence; R16-2** |
| Reviewed inherited control-plane binding | May pass verifier gate but fail another gate | **Only partly; current exception remedy overclaims** |
| Extra direct SA-policy binding | Refusal by exact policy | Removal is valid; the offered exception route is not |
| Zero retries omitted by v1, present in v2 | Accepted | **Yes** |
| Retries absent in both | Refused | **Yes:** inspect the presence-bearing response and redeploy; never infer zero |
| Benign new task/container field | Refused | **Yes:** reviewed exact-value extension in both copies |
| Equivalent but unsupported quantity spelling | Refused | **No explicit row:** use the authored canonical deployment; if server readback differs, review exact value normalization |
| Same-project alias, explicit `optional:false`, or qualified secret selector | Refused by the job contract | **No explicit row:** restore the authored canonical job; do not bypass validation |
| Image/commit mismatch | Refused | **Yes:** redeploy from the same sealing commit |

The quantity parser supports useful equivalent integer-unit forms, but not the complete quantity grammar. I have not observed Cloud Run returning the rejected fractional/exponent spellings for this deployment; they are a compatibility limit, not a demonstrated live failure.

## R16-3 — §5.5 is not yet an executable first-seal readback contract

**P2; blocks the first-seal procedure, not migration source.**

### SQL type mismatch

Runbook `:292` unions `chart_facts.build_id` and `chart_dashas.build_id` without casts.

The repository’s declared schemas make the former **TEXT** (`platform/migrations/_archive/014_chart_facts.sql:15`) and the latter **UUID** (`_archive/135_chart_dashas.sql:8`). Against those types, the UNION fails type resolution. This is a source-level conclusion; the live catalog was not inspected. [PostgreSQL UNION type resolution](https://www.postgresql.org/docs/15/typeconv-union-case.html).

**Closing change:** cast `build_id::text` in both branches and verify the complete readback query against the faithful schema.

### Different fingerprints are instructed to be equal

Runbook `:292–293` requires R0/R1/R2 to agree and also to equal what the brief and receipt name. But:

- Its auxiliary registry fingerprint is whole-table **MD5**, including audit fields.
- The manifest registry identity is selected-row **SHA-256**, with specified audit exclusions, plus the sealed-version census.
- The whole-chart build-ID/count inventory is not the consumed-row digest.
- The receipt does not reproduce every auxiliary corpus/build-ID fingerprint.

**Closing change:** define two comparisons explicitly:

1. Compare identically formatted auxiliary readbacks **R0 ↔ R1 ↔ R2**.
2. Compare each pinned component with its actual manifest/brief/receipt counterpart using the **same derivation and representation**.

A whole-table MD5 is not expected to equal the manifest registry digest. Normalize a repository-qualified image reference to its digest when comparing it with `producer.image_digest`.

### Operative descriptions remain stale

| Location | Remaining contradiction | Required correction |
|---|---|---|
| Runbook `:290` | Says seal-time registry rederivation and 1241 v7 are pending | Describe the landed job check and transaction lock |
| Runbook `:293` | Says natal disclosure is pending and introduces a first-approval G3 wait | Record the implemented disclosure; align with the owner decision being required before **numerical** activation |
| Decision document `:38`, `:67`, `:76` | Says registry content is not rederived at seal | Separate the now-enforced registry check from procedural ephemeris/L1 stability |
| Runbook `:103`; design v1.2 `:35` | Describe the stronger-isolation TRUNCATE hole as unfixed | State the new explicit non-READ-COMMITTED refusal |
| Runbook `:285` | Calls the sole carrier “1241 v6” | Change to v7 |
| Runbook `:287` | Opens with #2919 still carrying stale 1206, then records its resolution | Mark the old state historical; retain the current hash control |
| Rehearsal plan §0/M1/O2 | Operative counts still say 43/38 while the current run is 45/40 | Label historical counts or update the current checkpoint expectations |

The packet’s expressly retained round-15 section is historical; I am **not** treating that retained section as an operative contradiction.

## R16-4 — W5 is useful but incomplete; W6 does not check preservation in both directions

**P2 verification amendment; affects window qualification.**

I counted **32 relations and 106 triggers** in the committed manifest. The relation coverage now includes the previously omitted digest tables.

The catalog SQL is otherwise coherent for PostgreSQL 15: schema-qualified relation resolution, noninternal triggers, enabled mode, trigger function, timing, events, level, UPDATE columns, arguments and deferrability.

Two gaps remain:

1. **`window_trigger_manifest.sql:35` records only whether `tgqual` exists.**  
   The precision-propagation trigger has `true` in that column. Replacing its condition with another non-null condition would produce the same manifest line.

   **Close:** include the actual normalized condition, for example `pg_get_expr(t.tgqual, t.tgrelid)`, in an escaped representation; regenerate the expected manifest and verify that a changed condition is detected.

2. **Runbook W6 `:101` checks only surviving production extras.**  
   An old legacy trigger that disappears after the window is neither in the mirror’s expected set nor among the post-window extras. The described comparison does not detect that disappearance.

   **Close:** compare the pre-window legacy baseline against the post-window catalog as well. Require preservation, or an explicitly reviewed expected change, for every baseline trigger.

Also make the W5 invocation itself fail on SQL errors (`ON_ERROR_STOP` and checked command status), not merely depend on a later manual inspection.

**Stand-in judgment:** the manifest meaningfully checks the required added guards on `kala_gochara_windows`. It does **not** demonstrate compatibility with that relation’s real legacy schema and triggers. W6’s actual inventory and review remain necessary; the 45/40 rehearsal cannot establish those production-specific interactions.

W1’s canonical-chart checks, W3’s relation-presence rule, W4’s post-creation CONNECT check and W2’s effective table/column privilege inventory are appropriate at source. W2 still needs actual caller/isolation evidence. External L1 tables, migration-ledger access and RLS require their separate checks; “32 relations” is not a complete external-input immutability proof.

## R16-5 — Shared-contract malformed-input handling is not uniformly strict

**P3 hardening; not a demonstrated real-resource seal bypass.**

- `gochara_verification_job_contract.py:86–96` collapses malformed v2 retry values into the same `None` used for absence. With v1 `0`, v2 `false` or `"garbage"` is accepted.
- `gochara_seal_execution_check.py:177–182` discards the v2 job document after extracting retries. Its pre-execution path scans only v1 for forbidden annotations. Deployment readback and executed-resource checks scan both.
- `parse_int64` accepts values outside signed-int64 range and accepts negative Python integers. The exact timeout/retry comparisons reject inappropriate values for those fields, so this does not reopen the `"7200"` defect.

**Close:** distinguish absent from invalid-present retry fields, reject invalid-present values, scan both documents in all callers, and either enforce the named integer range/domain or narrow the parser’s claim. Keep both shared copies and their pins identical.

The executed-resource annotation check still refuses the v2-only annotation probe. Moreover, that synthetic system-annotation shape is not evidence of a valid v2 server response. I do not classify this as a demonstrated credential bypass.

## R16-6 — Evidence claims remain slightly broader than the frozen exhibit

**Evidence amendment; no new SQL defect established.**

1. `test_a53_r14_sealed_contacts.py:228–229` parametrizes sources over `STATUSES[1:]`: **three source statuses × four destinations = 12 tests**.  
   This covers all normally reachable sealed source statuses, but not the advertised 16 pairs. Correct the claim or add the four deliberately inconsistent candidate-with-seal cases.

2. The chronological test at `:329–376` genuinely seals before 1240, upgrades, and checks lifecycle refusal, receipt non-retroactivity, brief refusal, TRUNCATE and replay.  
   It does **not** execute historical contact enrichment or precision propagation after that upgrade. Add that behavior if retaining the chronological-behavior claim; otherwise narrow the claim.

3. The integration and #2952 exhibit are tree-identical. However, compared with #2949, their  
   `platform/tests/unit/migrations/gochara_b6_1241_verifier_sealer_grants_static.test.ts`  
   omits the new v7 test beginning at PR line 61, which specifically asserts the registry SELECT set.

   Bring that test into the integration/exhibit, run the affected static suite and correct the reported count. The omission does not negate the inspected final migration or the 67-grant database-test source.

The new granted-column attack does reach the publication guard: it grants the column privilege, verifies that privilege and excludes `InsufficientPrivilege` as the observed refusal.

# First-seal input stability and regression assessment

## What is actually enforced

| Input or identity | Enforcement at seal | Remaining boundary |
|---|---|---|
| Consumed L1 fact rows | SQL rederives the consumed-row digest; full-row content includes tier/build identity, excluding the specified audit field | L1 writers do not take the Gochara chart lock |
| Consumed daśā rows | SQL rederives the daśā digest; the selected build constant participates in implementation identity | Pin must be reviewed and updated after settlement; coexistence alone is not refusal |
| Registry content and census | **Sealing job** rederives both using the build’s functions, under chart-exclusive/global-shared transaction locks | Trusted owner/trigger bypass remains outside the model |
| Implementation | Own-checkout lock before DB contact; running implementation digest compared with the manifest inside the seal flow | The settlement re-pin creates a new reviewed identity |
| Ephemeris files/library/probe | Manifest binding and independent verifier check; producer/executed image digest binding | Not rederived by the sealing job |
| Candidate output and boundary | Approved-payload recomputation, post-publication comparison, SQL gate and database-enforced current-brief receipt | Trusted verifier/sealer computation remains part of the system |

### Registry lock and derivation

`seal_flow.py:232–245` owns the transaction and takes the locks before sealing. `:45–48` calls `registry_problem`; publication, SQL seal and receipt follow inside that transaction.

`seal_brief.py:481–502` uses:

- `rule_registry.bound_path_refs()`;
- `input_vector.registry_payload(...)`;
- `registry_digest_of(...)`;
- the complete sealed-version census.

These are the build’s derivation and bound-path selection. The selected path/predicate/factor rows, ordered memberships and excluded audit fields match what the manifest pins.

The database lock relationship is exact:

- `1153:471`: global **exclusive** transaction advisory lock;
- `1153:483`: global **shared** transaction advisory lock;
- both use `hashtext('gochara5:global')::bigint`.

Valid registry inserts require the exclusive lock; membership inserts do too. Updates/deletes are refused, and TRUNCATE is refused. Therefore ordinary registry writes cannot change that content or census between the job’s check and COMMIT.

This closes the registry freshness gap at the reviewed seal-job boundary. SQL alone still does not perform the new Python content rehash.

### Is the procedural remainder acceptable?

**Yes, for this first all-NULL milestone, once §5.5 is corrected and actually evidenced.**

An immutable verifier image contains the ephemeris files; `Dockerfile.pipeline:12–28` bundles them at build time and pins the `.se1` hashes. The job contract forbids mounted volumes and alternative environment inputs. Image/commit readbacks, the written freeze and the verifier’s independent input check are an acceptable bounded arrangement here.

The same cannot be described as database serialization of L1. R0/R1/R2 observations do not prove there was no transient change-and-revert; the written producer freeze supplies that operational assertion. Changes outside the consumed-row population are not necessarily detected by consumed-row digests. A sealed generation also has no automatic continuous freshness monitor.

SETTLED-1 and the reviewed daśā re-pin remain mandatory before the first seal. SETTLED-2 is not required for this candidate: it reads the mean-node natal facts and computes the Swiss mean node, without consuming stored node-series outputs.

### Natal disclosure

The disclosure is materially accurate and avoids a permanently hard-coded “single” assertion:

- It reads tiers from consumed fact IDs.
- The standard sentence appears only for the ten expected subjects, all observed as `single`.
- Otherwise it reports observed tiers.
- Those tiers enter the digested payload.

I independently rederived the implementation lock:

`7960a924f706a59124d53f3f8204f25fd4b0a7fe02c068959cf9885f09b9e764`.

It is **not absolutely un-stale-able independently of the freeze**. External L1 remains mutable. Also, `seal_brief.py:283–284` reads the tiers twice, once for the sentence and once for the map. Reading once and deriving both fields from that value would remove a needless intra-payload race. This is sensible hardening, not an additional first-seal blocker under the required freeze.

### Ten-step sequence

The runbook faithfully reproduces the adopted ten-step dependency order at `:260–269`. The merge control correctly remains **after the train and before act 9**, with 1241 excluded from the train and applied afterward.

§5.5 and the settlement decision add conditions to steps 9–10 without requiring the protected migration window to wait for SETTLED-1. That separation is correct. The additions need the corrections in R16-2/3/4; they do not require redesigning the ten steps.

# Ranked amendments

| Rank | Closing change | Blocks |
|---|---|---|
| **1 — R16-1** | Repair the complete #2961 annotation and resource-normalization paths; add composed-function tests | Isolation/preparation for **(a)** and **(c)** |
| **2 — R16-2** | Wire/document phase transitions and exception delivery; correct remedies that cannot pass all gates | Pre-window acts 3/10/7 and subsequent workflow use |
| **3 — R16-3** | Cast L1 build IDs; define auxiliary-versus-pinned comparisons; update landed-enforcement descriptions and approval boundary | First final brief/approval/seal; **(c)** |
| **4 — R16-4** | Compare actual trigger conditions; preserve the pre-window legacy baseline; check SQL command failure | Window qualification and post-window acceptance |
| **5 — operational capacity** | Measure actual build/verification/brief and clone-seal costs; accept demonstrated bounds | First approval/seal, not migration-source acceptance |
| **6 — R16-5** | Distinguish invalid v2 retries from absence; scan both representations consistently; tighten integer claim | Contract hardening; no demonstrated live bypass |
| **7 — R16-6** | Correct lifecycle/upgrade claims; include and run the omitted v7 static test | Accuracy of the evidence package |
| **8 — optional** | Read natal tiers once; optionally add the three legacy statement locks | Additional hardening only |

No further change to the accepted **1240 migration bytes** is required by these findings. Refresh the relevant evidence when changing code or manifest-generation logic; refresh implementation identities and goldens if governed Python changes.

# Operational preconditions requiring actual execution

These remain separate from source amendments.

| Timing | Required check and evidence |
|---|---|
| **PRE-WINDOW** | Freeze the actual merged commit. After the protected train, verify all ten migration hashes and the committed expected manifest. Confirm no unintended 1241 carrier or intervening routine deployment. |
| **PRE-WINDOW** | Refresh PostgreSQL version and migration ledger; confirm routine predecessors, 1206’s unapplied status and the expected absence of its objects. Establish existing governed rows and seals rather than assuming an empty population. |
| **PRE-WINDOW** | Execute W3, W1 and W2: required relations present, zero prohibited-chart rows, effective writers/column privileges, helper EXECUTE and actual caller isolation. |
| **PRE-WINDOW** | Capture and review the real legacy trigger baseline under W6. Resolve interactions that the minimal stand-in cannot exercise. |
| **PRE-WINDOW** | Run corrected isolation checks against actual project/folder/organization policies, resolved roles, service-account keys, secret policies and Cloud Run surfaces. Verify phase configuration and every named exception. |
| **PRE-WINDOW** | Perform combined role provisioning through the approved route. Verify attributes, memberships, ownership, authentication behavior, secret version and password-null sealer state. Remove temporary act-11 power after every terminal outcome; inventory ambiguous outcomes. |
| **PRE-WINDOW** | Establish the GitHub environment and execute #2981’s no-secret proof: waiting, prohibited-branch refusal, steward approval, continuation and actual approval-history representation. |
| **WINDOW / POST-WINDOW** | Owner personally dispatches the five-file window. Record per-file ledger outcomes and recovery evidence; verify owners, capability revocation, PUBLIC EXECUTE, CHECKs and corrected W5/W6 comparisons. |
| **POST-WINDOW** | Apply 1241; prove both principals were found and exact effective ACL closure. Verify CONNECT, schema, L1 reads/RLS and builder prerequisites. |
| **POST-WINDOW** | Perform act 2b; prove activation, staging-secret deletion and compensation where invoked. Distinguish temporary staging from the lasting environment secret/database password. |
| **POST-WINDOW** | Deploy the verifier job from the exact sealing commit and image digest. Observe both API representations, bootstrap/imports, ephemeris assets, connection, identity, terminal status and logs. |
| **POST-WINDOW** | Prove narrow-view log access and actual `PERMISSION_DENIED` outside it under the workflow identity. Verify execute, override, get/list, cancel and proxy permissions individually. |
| **POST-WINDOW, BEFORE FINAL CANDIDATE** | Receive SETTLED-1; review and land the daśā re-pin; regenerate implementation identity. Discard/rebuild pre-settlement dry-run material. |
| **POST-WINDOW, BEFORE APPROVAL** | Build the controlled all-NULL candidate; independently verify every required class/grain after the last build. Retain actual runner/login identities and persisted results. |
| **POST-WINDOW, BEFORE APPROVAL** | Measure actual counts, widths, brief bytes, runtime/memory and disposable-clone seal transaction costs. The configured timeouts/resources remain starting values until demonstrated. |
| **POST-WINDOW, THROUGH COMMIT** | Execute corrected §5.5: producer freeze, no competing build/verification, R0/R1/R2 comparisons, stable image/commit and required input identities. |
| **POST-WINDOW, SEAL/CLOSEOUT** | Approve the exact digest/run/attempt/brief ID; observe the persisted verifier brief, publication, seal and receipt. Reconcile lost acknowledgements/cancellations from database state and verify specified cleanup. |

I verified that Google currently documents `roles/run.jobsExecutorWithOverrides` with run, override and cancellation permissions. That does **not** establish the workflow identity’s actual grants or its get/list permissions. [Cloud Run IAM roles](https://docs.cloud.google.com/iam/docs/roles-permissions/run).

# Step lines

- **(a) BLOCKED BY R16-1/2 in pre-window preparation and R16-4 in window qualification, followed by the operational prerequisites. The protected-window SQL SOURCE itself is ACCEPTABLE and UNBLOCKED independently of (c).**
- **(b) UNBLOCKED — registry binding remains accepted; the new seal-job content/census recheck also closes the ordinary registry-change interval through COMMIT.**
- **(c) BLOCKED BY remaining source/procedure work R16-1/2/3/4, then SETTLED-1, the reviewed daśā re-pin, capacity evidence and actual operational acts/receipts. It is not yet waiting only on operational execution.**
- **(d) BLOCKED BY S1-REQ-EPHEMERIS, completed measurement freezes/readbacks and actual measurement evidence. #2923 is accepted for measurement only.**

# Measurement only

#2923 preserves the measurement boundary: Stage-1 configuration freeze, Stage-2 extract binding, unknown-value bounds and refusal of incomplete or mismatched inputs. Its extract path is read-only, and it refuses governed `5.x` generations because that reader is not implemented there.

A measured result does not authorize activation. Missing coverage evidence remains an honesty limitation; estimates and bounds must not be presented as demonstrated qualification. No numerical or serving switch is approved by this review.

# What I could not verify

- The read-only sandbox did not permit creating a disposable PostgreSQL instance. SQL, concurrency, ACL, upgrade and real-login behavior were reviewed at source level.
- I did **not** independently rerun the reported **951 PostgreSQL/Python tests, 55 static tests or 45/40 window assertions**. I verified relevant source composition and identified the missing v7 static case.
- No production database, live IAM inventory, credential, job, environment or deployment was contacted or changed.
- Actual Cloud Run/Logging/GitHub representations, bootstrap behavior, cancellation, compensation and commit reconciliation remain unobserved.
- Production catalog types, trigger inventory, effective privileges/RLS, ledger state, SETTLED-1, replacement daśā build and real candidate capacity remain unverified.

The detached checkout remained clean. **No file was created, edited, moved or deleted; no git write command was run.**