---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.4"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: "5626290c6 (campaign/pravaha) + b9d5d2718 (PR #2817)"
authority: "Review only; authorizes nothing."
---

**Verdict — ACCEPT_WITH_AMENDMENTS**

AM-5’s two P1 defects from v1.3 are **CLOSED at the specification level**. Finalized obligation-set commitments now expose never-inserted obligations, and immutable search-input binding prevents partial searches carrying different snapshot identities from combining.

Migration **1204 remains ACCEPT** as a vocabulary extension. **1205 is absent** from the reviewed PR; I accept its withdrawal, not an `inherited` frame implementation.

No P1 remains blocking acceptance of this amendment batch. The remaining items below are **A5.5-gate follow-ups**. This verdict does not establish database implementation, A5.5 completion, production readiness or deployment approval.

I read the v1.3 review first, then the packet, amendments, frozen specifications/oracles, executable evidence and migration sources. The packet still describes an earlier round; the explicit round-5 request and v0.5 exhibits govern this review.

Reference notation:

- **A**: [v0.5 amendment draft](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55e/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md).
- **S/O**: frozen `GOCHARA_DESIGN_SPECS_v1_4.md` and `GOCHARA_TEST_ORACLES_v1_4.json` in the same design directory.
- **M/C**: [model](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55e/00_ARCHITECTURE/briefs/pravaha/design/evidence/am5_model.py) and [cases](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55e/00_ARCHITECTURE/briefs/pravaha/design/evidence/am5_cases.py).
- Migration references identify numbered files under `platform/migrations`. I inspected 1153–1157 at main snapshot `2992093bc9626e0289ad570c569a17e7883d4953`; those files are byte-identical in the reviewed PR. The frozen specification and 57-oracle file remain unchanged.

**Per-amendment decisions**

| Amendment | Verdict | Assessment |
|---|---|---|
| **AM-1 — convention** | **ACCEPT** | The complete byte vector, compound ephemeris label, fixed ordinal domain and immutable bridge evolution resolve the implementation pins. I independently reproduced `eac922d4…a48e7a3`. `13d20m` deliberately changes the earlier erroneous `13.20` serialization. Mean nodes are an attested L1 selection, not a fallback when attestation is absent. The runtime and cited L1 fact remain unverified. |
| **AM-2 — identity** | **ACCEPT** | SHA-256 → UUIDv8 is sound with canonical-tuple comparison before deduplication. Enrichment preserves identity; corrections follow the supported supersession route. Example A now supplies `t_out` and attributes failures correctly. O-RX-1a must be a successor oracle: the frozen uppercase `Mars` serialization is not silently interchangeable with lowercase `mars`. |
| **AM-3 — writer grain** | **ACCEPT** | Per-body geometry/contact work followed by per-class/path/version interpretation fits the frozen two-phase architecture. Registry mutation and chart-serving transactions are correctly separated. Chart locking precedes legacy coverage mutation; substeps must preserve the outer writer transaction’s ownership. |
| **AM-4 — Moon/day tier** | **ACCEPT_WITH_AMENDMENTS** | EPHEMERAL results and query receipts are compatible with Moon’s exclusion from global sky rows and its separate `moon_on_demand` contact coverage. F-7 still owes the concrete receipt store, identity, rendering and manifest-exclusion implementation. |
| **AM-5 — completeness** | **ACCEPT_WITH_AMENDMENTS** | Both earlier P1 aspects are closed normatively. The proposed additive checks complement existing consumer guards. Full SQL enforcement, seal replay, verification implementation and the digest omission identified below remain gate work. |
| **AM-6 — ṣaḍbala** | **ACCEPT_WITH_AMENDMENTS** | Pick **Option C**, `sad_bala_sufficient` v1.0. Raw rūpas belong in typed evidence; the scored output is unitless. Correct the remaining factor-versus-membership `null_state` wording and supply F-5’s storage/citation details. |
| **AM-7 — P5 / 1204** | **ACCEPT_WITH_AMENDMENTS** | **1204 itself: ACCEPT.** A qualifier relationship record is appropriate for P5’s interpretation and lineage. Declaration consumption, numerical evidence and actual evaluator fixtures remain F-5/F-6 requirements. |
| **AM-8 — P6 / 1205** | **ACCEPT, withdrawal only** | Retaining the five concrete frame kinds avoids the earlier inheritance bypass. No 1205 migration or implemented inherited-frame contract is accepted here. Future P6 context, parent admission and containment remain held. |
| **AM-9 — nodes** | **ACCEPT** | The placement discrepancy is correctly scoped: XXVI.2 supports treating Rāhu/Ketu like the Sun for favourable houses. It does not independently establish node vedha pairs, detailed phala or nodal dṛṣṭi. No L0 repair is authorized. |

**AM-6 pick — Option C**

Adopt the versioned **unitless step factor**:

```text
sad_bala_sufficient = 1 when total ṣaḍbala ≥ the graha threshold
                     0 otherwise
```

The cited thresholds are Sun **6.5**, Moon **6**, Mars **5**, Mercury **7**, Jupiter **6.5**, Venus **5.5**, Saturn **5 rūpas**.

Classically, this represents the cited sufficiency predicate without inventing a continuous probability or blending ṣaḍbala with bhāvabala. Engineering-wise, it satisfies the factor’s `[0,1]` output range and `kgf_units_ck`; storing raw rūpas as that output would satisfy neither contract.

Missing, incompatible or unsupported operands—including nodes without a cited threshold—leave the **factor** unqualified. A soft factor’s zero or unknown contribution must not alter `admission_state`, which 1155 derives from necessary predicates.

The authored entry must cite:

1. **Phaladīpikā IV.22–23**, corpus locator `phaladeepika:PG79:C1`, with the actual edition, translator and corpus-document identity. The repository locator alone does not identify the edition.
2. **IV.24 / PG80:C1 only for the separate bhāvabala composition statement.**
3. The actual L1 operand: fact ID/category, subject, build, ayanāṃśa, verification tier, numerical value and unit; any conversion must be explicit.
4. The versioned factor, consuming path membership and adopted ranking policy. The classical threshold does not establish calibrated event probabilities.

A:830 still assigns `null_state` to the membership. It belongs on **`ka_gochara_factor`** (`1154:310–334`), as F-5 already acknowledges.

**Migrations and compatibility**

**1204 is correct and minimal for its stated scope.**

- `kgrr_object_role_ck` retains all nine existing roles and adds exactly `av_qualifier` (`1204:117–122`).
- The replacement `ka_gochara_object_selector_ok` adds the same role. Removing that addition and normalizing formatting leaves the executable validator equivalent to 1154.
- Embedded and standalone preflight blocks agree.
- Migrations 1153–1157 remain unchanged.

The selector widening is necessary: a rule path must be able to select the role its records carry. It preserves existing agent/relation validation, selector consistency, contact ownership, coverage checks, relative-frame restrictions, prerequisite finalization and seals.

Its precise consequence is that **any otherwise valid path can select `av_qualifier`**. SQL does not restrict that role to P5, residence contacts or declaration-consuming evaluators. Those remain explicit writer/evaluator requirements.

Replacing a CHECK helper does not automatically rescan existing rows. Here the change is a strict widening, so previously valid selectors remain valid; a future tightening would require separate validation. [PostgreSQL constraint documentation](https://www.postgresql.org/docs/17/ddl-constraints.html)

**Idempotency and replay require the correct distinction.** The migration runner verifies the recorded hash and skips an already applied migration (`migrate.ts:796–801`), and commits SQL with its migration-ledger record atomically (`829–839`). Bare SQL replay intentionally refuses once 1204 is recorded. Thus 1204 is **runner-idempotent**, not arbitrarily repeatable standalone SQL.

**Protected-window wiring is correct by source inspection.** The protected migration list, manual dispatch, protected environment, pinned deployment SHA, exact selection and capability grant/revoke include 1204. The transactional CHECK replacement has no committed unconstrained interval. Its locks do not themselves prove application-writer quiescence; the migration correctly leaves that as an operational requirement. [PostgreSQL locking documentation](https://www.postgresql.org/docs/17/explicit-locking.html)

**P5 should remain a qualifier represented by an auditable relationship record.** The record carries interpretation and provenance against a real residence contact; BAV/SAV measurements remain static operands. This preserves the shared physical root and separate P5a/P5b paths. Neither record existence nor an invented universal multiplier establishes admission.

The PR fixture uses a real residence contact and exercises the widened vocabulary, but its `consumeDeclaration` is test-local and checks existence/category. Identifier strings are not numeric bindu evidence. It does not close F-6’s actual evaluator and numerical-mismatch cases.

**1205 is absent.** The retained frame kinds are `moon`, `lagna`, `dasha_lord`, `graha` and `bhavat_bhavam`. The rejected `inherited` arm has not been implemented.

**AM-5 closure, executable evidence and gaps**

I ran the supplied Python cases without bytecode or file creation. Their output matched `am5_cases_output.txt` byte-for-byte. I also ran **37 additional in-memory assertions**, including adversarial cases that expose omissions in the model. These are logic checks, not PostgreSQL acceptance tests.

**The original W2, exactly as written, is now refused.**

```text
Sealed registry paths: P1, P5a
Path pins:             P1 included; P5a included
Stored obligations:    P1 obligations only
Stored intervals:      every stored obligation covers the whole horizon
Partition:             same horizon; exactly the stored obligations' relations
Inventory digest:      correctly recomputed from those stored rows
Records/windows:       empty
```

Under v0.5, each included pin must carry a nonempty finalized commitment. Keeping that row set, with P5a’s required commitment but **no P5a obligations inserted**, produces `committed_set_mismatch`. The two committed P5a IDs have no corresponding obligation rows. A verifier that merely rehashes the incomplete stored rows cannot defeat this check.

Trying to preserve the old state without supplying any commitment fails the new included-pin requirement. Relabelling it `computed_empty` requires an explicit disposition and matching independent verification.

My additional cases confirmed:

| Adversarial case | Observed result |
|---|---|
| W2: P5a included, obligations never inserted | `committed_set_mismatch` |
| Included pin with empty commitment | Refused at insertion |
| Sealed registry path without a pin | `registry_unaccounted_path` |
| Stored obligation without intervals | `obligation_uncovered` |
| False `computed_empty`, verifier expects a nonempty set | Verification mismatch |
| Smaller committed **and stored** set, verifier expects the full set | Verification mismatch |
| Genuine empty set with agreeing verification | No completeness violation |

The last two distinguish structural completeness from semantic derivation. If writer and verifier independently arrive at the same wrong set, SQL cannot discover the doctrinal mistake. A:680–690 now states that residual accurately.

**Different input snapshots cannot combine under the specified binding.**

A:498–534 restores a single snapshot per chart/generation, binds every interval to its input digest, incorporates that digest into inventory/ledger identities, and requires live-input and manifest-vector checks at first publication.

I tested genuinely nonoverlapping January/February intervals, avoiding an overlap rejection that could conceal the intended defect:

- Adjacent intervals carrying the same snapshot identity cover the horizon.
- Changing L1, AV declaration, dasha or manifest-vector components changes the input digest.
- A February interval carrying each changed digest is refused against the original inventory.
- A second snapshot for the same generation is refused.

Changed inputs therefore change **completion digests**. They need not change the nine-field `ob_id`; wording about “every identity” should remain scoped accordingly.

**The model is a partial executable abstraction, not full correspondence evidence.**

| Area | Observed model limitation |
|---|---|
| Partition and manifest checks | A deliberately wrong partition horizon, relations and convention passes because M:57 checks only whether `partition` is present. Incorrect manifest identity/horizon/vector also passes unless separately supplied through the limited drift parameters. |
| Seal lifecycle | `sealed` and `manifest` are unused state. A caller can select `first=False` on a never-sealed instance. Marking the model sealed does not stop subsequent writes. |
| Replay fidelity | M:70–71 still apply supplied drift checks when `first=False`, contrary to the normative replay branch’s explicit omission of live-input drift. |
| Interval input storage | `put_iv` checks the supplied digest but does not store it in the interval row (`M:41–48`). This models insertion rejection, not persisted FK/digest evidence. |
| Independent verification | C3 supplies an expected digest. It does not implement the separate inventory derivation required by O-RP-9. |
| Assertions and types | The supplied case runner prints outcomes without asserting expectations. It also omits closed exclusion-reason validation and real storage-domain validation. |

C16 therefore demonstrates only the effect of disabling registry accounting. It does **not** execute initial seal → identical replay → registry advancement → replay, with persisted manifest binding and immutability.

This keeps v1.3 rank 3 **PARTLY** closed. The normative branch is appropriate, but its promised lifecycle evidence is outstanding.

A BEFORE INSERT trigger runs before `ON CONFLICT` handling, so the explicit replay branch is necessary. It bypasses only the **new** first-publication checks; the existing 1153 seal guard remains operative. Replay should not be described as unconditional acceptance after arbitrary legacy manifest or coverage changes. [PostgreSQL INSERT documentation](https://www.postgresql.org/docs/17/sql-insert.html)

**New P2 — exclusion evidence is omitted from the inventory digest.**

A:556 requires exclusion `basis` and, for specified reasons, `ruling_ref`. A:600–610 says independent digest comparison validates exclusion bases. But the pinned preimage at A:592–598 contains only:

```text
path | rule_version | disposition | reason | committed IDs
```

It contains neither `basis` nor `ruling_ref`. Changing those fields leaves the digest unchanged; my adversarial case reproduced this.

Include their canonical values in the verified preimage, or specify a separate explicit comparison that establishes the same binding. Digest equality alone cannot currently prove the claimed exclusion-basis check. Update vectors when that amendment lands.

**Correspondence with 1155/1156 must remain additive.**

The proposed completeness checks correctly address something the applied migrations cannot see: a required path with no consumer row. `1156:509–518` enumerates existing records/windows; it cannot infer absent searches.

The implementation must retain:

- Exact `event_class` partition keys and current canonical `coverage_facts`.
- Bridged conventions, searched relations, contact ownership and contact `t_in` containment.
- Support/window containment and separate `moon_on_demand` treatment.
- Existing coverage-drift classification, including valid extension behavior.
- Chart EXCLUSIVE followed by global SHARED, including receipt-only transactions.

The Python model exercises none of those SQL interactions.

**Additional A5.3 contracts still needed**

These belong in the existing gate follow-ups:

- **Canonical storage mapping:** the synthetic `self` token is not the stored `affected_person` value `native`. Period-lord obligation roles must resolve through the pinned dasha snapshot to actual grahas in records/selectors. Frame arguments, target bytes, timestamp precision and delimiter handling need exact contracts.
- **Declared class scope:** define the expected class census and ensure an entirely absent class is reported `not_searched`. Iterating existing inventories alone does not establish that census.
- **Registry-version selection:** pinning every sealed version needs an explicit treatment of historical/superseded versions so they neither disappear nor unintentionally double-count interpretation.
- **Candidate replacement:** specify deletion/invalidation across verification rows, manifest bindings and derived contacts/records/windows. Replacing snapshot metadata must not preserve outputs computed under the previous inputs.
- **Implementation inventory:** replace the stale “four content tables” wording and enumerate all required immutability, digest, FK, interval and lock guards. The abbreviated migration object count is not an enforcement specification.

AM-9’s source boundary should remain equally precise. The inspected L0 seed omits favourable node house 10 and retains favourable Ketu-12; the repository transcription supports identifying that discrepancy. Reusing a Sun vedha citation in a helper does not independently source node vedha or detailed node phala.

**Ranked amendments and closure of v1.3 items**

| Previous rank | Status | Decision |
|---:|---|---|
| **1 — finalized/validated obligation sets** | **CLOSED** | Nonempty included commitments, stored-set equality, explicit validated `computed_empty` and mandatory verification close the original W2 defect. |
| **2 — immutable search-input binding** | **CLOSED** | One snapshot, interval binding, digest inclusion and first-publication drift checks close the normative gap. Disjoint mixed-snapshot intervals are refused by the model. |
| **3 — seal replay after registry advance** | **PARTLY** | The normative replay branch is repaired. The supplied model lacks the actual seal lifecycle and four-step replay test. |
| **4 — enrichment example A** | **CLOSED** | Required `t_out` is supplied, and CHECK/UPDATE-guard attribution agrees with 1153. |
| **5 — complete W1 preimage/digest** | **CLOSED** | Complete input/inventory preimages are published; recomputation matches. H1/H2 ledger digests are reproducible. Future preimage changes must update these vectors. |

There are **no remaining P1 batch-acceptance blockers**. Ranked remaining gate work:

| Rank | Severity / tracking | Required completion | Blocks |
|---:|---|---|---|
| **1** | **P2 / F-3, prior rank 3** | Implement the additive storage/seal checks and protected runner wiring; execute database adversaries and the full replay lifecycle, including wrong-manifest and post-seal mutation rejection. | Inventory migration acceptance |
| **2** | **P2 / new** | Bind exclusion `basis`/`ruling_ref` to verification; add mutation tests and revised digest vectors. | AM-5 verification acceptance |
| **3** | **P2 / F-4** | Finish canonical bytes, storage-domain mapping, class/version scope, geometry planning and input-change invalidation; retain O-RX-1a/O-RW-1 evidence. | A5.5 identity and writer gate |
| **4** | **P2 / F-5** | Implement typed rūpa/bindu evidence, declaration/build binding and P5 applicability; correct factor-row `null_state`; identify edition/translator. | AM-6/AM-7 writer acceptance |
| **5** | **P2 / F-6** | Exercise actual P5 evaluators with numerical mismatch, BAV/SAV selection and independent missingness; repair stale oracle-map references and sentinels. | P5/A5.5 acceptance |
| **6** | **P2 / F-7** | Implement Moon receipts, canonical result rendering and generation-5 digest binding/exclusion, with before/after-seal evidence. P6 remains held. | Moon/day implementation acceptance |

UUIDv8 remains acceptable: masking leaves **122 digest bits**, with a birthday-collision scale around \(2^{61}\), not guaranteed uniqueness. I reproduced the contact vectors, correction UUID and masking-collision example. Equality/divergence checks must precede UUID-keyed deduplication; `ON CONFLICT DO NOTHING` alone is insufficient. [RFC 9562 §5.8](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.8)

**What I could not verify**

I did not connect to production, inspect live migration-ledger hashes, verify deployment quiescence, attest installed ephemeris versions or retrieve the cited live L1 node fact. Production application of 1153–1157 remains the supplied premise.

I did not run PostgreSQL, Vitest or pytest. The inspected integration suite requires a disposable database and creates temporary files, which conflicts with this review’s no-file-creation instruction. Author-reported database results are not independent results from this review.

Classical assessment relies on repository transcriptions; I did not inspect the scanned edition. The new AM-5 migration, independent verifier and generation-5 digest implementation are not present as completed enforcement in the reviewed exhibit.

No file was created, edited, moved or deleted; no git write command was run. The checkout remained clean at `5626290c6`.