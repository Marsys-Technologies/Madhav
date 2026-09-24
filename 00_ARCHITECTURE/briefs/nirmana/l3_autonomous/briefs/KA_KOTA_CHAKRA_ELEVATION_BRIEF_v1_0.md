---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_KOTA_CHAKRA_ELEVATION_BRIEF
version: "1.1"
status: PROPOSED_FOR_NATIVE_RULING      # v1.0 → ACCEPT_WITH_CORRECTIONS (REVIEW_KA_KOTA_CHAKRA_v1_0.md, 21 findings); v1.1 folds each
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
asset_or_interface_ids: ["ka_kota_chakra", "SC-1 (the build-time date.today() horizon becomes a declared input)", "SC-5 (coverage on a rolling horizon)", "SC-8 (the single ayanāṃśa offset as a declared, edge-bounded approximation)", "registry successor: a version-aware integrity conjunct (a) — today's has NO version predicate", "Gochara w25 proposed-use (N-8 / M-4) + a registry-disagreement item"]
goal_objective: "Make the fort chart's rows say which horizon they were computed for and under which ring-table version, so a rebuild is a declared re-scan rather than a silent replacement and the integrity check can distinguish a stale grading from a wrong one; label the posture/severity synthesis the uncited extension it already admits to being and constrain its vocabulary; derive corpus verifiability from the L0 row that already carries it; and bound the single-offset approximation where it actually bites — window edges, not nakṣatra spans."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code identical at 3387c9ac3 (2026-09-24)"
accepted_upstream_contract: "L1 chart_facts MOON longitude_sidereal at lahiri_chitrapaksha (fact id carried; the fetch has no ORDER BY — see §2.2); L0 ephemeris_daily tropical knots at NOON UT (l0_ephemeris.py:160-161,:271-278); L0 bg_kota_chakra_rings — versioned `kota_chakra_rings_vNN` (l0_kota_chakra_rings.py:73; 523:45), revisions land by APPEND (523:44-48), PK (table_version, ring_position) (523:67), and the row already carries corpus_status DEFAULT 'not_in_corpus' (523:64) with ADJUDICATION-9's own 0-hit corpus finding (523:37-39)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_KOTA_CHAKRA_v1_0.md (ACCEPT_WITH_CORRECTIONS); re-verification of v1.1 pending"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_kota_chakra/{logic,writer}.py", "platform/python-sidecar/tests/l3/test_ka_kota_chakra_writer.py (today it covers only the two fetch helpers; run() is untested)", "one NEW registry migration: a version-aware successor to ka_kota_chakra's integrity_check_sql (conjunct (a) must join on table_version) plus a stale_partition signal — migration 670 is applied and is never edited", "one additive DDL migration on kala_kota_chakra (requested_horizon_start/end, ring_table_version, window_id, claim_grain/comparable_with/tier_basis/corpus_verifiable, and the two CHECK constraints) — or a qualification JSONB per §10.2"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_kota_chakra.ts:83 (the UTC-date `as_of` default) and :103-109 (the explicit column whitelist a new stamp must be added to) — Pūrṇa-owned", "platform-mcp/src/tools/kala_views/now.ts:418-445 (item 16) — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["brahmagyan/l0_kota_chakra_rings.py, bg_kota_chakra_rings (L0 — the partition, its citation tier and its corpus_status are L0's)", "ephemeris_daily / bg_ephemeris (L0)", "services/gochara_v3/mechanisms/w25_kota_chakra.py (Gochara-owned)", "platform-mcp/src/tools/kala_views/**", "platform/supabase/migrations/520_kala_kota_chakra.sql, platform/migrations/670_*, 853_* (applied)", "applied migrations 1033–1070", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → QUALIFIED at stage 3; no t3 event today"
wave: "W2 (foundation)"
shape: single asset, rows (chart × graha × ring-run over a rolling −60/+400-day horizon)
evidence_base: >
  Source read directly on 9feac52d7 [V]; reviewer-verified claims adopted are marked [R]; migrations
  520/523/670/853, blueprint v5.0, ADJUDICATION-9 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.1 (2026-09-24): ACCEPT_WITH_CORRECTIONS dispositions (21 findings) — F-01 the live conjunct (a) has NO table_version predicate, so it joins EVERY version and fails globally once a second version is appended: the defect is version-blindness, not stale-row detection, and the version pin is a PRECONDITION of the successor, not an add-on; F-02 the Positive fixture could not produce rows (the completeness gate demands one ephemeris row per inclusive horizon day); F-03 the two served files moved out of may_touch and both migration paths corrected; F-04 coverage has no persistence home under delete-then-insert — two implementable forms named and one chosen; F-05 corpus verifiability is DERIVED from bg_kota_chakra_rings.corpus_status, not hardcoded as a writer-local basis string (which would be the §N.7 item-3 shadowing the brief claimed to satisfy); F-06 mechanism_register.yaml:145 records w25 as admitted/fitted against evidence files that do not exist — a registry disagreement handed to Gochara; F-07–F-21 citations, the L3-A07 row, the UTC (not server) date, the edge-shift bound, the un-ordered janma fetch, three unfailable proof rows, the 853 per-graha counts, and the fact that run() has no test at all."
  - "1.0 (2026-09-24): first issue."
---

# `ka_kota_chakra` elevation brief — a fort chart with a declared horizon

## §0 — The recommendation, in one paragraph

`ka_kota_chakra` places each transiting graha in one of four rings by its nakṣatra count from the
natal Moon, over a horizon of **`date.today()` − 60 d to + 400 d computed at build time**
(`writer.py:239-241` [R]), against a ring partition read as the **latest**
`bg_kota_chakra_rings.table_version` (`MAX(table_version)`, `:90`), with one ayanāṃśa offset computed
at `today` (`:243`) and applied across the horizon. Its per-row disclosure is unusually honest —
`start_truncated`/`end_truncated`, `uncited_extension=TRUE` on every row for the posture/severity
synthesis (`:292`; `logic.py:45-55,:114-117`; DDL default `520:51`), `ring_table_citation` copied
verbatim from L0 (`:157-162,:175-177`). Four things are missing or wrong. (1) The rows do not say
**which horizon** they belong to; under delete-then-insert (`:305-309`) a later rebuild's windows
replace an earlier set with nothing recording the move — and `WriterResult.notes` (`:318`) is **not
persisted** (`asset_runner.py:742-792` aggregates only row counts) [R]. The current horizon is
inferable from row extremes, because the completeness gate forces every graha's first run to start at
`horizon_start`; the *previous* horizon is not recoverable. (2) The rows do not name the **partition
version** that graded them — and the live integrity conjunct (a) (`670:894-899`) has **no
`table_version` predicate at all** [R]: it joins `bg_kota_chakra_rings` on `ring_position` alone,
and since revisions land by APPEND (`523:44-48`) under PK `(table_version, ring_position)`
(`523:67`), the moment a second version exists every row of every chart is joined against both and
(a) fails globally wherever the two disagree. The defect is **version-blindness**, not stale-row
detection, and the pin is therefore a *precondition* of any successor, not an optional stamp.
(3) `severity`/`posture` are free `TEXT` (`520:43-44`) although the vocabulary is a closed template
(`logic.py:106-111`). (4) The served `as_of` defaults to the **UTC calendar date**
(`query_kota_chakra.ts:83`), which for an IST chart is the previous day between 00:00 and 05:30.
And corpus verifiability need not be invented: `bg_kota_chakra_rings` already carries
`corpus_status DEFAULT 'not_in_corpus'` (`523:64`) with ADJUDICATION-9's own 0-hit finding
(`523:37-39`) [R]. Recommendation: **`QUALIFY_LIMIT`** (plus one `ENRICH_CORRECT`: the horizon
becomes a declared input) — stamp `requested_horizon` and `ring_table_version`, derive
`corpus_verifiable` from L0, CHECK-constrain the two vocabularies, bound the single-offset
approximation at the window edge where it actually bites, and re-pin (a) on the version. Decisions:
§10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (`…CONTRIBUTION_REGISTER_v2_0.md:142`) | ring testimony; **"not an independent adverse vote by default"** [R] | that clause binds B4 (§7) |
| **Strategy §6.1 L3-A07 (`:277`)** [R] | *"Preserve ring testimony, exact version and applicability; **replace mutable latest-version selection with pinned authority**. Current v3 implementation does not consume it: qualify and prove any proposed integration."* | the version pin is already a ruled Strategy obligation — this brief executes it, it does not propose it |
| Strategy §3 (`:86-98`) | defines *Contact* and *Temporal testimony*; there is **no "Contact overlay" object** — that label is the blueprint's (`:325`) | the object here is *Temporal testimony* (posture) over a *Contact* |
| Blueprint §3.5 row 9 (`:325`), §4 (`:397`), §16.2 (`:907`) | served; corpus **0 rows** for "kota"; century **proposed-use** pending M-4 (N-8); version pinned, not latest | binds §4 |
| Migration 520 (`:33-56`) | DDL: `kota_ring` CHECK; `posture TEXT NOT NULL`, `severity TEXT NOT NULL` (**no CHECK**); DATE windows; truncation flags; `uncited_extension DEFAULT TRUE`; `id BIGSERIAL` (`:34`), `computed_at DEFAULT now()` (`:53`); `UNIQUE(chart, ayanamsha, graha, window_start)` (`:54-55`) | no horizon/version/grain column; `id`/`computed_at` make byte-equality comparisons impossible (F-16) |
| **Migration 670 (`:890-917`)** [R] | (a) `:894-899` ring = L0 partition — **no version filter**; (b) `:900-908` per-(chart,graha) tiling; (c) `:909-914` non-degenerate + nine grahas. No later migration alters this asset's `integrity_check_sql` (853 sets `expected_volume_*`; 900 a digest spec) | (a) is version-blind (F-01) |
| Migration 523 (`:37-39,:44-48,:64,:67`) [R] | ADJUDICATION-9: tier-iii citation; *"the ingested corpus has ZERO hits for kota/kotachakra terms"*; APPEND-only revisions; `corpus_status TEXT NOT NULL DEFAULT 'not_in_corpus'`; PK `(table_version, ring_position)` | **the corpus verdict is already an L0 row value** (F-05) |
| Migration 853 (`:27-30`) [R] | per-graha live measurement (Moon 442, Mercury 41, Venus 35, Sun 35, …); 670 `:1837` sets `target_floor = 588` | the most recent in-tree measurement; the blueprint's 585 and this are both [A] (F-20) |
| Gochara `w25_kota_chakra.py:9-10,:19-20,:26-29,:48-51,:163-181` | *"Admission into the live scoring path requires ablation evidence"*; multipliers 1.30/1.15/1.08/1.04; *"not surfaced in ClassContext.fetch()"* | the mechanism **cannot reach** the table through `ClassContext` (it does read `kota_chakra_data` when a context carries it) |
| **`mechanism_register.yaml:145`** vs `mechanisms/registry/w25_kota_chakra.yaml:13` and `grammar_v3_registry.yaml:148` [R] | `admitted` / `fitted` with an evidence link to `w43_ablation_runner.py` and `w44_weight_fitting.py` — **neither file exists** — against `candidate` in the other two | a GA.1-class registry disagreement inside Gochara's fence (F-06) |
| Seed (`asset_registry_seed.ts:2472-2487`) | `depends_on: ['ga_positions', 'bg_ephemeris', 'bg_kota_chakra_rings']` | accurate |
| `now.ts:418-445` (item 16) | `current_only: true` pushed into SQL ahead of the row cap — honest-empty preserved | good pattern; but the surface selects an explicit column whitelist (`:432-445`), as does `query_kota_chakra.ts:103-109` — no new stamp reaches either without the packet (F-18) |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_kota_chakra'`, `scope: 'per_chart'`,
`catalog_status: 'CURRENT'`. Cost: one ephemeris range read (9 bodies × ~461 days) + one swisseph
ayanāṃśa call; cheap; unmeasured.

### 2.2 The code [V]/[R]
- **Inputs**: natal Moon `longitude_sidereal` (SQL `:76-81`; fetch `:132-147`) — **no `ORDER BY`,
  no `LIMIT 1`, `fetchone()` at `:142`**, while `chart_facts` uniqueness includes `build_id`
  (`216_chart_facts_partial_indexes.sql:22,28`), so two build generations would make the pick
  order-undefined (mitigated in normal flow by `ga_writers/_idempotency.py:66`, which deletes the
  whole `fact_category` across builds) — F-15; ring partition `MAX(table_version)` (`:87-92`);
  `ephemeris_daily` tropical (`:94-99`); one `derive_sidereal` offset at `today` (`:243`).
- **Horizon**: `HORIZON_BACK_DAYS = 60`, `HORIZON_FORWARD_DAYS = 400` (`:73-74`) around
  `date.today()` (`:239-241`); `_has_complete_daily_series` (`:119-129`) requires **one row per
  inclusive horizon day**, else refusal *"incomplete daily ephemeris coverage … prior partition
  preserved"* (`:252-261`).
- **Rows**: per graha, `detect_ring_runs` → `count_from_janma` (`logic.py:47`) → `ring_for_count`
  (`:68-83`) → `attack_defence_reading` (`:114-124`) over `_READING_TABLE` (`:106-111`) with
  `NATURAL_MALEFICS`/`BENEFICS` (`:95-96`); every row `uncited_extension=True` (`:292`); truncation
  flags from the horizon edge; `ring_table_citation` from L0.
  **The closed vocabularies are:** `posture ∈ {attacking, reinforcing_perimeter, breaching_the_wall,
  guarding_the_wall, inside_the_middle_ward, settled_in_the_middle_ward, at_the_heart,
  anchoring_the_heart}`; `severity ∈ {watch, supportive, elevated, high, acute, strong_support}`
  (`logic.py:106-111` [R]) — spelled out here so the CHECK migration is derivable.
- **Write**: DELETE by chart, then INSERT `ON CONFLICT DO NOTHING` (`:101,:115,:305-309`); never
  commits. `WriterResult.notes` carries `horizon=…` (`:318`) and **is not persisted** [R].
- **No test exercises `run()`** — `tests/l3/test_ka_kota_chakra_writer.py:59-87` covers the two fetch
  helpers only, and `date.today()` is nowhere frozen (F-21).

### 2.3 Consumers [V]/[R]
| consumer | reads | role |
|---|---|---|
| `query_kota_chakra.ts` | rows; `MAX_LIMIT 50` (`:26`) with `truncated`/`total_matching` (`:122-123`); `current_only`; **`as_of` default = the UTC calendar date** (`:83`); explicit column whitelist (`:103-109`) | served `relevance_navigation` |
| `now.ts:418-445` | current ring per graha; `current_only: true` in SQL (`:430`) | served |
| `gochara_v3/mechanisms/w25_kota_chakra.py` | **declares** multipliers; **cannot reach** the table through `ClassContext`; registry records disagree (§1) | proposed-use (N-8) |
| Kāla writers, L4, Kṣetra | none | — |

**Live-path statement.** Served on two surfaces; scored by nobody; the UTC-date `as_of` default is
live on the wrapper.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `nakshatra_idx`, `count_from_janma`, windows | `COMPUTED_FACT_CONFIGURATION` | L0 knots + L1 Moon fact | `date_grain`, `noon_ut_knot`; single offset (`algorithmic_approximation`, edge-bounded — §4.6) |
| `kota_ring` | `QUALIFIED_RULE` (tier-iii, L0-cited) | `bg_kota_chakra_rings` **latest** | version unpinned on the row |
| `posture`, `severity`, `is_natural_malefic` | `INTERPRETIVE_INFERENCE` — template synthesis | this logic | `uncited_extension=TRUE` already; needs `source_qualification='algorithmic_approximation'`, a CHECK, **and `comparable_with`/`tier_basis` (B2 requires both on a graded quantity — `severity` is one)** |
| corpus support | none | **`bg_kota_chakra_rings.corpus_status`** (`523:64`) | `corpus_verifiable` is **derived**, not asserted (F-05) |
| horizon | build-time **UTC** date | this writer | undeclared on rows |

### 2.5 Ladders
`PLAN_REVIEWED`; W2 source accepted. t3: no event.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | Append a second ring-table version to `bg_kota_chakra_rings` (the L0 revision mechanism, `523:44-48`) and the live integrity conjunct (a) — which joins on `ring_position` alone (`670:894-899`) — evaluates **every** `kala_kota_chakra` row of **every** chart against **both** versions, so it returns FALSE wherever the two partitions disagree at any position, whether or not that chart was rebuilt. Separately, build on day D (rows cover D−60…D+400), rebuild on D+90 (rows cover D+30…D+490): the earlier span is deleted, nothing persisted records that the horizon moved (`WriterResult.notes` is not stored), and a consumer holding a `window_ref` from the first build finds no row and no reason. And the row's `severity='watch'` is a free string a consumer cannot enumerate, while the served "current" row is chosen by a UTC date |
| Evidence | `670:894-899`; `523:44-48,:67`; `writer.py:239-241,:90,:305-309,:318`; `asset_runner.py:742-792`; `520:43-44,:54-55`; `query_kota_chakra.ts:83` — [V]/[R] |
| Expected contract | **L3-A07** (*replace mutable latest-version selection with pinned authority*); SC-1 (a horizon is a declared input); SC-5/B5 (coverage incl. `unsearched_regions`); B3 (`window_ref` with a version-bearing `generation`); B2 (`source_qualification` split; `corpus_verifiable`; `comparable_with`/`tier_basis` on a graded quantity); §N.7 item 3; F28 |
| Defect class | **version-blind detector** + **wrong context** (build-time UTC date as horizon) + **unpinned generation** + **unqualified** (free-text severity/posture; corpus stamp not derived) + **coverage absent** |
| Impact | (a) becomes globally red on the first L0 revision, with no way to distinguish "graded under v01" from "graded wrongly"; rolling re-scans are indistinguishable from rebuilds; a Gochara admission (N-8) would be against an unpinned partition; an off-by-one "current" ring for an IST chart between 00:00 and 05:30 |
| Non-claim | no ring assignment is wrong; the < 0.02° single-offset bound holds as an **angle** (≈0.015° at +400 d) but is **not** bounded as a date-grain claim (§4.6); the live 670 result, the live version set and the row count (585 blueprint / 588 floor / 853's per-graha sum) are all [A] |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** **Q04** verbatim (`STRATEGY:65`): *"activity coexisting with strain"* — supporting
   and inhibiting paths can overlap; proof: *"a decisive second-domain opposition survives
   compilation"*. Q03 as substrate. Q-K06 is cited only as the baseline question the Value row runs
   against, not as an adopted question (F-12).
2. **Horizon declared (SC-1/B5, F-04).** The horizon becomes an explicit input: `requested_horizon =
   [as_of − 60 d, as_of + 400 d]` with `as_of` from `ctx.config` (chart-zone today by default,
   echoed) — never `date.today()` read inside the writer. **Persistence, under the "replace" policy
   (§10.1):** each row carries its `requested_horizon_start/end`, and the per-build coverage is
   **stateless** — `unsearched_regions = [ <requested_horizon.start, >requested_horizon.end ]`, which
   names any dropped span *without* remembering the previous horizon. A consumer resolves a stale
   `window_ref` by comparing its date against the current generation's coverage. (The alternative,
   retaining prior generations keyed by `requested_horizon`, would require widening the natural key
   `(chart, ayanamsha, graha, window_start)` (`520:54-55`) or the second generation collides on
   `ON CONFLICT DO NOTHING` — §10.1.)
3. **Partition version pinned (B3) — a precondition, not a stamp (F-01).** `ring_table_version`
   (form `kota_chakra_rings_vNN`, F-11) on every row; `window_id = sha256(chart, ayanamsha, graha,
   window_start, FORMULA_VERSION, ring_table_version)` and `window_ref = {asset_id, generation:
   ring_table_version + FORMULA_VERSION, id: window_id}` — the DDL addresses rows by `id BIGSERIAL`
   today, which B3 forbids as an identity. The **successor conjunct (a)** joins
   `r.table_version = k.ring_table_version`, so it measures "is this row's ring what the partition it
   names says", and a separate **`stale_partition`** signal (`k.ring_table_version <> MAX`) marks
   rows graded under a superseded version **without failing the contract**. Without the pin, (a)
   cannot be written correctly — hence precondition.
4. **Qualification (B2).** `epistemic_class` per §2.4; `source_qualification`: `kota_ring →
   'verse_cited'` carrying L0's tier-iii citation (as today), `posture/severity →
   'algorithmic_approximation'` with `uncited_extension=TRUE`; **`corpus_verifiable` derived from
   `bg_kota_chakra_rings.corpus_status` (`= 'in_corpus'`), carried the same way `citation` already
   is** — never a writer-local basis string, which would shadow the L0 value and drift from it the
   day the corpus gains Muhūrta-Cintāmaṇi (`523:39-42` files that work item) [F-05];
   `comparable_with='self'` and `tier_basis='relative_uncalibrated'` on `severity` (B2 requires both
   on a graded quantity, F-12/binding); `claim_grain='date_grain'`, `time_basis='noon_ut_knot'`,
   `inclusivity='closed_closed'` (`logic.py:121` uses `<=`).
5. **Closed vocabularies.** `severity` and `posture` gain CHECK constraints over the §2.2 value sets
   — one additive migration.
6. **The single-offset approximation, bounded where it bites (F-14).** The angular bound holds
   (~50.3″/yr × 1.10 yr ≈ 0.015° < 0.02°), but the writer's own comparison ("negligible next to a
   13.33° nakṣatra span") is the wrong denominator: the material effect is on **boundary-crossing
   dates**, and for a body moving < ~0.05°/day (Saturn ≈ 0.033°/d; the nodes ≈ 0.053°/d) a 0.015°
   error at a nakṣatra edge can move `window_start`/`window_end` by **one calendar day**. So either
   compute the offset per day (the writer's own cost note says this is ~9 × 460 swisseph calls —
   cheap by its own §2.1 accounting), or stamp
   `window_edge_tolerance_days = 1` for slow bodies and `0` otherwise.
7. **`as_of` (SC-1) at the wrapper** in the chart's zone, echoed — noting the default is the **UTC**
   calendar date, not the server's zone (F-13).
8. **B1 served type.** The DDL keeps `DATE` windows; the binding wants served `t_start/t_end` as
   `timestamptz`. This brief **declares the mapping**: the DATE columns are the natural key and stay;
   `t_start/t_end` are derived views at the chart's tz-aware midnight via
   `services/ka_temporal/date_resolver` (B1's "resolver" row), not a second conversion here.
9. **Gochara (N-8) untouched, plus a registry item (F-06).** The multipliers stay proposed-use; this
   brief supplies the pinned, stamped rows the M-4 operand audit needs. Separately,
   `mechanism_register.yaml:145` records w25 as `admitted`/`fitted` against evidence files that do not
   exist, while two other registries say `candidate` — handed to Gochara's owner, because a future
   loader reading that register would admit the multipliers without the ablation N-8 requires.
10. **Old vs new.** Positive: rebuild with a declared `as_of` → rows with horizon + version stamps +
    coverage. Negative: a graha's daily series incomplete → refusal naming it, coverage `exclusions`
    recording it. Boundary: a run touching the horizon edge → `start_truncated` **and**
    `unsearched_regions` naming the span beyond. Missing: `bg_kota_chakra_rings` empty → refusal.
    Duplicated: rebuild twice with the same `as_of` → identical rows **on the natural key and payload
    columns, excluding `id` and `computed_at`** (F-16).
11. **Simpler baseline.** The rows as they are.
12. **Ablation.** Rebuild on two `as_of` dates: today the second build silently replaces the window
    set; after, its coverage names the dropped span and every row names its horizon and version — the
    difference is the named span and the version.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: ring arithmetic; the L0 partition read (now pinned and version-aware); truncation
  flags; refusals; delete-then-insert; `uncited_extension`; `now.ts`'s `current_only`-in-SQL pattern.
- `QUALIFY_LIMIT`: the stamps in §4.3–4.6, 4.8; the CHECKs.
- `ENRICH_CORRECT`: `as_of` from config instead of `date.today()`; a total `ORDER BY`/`LIMIT 1` on
  the janma-Moon fetch (F-15).
- **Migration**: one additive DDL (stamp columns + two CHECKs) and one registry successor
  (version-aware (a) + `stale_partition`) — 670 is applied and never edited.
- Fences: L0 partition untouched; Gochara's w25 untouched; both served files are interface-packet
  targets.
- Rollback: additive; the writer reads `as_of` with a config default.

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | L3 rows; L0/L1 facts + tier-iii partition + template synthesis; object = *Temporal testimony* over a *Contact* (F-09); `QUALIFY_LIMIT` + one `ENRICH_CORRECT` |
| B | three declared edges, all real; fan-out: two served surfaces; Gochara proposed-use |
| C | invariants: successor (a) against the **named** version; every row names horizon + version; severity/posture ∈ closed sets; `as_of` echoed; deterministic janma pick. Golden: canonical chart's rings on a fixed fixture date |
| D | corpus support absent (derived from L0, not fabricated) |
| E | served ×2; scored ×0 |
| F | coverage, version, `corpus_verifiable`, closed vocabularies machine-readable |
| G | cheap; the per-day offset option costs ~4,140 swisseph calls — measured against the current single call at stage 3 |
| H | idempotent; refusal on incomplete series |
| I | files in `may_touch`; W2; one DDL + one registry successor |
| J | this brief; §7; the review |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | I | fixture ephemeris spanning **2025-12-31 … 2027-04-05 inclusive** with `as_of=2026-03-01` (the completeness gate demands one row per horizon day — F-02); rebuild; run the successor contract | rows with `requested_horizon=[2025-12-31, 2027-04-05]`, `ring_table_version`, coverage; contract TRUE | (a)–(c) + stamps | stamp absent / FALSE; or the writer refuses because the fixture is short | integrity SQL |
| Negative | COMPUTATIONAL_CORRECTNESS | I | Mars series missing one day | refusal names Mars; prior partition kept | honest refusal | rows written | writer test (**`run()` has no test today** — F-21) |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | U | natal Moon nakṣatra +1 | every `count_from_janma` −1; rings shift per the partition | isolation | posture unchanged where the ring changed | unit test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | S | two `as_of` inputs resolving to the **same chart-zone date** | identical current rows | zone-normalised | differs | wrapper test |
| Relevant influence (zone) | COMPUTATIONAL_CORRECTNESS | S | instant 2026-03-01T22:00Z (= 03-02 03:30 IST) on a day a graha changes nakṣatra | the served `as_of` echoes the chart-zone date and the current row is the 03-02 run | chart-zone resolution | the UTC date is used (today) | wrapper test |
| Duplication | COMPUTATIONAL_CORRECTNESS | I | rebuild twice, same `as_of` | identical on the natural key + payload columns, **excluding `id` and `computed_at`** | idempotent | a real payload difference | writer test |
| Context | COMPUTATIONAL_CORRECTNESS | I | rebuild with `as_of` + 90 d | new generation; coverage `unsearched_regions` names the spans outside the new horizon | declared re-scan | silent replacement (today) | writer test |
| Boundary | COMPUTATIONAL_CORRECTNESS | U | a run starting on horizon day 1; a slow graha (Saturn) whose ring changes within `window_edge_tolerance_days` | `start_truncated=true` + the region named; the edge tolerance stamped | edge honest; the offset approximation bounded where it bites | truncated without a region; no tolerance stamp | unit test |
| Duplication (janma) | COMPUTATIONAL_CORRECTNESS | I | two `chart_facts` MOON rows under different `build_id` | deterministic pick under a total `ORDER BY … LIMIT 1` | §N.7 item 2 | order-undefined `fetchone()` (today) | writer test |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel `corpus_verifiable=false` (derived) on one row | reaches `now.ts` item 16 and `query_kota_chakra`'s envelope — **gated on the Pūrṇa packet, since both surfaces select explicit column whitelists** | survives | absent | MCP/route test (L3-owned) |
| Revision | COMPUTATIONAL_CORRECTNESS | I | append `kota_chakra_rings_v02` differing at one position; rebuild **one** chart | that chart's rows `v02`; others `v01` + `stale_partition=true`; the **successor** contract TRUE for both | version-aware join | today's (a) goes FALSE for every chart | integrity SQL |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | S | the frozen Q-K06 baseline question | a posture with its horizon, version, corpus stamp and edge tolerance; the baseline gives posture alone | — | no distinction | baseline record |
| Evaluation | — | — | `not_applicable` | — | — | — | — |

Binding: **OFFERS** B1 (`inclusivity`, `time_basis`, `claim_grain`; `t_start/t_end` as declared
resolver-derived views over the DATE key), B2 (`epistemic_class`, `completeness_state`,
`source_qualification`, `corpus_verifiable` **derived from L0**, `comparable_with`, `tier_basis`,
`operator_role='testimony'`), B3 (`window_id` sha256 + a version-bearing `generation`), B5
(`coverage`). **B4:** `independence_group` per graha, `basis='declared_lineage'` — carrying the
register's *"not an independent adverse vote by default"* (`REGISTER:142`). **Asset-local:**
`ring_table_version`, `requested_horizon_start/end`, `stale_partition`, `uncited_extension`,
`start/end_truncated`, `window_edge_tolerance_days`.

---

## §8 — Prioritization

(1) the version pin (precondition for a correct (a), and L3-A07's own obligation) → (2) horizon as
input + coverage → (3) qualification stamps + CHECKs + derived `corpus_verifiable` → (4) the edge
tolerance or per-day offset → (5) `as_of` at the wrapper → (6) the janma-fetch ordering → (7) hand
the stamped rows to N-8 and the registry disagreement to Gochara. T0; W2.

---

## §9 — Disposition and target state

`QUALIFY_LIMIT` (+ `ENRICH_CORRECT` for the horizon input and the janma ordering). Data-plane:
`PRODUCER_READY`; `DATA_ACCEPTED` on the production successor contract TRUE with stamps;
`CONSUMER_INTEGRATED` when the served surfaces carry them. Campaign: `ANALYZED → QUALIFIED`.
Non-claims: no `VALUE_EVALUATED`; Gochara admission is N-8's; corpus support is absent and stays
derived-and-stamped.

**Walkthrough (ordinary period).** "Where is Saturn in my fort right now?" → one current row:
`prakara`, `posture='attacking'`, `severity='moderate'` (closed set), `ring_table_version=
'kota_chakra_rings_v01'`, `requested_horizon` shown, `corpus_verifiable=false` (from L0),
`uncited_extension=true`, `window_edge_tolerance_days=1`. The reader knows it is a cited ring with an
engineered reading, no corpus behind the word "kota", and a ±1-day edge.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Horizon policy on rebuild: replace (one generation; the dropped span named statelessly as `unsearched_regions`) or retain prior generations keyed by `requested_horizon` (which needs the natural key widened)?** | replace + name the span — the table is a rolling overlay, not a ledger |
| 2 | Stamp home: columns vs `qualification` JSONB | columns for `ring_table_version`, the horizon and `window_id` (a CHECK and a join can bind to them); JSONB for the rest |
| 3 | CHECK constraints on `severity`/`posture` from the §2.2 value sets | yes |
| 4 | **The registry successor: (a) joins on `ring_table_version` and `stale_partition` is a separate signal** | yes — without the pin, (a) cannot be written correctly |
| 5 | The single-offset approximation: compute per day, or stamp `window_edge_tolerance_days` | stamp now; measure the per-day cost at stage 3 |

---

## §11 — Not verified here

1. Live 670 result, live `table_version` set, live row count (blueprint 585 / floor 588 / 853's
   per-graha sum — all [A]).
2. The corpus count itself is DB-resident; two in-tree attestations exist (ADJUDICATION-9 `:572`
   *"0 hits across 10,651"*; `523:37-39`) — corroboration, not verification.
3. N-8 and M-4's own text — carried from the blueprint [A]; no Gochara plan in this worktree defines
   them.
4. Whether `mechanism_register.yaml`'s `admitted` entry is ever loaded at runtime — no Python reader
   found under `services/gochara_v3`.
5. The ayanāṃśa drift rate (~50.3″/yr) is the writer's own docstring figure, not measured here.
6. No database query; no test run.

## §12 — Review dispositions (v1.0 → v1.1)

F-01 accepted (§0, §1, §3, §4.3, §7 Revision, §10.4 — version-blindness, and the pin as a
precondition); F-02 accepted (§7 Positive fixture span); F-03 accepted (`interface_packet_targets`,
`must_not_touch`, both migration paths); F-04 accepted (§4.2 — the stateless form chosen, the
retain alternative named with its key consequence); F-05 accepted (§0, §2.4, §4.4 — derived from
`corpus_status`); F-06 accepted (§1, §4.9 — the registry disagreement handed to Gochara); F-07/F-08
accepted (citations `:239`, `:243`, `logic.py:45-55`, `:106-111`, `:114-124`; the value sets spelled
out); F-09 accepted (§1 L3-A07 verbatim; the object mapped to *Temporal testimony*; the register's
independence clause carried to B4); F-10 accepted (§0, §3 — the current horizon is inferable, the
previous is not); F-11 accepted (`kota_chakra_rings_vNN`); F-12 accepted (§4.1 — Q04 verbatim with
its proof; Q-K06 as the baseline question); F-13 accepted (UTC, not server); F-14 accepted (§4.6 —
the edge-shift bound); F-15 accepted (§2.2, §5, §7 janma row); F-16 accepted (§4.10, §7 Duplication —
excluding `id`/`computed_at`); F-17 accepted (§7 — the control split into a zone-normalised control
and a zone-relevant influence row); F-18 accepted (§7 Delivery gated on the packet); F-19 accepted
(§1, §2.3 — "cannot reach through `ClassContext`"); F-20 accepted (§1, §3 — 853's figures); F-21
accepted (§2.2, §7 Negative — `run()` is untested today).
