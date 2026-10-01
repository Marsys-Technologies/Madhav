---
artifact: GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT
version: 0.2
status: DRAFT — revised per ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_0 (REJECT as submitted, 2026-10-01); collects the A5.5-gate fold-in list; not a spec version
date: 2026-10-01
author: stream-B (spec lane; docs only — no code, no migration file)
supersedes: v0.1 (f870999c1) — AM-3/AM-5/AM-8 rewritten after Codex rejection; AM-1/AM-2/AM-4/AM-6/AM-7/AM-9 amended per the same review
sources: >
  ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_0 (Codex gpt-6-astra, verdict REJECT with
  per-amendment dispositions and seven ranked required amendments); steward
  revision order M20261001T171150-5c70. v0.1 sources retained: steward
  M20261001T015412-6df0 (pins 3–7), M20261001T121504-90d5; stream-B cited lookup
  M20261001T015350-644c; stream-A reports M20261001T080615-a232,
  M20261001T113409-04cd; steward acceptance M20261001T121451-1a8d; stream-B
  report M20261001T084457-5ceb.
---

# GOCHARA_DESIGN_SPECS v1.5 — AMENDMENT LIST (draft v0.2)

Revision disposition against ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_0, item by
item. **Accepted findings are folded into the proposed spec text below; where
this draft disagrees with the reviewer it says so with evidence.** Migration
discipline unchanged: migrations 1153/1154/1155/1156 are applied and **never
edited**; every schema-side change is a NEW migration, and each one touching a
live CHECK constraint needs a protected window.

Ranked-review crosswalk: rank 1 → AM-8/1205 (split; §AM-8) · rank 2 → AM-5 ·
rank 3 → AM-3 · rank 4 → AM-1/AM-2 · rank 5 → AM-6 · rank 6 → AM-7 ·
rank 7 → evidence corrections (folded into #2817's 1204 header and §AM-7/§AM-8).

---

## AM-1 — Convention row for generation `'5.0'` (pin 3) — ACCEPTED WITH AMENDMENTS, folded

Codex required: exact serialized values; convention identity ≠ generation; L1
node provenance deterministic and cited; the 1153 self-test is an admissible
example domain, not the runtime domain's authority; reconcile the literal
convention-id `'5.0'` with the A5.3 implementation's digest-based id.

**Proposed spec text (new §6.0):**

> The writer bootstrap registers the `ka_gochara_sky_convention` row for the
> `'5.0'` family in a **separate registry-bootstrap transaction** (see AM-3;
> 1153:430–485 forbids mixing the global registry lock with chart mutations),
> insert-if-absent with an equality check over **all convention-defining fields,
> excluding audit metadata** (`created_at` and any updated-at/by columns): a row
> already present with any different defining field is a loud build failure, not
> an `ON CONFLICT DO NOTHING` skip.
>
> **Convention identity ≠ generation identity.** `convention_id` names the
> *method vector* (ephemeris build, ayanāṃśa, node convention, grid, method
> version, domain); `generation` (`'5.0'`) names a *run* under that convention.
> The A5.3 implementation derives `convention_id` as `sha256:<digest>` over the
> convention vector (`services/gochara_kernel/substrate.py:153–171`, inspected
> at 694d16e9c by the reviewer); the literal `'5.0'` is a *generation label*,
> never the convention id. Once a convention id enters physical/contact
> identities it is immutable; a changed vector is a NEW id, never an edit.
>
> Exact serialized values (byte-exact; a runtime mismatch on any of them fails
> the build before any write):
>
> - `ephemeris_generation` — the exact pyswisseph build string
>   `swe.__version__` at write time (`gochara_kernel/knots.py:169`); on the
>   governed runtime today `20230604` (`swe.version = 2.10.03`). The recorded
>   value is whatever the governed runtime reports; a runtime reporting a
>   different string than the row being reused = failure.
> - `ayanamsha = 'lahiri_chitrapaksha'` (`step06_candidate_build.py:73`).
> - `node_convention = 'mean'` — **deterministically** selected: the L1 node
>   convention for chart 482012f1 as recorded in `chart_facts`, cited by
>   fact_id (subjects `RAH_MEAN`/`KET_MEAN`, e.g. fact_id `c520713087b97470`),
>   never "the latest fact" and never picked (`step06_candidate_build.py:77`
>   `node_model: "mean"` agrees). If the chart's L1 facts ever carry both node
>   conventions the selection rule is: the convention the L1 build itself
>   consumed, by its own attestation — absence of that attestation is a stop,
>   not a default.
> - `grid` — serialized exactly: sign `30`, nakṣatra `13+1/3` (13°20′ — **never
>   the decimal `13.20`**), kakṣya `3.75`, including the 0°/360° seam
>   (`gochara_kernel/contacts.py:13-15`, `convention.py:78`).
> - `method_version = '1.0.0'` (`step06_candidate_build.py:84`).
> - `domain` — half-open UTC `[start, end)`; the *governed* domain is set by
>   the campaign's scored-horizon ruling for the generation being built (the
>   1153 self-test's `1998-01-01 → 2085-01-01` demonstrates an admissible
>   domain shape; it is not the authority for any runtime domain).

**Schema impact:** none — data under the existing table.

---

## AM-2 — §6.1 identity hash: sha256 → UUIDv8 (pin 4) — ACCEPTED WITH AMENDMENTS, folded

Codex required: reconcile `hash(physical_object_id, ordinal)` with the
§6.1/O-RX-1 flattened bytes; explicit canonicalisation; collision taxonomy;
expected UUID vectors; forced-collision tests; correction identity.

**Proposed spec text (amend §6.1):**

> The identity hash is **sha256 over the §6.1 canonical bytes, first 128 bits
> carried as a UUID with the version-8 and variant bits set** (RFC 9562 §5.8).
> After the 6 fixed bits, **122 digest bits remain**; collision resistance is
> the birthday bound ≈ 2^61 identities — ample for this dataset, and **not** a
> substitute for collision handling (below). No SHA-1, no UUIDv5.
>
> **Canonical bytes, pinned:** UTF-8; body/relation tokens in the **stored
> lowercase form** (1153 persists lowercase body tokens — the hash is over what
> is stored, never over caller casing, so one natural tuple has exactly one
> ID); single-`|` delimiters; numerics at full precision with no exponent form
> and no trailing zeros added or stripped beyond the stored rendering; sign and
> star normalisation per §6.1; **no trailing whitespace or newline**. The
> O-RX-1 printed serialization (`GOCHARA_TEST_ORACLES_v1_4.json:64`) IS the
> canonical byte string; §6.1's shorthand `hash(physical_object_id, ordinal)`
> means sha256 over **the concatenation of the physical object's canonical
> bytes, the delimiter, and the ordinal's canonical rendering** — one flat
> byte string, not a nested hash. (A nested `hash(hash(A),B)` construction is
> NOT used; v0.1's shorthand was ambiguous and is corrected here.)
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
> **Correction identity:** changing a published non-null time must never mint
> a different ID from an unchanged tuple and ordinal. A correction changes an
> **explicitly versioned identity component** (S:641–646) and retains its
> `supersedes` linkage; the deterministic ID of the uncorrected tuple is
> untouched.
>
> **Test obligations (fold into the oracle suite):** expected-UUID vectors
> (independently computed — the reviewer computed
> `Mars|conjunction|point:198.52|c0|1 → 87b023cc-c9f3-8979-9b37-96701f285356`
> and the lowercase-variant divergence; such vectors are pinned in the oracle
> file); forced-collision tests **including collisions after the UUID
> bit-masks** (two digests differing only in masked bits); the O-RX-1
> direct/retrograde/direct, truncated-centre enrichment and forward-extension
> cases; replay under all three taxonomy arms.

**Schema impact:** none — PK columns are already plain UUIDs.

---

## AM-3 — Writer phase grain: **per-table persistence by publication state** (REWRITTEN — v0.1 REJECTED)

Codex rejected v0.1's blanket "each substep delete-then-insert, chart ×
generation": conventions, physical objects and contact identities are global
and insert-only; sky-event deletion is refused (1153:758–759, 813–887);
candidate contact replacement conflicts with surviving relationship FKs
(1155:413–459). The computational ordering (contacts before evaluation)
survives; the persistence sentence is rewritten by table and publication
state.

**Proposed spec text (amend §10.1):**

> The writer runs in **two phases**. Phase 1: per-body boundary substrate +
> contacts. Phase 2: per `(event_class × path_id, rule_version)` evaluation
> emitting relationship records and windows. Persistence is **per table, by
> publication state**:
>
> - **Global conventions, physical objects, contact identities** (chartless,
>   shared across charts and generations): **insert-if-absent with equality
>   checks** (AM-1/AM-2); never updated, never deleted by a build.
> - **Sky events:** only the **permitted enrichment/correction operations**
>   (1153's enrichment path and the versioned correction identity of AM-2);
>   deletion is refused by the substrate contract (1153:758–759, 813–887).
> - **Candidate (unpublished) chart × generation records and windows:**
>   replacement **in dependency order** (children before parents on delete,
>   parents before children on insert), at a **precisely owned grain** — the
>   grain is `(chart_id, generation, event_class, path_id, rule_version)` for
>   Phase-2 output and `(chart_id, generation, body-scope)` for Phase-1
>   candidate contacts — and a replacement must never target rows a surviving
>   relationship record still references (1155:413–459): the delete set is
>   computed from the grain and the FK closure, and a conflict is a loud
>   failure, not a cascade.
> - **Published / sealed data:** the existing refusal and enrichment rules
>   apply unchanged; **re-evaluation must not reopen a sealed generation** —
>   a re-run under an existing sealed generation is a refusal, and new
>   evaluation runs under a new generation label.
>
> **Transaction ownership:** the registry/convention bootstrap runs in its
> **own transaction**, separate from any chart-data mutation (1153:430–485
>   enforces READ COMMITTED and forbids mixing the global-exclusive registry
>   lock with chart mutations). "Two phases" never implies one transaction
>   that binds registries and then writes chart data. Transaction ownership
>   otherwise remains with the orchestrator.

**Schema impact:** none.

---

## AM-4 — Moon / day tier is EPHEMERAL (pin 6) — ACCEPTED WITH AMENDMENTS, folded

Codex accepted with two corrections: (a) v0.1's A:127 claim is wrong — contact
`body='moon'` identifies the **transiting** Moon (a transit-by-Moon contact),
not "natal-Moon contacts"; (b) define the lifetime and coverage of on-demand
responses, particularly after generation sealing.

**Proposed spec text (amend §6.2 / §10.1):**

> The Moon/day tier is **EPHEMERAL**: no materialised Moon rows in the global
> substrate (`kgse_body_domain_ck` excludes `'moon'`, 1153:684–685). The
> contact table's `kgc_body_domain_ck` *including* `'moon'` (1153:1072–1073)
> covers contacts where the **transiting body is the Moon** (a transit-Moon
> contact against a natal target) — it is not a natal-Moon-target licence, and
> v0.1's contrary gloss is retracted.
>
> **On-demand lifetime:** a Moon search writes its own `moon_on_demand`
> coverage record (1155:729–732 — Moon-agent coverage follows the same guard
> shape as every other agent's). The response itself is ephemeral: no
> relationship/window membership rows are written for it. After a generation
> is **sealed**, a Moon query against that generation still runs: what
> persists is the coverage record and the query receipt (query parameters,
> coverage snapshot, result digest); what never happens is a membership write
> or any mutation of the sealed generation. A post-publication P6/Moon answer
> attaches its provenance by referencing the sealed generation's manifest and
> its own coverage record — it never reopens the generation.

**Schema impact:** none.

---

## AM-5 — Coverage-partition ownership (pin 7) — REWRITTEN (v0.1 REJECTED)

Codex rejected v0.1's `partition_kind='event_class', partition_key=path`: BOTH
applied guards — 1155:706–709 and 1156:402–405 — require
`partition_key = event_class`. Writer ownership and same-transaction linkage
were accepted. Also required: an explicit cross-path completeness rule, and
the convention-bridge/`coverage_facts` snapshot bound in the same transaction.

**Proposed spec text (amend §10.1):**

> The `ka_gochara_v5` writer owns the `'5.0'` coverage partitions in
> `kala_gochara_coverage`: it inserts/extends its own partitions with
> `partition_kind = 'event_class'` and **`partition_key = <event_class>`**
> (the only key both applied guards admit), `completed_horizon` within the
> governed domain, `relations_searched` exact — **in the same transaction,
> before** the records/windows that FK them, with the required **convention
> bridge and the `coverage_facts` snapshot bound in that same transaction**.
>
> **Cross-path completeness:** a class partition covers exactly the paths the
> writer has evaluated for that class, named in the partition's relation set.
> Completing one path's transaction must NOT mark the class partition complete
> for paths not yet evaluated: the partition carries the evaluated path set
> explicitly, and a class-level "complete" signal exists only when every path
> the rule version declares applicable to that class appears in it. Extending
> a horizon and a relation set must never imply the unperformed Cartesian
> product of the two — each (path × horizon-interval) actually searched is
> recorded; nothing else is claimed. A no-window answer for class C reads the
> partition: "searched, none admitted" (evaluated path set complete) is a
> different answer from "not (yet) searched" (set incomplete), and the two are
> never collapsed.
>
> Coverage is written by the same registered writer that writes the records.

**Schema impact:** none (the guards already require this shape; v0.1's text
would have failed them).

---

## AM-6 — D2: `sad_bala_summary` — **OPTION C, as qualified by Codex** (the gate's pick is recorded)

Codex picked **Option C** with five qualifications, all folded here. Option A
was shown incompatible as written (1154:311–338 requires non-null finite
bounds within [0,1] — adding `'rupas'` to the enum does not permit `[0,+∞)`
and widening those constraints alters the factor algebra, not merely the
vocabulary). Option B introduces an uncited numerical scale and clamping makes
"exactly sufficient" indistinguishable from "above sufficient" unless the raw
value is retained anyway.

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
>   **output** range; it never bounds the raw input (v0.1 conflated the two).
> - **IV.24 (`PG80:C1`) is bhāvabala composition.** It does not establish the
>   seven graha thresholds as a bhāvabala sufficiency test; bhāvabala and
>   ṣaḍbala are never silently combined.
> - **No thresholds for Rāhu/Ketu exist in the citation.** A node operand —
>   or any missing, incompatible or unsupported operand — is explicitly
>   **unqualified**: the factor does not fire, and the path record carries
>   `unqualified`, never an invented value.
> - **Raw evidence retained, unscored:** the operand's raw rūpa magnitude
>   rides as **typed operand evidence** (value, unit `'rupas'`, and L1
>   provenance: fact_id, subject, build, ayanāṃśa, verification tier),
>   outside the factor's output range, never a second scored factor forced
>   into the bounded catalogue. It exists to explain the classification and
>   to diagnose unit/provenance errors.
> - **Zero semantics (S:129–130, S:401–402 vs S:209–213, reconciled):** this
>   is a **soft** factor. A `0` output floors the path's score contribution to
>   zero **for ranking only**; it never removes an admitted interval and never
>   becomes an undeclared necessary predicate. Admission is decided by the
>   path's hard predicates; the score orders admitted windows. (The
>   multiplication of S:209–213 applies to the score; S:129–130/S:401–402
>   govern admission — the factor's zero touches the first, never the second.)
> - **Versioning:** the factor and its consuming path membership are versioned
>   together; the legacy `sad_bala_summary` name is retired rather than
>   silently re-typed (a silent change of the raw measurement's unit or of the
>   output's meaning is forbidden — fix the data, not the detector).

**Schema impact:** none (Option C needs no migration — its compatibility with
`kgf_units_ck` and `kgf_range_unit_interval_ck` unchanged is precisely why
Codex picked it).

---

## AM-7 — D7: `object_role = 'av_qualifier'` — ACCEPTED WITH AMENDMENTS (1204 survives; contract completion specified)

Codex verified 1204's minimality (removing the added token restores both old
validator bodies byte-for-byte) and accepted the selector widening as
necessary under S:215–230 (enumeration selects by `(agent, relation,
object_role)` — a contract that admits the role in records but refuses it in
selectors cannot select its own records). The widening extends the allowed
interpretive vocabulary; it does not establish P5 semantics and removes no
contact/coverage/prerequisite/sealing/provenance/membership constraint.

**Proposed spec text (amend the `relationship_record` section's role vocabulary):**

> `object_role` admits `'av_qualifier'`: the aṣṭakavarga qualifier — the
> house-span whose BAV/SAV bindu strength qualifies a P5 window (P5a AV-quality
> / P5b SARVA-floor). Contract for its use:
>
> - **Form identity:** an `av_qualifier` relationship record represents a
>   **real transit interval** (the transiting agent's residence in the
>   qualified house-span) and carries the qualification's lineage (the AV
>   declaration consumed, the bindu figures, the convention). It **shares the
>   physical contact/root** with other interpretations of that same transit
>   and obeys S:194–207's within-path root reduction — the record is an
>   interpretation edge on existing physical evidence, never a duplicate of
>   it. A static BAV/SAV measurement alone is **operand evidence**; it never
>   mints a physical record of its own.
> - **The record never manufactures admission.** Its existence is not evidence
>   that any event occurred; admission still runs the path's full predicate
>   chain. Event-class and affected-person applicability must be declared per
>   path: an AV declaration's existence cannot establish occurrence of every
>   event class.
> - **P5a vs P5b stay distinct:** their outcomes and their missingness are
>   recorded separately (no accidental merging or double counting); P5a's
>   known-zero adverse result is reported against its (unresolved) nonzero
>   comparator honestly; P5b's cited bands are used as cited, never converted
>   into a universal multiplier.
> - **AV-build convention:** the exact AV build convention and declaration
>   consumed are named per record. Migration 1157:39–47 explicitly leaves the
>   declaration-consumption/citation gate to the writer/evaluator and the
>   meaning of its convention key unresolved; 1204 does not close that gap —
>   the writer/evaluator contract above is what closes it, and P5 DB writes
>   hold until the gate confirms it (steward M20261001T121451-1a8d stands).
>
> **Test obligation:** real residence-qualification acceptance against
> 1153–1157 **plus** 1204 (the review found the PR's AV fixture used a
> conjunction rather than the proposed house-span residence — the replacement
> test must exercise an actual span residence), and the v1.0 role vocabulary
> probed **in full**, not only `karaka`.

**Schema impact:** migration 1204 (in PR #2817, kept) — `kgrr_object_role_ck`
and `ka_gochara_object_selector_ok` each widened by the single value.

---

## AM-8 — D1: P6 frame — **REWORKED: no shared-validator arm; a context-specific P6 testimony template** (v0.1 REJECTED; 1205 SPLIT OUT of #2817)

Codex rejected the `ka_gochara_frame_ok` arm: it would permit unresolved
`'inherited'` frames on arbitrary paths and on relationship records **including
scored rows** (the PR's own positive test inserted `path_id=P6,
frame_kind=inherited, operator_role=scored, score_rule=within_path_product`
and expected success — contradicting S:385–393, which makes every P6 operator
testimony), and it evades 1155:527–528's exclusion of the native Moon frame
for relatives (`frame_kind <> 'moon'` — an unresolved `'inherited'` whose
effective frame IS Moon bypasses the check). It also provided no annotation
linkage: 1156:334–363 requires a window and its member record to share path
and version, so a P6 record cannot simply join a P1–P5 window.

**Disposition:** migration **1205 is split out of #2817** (the steward's
permitted alternative, M20261001T171150-5c70). No frame-validator change ships
now. The contract below is what a future migration must implement, landing
with the `day_on_demand` step:

> P6 day-resolution rows are **testimony templates**, represented in a
> **context-specific structure** (not the shared frame validator):
>
> - inheritance is admitted **only** on P6 testimony rows; every non-P6 use,
>   and every P6 use with `operator_role='scored'` (or any score_rule), fails;
> - an annotation is **evaluated with the parent window's concrete frame,
>   frame argument and affected person**, resolved at annotation time — the
>   stored template references its parent; the *effective* frame is computed,
>   and an effective frame the contract forbids (e.g. the native Moon frame
>   for a relative, 1155:527–528) fails loudly, exactly as if it had been
>   written literally;
> - **parent linkage is mandatory**: an absent parent fails; the parent must
>   be an admitted window of the same chart and generation;
> - **sealed-generation behaviour**: annotating against a sealed generation
>   writes no membership and mutates nothing sealed — the annotation is an
>   ephemeral response object or a separate annotation relationship with its
>   own table, never a member of the parent's window (1156:334–363's
>   same-path-and-version rule is not weakened);
> - the validator vocabulary of `ka_gochara_frame_ok` stays exactly the v1.0
>   four kinds until such a designed migration lands.
>
> **Test obligations (for that migration):** non-P6 inheritance rejected;
> scored P6 rejected; absent parent rejected; forbidden effective relative
> frame rejected; sealed-parent annotation produces the ephemeral/annotation
> object with zero membership writes; a resolved concrete frame recorded on
> the annotation.

**Schema impact:** none now. The future template migration is new and
protected-window if it touches any live CHECK.

---

## AM-9 — FINDING for the L0 owner: Rāhu/Ketu favourable-house discrepancy — ACCEPTED WITH AMENDMENTS (provenance narrowed per Codex)

Codex confirmed the reading (`CORPUS_READS_v1_0.md:130–137` supports {3,6,10,11}
from the Moon: the Sun's placements, the universal eleventh, the nodes'
similarity to the Sun; the L0 seed omits both 10s and adds Ketu-12) and
narrowed the owner finding in two ways, both folded:

**The finding (as narrowed):**

- Phaladīpikā XXVI.2 (PG321:C1) supports the **favourable placements** {3, 6,
  10, 11} from janma-rāśi for both nodes. The L0 seed's node rows combine
  three claims under one citation — the favourable placement, a
  `vedha_house`, and detailed phala. **XXVI.2 sources only the first.** The
  owner finding must keep the three provenances separate: repairing the
  favourable set (add Rāhu-10, Ketu-10) does NOT thereby source the node
  house-vedha pairs or every detailed outcome, and no compound row's citation
  is replaced wholesale.
- **Ketu-12:** its current citation `BPHS_CH29` is, on the inspected evidence,
  a **generic transit-results label**, and the file's own header records that
  attribution as unresolved in the served corpus. (v0.1's stronger claim —
  that BPHS_CH29 specifically denotes a node-over-Moon affliction passage — is
  **retracted**: it is not established by the inspected evidence.) Ketu-12
  needs a precise supporting source or an honest reclassification, preserving
  the historical lineage of the row.
- **No nodal dṛṣṭi follows from this finding.** No production repair is
  authorized by the review or by this draft; disposition belongs to the L0
  owner (repair the two 10s with the XXVI.2 citation; source or reclassify
  Ketu-12; keep vedha/phala provenance separate).

**Disposition unchanged in kind:** a finding for the **L0 owner**; no change
to the v1.5 specs or the P2 registry — `favourable_houses.py` follows the text
and stays as merged. Per the review, this correction need not hold unrelated
P1–P5 implementation work once the blocking contracts (AM-3/AM-5/AM-8) are
repaired.

---

## Batch checklist for the A5.5 gate (v0.2)

| # | Item | Spec fold | New migration? | Decision left? |
|---|------|-----------|----------------|------------------|
| AM-1 | Convention row, exact serialization; convention-id ≠ generation | §6.0 (new) | no (data row, own bootstrap txn) | no |
| AM-2 | sha256→UUIDv8, canonical bytes, collision taxonomy, vectors | §6.1 | no | no |
| AM-3 | Two phases + **per-table persistence by publication state**; separate registry txn | §10.1 | no | no |
| AM-4 | Moon/day tier EPHEMERAL; transiting-Moon correction; post-seal lifetime | §6.2/§10.1 | no | no |
| AM-5 | Coverage ownership: `partition_key=event_class` + cross-path completeness | §10.1 | no | no |
| AM-6 | **`sad_bala_sufficient` v1.0 — Option C as qualified** | factor catalogue | **no** | **picked: C** |
| AM-7 | `'av_qualifier'` + P5 contract (identity/applicability/lineage; no manufactured admission) | relationship_record | **1204 (kept), protected window** | no |
| AM-8 | P6 testimony template with concrete resolved frame | new (template), lands with day_on_demand | **1205 SPLIT OUT — future designed migration** | no |
| AM-9 | L0 Rāhu/Ketu finding, provenance narrowed | none | no | L0 owner's ruling |

## Evidence corrections folded outside the items (Codex rank 7)

- **1204's header** overstated the race claim: the protected environment and
  deployment concurrency do NOT demonstrate existing writers are paused. The
  corrected claim (in the reworked #2817): the transactional `ALTER TABLE`
  takes the requisite table lock with no committed unconstrained interval;
  concurrent writes can block or trip the lock timeout, and the window's
  quiescence is an operational precondition to be verified at dispatch, not a
  property the migration asserts.
- The oracle map v1.1's partial coverage stands as reported (11 REAL + 2
  strict-xfail sentinels); it is **not** behavioural closure — B6-F16's
  replacement must assert union admission, channel attribution and
  unknown-state behaviour; B6-F17's the actual tārā class, admitted-parent
  binding, coverage and zero scoring effect. The v1.5 batch by itself closes
  neither.
- The migration integration suite's `CONTRACT_FILES` omits 1156/1157 and its
  AV fixture is a conjunction, not a span residence — recorded as test debt
  against AM-7's obligation above.
