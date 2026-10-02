---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: "2026-10-01"
verdict: REJECT
reviewed_commit: "65836a915 (campaign/pravaha) + c9ddf622c (PR #2817)"
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT as submitted.** AM-5 contradicts both applied coverage guards; AM-3 prescribes deletion of immutable substrate data; and migration 1205 broadens a shared frame validator beyond the P6 testimony use it claims to permit. AM-1–AM-5 cannot be folded verbatim.

**AM-6 pick: Option C**, with the qualifications below. The `av_qualifier` selector widening in 1204 is justified. Migration 1205 should be reworked or separated from 1204.

The review used the frozen specifications and oracles at `65836a915`, and the proposed migrations, runner, workflow and tests at `c9ddf622c`. Migrations 1153–1157 were checked against locally available `origin/main`; their bytes are unchanged in the PR. The checkout remains clean.

For references below, **S** means `GOCHARA_DESIGN_SPECS_v1_4.md`, **A** means `GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md`, and **O** means `GOCHARA_TEST_ORACLES_v1_4.json`, all under `00_ARCHITECTURE/briefs/pravaha/design/`. Numbered SQL references identify files under `platform/migrations/`.

**Per-amendment decisions**

| Amendment | Verdict | Finding and required disposition |
|---|---|---|
| **AM-1 — Convention** | **ACCEPT_WITH_AMENDMENTS** | The selected dimensions and values are compatible with v1.4 and 1153. Pin their exact serialized values, distinguish convention identity from generation, and verify the cited L1 node provenance. The 1153 self-test demonstrates an admissible example domain; it does not establish the runtime domain’s authority. Reconcile the literal convention ID `'5.0'` with the referenced A5.3 implementation’s digest-based convention ID. |
| **AM-2 — SHA-256 → UUIDv8** | **ACCEPT_WITH_AMENDMENTS** | The algorithm is sound for deterministic identity, subject to explicit canonicalization and collision detection. Resolve the difference between `hash(physical_object_id, ordinal)` and the flattened bytes printed by §6.1/O-RX-1. Add expected UUID vectors and collision/replay tests. |
| **AM-3 — Two phases** | **REJECT** | Contacts preceding evaluation is sound. “Each substep” using chart×generation delete-then-insert is not: conventions, physical objects and contact identities are global and insert-only; sky-event deletion is refused. Candidate contact replacement also conflicts with surviving relationship FKs. Rewrite persistence behavior by table and publication state. |
| **AM-4 — Ephemeral Moon/day tier** | **ACCEPT_WITH_AMENDMENTS** | Consistent with S:385–393, S:655–658 and O-SS-4. Correct A:127: contact `body='moon'` identifies the **transiting Moon**, not a natal-Moon target. Define the lifetime and coverage of on-demand responses, particularly after generation sealing. |
| **AM-5 — Coverage ownership** | **REJECT** | Writer ownership and same-transaction linkage are correct. `partition_kind='event_class', partition_key=path` is wrong. Both 1155:706–709 and 1156:402–405 require `partition_key = event_class`. Per-path transactions also need an explicit rule for when shared class coverage is complete. |
| **AM-6 — Ṣaḍbala units** | **ACCEPT_WITH_AMENDMENTS — C** | Preserve raw rūpas as typed operand evidence; expose only the cited binary sufficiency result as a unitless factor. The draft incorrectly treats `[0,1]`, explicitly an **output** range, as though it bounded the raw input. Resolve zero-factor versus admitted-window semantics explicitly. |
| **AM-7 — `av_qualifier`** | **ACCEPT_WITH_AMENDMENTS** | Adding the role to both record and selector vocabularies is coherent and mechanically minimal. A relationship record is appropriate for an actual transit carrying AV qualification and provenance. Its existence must not manufacture event admission or duplicate physical evidence. Specify P5 form identity, applicability and declaration lineage. |
| **AM-8 — `inherited`** | **REJECT** | The proposed shared-function change permits unresolved inherited frames on arbitrary paths and relationship records, including scored rows. It also bypasses the literal relative/Moon-frame check. Restrict inheritance to a P6 testimony template and resolve a concrete frame for evaluated annotations. Define their parent linkage and sealed-generation behavior. |
| **AM-9 — Node houses** | **ACCEPT_WITH_AMENDMENTS** | Correctly routed as an L0-owner finding, with no automatic v1.5/P2 change. Separate favourable-placement citations from unsourced house-vedha and detailed phala claims. Do not replace a compound row’s citation wholesale or assert that Ketu-12 has been disproved across all sources. |

**AM-6: choose C**

The classical claim available here is a sufficiency classification. `PROMISE_NATURE_YOGA_MAP_v1_1.md:244–254` transcribes Phaladīpikā IV.22–23, `phaladeepika:PG79:C1`, giving these total ṣaḍbala thresholds:

| Graha | Rūpas |
|---|---:|
| Sun | 6.5 |
| Moon | 6 |
| Mars | 5 |
| Mercury | 7 |
| Jupiter | 6.5 |
| Venus | 5.5 |
| Saturn | 5 |

Implement a versioned, unitless step result, with the threshold comparison and equality boundary stated explicitly. Retain the raw measurement, its unit and its L1 provenance outside the scored factor’s output range.

This is preferable because:

- **Classical:** it encodes the cited threshold without inventing a continuous doctrine of strength or probability.
- **Engineering:** it preserves the bounded product/max algebra in S:165–213 and satisfies `kgf_units_ck` and `kgf_range_unit_interval_ck`, without widening either constraint.
- **Auditability:** the raw value remains available to explain the classification and diagnose unit or provenance errors.

**Option A is incomplete and incompatible as written.** Adding `rupas` to the enum does not permit `[0,+∞)` or missing bounds: 1154:311–338 requires non-null, finite bounds within `[0,1]`. Widening those constraints would alter the factor algebra, not merely admit another unit.

**Option B introduces an uncited numerical scale.** Clamping also makes “exactly sufficient” and “above sufficient” numerically indistinguishable unless the raw value is retained anyway.

C needs these exact qualifications:

1. Cite **Phaladīpikā IV.22–23, `phaladeepika:PG79:C1`**, with the edition/translation and resolvable corpus locator, for the seven thresholds. Cite the actual L1 operand’s fact ID, subject, unit, build, ayanāṃśa and verification tier separately.
2. **IV.24, `PG80:C1`, concerns bhāvabala composition.** It does not establish the seven graha thresholds as a bhāvabala sufficiency test. Do not silently combine bhāvabala and ṣaḍbala.
3. Do not invent thresholds for Rāhu/Ketu. Missing, incompatible or unsupported operands remain explicitly unqualified.
4. State whether zero can reduce the numerical rank to zero while preserving admission. S:129–130 and S:401–402 say soft factors must not zero an admitted window, while S:209–213 prescribes multiplication. C must reconcile that wording; zero must never become an undeclared necessary predicate or remove the admitted interval.
5. Version the factor and its consuming path membership. Raw rūpas are **operand evidence**, not a second scored factor forced into the same bounded catalogue.

A smaller implementation may retain the existing summary name if it already denotes a step output, with explicit input/output typing under a new version. That is effectively C; a silent change of the raw measurement’s unit is not.

**Identity, convention and writer consequences**

**AM-1 requires one exact convention contract.** A:46–67 names `'5.0'`, while the cited A5.3 substrate implementation inspected at `694d16e9c`, `services/gochara_kernel/substrate.py:153–171`, derives `convention_id` as `sha256:<digest>` of the convention vector. Either representation can fit 1153; they are not interchangeable once included in physical/contact identities.

Specify:

- Exact ephemeris build representation and failure on a runtime mismatch.
- Exact grid serialization: `13°20′` must not be interpreted as decimal `13.20°`.
- The half-open UTC domain and the governed basis for selecting it.
- A deterministic L1 node-convention selection with fact provenance, rather than an arbitrary latest fact.
- Equality of convention-defining fields on reuse, excluding audit metadata such as `created_at`.

**AM-2 is cryptographically reasonable but operationally underspecified.** UUIDv8 accommodates a SHA-256-derived format. After setting version and variant bits, **122 digest bits remain**, not 128 or 256; collision resistance is therefore approximately the birthday bound of \(2^{61}\) identities. That is ample for the intended dataset, but does not replace collision handling. [RFC 9562 §5.8](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.8)

Pin UTF-8 encoding, body/relation token case, delimiter rules, full-precision numeric rendering, sign/star normalization, and absence of trailing whitespace or newline. Preserve the explicit O-RX-1 serialization unless a reviewed oracle amendment changes it.

The distinction is observable. Independently calculated in memory using the proposed algorithm:

```text
Mars|conjunction|point:198.52|c0|1
→ 87b023cc-c9f3-8979-9b37-96701f285356

mars|conjunction|point:198.52|c0|1
→ 23276d7c-c127-8f4c-9ad5-6b7c8da8020f
```

1153 stores lowercase body tokens. An implementation that hashes caller casing and then lowercases for persistence can generate different IDs for the same stored natural tuple.

Collision handling must distinguish:

- Same canonical tuple and same ID: legitimate replay.
- Different canonical tuple and same ID: loud failure **before** any UUID-keyed deduplication.
- Same canonical tuple and different ID: serialization/version divergence, also a failure.

`ON CONFLICT DO NOTHING` alone is insufficient. Add forced-collision tests, including collisions after the UUID bit masks, plus the direct/retrograde/direct, truncated-centre enrichment and forward-extension cases of O-RX-1.

Also settle correction identity: changing a published non-null time cannot mint a different deterministic ID from an unchanged tuple and ordinal. The correction must change an explicitly versioned identity component, consistently with S:641–646, and retain the supersedes linkage.

**AM-3 needs distinct persistence rules.** Preserve its computational ordering, but replace its blanket deletion sentence with:

- Global conventions, physical objects and contact identities: insert-if-absent with equality checks.
- Sky events: only the permitted enrichment/correction operations.
- Candidate chart/generation records and windows: replacement in dependency order, at a precisely owned grain.
- Published/sealed data: obey the existing refusal and enrichment rules; reevaluation must not reopen the generation.

Evidence: 1153:584–658, 758–759 and 813–887; 1155:413–459.

The writer also needs a **separate registry bootstrap transaction**. Migration 1153:430–485 enforces `READ COMMITTED` and prohibits mixing the global-exclusive registry lock with chart mutations. “Two phases” must not imply one transaction that binds registries and then writes chart data. Transaction ownership remains with the orchestrator.

**Migrations 1204/1205**

**1204 — ACCEPT_WITH_AMENDMENTS.** I verified that removing the added `av_qualifier` token yields the original selector function body byte-for-byte. The record-role CHECK likewise preserves the old vocabulary.

The selector widening is necessary under the chosen model: S:215–230 makes enumeration depend on the `(agent, relation, object_role)` selector. Admitting the role in records while refusing it in selectors would leave a contract that cannot legitimately select its own records.

This widening does **not** remove existing contact, coverage, prerequisite, sealing, provenance or membership constraints. It extends the allowed interpretive vocabulary; it does not establish P5 semantics.

I favour a P5 `av_qualifier` relationship record when it represents a real transit interval and carries the qualification’s lineage. It should share the physical contact/root with other interpretations of that transit and obey S:194–207’s within-path root reduction. A static BAV/SAV measurement alone is operand evidence, not a reason to invent another physical record.

Before enabling P5 writes, specify:

- Event-class and affected-person applicability; an AV declaration’s existence alone cannot establish occurrence of every event class.
- How P5a and P5b retain distinct outcomes and missingness without accidental merging or double counting.
- P5a’s known-zero adverse result versus its unresolved nonzero comparator.
- P5b’s cited bands, without converting them into a universal multiplier.
- The exact AV-build convention and declaration consumed.

Migration **1157:39–47 explicitly leaves the declaration-consumption/citation gate to the writer/evaluator** and leaves the meaning of its convention key unresolved. 1204 does not close that gap.

**1205 — REJECT.** The added arm at 1205:84–95 affects both `kgrp_frame_ck` and `kgrr_frame_ck`. It does not enforce P6, testimony, an admitted parent, or a resolved frame.

The PR’s own positive test demonstrates the problem:

`platform/tests/integration/gochara_b6_v15_migrations.db.test.ts:332–342` inserts and expects success for:

```text
path_id=P6
frame_kind=inherited
provenance=verse_cited
operator_role=scored
score_rule=within_path_product
```

That contradicts S:385–393, which makes every P6 operator testimony. Furthermore, 1155:527–528 excludes the native Moon frame for relatives by checking `frame_kind <> 'moon'`; an unresolved `inherited` value evades that check even if its effective frame would be Moon.

Use a context-specific registry/template representation for inheritance. Restrict it to P6 testimony; evaluate annotations with the parent’s concrete frame, frame argument and affected person. Test that non-P6 inheritance, scored P6, absent parents and forbidden effective relative frames fail.

The proposed arm also does not provide annotation linkage. Migration 1156:334–363 requires a window and its member record to have the **same path and version**. A P6 record cannot simply become a member of a P1–P5 window through that table. Define a separate annotation relationship or an ephemeral response contract, without weakening contributing-record membership.

**Replay and protected-window assessment**

The following checks passed by source inspection and in-memory comparison:

- 1153–1157 are unchanged.
- Both standalone preflight blocks match their embedded migration gates.
- Both old validator bodies are preserved apart from the additions.
- The runner’s protected list includes 1204/1205.
- The workflow selects 1153–1157 and 1204–1205 for the Gochara contracts window, checks the deployment SHA, and brackets execution with capability grant/revoke.
- Each migration and its ledger entry execute in one runner-owned transaction.

These are **replay-safe through the runner**, not independently repeatable SQL scripts. The runner skips identical applied hashes; the embedded gates intentionally reject already-recorded migrations. The two-file batch is not atomic: 1204 can commit before 1205 fails, and a subsequent runner invocation resumes accordingly.

The CHECK swap has no committed unconstrained interval: its transactional `ALTER TABLE` takes the requisite table lock. However, the workflow’s protected environment and deployment concurrency **do not demonstrate that existing writers are paused**. Correct the claim in 1204’s header. Existing writes can block or cause the five-second lock timeout; constraint validation can hold the table lock while scanning. [PostgreSQL ALTER TABLE documentation](https://www.postgresql.org/docs/17/sql-altertable.html)

Replacing a function used by CHECK constraints does not automatically revalidate existing rows. Here, preservation of old behavior supports compatibility with existing valid rows; it does not justify the new inherited-frame semantics. Any later tightening or rollback needs explicit data checks and revalidation. [PostgreSQL CHECK-constraint documentation](https://www.postgresql.org/docs/17/ddl-constraints.html)

**Gaps A5.3 still needs**

1. **Coverage completeness across per-path commits.** Correct AM-5 to `partition_key=event_class`, then define when that partition can report completion. Completing one path must not claim that every applicable path was evaluated. Extending a horizon and relation set must not imply an unperformed Cartesian combination of searches. Bind the required convention bridge and `coverage_facts` snapshot in the same transaction.

2. **On-demand work after sealing.** Moon searches require their own coverage, but relationship/window membership writes are sealed. Specify what is ephemeral, what receipt persists, and how a post-publication P6 query attaches provenance without reopening the published generation. Moon-agent coverage must follow 1155:729–732.

3. **Remaining identity encodings.** AM-2 covers §6.1 physical/contact IDs. A5.3 also needs deterministic serialization for relationship/window identities, including versioned prerequisites, citation changes, nulls and ordering.

4. **Geometry planning and invalidation.** A per-body contact phase needs the qualified target/relation inventory before solving. Pin how changed selectors, frames or support domains trigger geometry work, while pure scoring changes reuse geometry, as required by S:795–801 and O-RW-1.

5. **Actual admission and P6 behavioral tests.** The oracle map does not establish these yet.

For **Exhibit 3**, the verdict is **ACCEPT_WITH_AMENDMENTS as a partial-coverage report**. At `ec0f9a7b1`, the inspected suite contains 11 ordinary tests and two strict-xfail tests. The map honestly limits its REAL claims to enumeration/binding legs.

The deferrals are legitimate, but the present tests are only interface sentinels:

- B6-F16 checks whether `evaluate_admission` exists.
- B6-F17 checks that P6 enumeration returns something.

Neither tests the complete oracle outcome. Their replacements must assert union admission, channel attribution and unknown-state behavior; and the actual tārā class, admitted-parent binding, coverage and zero scoring effect.

**The proposed v1.5 batch closes neither finding by itself.** Migration 1205 does not implement admission, P6 enumeration or annotation semantics. Literal expected row sets make parts of the suite useful detectors, but the reported mutation runs were not independently reproduced.

The migration integration suite also omits **1156 and 1157** from `CONTRACT_FILES` at lines 48–55. Its AV fixture uses a conjunction rather than the proposed house-span residence, and its “every v1.0 role” probe tests only `karaka`. These tests establish selected SQL plumbing, not complete P5/P6 contract acceptance.

**AM-9 scope**

The supplied transcription at `CORPUS_READS_v1_0.md:130–137` supports `{3,6,10,11}` from the Moon: the Sun’s placements, the universal eleventh, and the nodes’ stated similarity to the Sun. The inspected L0 seed indeed omits both tenth-house favourable rows and adds Ketu-12.

The owner finding should nevertheless be narrowed in two ways:

- Those L0 rows combine favourable placement, a `vedha_house`, and detailed phala under one citation. Phaladīpikā XXVI.2 supports the favourable placements; it does **not thereby source the node house-vedha pairs or every detailed outcome**. Keep their provenance separate.
- The inspected `BPHS_CH29` constant is a generic transit-results label, and the file’s header describes that attribution as unresolved in the served corpus. The packet’s stronger assertion that it specifically denotes a node-over-Moon affliction passage is not established by the inspected evidence. Ketu-12 needs a precise supporting source or honest reclassification, preserving historical lineage.

No nodal dṛṣṭi follows from this finding. No production repair is authorized by this review.

**Ranked amendments required before acceptance**

| Rank | Severity | Merge-blocking amendment and acceptance evidence |
|---:|---|---|
| **1** | **P1** | **Rework AM-8/1205.** Restrict inheritance to P6 testimony templates, resolve concrete annotation frames, and define parent/seal behavior. Replace the positive scored-P6 fixture with a rejection test; cover non-P6 and relative-frame bypasses. |
| **2** | **P1** | **Correct AM-5.** Use event-class keys and define completion across path transactions. Demonstrate records and windows passing the real 1155/1156 guards, with partial computation remaining distinguishable from complete empty results. |
| **3** | **P1** | **Rewrite AM-3 persistence semantics.** Preserve immutable global substrate identities, separate registry/chart transactions, and prove candidate replay without deleting referenced or sealed data. |
| **4** | **P2** | **Complete AM-1/AM-2 identity pins.** Reconcile convention IDs, exact bytes and token normalization; add UUID vectors, forced collisions, replay, enrichment and correction tests. |
| **5** | **P2** | **Adopt and finish AM-6 C.** Cite the thresholds and actual operand units, distinguish bhāvabala/nodes, version consumption, and settle zero-rank versus admission semantics. |
| **6** | **P2** | **Complete AM-7’s P5 contract.** Define form identity, applicability, root reduction and AV-declaration consumption. Test real residence qualification against 1153–1157 plus 1204. |
| **7** | **P2** | **Correct evidence and operational claims.** Distinguish protected deployment from writer quiescence, and partial oracle coverage from behavioral closure. Execute the relevant full-stack and negative controls before claiming the gate satisfied. |

AM-9’s provenance correction is required in the owner finding but need not hold unrelated P1–P5 implementation work once the blocking contracts above are repaired.

**What I could not verify**

I did not connect to production, inspect live migration-ledger hashes, verify the live L1 fact `c520713087b97470`, or confirm installed Swiss versions. Production application of 1153–1157 is treated as the supplied premise.

I did not rerun PostgreSQL/Vitest/pytest suites or the reported mutation experiments. Verification here consisted of source review, byte comparisons, test-source inspection and in-memory UUID calculations. Classical conclusions use the repository’s cited transcriptions; I did not independently inspect the original scanned editions.

No files were created, edited, moved or deleted; no git write command or production database operation was performed.

