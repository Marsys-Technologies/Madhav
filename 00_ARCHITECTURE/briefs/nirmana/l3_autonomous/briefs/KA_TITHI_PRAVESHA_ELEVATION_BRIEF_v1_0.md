---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_TITHI_PRAVESHA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW      # → PROPOSED_FOR_NATIVE_RULING after the Fable 5.1 review
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / blob 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md   # adopted by reference; B-rows in §7
asset_or_interface_ids: ["ka_tithi_pravesha", "SC-1 (temporal contract: tz-aware instants)", "D-M second L0 lane (source adjudication)", "SC-6 voice (annual frame)"]
goal_objective: "Make ka_tithi_pravesha's return instants true instants (tz-aware, UTC, not 5.5 h late), its method honestly stamped unsourced-with-receipt until the L0 lane adjudicates it, its rows typed as one root's annual testimony, and its integrator use decided as a concurrence voice rather than a dependency label — preserving a numerically careful lunar-return kernel that already verifies itself two ways."
source_revision: "9feac52d7 (l3/kala-layer-briefs; = origin/l3/kala-elevation-readiness tip 2026-09-24)"
accepted_upstream_contract: "L1 chart_facts MOON longitude_sidereal by fact_id (§N.5); birth_params via ctx.config (§N.2); W2 first-frontier source 47131772b (writer prepares its candidate before the chart-partition DELETE)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_TITHI_PRAVESHA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/services/ka_tithi_pravesha/{writer,logic}.py", "platform/python-sidecar/pipeline/orchestrator/writers/ka_tithi_pravesha.py", "platform/python-sidecar/tests/l3/test_ka_tithi_pravesha*.py", "one additive migration on kala_tithi_pravesha (qualification columns)", "interface packet only: platform/src/lib/retrieval/registry/layers/L3_kala/query_tithi_pravesha.ts, platform-mcp/src/tools/kala_views/now.ts"]
must_not_touch: ["chart_facts / ga_* (L1)", "pyjhora_adapter / panchang_engine (shared engines)", "classical_text_chunks (L0 corpus — the source adjudication is the L0 lane's, D-M)", "ka_gochara_v3_century_materialize (its declared Tithi edge was retired as an edge, N-8 — not this brief's to reinstate)", "platform-mcp/src/tools/kala_views/** except as an interface packet", "applied migrations", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY (stage 3); DATA_ACCEPTED requires a rebuild of the 120 rows under the corrected instants (a P-class step, W2 data); CONSUMER_INTEGRATED when the annual voice reaches a composite surface"
target_state_campaign: "ANALYZED → ENRICHED at stage 3; a t0 freeze exists and is inadmissible under t3"
wave: "W2"
shape: single asset, rows (chart × ayanāṃśa × praveśa year)
evidence_base: >
  Source read directly on 9feac52d7 [V]; KALA_ASSET_BRIEF_CONTEXT §4 (5.5 h measured in
  production), Lane D §13, T1 Frontier row, elevation plan Q2, Gochara N-8, KALA_DELEGATED_DECISIONS
  D-M [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_tithi_pravesha` elevation brief — an annual clock whose instants must be instants

## §0 — The recommendation, in one paragraph

`ka_tithi_pravesha` casts the lunar-return annual chart: it roots the transiting Moon's return to
the natal sidereal longitude (read by `fact_id` from L1, never restated) nearest each solar
anniversary and verifies the result two ways (`writer.py:181-230` [V]) — numerically the most
careful row-producer in the frontier. Two things undo it. **Its instants are not instants**: the
birth wall-clock is parsed naive (`datetime.fromisoformat(raw[:19])`, `:125` [V]), the return
instant is computed and stored as a naive local datetime into a `timestamptz` column — measured
in production as **5.5 hours late** on every row (context §4 [A]); a served "praveśa moment" that
is wrong by 5.5 h puts the Moon ~2.7° from where the row says it is. And **its method is
unqualified with an unreceipted absence claim**: `CLASSICAL_SOURCE_CITATION = "not_in_corpus: …"`
(`:64-70` [V]) is a string constant asserting the corpus lacks the technique — the exact defect
class (a directory read as a corpus) that cost this campaign a day; no `count(*)` was ever run
against `classical_text_chunks` for lunar-return / varṣa-praveśa doctrine. Recommendation:
**`ENRICH_CORRECT` + `QUALIFY_LIMIT`** — tz-aware instants under binding B1 (with a falsifier
that fails on today's rows: the Moon at the stored instant must be within tolerance of natal);
`source_qualification='unsourced'` **with a count(*) receipt**, upgradeable only by the D-M
second L0 lane; per-row `completeness_state` from the two-pass verification; the annual frame
declared one root (the natal Moon — shared with every nakṣatra daśā) and admitted as a
**concurrence voice**, not an integrator input, which settles Q2 for this asset without
retirement. Decisions: the L0 lane, the voice, and the rebuild (§10).

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 (REGISTER:146) | *"Return bracketing, annual-chart and numerical search kernels. P/Q/E: named method/equation needs source adjudication; current Moon-longitude return is not accepted merely from name. DP02/07."* | unchanged; the adjudication is D-M's lane |
| Strategy §6.1 **L3-A09** | *"Qualify the implemented Moon-return method against the admitted method before promotion. Preserve return identity and source; add an explicit use decision. Current v3 does not read it."* W2 | unchanged; Gochara N-8 retired the century edge *as an edge*, asset untouched |
| Strategy §3 *Clock interval* | method, hierarchy/parent, lord role, actual start/end, inclusivity, applicability/prerequisites, failure reason, exact vs approximated subdivision | the row has start/end and a verification status; no inclusivity, no applicability, no F06 state (§3) |
| KALA_ASSET_BRIEF_CONTEXT §4 | *"`kala_tithi_pravesha`'s window instants are stored **5.5 hours late** in production"* — naive datetime into `timestamptz` | mechanism confirmed at source [V] (§2.2); the production figure is [A] |
| W2 source `47131772b` | candidate prepared before the chart-partition DELETE | `_DELETE_SQL` + `ON CONFLICT DO NOTHING` (`:79,:97`) [V] |
| Lane D §13 / T1 | 120 rows `lit`; the sharpest consumer tension: served (`now.ts`, `query_tithi_pravesha.ts`) vs elevation-plan Q2 "consumed by nothing" | both true: **served, not integrated** — `now.ts`/`query_tithi_pravesha.ts` read the table [V]; no `ka_*` integrator reads it |
| Elevation plan Q2 | wire into a qualified operator or retire with evidenced disposition | §10: a concurrence voice (SC-6), no retirement |
| KALA_DELEGATED_DECISIONS D-M | tithi-praveśa source steward folded into a **second L0 lane pass** with the 19 residual `bg_transit_rules` rows | binds §4 item 3 and §10 |
| Blueprint v5.0 §3.5 row 7, §15 G-1, §16.2 | tz-aware instants; `source_qualification` stamp; `return_bracket`/`cross_check_diff` persisted as qualification; the corpus-absence lint | binds §4 |
| Guard G-1 (blueprint §15) | *absence by `count(*)` against the object* — any `not_in_corpus` literal without a receipt fails | `writer.py:64-70` is the canonical target |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V seed]
`asset_registry_seed.ts:2536-2544`: `postgres_table`, `target_table: 'kala_tithi_pravesha'`,
chart-scoped `count_sql`, `depends_on: ['ga_positions']`. Live: 120 rows canonical chart, single
build 2026-09-07, `asset_throughput` `lit` matching [A: Lane D].

### 2.2 The code [V]
- **Constants** `services/ka_tithi_pravesha/writer.py:60-70`: `FORMULA_VERSION =
  "ka_tithi_pravesha_v1.0"`; `CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"`; `ENGINE_AYANAMSHA =
  "lahiri"` (*"pyjhora_adapter's own id for the same ayanamsha"* — a second alias map, SC-10);
  `CLASSICAL_SOURCE_CITATION = "not_in_corpus: Tithi-Praveśa … no primary-source chapter/verse
  citation for the technique specifically is ingested in this corpus — an ingestion work item is
  filed, not fabricated here"` — a constant, no query behind it; the module docstring (`:35`)
  repeats it: *"honestly `not_in_corpus` on every row"*.
- **Natal Moon** `_FETCH_NATAL_MOON_SQL` (`:72-77`): `fact_id, fact_value_num FROM chart_facts …
  fact_subject='MOON' AND fact_key='longitude_sidereal'` — by `fact_id`, canonical ayanāṃśa
  (§N.5 done right); `moon_fact_id` persisted.
- **Birth instant** `_birth_dt_and_params_from_config` (`:116-127`): `datetime.fromisoformat(raw[:19])`
  — **truncates the ISO string at 19 characters, discarding any offset**, returning a naive
  wall-clock datetime; *"never guesses a birth instant"* (B.10 honoured) but the timezone is
  dropped silently.
- **Per year** `_compute_one_year` (`:181-230`): `pravesha_anniversary(birth_dt, N)` = `birth_dt +
  relativedelta(years=N-1)` (`logic.py:102-109`); `lunar_return(anniversary, natal_moon_long,
  _longitude_fn)` roots the return (`logic.py:121-139`, *"always returns a (datetime, audit) pair
  — never raises"*); the annual chart is cast at `instant`; **two-pass verification**: the annual
  chart's own Moon longitude vs natal within `LUNAR_RETURN_TOL_DEG = 0.01` (`logic.py:73`) →
  `verification_pass_status ∈ {two_pass_verified, divergent_flagged}` (`:203-211`);
  `window_start = instant`, `window_end = next_instant` (naive), `start_converged/end_converged`,
  `ephemeris_audit_jsonb` with both audits and the cross-check diff.
- **Write** (`:79-98`): `DELETE … WHERE chart_id`; `INSERT INTO kala_tithi_pravesha (chart_id,
  ayanamsha_id, pravesha_year, window_start, window_end, start_converged, end_converged,
  pravesha_lagna_sign_idx/name/degree, graha_positions_jsonb, natal_moon_longitude_deg,
  moon_fact_id, ephemeris_audit_jsonb, verification_pass_status, classical_source_citation,
  formula_version) … ON CONFLICT (chart_id, ayanamsha_id, pravesha_year) DO NOTHING`.
  `window_start`/`window_end` receive a **naive** `datetime`.
- `run` (`:240-275`): missing/unparsable `birth_params.datetime_iso` → honest no-op with notes
  (`:252`); one row per praveśa year (120 = a 120-year span).

### 2.3 Consumers (grep on this base, tests excluded) [V]
| consumer | reads | role |
|---|---|---|
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_tithi_pravesha.ts` | the table | `relevance_navigation` (served) |
| `platform-mcp/src/tools/kala_views/now.ts` | the table (reports `"computed"` for the canonical chart, STATE.md C2 [A]) | `relevance_navigation` |
| any `ka_*` writer | **none** | — |
| century materializer | declared edge **retired** (N-8); `ClassContext.fetch` never read it [A: Gochara plan §5.4] | — |

**Live-path statement.** The 5.5 h defect is live on every served row (both surfaces read
`window_start/window_end`). No integrator consumes the asset.

### 2.4 Epistemic class of the important fields
| field | class | authority | note |
|---|---|---|---|
| `natal_moon_longitude_deg`, `moon_fact_id` | `COMPUTED_FACT_CONFIGURATION` (reference) | L1 | correct |
| `window_start/end` (return instants) | computed fact — **astronomical** | this writer's root-find + the engine | true as a wall-clock, false as a `timestamptz` |
| `verification_pass_status` | detector output | this writer | two-pass; a real detector (it can and does read `divergent_flagged`) |
| `pravesha_lagna_*`, `graha_positions_jsonb` | computed fact | full chart cast at the instant | inherit the instant's error |
| the *technique* (lunar-return praveśa as an annual clock) | `QUALIFIED_RULE` only if adjudicated; today **`unsourced`** | L0 (DP02) | the absence claim has no receipt |
| `classical_source_citation` | a string constant | this writer | G-1 target |

### 2.5 Ladders and cost
`PLAN_REVIEWED`; W2 source accepted; 120 rows present under the wrong instants. t3: t0 freeze
inadmissible. Cost: *"~3.4 ms/row"* root-find (writer docstring `:13`) × 120 — cheap; unmeasured
end-to-end.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | For the canonical chart the served `window_start` of each praveśa year is a `timestamptz` that is 5.5 h later than the true lunar-return instant [A: context §4, production]. Mechanism [V]: the birth instant is parsed naive (`:125`), the return instant is a naive local datetime, and the INSERT (`:81-98`) hands it to a `timestamptz` column, which interprets it in the session's timezone (UTC on the builder) — IST wall-clock stored as if UTC. **Falsifier that fails today:** evaluate the Moon's sidereal longitude at the stored `window_start` *read as UTC*; it is ~2.7° from `natal_moon_longitude_deg` (5.5 h × ~0.5°/h), while the row's own `verification_pass_status` says `two_pass_verified` — because the verification was run on the naive value, not on what was stored. A verified row that is wrong: §N.7 item 5 (*verified fact ≠ verified prose*) applied to a timestamp |
| Evidence | `writer.py:125` (`raw[:19]`), `:181-230` (naive `instant`), `:81-98` (INSERT into `window_start/window_end`) [V]; the 5.5 h figure [A: KALA_ASSET_BRIEF_CONTEXT §4] |
| Expected contract | Binding B1 (`t_start/t_end` timestamptz UTC, never naive; tz from the birth instant); DP07 (*start/end/instant precision, timezone*); Strategy §3 *Clock interval*; SC-1; F28 (a `two_pass_verified` that cannot detect the stored error is not a detector for it) |
| Defect class | **wrong context** (timezone dropped) + **detector mismatch** (verification precedes the corrupting write) |
| Impact | Q06/Q-K06: the annual frame's boundary is wrong by 5.5 h — harmless for a *year* label, fatal for the praveśa **lagna** (the ascendant moves ~1 sign per 2 h: the served `pravesha_lagna_sign` can be off by two or three signs) and for every `graha_positions_jsonb` value; anything that later reads this as an instant (a concurrence voice, a comparison) inherits it |
| Non-claim | The 5.5 h figure is the context document's production measurement, not re-measured here; whether the *lagna* is actually wrong on the stored rows depends on when in the day each return fell — asserted as a mechanism, not counted |

**Secondary (G-1):** `CLASSICAL_SOURCE_CITATION` asserts corpus absence with no query. The served
corpus holds 15 texts / 10,651 chunks (Gochara G-9 count [A]); whether any carries lunar-return
or varṣa-praveśa doctrine (Tājika Nīlakaṇṭhī, if admitted; Phaladīpikā's annual chapters) has
**never been asked by predicate**. This brief does not assert presence or absence — it routes the
question to the D-M lane and makes the row honest either way.

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q06 (*how does this chapter differ* — an annual frame boundary), Q05/Q-K06 (an
   annual method as a distinct voice with its own root), Q09 (*what changes with convention* — it
   carries `ayanamsha_id`). Cannot serve Q01/Q02/Q08 (no mechanism, no search).
2. **Instants (B1, SC-1).** Parse `birth_params.datetime_iso` **with its offset** (or the chart's
   declared tz — never `raw[:19]`); compute the return in UTC; persist `t_start`/`t_end` as
   `timestamptz` UTC (aliasing `window_start/end` one generation), `inclusivity='closed_open'`
   (year N ends where year N+1 begins), `time_basis='event_instant'`, `claim_grain=
   'instant_grain'`; the verification runs on the value **as it will be stored** (round-trip
   through the column's semantics), so `two_pass_verified` can go false on a tz error.
3. **Source qualification with a receipt (B2, G-1).** `source_qualification='unsourced'`,
   `corpus_verifiable=false`, and the citation string replaced by a **receipt**: the predicate
   query and its `count(*)` against `classical_text_chunks` (run by the D-M L0 lane), recorded in
   the migration/docstring with the date. Upgrade to `verse_cited` only by that lane, at page grain.
4. **Per-row F06 state.** `completeness_state='applied'` iff `two_pass_verified` (both roots
   converged, cross-check ≤ tol) — else `'unavailable'` with the audit as reason; the technique's
   applicability stays `unqualified` on every row until item 3 upgrades it (both fields coexist:
   the *computation* applied, the *doctrine* unqualified — F04 keeps them distinct).
   `epistemic_class='COMPUTED_FACT_CONFIGURATION'` on the instant and the cast; `operator_role=
   'computation'`; `tier_basis` n/a (no score).
5. **One root, declared (B4).** `independence_group = [{family:'lunar_return_annual',
   roots:[moon_fact_id], basis:'declared_lineage'}]` — the same natal Moon that seeds every
   nakṣatra daśā and Sudarśana's Chandra frame; a consumer must not count this and Vimśottarī as
   two witnesses.
6. **Comparability.** `comparable_with='different_convention'` against every daśā/Sudarśana
   window — an annual frame is not a daśā scale.
7. **The use decision (Q2 → a voice, SC-6).** The asset becomes a **concurrence voice**: for an
   interval, `verdict ∈ {silent, not_applicable}` until the doctrine is qualified (a praveśa lagna
   or year-lord "supports/opposes" requires an interpretive rule the corpus must supply), then
   `supports/opposes` under that rule. No integrator dependency is created; the century edge stays
   retired (N-8).
8. **Coverage (B5).** `coverage = {years_requested, years_computed, unavailable_years[]}` on the
   partition; an unconvergeable year is a row with `unavailable`, never a missing year.
9. **Old vs new.** Positive: year N → `t_start` = true UTC instant; `Moon(t_start) − natal ≤ tol`
   when re-evaluated on the stored value. Negative: unparsable birth instant → no-op with notes
   (unchanged). Boundary: a return within minutes of midnight IST → the date changes correctly.
   Missing: non-convergent root → `unavailable`. Duplicated: n/a.
10. **Simpler baseline.** Today's rows.
11. **Ablation.** Re-evaluate the Moon at each stored instant before and after: before, ~2.7° off
    on every row with `two_pass_verified`; after, ≤ 0.01°. That delta *is* the elevation; if it is
    absent on this base's rows, the 5.5 h premise is wrong and the brief says so.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the root-find (`lunar_return`), the two-pass verification, `fact_id` provenance,
  `ephemeris_audit_jsonb`, the honest no-op on missing birth params, `ON CONFLICT` + DELETE.
- `ENRICH_CORRECT`: tz-aware instants; the verification round-trip; coverage.
- `QUALIFY_LIMIT`: `source_qualification` with receipt; `independence_group`; `comparable_with`.
- **Rebuild**: the corrected instants change every stored row — a rebuild of the 120-row partition
  is a P-class step (W2 data, under an accepted vector); the old rows are a rebuildable projection
  (no issued claim references them [A: no `phala_*` reader found by grep — §11]); `formula_version`
  bumps to `v1.1`.
- **Migration**: additive qualification columns (`source_qualification`, `corpus_verifiable`,
  `completeness_state`, `independence_group`, `comparable_with`, `time_basis`, `claim_grain`,
  `inclusivity`) ≥ 1082; `window_start/end` semantics corrected by the writer, column type
  unchanged.
- **Fences**: `classical_text_chunks` untouched (L0 lane); `pyjhora_adapter` untouched (its
  `'lahiri'` alias is SC-10's); `now.ts`/`query_tithi_pravesha.ts` by interface packet (serve
  `t_start` with `claim_grain`).
- **Rollback**: `formula_version` distinguishes generations; the prior partition is re-creatable
  from the old code path.

---

## §6 — Lenses A–J

| lens | answer |
|---|---|
| A | `ka_tithi_pravesha`, L3 rows; epistemic: astronomical computation (return instant, cast) + an unqualified classical technique; placement correct (annual Clock interval); `ENRICH_CORRECT + QUALIFY_LIMIT` |
| B | `ga_positions` declared and read (natal Moon by `fact_id`); `birth_params` from ctx (§N.2); the engine via the adapter; no hidden table; leaf (no L3 consumer) |
| C | invariants: `Moon(t_start) ≈ natal ± tol` **on the stored value**; `t_end(N) = t_start(N+1)`; roots converge; golden: the forensic chart's year-1 return; boundary: midnight-IST returns; detectors: the round-trip verification, the coverage count |
| D | 120 years is the full horizon; no rows sought; the *doctrine* is the gap (L0) |
| E | two served readers, zero integrators; the retired century edge; no duplication |
| F | `completeness_state`, `source_qualification`, `independence_group` machine-readable; the absence claim becomes a receipt |
| G | 3.4 ms/row — **justified no-change** |
| H | idempotent; single-run; `count_sql` chart-scoped; no credentials |
| I | files in `may_touch`; one migration ≥ 1082; rebuild as a P-class step; W2 |
| J | this brief; §7; review; the round-trip ablation output |

---

## §7 — Proof matrix

| proof | fixture | expected | invariant | detector fails when… |
|---|---|---|---|---|
| Positive | canonical birth params **with** offset; year 1 | `t_start` UTC; Moon at `t_start` within 0.01° of natal, evaluated on the stored value | round-trip verified | > tol |
| Negative | `datetime_iso` without offset and no chart tz | no-op with `unavailable` notes — **never** a naive guess | B.10 | a row is written |
| Relevant influence | shift the birth offset by +05:30 → +00:00 | `t_start` shifts by exactly 5.5 h; the cast changes | offset-sensitive | unchanged |
| Irrelevant control | reorder `graha_positions_jsonb` keys | identical row | order-invariant | differs |
| Duplication | this asset + Vimśottarī on one interval | one `independence_group` root | root shared | counted twice |
| Context/missingness | a year whose root does not converge | `unavailable` row with audit | never dropped | year missing |
| Boundary | a return at 23:55 IST | UTC date is the previous day; `pravesha_lagna` from the true instant | correct date | off by a day |
| Delivery | sentinel `source_qualification='unsourced'` | reaches `query_tithi_pravesha.ts` and `kala_now_get` | survives | absent |
| Revision | `formula_version` bump | prior partition replaced; no accretion | §N.3 | accretion |
| Value | frozen Q06 / ordinary-period | the annual boundary now correct to the minute; the baseline's is 5.5 h off | — | no delta (premise wrong) |

Binding: **OFFERS** B1 (`t_start/t_end`, `inclusivity`, `time_basis`, `claim_grain`), B2
(`completeness_state`, `source_qualification`, `corpus_verifiable`, `comparable_with`), B4
(`independence_group`), B5 (`coverage`). **DEMANDS** L1 natal Moon by `fact_id` (present).

---

## §8 — Prioritization

(1) the instant defect (correctness; live on every row; SC-1) → (2) the absence receipt (G-1; a
day of this campaign was lost to this defect class) → (3) F06/independence/comparability stamps →
(4) the voice (Q2). T0, W2; no P-candidate; no downstream unlock (leaf) — but the same naive-
datetime mechanism must be checked in every writer that persists an instant (blueprint SC-1).

---

## §9 — Disposition and target state

`ENRICH_CORRECT` + `QUALIFY_LIMIT`. Data-plane: `PRODUCER_READY` after §7; `DATA_ACCEPTED` after
the corrected rebuild on an accepted vector; `CONSUMER_INTEGRATED` when the voice reaches a
composite surface (D-H record). Campaign: `ANALYZED` → `ENRICHED`. Non-claims: the technique
stays `unqualified` until the L0 lane rules — *"it cannot earn full completion solely by returning
unavailable states"* (Strategy §7), so the lane is on this asset's critical path; no claim of
doctrinal correctness of the Moon-return definition itself.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **Run the D-M second L0 lane's predicate search for lunar-return / varṣa-praveśa doctrine before any `verse_cited` stamp; until then `unsourced` with a receipt** | yes |
| 2 | **Q2 for this asset: a concurrence voice (SC-6), no integrator edge, no retirement** | yes |
| 3 | Authorize the 120-row rebuild under the corrected instants once stage 3 lands (P-class, W2 data) | yes, on an accepted vector — the current rows are wrong by construction |
| 4 | Does the praveśa *lagna* become an admitted annual-frame object (a Tājika-style year chart) or stay a computed cast without interpretive weight? | stay computed-only until the lane qualifies it |

---

## §11 — Not verified here

1. The 5.5 h production figure — context document [A]; the mechanism is [V].
2. Whether any served or L4 row references `kala_tithi_pravesha` rows by id (grep found no
   `ph_*`/`mi_*` reader; scope: writers directory).
3. Whether the corpus carries lunar-return doctrine — deliberately **not asserted**; the lane asks.
4. The praveśa-lagna error on the stored rows — mechanism stated, not counted.
5. No database query.
