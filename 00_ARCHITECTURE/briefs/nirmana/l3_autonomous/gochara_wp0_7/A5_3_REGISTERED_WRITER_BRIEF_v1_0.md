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
