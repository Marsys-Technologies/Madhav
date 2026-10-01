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

