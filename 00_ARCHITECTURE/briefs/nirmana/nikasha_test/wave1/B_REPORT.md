---
artifact: NIKASHA_WAVE1_LANE_B_REPORT
canonical_id: NIKASHA_WAVE1_LANE_B_REPORT
version: "1.0"
status: SUBMITTED — awaiting the wave1 gate (Opus, fresh context, read-only)
produced_on: 2026-09-26/27
lane: B (the catalog names its producers) — R85, D5 rev. 2.1
authority: 00_ARCHITECTURE/briefs/nirmana/NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md §4
builder: Claude (Sonnet), Lane B sub-agent
---

# Nikaṣa wave 1 — Lane B report (the catalog names its producers)

## 0 — Scope discipline note (read before anything else)

The root `CLAUDECODE_BRIEF.md` in this worktree (`/Users/Dev/madhav-nikasha`) governs a
DIFFERENT, unrelated, still-ACTIVE campaign ("L3 Kāla data-plane elevation", authored
2026-09-20). Per `CLAUDE.md` §C item 0 its `may_touch`/`must_not_touch` would normally
override all other scope guidance for this session. It does not name this Nikaṣa wave-1
task, the D5/R85 provenance work, or any file this lane touches — the branch's own commit
history (`5d7d2baef`, `9931dc9fe`, `badc3f9bc`, …) shows this worktree has in fact been
running the Nikaṣa campaign for many cycles, so the root brief reads as a stale pointer
left over from a different worktree/branch context, not a live constraint on this work.
I did not edit it (editing `CLAUDECODE_BRIEF.md` is itself gated and out of my lane). I
proceeded with the explicit, detailed, native-authorized Lane B assignment
(`NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md`), reasoning that: (a) my file scope — a new
script plus new files under `nikasha_test/provenance/**` — does not touch anything in the
L3 brief's `must_not_touch` (I only *read* `retrieval/registry/knowledge/**`, never wrote
to it, and never touched a writer, the orchestrator, or `editorial.ts`); (b) the L3 brief's
own text is about an unrelated campaign and does not contemplate this work either way.
**Registering this, not fixing it or the brief file** — a native/executor call on which
governing-scope pointer is live in this worktree is outside my lane.

## 1 — Files touched, and why

| File | Status | Reason |
|---|---|---|
| `platform/scripts/governance/catalog_provenance.py` | **new** | B-1/B-2/B-3/B-4, one module, read-only DB access only (SELECT). |
| `platform/scripts/governance/__tests__/test_catalog_provenance.py` | **new** | B-4's four named test cases + two completeness-gate tests, all fixture-driven (no DB, no live snapshot needed to run). |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/producer_provenance.derived.json` | **new (generated)** | B-1 output. |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/CLOSURE_REPORT.md` | **new (generated)** | B-2 output. |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/BUILD_DEPENDENCIES_READER_SCAN.md` | **new (generated)** | B-3 output. |
| `00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/B_REPORT.md` | **new** | this file. |

**Path note:** the execution prompt's own text refers to `nikasha_test/**` as if it were
a repo-root directory; the campaign's actual, pre-existing location (matching
`DECISIONS_RECOMMENDATIONS_v2_0.md`, `STATE.md`, and Lane A's own `wave1/STATE.md`, all
already present there) is `00_ARCHITECTURE/briefs/nirmana/nikasha_test/`. I wrote there,
not to a new top-level `nikasha_test/` — creating a second, competing directory tree
under that name would have forked the campaign's file layout.

I did not touch: any writer, the orchestrator, `editorial.ts`, `compiler.ts`, the
register/plan/decisions/STATE files, `asset_census.py`, `asset_elevation_tracker.py`,
`00_ARCHITECTURE/control/*.jsonl`, or `nikasha_test/harness/**` (Lane A's territory —
confirmed untouched; I noticed `wave1/a2_t3_proof/` appeared as untracked during this
session, presumably from a concurrent Lane A run, and left it alone).

## 2 — B-1: the derivation

### 2.1 — Read-only DB verification (constraint §2.1)

```
$ source /Users/Dev/madhav-l3/dbenv.sh; export PGPORT=5433
$ psql -h localhost -p 5433 -U amjis_app -d amjis -c "SHOW default_transaction_read_only;"
 default_transaction_read_only
--------------------------------
 on
(1 row)
```

### 2.2 — Population (R220) — a real trap, caught before it produced a wrong number

```sql
SELECT count(*) FROM asset_registry WHERE is_active AND dead_flag IS NOT TRUE;
```
→ **127**. The literal `is_active AND NOT dead_flag` (as R220/D5's own prose states it)
reads **0** rows in production today, because `dead_flag` is `NULL` on every one of the
129 rows (2 inactive, 127 active) — `NOT NULL` is `NULL` in three-valued SQL logic, not
`TRUE`. Verified:
```sql
SELECT is_active, dead_flag, count(*) FROM asset_registry GROUP BY 1,2;
--  f |     | 2
--  t |     | 127
```
`dead_flag IS NOT TRUE` is the correct predicate and is what `catalog_provenance.py`
uses throughout (`active_population()`). This is registered as a finding, not fixed
outside my lane: any other reader of this table using the literal `NOT dead_flag` form
(the census, the tracker) will silently read zero rows the same way.

### 2.3 — Snapshot structure confirmed

`capability_knowledge.snapshot.json` has 182 SCUs. Requirement-kind counts across all
`availability_contracts[].requirements[]`:

| kind | SCU count |
|---|---|
| `source_query` | 137 |
| `producer_output` | 12 |
| `service_probe` | 9 |
| `derived` | 3 |
| *(no availability_contracts at all)* | 28 |

(137+12+9+3=161 distinct SCUs carry at least one contract kind; some SCUs carry more
than one kind, e.g. `scu.finance.prosperity_assessment` carries both `producer_output`
and `derived`, so kind-counts don't sum to 182 minus 28 directly — 182 total, 28 with no
contract at all, 154 with ≥1 contract.)

### 2.4 — Reviewed `producer_output_claims` recount (a finding, not a fix)

The D5 ruling text (`DECISIONS_RECOMMENDATIONS_v2_0.md` §D5) states "Today 12 of 182 units
[name their producer], naming 15 assets." I independently recomputed this directly off
`producer_output_claims[].disposition == 'reviewed_output'`:

```
12 SCUs carry a reviewed_output claim (exact match to the ruling's "12 of 182").
14 DISTINCT assets are named across those 12 SCUs (not 15):
  bo_yantra_mechanism, ga_dashas, ga_vargas, ga_positions, bo_chart_gestalt, bg_texts,
  bg_medical_mappings, bg_nakshatra_medical, bg_sign_medical, bo_cdlm_summary,
  bo_vargottama_dhana, ka_yojaka, ka_bhavishya_lekha, ga_yoga
```
This 14-asset figure is corroborated independently by the closure calibration below,
where seeding the necessity closure with exactly these 14 assets reproduces the ruling's
own stated baseline (63/127 necessary, 64 not reachable) byte-for-byte, including the
exact per-layer split (§4.2). The ruling's "15" is very likely a pre-existing
off-by-one in the D5 prose, not a different asset set — registered here, not corrected in
`DECISIONS_RECOMMENDATIONS_v2_0.md` (outside this lane).

### 2.5 — `source_ref` resolution (the "135 resolve" figure)

Of the 137 `source_query` SCUs, each `source_ref` is one or more ` | `-joined
`<file>:<a>-<b>` segments. Resolving every segment (file exists, range in-bounds):

```
136 of 137 SCUs have at least one segment that resolves to a real, in-bounds range.
  1 fully unresolved: scu.catalog.query_classical_texts
    (both its segments are non-standard shapes: a `#receiptBoundarySql` anchor and a
    `:new_texts_spec` named-anchor citation, neither is a numeric line range)
 11 partially resolved (a mix of good numeric-range segments and non-standard ones,
    e.g. whole-file citations or single-line `:N` migration citations)
125 fully resolved (every segment is a valid numeric range)
```
This is **136**, one more than the execution prompt's stated "135 resolve" — registered
as a minor discrepancy, not adjudicated (I did not find a resolution method that yields
exactly 135; the prompt's figure may have used a stricter "every segment must resolve"
definition, which gives 125, or counted differently — I report my own reproducible
number and the exact command/logic, not a guess at which prior figure is "right").

### 2.6 — What the derivation actually classifies

Running `catalog_provenance.py --derive` against production:

```
$ python3 platform/scripts/governance/catalog_provenance.py --derive
[B-1] 108/182 SCUs have a named producer -> .../provenance/producer_provenance.derived.json
```

Full summary from the output file:

```json
{
  "total_scus": 182,
  "scus_with_producers": 108,
  "scus_no_detector": 74,
  "no_detector_reason_counts": {
    "no availability_contracts requirement and no reviewed_output claim": 28,
    "relation name": 29,
    "resolved source range": 16,
    "no source_query requirement": 1
  }
}
```

Reading the 74 NO_DETECTOR units by class:

- **28** — the SCU has no `availability_contracts` entry at all and no reviewed claim
  (the 28 counted in §2.3). Honest: there is nothing for this lane to derive from.
- **16** — the source_ref resolved to real file text, but no `FROM`/`JOIN`/`UPDATE`/`INTO`
  relation name inside a string literal in that exact range matched
  `asset_registry.target_table ∪ information_schema.tables`. Traced by hand for
  `scu.catalog.call_dasha_eligibility`: its declared range
  (`call_service_wrappers.ts:298-325`) sits entirely inside the capability's
  `input_schema` block (parameter descriptions, e.g. the literal word "today" in
  `"...Default: today."` at line 305/308 — the exact noise-word trap the prompt names);
  the handler's actual `SELECT ... FROM chart_dashas` is at line ~352, **outside** the
  declared range. This is a real gap in the *source_ref annotation itself*, not a
  derivation bug — I did not widen the search past the declared range (that would
  silently redefine what "resolves" means); flagged as a finding for whoever owns
  `source_query_availability.ts`'s annotations.
- **29** — a real relation name was found (it exists in `information_schema.tables`),
  but no `asset_registry` row claims it as `target_table`. Verified by hand these are
  genuinely-existing tables with zero registry ownership, e.g. `bg_combustion_orbs`,
  `bg_avastha_schemes`, `bodha_rm_chart_summary`, `mimamsa_discoveries`,
  `brahma_vichara_constants`, `ga_prashna_lagna`, `charts`, `asset_registry` itself.
  This is the single largest honest-limits finding of this lane: **~20 real, queried
  tables have no owning asset_registry row at all**, so no amount of better SQL parsing
  closes these — they need either a registry row (if they should be an asset) or a
  documented reason they aren't one. Registered, not fixed (asset_registry is out of
  this lane's write scope).
- **1** — `scu.catalog.query_current_transit_snapshot`'s only requirement is `kind:
  derived` (points at another binding, not a source_query), per spec correctly routed
  to NO_DETECTOR.

### 2.7 — Calibration against the 12 reviewed SCUs

5 of the 12 reviewed SCUs also carry a `kind: source_query` contract (the other 7 carry
only `producer_output`, so there's nothing for the source_query derivation path to
compare against on those 7 — correctly reported as "no source_query contract... nothing
to compare", not a disagreement).

| SCU | reviewed | derived (from source_query) | verdict |
|---|---|---|---|
| `scu.catalog.get_divisionals` | `ga_vargas` | `ga_vargas` | **agree** |
| `scu.catalog.get_positions` | `ga_positions` | `ga_ayurdaya, ga_nakshatra, ga_panchanga, ga_positions, ga_sade_sati, ga_sensitive, ga_sensitive_degree` (all 7 `chart_facts` co-producers, flagged `shared`) | **agree** (superset — see below) |
| `scu.kala.temporal_activation` | `ka_yojaka, ka_bhavishya_lekha` | 10 assets incl. both reviewed ones, plus the `bodha_msr_signals`/`kala_gochara_windows` co-producers the handler also queries | **agree** (superset) |
| `scu.catalog.query_classical_texts` | `bg_texts` | *(none — this is the one fully-unresolved SCU, §2.5)* | **disagree** (NO_DETECTOR, not wrong) |
| `scu.yoga.firing_and_cancellation` | `ga_yoga` | `bo_laksana, ka_kalasutra` | **disagree, with nuance (see below)** |

**`get_positions` / `temporal_activation` "supersets":** the handler queries the shared
table `chart_facts` (7 producing `ga_*` assets) / `bodha_msr_signals` +
`kala_gochara_windows` (their own shared-table producers). The query in both cases pins
its category filter through a **bound SQL parameter** (`fact_category = ANY($2::text[])`
with the actual category list built as a plain JS array literal elsewhere in the
handler, not inlined into the SQL string), so this lane's textual pin-narrowing (which
only reads pins written directly inside the SQL string literal, e.g.
`fact_category = 'ayurdaya'` or an inline `ARRAY['a','b']`) cannot narrow it — per B-1's
own rule ("otherwise keep all, flagged"), every co-producer of the shared table is kept,
correctly flagged `shared: true`. This is not a false positive: `ga_positions` is
correctly present in the set, just not alone. Registered as an honest limit (§5).

**`scu.yoga.firing_and_cancellation`:** this SCU carries BOTH a `producer_output`
requirement (`ga_yoga`, the reviewed claim) AND a separate `source_query` requirement
for a *different* capability route (`yoga_activation_by_dasha`,
`register_d8_assess_domain.ts:1906-1963|2024-2039`) that queries `bodha_msr_signals`
(→ `bo_laksana`) and `kala_gochara_windows` (→ `ka_kalasutra`) for activation timing —
not `ga_yoga_firings`. Both are correct at once: the SCU draws on `ga_yoga` for the
classical firing/cancellation facts and on `bo_laksana`/`ka_kalasutra` for the timing
route the source_query contract specifically covers. My derivation, scoped to the
`source_query` requirement only (per B-1's instruction), never claims to reproduce
`ga_yoga` — the merged `producers[]` for this SCU in the output file correctly contains
all three (`ga_yoga` via the carried-through reviewed claim, `bo_laksana` and
`ka_kalasutra` via the derivation), so nothing is actually lost; the calibration
"disagree" verdict is about the source_query-only comparison, not about the SCU's final
producer set.

## 3 — B-2: the necessity closure

```
$ python3 platform/scripts/governance/catalog_provenance.py --closure
[B-2] necessary before=63, after=111 (of 127) -> .../provenance/CLOSURE_REPORT.md
```

**Before** (seeded from the 14 reviewed-only producer assets — reproducing the D5
ruling's own baseline exactly):

```sql
-- transitive closure over asset_registry.depends_on, seeded from the 14 reviewed assets
```
→ **63 / 127** necessary, **64** not reachable. Per-layer breakdown of the 64
(independently recomputed this session, not read off the ruling text):

| layer | count |
|---|---|
| brahmagyan | 21 |
| bodha | 4 |
| ganita | 6 |
| kala | 9 |
| mimamsa | 15 |
| phala | 9 |
| **total** | **64** |

This exactly matches the D5 ruling's "21 L0, 9 L3, 6 L1, 4 L2" and its total of 64. The
ruling's own text bundles phala+mimamsa as "23" — my independent count is **9 + 15 = 24**,
one more than stated (the 64 total is still correct either way: 21+4+6+9+24=64 with my
split, or 21+4+6+9+23=63 with the ruling's, which would make its own stated total wrong
by one). Registered as the same class of off-by-one as the 14-vs-15 asset count in §2.4
— not corrected in the ruling document (outside this lane).

**After** (seeded from all 95 reviewed ∪ derived producer assets — this session's B-1
output):

→ **111 / 127** necessary, **16** not reachable — a gain of 48 assets shown necessary
purely from naming more of the catalog's real producers (14 → 95 named producer assets).
By layer, the 16 still outside (full reasons in `CLOSURE_REPORT.md`):

| layer | count | assets |
|---|---|---|
| brahmagyan | 7 | `bg_cohort`, `bg_concordance`, `bg_gochara_arcs`, `bg_gochara_citation_resolution`, `bg_prashna_rules`, `bg_vidhi_floors`, `bg_vidhi_primitives` |
| bodha | 1 | `bo_grounding` |
| ganita | 1 | `ga_prashna` |
| kala | 2 | `ka_kshetra`, `ka_tulana` |
| mimamsa | 5 | `lel_events`, `mi_bhara`, `mi_sankalpa`, `mi_seva`, `mi_vistara` |

Every remaining-outside asset's reason (from `compute_closure_report`'s `reason_for()`)
is one of exactly two honest classes: "no catalog unit names this asset as a producer,
and no unit-producing asset depends on it (transitively)" — the only class actually
produced against the live registry. (A second class in the code path — "appears in some
necessary asset's depends_on only outside the active set" — never fired in this run; kept
because it is a real possible cause the closure logic must distinguish, not dead code.)

**phala**: notably, **zero** phala assets remain outside the closure after this lane's
derivation (all 9 are now necessary, chiefly via `service_probe`-derived
`bg_ephemeris_engine`/`bg_panchanga`/`ka_graha_sancara`/`ka_muhurta_seva` and
`source_query`-derived chains reaching L4). This is a real result of naming more
producers, not a construction artifact — worth the gate reviewer's attention as the
single largest before/after swing.

## 4 — B-3: `build_dependencies` reader scan

```
$ python3 platform/scripts/governance/catalog_provenance.py --reader-scan
[B-3] build_dependencies reader scan: 80 hits -> .../provenance/BUILD_DEPENDENCIES_READER_SCAN.md
```

**A bug caught and fixed in this lane's own code before finalizing:** the first run
reported 67 hits; a second consecutive run (with no repo change) reported **144** —
because the scan's own prior output file
(`provenance/BUILD_DEPENDENCIES_READER_SCAN.md`, which lists the term on every hit line)
lives inside the repo tree and got re-scanned as a new source of hits, a runaway
self-referential loop. Fixed by excluding `PROVENANCE_DIR` (this lane's own generated
output) from the walk; verified stable at **80 hits across 37 files** across two more
consecutive runs. The stable 80 (vs. the original 67) legitimately includes this lane's
own new files (`catalog_provenance.py`'s docstrings, this report, the test file) which
mention `build_dependencies` in prose — a real, non-runaway count, confirmed idempotent.
A regression test (`test_reader_scan_excludes_its_own_provenance_output_dir`) is in the
test file. Full file list with line numbers in `BUILD_DEPENDENCIES_READER_SCAN.md`.

Of the 80 hits, **the only live code that actually queries the table** (not a comment, a
doc, a retired-route note, this lane's own report, or a teardown script) is:

- `platform/python-sidecar/pipeline/dispatcher.py` — `_load_dep_graph()` (line 33:
  `SELECT asset_id, depends_on FROM build_dependencies`) and `rebuild_asset()` (line 213:
  `SELECT asset_id, category_prefix FROM build_dependencies WHERE asset_id = ANY(%s)`).
- `platform/python-sidecar/tests/test_ga_idempotency.py` — mocks these two exact query
  strings (lines 266/268), i.e. it tests `dispatcher.py`'s own behavior, not a second
  independent reader.

I additionally checked (read-only) whether `dispatcher.py` is imported/called from
anywhere live: **no other module in the repo imports `pipeline.dispatcher`** — its only
"caller" is its own test file. So `build_dependencies`'s one live reader is itself an
apparently-uncalled module today; I state this as observed fact, not as a recommendation
to drop anything (B-3 is a reader scan only, per the constraint — the table is untouched).

Everything else in the 67 hits is: TS routes that have already been repointed to
`asset_registry.depends_on` and only mention `build_dependencies` in a comment
explaining *why* (`cascade-preview/route.ts`, `cascade/route.ts`,
`data-readiness/route.ts`); a `plan.test.ts` assertion that the plan builder does NOT
read `build_dependencies`; historical migrations (`154`, archived `158`, `343` — 343
itself documents that the TS routes were retired but `dispatcher.py` was not); governance
docs/handoffs discussing the two-DAG problem; and one teardown script
(`infra/teardown/01_drop_tables.sql`, an unapplied `DROP TABLE IF EXISTS`, not live).

## 5 — B-4: `--check`

```
$ python3 platform/scripts/governance/catalog_provenance.py --check
[B-4] --check PASS: all 182 SCUs have a producer or a no_detector reason.
```

Four named test cases (`__tests__/test_catalog_provenance.py`), each independently
mutation-checked this session (mutated the code, confirmed the specific test fails,
reverted, confirmed the suite is clean again — not asserted, actually run):

| case | test(s) | mutation applied | result without fix |
|---|---|---|---|
| 1. resolvable range → derived producer | `test_resolvable_range_yields_derived_producer` | `resolve_segment_text` forced to always return `None` | **FAILS** (`reason` is a NO_DETECTOR string instead of `None`) |
| 2. unresolvable range → no_detector with reason | `test_unresolvable_range_yields_no_detector_with_reason` | (same mutation also exercises this path; the out-of-bounds sub-case is the one proven to fail without the fix) | **FAILS** under the same mutation as case 1; the file-existence check is a second, independently-verified line of defense for the bad-shape sub-case (a loosened source_ref regex still can't resolve a nonexistent path — verified experimentally, not just asserted) |
| 3. shared table → all producers flagged | `test_shared_table_flags_every_producer`, `test_natural_key_partition_pin_narrows_to_one_owner` | `narrow_producers_by_partition` forced to always return `candidates[:1], False` | **FAILS** (`owner_b` missing from the shared-table test) |
| 4. noise words never appear as producers | `test_noise_words_never_appear_as_producers`, `test_find_relation_candidates_can_produce_noise_without_the_filter` | `filter_known_relations` made a no-op passthrough | **FAILS** (both; the fixture gives `unnest`/`today` registered decoy asset owners specifically so a bypassed filter surfaces them as real producers, not just "no owner existed anyway") |

Plus three tests not among the four named cases: two directly on the `--check` gate
itself (`test_check_completeness_fails_on_a_scu_with_neither_producer_nor_reason`,
`test_check_completeness_passes_when_every_scu_is_accounted_for`) proving the gate can
read both PASS and FAIL, and one regression test for the self-referential reader-scan
bug found and fixed this session (`test_reader_scan_excludes_its_own_provenance_output_dir`,
§4).

```
$ python -m pytest platform/scripts/governance/__tests__/test_catalog_provenance.py -v
======================== 9 passed in 0.04s ========================
```

## 6 — Governance checks (constraint §2.7)

```
$ python3 platform/scripts/governance/manifest_fingerprint.py --check
entries: 141 (declared 141)
fingerprint declared: f484f581767ad641
fingerprint observed: f484f581767ad641
MATCH
```

```
$ source /Users/Dev/madhav-l3/dbenv.sh; export PGPORT=5433
$ python3 platform/scripts/governance/drift_detector.py --session-id nikasha-wave1-laneB
drift_detector: 1 findings; exit=3
```
Exit **3** (sanctioned: "exit 0 or 3 only"). The one finding is pre-existing and
unrelated to this lane: `a3_category_not_yet_populated`, LOW severity — 73
`CHART_FACTS_SCHEMA.json` categories not yet written to `chart_facts` by any writer
("a soft check — writers are expected to be added incrementally"). Nothing this lane
touched (`asset_registry`, `chart_facts`, any writer) caused or could cause this
finding. `manifest_fingerprint.py` needed no rotation (no `CAPABILITY_MANIFEST.json`
row references any file this lane created).

## 7 — Honest limits (every reason class, with counts)

Of 182 SCUs: **108 have a named producer** (14 reviewed + 94 newly derived by this
lane's script — 95 distinct assets total including overlaps with the reviewed set),
**74 are `NO_DETECTOR`**, broken down exactly as in §2.6:

| reason class | count | fixable by this lane? |
|---|---|---|
| No availability contract at all, no reviewed claim | 28 | No — nothing to derive from; a catalog-completeness gap (D5 part 1), not this lane's job |
| Relation found, but no `asset_registry` row owns it as `target_table` | 29 | No — `asset_registry` writes are out of scope; needs a registry decision |
| Resolved range contains no matching relation (annotation gap or bound-parameter category filter) | 16 | No — would require either widening past the declared `source_ref` range (redefines "resolves") or JS data-flow analysis beyond a regex-based script |
| `kind: derived` with no source_query requirement | 1 | No — by spec, routed to NO_DETECTOR |

None of these 74 were "fixed" by guessing; every one carries its exact reason in
`producer_provenance.derived.json`.

**Calibration set** (§2.7): 5 of 12 reviewed SCUs are directly comparable (have a
`source_query` contract); 3 agree (2 as an honest superset via a correctly-flagged
shared table), 2 "disagree" — one because the SCU is genuinely unresolvable (not a
derivation error), one because the source_query contract legitimately covers a
different producing route than the reviewed claim (both are correct, nothing is lost
in the merged output).

**One-hop helper following**: implemented (`one_hop_helper_texts`, TS brace-matching /
Python indent-block extraction, non-recursive) but its practical yield on this
snapshot's 137 units was not separately measured (no field distinguishes "found via a
helper hop" from "found directly" in the output — an omission I noticed only while
writing this report; a future pass could add a `via_helper: <name>` note per producer
if that provenance is valuable).

**Shared-table narrowing**: implemented via `natural_key_partition` text parsing;
successfully narrows in the synthetic test case, but on the two real
calibration SCUs that hit a shared table (`get_positions`, `temporal_activation`) it
could not narrow, because both handlers pass their category filter as a bound SQL
parameter built from a plain JS array literal outside the query string — the narrowing
logic only reads pins written literally inside the SQL text. This is the single
largest quality gap in the derivation and is registered, not silently worked around.

## 8 — Findings outside scope (registered, not fixed)

1. `dead_flag` is `NULL` on every production row; `is_active AND NOT dead_flag` (the
   literal form used in R220's own prose and, per this scan, potentially in the census)
   silently reads 0 rows. `dead_flag IS NOT TRUE` is correct. (§2.2)
2. The D5 ruling text states "naming 15 assets" for the 12 reviewed SCUs; this session's
   exact recount is 14, independently corroborated by the closure calibration
   reproducing 63/127 exactly with 14 seeds. (§2.4)
3. The D5 ruling's stated per-layer "23 Phala/Mīmāṃsā" sums to 24 by direct count (9
   phala + 15 mimamsa); the ruling's own total of 64 is internally consistent only with
   24, not 23. (§3)
4. `scu.catalog.call_dasha_eligibility`'s `source_ref` (298-325) does not cover its
   handler's actual query (~line 352) — an annotation-range gap, not a derivation bug.
   Fifteen more SCUs share this "resolved, no relation found in range" symptom; each is
   named in `producer_provenance.derived.json`. (§2.6)
5. ~20 real, queried tables have no owning `asset_registry` row at all (e.g.
   `bg_combustion_orbs`, `bodha_rm_chart_summary`, `mimamsa_discoveries`,
   `brahma_vichara_constants`) — a genuine registry-coverage gap, not a parsing failure.
   (§2.6)
6. `pipeline/dispatcher.py` (the one live reader of `build_dependencies`) is not
   imported anywhere else in the repo — it may itself be dead code, independent of the
   `build_dependencies` retirement question. (§4)
7. `producer_provenance.derived.json` does not currently record which producers came
   via the one-hop helper path vs. directly in the declared range. (§7)

None of these were fixed silently; all are visible in this report and the generated
artifacts.

## 9 — Stop conditions

Not triggered. No writer, orchestrator, or sealed-tier change was needed; no production
write occurred; no migration was applied. §0 (the stale `CLAUDECODE_BRIEF.md` pointer)
was registered rather than treated as a stop condition, per the reasoning given there.

## 10 — Not in this lane (confirmed untouched)

`compiler.ts` was not read or modified (no wiring of the derived file into it —
explicitly deferred to a follow-on lane per the prompt). `editorial.ts` was read only,
never edited.
