---
artifact: A5_3_REGISTERED_WRITER_BRIEF
version: "1.0"
author: "Stream A (Karma) — Kimi Code"
date: "2026-10-01"
status: ACTIVE
branch: pravaha/a53-registered-writer
---

# A5.3 — Registered ka_gochara writer (ka_gochara_v5, generation '5.0')

Campaign item **A5.3**: the registered `'5.0'` gochara writer — three objects, per-path pruning,
interval sweep with interior extrema, day tier on demand (closes Disclosure 3). Steps:
`geometry_store` → `rule_binding` → `window_evaluator` → `interval_sweep` → `day_on_demand` →
`writerbase_conformance`. Delivery: small PR sequence, **geometry store first** (steward
M20261001T015412-6df0). Spec text is NOT amended by this brief; the pins below fold into the
frozen specs' v1.5 at the A5.5 Codex gate.

Current state on this branch: inert `ka_gochara_v5` skeleton (WriterBase-conformant, chart-scope
refusal, every execution path NotImplementedError) — pins 1–2 per steward M20261001T014547-357e.

## Implementation pins (steward 2026-10-01, M20261001T015412-6df0)

These are IMPLEMENTATION PINS for the frozen specs' silent points, ruled by the steward from
Stream B's cited lookup M20261001T015350-644c. Recorded verbatim in substance; spec text gets
folded into v1.5 at the A5.5 Codex gate, not now.

**(1–2) Identity surface (M20261001T014547-357e):** asset_id `ka_gochara_v5`; generation `'5.0'`
(candidate discipline as ruled for the family — no flip without D-FLIP).

**(3) Convention row.** The writer bootstrap inserts the convention row **idempotently under the
chart lock** (`ON CONFLICT DO NOTHING`; if a row with that convention_id exists with ANY different
field → loud failure). Values:

- `ephemeris_generation` — the exact Swiss Ephemeris / pyswisseph build string the kernel already
  records: `gochara_kernel/knots.py:169` records `swe_version = getattr(swe, "__version__")`;
  on the governed runtime this is **`20230604`** (pyswisseph build; `swe.version` = `2.10.03`,
  Swiss Ephemeris release — recorded alongside where the kernel surfaces it).
- `ayanamsha` = **`lahiri_chitrapaksha`** (matches the kernel's CONVENTION_VECTOR,
  `step06_candidate_build.py:73`).
- `node_convention` = the SAME node convention L1 uses for 482012f1 — **mean node**, read from
  `chart_facts` (L1 is the authority, §N.5; never picked): `graha_position` subjects are
  `RAH_MEAN`/`KET_MEAN`, e.g. **fact_id `c520713087b97470`** (`graha_position` /
  `longitude_sidereal` / subject `RAH_MEAN`, source `pyjhora_adapter.positions/pyjhora/1.0.0`).
  Matches the kernel's `node_model: "mean"` (`step06_candidate_build.py:77`).
- `grid` and `method_version` = the kernel's existing constants: the 30° sign / 13°20′ nakṣatra /
  3.75° kakṣya grids including the 0°/360° seam (`gochara_kernel/contacts.py:13-15`,
  `KAKSHYA_CELL_DEG = 3.75` at `convention.py:78`); `method_version = "1.0.0"`
  (`CONVENTION_VECTOR`, `step06_candidate_build.py:84`).
- Domain **1998-01-01 → 2085-01-01 UTC** (migration 1153 self-test).

**(4) Identity.** `sha256` over the §6.1 canonical bytes, first 128 bits as a UUID with
version-8/variant bits set (kernel `canonical_digest` precedent; no SHA-1/UUIDv5). Collision ⇒
loud build failure. O-RX-1 prints the bytes.

**(5) Two-phase grain.** Phase 1: per-body boundary substrate + contacts. Phase 2: per
(event_class × path_id, rule_version) records + windows. Each substep is an idempotent
delete-then-insert scoped **chart × generation × its grain**.

**(6) Moon / day tier: EPHEMERAL.** No materialised Moon rows in the global substrate
(`kgse_body_domain_ck` already enforces it); write the `moon_on_demand` coverage record.

**(7) Coverage partitions.** Owned by the `ka_gochara_v5` writer, written in the SAME transaction
**before** the records/windows that FK them.

## Step `rule_binding` (landed 2026-10-01)

Design and encoding decisions live with the code in
`services/gochara_kernel/rule_registry.py` (E1–E6; deferrals D1/D2). Summary:

- New substep **`rules`**, FIRST in the plan (`rules` → `convention` → `body:<Body>` ×8).
  It binds Stream B's P1–P5 catalogue (`services/gochara_rules/registry.py`, rule_version
  `1.0.0`) into migration 1154's tables — 8 predicates, 11 factors, 5 paths, 7 prerequisite
  + 9 soft-factor membership rows, 5 F3 seals — insert-if-absent with full-field equality;
  ANY divergence is a loud `RegistryDivergenceError` (ADK-0026).
- Lock order (N13): the `rules` substep takes **no chart lock** — the registry tables ride
  the Gochara-5 GLOBAL family key (write-guard triggers), mutually exclusive with any chart
  key. The orchestrator commits per substep, so this substep is its own transaction.
- **Deferred (flagged to the steward):** P6 (frame "per the admitting path's objects" is no
  `ka_gochara_frame_ok` value; binds with `day_on_demand`) and `sad_bala_summary` (units
  "rupas" violates `kgf_units_ck`; spec fold for v1.5 — never a silent re-unit).
- **Phase-2 record grain (pin 5):** record/window-producing substeps are scoped
  per **(event_class × path_id, rule_version)** — idempotent delete-then-insert scoped
  chart × generation × event_class × path. The static enumeration is the 26 scored classes
  (27 minus `birth_anchor`, O-CF-N6) × the bound paths P1–P5; the H-unknown eight admit
  `unqualified` (§2.2). This grain lands with `window_evaluator` / `interval_sweep`.

## Step `window_evaluator` (1/N landed 2026-10-01)

Grain (pin 5 phase 2): `record:<event_class>:<path_id>` — the 26 scored classes
(27 minus `birth_anchor`) × the bound paths. Landed in this increment (pure
machinery only; **no DB writes** — transit records FK their contact ledger row
(kgrr_transit_natal_ck), so rows are written only when contacts materialise):

- `services/gochara_kernel/chart_context.py` — L1 chart_facts loader (lagna +
  nine natal λ + source fact_ids; conflicts/missing NAMED, never defaulted).
- `services/gochara_kernel/evaluator.py` — P3/P4 edge enumeration (S-03 union;
  R3-S02 restriction to Jupiter/Saturn; N-14 node aspects absent; māraka
  testimony rows D-PADMIT; H-unknown classes enumerate zero edges with the
  grain's admission recorded `unqualified`). Binding decisions E7 (record uuid8
  over records.py's canonical natural key), E8 (object conventions per the
  kgpo vocab), E9 (source_page locator fallback) documented in the module.
  Deferral D3: P1 non-node dispositorship/association rows are unwritable
  until ruled (uncited_extension without ruling_ref violates kgrr_ruling_ck).
- Unimplemented paths (P1/P2/P5) refuse LOUDLY — never a silent empty grain.

Remaining increments: P2/P1/P5 enumeration (P1 needs the §4.0 dasha context);
contact materialisation (physical solves per contract §6 #2, reusing the
kernel's boundary solver; residence spans from substrate ingress pairs);
then DB writes per grain (coverage partition FIRST in the same transaction,
pin 7) and prerequisite `result` evaluation at materialisation.

## Delivery sequence (steward M20261001T015412-6df0)

1. This brief.
2. Geometry store PR (step `geometry_store`) — queues behind #2799's rebase (done 2026-10-01,
   head `cb004ff00`).
3. Then `rule_binding` → `window_evaluator` → `interval_sweep` → `day_on_demand`, one step at a
   time with `$P step` evidence; `writerbase_conformance` completes last.

## Standing constraints

- Production writes only on the governed path; no local century enumeration (ADK-0028).
- '5.0' is a candidate generation: no flip without D-FLIP; '3.0' stays the rollback surface.
- Fix the data, not the detector (ADK-0026); a failed gate yields a new candidate, never a patch.

## Step `interval_sweep` — contact materialisation design (v1.0, 2026-10-01)

Plan extension (pin-5 grain): after the body substeps, per-grain record substeps
`record:<event_class>:<path_id>` over the static enumeration (26 scored classes ×
P1–P5), then `window:<event_class>:<path_id>` for the sweep itself. One
substep = one transaction (the orchestrator commits per substep).

Contact materialisation per grain (`record:` substep):

1. Enumerate edges — `evaluator.enumerate_edges(event_class, path, chart)` with
   the chart context from L1 chart_facts (`chart_context.py`; conflicts/missing
   NAMED, never defaulted).
2. Solve contacts per transit edge over the requested horizon:
   - `residence` on `span:sign:<X>` — from the substrate's `sign_ingress`
     sky events for that body (the A2 global boundary table, read-only):
     a span is [ingress into X, egress), re-entering on retrograde loops;
     a contact overlapping the horizon whose exact instant lies outside is a
     TRUNCATED span (t_exact NULL per 1152), never absence (Tier-0-G
     `truncated_contacts_kept`).
   - `conjunction` / `return` / `drishti_contact` on `point:<λ>` —
     `contacts.find_roots` with levels per relation (dṛṣṭi: body at
     target − angle; nodes cast none, N-14), bracketed from the arc index,
     swiss_refined at the instant (plan §4.2).
   - natal-fact edges (transit=False) — no solve; one record, contact_id NULL.
3. Occurrence ordinals — `substrate.assign_occurrence_ordinals` per physical
   object; contact_id = `ledger.compute_contact_id` over the pinned key.
4. Records — one per occurrence (transit) / one per edge (natal fact);
   record_id = `evaluator.record_uuid(natural_key)` (E7); `precision` restated
   from the contact (N7); `temporal_support_*` = the span (state `computed`),
   or `computed_empty` where the solve found no occurrence — a state, never an
   omission; `admission_state` finalised at COMMIT (F5, migration 1155).
5. Prerequisite `result` evaluation at materialisation into
   `ka_gochara_record_prerequisite` (the trigger's `result_only` path):
   `period_running_at` per occurrence against the §4.0 dasha rows (P1);
   `av_polarity_declaration_exists` joined and recorded in lineage (P5,
   O-BP-3, migration 1157); `p4_double_transit` overlap of the Jupiter/Saturn
   contacts (P4, R3-S02).
6. Coverage FIRST in the same transaction (pin 7): partition_kind
   `event_class`, key `<event_class>:<path_id>`, horizon + relations_searched +
   per-state counts + `unavailable_inputs` named (e.g. the P5c donor matrix).

### Design v1.1 (2026-10-01, 2/N implementation — what the applied contract taught)

The disposable-PG rehearsal of v1.0 surfaced four divergences between the design
and the FROZEN, already-applied artefacts. The frozen side won every time (ADK-0026:
fix the data — here, the writer's own design — never the detector). No CHECK
weakened; the v1.5 batch is untouched.

1. **`span:<sign>`, not `span:sign:<sign>`.** Spec v1.4 §6.1 renders span targets
   `span:<sign>` and 1153's `kgpo_target_form_ck` admits exactly
   `^span:[a-z0-9_]+$`. `evaluator._span_target` and the materialise assertions
   were aligned (single colon). Pre-writes, so no stored identity changes.
2. **F7: the `event_class` coverage key IS the class.** 1155's
   `ka_gochara_record_coverage_guard` rejects any other key. The per-grain
   `<class>:<path>` key in v1.0 item 6 is REPLACED by a `coverage:<event_class>`
   substep owning ONE class-level partition (the class's whole-generation
   declared search over every bound path, deterministic from the static
   enumeration, insert-if-absent + byte check). Record grains only BIND to the
   stored partition and REFUSE without it (`MissingCoverageError`). Pin 7 holds
   as existence-before-records; per-grain detail rides WriterResult notes.
3. **F5: prerequisite membership is read, never guessed.** Records mint their
   `ka_gochara_record_prerequisite` rows from the seeded
   `ka_gochara_rule_path_prerequisite` declaration (ordinal order); the grain
   fetches it when the caller does not supply it.
4. **Pin-3 tz false divergence fixed.** `substrate.register_convention`
   formatted the stored `timestamptz` domain in the session tz with a `Z`
   suffix — any non-UTC session fabricated a divergence. Now compares in UTC.

Also in 2/N: `record_store.py` (RecordStore + write_class_coverage +
materialise_record_grain), contact rows clipped per kgc (coverage.truncated ⇔
t_exact NULL; end-clipped spans carry their exact ingress with t_out = horizon),
resolution = max crossing ε actually read (0.0 = named non-claim), records
insert with `admission_state`/`outcome_valence` 'unqualified' and prerequisite
results NULL (unknown) — result EVALUATION (v1.0 item 5) is 3/N scope with the
point solves. Tests: tests/l3/gochara/test_a53_record_store.py — 9 fake-store +
2 disposable-PG (GOCHARA_A53_DSN, default postgresql://wp6:local@localhost:55434/a53;
the chain 1081+1152–1157 applied verbatim; NOT_RUN skip when unreachable).

The sweep (`window:` substep): per grain, admitted windows = the union of
scored-edge support intervals whose prerequisites pass; peaks = interior
extrema of the activity kernel within each window (§7.2 inv 2); era/month are
output resolutions of the paths at those grains (§2.3 inv 4 — never a clipped
curve); day rows only via P6 on demand (M-3) — the `day_on_demand` step.

Open bindings (flagged, never silently resolved):

- D7: P5 `object_role='av_qualifier'` is outside `kgrr_object_role_ck` v1.0 —
  reported to the steward (M20261001T113409-04cd) for the v1.5 contract fold;
  P5 grain DB writes hold until then. Enumeration carries the honest name.
- P5c donor matrix: pending the native-authorised ga_strength rebuild (#2731);
  D4 stands.
- `period_running_at` operand — CONFIRMED 2026-10-01 (3/N): the source is
  `public.chart_dashas` (`chart_id`, `ayanamsha_id`, `system_id`,
  `level_n ∈ {1,2,3}` = MD/AD/PD per spec §2.1, `lord_graha`, `start_iso`,
  `end_iso`), read through the platform's existing defensive reader
  `services/gochara_grammar/dasha_data.fetch_dasha_periods_multilevel`
  (9 live systems in store; P1 evaluates `vimshottari` per the operand
  selector `l1:dasha_periods`). The evaluation itself lands with the
  prerequisite `result` evaluation (item 5), 3/N scope.

## v1.5 contract-amendment batch (A5.5 gate) — one list

Per the steward's ruling (M20261001T121451-1a8d item 4, 2026-10-01T12:14:51Z),
the frozen-spec v1.5 amendment batch at the A5.5 gate is tracked as exactly
these three items. No CHECK is weakened for any of them; affected DB writes
hold until the fold lands.

1. **D7 — P5 `object_role='av_qualifier'`** joins the `kgrr_object_role_ck`
   vocabulary (accepted as proposed in M20261001T113409-04cd). P5 grain DB
   writes hold until then; enumeration carries the honest name.
2. **P6 frame value** for the admitting path's objects — `ka_gochara_frame_ok`
   carries no value for "per the admitting path's objects" (deferred at
   `rule_binding`; binds with `day_on_demand`).
3. **`sad_bala_summary` units** — "rupas" violates `kgf_units_ck`; the spec
   fold names the unit for v1.5 (never a silent re-unit).

Deferred alongside but NOT contract amendments: the P5c donor matrix (D4,
awaits the native-authorised `ga_strength` rebuild) and the P5d/P5e forms
(D5/D6). The `period_running_at` dasha-row source is CONFIRMED (above).

**OPEN ITEM — AM-1 ephemeris provenance (steward M20261001T182032-5d5b,
2026-10-01):** Suvarṇa's EPHEMERIS finding (PR #2840) shows production L1
chart_facts/panchanga_daily were computed on MOSHIER (image sets only
SWE_EPHE_PATH, which the C library ignores; SE_EPHE_PATH unset), while
gochara contact/convention rows are on swieph (~1 arcsec Moon, ~25 arcsec
TRUE_NODE divergence). The '5.0' convention row's node/ephemeris provenance
must therefore name the backend ACTUALLY USED BY L1 for each cited fact —
never a blanket "swieph". Bind at convention-row materialisation
(`geometry_store`/`rule_binding` write path) once Suvarṇa's shared locked
path helper lands on main; adopt that helper for the kernel's ephe
resolution at the same time. The gochara kernel itself already fails closed
on any non-swieph backend (`knots._check_retflag` raises) — unchanged.

**OPEN ITEM — build ordering: the L1 rebuild comes first (steward
M20261001T194030-8c0f, 2026-10-01):** Suvarṇa's `.se1` boundary-flip report for
482012f1: zero class flips, all seven birth anchors hold, largest input move
0.665 arcsec (Moon), and **Vimshottari period starts shift +6,993 s**. After the
L1 rebuild the daśā build that `period_running_at` / `p4_double_transit` read
(`public.chart_dashas` via `fetch_dasha_periods_multilevel`) is a NEW build id
with slightly different boundaries. Every `'5.0'` row that depends on the daśā
build — and the A2.5 `'4.1'` candidate — must be built AFTER that rebuild,
never straddling it. Rehearsals on the scratch DB before then are shape-proofs
only, never evidence of boundary values. (A2.5 record:
`A2_5_BUILD_ORDERING_NOTE_v1_0.md`, PR #2799.)

**NOTE — kernel Moon backend gate (same message, PR #2799):** the Moon's own
returned flag cannot prove the Swiss backend (semo missing ⇒ Moshier Moon, SWIEPH
flag still set). `knots.calc_sidereal_lon` now probes TRUE_NODE at the same
instant for every Moon calc and raises `EphemerisBackendError` otherwise; the
`'5.0'` writer inherits this through the kernel once #2799 is on main — nothing
to add here except that the AM-1 sentence above ("already fails closed") is now
true for the Moon too.

### Design v1.2 (2026-10-01, 3/N part 2 — point solves landed)

`conjunction`/`aspect` transit edges on `point:<λ>` targets now solve:
roots per relation level via `contacts.find_roots` (dṛṣṭi: body at target −
angle; N-14 nodes excluded at enumeration), Swiss-refined, ordinals over the
FULL convention domain (`substrate.assign_occurrence_ordinals`), span = the
in-orb interval at the pinned WP1 §7 orb (orb_conj_slow / orb_drishti_slow,
1.0°) derived ARC-LOCALLY around each root — deliberately not
`episodes.in_orb_intervals`, which resolves one unwrapped representative per
SEGMENT and silently misses every other revolution's band on stationless
bodies (reported to the steward 2026-10-01, M20261001T172758-6f81 — ruling
on the kernel fix's scope/sequencing is pending). Horizon discipline is the
A2 v1.1 half-open rule: an overlap only at the excluded end is not a span;
an exact centre outside the horizon with an overlapping interval is a
TRUNCATED contact (t_exact NULL, clipped_truncated), never absence.
Class coverage now names conjunction/aspect as searched when the arc index
is available (resolution includes the 1.0-arcsec index tolerance, N7) and
the deferral only when it is not. The writer builds one full-domain arc
index per body lazily per grain (Swiss knots, retflag asserted).

Tests: tests/l3/gochara/test_a53_record_store.py — 18/18 (fake-store:
conjunction full chain, aspect direction mutation detector, O-RX-1
retrograde ordinals, truncated-beyond-horizon + excluded-end control,
no-index deferral, coverage naming; disposable-PG: Swiss-refined Sun
conjunction through the real CHECK chain, full-domain ordinal 29 for the
2026 crossing, idempotent rerun). Failing-first: the 7 new point tests +
2 updated PG tests fail against the pre-change sources (9 failed / 9
passed). The shared a53 scratch DB's pre-3/N '5.0' rows were wiped (scratch
only, deterministic identities re-minted).

### Design v1.3 (2026-10-02, 3/N part 3 → v1.5 amendments AM-1/AM-2/AM-3 folded)

The Codex-accepted v1.5 amendment draft (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.5,
steward M20261001T201843-5359) supersedes the original pins 3–7. What landed against it,
and what is waiting:

- **Part 3 (prerequisite results).** period_running_at (P1) and p4_double_transit (P4) are
  evaluated at materialisation through the 1155 `result_only` path. Two defects only the REAL
  COMMIT-time F5 finalisation could see were fixed: a result write must re-derive the record's
  `admission_state` (any false ⇒ not_admitted; else any unknown/unevaluated ⇒ unqualified; else
  admitted), and P4 records carry `path_id 'P4'` with P4's own provenance/ruling (shared
  geometry, once-per-path interpretation, §2.1). The §4.0 daśā pin is ONE implementation
  (`services/gochara_kernel/dasha_read.py`, step06a delegates; AM-10 re-pin rules apply to it).
- **AM-1.** The convention grid is `nakshatra:13d20m` (never the decimal 13.20); `convention_id`
  is the draft's `sha256:eac922d4…e7a3`, pinned by test. Caveat for the amendment: the legacy
  kala convention vector carries no grid/domain, so a future sky-convention correction cannot
  mint a distinct legacy row as AM-1's bridge-evolution sentence says (the 1:1 bridge refuses a
  second mapping).
- **AM-2.** `services/gochara_kernel/targets.py`: span targets are the absolute sign numeral
  (`span:7` = Libra), validated at `PhysicalObjectId` construction (rejects `span:libra`,
  `span:13`, `span:07`, `sign:7`, exponent points); one full-precision no-exponent point
  formatter (quantization stays F-3). The five pinned UUIDv8 vectors reproduce.
- **AM-3.** Candidate chart × generation rows are REPLACED in FK dependency order (window
  membership → windows → records → only-orphaned contacts → class coverage); a contact another
  path still references survives; a sealed generation is refused up front. Global tables stay
  insert-if-absent. (A rebuild with a new build id used to die on the coverage byte-check.)
- **Waiting on Stream B's AM-5 storage migration:** search-input snapshot, inventory, path pins
  with committed obligation sets, obligations, interval ledger, independent verifier. Until the
  table shapes land the writer keeps only the guard-facing event_class partition.
- **Open question (to the steward): which prerequisites are evaluated at materialisation.** Only
  period_running_at and p4_double_transit are. P1/P2/P3 records therefore stay `unqualified`
  (their other declared prerequisites are NULL) and only P4 can reach `admitted`, so a window
  sweep today yields admitted windows from P4 alone. `transit_relation` and
  `p3_contact_house_or_lord` are `declaration_exists` over the stored contacts and `house_from_moon`
  is `house_from` — each can be evaluated by READ-BACK against the stored rows (not by the minting
  loop); `natal_bhava_relationship` needs the chart's natal relation of the class period lord.

### Design v1.4 (2026-10-02) — the AM-5 inventory writer + independent verifier, against migration 1206 (PR #2867, HOLD)

Shapes read from `1206_gochara_search_inventory_completeness.sql` (Stream B; under Codex review —
NOT frozen). Code lands on a branch STACKED on #2867, not on the A5.3 branch.

**Grants.** 1206 §7 already grants `data_plane_builder` exactly what this writer needs:
SELECT/INSERT/DELETE on the six `ka_gochara_search_*` tables, `UPDATE (inventory_digest,
ledger_digest, finalized_at)` on the inventory header, and SELECT on `ka_gochara_generation_seal`
and `ka_gochara_av_polarity_declaration` (1216 deferred them). The writer additionally READS (all
already held): `chart_facts`, `chart_dashas` (the digest functions run as the invoker),
`kala_gochara_publication`, `ka_gochara_rule_path_seal`. No new grant is needed beyond 1206 §7 —
it ships in the same protected window as 1204.

**Plan (per generation, chart lock then global SHARED — AM-5 item 7).**
`manifest` (publish_candidate: the snapshot's vector is bound to the manifest row) → `snapshot`
(ONE per chart × generation; first deletes the whole inventory chain, dependency order) → per class
`inventory:<class>` (delete the class chain → header → pins (a TOTAL partition of the sealed
registry) → obligations (each in its pin's committed set) → interval ledger → one-shot FINALISATION
UPDATE, digests read from the DB's own functions) → `coverage:<class>` (the partition now READS the
stored inventory: horizon = inventory horizon, relations_searched = the obligations' distinct
relations — `partition_overclaims` is a seal violation) → `record:<class>:<path>` grains →
`verify:<class>` (independent verifier row). Sealing stays outside the writer (A6).

**Obligations** = the enumerated edges of each included path, 9-tuple
`class|path|ver|agent|relation|object_role|target|frame|person`, lowercase, `ob_id` = the AM-2
UUIDv8 (identical to `substrate._uuid8_of`; the DB recomputes and refuses a mismatch). Targets are
the AM-2 grammar (`span:7`, `point:λ`).

**Path pins.** P1–P4: `included` (committed set = its obligation ids) or `computed_empty` where the
derivation proves an empty qualified set; P5: `excluded / tier_withheld_by_ruling` (degrading — needs
a `ruling_ref`; the existing hold is steward M20261001T121451-1a8d); P6 is not in the sealed
registry (D1) so no pin. H-unknown classes (8 of 26: achievement_recognition, business_launch,
financial_deception, foreign_settlement, parental_event, property_acquisition, psychological_arc,
spiritual_turn) cannot be `computed_empty` (not a proven empty set — C3's false twin); they need a
degrading `excluded / inputs_unavailable` pin WITH a ruling_ref the writer does not own — the build
REFUSES them by name until a ruling id exists.

**Intervals.** One `searched_complete` row spanning the class horizon per obligation whose search
ran (residence with a probe; point relations with an arc index); an obligation whose input is absent
gets `missing_inputs` — a seal refusal by design (never silently scored). Natal-fact obligations are
atemporal: a full-horizon row records that the L1 fact was evaluated.

**Independent verifier** (`services/gochara_kernel/inventory_verifier.py`): derives each class's
inventory from the sealed rule rows and the snapshot's L1 facts WITHOUT importing the builder,
the evaluator or any function the builder uses; computes the preimage/digest in Python itself; writes
the verification row. SQL checks presence + equality only — whether writer and verifier share a
misreading remains the named residual (O-RP-9, review).

**Open (steward):** (1) a `ruling_ref` for P5 and for H-unknown classes; (2) `natal_fact` relation
label — my coverage uses `natal_fact`, but `kgso_relation_ck` and `partition_overclaims` require the
real relations (occupancy/ownership/…); coverage is realigned to the real relations; (3) P1 agents —
AM-5 wants period-lord role tokens (`period_lord:md|ad|pd`) while the enumerator yields concrete
grahas; F-3 (B + A) owns the mapping, so concrete grahas are used and flagged until it lands.


### Design v1.5 (2026-10-02) — the window sweep (`window:<event_class>:<path_id>` → `ka_gochara_eval_window` + `_record`)

Read for this note: specs v1.4 §2.1 (eval_window; score algebra), §2.3 inv 3/4, §3.1, §7.2 inv 2 (interior
extrema + threshold roots; O-SM-4 `f(t)=t(1−t)`), migration 1156 (the typed contract + N10 coverage binding +
N16 seal-time membership check), `gochara_rules/score.py` (Stream B's algebra), the registry's declared
soft factors, and what exists in this stack. **Nothing below is implemented yet.**

**What the registry says each path's score is made of** (read from `RULE_PATHS`, version 1.0.0):

| path | soft factors (all `null_state=unqualified`, `uncalibrated_default`) | prerequisites |
|---|---|---|
| P3 | `activity_kernel` (linear, degrees), `graduated_drishti` (step) | `p3_contact_house_or_lord` |
| P4 | `activity_kernel` | `p4_double_transit` (written already, F5) |
| P2 | `vedha_attenuation` (step) | `house_from_moon` |
| P1 | `dignity_of_transit_sign`, `combustion`, `agent_nature`, `maitri_compound` | `period_running_at` (written), `natal_bhava_relationship`, `transit_relation` |
| P5 | `activity_kernel` | `av_polarity_declaration_exists` — **held** (tier_withheld_by_ruling) |
| P6 | none (testimony; day rows only, never windows) | — |

Because every factor's `null_state` is `unqualified`, a record whose factor operand cannot be evaluated makes
its path score `unqualified` (never 0, never 1) — so the sweep can only emit a QUALIFIED window for a path whose
every declared factor is computable. That orders the work: **P3/P4 first** (angular kernel + a per-record step),
then **P2** (the vedha overlay rows), then **P1** (needs Stream B's dignity/nature/combustion/maitrī evaluated at
the transit instant). P5 stays held.

**Algorithm (per grain; O(B log B + output), §10.1).** (1) Inputs: the grain's records with their stored temporal
support intervals (state `computed`; truncated spans carry `t_exact` NULL) and, per record, a `value(t)` built
from its declared factors; (2) the boundary set B = every support endpoint ∪ every factor breakpoint inside the
class horizon; between consecutive boundaries each record's value is a smooth function; (3) per piece, the
extremum is solved — **interior** extrema (bounded scalar maximisation after a bracketed scan) and **threshold
roots** (Brent) — never endpoint-only (§7.2 inv 2; O-SM-4); (4) per instant, the §2.1 reduction: per root
`max` over its role records, per path `Σ` over roots per channel, across paths `max`; the three-field valence
(§3.1) is evaluated at the peak instant from class polarity + record content (never copied from a rule row);
(5) a window is one connected component of the union of its admitted records' supports, with `peak_instant`,
`score`, `evidence_for/against`, `outcome_valence_for_native`, `severity`, the member `record_ids`, the
class's `event_class` coverage reference and `null_states_used[]`; (6) written under the chart lock + global
SHARED key after its coverage partition (pin 7), delete-then-insert scoped (chart × generation × class × path ×
version) — membership rows are immutable and the N16 seal check re-validates them.

**Open — needs a ruling before any code** (each is a doctrine/contract choice, not an implementation detail):
1. **`score` vs `evidence_for_occurrence`.** §2.1 defines the class-instant score as `max` over paths of the
   *path score*, and the path channel as `Σ over roots` of the per-root `max` — two different quantities. Is
   `eval_window.score := max over admitted paths of path.evidence_for_occurrence` (with `evidence_against`
   reported beside it, not netted), or the within-path factor PRODUCT on the best record? The `[0,1]`
   codomain only holds for the latter.
2. **Window interval.** Is the window the connected union of its admitted records' supports (my reading — no soft
   factor zeroes it, §2.3 inv 3), or a threshold-bounded sub-interval where the aggregate exceeds a stated
   `min_lambda`? The legacy projection used the threshold; the spec's invariants say none.
3. **Kernel for residence-on-sign records.** `activity = 1 − |Δλ|/orb` is angular (D-RQ2); a `residence` record on
   `span:<sign>` has no point to be Δ from. Is the kernel 1 across a residence span (a step), or the angular
   distance to the sign's centre / nearest boundary? (This decides every P3 house edge.)
4. **`graduated_drishti` input.** The step function `¼/½/¾/1` — keyed on the aspect's house distance
   (3/10 = ¼, 5/9 = ½, 4/8 = ¾, 7 = 1, specials full)? Which Stream B module is the source of that table, and may
   the sweep read it, or is it a registry row to bind first?
5. **Valence/severity inputs** at the peak: `valence.py` takes class polarity + record content — confirm it is the
   evaluator, and what `severity` is for a window whose path scores are `unqualified` (named null, not 0).
Also still open from earlier (unchanged): the P1 `dasha_lord` house anchor, the manifest
`input_generation_vector` content for `'5.0'`, the P2/P5 verifier derivation, and the writer capability flags.

### Design v1.6 (2026-10-02) — the window sweep for P3/P4, on the steward's rulings (M20261002T001617-5a34 / -dd2f)

Landed (`window_sweep.py` pure · `window_store.py` · writer substeps `window:<class>:<P3|P4>` planned after
the class's record grains, before `verify:<class>`):

- **Stored per window** (one path-version × class): `interval` = the connected union of the admitted
  records' half-open supports (abutting `[a,b)`,`[b,c)` are one set; no threshold, no clipping);
  `peak_instant` = earliest instant of the max; `score` = max member within-path product (for-channel),
  NULL when no member is qualified; `evidence_for/_against` = per-channel Σ over roots of the per-root max
  at the peak, never netted, NULL when unqualified; `outcome_valence_for_native` =
  `valence.compute_valence` at the peak; `severity` = NULL (named null) always; `null_states_used` = the
  null states actually applied.
- **Kernel read from the factor row** (ruling 3): `activity_kernel` evaluates the row's own
  `applicability` (`span` kinds ⇒ membership step with the row's `inside` value; `angular` kinds ⇒ `1 − |Δλ|/orb_deg`
  with the ROW's orb). No `applicability` ⇒ every record's operand is unqualified (`applicability_undeclared`)
  — today's 1.0.0 row, and exactly what is stored. A null `orb_deg` ⇒ `unqualified (orb_not_ratified)`.
  Both registry states are tested (a row declaring applicability lights the SAME records up with no code
  change; a skip-guarded test runs against the real `activity_kernel@1.1.0` the moment #2897 is on main).
- **Path → version from the records**, not a constant: the substep reads each grain's distinct
  `rule_version` from its records and the factor rows from that version. Nothing here binds 1.1.0 —
  binding (A's `rule_binding`) waits for #2897 to be Codex-accepted.
- **graduated_drishti**: aspect records only (declared by the row's `applicability.relations`); the source is
  CALLED through an injected `drishti(agent, offset)` — Stream B's `services/gochara_rules/drishti.py` once
  it lands (#2894), never a copy. Until then an aspect record's operand is the named missing input
  `graduated_drishti_source_not_landed`. The aspect house-offset operand is derived from the body's sign at t.
- **Interior extrema** (§7.2 inv 2, O-SM-4): bracketed scan + golden-section refinement per support piece
  (parabola test: endpoints 0, interior max found); plateau ⇒ earliest instant; cross-member ties within 1e-6
  (the maximiser's own 1 s resolution) resolve to the earlier instant.
- **Independent check**: after every grain write, Postgres `range_agg` over the stored admitted scored
  records' supports is compared with the stored windows, and the membership set with the admitted records
  — shares no code with `union_components`.
- **Mutation-checked**: latest peak (3 fail), abutting-not-merged (4), sum-all-records-not-per-root (1),
  unqualified-admission-as-member (1), testimony-weighs (1), not-applicable-as-missing (12),
  missing-as-1 (8), zero tie tolerance (1), endpoint-only maximisation (2), severity 0 (4).

Judgement calls (each flagged to the steward; none is a doctrine ruling):
 1. Window membership = `admitted` ∧ `operator_role='scored'` records with a computed support. A
    `not_admitted` record is pruned by a false necessary predicate; an admission-`unqualified` record (an
    unknown prerequisite) is not an *admitted* record, so it forms no window — it stays in the record table
    and the coverage counts; testimony never weighs (§1.2 inv 2).
 2. P3/P4 records all land in the FOR channel (no against-direction operand exists in either path), so
    `evidence_against` is the evaluated 0.0 of an empty sum on a qualified window and NULL on an unqualified one.
 3. A mixed window (some members qualified, some not) scores from its qualified members, per
    `path_channel_scores`, and discloses the rest through `null_states_used`.

Still open: P2 (vedha overlay rows) and P1 (dignity/nature/combustion/maitrī at the peak instant) sweeps — the
sweep refuses those paths by name; P5 stays held; `graduated_drishti` source; the 1.1.0 binding; ND-ORB
(point-kernel operands stay unqualified until ruled); `day_on_demand`.

**Activation checklist (one routine migration in 1230–1249, at activation):** `ka_gochara_v5` registry row —
`depends_on`, `has_substeps = true`, and a `count_sql` that counts what the writer actually writes
(`ka_gochara_eval_window` for the chart, not `kala_gochara_windows`), plus the stale skeleton
`english_description`.

### Design v1.7 (2026-10-02) — P2 sweep, the against-channel rule, the lower-bound disclosure, the semantic verifier

Steward M20261002T004131-012c: (a) membership rule CONFIRMED; (b) CONFIRMED WITH A CONDITION; (c) CONFIRMED WITH A DISCLOSURE.
**Today's registry makes every P3/P4 window unqualified BY DESIGN** — `activity_kernel@1.0.0` declares no
applicability and no ratified orb, so every record's operand is unevaluable (`applicability_undeclared`) and
every stored window has `score`, `evidence_*`, `peak_instant` NULL, `severity` NULL, valence `unqualified`
with a named reason. That changes only when 1.1.0 is bound (after #2897 is Codex-accepted) AND — for point
objects — when ND-ORB is ruled (`orb_not_ratified`). It is the honest outcome, not a defect.

- **(b) `evidence_against`** is the evaluated empty sum (0.0) ONLY when the path's own soft-factor rows declare no
  against-channel operand: `against_channel_state(factor_rows)` — every factor's `direction` is the
  magnitude-only vocabulary (`higher = stronger` / `lower = stronger`) ⇒ `none_declared` (0.0); a direction that
  names a channel/valence ⇒ `declared`; anything else ⇒ `ambiguous`; both leave the against sum NULL (and the
  valence `unqualified`: contested-vs-plain cannot be stated). Never keyed on a path name; the test runs the
  same factor rows under P3 and P4, and a synthetic path that declares an against operand. A path that assigns a
  DIRECTION per record (P2) evaluates both channels explicitly.
- **(c) lower bound.** A mixed window scores from its qualified members, so `score` and the evidence sums are LOWER
  BOUNDS. Migration 1156 gives no free JSON column — `coverage_facts` must equal the partition's facts
  byte-for-byte and `null_states_used` is CHECKed to `{omit, unqualified}` — and no DDL is allowed, so the stored
  encoding is `score IS NOT NULL AND 'unqualified' = ANY(null_states_used)`. `WindowDraft.score_is_lower_bound`
  carries it in code; **`window_verifier.verify_window_semantics`** reproduces it from the stored member records
  (it imports nothing from the builder). **If an explicit `score_is_lower_bound` column is wanted, that is a
  1156-successor migration (a steward/native call), not something to slip in.**
- **P2 sweep.** One direction per record from the cited sets (Stream B's `favourable_houses` /
  `ADVERSE_RESIDENCE_*`, called not copied; a house in neither or both sets refuses), channel through
  `score.channel_for` (class-relative polarity); score = for-channel max (an all-against window scores an
  evaluated 0.0 peaking at its start); evidence per channel at the peak, never netted. The vedha operand is a
  named missing input (`vedha_overlay_not_bound`) — open Questions Q1/Q2 on the tracker: source (kala_vedha_gochara
  vs derived) and the state→value mapping the registry row does not carry. NOTE the enumerator already
  restricts P2 edges by class polarity (adverse classes enumerate only the adverse-residence houses; the other
  Saturn houses are testimony and never window members), so the against channel is empty in practice.
- A record whose operand is undeterminable over its whole support (a source returning None everywhere) is
  UNQUALIFIED (`operand_undeterminable_over_support`), never a 0.0 — found when the first P2 plumbing returned 0.0.
- Mutation-checked: 19 mutations (13 builder, 6 verifier) all killed; 54 window tests; sidecar suite green.
- **graduated_drishti is now wired** to Stream B's `gochara_rules.drishti.graduated_drishti` (#2894 merged): the writer's
  `DRISHTI_SOURCE` calls it and reads its `value` (None = unclassifiable ⇒ an undeterminable instant ⇒ unqualified; nodes
  cast none, N-14). The aspect house-offset operand is derived from the body's sign at t. Under today's 1.0.0 rows an
  aspect record is still unqualified (`applicability_undeclared`) — the source only matters once 1.1.0 declares
  `applicability.relations`.
- **Steps are exact**: `maximise_earliest` bisects the transition between the last lower sample and the first maximal one,
  so a dṛṣṭi step inside one aspect record (the body leaving one source sign) peaks at its exact breakpoint (< 2 s),
  not at the next grid point.

### Design v1.8 (2026-10-02) — the P1 window sweep (windows formed, factors honestly unqualified)

P1's four soft factors — `dignity_of_transit_sign`, `combustion`, `agent_nature`, `maitri_compound` — are categorical or
step rows that declare **no [0,1] value mapping** (dignity's virūpa ordering anchor is "ordering anchor ONLY … no
magnitude claim"; agent_nature/maitrī assign channel/valence, not a magnitude). So the P1 sweep forms the windows (the
connected union of the admitted period-lord contacts' supports) and stores them **unqualified** with the named reason
`value_mapping_undeclared`; a row that later declares a `value_mapping` is REFUSED by name (the sweep has no reader for an
undeclared shape — never ignored). Channel assignment through `agent_nature` is not implemented and refuses if a P1 record
is ever qualified before it is. The independent verifier derives the same reason from the same rows with its own code (a
cross-check test compares builder and verifier on every factor state of every swept path). All four of P1–P4 now have a
`window:<class>:<path>` grain; P5 stays held; P6 is day-tier only.

### Design v1.9 (2026-10-02) — Codex round 6, R3 (window construction) and the consumer side of R1

Steward M20261002T005809-4f92 adopts Codex's closing text (`ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_5.md`). Landed:

- **R3 — one window per MAXIMAL CONNECTED COMPONENT of the prerequisite-satisfied support, never bridged.**
  For every path but P4 the support is the union of the admitted scored records' supports; for **P4 it is the
  INTERSECTION of Jupiter's and Saturn's influence unions** (`intersect_components`; Jupiter `[0,2)` ∧ Saturn
  `[1,3)` ⇒ `[1,2)`, not `[0,3)`; no joint support ⇒ no window). **Members are the admitted records OVERLAPPING the
  window** — a P4 record may extend past it (1156's membership guard checks the coverage horizon, not the window).
- **The peak maximises a NAMED objective, earliest attained maximum.** P4: the frozen max-min
  `min(act_Jupiter, act_Saturn)` (S:321–323, O-RP-3), with `act_g(t)` = the **max** over agent g's live admitted
  records of the within-path product (max, not Σ: union semantics, stays in [0,1]) — recorded as a definition for
  Codex. Every other path: `evidence_for(t)` = Σ over roots of the per-root max for-channel value. Solved
  piecewise between support endpoints (constant pieces exact; non-constant pieces by scan + golden section,
  steps by bisection). `score` = the max live for-channel product at the peak (P4: the max-min value itself);
  evidence per channel at the peak, never netted. Codex's counterexample (Jupiter 0.2+0.8t, Saturn 1−0.8t) is a
  test: the peak is t=0.5, not an endpoint (best-single-record) and not the plateau's start (summed evidence).
- **R1 consumer side — qualification PROPAGATES.** An unresolved applicable factor on any member makes its channel
  NULL (a member of unknown channel affects both); the objective is then unqualified and `peak_instant`, `score`
  and the dependent evidence are NULL with the reason kept (`unqualified_reason`). Admission and admitted support
  are unchanged; no partial subtotal is stored. **This SUPERSEDES the lower-bound disclosure of v1.7 (c)** — there is
  no `score_is_lower_bound` any more (the field and its encoding are removed). 1156 permits a NULL `peak_instant`
  (`CHECK peak_instant IS NULL OR peak_instant <@ interval`), so no DDL is needed.
- **Independent verification follows the same rules**: SQL `range_agg` components (P4: multirange `*` intersection),
  overlap membership both ways plus "admitted record in no window"; the semantic verifier re-derives qualification,
  propagation, the piecewise objective, peak, score and per-channel evidence from stored rows (constant members;
  non-constant ones are structural only).
- Mutation-checked: 27 mutations over the builder, the verifier and the SQL check — all killed except ONE equivalent
  mutant: the verifier's P4 numeric path only reproduces constant members, where both agents' step-kernel values are
  equal, so `min`↔`max` is unobservable there (non-constant P4 windows are structural-only by design).
- **Open for the next steps**: P1 prerequisite-restricted support (`period_running_at` is evaluated at a single
  instant; restricting a P1 record's support to the running-period intervals needs the §4.0 dasha intervals and waits
  with R2's Moon-lord domain on Stream B's AM-14 text); `score.py` is not yet the reduction used here — the sweep
  carries its own reduction until Stream B's qualification-in-the-result PR lands (then it is called, not copied).

### Design v1.10 (2026-10-02) — Codex round 6, R4 (geometry as a validated contract)

- **Kind ↔ target agreement is checked before any factor is evaluated** (`validate_geometry`): the kgrr object-kind
  vocabulary maps to the canonical-target FORM it requires (`sign_span`/`house_span` → `span:`, `star` → `star:`,
  `degree_point`/`derived_point`/`saham`/`house_lord` → `point:`); a malformed target, a missing one, or a disagreement
  (a point labelled a span would take the membership step and bypass the unratified-orb branch) REFUSES the build —
  it is a defect, not a missing operand. `varga_position` stays explicitly unqualified. A node-cast aspect record
  (N-14) is refused outright.
- **Membership comes from the contact geometry**, not only the stored support: the store supplies an `inside_at`
  probe (residence: the body is IN the sign; aspect-on-span: one of the agent's own directed rays λ+angle lands in
  it) and the sweep refuses a window whose peak lies where the geometry contradicts the support (a probe that cannot
  decide — None — is not "outside"). The `outside: 0.0` of a membership step is never a second admission filter:
  the sweep only evaluates inside a support.
- **Aspect distance is the DIRECTED ray with seam-safe wrap** (`wrap180`; the nearest of the agent's own angles;
  nodes: no provider) and the house offset keeps the inclusive convention.
- **The lowercase-token adapter is closed** (`GRAHA_TITLE`, nine tokens; anything else — Title case, unknown — refuses);
  every `.title()` in the window code is gone.
- **Orb configuration fails closed**: a finite, strictly positive number is required (0, negative, NaN, ±inf, bool,
  string are refused). *Open for Stream B:* Codex also asks for "a ratified decision binding and matching immutable
  factor version" before the angular formula runs — the factor row has no field naming the ratifying decision, so the
  sweep cannot check one; send the field name when ND-ORB is ruled and it becomes a guard.
- 95 window tests; 11 R4 mutations all killed.

### Design v1.11 (2026-10-02) — Codex round 6, R5 (version-aware persistence and consumption)

`rule_registry.py` no longer selects rows by a global version:

- **Explicit composite references**: `BOUND_PATH_REFS`, `BOUND_FACTOR_REFS`, `BOUND_PREDICATE_REFS` are literal
  `(id, version)` tuples. A new immutable version (the AM-13 `activity_kernel@1.1.0` / `P3,P4,P5@1.1.0` rows, or
  `vedha_attenuation`'s successor) is bound ONLY by a deliberate edit to them after its review gate passes — nothing
  is bound by default and nothing global is bumped (a test sets `RULE_VERSION = "9.9.9"` and asserts every row set is
  unchanged). Every row carries ITS ref's version; each prerequisite and each soft factor keeps ITS OWN version (a
  successor path `P3@1.2.0` with factors `@1.1.0` and a prerequisite `@1.0.0` is a test, so a binder that took the
  path's version for its members cannot pass). A path reference to an unbound member version, or a bound path ref
  absent from the catalogue, is refused before any SQL.
- **Flat applicability encoding** into the existing typed `operand_selector` (1154:221-240: flat object, token /
  number / token-array values, no nesting, no JSON null): closed key schema `span_kinds/span_function/span_inside/
  span_outside`, `angular_kinds/angular_function/angular_form/angular_orb_state[/angular_orb_deg]`, `relations`.
  The unavailable orb is OMITTED and the unratified state is an explicit token; the free-text `formula` becomes a token
  and `orb_status` is dropped; an unknown key or formula is REFUSED, never guessed. The real 1154 CHECK admits it and
  refuses the nested and the null forms (both tested on the real schema).
- **Read-back**: every insert is read back and compared with the declaration (a store that silently kept something
  else is a divergence); `bound_factor_rows(path, version)` reads the persisted membership, each factor row at its own
  version, decodes the flat applicability, requires it to RE-ENCODE to exactly what is stored and equal the
  declaration. The window sweep consumes THAT (the persisted declaration), dispatching evaluators on the exact
  membership reference; the prose `direction` the against-channel rule reads comes from the catalogue row at the same
  ref (the DB's direction is the binary CHECK vocabulary).
- **Open for Stream B (#2897)**: (i) the 1.1.0 `activity_kernel` row's top-level `function = "linear"` describes a
  piecewise function (step for extents, linear for points) — Codex asks that it identify the piecewise form;
  (ii) `graduated_drishti@1.1.0` and the 1.1.0 `drishti.py` ref (`FACTOR_REF` is still `1.0.0` in #2894): the evaluator must
  name the version it implements. The binder is ready for both; it will not bind 1.1.0 before acceptance.

### Design v1.12 (2026-10-02) — Codex round 6, R6 (AM-16: the input vector is the identity of what was consumed)

The manifest's `input_generation_vector` enters the snapshot's `input_digest` (1206), so it must distinguish every
result-bearing change. `input_vector.py` builds it with a **versioned key schema** (`ka_gochara_input_vector/1`) and a
canonical serialization; it binds:

| component | content |
|---|---|
| `registry` | digest over the SELECTED path, predicate and factor payloads (all columns but the enumerated audit fields `created_at`/`sealed_at`), the ORDERED prerequisite memberships, the soft-factor memberships, the applicability declarations (they ride the factors' flat `operand_selector`), and the accounted sealed-version CENSUS (every sealed `(path, version)`, bound or not) — plus the census itself |
| `sky_convention` | the kala/sky convention id |
| `node`, `ephemeris` | the node model/source/zodiac/ayanāṃśa AND the identity of the node series actually consumed: the Swiss library version and the sha256 of every `.se1` in the ephemeris path (a "mean" label does not distinguish two series). No path ⇒ refused, never recorded as unknown |
| `orb_policy` | BOTH policies: the contact/ADMISSION orb table digest (it fixes supports) and the ACTIVITY orb restated per `activity_kernel` row version (`undeclared` / `unratified` / the number) |
| `rulings_digest` | the standing rulings, every bound path's `ruling_ref`, and AM-14 |
| `implementation` | source digests of the geometry, evaluation and window-construction module closures |

Inputs already bound transitively by the snapshot (L1 facts, daśā, AV declarations) are not duplicated.

- **Two derivations that share nothing.** The builder canonicalises typed rows in Python; `input_vector_verifier.py` derives the
  registry digest entirely inside Postgres (1206's `ka_gochara_canonical_json` + `ka_gochara_sha256_hex` over `to_jsonb`).
  They must agree byte-for-byte; the manifest refuses to bind an identity they disagree on.
- **Every later substep verifies the inputs it consumes** (`_verify_live_inputs`): the vector is recomputed from what is consumed
  NOW and compared by component; drift is refused by name (`InputDrift`), a missing manifest is refused. A changed input is a
  NEW generation, never a silent continuation.
- **Historical replay** (`verify_replay`) checks the ORIGINAL bound inputs — the digest over the original references and the
  ORIGINAL census (every recorded seal must still exist) — never a fingerprint of today's catalogue; versions sealed since do
  not move a past build's identity.
- **Frozen cases** (real schema): membership-only (P1's prerequisite order swapped, identical row payloads), node-series-only (one
  `.se1` differs ⇒ exactly `ephemeris.files.semo_18.se1`), node-convention-only, admission-orb-only, rulings-only,
  window-algorithm-only (`implementation.window`), a successor version sealed after the build. 12 mutations, all killed.
- **For Stream B to confirm**: the key schema above is mine (Codex's closing text names the components, not the keys); and the
  implementation closure lists are mine — say if a module belongs in or out of a stage.

### Design v1.13 (2026-10-02) — the sweep calls Stream B's qualification-aware reduction (#2905)

`window_sweep.reduce_at` now CALLS `score.path_channel_scores` (per root max, Σ over roots, channel-preserving;
**qualification propagates — an affected channel is None, `known_partial_subtotals` are lower bounds and are
never stored**) instead of carrying its own reduction. The non-P4 peak objective is that function's for-channel result at
each instant; evidence at the peak is the same call over the members live at the peak. Consequences: (i) a member whose
operand is undeterminable AT an instant makes that instant's channel None (it used to be skipped silently); (ii) the
against channel is the per-instant reduction at the peak — an unqualified against-channel member not live at the peak
does not null it, one that is live does (the verifier follows). The window-level rule is unchanged: a for-channel
unqualified member anywhere in the window makes the objective, and so the peak, unqualified. 80 sweep tests; 17 mutations
killed (one equivalent: the verifier's P4 numeric path only reproduces constant members).

### Design v1.14 (2026-10-02) — Codex round 6, R2 (AM-14 Moon-resolved period domain) and the P1 running-period support

**R2 — built against PR #2909 / migration 1232 (HOLD; applied nowhere), gated on the APPLIED schema.**

- Moon exclusion follows the RESOLVED concrete agent, per role obligation. A Moon-resolved portion of a `period_lord:md|ad|pd`
  interval is `excluded_moon_tier` — neither `missing_inputs` nor `searched_complete` — **when the schema can account it**;
  `InventoryStore.moon_scope_available()` READS that from the database (the `kgsiv_state_ck` state AND the derived-domain function)
  and `SearchCapability.moon_scope_domain` carries it, so on today's 1206-only schema the same portion stays an honest
  `missing_inputs` (the class cannot seal) — the schema is never assumed to be ahead of what is applied. Nothing that runs on
  main's schema depends on 1232.
- A Moon bhukti excludes only the `ad` obligation's Moon portion: the MD lord's delivery during it is still searched; the Moon as a
  natal TARGET and in another agent's Moon-frame evaluation are untouched (tests).
- The independent verifier re-derives the ledger with its own code and is TOLD the schema fact like every other capability; told the
  wrong fact it disagrees (the check has teeth). Coverage names the excluded portion (`unavailable.moon_scope`) — said, never implied.
- The manifest `input_generation_vector` now carries **`stored_scope: "stored_non_moon"`** (1232's completeness function refuses a
  published manifest without it; serving must state it with every answer).
- **Judged by Stream B's own function**: the integration tests apply 1232 on top of 1206 on a throwaway database and let ITS
  `ka_gochara_search_completeness_violations` judge this writer's output — with 1232 there is no `missing_inputs_present`,
  `moon_domain_missing`, `moon_domain_extra` or non-period exclusion; on 1206 alone `missing_inputs_present` fires; a builder that
  does not account the domain is caught (`moon_domain_missing`). (The migration is read from the repo or from PR #2909's branch;
  the tests skip when neither exists.) `stored_scope_missing` fires only for a PUBLISHED manifest, which this build never publishes.

**P1 prerequisite-restricted support (R3 residual).** A P1 transit record's stored support is its contact span (clipped to the
horizon) restricted to the periods the agent RUNS: `record_store.period_running_support` cuts the span at every daśā-row boundary
inside it and keeps an elementary piece iff **Stream B's `period_running_at` predicate** is `true` at its start (called, never
re-implemented; half-open §4.0); adjacent kept pieces merge. An empty result is a `computed_empty` record whose prerequisite is
`false`; no L1 daśā rows for the agent leaves the contact span unrestricted and the prerequisite an explicit `unknown`. The old
instant-based semantics (judged at the ingress) are replaced — three record-store tests were rewritten and a pointwise
property test (hourly, ends included) ties the interval form to the predicate. **Flag to Stream B/steward:** this changes the AM-11
"evaluated at the occurrence instant" reading to "evaluated over the support" on Codex's R3 text.

*Still open:* the verifier's independent derivation of P2 (and P5's excluded pin from the sealed row) — the class-level `verify:`
substep still refuses P2 by name, so no class can seal yet; `day_on_demand`; the vedha derivation and 1.1.0 binding (wait on B).

### Design v1.15 (2026-10-02) — AM-16 reconciled with Stream B's model (steward M20261002T014514-c929)

`ka_gochara_input_vector/1` is normative; Stream B's `design/am16_vectors_model.py --cross-check input_vector.py` passes
(canonical_json, rulings_digest, registry_digest via a stand-in connection, diff_vectors agree byte-for-byte). Four changes:

1. **Ephemeris identity = the files the kernel actually OPENS.** `probe_opened_files` asks the Swiss library
   (`swe.get_current_file_data(0..4)` after a calc, under the Swiss-state lock) which files each substrate body opens at both
   ends of the CONSUMED range (the substrate domain, widened by the class horizon) and past every file-block boundary inside
   it; only those are hashed (measured: sepl_18 + semo_18, never seas_18). A probe served by the Moshier fallback is refused —
   an opened file that is absent is refused, never bound as unknown, including a MIDDLE block with both endpoints served.
2. **L0 identities**: `l0 = {asset_id: sha256(canonical rows consumed, total order)}`. **Consumed by P2 (AM-18's vedha operand):
   `bg_transit_rules` where `rule_type = 'vedha'`** (the surrogate `id` excluded — not content; non-vedha rows do not move it).
   **`bg_transit_av_gates` is consumed only by P5, which is held by ruling ST-P5-HOLD — it is NOT consumed by this build and is not
   bound**; when P5 is lifted it joins `L0_CONSUMED`. (P1/P3/P4 read no L0 table; the favourable-house table is Stream B's cited
   catalogue code, inside the evaluation implementation digest.) An absent or empty L0 table is refused.
3. **Implementation coverage**: the stage lists now name the writer's whole static import closure over `services.gochara_kernel` +
   `services.gochara_rules` (42 modules; verifiers sit with the stage they verify), and a coverage test (an AST closure helper)
   fails when a module the writer imports sits in no list — so editing it can never leave the vector unmoved. `kernel_factor`,
   `flat_selector`, `vedha_derive` join when they land on main and the writer imports them (the test says so).
4. **`sky_convention` = `{id, content_digest}`** — the digest is over the persisted convention row (audit field excluded), so the
   same label with different content moves it. **`activity_orb`** restates each `activity_kernel` row version as `undeclared` /
   `unratified` / `{orb_deg, orb_decision_ref}`; the flat encoding gained `angular_orb_decision_ref`: a numeric orb is admissible ONLY
   with the selector-token decision that ratified it (encoder AND the sweep refuse a bare number — Codex's "ratified decision
   binding"). *Note for Stream B:* I kept my flat key names (`angular_orb_state`, `angular_orb_deg`, `angular_orb_decision_ref`);
   your model's example row uses `orb_state`/`uncovered_state` — whichever #2897 binds, `encode_applicability` is the one place
   to align, and the vector restates the result either way.
31 AM-16 tests (real files where present, Swiss stand-ins otherwise); 8 mutations killed.

### Design v1.16 (2026-10-02) — Codex round 7, [1] (qualification over the whole component) and [7] (global maximum by pieces)

**[1] A peak is qualified only when the objective's maximum AND its earliest maximising instant are established over the ENTIRE
component.** `maximise_earliest` no longer drops unknown samples: a value that is unknown at ANY evaluated instant makes the whole
piece unknown, and any unknown piece makes the window's objective unqualified — `peak_instant`, `score`, `evidence_*` NULL,
`unqualified_reason = objective_unknown_over_component`, the piece count kept in `unresolved`. (An unknown portion could hold a larger
value; "first half vedha 0, second half None" no longer yields peak=start, score=0 — Codex's reproduction is a test, as is an unknown
island inside a known piece.) A bounded reduction would stay qualified only if proved independent of the unknown operands — none is
claimed. A record unknown at EVERY sampled instant is still unqualified at the record level. **Records store NULL, never a placeholder
0.0, for unevaluated evidence/severity** (1155 permits NULL; tested on the real schema). **Affected channels and reasons**: 1156 has no
column for them, so they are OBLIGATORILY RECONSTRUCTABLE — `window_verifier.reconstruct_qualification` rebuilds them from the stored
members and the bound factor rows (independent code), and the writer's note carries the reason summary. *Not mine:*
`score.aggregate_paths([0.2, "unqualified"]) -> 0.2` is Stream B's cross-path reduction (flagged).

**[7] The objective is solved per piece at EXACT factor-state boundaries, with a method that establishes the global maximum.** Members
declare `state_boundaries(lo, hi)` (a dṛṣṭi source-sign ingress, a vedha interval edge) and `peak_hints(lo, hi)` (a point contact's
exact instant); the component is cut at support endpoints ∪ every declared boundary, so within a piece each function is constant or
smooth-unimodal. Each piece's candidates = its start ∪ every exact hint ∪ a 96-point scan, refined by bracketed golden-section around
the best three scan points, and for a plateau/step the earliest instant is bisected to 1 ms. A short interior vedha island (12 h inside a
100-day support) is found when its edges are declared boundaries; a spike narrower than the scan spacing is found through its hint.
**Tie tolerance: 1e-9** (the frozen measurement contract), distinct from the 1e-6 storage-comparison tolerance (the verifier keeps
both, separately named). **Stored score ruling applied and made explicit in code**: `objective` (a NAME) and `objective_value` are
distinct from `score` — P4 stores the max-min value at the peak; every other path stores the max live record product at the peak
(unequal-agent P4 and two-root cases are tests). Note the consequence of the 1e-9 rule on a smooth flat top: the earliest instant
within 1e-9 of a parabola's maximum is ~27 s before it (kinked kernels — the real ones — are exact).

### Design v1.17 (2026-10-02) — Codex round 7, [3] (P1 support, independently verified) and [2] (AM-14 population + scope response)

**[3] P1 support.** Already restricted at write time (v1.14: contact span ∩ the running periods, cut by CALLING `period_running_at`,
disjoint pieces kept, `computed_empty` when never running). What round 7 asked for and is new: **the verifier derives the restriction
from the pinned periods** — `record_verifier.verify_p1_support` (no builder import; Postgres multirange arithmetic over the
snapshot-bound `consumed_dasha_row_ids`, levels 1–3, the agent's lord) requires, per P1 transit record, `stored support = contact ∩ ⋃ running
periods` and the stored `period_running_at` to be `true` iff that is non-empty (`unknown` + the unrestricted contact when the agent has no
rows). It runs at the end of every `record:<class>:P1` grain, and fails the build on a support that admits a period gap, discards a valid later
portion, or sits on the wrong pieces. Cases (all on the real schema): a period ending inside a contact; licensed pieces separated by a gap
(disjoint, never bridged); a contact that never meets a running period; an ingress before the horizon (clipped, then restricted); retrograde
re-crossings (separate contacts, each restricted on its own); an agent with no daśā rows. **Finding (not new, now explicit):** the writer's
house resolver returns None for the `dasha_lord` frame (the record's own frame arithmetic is unresolved — AM-15 does not replace it), so the
writer currently mints NO P1 transit record at all; the verifier is exercised through the grain directly. P1 therefore produces no window today,
which is consistent with "no qualified P1 window" but means P1's coverage claim rests on the inventory, not on records. Needs a ruling: the
anchor of a P1 transit record's `house_from_frame`.

**[2] AM-14.** (i) Both derivations (planner and independent ledger verifier) emit `excluded_moon_tier` for Moon-resolved period portions
when the applied schema accounts it (unchanged from v1.14 — gated on the applied schema). (ii) **The consumed daśā POPULATION is validated against
the §4.0 read contract by the verifier, independently** (`check_dasha_population`; its own constants, imports nothing from the builder): every
consumed row is of this chart, `lahiri_chitrapaksha`, `vimshottari`, `two_pass_verified`, levels 1–3, and — canonical chart — the frozen pinned build
(any other chart: one build); no consumed row wholly outside the horizon (extra), no pinned row overlapping it missing (omitted), no conflicting
pinned rows, no consumed id resolving to no row. A **wrong-build / wrong-system / wrong-tier Moon-row adversary** is refused, as is a consumed row
whose build changes after the build; `rederive_ledger_digest` calls the validation before trusting any row. (iii) `stored_scope = stored_non_moon`
is a top-level key of the candidate vector (v1.14). (iv) **The mandatory positive AND no-window response constructor**:
`scope_response.coverage_response` reads the scope back from the BOUND manifest vector of the generation, returns it with the windows (or none),
lists any `moon_on_demand` answers beside it (the scope does not change after an on-demand query), and **refuses** — `completeness = "refused"`,
`stored_scope_missing`, no scope statement — when the manifest states no scope, no manifest exists, or the scope is unknown. Serving must call it
(Stream C / the retrieval layer); the writer side is done and tested on the real schema.

### Design v1.18 (2026-10-02) — Codex round 7, [5] (no unconditional pass), [8] (validated row contract), [9] (frozen vectors)

**[5] Verifier.** `verify_window_semantics` now returns a **status**: `VERIFIED` only when every window's stored fields were reproduced EXACTLY
(statically-unqualified windows reproduce their NULLs; constant-member windows reproduce score, peak and per-channel evidence); a window with a
**function-valued member** is `UNVERIFIED_DYNAMIC` — checked against structure and **universal bounds** only (a per-root value is ≤ 1, so evidence
is ≤ the number of roots feeding the channel and the score cannot exceed the evidence at the same peak) and counted, never passed. The review's
fabricated one-root `evidence_for = 123.0` is refused (and a within-bounds wrong sum on a two-root window is refused by the exact check).
`satisfies_gate(report)` is True only for a fully VERIFIED report; the writer's note says **"UNVERIFIED … this result does NOT satisfy a verification
gate"** for a dynamic window and never "passed". **Source geometry:** `verify_member_support` checks, from the contact and its partition (independent
SQL), that every member's stored support equals the contact span clipped to the partition horizon (P1's restricted support is `record_verifier`'s) and
that the physical object's canonical target has the form its object kind requires (the verifier's own table). Dynamic numbers/peaks are NOT yet
reproduced from independently obtained operands: no qualified dynamic window can exist today (the orb is unratified; vedha is unbound), and the
status keeps that explicit when one does. **The surviving P4 mutant is equivalent only in the constant-step domain** (both agents' step value is 1),
supplies no evidence for dynamic P4, and is not used to imply coverage of the full sweep. *Vedha verification* must not call the same `derive_vedha`:
it needs an independent oracle over the source intervals — with #2901.

**[8] The validated row contract.** A numeric orb is admissible only when the row AFFIRMATIVELY declares `orb_state == "ratified"` (and names its
`orb_decision_ref`): the review's row — orb 5 with `orb_status` still "unratified" — is REFUSED (three spellings of "not ratified" tested); ratification
is never inferred from a number being present. **Span membership requires the contact GEOMETRY** (`inside_at`): missing geometry is the named missing
operand `geometry_operand_missing` (unqualified), never affirmative membership; the geometry is checked at every piece start and just inside its end
across the WHOLE component (not only at the peak), a contradiction refuses the build, an undeterminable geometry makes the piece unknown. (The nakṣatra
boundary defect is in #2897's `kernel_factor`; `star` records carry no geometry probe here and therefore stay unqualified — the explicit non-consumption gate.)
When #2897 lands the sweep delegates to `kernel_factor` — it is not copied.

**[9] Frozen vectors.** `input_vector.assemble_vector(inp)` is the ONE pure serializer (`build_input_vector` gathers inputs and calls it);
`tests/l3/gochara/fixtures/am16_vectors_frozen_v1.json` (Stream B's literal preimages + expected sha256, campaign/pravaha 425a89218) is reproduced
byte-for-byte for all 13 cases + the registry preimage; the ephemeris carries B's `probe_digest` (sha256 over the exact `float.hex()` `calc_ut` results of the
fixed probe set), equal to B's independent probe implementation; `stored_scope` and the audit/unopened-file cases agree with the model
(`am16_vectors_model.py` and `--cross-check` both OK). The writer module itself (`ka_gochara_v5`) is now in the evaluation stage list, with
`substrate`/`inventory`/`permission`/`frames` already listed; the closure coverage test stays.

### Design v1.19 (2026-10-02) — Codex round 7, [4] (ONE codec; the selected path reference reaches every consumer), against Stream B's pinned base ed03d3c6c

**One codec.** `rule_registry.py`'s private applicability codec is deleted; Stream B's `services/gochara_rules/flat_selector.py` is the only one.
A factor's catalogue `operand_selector` (the flat form IS the source of truth) is persisted **verbatim**, checked with `flat_problems` /
`kernel_flat_problems` (unknown key, a numeric orb without `orb_state=ratified` + `orb_decision_ref`, an unknown state → refused before any SQL),
read back **flat-to-flat**, and `decode(flat) == the declared applicability` is required of the persisted row (a decoder that loses the declaration, and a
persisted selector that drifted from the declaration, are both caught on read-back). `input_vector.activity_orb_states` reads B's `orb_state` /
`orb_deg` / `orb_decision_ref` (the vector now says `unratified_nd_orb_open`, as in B's frozen vectors); `flat_selector` and `kernel_factor` are in the
evaluation-stage import closure (AST-checked).

**The selected path reference is passed, not a global.** Every enumerator takes `rule_version` (default `RULE_VERSION` only for legacy callers); the
production consumers read the binding at call time (`rule_registry.bound_path_version(pid)` / `bound_path_refs()` — never a tuple captured at import):
the writer's coverage and record substeps, `inventory.plan_class_inventory` (each sealed `(path, version)` enumerates at ITS version, P1 included),
`materialise_record_grain(rule_version=…)` (edges that disagree with the grain's selected version refuse; the delete-then-insert and the prerequisite
membership read use it, with no `"1.0.0"` / global fallback), and the **independent verifier's** obligation derivation (`inventory_verifier` no longer
hard-codes `1.0.0` in the obligation bytes). **`record_store` now passes `_pv`** — the prerequisite's OWN version — to `set_prerequisite_result`
(it passed the path's version, which only worked while both were 1.0.0: for P3@1.1.0 the UPDATE matched no row).

**Drishti.** The sweep calls the source as `drishti(agent, offset, factor_ref)` with the membership's own `(factor_id, rule_version)`; the writer's
`_drishti_source` passes it as `graduated_drishti(..., factor_ref=ref)` and **verifies the returned `factor`** equals the ref asked for (a source
answering for another row is a `SweepRefusal`, never re-labelled).

**Tests are on the ACTUAL rows** (`tests/l3/gochara/_bound_1_1_0.py` binds P2–P5@1.1.0 and the three @1.1.0 factors beside the 1.0.0 ones — the production
default stays 1.0.0 until acceptance): binding (each member at its own version; predicate @1.0.0 under path @1.1.0), the real 1154 schema, SQL read-back
flat-to-flat + decode, inventory pins/obligation ids + the verifier's independent bytes at 1.1.0, the record grain and its prerequisite results at 1.1.0,
the sweep lighting up from the persisted declaration alone. Mutation checks (10): all killed except one equivalent mutant (P4's provenance lookup at
the global version — P4@1.0.0 and P4@1.1.0 carry identical provenance, and a missing version already fails in `_path_citation`).
`test_wp10_cutover.py::{step07,step08,clear_windows}` fail identically on the untouched baseline (verified with the change set stashed) — not this change.

### Design v1.20 (2026-10-02) — AM-20 (ND-P1-FRAME): P1 transit records may now be minted; the `dasha_lord` house is a stored descriptor

Steward directive (from Stream B's `design/P1_FRAME_ANSWER_v1_0.md`, campaign/pravaha 99689db4b). **`house_from_frame` of a P1 transit record = the inclusive
whole-sign count from the NATAL sign of the period lord that anchors the record**, resolved through Stream B's `frames` (`Frame("dasha_lord", <graha>)` +
`house_of` — called, not copied); AM-15's lagna-inclusive count for the NATAL relation is unchanged. Before this the writer's resolver returned `None` for
`dasha_lord`, so NO P1 transit record was minted in production; it now is (a stated state is retained for an edge with no anchor / a lord with no natal position).

**The anchor is enumerated, not read from the daśā rows.** `RecordEdge.period_lord` (concrete graha, lowercase; P1 transit edges only, `None` elsewhere): the
agent for its own/exaltation/debilitation signs (XX.37); for Sun/Jupiter on a sign that is only ANOTHER graha's exaltation sign (XX.38) the graha whose
exaltation sign it is (e.g. the Sun in Capricorn ⇒ Mars). It is NOT a natural-key field and NOT in the frame (1154's `ka_gochara_frame_ok` forces the
`dasha_lord` frame arg to NULL), so record identity, obligation bytes and the AM-5 inventory digest are unchanged. **Level:** the period *level* (md/ad/pd) is
a property of each running piece — one contact can span the lord's MD, AD and PD — so it cannot be a single per-edge value; the edge carries the graha only and
no stored or read quantity depends on the level (the support restriction already runs over all three levels). Flagged to the steward as an interpretation of
"graha + level".

**Nothing reads the descriptor** (tests): no `services/gochara_rules` module mentions `house_from_frame`; in the kernel only the store/verifier/sweep modules do, and
the sweep's single reader is P2's Moon-frame direction; a P1 window is byte-identical for every descriptor value 1–12 (unscored: `value_mapping_undeclared`, NULL
evidence/severity); and a PG round trip re-materialises the same P1 grain with the descriptor shifted by 1, 5, 11 — the descriptor changes and NOTHING else a
record stores (admission, prerequisite results, support, evidence, frame) does. **Independent verification:** `record_verifier.verify_p1_house_descriptor` (called by
the record phase after `verify_p1_support`) re-derives the anchor from the verifier's OWN classical table and the count from the snapshot-bound L1 natal positions;
a lagna-counted descriptor (the rejected option (a)) is caught. 11 tests; 8 mutations, all killed.

**Open (not changed here):** (1) one record exists per (agent, sign); where both XX.37 and XX.38 readings apply (the Sun in Libra: its debilitation AND Saturn's exaltation;
Jupiter in Capricorn, etc.) the agent's own reading is the anchor — the one the enumeration already carried. (2) P1's SUPPORT and the `period_running_at` / natal-relation
prerequisites run over the *agent's* running periods; for the Sun/Jupiter-in-X's-exaltation forms XX.38 speaks of X's bhukti, so the period restriction may belong to X, not the
agent — a semantic question for the gate, unchanged by AM-20 (the descriptor is the only thing that now follows the anchor).

### Design v1.21 (2026-10-02) — AM-20 REVISED (Stream B, P1_FRAME_ANSWER v1.1 / amendments draft v0.19): lagna-counted descriptor; P1 minting GATED on migration 1233

Steward M20261002T031247-e16e. Stream B re-read Phaladīpikā Adh. XX in full and corrected its own answer; v1.20's lord-sign anchor is superseded.
1. **Descriptor = the inclusive count FROM THE LAGNA** (XX.34 "the Bhava it represents when counted from the Lagna"; XX.59). The writer's `dasha_lord` resolver counts
   from the lagna sign; `record_verifier.verify_p1_house_descriptor` re-derives it from the snapshot-bound L1 lagna and now catches a **lord-sign-counted** descriptor (the superseded
   first reading). Still a stored descriptor that nothing reads (the v1.20 tests stand: no rule module mentions it; a P1 window is identical for every value; a PG round
   trip shifting the descriptor changes only the descriptor). `RecordEdge.period_lord` / the agent-first anchor table / `expected_p1_anchor` are REMOVED — the anchor is now
   Stream B's `(period_anchor_lord, period_anchor_level)` pair in the natural key (one record per anchor lord; the Sun in Libra = two records on ONE contact, anchors
   (Sun, AD) and (Saturn, AD); support = span ∩ D(anchor, level)), which no existing column can carry.
2. **The switch** `p1_minting_requires_period_anchor_columns`: P1 transit-record minting is OFF unless the APPLIED schema carries both `period_anchor_lord` and
   `period_anchor_level` on `ka_gochara_relationship_record` (`RecordStore.p1_anchor_columns_available`, read from `pg_attribute` like the 1232 Moon-scope gate; one column is not
   enough) **and** this writer implements writing them (`P1_ANCHOR_MINTING_IMPLEMENTED`, False until the 1233 implementation lands — so migration 1233 arriving cannot silently turn on
   mis-keyed minting; that second reason is named `p1_anchor_minting_not_implemented`). When closed the record substep says so in its notes
   ("P1 transit records NOT minted — <reason>"), `_house_resolver(context, p1_minting=False)` returns `None` for `dasha_lord` occurrences (kgrr_evaluated_has_house_ck — a state,
   never an omission), and the other paths are untouched. The minting code is kept; the gate is tested on the schema without 1233, on a disposable schema with a STAND-IN for the two
   columns (switch logic only — the real DDL, natural key and anchored minting are the next step), and with a single column. 11 tests; 7 mutations, all killed.
3. **Next (blocked on 1233 existing on my test schema):** implement against it on this branch — anchored enumeration (XX.34–35 forms: MD; XX.37–38: AD/bhukti; XX.38 anchor =
   the lord whose exaltation (favourable) or depression/inimical (adverse) sign the Sun/Jupiter enters), natural-key + record_uuid with the anchor, supports = contact ∩ D(anchor, level),
   prerequisites over the ANCHOR's periods, inventory/verifier obligations; oracle O-PP-5.

### Design v1.22 (2026-10-02) — Codex round 8, R8-2 (per-class version SELECTION and supersession)

Steward M20261002T032818-3cf4 (scope: the all-NULL `5.0` candidate; numeric activation DISABLED with named reasons). The writer treated the sealed catalogue as the search: with `P3@1.0.0` and
`P3@1.1.0` sealed it produced two `included` pins of 30 obligations each — which 1206 (`multiple_included_versions`) rejects — and the verifier derived the same wrong answer.
* **Catalogue ≠ selection.** `rule_registry.BOUND_PATH_REFS` is the sealed CATALOGUE (every pin must be accounted for — `registry_unaccounted_path`);
  `SELECTED_PATH_REFS` (+ `CLASS_SELECTION_OVERRIDES`) is the ONE version of each path a class's search runs under (`selected_versions_for(class)` / `selected_path_version(class, path)`,
  read at call time, refusing a selection outside the catalogue or a path twice). Default = the 1.0.0 set: binding a successor into the catalogue never changes what any class searches.
  `bound_path_version` is gone — it returned "the first bound", which with two versions bound was an accident.
* **Planner** (`inventory.plan_class_inventory(selected_versions=…)`): every sealed version accounted; at most one `included`; a multi-version path with no selection is refused (never "all");
  an older version is `excluded/superseded_by_version` (1206's non-degrading reason: no ruling, a spec-grammar basis naming the amendment) ONLY when the registry-approved successor is the selected version
  AND that version is `included` for the class; every other non-selected version is accounted exactly as it would be if searched (excluded / computed_empty — path-level exclusions such as the P5 hold and
  the H-unknown ruling apply to EVERY version of the path); a non-selected version that WOULD be searched and has no superseder needs its own **composite-keyed** `(path, version)` ruling
  (a WITHHELD successor: `tier_withheld_by_ruling` + ruling_ref) or the plan is refused by name.
* **Independent verifier** (`inventory_verifier.derive_class_pins`): derives the same dispositions from its OWN supersession table (`_SUPERSEDED`, asserted equal to what the registry approves so a new
  approval cannot go unmirrored) and refuses (`Unverifiable`) what it cannot derive. **Historical replay** reuses the ORIGINAL selection stored with the inventory (`stored_selection` = the included version
  of each path; no new vector key, so Stream B's frozen vectors stay byte-identical); the writer's verify step additionally refuses a stored selection that drifted from the configured one.
  Writer: coverage, record and inventory phases use the class's selected version.
* **Tests** (22 + the registry tests rewritten): old-only, old+new (successor included → old superseded), successor withheld (composite ruling / refused without), no selection, a non-approved successor
  (refused), unknown-H (every version excluded with the ruling — never `superseded` with no superseder), held P5, a computed-empty successor, P1/P4; planner == verifier for six scenarios; on the REAL 1206
  schema the supersession plan passes `ka_gochara_search_completeness_violations` and the old all-included behaviour is flagged `multiple_included_versions`; replay under a changed configuration
  reproduces the stored digest. 11 mutations, all killed.

### Design v1.23 (2026-10-02) — Codex round 8, R8-1 (the consumed-input identity)

* **L0 = what the pair loader consumes.** `input_vector.py` selected `rule_type = 'vedha'`; the authority (and B's loader) is the 42 rows carrying a vedha house, all `favourable` — on the real
  data the selection was empty and `l0_rows` raised, masked by four synthetic `'vedha'` rows in `test_a53_inventory.py`. The L0 identity is now `vedha_derive.load_pairs(...).content_digest` (B's loader:
  validated, census-checked 36 cited + 6 UNSOURCED node rows; a missing/uncited/fabricated/duplicated row or an incomplete authority is refused by name → `InputDrift`), bound at BOTH boundaries — the
  builder through the loader, the verifier by an independent Postgres derivation (`input_vector_verifier.sql_l0_digest`: the same rows, canonical JSON + sha256 in the database, no loader code). The integration
  fixture is now **B's validated 42-row exhibit** (`l0_vedha_rows_2026_10_02.json`), with row-deletion / pair-alteration / citation-alteration / node-row / non-vedha-row / surrogate-id / empty-authority tests.
  `assemble_vector` takes `l0_digests` (an identity computed by the authority's own loader) beside the frozen-vector `l0_rows`, so B's 13 frozen literals stay byte-identical.
* **A dependency only when consumed.** `build_input_vector(l0_consumed=…)`; the writer's `_l0_consumed()` is `("bg_transit_rules",)` only while `VEDHA_SOURCE` is bound (today `None` ⇒ `l0 == {}`: the table is
  neither loaded nor bound and cannot block or shape the build — tested with the table DROPPED). `verify_live` / `verify_replay` default the consumed set to the STORED vector's own (a manifest never silently
  gains or loses a dependency). `vedha_derive` joins the evaluation implementation stage (the AST closure test caught it).
* **Complete historical replay.** `verify_replay(conn, stored, refs, **inputs)` rebuilds the WHOLE vector over the original references + original census + the ORIGINAL L0 set and compares every component
  (ephemeris files, probe, runtime library, L0, implementation, orb policy, rulings, sky convention) — an L0 / ephemeris / series / runtime / policy / implementation change is refused by component name. The
  old registry-only form is gone.
* **Independent input check beyond the registry** (`input_vector_verifier.verify_inputs`): registry + L0 + sky-convention content in Postgres; opened-file digests and the swisseph runtime library by direct
  hashing (located through `importlib.util.find_spec`, not the builder's helpers); node identity from the verifier's own literals; implementation sources re-hashed independently (the module LISTS are the
  governing-code closure the AST test checks). It returns `{"derived": […], "not_derived": ["orb_policy", "rulings_digest"]}` — those two live in builder code and are named, so a pass never claims them. Called at
  the manifest bind and at every substep's live check.
* **Runtime artifact identity.** `ephemeris.runtime = {swisseph_sha256}` (sha256 of the loaded extension file) is bound beside the version string and the 16-instant probe; present whenever the build supplies it
  (production always) and absent only for inputs that predate it — B's frozen literals are unchanged. **This adds a key B's fixture does not yet contain: asking B to extend the frozen cases.**
* 13 mutations, all killed. tests/l3: only the 3 pre-existing wp10_cutover failures.

### Design v1.24 (2026-10-02) — Codex round 8, R8-4 (verification: comprehensive, durable, gate-enforced) + the coupled R8-6 policy parts

* **One frozen qualification policy** (`window_qualification/1`, documented in `draft_windows`; the independent verifier re-implements the same table from its own code): (1) an UNQUALIFIED member whose channel
  is `for` or unknown ⇒ peak, score, evidence_for, evidence_against all NULL; (2) else a QUALIFIED function-valued member ⇒ the same NULLs under the named switch `dynamic_objective_solver_guarantee_not_available`
  (`allow_dynamic` lifts it for the solver's own tests; the writer never passes it — tested); (3) else the for-channel objective is determined — a population with no for-channel member (against-only) has the identically-zero
  objective, whose earliest maximum is the component start — and `peak`, `evidence_for` are stored; (4) `score` = the max LIVE record product at the peak over ALL live members of any channel (P4: the max-min value), NULL when a
  live member at the peak is unqualified; (5) `evidence_against` NULL iff the path cannot evaluate it or a live unqualified against/unknown member could feed it. **The demonstrated disagreement** (an all-against P2 Saturn house-8
  window at 1.0.0: builder all-NULL via an empty-qualified artifact, verifier "qualified but NULL") is resolved by this table — builder and verifier store/expect `peak = start, evidence_for = 0.0, score = NULL, evidence_against = NULL`
  (a PG test runs the review's case). The blanket `score <= evidence_for` assertion is gone (incompatible with the adopted score). With the switch no window is `UNVERIFIED_DYNAMIC`: a function-valued window is an exact reproduction of "no numeric result".
* **Verified fields.** `verify_window_semantics` reproduces interval membership, peak, score, evidence_for/against, **outcome valence** (Stream B's `valence.compute_valence` CALLED with the verifier's own derived arguments), severity,
  null_states and the `windows_detail` below; VERIFIED requires every window reproduced exactly. **Every expected window:** `window_gate.expected_windows` derives the expected set (union of admitted scored supports; P4 intersection) in
  Python; the database recomputes it separately (`ka_gochara_eval_window_expected_digest`); a stored set that omits or invents a window is refused before a result exists.
* **Durable, generation-bound, gate-consumed — migration 1240 (authored, unapplied):** `ka_gochara_eval_window_verification` (one row per grain/verifier: status, policy_version, expected/stored/reproduced/unverified counts,
  expected + stored interval digests, **stored-content digest** (staleness), fields_verified, the generation's snapshot `input_digest`, and `windows_detail`); `ka_gochara_window_verification_violations` (missing / not VERIFIED /
  policy unknown / count mismatch / stale / expected-set mismatch / wrong input identity, for every INCLUDED P1–P4 pin) and `ka_gochara_candidate_gate_violations` (1206/1232 completeness ∪ window violations — no 1206/1232 function is
  redefined; calling it from the seal path is the sealer's). Write guard = the generic chart write guard (`no_update`), sealed generations frozen, sealed rule only, TRUNCATE refused; CHECKs make `VERIFIED` total (nothing unverified,
  every stored window reproduced, expected digest = stored digest) and the provenance mandatory (`jsonb_array_length(windows_detail) = windows_stored`). **Production caller:** the writer's window phase persists the result (naming the case
  where 1240 is absent — "gate cannot pass"), `satisfies_gate` is now CALLED by `record_verification`, and `verify:<class>` raises `CandidateGateRefused` for a class that cannot pass.
* **Objective + qualification provenance** persisted by RECONSTRUCTION (mandatory, in `windows_detail`: objective name/value, structured reasons, affected channels — verifier-derived), no change to 1156.
* **Member support against INDEPENDENT geometry.** `verify_member_geometry` probes the EPHEMERIS (the writer's Swiss longitude probe) 1 s inside and just outside each end of every member contact span: a sign for residence, the dṛṣṭi source
  signs for aspect-to-span, an orb band around each ray level for point conjunction/aspect — own orb + angle tables (asserted equal to the kernel's, imports none of it); a horizon-truncated end is probed inside only. The window phase
  runs it after `verify_member_support`; a span the sky does not support fails the build. (This surfaced fixtures whose constant Swiss stand-in contradicted their seeded geometry — fixed to be consistent.)
* **Included-P2 inventory derivation** (`inventory_verifier._p2_obligation_bytes`: own polarity + cited favourable-house + adverse-plan tables, asserted equal to the rule modules'): planner == verifier for all 26 classes; the stored
  digest of a P1+P2+P3+P4 plan is reproduced. No included path is "unverifiable" any more, so `verify:<class>` now reaches the aspect-span sampling check and the window gate (two writer tests updated to say so honestly).
* ~45 mutations, all killed except none outstanding. The 17 `test_wp10_cutover` ERRORS/failures this run are the shared `wp6` DB (baseline-failing, not this change).

### Design v1.25 (2026-10-02) — 1240 reworked to Stream B's contract note + the steward's clarification; AM-16 schema /2

Steward M20261002T034837-d6de / -f61a / -0c4b + Stream B's `MIGRATION_1240_CONTRACT_CONSTRAINTS_v1_0` (campaign/pravaha 9a8042796). Supersedes the v1.24 description of 1240 where they differ.
* **Roles.** The BUILDER holds **nothing** on the verification table (the writer cannot verify itself; 1206 §7's builder write of the inventory verification is not repeated). The VERIFIER role (`gochara_verifier`) gets
  SELECT/INSERT + pre-seal DELETE (the write guard enforces both) and SELECT on what it reads + EXECUTE on what the write path calls; the SEALER (`gochara_sealer`) gets SELECT + EXECUTE on the gate. Grants are
  role-existence-guarded, table-level, explicit, no `SECURITY DEFINER`, derived by the 1206-R6 loop on a deployment-faithful mirror (PUBLIC EXECUTE revoked, roles present) — the live suite proves each
  EXECUTE necessary. **Consequence, in the migration header and here:** neither role exists in production, so until the native provisions them NO verification row can be written there and the candidate gate stays
  CLOSED — the roles decision is a named blocker of the first candidate build. The writer is privilege-aware: with no INSERT it says "verification result NOT persisted — no verifier principal is provisioned (the candidate
  gate stays closed)" and `verify:<class>` reports the gate CLOSED instead of failing every class (the seal trigger is the authority); with the privilege it still raises on a class that cannot pass.
* **ONE additive BEFORE INSERT trigger on `ka_gochara_generation_seal`**, `…_zz_window_verified` (fires after 1206's `…_z_search_complete`; no 1153/1206 function replaced; chart EXCLUSIVE → global SHARED; no new family key) with the
  mandatory REPLAY branch: a first seal runs `ka_gochara_window_verification_violations`; a replay runs integrity only — a generation sealed BEFORE 1240 has no rows and replays cleanly; rows that exist must still equal the frozen windows;
  replay never reads today's catalogue. `ka_gochara_candidate_gate_violations` = completeness ∪ window violations.
* **Write guard = the 1206 trio** (statement lock → chart key first, sealed generation refuses INSERT/UPDATE/DELETE, rows immutable → no TRUNCATE), NOT 1155's table-keyed guard; the row requires a FINALISED inventory header and an INCLUDED pin
  (composite FKs, ON DELETE CASCADE so a candidate rebuild replaces it). PK = the grain `(chart, generation, class, path, rule_version)`.
* **Provenance on the WINDOW (the 1233 pattern, steward: "persist it, not reconstruct it").** `ka_gochara_eval_window` gains nullable `objective`, `objective_value`, `qualification` (closed-key JSONB shape CHECK, objective token CHECK, and a CHECK that
  an unqualified window carries no numeric result); the builder writes them (`WindowStore`), a sealed generation stays frozen automatically, and the independent verifier requires the persisted values to equal what it derives from the members and the
  bound factor rows (a window without provenance, or with a different one, is refused by the verifier and by the gate). The verification row no longer carries `windows_detail`.
* **Digests hash REAL columns as IEEE bits** (`float4send`, hex) with NULL distinct (`ka_gochara_f4_token`); a FROZEN literal preimage + sha256 is asserted in a static test, and the database digest equals the Python-built preimage of the stored values.
  Gate also refuses SHORT field coverage (the SQL required-field list is asserted equal to the verifier's governed list).
* **Tests** (live on PG15, restricted roles): builder holds nothing / is refused; verifier derives + verifies + persists with only the migration's grants and each EXECUTE is individually necessary; sealer runs the gate/replay check; the seal is refused for each of
  {missing, UNVERIFIED_DYNAMIC, FAILED, count mismatch, stale, short field coverage}, accepted when all VERIFIED, then the generation is frozen (verification and window UPDATE/DELETE/INSERT refused); a pre-1240-sealed generation replays cleanly; a replay with a drifted
  row is refused; the trigger fires after 1206's and is the only one added; a verification row needs a finalised inventory + included pin; static contract (no BEGIN/COMMIT, one seal trigger, no SECURITY DEFINER, no column-level grant, builder granted nothing, no applied
  function replaced, only the three window columns added). 1206's own seal trigger is DISABLED on the disposable DB to isolate 1240's guard (the full 1206+1240 seal is the protected-window rehearsal's). 15 SQL/Python mutations of the guards: all killed.
  **Not done here (stack dependency):** the `migrate.ts` / `deploy.yml` / `jataka_schema_capability` / `gochara_a5_1_contract_static` wiring — those edits sit on B's 1232/1233 branches (#2909/#2919), which this branch does not contain; to be added when the stack lands.
* **AM-16 schema /2 (Stream B's frozen vectors v2, campaign 6ba0c5fc7).** `VECTOR_SCHEMA = "ka_gochara_input_vector/2"`; the ephemeris component binds `library_sha256` (sha256 of the file `find_spec('swisseph').origin` names — the loaded compiled
  extension) and `platform` (`<system>-<machine>`), both REQUIRED (a new build without them is refused; there is no "absent" form; a /1 vector is refused by the schema check). My provisional `ephemeris.runtime` key is gone. The v2 fixture is vendored
  (16 cases incl. `library_artifact_only`, `platform_only`; the v1 file is removed); the independent verifier derives both fields itself (find_spec + hashing; its own platform string). `probe_digest` stays an end-to-end tripwire per B's AM-16 settlement.

### Design v1.26 (2026-10-02) — Codex round 8, R8-5 (scope ≠ completeness) + the steward's M…042833 / M…043431 follow-ups

* **R8-5.** `scope_response.coverage_response(…, horizon=None)` keeps two things apart. SCOPE (`stored_scope`, read back from the bound manifest vector) is always carried; COMPLETENESS is derived separately from the REQUESTED class/horizon's
  own state and `complete_within_scope` is the ONLY positive state (one place in the module says it): the manifest is PUBLISHED and its bound vector equals the search snapshot's; the class has a FINALISED inventory bound to that snapshot whose horizon covers
  the request; the event-class coverage partition completed the request; no `missing_inputs` interval; the inventory is independently VERIFIED (a verification row equal to the digest); every included P1–P4 window grain is VERIFIED/current/input-bound (1240).
  Otherwise a named state with reasons — `refused` (no scope), `not_published`, `class_not_searched`, `stale_binding`, `incomplete_horizon`, `incomplete_inventory`, `unverified`, `evidence_unavailable` (no search tables / 1240 not applied) — never "complete". Each returned
  window carries its PERSISTED qualification provenance (1240; never invented for a window without an id) and a numeric P2 window carries the cited vedha scope `excluding_on_demand_moon_obstruction`; on-demand answers are listed beside the unchanged scope.
  Tests (19, live): the review's manifest-only fake, unpublished, missing class, three incomplete-horizon requests, an incomplete coverage partition, a stale binding (manifest vector moved; inventory under another snapshot), missing inputs, unfinalised / unverified inventory, unverified / missing window result,
  1240 absent, before/after on-demand, a manifest without the scope, the complete case; 14 mutations killed. (On a schema without 1232 the Moon-resolved period portions stay honest `missing_inputs`, so a class is never complete there — the complete test uses a labelled stand-in for 1232's accounting.)
  **Call sites:** there is NO '5.0' window serving reader in this repository yet (the only `kala_gochara_windows` references are the legacy cockpit clear/query routes); the constructor is the single mandatory entry for the readers B's v1_10 §C2 names as a flip pre-condition — a TypeScript reader must implement the identical derivation or call the sidecar.
* **1240 follow-ups (steward M…042833).** The grants block PRINTS which principals it found (`RAISE NOTICE … issued to role …` / `role … NOT FOUND — NO … grants were issued`), tested by renaming each role away. The builder holds nothing, so the writer does not even READ the gate: with no INSERT the window substep records
  `verification_pending_verifier_principal` (never an error, never a builder-written row) and `verify:<class>` reports the gate CLOSED with the same token; `window_gate.require_candidate_gate` itself raises `CandidateGateRefused` by violation name.
* **`ephemeris_component` (steward M…043431).** ONE public function `input_vector.ephemeris_component(ephe_path, bodies, jd_lo, jd_hi, *, files_probe, series_probe)` returns the stored form `{backend, swe_version, library_sha256, platform, files, probe_digest}` and REFUSES without a path, with no opened file, or on a Moshier fallback
  (the probe checks the Swiss retflag bit on every call); `build_input_vector` now takes its component FROM it (`assemble_vector` validates a pre-shaped component against the closed key set) — no second definition. `'4.1'` writer untouched. **Bodies a `'4.1'` substep passes to swisseph** (read from the code, not run): step06 (`enumerate_core` via `sample_knots` / `swiss_bisect`) — the
  eight PERSISTED bodies Sun, Mercury, Venus, Mars, Jupiter, Saturn, Rahu (mean node) and Ketu (derived from the mean node); step06a (class context) — none (L1 facts only; `swe` is used for calendar conversion); step06b (windows projection, `planet_pos_fn(body, jd)`) — the contact bodies (the same eight) **and the Moon** (the P6 tārā annotator reads the transit Moon).
  So the later call must cover `Sun, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ketu` **plus `Moon`** over the 4.1 horizon [1998-01-01, 2026-04-18) (+1 day padding).

### Design v1.27 (2026-10-02) — Codex round 8, R8-3 (AM-21 + part 2: the P1 period ANCHOR)

* **Anchor = (lord, level), not the agent.** `RecordEdge.period_anchor_lord / period_anchor_level` (P1 transit edges only; the natural key and `record_uuid` include them only then, so P2–P4 and natal rows are unchanged). `enumerate_p1_edges` emits one edge per
  reading: own-transit forms XX.34–35 / XX.37 (agent = anchor, at MD, AD and PD over own ∪ exaltation ∪ debilitation signs) and the XX.38 forms (Sun/Jupiter in ANOTHER graha's exaltation sign, and the Sun in another graha's debilitation sign — anchor = that bhukti lord
  at AD). Marriage: 84 transit edges. The Sun in Libra is four readings: (Sun, MD/AD/PD) own debilitation and (Saturn, AD) Saturn's exaltation — role aliases sharing ONE physical `contact_id` (counted once).
* **Support = contact (clipped) ∩ D(anchor lord, anchor level)** from the pinned rows (`dasha_read.rows_for(lord, level)`, level-aware; `None` keeps the legacy every-level union for the other consumer), half-open, disjoint pieces kept; an anchor with no rows at that level is
  stored unrestricted with an explicit `unknown` prerequisite (never admitted as running). The natal relation / licence is judged on the ANCHOR lord (a testimony-licence anchor is not minted and is counted). Moon-tier exclusion still follows the transiting body.
* **Schema.** Stream B's 1233 (`period_anchor_lord`, `period_anchor_level`, pair/vocab/path-exact CHECKs) is now part of the test chain and the P1 minting gate is OPEN when the columns exist (`P1_ANCHOR_MINTING_IMPLEMENTED = True`); on a schema without 1233 the gate stays CLOSED
  with the named switch; an anchored edge on such a schema is refused, never mis-keyed. House descriptor unchanged (inclusive count from the Lagna, AM-20).
* **Independent verification.** `verify_p1_support` now derives D(anchor, level) in SQL from the record's STORED anchor (runs grouped by (lord, level_n)) — not the agent's periods; `verify_p1_anchors` derives the anchor SET per contact from the verifier's own own/exaltation/debilitation
  tables (minus testimony-licence lords via B's `permission.period_lord_relation`) and refuses an omitted, invented or wrong-level reading. Both are run by `verify:<class>`.
* **Tests (live, with the real 1233).** O-PP-5 literal (two records, one contact_id, anchors (Sun, AD)/(Saturn, AD), supports span ∩ D each); O-PP-4 (a) no rows ⇒ unknown, (b) disjoint pieces never bridged, (c) the level is part of the domain, (d) a period touching only at an endpoint
  contributes nothing; natural key includes the anchor only for P1; 1233 CHECKs; level-aware reads. Mutations killed: domain from the agent's periods (XX.38 reading), every-level union, one record anchored on the agent only, wrong level on a stored reading, rewritten support.
* **Flagged, not changed here.** (1) The inventory obligation model represents the agent as the role token `period_lord:md|ad|pd`; it does not represent XX.38 searches (a Sun/Jupiter contact read under another lord's AD), so the inventory's P1 obligations understate the readings the
  records now carry. (2) The PD level has no verse; it is the specification's flagged extension and is minted and verified as such. (3) The inimical-sign branch of XX.38 stays deferred.

### Design v1.28 (2026-10-02) — Codex round 8, R8-6 remainder + the steward's M…050622 follow-ups

* **P4 keeps its unknowns.** `_agent_activity` no longer filters `None` before the agent max: if ANY of an agent's live records is unknown at `t`, the agent's activity — hence the max-min objective — is unknown there, and the piece (so the window) is NULL with
  `objective_unknown_over_component`. The review's three-record case (Jupiter A = 0.4 known, Jupiter B unknown from day 5, Saturn C = 0.9) used to store min(0.4, 0.9); it is now NULL + reason. (A record unknown over its WHOLE support is unqualified at the record, as before.)
* **The tie tolerance is between distinct extrema only.** `maximise_earliest` reduces the scan to its distinct local extrema (runs equal to float noise `_EPS`=1e-12 are one plateau), resolves each on its own — a hump by bracketed golden-section to 1 ms, a plateau/step by bisecting its start to the earliest instant
  that reaches its value — and applies the frozen 1e-9 `_TIE` ONLY across those candidates (earliest wins inside it). The 27-second shift down a smooth hump's shoulder is gone (the O-SM-4 parabola test now asserts < 10 ms); a point contact's exact hint is reported exactly; humps 5e-10 apart tie to the earlier,
  5e-6 apart do not; a noisy flat-top plateau starts at its first instant.
* **Complete state boundaries, or no qualification.** A record with a STATE-valued operand (dṛṣṭi source, vedha overlay) must carry `state_boundaries` that the store asserts complete (`state_boundaries_complete`), else it is UNQUALIFIED (`state_boundaries_incomplete`) and the window NULL — an unlisted change could
  hide an interior gap a piece would bridge, or an island that scores 0. The store asserts completeness only for a dṛṣṭi record whose whole support lies inside the class's coverage partition's completed horizon; no source of vedha overlay edges exists, so a vedha-carrying record is never complete. The independent verifier derives the
  SAME rule from its own code (`_boundaries_complete`/`_record_state`: relation, coverage read in SQL, state-valued factor ids) — two derivations, one reason token. Consequence: until a vedha-edge source exists, P2 windows with a bound vedha source are NULL under `state_boundaries_incomplete` (previously
  under the dynamic switch); the pg tests of window arithmetic/unverified-dynamic keep their coverage by emptying both sides' state-valued sets and say so.
* **Steward M…050622 follow-ups.** B's stack (0f4470efd: 1232, 1233, 1240 wiring) was merged earlier (never rebased) and main merged again today (the three wp10_cutover failures are gone). CI: a new step after the 1206/1232/1233 live suite runs the A5.3 pytest live suites (1240 static + gate + roles/seal flows, P1 anchor, P1 support, scope completeness)
  against the CI Postgres through `GOCHARA_A53_ADMIN_DSN` with `GOCHARA_A53_REQUIRE_DB=1` (an unreachable server FAILS instead of skipping; verified locally: 84 passed, 0 skipped). Intended route for the '5.0' serving reader (NOT built, NOT mounted — a flip pre-condition, not this milestone): the SIDECAR
  exposes `GET /gochara/v5/windows` (chart_id, generation, event_class, optional horizon) returning `scope_response.coverage_response(...)`; one definition in Python, any TypeScript caller proxies it (a TS twin would be a second derivation).
  Test-environment note: since main's SE_EPHE_PATH rule, `tests/l3/ka_kshetra`, the muhurta route test and the W2 frontier preservation test need `MARSYS_TEST_SE1_DIR` (or `SWE_EPHE_PATH`) pointing at the three SHA-pinned .se1 files; with it set they pass (483), without it they fail loudly by design.

### Design v1.29 (2026-10-02) — the XX.38 delivery searches enter the inventory (steward M…053914; "no record ahead of the inventory")

* **The defect (my own flag (a)).** After R8-3 the records carried XX.38 readings (Sun/Jupiter in another graha's exaltation sign, the Sun in another's debilitation sign, anchored on that bhukti lord's AD) that the inventory never obliged: its P1 obligations were the role tokens `period_lord:md|ad|pd`, which resolve to the RUNNING LORD, never to the Sun or
  Jupiter. A class's P1 completeness claim therefore understated what was searched.
* **Option (i), inside the existing grammar — no migration.** `_plan_p1` additionally emits one CONCRETE-agent obligation (agent = `sun`|`jupiter`, relation `residence`, role `period_lord`, target `span:n`, frame `dasha_lord`) for every P1 transit edge whose agent is not its anchor lord — 8 Sun targets (signs 1, 2, 4, 6, 7, 8, 10, 12) and 6 Jupiter targets
  (1, 2, 6, 7, 10, 12) for marriage — each covering the WHOLE horizon with the capability-determined state, like every other non-role transit search. Why anchor-free: 1206's obligation 9-tuple has no anchor and the ledger digest preimage `ob_id|start|end|state|input_digest` has no domain, so an AD-domain cut would be
  unverified prose in `detail`; and the search it describes (the body's sign contacts over the horizon) IS whole-horizon — the AD domain restricts the record's SUPPORT, and the anchor set is verified at the record by `verify_p1_anchors`. If Stream B wants the anchor carried on the obligation itself that needs the grammar extended (a migration); this milestone does not.
* **Independent derivation.** `inventory_verifier._p1_obligation_bytes` derives the same set from its own exaltation/debilitation tables (Sun and Jupiter × every OTHER graha's exaltation sign, the Sun × every other graha's debilitation sign); with its delivery half removed three verifier tests fail (digest mismatch).
* **Tests.** The literal expected set (written out, not derived); the whole-horizon interval; `every P1 transit edge is obliged` for marriage / bereavement / career_entry / illness_acute (own-form edges by the role token of their anchor level, XX.38 edges by the concrete obligation); a mutation test that reinstates the defect
  (planner without delivery obligations leaves XX.38 edges unobliged) and the verifier mutant above. Named limits unchanged: PD level has no verse (flagged extension), inimical-sign branch of XX.38 deferred.

### Design v1.30 (2026-10-02) — the 1240 live-DB suites, and two design notes (steward M…055158; Codex round 9 running)

* **The 1240 / 1233 live-DB suites — exact files and how CI runs them.** They are **pytest**, not vitest, under `platform/python-sidecar/tests/l3/gochara/`; each builds its OWN throwaway database (`a53t_*`) and cluster roles through the admin DSN, applies the real migrations verbatim (1081, 1152–1157, **1233**, 1206, **1240**), and drops everything afterwards:
  `test_a53_migration_1240_static.py` (9: static contract + the FROZEN digest vector) · `test_a53_window_verification_gate.py` (16: the generation-bound result and the candidate gate) · `test_a53_window_verification_roles.py` (19: faithful builder/verifier/sealer principals, grants, the seal trigger and replay branch) ·
  `test_a53_p1_anchor.py` (13) · `test_a53_p1_support.py` (8) · `test_a53_scope_completeness.py` (19). CI: `.github/workflows/ci.yml` job `db-integration-tests`, the step **"Pravāha A5.3 — migration 1240 / 1233 live-DB suites … REQUIRED, never skipped"** (directly after the 1206/1232/1233 vitest step) runs exactly these six files with
  `GOCHARA_A53_ADMIN_DSN=postgresql://postgres:postgres@localhost:5432/postgres` and `GOCHARA_A53_REQUIRE_DB=1` (an unreachable server FAILS instead of skipping — `test_a53_inventory.py` and `test_a53_record_store.py` honour it); locally the same command passes 84, 0 skipped.
  Locally: `cd platform/python-sidecar && GOCHARA_A53_REQUIRE_DB=1 python -m pytest <those six files> -q`, with a PG15 server reachable at `GOCHARA_A53_ADMIN_DSN` (default `postgresql://wp6:local@localhost:55434/postgres`).
* **Design notes (no code).** `A5_3_DAY_ON_DEMAND_DESIGN_NOTE_v1_0.md` — the P6 day tier: what the Moon half already does, the serving-time function, parent/context resolution, testimony-only operators, receipt, sealed-generation behaviour, tests owed, holds.
  `A5_3_VERIFICATION_JOB_RUNNER_DESIGN_NOTE_v1_0.md` — the ND-ROLES option-A runner: entry point, identity self-check, refuse-by-name preconditions (unsealed candidate manifest, complete build, unchanged inputs), the per-class sequence over the existing verifier modules, outputs/exit codes, what changes in the writer, tests.


### Design v1.31 (2026-10-02) — Codex round 9, R9-4: the restricted builder can insert a window

* **The defect.** 1240's window CHECK (`kgew_qualification_shape_ck`) CALLS `ka_gochara_window_qualification_ok(jsonb)`; production revokes PUBLIC EXECUTE; no migration gave `data_plane_builder` EXECUTE on the new helper (1234's grant closure predates it) — a table INSERT grant does not carry it, so post-1240 the restricted builder could not insert a window.
  My role suite missed it because it built as SUPERUSER.
* **The fix (1240, unapplied so editable).** One role-existence-guarded grant — `GRANT EXECUTE ON FUNCTION public.ka_gochara_window_qualification_ok(jsonb) TO data_plane_builder` — with the found / NOT FOUND `RAISE NOTICE` pattern of the other grant blocks; still ZERO privileges on the verification table. The static test now asserts the builder's grants are exactly that one statement.
* **The proof.** New `test_a53_builder_restricted_flow.py` (in the CI step): the faithful mirror now applies the REAL builder-grant migrations after 1240 (1216 tables, 1220 functions, 1234 window tables/functions — 1234 merged from `pravaha/b6-1234-eval-window-builder-grants`) with PUBLIC EXECUTE revoked, and runs the complete build — convention, manifest, snapshot, inventory, coverage, sky events, records, windows —
  AS `data_plane_builder`; the builder holds nothing on the verification table throughout and the in-build verification only REPORTS (`verification_pending_verifier_principal`). Mutation: `REVOKE EXECUTE` on the helper makes the same flow fail with `permission denied for function ka_gochara_window_qualification_ok`.
* **A second, larger gap the restricted flow exposed (not 1240's, reported to the steward).** With every reviewed grant migration applied the builder still cannot REPLACE or FINALISE record-table rows: it lacks DELETE on `ka_gochara_relationship_record` and `ka_gochara_contact` (the writer's AM-3 delete-then-insert replace; 1216 says "replacement is impossible by design"),
  UPDATE (admission_state) on `ka_gochara_relationship_record` and UPDATE (result) on `ka_gochara_record_prerequisite` (the F5 finalisation). Found by running the flow TWICE (the second run is a rebuild) as the restricted builder and checking every executed INSERT/UPDATE/DELETE against `has_table_privilege`. Until Stream B's migration exists the faithful mirror applies
  `fixtures/pending_builder_record_grants.sql` (exactly those four grants, column-level UPDATE) and says so; the migration's number is B's (the reviewer's note: 1235 cannot follow the window). The 1206 inventory UPDATE (finalisation) is already column-level for the builder.
* **Test files named for CI** (v1.30's list plus this one): `test_a53_builder_restricted_flow.py` (3).


### Design v1.32 (2026-10-02) — Codex round 9, R9-1: ONE all-NULL result policy, selected by the manifest

* **The defect.** "Dynamic solving disabled" is not "all NULL": constant objectives and empty for-channel sums stayed numeric (P3 residence @1.1.0 stored score 1.0/evidence 1.0; P4 score 1.0/evidence 2.0; an all-against P2 stored evidence_for 0.0 + a peak), the independent verifier reproduced them, and 1240's CHECK permitted them — builder/verifier agreement is not compliance with the milestone.
* **Two named policies, one selected by the generation's MANIFEST.** `all_null_candidate/1` (this milestone): EVERY numerical result field — score, evidence_for, evidence_against, objective_value, severity — NULL for every path and channel composition, peak absent, valence `unqualified`, reason `all_null_candidate_policy`; interval, members, record ids, memberships and accounting counts stay populated and the per-member classification still fills `unresolved` (the audit trail survives).
  `window_qualification/1` stays documented and tested as the policy that applies when numbers are enabled. The selection is a REQUIRED key `result_policy` of the manifest input vector (**schema `ka_gochara_input_vector/3`**, steward-approved DECIDE-1; the frozen fixtures are `am16_vectors_frozen_v3.json` — the /2 file is removed, a `result_policy_only` case added, B to confirm and make normative);
  the writer's manifest step takes the policy as a build INPUT (`ctx.config['result_policy']`, default the milestone's) and every later stage reads it BACK from the stored manifest (`result_policy.manifest_policy`) — nothing downstream holds a policy constant; replay/live checks reuse the manifest's own value.
* **Four implementations of one name.** (1) Builder: `draft_windows(policy=…)` decides before any objective is evaluated, so no composition can store a number. (2) The independent `window_verifier` keeps its OWN literals (a test asserts equality and that it imports nothing from the builder), reads the policy by its own SQL, expects all-NULL under the policy, refuses a manifest/explicit-policy disagreement, and records the manifest's policy as the verification row's `policy_version`.
  (3) 1240's window CHECK: the qualification shape now REQUIRES a `policy` key from the two names, and `kgew_all_null_policy_ck` refuses any number, peak, severity, non-`unqualified` valence or other reason under `all_null_candidate/1`. (4) The candidate gate (`ka_gochara_window_verification_violations`) gains `result_policy_not_selected`, `window_policy_differs_from_manifest`, `window_verification_policy_differs_from_manifest` and `window_carries_a_number_under_all_null_policy`
  (the verifier and sealer roles now also read `kala_gochara_publication`).
* **Tests.** `test_a53_all_null_policy.py` (11, pure: the reviewer's three cases numeric under `window_qualification/1` and NULL under the policy, every path/class composition, accounting unchanged, the audit trail survives, unknown policy refused) and `test_a53_all_null_policy_db.py` (11, real schema: manifest binds /3 + policy, window phase reads it back, verification rows carry it, a qualification-policy manifest is followed by every stage, a manifest without a policy refuses, the CHECK refuses each numeric field and the valence,
  the gate and the independent verifier each refuse a numeric window with the CHECK removed, windows under another policy are refused by both, an explicit policy cannot override the manifest). Mutations killed: table CHECK, gate arm, builder early-out, verifier branch. The legacy fixtures that exercise numbers-enabled semantics now SELECT `window_qualification/1` in their manifest (the sweep-pg fixtures publish a candidate manifest; the gate/roles worlds set `result_policy`). Both new files are in the CI step.

### Design v1.33 (2026-10-02) — Codex round 9, R9-2: verification proves the COMPLETE output set and stays current

* **The defects.** (1) `verify_window_semantics` read the stored membership links and reported `membership` verified; (2) 1240's content digest hashed window fields + existing member ids and its expected digest only the union of admitted supports, so the reviewer's attack — verify, then insert a valid admitted scored record wholly inside the window and OMIT its membership link — changed none of what was hashed;
  (3) `verify_p1_anchors` started from relationship RECORDS, so a contact with every anchored record omitted returned `{"contacts": 0}` successfully.
* **(i) Expected membership, independently, both directions.** The verifier now derives, from the grain's own admitted scored records, the full expected member set of every window (supports overlapping it; P4's members extend past the window) and compares it with the stored links both ways, plus "an admitted record with a support sits in no window"; the numeric derivation runs over the EXPECTED members. `membership` is in `fields_verified`
  only because that comparison raises on any difference. The gate does the same in SQL (`window_membership_not_expected`: missing / unexpected / orphan counts).
* **(ii) Verification bound to every derivation input.** New column `derivation_inputs_digest` on the verification row and SQL function `ka_gochara_eval_window_inputs_digest` over a canonical preimage of: every record of the grain (identity, agent, relation, kind, role, admission, house, anchor, target, contact, supports), its prerequisite results, the referenced contacts (t_in/t_out), the snapshot's input identity, the manifest vector (digest) and the result policy.
  The verifier builds the SAME preimage in Python from its own reads (own canonicalisation — `window_gate.derivation_inputs_preimage`/`_canon`, pinned by a literal test; equality with the SQL function is asserted on the real database, empty grains included); the gate recomputes it (`window_verification_inputs_changed`). The reviewer's attack, a flipped prerequisite result, a moved contact, a changed manifest vector and a changed record each make the stored verification stale at the seal; the old gate (windows + expected set + member ids only) is shown to miss the attack.
  1240 now has a `migration_1233_not_applied` preflight (the digest reads the anchor columns); the verifier/sealer roles read the extra tables (`ka_gochara_record_prerequisite`, `ka_gochara_contact`, `ka_gochara_physical_object`, `kala_gochara_publication`).
* **(iii) P1 anchors from the EXPECTED CONTACT SET.** New independent module `contact_reconstruct` (own speed bounds, imports nothing from the builder's geometry) reconstructs, from the ephemeris alone, the maximal in-sign intervals of every body over the inventory horizon; `verify_p1_anchors(…, position_at)` starts from every expected P1 contact (own forms and XX.38), requires it in the ledger with exactly the derived anchor set
  (minus testimony lords), and refuses a contact carrying P1 records that the ephemeris does not reconstruct. Zero-output cases both ways: contacts expected but no records ⇒ fail; no contacts expected and none stored ⇒ pass. No ephemeris ⇒ `GeometryUnavailable` (no complete-search claim). The guarantee is a sentence with its assumption and a NAMED limit: under smooth motion (per-body speed bound) every in/out-of-sign interval of at least 60 s is found and crossings located to 1 s; excursions shorter than 60 s are not excluded.
  The reconstruction is the shared base of R9-3's certification.
* **Tests** (all in the CI step): `test_a53_complete_output_verification.py` (11), `test_a53_p1_contact_completeness.py` (15, incl. the interior exit/re-entry, a sub-step excursion found only by the boundary-aware refinement, the named limit), the updated anchor/gate/roles suites. Mutations killed: inputs-digest comparison removed, verifier trusting stored links, gate membership arm removed, endpoint-only reconstruction, record-started anchor verifier.


### Design v1.34 (2026-10-02) — Codex round 9, R9-3: complete contact geometry, and what the input verifier does and does not derive

* **The defects.** (1) `window_verifier._probe_contact` checks a position just inside and just outside each END of a stored span; a residence `[0,10)` with the body outside the sign during `[4,6)` passes, and the separate aspect-to-span check does not establish complete residence/point-contact output for every admitted obligation — NULL numbers would not repair a falsely continuous support.
  (2) The independent input verifier hashed the FILE NAMES the stored vector supplied (it did not establish the opened-file census), and its `not_derived` list named only `orb_policy` and `rulings_digest` while backend, version/probe and scope/schema semantics were not derived either.
* **The certification (`contact_certify`, over `contact_reconstruct`).** For every concrete transit obligation of the class (role-token P1 obligations are covered by `verify_p1_anchors` over the same reconstruction) the verifier reconstructs, from `position_at` alone and over the INVENTORY horizon, the contact set the obligation implies — residence on a sign or nakṣatra (generalised partition intervals), aspect-to-sign (the union of the source signs' intervals),
  conjunction/aspect to a point (orb-band intervals around each aspect point) — and compares it with the ledger BOTH ways: an interior exit/re-entry, a bridged or truncated support, an omitted contact and an invented one each fail. It runs in the writer's `verify:<class>` step (and the notes carry its counts and the limit). Incomplete evidence (no ephemeris, an undeterminable position) raises `GeometryUnavailable`: no verification row is
  written and the gate stays closed — "incomplete boundary evidence prevents a complete-search claim".
* **The guarantee, as a sentence with its assumption (steward addition).** *Under smooth motion (a body's speed never exceeds its stated bound) every in-sign / out-of-sign interval of at least 60 s is found and each crossing is located to within 1 s; excursions shorter than 60 s are NOT excluded.* Method: sample every 6 h; from a sample at distance `d` from the nearest edge the state cannot flip within `dt` when `d > vmax·dt`, so any step that could reach an edge is bisected down to 60 s (a smooth sub-step excursion is found by exactly this refinement — tested, and an endpoint-only variant fails that test).
  `NAMED_LIMIT` and `GUARANTEE_ASSUMPTION` are returned by every certification and reported in the verify notes; the reconstruction is memoised across classes only for a position source that declares a `cache_key` (the writer's Swiss source). Cost: about 41k samples per body over the 28-year horizon, shared by all 26 classes.
* **The input verifier derives more, and names what it does not.** `derive_opened_file_census` (its own body list, own 120-day sampling, read back from the library's own record; a Moshier fallback refused) must EQUAL the stored census (names, then hashes); `derive_backend_and_version` and its own copy of the series-probe definition (`derive_series_probe_digest`) check backend, swe_version and `probe_digest`; schema, `stored_scope` and `result_policy` must be NAMED members of the verifier's own vocabularies.
  `NOT_INDEPENDENTLY_DERIVED = (orb_policy, rulings_digest, consumed_range, schema_semantics, scope_semantics, result_policy_semantics)` — the span the census was taken over is supplied by the caller (`input_vector.consumed_jd_range`, one definition), and the verifier checks vocabulary, not what a token means to a consumer; with no span supplied `ephemeris.census` itself moves into `not_derived`.
  On the REAL files the verifier's census, probe and backend equal the builder's (test). The verifier's own Swiss probes are registered as Swiss owners.
* **Tests** (CI step): `test_a53_contact_certification.py` (8: complete world, the reviewer's interior gap — which the endpoint probes still pass —, omitted/invented/truncated contact, incomplete evidence, point and aspect reconstruction), `test_a53_p1_contact_completeness.py`, and the rewritten input-vector tests (census set equality both ways, tampered backend/version/probe/schema/scope/policy, the real-files equality, the accurate `not_derived`). Mutations killed: certifier trusting the ledger, census comparison removed, endpoint-only reconstruction.


### Design v1.35 (2026-10-02) — R9-9 (derived boundary tolerance) folded into R9-3, and the real 1242 replaces my stand-in (steward M…073918 / M…075228)

* **R9-9 (Stream B's all-guards rehearsal on the REAL sky).** `verify_member_geometry` probed 1 s from each stored edge, but the contact solver is accurate to ONE ARCSECOND of longitude — ≈ 24 s for the Sun, ≈ 12 min for Saturn, unbounded at a station — so on the real ephemeris the writer's own window phase rejected its own correct contacts (marriage/P3 point contacts of the Sun, Mercury and Mars); constant stand-in ephemerides hid it.
* **The tolerance is a named function, never a constant in seconds.** New verifier-side `boundary_match`: `time_tolerance_seconds(position_at, body, t, accuracy_deg) = accuracy / |speed(t)| + 1 s`, where `accuracy` is the STORED contact's own `delta_lambda` (the solver's 1 arcsecond when none is stated) and `speed` is the body's speed at that instant (central difference, ±60 s). At a station (|speed| < 1e-3 °/day) no time tolerance exists (`None`) and the
  comparison is made in ANGLE: |Δλ| ≤ accuracy + the reconstruction's location error AND the body must have stayed within that band of the boundary longitude for the whole interval between the two instants (two instants at the same angle with the body elsewhere in between are different crossings of the same edge). Used by `contact_certify` (every reconstructed-vs-stored boundary; the two sequences must also pair up boundary for boundary),
  by `record_verifier.verify_p1_anchors`, and by `verify_member_geometry` (probe margins DERIVED per end: 2 × the tolerance, never closer than 1 s nor more than a quarter of the span; an end at a station is verified in angle — the stored boundary must lie within accuracy of an edge of the geometry — and the ordinary probes still run for an end that is not at an edge).
* **Tests on the REAL Swiss ephemeris** (`test_a53_boundary_tolerance.py`, 8): the Sun (≈ 24 s) and Saturn (≈ 12 min) — a stored edge 0.9 arcsec off in time is accepted, 3 × the tolerance is refused, and a fixed 1 s margin would have refused the correct one; the member-geometry probe accepts a correct real Sun conjunction contact that the old fixed margin rejects and still refuses one wrong by 6 hours;
  Saturn's real June–August 2025 retrograde station (found by scanning the ephemeris) has NO time tolerance, boundaries hours apart agree in angle, 20 days apart do not. Exact stand-ins pin the derivation (accuracy ÷ speed, scales with the body, a stated 2 arcsec is used as stated). Mutation: a constant 2 s tolerance fails three of them.
* **Stated in coverage as well as here.** `scope_response.named_limits()` is carried by every non-refused coverage response: the contact-geometry guarantee with its smooth-motion assumption and the boundary-tolerance statement (`contact_certify.BOUNDARY_TOLERANCE_STATEMENT`), tested.
* **1242 is real.** Stream B's `1242_gochara_builder_record_replace_finalise_grants.sql` (draft PR #2940; the four grants I proposed, guarded, with a post-check) is merged (plain merge) and replaces my stand-in fixture: the faithful mirror applies 1216 → 1220 → 1234 → 1242, the fixture file is deleted, and the restricted-builder suite passes on the real grant stack.


### Design v1.36 (2026-10-02) — R9-9 follow-up: the builder's REAL contacts on the real sky (steward M…082805)

* **The comparison tolerance, stated.** A reconstructed boundary equals a stored one within `accuracy / |speed| + 1 s` (`boundary_match.time_tolerance_seconds`), `accuracy` = the stored contact's own `delta_lambda` (1 arcsecond when none is stated), `speed` = the body's speed at that instant; at a station (|speed| < 1e-3 °/day) it is compared in angle (and the body must have stayed within that band over the whole interval between the two instants).
  Where: `boundary_match.py` (`time_tolerance_seconds`, `boundaries_agree`, `intervals_agree`); used by `contact_certify.compare_contact_sets`, `record_verifier.verify_p1_anchors` and `window_verifier._probe_contact_derived`. The old fixed-margin `verify_member_geometry` call is REPLACED in the window phase by the derived margins (per-end 2 × tolerance; angle at a station).
* **What the real sky taught (Sun and Saturn, builder solver vs reconstruction).** Running the builder's real `solve_episodes` (Swiss-refined) over a real window: the Sun's episode agrees with the reconstruction to 0.4 s (stated tolerance 2 arcsec ⇒ 49 s); Saturn's loop yields THREE episodes, two of them OVERLAPPING (a direct pass and a retrograde pass whose end sits at an arc seam inside the band), where the reconstruction has the one maximal in-orb interval.
  A one-for-one pairing would have rejected correct contacts, and so would requiring every stored boundary to lie on an edge. Certification therefore compares the UNION of the ledger's contacts with the reconstructed set (every union boundary against a derived tolerance); a seam between overlapping episodes is not a boundary of the contact SET. A real GAP in the union is still refused.
* **Tests on the real `.se1` ephemeris** (`test_a53_boundary_tolerance.py`, 10): the builder's real contacts for the Sun (fast) and Saturn (slow, with the real retrograde loop and its overlapping episodes) are certified against the real ephemeris, and the same ledger with one boundary moved by more than the tolerance is refused; the member-geometry probe accepts a correct real Sun contact the old 1 s margin rejected; Saturn's real station has no time tolerance and is compared in angle; exact stand-ins pin the derivation; a constant 2 s tolerance fails three of them.
