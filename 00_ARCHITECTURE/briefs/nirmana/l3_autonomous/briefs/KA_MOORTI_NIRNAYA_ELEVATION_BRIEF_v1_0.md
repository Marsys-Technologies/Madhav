---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_MOORTI_NIRNAYA_ELEVATION_BRIEF
version: "1.1"
status: DRAFT_FOR_INDEPENDENT_RE_REVIEW      # v1.0 → REWORK (REVIEW_KA_MOORTI_NIRNAYA_v1_0.md: 1 BLOCKER, 5 MAJOR, 14 minor/note); v1.1 disposes each
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
synergy_binding_version: "2.3"  # binding is UNADOPTED (PROPOSED_FOR_NATIVE_RULING_THEN_ADOPTION) and its §B8 item 9
# still lists the rename direction as open while §B1 asserts it. Authority for the field NAME is therefore the
# underlying rulings, not the binding: Kṣetra ruling 8 + Gochara G-9 + Saṅgam M-3 name `precision_regime`, native
# ruling D-S4 (2026-09-24) confirms it. Alias condition is Saṅgam D-7: `day_grade` reads as `date_grain` until every
# dependent claim has an authorized successor — NOT for a count of generations. Values {instant_grain, date_grain}.
asset_or_interface_ids: ["ka_moorti_nirnaya", "G21 (the F4 grant on bg_transit_moorti — numbered 1071 by ruling R6, 1073 by blueprint §5.3; absent on this base)", "a 670-SUCCESSOR migration amending conjunct (f) IF the native takes §10.1(a) — without it, an 'unavailable' row fails the post-write gate and the build still errors", "SC-1 (the build-time date.today() horizon)", "SC-8 / a DEMAND on the position reference for ingress-INSTANT grading", "Gochara w22 + Kṣetra ruling-4: both recorded as not-live"]
goal_objective: "Make the mūrti grading survive its own dependencies and say what it measures: an L0-table lookup (cited) keyed by the Moon's nakṣatra at the ingress DATE's noon-UT knot — which LAGS the true ingress instant by 0–24 h, one-sided, so roughly half of all graded rows are expected to carry an offset one step ahead of the instant value — over a declared horizon, with a missing grant producing an F06 state rather than a build outage, and without asserting a repair the post-write integrity gate would reject."
source_revision: "9feac52d7 (l3/kala-layer-briefs); `git diff 9feac52d7 3387c9ac3 -- services/ka_moorti_nirnaya/` is empty"
accepted_upstream_contract: "L1 chart_facts MOON longitude_sidereal at lahiri_chitrapaksha (fact id carried; 670(d)); L0 ephemeris_daily tropical knots computed at NOON UT (l0_ephemeris.py:271,:278); L0 bg_transit_moorti (migration 401; 27 rows; Phaladeepika Ch.26 / BPHS Ch.28 per L0 401:3,:35 — note w22_moorti_nirnaya.py:9 cites Ch.27, a Gochara-owned discrepancy) — READ WITHOUT A GRANT GUARD; the grant is G21, absent on this base"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_MOORTI_NIRNAYA_v1_0.md (REWORK); re-verification of v1.1 pending"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_moorti_nirnaya/{logic,writer}.py", "platform/python-sidecar/tests/l3/test_ka_moorti_nirnaya_writer.py", "one 670-SUCCESSOR registry migration amending conjunct (f) — REQUIRED if §10.1 takes option (a); 670 is applied and is never edited", "one additive DDL migration on kala_moorti_nirnaya (requested_horizon, grading_basis, reason, window_id) — or a qualification JSONB per §10.3"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_moorti_nirnaya.ts:81 (the `as_of` default) and its explicit column whitelist — Pūrṇa-owned", "platform-mcp/src/tools/kala_views/now.ts:497-556 — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["bg_transit_moorti, brahmagyan/** (L0 — the grant is a migration owned by G21; this brief adds the guard, not the grant)", "ephemeris_daily / bg_ephemeris (L0)", "services/gochara_v3/** (the context prefetch and w22 are Gochara-owned)", "services/ka_kshetra/** (ruling 4, not executed)", "platform-mcp/src/tools/kala_views/**", "platform/supabase/migrations/525_kala_moorti_nirnaya.sql, platform/migrations/670_*, 852_*, 853_*, 855_*, 900_* (applied)", "applied migrations 1033–1070", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; blueprint §4: 'cannot rebuild' today (G21)"
wave: "W2 (foundation)"
shape: single asset, rows (chart × graha × sign-run over a rolling −60/+400-day horizon; 8 grahas, Moon excluded by design)
evidence_base: >
  Source read directly on 9feac52d7 [V]; reviewer-verified claims adopted are marked [R]; migrations
  525/670/401/852/853/855/900, blueprint v5.0, ruling sheet R6 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.1 (2026-09-24): REWORK dispositions (20 findings) — F-01 (BLOCKER) the recommended guard outcome cannot be executed inside the brief's own fences: migration 670 conjunct (f) (:1079-1089) requires EVERY interior run to be graded, and the orchestrator runs integrity_check_sql after the writer and rolls back + marks the asset error on failure (asset_runner.py:1041,:1064-1072), so writing `unavailable` rows still ends in `error` — option (a) now REQUIRES a 670-successor amending (f), and option (b) (refuse, prior partition preserved) is the fence-clean alternative; F-02 the grain defect is one-sided and much larger than stated: the run start is the first NOON-UT knot in the new sign, so the Moon knot used is 0–24 h AFTER the ingress, never before, and ~49% of graded rows are expected to carry an offset one step ahead — the §3 example was inverted and the 'if zero, decorative' clause is impossible; F-03 Gochara PREFETCHES moorti rows but engine.py never consumes them (no w22 reference; λ has no mūrti term) — 'century v3 actual input' was false; F-04 the Moon-gap branch is dead under the completeness gate; F-05 the instant-boundary proof row was inverted and unfailable; F-06 Kṣetra's build_moorti_primitive reads bg_transit_moorti directly and has NO caller; F-07 the guard's real trace (savepoint → rollback → asset_throughput.last_error) replaces 'survives by accident'; F-08–F-20 control/value rows, citations, paths, the grant's number, B5/B2/B1 gaps, the root-find's owner, 71 vs 72, Q-K06, two more readers, the over-reading column name, the Ch.26/27 discrepancy."
  - "1.0 (2026-09-24): first issue."
---

# `ka_moorti_nirnaya` elevation brief — the ingress grade, guarded and dated honestly

## §0 — The recommendation, in one paragraph

`ka_moorti_nirnaya` grades each sign-ingress of eight grahas (Moon excluded by declared design,
`logic.py:22-30,:64-66`) as svarṇa/rajata/tāmra/loha by the Moon's nakṣatra offset from the natal
Moon at the ingress, looked up **verbatim** in L0's `bg_transit_moorti` (`writer.py:164-171`), over a
`date.today()` −60/+400-day horizon (`:203-205`). Its integrity contract is the strongest in the
layer — (a)–(h) including `moorti_computed` **re-derived** rather than self-reported (670
`:1079-1089`, §N.8). Three things are wrong, and the reviewer corrected my own account of two of
them. (1) `_fetch_moorti_table` has **no guard** (`:164-171`: bare cursor, no SAVEPOINT, no try); with
the F4 grant on `bg_transit_moorti` missing, the SELECT raises. The **trace** is not "the prior rows
survive by accident": `_drive_substeps` wraps even light writers in `SAVEPOINT writer_exec` and rolls
back (`asset_runner.py:759-765`), `_run_data_writer` catches and calls `mark_asset_error`
(`:1047-1055`), and the failure **is** recorded in `asset_throughput.last_error` (`:523-528`) — the
prior partition survives by **transaction semantics**, and the real defect is that the asset carries
no F06 state of its own while `ka_gochara_v3_century_materialize` declares it a dependency under
`_DEP_ASSERT_MODE='enforce'` (`:44`). **And my v1.0 remedy was not executable:** conjunct (f)
requires every interior run to be graded, and the orchestrator runs the contract *after* the writer
and rolls back on failure (`:1041,:1064-1072`), so writing `completeness_state='unavailable'` rows
ends in `error` anyway — one step later, with a misleading message. (2) The rule is defined at the
ingress **instant**; the run's `start_date` is the **first date whose noon-UT knot shows the new
sign** (`logic.py:97-115`), so the Moon knot used is **0–24 h after** the true ingress — **one-sided,
never before** — and with the Moon at ≈13.2°/day against a 13.33° nakṣatra, **≈49 % of graded rows
are expected to store an offset one step ahead of the instant value** [R]. My §3 example was
inverted and my "if the difference is zero, the instant generation is decorative" clause was
impossible. (3) The horizon is the server's build date, unstamped. Also: Gochara **prefetches** the
rows (`context.py:186,:252,:274`) and `engine.py` **never consumes them** (no w22 reference; the λ
formula at `:632` has no mūrti term), and Kṣetra's `build_moorti_primitive`
(`stage1_symbolization.py:222-238`) reads `bg_transit_moorti` directly and has **no caller** — so
this asset has **zero live integrators**. Recommendation: **`ENRICH_CORRECT` + `QUALIFY_LIMIT`** —
the guard with the failure mode the gate actually admits (§10.1); `grading_basis` and `precision_regime`
stamped now with the one-sided lag named; an **ingress-instant DEMAND** whose root-find owner is
named; `requested_horizon` + coverage; `as_of` in the chart's zone. Decisions: §10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 | contact overlay (ingress quality) | — |
| Blueprint §3.5 row 10 (`:326`), §4 (`:398`), §5.3 G21, §16.2 (`:908`) | **unguarded read, grant missing (F4)**; *cannot rebuild*; *try/except + SAVEPOINT → F06 unavailable; ingress-instant grading (WP9); coverage = requested horizon; overlay stamps*; consumers: century v3 (actual input), Kṣetra S1 (ruled 4) | the consumer claims are **false at source** (§2.3); the rest is this brief |
| Migration 525 (`:64-103`, CHECK `:91-102`) | DDL: `moorti_name ∈ {swarna, rajata, tamra, loha}`, `quality_tier 1..4`, `nakshatra_offset 1..27`, `moorti_computed` + a consistency CHECK (computed ⇔ all grade fields non-null); DATE windows; truncation flags; `UNIQUE(chart, ayanamsha, graha, window_start)`; **`moon_nakshatra_idx_at_ingress`** (`:76-77`) | the column **name itself over-reads** the instant (F-18); no horizon/grain/basis column |
| **Migration 670 (`:1017-1117`), conjunct (f) `:1079-1089`** [R] | grade = L0 row; offset key resolves; offset is a restatement; janma fact id resolves; runs tile the horizon; **`moorti_computed` re-derived — a row violates when `m.moorti_computed = (m.window_start = h.h_start)`, i.e. every INTERIOR run MUST be graded** (`:1081-1082`); same horizon per chart; labels restate `reference_signs`. Not superseded (852/853/855 set volume fields; 900 a digest spec) | (f) is the reason §10.1(a) needs its own successor migration (F-01) |
| **`asset_runner.py:759-765, :1041, :1047-1055, :1064-1072, :523-528, :44`** [R] | light writers run inside `SAVEPOINT writer_exec`; a raise → `ROLLBACK TO SAVEPOINT` + re-raise → `conn.rollback()` + `mark_asset_error` → `asset_throughput.state='error', last_error=<traceback>`; when `integrity_check_sql` exists the commit is deferred and the check runs post-write, failing the same way; `_DEP_ASSERT_MODE='enforce'` | the guard's real trace (F-07) and the BLOCKER's mechanism |
| `logic.py:22-30,:37-55,:64-66,:97-115,:126-134` | Moon excluded by design; start-truncated runs are not graded because the true ingress is unknown; `MOORTI_GRAHAS`; run detection over noon-UT knots; `nakshatra_offset_from_janma` | the same reasoning the brief extends one step: the ingress **date** is not the ingress **instant** |
| `ka_avadhi.py:229-246`; `gochara_intensity/_dbutil.py:122` | writer-local savepoints nested under `writer_exec` are established practice | the guard is contract-conformant by precedent, not a contract change |
| Ruling sheet **R6** (`KALA_NATIVE_RULING_SHEET_v1_0.md:147-151`) [R] | numbers the grant **1071**; blueprint §5.3 says **1073**; in-tree 1071 is `kala_convergence_target_provenance.sql` and no `GRANT` naming `bg_transit_moorti` exists in either migration tree | the number is **unresolved**; the grant is absent here either way (F-11) |
| Migration 855 (`:5,:41,:72`) + `test_migration_855_…:34-37` [R] | live-measured **72** rows (per-graha sum); 670 `:1839` `target_floor = 72`; blueprint `:326` says 71 | both [A] (F-15) |
| `now.ts:497-556` (`:519-520`) | `moorti_computed=false` rows carry null grade fields **verbatim, never backfilled** | good; preserved |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_moorti_nirnaya'`, `scope: 'per_chart'`,
`catalog_status: 'CURRENT'`; 71 (blueprint) / 72 (855) rows live [A]. Cost: one ephemeris range read
(9 bodies incl. Moon × ~461 days) + one swisseph call; cheap.

### 2.2 The code [V]/[R]
- **Inputs**: natal Moon fact (`:69-73`, fetch `:120-135`); **`bg_transit_moorti` read unguarded**
  (`:164-171`; on an empty table → honest refusal `:196-201`; on a permission error → the exception
  propagates); `ephemeris_daily` tropical (`:76-80`); one offset at `today` (`:138-142`, `:243`).
  Note `_fetch_janma_nakshatra_idx` (`:120-135`) and `_fetch_daily_sidereal_by_body` (`:145-161`) are
  **equally bare** — §10.1 must say why only the L0 mūrti read is guarded.
- **Horizon**: `HORIZON_BACK_DAYS=60`, `FORWARD=400` (`:65-66`) around `date.today()` (`:203-205`);
  `_has_complete_daily_series` per body **including Moon** (`:107-117`, `bodies_needed` at `:208`)
  else the **whole build refuses** (`:211-225`).
- **Rows** (`:232-297`): per graha `detect_sign_runs`; `moorti_computed = not start_truncated`
  (`:243`); the Moon's nakṣatra **on the ingress date** from `moon_nak_by_date` (`:227-230`, lookup
  `:268`); `nakshatra_offset_from_janma`; the L0 row copied verbatim. The
  **`:292-295` Moon-gap branch is dead** under the completeness gate (F-04) — and 670(f) would reject
  such an interior ungraded row anyway.
- **Write**: DELETE by chart after the full candidate is assembled (`:305-308`), INSERT
  `ON CONFLICT DO NOTHING` (`:103`); never commits.
- **Tests**: `tests/l3/test_ka_moorti_nirnaya_writer.py:90-115` covers only the empty-table and
  keyed-dict cases of `_fetch_moorti_table`.

### 2.3 Consumers [V]/[R]
| consumer | reads | role |
|---|---|---|
| `query_moorti_nirnaya.ts` | rows; `MAX_LIMIT 50` + `truncated`/`total_matching`; `as_of` default = the UTC date (`:81`); explicit column whitelist | served `relevance_navigation` |
| `now.ts:497-556` | current rows; nulls verbatim | served |
| `gochara_v3/context.py:186,:252,:274` (`_fetch_moorti_rows` `:486-531`, savepoint-scoped, degrades to `[]`) | **prefetches** all rows into `ClassContext` — while **`engine.py` contains no `w22`/`moorti_rows` reference** (imports only w23/w30 at `:100-101`; the λ formula `:632` has no mūrti term) and `w22_moorti_nirnaya.py:18-19,:162-163` says it is not wired | **prefetched, not consumed** — no live caller within `services/gochara_v3/engine.py` (F-03) |
| `ka_kshetra/stage1_symbolization.py:222-238` | `build_moorti_primitive` takes the grade as **arguments** and stamps `source_table="bg_transit_moorti"`; **no caller** outside its own test; no Kṣetra file reads `kala_moorti_nirnaya` | ruled future consumer (ruling 4), **not executed** (F-06) |
| `source_query_availability.ts:2891-2894`; `data-plane-ownership-preflight.ts:63` | availability / ownership | census (F-17) |

**Live-path statement.** Served ×2; **zero live integrators**; **not rebuildable** today on the build
role (G21).

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| sign-run windows, `target_sign` | `COMPUTED_FACT_CONFIGURATION` | L0 knots | `date_grain`, `noon_ut_knot`, single offset |
| `moon_nakshatra_idx_at_ingress` | computed **on the ingress date's noon-UT knot** | L0 Moon knot | **lags the instant by 0–24 h, one-sided**; ≈49 % of rows expected one step ahead; the column name over-reads (F-18) |
| `nakshatra_offset` | restatement (670(c)) | this logic | differs from the instant value for **all** lagged rows, even where the tier does not |
| `moorti_name`, `quality_tier`, `phala_brief`, `classical_citation` | `QUALIFIED_RULE`, `verse_cited` | L0 `bg_transit_moorti` | copied verbatim — correct |
| `moorti_computed` | earned flag (670(f)) | this writer | means "run start inside the horizon and a Moon knot present" — **not** "graded at the instant" |
| horizon | server build date | this writer | undeclared |

### 2.5 Ladders
`PLAN_REVIEWED`; W2 source accepted; **rebuild blocked** (G21). t3: no event.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | **(i)** Build on a role without SELECT on `bg_transit_moorti`: `_fetch_moorti_table` raises inside `SAVEPOINT writer_exec`; the orchestrator rolls back, records `asset_throughput.state='error'` with the traceback, flips downstream assets stale, and the prior partition survives by transaction semantics. The asset itself carries no F06 state, and a dependent (`ka_gochara_v3_century_materialize`) declares it under `enforce`. **(ii)** Take Jupiter ingressing Taurus at 02:00 UT on date D: at noon UT of D−1 Jupiter is still in Aries, so the run's `start_date` is **D**, and the Moon knot used is noon UT of D — **10 h after** the ingress. The lag is always forward, uniform on (0, 24 h], and the Moon covers ≈6.6° in the mean case against a 13.33° nakṣatra, so **about half of all graded rows store `moon_nakshatra_idx_at_ingress` (and hence `nakshatra_offset`) one step ahead of the instant value**, with `moorti_computed=true` and a column named `…_at_ingress` |
| Evidence | `writer.py:164-171,:196-201,:203-205,:211-225,:227-230,:243,:268,:292-295,:305-308`; `logic.py:37-55,:97-115,:126-134`; `525:76-77,:91-102`; `670:1079-1089`; `asset_runner.py:759-765,:1041,:1047-1055,:1064-1072,:523-528,:44`; `l0_ephemeris.py:271,:278` — [V]/[R] |
| Expected contract | F06 (a dependency failure is a state, not an outage — **and not a row the post-write gate will reject**); §N.8 (a `computed` flag names exactly what was computed); B1 (an instant rule graded at date grain is an `algorithmic_approximation`, declared); SC-1; SC-8; B5 |
| Defect class | **unguarded dependency** (an outage with no asset-level state) + **grain mismatch undeclared, one-sided and large** + **wrong context** (build-date horizon; UTC `as_of`) + **prefetched-but-unconsumed** consumer |
| Impact | the asset cannot be rebuilt until the grant lands and fails loudly rather than degrading; **roughly half** the stored offsets are expected to differ from the instant value (the tier differs for the subset where adjacent `bg_transit_moorti` offsets disagree), unmarked, under a column name that asserts the instant |
| Non-claim | the ≈49 % figure is an **a priori** expectation from uniform ingress phase and mean lunar motion, not a measurement — the §4.11 ablation is the measurement; no claim the L0 table is wrong; the live grant state, the row count (71/72) and the live 670 result are [A] |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q05 (an ingress grade as one qualified voice). Q-K06 is a blueprint
   cross-reference, not an adopted question (F-16).
2. **The guard, with a failure mode the gate admits (F-01).** `_fetch_moorti_table` goes inside
   `SAVEPOINT sp_moorti_l0` + try/except (the `ka_avadhi.py:229-246` precedent). On failure, **two
   options, and only one is fence-clean**:
   **(a)** write the sign-runs with `completeness_state='unavailable'`, grade fields null — which
   **violates 670 conjunct (f)** for every interior run, so the post-write gate rolls the build back
   and marks `error` anyway. This option is only available **with a 670-successor migration** that
   amends (f) to admit interior rows carrying `completeness_state='unavailable'`; that migration is
   in `may_touch` and is part of the option.
   **(b)** refuse with the prior partition preserved and the reason in `notes` — exactly the writer's
   existing incomplete-series behaviour (`:211-225`), no migration, no gate conflict.
   §10.1 decides. Either way the build no longer raises an untyped exception, and the asset's own
   F06 state (with `reason`, `owner`, `evidence_ref`, `next_eligible_action` — F-12) is what a
   consumer sees instead of only `asset_throughput.last_error`.
3. **Grain and basis declared, with the right sign and size (F-02).** Every row:
   `precision_regime='date_grain'`, `time_basis='noon_ut_knot'`,
   `grading_basis='moon_nakshatra_on_ingress_date_noon_ut'`, and an explicit
   `grading_lag='0_to_24h_after_ingress_one_sided'`; `source_qualification`: the L0 lookup
   `'verse_cited'` (carrying `classical_citation`), the date-grain keying
   `'algorithmic_approximation'`. `moorti_computed` keeps its 670(f) meaning; the new fields carry
   the caveat the column name `moon_nakshatra_idx_at_ingress` does not (F-18).
4. **Ingress-instant grading — a DEMAND with a named owner (F-14).** A later generation grades at the
   ingress instant. The position reference (Graha Sañcāra brief §4 item 3) supplies **positions at an
   instant**; it does **not** supply an ingress root-find. The bisection of the graha's sign crossing
   between noon(D−1) and noon(D) over that kernel is **new numerical code owned by this writer**
   (precedent: `ka_tithi_pravesha/writer.py`'s Moon-return root-find), with its bracket and tolerance
   declared as part of the DEMAND so it is executable when the reference lands. Until then this brief
   adds **no second swisseph integration** (SC-8) and `grading_basis` is the switch.
5. **Horizon declared (SC-1/B5).** `as_of` from `ctx.config` (chart-zone today by default, echoed);
   `requested_horizon` on every row; per-build `coverage = {requested_horizon, **completed_horizon**,
   **resolution: 'calendar_day'**, partitions_searched: [8 grahas + Moon], exclusions: [refused
   bodies; uncomputed runs with reason], unsearched_regions: [], completion_detector:
   '_has_complete_daily_series'}` — `completed_horizon` and `resolution` were missing (F-12).
6. **`as_of` (SC-1) at the wrapper** in the chart's zone, echoed.
7. **B1/B2/B3 completions (F-12, binding).** `t_start/t_end` are declared **resolver-derived views**
   over the DATE key (chart-tz midnight via `services/ka_temporal/date_resolver`), not a second
   conversion here; `corpus_verifiable` (blueprint `:889` names it a WP9 stamp on this table),
   `comparable_with='self'`, `tier_basis='relative_uncalibrated'` on `quality_tier` (a 1..4 ordinal);
   `window_id = sha256(chart, ayanamsha, graha, window_start, FORMULA_VERSION)`, `generation =
   FORMULA_VERSION`.
8. **Consumers recorded as they are (F-03, F-06).** Gochara: *prefetched, not consumed* — the
   contradiction to hand its owner is **three-way** (`mechanism_register.yaml:87-103` says `admitted`;
   `context.py` prefetches; `engine.py` never invokes; the module docstring says not plumbed).
   Kṣetra: *ruled future consumer, not executed* (`build_moorti_primitive` has no caller and reads
   `bg_transit_moorti` directly). Neither is claimed as an integrator.
9. **Old vs new.** Positive: rebuild with the grant → rows with stamps + coverage. Negative: grant
   missing → per §10.1 either typed `unavailable` rows (with the 670 successor) or an honest refusal;
   **never an untyped exception**. Boundary: see §7. Missing: a Moon knot absent → **the whole build
   refuses** (`:211-225`) — the per-row branch is dead (F-04). Duplicated: n/a.
10. **Simpler baseline.** The rows as they are, with the grant.
11. **Ablation (the measurement).** Grade the canonical chart's ingresses under both bases; the set of
    rows whose `nakshatra_offset` differs is the measured lag incidence (expected ≈ half), and the
    subset whose `quality_tier` differs is the material one. There is **no** "if zero, decorative"
    branch — a zero result is not possible under a one-sided lag unless every ingress happens to fall
    within a nakṣatra's interior for the whole 24 h.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the verbatim L0 lookup; `moorti_computed`'s 670(f) meaning; the start-truncation rule;
  assemble-before-delete; the 525 CHECK; `now.ts`'s null carriage; the honest whole-build refusal on
  an incomplete series.
- `ENRICH_CORRECT`: the guard (§10.1); `as_of` from config.
- `QUALIFY_LIMIT`: `precision_regime`, `grading_basis`, `grading_lag`, `source_qualification`,
  `requested_horizon`, coverage, `reason` + its F06 companions.
- **Dead code named**: `:292-295` (unreachable under the completeness gate).
- **DEMANDS**: ingress-instant positions from the position reference (the root-find itself owned
  here); the L0 grant (G21 — numbered 1071 by R6, 1073 by the blueprint; unresolved).
- **Migration**: one additive DDL (stamps + `reason` + `window_id`) or JSONB (§10.3); **plus a
  670-successor if §10.1 takes option (a)**.
- Fences: L0 untouched; Gochara and Kṣetra untouched; both served files are interface-packet targets.
- Rollback: additive; the guard only widens the set of buildable situations.

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | L3 rows; L0/L1 facts + a cited L0 rule applied at date grain; `ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | declared edges real; fan-out: two served surfaces; **zero live integrators** |
| C | invariants: 670 (a)–(h) — **and any new row shape must satisfy (f) or ship with its successor**; every row names basis, lag and horizon; an unreadable L0 → a typed outcome, never an untyped exception; grade = L0 row |
| D | the instant computation (DEMAND); the grant (G21) |
| E | served ×2; Gochara prefetched-not-consumed; Kṣetra ruled-not-executed |
| F | `grading_basis`, `grading_lag`, `completeness_state`, `reason`, coverage machine-readable |
| G | cheap; the root-find adds one bisection per ingress (~15–60 per chart) |
| H | idempotent; savepoint boundary (precedent cited); refusal on incomplete series |
| I | files in `may_touch`; W2; one DDL + (conditionally) one 670-successor; DEMANDs with owners |
| J | this brief; §7; the review; the two-basis measurement |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served, `[X]` gated.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | I | fixture with grant; fixed `as_of`; rebuild; run 670 (+ successor if §10.1(a)) | rows with `grading_basis`, `grading_lag`, `requested_horizon`, coverage; contract TRUE | (a)–(h) + stamps | absent / FALSE | integrity SQL |
| Negative (guard) | COMPUTATIONAL_CORRECTNESS | I | revoke SELECT on `bg_transit_moorti` in the fixture role; rebuild | **per §10.1**: (a) `unavailable` rows **and the successor contract TRUE**, or (b) a refusal with the prior partition intact and `notes` naming the reason | a typed outcome; **no untyped exception; no post-write rollback** | the exception propagates (today); or `unavailable` rows are written without the successor and (f) rejects them | writer test + integrity SQL |
| Grading direction | COMPUTATIONAL_CORRECTNESS | U | `grade(moon_lon_at_ingress, janma_idx)` as a **pure function with the Moon-longitude oracle injected**: knot at noon 0.1° **after** a nakṣatra boundary; stub instant 6 h earlier → **before** it | date-grain → the later nakṣatra; instant → the earlier; the two differ | the lag is one-sided **forward** | the two agree, or the instant is "later" (the v1.0 inversion) | unit test |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | U | natal Moon nakṣatra +1 | every `nakshatra_offset` −1 (mod 27); tiers per the L0 table | isolation | offset unchanged | unit test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | S | two `as_of` inputs resolving to the **same chart-zone date** | identical current rows | zone-normalised | differs | wrapper test |
| Relevant influence (zone) | COMPUTATIONAL_CORRECTNESS | S | an instant straddling the IST/UTC date line on a day a run starts | the chart-zone date is used and echoed | chart-zone resolution | the UTC date is used (today) | wrapper test |
| Duplication | COMPUTATIONAL_CORRECTNESS | I | rebuild twice, same `as_of` | identical on the natural key + payload columns | idempotent | accretion | writer test |
| Context | COMPUTATIONAL_CORRECTNESS | I | Moon series missing one day | **the whole build refuses**, naming Moon; coverage `exclusions=['Moon']` (the per-row branch at `:292-295` is dead) | the completeness gate | a per-row `moon_knot_missing` expected | writer test |
| Boundary | COMPUTATIONAL_CORRECTNESS | U | ingress at 23:50 UT vs 00:10 UT of the next day | the run's `start_date` and hence the keyed Moon knot shift by one day; `grading_lag` stamped in both | run-detection boundary | the lag is described as bidirectional | unit test |
| Boundary (instant) | COMPUTATIONAL_CORRECTNESS | X | the same pure function with the **real** kernel oracle instead of the stub | identical assertions to the Grading-direction row | DEMAND landed | — (gated) | ablation record |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel `grading_basis` on one row | reaches `now.ts` and `query_moorti_nirnaya`'s envelope — gated on the Pūrṇa packet (both select explicit column whitelists) | survives | absent | MCP/route test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | `bg_transit_moorti` row for offset 5 changed in the fixture; rebuild | that tier changes; others fixed; 670(a) TRUE | L0 authority | a stale copy | writer test |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | X | **tied to the §4.11 ablation**: the frozen Q05 question on a fixture where the two bases disagree | the served reading's tier (and the caveat the reader is told) changes | the answer improves, not just the field set | the served answer is identical under both bases | baseline record |
| Evaluation | — | — | `not_applicable` | — | — | — | — |

Binding: **OFFERS** B1 (`precision_regime`, `time_basis`, `inclusivity='closed_closed'`; `t_start/t_end`
as declared resolver-derived views), B2 (`completeness_state` + the F06 companions,
`epistemic_class`, `source_qualification`, **`corpus_verifiable`, `comparable_with`, `tier_basis`**,
`operator_role='applicability'`), B3 (`window_id`, `generation`, `window_ref`), B5 (`coverage`, all
seven keys). B4: per-graha `independence_group` (`declared_lineage`). **DEMANDS** ingress-instant
positions (SC-8) and the L0 grant (G21). **Asset-local:** `grading_basis`, `grading_lag`, `reason`,
`moorti_computed`, `requested_horizon`, truncation flags.

---

## §8 — Prioritization (re-ranked — F-02)

(1) **the grain/basis/lag stamps** — with ~half the stored offsets expected to differ from the
instant value, an unmarked approximation is the most material live defect → (2) the guard (the build
outage; unblocks rebuild the moment the grant lands) → (3) horizon + coverage → (4) `as_of` at the
wrapper → (5) the instant DEMAND and its root-find → (6) the Gochara three-way contradiction and the
Kṣetra/Ch.26-vs-27 items to their owners. T0; W2.

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY` after the `[U]`/`[I]` rows;
`DATA_ACCEPTED` when a production rebuild succeeds under the grant and the contract is TRUE with
stamps; `CONSUMER_INTEGRATED` when the served surfaces carry `grading_basis` — noting **no
integrator exists to integrate**. Campaign: `ANALYZED → ENRICHED`. Non-claims: no `VALUE_EVALUATED`;
the lag incidence is an expectation until measured; the grant is not this brief's to land.

**Walkthrough (ordinary period).** "What is the quality of Jupiter's current sign transit?" → one
current row: Jupiter in Taurus since D, `moorti_name='rajata'`, `quality_tier=2`, the L0 citation,
`grading_basis='moon_nakshatra_on_ingress_date_noon_ut'`,
`grading_lag='0_to_24h_after_ingress_one_sided'`, `precision_regime='date_grain'`, `requested_horizon`
shown. The reader gets a cited grade and knows exactly which instant it was keyed on and which way
that can be off.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Guard failure mode: (a) typed `unavailable` sign-run rows — which REQUIRES a 670-successor amending conjunct (f), or (b) refuse with the prior partition preserved (no migration, no gate conflict)?** And: should the equally-bare janma and ephemeris fetches be guarded too? | **(b)** unless the native wants the ingress facts served without a grade — (a) is defensible but costs a migration and re-opens an applied contract. Guard all three reads the same way |
| 2 | **Record the ingress-instant DEMAND**, with the root-find owned by this writer over the position reference's kernel (no second swisseph integration) | yes; the ablation is the first measurement of the lag incidence |
| 3 | Stamp home: columns (`grading_basis`, `grading_lag`, `reason`, horizon, `window_id`) vs JSONB | **columns** — a CHECK and an integrity conjunct can bind to a column; JSONB cannot (the Gochara prefetch filters only on chart/ayanāṃśa, so "consumers filter on them" is not the reason) |
| 4 | Route the **three-way** Gochara contradiction (register `admitted` / context prefetches / engine never invokes / docstring says not plumbed) and the Ch.26-vs-Ch.27 citation discrepancy to Gochara's owner | yes |
| 5 | The grant's number: R6 says 1071, the blueprint says 1073 | resolve before the grant lands |

---

## §11 — Not verified here

1. The live grant state on `bg_transit_moorti`; whether the grant migration has landed since this
   base.
2. The row count (71 blueprint / 72 migration 855) and the live 670 result — [A].
3. The lag incidence — an a priori expectation (uniform ingress phase × mean lunar motion), measured
   only by the §4.11 ablation.
4. Which migration directory the deploy runner applies (both `platform/migrations/` and
   `platform/supabase/migrations/` exist).
5. The exact psycopg exception class on a missing grant (`InsufficientPrivilege` expected).
6. Whether `mechanism_register.yaml`'s `admitted` entry is loaded at runtime.
7. No database query; no test run.

## §12 — Review dispositions (v1.0 → v1.1)

F-01 accepted — the BLOCKER: §4.2 now names both options with 670(f)'s consequence, and option (a)
carries its own successor migration in `may_touch` (§10.1); F-02 accepted (§0, §2.4, §3, §4.3, §4.11,
§7 Grading-direction and Boundary rows, §8 re-ranked — one-sided forward lag, ≈49 %); F-03 accepted
(§2.3 — prefetched, not consumed; the three-way contradiction); F-04 accepted (§2.2, §4.9, §7
Context — the dead branch); F-05 accepted (§7 — a pure function with an injected oracle, runnable
today); F-06 accepted (§2.3 — Kṣetra not executed); F-07 accepted (§0, §3 — the real trace, the
`enforce` dependency, the `ka_avadhi` precedent); F-08 accepted (§7 control split); F-09 accepted
(§7 Value tied to the ablation); F-10 accepted (citations re-pinned); F-11 accepted (`must_not_touch`
paths; the grant's number unresolved); F-12 accepted (§4.5, §4.7 — `completed_horizon`, `resolution`,
`corpus_verifiable`, `comparable_with`, `tier_basis`, B1 resolver position, F06 companions); F-13
accepted (§10.3 — the real rationale); F-14 accepted (§4.4 — the root-find's owner, bracket and
tolerance); F-15 accepted (§1, §2.1 — 71 vs 72); F-16 accepted (§4.1); F-17 accepted (§2.3 — two
more readers); F-18 accepted (§2.4, §4.3 — the column name over-reads); F-19 accepted (§10.4 —
Ch.26 vs Ch.27); F-20 noted (header fields at the flip to PROPOSED).
