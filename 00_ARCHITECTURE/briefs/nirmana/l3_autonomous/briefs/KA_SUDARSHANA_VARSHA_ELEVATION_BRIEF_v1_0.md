---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_SUDARSHANA_VARSHA_ELEVATION_BRIEF
version: "1.1"
status: DRAFT_FOR_INDEPENDENT_RE_REVIEW      # v1.0 → REWORK (REVIEW_KA_SUDARSHANA_VARSHA_v1_0.md, 21 findings); v1.1 disposes each
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
synergy_binding_version: "2.3"  # binding is UNADOPTED (PROPOSED_FOR_NATIVE_RULING_THEN_ADOPTION) and its §B8 item 9
# still lists the rename direction as open while §B1 asserts it. Authority for the field NAME is therefore the
# underlying rulings, not the binding: Kṣetra ruling 8 + Gochara G-9 + Saṅgam M-3 name `precision_regime`, native
# ruling D-S4 (2026-09-24) confirms it. Alias condition is Saṅgam D-7: `day_grade` reads as `date_grain` until every
# dependent claim has an authorized successor — NOT for a count of generations. Values {instant_grain, date_grain}.
asset_or_interface_ids: ["ka_sudarshana_varsha", "SC-4 (one group, one current: the three frames share an anchor and a rule)", "SC-1 interface packet (NEW, proposed for blueprint §12.2): the omitted-`as_of` default resolves in the chart's zone — at now.ts:1643 AND the wrapper, since the former never reaches the latter", "binding amendment (generic, not asset-local): a B1 time_basis value for DATE-grain producers", "Gochara w27c: a three-way disposition, not a binary"]
goal_objective: "Qualify the year-wheel for what it provably is: ONE temporal current with one anchor and one rule, whose `tri_lagna_convergence` flag is a per-chart CONSTANT carrying no annual information; whose windows are calendar anniversaries, not solar returns; and whose served 'current year' is chosen by a UTC clock on both served paths. A consumer must never count three witnesses, read an anniversary as a return, or get the wrong year around a birthday."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code identical at 3387c9ac3 (2026-09-24)"
accepted_upstream_contract: "L1 chart_facts graha_position/sign for LAGNA, MOON, SUN at lahiri_chitrapaksha (three fact ids carried per row); ctx.config.birth_params.datetime_iso — VERIFIED naive local wall-clock (pipeline/orchestrator/birth_params.py:96,:106; the zone travels separately as tz_offset_hours :99,:109), so writer.py's raw[:10] equals charts.birth_date exactly"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_SUDARSHANA_VARSHA_v1_0.md (REWORK); re-verification of v1.1 pending"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_sudarshana_varsha/{logic,writer}.py", "platform/python-sidecar/tests/l3/test_ka_sudarshana_varsha*.py", "one NEW registry migration adding stamp conjuncts (i)/(j) and an anchor conjunct (h′) to ka_sudarshana_varsha's integrity_check_sql (migration 670 is applied — a successor UPDATE, never an edit)", "one additive DDL migration on kala_sudarshana_varsha ONLY if §10.2 chooses columns over JSONB"]
interface_packet_targets_not_may_touch: ["platform-mcp/src/tools/kala_views/now.ts:1643 (the `as_of` default `new Date().toISOString().slice(0,10)`, passed explicitly at :474-478 — this is the PRIMARY served path) and :469-495 (item 17 field projection) — Pūrṇa-owned", "platform/src/lib/retrieval/registry/layers/L3_kala/query_sudarshana_varsha.ts:38-39 ('a classically notable alignment year' — a wording correction, F-01) and :71 (the same default) — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["chart_facts / ga_positions (L1)", "bo_sudarshana (L2 namesake — confirmed unrelated computation, logic.py:8-19)", "services/gochara_v3/** (w27c is Gochara-owned; a disposition item, not an edit)", "platform-mcp/src/tools/kala_views/**", "platform/supabase/migrations/521_kala_sudarshana_varsha.sql, platform/migrations/670_* (applied)", "applied migrations 1033–1070", ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → QUALIFIED at stage 3; no t3 event today"
wave: "W2 (foundation)"
shape: single asset, rows (chart × varsha_year, 120 rows)
evidence_base: >
  Source read directly on 9feac52d7 [V]; reviewer-verified claims adopted are marked [R] (including
  an exhaustive re-computation of the convergence invariant over all 1728 natal triples × 120 years);
  migration 521, migration 670 (a)–(h), blueprint v5.0, STRAT A10 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.1 (2026-09-24): REWORK dispositions (21 findings) — F-01 the central claim is stronger and already recorded: because all three frames add the identical offset, tri_lagna_convergence is a PER-CHART CONSTANT across all 120 rows (migration 670 conjunct (c) comment :1252-1254 says so; false in all 120 for the canonical chart), so 'convergence years' do not exist and the served 'alignment year' wording is an interface correction; F-02 independence_group re-shaped to the binding's array form with roots[] = the birth anchor + all three fact ids, and the real reason the frames are one witness stated (shared anchor + rule, not a shared fact); F-03 now.ts:1643 carries the identical UTC default and passes it explicitly, so a wrapper-only fix reaches nothing — SC-1 becomes an interface packet over both; F-04 now.ts moved to must_not_touch; F-05 as_of is a date string, so two proof rows were not executable — replaced by an omitted-default fixture at a fixed wall clock; F-06 no concurrence consumer exists, so the 3→1 ablation is not measurable today; F-07 the Delivery sentinel was a constant; F-08 the Relevant-influence row demanded a behaviour the arithmetic forbids; F-09 the B1 amendment re-aimed as one generic DATE-grain value for the binding owner; F-10 birth_params is naive local wall-clock (hazard over-stated) but nothing detects a wrong anchor (under-stated) → conjunct (h′); F-11 w27c is three-way and two registry records disagree; F-12–F-21 live-path targeting, stamp detectors, baseline absence, Q05 scope, one source_qualification, B3 sha256, missing §1 records, citations, single target state, fact-id determinism."
  - "1.0 (2026-09-24): first issue."
---

# `ka_sudarshana_varsha` elevation brief — one current, three frames, honestly counted

## §0 — The recommendation, in one paragraph

`ka_sudarshana_varsha` is the cleanest small asset in the layer: pure arithmetic, no ephemeris, 120
rows per chart, natal signs read from L1 with their `fact_id`s on every row (`writer.py:44-52,
:168-170` [V]), delete-then-insert (`:54,:184`), and an eight-conjunct integrity contract (670
`:1221-1318`) whose every conjunct is a real detector. What it lacks is qualification, and the
reviewer sharpened the central point past where I had it. **All three frames add the identical
offset** `(N−1) mod 12` (`logic.py:69-74`) to their own natal index (`:110-112`), so
`tri_lagna_convergence = (jl == cl == sl)` (`:117`) holds for year N **iff the three natal signs are
equal** — it is a **per-chart constant across all 120 rows**, verified exhaustively over every natal
triple [R], and migration 670's own conjunct-(c) comment already records it (`:1252-1254`: *"The flag
is constant per chart because all three references share one offset — a known, recorded finding"*).
For the canonical chart (Aries / Aquarius / Capricorn) it is `false` in all 120 rows. So there are no
"convergence years", and the served phrase *"a classically notable alignment year"*
(`query_sudarshana_varsha.ts:38-39`; DDL comment `521:66-67`) reads a natal constant as an annual
event. Three further gaps: the windows are **calendar anniversaries**, explicitly not solar returns
(`logic.py:41-46,:83-91`), undeclared on the row; the served "current year" is chosen by a **UTC
date** at `now.ts:1643` — the primary path, which passes it explicitly and never reaches the
wrapper's own identical default [R]; and the classical rule is prose-cited only. Also: Gochara's
`w27_annual_stack.py:31` declares `context.sudarshana_rows` that nothing populates, while its
expected row shape (`{graha, house_number, …}`, `:436-460`) matches **neither** namesake table, and
two registry records disagree on its admission state [R]. Recommendation: **`QUALIFY_LIMIT`** —
state the invariant, shape `independence_group` as one group over the shared anchor, declare the
anniversary basis, fix the served wording, and carry SC-1 as an interface packet over both served
paths. Decisions: §10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (`…CONTRIBUTION_REGISTER_v2_0.md:145`) | annual frame; year-wheel progression | — |
| Strategy §3 *Clock interval* (`:91`) | annual/return adapters; inclusivity; exact vs approximated | the anniversary is *approximated*; unstamped |
| Strategy A10 (`:280`) / blueprint §3.5 row 8 (`:324`), §4 (`:396`), §16.2 (`:906`) | *"no integrator reads it"*; `independence_group = natal_root`; day-grade declared; concurrence voice (Q2) | confirmed; blueprint `:906` still says `precision_regime` — stale against binding `:32` (`precision_regime`), which this brief uses |
| **`MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md:130`** [R] | *"no L3 input; annual evidence \| preserve; receiving operator owed"* | the owed operator is exactly §10.3's question |
| **W0 field register (`…FIELD_CONTRACT_REGISTER_v1_0.md:35,:215-218`)** [R] | lists *"gochara-v3 annual stack"* as a receiver | **stale** — nothing populates `sudarshana_rows` (§2.3); recorded as such per guide §1 |
| Binding B1 (`:30-32`), B4 (`:64`) | `inclusivity` declared on every row; `time_basis` enum; `independence_group` = `[{group_id, family, roots[], members[], basis}]` | a calendar-anniversary bound fits no `time_basis` value — and neither does the binding's own tz-aware-midnight derivation for DATE producers (§4.3) |
| Migration 521 (`:32-57`, `:66-67`) | DDL: `varsha_year 1..120`, six sign indices, `tri_lagna_convergence BOOLEAN`, `UNIQUE(chart, ayanamsha, varsha_year)`, `formula_version` (not in the key), `computed_at`; comment *"a classically notable alignment year"* | no inclusivity/grain/independence column; the comment is F-01's wording issue |
| **Migration 670 (`:1221-1318`) (a)–(h), esp. (c) `:1252-1254`** [R] | tiling; arithmetic pinned; convergence re-derived — **with the comment recording that the flag is constant per chart**; labels restate `reference_signs`; fact ids resolve and match L1 values; contiguity; one anchor; anniversary windows | all eight are real detectors; **none tests a stamp**, and (h) anchors on `min(window_start)`, so a wheel built from a wrong birth date passes (F-10) |
| `tests/l3/test_ka_sudarshana_varsha.py:115-117,:124-134` [R] | canonical triple Aries/Aquarius/Capricorn; the lockstep invariant already asserted | the invariant is known to the code, not only to this brief |
| `birth_params.py:96,:106,:109` [R] | `datetime_iso` = naive local wall-clock; zone separate as `tz_offset_hours` | `raw[:10]` **is** `charts.birth_date` — the v1.0 tz hazard was over-stated |
| `logic.py:8-19` | namesake-only collision with `bo_sudarshana` — *do not revisit* | respected |
| Seed (`asset_registry_seed.ts:2498-2514`) | `depends_on: ['ga_positions']` | accurate |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration and latent value [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_sudarshana_varsha'`, `scope: 'per_chart'`,
`depends_on: ['ga_positions']`, `catalog_status: 'CURRENT'`. Cost: trivial (no ephemeris).
**Latent-value classes (template §2.1):** (a) *existing, served, correct* — the six sign indices and
the three fact ids; (b) *existing, served, mis-framed* — `tri_lagna_convergence` (a natal constant
served as an annual event); (c) *existing, unserved* — the anniversary basis and the shared-anchor
independence, computable but on no row; (d) *absent* — a verse-grain citation.
**Knowledge time (template §2.6):** `window_start/window_end` are event-time calendar bounds;
`computed_at` (`521:53`) is the only knowledge-time field.

### 2.2 The code [V]/[R]
- `logic.py`: `DEFAULT_MAX_VARSHA_YEAR = 120` (`:57`); `varsha_year_for_date` (`:60-66`, raises
  before birth — **no production caller**, F-12); `active_house_offset = (N−1) % 12` (`:69-74`);
  `progressed_sign_index` (`:77-80`); `varsha_window` = `[birth + (N−1)y, birth + Ny)` calendar
  anniversaries (`:83-91`; docstring *"not a true solar-return instant"* `:41-46`);
  `compute_tri_lagna_year` → `jl == cl == sl` (`:117`) — **constant per chart** (F-01).
- `writer.py`: natal signs from `chart_facts` (`:44-52`, `:81-95`; indices via the engine's `SIGNS`);
  birth date = `birth_params.datetime_iso[:10]` (`:98-113`) — naive local, so equal to
  `charts.birth_date`; 120 rows (`:148-172`, fact ids at `:168-170`); refusals (`:130-142`);
  DELETE then INSERT `ON CONFLICT DO NOTHING` (`:54,:57-70,:184-187`); never commits.

### 2.3 Consumers [V]/[R]
| consumer | reads | role |
|---|---|---|
| `now.ts:469-495` (item 17), via the wrapper with **`asOfDate` from `:1643` `new Date().toISOString().slice(0,10)`** passed explicitly at `:474-478` | the current row; honest `current: null` before birth / after 120 (`:483`) | served — **the primary path; the wrapper's own default at `:71` is never reached through it** |
| `query_sudarshana_varsha.ts` | full 120-row wheel (`MAX_LIMIT 120`, `:26`), `is_current` by `as_of` (a `YYYY-MM-DD` **string**, `:46,:71,:88`), `total_matching` | served, direct |
| `source_query_availability.ts:2944-2961` | availability | census |
| `gochara_v3/mechanisms/w27_annual_stack.py:10,31,75,82` | declares `context.sudarshana_rows` *"(kala_sudarshana / bo_sudarshana)"*; `compute_sudarshana` (`:436-460`) expects `{graha, house_number, window_start_iso, window_end_iso}` — **a shape neither namesake has**; `context.py:114-186` has no such field and nothing populates one; `engine.py` never invokes w27 | **dangling declaration** (Gochara-owned) |
| Kāla writers, L4 | none | — |

**Live-path statement.** Served on two surfaces; read by no integrator; the UTC `as_of` default is
live on both served paths.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| natal sign indices + fact ids | `COMPUTED_FACT_CONFIGURATION` (referenced) | L1 | correct; 670(e) re-derives the index from the L1 value |
| progressed signs | `QUALIFIED_RULE` if the `(N−1) mod 12` rule is verse-cited; prose-cited today | this logic | the row's **single** `source_qualification` (B2 allows one, F-16) |
| `tri_lagna_convergence` | derived boolean, **constant per chart** | this logic | carries no temporal information; `convergence_basis='natal_constant'` |
| windows | calendar anniversary — an approximation of the solar return | this logic | `precision_regime='date_grain'`; `inclusivity='closed_open'`; the approximation is carried by the asset-local `window_basis`/`approximates`, not by a second `source_qualification` |
| `is_current` | serving-time derivation | TS | depends on the `as_of` default's zone |

### 2.5 Ladders
`PLAN_REVIEWED`; W2 source accepted. t3: no event. 120 rows [A].

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | A concurrence reader (Q2/Q3, SC-4) receiving a `tri_lagna_convergence=true` row sees three frames agreeing, with no field saying they share one anchor and one rule — and no field saying the flag is the **same in all 120 rows of that chart**, so it can be read as "this year is special" when it means "this chart's three natal signs coincide". The served description calls it *"a classically notable alignment year"*. The same reader sees DATE windows with no grain or basis and cannot tell an anniversary from a solar return. And a caller at 2026-02-04 23:30 IST — the eve of the native's birthday — is told year 42 or 43 depending on a **UTC** clock read in `now.ts:1643` |
| Evidence | `logic.py:69-74,:83-91,:117`; `writer.py:44-52,:98-113`; `521:32-57,:66-67`; `670:1252-1254`; `now.ts:1643,:474-478`; `query_sudarshana_varsha.ts:38-39,:71`; binding B1/B4 — [V]/[R] |
| Expected contract | B4 (`independence_group` + `declared_current_count` on anything a concurrence reads), B1 (`inclusivity`, `precision_regime`, `time_basis` on every row), SC-1 (`as_of` in the chart's zone), Strategy §3 (exact vs approximated), §N.7 item 1 (narration restates what the fact is) and item 5 |
| Defect class | **unqualified** (independence, grain, basis, citation absent) + **mis-framed** (a natal constant described as an annual event) + **wrong context** (UTC `as_of` on both served paths) + **dangling declaration** (w27c) |
| Impact | over-counting in any annual-frame concurrence; misreading an anniversary as a return; an off-by-one current year around birthdays; a Gochara mechanism naming an input it cannot fetch in a shape neither table has |
| Non-claim | no computed value is wrong; 670 (a)–(h) is assumed green (not queried); the flag's constancy is proved by arithmetic and 670's own comment, not by a DB count |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q05 **partial and conditional** (F-15): Q05's proof is *"remove a method; show
   actual changed and unchanged evidence"* (`STRATEGY:65`), and with no ledger and no integrator
   nothing consumes the voice today — so this asset currently offers the voice's *qualification*, not
   the voice. Q-K06 is a blueprint cross-reference, not an adopted question.
2. **The invariant stated, not discovered (F-01).** Every row carries `convergence_basis=
   'natal_constant'` and the brief states plainly: `tri_lagna_convergence` is constant per chart and
   carries **zero temporal information**; it is a restatement of "the three natal signs coincide".
   The served wording *"a classically notable alignment year"* is corrected in the interface packet
   (and in 521's comment by a successor migration if the native wants the DDL text changed).
3. **Independence (B4, SC-4) in the binding's shape (F-02).** One group:
   `independence_group = [{group_id, family:'sudarshana_varsha', roots:[<birth-date anchor>,
   lagna_fact_id, moon_fact_id, sun_fact_id], members:['jl','cl','sl'], basis:'declared_lineage'}]`,
   `declared_current_count = 1` — **counting groups, not facts**. The three natal signs *are* three
   distinct L1 facts; what makes the frames one witness is the **shared anchor and the shared rule**,
   and the `moon_fact_id` in `roots[]` is what makes this asset non-independent of
   `ka_tithi_pravesha` for a consumer of both.
4. **Time (B1) — one generic amendment, not an asset-local one (F-09).** `inclusivity='closed_open'`,
   `precision_regime='date_grain'`, and the asset-local `window_basis='calendar_anniversary'` with
   `approximates='solar_return_instant'`. `time_basis`: none of `{event_instant, noon_ut_knot,
   date_grain_midpoint}` describes a calendar-anniversary bound — and the binding's own Saṅgam rule
   (`:27`, *"instant at the chart's tz-aware midnight"*) names a fourth derivation the enum also
   lacks. The gap is **binding-wide for every DATE-grain producer** (sudarshana, kota, moorti,
   jivana, avadhi), so this brief raises **one** amendment for a generic value (e.g.
   `date_grain_local_midnight`) to the binding owner, and carries `time_basis=null` with the
   amendment id as a transitional state.
5. **Citation (B2) — one `source_qualification` per row (F-16).** The row's `source_qualification`
   is the **rule's** (`verse_cited` with a page/verse reference if the L0 corpus has one — DP02
   request; else `unsourced`); the window's approximation lives in `window_basis`/`approximates`, not
   in a second `source_qualification`. The out-of-scope sub-daśā structure is recorded `unexplored`.
6. **`as_of` (SC-1) as an interface packet over BOTH paths (F-03, F-04).** The omitted `as_of`
   resolves to *today in the chart's zone* (`charts.timezone_id`, which the TS registry already reads
   — `chart_header.ts:78`), echoed in the response. The packet must cover **`now.ts:1643`** (the
   primary path, which passes its own UTC date explicitly and shares that default with every item
   `kala_now_get` assembles) **and** `query_sudarshana_varsha.ts:71`. A wrapper-only fix changes
   nothing a `kala_now_get` reader sees. Pūrṇa owns the TS; L3 owns the sentinel test.
7. **Coverage (B5).** Trivial and complete: `{requested_horizon:[1,120], completed_horizon:[1,120],
   resolution:'varsha_year', partitions_searched:['jl','cl','sl'], exclusions:[],
   unsearched_regions:[], completion_detector:'120_rows_contiguous'}` — emitted once per chart.
8. **B3 (F-17).** `window_ref = {asset_id, generation, id}` with `id = sha256(chart_id, varsha_year,
   FORMULA_VERSION)` and `generation = FORMULA_VERSION`; the natural-key tuple is **not** an id, and
   `formula_version` is not in the PK today (`521:54-55`) — the mapping is declared either way.
9. **A real stamp detector (F-13) and an anchor detector (F-10).** 670 tests no stamp, and (h)
   anchors on `min(window_start)`, so a wheel built from a wrong birth date passes all eight. A
   **successor migration** (670 is applied; never edited) adds: (i) every row carries the stamps with
   vocabulary-valid values; (j) `declared_current_count = 1`; and **(h′) `min(window_start) =
   charts.birth_date`** — the only external anchor.
10. **The w27c disposition is three-way (F-11).** The mechanism's expected shape
    (`{graha, house_number, …}`) matches neither namesake, so "consume by `window_ref`" is not
    available without a **new Gochara-owned transform**, and that transform would be a λ-product
    modifier (`_SD_HOUSE_MODIFIERS`), the operand class blueprint Q2 (`:667`) bars before an M-4
    audit. Two registry records disagree — `w27c_sudarshana.yaml:15` `candidate` vs
    `mechanism_register.yaml:237` `admitted`, both asserting `citation_status: cited` to *"BPHS
    Sudarśana Cakra chapter"*, which also bears on decision §10.3's citation question. Options:
    drop the declaration; re-scope to a Gochara transform under M-4; or leave it candidate with the
    declaration corrected.
11. **Old vs new.** Positive: 120 rows with stamps. Negative: **live path** — `as_of` before birth →
    no `is_current` row → `current: null` with honest-empty coverage (F-12; the unit-level
    pre-birth raise has no production caller). Boundary: the omitted-default fixture (item 6).
    Missing: no `datetime_iso` → refusal. Duplicated: three frames → one witness.
12. **Simpler baseline.** The rows as they are.
13. **Ablation (F-06).** The 3→1 count cannot be measured today: no concurrence consumer exists
    (SC-6 ledger unowned, IP-5 unbuilt, w27c unwired). Today's provable ablation is **row-level** —
    with and without the stamps, a consumer fixture that counts `members` vs `declared_current_count`
    reads 3 vs 1 — and the served count test is marked *"detector exists once IP-5/SC-6 lands"*.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: all arithmetic; fact-id carriage; refusals; delete-then-insert; the 670 contract; the
  lockstep test (`test_ka_sudarshana_varsha.py:124-134`).
- `QUALIFY_LIMIT`: the stamps in §4.2–4.5, 4.7, 4.8.
- **Migrations**: one successor adding (i)/(j)/(h′); optionally one additive DDL (§10.2).
- Fences: `bo_sudarshana` untouched; Gochara's w27c by its owner; L1 untouched; both served files are
  interface-packet targets, not `may_touch`.
- Rollback: additive.

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | L3 rows; L1 refs + one rule + calendar arithmetic; placement correct; `QUALIFY_LIMIT` |
| B | `ga_positions` real; `birth_params` from ctx; no hidden read; fan-out: two served surfaces, one dangling Gochara declaration |
| C | invariants: 670 (a)–(h) + (h′)/(i)/(j); `declared_current_count=1`; `tri_lagna_convergence` identical in all 120 rows of a chart; `is_current` invariant to the server's zone. Golden: canonical chart year 1 = natal signs |
| D | the verse citation (DP02) |
| E | served ×2; integrator ×0 |
| F | `independence_group`, `convergence_basis`, `precision_regime`, `approximates`, echoed `as_of` |
| G | trivial; justified no-change |
| H | idempotent; no ephemeris |
| I | files in `may_touch`; W2; one successor migration; one optional DDL |
| J | this brief; §7; the review |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Invariant | COMPUTATIONAL_CORRECTNESS | U | `-k convergence_is_constant` — every natal triple × 120 years | `tri_lagna_convergence` identical in all 120 rows; `true` iff the natal triple is equal | the lockstep rule | any row differs within a chart | unit test |
| Positive | COMPUTATIONAL_CORRECTNESS | I | canonical chart rebuild; run the **successor** `integrity_check_sql` | 120 rows; (a)–(h)+(h′)+(i)+(j) TRUE; stamps present | the contract | any conjunct FALSE; a stamp absent | integrity SQL |
| Negative (live path) | COMPUTATIONAL_CORRECTNESS | S | `as_of` before birth via `kala_now_get` | `current: null` with honest-empty coverage | no fabricated year | a year returned | MCP test |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | U | natal Moon sign +1 | `cl_active_*` +1 in **every** row; `jl_*`/`sl_*` byte-identical; `tri_lagna_convergence` **unchanged** (all `false`) — or, from an equal-triple fixture, **all 120 flip** | the flag's real dependence | "convergence years move" (arithmetically impossible) | unit test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | S | two `as_of` inputs resolving to the same chart-zone date | identical `is_current` row | zone-normalised | differs | wrapper test |
| Duplication | COMPUTATIONAL_CORRECTNESS | I | persisted row | one group; `declared_current_count=1`; three `members`; `roots[]` contains the real `moon_fact_id` | B4 shape | a per-fact count of 3 | integrity conjunct (j) |
| Context | COMPUTATIONAL_CORRECTNESS | U | `datetime_iso` absent | refusal note | honest absence | rows written | unit test |
| Boundary | COMPUTATIONAL_CORRECTNESS | S | **omitted `as_of`**, wall clock faked to `2026-02-04T18:30:00Z` (= 2026-02-05 00:00 Asia/Kolkata); and again at `18:29:59Z` | year 43 at the first clock, 42 at the second; resolved date echoed | chart-zone resolution | today's code answers 42 at both | wrapper + MCP test |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel: `independence_group[0].roots` containing the **real** `moon_fact_id` (a per-row value the wrapper cannot synthesise) | reaches `kala_now_get`'s `sudarshana_varsha` object and the saved reading | per-row propagation | absent | MCP test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | L1 sign fact regenerated | rows replaced; natal indices equal the regenerated fact values; ids re-resolved (whether `fact_id` is deterministic is unverified — §11.5) | 670(e) | stale ids or indices | writer test |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | S | ordinary-period case (year 43, no convergence) — **the frozen-question fixture is pending the baseline freeze** (`KALA_BASELINE_v1_0.md` does not exist) | one annual voice with its basis and a count of 1; the baseline gives three unlabelled frames and an "alignment year" phrase | — | no distinction | baseline record (pending) |
| Evaluation | — | — | `not_applicable` (no claim issued) | — | — | — | — |

Binding: **OFFERS** B1 (`inclusivity`, `precision_regime`; `time_basis` null pending the generic
amendment), B2 (`epistemic_class`, `completeness_state='applied'`, one `source_qualification`), B3
(`window_ref` with a sha256 id), B4 (`independence_group` in the array shape,
`declared_current_count`), B5 (`coverage`). **DEMANDS** a B1 ruling on DATE-grain derivation.
**Asset-local:** `convergence_basis`, `window_basis`, `approximates`.

---

## §8 — Prioritization

(1) the invariant + independence stamps (the over-count and the mis-framing) → (2) the served
"alignment year" wording → (3) grain/basis stamps → (4) SC-1 over both served paths → (5) the
successor migration's (h′)/(i)/(j) → (6) citation (DP02) → (7) w27c to Gochara. T0; W2.

---

## §9 — Disposition and target state

`QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY`; `DATA_ACCEPTED` on the production successor contract
TRUE with stamps; `CONSUMER_INTEGRATED` when both served paths carry them. Campaign: `ANALYZED →
QUALIFIED`. Non-claims: no `VALUE_EVALUATED`; no integrator exists; the rule's verse citation is
pending; the 3→1 count is unmeasurable until SC-6/IP-5.

**Walkthrough (ordinary year).** "Which year of the wheel am I in?" → year 43, the three progressed
signs, `tri_lagna_convergence=false` **with `convergence_basis='natal_constant'`**,
`declared_current_count=1`, `precision_regime='date_grain'`, `approximates='solar_return_instant'`,
`as_of` echoed in Asia/Kolkata. Quiet, exact, honest about what it approximates and about what the
flag is not.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **B1 for DATE-grain producers: one generic value (e.g. `date_grain_local_midnight`) raised to the binding owner, covering sudarshana/kota/moorti/jivana/avadhi — not an asset-local `calendar_anniversary`** | yes, one generic amendment |
| 2 | Stamp home: additive `qualification` JSONB column vs per-chart meta table | JSONB column |
| 3 | Citation: request a verse-grain source, else stamp `unsourced` — noting `mechanism_register.yaml:242-244` already asserts a BPHS Sudarśana chapter citation for the Gochara mechanism | request; adjudicate that assertion in the same pass |
| 4 | **w27c: drop the declaration, re-scope to a Gochara-owned transform under M-4, or leave candidate with the declaration corrected?** — and reconcile `candidate` vs `admitted` | route to Gochara's owner with all three options and the contradiction named |
| 5 | The "receiving operator owed" (CURRENT_STATE `:130`) — who consumes this voice? | the SC-6 ledger's owner; until then the asset stays qualified-but-unconsumed |

---

## §11 — Not verified here

1. The 670 contract's live result and the 120-row count [A].
2. Whether the L0 classical corpus holds a verse-grain Sudarśana-cakra source.
3. Gochara branches other than this base.
4. Node's IANA-zone formatting on the deployed runtime (the chart-zone `as_of` is implementable —
   `charts.timezone_id` is already read by the TS registry — but ICU availability was not checked).
5. Whether `ga_positions` regenerates `chart_facts.fact_id` deterministically (bears on the Revision
   row).
6. No database query; no test run.

## §12 — Review dispositions (v1.0 → v1.1)

F-01 accepted (§0, §2.4, §3, §4.2, §7 Invariant row, and the served-wording packet); F-02 accepted
(§4.3 — array shape, `roots[]`, groups not facts); F-03 accepted (§2.3, §4.6,
`interface_packet_targets`); F-04 accepted (`must_not_touch`); F-05 accepted (§7 Boundary and
Irrelevant-control replaced with the omitted-default fixture); F-06 accepted (§4.13, §7 Duplication);
F-07 accepted (§7 Delivery — `roots[]` with the real `moon_fact_id`); F-08 accepted (§7
Relevant-influence); F-09 accepted (§4.4, §10.1 — one generic amendment); F-10 accepted (§1, §4.9 —
conjunct (h′); the tz hazard withdrawn); F-11 accepted (§2.3, §4.10, §10.4 — three-way + the
registry contradiction); F-12 accepted (§2.2, §7 Negative — the live path); F-13 accepted (§4.9);
F-14 accepted (§7 Value — the baseline does not exist); F-15 accepted (§4.1); F-16 accepted (§2.4,
§4.5 — one `source_qualification`); F-17 accepted (§4.8); F-18 accepted (§1 three records added; §2.1
latent-value classes and knowledge-time pin); F-19 accepted (citations and paths re-pinned; the stale
blueprint `precision_regime` noted); F-20 accepted (`target_state_data_plane` = one state); F-21
accepted (§7 Revision + §11.5).
