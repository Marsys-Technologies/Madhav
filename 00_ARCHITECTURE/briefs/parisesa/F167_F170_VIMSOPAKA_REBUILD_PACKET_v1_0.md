---
canonical_id: F167_F170_VIMSOPAKA_REBUILD_PACKET
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: F-167, F-168 (code portion), F-170
authored: 2026-08-22
authored_by: PARIŚEṢA-V4 repair lane (GA-2/GA-3 authority)
execution_status: NOT EXECUTED — awaiting properly-scoped GA-3 execution
ga3_process_template: R-7-style (mirrors F62_MOOLATRIKONA_REBUILD_PACKET_v1_0.md /
  F157_PARIVARTANA_REBUILD_PACKET_v1_0.md's two-clause shape), both clauses
  addressed in §4 below
shares_execution_with: F62_MOOLATRIKONA_REBUILD_PACKET_v1_0 (F-62),
  F157_PARIVARTANA_REBUILD_PACKET_v1_0 (F-157) — same writer, same asset,
  same chart set. See §0.
---

# F-167 (+ F-168 code) + F-170 — vimsopaka_total NULL: code repair landed, DATA REBUILD PENDING

## §0 — Do not queue a fourth separate `ga_structural` rerun

`ga_structural` already has **two** authored, not-yet-executed GA-3 rebuild
packets outstanding for the canonical chart set: `F62_MOOLATRIKONA_REBUILD_PACKET_v1_0.md`
(F-62) and `F157_PARIVARTANA_REBUILD_PACKET_v1_0.md` (F-157), which itself already
states it must share F-62's execution rather than queue a second one. **This
packet's `ga_structural` rerun must be the SAME execution as those two — do not
author or dispatch a third.** All three findings are code defects in the same
writer (`ga_structural_writer.py`), on the same asset (`ga_structural`), for the
same chart set. Whichever GA-3 execution finally runs `ga_structural` for a given
chart+ayanamsha discharges all three packets' data-correction obligation for that
build unit in one pass, **provided all three code fixes are present in the code
being run**: F-62's moolatrikona classifier fix (already landed), F-157's
`lord1 == g1` guard (already landed), and this PR's `_build_vimsopaka_ext_rows`
summation fix + `ga_vargas_writer.VIMSOPAKA_SHODA_WEIGHTS` D40/D45 correction.

This packet additionally requires **`ga_vargas` to be rebuilt first** (§3.2) —
neither F-62 nor F-157 required that, because their defects lived entirely
inside `ga_structural_writer.py` itself. This one does not: the weight-table fix
(F-168) lives in `ga_vargas_writer.py` and changes the `varga_vimsopaka_contribution`
rows in `chart_divisionals` that `ga_structural`'s new reader sums. **Sequencing
matters — see §3.2.**

## §1 — What this document is, and what it is not

This is the **rebuild specification** for F-167 + F-168's code portion + F-170.
It is deliberately **not a rebuild execution**. No production data was written
by the lane that authored it; every number below was obtained with a read-only
`SELECT` against production, 2026-08-22.

`ga_structural` and `ga_vargas` are both **L1, chart-scoped, delete-then-insert**
writers (CLAUDE.md §N.3). Re-running either DESTROYS and REPLACES the existing
rows for a chart+ayanamsha. That is protected-data execution and belongs to a
GA-3 packet run under its own scope declaration — not to a code-repair lane.

## §2 — The findings, and what this PR fixes in code

| Finding | What it is | Disposition |
|---|---|---|
| **F-168** | `ga_vargas_writer.VIMSOPAKA_SHODA_WEIGHTS`: D40/D45 both wrongly 1.0 (table summed to 21.0, not 20). Doctrine finding already CLOSED — L0's weight tables are correct and are not re-litigated here; only the code fix ships. | FIXED IN CODE by this PR |
| **F-167** | `ga_structural_writer._build_vimsopaka_ext_rows` emitted a literal `value_num=None` on every one of 105 rows (7 grahas × 15 ayanamshas) — the same defect shape as F-61's `graha_saptavargaja_bala_component`. | FIXED IN CODE by this PR (copies F-61's playbook exactly) |
| **F-170** | `_get_saptavargaja_components` and `_get_divisional_constituent_ids` (siblings in the same file) had no detector for migration 218's "one canonical build per chart" invariant breaking. | FIXED IN CODE by this PR — a distinct-build `RuntimeError` assertion added to both, plus the new `_get_shodasavarga_components` reader F-167 introduces |

**Live confirmation of F-167's blast radius, measured before this PR's fix:**

```sql
SELECT fact_value_text, count(*) FROM chart_facts
 WHERE fact_category='vimsopaka_bala_per_graha' AND fact_key='vimsopaka_total'
 GROUP BY 1;
-- fact_value_text=NULL | count=105
```

Exactly matches the plan's predicted shape: 7 `CLASSICAL_GRAHAS` × 15 ayanamsha-rows
(3 charts × 5 ayanamshas) = 105, all NULL, zero exceptions.

### §2.1 — Write path (fixed by this PR, verified not assumed)

- `ga_writers/ga_vargas_writer.py::VIMSOPAKA_SHODA_WEIGHTS` — D40/D45 corrected
  0.5/0.5 (was 1.0/1.0), matching L0 (`brahmagyan/l0_reference.py._VIMSHOPAKA
  ["shodashavarga"]`) exactly. A module-level `assert sum(...) == 20.0` now
  guards the constant at import time, plus a dedicated pytest.
- `ga_writers/ga_structural_writer.py::_build_vimsopaka_ext_rows` — rewritten to
  sum `_get_shodasavarga_components`'s per-varga `varga_vimsopaka_contribution`
  values across the 16-member shodasavarga group
  (new `SHODASAVARGA_EXPECTED_VARGAS` constant), with F-61's three-way honest
  coverage discipline (NULL on zero constituents, `partial_N_of_16` /
  `complete_16_of_16` fact_value_text, `coverage_complete` + `vargas_missing`
  in the JSONB).
- `_get_saptavargaja_components`, `_get_divisional_constituent_ids`, and the new
  `_get_shodasavarga_components` all now assert a single `build_id_uuid` across
  the rows they read, raising `RuntimeError` rather than silently summing across
  builds (F-170).

### §2.2 — Read path — the D30 gap this rebuild will HONESTLY still show

Measured (read-only) against `chart_divisionals`:

```sql
SELECT chart_id, ayanamsha_id, count(*) FROM chart_divisionals
WHERE fact_category='varga_vimsopaka_contribution'
GROUP BY chart_id, ayanamsha_id;
-- every (chart_id, ayanamsha_id) = 105 rows = 7 grahas × 15 vargas present (of 16 expected)
```

The missing varga is **D30** (confirmed absent from the per-graha varga set on the
canonical chart/lahiri sample). This is the same known D30 gap F-61's packet
disclosed for the saptavargaja group. **This rebuild will not fabricate D30
coverage** — post-rebuild, `vimsopaka_total` will honestly read
`fact_value_text = "partial_15_of_16"` with `coverage_complete=false` and
`vargas_missing=["D30"]`, not `complete_16_of_16`. Closing that gap is a separate,
already-known finding (the D30 divisional build), not part of this packet.

### §2.3 — Out of scope, disclosed rather than silently ignored

F-168's write-up also names a **separate** downstream consumer —
`ga_strength_writer.py::_derive_vimsopaka` → PyJHora's `sapthavarga` table —
whose `graha_vimsopaka_saptavarga`/`graha_vimsopaka_shodasavarga` (GA3)
`chart_facts` rows are a **different category**, written by a different function,
sourced from PyJHora's own internal weight table rather than
`ga_vargas_writer.VIMSOPAKA_SHODA_WEIGHTS`. **This PR's weight fix does not
touch it** — verified by grep, `graha_vimsopaka_shodasavarga` is written only at
`ga_strength_writer.py:862`, never referencing `VIMSOPAKA_SHODA_WEIGHTS`. PyJHora's
own `sapthavarga` transposition (D7/D9/D12/D30 rotated) remains a live, separate,
third-party-library defect, out of scope for both F-167 and F-170 and not
addressed by this packet.

## §3 — Rebuild scope

### §3.1 — Blast radius, measured (read-only, 2026-08-22, against live production)

```sql
SELECT chart_id, ayanamsha_id, count(*) FROM chart_facts
WHERE fact_category='vimsopaka_bala_per_graha' AND fact_key='vimsopaka_total'
GROUP BY chart_id, ayanamsha_id;
```

| chart_id | ayanamshas affected | rows per ayanamsha |
|---|---|---|
| `482012f1-710e-4a25-994a-93821f5871aa` (canonical native) | krishnamurti, lahiri_chitrapaksha, raman, surya_siddhanta_classical, true_chitra | 7 each (35 total) |
| `cb73cd3d-9eba-4220-9902-0de91566e980` | same 5 | 7 each (35 total) |
| `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan) | same 5 | 7 each (35 total) |

3 charts × 5 ayanamshas × 7 grahas = **105 rows, all NULL, chart-wide — every
single row of this category is affected, with zero exceptions.**

### §3.2 — Assets to rebuild, in dependency order

From `asset_registry.depends_on`, live (measured, not assumed):

```sql
SELECT asset_id, depends_on FROM asset_registry WHERE asset_id IN ('ga_structural','ga_vargas','bo_laksana');
-- ga_structural.depends_on includes 'ga_vargas' (7 total deps)
-- bo_laksana.depends_on includes 'ga_structural' and 'ga_vargas' (11 total deps)
```

```
ga_vargas  →  ga_structural  →  bo_laksana  →  (remainder of the L2→L5 chain that consumes bodha output)
```

**`ga_vargas` MUST be rebuilt first and confirmed before `ga_structural`.**
`ga_vargas` is the row-of-record writer for `varga_vimsopaka_contribution` in
`chart_divisionals` — until it re-runs with the corrected `VIMSOPAKA_SHODA_WEIGHTS`,
the D40/D45 contribution rows in `chart_divisionals` still carry the wrong (1.0)
weight, and `ga_structural`'s corrected summation would sum over stale inputs
(21.0-table-derived contributions), reproducing a wrong-but-no-longer-NULL number —
the exact "confident wrong number, worse than honest NULL" failure this packet's
own ordering discipline (§0) exists to prevent. This is a genuinely different
sequencing requirement from F-62/F-157, which never needed a `ga_vargas` rerun.

`bo_laksana` classifies `vimsopaka_bala_per_graha` as a `_MAGNITUDE_CATS` category
(`pipeline/orchestrator/writers/bo_laksana.py:228`) — it currently receives NULL
for this category (so contributes nothing today) and will begin receiving a real
magnitude once `ga_structural` is rebuilt. This is an **expected**, not incidental,
downstream effect; it must be rebuilt AFTER `ga_structural`, per the standard chain.

### §3.3 — Idempotency classification (why this is not self-serve)

| Writer | Layer | §N.3 class | Table(s) affected | Safe for a code lane to run? |
|---|---|---|---|---|
| `ga_vargas` | L1 | per-chart **delete-then-insert** | `chart_divisionals` | **NO — protected data** |
| `ga_structural` | L1 | per-chart **delete-then-insert** | `chart_facts` (+ FK-child `chart_fact_identity`, §4.1) | **NO — protected data** |
| `bo_laksana` | L2 | per-chart **delete-then-insert** | `bodha_msr_signals` | **NO — protected data** |

## §4 — Two-clause packet-template requirements (both addressed)

### §4.1 — Clause 1: rollback rehearsal against the full FK-connected table set

Measured (read-only), not assumed from documentation:

```sql
SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND (ccu.table_name = 'chart_facts' OR tc.table_name = 'chart_facts');
-- ONE result: chart_fact_identity.fact_id -> chart_facts.fact_id (chart_fact_identity_fact_id_fkey)
```

Same single FK-child as F-62/F-157 found — `chart_fact_identity`. The rollback
rehearsal replica MUST include both `chart_facts` and `chart_fact_identity`.
Re-run the equivalent FK enumeration against `chart_divisionals` (for the
`ga_vargas` half) and `bodha_msr_signals` (for the `bo_laksana` half) before
executing — do not assume this packet's `chart_facts` enumeration also covers
those tables.

### §4.2 — Clause 2: before-image scope verified against measured rows_written

Measured (read-only, 2026-08-22) `ga_structural` row counts per chart+ayanamsha —
the actual before-image scope this rebuild will delete-then-replace:

```sql
SELECT chart_id, ayanamsha_id, count(*) FROM chart_facts
WHERE source_calculation LIKE 'ga_structural.%' OR source_calculation LIKE 'pyjhora_adapter.ga6_vimsopaka_ref%' OR source_calculation LIKE 'pyjhora_adapter.structural%'
GROUP BY chart_id, ayanamsha_id;
```

| chart_id | ayanamsha_id | rows (before-image) |
|---|---|---|
| `482012f1-…` | krishnamurti / lahiri_chitrapaksha / raman / surya_siddhanta_classical / true_chitra | 11,836 / 11,833 / 11,898 / 11,823 / 11,854 |
| `cb73cd3d-…` | krishnamurti / lahiri_chitrapaksha / raman / surya_siddhanta_classical / true_chitra | 11,803 / 11,804 / 11,833 / 11,812 / 11,809 |
| `1c826d5a-…` (Abhinandan) | krishnamurti / lahiri_chitrapaksha / raman / surya_siddhanta_classical / true_chitra | 11,884 / 11,884 / 11,877 / 11,942 / 11,898 |

15 build units (3 charts × 5 ayanamshas) total. **These numbers already differ
slightly from F-62's and F-157's earlier snapshots of the same query** (e.g.
canonical/lahiri read 11,826 in F-62's packet, 11,829 in F-157's, 11,833 here) —
consistent with both packets' own warning that this table drifts with other GA-3
activity between authoring and execution. **Re-measure at execution time; do not
reuse this table's numbers if execution happens after other work has touched
these charts.**

Also measured, the `ga_vargas` before-image (the `chart_divisionals` half):

```sql
SELECT chart_id, ayanamsha_id, count(*) FROM chart_divisionals
WHERE fact_category='varga_vimsopaka_contribution'
GROUP BY chart_id, ayanamsha_id;
-- all 15 build units read 105 rows (7 grahas × 15 vargas present of 16 expected — D30 missing, §2.2)
```

## §5 — Verification the GA-3 execution should run

Post-rebuild, all of the following must hold:

1. **The reproducer inverts.** `SELECT count(*) FROM chart_facts WHERE
   fact_category='vimsopaka_bala_per_graha' AND fact_key='vimsopaka_total' AND
   fact_value_num IS NULL` returns **0** for every rebuilt chart+ayanamsha where
   `chart_divisionals` has at least one `varga_vimsopaka_contribution` row for
   that graha (was 105/105 pre-rebuild).
2. **Honest partial coverage, not a fabricated complete.** Every rebuilt row's
   `fact_value_text` reads `partial_15_of_16` (not `complete_16_of_16`) and
   `fact_value_jsonb.vargas_missing == ["D30"]`, per §2.2 — a rebuild that reports
   `complete_16_of_16` has fabricated D30 coverage that does not exist and the
   execution must be treated as failed.
3. **The golden-value shape holds.** For any graha whose 15 present
   `varga_vimsopaka_contribution` rows are known independently (e.g. via a direct
   `chart_divisionals` query), the rebuilt `vimsopaka_total` equals their sum
   exactly (`pytest.approx`-tight, not merely "non-null”) — mirrors
   `test_score_equals_hand_computed_sum`'s discipline in the unit-test suite this
   PR ships, now checked against real rebuilt data.
4. **F-168's weight fix actually took.** Spot-check at least one graha's D40 and
   D45 `varga_vimsopaka_contribution` rows in `chart_divisionals` post-rebuild;
   confirm neither implies a weight of 1.0 (i.e. `fact_value_num` for a fully
   exalted graha at D40/D45 would be 0.5, not 1.0 — back out the dignity factor
   from the writer's own contribution formula to confirm).
5. **F-170's invariant holds, not just compiles.** `SELECT chart_id, ayanamsha_id,
   count(DISTINCT build_id_uuid) FROM chart_divisionals WHERE
   fact_category IN ('varga_saptavargaja_bala_component','varga_vimsopaka_contribution')
   GROUP BY 1,2 HAVING count(DISTINCT build_id_uuid) > 1` returns **zero rows**
   both before and after this rebuild — if it does not, the F-170 assertion
   should have raised during the rebuild itself, and a raise there is a correctly
   functioning detector, not a rebuild failure to work around.
6. **F-62's and F-157's own verification checklists also hold**, since this
   execution is shared with both those packets: see `F62_MOOLATRIKONA_REBUILD_PACKET_v1_0.md`
   §4 items 1–4 and `F157_PARIVARTANA_REBUILD_PACKET_v1_0.md` §5 items 1–4 in
   full. **Do not mark this execution complete on this packet's checklist alone**
   — all three packets' checklists gate the same `ga_structural` rebuild.
7. **L2 fan-out.** After `ga_structural` is verified, rebuild `bo_laksana` and
   confirm the `vimsopaka_bala_per_graha` `_MAGNITUDE_CATS` entries it derives
   now carry a real value where they previously derived from NULL — and that no
   `bodha_msr_signals` row silently changed its `constituent_facts_array`
   resolution as a side effect (a dangling or newly-appearing fact_id reference
   here would itself be a §N.5 concern).

## §6 — Open items, disclosed rather than decided

- **D30 shodasavarga coverage** remains open (§2.2) — closing it is a separate,
  already-known finding (a D30 divisional build gap), not part of this packet.
  Do not fold it into this rebuild's scope or its acceptance criteria.
- **PyJHora's `sapthavarga` transposition** (§2.3) remains open and unaddressed —
  it lives in a different code path (`ga_strength_writer.py` / PyJHora's own
  `const.py`) than either fix in this PR and is not this packet's responsibility.
- **Sequencing risk.** If this packet's `ga_vargas` rebuild runs without this
  PR's `VIMSOPAKA_SHODA_WEIGHTS` fix live in the deployed code, `chart_divisionals`
  will be re-populated with the SAME wrong (21.0-summing) weights it already
  has today — a rebuild that appears to have "run" without actually correcting
  anything. Confirm the fix commit is on the code being rebuilt from before
  starting execution, exactly as F-157's packet required for its own guard.
