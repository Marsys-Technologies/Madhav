---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.2"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: REJECT
reviewed_commit: "c6367051e (campaign/pravaha) + f8b1c8b63 (PR #2817)"
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT as submitted. Migration 1204 independently receives ACCEPT.**

The bootstrap correction closes the previous lock-category defect. The convention digest, UUID vectors, collision example, and repaired old-role detector check out.

Two P1 issues remain: **AM-2 now prescribes identity/correction behavior incompatible with migration 1153**, and **AM-5 still cannot establish the completeness its publication and serving rules claim**. These exceed P2 specification detail.

**Evidence notation:** `A` = [amendments v0.3](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55c/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md); `S` = [frozen specs v1.4](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55c/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md); `O` = [frozen oracles v1.4](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55c/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_TEST_ORACLES_v1_4.json). Numbered SQL references identify files under `platform/migrations/`. Applied migrations were inspected at local `origin/main`, **`ee12eab8c74329c70db7aab430ad9d31487abc4d`**; PR source at **`f8b1c8b63d5cfab74789a7c856b8fc479d9640fe`**.

**Per-amendment verdicts**

| Amendment | Verdict | Assessment |
|---|---|---|
| **AM-1 — convention** | **ACCEPT** | The complete vector and expected digest agree. Runtime labels, L1-based node selection, domain versus searched horizon, and immutable bridge evolution are now explicit (`A:46–108`). The proposed `13d20m` correction correctly changes convention identity. Actual runtime/L1 attestations remain unverified here. |
| **AM-2 — identities** | **REJECT** | Lowercase successor-oracle policy and UUID construction are sound. However, `sign:1–12` is not an accepted stored target, and changing an existing non-NULL `t_exact` cannot be same-ID enrichment (`A:143–168`; `1153:632–635,1147–1156`). Six-decimal rendering also introduces an unresolved precision change. |
| **AM-3 — substeps/bootstrap** | **ACCEPT** | Two-phase grain and the registry/chart transaction split are consistent with the applied protocol. Chart-lock-before-legacy-coverage is correctly explicit (`A:225–282`). Receipt-specific global-SHARED and sealing requirements remain an AM-5 gap. |
| **AM-4 — Moon/day** | **ACCEPT_WITH_AMENDMENTS** | Ephemeral results, durable Moon coverage, manifest exclusion and separate answer receipts are coherent (`A:297–327`). Concrete log storage, query identity, canonical result bytes and digest implementation remain gate follow-ups. P6 context deferral is appropriately bounded. |
| **AM-5 — completeness receipts** | **REJECT** | Fixes cross-path interval conflation, but retains flattening within each path: target counts are not a target inventory, and relations are not bound to targets/intervals. Publication integration, the frozen applicability inventory, and receipt protection are incomplete (`A:370–429`). |
| **AM-6 — ṣaḍbala** | **ACCEPT_WITH_AMENDMENTS** | Option C and admission/score separation are correct (`A:442–481`). Correct the SQL location of `null_state`, identify the edition/translator, and specify where typed operand evidence is retained. |
| **AM-7 — P5/1204** | **ACCEPT_WITH_AMENDMENTS** | The two vocabulary widenings are correct and minimal. Auditable residence-qualification records are appropriate. P5 form separation and declaration semantics improve substantially, but exact storage/key and complete semantic acceptance remain open (`A:502–552`). |
| **AM-8 — P6/1205** | **ACCEPT — withdrawal only** | No 1205 migration/preflight or `inherited` validator arm ships. The five-kind correction is accurate. Future P6 acceptance remains separate (`A:559–596`). |
| **AM-9 — L0 finding** | **ACCEPT** | Correctly separates favourable placement from vedha and detailed phala, leaves Ketu-12 for sourcing/reclassification, and authorizes neither L0 repair nor nodal dṛṣṭi (`A:607–616`). |

**Disposition of all seven v1.1 ranked items**

| Prior rank | Status | Evidence and remaining boundary |
|---:|---|---|
| **1 — completeness representation** | **PARTLY** | Explicit per-path intervals and completion states replace the invalid path-in-relation-set proposal. The P1-January/P5-February example is resolved. Target/relation completeness within a path and enforceable publication remain unresolved; see findings below. |
| **2 — bootstrap categories** | **CLOSED** | `A:247–279` separates global-EXCLUSIVE registry work from chart-context conventions/substrate and takes the chart lock before legacy coverage writes. Matches `1153:430–502,560–578,604–607` and `1154:407–410`. |
| **3 — convention/identity bytes** | **PARTLY** | Convention digest, all five UUID vectors and the masked-bit example independently match. Lowercase O-RX-1a resolves the former casing contradiction. Stored sign encoding and correction semantics now contradict 1153; precision and other identity serialization remain incomplete. |
| **4 — old-role detector/residence fixture** | **CLOSED for migration compatibility** | Every old role now receives a committed acceptance probe with seeded coverage. The static detector isolates the executable CHECK list; removing `lord` makes it fail in my in-memory reproduction. Residence kind/frame/grain and declaration read-back are repaired. This does not establish full P5 evaluation acceptance. |
| **5 — P5 identity/applicability/lineage** | **PARTLY** | Separate path/version identities, L1 AV-convention meaning and rejection conditions are stated (`A:510–539`). Exact declaration-key construction, applicability storage and typed evidence storage are still unspecified. The fixture does not test numeric operand disagreement. |
| **6 — soft-factor null/admission boundary** | **CLOSED semantically** | `A:456–478` now explicitly preserves hard-predicate admission when the soft factor is missing or zero, matching `1155:822–832`. The remaining SQL-placement and evidence-storage details are P2 follow-ups. |
| **7 — post-seal receipts/P6 context** | **PARTLY** | Coverage identity, digest exclusion and receipt contents are substantially improved. “Ordinary application answer log” is not yet a concrete replay/storage contract. P6 parent-context and containment are expressly deferred; that deferral is acceptable for the withdrawn migration, not behavioral closure. |

**AM-6 pick: Option C**

Adopt **`sad_bala_sufficient` v1.0**, `units='unitless'`, output range `[0,1]`:

| Graha | Sufficiency threshold, rūpas |
|---|---:|
| Sun | 6.5 |
| Moon | 6 |
| Mars | 5 |
| Mercury | 7 |
| Jupiter | 6.5 |
| Venus | 5.5 |
| Saturn | 5 |

For a supported operand, output `1` at or above the threshold and `0` below it. Missing, incompatible or unsupported evidence produces an **unqualified score contribution**. It does not alter admission established by necessary predicates.

The repository transcription at `PROMISE_NATURE_YOGA_MAP_v1_1.md:244–254` supports a sufficiency classification. It does not supply a continuous event-strength mapping. Engineering-wise, the binary output satisfies unchanged `kgf_units_ck` and `[0,1]` constraints; adding `rupas` alone would still leave raw measurements outside that codomain.

The authored factor must cite:

1. **Phaladīpikā IV.22–23, `phaladeepika:PG79:C1`**, with the actual edition/translator and corpus document identity. The draft still does not name that edition/translator.
2. **IV.24, `PG80:C1`**, only for the separate bhāvabala composition statement.
3. The consumed L1 fact’s ID, category, subject, build, ayanāṃśa, raw value, unit and verification tier; any conversion must be explicit.
4. The versioned factor/path membership and adopted ranking policy, retaining its uncalibrated status where appropriate.

No threshold is established for Rāhu or Ketu.

One SQL correction is necessary: **`null_state` belongs to `ka_gochara_factor`** (`1154:310–334`). The soft-factor membership table contains only the path/factor version references (`1154:435–445`). State that membership binds a factor version whose `null_state='unqualified'`.

**Migrations and P5 modelling**

**1204: ACCEPT as a vocabulary-only migration.**

Independent source comparison establishes:

- `kgrr_object_role_ck` retains all nine old roles and adds exactly `av_qualifier` (`1204:117–122`).
- After removing that added value and normalizing whitespace/comments, the replacement selector’s executable token sequence equals the 1154 function (`1204:130–149`; `1154:243–261`).
- Embedded and standalone preflight DO blocks are byte-identical.
- Migrations 1153–1157 are byte-identical between inspected `origin/main` and the PR commit.

Widening both locations is necessary: otherwise the registry cannot select a role that relationship records may store. The change removes no contact FK, coverage guard, relative-frame restriction, prerequisite finalizer, rule seal or generation seal.

It deliberately does **not** enforce P5-only use, residence-only use, applicability or declaration consumption. Those remain writer/evaluator obligations, correctly acknowledged at `A:540–546`.

**Replay and protected-window wiring are correct by source inspection.**

`migrate.ts:138–158` protects 1204; `796–801` verifies an applied file’s hash and skips it; `829–839` atomically applies each migration with its ledger record. Thus runner replay is safe, while a direct repeat of already-recorded 1204 is intentionally refused by its preflight. It is not freely repeatable standalone SQL.

`deploy.yml:963–999,1043–1101` retains manual dispatch, the protected environment, pinned deployment SHA, exact migration selection, and capability grant/revoke. Atomicity is **per migration**, not across the entire selected family.

The CHECK swap has no committed unconstrained interval. Its locking can still block writers or time out; workflow concurrency does not itself prove writer quiescence. [PostgreSQL locking documentation](https://www.postgresql.org/docs/17/explicit-locking.html)

Replacing the selector helper does not automatically revalidate existing CHECK consumers. Here, strict widening preserves previously valid selectors. A future tightening or rollback must examine and revalidate affected selectors as well as relationship rows. [PostgreSQL CHECK documentation](https://www.postgresql.org/docs/17/ddl-constraints.html)

**The revised detector is credible; the P5 fixture remains narrower than its prose.**

In `gochara_b6_v15_migrations.db.test.ts`, coverage is now seeded for every probed role (`325–328`), old-role inserts must commit and read back (`392–414`), and the residence fixture uses `house_span`, lagna and `transit_residence` (`349–377`).

However:

- `consumeDeclaration` is a **test-local helper**, checking existence/category only (`250–259`).
- The negative arms call that helper, without exercising an actual evaluator insertion/citation path (`380–384`).
- The positive fixture stores identifier strings, not typed bindu measurements (`361–362`).
- Synthetic operands still use `fixture=false` through `insertRecord` (`287–293`).
- No arm checks mismatched numeric bindus, competing BAV/SAV selection, or independent P5a/P5b missingness.

These are A5.5/P5 acceptance follow-ups. They do not invalidate the narrow SQL widening.

**P5 should remain a qualifier represented by an auditable relationship record.** A record can attach AV interpretation and lineage to an existing residence contact while preserving the shared physical root. Static AV measurements remain operands. Separate P5a/P5b paths preserve distinct outcomes under within-path reduction; mere record existence must never establish event admission.

**1205: absent.** Its withdrawal remains correct. No replacement migration or implemented P6 testimony mechanism is approved by this review.

**Gaps and contradictions**

**1. P1 — AM-2 violates the applied identity contract.**

Two direct incompatibilities must be corrected before the batch is accepted.

- **Stored sign targets:** `A:150–151` prescribes `sign:1` through `sign:12`. Migration `1153:632–635` accepts only `point:…`, `span:…` and `star:…`. Both proposed sign endpoints fail that exact grammar. Use **`span:1` through `span:12`**, explicitly defined as absolute signs, consistent with frozen `S:648–649` and the PR’s `span:7` fixture. No CHECK widening is needed.
- **Non-NULL time correction:** `A:159–168` says a refined `t_exact` keeps its UUID and amends mutable enrichment with supersedes linkage. Frozen `S:641–646` expressly forbids changing a published non-NULL time in place. Migration `1153:1147–1156` rejects it; `1163–1175` also rejects conflicting solved readings under the same contact identity across generations. Sky-event enforcement is analogous at `1153:775–788`.

The contract must distinguish:

1. **NULL/truncated → solved:** same identity, permitted enrichment, no new supersedes edge.
2. **Existing non-NULL reading → corrected reading:** new deterministic identity under an appropriately revised convention or corrected physical target, with supersedes linkage.

The current contact-identity row is insert-only and rejects self-supersession (`1153:813–884`). A same-ID correction cannot acquire the proposed supersedes history. Also retract the blanket prohibition on corrected-target supersession: frozen §6.1 and 1153 explicitly support it.

**UUIDv8 itself is sound.** Taking SHA-256’s first 16 bytes and setting version 8/variant `10` leaves 122 digest bits; uniqueness remains implementation-specific. The birthday collision scale is approximately \(2^{61}\), not a uniqueness guarantee. [RFC 9562 §5.8](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.8)

All five supplied UUID vectors and the fabricated masked-bit collision pair recompute correctly. Retain the three-way collision checks before deduplication, and require equality of immutable payloads before treating same-tuple/same-ID as replay.

The six-decimal rule is a separate P2 issue: it quantizes full-precision physical targets. For example, `198.5200001` and `198.5200004` collapse under ordinary six-decimal rendering. That loss occurs **before hashing**, so UUID collision detection cannot recover it. Preserve full solved precision, or explicitly govern the quantization, rounding mode, seam behavior and method-version consequence.

**2. P1 — AM-5’s receipt still does not represent complete search coverage.**

The new table resolves **different paths over different intervals**. It does not resolve **different relations/targets over different intervals within one path**.

`A:373–378` stores:

- one interval multirange;
- one flat relation list;
- three target counts;
- an input-identity object.

There are no target identities or associations between target, relation, interval and completion state.

For example, within one path, searching target A in January and target B in February can produce the same summary counts, relation list and interval union as searching both targets throughout January–February. The publication predicate at `A:398–403` checks receipt presence, state and horizon coverage; it cannot distinguish those histories.

Choose an explicit representation:

- interval/state entries keyed by the required **agent–relation–target–frame/person** obligations; or
- an immutable, identifiable search inventory, with a precisely defined universal-completion rule and separate partial-search details.

Counts may summarize that inventory; they cannot replace it. This does not require enumerating an unrestricted Cartesian product: the inventory must contain exactly the qualified obligations required by `S:215–231` and O-RP-8.

The same contract must also settle:

- **Inventory identity:** pin the applicable paths and versions to the generation/manifest. “Applicable sealed versions” cannot mean whatever registry rows happen to exist at serving time. The registry itself has no event-class/person columns (`1154:369–381`).
- **Seal integration:** the applied generation seal checks consumer drift and membership, not receipts (`1153:918–955`). The drift function enumerates only records/windows (`1156:509–518`); a wholly missing path produces no consumer violation. A new table with only chart-context and insert-only triggers does not enforce the proposed publication rule. Name the new seal/publication check explicitly.
- **Lock order:** receipt-only complete-empty or missing-input transactions must take **chart EXCLUSIVE → global SHARED** before consulting rule seals/inventory. They cannot rely on record/window triggers when no such rows are emitted. Reuse the rule-seal discipline of `1154:479–490`.
- **Immutability:** reject receipt insertion into sealed generations, preserve the receipt inventory in the manifest’s content contract, and define identical replay versus changed-input retry.
- **Serving states:** `completed_unqualified` is allowed to seal, but the serving algorithm only explicitly handles `completed` and missing coverage. Define all states, including all-paths-unsearched, without reporting unknown as rejection.
- **Applicability boundaries:** explain how disabled P5 forms, unavailable operands and on-demand P6 affect the build inventory. Missing inputs cannot silently remove required paths; P6 must not make a build depend on every future day query.

These are core completeness requirements, not merely missing SQL syntax.

**3. P2 — the additive receipt migration still needs a protected schema capability.**

`A:425–427` concludes “no live CHECK touched — no protected window.” That does not follow from the deployed permission model.

`deploy.yml:953–962` explicitly says the ordinary role lacks `CREATE` on `public`; `jataka-schema-capability.ts:54–67` grants and revokes that capability for the protected window. Creating the proposed table/functions requires an authorized schema-capability route even without altering an existing CHECK. Correct the packet’s deployment claim and wire the eventual migration accordingly.

**4. Remaining A5.3/A5.5 specification follow-ups**

| Gap | Required completion |
|---|---|
| **Typed operand storage** | Name the persistent representation for AM-6 raw rūpas and AM-7 bindus/declaration binding. The 1155 record has no general operand-evidence field; `source_fact_ids` admits strings, and `precision` has a closed shape (`1155:317–332,465–508,583–585`). Specify a durable evidence reference or new storage rather than implying these fields already exist. |
| **P5 keys/applicability** | Pin declaration-key construction and its L1 build/convention identity, exact P5a/P5b path IDs, and where class/person applicability is stored and validated. Naming “L1 AV-build convention” resolves meaning, but not serialization or storage. |
| **Relationship/window identity** | Complete canonical bytes for record/window IDs: frame arguments, nulls, ordered versioned prerequisites, source/citation serialization, intervals and generation/input binding. AM-2 currently addresses physical/contact identity. |
| **Geometry planning/invalidation** | Declare qualified geometry before phase-one solving and retain the reason for re-solving versus re-scoring. Adding a previously unsearched target/relation must trigger the required solver work; retain O-RW-1’s invocation assertions. |
| **Moon receipt implementation** | Name the answer-log table/API and receipt key; pin query context, evaluator versions and canonical result rendering, excluding self-referential digest/audit fields. The existing legacy digest helper includes **all** coverage rows (`gochara_kernel/ledger.py:503–518`); AM-4’s exclusion requires an explicit generation-5 implementation and before/after-seal proof. |
| **Behavioral oracle closure** | Replace B6-F16/F17 sentinels with actual union/channel/unknown-state and P6 tārā/parent/containment/zero-score assertions. The map’s stale 1205 reference remains present at line 133; the draft acknowledges its future correction but has not corrected that artifact. |

AM-9 needs no expansion. The inspected L0 seed omits node house 10 and includes favourable Ketu-12; `CORPUS_READS_v1_0.md:132–137` supports the placement finding. XXVI.2 does not independently source node vedha pairs or the seed’s detailed phala. Preserve that distinction.

**Ranked amendments required**

| Rank | Severity | Required amendment and acceptance evidence | Blocking scope |
|---:|---|---|---|
| **1** | **P1** | Correct AM-2 to SQL-valid `span:` bytes and restore enrichment versus correction immutability. Prove truncated enrichment retains ID, while changed non-NULL readings require valid new identity/supersession. | Spec batch and identity implementation |
| **2** | **P1** | Complete AM-5’s obligation inventory/interval representation, manifest binding, seal integration and chart→global-SHARED protocol. Demonstrate same-path partial searches cannot become complete-empty. | Spec batch, receipt migration and coverage acceptance |
| **3** | **P2** | Correct the receipt migration’s protected-window claim and specify its exact capability/runner route. | Receipt migration acceptance |
| **4** | **P2** | Resolve six-decimal quantization and finish physical-object, relationship-record and window byte contracts; retain O-RX-1a and invalidation tests. | A5.5 identity gate |
| **5** | **P2** | Specify typed operand storage, declaration-key bytes and applicability binding; place `null_state` on the versioned factor row. | AM-6/AM-7 writer acceptance |
| **6** | **P2** | Complete synthetic P5 semantic fixtures, numeric mismatch and citation-through-declaration tests; correct oracle-map status claims. | P5/A5.5 acceptance, not vocabulary-only 1204 |
| **7** | **P2** | Complete Moon query-log/key/canonical digest and publication-exclusion proof. Retain the explicit hold on P6 parent-context and containment until its separate design lands. | Moon/day implementation acceptance |

**What I could not verify**

I did not connect to production, inspect live migration-ledger hashes, verify the cited L1 node fact, confirm installed Swiss/runtime versions, or verify deployment quiescence. Production application of 1153–1157 remains the supplied premise.

I did not run PostgreSQL, Vitest or pytest. The inspected DB suite requires a supplied disposable database and creates temporary files; I did not invoke it under the no-file-write instruction. The packet’s PG 17.10, 8/8 DB and 873-test results remain author-reported.

Independent verification here comprised source/byte comparisons, SHA-256 and UUID calculations, target-grammar checks, and in-memory mutation of the repaired static detector. Frozen v1.4 specs/oracles remain unchanged from the preceding reviewed commit, and the oracle inventory contains 57 entries.

Classical conclusions use the repository’s cited transcriptions; I did not independently inspect the scanned editions. No file was created, edited, moved or deleted, and no git write command or production database operation was performed.