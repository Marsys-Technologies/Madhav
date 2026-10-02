---
artifact: ASTRA_REVIEW_A5_1_MIGRATIONS
version: "1.1"
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: 9b439c5fc
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT.**

Amendments **#2 and #3 are CLOSED at source-review level**. The other seven are **PARTLY CLOSED**. The rewrite makes substantial structural repairs, but still permits publication-history loss, changes to existing rule definitions, inconsistent contact ownership, and invalid typed values. It also overrules C2 through an unauthorized factor restriction, and its preflight/schema-verification mechanisms remain defective.

Reviewed HEAD: `9b439c5fc7367902c173086f45db2f01bafa9bde`. The twelve reviewed migration, preflight and test files match HEAD. No files were written, no git write commands were run, and no database was contacted. The prohibited directories were not accessed.

Evidence abbreviations:

- **S**: [frozen design specification](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md); **O**: [frozen test oracles](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_TEST_ORACLES_v1_4.json).
- **M1153**: [1153_gochara_sky_event_substrate.sql](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/migrations/1153_gochara_sky_event_substrate.sql).
- **M1154**: [1154_gochara_rule_path_registry.sql](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/migrations/1154_gochara_rule_path_registry.sql).
- **M1155**: [1155_gochara_relationship_record.sql](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/migrations/1155_gochara_relationship_record.sql).
- **M1156**: [1156_gochara_eval_window.sql](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/migrations/1156_gochara_eval_window.sql).
- **M1157**: [1157_gochara_av_polarity_declaration.sql](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/migrations/1157_gochara_av_polarity_declaration.sql).
- **PF1154/PF1155**: [preflight_1154_rule_path_registry.sql](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/python-sidecar/scripts/kala_gochara_cutover/preflight_1154_rule_path_registry.sql), [preflight_1155_relationship_record.sql](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/python-sidecar/scripts/kala_gochara_cutover/preflight_1155_relationship_record.sql).
- **DBT**: [database tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/tests/integration/gochara_a5_1_migrations.db.test.ts); **ST**: [static tests](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/tests/unit/migrations/gochara_a5_1_contract_static.test.ts).

**Closure table**

“CLOSED” below describes the reviewed implementation and test design; it does not claim an executed PostgreSQL test result.

| # | Round-1 amendment | Judgment | Evidence and remaining gap |
|---|---|---|---|
| 1 | Separate contacts from boundary events; define lifecycle | **PARTLY CLOSED** | Separate contact storage, transit relations and interval fields now exist: **M1153:391–461**. Transit records reference it: **M1155:201–202**. Legacy correspondence is explicitly generation-based: **M1153:50–57**. However, global keys conflict with generation ownership, contact references omit ownership, and deletion protection depends only on current publication status. See F1–F2. |
| 2 | Restore atomic DDL-and-ledger application | **CLOSED** | None of the five migration bodies contains transaction-control `BEGIN`, `COMMIT` or `ROLLBACK`. Remaining `BEGIN` tokens delimit PL/pgSQL blocks. The runner owns DDL plus ledger insertion in one transaction. **DBT:997–1038** injects a real ledger-insert failure after 1153’s DDL. Its limits are explained below. |
| 3 | Mandatory versioned FKs and normalized membership | **CLOSED** | Path/version columns are mandatory: **M1155:140–141**, **M1156:75–76**. All four reference lists now use membership tables with actual FKs: **M1154:347–375**, **M1155:304–325**, **M1156:156–170**. Window membership binds both ends to the same chart/generation and supports deletion through cascades. The normalization introduces a separate version-immutability regression, F3. |
| 4 | Real coverage identity and scope consistency | **PARTLY CLOSED** | Coverage now references the actual 1081 partition key with chart/generation: **M1155:206–212**, **M1156:126–130**. Body/convention and agent/object consistency are improved: **M1153:256–258, 418–420**, **M1155:201–202**. Applicable partition scope and physical relation consistency remain unenforced. See F7. |
| 5 | Tagged states, precision, valence and qualification persistence | **PARTLY CLOSED** | Support-state cardinality is enforced: **M1155:213–229**. Transit precision is mandatory; valence is NOT NULL; admission, prerequisite results and frame arithmetic have separate fields: **M1155:147–163, 230–239, 304–317**. Explicit truncation and exact-event payload requirements are present: **M1153:272–286**. New helpers still admit SQL NULL results, and contradictory qualification states are accepted. See F5. |
| 6 | Publication immutability and correction identity | **PARTLY CLOSED** | Non-NULL precision/history protections and predecessor checks exist: **M1153:305–387, 474–557**. But `correction_seq` changes the prescribed identity recipe without a supplied binding decision; target-changing corrections cannot use the new supersession mechanism. The solver-method enrichment exemption is too broad. See F4. |
| 7 | Factor/score contract, as narrowed by C2 | **PARTLY CLOSED** | Factor bounds, mandatory calibration status, calibrated mapping presence and mandatory `score_rule` are implemented: **M1154:228–264, 302**. Score bounds, nonnegative evidence, nonempty intervals and peak containment are present: **M1155:264–267**, **M1156:111–123**. However, the factor CHECK additionally prohibits uncalibrated mappings and requires category ordering, contrary to the binding ruling. See F6. |
| 8 | Effective preflight and definition verification | **PARTLY CLOSED** | Preflights now raise on findings and use wildcard-safe ledger prefixes. But signature matching is wrong, deployment still bypasses the preflights, schema resolution remains unpinned, and post-DDL verification mostly checks names rather than definitions. **PF1154:72–81; PF1155:87–123; M1157:103–135**. See F8–F9. |
| 9 | Typed frames/selectors, provenance and lineage | **PARTLY CLOSED** | Vocabulary checks, string-array lineage, citation presence, canonical-chart enforcement and the narrower ruling condition are implemented: **M1154:130–200, 308–320; M1155:167–185, 242–256**. NULL frame arguments still bypass validation; arbitrary strings remain accepted as named selectors; resolvable fact lineage has no demonstrated write-boundary gate. See F5 and F11. |

The two earlier minor items are addressed: the duplicate sky-event index is removed, and both coverage-consuming tables have coverage indexes—**M1153:568–572; M1155:299–300; M1156:151–152**.

The atomicity test is meaningful. The [runner at lines 791–803](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/scripts/migrate.ts:791) executes migration SQL, inserts its ledger row, then commits. **DBT:1003–1012** installs a trigger that raises on that insert; **DBT:1021–1038** requires the specific injected error and checks table/ledger absence. With the empty ledger and supplied options, this reaches 1153’s post-DDL ledger insertion. However, **1154–1157 are never attempted in this failure test**: their absence is not rollback evidence. The test also checks tables rather than every standalone function. This is a valid regression test for the original transaction-ownership bug, not evidence of an executed five-migration rollback campaign.

**New defects and rewrite-specific failure cases**

The counterexamples below follow from the source and PostgreSQL semantics; they were not executed against a database.

**F1 — P1: Contact ownership is incompatible with coexistence and permits cross-generation references.**

`contact_id` is a global PK, and `(physical_object_id, occurrence_ordinal, correction_seq)` is globally unique—**M1153:392, 431–437**. Consequently, the same unchanged physical contact cannot be owned by two generations: copying its ID fails the PK; assigning another ID still fails the natural uniqueness constraint. This conflicts with the required per-generation ownership and retained published generations.

Conversely, the record-to-contact FK includes only contact ID, agent and object—**M1155:201–202**. A record can therefore reference another generation’s contact. The test suite actually constructs this: contacts use `GEN` at **DBT:278**, while **DBT:687** inserts a `GEN_OLD` record through a helper that always references `CONTACT_1`—**DBT:326–336**.

The schema needs a coherent distinction between stable physical identity and chart/generation ownership, with references bound to that ownership. Minting a fake correction solely to avoid a generation collision is not an acceptable repair.

**F2 — P1: Publication protection expires and is not coordinated with publication transitions.**

The contact DELETE guard checks only `pub.status = 'published'`—**M1153:518–528**. The inherited publication table also permits `superseded` and `rolled_back`—[1081:116–119](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/migrations/1081_nirmana_l3_gochara_ledger_coverage_publication.sql:116). After either transition, an otherwise unreferenced contact becomes deletable and its ID reusable. **S:641–646 protects an identity once published**, regardless of later serving status.

The plain `EXISTS` also supplies no serialization with publication. A candidate deletion can pass its check while another transaction publishes that generation; the schema does not coordinate the two operations.

Furthermore, the immutable guards cover `UPDATE OR DELETE`, not `TRUNCATE`—for example **M1153:384–387, 563–566; M1154:385–393; M1157:93–96**. A role holding the relevant TRUNCATE privileges can bypass those row guards, including through cascading truncation. PostgreSQL explicitly does not fire DELETE triggers for TRUNCATE. [PostgreSQL TRUNCATE documentation](https://www.postgresql.org/docs/16/sql-truncate.html).

Protection must follow permanent publication history and a defined publication/rebuild synchronization protocol. TRUNCATE needs protection or a verified privilege boundary.

**F3 — P1: Normalization makes an existing rule version extensible.**

The prerequisite and soft-factor membership guards reject UPDATE and DELETE only—**M1154:347–393**. After `(P1, v1)` has produced records, an INSERT can append another prerequisite or factor to that same version. Its interpretation changes without changing `rule_version`, violating **S:152–155**.

The FKs are real and correctly close amendment #3’s reference-existence problem. They do not make the complete rule definition immutable. Membership construction needs an explicit completion/sealing boundary that prevents later additions to an existing definition while allowing its initial atomic construction.

**F4 — P1: Correction identity remains an unresolved contract decision, and the implementation excludes required corrections.**

**M1153:59–70** declares a new hash recipe including `correction_seq`. The frozen contract still specifies `hash(physical_object_id, occurrence_ordinal)` and its canonical serialization—**S:621–629, 647–649**. Neither supplied steward ruling authorizes that change. Labeling a migration comment “contract decision” does not settle it.

Both supersession guards require the predecessor to have the **same physical object and ordinal**—**M1153:311–316, 480–485**. A corrected target changes the physical-object identity, so the required target-correction edge cannot be inserted, although **S:645–646** explicitly requires such corrections to mint a new ID and supersede the old one.

There is also a precision loophole: the solver-method exception allows any method change during an enrichment flip—**M1153:367–368, 548–549**. It does not restrict the exception to replacing the `clipped_truncated` placeholder. A truncated row already carrying a meaningful method can change that non-NULL method without a new convention.

Resolve and ratify the correction recipe, preserve original identity compatibility, and test same-tuple, target-changing and convention-changing corrections separately.

**F5 — P1: Typed CHECK helpers still accept invalid NULL values.**

Two direct bypasses remain:

- `ka_gochara_frame_ok('graha', NULL)` and `ka_gochara_frame_ok('bhavat_bhavam', NULL)` return SQL NULL—**M1154:111–122**. Their CHECK callers accept that result.
- `{"solver_method":null,"delta_lambda":0.001,"delta_t":60}` satisfies key/type checks but makes the solver comparison NULL—**M1155:96–104**. A non-NULL transit precision payload therefore passes **M1155:230–238** without a valid solver.

A PostgreSQL CHECK rejects false, but accepts NULL. Helpers used as validators must return a total boolean or be required to evaluate `IS TRUE`. [PostgreSQL CHECK semantics](https://www.postgresql.org/docs/16/ddl-constraints.html).

Qualification persistence also lacks consistency enforcement. **DBT:329–335** creates an admitted record, then **DBT:671–675** successfully adds an `unknown` prerequisite without changing its admission. This contradicts **S:103, 163**. The atomic write/finalization boundary must reject that final state; adding separate fields alone does not establish the invariant.

**F6 — P1: The factor CHECK contradicts the binding C2 ruling.**

**M1154:261–264** requires every `uncalibrated_default` row to have:

- `category_mapping IS NULL`; and
- a non-NULL `doctrine_ordering`.

The ruling requires only bounded range, mandatory valid calibration status, and a mapping for calibrated rows. It does not prohibit an authored default mapping. Indeed, **S:173–178** places the B5.1 mapping on the factor row while it remains `uncalibrated_default` until L5 calibration.

The added restriction also forces continuous factors to supply category ordering whether applicable or not. **DBT:819–839** explicitly tests the incorrect prohibition.

Remove that extra restriction. Preserve the calibrated-mapping implication and existing range/status requirements. **No numeric values need to be invented or seeded.**

**F7 — P1: Existence and chart/generation FKs still permit contradictory lineage.**

Three consistency gaps remain:

- **Physical relation:** the object-to-contact FK omits `relation_kind`; the contact-to-record FK omits `relation`. A conjunction physical object, an aspect contact and a residence record can describe the same referenced identity without a constraint failure—**M1153:418–437; M1155:201–202**.
- **Window membership:** membership binds chart/generation but not event class or path/version. A `P1/v1` marriage window can include a `P2/v2` surgery record from the same generation—**M1156:156–170**—despite the per-path/class window contract at **S:183–205**.
- **Coverage applicability:** the coverage FKs prove that a partition exists, but do not establish that it covers the consuming class, relation, body/target, convention or interval—**M1155:206–212; M1156:126–130**. An unrelated `event_class` partition can be selected, and a Moon record need not reference `moon_on_demand` coverage.

The inherited coverage table actually carries convention, horizons and searched relations—[1081:225–248](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/platform/migrations/1081_nirmana_l3_gochara_ledger_coverage_publication.sql:225). The test stub omits them—**DBT:211–216**—so it cannot establish applicability. The relationship between its legacy convention and the new sky convention also needs an explicit bridge or validation rule.

**F8 — P1: The intended preflight sequence rejects its own valid helpers.**

**PF1155:111–123** compares `pg_get_function_identity_arguments` with type-only strings such as `text, text` and `jsonb`. But M1154 creates **named** parameters:

- `frame_kind text, frame_arg text`—**M1154:111**;
- `j jsonb`—**M1154:130**.

PostgreSQL’s identity-argument formatter retains parameter names. Therefore, after a correct 1154 application, PF1155 reports those helpers missing. The same mistake causes PF1154’s collision checks to miss named same-signature functions—**PF1154:72–81**. This follows directly from PostgreSQL’s formatter implementation. [PostgreSQL source](https://raw.githubusercontent.com/postgres/postgres/REL_16_STABLE/src/backend/utils/adt/ruleutils.c).

Use argument type identities, such as `to_regprocedure`/catalog type OIDs, with required return-type properties. Also check collisions for 1155’s own precision and interval helpers before replacing them.

The tests miss this failure: only PF1153 has a successful preflight case; fresh application bypasses the preflights; post-application tests accept any `BLOCKED` error—**DBT:403–404, 442–450, 483–486**.

**F9 — P1: The effective deployment and drift-verification gate remains incomplete.**

The [deployment workflow](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765b/.github/workflows/deploy.yml:1186) still invokes the general runner without these preflights. No reviewed interleaved execution receipt was supplied with this closure request.

The post-DDL checks do not prove schema equivalence:

- **M1153:647–690** checks constraint names, not their definitions.
- **M1157:123–127** accepts any constraint named `kgav_categories_nonempty_ck`.
- M1157 never verifies its primary key.

A same-named AV table with the expected NOT NULL column types, **no primary key**, and `kgav_categories_nonempty_ck CHECK (true)` passes M1157’s verification. The added drift test removes a column—**DBT:979–990**—and therefore does not exercise this failure.

All five migrations also leave creation/reference schema resolution implicit while verification targets `public`. PF1154/PF1155 verify only CREATE privilege on `public`, not effective schema resolution or the needed reference/runtime privileges. Unqualified relation lookups inside trigger functions likewise depend on runtime name resolution.

Require an effective ordered gate, pinned schema resolution, and actual PK/UNIQUE/FK/CHECK definitions and validation state. Distinguish a tracked skip, deliberate equivalent replay, and rejection of an untracked collision. Replacing functions and recreating triggers is not a literal no-op.

**F10 — P1: The new destructive database-test guard does not validate the database name.**

**DBT:384** searches the entire connection string for `gochara_a51_test`. For example, this passes the guard:

```text
postgresql://db.example/production?application_name=gochara_a51_test
```

Its database is still `production`. The subsequent reset drops `charts`, publication, coverage and the migration ledger with CASCADE—**DBT:160–180, 391–392**.

Parse and validate the actual database target before creating the pool. Require an explicit disposable-database boundary and test misleading username, hostname and query-string cases without connecting anywhere.

**F11 — P2: Several claimed typed boundaries remain only shape checks.**

`ka_gochara_named_operands_ok` accepts arbitrary string values, including empty strings and prose, despite its comment claiming prose rejection—**M1154:169–181**. Declare and validate the selector encoding. Fact IDs now have nonempty-string shape, but **M1155:242–244** supplies no resolvability guarantee; that remains a required, explicit writer-boundary validation.

Precision payloads accept negative uncertainties—**M1155:96–104**—and sky/contact uncertainties have no numerical-domain checks—**M1153:249–251, 411–413**. Evidence checks using only `>= 0` accept PostgreSQL `NaN` and positive infinity—**M1155:264–267; M1156:120–123**. PostgreSQL sorts NaN above ordinary floating-point values. Reject invalid/nonfinite computed quantities without imposing an evidence upper bound of one. [PostgreSQL numeric-type documentation](https://www.postgresql.org/docs/16/datatype-numeric.html).

Finally, the new AV category check counts array elements but accepts `{NULL}` or an empty-string category—**M1157:74–75**. Those do not establish an applicable fact category.

**Ranked merge-blocking amendments**

| Rank | Priority | Required closure |
|---|---|---|
| 1 | **P1** | **F1–F2:** Reconcile stable contact identity with generation ownership; enforce scoped references and permanent publication protection. Test retained published generations, candidate rebuilds, retired statuses and concurrent publication/rebuild behavior. |
| 2 | **P1** | **F8–F9:** Repair signature checks and establish the effective ordered preflight/application/verification gate. Test successful interleaving, same-signature collisions, wrong constraint definitions, missing keys and schema resolution. |
| 3 | **P1** | **F3:** Make complete rule-version membership immutable after construction. Reject later prerequisite/factor additions to a used or sealed version. |
| 4 | **P1** | **F4:** Obtain the binding correction-identity disposition and implement its complete supersession/enrichment rules, including target/convention changes and original identity compatibility. |
| 5 | **P1** | **F5:** Make validators reject SQL NULL results and prevent contradictory final qualification states. Add the exact NULL payload cases identified above. |
| 6 | **P1** | **F6:** Remove the unauthorized uncalibrated-mapping/category-ordering restrictions and correct the tests to match C2. |
| 7 | **P1** | **F7:** Enforce relation consistency, window class/path membership and applicable coverage lineage at the contracted atomic write boundary. |
| 8 | **P1** | **F10:** Repair the destructive-test target guard before running or relying on the suite. |
| 9 | **P2** | **F11:** Complete selector encoding, fact-resolution disposition, finite/nonnegative precision/evidence validation and nonempty AV-category elements. |

Existing legitimate evaluator obligations remain separate: solver mathematics, deterministic hashing execution, predicate ordering, testimony exclusion, Moon scheduling and score evaluation still require their designated later tests. The AV declaration-to-evaluation gate is explicitly deferred at **M1157:32–44**; its table alone does not satisfy **O-BP-3**.

**What I could not verify**

- No PostgreSQL execution was performed: fresh application, rollback, replay, locks, trigger behavior and concurrent lifecycle cases remain unverified at runtime.
- Neither Vitest suite was executed. Vitest dependencies are absent in this checkout; the database suite is additionally opt-in through its environment variable—**DBT:382**. Reviewed test code is not a passing receipt.
- Production object definitions, privileges, search paths, applied hashes and live migration-number reservations were not inspected. I accepted the supplied statement that 1153–1157 have never been applied.
- The database suite uses parent key-shape stubs, not the full production migration chain. It cannot establish complete parent-schema compatibility or coverage semantics.
- The 57 frozen oracles—21 literal and 36 executable-at-A5.5—were not executed. The test labeled O-RX-1 uses supplied UUIDs and ordinals; it does not verify the frozen identity serialization/hash.
- Read-only checks confirmed the reviewed files match HEAD, `git diff --check` passes, and all five migrations have no top-level transaction-control or business-data mutation statements.

Frozen input SHA-256 values remain:

```text
S  d5097ca18a721d8005cab593f3c3865227d22ff1435b8adc9973275d3f786a47
O  19951b06ce672ac4cff82d74fb6c7bb7babe4315582ec1c142a0a7871752c277
```