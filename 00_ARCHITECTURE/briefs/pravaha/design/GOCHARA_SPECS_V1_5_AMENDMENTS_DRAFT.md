---
artifact: GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT
version: 0.3
status: DRAFT — revised per ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_1 (REJECT, narrowed, 2026-10-01); collects the A5.5-gate fold-in list; not a spec version
date: 2026-10-01
author: stream-B (spec lane; docs only — no code, no migration file)
supersedes: v0.2 (55a6ea8a2) — AM-5 completeness rewritten as an explicit receipt representation; AM-1/AM-3 bootstrap transactions re-categorised; identity bytes pinned (successor oracle, digest, normalisation, UUID vectors); AM-4 receipt storage; AM-6 null policy; AM-7 P5 contract completed; stale statements corrected
sources: >
  ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_1 (Codex gpt-6-astra, verdict REJECT with
  seven ranked required amendments; CLOSED: AM-8/1205 withdrawal, AM-9, AM-6's five
  qualifications; 1204 judged consistent and minimal); steward revision order
  M20261001T174917-3007. v0.2 sources retained: ASTRA_REVIEW v1_0; steward
  M20261001T171150-5c70, M20261001T015412-6df0, M20261001T121504-90d5; stream-B
  cited lookup M20261001T015350-644c; stream-A reports M20261001T080615-a232,
  M20261001T113409-04cd; steward acceptance M20261001T121451-1a8d; stream-B
  reports M20261001T084457-5ceb, M20261001T172813-94e5.
---

# GOCHARA_DESIGN_SPECS v1.5 — AMENDMENT LIST (draft v0.3)

Revision disposition against ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_1, rank by
rank. **Accepted findings are folded into the proposed spec text below; where
this draft disagrees with the reviewer it says so with evidence.** Migration
discipline unchanged: migrations 1153/1154/1155/1156/1157 are applied and
**never edited**; every schema-side change is a NEW migration, and each one
touching a live CHECK constraint needs a protected window.

v1.1 ranked crosswalk: rank 1 (P1) → §AM-5 (completeness representation) ·
rank 2 (P1) → §AM-1/§AM-3 (bootstrap transaction categories) · rank 3 (P2) →
§AM-1/§AM-2 (convention vector + identity bytes) · rank 4 (P2) → PR #2817
detector + fixture (code, separate commit) · rank 5 (P2) → §AM-7 ·
rank 6 (P2) → §AM-6 · rank 7 (P2) → §AM-4 (+ deferral note for P6).

---

## AM-1 — Convention row for generation `'5.0'` (pin 3) — REWORKED per v1.1 rank 2/3

Codex v1.1: the convention vector is still not byte-pinned (v0.2 gave
components without one complete serialized string, delegated the domain to an
unnamed ruling, and differed from the A5.3 implementation's compound ephemeris
label and `nakshatra:13.20`); convention bootstrap was assigned to the wrong
transaction category (see AM-3). All folded.

**Proposed spec text (new §6.0):**

> **The pinned convention vector.** Exactly one convention row serves the
> `'5.0'` family. Its canonical serialization is the sorted-key `key=value`
> list joined by single `|`, UTF-8, no trailing whitespace, and its
> `convention_id` is `sha256:<hex>` over those exact bytes:
>
> ```
> ayanamsha=lahiri_chitrapaksha|domain_end=2085-01-01T00:00:00Z|domain_start=1998-01-01T00:00:00Z|ephemeris_generation=pyswisseph:20230604/swisseph:2.10.03|grid=sign:30/nakshatra:13d20m/kakshya:3.75/seam:0|method_version=1.0.0|node_convention=mean
> ```
>
> **Expected digest (independently computed, sha256 over the string above):**
> `sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3`.
>
> Field authority, field by field:
>
> - `ephemeris_generation` — the **compound label** of the governed runtime:
>   pyswisseph build `20230604` (`swe.__version__`,
>   `gochara_kernel/knots.py:169`) and Swiss Ephemeris `2.10.03`
>   (`swe.version`). This adopts the A5.3 implementation's label
>   (`substrate.py:153–171` at 694d16e9c) verbatim; v0.2's bare-build label is
>   withdrawn. A runtime reporting any other pair = build failure before any
>   write.
> - `ayanamsha = 'lahiri_chitrapaksha'` (`step06_candidate_build.py:73`).
> - `node_convention = 'mean'` — **deterministically** selected: the L1 node
>   convention for chart 482012f1 as recorded in `chart_facts`, cited by
>   fact_id (subjects `RAH_MEAN`/`KET_MEAN`, fact_id `c520713087b97470`),
>   never "the latest fact" and never picked (`step06_candidate_build.py:77`
>   `node_model: "mean"` agrees). If the chart's L1 facts ever carry both node
>   conventions the selection rule is: the convention the L1 build itself
>   consumed, by its own attestation — absence of that attestation is a stop,
>   not a default.
> - `grid` — `sign:30/nakshatra:13d20m/kakshya:3.75/seam:0`. The nakṣatra span
>   is 13°20′ = 13⅓°, rendered `13d20m` — **never** the decimal `13.20`
>   (13.20° ≠ 13°20′; v0.2 said this but left the implementation's `13.20`
>   unreconciled). **This is a deliberate correction of the A5.3 vector at
>   694d16e9c** (`grid: sign:30/nakshatra:13.20/…`): it changes the canonical
>   bytes, therefore the digest, therefore the convention_id — it is NOT
>   interchangeable with the old bytes and must land before any row is written
>   under the new id. (`gochara_kernel/contacts.py:13-15`,
>   `convention.py:78` agree on the 13°20′ span.)
> - `method_version = '1.0.0'` (`step06_candidate_build.py:84`).
> - `domain` — half-open UTC `[1998-01-01T00:00:00Z, 2085-01-01T00:00:00Z)`.
>   **Domain authority:** the full-domain ordinal boundaries are pinned *in
>   the convention identity itself* (O-RX-1's extension rule operates INSIDE
>   this fixed domain; changing the domain is a new convention, never an edit).
>   The *searched partition* within the domain is set per generation by the
>   campaign's scored-horizon ruling (the `'5.0'` build's governed horizon) and
>   is a coverage fact, never a convention fact. The 1153 self-test's
>   1998→2085 demonstrated this domain shape; the runtime domain is pinned
>   here, in the vector, and nowhere else.
>
> **Convention identity ≠ generation identity.** `convention_id` names the
> *method vector* above; `generation` (`'5.0'`) names a *run* under that
> convention. The literal `'5.0'` is a generation label, never a convention
> id. Once a convention id enters physical/contact identities it is immutable;
> a changed vector is a NEW id, never an edit.
>
> **Convention-bridge evolution (v1.1 additional gap, folded):**
> `ka_gochara_convention_bridge` (1153:1016–1034) gives each legacy
> `kala_gochara_convention` row exactly one immutable mapping and can never be
> repointed. A domain/method correction therefore mints a **new** sky
> convention id **and a new legacy convention row** bridged to it; the old
> pair stays, preserving the lineage of every coverage row that cites it.
> Existing mappings are never rewritten.

**Schema impact:** none — data under the existing tables (a correction that
arrives after rows exist adds rows; it edits none).

---

## AM-2 — §6.1 identity hash: sha256 → UUIDv8 (pin 4) — REWORKED per v1.1 rank 3

Codex v1.1: the UUIDv8-from-SHA-256 construction is sound (122 retained digest
bits, birthday bound ≈ 2⁶¹; RFC 9562 §5.8); the collision taxonomy is
approved; but lowercase canonicalisation contradicts O-RX-1's uppercase
canonical bytes, numeric/sign/star normalisation is unfinished, and expected
UUID literals were claimed but not pinned. All folded.

**Proposed spec text (amend §6.1):**

> The identity hash is **sha256 over the §6.1 canonical bytes, first 128 bits
> carried as a UUID with the version-8 and variant bits set** (RFC 9562 §5.8).
> After the 6 fixed bits, **122 digest bits remain**; collision resistance is
> the birthday bound ≈ 2^61 identities — ample for this dataset, and **not** a
> substitute for collision handling (below). No SHA-1, no UUIDv5.
>
> **Canonical bytes, pinned (this resolves the lowercase contradiction):**
> body/relation tokens are the **stored lowercase form** (1153 persists
> lowercase body tokens — the hash is over what is stored, never over caller
> casing, so one natural tuple has exactly one ID). Because the frozen
> O-RX-1's printed serialization begins with uppercase `Mars`, **O-RX-1's
> byte example is amended by a reviewed successor oracle O-RX-1a** whose
> canonical bytes are `mars|conjunction|point:198.52|c0|1`; the frozen v1.4
> oracle file is preserved untouched, and O-RX-1a is the only serialization
> authority for identity bytes. Remaining pins:
>
> - delimiters: single `|`; **no trailing whitespace or newline**; one flat
>   byte string (a nested `hash(hash(A),B)` construction is NOT used).
> - **numeric rendering:** decimal, no exponent form, produced at write time
>   by one pinned formatter: render with up to 6 fractional digits, **strip
>   trailing zeros and a trailing dot**, integers render with no dot. The
>   stored text IS the canonical text: `198.520` and `198.52` normalize to the
>   same stored rendering `point:198.52` before hashing, so the two inputs
>   cannot mint two IDs for one longitude (1153:632–635 accepts either
>   string; the formatter runs first).
> - **sign encoding:** absolute sign index `sign:1`–`sign:12` (1 = Meṣa),
>   the stored form.
> - **star encoding:** the **stored 1-based** index `star:1`–`star:27`
>   (SQL's accepted range); the tārā oracle's zero-based indices map as
>   `star_zero_based = star_stored − 1`. Zero-based values never appear in
>   canonical bytes.
> - identity tuple components, exhaustive and ordered:
>   `body | relation | target | convention_id | occurrence_ordinal`.
>
> **Correction identity — the component that changes is named:** the tuple
> above has no time component, so a **time-only correction** (a refined
> t_exact for the same crossing) never mints a new UUID: it amends the
> contact's mutable enrichment under the versioned correction rule (S:641–646)
> with its `supersedes` linkage, identity untouched. A **method/convention
> correction** changes the `convention_id` component — a coherent route that
> mints new identities under the new convention and retains the supersedes
> chain to the old. No other component may change on a correction; a change
> of body, relation, target or ordinal is a different physical claim, not a
> correction.
>
> **Collision taxonomy, all decided BEFORE any UUID-keyed deduplication**
> (`ON CONFLICT DO NOTHING` alone is insufficient and forbidden as the only
> check):
>
> 1. same canonical tuple, same ID — legitimate replay; skip.
> 2. different canonical tuple, same ID — loud build failure.
> 3. same canonical tuple, different ID — serialization/version divergence;
>    loud build failure.
>
> Comparison happens on the **canonical tuple**, never on the UUID alone:
> the UUID masks overwrite 6 digest bits, so two genuinely different digests
> can share one UUID (worked vector below).
>
> **Pinned UUIDv8 vectors (independently recomputed by stream-B, matching the
> reviewer's table):**
>
> | Canonical bytes | UUIDv8 |
> |---|---|
> | `mars\|conjunction\|point:198.52\|c0\|1` | `23276d7c-c127-8f4c-9ad5-6b7c8da8020f` |
> | `mars\|conjunction\|point:198.52\|c0\|2` | `b6cd1a15-4820-859f-b6e4-d7e144e59416` |
> | `mars\|conjunction\|point:198.52\|c0\|3` | `c523b443-fcc4-8665-8bfc-52b6e3e831d9` |
> | `mars\|conjunction\|point:198.52\|c0\|4` | `8e423fdf-6ab5-842a-ab1f-b31d4720d319` |
> | `Mars\|conjunction\|point:198.52\|c0\|1` (uppercase — MUST NOT occur under O-RX-1a) | `87b023cc-c9f3-8979-9b37-96701f285356` |
>
> **Post-mask collision control vector:** sha256 of tuple 1 begins
> `23276d7cc1279f4cdad56b7c8da8020f…`; the fabricated digest
> `23276d7cc1276f4c1ad56b7c8da8020f…` differs ONLY in the 6 bits the UUID
> masks overwrite, and both map to `23276d7c-c127-8f4c-9ad5-6b7c8da8020f`
> (verified). The forced-collision test suite must include this class —
> differences confined to masked bits — alongside different-tuple/same-UUID
> and same-tuple/different-UUID arms.
>
> **O-RX-1a acceptance:** one physical object, ordinals 1–3, truncated-centre
> enrichment without identity change, ordinal 4 appended on in-domain
> partition extension without renumbering; the uppercase variant rejected as
> non-canonical input.

**Schema impact:** none — PK columns are already plain UUIDs.

---

## AM-3 — Writer phase grain and **transaction categories** (REWORKED per v1.1 rank 2)

Codex v1.1: v0.2's per-table persistence rules stand (global insert-only,
sky-event enrichment/correction only, candidate replacement in dependency
order, sealed never reopened), but the combined "registry/convention
bootstrap" transaction is incompatible with the applied lock guards:
1153:560–578 makes substrate writes require chart context, 1153:604–607 makes
sky-convention inserts invoke that guard, 1153:450–469 forbids chart-family
and global-exclusive keys in one transaction, and 1154:407–410 routes
rule-path insertion through the global-exclusive guard. **Sky conventions are
not 1154 registry rows.** Folded.

**Proposed spec text (amend §10.1):**

> The writer runs in **two phases**. Phase 1: per-body boundary substrate +
> contacts. Phase 2: per `(event_class × path_id, rule_version)` evaluation
> emitting relationship records and windows. Persistence is **per table, by
> publication state** (unchanged from v0.2, restated for the gate):
>
> - **Global physical objects and contact identities** (chartless, shared
>   across charts and generations): **insert-if-absent with equality checks**
>   (AM-1/AM-2); never updated, never deleted by a build.
> - **Sky events:** only the **permitted enrichment/correction operations**;
>   deletion is refused by the substrate contract (1153:758–759, 813–887).
> - **Candidate (unpublished) chart × generation records and windows:**
>   replacement **in dependency order** at the owned grain
>   `(chart_id, generation, event_class, path_id, rule_version)` for Phase-2
>   output and `(chart_id, generation, body-scope)` for Phase-1 candidate
>   contacts; the delete set is computed from the grain and the FK closure,
>   and a conflict with a surviving relationship reference (1155:413–459) is
>   a loud failure, not a cascade. Candidate replay preserves this rule: it
>   never deletes a shared contact another path still references.
> - **Published / sealed data:** refusal and enrichment rules unchanged; a
>   re-run under an existing sealed generation is a refusal; new evaluation
>   runs under a new generation label.
>
> **Transaction categories (corrected):** exactly two, never mixed.
>
> 1. **Registry transaction** (orchestrator-owned; takes the
>    `gochara5:global` family key EXCLUSIVE via `ka_gochara_lock_global`,
>    1154:407–410 route): predicates, factors, rule paths, memberships, rule
>    seals. No chart-scoped row — including no sky convention — is written in
>    this transaction.
> 2. **Chart-serving transaction** (orchestrator-owned; takes the chart
>    family key via `ka_gochara_lock_chart` FIRST, before any write): sky
>    conventions (insert-if-absent with the AM-1 equality check), the
>    convention bridge, AV declarations where required, substrate/contacts,
>    candidate records/windows, receipts (AM-5), and **every legacy
>    `kala_gochara_coverage` mutation — the chart lock is acquired BEFORE the
>    first legacy coverage write**, not only before the record/window inserts
>    that FK it (the legacy table carries no Gochara-family trigger; the
>    ordering is the writer's obligation, stated here as contract).
>
> **Worked example (required bootstrap sequence for the `'5.0'` build):**
>
> ```
> txn R (registry):   SELECT ka_gochara_lock_global();
>                     insert predicates, factors, rule paths P1–P6, memberships; seal rule versions.
>                     -- any ka_gochara_sky_convention insert here FAILS (1153:604–607 chart guard)
> txn C (chart):      SELECT ka_gochara_lock_chart('482012f1-…');
>                     insert-if-absent ka_gochara_sky_convention (AM-1 vector, equality-checked);
>                     insert convention bridge (kala_convention_id → sky id);
>                     upsert legacy kala_gochara_coverage partitions (event_class keys);
>                     insert path-search receipts (AM-5), contacts, records, windows.
> ```
>
> Reversing the categories fails loudly in both directions: convention insert
> inside txn R trips the substrate chart guard (1153:560–578); a registry
> insert inside txn C trips the N13 lock-order refusal (1153:450–469). The
> PR's own fixture already separates the two correctly
> (`gochara_b6_v15_migrations.db.test.ts:292–305`: convention under
> `chartCtx`, rules in a separate global transaction).

**Schema impact:** none.

---

## AM-4 — Moon / day tier is EPHEMERAL (pin 6) — REWORKED per v1.1 rank 7

Codex v1.1: the transiting-Moon correction and ephemeral-response policy are
closed; what remains open is the persistent query-receipt contract — where
receipts live, their key, how query coverage stays distinct from sealed build
coverage, manifest-digest treatment, and replay. Folded.

**Proposed spec text (amend §6.2 / §10.1):**

> The Moon/day tier is **EPHEMERAL**: no materialised Moon rows in the global
> substrate (`kgse_body_domain_ck` excludes `'moon'`, 1153:684–685). The
> contact table's `kgc_body_domain_ck` *including* `'moon'` (1153:1072–1073)
> covers contacts where the **transiting body is the Moon** (a transit-Moon
> contact against a natal target) — it is not a natal-Moon-target licence.
>
> **Coverage identity:** a Moon/day query writes its own `moon_on_demand`
> coverage partition in `kala_gochara_coverage`, keyed
> `moon:interval:<start>/<end>` (1081's key shape; 1155:729–732 applies the
> same guard shape to the Moon agent). That row is the query's durable
> coverage identity — written under the chart lock like any coverage row
> (AM-3), and **distinct from build coverage by `partition_kind`**: the
> sealed generation's published manifest digest is computed over the build
> partitions (`event_class`, `body_target`) only; `moon_on_demand` rows are
> excluded from it, whether written before or after sealing, so a post-seal
> Moon query never changes the sealed manifest.
>
> **Query receipt (post-seal behaviour pinned):** the answer carries a
> receipt object binding five things: (1) the sealed generation's **manifest
> id and digest**; (2) the **coverage partition key and the `coverage_facts`
> snapshot** it answered under; (3) the **query interval**; (4) the **input
> identity** (sky convention id + the natal-target fact ids consumed); (5) a
> **result digest** (sha256 over the canonical answer rendering). The receipt
> is returned with the response and recorded in the ordinary application
> answer log; **no row is written to any ka_gochara family table for it, no
> membership row is written, and nothing in the sealed generation mutates.**
> Replay: re-issuing the same query interval against the same coverage facts
> re-derives the receipt; equality of the result digest is the replay check.
> A Moon query against a sealed generation is therefore fully served by: the
> moon_on_demand coverage row (durable), the ephemeral answer, and the
> logged receipt — never by reopening the generation.
>
> **Deferred (v1.1 rank 7, second half):** the P6 parent-context and
> temporal-containment rules (1156:247–265 carries no frame/person fields on
> the window; context must resolve from specified admitting objects/records
> with an unambiguous rule when members differ; annotation support restricted
> to the admitted parent interval) are **deferred to before any P6
> implementation lands** and are tracked with AM-8's future template
> migration. They are not part of this batch.

**Schema impact:** none.

---

## AM-5 — Coverage-partition ownership and **explicit completeness** (REWORKED per v1.1 rank 1)

Codex v1.1: `partition_key = event_class`, writer ownership and the
same-transaction bridge/snapshot binding are closed. What is rejected is the
completeness story: applied coverage treats "paths" and "relations" as
different concepts (1155:733 checks the contact's relation against
`relations_searched`; 1155:361–380 snapshots only convention, horizon and
relations; 1156:499–545 classifies extension by horizon + relation-set
containment), and "naming paths in the relation set" cannot represent *which
path version searched which relations/targets over which intervals*. A flat
path list plus a flat relation list plus one horizon falsely implies the
unperformed Cartesian product. Folded: the path-in-relation-set idea is
replaced by an explicit, versioned **path-search receipt** representation.

**Proposed spec text (amend §10.1):**

> The `ka_gochara_v5` writer owns the `'5.0'` coverage partitions in
> `kala_gochara_coverage`: it inserts/extends its own partitions with
> `partition_kind = 'event_class'` and **`partition_key = <event_class>`**
> (the only key both applied guards admit, 1155:706–709 / 1156:402–405),
> `completed_horizon` within the governed domain, `relations_searched` exact
> — **in the same chart-serving transaction, after the chart lock and before**
> the records/windows that FK them, with the convention bridge and the
> `coverage_facts` snapshot bound in that same transaction (AM-3).
>
> **Completeness representation — the path-search receipt.** Completeness is
> carried by an explicit per-path receipt, never inferred from the
> partition's flat fields. Receipt identity and content:
>
> ```
> ka_gochara_path_search_receipt
>   (chart_id, generation, event_class, path_id, rule_version)   -- PK
>   searched_intervals    tstzmultirange   -- the intervals ACTUALLY searched
>   relations_searched    text[]           -- this path's relation inventory
>   targets_required      int              -- the path's declared target inventory
>   targets_resolved      int
>   targets_unresolved    int
>   input_identity        jsonb            -- {convention_id, declaration refs, operand fact_ids}
>   completion_state      text             -- 'completed' | 'completed_unqualified' | 'missing_inputs'
>   completion_detail     jsonb            -- unavailable inputs / unqualified reason / NULL
>   coverage_partition    (partition_kind, partition_key)        -- the owning partition
>   computed_at           timestamptz
> ```
>
> Chart-scoped, insert-only, written under the chart lock in the same
> transaction as the partition it belongs to; one row per
> (class × path × rule version); a re-search under the same version amends
> nothing — it runs under a new rule_version or a new generation.
>
> **The three states are never collapsed.** For (class C, path P, interval I):
> a `completed` receipt covering I with an empty admitted set means
> **"searched, none admitted"**; `completed_unqualified` means evaluation ran
> but prerequisites stayed unknown (distinct from rejection); `missing_inputs`
> records exactly which inputs were unavailable; and **no receipt means "not
> searched"** — an unknown result is never equivalent to a qualified
> "none admitted".
>
> **Publication rule:** a generation's class C may seal only when the receipt
> set for C equals the applicable-path inventory of the sealed rule versions
> for C, every receipt is `completed` or `completed_unqualified`, and the
> union of `searched_intervals` per path covers that path's governed horizon.
> (The existing seal checks validate consumers and membership; the receipt
> inventory is what proves every required path was executed.)
>
> **Serving rule:** an answer for (class C, interval I) reads the receipts:
> every applicable path with a `completed` receipt whose
> `searched_intervals` contain I → "searched"; any applicable path missing a
> receipt, or whose intervals do not contain I → the answer is qualified
> **"partially searched: <paths/intervals missing>"**. A partial search can
> never read as complete-empty, and receipts can never imply unsearched
> (path × interval) combinations, because every claim is a stored row, not an
> inference from a shared horizon and a merged relation list.
>
> **Worked example (the reviewer's case):** class `marriage`; P1 searched
> January, P5 searched February. Receipts:
> `(P1, v1.0, searched=[01-01,02-01), completed)` and
> `(P5, v1.0, searched=[02-01,03-01), completed)`. A query for January–February
> answers: **"partially searched — P1 not searched February; P5 not searched
> January"**; a query for January alone answers "searched" for P1 and
> "not searched" for P5. Under v0.2's flat representation the partition would
> have carried paths {P1,P5}, one horizon Jan–Feb and merged relations —
> reading falsely as "P1 and P5 both searched Jan–Feb". Under the receipt
> representation that reading is unrepresentable.

**Schema impact:** ONE new additive migration (`ka_gochara_path_search_receipt`,
chart-context trigger + insert-only guard, no live CHECK touched — no
protected window). v0.2's "schema impact: none" is corrected: the guards
admit the partition shape, but the completeness representation is new
storage, and saying the partition "carries" it does not make it free.

---

## AM-6 — D2: `sad_bala_sufficient` v1.0 — **OPTION C (closed); null policy + admission boundary pinned per v1.1 rank 6**

Codex v1.1 CLOSED the five substantive qualifications (Option C, thresholds,
bhāvabala distinction, unsupported nodes, typed raw evidence, versioning,
zero-score/admission separation). One clarification remained and is folded:
missing soft-factor evidence must not corrupt SQL `admission_state`.

**Proposed spec text (factor catalogue entry, versioned):**

> **`sad_bala_sufficient` v1.0** — a unitless **step** factor carrying the
> cited sufficiency predicate, and nothing else:
>
> - **Cited rule:** Phaladīpikā **IV.22–23, `phaladeepika:PG79:C1`** (the
>   campaign's served edition/translation, corpus locator as transcribed in
>   `PROMISE_NATURE_YOGA_MAP_v1_1.md:244–254`): total ṣaḍbala sufficiency
>   thresholds — Sun 6.5, Moon 6, Mars 5, Mercury 7, Jupiter 6.5, Venus 5.5,
>   Saturn 5 rūpas. Output `1` when the operand's total ṣaḍbala **≥** its
>   graha threshold (equality IS sufficient — the boundary is stated
>   explicitly), else `0`. `units='unitless'`, `range=[0,1]` — the range is an
>   **output** range; it never bounds the raw input. IV.24 (`PG80:C1`) is
>   bhāvabala composition, cited only for that separate statement; bhāvabala
>   and ṣaḍbala are never silently combined. No thresholds for Rāhu/Ketu
>   exist in the citation and none are manufactured.
> - **Null policy (pinned):** the factor's membership declares
>   **`null_state = 'unqualified'`**. A node operand, or any missing,
>   incompatible or unsupported operand, leaves the factor **unqualified**:
>   it does not fire, and the score contribution is unknown, never an
>   invented value. **Score qualification is not admission.** Migration
>   1155:822–832 derives `admission_state` from the path's **necessary
>   predicates only** (any false ⇒ `not_admitted`; else any
>   unknown/unevaluated ⇒ `unqualified`; else `admitted`). Because
>   `sad_bala_sufficient` is a **soft factor**, its missing evidence can
>   never set the record's `admission_state` to `unqualified`, and its `0`
>   output can never revoke an admitted interval: admission is decided by the
>   hard predicates; the score orders admitted windows. (S:209–213's
>   multiplication applies to the score; S:129–130/S:401–402 govern
>   admission — the factor touches the first, never the second.)
> - **Evidence binding (pinned):** the operand's raw rūpa magnitude rides as
>   **typed operand evidence** — value, unit `'rupas'`, and full L1
>   provenance (fact_id, subject, build, ayanāṃśa, verification tier), with
>   any unit conversion documented rather than inferred from a field name —
>   outside the factor's output range, never a second scored factor. The
>   authored entry cites the actual L1 operand (fact/category, subject,
>   build, value, unit, tier) and the versioned path membership with its
>   adopted ranking policy; the threshold citation does not establish a
>   calibrated event probability.
> - **Versioning:** the factor and its consuming path membership are
>   versioned together; the legacy `sad_bala_summary` name is retired rather
>   than silently re-typed.

**Schema impact:** none.

---

## AM-7 — D7: `object_role = 'av_qualifier'` + the P5 contract (COMPLETED per v1.1 rank 5)

Codex v1.1: 1204 is consistent and minimal; real residence evidence, shared
physical roots, separate P5 forms and no universal multiplier are accepted.
What remained requirements-not-contracts — form identity, applicability,
typed operand lineage, exact declaration consumption/read-back — are pinned
here. (1157's own header records the declaration-consumption gate as
deliberately deferred to the writer/evaluator contract; this is that
contract.)

**Proposed spec text (amend the `relationship_record` section's role vocabulary + P5 contract):**

> `object_role` admits `'av_qualifier'`: the aṣṭakavarga qualifier — the
> house-span whose BAV/SAV bindu strength qualifies a P5 window. Contract:
>
> - **Form identity:** an `av_qualifier` relationship record represents a
>   **real transit interval** (the transiting agent's residence in the
>   qualified house-span), resolved to an **absolute physical sign** before
>   identity creation, and **shares the physical contact/root** with other
>   interpretations of that same transit, obeying S:194–207's within-path
>   root reduction — an interpretation edge on existing physical evidence,
>   never a duplicate of it. A static BAV/SAV measurement alone is **operand
>   evidence**; it never mints a physical record of its own.
> - **P5a / P5b identity:** the two forms are **separate rule paths with
>   separate (path_id, rule_version) memberships**; their records are
>   identified by that membership, never merged and never double counted.
>   P5a's known-zero adverse result is reported against its (unresolved)
>   nonzero comparator honestly; P5b's cited bands are used as cited, never
>   converted into a universal multiplier. Distinct outcomes survive
>   reduction because reduction never crosses paths.
> - **Applicability:** event-class and affected-person applicability are
>   declared per path; an AV declaration's existence cannot establish
>   occurrence of every event class, and the record's class/person binding
>   must match its path's declaration.
> - **Typed operand lineage:** each record binds (a) the consumed
>   **AV declaration key** — the declaration table's PK `convention`
>   (1157's `ka_gochara_av_polarity_declaration`; its deliberately
>   unresolved key meaning is resolved HERE: the key names the **L1 AV-build
>   convention** the bindu figures were computed under, and the record
>   carries it verbatim); (b) the **bindu figures** as typed operand
>   evidence (value, unit 'bindus', L1 provenance: fact_id, build, tier),
>   competing BAV/SAV operands both recorded when both inform the outcome;
>   (c) the sky convention id of the residence contact.
> - **Declaration consumption / read-back (O-BP-3 made executable):** the
>   writer **reads back the declaration row at insert time**. The insert is
>   rejected loudly when: the named declaration key is **absent**; the
>   operand's fact category is **not in** the declaration's
>   `applies_to_fact_categories`; or the recorded bindu figures **disagree**
>   with the L1 AV extract the declaration governs. A P5 record with a
>   missing or mismatched consumed declaration cannot be written — O-BP-3
>   fails exactly there. P5 **missingness** (no declaration, unavailable AV
>   inputs) is recorded separately per form via the AM-5 receipt's
>   `missing_inputs` state — never silently scored.
> - **The record never manufactures admission.** Its existence is not
>   evidence that any event occurred; admission still runs the path's full
>   predicate chain. The role widening extends interpretive vocabulary; it
>   does not enforce P5-only usage, residence-only records, or
>   declaration-first ordering in SQL — those are THIS named
>   writer/evaluator gate, and P5 DB writes hold until the gate confirms it
>   (steward M20261001T121451-1a8d stands).
>
> **Test obligation:** real residence-qualification acceptance against
> 1153–1157 **plus** 1204 exercising an actual span residence with AV
> declaration consumption (declaration present/absent/mismatched arms), and
> the v1.0 role vocabulary probed in full with valid coverage/contact
> fixtures (the PR-side detector repair ships with this batch).

**Schema impact:** migration 1204 (in PR #2817, kept) — `kgrr_object_role_ck`
and `ka_gochara_object_selector_ok` each widened by the single value.

---

## AM-8 — D1: P6 frame — CLOSED for this batch (1205 SPLIT OUT of #2817; v1.1 ACCEPT)

Codex v1.1 ACCEPTED the withdrawal: no 1205 migration or preflight remains in
#2817; no frame-validator widening ships; the unsafe scored/inherited route
is removed. One evidence correction folded: the retained
`ka_gochara_frame_ok` validator has **five** kinds — `moon`, `lagna`,
`dasha_lord`, `graha`, `bhavat_bhavam` — not the four v0.2 stated.

**Disposition (unchanged):** the future P6 contract lands with the
`day_on_demand` step as a **context-specific testimony template**, not a
shared-validator arm:

> - inheritance admitted **only** on P6 testimony rows; every non-P6 use, and
>   every P6 use with `operator_role='scored'` (or any score_rule), fails;
> - an annotation is evaluated with the parent window's concrete frame, frame
>   argument and affected person, resolved at annotation time; a forbidden
>   effective frame (e.g. the native Moon frame for a relative, 1155:527–528)
>   fails loudly, exactly as if written literally;
> - **parent linkage mandatory**: an absent parent fails; the parent must be
>   an admitted window of the same chart and generation; context resolution
>   when parent members differ follows the AM-4 deferred rule (resolved
>   before P6 lands);
> - **sealed-generation behaviour**: annotating against a sealed generation
>   writes no membership and mutates nothing sealed — the annotation is an
>   ephemeral response object or a separate annotation table, never a member
>   of the parent's window (1156:334–363's same-path-and-version rule is not
>   weakened);
> - `ka_gochara_frame_ok`'s vocabulary stays exactly the v1.0 **five** kinds
>   until such a designed migration lands.
>
> **Test obligations (for that migration):** non-P6 inheritance rejected;
> scored P6 rejected; absent parent rejected; forbidden effective relative
> frame rejected; sealed-parent annotation produces the ephemeral/annotation
> object with zero membership writes; a resolved concrete frame recorded on
> the annotation.

**Schema impact:** none now. The future template migration is new and
protected-window if it touches any live CHECK.

---

## AM-9 — FINDING for the L0 owner: Rāhu/Ketu favourable-house discrepancy — CLOSED (v1.1 ACCEPT)

Codex v1.1 ACCEPTED the narrowed finding in full: placement/vedha/phala
provenances separated; the `BPHS_CH29` affliction gloss retracted; Ketu-12
referred for sourcing/reclassification; no nodal dṛṣṭi; no repair authorized.
Text unchanged from v0.2:

- Phaladīpikā XXVI.2 (PG321:C1) supports the **favourable placements** {3, 6,
  10, 11} from janma-rāśi for both nodes. The L0 seed's node rows combine
  three claims under one citation — the favourable placement, a
  `vedha_house`, and detailed phala. **XXVI.2 sources only the first.**
- **Ketu-12** needs a precise supporting source or an honest
  reclassification, preserving the historical lineage of the row.
- **Disposition:** a finding for the **L0 owner**; no change to the v1.5
  specs or the P2 registry; `favourable_houses.py` follows the text and stays
  as merged. This correction does not hold unrelated P1–P5 implementation
  work.

---

## Batch checklist for the A5.5 gate (v0.3)

| # | Item | Spec fold | New migration? | Decision left? |
|---|------|-----------|----------------|------------------|
| AM-1 | Convention vector byte-pinned + digest; domain authority; bridge evolution | §6.0 (new) | no (data row, chart-serving txn) | no |
| AM-2 | UUIDv8 + lowercase successor oracle O-RX-1a; numeric/sign/star pins; UUID + post-mask vectors | §6.1 | no | no |
| AM-3 | Two transaction categories; chart lock BEFORE legacy coverage writes | §10.1 | no | no |
| AM-4 | Moon/day EPHEMERAL; query receipt storage/identity/manifest exclusion; P6-context deferral | §6.2/§10.1 | no | no |
| AM-5 | `partition_key=event_class` + **path-search receipt completeness** + publication/serving rules | §10.1 | **yes — one additive receipt table** | no |
| AM-6 | `sad_bala_sufficient` v1.0; `null_state='unqualified'`; score-qualification ≠ admission | factor catalogue | no | picked: C |
| AM-7 | `'av_qualifier'` + P5 contract completed (identity/applicability/lineage/read-back) | relationship_record | 1204 (kept), protected window | no |
| AM-8 | P6 testimony template; five frame kinds; future designed migration | new (template) | 1205 SPLIT OUT | no |
| AM-9 | L0 Rāhu/Ketu finding (provenance narrowed) | none | no | L0 owner's ruling |

## Stale-statement corrections folded in v0.3 (v1.1: "correct alongside")

- **Oracle map v1.1 line 133** still referred to 1205 in PR #2817 — stale
  since the 1205 split; the oracle map's partial-coverage report (11 REAL + 2
  strict-xfail sentinels) stands, and its 1205 reference is corrected to name
  the future template migration when the map next versions.
- **v0.2's evidence note** describing the migration suite's omitted
  1156/1157 chain and conjunction AV fixture is stale as of the PR rework:
  `CONTRACT_FILES` covers 1153–1157 and the fixture is a real span residence;
  the *remaining* test debt is the detector/fixture repair tracked under
  v1.1 rank 4 (PR-side, shipping with this batch).
- **AM-8's "four kinds"** corrected to five (above).
- B6-F16/B6-F17 replacements must assert actual union admission, channel
  attribution and unknown-state behaviour (F16) and the actual tārā class,
  admitted-parent binding, coverage and zero scoring effect (F17) — the v1.5
  batch by itself closes neither.
