---
artifact: GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT
version: 0.4
status: DRAFT — revised per ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_2 (REJECT, closer; 1204 independently ACCEPTED, 2026-10-02); collects the A5.5-gate fold-in list; not a spec version
date: 2026-10-02
author: stream-B (spec lane; docs only — no code, no migration file)
supersedes: v0.3 (340f5a7d9) — AM-2 corrected to SQL-valid 'span:' bytes and 1153's enrichment-vs-correction model; AM-5 completed with an obligation inventory, manifest binding, seal integration and the chart→global-SHARED protocol; the five v1.2 P2s listed as named gate follow-ups
sources: >
  ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_2 (Codex gpt-6-astra, verdict REJECT;
  ACCEPTED: AM-1, AM-3, 1204-as-vocabulary-only, rank-2 bootstrap, rank-4
  detector; two P1s remained); steward revision order M20261001T183729-5c91
  (round 4: ONLY the two P1s, each with a worked example and an explicit
  check against 1153's actual SQL; the five P2s listed, not expanded). v0.3
  sources retained: ASTRA_REVIEW v1_0/v1_1; steward M20261001T171150-5c70,
  M20261001T174917-3007, M20261001T015412-6df0, M20261001T121504-90d5;
  stream-B reports M20261001T172813-94e5, M20261001T180938-eac8.
---

# GOCHARA_DESIGN_SPECS v1.5 — AMENDMENT LIST (draft v0.4)

Revision disposition against ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_2. Per the
steward's round-4 order, **only the two P1s are reworked** (§AM-2, §AM-5),
each with a worked example and an explicit check against migration 1153's
applied SQL; the five P2s are listed as named gate follow-ups with owners
(§"A5.5-gate follow-ups"), not expanded. Everything else stands as accepted
in v1.2. Migration discipline unchanged: migrations 1153–1157 are applied and
**never edited**; every schema-side change is a NEW migration, and each one
touching a live CHECK constraint needs a protected window.

v1.2 ranked crosswalk: rank 1 (P1) → §AM-2 (identity/correction vs 1153) ·
rank 2 (P1) → §AM-5 (obligation inventory, manifest, seal, lock protocol) ·
ranks 3–7 (P2) → §"A5.5-gate follow-ups" (named, owned, deferred).

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

## AM-2 — §6.1 identity hash: sha256 → UUIDv8 (pin 4) — REWORKED per v1.2 rank 1 (P1)

Codex v1.2: the UUIDv8 construction, lowercase O-RX-1a policy, UUID vectors
and masked-bit collision example are ACCEPTED. Two direct incompatibilities
with applied migration 1153 remained and are corrected here: (a) `sign:1–12`
is not an accepted stored target (1153:632–635 admits only `point:…`,
`span:…`, `star:…`); (b) v0.3's "a time-only correction keeps its UUID"
contradicts S:641–646 and 1153's enrichment-vs-correction triggers. Both are
rewritten against the actual SQL, quoted below.

**Proposed spec text (amend §6.1):**

> The identity hash is **sha256 over the §6.1 canonical bytes, first 128 bits
> carried as a UUID with the version-8 and variant bits set** (RFC 9562 §5.8).
> After the 6 fixed bits, **122 digest bits remain**; collision resistance is
> the birthday bound ≈ 2^61 identities — a scale, not a uniqueness guarantee,
> and **not** a substitute for collision handling (below). No SHA-1, no
> UUIDv5.
>
> **Canonical bytes, pinned (unchanged from v0.3 except where noted):** UTF-8;
> body/relation tokens in the **stored lowercase form**; single `|`
> delimiters; one flat byte string (no nested hash); **no trailing whitespace
> or newline**. The serialization authority is the reviewed successor oracle
> **O-RX-1a** (lowercase; the frozen v1.4 file is preserved untouched).
>
> **Target grammar — checked against the applied CHECK.** Migration
> 1153:632–635 accepts exactly three target shapes:
>
> ```sql
> canonical_target ~ '^point:([0-9]|[1-9][0-9]|[12][0-9][0-9]|3[0-5][0-9])(\.[0-9]+)?$'
> OR canonical_target ~ '^span:[a-z0-9_]+$'
> OR canonical_target ~ '^star:([1-9]|1[0-9]|2[0-7])$'
> ```
>
> Accordingly (v0.3's `sign:` tokens are WITHDRAWN — they fail this grammar):
>
> - **point targets:** `point:<λ>` at **full solved precision as stored**
>   (S:648–649: `point:<λ full precision>`). v0.3's six-decimal rendering
>   rule is WITHDRAWN: it quantizes before hashing (`198.5200001` vs
>   `198.5200004` collapse), destroying exactly the distinction collision
>   detection depends on. Numeric rendering is: the stored text, produced by
>   one pinned formatter that preserves full precision, decimal, no exponent;
>   the quantization/governance question (rounding mode, seam behaviour,
>   method-version consequence) is follow-up **F-4**, not settled here.
> - **span targets (absolute signs):** `span:1`–`span:12`, explicitly defined
>   as absolute signs (1 = Meṣa), consistent with S:648–649's `span:<sign>`
>   and the shipped fixture's `span:7`. No CHECK widening is needed.
> - **star targets:** the **stored 1-based** index `star:1`–`star:27`; the
>   tārā oracle's zero-based indices map as `star_zero = star_stored − 1`.
>   Zero-based values never appear in canonical bytes.
>
> Identity tuple components, exhaustive and ordered:
> `body | relation | target | convention_id | occurrence_ordinal`.
>
> **Enrichment vs correction — checked against the applied triggers.**
> Migration 1153 enforces, and this amendment adopts verbatim, the following
> model (v0.3's "a time-only correction amends mutable enrichment, identity
> untouched" is RETRACTED — it is exactly what the SQL rejects):
>
> ```sql
> -- 1153:1131-1136 (ka_gochara_contact_guard, BEFORE UPDATE) — the ONLY
> --   permitted enrichment flip:
> --     OLD.t_exact IS NULL AND NEW.t_exact IS NOT NULL
> --     AND OLD.coverage->>'truncated' = true AND NEW.coverage->>'truncated' = false
> --     AND OLD.solver_method = 'clipped_truncated' AND NEW.solver_method <> 'clipped_truncated'
> --     AND (OLD.coverage - 'truncated') = (NEW.coverage - 'truncated')
> -- 1153:1137-1145: id / physical_object_id / ordinal / convention / body /
> --   relation_kind (and chart/generation) are IMMUTABLE in an UPDATE
> -- 1153:1147-1153: t_in is never changeable; a published non-NULL
> --   t_out/t_exact/delta_lambda/delta_t/precision_regime RAISES '...a
> --   correction (new identity + supersedes edge, under a corrected target or
> --   a new convention), not an UPDATE'
> -- 1153:1155-1159: solver_method may only LEAVE 'clipped_truncated' as part of
> --   the flip; coverage changes only as part of the flip
> -- 1153:1163-1175 (N6): one contact_id carries ONE solved reading across
> --   generations; a conflicting reading under the same id is refused
> -- 1153:1081-1093 (row CHECKs): t_exact IS NULL <=> coverage.truncated;
> --   coverage.truncated <=> solver_method='clipped_truncated'; an exact row
> --   needs delta_lambda, delta_t and precision_regime NOT NULL
> -- 1153:773-788: the identical rules for ka_gochara_sky_event
> -- 1153:813-826 (ka_gochara_contact_identity): contact_id PK,
> --   UNIQUE(physical_object_id, occurrence_ordinal), kgci_no_self_supersede_ck,
> --   kgci_supersedes_uq (a chain, never a tree); 1153:839-870 supersede guard:
> --   predecessor must exist, SAME body AND relation_kind, not already
> --   superseded; 1153:881-884: UPDATE/DELETE refused (insert-only)
> -- 1153:619-635 (ka_gochara_physical_object): the natural key INCLUDES
> --   convention_id — a new convention or a new target IS a new physical object
> ```
>
> The two cases, and only these two:
>
> 1. **NULL/truncated → solved (enrichment):** the row keeps its `contact_id`
>    and ordinal; the UPDATE satisfies the 1153:1131–1136 flip predicate
>    **exactly** (t_exact NULL→value, `coverage.truncated` true→false,
>    `solver_method` leaving `clipped_truncated`, remaining coverage keys
>    equal) and fills `delta_lambda`/`delta_t`/`precision_regime` (required
>    by kgc_exact_precision_ck) and, if NULL, `t_out`; it changes no
>    published non-NULL value and never `t_in`; **no supersedes edge** is
>    written or needed. (S:641–646's enrichment clause.) Any UPDATE touching
>    more than that raises.
> 2. **Existing non-NULL reading → corrected reading (correction):** a NEW
>    identity row, never an UPDATE. Because `ka_gochara_physical_object`'s
>    natural key is `(body, relation_kind, canonical_target, convention_id)`
>    and identity is one row per `(physical_object_id, occurrence_ordinal)`,
>    the correction can only exist under **a corrected `canonical_target`
>    (a different physical object) or a new `convention_id`** — the same
>    target under the same convention has exactly one identity per ordinal
>    and exactly one reading. The new identity is the same `body` and
>    `relation_kind` (the guard at 1153:858–861 enforces it), deterministic
>    UUID, linked by `supersedes_contact_id` to the retired predecessor; the
>    old id is retired, never updated, never reused, and may be superseded
>    once only (kgci_supersedes_uq). v0.3's blanket prohibition on
>    corrected-target supersession is RETRACTED: S:645–646, the
>    identity-table COMMENT (1153:829–837) and the guard expressly support it.
>    A "corrected ephemeris" that changes a solved reading is by definition a
>    new `ephemeris_generation` and therefore a new convention (AM-1): it is
>    case 2 under a new convention id, never case 1.
>
> **Worked example A — enrichment (acceptance shape for O-RX-1a):**
> contact `mars|conjunction|point:198.52|c0|1` →
> `23276d7c-c127-8f4c-9ad5-6b7c8da8020f`, inserted truncated:
> `t_exact` NULL, `coverage={"truncated":true}`,
> `solver_method='clipped_truncated'`, `t_out` NULL allowed
> (kgc_t_out_unless_truncated_ck). The solver refines it with ONE UPDATE:
> `t_exact='2025-03-10T00:00Z'`, `delta_lambda`, `delta_t`,
> `precision_regime` set, `coverage={"truncated":false}`,
> `solver_method='swiss_refined'`. Every row CHECK holds and the flip
> predicate is TRUE → accepted, **same UUID**, no supersedes edge. The same
> UPDATE with `t_in` changed, or with `t_exact` filled while
> `solver_method` stays `clipped_truncated`, raises (1153:1147–1153 /
> 1155–1156) — and kgc_t_exact_iff_truncated_ck would refuse it independently.
>
> **Worked example B — correction (the same contact, later):** the reading
> is now non-NULL (`t_exact='2025-03-10T00:00Z'`). The corrected ephemeris
> puts the crossing at `2025-03-10T00:00:30Z`.
> (1) `UPDATE … SET t_exact='2025-03-10T00:00:30Z'` → **raises** at
> 1153:1147–1153 (published non-NULL value). (2) Re-inserting the same id in
> another generation with the new reading → **raises** at 1153:1163–1175
> (N6). (3) The only accepted route: AM-1 mints convention `c1`
> (new `ephemeris_generation` label ⇒ new digest ⇒ new `convention_id` and
> bridge row); the substrate inserts physical object
> `mars|conjunction|point:198.52` under `c1`; the contact identity is
> `mars|conjunction|point:198.52|c1|1` →
> `eec1d008-2a69-8857-9164-786f5c8e96e8`, inserted with
> `supersedes_contact_id = 23276d7c-…020f`. The guard passes (predecessor
> exists, body `mars` = `mars`, relation `conjunction` = `conjunction`, not
> yet superseded). (4) A second correction of `23276d7c-…020f` — e.g. under a
> `c2` — raises "already superseded" (the guard's message; race-safe
> backstop kgci_supersedes_uq). (5) An attempt to write identity
> `mars|residence|…` superseding the conjunction raises at 1153:858–861
> (relation_kind differs). (6) A corrected **target** instead of a new
> convention follows the same path: `mars|conjunction|point:198.5300|c0|1`
> is a different physical object, its own UUID, supersedes the old id.
>
> **Target grammar — SQL-valid vs writer-enforced.** The CHECK only requires
> `^span:[a-z0-9_]+$`, so `span:13` or `span:abc` would pass SQL. The `span:`
> sign pin (`span:1`–`span:12`, absolute) is therefore a **writer/validator
> obligation**, not a database guarantee; the identity builder rejects any
> other `span:` value, and the O-RX-1a acceptance includes the negatives
> `sign:7` (fails kgpo_target_form_ck), `span:13` and `span:07`
> (builder-rejected).
>
> **Collision taxonomy, all decided BEFORE any UUID-keyed deduplication**
> (`ON CONFLICT DO NOTHING` alone is forbidden as the only check):
>
> 1. same canonical tuple, same ID — legitimate replay, **provided the
>    immutable payloads are equal**; skip.
> 2. different canonical tuple, same ID — loud build failure.
> 3. same canonical tuple, different ID — serialization/version divergence;
>    loud build failure.
>
> Comparison happens on the **canonical tuple**, never on the UUID alone:
> the UUID masks overwrite 6 digest bits, so two genuinely different digests
> can share one UUID (worked vector below).
>
> **Pinned UUIDv8 vectors (recomputed by stream-B; the reviewer independently
> matched all five plus the masked-bit pair):**
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
> (verified). The forced-collision suite must include this class alongside
> the different-tuple/same-UUID and same-tuple/different-UUID arms.
>
> **O-RX-1a acceptance:** one physical object, ordinals 1–3, truncated-centre
> enrichment retaining its id (case 1 above), ordinal 4 appended on in-domain
> partition extension without renumbering; a changed non-NULL reading
> rejected as an UPDATE and accepted only as a new identity with a supersedes
> edge (case 2); the uppercase variant rejected as non-canonical input.

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
>    candidate records/windows, search inventory + ledger rows (AM-5), and **every legacy
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
>                     insert AM-5 inventory, path pins, obligations, search-interval ledger, contacts, records, windows.
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

## AM-5 — Coverage-partition ownership and **explicit completeness** (REWORKED per v1.2 rank 2 (P1))

Codex v1.2: v0.3's receipt fixed cross-path interval conflation but kept
flattening *within* a path — target counts are not a target inventory, and
relations were not bound to targets or intervals; publication integration, the
frozen applicability inventory and receipt protection were incomplete. The v0.3
`ka_gochara_path_search_receipt` (one multirange + one relation list + three
counts per path) is **WITHDRAWN** and replaced by the obligation inventory and
interval ledger below.

**What is and is not claimed.** No *general* proof that the evaluator searched
"everything the doctrine implies" is claimed — the database cannot know the
doctrine. What is specified is the **conservative completeness rule**: a class
is *complete* over an interval only when **every obligation of an immutable,
digest-bound inventory is recorded searched over that whole interval in the
SAME sealed generation**; otherwise the state is *partial* (or weaker) and
serving refuses "complete-empty". The split between what SQL enforces and what
remains a writer/oracle obligation is stated explicitly (table below), so no
flag claims more than a detector measures (CLAUDE.md §N.8).

**Proposed spec text (amend §10.1):**

> The `ka_gochara_v5` writer owns the `'5.0'` coverage partitions in
> `kala_gochara_coverage`: it inserts/extends its own partitions with
> `partition_kind = 'event_class'` and **`partition_key = <event_class>`**
> (the only key both applied guards admit, 1155:706–709 / 1156:402–405),
> `completed_horizon` within the governed domain, `relations_searched` exact —
> in the same chart-serving transaction, after the chart lock and before the
> records/windows that FK them (AM-3). **The partition is only the
> guard-facing summary; completeness authority is the inventory + ledger.**
>
> **1. Obligation — the atomic unit of search.** An obligation is the 9-tuple
> `(event_class, path_id, rule_version, agent, relation, object_role, target,
> frame, person)`: exactly the qualified `(agent, relation, object_role)` that a
> sealed `(path_id, rule_version)` row's `object_selector` names (S:228,
> O-RP-8), instantiated to a concrete natal `target` of the class's target
> inventory (S:215–231), with its `frame` (`moon`/`lagna`/`dasha_lord`/…) and
> `person` (`self` or the relative of a bhāvāt-bhāvam frame). Period-lord
> agents are role tokens (`period_lord:md|ad|pd`), the concrete graha being
> resolved per interval from L1. It enumerates exactly the qualified
> obligations — never an unrestricted Cartesian product.
>
> **Obligation identity (pinned bytes).** `canonical_bytes` = the nine fields
> in that order, lowercase stored form, single `|`, absent field = empty string
> (arity always 9), UTF-8, no trailing whitespace; `ob_id` = the AM-2 UUIDv8
> construction over those bytes. The insert trigger **recomputes** `ob_id` from
> the columns (`sha256()` + the version/variant bit mask) and refuses a mismatch.
>
> **2. Path pins — the frozen applicability inventory.** Per
> `(chart, generation, event_class)` the writer declares, **before** any search
> (this also gives geometry planning its qualified-target input), a *total
> partition of the registry's sealed rule versions*: every sealed
> `(path_id, rule_version)` in `ka_gochara_rule_path_seal` appears exactly once
> as `included` or `excluded`. An exclusion carries a closed `reason` and a
> non-blank `basis` (spec section or ruling):
>
> | exclusion reason | degrades "complete-empty"? |
> |---|---|
> | `not_applicable_to_class` | no |
> | `on_demand_tier` (P6 testimony; never admits a window) | no |
> | `disabled_form` (e.g. a P5 form not enabled; requires `ruling_ref`) | **yes** |
> | `inputs_unavailable` (e.g. no AV declaration; requires `ruling_ref`) | **yes** |
> | `tier_withheld_by_ruling` | **yes** |
>
> Silence is never an exclusion, and "applicable sealed versions" is **copied
> into the pins at declaration** — it can never mean whatever registry rows
> happen to exist at serving time. P6 therefore cannot make a build depend on
> future day queries (it is a recorded `on_demand_tier` exclusion), and a
> disabled or input-starved path cannot silently vanish from the inventory.
>
> **3. Storage (one additive migration, chart-scoped, all under the chart lock):**
>
> ```
> ka_gochara_search_inventory (chart_id, generation, event_class)   -- PK
>   horizon tstzrange NOT NULL        -- governed horizon, finite, inside the AM-1 domain
>   convention_id text NOT NULL       -- the AM-1 sky convention
>   inventory_digest text NOT NULL    -- sha256(sorted pin rows ‖ sorted obligation bytes ‖ horizon ‖ convention)
> ka_gochara_search_path_pin (chart_id, generation, event_class, path_id, rule_version)  -- PK
>   disposition text ('included'|'excluded'), exclusion_reason text, basis text, ruling_ref text
>   FK (path_id, rule_version) -> ka_gochara_rule_path_seal
> ka_gochara_search_obligation (chart_id, generation, event_class, ob_id)  -- PK
>   path_id, rule_version, agent, relation, object_role, target, frame, person, canonical_bytes
>   FK to an 'included' pin (trigger); ob_id recomputed (trigger)
> ka_gochara_search_interval (chart_id, generation, ob_id, search_range tstzrange)
>   state text ('searched_complete'|'searched_unqualified'|'missing_inputs'), detail jsonb
>   -- half-open, finite, inside inventory.horizon; per-ob_id ranges are DISJOINT
>   --   (trigger check, race-free because every writer holds the chart EXCLUSIVE key)
> ```
>
> Writes to all four: BEFORE-statement chart-context trigger
> (`ka_gochara_substrate_chart_lock`, 1153:560–578), UPDATE refused always,
> DELETE refused once the generation is sealed (`ka_gochara_generation_is_sealed`)
> and permitted on a candidate generation only as the dependency-ordered
> candidate replacement of AM-3 (intervals → obligations → pins → inventory),
> TRUNCATE refused. Obligation insert additionally runs
> `ka_gochara_require_sealed_rule_path()` (1154:481–492; it already takes
> `ka_gochara_lock_global_shared()` before reading the rule seal), so no
> obligation can name an unsealed rule version.
>
> **4. The completion rule (universal over the inventory).** For class C and
> interval I, with `Inv(C)` the stored obligations:
> `complete(C, I) ⇔ ∀ ob ∈ Inv(C): I ⊆ ⋃ { r.search_range : r.state = 'searched_complete' }`.
> Counts and relation lists may *summarize* the inventory; they never replace it.
>
> **5. Publication / seal integration.** A new `BEFORE INSERT` trigger
> `ka_gochara_generation_seal_z_search_complete` on `ka_gochara_generation_seal`
> (additive: the applied `ka_gochara_generation_seal_guard`, 1153:918–955, is
> **not** replaced; the new trigger takes the chart key itself, then
> `ka_gochara_lock_global_shared()`, so firing order is irrelevant) calls the
> new `ka_gochara_search_completeness_violations(chart, generation)` and refuses
> the seal if any row returns:
>
> | violation | meaning |
> |---|---|
> | `partition_without_inventory` | an `event_class` partition exists with no inventory (class claimed, never inventoried) |
> | `inventory_without_partition` | inventory for a class with no partition |
> | `registry_unaccounted_path` | a sealed registry path is neither pinned `included` nor `excluded` for the class (covers a path added after declaration) |
> | `inventory_digest_mismatch` | stored digest ≠ recomputation from the stored pins/obligations |
> | `obligation_uncovered` | `inventory.horizon ⊄ ⋃ searched_complete ∪ searched_unqualified` for an obligation — **including an obligation with zero ledger rows** (a wholly missing path, which 1156's consumer-based drift function cannot see) |
> | `missing_inputs_present` | any ledger interval in state `missing_inputs` (the path must instead be re-declared as an `inputs_unavailable` exclusion with a ruling, in a new candidate inventory) |
> | `partition_overclaims` | partition `completed_horizon ≠ inventory.horizon`, or a relation in `relations_searched` that no included obligation names, or an included obligation's relation absent from `relations_searched` |
>
> `searched_unqualified` seals (it is evaluated-but-unknown, not rejection). The
> check reads the tables directly — it does not depend on records or windows
> existing, so a receipt-only complete-empty class is sealed or refused on its
> own evidence.
>
> **6. Manifest binding.** `inventories_digest := sha256` over the sorted
> `(event_class, inventory_digest, ledger_digest)` triples of the generation,
> where `ledger_digest` is sha256 over the class's canonical
> `ob_id|lower|upper|state` rows, sorted. The generation-5 manifest-digest
> preimage **includes** `inventories_digest` (the existing legacy helper hashes
> all coverage rows — `gochara_kernel/ledger.py:503–518` — so this is an
> explicit generation-5 implementation shared with AM-4's `moon_on_demand`
> exclusion: follow-up F-7). Because the four tables are immutable once the
> generation is sealed, a read-only `ka_gochara_search_inventories_digest(chart,
> generation)` recomputes the identical value forever; manifest ↔ ledger is
> verifiable by recomputation, not by trust.
>
> **7. Chart → global-SHARED lock protocol.** Every transaction that writes
> inventory, pins, obligations, intervals or seals — **including a receipt-only
> transaction that emits no record or window** — takes
> `ka_gochara_lock_chart(chart)` (chart EXCLUSIVE) **first**, then
> `ka_gochara_lock_global_shared()` before reading any rule seal or the
> registry's sealed set (the same discipline as 1154:479–490). The seal trigger
> repeats the sequence, so a sealing transaction cannot interleave with a
> registry mutation (which holds global EXCLUSIVE and is refused if a chart key
> is held, 1153:467–470). No receipt-only path relies on record/window triggers
> to reach these locks.
>
> **8. Immutability and replay.** Inserts into a sealed generation are refused.
> Identical replay (same `ob_id`, equal payload) is a no-op; a changed-input
> retry on a candidate deletes and re-inserts in dependency order and changes
> `inventory_digest`; an extension of search after seal is a **new generation**.
>
> **9. Serving rule.** For (class C, interval I) of a sealed generation, compute
> per obligation the status of I from the ledger and report the **weakest**
> present state, in this order (weakest → strongest): `not_searched`
> (no inventory/partition for C) · `partial` (some part of I covered by no
> interval, listing each `(ob_id, gap)`) · `unqualified` (all covered, some
> only by `searched_unqualified`) · `searched`. An empty admitted set is
> reported as **"searched, none admitted"** only when the status is `searched`
> **and** no degrading exclusion (table above) applies; with a degrading
> exclusion the answer is `searched_scoped`: "none admitted among the searched
> paths; excluded: <path, reason>". Every answer carries the per-obligation
> detail. `not_searched`, `partial`, `unqualified` and `searched_scoped` are
> never reported as rejection or as complete-empty.

**What SQL enforces vs what stays a writer/oracle obligation (stated, not implied):**

| Claim | Enforced by |
|---|---|
| ledger gaps / uncovered obligation / missing path **cannot seal** | SQL (seal trigger, §5) |
| `ob_id` matches its bytes; digests match stored rows; sealed rows immutable | SQL (triggers, recomputation) |
| every sealed registry path accounted for per class | SQL (`registry_unaccounted_path`) |
| partition cannot over-claim vs the ledger | SQL (`partition_overclaims`) |
| the inventory contains **the right obligations** for the class | writer derivation + new oracle **O-RP-9** (deterministic re-derivation of `Inv(C)` from the sealed rules + L1 facts; recomputation must reproduce `inventory_digest`), with O-RP-8 qualification — **not** SQL |
| an exclusion's `basis` is true | review / O-RP-9 — SQL checks only non-blank + closed reason + ruling presence |

**Worked example W1 — the reviewer's within-path case (illustrative tokens, not
doctrine; the arithmetic is what is shown).** Class `marriage`, path `p1`
v`1.0`, two obligations (`ob_id` = UUIDv8 over the bytes):
`A = marriage|p1|1.0|jupiter|residence|lord|lord_of:7|dasha_lord|self` →
`b08c2264-6ddc-8323-8476-8d8fcb71c463`;
`B = marriage|p1|1.0|jupiter|residence|occupant|occupant_of:7|dasha_lord|self` →
`60b22060-4b9c-892b-9d19-f05eb3b2f70b`. Governed horizon
`[2025-01-01, 2025-03-01)`; `inventory_digest` prefix `b4e36531d8b1d400` (sorted
bytes).
- **History H1:** A searched January only, B searched February only → ledger
  `(A,[01-01,02-01),complete)`, `(B,[02-01,03-01),complete)`; `ledger_digest`
  prefix `329b06390ffa28da`.
- **History H2:** both searched January–February → `(A,[01-01,03-01),complete)`,
  `(B,[01-01,03-01),complete)`; `ledger_digest` prefix `40663c778b623cfe`.
- Under **v0.3** both histories were the *same row*: relations `{residence}`,
  2 targets required/2 resolved, interval union `[01-01,03-01)`. Under the
  ledger they are distinct, and: serving a Jan–Feb query with zero windows →
  H1: `partial` — A uncovered `[02-01,03-01)`, B uncovered `[01-01,02-01)`; the
  seal trigger returns two `obligation_uncovered` rows and **refuses**; H2:
  `searched` → "searched, none admitted", seal accepted. Two same-path partial
  searches are therefore never readable as complete-empty: completeness is
  `∀ ob` coverage, and H1 fails it for A and B individually. A later append of
  `(A,[02-01,03-01))` and `(B,[01-01,02-01))` to the *candidate* turns H1 into H2
  (new `ledger_digest`); the same append after sealing is refused (new
  generation).

**Worked example W2 — a wholly missing path.** Class `marriage` pins `p1` and
`p5a` both `included`; the writer inserts obligations and ledger rows for `p1`
only. No record or window references `p5a`, so 1156's drift function returns
no violation. The seal trigger's `obligation_uncovered` check finds `p5a`
obligations with zero ledger rows → refused. If instead `p5a` was never pinned
and the registry holds its sealed row → `registry_unaccounted_path` → refused.
If `p5a` is declared `excluded / inputs_unavailable` with a ruling, the class
seals and serves `searched_scoped`.

**Worked example W3 — receipt-only complete-empty transaction.**
```
BEGIN (READ COMMITTED);
SELECT ka_gochara_lock_chart('482012f1-…');          -- chart EXCLUSIVE first
SELECT ka_gochara_lock_global_shared();               -- then global SHARED, before any rule-seal read
INSERT … ka_gochara_search_inventory / path_pin / obligation / interval …;
  -- obligation insert re-runs ka_gochara_require_sealed_rule_path()
UPSERT kala_gochara_coverage (event_class, <class>) partition;   -- chart key already held
UPDATE kala_gochara_publication SET status='published';
SELECT ka_gochara_seal_generation(chart, '5.0');      -- seal trigger re-takes both keys, checks §5
COMMIT;
```
No record or window is written; the transaction is still serialized against
registry mutation and against every other chart writer, and the seal either
records a ledger-proved complete-empty class or refuses.

**Check against the applied guards.** *1155 record guard:* the partition shape
is unchanged (`partition_kind='event_class'`, `partition_key=<class>`, finite
horizon, `coverage_facts` = current facts, relation ∈ `relations_searched`,
bridged convention, `t_in` ∈ horizon — 1155:696–748) because the inventory only
*tightens* what the writer may put in the partition (`partition_overclaims`);
no record that passed before is rejected for a reason the inventory adds, and
the added seal-time `relations_searched` equality is satisfied by construction.
*1156 drift:* `ka_gochara_coverage_drift` (1156:499–546) still classifies
records/windows against the partition; the horizon-`extended` allowance is
preserved, and the added seal check closes the one thing it cannot see (an
unsearched obligation with no consumer). *1153 seal:* the applied guard and
`ka_gochara_seal_generation` are untouched; the new trigger is purely
additive. Nothing in 1153–1157 is edited.

**Schema impact (corrected, again):** ONE new additive migration — four
tables, three functions (`…_violations`, `…_inventories_digest`, the seal
trigger function) and one trigger on an existing table. It touches no live
CHECK, but it **does** need the protected schema-capability route (the
ordinary role has no `CREATE` on `public`: `deploy.yml:953–962`,
`jataka-schema-capability.ts:54–67`) — v0.3's "no protected window" claim is
withdrawn; exact wiring is follow-up F-3.

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
>   inputs) is recorded separately per form via the AM-5 ledger's
>   `missing_inputs` interval state or an `inputs_unavailable` exclusion — never silently scored.
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

## Batch checklist for the A5.5 gate (v0.4)

| # | Item | Spec fold | New migration? | Decision left? |
|---|------|-----------|----------------|------------------|
| AM-1 | Convention vector byte-pinned + digest; domain authority; bridge evolution | §6.0 (new) | no (data row, chart-serving txn) | no |
| AM-2 | UUIDv8 + O-RX-1a; SQL-valid `span:`/`star:`/`point:` bytes; enrichment-vs-correction per 1153; UUID + post-mask vectors | §6.1 | no | no |
| AM-3 | Two transaction categories; chart lock BEFORE legacy coverage writes | §10.1 | no | no |
| AM-4 | Moon/day EPHEMERAL; query receipt storage/identity/manifest exclusion; P6-context deferral | §6.2/§10.1 | no | no |
| AM-5 | `partition_key=event_class` + **obligation inventory + interval ledger**, seal trigger, manifest binding, lock protocol, serving states | §10.1 | **yes — one additive migration (4 tables, 3 functions, 1 trigger); protected schema-capability route (F-3)** | no |
| AM-6 | `sad_bala_sufficient` v1.0; `null_state='unqualified'`; score-qualification ≠ admission | factor catalogue | no | picked: C |
| AM-7 | `'av_qualifier'` + P5 contract completed (identity/applicability/lineage/read-back) | relationship_record | 1204 (kept), protected window | no |
| AM-8 | P6 testimony template; five frame kinds; future designed migration | new (template) | 1205 SPLIT OUT | no |
| AM-9 | L0 Rāhu/Ketu finding (provenance narrowed) | none | no | L0 owner's ruling |

## A5.5-gate follow-ups (v1.2 ranks 3–7, P2 — named and owned, NOT expanded in this round)

| ID | v1.2 rank | Follow-up | Owner | Blocks |
|---|---:|---|---|---|
| F-3 | 3 | Receipt/inventory migration: correct the "no protected window" claim (done in AM-5 schema impact) and specify the exact schema-capability route and runner wiring (`deploy.yml:953–962`, `jataka-schema-capability.ts:54–67`) | Stream A (migration author) with steward (dispatch) | receipt migration acceptance |
| F-4 | 4 | Full-precision point formatter pin and the quantization/rounding/seam/method-version question; canonical-byte contracts for physical-object, relationship-record and window IDs (frame args, nulls, ordered versioned prerequisites, source/citation serialization, intervals, generation/input binding); qualified-geometry declaration before phase-one solving and re-solve-vs-re-score reason (AM-5's pins/obligations are its input); retain O-RX-1a and invalidation tests (O-RW-1) | Stream B (bytes/spec) + Stream A (identity builder) | A5.5 identity gate |
| F-5 | 5 | Typed operand storage for AM-6 rūpas and AM-7 bindus/declaration binding; declaration-key bytes and L1 build/convention identity; exact P5a/P5b path IDs and applicability storage; place `null_state` on the versioned `ka_gochara_factor` row (1154:310–334), not the membership row, and name the edition/translator for Phaladīpikā IV.22–23 | Stream B (AM-6/AM-7 text, one-line SQL-location correction due in v0.5) + Stream A (storage) | AM-6/AM-7 writer acceptance |
| F-6 | 6 | Complete synthetic P5 semantic fixtures: numeric bindu mismatch, BAV/SAV selection, independent P5a/P5b missingness, citation-through-declaration via an actual evaluator path (not the test-local `consumeDeclaration`); correct the oracle map's stale 1205 reference (line 133) at its next version; replace B6-F16/F17 sentinels | Stream A (PR #2817 fixtures) + Stream B (oracle map v1.2) | P5/A5.5 acceptance (not vocabulary-only 1204) |
| F-7 | 7 | Moon query log: table/API name, receipt key, query context, evaluator versions, canonical result rendering excluding self-referential digest/audit fields; generation-5 manifest-digest implementation (also carrying AM-5's `inventories_digest`) with before/after-seal proof; P6 parent-context/containment stays held | Stream B (AM-4 text) + Stream A (implementation) | Moon/day implementation acceptance |

New oracle proposed by AM-5 for the successor oracle file (frozen v1.4 untouched):
**O-RP-9** — deterministic re-derivation of `Inv(C)` from the sealed rule
versions + L1 facts reproduces `inventory_digest`; plus negative arms for the
W1/W2 histories (partial → refused seal, `partial` serving; missing path →
refused; exclusion without ruling → refused).

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
