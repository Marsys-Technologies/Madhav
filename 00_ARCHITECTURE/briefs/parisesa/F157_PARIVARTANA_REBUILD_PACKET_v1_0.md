---
canonical_id: F157_PARIVARTANA_REBUILD_PACKET
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: F-157
authored: 2026-08-22
authored_by: PARIŚEṢA-V4 repair lane (GA-2/GA-3 authority)
execution_status: NOT EXECUTED — awaiting properly-scoped GA-3 execution
ga3_process_template: R-7-amended (OWNER_RULINGS_20260821.md §R-7), both mandatory
  clauses addressed in §4 below
---

# F-157 — parivartana self-exchange: code repair landed, DATA REBUILD PENDING

## §1 — What this document is, and what it is not

This is the **rebuild specification** for F-157. It is deliberately **not a rebuild
execution**. No production data was written or deleted by the lane that authored it;
every number below was obtained with a read-only `SELECT`.

`ga_structural` is an **L1, chart-scoped, delete-then-insert** writer (CLAUDE.md
§N.3). Re-running it DESTROYS and REPLACES the existing `chart_facts` rows for a
chart+ayanamsha. That is protected-data execution and belongs to a GA-3 packet run
under its own scope declaration — not to a code-repair lane.

**This packet also discharges F-157's coupling instruction:** F-157's `ga_structural`
rerun **must be the SAME execution** as F-62's already-authored, not-yet-executed
rebuild (`F62_MOOLATRIKONA_REBUILD_PACKET_v1_0.md`) — both findings are code defects
in the same writer, on the same asset, for the same set of charts. **Do not queue two
separate `ga_structural` reruns.** Whichever GA-3 execution finally runs
`ga_structural` for a given chart+ayanamsha discharges both packets' data-correction
obligation for that build unit in one pass, provided both code fixes (F-62's
moolatrikona classifier fix, already landed per that packet's §2.1, and this PR's
`lord1 == g1` guard) are present in the code being run.

## §2 — The finding

`ga_writers/ga_structural_writer.py::_build_varga_relationship_rows`'s parivartana
(mutual-exchange) enumeration loop had no `lord1 != g1` guard. For a graha sitting in
its OWN sign, `lord1 == g1` (e.g. Jupiter in Sagittarius: `sign1="Sagittarius"`,
`lord1=SIGN_LORDS["Sagittarius"]="Jupiter"`), which makes the
`sign_lord1 in OWN_SIGNS.get(g1, [])` test trivially true against itself. The
`_seen_parivartana` dedup set does not catch this — it only suppresses the redundant
A→B / B→A double-hit of a REAL exchange; a self-pair only ever hits the loop once, so
dedup never sees a duplicate to catch.

Fixed by this PR: a guard, `if lord1 == g1: continue`, placed before the `OWN_SIGNS`
test (see `ga_writers/ga_structural_writer.py`, in `_build_varga_relationship_rows`,
immediately after `lord1` is resolved and validated non-None/classical). Verified with
a mutation check: reverting the guard makes the new regression tests in
`tests/test_f157_parivartana_self_exchange.py` fail exactly as expected.

**Write path:** ALREADY FIXED IN CODE by this PR. **Data path:** the already-computed
`chart_facts` rows remain wrong until this packet's rebuild runs.

**Not affected — do not chase this elsewhere.** `bo_cgm_motifs.py`'s
`mutual_reception` check (~lines 277–296) is not affected: it iterates
`graha_ids[i+1:]`, which structurally excludes self-pairs (`a_id != b_id` by
construction of the index-offset loop) — no guard was ever needed there, and no
rebuild of anything it reads is implied by this packet.

## §3 — Rebuild scope

### §3.1 — Blast radius, measured (read-only, 2026-08-22, against live production)

```sql
SELECT count(*) AS total_self_pair_rows,
       count(DISTINCT chart_id) AS distinct_charts,
       count(DISTINCT chart_id || ':' || ayanamsha_id) AS distinct_chart_ayanamsha
FROM chart_facts
WHERE fact_category = 'parivartana_per_varga'
  AND fact_value_text ~ '^([A-Za-z]+)_in_\w+_\1_in_\w+$';
-- total_self_pair_rows=439 | distinct_charts=3 | distinct_chart_ayanamsha=15
```

```sql
SELECT count(*) AS total_parivartana_rows FROM chart_facts
WHERE fact_category = 'parivartana_per_varga';
-- 624
```

**439 of 624 (≈70%) of all `parivartana_per_varga` rows chart-wide are self-pairs.**
This is not a rare edge case — every graha sitting in its own sign, in every varga
that carries a real `lord1==g1` relation for that sign, fabricates one. Per-chart
breakdown, including the D1-only count (the highest-visibility subset, since D1 is
what most serving surfaces read by default):

| chart_id | self-pair rows (all vargas) | self-pair rows (D1 only) |
|---|---|---|
| `482012f1-710e-4a25-994a-93821f5871aa` (canonical native) | 153 | **5** |
| `cb73cd3d-9eba-4220-9902-0de91566e980` | 169 | 5 |
| `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan) | 117 | 0 |

The canonical chart's own live reproducer is confirmed present exactly as the finding
describes:

```sql
-- chart_id='482012f1-…', ayanamsha_id='lahiri_chitrapaksha':
-- fact_subject='D1_JUP_JUP', fact_value_text='Jupiter_in_Sagittarius_Jupiter_in_Sagittarius'
```

(Jupiter sits in Sagittarius, its own sign, across `lahiri_chitrapaksha`,
`krishnamurti`, `raman`, and `surya_siddhanta_classical` for this native — each
produces its own self-pair row at D1. `true_chitra` was not returned by the D1 query
above for this subject in the sampled page; unlike F-62's ayanamsha-dependent
moolatrikona boundary, this is not expected to be ayanamsha-sensitive in the same
way — Jupiter's own-sign membership doesn't move across a fractional-degree boundary
the way its moolatrikona/own split does — so any apparent exception should be
double-checked at execution time, not assumed.)

Rows are NOT limited to D1 — they occur at every varga where the placement recurs
(D2, D3, D6, D8, D9, and higher vargas up to D2700 all appear in the sampled data),
because `_build_varga_relationship_rows` runs once per varga and the guard's absence
is varga-agnostic.

### §3.2 — Assets to rebuild, in dependency order

From `asset_registry.depends_on`, live (measured, not assumed):

```sql
SELECT asset_id, depends_on FROM asset_registry WHERE asset_id IN ('ga_structural','bo_laksana');
-- bo_laksana.depends_on includes 'ga_structural' (11 total deps)
-- ga_structural.depends_on: ga_dashas, ga_nakshatra, ga_panchanga, ga_positions, ga_sensitive, ga_strength, ga_vargas
```

```
ga_structural  →  bo_laksana  →  (remainder of the L2→L5 chain that consumes bodha output)
```

`ga_structural` is the row-of-record writer for `parivartana_per_varga` (and, per
F-62, for `graha_dignity_per_varga`). `bo_laksana` reads `parivartana_per_varga` at
lines 140/213/486 of `pipeline/orchestrator/writers/bo_laksana.py` and fans it out to
`career`/`wealth`/`relationship` domain signals in `bodha_msr_signals`
(delete-then-insert via `replace_prior_msr_for_chart`, §N.3-conformant). It must be
rebuilt AFTER `ga_structural`, never before or in parallel.

### §3.3 — Idempotency classification (why this is not self-serve)

| Writer | Layer | §N.3 class | Table(s) affected | Safe for a code lane to run? |
|---|---|---|---|---|
| `ga_structural` | L1 | per-chart **delete-then-insert** | `chart_facts` (+ its FK-child `chart_fact_identity`, see §4.1) | **NO — protected data** |
| `bo_laksana` | L2 | per-chart **delete-then-insert** | `bodha_msr_signals` | **NO — protected data** |

## §4 — R-7-amended GA-3 packet-template requirements (both addressed)

Per `OWNER_RULINGS_20260821.md` §R-7: "a packet missing either [clause] is
DATA_PARKED (incomplete) by definition." Both are addressed here.

### §4.1 — Clause 1: rollback rehearsal against the full FK-connected table set

Measured (read-only), not assumed from documentation — every foreign key touching
`chart_facts` in either direction:

```sql
SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND (ccu.table_name = 'chart_facts' OR tc.table_name = 'chart_facts');
-- ONE result: chart_fact_identity.fact_id -> chart_facts.fact_id (chart_fact_identity_fact_id_fkey)
```

`chart_facts` has exactly one FK-connected child table: **`chart_fact_identity`**.
The rollback rehearsal replica for this execution MUST include both `chart_facts` AND
`chart_fact_identity` — not `chart_facts` alone — and must exercise the delete-then-
insert path against both so a partial failure (e.g. `chart_facts` rows deleted but
`chart_fact_identity` rows orphaned, or vice versa) is caught in rehearsal rather than
in production. For the `bo_laksana` half of the rebuild, re-run the same FK
enumeration query against `bodha_msr_signals` before executing, and include whatever
it returns — do not assume this packet's `chart_facts` enumeration also covers L2.

### §4.2 — Clause 2: before-image scope verified against measured rows_written

Measured (read-only) `ga_structural` row counts per chart+ayanamsha, the actual
before-image scope this rebuild will delete-then-replace — NOT assumed from any
writer docstring or asset spec:

```sql
SELECT chart_id, ayanamsha_id, count(*) FROM chart_facts
WHERE source_calculation LIKE 'ga_structural.%' GROUP BY chart_id, ayanamsha_id;
```

| chart_id | ayanamsha_id | ga_structural rows (before-image) |
|---|---|---|
| `482012f1-…` | `krishnamurti` | 11,829 |
| `482012f1-…` | `lahiri_chitrapaksha` | 11,826 |
| `482012f1-…` | `raman` | 11,891 |
| `482012f1-…` | `surya_siddhanta_classical` | 11,816 |
| `482012f1-…` | `true_chitra` | 11,847 |
| `cb73cd3d-…` | krishnamurti / lahiri_chitrapaksha / raman / surya_siddhanta_classical / true_chitra | 11,796 / 11,797 / 11,826 / 11,805 / 11,802 |
| `1c826d5a-…` (Abhinandan) | krishnamurti / lahiri_chitrapaksha / raman / surya_siddhanta_classical / true_chitra | 11,877 / 11,877 / 11,870 / 11,935 / 11,891 |

15 build units (3 charts × 5 ayanamshas) total, each ≈11,800–11,935 rows. The
before-image snapshot taken immediately before execution MUST match these counts
(within the small natural drift expected if any of these charts has been rebuilt
between this packet's authoring and its execution — re-measure at execution time,
do not reuse this table's numbers if execution happens after other GA-3 work has
touched these charts) — any large discrepancy means the packet's scope assumption is
stale and execution must halt and re-scope, not proceed on the old numbers.

## §5 — Verification the GA-3 execution should run

Post-rebuild, all of the following must hold:

1. **The reproducer inverts.** `SELECT count(*) FROM chart_facts WHERE
   fact_category='parivartana_per_varga' AND fact_value_text ~
   '^([A-Za-z]+)_in_\w+_\1_in_\w+$'` returns **0** for every rebuilt chart+ayanamsha
   (was 153 / 169 / 117 respectively per §3.1's per-chart table, pre-rebuild).
2. **Genuine exchanges are preserved, not collaterally deleted.** Spot-check at least
   one known real parivartana on the canonical chart survives with an unchanged
   `pair_key` (sample one from the pre-rebuild `parivartana_per_varga` set whose
   `fact_value_jsonb.planet_a != planet_b`, confirm it is still present post-rebuild
   with the same value).
3. **Row-count delta is exactly the self-pair count, not more and not less.**
   `(pre-rebuild parivartana_per_varga count) - (post-rebuild parivartana_per_varga
   count) == (pre-rebuild self-pair count measured in §3.1)`. A larger delta means
   real exchanges were also lost; a smaller delta means the guard did not fully take
   effect in the rebuilt data.
4. **F-62's own verification checklist also holds**, since this execution is shared
   with F-62's packet: see `F62_MOOLATRIKONA_REBUILD_PACKET_v1_0.md` §4 items 1–4 in
   full (moolatrikona reproducer inverts; D1_JUP correctly `moolatrikona` under
   lahiri/krishnamurti/true_chitra and correctly still `own` under raman/
   surya_siddhanta_classical; no dignity-tier bleed; the corrected D2+ scope guard
   query returns zero). **Do not mark this execution complete on F-157's checklist
   alone if it also touched `ga_structural`** — both packets' checklists gate the
   same rebuild.
5. **L2 fan-out.** After `ga_structural` rebuild is verified, rebuild `bo_laksana` and
   confirm `bodha_msr_signals` rows for `career`/`wealth`/`relationship` domains that
   were derived from a now-deleted self-pair `parivartana_per_varga` row no longer
   cite it in their `constituent_facts_array` (a dangling fact_id reference here would
   itself be a §N.5 violation — L2 must not go on referencing a fact_id that no
   longer resolves).

## §6 — Open items, disclosed rather than decided

- **`true_chitra` ambiguity (§3.1).** The 200-row sample used to enumerate individual
  self-pair rows did not surface a `true_chitra` / `D1_JUP_JUP` row for the canonical
  chart, while the other four real ayanamshas did. This packet does not resolve
  whether that is a genuine absence (e.g. a slightly different computed longitude
  puts Jupiter outside Sagittarius under that ayanamsha) or a sampling artifact of
  the read query. **Re-run the full (non-`LIMIT`) enumeration at execution time** and
  do not assume either answer.
- **Coupling risk.** If F-62's packet executes first (or has already executed) without
  this PR's `lord1 == g1` guard also being live in the deployed code at execution
  time, its rebuild will re-create the same self-pair rows this packet exists to
  remove — the two fixes must both be present in the code the GA-3 execution runs
  against. Conversely, if this packet's rebuild runs without F-62's moolatrikona fix
  landed (it already is, per that packet's §2.1 — verified, not re-verified here),
  the moolatrikona defect would separately persist. Confirm both fixes are on the
  commit being rebuilt from before starting execution.
