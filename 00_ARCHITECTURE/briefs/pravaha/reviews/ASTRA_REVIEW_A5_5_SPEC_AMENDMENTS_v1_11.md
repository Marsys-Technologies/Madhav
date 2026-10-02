---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.11"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: "ac36f6a86 (campaign/pravaha)"
reviewed_heads:
  campaign/pravaha: "ac36f6a8699533ea4bc32c650ec49005acd97fe0"
  origin/main_initial: "b88f0965b8bdb0df3066f1a1a2b6a0ab54abd106"
  origin/main_later_observed: "ea62dc0f757f4cdc054f7ae9f3e48090d051a220"
  pravaha/a53-am5-inventory: "bf369fcaa8bf399e3f23667d728e8ee56b216479"
  PR_2867_pravaha/b6-am5-inventory-migration: "e4d31c9ef82aa2e3874cd2095d295622f6756bf6"
  pravaha/b6-am21-p1-anchor-1233: "728b91501ad5c3b653a6130c7cac792b381871da"
  PR_2949_pravaha/b6-1241-verifier-sealer-grants: "20255185ff10c4c650f576e14fb3b01147f4f8cc"
  PR_2952_pravaha/b6-composed-rehearsal: "0a3347749f7cfffe0e6031ecece93b856091bd4e"
  pravaha/b6-composed-rehearsal-integration: "34f23a4756bd9f34e92a29b96ecc8bb36d24f8ac"
  PR_2963_pravaha/b6-gochara-role-provisioning-oneshot: "7dfcef1f5a1768bb219064c013c53f0462712362"
  PR_2961_pravaha/b6-act7-verifier-secret-isolation: "84331f7042825bd7e86b5ea8909173c3b8e0a9bc"
  PR_2923_pravaha/b6-stage1-candidate-measurement: "0855876eb0a5e17da02a5dd599c29a0f33f5e2c5"
  PR_2897_pravaha/b6-am13-kernel-registry: "2839fe03a8c4a80e008ee89603e973fece6bde28"
  PR_2897_merge_on_main: "8cf05f507de0a2f8047ea32640ab50eeb16cf65c"
comparison_heads:
  round_11_writer: "d4609f1817f5524eb8c6dc9524cf446bc88929c4"
  round_11_measurement: "aa4a9853e30e27f1b2f3438616e3a55545c9e475"
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT.**

R11-1, R11-2 and R11-5 are **CLOSED at source**. R11-3 and R11-4 are **PARTLY CLOSED**. The remaining work includes source changes; this is not merely awaiting operational acts and receipts.

The owner’s decision to allow the steward to approve using the same account is **not itself a rejection reason**. The revised trust boundary is substantially honest. However, “the brief binds approval to the exact output” remains overstated, and the trusted GitHub sealing workflow on which that statement depends is not implemented in the reviewed sources.

Numerical activation remains **DISABLED**.

**Item status**

| Item | Status | Verdict | Remaining change |
|---|---|---|---|
| R11-1: excluded-version/held-path output escapes the gate | **CLOSED** for the governed record/window/membership tables | ACCEPT | The original attacks are addressed. The broader candidate boundary is a separate R12-1 finding below. |
| R11-2: incomplete/shared P1 derivation | **CLOSED** | ACCEPT | No remaining defect from the round-11 reproductions. |
| R11-3: report, brief, approval binding and receipt | **PARTLY** | REJECT | Complete the output identity and implement the actual approval-consuming sealing workflow: R12-1, R12-2. |
| R11-4: secret command and concealed pipeline failure | **PARTLY** | REJECT | Correct command is present; the outer wrapper still returns success after failure. Provisioning also has uncovered failure paths: R12-3–R12-5. |
| R11-5: extractor transaction configuration | **CLOSED at source** | ACCEPT | No remaining transaction-configuration change. Step (d)’s ephemeris and freeze requirements remain. |
| Deferred receipt constraint | **Sound within its stated first-seal scope** | ACCEPT | It enforces receipt existence and manifest matching, not genuine approval. Attribution/documentation qualifications below apply. |
| Seven-table output identity | **Incomplete for the complete-candidate claim** | REJECT | Bind the additional published facts or enforce their exclusion. |
| 1241 v4 privileges | **Acceptable for the implemented library flow** | ACCEPT_WITH_AMENDMENTS | Reconcile receipt-attribution claims; rederive grants if R12-1/R12-2 add reads. |
| #2963 provisioning | **Not fail-closed as claimed** | REJECT | R12-3 and R12-4. |
| #2961 secret-isolation preflight | **Acceptable at source** | ACCEPT | Live configuration and execution receipts remain outstanding. |
| Composed rehearsal | **Useful composition evidence, with qualifications** | ACCEPT_WITH_AMENDMENTS | Correct its completeness claims and cover the new attacks. |
| #2923 measurement tooling, for (d) only | **Acceptable for the reviewed fix** | ACCEPT | Does not discharge the 4.1 ephemeris requirement or Stage-1 freeze. |

I read the round-11 review first. Reviewer reproductions used exact Python/shell source loaded into memory, with database-row adapters or command shims where needed. **They were not PostgreSQL executions.** The PostgreSQL results below remain author-reported evidence.

The requested reproductions produced these results:

| Reproduction | Result |
|---|---|
| Superseded P3 record and held P5 record carrying a numeric result, reusing existing contact data, before/after verification | Python preflight refuses both with `generation_output`; SQL source independently ranges over the whole governed generation. Existing included-grain attestations do not bypass the new arms. |
| Duplicate fifth P1 record | Refused by exact multiset cardinality. |
| Wrong affected person / object role | Separately refused by `verify_p1_results`. |
| Builder permission-function mutation | Verifier’s independently derived relation remained unchanged. The unmutated implementations agreed on 234 class/lord cases examined. |
| `--report-only` | Evaluates the gate, retains violations, persists nothing and reports `REPORT_ONLY`. Exit 0 means report completion, not verification success. |
| `--brief` with a gate violation | Refuses with `candidate_not_approvable`. |
| Two empty-gate candidates differing in a covered citation field | Different digests; old approval refused before publication; fresh approval reaches publish/seal/receipt flow. |
| Candidate differing only in omitted coverage facts | **Same approval digest; different publication content digest; old approval accepted by recompute.** |
| Corrected `gh secret set` command | Correct stdin form. |
| Failure of either secret write in the runbook wrapper | **Overall wrapper exit 0**, despite printing the captured failure. |
| Sealer post-password verification query fails | Script exits nonzero, but performs **no password rollback**. |
| Provisioning with the documented version-adder-only permissions | Version creation succeeds; listing and rollback destruction fail in the permission model. |
| Extractor with non-autocommit transaction state | Old setter reproduces `ProgrammingError … INTRANS`; new four-readback and extraction flows configure one READ ONLY / REPEATABLE READ transaction before querying. |

**Migrations**

The five window files and 1241 in integration commit `34f23a475` are byte-identical to their respective reviewed source heads. The window hashes also match the campaign’s current `EXPECTED_WINDOW_SHA256.txt`.

| Migration | Reviewed SHA-256 prefix | Verdict | Assessment |
|---|---|---|---|
| 1204 | `a0b267f7ef6002a1` | ACCEPT | Prior acceptance carried forward on matching bytes. |
| 1206, including PC-4 | `941c79f59f2d3d31` | ACCEPT | Builder verification-write separation and existing completeness/seal guards retained. |
| 1232 | `f2ef6406604b819d` | ACCEPT | Moon-scope/domain changes compose with the reviewed stack. |
| 1233 | `958b911703eee352` | ACCEPT | P1 anchor substrate retained; improved P1 verification is in the writer/job source. |
| 1240 | `11a8747a00cbd893` | ACCEPT for its governed-table gate and first-seal receipt constraint | R11-1 is repaired. Receipt enforcement is additive and replay-compatible. This does not make the complete-candidate approval claim true. |
| 1241 v4 | `adb47a8158740548` | ACCEPT_WITH_AMENDMENTS | 52 origin-1241 privilege entries confirmed; narrow publication UPDATE, legacy-window column SELECT and ledger column SELECT are appropriate. Qualifications below apply. |
| 1234, 1236, 1242 | Integration dependencies | Applied status unverified by reviewer | Production application and ledger IDs 919–921 are steward-reported. |

1241’s closure check compares effective privileges against its specification within its declared relation/function scope. It checks prohibited privileges as well as missing ones. It does not establish an unrestricted, database-wide least-privilege theorem.

The separate L1 reads on `chart_facts` and `chart_dashas` remain an explicit data-plane ACL dependency. Missing roles cause skipped grants and warnings, not future automatic provisioning. The execution receipt must show both principals found and the expected grants present.

The 52 removal tests establish necessity at the specified privilege-entry level. They do not prove that every column of each table-wide grant is independently necessary.

**The seal-approval arrangement and §R10a-2**

The withdrawal of “no agent can approve” and “an independent human approved” is accurate and necessary. The owner’s direct ruling supersedes the earlier delegated wording. The delegated BPHS reread must likewise remain described as an agent’s read under the owner’s instruction; it does not establish a human reread or activate numbers.

The proposed GitHub configuration can hold an environment job and its secrets until approval, permit same-account approval when self-review prevention is disabled, and prohibit administrator bypass. These are configuration-dependent controls, not evidence that they are already installed. A live branch-policy refusal is still needed; “protected branches only” has a documented permissive case when no branch protection exists. [GitHub environment controls](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)

§R10a-2 is accurate about:

- The loss of independent human approval.
- The distinction between the approval-gated sealing environment and the **ungated** provisioning workflow.
- Independent verification depending on the integrity of a separate job and login.
- The authoritative SQL seal checking the published manifest.
- A first seal requiring a receipt naming that manifest and containing a well-formed digest.
- An authorized sealer being able to supply a fabricated, well-formed receipt.

It is **not yet accurate as an accomplished end-to-end guarantee** that approval binds the exact complete candidate. R12-1 leaves published facts outside the digest; R12-2 leaves approval acquisition and transaction ownership without a reviewed executable caller.

Under this arrangement, a correctly executed, corrected sealing workflow would establish that the approved candidate identity still matched under the seal locks, the required verification state was current, the authoritative SQL checks passed, and a permanent seal/receipt pair committed.

It would **not** establish:

- Independent human judgment or a second actor.
- Attribution beyond the shared account and the supplied approval note.
- Honest computation by a compromised verifier or sealer.
- Exact contact-multiset completeness beyond the declared certification limits.
- Numerical validity, numerical activation, serving activation or owner acceptance of results.

No second approver identity is required by this review. Source and documents must accurately implement the owner’s chosen arrangement.

The deferred receipt trigger composes correctly with the other guards:

1. The 1153 publication/seal guard, 1206 completeness guard and 1240 window-verification guard remain effective. The new constraint is additional.
2. At first-seal commit, the receipt must match chart, generation and manifest, with a 64-hex digest.
3. The deferred FK permits receipt/seal insertion in either order within that transaction and prevents an orphan receipt from committing.
4. `ON CONFLICT DO NOTHING` replay inserts no new seal row, so it queues no new AFTER INSERT receipt requirement. Existing BEFORE guards still execute.
5. Seals predating 1240 are not backfilled or invalidated merely because they lack receipts. This follows PostgreSQL’s row-trigger and deferred-constraint semantics. [PostgreSQL trigger reference](https://www.postgresql.org/docs/15/sql-createtrigger.html)

**An arbitrary 64-hex digest is sufficient for this database constraint**, provided the remaining receipt fields and manifest match satisfy it. The composed race helpers themselves insert `repeat('a',64)`. SQL does not authenticate a GitHub approval, fetch its comment, or recompute the Python payload.

Two narrower qualifications should be recorded:

- The FK references only `(chart_id, generation)`. A receipt added later to a pre-1240 seal is not checked by a newly queued first-seal trigger; its manifest identity does not receive that trigger’s validation.
- `sealed_by DEFAULT session_user` and `approved_at DEFAULT now()` are defaults, not protected values. 1241’s table-wide INSERT permits explicit values. Either restrict receipt INSERT columns/enforce these values, or describe them as workflow-produced metadata rather than independently authenticated database attribution.

The first-seal constraint also does not force publication to occur in the same transaction as sealing. That atomicity is supplied by the sealing workflow’s transaction.

**New findings**

**R12-1 — The approval identity omits published candidate facts. Blocks (c).**

At writer `bf369fcaa`, `seal_brief.py:33–35,64–77` hashes every column except `created_at` of exactly seven tables. That implementation is sound for those tables, including otherwise unexamined citation fields. Its claim to cover all output is broader than its implementation.

The omissions are material:

- `kala_gochara_coverage` is absent. Its resolution, target counts, unavailable-input declarations and unsearched reason are candidate facts.
- `ledger.py:561–579` includes coverage rows and legacy contact rows in the publication’s `content_digest`.
- The coverage-drift check in migration 1156 examines convention, completed horizon and searched relations. It does not make the other coverage fields part of the approval identity.
- The manifest query in `seal_brief.py:107–108` omits `ephemeris_backend` and `writer_asset_id`.
- Legacy `kala_gochara_contacts` and `kala_gochara_windows` are absent, although publication consumes the former’s content and the latter’s count.

The exact-source reproduction changed coverage facts while preserving the covered output and gate result. The approval digest stayed unchanged; `ledger._canonical_row_set` changed; the old approval passed recomputation. The gate result was supplied by the row adapter; the corresponding SQL omissions were checked separately at source.

There is also a concrete boundary problem in the rehearsal: `composed_world.py:135–141` creates two legacy windows for generation `'5.0'` with non-NULL intensity values. The approved-flow tests accept that world. It therefore cannot substantiate the unqualified disclosure:

> “no numerical result exists in this generation”

This does not reopen the original excluded-version/held-path defect in the governed tables. It demonstrates that the claimed complete generation extends beyond the enforced boundary.

**Closing change:** define one explicit candidate boundary shared by the brief, publication and sealing path. Bind semantic coverage and publication identity fields. For the first 5.0 candidate, reject matching legacy projection rows unless they are deliberately included, policy-checked and identity-bound. Bind or enforce absence of legacy contacts as appropriate. Ensure the consumed facts cannot change between recompute and publication through an unguarded write path.

Preserve the deliberate AM-4 exclusion of on-demand Moon query receipts; do not indiscriminately hash them into build identity. Publication must use the same boundary.

Add tests for coverage-only and publication-identity-only changes with otherwise empty gates, and for legacy generation-5 numeric rows. An old approval must fail before publication.

Physical objects and sky events require a more precise statement, not blanket hashing:

- Referenced physical objects/contact identities are global and insert-only. Binding their references while relying on their enforced immutability is defensible within the same database.
- Sky events are global and permit defined enrichment. They are not consumed by the reviewed P1–P4 candidate verification path. Their exclusion is acceptable for this milestone, but the digest must not be described as covering all sky substrate.
- `created_at` exclusion is acceptable as an explicit audit-field exclusion. The claim should concern semantic candidate identity, not every possible byte difference.

**R12-2 — The trusted approval-consuming sealing workflow is missing. Blocks (c).**

`seal_flow.py:16–37` is a useful library implementation. It accepts `approved_digest`, login, note, run identifiers and sealing commit from its caller. It neither obtains nor authenticates those values and expressly leaves transaction ownership to the caller.

In the reviewed writer and composed integration sources, its executable callers are tests. No reviewed production workflow:

- Displays and retains the verifier’s brief before the approval gate.
- Retrieves the approval/comment for the correct run and attempt.
- Extracts and checks the approved digest.
- Binds execution to the reviewed sealing revision.
- Mounts the sealer credential only in the gated job.
- Owns the transaction encompassing recompute, publish, seal and receipt.

The test harness supplies approval strings directly. That is appropriate for library testing, but it does not implement GitHub approval binding.

**Closing change:** implement and review that workflow and its caller. Reject absent, malformed, wrong-run and stale approvals. Require the milestone’s `all_null_candidate/1` policy explicitly. Use an explicit transaction and verify a receipt failure rolls back publication as well as sealing. Test mismatched run/attempt, changed brief, wrong revision and failure after publication. No independent human identity is required.

**R12-3 — Provisioning permissions do not support its success or rollback path. Blocks the prescribed preparation for (a), and consequently (c).**

Runbook act 11 grants the workflow identity only `roles/secretmanager.secretVersionAdder` on the verifier secret.

But `gochara-provision-roles.sh`:

- Calls `secrets versions list` at line 133 before marking completion.
- Calls `secrets versions destroy` at line 41 on failure.

Version Adder provides neither permission. [Google Secret Manager role permissions](https://docs.cloud.google.com/iam/docs/roles-permissions/secretmanager)

Under the documented permission set, the script can add a version and set the verifier password, then fail listing versions; rollback also cannot destroy the version. The command-shim reproduction followed that path and reported an incomplete rollback. Undeclared inherited powers could change the live outcome, but would not validate the documented least-privilege model.

The temporary IAM binding also needs an explicit failure/cancellation removal path; removal only after successful completion is insufficient.

Additionally, the script’s “nothing secret … in argv” claim is false: `ADMIN_DATABASE_URL` is passed positionally to `psql` in queries, mutations and rollback.

**Closing change:** align the reviewed permissions and implementation. Either authorize the narrowly scoped, non-access permissions actually required for verification/destruction, or move those operations to an explicitly defined authorized cleanup path. Test using that exact permission model. Require verified removal of the temporary binding after success or failure, and explicit recovery after interruption. Keep the admin connection secret out of process arguments.

**R12-4 — Sealer password activation is not rolled back after a later failure. Blocks (c).**

In `gochara-provision-roles.sh:137–150`, `ALTER ROLE … LOGIN PASSWORD` precedes `verification_facts`.

The EXIT trap cleans up only recorded newly created roles or secret versions. Neither is recorded during `sealer-password`.

Injecting failure into the first post-ALTER fact query produced:

```text
exit 31
SEALER_PASSWORD_SET
POSTCHECK_QUERY_FAILED
```

There was no password reset or disabling action.

The runbook’s partial-failure table says a workflow failure leaves `PASSWORD NULL` and instructs deletion of both secrets. That is false for this path and could discard the stored copies while leaving the login active.

**Closing change:** make activation and required postconditions transactional where possible, with fail-closed checks before commit. Provide compensating reset/disable and verification for ambiguous or interrupted outcomes. Correct the recovery table: do not assume a failed run left the password unset, and do not discard recovery material before confirming the role’s state.

**R12-5 — The runbook still converts failure into shell success. Blocks (c).**

The corrected command is valid:

```text
gh secret set GOCHARA_SEALER_DB_URL --env gochara-seal
```

With no `--body`, the CLI reads stdin. [GitHub CLI manual](https://cli.github.com/manual/gh_secret_set)

However, the final wrapper statement is:

```bash
[ "$rc" -eq 0 ] || { echo "ACT 2b STEP 1 FAILED ..." >&2; }
```

On failure, the successful `echo` becomes the final status. Exact-snippet reproductions returned **0** after both the lasting-secret write failed with captured status 12 and the staging-secret write failed with captured status 13.

**Closing change:** propagate the captured nonzero status from the complete executable unit and require its caller to stop. Retain cleanup and rollback diagnostics. Test password generation, each secret write and rollback failure at the outermost invocation boundary.

**Documentation amendments, distinct from blockers**

Reconcile the final packet with its operative documents:

- The runbook frontmatter and opening still contain owner-in-person/owner-only wording contradicted by the direct ruling and §5.3.
- Runbook §6 and `SEAL_APPROVAL_PAYLOAD_v1_0.md` still describe receipt storage as an undecided R1/R2 proposal, with R2 recommended. The implemented choice is R1.
- The rehearsal plan’s “CURRENT” table still names round-11 writer/integration heads and the old 1240 hash, although the hash file is updated.
- Scope `sealed_by`, same-transaction and manifest-matching claims to what SQL actually enforces.
- Replace “no stand-in anywhere” with a precise account of the mirrored schema, externally supplied L1 grants, selective monkeypatches and role-switching harness.

These corrections do not require reversing any owner ruling.

**What the composed rehearsal establishes**

I confirmed that the relevant writer implementation files and all six migration files in `34f23a475` match the reviewed heads. I also confirmed the embedded 1241 specification contains 52 origin-1241 privilege entries.

The author-reported **97 passed, 0 failed, 0 xfailed** is meaningful evidence for the implemented composition:

- Restricted build, independent verification and sealing library flow.
- New generation-wide governed-output checks.
- Grant necessity across verify → brief → recompute → publish → seal → receipt → replay.
- First-seal receipt absence/wrong-manifest refusal.
- Receipt immutability under ordinary DML.
- Historical-seal replay.
- Chart-lock contention and stale-approval refusal for a covered output change.

It does not establish live production provisioning, IAM correctness, a GitHub approval flow, full candidate identity or numerical activation.

Specific limits matter:

- The verifier is exercised through a real login; the sealer helper uses `SET ROLE` on the harness connection. The test explicitly accommodates the harness `session_user`. This is privilege evidence, not a production sealer-authentication receipt.
- L1 reads are supplied separately.
- The foreign P3 attack uses an added successor; one setup isolates the new generation-output check from other census checks. The SQL predicate nevertheless covers the original superseded-version case.
- The wrong-person composed case adds a copied record, allowing cardinality rejection to occur first. Separate semantic probes are needed; my in-memory probes separately exercised person and role.
- The numeric legacy-window fixture prevents the suite from proving the unqualified whole-generation all-NULL claim.
- The 43/38 mechanical window assertion counts remain author-reported, not independently rerun here.

The disclosed sub-60-second, smooth-motion, boundary-tolerance and occupied-time-union limits remain acceptable limits for this milestone. They are not newly imposed blockers. Exact episode multiplicity and numerical evidence-root behavior remain outside acceptance.

**Measurement tooling for (d)**

R11-5 is closed at source. `dump_extract.py:175–203` configures transaction characteristics once before querying. Readers now require that configuration without resetting it mid-transaction.

Using actual psycopg transaction-setting methods against a controlled transaction-state adapter, I reproduced the old INTRANS exception and exercised:

- All four readbacks in one invocation.
- Manifest, donor and tier reconciliation followed by extraction.
- One `BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY`.
- Rollback and close at completion.

Output was captured in memory; no extract file was written. This was not a live PostgreSQL snapshot/isolation test.

Step (d) still needs the 4.1 chain’s acceptable AM-16 ephemeris identity, covering all consumed bodies including the Moon and the consumed horizon, followed by the substantive Stage-1 freeze. A backend probe alone remains insufficient. These requirements are separate from the all-NULL 5.0 milestone.

**Ranked closing amendments**

| Rank | Item | Exact closing result | Blocks |
|---|---|---|---|
| 1 | R12-1 | Shared, complete candidate boundary; bound coverage/publication identity; excluded or verified legacy output; stale approval rejected for each newly covered change | (c) |
| 2 | R12-2 | Reviewed executable workflow consumes the actual run’s approval and owns the atomic sealing transaction | (c) |
| 3 | R12-3 | Provisioning succeeds and cleans up under its declared permissions; temporary IAM cleanup covers failure; admin secret removed from argv | Prescribed preparation for (a), then (c) |
| 4 | R12-4 | Failed/interrupted sealer activation cannot silently leave an active credential; recovery instructions match actual state | (c) |
| 5 | R12-5 | Complete password wrapper returns nonzero on every failed prerequisite and its caller stops | (c) |

After source closure, the operational acts remain, in this order:

1. Integrate the accepted revisions, reconcile documents, record final hashes and rerun the composed/window rehearsals on those bytes.
2. Refresh the ledger and ownership/default-privilege evidence; confirm protected files remain unapplied and routine predecessors/dependencies are present.
3. Apply the reviewed act-7 isolation changes; provision the verifier service account, key prohibition, secret and temporary workflow permissions; run corrected role creation; remove and verify temporary permissions.
4. Configure the same-account sealing environment and prove its actual gate/branch behavior while the sealer remains unable to authenticate.
5. Perform the owner’s protected-window dispatch: **1204 → 1206 → 1232 → 1233 → 1240**, retaining capability cleanup and per-file receipts.
6. Apply 1241 afterward; verify both principals and exact privileges; complete the separately governed L1 reads.
7. Complete corrected sealer activation and staging-secret deletion; deploy the reviewed verifier and sealing workflow.
8. Build the explicitly all-NULL 5.0 candidate, run independent verification, emit/display the brief, record the steward’s digest-bearing approval, execute the atomic seal, and verify the resulting publication/seal/receipt. Keep serving and numerical activation disabled.

**Step lines**

- **(a) BLOCKED BY R12-3 for the prescribed provisioning route, plus the listed operational preconditions.** The five protected SQL files themselves close the round-11 source objection; this review does not authorize dispatch.
- **(b) UNBLOCKED.** #2897 is present on main at merge `8cf05f507`; the reviewed registry implementation matches the merged files.
- **(c) BLOCKED BY R12-1, R12-2, R12-3, R12-4 and R12-5, plus provisioning, deployment and execution receipts.**
- **(d) BLOCKED BY the undischarged 4.1 ephemeris requirement and the uncompleted Stage-1 freeze. R11-5 is closed.**

**What I could not verify**

The read-only sandbox precluded initializing a disposable PostgreSQL instance. SQL trigger, FK, privilege and concurrency conclusions are source-level assessments supported by the inspected rehearsal source and author-reported results.

I did not connect to production, inspect secret values, perform credential acts, dispatch workflows or independently verify the reported production ledger applications. I did not independently rerun the 97 PostgreSQL tests, the mechanical window rehearsals or the real ephemeris workload.

No file was created, edited, moved or deleted, and no git write command was run.