---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.1"
reviewer: "Codex gpt-6-astra"
date: "2026-10-01"
verdict: REJECT
reviewed_commit: "55a6ea8a2 (campaign/pravaha) + 45f4604b9 (PR #2817)"
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT as submitted.**

The revision closes the dangerous, unrestricted `inherited` change by **removing migration 1205 from PR #2817**. Migration 1204’s two vocabulary changes are consistent and minimal.

The batch still has blocking contract defects: AM-1/AM-3 misclassify convention bootstrap transactions; AM-2 contradicts its own canonical-byte rule; AM-5 asserts a completeness representation that the existing coverage contract does not provide. AM-7 improves the model, but its declaration binding remains unspecified, and the replacement compatibility test contains a false-positive path.

**Evidence references.** `A` denotes [amendment draft v0.2](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55b/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md), `S` denotes [frozen specs v1.4](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55b/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md), and `O` denotes [frozen oracles v1.4](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55b/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_TEST_ORACLES_v1_4.json). Numbered migration references identify the corresponding SQL file under `platform/migrations/`. Migrations 1153–1157 were inspected at the local `origin/main` ref, `4eb40bec1`; PR files were inspected at `45f4604b9`.

**Per-amendment verdicts and v1.0 finding closure**

| Amendment | Verdict | v1.0 closure and evidence |
|---|---|---|
| **AM-1 — convention** | **ACCEPT_WITH_AMENDMENTS** | **PARTLY.** Convention versus generation identity, deterministic L1 node selection, audit-field exclusion, and withdrawal of the self-test as domain authority are corrected (`A:42–83`). The complete serialized vector, governed domain endpoints/reference, and digest vector remain unpinned. Convention bootstrap is assigned to the wrong transaction category. |
| **AM-2 — identities** | **REJECT** | **PARTLY.** Flat hashing, 122 retained digest bits, collision taxonomy, and versioned correction intent are sound (`A:97–138`). Lowercase canonicalization contradicts the uppercase O-RX-1 bytes declared canonical. Numeric/sign normalization and expected oracle UUIDs remain incomplete. |
| **AM-3 — persistence/substeps** | **REJECT** | **PARTLY.** Per-table persistence, preservation of global identities, candidate dependency order, and sealed-generation refusal replace the invalid blanket-delete rule (`A:156–179`). The combined “registry/convention bootstrap” transaction remains incompatible with applied lock guards (`A:181–186`). |
| **AM-4 — Moon/day** | **ACCEPT_WITH_AMENDMENTS** | **PARTLY.** The transiting-Moon correction and ephemeral response policy are closed (`A:201–217`). Persistent query-receipt storage, identity, coverage partition key, replay, and post-seal manifest treatment are still unspecified. |
| **AM-5 — coverage** | **REJECT** | **PARTLY.** `partition_key=event_class`, writer ownership, and transactional bridge/snapshot binding are corrected (`A:233–239`). Cross-path completeness is described but not representably specified; putting paths in the relation set does not solve it (`A:241–257`). |
| **AM-6 — ṣaḍbala** | **ACCEPT_WITH_AMENDMENTS** | **CLOSED for the five substantive v1.0 qualifications.** Option C, thresholds, bhāvabala distinction, unsupported nodes, typed raw evidence, versioning, and zero-score/admission separation are folded (`A:273–307`). A further clarification is required: missing soft-factor evidence must not incorrectly change SQL `admission_state`. |
| **AM-7 — P5/1204** | **ACCEPT_WITH_AMENDMENTS** | **PARTLY.** Real residence evidence, shared physical roots, separate P5 forms, and no universal multiplier are correctly stated (`A:331–349`). Actual form encoding, applicability, and AV-declaration binding remain requirements rather than completed contracts. The revised tests do not establish the claimed full compatibility or P5 acceptance. |
| **AM-8 — P6/1205** | **ACCEPT — withdrawal from this PR only** | **CLOSED for the shipping defect.** No 1205 migration or preflight remains at `45f4604b9`; no frame-validator widening ships. The unsafe scored/inherited route is removed. Future P6 implementation and its behavioral acceptance remain open (`A:381–414`). |
| **AM-9 — L0 finding** | **ACCEPT** | **CLOSED.** Placement, vedha, and detailed-phala provenance are separated; the unsupported interpretation of `BPHS_CH29` is retracted; Ketu-12 is referred for sourcing/reclassification, without authorizing a repair or nodal dṛṣṭi (`A:425–445`). |

Prior ranked findings 1–6 are accounted for above. **Prior rank 7 is PARTLY closed:** operational wording and coverage-report qualification improved, but test overclaims and stale packet statements remain. The additional v1.0 gaps are accounted for below.

**AM-1–AM-5: remaining contradictions and consequences**

**1. Convention bootstrap must use the chart transaction category.**

`A:42–44` and `A:181–185` group convention registration with registry bootstrap and cite the global/chart separation rule. Applied migration 1153 explicitly makes sky-convention inserts acquire the chart-family lock:

- `1153:560–578`: substrate writes require chart context.
- `1153:604–607`: sky-convention inserts invoke that guard.
- `1153:450–469`: chart-family and global-exclusive registry locks cannot coexist.
- `1154:407–410`: rule-path insertion takes the registry/global-exclusive route.

A literal combined bootstrap fails in either order. This also corrects any imprecision in my v1.0 recommendation: **sky conventions are not 1154 registry rows.**

Specify separate orchestrator-owned transactions:

1. Registry transaction: predicates, factors, paths, memberships, and rule seals.
2. Chart-serving transaction: chart-family lock first, then conventions, bridge, AV declaration where required, substrate/contact work, and chart-owned data.

The PR’s own fixture already separates these correctly: `gochara_b6_v15_migrations.db.test.ts:292–305` inserts the convention under `chartCtx`, then registers rules in another transaction.

The two-phase grain itself is reasonable. Per-body geometry followed by class/path evaluation is consistent with `S:669`. Candidate replay must preserve the corrected dependency rules; it cannot delete shared contacts while another path still references them.

**2. AM-1 still does not supply a byte-exact convention contract.**

The amendment now correctly distinguishes `'5.0'` from `sha256:<digest>`. However:

- `A:76–78` gives grid components without one complete serialized string.
- `A:80–83` delegates domain endpoints to an unnamed ruling rather than identifying its exact values/reference.
- The cited `substrate.py:153–171` at `694d16e9c` uses a compound ephemeris label and `nakshatra:13.20`; these differ from the revised proposed values.

These can be deliberate corrections, but they must produce a newly pinned convention vector and digest. They cannot be represented as already interchangeable bytes.

Pin one complete vector, its canonical serialization, the expected digest, and the domain authority. Keep full-domain ordinal boundaries distinct from the currently searched partition. O-RX-1 permits extension **inside the fixed domain**; it does not permit changing the domain while retaining the old convention identity.

**3. UUIDv8-from-SHA-256 is sound; the submitted canonicalization is not yet coherent.**

The construction is valid: take the first 16 SHA-256 bytes, set the version nibble to 8 and variant to binary `10`. That retains 122 digest bits, with a birthday-scale collision threshold around \(2^{61}\) generated identifiers. UUIDv8 does not itself guarantee uniqueness. [RFC 9562 §5.8](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.8)

The three collision cases in `A:116–123` are appropriate, provided comparison happens before UUID-keyed deduplication and divergent immutable payloads are not treated as legitimate replay.

The immediate contradiction is:

- `A:103–105`: lowercase stored body tokens are canonical.
- `A:109`: O-RX-1’s printed serialization **is** canonical.
- `O:65`: that serialization begins with uppercase `Mars`.

Independent in-memory calculations confirm distinct results:

| Input bytes | UUIDv8 |
|---|---|
| `Mars\|conjunction\|point:198.52\|c0\|1` | `87b023cc-c9f3-8979-9b37-96701f285356` |
| `mars\|conjunction\|point:198.52\|c0\|1` | `23276d7c-c127-8f4c-9ad5-6b7c8da8020f` |
| `mars\|conjunction\|point:198.52\|c0\|2` | `b6cd1a15-4820-859f-b6e4-d7e144e59416` |
| `mars\|conjunction\|point:198.52\|c0\|3` | `c523b443-fcc4-8665-8bfc-52b6e3e831d9` |
| `mars\|conjunction\|point:198.52\|c0\|4` | `8e423fdf-6ab5-842a-ab1f-b31d4720d319` |

**Choose lowercase and explicitly amend the oracle serialization in a reviewed successor.** Preserve the frozen v1.4 file.

`A:134` also overstates that expected UUID vectors are pinned in the oracle file. The inspected O-RX-1 has byte examples and behavioral requirements, but no expected UUID literals.

Two further pins remain necessary:

- “No trailing zeros added or stripped beyond stored rendering” is not canonical numeric normalization. The physical target strings `point:198.52` and `point:198.520` both satisfy `1153:632–635` and produce different IDs for the same longitude.
- §6.1 does not settle the promised sign/star normalization. Choose one absolute-sign encoding and an explicit star-index mapping; SQL accepts `star:1` through `star:27`, while the tārā oracle uses zero-based indices.

For corrections, name the identity component that changes. A time-only correction cannot retain the same object/convention/ordinal and receive an arbitrary fresh UUID. A changed method/convention identity is a coherent route, retaining the supersedes chain.

O-RX-1 acceptance must prove one physical object, ordinals 1–3, truncated-center enrichment without identity change, and ordinal 4 appended without renumbering. Forced collisions must include differences confined to bits overwritten by the UUID masks.

**4. AM-5 has not defined a usable completeness representation.**

`A:242` says evaluated paths are “named in the partition’s relation set.” Applied coverage treats these as different concepts:

- `1155:733` checks that the contact’s actual relation occurs in `relations_searched`.
- `1155:361–380` snapshots only convention, horizon, and relations.
- `1156:499–545` classifies extension using horizon containment and relation-set containment.

A flat path list, a flat relation list, and one `completed_horizon` cannot describe which **path version searched which relations/targets over which intervals**.

For example, P1 searched over January and P5 searched over February must not become “P1 and P5 searched January–February.” Adding both names to an array does not prevent that false implication.

Specify a versioned receipt representation and its storage, including at least path/version, actual searched intervals, required relation/target inventory, input/convention identity, and completion or missing-input state. Then specify how publication and serving consume it. An existing JSON field might host a carefully defined encoding; “schema impact: none” is not established merely by saying the partition carries this information.

Two further requirements:

- Acquire the chart-family lock **before mutating legacy coverage**, not only when later inserting records. The legacy coverage table has no Gochara-family trigger that supplies this ordering.
- Distinguish incomplete search, completed rejection, and completed evaluation with unresolved prerequisites. “All paths evaluated” does not make an unknown result equivalent to a qualified “none admitted.”

The existing seal checks validate consumers and membership; they do not prove that every required path was executed.

**5. AM-4’s lifecycle direction is acceptable, but its receipt contract remains open.**

The Moon-agent correction matches `1153` and O-SS-4. Ephemeral answers with independent coverage are compatible with frozen sealing.

Nevertheless, `A:208–219` promises persistent query receipts without specifying where they live, their key, or how replay works. Define how query coverage is kept distinct from sealed build coverage, whether it is excluded from the published manifest digest, and how the receipt binds manifest, query interval, inputs, and result digest. “No mutation of the sealed generation” needs that precise distinction.

**AM-6 pick: Option C**

Use **`sad_bala_sufficient` v1.0**, a unitless sufficiency classification:

| Graha | Threshold, rūpas |
|---|---:|
| Sun | 6.5 |
| Moon | 6 |
| Mars | 5 |
| Mercury | 7 |
| Jupiter | 6.5 |
| Venus | 5.5 |
| Saturn | 5 |

For a supported, compatible operand: output `1` at or above its threshold, otherwise `0`. Retain the raw measurement and its units as operand evidence.

The classical basis is a sufficiency classification, not a universal continuous event multiplier. The repository transcription at `PROMISE_NATURE_YOGA_MAP_v1_1.md:244–254` supports these seven thresholds and separately identifies IV.24 as bhāvabala composition.

Engineering reasons:

- It satisfies unchanged `kgf_units_ck` and the finite `[0,1]` output constraint (`1154:331–338`).
- Adding `'rupas'` alone would not make an unbounded raw measurement legal in that factor catalogue.
- A normalized ratio introduces a numerical mapping not supplied by the cited sufficiency rule.
- Raw evidence preserves explanatory detail without changing the scoring codomain.

**Required clarification:** `A:287–290` must distinguish **score qualification** from `admission_state`. Migration `1155:822–832` derives admission from necessary predicates: all true means admitted. Missing ṣaḍbala, when ṣaḍbala is only a soft factor, cannot independently set that record’s admission to `unqualified`.

Set the factor’s missing-input policy explicitly to `null_state='unqualified'`; propagate score qualification as specified. Preserve the admitted interval. A supported below-threshold value may yield numerical zero for ranking, while admission remains governed by hard predicates.

The authored entry must cite:

1. **Phaladīpikā IV.22–23, `phaladeepika:PG79:C1`**, identifying the actual served edition/translator.
2. **IV.24, `PG80:C1`**, only for the separate bhāvabala statement.
3. The actual L1 operand: fact/category, subject, build, value, unit, ayanāṃśa and verification tier; document any unit conversion rather than inferring units from a field name.
4. The versioned path membership and adopted ranking policy. The threshold citation does not establish a calibrated event probability.

No cited threshold should be manufactured for Rāhu or Ketu.

**Migrations and P5/P6 modelling**

**1204: minimal SQL change, acceptable with test amendments.**

Source comparison confirms:

- The record CHECK retains all nine old roles and adds only `av_qualifier` (`1204:117–122`).
- Removing the added token from the selector function restores the old executable token sequence, apart from whitespace (`1204:130–149`; `1154:243–261`).
- The embedded and standalone preflight blocks are byte-identical.
- Migrations 1153–1157 are byte-identical between the inspected `origin/main` and PR commit.

The selector widening is necessary. Otherwise a path cannot select the role its records may carry.

No existing contact FK, coverage guard, relative-frame check, prerequisite finalization, rule seal, publication seal, or membership restriction is removed. The change deliberately widens the role vocabulary. It does **not** enforce that the new role is used only by P5, only with residence/house-span records, or only after declaration consumption. Those guarantees require a named writer/evaluator gate if they remain outside SQL.

**Replay and protected window are correctly wired by source inspection.**

- `platform/scripts/migrate.ts:138–158` protects 1204 from routine application.
- `.github/workflows/deploy.yml:963–999,1043–1101` uses the manual protected route, verifies the deployment SHA, selects 1153–1157 plus 1204, and brackets execution with capability grant/revoke.
- `migrate.ts:796–801` skips an applied file after hash verification.
- `migrate.ts:829–839` applies each file and its ledger entry in one transaction.

Thus 1204 is **replay-safe through the runner**, not independently repeatable SQL: its gate rejects an already-recorded 1204. The protected selection remains per-file atomic, not one transaction for the entire family.

The transactional CHECK swap has no committed unconstrained interval. It still takes a substantial table lock and can block or time out; the corrected header properly avoids claiming that deployment concurrency pauses writers. [PostgreSQL ALTER TABLE documentation](https://www.postgresql.org/docs/17/sql-altertable.html)

Replacing a CHECK helper does not automatically revalidate existing rows. Here, the strict widening preserves previously valid inputs. Any later tightening or rollback needs explicit checks and revalidation of affected selector rows as well as relationship rows. [PostgreSQL CHECK documentation](https://www.postgresql.org/docs/17/ddl-constraints.html)

**The “every old role” test is not a valid detector.**

In `platform/tests/integration/gochara_b6_v15_migrations.db.test.ts`:

- Lines 299–301 seed coverage only for `karaka`, `av_qualifier`, and `not_a_role`.
- Lines 254–255 call `factsFor` before executing the INSERT.
- Line 228 throws `no coverage partition` when that lookup fails.
- Lines 342–349 accept any rejection whose message does not mention `kgrr_object_role_ck`.

Eight old-role probes therefore fail before the INSERT. The remaining dangling-contact probe can fail in the BEFORE coverage guard before CHECK evaluation. These failures cannot demonstrate role acceptance.

The static companion has the same weakness by another route. At `platform/tests/unit/migrations/gochara_b6_v15_contract_static.test.ts:113`, its search starts at the first `ADD CONSTRAINT` occurrence—which is the rollback comment at `1204:55`—and scans the rest of the file. I removed `lord` from the actual CHECK **in memory**; its “all roles present” predicate still passed.

Require valid acceptance probes for every old role, with necessary coverage/contact fixtures, or an isolated check-specific assertion. A mutation removing an old role from the actual CHECK must make the detector fail.

**The replacement residence fixture is only partial P5 evidence.**

The suite now includes 1156/1157 and uses a residence contact. Those prior deficiencies are corrected. However, `insertRecord` still hardcodes:

- `object_kind='degree_point'` for the purported span;
- day grain;
- a P1 citation;
- `fixture=false` with synthetic-looking `fact-1` evidence.

See `gochara_b6_v15_migrations.db.test.ts:257–263`. It supplies no AV declaration consumption, competing BAV/SAV operands, or P5 missingness proof. It demonstrates selected SQL plumbing, not the complete residence-qualification contract.

**P5 should remain a qualifier, with an auditable relationship record for its transit interpretation.**

I support the revised modelling direction over a qualifier with no record:

- Reuse the physical residence contact and root.
- Resolve the frame-relative house to an absolute physical sign before identity creation.
- Store the AV qualification and lineage as an interpretation of that transit.
- Keep static BAV/SAV measurements as operands.
- Do not manufacture event admission from the mere existence of that record.

The remaining contract must choose how P5a and P5b are separately identified, how their class/person applicability is bound, and how distinct outcomes survive reduction without duplicate physical evidence.

`A:350–355` does not yet close 1157’s deliberately unresolved key meaning. Name the precise AV-build/declaration key, where each record binds it, the category compatibility check, and the read-back rejection behavior. Preserve O-BP-1/O-BP-2 distinctions and make O-BP-3 fail when the consumed declaration is missing or mismatched.

**1205: absent, therefore no replacement migration can be approved.**

The withdrawal closes the previous shipping risk. The retained frame validator has **five** kinds—`moon`, `lagna`, `dasha_lord`, `graha`, `bhavat_bhavam`—not the four stated at `A:404–405`.

The new negative test shows inherited/scored insertion remains rejected under the unchanged validator. It does not establish a general P6 testimony-only gate. That belongs to the future implementation and its acceptance tests.

**Remaining gaps for A5.3, including prior findings**

| Gap | Closure status | Required contract |
|---|---|---|
| Coverage completeness across path commits | **PARTLY** | Event-class key fixed; typed per-path/version/interval receipts, applicability inventory, publication and serve-time completeness remain open. |
| On-demand work after sealing | **PARTLY** | Ephemeral answer policy supplied; persistent receipt/key/replay/manifest treatment remains open. |
| Relationship/window identity serialization | **NOT CLOSED** | Pin nulls, ordering, versioned prerequisites, citation/input changes, interval encoding, and replay equality. AM-2 only addresses physical/contact identity. |
| Geometry planning and invalidation | **NOT CLOSED** | Define the qualified target/relation inventory before solving and record why a change re-solves or only re-scores, as required by `S:795–801` and O-RW-1. |
| Admission and P6 behavioral oracles | **NOT CLOSED** | The map still reports B6-F16/B6-F17 as strict-xfail interface sentinels. Require actual union admission, channel/unknown behavior, tārā class, parent binding, coverage, and zero score effect. |
| Convention bridge evolution | **Additional gap** | `1153:1016–1034` gives each legacy convention one immutable sky-convention mapping. Define how a new sky convention caused by domain/method correction gets a compatible new legacy identity; existing mappings cannot be repointed. |
| Concrete P6 parent context | **Additional gap for deferred work** | `1156:247–265` has no frame/person fields on the window. Resolve context from specified admitting objects/records, with an unambiguous rule when members differ; also restrict annotation support to the admitted parent interval. |

The oracle map remains **ACCEPT_WITH_AMENDMENTS as a partial-coverage report**, not behavioral closure. Its line 133 still refers to 1205 in PR #2817, and `A:484–486` still describes the old omitted-migration/conjunction fixture. Both statements are stale.

**Ranked amendments required**

| Rank | Severity | Required amendment and acceptance evidence | Blocking scope |
|---:|---|---|---|
| **1** | **P1** | Replace AM-5’s path-in-relation-set claim with an explicit completeness representation and publication/serving rules. Demonstrate partial searches cannot become complete-empty or imply unsearched combinations. | Spec batch and A5.3 coverage acceptance |
| **2** | **P1** | Correct AM-1/AM-3 bootstrap categories. Keep registry/global-exclusive transactions separate from chart-context convention/substrate transactions; take the chart lock before legacy coverage writes. | Spec batch and writer bootstrap |
| **3** | **P2** | Finish convention and identity bytes: exact vector/domain/digest, lowercase successor oracle, decimal/sign/star normalization, correction component, UUID vectors and collision controls. | Spec batch and identity acceptance |
| **4** | **P2** | Repair the old-role detector and residence fixture. Removing an old CHECK role must fail the test; valid old roles must pass the intended boundary. | PR #2817 acceptance |
| **5** | **P2** | Specify P5 form identity, applicability, typed operand lineage, and exact declaration consumption/read-back rejection. Preserve separate missingness and shared-root rules. | AM-7/P5 writer acceptance |
| **6** | **P2** | Clarify AM-6 score qualification versus hard-predicate admission; pin the factor’s null policy and evidence binding. | AM-6 factor consumption |
| **7** | **P2** | Define post-seal query receipt storage and coverage identity; complete deferred parent-context and temporal-containment rules before P6 lands. | Moon/day implementation acceptance |

Correct the stale checklist, oracle-map and test-debt statements alongside these changes. The withdrawn 1205 implementation is not a prerequisite for accepting an independently corrected, vocabulary-only 1204.

**What I could not verify**

I did not connect to production, inspect live migration-ledger hashes, verify the live L1 node fact, confirm installed Swiss/runtime versions, or verify writer quiescence. Production application of 1153–1157 remains the supplied premise.

I did not run PostgreSQL, Vitest, pytest, or the reported mutation suites. The inspected DB suite expects a supplied disposable database and creates temporary files; I did not invoke it under this read-only instruction. Verification consisted of source inspection, byte/token comparisons, independent UUID calculations, and an in-memory reproduction of the static detector’s false positive.

Classical conclusions use the repository’s cited transcriptions. I did not independently inspect the original scanned editions. No files were created, edited, moved or deleted; no git write command or production database operation was performed.

