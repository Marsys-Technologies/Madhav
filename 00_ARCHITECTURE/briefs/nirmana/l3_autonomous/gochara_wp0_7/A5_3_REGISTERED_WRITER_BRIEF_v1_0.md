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
