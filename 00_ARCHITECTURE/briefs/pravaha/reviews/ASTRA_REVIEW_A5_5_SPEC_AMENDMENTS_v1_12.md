---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.12"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: "a97a704cb (campaign/pravaha)"
reviewed_heads:
  campaign/pravaha: a97a704cb2f3ecc6a4880820130c1870900611eb
  origin/main: 9791d5c1a42210ca3e0397c1dddcff3f647d53d0
  "WRITER origin/pravaha/a53-am5-inventory": 39ca825b32c2e1df76dbe93136b00d1b0564bc30
  "PR #2949 origin/pravaha/b6-1241-verifier-sealer-grants": 5e080e9c157e3d97c596b8913c19e06508895682
  "PR #2867 origin/pravaha/b6-am5-inventory-migration": e4d31c9ef82aa2e3874cd2095d295622f6756bf6
  "PR #2919 origin/pravaha/b6-am21-p1-anchor-1233": 728b91501ad5c3b653a6130c7cac792b381871da
  "PR #2963 origin/pravaha/b6-gochara-role-provisioning-oneshot": 4113dfe2df0a752a344d291fe588029ab9579b52
  "PR #2961 origin/pravaha/b6-act7-verifier-secret-isolation": 84331f7042825bd7e86b5ea8909173c3b8e0a9bc
  "PR #2975 origin/pravaha/b6-gochara-seal-workflow": 8b65fc4c775244aee31bd30f233eeb8fd66e9474
  "PR #2976 origin/pravaha/b6-gochara-verification-job-def": ef3a1ade17b9b169222717f703a223104bca7cad
  "PR #2952 origin/pravaha/b6-composed-rehearsal": 666645cc40f5b1d3ef681fe64ffe33d0fe8c7c8f
  origin/pravaha/b6-composed-rehearsal-integration: 4be2e2369cb17c644d71eaecd50db7c62304b083
  "PR #2923 origin/pravaha/b6-stage1-candidate-measurement": d52cbea971944454785480398aefa5da568b30f8
  "PR #2897 origin/pravaha/b6-am13-kernel-registry": 2839fe03a8c4a80e008ee89603e973fece6bde28
  "PR #2897 merged commit": 8cf05f507de0a2f8047ea32640ab50eeb16cf65c
comparison_commits:
  round_12_writer: bf369fcaa8bf399e3f23667d728e8ee56b216479
  round_12_measurement: 0855876eb0a5e17da02a5dd599c29a0f33f5e2c5
observed_later_heads_NOT_REVIEWED:
  writer: 7e81f28705d6ca994fc46cb6476620f757bcdb45
  "PR #2963": 9bbad986ab755044412354e437de52b37a219ada
  "PR #2975": 09d5eecad9d5f493d829fc7513694a1b7235db28
  "PR #2976": 273f114a91fa118b3da2b5093e3a946fd2b636fb
  "PR #2952": 950872acade5f348ac16396150f57c429812d8aa
  composed_integration: 78f98389597dd473b02bd81f32678a31fd19e440
authority: "Review only; authorizes nothing."
---

**Verdict**

**REJECT the submitted round-13 packet.** The original boundary omissions and provisioning defects are substantially repaired. The submitted sealing workflow nevertheless rejects the real verifier output, does not establish the brief producer’s execution/commit identity, and relies on a database state check that does not serialize every covered write through COMMIT.

These are source defects. **This packet is not held only for operational acts and execution receipts.**

Numerical activation remains **DISABLED**. Registry binding remains accepted. The all-NULL build and independent-verification work retains its earlier acceptance within the declared scope; that does not establish a completed approved seal.

The remote-tracking branches listed separately above advanced during this review. This verdict applies to the **submitted pinned commits**, not those later revisions.

**Item status**

“CLOSED” below closes the original finding; it does not override a new finding elsewhere in this review.

| Item | Status | Verdict | Exact remaining change |
|---|---|---|---|
| Codex R12-1 — omitted candidate facts | **CLOSED** for the named omissions | ACCEPT | Coverage, publication identity and search inputs are now bound; legacy projections are forbidden. The newly identified COMMIT race is **R13-2**. |
| Codex R12-2 — executable approval-consuming workflow | **PARTLY** | REJECT | The caller exists, but fix its actual wire contract, producer provenance and approval/retry handling: **R13-1, R13-3, R13-4**. |
| Codex R12-3 — provisioning permissions, cleanup and admin URL in argv | **CLOSED at source** | ACCEPT | Version Manager supports the commands used; URL is parsed into process environment; temporary IAM removal covers terminal states. Operational cleanup receipts remain. |
| Codex R12-4 — failed activation leaves sealer active | **CLOSED for the identified failure path** | ACCEPT | Transactional postconditions and compensating reset now exist. Correct the runbook’s recovery evidence and interruption claims: **R13-6**. |
| Codex R12-5 — wrapper converts failure to success | **CLOSED** | ACCEPT | The complete staging unit returns nonzero, and the documented caller stops. |
| Fable F-R12-1 — sealing workflow and act-6 definition absent | **PARTLY** | REJECT | Both are written and reviewed here; the sealing chain still requires **R13-1, R13-3, R13-4**. |
| Fable F-R12-2 — coverage/snapshot/obligation/interval omitted | **CLOSED** for the named omissions | ACCEPT | All four are covered. Atomicity remains a separate **R13-2** defect. |
| Fable F-R12-3 — dependence on reading `pg_authid` | **CLOSED at source** | ACCEPT | Recorded state plus authentication probes replace the forbidden read. Recovery prose still needs **R13-6**. |
| Fable F-R12-4 — verifier-persisted brief required | **PARTLY** | REJECT | Fabricated and ordinarily stale digests are rejected. Enforce latest-brief/state stability through COMMIT and bind producer provenance: **R13-2, R13-3**. |
| Fable F-R12-5 — sealer identity self-check | **PARTLY** | ACCEPT_WITH_AMENDMENTS | Reject owner-role membership and column-only verification-table writes: **R13-5**. |
| Fable F-R12-6 — session rendering pinned | **CLOSED at source** | ACCEPT | Python and SQL pin the relevant settings. PostgreSQL execution was unavailable to this reviewer. |
| Fable F-R12-7 — documentation corrections | **PARTLY** | ACCEPT_WITH_AMENDMENTS | The packet improves substantially, but current runbook/design/rehearsal sections still contradict the code and ruling: **R13-6**. |

Additional unit verdicts:

| Unit | Verdict | Scope |
|---|---|---|
| #2975 sealing workflow and four scripts | **REJECT** | R13-1, R13-3, R13-4. |
| #2976 verification-job definition | **ACCEPT_WITH_AMENDMENTS** | Suitable dispatch-only structure; immutable image/execution identity and deployment verification must join the sealing contract. |
| #2963 provisioning workflow/scripts | **ACCEPT_WITH_AMENDMENTS** | Original code defects repaired; execution/recovery instructions must be reconciled before use. |
| #2961 secret-isolation preflight | **ACCEPT at source** | Live IAM, secret bindings and invocation evidence remain operational prerequisites. |
| #2952/composed integration | **ACCEPT_WITH_AMENDMENTS as evidence** | Useful database composition evidence; not end-to-end workflow qualification. |
| #2923 measurement tooling | **ACCEPT for (d)’s reviewed tooling scope** | Does not discharge ephemeris or freeze prerequisites. |

I re-exercised the feasible Python/shell reproductions using exact source loaded into memory, with explicit query adapters or command shims. These were **not PostgreSQL executions**.

| Attack/check | Reviewer result |
|---|---|
| Excluded-version P3 and held P5 numeric records | Python generation-wide check refuses both; SQL independently checks the whole generation. |
| Duplicate/missing P1 anchor, wrong affected person/object role, duplicate prerequisite | Refused by the real verification functions using controlled input adapters. Independent-import guard passes. |
| Mutation of each of the ten output/search-input table contributions | Each changes the real Python output identity digest. |
| Coverage-disclosure mutation | Changes the real coverage identity digest. |
| Real verifier CLI output passed to #2975 checker | **Refused: incompatible envelope.** |
| Real CLI JSON represented as Cloud Run structured logging | **Extractor finds no brief.** |
| Free-typed note, malformed mechanical note, another actor | Refused by the sealing caller. |
| Note/digest/commit with trailing newline | Refused by the sealing caller’s `\Z` checks. The workflow checker still has weaker `$` validation; see R13-1. |
| Approval naming another run/attempt | Refused by the approval extractor. |
| Approval-history ordering reversed | Changes which review is accepted; implementation depends on array order. |
| Generation, first secret write, second secret write, rollback failure | Staging unit returns **11, 12, 13, 14**, respectively; success returns 0. |
| Measurement’s four readbacks on one non-autocommit connection | Exit 0; four queries after one READ ONLY/REPEATABLE READ configuration. Old INTRANS failure and unconfigured-reader refusal reproduced. |
| Fabricated digest, another manifest, superseded brief, SQL state changes/settings | Assessed from SQL and author tests; **not independently executed in PostgreSQL**. Conclusions and exceptions follow below. |

**Migrations**

The five protected migration hashes match `EXPECTED_WINDOW_SHA256.txt`. All six files below are byte-identical in the submitted integration commit. The writer’s kernel modules and both job entry points also match the submitted writer commit.

| Migration | SHA-256 | Verdict |
|---|---|---|
| 1204 | `a0b267f7ef6002a1997c30d34595ec3b86147ca617bf70ef8a05de55b8407ca1` | ACCEPT |
| 1206, PC-4 folded | `941c79f59f2d3d3125dc5ca680430d4a91a7dcddb53fc6daa9a9da8819e410d7` | ACCEPT |
| 1232 | `f2ef6406604b819d5f443e32c1e70914f2337ead8867f12e0aecd96d13f1ec44` | ACCEPT |
| 1233 | `958b911703eee3528e1db75624984020964b8d31fe3fe286d64071368bd5a705` | ACCEPT |
| 1240 | `db27905a3b4e1478b9b75bf6f2f39aef5bd2eaefac51e282ad789911c82c1ae8` | **REJECT: R13-2** |
| 1241 v6 | `6938d589a44db5308ccec24201092b71c02ee9282b0f0a3152e67e6d0592962e` | ACCEPT_WITH_AMENDMENTS; revalidate against corrected 1240 |

1241 contains **62 origin-1241 privilege entries: 25 verifier and 37 sealer**, in addition to its 1240 backfill. Its revoke-one tests target the full verification → brief → seal → replay flow. Their reported execution supports necessity within that flow; I did not independently execute the privilege matrix.

The intended verifier write surface is now:

- Inventory-verification table: INSERT.
- Window-verification table: INSERT and guarded pre-seal DELETE.
- Brief table: INSERT, append-only.

It receives no builder-output write or seal capability. Database ACLs restrict the principal; they cannot restrict that principal to the CLI’s `--brief` mode specifically.

The sealer’s publication UPDATE remains correctly restricted to `status`, `published_at`, `content_digest`, and `row_counts`. Legacy-window and migration-ledger reads are column-restricted.

The exact-ACL post-check rejects missing and unexpected effective table/column privileges and unexpected `ka_gochara_*` function execution privileges in its enumerated scope. It is **not** a database-wide privilege or role-membership audit: L1 grants, other namespaces, other relation kinds, and latent `NOINHERIT` memberships require separate treatment.

Composition remains sound for the existing guarded tables: 1153’s publication/coverage/membership guard precedes 1206’s completeness guard and 1240’s window guard. Receipt constraints are additive. Raw SQL replay inserts no new seal row and therefore requires no new receipt; existing BEFORE guards still run. Pre-1240 seals remain sealed and honestly unverified. The new receipt first-seal check prevents the ordinary later graft of an approval receipt onto such a seal.

Roles must exist when grants are applied. A warning for an absent role is not deferred provisioning. If 1241 is recorded while a principal is absent, a later additive migration is required.

**The sealing chain**

| Layer | What it enforces | What it does not establish |
|---|---|---|
| 1153/1206/1240 gates | Permitted output grains, all-NULL record/window results, legacy-projection absence, required verification, input/content agreement and manifest-pinned implementation identity. | Every covered legacy write is serialized through seal COMMIT. |
| Persisted brief table | Append-only digest record; trigger overwrites manifest, state digest, database login and timestamp. | That the supplied digest was honestly computed; that the row came from a particular Cloud Run execution or GitHub attempt. |
| Receipt constraints | First seal requires a matching receipt; receipt requires its seal; digest must match the latest persisted brief observed by the check and its observed state. | GitHub approval authenticity, environment protection, or unconditional latest-state equality at COMMIT. |
| Receipt attribution trigger | `sealed_by = session_user`; `approved_at = transaction_timestamp()`. | Human identity, AI-session identity, or GitHub approval time. |
| `execute_seal` | Explicit transaction, milestone policy, identity checks, run/attempt comparison, actor-note check, recomputation, publication, seal and receipt. Controlled failures roll the transaction back. | Producer execution identity; complete identity-drift detection; certainty after a lost COMMIT acknowledgement. |
| #2975 | Main-ref dispatch, retained brief, approval lookup, environment-labelled sealing job, caller invocation. | A functioning transport on submitted bytes; authenticated producer provenance; documented approval-history ordering. |
| Operational configuration | Once verified, GitHub can pause the environment job, restrict branches/reviewer and prevent admin bypass. | The workflow YAML alone does not prove those settings exist. |
| Nothing in this design | — | Independent human judgment, which hand operated the shared account, or correctness of a compromised trusted verifier/sealer. |

A direct holder of the sealer credential can still submit a **genuine current verifier-persisted digest** with invented GitHub metadata. The database does not consult GitHub. That is the disclosed trusted-workflow boundary, not a reason to demand a second human account.

Under the owner’s ruling, approval records use of the owner’s account under delegated authority. It can bind the declared digest to a workflow ceremony. It does **not** prove that the owner personally read it, that a distinct human approved it, or that the approving agent reasoned independently. `github.triggering_actor` identifies the dispatcher/rerunner account; it is not evidence identifying the human or agent who reviewed the brief.

The owner ruling, workflow summary and packet say this honestly. **Not every document does:** the runbook frontmatter still reserves “every seal approval” to the owner “in person.”

The sealer credential’s actual lifetime is also broader than “only in the seal job”:

1. Act 2b generates it in the steward’s process.
2. The full DSN persists in the `gochara-seal` environment secret.
3. The password temporarily also persists in the **ungated cutover environment**, until verified deletion.
4. The provisioning runner receives that staging password and activates it.
5. #2975 exposes the DSN to its final sealing step and child processes after the environment job starts.

Neither the lasting secret nor the database password expires when a sealing run ends. Staging deletion is procedural and has no automatic TTL. The two-hour expiry applies to the temporary **Secret Manager IAM power**, not to the sealer password.

**New findings**

**R13-1 — The actual producer, log transport and consumer are incompatible. Blocks (c).**

The writer’s `pipeline/orchestrator/verification_job.py:87–104` emits:

```json
{"brief": "...", "sha256": "...", "persisted": "..."}
```

The checker accepts **exactly** `{"brief", "sha256"}`. Its rejection is unconditional for the submitted successful CLI output. [Checker, lines 55–69](https://github.com/Marsys-Technologies/Madhav/blob/8b65fc4c775244aee31bd30f233eeb8fd66e9474/platform/scripts/gochara_seal_brief_check.py#L55)

Independently, the extractor reads only `textPayload` or a string in `jsonPayload.message`. The verifier emits a JSON object without a `message` wrapper. Cloud Run parses structured stdout JSON into the root `jsonPayload`; the extractor therefore sees no brief in the documented representation. This was also reproduced with the exact extractor and a structured-log adapter. [Cloud Run structured logging](https://docs.cloud.google.com/run/docs/logging#use-simple-text-vs-structured-json-in-logs)

The tests supplying an old two-key object inside `jsonPayload.message` do not exercise this interface.

Additional transport facts:

- Identical duplicate entries are accepted because the extractor checks `len(set(hits))`, despite prose promising exactly one entry.
- Distinct entries and split/truncated JSON fail closed.
- The suggested “chunked emit mode” is not implemented by these scripts.
- The checker’s SHA/digest regexes still use `$`. The downstream sealing caller correctly rejects trailing newlines, so this is not a demonstrated seal bypass.

**Closing change:** define one versioned envelope and serialization contract shared by the actual CLI, Cloud Logging representation, extractor and checker. Carry and validate the persisted brief identity; preserve numeric types in canonical payloads; use strict full-string validation. Add a cross-component test starting from the **real CLI’s output**, plus structured logs, duplicates, splits, truncation and newline cases.

**R13-2 — The deferred state check does not make the approved state stable through COMMIT. Blocks (a) and (c).**

1240’s digest reads build coverage and legacy projections, but those reads do not lock out every writer. Migration 1216 grants the builder INSERT/DELETE on `kala_gochara_coverage`; that legacy table has no chart-lock write trigger. The post-publication Python recheck merely moves the last observation later.

The new brief attestation trigger also does not itself acquire the chart lock. Its comment assumes the caller already holds it. A verifier using its granted INSERT directly is not mechanically bound to that protocol. [1240 digest, attestation and receipt checks](https://github.com/Marsys-Technologies/Madhav/blob/39ca825b32c2e1df76dbe93136b00d1b0564bc30/platform/migrations/1240_gochara_window_verification_gate.sql#L655)

A deterministic adversarial schedule follows from the source:

1. Sealer transaction publishes, inserts its seal and valid receipt.
2. Sealer executes `SET CONSTRAINTS ALL IMMEDIATE`; all queued receipt checks pass.
3. A second connection, as the builder, inserts a valid build-coverage partition with a fresh key, copying the other required fields from an existing partition. This requires neither UPDATE privilege nor disabling triggers.
4. That connection commits.
5. Sealer commits. No changed receipt row queues another state check.

The coverage state at seal COMMIT now differs from the approved state. The same early-check schedule can admit a later brief inserted directly by the verifier.

PostgreSQL explicitly allows `SET CONSTRAINTS` to execute deferred constraint triggers early. Even without that command, a final snapshot read is not a lock against an unguarded concurrent writer. This is a **source-derived concurrency finding, not a PostgreSQL reproduction performed here**. [PostgreSQL 15 constraint timing](https://www.postgresql.org/docs/15/sql-set-constraints.html)

**Closing change:** make all writes affecting the claimed boundary participate in database-enforced serialization, including governed legacy coverage/projections and brief insertion. Protect the state after sealing where immutability is claimed. Preserve the established lock order. An equivalent immutable sealed-state design would also work.

Add real-role, two-connection tests for changes after the last Python check and after forced immediate constraint checking. The test must demonstrate blocking/refusal through COMMIT without owner privileges or disabled triggers.

**R13-3 — The workflow does not bind the brief to the actual verifier execution at this commit. Blocks (c).**

#2975 executes a mutable named Cloud Run job and passes `--sealing-commit=$GITHUB_SHA`. It does not verify that execution’s resolved image or producer commit.

The supplied sealing commit proves what the caller requested, not which code produced the brief:

- `code.verification_runners` comes from previously persisted verification rows.
- `persist_brief` records the running brief producer’s identity, but the receipt check does not compare that identity with the sealing revision.
- The checker does not validate producer identity. An older runner identity was accepted in my exact-function probe.
- No execution ID, run/attempt nonce or specific persisted `brief_id` is bound into the approval contract.

#2976 separately sets the image tag and `GOCHARA_RUNNER_COMMIT` during deployment. That does not establish that the job later executed by #2975 still has that definition. Its concurrency group also does not coordinate with the sealing workflow.

The narrow log view limits **read access**; it does not authenticate who created an entry. A principal with `logging.logEntries.create` can supply resource and label fields. A view accessor alone cannot inject logs, and I did not establish that any particular production principal can. Nevertheless, the source must not treat matching log labels as producer attestation. The persisted-brief constraint prevents an arbitrary invented digest; it does not distinguish a replay of a genuine older same-state brief. [Cloud Logging write API](https://docs.cloud.google.com/logging/docs/reference/v2/rest/v2/entries/write)

**Closing change:** bind and verify the actual producer commit, immutable image digest, execution identity and persisted brief identity. Carry them through the retained envelope and sealing check. Verify the executed resource’s configuration/status, not just a separately deployed job name. Define fresh-attempt versus safe-reuse behavior explicitly; an older same-state execution must not silently masquerade as the newly dispatched execution.

**R13-4 — Approval selection and artifact handling lack a sound retry contract. Blocks acceptance of (c)’s workflow.**

`gochara_seal_approval.py:48` selects `mine[-1]` with the assertion that GitHub returns oldest-first history. The published endpoint does not document that ordering or expose an attempt field in its illustrated review record. My probe confirms that reversing the array changes the decision. [GitHub review-history endpoint](https://docs.github.com/en/rest/actions/workflow-runs#get-the-review-history-for-a-workflow-run)

Run and attempt matching currently comes from the **comment text**. That is useful, but should not be described as independently verified API attempt metadata.

Retry behavior is incomplete:

- A full rerun uses the same artifact names. If the prior artifact remains, upload-artifact’s default behavior rejects another upload with that name.
- A seal-only rerun can consume the previous brief job’s artifact; it needs an explicit reuse policy and a fresh valid approval.
- Cancellation of the GitHub wait does not prove cancellation of the Cloud Run execution.
- Cancellation or connection loss around COMMIT requires receipt/state reconciliation; a failed workflow alone does not prove rollback.

Artifact immutability is useful, but needs explicit attempt identity. [Artifact naming and overwrite behavior](https://github.com/actions/upload-artifact#inputs)

**Closing change:** remove the unsupported ordering assumption. Select an unambiguous current approval using supported evidence; where the API cannot distinguish competing records safely, refuse and require a fresh workflow run. Bind artifacts to explicit run/attempt identity. Test full reruns, seal-only reruns, rejection histories, cancelled executions and ambiguous COMMIT outcomes.

**R13-5 — The adopted sealer self-check omits two prohibited capabilities. Blocks closure of F-R12-5 before sealing.**

`seal_flow.check_sealer_identity` checks membership in builder and verifier, but does not perform the verifier’s owner-role membership check.

Also, `_write_surface` excludes both verification tables by default. The sealer then checks those tables only with `has_table_privilege`. Consequently, a column-only INSERT/UPDATE grant on a verification table escapes this check. [Sealer identity check](https://github.com/Marsys-Technologies/Madhav/blob/39ca825b32c2e1df76dbe93136b00d1b0564bc30/platform/python-sidecar/services/gochara_kernel/seal_flow.py#L144)

A controlled query adapter confirmed that the function accepts these modeled conditions and issues neither the owner-membership query nor verification-column privilege queries.

The intended provisioning starts with no memberships, and 1241’s column ACL check is stronger at migration time. Those reduce operational exposure; they do not complete the adopted runtime requirement.

**Closing change:** reject membership in every owner role, including `NOINHERIT` membership, and inspect verification-table column privileges. Add real-login negatives for both conditions.

**R13-6 — Current operational documents still contradict the implemented arrangement. Blocks reliable execution of the affected acts.**

Concrete contradictions at campaign `a97a704cb`:

- Runbook frontmatter says every seal approval is the owner’s “in person”; the ruling and body authorize the steward.
- The ordered sequence treats acts 1 and 2a separately, and act 2a requires the sealer to be absent. #2963’s `create-roles` stage already performs **both**.
- The act-2b example supplies a Cloud Run **socket** DSN. #2975 starts a **TCP loopback** proxy and requires `@127.0.0.1:5432/<db>`.
- Recovery sections still require evidence from `rolpassword IS NULL`, although the chosen admin route’s inability to read it caused F-R12-3.
- Act 8 still describes only two verifier write tables.
- Runbook §6 and the **current** design v1.1 still say attribution fields are overrideable defaults and that the sealer can use any well-formed digest. The submitted trigger and persisted-brief check have already changed both facts.
- Design v1.1 still describes seven output tables, the old two-key envelope, and implemented boundary changes as a plan.
- Rehearsal plan §0’s modes row still names `c30fe5857…`; M4 still treats the folded PC-4 change as open.
- Act 6 says the isolation gate passes “in the deploy,” but #2976 does not invoke it.
- Act 12 requires a prior job execution, while the opening sequence places it before the first execution without specifying a bootstrap run.
- `gochara-seal-gate-proof.yml` remains absent from the submitted campaign and new workflow branches.

**Closing change:** reconcile the operative sections, not just append another correction table. Specify distinct verifier/sealer DSN forms, combined role creation, the actual recovery proof, three-table verifier writes, current receipt enforcement, explicit preflight execution, and the bootstrap execution preceding act 12. Author and review the required no-secret gate-proof workflow.

Ordinary failure compensation is improved. Claims that cleanup runs on **every** cancellation/interruption remain too strong: SIGKILL, runner loss and an external mutation whose acknowledgement is lost can leave unknown state. Require inventory/reconciliation of roles, secret versions and active credentials after such outcomes; do not infer safety solely from an absent final log line.

**State-digest completeness, determinism and cost**

The SQL function now covers the ten output/search-input tables, both verification tables, build coverage and manifest identity, plus legacy-projection absence. I found no further omitted generation-scoped result table consumed by this P1–P4 all-NULL path.

Its claim must retain these boundaries:

- `created_at` is excluded; coverage `computed_at` is included.
- AM-4 on-demand coverage is deliberately excluded.
- Immutable global objects/contact identities are bound by reference.
- Enrichable sky-event substrate is not covered and is not consumed by this candidate verification path.
- Publication status/digest/counts are normalized or excluded because publication writes them. In particular, the publication coverage count still includes on-demand rows, so the approved digest does not mean every publication metadata byte is fixed.
- The SQL state digest is not the full approval-payload digest. Migration-ledger evidence, disclosures and workflow/code assertions additionally depend on the trusted Python recomputation.

For stored values on the same PostgreSQL database, SQL ordering is explicit `COLLATE "C"`, and TimeZone, DateStyle, IntervalStyle and `extra_float_digits` are pinned. JSONB text avoids key-insertion-order dependence. The Python payload pins the same rendering settings; its row queries use database-default collation, which is stable within this database but is not an explicit portable ordering contract.

This is a semantic-state identity, not a cross-version or arbitrary-database byte-canonicalization guarantee. Numeric rendering and transport must be tested together; the CLI’s `default=str` also deserves a Decimal round-trip test.

Cost remains unqualified. The SQL implementation sorts and concatenates **entire table JSON streams** with `string_agg`, then converts/hashes them. This can consume substantial memory and encounter PostgreSQL’s field-size limit; it is not a streaming hash. Brief persistence, the early seal check and the deferred check perform repeated state scans, alongside Python recomputation. [PostgreSQL limits](https://www.postgresql.org/docs/15/limits.html)

Timeout or allocation failure ordinarily aborts the transaction; it does not silently skip the check. However, the old rehearsal’s sub-second seal timings do not qualify this new full digest at complete-generation volume. Measure bytes, runtime, memory and lock duration. Cloud Run’s **8 GiB/2 CPU/7200 seconds** are disclosed starting values, not demonstrated capacity; #2975’s brief wait is only **45 minutes**, and its sealing job **30 minutes**.

**Provisioning and job-definition assessment**

The Cloud SQL socket approach in #2976 is supported: `--set-cloudsql-instances` supplies the configured instance connection and the verifier DSN can use its `/cloudsql/...` socket. The actual DSN shape, mounted instance and login must still be proven together. This does not make that socket DSN suitable for the GitHub sealer’s TCP proxy. [Job deployment flags](https://docs.cloud.google.com/sdk/gcloud/reference/run/jobs/deploy), [Cloud SQL socket connections](https://docs.cloud.google.com/sql/docs/postgres/connect-run#connect_with_unix_sockets)

I independently asserted equality of the names in #2975, #2976 and #2961: all are **`gochara-verification-job`**. That closes the present cross-ref spelling question, though a retained repository contract test should protect it.

#2976 correctly separates deployment from execution, replaces secret bindings, overrides the builder entry point, selects the verifier service account and disables task retries. Its readback checks only part of the deployed definition. Complete it with the immutable image/execution checks of R13-3 and explicit confirmation of the connection configuration, task/retry settings and isolation preflight. A failed post-deploy check leaves a deployed definition to inspect or remove; it is not an automatic rollback.

#2963 now keeps the admin URL out of argv, uses the required version-management permissions without secret-read permission, and activates the sealer transactionally with compensation. These are substantive closures. Its temporary IAM removal, staging-secret deletion and unknown-outcome recovery still require verified operational acts.

**What the composed rehearsal establishes**

The reported **187 passed in one invocation**, followed by **three separately passing added attacks**, is useful evidence on the submitted matching bytes. It covers restricted-role construction, real verifier/sealer logins, the executable transaction owner, current/fabricated/superseded brief behavior, attribution triggers, grants, replay, pre-1240 generations and several contention cases.

It does **not** establish:

- A single complete run including the three later tests and the new findings here.
- Compatibility between actual CLI output, Cloud Logging and the workflow checker.
- Actual GitHub environment protection, approval API ordering or rerun behavior.
- Producer execution provenance.
- The R13-2 late-write schedule.
- Managed Cloud SQL behavior or full-generation capacity.

The disclosed stand-ins remain material: migration-built PG15 mirror; fixture-supplied L1 schema/grants; selected input/ephemeris monkeypatches; owner connections for raw database attacks; builder `SET ROLE`; in-process CLI execution; API/log fixtures; and a modeled `cloudsqlsuperuser` group. Real sealer/verifier logins improve the evidence, but do not remove those limits.

The integration commit is the composed evidence bundle. The older #2952 exhibit’s mergeability is a separate unresolved matter.

**Measurement — (d) only**

The production measurement modules are unchanged from the reviewed round-12 measurement commit. The READ ONLY/REPEATABLE READ repair remains correct; the four-readback reproduction passed here.

No new source objection is established for the accepted measurement scope. This does not establish a measurement result or satisfy **S1-REQ-EPHEMERIS**: the `'4.1'` manifest must identify the ephemeris for every consumed body, including the Moon, and the consumed horizon. Stage-1 and Stage-2 freezes remain required.

`'4.1'` remains diagnostic-only, with `t_honesty = UNVERIFIABLE`; this tooling supplies no numerical or serving activation authority.

**Ranked amendments**

| Rank | Item | Exact closing result | Blocks |
|---|---|---|---|
| 1 | **R13-2** | Database-enforced serialization of every covered mutation and brief insertion through COMMIT; real-role late-write/immediate-constraint tests pass. | Final 1240 acceptance, **(a), (c)** |
| 2 | **R13-1** | Actual verifier CLI → actual structured-log envelope → extractor → checker succeeds with one versioned contract; corruption cases refuse. | **(c)** |
| 3 | **R13-3** | Immutable producer commit/image/execution and persisted brief identity verified through the approval/seal chain; old-execution handling explicit. | **(c)**; incorporate any SQL changes before (a) |
| 4 | **R13-4** | Approval selection independent of undocumented ordering; ambiguity refused; run/attempt artifacts and rerun/cancellation reconciliation tested. | **(c)** |
| 5 | **R13-5** | Owner memberships and verification-column grants refused by the real sealer login’s self-check. | F-R12-5 closure, **(c)** |
| 6 | **R13-6** | One consistent executable runbook/design, correct DSNs/order/recovery/attribution, explicit preflight and reviewed gate-proof workflow. | Affected preparation for **(a), (c)** |

The following are **disclosed limits or operational qualifications**, not additional discoveries of an unsafe source path: same-account approval; trusted verifier arithmetic; declared candidate-boundary exclusions; starter resource values; lack of production receipts; and inability to infer rollback from a lost COMMIT acknowledgement.

After source closure, the required operational sequence is:

1. **Before the protected window:** freeze the combined reviewed bytes; refresh expected hashes; rerun the complete composed suite, new attacks and mechanical window rehearsal. Refresh the routine-predecessor ledger evidence.
2. **Before the window:** merge act 7’s preflight at the authorized time; tell the owner the sitting is starting.
3. **Before the window:** act **3 → 10 → 4 → 11**: verifier service account and Cloud SQL access; narrowly scoped deployment `actAs`; verifier secret/accessor; temporary expiring version-management grant.
4. **Before the window:** execute combined acts **1 + 2a** once. Verify both roles and the verifier secret version; sealer remains password-null/disabled. Remove act 11’s temporary IAM binding and verify removal after every terminal outcome.
5. **Before the window under the prescribed sequence:** act **5**, then the reviewed no-secret live-gate proof: protected-branch wait, non-protected-branch refusal, delegated approval and successful continuation.
6. **Before dispatch:** reconfirm final migration bytes, routine predecessors, role state and 1206’s unapplied status. **Act 9 remains the owner’s personal protected-window dispatch.**
7. **After the window:** act **8**, routine 1241, with both principals found and exact ACL closure; provision the separately governed L1 reads and verify builder prerequisites.
8. **After the window:** complete act **2b** only behind the proven gate; verify activation and staging-secret deletion. Deploy act **6**, verify its complete definition/connection/isolation, and perform the explicitly defined bootstrap execution needed by act **12**.
9. **After the window:** complete act **12** and its negative read probe; build and independently verify the held candidate as required by dependencies. Obtain the full-generation capacity evidence.
10. **After those prerequisites:** run the corrected brief → digest-bound approval → seal workflow. Reconcile publication, seal and receipt after success or ambiguous failure. Report the delegated approval and perform the specified temporary-resource cleanup.

These steps describe dependencies; they authorize none of the acts.

**Step lines**

- **(a) BLOCKED BY R13-2, affected R13-6 preparation corrections, refreshed final-byte rehearsal and the listed pre-window operational prerequisites.**
- **(b) UNBLOCKED.** Registry 1.1.0 binding is merged in #2897; its binding is present on the inspected main.
- **(c) BLOCKED BY R13-1 through R13-6, followed by provisioning, deployment, independent-verification, approval and seal receipts.** Build/verification source acceptance does not imply seal acceptance.
- **(d) BLOCKED BY S1-REQ-EPHEMERIS and the uncompleted Stage-1/Stage-2 freezes.** The reviewed measurement tooling is acceptable for that scope.

**What I could not verify**

- The read-only sandbox did not permit starting a disposable PostgreSQL cluster. No cluster was started, and no production database was contacted. SQL, ACL and concurrency conclusions are source assessments; reported PostgreSQL passes remain author evidence.
- Production role, secret, IAM, migration-ledger, RLS and environment state. The absence of principals and prior production execution is the supplied packet’s premise, not a live finding by this reviewer.
- Actual Cloud Run deployment/log delivery, GitHub approval/retry behavior, Cloud SQL authentication and full-generation resource consumption.
- The later branch revisions listed as observed but unreviewed.
- Mathematical independence beyond the reviewed all-NULL verifier scope, or any numerical activation claim.

No file was created, edited, moved or deleted by this review. No git write command was run. The detached checkout remained clean.