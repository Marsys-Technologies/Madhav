---
artifact: L5_C13_BLAST_RADIUS_v1_0.md
canonical_id: NIRMANA_L5_C13_BLAST_RADIUS
version: "1.0"
status: CURRENT — C13 blast-radius statements for all 15 L5 routes
session: L5
produced_on: 2026-09-05
charter_ref: C13 (D-NATIVE-05) · D-CND-15 · D-CND-16
method: >
  Catalogue queried directly (pg_constraint / information_schema), never a code comment —
  D-CND-16. The CASCADE closure reimplements platform/scripts/nirmana/cascade_check.sql's
  recursive query over all 27 L5 write-target tables at once; the no-FK half reimplements its
  second query. Read-only throughout. Every row count is live as of 2026-09-05.
---

# L5 — C13 blast-radius statements, all 15 routes

C13: *"The DAG models ancestors; the E-gate is necessary and NOT sufficient. Every W2 route
decision must include a downstream blast-radius statement: cascade children, no-FK referrers,
live row counts. `rebuild_only` is NOT safe by default for any asset with populated descendants."*

## §1 — The headline: L5's cascade blast radius is EMPTY, and that is measured

**Zero CASCADE children from any of the 27 tables the 15 L5 assets write.**

```sql
-- transitive CASCADE closure, all L5 write-targets, depth <= 8
WITH RECURSIVE fk AS (
  SELECT confrelid::regclass::text AS parent, conrelid::regclass::text AS child
  FROM pg_constraint WHERE contype='f' AND confdeltype='c' AND conrelid::regclass::text !~ '__ssv_'
), chain AS (...)
SELECT ... FROM chain;
-- → 0 rows
```

L5 is the terminal layer. **No L5 rebuild destroys another layer's data.** This is the structural
reason L5's routes do not inherit the hazard that made C13 necessary — the `bo_laksana` MSR
rebuild that cascade-deletes 710,899 rows across five L3 tables has no L5 analogue, in either
direction:

**Inbound, also checked.** No campaign-layer table CASCADEs *into* L5 either. The only CASCADE
reaching an L5 table originates at `profiles` (depth 2 → `life_events`, depth 3 →
`mimamsa_intervention_ledger`) — i.e. deleting a *user account*, which is outside campaign scope
and is correct behaviour for user data.

**Consequence for the routes:** the C13 clause *"if it crosses a boundary, the dispatch is HELD"*
is **not triggered by any of the 15**. L5's holds are all for other reasons (identity stability,
the evidence spine), not for destruction.

## §2 — No-FK referrers: the harder half, and where L5 actually has something

C13: *"no-FK referrers ... ORPHAN rather than cascade — the harder failure, since a stale pointer
still resolves and nothing reads false."*

### 2.1 `mimamsa_multipliers.weight_id` — 224,742 in-layer referrers, all resolving

| referrer | layer | rows w/ weight_id | unresolvable |
|---|---|---|---|
| `mimamsa_fact_adjustment` | L5 | 123,272 | **0** |
| `mimamsa_signal_adjustment` | L5 | 100,275 | **0** |
| `mimamsa_convergence_adjustment` | L5 | 1,000 | **0** |
| `mimamsa_anchor_adjustment` | L5 | 195 | **0** |

All in-layer, all resolving. **Disposition: documented orphan-tolerance WITH a detector**, which
C13 requires and which already ships — migration 691's `mi_adhilepa` contract asserts every
overlay row's `weight_id` resolves to a `mimamsa_multipliers` row on the same chart, *and* that
the overlay's stored multiplier still equals its source. That second clause is the one that
matters: it catches `mi_gunanaka` re-running and 123,272 fact-overlay rows continuing to apply a
stale figure — identical row count, stale served numbers.

`weight_id` is deterministic (`mechanism || ':' || target_ref`, asserted by the same contract), so
these references are stable across rebuilds by construction rather than by luck.

### 2.2 A name collision that is NOT a cross-layer reference — recorded so nobody "fixes" it

`kala_field_provenance` (**663,000 rows**) and `kala_field_weights` (29) also carry a `weight_id`
column. A column-name sweep flags them as cross-layer referrers to `mimamsa_multipliers`. **They
are not.**

```
kala_field_provenance : 663,000 rows with weight_id, 663,000 UNRESOLVABLE against mimamsa_multipliers
kala_field_weights    :      29 rows with weight_id,      29 UNRESOLVABLE
```

**100% unresolvable in both cases** — they are L3's own weight vocabulary, seeded by migration 491,
in a disjoint namespace that happens to share a column name. Adding an FK here would be actively
wrong. Recorded explicitly because the naive query says "663,000 L3 rows depend on an L5 table",
which is alarming and false.

### 2.3 `signal_id` — the two dispositions, which are opposite

Full detail on issue #1748. In summary:

| table | rows | uuid-shaped | resolve to `bodha_msr_signals` | disposition |
|---|---|---|---|---|
| `mimamsa_attribution` | 1,425 | 1,425 | **1,425** | **real FK**, after `text`→`uuid`, `ON DELETE RESTRICT`; sequenced behind L2's deterministic `signal_id` |
| `mimamsa_load_bearing` | 9 | 0 | **0** | **never an FK to signals** — all 9 hold `fam_*` values resolving to `mimamsa_signal_families.family_id`. A mis-named column (W1 finding C-F-19), not a broken reference. Detector already ships in 691. |

L5 is the only layer storing `signal_id` as `text`; the other nine such columns across L2/L3/L4 are
`uuid`. So "add a real FK" is a type change first, which is why it is sequenced and not done here.

## §3 — Per-route statements (all 15)

Every route's cascade radius is **empty**; the column below records what else the route touches.

| # | asset | route | cascade children | no-FK referrers to its tables | C13 verdict |
|---|---|---|---|---|---|
| 1 | `mi_vistara` | `rebuild_only` | none | none | **CLEAR** — writes 0 rows by design |
| 2 | `lel_events` | `static` | none | none (its `id` matches many unrelated PKs — checked, all false positives) | **CLEAR** — no build at all |
| 3 | `mi_jivanaghatana` | `changed` | none | none | **CLEAR** |
| 4 | `mi_kula` | `changed` | none | `mimamsa_multipliers.target_ref` (18, in-layer, detector in 691) | **CLEAR** — but note the global unqualified DELETE: dispatch `scope='global'` only |
| 5 | `mi_sankalpa` | `rebuild_only` | none | none | **CLEAR** — 0 rows; status-preserving delete-then-reinsert |
| 6 | `mi_seva` | `rebuild_only` | none | none | **CLEAR** — writes nothing |
| 7 | `mi_bhara` | `changed` | none | none | **CLEAR** — registry-only change; `kala_field_weight_versions` is L3-owned and L5 **reads** it (#1743) |
| 8 | `mi_bhavisya` | `changed` · **HELD** | none | `mimamsa_calibration.prediction_id` (57, in-layer) | **CLEAR on destruction** — held on identity (#1732 collision), not blast radius |
| 9 | `mi_pramana` | `changed` · **HELD** | none | `mimamsa_attribution.match_id` (1,425, in-layer) | **CLEAR on destruction** — same hold |
| 10 | `mi_abhilekha` | `probe` | none | none | **CLEAR** — 0 rows; probe writes nothing |
| 11 | `mi_gunanaka` | `changed` | none | **224,742 overlay rows** (in-layer, §2.1) | **CLEAR but LOUDEST** — the one route whose rebuild leaves real stale references if `mi_adhilepa` is not re-run after it. Sequence `mi_gunanaka` → `mi_adhilepa`, always. |
| 12 | `mi_pariksha` | `rebuild_only` | none | none | **CLEAR** |
| 13 | `mi_adhilepa` | `changed` | none | none | **CLEAR** — it is the referrer, not the referent |
| 14 | `mi_sambandha` | `changed` | none | none | **CLEAR** |
| 15 | `mi_darshana` | `rebuild_only` | none | `mimamsa_insight_embeddings.insight_id` (0 rows) | **CLEAR** — and its own substep DELETEs embeddings on every rebuild by construction |

## §4 — The one sequencing rule this analysis produces

**`mi_gunanaka` must be followed by `mi_adhilepa`, in that order, every time.**

Not because of cascade — there is none — but because 224,742 overlay rows carry a *copy* of each
multiplier's value, and a `mi_gunanaka` rebuild that changes a multiplier leaves those copies
stale with an unchanged row count. That is the silent-orphan shape C13 names, one level below FK
semantics: nothing dangles, everything resolves, and the served numbers are wrong.

The detector exists (691, `mi_adhilepa`'s contract, the overlay-consistency clause). This rule
makes the detector unnecessary rather than merely present.

## §5 — Honest limits

- The CASCADE closure finds tables reachable by **declared FK with CASCADE**. Anything reached by
  application code rather than by a constraint is invisible to it, exactly as `cascade_check.sql`'s
  own header warns.
- The no-FK sweep matches on **column name**, so it over-reports (every table with an `id` column
  appears to "reference" `life_events.id`). Every hit above was checked for semantic reality and
  the false positives are named as such rather than silently dropped.
- **`__ssv_*` shadow tables are excluded**, matching the shared tool. If any carries an L5
  reference it is not covered here.
- Per **D-CND-17**, chart `cb73cd3d` is DAMAGED and is not a measurement baseline; row counts are
  whole-table or from `482012f1` / `1c826d5a`.

---

## Heartbeat log (§R3)

- `2026-09-05T~01:40Z` — `L5-W3` — all 7 resume assignments discharged: #1790 rebased/queued;
  #1785 extended with the free registry window and re-armed; no-FK dispositions posted (#1748);
  writer audit verified complete on `main` (9 raises present, zero inability-notes remaining) and
  the held A5 item **decided as B under §R5** rather than left waiting; #1757 answered with the
  decision *and* the reason a migration cannot deliver it; hold on `mi_bhavisya`/`mi_pramana`
  re-grounded on the newly-found anchor-identity collision; C13 statements for all 15 routes
  published. — **Blocked on:** W2 acceptance must wait for #1785 to merge, because D-CND-09 closes
  the registry window on first acceptance and 691 carries the last of it. Not idle: that is a
  sequencing constraint I am honouring, not a stall.
