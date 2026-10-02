---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.10"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: "af7111eaa (campaign/pravaha)"
reviewed_heads:
  campaign/pravaha: af7111eaaf5073091a8966dc9e64bca2c973054d
  origin/main: 9ca920d842dd60b6882d76d44e6fe59c30cd02e8
  origin/pravaha/a53-am5-inventory: d4609f1817f5524eb8c6dc9524cf446bc88929c4
  "PR #2897 origin/pravaha/b6-am13-kernel-registry": b29a7114df1e1b18d3207a5d460f854e91dcc551
  "PR #2867 origin/pravaha/b6-am5-inventory-migration": e4d31c9ef82aa2e3874cd2095d295622f6756bf6
  origin/pravaha/b6-pc4-1206-builder-verification-grant: e4d31c9ef82aa2e3874cd2095d295622f6756bf6
  "PR #2919 origin/pravaha/b6-am21-p1-anchor-1233": 728b91501ad5c3b653a6130c7cac792b381871da
  "PR #2949 origin/pravaha/b6-1241-verifier-sealer-grants": 089c65f27e62ff0e7b0057c57dd444dbf12e6a4f
  "PR #2952 origin/pravaha/b6-composed-rehearsal": aea94dc2ab7b10cddf823603738dfb27392b35de
  origin/pravaha/b6-composed-rehearsal-integration: 169141f0e032d647b557dffbe4ac42f7fba37a02
  "PR #2961 origin/pravaha/b6-act7-verifier-secret-isolation": 84331f7042825bd7e86b5ea8909173c3b8e0a9bc
  "PR #2923 origin/pravaha/b6-stage1-candidate-measurement": aa4a9853e30e27f1b2f3438616e3a55545c9e475
  "PR #2954 origin/pravaha/a58-honest-tier-readers": 9d46d22b489e6a858b345628b76661af76a26f9d
comparison_commits:
  round_10_writer: dc63af1129c63b4d6bfafbf59fbe9f1c9c3730b6
  round_10_measurement: 2e1e5fdd39578009b7972e90ed8338e07c9fdd3b
authority: "Review only; authorizes nothing."
---

**Verdict**

**REJECT the complete gate.** The original empty-output, freshness, locking, identity, boundary-tolerance and enumeration defects have substantive fixes. However, the all-NULL guarantee still misses records outside the included rule-version grains, and P1 still lacks complete independent record validation. The seal-brief procedure also promises behaviour the submitted implementation does not provide.

**Registry 1.1.0 binding is UNBLOCKED at source.** Numerical activation remains **DISABLED**.

What remains is **not only the owner’s operational acts and execution receipts**: the source and runbook corrections below are required first.

**Item status table**

“CLOSED” below denotes source-review closure. PostgreSQL execution evidence supplied by the authors is distinguished from my independent Python runs.

| Item | Status | Verdict | Evidence and exact remaining change |
|---|---|---|---|
| **R10-1 — complete record derivation** | **PARTLY** | **REJECT** | Repeated the real `verify_class` control-flow probes with controlled database adapters: empty required P1 and P3 outputs now raise disagreements, with zero verification writes. P2–P4 derive records and prerequisite results independently. P1 still accepts duplicate anchored records and does not validate affected person/object role: **R11-2**. |
| **R10-2 — result policy and dependency digest** | **PARTLY** | **REJECT** | For an included grain, replacing the same record ID with `evidence_for_occurrence=1` changes `inputs/2`; SQL also has an independent numeric-result refusal. But excluded/superseded-version records escape both the selected-grain digest and the result-policy arm: **R11-1**. |
| **R10-3 — derivation/persistence race** | **CLOSED** | **ACCEPT** | Chart then global-shared locks precede attestation reads and remain through persistence. Fingerprints are checked again before writing. Inspected the barrier-controlled early/late replacement tests and the composed builder-first contention test. I did not execute the PostgreSQL races. |
| **R10-4 — input identity, runner identity, final gate** | **CLOSED for the persisting job** | **ACCEPT** | Missing ephemeris path or module map refuses before input reads. Runner identity is required and its implementation digest is compared with the manifest pin. The candidate adapter preserves the combined gate’s other violations. The `'*'` subset-scope defect is fixed. The separate seal-brief use of `--report-only` is defective: **R11-3**. |
| **R10-5 — identity separation** | **CLOSED** | **ACCEPT** | In-memory calls to the actual checker refused both a superuser session under a restricted current role and a verifier with column-level `UPDATE`, each with exit code 4. Both identities, owner/builder memberships, and catalog-derived table/column writes are checked. |
| **R10-6 — one boundary contract** | **CLOSED** | **ACCEPT** | The fixed precheck is removed from job and writer. On a smooth one-degree/day crossing with one-arcsecond accuracy, the derived bound was 25 seconds: a 10-second offset passed; 26 seconds failed. Complete-job PostgreSQL regressions are present but were not run here. |
| **R10-7 — provisioning grants and ACL closure** | **CLOSED at source** | **ACCEPT_WITH_AMENDMENTS** | 1241 carries the 1240 backfill, necessary combined-gate reads/helpers, narrow publication UPDATE and legacy-window SELECT. Its effective table/column/function privilege checks reject missing and prohibited privileges within the declared namespace. Update stale comments saying roles are created *after* the window; the delegated sequence now creates them immediately before it. |
| **R10-8 — unknown enumeration budget** | **CLOSED** | **ACCEPT** | Ten unknowns with budget 1 now raise before `_slot_options` is called: **zero options materialised**, versus 512 previously. Forty unknowns likewise refuse before generation. Conservative unqualified fallback remains. A separate extractor defect affects (d): **R11-5**. |
| **Registry 1.1.0 and codec, #2897** | **CLOSED at source** | **ACCEPT** | Additive versions preserve old rows; the flat codec and applicability declarations remain suitable for binding. This does not activate numerical results. |
| **Option A / owner-only seal approval** | **Architecture acceptable; execution incomplete** | **ACCEPT_WITH_AMENDMENTS** | The delegated responses preserve separate identities, sole-owner approval and a passwordless sealer until the gate is proven. Correct **R11-3/R11-4** before executing the sealing procedure. |
| **Act 7, #2961** | **Acceptable at source** | **ACCEPT** | The declared verifier pair is narrowly recognised, unknown gochara/sealer resources are rejected, and verifier secret exposure is constrained to the named job. Actual IAM, deployment and negative-access receipts remain operational prerequisites. |
| **Measurement tooling, #2923** | **PARTLY** | **REJECT for extraction execution** | Budget handling and the additional frozen donor/tier identities are acceptable. The normal extraction path fails with Psycopg’s default transaction mode: **R11-5**. |

**Migrations table**

The five protected-file SHA-256 values match `EXPECTED_WINDOW_SHA256.txt` exactly.

| Migration | Reviewed result | Order / qualification |
|---|---|---|
| **1204** | **ACCEPT** | First protected file; hash `a0b267f7…`. |
| **1206, PC-4** | **ACCEPT** | Builder verification-table grants are removed. Hash `941c79f5…`. |
| **1232** | **ACCEPT** | Additive Moon-scope/domain completeness changes; hash `f2ef6406…`. |
| **1233** | **ACCEPT** | Anchor columns/checks; refuses pre-existing unanchored P1 rows. Hash `958b9117…`. |
| **1240** | **REJECT pending R11-1** | Current final bytes hash `c30fe5857…`. Included-grain checks are insufficient for the generation-wide all-NULL claim. |
| **1241 v3** | **ACCEPT_WITH_AMENDMENTS** | Apply through the routine route **after** the protected window. Backfills 1240 grants and adds its own. Correct obsolete role-order commentary. |
| **1234 / 1236 / 1242** | **No new source objection in this review** | Present in the archived refreshed ledger and composed stack. Production application at ledger IDs 919–921 remains steward-reported. |

The archived TODAY ledger contains 919 filenames. Comparing it with the integration tree found **no unselected, unapplied SQL predecessor numbered ≤1240**. This supports the packet’s predecessor claim against that snapshot; it is not a live production-ledger check.

The intended sequence is coherent: create the roles immediately before dispatch, allowing 1240’s guarded grants to fire; apply 1241 afterwards as the complete additive grant specification. If 1241 itself runs while a role is absent, its warning does not create a deferred grant—an additive follow-up is still required.

**New findings**

**R11-1 — Excluded rule-version records escape the generation-wide all-NULL gate. Blocks (a), (c).**

[1240’s `expected` CTE](/Users/Dev/madhav-l3/pravaha-a53am5/platform/migrations/1240_gochara_window_verification_gate.sql:375) selects only included P1–P4 grains. The `record_result_not_policy` arm at lines 547–556 checks records joined to those grains. The window-policy checks have the same restricted scope.

Meanwhile, the relationship-record FK and `ka_gochara_require_sealed_rule_path` require a **sealed** version, not a version included by this generation’s inventory.

A source-level counterexample is therefore:

1. Verify the included P3@1.1.0 grain.
2. Insert a structurally valid P3@1.0.0 record, where 1.0.0 is sealed but excluded as superseded.
3. Reuse an existing contact and coverage partition; supply consistent prerequisites/admission; set a numeric evidence result. A non-admitted record needs no window membership.

That record is outside the included-grain policy checks and attestations. Adding it need not change any contact, inventory, or included-grain dependency digest. My adapter probe confirmed that adding such an excluded-version numeric record leaves the included digest unchanged. I did **not** execute this attack against PostgreSQL.

No inspected combined-gate arm rejects the unexpected output grain. Consequently, the packet’s generation-wide statement that the database enforces all-NULL results is too strong.

**Closing change:** Reject materialised records/windows outside the generation’s explicitly permitted output grains, and enforce the manifest’s all-NULL policy across **all generation results**, independently of the expected-verification CTE. Add restricted-builder attacks using superseded versions and held paths, before and after verification, without introducing new contacts.

---

**R11-2 — P1’s anchor-set check is not complete independent record derivation. Blocks (c).**

[`verify_p1_anchors`](/Users/Dev/madhav-l3/pravaha-a53am5/platform/python-sidecar/services/gochara_kernel/record_verifier.py:231) collapses records into a set of `(lord, level)` per contact. It does not compare complete record identities or multiplicity. [`verify_p1_results`](/Users/Dev/madhav-l3/pravaha-a53am5/platform/python-sidecar/services/gochara_kernel/record_derivation.py:296) checks selected results, role/provenance/ruling and admission, but does not compare affected person or object role with independently derived values.

My isolated probes of the actual functions found:

- Four required anchored records passed.
- Adding a fifth record duplicating an existing anchor still passed.
- A P1 record supplied with the wrong affected person and object role passed the P1 result checker.

The surrounding P1 support, house and anchor checks do not close the affected-person omission. The schema allows, for example, `father` with `dasha_lord`; it does not enforce the class’s intended person.

There is also shared semantic implementation: both builder and P1 verifier call `permission.period_lord_relation`. Its `testimony` classification determines both which records the builder omits and which anchors the verifier removes from its expected set. A defect there can make both sides agree on the same omission.

These are **record-validation defects on a fixed contact population**. They are not covered by the accepted disclaimer about exact contact/retrograde multiplicity.

**Closing change:** Derive the complete P1 record identities and semantic fields independently, including person, object role, anchor, prerequisite truth and admission; compare both directions with the required cardinality. Remove the common builder/verifier permission computation from the independent check. Add duplicate-record, wrong-person and shared-permission mutation tests.

---

**R11-3 — The prescribed seal brief is neither implemented nor correctly bound to approval. Blocks (c).**

The [provisioning runbook §6](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55k/00_ARCHITECTURE/briefs/pravaha/runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md:134) says the verifier’s `--report-only` step produces a brief containing a clean combined gate, emits an artifact/hash, and binds subsequent sealing to that brief.

The submitted job instead explicitly does:

```python
gate_all = [] if report_only else candidate_gate_on_candidate_manifest(...)
```

It skips the gate while still labelling `gate_source` as the combined function. The CLI produces its ordinary report, not the specified approval artifact, ledger evidence and canonical brief digest.

There are two further contract gaps:

- The runbook requires the raw SQL combined function to return zero on a **candidate** row. That contradicts the correctly disclosed need for the candidate adapter.
- Recomputing only a gate result cannot establish that the approved candidate is unchanged. Two different valid candidates can both produce `[]`.

The promised approver login/run ID are also not fields of the inspected generation-seal table.

**Closing change:** Implement and review the verifier-produced brief and sealing workflow. Evaluate the candidate adapter, read the persisted attestations, and hash a canonical **complete approval payload** containing the specified manifest, generation, output/attestation identities, policies, code and ledger evidence. After owner approval, recompute that payload under the sealing locks and refuse a mismatch; then publish and execute the authoritative SQL seal checks atomically. Implement the promised approval receipt, or explicitly revise its storage contract to a durable receipt linked to the seal. Provide the necessary narrow read privileges.

A changed candidate whose gate remains empty must invalidate the old approval.

---

**R11-4 — Act 2b’s secret command is invalid, and the password pipeline can conceal failure. Blocks execution of (c).**

The same runbook, line 124, prescribes:

```text
gh secret set gochara-sealer-db-url --env gochara-seal --body-file -
```

GitHub secret names cannot contain hyphens. `gh secret set` accepts stdin when `--body` is omitted; it has no `--body-file` option. The intended form is `gh secret set GOCHARA_SEALER_DB_URL --env gochara-seal`, receiving the DSN through stdin. [GitHub naming rules](https://docs.github.com/en/actions/reference/security/secrets#naming-your-secrets), [CLI reference](https://cli.github.com/manual/gh_secret_set).

The §2 subshell also lacks checked exits or fail-fast handling. A failed password or secret-store command can be followed by `unset PW`, leaving a successful final shell status.

**Closing change:** Correct the secret name and stdin invocation consistently; explicitly check both operations, stop on failure, and implement secret-safe cleanup and the documented partial-failure rollback. Retain `PASSWORD NULL` until the human gate has been proven.

---

**R11-5 — The 4.1 extractor fails during transaction configuration. Blocks (d) only.**

[`dump_extract.py`](/Users/Dev/madhav-l3/pravaha-b-measure/platform/python-sidecar/services/gochara_eval/dump_extract.py:280) uses a normal `psycopg.connect(dsn)` connection. `read_manifest_orb` sets `read_only=True` and executes its SELECT, starting a transaction. `read_av_donor_identity` then sets `read_only=True` again.

Psycopg rejects that assignment inside an active transaction, even when the value is unchanged. The later helpers and `dump_rows` repeat the same pattern. The connection defaults to `autocommit=False`. [Psycopg connection documentation](https://www.psycopg.org/psycopg3/docs/api/connections.html).

Using the actual `main` control flow and the installed Psycopg 3.3.4 setter with a controlled transaction-state adapter produced:

```text
ProgrammingError: can't change 'read_only' now:
connection in transaction status INTRANS
```

Only the manifest query had executed; rollback and close followed. The submitted PostgreSQL fixture uses `autocommit=True`, masking this failure.

**Closing change:** Configure transaction characteristics once, before the first query. Keep manifest/input reconciliation and extraction in one consistent read-only snapshot rather than committing between checks. Add a complete extraction regression using the CLI’s normal non-autocommit connection mode.

**Independence, freshness and the candidate-gate claim**

P2–P4 now have meaningful independence from the builder’s record implementation: their obligations, semantic classifications, prerequisites and admissions are re-derived rather than accepted from surviving output. They still depend on the same bound facts and sealed registry, and on **stored contacts certified through occupied-time union comparison**. That is compatible with the disclosed contact-certification limits; it is not proof of exact contact multiplicity. P1 needs R11-2.

An underivable path produces no new attestation. For a fresh candidate, the missing required verification closes the gate. **A failed later run does not itself revoke earlier current attestations.** That retained-attestation behaviour is disclosed and acceptable; the combined gate, not an isolated run-status phrase, determines present eligibility.

For included grains, `inputs/2` now covers all three numeric relationship-record result fields, valence, the listed semantic fields, prerequisites, and every generation contact used by certification. I found no further omitted numeric result column within that covered grain. Its generation-wide hole is R11-1.

It is nevertheless **not a hash of every record field**: `source_text`, `source_page`, `source_fact_ids`, `temporal_support_grain`, coverage-reference/facts fields and `fixture` are omitted. Some omitted fields have separate structural checks; citation payloads are not thereby independently certified. The packet should replace “every record field” with the actual covered-field claim. Inventory/registry/L1 freshness also relies on the composed 1206/1232 and immutable-registry checks, not `inputs/2` alone.

Binding **all generation contacts** is sound and explicitly disclosed. It conservatively invalidates other classes’ attestations when one class’s rebuild changes the shared contact population. Verify every class after the final build.

For the **persisting job**, the candidate-gate wording is accurate: three spurious published-only violation categories are removed, their predicates are evaluated against the candidate, the candidate convention mismatch is checked, and other SQL violations remain. The authoritative seal evaluates the published row. This is a Python adaptation of the gate, not literal SQL-function identity. I found no additional predicate lost in that adaptation. R11-3 concerns the separate report-only approval flow.

**What the composed rehearsal establishes**

The integration’s relevant writer/verifier modules and 1240 are byte-identical to `d4609f181`; its 1241 matches `089c65f27`. Its inspected tests exercise:

- Restricted build/rebuild, real verifier login, first seal, refusal before verification and replay.
- Both seal guards, migration ownership/default privileges, legacy-window presence and production-shaped chart RLS.
- Combined-gate access, narrow publication privileges, prohibited-privilege refusals and individual grant necessity.
- Omission, numeric-result, runner-identity, subset-gate and contention attacks.

The late-role test reproduces the **missing-grant state by stripping privileges**, then applies 1241. This is useful backfill evidence, not an execution receipt for production role creation.

The reported **81 passed / 0 failed / 0 xfailed**, and the mechanical **43/38 assertions**, remain author execution evidence. They do not establish the new attacks above, the approval-artifact protocol, actual cloud isolation, production authentication, or full-volume production performance. Rehearse again after the closing changes and refresh the final migration hashes.

**Owner safeguards and operational prerequisites**

The delegated documents do not weaken the intended approval boundary: the owner remains the sole approver; an agent-usable identity is excluded; self-review and admin bypass are disabled; the sealer remains without a password until the gate proof. The verifier produces the brief, and the sealer rechecks it. Those are acceptable requirements, subject to implementing R11-3 and correcting R11-4.

Separately, the owner still must perform the authorised provisioning sitting, prove the environment gate and secret isolation, establish the data-plane-owned L1 read ACLs, dispatch the protected window, apply 1241, deploy the pinned verifier job with `GOCHARA_RUNNER_COMMIT=DEPLOY_SHA`, and obtain actual verification/seal receipts. These are operational prerequisites, not evidence of additional source defects.

For **(d)**, “keep” settles the daśā plurality choice. The freeze must record its actual observed tiers/counts and policy identity, preserve the partial denominator/ceiling treatment, and bind donor-row identity. The 4.1 manifest still needs the required shared AM-16 ephemeris identity covering all consumed bodies, including the Moon, and the consumed horizon. A backend probe alone is insufficient.

Stage 1 must be completed and committed before extraction; Stage 2 must bind the extract bytes before inspection. The 4.1 result remains diagnostic-only, with `t_honesty=UNVERIFIABLE`, `pass:false`, and no flip eligibility under v2.3.

**Ranked amendments**

| Rank | Required closing change | Blocks |
|---|---|---|
| **1 — R11-1** | Generation-wide output-selection and all-NULL checks; excluded-version/held-path attacks refused with unchanged contacts. | **(a), (c)** |
| **2 — R11-2** | Complete independent P1 record derivation; duplicate, wrong-person and shared-permission mutations detected. | **(c)** |
| **3 — R11-3** | Implement the canonical approval brief, locked identity recheck, authoritative publish/seal transaction and approval receipt. | **(c)** |
| **4 — R11-4** | Correct secret invocation and fail-closed password/secret handling. | **(c)** |
| **5 — R11-5** | Configure the extractor transaction once; test the complete non-autocommit path. | **(d) only** |

Nonblocking documentation corrections: reconcile 1241’s role-order comments and the rehearsal plan’s obsolete heads/status statements; narrow the “every record field” claim. The disclosed smooth-motion, sub-60-second, boundary-tolerance, contact-union and retained-attestation limits remain accepted for this all-NULL milestone.

**Step lines**

- **(a) Protected window 1204 → 1206 → 1232 → 1233 → 1240: BLOCKED BY R11-1.**
- **(b) Binding registry versions 1.1.0: UNBLOCKED at source.**
- **(c) Independently verifiable all-NULL first ‘5.0’ candidate: BLOCKED BY R11-1, R11-2, R11-3, R11-4.**
- **(d) ‘4.1’ diagnostic measurement: BLOCKED BY R11-5, S1-REQ-EPHEMERIS, and the uncompleted Stage-1/Stage-2 freezes. R10-8 is closed.**

**What I could not verify**

Independent selected-suite results were **254 passed, 12 skipped, 275 deselected**, plus the in-memory probes described above. Database- and filesystem-writing fixtures were excluded. No PostgreSQL end-to-end, ACL or concurrency suite was executed by me.

I did not verify live production ledger IDs, deployment revisions, GitHub checks/merge status, IAM, environment protections, secrets or credentials. The production application/deployment facts remain steward-reported. Review used the pinned local refs; no fetch was performed.

No file was written, no git write command was run, and no production database was contacted.