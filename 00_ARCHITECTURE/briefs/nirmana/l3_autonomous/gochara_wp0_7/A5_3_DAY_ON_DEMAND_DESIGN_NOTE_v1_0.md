---
artifact: A5_3_DAY_ON_DEMAND_DESIGN_NOTE
version: "1.0"
status: "DESIGN ONLY — no code, no migration, nothing proposed here is decided. For the steward / Stream B / the native."
date: 2026-10-02
author: Pravāha Stream A (Exec A), steward M20261002T055158-aac2
changelog:
  - "1.0 (2026-10-02): first note. What exists, what the `day_on_demand` step still owes, the design, the holds."
---

# `day_on_demand` — the P6 day tier (design note)

## 1. What exists and what is owed
**Exists (Moon half).** `services/gochara_kernel/moon_on_demand.py` answers a Moon boundary query (sign / nakṣatra ingress over an interval) ephemerally: nothing is stored except ONE `moon_on_demand` coverage partition keyed `moon:interval:<start>/<end>`
(distinct from build coverage by `partition_kind`, so a sealed generation's manifest digest never moves); the answer carries a five-part receipt (manifest id+digest, coverage key + `coverage_facts`, interval, input identity, result digest) that is RETURNED, never written to a `ka_gochara_*` table.
AM-14 accounts the Moon-resolved period portions as `excluded_moon_tier`; `scope_response.coverage_response` lists `moon_on_demand` answers beside the unchanged `stored_non_moon` scope.
**Owed (the P6 half).** P6 (spec §2.2) is the **Moon channel**: tārā (nine-fold), tithi–nakṣatra, the Moon's own vedha, chandrāṣṭama (context-bound 8th-from-Moon rules). Every P6 operator is `testimony` (D-PADMIT, S-04): P6 **annotates admitted day rows; it never creates or weights a scored window** (§2.3 inv 7), and **day rows come only from P6** (inv 6),
on demand inside admitted windows, with its own coverage record. P6 is deliberately NOT bound (`rule_registry` D1; AM-8): its frame ("per the admitting path's objects") is no value of `ka_gochara_frame_ok`, and AM-4/AM-8 defer its parent-context and containment rules "to before any P6 implementation lands".

## 2. Design
1. **A serving-time act, not a build step.** The orchestrator contract is frozen and a build writes nothing P6; so `day_on_demand` is a function in the sidecar (`services/gochara_kernel/day_on_demand.py`) called by a route, returning an ephemeral response. It is NOT a registered writer substep and adds no asset.
2. **Input: a parent and a day range.** `(chart_id, generation, parent_window_id, day_start, day_end)`. The parent must be an **admitted window of the same chart and generation** (absent parent ⇒ refuse `parent_absent`); the day range must lie **inside the parent's interval** (annotation support is restricted to the admitted parent interval, AM-4 deferred rule) — outside ⇒ refuse `outside_parent_interval`.
3. **Context resolution (the deferred "unambiguous rule").** The annotation is evaluated under the parent's CONCRETE frame, frame argument and affected person, resolved from the parent's members at annotation time (the window row carries none). If the members do not agree on one `(frame_kind, frame_arg, person)` ⇒ refuse `parent_context_ambiguous` — never pick one. A forbidden effective frame (e.g. the native Moon frame for a relative, 1155's frame rule) fails loudly exactly as if written literally.
4. **Operators.** Each of the four emits annotation objects `{day, operator, value, operator_role: "testimony", source_ref, parent_window_id, resolved_frame}`. The constructor has **no scored arm**: `operator_role='scored'`, or any score rule, is unrepresentable (AM-8's "scored P6 rejected"), and the response carries no number any score, window or severity consumes. The Moon's own vedha exists **only** inside these day annotations with a P6 coverage record, annotation-only; absent overlay coverage reads `unavailable` with a coverage object, never 1.0 (§5.2 inv 3–4).
5. **Moon positions.** Through the existing `moon_on_demand` machinery (kernel arcs + Swiss refinement, the file-level Swiss probe on every Moon calc, N-28) — no second ephemeris path.
6. **Durability = one coverage row.** Same as the Moon query: a `moon_on_demand` partition whose `relations_searched` names exactly the P6 operators evaluated and the day range, written under the chart lock; nothing else. **Receipt** = the AM-4 five parts + the parent window id, the resolved frame and the operator set, with the result digest over a canonical rendering that excludes self-referential and audit fields. Replay = re-issue and compare the digest.
7. **Sealed generations.** No membership row, no window or record mutation, no change to the manifest digest — asserted by test (row counts and `inventories_digest` identical before and after a P6 query on a SEALED generation).
8. **Registry.** P6 stays a testimony template (AM-8): no shared-validator arm, `ka_gochara_frame_ok` stays at its five kinds; binding P6 into the registry is a designed migration owned by Stream B, after the context rule above is ruled.

## 3. Tests the design owes (from AM-8's obligations)
Non-P6 inheritance rejected · scored P6 rejected · absent parent rejected · forbidden relative frame rejected · day range outside the parent rejected · ambiguous parent context refused · sealed-parent annotation writes zero rows and the manifest digest does not move · the resolved concrete frame recorded on the annotation · replay digest equality · tārā / tithi–nakṣatra / chandrāṣṭama oracles (O-P6-TARA …) · Moon vedha unavailable-not-1.0.

## 4. Holds and questions (not mine to settle)
* **Who writes the coverage row at serve time.** Today the Moon query writes through the caller's connection. In production the serving principal needs INSERT on `kala_gochara_coverage` for `moon_on_demand` rows only (and the chart-lock function) — a grant for Stream B / the roles ruling, not the builder.
* **Parent-context rule** (item 3) is my proposal for the AM-4 deferred rule; Stream B owns the spec text.
* **tārā refinement:** the cycle/thirds refinement and the OCR "[?]" at PG67:C1 are Śāstra's, recorded at that clause; the note takes no position.
* PC-2b (receipt table/API, canonical rendering, before/after-seal evidence) gates the ACTUAL on-demand use; this note is the design for it, not the evidence.
