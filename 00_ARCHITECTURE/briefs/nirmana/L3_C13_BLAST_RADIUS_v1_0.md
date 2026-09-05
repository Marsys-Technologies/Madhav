---
artifact: L3_C13_BLAST_RADIUS_v1_0.md
canonical_id: NIRMANA_L3_C13_BLAST_RADIUS
version: "1.0"
status: COMPLETE — 23/23 routes carry a blast-radius statement
produced_on: 2026-09-05
campaign_id: nirmana-elevation
layer: L3 — Kāla
authorized_by: >
  Charter C13 (D-NATIVE-05, native-ruled 2026-09-05) — every W2 route decision must include a
  downstream blast-radius statement. Produced by querying the catalogue, never a code comment
  (D-CND-16). Tool: platform/scripts/nirmana/cascade_check.sql plus the two layer-wide closure
  queries recorded in §5.
---

# L3 KĀLA — C13 BLAST-RADIUS STATEMENTS (23/23 routes)

**Headline: of L3's 18 target tables, exactly ONE has any outbound CASCADE closure at all.**
Twenty-two of the twenty-three routes destroy nothing beyond their own rows. The twenty-third —
`ka_sangam` / `kala_convergence` — reaches **3,708 rows across five L4 tables**, and is HELD.

That asymmetry is the useful finding. A blanket "L3 is cascade-safe" would have been wrong, and a
blanket "every rebuild is dangerous" would have held twenty-two assets for nothing.

## §1 — The one route with a cascade radius

`ka_sangam` → `kala_convergence`, transitive CASCADE closure (`cascade_check.sql`):

| depth | destroys | layer | live rows | verdict |
|---:|---|---|---:|---|
| 1 | `phala_anchors` | **L4** | 195 | **CROSS-LAYER — HOLD** |
| 2 | `phala_sankrama` | **L4** | 2,985 | **CROSS-LAYER — HOLD** |
| 2 | `phala_pramana` | **L4** | 195 | **CROSS-LAYER — HOLD** |
| 2 | `phala_suddha_sodhana` | **L4** | 195 | **CROSS-LAYER — HOLD** |
| 2 | `phala_sodhana` | **L4** | 138 | **CROSS-LAYER — HOLD** |
| 1 | `kala_darshana` | L3 | 1,500 | in-layer (mine, replaced deliberately) |
| 1 | `kala_obstruction` | L3 | 1,283 | in-layer (mine, replaced deliberately) |

**L4 total: 3,708 rows.** The depth-2 rows are reached through `phala_anchors`' own outbound
CASCADEs — one hop past where a single-parent `pg_constraint` check stops. I made exactly that
mistake first (see §6) and the tool caught it.

**Disposition: HELD under C13.** It crosses a layer boundary, so per C13 the ordering is an
adjudication and L4 must confirm regenerability *before* the snapshot is spent. Filed on #1770.

## §2 — The twenty-two routes with an empty cascade radius

Verified by a single layer-wide transitive closure over `pg_constraint` (§5, query 1) across all
18 L3 target tables. Every table below returned **zero** CASCADE descendants:

`kala_activation` · `kala_activation_predicates` · `kala_avadhi` · `kala_bhavishya` ·
`kala_darshana` · `kala_field` · `kala_gochara_windows` · `kala_gochara_windows_v2` ·
`kala_jivana_parva` · `kala_kota_chakra` · `kala_moorti_nirnaya` · `kala_obstruction` ·
`kala_sudarshana_varsha` · `kala_taranga` · `kala_tithi_pravesha` · `kala_vedha_gochara` ·
`gochara_resonance_map`

Plus the four `asset_kind='service'` assets (`ka_graha_sancara`, `ka_muhurta_seva`,
`ka_dasha_kala`, `ka_tulana`), which write no rows and therefore have no radius at all.

**This is not the same as "safe to dispatch."** Two of these tables are still HELD for reasons
that have nothing to do with cascades: `kala_gochara_windows` holds the irreplaceable v1 corpus
(snapshot rule absolute), and every L3 asset is held under D-NATIVE-05 until WP-6 is live.

## §3 — No-FK referrers: the ones that ORPHAN

C13's closing rule: *no-FK referrers get dispositions, not cascades — either a real FK with an
intended delete rule, or documented orphan-tolerance **with a detector**. Silent orphaning is worse
than loud cascade.* Excluding `__ssv_*` rollback snapshots (already dispositioned in W2 N6):

| my table | orphaned by my rebuild | layer | rows | disposition |
|---|---|---|---:|---|
| `kala_obstruction` | `phala_mitigation.obstruction_id` | **L4** | 1,277 | **hand to L4** — my `ka_vighnakara` re-run silently orphans them |
| `kala_convergence` | `bodha_convergence.convergence_id` | **L2** | 120 | **hand to L2** — note the column is `uuid` against my `bigint` key, so it may not be a live pointer at all; L2 should confirm rather than either of us assume |
| `gochara_resonance_map` | `bodha_rm_resonances.resonance_id` | **L2** | 135 | hand to L2 |
| `kala_field` | `kala_field_provenance` | L3 (mine) | **2,229,522** | **mine** — see §3.1 |
| `kala_field` | `kala_field_windows` · `kala_field_salience` | L3 (mine) | 39,000 · 39,000 | mine, §3.1 |
| `kala_field` | `kala_insights` · `kala_field_null` · `kala_timeline_spec` · `kala_field_gof` · `kala_field_skill` · `kala_field_snapshots` | L3 (mine) | 846 · 310 · 12 · 6 · 7 · 2 | mine, §3.1 |
| `kala_convergence` | `kala_convergence_staging` | L3 (mine) | 0 | mine — empty; drop-or-declare at Phase Z |
| `gochara_resonance_map` | `l25_rm_resonances` | other | 0 | empty; flag only |

### §3.1 — `kala_field`'s own family: 2.3M rows of mine orphan on a `ka_kshetra` rebuild

Eight tables in the `kala_field_*` family point at `kala_field.field_snapshot_id` with **no FK**,
`kala_field_provenance` alone at **2,229,522 rows**. A `ka_kshetra` rebuild issues a new
`field_snapshot_id` and every one of those pointers goes stale — *and still resolves in shape*,
which is the failure C13 calls harder than a cascade because nothing reads false.

**Disposition: documented orphan-tolerance WITH a detector, not an FK.** An FK here would have to
choose a delete rule, and both choices are worse than the status quo: `CASCADE` would add 2.3M rows
to a destruction surface the campaign is currently trying to shrink, and `SET NULL` would destroy
the provenance linkage while preserving the row, which is the silent failure in its purest form.
The detector is the right answer, and **it already exists**: `ka_kshetra`'s D-CND-03 contract
(migration 670) asserts *"single registered snapshot+weights pin per chart"* and
*"`kala_field_windows` inside its class span and carrying the chart's pin"* — a stale-pin orphan
makes both conjuncts fail. **W3 item:** extend it to `kala_field_provenance` explicitly, which the
current contract does not name.

### §3.2 — `kala_activation_predicates` (assignment 3): orphaning has ALREADY happened, at scale

Measured, not projected:

```
kala_activation_predicates FKs ......... NONE   (zero FK constraints on the table)
rows with signal_id set ................ 150,150
signal_id ALREADY orphaned ............. 49,730
```

**One row in three already points at a `bodha_msr_signals` row that does not exist.** This is not a
hypothetical exposure to a future `bo_laksana` rebuild — a prior one already did it, silently, and
nothing reported it until `ka_yojaka`'s D-CND-03 contract went red on exactly this in migration 670.

**Disposition: documented orphan-tolerance, detector already live, NO new FK.**
- **Not `CASCADE`:** it would convert 150,150 silently-stale rows into 150,150 destroyed rows on
  the next MSR rebuild — strictly worse, and it is the very cascade the campaign is holding for.
- **Not `SET NULL`:** `signal_id` is the predicate's link to what it is a predicate *about*; nulling
  it leaves a row that cannot say what it means. That is §N.8's shape — a record that survives its
  own meaning.
- **Orphan-tolerance is honest here** *because the detector exists and fires*: `ka_yojaka`'s
  contract is red right now, on these 49,730 rows, and stays red until they are regenerated from a
  rebuilt MSR base. **The red contract IS the disposition's enforcement**, which is precisely the
  standard C13 asks for and the reason it ships red rather than scoped.

## §4 — What this changes about my W2 routes

Nothing is re-routed. C13 adds a statement, not a re-decision, and the statement is: **21 of 23
routes were correctly assessed as in-layer; one (`ka_sangam`) was not, and is now held; one
(`ka_yojaka`) carries an orphan disposition it did not previously carry.**

The `rebuild_only` assets in particular are confirmed safe *in the cascade sense* — which is what
C13 warns must not be assumed: *"`rebuild_only` is NOT safe by default for any asset with populated
descendants."* For twenty-two L3 tables the catalogue says there are no cascade descendants. For
`kala_field` there are 2.3M non-cascade ones, and that is why §3.1 exists.

## §5 — Method (reproducible)

1. **Transitive CASCADE closure, all 18 L3 tables at once** — recursive CTE over `pg_constraint`
   filtered to `confdeltype='c'`, depth-limited to 5, joined to `pg_stat_user_tables` for live
   counts. Layer inferred from table-name prefix.
2. **No-FK referrers** — columns elsewhere in `public` whose *name* matches an L3 key column, minus
   any table that already holds an FK to that parent. Deliberately narrower than
   `cascade_check.sql`'s own no-FK section, which matches any column named `id` and returned 144
   rows for `kala_activation` — nearly all of them unrelated tables that merely have an `id`. That
   breadth is right for a pre-dispatch warning and too broad for a disposition register.
3. Per-table confirmation with `cascade_check.sql` itself for `kala_convergence` and
   `kala_activation`.

## §6 — One correction to my own work, recorded rather than quietly fixed

I first answered #1770 from `pg_constraint` on the immediate parent only, and reported **188** L4
rows at risk. Running the transitive closure as C13 instructs gave **3,708** across five tables. I
corrected it on the thread within the same loop.

The lesson is the one C13 already states and I did not follow: **one hop is not the radius.** The
tool exists because the immediate FK is the part you can see. Recorded here so the next reader of
this document does not repeat it from my summary.

*End L3 C13 blast-radius. 23/23 routes covered.*
