---
artifact: GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT
version: 0.25
status: v0.5 ACCEPTED at pre-gate 2026-10-02 (Codex v1.4, ACCEPT_WITH_AMENDMENTS, no P1 blocking; reviewed commit 5626290c6); v0.6 adds AM-10 and the F-2 exclusion-evidence binding (not yet reviewed); follow-ups F-1..F-6 owed at the A5.5 gate (table at §"A5.5-gate follow-ups"); still a draft amendment list, not a spec version
date: 2026-10-02
author: stream-B (spec lane; docs only — no code, no migration file)
supersedes: v0.5 (5626290c6, ACCEPTED at pre-gate; v0.6 = AM-10 + F-2 exclusion-evidence binding + header/follow-up renumbering F-1..F-6). v0.5 itself superseded v0.4 (454881c71) — AM-5 completeness reworked (committed obligation sets + proven-empty disposition, immutable search-input snapshot bound to every interval, independent pre-seal verification, seal-replay branch, complete W1 preimages, adversarial-case matrix with an executable model); AM-2 example A repaired. v0.4 itself superseded v0.3 (340f5a7d9) — AM-2 corrected to SQL-valid 'span:' bytes and 1153's enrichment-vs-correction model; AM-5 completed with an obligation inventory, manifest binding, seal integration and the chart→global-SHARED protocol; the five v1.2 P2s listed as named gate follow-ups
sources: >
  ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_3 (Codex gpt-6-astra, REJECT on AM-5; AM-2
  CLOSED, example repair; five ranked items); steward revision order
  M20261001T195233-7184 (round 5: AM-5 completeness ONLY plus three small P2
  repairs; adversarial cases written by the author). Retained: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_2 (Codex gpt-6-astra, verdict REJECT;
  ACCEPTED: AM-1, AM-3, 1204-as-vocabulary-only, rank-2 bootstrap, rank-4
  detector; two P1s remained); steward revision order M20261001T183729-5c91
  (round 4: ONLY the two P1s, each with a worked example and an explicit
  check against 1153's actual SQL; the five P2s listed, not expanded). v0.3
  sources retained: ASTRA_REVIEW v1_0/v1_1; steward M20261001T171150-5c70,
  M20261001T174917-3007, M20261001T015412-6df0, M20261001T121504-90d5;
  stream-B reports M20261001T172813-94e5, M20261001T180938-eac8.
---

# GOCHARA_DESIGN_SPECS v1.5 — AMENDMENT LIST (draft v0.6)

Revision disposition against ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_3 (round 5).
Per the steward's order only **AM-5 completeness** is reworked, plus three
small P2 repairs: seal-function replay, AM-2 example A, and W1's complete
preimage. AM-2's normative text is CLOSED (v1.3) and unchanged apart from the
example repair; everything else stands as accepted. The five v1.2 P2 follow-ups
(now F-1…F-6 — renumbered; see the table) remain named, owned and deferred. Migration discipline unchanged:
migrations 1153–1157 are applied and **never edited**; every schema-side change
is a NEW migration, and each one touching a live CHECK needs a protected window.

v1.3 ranked crosswalk: rank 1 (P1) → §AM-5 items 2, 5 + `committed_set_mismatch`
(finalized obligation sets; absent vs proven-empty; W2 replayed as C1) · rank 2
(P1) → §AM-5 item 0 (immutable search-input snapshot bound to every interval and
to both digests) · rank 3 (P2) → §AM-5 item 5 replay branch (C16) · rank 4 (P2) →
§AM-2 example A · rank 5 (P2) → §AM-5 W1 complete preimages. Prior crosswalks:
v1.2 rank 1 → AM-2, rank 2 → AM-5, ranks 3–7 → F-1…F-6.

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
> **Convention-bridge evolution (restated per Stream A's disagreement report, steward
> M20261001T202801-8ee8 item 2).** `ka_gochara_convention_bridge` (1153:1016–1034) gives each
> legacy `kala_gochara_convention` row exactly one immutable mapping and can never be repointed.
> The legacy convention vector (`record_store.py:257–268`, `ledger.convention_id_for`) carries
> **only** `zodiac, ayanamsha, sidereal_method, node_model, node_source, epoch_convention,
> time_scale, house_system, ephemeris_mode, method_version` — **no grid, no domain, no
> ephemeris-generation label.** A sky-convention correction that changes only those absent fields
> therefore leaves the legacy id identical, and the 1:1 bridge would (correctly) refuse a second
> mapping. The binding rules:
>
> 1. **Lockstep through `method_version`.** `method_version` is the one field both vectors carry.
>    Any correction that changes the sky convention's canonical bytes **must also bump
>    `method_version`** (in the sky vector *and* the legacy vector), which mints a new sky id and
>    a new legacy id together; the old pair stays, each mapped once, mappings never rewritten.
>    The writer **fails loudly before any write** if a changed sky id would resolve to an
>    unchanged legacy id.
> 2. **The `13d20m` correction itself** (A5.3 `13.20` → `13d20m`): **provided no row has been written under the old
>    id (Stream A to confirm — I have not verified production)**, it is applied **before** the first `'5.0'` write as a correction of the
>    not-yet-bridged vector — the bridge row is created once, against the corrected sky id; no
>    second mapping is needed and `method_version` stays `1.0.0`. If any row under the old id
>    exists at that moment, rule 1 applies instead.
> 3. Adding a field to the legacy vector (to tie it to the sky convention directly) is **rejected**:
>    it would change every legacy id (`'4.0'`/`'4.1'` lineage) and `CANONICAL_VECTOR_KEYS` is
>    frozen at WP1 §1.1.

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
>   method-version consequence) is follow-up **F-3**, not settled here.
> - **span targets (absolute signs):** `span:1`–`span:12`, explicitly defined
>   as absolute signs (1 = Meṣa) — **sign NAMES (`span:virgo`, `span:capricorn`, …) are not
>   canonical bytes**; Stream A's evaluator and the span literals in the A5.3 oracle tests
>   (`test_b6_oracles_a53.py`) move to the numerals in one commit (steward
>   M20261001T202801-8ee8 item 1; Stream B reviews that change when it lands), consistent with S:648–649's `span:<sign>`
>   and the shipped fixture's `span:7`. No CHECK widening is needed.
> - **star targets:** the **stored 1-based** index `star:1`–`star:27`; the
>   tārā oracle's zero-based indices map as `star_zero = star_stored − 1`.
>   Zero-based values never appear in canonical bytes.
>
> Identity tuple components, exhaustive and ordered:
> `body | relation | target | convention_id | occurrence_ordinal`.
>
> **Enrichment vs correction — checked against the applied triggers.**
> Migration 1153 enforces, and this amendment adopts, the following model
> (the SQL block below **paraphrases** the cited lines; the lines govern;
> v0.3's "a time-only correction amends mutable enrichment, identity
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
> -- 1153:761-788: the identical rules for ka_gochara_sky_event (its flip
> --   predicate is at 761-766; N6 compares only the solved t_exact/delta_lambda/
> --   delta_t/precision_regime/solver_method fields — NOT t_in/t_out)
> -- 1153:813-826 (ka_gochara_contact_identity): contact_id PK,
> --   UNIQUE(physical_object_id, occurrence_ordinal), kgci_no_self_supersede_ck,
> --   kgci_supersedes_uq (a chain, never a tree); 1153:839-870 supersede guard:
> --   predecessor must exist, SAME body AND relation_kind, not already
> --   superseded; 1153:881-884: UPDATE/DELETE refused (insert-only)
> -- 1153:619-637 (ka_gochara_physical_object): the natural key
> --   ka_gochara_physical_object_natural_uq (636-637) INCLUDES convention_id —
> --   a new convention or a new target IS a new physical object
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
> `23276d7c-c127-8f4c-9ad5-6b7c8da8020f`, inserted truncated with
> `t_in='2025-03-09T00:00:00Z'`, `t_exact` NULL, `t_out` NULL (allowed only
> while truncated: kgc_t_out_unless_truncated_ck, 1153:1089–1090),
> `coverage={"truncated":true}`, `solver_method='clipped_truncated'`.
> The solver refines it with ONE UPDATE that sets
> `t_exact='2025-03-10T00:00:00Z'`, **`t_out='2025-03-11T00:00:00Z'`**
> (NULL→value is permitted, 1153:1148), `delta_lambda`, `delta_t`,
> `precision_regime`, `coverage={"truncated":false}`,
> `solver_method='swiss_refined'`, leaving `t_in` unchanged. The flip
> predicate (1153:1131–1136) is TRUE; kgc_t_exact_iff_truncated_ck
> (1085–1086), kgc_truncated_method_ck (1087–1088),
> kgc_t_out_unless_truncated_ck (1089–1090), kgc_exact_precision_ck
> (1091–1093) and kgc_time_order_ck (`t_in ≤ t_exact ≤ t_out`, 1098–1100)
> all hold → accepted, **same UUID**, no supersedes edge. Each negative arm,
> with its true refuser:
> (a) `t_in` changed → **UPDATE guard**, 1153:1147–1153;
> (b) `coverage.truncated=false` but `solver_method` left
> `clipped_truncated` → **UPDATE guard** 1153:1158–1159 (coverage may change
> only in the flip), with **kgc_truncated_method_ck** (1087–1088) as the
> independent backstop;
> (c) `t_exact` filled while `coverage.truncated` stays `true` and
> `solver_method` unchanged → the guard passes (nothing non-NULL changed) and
> **kgc_t_exact_iff_truncated_ck** (1085–1086) refuses — this is the arm
> that CHECK actually owns;
> (d) the flip with `t_out` left NULL →
> **kgc_t_out_unless_truncated_ck** (1089–1090);
> (e) any change to a non-NULL `t_exact` → UPDATE guard, 1153:1149.
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

## AM-5 — Coverage-partition ownership and **explicit completeness** (REWORKED per v1.3 ranks 1–3, 5)

Codex v1.3: the per-obligation interval ledger, seal integration, lock order
and serving states stand, **conditional on a correctly finalized, input-bound
inventory**. Two P1s remained: (1) v0.4's SQL could not detect an included
path whose obligations were never inserted (W2 as written was refused only by
accident of how the example was phrased); (2) v0.3's explicit search-input
identity had been dropped, so changed L1/declaration inputs could preserve a
completion identity and partial searches from different snapshots could
accumulate. Both are closed below; two P2s (seal replay, W1 preimage) are
folded. **No general completeness proof is claimed** — the rule is the
conservative one and the residual trust boundary is named (§"What SQL enforces").

**Proposed spec text (amend §10.1):**

> The `ka_gochara_v5` writer owns the `'5.0'` coverage partitions in
> `kala_gochara_coverage` with `partition_kind = 'event_class'` and
> **`partition_key = <event_class>`** (the only key both applied guards admit,
> 1155:706–709 / 1156:402–405), `completed_horizon` within the governed
> domain, `relations_searched` exact — in the chart-serving transaction, after
> the chart lock and before the records/windows that FK them (AM-3). **The
> partition is only the guard-facing summary; completeness authority is the
> snapshot + inventory + ledger below.**
>
> **0. Search-input snapshot (declared FIRST, one per chart × generation).**
> `ka_gochara_search_input_snapshot (chart_id, generation)` PK, with
> `convention_id`, `input_generation_vector jsonb`, `consumed_fact_ids text[]`,
> `l1_facts_digest`, `dasha_digest`, `av_declarations text[]` (each
> `<1157 declaration key>:<row sha256>`), and
> `input_digest = sha256` over the canonical preimage (sorted `key=value`
> lines, UTF-8, single `\n`):
>
> ```
> av_declarations=<comma-joined, sorted>
> convention_id=<the AM-1 sky convention id>
> dasha_digest=<sha256 over the sorted L1 dasha rows used for period-lord resolution>
> input_generation_vector=<the manifest's vector, canonical JSON: sorted keys, no spaces>
> l1_facts_digest=<sha256 over sorted "fact_id|sha256(row content)" lines of consumed_fact_ids>
> ```
>
> "Row content" is every column of the L1 row except audit timestamps (exact
> enumeration is F-3's byte contract); a benign L1 rebuild that rewrites
> identical values still changes the identity — the conservative direction.
> Binding, all enforced:
> (a) the snapshot insert trigger **recomputes** `input_digest` from its columns;
> (b) its `input_generation_vector` must **equal** the generation's manifest row
> (`kala_gochara_publication.input_generation_vector`, 1081:109) — the existing
> vector is frozen and checked here, not re-invented;
> (c) the inventory header and **every ledger interval** carry
> `input_digest` and FK `(chart_id, generation, input_digest)` to the snapshot;
> (d) a generation has exactly ONE snapshot (PK), so intervals evaluated under
> two snapshots can never coexist in one generation: a different snapshot is a
> different generation, or — on a candidate — a dependency-ordered delete of
> every dependent row (intervals → obligations → pins → inventory → snapshot)
> followed by a full re-search;
> (e) `input_digest` is an input to both `inventory_digest` and `ledger_digest`,
> so a changed L1 / declaration / dasha input changes every completion identity
> even when targets, path versions and sky convention are identical (C15).
> At seal the check **recomputes** the L1/dasha/AV digests from the live rows and
> refuses on drift (`input_snapshot_drift`), and re-compares the vector to the
> manifest (`input_vector_mismatch`).
>
> **1. Obligation — the atomic unit of search.** The 9-tuple
> `(event_class, path_id, rule_version, agent, relation, object_role, target,
> frame, person)`: the qualified `(agent, relation, object_role)` a sealed rule
> version's `object_selector` names (S:228, O-RP-8), instantiated to a concrete
> natal `target` of the class's target inventory (S:215–231), with its `frame`
> and `person`. Period-lord agents are role tokens (`period_lord:md|ad|pd`).
> **Identity bytes:** the nine fields in that order, lowercase stored form,
> single `|`, absent field = empty string (arity 9), UTF-8, no trailing
> whitespace; `ob_id` = the AM-2 UUIDv8 over those bytes, **recomputed by the
> insert trigger**.
>
> **2. Path pins with an obligation-set COMMITMENT.** Per
> `(chart, generation, event_class)` the writer declares, before any
> obligation or search, a *total partition of the registry's sealed rule
> versions* (every sealed `(path_id, rule_version)` exactly once), each pin
> carrying **`committed_ob_ids uuid[]`** — the finalized obligation set, sorted
> and unique — and a disposition:
>
> | disposition | `committed_ob_ids` | insert-time CHECK | meaning |
> |---|---|---|---|
> | `included` | ≥ 1 ids | cardinality ≥ 1 | the path's qualified obligations are exactly these |
> | `computed_empty` | `{}` | cardinality = 0 | the path was derived and **proven to have an empty qualified set** — a stated disposition, never an absence |
> | `excluded` | `{}` | cardinality = 0, closed `reason`, non-blank `basis`, `ruling_ref` where required | path deliberately outside this class's build |
>
> | exclusion reason | degrades "complete-empty"? |
> |---|---|
> | `not_applicable_to_class` | no |
> | `on_demand_tier` (P6 testimony; never admits a window) | no |
> | `disabled_form` / `inputs_unavailable` / `tier_withheld_by_ruling` (each requires `ruling_ref`) | **yes** |
>
> **Exclusion and `computed_empty` evidence is structured, derivable and
> verified (F-2).** `basis` is a **closed-grammar reference**, never prose:
> `spec:<artifact>@<version>#<anchor>` | `ruling:<id>` | `oracle:<id>`
> (regex `^(spec:[A-Za-z0-9_.-]+@[0-9][0-9A-Za-z.]*#[^|\n%]+|ruling:[A-Za-z0-9._-]+|oracle:[A-Za-z0-9._-]+)$`
> — it can contain no `|`, newline or `%`, so the preimage needs no escaping).
> It is **required** on `excluded` and `computed_empty` pins and **absent** on
> `included` pins. `ruling_ref` (`^[A-Za-z0-9._-]+$`) is **present iff** the
> reason is one of the three degrading reasons (`disabled_form`,
> `inputs_unavailable`, `tier_withheld_by_ruling`) and absent otherwise; `reason`,
> `ruling_ref` and `basis` apply only to `excluded` (basis also to
> `computed_empty`). All three are inserted into the pin row's CHECKs and into
> the pinned `inventory_digest` preimage, so the independent verifier — which
> derives each path's disposition, reason, ruling and basis from **its own**
> applicability table and ruling registry, not from the writer's rows — must
> reproduce them byte-for-byte or the digests differ and the seal refuses
> (`verification_missing_or_mismatch`). Free-text commentary may live in a
> non-authoritative `note` column that is **excluded** from every digest and
> never read by serving.
>
> **Absent obligations vs a proven empty set are therefore different rows:**
> "never inserted" is `committed_ob_ids ≠ stored obligations` (a seal
> violation, below); "proven empty" is the explicit `computed_empty` disposition,
> which is bound to the input snapshot, hashed into `inventory_digest`, named in
> every answer that relies on it, and — like every pin — **re-derived by the
> independent verifier before sealing (item 4)**. An obligation insert is
> refused unless its pin is `included` **and** its `ob_id` is in that pin's
> committed set; it also runs `ka_gochara_require_sealed_rule_path()`
> (1154:481–492; takes `ka_gochara_lock_global_shared()` first).
>
> **3. Storage (one additive migration; all rows chart-scoped under the chart
> lock):** `ka_gochara_search_input_snapshot`, `ka_gochara_search_inventory`
> `(chart_id, generation, event_class)` PK with `horizon`, `input_digest`,
> `inventory_digest`; `ka_gochara_search_path_pin`; `ka_gochara_search_obligation`;
> `ka_gochara_search_interval (chart_id, generation, event_class, ob_id,
> search_range, state, detail, input_digest)` with
> `lower_inc(search_range) AND NOT upper_inc(search_range)`, finite, inside the
> inventory horizon, ranges **disjoint** per `ob_id` (trigger; race-free under
> the chart EXCLUSIVE key), state ∈ {`searched_complete`,
> `searched_unqualified`, `missing_inputs`}; and
> `ka_gochara_search_inventory_verification (chart_id, generation,
> event_class, verifier_id, verifier_version, rederived_inventory_digest)`.
> All: chart-context statement trigger (`ka_gochara_substrate_chart_lock`,
> 1153:560–578); UPDATE refused (**the inventory header's one-shot finalisation excepted**:
> its digests are NULL until a single UPDATE that must equal the recomputation, after which the
> class is immutable); DELETE refused once the generation is sealed and otherwise only as the
> candidate replacement of AM-3; TRUNCATE refused.
>
> **`inventory_digest` preimage (pinned; sorted within sections, `\n`-joined):**
> `convention=<id>` · `horizon=[<lo>,<hi>)` (UTC, `Z`) · `input=<input_digest>` ·
> one `pin=<path>|<rule_version>|<disposition>|<reason>|<ruling_ref>|<basis>|<committed ids, comma-joined>`
> per pin (absent fields rendered empty; **`reason`, `ruling_ref` and `basis` are inside the verified preimage**, v1.4 F-2) · one `ob=<canonical bytes>` per stored obligation.
> `ledger_digest` preimage: `input=<input_digest>` then `<ob_id>|<lower>|<upper>|<state>|<input_digest>` rows,
> sorted (v0.7: the header line input-binds an EMPTY ledger too). `inventories_digest` = sha256 over sorted
> `(event_class, inventory_digest, ledger_digest)` triples.
>
> **4. Mandatory independent verification before publication.** Before
> `ka_gochara_seal_generation`, a **separate derivation path** (verifier code
> that shares no function with the writer's inventory builder — O-RP-9)
> re-derives each class's inventory from the sealed rule versions + the
> snapshot's L1 facts and inserts a verification row carrying its
> `rederived_inventory_digest`. The seal requires, per class, a row whose
> digest equals the stored `inventory_digest`. This is the detector for "the
> inventory contains the right obligations" (pin dispositions, exclusion
> bases, `computed_empty`, committed-set contents); SQL enforces its presence
> and equality, the verifier's independence is a process property (named
> residual below).
>
> **5. Publication / seal integration.** An additive `BEFORE INSERT` trigger
> `ka_gochara_generation_seal_z_search_complete` on `ka_gochara_generation_seal`
> (the applied guard, 1153:918–955, is not replaced; the new trigger takes the
> chart key itself, then `ka_gochara_lock_global_shared()`) has **two branches**:
>
> * **First publication** (no seal row for `(chart, generation)`): runs
>   `ka_gochara_search_completeness_violations(chart, generation)` and refuses on
>   any row:
>
>   | violation | meaning |
>   |---|---|
>   | `partition_without_inventory` / `inventory_without_partition` | class claimed without inventory / inventory without class partition |
>   | `registry_unaccounted_path` | a sealed registry path is neither pinned nor excluded for the class |
>   | `committed_set_mismatch` | for any pin, `committed_ob_ids` ≠ the stored obligation ids (**includes obligations absent / never inserted**, and uncommitted extras) |
>   | `inventory_digest_mismatch` | stored digest ≠ recomputation from stored pins/obligations |
>   | `obligation_uncovered` | `inventory.horizon ⊄ ⋃ (searched_complete ∪ searched_unqualified)` for a stored obligation (incl. zero ledger rows) |
>   | `missing_inputs_present` | any `missing_inputs` interval (re-declare the path as an `inputs_unavailable` exclusion with a ruling in a new candidate) |
>   | `partition_overclaims` | partition horizon ≠ inventory horizon, or `relations_searched` ≠ the included obligations' relations |
>   | `input_snapshot_mismatch` / `input_snapshot_drift` / `input_vector_mismatch` | inventory not bound to the snapshot; live L1/dasha/AV rows no longer match it; snapshot vector ≠ manifest vector |
>   | `horizon_manifest_mismatch` | inventory horizon ≠ `kala_gochara_publication.horizon` |
>   | `verification_missing_or_mismatch` | no verification row, or its digest ≠ the stored `inventory_digest` |
>
>   `searched_unqualified` seals (evaluated-but-unknown, not rejection).
> * **Replay of an already-sealed generation** (`ka_gochara_seal_generation`
>   inserts with `ON CONFLICT DO NOTHING`, 1153:990–992, and a BEFORE-INSERT
>   trigger fires before conflict handling): the trigger enters a **replay
>   branch** that requires (i) `NEW.manifest_id` = the existing seal's
>   `manifest_id` (else raise), (ii) every stored inventory still recomputes to
>   its `inventory_digest` and `ka_gochara_search_inventories_digest` is
>   unchanged, (iii) verification rows still present — and does **not** apply
>   `registry_unaccounted_path`, `input_snapshot_drift` or partition checks,
>   which are first-publication predicates. Historical inventories never have
>   to adopt later registry versions.
>
> **6. Manifest binding.** The generation-5 manifest-digest preimage includes
> `inventories_digest` (the legacy helper hashes all coverage rows —
> `gochara_kernel/ledger.py:503–518` — so this is an explicit generation-5
> implementation shared with AM-4's `moon_on_demand` exclusion: F-6). The six
> storage tables are immutable once sealed, so the read-only
> `ka_gochara_search_inventories_digest(chart, generation)` recomputes the same
> value forever; manifest ↔ ledger ↔ input snapshot is verified by
> recomputation, and the snapshot's vector equals the manifest's.
>
> **7. Chart → global-SHARED lock protocol.** Every transaction that writes the
> snapshot, inventory, pins, obligations, intervals, verification rows or a
> seal — **including a receipt-only transaction emitting no record/window** —
> takes `ka_gochara_lock_chart(chart)` (chart EXCLUSIVE) first, then
> `ka_gochara_lock_global_shared()` before reading any rule seal or the
> registry's sealed set (1154:479–490). A registry mutation holds global
> EXCLUSIVE and is refused if a chart key is held (1153:467–470), so the sealed
> set cannot change under a sealing transaction.
>
> **8. Replay and extension.** Identical replay (same ids, equal payload) is a
> no-op; a changed-input retry on a candidate replaces the whole dependent
> chain and changes `input_digest` and therefore every digest; extending a
> search after seal is a **new generation**.
>
> **9. Serving rule.** Only a **sealed** generation can yield `searched`; an
> unsealed candidate is reported `candidate` (no completeness claim). For
> (class C, interval I) of a sealed generation report the **weakest** present
> state (weakest → strongest): `not_searched` · `partial` (each uncovered
> `(ob_id, gap)` listed) · `unqualified` · `searched`. "Searched, none
> admitted" requires `searched` **and** no degrading exclusion; with one, the
> answer is `searched_scoped` ("none admitted among the searched paths;
> excluded: <path, reason>"). Any `computed_empty` path is **named** in the
> answer. Every answer carries the snapshot's `input_digest` and the
> per-obligation detail.

**What SQL enforces vs the named residual (§N.8 — each claim has a detector):**

| Claim | Enforced by |
|---|---|
| uncovered obligation / zero-ledger obligation / never-inserted obligation **cannot seal** | SQL: `obligation_uncovered`, `committed_set_mismatch` |
| sealed registry path unaccounted for **cannot seal** (first publication) | SQL: `registry_unaccounted_path` |
| intervals from different input snapshots cannot coexist; changed inputs change every completion digest; L1 drift blocks seal | SQL: PK/FK, digest recomputation, `input_snapshot_drift` |
| `ob_id`, `input_digest`, `inventory_digest` match their bytes; sealed rows immutable | SQL triggers |
| partition cannot over-claim vs the ledger | SQL: `partition_overclaims` |
| the inventory / `computed_empty` / exclusion basis is the **right** one | independent re-derivation (O-RP-9) — SQL enforces **presence and digest equality of the verification row only** |
| **named residual:** writer and verifier derive the same wrong inventory (shared bug/misreading of the doctrine) | not detectable in SQL; mitigated by verifier code independence, O-RP-8/O-RP-9 oracle cases and review; a `computed_empty` or non-degrading exclusion is always surfaced in answers |

**Adversarial cases** (every "can never be read as complete" claim, the concrete
row set that would break it, and the guard that stops it). Cases below were
executed against a scratch executable model of the stated predicates —
`design/evidence/am5_model.py`, `am5_cases.py` (32 self-asserting cases; exit status non-zero on any failure), output `am5_cases_output.txt`
(**not Postgres; it checks the logic of the specified predicates, not the SQL**).
Cases marked "not modelled" are by inspection of the predicate; every other refusal appears under its stated guard:

| # | Row set that tries to break the claim | Guard | Result |
|---|---|---|---|
| C1 | **Codex's W2, exactly:** registry {P1,P5a}; pins P1 & P5a `included` (P5a with its committed ids); obligations stored for P1 only; intervals cover every *stored* obligation across the horizon; partition same horizon; `inventory_digest` correctly recomputed from the stored rows; no records/windows; a verifier that merely re-hashes stored rows | `committed_set_mismatch` (P5a: both committed ids have no obligation) | **REFUSED** |
| C1b | P5a `included` with an empty commitment (to dodge C1) | pin CHECK: included ⇒ cardinality ≥ 1 | refused at insert |
| C2 | Absent pin: registry has P5a, no pin for it | `registry_unaccounted_path` | **REFUSED** |
| C3 | P5a pin `computed_empty` though the true qualified set is non-empty; stored rows self-consistent | independent re-derivation digest ≠ stored → `verification_missing_or_mismatch` | **REFUSED** |
| C3b | Same, with no verification row at all | `verification_missing_or_mismatch` | **REFUSED** |
| C3c | Writer commits a strictly smaller `included` set (omits P5B) | same mechanism as C3 (verifier digest differs) | REFUSED (by C3's mechanism; not separately modelled) |
| C4 | Obligations present, one with no ledger rows | `obligation_uncovered` | **REFUSED** |
| C5 | *(positive control)* genuinely empty qualified target set: P5a `computed_empty`, verifier agrees | no violation; serving names P5a as `computed_empty` | seals |
| C7 | Obligation inserted but not in its pin's committed set | insert trigger | refused at insert |
| C8a | An interval stamped with a different `input_digest` | FK `(chart,generation,input_digest)` | refused at insert |
| C8b | A second snapshot for the same generation | PK `(chart_id, generation)` | refused at insert |
| C9 | L1 rebuilt after the search, before the seal | `input_snapshot_drift` | **REFUSED** |
| C9b | Manifest `input_generation_vector` changed after the snapshot | `input_vector_mismatch` | **REFUSED** |
| C11 | Overlapping intervals for one obligation (mixed states) | disjointness trigger | refused at insert |
| C12 | Interval outside the horizon / not `[lo,hi)` | interval CHECKs/trigger | refused at insert |
| C14 | A `missing_inputs` interval | `obligation_uncovered` + `missing_inputs_present` | **REFUSED** |
| C15 | Same targets/paths/convention, different L1 snapshot: does the completion identity survive? | `input_digest` ∈ both digests | **No**: input digests `800d572c…` vs `79109610…`; inventory digests `d9521636…` vs `893619b7…` |
| C16 | Seal replay after registry advance (initial seal → identical replay → registry advance → replay again) | replay branch (item 5) | initial: pass; replay: no-op; after P7 sealed: **replay passes**, while a **first** seal under the same state is refused (`registry_unaccounted_path` P7); different `manifest_id` on replay → raise (specified; not modelled) |
| C17 | Exclusion falsely declared `not_applicable_to_class` | verifier re-derivation (same mechanism as C3/M5; `basis`/`ruling_ref`/`reason` are in the preimage) | REFUSED if the verifier derives the path as applicable; **otherwise the named residual** |
| M1 | A pin's `basis` changed (e.g. P6's on-demand basis swapped for another anchor) | `basis` ∈ preimage → `inventory_digest` changes | digest differs (executed) |
| M2 | A pin's `ruling_ref` changed | `ruling_ref` ∈ preimage | digest differs (executed) |
| M3 | An exclusion `reason` swapped (non-degrading ↔ degrading) | `reason` ∈ preimage | digest differs (executed) |
| M4 | The writer edits an exclusion's basis **after** verification | stored digest/verification mismatch → `verification_missing_or_mismatch` | **REFUSED** (executed) |
| M5 | The writer declares a non-degrading exclusion where the verifier derives a degrading one (hiding a reduced scope) | verifier digest ≠ stored → `verification_missing_or_mismatch` | **REFUSED** (executed) |
| M6 | (a) degrading exclusion with no `ruling_ref`; (b) `basis` outside the closed grammar (prose); (c) `ruling_ref` on a non-degrading reason | pin CHECKs (basis grammar; ruling_ref iff degrading) | refused at insert (executed; each asserted for its own reason) |

**Worked example W1 — the reviewer's within-path case, with the COMPLETE
preimages (illustrative synthetic tokens and input components — not doctrine,
no chart values).** Class `marriage`, path `p1` v`1.0` (`p6` v`1.0` excluded
`on_demand_tier`), horizon `[2025-01-01, 2025-03-01)`. Obligations:
`A = marriage|p1|1.0|jupiter|residence|lord|lord_of:7|dasha_lord|self` →
`b08c2264-6ddc-8323-8476-8d8fcb71c463`;
`B = marriage|p1|1.0|jupiter|residence|occupant|occupant_of:7|dasha_lord|self` →
`60b22060-4b9c-892b-9d19-f05eb3b2f70b`.

```
-- input preimage -> input_digest = 800d572c7db35d0e05f2c41bec3c6c9420b72b42619aaa4602de9596c7a2a0da
av_declarations=1157:lahiri_av_v1:f6493ca574a3
convention_id=sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3
dasha_digest=a244291a2514cca194fa335fa2aac9fa9e2661be5959866518fe55dba423d448
input_generation_vector={"bg_transit_av_gates":"d2","bg_transit_rules":"d1"}
l1_facts_digest=f1bd785eb72ddd67c93664e53d18eb8434e38297ebc37017fde64372b3f5cd11

-- inventory preimage -> inventory_digest = fb278bb92edce1505d649c6aabab96a01f65622fd00e6437a3a33c30836d07db
convention=sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3
horizon=[2025-01-01T00:00:00Z,2025-03-01T00:00:00Z)
input=800d572c7db35d0e05f2c41bec3c6c9420b72b42619aaa4602de9596c7a2a0da
pin=p1|1.0|included||||60b22060-4b9c-892b-9d19-f05eb3b2f70b,b08c2264-6ddc-8323-8476-8d8fcb71c463
pin=p6|1.0|excluded|on_demand_tier||spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/P6|
ob=marriage|p1|1.0|jupiter|residence|lord|lord_of:7|dasha_lord|self
ob=marriage|p1|1.0|jupiter|residence|occupant|occupant_of:7|dasha_lord|self
```

* **H1** (A searched January only, B February only) — ledger preimage → `ledger_digest = bfab922403c857b66ff2eef99f63a45b6882cba31f61f8e7d448c6099fee01ce` (v0.7 input-bound preimage; the v0.6 value `ddbd5a44…` is withdrawn):
  `60b22060-…|2025-02-01T00:00:00Z|2025-03-01T00:00:00Z|searched_complete|800d572c…` and
  `b08c2264-…|2025-01-01T00:00:00Z|2025-02-01T00:00:00Z|searched_complete|800d572c…`.
* **H2** (both January–February) → `ledger_digest = b43e3157f320d15b19074b21d35bdd0546cc4901087632eb313faed1421d82a6` (v0.7; `62c4224e…` withdrawn)
  (full rows in `am5_cases_output.txt`).
* Under v0.3 the two histories were one row (same relations, counts, interval
  union); here they differ. Serving a January–February query with zero windows:
  H1 → `partial` (A uncovered `[02-01,03-01)`, B uncovered `[01-01,02-01)`), the
  seal returns two `obligation_uncovered` rows and **refuses**; H2 → `searched`
  → "searched, none admitted", seal accepted. (Earlier, input-less digests
  `b4e36531…`/`329b0639…`/`40663c77…` described only parts of the preimage and
  are withdrawn.)

**Worked example W2 — Codex's W2 row set, replayed exactly** is **C1** above:
every stored obligation is covered, the partition and recomputed digest agree,
no consumer exists — and the seal is refused by `committed_set_mismatch`,
because P5a's committed ids (`b817eebc-…`, `cfd4db84-…`) have no stored
obligation. Separately tested (as v1.3 requires): absent pin = C2; pin present
with obligations absent = C1; obligations present with intervals absent = C4;
genuinely empty qualified set = C5 (and its false twin C3).

**Worked example W3 — receipt-only complete-empty transaction.**
```
BEGIN (READ COMMITTED);
SELECT ka_gochara_lock_chart('482012f1-…');           -- chart EXCLUSIVE first
SELECT ka_gochara_lock_global_shared();                -- then global SHARED, before any rule-seal read
INSERT snapshot (manifest vector must match) → inventory → pins (with committed ids)
       → obligations (each in its pin's commitment; require_sealed_rule_path) → intervals;
INSERT verification rows (independent verifier, same chart lock);
UPSERT kala_gochara_coverage (event_class, <class>);   -- chart key already held
UPDATE kala_gochara_publication SET status='published';
SELECT ka_gochara_seal_generation(chart, '5.0');       -- seal trigger: first-publication branch
COMMIT;
```
No record or window is written; the seal records a ledger-proved,
input-bound complete-empty class, or refuses.

**Check against the applied guards.** *1155 record guard:* partition shape
unchanged (`event_class`, `partition_key=<class>`, finite horizon,
`coverage_facts` = current facts, relation ∈ `relations_searched`, bridged
convention, `t_in` ∈ horizon — 1155:696–748); the inventory only tightens what
may be put in the partition. *1156 drift:* `ka_gochara_coverage_drift`
(1156:499–546) still classifies records/windows and keeps its `extended`
allowance; the seal check adds what it cannot see (an unsearched or
never-inserted obligation with no consumer). *1153 seal:* the applied guard and
`ka_gochara_seal_generation` are untouched; the trigger is additive and, via
the replay branch, cannot break the function's `ON CONFLICT DO NOTHING` replay.
Nothing in 1153–1157 is edited.

**Schema impact:** ONE new additive migration — six tables, 17 functions (identity/digest
helpers, the write guard, the two violation functions, the seal-trigger function) and one trigger
on an existing table. It touches no live CHECK but **does** need the protected schema-capability
route (no `CREATE` on `public` for the ordinary role: `deploy.yml:953–962`,
`jataka-schema-capability.ts:54–67`); exact wiring is F-1.

**Review-driven corrections (v0.7, Codex review of migration 1206, R1–R5).** (R1) commitment equality is exact per
the FULL key chart/generation/class/**path/version** — another path's or version's obligations never satisfy a pin;
(R2) the snapshot's sky convention is bound to the publication's AND every claimed event_class partition's legacy
convention through the immutable bridge (`convention_bridge_missing` / `convention_mismatch`); (R3) an excluded
pin needs a non-NULL reason, CHECKs are total booleans; (R4) live-input digests pin TimeZone/extra_float_digits,
exclude the ACTUAL audit column `computed_at`, key rows by chart, and read dasha ids as `uuid[]`; (R5) CI requires
the live suite and runs a reproducible mutation harness; builder and seal principals are tested separately —
**sealing needs a separately authorised principal** (1216 withholds INSERT on the seal table; not widened).
Stricter than stated earlier: the seal requires EVERY verification row of a class to equal the stored digest (a stale
disagreeing row vetoes sealing until a candidate deletes it). A class absent from both coverage and inventory is not a
violation — serving must report it `not_searched`.

**v0.8 — steward M20261001T224443-bfc4 (R6 + version scope; migration 1206 v1.2 in place, still applied nowhere).**
(R6, **function EXECUTE**) In production every function `amjis_app` creates has PUBLIC EXECUTE revoked by default
(`platform/scripts/nirmana-evidence-ownership-preflight.ts:259`), and verified read-only the builder can execute **none**
of the 42 `ka_gochara_*` functions of 1153–1157. A table grant alone therefore leaves every guard uncallable. 1206 §7 now
grants `data_plane_builder` **explicit EXECUTE on exactly 17 functions** — its own 12 helpers plus the 5 contract
functions its guards call (`lock_chart`, `lock_global_shared`, `generation_is_sealed`, `generation_governed`,
`horizon_finite_ok`; repeated from the separate 1220 so 1206 is correct in either landing order) — and **not** the
seal-side functions or the two trigger functions (a trigger function needs no EXECUTE to fire). The set was derived by
running the builder's construct-and-finalise flow under a role mirror (objects owned by a role named `amjis_app`, PUBLIC
revoked) and adding one EXECUTE per `permission denied for function X` until it converged, then **re-proved in the live
suite: each of the 17 is individually necessary** (revoke any one → the flow fails naming that function). The sealing
principal's 20 EXECUTE grants are not in any migration (D-FLIP is the native's to authorise); they are the suite's
`SEALER_FUNCTIONS`, and every seal in the suite now runs as that principal. The builder's refusal at the seal is now
two walls — no EXECUTE on `ka_gochara_seal_generation`, and no INSERT on the seal table.
(**Version scope**, F-3) per class and path **at most one version is `included`**; every other version is `excluded`.
New non-degrading closed reason **`superseded_by_version`** (no `ruling_ref`, basis required) and two seal checks:
**`multiple_included_versions`** (two included versions of one path in one class — a double-count) and
**`superseded_without_included_version`** (a supersession claim whose superseder is not included — a coverage hole
wearing a non-degrading reason; added because a reason without a detector is a null, CLAUDE.md §N.8). The reason sits
inside the verified inventory preimage already (the `exclusion_reason` field), so no vector changes.

**Implementation record (F-1) — migration `1206_gochara_search_inventory_completeness.sql`,
HOLD, same protected window as 1204.** Written as new files only (1153–1157 untouched; a live-DB
test fingerprints every pre-existing `ka_gochara*` function, constraint and trigger before/after
and asserts none changed). Deviations from this draft's earlier wording, now folded above and
disclosed in the migration header: (1) the header's finalisation UPDATE (above); (2) every
timestamp in a digest preimage is whole-second UTC `…Z` and sub-second bounds are refused by CHECK
(the preimage would otherwise collide); (3) canonical JSON = sorted keys (codepoint order), no
spaces, UTF-8 not escaped; (4) `path_id`/`rule_version` appear **lowercased** in preimages and
obligation bytes while the pin keeps the registry's own case for its FK; (5) the migration grants
`data_plane_builder` SELECT on `ka_gochara_generation_seal` and `ka_gochara_av_polarity_declaration`
(1216 deferred both; the new guards read them as the invoking role); (6) the replay branch's
`manifest_id` equality check is defence in depth — the applied 1153 guard refuses a different
manifest first, so it is not independently reachable. Evidence: a 20-case live suite on a
disposable PG 17 runs the adversarial matrix as real INSERT/finalise/seal attempts (C1–C16, M1–M6,
the full seal lifecycle) and reproduces the Python-model vectors byte-for-byte; **18 mutations of
the migration (each guard neutered in turn) are each caught by at least one test**.

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

## AM-10 — §4.0 daśā read contract: re-pin on L1 rebuild (steward queue M20261001T201026-9988) — NEW

**Why.** §4.0 pins every daśā read for chart 482012f1 to
`(ayanamsha_id = lahiri_chitrapaksha, system_id = vimshottari, tier =
two_pass_verified, build_id = 1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb)`. The pin is
carried as `DASHA_READ_CONTRACT` (`services/gochara_rules/permission.py:27–34`),
enforced by `select_dasha_read_contract`, which now has **ONE implementation** in
`services/gochara_kernel/dasha_read.py` (`scripts/kala_gochara_cutover/step06a_class_context.py`
delegates to it; the earlier `step06a_class_context.py:225–260` body is superseded): for the
canonical chart, a build set that does not contain the pinned id raises `DashaReadConflict` —
"a wrong sole build is never accepted"; asserted by
`test_canonical_chart_refuses_a_wrong_sole_build_and_null_builds`), and
literal-checked by the reference rows of §4.0 (MD/AD/PD row ids and
timestamps; `permission.py` `MD_ROWS`/`AD_ROWS`/`PD_ROWS`; O-PP-1/2/3). Suvarṇa's
L1 rebuild on the corrected ephemeris backend will mint a **new** daśā build
(steward-reported, to be re-measured as evidence at re-pin: Vimśottarī period
starts shift by +6,993 s ≈ 1 h 56 m 33 s; zero class flips; the seven FORENSIC
anchors hold). Baseline (read-only, 2026-10-01): the canonical chart has exactly
one Vimśottarī build at `two_pass_verified` — 63 / 515 / 4,576 / 40,510 rows at
levels 1–4, spanning 1950-01-01 → 2100-12-31 (a measurement, not a contract
value; the predicate that produced it is in the evidence list below).

**Proposed spec text (amend §4.0; effective only on the steward's declaration
that the L1 rebuild has landed — until then the v1.4 pin governs unchanged):**

> **The pin is amended by evidence, never loosened. Rules for every future L1
> rebuild of a pinned read:**
>
> 1. **One pin, no auto-follow.** Exactly one `build_id` is pinned per
>    `(chart, ayanāṃśa, system)`. A newer build — however verified — is
>    **refused** until a re-pin lands; the contract never resolves "latest",
>    "any `two_pass_verified` build", a range or an allow-list (CLAUDE.md §N.7
>    item 2: no category-only selection). The old id is **refused** after the
>    re-pin — it is not kept as an alternate.
> 2. **Re-pin only by evidence, in one small PR.** The PR changes the pinned id
>    and nothing else of substance, and carries read-only evidence: (a) the new
>    build id and its `two_pass_verified` tier; (b) period row counts per level
>    against the old build (a count difference needs an explanation); (c)
>    parent-linkage integrity and zero duplicate/conflict rows under the §4.0
>    duplicate rules; (d) the **measured boundary shift** per level (min / max /
>    mean seconds, old vs new, matched by (level, parent, index)); (e) the seven
>    FORENSIC anchors re-checked against the new build; (f) for every instant
>    the contract is exercised by the oracles (the three worked-event instants
>    and every O-PP-1/2/3 instant) the PD/AD/MD lords under old vs new — **any
>    class flip, lord flip or anchor failure is a stop**, not a re-pin: report
>    and park (CLAUDE.md §N.5: a disagreement is a halt-worthy finding, never a
>    stored divergence); (g) a test that the **old id is refused**
>    (`DashaReadConflict`) and the new id accepted.
> 3. **Literal reference data moves with the pin.** The §4.0 reference rows are
>    `[L]` constants keyed to the old build. In the same PR they are re-measured
>    from the new build into the v1.5 successor files (the frozen v1.4 spec and
>    oracles stay untouched as history), each row id printed in full; a literal
>    that cannot be re-measured is marked `[EXTERNAL_COMPUTATION_REQUIRED]`
>    (B.10), never carried over.
> 4. **No silent absorption.** A re-pin changes `dasha_digest` and therefore the
>    AM-5 `input_digest` of any generation built under it: an L1 rebuild can
>    never be folded into an existing candidate or sealed generation; sealed
>    generations keep verifying against the build recorded in their own search-
>    input snapshot, not against the current pin.
> 5. **Ordering is fail-closed and must be scheduled.** While the pinned build
>    is absent from `chart_dashas` the contract refuses every canonical-chart
>    read (correct behaviour). Therefore the re-pin PR must be merge-ready
>    **before** the L1 rebuild lands, or the old build's rows must be retained
>    until it merges; the steward schedules both in one window.
> 6. **Scope.** Rules 1–4 apply identically to every other L1 read pinned by id
>    in the contract (the AV extract's build/convention key of AM-7, the sky
>    convention of AM-1, the node convention). Non-canonical charts keep
>    `select_dasha_read_contract`'s existing single-build rule; AM-10 does not
>    change it.

**Read-only evidence predicates for the re-pin PR** (publish predicates, not
numbers — DVA Ruling 16): `SELECT build_id, verification_pass_status, level_n,
count(*), min(start_iso), max(end_iso) FROM chart_dashas WHERE chart_id =
'482012f1-710e-4a25-994a-93821f5871aa' AND system_id = 'vimshottari' GROUP BY 1,2,3`
(counts and spans per build); and, for shift, the self-join of old/new rows on
`(level_n, parent match, ordinal within parent)` reporting `min/max/avg(new.start_iso
- old.start_iso)`; run through `pgenv.sh` read-only.

**Schema impact:** none. **Code impact (later, one PR):** the pinned id in
`permission.py` (`DASHA_READ_CONTRACT`) and the reference rows; the test that the old id is refused
against the single kernel implementation (`services/gochara_kernel/dasha_read.py`).

---

## AM-11 — Implementation pins for the P1/P2/P3/P6 prerequisite evaluation + the P1 obligation-agent token (steward M20261001T204900-21ac) — NEW

Source: `PREREQUISITE_EVALUATION_ANSWER_v1_0.md` (adopted by the steward). Frozen v1.4 is **silent**
on the five points below; each is marked as Stream B's recommendation, now pinned as an
**implementation pin for the A5.5 gate** (not a v1.4 edit). General rule restated: every declared
prerequisite is **evaluated, never hard-coded and never left `NULL`** where it is decidable
(F5, 1155:822–832: `NULL` ≡ unknown; "unevaluated" is not "unknown"; CLAUDE.md §N.8).

> **Pin (a) — `natal_bhava_relationship` (P1 #2), testimony kind.** A relation of a *testimony* kind
> (node-dispositor under D-PADMIT; non-node dispositorship and association — no clause in
> PG249:C1/PG250:C1) stores prerequisite result **`true`** and the record's
> `operator_role = 'testimony'`. Role, not result, is what stops it admitting (§0, S:56–62). A scored
> kind (occupancy, ownership of a signature house) stores `true` with `operator_role='scored'`;
> `relation = none` stores `false`; H unknown, or the lord's natal position unreadable, stores
> `unknown`. Evaluated from L1 natal positions + sign lordship + the class H table
> (`permission.period_lord_relation` is the reference logic).
>
> **Pin (b) — natal-fact P1 rows are not admission-bearing.** P1's natal-fact records
> (`contact_id IS NULL`: occupancy/ownership/dispositorship of the period lord) have no transit
> contact, F5 still demands every declared prerequisite, and 1155 has no "not applicable". They are
> therefore **not materialised as admission-bearing records**: prerequisite (2) is carried as the
> *evaluated predicate on the transit record*, the relation recorded in its `source_fact_ids`. If a
> natal-fact row is retained as a testimony annotation, its `transit_relation` result is `unknown`.
> `transit_relation` on a transit record is a **read-back of its own contact row** (true by
> construction — contact ownership/coverage guards 1155:717–747 — but computed, not asserted).
>
> **Pin (c) — `house_from_moon` (P2) polarity.** The predicate tests **h ∈ the agent's cited
> favourable ∪ adverse house set** (Phaladīpikā XXVI.1–8; adverse 12/8/1 for Saturn/Sun/Mars/Jupiter,
> D-RQ5). Polarity (the D-RQ5 evidence channel, §3.1) is a **valence** step, not admission. The
> operand is renamed **`p2:cited_house_set`** (it was `p2:adverse_house_set`,
> `rule_registry.py:164`). A predicate change is a **new `rule_version` row**, never an edit (1154 /
> §2.1 amendment 1): if `(house_from_moon, '1.0.0')` has been bound anywhere, bump the version.
> Nodes without an independently sourced set (AM-9, Ketu-12) → `unknown`; a relative's event cannot
> carry a Moon-frame record (`kgrr_relative_frame_ck`).
>
> **Pin (d) — `admitted_window_exists` (P6) is a read-back.** Evaluated against the parent admitted
> window of the same chart/generation (1156, sealed generation), not asserted from the emission path.
> P6 remains outside this batch (AM-8 / AM-4 defer parent-context and containment); the
> `B6-F17` sentinel stays until that design lands.
>
> **Pin (e) — the obligation `agent` for P1's period-role agent is the ROLE token
> `period_lord:md|ad|pd`** (grammar `period_lord:(md|ad|pd)`); every other path's obligation agent is
> a concrete graha. (Settles the F-3 sub-point; Stream A may keep "concrete graha + role alongside"
> on **records**, which store a concrete graha, but the **inventory** uses the role token.) Reasons:
> (1) *completeness* — an obligation must be coverable over the whole horizon (AM-5 §4); a
> concrete-graha period obligation is only *applicable* while that graha runs in that role and the
> ledger has no "not applicable" state, whereas the Vimśottarī rows partition the horizon, so a role
> token is fully coverable; (2) *stability* — the inventory and its digest must not move with an L1
> daśā rebuild's boundary shift (AM-10): only `dasha_digest`/`input_digest` do; (3) the registry's
> agent vocabulary stays concrete (a selector vocabulary, not an inventory unit). **Resolution:**
> each `searched_*` interval of a role-token obligation is cut at the pinned dasha rows' boundaries
> (half-open, §4.0) and carries `detail = {"resolved_agent": "<graha>", "dasha_row_id": "<uuid>"}`;
> records emitted from it carry the concrete graha as `agent`. The independent verifier re-derives the
> cut points and resolved agents from the snapshot's `consumed_dasha_row_ids` (an O-RP-9 extension);
> **SQL does not check the resolution — a named residual** like the inventory's doctrinal correctness.
> Migration 1206 already admits any non-blank agent token; **no schema change.**

**Schema impact:** none. **Owner:** A implements the evaluations; B supplies the reference logic and
the O-RP-9 extension; both are A5.5-gate items.

---

## AM-12 — CANDIDATE (not yet a pin): carry `sad_bala_sufficient` as a P1 soft factor — NEW (v0.8)

**Status: proposal for the A5.5 gate; no code or registry change made.** Stream B's F-4 landed the factor
`sad_bala_sufficient` v1.0 (Phaladīpikā IV.22–23, corroborated by BPHS ch.27 śl.32–33) with a typed rūpa operand and
`null_state='unqualified'`, but **no rule path lists it as a soft factor** — it exists in the catalogue and in the
evaluator and nothing consumes it. Doing so is a *new P1 `rule_version`* (a sealed version is never edited): P1@next
adds the factor to its soft-factor set; per AM-5 the older P1 version then becomes `superseded_by_version` in each
class inventory (the new reason above) — which is exactly the case that reason exists for. Because the factor
orders admitted windows and never admits (1155:822–832), adopting it cannot change which windows exist, only their
order. Open for the native/A5.5 gate: whether P1 alone, or also the other graha-keyed paths, carry it; and the
**L1 data finding** referred earlier (chart_facts Sun total/required rupa 5.0 contradicts Phaladīpikā IV.22 and
BPHS ch.27 śl.32–33 = 6.5; six others agree) must be resolved by the L1 owner BEFORE any serving use, since the factor
reads that fact.

---

## AM-13 — RULED (steward M20261002T001617-8321): factor applicability by object kind; `activity_kernel@1.1`; `graduated_drishti` scope

**Defect in the frozen text.** §2.1 says a missing factor operand takes its `null_state` ("never silently 1"). The registry
declares `activity_kernel` (operand: angular |Δλ| to a point; **no orb parameter**) on P3/P4/P5, although their contacts include
**span residence and aspect-on-span** records that have no |Δλ|; P2 — pure span residence — declares no kernel at all. Read literally,
every P3/P4/P5 span record is `unqualified`.

**Rule (ruled).** A versioned factor row **`activity_kernel@1.1`** declares **applicability by object kind**, in its
`operand_selector` (JSONB; `ka_gochara_named_operands_ok` already admits a token-array value, so **no schema change**):
* **objects with EXTENT** (`sign_span`, `house_span`, and **`star:<n>` — a 13°20′ nakṣatra span**): a **membership step — 1.0 inside, 0.0 outside**,
  `unitless`, `uncalibrated_default` (such a target has no centre or orb in any cited source; an angular gradient would be an invented effect, §N.7 item 6);
* **true POINT objects** (`degree_point`, `derived_point`, `saham`, `house_lord` — a longitude): the angular kernel `1 − |Δλ|/orb` (§7.2 inv 3), with the **orb a row parameter**.
* Classification is by **geometry, not name** (steward M20261002T002620-6575); `varga_position` is not classified (unqualified).

`graduated_drishti` is declared applicable to **aspect records only** (offset operand); residence/conjunction records have no offset —
"not applicable" is a declared state of the row, not a missing operand and not a silent 1. New P3/P4/P5 rule_versions reference the
new factor versions. **Supersession (Codex R5 text, replaces the earlier blanket sentence):** an older version is `superseded_by_version`
**only when another version of that path is `included` for the same class**. Where no successor is included, the independently derived
computed-empty or exclusion disposition and basis are retained — otherwise unknown-H or empty classes would hit 1206's intentional
`superseded_without_included_version` refusal.

**ORB — what is and is not ratified (line cites).** The spec ratifies the **shape**, not a number: §7.2 inv 3 (`activity = 1 − |Δλ|/orb`,
D-RQ2) and `GOCHARA_PLAN_V3_AMENDMENT_v1_0.md:32` (M-1: "linear-no-box shape ruled; … **5.0° candidate 1 / 1.0° candidate 2**" — candidates).
Other numbers exist but none is a ratified activity-kernel orb: `services/gochara_kernel/convention.py:80–93` (WP1 §7 `ORB_TABLE`, e.g.
`orb_conj_slow` 1.0°, `orb_conj_moon` 3.0°) — its own header marks every numeric orb `uncited_extension=true` and it governs **contact
enumeration** (episodes emitted at `orb_max_deg`), not the kernel's scale; O-RP-3 "the pinned 5° admission orb" is an **oracle fixture pin**
for P4 admission; the 4.x manifest vector records `orb_ruling: "M-1 fallback no-box × 5.0° (unratified)"`. **Therefore the point-kernel orb
is a named NATIVE DECISION (ND-ORB, open) and until it is made the point branch stays `unqualified` with reason `orb_not_ratified` —
the unratified 5.0° is not carried forward.** The extent branch needs no orb and is unaffected. Decision packet: `decisions/ND_ORB_DECISION_PACKET_v1_1.md` (v1.0 is superseded). It is **two native decisions**, ND-ORB-ADMISSION (the angular criterion that admits/enumerates contact support) and ND-ORB-SCALE (the scale that ranks an already-admitted contact); whether one ruling governs both must be stated by the ruling. A ranking-scale change alone never changes the admitted-day union.

**Vehicle.** The catalogue is persisted at run time by Stream A's `rule_binding` step from `services/gochara_rules/registry.py`
(insert-if-absent) — no DDL. **Version-aware binding (Codex R5; the 1.1.0 rows are not bound until this is done):** the binder selects explicit
composite path/factor references, preserves **each prerequisite's own version**, **encodes the applicability declaration losslessly into
the existing typed `operand_selector`**, reads it back and compares it, and evaluators are dispatched by the **exact soft-factor membership
reference** (a 1.1.0 path never receives a 1.0.0 evaluation or label). It must **not** be solved by a global `RULE_VERSION` bump, which would
disturb unchanged paths and predicates.

**Flat encoding contract** (1154:221–240 admits only a FLAT object of selector tokens, numbers and token arrays; no nested object, no
boolean, no JSON null). `services/gochara_rules/flat_selector.py` is the codec; the persisted declaration carries the branch selection
(`span_kinds` / `point_kinds`), the relation applicability (`applicable_relations`), the step values (`span_inside`, `span_outside`),
the angular form (`point_form`), the **explicit unratified state** (`orb_state = unratified_nd_orb_open`), and — **only when ratified** — the
numeric `orb_deg` and a token `orb_decision_ref`. **An unavailable numeric orb is OMITTED, never inserted as null.** The top-level numeric form is
`piecewise_step_linear` (step on extents, `1 − |Δλ|/orb` on points), not `linear`. The regexes are cross-checked against migration 1154
in CI; `encode(decode(flat)) == flat` is tested.

**Geometry and orb validation (Codex R4 closing text).**
> Before factor evaluation, resolve the record's physical object and validate its canonical target against its object kind. `span:1`–`span:12`
> and `star:1`–`star:27` are extents; the declared point kinds require `point:<longitude>`. Mismatches fail validation. `varga_position`
> remains explicitly unqualified. Membership comes from the validated contact geometry, not an unchecked caller flag.

For aspects, membership and distance use the **directed aspect ray** with seam-safe angular distance; the inclusive offset convention is
preserved; N-14 forbids node-cast aspect records; persisted lowercase graha tokens pass a closed, tested adapter to the helper vocabulary.
The angular branch requires a **finite, strictly positive, ratified** orb bound to a decision reference and to the matching immutable factor
version; **invalid configuration (0, negative, NaN, ±Infinity, status/decision mismatch) fails closed — it never scores.** A declared membership
step supplies a known unitless factor of 1 inside support (NK-4); its 0 outside support is **not** a second admission filter.

**Qualification propagation (Codex R1 closing text; implemented in `score.py`, PR #2905).**
> An unresolved applicable factor propagates score qualification. An affected evidence channel is NULL unless its value is established
> independently under an explicitly specified reduction rule. Known partial subtotals may be reported separately, but never as complete
> evidence. Admission and admitted support remain unchanged.

**Attribution.** The special-aspect `1.0` values rest on the frozen oracle **O-CF-DRISHTI**; the served Brihat Jātaka passage corroborates the
ordinary ¼/½/¾/full graduation but does not itself numerically establish Jupiter's and Saturn's specials.

---

## AM-14 — RULED, **REWRITTEN per Codex round 6 R2** (the earlier "Moon-agent obligations are excluded; 1206 needs no change" text is withdrawn)

AM-4 forbids storing Moon contacts/records in a generation. A literal removal of obligations whose `agent` equals `moon` does **not** settle
the stable `period_lord:md|ad|pd` obligations of AM-11, which cover the whole horizon and **resolve to the Moon during Moon periods**: Stream A's
inventory assigns `missing_inputs` there (`gochara_kernel/inventory.py:268–275`, reproduced by `inventory_verifier.py:357–359`) and 1206:880–898
refuses every `missing_inputs` interval and every uncovered obligation. Removing the Moon-resolved intervals leaves coverage gaps; relabelling an
unperformed search as complete would defeat the accepted contract.

**Closing contract (Codex).**
> Moon exclusion applies to the **resolved concrete transiting agent, including period-role agents.** Each period-role obligation has a
> **snapshot-bound applicable time domain.** Moon-resolved portions are explicitly accounted for as **excluded from the stored tier**; they are
> neither missing search intervals nor completed geometry searches. **Completeness requires coverage of the applicable domain and verified
> accounting of its excluded complement.**

* **Domain.** For a period-role obligation the applicable domain = the class horizon minus the union of the consumed daśā rows (the snapshot's
  `dasha_digest` binds them) at that role's level whose resolved lord is the Moon. Excluded complement = that union ∩ horizon. Both derivations
  (the writer's and the independent verifier's) compute it from the snapshot's own rows; the seal recomputes it and **refuses any mismatch**
  (missing exclusion, extra exclusion, an excluded portion that is also claimed as searched).
* **Not removed:** the Moon as a **natal target**; **Moon-frame evaluation by other agents**; **Sun/Jupiter delivery during a Moon bhukti.** Exclusion follows the **transiting agent** only.
* **Machine-readable scope** (e.g. `stored_non_moon`) is **bound to the manifest** and **returned by the mandatory coverage constructor**; a missing scope
  **prevents an unqualified "complete" answer**. Tested on positive and no-window responses, before and after an on-demand query.
* **Storage/checks.** The accepted 1206 remains correct for its contract (ordinary concrete-agent exclusion) and **must not be weakened**
  (`missing_inputs_present` and `obligation_uncovered` stay as they are for the applicable domain). The additional domain/complement accounting is a
  **new additive migration, 1232 (HOLD, protected window after 1206)** — see `migrations/1232_…` on the stacked branch of #2867; a real database test
  uses a **Moon-resolved daśā interval** (not an already non-Moon fixture).
* **Withdrawn claim:** "1206 needs no change" is established only for ordinary concrete-agent exclusion, **not** for the complete AM-14.

---

## AM-15 — RULED: P1 daśā-lord house anchor
The natal relation of the period lord to the class's signature-house set H is counted **inclusive from the lagna** (§0 inclusive counting;
P3 table is "lagna frame"). Previously silent beyond "natal sign positions".

## AM-20 — RULED: reference sign for P1 transit records' `house_from_frame` = the LAGNA
S §0 never defines the `dasha_lord` frame's reference sign; §2.2 P1 says only "Frame: `dasha_lord` / natal sign positions"; no oracle exercises it; `ka_gochara_frame_ok` forbids `dasha_lord` carrying an argument. The served text counts the daśā lord's transit **from the Lagna** (Phaladīpikā XX.34, `phaladeepika:PG249:C1`: "the Bhava it represents when counted from the Lagna"; XX.59, `PG256:C1`) and never from the lord's own natal sign (`design/P1_FRAME_ANSWER_v1_0.md` v1.2). **Ruled text:** *`house_from_frame` of a P1 transit record is the inclusive count from the **lagna** (consistent with AM-15 and the P3 frame). It is a stored descriptor: no P1 predicate, factor, admission test or channel assignment reads it, and the verifier tests that changing it cannot alter any of them. The period lord and level that license the record are carried by the typed anchor of AM-21 part 2 (migration 1233), not by the frame.* Native confirmation: **ND-P1-FRAME** (a label convention; nothing waits on it). Named limitation: XX.37's "or be retrograde, the effects will be good" has no factor in the P1 inventory; adopting it would change which readings exist and therefore needs an explicit admission amendment, not only a score factor.

## AM-21 — RULED TEXT (steward M20261002T032818-fea8, Codex round 8 R8-3): P1 support = contact ∩ the running-period domains of the ANCHORING lord and role — supersedes occurrence-instant admission
**Operative text (Codex's exact sentence, adopted):**
> **P1 transit admitted support is the contact support, clipped to the requested horizon, intersected with the applicable running-period domains of the lord and role anchoring that rule instance and with its other necessary prerequisites. This supersedes occurrence-instant-only admission. Disjoint licensed pieces remain disjoint. Unknown prerequisites do not become admitted support. For Sun/Jupiter delivery, the anchor is the relevant bhukti lord; Moon-tier exclusion follows the transiting body.**

AM-17's general "after prerequisites" wording does not clearly supersede the earlier occurrence-instant reading; this amendment does, for P1. "Moon-tier exclusion follows the transiting body" (AM-14): a **Moon bhukti anchoring a Sun/Jupiter delivery does not exclude that delivery** (the transiting body is the Sun or Jupiter, a stored agent); a Moon **agent** (own-transit reading with the Moon as period lord) is the AM-14 `excluded_moon_tier` accounting.

**What is replaced.** AM-11 pinned how P1's three prerequisites are *evaluated* but, like the writer (`record_store.py:1294–1302`), judged `period_running_at` **once, at the contact's occurrence instant**. That can **admit support through a period gap** (a positive test at ingress) or **discard a valid later portion** (a negative test at ingress, or an ingress before the horizon). Frozen S §4.2 is explicit that the licence is **a function of t** (inv 1) and prunes **only through a path's necessary period prerequisite** (inv 4) — an instant-judged prerequisite does not do that. AM-11 pins (a)–(e) stand otherwise (natal relation and testimony roles, natal-fact rows, the `period_lord:md|ad|pd` obligation token).
**Rule.** For a P1 transit record whose agent is the period lord at level ℓ ∈ {md, ad, pd}, the **admitted support** is
`support(record) = contact_support ∩ D`, where `D` = the union of the **half-open `[start_iso, end_iso)` running intervals** (§4.0) of the pinned `chart_dashas` rows at level ℓ whose lord is that agent, with `licence = scored` for the natal relation (prerequisite 2; AM-15's lagna count). Consequences, all required:
1. **Multiple disjoint pieces are retained** as separate intervals of the one record's `temporal_support`; they are **never merged into a hull** across a gap.
2. A period beginning or ending **inside** a contact clips the support at the row boundary (half-open; the boundary instant belongs to the later period).
3. The contact's **ingress before the horizon** neither admits nor discards anything: the clipped-to-horizon support is intersected with `D`.
4. **Retrograde re-crossings** (several residence spans of one contact) are intersected **independently**, each against `D`.
5. `period_running_at` is stored as a **function of t**: `true` on the pieces, `false` where the level lord is not running (those parts are **not admitted** — excluded by a failed necessary predicate, the only exclusion §2.3 inv 7 allows), `unknown` only where the pinned rows do not cover a part of the support (that part is `unqualified`, never dropped; R1).
6. The **independent verifier derives `D` from the pinned dasha rows (§4.0 read contract) itself** and compares it with the stored pieces; it does **not** union the builder's stored supports. Moon-tier exclusion follows the **transiting body** (AM-14): a Moon-resolved portion of a Moon-agent reading is the `excluded_moon_tier` accounting, not a P1 period test; a Moon bhukti anchoring a Sun/Jupiter delivery excludes nothing.
**Oracle (new, literal — O-PP-4, Stream B; rows from the §4.0 pinned build, printed in O-PP-2):** PD **Saturn** rows `a4cf46db-fcb5-479c-8aab-ca87bcb551ff` = [2019-06-21T00:55:52Z, 2019-08-17T09:18:53Z) under the Mars AD and `73eea5c0-631f-4b48-8c8f-483c910c6fde` = [2020-11-04T09:13:29Z, 2021-03-31T20:29:50Z) under the Rāhu AD (**verified read-only 2026-10-02: with the §4.0 pins — system vimshottari, lahiri_chitrapaksha, build `1f89fd4c…`, tier `two_pass_verified`, level 3, lord Saturn — exactly these two rows overlap [2019-05-01, 2021-06-01)**). Synthetic Saturn contact fixtures (`fixture = true`): **(a)** one residence span [2019-05-01, 2021-06-01) ⇒ exactly **two pieces** [2019-06-21T00:55:52Z, 2019-08-17T09:18:53Z) and [2020-11-04T09:13:29Z, 2021-03-31T20:29:50Z), not a hull; **(b)** a span [2019-08-01, 2019-12-01) beginning inside the first PD and ending in the gap ⇒ [2019-08-01, 2019-08-17T09:18:53Z); **(c)** ingress before the horizon: span [2019-05-01, 2019-08-01) with horizon start 2019-07-01 ⇒ [2019-07-01, 2019-08-01); **(d)** re-crossings S1 = [2019-06-01, 2019-07-15), S2 = [2019-08-01, 2019-09-15) ⇒ S1 → [2019-06-21T00:55:52Z, 2019-07-15) and S2 → [2019-08-01, 2019-08-17T09:18:53Z) (two records' pieces, never one). **Mutations that must fail:** judging the period at the occurrence instant (fails b, c); a closed upper bound (boundary instant); a hull across the gap (fails a); an unclipped horizon (fails c); the verifier unioning the builder's pieces instead of deriving `D`.
**Owner:** Stream A implements; the verifier derivation is A's; B supplies the oracle. **Status:** RULED text (operative sentence above) with the part-2 rule below; implementation is Stream A's, the migration is 1233.

### AM-21 part 2 (steward M20261002T030818-1676): the period ANCHOR — which lord's periods, at which level — and record identity
**What the verses say (verbatim, `phaladeepika:PG249:C1` / `PG250:C1`).** XX.34: "a planet whose **Dasa** is in progress … passes through (in transit) his Swakshetra, exaltation or a friendly house" (level: **Dasa/MD**); XX.35: "a planet whose **Dasa** is in progress be weak, eclipsed …, in depression or inimical house **at birth**" (MD; natal conditions); XX.37: "the planet whose **Bhukti** is in progress … during the course of his transit pass through his depression or inimical house or become eclipsed … Should he pass through his own, or exaltation house or be retrograde" (level: **Bhukti/AD**); XX.38: "In the case of a planet whose **Bhukti** is auspicious, the good effect will be manifested when **the Sun enters the planet's exaltation sign**. The same effect will be felt when **Jupiter** transits the place. As regards the planet whose Bhukti is inauspicious …, the evil effects will be felt when **the Sun** in his transit passes through the **Bhukti lord's** depression or inimical sign." (level: **AD**). **The pratyantara (PD) level is not mentioned in any of XX.34–39**; S §2.2 P1's "running MD/AD/PD lords" is the specification's extension (flagged: PD-level P1 records have no verse).
**What the spec/registry say.** S §2.2 P1: "Frame: `dasha_lord`… running MD/AD/PD lord's own transit … Sun or Jupiter transiting the **bhukti lord's** exaltation sign delivers the bhukti's fruit". The registry row (`_path("P1", …)`) lists the agent set as the "running MD/AD/PD lords in their period role" and its object selector as "(period_lord, natal sign/house objects …)" — which does **not** describe the XX.37–38 *sign-quality* forms at all (they are a residence of an agent in a sign, judged by that sign's quality **for a named period lord**).
**Rule (both questions).**
1. **Anchor.** Every P1 record has a **period anchor = (anchor lord X′, level ℓ)**: the period lord whose running periods license it and whose sign-quality is judged. **Form XX.37 (own transit):** agent = X′ (the sign is judged for the agent itself), ℓ = AD (bhukti); **XX.34–35 (Dasa lord's own transit):** agent = X′, ℓ = MD; **XX.38 (Sun/Jupiter in the bhukti lord's sign):** agent = Sun or Jupiter, **X′ = the bhukti lord whose exaltation / depression / inimical sign is entered, ℓ = AD**. The spec's PD extension keeps ℓ = PD with agent = X′ and is **flagged**: no verse supports it.
2. **Domain.** The period restriction of AM-21 uses **D(X′, ℓ)** — the running intervals of the pinned level-ℓ rows whose lord is **X′** — **not the agent's** periods. For XX.37 the two coincide; for XX.38 they differ (the Sun's/Jupiter's own periods are irrelevant to that reading).
3. **One contact, several records.** Sun in Libra is the Sun's own debilitation sign (XX.37, anchor Sun) **and** Saturn's exaltation sign (XX.38, anchor Saturn): **two readings with different anchors, domains and directions — both must exist**; anchoring only on the agent's own reading silently drops the second. They are **role aliases of one physical contact** (S §1.2 inv 3): they **share one `contact_id`**, are never independent observations, and the evidence reduction takes the **per-root maximum within a channel** — a favourable and an adverse reading land in **different channels and are never netted** (§3.2 inv 1). Where several lords X′ have the entered sign as an *inimical* sign (XX.38's second branch) there is one record per X′.
4. **Identity needs the anchor — SCHEMA CHANGE (plainly).** The natural key (S §1.1: chart, generation, event_class, affected_person, **frame**, agent, relation, object_id, object_role, contact_id, path, rule_version, prerequisites, source_text) **cannot carry (X′, ℓ)** in its present columns: 1154's `ka_gochara_frame_ok` forces `dasha_lord` to carry **no** argument (and the classical frame is the lagna, AM-20); `object_id` must be the contacted physical object (the sign) so it cannot also name X′; `prerequisites` carry predicate versions, not lords; `source_text` is a citation (encoding a lord in it would be identity by prose). **Required: an additive migration — 1233, PR #2919 (HOLD)** — adding two nullable columns to `ka_gochara_relationship_record` — `period_anchor_lord` (nine graha tokens) and `period_anchor_level` (`md|ad|pd`) — with a CHECK that both are non-NULL exactly for `path_id = 'P1'` and NULL otherwise, both **added to the writer's natural-key hash and to the S §1.1 key list** (a version bump: the key changes), and the inventory obligation token stays `period_lord:md|ad|pd` (AM-11 pin e). It follows the 1232 pattern (new migration, never an edit of 1155; protected-window listing; surgical verification). **Stream A mints P1 records only against a database carrying 1233** and with the anchor in the writer's `record_id` hash; the first candidate's P1 search is either implemented with anchors or explicitly excluded by a separately governed exclusion — it is never silently absent while claimed complete (Codex R8-3).
**Oracle additions (O-PP-5, literal):** Sun in Libra over a Sun residence span that overlaps both a Saturn AD and a Sun AD of the pinned build ⇒ **two records**, same `contact_id`, anchors (Sun, AD) and (Saturn, AD), supports = span ∩ D(Sun, AD) and span ∩ D(Saturn, AD) respectively, directions adverse and favourable; mutation that must fail: one record anchored on the agent only; domains taken from the agent's periods for the XX.38 reading.


### AM-21 part 3 (steward M20261002T053914-0033 / T054631-b83c): the XX.38 delivery searches in the AM-5 inventory — no new migration
**Question.** P1 records are anchored (lord X′, level ℓ) and include the XX.38 forms (Sun/Jupiter transiting a sign of the bhukti lord X′ read under X′'s AD), but the AM-5 inventory keys P1 agents as the role tokens `period_lord:md|ad|pd` and had no obligation for those Sun/Jupiter searches. Can the existing 1206/1232 grammar carry them without a migration?
**Answer: YES — confirmed against the migration text and against a live database (migrations 1206 + 1232 as applied, PostgreSQL 15, real daśā Moon interval).**
**Encoding (exact).** For every P1 transit edge whose **agent is not its anchor lord** (the XX.38 forms) the planner emits one **concrete-agent obligation** in the existing qualified 9-tuple `(event_class, path, version, agent, relation, object_role, target, frame, person)` with:
`agent = sun | jupiter` (the concrete transiting body, lowercase) · `relation = residence` · `object_role = period_lord` (a **role token in the OBJECT-ROLE column**, not an agent token) · `target = span:n` (the edge's canonical target, per Stream A's planner statement) · `frame = dasha_lord` · `person` = the edge's affected person (the live fixtures use `self`); e.g. (fixture person token) `marriage|p1|1.0|sun|residence|period_lord|span:2|dasha_lord|self`. Its interval ledger covers the **whole class horizon** like every other obligation.
**Why no migration is needed (each point read from the file, not assumed).**
1. **1206 `ka_gochara_search_obligation`** constrains only: `canonical_bytes` equal to the lowercased `|`-joined 9-tuple (`kgso_bytes_ck`), arity exactly 9 and no newline (`kgso_bytes_shape_ck`), `agent`, `relation`, `object_role` non-blank (`kgso_core_nonblank_ck`), and `relation` ∈ {residence, aspect, conjunction, dispositorship, association, ownership, occupancy, period_running} (`kgso_relation_ck`). **There is no vocabulary check on `agent`, `object_role`, `target` or `frame`**: a concrete agent with `object_role = period_lord`, `target = span:n`, `frame = dasha_lord` and `relation = residence` is admitted. (The vocabulary is enforced by the **planner and the independent verifier**, which derive the same set from their own tables — a database CHECK cannot judge the *right* inventory; AM-5's standing limit.)
2. **1232's Moon-domain accounting keys on the AGENT token**: `ka_gochara_search_moon_resolved_domain` and both Moon-scope violation branches select only `agent ~ '^period_lord:(md|ad|pd)$'`; the **role** column is never consulted. A concrete `sun`/`jupiter` obligation therefore has an **empty** Moon-resolved domain and is **not** treated as Moon-resolved **even while a Moon bhukti is consumed** — matching AM-21's "Moon-tier exclusion follows the transiting body". It must be **searched over the whole horizon**; the Moon period does not excuse an unsearched portion (`obligation_uncovered`).
3. **It cannot be hidden as a Moon exclusion**: an `excluded_moon_tier` interval on it is refused by 1232's `moon_exclusion_on_non_period_obligation` (the Moon is never a stored concrete agent).
4. **Anchor-free by construction.** The 9-tuple, `ob_id` (UUIDv8 of the canonical bytes) and the ledger digest preimage carry **no anchor lord, no level and no domain** — and need none: the search the obligation describes (the body's sign contacts) is **whole-horizon**. The anchor and its AD domain restrict the **record's support** (AM-21 part 2), not the search; they are verified **at the record** by the independent verifier (`verify_p1_anchors`). Two anchors needing the same Sun/Jupiter search share **one** obligation (identical tuple ⇒ identical id), which is correct: it is one search.
**Boundary of the claim (plainly).** The inventory certifies that the **search was performed** over the whole horizon; it does **not** certify that every anchored record (every lord X′ whose sign is entered) was minted — that is the record-level verification, whose persistence is the verifier's (ND-ROLES / 1240 for windows). A mutation that drops an anchor at a record is caught by the record verifier, not by the inventory gate.
**Live evidence (Stream B, `tests/integration/gochara_b6_am14_moon_domain.db.test.ts`, +5 tests, 14 pass on PG15):** (a) `sun` and `jupiter` obligations with a consumed Moon period ⇒ domain `{}` and the generation SEALS on the whole-horizon search; (b) the Moon portion left unsearched ⇒ `obligation_uncovered`; (c) `excluded_moon_tier` on it ⇒ `moon_exclusion_on_non_period_obligation`; (d) the stored row's `canonical_bytes` is exactly the arity-9 anchor-free string.
**Mutations that must fail:** treating the role column `period_lord` as the Moon-domain key (would exclude Sun/Jupiter delivery during a Moon bhukti); putting the anchor lord or level into the tuple (two anchors ⇒ two obligations for one search; the preimage would then differ between planner and verifier); a P1 transit edge whose agent ≠ anchor lord with **no** concrete obligation (the delivery search would be unrecorded).
**Owner:** Stream A implemented the planner/verifier derivation (head `4221f3bc5`, brief v1.29); Stream B wrote this text and the live evidence. **Status:** RULED by confirmation — no migration; the XX.38 forms are **in** this milestone (no named switch is needed).

## AM-16 — RULED, **REWRITTEN per Codex round 6 R6**: the complete `'5.0'` fingerprint

**Closing text (Codex).**
> The input vector has a **versioned key schema and canonical serialization**. Its **registry digest** covers selected path, predicate and factor
> payloads, **ordered prerequisite memberships, soft-factor memberships, applicability declarations** and the **accounted sealed-version census**,
> excluding only enumerated audit fields. It binds consumed **L0/arc/node-series identities and content digests**, **both admission and
> activity-orb policies**, applicable rulings, and the **implementation identities** governing geometry, evaluation and window construction. Inputs
> already transitively bound by the snapshot need not be duplicated.

* **Why the earlier list was insufficient:** a `ka_gochara_rule_path_seal` row holds only path, version and timestamp — there is **no built-in "seal digest"
  of the rule graph**; path/predicate/factor rows alone commit neither prerequisite ordering nor soft-factor edges; `node_convention = "mean"` names a
  convention, not **which mean-node series or source revision** was consumed; and 1206:767–768 only compares manifest vector with snapshot vector — two
  identical stale or incomplete vectors pass.
* **Key schema (v1).** `vector_schema=<n>`; keys sorted by codepoint, canonical JSON (no spaces, UTF-8, whole-second UTC), each value a lowercase-hex sha256
  or a token: `registry_digest`, `registry_version_census`, `l0_identities` (per consumed L0 asset: asset id + content digest), `arc_series_digest`,
  `node_series_digest` (**content digest of the series itself, not a label**), `admission_orb_policy`, `scale_orb_policy`, `rulings` (sorted ids),
  `impl_geometry`, `impl_evaluation`, `impl_window` (implementation identities = source commit ids of the governing modules).
* **Registry digest preimage:** sorted lines of the canonical payload of every *selected* `(path, version)`, `(predicate, version)`, `(factor, version)` row
  (all columns except `created_at`), then the ordered prerequisite memberships `(path, version, ordinal, predicate, version)`, the soft-factor memberships,
  the applicability declarations (the flat `operand_selector`), and the census of **sealed versions** per path. Enumerated audit fields excluded: `created_at`.
* **Verification.** The writer and the independent derivation **recompute** these bindings from the inputs they actually consume and **refuse on mismatch**;
  changing any result-bearing component changes the input identity or raises a mismatch refusal. **Historical replay checks its original bound inputs; it
  does not recompute a fingerprint of today's catalogue.**
* **NORMATIVE key schema (reconciled with Stream A's implementation `input_vector.py` @`3677cccae`; v0.14).** The vector is a **nested object** (so a refusal names the component that
  moved) with `schema = "ka_gochara_input_vector/2"` (**bumped from /1 — v0.21, Codex R8-1; no build used /1**) and: `sky_convention {id, content_digest}`; `registry {digest, census}` (digest = sha256 of the canonical JSON of
  `{schema:"ka_gochara_registry_digest/1", paths, prerequisites, soft_factors, predicates, factors, census}` — full jsonb rows of the selected versions and the predicates/factors they reference,
  minus enumerated audit fields `created_at` (predicate/factor/path) and `sealed_at` (seal table, never selected), in a total order; ordinals preserved); `node {model, source, zodiac, ayanamsha}`;
  `ephemeris {backend, swe_version, library_sha256, platform, files, probe_digest}` where **`library_sha256` is the sha256 of the loaded swisseph artifact** (the compiled extension the import resolved to — a version string does not distinguish two builds) and **`platform` is `<system>-<machine>`** (floating-point behaviour is a function of the architecture/libm); `files` are **`files` are the `.se1` files the kernel actually opens for the consumed bodies over the consumed horizon, not every file present**
  (measured: Sun/Moon/Saturn/MEAN_NODE open `sepl_18` + `semo_18` and never `seas_18`; a file present but unopened must not move the identity, and an opened file absent is refused);
  `l0 {asset_id: sha256(canonical rows consumed)}` for every L0 table a path reads (AM-18: the `bg_transit_rules` vedha rows); `orb_policy {admission_digest, activity{row version: orb | state token, + orb_decision_ref once ratified}}`;
  `rulings_digest`; `implementation {geometry, evaluation, window}` = sha256 of the canonical `{module: sha256(source)}` over module lists that **must cover** the import closure of the writer from `services.gochara_kernel` + `services.gochara_rules`
  (a coverage test fails when a result-bearing module is missing from every list — `kernel_factor`, `flat_selector`, `vedha_derive`, `records`, `frames`, `permission`, `p6`, `ashtakavarga`, `nature` today). Canonical JSON: sorted keys, no spaces, UTF-8, no NaN.
  `stored_scope = "stored_non_moon"` is a top-level key (AM-14: the mandatory positive **and no-window** response constructors read it back from the bound manifest; a missing scope refuses an unqualified completeness claim). **Schema version.** The key set gained `ephemeris.library_sha256` and `ephemeris.platform`; the label is therefore bumped to **`/2`** — one label must name exactly one key set, a `/1` vector verified against `/2` code must be refused by the schema check rather than silently reported as drift in two new keys, and no build has used `/1` (so the bump costs nothing and the v1 frozen file is superseded by `am16_vectors_frozen_v2.json`). The registry-digest schema (`ka_gochara_registry_digest/1`) is unchanged. **Schema version /3 (steward M20261002T062742-971a, Codex round 9 R9-1).** One new **REQUIRED** key, `result_policy`, beside `stored_scope`: `'all_null_candidate/1'` | `'window_qualification/1'`, **selected by the manifest** and bound into the vector. The label is bumped to **`/3`** (one label names exactly one key set; a `/2` vector, which has no such key, is refused by the schema check rather than reported as a one-key drift; no build has used `/2`). The frozen literals are `design/am16_vectors_frozen_v3.json` (`/2` superseded; 17 entries incl. the new `result_policy_only` case), recomputed by `design/am16_vectors_model.py` v5 and **confirmed byte-identical to Stream A's `tests/l3/gochara/fixtures/am16_vectors_frozen_v3.json`** (all 17 literals and sha256s). **Binding sentence:** *the candidate gate refuses a window whose stored result contradicts the manifest's `result_policy`* (under `all_null_candidate/1`, any non-NULL numerical result field; under `window_qualification/1`, a NULL one the policy requires) — a stored result is only readable under the policy its generation was built under. **Consumed arc/node-series binding (Codex round 7 [9], R8-1).** The kernel does not store the series; it computes it with pyswisseph, so the series is a pure function of (the loaded **artifact** — code, the opened **file contents** — data, the flags/sidereal mode — convention, the instants — inputs), on a stated platform. `design/am16_series_equivalence_probe.py` demonstrates on the real files (swisseph 2.10.03): the series is byte-identical across two processes and for a byte-identical copy in another directory (identity is content, not location); an **unopened** file (`seas_18`) may be removed or altered with **no** change; damage inside the opened files is refused by the library or moves the series; a byte outside the consumed segments does not move the series — the opened-file hash is a **sufficient, conservative** identity. **What `probe_digest` is for (settled here):** with the artifact hash bound it is **not** a claim of correct behaviour at unprobed instants — a finite probe cannot prove that, and that proof is carried by artifact + files + flags. It is an **end-to-end tripwire for environment drift those three cannot see** (a different libm/FMA behaviour on the same architecture string, a preloaded or shimmed library, a wrong sidereal mode/flag at run time): if the running process does not reproduce the recorded numbers at the probe instants, the build is refused before it writes anything. **The LITERAL preimages and expected sha256s are frozen** in `design/am16_vectors_frozen_v2.json` (v1 superseded; no build used it) (registry preimage + the whole-vector canonical JSON per case); `python design/am16_vectors_model.py` recomputes and compares them, so serializer drift (separators, key order, escaping, number format, a renamed key) fails. Stream A's `assemble_vector` is to reproduce these literals.
  There is no aggregate identity field; `diff_vectors` names the differing components. The reference model `design/am16_vectors_model.py` v2 states this and was **cross-checked byte-for-byte against A's pure functions**.
* **Frozen test vectors (DELIVERED: `design/am16_vectors_model.py`, reference model + frozen identity table; Stream A's implementation must reproduce them byte-for-byte):** a membership-only change (a soft factor moved), a node-series-only change (one series
  row differs) and a window-algorithm-only change (implementation identity bumped) must each change the vector and be refused when mismatched.

---

## AM-17 — RULED, **REWRITTEN per Codex round 6 R3**: window components, supports, peak objective

The earlier text ("one window per class × path-version" and, in the next sentence, a connected union) is withdrawn: a path can have several disconnected
components, and "admitted records' supports" must mean support **after all necessary predicates are applied**.

**Closing text (Codex; adopted by the steward before any candidate inspection).**
> Emit **one window per maximal connected component of the prerequisite-satisfied support**, within a class and path-version. **Never bridge a gap.**
> **P4 support is the intersection of the two agents' influence unions.** Its peak retains the **frozen max–min objective** (S:321–323, O-RP-3:
> `max over t of min(activity_Jupiter(t), activity_Saturn(t))`); each agent's activity reduction is explicitly defined over its applicable records. For
> **other paths, the peak objective is the per-root-reduced `evidence_for` function.** Choose the **earliest attained maximum** of the specified objective.
> If that objective is unqualified, `peak_instant` and dependent peak values are **NULL with the reason retained.**

* **Why the objective must be named:** on `[0,1]` let Jupiter's activity be `0.2+0.8t` and Saturn's `1−0.8t`. P4's prescribed peak is `t = 0.5`; maximising the best record
  selects an endpoint; maximising the summed evidence gives a plateau. Earliest-tie handling cannot reconcile them.
* **STEWARD RULING (Codex round 7 [7]) — objective ≠ stored score; frozen reductions and tolerances.** (i) The peak **objective** and the stored `score` are **distinct, separately named fields**. For **P4** the stored `score` = the **max–min objective value at the peak** (`max over t of min(act_Jupiter(t), act_Saturn(t))`); for **every other path** the stored `score` = the **maximum live record product at the peak**. The objective's name and value are disclosed in the window's provenance; they are never silently substituted for one another. (ii) **`act_g` = max over the agent's live admitted records** (a bounded activity value; one qualifying influence suffices; no summation by contact count). (iii) **Peak-tie tolerance = 1e-9 applies between DISTINCT maxima or plateaus** (two separate candidate peaks whose objective values differ by < 1e-9 are the same value and the earliest is chosen); **within a smooth piece the piece's own argmax is taken** (no tolerance blurs a single smooth maximum) — steward ruling, round 8 (the frozen measurement contract's 1e-9); the **storage-comparison tolerance** (verifier equality of stored vs recomputed values, at the column's precision) is a **separate, named constant** and is never used to choose a peak. (iv) Peaks are **solved over pieces partitioned at exact factor-state boundaries** (every vedha/aspect/prerequisite/qualification change point) by a method that **establishes the global maximum on each piece** (on a piece where each member value is affine in t, the maximum of the max–min objective lies at a piece end or at the crossing of two affine members — closed form); a sampled maximiser is not a proof, and a short interior island (e.g. a vedha-inactive stretch) must be found.
* **Stored fields at the selected peak (1156:247–309):** `score` per the ruling above (∈ [0,1],
  NULL = unqualified); `evidence_for` / `evidence_against` = per-channel Σ over roots of the per-root max (finite ≥ 0, never netted; **NULL when qualification
  does not propagate cleanly — R1**); `severity` = **NULL** (`valence.py:26` still defaults it to `0.0`: **Stream C's C8 fix is required**, not in PR #2894);
  `outcome_valence_for_native` via `valence.compute_valence` (a NULL evidence channel takes the unresolved branch). The CHECKs validate values; they do not clip or define the reduction.
* **Two NAMED result policies (steward M20261002T062742-971a; Codex round 9 R9-1); the manifest selects exactly one.** (a) **`all_null_candidate/1`** — the policy of the all-NULL candidate milestone. **Every numerical result field is NULL, including `objective_value`**; `peak_instant` is **absent** (NULL, reason retained); `outcome_valence_for_native` is **`unqualified`**; while the **geometry, the supports, the memberships and the counts stay populated** (components, support ranges, member lists and the counts derived from them are facts of the search, not qualified results). (b) **`window_qualification/1`** — the policy of the later qualified-scoring milestone (objective, peak, score, evidence channels and valence as ruled above). The policy is a **required key of the AM-16 vector (/3)** and the candidate gate refuses a window whose stored result contradicts it. The objective ≠ score ruling above applies under (b); under (a) the objective is named in provenance but carries no value.
* **Admission is independent of qualification.** Retaining the full admitted union is consistent with P's merge and T-FP rules; a resulting budget failure is a **failure to report,
  not grounds for a hidden score threshold.** The ranking adapter's `si := evidence_for` and its NULL policy are the pre-registration in
  `measurement/EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING_v1_3.md`.

---

## AM-18 — RULED (steward M20261002T004621-2b84; source design/P2_VEDHA_ANSWER_v1_0.md): vedha source, value mapping, scopes

**This amends FROZEN text (§2.3 inv 3, §5.2 inv 1) and therefore goes to Codex with the A5.5 gate.**
1. **Source.** Vedha intervals are **derived inside `ka_gochara_v5`** as the half-open intersection, at the stored spans' own instant precision, of
   (primary graha resident in house *h* from janma-rāśi) ∩ (an obstructor resident in the vedha house *v*). Pairs come **only** from the **36 cited**
   `bg_transit_rules` vedha rows (**read, not copied**; accessor `services/gochara_rules/vedha_derive.py::load_pairs/pairs_from_rows`, which **validates the load** — supported
   Phaladīpikā XXVI.3–8 citation, unique keys, `favourable` only, house domains, node rows still L0-flagged UNSOURCED, the 36 + 6 census — **refuses** an incomplete or changed authority
   (a missing pair is never a declared non-applicability) and returns the **content digest of all 42 consumed rows** for the AM-16 `l0` binding; `derive_vedha` accepts only that validated object); the **6 Rāhu/Ketu rows L0 itself flags UNSOURCED are not usable**. Exceptions: Sun↔Saturn and Moon↔Mercury never obstruct each
   other (M-8). `kala_vedha_gochara` is **not read** (date grain, separate generation).
2. **Value (cited step).** Phaladīpikā XXVI.3–8 (`phaladeepika:PG322:C1`, `PG323:C1`): an occupied vedha place **nullifies** the good result of a
   favourable-house transit. `vedha_attenuation@1.1.0`: **apply the cited binary factor to the favourable-residence record's contribution, then assign that contribution to the event class's channel. Active obstruction never changes admission or admitted support.** (Codex round 7 [6d]: this avoids treating "FOR" as an unconditional channel label.) Active ⇒ 0.0; **established** inactivity ⇒ 1.0; nothing graded. The window **stays admitted**; the record stays stored with qualification `vedha_active`. **Amendment:** §2.3 inv 3 "no soft
   factor zeroes an admitted window" and §5.2 inv 1 "never excludes" now read: *no soft factor **excludes** an admitted window* (a cited nullification may
   drive a record's value to 0.0). **Applicability:** favourable houses only — adverse-residence records carry no vedha factor (declared not-applicable).
3. **Vipareeta:** `cancelled_vipareeta` is **not produced** — no served citation (verbatim PG322–323 contain none). Open: **ND-VIPAREETA**.
3a. **Coverage (Codex round 7 [6a]).** An obstructor's stored residence must be **established over the primary span** before its absence from the vedha house counts: an empty or gapped residence is *missing data*, not inactivity. Precedence per sub-interval: a known cited obstruction ⇒ 0.0 (it settles the value whatever else is unknown); otherwise a coverage gap of a necessary obstructor (`obstructor_residence_unknown`), an undecided node obstruction (`node_obstruction_undecided`) or a node coverage gap (`node_residence_unknown`) ⇒ `unqualified`; only established inactivity ⇒ 1.0 with the Moon scope. Exception obstructors (Sun↔Saturn, Moon↔Mercury) need no coverage.
4. **Nodes as obstructors:** undecided (**ND-NODE-VEDHA**). While Rāhu or Ketu resides in the vedha house and no cited obstructor does, the factor is
   `unqualified` (`node_obstruction_undecided`) for that sub-interval — neither 0 nor 1; a cited obstructor present ⇒ active regardless.
5. **Moon as obstructor:** the Moon is not a stored agent (AM-4/AM-14), so stored state can prove `active` but never fully `inactive`. Value 1.0 is stored
   with the machine-readable scope **`excluding_on_demand_moon_obstruction`** on every such record and window (a **Mercury primary is exempt** — Phaladīpikā
   XXVI.6 excepts the Moon, so its stored `inactive` is complete); the `day_on_demand` tier evaluates Moon obstruction at serve time and serving must show the scope.
6. **O-VI-6** (Stream B): literal residence spans incl. both exception pairs, a node alone in the vedha house, a cited obstructor beating a simultaneous node,
   abutting obstructors, half-open edges, not-applicable and missing-input cases — `tests/l3/gochara_rules/test_am18_vedha.py` (sibling PR, stacked on #2897).
   The **independent verifier** compares the builder's vedha segments with an **independent oracle** — `services/gochara_rules/vedha_oracle.py`, a *pointwise* evaluation (which sign is each graha in at the instant?) merged over elementary intervals, a different algorithm from `derive_vedha`'s interval algebra — and **not** with `derive_vedha` itself. The oracle agrees with the algebra on 126 scenarios and catches mutants of it. Structured factor results (`state`, `value`, `reason`/`reasons`, `qualification`, `scope`, `obstructors`, `unknown_obstructors`; `vedha_factor_results`) are what the writer carries and persists; `excluding_on_demand_moon_obstruction` must survive storage and serving on every affected record and window.
7. **Registry:** `vedha_attenuation@1.1.0` + `P2@1.1.0` (1.0.0 rows untouched; `SUPERSEDED_*` recorded).
8. **Unique keys cover ALL rows (Codex round 8 R8-7).** The pairs load validates unique `(graha, primary_house)` keys over **every** row — the six L0-flagged UNSOURCED node rows included — **before** any node-row early return; a duplicate Rāhu or Ketu key is refused even though the 36 + 6 census still balances. (This validates the authority; it does not enable node doctrine.)
9. **The structured, version-bound callback contract (for the later writer/sweep integration).** A vedha callback is called with the **exact factor reference** of the membership (`vedha_attenuation@<v>`), the agent, the primary house and the primary span, and returns `{factor, applicable, results[], boundaries[], scopes[]}` (`vedha_derive.vedha_callback_result`): `factor` echoes the requested reference; `results` are one structured factor result per segment (`state`, `value`, `reason`/`reasons`, `qualification`, `scope`, `obstructors`, `unknown_obstructors`, `t_in`/`t_out`) partitioning the primary span, or the single declared `not_applicable`; `boundaries` are every segment boundary instant and are passed to the sweep as its `state_boundaries` (so a short interior island is found); `scopes` lists the machine-readable scopes present (`excluding_on_demand_moon_obstruction`), which must be **persisted on every affected record and window and served**. **The caller validates** (`check_callback_result`): the returned reference equals the one requested (top level and on every result), segments abut, a not-applicable result is exactly one declared entry. A float-only callback — or one that does not echo the reference — is refused. The independent oracle runs over the **bound source residence data**, never over the builder's derived segment output.

---

### AM-21 part 4 (steward ruling, Codex round 9 R9-5): the P1 pratyantar (PD) level is authorised TESTIMONY, not a scored-path member — named limitation `p1_pd_level_no_source`
**What is true of the code (stated plainly, correcting the earlier packet wording).** The writer enumerates the P1 PD level, mints anchored records for it (agent = anchor lord X′, ℓ = PD) and the record verifier requires it — it is **not** disabled, and anchored P1 records **are** minted. The packet's earlier statements "P1 PD level — disabled" and "anchored records not minted" were wrong and are withdrawn.
**Ruling.** The served corpus gives **no verse** for a pratyantar-level reading (XX.34–39 speak of Dasa and Bhukti; AM-21 part 2 flagged the PD extension). Therefore: **P1 PD-level records are authorised TESTIMONY** — stored, verified and served with their anchor, **never scored-path members**: they do not enter the admitted-score set, any qualified P1 scoring (AM-19), T-FP burden or ranking; they carry the stamp `source_qualification = 'testimony'` and the named limitation **`p1_pd_level_no_source`** (reason: no served-corpus source; the spec's PD extension is retained as observation only).
**Executable form (one policy, four places).** (i) *Enumeration/inventory:* the PD-level edges are enumerated and appear in the inventory as obligations (their searches are performed); (ii) *records:* PD-level records are minted with `period_anchor_level = 'pd'` and are excluded from the scored-eligibility predicate by that value; (iii) *verification:* the independent verifier derives the PD-level records and compares them like any other, and additionally asserts that **no PD-level record is counted as scored**; (iv) *the candidate gate and the packet:* the limitation is listed as a **named limitation**, not as a disabled capability.
**Deferred limits that stay explicit (never described as exhaustive classical coverage).** The inimical-sign / retrograde admission clauses of XX.37 (AM-22's neighbour; "retrograde" as a Phaladīpikā XX.37 admission) are **not implemented as scored forms**; the implemented subset is the Dasa/Bhukti forms XX.34, XX.35, XX.37, XX.38 under the stated anchors.
**Status:** RULED (steward). Stream A aligns enumeration/records/verification to the stamp; Stream B reconciled the packet.

## AM-22 — RULED TEXT (Codex round 8 R8-2; steward M20261002T032818-fea8): per-class version selection and supersession
**Defect.** A class inventory that includes **every sealed version** of a path double-counts once a successor coexists with its predecessor: 1206 detects `multiple_included_versions` and `superseded_without_included_version`, and the writer's `bound_path_version` materialises one selected reference per path — so inventory and output would describe different searches.
**Operative text (Codex, adopted):**
> **Separate the bound catalogue from the selected version for each class/path. Account for every sealed version, include at most one, and mark an older version `superseded_by_version` only when its approved successor is included for that class. Derive the same dispositions independently. Preserve original selections for historical replay.**
**Rules.**
1. **Two sets.** The *bound catalogue* = every sealed `(path, version)` (the AM-16 `registry.census`); the *selection* = for each `(class, path)`, **at most one** version marked `included` (or `computed_empty` where it has no obligations); the selection is a manifest fact bound into the AM-16 vector, so changing it changes the input identity.
2. **Accounting.** Every sealed version appears in every class inventory with exactly one disposition: `included` (the selected one), `superseded_by_version` (an older version whose **approved successor is included for that class**; the successor is named in the row), `excluded` (with reason/ruling), or `computed_empty`. An older version is **never** `superseded_by_version` for a class whose successor is withheld or not included there.
3. **Composite keys.** All version-specific dispositions, obligations, pins and verifications are keyed by the composite `(path_id, rule_version)`; a bare path id never selects a version.
4. **Independent derivation.** The verifier derives the same dispositions from the sealed catalogue, the approved-successor relation (`SUPERSEDED_PATHS` / `SUPERSEDED_FACTORS`, per class) and the manifest's selection — never from the writer's inventory output.
5. **Historical replay** checks the **original** selection and catalogue stored on its manifest (AM-16), not today's.
**Required tests (Stream A):** old-only; old + new with the successor included (old = `superseded_by_version`); old + new with the successor **withheld** for the class (old stays `included`, new `excluded` with reason); unknown-H classes; held P5; a mutation that includes both versions fails 1206's `multiple_included_versions`.
**No new selector DDL** is justified by this finding (Codex).

## AM-23 — NOTE (Codex round 8 R8-9): relationship of #2914 to qualified P1 scoring
PR #2914 (strict L1 input wrappers) is a **prerequisite of qualified P1 scoring only**, not of the first all-NULL candidate. Completion before numeric P1 activation: use the wrappers in the governed transit path; bind the consumed L0 rows and the effective L1 implementation (AM-16 `l0` and `implementation`); replace the duplicate maitrī authority through the accepted loader; keep named failures for missing or divergent inputs; resolve AM-19 value mappings/channel assignment. **The retrograde clause (Phaladīpikā XX.37) remains a named limitation**; if adopted it changes admitted readings and needs an explicit admission amendment — it cannot be treated as merely an unavailable score factor.

## AM-24 — RULED TEXT (Codex round 9 R9-2; steward M20261002T062613-6d61): the window-verification invariant — complete derivation, bound to every relevant input, current at the seal
**The invariant (normative).** A window verification result may satisfy the candidate gate only if **all** of the following hold at the moment of the first seal, each derived **independently of the builder's stored output**:
1. **Complete expected output, both directions.** The verifier derives from the bound inputs (pinned L1 facts, daśā rows, sealed registry selection, sky convention, ephemeris identity) the **complete expected sets** — contacts, anchored records (with their prerequisite results and admission state), windows, and window↔record memberships — **including the empty set** ("zero contacts / zero records" is a derived claim, not an absence). The gate compares **expected against stored in BOTH directions**: a stored element with no expected counterpart **and** an expected element with no stored counterpart (an omitted contact, an omitted anchored record, an omitted membership link) are each a violation. Verifying only the surviving records is **not** verification of the output.
2. **Bound to every derivation-relevant dependency.** The verification result carries a digest over **all** of: the window content, the **membership links**, the **contents** of the records and prerequisites the windows derive from, the contacts they cite, the registry selection, the inventory and the input snapshot identity (`input_digest`) — not only window fields and existing member IDs, and not only the union of admitted supports.
3. **Stale attestations are rejected at sealing.** Any change after verification to any element of (2) — including **adding a valid admitted record whose support lies inside an already-verified window and omitting its membership link** (the review's counterexample) — makes the verification stale; the seal trigger recomputes the dependency digest from the database and **rejects** a result whose digest differs. Relevant changes **invalidate** verification; they never leave it "current".
4. **Trust boundary stated plainly.** Database grants identify *which principal* wrote a result; they cannot prove that the independent derivation *ran*. The verifier job is therefore **pinned** (code identity recorded on the result: runner commit/digest, policy version) and **executed independently** of the build; table access alone is never described as computational independence.
**What this does not claim.** It does not require the deferred objective maximiser or qualified vedha/P1 scoring; it concerns **completeness and currency of the materialised, all-NULL output**.
**Owner:** Stream A implements the derivations and the migration-1240 dependency digest; Stream B states the invariant and reviews the fix when pushed (steward M20261002T062613-6d61).

## AM-25 — CANDIDATE (not ruled; named pre-condition of NUMERICAL activation): one in-orb stay = one evidence root (steward M20261002T084648-f2c2)
Full text, the real-loop computation and the proposed oracle O-RL-1: `design/AM25_RETROGRADE_LOOP_ROOT_IDENTITY_CANDIDATE_v1_0.md`. Summary: the frozen §2.1 sums over roots with `root_id := contact_id` (one exact crossing = one contact, NK-2/O-RX-1) and the kernel's WP2-pinned episodes overlap by construction, so one continuous in-orb stay holding k exact crossings would contribute k times once numbers exist. Candidate rule: keep contact identity and episodes exactly as frozen; accumulate over **stays** (`stay_id`, maximal connected in-orb interval) with `max` inside a stay; exact hits are sub-events. Real example (Saturn, canonical natal Ketu 229.0330°, aspect 270°, orb 1.0°, 2024): 3 roots in 2 stays (frozen 3.0 vs candidate 2.0 for a unit record value). Not part of the all-NULL milestone.

## RULINGS BY DELEGATE (authority: `decisions/NATIVE_RULINGS_BY_DELEGATE_v1_0.md`, 2026-10-02) — status of every named decision; implementation DEFERRED until round 10 returns
The native delegated every open decision; the file is treated as the native's rulings (he may overrule by a later dated ruling; nothing in it is edited — a change is a new version). **These rulings enable numerical-activation work but do NOT change the current milestone: the all-NULL `'5.0'` candidate stays the gate target, and no registry rows for the newly ruled values are started before round 10 returns.**
| decision | ruling id | status | one line | implementation |
|---|---|---|---|---|
| ND-ORB-ADMISSION | `NR-ORB-ADMISSION-20261002` | **RULED** | admission orb = the engine's own `ORB_TABLE` (1.0° slow / 3.0° Moon), read at bind time, never copied; labelled an uncited engineering convention; disclosed on every served point-contact answer | deferred (new `activity_kernel` version + new path versions) |
| ND-ORB-SCALE | `NR-ORB-SCALE-20261002` | **RULED** | `1 − |Δλ|/orb` over the same referenced orb, `uncalibrated_default — ordering only`, separately versioned | deferred |
| ND-VIPAREETA | `NR-VIPAREETA-20261002` | **RULED: not used** | `cancelled_vipareeta` is never produced; AM-18 item 3 closes | none needed |
| ND-NODE-VEDHA | `NR-NODE-VEDHA-20261002` | **RULED: undecided stays, with a named deadline** | `node_obstruction_undecided` (unqualified sub-interval); deadline = before qualified P2 scoring is scheduled; native chooses at the deadline if no source is found | none |
| ND-NODE-RETRO-VEDHA | `NR-NODE-RETRO-20261002` | **RULED = N-83 (Stream B's recommendation (b) NOT adopted)** | `retrograde_malefic` never attaches to a node (NULL = "not applicable", with a stated reason); motion stored as a cited constant `obstructor_motion_basis` (always retrograde, mean series, Phaladīpikā XXVI.48 `PG348:C1`); Sarvatobhadra rows add `vedha_side = right` and `text_intensifier_status = implied_by_premise_not_computed`; Mars–Saturn keep the per-day detector | step-3 spec §12c; vedha writer version bump deferred |
| ND-COMBUSTION | `NR-COMBUSTION-20261002` | **RULED** | L0 `bg_combustion_orbs` via L1 `check_combustion` (reference, never a copy); Jupiter 11° with the Nāḍī 12° disclosed as a source variance | deferred |
| ND-P1-FRAME | `NR-P1-FRAME-20261002` | **RULED: the lagna (AM-20)** | confirmed | none |
| AM-19 D1–D7 | `NR-AM19-D1…D7-20261002` | **RULED** | D1 L1's nine dignity categories; D2 XX.30 ladder (1·¾·½·¼) favourable, adverse a declared ungraded 1; D3 friendly ¼, neutral = does not fire; D4 combustion a binary adverse trigger; D5 each trigger its own directed reading, never netted; D6 adopt the retrograde clause (XX.37) via an explicit admission amendment and new P1 path version AFTER the first all-NULL candidate; D7 XX.29 as the bhukti-auspiciousness predicate for the XX.38 deliveries | deferred (P1 path version) |
| ND-P1-PD-LEVEL | `NR-P1-PD-LEVEL-20261002` | **RULED = the steward's ruling confirmed** | PD-level readings are authorised testimony, never counted (AM-21 part 4) | in the writer already |
| `'4.1'` T-honesty | `NR-41-DIAGNOSTIC-20261002` | **RULED: diagnostic-only** | `t_honesty.status = UNVERIFIABLE`, `pass:false`, never flip-eligible under v2.3; `'5.0'` is the gated generation | the Stage-1 freeze proceeds as prepared |
| ND-ROLES | `NR-ROLES-20261002` | **RULED: option A** | separate principals; new `gochara_verifier` (not `data_plane_verifier`); verification = separate operator-dispatched job; seal = approval-gated workflow with the native as required reviewer; 1206 §7 edited BEFORE first application (folded into #2867) | credential/infrastructure acts (rulings §3.6, nine) **await the native's explicit go-ahead — none performed** |
**Findings recorded by the delegate:** (1) Phaladīpikā XXVI.31–32 (`phaladeepika:PG334:C1`) states a cited house-favourability × dignity/combustion interaction bearing on the P2/P3 mappings — it needs its own decision packet before any P2/P3 numerical amendment; (2) the served BPHS cannot cite chapter 26 by locator (`read_chapter(bphs, 26)` returns chapter-1 chunks) — an L0 corpus defect passed to the L0 owner; until it is fixed such citations are by CHUNK ID and marked "re-point when the L0 corpus fix lands". **Not touched:** ST-P5-HOLD-20261001 and ST-H-UNKNOWN-20261002 stay in force.

## Batch checklist for the A5.5 gate (v0.5)

| # | Item | Spec fold | New migration? | Decision left? |
|---|------|-----------|----------------|------------------|
| AM-1 | Convention vector byte-pinned + digest; domain authority; bridge evolution | §6.0 (new) | no (data row, chart-serving txn) | no |
| AM-2 | UUIDv8 + O-RX-1a; SQL-valid `span:`/`star:`/`point:` bytes; enrichment-vs-correction per 1153; UUID + post-mask vectors | §6.1 | no | no |
| AM-3 | Two transaction categories; chart lock BEFORE legacy coverage writes | §10.1 | no | no |
| AM-4 | Moon/day EPHEMERAL; query receipt storage/identity/manifest exclusion; P6-context deferral | §6.2/§10.1 | no | no |
| AM-5 | `partition_key=event_class` + **search-input snapshot, committed obligation sets (absent ≠ proven-empty), interval ledger, independent verification, seal trigger with replay branch**, manifest binding, lock protocol, serving states | §10.1 | **yes — migration 1206 (6 tables, 17 functions, 1 trigger); protected schema-capability route (F-1)** | no |
| AM-6 | `sad_bala_sufficient` v1.0; `null_state='unqualified'`; score-qualification ≠ admission | factor catalogue | no | picked: C |
| AM-7 | `'av_qualifier'` + P5 contract completed (identity/applicability/lineage/read-back) | relationship_record | 1204 (kept), protected window | no |
| AM-8 | P6 testimony template; five frame kinds; future designed migration | new (template) | 1205 SPLIT OUT | no |
| AM-9 | L0 Rāhu/Ketu finding (provenance narrowed) | none | no | L0 owner's ruling |
| AM-10 | §4.0 daśā read-contract re-pin rule (conditional on L1-rebuild close; no new pin value) | §4.0 | no (one code PR at re-pin) | steward declares rebuild landed |
| AM-11 | Prerequisite-evaluation implementation pins (a)–(d) + P1 obligation-agent role token (e) | §2.2 / §10.1 | no | no |
| PC-1, PC-2a/2b, PC-3, PC-4, **PC-5** | Named pre-conditions, restructured per Codex R9 (sealer activation; identity/registry/manifest; Moon receipts; protected window; verifier independence; **first 5.0 candidate build**) | see the PRE-CONDITIONS section | — | gate steps, not merges |
| AM-18 | RULED: vedha derived from stored residence spans (36 cited L0 pairs, validated complete + content-bound), residence **coverage** required (gaps ⇒ unqualified), cited nullification step applied to the record's contribution then channel-assigned (active 0.0 / established-inactive 1.0; admission never changed — amends §2.3 inv 3 / §5.2 inv 1), vipareeta not produced, nodes undecided, `inactive` Moon-scoped; `vedha_attenuation@1.1.0`, `P2@1.1.0`, O-VI-6 | §5 / §2.3 | no (registry code; no DDL) | ND-VIPAREETA, ND-NODE-VEDHA |
| AM-13 | RULED: factor applicability by object kind (`activity_kernel@1.1`: extent targets incl. star ⇒ membership step, true points ⇒ angular with orb a row parameter; drishti = aspect records only); orb = open native decision ND-ORB | factor catalogue | no (registry code + A's binding; no DDL) | ND-ORB |
| AM-14 | RULED, **rewritten per Codex R2**: Moon-resolved portions of `period_lord:*` obligations are accounted as `excluded_moon_tier` (neither missing nor searched), derived per obligation from the snapshot-bound daśā rows; `stored_scope = stored_non_moon` bound to the manifest vector and returned by the mandatory response constructors | §AM-5 / AM-4 | **yes — additive migration 1232 (PR #2909, HOLD, stacked on #2867)**; it replaces 1206's completeness function with exactly two edits and extends the state CHECK | no |
| AM-15 | RULED: P1 anchor counted inclusive from the lagna | §2.2 P1 | no | no |
| AM-16 | RULED: `'5.0'` manifest vector contents | §10 / AM-5 | no | no |
| AM-17 | RULED: stored window fields (score ∈ [0,1]/NULL, evidence Σ-over-roots, severity NULL, union interval, earliest peak) | §2.1 / §3 | no | no |
| AM-20 | RULED: `house_from_frame` of a P1 transit record = lagna count; a stored descriptor nothing scores on | §0 / §2.2 P1 | no | ND-P1-FRAME (label only) |
| AM-21 | RULED TEXT: P1 support = contact ∩ running-period domains of the ANCHORING lord/role; Sun/Jupiter delivery anchors on the bhukti lord; Moon-tier exclusion follows the transiting body; supersedes occurrence-instant admission | §4 / §2.2 P1 / AM-11 | **yes — additive migration 1233 (PR #2919, HOLD, stacked on #2909)**: `period_anchor_lord` / `period_anchor_level` | AM-19 (value mappings), PD level has no verse |
| AM-22 | RULED TEXT: per-class version selection and supersession (bound catalogue ≠ selected version; at most one included; `superseded_by_version` only with the successor included for that class) | §AM-5 / AM-13 | no | no |
| AM-12 | CANDIDATE: `sad_bala_sufficient` as a soft factor of a new P1 rule_version (older P1 → `superseded_by_version`) | factor catalogue / rule_path | no (data rows, new rule_version) | A5.5 gate + L1 owner (Sun rūpa finding) |

## A5.5-gate NAMED PRE-CONDITIONS (v0.13 — restructured per Codex round 6 R9: each gate is placed BEFORE the action it protects)

Conditions of **named later steps**, not of merging #2867/#2817 (both stay HOLD; the steward schedules ONE protected window for 1204 + 1206).

| # | Gate | Must hold before | Evidence required |
|---|---|---|---|
| **PC-1** | **Sealer activation.** The restricted sealing principal runs the **initial seal and BOTH replays** under the **intended restricted role**, with **PUBLIC EXECUTE revoked** and the **complete helper closure** available; **effective privileges are verified and the builder cannot seal**. (#2867's source repair addresses the earlier test defect; actual-activation evidence is outstanding.) | the sealing principal is **activated** | live run as the real role: effective-privilege query, seal, replay, replay-after-registry-advance; builder refusal; **EXECUTE on 1232's two new functions** (`ka_gochara_search_moon_resolved_domain`, `ka_gochara_search_moon_scope_violations`) in the helper closure |
| **PC-3** | **Protected 1204 → 1206 → 1232 window** (logical order, **separate file transactions**; 1232 is the additive AM-14 migration, PR #2909). **Ledger precondition (stated, not assumed):** `migrate.ts:756–763` **refuses a `--only` list that jumps an unapplied predecessor**, and the 1232 live fixture applies **1216 between 1206 and 1232** — so the single deployment invocation works **only when every unselected predecessor of 1204/1206/1232 is already applied on the target ledger**; otherwise stage them through their proper route first. The fixture does not prove the single invocation on that ledger; the rehearsal must. Exact migration/application **heads**; a **supported PostgreSQL version**; **faithful object ownership and default privileges**; **complete role grants**; **realistic 26-class volume**; **contention and seal timing**; **per-file failure recovery** (1204 can stay committed if 1206 fails). The advisory DB job needs **explicit evidence at the reviewed head**; its existence is not sufficient. | the **protected deployment** | rehearsal record on a production-shaped clone with the above items, **including the actual deployment invocation against the migration ledger** and per-file recovery for all three files |
| **PC-5** (new) | **First `'5.0'` candidate build.** *Accepted successor contracts and oracles; version-aware registry binding and read-back; geometry and qualification handling; the resolved Moon-scope contract (AM-14); deterministic window construction (AM-17); complete input/manifest binding (AM-16); class census and candidate invalidation — implemented and demonstrated through the intended restricted writer's complete output flow.* ND-ORB may remain open for a deliberately **unqualified-point** candidate, provided that state and its measurement consequences are frozen (SI addendum v1.3 §4). | the **first 5.0 candidate build** | the writer's complete flow run as the restricted role against the accepted contracts; frozen vectors |
| **PC-2a** | **Identity, registry and manifest prerequisites** — F-3 (identity bytes, census, `self`→`native` vector update), version-aware registry binding/read-back, AM-16 manifest binding. *(split from the old PC-2)* | the first `'5.0'` candidate build (part of PC-5) | contract + vectors accepted; writer reproduces them |
| **PC-2b** | **Moon receipts and deferred P6 containment** — F-6. *(split from the old PC-2)* | their **actual on-demand use** | receipt table/API, canonical rendering, before/after-seal evidence |
| **PC-4** | **Verifier independence.** The verifier role has the **source/registry reads and invoker-helper EXECUTE** needed for independent derivation — not merely SELECT on the inventory tables; the **builder's verification-write capability is removed**; effective inheritance and role-switching boundaries are tested. Until then independence is described as **a property of the separate derivation code**, not of the database. | **verifier independence is claimed** | role-mirror suite: verifier derives and writes verification rows only; builder cannot |

**1220 needs no corrective grant change** (Codex): 18 named function signatures + seal-table SELECT, no seal-table writes, no `ka_gochara_seal_generation`, no grant option, no SECURITY DEFINER change; repeated GRANT is idempotent; it does not remove unrelated inherited privileges and its suite does not establish capability for the future window-writing flow.

## A5.5-gate follow-ups — Codex v1.4 ranked list (P2; owed at the A5.5 gate; no P1 blocks)

Numbering follows Codex v1.4's ranking (**F-1…F-6**). Old label → new:
F-3→F-1, (new)→F-2, F-4→F-3, F-5→F-4, F-6→F-5, F-7→F-6. Owner **A** = Stream A
(build/delivery), **B** = Stream B (spec/oracle/measurement), **S** = steward.

| ID | Codex rank | Required completion | Owner | Blocks |
|---|---:|---|---|---|
| F-1 | 1 | Additive storage + seal checks for AM-5 (6 tables, 17 functions, seal trigger, replay branch) as new migration file(s) with protected-runner wiring in the SAME window as 1204; database adversaries on a disposable PG: wrong manifest, post-seal mutation rejection, full replay lifecycle (initial seal → identical replay → registry advance → replay again). **IMPLEMENTED as migration 1206 (v1.2: explicit EXECUTE grants, `superseded_by_version`, version-scope seal checks) + live suite + static test, PR #2867 HOLD (Codex re-review owed); see §AM-5 implementation record** | **B** wrote the migration + DB tests (steward M20261001T201843-f8e5), **S** schedules the protected window | inventory migration acceptance |
| F-2 | 2 | Bind exclusion `basis` / `ruling_ref` into the verified inventory preimage; mutation tests; revised digest vectors. **Spec text, vectors and model mutation cases M1–M6 CLOSED in v0.6 (not yet reviewed)**; remaining: the same mutations as real INSERT/seal attempts in F-1's database suite | **B** | AM-5 verification acceptance |
| F-3 | 3 | Canonical bytes and storage-domain mapping (the synthetic `self` token vs stored `affected_person='native'`; period-lord role tokens → concrete grahas via the pinned dasha snapshot — **token form SETTLED in AM-11 pin (e)**: role tokens in the inventory; frame args, target bytes, timestamp precision, delimiters); full-precision formatter / quantization question; declared class census (an absent class reports `not_searched`); registry-version selection (historical/superseded versions neither vanish nor double-count); candidate replacement/invalidation across verification rows, manifest bindings and derived outputs; qualified-geometry planning and O-RW-1 invalidation; retain O-RX-1a | **B** (bytes/spec) + **A** (identity builder, writer) | A5.5 identity and writer gate |
| F-4 | 4 | Typed rūpa/bindu operand storage; declaration-key bytes and L1 build/convention identity; P5a/P5b path ids and applicability storage; `null_state` on the versioned `ka_gochara_factor` row (1154:310–334), **not** the membership (draft text at AM-6 still says membership — one-line correction owed); edition/translator for Phaladīpikā IV.22–23 | **B** (AM-6/AM-7 text) + **A** (storage) | AM-6/AM-7 writer acceptance |
| F-5 | 5 | Actual P5 evaluator fixtures: numeric bindu mismatch, BAV/SAV selection, independent P5a/P5b missingness, citation through declaration (not the test-local `consumeDeclaration`); repair the oracle map's stale 1205 reference (line 133) and the B6-F16/F17 sentinels | **A** (PR #2817 fixtures/evaluators) + **B** (oracle map v1.2) | P5/A5.5 acceptance (not vocabulary-only 1204) |
| F-6 | 6 | Moon receipts: table/API, key, canonical result rendering excluding self-referential digest/audit fields; generation-5 manifest-digest implementation carrying AM-5's `inventories_digest` and excluding `moon_on_demand`, with before/after-seal evidence; P6 context/containment stays held | **B** (AM-4 text) + **A** (implementation) | Moon/day implementation acceptance |

Also owed from Codex v1.4 (folded in the rows above or already applied): the
model is a partial abstraction (partition/manifest/lifecycle/replay fidelity,
no independent derivation) — SQL-level adversaries in F-1 replace it as the
acceptance evidence; wording scoped so that changed inputs change **completion
digests**, not the nine-field `ob_id`.

New oracle proposed by AM-5 for the successor oracle file (frozen v1.4 untouched):
**O-RP-9** — an independent re-derivation of every class's inventory (pins,
dispositions, committed sets, `computed_empty`, exclusion bases) from the sealed
rule versions + the snapshot's L1 facts reproduces the stored
`inventory_digest`; plus the negative arms C1–C17 of AM-5's adversarial matrix
(absent pin, absent obligations, absent intervals, false `computed_empty`,
changed input snapshot, mixed-snapshot intervals, L1 drift, `missing_inputs`,
exclusion without ruling) and the four-step seal-replay sequence (initial seal →
identical replay → registry advance → replay again). The executable model in
`design/evidence/` is a logic check of the predicates, **not** the oracle and not
a substitute for the disposable-database test.

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
