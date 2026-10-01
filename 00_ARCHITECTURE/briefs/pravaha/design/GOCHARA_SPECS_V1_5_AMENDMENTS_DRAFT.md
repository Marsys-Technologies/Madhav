---
artifact: GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT
version: 0.1
status: DRAFT — collects the A5.5-gate fold-in list; not a spec version
date: 2026-10-01
author: stream-B (spec lane; docs only — no code, no migration file)
sources: >
  steward M20261001T015412-6df0 (pins 3–7 ruled) and M20261001T121504-90d5 (this task);
  stream-B cited lookup M20261001T015350-644c; stream-A reports M20261001T080615-a232
  (D1 P6 frame, D2 sad_bala_summary) and M20261001T113409-04cd (D7 av_qualifier);
  steward acceptance M20261001T121451-1a8d; stream-B report M20261001T084457-5ceb
  (L0 Rāhu/Ketu discrepancy). Commits: da240d931 (A5.3 brief pins), 4f152e6ec
  (rule_binding), e1470d769/e40a1ff4b (P5 enumeration).
---

# GOCHARA_DESIGN_SPECS v1.5 — AMENDMENT LIST (draft)

Everything the A5.5 Codex gate must fold into `GOCHARA_DESIGN_SPECS_v1_5.md`, one
amendment per section. Each entry gives the source (message/commit), the evidence
(file:line), and the **exact proposed spec text**. Items AM-1…AM-5 are settled
implementation pins — fold verbatim. Items AM-6 (D2) and AM-7 (D7) need a gate
decision; AM-6 proposes options and deliberately does **not** pick one. AM-8 (P6
frame) needs one new frame-kind value. AM-9 is a **finding for the L0 owner**, not
a spec change — recorded here so the gate sees it in the same pass.

Migration discipline throughout: migrations 1153/1154/1155/1156 are applied and
**never edited**; every schema-side change below is a NEW migration, and each one
that touches a live CHECK constraint needs a **protected window**.

---

## AM-1 — Convention row for generation `'5.0'` (pin 3)

**Source:** steward pin 3, M20261001T015412-6df0; recorded in the A5.3 brief
(`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/A5_3_REGISTERED_WRITER_BRIEF_v1_0.md:22-47`,
commit da240d931, branch `pravaha/a53-registered-writer`).

**Why the fold:** v1.4 is silent on the convention row's *values* (dimensions only,
`GOCHARA_DESIGN_SPECS_v1_4.md:610`); migration 1153 declares the schema and inserts
no `'5.0'` row (`platform/migrations/1153_gochara_sky_event_substrate.sql:584-596`,
origin/main). The values below are the kernel's existing recorded constants, not
new choices.

**Proposed spec text (new §6.0 or amend §6.1):**

> The writer bootstrap inserts the `ka_gochara_sky_convention` row for
> `convention_id = '5.0'` **idempotently under the chart lock** (`ON CONFLICT DO
> NOTHING`; a row with that convention_id existing with ANY different field is a
> loud build failure). Values:
>
> - `ephemeris_generation` — the Swiss Ephemeris / pyswisseph build string the
>   kernel already records (`gochara_kernel/knots.py:169`,
>   `swe_version = getattr(swe, "__version__")`; on the governed runtime
>   `20230604`, `swe.version = 2.10.03`);
> - `ayanamsha = 'lahiri_chitrapaksha'` (kernel CONVENTION_VECTOR,
>   `step06_candidate_build.py:73`);
> - `node_convention` — the SAME convention L1 uses for 482012f1, read from
>   `chart_facts` and cited by fact_id (§N.5; never picked): **mean node**,
>   `graha_position` subjects `RAH_MEAN`/`KET_MEAN`, e.g. fact_id
>   `c520713087b97470` (matches kernel `node_model: "mean"`,
>   `step06_candidate_build.py:77`);
> - `grid` — the kernel's constants: 30° sign / 13°20′ nakṣatra / 3.75° kakṣya
>   including the 0°/360° seam (`gochara_kernel/contacts.py:13-15`,
>   `KAKSHYA_CELL_DEG = 3.75` at `convention.py:78`);
> - `method_version = '1.0.0'` (`step06_candidate_build.py:84`);
> - domain `1998-01-01 → 2085-01-01 UTC` (1153 self-test,
>   `1153_gochara_sky_event_substrate.sql:1243`).

**Schema impact:** none — the row is data under the existing table.

---

## AM-2 — §6.1 identity hash algorithm: sha256 → UUIDv8 (pin 4)

**Source:** steward pin 4, M20261001T015412-6df0; A5.3 brief lines 49-53.

**Why the fold:** v1.4 §6.1 pins the canonical *bytes* but not the *algorithm*
(`GOCHARA_DESIGN_SPECS_v1_4.md:615-622` — `physical_object_id =
hash(body, relation_kind, canonical_target, convention_id)`, `contact_id =
hash(physical_object_id, occurrence_ordinal)`; rounded-time/role hashing forbidden
:618-620; collision ⇒ loud build failure :628-629). 1153 stores plain UUID PKs
with no digest function.

**Proposed spec text (amend §6.1):**

> The identity hash is **sha256 over the §6.1 canonical bytes, first 128 bits
> carried as a UUID with version-8/variant bits set** (kernel `canonical_digest`
> precedent; no SHA-1, no UUIDv5). A collision is a loud build failure. O-RX-1
> prints the identity bytes (`GOCHARA_TEST_ORACLES_v1_4.json:64`).

**Schema impact:** none — PK columns are already plain UUIDs.

---

## AM-3 — Writer two-phase substep grain (pin 5)

**Source:** steward pin 5, M20261001T015412-6df0; A5.3 brief lines 55-57.

**Why the fold:** v1.4 §10.1 names one writer family and idempotent
per-(chart_id × generation) delete-then-insert (`GOCHARA_DESIGN_SPECS_v1_4.md:802-805`)
but never states the ordered substep grain; O-RW-1's given ("built contact ledger +
window set", `GOCHARA_TEST_ORACLES_v1_4.json:372`) implies contacts precede windows.

**Proposed spec text (amend §10.1):**

> The writer runs in **two phases**. Phase 1: per-body boundary substrate +
> contacts. Phase 2: per `(event_class × path_id, rule_version)` evaluation
> emitting relationship records and windows. **Each substep is an idempotent
> delete-then-insert scoped chart × generation × its grain.**

**Schema impact:** none.

---

## AM-4 — Moon / day tier is EPHEMERAL (pin 6)

**Source:** steward pin 6, M20261001T015412-6df0; stream-B lookup
M20261001T015350-644c answer (6) — EPHEMERAL, not silent.

**Why the fold:** this is a *statement* fold, not a change: v1.4 already says Moon
events are generated on demand with a `moon_on_demand` coverage record
(`GOCHARA_DESIGN_SPECS_v1_4.md:655-658`, :807; O-SS-4
`GOCHARA_TEST_ORACLES_v1_4.json:281-284` requires count(*)=0 Moon rows in the
global substrate). The structural enforcement is already in the schema:
`kgse_body_domain_ck` excludes `'moon'` from the global substrate
(`1153_gochara_sky_event_substrate.sql:684-685`) while `kgc_body_domain_ck` on the
contact table includes `'moon'` (:1072-1073) — natal-Moon contacts fine, no
materialised Moon substrate.

**Proposed spec text (amend §6.2 / §10.1, one sentence each):**

> The Moon/day tier is **EPHEMERAL**: no materialised Moon rows in the global
> substrate (`kgse_body_domain_ck` enforces); a Moon search writes the
> `moon_on_demand` coverage record.

**Schema impact:** none.

---

## AM-5 — Coverage-partition ownership (pin 7)

**Source:** steward pin 7, M20261001T015412-6df0; stream-B lookup
M20261001T015350-644c answer (7) — SILENT in spec/oracles.

**Why the fold:** `kala_gochara_coverage` (migration 1081) is referenced by 1156
(`1156_gochara_eval_window.sql:14`) and read by 1155's composite FK +
`ka_gochara_record_coverage_guard` (`1155_gochara_relationship_record.sql:72-80`);
steward ruling 1 forbids any trigger on the legacy coverage table (1156:63).
v1.4's "Every no-window answer carries its coverage object" (:818) names no writer.

**Proposed spec text (amend §10.1):**

> The `ka_gochara_v5` writer owns the `'5.0'` `event_class` coverage partitions
> in `kala_gochara_coverage`: it inserts/extends its own partitions
> (chart × generation × `partition_kind = event_class` × `partition_key = path`,
> `completed_horizon` within the governed domain, `relations_searched`) **in the
> same transaction, before** the records/windows that FK them. Coverage is written
> by the same registered writer that writes the records.

**Schema impact:** none.

---

## AM-6 — D2: `sad_bala_summary` units — OPTIONS, no pick (gate decision)

**Source:** stream-A rule_binding report M20261001T080615-a232; deferral recorded
in `services/gochara_kernel/rule_registry.py:48-50` and :146 (commit 4f152e6ec,
branch `pravaha/a53-registered-writer`).

**The conflict:** Stream B's factor declares `units="rupas"`, `range=[0.0, 1.0]`
(`services/gochara_rules/registry.py:453-455`, branch `pravaha/b5-rule-paths`).
`rupas` is not in `kgf_units_ck`'s enum (`('degrees','days','count','unitless')` —
`platform/migrations/1154_gochara_rule_path_registry.sql:331`), and the range
`[0,1]` contradicts rūpa magnitudes (the cited pūrṇa-bala thresholds are 5–7
rūpas: Sun 6.5, Moon 6, Mars 5, Mercury 7, Jupiter 6.5, Venus 5.5, Saturn 5 —
Phaladīpikā IV.22–24, `PG79:C1`/`PG80:C1`, per
`design/PROMISE_NATURE_YOGA_MAP_v1_1.md:37`).

**Cited constraint on any fix:** the *binary* strong/weak predicate at the
pūrṇa-bala thresholds is `[D]`-cited; **any finer scaling is not**
(`PROMISE_NATURE_YOGA_MAP_v1_1.md:37`, registry.py:460-463). A silent re-unit is
forbidden (fix the data, not the detector — ADK-0026, rule_registry.py:48-51).

**Option A — extend the DB units enum (new migration).** Add `'rupas'` to
`kgf_units_ck` via a NEW migration (1154 is applied and never edited; the CHECK
swap needs a **protected window**). Spec text: `sad_bala_summary` keeps
`units='rupas'`; range becomes `[0, +∞)` (or the range key is dropped); the
pūrṇa-bala thresholds remain the cited decision points. Cost: one schema
migration for one factor; the honest unit is preserved.

**Option B — re-encode as a unitless ratio against the cited threshold.** Factor
value = operand value ÷ the graha's cited pūrṇa-bala threshold, `units='unitless'`,
`range=[0,1]` where 1.0 = pūrṇa-bala exactly (values > 1 clamp or carry a flag).
No migration. Cost: the stored number is a derived ratio, not the L1 operand; the
spec must state the transform and that only the threshold crossing is cited — the
ratio's gradations carry no doctrine.

**Option C — split the factor.** (i) A binary factor `sad_bala_sufficient`
(`function='step'`, `units='unitless'`, range `{0,1}`) carrying the cited
threshold predicate — this is the only scored surface; (ii) the raw rūpa magnitude
rides as operand payload outside the factor range contract, never scored. No
migration. Cost: two catalogue entries where the doctrine reads as one summary.

**Recommendation:** none — the gate picks. Stream B's doctrinal note: the cited
content is the threshold predicate; any encoding that keeps *that* binary and
labels everything finer as uncited is doctrinally safe.

---

## AM-7 — D7: `object_role = 'av_qualifier'` — NEW migration, protected window

**Source:** stream-A contract-gap report M20261001T113409-04cd; steward acceptance
M20261001T121451-1a8d (item 4: joins the v1.5 contract-amendment batch; P5 DB
writes hold until then; no CHECK weakened).

**The gap:** P5 enumeration carries `object_role='av_qualifier'`
(`services/gochara_kernel/evaluator.py:512`, D7 note at :53-56, commits
e1470d769/e40a1ff4b), which is NOT in `kgrr_object_role_ck`'s v1.0 vocabulary
(`'lord','occupant','karaka','dispositor','maraka_of_house','period_lord',
'yoga_constituent','pada','signature_house'` —
`platform/migrations/1155_gochara_relationship_record.sql:537-539`).

**Proposed spec text (amend the `relationship_record` section's role vocabulary):**

> `object_role` admits `'av_qualifier'`: the aṣṭakavarga qualifier — the
> house-span whose BAV/SAV bindu strength qualifies a P5 window (P5a AV-quality /
> P5b SARVA-floor). Carried at enumeration with the honest name; never a
> mislabelled role to fit a CHECK.

**Schema impact (stated, not executed here):** requires a **NEW migration**
extending `kgrr_object_role_ck` with `'av_qualifier'`. Migration 1155 is applied
and **never edited**. Because the CHECK is being swapped on a live table the
writer family writes to, the migration needs a **protected window** (writer paused
or the window where no `'5.0'` write can race the constraint swap). Until that
migration lands, P5-grain DB writes hold (steward M20261001T121451-1a8d).

---

## AM-8 — D1: P6 frame value — one new frame-kind

**Source:** stream-A rule_binding report M20261001T080615-a232; deferral at
`rule_registry.py:45-47` (D1) and :76.

**The gap:** the spec gives P6's frame as the prose **"per the admitting path's
objects"** (`GOCHARA_DESIGN_SPECS_v1_4.md:385-391`; registry row at
`services/gochara_rules/registry.py:578`), which is no value of
`ka_gochara_frame_ok` — the function admits exactly `'moon'`, `'lagna'`,
`'dasha_lord'`, `'graha'` (arg ∈ 9 grahas), `'bhavat_bhavam'` (arg ∈ 1..12)
(`platform/migrations/1154_gochara_rule_path_registry.sql:177-189`).

**Proposed spec text (amend §2.2 P6 entry and §0 frame enum):**

> P6's frame is the frame of the path whose admitted window the day row
> annotates: a new frame-kind **`'inherited'`** (arg NULL) — "the admitting
> path's frame, resolved at annotation time." P6 being testimony, the frame never
> scopes a scored window of P6's own; it names where the day-resolution row
> hangs. Counting rules of the inherited frame apply unchanged.

**Schema impact:** `ka_gochara_frame_ok` needs a `WHEN 'inherited' THEN frame_arg
IS NULL` arm — a NEW migration over 1154 (protected window as AM-7; the two can
ride one migration). P6 binds with the `day_on_demand` step (pin 6, EPHEMERAL), so
the gate may sequence this fold with that step rather than with P1–P5.

---

## AM-9 — FINDING for the L0 owner: Rāhu/Ketu favourable-house discrepancy (not a spec change)

**Source:** stream-B report M20261001T084457-5ceb (PR #2812, branch
`pravaha/b5-p2-favourable-houses`, `services/gochara_rules/favourable_houses.py`).

**The finding:** Phaladīpikā XXVI.2 (PG321:C1) — "Rāhu and Ketu are similar to the
Sun" — gives both nodes the Sun's favourable set **{3, 6, 10, 11}** from janma-rāśi
(`favourable_houses.py:45-67`, all entries `state: 'cited'`, read verbatim from the
served corpus 2026-10-01). The L0 seed
(`platform/python-sidecar/brahmagyan/l0_transit.py`, branch
`pravaha/b5-p2-favourable-houses`) instead carries:

- Rāhu favourable rows **{3, 6, 11}** — house 10 **omitted**
  (`l0_transit.py:758-784`), each cited `RAHU_KETU_HOUSE_VEDHA_UNSOURCED`;
- Ketu favourable rows **{3, 6, 11}** plus an extra **12th-house** row
  (`l0_transit.py:841-875`), the 3/6/11 rows cited
  `RAHU_KETU_HOUSE_VEDHA_UNSOURCED`, the 12th cited `BPHS_CH29`.

So against the śl.2 equivalence, L0 (a) misses Rāhu-10 and Ketu-10, and (b) adds a
Ketu-12 favourable row with no Phaladīpikā basis (its BPHS_CH29 citation is for a
node-over-Moon affliction class, not a favourable 12th). L0's own header already
records that no Rāhu/Ketu house-vedha doctrine was found anywhere in the corpus
(`l0_transit.py:80-82`, `RAHU_KETU_HOUSE_VEDHA_UNSOURCED`), which makes the
PG321:C1 śl.2 equivalence the strongest available source for the favourable sets.

**Disposition:** a finding for the **L0 owner** to rule on (repair rows 10; justify
or drop Ketu-12; upgrade the favourable-set citations from UNSOURCED to
Phaladīpikā XXVI.2 PG321:C1). **No change to the v1.5 specs or to the P2
registry** — `favourable_houses.py` follows the text and stays as merged.

---

## Batch checklist for the A5.5 gate

| # | Item | Spec fold | New migration? | Decision needed? |
|---|------|-----------|----------------|------------------|
| AM-1 | Convention row values | §6.0/§6.1 | no (data row) | no — pin, fold verbatim |
| AM-2 | sha256→UUIDv8 identity | §6.1 | no | no — pin |
| AM-3 | Two-phase substep grain | §10.1 | no | no — pin |
| AM-4 | Moon/day-tier ephemeral | §6.2/§10.1 | no | no — pin (statement) |
| AM-5 | Coverage-partition ownership | §10.1 | no | no — pin |
| AM-6 | D2 `sad_bala_summary` units | factor catalogue | option A only | **yes — pick A/B/C** |
| AM-7 | D7 `'av_qualifier'` role | relationship_record | **yes (kgrr_object_role_ck), protected window** | no — accepted by steward |
| AM-8 | P6 frame `'inherited'` | §0/§2.2 | **yes (ka_gochara_frame_ok), may ride AM-7's migration** | no — binds with day_on_demand |
| AM-9 | L0 Rāhu/Ketu discrepancy | none | no | L0 owner's ruling |
