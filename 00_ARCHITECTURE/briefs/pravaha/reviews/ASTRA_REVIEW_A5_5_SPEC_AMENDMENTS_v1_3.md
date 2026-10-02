---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.3"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: "454881c71 (campaign/pravaha) + f8b1c8b63 (PR #2817)"
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT — AM-5’s completeness P1 remains partly open. Migration 1204 independently receives ACCEPT.**

AM-2 fixes the two substantive identity contradictions identified in v1.2. Its new enrichment example needs a correction, but the normative identity contract now agrees with 1153.

AM-5 fixes interval conflation **for obligations actually present in its inventory**. It still falsely claims that its SQL detects an included path whose obligations were never inserted. It also removes v0.3’s explicit search-input identity without providing an equivalent binding. Consequently, the unconditional claim that partial search can never become complete-empty is not established.

The five existing P2 follow-ups remain deferred and do not drive this rejection.

**Evidence basis**

`A` denotes the [amendment draft v0.4](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55d/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md). `S` denotes the [frozen v1.4 specs](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55d/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md). `O` denotes the [frozen v1.4 oracles](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55d/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_TEST_ORACLES_v1_4.json). SQL references identify numbered lines in `platform/migrations/<number>_*.sql`.

I read the [v1.2 review](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/reviews/ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_2.md) before reviewing the revised exhibits. The supplied request packet still describes round 3/v0.3; this review follows the user’s round-4 scope and the actual v0.4 draft.

The final inspected local `origin/main` snapshot was **`d9d7993642f2ab1dfcdec54c81cfb751dca5babd`**. Migrations 1153–1157 are byte-identical between that snapshot, the initially inspected `65789c86c`, and PR commit **`f8b1c8b63d5cfab74789a7c856b8fc479d9640fe`**. Frozen specs/oracles are unchanged from the preceding reviewed campaign commit; the oracle inventory remains 57.

**Disposition of the two P1s**

| Prior P1 | Status | Judgment |
|---|---|---|
| AM-2 identity/correction versus 1153 | **CLOSED** | SQL-valid `span:` targets replace `sign:`. NULL/truncated enrichment retains identity; correction of an existing non-NULL reading requires a new identity and supersession. The malformed worked example is a separate repair below. |
| AM-5 completeness | **PARTLY — NOT CLOSED** | Per-obligation intervals, explicit seal integration, chart→global-SHARED locking and serving states are substantial improvements. Missing obligation sets and search-input binding remain unresolved. |

**Per-amendment verdicts**

| Amendment | Verdict | Assessment |
|---|---|---|
| **AM-1 — convention** | **ACCEPT** | Canonical string reproduces the stated SHA-256 digest. Domain, runtime labels, L1 node-selection rule and immutable bridge evolution remain coherent. Actual runtime and L1 attestations were not verified. |
| **AM-2 — identity** | **ACCEPT_WITH_AMENDMENTS** | The original P1 is closed. UUID construction, supplied vectors and correction identity check out. Repair example A’s missing `t_out` and incorrect CHECK attribution (`A:233–245`). |
| **AM-3 — writer phases** | **ACCEPT** | Two-phase grain and registry/chart transaction separation remain consistent with the applied contract. The explicit chart lock before legacy coverage writes is correct. |
| **AM-4 — Moon/day** | **ACCEPT_WITH_AMENDMENTS** | Ephemeral results, durable on-demand coverage and manifest exclusion remain coherent. F-7 still owns the concrete logging, digest and replay implementation. |
| **AM-5 — completeness** | **REJECT** | The universal rule works over a correctly finalized, input-bound inventory. The proposed checks do not establish those prerequisites; W2’s asserted refusal is false as written. |
| **AM-6 — ṣaḍbala** | **ACCEPT_WITH_AMENDMENTS** | Retain Option C. F-5 must correct `null_state` placement, identify the edition/translator and specify typed operand storage. |
| **AM-7 — P5/1204** | **ACCEPT_WITH_AMENDMENTS** | Both vocabulary widenings are correct and minimal. Residence-based qualifier records are appropriate. Complete P5 semantic acceptance remains F-5/F-6 work. |
| **AM-8 — P6/1205** | **ACCEPT — withdrawal only** | No 1205 migration/preflight or `inherited` frame arm exists in the reviewed PR. Future P6 behavior remains separately gated. |
| **AM-9 — L0 finding** | **ACCEPT** | Correctly confines the finding to favourable placement provenance and the unsupported Ketu-12 classification, without authorizing L0 changes or nodal dṛṣṭi. |

**AM-6 pick: Option C**

Adopt **`sad_bala_sufficient` v1.0**, a step function with `units='unitless'` and output range `[0,1]`.

| Graha | Threshold in rūpas |
|---|---:|
| Sun | 6.5 |
| Moon | 6 |
| Mars | 5 |
| Mercury | 7 |
| Jupiter | 6.5 |
| Venus | 5.5 |
| Saturn | 5 |

A supported total at or above its threshold produces `1`; below it produces `0`. Missing, incompatible or unsupported evidence leaves the score contribution unqualified. Neither missing evidence nor zero changes admission already established by necessary predicates.

The repository’s transcription supports sufficiency classification, without establishing a continuous event-strength mapping. Engineering-wise, the binary output satisfies unchanged `kgf_units_ck` and `kgf_range_unit_interval_ck` (`1154:330–338`). Adding `rupas` to the unit vocabulary alone would not make raw ṣaḍbala totals compatible with the factor codomain.

The authored entry must cite:

1. **Phaladīpikā IV.22–23, `phaladeepika:PG79:C1`**, with the actual edition, translator and corpus-document identity. The transcription is at `PROMISE_NATURE_YOGA_MAP_v1_1.md:244–250`.
2. **IV.24, `PG80:C1`**, only for the separate bhāvabala composition statement.
3. The consumed L1 fact’s ID, category, subject, build, ayanāṃśa, verification tier, raw value and unit, with any conversion explicit.
4. The versioned factor and consuming path membership, plus the adopted ranking/calibration policy.

No Rāhu/Ketu threshold is supplied by that citation.

`null_state` belongs to **`ka_gochara_factor`** (`1154:310–334`), not the soft-factor membership table (`1154:435–445`). F-5 correctly records this outstanding textual correction. The admission boundary agrees with `1155:822–832`.

**Migrations and modelling**

**1204: ACCEPT as a vocabulary-only migration.**

Independent comparison establishes:

- `kgrr_object_role_ck` retains all nine previous roles and adds exactly `av_qualifier` (`1204:117–122`).
- Removing that added value and normalizing whitespace/comments makes the replacement selector’s executable text equal to the 1154 function.
- Embedded and standalone preflight DO blocks are byte-identical.
- The applied 1153–1157 files remain unchanged.

Widening `ka_gochara_object_selector_ok` is necessary: a path must be able to select the role its records carry. The widening preserves agent/relation validation, selector consistency, contact ownership, coverage applicability, relative-frame restrictions, prerequisite finalization and seals.

It does not establish P5-only use, residence-only use or declaration consumption. Those remain the expressly named writer/evaluator gates.

**Runner replay and protected-window wiring are correct by source inspection.** `migrate.ts:138–159` protects 1204; `796–801` verifies and skips an already recorded file; `829–839` applies each migration and its ledger record atomically. Directly repeating recorded 1204 is intentionally refused by its preflight. Thus it is runner-idempotent, not freely repeatable standalone SQL.

`deploy.yml:963–999,1043–1101` retains manual dispatch, protected environment, pinned deployment SHA, exact migration selection and capability grant/revoke. The transactional CHECK replacement has no committed unconstrained interval; writer quiescence remains an operational prerequisite, as the migration now acknowledges. [PostgreSQL locking documentation](https://www.postgresql.org/docs/17/explicit-locking.html)

Replacing a function used by CHECK constraints does not automatically rescan existing consumers. This strict widening preserves previously valid selectors; a future tightening must inspect and revalidate them. [PostgreSQL constraint documentation](https://www.postgresql.org/docs/17/ddl-constraints.html)

The repaired old-role detector remains credible. My in-memory mutation removing `lord` from the executable CHECK list makes its bounded detector fail. The inspected DB fixture now seeds coverage for every old role and requires committed acceptance/read-back. Its broader P5 claims remain limited: `consumeDeclaration` is test-local, checks existence/category only, and the fixture stores identifier strings rather than numeric bindu evidence. Those are unchanged F-6 limitations.

**P5 should remain a qualifier represented by an auditable relationship record.** Its record attaches interpretation and lineage to an existing residence contact, preserving the physical root. Static BAV/SAV measurements remain operands. Separate P5a/P5b paths preserve their distinct outcomes; record presence alone must never establish admission.

**1205 is absent.** The retained frame validator has five kinds: `moon`, `lagna`, `dasha_lord`, `graha`, `bhavat_bhavam`. Withdrawal avoids the earlier arbitrary-path and relative-frame bypass. This review accepts no implemented P6 inheritance mechanism.

**Gaps and counterexamples**

**1. P1 — W2 cannot detect obligations that do not exist.**

`A:653–658` states that the writer inserts obligations and intervals for P1 only, then claims `obligation_uncovered` finds P5a obligations with zero intervals. Those P5a obligations were never inserted.

A concrete state satisfying the proposed checks is:

```text
Sealed registry paths: P1, P5a
Path pins:             P1 included; P5a included
Stored obligations:    P1 obligations only
Stored intervals:      every stored obligation covers the whole horizon
Partition:             same horizon; exactly the stored obligations' relations
Inventory digest:      correctly recomputed from those stored rows
Records/windows:       empty
```

The stated checks produce:

| Check | Result |
|---|---|
| Partition/inventory pairing | Pass |
| `registry_unaccounted_path` | Pass: P5a is pinned |
| `inventory_digest_mismatch` | Pass: hashing an incomplete set still yields a valid hash |
| `obligation_uncovered` | Pass: every **stored** obligation is covered |
| `missing_inputs_present` | Pass |
| `partition_overclaims` | Pass |

With no degrading exclusion, `A:603–614` permits **“searched, none admitted”**, although an included required path was never searched.

The applied guards provide no backstop. `1156:509–518` enumerates existing records/windows; an absent path contributes no consumer. `1153:939–954` checks that consumer drift and existing memberships, not an expected search inventory.

The conservative interval formula itself is sound **conditional on a complete declared inventory**. The defect is the unproved declaration boundary and the stronger SQL claim at `A:620`.

Required closure:

- Every included pin must have a finalized obligation-set commitment, or an explicit, validated `computed_empty` disposition.
- Publication must verify that the stored obligations equal that commitment.
- The writer’s qualified inventory derivation and O-RP-9 should establish semantic correctness; the publication contract must specify when that validation is mandatory.
- Test separately: absent pin; present pin with absent obligations; present obligations with absent intervals; genuinely empty qualified target set.

Naming a future oracle does not make the stated seal predicate detect the missing rows.

**2. P1 within AM-5 — search-input binding regressed.**

V0.3 explicitly carried:

```text
input_identity = {convention_id, declaration refs, operand fact_ids}
```

V0.4 removes that field. Its replacement inventory digest includes pins, obligation bytes, horizon and sky convention (`A:521–535`); its ledger digest includes only `ob_id|lower|upper|state` (`A:575–585`).

Neither declared preimage binds the L1 build/facts, AV declaration or interval-specific period-lord resolution used by the search. Changing one of those inputs while preserving the selected targets, path versions and sky convention can leave both digests unchanged. Therefore `A:599–601`’s assertion that a changed-input retry changes `inventory_digest` is false in that case.

It also leaves no specified detector preventing intervals evaluated under different input snapshots from accumulating into apparently complete coverage in one candidate generation.

Restore an immutable input-snapshot identity, bind every search interval to it, and include that binding in the inventory/manifest contract. An existing manifest `input_generation_vector` can provide part of this identity, provided the contract explicitly freezes and checks the connection before search and publication. This is completeness provenance, distinct from deferred typed-operand storage.

**3. Worked-example replay and SQL-citation audit**

| Example or citation | Independent result |
|---|---|
| AM-1 convention vector | Reproduces `sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3`. |
| AM-2 target grammar | The three quoted regexes match `1153:633–635`. `span:1–12` pass; `sign:1–12` fail. `span:13` and `span:07` require the stated builder rejection because SQL accepts them. |
| AM-2 existing five UUID vectors and masked-bit pair | All reproduce exactly. |
| **Example A: enrichment** | **Fails as written for the allowed initial `t_out=NULL` case.** The update sets `truncated=false` but omits `t_out`, violating `kgc_t_out_unless_truncated_ck` (`1153:1089–1090`). |
| Example A, repaired | With unchanged `t_in=2025-03-09T00:00:00Z` and a supplied `t_out=2025-03-11T00:00:00Z`, the printed centre and precision update satisfy the relevant predicates and retain the UUID. |
| Example A’s negative CHECK attribution | Changing `t_in` is rejected by the UPDATE guard. Retaining `clipped_truncated` while clearing truncation violates `kgc_truncated_method_ck`. Neither requires failure of `kgc_t_exact_iff_truncated_ck`, contrary to `A:243–245`. |
| **Example B: correction** | Same-ID UPDATE is refused at `1153:1149`; conflicting cross-generation `t_exact` is refused at `1168`. The new `c1` tuple produces **`eec1d008-2a69-8857-9164-786f5c8e96e8`**, as stated. Same-body/relation and single-successor checks agree with `839–869`. Corrected-target supersession is a valid alternative using an unsuperseded predecessor. |
| **W1: partial versus complete** | Correct interval arithmetic. H1 leaves A uncovered in February and B uncovered in January; H2 covers both throughout. The two obligation UUIDs reproduce. |
| W1 ledger hashes | The stated prefixes reproduce using sorted newline-joined rows with UUID, full UTC endpoints and `searched_complete`. |
| **W1 inventory hash** | `b4e36531d8b1d400` reproduces from the two sorted obligation strings alone. It omits pins, horizon and convention required by `A:524`; it is not a complete inventory-digest vector. |
| **W2: missing path** | Incorrect refusal claim, as demonstrated above. It works only if P5a obligations already exist and their intervals are missing. |
| **W3: receipt-only transaction** | Lock and publication-call ordering agree with `1153:430–502,969–992` and `1154:479–492`. Acceptance remains conditional on repairing the completeness checks. |

The quoted enrichment, immutability, supersession and coverage-guard locations are substantively grounded in the inspected SQL. The comment block at `A:174–201` is a paraphrase, despite “adopts verbatim”: the sky-event flip predicate is at `1153:761–766`, and the physical-object natural UNIQUE is at `636–637`. N6 compares the listed solved fields across generations; it does not compare `t_in`/`t_out` there.

UUIDv8-from-SHA-256 is sound for this contract when canonical-tuple equality and divergence checks precede deduplication. Masking leaves 122 digest bits; approximately \(2^{61}\) is the birthday-collision scale, not guaranteed uniqueness. Lowercase O-RX-1a correctly supersedes the frozen oracle’s uppercase serialization without editing that oracle. [RFC 9562 §5.8](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.8)

**4. New P2 — the proposed seal trigger can break existing seal replay.**

`ka_gochara_seal_generation()` uses `INSERT … ON CONFLICT DO NOTHING` (`1153:990–992`). A BEFORE INSERT trigger runs before conflict handling. [PostgreSQL INSERT documentation](https://www.postgresql.org/docs/17/sql-insert.html)

Under `A:552–564`:

1. Generation G seals with all then-existing registry versions pinned.
2. A new registry version is sealed later.
3. Repeating `ka_gochara_seal_generation(G)` invokes the new trigger.
4. `registry_unaccounted_path` rejects the already sealed generation before its conflict becomes a no-op.

The new trigger needs a deliberate already-sealed replay branch that validates the existing immutable seal/manifest binding without requiring historical inventories to adopt later registry versions. First publication should retain the current completeness checks.

**5. Compatibility and remaining A5.3 needs**

The new storage is compatible in principle with 1155/1156:

- Preserve the exact `event_class` partition key, current `coverage_facts`, bridged convention, relation coverage, contact `t_in` containment and support/window containment.
- Preserve the separate `moon_on_demand` guard for transiting-Moon contacts.
- Treat partitions as summaries and use the obligation ledger for serving completeness.
- Take chart EXCLUSIVE then global SHARED even when no record/window is emitted.

These guards validate existing consumers; they cannot independently prove search completeness. The new SQL must add that proof.

F-3 through F-7 remain the agreed nonblocking follow-ups:

| Follow-up | Required gate completion |
|---|---|
| **F-3** | Exact protected schema-capability and migration-runner wiring for the inventory migration. The draft now correctly acknowledges the capability requirement. |
| **F-4** | Full-precision formatter; remaining identity byte contracts; qualified geometry planning and O-RW-1 invalidation evidence. Withdrawing six-decimal quantization is an improvement. |
| **F-5** | Typed operand storage, declaration-key/applicability binding, factor-row `null_state`, edition/translator identification. |
| **F-6** | Actual evaluator P5 fixtures, numeric mismatch and independent missingness cases, declaration-mediated citations, oracle-map/sentinel corrections. |
| **F-7** | Concrete Moon receipt storage/key, canonical answer rendering and generation-5 manifest implementation, including inventory digests and on-demand exclusion; P6 context/containment remains held. |

AM-9 remains correctly scoped. The inspected L0 seed omits favourable node house 10 and retains favourable Ketu-12. `CORPUS_READS_v1_0.md:132–137` supports the placement finding; XXVI.2 does not independently source the stored vedha pairs or detailed phala. Keep those provenance questions separate.

**Ranked amendments**

| Rank | Severity | Required amendment and acceptance evidence | Blocking scope |
|---:|---|---|---|
| **1** | **P1** | Finalize and validate each included path’s obligation set; distinguish absent obligations from a proven empty set. Replay W2 exactly as written and require refusal. | AM-5/spec batch |
| **2** | **P1, same completeness closure** | Restore immutable search-input binding. Demonstrate that changing L1/declaration inputs cannot preserve a misleading completion identity or combine partial searches from different snapshots. | AM-5/spec batch |
| **3** | **P2, new** | Preserve seal-function replay after later registry versions appear. Test initial seal, identical replay, registry advancement and replay again. | Inventory migration acceptance |
| **4** | **P2, new example repair** | Supply example A’s required `t_out` and correct the negative CHECK attribution. | AM-2 acceptance example |
| **5** | **P2, new example repair** | Publish W1’s complete inventory preimage and matching digest; label the existing two-string hash accurately if retained. | AM-5 digest-vector acceptance |

The existing five P2s have not been promoted into round-4 blockers.

**What I could not verify**

I did not connect to production, inspect live migration-ledger hashes, confirm deployment quiescence, verify the cited L1 node fact or attest installed Swiss/runtime versions. Production application of 1153–1157 remains the supplied premise.

I did not run PostgreSQL, Vitest or pytest. The inspected DB suite requires a supplied disposable database and creates temporary files. The packet’s database/test results remain author-reported. My independent replay used the inspected SQL predicates and in-memory calculations, not database execution.

Classical conclusions rely on the repository transcriptions; I did not inspect the scanned editions. The inventory migration and generation-5 digest implementation do not yet exist in the reviewed exhibit, so their future enforcement cannot be credited as implemented.

No file was created, edited, moved or deleted; no git write command was run. The reviewed checkout remained clean.

