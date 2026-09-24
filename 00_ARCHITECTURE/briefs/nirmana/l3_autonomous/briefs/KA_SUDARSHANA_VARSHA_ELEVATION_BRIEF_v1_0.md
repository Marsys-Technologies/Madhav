---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_SUDARSHANA_VARSHA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW      # → PROPOSED_FOR_NATIVE_RULING after the Fable 5.1 review
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; one B1 question raised (§4.3)
asset_or_interface_ids: ["ka_sudarshana_varsha", "SC-4 (independence_group = natal_root across the three frames)", "SC-1 (as_of at the served wrapper)", "Gochara w27c_sudarshana consumer (verification item)"]
goal_objective: "Qualify the year-wheel for what it is — three reference frames progressed from one natal root on calendar-anniversary windows — so that a consumer can never count Lagna/Chandra/Sūrya agreement as three independent witnesses, never read an anniversary date as a solar-return instant, and never receive a 'current year' computed from the server's clock instead of the chart's; and confirm whether any integrator actually reads it."
source_revision: "9feac52d7 (l3/kala-layer-briefs)"
accepted_upstream_contract: "L1 chart_facts graha_position/sign for LAGNA, MOON, SUN at lahiri_chitrapaksha (fact ids carried on every row); ctx.config.birth_params.datetime_iso (FROZEN contract input) for the birth date"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_SUDARSHANA_VARSHA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_sudarshana_varsha/{logic,writer}.py", "platform/python-sidecar/tests/**/test_ka_sudarshana_varsha*.py", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/query_sudarshana_varsha.ts:71 (as_of default), platform-mcp/src/tools/kala_views/now.ts:466-480 (item 17)", "one additive DDL migration on kala_sudarshana_varsha ONLY if §10.2 chooses columns over JSONB"]
must_not_touch: ["chart_facts / ga_positions (L1)", "bo_sudarshana (L2 namesake — confirmed unrelated computation, logic.py:8-19)", "services/gochara_v3/** (the w27c reader is Gochara-owned; a verification item, not an edit)", "supabase/migrations/521_kala_sudarshana_varsha.sql, migration 670 (applied)", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY (stage 3); DATA_ACCEPTED when the 670 contract (a)–(h) returns TRUE on production with the new stamps present; CONSUMER_INTEGRATED when now.ts/query_sudarshana_varsha serve the stamps under a chart-tz as_of"
target_state_campaign: "ANALYZED → QUALIFIED at stage 3; no t3 event today"
wave: "W2 (foundation)"
shape: single asset, rows (chart × varsha_year, 120 rows)
evidence_base: >
  Source read directly on 9feac52d7 [V]; migration 521, migration 670 ka_sudarshana_varsha
  contract (a)–(h) [V]; blueprint v5.0 §3.5 row 8 / §4 / §16.2, STRAT A10 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_sudarshana_varsha` elevation brief — one root, three frames, honestly counted

## §0 — The recommendation, in one paragraph

`ka_sudarshana_varsha` is the cleanest small asset in the layer: pure arithmetic, no ephemeris,
120 rows per chart, natal signs read from L1 with their `fact_id`s carried on every row
(`writer.py:44-52,157-160` [V]), delete-then-insert (`:54,:184` [V]), and an integrity contract
(670 `:1221-1320`) that re-derives the arithmetic, the convergence flag, the tiling, the labels
and the fact ids — eight conjuncts, all of them real detectors. What it lacks is not correctness
but **qualification**: (1) the three "frames" (Janma/Chandra/Sūrya lagna) progress from **one
natal root** by the same `(N−1) mod 12` rule (`logic.py:70-77`), so `tri_lagna_convergence`
(`jl == cl == sl`, `logic.py:117`) is a property of the natal sign spacing, not three independent
testimonies — yet no row says so, and a concurrence reader would count three; (2) the windows are
**calendar anniversaries** (`varsha_window`, `logic.py:84-92`), explicitly *not* a solar-return
instant (`logic.py:41-46`), day-grade, half-open per docstring — none of which is declared on the
row (the DDL only checks `window_end >= window_start`, 521 `:56`); (3) the served "current year"
is chosen by `as_of` defaulting to `new Date()` at the TS wrapper (`query_sudarshana_varsha.ts:71`)
— the **server's** date, not the chart's zone (SC-1), and `now.ts` passes its own `asOfDate`; (4)
the classical source is named in prose (*"Per Maharishi Parashara's tri-lagna framework"*,
`logic.py:22`) with no verse-grain citation and the sub-daśā structure is declared out of scope
(`:27-33`) — honest, but unstamped; (5) the blueprint says no integrator reads it (STRAT A10),
while Gochara's `w27c_sudarshana` mechanism declares `context.sudarshana_rows` sourced from
*"kala_sudarshana / bo_sudarshana"* (`w27_annual_stack.py:31`) and `context.py` has **no**
sudarshana prefetch [V grep] — the mechanism names a namesake it cannot read. Recommendation:
**`QUALIFY_LIMIT`** — stamp `independence_group={basis:'declared_lineage', root:'natal_signs',
members:[jl,cl,sl]}`, `declared_current_count=1`, `claim_grain='date_grain'`, `inclusivity=
'closed_open'`, `source_qualification` per rule, the anniversary basis declared (B1 question,
§4.3); `as_of` resolved in the chart's zone at the wrapper; the w27c reference corrected by its
owner. No new rows. Decisions: the B1 basis and the stamps' home (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (ka_sudarshana_varsha row) | annual frame; year-wheel progression | — |
| Strategy §3 *Clock interval* (`:91`) | annual/return adapters; inclusivity; exact vs approximated | the anniversary is *approximated*; unstamped |
| Strategy A10 / blueprint §3.5 row 8 (`:324`), §4 (`:396`), §16.2 (`:906`) | *"no integrator reads it"*; `independence_group = natal_root` on all three frames; day-grade declared; concurrence voice (Q2) | confirmed; the w27c mention is a namesake reference, not a read (§2.3) |
| Blueprint §9 Q2 / Q3 | independent-witness discipline; annual-frame concurrence | this asset offers **one** witness |
| Binding B1 (`:30-32`) | `inclusivity ∈ {closed_closed, closed_open}`; `time_basis ∈ {event_instant, noon_ut_knot, date_grain_midpoint}`; `claim_grain ∈ {instant_grain, date_grain, day_grade→date_grain}` | a calendar-anniversary bound fits none of the three `time_basis` values (§4.3) |
| Migration 521 (`:32-56`) | DDL: `varsha_year 1..120`, six sign indices `0..11`, `tri_lagna_convergence BOOLEAN`, `UNIQUE(chart, ayanamsha, varsha_year)`, `window_end >= window_start`; three `*_fact_id` columns | no inclusivity/grain/independence column; ayanāṃśa defaulted to lahiri |
| Migration 670 (`:1221-1320`) (a)–(h) | tiling; arithmetic pinned; convergence re-derived (§N.8); labels restate `reference_signs`; fact ids resolve; contiguous years; one natal anchor; anniversary windows | strong; assumed green (§11) |
| `logic.py:8-19` | namesake-only collision with `bo_sudarshana` — *do not revisit* | respected |
| Seed (`asset_registry_seed.ts:2498-2513`) | `depends_on: ['ga_positions']`; `count_sql` chart-scoped | accurate |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_sudarshana_varsha'`, `scope: 'per_chart'`,
`depends_on: ['ga_positions']`, `catalog_status: 'CURRENT'`. Cost: trivial (no ephemeris).

### 2.2 The code [V]
- `logic.py`: `DEFAULT_MAX_VARSHA_YEAR = 120` (`:57`); `varsha_year_for_date` (`:60-66`, raises
  before birth); `active_house_offset = (N−1) % 12` (`:69-74`); `progressed_sign_index` (`:77-80`);
  `varsha_window` = `[birth + (N−1)y, birth + Ny)` calendar anniversaries (`:84-92`, docstring
  *"not a true solar-return instant"* `:41-46`); `compute_tri_lagna_year` → `tri_lagna_convergence
  = jl == cl == sl` (`:117`).
- `writer.py`: natal signs from `chart_facts` `graha_position/sign` for `LAGNA, MOON, SUN` at
  `CANONICAL_AYANAMSHA` (`:44-52`, `:80-95`; sign names → index via the engine's `SIGNS`, never a
  second table `:19-22`); birth date = `birth_params.datetime_iso[:10]` (`:98-112` — the calendar
  date component of an ISO string whose zone is whatever the orchestrator supplied); 120 rows
  (`:140-165`); refusals on missing birth date / missing facts (`:124-136`); DELETE then INSERT
  `ON CONFLICT DO NOTHING` (`:54,:57-70,:184-187`); never commits.

### 2.3 Consumers (grep `kala_sudarshana`, tests/seed/generated excluded) [V]
| consumer | reads | role |
|---|---|---|
| `query_sudarshana_varsha.ts` | full 120-row wheel (`MAX_LIMIT 120`, `:26`), `is_current` by `as_of` **default `new Date()`** (`:71`), `total_matching` | served `relevance_navigation` |
| `now.ts:466-480` (item 17) | the current row via the wrapper with its own `asOfDate`; honest `current: null` when before birth/after 120 | served |
| `source_query_availability.ts` | availability | census |
| `gochara_v3/mechanisms/w27_annual_stack.py:10,31,75,82` | declares `context.sudarshana_rows` *"(kala_sudarshana / bo_sudarshana)"* — `context.py` has **no** `sudarshana` read [V grep] | **dangling declaration** (Gochara-owned) |
| Kāla writers, L4 | none | — |

**Live-path statement.** Served on two surfaces; read by no integrator; the server-date `as_of`
default is live on the direct wrapper call.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| natal sign indices + fact ids | `COMPUTED_FACT_CONFIGURATION` (referenced) | L1 | correct |
| progressed signs | `QUALIFIED_RULE` **if** the `(N−1) mod 12` rule is cited at verse grain; today prose-cited | this logic | `source_qualification` owed (`verse_cited` pending / `unsourced`) |
| `tri_lagna_convergence` | derived boolean over one root | this logic | not a concurrence of independent witnesses |
| windows | calendar anniversary — `algorithmic_approximation` of the solar return | this logic | `claim_grain='date_grain'`; `inclusivity='closed_open'` (docstring) |
| `is_current` | serving-time derivation | TS wrapper | depends on `as_of`'s zone |

### 2.5 Ladders
`PLAN_REVIEWED`; W2 source accepted. t3: no event. 120 rows live [A].

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | A concurrence reader (Q2/Q3, SC-4) receiving a year with `tri_lagna_convergence=true` sees three frames agreeing and no field saying they share one natal root and one rule — it can count three witnesses where there is one. The same reader sees `window_start/end` as DATEs with no grain or basis field and cannot tell an anniversary from a solar return. And a caller of `query_sudarshana_varsha` at 23:30 IST on the eve of the native's birthday gets `is_current` on year N or N+1 depending on the **server's** UTC date |
| Evidence | `logic.py:70-77,84-92,117`; `writer.py:44-52,98-112`; migration 521 `:32-56` (no grain/independence column); `query_sudarshana_varsha.ts:71`; binding B1/B4 [V] |
| Expected contract | Binding B4 (`independence_group` + `declared_current_count` on anything a concurrence reads), B1 (`inclusivity`, `claim_grain`, `time_basis` declared on every row), SC-1 (`as_of` in the chart's zone), Strategy §3 (exact vs approximated), §N.7 item 5 (verified fact ≠ verified prose: the rule needs its citation) |
| Defect class | **unqualified** (independence, grain, basis, citation absent) + **wrong context** (server-date `as_of`) + **dangling declaration** (w27c) |
| Impact | over-counting in any annual-frame concurrence; misreading of anniversary as return; an off-by-one current year around birthdays and midnight; a Gochara mechanism that names an input it cannot fetch |
| Non-claim | no computed value is wrong; 670 (a)–(h) is assumed green (not queried); the `datetime_iso` zone convention is the orchestrator's (`birth_params.py`) and is not re-derived here |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q05 (an annual frame beside other clocks — as **one** voice); Q-K06. Not
   Q01–Q04 alone.
2. **Independence (B4, SC-4).** Every row carries `independence_group = {basis:'declared_lineage',
   root:'natal_signs', members:['jl','cl','sl'], root_fact_ids:[lagna, moon, sun]}` and
   `declared_current_count = 1`; `tri_lagna_convergence` keeps its meaning and gains
   `convergence_basis='same_root_same_rule'`.
3. **Time (B1) — a question, not an invention.** `inclusivity='closed_open'` (as the docstring
   says), `claim_grain='date_grain'`, `source_qualification='algorithmic_approximation'` on the
   window, with `approximates='solar_return_instant'`. `time_basis`: none of `{event_instant,
   noon_ut_knot, date_grain_midpoint}` describes a calendar-anniversary bound. The brief **asks
   the binding owner** (§10.1) whether (i) `calendar_anniversary` is added to B1, or (ii) the
   windows are re-based on the true solar-return instant (`event_instant`) via a root-find — a
   larger change this asset does not need for its own rule and which would make `window_start`
   a `timestamptz`. Until ruled, the row declares `time_basis=null` with the reason.
4. **Citation (B2).** `source_qualification='verse_cited'` with the BPHS/Sudarśana-cakra
   reference at page/verse grain if the L0 corpus has it (`find_verses_about` / classical text
   tables — DP02 request), else `'unsourced'` stamped honestly; the out-of-scope sub-daśā
   structure recorded as `unexplored`.
5. **`as_of` (SC-1).** The wrapper resolves an omitted `as_of` to *today in the chart's zone*
   (`charts.timezone_id`, the convention `ka_taranga.py:92` already uses), echoed in the response;
   `now.ts` already passes its own date — unchanged.
6. **Coverage (B5).** Trivial and complete: `{requested_horizon:[1,120], completed_horizon:
   [1,120], resolution:'varsha_year', partitions_searched:['jl','cl','sl'], exclusions:[],
   unsearched_regions:[], completion_detector:'120_rows_contiguous'}` — emitted once per chart
   (a `quality`-style JSONB, §10.2), so the layer's uniform reader finds it.
7. **The w27c reference.** Raised to Gochara's owner: `w27_annual_stack.py:31` names
   `kala_sudarshana / bo_sudarshana`; `context.py` reads neither; the mechanism must either
   consume `kala_sudarshana_varsha` by `window_ref` (then it is an integrator and STRAT A10
   updates) or drop the declaration.
8. **Old vs new.** Positive: 120 rows with stamps. Negative: missing SUN fact → refusal
   (unchanged). Boundary: `as_of` = birthday eve 23:30 IST → `is_current` = year N (chart zone).
   Missing: no `datetime_iso` → refusal. Duplicated: three frames agreeing → one witness.
9. **Simpler baseline.** The rows as they are.
10. **Ablation.** Feed a convergence year to a concurrence consumer with and without
    `declared_current_count`: today it counts 3; after, 1. That count is the elevation.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: all arithmetic; fact-id carriage; refusals; delete-then-insert; the 670 contract.
- `QUALIFY_LIMIT`: the stamps in §4.2–4.4, 4.6.
- **Stamp home (§10.2):** a `qualification` JSONB column (one additive DDL) **or** a per-chart
  `kala_sudarshana_varsha_meta` — recommend the JSONB column; 670's conjuncts unaffected.
- Fences: `bo_sudarshana` untouched; Gochara's w27c by its owner; L1 untouched.
- Rollback: additive.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_sudarshana_varsha`, L3 rows; epistemic: L1 refs + one rule + calendar arithmetic; placement correct (annual frame); `QUALIFY_LIMIT` |
| B | `ga_positions` real; `birth_params` from ctx; no hidden read; fan-out: two served surfaces, one dangling Gochara declaration |
| C | invariants: 670 (a)–(h); `declared_current_count=1` on every row; `is_current` invariant to server zone. Golden: canonical chart year 1 = natal signs; boundary: birthday eve |
| D | the verse citation (DP02) |
| E | served ×2; integrator ×0 (w27c dangling) |
| F | `independence_group`, `claim_grain`, `approximates`, `as_of` echoed |
| G | trivial; justified no-change |
| H | idempotent; no ephemeris; no credentials |
| I | files in `may_touch`; W2; one optional DDL |
| J | this brief; §7; review |

---

## §7 — Proof matrix (tier `[U]` unit, `[I]` DB fixture, `[S]` served)

| proof | tier | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|
| Positive | I | canonical chart rebuild; `SELECT integrity_check_sql` | 120 rows; 670 TRUE; stamps present | (a)–(h) + stamps | any conjunct FALSE / stamp absent | integrity SQL |
| Negative | U | `varsha_year_for_date(birth, birth−1d)` | raises | pre-birth rejected | returns 0 | unit |
| Relevant influence | U | change natal Moon sign by 1 | `cl_active_*` shift by 1 every year; `jl/sl` unchanged; convergence years move | isolation | others move | unit |
| Irrelevant control | S | same `as_of` instant expressed in UTC vs chart zone | same `is_current` row | zone-invariant | differs (today, around midnight) | wrapper test |
| Duplication | S | a convergence year to a concurrence consumer | counted as **one** witness (`declared_current_count=1`) | one root | counted 3 | consumer fixture |
| Context | U | `datetime_iso` absent | refusal note | honest absence | rows written | unit |
| Boundary | S | `as_of` = birthday eve 23:30 chart-local | year N current; `+1 h` → N+1 | `closed_open` | wrong year | wrapper test |
| Delivery | S | sentinel `approximates='solar_return_instant'` | reaches `now.ts` item 17 | survives | absent | MCP test |
| Revision | I | L1 sign fact regenerated | rows replaced; `root_fact_ids` new | fresh | stale ids | writer test |
| Value | S | frozen Q-K06 question | the reader receives one annual voice with basis; baseline gives three unlabelled | — | no distinction | baseline |
| Evaluation | — | `not_applicable` (no claim issued) | — | — | — | — |

Binding: **OFFERS** B1 (`inclusivity`, `claim_grain`, `time_basis` pending §10.1), B2
(`epistemic_class`, `completeness_state='applied'`, `source_qualification`), B4
(`independence_group`, `declared_current_count`), B5 (`coverage`, per chart). **DEMANDS** a B1
ruling on the anniversary basis. B3: `window_ref={asset_id, generation:FORMULA_VERSION, id:
(chart, varsha_year)}`. **Asset-local:** `convergence_basis`, `approximates`, `root_fact_ids`.

---

## §8 — Prioritization

(1) independence stamps (the over-count) → (2) grain/inclusivity/approximation stamps → (3)
`as_of` in chart zone → (4) citation (DP02) → (5) w27c to Gochara. T0; W2; no P-candidate; fan-out
nil.

---

## §9 — Disposition and target state

`QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY` after §7 `[U]`/`[I]`; `DATA_ACCEPTED` on the
production 670 TRUE with stamps; `CONSUMER_INTEGRATED` when `now.ts`/wrapper serve them. Campaign:
`ANALYZED → QUALIFIED`. Non-claims: no `VALUE_EVALUATED`; no integrator exists to integrate; the
rule's verse citation is pending.

**Walkthrough (ordinary year).** "Which year of the wheel am I in?" → one row: year 43, the three
progressed signs, `tri_lagna_convergence=false`, `declared_current_count=1`, `claim_grain=
'date_grain'`, `approximates='solar_return_instant'`, `as_of` echoed in Asia/Kolkata. Quiet, exact,
honest about what it approximates.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **B1 `time_basis` for calendar-anniversary bounds: add `calendar_anniversary`, or re-base on the true return instant?** | add the enum value (this rule is defined on anniversaries); re-basing is a different technique |
| 2 | Stamp home: additive `qualification` JSONB column vs per-chart meta table | JSONB column |
| 3 | Citation: request a verse-grain source from the L0 corpus, else stamp `unsourced` | request; stamp honestly meanwhile |
| 4 | Route the w27c dangling declaration to Gochara's owner | yes |

---

## §11 — Not verified here

1. The 670 contract's live result (assumed green; blueprint records 120 rows and no `error`).
2. The zone convention of `birth_params.datetime_iso` (`pipeline/orchestrator/birth_params.py`) —
   not read; if it is UTC, a near-midnight birth could shift the anniversary by a day.
3. Whether the L0 classical corpus holds a verse-grain Sudarśana-cakra source.
4. `context.py` has no `sudarshana` read — grep on this base; Gochara's branches not checked.
5. No database query; no test run.
